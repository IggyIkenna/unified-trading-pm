---
doc_type: plan
title: DeFi CF-2/CF-3 legacy-vs-canonical cell-diff gaps — scope + backfill/relabel campaign
summary:
  Successor of data_completion_to_100_all_ag_2026_06_21.md's CF-2/CF-3 todo (operator-approved 2026-08-08, "scope it and
  dispatch") — a real ~703-date DeFi backfill/relabel campaign for dex_pools/swaps_ohlcv on UNISWAP_V2/UNISWAP_V3/CURVE
  plus lending_indices/lst_rates for named Solana protocols, first confirmed real by a 2026-07-13 CF-1..CF-14 audit and
  never actioned since (flagged in that session as "out of scope, needs a physical relabel/backfill migration"). This
  plan does the scoping pass (exact date list, exact protocol/venue cells, exact legacy-vs-canonical path shapes,
  row-count sizing) that the original finding deliberately deferred, then splits into concrete dispatch-ready
  backfill/relabel todos.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, cf-audit, backfill, relabel, legacy-canonical, dex_pools, swaps_ohlcv, lending_indices, lst_rates]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/archive/2026_07/data_completion_to_100_all_ag_history2_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-08-08
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-08
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    "operator ruling 2026-08-08 (NA-corpus blocker digest, cross-cutting round 5, id=49): 'Yes, scope it and dispatch'",
    "data_completion_to_100_all_ag_2026_06_21.md ~line 712, CF-2/CF-3 todo",
    "2026-07-13 CF-1..CF-14 audit (data_completion_to_100_all_ag_history2_2026_07_24.md ~line 490) — first confirmed the
    ~703-date gap, deliberately deferred",
  ]
context_scope:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/pipeline-mode-partition.md,
    plans/audit/results/cf_manifest_audit_all.py,
    market-tick-data-service/scripts/reshape_bybit_futures_chain_glued_to_hive_2026_07_13.py,
  ]
---

# DeFi CF-2/CF-3 legacy-vs-canonical cell-diff gaps — scope + backfill/relabel campaign

## Why this plan exists

`data_completion_to_100_all_ag_2026_06_21.md`'s CF-2/CF-3 todo has carried the SAME unscoped finding since 2026-07-13
(confirmed real: `dex_pools`/`swaps_ohlcv` gaps on `UNISWAP_V2`/`UNISWAP_V3`/`CURVE`, `lending_indices`/`lst_rates` gaps
for named Solana protocols, spanning ~703 dates) without ever being sized or split into dispatchable work — every
session since has correctly declined to "blindly fix it same-session" (it is a physical relabel/backfill migration, not
a one-line patch) but also never opened the scoping pass itself. The operator's 2026-08-08 ruling ("yes, scope it and
dispatch") authorizes exactly that next step. This plan IS the scoping pass, ending in either dispatch-ready child
todos/plans or a documented reason it still can't be scoped.

## Todos

- [ ] [DIAG] P1. **Re-run the CF-2/CF-3 checks fresh** against current defi manifest state (`plans/audit/results/`
      CF-audit tooling, or the live `uts-prod-cf-manifest-audit` Cloud Run Job output if a recent green run exists —
      check `gs://cf-manifest-audit-central-element-323112/cf_audit/` for a post-2026-07-13 run first, don't re-derive
      from scratch if a fresher one already exists) to get the CURRENT exact date list + cell list — the ~703-date
      figure is 3.5 weeks stale and defi has had material backfill activity since (Hyperliquid/Aster asset_group
      migration, dex-swaps backfills, etc. per recent Progress Log entries fleet-wide) that may have already closed some
      of the gap. Do not assume the original 703 still holds unchanged.
