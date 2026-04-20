# Strategy Origin × Stack Depth — The DART Commercial Matrix

> Implementation reference for [rule 04](../_ssot-rules/04-dart-commercial-axes.md). Worked examples, per-cell
> commercial mapping, and the demo-restriction profile each cell resolves to.

**Rule source:** [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md)

## The two axes, restated

Every DART engagement resolves on two independent axes. Every commercial conversation must resolve both axes before
pricing is discussed.

**Axis 1 — Strategy origin.** Whose strategy is being run?

- **Odum strategy** — Odum-developed, Odum-run systematic strategy. Odum owns the IP.
- **Client strategy** — Client-developed strategy. Client retains IP. Strategy generation (regime classification, signal
  generation, allocation logic) happens outside Odum.

**Axis 2 — Stack depth.** How much of the Odum operating stack is the client buying?

- **Reporting-only visibility** — reporting surface only. Closer to IM or Reg Umbrella than true DART.
- **Client strategy + downstream integration** — client keeps strategy generation upstream; Odum runs execution, trading
  terminal, position monitoring, reconciliation, and scoped analytics.
- **Full DART pipeline** — the deeper stack including research, backtest, promote, execute, trade, observe.

## The 2 × 3 matrix

```
                        │  Reporting-only     │  Client strategy +         │  Full DART pipeline
                        │  visibility         │  downstream integration    │
────────────────────────┼─────────────────────┼────────────────────────────┼───────────────────────────
Odum strategy origin    │ [IM / Reg Umbrella] │ [Rare]                     │ [DART + Odum exposure]
                        │                     │                            │
Client strategy origin  │ [Rare]              │ [DART signals-only]        │ [Full DART build/run]
```

## Cell-by-cell resolution

| Cell                       | Practical path                           | Commercial home                                                                                      |
| -------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `(Odum, reporting-only)`   | Route to IM or Reg Umbrella              | [pb2a](../experience/im-decision-journey.md) / [pb2c](../experience/regulatory-umbrella-briefing.md) |
| `(Odum, downstream-only)`  | Rare; usually collapses to full-pipeline | Escalate to leadership; default to `(Odum, full)`                                                    |
| `(Odum, full-pipeline)`    | DART client with Odum strategy exposure  | Full DART pricing + Odum strategy premium                                                            |
| `(Client, reporting-only)` | Rare; usually Reg Umbrella               | Route to Reg Umbrella                                                                                |
| `(Client, downstream)`     | Signals-only DART                        | [pb2b](../experience/dart-briefing.md) signals-only path; rule 10 fit-check                          |
| `(Client, full-pipeline)`  | Full DART build-and-run                  | [pb2b](../experience/dart-briefing.md) full path                                                     |

## Three practical paths that sell

Collapsing the matrix to the three cells that produce engagements:

1. **Reporting-only visibility** → IM or Reg Umbrella entry points. Not DART commercially.
2. **`(Client, downstream)` = signals-only DART** — client keeps the edge upstream; Odum runs the downstream stack. Rule
   10 fit-check runs before any demo. Block composition: reporting core + strategy-service entry + instructions
   integration + execution layer + venue/chain/instrument-type packs + scoped analytics. No research/promote pipeline
   (block 6 excluded).
3. **Full DART pipeline** — `(Client, full)` or `(Odum, full)`. The richer engagement. Adds block 6 (research/promote
   pipeline). Odum strategy exposure lives here when present, priced as a premium.

## Worked examples

### Example 1 — DeFi stat-arb fund

**Situation:** Fund has a working stat-arb strategy on their own infrastructure. Hits operational limits: venue
onboarding, cross-chain treasury rebalancing, regulatory cover, monitoring fragility.

**Axis resolution:** Strategy origin = client; stack depth = downstream integration.

**Cell:** `(Client, downstream)` → signals-only DART.

**Blocks:** reporting core + strategy-service entry + instructions integration + execution layer + venue packs (their 3
primary venues) + chain packs (their 2 primary chains) + instrument-type packs (perps + spot). Analytics pack optional.

**Pricing shape:** Tier B on sticky blocks (reporting, strategy-service, instructions); Tier A on marginal venue packs.

### Example 2 — Family office wanting Odum-run exposure

**Situation:** Allocator evaluating Odum as a manager. Wants to allocate capital; not operate infrastructure.

