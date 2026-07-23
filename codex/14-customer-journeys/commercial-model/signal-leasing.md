---
doc_type: codex-ssot
title: Signal Leasing
summary:
  Signal-leasing commercial path (fourth path beyond DART/IM/Reg Umbrella) — Odum sells strategy signal output to
  counterparties who self-execute; four candidate pricing models (recommended hybrid — £10-20k/mo floor + per-signal
  uplift + optional 5% P&L share), only non-IM_RESERVED cells, £4k/mo Sept-2026 anchor.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [admin, sales]
tags: [commercial-model, signal-leasing, pricing, dart, strategy, revenue]
related:
  [
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/commercial-model/revenue-projection-2026-monthly.md,
    ../shared-core/signal-broadcast-architecture.md,
  ]
created: 2026-04-20
authoritative_for: [signal-leasing commercial path (fourth path, pricing models)]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/elysium-account-trajectory-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/revenue-projection-2026-monthly.md,
    /codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Signal Leasing

> Monthly licence model for leasing Odum-generated strategy signals to institutional counterparties. Distinct from DART
> signals-only (which is client sending instructions to Odum) and from IM (which is Odum running strategies on allocated
> capital). Signal leasing = Odum sells the _output_ of its strategies.

**Rule sources:** [rule 04](../_ssot-rules/04-dart-commercial-axes.md) — outside the 2×3 matrix; signal leasing is a
separate commercial path; [rule 07](../_ssot-rules/07-data-licensing-boundaries.md) — signal output IS an Odum-enriched
service, not raw data; [rule 08](../_ssot-rules/08-pricing-principles.md) — Tier B default because signal leasing
involves commitment.

## What signal leasing is

**Odum sends strategy-level signals** (long / short / position-size indicators on specific instruments) to a
counterparty. The counterparty executes on their own infrastructure. Odum does NOT see their execution, their positions,
their fills.

This is **Odum output**, not Odum execution. Commercially similar to a premium research subscription but with signals
designed for direct position-taking, not discretionary interpretation.

**What it is NOT:**

- **NOT DART signals-only** (rule 04 `(Client, downstream)`) — that's the reverse: client signals → Odum execution.
- **NOT IM** — Odum does not manage capital; counterparty manages their own.
- **NOT raw data resale** (rule 07) — signals are Odum-enriched; the client buys the enriched output, not the data
  feeding it.
- **NOT analytics pack resale** — block 11 is about analytics ON a client's own flow. Signal leasing is a different
  product entirely.

## Pricing model — TBD / pending user confirmation

Three candidate structures. User to confirm which (or a hybrid):

### Option 1 — Monthly licence flat

Fixed monthly fee per counterparty × signal-scope.

| Scope                                                                     | Monthly licence (Tier B)     |
| ------------------------------------------------------------------------- | ---------------------------- |
| Single signal family (e.g. BTC ML directional signals only)               | $15-25k/mo per counterparty  |
| Bundled multi-family (e.g. BTC ML + S&P ML + sports ML)                   | $35-60k/mo per counterparty  |
| Full signal catalogue (every Odum strategy that is externally-licensable) | $75-120k/mo per counterparty |

**Pros**: predictable revenue; clean accounting; counterparty pays for the option to act on signals regardless of how
they use them. **Cons**: counterparty can consume signals without deploying capital → no upside for Odum. Flat caps the
upside when the counterparty scales.

### Option 2 — Per-signal metering

Metered per signal-delivered or per signal-acted-upon.

