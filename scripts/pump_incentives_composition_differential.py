"""Signed offline Pump admin->claim token-incentives composition differential.

Chains the two bounded handlers in one LiteSVM instance per program binary:
admin_update_token_incentives (authority substituted locally on a finalized
Global snapshot, as in pump_admin_token_incentives_differential) sets a real
schedule on a zeroed GlobalVolumeAccumulator, then — with the user volume
accumulator and funded canonical incentive ATA seeded as in
pump_claim_token_incentives_differential — the clock advances past a day
boundary and claim_token_incentives runs. The identical scenario executes
against the captured original ELF and the candidate; admin post-state, claim
outcome, payout, user-accumulator transitions, events, inner CPIs and watched
post-states are compared. The global sol_volumes denominator is patched in
after the admin transaction (documented synthetic volume seed, mirroring the
claim fixture, whose schedule/vault are synthetic there). No broadcast, no
live funds.
"""

import base64
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pump_admin_token_incentives_differential as adm
import pump_claim_token_incentives_differential as clm

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction, VersionedTransaction
from solders.transaction_metadata import FailedTransactionMetadata

PUMP = adm.PUMP
TARGET = ROOT / "evidence/original/pump/deployed.so"
IDL = json.loads((ROOT / "evidence/upstream/pump.json").read_text())

# Schedule set by the admin transaction.
START, END, PERIOD, SUPPLY = 1000, 3900, 100, 1000
ADMIN_NOW, CLAIM_NOW = 900, 1150
DAY0_VOLUME = 100          # synthetic global sol-volume denominator (day 0)
USER_VOLUME = 20           # user's day-0 sol volume
EXPECTED_PAYOUT = USER_VOLUME * SUPPLY // DAY0_VOLUME   # 200


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def account_record(vm, key):
    return clm.account_record(vm, key)


def idl_item(name):
    return next(row for row in IDL["instructions"] if row["name"] == name)


def global_fixture_data():
    fixture = next(row for row in json.loads(adm.SNAPSHOT.read_text())["accounts"]
                   if row["program_name"] == "pump")
    raw = bytearray(base64.b64decode(fixture["data_base64"]))
    raw[9:41] = bytes(adm.AUTH.pubkey())
    return fixture, bytes(raw)


def build_vm(binary, case):
    """Fresh VM with Global (authority=AUTH), a zeroed-schedule accumulator
    (or the pre-existing schedule for the control), the claim fixture's mint /
    user ATA / user volume, and a funded canonical incentive ATA."""
    _, keys, prior, user_volume, global_ata = clm.fixture_data()
    vm = LiteSVM().with_sigverify(True).with_blockhash_check(False) \
        .with_log_bytes_limit(None)
    vm.add_program_from_file(PUMP, str(binary))
    for program, path in ((adm.TOKEN, "spl_token"), (adm.TOKEN22, "spl_token_2022"),
                          (adm.ATA, "associated_token")):
        vm.add_program_from_file(program, str(
            ROOT / "evidence/dependencies" / path / "deployed.so"))
    vm.airdrop(adm.AUTH.pubkey(), 10**10)
    vm.airdrop(clm.PAYER.pubkey(), 10_000_000_000)
    fixture, global_data = global_fixture_data()
    vm.set_account(adm.GLOBAL, Account(fixture["lamports"], global_data, PUMP))
    mint_key = keys["mint"]
    if case.get("admin"):
        initial = adm.initial_accumulator({
            "old_start": 0, "old_end": 0, "old_period": 0,
            "supplies": [0] * 30, "volumes": [0] * 30,
            "old_mint": str(mint_key)})
    else:  # control: pre-existing schedule, never touched by an admin update
        initial = adm.initial_accumulator({
            "old_start": START, "old_end": END, "old_period": PERIOD,
            "supplies": [SUPPLY] * 30, "volumes": [DAY0_VOLUME] * 30,
            "old_mint": str(mint_key)})
    vm.set_account(adm.VOLUME, Account(10**8, initial, PUMP))
    for name in ("mint", "user_base"):
        record = prior[name]
        vm.set_account(keys[name], Account(record["lamports"],
            base64.b64decode(record["data_base64"]),
            Pubkey.from_string(record["owner"])))
    user_data = bytearray(base64.b64decode(prior["volume"]["data_base64"]))
    user_data[40] = 1  # needs_claim
    struct.pack_into("<QQQq", user_data, 41, 0, 0,
                     case.get("user_volume", USER_VOLUME), START)
    user_data[73] = 0  # has_total_claimed_tokens
    vm.set_account(user_volume, Account(prior["volume"]["lamports"],
                                        bytes(user_data), PUMP))
    incentive_data = bytearray(base64.b64decode(prior["curve_base"]["data_base64"]))
    incentive_data[32:64] = bytes(adm.VOLUME)
    struct.pack_into("<Q", incentive_data, 64, 1_000_000)
    vm.set_account(global_ata, Account(prior["curve_base"]["lamports"],
                                       bytes(incentive_data), adm.TOKEN22))
    return vm, keys, user_volume, global_ata


