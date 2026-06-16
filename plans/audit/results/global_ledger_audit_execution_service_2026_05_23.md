---
type: analysis
title: Global Ledger Audit — execution-service
epic: global_ledger_pnl_attribution_master
auditor: slot-7
date: "2026-05-23"
status: complete
source:
  - global_ledger_pnl_attribution_discovery_2026_05_21.md Phase 1 audit task
scope: execution-service emission-side audit
---

# Global Ledger Audit: execution-service (2026-05-23)

**Audit type**: Emission-side. execution-service is the primary writer of fill, transfer, stake, borrow, and funding-PnL
events. This audit maps what it actually emits today vs the target `InstructionLedger` `LedgerRow` schema.

**Files read**: all Python source under `execution_service/` (full tree, ~200 source files). Key files:
`transfer_coordinator.py`, `engine/handlers/transfer_handler.py`, `engine/handlers/trade_handler.py`,
`engine/handlers/stake_handler.py`, `engine/handlers/borrow_handler.py`, `engine/live/pbms_publisher.py`,
`providers/funding_pnl_accrual.py`, `results/save_operations.py`, `engine/modes/live/data_sink.py`,
`adapters/order_adapter.py`, `defi_execution/orchestrators/recursive_loop_orchestrator.py`, `pnl_attribution/rows.py`,
`isolation_policy.py`, `compliance/compliance_reporter.py`.

**Sampling vs exhaustive**: exhaustive grep across all `.py` files for `log_event`, `record_captured`, `ManifestWriter`,
`CrossClientTransferForbiddenError`, `_resolve_policy_output_data_type`, `_publish_emission_check`. No sampling — all
patterns searched workspace-wide.

---

## What it emits today

### 1. UTL `log_event(...)` — financial event bus emissions

