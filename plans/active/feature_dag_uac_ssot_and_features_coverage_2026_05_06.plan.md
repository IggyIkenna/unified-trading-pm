---
name: feature-dag-uac-ssot-and-features-coverage
overview:
  Companion to writegate_honest_coverage_endtoend_2026_05_06 — covers ONLY the features-pipeline gaps writegate defers
  or doesn't touch. (1) UAC feature_group->required_inputs DAG SSOT (writegate explicitly defers this as
  feature_dag_uac_ssot_<TBD>). (2) UAC EXPECTED_FEATURE_GROUPS_BY_SERVICE + FEATURE_COVERAGE_START registries —
  honest-coverage denominator for features (writegate covers raw-data shards, not features). (3) data-status denominator
  clip for features in deployment-api. (4) Phantom-row audit extension to features manifest. (5) ManifestFreshnessCache
  lifted to UTL + adopted in features-sports + features-volatility BatchHandlers.
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
  business: B2
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: features-sports-service
    code: C0
    deployment: D0
    business: none
  - repo: features-volatility-service
    code: C0
    deployment: D0
    business: none
  - repo: features-onchain-service
    code: C0
    deployment: D0
    business: none
  - repo: features-delta-one-service
    code: C0
    deployment: D0
    business: none
  - repo: deployment-api
    code: C0
    deployment: D0
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
depends_on:
  - writegate_honest_coverage_endtoend_2026_05_06
isProject: false
---

# Feature DAG UAC SSOT + features-only coverage

## Why this exists (and what it deliberately doesn't cover)

`writegate_honest_coverage_endtoend_2026_05_06.plan.md` (in-flight, locked to live-defi-rollout) is the canonical plan
for `LookaheadBiasError`, `available_at` write-time stamping, sports temporal rules (`stamp_available_at_*` family),
`record_captured` write-gate integration, the 4-pillar gate (incl. cluster validation), and the UAC `BUNDLED_DATA_TYPES`
registry. **This plan does not duplicate any of that.**

Writegate's "Temporary states + their canonical follow-up plans" table (line 113) explicitly defers two items that this
plan picks up:

> "MDPS / features-\* `feature_group → required_inputs[]` DAG inlined per-service — Three services keep their local DAGs
> (features-onchain, features-sports, features-delta-one). Lookahead-bias enforcement still runs but reads from
> per-service DAG. Successor: `feature_dag_uac_ssot_2026_<TBD>.plan.md`"

This plan is that `feature_dag_uac_ssot_2026_<TBD>` plan, plus the four features-only coverage items writegate doesn't
touch (because writegate is scoped to raw-data shards, not features manifests).

## Scope (5 items)

1. **UAC `feature_group → required_inputs[]` DAG SSOT** — single declaration consumed by writegate's
   `LookaheadBiasError` + by deployment-api's denominator clip. Today the DAG is inlined three times across
   features-onchain, features-sports, features-delta-one (per writegate findings).
2. **UAC `EXPECTED_FEATURE_GROUPS_BY_SERVICE` + `FEATURE_COVERAGE_START`** — honest-coverage denominator for the
   features manifest, mirroring the existing `SOURCE_COVERAGE_START` shape for sports sources.
3. **`deployment-api/services/data_status_service.py`** — feature-coverage rollup uses (a) UAC registry as denominator
   (instead of inferring from manifest contents), (b) `_clip_dates_to_feature_coverage(...)` mirroring the sports clip
   helper.
4. **`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`** — extend audit to probe features manifest
   paths. Add features-specific drift axes (timeframe hive casing, feature_group empty-check).
5. **UTL `ManifestFreshnessCache(ttl_seconds=60)`** — lift the `_refresh_captured_cache` + `_is_now_captured` pattern
   (currently inlined at `/tmp/fill_missing_ohlcv.py` per CLAUDE.md manifest-concurrency principle) to a shared UTL
   helper. Adopt in features-sports + features-volatility BatchHandlers (the two services running under concurrent
   backfill scale-out per the audit).

Out of scope (owned elsewhere):

- `LookaheadBiasError` definition + `available_at` stamping + sports temporal rules — owned by
  `writegate_honest_coverage_endtoend_2026_05_06`.
- Write-gate pillars 1-4 (row-count, NaN ratio, schema match, cluster coverage) — writegate.
- UAC `BUNDLED_DATA_TYPES` + `record_captured` cluster guard — writegate.
- Per-source `available_at` schema columns + `stamp_available_at_*` helpers — writegate.
- ML training feature-read perf — sibling `ml_training_feature_read_perf_2026_05_06`.
- Feature-store consolidation, UTL `FeatureBatchHandler` base, deployment-ui drill-down — sibling
  `features_consolidation_and_drilldown_2026_05_06`.

