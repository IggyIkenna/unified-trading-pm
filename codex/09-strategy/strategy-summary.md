---
doc_type: codex-ssot
title: Strategy Architecture v2 — Summary
summary: >-
  Human-readable summary of Strategy Architecture v2 (2026-04-17 clean-start) — 9 families, 57 archetypes (the UAC
  `StrategyArchetype` enum is the canonical SSOT; this doc reflects it), 7 axes of composition, 10 cross-cutting
  concerns, and a 5-layer strategy identity (family → archetype → instance → config → derived categories). Execution
  talks via a polymorphic `StrategyInstruction` with 14 action types; batch=live is guaranteed by the benchmark-fills
  contract; target ceiling ~240-300 instances without code explosion. Supersedes the per-category
  (cefi/defi/sports/tradfi/prediction) structure.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, unified-trading-pm]
scope: [engineer]
tags: [strategy, archetype, strategy-family, execution, uac, ml]
related: [architecture-v2/README.md, architecture-v2/cross-cutting/pnl-attribution.md, architecture-v2/MIGRATION.md]
created: 2026-04-24
authoritative_for:
  [strategy architecture v2 narrative summary (9 families / 57 archetypes / 7 axes / 10 cross-cutting overview)]
referenced_by:
  [
    /codex/01-domain/market-making-strategy.md,
    /codex/04-architecture/live-strategy-config-hot-reload.md,
    /codex/04-architecture/ml-experiment-lifecycle.md,
    /codex/04-architecture/research-service-and-dart-integration.md,
    /codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    plans/epics/cross_cutting_may_23_SUPERSEDED_2026_05_21.md,
  ]
owner:
last_reviewed:
code_refs: [unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py]
---

# Strategy Architecture v2 — Summary

**What it is:** The canonical, clean-start architecture (dated 2026-04-17) for every trading strategy in the Unified
Trading System. It lives in
[/home/hk/unified-trading-system-repos/unified-trading-pm/codex/09-strategy](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-pm/codex/09-strategy/architecture-v2/)
and supersedes the previous per-category structure (cefi / defi / sports / tradfi / prediction), which is now
reference-only.

**Core mental model:** Every strategy decomposes into:

| Layer                  | Count | What it captures                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ---------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Families               | 9     | Orthogonal alpha styles (ML Directional, Rules Directional, Carry & Yield, Arbitrage/Structural, Market Making, Event-Driven, Vol Trading, Stat Arb/Pairs, **Portfolio**). PORTFOLIO added 2026-04-25 (cross-category sleeves) per Phase 9 of `dart_ui_strategy_filtering_and_onboarding_2026_04_24.md`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Archetypes             | 57    | Specific code paths within a family (e.g.`CARRY_BASIS_PERP`, `ML_DIRECTIONAL_CONTINUOUS`). 2026-04-25 Phase 9 expansion grew the surface from 18 to 53: VOL family 1→19, MM family 2→10 (incl. 3 DeFi LP variants), ARBITRAGE_STRUCTURAL 2→7 (incl. 4 MEV + cross-domain event arb), PORTFOLIO 0→4. Subsequent additions: `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` → **55**. 2026-05-12 operator taxonomy decision: `CARRY_RECURSIVE_BORROW_PERP_HEDGED` renamed `CARRY_BASIS_PERP_INV` (net 0); added `CARRY_STAKED_BASIS_DATED` + `CARRY_BASIS_DATED_INV` → **57** (uac@0196842, 2026-05-18). **SSOT**: `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` + `ARCHETYPE_TO_FAMILY` dict — that file is canonical; this doc reflects it. |
| Axes of composition    | 7     | signal × edge × staking × venue × expression × hold-policy × share-class                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Cross-cutting concerns | 10    | Risk gates, venue selection, execution policies, transfers, allocator, MEV, benchmark fills, capital isolation, trade expression, venue-account coordination                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

A strategy's identity has **5 layers** : family → archetype → instance → config → derived categories. Communication with
execution happens through a **polymorphic `StrategyInstruction`** with 14 action types (TRADE, SWAP, LEND, BORROW,
STAKE, UNSTAKE, QUOTE, TRANSFER, BRIDGE, ATOMIC, CANCEL, **CONVERT_DUST, LP_MINT, LP_BURN**) — the latter 3 added with
the Phase 9 DeFi LP archetypes (LP_MINT + LP_BURN are 2 distinct enum members, not one slash-pair). SSOT:
`unified_api_contracts.internal.architecture_v2.enums.InstructionActionV2`.

> **2026-05-08 drift correction.** Pre-2026-05-08 this doc described 8 families / 18 archetypes — those numbers were the
> 2026-04-17 baseline before the Phase 9 expansion. The UAC enum is canonical; if this doc disagrees with
> `unified_api_contracts/internal/architecture_v2/enums.py`, the enum wins. Refresh trigger: slot 8 Strategy-area Phase
> 1.B audit (2026-05-12; see
> [`plans/archive/issues/codex_audit_strategy_2026_05_12.md`](../../plans/archive/issues/codex_audit_strategy_2026_05_12.md)
> ST-1/ST-2/ST-14 — the prior `cross_cutting_strategy_catalogue_already_shipped_2026_05_08.md` issue-doc reference is no
> longer at the listed path; the audit chain now anchors on the Phase 1.B issue doc + the
> `codex_vs_citadel_infrastructure_audit_2026_05_10.md` parent plan).

> **Static enforcement of "the enum wins"** (codex audit ST-10 2026-05-12): the QG ratchet
> `check_strategy_taxonomy_counts.py` (planned at `unified-trading-pm/scripts/quality_gates/`) parses `enums.py` member
> counts + greps codex `.md` files for hard-count patterns (`\d+ archetype` / `\d+ families` / `\d+ action types`) +
> fails on mismatch. Would have caught the ST-1 / ST-2 / ST-3 / ST-6 drift cluster automatically. Ships under the
> Strategy-area Phase 4 follow-up. Until the QG ships, reviewers reject codex `.md` PRs that change hard counts without
> a same-PR `enums.py` edit.

> **Strategy-service co-location invariants** (codex audit ST-8 + ST-9 2026-05-12):
>
> - `strategy_service/engine/` MUST have ZERO imports from `strategy_service/adapters/` — co-location boundary per
>   `python-backend.md` "engine/adapters/cli structure". Enforcement: `strategy_service/topology_enforcement.py` (verify
>   coverage; if it doesn't statically check engine→adapter, add a `grep`-on-engine-imports or AST-walk to
>   `strategy-service/scripts/quality-gates.sh`).
> - `strategy_service/signal_broadcast/` (12 modules) MUST satisfy the 5 service-infrastructure invariants enumerated in
>   [`/codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md`](/codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md):
>   `ServiceBootstrap` wired · `make_health_router` with nested `signal_broadcast` `data_freshness` callback · typed
>   `SignalBroadcastConfig` reloaders · zero local schema definitions (UAC `signal_broadcast` facade) · `ApiKeyReloader`
>   for HMAC creds (NOT one-shot `validate_api_keys_for_venues()`). Statically asserted via `failure_isolation.py` using
>   `classify_venue_error()` + emitting `ADAPTER_FETCH_FAILED`; `credentials.py` importing `ApiKeyReloader`. QG-step
>   wiring to be added to strategy-service `scripts/quality-gates.sh` under Phase 4 follow-up.

**Main use / why it exists:**

1. **Collapse 200+ legacy strategy variants into 57 code paths** served by shared family engines — new strategies become
   config, not new code. (The 2026-04-17 baseline had 18 archetypes covering the original 53 strategies; Phase 9
   expanded the archetype set to 53 to cover MEV, DeFi LP, full vol-surface trading, prediction MM, cross-category event
   arb, and portfolio sleeves; the subsequent `CARRY_RECURSIVE_STAKED` split — into
   `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` — brought the total to **55**;
   2026-05-18 operator taxonomy decision renamed `CARRY_RECURSIVE_BORROW_PERP_HEDGED` → `CARRY_BASIS_PERP_INV` and added
   `CARRY_STAKED_BASIS_DATED` + `CARRY_BASIS_DATED_INV` → **57**.)
2. **Categories become derived labels** , not routing axes — no more `CEFI_ML_DIRECTIONAL_BTC` vs
   `TRADFI_ML_DIRECTIONAL_SPY` duplication.
3. **Unify capital flow** across DeFi bridges, CEX wallet transfers, Unity sports pools, and TradFi tunnels via a single
   event-driven primitive (`TRANSFER` / `BRIDGE` / `AllocationDirective`).
4. **Versioned, opt-in artifacts** for feature groups, ML models, execution policies, risk policies, venue capabilities
   — no auto-upgrades.
