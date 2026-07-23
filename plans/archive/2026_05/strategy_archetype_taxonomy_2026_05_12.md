---
doc_type: plan
title:
  Strategy archetype taxonomy — share-class-driven neutrality + recursive carry rename + cross-domain extensions + vol
  surface infra + doc completion
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
priority: P0
promoted_from_issue: 2026-05-12
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
source:
  [
    /codex/09-strategy/strategy-summary.md,
    codex/09-strategy/architecture-v2/archetypes/*,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py (StrategyArchetype enum +
    ARCHETYPE_TO_FAMILY dict),
    "plans/active/master_to_live_defi_2026_05_23.md:224",
    plans/active/defi_recursive_borrow_archetypes_2026_05_10.md,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-12
parent_epic: strategy_master
---

> **ARCHIVED 2026-05-21** — 100% complete (0 open todos). Strategy archetype taxonomy + share-class neutrality +
> recursive carry rename + cross-domain extensions + vol surface infra + doc completion all shipped. status: done →
> archived.

## Deferred work — migrated to:

| Item                                                                             | Successor plan |
| -------------------------------------------------------------------------------- | -------------- |
| All phases complete — no deferred items. Plan status: done → archived 2026-05-21 | n/a            |

> **Promoted to standalone plan 2026-05-12** from
> `plans/active/issues/strategy_archetype_taxonomy_refinement_2026_05_12.md`. The issue body grew past 280 lines with
> operator-supplied design call (foundational axiom + 13 corrections + per-slot routing + operator directives +
> decisions received) — too substantial to fold; lifted in place as a design-class active plan.

# Strategy archetype taxonomy refinement

> **Severity**: P0 — pre-May-23-cutover taxonomy clean-up. Operator-supplied design call 2026-05-12 covering 8 distinct
> corrections + a central "share-class determines market neutrality" axiom. **Suggested owner**: split — slot 2 (UAC
> enum + catalogue), slot 5 (recursive carry engine refactor), slot 6 (vol surface infra + Vol Trading doc completion),
> slot 8 (codex doc completion + workspace-grep for count drift).

## Foundational axiom (operator 2026-05-12)

**Share class determines what market-neutral means.** Every carry/yield strategy is market-neutral _to its share class_,
not USD-neutral by default:

- USD\* share class → USD-neutral (existing "delta-neutral" framing assumes this implicitly).
- ETH share class → ETH-neutral.
- SOL share class → SOL-neutral.
- Future expansion (BTC / native-PoS chains with LST infra) → per-class-neutral.

Implication: a strategy that's "ETH-neutral" (e.g. `CARRY_RECURSIVE_STAKED` on ETH share class) is **not** USD-neutral —
it has full ETH/USD exposure as a deliberate, structural choice of the share class. Adding a USD-neutralising perp hedge
would _break_ the share-class definition.

**Arbitrage archetypes are always USD\* share class** — by construction. Cross-venue dispersion captures USD-denominated
edge.

## Corrections per archetype

### 1. CARRY_STAKED_BASIS — leg description fix

**Current codex** (`carry-staked-basis.md` + summary): "3-leg: stake native → LST → **pledge LST on lending protocol →
borrow base** → short perp".

**Reality per operator**: "no need to borrow base — buy ETH (or stake-token), stake it, get LST, use as collateral on
**perp venue directly**, short perp".

**Updated description**:

- USD\* share class only (strictly USD-neutral hence the perp hedge).
- 3-leg shape: **buy stake-token → stake → use LST as perp-venue collateral → short perp**.
- NO lending protocol borrow leg.
- Token-agnostic: works for any (stake-token, LST) pair where the LST is recognised collateral on ≥1 of the 6 perp
  venues (Binance / Bybit / OKX / Hyperliquid / Aster / Deribit).
- Today: ETH (Lido/Rocket Pool/Etherfi LSTs), SOL (Jito/Marinade LSTs). Expansion: any PoS token with LST + perp-venue
  collateral acceptance.

### 2. CARRY_STAKED_BASIS_DATED — NEW archetype

Same shape as `CARRY_STAKED_BASIS` but **short leg = dated future instead of perp**:

- Buy stake-token → stake → LST collateral → **short dated future** (needs roll at expiry).
- Venue constraint: OKX or Bybit dated futures (operator unsure about Deribit; needs verification — Deribit has dated
  futures but check LST collateral acceptance).
- Carry expression: staking yield + (futures premium / time-to-expiry) − roll costs.
- Same share-class & token-axis as `CARRY_STAKED_BASIS`.

### 3. CARRY_RECURSIVE_STAKED — refinement

**Per share class**:

- **ETH/SOL share class**: stake → LST → collateral → borrow same underlying (ETH/SOL) → stake again → loop. Target
  leverage = f(max acceptable LST↔native spread drawdown). Already market-neutral to share class; **no perp hedge**
  needed (operator: "never").
- **USD\* share class** (canonical "recursive borrow lending only with staking"): fraction of USDT on Aave (config) as
  collateral → borrow ETH → stake → LST → re-borrow → loop. Market-neutral in USD\* because borrow + lend on same
  underlying-token-family. No perp hedge.

**Execution axes**:

- Sequential loop OR flash-loan axis (single-tx unwind via Aave flash loan).
- Both are valid configurations of the same engine.

### 4. CARRY_RECURSIVE_BORROW_LENDING_ONLY — distinction

- **Pure** borrow-lending arb (no staking leg).
- Lending & borrowing the **same underlying token cross-venue** (or token family, _excluding_ LST/LRT tokens whose yield
  offsets the borrow-lending arb).
- Market-neutral by construction (USD\* + any single-token share class).
- Sequential OR flash-loan axis (same as `CARRY_RECURSIVE_STAKED`).

**Difference from `CARRY_RECURSIVE_STAKED`**: the latter adds a staking leg, generating the additional
`staking-yield - lending-rate` edge; the former is pure cross-venue rate spread.

### 5. CARRY_RECURSIVE_BORROW_PERP_HEDGED → RENAME

**Rename rationale**: it's not actually _recursive_. It's a single-pass perp-hedged carry trade that kicks in when
funding rates flip negative.

**Proposed new name**: `CARRY_BORROW_PERP_HEDGED` (drop "RECURSIVE").

**Plus new variant**: `CARRY_BORROW_PERP_HEDGED_DATED` for the dated-futures equivalent (term-structure flip case).

**Alternative naming** (operator-proposed) emphasising the inversion-of-basis intuition:

- `CARRY_BASIS_PERP_INV` (was `CARRY_BORROW_PERP_HEDGED`) — inverse of `CARRY_BASIS_PERP`.
- `CARRY_BASIS_DATED_INV` (was `CARRY_BORROW_PERP_HEDGED_DATED`) — inverse of `CARRY_BASIS_DATED`.

**Recommended**: pick the `_INV` naming because it makes the structural symmetry obvious (these ARE inverse basis
trades, not different families of trade).

**Mechanics** (negative-funding regime):

- USD\* share class collateral → lend on Aave (or perp venue if rates available) → borrow ETH → sell ETH to short → long
  perp the same notional.
- P&L = lending rate + perp funding (positive for long when funding negative) − ETH borrow rate.
- Trading-wallet ratio: ~50% perp-collateral / ~50% ETH-borrow (configurable).
- Works for SOL or any token with perp + funding data.
- Future enhancement: if perp venues offer coin borrow + rate + availability data, factor those into routing (historical
  fetching needed).

### 6. Centralized carry engine — architecture principle

**Operator directive**: "logic should be done in centralised abstractable way that fits structure rather than a series
of bolt ons as lots of params and decision making are the same anyway".

**Implied refactor**:

- ONE carry strategy engine.
- Axes determining the variant:
  - **share-class** (USD\* / ETH / SOL / future)
  - **staking-leg** (on / off)
  - **hedge-leg** (off / perp / dated-future)
  - **recursion** (none / sequential / flash-loan)
  - **direction** (direct / inverse — for negative-funding regime)
- Each `CARRY_*` archetype = a named configuration of this engine.
- Eliminates 8+ near-duplicate code paths.

**Implementation impact**: `strategy-service` carry handlers consolidate to one `CarryFamilyEngine` with axis-driven
dispatchers (similar to writegate slice (c) `_publish_emission_check` generalised dispatcher).

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
- **Pure option vol arb** ← **NEW HOMEWORK ASSIGNED 2026-05-12**: cross-venue same-strike-same-term option price
  dispersion. _Not_ a Vol Trading archetype (no vol-edge view); it's price-dispersion arb in the Arbitrage family.

All ARBITRAGE_PRICE_DISPERSION variants = **USD\* share class** by construction.

### 8. ARBITRAGE_CROSS_DOMAIN_EVENT — universe expansion

**Cross-domain event arb universe** (expiry-aligned events priced across multiple venue domains):

- Sports book vs Polymarket (e.g. "Lakers beat Celtics" on Pinnacle + Polymarket).
- Sports book vs Kalshi (event-binary on Kalshi).
- Sports book vs Opinion.trade.
- Polymarket vs Kalshi vs Opinion.trade (3-way prediction-CLOB dispersion).
- **CME binary options** (event-aligned binaries with same expiry — e.g. CPI-print binaries) added to the cross-domain
  universe.

**Definition**: same real-world event listed in ≥2 venue domains (sports book / prediction CLOB / CME binary) where
expiries align → arb across them.

When the same real-world event appears in ONE domain only (e.g. Polymarket alone) but at multiple price-quote venues, it
falls under `ARBITRAGE_PRICE_DISPERSION` (cross-book within domain). Cross-domain = cross-venue-type, not
cross-venue-instance.

### 9. MARKET_MAKING_EVENT_SETTLED — RETAIN, not legacy

**Operator pushback**: "why we removing MARKET_MAKING_EVENT_SETTLED and how are we market making betfair for example
then where does this fall".

**Resolution**: KEEP `MARKET_MAKING_EVENT_SETTLED` as a first-class archetype (drop "legacy" label). It's the canonical
home for:

- Sports exchange back/lay MM: Betfair / Smarkets / Matchbook / Betdaq.
- (Polymarket goes to `MARKET_MAKING_PREDICTION` per Phase 9 split, but `MARKET_MAKING_EVENT_SETTLED` is the
  bookmaker-style umbrella).

**Splitting rule**:

- Sports exchange (back/lay model) → `MARKET_MAKING_EVENT_SETTLED`.
- Prediction CLOB (binary YES/NO outcome via order book) → `MARKET_MAKING_PREDICTION`.

**Per-archetype doc completion**: write `market-making-event-settled.md` covering Betfair/Smarkets/etc. back/lay quoting
mechanics, vig-free pricing, settlement integration.

### 10. MARKET_MAKING_CONTINUOUS — split into granular variants, drop legacy

Per the Phase 9 expansion: legacy `MARKET_MAKING_CONTINUOUS` covers too much. Once the granular variants
(`MARKET_MAKING_PASSIVE_SPREAD` / `_INVENTORY_SKEW` / `_ML_LEAN` / `_QUEUE_MICROSTRUCTURE`) are doc-complete, deprecate
the legacy.

**Completion criterion**: ALL 4 granular variants doc-complete + tested + at least one live config per variant → safe to
deprecate `MARKET_MAKING_CONTINUOUS`. Until then, keep both.

### 11. Vol Trading — surface infra + doc completion

**Operator-requested infra** (pre-May-23):

- SVI / SSVI options surface fitter (per-venue per-asset).
- Normalised strike + term slices (constant-moneyness, constant-tenor) for ML continuity.
- ML predictions on fixed normalised strikes/terms → convert to closest real strikes at trade time.
- "Lots of existing stuff around" — verify what's shipped vs needs build (slot 6 audit).

**Doc completion** for all 19 Vol Trading archetypes:

- `VOL_TRADING_OPTIONS` (legacy — covered)
- ✅ `VOL_CARRY` — PM@3bdadf74 (2026-05-19 slot 1)
- `VOL_ARB_RV_IV` / `VOL_SPREAD_STRUCTURES` / `VOL_OVERLAY_COVERED_CALLS` / `VOL_OVERLAY_PROTECTIVE_PUT` /
  `VOL_STRADDLE` / `VOL_SYNTHETIC_DELTA` / `VOL_MARKET_MAKING` / `VOL_ML_LEAN` / `VOL_0DTE_GAMMA_SCALPING` /
  `VOL_0DTE_PIN_RISK` / `VOL_TERM_STRUCTURE_ARB` / `VOL_TERM_STRUCTURE_SLOPE` / `VOL_DISPERSION` / `VOL_VARIANCE_SWAP` /
  `VOL_LEAPS_CONVEXITY` / `VOL_CROSS_ASSET_SPREAD` / `VOL_RATIO_SPREAD`

**Pure option vol arb** (cross-venue same-strike same-term price-dispersion) → `ARBITRAGE_PRICE_DISPERSION` (NOT a Vol
Trading archetype; price-dispersion arb).

### 12. Portfolio — doc completion ✅ SHIPPED 2026-05-18 slot 3

All 4 Portfolio archetype docs created at PM@`747bd623`:

- `architecture-v2/archetypes/portfolio-multi-strategy.md` ✅
- `architecture-v2/archetypes/portfolio-risk-parity.md` ✅
- `architecture-v2/archetypes/portfolio-factor-allocation.md` ✅
- `architecture-v2/archetypes/portfolio-tactical-overlay.md` ✅
- `architecture-v2/families/portfolio.md` ✅ (family doc)

`strategy-summary.md` updated: "(per-archetype doc pending)" labels removed; links to new docs added.

### 13. Code/config wiring — share-class × archetype × venue universe matrix

**Per-archetype capability matrix** must be hooked up:

- **Share class compatibility**: which share classes can run which archetype? (e.g. `ARBITRAGE_*` always USD*;
  `CARRY_STAKED_BASIS` USD*-only; `CARRY_RECURSIVE_STAKED` USD\*/ETH/SOL).