## Pre-audit manifest

| Symbol                                                                                                                  | Producers | Consumers                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified_api_contracts.canonical.domain.features.required_inputs.FEATURE_REQUIRED_INPUTS: dict[str, list[InputReq]]`    | UAC (new) | writegate's `LookaheadBiasError.assert_no_lookahead()`; data-status denominator clip; phantom audit denominator                                 |
| `unified_api_contracts.canonical.domain.features.registry.EXPECTED_FEATURE_GROUPS_BY_SERVICE: dict[str, list[str]]`     | UAC (new) | data-status denominator; phantom audit denominator                                                                                              |
| `unified_api_contracts.canonical.domain.features.registry.FEATURE_COVERAGE_START: dict[(service, feature_group), date]` | UAC (new) | data-status `_clip_dates_to_feature_coverage`                                                                                                   |
| `unified_trading_library.manifest.freshness.ManifestFreshnessCache`                                                     | UTL (new) | features-sports BatchHandler; features-volatility orchestrator; future backfill scripts (replaces `/tmp/fill_missing_ohlcv.py` ad-hoc inlining) |

## Phased execution DAG

```
Phase 1 [UAC]                 Phase 1 [UTL]                  (parallel)
   |                              |
   +-------------+----------------+
                 |
                 v
Phase 2: features-* + deployment-api integrations (parallel sub-tasks)
                 |
                 v
