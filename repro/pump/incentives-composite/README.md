# Pump incentives composite checkpoint

This package composes the two bounded token-incentive source slices onto the
current Pump source on the `rea/incentives-composite` branch:
`admin_update_token_incentives` (`programs/pump/src/incentives.rs`) and
`claim_token_incentives` (`programs/pump/src/token_incentives/`), dispatched
from `programs/pump/src/lib.rs` alongside the existing 48 bounded handlers and
the partial trade/creation paths. It is not byte-identical to deployed Pump
and is not a deployable replacement.

Two isolated clean builds (the second from a fresh target directory) with
`cargo-build-sbf` 4.1.0 and platform-tools **v1.44** produced the identical
1,641,296-byte [candidate](candidate.so), SHA-256
`d4e22cd5af1ae1b3a207b363188785a25cfb87fd01d37e5834d61b0f20d3fdcf`.
[build-comparison.json](build-comparison.json) and
[second-build-comparison.json](second-build-comparison.json) bind the source
hashes (40 files), toolchain and both build logs
([build.log.gz](build.log.gz), [second-build.log.gz](second-build.log.gz)).
The captured original is 10,485,715 bytes, SHA-256
`7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`; first
difference at byte 24, 912,723 differing positions in the shared length.
Whole-file equality is false.

## Source change made during the build

The ported claim handler referenced `PumpError::ReconstructionBranchUnsupported`,
which does not exist in this source tree — the variant lives on the separate
local `ReconstructionError` enum (`src/lib.rs`, `= 110`, the same convention
every other reconstruction-limit site uses). Seven references in
`programs/pump/src/token_incentives/claim_token_incentives.rs` were repointed
to `crate::ReconstructionError::ReconstructionBranchUnsupported` and the
now-unused `PumpError` import was dropped. No logic, accounts, arithmetic or
error codes changed. This was the only source edit; everything else compiled
as ported.

## Differential coverage on this exact candidate

| Suite | Cases | Result |
| --- | ---: | --- |
| `admin_update_token_incentives` | 98 | **98 matched** — 43 successes, 55 rollbacks |
| `claim_token_incentives` | 60 | **60 matched** — 48 successes, 31 payouts, 12 rollbacks |
| Admin→claim composition | 3 | **3 matched** — payouts 200 / 0 / 200 |

- Admin: [admin-differential.json.gz](admin-differential.json.gz), run with
  `--candidate` / `--build-comparison` / `--second-build-comparison` pointing
  at this package. Its independent verifier
  (`scripts/pump_admin_token_incentives_verify.py`, same arguments) **passes**:
  `{"verified": true, "signed_cases": 98, "successes": 43, "rollbacks": 55}`.
- Claim: [claim-differential.json](claim-differential.json). The script's
  build-receipt constant was repointed to this package's build-comparison via
  an import wrapper (the historical claim package is untouched). The claim
  verifier **cannot** target this candidate: it hard-pins the historical
  `repro/pump/claim-token-incentives/` reproducibility and inherited-regression
  files, which assert the earlier slice candidate's hash. It was not run and
  not forced.
- Composition: [composition-differential.json](composition-differential.json)
  from the new `scripts/pump_incentives_composition_differential.py` — in one
  LiteSVM instance, the admin transaction sets the schedule on a zeroed
  accumulator (start 1000, end 3900, 100-second days, 1,000/day), the clock
  advances to day 1, and claim pays `floor(20 × 1000 / 100) = 200`. Compared
  fields: admin post-state, claim outcome, payout, user-accumulator
  transitions, events, inner CPIs and all watched post-states. The
  zero-volume case claims successfully with no payout and no event; the
  control claims the same 200 against a pre-existing schedule with no admin
  transaction.

## Inherited regressions actually rerun on this candidate

- Quote-control fresh differential
  ([quote-control-regression.json](quote-control-regression.json)):
  **507 cases, 0 mismatches**.
- Native-curve / multi-hop harness
  ([multi-hop-regression.json](multi-hop-regression.json),
  `repro/pump/native-curve-partial-fortyeight/harness/pump_multi_hop_curve_differential.py --candidate`):
  **56 cases, 56 passed**.

Not rerun on this composite: the maintained 7,957-case Pump suites,
holder-distribution (649), nested-create (48) and the 1,024 Surfpool
comparisons. The 8099 packages' counts for those suites bind their own
candidates, not this one.

## Limits

- Admin fixtures use a finalized public Global snapshot with its authority
  substituted locally by a disposable signer; this does not prove live
  admin-key possession or all reachable incentive schedules.
- Claim and composition fixtures use synthetic schedule/volume state and a
  synthetically funded canonical incentive ATA; in the composition the global
  day-0 `sol_volumes` denominator (100) is patched in after the admin
  transaction, mirroring the claim fixture's practice. Reachability of the
  exact composed state through live trading is not proven.
- All execution is signed, offline LiteSVM. No transaction was broadcast and
  no real funds moved.
- Full deployed-byte equality remains false; this is bounded handler
  recovery, not historical source identity.

## Completion change (applied 2026-10-26, owner-approved)

`repro/completion.json` was updated with this package:

- `pump.admin_update_token_incentives`: `unrecovered` → `bounded_implementation`
- `pump.claim_token_incentives`: `unrecovered` → `bounded_implementation`
- Counts: bounded **140 → 142**, unrecovered **5 → 3**, partial unchanged at 5
  (remaining unrecovered: `pump.set_mayhem_virtual_params`,
  `pump_amm.create_config`, `mayhem.initialize_mayhem_state`).

`repro/status.json` was intentionally not edited: its Pump entry still binds
the prior main checkpoint candidate, and this composite does not replace that
binding.
