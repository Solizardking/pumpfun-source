# pumpfun-source

<<<<<<< ours
Source code for pump.fun

**Verified checkpoint progress**

| Program | Matched windows | Matched % | Raw-equal bodies | Normalized only | Unmatched | Whole meaningful ELF equal |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| [Pump Main](programs/pump/README.md) |1,020/1,035|98.6%|188|832|15|No|
| [PumpSwap / AMM](programs/pump-amm/README.md) |785/785|100.0%|785|0|0|**Yes**|
| [Fees](programs/pump-fees/README.md) |585/585|100.0%|585|0|0|**Yes**|
| [Mayhem](programs/mayhem/README.md) |441/441|100.0%|441|0|0|**Yes**|
| [Donation Relay](repro/donation-relay/canonical-exact-selection/README.md) |492/492|100.0%|492|0|0|**Yes**|
| **Total** |**3,323/3,338**|**99.6%**|**2,491**|**832**|**15**|**4/5**|

Matched windows cover **5,045,232/5,213,128 code bytes (96.8%)**.
Raw equality compares complete instruction bytes. Normalized windows mask
specified call/address operands and do not prove whole-program identity.
These counts describe the selected maintained recipes; they are not a
percentage of engineering work completed.

The [reconstruction toolchain](reconstruction/README.md) rebuilds `programs/pump` and
scores it against the captured original in `evidence/original/`.

<!-- app-progress:start -->
## Application source and feature progress

As of **2026-10-28**. The [app workspace](app/README.md) contains the SDK, frontend and independent API-compatible backend. [PRD](app/PRD.md) · [Detailed ledger](app/contracts/feature-progress.json) · [Validation](app/evidence/validation.json).

Source acquisition/extraction is separate from editable feature reconstruction and working behavior. Percentages below use explicit counts or accepted milestones; they are not estimates of engineering effort. The original backend source is unavailable.

| Source / evidence measure | Complete / inventoried | Progress | Meaning |
| --- | ---: | ---: | --- |
| Published SDK source | 31 / 31 files | 100% | Exact npm 4.3.1 source bytes; full behavior parity still unqualified |
| Frontend JavaScript capture | 648 / 648 scripts | 100% | Known scripts in the captured route/asset graph only |
| Frontend factory extraction | 5947 / 5947 inventoried variants | 100% | Extracted factories, not original source files; authenticated/unseen modules unknown |
| Public developer API contract | 67 / 67 documented operations | 100% | Specification captured; native compatibility 0 / 67 (0%) |
| Original backend source | Not observable | N/A | Implement replacement behavior from API evidence |

**Feature scoring:** source = contract/dependency mapping, editable logic, and required adapters (3 milestones). Completion = source accepted, successful behavior, failure/auth states, and UI or data consistency checks (4 milestones). A milestone needs evidence to count. Stubs, 501 responses and historical fixture replay earn no feature credit. N/A needs an explicit applicability decision.

### Backend features

| Feature family | Static API leads¹ | Native source readiness | Feature completion | Reviewed state |
| --- | ---: | ---: | ---: | --- |
| Identity / authentication | 30 | 0/3 (0%) | 0/4 (0%) | Original auth, sessions and authorization unavailable. |
| Profiles / follow graph | 70 | 0/3 (0%) | 0/4 (0%) | Local GET /profiles/verified projects daily leaders to full profiles; production PnL, identity policy and authorization remain unqualified. Family milestones remain pending. |
| Feed / posts / callouts | 39 | 0/3 (0%) | 0/4 (0%) | No native content handlers or persistence. |
| Market discovery / search | 35 | 0/3 (0%) | 0/4 (0%) | One dated price fixture; no native discovery or price service. |
| Leaderboards / competitions | 27 | 0/3 (0%) | 0/4 (0%) | No native ranking, PnL or competition logic. |
| Livestream / presence | 9 | 0/3 (0%) | 0/4 (0%) | LiveKit configuration observed; no native orchestration. |
| Coin creation / media | 4 | 0/3 (0%) | 0/4 (0%) | No upload or metadata lifecycle; SDK source is tracked separately. |
| Rewards / fees / referrals | 12 | 0/3 (0%) | 0/4 (0%) | No native reward accounting or claims. |
| Portfolio / indexing | 17 | 0/3 (0%) | 0/4 (0%) | Opt-in materialized spot positions and user trade/transfer-history reads exist; contract/feature completion stays pending. No local chain indexer, financial derivation, production compatibility or reorg handling. |
| Settings / notifications | 29 | 0/3 (0%) | 0/4 (0%) | No native preferences, notification or messaging handlers. |