Phase 3: phantom audit extension + sanity replay
```

QG gate between phases.

## Phase 1 — UAC + UTL (PARALLEL)

### 1A — UAC

- [ ] [AGENT] P0. **`FEATURE_REQUIRED_INPUTS` DAG**. Single declaration in
      `unified_api_contracts/canonical/domain/features/required_inputs.py`. Lift the inlined DAG entries currently
      scattered across features-onchain, features-sports, features-delta-one (writegate identified these locations).
      `InputReq(source, data_type, available_at_rule, horizon)` where `available_at_rule` reuses writegate's
      `AVAILABILITY_AT_SEMANTICS` taxonomy (do NOT redefine — import). Export via `unified_api_contracts.features`
      facade.
- [ ] [AGENT] P0. **Per-service registry**. `EXPECTED_FEATURE_GROUPS_BY_SERVICE: dict[str, list[str]]` in
      `unified_api_contracts/canonical/domain/features/registry.py`. Source: each service's `app/calculators/` directory
      listing + the matrix in `codex/02-data/data-lineage-MTDS-features-ml.md` Layer 3 table.
- [ ] [AGENT] P0. **Per-feature-group coverage floor**. `FEATURE_COVERAGE_START: dict[tuple[str, str], date]` mirroring
      `SOURCE_COVERAGE_START` shape. Default = epoch when not declared.
- [ ] [AGENT] P0. **Tests**. UAC unit tests assert: (a) every service in `EXPECTED_FEATURE_GROUPS_BY_SERVICE` has a
      corresponding directory in workspace; (b) every entry in `FEATURE_REQUIRED_INPUTS` references a real
      source/data_type from existing UAC registries; (c) DAG has no cycles.

### 1B — UTL

- [ ] [AGENT] P0. **`unified_trading_library/manifest/freshness.py::ManifestFreshnessCache(ttl_seconds=60)`**. Methods:
      `is_now_captured(row_key) -> bool`, `refresh()` on TTL expiry, `bulk_load(skip_set)` at startup. Reference impl:
      `/tmp/fill_missing_ohlcv.py` `_refresh_captured_cache` + `_is_now_captured`. Tests must cover concurrent-write
      race: two workers picking up same row_key from a stale skip-set; one's `is_now_captured` returns True after the
      other's `record_captured`; loser skips.
- [ ] [AGENT] P0. **Public API**: re-export from `unified_trading_library.manifest`. Document the 60s TTL default and
      the trade-off explicit in CLAUDE.md (don't drop below 30s — burns GCS reads).

**Phase 1 success**: UAC + UTL pass quickmerge; downstream services can
`from unified_api_contracts.features import FEATURE_REQUIRED_INPUTS, EXPECTED_FEATURE_GROUPS_BY_SERVICE, FEATURE_COVERAGE_START`
and `from unified_trading_library.manifest import ManifestFreshnessCache`.

## Phase 2 — Service integrations (PARALLEL)

### 2A — Replace per-service DAGs with UAC import

- [ ] [AGENT] P1. **features-onchain-service**: delete local feature_group → required_inputs DAG; replace with
      `from unified_api_contracts.features import FEATURE_REQUIRED_INPUTS`. Writegate's `assert_no_lookahead(...)`
      already reads from this; just point at the new SSOT.
- [ ] [AGENT] P1. **features-sports-service**: same.
- [ ] [AGENT] P1. **features-delta-one-service**: same.

### 2B — Adopt `ManifestFreshnessCache`

- [ ] [AGENT] P1. **features-sports-service BatchHandler**: instantiate `ManifestFreshnessCache(ttl_seconds=60)` at
      handler init; call `cache.is_now_captured(row_key)` before any expensive remote call (per-source API fetch).
      Reference: CLAUDE.md "Manifest concurrency principle" rule.
- [ ] [AGENT] P1. **features-volatility-service orchestrator**: same. Skip if manifest already says captured; avoids
      redundant IV-surface fits under concurrent backfill.

### 2C — deployment-api denominator clip

- [ ] [AGENT] P1. **`data_status_service.py`**:
  - Add `_clip_dates_to_feature_coverage(service, feature_group, start, end)` mirroring the sports clip helper at lines
    39-50. Reads UAC `FEATURE_COVERAGE_START`.
  - `_build_feature_group_breakdown` (line 3684): denominator = clipped_dates ×
    `EXPECTED_FEATURE_GROUPS_BY_SERVICE[service]` (instead of inferring from what's been written).
    `found = captured + empty_confirmed`. `missing = attempted_failed`. Same shape as sports.
  - Endpoint `/data_status?check_feature_groups=true` (line 2288) returns honest expected/found/missing per
    feature_group.

**Phase 2 success**: per-service QG passes; data-status feature-coverage % matches honest expected/found/missing when
verified against deployment-ui DataStatusTab on a representative shard.

## Phase 3 — Phantom audit + sanity replay

- [ ] [AGENT] P2. **`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`**: extend `--asset-group` to
      accept `features` (or add `--features` flag). Probe feature parquet paths via UAC SSOT candidate-path helper
      (mirror sports' `candidate_parquet_paths`). New drift axes: timeframe hive casing, feature_group empty-check
      (parquet exists but is 0 rows or all-NaN beyond writegate's NaN-threshold). Regression test: synthesise a phantom
      row + missing parquet; audit flags it.
- [ ] [AGENT] P2. **Same-region GCE smoke run** of the audit in `--dry-run` against the features manifest (per CLAUDE.md
      cross-region listing perf rule). Confirm zero phantoms or document genuine drift.
- [ ] [AGENT] P3. **Sanity replay** — pick 3 small representative shards (one DeFi onchain, one CeFi delta-one, one
      sports), recompute. Assert: (a) features-\* services no longer carry inlined DAGs (grep returns 0); (b)
      data-status feature-coverage % matches expected (denominator clip works); (c) phantom audit dry-run output is
      parseable.

**Phase 3 success**: features manifest is now under the same phantom-audit regime as raw data; data-status shows honest
features coverage end-to-end.

## Success criteria

| Criterion                                                                                                          | Gate |
| ------------------------------------------------------------------------------------------------------------------ | ---- |
| `FEATURE_REQUIRED_INPUTS`, `EXPECTED_FEATURE_GROUPS_BY_SERVICE`, `FEATURE_COVERAGE_START` declared in UAC + tested | C2   |
| Three features-\* services consume UAC DAG (no inlined duplicates)                                                 | C5   |
| `ManifestFreshnessCache` in UTL + adopted by features-sports + features-volatility                                 | C5   |
| data-status feature-coverage % uses UAC denominator + coverage-start clip                                          | C5   |
| Phantom audit covers features manifest                                                                             | C5   |
| Sanity replay passes on 3 representative shards                                                                    | B2   |

## Anti-patterns

- Don't redefine `LookaheadBiasError` or `available_at` stamping helpers — writegate owns them. Import.
- Don't redefine `AVAILABILITY_AT_SEMANTICS` taxonomy — writegate owns. Reuse.
- Don't keep per-service DAGs alive in parallel with the UAC SSOT (workspace "delete deprecated code" rule).
- Don't tune `ManifestFreshnessCache` TTL below 30s — CLAUDE.md says it burns GCS reads for marginal gain.
- Don't add a fallback "if UAC registry missing, infer from manifest" — that's the bug we're fixing.

## Coordination with writegate

- Watch writegate's commit stream on `live-defi-rollout`; rebase as needed.
- If writegate's Phase 2.D landed before this plan starts, the per-source `available_at` stamping shape is fixed —
  confirm `FEATURE_REQUIRED_INPUTS.available_at_rule` semantics match writegate's `AVAILABILITY_AT_SEMANTICS` exactly.
  If divergent, treat as a writegate amendment, not a fork.
