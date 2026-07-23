---
doc_type: codex-ssot
title: Rule 06 — Show / don't-show discipline
summary:
  "Show/don't-show demo discipline — every experience playbook carries a populated what-not-to-show list; three
  orthogonal axes (demo mode / commercial path / prod restriction), default per-path exclusions, and the LOCKED-VISIBLE
  vs HIDDEN-ENTIRELY choice per item."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin, sales]
tags: [customer-journey, sales, ui, dart, docspec]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/01-grammar.md,
    /codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md,
    /codex/14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md,
    /codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md,
  ]
created: 2026-04-20
authoritative_for: [show/don't-show demo disclosure discipline (LOCKED-VISIBLE vs HIDDEN-ENTIRELY)]
referenced_by:
  [
    /codex/14-customer-journeys/_ssot-rules/01-grammar.md,
    /codex/14-customer-journeys/_ssot-rules/02-tone-and-posture.md,
    /codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md,
    /codex/14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md,
    /codex/14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md,
    /codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md,
    /codex/14-customer-journeys/_ssot-rules/README.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 06 — Show / don't-show discipline

> What you leave off the page matters as much as what you put on it. Every experience playbook has an explicit
> what-not-to-show list. An empty list is a drafting failure.

**Mechanism SSOT:** [`../cross-cutting/visibility-slicing.md`](../playbook-concepts/visibility-slicing.md) carries the
`visible(user, item)` filter function that enforces this rule at runtime.

## The show / don't-show contract

Every experience playbook under [`../experience/`](../experience/) has two paired sections (rule 01 §5 and §7):

- **Walkthrough** — what the audience sees, in order.
- **What not to show** — what the audience does not see, even if they ask, even if it would be impressive.

The two must be consistent. A walkthrough that leaks competitive intel while the not-show section forbids it is a
rule-06 violation.

## Why this matters commercially

Odum loses deals three ways through careless disclosure:

1. **Pricing leakage.** Internal cost columns, Tier A vs Tier B rationale, exclusivity pricing — exposed too early,
   these anchor the conversation in ways that are hard to walk back.
2. **Scope leakage.** Showing a signals-only prospect the research/promote pipeline creates an expectation that the
   lighter engagement includes it. The package boundaries in rule 04 and rule 10 only hold if the demo respects them.
3. **Feature leakage.** Showing in-progress or internal-only capabilities creates forward-tense expectations ("when will
   that be available?") and wastes trust when the answer is "it's not for you".

Rule 06 is how Odum avoids these.

## The three axes (restated)

From the v1 feedback, show/don't-show decomposes along three independent axes:

| Axis                       | Values                                                        | Controlled by                                    |
| -------------------------- | ------------------------------------------------------------- | ------------------------------------------------ |
| **Demo mode**              | broader platform / turbo / deep-dive                          | Sales decision per prospect, configurable toggle |
| **Commercial path**        | reporting-only / signals-only / full-DART / IM / Reg Umbrella | Axis resolution (rule 04)                        |
| **Production restriction** | the paying client's entitlement slice                         | Stage 3B entitlement registry                    |

These axes are orthogonal. The same underlying platform supports all three through one visibility-slicing derivation
(Stage 3C).

### Demo mode variants

- **Broader platform demo** — wider tour, more surfaces, shallower depth per surface. For prospects who want to
  understand scope before depth. Default for pb3c (DART) when the prospect is evaluating multiple service families.
- **Turbo demo** — narrower surface, deeper interaction. For prospects who know what they want and need proof. Default
  for pb3b (IM) where the reporting surface is the proof point.
- **Deep-dive demo** — one surface, taken to the limit. Used late in the sales cycle after narrowing.

Demo mode layers on top of commercial-path defaults. A `(Client, downstream)` prospect can see a broader-platform demo
or a turbo demo — the underlying restriction profile is the same; the breadth of surfaces walked through differs.

## Default what-not-to-show by commercial path

Each commercial path carries default exclusions. Experience playbooks may override with explicit justification.

### All paths

- Internal cost column from the pricing registry (rule 08).
- Any client-identifying data belonging to another client. Aggregates and anonymised case studies only.
- In-progress capabilities marked `CODE_NOT_WRITTEN` or `CODE_WRITTEN` maturity (see strategy-availability model).
- Internal ops routes: `/admin/*`, `/ops/*`, `/config/*`, `/devops/*`.
- Competitor names, comparisons, or disparagement.
- Odum's internal engineering diagrams unless the audience is an investor or an engineering-technical diligence session.

### Reporting-only visibility (IM / Reg Umbrella entry)

- Full DART surface (research/promote pipeline, strategy catalogue depth, DART trading terminal beyond the read-only
  views the reporting surface offers).
- Strategy-service internals. They don't touch it.
- Execution-algo internals. They don't touch it.

### `(Client, downstream)` — signals-only DART

- Research / promote pipeline (block 6, rule 05). Locked with an explicit LOCKED-VISIBLE treatment: the surface exists
  in the nav, it is marked "available in full DART", clicking shows a short explanation.
- Full strategy catalogue depth beyond the slots the client's instruction schema hits.
- Internal-only promote-pipeline stages.
- Odum-run IM strategy detail beyond the aggregate that the client can see as a peer.

### `(Client, full-pipeline)` — full DART

- Internal-only pre-maturity slots (CODE_NOT_WRITTEN / CODE_WRITTEN). CODE_AUDITED and later are fine.
- Odum-strategy IP depth beyond what the client has licensed.
- Other-client CLIENT_EXCLUSIVE slots.

### IM

- DART research/promote / strategy-authoring surfaces. The IM client allocates capital; they do not operate strategies.
- Execution-layer depth beyond what shows up on the reporting surface.
- Other investors' allocations within the fund.

### Reg Umbrella

- Other Umbrella clients' operational data.
- Odum-run IM strategy detail.
- DART research/promote pipeline.

## How this pairs with rule 03

Rule 03 (same-system principle) says there is one underlying system. Rule 06 says not every audience sees all of it.
These are complementary:

- **One route, not two.** A demo prospect and a paying client both visit `/services/reports/overview`. The route is the
  same (rule 03).
- **Different slices.** What they see on that route is different (rule 06). The demo prospect's filter is the demo
  profile; the paying client's filter is their entitlement set.
- **Locked surfaces are visible, not hidden.** Rule 06 prefers LOCKED-VISIBLE over HIDDEN-ENTIRELY for scope-adjacent
  surfaces. A signals-only client should see the research surface in their nav, marked "full DART only", so the upgrade
  path is visible. Hiding it creates the wrong impression when they ask.

## LOCKED-VISIBLE vs HIDDEN-ENTIRELY

Two exclusion modes, used differently:

- **LOCKED-VISIBLE** — the surface appears in the nav with a lock icon and short explanation. Clicking shows a
  restriction message with a hook to the upgrade path. Use this for scope-adjacent surfaces (research/promote in a
  signals-only demo). Keeps the upgrade path legible.
- **HIDDEN-ENTIRELY** — the surface does not appear in the nav and is not reachable. Use this for out-of-audience
  surfaces (a reporting-only IM prospect does not see DART research surfaces at all; they are not a plausible next
  step). Also use for internal-only ops routes and other clients' CLIENT_EXCLUSIVE data.

Default to LOCKED-VISIBLE when the surface is an obvious next step; HIDDEN-ENTIRELY when it is not.

## Enforcement rules

1. **Every experience playbook has a populated what-not-to-show section.** Empty = drafting failure, do not ship.
2. **What-not-to-show items cite a rule or reason.** "Pricing internal cost (rule 08)", "other-client data (rule 07)",
   "in-progress maturity (strategy-availability model)". Reasonless exclusions drift.
3. **LOCKED-VISIBLE vs HIDDEN-ENTIRELY is an explicit choice per item.** The playbook says which mode the item is in and
   why.
4. **Demo scripts carry the same list.** Stage 2 `demo-ops/demo-scripts/*.md` must mirror the what-not-to-show list of
   the corresponding experience playbook, verbatim or by explicit reference.
5. **The account-intelligence record logs deviations.** If a sales person shows something that was on the not-show list,
   they log it in the prospect record with the justification. Unjustified deviations surface in weekly review.
6. **Production entitlements enforce the exclusions.** What a demo client can't see in staging, the equivalent
   production client cannot see either, unless their entitlement set explicitly unlocks it.

## Stage 2 implications

- `demo-ops/demo-restriction-profiles.md` tabulates the defaults above across all commercial paths.
- `demo-ops/demo-scripts/*.md` per-playbook scripts carry the what-not-to-show list.
- Every experience playbook's §7 references the relevant demo-restriction profile.

## Stage 3 implications

Stage 3C's derivation engine resolves `(audience, route, block) → visible | locked-visible | hidden` from one registry
read. Rule 06's defaults become the default lookup values; per-client entitlements override.

## Cross-references

- [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On demo mode vs commercial path vs production restriction"
- [`03-same-system-principle.md`](03-same-system-principle.md) — one system, many views
- [`04-dart-commercial-axes.md`](04-dart-commercial-axes.md) — commercial-path resolution picks the default profile
- [`07-data-licensing-boundaries.md`](07-data-licensing-boundaries.md) — data-licence-specific not-show items
- [`08-pricing-principles.md`](08-pricing-principles.md) — pricing leakage is the top not-show class
- [`../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md`](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
  — maturity gating that rule 06 inherits
