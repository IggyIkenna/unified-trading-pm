---
doc_type: codex-ssot
title: Rule 04 — DART commercial axes
summary:
  "DART commercial resolution — two axes (strategy origin: Odum/client × stack depth: reporting-only/downstream/full)
  collapse to three practical paths, plus the fourth outbound Odum-Signals path; the resolved cell drives pricing, demo
  scope, and prod restrictions."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin, sales]
tags: [customer-journey, sales, dart, cost, strategy]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md,
    /codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md,
    /codex/14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md,
    /codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md,
  ]
created: 2026-04-19
authoritative_for: [DART commercial axes (strategy-origin × stack-depth resolution)]
referenced_by:
  [
    /codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md,
    /codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md,
    /codex/14-customer-journeys/_ssot-rules/09-internal-commercial-oneliners.md,
    /codex/14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md,
    /codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md,
    /codex/14-customer-journeys/_ssot-rules/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 04 — DART commercial axes

> Two axes, three practical paths. Every DART commercial engagement resolves to (strategy origin × stack depth). All
> pricing, demo scope, and production restrictions follow from that resolution.

**Source:** [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On DART commercial model (rule 04)". User directive
2026-04-19 simplified the earlier 3-path framing into a 2-axis matrix with 3 derived paths.

## The two axes

### Axis 1 — Strategy origin

Whose strategy is being run?

- **Odum strategy** — Odum-developed, Odum-run systematic strategy. Lives in the Odum strategy catalogue. Strategy IP =
  Odum's.
- **Client strategy** — Client-developed strategy. Client retains IP. Strategy generation (regime classification, signal
  generation, allocation logic) happens outside Odum; client sends instructions in.

### Axis 2 — Stack depth

How much of the Odum operating stack is the client buying into?

- **Reporting-only visibility** — Client uses reporting surface only. Closer to regulatory or investor-relations access
  than true DART. Often a Reg Umbrella or IM entry point in disguise.
- **Client strategy + downstream integration** — Client keeps strategy generation upstream. Odum provides execution,
  DART trading terminal, position monitoring, reconciliation, and selected analytics to the extent the client's
  instruction schema supports them. Does NOT include the richer research / backtest / promote layer.
- **Full DART pipeline** — Client buys into the deeper stack: enriched data services, research, backtesting, promotion,
  execution, trading, observation. Odum strategy exposure, if offered, sits here.

## The 2 × 3 matrix

```
                        │  Reporting-only     │  Client strategy +         │  Full DART pipeline
                        │  visibility         │  downstream integration    │
────────────────────────┼─────────────────────┼────────────────────────────┼───────────────────────────
Odum strategy origin    │ [IM / Reg Umbrella] │ [Rare]                     │ [DART + Odum exposure]
                        │                     │                            │
Client strategy origin  │ [Rare]              │ [DART signals-only]        │ [Full DART build/run]
```

### Cell-by-cell meaning

- **(Odum, reporting-only)** → this is really IM or Reg Umbrella, not DART. Route the prospect there.
- **(Odum, client-strategy+downstream)** → rare. Odum running its own strategy but only handing out execution
  integration? Unusual; usually collapses to full-DART when interrogated.
- **(Odum, full-pipeline)** → DART client wants Odum strategy exposure as part of the engagement. Sits in full DART, not
  a lighter package. Prevents "I'll take your strategy but skip your research stack" pricing leakage.
- **(Client, reporting-only)** → rare. If the client has their own strategy and only wants reporting, they're closer to
  a Reg Umbrella engagement; handle accordingly.
- **(Client, client-strategy+downstream)** → the **signals-only** DART path. Client keeps their edge upstream; Odum runs
  the downstream operational layer. See rule 10 (`strategy-instruction-schema-principles.md`) for the schema and
  fit-check logic.
- **(Client, full-pipeline)** → client builds and runs on Odum infrastructure top-to-bottom. Research, backtest,
  promote, execute, trade, observe — all on Odum's stack.

## The three practical commercial paths

Collapsing the matrix to the three cells that actually sell:

1. **Reporting-only visibility** — map to IM or Reg Umbrella entry points. Not a DART path in the commercial sense.
2. **Client strategy + downstream integration** (signals-only DART) — `(Client, downstream)` cell. The most common "DART
   lite" engagement.
3. **Full DART pipeline** — `(Client, full)` or `(Odum, full)` cell. The richer engagement. Odum strategy exposure, when
   present, sits here.

## Fourth path — Odum Signals (outbound, NOT DART)

Signal Leasing is a **fourth commercial path** that sits alongside — but outside — the DART matrix above. Direction is
inverted: Odum emits strategy-level position/directional signals to authenticated counterparty endpoints who execute on
their own infrastructure. No capital flows; Odum does not see counterparty fills.

Because the direction is outbound (Odum → counterparty) rather than inbound (client → Odum), it does not resolve to a
cell in the (strategy origin × stack depth) matrix. Keep it as a separate commercial path to avoid pricing-leakage
confusion with the `(Client, downstream)` signals-only DART cell, which is inbound.

- Commercial framing: `commercial-model/signal-leasing.md`
- Architecture: `shared-core/signal-broadcast-architecture.md`
- Plan of record: `plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md`

## Worked examples

### Example 1 — DeFi-native hedge fund with a live stat-arb strategy

**Context:** The fund has a working stat-arb strategy running on their own infrastructure. They've hit operational
limits: venue onboarding, treasury rebalancing across chains, regulatory cover, monitoring fragility.

**Axis resolution:** Strategy origin = client. Stack depth = client-strategy+downstream-integration (they want
execution, treasury, observability, reporting — they do NOT want Odum running their backtest pipeline).

**Path:** Signals-only DART. Pricing and demo scope follow from the downstream-integration path. See
[rule 10](10-strategy-instruction-schema-principles.md) for the instruction-schema fit-check.

### Example 2 — Family office wanting Odum-run systematic exposure

**Context:** Allocator evaluating Odum as a manager. They want to allocate capital, not operate infrastructure.

**Axis resolution:** Strategy origin = Odum. Stack depth = reporting-only.

**Path:** Route to IM, not DART. The matrix correctly collapses this to the `(Odum, reporting-only)` cell which is
actually IM. DART-specific commercial logic does not apply.

### Example 3 — Emerging manager launching under regulated cover

**Context:** A manager wants to launch a strategy with regulatory cover, execution infra, and reporting, but will retain
some strategy discretion.

**Axis resolution:** Strategy origin = client. Stack depth = client-strategy+downstream-integration (hybrid — some
execution, reporting, regulatory umbrella).

**Path:** Usually Reg Umbrella + signals-only DART combo. Commercial engagement spans two service families; pricing
combines building blocks from both.

### Example 4 — Institutional prop firm wanting to buy Odum's strategy IP

**Context:** Firm wants to run Odum-developed strategies on their own capital with Odum's full infrastructure.

**Axis resolution:** Strategy origin = Odum. Stack depth = full-DART-pipeline.

**Path:** Full DART with Odum strategy exposure. This is NOT a lighter package even though the client doesn't develop
strategies themselves. Odum's IP comes with the full stack engagement.

### Example 5 — DAO treasury wanting yield rotation with reporting

**Context:** DAO wants systematic yield rotation across DeFi protocols + regulated reporting for members.

**Axis resolution:** Strategy origin = Odum (DAO wants Odum to run yield strategies). Stack depth = reporting-only.

**Path:** Route to IM with DeFi flavour. Same pattern as family office — the matrix routes the client out of DART and
into IM.

## Mapping to pricing

Rule 08 (`pricing-principles.md`) maps each cell to a pricing profile:

- **(Odum, reporting-only)** → IM pricing (allocator fee model, not DART building blocks).
- **(Odum, full-pipeline)** → Full DART building blocks + Odum-strategy-exposure premium. Tier B preferred
  (exclusivity-adjacent).
- **(Client, downstream)** → Signals-only DART building blocks: execution layer + venue packs + chain packs +
  instrument-type packs + reconciliation depth + limited analytics. No research/promote pipeline blocks. Tier A or B per
  block.
- **(Client, full-pipeline)** → Full DART building blocks including research/promote pipeline + exclusivity/custom
  premiums if negotiated. Tier A or B per block.

The per-block mixability (rule 08) means a signals-only client can still buy Tier B on reporting core + Tier A on
marginal venue packs — axes resolve the path; pricing tier is a separate decision per block.

## Mapping to demo restriction profiles

Stage 2 `demo-ops/demo-restriction-profiles.md` will map each cell to a default demo profile:

- `(Client, downstream)` demo profile = unlock execution + trading + observe + reports; lock research/promote surface
  with LOCKED-VISIBLE message "available in full DART".
- `(Client, full-pipeline)` demo profile = unlock all four catalogues + research + promote + execute + trade + observe.
- Odum-origin paths usually route to IM demos (pb3b), not DART demos (pb3c).

DART demo modes (broader-platform vs turbo) layer on top of these defaults — same cell can be shown in either demo mode
depending on prospect seniority and time budget.

## Edge cases

### Hybrid engagements

Some prospects span two cells — for example, a manager who wants Reg Umbrella + signals-only DART + IM allocator
reporting on behalf of their investors. Handle as three separate commercial engagements with shared infrastructure, not
as a single mega-package.

### Build-for-client

Occasionally Odum builds a strategy to a client spec and runs it on their capital. Axis resolution: strategy origin =
Odum (Odum built it); stack depth = full-pipeline. Sits in `(Odum, full)`. Priced with a build-engagement upfront
premium plus ongoing Tier B.

### Strategic partnership

Rare. A co-development engagement where strategy origin is genuinely shared. Doesn't fit the matrix cleanly; negotiate
bespoke. Flag to leadership; don't try to force into a standard path.

### Non-compete / exclusivity

Any cell can carry an exclusivity premium (Tier B only per rule 08). Exclusivity is a modifier on the cell, not a new
cell.

## Enforcement rules

1. **Resolve the path before pricing.** Every commercial conversation must resolve axis-1 and axis-2 before a quote is
   built. Path-ambiguous quotes cause drift.
2. **Odum strategy + downstream-only = escalate.** If a prospect asks for Odum strategy exposure with only downstream
   integration, do not price it as signals-only. Either upgrade them to full-pipeline or route them to IM.
3. **Reporting-only = not DART.** If the resolved cell is reporting-only, the commercial engagement is IM or Reg
   Umbrella. Do not use DART pricing or DART demo profiles.
4. **Signals-only clients don't get research/promote.** The package boundary is load-bearing. Clients who later want
   research/promote capability upgrade to full DART; it is not a bolt-on.
5. **One demo, one resolved cell.** A single demo session assumes one resolved path. Prospects exploring multiple paths
   get multiple demos.

## Service-family scope — see rule 12

The commercial axes above generate a closed set of service families (`IM`, `RegUmbrella`, `DART`, `DART_reporting_only`,
`admin`, `IM_desk`). The mechanical scope constraints — which tiles / routes each family can reach — live in rule 12
([`12-service-family-scope-rules.md`](./12-service-family-scope-rules.md)) with a matching machine-readable YAML at
[`12-service-family-scope-rules.yaml`](./12-service-family-scope-rules.yaml). Enforcement is a pre-check inside G1.6's
`access_control()` formula at `unified-api-contracts/.../internal/architecture_v2/service_family_scope.py`.

Do NOT duplicate the scope table here; rule 04 is the vocabulary + the commercial rationale, rule 12 is the enforcement
contract.

## Cross-references

- [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On DART commercial model (rule 04)"
- [`05-building-block-dimensions.md`](05-building-block-dimensions.md) — 13 blocks, the atomic units that each cell
  composes
- [`08-pricing-principles.md`](08-pricing-principles.md) — 2-tier pricing applied per block
- [`10-strategy-instruction-schema-principles.md`](10-strategy-instruction-schema-principles.md) — the fit-check layer
  for the `(Client, downstream)` path
- [`03-same-system-principle.md`](03-same-system-principle.md) — all paths use the same underlying system
- [`12-service-family-scope-rules.md`](12-service-family-scope-rules.md) — machine-readable scope enforcement per
  service family (paired with `12-service-family-scope-rules.yaml`)
- [Stage 2 `commercial-model/dart-entry-points.md`](../../../plans/ai/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md)
  — applies this rule to write the client-facing commercial doc
- [Stage 3 Phase 3C `derivation-engine.md`](../../../plans/ai/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md) —
  uses this matrix as one input to `demo_universe` and `prod_restrictions` formulas
