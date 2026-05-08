# Odum × POD — Synergy Memo

**To:** Patrick Lynch (CEO), Cathal Hardiman (CCO), Timo Neumann (CTO) — POD **From:** Iggy Ikenna — Odum Research /
Unified Trading System **Re:** Where our stacks complement, and three integration shapes worth a call

---

## The thesis in one line

POD is the regulated _fund operating system_; Odum is the regulated _trading operating system_. The seam is clean — POD
doesn't generate alpha, Odum doesn't issue fund shares — and the two together are the only crypto-native vehicle that
solves both allocator gates (regulated wrapper **and** verifiable, fully-attributed track record) in one product.

---

## What Odum brings (the alpha + transparency layer)

- **13 implemented strategy archetypes** with live-data tracers running against real 2025 on-chain + venue data
  (CARRY_RECURSIVE_STAKED, REBASING_YIELD, ARBITRAGE_PRICE_DISPERSION cross-venue & cross-chain, LIQUIDATION_CAPTURE,
  TARGET_UNIVERSE_REBALANCE, etc.). Recent results: ankrETH 9.45% net APR @ 6.67× lev with EigenLayer overlay; BTC
  funding-arb 35.72% book weight; LIQUIDATION_CAPTURE 736 events captured 2025-06-15..21. Catalogue:
  [`codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`](../../codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md),
  archetype index:
  [`codex/09-strategy/architecture-v2/archetypes/`](../../codex/09-strategy/architecture-v2/archetypes/).
- **9-factor PnL attribution** that decomposes carry into CARRY*BASE / CARRY_AVS_CONTINUOUS / CARRY_ISSUER_SEASONAL /
  REWARD_REALISATION_SLIPPAGE etc., with matching-engine-simulated execution-alpha separated from strategy-alpha so
  allocators see \_why* the NAV moved, not just _what_ it moved to. SSOT:
  [`codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`](../../codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md).
  Restaking economics SSOT:
  [`codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`](../../codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md).
- **Unified pipeline (batch = live)** — strategy, position, risk, execution all share one code path; the only seam is
  fill source (matching engine vs venue). Architecture:
  [`codex/04-architecture/batch-live-symmetry.md`](../../codex/04-architecture/batch-live-symmetry.md).
- **Asset-group breadth Haruko doesn't cover** — alongside CeFi/DeFi we already run sports, prediction markets, TradFi
  (ES futures + options chains + spot ETFs). Same taxonomy, same PnL attribution, same regulated-wrapper-ready output.