5. **Batch = live** via the benchmark-fills contract, so strategy alpha is isolated from execution alpha. See
   [`pnl-attribution.md § 7`](architecture-v2/cross-cutting/pnl-attribution.md#7-factor--layer-dual-axis--closed-sets-stay-decoupled)
   for the factor × layer decomposition (16-factor closed set, `STRATEGY` vs `EXECUTION` layers, 5 decomposition
   invariants) that this batch=live contract enables. `STRATEGY_ALPHA` and `EXECUTION_ALPHA` are derived rollup views,
   not enum members.
6. **Target ceiling** of ~240-300 strategy instances without code explosion.

**How it's used in practice:** Implementers read the protocol spec + identity-versioning rules; strategy designers pick
a family doc then an archetype doc; operators focus on portfolio-allocator + venue-account-coordination; UI/reporting
consumes the derived-categories and share-class axes. Migration tracking for every legacy doc/strategy lives in
[MIGRATION.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/MIGRATION.md).

# The 9 Families — One-Liner Each

| #   | Family                          | Core idea                                                                                                                            | Example                                                                                                                     |
| --- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| 1   | **ML Directional**              | A trained model predicts outcome probability; trade when model prob diverges from implied/market price.                              | ML model says BTC 5m up-move prob = 58%, market implies 50% → go long.                                                      |
| 2   | **Rules Directional**           | Hard-coded if/then rules on features fire signals — no model, just thresholds.                                                       | "If RSI < 30 AND funding < 0 → buy."                                                                                        |
| 3   | **Carry & Yield**               | Capture a rate/yield differential by holding a spread, earning funding, lending, staking, or basis.                                  | Long spot BTC + short perp BTC → earn positive funding.                                                                     |
| 4   | **Arbitrage / Structural Edge** | Near-risk-free payment from price dispersion or protocol mechanics. Includes MEV (DeFi-only).                                        | Buy on Pinnacle, lay on Betfair at better odds → locked profit; or capture a liquidation bonus on Aave.                     |
| 5   | **Market Making**               | Post two-sided quotes and earn the bid-ask spread while managing inventory risk. Includes DeFi LP.                                   | Quote Betfair EPL 1X2 at 1-tick spread; rebalance as fills arrive.                                                          |
| 6   | **Event-Driven**                | Scheduled external event with measurable surprise drives the trade (earnings, CPI, fixture news).                                    | Buy straddle before FOMC; unwind after surprise is priced.                                                                  |
| 7   | **Vol Trading**                 | Alpha comes from vol metrics themselves — IV vs RV, skew, term structure, cross-asset vol.                                           | Sell Deribit BTC 30d IV when it trades rich vs realized.                                                                    |
| 8   | **Stat Arb / Pairs**            | Spread between two correlated underlyings mean-reverts or trends.                                                                    | Long GOOG / short META when z-score of spread < −2.                                                                         |
| 9   | **Portfolio**                   | Cross-category sleeves: not a single edge, but a meta-allocation across instances of the other 8 families. Added 2026-04-25 Phase 9. | A multi-strategy sleeve that runs ML Directional + Carry + Vol Trading instances in fixed weights and rebalances quarterly. |

**Key rule:** one family per strategy — assigned by the _primary_ alpha source. "ML directional with a vol hedge" is
still ML Directional; the vol leg is just risk management, not a composite. Portfolio is the one exception: by
construction it spans family instances (its `primary_category` is `CROSS_CATEGORY`).

# The 9 Families — Pulled directly from the family docs

**1. ML Directional** —
[families/ml-directional.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/families/ml-directional.md)

- **Alpha source:** Machine-learning model prediction of outcome probability vs. market-implied probability. When model
  probability exceeds implied by a threshold, a bet is placed with stake sized by signal strength.
- **Primary edge method:** Value (`model_prob > implied_prob + min_edge_threshold`).
- **Covers:** Crypto ML (BTC/ETH/SOL direction on perps, spot, options), Equity ML (SPY/QQQ/individual stocks), Sports
  ML (1X2, O/U, BTTS), Options ML, Binary prediction-market ML (Polymarket).

**2. Rules Directional** —
[families/rules-directional.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/families/rules-directional.md)

- **Alpha source:** Hard-coded if-else rules on features that produce discrete fire/no-fire signals. Each rule encodes a
  specific behavioural or statistical hypothesis.
- **Primary edge method:** Threshold-crossed (rule fires when feature values meet condition).
- **Examples from the doc:** "when 20-day z-score > 2.0 and volume > 1.2x average, go long"; "when RSI < 30 and MACD
  crosses up, buy"; "when home team scores first within 20 min, back away team for HT draw"; "when HT score is 0-0 and
  both teams have ≥0.5 xG, back over 0.5 goals 2H".

**3. Carry & Yield** —
[families/carry-and-yield.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/families/carry-and-yield.md)

- **Alpha source:** Rate / yield differential capture. Whether funding on a perp, lending APY, staking reward, or basis
  spread on a dated future — the common thesis is capturing a paid rate that compensates for holding a position.
- **Primary edge method:** Rate-differential sustained above a cost threshold.
- **Sub-patterns:** Basis dated (long spot + short dated future), Basis perp (long spot + short perp for funding),
  Staked basis (stake ETH → stETH → Aave pledge → short perp), Recursive staked basis, Yield rotation across lending
  protocols, Simple staking.

**4. Arbitrage / Structural Edge** —
[families/arbitrage-structural.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/families/arbitrage-structural.md)

- **Alpha source:** Price dispersion between markets OR structural payment from protocol mechanics. Edge is largely
  risk-free (or near-risk-free) conditional on correct execution. NOT directional — no view on where prices go.
- **Primary edge method:** Spread > cost (dispersion) OR structural bonus > cost (protocol-mechanic).
- **Examples from the doc:** Cross-CEX arb, cross-DEX arb, flash-loan DEX arb, sports cross-book arb, cross-category
  (Polymarket-Betfair), cross-venue vol arb (same option quoted at different IVs on Deribit vs OKX), hard no-arb
  violations (butterfly / calendar / put-call parity), Aave/Compound/Euler/Morpho liquidation capture.

**5. Market Making** —
[families/market-making.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/families/market-making.md)

- **Alpha source:** Bid-ask spread capture via two-sided quoting around a theoretical fair price. We provide liquidity;
  we earn spread minus adverse selection.
- **Primary edge method:** Spread capture, net of adverse selection + inventory risk + fees.
- **Covers:** CEX spot/perp MM (Binance, OKX, Bybit, Hyperliquid, Deribit), Options MM (Deribit, CBOE SPY), DeFi active
  LP (Uniswap V3 concentrated, Orca on Solana), Sports exchange MM (Betfair, Smarkets, Matchbook), Cross-venue MM.

**6. Event-Driven** —
[families/event-driven.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/families/event-driven.md)

- **Alpha source:** Scheduled external events with measurable surprise. When an event releases (FOMC, CPI, NFP,
  earnings, OPEC), the event's surprise relative to consensus produces a measurable, time-bounded reaction.
- **Primary edge method:** `surprise magnitude × model-predicted direction > threshold`, within a bounded time window
  around the event.
- **Examples from the doc:** FOMC rate decisions, US CPI/PPI/PCE releases, US Non-Farm Payrolls, OPEC/OPEC+ meetings,
  EIA crude inventory release, corporate earnings, ECB/BoE/BoJ rate decisions, China economic data.

**7. Vol Trading** —
[families/vol-trading.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/families/vol-trading.md)

- **Alpha source:** Volatility-metric dislocation. Alpha is a view on vol itself (IV vs RV, skew, term structure,
  cross-asset vol) — not a directional view on the underlying. Baseline positions are delta-hedged; P&L comes from vega,
  gamma, theta.
- **Primary edge method:** Vol-metric dislocation vs fair (IV too rich/cheap vs realized; skew extreme vs historical;
  term structure bowed beyond no-arb bounds).
- **Sub-patterns from the doc:** IV vs RV, skew dislocation (e.g., 25d put skew rich vs historical → risk reversal),
  term structure (calendar trades), soft surface residuals (SVI fit residuals suggesting rich/cheap strikes),
  cross-asset vol.

**8. Stat Arb / Pairs** —
[families/stat-arb-pairs.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/families/stat-arb-pairs.md)

- **Alpha source:** Statistical spread between two or more underlyings that mean-reverts (or trends) against a
  historical relationship. Unlike price-dispersion arb, Stat Arb has spread risk — relationship can break —
  statistically, not mechanically, profitable.
- **Primary edge method:** Spread z-score mean-reversion (or less commonly, spread momentum / divergence).
- **Examples from the doc:** Fixed pairs — GOOG-META, ES-NQ, BTC-ETH, XLE-SPY (cointegration-tested); Cross-sectional —
  rank all assets in a universe by a signal (e.g., cross-sectional ML), long top-N / short bottom-N, e.g. Russell 1000
  daily, crypto top-50 hourly.

**Distinguishing test called out in the docs:** is the edge _mechanical_ (guaranteed conditional on correct execution)
or _statistical_ (profitable on average with spread risk)? Mechanical → Arbitrage. Statistical → Vol Trading / Stat Arb.

**9. Portfolio** — _added 2026-04-25. Family doc:
[`architecture-v2/families/portfolio.md`](./architecture-v2/families/portfolio.md)_

- **Alpha source:** Meta-allocation across instances of the other 8 families. The Portfolio family does NOT generate its
  own per-trade signals — it produces `AllocationDirective` events that re-weight or activate/deactivate child strategy
  instances based on portfolio-level objectives (risk parity, factor exposure, regime, manual mandate).
- **Primary edge method:** Allocator-driven (closest mapping is rate-differential or rank-weighted, but at the strategy
  level not the instrument level).
- **Sub-patterns:** Multi-strategy sleeves, risk-parity allocation, factor-allocation overlay, tactical operator
  override.
- **Why it's a family, not a cross-cutting concern:** unlike the Portfolio Allocator service (which sits ABOVE all
  strategies), Portfolio archetypes are themselves strategy instances — they receive equity, emit `AllocationDirective`s
  to child strategies, run through the same risk-gate / kill-switch / share-class machinery as any other strategy. This
  composability is intentional: a tactical-overlay sleeve can itself be allocated capital by a higher-level allocator.

# The 53 Archetypes — pulled from each archetype doc

