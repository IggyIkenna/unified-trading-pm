---
scope: [engineer, admin]
---

# CeFi Cross-Exchange Spread

> **Asset class:** CeFi **Strategy type:** Arbitrage (spread reversion) **Strategy ID pattern:**
> `QUANT_CROSS_EXCHANGE_{ASSET}`

## Overview

ML-driven cross-exchange spread strategy that exploits fee-adjusted price discrepancies between two venues (e.g. Binance
vs Kraken). This is NOT pure instant arbitrage (impractical at ~500ms exchange latency). Instead, the strategy uses ML
to predict spread direction, takes a position betting on reversion, and unwinds when the spread normalises. Entry and
exit are gated by z-score thresholds on the fee-adjusted spread, with a maximum hold period as a safety stop.

## Token / Position Flow

```
Start:  WALLET:USDT on Venue A + WALLET:USDT on Venue B

Step 1 - FEATURE INGEST: Receive fee_adjusted_spread_bps and fee_adjusted_spread_zscore
         from CrossInstrumentFeatures service
Step 2 - ENTRY CHECK: |spread_zscore| >= entry_zscore (default 1.5)
         - spread_zscore > 0 -> direction_signal = -1.0 (fade: venue A overpriced, sell A / buy B)
         - spread_zscore < 0 -> direction_signal = +1.0 (fade: venue B overpriced, sell B / buy A)
Step 3 - HOLD: Maintain position until exit condition
Step 4 - EXIT CHECK (any of):
         - |spread_zscore| < exit_zscore (default 0.3) -> spread reverted
         - bars_held >= max_hold_bars (default 120) -> forced exit (safety)

Wallet after deploy:
  - Venue A: {ASSET} LONG or SHORT (leg A)
  - Venue B: {ASSET} SHORT or LONG (leg B, opposite of A)
```

## Instruments

| Instrument Key             | Venue   | Type      | Role                |
| -------------------------- | ------- | --------- | ------------------- |
| `WALLET:USDT` (Venue A)    | Binance | Spot      | Margin for leg A    |
| `WALLET:USDT` (Venue B)    | Kraken  | Spot      | Margin for leg B    |
| `{VENUE_A}:{TYPE}:{ASSET}` | Binance | Spot/Perp | Long or short leg A |
| `{VENUE_B}:{TYPE}:{ASSET}` | Kraken  | Spot/Perp | Opposite leg B      |

## Key Features Consumed

| Feature                      | Source Service            | SLA | Used For                            |
| ---------------------------- | ------------------------- | --- | ----------------------------------- |
| `fee_adjusted_spread_bps`    | features-cross-instrument | 1s  | Signal: spread magnitude after fees |
| `fee_adjusted_spread_zscore` | features-cross-instrument | 1s  | Signal: entry/exit z-score gating   |

**Fee model:** Per-venue maker/taker fees are embedded in config. Default BTC factory uses:

- Binance: maker 1.0 bps, taker 1.0 bps
- Kraken: maker 1.6 bps, taker 2.6 bps

The fee_adjusted_spread_bps already accounts for roundtrip costs on both legs.

## PnL Attribution

| Component     | Settlement Type | Mechanism                                           |
| ------------- | --------------- | --------------------------------------------------- |
| `spread_pnl`  | Mark-to-market  | Profit from spread convergence after entry          |
| `fee_drag`    | Per-trade       | Roundtrip maker/taker fees on both venues           |
| `funding_pnl` | `FUNDING_8H`    | Net funding if using perps (venue A rate - venue B) |
| `slippage`    | Per-trade       | Execution slippage on both legs                     |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target     | Notes                                         |
| -------------------- | ---------- | --------------------------------------------- |
| Target annual return | TBD        |                                               |
| Target Sharpe ratio  | TBD        |                                               |
| Max drawdown         | TBD        |                                               |
| Max leverage         | 1x per leg | Market-neutral when both legs are hedged      |
| Capital scalability  | TBD        | Limited by venue liquidity differential       |
| Entry threshold      | 1.5 sigma  | `entry_zscore` on fee-adjusted spread         |
| Exit threshold       | 0.3 sigma  | `exit_zscore` -- spread reverted sufficiently |
| Max hold period      | 120 bars   | `max_hold_bars` -- forced exit safety stop    |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 50ms       | 200ms      |                     |
| Feature -> signal      | 1ms        | 5ms        |                     |
| Signal -> instruction  | 5ms        | 20ms       |                     |
| Instruction -> fill    | 100ms      | 500ms      |                     |
| **End-to-end**         | **156ms**  | **725ms**  | **No**              |