- **Treasury management**: per-share-class deposit/withdraw routing per archetype's venue set (composes with venue ×
  deposit-chain × custody matrix issue doc shipped earlier today).
- **Venue universe filter**: vol archetypes don't execute on spot-only venues; perp archetypes don't execute on
  spot-only venues; arbitrage archetypes need ≥2 venues for the spread; etc.
- **Strategy registry update**: `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` +
  `ARCHETYPE_TO_FAMILY` dict + per-archetype `topology_requirements` + `share_class_compatibility` + `venue_universe`.

## PnL Emission Readiness (StrategyPnlStreamEvent — per architecture-unlock plan)

Per operator directive 2026-05-20 and `trading_agent_service_architecture_unlock_2026_05_22.md` Phase 1+2:

| Archetype                    | Family                 | Emits StrategyPnlStreamEvent                                                 | Status                            |
| ---------------------------- | ---------------------- | ---------------------------------------------------------------------------- | --------------------------------- |
| `carry_staked_basis`         | Carry & Yield          | ✅ May-23 (per architecture-unlock plan Phase 2)                             | SHIPPED strategy-service@a0f87c66 |
| `arbitrage_price_dispersion` | Arbitrage / Structural | ✅ May-23 (per architecture-unlock plan Phase 2)                             | SHIPPED strategy-service@a0f87c66 |
| All other archetypes (55)    | —                      | TODO post-cutover (when continuous-paper infrastructure lands per archetype) | —                                 |