> **Per-archetype docs lag the enum.** The `architecture-v2/archetypes/` folder has 25 individual archetype docs
> covering the 2026-04-17 baseline + 7 of the Phase 9 additions. The remaining 28 Phase 9 archetypes (mostly the new VOL
> family variants + the 4 PORTFOLIO archetypes) are declared in the UAC enum + `STRATEGY_REGISTRY` but await full
> per-archetype write-ups. The summary entries below cite the enum SSOT and link to docs where they exist.

## ML Directional (2)

**`ML_DIRECTIONAL_CONTINUOUS`** —
[archetypes/ml-directional-continuous.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md)
Consumes probability predictions from an ML model (per direction, per instrument), compares to market-implied
probability, and emits target-state trade instructions when edge + confidence thresholds are met. Flow: model inference
→ calibration → implied-from-mid → edge = calibrated_P − implied_P → confidence/edge gates → Kelly-sized stake → emit
`TRADE`. Held until `HOLD_UNTIL_FLIP` or `SAME_CANDLE_EXIT`.

**`ML_DIRECTIONAL_EVENT_SETTLED`** —
[archetypes/ml-directional-event-settled.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md)
Same value-edge logic but for event-settled markets (sports 1X2, O/U, BTTS, prediction binaries). Flow adds: implied
from `1/decimal_odds` (optionally vig-free), odds gate (`decimal_odds ≤ max_odds`), best-odds selection across eligible
books (Unity routes per outcome). Stakes settle at event resolution.

## Rules Directional (2)

**`RULES_DIRECTIONAL_CONTINUOUS`** —
[archetypes/rules-directional-continuous.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/rules-directional-continuous.md)
Evaluates a registry of explicit if-else rules on features. When a rule fires, emit a directional signal; stake is
rule-specific (fixed % equity or calibrated from backtested hit rate). Engine does feature read → rule eval → conflict
resolution (priority / unanimity / highest-confidence) → emit `TRADE`.

**`RULES_DIRECTIONAL_EVENT_SETTLED`** —
[archetypes/rules-directional-event-settled.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/rules-directional-event-settled.md)
Same rules engine but targeting sports / prediction markets. Flow adds market-availability check, odds gate, best-odds
routing; bets settle standard WON/LOST/VOID.

## Carry & Yield (10)

**`CARRY_BASIS_DATED`** — [archetypes/carry-basis-dated.md](architecture-v2/archetypes/carry-basis-dated.md) Long spot +
short dated future. Captures futures–spot premium (contango) as the spread converges to zero at expiry. Near-atomic
paired entry; exits on convergence, expiry, or stop-loss on adverse widening.

**`CARRY_BASIS_DATED_INV`** — [archetypes/carry-basis-dated-inv.md](architecture-v2/archetypes/carry-basis-dated-inv.md)
Inverse of CARRY_BASIS_DATED: short dated future + long cash. Captures backwardation (futures < spot) as spread
converges to zero at expiry. Typical in commodity supply-crunch regimes (oil/gas) and crypto bear markets. Added
2026-05-18 per operator taxonomy decision (strategy_archetype_taxonomy_2026_05_12.md §V-1).

**`CARRY_BASIS_PERP`** —
[archetypes/carry-basis-perp.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md)
Long spot + short perpetual. Captures funding rate while delta-neutral; ATOMIC when both legs on same venue (e.g.,
Binance cross-margin netting — "enormous capital efficiency"), LEADER_HEDGE cross-venue. Rebalance triggers: funding
drops below exit, better funding elsewhere, delta drift, equity change.

**`CARRY_STAKED_BASIS`** — [archetypes/carry-staked-basis.md](architecture-v2/archetypes/carry-staked-basis.md) Stake
native → LST → transfer to perp venue as cross-margin → short perp. Earns staking yield + funding simultaneously. Net
carry = staking_apy_total + funding − fees. LST_AS_MARGIN only (no SPLIT_STAKE, no COLLATERAL_BORROW). Kill switch on
stETH depeg.

**`CARRY_STAKED_BASIS_DATED`** —
[archetypes/carry-staked-basis-dated.md](architecture-v2/archetypes/carry-staked-basis-dated.md) Dated-contract variant
of CARRY_STAKED_BASIS: stake LST + short a quarterly/monthly dated futures contract instead of a perp. Locks in the
basis premium at entry (no funding-rate variability); staking yield accrues during hold. Best when dated basis >
expected perp funding. Added 2026-05-18 per operator taxonomy decision.

**`CARRY_RECURSIVE_STAKED`** —
[archetypes/carry-recursive-staked.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/carry-recursive-staked.md)
Recursive leveraging of a staking position: stake → pledge → borrow → stake → ... Effective leverage ≈
`1 / (1 − LTV × safety)`, typically 3-4× on ETH. Captures leveraged staking yield with cascading liquidation risk;
unwind respects LST unbonding period.

**`CARRY_RECURSIVE_BORROW_LENDING_ONLY`** —
[archetypes/carry-recursive-borrow-lending-only.md](architecture-v2/archetypes/carry-recursive-borrow-lending-only.md)
Family 1 — pure-lending recursive arb (no perp leg, no LST-staking-yield leg). LST collateral on Aave V3 E-Mode at 0.93
LTV; borrow ETH; swap back to LST on Uniswap V3; redeposit; repeat. Closed-form `E_actual = base` — recursion amplifies
SPREAD not directional exposure. Top-7 May-23 cells across Aave V3 Ethereum / Arbitrum / Base; expected APR 6-10% net
for canonical wstETH/WETH cell. Added 2026-05-12.

**`CARRY_BASIS_PERP_INV`** — [archetypes/carry-basis-perp-inv.md](architecture-v2/archetypes/carry-basis-perp-inv.md)
Family 2 — recursive on-chain borrow loop (Aave V3 / Morpho wstETH/WETH E-Mode) + USDC-margined ETH perp short for delta
neutrality. Net APR = R_lend + R_fund + R_usdc − gas − slippage ≈ 17.4% for wstETH/WETH cell at +12% funding. HL
PRIMARY + Bybit SECONDARY (50% cap first 30 days). PerpHedgeSizer rebalances on delta-drift > 5% of E_actual. Renamed
from CARRY_RECURSIVE_BORROW_PERP_HEDGED 2026-05-18; see
[carry-recursive-borrow-perp-hedged.md](architecture-v2/archetypes/carry-recursive-borrow-perp-hedged.md) for historical
doc.

**`YIELD_ROTATION_LENDING`** —
[archetypes/yield-rotation-lending.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/yield-rotation-lending.md)
Single-sided supply (no leverage) rotated across chains/protocols based on APY. Continuous APY monitor → target
allocation per (protocol, chain) → `LEND` + `BRIDGE` instructions. Gas-aware: skip rebalance if gas > expected uplift.

**`YIELD_STAKING_SIMPLE`** —
[archetypes/yield-staking-simple.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/yield-staking-simple.md)
Pure staking — deposit native PoS asset into liquid staking protocol (Lido → stETH, Rocket Pool → rETH, Jito → JitoSOL,
Marinade → mSOL), hold, exit via DEX swap or withdrawal queue. No basis leg, no leverage, no directional view.

## Arbitrage / Structural (7)

**`ARBITRAGE_PRICE_DISPERSION`** —
[archetypes/arbitrage-price-dispersion.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md)
Detects price dispersion between venues on the same/equivalent instrument and locks in the spread net of costs. Covers
cross-CEX, cross-DEX (optional flash loan), sports cross-book (via Unity), cross-category (Polymarket ↔ Betfair),
cross-venue vol arb, within-venue no-arb violations (butterfly/calendar/put-call parity), funding-rate dispersion.
ATOMIC where supported, LEADER_HEDGE otherwise.

**`LIQUIDATION_CAPTURE`** —
[archetypes/liquidation-capture.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/liquidation-capture.md)
Monitors under-collateralised DeFi lending positions and executes liquidations to capture the protocol's paid bonus
(typically 5-10% of seized collateral). Zero directional risk. Health-factor watcher → flash-loan + repay + seize + DEX
swap + repay-flash-loan, all in a multicall bundle submitted via Flashbots for MEV protection.

**`ARBITRAGE_MEV_SANDWICH`** —
[archetypes/arbitrage-mev-sandwich.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-sandwich.md)
Front-run + back-run a victim swap to capture price impact. Mempool watcher → simulate victim trade impact → submit
buy-before + sell-after bundle via Flashbots / private RPC. DeFi-only. ETHICAL caveat: most workspaces deprioritise
sandwich strategies on user trades; may be retained for adversarial-defence research only. **Operator review required
before live activation.**

**`ARBITRAGE_MEV_JIT_LIQUIDITY`** —
[archetypes/arbitrage-mev-jit-liquidity.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-jit-liquidity.md)
Just-in-time concentrated liquidity provision around a pending large swap. Mint a tight Uniswap V3 position immediately
before the victim swap, capture fees, burn position immediately after. Zero inventory carry, fee-only profit. DeFi-only.

**`ARBITRAGE_MEV_BACKRUN`** —
[archetypes/arbitrage-mev-backrun.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-backrun.md)
Submit an arb transaction immediately after a target tx that creates a price dislocation (oracle update, large swap,
liquidation). Pure dispersion arb mechanically — distinguishes from `ARBITRAGE_PRICE_DISPERSION` by the mempool-trigger
shape vs continuous quote-poll. DeFi-only.

