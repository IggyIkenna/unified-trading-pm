---
doc_type: codex-ssot
title: Meeting History and Interest Tracking
summary:
  Per-session log-back to the account-intelligence record (7 fields — session_id/type, flavour, mode, surfaces_covered
  with per-surface time, interest_signals, reservations_raised verbatim, next_commitment_named) so each call is
  cumulative; interest-signal taxonomy, verbatim-reservation discipline, and 30-min post-session capture window.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [sales, engineer, admin]
tags: [demo-ops, sales, crm, session-tracking, interest-signals, follow-up]
related:
  [
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/pre-demo-discovery-framework.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
    /codex/14-customer-journeys/demo-ops/demo-decision-matrix.md,
  ]
created: 2026-04-20
authoritative_for: [demo meeting history and interest tracking]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/demo-ops/README.md,
    /codex/14-customer-journeys/demo-ops/account-intelligence-record.md,
    /codex/14-customer-journeys/demo-ops/post-demo-followup-orchestration.md,
    /codex/14-customer-journeys/experience/staging-demo-journey.md,
    /codex/14-customer-journeys/implementation-mapping/demo-email-and-provisioning-flow.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Meeting History and Interest Tracking

> How each demo session logs back to the account-intelligence record so the next call is cumulative. Session outcomes,
> surfaces covered, interest signals, reservations raised. Feeds follow-up orchestration.

**Rule source:** [rule 06](../_ssot-rules/06-show-dont-show-discipline.md) §Enforcement rule 5 (deviations logged)

## Why this tracking matters

Cumulative context. A demo that reads as the fifth session in a deepening conversation is operationally different from
one that reads as an unconnected meeting. Without tracking, every session starts cold; with tracking, every session
builds on what came before.

## What to capture per session

Structured post-session update to the account-intelligence record (see
[`account-intelligence-record.md`](account-intelligence-record.md)). Seven fields per session entry:

| Field                   | Content                                                                                 |
| ----------------------- | --------------------------------------------------------------------------------------- |
| `session_id`            | UUID; timestamped                                                                       |
| `session_type`          | `intro_call` / `pb2_briefing_read` / `second_call` / `pb3_demo` / `follow_up`           |
| `flavour` (demos only)  | `pb3a` / `pb3b` / `pb3c` / `combined`                                                   |
| `mode` (demos only)     | `broader_platform` / `turbo` / `deep_dive`                                              |
| `surfaces_covered`      | Ordered list of surfaces walked with per-surface time spent                             |
| `interest_signals`      | Observations — what the prospect engaged with, what they lingered on, what they skipped |
| `reservations_raised`   | Verbatim objections or concerns raised by the prospect                                  |
| `next_commitment_named` | The named next action at session close                                                  |

Plus:

- `deviations_logged` — rule 06 / rule 07 / rule 08 deviations during the session (what was shown that was on the
  not-show list, and the justification).
- `freeform_notes` — narrative observations that don't fit the structured fields.

## Interest-signal taxonomy

What counts as an interest signal:

- **Engagement markers.** Prospect leaned in, asked a follow-up question, asked for the surface to be shown again.
- **Lingering.** Prospect kept clicking around on a surface after the sales person moved on.
- **Specific asks.** "Can we see this for [specific venue]?" or "How does this handle [specific instrument]?"
- **Comparative framing.** "How does this compare to [their current solution]?" — usually a latent objection; record it.
- **Skipping / disengagement.** Prospect glazed over on a surface; rushed through; asked to move on.
- **Technical depth questions.** Engineering-grade questions from a technical attendee usually flag a diligence review
  step later; record the attendee and the question.

## Reservation-capture discipline

Reservations are captured verbatim, not paraphrased. This is load-bearing for two reasons:

1. **Accuracy.** "Your pricing is too high" and "we're not sure the value justifies the fixed monthly for us at our
   current AUM" look similar but mean different things. Verbatim captures the nuance.
2. **Response quality.** Sales can address a reservation precisely only if it is recorded precisely. Paraphrasing loses
   the handle.

## Surfaces-covered tracking

Each surface walked gets a time stamp (approximate minutes) and a brief note. Example entry for a pb3c signals-only
demo:

```
surfaces_covered:
  - surface: /services/strategy-catalogue (scope-filtered)
    time_mins: 4
    note: Prospect lingered on the stat-arb-pairs-fixed row
  - surface: /services/strategy-service (strategy-service entry)
    time_mins: 7
    note: Asked about per-instruction risk limits — specific
  - surface: /services/execution/terminal
    time_mins: 12
    note: Engaged deeply; asked to see cross-venue routing for Binance-perp → Hyperliquid
  - surface: /services/reports/overview
    time_mins: 8
    note: Standard walkthrough; less engagement here
```

This format lets the next session's prep identify where to deepen ("Prospect lingered on stat-arb-pairs-fixed; bring
that surface back into a follow-up").

## Tracking interest across sessions

The account-intelligence record accumulates session entries. Over time, patterns emerge:

- **Consistent lingering on one surface across sessions** → that surface is a latent primary interest; weight it in
  commercial shape.
- **Consistent reservation on one dimension** → unresolved objection; address directly rather than hope it fades.
- **Signals of secondary path interest** → prospect initially resolved to signals-only but keeps asking about research
  surfaces → they may be a full-DART candidate; run the fit-check again.
- **Escalating depth questions over sessions** → diligence is building; anticipate a technical review.

## What tracking does not do

- **Does not replace the freeform notes.** Structured fields plus narrative notes; the narrative catches what the fields
  miss.
- **Does not judge the prospect.** Interest signals are observations, not character assessments. Rule 02 calm posture
  applies to internal records too.
- **Does not leak externally.** Account-intelligence records are internal only.

## Post-session update timing

- **Within 30 minutes of the session close.** Memory decays; structured capture immediately while detail is fresh.
- **Before scheduling any next touch.** The record's `next_commitment_named` drives the orchestration scheduler (see
  [`post-demo-followup-orchestration.md`](post-demo-followup-orchestration.md)).
- **Before any shared-team discussion.** Weekly review reads the records; a session not recorded is invisible to the
  team review.

## Cross-references

- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [account-intelligence-record.md](account-intelligence-record.md) — record structure
- [pre-demo-discovery-framework.md](pre-demo-discovery-framework.md) — signals framework
- [post-demo-followup-orchestration.md](post-demo-followup-orchestration.md) — follow-up scheduling
- [demo-decision-matrix.md](demo-decision-matrix.md) — cross-session patterns reshape matrix choice
- [../experience/](../experience/) — every experience playbook §9 internal handoff updates this tracking