def send(vm, tx):
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    error = str(result.err()) if failed else None
    inner = []
    message_keys = tx.message.account_keys
    for group in meta.inner_instructions():
        for entry in group:
            ix = entry.instruction()
            inner.append({"program": str(message_keys[ix.program_id_index]),
                          "accounts": [str(message_keys[i]) for i in ix.accounts],
                          "data_hex": bytes(ix.data).hex(),
                          "stack_height": entry.stack_height()})
    return {"error": error, "success": error is None,
            "signature": str(tx.signatures[0]),
            "events": [line.removeprefix("Program data: ")
                       for line in meta.logs() if line.startswith("Program data: ")],
            "inner": inner,
            "relevant_logs": [line for line in meta.logs()
                              if "Instruction:" in line or "AnchorError" in line
                              or "Program data:" in line or "failed" in line]}


def admin_tx(vm):
    item = idl_item("admin_update_token_incentives")
    _, keys, _, _, global_ata = clm.fixture_data()
    accounts = {"authority": adm.AUTH.pubkey(), "global": adm.GLOBAL,
                "global_volume_accumulator": adm.VOLUME, "mint": keys["mint"],
                "global_incentive_token_account": global_ata,
                "associated_token_program": adm.ATA, "system_program": adm.SYSTEM,
                "token_program": adm.TOKEN22, "event_authority": adm.EVENT,
                "program": PUMP}
    metas = [AccountMeta(accounts[entry["name"]], bool(entry.get("signer")),
                         bool(entry.get("writable"))) for entry in item["accounts"]]
    data = bytes(item["discriminator"]) + struct.pack(
        "<qqqQQ", START, END, PERIOD, 99, SUPPLY)  # day>=30: set every day
    message = Message.new_with_blockhash(
        [Instruction(PUMP, data, metas)], adm.AUTH.pubkey(), vm.latest_blockhash())
    tx = VersionedTransaction(message, [adm.AUTH])
    assert all(tx.verify_with_results())
    return tx


def claim_tx(vm):
    _, keys, _, user_volume, global_ata = clm.fixture_data()
    item = idl_item("claim_token_incentives")
    ordered = [keys["user"], keys["user_base"], adm.VOLUME, global_ata,
               user_volume, keys["mint"], adm.TOKEN22, adm.SYSTEM, adm.ATA,
               adm.EVENT, PUMP, clm.PAYER.pubkey()]
    metas = [AccountMeta(key, bool(info.get("signer")), bool(info.get("writable")))
             for key, info in zip(ordered, item["accounts"], strict=True)]
    tx = Transaction.new_signed_with_payer(
        [Instruction(PUMP, clm.DISCRIMINATOR, metas)], clm.PAYER.pubkey(),
        [clm.PAYER], vm.latest_blockhash())
    assert all(tx.verify_with_results())
    return tx


def token_amount(record):
    if record is None:
        return None
    return struct.unpack_from("<Q", base64.b64decode(record["data_base64"]), 64)[0]


