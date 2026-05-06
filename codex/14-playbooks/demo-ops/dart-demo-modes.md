---
scope: [sales, engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# DART Demo Modes — Broader Platform vs Turbo vs Deep-Dive

> The demo-mode axis layers on top of the restriction profile. Same `(Client, downstream)` cell can be demoed in
> broader-platform or turbo; same profile, different walk-through breadth.

**Rule source:** [rule 06](../_ssot-rules/06-show-dont-show-discipline.md) §Demo mode variants

## The three modes

### Broader platform demo

Wider tour across more surfaces; shallower per-surface. Typical 60 minutes. Fit: prospects wanting scope-before-depth,
early-stage evaluators, multi-role attendees. Default for pb3c first-look sessions.

### Turbo demo

Narrower surface count; deeper per-surface. Typical 45 minutes. Fit: prospects with a specific capability question;
decision-ready buyers. Default for pb3b IM demos where reporting is the proof point.

### Deep-dive demo

One surface, walked end-to-end. Typical 45-60 minutes. Fit: late-stage narrowing; diligence sessions. Default for pb3a
Reg Umbrella demos.

## Mode × path matrix

| Path                         | Typical first-demo mode | Typical second-demo mode            |
| ---------------------------- | ----------------------- | ----------------------------------- |
| IM allocator (pb3b)          | Turbo                   | Deep-dive on structural question    |
| Reg Umbrella (pb3a)          | Deep-dive (reporting)   | Rare; usually one demo              |
| Signals-only DART (pb3c)     | Broader platform        | Turbo on execution + reconciliation |
| Full DART (pb3c)             | Broader platform        | Deep-dive on research or promote    |
| Combined Reg Umbrella + DART | Two demos per flavour   | —                                   |

## Mode is orthogonal to restriction profile

The restriction profile (see [`demo-restriction-profiles.md`](demo-restriction-profiles.md)) is unchanged across modes.
What changes: the agenda (surfaces walked), the depth (how far into each), the pacing (narrative vs interactive).

A signals-only prospect can see a broader-platform, turbo, or deep-dive demo — the restriction profile is the same;
research / promote stays LOCKED-VISIBLE.

## How mode is chosen

| Signal                              | Lean toward      |
| ----------------------------------- | ---------------- |
| Exploratory, broad interest         | Broader platform |
| One sharp capability question       | Turbo            |
| Diligence-ready, narrowed scope     | Deep-dive        |
| Multi-attendee mixed roles          | Broader platform |
| Decision-maker solo, decision-ready | Turbo            |
| Follow-up after prior demo          | Deep-dive        |

If in doubt, start broader-platform. The cost of breadth-then-depth (two sessions) is lower than forcing depth on a
prospect not ready.

## Mode configuration

Mode is a sales-side staging toggle. Adjusts:

- **Landing-page agenda** — the pb3 hub renders the named agenda per mode.
- **Nav default-collapse state** — broader-platform opens more groups; turbo / deep-dive collapse to focused surface.
- **Post-demo prompt** — broader-platform prompts for deep-dive surface; deep-dive prompts for commitment.

Sales admin controls (including mode toggle) are HIDDEN-ENTIRELY from the prospect's view per rule 06.

## Cross-references

- [rule 06](../_ssot-rules/06-show-dont-show-discipline.md)
- [demo-restriction-profiles.md](demo-restriction-profiles.md)
- [pre-demo-curation-rules.md](pre-demo-curation-rules.md)
- [pre-demo-discovery-framework.md](pre-demo-discovery-framework.md)
- [upsell-overlays.md](upsell-overlays.md)
- [../experience/staging-demo-journey.md](../experience/staging-demo-journey.md)
- [../experience/dart-demo.md](../experience/dart-demo.md)
- [../experience/investment-management-demo.md](../experience/investment-management-demo.md)
- [../experience/regulatory-demo.md](../experience/regulatory-demo.md)
