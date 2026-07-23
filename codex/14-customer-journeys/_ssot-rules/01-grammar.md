---
doc_type: codex-ssot
title: Rule 01 — Experience playbook grammar
summary:
  "The fixed nine-section grammar (Audience → Moment in journey → What Odum must prove → Experience goal → Walkthrough →
  Key messages → What not to show → Desired next step → Internal handoff) every experience playbook under experience/
  must carry, in order, with no omissions."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin, sales]
tags: [customer-journey, playbooks, sales, grammar, docspec]
related:
  [
    /codex/14-customer-journeys/_ssot-rules/02-tone-and-posture.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
  ]
created: 2026-04-20
authoritative_for: [experience playbook grammar (nine mandatory sections)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/_ssot-rules/02-tone-and-posture.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/_ssot-rules/README.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/experience/README.md,
    /codex/14-customer-journeys/experience/TEMPLATE.md,
    /codex/14-customer-journeys/experience/briefings-hub.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Rule 01 — Experience playbook grammar

> Nine sections, in this order, in every experience playbook. No omissions, no reordering, no merging. A playbook that
> skips a section is not a playbook; it is a draft.

**Source:** [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On document grammar (rule 01)".

## The nine sections

Every doc under [`../experience/`](../experience/) MUST contain these sections, with these exact headings, in this
order:

1. **Audience** — who this playbook is written for. One sentence: role, seniority, buying context.
2. **Moment in journey** — where the prospect or client is in their relationship with Odum when this playbook applies.
   One short paragraph; ties to the marketing → briefing → demo → onboarding ladder.
3. **What Odum must prove** — the three-to-five credibility claims the audience needs to accept before they act.
   Bulleted; each bullet is a claim, not a feature list.
4. **Experience goal** — the single outcome this playbook is trying to produce in the audience's head. One sentence.
   Must be specific enough to be falsifiable ("prospect understands that reporting is the same surface Odum uses
   internally" — not "prospect is impressed").
5. **Walkthrough** — the actual narrative or click-path the audience is taken through. Prose for briefings; structured
   click-path for demos. References to concrete routes, UI surfaces, or documents by link.
6. **Key messages** — three to five lines the audience should be able to recall after the session. These are the
   sentences a sales person would say verbatim. Written in Odum's voice (calm, specific, credible — see rule 02).
7. **What not to show** — the explicit exclusions for this playbook. Features, screens, data, or talking points that
   would dilute the experience goal or leak pricing / competitive intelligence. This section is load-bearing: if it is
   empty, rule 06 is being violated.
8. **Desired next step** — the one action this playbook is trying to produce. Book a follow-up call. Sign a mandate.
   Move to demo. Hand off to onboarding. One sentence, imperative.
9. **Internal handoff** — what happens inside Odum after the audience takes the next step. Who picks them up, which CRM
   record gets updated, which downstream playbook they enter. One short paragraph.

## Why the grammar is fixed

Three reasons the ordering and completeness matter:

1. **Audience comfort.** A briefing reader or demo prospect should feel the same structural rhythm across every Odum
   asset. Inconsistency reads as a small operational failure; consistency reads as an operating system.
2. **Sales ops reuse.** The account-intelligence record that every prospect generates (see rule 09 and Stage 2
   `demo-ops/`) slots directly against sections 4, 7, 8, 9. Drifting the grammar breaks the CRM pipeline.
3. **Engineering traceability.** Each playbook ships with a Playwright spec (see rule 02 + Stage 2 `testing/`). The spec
   asserts section 5's walkthrough and section 8's exit. Missing sections mean missing test coverage.

## Section-by-section writing guidance

### 1. Audience

One sentence. Name the role, the seniority, and the buying context. "CIO at a multi-strategy hedge fund evaluating
outsourced execution infrastructure." Not: "Hedge fund professionals." Generic audiences produce generic content.

### 2. Moment in journey

Anchor to the three-stage journey: pre-first-call / post-first-call / warm-prospect demo (matching pb1 / pb2 / pb3).
State which stage this is and what the prospect has already done. "Post-first-call. Prospect has had a 30-minute intro
with Odum leadership, signed a light-auth briefing code, and is now reading the IM briefing ahead of a second call."

### 3. What Odum must prove

Three to five bullets. Each is a **claim the audience must accept** — not a feature Odum ships. "Odum has institutional
operating discipline" is a claim. "Odum has a reconciliation service" is a feature.

### 4. Experience goal

Single sentence. Falsifiable. The test: if you asked the audience afterwards "what was the point of that document /
demo?", what answer would count as success? Write that answer.

### 5. Walkthrough

The spine of the doc. For briefings: three-to-five-paragraph narrative. For demos: structured click-path with route
references. Every route referenced here must exist (or be tagged `[TO BUILD]` with a cross-reference to the impl-layer
plan). No hypothetical routes.

### 6. Key messages

Three to five sentences that a sales person would say verbatim. These are the lines that show up in call notes, email
follow-ups, and proposal decks. Written in Odum voice — rule 02. Anti-pattern: generic "we help firms scale" prose.

### 7. What not to show

Explicit. "Internal pricing cost column. Internal engineering diagrams. In-progress maturity slots. Competitor
comparisons. Specific client names outside the anonymised aggregate." If this section reads short, rule 06 is being
violated — go back and tighten.

### 8. Desired next step

One sentence, imperative. "Book the next 45-minute session with the IM desk." "Issue staging credentials for the DART
demo." "Sign the mandate and transition to onboarding." Not: "Keep the conversation going."

### 9. Internal handoff

Where the prospect goes inside Odum next. Which team member owns the next touch. Which CRM fields get updated. Which
downstream playbook they become the audience for. This section connects experience-layer docs to demo-ops and sales-ops
(Stage 2).

## Cross-section consistency rules

- **Audience and walkthrough must match.** Don't write a CIO-audience playbook whose walkthrough is a developer
  click-path. Re-scope or split.
- **Experience goal and next step must match.** If the goal is "understand the reporting surface", the next step should
  be reporting-adjacent (book the reporting-focused follow-up), not "sign a Tier B contract".
- **What-not-to-show and key-messages must not contradict.** If a key message implies feature X, and what-not-to-show
  excludes X, the playbook is inconsistent. Fix one.
- **Next step and handoff must chain.** The handoff paragraph must name the team member / flow that receives the
  prospect after they take the desired next step. A handoff that doesn't match the next step is a drift signal.

## Enforcement rules

1. **Nine sections, every time.** No "we'll merge 6 and 7 for this one" shortcuts.
2. **Section headings are `##` level.** Sub-points use `-` bullets or `###` sub-headings, never alternative heading
   levels for the main nine.
3. **Order is fixed.** Audience first, Internal handoff last. No exceptions.
4. **Empty sections are not allowed.** A section with "TBD" or "see later" is an incomplete playbook — either finish it
   or the playbook is not ready to ship.
5. **One experience goal per playbook.** Multi-goal playbooks get split; one audience + one goal per file.

## Stage 2 implications

The Stage 2 dir rewrite
([`plans/ai/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md`](../../../plans/ai/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md))
replicates the pattern from [`../experience/im-decision-journey.md`](../experience/im-decision-journey.md) across the
other eight experience playbooks. Stage 2 agents MUST run the nine-section completeness check against every doc they
produce before commit.

## Cross-references

- [`_source-v1-feedback.md`](_source-v1-feedback.md) §"On document grammar (rule 01)"
- [`02-tone-and-posture.md`](02-tone-and-posture.md) — HOW each section is written
- [`06-show-dont-show-discipline.md`](06-show-dont-show-discipline.md) — polices section 7 specifically
- [`../experience/TEMPLATE.md`](../experience/TEMPLATE.md) — empty skeleton conforming to this grammar
- [`../experience/im-decision-journey.md`](../experience/im-decision-journey.md) — canonical filled reference
