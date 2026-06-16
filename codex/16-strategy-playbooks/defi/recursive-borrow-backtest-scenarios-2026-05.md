---
scope: [engineer, admin]
---

# Recursive-Borrow Backtest Scenario Taxonomy — 2026-05

> **SSOT status**: ACTIVE — Phase 12 deliverable (2026-05-15). Gates Family 1 + Family 2 recursive-borrow cells from
> `design-shipped` → `live-ready`. Do NOT archive until all 17 cells carry verdicts in the per-cell matrix below.
>
> **Implementation chain**: `UAC internal/architecture_v2/backtest_scenarios.py` (`BACKTEST_SCENARIOS` list +
> `BacktestScenario` dataclass) → `strategy-service/tests/integration/test_recursive_borrow_scenarios.py` →
> `e2e-testing/scripts/defi/recursive_borrow_paper_smoke.py` → this document (taxonomy + success criteria + SSOT
> alignment)

## Scope

Closed set of 14 backtest scenarios that every Family 1 + Family 2 cell must clear before Phase 13 live deployment.
Scenarios are grouped into three categories by what they stress:

| Category    | Count | What it stresses                                      |
| ----------- | ----- | ----------------------------------------------------- |
| A — Funding | 4     | Funding-regime changes (Family 2 only)                |
| B — Peg     | 5     | Price shocks, LST peg deviation, oracle staleness     |
| C — Venue   | 5     | Bridge + API failures, protocol pauses, pool drainage |

## Category A — Funding regime (Family 2 only)

Family 1 (lending-only) skips Category A — no perp hedge means no funding exposure.

| Scenario ID             | Window                  | Regime summary                                           | Cells exercised                  | Success criteria                                                                                                |
| ----------------------- | ----------------------- | -------------------------------------------------------- | -------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `SCN-A1-NORMAL-2024`    | 2024-01-01 → 2024-12-31 | Positive funding median ~+12% APR; episodic +30% spikes  | All Family 2 cells               | Net APR > 0 on ≥80% of trading days; max consecutive drawdown < 8% per cell                                     |
| `SCN-A2-FLIP-NOV-2022`  | 2022-10-01 → 2022-12-31 | FTX collapse; ETH-perp funding flipped negative ~6 weeks | All Family 2 cells               | Adaptive-sizing trigger fires ≤7 days after 30d-avg < −5% APR; perp_short_size reduces ≥50%; max drawdown < 15% |
| `SCN-A3-FOMO-2024-Q1`   | 2024-01-01 → 2024-03-31 | Funding spiked +50-100% APR; ETH/BTC ETF approval flow   | Family 2 wstETH / weETH cells    | Strategy holds short; cumulative funding-capture > 8% APR over 90 days                                          |
| `SCN-A4-DEPEG-MAR-2023` | 2023-03-08 → 2023-03-15 | USDC depeg post-SVB; USDC traded 0.87–0.93 for ~48h      | All Family 2 USDC-margined cells | Margin auto-topup fires < 60s after deviation > 3%; no liquidation events                                       |

## Category B — Liquidation stress (both families)

Tests Phase 8 HealthFactorMonitor + LiquidationProximityCircuit + kill-switch wiring. Oracle-deviation features sourced
from `features-service` `chainlink_peg_deviation_calculator` (commit `01fb8d73`; per-block Chainlink deviation for
wstETH/ETH, cbETH/ETH, weETH/eETH). Each shock is replayed via Tenderly fork; swap leg P&L through slot 6
`PoolMatcher.quote()`.