**`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`** —
[archetypes/arbitrage-mev-liquidation-bundle.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-liquidation-bundle.md)
MEV-bundled liquidation flow: oracle-update mempool watcher → pre-position before oracle lands → liquidate freshly
under-collateralised positions in same block. Strictly higher-throughput than `LIQUIDATION_CAPTURE` (which polls
on-chain health factors); both can run concurrently with non-overlapping target sets.

**`ARBITRAGE_CROSS_DOMAIN_EVENT`** _(per-archetype doc pending)_ — Same real-world event listed in PREDICTION + SPORTS
markets (e.g. "Trump wins 2028 election" on Polymarket + same line on Smarkets). Capture price dispersion across the two
venue-domains. `primary_category=CROSS_CATEGORY`. Strategy-picked routing per leg, ATOMIC where venues support it,
LEADER_HEDGE otherwise.

## Market Making (10)

**`MARKET_MAKING_CONTINUOUS`** _(legacy — retained for back-compat; new MM strategies use the granular variants below)_
—
[archetypes/market-making-continuous.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md)
Two-sided quoting around a theoretical fair price. Covers CLOB MM (Binance/OKX/Bybit/Hyperliquid/Deribit/Betfair/Unity),
AMM concentrated-liquidity "active LP" (now split into `DEFI_LP_CONCENTRATED`), and passive full-curve LP (now
`DEFI_LP_POOL`). Inventory-aware skewing, delta-proxy repricer (sub-ms). Highest latency budget of any archetype (40 ms,
premium tier, strategy-service co-located with execution).

**`MARKET_MAKING_EVENT_SETTLED`** _(canonical sports exchange MM archetype — Betfair / Smarkets / Matchbook / Betdaq
back-lay quoting. NOT legacy. Prediction CLOBs use `MARKET_MAKING_PREDICTION`. Retained per §9 operator decision in
`strategy_archetype_taxonomy_2026_05_12.md`)_ —
[archetypes/market-making-event-settled.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md)
Back + lay quoting on sports exchanges (Betfair, Smarkets, Matchbook, Betdaq) and prediction markets (Polymarket).

**`MARKET_MAKING_PASSIVE_SPREAD`** _(per-archetype doc pending)_ — Symmetric two-sided quotes at a fixed offset around a
reference mid. Simplest MM shape; no inventory adaptation, no ML lean — quote-and-hold. Used as the baseline benchmark
for more sophisticated MM variants.

**`MARKET_MAKING_INVENTORY_SKEW`** _(per-archetype doc pending)_ — Symmetric quotes whose mid-offset shifts with current
inventory: long inventory → skew quotes lower (faster fill on the sell side); short inventory → skew up.
Avellaneda–Stoikov style. Most CLOB MM strategies are this shape with venue-specific tunings.

**`MARKET_MAKING_ML_LEAN`** _(per-archetype doc pending)_ — Inventory-skew with an ML lean overlay: short-horizon
direction model produces a per-update directional bias that nudges the mid in the predicted direction. Adverse-selection
mitigation; leans toward the side that's likely to be the next fill.

**`MARKET_MAKING_QUEUE_MICROSTRUCTURE`** _(per-archetype doc pending)_ — Quote placement informed by L2-queue state
(queue position, order arrival rate, cancellation rate). Targets venues with deep books and meaningful queue priority
(Binance spot, large CME futures). Sub-tick price improvement as a function of queue dynamics.

**`MARKET_MAKING_PREDICTION`** _(per-archetype doc pending)_ — Two-sided quoting on prediction-market binary CLOBs
(Polymarket YES/NO; Kalshi). Theo from sharp reference (sport sharp book), model-derived (ML probability on macro
binaries), or vig-free consensus across multiple venues. Cancel quotes near settlement.

**`DEFI_LP_CONCENTRATED`** —
[archetypes/defi-lp-concentrated.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/defi-lp-concentrated.md)
Active concentrated-liquidity LP on Uniswap V3 / V4 / clones (Camelot, Aerodrome, Raydium CLMM, Joe V2). Mint a tight
range around fair, rebalance / re-mint when price drifts out of range. Routes through `LP_MINT` / `LP_BURN` actions
(Phase 9 InstructionAction additions) → NonfungiblePositionManager.

**`DEFI_LP_POOL`** —
[archetypes/defi-lp-pool.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/defi-lp-pool.md)
Passive full-curve LP (Uniswap V2 / Curve / Balancer / Aerodrome stable pools). Deposit + hold + collect fees;
divergence loss is the carry cost. No active rebalancing.

**`DEFI_LP_VAULT`** —
[archetypes/defi-lp-vault.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/defi-lp-vault.md)
LP via vault wrapper (Yearn, Beefy, Gamma, Arrakis) — vault manages the underlying position; we hold the vault token.
Single-deposit + single-withdraw lifecycle; vault APY is the gross yield, vault fee is the carry cost.

## Event-Driven (1)

**`EVENT_DRIVEN`** —
[archetypes/event-driven.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/event-driven.md)
Schedules positioning around known external events (FOMC, CPI, NFP, OPEC, earnings, EIA). At release tick: surprise =
(realized − consensus) / σ_forecasts; direction model maps surprise → per-instrument direction; emit `TRADE` at
HIGH/EMERGENCY urgency (typically MARKET orders); flatten at `T + event_window_minutes`.

## Vol Trading (19)

The 2026-04-25 Phase 9 expansion grew Vol Trading from a single `VOL_TRADING_OPTIONS` archetype to a full
surface-trading suite. The legacy archetype is retained for back-compat with existing Firestore + GCS records; new vol
strategies use the granular variants below. Per-archetype docs for the 18 new variants are pending — the entries below
cite the UAC enum SSOT only.

**`VOL_TRADING_OPTIONS`** _(legacy)_ —
[archetypes/vol-trading-options.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/vol-trading-options.md)
Delta-hedged options expression of a vol view. Surface fitter (SVI/SSVI) → vol dislocation scanner (IV vs RV, skew
extreme, term bowed, soft surface residuals — hard no-arb violations are routed to `ARBITRAGE_PRICE_DISPERSION`). Trade
constructors: straddle, strangle, butterfly, calendar, risk reversal, single-leg + delta hedge (gamma scalping).

**`VOL_ARB_RV_IV`** _(per-archetype doc pending)_ — Realised-vs-implied vol arb. Sell IV when IV/RV ratio is rich vs
historical; buy when cheap. Delta-hedged; P&L from vega + gamma scalping.

**`VOL_SPREAD_STRUCTURES`** _(per-archetype doc pending)_ — Structured option-spread expressions of a vol view: bull
spreads, bear spreads, condors, iron flies. Defined-risk vega expression.

**`VOL_CARRY`** — [archetypes/vol-carry.md](architecture-v2/archetypes/vol-carry.md) Sell short-dated options (straddle
/ strangle / iron condor) + delta-hedge via underlying perp. Harvests persistent IV-over-RV premium at 7-21 DTE tenors.
Net carry = theta + vega_carry − gamma_hedge_cost − fees. Roll at ≤3 DTE to avoid pin risk.

**`VOL_OVERLAY_COVERED_CALLS`** _(per-archetype doc pending)_ — Long underlying + short OTM calls. Income generation
overlay on a long-only book. Common in TradFi equity overlays.

**`VOL_OVERLAY_PROTECTIVE_PUT`** _(per-archetype doc pending)_ — Long underlying + long OTM puts. Tail-protection
overlay; pays insurance premium for downside cover.

**`VOL_STRADDLE`** _(per-archetype doc pending)_ — Long or short ATM straddle. Bet on realised vol vs implied; delta-
hedged for pure vega expression.

**`VOL_SYNTHETIC_DELTA`** _(per-archetype doc pending)_ — Synthetic underlying expression via long call + short put (or
reverse) at the same strike — used when the synthetic is cheaper than direct exposure (e.g. tax-advantaged TradFi).

**`VOL_MARKET_MAKING`** _(per-archetype doc pending)_ — Two-sided quoting on options markets (Deribit, CBOE). Theo from
surface fitter; inventory-skewed by net vega + gamma. Distinct from `MARKET_MAKING_CONTINUOUS` because the quoted
instrument has Greeks the strategy must continuously delta-hedge.

**`VOL_ML_LEAN`** _(per-archetype doc pending)_ — Vol-MM with an ML overlay predicting short-horizon IV moves; tilts
quotes asymmetrically to capture predicted direction.

**`VOL_0DTE_GAMMA_SCALPING`** _(per-archetype doc pending)_ — Same-day-expiry options + intraday delta-hedging. Captures
realised gamma on short-dated SPX/QQQ options. Highly latency-sensitive.

**`VOL_0DTE_PIN_RISK`** _(per-archetype doc pending)_ — Bet on/against pin behaviour at common round-number strikes on
0DTE expiries. Pin risk = price gravitating toward heavy open-interest strikes near close.

**`VOL_TERM_STRUCTURE_ARB`** _(per-archetype doc pending)_ — Calendar spread expression of a term-structure view. Long
vol on cheap tenor + short vol on rich tenor. P&L from term-structure-bow normalising.

**`VOL_TERM_STRUCTURE_SLOPE`** _(per-archetype doc pending)_ — Continuous expression of term-structure slope:
front-month vs back-month vs LEAPS. Distinct from `VOL_TERM_STRUCTURE_ARB` by hold horizon (slope = continuous, arb =
mean-reversion to a band).

**`VOL_DISPERSION`** _(per-archetype doc pending)_ — Long index vol + short single-name vols (or reverse). Captures
realised correlation differentials. Index-vol-rich-vs-single-name-vol setup is the textbook case.

