## Scenario `cross_asset_basis_blowout_perp_spot` — Perp-spot basis explosion

| Field | Value |
|---|---|
| `scenario_id` | `cross_asset_basis_blowout_perp_spot` |
| Category | `PRICE_SHOCK` + `CROSS_ASSET` (perp-spot divergence) |
| Layer | `RAW_TICK` (per-venue mid/last/funding) + `FEATURE` (basis-curve feature) |
| Asset groups | `frozenset({MarketAssetGroup.CEFI})` (primary); `frozenset({MarketAssetGroup.DEFI})` (cross-chain spot leg variant) |
| Applies-to | per-instrument-cluster (BTC perp vs BTC spot; ETH perp vs ETH spot; SOL perp vs SOL spot); per-venue-pair (perp-venue + spot-venue OR perp-venue + DEX) |
| Targets archetype(s) | `ARBITRAGE_PRICE_DISPERSION` (PRIMARY — basis IS the literal feature traded); `carry_staked_basis` (SECONDARY — LST-perp hedge basis is a sub-case) |

### Real-world referent

Basis blowout = perp trades materially above or below corresponding spot for sustained period, driven by directional flow imbalance or venue-idiosyncratic squeeze. Concrete incidents: 2021-01-04 Bitfinex BTC-PERP traded +8% over spot during Tesla/Bitcoin disclosure FOMO; 2022-06-15 stETH-ETH peg blowout (-7% during 3AC + Celsius unwind); 2024-03 ETH staking-yield-perp spreads widened 400bps in week pre-Shanghai upgrade; 2025-02 Hyperliquid memecoin perps trading 50%+ above DEX spot during launch frenzy. Mechanism: leveraged flow concentrated on one venue OR liquidity-providers withdrawing exposure during stress OR known catalyst priced via perps before spot adjusts. The trade is "sell rich perp, buy cheap spot, hold to convergence" — but if blowout persists or widens further, MTM loss before convergence can be severe.

### Trigger condition (synthetic injection)

At T+N seconds, perp mid-price diverges from spot mid-price by `basis_bps` (operator pick: 500bps = 5% absolute basis; baseline 5-20bps). Sustained for D seconds (operator: 7200s = 2h). Recovery curve: linear convergence over next 3600s OR step convergence when funding payment crystallizes. Three sub-variants: (a) `perp_above_spot` — long-bias, positive basis, funding goes positive; (b) `perp_below_spot` — short-bias, negative basis, funding goes negative; (c) `multi_venue_inconsistent` — basis blowout on 1 venue only, other 5 venues stay aligned (tests cross-venue dispersion alpha). Synthetic shift applied at FEATURE layer to one half of the basis pair while leaving the other half real.

### Observable signature

- Basis-curve feature spikes from baseline 5-20bps to 500bps within next tick.
- Implied funding-rate-forward feature jumps accordingly (funding auto-rebalances).
- Cross-venue dispersion feature spikes if `multi_venue_inconsistent` variant.
- `ARBITRAGE_PRICE_DISPERSION` signal generator emits LARGER size signal (the alpha source is precisely this dispersion) — operator MUST validate that risk limits cap this.
- Pre-flight check on the larger signal fires `MAX_POSITION_SIZE_PER_INSTRUMENT` `RiskRuleConsequence.SCALE_DOWN`.
- If basis goes wrong direction post-entry (widens more), MTM-loss feature spikes → `MAX_DRAWDOWN_BREACH` per `RiskRuleTrigger`.
- `RISK_RULE_SCALED_DOWN` alert; `CIRCUIT_BREAKER_TRIPPED` if drawdown breach.

### Mutation spec (UAC `ScenarioMutationSpec`)

- Mutation type: `PriceShift` on perp-leg-only (asymmetric mutation — preserves cross-asset signal) + `LatencyInject` for cross-venue propagation (basis blowouts often have 30s-5min cross-venue lag)
- Parameters: `instrument_cluster: "BTC" | "ETH" | "SOL" | "LST_CLUSTER"`, `basis_bps: 500`, `direction: "perp_above_spot" | "perp_below_spot" | "multi_venue_inconsistent"`, `duration_seconds: 7200`, `recovery_curve: "linear_3600s" | "step_at_funding"`, `affected_venues: frozenset({...})` (1 venue for variant c; all 6 for variants a/b)
- Pipeline tap layer: `FEATURE` (basis-curve feature, cleanest tap) + `RAW_TICK` (perp mid + last on specific venue for adapter-level testing)
- `available_at` discipline: synthetic basis shift stamps `available_at = real_event_time`; no shift; lookahead-bias check unaffected.

