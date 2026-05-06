# Features Pipeline Pre-Compute Audit — 2026-05-06

**Owner**: Harsh **Trigger**: instruments + most market-data captured/processed; ready to scale features computation.
Audit before code changes. **Method**: 3 parallel Explore-agent sweeps over the 8 features-\* services + UTL
`manifest_writer.py` + UAC + `deployment-api/data_status_service.py` + `deployment-ui/DataStatusTab.tsx` +
`ml-training-service`. **Verdict**: pipeline is structurally sound but has 3 critical correctness/observability gaps
that MUST close before scale-out, plus 3 perf wins.

---

## TL;DR — what's broken vs what's fast enough

> **Routing note (post-overlap-check 2026-05-06)**: many items below were already in scope for
> `writegate_honest_coverage_endtoend_2026_05_06.plan.md` (in-flight, locked to live-defi-rollout). The "Action" column
> reflects that — only items writegate explicitly defers or doesn't touch are owned by my new plans.

| Area                                                                                                                  | Status                                                                        | Action                                                        |
| --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Compute lifecycle (BaseFeatureServiceV2, manifest emit, shard isolation)                                              | Green                                                                         | none                                                          |
| Honest coverage (manifest v5/v6 columns)                                                                              | Green                                                                         | none                                                          |
| **Lookahead-bias guard (`LookaheadBiasError`, `available_at`, `record_captured` integration, sports temporal rules)** | **Red — none exist today**                                                    | **writegate** (already in scope)                              |
| **Write-gate 4 pillars (row-count, NaN ratio, schema, cluster coverage) + UAC `BUNDLED_DATA_TYPES`**                  | Amber — only pillar 1 implemented                                             | **writegate** (already in scope)                              |
| `feature_group → required_inputs[]` DAG SSOT in UAC (writegate explicitly defers)                                     | Red — inlined per-service across 3 services                                   | **new Plan A** (`feature_dag_uac_ssot_and_features_coverage`) |
| **Feature-coverage denominator** (no UAC `EXPECTED_FEATURE_GROUPS_BY_SERVICE` / `FEATURE_COVERAGE_START`)             | Amber — false-positive coverage %                                             | **new Plan A**                                                |
| **Phantom-row audit** for features manifest                                                                           | Red — `reconcile_phantom_manifest_rows_all.py` doesn't probe feature parquets | **new Plan A**                                                |
| **Manifest concurrency** (per-date freshness cache) in features-sports + features-volatility                          | Red — blind iteration; wastes compute under concurrent scale                  | **new Plan A**                                                |
| ML training feature-read perf (per-shard parquet, no row-group pruning, pandas outer-merge)                           | Amber — works but slow                                                        | **Plan B** (`ml_training_feature_read_perf`)                  |
| Calculator concurrency tuning (Vol `max_workers=4`, Delta-One unspec)                                                 | Amber — leaves 2-4× speedup on table                                          | **Plan B**                                                    |
| BatchHandler boilerplate duplication across Delta-One/Onchain/Sports/Vol                                              | Amber — 200+ LOC reducible to UTL base                                        | **Plan C** (later, depends on writegate)                      |
| Feature-store consolidation (pre-joined wide-table parquets)                                                          | Amber — high-effort transformational                                          | **Plan C**                                                    |
| deployment-ui feature-group drill-down                                                                                | Amber — operator visibility                                                   | **Plan C**                                                    |

---

## 1. Compute architecture — current state (8 services)

