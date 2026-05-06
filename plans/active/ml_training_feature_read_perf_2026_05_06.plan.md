---
name: ml-training-feature-read-perf
overview:
  Reduce ML training feature-read time by 2-4x via three surgical changes to ml-training-service feature reader
  (date-partition row-group pruning, column pushdown, DuckDB lazy joins replacing pandas outer-merge) plus
  concurrency tuning of features-volatility-service (max_workers=4 default is conservative). Foundation for the
  P2 feature-store consolidation plan (sibling), which is high-effort and shipped after this lands.
type: code
epic: data-pipeline-completion
status: active
owner: Harsh
created: 2026-05-06
locked_by: live-defi-rollout
locked_since: 2026-05-06
completion_gates:
  code: C5
  deployment: D2
  business: B3
repo_gates:
  - repo: ml-training-service
    code: C0
    deployment: D0
    business: B0
  - repo: features-volatility-service
    code: C0
    deployment: D0
    business: B0
  - repo: features-delta-one-service
    code: C0
    deployment: D0
    business: B0
depends_on: []
isProject: false
---

# ML training feature-read perf — surgical wins

## Problem

Pre-compute audit `unified-trading-pm/plans/ai/features_pipeline_pre_compute_audit_2026_05_06.md` § 5 measured the
`ml-training-service` feature read path:

- Path template: `gs://features-delta-one-{asset_group}-{project_id}/by_date/day={YYYY-MM-DD}/feature_group={group}/timeframe={tf}/{instrument_id}.parquet`
- `ParallelGCSFeatureReader` ThreadPool `max_workers=50`, `pd.read_parquet(io.BytesIO(parquet_bytes))` (entire file
  into RAM).
- Per training run: **38 days × 4 feature_groups = 152 parquet GETs per instrument**, sequential outer-merge in
  pandas with row duplication on timestamp mismatch.
- No row-group min/max pruning, no column push-down, no disk cache, no Arrow mmap, no DuckDB.

Three bottleneck files:

| File | Issue |
| --- | --- |
| `ml-training-service/ml_training_service/app/core/gcs_feature_reader.py:157-183` | per-file GCS GET, no batching, full BytesIO load |
| `ml-training-service/ml_training_service/app/core/gcs_feature_reader.py:205-213` | sequential pandas outer-merge per feature_group |
| `ml-training-service/ml_training_service/adapters/feature_data_adapter.py:61-88` | reads all dates' files, then filters in pandas |

## Goal

2-4× faster ML training feature read with surgical changes to one service. No new architecture, no new
microservices. The feature-store consolidation layer (single pre-joined wide-table parquet per `(asset_group, day)`)
that would give 5-10× is sibling plan
`features_consolidation_and_drilldown_2026_05_06.plan.md` and is sequenced after this one stabilises.

## Pre-audit manifest

| Change | Files |
| --- | --- |
| Row-group pruning (push date filter to parquet) | `gcs_feature_reader.py:157-183`, `feature_data_adapter.py:61-88` |
| Column push-down | `gcs_feature_reader.py:_download_parquet`, `feature_data_adapter.py` (need column list at read-time) |
| DuckDB lazy joins | `gcs_feature_reader.py:185-232` `_merge_features` |
| Concurrency tuning | `features-volatility-service` orchestrator default `max_workers`; `features-delta-one-service` BatchHandler concurrency knob |

No downstream consumer changes — output of `FeatureDataAdapter.read_features()` remains a pandas DataFrame with the
same columns; only internals change.

## Phased execution DAG

```
Phase 1: row-group pruning + column push-down  (parallel sub-tasks)
   |
   v  (QG + benchmark)
Phase 2: DuckDB lazy joins
   |
   v  (QG + benchmark)
Phase 3: concurrency tuning (features-volatility, features-delta-one)
   |
   v  (QG + benchmark)
Phase 4: end-to-end benchmark + business-readiness sign-off
```

## Phase 1 — Row-group pruning + column push-down (PARALLEL)

- [ ] [AGENT] P0. **Row-group pruning** in `gcs_feature_reader.py:_download_parquet`. Replace
      `pd.read_parquet(io.BytesIO(parquet_bytes))` with `pyarrow.parquet.ParquetFile(...).read(filters=...)` or
      `pyarrow.dataset.dataset(...).to_table(filter=...)`. Push date-range filter (already known at the call site)
      to row-group min/max pruning. For instrument-id partitioning that's already happening at the path level, no
      additional filter needed.
