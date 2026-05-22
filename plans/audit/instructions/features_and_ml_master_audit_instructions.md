---
name: features_and_ml_master_audit_instructions
type: audit-instructions
epic: features_and_ml_master
assigned_vm: vm-ml
tier: L1
last_updated: 2026-05-22
---

# Features + ML Master — Audit Instructions

## Epic Scope

features-service (8 feature families: DeFi, CeFi, TradFi, Sports, Predictions, Macro, On-Chain, Cross-Asset), ml-service
(inference + training pipelines), IS→features contract. All feature schemas must be in UAC; no local definitions.

## Triggers

- Weekly (minimum cadence)
- After model retrain (verify training pipeline manifest compliance)
- When strategy-service reports feature shape mismatch at inference time
- After any UAC feature schema change
- After `ml_repo_consolidation` completes (verify merged repo structure)

## Checklist

- [ ] (a) **All 8 feature families have active adapters**: each family has at least one adapter with batch+live parity.
      Find: `rg "class.*Feature.*Adapter|class.*Handler" features-service/ --include="*.py" -l` Verify: 8 families
      covered (DeFi, CeFi, TradFi, Sports, Predictions, Macro, On-Chain, Cross-Asset)

- [ ] (b) **IS→features contract**: `is_features_contract_audit_2026_05_20.md` findings all addressed. Check: any
      outstanding RED items in that audit have been absorbed into active plans

- [ ] (c) **ml-service inference end-to-end test**: inference path has a test that exercises the full pipeline (features
      → model → signal) with mock data. Find: `rg "inference|predict" ml-service/tests/ --include="*.py" -l` (or merged
      ml-service path post-consolidation)

- [ ] (d) **Training pipeline manifest compliance**: training outputs emit manifest rows with correct schema*version,
      `asset_group`, and `available_at` (write-time, not read-time derivation). Read: training pipeline output path —
      verify `record_captured()` called with cluster*\* kwargs

- [ ] (e) **Feature schemas in UAC**: no local feature schema definitions in features-service or ml-service. Grep:
      `rg "class.*Schema|dataclass" features-service/ --include="*.py"` — every schema must import from UAC

- [ ] (f) **No os.getenv() in feature computation**: all config via `UnifiedCloudConfig`. Grep:
      `rg "os\.getenv" features-service/ ml-service/ --include="*.py"` — should be 0 hits

- [ ] (g) **PYTEST_UNIT_DIR override wired**: `quality-gates.sh` uses `PYTEST_UNIT_DIR="tests/"` to collect all
      per-family tests (not just root-level `tests/unit/`). Check: `features-service/scripts/quality-gates.sh` — verify
      override is set before `source base-service.sh`

- [ ] (h) **ml-service repo consolidation complete**: if `ml_repo_consolidation` plan is complete, verify merged repo
      has no duplicate code paths or conflicting imports. Check: `ml_repo_consolidation_2026_05_19.md` completion status


### Batch vs Live Parity

- (batch-live) **Batch adapter output**: confirm each adapter in scope produces manifest rows with
  `capture_status=captured` for a known date range using the batch invocation path (`--mode batch`). Run against
  mock data if real upstream is unavailable (`CLOUD_MOCK_MODE=true`).
- (live-adapter) **Live adapter parity**: for each batch adapter, confirm the live adapter exists, accepts the same
  schema, and emits `available_at` at write-time (not read-time). Confirm no `DIVERGENT_EMPTY` rows for live mode.
- (mock-upstream) **Mock upstream pattern**: audits for this data layer MUST be runnable without hitting real APIs.
  Document fixture paths and `CLOUD_MOCK_MODE=true` invocations so downstream services can be audited independently.

## Success Criteria

- All 8 checklist items GREEN
- features-service QG exits 0 with full per-family test collection
- IS→features contract audit has zero open RED items

## Output Format

Result file at `plans/audit/results/features_and_ml_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
