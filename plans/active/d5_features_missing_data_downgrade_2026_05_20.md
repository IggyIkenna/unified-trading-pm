---
name: d5-features-missing-data-downgrade-2026-05-20
title: D5 — Features missing-data downgrade plan
created: 2026-05-20
author: ikenna (slot-8)
status: active
priority: P0
deadline: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
parent_plan: master_to_live_defi_2026_05_23.md
source_audits:
  - plans/audit/mtds_features_contract_audit_2026_05_20.md # C4
  - plans/audit/features_strategy_contract_audit_2026_05_20.md # C6
  - plans/audit/results/dependency_propagation_2026_05_20_summary.md # A5
related_plans:
  - d4_mtds_adapters_preflight_2026_05_20.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
prerequisite_plans:
  - d4_mtds_adapters_preflight_2026_05_20.md # preflight must be in place before downgrade gates can fire
---

# D5 — Features missing-data downgrade plan

> **Ordering step 5** in the Phase-E execution chain. Requires D4 (MTDS preflight) partially done.
>
> **REVIEW-BLOCKING status**: C6 audit found 5 P0 violations. APD strategy engine re-derives price spread from raw
> per-leg data instead of consuming the `paired_price_dispersion` feature stream produced by features-service.
> Strategy-service has zero manifest emission. Strategy batch handler has a hardcoded inline bucket f-string. These
> block the May-23 live deployment.

## What this covers

1. **Warn-but-proceed fixes in features-service** (A5/C4): EIA adapters silently return `{}` on empty
2. **APD engine consuming paired_price_dispersion** (C6): strategy must consume the feature stream
3. **cross_instrument handler record_empty** (C6): skipped groups must emit honest absence
4. **Strategy manifest emission** (C6/C2): zero manifest emission on strategy write paths
5. **Strategy bucket-SSOT** (C6): hardcoded `f"strategy-store-{project_id}"` inline

## P0 findings from audits

### From C6 (features → strategy)

| Finding                                                                                                          | Severity          | File                                                   |
| ---------------------------------------------------------------------------------------------------------------- | ----------------- | ------------------------------------------------------ |
| APD engine re-derives spread from raw per-leg data — `paired_price_dispersion` feature produced but not consumed | P0-C6-1           | `strategy-service/cli/handlers/batch_handler.py`       |
| No per-pair viability filter in strategy APD engine — dead venues not skipped                                    | P0-C6-2           | `batch_handler.py`                                     |
| Strategy APD engine doesn't consume `paired_price_dispersion` from features stream                               | P0-C6-3           | `batch_handler.py`                                     |
| Zero manifest emission for strategy outputs — `_write_instructions_to_gcs()` never calls `record_captured`       | P0-C6-4           | `batch_handler.py:1261-1296`, `gcs_storage_service.py` |
| Hardcoded bucket: `f"strategy-store-{project_id}"` inline f-string                                               | P0-Bucket-SSOT    | `batch_handler.py:1276`                                |
| `cross_instrument/cli/handlers/batch_handler.py` — no `record_empty` for skipped groups                          | P0-Manifest-Empty | `cross_instrument/batch_handler.py`                    |

### From C4 + A5 (features warn-but-proceed)

| Finding                                                                         | Severity | File                                               |
| ------------------------------------------------------------------------------- | -------- | -------------------------------------------------- |
| `eia_ng.py:70` — `logger.warning("no data rows"); return {}` (warn-but-proceed) | P0-A5    | `features_service/commodity/adapters/eia_ng.py`    |
| `eia_crude.py:61` — identical warn-but-proceed pattern                          | P0-A5    | `features_service/commodity/adapters/eia_crude.py` |
| `ml-inference-service batch_handler.py:79,259` — warn-but-proceed               | P0-A5    | `ml-inference-service`                             |
| `ml-service batch_handler.py:79,259` — warn-but-proceed                         | P0-A5    | `ml-service`                                       |
| `strategy-service batch_handler.py:130,502` — warn-but-proceed                  | P0-A5    | `strategy-service`                                 |

## Remediation backlog (ordered)

### Phase 1 — EIA adapters + features warn-but-proceed (quick fixes)

- [ ] [AGENT] P0. Fix `features_service/commodity/adapters/eia_ng.py:70`:
  - Replace `self.logger.warning("EIA storage API returned no data rows"); return {}` with
    `self.logger.warning("EIA storage API returned no data rows"); record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO); raise DependencyError(fail_fast=False)`
  - Note: fail_fast=False because EIA data is supplemental — downstream handler decides whether to abort
