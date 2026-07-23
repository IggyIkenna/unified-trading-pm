---
doc_type: codex-ssot
title: Investment Management — Decision Journey
summary:
  pb2a IM decision-journey briefing (canonical reference playbook) — walks strategy surface, SMA/Pooled structure
  (POD-administered custody), same-system reporting partition, FCA/MLRO cover, and the platform-fee client choice (+5%
  perf uplift or $500/mo access); 12-month minimum, feeds pb3b demo.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [sales, prospect]
tags: [investment-management, briefing, prospect, sales, reporting, sma-pooled, ui]
related:
  [
    /codex/14-customer-journeys/experience/investment-management-demo.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
    ../shared-core/same-system-principle.md,
    ../commercial-model/im-vs-reg-reporting-logic.md,
    ../commercial-model/im-profit-share-structures.md,
  ]
created: 2026-04-20
authoritative_for: [pb2a IM decision-journey briefing experience]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/_ssot-rules/01-grammar.md,
    /codex/14-customer-journeys/_ssot-rules/02-tone-and-posture.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/commercial-model/im-vs-reg-reporting-logic.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
  ]
owner:
last_reviewed:
code_refs: [unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts]
---

# Investment Management — Decision Journey

> Canonical reference playbook. Stage 2 replicates this pattern across the other eight experience playbooks. Conforms to
> [rule 01 (grammar)](../_ssot-rules/01-grammar.md) and
> [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md).

**Internal label:** pb2a (research & documentation — IM pillar), continuing into pb3b (warm-prospect IM demo)
**Status:** canonical reference **Owner:** IM desk

## Audience

An allocator or family-office principal evaluating Odum as a manager for systematic exposure — capital allocation, not
infrastructure operation.

## Moment in journey

Post-first-call. The prospect has had a thirty-minute intro with Odum leadership, signed a light-auth briefing code, and
is reading the IM briefing ahead of a second call. They know what Odum does at the category level; they do not yet know
whether Odum's operating discipline, reporting transparency, and regulatory posture stand up to institutional diligence.
This playbook is the content they sit with between the first call and the second.

## What Odum must prove

- Odum's strategies are run on the same infrastructure Odum built for itself, with institutional-grade reporting.
- Allocator-side reporting is genuine — positions, exposures, P&L, reconciliation — not a filtered marketing surface.
- The fund structure (SMA or Pooled) is a real operational decision with real consequences, not a sales script.
- FCA regulatory cover, compliance oversight, and MLRO functions are operated — not outsourced and not hand-waved.
- Twelve-month minimum commitment is explicit and the rationale holds up.

## Experience goal

The allocator finishes the briefing with a clear mental model of the IM engagement shape (structure, reporting,
regulatory cover, commitment) and a specific reason to book the second call — not vague enthusiasm.

## Walkthrough

The briefing opens with the one paragraph that sets the frame (see
[rule 09 expansion](../_ssot-rules/09-internal-commercial-oneliners.md)): Investment Management allocates client capital
to Odum-run systematic strategies under Odum's FCA permissions, and reporting comes from the same surface Odum uses to
run its own operation.

From there, the reader walks through four sections. The first is **the strategy surface** — one screen that shows the
strategies the allocator is actually being offered, with maturity and capacity visible per slot, filtered to the public
/ IM-reserved slice their role warrants ([rule 06](../_ssot-rules/06-show-dont-show-discipline.md)). No in-progress
placeholders, no DART-only research surfaces. The message the reader leaves this section with is: these are real, live
strategies, with real capacity, and they can see them.

The second is **structure** — SMA versus Pooled. A single page laying out the operational differences: SMAs have their
own fund, their own venues, their own API keys; Pooled holds multiple clients as share classes on one set of positions.
Fund structure is administered by POD, a regulated affiliate — Odum-the-trading-entity is never the custodian in either
structure. See [shared-core/fund-administration-and-custody.md](../shared-core/fund-administration-and-custody.md) for
the POD mechanic, the execute+read API-key pattern, and the public-copy phrasing rule (POD is internal-only; public
surfaces say "regulated affiliate"). The reader leaves with an inclination — most allocators default to SMA for
isolation, some to Pooled for operational simplicity — and an understanding that the decision has real cost
consequences, explored at the next call.

The third is **reporting**. The briefing shows the reporting surface — positions, exposures, P&L attribution,
reconciliation, audit trail — as an allocator-side partition of the operational surface Odum runs internally. See
[`../shared-core/same-system-principle.md`](../shared-core/same-system-principle.md) and
[`../commercial-model/im-vs-reg-reporting-logic.md`](../commercial-model/im-vs-reg-reporting-logic.md) for the
mechanism. IM-specific view: an allocator sees only their share of pooled positions and their selected strategy set.