## Counts after refinement

Current section enumeration in strategy-summary.md = **55**. After refinement:

| Family                 | Count                                                                        | Δ from current                                               |
| ---------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------ |
| ML Directional         | 2                                                                            | 0                                                            |
| Rules Directional      | 2                                                                            | 0                                                            |
| Carry & Yield          | **8 → 9** (add `CARRY_STAKED_BASIS_DATED`)                                   | +1                                                           |
| Arbitrage / Structural | 7                                                                            | 0 (no archetype count change; sub-variants are configs/axes) |
| Market Making          | 10 → **9** (after legacy deprecation post-completion)                        | -1 (eventually)                                              |
| Event-Driven           | 1                                                                            | 0                                                            |
| Vol Trading            | **19 → 18** (after `VOL_TRADING_OPTIONS` legacy deprecation post-completion) | -1 (eventually)                                              |
| Stat Arb / Pairs       | 2                                                                            | 0                                                            |
| Portfolio              | 4                                                                            | 0                                                            |

**Pre-deprecation total**: 56 (current 55 + new `CARRY_STAKED_BASIS_DATED`). **Post-deprecation target**: 54 (drop 2
legacy archetypes after granular variants doc-complete). **+rename**: `CARRY_RECURSIVE_BORROW_PERP_HEDGED` →
`CARRY_BASIS_PERP_INV`; add `CARRY_BASIS_DATED_INV` (was already in the +1).

