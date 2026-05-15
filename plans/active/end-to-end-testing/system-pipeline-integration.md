# System Pipeline Integration Test — DeFi Backtest Grid

## Purpose

Validate the **cross-service data flow** for a full DeFi backtest pipeline. Per-service E2E tests (001–023) verify each
service in isolation. This test verifies the **handoff points** between services — schema parity, GCS path conventions,
and data completeness as artifacts flow through the pipeline.

## Pipeline Under Test

```
instruments-service (DEFI)
    │ GCS: instruments-store-defi-{project_id}/day=YYYY-MM-DD/
    ▼
market-tick-data-service (DEFI)
    │ GCS: market-tick-data-store-defi-{project_id}/day=YYYY-MM-DD/
    ▼
market-data-processing-service (DEFI)
    │ GCS: processed-market-data-store-defi-{project_id}/day=YYYY-MM-DD/
    ▼
features-service (onchain family)
    │ GCS: features-store-onchain-{project_id}/day=YYYY-MM-DD/
    ▼
strategy-service (DEFI strategies)
    │ GCS: strategy-store-{project_id}/backtest/{grid_id}/
    │ Outputs: strategy results + StrategyInstructions
    ▼
execution-service (backtest mode)
    │ GCS: execution-store-{project_id}/backtest/{run_id}/
    │ Outputs: simulated fills (execution_fills layout)
    ▼
pnl-attribution-service
    │ GCS: pnl-store-{project_id}/pnl/day=YYYY-MM-DD/
    │ Outputs: PnL attribution per strategy, alpha vs beta decomposition
    ▼
position-balance-monitor-service
    │ Outputs: reconstructed positions from backtest fills
```

## Pre-Requisites

- All per-service E2E tests (001–016, 018) have passed their Phase 1 (startup validation)
- GCS buckets exist for dev environment (or `CLOUD_MOCK_MODE=true` for local-only run)
- Date range with known data: use `2026-03-20` to `2026-03-21` (or mock seed dates)

## Test Matrix

### Phase 1: Instruments → Tick Data Handoff

