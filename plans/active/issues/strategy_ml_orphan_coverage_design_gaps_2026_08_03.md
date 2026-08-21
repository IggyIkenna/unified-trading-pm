---
doc_type: issue
title:
  "3 remaining ml/strategy orphan-coverage gaps investigated (todo 3c) — none are buildable as a mechanical sweep port;
  each is an operator-facing manifest-WRITE / dead-code decision, not a wiring task"
summary: >-
  Todo 3c of mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md asked for a design + wire pass on 3
  deferred gaps: (a) strategy_orders/strategy_positions/strategy_pnl, (b) backtest_results, (c) ml_models/
  ml_model_metadata/ml_training_artifacts. Investigated all 3 by reading every write call site (not guessing at shape).
  Conclusion for all 3: orphan-sweep tooling cannot be meaningfully built yet — (a) has NO live writer at all (dead
  code, zero production callers), (b) has NO manifest of any kind to diff against (genuinely untracked, confirmed by
  reading every write method), (c) has a live writer but zero manifest coverage by either omission or design (already
  surfaced by todo 3b's real VM run). Each needs an operator-facing decision (wire-up-or-delete for (a); a
  manifest-WRITE design pass for (b)/(c)) before a sweep is buildable — building one now would be a mechanical port onto
  a shape that doesn't exist, exactly what this parent doc's own text warned against.
status: open
nature: issue
asset_group: [cefi, defi, tradfi]
stage: [data]
repos: [strategy-service, ml-service, unified-trading-pm]
scope: [engineer, admin]
tags: [orphan, manifest-completeness, strategy, ml, dead-code, design-gap, operator-decision]
related:
  [
    /plans/archive/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/archive/issues/ml_strategy_manifest_coverage_gap_2026_08_03.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: "2026-08-03"
author: unknown
last_updated: "2026-08-09" # bumped by plan_reconciler Phase -1 (real last-touch per git log; field was 1+ week stale)
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Surfaced 2026-08-03 (slot 14) picking up todo 3c of mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md.
resolved_by:
locked_by:
locked_since:
context_scope: [/plans/archive/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md, /plans/archive/issues/ml_strategy_manifest_coverage_gap_2026_08_03.md, /codex/02-data/orphan-object-detection.md, strategy-service/strategy_service/engine/core/cloud_strategy_storage.py, strategy-service/strategy_service/engine/core/gcs_storage_service.py, ml-service/ml_service/training/app/core/training_orchestrator.py]
depends_on: []
---

# 3 ml/strategy orphan-coverage gaps investigated — each needs an operator decision, not a sweep port

## What I found

### (a) `strategy_orders`/`strategy_positions`/`strategy_pnl` — DEAD CODE, no live writer

`CloudStrategyStorage` (`strategy-service/strategy_service/engine/core/cloud_strategy_storage.py:76-78`) constructs 3
`DataSink`s via `get_data_sink(routing_key="strategy_orders"/"strategy_positions"/"strategy_pnl")` and exposes
`store_orders_batch`/`store_positions`/`store_pnl`. Grepped every call site in the repo (excluding tests):

- `store_positions` / `store_pnl`: **zero callers anywhere** in `strategy-service/strategy_service/`.
- `store_orders_batch`: exactly ONE caller, `OrderBatchStorage.__init__`/`.store()`
  (`engine/core/order_batch_storage.py:104`). `OrderBatchStorage` itself is **never instantiated** outside its own unit
  tests (`grep -rn "OrderBatchStorage(" strategy-service/ --include=*.py"` returns only
  `tests/unit/test_order_batch_storage*.py`, each with `cloud_storage=None` — the GCS path is never even exercised by
  the tests that do exist).

Both files (`cloud_strategy_storage.py`, `order_batch_storage.py`) date to the repo's first commit (2026-03-07,
`e3749572`) and have received maintenance commits since (e.g. `90e00bb1` threaded `job_id` into the manifest write) —
this is not abandoned WIP, it is code that has been kept alive without ever being wired to a real caller.

