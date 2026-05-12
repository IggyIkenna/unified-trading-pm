---
title: "Strategy archetype taxonomy — share-class-driven neutrality + recursive carry rename + cross-domain extensions + vol surface infra + doc completion"
created: 2026-05-12
author: ikenna-main-slot1
source:
  - codex/09-strategy/strategy-summary.md
  - codex/09-strategy/architecture-v2/archetypes/*
  - unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py (StrategyArchetype enum + ARCHETYPE_TO_FAMILY dict)
  - plans/active/master_to_live_defi_2026_05_23.md:224
  - plans/active/defi_recursive_borrow_archetypes_2026_05_10.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# Strategy archetype taxonomy refinement

> **Severity**: P0 — pre-May-23-cutover taxonomy clean-up. Operator-supplied design call 2026-05-12 covering 8 distinct corrections + a central "share-class determines market neutrality" axiom.
> **Suggested owner**: split — slot 2 (UAC enum + catalogue), slot 5 (recursive carry engine refactor), slot 6 (vol surface infra + Vol Trading doc completion), slot 8 (codex doc completion + workspace-grep for count drift).

## Foundational axiom (operator 2026-05-12)

**Share class determines what market-neutral means.** Every carry/yield strategy is market-neutral *to its share class*, not USD-neutral by default:
- USD* share class → USD-neutral (existing "delta-neutral" framing assumes this implicitly).
- ETH share class → ETH-neutral.
- SOL share class → SOL-neutral.
- Future expansion (BTC / native-PoS chains with LST infra) → per-class-neutral.

Implication: a strategy that's "ETH-neutral" (e.g. `CARRY_RECURSIVE_STAKED` on ETH share class) is **not** USD-neutral — it has full ETH/USD exposure as a deliberate, structural choice of the share class. Adding a USD-neutralising perp hedge would *break* the share-class definition.

**Arbitrage archetypes are always USD* share class** — by construction. Cross-venue dispersion captures USD-denominated edge.

## Corrections per archetype

### 1. CARRY_STAKED_BASIS — leg description fix

**Current codex** (`carry-staked-basis.md` + summary): "3-leg: stake native → LST → **pledge LST on lending protocol → borrow base** → short perp".

**Reality per operator**: "no need to borrow base — buy ETH (or stake-token), stake it, get LST, use as collateral on **perp venue directly**, short perp".

**Updated description**:
- USD* share class only (strictly USD-neutral hence the perp hedge).
- 3-leg shape: **buy stake-token → stake → use LST as perp-venue collateral → short perp**.
- NO lending protocol borrow leg.
- Token-agnostic: works for any (stake-token, LST) pair where the LST is recognised collateral on ≥1 of the 6 perp venues (Binance / Bybit / OKX / Hyperliquid / Aster / Deribit).
- Today: ETH (Lido/Rocket Pool/Etherfi LSTs), SOL (Jito/Marinade LSTs). Expansion: any PoS token with LST + perp-venue collateral acceptance.

### 2. CARRY_STAKED_BASIS_DATED — NEW archetype

Same shape as `CARRY_STAKED_BASIS` but **short leg = dated future instead of perp**:
- Buy stake-token → stake → LST collateral → **short dated future** (needs roll at expiry).
- Venue constraint: OKX or Bybit dated futures (operator unsure about Deribit; needs verification — Deribit has dated futures but check LST collateral acceptance).
- Carry expression: staking yield + (futures premium / time-to-expiry) − roll costs.
- Same share-class & token-axis as `CARRY_STAKED_BASIS`.

### 3. CARRY_RECURSIVE_STAKED — refinement

**Per share class**:
- **ETH/SOL share class**: stake → LST → collateral → borrow same underlying (ETH/SOL) → stake again → loop. Target leverage = f(max acceptable LST↔native spread drawdown). Already market-neutral to share class; **no perp hedge** needed (operator: "never").
- **USD* share class** (canonical "recursive borrow lending only with staking"): fraction of USDT on Aave (config) as collateral → borrow ETH → stake → LST → re-borrow → loop. Market-neutral in USD* because borrow + lend on same underlying-token-family. No perp hedge.

**Execution axes**:
- Sequential loop OR flash-loan axis (single-tx unwind via Aave flash loan).
- Both are valid configurations of the same engine.

### 4. CARRY_RECURSIVE_BORROW_LENDING_ONLY — distinction

- **Pure** borrow-lending arb (no staking leg).
- Lending & borrowing the **same underlying token cross-venue** (or token family, *excluding* LST/LRT tokens whose yield offsets the borrow-lending arb).
- Market-neutral by construction (USD* + any single-token share class).
- Sequential OR flash-loan axis (same as `CARRY_RECURSIVE_STAKED`).

**Difference from `CARRY_RECURSIVE_STAKED`**: the latter adds a staking leg, generating the additional `staking-yield - lending-rate` edge; the former is pure cross-venue rate spread.

### 5. CARRY_RECURSIVE_BORROW_PERP_HEDGED → RENAME

**Rename rationale**: it's not actually *recursive*. It's a single-pass perp-hedged carry trade that kicks in when funding rates flip negative.

**Proposed new name**: `CARRY_BORROW_PERP_HEDGED` (drop "RECURSIVE").

**Plus new variant**: `CARRY_BORROW_PERP_HEDGED_DATED` for the dated-futures equivalent (term-structure flip case).

**Alternative naming** (operator-proposed) emphasising the inversion-of-basis intuition:
- `CARRY_BASIS_PERP_INV` (was `CARRY_BORROW_PERP_HEDGED`) — inverse of `CARRY_BASIS_PERP`.
- `CARRY_BASIS_DATED_INV` (was `CARRY_BORROW_PERP_HEDGED_DATED`) — inverse of `CARRY_BASIS_DATED`.

**Recommended**: pick the `_INV` naming because it makes the structural symmetry obvious (these ARE inverse basis trades, not different families of trade).

**Mechanics** (negative-funding regime):
- USD* share class collateral → lend on Aave (or perp venue if rates available) → borrow ETH → sell ETH to short → long perp the same notional.
- P&L = lending rate + perp funding (positive for long when funding negative) − ETH borrow rate.
- Trading-wallet ratio: ~50% perp-collateral / ~50% ETH-borrow (configurable).
- Works for SOL or any token with perp + funding data.
- Future enhancement: if perp venues offer coin borrow + rate + availability data, factor those into routing (historical fetching needed).

### 6. Centralized carry engine — architecture principle

**Operator directive**: "logic should be done in centralised abstractable way that fits structure rather than a series of bolt ons as lots of params and decision making are the same anyway".

**Implied refactor**:
- ONE carry strategy engine.
- Axes determining the variant:
  - **share-class** (USD* / ETH / SOL / future)
  - **staking-leg** (on / off)
  - **hedge-leg** (off / perp / dated-future)
  - **recursion** (none / sequential / flash-loan)
  - **direction** (direct / inverse — for negative-funding regime)
- Each `CARRY_*` archetype = a named configuration of this engine.
- Eliminates 8+ near-duplicate code paths.

**Implementation impact**: `strategy-service` carry handlers consolidate to one `CarryFamilyEngine` with axis-driven dispatchers (similar to writegate slice (c) `_publish_emission_check` generalised dispatcher).

### 7. ARBITRAGE_PRICE_DISPERSION — sub-variants

**ARBITRAGE_PRICE_DISPERSION universe** (axes / configs, not separate archetypes):
- **Cross-CEX same-instrument** (spot/perp/dated on Binance vs OKX vs Bybit etc).
- **Cross-DEX same-instrument** (Uniswap V3 ETH/USDC vs SushiSwap vs Aerodrome).
- **CEX-vs-DEX same-instrument** (Binance ETH/USDC vs Uniswap V3).
- **Cross-expiry** (dated futures on different venues, **same expiry day** — must align).
- **Spot vs dated vs perp basis dispersion** (where the basis converges differently across instrument types).
- **Funding-rate dispersion** (same instrument different perp venues).
- **Sports cross-book** (Betfair vs Smarkets vs Pinnacle).
- **Within-venue no-arb violations** (butterfly / calendar / put-call parity — option-pricing constraints).
- **Pure option vol arb** ← **NEW HOMEWORK ASSIGNED 2026-05-12**: cross-venue same-strike-same-term option price dispersion. *Not* a Vol Trading archetype (no vol-edge view); it's price-dispersion arb in the Arbitrage family.

All ARBITRAGE_PRICE_DISPERSION variants = **USD* share class** by construction.

### 8. ARBITRAGE_CROSS_DOMAIN_EVENT — universe expansion

**Cross-domain event arb universe** (expiry-aligned events priced across multiple venue domains):
- Sports book vs Polymarket (e.g. "Lakers beat Celtics" on Pinnacle + Polymarket).
- Sports book vs Kalshi (event-binary on Kalshi).
- Sports book vs Opinion.trade.
- Polymarket vs Kalshi vs Opinion.trade (3-way prediction-CLOB dispersion).
- **CME binary options** (event-aligned binaries with same expiry — e.g. CPI-print binaries) added to the cross-domain universe.

**Definition**: same real-world event listed in ≥2 venue domains (sports book / prediction CLOB / CME binary) where expiries align → arb across them.

When the same real-world event appears in ONE domain only (e.g. Polymarket alone) but at multiple price-quote venues, it falls under `ARBITRAGE_PRICE_DISPERSION` (cross-book within domain). Cross-domain = cross-venue-type, not cross-venue-instance.

### 9. MARKET_MAKING_EVENT_SETTLED — RETAIN, not legacy

**Operator pushback**: "why we removing MARKET_MAKING_EVENT_SETTLED and how are we market making betfair for example then where does this fall".

**Resolution**: KEEP `MARKET_MAKING_EVENT_SETTLED` as a first-class archetype (drop "legacy" label). It's the canonical home for:
- Sports exchange back/lay MM: Betfair / Smarkets / Matchbook / Betdaq.
- (Polymarket goes to `MARKET_MAKING_PREDICTION` per Phase 9 split, but `MARKET_MAKING_EVENT_SETTLED` is the bookmaker-style umbrella).

**Splitting rule**:
- Sports exchange (back/lay model) → `MARKET_MAKING_EVENT_SETTLED`.
- Prediction CLOB (binary YES/NO outcome via order book) → `MARKET_MAKING_PREDICTION`.

**Per-archetype doc completion**: write `market-making-event-settled.md` covering Betfair/Smarkets/etc. back/lay quoting mechanics, vig-free pricing, settlement integration.

### 10. MARKET_MAKING_CONTINUOUS — split into granular variants, drop legacy

Per the Phase 9 expansion: legacy `MARKET_MAKING_CONTINUOUS` covers too much. Once the granular variants (`MARKET_MAKING_PASSIVE_SPREAD` / `_INVENTORY_SKEW` / `_ML_LEAN` / `_QUEUE_MICROSTRUCTURE`) are doc-complete, deprecate the legacy.

**Completion criterion**: ALL 4 granular variants doc-complete + tested + at least one live config per variant → safe to deprecate `MARKET_MAKING_CONTINUOUS`. Until then, keep both.

### 11. Vol Trading — surface infra + doc completion

**Operator-requested infra** (pre-May-23):
- SVI / SSVI options surface fitter (per-venue per-asset).
- Normalised strike + term slices (constant-moneyness, constant-tenor) for ML continuity.
- ML predictions on fixed normalised strikes/terms → convert to closest real strikes at trade time.
- "Lots of existing stuff around" — verify what's shipped vs needs build (slot 6 audit).

**Doc completion** for all 19 Vol Trading archetypes:
- `VOL_TRADING_OPTIONS` (legacy — covered)
- `VOL_ARB_RV_IV` / `VOL_SPREAD_STRUCTURES` / `VOL_CARRY` / `VOL_OVERLAY_COVERED_CALLS` / `VOL_OVERLAY_PROTECTIVE_PUT` / `VOL_STRADDLE` / `VOL_SYNTHETIC_DELTA` / `VOL_MARKET_MAKING` / `VOL_ML_LEAN` / `VOL_0DTE_GAMMA_SCALPING` / `VOL_0DTE_PIN_RISK` / `VOL_TERM_STRUCTURE_ARB` / `VOL_TERM_STRUCTURE_SLOPE` / `VOL_DISPERSION` / `VOL_VARIANCE_SWAP` / `VOL_LEAPS_CONVEXITY` / `VOL_CROSS_ASSET_SPREAD` / `VOL_RATIO_SPREAD`

**Pure option vol arb** (cross-venue same-strike same-term price-dispersion) → `ARBITRAGE_PRICE_DISPERSION` (NOT a Vol Trading archetype; price-dispersion arb).

### 12. Portfolio — doc completion

All 4 Portfolio archetypes are doc-pending: `PORTFOLIO_MULTI_STRATEGY` / `PORTFOLIO_RISK_PARITY` / `PORTFOLIO_FACTOR_ALLOCATION` / `PORTFOLIO_TACTICAL_OVERLAY`. Complete pre-May-23.

### 13. Code/config wiring — share-class × archetype × venue universe matrix

**Per-archetype capability matrix** must be hooked up:
- **Share class compatibility**: which share classes can run which archetype? (e.g. `ARBITRAGE_*` always USD*; `CARRY_STAKED_BASIS` USD*-only; `CARRY_RECURSIVE_STAKED` USD*/ETH/SOL).
- **Treasury management**: per-share-class deposit/withdraw routing per archetype's venue set (composes with venue × deposit-chain × custody matrix issue doc shipped earlier today).
- **Venue universe filter**: vol archetypes don't execute on spot-only venues; perp archetypes don't execute on spot-only venues; arbitrage archetypes need ≥2 venues for the spread; etc.
- **Strategy registry update**: `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` + `ARCHETYPE_TO_FAMILY` dict + per-archetype `topology_requirements` + `share_class_compatibility` + `venue_universe`.

