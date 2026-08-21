---
doc_type: plan
title: ml-training-feature-read-perf
summary: Reduce ML training feature-read time by 2-4x via three surgical changes to ml-training-service feature reader (date-partition
  row-group pruning, column pushdown, DuckDB lazy joins replacing pandas outer-merge) plus concurrency tuning of features-volatility-service
  (max_workers=4 default is conservative). Foundation for the P2 feature-store consolidation plan (sibling), which is high-effort
  and shipped after this lands.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-06
type: code
epic: data-pipeline-completion
owner: Harsh
locked_by: live-defi-rollout
locked_since: 2026-05-06
completion_gates: { code: C5, deployment: D2, business: B3 }
repo_gates:
  - { repo: ml-training-service, code: C0, deployment: D0, business: B0 }
  - { repo: features-volatility-service, code: C0, deployment: D0, business: B0 }
  - { repo: features-delta-one-service, code: C0, deployment: D0, business: B0 }
depends_on: []
isProject: false
---

> **ARCHIVED 2026-05-07** — folded into
> [`ml_and_features_master_2026_05_07.md`](../active/ml_and_features_master_2026_05_07.md). All open todos preserved in
> the umbrella's Phase 1-4. This file is the historical SSOT.

# ML training feature-read perf — surgical wins

## Codex SSOTs

This plan implements / extends the following codex documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`/codex/02-data/data-lineage-MTDS-features-ml.md`](/codex/02-data/data-lineage-MTDS-features-ml.md) — MTDS → features
  → ml-training reader lineage; this plan reduces wall-clock at the ml-training read boundary
- [`/codex/06-coding-standards/quality-gates.md`](/codex/06-coding-standards/quality-gates.md) — QG discipline for the
  perf changes (basedpyright, ruff, coverage floor on the rewritten reader path)
- [`/codex/06-coding-standards/performance-targets.md`](/codex/06-coding-standards/performance-targets.md) —
  service-level perf targets (the 2-4× target lives here)
- [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md) — the
  DuckDB lazy-join must preserve honest-absence semantics; outer-merge-equivalent behaviour required

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 11 of 11 unchecked todos
- **Mis-marked DONE → flipped**: 0 (none — verified `gcs_feature_reader.py:166` still uses
  `pd.read_parquet(io.BytesIO(parquet_bytes))`; `_merge_features` still uses pandas outer-merge with `_dedupe_columns`;
  no `pyarrow.parquet`/`pyarrow.dataset`/`duckdb` imports anywhere in `ml-training-service/ml_training_service/`. The
  manifest-side commit `f7369f2` (job_id threading per Phase 1B b.2) is in writegate scope, not this plan.)
- **In-flight (running VMs)**: none (no ML training runs blocked on this; profiling/benchmark Phase 4 will need a
  representative GCS sample, but that is on-demand, not a continuous VM).
- **Blocked by**:
  - none structurally — this plan has `depends_on: []`. However the Phase 4 benchmark sign-off requires features
    manifest to be honest enough that representative shards exist, which itself depends on writegate Tier 2 adapters
    finishing for the chosen asset_group. Today CeFi spot/perp + sports adapters are migrated; tradfi adapters tier 2E
    shipped at MDPS@e9520a0. Pick CeFi for the benchmark — fewest unknowns.
- **Blocks**:
  - `features_consolidation_and_drilldown_2026_05_06` Phase 1C — needs the post-DuckDB-merge baseline number to claim
    the 5-10x speedup target (which is the whole reason consolidation is justified).
  - `master_to_live_defi_2026_05_23` Group D Coverage operability (read-perf affects nightly retraining cadence). Not a
    hard live-go blocker — current pipeline works, just slowly.
- **Last meaningful commit**: ml-training@`f7369f2` (job_id manifest threading — out-of-scope for this plan, in scope
  for writegate Phase 1B). No commits modify `gcs_feature_reader.py` or `feature_data_adapter.py` since plan creation on
  2026-05-06.
- **Recommendation**: KEEP active. This is a 1-3 day item that's fully self-contained and unlocks the 5-10× target for
  the consolidation plan. For May-23 deadline this is post-launch optimisation but should be queued behind the May-23
  Group F+G live-readiness work. Phases 1+2 (row-group pruning + DuckDB) are pure-win pure-Python — no risk to live
  trading correctness if shipped post-May-23.

