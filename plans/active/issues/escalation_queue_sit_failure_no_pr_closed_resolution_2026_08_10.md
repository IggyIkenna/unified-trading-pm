---
doc_type: issue
title:
  sit_failure escalation walls on closed/superseded promote PRs can't machine-resolve — hold queued, spawn no-op
  workers, eventual false abandon/page
summary: >-
  `_poll_wall_resolution` (agent-orchestrator/server/escalation.py) returns None for ALL `sit_failure` walls — the
  2026-08-09 fix (884a9bf) gated machine-resolution to `_QG_SIGNAL_WALLS` = {ldr_qg_failure, main_ci_red} to stop
  false-resolving non-QG walls off an UNRELATED repo-wide LDR-QG-green signal. But the same function gives
  `ldr_qg_failure` (d990ed5) and `merge_conflict`/`stuck_promotion_pr` (`_CONFLICT_RESOLVER_WALLS`) a DIRECT
  PR-merged/closed check (`_pr_merge_state`) when the wall names a promote PR. `sit_failure` walls are
  promotion-PR-scoped (every observed row names a `promote/*→main` PR), yet never get that direct terminal check. Live
  2026-08-10: 3 queued `sit_failure` rows on now-CLOSED/superseded promote PRs (agt-7c472b PM#2713, agt-341788 PM#2712,
  agt-ca5389 PM#2708 queued 4-14h) can't machine-resolve, and dispatch is simultaneously blocked by the repo-collision
  guard (`active_repos_excluding`, escalation_backlog_repo_collision_blind_spot_2026_07_25) because PM is continuously
  occupied by 4+ dispatched sit_failure/ plan_health workers. Rows hold queued with a false "wall still RED" last_error,
  burn an attempt every tick, spawn no-op workers onto already-closed PRs when capacity finally opens, and eventually
  (QUEUE_TTL_HOURS=24 hold → HARD_ABANDON_HOURS=48) get abandoned + Slack-paged for walls closed ~48h prior. Proposed
  fix (mirrors d990ed5): extend the direct PR-closed/merged check to sit_failure when pr_number>0 — a closed/superseded
  promote PR is a definitive, DIRECT terminal signal, not the unrelated repo-wide QG-green the 08-09 fix protected
  against. Routed to main first (BLK-f7bb0212) per Step 3; timed out 2-min bounded wait — operator decision pending in
  /api/blocked.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [escalation, escalation-queue, sit_failure, agent-orchestrator, ci-cd, promotion]
related:
  [
    /plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md,
    /plans/archive/issues/escalation_watchdog_retune_and_reconcile_2026_08_07.md,
  ]
created: "2026-08-10"
author: escalation_queue_reconciler
source: agt-ddadf8
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by:
depends_on: []
---

# sit_failure escalation walls on closed/superseded promote PRs can't machine-resolve

Dispatch `agt-ddadf8` (escalation_queue_reconciler, slot 13), 2026-08-10 ~18:40Z. Findings from the 3-hourly
`/escalation-queue-reconcile` health check (Step 1 anomaly → Step 2 root-cause → Step 3 ask-main → Step 4 file).

## Finding

`agent-orchestrator/server/escalation.py::_poll_wall_resolution` returns `None` for every `sit_failure` wall — it is not
in `_QG_SIGNAL_WALLS`, and the pre-TTL return (`if wall_type not in _QG_SIGNAL_WALLS: return None`) fires BEFORE any
`_pr_merge_state` PR-closed/merged check. Consequence: a `sit_failure` wall scoped to a **promote PR** can never be
machine-resolved when that PR is closed/superseded (the promotion auto-drain closes each promote PR as a newer one
supersedes it — a constant occurrence). The row is then doubly stuck:

1. **Cannot self-resolve** — the probe has no terminal signal for it (by the 2026-08-09 `884a9bf` design, see below).
2. **Cannot dispatch** — the repo-collision guard (`active_repos_excluding` at escalation.py:548-564) refuses a second
   worker on `unified-trading-pm` while 4+ dispatched PM sit_failure/plan_health workers occupy it.

It eventually drains only by luck of capacity (a worker dispatches, finds the PR closed, marks resolved) or by the TTL
lifecycle (held at 24h with false `"wall still RED, no capacity"`, abandoned + Slack-paged at 48h for a wall closed ~48h
prior).

## Evidence (2026-08-10 ~18:40Z)

| escalation_id | status | repo               | wall_type   | PR                    | created → age | dispatched_at | attempts | notes                                                                   |
| ------------- | ------ | ------------------ | ----------- | --------------------- | ------------- | ------------- | -------- | ----------------------------------------------------------------------- |
| agt-7c472b    | queued | unified-trading-pm | sit_failure | #2713 (CLOSED 15:46Z) | 14:44Z → 4h   | null          | 98       | `last_error="repo 'unified-trading-pm' already active on another slot"` |
| agt-341788    | queued | unified-trading-pm | sit_failure | #2712 (CLOSED 14:01Z) | 13:52Z → 4.8h | null          | 127      | same                                                                    |
| agt-ca5389    | queued | unified-trading-pm | sit_failure | #2708 (CLOSED)        | ~04:33Z → 14h | null          | 181      | `reescalations=6`, same block                                           |

All six promote PRs named by this sit_failure wave (2708-2713) are `state=CLOSED` (superseded, `mergedAt=null`).
Dispatch loop IS active (autospawn tick retries every ~1-2 min, `journalctl` confirms); every retry re-probes
(`_poll_wall_resolution` → None for sit_failure), then raises the collision-guard `EscalationError`, `attempts++`.
Control case proving rows drain on capacity: `agt-0ab5b0` (market-tick-data-service data_pipeline_failure) was queued
18:37Z and dispatched ~18:40Z the moment an MTDS slot freed.

## Root cause

The 2026-08-09 fix `884a9bf` ("stop false-resolving non-QG walls") gated `_poll_wall_resolution`'s fallthrough to
`_QG_SIGNAL_WALLS = {ldr_qg_failure, main_ci_red}`. That fix's documented intent was to stop resolving non-QG walls off
the **unrelated repo-wide LDR-QG-green** signal (auto-closed 99-100% of sit_failure/data_pipeline_failure/plan_health
walls within minutes, zero worker dispatched). But the gate also removed the **direct PR-closed/merged** terminal check
from PR-scoped sit_failure walls — a signal that is NOT unrelated to the wall (a promote PR being closed/superseded
definitively clears a wall scoped to that PR). `ldr_qg_failure` retains exactly this check (d990ed5, 2026-08-06:
"resolve ldr_qg_failure walls on merged/closed promote PR"), as do `_CONFLICT_RESOLVER_WALLS` (merge_conflict /
stuck_promotion_pr). sit_failure is the promotion-PR wall type left without it.

## Step 3 — live main-agent ask (timed out)

Per the skill's Step 3 ladder (judgment call: "does this pattern match an accepted precedent or is it new"), posted
`BLK-f7bb0212` to `main_agent` (2026-08-10 ~18:45Z, `POST /api/slots/13/blocked`, `can_continue:false`,
`recommendation: A`) asking whether to extend the direct PR-closed/merged check to sit_failure with `pr_number>0`
(mirror d990ed5) vs leave the probe untouched and accept the stale-row cost. Polled `GET /api/slots/13/messages` with
heartbeats for the full bounded 2-minute window — **no answer**. Per the skill, stopped waiting (did not hold the slot);
the question persists in `/api/blocked` for the operator. This issue doc carries the full context so the operator does
not have to re-derive it.

## Proposed fix (if operator approves)

In `_poll_wall_resolution` (escalation.py:1693), for `wall_type == "sit_failure"` with `pr_number > 0`, apply the same
`_pr_merge_state` check the `ldr_qg_failure` block uses (escalation.py:1772-1791): merged → `pr_merged`; CLOSED not
merged → `pr_closed_superseded`. Do NOT add the head-branch QG poll (that signal is QG-specific and unrelated to a SIT
wall). Regression test in `tests/test_escalation.py` mirroring
`test_reconcile_prioritizes_recent_over_ancient_under_a_tight_limit`'s real-SQLite approach (a mock cannot catch a
probe-return contract). Gate: only apply when the escalate payload actually names a promote-style PR branch
(`promote/*→main`), so a hypothetical non-promote sit_failure on a feature PR isn't auto-closed off a repo-wide signal.

## Status / follow-ups

- [ ] [SCRIPT] P1. Operator decision on BLK-f7bb0212: approve extending the direct PR-closed/merged check to sit_failure
      with pr_number>0 (mirror d990ed5, add regression test, ship via quickmerge) — OR declare the current behavior
      intended and note why. (escalation_queue_reconciler, agt-ddadf8, 2026-08-10)

## Progress Log

- 2026-08-10 ~18:40Z — agt-ddadf8 (slot 13): Step-1 `/api/escalations/active` → 2 queued sit_failure rows past the
  45-min deadline (agt-7c472b, agt-341788). Constants verified intact (45/10/2/24). Reconcile pass verified correctly
  ordered (`order_by(resolved_at.desc())`). Dispatch loop confirmed active via journalctl. Row payloads + SQLite
  `last_error` confirm collision-guard block. PR states verified via `gh pr view` (all 2708-2713 CLOSED).
- 2026-08-10 ~18:45Z — Step 3: posted BLK-f7bb0212 to main_agent; polled 2 min bounded, no answer; deferred to operator
  via /api/blocked. Filed this issue doc per Step 4.