### Magnitude curve + duration distribution

- **Magnitude**: 500bps default (≈25σ on 30-day rolling per-cluster basis distribution); 200bps moderate; 1000bps catastrophic (stETH-ETH-2022-06 scale).
- **Duration**: ranges from 30min (intraday liquidity dislocation) to 3 weeks (3AC-collapse scale structural events); median 4h (one funding period); right-skewed.
- **Cross-venue correlation**: HIGH (>0.8) when basis blowout is asset-wide (BTC perp rich on all venues); LOW (<0.3) when venue-idiosyncratic (Hyperliquid memecoin basis distinct from Bybit basis). Scenario MUST support both.

### Expected outcomes (per archetype × per direction)

| Archetype | Direction | `RiskRuleConsequence` | Rule(s) fired | Breaker(s) tripped | `BreakerAction` | `KillSwitchId` armed | `AlertCode` fired | `expected_within` |
|---|---|---|---|---|---|---|---|---|
| `ARBITRAGE_PRICE_DISPERSION` | initial blowout (entry signal) | SCALE_DOWN (large signal → cap at max position size) | `MAX_POSITION_SIZE_PER_INSTRUMENT` + `MAX_LEVERAGE` | none initially | (none) | none | `RISK_RULE_SCALED_DOWN` | 30s |
| `ARBITRAGE_PRICE_DISPERSION` | basis widens post-entry (adverse move) | BLOCK + KILL on existing | `MAX_DRAWDOWN_BREACH` + `MAX_DAILY_LOSS` | `arbitrage_price_dispersion_basis_widening` (or **FOLLOW-UP**) | KILL_ALL (FAST_UNWIND on existing positions) | `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` | `RISK_RULE_BLOCKED` + `CIRCUIT_BREAKER_TRIPPED` + `KILL_SWITCH_ARMED` | 60s |
| `carry_staked_basis` | LST-perp basis blowout (stETH-ETH style) | BLOCK + KILL on existing | `MAX_DRAWDOWN_BREACH` + `LST_PEG_DEVIATION` | `carry_staked_basis_lst_peg_breach` (or **FOLLOW-UP**) | FAST_UNWIND | `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` | `RISK_RULE_BLOCKED` + `CIRCUIT_BREAKER_TRIPPED` | 60s |

### Auto-recovery contract

`recovery_mode=manual_unkill` for KILL_ALL-armed cases (operator inspects basis history + verifies recovery path before resume). `auto_cooldown` cooldown_seconds=1800 + guard="basis returned to within 50bps of baseline for 3600s contiguous AND drawdown recovered to within 25% of pre-blowout level" for moderate variants. Per `BREAKER_RECOVERY_DEFAULTS`: KILL_ALL → manual_unkill (matches UAC@`a7a99b5`).

### Cross-references / prior art

- UAC `BreakerConfig`: `registry/circuit_breakers/arbitrage_price_dispersion.py` — grep `basis_*` / `dispersion_*` (**FOLLOW-UP** if missing).
- UAC `RiskRule`: `registry/risk_rules/archetype.py` `MAX_DRAWDOWN_BREACH` + `MAX_POSITION_SIZE_PER_INSTRUMENT` (existing per Phase 2.A UAC@`86851ab`).
- UAC `KillSwitch`: `KILL_PER_ARCHETYPE_*` entries per UAC@`a7a99b5`.
- DR plan § Phase 1.B archetype seeds.
- Risk plan § ArchetypeRules.
- `defi_recursive_borrow_archetypes_2026_05_10.md` — LST-ETH basis as direct trade input for Family 1 archetype.
- Historical: 2021-01-04 Bitfinex BTC, 2022-06-15 stETH-ETH peg (3AC + Celsius), 2024-03 ETH staking-yield-perp, 2025-02 Hyperliquid memecoin perps.