| Scenario ID                    | Shock type                                            | Magnitude        | Cells exercised              | Success criteria                                                                                                                                       |
| ------------------------------ | ----------------------------------------------------- | ---------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SCN-B1-FLASH-CRASH-LST-DEPEG` | wstETH/ETH oracle drops 3% over 1 block (15s)         | 3% peg deviation | All wstETH / weETH cells     | HF ≥ 1.05; partial unwind fires at HF 1.10 (`HEALTH_FACTOR_CRITICAL`); position state matches HealthFactorMonitor prediction at ±0.5%                  |
| `SCN-B2-ETH-CRASH-15PCT-1D`    | ETH/USD drops 15% in 1 day (2024-04-13 magnitude)     | 15%              | All ETH-debt cells           | Kill-switch unwinds before liquidation (`LIQUIDATION_IMMINENT`); unwind P&L within 2% of analytical model                                              |
| `SCN-B3-WSTETH-PEG-EXTREME`    | wstETH/ETH oracle drops 8% (Lido validator slashing)  | 8% peg deviation | wstETH cells (Aave + Morpho) | Morpho LLTV 0.945 cell unwinds at HF 1.05; Aave 0.93 LTV cell maintains; recursive flash-unwind closes loop atomically                                 |
| `SCN-B4-CBETH-PEG-COINBASE`    | cbETH/ETH drops 5% (Coinbase custody-stress scenario) | 5% peg           | Base cbETH cells             | Cell auto-pauses; bridge-risk + counterparty-risk fire as separate alerts                                                                              |
| `SCN-B5-ORACLE-STALE-24H`      | Chainlink feed goes stale > 24h heartbeat (all feeds) | 24h staleness    | All cells                    | All cells halt opening new loops; existing positions held with `ORACLE_STALE_PAUSE` alert; `oracle_stale_flag_24h` feature = True triggers halt policy |

**Feature dependency for B1-B5**: `peg_deviation_bps`, `peg_deviation_flag_30bps`, `peg_deviation_flag_100bps`,
`peg_deviation_flag_300bps`, `oracle_staleness_seconds`, `oracle_stale_flag_24h` from `ChainlinkPegDeviationCalculator`
(`"chainlink_peg_deviation"`). MTDS source: `oracle_prices` parquet (instrument_id ∈ {`wstETH/ETH`, `cbETH/ETH`,
`weETH/eETH`}).

## Category C — Venue + bridge failure

Tests cross-venue coordination, USDC margin top-up automation, and pool-liquidity gating.

| Scenario ID                        | Failure type                                      | Cells exercised                 | Success criteria                                                                                                                    |
| ---------------------------------- | ------------------------------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `SCN-C1-HL-BRIDGE-HALT`            | Hyperliquid Arbitrum-bridge halt for 30 min       | All Family 2 HL cells           | Maintain existing perp position; route new opens to Bybit failover; 30-min unwind budget respected                                  |
| `SCN-C2-BYBIT-API-RATELIMIT`       | Bybit REST returns 429 for 5 min sustained        | All Family 2 Bybit cells        | Exponential backoff; `BybitCCXTAdapter` does NOT silently fail; positions maintained; alert fires at 60s of sustained 429           |
| `SCN-C3-AAVE-PAUSE-RESERVE`        | Aave V3 pauses one reserve (supply cap reached)   | Cells supplying that reserve    | Cell → `PAUSED_NEW_OPENS`; existing positions held; close/repay still works                                                         |
| `SCN-C4-UNISWAP-V3-POOL-DRAIN`     | Uniswap V3 wstETH/WETH pool drops to < $1M depth  | All wstETH cells using swap leg | Slippage gate triggers; cells abort new loops; existing positions unwind via fallback (Curve / Balancer per slot 6 aggregator path) |
| `SCN-C5-USDC-TOPUP-TREASURY-EMPTY` | Treasury USDC = 0 just as margin top-up is needed | All Family 2 cells              | Partial unwind fires (Family 1 + perp simultaneously) to release margin; no liquidation events                                      |

## Per-cell verdict taxonomy

Each scenario produces a per-cell verdict from this closed set:

| Verdict             | Definition                                                                                               |
| ------------------- | -------------------------------------------------------------------------------------------------------- |
| `PASS`              | Net APR within ±10% of analytical model + zero risk-rule violations + zero unwind anomalies              |
| `PASS_WITH_WARNING` | Net APR within ±20% OR minor risk-rule warning (HF dipped < 1.10 but recovered; no liquidation)          |
| `FAIL_ALPHA`        | Net APR < 50% of analytical prediction — cell un-economic in regime; flag for removal or scenario-skip   |
| `FAIL_RISK`         | HF < 1.05 OR liquidation fired OR cross-venue delta drift > 10% — cell un-safe; mandatory fix or removal |
| `INFRA_GAP`         | Scenario data missing — verdict pending; flag for `defi_catalogue` follow-up; blocks promotion           |

**Promotion gate**: cell reaches `live-ready` only when ALL Category B + C → `PASS` or `PASS_WITH_WARNING` AND ≥80% of
Category A → `PASS`.

## Backtest harness shape

```python
# strategy-service/tests/integration/test_recursive_borrow_scenarios.py
@pytest.mark.parametrize("cell_id", FAMILY_1_CELL_IDS + FAMILY_2_CELL_IDS)
@pytest.mark.parametrize("scenario", BACKTEST_SCENARIOS)
def test_cell_scenario(cell_id: str, scenario: BacktestScenario) -> None:
    cell = get_target_universe_spec(cell_id)
    result = run_backtest(
        cell=cell,
        scenario_window=scenario.window,
        oracle_overrides=scenario.oracle_overrides,
        funding_overrides=scenario.funding_overrides,
        venue_overrides=scenario.venue_overrides,
    )
    verdict = scenario.compute_verdict(result)
    assert verdict in {PASS, PASS_WITH_WARNING}, (cell_id, scenario.id, verdict, result)