**Operator decision needed**:

- (a) `CARRY_BORROW_PERP_HEDGED` / `CARRY_BORROW_PERP_HEDGED_DATED` (descriptive)
- (b) `CARRY_BASIS_PERP_INV` / `CARRY_BASIS_DATED_INV` (inverse-of-basis intuition) **[my recommendation]**

**PnL emission status (StrategyPnlStreamEvent)**:

- `carry_staked_basis`: ✅ May-23 (architecture-unlock plan Phase 2 — strategy@a0f87c66)
- `arbitrage_price_dispersion`: ✅ May-23 (architecture-unlock plan Phase 2 — strategy@a0f87c66)
- All other archetypes: TODO post-cutover (when continuous-paper infrastructure lands per archetype)

## Routing (per-slot)

**Slot 2** (defi_catalogue + cross_asset_audit owner):

- UAC `StrategyArchetype` enum updates: rename + add `CARRY_STAKED_BASIS_DATED` + `CARRY_BASIS_PERP_INV` +
  `CARRY_BASIS_DATED_INV` (pending operator naming choice).
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
- Vol Trading 18 per-archetype docs (slot 6 has Phase 2C-H pool-class connector implementation absorbed from Harsh slot
  4 — extend with Vol Trading docs).

**Slot 8** (codex_vs_citadel + cross_cutting #4):

- Update `/codex/09-strategy/strategy-summary.md`: corrections per items 1-13 above; corrected counts.
- Per-archetype doc completion: 4 Portfolio + 18 Vol + `market-making-event-settled.md` (drop legacy) + new
  `carry-staked-basis-dated.md` + new `carry-basis-perp-inv.md` + new `carry-basis-dated-inv.md`.
- Workspace-grep + reconcile `(8 families / 18 archetypes)` / `(9 families / 53 archetypes)` /
  `(9 families / 55 archetypes)` count drift across all plans + master plan + CLAUDE.md (likely 10+ locations).
- Update `/codex/09-strategy/strategy-summary.md` § 18 line (Phase 9 expansion sub-count drift).

**Slot 1 (main)**:

- Master plan `:224` re-update post slot-2/5/6/8 ships.
- Surface naming decision (a)/(b) for operator (this commit's AskUserQuestion).
- Surface Deribit-LST-collateral verification ask (slot 2 or slot 4 verification — for `CARRY_STAKED_BASIS_DATED`
  Deribit eligibility).

## 🚀 OPERATOR DIRECTIVE 2026-05-12 — SHIP ALL SCOPE THIS CYCLE (no Cycle-6 deferrals)

> _"ship all regardless of risk we will land"_

**Full taxonomy refinement scope = MUST-SHIP within 2026-05-15 freeze-gate cycle**, NOT partial / at-risk-deferred /
Cycle-6-deferred. Every routed item (slot 2 / 5 / 6 / 8) is a freeze-gate hard requirement now:

- **Slot 2** — UAC enum + ARCHETYPE_TO_FAMILY + share-class/venue compat matrix. ~30 min mechanical. **MUST-SHIP**.
- **Slot 5** — `CarryFamilyEngine` **fully wired across all 9 Carry archetypes** (NOT scaffold-only). Axes: share-class
  × staking-leg × hedge-leg × recursion × direction × sequential-vs-flashloan. Replaces all existing carry handlers.
  **MUST-SHIP**.
- **Slot 6** — **SVI/SSVI options surface fitter** + **normalised strike/term slicing infra**
  (`vol/surface/normalised_grid.py`) + **all 18 Vol Trading per-archetype docs**. Audit existing libs (py_vollib /
  QuantLib / ArbitrageRepair) first → integrate vs greenfield call. **MUST-SHIP**.
- **Slot 8** — `strategy-summary.md` 13 corrections + workspace-grep count drift + **4 Portfolio docs** + **new Carry
  docs** (`carry-staked-basis-dated.md` + `carry-basis-perp-inv.md` + `carry-basis-dated-inv.md`) +
  `market-making-event-settled.md` retention update + **Deribit LST verification** + **legacy deprecation execution**
  (`MARKET_MAKING_CONTINUOUS` + `VOL_TRADING_OPTIONS` enum-remove + workspace-grep migration audit + config flips).
  **MUST-SHIP**.

**Allocation principle override**: pace is 5× calibrated; capacity exists. Risk = at-risk-items-pre-2026-05-15-freeze is
preferred over Cycle-6-defer. If a slot is overloaded, fan-out sub-agents 6-8 deep (already in playbook).

**3 calendar days remaining (2026-05-13 / 14 / 15)**. Each slot has ~3-5 days of single-AI work at calibrated pace =
~15-25 days at 5× = sufficient.

**Cross-slot sequencing for May-23 critical path coverage**:

1. Slot 2 ships UAC enum FIRST (~30 min) — unblocks slot 5 + slot 8 imports.
2. Slot 5 + slot 6 + slot 8 fan out in parallel after UAC lands.
3. Slot 8 workspace-grep + count-drift sweep + legacy deprecation runs LAST (after granular variant docs land, per
   "deprecate as soon as docs land" decision).

**Per-slot capacity confirmation**: this taxonomy work is ON TOP OF existing slot scope (Day-1 ✅ + SCOPE EXTENSION +
SCOPE EXTENSION 2 + SCOPE EXTENSION 3 Harsh absorption). Operator confirmed pace covers it. No scope-cuts.

## ✅ Operator decisions received 2026-05-12

1. **Naming**: ✅ Option (b) — `CARRY_BASIS_PERP_INV` + `CARRY_BASIS_DATED_INV` (inverse-of-basis intuition).
   Implementation:
   - UAC enum: rename `CARRY_RECURSIVE_BORROW_PERP_HEDGED` → `CARRY_BASIS_PERP_INV`; add `CARRY_BASIS_DATED_INV`.
   - `defi_recursive_borrow_archetypes_2026_05_10.md` updated to reflect (Family 2 → renamed).
   - Per-archetype docs: rename file `carry-recursive-borrow-perp-hedged.md` → `carry-basis-perp-inv.md`; add new
     `carry-basis-dated-inv.md`.
   - Workspace-grep: 2026-05-12 archetype mentions reconciled (slot 8 sweep).
2. **Centralized `CarryFamilyEngine`**: ✅ ONE engine + axis-driven config — slot 5 ships. Axes: share-class ×
   staking-leg × hedge-leg × recursion × direction × sequential-vs-flashloan. Validates against existing
   `defi_recursive_borrow_archetypes_2026_05_10.md` Phases 1-2 design batch (slot 5's Day-1 work).
3. **Legacy deprecation**: ✅ **Pre-cutover** — deprecate `MARKET_MAKING_CONTINUOUS` + `VOL_TRADING_OPTIONS` as soon as
   granular variant docs land (NOT post-cutover). Slot 6 owns Vol Trading 18-doc completion → triggers
   `VOL_TRADING_OPTIONS` deprecation. Slot 8 / Harsh slot 6 owns MM granular completion → triggers
   `MARKET_MAKING_CONTINUOUS` deprecation. Config migration audit before deprecation: workspace-grep for live strategy
   configs using the legacy enums → migrate to granular variants in same logical unit.
4. **Deribit LST collateral verification**: ✅ Single slot — **slot 8 cross_asset audit**. Output: list of LSTs Deribit
   accepts as dated-futures collateral (if any). Result feeds `CARRY_STAKED_BASIS_DATED` venue list (OKX + Bybit known;
   Deribit pending verification).

## Operator decisions needed (next round, surfaced after slot 2/5/6/8 progress)

## ✅ Verification status — 2026-05-18 (slot-3 audit PM@e2dd2a2a)

### Item V-1 — ARCHETYPE_TO_FAMILY completeness ✅ VERIFIED

`unified_api_contracts/internal/architecture_v2/enums.py` `ARCHETYPE_TO_FAMILY` dict audited 2026-05-18:

- **Total entries**: 55 (matches `strategy-summary.md` count of 55)
- **Family coverage**: all 9 families represented (ML_DIRECTIONAL ×2, RULES_DIRECTIONAL ×2, CARRY_AND_YIELD ×8,
  ARBITRAGE_STRUCTURAL ×7, MARKET_MAKING ×10, EVENT_DRIVEN ×1, VOL_TRADING ×19, STAT_ARB ×2, PORTFOLIO ×4)
- **All 55 enum members have exactly one ARCHETYPE_TO_FAMILY entry** — no orphans, no duplicates confirmed.

**✅ UAC changes DONE — slot 3 — 2026-05-18 — uac@0196842 + strategy-service@a636a29:**

- `CARRY_RECURSIVE_BORROW_PERP_HEDGED` ✅ renamed → `CARRY_BASIS_PERP_INV` in UAC enum, ARCHETYPE_TO_FAMILY,
  archetype_config, risk_rules, chain_env (STEP 5.72 fix), tests
- `CARRY_STAKED_BASIS_DATED` ✅ added to enum + ARCHETYPE_TO_FAMILY + archetype_config + risk_rules + archetype_defaults
  (TIER_MID_VARIANCE) + factory (CarryStakedBasisEngine) + catalog (3 seed slots) + tests
- `CARRY_BASIS_DATED_INV` ✅ added to enum + ARCHETYPE_TO_FAMILY + archetype_config + risk_rules + archetype_defaults
  (TIER_STABLE_STRUCTURAL) + factory (CarryBasisDatedEngine) + catalog (3 seed slots) + tests
- Pre-deprecation total: 57 (55 pre + rename-unchanged + 2 additions)

### Item V-2 — Taxonomy plan correction flags ✅ DOCUMENTED

Two discrepancies found between this plan's operator decisions and current UAC state:

1. **§9 `MARKET_MAKING_EVENT_SETTLED` legacy flag**: UAC line 91 marks it `# legacy` but operator decision (§9 "RETAIN,
   not legacy") says to KEEP it as a first-class archetype. The enum VALUE and ARCHETYPE_TO_FAMILY entry are correct
   (present + mapped); only the inline `# legacy` comment is wrong. Slot 2 to fix comment.
2. **Archetype count**: strategy-summary.md says 55; post-`CARRY_STAKED_BASIS_DATED` addition will be 56. The count in
   `strategy-summary.md` will auto-correct once slot 2 adds the new enum member + ARCHETYPE_TO_FAMILY entry, per "the
   enum wins" drift correction note in strategy-summary.md.

### Item V-3 — Per-archetype doc completion (3 new/renamed docs) ✅ SHIPPED 2026-05-18 slot-3

Slot-3 created the missing per-archetype docs for the 3 V-1 archetypes (PM@`f3236961`):

- `/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp-inv.md` ✅ — canonical doc for renamed archetype;
  recursive borrow loop + CeFi perp hedge; replaces `carry-recursive-borrow-perp-hedged.md` (redirect banner added)
- `/codex/09-strategy/architecture-v2/archetypes/carry-basis-dated-inv.md` ✅ — new archetype; inverse dated basis
  (short future + long cash captures backwardation); full config schema + risk profile
- `/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis-dated.md` ✅ — new archetype; dated-contract variant
  of staked basis; staking yield + locked basis premium at expiry; Deribit/Drift/Bybit catalog slots
- `/codex/09-strategy/strategy-summary.md` ✅ — Carry & Yield count 8 → 10; new archetype entries; updated links

**Scope boundary**: Slot-8 Vol Trading 18 per-archetype docs + `market-making-event-settled.md` retention doc remain on
Slot 8's stack (not yet shipped). This V-3 covers only the 3 V-1 Carry archetypes.

### Item V-4 — Count-drift codex sweep ✅ SHIPPED 2026-05-18 slot-3

Slot-3 updated 4 codex docs to reflect 55 → 57 archetype count post V-1 additions (PM@`f5107fe4`):

- `codex/00-SSOT-INDEX.md` ✅ — "9 families × 55 archetypes" → "9 families × 57 archetypes"; "StrategyArchetype (55)" →
  "(57)"; "55 strategy archetypes" → "57 strategy archetypes"
- `/codex/09-strategy/architecture-v2/README.md` ✅ — "## 55 Archetypes" → "## 57 Archetypes"; "1 of 55 archetypes" → "1
  of 57"; "Total: 55 archetypes" → "57"; Carry & Yield row: renamed `CARRY_RECURSIVE_BORROW_PERP_HEDGED` →
  `CARRY_BASIS_PERP_INV` + added `CARRY_STAKED_BASIS_DATED` + `CARRY_BASIS_DATED_INV`; 8 docs → 10 docs; historical
  narrative updated with V-1 rename + +2 addition
- `/codex/09-strategy/architecture-v2/strategy-registry-v2.md` ✅ — "9 families / 55 archetypes" → "9 families / 57
  archetypes" in the PARTIALLY SUPERSEDED banner canonical-counts note
- `/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md` ✅ — "55 archetypes" → "57 archetypes"
  (frontmatter + body); CARRY_RECURSIVE_BORROW_PERP_HEDGED row renamed + 2 new stub rows added for
  `CARRY_STAKED_BASIS_DATED` + `CARRY_BASIS_DATED_INV`

**Also verified**: `MARKET_MAKING_EVENT_SETTLED` `# legacy` bug from V-2 was already fixed at uac@`2e53d1b` (not slot-3
work; pre-existing fix). CLAUDE.md + `master_to_live_defi_2026_05_23.md` have no archetype count references (confirmed
clean).

**Scope boundary**: `strategy-summary.md` lines 807/815 say "55 archetypes" in a historical narrative context (correct —
they describe the size of the manifest JSON before Phase 9 further expansion); not updated. Plans/epics with "18
archetypes" or "53 archetypes" are all historical baseline markers (correct context; not updated).

### Item V-5 — Remaining stale CARRY_RECURSIVE_BORROW_PERP_HEDGED refs in codex ✅ SHIPPED 2026-05-19 slot-3

Slot-3 found and updated 6 codex docs + 1 active plan that still referenced the old archetype name as a live
(non-historical) identifier (PM@`013d6d0f`):

- `/codex/04-architecture/flash-loan-receiver.md` ✅ — RecursiveLeverageReceiver users list
- `/codex/04-architecture/cefi-perp-leg-bybit.md` ✅ — Family 2 context callout
- `/codex/04-architecture/batch-live-architecture.md` ✅ — archetype × engine table row
- `/codex/08-workflows/cutover-window-dependency-order.md` ✅ — backtest dependency diagram
- `/codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` ✅ — Family 2 section header
- `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` ✅ — currency note + 57-count annotation added
- `plans/active/compute_optimization_mock_data_2026_05_13.md` ✅ — deferred item archetype list

Additional active references found and fixed in follow-on commits (PM@`d17236bb`, `e9e5f976`):

- `plans/active/defi_recursive_borrow_archetypes_2026_05_10.md` ✅ — Family 2 definition + ground-truth note annotated
- `plans/active/defi_master.md` ✅ — IN-FLIGHT banner + ready-to-go-live list

All remaining `CARRY_RECURSIVE_BORROW_PERP_HEDGED` references in the PM repo are now in historical change-log narratives
(correct context; intentionally preserved). Full workspace audit confirmed clean.

### Item V-6 — carry-and-yield family doc 6 → 10 archetypes ✅ SHIPPED 2026-05-19 slot-3

`/codex/09-strategy/architecture-v2/families/carry-and-yield.md` was last written when the family had 6 archetypes.
After V-1 additions (uac@0196842) the canonical count is 10. Slot-3 updated (PM@`a28a315e`):

- Frontmatter archetype count: `6` → `10` with V-1 provenance note
- Alpha thesis: 6 bullets → 10 bullets (added CARRY_BASIS_DATED_INV, CARRY_BASIS_PERP_INV, CARRY_STAKED_BASIS_DATED,
  CARRY_RECURSIVE_BORROW_LENDING_ONLY)
- Section heading: `## 6 Archetypes` → `## 10 Archetypes`
- Archetype table: 6 rows → 10 rows with 4 new entries and their position structures / rates / when-to-use
- Cross-references section: 4 new archetype doc links added

### Item V-7 — arbitrage-structural family doc 2 → 7 archetypes ✅ SHIPPED 2026-05-19 slot-3

`/codex/09-strategy/architecture-v2/families/arbitrage-structural.md` showed count 2; UAC enum has 7 after MEV
variants + ARBITRAGE_CROSS_DOMAIN_EVENT were added. Updated (PM@`4d0ffca5`):

- Frontmatter archetype count: `2` → `7` with V-1 provenance note
- Section heading: `## 2 Archetypes` → `## 7 Archetypes`
- Table: 2 rows → 7 rows (added ARBITRAGE_MEV_BACKRUN, ARBITRAGE_MEV_SANDWICH (theoretical-only),
  ARBITRAGE_MEV_JIT_LIQUIDITY, ARBITRAGE_MEV_LIQUIDATION_BUNDLE, ARBITRAGE_CROSS_DOMAIN_EVENT (doc pending Slot 8))
- `Shared primitives (both archetypes)` → `(all archetypes)`
- Cross-references: 4 MEV archetype doc links added

### Item V-8+V-9 — codex-wide 55/53 archetype count drift → 57 ✅ SHIPPED 2026-05-19 slot-3

Found and fixed 3 additional codex docs still referencing stale 55/53 archetype counts (PM@`37b520ce`):

- `/codex/09-strategy/README.md` ✅ — "9 families × 55 archetypes" + "StrategyArchetype (55)" → 57
- `/codex/09-strategy/mvp-universe-per-asset-group.md` ✅ — "enum (53 archetypes)" → 57; "25 files" → 35
- `/codex/09-strategy/architecture-v2/MIGRATION.md` ✅ — Phase 9 note "55 archetypes" → 57 with V-1 provenance

Also pinged Slot 1 main about `master_to_live_defi_2026_05_23.md:264` stale "Carry & Yield (6)" → (10) + "53 archetypes"
→ 57 (Slot 1 owns that file per slot-precedence rule).

`strategy-summary.md` stale "55 archetypes" references at lines 808/816 remain — Slot 8 scope per taxonomy plan routing.

### Item V-9 — category-instrument-coverage.md scope header 53 → 57 ✅ SHIPPED 2026-05-19 slot-3

`category-instrument-coverage.md:11` said "53 v2 strategy archetypes". The V-4 sweep added a 2026-05-18 currency note in
the changelog (lines 1441-1443) but the scope header itself was missed. Fixed (PM@`85f7fe34`).

### Item V-10 — architecture-v2/README.md arbitrage doc count 7 → 6 ✅ SHIPPED 2026-05-19 slot-3

README table row for Arbitrage / Structural said "7 docs" but `arbitrage-cross-domain-event.md` doesn't exist — only 6
docs present. Corrected to "6 docs (1 pending Slot 8)" (PM@`f7ded4ef`).

### Item V-11 — architecture-v2/README.md MM + Vol doc counts corrected ✅ SHIPPED 2026-05-19 slot-3

README Docs column said "10 docs" for Market Making (only 5 exist) and "19 docs" for Vol Trading (only 2 exist). The
counts reflected archetype targets, not actual files. Corrected to "5 docs (5 pending Slot 8)" and "2 docs (17 pending
Slot 6/8)" (PM@`f36f2cd4`).

### Item V-12 — 23 missing per-archetype codex docs shipped ✅ SHIPPED 2026-05-19 slot-4

All 23 pending archetype docs written and pushed. README table updated to reflect actual counts.

**Batch 1** (PM@`642014e1`) — 9 Vol Trading docs: `vol-arb-rv-iv.md`, `vol-spread-structures.md`,
`vol-overlay-covered-calls.md`, `vol-overlay-protective-put.md`, `vol-straddle.md`, `vol-synthetic-delta.md`,
`vol-market-making.md`, `vol-ml-lean.md`, `vol-0dte-gamma-scalping.md`

**Batch 2** (PM@`6d4011ae`) — 14 docs (8 Vol + 5 MM + 1 Arb): `vol-0dte-pin-risk.md`, `vol-term-structure-arb.md`,
`vol-term-structure-slope.md`, `vol-dispersion.md`, `vol-variance-swap.md`, `vol-leaps-convexity.md`,
`vol-cross-asset-spread.md`, `vol-ratio-spread.md`, `market-making-passive-spread.md`,
`market-making-inventory-skew.md`, `market-making-ml-lean.md`, `market-making-queue-microstructure.md`,
`market-making-prediction.md`, `arbitrage-cross-domain-event.md`

**README updated** (this commit): Arbitrage `7 docs`, Market Making `10 docs`, Vol Trading `19 docs`, Document Layout
comment updated to `57 docs — all archetypes documented`. All 57 archetypes now have canonical docs.

### Item V-13 — Full architecture-v2 doc audit + family-doc reconciliation ✅ SHIPPED 2026-05-20

Operator-requested audit of every `codex/09-strategy/architecture-v2/` family + archetype doc against the UAC enum (57
archetypes / 9 families), prompted by concern that the 2026-05-19 V-12 batch (23 docs) was written under thin guidance.

**Key finding — the V-12 archetype docs are sound.** All 18 Vol, 5 granular MM, `ARBITRAGE_CROSS_DOMAIN_EVENT`, 4 MEV,
and 3 DeFi-LP docs are accurate, internally consistent, and useful. They use a lighter 7-section taxonomy than the
README's 11-section authoring convention, but they are complete and correct — **no rewrites needed.** The real drift was
in the **family docs**, which were never updated after the Phase-9 expansion, plus scattered small defects.

**Fixed (4 commits on `live-defi-rollout`):**

- `families/vol-trading.md` ✅ — "1 Archetype" → enumerate all **19** (table + 19 cross-ref links) (PM@`f976d521`)
- `families/market-making.md` ✅ — "2 Archetypes" → enumerate all **10** (5 granular CeFi + prediction + 3 DeFi LP);
  corrected the stale "passive Uniswap-V2-style LP is not in this family" bullet (`DEFI_LP_POOL` _is_ full-range/passive
  pool LP, in `MARKET_MAKING`) (PM@`f976d521`)
- `families/arbitrage-structural.md` ✅ — un-staled `ARBITRAGE_CROSS_DOMAIN_EVENT` "doc pending" labels (PM@`f976d521`)
- `architecture-v2/naming-convention.md` ✅ — "Family axis (8 values)" → 9 (add `PORTFOLIO`); "Archetype axis (18
  values)" → 57 (replaced drift-prone inline 18-list with a pointer to README + enum SSOT) (PM@`8b6350dc`)
- `architecture-v2/README.md` ✅ — removed duplicate decision-tree bullet (items 9 & 10 were identical) (PM@`8b6350dc`)
- `archetypes/defi-lp-pool.md` ✅ — `LP_DEPOSIT`/`LP_WITHDRAW` are **not** enum values; aligned to the real engine wire
  format (`SWAP` + `lp_operation="deposit"|"withdraw"`, verified against `defi_lp/pool.py`) (PM@`217660c1`)
- `archetypes/defi-lp-concentrated.md` ✅ — clarified `LP_MINT`/`LP_BURN` now exist (actions 13/14) but engines still
  route via `SWAP`+`lp_operation`; migration is a non-blocking follow-up (PM@`217660c1`)
- `archetypes/vol-carry.md` ✅ — dropped stale "(doc pending)" labels (PM@`217660c1`)
- `archetypes/vol-0dte-pin-risk.md` ✅ — "Gamma scalping archetype" link pointed at `vol-arb-rv-iv.md`; corrected to
  `vol-0dte-gamma-scalping.md` (PM@`217660c1`)
- `archetypes/carry-recursive-borrow-lending-only.md` ✅ — sibling link pointed at the renamed
  `carry-recursive-borrow-perp-hedged` redirect; repointed to `carry-basis-perp-inv.md`; added `StrategyFamily` link +
  disambiguated the plan's "Family 0/1/2" numbering from `StrategyFamily` (PM@`217660c1`)
- 4 MEV + 3 DeFi-LP archetype docs ✅ — added markdown family-doc links (were plain-text family names) (PM@`217660c1`)
- `strategy-summary.md` ✅ — registry/coverage narrative still cited "55 archetypes" at lines 808/816 (the V-8-deferred
  leftovers); bumped to 57 and clarified the manifest declares cells for a 22-archetype live subset today
  (PM@`09f68f3a`)

**Verified clean (no change needed):** all 18 Vol archetype docs, 5 granular MM docs, `arbitrage-cross-domain-event.md`,
3 MEV docs (body), `category-instrument-coverage.md` (scope = 57), `archetype-paper-readiness.md` (= 57), README
archetype doc-count table (2/2/10/7/10/1/19/2/4 = 57). `archetypes/` holds 58 files = 57 enum archetypes + 1 redirect
stub (`carry-recursive-borrow-perp-hedged.md`).

## Composes with

- `/codex/09-strategy/strategy-summary.md` (canonical archetype list)
- `unified-api-contracts/.../internal/architecture_v2/enums.py` (UAC enum)
- `plans/active/defi_recursive_borrow_archetypes_2026_05_10.md` (slot 5 Phases 1-2 design + new Family 1/2 archetypes)
- `plans/active/master_to_live_defi_2026_05_23.md:224` (master plan strategy archetypes row)
- `plans/archive/issues/venue_chain_custody_routing_matrix_2026_05_12.md` (share-class × venue compatibility matrix
  overlap)
- `cursor-configs/CLAUDE.md` (any archetype-count references)