## Counts after refinement

Current section enumeration in strategy-summary.md = **55**. After refinement:

| Family | Count | Δ from current |
|---|---|---|
| ML Directional | 2 | 0 |
| Rules Directional | 2 | 0 |
| Carry & Yield | **8 → 9** (add `CARRY_STAKED_BASIS_DATED`) | +1 |
| Arbitrage / Structural | 7 | 0 (no archetype count change; sub-variants are configs/axes) |
| Market Making | 10 → **9** (after legacy deprecation post-completion) | -1 (eventually) |
| Event-Driven | 1 | 0 |
| Vol Trading | **19 → 18** (after `VOL_TRADING_OPTIONS` legacy deprecation post-completion) | -1 (eventually) |
| Stat Arb / Pairs | 2 | 0 |
| Portfolio | 4 | 0 |

**Pre-deprecation total**: 56 (current 55 + new `CARRY_STAKED_BASIS_DATED`).
**Post-deprecation target**: 54 (drop 2 legacy archetypes after granular variants doc-complete).
**+rename**: `CARRY_RECURSIVE_BORROW_PERP_HEDGED` → `CARRY_BASIS_PERP_INV`; add `CARRY_BASIS_DATED_INV` (was already in the +1).

**Operator decision needed**:
- (a) `CARRY_BORROW_PERP_HEDGED` / `CARRY_BORROW_PERP_HEDGED_DATED` (descriptive)
- (b) `CARRY_BASIS_PERP_INV` / `CARRY_BASIS_DATED_INV` (inverse-of-basis intuition) **[my recommendation]**