¹ 330 distinct static operation candidates overall. Family leads overlap, lack confirmed origin bindings and may include privileged/excluded paths; do not sum them or treat them as a full API denominator. The 67 public developer operations currently have **0% native compatibility qualification**: `content.read` 0/18, `graph.read` 0/17, `leaderboards.read` 0/11, `moderation.read` 0/1, `positions.read` 0/7, `profiles.read` 0/13.

### Frontend features

| Feature family | Reconstructed source readiness | Feature completion | Reviewed state |
| --- | ---: | ---: | --- |
| Shared layout / navigation | 3/3 (100%) | 3/4 (75%) | Evidence-mapped responsive shell, navigation, search URL state and failure boundaries pass browser tests. The shared search dialog also reads five hash-bound synthetic profiles through the maintained user-search adapter. Live search, full original runtime and visual parity remain unqualified; milestone statuses are unchanged. |
| Home / feed | 3/3 (100%) | 3/4 (75%) | Evidence-mapped, hash-bound synthetic examples, strict local validation and honest For You/Following boundaries pass unit and browser tests. Native feed compatibility, authenticated personalization and original visual parity remain unqualified. |
| Explore / search | 3/3 (100%) | 3/4 (75%) | Authenticated one-record historical snapshot, fail-closed adapter and offline name/symbol/mint search pass unit and browser tests. Native market discovery, production ranking and original visual parity remain unqualified. |
| Leaderboards / competitions | 3/3 (100%) | 2/4 (50%) | Contract-driven read-only interface and failure paths verified. Live API success and original visual parity remain unqualified. |
| Live discovery / playback | 3/3 (100%) | 3/4 (75%) | Authenticated five-record historical discovery snapshot, fail-closed evidence adapter and local search/selection states pass unit and browser tests. Current livestream state, native API compatibility, playback, presence and original visual parity remain unqualified. |
| GO | 3/3 (100%) | 3/4 (75%) | Authenticated 25-record historical bounty snapshot, fail-closed evidence adapter, local search/filter/sort/cursor state and unavailable account actions pass unit and browser tests. Current API compatibility, authenticated flows, mutations and original visual parity remain unqualified. |
| Mayhem | 3/3 (100%) | 2/4 (50%) | Evidence-mapped state filters, sorting, strict validation and fail-closed offline states pass unit and browser tests. No archived Mayhem response, qualified live API compatibility or original visual parity is claimed. |
| Holder rewards | 3/3 (100%) | 3/4 (75%) | Published-SDK PDA derivation now offers an explicit read of public SOL/token holdings through the existing mainnet RPC service. Holdings do not establish account existence, eligibility, accrued or claimable rewards. Claims and original visual/API parity remain unavailable or unqualified. See packages/frontend/HOLDER-PUBLIC-BALANCES.md. |
| Create coin / upload | 3/3 (100%) | 3/4 (75%) | Evidence-mapped offline metadata drafting, validation, local image preview and failure states pass browser tests. Upload, wallet signing, transaction creation, token launch and original visual parity remain unqualified. |
| Profiles / social graph | 3/3 (100%) | 3/4 (75%) | Evidence-mapped, hash-bound synthetic profiles resolve by exact user id or wallet and render filtered authored posts and separate local follow-graph lists with profile navigation. Native profile/graph compatibility, authenticated behavior and original visual parity remain unqualified; no milestone status changes for this addition. |
| Authentication / wallets | 0/3 (0%) | 0/4 (0%) | Sign-in remains unavailable. An opt-in Wallet Standard public-address connection/forget workflow is implemented with source witnesses and local protocol/UI tests; it supplies no authentication, signing or persisted identity. See packages/frontend/PUBLIC-WALLET-EVIDENCE.md. Full original auth/wallet parity remains pending. |
| Portfolio / positions | 3/3 (100%) | 3/4 (75%) | Live mainnet SOL, SPL Token and Token-2022 account reads pass unit, browser and actual-RPC checks. Pump positions/PnL compatibility and original visual parity remain unqualified. |
| Settings / notifications | 0/3 (0%) | 0/4 (0%) | No local settings or notification UI. |
| Legal / fee information | 3/3 (100%) | 3/4 (75%) | Authenticated archived fee, privacy and terms documents now render through a fail-closed offline adapter with responsive navigation and corruption tests. Current legal authority and original visual parity remain unqualified. |

