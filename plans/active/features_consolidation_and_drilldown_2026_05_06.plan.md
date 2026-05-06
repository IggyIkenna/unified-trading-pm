---
name: features-consolidation-and-drilldown
overview:
  Two follow-on improvements after correctness + read-perf land. (1) Feature-store consolidation layer that
  pre-joins all relevant feature_groups into a wide-table parquet per (asset_group, day) at write-time, giving
  ML training a single GCS GET per day instead of N. (2) UTL FeatureBatchHandler base class lifting the
  Delta-One/Onchain/Sports/Volatility BatchHandler boilerplate (~200 LOC each). (3) deployment-ui feature-group
  drill-down route + per-feature-group parquet download endpoint. Sequenced after sibling plans
  features_pipeline_correctness_and_coverage and ml_training_feature_read_perf.
type: code
epic: data-pipeline-completion
status: active
owner: Harsh
created: 2026-05-06
locked_by: live-defi-rollout
locked_since: 2026-05-06
completion_gates:
  code: C5
  deployment: D3
  business: B3
repo_gates:
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: features-delta-one-service
    code: C0
    deployment: D0
    business: none
  - repo: features-onchain-service
    code: C0
    deployment: D0
    business: none
  - repo: features-sports-service
    code: C0
    deployment: D0
    business: none
  - repo: features-volatility-service
    code: C0
    deployment: D0
    business: none
  - repo: features-multi-timeframe-service
    code: C0
    deployment: D0
    business: none
  - repo: ml-training-service
    code: C0
    deployment: D0
    business: B0
  - repo: deployment-api
    code: C0
    deployment: D0
    business: none
  - repo: deployment-ui
    code: C0
    deployment: D0
    business: none
depends_on:
  - features_pipeline_correctness_and_coverage_2026_05_06
  - ml_training_feature_read_perf_2026_05_06
isProject: false
---

# Features consolidation + drill-down (P2/P3 follow-ons)

## Why sequenced after siblings

The two sibling plans land first because they're correctness + cheap perf. This plan ships the higher-effort
transformational pieces:

- **Feature-store consolidation** — single pre-joined wide-table parquet per `(asset_group, day)`, eliminating the
  N parquets × M instruments × K feature_groups read pattern in ml-training-service entirely. ~5-10× ML read
  speedup. Net new ~500 LOC + new write-time orchestration. Risky if shipped before write-gate validation
  (sibling A) lands, because a bad join in the consolidator silently corrupts every downstream training run.
- **UTL `FeatureBatchHandler` base** — Delta-One / Onchain / Sports / Volatility re-implement nearly identical
  `(DataLoader, Calculator, FeatureWriter, ManifestWriter)` glue. Lifting saves ~200 LOC per service but requires
  per-service knobs. Easier after sibling A introduces the write-gate helper they all consume.
- **deployment-ui feature-group drill-down** — UI-side improvement, not on the critical path for backfill, but
  needed for operator visibility once the feature manifest is honest (sibling A) and consolidation parquets exist.

## Phase 1 — Feature-store consolidation

### 1A — Design

- [ ] [AGENT] P0. **Decide consolidation atom**: per `(asset_group, day, timeframe)` wide-table or per
      `(asset_group, day, instrument_id)` per-instrument wide-table. Trade-off: instrument-wide reads in single
      file (fast for per-instrument training) vs day-wide cross-instrument reads (fast for ranking/portfolio
      models). Recommendation: ship instrument-wide first; add day-wide if measured useful.
- [ ] [AGENT] P0. **Path SSOT in UAC**:
      `gs://features-consolidated-{asset_group}-{project_id}/by_date/day=YYYY-MM-DD/timeframe={tf}/{instrument_id}.parquet`.
      One file per (asset_group, day, instrument, timeframe) carrying every feature column from every
      feature_group joined on `(timestamp, instrument_id)`.
- [ ] [AGENT] P0. **Manifest** — consolidation rows in availability manifest with `feature_group="_consolidated"`
      sentinel + `model_family / training_period` empty.

### 1B — Write-time orchestration

- [ ] [AGENT] P1. **features-consolidation sidecar (or per-service post-compute hook)**: after each
      features-*-service finishes a (day, instrument, timeframe) shard, emit a Pub/Sub event. Subscriber
      consolidator joins all available feature_groups for that key into a wide parquet. If any required
      feature_group is missing, write `record_failed(MissingFeatureGroup)`; honest signal.
- [ ] [AGENT] P1. **Strict ordering** — consolidator depends on sibling A's write-gate, so it never joins
      garbage rows. UTL `validate_shard()` re-runs on the consolidated output (pillars 2-4).

### 1C — ml-training read switch

- [ ] [AGENT] P1. `FeatureDataAdapter` switches to read `features-consolidated-...` paths when present, falls
      back to per-feature_group paths only for legacy training periods. Migration window documented.
- [ ] [AGENT] P1. Benchmark vs sibling B baseline (post-DuckDB-merge): target 5-10× speedup on representative
      training run.

## Phase 2 — UTL FeatureBatchHandler base

- [ ] [AGENT] P2. **UTL `unified_trading_library/feature_service_base/batch_handler.py`** —
      `FeatureBatchHandler[T]` generic base lifting the (DataLoader, Calculator, FeatureWriter, ManifestWriter,
      ManifestFreshnessCache, write-gate) wiring. Per-service hooks: `load_inputs(shard_key) -> InputBundle`,
      `compute(inputs) -> OutputBundle`, `expected_clusters(shard_key) -> dict | None`.
- [ ] [AGENT] P2. Refactor Delta-One, Onchain, Sports, Volatility BatchHandlers to extend the base. Net delete
      ~200 LOC each. Behavior-preserving — diff existing batch outputs.

## Phase 3 — deployment-ui feature drill-down

- [ ] [AGENT] P3. **deployment-api**: per-feature_group leaf endpoint
      `GET /data_status/feature_groups/{service}/{feature_group}/shards?...` returning shard-level rows + GCS
      URIs. Mirror the existing market-data drill-down depth.
- [ ] [AGENT] P3. **deployment-api**: parquet download endpoint
      `GET /data_status/feature_groups/{service}/{feature_group}/parquet?day=...&instrument=...&timeframe=...`
      returning the parquet bytes (or a signed URL).
- [ ] [AGENT] P3. **deployment-ui** new route `/feature-groups/{service}/{feature_group}` rendering shard list +
      schema view + download button. Match the look of the existing market-data drill-down. Reuses
      `DimensionStatus` types already in `deployment-ui/src/types/index.ts`.

## Success criteria

| Criterion | Gate |
| --- | --- |
| Consolidation parquet path declared in UAC + written by sidecar | C5 |
| ML training reads consolidation parquet by default | C5 |
| Benchmark: ≥ 5× faster feature read step vs sibling-B baseline | B3 |
| `FeatureBatchHandler` base merged + 4 services migrated | C5 |
| deployment-ui `/feature-groups/{service}/{feature_group}` renders + download works | D3 |

## Anti-patterns

- Don't ship consolidation before sibling A's write-gate lands — joining ungated shards is a silent-corruption
  amplifier.
- Don't keep both per-feature_group and consolidated read paths permanently active in ml-training. Migrate then
  delete the legacy reader (workspace "delete deprecated code" rule).
- Don't add asset-group-specific consolidator microservices — single sidecar with per-asset-group config knobs.
