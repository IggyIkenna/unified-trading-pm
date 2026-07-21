---
doc_type: plan
title: CME combo bundling — one parquet per (date, data_type, underlying) instead of per-combo
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-30
priority: P1
owner: agent
type: refactor
epic: tradfi-data-pipeline
completion_gates: { code: C2, deployment: D2, business: none }
repo_gates:
  - { repo: market-tick-data-service, deployment: D0 }
  - { repo: deployment-service, deployment: D1 }
depends_on: []
isProject: false
---

## Deferred work — migrated to: `plans/active/issues/batch4_strategy_ui_archived_plan_residuals_2026_07_21.md` — successor:

batch4_strategy_ui_archived_plan_residuals (the writer-side bundling shipped —
`market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py:256` confirms `"combo"` is now
underlying-partitioned — but the historical re-bundle migration script, reader-compat-shim removal, and manifest
reconciler have no found evidence of having run; tracked as a fresh verification todo there, folding into
`tradfi_consolidated_closeout_2026_07_18.md` if still outstanding).

## Context

The 2026-04-30 ES_OPT backfill confirmed CME combos write **one parquet file per combo per day**. For a single trading
day (`2024-04-20`), the writer dropped **2,072 separate `.parquet` files** under
`instrument_type=combo/data_type=ohlcv_1m/`:

- Named calendar spreads: `ESM2-ESU2.parquet`, `ESU2-ESH3.parquet`, `BTCM4-BTCN4.parquet`
- CME user-defined combos: `UD_1V_C12_*.parquet`, `UD_1V_BO_*.parquet`, `UD_1V_VT_*.parquet`, `UD_1V_CFO_*.parquet`
  (butterflies, iron condors, vertical spreads, boxes, calendar diagonals)

Most files are 1-4 rows. Total day-size is small (~MB-range) but **GCS small-file write rate is the bottleneck**: ES_OPT
VMs spend ~3-4 min per trading day, dominated by writing thousands of tiny parquets. ES_OPT 5 year-shards run ~12h each
instead of the ~2h ES futures takes for similar wall-clock.

Compare to `instrument_type=futures_chain` which already bundles: one `ticks.parquet` per
`(date, data_type, underlying)` containing all child contracts. That's the right shape — read-side queries filter by
`symbol` column, not file path. The combo writer should match.

## Why bundling is correct

1. **Read-side**: feature pipelines / backtests / data-status queries always read by date, then filter by symbol.
   Per-symbol files give zero benefit because consumers always need the union.
2. **Write-side**: GCS `objects.insert` cost dominates for small files. Bundling N rows into one parquet is one PUT vs N
   PUTs.
3. **Manifest**: one row per `(date, data_type, underlying)` instead of per combo — drops manifest cardinality ~10x.
4. **Cost**: GCS lifecycle / inventory / billing all scale with object count.

## Files to modify

| Repo                     | File                                                                                                                   | Change                                                                                                                                       |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| market-tick-data-service | `market_tick_data_service/writers/partitioned_tick_writer.py` (or wherever `instrument_type=combo` routing is decided) | Bundle combo rows by `(date, data_type, underlying)` into one `combos.parquet` per partition. Match existing `futures_chain` bundling logic. |
| market-tick-data-service | `market_tick_data_service/scripts/_migrate_tradfi_classifier.py:81`                                                    | `_BUNDLED_INSTRUMENT_TYPES` already includes `combo` — verify the writer honors this flag (likely the bug).                                  |
| market-tick-data-service | new helper for underlying detection on `UD_1V_*` combos                                                                | Lookup via Databento definition stream OR fall back to a per-day `underlying=UD/combos.parquet` catch-all.                                   |
| deployment-service       | `scripts/migrations/rebundle_combo_parquets.py` (NEW)                                                                  | One-time migration script: walk existing per-combo files, bundle into new layout, mark legacy for GCS lifecycle expire.                      |

## Phase plan

### Phase 1 — Trace + reproduce (read-only)

- [ ] [AGENT] P0. Locate the writer code path that decides per-symbol vs bundled file for `instrument_type=combo`.
      Likely candidates: `PartitionedTickWriter._resolve_path`, `databento_adapter` post-classification routing.
- [ ] [AGENT] P0. Confirm `_BUNDLED_INSTRUMENT_TYPES` (currently
      `frozenset({"options_chain", "futures_chain", "combo"})` per `_migrate_tradfi_classifier.py` (search for
      `_BUNDLED_INSTRUMENT_TYPES`)) is honored at write time. The set is consulted by the migration script; the live
      writer may use different logic.
