"""Offline PumpSwap create_config target/candidate differential.

The fixture is the authentic historical create_config transaction (signature
2gNxbFQQ..., slot 321942956, 2025-02-20) retained in
repro/pump_amm/create-config/historical-tx.json. That transaction was built
for the February 2025 program build: 272 argument bytes (lp fee, protocol
fee, eight recipients), a 313-byte GlobalConfig and a 320-byte event. The
captured original ELF in this repository is a later build whose
create_config takes two more arguments (coin_creator_fee_basis_points,
admin_set_coin_creator_authority), creates a 949-byte account and emits a
360-byte event. Cases therefore cover both the literal historical replay
(target/candidate agreement is the standard) and the modern-format
zero-extension of the same historical arguments, whose first 320 event
bytes must equal the authentic 2025 event bytes under the historical clock.

No transaction is broadcast and no real funds are used. The admin account
is always the real fixed address 8LWu7QM2...; it is never substituted.
"""

import argparse
import base64
import gzip
import hashlib
import json
import re
import struct
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.hash import Hash
from solders.instruction import AccountMeta, CompiledInstruction, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message, MessageHeader, MessageV0
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.transaction import Transaction, VersionedTransaction


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "evidence/original/pump_amm/deployed.so"
PKG = ROOT / "repro/pump_amm/create-config"
CANDIDATE = PKG / "candidate.so"
BUILD = PKG / "build-comparison.json"
SECOND_BUILD = PKG / "second-build-comparison.json"
FIXTURE = PKG / "historical-tx.json"
OUTPUT = PKG / "create-config-differential.json.gz"

