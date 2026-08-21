---
doc_type: plan
title: features-consolidation-and-drilldown
summary: Two follow-on improvements after correctness + read-perf land. (1) Feature-store consolidation layer that pre-joins
  all relevant feature_groups into a wide-table parquet per (asset_group, day) at write-time, giving ML training a single
  GCS GET per day instead of N. (2) UTL FeatureBatchHandler base class lifting the Delta-One/Onchain/Sports/Volatility BatchHandler
  boilerplate (~200 LOC each). (3) deployment-ui feature-group drill-down route + per-feature-group parquet download endpoint.
  Sequenced after sibling plans writegate_honest_coverage_endtoend, feature_dag_uac_ssot_and_features_coverage, and ml_training_feature_read_perf.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-06
type: code
epic: data-pipeline-completion
owner: Harsh
locked_by: live-defi-rollout
locked_since: 2026-05-06
completion_gates: { code: C5, deployment: D3, business: B3 }
repo_gates:
  - { repo: unified-trading-library, code: C0, deployment: none, business: none }
  - { repo: features-delta-one-service, code: C0, deployment: D0, business: none }
  - { repo: features-onchain-service, code: C0, deployment: D0, business: none }
  - { repo: features-sports-service, code: C0, deployment: D0, business: none }
  - { repo: features-volatility-service, code: C0, deployment: D0, business: none }
  - { repo: features-multi-timeframe-service, code: C0, deployment: D0, business: none }
  - { repo: ml-training-service, code: C0, deployment: D0, business: B0 }
  - { repo: deployment-api, code: C0, deployment: D0, business: none }
  - { repo: deployment-ui, code: C0, deployment: D0, business: none }
depends_on:
  [
    writegate_honest_coverage_endtoend_2026_05_06,
    feature_dag_uac_ssot_and_features_coverage_2026_05_06,
    ml_training_feature_read_perf_2026_05_06,
  ]
isProject: false
---

> **ARCHIVED 2026-05-07** — folded into
> [`ml_and_features_master_2026_05_07.md`](../active/ml_and_features_master_2026_05_07.md). All open todos preserved in
> the umbrella's Phase 1-4. This file is the historical SSOT.

# Features consolidation + drill-down (P2/P3 follow-ons)

## Codex SSOTs

This plan implements / extends the following codex documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md) —
  downstream NaN handling at consolidation join boundary (rolling-window denominator adjustment, propagated NaN through
  cross-instrument calcs)
- [`/codex/02-data/data-lineage-MTDS-features-ml.md`](/codex/02-data/data-lineage-MTDS-features-ml.md) — MTDS → features
  → ML lineage; consolidation layer sits between features-\* writers + ml-training reader
- [`/codex/02-data/data-status-drilldown-hierarchy.md`](/codex/02-data/data-status-drilldown-hierarchy.md) — drill-down
  hierarchy SSOT for the deployment-ui feature-group route + per-feature-group parquet download endpoint
- [`/codex/06-coding-standards/feature-service-pattern.md`](/codex/06-coding-standards/feature-service-pattern.md) —
  features-\* service pattern; the UTL `FeatureBatchHandler` base class lifts the boilerplate the doc describes

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 14 of 14 unchecked todos
- **Mis-marked DONE → flipped**: 0 (none — Phase 3 deployment-ui shipped multi-axis SchemaModal + per-asset-group
  accordion + SmartDownloadButton via `8056995` / `7309b56` / `537d468` / `0fbd28b`, but those land general data-status
  drilldown — they do NOT yet implement the feature_group-specific routes named here, so the Phase 3 todos are still
  fresh as scoped.)
- **In-flight (running VMs)**: none (this plan is pure code-shipping).
- **Blocked by**:
  - `writegate_honest_coverage_endtoend_2026_05_06` — write-gate must validate consolidator output (Phase 1B Step 2).
    Tier 1 UTL contract shipped (UAC@8867891 + UTL@958634f9), Tier 2 sports/cefi/defi/tradfi adapters shipped, but
    `LookaheadBiasError` strict-mode + Phase 5 ratchet still pending.
  - `feature_dag_uac_ssot_and_features_coverage_2026_05_06` (sibling) — `EXPECTED_FEATURE_GROUPS_BY_SERVICE` is required
    to know which feature_groups must be present in a consolidated parquet for a given (asset_group, day) (Phase 1B
    `MissingFeatureGroup` honest-failure path).
  - `ml_training_feature_read_perf_2026_05_06` — needs to land first to establish the baseline that consolidation must
    beat by ≥5x (Phase 1C benchmark target).
