---
doc_type: issue
title: Solana dex_pool_swaps (ORCA/RAYDIUM) has no existing data source — new-capability scope
summary: >
  mvp_backfill_defi_onchain_v10_2026_06_27.md G1.6 found that dex_pool_swaps for ORCA and RAYDIUM cannot be filled by
  any existing MTDS code path: SolanaDefiHandler only captures dex_pool_state (current pool/vault snapshots via REST),
  DexSwapsHandler's Solana routing always resolves to no subgraph (get_subgraph_id returns None for these venues, since
  they are REST-API venues with no subgraph), and the ORCA/RAYDIUM live WS connectors (orca_defi_ws.py /
  raydium_defi_ws.py) are Jupiter-quote PRICE pollers, not swap-event capture. Filling this data_type genuinely needs
  new capability - an on-chain Solana swap-event indexer - not a VM launch or a config change. This doc scopes that
  capability (design starting point + a concrete, reusable precedent already in this codebase) so a future plan can pick
  it up sized correctly, rather than attempting it inline in a 1-hour backfill-verification task.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, solana, dex-pool-swaps, new-capability, scoping, orca, raydium]
related:
  [
    plans/archive/2026_08/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/solana_defi_fake_history_snapshot_2026_06_17.md,
  ]
created: 2026-07-12
author: unknown
parent_epic: mtds_mdps_master
priority: P2
source: [plans/archive/2026_08/mvp_backfill_defi_onchain_v10_2026_06_27.md G1.6, slot-2 2026-07-12]
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-20
locked_by:
context_scope:
  [
    /plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md,
    /plans/active/solana_dex_pool_swaps_indexer_2026_08_08_finalize.md,
    /plans/archive/2026_08/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /plans/archive/issues/solana_defi_fake_history_snapshot_2026_06_17.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
  ]
resolved_by:
---

# Solana dex_pool_swaps (ORCA/RAYDIUM) — new-capability scope

## What I found

Confirmed (re-reading the code, not re-deriving the G1.6 finding): three existing paths were checked and none produce
individual swap events for ORCA/RAYDIUM on Solana.

1. `market_tick_data_service/cli/handlers/solana_defi_handler.py` (`SolanaDefiHandler`,
   `--operation collect-solana-defi`) via `_solana_defi_fetch.py` captures **`dex_pool_state` only** — periodic REST
   snapshots of the current pool/vault set (`fetch_orca`, `fetch_raydium`, `fetch_kamino_vault`). No per-trade/per-swap
   output.
2. `DexSwapsHandler` (the generic EVM-chain swap handler) resolves protocol→chain via UAC
   `get_supported_chains_for_protocol()`, a `SUBGRAPH_IDS`-only lookup. ORCA/RAYDIUM have no subgraph entry (they're
   REST-API venues, not subgraph-indexed) so this always returns `[]` and the per-protocol loop `continue`s — dead code
   for these two venues specifically.
3. `market_tick_data_service/live/connectors/{orca,raydium}_defi_ws.py` — these are Jupiter
   `lite-api.jup.ag/swap/v1/quote` PRICE-QUOTE pollers (emit a price tick per poll interval), not swap-transaction
   capture. Confirmed by reading `orca_defi_ws.py`'s docstring + poll loop directly — no swap/trade event is ever parsed
   or emitted.

**Conclusion: building `dex_pool_swaps` for these two venues requires a genuine on-chain Solana swap-event indexer**
(parse ORCA Whirlpool / Raydium AMM swap instructions from transaction logs), not a config fix, VM relaunch, or
connector rewire.

## A reusable precedent already exists in this codebase

> **CORRECTED 2026-08-12 (/plan-reconcile)**: `build_drift_v2_sig_index.py` (and its test suite) no longer exist —
> deleted 2026-07-16 by the DRIFT/PACIFICA retirement, so it is no longer a _live_ precedent script; the design pattern
> below is preserved for reference only. The actual current state of this generalization work (recovered via
> `git show 2e674d1f~1:...` as a design reference, extracted into the chunk-flush/resume core) is tracked content-wise
> in `plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md` (its todo 1, `[x]` DONE) — see that doc rather than
> assuming this script is present on disk.