Separately, even if a real caller existed: strategy-service's Cloud Run deployment
(`deployment-service/terraform/services/strategy-service/gcp/main.tf:197-224`) sets `STRATEGY_BUCKET_CEFI`/`_TRADFI`/
`_DEFI` + read/write GCS-FUSE mounts, but **no `PROTOCOL_DATA_SINK_BACKEND` or `PROTOCOL_DATA_SINK_BUCKET*` env var at
all**. `get_data_sink()`'s own default (`unified-trading-library/.../cloud_interface/factory.py:469-471`) is
`p = os.environ.get(PROTOCOL_DATA_SINK_BACKEND, "local")` — with no bucket passed either, this resolves to
`LocalDataSink()` (ephemeral local write), not GCS, in the one deployment config this repo defines for the service.

A THIRD PATH_REGISTRY divergence, same class as todo 3/3b's `ml_predictions`/`strategy_instructions` findings:
`PATH_REGISTRY["strategy_orders"].path_template` (`unified-trading-library/.../config_interface/paths/registry.py:179`)
declares `"strategy_orders/by_date/day={date}/strategy_id={strategy_id}/"`, but the real writer call —
`get_data_sink(routing_key="strategy_orders")` with no `prefix=` kwarg,
`.write(df, partition={"day":..., "strategy_id":...})` — resolves to `StorageDataSink(bucket, prefix="")`, and
`_build_partition_path` (`cloud_interface/providers/ protocol_impls.py:23-29`) sorts partition keys alphabetically
(`day` before `strategy_id`) with NO prefix segment prepended — i.e. **bucket-root**
`day={date}/strategy_id={strategy_id}/{uuid}.parquet`, not `strategy_orders/by_date/...`. Confirmed by code reading only
(never live-verified — there is no live writer to verify against).