**Excluded (N/A, outside every feature denominator):** Support/Intercom; Terminal/Padre; Native/mobile app and app promotion; Individual coin/token detail pages; /pump-token ($PUMP).
**Deferred (N/A):** Perps/Hyperliquid; Separate PumpSwap/revenue/GO microsites.

All app percentages above are generated by `python3 app/scripts/progress.py` from the checked-in evidence and feature ledger. Verify freshness with `python3 app/scripts/progress.py --check`. Source capture is bounded by the recorded snapshot; original frontend source completeness and the full internal API surface remain unknown.
<!-- app-progress:end -->

## License

Repository code and documentation are [MIT licensed](LICENSE). Third-party
sources and artifacts retain their original licenses and ownership.
=======
Deployment evidence and reconstruction tooling for the official Pump.fun Solana
programs. **Byte-for-byte source reconstruction is not complete.** Experimental executables now contain recovered handlers with pinned candidate build recipes,
but the implementations remain partial and all whole-program comparisons differ.

Verified captures include Pump, PumpSwap, Pump Fees and Mayhem, plus five separately
deployed dependencies. Each capture preserves the entire account payload, including
allocation padding, with SHA-256, finalized observation slots and available loader
metadata. See [scope and hashes](docs/SCOPE.md).

```sh
python3 scripts/verify_evidence.py
python3 scripts/test_tooling.py
```

A partial Rust fee-tier selector now matches the original instruction sequence except
for unresolved relocations with platform-tools v1.43, and passes 1,215 local
differential cases. Recovered quote-mint routing additionally passes 9,428 original-program
queries, but its compiled instructions still differ. All 31 Fees instruction bodies pass 17,461 SBF comparison receipts; forty-eight recovered Pump
handlers plus five partial creation/trading paths pass 9,269. Thirty-seven PumpSwap
handlers pass 17,462 comparisons, and twenty-four Mayhem handlers pass 9,595. These
53,787 saved comparisons cover 140 implemented handlers and five partial paths, not the
complete programs. The Fees total includes 69 repeated-input checks with stronger log or signature assertions. Two Fees handlers are deprecated dispatches that always reject.
The current [Pump buy-order checkpoint](repro/pump/buy-mode-order-fortyeight/README.md) restores complete-before-cashback rejection order in the admitted buy path. Its entire executable differs from the preceding fee-basis build at nine bytes, all within buy; exact-quote is raw-unchanged. All 9,269 differential and 1,024 Surfpool comparisons pass, with no new cases. The inspected existing fixtures do not cover simultaneous complete/cashback flags or divergent mint/curve supplies. Whitelist admission, broader settlement and whole-original identity remain incomplete.
The current Pump `sell_v2` has a confirmed quote transfer-fee minimum-output and event mismatch; its saved passes do not cover that boundary.
The current PumpSwap checkpoint corrects the earlier zero-fee cashback event mismatch;
the [signed negative probe](repro/pump_amm/legacy-sell-zero-fee-gap/README.md) preserves evidence against the prior executable.
The current [AMM accumulator-order checkpoint](repro/pump_amm/accumulator-order-v144/README.md) puts the accumulator user-field assignment after successful Clock retrieval, as in the captured original. Its clean main executable and symbols equal the tested scratch build; all 17,462 existing comparisons and 35,418 saved signature checks pass. The full inventory still has 310 unmatched original windows. Scalar specialization, recipient diagnostics, transitive data, authentic initializer success and whole ELF identity remain unresolved.