```

Data envelope:

| Data type                                        | Source                 | Cadence   | Horizon needed                |
| ------------------------------------------------ | ---------------------- | --------- | ----------------------------- |
| `SUPPLY_APY` / `BORROW_APY` / `UTILISATION`      | MTDS lending-indices   | hourly    | 2022-03-01 → today            |
| `funding_rate` ETH-PERP (HL + Bybit)             | MTDS funding adapters  | 1h / 8h   | HL: 2023-06-29+; Bybit: 2018+ |
| `oracle_prices` Chainlink (wstETH, cbETH, weETH) | MTDS oracle adapters   | per-block | 2022-01-01 → today            |
| AMM pool snapshots (Uniswap V3 wstETH + cbETH)   | slot 6 golden fixtures | per-shape | scenario-specific JSON corpus |

## SSOT alignment caveats

- `BACKTEST_SCENARIOS` list is canonical in UAC `internal/architecture_v2/backtest_scenarios.py`. This doc is the
  human-readable SSOT; the Python file is the machine-readable twin. Keep in sync.
- Category B threshold values (30/100/300 bps; 24h staleness) mirror constants in
  `features_service/onchain/app/calculators/chainlink_peg_deviation_calculator.py` (`_THRESHOLD_30BPS`,
  `_THRESHOLD_300BPS`, `_STALE_THRESHOLD_SECONDS`). If thresholds change there, update this doc and the UAC dataclass
  accordingly.
- Scenario verdict logic lives in `BacktestScenario.compute_verdict()` (UAC). Per-cell success criteria above are the
  human spec that `compute_verdict` must implement.
- Tenderly fork fixtures for B1-B5 are BLOCKED-CREDENTIALS (see `pings/slot_2.md`). Unit tests in
  `test_recursive_borrow_scenarios.py` use mocked oracle overrides and pass; integration tests are marked
  `@pytest.mark.requires_credentials` and skip by default.

## Composes with

- `codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md` — staking archetype overview
- `codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md` — Family 1 spec
- `codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-perp-hedged.md` — Family 2 spec
- `codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` — per-cell collateral + LTV rules
- `plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` — the plan driving Phase 12 implementation
  (Phase 10+)
