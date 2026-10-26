# PumpSwap create_config checkpoint

This package executes PumpSwap `create_config` (discriminator
`c9cff3724b6f2fbd`) against its authentic historical fixture and the
modern-format extension of the same arguments, comparing the captured
original program against a fresh build of the current source. It is not
byte-identical to deployed PumpSwap and is not a deployable replacement.

`create_config` was already dispatched in `programs/pump-amm/src/lib.rs`
and its `CreateConfig` accounts struct (fixed-admin address constraint,
`space = 949`, `[b"global_config"]` PDA) already existed, matching the
static source proposal in `repro/pump_amm/create-config-source-proposal/`.
**No program source was changed for this package** — the differential ran
against the source exactly as it stands on this branch.

Two clean builds (the second from a fresh target directory) with
`cargo-build-sbf` 4.1.0 and platform-tools **v1.44** produced the identical
1,200,600-byte [candidate](candidate.so), SHA-256
`3ec8dc3a31cd3aa08dd8124bc0f08ae7844e978650c1f7c30a7a48c744aa1cce`.
[build-comparison.json](build-comparison.json) and
[second-build-comparison.json](second-build-comparison.json) bind the
source hashes (28 files), toolchain and both build logs
([build.log.gz](build.log.gz), [second-build.log.gz](second-build.log.gz)).
The captured original is 10,485,715 bytes, SHA-256
`6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7`;
first difference at byte 24, 672,430 differing positions in the shared
length. Whole-file equality is false.

## Fixture provenance

[historical-tx.json](historical-tx.json) is the full getTransaction body
of the real `create_config` transaction:

- Signature `2gNxbFQQmCsMaq7QYZkBxgeb2fcy5rsvQV9Mv9LzzoMtek9NbNWDzqqDcd4kfu8VeZFrf5FMqdeVw2YDpwJJYZTN`
- Slot 321942956, blockTime 1740069258 (2025-02-20), success, 22,276 CU
- Admin `8LWu7QM2dGR1G8nKDHthckea57bkCzXyBTAKPJUBDHo8` (the fixed admin),
  preBalance 10,000,010,020; `global_config` PDA
  `ADyA8hdefvWN2dbGGWFotbzWxrAvLW83WG6QCVXvJKqw` 0 → 3,069,360 lamports
- [admin-signature-history.json](admin-signature-history.json): the admin's
  289-signature history; this transaction is its 7th.

The 2025 event emitted by that transaction (its base64 `Program data:` log
line) is retained in the fixture and used as an authentic anchor below.

## The version gap, stated plainly

The fixture predates the captured program build, and the difference is
visible in the fixture itself:

| | 2025 transaction | Captured build (this repo) |
| --- | ---: | ---: |
| Instruction data | 280 bytes (272 argument bytes: LP fee 25, protocol fee 0, 8 recipients) | 320 bytes (adds `coin_creator_fee_basis_points`, `admin_set_coin_creator_authority`) |
| Created account space | 313 bytes (its System `create_account` inner instruction encodes space 313; funded 3,069,360 lamports = rent for 313) | 949 bytes |
| Event payload | 320 bytes | 360 bytes |

The `GlobalConfig` layout grew between the two builds; the current source
deserializer explicitly accepts the 907/940/949 legacy lengths. The honest
acceptance standard is therefore **target-vs-candidate agreement**, with
the 2025 figures used as anchors — not as the expected outputs of the
captured build.

## Differential coverage on this exact candidate

