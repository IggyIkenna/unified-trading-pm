---
doc_type: issue
title:
  Escalation dispatch spawns a fresh `data_pipeline_failure` worker per re-page even when an OPEN, already-diagnosed
  issue doc already covers the exact (asset_group, data_type, event) condition -- no dedup at the escalation-worker
  layer (distinct from the already-fixed Slack re-page cadence)
summary: >-
  Three `data_pipeline_failure` escalation workers (agt-7a4d1d, agt-27e235, agt-0df274) were dispatched across
  2026-07-28/29 for the SAME byte-identical `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) condition -- asset_group=cefi,
  data_type=derivative_ticker, `attempted_failed` numerator frozen at 158,085 across all three readings (only
  `captured`/ratio moved as the backlog partially recovers). The first two sessions did all the real work (root-caused +
  fixed 3 distinct code bugs, `market-tick-data-service@6a067cf1`/`@6c6fab03`) and left 3 deliberately-deferred P3
  todos; the third session (this one) found nothing new to fix and spent a full escalation-worker session re-confirming
  that. `dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md` (archived, all 3 todos done) already fixed the adjacent
  problem -- Slack re-paging the SAME condition every detector tick -- via a cadence-aware cooldown map
  (`_RECURRING_ALERT_COOLDOWNS`, 1800s for `DP_RUN_MOSTLY_EMPTY`) and a persisted re-nag interval in
  `check_high_attempted_failed`. Neither fix touches the SEPARATE escalation fast path (`repository_dispatch
  escalate-to-orchestrator`, `wall_type=data_pipeline_failure`) that spawns a full `data_pipeline_failure`
  orchestrator-agent session on every CRITICAL page that reaches it -- that path has no check for "is there already an
  OPEN issue doc filed for this exact (asset_group, data_type, event) tuple, and if so, is a fresh worker actually
  needed vs. just appending to its Progress Log / verifying nothing regressed." This is real orchestrator-capacity waste
  (a full agent session per re-page of a KNOWN condition) and is NOT covered by the archived 2026-07-15 fix (that fix is
  about Slack noise, this is about escalation-worker dispatch).
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags: [monitoring, alerting, data-pipeline, observability, escalation, dp-fetch-009, dedup, orchestrator-capacity]
related:
  [
    /plans/active/issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md,
    /plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-29
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "data_pipeline_failure escalation worker (agt-0df274), found while working
  cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md's third re-fire"
last_updated: 2026-07-29
---

# Escalation-worker dispatch has no "already an open issue doc" dedup check

## What I found

The `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009, `check_high_attempted_failed`) alert fired three times in ~24h for the
identical `(asset_group=cefi, data_type=derivative_ticker)` cell, each time spawning a fresh `data_pipeline_failure`
orchestrator-agent session (`agt-7a4d1d` 2026-07-28, `agt-27e235` 2026-07-28, `agt-0df274` 2026-07-29). Evidence the
condition did NOT change between firings: the `attempted_failed` numerator was byte-identical (158,085) across all three
readings -- only the denominator (`captured`) grew, dropping the ratio 11.2%→10.9%, i.e. this is the SAME static backlog
the first session already split and mostly fixed, not a new failure batch.

This is a DIFFERENT layer from the already-fixed problem in `dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`
(archived, all 3 todos `[x]`): that fix added a cadence-aware Slack cooldown (`_RECURRING_ALERT_COOLDOWNS`, 1800s) and a
persisted re-nag interval to the detector itself, so `#data-pipeline-alerts` isn't spammed every 15-min tick. But the
escalation fast path (`repository_dispatch escalate-to-orchestrator`, `wall_type=data_pipeline_failure`, per
`/codex/05-infrastructure/data-pipeline-alerts.md` § "self-heal actuator layer") apparently still fires a full
worker-spawn on each CRITICAL page that reaches PagerDuty/Telegram, with no check for "is there already an OPEN issue
doc filed for this exact tuple, and would a fresh full diagnosis actually find anything new."

**Not investigated in this session** (out of scope for a one-shot `data_pipeline_failure` escalation worker, and this
repo is `market-tick-data-service` — this issue's fix lives in `agent-orchestrator`/`deployment-service`):

- The exact call site in `agent-orchestrator` that receives the `repository_dispatch` and decides to spawn a
  `data_pipeline_failure` worker — whether it already has ANY notion of "this escalation_id maps to an existing issue
  doc" (the `source:` frontmatter field in the issue docs I read suggests escalation_id is recorded, but not clear
  whether it's used to SKIP a redundant spawn).
- Whether spawning a fresh worker every time is actually intentional design (e.g. "always re-verify the condition hasn't
  gotten WORSE, cheaply") vs. an oversight — this is a genuine design question, not a mechanical bug fix.

## Recommended decision

This needs an operator/design call on the right dedup semantics before implementation (marked `assigned_vm: NA` — not
AO-dispatch-eligible as a bare "fix it" todo per the workspace's dispatch-scope-eligibility rule). Options:

A: **Before spawning, check for an OPEN issue doc matching `(asset_group, data_type, event)` in its
`source:`/tags/title.** If found AND the alert's own numerator/ratio hasn't moved since that doc's `last_updated`, skip
the full worker spawn — instead append a one-line "re-fired, still static, no new action" note directly (a cheap
deterministic check, not a full diagnosis) and re-arm the Slack cooldown. [RECOMMENDED — closes the actual waste without
losing detection of genuine regressions, since a numerator MOVING still triggers a full worker] B: **Leave dispatch
as-is; only reduce PagerDuty/Telegram page frequency further** (extend the 1800s cooldown) so fewer re-pages reach the
escalation fast path at all — cheaper to implement but weakens "genuinely got worse" detection latency. C: **Do nothing
— the current 3-worker cost for this condition was small in absolute terms and the alternative (missing a real
regression) is worse.**

## Todos

- [ ] [DESIGN] P2. Operator/main-agent decision: pick option A/B/C above (or a variant), scoped precisely enough to
      dispatch as a bounded AO todo once decided.
- [ ] [CODE] P2. Once decided: implement the chosen dedup check in the escalation dispatch path
      (`agent-orchestrator`/`deployment-service`, exact call site TBD by whoever picks this up).

## Progress Log

- **2026-07-29 (data_pipeline_failure escalation worker, agt-0df274):** Filed this issue after finding a third
  escalation-worker spawn for the same static DP-FETCH-009 condition already fully diagnosed by two prior sessions. Did
  not implement a fix (design decision + wrong-repo for this one-shot's target repo). Cross-referenced from
  `cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md`'s Progress Log.