- [ ] [AGENT] P0. Fix `features_service/commodity/adapters/eia_crude.py:61` — same pattern
- [ ] [AGENT] P0. Fix `strategy-service/...batch_handler.py:130,502` — replace warn-but-proceed with DependencyError
      raise
- [ ] [AGENT] P1. Fix `ml-inference-service batch_handler.py:79,259` and `ml-service batch_handler.py:79,259` — same
      pattern (lower priority, not on May-23 critical path for DeFi)

### Phase 2 — cross_instrument handler honest absence

- [ ] [AGENT] P0. Add `record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)` to
      `features-service/cross_instrument/cli/handlers/batch_handler.py` for every skipped-group path
  - Grep: `rg '_persist_results|skip' features_service/cross_instrument/ --type py` to find all skip paths
  - Every group that is skipped (due to empty upstream, missing instruments, etc.) must emit `record_empty`

### Phase 3 — Strategy manifest emission

- [ ] [AGENT] P0. Add `ManifestWriter.record_captured(...)` to `strategy-service/_write_instructions_to_gcs()`
      (`batch_handler.py:1261-1296`):
  - Call after successful GCS write
  - `available_at` = datetime.now(UTC)
  - Cluster validation kwargs required (per QG MissingClusterValidationError rule)
- [ ] [AGENT] P0. Replace `f"strategy-store-{project_id}"` at `batch_handler.py:1276` with
      `resolve_bucket_name("strategy-store", project_id=project_id)` (or the correct UTL resolver call)
- [ ] [AGENT] P0. Add `record_captured` to `gcs_storage_service.py` if it is the canonical write path (verify which of
      `_write_instructions_to_gcs` vs `gcs_storage_service` is the actual write path)

### Phase 4 — APD engine: consume paired_price_dispersion feature stream

- [ ] [AGENT] P0. Add `paired_price_dispersion` to `_MULTI_GROUP_STRATEGIES` map in strategy APD engine:
  - Features-service already produces `paired_price_dispersion` parquet per (pair, date)
  - Strategy APD engine must load this feature instead of re-deriving spread from raw per-leg prices
  - Grep: `rg 'paired_price_dispersion' strategy-service/ --type py` to find current (empty) hook
- [ ] [AGENT] P0. Add per-pair viability filter: before processing a pair, check that both legs have non-stale features
      manifest rows; emit `VENUE_DATA_ABSENT` event when a configured venue is missing from APD features dict

### Phase 5 — Quality gates

- [ ] [AGENT] P0. Run `cd strategy-service && bash scripts/quality-gates.sh` — must be green after Phase 3 changes
- [ ] [AGENT] P0. Run `cd features-service && bash scripts/quality-gates.sh` — must be green after Phase 1-2 changes
- [ ] [AGENT] P0. Run cassette parity: `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py`

## Success criteria

- [ ] Phase 1: `rg 'warn.*no data\|return {}.*warning' features_service/commodity/ --type py` returns 0 hits for EIA
      adapters; strategy warn-but-proceed removed
- [ ] Phase 2: `rg 'record_empty' features_service/cross_instrument/ --type py` returns hits; no `_persist_results` path
      without record_empty
- [ ] Phase 3: `rg 'record_captured' strategy-service/ --type py` returns hits on write paths; no inline
      `strategy-store-` f-strings
- [ ] Phase 4: `rg 'paired_price_dispersion' strategy-service/ --type py` returns hits in APD engine consumer map; APD
      engine no longer re-derives spread from raw
- [ ] Phase 5: strategy-service + features-service QG green

## Full-execution criterion

> strategy-service QG green. features-service QG green. One end-to-end batch run of the APD strategy for one DeFi pair
> (e.g. ETH/WBTC) consumes `paired_price_dispersion` feature (not raw prices), and the strategy manifest shows
> `record_captured` rows for the strategy-store outputs. EIA adapters raise DependencyError on empty upstream (verified
> via unit test with mock returning empty response).

## Temporary states + their canonical follow-up plans

- `ml-inference-service` and `ml-service` warn-but-proceed fixes (Phase 1, P1): targeted post-May-23 since ML inference
  is not on the DeFi critical path. Named successor: `ml_service_hardening_2026_06_01.md` (to be created when ML track
  becomes active).
- DependencyError fail_fast=False for EIA adapters: acceptable for now; tighten to fail_fast=True when features-service
  commodity track has full expected_coverage() wiring (D2 plan).