- **Three-tier prospect funnel already collecting allocator-grade DDQ data** — Briefings → Strategy Evaluation (8-step,
  100+ fields) → Strategy Review. Shipping at [odum-research.com](https://www.odum-research.com):
  `/strategy-evaluation`, `/strategy-review`, `/platform`, `/investment-management`, `/regulatory`.
- **Existing IR deck on the regulatory umbrella thesis** — ours:
  [`presentations/06-regulatory-umbrella.html`](../06-regulatory-umbrella.html). It's the gap POD fills natively.

## What POD brings (the wrapper + distribution layer)

- BVI SPC + Segregated Portfolio sub-funds, regulated investment manager overlay, Central-Bank-of-Ireland on-chain fund
  admin.
- Fund launch cost compressed from ~$185k → ~$10k Year-1; variable-only pricing aligns POD with manager success.
- NeoBank-grade investor app (paperless KYC, fiat & stablecoin subscriptions, daily dealing, atomic settlement).
- Banking + custody commercial relationships at SPC scope (Bank Frick, Coinbase Prime, Ceffu, Copper) that we currently
  credential per-client.

---

## Three integration shapes worth a call

### A. Mutual referral _(your initial framing)_

Odum-graduated managers route to POD for the SPC + admin; POD-onboarded managers route to Odum for DART + strategy
modules + PnL attribution. Plug-in points: terminal step of
[`/strategy-evaluation`](https://www.odum-research.com/strategy-evaluation) on our side; "Strategy / Tech Partners" in
POD's onboarding flow. **Lowest integration cost, lowest commercial upside.**

### B. Embedded — POD UX hosts Odum capabilities

- Odum's PnL attribution runs underneath POD's Fund Manager App, so every NAV ships with auditable factor decomposition
  (immediate differentiation vs every other crypto fund admin).
- Odum's strategy archetypes appear as opt-in "alpha modules" inside POD — emerging managers pick a fund structure _and_
  a strategy template in one flow.
- Odum's UAC `EventEnvelope` topics extend to `pod.fund.*` events so a manager running DART + booking through POD has
  one unified event log end-to-end. UAC SSOT: [`unified-api-contracts`](../../../unified-api-contracts) (Wave A
  foundations recently shipped).

### C. Embedded — Odum UX hosts POD fund creation

- POD fund creation lives inside DART's Strategy Evaluation completion path; the 100+ DDQ fields we already collect
  pre-warm POD's KYC + fund-creation flow.
- POD's SPC appears as a _settlement venue_ in Odum's `instruments-service` / `execution-service` — DART strategies
  route fills into the manager's POD sub-fund natively.

---

## Commercial sketch (placeholder, to discuss)

Your model: $8k setup + 5–25% of management + performance fees the fund manager pays POD. Suggested mirror: a fixed
share of _POD's_ 5–25% slice for managers Odum routes who run on DART for strategy/execution — tying our number to
lifetime value rather than a one-shot intro fee. Inverse on POD-originated managers we onboard for tech.

This avoids a flat referral-fee schedule and lets each side keep its variable-only pricing posture intact.

---

## Asks for the first call

1. Confirm whether shape **A**, **B**, or **C** fits POD's current roadmap pressure.
2. Walk us through the regulatory line you draw between POD-as-investment-manager and a tenant manager's strategy IP. We
   need to understand where Odum's strategy modules sit in your sub-fund governance before we can scope shape B/C.
3. Asset-group expansion appetite: would POD entertain holding sports / prediction-market / TradFi exposure inside the
   SPC structure if Odum carries the operational + reporting load? This is greenfield no other counterparty can offer.

---

## Reference set (for due diligence)

| Topic                                | Source                                                                                                                                                                                                                                                                                                                                                     |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Strategy archetype catalogue         | [`unified-trading-pm/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`](../../codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md)                                                                                                                                                                                                  |
| PnL attribution (9-factor)           | [`unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`](../../codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md)                                                                                                                                                                                                                        |
| Restaking reward economics           | [`unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md`](../../codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md)                                                                                                                                                                                                  |
| Capital structure & regulatory model | [`unified-trading-pm/codex/04-architecture/capital-structure-and-regulatory.md`](../../codex/04-architecture/capital-structure-and-regulatory.md)                                                                                                                                                                                                          |
| Batch = Live unified pipeline        | [`unified-trading-pm/codex/04-architecture/batch-live-symmetry.md`](../../codex/04-architecture/batch-live-symmetry.md)                                                                                                                                                                                                                                    |
| Regulatory umbrella IR deck          | [`unified-trading-pm/presentations/06-regulatory-umbrella.html`](../06-regulatory-umbrella.html)                                                                                                                                                                                                                                                           |
| Strategy white-labelling IR deck     | [`unified-trading-pm/presentations/03-strategy-white-labelling.html`](../03-strategy-white-labelling.html)                                                                                                                                                                                                                                                 |
| Investment management IR deck        | [`unified-trading-pm/presentations/05-investment-management.html`](../05-investment-management.html)                                                                                                                                                                                                                                                       |
| Public funnel                        | [odum-research.com/strategy-evaluation](https://www.odum-research.com/strategy-evaluation), [/strategy-review](https://www.odum-research.com/strategy-review), [/platform](https://www.odum-research.com/platform), [/investment-management](https://www.odum-research.com/investment-management), [/regulatory](https://www.odum-research.com/regulatory) |