- [ ] [AGENT] P0. **Column push-down**. `FeatureDataAdapter.read_features(columns=...)` already exists; thread
      `columns` argument all the way through `ParallelGCSFeatureReader._download_parquet` so only requested columns
      are deserialised. Today the entire row-group is read.
- [ ] [AGENT] P0. **Tests**: synthetic 365-day per-instrument parquet with 50 feature columns. Assert reading 38
      days × 5 columns is at least 4× faster than reading all data + filtering.

**Phase 1 success**: per-file read time drops on benchmark; integration test against a real GCS sample (one CeFi
asset_group, one feature_group, 38 days) confirms >= 30% wall-clock improvement on the read step.

## Phase 2 — DuckDB lazy joins

- [ ] [AGENT] P1. **Replace pandas outer-merge with DuckDB**. `_merge_features` (`gcs_feature_reader.py:185-232`):
      build an in-process DuckDB connection, register each per-day per-group DataFrame as a view, run
      `SELECT * FROM g0 FULL OUTER JOIN g1 USING (timestamp, instrument_id) FULL OUTER JOIN g2 ...`. DuckDB
      query planner picks join order; lower memory peak; faster for 4+ groups.
- [ ] [AGENT] P1. Drop the manual `_dedupe_columns` logic — DuckDB join uses `USING` so no `_x` / `_y` suffixes.
- [ ] [AGENT] P1. **Tests**: identical-output test against pandas merge baseline on a fixture with 4 feature_groups
      and overlapping timestamps. Diff must be empty (modulo column order).

**Phase 2 success**: end-to-end read benchmark shows additional speedup; memory peak drops measurably.

## Phase 3 — Concurrency tuning

- [ ] [AGENT] P2. **features-volatility-service**: profile `VolatilityFeaturesOrchestrator.process()` with
      `max_workers ∈ {4, 8, 16, 32}` on a representative options-chain shard. Pick the knee. Update default in
      service config. CPU vs IO mix likely supports 16+ on standard VM.
- [ ] [AGENT] P2. **features-delta-one-service**: identify BatchHandler concurrency knob; apply same profiling
      methodology. Document knee in service config.
- [ ] [AGENT] P2. **Per-asset-group max_workers SSOT** in UAC or per-service config — codify the knees so future
      operators don't have to re-profile.

**Phase 3 success**: features-volatility + features-delta-one default `max_workers` updated; benchmark replays
demonstrate 2-4× compute speedup on representative shards.

## Phase 4 — End-to-end benchmark + B3 sign-off

- [ ] [AGENT] P3. **Benchmark harness**: replay one full ML training run (one model_family, one asset_group, 38-day
      window) before-and-after. Report wall-clock + peak RSS for: feature read step, feature merge step, total
      training time.
- [ ] [AGENT] P3. **Document results** in this plan's Benchmark section. Target: ≥ 2× faster feature read step;
      ≥ 30% lower peak RSS during merge.
- [ ] [AGENT] P3. **B3 sign-off**: KPI met → mark plan code-ready for archive after data-pipeline-completion epic
      closes.

## Success criteria

| Criterion | Gate |
| --- | --- |
| Row-group pruning + column push-down landed | C2 |
| DuckDB lazy joins landed; output identical to pandas baseline | C2 |
| features-volatility default `max_workers` updated based on profiling | C5 |
| Benchmark: ≥ 2× faster feature read step on representative training run | B3 |
| Benchmark: ≥ 30% lower peak RSS during merge | B3 |
| No correctness regressions in existing ML training experiments | D2 |

## Anti-patterns (don't do)

- Don't write a "fast path" parallel to the existing reader. Replace in place. (Workspace rule: no parallel code paths.)
- Don't introduce DuckDB as a process-wide singleton — per-call connection is fine; avoid hidden state across
  training runs.
- Don't tune `max_workers` higher than the GCS HTTP pool size in the storage client (CLAUDE.md: pool tuned to
  `2 * workers`; symmetric on the read side).
- Don't pre-emptively build a feature-store consolidation layer here — that's the sibling P2 plan.

## Benchmark (filled during Phase 4)

| Metric | Before | After (target) | After (actual) |
| --- | --- | --- | --- |
| Feature read step wall-clock | TBD | -50% | TBD |
| Peak RSS during merge | TBD | -30% | TBD |
| End-to-end ML training | TBD | -20% | TBD |