- [ ] [DIAG] P1. **For each of the 2 cell families, determine the exact legacy vs. canonical path SHAPES** (not just "a
      gap exists") — `dex_pools`/`swaps_ohlcv` on UNISWAP_V2/UNISWAP_V3/CURVE, and `lending_indices`/`lst_rates` for the
      named Solana protocols. Per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` Part 5 (legacy-
      COPIED-not-MOVED invariant), confirm whether these are true absences (never captured under either shape) or
      legacy-shape-only cells (data exists, just not at the canonical path) — the fix differs completely (backfill vs.
      relabel/copy). Cross-check `/codex/02-data/defi-canonical-naming-ssot.md` for the current canonical shape per
      data_type.
- [ ] [DIAG] P1. **Size the actual backfill/relabel work**: row counts, estimated Tardis/RPC cost (if any external pull
      is needed vs. a pure on-disk relabel), estimated wall-clock/VM-hours, and whether this is closer to the
      `bybit_futures_chain` glued-to-hive reshape precedent (pure relabel, in-place) or a genuine from-source backfill
      (new data pull). Cite the precedent script pattern (`market-tick-data-service/scripts/reshape_*_2026_07.py`) if
      relabel-shaped.
- [ ] [DIAG] P1. **Confirm zero live-writer/live-reader conflict** on both the legacy and canonical shapes for the
      affected dates/protocols before proposing any delete-after-relabel step (Part 3/4 of the delete-safety protocol) —
      this campaign will very likely end with a legacy-object cleanup step once relabeled, which inherits the same
      five-part-proof + `[OPERATOR]`-or-§3a-reversibility-qualified gating as every other prod delete in this corpus.
- [ ] [SCRIPT] P1. **Split into dispatch-ready child todos/plans** once the above scoping lands — likely one
      `[DATA]`/`[SCRIPT]` plan per cell-family (dex_pools/swaps_ohlcv vs. lending_indices/lst_rates), each sized under
      the 10-100 AO-todo cap, `assigned_vm: planning` if the scoped outcome is a bounded/deterministic backfill-or-
      relabel job (the normal case once real scope numbers exist), staying `NA` only for any residual judgment call the
      scoping pass itself can't resolve (e.g. a genuine cost/priority tradeoff needing another operator read).
- [ ] [DATA] P2. **Close the loop on `data_completion_to_100_all_ag_2026_06_21.md`'s original CF-2/CF-3 todo** — once
      the child plan(s) are filed and active, that todo's `[x]` closure (already flipped, citing this plan) is complete;
      this todo just confirms no further edit is owed there once dispatch is real (not just filed).

## Codex SSOTs (read before touching — plan↔codex drift is review-blocking)

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — any eventual legacy-cleanup step inherits the full
  five-part proof + hard-stop gating.
- `/codex/02-data/defi-canonical-naming-ssot.md` — canonical path shape per data_type, the target this backfill/relabel
  campaign converges on.
- `/codex/02-data/pipeline-mode-partition.md` — reader-fallback discipline if a soft alias window is needed during the
  transition.

## Progress Log

- **2026-08-08, authored** (round5-cross-cutting-audit, id=49) — operator ruled "yes, scope it and dispatch" on the
  standing, never-scoped CF-2/CF-3 finding first confirmed 2026-07-13. This plan is the scoping pass itself; nothing
  executed yet. `assigned_vm: NA` deliberately — the scope isn't known yet, so dispatch-eligibility can't be assessed
  until the DIAG todos land real numbers (per the dispatch-scope-eligibility rule: a todo is AO-eligible only once its
  outcome is a checkable, bounded fact, not "figure out how big this is").
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — all 5 open todos are the scoping pass
  itself (exact date list, cell shapes, sizing, backfill-vs-relabel classification), none of which is a bounded fact
  yet; the doc's own last todo already names the correct future action (fork into `assigned_vm: planning` child plan(s)
  once the scoping numbers exist). No cheat-sheet precedent applies pre-scoping. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- Freshly-authored (2026-08-08) scoping-only plan
  responding to an explicit operator ruling. All 6 open todos are the scoping pass itself (re-run CF-audit, determine
  path shapes, size the work, confirm writer/reader conflict, THEN split into dispatch-ready child plans) -- todo 5
  requires a judgment call sequenced after 1-4 land real numbers, so the whole doc doesn't clear the RECLASSIFY bar yet.
  Corroborated same-day by `defi_satellite_ao_dispatch_batch11_2026_08_09.md`'s fresh extraction pass, which examined
  this doc and found zero extractable items. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-15**: refreshed context_scope (6 entries) -- added `pipeline-mode-partition.md` (already named
  in this doc's own "Codex SSOTs" section but missing from context_scope) and
  `reshape_bybit_futures_chain_glued_to_hive_2026_07_13.py` (the concrete file the doc's own todo 3 names as the
  relabel-precedent pattern to cite, resolved from its `reshape_*_2026_07.py` glob reference).
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — re-confirmed; all 6 open todos are still the scoping pass itself (re-run CF-audit, determine path shapes, size the work, confirm writer/reader conflict, split into dispatch-ready child plans, close the loop on the original todo) — none is a bounded fact yet per the doc's own repeated verdicts since 2026-08-08/09. Doc stays `assigned_vm: NA`.
