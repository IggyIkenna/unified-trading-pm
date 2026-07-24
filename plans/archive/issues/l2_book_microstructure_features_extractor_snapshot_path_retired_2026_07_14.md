---
doc_type: issue
title:
  l2_book_microstructure_capture todo 5 targets a retired extractor architecture — no wiring path for
  queue_position/depth_levels exists
summary: >
  l2_book_microstructure_capture_2026_07_13.md todo 5 ("extend book_microstructure_feature_extractor.py's
  extract_book_microstructure_feature_dict to surface queue_position_bid/ask/book_depth_levels") targets a function and
  a data path (CanonicalBookMicrostructure raw-snapshot rows) that
  features_read_book_columns_not_snapshots_2026_06_28.md DELETED as "no-tech-debt" on 2026-06-28/29, replacing it with
  MDPS precomputed bar-level candle columns (book_summary_spec.py, L1-L5 only). The new queue_position/depth_of_book_10
  data this plan's todo 4 now produces (market-tick-data-service@ef467572) has no consumer wired to it in
  features-service — extending the named function is impossible (it no longer exists) and reintroducing raw-snapshot
  reads would reverse a deliberate, already-shipped architecture decision.
status: resolved
nature: notes
asset_group: [cefi]
stage: [features]
repos: [features-service, market-data-processing-service, market-tick-data-service]
scope: [engineer]
tags: [features, book-microstructure, premise-correction, architecture-decision]
related:
  [
    /plans/active/l2_book_microstructure_capture_2026_07_13.md,
    /plans/archive/2026_07/features_read_book_columns_not_snapshots_2026_06_28.md,
    /plans/archive/2026_07/mdps_book_microstructure_precompute_columns_2026_06_28.md,
  ]
created: 2026-07-14
parent_epic: strategy_master
priority: P2
source:
  [
    "Discovered while dispatched l2_book_microstructure_capture-005 (slot 11, 2026-07-14) — read
    features_service/cefi/book_microstructure_feature_extractor.py before extending it per the todo's instruction and
    found it no longer reads CanonicalBookMicrostructure snapshot rows at all.",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-14
locked_by:
resolved_by: operator (via BLK-e5571ccf, 2026-07-14) — Option C confirmed, Option A not authorized as a new plan yet
---

# l2_book_microstructure_capture todo 5 targets a retired extractor architecture

## What I found

Dispatched `l2_book_microstructure_capture_2026_07_13.md` todo 5: "Extend
`features-service/.../book_microstructure_feature_extractor.py` (`extract_book_microstructure_feature_dict`) to surface
`queue_position_bid`/`queue_position_ask`/`book_depth_levels` when present."

Reading the target file (`features_service/cefi/book_microstructure_feature_extractor.py`) before touching it found:

1. **The named function doesn't exist.** The extractor's public function is
   `extract_book_microstructure_from_candle_columns(candle: dict[str, float | None])`, not
   `extract_book_microstructure_feature_dict`.
2. **The whole data path changed.** Per the module's own docstring: _"Replaces the retired snapshot path
   (`CanonicalBookMicrostructure`). The 25 book-summary columns on the processed candle... carry time-weighted
   aggregates over all intra-bar `book_snapshot_5` samples; this extractor reads them directly — no book ticks needed
   downstream."_ `FORMULA_VERSION` is 2, "migrated from snapshot → bar-column path 2026-06-29".
3. **The retirement was deliberate and already shipped.** Cross-repo plan
   `features_read_book_columns_not_snapshots_2026_06_28.md` (status: complete, all 4 todos `[x]`,
   `features-service@d794b8c1`, CI green 2026-06-29) explicitly: "Delete the now-dead raw-snapshot aggregation path
   (**no-tech-debt**)" — the old extractor that consumed `CanonicalBookMicrostructure` rows (including
   `queue_position_bid/ask`/depth fields) was intentionally deleted, not just unused.
4. **The new bar-column source (MDPS) never anticipated deeper-than-L5.**
   `unified_api_contracts/internal/domain/market_data_processing/book_summary_spec.py` (the SSOT for what MDPS
   precomputes onto the candle) is explicitly scoped to `book_snapshot_5` — every depth column is
   `for level in range(1, 6)` (L1-L5 only), and the module docstring says columns are "computed per-target-timeframe
   directly from the raw `book_snapshot_5` ticks in that bar." No mention of `depth_of_book_10`/`queue_position`
   anywhere in that spec or its authoring plan (`mdps_book_microstructure_precompute_columns_2026_06_28.md`).

So this plan's todo 4 (just shipped: `market-tick-data-service@ef467572` — a `BookMicrostructureHandler` deriving
`queue_position` + `depth_levels_bid/ask`-beyond-L5 as `CanonicalBookMicrostructure` rows via
`compute_book_microstructure`, for the 5 `depth_of_book_10`-capable venues) has **no consumer wired to it anywhere in
features-service** — the only extractor that ever read that canonical shape was deleted 2 weeks before this plan was
written.

