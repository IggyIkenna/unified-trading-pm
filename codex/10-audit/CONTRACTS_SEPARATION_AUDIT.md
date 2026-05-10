---
scope: [engineer, admin]
---

# Contracts Separation of Concerns — Audit Report

> Updated 2026-03-15 to reflect UAC Citadel Architecture v2 layout.

**Generated:** 2026-03-04 **Scope:** unified-api-contracts (external + normalised + internal subpackage), schema usage
across 62 repos

---

## 1. Separation Rules (SSOT)

| Rule                                             | Location                                                                                 |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| **Internal contracts**                           | Component-to-component API contracts only → `unified_api_contracts.internal`             |
| **Schemas used by a component within itself**    | `unified_api_contracts.internal` OR `unified_api_contracts` (canonical/external surface) |
| **Schemas that map/normalise external→internal** | unified-api-contracts                                                                    |
| **Service-owned output schemas**                 | schemas/output_schemas.py per service — no cross-repo imports                            |

---

## 2. Structure Summary

### 2.1 unified-api-contracts

| Area                             | Purpose                                                                               |
| -------------------------------- | ------------------------------------------------------------------------------------- |
| unified_api_contracts/external/  | Raw external API schemas per venue (60+ subpackages)                                  |
| unified_api_contracts/canonical/ | Canonical schemas: domain, errors, execution, normalize                               |
| schemas/                         | Shared API schemas: accounts, analytics, defi, derivatives, errors                    |
| Root                             | canonical_mappings, domain_config, endpoint_registry, venue_constants, venue_manifest |

**Schema audit matrix:** `unified-api-contracts/docs/SCHEMA_AUDIT_MATRIX.md` — auto-generated Provider × Schema Type
(✓/~/—, canonical target). Regenerate: `python scripts/generate_schema_audit_matrix.py`. Use for auditing usage,
orphaned schemas, import errors, missing functionality.

### 2.2 unified_api_contracts.internal (subpackage of unified-api-contracts)

| Module                | Key Schemas                                                                            |
| --------------------- | -------------------------------------------------------------------------------------- |
| internal/events.py    | LifecycleEventType, EventSeverity, ServiceMode, PubSubLifecycleEventMessage            |
| internal/features.py  | DeltaOneFeatureRecord, OptionsIvRecord, FeatureSnapshotRequest, CrossTimeframeFeatures |
| internal/market_data/ | CanonicalOHLCV, CanonicalTrade, CanonicalOrderBook, CanonicalLiquidation               |
| internal/ml.py        | InferenceRequest, InferenceResult, ModelMetadata, TrainingJobRequest/Result            |
| internal/positions/   | CeFiPosition, DeFiLendingPosition, DeFiLPPosition, DeFiStakingPosition                 |
| internal/pubsub.py    | PubSubMessageEnvelope, FillEventMessage, MarketTickMessage, RiskAlertMessage           |
| internal/risk.py      | PreTradeCheckRequest/Response, RiskStatus, ExposureSummary                             |
| internal/defi.py      | GasCostAction, GasCostEstimate                                                         |

---

## 3. Violations

### 3.1 Canonical market schemas duplicated (P0)

market-tick-data-service/market_tick_data_service/market_interface defines CanonicalTrade, CanonicalOrderBook,
CanonicalTicker, CanonicalLiquidation in own schemas.py; `unified_api_contracts.internal` also has these. Three sources
of truth.

**Fix:** UMI imports from `unified_api_contracts.internal`; remove local definitions.

### 3.2 ML inference schemas duplicated (P1)

ml-inference-service uses ml_inference_service.models instead of `unified_api_contracts.internal.ml`.

**Fix:** Migrate ml-inference-service to `unified_api_contracts.internal.ml`.

### 3.3 Risk types duplicated (P1)

risk-and-exposure-service defines PreTradeCheckRequest/Response, RiskMetrics, ExposureSummary;
`unified_api_contracts.internal.risk` has same.

**Fix:** risk-and-exposure-service imports from `unified_api_contracts.internal.risk`.

### 3.4 InstrumentDefinition duplicated (P2)

instruments-service and market-tick-data-service both define InstrumentDefinition.

**Fix:** Add to UIC reference; both import.

---

## 4. Orphan Schemas

| Schema                                         | Package         | Status                              |
| ---------------------------------------------- | --------------- | ----------------------------------- |
| InferenceRequest, InferenceResult              | UIC ml.py       | ml-inference uses own; UIC orphaned |
| GasCostAction, GasCostEstimate                 | UIC defi.py     | Used by execution-service           |
| DeltaOneFeatureRecord, FeatureSnapshotRequest  | UIC features.py | TBD                                 |
| CircuitBreakerEventMessage, HealthAlertMessage | UIC pubsub.py   | TBD                                 |

See: unified-trading-pm/plans/archive/orphan-contracts-utilization.plan.md

---

## 5. Audit Score

| Metric         | Value |
| -------------- | ----- |
| Violations     | 5     |
| Orphan schemas | 4+    |
| Repos with AC  | 9     |
| Repos with UIC | 15    |