| Path                                                                                                      | Event name(s)                                                                                                                             | Key fields emitted                                                                                              | Missing LedgerRow fields                                                                                                                                                                                                                                                                                                                        |
| --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `engine/handlers/transfer_handler.py:182`                                                                 | `TRANSFER_INITIATED`                                                                                                                      | `instruction_id`, `transfer_type`, `from_venue`, `to_venue`, `token`, `amount`                                  | `event_id`, `event_type`, `trade_id`, `leg_id`, `parent_event_id`, `timestamp_utc`, `asset_group`, `chain`, `chain_tx_hash`, `gas_paid_native`, `account_id`, `client_id`, `counterparty_client_id`, `asset_canonical_id`, `asset_class`, `delta`, `price`, `fees_in_quote`, `underlying`, `expiry_date`, `option_right`, `strike`, `direction` |
| `engine/handlers/transfer_handler.py:221,231`                                                             | `TRANSFER_CONFIRMED`, `TRANSFER_FAILED`                                                                                                   | `instruction_id`, `transfer_type`, `amount_executed`, `tx_hash`, `error`                                        | Same as above; `tx_hash` present but not as `chain_tx_hash`                                                                                                                                                                                                                                                                                     |
| `engine/handlers/transfer_handler.py:300`                                                                 | `CEX_INTERNAL_TRANSFER_COMPLETED`                                                                                                         | `instruction_id`, `venue`, `exchange_id`, `token`, `amount`, `transfer_id`, `ccxt_params`                       | Same as TRANSFER_INITIATED; no `client_id` in payload                                                                                                                                                                                                                                                                                           |
| `adapters/order_adapter.py:173`                                                                           | `ORDER_CREATED`                                                                                                                           | `client_order_id`, `instrument_id`, `side`, `order_type`, `quantity`, `price`, `time_in_force`                  | `event_id`, `trade_id`, `leg_id`, `parent_event_id`, `timestamp_utc`, `asset_group`, `chain`, `chain_tx_hash`, `gas_paid_native`, `account_id`, `client_id`, `counterparty_client_id`, `asset_canonical_id`, `asset_class`, `delta`, `fees_in_quote`                                                                                            |
| `adapters/order_adapter.py:193`                                                                           | `ORDER_FILLED`                                                                                                                            | `client_order_id`, `exchange_timestamp`, `venue_response_id`, `fill_price`, `fill_quantity`                     | Same; `client_id` absent from payload                                                                                                                                                                                                                                                                                                           |
| `adapters/order_adapter.py:196+`                                                                          | `ORDER_REJECTED`                                                                                                                          | `client_order_id`, `exchange_timestamp`, `venue_response_id`                                                    | Same                                                                                                                                                                                                                                                                                                                                            |
| `adapters/order_adapter.py:137,146`                                                                       | `ORDER_IDEMPOTENCY_CACHE_HIT`, `ORDER_DUPLICATE_SUPPRESSED`                                                                               | `client_order_id`, `staleness_seconds`                                                                          | Not ledger events; operational only                                                                                                                                                                                                                                                                                                             |
| `providers/funding_pnl_accrual.py:149`                                                                    | `FUNDING_PNL_ACCRUED`                                                                                                                     | `venue`, `symbol`, `quantity`, `notional_usd`, `funding_rate_apy_bps`, `tick_interval_seconds`, `delta_pnl_usd` | `event_id`, `event_type`, `trade_id`, `leg_id`, `parent_event_id`, `timestamp_utc`, `asset_group`, `chain`, `chain_tx_hash`, `gas_paid_native`, `account_id`, `client_id`, `counterparty_client_id`, `asset_canonical_id`, `asset_class`, `price`, `fees_in_quote`, `underlying`, `expiry_date`, `option_right`, `strike`, `direction`          |
| `engine/live/pbms_publisher.py:88`                                                                        | `PBMS_POSITION_PUBLISHED` (+ PubSub `AGGREGATED_POSITIONS` topic)                                                                         | `canonical_id`, `venue`, `venue_positions` (Decimal str map)                                                    | Not a ledger fill row; position snapshot only; `client_id` absent                                                                                                                                                                                                                                                                               |
| `defi_execution/orchestrators/recursive_loop_orchestrator.py:211,233,286,321,348,376,396,441,475,518,573` | `LOOP_OPEN_STARTED`, `LOOP_CLOSE_STARTED`, `LOOP_ITER_COMPLETED`, `LOOP_OPEN_COMPLETED`, `LOOP_CLOSE_COMPLETED`, `LOOP_ITER_FAILED`, etc. | `correlation_id`, `chain`, `protocol`, `n_loops`, `ltv_per_loop`, `tx_hash`, `gas_used`, partial position state | `event_id`, `event_type`, `trade_id`, `leg_id`, `parent_event_id`, `timestamp_utc`, `asset_group`, `account_id`, `client_id`, `counterparty_client_id`, `asset_canonical_id`, `asset_class`, `delta`, `price`, `fees_in_quote`; `tx_hash` present but keyed `tx_hash` not `chain_tx_hash`                                                       |
| `defi_execution/monitors/health_factor_monitor.py:76,80,91,107,114,121,131`                               | `STARTED`, `HEALTH_FACTOR_CHECKED`, `HEALTH_FACTOR_BELOW_THRESHOLD`, `LIQUIDATION_RISK_ALERT`                                             | health factor metrics                                                                                           | Operational/monitoring, not ledger                                                                                                                                                                                                                                                                                                              |
| `compliance/compliance_reporter.py:77+`                                                                   | `ORDER_SUBMITTED_MIFID`, `TRADE_REPORTED_MIFID`, `BEST_EXECUTION_CHECKED`                                                                 | `instrument_id`, `venue_id`, `quantity`, `price`, `jurisdiction`                                                | Compliance-specific; not directly ledger rows; missing `client_id`, `account_id`                                                                                                                                                                                                                                                                |

### 2. `ManifestWriter.record_captured(...)` — GCS manifest emissions

| Path                                 | `data_type` value                                             | Row key fields                                               | Notes                                                                                                                                             |
| ------------------------------------ | ------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `results/save_operations.py:749`     | `"execution_fills"`                                           | `date`, `venue`, `strategy_id`, `instruction_type`, `job_id` | Batch mode; `PipelineMode.BATCH_EXECUTION_SERVICE`; no `client_id` in row_key                                                                     |
| `engine/modes/live/data_sink.py:130` | `data_type` (runtime string from queue, typically `"result"`) | `date`, `venue`, `job_id`                                    | Live mode; `PipelineMode.LIVE_WEBSOCKET`; `data_type` is not a fixed constant — it comes from the write queue, defaulting to `"unknown"` if unset |

### 3. Direct GCS writes — parquet / JSON