**`VOL_VARIANCE_SWAP`** _(per-archetype doc pending)_ — Pure variance exposure via variance swap or variance-replication
portfolio. P&L = ∑(ln(S*t/S*{t-1}))² − strike. Delta-immune by construction.

**`VOL_LEAPS_CONVEXITY`** _(per-archetype doc pending)_ — Long-dated equity options (LEAPS, 1y+ expiry). Convexity
expression on long-horizon vol; vega large, theta small.

**`VOL_CROSS_ASSET_SPREAD`** _(per-archetype doc pending)_ — Long vol on asset A vs short vol on asset B (e.g. SPX vol
vs gold vol, BTC vol vs ETH vol). Captures cross-asset vol differentials.

**`VOL_RATIO_SPREAD`** _(per-archetype doc pending)_ — Long N options at strike K + short M options at strike K′ (N ≠
M). Custom convexity / theta-harvesting profile depending on the ratio + strike spacing.

## Stat Arb / Pairs (2)

**`STAT_ARB_PAIRS_FIXED`** —
[archetypes/stat-arb-pairs-fixed.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/stat-arb-pairs-fixed.md)
Pre-determined, cointegration-tested or historical-beta-stable pair. `spread = price_A − hedge_ratio × price_B`; z-score
vs rolling mean/std. Entry on `|z| > entry_threshold AND cointegration_pvalue < 0.05`. Exits on convergence, p-value
degrading > 0.15, max-z stop, or max_hold_bars.

**`STAT_ARB_CROSS_SECTIONAL`** —
[archetypes/stat-arb-cross-sectional.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/stat-arb-cross-sectional.md)
Universe-wide ranking (Russell 1000, S&P 500, crypto top-50). Cross-sectional ML/factor model scores each member; long
top-M, short bottom-M; equal-weight / rank-weighted / confidence-weighted. Members rotate each rebalance. "Joint
reasoning over the whole universe — this is what distinguishes it from running N independent ML directional strategies."

## Portfolio (4) _— added 2026-04-25 Phase 9_

The Portfolio family adds 4 cross-category sleeve archetypes. Each is itself a strategy instance: receives equity, runs
through risk gates, kill-switch machinery, and share-class accounting like any other strategy — but its emitted
instructions are `AllocationDirective` events to child strategy instances rather than per-instrument `TRADE`s.

**[`PORTFOLIO_MULTI_STRATEGY`](./architecture-v2/archetypes/portfolio-multi-strategy.md)** — Equal-weighted (or
fixed-weight) multi-strategy sleeve. Allocates across N child strategy instances spanning multiple families (e.g. ML
Directional + Carry + Vol Trading) with operator-mandated weights. Rebalances on a fixed cadence (daily / weekly /
monthly).

**[`PORTFOLIO_RISK_PARITY`](./architecture-v2/archetypes/portfolio-risk-parity.md)** — Risk-parity allocation across
child strategy instances. Per-strategy realised-vol estimate → inverse-vol weighting → child equity targets. Re-runs at
the rebalance cadence.

**[`PORTFOLIO_FACTOR_ALLOCATION`](./architecture-v2/archetypes/portfolio-factor-allocation.md)** — Factor-exposure
allocation: declares target loadings on systemic factors (carry / momentum / vol / size / quality), allocates to child
strategies whose realised exposures load onto those factors. Used for mandate-driven sleeves.

**[`PORTFOLIO_TACTICAL_OVERLAY`](./architecture-v2/archetypes/portfolio-tactical-overlay.md)** — Operator/regime-driven
tactical re-weighting on top of a base allocation. Regime classifier or operator command → per-strategy multiplier on
base weight. Higher-frequency rebalancing than the other 3 (intraday possible).

---

**Coverage note from the docs:** each archetype declares `topology_requirements` frontmatter (isolation, co-location,
latency budget, min SLA tier). MM archetypes (incl. all Phase 9 MM variants and `VOL_MARKET_MAKING`) are the only ones
needing premium tier + strategy-service isolated + co-located with execution (40 ms budget). MEV archetypes need
co-location with a private RPC / Flashbots relay. Rules/yield archetypes sit on basic tier (500 ms). Portfolio
archetypes are higher-latency-tolerant since they re-emit allocation directives at scheduled cadences, not on each tick.
Everything else is standard tier (150 ms).

# The 7 Axes — pulled from each axis doc

**1. Signal Source** —
[axes/signal-sources.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/axes/signal-sources.md)
The mechanism that produces the raw decision trigger — _how_ the alpha is generated. Catalog:

- **ML models** (binary classifier, multi-class, regression, cross-sectional ranking, probability calibration)
- **Rules engines** (TA indicators, feature-condition rules, regime classifiers, pattern match)
- **Rate / yield monitors** (funding, lending APY, staking reward, basis spread)
- **Orderbook / microstructure** (L2 depth, theo fair-value, reference price, inventory state)
- **Price-dispersion scanners** (cross-venue same-instrument, funding dispersion, vol dispersion, aggregated sports
  books)
- **Protocol state watchers (DeFi)** (health factor, pool TVL/volume, oracle vs market, gas)
- **Event calendars** (macro, earnings, sports fixtures, crypto-specific)
- **Vol metrics** (IV surface fitter, realized vol, skew, percentiles)
- **Spread models** (rolling OLS, Kalman, cointegration, factor models)
- **Mempool** (pending swap watcher, oracle update pending — DeFi-specific)

Every signal source is a versioned artifact; strategy configs reference by explicit version.

**2. Edge Method** —
[axes/edge-methods.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/axes/edge-methods.md)
The rule for "when should this fire?" — turns a raw signal into a bet decision. Signal source produces data; edge method
decides whether to act on it. Catalog:

- **Value** (`model_prob > implied + threshold`) — ML Directional
- **Threshold-crossed** (rule fires when feature crosses) — Rules Directional
- **Rate-differential sustained** — Carry & Yield
- **Spread capture** (post liquidity, earn spread) — Market Making
- **Arbitrage** (dispersion > cost) — Arbitrage / Structural
- **Structural bonus** (protocol-paid) — Liquidation Capture
- **Z-score / mean-reversion** — Stat Arb (also some Rules)
- **Momentum / trend** — Rules Directional
- **Vol-metric dislocation** — Vol Trading
- **Surprise-magnitude × direction model** — Event-Driven

**3. Staking Method (Position Sizing)** —
[axes/staking-methods.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/axes/staking-methods.md)
How much to bet once the edge method has said "yes." Orthogonal to edge method. Catalog:

- **Fractional Kelly** (ML Directional; 0.25×/0.5×/1.0× multipliers)
- **Confidence-scaled** (ML with calibrated models)
- **Fixed % of equity** (Rules, Carry, many defaults; 1-3% sports, 5-15% continuous ML, 10-25% carry)
- **Fixed notional $** (Arbitrage per-opp, some Carry)
- **Vol-scaled** (Rules, TradFi equity)
- **Delta-neutral paired** (Carry basis, Stat Arb pairs)
- **Inventory-skewed** (Market Making)
- **Vega / Gamma notional cap** (Vol Trading, Options MM)
- **Tier-based (confidence × edge)**
- **Rank-weighted** / **Equal-weight** (Stat Arb Cross-Sectional)

Final size is always capped by
`min(staking_output, per_instrument_cap, family_cap, venue_account_headroom, post_kill_switch_reduction)`. Martingale
and Roll-up are explicitly unsupported (ruin risk).

**4. Venue Eligibility** —
[axes/venue-eligibility.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/axes/venue-eligibility.md)
The _slow-moving_ venue dimension — which venues a strategy is allowed to use, plus per-venue constraints. Fast-moving
pick (SOR at tick time) is execution-service's job. Config declares:

- **Venue set** (e.g., `BINANCE, OKX, BYBIT` or `UNISWAP_V3_ETHEREUM/ARBITRUM/OPTIMISM`)
- **Venue-specific constraints** (`max_notional_usd`, `min_liquidity_usd`, `fee_tier`, pool TVL / fee tier for DEXes)
- **Child-book eligibility** (Unity meta-broker: eligible list + preferred/avoid order)
- **Chain eligibility** (DeFi)
- **Credential + capability gating** (auto-filtered on missing secrets, adapter action support, venue capability
  registry)

Routing mode: `SOR_AT_EXECUTION` (fungible), `STRATEGY_PICKED` (non-fungible perps/options/sports lines), or
`META_BROKER` (Unity routes internally).

**5. Expression** —
[axes/expression.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/axes/expression.md)
How the view is translated into instruments actually traded. Independent of signal source and edge method — a value-edge
ML view can be expressed as spot OR perp OR ATM call OR 25-delta call. Catalog:

- **Cash-equivalent directional** : `SPOT`, `PERP`, `DATED_FUTURE`, `MARGIN`
- **Options** : `ATM_CALL/PUT`, `NDD_CALL/PUT` (25d/10d), `OTM_CALL/PUT`, `STRADDLE`, `STRANGLE`,
  `CALL_SPREAD/PUT_SPREAD`, `CALENDAR`, `BUTTERFLY`, `RISK_REVERSAL`, `IRON_CONDOR`
- **DeFi / on-chain** : `DEX_SWAP`, `LP_PASSIVE`, `LP_ACTIVE`, `LEND`, `BORROW`, `STAKE_LIQUID`, `STAKE_NATIVE`,
  `LEVERAGED_LENDING_LOOP`