The [controlled compiler comparison](repro/pump_fees/compiler-family/CONTROLLED-HELPER-REPORT.md)
favors platform-tools v1.44 among the tested Fees builds: two complete runtime
helper bodies match the capture exactly. The current Fees candidate uses that
compiler. The [previous retained Fees build](repro/pump_fees/all-thirtyone-v144/README.md)
also passed 112 independent Surfpool comparisons with 224 signed local transactions.
The current [Fees V2 caller checkpoint](repro/pump_fees/v2-caller-v144/README.md) composes quote admission, remaining-account preprocessing, generated AMM/Pump V2 CPIs, payout filtering/rescaling and early serialization. All 17,461 existing comparisons and the separate ten-step sequence pass; a clean main build matches the tested executable and symbols. Five original windows gain normalized matches, leaving 130 unattributed and two conflicting windows. Whole-file identity, complete caller/parser/error/cleanup equivalence and the security audit remain incomplete.

The current [Mayhem swap-sell typed-error checkpoint](repro/mayhem/sell-result-error-twentyfour/README.md) restores the typed zero-divisor error in SellPumpSwap, following the prior buy correction. All 9,595 functional comparisons pass; 61 diagnostic rows remain explicit. Saved verification checks 13,284 retained transaction strings and 26,500 signatures; 19,190 remains the recorded/derived signed-execution count. Both clean main builds equal their tested scratch executables and symbols.

[Recovery status](docs/RECOVERY.md) separates observed evidence from unresolved work. The [twenty-third layered pass](repro/layered-passes/pass-23/README.md) records the latest fixes, complete byte differences, function/call/data inventories and the next source obligations.
The [completion and remaining-work ledger](docs/COMPLETION.md) enumerates all 150 instruction dispositions: 140 bounded implementations (93.3%), five partial and five unrecovered. Whole-binary completion remains 0/4; this is not a 93.3% overall completion estimate.
[Parallel worker results and concurrency configuration](docs/PARALLEL_WORK.md) document the completed CLI research waves, focused follow-ups and configured concurrency.
[Tooling](docs/TOOLING.md) covers recapture, disassembly and strict candidate comparison.
The [migration attribution](docs/MIGRATION_RAYDIUM_CUTOVER.md) records the Raydium-to-PumpSwap cutover of 2025-03-20 with on-chain anchors.
The [security assessment](audit/AUDIT.md) remains incomplete. Local validation
includes 393 malformed-input checks and 30 signed offline lifecycle transactions;
these bounded checks do not establish full security or differential coverage.
Zero confirmed findings does not establish security.

The SPL Token dependency now has a fresh Linux source build matching the entire
captured 108,600-byte payload. [Build evidence](repro/pump/verified-spl-token/README.md)
is separate from the still-unmatched four Pump.fun programs. Token2022 also has a
[verified fresh source build](repro/pump/verified-token-2022/README.md), including
explicitly regenerated zero allocation padding.

Original bytes live under `evidence/`, never as rebuilt artifacts. This project
contains no on-chain deployment or transaction-broadcast tooling; the imported
signed test harness submits only to offline loopback simulators. Upstream IDLs retain their
original authorship; this repository does not assert a license over Pump's materials.

