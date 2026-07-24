## Scenario `cefi_funding_spike_10x` — Perp funding-rate jump (CeFi)

| Field                | Value                                                                                                                                                                                               |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scenario_id`        | `cefi_funding_spike_10x`                                                                                                                                                                            |
| Category             | `PRICE_SHOCK` (funding rate IS a price the strategy pays/receives)                                                                                                                                  |
| Layer                | `RAW_TICK` (funding event from venue WS/REST) + `FEATURE` (funding-rate feature)                                                                                                                    |
| Asset groups         | `frozenset({MarketAssetGroup.CEFI})`                                                                                                                                                                |
| Applies-to           | per-venue (any of bybit / deribit / binance / okx / hyperliquid / aster); per-instrument (BTC-PERP / ETH-PERP / SOL-PERP primarily)                                                                 |
| Targets archetype(s) | `ARBITRAGE_PRICE_DISPERSION` (PRIMARY — funding-arb is the literal entry path; funding spike inverts the trade); `carry_staked_basis` (SECONDARY — hedge leg pays funding cost; spike erodes carry) |

### Real-world referent

Funding rates on perpetual swaps spike 10× during stress regimes. Concrete incidents: Bybit ETHUSDT 2024-04-12 (FTX
collapse aftermath) funding hit +0.375%/8h (annualized ~410% vs 10% baseline); Hyperliquid 2025-01 JLP funding storm
during memecoin volatility; Binance BTCUSDT 2022-11-08 (FTX wallet drain) funding spiked to -0.5%/8h. Mechanism: as perp
price diverges from spot (because either: panic flow on one side OR market-makers withdraw liquidity), funding rate
auto-rebalances to incentivize the opposite side. A 10× spike compresses the basis arbitrage profit to negative or
forces unwind.

### Trigger condition (synthetic injection)

At T+N seconds, venue's funding-rate tick spikes from baseline `0.01%/8h` (≈10% annualized) to `0.1%/8h` (≈110%
annualized) — 10× multiplier. Sustained for D seconds (operator pick: D=28800s = 8h = one full funding period). Recovery
curve: instant drop to baseline OR step-down over next funding period. Synthetic funding-rate row injected at FEATURE
layer (after RAW_TICK normalization in MTDS, before strategy consumption); applies to ONE `(venue, instrument)` pair per
scenario run (operator picks at runtime). Optionally compose with `cross_venue_staleness_perp_60s` for the bivariate
"spike + stale" worst case.

### Observable signature

- Funding-rate feature jumps 10× on selected `(venue, instrument)` pair within next-funding-tick boundary.
- `ARBITRAGE_PRICE_DISPERSION` basis-arb spread feature flips sign (was profitable long-perp, now expensive).
- Per-venue funding-cost-ceiling rule (per risk plan `FundingCostCeiling` `RiskRuleTrigger`) fires.
- Pre-flight check on any NEW funding-arb signal returns `BLOCK` consequence.
- Existing positions get `SCALE_DOWN` instruction proportional to spike magnitude (per pre-flight aggregation).
- `RISK_RULE_BLOCKED` / `RISK_RULE_SCALED_DOWN` alert events emitted with `synthetic=true` provenance.
- Position-balance-monitor shows pending-resize action; execution-service receives resize-down child order.

### Mutation spec (UAC `ScenarioMutationSpec`)

- Mutation type: `PriceShift` (existing closed-union member per Phase 1.B; funding rate is semantically a price)
- Parameters: `venue: "bybit" | "binance" | "okx" | "deribit" | "hyperliquid" | "aster"`,
  `instrument: "BTCUSDT" | "ETHUSDT" | ...`, `data_type: "funding_rate"`, `target_value_bps: 100` (= 0.1%/8h),
  `baseline_bps: 10`, `duration_seconds: 28800`, `recovery_curve: "step" | "linear_28800s"`.
- Pipeline tap layer: `FEATURE` (preferred — clean injection point after RAW_TICK normalization); secondary `RAW_TICK`
  for adapter-level testing.
- `available_at` discipline: synthetic funding-rate row stamps `available_at = funding_event_time` (the venue's
  funding-tick boundary). No `available_at` shift; downstream lookahead-bias check unaffected.

### Magnitude curve + duration distribution (price-shock-specific)

- **Magnitude**: 10× multiplier (operator-configurable 5× / 10× / 20× / 50× as sub-scenarios). 30σ-equivalent on 30-day
  rolling funding-rate distribution per venue.
- **Duration**: 1 funding period (8h Bybit/Binance; 1h Hyperliquid; 4h Aster) → 7 funding periods (≈2 days) max.
  Bimodal: most spikes resolve within 2 periods; 5% persist >5 periods.
- **Cross-venue correlation**: high (>0.7) for top-5 venues during BTC/ETH stress (FTX-style events); LOW (<0.2) for
  venue-idiosyncratic events (Hyperliquid memecoin storms don't affect Bybit). Scenario MUST support both
  correlated-spike (all 6 venues) and isolated-spike (1 venue) sub-cases.

### Expected outcomes (per archetype)

| Archetype                        | `RiskRuleConsequence`                                                  | Rule(s) fired (cite `RiskRuleId`)                                                           | Breaker(s) tripped                                                              | `BreakerAction`                 | `KillSwitchId` armed           | `AlertCode` fired                             | `expected_within`      |
| -------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------- | ------------------------------ | --------------------------------------------- | ---------------------- |
| `ARBITRAGE_PRICE_DISPERSION`     | BLOCK on new entries; SCALE_DOWN on existing                           | `FUNDING_COST_CEILING_ARBITRAGE_PRICE_DISPERSION` (from `registry/risk_rules/archetype.py`) | `arbitrage_price_dispersion_funding_cost_blowout` (or **FOLLOW-UP** if missing) | BLOCK_NEW + SCALE_DOWN existing | none (operational, not safety) | `RISK_RULE_BLOCKED` + `RISK_RULE_SCALED_DOWN` | 60s after funding tick |
| `carry_staked_basis` (hedge leg) | SCALE_DOWN (hedge cost erodes carry margin; reduce or pause rebalance) | per-archetype `FundingCostCeiling` rule                                                     | `carry_staked_basis_hedge_funding_cost` (or **FOLLOW-UP**)                      | SCALE_DOWN                      | none                           | `RISK_RULE_SCALED_DOWN`                       | 60s                    |

### Auto-recovery contract (per DR plan `BreakerRecoveryRule`)

`recovery_mode=auto_cooldown`; `cooldown_seconds=480` (1 funding period); `retry_policy=linear`;
`guard_description="funding rate < baseline * 3 for one full funding period contiguous"`. Manual-unkill required if
breaker re-fires >3 times within 24h (operator triage). Per `BREAKER_RECOVERY_DEFAULTS` SSOT at UAC@`a7a99b5`:
SCALE_DOWN action default is auto_cooldown — matches funding-spike operational character.

### Cross-references / prior art

- UAC `BreakerConfig`: `registry/circuit_breakers/arbitrage_price_dispersion.py` — grep `funding_cost_*` / `basis_*`
  breakers (**FOLLOW-UP** if missing).
- UAC `RiskRule`: `registry/risk_rules/archetype.py` `FundingCostCeiling` trigger (existing per risk plan Phase 2.A —
  UAC@`86851ab`).
- DR plan § Phase 1.B `BreakerConfig` seed for `arbitrage_price_dispersion`.
- Risk plan § ArchetypeRules: per-archetype funding-cost ceiling.
- `unified-trading-pm/plans/archive/2026_07/master_to_live_defi_2026_05_23.md` — `ARBITRAGE_PRICE_DISPERSION` is the
  funding-arb archetype rename per Stream B canonicalisation 2026-05-07.
- Historical: Bybit ETHUSDT 2024-04-12, Hyperliquid 2025-01, Binance BTCUSDT 2022-11-08.