## Why it matters

Todo 5 as literally scoped is not just blocked, it targets code that doesn't exist. There are two structurally different
ways to actually surface `queue_position`/deeper-depth features, and picking between them is an architecture decision,
not an implementation detail:

- **Option A — extend the MDPS bar-column pipeline** (mirrors the pattern that already exists for L5): add
  `queue_position_bid/ask_tw_mean` and `book_{bid,ask}_qty_L{6-10}_tw_mean` (or similar) to `book_summary_spec.py`,
  teach MDPS's candle computation to aggregate the new `depth_of_book_10`/ `queue_position` captures the SAME way it
  already aggregates `book_snapshot_5`, then extend `extract_book_microstructure_from_candle_columns` to read the new
  columns (honest-null for the 5-capped venues, matching the existing per-level null rule). Keeps the single-canonical
  bar-column architecture intact — no regression of the 2026-06-28/29 decision. **Bigger scope**: touches
  `market-data-processing-service` (not in this plan's `repos:` list) + UAC schema + features-service; realistically its
  own plan.
- **Option B — read `CanonicalBookMicrostructure` snapshot rows directly** in a new, separate extractor path parallel to
  the bar-column one (NOT touching the deleted function — that's gone). Fits inside this plan's existing repo scope
  (`features-service`) and today's `queue_position` data as shipped. **Directly reverses the "no-tech-debt"
  snapshot-path deletion** — reintroduces exactly the raw-book-tick dependency
  `features_read_book_columns_not_snapshots_2026_06_28.md` removed on purpose, for one narrow feature slice.
- **Option C — do nothing here**: leave `queue_position`/deeper `depth_levels_*` as MTDS-only data (a real capability
  now, per todo 4's UAC flip) with no features-service consumer yet. Todo 5 (and the downstream
  `MarketMakingQueueMicrostructureEngine` backtest gate, held in the parent plan's Phase E1) stay honestly blocked until
  a properly-scoped MDPS extension (Option A) lands as its own plan.

## Recommended decision

**Option C now, Option A as the real follow-up.** Reintroducing a parallel snapshot-read path (Option B) to hit this
plan's narrow scope would be a deliberate architecture regression for one feature group, decided unilaterally by
whichever agent picks up todo 5 next — exactly the kind of call `/codex/12-agent-workflow/work-philosophy.md`'s
craft-scoping keeps out of a single dispatched task. Recommend: mark todo 5 blocked-on-this-issue-doc in the plan (done
below), and file a new MDPS-scoped plan (Option A) as a separate piece of work when someone picks up the
`MarketMakingQueueMicrostructureEngine` backtest gate for real — it is not on this plan's critical path today (no
backtest has been authorised yet per this plan's own todo 7).

## Resolution (2026-07-14, slot 14, BLK-e5571ccf)

Operator confirmed **Option C**: leave `queue_position`/deeper `depth_levels_*` as MTDS-only data for now, with no
features-service consumer yet. Explicitly rejected Option B (reintroducing a parallel `CanonicalBookMicrostructure`
snapshot-read path) — that would reverse the deliberate, already-shipped no-tech-debt deletion from
`features_read_book_columns_not_snapshots_2026_06_28.md` for one narrow feature slice. Option A (extend
`book_summary_spec.py` + MDPS candle aggregation to cover `depth_of_book_10`/`queue_position`, then repoint the features
extractor) is agreed as the right long-term path, but is **NOT authorized as its own plan today** — it should be scoped
only when the `MarketMakingQueueMicrostructureEngine` backtest gate is actually picked up (no backtest work is
authorized yet per `l2_book_microstructure_capture_2026_07_13.md` todo 7).

## Todos

- [x] ✅ [DESIGN] P2. Operator/main: confirm Option C (leave `queue_position` MTDS-only for now) vs. authorize a new
      MDPS-scoped plan for Option A (extend `book_summary_spec.py` + MDPS candle computation to aggregate
      `depth_of_book_10`/`queue_position` the same way `book_snapshot_5` is aggregated today, then repoint the features
      extractor). (repo: unified-trading-pm — plan decision) — **DONE: Option C confirmed via BLK-e5571ccf, see
      Resolution above.**
- [x] ✅ [SCRIPT] P3. **NOT APPLICABLE — Option A not authorized** (operator ruling 2026-07-14, `BLK-e5571ccf`): no
      MDPS-scoped plan to author today. Deferred until the `MarketMakingQueueMicrostructureEngine` backtest gate is
      actually picked up — whoever picks that up then authors `mdps_book_microstructure_deeper_depth_columns_<date>.md`
      scoping the `book_summary_spec.py` extension + MDPS aggregation change + the features-service extractor follow-on,
      depends_on this issue doc. Closing this todo now (rather than leaving it open) so it stops being redispatched —
      re-opening requires a fresh operator decision when the backtest gate is actually picked up, tracked as a new
      plan/todo at that time, not this one re-firing. (repo: unified-trading-pm)
