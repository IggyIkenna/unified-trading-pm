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

| Method | Path                      | Description                                        |
| ------ | ------------------------- | -------------------------------------------------- |
| POST   | /manual/instruction       | Submit manual instruction (EXECUTE or RECORD_ONLY) |
| POST   | /manual/cancel            | Cancel pending instruction                         |
| POST   | /manual/amend             | Amend pending instruction                          |
| GET    | /manual/instructions/{id} | Get instruction status                             |
| GET    | /manual/venues            | Dynamic venue list from UAC registry               |
| GET    | /manual/algos             | Supported execution algorithms                     |

## SSOT

- ManualInstruction schema: `unified-api-contracts/unified_api_contracts/internal/execution.py`
- ManualExecutionMode enum: same file
- OperationalMode enum: `unified-api-contracts/unified_api_contracts/internal/modes.py`
- API handler: `execution-service/execution_service/api/manual_instruction_api.py`
- Cluster configs: `deployment-service/configs/clusters/*.yaml`
