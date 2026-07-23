---
doc_type: issue
title: DeFi archetypes — doc ↔ plan drift (carry_staked_basis + leveraged_funding_arb)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-07
author: harsh
source:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/defi_master_2026_05_07.md,
    plans/archive/carry_staked_basis_structure_axis_2026_05_04.md,
    plans/archive/leveraged_leg_controller_2026_05_01.md,
    plans/archive/defi_pipeline_extension_2026_05_01.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    /codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

# DeFi archetypes — doc ↔ plan drift

> **Cross-ref 2026-05-07:** Separate from this archetype-canonicalisation drift, the rollup-vs-drilldown data-status
> denominator gap closure shipped in parallel via writegate Phase 3.D.4 expected-universe `--apply-write` on all 5
> asset_groups + consolidator merge landed (PM@79e47874 + PM@341bb285): 1,455,901 rows written + merged into canonical
> (tradfi 35,033 + sports 13,176 + cefi 119,152 + prediction 2,280 + defi 1,286,260; cefi + prediction now real impl per
> UAC@ac218dc + instruments-service@d1c9928, no longer stubbed). Consolidator P0 briefly blocked tradfi / defi /
> prediction merge; resolved at PM@341bb285. Detail in
> [`../writegate_honest_coverage_endtoend_2026_05_06.md`](../writegate_honest_coverage_endtoend_2026_05_06.md) § Phase
> 3.D.4. The archetype-canonicalisation streams below (5 streams) are NOT blocked by the data-status work and proceed in
> parallel.

Cross-checked the May-23 cutover archetypes (`carry_staked_basis` + `leveraged_funding_arb`) between the master/umbrella
plans and the codex archetype docs. **Concept is aligned, several mechanics are not.** Three contradictions are
launch-blocking; two are forward-drift (plans ahead of docs, expected per the SSOT pattern but the doc updates haven't
shipped). Raising before code starts in the affected area, per the master plan's "doc → plan → code, drift is
review-blocking" rule.

---

## Issue #1 (BLOCKER) — DRIFT (Solana) is the only live venue for `carry_staked_basis` but is not in the master plan's "6 perp venues live" list

**Severity:** P0 — affects whether the lead archetype can launch May 23 at all.

**Evidence:**

- [`master_to_live_defi_2026_05_23.md`](../master_to_live_defi_2026_05_23.md) headline: _"Both archetypes hedge on a
  6-venue perp universe spanning CeFi (Bybit, Deribit, Binance, OKX) and DeFi perp DEXs (Hyperliquid, Aster) — all six
  must be live."_
- [`defi_master_2026_05_07.md`](../defi_master_2026_05_07.md): _"2 DeFi perp DEXs live: Hyperliquid + Aster"_. No
  mention of DRIFT.
