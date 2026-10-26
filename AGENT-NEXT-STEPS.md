# AGENT NEXT STEPS — pumpfun-source, from 143/150

You are picking up the pump.fun reverse-engineering reconstruction
(`Solizardking/pumpfun-source`). This file tells you exactly where the work
stands and how to take the next lanes. Read it fully before starting.

## Where things stand (2026-10-26)

- **Landing status:** the bounded-handler work below lives on the branch
  `rea/bounded-incentives-create-config`, pending PR merge. Until that PR
  lands, `main`'s `repro/completion.json` still reads **140 bounded /
  5 partial / 5 unrecovered**; this branch carries the updated accounting:
  **143 bounded / 5 partial / 2 unrecovered of 150 handlers; 0/4 whole
  binaries byte-identical.** Bounded means: signed LiteSVM differential
  receipts against the captured original ELF — nothing else counts.
- Just landed on this branch (study these checkpoints before starting;
  they are the template for yours):
  - Pump `admin_update_token_incentives` + `claim_token_incentives` —
    `repro/pump/incentives-composite/` (candidate `d4e22cd5…`; admin 98/98,
    claim 60/60, admin→claim composition 3/3, quote-control 507/507,
    native-curve 56/56).
  - PumpSwap `create_config` — `repro/pump_amm/create-config/` (candidate
    `3ec8dc3a…`; 6/6 cases against the authentic 2025-02-20 transaction
    `2gNxbFQQmCsMaq7QYZkBxgeb2fcy5rsvQV9Mv9LzzoMtek9NbNWDzqqDcd4kfu8VeZFrf5FMqdeVw2YDpwJJYZTN`,
    slot 321942956).
- Captured original ELFs: `evidence/original/<program>/deployed.so` with
  `capture.json` hashes. Verify before trusting: pump `7a19affa…`,
  pump_amm `6a7ad345…`, mayhem `a87fa9f8…`, pump_fees in its capture file.
- This repo is a **partial reconstruction for reference — not deployable
  code**, and it never will be presented as such.

## The only two unrecovered handlers left

### Lane A — mayhem `initialize_mayhem_state` (disc `9dbd5e485545cc2d`)

Owner: _(unclaimed — write your name + date here, in your branch, first)_

- No official IDL. Ghidra decompilations are retained at
  `repro/pump/mayhem-signer-boundary/ghidra-initialize-{wrapper,body}.txt`
  (wrapper `0x80ef0`, parser `0x692f8`, body `0x82938`; body shows state
  init + Clock helper, no direct Pump CPI).
- `MayhemState` layout is already recovered in
  `programs/mayhem/src/state.rs` (fields at offsets 8/16/24/56/72/88/89/97/98).
- Authentic fixtures exist: two finalized mainnet Pump `create_v2` txs
  (slots **461114637**, **461115028**) that CPI into this handler, saved
  with verified signatures in
  `repro/pump/mayhem-signer-boundary/mainnet-createv2-traces.json.gz`.
- Job: write the handler from the Ghidra body, build the mayhem candidate,
  replay both traces in LiteSVM original-vs-candidate, compare the
  initialized state bytes, watched post-states, events, CPIs, outcomes.
  This initializer does NOT need any signer bypass — Pump signs via CPI in
  the real traces.
- Checkpoint target: `repro/mayhem/initialize-mayhem-state/`.

### Lane B — pump `set_mayhem_virtual_params` CPI sweep (disc `3da9bcbf99952a61`)

Owner: _(unclaimed — write your name + date here, in your branch, first)_

- Static recovery is COMPLETE and sealed at
  `repro/pump/mayhem-virtual-params-static/`. Do not redo it.
- The runtime blocker is structural: account 0 (`sol_vault_authority`) must
  sign, and it is Mayhem's `sol-vault` PDA
  `BwWK17cbHxwWBKZkUYvzxLcNQ1YVyaFezduWbtm2de6s` (bump 253) — only Mayhem
  can sign it, via `invoke_signed`. Direct calls fail ConstraintSigner 2002.
  No Mayhem handler is yet known to call this selector; the retained traces
  (2× create_v2, 1 buy CPI, 1 sell CPI) do NOT contain it.
- Job: a Ghidra/static sweep of all 25 Mayhem handlers' CPI targets for
  the selector `3da9bcbf99952a61` and any `invoke_signed` path to pump with
  the sol-vault seeds. Deliver a coverage table (handler → CPI targets →
  selector present? → evidence offsets). **A documented negative —
  "unreachable in captured code paths" — is a complete, acceptable
  outcome.** Do NOT fabricate a signer or a fixture.
- Checkpoint target: `repro/pump/mayhem-virtual-params-cpi-sweep/` (or an
  extension of the existing static package).

