# Plan: UIC Orphan Contracts Utilization

## Status: Active

## Created: 2026-03-10

## Source: check_uic_adoption.py --orphans-only (57 schemas, no terminal consumer importer)

These 57 schemas are in UIC `__all__` and have clear intended consumers but are not yet explicitly imported by any of
the 20 scanned repos (18 terminal services + UMI + USEI). The GHA `contract-adoption-check` job will fail until these
are wired in or moved to `EXEMPT_CLASSES`.

---

## Group 1: market-tick-data-service (2)

Target: `market-tick-data-service` — should import these for its canonical output models.

- `MarketTickMessage` — canonical websocket tick published to PubSub
- `DerivativeTickerMessage` — derivative-specific tick (funding rate, open interest)

**Action:** Add `from unified_internal_contracts import MarketTickMessage, DerivativeTickerMessage` to
`market_tick_data_service/publisher.py` or equivalent output layer.

---

## Group 2: ml-training-service (3)

Target: `ml-training-service` — job lifecycle schemas.

- `TrainingJobRequest`
- `TrainingJobResult`
- `TrainingPeriod`

**Action:** Import in `ml_training_service/job_manager.py` or training runner.

---

## Group 3: ml-inference-service + feature services (3)

Target: `ml-inference-service` + `features-*` services.

- `MLPredictionMessage` — prediction output published to PubSub
- `FeatureUpdateMessage` — feature snapshot published downstream
- `FeatureSnapshotRequest` — request schema for on-demand feature pull

**Action:** Import in ml-inference output layer and each features-\* publisher.

---

## Group 4: features-sports-service + instruments-service (13)

Sports reference data schemas — belong in sports feature pipeline.

- `FixtureRecord`, `FixtureEventsRecord`, `FixtureLineupsRecord`, `FixturePlayerStatsRecord`
- `LeagueRecord`, `TeamRecord`, `PlayerRecord`, `RefereeRecord`
- `RoundRecord`, `StandingsRecord`, `InjuryRecord`, `VenueRecord`

Also: `DataSourceConstraint`, `OHLCVSource` → `instruments-service` reference data layer.

**Action:** Import sports schemas in `features_sports_service/data_models.py` or equivalent; import
`DataSourceConstraint`/`OHLCVSource` in `instruments_service/reference/` layer.

---

## Group 5: execution-service (6)

Execution lifecycle and risk schemas.

- `ExecutionResultMessage` — canonical fill/order result published to PubSub
- `OrderRequestMessage` — inbound order request canonical schema
- `LiquidationMessage` — liquidation event published downstream
- `CircuitBreakerEventMessage` — circuit breaker state change event
- `RiskAlertMessage` — risk limit breach alert
- `HealthAlertMessage` — service health alert (also alerting-service)

**Action:** Import in `execution_service/engine/` or `execution_service/publishers/`.

---

## Group 6: strategy-service (2)

- `StrategySignalMessage` — canonical signal published to PubSub
- `DataBroadcastDetails` — data broadcast lifecycle detail (also used by market-data-processing-service)

**Action:** Import in `strategy_service/signal_publisher.py`.

---

## Group 7: alerting-service (3)

- `AlertContextData` — structured alert context payload
- `AuthFailureDetails` — auth failure event detail
- `AuthFailureEvent` — auth failure event envelope

**Action:** Import in `alerting_service/handlers/` or alert router.

---

## Group 8: risk-and-exposure-service (4)

- `MarginState` — current margin snapshot
- `InternalPosition` — internal position tracking model
- `AccountState` — account-level state snapshot
- `PositionUpdateMessage` — position delta published to PubSub

**Action:** Import in `risk_and_exposure_service/models/` or position tracker.

---

## Group 9: features-onchain-service (7)

DeFi / onchain data schemas.

- `DeFiLPPosition` — liquidity provider position
- `DeFiStakingPosition` — staking position
- `GasCostAction`, `GasCostEstimate` — gas cost tracking
- `LendingEntry` — DeFi lending position
- `FeeStructure` — protocol fee structure
- `OnchainDataFreshnessConfig` — staleness config for onchain data

**Action:** Import in `features_onchain_service/models/` or data normalizer.

---

## Group 10: all services via UTL/UEI lifecycle (10)

Service lifecycle event schemas — should be imported wherever services publish lifecycle events. Currently UTL wraps
these internally but services should own the type reference.

- `ServiceLifecycleEventMessage` — service start/stop lifecycle envelope
- `ConfigChangedDetails`, `ConfigChangedEvent` — config reload event
- `StartedDetails`, `StartedEvent` — service started lifecycle
- `StoppedDetails`, `FailedDetails`, `FailedEvent` — service stopped/failed lifecycle
- `SecretAccessedDetails`, `SecretAccessedEvent` — secret access audit event
- `DataIngestionDetails`, `DataIngestionCompletedDetails` — data ingestion lifecycle

**Action:** Import in each service's `UnifiedCloudService` subclass or event publisher setup. Start with
`execution-service` and `strategy-service` as the highest-value consumers.

---

## Group 11: options pipeline (1)

- `CanonicalOptionsChainEntry` — UIC's own version (UAC has a parallel); used in options normalizer. Belongs in
  `strategy-service` options module or `execution-service` strike mapping.

**Action:** Confirm whether services should use the UIC or UAC version; consolidate if duplicate.

---

## Priority Order

1. Groups 1-3 (market data + ML pipeline) — high-signal; GHA gate fails loudest here
2. Groups 5-6 (execution + strategy) — core trading path
3. Group 4 (sports reference data) — next major feature area
4. Groups 7-10 — lifecycle + monitoring; lower urgency but complete the picture

## Tracking

Gate: `system-integration-tests/.github/workflows/smoke-test-gate.yml` — `contract-adoption-check` job Checker:
`unified-internal-contracts/scripts/check_uic_adoption.py --orphans-only`