The fourth is **regulatory and commitment**. Odum operates under FCA permissions; MLRO, compliance, and supervisory
reporting are run internally. The commitment floor is twelve months, and the briefing explains why — provisioning, legal
review, venue setup, per-client API-key issuance all carry fixed costs that the twelve-month floor recovers. The reader
leaves understanding the shape of the engagement, not just its label.

A short paragraph covers the **platform-fee client-choice mechanic**. At mandate signing the allocator picks a
platform-fee option — either a +5% performance-fee uplift (pure alignment, zero fixed) or a $500/month platform-access
fee (small floor regardless of strategy year). Either captures allocation to the same IM strategies; the difference is
purely whether the allocator prefers higher variable share with zero floor, or base variable share with a small
guaranteed floor. See
[`../commercial-model/im-profit-share-structures.md`](../commercial-model/im-profit-share-structures.md) for the
mechanic in full.

Footnote on catalogue scope for the narrative context when the allocator asks "what strategies are on offer today": the
BTC Fund of Funds wrapper is an **external** fund-of-funds mandate, not an Odum-system strategy. It appears in
client-reporting separately for the specific wrapper mandate and is not in the IM strategy catalogue.

The briefing closes with the second-call hook: a forty-five-minute session with the IM desk to walk the specific
strategies the allocator's mandate shape fits, the fund-structure choice, and the pricing.

## Key messages

1. Investment Management is allocation to Odum-run strategies on Odum infrastructure under Odum's FCA permissions.
2. Reporting: allocator-side partition of Odum's internal surface (see
   [`../commercial-model/im-vs-reg-reporting-logic.md`](../commercial-model/im-vs-reg-reporting-logic.md)). Pooled
   allocators see only their share plus their selected strategy set.
3. SMA and Pooled are the two structural options. Decision walked at the next call.
4. Regulatory cover, compliance, and MLRO are operated inside Odum — not outsourced.
5. Twelve-month minimum commitment; onboarding carries fixed legal, venue, and key-issuance costs.

## What not to show

- Internal monthly cost column from the pricing registry — [rule 08](../_ssot-rules/08-pricing-principles.md),
  HIDDEN-ENTIRELY.
- DART research / promote / strategy-authoring surfaces — [rule 04](../_ssot-rules/04-dart-commercial-axes.md) +
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY (IM allocators do not author strategies;
  those surfaces are not plausible next steps in this journey).
- Strategy slots at `CODE_NOT_WRITTEN` or `CODE_WRITTEN` maturity —
  [rule 06](../_ssot-rules/06-show-dont-show-discipline.md), HIDDEN-ENTIRELY. Only `BACKTESTED` and later are visible
  externally.
- Other allocators' positions, capital, or fund structure — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  HIDDEN-ENTIRELY.
- Raw market-data feeds or upstream data-source access — [rule 07](../_ssot-rules/07-data-licensing-boundaries.md),
  HIDDEN-ENTIRELY. The product is allocation to enriched services, not data.
- Execution-layer depth beyond the reporting surface — [rule 06](../_ssot-rules/06-show-dont-show-discipline.md),
  LOCKED-VISIBLE with a short explanation. Execution is Odum-operated; the allocator sees the consequences, not the
  mechanism.
- Tier A / Tier B price quotes — reserved for the second call. Briefing is scope and discipline, not numbers.

## Desired next step

Book the forty-five-minute IM desk session.

## Internal handoff

The IM desk picks up the prospect once the session is booked. The CRM record updates with the briefing-view event, the
scheduled session time, and any inferred gaps from the prospect's briefing behaviour (page dwell, section skips). The
desk session walks specific strategy slots against the allocator's mandate, the SMA-vs-Pooled decision in detail, and a
first-pass pricing conversation. If the session produces alignment, the prospect transitions to pb3b — the warm-prospect
IM demo on staging Firebase, with a demo user provisioned to the IM flavour entitlement set.

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md) — reporting is a partition of Odum's
  internal operating surface
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md) — the full default-exclusion
  set for IM
- [rule 07 — data licensing boundaries](../_ssot-rules/07-data-licensing-boundaries.md) — enriched-services framing
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — twelve-month minimum, internal cost private
- [rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md) — the scope-setting
  paragraph expands from the IM one-liner
- Impl-layer briefing: [../playbooks/02a-research-im.md](../playbooks/02a-research-im.md)
- Downstream demo: [../playbooks/03b-demo-im.md](../playbooks/03b-demo-im.md)
- Client-reporting cross-cutting doc: [../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md)
- SMA vs Pooled: [../cross-cutting/sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` (IM persona)