def run_scenario(binary, case):
    vm, keys, user_volume, global_ata = build_vm(binary, case)
    watched = {"global": adm.GLOBAL, "global_volume": adm.VOLUME,
               "mint": keys["mint"], "user": keys["user"],
               "user_ata": keys["user_base"], "user_volume": user_volume,
               "global_ata": global_ata}
    vm.set_clock(Clock(0, 0, 0, 0, ADMIN_NOW))
    admin_result = None
    if case.get("admin"):
        admin_result = send(vm, admin_tx(vm))
        # Synthetic day-0 volume seed (see module docstring): patch only the
        # sol_volumes denominator into the admin-set accumulator.
        record = vm.get_account(adm.VOLUME)
        data = bytearray(bytes(record.data))
        struct.pack_into("<Q", data, 304, DAY0_VOLUME)
        vm.set_account(adm.VOLUME, Account(record.lamports, bytes(data), PUMP))
    admin_after = {name: account_record(vm, key) for name, key in watched.items()}
    user_before_claim = clm.parse_user(
        base64.b64decode(admin_after["user_volume"]["data_base64"]))
    vm.set_clock(Clock(0, 0, 0, 0, CLAIM_NOW))
    claim_result = send(vm, claim_tx(vm))
    after = {name: account_record(vm, key) for name, key in watched.items()}
    user_after = clm.parse_user(base64.b64decode(after["user_volume"]["data_base64"]))
    payout = (token_amount(after["user_ata"]) or 0) - \
             (token_amount(admin_after["user_ata"]) or 0)
    return {"admin": admin_result, "admin_after": admin_after,
            "claim": claim_result, "after": after, "payout": payout,
            "user_before_claim": list(user_before_claim),
            "user_after": list(user_after)}


CASES = (
    {"name": "paying_composition", "admin": True, "user_volume": USER_VOLUME},
    {"name": "zero_volume_claim", "admin": True, "user_volume": 0},
    {"name": "claim_without_admin_control", "admin": False,
     "user_volume": USER_VOLUME},
)

COMPARE_FIELDS = ("admin", "admin_after", "claim", "after", "payout",
                  "user_before_claim", "user_after")


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for case in CASES:
        target = run_scenario(TARGET, case)
        candidate = run_scenario(args.candidate, case)
        differences = [field for field in COMPARE_FIELDS
                       if target[field] != candidate[field]]
        rows.append({"case": case["name"], "match": not differences,
                     "differing_fields": differences,
                     "target": target, "candidate": candidate})
    receipt = {
        "scope": "Admin->claim composition: admin_update_token_incentives sets "
                 "the schedule, clock advances past a day boundary, "
                 "claim_token_incentives pays out. Signed, offline LiteSVM "
                 "only; no broadcast or live funds.",
        "target_sha256": sha(TARGET.read_bytes()),
        "candidate_sha256": sha(args.candidate.read_bytes()),
        "schedule": {"start_time": START, "end_time": END,
                     "seconds_in_a_day": PERIOD, "day_number_arg": 99,
                     "supply_per_day": SUPPLY, "admin_now": ADMIN_NOW,
                     "claim_now": CLAIM_NOW,
                     "expected_payout": EXPECTED_PAYOUT},
        "summary": {"cases": len(rows),
                    "matched": sum(row["match"] for row in rows),
                    "paying_target_payouts": [row["target"]["payout"]
                                                for row in rows]},
        "cases": rows,
        "limits": [
            "Global account is a finalized public snapshot with its authority "
            "substituted locally by a disposable signer; no live admin key.",
            "The global sol_volumes day-0 denominator (100) is patched in "
            "after the admin transaction as a synthetic volume seed, mirroring "
            "the claim fixture's synthetic schedule/vault practice.",
            "User volume accumulator and mint/user ATA come from the claim "
            "fixture's saved signed Pump lifecycle; incentive ATA is funded "
            "synthetically (1,000,000).",
        ],
    }
    args.output.write_text(json.dumps(receipt, indent=1))
    print(json.dumps(receipt["summary"], indent=1))


if __name__ == "__main__":
    main()
