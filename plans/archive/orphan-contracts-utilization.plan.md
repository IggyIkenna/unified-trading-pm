# Orphan Contracts Utilisation Plan

**Status:** Active (Phase 1 complete; Phase 2+ pending — augmented by Plan #0c findings) **Created:** 2026-03-04
**Related:** unified-trading-codex/10-audit/CONTRACTS_SEPARATION_AUDIT.md. Schema normalization completion plan — UAC
normalization coverage (all external schemas → canonical) is part of contracts utilization; orphan schemas without
normalizers are in scope. **Feeds from:** [schema_contracts_full_audit.plan.md](schema_contracts_full_audit.plan.md)
(Plan #0c) — comprehensive 60-repo orphan scan will append new orphan schemas to the table below.

---

## Purpose

Schemas in unified-api-contracts and unified-internal-contracts that are not imported anywhere are "orphans". This plan
proposes testing and utilising them. **Decision required:** Use, deprecate, or leave as-is.

---

## Orphan Schemas (from audit)

| Schema                                         | Package         | Notes                                  |
| ---------------------------------------------- | --------------- | -------------------------------------- |
| InferenceRequest, InferenceResult              | UIC ml.py       | ml-inference-service uses own models   |
| DeltaOneFeatureRecord, FeatureSnapshotRequest  | UIC features.py | features-delta-one uses output_schemas |
| OptionsIvRecord, FuturesTermStructureRecord    | UIC features.py | TBD                                    |
| CircuitBreakerEventMessage, HealthAlertMessage | UIC pubsub.py   | TBD                                    |

---

## Options

**A. Migrate consumers** — ml-inference to UIC ml.py; features services to UIC features.py **B. Add tests** — Unit tests
in UIC/UAC that instantiate each schema **C. Deprecate** — Remove superseded schemas **D. Document** — Mark as
future-facing

---

## Recommended

1. Phase 1: Add unit tests for all UIC/UAC schemas (Option B)
2. Phase 2: Per-schema — ML types migrate (A); feature types migrate if aligned
3. Phase 3: Deprecate confirmed superseded (C)
4. Phase 4: Align with schema normalization completion — ensure orphan external schemas get normalizers per UAC
   ideology.

---

## Decision Log

| Date       | Decision                     | Owner |
| ---------- | ---------------------------- | ----- |
| 2026-03-04 | Plan created; pending review | —     |

## Phase 1 Completed (2026-03-05)

- Added `unified-internal-contracts/tests/unit/test_orphan_schemas.py` with 8 tests for:
  - ml.py: InferenceRequest, InferenceResult
  - features.py: DeltaOneFeatureRecord, FeatureSnapshotRequest, OptionsIvRecord, FuturesTermStructureRecord
  - pubsub.py: CircuitBreakerEventMessage, HealthAlertMessage
- ml-inference-service migrated to UIC InferenceRequest (import from unified_internal_contracts)