## How to work (the rules that produced everything above)

1. **Branch + worktree per lane, off current `main`:**
   `git worktree add ~/workspace/<lane-dir> -b rea/<lane-slug> main`
   Never commit to another agent's branch. Never work two lanes in one
   worktree.
2. **Toolchain — exact, no substitutes:** `cargo-build-sbf` (Agave) with
   `--tools-version v1.44`; PATH needs `~/.local/share/solana/bin` and
   `~/.cargo/bin`. Platform-tools v1.44 downloads once to
   `~/.cache/solana/v1.44`. The machine-default toolchain (v1.54) produces
   different binaries — do not use it, and do not silently fall back if
   v1.44 fails; report the exact failure.
   ⚠️ `/tmp` is a small (512 MB) tmpfs here: put cargo target dirs on the
   workspace filesystem, NOT /tmp, or builds die with "No space left".
3. **Python:** `solders==0.27.1` per `requirements.txt`
   (`from solders.litesvm import LiteSVM`). A working venv may exist at
   `~/workspace/pumpfun-incentives/.venv` — reuse it read-only or create
   your own inside your worktree.
4. **Two clean builds, identical hash.** Every candidate is built twice
   (second from a fresh target dir); the two SHA-256s must match before
   any differential result counts. Save `candidate.so`, build-comparison
   files, and gzipped build logs in your checkpoint package.
5. **Offline only.** LiteSVM/Surfpool simulation. No broadcast, no real
   funds, no mainnet writes. RPC use is read-only archaeology (that is
   how the create_config fixture was found: the fixed admin
   `8LWu7QM2dGR1G8nKDHthckea57bkCzXyBTAKPJUBDHo8` has only 289 signatures —
   paging an involved low-activity address beats paging a hot PDA).
   Note: `getAccountInfo` + `minContextSlot` does NOT give historical
   state (verified the hard way) — don't build a method on it.
6. **No synthetic signer bypass, no foreign signatures, no substituted
   authorities** — except exactly where a prior checkpoint documents the
   technique and its limits (e.g. substituted authority inside a copied
   account snapshot for the admin-incentives differential; placeholder
   signatures with sigverify off for the fixed-admin create_config case,
   where the historical tx itself was also replayed with its authentic
   signature). If your lane needs a signer you cannot legitimately
   produce, that is a documented finding, not a wall to tunnel through.
7. **Accounting is central.** Do NOT edit `repro/completion.json` or
   `repro/status.json`. Write the status change you believe you earned as
   a PROPOSAL section in your checkpoint README. The primary agent
   verifies receipts and applies accounting on `main` at merge time.
8. **Checkpoint README style:** copy the shape of
   `repro/pump/incentives-composite/README.md` — scope, fixture
   provenance, candidate hash/size, two-build identity, per-case results,
   explicit limits (what was NOT proven), signature handling stated
   plainly, proposed completion change. Disclose every source change and
   every harness bug you hit and fixed; prior checkpoints do this and
   yours must too.
9. **Commits:** author `Shaw <shawmakesmagic@gmail.com>` (env vars are
   fine), message subject naming the handler + outcome, body with the
   numbers. Push your branch when the checkpoint is complete; merges to
   `main` happen after review, `--no-ff`, one lane at a time.
10. **Landing convention:** this repo lands work by pull request against
    `main` (see the recent PRs #60–#70). The branch
    `rea/bounded-incentives-create-config` is the vehicle for the
    incentives + create_config accounting described above — open the PR
    from it rather than pushing to `main` directly. The same applies to
    your lane: branch, push, PR.

## Report format (when you finish a lane)

Lane · outcome (bounded-earned / documented-negative / blocked-with-
evidence) · candidate sha256 + size · case counts (matched/total, with
the success/rollback split) · checkpoint path · branch + commit hash ·
anything that did not work, stated plainly. Numbers without receipts
don't count.

## Pointers

- Full original plan for all five lanes:
  `PARALLEL.md` (in the launchpad goal's hidden files, kept by the
  primary agent; Lanes "incentives" and C/create_config are DONE and
  merged — this file supersedes it for what remains).
- Design work that builds on this repo (Metaplex agent integration,
  multi-venue agent launchpad): `AGENT-INTEGRATION-DESIGN-2026-10-26.md`
  and `AGENT-VENUES-ADDENDUM-2026-10-26.md` in the same goal folder. If
  you are asked to build the launchpad, start there: pump `create_v2`
  takes `creator` as a plain Pubkey argument (Asset Signer PDA works as
  creator today), and fee collection is a permissionless crank.
- The gating unknown for the launchpad work: whether `setAgentTokenV1`
  accepts a non-Genesis mint. That is a devnet experiment, not a
  research question — it is Step 0 in the venues addendum.
