# Portable Backtests Plan

**Deadline:** March 12, 2026 (with all plans complete) **Reference:** MASTER_PRE_DEPLOYMENT_PLAN_CHAIN.md,
mvp-universe.yaml **Order:** Plan 7 in chain

---

## Objective

Deliver portable backtests for at least one strategy per category (CEFI, DeFi, Sports, TradFi) so that:

- Backtests run in CI and locally without external API keys (VCR/mock data)
- Results are reproducible
- Same engine path used for live trading (batch-live symmetry)

---

## Strategy Scope (by March 20 live trading)

| Category   | Strategy                                                | Backtest Target                                       |
| ---------- | ------------------------------------------------------- | ----------------------------------------------------- |
| **Sports** | Arb                                                     | Portable arb backtest                                 |
| **CEFI**   | ML signal                                               | Portable ML swing prediction backtest                 |
| **TradFi** | ML signal                                               | Portable ML swing prediction backtest                 |
| **DeFi**   | 4 MVP: staking, lending, recursive staking, basis trade | Portable backtest for each (or representative subset) |

---

## Portable Criteria

1. **No live API calls in CI** — Use VCR cassettes, fixtures, or mock adapters
2. **Deterministic** — Same input → same output
3. **Fast** — Completes in &lt;5 min per strategy (or marked integration)
4. **Shared engine** — Same strategy logic as live mode (batch-live symmetry)

---

## Per-Category Tasks

### Sports (Arb)

- Strategy-service or sports execution path
- VCR cassettes for odds/line feeds
- Portable arb backtest script

### CEFI (ML signal)

- ml-inference-service or strategy-service
- Fixtures for OHLCV + features
- Portable ML swing prediction backtest

### TradFi (ML signal)

- Same ML framework as CEFI
- TradFi fixtures (ES/MES/SPY)
- Portable ML swing prediction backtest

### DeFi (4 MVP strategies)

- staking, lending, recursive_staking_with_flash_loans, basis_trade_long_spot_short_perp
- The Graph / protocol mocks
- Portable backtest per strategy (or combined fixture)

---

## References

- VCR_CREDENTIAL_RECORDING_PLAN.md
- mvp-universe.yaml strategies
- batch-live-symmetry.mdc
- TEST_FAILURE_ACTION_PLAN.md
