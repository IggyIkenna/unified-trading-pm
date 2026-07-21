---
doc_type: plan
title: DeFi recursive-borrow archetypes — leveraged lending arb + long-funding-perp recursive-borrow flavor
summary:
status: closed-spawned-plan
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/defi_recursive_borrow_archetypes_2026_05_10.md,
    plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md,
    plans/active/defi_master_2026_05_07.md,
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/issues/defi_archetypes_doc_plan_drift_2026_05_07.md,
  ]
created: 2026-05-08
type: question-doc
closed: 2026-05-10
author: ikenna
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
related_codex:
  [
    codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md,
    codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md,
    codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md,
    codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md,
    codex/09-strategy/strategy-summary.md,
  ]
spawned_plan: plans/active/defi_recursive_borrow_archetypes_2026_05_10.md
---

## Deferred work — migrated to: **None** — successor: not applicable. This is a question-doc (`status:

closed-spawned-plan`) whose open items were a pre-implementation checklist, not standing work — the frontmatter's own `spawned_plan:
plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`already names the real successor (the regex just didn't recognize the`spawned_plan:`key as a successor token). Traced the full chain: that spawned plan (now at`plans/archive/2026_05/defi_recursive_borrow_archetypes_2026_05_10.md`) itself has ZERO open items and its own `successor_plan:
plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md`(now at`plans/archive/2026_05/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md`) also has ZERO open items, `status:
complete`. Both descendants confirm the recursive-borrow archetype work (Family 1 leveraged lending arb + Family 2
long-funding-perp recursive-borrow) shipped in full — no live successor plan is needed for this question-doc's 35
checklist items.

# DeFi recursive-borrow archetypes — leveraged lending arb + long-funding-perp recursive-borrow flavor

## Intent

Two recursive-borrow strategy families sit half-stated in the workspace and need to be either (a) canonicalised as
derivations of existing archetypes (`CARRY_STAKED_BASIS`, `ARBITRAGE_PRICE_DISPERSION`, `CARRY_BASIS_PERP`) or (b)
declared as new archetypes with proper UAC enums + strategy-service factories + codex docs. We don't yet have the
flow-of-funds matrix, the share-class abstraction story, the per-venue feasibility map, or the cross-venue accounting
shape pinned down. This doc captures the questions before we start drafting plans.

**Family 1 — DeFi leveraged lending arb (pure-lending, no perp leg).** Borrow recursively against your own collateral to
amplify the rate spread between supply APY and borrow APY. Four orthogonal dimensions: same-coin vs different-coin,
same-venue vs different-venue. Effective leverage comes from the fact that the loop's collateral always exceeds the debt
by the LTV cushion, so you compound the spread on each turn until LTV / health-factor binds.

**Family 2 — Long-funding-perp recursive-borrow (delta-neutral, share class = underlying coin).** Hold spot coin (e.g.
ETH) as collateral, borrow more of the same coin against it, short on perps to capture funding, recursively
re-collateralise the borrowed coin into more spot, borrow more, short more. Delta-neutral on the share class (you "hold
N ETH" net). PnL = funding income on the perp short minus borrow rate on the lending leg minus liquidation insurance
buffer cost.

Both families need: an audit pass against existing archetypes (do they already cover these, or partially?), a
flow-of-funds diagram per dimension combination, a viability call per (coin × venue × chain), and a decision on
derivation vs new archetype. Web research + rate-sampling across protocols (Aave V3 / Compound V3 / Spark / Morpho /
Maker DSR / Lido / Pendle / Hyperliquid / Bybit / Binance / OKX / Deribit / Aster) is allowed and expected.

**Bias.** Prefer derivations over new archetypes if the existing archetype shape genuinely covers the strategy mechanics
(per the 2026-05-07 operator decision that `leveraged_funding_arb` is a config variant of `ARBITRAGE_PRICE_DISPERSION`,
not a new archetype). New archetypes are justified only when share-class semantics, leg structure, or kill-switch
surface materially diverges.

## Question

### Block A — Existing archetype audit (before we add anything)

- [ ] A1. Enumerate every DeFi-touching archetype currently in UAC + strategy-service + codex. Known so far:
      `CARRY_STAKED_BASIS`, `ARBITRAGE_PRICE_DISPERSION` (with `leveraged_funding_arb` as a config variant per
      2026-05-07), `CARRY_BASIS_PERP`. Anything else? Anything in flight in
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](../active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      not yet ratified?
- [ ] A2. Of those archetypes, which already involve **recursive borrowing** (loop the collateral → debt → re-supply →
      borrow chain)? `CARRY_STAKED_BASIS` ETH leg uses Aave supply + LST yield but I don't think it loops; confirm.
- [ ] A3. Which already cross venues for the lending vs hedging legs? `CARRY_STAKED_BASIS` does (Aave on EVM + perp
      hedge on a CeFi venue). Are there pure on-chain cross-venue archetypes (e.g. supply on Aave, borrow on Compound,
      arb the rate)?
- [ ] A4. Share-class abstraction in current archetypes — are they parameterised by underlying coin / coin group, or
      hard-coded to specific symbols? `LeveragedLegController` exists per the canonicalisation plan; does it already
      abstract share class, or just leverage / net-delta targets?
- [ ] A5. Audit findings dump — for each existing archetype, summarise its leg structure, share-class semantics,
      kill-switch surface, batch=live symmetry status. This is the baseline against which we decide derivation vs new.

### Block B — Family 1: DeFi leveraged lending arb (recursive borrow, pure lending)

- [ ] B1. **Same coin, same venue.** Supply USDC on Aave V3 → borrow USDC against it → re-supply → borrow … . Net carry
      = (supply*APY - borrow_APY) × leverage_factor, where leverage = 1 / (1 - LTV) at the loop limit. On most
      same-asset same-venue pairs this spread is \_negative* (borrow > supply) — when is it ever positive? E-mode for
      correlated assets? Incentive emissions (rewards token boosts supply APY above borrow APY)? Rate-curve kinks during
      utilisation spikes? List the regimes where this is profitable, not theoretical.
- [ ] B2. **Different coin, same venue.** Supply ETH → borrow USDC → swap USDC to ETH → re-supply → borrow USDC …
      (recursive levered ETH long via stablecoin debt). Or the inverse: supply USDC → borrow ETH → short / sell ETH for
      USDC → re-supply (recursive ETH short via collateral debt). Both are duration / direction trades on ETH-USDC, not
      pure carry. Where's the arb? Is the arb the rate differential between two correlated assets (e.g. supply stETH,
      borrow ETH on a non-LSD-aware venue, capture LST spread)? E-mode (Aave V3) materially shifts this — does our spec
      account for e-mode max-LTV explicitly?
- [ ] B3. **Same coin, different venue.** Supply USDC on Aave → borrow USDC on Compound (would require flash-loan or
      cross-venue collateral migration since you can't post Aave-supplied USDC as Compound collateral directly). When is
      the rate-arb spread big enough to overcome bridging / gas / flash-fee cost? Is this a flash-loan-only opportunity
      per opening, or can it be held?
- [ ] B4. **Different coin, different venue.** Multi-hop flow of funds. Practical at all, or always dominated by
      single-venue B2 / same-venue cross-asset variants?
- [ ] B5. **Health-factor / LTV binding constraint.** What's the recursion depth limit? E-mode pushes max-LTV ~93% for
      correlated pairs, giving ~14× leverage at the loop limit. Non-e-mode is ~75% LTV → ~4× leverage. Does the
      archetype config expose recursion depth + safety buffer as parameters?
- [ ] B6. **Flash-loan-based opening vs persistent recursive position.** Aave V3 flash-loan → open the entire recursive
      position atomically → close atomically when spread compresses. Vs holding the position open across blocks.
      Different risk surfaces (flash = atomic but pays flash fee; persistent = no fee but liquidation risk). Does either
      map to existing `CARRY_STAKED_BASIS` open / close mechanics, or is it a new orchestration pattern?
- [ ] B7. **Liquidation surface.** What triggers liquidation in each B1-B4 variant? Oracle deviation? Rate spike? Flash
      crash on the borrow asset? How does the kill-switch tier-up integrate (per
      `alerting_service_live_rules_2026_05_07.md`)? Per-venue tolerances (Aave V3 oracle freshness vs Compound V3 vs
      Morpho)?
- [ ] B8. **Web-research input.** Sample current rates across {Aave V3 ETH/Arb/Base/Polygon/OP, Compound V3
      ETH/Arb/Base, Spark, Morpho Blue, Maker DSR} for {USDC, USDT, ETH, stETH, wstETH, weETH, BTC, wBTC} — produce a
      current-spread matrix and flag the (coin, venue) combinations where the spread is wide enough to justify a
      recursive position after gas + flash-fee + LTV haircut. Use the web tool.

### Block C — Family 2: Long-funding-perp recursive-borrow (delta-neutral, share class = underlying)

- [ ] C1. **Base archetype (non-recursive) — does it already exist?** Spot ETH long (held on-chain or in custody) +
      short ETH-PERP funded against funding > 0. PnL = funding rate. Is this already covered by `CARRY_BASIS_PERP` or by
      `ARBITRAGE_PRICE_DISPERSION` as a funding-spread variant? If so, the recursive-borrow flavor is a derivation; if
      not, the base case is also missing.
- [ ] C2. **Recursive-borrow flavor flow.** Hold N spot ETH → supply on Aave as collateral → borrow ~LTV × N ETH → short
      the borrowed ETH on a perp venue (Hyperliquid / Bybit / Binance / OKX / Deribit / Aster) → use the perp short
      margin from the proceeds (if any) or from set-aside USDC → loop: re-supply the spot ETH from … wait, that's the
      question. Does the loop work at all if you can't re-collateralise the borrowed ETH back into the lending pool
      without changing your net spot position? Walk the flow of funds step-by-step and verify it's actually achievable
      on-chain.
- [ ] C3. **Delta neutrality math.** Spot ETH long = +1 × N. Aave supply maintains the +1 × N exposure (supplied ETH is
      still ETH-denominated). Borrowed ETH is -1 × (LTV × N) on the lending side. Perp short captures funding on -1 ×
      (LTV × N) notional. Net delta = N - (LTV × N) + 0 (perp is delta-neutral by construction once shorted at spot
      reference) = N × (1 - LTV). Wait — the recursive flavor is supposed to be delta-neutral on the **share class**,
      not zero-delta on the world. Confirm: share class is ETH; user "holds 1 ETH" and earns ETH-denominated yield =
      funding
  - borrow_rate. So we don't want zero net delta in USD — we want zero delta vs share class. Is this distinction
    documented anywhere?
- [ ] C4. **Cross-venue accounting.** Collateral on Aave (Ethereum / Arb / Base), perp on a CeFi venue (Bybit etc.).
      Margin posting to the perp venue requires moving USDC or USD-denominated value into the venue. How is the
      cross-cloud / cross-venue position aggregated? `position-balance-monitor-service` already handles cross-venue;
      does it correctly net out the on-chain Aave debt against the off-chain perp short for share-class accounting?
- [ ] C5. **Recursion mechanics.** Each loop iteration: borrow more ETH → short more on perp → use proceeds (USDC) to
      buy more spot ETH → supply on Aave → repeat. The recursion is on the _spot quantity_, not on the lending pool
      position. Confirm that's the right framing. The leverage ladder is bounded by Aave health-factor as in B5.
- [ ] C6. **Funding sign-flip risk.** When funding goes negative, the strategy bleeds (paying funding on the short while
      still paying borrow rate on the loan). What's the unwind discipline? Threshold-based exit per
      `LeveragedLegController` target_net_delta? Continuous monitoring vs periodic rebalance?
- [ ] C7. **Liquidation cross-coupling.** Aave liquidation (oracle deviation, rate spike) AND perp liquidation (margin
      call, funding squeeze) are now linked: a liquidation on either leg unwinds the share-class neutrality. Does the
      kill-switch tier-up handle the cascading-liquidation case explicitly, or does it treat each leg's liquidation as
      independent?
- [ ] C8. **Coin universality.** The user wants this to work on "any coin underlying / group" as the share class. What
      constraints does that impose?
  - Lending venue must support the coin as collateral with non-zero borrow capacity.
  - Perp venue must list the coin's perpetual with sufficient depth.
  - Funding regime must be predominantly positive (longs paying shorts) at expected leverage levels.
  - LST coins (stETH, weETH) add yield-on-collateral but complicate the e-mode story.
  - List the "tradeable share-class universe" given these constraints — ETH, BTC, SOL, … ?

### Block D — Share class + archetype derivation decision

- [ ] D1. **Share class definition.** Is the share class always the coin the user effectively "holds" net (i.e. the coin
      the strategy reports its yield in)? Family 1 B2-B4 might end up share-classed in USD (stable carry) even when the
      loop touches volatile assets. Family 2 C is share-class-in-underlying-coin by construction. Does UAC have a
      `share_class` field on archetype config, or is it implicit?
- [ ] D2. **Stable share class with volatile collateral.** User wants to be USDC-share-class but uses ETH as
      recursive-borrow collateral. Does this fit `CARRY_STAKED_BASIS` (which already has stable + LST mixing) or does it
      need a new "stable-share-class-with-volatile-collateral" derivation?
- [ ] D3. **Derivation vs new archetype call.** Decision tree:
  - Family 1 (lending arb, no perp leg): does it fit `ARBITRAGE_PRICE_DISPERSION` (the price-dispersion is the
    rate-dispersion) or `CARRY_STAKED_BASIS` (carry on collateral)? Or neither?
  - Family 2 (long-funding-perp recursive): does it fit `CARRY_BASIS_PERP` (with leveraged-leg controller turned up) or
    `ARBITRAGE_PRICE_DISPERSION` (funding-spread variant)? Or neither?
  - The 2026-05-07 operator decision that `leveraged_funding_arb` = `ARBITRAGE_PRICE_DISPERSION` config variant is
    precedent. Does that precedent extend to these two families?
- [ ] D4. **Registration discipline.** If new archetype: UAC enum addition, strategy-service factory, codex doc under
      `codex/09-strategy/architecture-v2/archetypes/`, deployment-UI ArchetypeMatrix entry, target-universe catalog. If
      derivation: UAC config field addition (e.g. `recursion_depth`, `borrow_chain_axis`), strategy-service
      config-handler, codex doc section in the parent archetype, no UI shape change. Map the registration touchpoints
      per outcome.

### Block E — Research method + rate-sampling

- [ ] E1. **Existing rate coverage in MTDS.** What lending / funding rate snapshots do we already capture per protocol?
      `mtds-s3-5/6` shipped Pyth + Chainlink for spot prices. Aave V3 / Compound V3 / Spark borrow + supply rates —
      captured? Per chain? Historical depth? (Cross-reference with
      `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` lending-indices DEFERRED note.)
- [ ] E2. **Web-research scope.** Protocols not yet in MTDS — list, scope what to fetch via web (current rates + e-mode
      parameters + LTV caps per asset + recent rate-spike events). Bound the research effort to one focused pass, not
      exploratory.
- [ ] E3. **Backtest replay feasibility.** Do we have the historical lending rate + perp funding rate data to backtest
      these archetypes pre-cutover? If we don't, the May-23 cutover for Family 2 is paper-only until we backfill — flag
      as a prerequisite plan.
- [ ] E4. **Cross-instrument / cross-chain sampling.** Sample the (coin, venue, chain) cube to identify the top-N
      high-spread combinations worth implementing first. Avoid implementing all 4 dimensions of B1-B4 + C variants
      uniformly — pick the wedges with the best spread-per-implementation-cost ratio.

### Block F — Batch = live symmetry for these archetypes

- [ ] F1. **Single code path per workspace SSOT.** Per `CLAUDE.md` "Batch = Live: Unified Pipeline Architecture" these
      archetypes' strategy logic, rate-sampling, sizing, kill-switch wiring must be bit-identical between batch and live
      — only the fill source (matching engine vs real venue) and tick source (replay vs live feed) differ. Confirm the
      recursive-borrow loop simulation in batch faithfully models on-chain mechanics: gas costs, flash-loan fees, oracle
      staleness, health-factor binding, liquidation triggering.
- [ ] F2. **Matching-engine fidelity for DeFi.** Per `master_to_live_defi_2026_05_23.md` Group F item 17 (real gas /
      matching engine / cost+yield precision). Does the matching engine model recursive-borrow opening as a single
      multi-step transaction (atomic with flash-loan) or as N sequential transactions (persistent loop)? Per-step gas
      cost modelling for non-flash recursion?
- [ ] F3. **Live-only seams.** What batch-side approximations do we accept for these archetypes vs require to be
      bit-identical to live? Examples: oracle update cadence (Chainlink heartbeat, Pyth pull frequency), MEV impact on
      recursion-opening transactions, liquidator response time. List the seams + tolerance per seam.

### Block G — Risk + compliance posture

- [ ] G1. **Concentration risk.** Recursive borrow concentrates the position in one (coin, venue) pair. How does the
      risk-and-exposure-service treat the gross notional vs net delta? Should the kill switch arm earlier on recursive
      archetypes given the concentration?
- [ ] G2. **Custody story.** Where does the spot collateral live in Family 2 — Copper / CEFFU custody (per master plan
      Group F item 19) or directly held on-chain via the wallet? If custody, how does the recursive-supply step interact
      with custody withdraw discipline?
- [ ] G3. **DART manual-trade boundary.** Per master plan Group G item 23 (DART manual-trade gate), recursive-borrow
      opening is a multi-step transaction sequence — does it enter as one DART instruction (atomic intent) or N
      instructions (per-step)? Default discipline?

## What we want out of this Q-group

A draft plan (or set of plans) that:

1. **Audit pass** completes Block A with concrete archetype-by-archetype findings (1-2 days, parallelisable across 3-4
   archetypes).
2. **Decision call** on each of Family 1 + Family 2: derivation vs new archetype, with reasoning citing the 2026-05-07
   precedent.
3. **Flow-of-funds + viability map** (Block B + C) — markdown table per dimension cube, with web-research-backed
   rate-spread ranges flagging viable wedges.
4. **Implementation plan** scoped to top-N wedges (E4) — UAC + strategy-service + codex + deployment-UI touchpoints per
   wedge, sized in AI-days.
5. **Batch=live symmetry checklist** (Block F) — explicit per-seam tolerance for these archetypes, fed into the May-23
   cutover gate.

Operator iterates on the answers above with the agent. When the answers stabilise, this Q-group spawns one or more plans
in `plans/active/` and migrates to status: `closed-spawned-plans`.

---

## Research summary 2026-05-09

Four parallel sub-agent streams ran on 2026-05-09 to populate Blocks A / B / C / E. Reports synthesised below; each
finding is OBSERVED-FROM-CODE / OBSERVED-FROM-WEB / INFERRED per the underlying agent's labelling.

### Stream 1 — Existing archetype audit (Block A)

OBSERVED — 8 archetypes currently in
[`unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py`](../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py)
covering DeFi:

| Archetype                    | Recursive-borrow? | Cross-venue? | Share-class config? |      Lending leg      |  Perp leg   |        Kill-switch wired?        |
| ---------------------------- | :---------------: | :----------: | :-----------------: | :-------------------: | :---------: | :------------------------------: |
| `CARRY_STAKED_BASIS`         |        NO         |     YES      |    USDC (fixed)     |          YES          |     YES     | YES (drawdown 0.05, breach 0.03) |
| `CARRY_BASIS_PERP`           |        NO         |     YES      |    Configurable     |          NO           |     YES     | YES (drawdown 0.10, breach 0.05) |
| `ARBITRAGE_PRICE_DISPERSION` |        NO         |     YES      |    Configurable     |          NO           | Conditional |       NO (not yet seeded)        |
| **`CARRY_RECURSIVE_STAKED`** |      **YES**      |     YES      |   ETH/SOL (fixed)   |          YES          |     YES     | YES (drawdown 0.05, breach 0.03) |
| `CARRY_BASIS_DATED`          |        NO         |     YES      |    USDT (fixed)     |          NO           |     YES     | YES (drawdown 0.10, breach 0.05) |
| `YIELD_ROTATION_LENDING`     |        NO         |     YES      |   USDC (default)    |          YES          |     NO      |       NO (not yet seeded)        |
| `YIELD_STAKING_SIMPLE`       |        NO         |      NO      |  Native (ETH/SOL)   |          NO           |     NO      |       NO (not yet seeded)        |
| `LIQUIDATION_CAPTURE`        |        NO         |     YES      |      USDC/USDT      | YES (liq. collateral) |     NO      |       NO (not yet seeded)        |

**Key finding**: `CARRY_RECURSIVE_STAKED` ALREADY exists at
[enums.py:65](../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py#L65) with codex doc
[`carry-recursive-staked.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md) and tracer
math `_net_apr_recursive(stake_apy, borrow_apy, ltv, n_loops)` at
[`defi_carry_recursive_staked_decision_trace.py:210`](../../../execution-service/execution_service/cli/defi_carry_recursive_staked_decision_trace.py#L210).
The recursion semantics, share-class semantics, and kill-switch surface are identical to Family 1 + Family 2 needs.

### Stream 2 — MTDS lending+funding rate coverage audit (Block E)

OBSERVED — `lending-indices DEFERRED` note in
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](../active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
blocks backtest. Three bugs gate the fix:

1. **Bug 1** — Aave V3 Ethereum silent-zero capture (subgraph returns 0 → adapter writes `empty_confirmed` instead of
   `attempted_failed`; CLAUDE.md "honest absence vs fake placeholders" violation).
2. **Bug 2** — Compound V3 multi-chain subgraph schema mismatch.
3. **Bug 3** — `instruments-store-defi` 2022 metadata floor (no pre-2022 instrument metadata; recursive-borrow needs ≥1y
   backtest).

OBSERVED — `LST_RATES` + `PERP_FUNDING` data_type enums exist; `SUPPLY_APY` / `BORROW_APY` / `UTILISATION` /
`LIQUIDATION_THRESHOLD` / `EMODE_PARAMS` do NOT yet exist as data_type enums. Spawned plan Phase 1 ships them.

**Backtest verdict**: BLOCKED for both Family 1 and Family 2 until Bug 1/2/3 fix + lending-indices backfill runs. Phase
1 of the spawned plan is therefore P0 critical-path.

### Stream 3 — Web rate sampling (Block B + C)

OBSERVED-FROM-WEB (snapshot 2026-05-09; data freshness caveat):

- **Same-asset spreads on Aave V3 / Compound V3 are NEGATIVE (-0.5% to -1.7%)** across Ethereum / Arbitrum / Base for
  USDC / USDT / ETH / WBTC. Pure same-asset rate carry is NOT viable on any tier-1 lending venue under current rates.
- **Family 1 viable wedges** (LST/LRT cross-asset loops):
  1. wstETH-collateral / WETH-debt on Aave V3 Ethereum (e-mode 14×): ~9% net APY post-fees + slippage.
  2. weETH-collateral / WETH-debt (modified Liquid e-mode): ~15-28% gross at 10-14× leverage; higher tail (LRT depeg +
     slashing).
  3. Pendle PT-stETH leveraged via Aave (PT e-mode, 2026-04-29 onboarded): 5-22% implied yield depending on PT maturity.
- **Family 2 viable wedges** (long-funding-perp recursive-borrow):
  1. ETH spot-on-Aave-Eth + ETH-PERP-short-on-Hyperliquid: funding ~10-11% − ETH borrow 2.05% ≈ 8-9% net spread; ~25-40%
     APY at peak funding regime.
  2. BTC spot-on-Aave + BTC-PERP-short-on-Bybit: ~9-10% net spread; ~30-45% APY.
  3. ETH spot-on-Aave-Base + ETH-PERP-short-on-HL: same trade as #1 with Base gas savings; ~7-8% net.
- **E-mode parameters**: ETH-correlated 93% LTV / 95% LT / 1% penalty on Ethereum mainnet; 90% LTV on Base + Arbitrum.
  Stablecoin e-mode ~95-97% LTV. cbBTC/WBTC liquid e-mode onboarded Nov-2024.
- **Aave V3 flash fee**: 0.05% per principal (governance SSOT).
- **Production looping helpers**: DefiSaver, Instadapp/Avocado, Contango, Summer.fi, Gearbox — all live;
  recursive-looping is no longer a manual integration.

### Stream 4 — Family 2 flow-of-funds verification (Block B6 + C2 + C5)

CRITICAL FRAMING-GAP CAUGHT — the user's stated flow ("borrow ETH → short borrowed ETH on perp directly") is
mechanically broken because Hyperliquid / Bybit / OKX margin only in USDC. The correct shape:

- **The recursion is purely lending-side**. N supply-borrow loops compound the spot-ETH stack on Aave.
- **The perp short is a SINGLE matched leg** sized against cumulative spot-ETH exposure post-recursion.
- **USDC margin for the perp is separately funded** (treasury allocation, NOT from the recursive borrow).
- **Share-class accounting** = (aETH_balance + free_ETH − ETH_debt + perp_short_signed) → configurable target net delta:
  - `target_net_delta=0` → fully hedged, NAV in ETH, earn pure carry.
  - `target_net_delta=+1.0` → "hold 1 ETH" + earn carry on top (perp under-hedged by 1 ETH).
- **Leverage ceiling**: 1/(1 − safety_LTV). At 80% safety LTV = 5x; at 93% e-mode max LTV = 14.3x (liquidation-prone,
  never run there).

OBSERVED — execution-service primitives shipped:

- Aave supply / withdraw / borrow / repay / flash_loan in
  [`aave.py:933-1123`](../../../execution-service/execution_service/defi_execution/protocols/aave.py)
- Morpho equivalents in
  [`morpho.py:142-235`](../../../execution-service/execution_service/defi_execution/protocols/morpho.py)
- Uniswap `swap_exact_input` in
  [`uniswap.py:863`](../../../execution-service/execution_service/defi_execution/protocols/uniswap.py)
- WETH wrap/unwrap in [`weth.py:53`](../../../execution-service/execution_service/defi_execution/protocols/weth.py)
- `FlashLoanReceiver.sol` 35-LOC passthrough in
  [`deployment-service/contracts/FlashLoanReceiver.sol`](../../../deployment-service/contracts/FlashLoanReceiver.sol) —
  does NOT execute custom user logic in the callback; needs extension to run supply/borrow/swap atomically.
- Hyperliquid `place_order` in
  [`hyperliquid.py:163`](../../../execution-service/execution_service/defi_execution/protocols/hyperliquid.py) —
  **simulation-only** per docstring; needs live wire-up.

OBSERVED — missing primitives (Phase 5-9 of spawned plan):

1. `RecursiveLoopOrchestrator` (persistent + flash modes).
2. Extended `RecursiveLeverageReceiver.sol` (action-encoder pattern).
3. Hyperliquid LIVE perp connector.
4. `PerpHedgeSizer` + USDC margin top-up automation.
5. `HealthFactorMonitor` + `LiquidationProximityCircuit` + alerting integration.
6. Matching-engine DeFi cost model (gas + slippage + flash premium).

## Architectural decisions 2026-05-10 (locked)

| Decision | Call                                                                                                      | Justification                                                                                                                                                                       |
| -------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **AD-1** | Both families = CONFIG VARIANTS of `CARRY_RECURSIVE_STAKED`, NOT new archetypes                           | Recursion + share-class + kill-switch surface match the existing archetype; extends 2026-05-07 precedent (`leveraged_funding_arb` = config variant of `ARBITRAGE_PRICE_DISPERSION`) |
| **AD-2** | Recursion is lending-side only; perp is a single matched leg with separate USDC margin                    | Hyperliquid / Bybit / OKX margin USDC-only; user's "borrow coin → margin perp" framing is mechanically broken                                                                       |
| **AD-3** | Share class configurable via `target_net_delta` (units of share-class coin)                               | Same archetype handles delta-neutral (NAV-in-coin) AND "hold N coin + carry" with one parameter                                                                                     |
| **AD-4** | Two opening modes: `persistent` (N-tx, no flash fee) and `flash` (1-tx, 0.05% Aave premium) ship together | Persistent default below 5 ETH; flash above; gas-cost crossover                                                                                                                     |
| **AD-5** | May-23 scope: Aave V3 (Eth + Base) + Hyperliquid + Bybit ONLY                                             | Spark / Morpho / Maker / Compound multi-chain / other perp venues / Solana to follow-up plan                                                                                        |
| **AD-6** | Backtest is the gate, not paper-trade                                                                     | Phase 1 lending-indices backfill is P0 critical-path; without it, no historical funding-regime coverage for paper-smoke                                                             |

## Spawned plan

→
[`plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`](../active/defi_recursive_borrow_archetypes_2026_05_10.md)

13 phases, ~17 calendar AI-days end-to-end, fits the May-23 cutover if Phase 1 starts no later than 2026-05-12.
Cross-plan coordination banners (4 banners on `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`,
`master_to_live_defi_2026_05_23.md`, `defi_master_2026_05_07.md`, `alerting_service_live_rules_2026_05_07.md`) listed in
Phase 0 of the spawned plan.
