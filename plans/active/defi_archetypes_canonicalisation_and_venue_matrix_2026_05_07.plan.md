---
title: "DeFi archetypes canonicalisation + venue-collateral matrix correction (multi-stream)"
created: 2026-05-07
author: claude-session
source:
  - plans/active/issues/defi_archetypes_doc_plan_drift_2026_05_07.md (Harsh audit + 2026-05-07 PM operator follow-up)
  - unified-api-contracts/unified_api_contracts/registry/venue_collateral.py (stale SSOT)
  - codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md
  - codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md
  - codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md
  - plans/archive/leveraged_leg_controller_2026_05_01.plan.md
  - plans/archive/carry_staked_basis_structure_axis_2026_05_04.plan.md
  - plans/active/master_to_live_defi_2026_05_23.plan.md
  - plans/active/defi_master_2026_05_07.plan.md
related_archetypes:
  - CARRY_STAKED_BASIS
  - ARBITRAGE_PRICE_DISPERSION
  - CARRY_BASIS_PERP
  - RECURSIVE_STAKED
  - all archetypes touched by LeveragedLegController
---

# DeFi archetypes canonicalisation + venue-matrix correction

This plan ships the doc + plan + code corrections raised by the 2026-05-07 operator review of
[`plans/active/issues/defi_archetypes_doc_plan_drift_2026_05_07.md`](../active/issues/defi_archetypes_doc_plan_drift_2026_05_07.md).
Each stream below is independently shippable. Streams A–D run in parallel; Stream E is the integration sweep that pulls
everything together for the master plan.

**Workspace rule applied:** _docs are the intent_ — verbal doc / plan updates ship even when the code change is
deferred, so the doc / plan / code triad stays in sync. Code follow-throughs are tracked as their own todos with
explicit `**DEFERRED**` markers where applicable.

## Streams overview (parallelisable)

```
Stream A  —  venue_collateral.py SSOT correction          [UAC + codex doc]
Stream B  —  leveraged_funding_arb → ARBITRAGE_PRICE_DISPERSION canonicalisation
                                                          [UAC + codex + plans + strategy-service]
Stream C  —  LeveragedLegController codex doc backport    [codex archetypes/]
Stream D  —  target_leverage / target_net_delta schemas   [codex archetypes/ + deployment-UI]
Stream E  —  Master plan + defi_master alignment sweep    [PM plans/active/]
```

---

## Stream A — `venue_collateral.py` SSOT correction

**Problem:** UAC `venue_collateral.py` carries a 2026-05-05 comment claiming _"NO production ETH-perp venue accepts an
ETH LST as direct cross-margin today"_ and explicit `accepted=False` rows for stETH/wstETH on Deribit / Bybit / OKX. Web
verification 2026-05-07 confirms this is **wrong**:

- **DERIBIT** stETH 7.5% haircut, X:PM/X:SM, offsets ETH-perp shorts directly (effective 2026-01-13)
  ([source](https://insights.deribit.com/exchange-updates/portfolio-margin-improvements-for-steth-and-cross-collateral-haircuts/))
- **BYBIT** stETH/METH/USDe UTA-collateral-eligible (stETH+METH since Feb 2024, USDe since Dec 2024)
- **OKX** wstETH on multi-currency-margin / portfolio-margin discount-rate list

`BINANCE` Multi-Assets Mode genuinely does NOT support LSTs (BTC/ETH/BNB/XRP/ADA/DOT/SOL/USDC/USDT only —
cross-collateral feature retired). `HYPERLIQUID` L1 still USDC-only (HIP-3 builder DEXes irrelevant to the ETH-perp
short hedge). `ASTER` is USDT/USDF/asBNB only.

**Tasks**

- [ ] [SCRIPT] P0. Live-API probe to confirm exact 2026-05-07 collateral value ratios for: Deribit stETH, Bybit
      stETH/wstETH/USDe/sUSDe, OKX wstETH/stETH. Document each in a new file
      `unified-trading-pm/codex/14-playbooks/defi/venue-collateral-2026-05-07.md` with screenshot/URL evidence per
      venue. Bandit-clean, no hardcoded creds; use public endpoints where available, manual UI screenshot otherwise.
      Citadel-grade evidence per row before the matrix flip.
- [ ] [UAC] P0. Update `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py` matrix entries:
  - Flip `("DERIBIT", "stETH", accepted=False)` →
    `(accepted=True, haircut_pct=Decimal("0.075"), margin_type="PORTFOLIO", notes="X:PM cross-collateral, offsets ETH-perp directly (2026-01-13 haircut cut from 15→7.5%)")`.
  - Flip `("BYBIT", "stETH", accepted=False)` →
    `(accepted=True, haircut_pct=<verified>, margin_type="UTA", notes="UTA cross-collateral since 2024-02; ratio per Bybit margin-spec page")`.
  - Add new row `("BYBIT", "METH", accepted=True, ...)` if METH probe confirms it's still active.
  - Add new row
    `("BYBIT", "USDe", accepted=True, haircut_pct=<verified>, margin_type="UTA", notes="UTA cross-collateral since 2024-12-19")`.
  - Flip `("OKX", "wstETH", accepted=False)` →
    `(accepted=True, haircut_pct=<verified>, margin_type="MULTI_CCY", notes="multi-currency-margin discount-rate list")`.
  - Update the comment block at line 103–113 to reflect the corrected understanding; remove the "NO production ETH-perp
    venue accepts" claim.
  - Add 2026-05-07 plan reference in the comment block.
- [ ] [UAC] P0. Add unit tests covering the 5+ flipped rows:
      `tests/unit/test_venue_collateral.py::test_lst_acceptance_2026_05_07` verifying
      `venue_accepts_collateral("DERIBIT", "stETH") is True`, etc.
- [ ] [codex] P0. Update
      [`carry-staked-basis.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md) "Today's
      matrix" table (lines 101–112): replace the single DRIFT row with the corrected multi-venue table (DRIFT +
      Deribit + Bybit + OKX); update the slot count from 2 to ~10 (3 ETH-LSTs × 3 ETH-perp-venues + DRIFT/JitoSOL +
      DRIFT/mSOL); update the "Honest — DRIFT is the only venue" sentence to reflect the corrected reality. Update Phase
      7a status from "operator audit pending" → "shipped 2026-05-07 — see plan".
- [ ] [codex] P0. Update
      [`carry-staked-basis.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md) lines 124–130
      (Catalog axis): bump "2 slots today" → "N slots today (post-Stream A flip)".
- [ ] [strategy-service] P1. Confirm `_build_carry_staked_basis` in `target_universe/catalog.py` regenerates the
      expanded slot list automatically from the corrected matrix (per the codex SSOT design). If hardcoded anywhere,
      remove the hardcode. **DEFERRED to next strategy-service touch**: low risk because regeneration is on import.

**Gate:** UAC quality-gates pass with the 5+ flipped rows + new tests; codex doc reflects the corrected matrix; PM
quality-gates pass on the new playbook + carry-staked-basis.md edits.

---

## Stream B — `leveraged_funding_arb` → `ARBITRAGE_PRICE_DISPERSION` canonicalisation

**Operator decision (2026-05-07):** `leveraged_funding_arb` is a **configuration variant of
`ARBITRAGE_PRICE_DISPERSION`**, not a new archetype. Reasoning: funding-rate spread IS the price dispersion in this
case; leverage is orthogonal (Stream D `target_leverage`). The engine `ArbitragePriceDispersionHierarchicalEngine`
already supports LEADER_HEDGE mode.

**Tasks**

- [ ] [codex] P0. Update
      [`arbitrage-price-dispersion.md`](../../codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md):
      promote "Funding-rate dispersion arb | LEADER_HEDGE" from one-line "Supported scenarios" mention to first-class
      sub-section with its own config-schema variant. Document the cross-venue funding mechanic, the leverage
      multiplier, and the volatility-cap clamp.
- [ ] [codex] P0. Resolve circular cross-reference: in `arbitrage-price-dispersion.md` "Not in this archetype" section,
      remove the line pointing at `CARRY_BASIS_PERP` for funding arb. Leave the paired authoritative claim in
      `carry-basis-perp.md` only.
- [ ] [codex] P0. Update [`carry-basis-perp.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md)
      "Not in this archetype" section: keep the line "Cross-venue perp spread arbitrage (funding-rate differential
      between two perp venues for the same asset) — `ARBITRAGE_PRICE_DISPERSION`" but reword it to be authoritative
      rather than circular.
- [ ] [PM-plan] P0. Edit [`master_to_live_defi_2026_05_23.plan.md`](../active/master_to_live_defi_2026_05_23.plan.md):
      rename `leveraged_funding_arb` → `ARBITRAGE_PRICE_DISPERSION` (with config variant
      `ARBITRAGE_PRICE_DISPERSION@funding-dispersion-leveraged` where useful). Update the "Both archetypes" headline to
      use the canonical name.
- [ ] [PM-plan] P0. Edit [`defi_master_2026_05_07.plan.md`](../active/defi_master_2026_05_07.plan.md): same rename.
- [ ] [UAC] P1. Verify `StrategyArchetype` enum in UAC: confirm `ARBITRAGE_PRICE_DISPERSION` exists and that
      `LEVERAGED_FUNDING_ARB` is **not** in the enum. If absent, no enum change needed; if mistakenly added, remove.
- [ ] [strategy-service] P1. Confirm catalog has rows for the funding-dispersion-leveraged variant under
      `ARBITRAGE_PRICE_DISPERSION` archetype prefix. If not, add. **DEFERRED to strategy-service feature work**; tracker
      only here so the task isn't lost.
- [ ] [tracer-scripts] P1. Confirm `scripts/trace_arbitrage_price_dispersion.py` (or equivalent) handles the
      funding-dispersion-leveraged variant. **DEFERRED**.
- [ ] [P&L attribution] P1. Confirm `pnl-attribution-service` rows attribute under `ARBITRAGE_PRICE_DISPERSION` for the
      funding-dispersion-leveraged variant. **DEFERRED**.

**Gate:** Codex doc/code/plans all use `ARBITRAGE_PRICE_DISPERSION` (with config variant) for
funding-dispersion-leveraged. No remaining references to `leveraged_funding_arb` as a standalone archetype except in
this plan + the issue file (as historical context).

---

## Stream C — LeveragedLegController codex doc backport

**Problem:** [`leveraged_leg_controller_2026_05_01`](../archive/leveraged_leg_controller_2026_05_01.plan.md) (archived
post-shipping per the issue file) introduces a generic delta-targeted multi-leg primitive replacing every bespoke
`_build_legs`. Codex archetype docs still describe legs as hand-built (`carry-staked-basis.md` 4-leg LST_AS_MARGIN
sequence, `carry-basis-perp.md` 2-leg paired entry/exit, `arbitrage-price-dispersion.md` ATOMIC / LEADER_HEDGE without
controller layer).

**Operator decision (2026-05-07):** _docs ship now even if the code backport hasn't propagated to all 11 archetypes._

**Tasks** (per archetype doc — each is independently shippable)

- [ ] [codex] P0. [`carry-staked-basis.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md)
      "Token / position flow" + "Execution semantics" sections: rewrite to reference `LegController.update`. Keep the
      4-leg sequence as the **logical** flow (SWAP → STAKE → TRANSFER → TRADE) but credit the controller for
      mechanically generating it. Drop "hand-built" implications.
- [ ] [codex] P0. [`carry-basis-perp.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md): same
      rewrite for the 2-leg paired entry/exit.
- [ ] [codex] P0.
      [`arbitrage-price-dispersion.md`](../../codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md):
      add a "LegController integration" sub-section. ATOMIC mode and LEADER_HEDGE mode both flow through
      `LegController.update` with mode-specific deadlines + compensation rules.
- [ ] [codex] P0. [`recursive-staked.md`](../../codex/09-strategy/architecture-v2/archetypes/recursive-staked.md): same
      rewrite for the recursive supply/borrow loop.
- [ ] [codex] P1. Remaining 7 archetype docs in `codex/09-strategy/architecture-v2/archetypes/` — same rewrite. Per
      Citadel-grade `doc → plan → code` rule, ship even if the code backport for that archetype is deferred. Each doc
      gets a `**Code-backport status:**` line declaring SHIPPED / DEFERRED.
- [ ] [PM-plan] P1. Once the 11 doc rewrites land, update the archived
      [`leveraged_leg_controller_2026_05_01`](../archive/leveraged_leg_controller_2026_05_01.plan.md)'s Phase 4 GATE
      description (in a follow-up commit) to note "doc rewrites shipped 2026-05-07; code backport proceeds
      independently."

**Gate:** All 11 archetype docs reference `LegController.update`. None describe legs as "hand-built" without flagging
that as a deferred-backport state.

---

## Stream D — `target_leverage` / `target_net_delta` config schema extensions

**Problem:** [`leveraged_leg_controller_2026_05_01`](../archive/leveraged_leg_controller_2026_05_01.plan.md) Phase 1.2
promoted `target_leverage` from per-archetype configs to `StrategyInstanceDefinition`. Codex archetype config schemas do
NOT have this field. Without a config-schema slot, deployment-UI strategy builders, paper-trade configs, and operator
runbooks have no surface to set leverage. This is the **entire alpha multiplier** on the funding-dispersion-leveraged
variant (6% → 18% net at 3x).

**Operator decision (2026-05-07):** _agree do this._

**Tasks**

- [ ] [codex] P0.
      [`arbitrage-price-dispersion.md`](../../codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md)
      config schema (currently lines ~84–105): add `target_leverage: float = 1.0`, `target_net_delta: float = 0.0`, and
      the volatility-cap clamp behaviour (`max_underlying_move_pct` + `instrument_volatility_registry_lookup`). Document
      defaults + bounds (e.g. `target_leverage ∈ [1, 10]`, hard-clamped by per-instrument vol cap).
- [ ] [codex] P0. [`carry-basis-perp.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md) config
      schema (currently lines ~74–87): same additions.
- [ ] [codex] P0. [`carry-staked-basis.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md)
      config schema: same additions; document that `target_leverage = 1.0` is the typical value (LST_AS_MARGIN doesn't
      natively leverage the way funding-dispersion does, but the field is universal per `StrategyInstanceDefinition`).
- [ ] [codex] P1. Remaining archetype docs — same `target_leverage` / `target_net_delta` schema entries. Defaults can
      vary per archetype; the field is universal.
- [ ] [deployment-ui] P1. Strategy-builder form must surface `target_leverage` + `target_net_delta` fields where the
      schema declares them. **DEFERRED to deployment-ui touch**; tracker here.
- [ ] [paper-trade configs] P1. Paper-trade YAML templates need `target_leverage` field examples. **DEFERRED**.

**Gate:** All affected archetype docs have `target_leverage` + `target_net_delta` + volatility-cap clamp in their config
schemas.

---

## Stream E — Master plan + `defi_master` alignment sweep

After Streams A–D ship, the master plan + `defi_master` need a final alignment pass to reflect the corrected venue list,
the canonical `ARBITRAGE_PRICE_DISPERSION` name, and the `target_leverage` schema.

**Tasks**

- [ ] [PM-plan] P0. Edit [`master_to_live_defi_2026_05_23.plan.md`](../active/master_to_live_defi_2026_05_23.plan.md):
      replace "6 perp venues (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster)" with the corrected statement of what's
      actually live: DRIFT (Solana) + Deribit + Bybit + OKX as ETH-LST-margin-capable; Hyperliquid + Binance + Aster
      remain venues for the **`ARBITRAGE_PRICE_DISPERSION`** funding-arb hedge but not for `carry_staked_basis`
      LST_AS_MARGIN. Reword the "Both archetypes hedge on a 6-venue perp universe" claim to be precise about which
      archetype uses which subset.
- [ ] [PM-plan] P0. Edit [`defi_master_2026_05_07.plan.md`](../active/defi_master_2026_05_07.plan.md): same precision
      pass — venue list is no longer monolithic, archetypes have different venue subsets.
- [ ] [PM-plan] P1. Both plans get a "2026-05-07 venue-matrix re-verification" sub-section pointing at this plan +
      Stream A's playbook (`codex/14-playbooks/defi/venue-collateral-2026-05-07.md`).

**Gate:** Master plan + `defi_master` use precise venue subsets per archetype; no remaining "6 venues"
overgeneralisation.

---

## Success criteria (whole plan)

- [ ] Stream A: UAC matrix flipped + tests pass + codex venue table updated
- [ ] Stream B: All references to `leveraged_funding_arb` as a standalone archetype gone (except historical references
      in the issue file + this plan)
- [ ] Stream C: All 11 archetype docs reference `LegController.update`; no "hand-built" without a deferred-backport flag
- [ ] Stream D: All affected archetype config schemas have `target_leverage` + `target_net_delta` + vol-cap clamp
- [ ] Stream E: Master plan + `defi_master` use precise venue subsets per archetype
- [ ] Cross-cutting: PM `quality-gates.sh` passes; UAC `quality-gates.sh` passes (Stream A); codex links resolve;
      doc/plan/code triad in sync per the workspace rule

## Temporary states + their canonical follow-up plans

- **Stream A** ships SSOT correction + new tests; the actual catalog regeneration is design-determined (on import, per
  `_build_carry_staked_basis`) so no separate code task. **Successor:** none needed if regeneration verified.
- **Stream B** ships docs/plans/UAC enum-check; strategy-service catalog rows + tracer scripts + P&L attribution rows
  are deferred. **Successor:** to be opened when strategy-service touches funding-dispersion-leveraged. If not opened by
  2026-05-15, escalate.
- **Stream C** ships codex doc rewrites; the LeveragedLegController **code backport** to 11 archetypes is the archived
  plan's Phase 4. **Successor:** the archived plan re-opens for code-backport work as needed.
- **Stream D** ships codex schema entries; deployment-UI form-field surface + paper-trade YAML templates are deferred.
  **Successor:** opened when deployment-ui or strategy-service touches paper-trade configs. If not opened by 2026-05-15,
  escalate.
- **Stream E** ships master-plan / defi*master alignment; Phase 7a venue-matrix audit follow-throughs (live-venue
  monitoring + automated verification) are deferred to a separate plan. **Successor:** open
  `defi_venue_matrix_continuous_audit_2026_05*<date>.plan.md` when the operator decides cadence (suggested: monthly).