**Note:** Both legs must be filled within a tight window to avoid leg risk. Execution-service handles simultaneous order
routing to both venues.

## Execution Details

- **Venues:** Binance + Kraken (BTC default); configurable via `venue_a` / `venue_b`
- **Order types:** Market on both legs for simultaneous execution
- **Atomic execution required?** Yes -- both legs must execute together to avoid single-leg exposure
- **Rebalancing:** Event-driven on each spread feature update; forced exit at max_hold_bars
- **Gas budget:** N/A (CeFi)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern         | Exposure Type    | Used For                     |
| -------------------------- | ---------------- | ---------------------------- |
| `{VENUE_A}:{TYPE}:{ASSET}` | Notional (leg A) | Leg A position size          |
| `{VENUE_B}:{TYPE}:{ASSET}` | Notional (leg B) | Leg B position size (hedged) |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Threshold         | Action on Breach          |
| --------------- | ----------- | ----------------- | ------------------------- |
| `delta`         | Yes         | Net delta drift   | Rebalance legs            |
| `basis`         | Yes         | Spread divergence | Exit if max_hold exceeded |
| `funding`       | Yes (perps) | Net funding cost  | Factor into hold decision |
| `protocol_risk` | No          | --                | --                        |
| `liquidity`     | Yes         | Venue depth       | Reduce size on thin books |

## Margin & Liquidation

- **Margin model:** Isolated per venue (separate margin pools on Binance and Kraken)
- **Health factor threshold:** N/A (CeFi margin maintenance)
- **Liquidation penalty:** Venue-dependent; leg risk if one venue liquidates before the other
- **Monitoring:** Per-bar spread z-score and bars_held counter

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue   | Secret Name               | Testnet Available? | Notes           |
| ------- | ------------------------- | ------------------ | --------------- |
| Binance | `exec-{client}-binance-*` | Yes                |                 |
| Kraken  | `exec-{client}-kraken-*`  | No                 | Paper mode only |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Accounts on both venue A and venue B with USDT margin
2. **Secret Manager:** Per-venue: `exec-{client}-{venue}-api-key`, `exec-{client}-{venue}-api-secret`
3. **Config:** New `CrossExchangeConfig` with `strategy_id`, `venue_a`, `venue_b`, `underlying_symbol`, fee model
4. **Position isolation:** One strategy instance per client per asset pair
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                       | Restart?        |
| ----------------- | ---------------------------------- | --------------- |
| strategy-service  | New config entry in GCS            | No (hot-reload) |
| execution-service | New client routing for both venues | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Margin health time series (Stream D)
- Position breakdown (both legs)

### Strategy-specific views (extensions)

- Fee-adjusted spread z-score time series with entry/exit bands
- Venue A vs Venue B price overlay
- Spread basis points histogram
- Hold duration distribution

## Testing Stage Status

| Stage        | Status  | Notes                                   |
| ------------ | ------- | --------------------------------------- |
| MOCK         | Done    | Static seed data + paper execution      |
| HISTORICAL   | Done    | Backtested BTC Binance/Kraken spread    |
| LIVE_MOCK    | Pending | Real spread data + paper execution      |
| LIVE_TESTNET | Pending | Binance testnet only (Kraken lacks one) |
| BATCH_REAL   | Pending |                                         |
| STAGING      | Pending |                                         |
| LIVE_REAL    | Pending |                                         |

## References

- **Strategy implementation:**
  `strategy-service/strategy_service/engine/strategies/cross_exchange/cross_exchange_strategy.py`
- **Config type:** `strategy-service/strategy_service/config.py` (`CrossExchangeConfig`)
- **Signal type:** `CrossExchangeSignal` dataclass in same file
- **Config schema:** `strategy-service/docs/CONFIG_SCHEMA.md`
- **Strategy modes:** `strategy-service/docs/STRATEGY_MODES.md`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