| Metric                                                               | Tier A-ish price                    |
| -------------------------------------------------------------------- | ----------------------------------- |
| Per signal delivered (signal emitted to counterparty's endpoint)     | $50-200 per signal                  |
| Per signal acted upon (counterparty confirms they took the position) | $500-2k per executed signal         |
| Per basis point of P&L (requires client reporting back)              | Typically not workable commercially |

**Pros**: aligns revenue with counterparty's actual usage. **Cons**: hard to audit; counterparty has incentive to
under-report; clunky for low-frequency strategies where signals are rare and high-value.

### Option 3 — Revenue share on counterparty's P&L (upside-aligned)

Odum takes a small percentage of the counterparty's P&L attributable to Odum signals.

| Structure                                       | Tier B                             |
| ----------------------------------------------- | ---------------------------------- |
| 5-10% of counterparty's signal-attributable P&L | Requires trust + audit rights      |
| + floor monthly licence ($5-15k/mo)             | Ensures revenue even in flat years |

**Pros**: full alignment with counterparty's success; upside capture. **Cons**: requires counterparty to share P&L and
attribution data; trust-dependent; audit mechanics add friction.

### Option 4 — Hybrid (recommended if no clear preference)

- **Floor monthly licence** ($10-20k/mo per counterparty, covers shared platform costs)
- **Per-signal uplift** ($25-100 per signal delivered on high-signal-count strategies, $200-500 on sparse strategies)
- **Optional P&L share** (5% on counterparty's signal P&L, with audit rights) as a Tier B upsell

The hybrid gives revenue certainty (licence floor), captures usage scaling (per-signal), and has upside via optional P&L
share. Easiest to pitch because each component justifies itself.

## Which signals are licensable

Only signals from strategies that are NOT IM_RESERVED for Odum's own use can be externally licensed. Per the rule-06
show/don't-show principle, signal leasing a strategy Odum is running for its own IM would reveal Odum alpha to the
counterparty — effectively competing against ourselves.

Licensable today (per the strategy-allocation-lock-matrix):

- Mean-reversion (STAT_ARB_PAIRS_FIXED × crypto) — PUBLIC → potentially licensable

Licensable after IM-reserved exemption granted:

- Specific archetype × instrument × venue combinations that Odum is comfortable sharing _because_ they're not Odum's
  primary mandate. Decision per-cell by commercial leadership.

**Default posture**: signal leasing starts narrow (1-2 cells max per counterparty) and expands only where explicit
commercial approval is granted. Avoid leasing core Odum alpha.

## Per rule 04 / rule 07 framing

Signal leasing fits inside the `investor-platform` + institutional-allocator space but is a **fourth commercial path**
alongside DART, IM, Reg Umbrella. It does not fit cleanly into the rule-04 matrix because it's output-only.

Treat as a **fourth path** in commercial-model docs when relevant. When it appears alongside rule-04 paths, label it
"Signal Leasing" explicitly.

## Deck framing (per path-to-$100M plan-presentation)

The deck (`plan-presentation/data.ts`) frames signal leasing as a third-revenue-line alongside platform clients +
regulatory coverage. Consistent with that framing:

- End 2026: 2 signal-leasing counterparties in active conversations (per deck).
- End 2027: signal leasing expanded.
- End 2028: signal leasing revenue stream established.

## 2026 concrete anchor (locked 2026-04-20)

**Go-live: September 2026. Two counterparties interested, ~$5k/month combined (≈£4k/mo).** Revised down from the initial
£12-24k/mo modelling — reflects commercial reality of the first two deals being narrow-scope prove-out rather than
full-catalogue bundles.

|                          | September 2026 onwards |
| ------------------------ | ---------------------- |
| # counterparties live    | 2                      |
| Combined monthly revenue | ~$5k (≈£4k)            |
| Per-counterparty average | ~$2.5k / ≈£2k          |

**Scope at launch** is narrow per counterparty — likely single-signal-family or minimal-schema. The pricing scales up
with:

- Bundle expansion (adding more signal families) → $15-25k/mo/counterparty per the pricing anchors below
- Schema depth increase (minimal → standard → rich)
- Additional counterparties (the plan-presentation deck frames 2026 as "2 counterparties in active conversations"; this
  anchor reflects that commitment converting to paying engagements)

**Pricing anchors for future deals (post-launch bundle expansion):**

|                                                         | Conservative | Target    | Upside     |
| ------------------------------------------------------- | ------------ | --------- | ---------- |
| £/month per counterparty (hybrid model, expanded scope) | 10           | 15        | 25         |
| **Bundle-expansion revenue potential end-2027**         | **20/mo**    | **45/mo** | **100/mo** |

**Within the 2026 monthly revenue projection**, signal leasing now modelled at **£4k/mo from Sept 2026** (flat for
Sept-Dec). This ties to the ~£35k year-end cash-projection revision per
[`revenue-projection-2026-monthly.md`](revenue-projection-2026-monthly.md).

**Backend enablement**: external broadcast mechanism requires the cross-repo refactor tracked in
[`../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md`](../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md).
The $5k/mo revenue is gated on that refactor landing before Sept 2026. Architecture implementation map (D1–D10, failure
isolation, auth model, transport, observability) is in
[`../shared-core/signal-broadcast-architecture.md`](../shared-core/signal-broadcast-architecture.md).

## Operational mechanics

Signal delivery:

- Signal emission: from `strategy-service` via `STRATEGY_SIGNAL_EMITTED` UTL event.
- Delivery channel: counterparty-chosen (webhook, signed JSON, message bus). Authenticated + rate-limited.
- Latency SLA: per-strategy cadence (1-minute for ML directional; hourly for DeFi; event-settled for sports).
- Delivery log: every signal delivered is logged for metering + audit.

Counterparty integration:

- One-time integration (webhook setup + auth + test signal flow) — can price as block-13 custom premium if counterparty
  wants a custom delivery channel.
- Standard webhook / signed-JSON channel comes included in the licence.

## Follow-ups

- User to confirm which pricing model (1/2/3/4) applies. Current recommendation: **Option 4 hybrid**.
- Follow-up item in roadmap: formalise signal-licensing terms (data rights, audit rights, resale prohibition) in a
  standard legal template.
- Stage 3E refactor item: signal-emission eventing pipeline with metered audit log.

## Cross-references

- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md) — signal leasing sits outside the 2×3
  matrix as a fourth path
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) — signals are enriched output,
  not raw data
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — Tier B default
- [pricing-building-blocks.md](pricing-building-blocks.md) — pricing rows for signal leasing (new, TBD)
- [im-profit-share-structures.md](im-profit-share-structures.md) — IM is distinct commercial mechanic
- [../shared-core/strategy-allocation-lock-matrix.md](../shared-core/strategy-allocation-lock-matrix.md) — which
  strategies are licensable
- [../shared-core/signal-broadcast-architecture.md](../shared-core/signal-broadcast-architecture.md) — implementation
  map (D1–D10, failure isolation, auth, transport, observability)
- [revenue-projection-2026-monthly.md](revenue-projection-2026-monthly.md) — signal leasing lines in 2026 model
- [`../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md`](../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md)
  — plan SSOT