## Problem

Pre-compute audit `unified-trading-pm/plans/ai/features_pipeline_pre_compute_audit_2026_05_06.md` § 5 measured the
`ml-training-service` feature read path:

- Path template:
  `gs://features-delta-one-{asset_group}-{project_id}/by_date/day={YYYY-MM-DD}/feature_group={group}/timeframe={tf}/{instrument_id}.parquet`
- `ParallelGCSFeatureReader` ThreadPool `max_workers=50`, `pd.read_parquet(io.BytesIO(parquet_bytes))` (entire file into
  RAM).
- Per training run: **38 days × 4 feature_groups = 152 parquet GETs per instrument**, sequential outer-merge in pandas
  with row duplication on timestamp mismatch.
- No row-group min/max pruning, no column push-down, no disk cache, no Arrow mmap, no DuckDB.

Three bottleneck files:

| File                                                                             | Issue                                            |
| -------------------------------------------------------------------------------- | ------------------------------------------------ |
| `ml-training-service/ml_training_service/app/core/gcs_feature_reader.py:157-183` | per-file GCS GET, no batching, full BytesIO load |
| `ml-training-service/ml_training_service/app/core/gcs_feature_reader.py:205-213` | sequential pandas outer-merge per feature_group  |
| `ml-training-service/ml_training_service/adapters/feature_data_adapter.py:61-88` | reads all dates' files, then filters in pandas   |

## Goal

2-4× faster ML training feature read with surgical changes to one service. No new architecture, no new microservices.
The feature-store consolidation layer (single pre-joined wide-table parquet per `(asset_group, day)`) that would give
5-10× is sibling plan `features_consolidation_and_drilldown_2026_05_06.md` and is sequenced after this one stabilises.

## Pre-audit manifest

| Change                                          | Files                                                                                                                        |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Row-group pruning (push date filter to parquet) | `gcs_feature_reader.py:157-183`, `feature_data_adapter.py:61-88`                                                             |
| Column push-down                                | `gcs_feature_reader.py:_download_parquet`, `feature_data_adapter.py` (need column list at read-time)                         |
| DuckDB lazy joins                               | `gcs_feature_reader.py:185-232` `_merge_features`                                                                            |
| Concurrency tuning                              | `features-volatility-service` orchestrator default `max_workers`; `features-delta-one-service` BatchHandler concurrency knob |

No downstream consumer changes — output of `FeatureDataAdapter.read_features()` remains a pandas DataFrame with the same
columns; only internals change.

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
      `pyarrow.dataset.dataset(...).to_table(filter=...)`. Push date-range filter (already known at the call site) to
      row-group min/max pruning. For instrument-id partitioning that's already happening at the path level, no
      additional filter needed. [AUDIT 2026-05-07: FRESH — actionable; verified `gcs_feature_reader.py:166` still
      `pd.read_parquet(io.BytesIO(parquet_bytes))`, no pyarrow.dataset/parquet imports.]
- [ ] [AGENT] P0. **Column push-down**. `FeatureDataAdapter.read_features(columns=...)` already exists; thread `columns`
      argument all the way through `ParallelGCSFeatureReader._download_parquet` so only requested columns are
      deserialised. Today the entire row-group is read. [AUDIT 2026-05-07: FRESH — `_download_parquet(self, blob_name)`
      has no `columns` parameter today.]
- [ ] [AGENT] P0. **Tests**: synthetic 365-day per-instrument parquet with 50 feature columns. Assert reading 38 days ×
      5 columns is at least 4× faster than reading all data + filtering. [AUDIT 2026-05-07: FRESH — depends on the two
      preceding todos.]

**Phase 1 success**: per-file read time drops on benchmark; integration test against a real GCS sample (one CeFi
asset_group, one feature_group, 38 days) confirms >= 30% wall-clock improvement on the read step.

## Phase 2 — DuckDB lazy joins

- [ ] [AGENT] P1. **Replace pandas outer-merge with DuckDB**. `_merge_features` (`gcs_feature_reader.py:185-232`): build
      an in-process DuckDB connection, register each per-day per-group DataFrame as a view, run
      `SELECT * FROM g0 FULL OUTER JOIN g1 USING (timestamp, instrument_id) FULL OUTER JOIN g2 ...`. DuckDB query
      planner picks join order; lower memory peak; faster for 4+ groups. [AUDIT 2026-05-07: FRESH — workspace-wide grep
      for `duckdb` in ml-training-service → 0 hits.]
