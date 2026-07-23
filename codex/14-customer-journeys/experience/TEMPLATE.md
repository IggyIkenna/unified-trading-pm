---
doc_type: codex-ssot
title: "[Playbook title — audience-facing, not internal shorthand]"
summary:
  Canonical skeleton for experience-playbook docs (rule 01) — the fixed section set (Audience, Moment in journey, What
  Odum must prove, Experience goal, Walkthrough, Key messages, What not to show, Desired next step, Internal handoff)
  every pb1/pb2/pb3 playbook under this dir fills in.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [sales, prospect]
tags: [template, experience-playbook, playbook, sales, prospect]
related:
  [../_ssot-rules/01-grammar.md, ../_ssot-rules/02-tone-and-posture.md, ../_ssot-rules/06-show-dont-show-discipline.md]
created: 2026-04-20
authoritative_for: [experience playbook skeleton template file]
referenced_by: [/codex/14-customer-journeys/_ssot-rules/01-grammar.md, /codex/14-customer-journeys/experience/README.md]
owner:
last_reviewed:
code_refs:
---

# [Playbook title — audience-facing, not internal shorthand]

> **Template status:** canonical skeleton conforming to [rule 01](../_ssot-rules/01-grammar.md). Every experience
> playbook under this dir uses this structure.
>
> Before writing, re-read [rule 02 (tone and posture)](../_ssot-rules/02-tone-and-posture.md) and
> [rule 06 (show / don't-show discipline)](../_ssot-rules/06-show-dont-show-discipline.md). Cite other rules (03–10) as
> their content is invoked.

**Internal label:** [pb1 / pb2a / pb2b / pb2c / pb3a / pb3b / pb3c — for cross-reference with impl-layer docs]
**Status:** [draft / reviewed / canonical] **Owner:** [sales / product / marketing — one name]

## Audience

[One sentence. Role, seniority, buying context. "CIO at a multi-strategy hedge fund evaluating outsourced execution
infrastructure." Avoid generic audience labels.]

## Moment in journey

[One short paragraph. Which of the three journey stages (pre-first-call / post-first-call / warm-prospect demo) this
applies to, and what the audience has already done. Ties to pb1 / pb2 / pb3 internal labels.]

## What Odum must prove

[Three to five bullets. Each bullet is a credibility claim the audience must accept — not a feature Odum ships.]

- [Claim one — e.g. "Odum operates with institutional discipline, not founder-mode improvisation"]
- [Claim two]
- [Claim three]

## Experience goal

[One sentence. Falsifiable. The single outcome this playbook is trying to produce in the audience's head. Test: if the
audience were asked afterwards "what was the point of that", what specific answer would count as success?]

## Walkthrough

[The spine of the doc. For briefings: three-to-five-paragraph narrative. For demos: structured click-path with route
references. Every route referenced must exist, or be tagged `[TO BUILD]` with a cross-reference to the impl-layer plan.
Rule 02 tone throughout — calm, specific, present tense, no adverbs. See
[rule 03 (same-system principle)](../_ssot-rules/03-same-system-principle.md) when the walkthrough touches the
research/live relationship.]

[Paragraph one — or click-path step 1.]

[Paragraph two — or click-path step 2.]

[Paragraph three — or click-path step 3.]

## Key messages

[Three to five sentences the audience should recall. These are the lines a sales person would say verbatim. Rule 02
voice; no adverbs, no forward-tense marketing.]

1. [Message one — Odum voice]
2. [Message two]
3. [Message three]

## What not to show

[Explicit exclusions. Every item cites a rule or a reason. LOCKED-VISIBLE vs HIDDEN-ENTIRELY is an explicit choice per
item. If this section reads short, re-read rule 06 — it probably needs more items.]

- [Internal cost column from the pricing registry — rule 08, HIDDEN-ENTIRELY]
- [Research / promote pipeline for signals-only prospects — rule 04 + rule 06, LOCKED-VISIBLE with "full DART only"
  message]
- [In-progress `CODE_NOT_WRITTEN` / `CODE_WRITTEN` maturity slots — rule 06, HIDDEN-ENTIRELY]
- [Other-client data — rule 07 (if data-related) or rule 06, HIDDEN-ENTIRELY]

## Desired next step

[One sentence, imperative. "Book the 45-minute IM desk session." "Sign the mandate." "Issue staging credentials for the
DART demo." Must chain to the internal handoff below.]

## Internal handoff

[Where the prospect goes inside Odum next. Which team member owns the next touch. Which CRM fields get updated. Which
downstream playbook becomes their next frame. One short paragraph. Chain back to the desired next step above.]

---

## Cross-references

- [rule 01 — grammar](../_ssot-rules/01-grammar.md)
- [rule 02 — tone and posture](../_ssot-rules/02-tone-and-posture.md)
- [[cite rules 03–10 as invoked]]
- [Impl-layer doc for this audience (if exists)](../playbooks/[xx-filename].md)
- [Playwright spec](../testing/[matching spec path])