- **Sports / prediction** : `BET_BACK`, `BET_LAY`, `BET_BACK_ARB_SET`, `BET_CLOB_YES/NO`
- **Synthetic / structured** : `SYNTHETIC_PERP_FROM_OPTIONS`, `SYNTHETIC_SPOT_FROM_PERP_FUNDING`, `BASKET`,
  `DELTA_HEDGED_OPTION`, `PAIRED_SPREAD`
- **`AUTO`** : execution picks optimal expression given conditions (rare)

Driven by capital efficiency, funding/borrow cost, convexity needs, share-class match, venue availability, regulatory,
expiry alignment, greek profile.

**6. Hold Policy** —
[axes/hold-policy.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/axes/hold-policy.md)
How long a position lives and what triggers its exit. Drives P&L attribution and fixes which exit mechanics the strategy
emits. Catalog:

- **`SAME_CANDLE_EXIT`** — entered + exited within same bar (ML Continuous with TP/SL). Never used on DeFi (gas +
  confirmation latency).
- **`HOLD_UNTIL_FLIP`** — held until signal flips / spread converges / funding flips (most ML Continuous, Rules
  trend-following, Carry, Stat Arb). Default for all DeFi.
- **`CONTINUOUS`** — always-on quoting; no entry/exit, inventory tilts around target (Market Making, LP).
- **`ONE_SHOT`** — fixed-rule unwind (Arbitrage, Liquidation, Event-Driven, event-settled ML/Rules, sports bets).
- **`EXPIRY_DRIVEN`** — lives until instrument expires (Vol Trading Options, Carry Basis Dated).
- **`CONVERGENCE_DRIVEN`** — closes when spread/residual converges to band (Stat Arb Pairs Fixed, some Cross-Sectional,
  basis arb variants).
- **`REBALANCE_DRIVEN`** — moving target, reconciled each rebalance tick; exits implicit when target weight → 0 (Stat
  Arb Cross-Sectional, Yield Rotation, LP allocation, allocator-directed).

**7. Share Class** —
[axes/share-class.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/axes/share-class.md)
The accounting currency for a strategy instance — denominator for all P&L, NAV, Sharpe, and allocation decisions.
**Structural per-instance field — not a config knob; different share class = different instance.** Supported:

- **Stablecoin** : `USDT`, `USDC`, `FDUSD`
- **Fiat** : `USD`, `GBP`, `EUR`
- **Crypto-native** : `ETH`, `BTC`, `SOL`

Chosen by venue margin unit, client mandate, fund structure, asset-native economics, regulatory context. Cross-currency
policy declared in config (`HEDGE_ON_ENTRY` / `HEDGE_ON_EXIT` / `ACCEPT` / `REBALANCE_PERIODICALLY`) — e.g., a
USD-share-class strategy running on USDT-margined Binance carries USD↔USDT basis risk explicitly handled per policy.

---

**Key composition rule across the axes:** they are orthogonal — signal source feeds into edge method, which triggers
staking method to size; expression picks the instrument; venue eligibility constrains where it can land; hold policy
controls life; share class is the accounting unit. Changing any one axis typically produces a new config hash but not
necessarily a new archetype.

# The 12 Cross-Cutting Docs

**1. Risk Gates (4-Layer Model)** —
[cross-cutting/risk-gates.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md)
Four risk enforcement layers between a strategy's emitted instruction and the actual venue order:

- **Layer 1 — Strategy self-check** (inside strategy-service): position delta sanity, config self-limits, per-instance
  kill-switch, share-class invariant, attestation presence. Failures → `REJECTED_SELF_CHECK`.
- **Layer 2 — Risk & Exposure service pre-flight** : portfolio-level guards across strategies (firm-wide
  instrument/venue concentration, client/fund limits, family-level caps like total vol-trading vega, correlation,
  regulatory, greek aggregates). Failures → `REJECTED_RISK`.
- **Layer 3 — Execution-service pre-trade** : venue-account feasibility (balance, margin, rate-limit headroom,
  credential freshness, venue capability, venue health). Failures → `REJECTED_EXECUTION` or `RESIZED_EXECUTION`.
- **Layer 4 — Venue-side risk (external)** : venue's own rules (margin/haircut, position limits, self-trade prevention,
  circuit breakers). Failures → `ORDER_REJECTED`.