- [ ] [AGENT] P1. Drop the manual `_dedupe_columns` logic — DuckDB join uses `USING` so no `_x` / `_y` suffixes. [AUDIT
      2026-05-07: FRESH — depends on preceding todo.]
- [ ] [AGENT] P1. **Tests**: identical-output test against pandas merge baseline on a fixture with 4 feature_groups and
      overlapping timestamps. Diff must be empty (modulo column order). [AUDIT 2026-05-07: FRESH — depends on preceding
      todos.]

**Phase 2 success**: end-to-end read benchmark shows additional speedup; memory peak drops measurably.

## Phase 3 — Concurrency tuning

- [ ] [AGENT] P2. **features-volatility-service**: profile `VolatilityFeaturesOrchestrator.process()` with
      `max_workers ∈ {4, 8, 16, 32}` on a representative options-chain shard. Pick the knee. Update default in service
      config. CPU vs IO mix likely supports 16+ on standard VM. [AUDIT 2026-05-07: FRESH — needs at least one
      writegate-validated options-chain shard to profile against.]
- [ ] [AGENT] P2. **features-delta-one-service**: identify BatchHandler concurrency knob; apply same profiling
      methodology. Document knee in service config. [AUDIT 2026-05-07: FRESH — same as preceding.]
- [ ] [AGENT] P2. **Per-asset-group max_workers SSOT** in UAC or per-service config — codify the knees so future
      operators don't have to re-profile. [AUDIT 2026-05-07: FRESH — depends on the two preceding profiling runs.]

**Phase 3 success**: features-volatility + features-delta-one default `max_workers` updated; benchmark replays
demonstrate 2-4× compute speedup on representative shards.

## Phase 4 — End-to-end benchmark + B3 sign-off

- [ ] [AGENT] P3. **Benchmark harness**: replay one full ML training run (one model_family, one asset_group, 38-day
      window) before-and-after. Report wall-clock + peak RSS for: feature read step, feature merge step, total training
      time. [AUDIT 2026-05-07: FRESH — depends on Phases 1+2 landing first; pick CeFi as the chosen asset_group (Tier 2C
      cefi adapters shipped at MDPS@b9f9328 so a clean validated shard set exists).]
- [ ] [AGENT] P3. **Document results** in this plan's Benchmark section. Target: ≥ 2× faster feature read step; ≥ 30%
      lower peak RSS during merge. [AUDIT 2026-05-07: FRESH — depends on benchmark harness above; Benchmark table at
      bottom of plan still all TBD.]
- [ ] [AGENT] P3. **B3 sign-off**: KPI met → mark plan code-ready for archive after data-pipeline-completion epic
      closes. [AUDIT 2026-05-07: FRESH — final acceptance gate.]

## Success criteria

| Criterion                                                               | Gate |
| ----------------------------------------------------------------------- | ---- |
| Row-group pruning + column push-down landed                             | C2   |
| DuckDB lazy joins landed; output identical to pandas baseline           | C2   |
| features-volatility default `max_workers` updated based on profiling    | C5   |
| Benchmark: ≥ 2× faster feature read step on representative training run | B3   |
| Benchmark: ≥ 30% lower peak RSS during merge                            | B3   |
| No correctness regressions in existing ML training experiments          | D2   |

## Anti-patterns (don't do)

- Don't write a "fast path" parallel to the existing reader. Replace in place. (Workspace rule: no parallel code paths.)
- Don't introduce DuckDB as a process-wide singleton — per-call connection is fine; avoid hidden state across training
  runs.
- Don't tune `max_workers` higher than the GCS HTTP pool size in the storage client (CLAUDE.md: pool tuned to
  `2 * workers`; symmetric on the read side).
- Don't pre-emptively build a feature-store consolidation layer here — that's the sibling P2 plan.

## Benchmark (filled during Phase 4)

| Metric                       | Before | After (target) | After (actual) |
| ---------------------------- | ------ | -------------- | -------------- |
| Feature read step wall-clock | TBD    | -50%           | TBD            |
| Peak RSS during merge        | TBD    | -30%           | TBD            |
| End-to-end ML training       | TBD    | -20%           | TBD            |