- [`carry-staked-basis.md:103-112`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md#L103):
  HYPERLIQUID, BINANCE, BYBIT, OKX, DERIBIT, ASTER, GMX **all explicit `accepted=False`**. Only DRIFT accepts an LST as
  cross-margin.
- [`carry-staked-basis.md:110-112`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md#L110): _"Today's
  slot count = 2: `CARRY_STAKED_BASIS@jito-drift-f100-usdc-1h-usdc-v2-prod` +
  `CARRY_STAKED_BASIS@marinade-drift-f100-usdc-1h-usdc-v2-prod`. Honest — DRIFT is the only venue that accepts an LST as
  cross-margin in production today."_

**Why it matters:** the firm rule (post-2026-05-05) is _slot rejected at preflight if the LST is not accepted as direct
cross-margin at the perp venue_ — no SPLIT_STAKE fallback, no COLLATERAL_BORROW fallback. So `carry_staked_basis` cannot
hedge on any of the 6 named perp venues today. The only realisable slots run on **DRIFT (Solana)**, which neither the
master plan nor `defi_master` lists as a venue going live.

**Two possible resolutions, pick one:**

1. **Add DRIFT as a 7th perp venue going live by May 23.** Implies instrument-registry / market-data / execution
   connector / position-balance-monitor coverage for DRIFT. Tightens the Pyth-Solana-oracle dependency further (jitoSOL
   / mSOL price reads).
2. **Phase 7a venue-matrix audit makes one of the existing 6 venues accept an ETH LST.** Codex
   [`carry-staked-basis.md:114-120`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md#L114) says this
   is a per-venue verification with haircut citations — not done today. Aevo / Lyra-V2 / Hyperliquid candidate list per
   the doc.

Either way, the master plan + defi_master need to surface this dependency. Today they do not.

---

## Issue #2 (BLOCKER) — Plan-shipped catalog (22 slots, `f ∈ {0.5, 0.75}`) contradicts codex (2 slots, `f = 1.0`)

**Severity:** P0 — the actual code emits one of these; the other plan/doc is stale.

**Evidence:**

- [`carry_staked_basis_structure_axis_2026_05_04.md`](../../archive/carry_staked_basis_structure_axis_2026_05_04.md)
  Phase 3a-catalog-regenerate (status: done, strategy-service `7074eee`): _"22 slots: 3 ETH-LST × 3 ETH-perp
  (HYPERLIQUID/DERIBIT/ASTER) × f∈{0.5,0.75} + 2 SOL-LST × HYPERLIQUID × f∈{0.5,0.75}"_. Phase 3b bumped catalog ceiling
  260 → 280.
- [`carry-staked-basis.md:52-54`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md#L52):
  _"`stake_fraction` = `1.0` is the only meaningful value: the LST IS the perp margin, there is no spare USDC bucket.
  The f-grid was a SPLIT_STAKE-era artefact and was retired with the deletion."_ Slot label is `f100`.
- [`carry-staked-basis.md:124-130`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md#L124): _"`f` is
  fixed at `100` (= 1.0) because LST_AS_MARGIN is the only allowed structure."_

**Why it matters:** the codex was updated **after** the plan's Phase 3a shipped, reflecting the
post-SPLIT_STAKE-deletion state. If Phase 3a's 22-slot catalog actually shipped to
[`strategy-service/.../target_universe/catalog.py`](../../../../strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py)
`_build_carry_staked_basis`, the live code is emitting slots the codex says shouldn't exist (f=0.5/0.75 is conceptually
SPLIT_STAKE, which is deleted).

**Action:** read `_build_carry_staked_basis` and confirm what ships today. Whichever wins, the other side must update —
the plan was archived 2026-05-07, so the codex is the live SSOT and the plan's archive copy needs an `OBSOLETED-BY:`
note pointing at the codex doc.

---

## Issue #3 (BLOCKER) — `leveraged_funding_arb` is named in plans but is not a codex archetype

**Severity:** P0 — second cutover archetype has no canonical identity.

**Evidence:**

- [`master_to_live_defi_2026_05_23.md`](../master_to_live_defi_2026_05_23.md): names the second DeFi archetype
  `leveraged_funding_arb` — _"cross-venue funding-rate spread trade"_.
- [`defi_master_2026_05_07.md`](../defi_master_2026_05_07.md): _"2 DeFi archetypes live: `carry_staked_basis` +
  `leveraged_funding_arb`"_.
- [`codex/09-strategy/architecture-v2/archetypes/`](../../../codex/09-strategy/architecture-v2/archetypes/) directory
  has 25 archetype docs. **No file named `leveraged-funding-arb.md`. No archetype named `LEVERAGED_FUNDING_ARB` in
  `StrategyArchetype` enum.**
- [`defi_pipeline_extension_2026_05_01.md`](../../archive/defi_pipeline_extension_2026_05_01.md) names the engine: _"the
  9.34% Hyperliquid BTC short × 3 CeFi long book in `ArbitragePriceDispersionHierarchicalEngine`"_ — i.e. the engine
  actually lives under `ARBITRAGE_PRICE_DISPERSION`.

**Codex internal contradiction (independent of plans):**

- [`arbitrage-price-dispersion.md:81`](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md#L81)
  "Supported scenarios" includes _"Funding-rate dispersion arb | LEADER_HEDGE"_.
- [`arbitrage-price-dispersion.md:179`](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md#L179)
  "Not in this archetype": _"Funding-rate arbitrage between perp venues — `CARRY_BASIS_PERP` (cross-venue mode)"_.
- [`carry-basis-perp.md:144`](/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md#L144) "Not in this
  archetype": _"Cross-venue perp spread arbitrage (funding-rate differential between two perp venues for the same asset)
  — `ARBITRAGE_PRICE_DISPERSION`"_.

Each codex doc points at the other for cross-venue funding arb. Circular, contradictory.

**Why it matters:** the second cutover archetype has no clear engine, no clear config schema, no clear catalog entry
shape, no rank allocator subclass, and no archetype doc. Tracer scripts, batch=live verification, P&L attribution rows,
deployment-UI surfaces — all of these key off `StrategyArchetype` enum values.

**Action:**

1. Pick a canonical name. Likely `ARBITRAGE_PRICE_DISPERSION` with a leveraged-funding-dispersion configuration variant
   (since the engine is `ArbitragePriceDispersionHierarchicalEngine`), OR introduce a new
   `StrategyArchetype.LEVERAGED_FUNDING_ARB` enum value with its own engine.
2. Resolve the circular cross-reference between `arbitrage-price-dispersion.md` and `carry-basis-perp.md` "Not in this
   archetype" sections.
3. Open a codex archetype doc at the canonical path (or extend the existing one's "Supported scenarios" with a leveraged
   variant + config schema).
4. Update master plan + defi_master to use the canonical name.

---

## Issue #4 (drift, P1) — `LeveragedLegController` is plan-only; archetype docs describe legs as hand-built

**Severity:** P1 — forward-drift (plans ahead of docs is the workspace pattern), but Phase 4 backport gates require the
codex updates.

**Evidence:**

- [`leveraged_leg_controller_2026_05_01.md`](../../archive/leveraged_leg_controller_2026_05_01.md) introduces a generic
  delta-targeted multi-leg primitive. Phase 4 lists 11 strategy backports — `staked_basis.py`, `recursive_staked.py`,
  `basis_perp.py`, `price_dispersion.py`, `ml_directional/continuous.py`, etc. — replacing every bespoke `_build_legs`
  with `LegController.update`.
- Codex archetype docs do not mention the controller. They describe legs archetype-specifically:
  - [`carry-staked-basis.md:36-50`](/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md#L36): 4-leg
    `LST_AS_MARGIN` sequence presented as hand-built
  - [`carry-basis-perp.md:30-49`](/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md#L30): 2-leg paired
    entry/exit, hand-built
  - [`arbitrage-price-dispersion.md:38-63`](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md#L38):
    ATOMIC / LEADER_HEDGE modes, no controller layer

**Why it matters:** when Phase 4 backports ship and `_build_legs` is replaced by `LegController.update`, the archetype
docs become misleading for new engineers. The plan's Phase 4 GATE only checks parity tests + quality-gates — not the
codex doc edits. Per master plan's "doc → plan → code" rule, the codex updates should ship in the same PR as the
backport.

**Action:** add Phase 4.x sub-todos to the LeveragedLegController plan: edit each archetype doc's "Token / position
flow" + "Execution semantics" sections to reference the controller; keep the archetype-specific math (target_leverage
derivation, target_net_delta source) in the doc, drop the hand-built leg-listing.

---

## Issue #5 (drift, P1) — `target_leverage` is in plans but not in codex config schemas

**Severity:** P1 — forward-drift, blocks the Issue #3 resolution if `leveraged_funding_arb` becomes a leveraged variant
of an existing archetype.

**Evidence:**

- [`defi_pipeline_extension_2026_05_01.md`](../../archive/defi_pipeline_extension_2026_05_01.md): cross-venue funding
  arb runs at `target_leverage=1.0` today; at 3x = 18% net spread. Adds `MaxUnderlyingMove` +
  `INSTRUMENT_VOLATILITY_REGISTRY` primitive to clamp per-instrument.
- [`leveraged_leg_controller_2026_05_01.md`](../../archive/leveraged_leg_controller_2026_05_01.md) Phase 1.2: _"Promote
  target_leverage from per-archetype configs to StrategyInstanceDefinition"_.
- [`arbitrage-price-dispersion.md:84-105`](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md#L84)
  config schema has **no `target_leverage` field** — only `max_capital_per_opp_pct: 0.05`.
- [`carry-basis-perp.md:74-87`](/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md#L74) config schema
  also has no leverage field; uses `max_allocated_equity_pct: 0.30`.

**Why it matters:** the leverage layer is the entire alpha multiplier on `leveraged_funding_arb` (6% → 18% net at 3x).
Without `target_leverage` in the config schema and codex docs, deployment-UI strategy builders, paper-trade configs, and
operator runbooks have no surface to set it.

**Action:** when Issue #4 backport lands, also extend the affected archetype docs' config schemas with `target_leverage`

- `target_net_delta` fields, plus the volatility-cap clamp behaviour.

---

## Where the docs and plans align (for completeness)

These were checked and are consistent:

- Strategy concept: long LST + short perp on same coin, market-neutral, USDC share class
- Structure rule: `LST_AS_MARGIN` is the only allowed path post-2026-05-05; SPLIT_STAKE + COLLATERAL_BORROW deleted
- Eligibility: `VENUE_COLLATERAL_MATRIX` is SSOT;
  [`venue_collateral.py`](../../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py)
  `venue_accepts_collateral` query at preflight
- Truth source: on-chain APY from MTDS `lst_rates` rate-diff `(rate[t]/rate[t-1])^365 − 1`. NOT DefiLlama vendor APY.
  Live engine + tracer both consume this (per Phase 4a-5 calculator refactor at features-onchain `b1245b1`)
- Execution flow: `SWAP → STAKE → TRANSFER → TRADE`, `LEADER_HEDGE` mode, `CLOSE_LEADER_IF_HEDGE_FAILS` compensation,
  `hedge_deadline_ms: 5000`
- Risk: `min_health_factor: 1.25` gates the perp short, depeg + funding-flip kill switches, smart-contract risk reduced
  vs deleted COLLATERAL_BORROW path
- P&L attribution: 4-row decomposition (staked_principal + perp_short + transfer + spot_conversion)
- Tracer: [`scripts/trace_carry_staked_basis.py`](../../../../strategy-service/scripts/trace_carry_staked_basis.py) +
  parquet output schema match exactly between plan Phase 4a and codex `carry-staked-basis.md` "Tracer protocol"
- Lifecycle: PBMS + R&E + pnl-attribution all wired; matching engine in batch (batch=live)
- Rank allocator: `BaseRankAllocator` + per-archetype subclass pattern (Phase 8 of carry_staked_basis plan matches codex
  `carry-staked-basis.md` "Per-archetype rank allocator" section)

---

## Summary table

| #   | Severity   | Topic                                         | Plan says                                              | Codex says                                                                            | Resolution owner                         |
| --- | ---------- | --------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------- | ---------------------------------------- |
| 1   | BLOCKER    | Live perp venue list for `carry_staked_basis` | 6 venues (Bybit/Deribit/Binance/OKX/Hyperliquid/Aster) | Only DRIFT (Solana) accepts LST as margin today                                       | Master-plan owner (Ikenna)               |
| 2   | BLOCKER    | `stake_fraction` grid + slot count            | `f ∈ {0.5, 0.75}`, 22 slots                            | `f = 1.0` only, 2 slots                                                               | Whoever owns `_build_carry_staked_basis` |
| 3   | BLOCKER    | `leveraged_funding_arb` archetype identity    | Named archetype going live May 23                      | No codex archetype with that name; codex internally circular on funding arb ownership | Strategy-architecture owner              |
| 4   | DRIFT (P1) | `LeveragedLegController` in archetype docs    | Generic primitive, 11-archetype backport               | Archetype docs describe legs as hand-built                                            | LeveragedLegController plan Phase 4      |
| 5   | DRIFT (P1) | `target_leverage` in config schemas           | Promoted to `StrategyInstanceDefinition`               | Not in any archetype's config schema                                                  | LeveragedLegController plan Phase 1.2    |

---

## Suggested next steps (for triage call)

1. **Issues #1–#3 must be resolved before any code change in the affected area** — doc/plan/code drift is
   review-blocking per the master plan's SSOT rule.
2. **Issue #1** is the highest-leverage call: either DRIFT joins the venue-go-live list (and Pyth-Solana wiring becomes
   even more critical) or Phase 7a venue-matrix audit lands one of the existing 6 venues with LST collateral support
   before May 23. Affects critical-path DAG.
3. **Issue #2** is a 30-minute investigation: read `_build_carry_staked_basis` in
   [`strategy-service/.../target_universe/catalog.py`](../../../../strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py)
   and confirm what ships. Update the losing side.
4. **Issue #3** needs a strategy-architecture decision: enum-extend vs config-variant. Either way, an archetype doc must
   exist by May 13 (Week 2 start) for the second-archetype work to begin.
5. **Issues #4 + #5** can ship as part of the LeveragedLegController plan's Phase 4 backport — add codex doc edits to
   each Phase 4.x sub-todo's GATE.

---

## 2026-05-07 PM follow-up — operator review + venue-matrix re-verification (Claude session)

**This section supersedes the original Issues #1, #3, #4, #5 wording above where it conflicts. Issue #2 stands as
written.** Operator (Ikenna) reviewed the audit on 2026-05-07; below captures (a) the corrected understanding of which
venues actually accept ETH LSTs as cross-margin today (`venue_collateral.py` SSOT is stale), (b) operator confirmations
on the canonical-name + leverage decisions, and (c) the named successor plan that holds the actionable todos.

### Issue #1 — REFRAMED: SSOT is stale, not the conclusion

The original audit relied on `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py` which carries
explicit `accepted=False` rows for stETH/wstETH on every named venue, with a comment dated 2026-05-05: _"NO production
ETH-perp venue accepts an ETH LST as direct cross-margin today."_ **Re-verified 2026-05-07 against live venue docs and
this is wrong:**

- **DERIBIT** — stETH IS accepted as cross-collateral with a **7.5% haircut** (reduced from 15% on
  [2026-01-13](https://insights.deribit.com/exchange-updates/portfolio-margin-improvements-for-steth-and-cross-collateral-haircuts/)).
  stETH is grouped within ETH's bucket in the Extended Risk Matrix; **stETH holdings can directly offset ETH derivative
  positions** (i.e. margin an ETH-PERP short). Applies to X:PM (cross-collateral portfolio margin) and X:SM accounts;
  S:PM (segregated PM) is unaffected.
- **BYBIT** — stETH and METH have been UTA-collateral-eligible since
  [Feb 2024](https://announcements.bybit.com/article/collateral-value-ratio-adjustments-for-steth-and-meth-blt8fc7ba628f15dd27/);
  USDe since
  [Dec 2024](https://announcements.bybit.com/article/collateral-value-ratio-adjustments-for-usde-blt093009fa8ea0dacc/).
  Bybit UTA supports 70+ assets as cross-collateral; LST-as-perp-margin works with the published collateral value ratio.
- **OKX** — wstETH is on the multi-currency-margin / portfolio-margin discount-rate list (per OKX help-center
  cross-margin docs); confirmation of haircut pending live API probe.
- **BINANCE** — Multi-Assets Mode currently lists `BTC / ETH / BNB / XRP / ADA / DOT / SOL / USDC / USDT` only with
  5–10% haircuts. **No LST support today** in Multi-Assets Mode (cross-collateral feature was retired). This venue
  remains unsuitable for `carry_staked_basis` LST_AS_MARGIN.
- **HYPERLIQUID** — main L1 still USDC-only (correct in SSOT). HIP-3 builder-deployed perp DEXes can use USDe / BTC /
  ETH / etc. as their quote/collateral asset; not relevant to the L1 perp short hedge.
- **ASTER** — USDT / USDF / asBNB only; no ETH LSTs.
- **DRIFT** — JitoSOL / mSOL accepted with 10% haircut (correct in SSOT, already shipping 2 catalog rows).

**Net implication.** `carry_staked_basis` can launch on **DRIFT (Solana) + Deribit + Bybit + OKX** as of today, NOT just
DRIFT. The "6 perp venues" master-plan list is partly wrong (Binance and Aster don't accept ETH LSTs; Hyperliquid L1
doesn't), but the strategy is **NOT venue-blocked** the way Issue #1 claimed. Phase 7a venue-matrix audit is real work
that needs doing — but as a SSOT correction, not as a launch-gating dependency.

**Resolution owner:** UAC `venue_collateral.py` SSOT correction + codex `carry-staked-basis.md` venue table update.
Tracked in the new plan named below.

### Issue #2 — CONFIRMED CORRECT (operator 2026-05-07)

Codex is right: `f = 1.0` only, **2 slots** (DRIFT/JitoSOL + DRIFT/mSOL today; expanding to Deribit/Bybit/OKX once Issue
#1 SSOT correction lands). The 22-slot version was a SPLIT_STAKE-era artefact that was retired with the deletion.
Whichever side of the code is still emitting 22 slots needs trimming.

### Issue #3 — RESOLVED: it's `ARBITRAGE_PRICE_DISPERSION` (operator 2026-05-07)

Operator decision: `leveraged_funding_arb` is **a configuration variant of `ARBITRAGE_PRICE_DISPERSION`**, not a new
archetype. Reasoning: funding-rate spread IS the price dispersion in this case (cross-venue funding = cross-venue
forward-pricing differential), and leverage is an orthogonal axis applicable to any arbitrage strategy (scaled via
`target_leverage` per Drift P1 #5). The engine `ArbitragePriceDispersionHierarchicalEngine` already exists and supports
the LEADER_HEDGE mode that funding arb requires.

**Action to align docs / plans / code:**

- Codex `arbitrage-price-dispersion.md` — make "Funding-rate dispersion arb | LEADER_HEDGE" a first-class supported
  scenario with its own config-schema variant (not a one-line mention). Resolve the circular cross-reference with
  `carry-basis-perp.md` by removing the "Not in this archetype" line that points outward, leaving the paired claim in
  `carry-basis-perp.md` only.
- Codex `carry-basis-perp.md` — keep its "Not in this archetype: cross-venue funding arb → `ARBITRAGE_PRICE_DISPERSION`"
  line; that becomes authoritative.
- Master plan + `defi_master_2026_05_07.md` — rename `leveraged_funding_arb` → `ARBITRAGE_PRICE_DISPERSION` (with a
  config-variant suffix where useful, e.g. `ARBITRAGE_PRICE_DISPERSION@funding-dispersion-leveraged`).
- Strategy-service catalog — confirm `_build_arbitrage_price_dispersion` (or equivalent) emits the
  funding-dispersion-leveraged slots; if not, add the config-variant rows.

### Drift P1 #4 — CONFIRMED: codex updates to align with LeveragedLegController (operator 2026-05-07)

Codex archetype docs (`carry-staked-basis.md`, `carry-basis-perp.md`, `arbitrage-price-dispersion.md`,
`recursive-staked.md`, etc.) need their "Token / position flow" + "Execution semantics" sections rewritten to reference
`LegController.update` instead of bespoke `_build_legs`. Archetype-specific math (`target_leverage` derivation,
`target_net_delta` source) stays in the doc; the hand-built leg-listing goes. Even if the code backports defer, the docs
ship now to keep doc/plan/code in sync per the workspace rule.

### Drift P1 #5 — CONFIRMED: extend archetype config schemas (operator 2026-05-07)

Add `target_leverage` + `target_net_delta` + the volatility-cap clamp behaviour to the affected archetype docs' config
schemas. Without these, deployment-UI strategy builders, paper-trade configs, and operator runbooks have no surface to
set leverage. Schemas to extend: `arbitrage-price-dispersion.md`, `carry-basis-perp.md`, plus any other archetype that
uses leverage (i.e. all of them, since `LeveragedLegController` is workspace-wide).

### Named successor plan

Actionable todos for all of the above tracked in:
[`plans/ai/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](../../ai/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md).

Plan covers four parallel streams:

1. **Stream A — venue_collateral.py SSOT correction** (UAC) — live API verification of Deribit / Bybit / OKX LST
   collateral haircuts → patch matrix entries → update codex venue table.
2. **Stream B — `leveraged_funding_arb` → `ARBITRAGE_PRICE_DISPERSION` canonicalisation** (UAC + codex + plans
   - strategy-service) — rename across all surfaces, codex doc rewrite, catalog rows.
3. **Stream C — LeveragedLegController codex doc backport** (codex archetypes/) — rewrite leg-flow sections in 11
   archetype docs even when the code backport defers.
4. **Stream D — `target_leverage` / `target_net_delta` config schema extensions** (codex archetypes/) — extend
   config-schema sections, paired with deployment-UI form-field surface.