**Axis resolution:** Strategy origin = Odum; stack depth = reporting-only.

**Cell:** `(Odum, reporting-only)` → route to IM, not DART.

**Commercial home:** IM briefing (pb2a) + IM demo (pb3b). DART pricing and demo profile do not apply.

### Example 3 — Emerging manager launching under regulated cover

**Situation:** Manager wants regulatory cover, execution infrastructure, and reporting. Retains some strategy
discretion.

**Axis resolution:** Strategy origin = client; stack depth = downstream integration (hybrid with reg cover).

**Cell:** `(Client, downstream)` + Reg Umbrella composition. Two commercial engagements with shared infrastructure.

**Blocks:** regulatory umbrella reporting + reporting core + strategy-service entry + instructions integration +
execution layer + relevant venue/instrument-type packs.

### Example 4 — Prop firm buying Odum strategy IP + running it themselves

**Situation:** Firm wants to run Odum-developed strategies on their own capital with Odum's infrastructure.

**Axis resolution:** Strategy origin = Odum; stack depth = full-pipeline.

**Cell:** `(Odum, full)` → Full DART + Odum strategy premium. This is NOT a lighter package; it's full DART pricing with
the Odum-strategy exposure priced on top.

### Example 5 — DAO wanting systematic yield rotation

**Situation:** DAO wants yield rotation across DeFi protocols plus reporting for members.

**Axis resolution:** Strategy origin = Odum (DAO is buying exposure); stack depth = reporting-only.

**Cell:** `(Odum, reporting-only)` → Route to IM with DeFi flavour.

## Mapping to demo restriction profiles

Each cell resolves to a default restriction profile (see
[`../demo-ops/demo-restriction-profiles.md`](../demo-ops/demo-restriction-profiles.md)).

| Cell                              | Default restriction profile                                                                               |
| --------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `(Odum, reporting-only)`          | IM default profile (pb3b) — catalogue of IM-available slots + reporting; research/promote HIDDEN-ENTIRELY |
| `(Client, downstream)`            | signals-only DART — execution + strategy-service + reporting unlocked; research/promote LOCKED-VISIBLE    |
| `(Client, full)` / `(Odum, full)` | full DART — everything unlocked (catalogue + research + promote + execution + reporting)                  |

Demo mode (broader-platform / turbo / deep-dive — see
[`../demo-ops/dart-demo-modes.md`](../demo-ops/dart-demo-modes.md)) layers on top; cell resolves the restriction, mode
resolves the breadth of walk-through.

## Edge cases

- **Hybrid engagements.** A prospect spans two cells (Reg Umbrella + signals-only DART). Handle as two commercial
  engagements with shared infrastructure; do not try to collapse.
- **Build-for-client.** Odum builds a strategy to client spec and runs it on the client's capital. Strategy origin =
  Odum (Odum built it); stack depth = full-pipeline. Sits in `(Odum, full)` with a build-engagement upfront premium.
- **Strategic partnership.** Genuine co-development. Doesn't fit the matrix cleanly; bespoke, leadership signoff.
- **Non-compete / exclusivity.** A modifier on Tier B blocks, not a separate cell (see rule 05 block 12, rule 08
  exclusivity principles).

## Relationship to rule 10 (signals-only schema)

`(Client, downstream)` is the cell rule 10 guards. The instruction-schema fit-check determines whether the prospect's
upstream can produce the eight required fields. If yes, they fit signals-only; if no, they are either full-DART (Odum
runs the upstream too) or bespoke (custom premium block 13). Rule 10 is the fit-check layer; this doc is the commercial
matrix underneath.

## Cross-references

- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — the blocks each cell composes
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — tier assignment per block
- [rule 10 — strategy instruction schema](../_ssot-rules/10-strategy-instruction-schema-principles.md) — fit-check for
  `(Client, downstream)`
- [instruction-schema-fit-and-package-boundaries.md](instruction-schema-fit-and-package-boundaries.md) — rule 10
  implementation
- [../experience/dart-briefing.md](../experience/dart-briefing.md) — pb2b briefing that walks this matrix
- [../experience/dart-demo.md](../experience/dart-demo.md) — pb3c demo scoped per resolved cell
- [../commercial-model/dart-entry-points.md](../commercial-model/dart-entry-points.md) — commercial-facing expansion
- [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md) — profile per cell
