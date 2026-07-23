---
doc_type: codex-ssot
title: Manual Trade Booking Architecture
summary:
  "Operator-initiated trade booking across all instrument types via two UI surfaces (Book Trade page + in-context
  ManualTradingPanel) and two ManualExecutionMode paths — EXECUTE routes to venue (same path as automated), RECORD_ONLY
  records a CanonicalFill directly (OTC). One ManualInstructionAuditLog row per action (trade + ML training-control),
  GCS/S3 immutable audit persistence."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    deployment-service,
    execution-service,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [execution, defi, ui, audit, kill-switch, uac, ssot]
related:
  [
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/kill-switch-event-bus.md,
    /codex/04-architecture/operational-modes.md,
  ]
created: 2026-03-27
authoritative_for:
  [
    manual trade booking architecture,
    ManualInstruction schema,
    manual-instruction audit-log persistence,
    RECORD_ONLY vs EXECUTE manual execution modes,
  ]
referenced_by:
  [
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/risk-preflight-flow.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    /codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Manual Trade Booking Architecture

## Overview

The unified trading system supports Citadel-grade manual trade booking across all instrument types (CeFi, DeFi, TradFi,
Sports, Prediction). Two UI surfaces and two execution modes provide comprehensive coverage for operator-initiated
trades.

## Operational Mode

`OperationalMode` enum in UIC `modes.py` defines per-service operational modes:

| Mode     | Value      | Description                           |
| -------- | ---------- | ------------------------------------- |
| LIVE     | `live`     | Automated strategy execution          |
| MANUAL   | `manual`   | Operator-entered instructions via API |
| BACKTEST | `backtest` | Historical replay                     |
| PAPER    | `paper`    | Live market data, simulated execution |

Injected as `OPERATIONAL_MODE` env var. Execution-service CLI validates against this enum at startup -- invalid values
fail loud.

## Dual Execution-Service Deployment

Every deployment cluster runs two execution-service instances:

- `execution-service` -- LIVE operational mode (automated strategies from strategy-service)
- `execution-service:manual` -- MANUAL operational mode (operator booking via API + live backup)

If the LIVE instance goes down, the MANUAL instance serves as backup. Cluster configs:
`deployment-service/configs/clusters/*.yaml`.

## Execution Modes

`ManualExecutionMode` enum in UIC `execution.py`:

| Mode        | Value         | Description                                                         |
| ----------- | ------------- | ------------------------------------------------------------------- |
| EXECUTE     | `execute`     | Route to venue via orchestrator (same path as automated trades)     |
| RECORD_ONLY | `record_only` | Skip venue, record CanonicalFill directly (OTC, missed, simulation) |

### EXECUTE Flow

```
ManualTradingPanel / Book Trade page
  -> POST /manual/instruction (execution_mode=execute)
    -> _validate_instruction_request() (venue from UAC registry, side, execution_mode)
    -> ManualOperationHandler.build_instruction()
    -> LiveOrchestrator.execute_instruction()
    -> CanonicalFill published to fill-events-{venue}
    -> Downstream: position-service, PnL, risk, settlement
```

### RECORD_ONLY Flow

```
Book Trade page / ManualTradingPanel (record_only toggle)
  -> POST /manual/instruction (execution_mode=record_only)
    -> _validate_instruction_request() (skip venue validation for OTC)
    -> _record_fill_directly()
      -> Create CanonicalFill (fill_id=UUID, order_id=instruction_id)
      -> log_event("MANUAL_FILL_RECORDED")
      -> persist_audit_log()
      -> Return ManualInstructionResponse(status="RECORDED")
```

## ManualInstruction Schema

Extended `ManualInstruction` in UIC `execution.py`:

| Field            | Type                | Description                   |
| ---------------- | ------------------- | ----------------------------- |
| instruction_id   | str                 | UUID for idempotency          |
| submitted_by     | str                 | Operator identity (OAuth sub) |
| venue            | str                 | Target venue or counterparty  |
| execution_mode   | ManualExecutionMode | EXECUTE or RECORD_ONLY        |
| client_id        | str                 | Org hierarchy: client         |
| strategy_id      | str                 | Org hierarchy: strategy       |
| portfolio_id     | str                 | Org hierarchy: portfolio/book |
| category         | str                 | Instrument category           |
| counterparty     | str                 | OTC counterparty identifier   |
| source_reference | str                 | External trade ID             |

## UI Surfaces

### Back-Office Booking Page (`/services/trading/book`)

Full-page form for dedicated back-office operations:

- Hierarchical org/client/strategy selectors
- Category tabs (CeFi Spot, CeFi Derivatives, DeFi, TradFi, Sports, Prediction)
- EXECUTE vs RECORD_ONLY toggle
- Algo selection (MARKET, TWAP, VWAP, ICEBERG, SOR, BEST_PRICE, BENCHMARK_FILL)
- Pre-trade compliance checks (EXECUTE mode)
- URL prefill support (`?prefill=`) for reconciliation corrections

### In-Context ManualTradingPanel

Sheet/drawer alongside order book and candle visualization:

- Same algo selection and execution mode toggle
- Contextual to the instrument being viewed
- Pre-trade compliance checks

## Dynamic Venue List

Venue validation uses UAC `CAPABILITY_DECLARATIONS` registry instead of hardcoded list. `_get_supported_venues()` in
`manual_instruction_api.py` resolves venues dynamically with `@lru_cache`.

For RECORD_ONLY mode, venue validation is skipped (OTC trades have arbitrary counterparty names).

## API Endpoints

### Trade actions (execution-service)

| Method | Path                      | Description                                        |
| ------ | ------------------------- | -------------------------------------------------- |
| POST   | /manual/instruction       | Submit manual instruction (EXECUTE or RECORD_ONLY) |
| POST   | /manual/cancel            | Cancel pending instruction                         |
| POST   | /manual/amend             | Amend pending instruction                          |
| GET    | /manual/instructions/{id} | Get instruction status                             |
| GET    | /manual/venues            | Dynamic venue list from UAC registry               |
| GET    | /manual/algos             | Supported execution algorithms                     |

### ML training-control actions (ml-training-service)

Per `cross_cutting_may_23_deliverables` deliverable #4 BUILD #3 — DART manual ML training trigger. Distinct API surface
(training-control is not a trade) but persists to the **same audit log** for unified operator-action timeline.

| Method | Path                           | Description                                                          |
| ------ | ------------------------------ | -------------------------------------------------------------------- |
| POST   | /training/{archetype}/{action} | Apply lifecycle action (`pause` / `resume` / `retrain`) to archetype |
| GET    | /training/{archetype}/status   | Get current training-loop status per archetype                       |
| GET    | /training/audit/{request_id}   | Lookup audit row for a control request                               |

Action axis is the closed-set `ManualMLTrainingAction` enum (`PAUSE` / `RESUME` / `RETRAIN`).

## Audit log surface

Single `ManualInstructionAuditLog` row per operator-initiated action across BOTH trade + ML control axes. Dispatched via
`action_category: ManualAuditCategory` (`MANUAL_TRADE` populates `manual_instruction`; `ML_TRAINING_CONTROL` populates
`ml_training_request` + optionally `ml_training_response`).

Consumed by:

- **pnl-attribution-service** — rolls up manual fills by `strategy_id` alongside automated fills.
- **batch-live-reconciliation-service** — isolates execution alpha (manual vs simulated fills).
- **alerting-service** — emits `strategy_id` per fired alert when manual action triggers a threshold.

Persistence happens at the API boundary BEFORE forwarding (EXECUTE flow) or directly after recording the fill
(RECORD_ONLY flow). Audit-log row is the durable record; downstream processing failures do not invalidate the audit row.

## Audit log persistence (GCS / S3)

Path SSOT lives at `unified_api_contracts/internal/manual_audit_paths.py`. Callers MUST use the path-helper functions;
inline f-string paths are banned (would drift from the SSOT).

### Object key shape

```text
manual_audit/{YYYY-MM-DD}/{action_category}/{audit_id}.jsonl
```

Concrete examples:

- `manual_audit/2026-05-12/manual_trade/aud-defi-100.jsonl`
- `manual_audit/2026-05-12/ml_training_control/aud-ml-200.jsonl`

### Bucket name (env-tiered)

Resolved via
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name( cloud=..., kind="manual-audit", env=...)`.
The `manual-audit` bucket-kind entry lands in `deployment-service/configs/cloud-providers.yaml` per the
[`bucket_name_ssot_canonicalisation_2026_05_10`](../../plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md)
Phase 0i tail (slot 4 owned scope) — proposed shape:

```yaml
manual-audit: "manual-audit-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}" # GCP
manual-audit: "unified-trading-manual-audit-${DEPLOYMENT_ENV}-${AWS_ACCOUNT_ID}" # AWS
```

### Why separate from operational events bucket

Operational events at `gs://{pid}-events-{env}/events/{service}/...` are short-retention (~30d) hourly-partitioned
streams optimised for log-tail. Manual audit rows have different requirements:

- **Long retention** for compliance (≥7 years).
- **Append-only / immutable** — operator actions are durable record.
- **Indexed by wallet / strategy / submitted_by** for pnl-attribution + batch-live-recon + alerting queries.

A dedicated `manual-audit` bucket (env-tiered) gives operations independent retention + access controls + lifecycle
policies without polluting the operational events surface.

### Date partition + UTC convention

`YYYY-MM-DD` is computed from `ManualInstructionAuditLog.persisted_at` in UTC. Cross-day operator sessions (e.g. an
action submitted at 2026-05-12T23:59 UTC) partition by UTC date, not operator-local timezone — keeps the audit log
queryable without timezone-conversion logic.

### Action-category sub-partition

The `action_category` directory matches `ManualAuditCategory` value strings (`manual_trade` / `ml_training_control`).
Consumers selectively read one category for cheaper queries (e.g. pnl-attribution only needs `manual_trade/`;
ml-training-service introspection only needs `ml_training_control/`).

### File format

Single-row line-delimited JSON (`.jsonl`). Object keys include the `.jsonl` suffix even for the common single-row write
case — readers iterate via `readlines()` for forward-compat with future multi-row append batches. Pydantic round-trip
via `ManualInstructionAuditLog.model_dump_json()` / `.model_validate_json()`.

## Wallet-tier wiring (DeFi manual trades)

When `ManualInstruction.wallet_id` is non-empty (DeFi action), the `/manual/instruction` endpoint performs a pre-trade
wallet-tier validation BEFORE forwarding to the executor. The validation consumes the operator-target
`WalletProvisioningConfig` (per slot 4 wallet schema at `unified_api_contracts/internal/domain/defi/wallet_config.py`)
and computes a `WalletSpendingPreCheckResult` row that is persisted into the audit log.

### Validation algorithm (execution-service runtime)

1. **Kill-switch check** — load `WalletProvisioningConfig.kill_switch_id`; if armed in the live `KillSwitchBus` state,
   set `kill_switch_armed=True`, `passed=False`, `denial_reason="kill_switch_armed"`. Short-circuit (skip cap checks).
2. **Per-tx cap** — compute `amount_usd` from `manual_instruction.quantity × price` (or reference price for market
   orders) and call `SpendingCaps.is_within_per_tx(amount_usd)`. Populate `per_tx_check`.
3. **Per-hour cap** — query `position-balance-monitor-service` for the rolling 1h spend on this wallet; populate
   `per_hour_check`.
4. **Per-day cap** — same for rolling 24h; populate `per_day_check`.
5. **Per-protocol cap** — if `manual_instruction.venue` matches a `SpendingCaps.per_protocol_usd` key, check the
   per-protocol limit; populate `per_protocol_check`.
6. **Aggregate** — `passed = (kill_switch_armed is False) and all 4 cap checks True`. If `passed is False`, populate
   `denial_reason` with the failed check name (`kill_switch_armed` / `per_tx_cap_exceeded` / `per_hour_cap_exceeded` /
   `per_day_cap_exceeded` / `per_protocol_cap_exceeded`).

### UI surface (DART panel — Harsh T6)

The DART `ManualTradingPanel` "DeFi Action" tab (per `dart-manual-trade-spec.md` § 4 BUILD #1) extends the form with:

- **Wallet selector** — dropdown of the operator's `(client × archetype)` wallets from `WalletMappingConfig`. Disabled
  rows for wallets where `kill_switch_id` is currently armed (with hover tooltip explaining the kill-switch state).
- **Per-row kill-switch button** — wallet-tier kill-switch arm/disarm action; each click writes a
  `ManualInstructionAuditLog` row with `action_category=ManualAuditCategory.MANUAL_TRADE`, `manual_instruction=None`,
  and a stub instruction documenting the kill-switch event (per cross-side handoff with slot 4 — final shape may move to
  a dedicated `KillSwitchAction` audit category in a follow-up cycle).
- **Spending-caps display** — per-wallet `SpendingCaps` (per-tx / per-hour / per-day / per-protocol) surfaced read-only
  above the submit button, with a "remaining headroom" indicator pulled from the position-balance-monitor rolling-window
  query that drives the validation algorithm above.
- **Pre-submit validation echo** — after the operator clicks Submit but before the request fires, the client calls
  `POST /manual/instruction/precheck` (same payload, dry-run) and renders the resulting `WalletSpendingPreCheckResult`
  so the operator sees the validation outcome without spending actual quote-asset capital.

Per-row UI components map to slot 4's `WalletProvisioningConfig` fields: `kill_switch_id` → kill-switch button state ·
`spending_caps` → caps display · `allowed_protocols` → enabled-action filter · `signing_surface` → pending-signing-modal
route.

## SSOT

- ManualInstruction schema: `unified-api-contracts/unified_api_contracts/internal/execution.py`
- ManualExecutionMode enum: same file
- ManualMLTrainingAction enum: same file (DART BUILD #3)
- ManualAuditCategory enum: same file (audit-log dispatch axis)
- MLTrainingControlRequest / MLTrainingControlResponse: same file
- ManualInstructionAuditLog schema: same file
- OperationalMode enum: `unified-api-contracts/unified_api_contracts/internal/modes.py`
- API handler (trade): `execution-service/execution_service/api/manual_instruction_api.py`
- API handler (training control): `ml-training-service/ml_training_service/api/training_control_api.py` (TBD per BUILD
  #3)
- Cluster configs: `deployment-service/configs/clusters/*.yaml`
- DART scope spec: `/codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md`