- **Blocks**:
  - `master_to_live_defi_2026_05_23` — if the May-23 deadline hits, this whole plan is post-deadline. Drill-down
    (Phase 3) is closer to operator-UX surface area but not on the live-go critical path.
- **Last meaningful commit**: deployment-ui multi-axis SchemaModal stack landed (`7309b56`, `537d468`, `0fbd28b`,
  `8056995`, `ebfbc5d`), but NONE wire the feature_group-leaf endpoint specified in Phase 3 — drill-down today is at
  per-shard granularity, not per-feature_group route.
- **Recommendation**: KEEP active but explicitly P2/P3. Plan is well-scoped and depends-on chain is correct (writegate →
  feature_dag → ml-read-perf → this plan). For May-23 deadline this is post-launch optimisation. If budget tight: drop
  Phase 1 (feature-store consolidation = ~500 LOC + risky), keep Phase 2 (UTL FeatureBatchHandler, worth 200 LOC × 4
  services) + Phase 3 (drill-down — operator visibility for Group G UX).

## Why sequenced after siblings

The two sibling plans land first because they're correctness + cheap perf. This plan ships the higher-effort
transformational pieces:

- **Feature-store consolidation** — single pre-joined wide-table parquet per `(asset_group, day)`, eliminating the N
  parquets × M instruments × K feature_groups read pattern in ml-training-service entirely. ~5-10× ML read speedup. Net
  new ~500 LOC + new write-time orchestration. Risky if shipped before write-gate validation (writegate) lands, because
  a bad join in the consolidator silently corrupts every downstream training run.
- **UTL `FeatureBatchHandler` base** — Delta-One / Onchain / Sports / Volatility re-implement nearly identical
  `(DataLoader, Calculator, FeatureWriter, ManifestWriter)` glue. Lifting saves ~200 LOC per service but requires
  per-service knobs. Easier after writegate introduces the write-gate helper they all consume.
- **deployment-ui feature-group drill-down** — UI-side improvement, not on the critical path for backfill, but needed
  for operator visibility once the feature manifest is honest (writegate) and consolidation parquets exist.

## Phase 1 — Feature-store consolidation

### 1A — Design

- [ ] [AGENT] P0. **Decide consolidation atom**: per `(asset_group, day, timeframe)` wide-table or per
      `(asset_group, day, instrument_id)` per-instrument wide-table. Trade-off: instrument-wide reads in single file
      (fast for per-instrument training) vs day-wide cross-instrument reads (fast for ranking/portfolio models).
      Recommendation: ship instrument-wide first; add day-wide if measured useful. [AUDIT 2026-05-07: FRESH — design
      decision, not started.]
- [ ] [AGENT] P0. **Path SSOT in UAC**:
      `gs://features-consolidated-{asset_group}-{project_id}/by_date/day=YYYY-MM-DD/timeframe={tf}/{instrument_id}.parquet`.
      One file per (asset_group, day, instrument, timeframe) carrying every feature column from every feature_group
      joined on `(timestamp, instrument_id)`. [AUDIT 2026-05-07: FRESH — UAC grep `features-consolidated` → 0 hits;
      bucket SSOT not yet added.]
- [ ] [AGENT] P0. **Manifest** — consolidation rows in availability manifest with `feature_group="_consolidated"`
      sentinel + `model_family / training_period` empty. [AUDIT 2026-05-07: FRESH — sentinel value not yet written by
      any service.]

### 1B — Write-time orchestration

- [ ] [AGENT] P1. **features-consolidation sidecar (or per-service post-compute hook)**: after each features-\*-service
      finishes a (day, instrument, timeframe) shard, emit a Pub/Sub event. Subscriber consolidator joins all available
      feature_groups for that key into a wide parquet. If any required feature_group is missing, write
      `record_failed(MissingFeatureGroup)`; honest signal. [AUDIT 2026-05-07: FRESH — no `features-consolidation`
      service or sidecar exists in workspace.]
- [ ] [AGENT] P1. **Strict ordering** — consolidator depends on writegate's write-gate, so it never joins garbage rows.
      UTL `validate_shard()` re-runs on the consolidated output (pillars 2-4). [AUDIT 2026-05-07: BLOCKED-ON writegate
      Phase 1A `record_captured` 4-pillar gate — Tier 1 contract shipped at `8867891`/`958634f9`, but
      `LookaheadBiasError` strict-mode pending across writers.]