| Path                                                                  | Output format             | Bucket/path pattern                                                                                    | Content                                                                                                                                                                                                              |
| --------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `results/save_operations.py:_write_canonical_fills()`                 | Parquet (`fills.parquet`) | `gs://<execution_bucket>/execution_fills/date=<date>/mode=<mode>/fills.parquet`                        | Fill DataFrame with columns: `ts_event`, `ts_init`, `fill_id`, `order_id`, `strategy_id`, `venue`, `account_id`, `instrument_id`, `side`, `quantity`, `price`, `liquidity_side`, `commission`, `commission_currency` |
| `results/save_operations.py:_upload_report_to_gcs()`                  | Parquet + JSON            | `gs://<bucket>/results/date=<date>/strategy_id=<strategy_id>/instruction_type=<type>/run_id=<run_id>/` | `orders.parquet`, `fills.parquet`, `positions.parquet`, `equity_curve.parquet`, `summary.json`, `execution_alpha.json`                                                                                               |
| `engine/modes/live/data_sink.py:_write_to_gcs()`                      | JSON                      | `gs://<bucket>/results/<venue>/<date>/<instruction_id>_<timestamp>.json`                               | Full result dict; schema untyped                                                                                                                                                                                     |
| `engine/modes/live/data_sink.py:_flush_to_gcs()` (via `LiveDataSink`) | Parquet                   | `gs://<bucket>/live/fills.parquet`                                                                     | Fills DataFrame; no fixed schema enforcement                                                                                                                                                                         |

### 4. PubSub emissions

| Path                               | Topic                                                                   | Payload shape                                                                                        |
| ---------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `engine/live/pbms_publisher.py:87` | `InternalPubSubTopic.AGGREGATED_POSITIONS` (via `PubSubClient.publish`) | `{"canonical_id": str, "venue": str, "venue_positions": {venue: Decimal_str}, "timestamp": ISO8601}` |

---

## What it consumes

- **MTDS** (market-tick-data-service): tick data / order book snapshots loaded via `data/loaders/`,
  `data/gcs_data_loading.py`, `utils/instrument_resolver.py` — GCS parquet reads (data_types: `trades`, `swaps`,
  `perp_funding`, `lending_indices`, `gas_fees`, `liquidations`, `oracle_prices`)
- **instruments-service**: `InstrumentRecord` resolved via `utils/instrument_resolver.py` +
  `utils/instrument_conversion.py`; no MTDS direct resolve
- **features-service**: feature dicts passed into execution engine from strategy-service caller (not directly fetched by
  execution-service)
- **strategy-service** (upstream caller): `TransferIntent`, `ExecutionInstruction` received via API or event bus
- **Secret Manager**: per-client venue credentials via `load_client_venue_credentials()` in `isolation_policy.py`

---

## Cross-client isolation status

**Status: COMPLIANT at the TransferCoordinator layer; PARTIAL elsewhere**

### Evidence — compliant paths

1. **`TransferCoordinator.execute()` / `validate_intent()`** (`transfer_coordinator.py:233`):
   - Hard raises `CrossClientTransferForbiddenError` when `intent.client_id != self._client_id`.
   - Defence-in-depth second check: calls `assert_client_allowed(intent.client_id)` which raises `CrossClientEventError`
     if the process's `CLIENT_ID` env var mismatches.
   - This is the canonical raise site documented in `codex/04-architecture/client-funds-isolation.md`.

2. **`isolation_policy.assert_client_allowed()`** (`isolation_policy.py:79`):
   - Process-level guard: raises `CrossClientEventError` on any cross-client event bus message.
   - Wired into `engine/modes/live/trigger.py` (cross-client event check at the live trigger layer).

### Evidence — partial / missing enforcement

3. **`engine/handlers/transfer_handler.py`**: Executes transfers via `_adapter` without propagating `client_id` into the
   log_event payloads (TRANSFER_INITIATED, TRANSFER_CONFIRMED, CEX_INTERNAL_TRANSFER_COMPLETED). The `client_id` is not
   emitted in any of the `log_event` calls, making post-hoc audit of cross-client violations from event logs impossible.

4. **`adapters/order_adapter.py`**: `ORDER_CREATED` / `ORDER_FILLED` events do not carry `client_id` in the payload. The
   order adapter does not call `assert_client_allowed()` — it relies on the caller (engine orchestrator) to have already
   validated.

5. **`engine/live/pbms_publisher.py`**: PBMS position update payload (`publish_position_update`) does not carry
   `client_id`. Position data could be inadvertently commingled if the publisher is called from a shared context.