| Service                   | Entry                                                       | Shard atom                                | Manifest emit                                   | Concurrency                |
| ------------------------- | ----------------------------------------------------------- | ----------------------------------------- | ----------------------------------------------- | -------------------------- |
| features-calendar         | `CalendarFeatureService.compute_features()`                 | (feature_group, date)                     | `record_empty/failed` ✓                         | per-day serial             |
| features-commodity        | `CommodityFeatureService.compute_features()`                | per-commodity                             | via batch_handler (try/except wrap)             | serial; PubSub IO in loop  |
| features-cross-instrument | `service.py:82` `get_calculator_for_group()`                | per-(group, symbol)                       | at orchestrator (not service.py)                | none at service            |
| features-delta-one        | `BatchHandler.run(asset_group, feature_group, ...)`         | (group, instrument, day, timeframe)       | via FeatureWriter                               | BatchHandler-level         |
| features-multi-timeframe  | `MtfOrchestrationService.run_batch(...)`                    | (instrument, date)                        | at orchestrator                                 | per-instrument             |
| features-onchain          | `BatchHandler.run(asset_group="DEFI", ...)`                 | (chain, protocol, day, group)             | via FeatureWriter                               | per-chain                  |
| features-sports           | `BatchHandler.run(date_str, providers, tables, league_ids)` | (source, league_id, day)                  | `record_empty/failed` for KNOWN_COVERAGE_GAPS ✓ | per-source                 |
| features-volatility       | `VolatilityFeaturesOrchestrator.process()`                  | (chain_type, root, venue, day, timeframe) | at orchestrator                                 | ThreadPool `max_workers=4` |

All services extend UTL `BaseFeatureServiceV2`; lifecycle events (STARTED/STOPPED/FAILED) emit via UEI. Shard-level
failure isolation present everywhere via `classify_and_emit_error()`.

### Calculator examples (spot-checked)

- `features-delta-one-service/app/calculators/market_structure.py:126-140` — swing-high via
  `rolling(window=20, center=True).max() == high` (correct for structure detection);
  `df["high"] > df["high"].shift(1) * (1 + breach_threshold)` (correctly compares current bar to prior —
  lookahead-free).
- `features-onchain-service/app/calculators/{PoolInvariantDriftCalculator, FlashLoanCalculator}` — present, no lookahead
  checks.
- `features-volatility-service/calculators/{VolatilityCalculator, FuturesCalculator}` — present, no lookahead checks.

---

## 2. GCS layout (write-side, output)

Per `unified-trading-pm/codex/02-data/data-lineage-MTDS-features-ml.md` Layer 3:

Bucket: `features-{feature_group}-{category}-central-element-323112`

Path:
`features/by_date/day=YYYY-MM-DD/category={cat}/feature_group={group}/timeframe={tf}/venue={venue}/instrument_type={type}/.parquet`

Writer: `unified_trading_library.io.streaming_writer.StreamingParquetWriter(strict=True)` +
`ManifestWriter.write_with_zero_fill`. Manifest carries `feature_group, model_family, training_period` columns (per
`manifest_writer.py:420-422`); v6 schema fully encodes feature axes (`manifest_writer.py:73`).

ML-training read path (`ml-training-service/app/core/gcs_feature_reader.py`):

- Path:
  `gs://features-delta-one-{asset_group}-{project_id}/by_date/day={YYYY-MM-DD}/feature_group={group}/timeframe={tf}/{instrument_id}.parquet`
- ThreadPool `max_workers=50`, `pd.read_parquet(io.BytesIO(...))` (entire file into RAM).
- 38 days × 4 feature_groups = **152 parquet GETs per instrument per training run**, with sequential outer-merge in
  pandas.
- No row-group min/max pruning, no column push-down, no disk cache, no Arrow mmap, no DuckDB. Every training run
  re-fetches and re-joins.

---

## 3. Tracking + deployment-UI integration — current state

### Where the data flows

1. Features-\* writes parquet + per-VM manifest shard via `ManifestWriter`.
2. `manifest_consolidator.py` (Cloud Scheduler `*/1 * * * *`) merges per-VM shards into canonical index.
3. `deployment-api/services/data_status_service.py` reads canonical, builds rollups:
   - line 548 filters by feature_group when present
   - lines 3684-3686 `_build_feature_group_breakdown(v_df, ...)`
   - endpoint `/data_status?check_feature_groups=true` (line 2288)
   - returns `feature_groups: Record[str, DimensionStatus]` (lines 3686, 4837)
4. `deployment-ui/src/components/DataStatusTab.tsx:275` iterates `feature_groups` map nested under category.

