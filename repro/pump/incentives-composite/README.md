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

> **Candidate superseded — see "Post-drift rerun (2026-10-26)" at the end of
> this file.** The `candidate.so` in this package is now the post-drift
> rebuild (1,642,400 bytes, SHA-256
> `d9f1ba066f9293bbbe407c361f3be4922c578509b7dcf8cb97a9037dd2b3c9a1`), and all
> three incentives suites plus both inherited regressions were rerun against
> it with full matches. The sections below describe the original pre-drift
> run; its receipts are unchanged and the pre-drift candidate remains in git
> history at the commit that introduced this package.

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

## Post-drift rerun (2026-10-26)

This package was ported onto the current `origin/main` tree (branch
`rea/bounded-incentives-create-config`). Between the pre-drift base and
`origin/main`, upstream changed exactly one of the 40 build-bound Pump source
files: `programs/pump/src/admin_cto.rs` (4 lines — raw `err()` codes replaced
by named `PumpError` variants carrying pubkeys, an added native-mint
quote-mint rejection, and an added holder-key creator check). Verified two
ways: the source-hash table in
[post-drift-rerun-2026-10-26/build-comparison.json](post-drift-rerun-2026-10-26/build-comparison.json)
differs from the pre-drift `build-comparison.json` in that file only, and a
direct diff of the file against the old base shows the same change. A rebuild
of the ported tree with the identical v1.44 recipe therefore cannot be
byte-identical to the pre-drift candidate: it produces a 1,642,400-byte
candidate (+1,104 bytes), SHA-256
`d9f1ba066f9293bbbe407c361f3be4922c578509b7dcf8cb97a9037dd2b3c9a1`, first
difference vs the captured original at byte 24, 913,409 differing positions
in the shared length. The rebuild was reproduced independently twice with
identical output. `candidate.so` in this package is now that binary.

All three incentives suites were rerun against the rebuilt candidate versus
the same captured original, with unchanged fixtures, case sets and expected
values (receipts in
[post-drift-rerun-2026-10-26/](post-drift-rerun-2026-10-26/)):

| Suite | Cases | Result |
| --- | ---: | --- |
| `admin_update_token_incentives` | 98 | **98 matched** — 43 successes, 55 rollbacks |
| `claim_token_incentives` | 60 | **60 matched** — 48 successes, 12 rollbacks |
| Admin→claim composition | 3 | **3 matched** — payouts 200 / 0 / 200 |

- Admin: [post-drift-rerun-2026-10-26/admin-differential.json.gz](post-drift-rerun-2026-10-26/admin-differential.json.gz),
  run with `--candidate` / `--build-comparison` pointing at the post-drift
  build receipt (no second-build comparison this run). The independent
  verifier **passes** on the new evidence:
  `{"verified": true, "signed_cases": 98, "successes": 43, "rollbacks": 55}`.
- Claim: [post-drift-rerun-2026-10-26/claim-differential.json](post-drift-rerun-2026-10-26/claim-differential.json),
  run through the same import wrapper as the pre-drift run, repointing the
  script's build-receipt constant at the post-drift build comparison. The
  claim verifier still cannot target this candidate (it hard-pins the
  historical `repro/pump/claim-token-incentives/` package); it was not run
  and not forced, same as the pre-drift run.
- Composition: [post-drift-rerun-2026-10-26/composition-differential.json](post-drift-rerun-2026-10-26/composition-differential.json).

Extra assurance, also rerun on the rebuilt candidate:
[post-drift-rerun-2026-10-26/quote-control-regression.json](post-drift-rerun-2026-10-26/quote-control-regression.json)
— **507 cases, 0 mismatches** — and
[post-drift-rerun-2026-10-26/multi-hop-regression.json](post-drift-rerun-2026-10-26/multi-hop-regression.json)
— **56 cases, 56 passed**. The quote-control harness binds a
`build-comparison.json` adjacent to the candidate file, so it was run
against the byte-identical staging copy at
`post-drift-rerun-2026-10-26/candidate.so` (kept in place so the receipt's
bound inputs resolve); the package-root `candidate.so` is the same bytes.

Conclusion: the `admin_cto.rs` drift does not leak into incentives behavior —
every compared field (errors, post-states, events, inner CPIs, payouts)
matches the captured original exactly as it did pre-drift.
`repro/completion.json` carries only the candidate path for these two
handlers (no hash), so it is unchanged; statuses and counts are untouched.