### 1C — ml-training read switch

- [ ] [AGENT] P1. `FeatureDataAdapter` switches to read `features-consolidated-...` paths when present, falls back to
      per-feature_group paths only for legacy training periods. Migration window documented. [AUDIT 2026-05-07: FRESH —
      `feature_data_adapter.py` still reads per-feature_group GCS paths; no consolidation branch.]
- [ ] [AGENT] P1. Benchmark vs ml_training_feature_read_perf baseline (post-DuckDB-merge): target 5-10× speedup on
      representative training run. [AUDIT 2026-05-07: BLOCKED-ON ml_training_feature_read_perf_2026_05_06:Phase-4
      baseline numbers (which itself is not yet started — `gcs_feature_reader.py` still uses pandas + BytesIO +
      ThreadPoolExecutor, no DuckDB).]

## Phase 2 — UTL FeatureBatchHandler base

- [ ] [AGENT] P2. **UTL `unified_trading_library/feature_service_base/batch_handler.py`** — `FeatureBatchHandler[T]`
      generic base lifting the (DataLoader, Calculator, FeatureWriter, ManifestWriter, ManifestFreshnessCache,
      write-gate) wiring. Per-service hooks: `load_inputs(shard_key) -> InputBundle`, `compute(inputs) -> OutputBundle`,
      `expected_clusters(shard_key) -> dict | None`. [AUDIT 2026-05-07: FRESH —
      `unified_trading_library/feature_service_base/` exists, no `batch_handler.py` shipped; depends on
      `ManifestFreshnessCache` from sibling feature_dag plan.]
- [ ] [AGENT] P2. Refactor Delta-One, Onchain, Sports, Volatility BatchHandlers to extend the base. Net delete ~200 LOC
      each. Behavior-preserving — diff existing batch outputs. [AUDIT 2026-05-07: BLOCKED-ON preceding todo.]

## Phase 3 — deployment-ui feature drill-down

- [ ] [AGENT] P3. **deployment-api**: per-feature_group leaf endpoint
      `GET /data_status/feature_groups/{service}/{feature_group}/shards?...` returning shard-level rows + GCS URIs.
      Mirror the existing market-data drill-down depth. [AUDIT 2026-05-07: FRESH — deployment-api grep
      `/data_status/feature_groups/` route → 0 hits; current data-status surfaces feature_groups via
      `_build_feature_group_breakdown` aggregate only.]
- [ ] [AGENT] P3. **deployment-api**: parquet download endpoint
      `GET /data_status/feature_groups/{service}/{feature_group}/parquet?day=...&instrument=...&timeframe=...` returning
      the parquet bytes (or a signed URL). [AUDIT 2026-05-07: FRESH — `SmartDownloadButton` shipped in deployment-ui
      (`7309b56`) but no per-feature_group download endpoint on deployment-api side.]
- [ ] [AGENT] P3. **deployment-ui** new route `/feature-groups/{service}/{feature_group}` rendering shard list + schema
      view + download button. Match the look of the existing market-data drill-down. Reuses `DimensionStatus` types
      already in `deployment-ui/src/types/index.ts`. [AUDIT 2026-05-07: FRESH — multi-axis SchemaModal + per-asset-group
      accordion shipped at `8056995`/`7309b56`/ `537d468`/`0fbd28b`/`ebfbc5d` but those land general data-status
      drilldown, not the feature_group leaf route named here.]

## Success criteria

| Criterion                                                                          | Gate |
| ---------------------------------------------------------------------------------- | ---- |
| Consolidation parquet path declared in UAC + written by sidecar                    | C5   |
| ML training reads consolidation parquet by default                                 | C5   |
| Benchmark: ≥ 5× faster feature read step vs ml_training_feature_read_perf baseline | B3   |
| `FeatureBatchHandler` base merged + 4 services migrated                            | C5   |
| deployment-ui `/feature-groups/{service}/{feature_group}` renders + download works | D3   |

## Anti-patterns

- Don't ship consolidation before writegate's write-gate lands — joining ungated shards is a silent-corruption
  amplifier.
- Don't keep both per-feature_group and consolidated read paths permanently active in ml-training. Migrate then delete
  the legacy reader (workspace "delete deprecated code" rule).
- Don't add asset-group-specific consolidator microservices — single sidecar with per-asset-group config knobs.