- [ ] [AGENT] P0. Decide underlying convention for `UD_1V_*` combos:
  - Option A — look up via Databento `definition.parquet` per day and resolve `underlying_root`
  - Option B — catch-all `underlying=UD/` per day (cheaper, slightly less queryable)
  - **Recommended:** Option B for the immediate fix; revisit Option A if consumers need per-root UD filtering.

### Phase 2 — Writer change (MTDS)

- [ ] [AGENT] P0. Update writer to bundle combo rows by `(date, data_type, underlying)` into one `combos.parquet`.
- [ ] [AGENT] P0. Unit test: feed mock combo rows with mixed underlyings (ES, BTC, ETH, UD); assert one bundled parquet
      per underlying with `symbol` column preserved.
- [ ] [AGENT] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh` clean.
- [ ] [AGENT] P0. Commit + push.

### Phase 3 — Reader compat (consumer audit)

- [ ] [AGENT] P0. Audit consumers that read `instrument_type=combo`:
  - `features-cross-instrument-service` (most likely consumer)
  - `data-status` / `manifest-reader`
  - any `executions` simulator
- [ ] [AGENT] P0. For each, update reader to handle either per-combo legacy files or new bundled file. Single-pass
      `glob('*.parquet')` + concat already works for both layouts in most cases.
- [ ] [AGENT] P0. Test on a known multi-combo date (e.g., `2024-04-20` with 2,072 legacy files) — assert same row counts
      whether read via legacy or bundled.

### Phase 4 — Migration script (deployment-service)

- [ ] [AGENT] P0. Write `scripts/migrations/rebundle_combo_parquets.py`:
  - Bulk-list all `instrument_type=combo/data_type=*/` parquets per day (use `gsutil ls` or `google.cloud.storage`)
  - Group by `(date, data_type, underlying)`
  - Read all rows, write single bundled `combos.parquet`, delete legacy per-combo files
  - Idempotent: skip days where bundled file already exists
- [ ] [AGENT] P0. Dry-run on a small date range first; sample-validate row counts before production migration.
- [ ] [HUMAN] P0. Run migration in batched dry-runs (~30 days at a time) so the human can spot-check before committing
      each batch.

### Phase 5 — Cutover + cleanup

- [ ] [AGENT] P0. Switch writer to bundled-only after re-bundle migration completes.
- [ ] [AGENT] P1. Remove reader compat shim once all consumers are bundled-aware (track via plan completion gate).
- [ ] [AGENT] P1. Add manifest reconciler to flip stale per-combo manifest rows to attempted_failed if the bundled file
      exists at canonical path (similar to phantom-row recon).

## Out of scope

- Bundling `options_chain` further than current per-underlying. ES options already bundle by underlying (one file per
  ES.OPT per day per data_type). Per-strike granularity within a chain is intentional (queries often want a specific
  strike).
- Bundling `future` (single contract) into `futures_chain` (parent) — they're separate intentionally so consumers can
  pick a specific contract or the chain.
- Changing the combo `symbol` naming convention (`UD_1V_*` etc.) — those are CME-canonical IDs.

## Success criteria

- ES_OPT VM wall-clock drops from ~12h per year-shard to ~1-2h (matching ES futures rate).
- Manifest row count for combo data_types drops by ~10x.
- GCS object count under `instrument_type=combo/` drops by ~10x.
- Existing combo data still queryable through reader compat shim during transition.

## Estimated effort

~2 days. Phase 2 (writer change) is small; Phase 3 (consumer audit) and Phase 4 (migration) drive the schedule.

## Verification

- After Phase 2: launch one ES_OPT smoke (single year-shard via
  `bash launch-tradfi-backfill-vm.sh --root-symbol ES_OPT --year 2024 --force`). Compare wall-clock vs the 2026-04-30
  baseline (12h+ per year-shard). Should drop to ~1-2h.
- After Phase 4: spot-check
  `gsutil ls gs://market-data-tick-tradfi-central-element-323112/raw_tick_data/by_date/day=2024-04-20/asset_group=tradfi/venue=CME/instrument_type=combo/data_type=ohlcv_1m/`
  — should show 1-3 bundled `combos.parquet` files (one per underlying) instead of 2,072 per-combo files.
