---
doc_type: codex-ssot
title: Regulatory Umbrella — Warm-Prospect Demo
summary:
  pb3a warm-prospect Regulatory Umbrella demo on staging — walks the regulated-activity reporting landing, transaction
  reporting with best-execution evidence, the supervisory-artifact index, and the shared reporting walkthrough; demo
  surface is identical across mandate Shapes 1/2/3, entitlement-sliced.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [sales, prospect]
tags: [regulatory, demo, prospect, sales, compliance, reporting, ui]
related:
  [
    /codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    ../shared-core/client-reporting-demo-walkthrough.md,
    ../demo-ops/demo-restriction-profiles.md,
    ../commercial-model/im-vs-reg-reporting-logic.md,
  ]
created: 2026-04-20
authoritative_for: [pb3a Regulatory Umbrella warm-prospect demo experience]
referenced_by:
  [
    /codex/14-customer-journeys/demo-ops/dart-demo-modes.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/regulatory-umbrella-briefing.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    /codex/14-customer-journeys/playbooks/03a-demo-reg-umbrella.md,
  ]
owner:
last_reviewed:
code_refs: [unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts]
---

# Regulatory Umbrella — Warm-Prospect Demo

> Experience playbook for pb3a. Narrative overlay; the underlying reporting walkthrough lives in
> [`../shared-core/client-reporting-demo-walkthrough.md`](../shared-core/client-reporting-demo-walkthrough.md). Conforms
> to [rule 01 (grammar)](../_ssot-rules/01-grammar.md) and
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md).

**Internal label:** pb3a (warm-prospect Regulatory demo) **Status:** Stage 2 draft **Owner:** Reg Umbrella lead

## Audience

A principal at a firm that has completed the pb2c briefing and second call, has agreed a scoped Umbrella engagement in
principle, and is now viewing the staging environment to confirm that the operating surface matches the expectations set
in the call.

## Moment in journey

Warm-prospect demo. The prospect is logged into staging with a demo user scoped to the Regulatory Umbrella restriction
profile. The call that preceded this session resolved regulatory scope, onboarding path, and commercial shape. The
demo's job is to show the operating surface — specifically the reporting and supervisory artifacts the firm will use
once live — in a way that either confirms the scope or surfaces a gap.

## What Odum must prove

- The regulatory reporting surface exists, runs on live data shapes, and is the same component tree IM and DART clients
  use — filtered to the regulated-activity view ([rule 03](../_ssot-rules/03-same-system-principle.md)).
- Transaction reporting, best-execution evidence, and supervisory artifacts are operating features, not slides.
- The firm's activity, once onboarded, will surface on the reporting views the prospect sees today.
- Entitlement slicing is real — the prospect sees only their firm's view, not other Umbrella firms' data.

## Experience goal

The prospect leaves the demo either agreeing to move to onboarding or naming a specific scope gap the session surfaced.
A vague "we'll think about it" is not an outcome; the demo is designed to resolve.

## Walkthrough

The sales person opens the session by confirming the demo context — prospect firm name, scoped activity, permissions
mapped, demo mode (typically deep-dive for Umbrella, since reporting is the single proof point). The session runs
through the reporting surface the Umbrella firm will operate under.

The first surface is the regulated-activity reporting landing page. The prospect sees positions, transactions,
best-execution metrics, and the supervisory-artifact index — filtered to the demo firm's synthetic activity. The sales
person names that this is the same landing page IM and DART clients use, with a different entitlement set. The
prospect's dwell pattern on this page is captured in the account record as a signal.

The second surface is transaction reporting. The demo walks through the transaction reporting view, filter by instrument
and venue, drill into a transaction, show the supporting execution-quality evidence that ties the transaction to its
best-execution claim. The narrative names the regulatory obligation and shows the artifact that satisfies it. The shape
is: obligation named, surface shown, artifact linked.

The third surface is the supervisory-artifact index. Quarterly compliance reports, MLRO activity summaries, periodic
attestations — the prospect sees the shape of what they will receive as part of the operating relationship with Odum,
not the internal workbooks that produce them (those are rule-06 HIDDEN-ENTIRELY).