| #   | Step                                                                                            | Verify                                                                                            | Status |
| --- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------ |
| 1.1 | Run instruments-service `--asset-group DEFI --start-date 2026-03-20 --end-date 2026-03-20`      | Parquet written to `instruments-store-defi-*` (not cefi — see Issue #11)                          |        |
| 1.2 | Inspect instrument schema                                                                       | Columns: `symbol`, `venue`, `instrument_type`, `protocol`, `chain_id`, `contract_address` present |        |
| 1.3 | Run market-tick-data-service `--asset-group DEFI --start-date 2026-03-20 --end-date 2026-03-20` | Reads instruments from 1.1, fetches tick data, writes to `market-tick-data-store-defi-*`          |        |
| 1.4 | Tick data references valid instruments                                                          | Every `symbol` in tick data exists in instruments output from 1.1                                 |        |
| 1.5 | Empty instrument handling                                                                       | If instruments returns 0 for a protocol, tick-data skips that protocol gracefully                 |        |

### Phase 2: Tick Data → Processed Market Data → Features Handoff

| #   | Step                                                                                  | Verify                                                                                                                       | Status |
| --- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------ |
| 2.1 | Run MDPS `--asset-group DEFI --start-date 2026-03-20 --end-date 2026-03-20`           | Reads tick data from 1.3, produces candles/processed data                                                                    |        |
| 2.2 | Processed data schema                                                                 | Candle schema: `open`, `high`, `low`, `close`, `volume`, `timestamp` + DeFi fields (`tvl`, `pool_fee_tier` where applicable) |        |
| 2.3 | Run features-service (onchain family) `--start-date 2026-03-20 --end-date 2026-03-20` | Reads processed market data + on-chain sources, writes features                                                              |        |
| 2.4 | Feature completeness                                                                  | Features written for: lending (Aave rates, utilization), TVL (DefiLlama), staking (LST rates), protocol rewards              |        |
| 2.5 | Feature temporal alignment                                                            | Feature timestamps align with market data timestamps (no look-ahead bias)                                                    |        |

### Phase 3: Features → Strategy Backtest Handoff

| #   | Step                                                                                    | Verify                                                                                                                           | Status |
| --- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 3.1 | Run strategy-service `--asset-group DEFI --start-date 2026-03-20 --end-date 2026-03-20` | Reads features from 2.3, runs DeFi strategies                                                                                    |        |
| 3.2 | Strategy types executed                                                                 | AAVE_LENDING, BASIS_TRADE, STAKED_BASIS, RECURSIVE_STAKED_BASIS all produce results                                              |        |
| 3.3 | Strategy output schema                                                                  | Each result has: `strategy_id`, `instrument`, `signals`, `pnl_series`, `metrics`                                                 |        |
| 3.4 | StrategyInstruction generation                                                          | Strategy outputs include `StrategyInstruction` artifacts for execution-service                                                   |        |
| 3.5 | Instruction schema                                                                      | Instructions contain: `instruction_type` (SWAP/LEND/BORROW/STAKE), `instrument`, `quantity`, `price`, `timestamp`, `strategy_id` |        |
| 3.6 | Feature dependency validation                                                           | `--skip-dependency-check` not needed — features from 2.3 are found                                                               |        |

### Phase 4: Strategy Instructions → Execution Backtest Handoff

| #   | Step                                                                                                    | Verify                                                                                                                      | Status |
| --- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------ |
| 4.1 | Run execution-service `--operation backtest --mode batch --start-date 2026-03-20 --end-date 2026-03-20` | Reads StrategyInstructions from 3.4, runs matching-engine simulation                                                        |        |
| 4.2 | Instruction consumption                                                                                 | All instructions from strategy-service consumed (count match)                                                               |        |
| 4.3 | DeFi instruction routing                                                                                | SWAP → Uniswap sim, LEND/BORROW → Aave sim, STAKE → staking sim                                                             |        |
| 4.4 | Realistic assumptions applied                                                                           | Gas costs, slippage, pool depth impact, MEV exposure modeled in fills                                                       |        |
| 4.5 | Fill output schema                                                                                      | Fills contain: `fill_id`, `order_id`, `strategy_id`, `instrument`, `side`, `quantity`, `price`, `fee`, `timestamp`, `venue` |        |
| 4.6 | Fill output path                                                                                        | Written to `execution_fills/` layout that PnL-attribution expects                                                           |        |
| 4.7 | Execution alpha metrics                                                                                 | TCA metrics produced: slippage vs arrival price, implementation shortfall                                                   |        |

### Phase 5: Execution Fills → PnL Attribution Handoff

| #   | Step                                                                                                         | Verify                                                                                     | Status |
| --- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | ------ |
| 5.1 | Run pnl-attribution-service `--operation compute --mode batch --start-date 2026-03-20 --end-date 2026-03-20` | Reads fills from 4.6, computes PnL attribution                                             |        |
| 5.2 | Fill ingestion                                                                                               | All fills from execution-service consumed (count match)                                    |        |
| 5.3 | Per-strategy attribution                                                                                     | PnL computed per `strategy_id` — matches strategies from Phase 3                           |        |
| 5.4 | Alpha vs beta decomposition                                                                                  | Strategy alpha = strategy PnL - benchmark return                                           |        |
| 5.5 | Execution alpha from fills                                                                                   | Execution alpha = arrival price - fill price (slippage impact)                             |        |
| 5.6 | DeFi fee attribution                                                                                         | Gas fees, protocol fees, MEV costs attributed separately                                   |        |
| 5.7 | Cross-validation                                                                                             | Strategy-service PnL (from 3.3) ≈ PnL-attribution output (within execution cost tolerance) |        |

### Phase 6: Execution Fills → Position Reconstruction

| #   | Step                                                    | Verify                                                               | Status |
| --- | ------------------------------------------------------- | -------------------------------------------------------------------- | ------ |
| 6.1 | Feed backtest fills to position-balance-monitor-service | PositionTracker reconstructs positions from fill events              |        |
| 6.2 | Position state consistency                              | Net position per instrument = sum(buy fills) - sum(sell fills)       |        |
| 6.3 | Position × PnL reconciliation                           | Unrealised PnL from positions matches PnL-attribution mark-to-market |        |

### Phase 7: Full Pipeline Mock Mode

Run the entire pipeline in `CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local` to verify mock parity:

| #   | Step                          | Verify                                                     | Status |
| --- | ----------------------------- | ---------------------------------------------------------- | ------ |
| 7.1 | Full pipeline mock run        | Every service produces mock output in local-dev-cache      |        |
| 7.2 | Schema parity                 | Mock output schemas match real output schemas at each step |        |
| 7.3 | Downstream consumption        | Each service can consume mock output from upstream service |        |
| 7.4 | No cloud credentials required | Entire pipeline runs without GCS/Secret Manager access     |        |

## GCS Path Convention Verification

| Service                           | Expected bucket pattern                         | Layout                                    |
| --------------------------------- | ----------------------------------------------- | ----------------------------------------- |
| instruments-service               | `instruments-store-defi-{project_id}`           | `day=YYYY-MM-DD/{venue}.parquet`          |
| market-tick-data-service          | `market-tick-data-store-defi-{project_id}`      | `day=YYYY-MM-DD/{venue}/{symbol}.parquet` |
| market-data-processing-svc        | `processed-market-data-store-defi-{project_id}` | `day=YYYY-MM-DD/{candle_size}/`           |
| features-service (onchain family) | `features-store-onchain-{project_id}`           | `day=YYYY-MM-DD/{feature_group}/`         |
| strategy-service                  | `strategy-store-{project_id}`                   | `backtest/{grid_id}/{strategy_id}/`       |
| execution-service                 | `execution-store-{project_id}`                  | `execution_fills/day=YYYY-MM-DD/`         |
| pnl-attribution-service           | `pnl-store-{project_id}`                        | `pnl/day=YYYY-MM-DD/`                     |

Verify at each handoff that the downstream service reads from the exact path the upstream service wrote to.

## Schema Parity Checks (Handoff Contracts)

These are the critical schema contracts between services. A mismatch here breaks the pipeline silently.

| Handoff                 | Producer field           | Consumer expectation            | Check                        |
| ----------------------- | ------------------------ | ------------------------------- | ---------------------------- |
| instruments → tick-data | `symbol`, `venue`        | Same `symbol`, `venue` lookup   | String equality              |
| tick-data → MDPS        | `timestamp`, OHLCV       | Candle aggregation input        | Polars dtype match           |
| MDPS → features         | Candle schema            | Feature calculator input schema | Column superset              |
| features → strategy     | Feature columns by group | Strategy engine feature lookup  | Feature name registry match  |
| strategy → execution    | `StrategyInstruction`    | Instruction parser in exec-svc  | UAC schema version alignment |
| execution → PnL         | `execution_fills` layout | `PnlDomainAdapter.read_fills()` | Parquet column match         |
| execution → position    | `FillEventMessage`       | `PositionTracker` event handler | Event schema match           |

## Failure Modes to Test

| #   | Scenario                               | What breaks                                | Expected behavior                             |
| --- | -------------------------------------- | ------------------------------------------ | --------------------------------------------- |
| F.1 | Instruments returns 0 DeFi protocols   | No tick data to fetch                      | Tick-data skips DEFI, logs warning            |
| F.2 | Tick data missing for 1 of 3 protocols | Features computed for 2/3 protocols        | Strategy runs with partial features, warns    |
| F.3 | Strategy produces 0 instructions       | Execution backtest has nothing to simulate | Execution returns empty results, no crash     |
| F.4 | Execution fills have unexpected column | PnL-attribution fails to parse             | Clear schema error, not silent wrong PnL      |
| F.5 | PnL date range has no fills            | Empty attribution output                   | Returns cleanly, no crash, logs empty date    |
| F.6 | Pipeline mid-failure (features crash)  | Strategy has stale/missing features        | Strategy detects missing deps, fails or warns |

## Relationship to Per-Service E2E

This plan **depends on** per-service E2E tests passing first:

- `001_instruments_service.md` Phase 4.3 DEFI must PASS (currently FAIL — wrong bucket)
- `002_market_tick_data_service.md` Phase 2 must cover DEFI category
- `007_features_onchain_service.md` must pass all phases
- `014_strategy_service.md` Phase 2.3 DEFI must PASS
- `015_execution_service.md` Phase 2.1 backtest must PASS
- `016_pnl_attribution_service.md` Phase 2.1 compute must PASS

This plan is **not runnable** until the per-service DEFI category tests pass. Fix per-service issues first, then run
this integration pipeline.
