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
The reader leaves with an inclination — most allocators default to SMA for isolation, some to Pooled for operational
simplicity — and an understanding that the decision has real cost consequences, explored at the next call.

The third is **reporting**. The briefing shows the reporting surface — positions, exposures, P&L attribution,
reconciliation, audit trail. It names the fact explicitly: this is the same surface Odum uses to monitor its own
operation. Allocator-side views are filtered from the same component tree
([rule 03](../_ssot-rules/03-same-system-principle.md)). The reader understands that their reporting is not a
purpose-built investor view assembled after the fact; it is a partition of an operational surface.

The fourth is **regulatory and commitment**. Odum operates under FCA permissions; MLRO, compliance, and supervisory
reporting are run internally. The commitment floor is twelve months, and the briefing explains why — provisioning, legal
review, venue setup, per-client API-key issuance all carry fixed costs that the twelve-month floor recovers. The reader
leaves understanding the shape of the engagement, not just its label.

The briefing closes with the second-call hook: a forty-five-minute session with the IM desk to walk the specific
strategies the allocator's mandate shape fits, the fund-structure choice, and the pricing.

## Key messages

1. Investment Management is allocation to Odum-run strategies on Odum infrastructure under Odum's FCA permissions — not
   a third-party reporting wrapper.
2. Reporting is the same surface Odum uses internally, filtered for allocator-side views. Same data, same components,
   different entitlements.
3. SMA and Pooled are the two real structural options. The choice has operational consequences; Odum will walk through
   both with you at the next call.
4. Regulatory cover, compliance, and MLRO are operated inside Odum — not outsourced, not optional.
5. Twelve-month minimum commitment reflects onboarding reality: legal, venue, per-client key issuance, reconciliation
   setup. Shorter is not a standard option.

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
- Client-reporting cross-cutting doc: [../cross-cutting/client-reporting.md](../cross-cutting/client-reporting.md)
- SMA vs Pooled: [../cross-cutting/sma-vs-pooled.md](../cross-cutting/sma-vs-pooled.md)
- Playwright spec: `unified-trading-system-ui/tests/e2e/playbooks/warm-prospect-demo.spec.ts` (IM persona)