AMM = Pubkey.from_string("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
SYSTEM = Pubkey.default()
DISCRIMINATOR = bytes.fromhex("c9cff3724b6f2fbd")
ERROR = re.compile(r"InstructionErrorCustom\((\d+)\)")
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
# Deterministic disposable signer used ONLY in the wrong_admin control, where
# it sits in the admin position precisely so the fixed-address check can fire.
WRONG_ADMIN = Keypair.from_seed(bytes([231]) * 32)


def sha(raw):
    if isinstance(raw, Path):
        raw = raw.read_bytes()
    return hashlib.sha256(raw).hexdigest()


def receipt_path(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def b58decode(text):
    num = 0
    for char in text:
        num = num * 58 + B58_ALPHABET.index(char)
    pad = len(text) - len(text.lstrip("1"))
    body = num.to_bytes((num.bit_length() + 7) // 8, "big") if num else b""
    return b"\x00" * pad + body


def b58encode(raw):
    num = int.from_bytes(raw, "big")
    text = ""
    while num:
        num, rem = divmod(num, 58)
        text = B58_ALPHABET[rem] + text
    return "1" * (len(raw) - len(raw.lstrip(b"\x00"))) + text


def load_fixture():
    doc = json.loads(FIXTURE.read_text())
    message = doc["transaction"]["message"]
    meta = doc["meta"]
    keys = [Pubkey.from_string(key) for key in message["accountKeys"]]
    ix = message["instructions"][0]
    data = b58decode(ix["data"])
    assert data[:8] == DISCRIMINATOR, data[:8].hex()
    assert Pubkey.find_program_address([b"global_config"], AMM)[0] == keys[1]
    assert Pubkey.find_program_address([b"__event_authority"], AMM)[0] == keys[4]
    event_lines = [line.split("Program data: ", 1)[1] for line in
                   meta["logMessages"] if line.startswith("Program data: ")]
    assert len(event_lines) == 1
    inner = []
    for group in meta["innerInstructions"]:
        for item in group["instructions"]:
            inner.append({
                "program": str(keys[item["programIdIndex"]]),
                "accounts": [str(keys[idx]) for idx in item["accounts"]],
                "data_hex": b58decode(item["data"]).hex(),
            })
    return {
        "signature": doc["transaction"]["signatures"][0],
        "slot": doc["slot"], "block_time": doc["blockTime"],
        "keys": keys, "header": message["header"],
        "recent_blockhash": message["recentBlockhash"],
        "instruction": {"program_id_index": ix["programIdIndex"],
                        "accounts": ix["accounts"], "data": data},
        "pre_balances": meta["preBalances"], "post_balances": meta["postBalances"],
        "historical_event_base64": event_lines[0],
        "historical_event": base64.b64decode(event_lines[0]),
        "historical_inner": inner,
        "historical_compute_units": meta["computeUnitsConsumed"],
        "historical_logs": meta["logMessages"],
    }


FIX = load_fixture()
ADMIN = FIX["keys"][0]
GLOBAL_CONFIG = FIX["keys"][1]
EVENT_AUTHORITY = FIX["keys"][4]
ADMIN_PRE_BALANCE = FIX["pre_balances"][0]
HISTORICAL_ARGS = FIX["instruction"]["data"][8:]
assert len(HISTORICAL_ARGS) == 272
# Modern-format zero extension: same historical arguments plus the two
# arguments the captured (later) build added, at their zero values.
MODERN_DATA = (DISCRIMINATOR + HISTORICAL_ARGS + struct.pack("<Q", 0) + bytes(32))
assert len(MODERN_DATA) == 320
EPOCH = FIX["slot"] // 432000


def config_fields(data):
    def key(offset):
        return b58encode(data[offset:offset + 32])
    return {
        "space_bytes": len(data),
        "discriminator_hex": data[:8].hex(),
        "admin": key(8),
        "lp_fee_basis_points": struct.unpack_from("<Q", data, 40)[0],
        "protocol_fee_basis_points": struct.unpack_from("<Q", data, 48)[0],
        "disable_flags": data[56],
        "protocol_fee_recipients": [key(57 + 32 * i) for i in range(8)],
        "coin_creator_fee_basis_points": struct.unpack_from("<Q", data, 313)[0],
        "admin_set_coin_creator_authority": key(321),
        "whitelist_pda": key(353),
        "reserved_fee_recipient": key(385),
        "mayhem_mode_enabled": bool(data[417]),
        "reserved_fee_recipients": [key(418 + 32 * i) for i in range(7)],
        "is_cashback_enabled": bool(data[642]),
        "buyback_fee_recipients": [key(643 + 32 * i) for i in range(8)],
        "buyback_basis_points": struct.unpack_from("<Q", data, 899)[0],
        "boost_authority": key(907),
        "boost_enabled": bool(data[939]),
        "creator_fee_configurable": bool(data[940]),
        "max_configurable_creator_fee_bps": struct.unpack_from("<Q", data, 941)[0],
    }


def snapshot(vm, addresses):
    result = {}
    for name, key in addresses.items():
        account = vm.get_account(key)
        result[name] = None if account is None else {
            "pubkey": str(key), "lamports": account.lamports,
            "owner": str(account.owner),
            "data_base64": base64.b64encode(bytes(account.data)).decode(),
            "data_sha256": sha(bytes(account.data)),
            "data_len": len(account.data),
            "executable": account.executable,
        }
    return result


def new_vm(binary, sigverify):
    vm = LiteSVM().with_sigverify(sigverify).with_blockhash_check(False) \
        .with_log_bytes_limit(None)
    vm.add_program_from_file(AMM, str(binary))
    vm.set_clock(Clock(FIX["slot"], FIX["block_time"], EPOCH, EPOCH + 1,
                       FIX["block_time"]))
    vm.set_account(ADMIN, Account(ADMIN_PRE_BALANCE, b"", SYSTEM))
    return vm


def execute(vm, transaction, watched):
    before = snapshot(vm, watched)
    result = vm.send_transaction(transaction)
    error = str(result.err()) if hasattr(result, "err") else None
    meta = result.meta() if error else result
    match = ERROR.search(error or "")
    after = snapshot(vm, watched)
    keys = [str(key) for key in transaction.message.account_keys]
    inner = []
    for group in meta.inner_instructions():
        for item in group:
            compiled = item.instruction()
            inner.append({
                "program": keys[compiled.program_id_index],
                "accounts": [keys[idx] for idx in compiled.accounts],
                "data_hex": bytes(compiled.data).hex(),
            })
    created = after["global_config"]
    return {
        "error": error,
        "error_code": int(match.group(1)) if match else None,
        "success": error is None,
        "before": before, "after": after,
        "admin_lamport_delta": (after["admin"]["lamports"]
                                - before["admin"]["lamports"]),
        "events_base64": [line.split("Program data: ", 1)[1] for line in
                          meta.logs() if line.startswith("Program data: ")],
        "inner_instructions": inner,
        "compute_units": meta.compute_units_consumed(),
        "relevant_logs": [line for line in meta.logs() if "Instruction:" in line
                          or "Error" in line or "failed" in line
                          or "panicked" in line],
        "created_config": None if created is None else {
            "owner": created["owner"], "lamports": created["lamports"],
            "data_sha256": created["data_sha256"],
            "fields": config_fields(base64.b64decode(created["data_base64"])),
        },
    }


WATCHED = {"admin": ADMIN, "global_config": GLOBAL_CONFIG,
           "event_authority": EVENT_AUTHORITY}


def historical_transaction():
    header = FIX["header"]
    compiled = CompiledInstruction(FIX["instruction"]["program_id_index"],
                                   FIX["instruction"]["data"],
                                   bytes(FIX["instruction"]["accounts"]))
    message = MessageV0(
        MessageHeader(header["numRequiredSignatures"],
                      header["numReadonlySignedAccounts"],
                      header["numReadonlyUnsignedAccounts"]),
        FIX["keys"], Hash.from_string(FIX["recent_blockhash"]), [compiled], [])
    signature = Signature.from_string(FIX["signature"])
    transaction = VersionedTransaction.populate(message, [signature])
    assert all(transaction.verify_with_results())
    return transaction


def constructed_transaction(vm, data, admin_key, signer, placeholder=None):
    """Equivalent/modern transaction: fresh VM blockhash. When signer is None
    the signature slot carries a placeholder (the real admin keypair is not
    available); the VM used for those cases runs with sigverify disabled and
    that fact is recorded in the receipt."""
    # Five accounts, in the historical instruction's order; the fifth is the
    # program itself, appended by Anchor's event-CPI accounts layout.
    metas = [AccountMeta(admin_key, True, True),
             AccountMeta(GLOBAL_CONFIG, False, True),
             AccountMeta(SYSTEM, False, False),
             AccountMeta(EVENT_AUTHORITY, False, False),
             AccountMeta(AMM, False, False)]
    message = Message.new_with_blockhash([Instruction(AMM, data, metas)],
                                         admin_key, vm.latest_blockhash())
    if signer is None:
        return Transaction.populate(message, [placeholder or Signature.default()])
    return VersionedTransaction(message, [signer])


def run_case(binary, case):
    kind = case["kind"]
    if kind == "historical_exact":
        vm = new_vm(binary, sigverify=True)
        transaction = historical_transaction()
        outcome = execute(vm, transaction, WATCHED)
        outcome["signature_verified"] = True  # asserted in the builder
        outcome["transaction_base64"] = base64.b64encode(
            bytes(transaction)).decode()
        return outcome
    if kind == "already_exists":
        vm = new_vm(binary, sigverify=False)
        first = execute(vm, constructed_transaction(
            vm, MODERN_DATA, ADMIN, None), WATCHED)
        vm.expire_blockhash()
        # A distinct placeholder signature is required: LiteSVM deduplicates
        # on the first signature, and both transactions would otherwise carry
        # the same all-zero placeholder and read as AlreadyProcessed.
        second_placeholder = Signature.from_string(b58encode(bytes([7]) * 64))
        second = execute(vm, constructed_transaction(
            vm, MODERN_DATA, ADMIN, None, placeholder=second_placeholder),
            WATCHED)
        return {"first": first, "second": second,
                "signature_handling": "zero placeholder signature; sigverify disabled"}
    sigverify = kind == "wrong_admin"
    vm = new_vm(binary, sigverify=sigverify)
    if kind == "wrong_admin":
        vm.set_account(WRONG_ADMIN.pubkey(),
                       Account(ADMIN_PRE_BALANCE, b"", SYSTEM))
        watched = {"admin": WRONG_ADMIN.pubkey(),
                   "global_config": GLOBAL_CONFIG,
                   "event_authority": EVENT_AUTHORITY,
                   "real_admin": ADMIN}
        transaction = constructed_transaction(vm, MODERN_DATA,
                                              WRONG_ADMIN.pubkey(), WRONG_ADMIN)
        outcome = execute(vm, transaction, watched)
        outcome["signature_verified"] = all(transaction.verify_with_results())
        return outcome
    data = {"modern_positive": MODERN_DATA,
            "historical_data_equivalent": FIX["instruction"]["data"],
            "truncated_args": MODERN_DATA[:8 + 120]}[kind]
    transaction = constructed_transaction(vm, data, ADMIN, None)
    outcome = execute(vm, transaction, WATCHED)
    outcome["signature_handling"] = (
        "admin is the real fixed address; signature slot carries a zero "
        "placeholder because the admin keypair is not available, and this "
        "VM ran with sigverify disabled (LiteSVM default in this repo's "
        "harness is sigverify on only for genuinely signed cases)")
    outcome["signature_verified"] = False
    return outcome


CASES = [
    {"name": "historical_exact_replay", "kind": "historical_exact",
     "note": "Literal reconstruction of the 2025-02-20 v0 transaction, "
             "including its authentic signature (verified before send) and "
             "its original recent blockhash (blockhash check disabled)."},
    {"name": "historical_data_equivalent", "kind": "historical_data_equivalent",
     "note": "Historical 280-byte instruction data in a fresh transaction."},
    {"name": "modern_format_positive", "kind": "modern_positive",
     "note": "Historical arguments plus the captured build's two added "
             "arguments at zero values (coin_creator_fee_basis_points=0, "
             "admin_set_coin_creator_authority=default)."},
    {"name": "wrong_admin", "kind": "wrong_admin",
     "note": "Control (i): disposable signer in the admin position, modern "
             "data, genuinely signed (sigverify on). Must fail."},
    {"name": "already_exists", "kind": "already_exists",
     "note": "Control (ii): modern create succeeds, the identical second "
             "create in the same VM must fail."},
    {"name": "truncated_args", "kind": "truncated_args",
     "note": "Control (iii): modern data truncated to 120 argument bytes. "
             "Must fail."},
]

COMPARE_FIELDS = ("error", "error_code", "success", "before", "after",
                  "admin_lamport_delta", "events_base64",
                  "inner_instructions", "created_config")


def compare(case_name, target, candidate):
    if case_name == "already_exists":
        diffs = []
        for part in ("first", "second"):
            for field in COMPARE_FIELDS:
                if target[part][field] != candidate[part][field]:
                    diffs.append(f"{part}.{field}")
        return diffs
    return [field for field in COMPARE_FIELDS if target[field] != candidate[field]]


def main(candidate=CANDIDATE, build_path=BUILD, output=OUTPUT,
         second_build_path=SECOND_BUILD):
    candidate, build_path, output = map(Path, (candidate, build_path, output))
    build = json.loads(build_path.read_text())
    assert sha(TARGET) == build["comparison"]["original_sha256"]
    assert sha(candidate) == build["comparison"]["candidate_sha256"]
    clean_rebuild = None
    second_build_path = Path(second_build_path)
    if second_build_path.exists():
        second = json.loads(second_build_path.read_text())
        assert second["comparison"]["candidate_sha256"] == sha(candidate)
        assert second["source_sha256"] == build["source_sha256"]
        assert second["selected_toolchain"] == build["selected_toolchain"] == "v1.44"
        clean_rebuild = {"comparison_path": receipt_path(second_build_path),
                         "comparison_sha256": sha(second_build_path),
                         "candidate_sha256": second["comparison"]["candidate_sha256"],
                         "source_hashes_equal": True, "toolchain_equal": True}
    assert str(GLOBAL_CONFIG) == "ADyA8hdefvWN2dbGGWFotbzWxrAvLW83WG6QCVXvJKqw"
    assert str(ADMIN) == "8LWu7QM2dGR1G8nKDHthckea57bkCzXyBTAKPJUBDHo8"
    rows = []
    for case in CASES:
        target = run_case(TARGET, case)
        recovered = run_case(candidate, case)
        diffs = compare(case["name"], target, recovered)
        rows.append({"case": case["name"], "note": case["note"],
                     "match": not diffs, "differing_fields": diffs,
                     "target_compute_units": (
                         target.get("compute_units") or
                         target.get("second", {}).get("compute_units")),
                     "candidate_compute_units": (
                         recovered.get("compute_units") or
                         recovered.get("second", {}).get("compute_units")),
                     "target": target, "candidate": recovered})
        print(case["name"], "match:", not diffs, "diffs:", diffs)
    modern = next(row for row in rows if row["case"] == "modern_format_positive")
    event_anchor = None
    if modern["target"]["events_base64"]:
        modern_event = base64.b64decode(modern["target"]["events_base64"][0])
        event_anchor = {
            "historical_2025_event_bytes": len(FIX["historical_event"]),
            "modern_event_bytes": len(modern_event),
            "first_320_bytes_equal_historical_event": (
                modern_event[:320] == FIX["historical_event"]),
            "historical_event_sha256": sha(FIX["historical_event"]),
            "modern_event_sha256": sha(modern_event),
        }
    report = {
        "scope": "PumpSwap create_config only; offline LiteSVM target/candidate "
                 "differential against the authentic 2025-02-20 fixture and "
                 "its modern-format zero extension",
        "target_sha256": sha(TARGET), "candidate_sha256": sha(candidate),
        "candidate_path": receipt_path(candidate),
        "build_comparison_path": receipt_path(build_path),
        "build_comparison_sha256": sha(build_path),
        "second_clean_build": clean_rebuild,
        "fixture": {
            "path": receipt_path(FIXTURE), "sha256": sha(FIXTURE),
            "signature": FIX["signature"], "slot": FIX["slot"],
            "block_time": FIX["block_time"],
            "admin_pre_balance": FIX["pre_balances"][0],
            "historical_post_balances": FIX["post_balances"],
            "historical_global_config_lamports": FIX["post_balances"][1],
            "historical_instruction_data_bytes": len(FIX["instruction"]["data"]),
            "historical_event_bytes": len(FIX["historical_event"]),
            "historical_inner_instructions": FIX["historical_inner"],
            "historical_compute_units": FIX["historical_compute_units"],
        },
        "event_anchor": event_anchor,
        "programs": {"pump_amm": str(AMM), "system": str(SYSTEM)},
        "accounts": {"admin": str(ADMIN), "global_config": str(GLOBAL_CONFIG),
                     "event_authority": str(EVENT_AUTHORITY)},
        "summary": {"cases": len(rows),
                    "matched": sum(row["match"] for row in rows)},
        "cases": rows,
        "limits": "The February 2025 transaction predates the captured program "
                  "build: it carries 272 argument bytes, a 313-byte config and "
                  "a 320-byte event, while the captured build defines 312 "
                  "argument bytes, a 949-byte config and a 360-byte event. "
                  "The modern positive case is therefore the zero extension "
                  "of the historical arguments, not a byte-identical replay. "
                  "Constructed transactions keep the real fixed admin "
                  "address but cannot carry its signature (keypair "
                "unavailable); those VMs ran with sigverify disabled, while "
                  "the literal historical replay and the wrong-admin control "
                  "ran with sigverify enabled and genuinely verified "
                  "signatures. Compute units are recorded per binary but "
                  "excluded from matching, following this repository's "
                  "differential convention. No broadcast or real funds.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(report, separators=(",", ":")) + "\n").encode()
    output.write_bytes(gzip.compress(encoded, mtime=0) if output.suffix == ".gz"
                       else encoded)
    print(json.dumps(report["summary"], indent=2))
    print("event_anchor:", json.dumps(event_anchor))
    if not all(row["match"] for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    parser.add_argument("--build-comparison", type=Path, default=BUILD)
    parser.add_argument("--second-build-comparison", type=Path,
                        default=SECOND_BUILD)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    main(args.candidate, args.build_comparison, args.output,
         args.second_build_comparison)
