## Scenario `defi_stablecoin_depeg` — Stablecoin de-peg (USDC / USDT / DAI / USDE)

| Field | Value |
|---|---|
| `scenario_id` | `defi_stablecoin_depeg` |
| Category | `PRICE_SHOCK` + `DATA_CORRUPTION` (de-peg invalidates derived value-at-peg features) |
| Layer | `RAW_TICK` (oracle peg-price ticks) + `FEATURE` (peg-deviation feature) + `EVENT` (governance pause if issuer-side) |
| Asset groups | `frozenset({MarketAssetGroup.DEFI})` (primary — DeFi LST yield + lending denominated in stables); `frozenset({MarketAssetGroup.CEFI})` (secondary — USDT-quoted perps risk pricing model break) |
| Applies-to | per-stablecoin (USDC / USDT / DAI / USDE / FRAX / GHO); per-chain (where the stable lives + bridges); per-protocol (Aave / Morpho / Marinade if stable used as collateral or denominator) |
| Targets archetype(s) | `carry_staked_basis` (PRIMARY — USDC borrow leg for deleverage; LST yield denominated in stable terms; if stable de-pegs the entire P&L numeraire is unstable); `ARBITRAGE_PRICE_DISPERSION` (SECONDARY — USDT-quoted perps need spot-USDT-USD adjustment) |

### Real-world referent

Stablecoin de-pegs happen at 1-2 year intervals, last weeks-to-months, and can cascade across protocols. Concrete incidents: 2023-03-11 USDC de-peg to $0.87 (SVB exposure, full recovery in 72h after Treasury intervention), 2022-05-09 UST collapse to $0.00 (algorithmic stablecoin death spiral, ~$60B destroyed), 2024-07 PYUSD de-peg to $0.93 during issuer redemption uncertainty, 2024-Q4 USDE volatility during Ethena yield-strategy unwinds. Mechanism: redemption fails or issuer pause → secondary-market sells exceed bid → peg breaks → lending protocols may freeze the stable as collateral → cascade.

### Trigger condition (synthetic injection)

