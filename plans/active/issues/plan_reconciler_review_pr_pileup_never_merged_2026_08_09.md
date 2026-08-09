---
doc_type: issue
title: "plan_reconciler's review-branch PRs are piling up unmerged — 19 open, oldest 7 days, none merged"
summary: >-
  plan_reconciler.md STEP 7 ships every run's fixes to a review branch + opens a PR into `live-defi-rollout` (the
  "PROVING PHASE" gate — "no direct LDR write... while this agent is unproven"), with a stated escalation to a
  direct-push "STEADY STATE" only "after >=2 clean proven runs, operator-enabled." Verified live this session (`gh pr
  list --search "plan_reconciler" --state open --limit 50`, run twice, ~1h apart, same result both times): 19 open
  `plan_reconciler/*` PRs, oldest (`#1998`) opened 2026-08-02T12:53:13Z — 7 days old — none merged. This run's own PR
  will be the 20th. No doc in the `ao` tranche (or, per a corpus-wide grep, anywhere else checked) tracks this as a
  known/monitored condition, despite one `ao`-tranche doc (`ao_scheduled_job_reserve_and_staggering_2026_08_04.md`)
  extensively tracking plan_reconciler's own dispatch/sharding/timer reliability in detail.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, review-gate, pr-backlog, governance, plan-hygiene]
related:
  [
    /plans/active/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
    /plans/active/issues/plan_reconciler_findings_2026_08_09_ao.md,
  ]
created: "2026-08-09"
author: plan_reconciler
priority: P1
parent_epic: plan_hygiene_master
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: review
drift_direction: none
depends_on: []
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
locked_since:
context_scope:
  [unified-trading-pm/agents/plan_reconciler.md, unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md]
source: "plan_reconciler agt-fe4564 (slot 21), ao-tranche reconciliation run, 2026-08-09"
---

# plan_reconciler review-PR pileup — never merged, 2026-08-09

## What I found

`plan_reconciler.md` STEP 7 describes the current mode explicitly as a proving-phase safety rail:

> **PROVING PHASE (DEFAULT while this agent is unproven) — REVIEW GATE, no direct LDR write.** Open a PR from your
> review branch into live-defi-rollout... **STEADY STATE (ONLY after >=2 clean proven runs, operator-enabled)** —
> replace the review-branch push above with the conditional FF-push to LDR.

Measured live this session, twice (~1h apart, same result both times):

```
gh pr list --search "plan_reconciler" --state open --limit 50 --json number,title,createdAt
# => 19 open PRs
```

Oldest: `#1998` ("docs(plans): scheduled reconciliation undefined [review]"), opened `2026-08-02T12:53:13Z` — **7 days
old** at measurement time. Newest 2 (from earlier today, 2026-08-09) are `#2630` (defi tranche) and `#2631` (tradfi
tranche). None of the 19 show any review comments, approvals, or merge activity in the `gh pr list` output. This run's
own PR (opened at the end of this dispatch) will become the 20th.

A corpus-wide grep of all 33 non-grace `ao`-tranche docs this run for `review.?pr`, `review branch`, `merge queue`,
`PR backlog`, `plan_reconciler.*branch` returned zero hits describing this as a tracked concern anywhere in the tranche.

## Why it matters

If the PROVING PHASE gate is still the intended steady state (i.e., nobody has decided to flip to direct-push yet), then
**every plan_reconciler run for at least the past 7 days — sharded across cefi/defi/tradfi/prediction/sports/
cross-cutting/ao/ci/infra/ui, dozens of dispatches — has had zero effect on the live corpus.** Every verified flip,
every dangling-ref fix, every contradiction resolution documented in each run's findings doc is sitting in an unreviewed
branch, not actually reconciling anything a worker or the operator will ever read from `live-defi-rollout`. The
daily/twice-daily reconciliation cadence this skill runs on is only doing real work if someone is reviewing and merging
these PRs on a matching cadence — 0 merges against 19 opens over 7 days suggests that isn't happening.

This is also compounding: each new sharded run opens its OWN PR against the CURRENT state of `live-defi-rollout` (not
against the prior run's still-open PR), so PRs don't stack cleanly — if several get merged out of order, or if the same
doc was touched by two different tranche runs, conflicts become more likely the longer the backlog grows.

## Recommended next steps (operator ruling needed)

- **Option A** — review and merge (or close, for any that have gone stale/conflicting) the backlog now, then decide
  going forward whether plan_reconciler has proven itself enough to flip to STEADY STATE (direct FF-push, per its own
  documented escalation path).
- **Option B** — flip to STEADY STATE now without a manual backlog review, on the reasoning that plan_reconciler's own
  adversarial-verification discipline (every fix independently confirmed before applying) already provides the safety
  this gate was meant to add, and the backlog itself is evidence the gate isn't being exercised anyway.
- **Option C** — keep PROVING PHASE, but establish an actual review cadence (a standing runbook entry, or a
  human/main-agent task) so the backlog stops growing unbounded.
- **[WORKER REC]**: **A, then re-evaluate** — the 7-day-old PRs may already have merge conflicts or be superseded by
  later runs touching the same docs; a human pass to review/merge/close the backlog is needed regardless of which
  long-term mode is chosen, and doing that first gives the operator real signal on whether plan_reconciler's output has
  actually been trustworthy (informing the A-vs-B choice).

## Progress Log

- 2026-08-09 (plan_reconciler agt-fe4564, slot 21, ao-tranche run): Filed. PR count independently verified live twice
  this session (19, oldest 7 days, unchanged between checks). Not fixable by this agent — merging PRs and deciding the
  steady-state cutover are both human/operator actions. Routed via `/blocked`.