6. **`providers/funding_pnl_accrual.py`**: `FUNDING_PNL_ACCRUED` events do not carry `client_id`. `FundingPnLAccruer`
   has no isolation guard.

7. **`pnl_attribution/rows.py` (`FillAttributionContext`)**: `client_id` IS present as a field in
   `FillAttributionContext` and propagated into `PnLAttributionRow`. However `build_attribution_rows()` does not
   validate that `client_id` matches the process-bound client.

8. **`results/save_operations.py` ManifestWriter `record_captured()`**: `client_id` is not in the row_key. Multiple
   clients' fills from the same venue/strategy would collide in manifest if running in a shared-process deployment
   (should not happen given isolation policy, but the manifest schema does not enforce it).

**Summary**: The critical money-movement path (TransferCoordinator) is correctly guarded. The event/log/manifest
emission paths do not carry `client_id`, which means the audit trail does not provide client-level attribution for
forensic analysis.

---

## Service-output emission semantics compliance

**Status: MISSING — no `_resolve_policy_output_data_type` or `_publish_emission_check` usage found anywhere in
execution-service**

Full grep across all `*.py` files in `execution_service/` for:

- `_resolve_policy_output_data_type` → **0 hits**
- `_publish_emission_check` → **0 hits**

All GCS write paths bypass the canonical service-output emission semantics:

| Write path                                                            | Goes through policy check? | Bypass evidence                                                                                                                             |
| --------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `results/save_operations.py:_write_canonical_fills()`                 | NO                         | Direct `_client.upload_bytes()` call after `build_path()`                                                                                   |
| `results/save_operations.py:_upload_report_to_gcs()`                  | NO                         | Direct `upload_data_sync()` calls                                                                                                           |
| `engine/modes/live/data_sink.py:LiveCloudStorageSink._write_to_gcs()` | NO                         | Direct `_storage.upload_bytes()` call                                                                                                       |
| `engine/modes/live/data_sink.py:LiveDataSink._flush_to_gcs()`         | NO                         | Direct `_storage.upload_batch()` call                                                                                                       |
| ManifestWriter calls in both write paths                              | PARTIAL                    | `ManifestWriter.record_captured()` is called but wrapped in `try/except Exception` catch-all that silently swallows ManifestWriter failures |

**Critical finding**: The ManifestWriter calls are wrapped in bare `except Exception` blocks that log at `DEBUG` level
and continue. This means manifest failures are invisible in normal operation — a manifest write failure produces no
alert, no FAILED event, no retry.

---

## Gap to InstructionLedger target

Per target `LedgerRow` schema:

| Field                    | Status  | Notes                                                                                                                                                |
| ------------------------ | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `event_id`               | MISSING | No UUID assigned to any emitted event in `log_event()` calls                                                                                         |
| `event_type`             | PARTIAL | Event name string is passed as first arg to `log_event()` but is not a typed `LedgerRow.event_type` enum; no mapping to canonical ledger event types |
| `trade_id`               | MISSING | `instruction_id` is present but not mapped to a `trade_id` field                                                                                     |
| `leg_id`                 | MISSING | Not present in any emission path                                                                                                                     |
| `parent_event_id`        | MISSING | Not present; recursive loop `correlation_id` is the closest analogue but is not propagated into fill events                                          |
| `timestamp_utc`          | PARTIAL | `exchange_timestamp` in ORDER_FILLED; timestamp in FundingPnLAccrued; but no uniform `timestamp_utc` field in all emissions                          |
| `asset_group`            | MISSING | Not in any `log_event()` payload; present in GCS path (`results/{venue}/{date}/`) but not in event payloads                                          |
| `venue`                  | PARTIAL | Present in TRANSFER_INITIATED, FUNDING_PNL_ACCRUED, fills parquet; absent from ORDER_CREATED / ORDER_FILLED payloads in a unified way                |
| `chain`                  | PARTIAL | In recursive_loop_orchestrator log_events; absent from cross-chain transfer events                                                                   |
| `chain_tx_hash`          | PARTIAL | `tx_hash` field present in LOOP_ITER_COMPLETED and TRANSFER_CONFIRMED; not canonically named `chain_tx_hash`                                         |
| `gas_paid_native`        | PARTIAL | `gas_used` (integer) in recursive loop events; `gas_price_gwei` in borrow/stake handlers; no unified `gas_paid_native` (wei / lamport unit) field    |
| `account_id`             | MISSING | Not in any `log_event()` payload; present in fills parquet schema as column                                                                          |
| `client_id`              | PARTIAL | Present in `FillAttributionContext` and `PnLAttributionRow`; absent from all `log_event()` financial event payloads                                  |
| `counterparty_client_id` | MISSING | Not present anywhere; cross-client checks only on TransferIntent's single `client_id` field                                                          |
| `asset_symbol`           | PARTIAL | `token` / `symbol` in various events but not as unified `asset_symbol`                                                                               |
| `asset_canonical_id`     | PARTIAL | `canonical_id` in PBMS publisher; `instrument_id` in fills parquet; not consistently emitted as `asset_canonical_id` in event payloads               |
| `asset_class`            | MISSING | Not present in any emission                                                                                                                          |
| `delta`                  | PARTIAL | `quantity` / `amount` / `filled_quantity` present in fills; no unified signed `delta` field                                                          |
| `price`                  | PARTIAL | `fill_price` in ORDER_FILLED; `actual_price` / `benchmark_price` in ExecutionResult; no unified `price` at the log_event layer                       |
| `fees_in_quote`          | PARTIAL | `commission` in fills parquet; `trading_fee` in ExecutionResult; `delta_pnl_usd` in FUNDING_PNL_ACCRUED; not unified as `fees_in_quote`              |
| `underlying`             | MISSING | Not present in any emission                                                                                                                          |
| `expiry_date`            | MISSING | Not present in any emission                                                                                                                          |
| `option_right`           | MISSING | Not present in any emission                                                                                                                          |
| `strike`                 | MISSING | Not present in any emission                                                                                                                          |
| `direction`              | MISSING | Not present; `side` (BUY/SELL) is the closest but `direction` is a different semantic                                                                |