At T+N seconds, oracle-published peg-price for selected stable drops from `$1.00` to `target_price` (operator: $0.95 = 5% de-peg moderate; $0.87 = 13% USDC-2023 reenactment; $0.50 = catastrophic). Sustained for D seconds (operator: 86400s = 24h moderate; 604800s = 7d catastrophic). Recovery curve: (a) `instant_recovery` (Treasury-intervention style: snaps back in 6-12h), (b) `linear_recovery_7d`, (c) `no_recovery` (UST-style death spiral). Optional sub-variant: `issuer_paused: bool` (synthetic on-chain `Paused()` event on the issuer's mint/redeem contract). DEX swap pools see asymmetric flow → AMM curves price the stable below oracle-published peg first → arbitrage routes hit the breaker on `slippage_budget_exceeded`.

### Observable signature

- Peg-deviation feature spikes from baseline <10bps to 500-5000bps depending on variant.
- Oracle ticks publish low peg-price; if oracle stales mid-event, composes with `defi_oracle_deviation_30sigma`.
- `MAX_DAILY_LOSS` rule fires on positions denominated in the affected stable.
- For `carry_staked_basis`: LST-yield numeraire becomes unstable → strategy P&L attribution feature spikes; deleverage path's USDC-borrow leg becomes structurally unfavorable.
- For `ARBITRAGE_PRICE_DISPERSION` on USDT-quoted perps: basis-curve feature gets noise from USDT-USD adjustment; existing positions need stable-denominator-correction.
- Aave / Morpho see deposits flee the stable; utilization spike → composes with `defi_liquidity_drain_lending_pool`.
- Alert events: `RISK_RULE_BLOCKED`, `KILL_SWITCH_ARMED` (if peg < threshold), multiple `CRITICAL` alerts; manual_unkill expected.

### Mutation spec (UAC `ScenarioMutationSpec`)

- Mutation type: `PriceShift` (peg-price drops) + optionally `EventDuplicate` for synthetic issuer-`Paused()` event
- Parameters: `stable_id: "USDC" | "USDT" | "DAI" | "USDE" | "FRAX" | "GHO"`, `peg_target_price: 0.95` (or 0.87 / 0.50 per variant), `duration_seconds: 86400`, `recovery_variant: "instant_recovery" | "linear_recovery_7d" | "no_recovery"`, `issuer_paused: bool = false`, `affected_chains: frozenset({"ethereum", "arbitrum", "optimism", "base", "solana"})` (per chain bridges of that stable), `affected_protocols: frozenset({"aave_v3", "morpho", "marinade"})` (any protocol using this stable as collateral or denominator)
- Pipeline tap layer: `RAW_TICK` (oracle peg-price feed) + `FEATURE` (downstream peg-deviation + P&L-in-stable features) + `EVENT` (issuer Paused)
- `available_at` discipline: peg-price ticks use real `available_at` (oracle heartbeat is real; we synthesize the VALUE not the timing). No lookahead bias. Issuer-Paused event uses real-block `available_at`.

### Magnitude curve + duration distribution

- **Magnitude**: -500bps (≈ -5%) moderate (USDC-2023 scale); -1300bps catastrophic (USDC-2023 trough); -5000bps + (UST-2022 / algo-stable death). 30σ on 30-day rolling peg-deviation distribution per stable.
- **Duration**: 6h (instant-recovery class) → 7 days (slow-recovery) → permanent (UST). Bimodal: most de-pegs resolve within 72h (90% of historical instances); 10% are structural (UST, BUSD wind-down).
- **Cross-stable correlation**: LOW (<0.2) — each stable has distinct issuer + collateral; idiosyncratic. EXCEPT during systemic events (2023-03 USDC drop dragged DAI down via 50%+ USDC backing). Scenario MUST support both isolated-stable (USDC only) and correlated-multi (USDC + DAI + FRAX).

### Expected outcomes (per archetype × per magnitude tier)

| Archetype | Magnitude | `RiskRuleConsequence` | Rule(s) fired | Breaker(s) tripped | `BreakerAction` | `KillSwitchId` armed | `AlertCode` fired | `expected_within` |
|---|---|---|---|---|---|---|---|---|
| `carry_staked_basis` | moderate (-500bps USDC) | SCALE_DOWN (reduce LST positions; pause new entries until peg recovers) | `MAX_CONCENTRATION` (stable exposure) + `MAX_DAILY_LOSS` | `carry_staked_basis_stable_depeg_moderate` (or **FOLLOW-UP**) | SCALE_DOWN; existing positions held | none initially | `RISK_RULE_SCALED_DOWN` + `CIRCUIT_BREAKER_TRIPPED` | 120s |
| `carry_staked_basis` | catastrophic (-1300bps+ OR no_recovery) | BLOCK + KILL on existing | `MAX_DRAWDOWN_BREACH` + `GLOBAL_DATA_STALENESS_HALT` (peg disagreement = stale numeraire) | `carry_staked_basis_stable_depeg_catastrophic` (or **FOLLOW-UP**) | KILL_ALL + FAST_UNWIND | `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` + `KILL_ALL_LIVE` (if multi-stable systemic) | `RISK_RULE_BLOCKED` + `KILL_SWITCH_ARMED` + multiple `CRITICAL` | 60s |
| `ARBITRAGE_PRICE_DISPERSION` (USDT-quoted perps) | moderate USDT de-peg | SCALE_DOWN (correct denominator + halve new positions until peg stable) | `MAX_POSITION_SIZE_PER_INSTRUMENT` (denominator-corrected) | `arbitrage_price_dispersion_denominator_depeg` (or **FOLLOW-UP**) | SCALE_DOWN | none | `RISK_RULE_SCALED_DOWN` | 120s |

### Auto-recovery contract

`recovery_mode=manual_unkill` for all catastrophic-tier outcomes (operator inspects Treasury / issuer announcements + verifies peg-recovery is structural before resume). `auto_cooldown` cooldown_seconds=7200 + guard="peg-deviation < 50bps for 86400s contiguous AND issuer not in `Paused` state" for moderate-tier kill-switches. Per `BREAKER_RECOVERY_DEFAULTS` SSOT at UAC@`a7a99b5`: KILL_ALL → manual_unkill; SCALE_DOWN → auto_cooldown — matches the tiered approach here.

### Cross-references / prior art

- UAC `BreakerConfig`: `registry/circuit_breakers/carry_staked_basis.py` — grep `stable_*` / `depeg_*` / `peg_*` (**FOLLOW-UP** for missing entries; likely 2+ tiers needed: moderate + catastrophic).
- UAC `RiskRule`: `MAX_CONCENTRATION` + `MAX_DAILY_LOSS` + `MAX_DRAWDOWN_BREACH` triggers (existing per UAC@`86851ab`).
- UAC `KillSwitch`: `KILL_PER_ARCHETYPE_*` + `KILL_ALL_LIVE` per UAC@`a7a99b5`.
- DR plan § Phase 1.B + recovery-mode SSOT.
- Risk plan § GlobalRules: `GLOBAL_DATA_STALENESS_HALT` (peg disagreement is data-staleness in spirit).
- `defi_catalogue_chain_primitives_2026_05_10.md` — chain × stable bridges + protocol-uses-of-stable matrix.
- `defi_recursive_borrow_archetypes_2026_05_10.md` — Family 1 / Family 2 USDC-borrow leg sensitivity.
- Historical: 2023-03-11 USDC, 2022-05-09 UST, 2024-07 PYUSD, 2024-Q4 USDE.
- **Composition note**: stablecoin de-peg frequently triggers BOTH `defi_liquidity_drain_lending_pool` (utilization spike on the affected stable's pool) AND `defi_oracle_deviation_30sigma` (oracle disagrees with AMM-derived peg). Phase 5 matrix SHOULD include composite scenario `defi_stablecoin_depeg + defi_liquidity_drain_lending_pool` exercising both — captured as Phase 4 follow-up if not in compressed scope.