### Gaps in tracking

- **UAC has no `EXPECTED_FEATURE_GROUPS_BY_SERVICE` registry**. Denominator is inferred from manifest contents → "if we
  wrote 3 feature_groups, expected = 3". Coverage % can be 100% even when the service should emit 8 groups.
- **No coverage-start clip for features**. Sports `_clip_dates_to_source_coverage()` exists
  (data_status_service.py:39-50); features have no equivalent → services with staggered launch dates show inflated
  coverage.
- **No phantom audit for features**. `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:395` covers
  asset_groups but not features. Phantoms (manifest says captured, parquet missing or empty) silently pass.
- **No drill-down detail page** in UI. Feature coverage is buried under category dimension list; no
  `/feature-groups/{service}/{feature_group}` route, no leaf-parquet download dedicated to features.

---

## 4. Lookahead-bias + formula correctness — current state

CLAUDE.md mandates `LookaheadBiasError` raised at every features-\* + MDPS compute (strict, not warn) using a UAC
`feature_group → required_inputs` DAG and write-time `available_at` columns.

**Reality**: zero implementation. Workspace-wide grep for `LookaheadBiasError`, `available_at`, the DAG, and sports
temporal rules (`kickoff − 60min`, etc.) returns **0 matches in every features-\*-service and in UTL/UAC**.

The CLAUDE.md note "Currently fires for lst_yields; extend to every features-\* calculator" is aspirational — lst_yields
itself doesn't have it either at this point.

### Why this matters before scale-out

Once we backfill 7 years × 8 services × N feature_groups, every NaN column we don't catch becomes a silent corruption.
Strategy backtests trained on lookahead-biased features confidently produce wrong signals. The fix needs to land
**before** the bulk compute, not after — re-running 7 years is expensive.

---

## 5. ML training feature-read perf — current state

| Bottleneck                     | Location                                            | Cost                                                      | Fix difficulty                            |
| ------------------------------ | --------------------------------------------------- | --------------------------------------------------------- | ----------------------------------------- |
| Per-file GCS GET, no batching  | `gcs_feature_reader.py:157-183` `_download_parquet` | network latency × file_count, 152 GETs/instrument typical | Med (pre-join + path consolidation)       |
| In-memory outer joins per day  | `gcs_feature_reader.py:205-213`                     | RAM peak, row duplication on timestamp mismatch           | Low (DuckDB lazy join)                    |
| Load-then-filter               | `feature_data_adapter.py:61-88`                     | reads all dates, filters in pandas                        | Low (pyarrow row-group pruning)           |
| No caching layer               | n/a                                                 | every training re-fetches                                 | Med (disk LRU or Arrow mmap)              |
| No feature-store consolidation | n/a                                                 | N feature_group buckets joined in-memory each run         | High (post-compute consolidation sidecar) |

### Estimated wins

- DuckDB joins + row-group pruning + column push-down: **~2× faster reads, lower memory** — low-effort wins.
- Pre-joined wide-table parquets per (asset_group, day): **~5-10× faster reads** for typical training jobs (single GCS
  GET vs 152) — high-effort but transformational at scale.

---

## 6. Cross-cutting opportunities (impact-ranked)

1. **[P0 / blocks scale-out]** Lift write-gate validation pillars 2-4 (NaN ratio, schema match, cluster coverage) to UTL
   helper consumed by every features-\* writer.
2. **[P0 / blocks scale-out]** Implement `LookaheadBiasError` + write-time `available_at` stamping + UAC
   `feature_group → required_inputs` DAG.
3. **[P0 / blocks accurate UI]** UAC `EXPECTED_FEATURE_GROUPS_BY_SERVICE` registry + `FEATURE_COVERAGE_START` +
   data-status denominator clip + phantom audit extension to features.
4. **[P0 / blocks concurrent scale]** Per-date manifest freshness re-check in features-sports + features-volatility
   BatchHandlers (CLAUDE.md `_is_now_captured(row_key)` pattern, 60s TTL).