The fourth is the shared reporting walkthrough — positions, exposures, P&L, reconciliation — per
[`../shared-core/client-reporting-demo-walkthrough.md`](../shared-core/client-reporting-demo-walkthrough.md).
Reg-specific frame: the Umbrella firm's Pooled/SMA structural choice drives accounting and reporting setup, not which
features exist. Mandate-shape framing is deferred to the upstream briefing — the demo surface is identical across Shapes
1, 2, and 3 (Odum-as-IM default vs. AR route), so the walkthrough does not branch on shape. If the prospect opens a
mandate-shape question during the demo, route it back to the briefing
([regulatory-umbrella-briefing.md](regulatory-umbrella-briefing.md) "Who faces whom — mandate shapes") rather than
litigate it on a reporting surface.

The session closes with the onboarding-path recap. Five workstreams (legal, compliance, MLRO, venue, reporting) and
their Odum owners. The next commitment is the onboarding kickoff date, not another demo.

## Key messages

1. What you're looking at is the production system, filtered to your firm's view. The staging environment is the
   production UI.
2. Transaction reporting, best-execution, and supervisory artifacts are operating features on one component tree — not a
   separate regulatory product.
3. Your view is entitlement-sliced. Other Umbrella firms' data is not in your view; your data is not in theirs.
4. The onboarding kickoff is the next step. Legal, compliance, MLRO, venue, and reporting setup run in parallel.

## What not to show

- Internal compliance workbooks, MLRO internal procedures, or supervisory SOPs —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY. The prospect sees the artifacts they
  receive; they do not see how Odum produces them internally.
- Other Umbrella firms' activity, positions, or regulatory perimeters —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- DART research, promote, or strategy-authoring surfaces for pure Umbrella prospects —
  [rule 04](../_ssot-rules/04-dart-commercial-axes.md) + [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  LOCKED-VISIBLE with the "available in full DART" message. The surfaces appear in nav; they are not demonstrated.
- Pre-BACKTESTED maturity strategy slots — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- Odum-run IM strategy detail beyond the peer-visible aggregate —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY.
- Raw venue data feeds, on-chain dumps, regulatory-data subscriptions —
  [rule 07](../_ssot-rules/07-data-licensing-boundaries.md), HIDDEN-ENTIRELY. The reporting surfaces are Odum-enriched.
- Internal admin, ops, or devops routes — HIDDEN-ENTIRELY.
- Pricing breakdowns or internal cost columns — [rule 08](../_ssot-rules/08-pricing-principles.md), HIDDEN-ENTIRELY.
  Numbers live in the commercial follow-up, not the demo.

## Desired next step

Agree the onboarding kickoff date.

## Internal handoff

After the session, the Reg Umbrella lead captures the session outcome in the account-intelligence record — surfaces
covered, gaps surfaced, reservations raised, named next commitment. If the prospect agrees the onboarding kickoff, the
record transitions to onboarding ownership and the five workstreams start (legal agreements draft, compliance
pre-review, MLRO intake, venue provisioning request, reporting entitlement setup). If the prospect surfaces a scope gap,
the gap is captured verbatim and routed to the Reg Umbrella lead for scope-adjustment review. If the prospect has
combined Umbrella + DART or Umbrella + IM intent, the companion demo is scheduled through
[`../demo-ops/demo-decision-matrix.md`](../demo-ops/demo-decision-matrix.md).

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — reporting is a filter over one
  component tree
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — no numbers in the demo
- Impl-layer: [../playbooks/03a-demo-reg-umbrella.md](../playbooks/03a-demo-reg-umbrella.md)
- Upstream briefing: [regulatory-umbrella-briefing.md](regulatory-umbrella-briefing.md)
- Shared walkthrough:
  [../shared-core/client-reporting-demo-walkthrough.md](../shared-core/client-reporting-demo-walkthrough.md)
- Shared reporting core: [../shared-core/shared-reporting-core.md](../shared-core/shared-reporting-core.md)
- Demo restriction profile (Reg Umbrella):
  [../demo-ops/demo-restriction-profiles.md](../demo-ops/demo-restriction-profiles.md)
- Commercial model: [../commercial-model/im-vs-reg-reporting-logic.md](../commercial-model/im-vs-reg-reporting-logic.md)
- Compliance reference: [../../07-security/compliance.md](../../07-security/compliance.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` (Reg Umbrella persona)