`market_tick_data_service/scripts/build_drift_v2_sig_index.py` (657 lines) already solves HALF of this exact problem for
a different Solana program (Drift V2 perps): it walks Helius RPC `getSignaturesForAddress` for a program address from
HEAD backwards, chunk-flushing `(signature, slot, blockTime)` tuples to GCS parts (`_index/<program>_sig_index_parts/`)
with `--resume` support seeded from the oldest already-indexed signature — avoiding the OOM class this codebase hit
before (tens of millions of sigs held in RAM). This pattern generalizes directly:

- **Program addresses already registered in UAC**
  (`unified_api_contracts/registry/capability_declarations/_defi_chain_data.py`):
  `raydium.program_id = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"`,
  `orca.program_id = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"` — no new address discovery needed.
- **What `build_drift_v2_sig_index.py` does NOT do** (the other half of this capability, not yet built anywhere): it
  only indexes signatures + blockTime, it does not fetch/parse the actual transaction to extract a swap event (amounts,
  direction, pool/pair, price). A dex_pool_swaps indexer needs a SECOND stage: for each indexed signature, fetch the
  full transaction (`getTransaction` via Helius), decode the Whirlpool/Raydium AMM swap instruction's account + data
  layout into `(pool, base_amount, quote_amount, side, price)`, and write via
  `ManifestWriter.record_captured(..., data_type="dex_pool_swaps", ...)` following the same
  `pipeline_mode`/honest-absence conventions the rest of this asset_group already uses.

## Why this is scoped as its own capability, not folded into a backfill task

- It's a multi-stage build (sig-index walk → per-tx fetch+decode → manifest write), each stage with its own failure
  modes (Helius rate limits, instruction-layout parsing correctness, OOM-safety at scale) — the same "smoke-first, don't
  fan out blind" caution that governs every other new-venue integration in this workspace.