5. **[P1]** ML read perf: row-group pruning + DuckDB joins + column push-down — small surgical changes, ~2× speedup.
6. **[P1]** Concurrency tuning per service profile — Volatility `max_workers=4` likely 2-4× under-tuned; Delta-One
   unspec.
7. **[P2]** Feature-store consolidation layer (pre-joined wide-table parquets at write-time) — transformational ML-read
   speedup but new surface area; sequence after P0/P1 stabilise.
8. **[P2]** UTL `FeatureBatchHandler` base class lifting Delta-One/Onchain/Sports/Vol boilerplate (~200 LOC each).
9. **[P3]** Deployment-UI feature-group drill-down page + parquet download endpoint.

---

## 7. Plan routing (post overlap-check 2026-05-06)

After cross-checking against `plans/active/` it became clear that
`writegate_honest_coverage_endtoend_2026_05_06.plan.md` already owns the largest items in this audit
(`LookaheadBiasError`, `available_at` write-time stamping, sports temporal rules, write-gate 4-pillar gate at
`record_captured`, UAC `BUNDLED_DATA_TYPES`). My initial draft of `features_pipeline_correctness_and_coverage`
duplicated ~70% of writegate and was deleted. The remaining work is sliced into three smaller plans:

| Plan                                                            | Scope                                                                                                                                                                                                                                                                                                                                                                                                                                | Owner                    | Sequencing                                                                           |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------ | ------------------------------------------------------------------------------------ |
| `writegate_honest_coverage_endtoend_2026_05_06.plan.md`         | Items #1-3 + part of #4 (writegate 4 pillars, lookahead guard, available_at, sports temporal rules, cluster validation, BUNDLED_DATA_TYPES).                                                                                                                                                                                                                                                                                         | (existing — Iggy/Ikenna) | In flight                                                                            |
| `feature_dag_uac_ssot_and_features_coverage_2026_05_06.plan.md` | Features-only items writegate explicitly defers or doesn't touch: UAC `feature_group → required_inputs` DAG (the `feature_dag_uac_ssot_<TBD>` plan writegate names at line 113); UAC `EXPECTED_FEATURE_GROUPS_BY_SERVICE` + `FEATURE_COVERAGE_START`; data-status feature denominator clip; phantom-audit extension to features manifest; `ManifestFreshnessCache` lifted to UTL + adopted in features-sports + features-volatility. | new (Harsh)              | Depends on writegate's DAG semantics; can start in parallel for the parts that don't |
| `ml_training_feature_read_perf_2026_05_06.plan.md`              | P1 items #5-6 (row-group pruning, column push-down, DuckDB joins, concurrency tuning).                                                                                                                                                                                                                                                                                                                                               | new (Harsh)              | Independent; can run alongside                                                       |
| `features_consolidation_and_drilldown_2026_05_06.plan.md`       | P2-P3 items #7-9 (feature-store consolidation, UTL `FeatureBatchHandler` base, deployment-ui drill-down).                                                                                                                                                                                                                                                                                                                            | new (Harsh)              | After writegate + feature-DAG-SSOT plans stabilise                                   |

Concurrent execution: writegate is in flight; new Plan A (feature-DAG-SSOT) and Plan B (ml-read-perf) can land in
parallel; Plan C (consolidation + drill-down) sequences after.

---

## 8. References

- Compute audit: agent `a319c498607e6275b` (subagent jsonl in `~/.claude/projects/.../subagents/`)
- Tracking + UI audit: agent `a80d86a299df8b064`
- Lookahead + ML-read audit: agent `aed165a998b7e152b`
- SSOT: `unified-trading-pm/codex/02-data/data-lineage-MTDS-features-ml.md`
- SSOT: `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`
- Adjacent active plan: `features_sports_honest_coverage_2026_05_05.plan.md` (Iggy-owned; sports-specific
  honest-coverage; this audit's plans complement, do not collide).
- Adjacent active plan: `data_pipeline_completion_2026_04_18.plan.md` (umbrella; this audit's plans live under same
  epic).