The [integrated research lab](research/README.md) supplies pinned Pump.fun lifecycle
fixtures, signed offline replay harnesses, receipt verifiers and an explicitly
incomplete 31-handler Fees scaffold. Its import provenance and validation status
are separate from source-reconstruction claims.

The prior [AMM formatter checkpoint](repro/pump_amm/formatter-restoration-v144/README.md) restores the evidenced stack-buffer base58 and checked UTF-8 algorithm in a narrowly patched dependency. All 17,462 unchanged comparisons and 35,418 saved signatures pass; the clean main build equals scratch. Four more original function windows match under the existing normalization, leaving 306 unmatched at that checkpoint (the current claim checkpoint has302). Full original byte identity and historical dependency identity remain unresolved.

The prior [Relay IDL header checkpoint](repro/donation-relay/source-build-09-idl-owned/README.md) restores the reviewed I/O-to-owned-error path. The unchanged12 ordinary cases and all saved signature/effect checks pass. Complete source is bound by [current.json](repro/donation-relay/current.json);369 original windows and whole-file identity remain unresolved.

The latest [Fees withdrawal checkpoint](repro/pump_fees/withdraw-owned-error-v144/README.md) restores missing-option-only, origin-free error conversion. The [AMM claim context checkpoint](repro/pump_amm/claim-context-v144/README.md) restores original account ownership and inline storage. Both clean main builds equal their tested executables and symbols. Unchanged corpora pass; whole-original equality remains incomplete.

The [sixteenth layered pass](repro/layered-passes/pass-16/README.md) restores full BondingCurve decoding and mutation/log order in three Pump creator paths, plus AMM claim overflow-before-mutation order. Both main builds exactly reproduce their tested executables and symbols. Core byte identity remains0/4; the [complete remaining-work report](repro/layered-passes/pass-16/REMAINING.md) retains every mismatch.

The [seventeenth layered pass](repro/layered-passes/pass-17/README.md) restores the AMM Claim self-transfer predicate, Fees sharing missing-pool error ownership, and Relay IDL header-read owned errors. Main/scratch builds and unchanged corpora are verified; all whole-core originals still differ.

The [eighteenth layered pass](repro/layered-passes/pass-18/README.md) restores AMM Sync ownership and its no-change log, Fees' four-reserve graduation predicate, and Relay's owned missing-discriminator error. AMM now has300 unmatched original windows. The unchanged corpora and main/scratch identities pass; all four original core binaries still differ.

The [nineteenth layered pass](repro/layered-passes/pass-19/README.md) restores Pump admin-CTO typed curve state, AMM initializer user ownership, and Fees late account-check/state-exit order. All existing corpora pass; AMM retains297 unmatched original windows. Whole original byte identity remains0/4.

The [twentieth layered pass](repro/layered-passes/pass-20/README.md) restores Pump owned CTO error metadata, Fees first typed CPI ownership, and AMM logical module provenance. All three main builds equal tested scratch artifacts;0/4 core originals match. Upstream history is reconciled with excluded executions retained.

[Pass21](repro/layered-passes/pass-21/README.md) restores Pump owned6083 and the second typed Fees Pump CPI, with exact main/scratch identity. Concurrent helper-default integrity failures are preserved and narrowly reconciled through explicit-version AST proof; byte identity remains0/4.

[Pass22](repro/layered-passes/pass-22/README.md) integrates five CTO owned errors, the final two typed sharing CPIs and Relay owned3002, with full artifact/input proofs. Complete original identity remains0/4; the next proven Fees admin-or-creator authorization gap is explicitly retained.

[Pass23](repro/layered-passes/pass-23/README.md) restores the proved sharing admin-or-creator guard and plain rejection ownership. All existing cases and exact main/scratch identity pass; admin-only runtime coverage is zero, and core original identity remains0/4.
>>>>>>> theirs