**Decision needed, not a wiring task**: is this corpus meant to be live (needs a real caller + explicit
`PROTOCOL_DATA_SINK_BUCKET_STRATEGY_ORDERS`-class deployment config + a PATH_REGISTRY fix mirroring todo 3b's), or is it
dead tech debt that should be deleted (`store_positions`/`store_pnl` entirely, `store_orders_batch` +
`OrderBatchStorage` if execution-service's order-fill simulation genuinely moved onto a different path — worth checking
against `strategy_instructions`, which IS live and IS consumed downstream)? Building an orphan sweep for a corpus with
no confirmed live writer would either scan an empty prefix forever or flag long-dead legacy litter as "orphan" findings
nobody can action.

### (b) `backtest_results` — genuinely untracked, no manifest to diff against

`gcs_storage_service.py`'s `CloudStorageService` writes backtest artifacts to
`backtest_results/strategy_id={strategy_id}/run_id={run_id}/...` (fast results line 238, full results line 347, summary
line 461) — read every one of these write methods: **zero `ManifestWriter`/`record_captured` calls anywhere near them**
(`grep -n "ManifestWriter\|record_captured\|manifest" gcs_storage_service.py` hits only the docstring-log line 204 and
the `strategy_instructions` write path at line 210 — nothing for `backtest_results`).

The only OTHER manifest write touching backtests, `cli/handlers/batch_results.py:126-139`, reuses
`data_type="strategy_instructions"` (confirms the parent doc's own prior note) with row_key
`(date, strategy_id, client_id)` — **no `run_id` column exists on that row at all**, so even that write cannot be
repurposed as backtest_results coverage.

**Decision needed**: `backtest_results` is genuinely NOT manifest-tracked by any key, anywhere. Orphan detection is
undefined without a manifest to diff against — this needs a manifest-WRITE design pass (a new
`data_type= backtest_results` keyed by `(strategy_id, run_id)`?) OR a deliberate decision that ad-hoc/exploratory
backtest-grid runs are intentionally out of the availability-manifest's scope (they are not systematic pipeline data the
way raw ticks/candles/features are).

### (c) `ml_models`/`ml_model_metadata`/`ml_training_artifacts` — live writer, zero manifest coverage (reaffirmed)

Already surfaced by todo 3b's real VM run (233 real objects misclassified `D_junk` before the `F_other_corpus` fix).
Re-confirmed by code: `grep -rn "ManifestWriter\|record_captured" ml-service/ml_service/` hits ONLY
`inference/app/core/prediction_publisher.py` (the `ml_predictions` writer) — zero manifest calls anywhere in
`ml-service/ml_service/training/`. Unlike (a), this corpus IS actively written (real writer:
`training/app/core/training_orchestrator.py:527-546`/`679-689`, `training-artifacts/experiments/{model_id}/...`) — this
is the genuinely-different case the parent doc's own text already flagged: a live corpus with a well-formed key
(`model_id`) that was simply never wired into the manifest pattern, by omission or by original design (training
artifacts may have been deliberately kept outside the availability-manifest's raw/processed-data scope).

**Decision needed** (same shape as (b), per the parent todo's own instruction to scope this as an operator-facing call):
should `ml_models`/`ml_model_metadata`/`ml_training_artifacts` get a manifest-WRITE design (keyed by `model_id`,
mirroring how `ml_predictions` is `(day, mode)`-keyed), or are they intentionally exempt from manifest-based orphan
detection?

## Why it matters

All 3 gaps converge on the same root cause: orphan detection is fundamentally a GCS-vs-manifest diff, and for these 3
families there is either no live writer (a), no manifest of any kind (b), or a live writer with a manifest gap that may
be intentional (c). Mechanically porting the existing A-E sweep taxonomy onto any of them right now would either find
nothing meaningful (a — no real corpus), be undefined (b — no manifest to diff), or require inventing a manifest schema
unilaterally (c — a product decision, not an engineering one). This is exactly the same judgment call the parent doc's
own text called out for (c) alone; investigating (a) and (b) in full shows the same conclusion applies to all 3, not
just (c).

## Open work

- [x] ✅ 1. [DOCS] P2. Decide the fate of `strategy_orders`/`strategy_positions`/`strategy_pnl`. **RULED 2026-08-05
      (operator, BLK-75060009): wire up.** The orphan-sweep-tooling half of this decision already shipped (todo 4 below,
      strategy-service@4733a7e7). The real-caller wiring + PATH_REGISTRY divergence fix implied by "wire up" is NOT yet
      built — tracked as new todo 5 below so it isn't lost now that the decision itself is closed. Repo:
      strategy-service.
- [x] ✅ 2. [DOCS] P2. Decide whether `backtest_results` should get a manifest-WRITE design. **RULED 2026-08-05
      (operator, BLK-75060009): ephemeral, no sweep** — intentionally out of the availability-manifest's scope, no
      further work needed. Repo: strategy-service.
- [x] ✅ 3. [DOCS] P2. Decide whether `ml_models`/`ml_model_metadata`/`ml_training_artifacts` should get a
      manifest-WRITE design. **RULED 2026-08-05 (operator, BLK-75060009): ephemeral, no sweep** — intentionally exempt,
      no further work needed. Repo: ml-service.
- [x] ✅ 4. [SCRIPT] P3. Once any of todos 1-3 resolves toward "wire it up", build the corresponding orphan-sweep
      extension — strategy-service@4733a7e7 (extend `strategy_orphan_sweep.py` for orders/positions/pnl and/or
      backtest_results; `ml_orphan_sweep.py` for models/metadata/training_artifacts) mirroring the A-E taxonomy pattern.
      Repo: strategy-service, ml-service.
- [ ] 5. [OPERATOR] P2. **New 2026-08-09, split out of todo 1's now-resolved decision. Mechanical sub-parts SHIPPED
      2026-08-09 (slot 8); the real-caller sub-part is now BLOCKED on an operator decision — see BLK below.** Wire up a
      real caller for `strategy_orders`/`strategy_positions`/`strategy_pnl`: add explicit
      `PROTOCOL_DATA_SINK_BUCKET_STRATEGY_ORDERS`-class deployment config (currently defaults to `LocalDataSink()` — no
      `PROTOCOL_DATA_SINK_BACKEND`/bucket env var set in
      `deployment-service/terraform/services/strategy-service/gcp/main.tf:197-224`) — **done, strategy-service /
      deployment-service, see Progress Log** — and fix the PATH_REGISTRY divergence
      (`PATH_REGISTRY["strategy_orders"].path_template` declares
      `strategy_orders/by_date/day={date}/strategy_id={strategy_id}/` but the real writer call resolves to bucket-root
      `day={date}/strategy_id={strategy_id}/{uuid}.parquet` with no prefix — same class as todo 3b's
      `ml_predictions`/`strategy_instructions` fixes) — **done, strategy-service, see Progress Log**. **Still open**:
      wiring an actual real (non-test) caller of `store_orders_batch`/`store_positions`/`store_pnl` — investigation this
      session found `OrderRecord`/UAC `OrderData` has ZERO real-data producers anywhere in the workspace (see BLK
      question in Progress Log); inventing one would fabricate the `strategy_orders` corpus, not wire it up. **Done
      when**: a real caller writes through `get_data_sink(routing_key="strategy_orders")` to the documented
      `PATH_REGISTRY` path, deployment config sets an explicit GCS backend, and `bash scripts/quality-gates.sh` is
      green. Repo: strategy-service, deployment-service.

## Progress Log

- **2026-08-03** (AO dispatch, slot 14) — Filed this doc after investigating todo 3c of the parent doc in full (read
  every write call site for all 3 deferred families rather than guessing at shape, per the parent doc's own discipline).
  Conclusion: none of the 3 is buildable as a mechanical sweep-tool port right now — each needs an operator-facing
  decision first (dead-code wire-up-or-delete for (a); a manifest-WRITE design pass for (b)/(c)).
- **2026-08-05** (AO dispatch, slot 7) — Todo 4 shipped: strategy_orphan_sweep.py extended with strategy_data family
  (orders/positions/pnl combined, keyed by (day, strategy_id), grain-tolerant blank-data_type manifest matching,
  sibling-prefix exclusions with F_other_corpus). Operator answered BLK-75060009: (1) strategy_orders/positions/pnl →
  wire up; (2) backtest_results → ephemeral, no sweep; (3) ml_models → ephemeral, no sweep. strategy-service@4733a7e7.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped in the sibling "todo 3b" doc (the real VM
  run gap (c) cites as prior evidence) and the orphan-detection codex SSOT, and swapped the ml-service writer in for the
  sweep-tool script since this doc's decision is about the 3 write-site gaps, not the future sweep extension.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **stale-`[OPERATOR]`-flip sweep 2026-08-09**: todos 1-3 carried stale `[OPERATOR]` tags — all 3 were already ruled
  2026-08-05 (BLK-75060009, cited inline in the 2026-08-05 entry above). Flipped all 3 `[x]`, retagged `[DOCS]`. Todo
  1's "wire up" ruling implies real, un-started implementation work (a live caller + PATH_REGISTRY fix) beyond the
  orphan-sweep-tool extension todo 4 already shipped — split that out as new todo 5 (`[BACKEND] P2`) rather than let it
  go untracked. Todos 2/3 needed no follow-up (both ruled "ephemeral, no sweep").
- **2026-08-09** (AO dispatch, slot 8, data_engineering) — Todo 5's two mechanical sub-parts shipped:
  1. **PATH_REGISTRY divergence fix** — `CloudStrategyStorage.__init__` now passes `prefix="strategy_orders/by_date"` to
     `get_data_sink(routing_key="strategy_orders", ...)` (was: no `prefix=`, resolving to bucket-root);
     `store_orders_batch`'s write call now passes `filename="orders.parquet"` matching
     `PATH_REGISTRY["strategy_orders"].file_template`. Combined with `_build_partition_path`'s alphabetical
     partition-key sort (`day` before `strategy_id`, matching the template's own order), a real write now lands at
     `strategy_orders/by_date/day={date}/strategy_id={strategy_id}/orders.parquet`, matching the documented path
     exactly. `strategy_positions`/`strategy_pnl` have no `PATH_REGISTRY` entry to diverge from, so left unprefixed —
     out of this fix's stated scope. strategy-service (uncommitted at time of writing — see below).
  2. **Deployment config** — added `PROTOCOL_DATA_SINK_BACKEND=gcp` +
     `PROTOCOL_DATA_SINK_BUCKET_STRATEGY_{ORDERS,POSITIONS,PNL}=strategy-store-prd-${var.project_id}` to
     `deployment-service/terraform/services/strategy-service/gcp/main.tf`'s `daily_job` env vars — bucket matches
     `PATH_REGISTRY["strategy_orders"].bucket_template` (the strategy-store FOLD D flat env-tiered bucket) so the
     UCI-DataSink writer and any future PATH_REGISTRY-based reader agree on the physical bucket. deployment-service
     (uncommitted at time of writing).
  3. **Real-caller sub-part investigated, found genuinely blocked** — grepped every non-test call site of
     `CloudStrategyStorage`/`OrderBatchStorage`/UAC `OrderData(` in the ENTIRE workspace (not just strategy-service):
     `store_positions`/`store_pnl` have zero callers anywhere; `store_orders_batch`'s only caller
     (`OrderBatchStorage.save_order_batch`) is itself never instantiated outside its own unit tests; UAC
     `OrderData(...)` has **zero real constructors in any repo** (the only workspace-wide grep hits for `OrderData(`
     were a `CeFiVenueOrderData(TypedDict)` false-positive and test fixtures). Every actual strategy-signal-generation
     code path in the current tree (`batch_signals.py`'s DeFi `_collect_instructions` → operation/instrument_id/amount/
     direction envelopes, and the `v2_prod` harness's `on_tick()` emissions) produces operation-shaped data with no
     side/price/status fields — there is no code path anywhere that naturally produces `OrderRecord`-shaped
     (order_id/side/quantity/price/status) data. The generic non-DeFi `generate_signal()` path `batch_signals.py` falls
     back to for non-DeFi strategies has zero concrete implementations in the tree (V1 archetype deleted, 2026-05-01
     V1-RETIRE Phase 2) — it is dead code, not a live signal source either. Constructing an `OrderRecord` from a DeFi
     instruction would require inventing what "side"/"price"/"status" mean for non-trade operations
     (TRANSFER/BORROW/REPAY/FLASH_BORROW have no buy/sell direction or price at signal time) — a genuine product
     decision, not a mechanical wire-up, and doing it unilaterally risks writing systematically-wrong data under the
     `strategy_orders` corpus (a data-correctness violation per this craft's own north-star). Posting `/blocked`
     (question below) rather than fabricating a caller; the two mechanical sub-parts above are shipped as real partial
     progress. Todo 5 stays open, retagged `[OPERATOR]`.
  - **BLK question**: "The BLK-75060009 'wire up' ruling for `strategy_orders`/`strategy_positions`/`strategy_pnl`
    assumed a real caller could simply be added, but this session found `OrderRecord`/UAC `OrderData` has ZERO real-data
    producers anywhere in the workspace — no strategy code path emits side/price/status-shaped data. What should
    'strategy orders' data represent for the real caller?" Options: **(A, recommended)** treat each DeFi strategy
    instruction as the 'order' (matches `OrderBatchStorage`'s own docstring — "orders generated by strategy service ...
    for later use by execution service backtest"): map `operation`→`side` only for directional ops (SWAP/TRADE have a
    `direction`), synthesize `price` from `benchmark_price`/candle close at signal time, and explicitly SKIP
    non-directional ops (TRANSFER/BORROW/REPAY/FLASH_BORROW) rather than force them into a side/price shape they don't
    have — i.e. `strategy_orders` covers only the directional-trade subset of instructions, honestly. **(B)** reverse
    the "wire up" ruling to "ephemeral, no sweep" (matching `backtest_results`/`ml_models`) since no real data source
    exists and inventing one is fabrication. **(C)** wire `strategy_orders` from execution-service's real fill data
    instead of strategy-service — a different repo/flow, out of this todo's declared repos, much larger scope.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