Receipt: [create-config-differential.json.gz](create-config-differential.json.gz),
from `scripts/pump_amm_create_config_differential.py`. Clock set to the
historical slot/blockTime; admin funded with its historical preBalance;
`global_config` absent. **6 cases, 6 matched** on error identity, full
watched-account pre/post states, event bytes, inner CPIs and admin lamport
delta (compute units recorded per binary, excluded from matching per this
repository's convention).

| Case | Target | Candidate |
| --- | --- | --- |
| Historical exact replay | Anchor 102 `InstructionDidNotDeserialize`, fee-only delta −5,000, no state change (CU 3,222) | identical (CU 3,222) |
| Historical data, fresh tx | Anchor 102, delta −5,000 (CU 3,222) | identical (CU 3,222) |
| Modern-format positive | **Success** — 949-byte config created (CU 21,598) | **Success** — byte-identical result (CU 21,613) |
| Wrong admin (control) | Custom 6005 `InvalidAdmin`, rolled back (CU 10,820) | identical (CU 10,835) |
| Already exists (control) | Second create fails, System Program error 0x0, config untouched (CU 5,907) | identical (CU 5,907) |
| Truncated args, 120 of 312 (control) | Anchor 102 (CU 2,989) | identical (CU 2,989) |

**Historical exact replay.** The literal v0 transaction was reconstructed
from the fixture JSON, including its original recent blockhash and its
authentic signature; the signature verifies (asserted in the script before
sending) and the VM ran with sigverify enabled (blockhash check disabled,
since the 2025 blockhash is not in the VM's bank). Both binaries reject it
with Anchor error 102: the 272 argument bytes cannot deserialize into the
captured build's 312-byte argument struct. This is the version gap above
acting, identically, on original and reconstruction — it is not a defect
in either.

**Modern-format positive.** The same historical arguments, zero-extended
with the captured build's two added arguments
(`coin_creator_fee_basis_points = 0`,
`admin_set_coin_creator_authority = 11111111111111111111111111111111`).
Both binaries succeed and produce a **byte-identical 949-byte account**
(SHA-256 `6aac056dc8ec1ce2…`), owned by the PumpSwap program, funded with
7,495,920 lamports (rent for 949 bytes); admin delta −7,500,920 including
the 5,000 fee. Decoded fields are exactly the historical values — fixed
admin, LP fee 25, protocol fee 0, the eight 2025 recipients verbatim —
with every later-added field zero. Inner CPIs are identical: System
`create_account` (7,495,920 lamports, space 949) and the event self-CPI
(368 bytes). The emitted event is 360 bytes whose **first 320 bytes equal
the authentic 2025 event byte-for-byte** (SHA-256 `94120587716b19ff…`):
same discriminator `6b34598137e25116`, same timestamp under the historical
clock, same admin, fees and recipients; the appended 40 bytes are the zero
coin-creator fee and the default authority. The event's shared prefix
matching a genuine 2025 emission is the strongest single anchor in this
package.

**Controls.** The wrong-admin control is genuinely signed by a disposable
keypair sitting in the admin position (sigverify on): both binaries fail
with `PumpAmmError::InvalidAdmin` (custom 6005), and the failed
transaction's inner instructions show the System `create_account` CPI
*before* the failure — the init-before-fixed-admin-check ordering the
static proposal documented — with full rollback (no account persists).
The already-exists control fails in the System Program (error 0x0,
account-already-exists propagated) with the created config byte-untouched.
Truncated data fails deserialization on both.

## Signature handling

The admin is always the real fixed address; it was never substituted. For
the literal replay its genuine signature is used and verified. The
constructed transactions cannot carry that signature (the keypair is not
available), so their signature slots carry placeholders and those VMs ran
with sigverify disabled — LiteSVM executes them regardless, which the
receipt records per case. The wrong-admin control, the one case where the
signer check is the point, is genuinely signed and ran with sigverify on.

## Limits

- Positive coverage is one argument vector — the historical one,
  zero-extended. Other fee/recipient combinations reach `create_config`'s
  setters only through the shared-setter evidence of the static proposal
  and the separate bounded `update_fee_config` handler corpus; they were
  not re-run here as initializer cases.
- The 2025 positive execution belongs to an earlier program build. This
  package proves the captured build and the reconstruction agree on the
  historical input (identical rejection), on its modern extension
  (identical creation, event-prefix-identical to 2025), and on all three
  controls. It does not prove the captured build ever created the live
  949-byte config on mainnet — the live account reached 949 bytes through
  later reallocating handlers as well.
- All execution is offline LiteSVM. No transaction was broadcast and no
  real funds moved.
- Full deployed-byte equality remains false; this is bounded handler
  recovery, not historical source identity.

## Proposed completion change (proposal only — NOT applied)

If this package is accepted and merged, `repro/completion.json` should
change:

- `pump_amm.create_config`: `unrecovered` → `bounded_implementation`
- Counts: bounded **142 → 143**, unrecovered **3 → 2**, partial unchanged
  at 5 (remaining unrecovered: `pump.set_mayhem_virtual_params`,
  `mayhem.initialize_mayhem_state`).

Neither `repro/completion.json` nor `repro/status.json` was edited by this
work, and nothing here was committed.