**2. Venue Selection Split (slow eligibility + fast SOR)** —
[cross-cutting/venue-selection-split.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md)
Venue routing is split in two and never collapsed. **Slow path (strategy config):** eligible_venues list, per-venue
constraints, routing mode. **Fast path (execution, ms):** SOR picks among eligible based on best quote, net cost, venue
health, rate-limit headroom, real-time liquidity, MEV mode for DeFi. Three routing modes: `SOR_AT_EXECUTION` (fungible,
execution picks), `STRATEGY_PICKED` (non-fungible perps/options/sports lines — strategy names venue per instruction),
`META_BROKER` (Unity's own SOR picks child book).

**3. Execution Policies** —
[cross-cutting/execution-policies.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md)
A versioned, artifact-registered **rule table** mapping `(venue × action × condition) → (algorithm + parameters)`.
Strategies emit intent; policy picks the algo at order time. Lets strategy code stay stable while policy evolves
independently. Example policy has rules like "notional <
$50k → MARKET_SWEEP with 10 bps slippage cap", "$50k-$500k →
TWAP(10 slices, 300s, 20% participation)", "≥$500k → TWAP(30
slices, 1800s, 10%)". References a separate `cost_model_ref` and `benchmark_mode_ref`.

**4. Transfer / Rebalance** —
[cross-cutting/transfer-rebalance.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md)
The **venue scope** of capital movement — moves capital between venues within one strategy (or between subaccounts).
Does NOT move between strategies (that's Portfolio Allocator) or between clients (platform allocator). Triggers: drift
from allocation policy, scheduled cadence, operator command, allocator directive, post-fill imbalance. 7 transfer types:
`INTERNAL_SUBACCOUNT`, `CEX_WITHDRAWAL_DEPOSIT`, `ON_CHAIN_TRANSFER`, `BRIDGE` (Across/Stargate/LayerZero),
`WRAP_UNWRAP`, `UNITY_WALLET_OP`, `IBKR_FUND_MOVE`. Target-state protocol + idempotent by `instruction_id`; cost-aware
(gas, withdrawal fees, bridge fees, time-out-of-market).

**5. Portfolio Allocator** —
[cross-cutting/portfolio-allocator.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md)
The **strategy scope** of capital movement — decides how much equity each strategy instance gets, per client, per
cadence. Separate dedicated service (not inside strategy-service) because allocators are algorithms with their own
versioning/replay. Emits `AllocationDirective` events; strategies reconcile new equity and adapt positions. **8
allocator archetypes** : `FIXED`, `PNL_WEIGHTED`, `SHARPE_WEIGHTED`, `RISK_PARITY`, `KELLY`, `MIN_CVAR`, `REGIME_AWARE`,
`MANUAL` (human-in-loop approval). One archetype per client allocator instance — no composites.

**6. MEV Protection** —
[cross-cutting/mev-protection.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md)
DeFi-specific execution policy for routing transactions to avoid miner/validator extractable value (frontrunning,
sandwich, backrunning). Submission modes: `PUBLIC_MEMPOOL`, `FLASHBOTS_PROTECT`, `MEV_BLOCKER`, `MANIFOLD`,
`CUSTOM_PRIVATE_RPC` (Bloxroute explicitly removed — don't reintroduce). Policy mapping is versioned; example: Ethereum
≥$10k → FLASHBOTS_PROTECT, Ethereum <$10k → PUBLIC_MEMPOOL, L2s (Arbitrum/Optimism/Base/Polygon) → PUBLIC_MEMPOOL (less
MEV on L2). `LIQUIDATION_CAPTURE` has its own profile — we ARE the MEV bot.

**7. Benchmark Fills Contract** —
[cross-cutting/benchmark-fills.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md)
The contract that lets batch and live share one code path. Every algo exposes a `benchmark_fill()` that returns a
deterministic "zero market impact / zero timing alpha" fill. **Batch mode:** benchmark fills _replace_ real fills →
`exec_alpha = 0`. **Live mode:** benchmark fills computed _alongside_ real → `exec_alpha = real − benchmark` measurable
continuously. Strategy code, risk checks, position tracking, PBMS, allocator — all identical across modes. Per-algo
benchmarks: MARKET_SWEEP = mid at arrival, TWAP = time-weighted mid, VWAP = volume-weighted mid, QUOTE_LOOP = mid at
each update, MEV_PROTECTED_SWAP = pool mid at target block, ATOMIC_MULTI_LEG = sum of legs, etc.

**8. Capital / Client Isolation** —
[cross-cutting/capital-client-isolation.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/capital-client-isolation.md)
Guarantees one client's capital, credentials, risk, and audit state are fully isolated from another's. 10 isolation
dimensions: capital, credentials, configs, instructions, fills+P&L, risk, kill switches, audit, allocator, UI scope.
**Rule:** we face ONE client per strategy instance; a fund is a single client at our layer (investor-in-fund accounting
is the fund's responsibility). Credentials stored in Secret Manager keyed as
`trading/{client_id}/{venue}/{credential_type}` — fetched at runtime, injected via factory, reloaded via
`ApiKeyReloader`, never logged or emitted in events. Every venue account is a `(client_id, venue, account_id)` tuple;
PBMS never aggregates across client_id.

**9. Trade Expression (runtime machinery)** —
[cross-cutting/trade-expression.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/trade-expression.md)
The runtime side of the expression axis — how composite expressions are assembled/decomposed at execution time.
Single-leg expressions don't need this; the machinery kicks in for synthetics (long perp as `long call + short put`),
multi-leg (straddle), delta-hedged options, paired/basket, cross-venue assemblies (basis legs on two venues,
leader-hedge), and protocol composites (recursive staking, leveraged lending loops). Primitives: `ATOMIC` bundle (native
multi-leg where venue supports — Deribit multi-leg, Binance OCO, IBKR combo), `LEADER_HEDGE` bundle (cross-venue with
hedge deadline + `compensation_policy`), delta-hedge rider attachment to any option-bearing expression.

**10. Venue-Account Coordination** —
[cross-cutting/venue-account-coordination.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
Primitives for multiple strategies sharing a single venue account — avoids the one-strategy-per-account waste and
unlocks Binance cross-margin / Deribit portfolio margin / IBKR reg-T netting. **Three primitives:**

- **Aggregation (PBMS):** two orthogonal projections — per-strategy_instance_id logical positions AND per-(client,
  venue, account_id) actual positions; sum of strategy views must equal venue-account view (invariant), drift emits
  `VENUE_ACCOUNT_STRATEGY_SUM_DRIFT`.
- **Pre-flight:** Layer 3 simulates an instruction against current venue-account state (not just the emitting strategy's
  view) before venue submission.
- **Atomic rebalance:** multiple strategies can emit coordinated rebalances bundled as ATOMIC for the account.

**11. Futures Roll & Combos** —
[cross-cutting/futures-roll-and-combos.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/futures-roll-and-combos.md)
Applies to every archetype trading `dated_future` under the default rolling-continuous convention (ML continuous, rules
continuous, stat-arb pairs/cross-sectional, arbitrage price-dispersion, event-driven, basis-dated default). Does NOT
apply to `VOL_TRADING_OPTIONS` (expiry-aware by design) or to expiry-anchored instances using `-fixed-{contract}-` slot
labels. An **underlying** (e.g., `ES-USD-CME`, `BTC-USD-DERIBIT-DATED`) resolves deterministically at any instant to a
**representative future** via a `RepresentativeFutureRegistry` in UAC. When the representative changes, a single event
ripples to all subscribed strategies, which emit a roll instruction handled as a combo order (native-listed where
supported, synthesised otherwise). Liquidity feature group (OI, 24h volume, top-5 depth notional, expiry timestamp)
drives the roll decision.

**12. Strategy Availability & Locking** —
[cross-cutting/strategy-availability-and-locking.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
SSOT for how ONE combinatoric strategy universe powers both the **Strategy-as-a-Service (DIY client)** business and the
**Investment Management (fund)** business without code duplication. Same engines run for both; the difference is
**visibility + RBAC + lock state** . Every slot instance carries an `availability_state`:

- `PUBLIC` — SaaS catalog + IM + Admin can see; any DIY client or IM can allocate (default).
- `INVESTMENT_MANAGEMENT_RESERVED` — IM + Admin see; only IM allocates (prevents DIY piling on).
- `CLIENT_EXCLUSIVE` — IM (read-only) + Admin + Client X see; only Client X allocates (bespoke contract for its term).
- `RETIRED` — Admin only; nobody allocates; migration destination marked.

Bespoke variants create new `v{N}` slot instances while the base `PUBLIC` slot keeps running. Surfaces differ per actor:
Admin sees full universe with lock state overlay; DIY client sees only PUBLIC + their own CLIENT_EXCLUSIVE; IM desk sees
PUBLIC + RESERVED + read-only CLIENT_EXCLUSIVE.

---

**Shape of the set:** the 12 cross-cutting docs fall into three informal groups:

- **Runtime machinery** (risk-gates, execution-policies, benchmark-fills, trade-expression, venue-account-coordination,
  futures-roll) — how an instruction becomes a fill.
- **Capital plumbing** (transfer-rebalance, portfolio-allocator, capital-client-isolation) — how money moves and stays
  isolated.
- **Routing & governance** (venue-selection-split, mev-protection, strategy-availability-and-locking) — which venue,
  which submission mode, who can see/allocate.

# Root-Level Docs in architecture-v2

**1. MIGRATION.md** —
[MIGRATION.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/MIGRATION.md)
Complete audit of every legacy strategy doc, code module, and config mapped to its v2 placement. Status flags:
`✓ Mapped`, `~ Partial`, `+ Enhanced`, `R Retired`, `! Routing default`. Rule: if a legacy strategy isn't in this table,
it's a bug. Covers all 5 legacy category buckets — cefi, defi, sports, tradfi, prediction — mapping each doc to its
target archetype + example v2 slot labels. Key callouts: `defi/basis-trade.md`, `defi/btc-basis-trade.md`,
`defi/l2-basis-trade.md` all collapse to the same `CARRY_BASIS_PERP` archetype (they were always the same code,
different config); `defi/omnichain-transfers.md` moved out of strategies entirely — it is now the Transfer/Rebalance
service.

**2. naming-convention.md** —
[naming-convention.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/naming-convention.md)
SSOT for how a strategy is named everywhere — registry, records pipeline, UI URLs, audit logs. Three interlocking
identifier forms:

- **Slot label** (`ARCHETYPE@venue-asset-instrument-period-quote-env`) — e.g.
  `CARRY_BASIS_PERP@binance-eth-perp-10m-usdt-prod`
- **Fully-qualified** (`FAMILY.ARCHETYPE.slot_id`) — for UI URLs, admin surfaces, cross-references
- **Bare slot id** (`venue-asset-instrument-period-quote-env`) — when archetype/family already known from context

Family is never stored in the slot label — always derivable from archetype via `ARCHETYPE_TO_FAMILY`. Parser lives at
`unified_api_contracts.strategy.parse_strategy_id` / `format_strategy_id` / `ParsedStrategyId`. Raises `ValueError` on
unknown archetype/family.

**3. strategy-registry-v2.md** —
[strategy-registry-v2.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/strategy-registry-v2.md)
Documents the post-v1-delete shape of the strategy registry — the ONE place in Python that resolves
`strategy_id → (name, family, category, archetype)`. v1 `StrategyFamily` (17 values), `StrategyArchetype` (13 values),
and 55-entry `_DEFAULT_STRATEGIES` were deleted 2026-04-21. v2 registry is **derived, not hand-maintained** — generated
from `archetype_capability_manifest.json`, flattening the canonical archetype surface × their cells' representative slot
labels (originally sized for 18 archetypes / 96 entries on 2026-04-20; expanded by Phase 9 to 53, then to 55 by the
`CARRY_RECURSIVE_STAKED` split, then to **57** by the 2026-05-18 taxonomy decision — see UAC `StrategyArchetype` enum
SSOT; the manifest declares cells for a 22-archetype live subset today, the remainder await their cell declarations).
Public API signatures preserved so consumers need no call-site changes. Key v1→v2 field drift: `strategy_id` changed
from flat ID (e.g. `DEFI_ETH_BASIS_HUF_1H`) to slot-label grammar; `execution_mode`, `strategy_type`,
`default_timeframe` all removed (now archetype-derived).

**4. category-instrument-coverage.md** —
[category-instrument-coverage.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/category-instrument-coverage.md)
SSOT matrix: for every one of the 57 archetypes (originally 18 on 2026-04-20; expanded to 53 in Phase 9; then to 55 by
the `CARRY_RECURSIVE_STAKED` split; then to 57 by the 2026-05-18 taxonomy decision — 35+ new archetypes await their cell
declarations), every `(category, instrument_type)` cell is declared SUPPORTED / PARTIAL / BLOCKED / N/A with
representative venues, signal variant, gap reason, and fully-spelled slot-label examples. Category is always derived
from the execution venue — the same `ARBITRAGE_PRICE_DISPERSION` engine runs CeFi, DeFi, or Unity event-settled markets;
only venue params differ. As of 2026-04-20 snapshot: only `STAT_ARB_PAIRS_FIXED × CEFI × spot|perp` cells are `PUBLIC`;
all others default to `INVESTMENT_MANAGEMENT_RESERVED`. Key IM-reserved cells currently live: ML Directional Continuous
× CeFi (Jun 2026), ML Directional Continuous × TradFi dated futures (Sept 2026), Vol Trading Options × TradFi (Oct 2026
India options), ML Directional Event-Settled × Sports (Jun 2026, capacity-bound).

**5. uac-registry-gaps.md** —
[uac-registry-gaps.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/uac-registry-gaps.md)
12 additive UAC declarations needed to unblock cells in the coverage matrix — proposed in a single PR to avoid churn.
Key additions:

- `ArchetypeCapabilityV2` registry (lifts coverage matrix from markdown into queryable Python)
- `FlashLoanReceiverRegistry` (unblocks ARB × DeFi flash-loan)
- `LiquidationBonusScheduleV2` (precision for LIQUIDATION_CAPTURE risk gates)
- `EventCalendarSourceCapability` (unblocks EVENT_DRIVEN across all categories)
- `IvSurfaceFidelity` + option-venue extension (unblocks vol-arb cells, BL-1 partial)
- `MultiLegOrderCapability` (unblocks basket + options MM + combos)
- `RepresentativeFutureRegistry` + event (unblocks BL-10 dated-future auto-roll)
- `StrategyAvailabilityRegistry` + events (SaaS vs IM lock-state separation)

**6. block-list.md** —
[block-list.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/block-list.md)
Narrative + remediation for every `CoverageStatus = BLOCKED` cell in the coverage matrix. When a cell flips to BLOCKED,
a new `BL-N` section is authored here with affected cells, rationale, remediation, and owner — then mirrored into
`block-list.ts` for the UI coverage view at `/services/strategy-catalogue/coverage/blocked`. Example entries: `BL-1` —
no supported DeFi options venue (Lyra and Dopex archived 2026-03; evaluate Aevo, Premia, or Hegic); `BL-4` — Rules
Directional × DeFi × option (same root cause as BL-1).

**7. restriction-policy.md** —
[restriction-policy.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/restriction-policy.md)
Per-strategy-family × restriction matrix driving: (1) default lock-state for catalogue cells (IM reserve vs public), (2)
questionnaire-based demo filtering for prospects, (3) derivation surface the UI uses to render the catalogue under a
given persona. Most ~200 SUPPORTED/PARTIAL cells are `INVESTMENT_MANAGEMENT_RESERVED` by default — either running for IM
clients, slated for an IM mandate, or capacity-bound. Questionnaire-driven demo profiles narrow the visible set further
for unauthenticated/prospect audiences. Hard blocks (`BLOCKED` cells) are architecture/venue gaps, not commercial
reserves, and are in `block-list.md`.

**8. strategy-lifecycle-maturity.md** —
[strategy-lifecycle-maturity.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md)
9-phase forward-only maturity staircase + terminal `retired` state. Phases: `smoke` → `backtest_minimal` →
`backtest_1yr` → `backtest_multi_year` → `paper_1d` → `paper_14d` → `paper_stable` → `live_early` → `live_stable`.
Promotion gates enforced by admin editor: e.g. `paper_14d → paper_stable` requires ≥30d continuous paper fills with no
`STRATEGY_CIRCUIT_BREAKER` events; `live_early → live_stable` requires ≥30d live fills + Sharpe ≥ 1.0. Allocation CTA on
FOMO tearsheets only allowed for `paper_stable` or later. Every transition writes a `PhaseTransition` record with
from/to/at/by/reason. Also answers: who can see/subscribe to it (product routing), which venue-set variants it runs on,
and who runs it in paper mode (`odum-paper` client-zero for continuous P&L record).

**9. strategy-catalogue-3tier.md** —
[strategy-catalogue-3tier.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md)
Single shared `<StrategyCatalogueSurface viewMode=... />` component rendered into 4 view modes across 3 business tiers:

- **Tier 1 `admin-universe`** — read-only, all ~200-300 instances; admin + internal-trader + IM-ops
- **Tier 2 `admin-editor`** — allows maturity + routing mutations; admin + internal-trader
- **Tier 3a `client-reality`** — subscribed DART + IM clients; their running strategies only
- **Tier 3b `client-fomo`** — all entitled clients; `explore` tab with tearsheets + allocation request CTA for
  `paper_stable`+ instances

One component to keep visual grammar uniform across admin + client + IM surfaces.

**10. performance-overlay.md** —
[performance-overlay.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/performance-overlay.md)
`<PerformanceOverlay>` renders one strategy instance's continuous P&L timeline across three regimes on one chart:
**Backtest** (muted-blue, historical sim), **Paper** (`odum-paper` client-zero matching-engine fills, amber), **Live**
(real-venue fills, emerald). Three render modes: `overlay` (all three series, shared X — alpha-decay diagnosis),
`stitched` (one continuous line with regime transition markers — FOMO tearsheets), `split` (three stacked sub-charts —
IM allocator reports). Canonical colour mappings must not be rebranded by any surface consuming this component. Dashed
vertical markers at `paper_started_at` + `live_started_at` with phase-badge labels.

**11. dashboard-services-grid.md** —
[dashboard-services-grid.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/dashboard-services-grid.md)
SSOT for the 5-tile product-axis `/dashboard` grid. Separate from the top-nav (lifecycle axis). The 5 tiles: **DART**
(terminal, positions, orders, P&L, research, promote, observe, config), **Odum Signals** (external counterparty signal
broadcast, webhook/REST, HMAC-signed), **Coverage Explorer** (strategy universe + allocation matrix), **Reports** (P&L,
settlement, reconciliation, invoices, regulatory), **Manage** (clients, mandates, fees, compliance). Each tile has
entitlement gates, sub-routes as chips, and a padlock rendered if gate not met. Same `<ServiceTile>` primitive across
all 5 for uniform visual grammar.

**12. dart-tab-structure.md** —
[dart-tab-structure.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/dart-tab-structure.md)
SSOT for the authenticated shell navigation shape and DART sub-tab visibility per persona. The 8 historic lifecycle
stages collapsed to 4: `Data` (admin/internal only), `DART` (absorbs Research + Promote + Run + Execute + Observe +
Config — renamed from "Trading"), `Manage`, `Reports`. DART sub-tab catalogue: `research`, `promote`, `strategy-config`
(NEW), `execution-config` (NEW), `terminal` (repositioned — primary is Analytics + Reconciliation, Manual Execution is a
collapsed emergency-use secondary), `signal-intake`, `observe`, `deployment`, `reports-sub` (embedded). Sub-tab identity
is stable across personas; visibility is the axis that varies per entitlement.

**13. value-betting-archetype-decision.md** —
[value-betting-archetype-decision.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/value-betting-archetype-decision.md)
Decision record resolving the v1 `VALUE_BETTING` gap without adding a new archetype. **Decision:** value-betting is
`EdgeMethod.VALUE_PROB_VS_IMPLIED` attached to `ML_DIRECTIONAL_EVENT_SETTLED` — not its own archetype. Rationale: v2
already models it at the edge-method layer; strategy-service has run it this way since Phase 2; every value-bet strategy
uses a probability model, making it ML-directional by construction; risk-profile differentiation is handled by
`StakingMethod` (Fractional Kelly / Confidence-Scaled), not a separate archetype.

**14. tradfi-bond-instrument-type-decision.md** —
[tradfi-bond-instrument-type-decision.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/tradfi-bond-instrument-type-decision.md)
Decision record resolving the `TRADFI_BOND_MEAN_REV_HUF_1D` gap without adding a `bond` instrument type. **Decision:**
treasury ETFs (TLT, IEF, SHY) on IBKR are `spot` equities by instrument type — already covered by the existing
`STAT_ARB_PAIRS_FIXED × TRADFI × spot` cell. No new enum value needed because instrument types are execution-layer
categories, not asset-class labels. Actual CME Treasury futures (ZB/ZN/ZT) are `dated_future` — already supported. The
Wave-5 audit's verdict was wrong because it looked for a `(TRADFI, bond)` key which doesn't exist; the correct key
`(TRADFI, spot)` was already declared.

**15. legacy-family-migration.md** —
[legacy-family-migration.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/legacy-family-migration.md)
Audit report of all v1-era family strings (`basis-trade`, `mean-reversion`, `sports-arb`, `prediction-ml`) still in the
UI codebase as route slugs, filter values, or display labels. Completed migrations: `/basis-trade` → `/carry-basis`.
Deferred to Phase 11: 53-strategy fixture in `strategy-catalog-data.ts` (and 7 other mock/config files) still use v1
strings — bridged at read time via `LEGACY_FAMILY_TO_V2` map in `legacy-mapping.ts` rather than regenerating. Will be
deleted once Phase 11 (strategy fixture migration) lands and regenerates the catalog from UAC
`StrategyInstanceDefinition` rows.

**16. admin-registry-api.md** —
[admin-registry-api.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/admin-registry-api.md)
SSOT for three admin-only HTTP endpoints that let the UI `CatalogueTruthinessAdapter` reconcile UAC canonical lists
against what is actually registered in backend services at runtime:

- `GET /api/v1/registry/archetypes` — strategy-service; returns all archetypes with status (LIVE /
  PLANNED_NOT_IMPLEMENTED) and registered slot labels
- `GET /api/v1/registry/ml-models` — strategy-service; ML-directional subset
- `GET /api/v1/registry/features` — every features-\*-service; `FeatureGroupRegistry` per service key

All gated by `X-Admin-Token` HMAC-compared shared secret; services without the secret return `503` safe-by-default.

**17. dart-exclusive-research-fork.md** —
[dart-exclusive-research-fork.md](vscode-webview://09jfvupa03v4sfnuon9htjsoeab7rbdp72dj30bd86vckd3bkckv/unified-trading-system-repos/unified-trading-pm/codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md)
Design spec for DART exclusive subscriptions + client-authored research + version lineage. Three principles: (1)
**Exclusive ownership** — one DART client per strategy instance; no concurrent `dart_exclusive` subscriptions (IM
allocations and signals-in coexist because they consume differently); (2) **Client-authored research** — subscribed DART
client can modify config (thresholds, risk limits, ML-model variants, execution algos) and produce a draft version
inside the instance's version lineage — not a clone; (3) **Joint rollout decision** — Odum retains the rollout gate;
client drafts don't reach live trading until they pass the canonical backtest pipeline (at minimum `backtest_1yr`) AND
an Odum admin approves.

---

**Rough grouping of the root docs:**

- **Architecture decisions** (naming-convention, strategy-registry-v2, category-instrument-coverage, uac-registry-gaps,
  block-list, MIGRATION) — the canonical reference layer
- **Governance + access** (restriction-policy, strategy-lifecycle-maturity, strategy-catalogue-3tier,
  dart-exclusive-research-fork, admin-registry-api) — who sees/uses what and when
- **UI surfaces** (performance-overlay, dashboard-services-grid, dart-tab-structure) — what the platform looks like
- **Decision records** (value-betting-archetype-decision, tradfi-bond-instrument-type-decision, legacy-family-migration)
  — auditable "we considered X and decided Y"