## Routing (per-slot)

**Slot 2** (defi_catalogue + cross_asset_audit owner):
- UAC `StrategyArchetype` enum updates: rename + add `CARRY_STAKED_BASIS_DATED` + `CARRY_BASIS_PERP_INV` + `CARRY_BASIS_DATED_INV` (pending operator naming choice).
- `ARCHETYPE_TO_FAMILY` dict updates.
- Per-archetype `share_class_compatibility` + `venue_universe` + `topology_requirements` matrix wire-up.
- Cross-asset catalogue audit dimension: extend with share-class × archetype × venue capability matrix.

**Slot 5** (defi_recursive_borrow owner + carry refactor):
- Centralized `CarryFamilyEngine` design + impl. Replaces 8+ near-duplicate handlers.
- Axes: share-class / staking-leg / hedge-leg / recursion / direction / sequential-vs-flashloan.
- Validate against existing `defi_recursive_borrow_archetypes_2026_05_10.md` Phases 1-2 design batch.

**Slot 6** (defi_simulation_realism + vol surface):
- SVI/SSVI options surface fitter audit (what's shipped vs needs build).
- Normalised strike + term slicing infra (`vol/surface/normalised_grid.py`?).
- Vol Trading 18 per-archetype docs (slot 6 has Phase 2C-H pool-class connector implementation absorbed from Harsh slot 4 — extend with Vol Trading docs).

**Slot 8** (codex_vs_citadel + cross_cutting #4):
- Update `codex/09-strategy/strategy-summary.md`: corrections per items 1-13 above; corrected counts.
- Per-archetype doc completion: 4 Portfolio + 18 Vol + `market-making-event-settled.md` (drop legacy) + new `carry-staked-basis-dated.md` + new `carry-basis-perp-inv.md` + new `carry-basis-dated-inv.md`.
- Workspace-grep + reconcile `(8 families / 18 archetypes)` / `(9 families / 53 archetypes)` / `(9 families / 55 archetypes)` count drift across all plans + master plan + CLAUDE.md (likely 10+ locations).
- Update `codex/09-strategy/strategy-summary.md` § 18 line (Phase 9 expansion sub-count drift).

**Slot 1 (main)**:
- Master plan `:224` re-update post slot-2/5/6/8 ships.
- Surface naming decision (a)/(b) for operator (this commit's AskUserQuestion).
- Surface Deribit-LST-collateral verification ask (slot 2 or slot 4 verification — for `CARRY_STAKED_BASIS_DATED` Deribit eligibility).

## Operator decisions needed (surface inline)

1. **Naming** for the perp-hedged carry trade — option (a) `CARRY_BORROW_PERP_HEDGED` (descriptive) vs option (b) `CARRY_BASIS_PERP_INV` (inverse-of-basis intuition).
2. **Deribit LST collateral acceptance** — verify whether Deribit accepts ETH LSTs as collateral for dated futures (affects `CARRY_STAKED_BASIS_DATED` venue list).
3. **Centralized carry engine** — confirm refactor approach: ONE engine + axis-driven config (recommended) vs N separate handler-per-archetype (current).
4. **Legacy deprecation timing** — `MARKET_MAKING_CONTINUOUS` + `VOL_TRADING_OPTIONS` removed only after granular variants all doc-complete + 1 live config each. May-23 = both still in registry. Confirm: post-cutover deprecation OK?

## Composes with

- `codex/09-strategy/strategy-summary.md` (canonical archetype list)
- `unified-api-contracts/.../internal/architecture_v2/enums.py` (UAC enum)
- `plans/active/defi_recursive_borrow_archetypes_2026_05_10.md` (slot 5 Phases 1-2 design + new Family 1/2 archetypes)
- `plans/active/master_to_live_defi_2026_05_23.md:224` (master plan strategy archetypes row)
- `plans/active/issues/venue_chain_custody_routing_matrix_2026_05_12.md` (share-class × venue compatibility matrix overlap)
- `cursor-configs/CLAUDE.md` (any archetype-count references)
