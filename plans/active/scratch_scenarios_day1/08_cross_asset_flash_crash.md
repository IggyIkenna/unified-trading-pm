## Scenario `cross_asset_flash_crash` — Flash crash (multi-venue cascade)

| Field                | Value                                                                                                                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario_id`        | `cross_asset_flash_crash`                                                                                                                                                             |
| Category             | `PRICE_SHOCK` + `CROSS_ASSET` (correlated multi-venue, multi-asset_group event)                                                                                                       |
| Layer                | `RAW_TICK` (mid-price + last-trade ticks) + `FEATURE` (derived volatility / VaR features) + `ORDER` (liquidation cascade event)                                                       |
| Asset groups         | `frozenset({MarketAssetGroup.CEFI, MarketAssetGroup.DEFI})`                                                                                                                           |
| Applies-to           | per-instrument (BTC + ETH primarily; SOL + LST cluster secondary); per-venue (top-N CeFi perp venues simultaneous); cross-chain DeFi spot legs (Uniswap V3 on Ethereum/Arbitrum/Base) |
| Targets archetype(s) | BOTH (`carry_staked_basis` — LST de-peg risk + Solana RPC stress; `ARBITRAGE_PRICE_DISPERSION` — basis blows out + funding-rate auto-rebalances)                                      |

### Real-world referent

Flash crashes are concentrated, short-duration (≤30min), large-magnitude (>10% nominal) drawdowns followed by partial
mean-reversion. Concrete incidents: 2020-03-12 BTC -50% in 2h (COVID-onset deleveraging cascade), 2022-11-08 FTX
disclosure (BTC -25% in 6h with cross-venue liquidation cascade), 2024-08-05 BTC-ETH -20% during JPY carry unwind
(US-equity vol spike correlated to crypto), 2024-12-19 ETH -15% during Plus-Token-style whale liquidation. Mechanism:
large directional flow on a single venue → other venues' arbitrage bots front-run the deviation → liquidation cascade as
leveraged longs hit margin calls → forced sells amplify the move → funding rate inverts → basis widens.

### Trigger condition (synthetic injection)

At T+N seconds, mid-price of selected instrument(s) drops `magnitude_bps` (operator pick: -1500bps = -15%) over
`duration_seconds` (180s = 3min). Cross-venue correlation: ALL 6 CeFi perp venues see the move within `propagation_ms`
(50-500ms; configurable to test exchange-arb-bot speed). DeFi spot legs lag by 30-180s (block-time discretization on
Ethereum mainnet). Funding rates auto-rebalance over next funding period. Trade-volume spike to 10× baseline; book-depth
drops to 30% baseline (liquidity withdrawal). Optional sub-variants: (a) `partial_recovery_50pct` — bounces back 50%
over next 1800s; (b) `no_recovery` — stays at low for full session; (c) `overshoot_then_revert` — drops 1500bps, bounces
300bps over-target, settles at -1200bps. The 30σ assertion is on 30-day rolling per-venue ATR.

### Observable signature

- Mid-price feature drops `magnitude_bps` synchronized across 6 CeFi venues within propagation window.
- Per-instrument realized-vol feature spikes (10× rolling 30-day baseline) within 1 minute.
- Book-imbalance feature swings to extreme (>0.8 in either direction).
- Open-interest / position-balance-monitor sees forced-liquidation flow on leveraged legs.
- `MAX_DRAWDOWN_BREACH` / `DAILY_LOSS_BREACH` rule fires per `RiskRuleTrigger` (per risk plan Phase 1.B + 2.A).
- `MAX_DRAWDOWN_BREACH` event → `KILL_ALL_LIVE` kill-switch arms (per UAC@`a7a99b5` `KillSwitchId` + DR plan Phase 1.C).
- DeFi spot Uniswap pool sees sell pressure; LP-quoted slippage spikes; Pyth feed publishes new low; lending-indices
  utilization may spike too (compose with `defi_liquidity_drain_lending_pool`).
- Alert events: multiple `CRITICAL` severity entries across `RISK_RULE_BLOCKED`, `MARKET_DATA_*`, `KILL_SWITCH_ARMED`,
  `CIRCUIT_BREAKER_TRIPPED`.

### Mutation spec (UAC `ScenarioMutationSpec`)

- Mutation type: `PriceShift` (primary) + `BookSpoof` (liquidity withdrawal — `book_depth_scale: 0.3`) + `LatencyInject`
  (DeFi spot lags CeFi by 30-180s)
- Parameters: `instruments: frozenset({"BTC-PERP", "ETH-PERP", "SOL-PERP"})`,
  `venues: frozenset({"bybit", "deribit", "binance", "okx", "hyperliquid", "aster"})`, `magnitude_bps: -1500`,
  `crash_duration_seconds: 180`, `cross_venue_propagation_ms_p95: 500`, `defi_spot_lag_seconds: 60`,
  `volume_multiplier: 10`, `book_depth_scale: 0.3`,
  `recovery_variant: "partial_50pct" | "no_recovery" | "overshoot_then_revert"`, `recovery_duration_seconds: 1800`.
- Pipeline tap layer: `RAW_TICK` (mid + last + book) + `FEATURE` (derived realized-vol / VaR) + `ORDER` (synthetic
  liquidation cascade events from execution-service matching engine adversarial mode).
- `available_at` discipline: synthetic ticks stamp `available_at = real_event_time` (no shift); preserves honest
  lookahead-bias semantics.

### Magnitude curve + duration distribution

- **Magnitude**: 30σ on 30-day rolling per-venue ATR. -1500bps default; -750bps moderate; -3000bps catastrophic
  (calibration variants).
- **Duration**: crash 60-300s (operator chooses); recovery 0-7200s depending on variant. Bimodal: most flash crashes
  (75% historical) revert >50% within 1h; 25% persist (FTX-style structural events).
- **Cross-venue correlation**: extremely high (>0.95) on CeFi perp venues during the crash window; HIGH (>0.7) on DeFi
  spot with 30-180s lag; MODERATE (0.4-0.6) on uncorrelated assets (e.g. equity/FX feeds during crypto-only crashes —
  tests asset-group isolation).

### Expected outcomes (per archetype)

| Archetype                    | `RiskRuleConsequence`                                                              | Rule(s) fired                                                                 | Breaker(s) tripped                                                                                                     | `BreakerAction`                                                                     | `KillSwitchId` armed                                                                            | `AlertCode` fired                                                     | `expected_within`     |
| ---------------------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------- |
| `ARBITRAGE_PRICE_DISPERSION` | BLOCK (basis math degenerate under panic; halt new entries)                        | `MAX_DRAWDOWN_BREACH` + `MAX_DAILY_LOSS` + `MAX_CONCENTRATION`                | `arbitrage_price_dispersion_drawdown_breach` + `arbitrage_price_dispersion_volatility_regime_shift` (or **FOLLOW-UP**) | KILL_ALL on `arbitrage_price_dispersion` archetype scope                            | `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` (and `KILL_ALL_LIVE` if multi-archetype breach) | `RISK_RULE_BLOCKED` + `CIRCUIT_BREAKER_TRIPPED` + `KILL_SWITCH_ARMED` | 30s after crash onset |
| `carry_staked_basis`         | BLOCK (LST de-peg risk + hedge-leg liquidation; halt entries + force partial exit) | `MAX_DRAWDOWN_BREACH` + `MAX_LEVERAGE` + `LST_PEG_DEVIATION` (if LST de-pegs) | `carry_staked_basis_drawdown_breach` + `carry_staked_basis_lst_peg_breach` (or **FOLLOW-UP**)                          | KILL_ALL on `carry_staked_basis` archetype scope; FAST_UNWIND on existing positions | `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` + `KILL_ALL_LIVE` (if global drawdown breach)           | `RISK_RULE_BLOCKED` + `CIRCUIT_BREAKER_TRIPPED` + `KILL_SWITCH_ARMED` | 30s                   |

### Auto-recovery contract

`recovery_mode=manual_unkill` for `KILL_ALL_LIVE` armed (operator must verify market state + portfolio P&L before
resume). Per `KillSwitch` UAC entry: KILL_ALL → manual_unkill (`BREAKER_RECOVERY_DEFAULTS` row). Per-archetype
kill-switches: `auto_cooldown` with cooldown_seconds=3600 + guard="realized-vol back within 2× of 30-day baseline for
1800s contiguous AND drawdown < 50% of pre-crash level". Composes with risk plan AlertCode
`KILL_SWITCH_MANUAL_UNKILLED` + `KILL_SWITCH_AUTO_RECOVERED` on resume.

### Cross-references / prior art

- UAC `BreakerConfig`: both archetype registries — grep `drawdown_*` / `volatility_*` / `lst_peg_*` (**FOLLOW-UP** for
  missing `volatility_regime_shift` + `lst_peg_breach`).
- UAC `KillSwitch`: `canonical/crosscutting/kill_switch.py` `KILL_ALL_LIVE` (primary) + per-archetype + per-asset_group
  entries.
- UAC `RiskRule`: `registry/risk_rules/archetype.py` `MAX_DRAWDOWN_BREACH` + `MAX_DAILY_LOSS` triggers (existing per
  UAC@`86851ab`).
- DR plan § Phase 1.B + Phase 1.E recovery rules.
- Risk plan § GlobalRules: `GLOBAL_PORTFOLIO_DRAWDOWN_HALT` (CRITICAL severity, KILL_ALL action).
- master_to_live_defi_2026_05_23.md Group F item 20 (circuit-breakers + kill-switches) — flash-crash IS the canonical
  test case.
- Historical: 2020-03-12 BTC, 2022-11-08 FTX, 2024-08-05 JPY-carry-unwind, 2024-12-19 ETH whale-liquidation.