- Instruction decoding for an AMM program is protocol-specific (Whirlpool's swap instruction layout differs from
  Raydium's) — this is genuinely new adapter code per venue, not a shared script extension.
- `mvp_backfill_defi_onchain_v10_2026_06_27.md`'s own G2 gate text already excludes this (`dex_pool_swaps` for
  ORCA/RAYDIUM is a known, separately-tracked gap — see that plan's G1.6 + Progress Log entries) — closing this doc's
  scope is what lets that gate's language stay accurate rather than silently drop the two venues from consideration.

## Recommended next step

File a dedicated implementation plan (repo: `market-tick-data-service`) when this becomes a priority, sized as
`brand-new` (1.0× estimate calibration, per this workspace's estimate-calibration table) given it's genuinely new
adapter capability, not a refactor or config change. Suggested todo breakdown for that future plan:

1. Generalize `build_drift_v2_sig_index.py` (or extract its chunk-flush/resume core into a shared helper) to accept an
   arbitrary program address, so ORCA/RAYDIUM reuse the exact same OOM-safe sig-walk instead of a second bespoke
   implementation.
2. Build the per-signature transaction fetch + instruction decoder for Whirlpool swaps (start here — Orca's swap
   instruction layout is simpler/better-documented than Raydium's CLMM/CPMM variants).
3. Same for Raydium (may need to branch on AMM version — legacy AMM vs CLMM vs CPMM each have a different swap
   instruction shape).
4. Wire the decoded swap records through `ManifestWriter.record_captured(data_type="dex_pool_swaps")` with the same
   honest-absence conventions (`EXPECTED_PRE_VENUE_LAUNCH` pre-genesis, etc.) the `dex_pool_state` path already
   established.
5. Backfill VM launch + G2 re-verification once shipped.

## Open actions

- [x] ✅ [DESIGN] P3. **DONE 2026-08-08 (operator ruling: prioritize it now).** Authored the dedicated implementation
      plan per the breakdown above -- `/plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md`
      (`assigned_vm: planning`, 5 todos, `sequential: true`) + its gated companion
      `/plans/active/solana_dex_pool_swaps_indexer_2026_08_08_finalize.md`. The indexer itself is not built yet (that
      plan's own scope); this doc's sole open item is now closed by citation.
- [ ] [DOCS] P3. **Archive this scoping doc** once `/plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md` +
      `/plans/active/solana_dex_pool_swaps_indexer_2026_08_08_finalize.md` complete — the finalize plan's own
      reconciliation todo owns this closure (see the 2026-08-08 Progress Log entry below); this todo just makes that
      already-stated intent a tracked item instead of prose, per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2.

## Progress Log

- **round5-na-digest-defi 2026-08-08 (apply pass, item 74)**: operator ruled "yes, prioritize it now" -- authored the
  dedicated implementation plan (`solana_dex_pool_swaps_indexer_2026_08_08.md`) per this doc's own 5-step breakdown,
  plus its gated finalize companion. Closed this doc's sole open todo by citation (see above). This issue doc now has 0
  open todos -- flagged for the finalize plan's own reconciliation todo to archive it once the implementation plan
  completes, per `task_template.md`'s "also check each SOURCE doc" rule; not archived immediately here since the
  finalize-plan pattern owns that step.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - sole todo is 'author a dedicated implementation plan when this
  becomes a priority' — plan-authoring + prioritisation, both operator calls
- **context-scout 2026-08-03**: reviewed context_scope (4 entries), no change needed — still accurate.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdict re-affirmed) —
  sole open item ("author a dedicated implementation plan when this becomes a priority") remains a plan-authoring
  timing/prioritization call, an operator judgment, not a bounded task. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently; no content change
  since the 2026-08-04 audit (context-scout metadata only, per git log). Sole open item remains a plan-authoring
  timing/prioritization call, an operator judgment, not a bounded task. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — 0 open todos (the sole item was closed
  by citation today via `round5-na-digest-defi 2026-08-08`, operator ruling "prioritize it now": the dedicated
  implementation plan `solana_dex_pool_swaps_indexer_2026_08_08.md` was authored, `assigned_vm: planning`, gated
  finalize companion included). This scoping doc's own work is done; the real dispatchable build lives in that new plan
  pair, not here. Not archived this pass. Nothing to reclassify.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA-STALE (already-duplicated) — the doc's 1 open checkbox
  ([DOCS] P3, archive-once-complete) is the exact same closing action already tracked, verbatim, as todo 2 of the active
  `solana_dex_pool_swaps_indexer_2026_08_08_finalize.md` (gated on the implementation plan, currently 2/5 todos done).
  Flipping `assigned_vm` here would dispatch a duplicate of that finalize todo. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-16** [body-hash:af9008fe203a4904]: KEEP-NA-STALE (already-duplicated), re-confirmed -- doc unchanged since the 2026-08-09 verdict. Sole open item (line ~135, archive-this-doc trigger) is the identical closing action already tracked as todo 2 of the active solana_dex_pool_swaps_indexer_2026_08_08_finalize.md; citation already correct and current. No action needed.

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-17 (defi tranche, dispatch agt-f4fef7)**: KEEP-NA-STALE (already-duplicated),
  re-confirmed — doc unchanged since the 2026-08-16 verdict (context-scout metadata touch only). Sole open item
  (archive-this-doc trigger) is still the identical closing action tracked as todo 2 of the active
  `solana_dex_pool_swaps_indexer_2026_08_08_finalize.md`; citation still correct and current. No action needed.
- **na-eligibility-audit 2026-08-18** (defi tranche, dispatch agt-2c8a26): KEEP-NA-STALE (already-duplicated),
  reconfirmed — content-hash change since 2026-08-17 was plan_reconciler's same-day hygiene fix (removed a stray
  leftover "N." template token between a checkbox and its tag), not a substantive edit. Sole open item unchanged;
  citation to `solana_dex_pool_swaps_indexer_2026_08_08_finalize.md` todo 2 still correct and current. No action
  needed.

- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
