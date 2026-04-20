# IM vs Reg Umbrella Reporting — Same UI, Two Commercial Framings

> The reporting surface IM allocators and Reg Umbrella firms use is the same UI (rule 03 same-system principle). The
> commercial framing differs, the block composition differs, and the pricing differs. This doc maps the differences.

**Rule sources:** [rule 03](../_ssot-rules/03-same-system-principle.md),
[rule 05](../_ssot-rules/05-building-block-dimensions.md) blocks 1, 2, 3,
[rule 09](../_ssot-rules/09-internal-commercial-oneliners.md)

## The shared surface

The UI at `/services/reports/*` renders the same component tree for both audiences. See
[`../shared-core/shared-reporting-core.md`](../shared-core/shared-reporting-core.md) for the implementation map. What
differs between audiences is which panels mount (per their entitlement set) and how the data is scoped (per their
API-key set).

This is load-bearing: one UI is cheaper to operate, more credible to diligence ("the allocator uses the same surface
Odum uses internally"), and eliminates drift between parallel reporting products.

## Two commercial framings

### IM allocator framing

The allocator is buying **allocation to Odum-run strategies with institutional-grade reporting on their share of
performance.** The reporting surface renders share-class NAV, fees, investor statements — the artifacts an allocator
needs to run their own fund operation.

Rule 09 expansion: _Investment Management allocates client capital to Odum-run systematic strategies operating under
Odum's FCA permissions. Reporting — positions, exposures, P&L, reconciliation — comes from the same surface Odum uses to
run its own operation, with allocator-side views filtered by entitlement. The minimum engagement is twelve months._

**Who buys:** Family-office principals, multi-strategy allocators, institutional investment committees.

### Reg Umbrella framing

The Umbrella client is buying **regulatory cover with operating reporting that satisfies their MIFID / FCA
obligations.** The reporting surface renders transaction reporting, best-execution evidence, and supervisory artifacts —
the artifacts a regulated firm needs to satisfy their compliance perimeter.

Rule 09 expansion: _Firms running regulated activity that want operational coverage without seeking direct FCA
authorisation can operate under Odum's permissions. Onboarding handles regulatory scope, compliance setup, MLRO
coverage, and supervisory reporting. Reporting surfaces use the same component tree as IM and DART reporting, filtered
to the firm's regulated-activity view._

**Who buys:** Emerging managers, firms spinning up new regulated activity, DeFi-native firms stepping into regulated
execution.

## Block composition — IM vs Reg Umbrella

Same UI, two different block sets. Rule 05 blocks 1, 2, 3 are the reporting-adjacent blocks; 1 is universal, 2 is Reg
Umbrella specific, 3 is IM specific.

| Block                             | IM engagement | Reg Umbrella engagement | Notes                                           |
| --------------------------------- | ------------- | ----------------------- | ----------------------------------------------- |
| 1 — Reporting core                | Yes           | Yes                     | Universal across all paying clients             |
| 2 — Regulatory umbrella reporting | No            | Yes                     | MIFID / FCA filing surfaces, best-ex evidence   |
| 3 — IM allocator reporting        | Yes           | No                      | NAV, fees, investor statements                  |
| 4 — Strategy-service entry        | No            | Sometimes               | Only if Reg Umbrella includes execution scope   |
| 5 — Instructions integration      | No            | Sometimes               | If signals-only DART combined with Reg Umbrella |
| 7 — Execution layer               | No            | Yes (typically)         | Umbrella firm executes under Odum's permissions |
| 8 — Venue packs                   | No            | Yes                     | Scoped to firm's activity                       |
| 10 — Instrument-type packs        | No            | Yes                     | Scoped to firm's activity                       |
| 11 — Analytics packs              | Optional      | Optional                | Scope depends                                   |

**Combined engagements.** A manager doing IM (for their own investors) + Reg Umbrella (for their regulatory posture)

- signals-only DART (for their execution stack) is three engagements with shared infrastructure, three block sets
  composed, three pricing computations — not one mega-bundle. Shared-infrastructure pricing does apply; the twelve-month
  floor applies per engagement.

## Pricing differences

Same UI doesn't mean same pricing. Tier A / Tier B per-block assignment differs per audience because the value shape
differs.

### IM typical pricing shape

- Block 1 (reporting core) — Tier B. Institutional allocators need SLA certainty; reporting is the proof point.
- Block 3 (IM allocator reporting) — Tier B. Specific to the engagement; fixed monthly.
- Optional analytics packs — Tier A.
- **No execution-layer block** — IM allocates capital; Odum runs execution. The execution cost is embedded in the
  management-fee side of the commercial, not in block 7 per se.

IM pricing also carries a management-fee + performance-fee layer on the allocated capital, which is a separate
commercial mechanic from the DART building-block pricing. IM blocks 1 + 3 are the infrastructure-access portion; the
fees are the allocation-to-strategy portion. Both live in the IM commercial envelope, distinct from DART.

### Reg Umbrella typical pricing shape

- Block 1 (reporting core) — Tier B.
- Block 2 (regulatory umbrella reporting) — Tier B. The core regulatory block; fixed monthly for predictability.
- Block 7 (execution layer) — Tier B or A depending on execution volume.
- Block 8 (venue packs) — Mix: Tier B for primary, Tier A for marginal.
- Block 10 (instrument-type packs) — Tier A or B per type.

Reg Umbrella does not typically carry a management-fee layer because the Umbrella client is running their own regulated
activity; Odum is the regulated counterparty providing cover, not the manager of the client's capital.

## The "same UI" claim, commercially

When a sales person on the IM or Reg Umbrella path says "this is the same surface Odum uses internally", the claim is
true and it is a positive commercial signal:

- The allocator's reporting is not a purpose-built investor view assembled after the fact; it is a partition of an
  operational surface. That framing lands as operating credibility.
- The Umbrella firm's regulatory artifacts are not a compliance-tool bolt-on; they are entitlement-filtered views on the
  same operational surface. That framing lands as audit-worthiness.

The rule 03 same-system principle is commercially valuable, not just engineering-principled.

## What about DART + IM or DART + Reg Umbrella?

See [`dart-entry-points.md`](dart-entry-points.md) Example D. Combined engagements compose block sets across audiences
but the shared reporting surface is one UI — the audience's entitlement set mounts the audience-specific panels. A
DART+Reg Umbrella client on the same surface sees transaction reporting (block 2 entitlement) AND strategy-service entry
(block 4 entitlement); the same report landing page renders both.

## Cross-references

- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md)
- [rule 05 — building-block dimensions](../_ssot-rules/05-building-block-dimensions.md) — blocks 1, 2, 3
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — per-block mixability
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md)
- [../shared-core/shared-reporting-core.md](../shared-core/shared-reporting-core.md) — the shared UI
- [../shared-core/client-reporting-demo-walkthrough.md](../shared-core/client-reporting-demo-walkthrough.md) — the
  shared demo path
- [building-block-packaging.md](building-block-packaging.md)
- [pricing-building-blocks.md](pricing-building-blocks.md)
- [../experience/im-decision-journey.md](../experience/im-decision-journey.md) — pb2a
- [../experience/regulatory-umbrella-briefing.md](../experience/regulatory-umbrella-briefing.md) — pb2c