**Field-level summary**: 5 fields MISSING entirely (event_id, leg_id, parent_event_id, asset_class,
underlying/expiry/option_right/strike); 9 PARTIAL (exist in some paths but not canonically named or universally
emitted); 4 fields present in fills parquet schema but not in event-bus payloads.

---

## PnL attribution module status

`execution_service/pnl_attribution/rows.py` ships a `build_attribution_rows()` function that produces
`PnLAttributionRow` instances from `(benchmark_MatchResult, live_MatchResult, FillAttributionContext)`. The function is:

- **Implemented** and referenced by `matching_engine/defi/cost_aggregator.py:build_defi_fill_context()`
- **Pure function** — no I/O, no GCS write, no `log_event()` call
- **Not connected to any write path**: searching the full codebase for callers of `build_attribution_rows()` outside the
  pnl_attribution module and cost_aggregator returns 0 hits. The attribution rows are computed but never persisted to
  GCS, never emitted via `log_event()`, and never manifested.

**Gap**: The PnL attribution compute layer exists but has no downstream write path. `PnLAttributionRow` objects computed
by `build_attribution_rows()` are currently dead-ends.

---

## Summary findings (P0 gaps)

| #   | Finding                                                                                                                                                                                          | Severity |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| 1   | `_resolve_policy_output_data_type` + `_publish_emission_check` not used anywhere in execution-service; all GCS writes bypass canonical service-output emission semantics                         | P0       |
| 2   | ManifestWriter calls wrapped in `except Exception: logger.debug(...)` — manifest failures are silently swallowed                                                                                 | P0       |
| 3   | `client_id` absent from all `log_event()` financial event payloads (ORDER_FILLED, TRANSFER_CONFIRMED, FUNDING_PNL_ACCRUED, etc.) — audit trail has no client attribution                         | P0       |
| 4   | `build_attribution_rows()` returns `PnLAttributionRow` objects that are never written anywhere — PnL attribution compute exists but has no sink                                                  | P0       |
| 5   | Live `LiveCloudStorageSink.data_type` field populated with `"result"` (generic) or `"unknown"` — manifest records have no semantic data_type; downstream consumers cannot distinguish fill types | P1       |
| 6   | `event_id`, `leg_id`, `parent_event_id` missing from all event emissions — no instruction-level event graph possible                                                                             | P1       |
| 7   | `chain_tx_hash` present as `tx_hash` in some DeFi events but not in transfer events — cross-path inconsistency                                                                                   | P1       |
| 8   | `asset_class`, `underlying`, `expiry_date`, `option_right`, `strike` entirely absent from all emissions — options/structured product support not wired                                           | P2       |
