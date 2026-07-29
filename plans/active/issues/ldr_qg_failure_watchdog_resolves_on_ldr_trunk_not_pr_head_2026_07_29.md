---
doc_type: issue
title:
  Escalation watchdog resolves a promotion-PR-scoped `ldr_qg_failure` wall as `qg_v2_green` by checking LDR TRUNK's own
  quality-gates-v2 conclusion, never the actual PR head — false-positive "resolved" while the PR stays genuinely red;
  also answers the open root-cause question in `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`
summary: >-
  Dispatched as `cicd` one-shot escalation `agt-0cd704` to fix `ldr_qg_failure` on `unified-api-contracts` promotion PR
  #796 (LDR→main). Diagnosed the original wall as transient host contention (a `uv` build-isolation flake), then hit an
  unrelated much bigger fleet-wide GitHub Actions account-level billing wall while trying to re-gate the PR (tracked
  separately: `github_actions_billing_wall_recurrence_2026_07_29.md`). When attempting `/done`, got the familiar
  `"one_shot_complete ... no active agent owns its session"` 400. Querying `GET /api/escalations/active` directly
  (rather than assuming, per the sibling doc's own recommended-decision todo) showed `agt-0cd704` was already `status:
  "resolved", resolution: "qg_v2_green", resolved_at: "2026-07-29T20:24:11Z"` — but PR #796's own head check (`gh pr
  view 796`) is STILL `mergeStateStatus: UNSTABLE` and the PR head's `quality-gates-v2` run history shows only
  `failure`/`startup_failure`, never a green run. **The escalation was marked resolved while the promotion PR it was
  dispatched to fix is still genuinely blocked.** Read `server/escalation.py::_poll_wall_resolution` — confirmed root
  cause: for `wall_type="ldr_qg_failure"` (not in `_CONFLICT_RESOLVER_WALLS = {merge_conflict, stuck_promotion_pr}`),
  the PR-state check is skipped entirely and resolution falls straight to `ci_reconcile.repo_ldr_qg_conclusion(repo)` —
  which queries the LATEST `quality-gates-v2` run on `live-defi-rollout` (the integration branch), NOT the specific PR
  head the escalation was created for. In this case LDR's own trunk had a green `workflow_dispatch` run at 16:31:50Z (an
  unrelated retry, done before the worker was even dispatched at 20:13:59Z) — the watchdog saw that stale trunk-level
  green and immediately closed the escalation 9 minutes after dispatch, despite PR #796's own head never having passed.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, escalation, ldr_qg_failure, false-resolution, promotion-pr, watchdog, one-shot, agentrow]
related:
  [
    /plans/active/issues/cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md,
    /plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md,
    /plans/active/issues/github_actions_billing_wall_recurrence_2026_07_29.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-29
parent_epic: agent_operating_framework_master
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.3
assigned_role: backend_engineer
assigned_vm: planning
execution_scope: orchestrator-agent
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
source: "cicd escalation agt-0cd704, slot 9, unified-api-contracts PR#796 (ldr_qg_failure), 2026-07-29"
---

# `ldr_qg_failure` watchdog resolves on LDR trunk health, not the actual PR head

## What I found

**Confirmed via direct API query** (not assumed): `GET /api/escalations/active?include_resolved_within_hours=6` shows

```json
{
  "escalation_id": "agt-0cd704",
  "status": "resolved",
  "repo": "unified-api-contracts",
  "pr_number": 796,
  "wall_type": "ldr_qg_failure",
  "slot_id": 9,
  "created_at": "2026-07-29T16:03:55Z",
  "dispatched_at": "2026-07-29T20:13:59Z",
  "resolved_at": "2026-07-29T20:24:11Z",
  "resolution": "qg_v2_green",
  "attempts": 1
}
```

**But the actual promotion PR is not green.** `gh pr view 796 --repo IggyIkenna/unified-api-contracts` at the time of
this write-up (2026-07-29 ~21:00Z, well after the 20:24:11Z "resolved" timestamp):

```json
{ "mergeStateStatus": "UNSTABLE", "mergeable": "MERGEABLE", "state": "OPEN" }
```

and the PR head branch's (`promote/unified-api-contracts/42feddaaeee6`) own `quality-gates-v2` run history shows only:

- `30468558109` (`pull_request`, 15:59:21Z) → `failure` (the original wall)
- `30489949022`, `30490035042` (`workflow_dispatch`, 20:49-20:50Z) → `startup_failure`

**No run on the PR head has ever succeeded.** The escalation is "resolved" but the thing it was dispatched to fix is
still broken.

## Root cause (confirmed by reading `server/escalation.py`)

`_poll_wall_resolution(repo, pr_number, wall_type)` (line ~1321):

```python
if pr_number and wall_type in _CONFLICT_RESOLVER_WALLS:   # {"merge_conflict", "stuck_promotion_pr"} ONLY
    ...  # gh pr view --json state,mergedAt  (checks the actual PR)
    ...
try:
    conclusion = ci_reconcile.repo_ldr_qg_conclusion(repo)   # <-- default branch=live-defi-rollout, NOT the PR head
except Exception:
    ...
if conclusion == "success":
    return "qg_v2_green"
```

`ldr_qg_failure` is **not** in `_CONFLICT_RESOLVER_WALLS` (line 99:
`frozenset({"merge_conflict", "stuck_promotion_pr"})`), so for this wall type the PR-specific branch is skipped entirely
regardless of whether `pr_number > 0`. Resolution falls straight to `ci_reconcile.repo_ldr_qg_conclusion(repo)`
(`server/ci_reconcile.py:157`), whose default `branch=_INTEGRATION_BRANCH` (`"live-defi-rollout"`, line 52) queries
**the latest `quality-gates-v2.yml` run on LDR trunk** — a fleet-level signal, not the specific PR's head commit.

For `unified-api-contracts`, LDR trunk itself had a green `workflow_dispatch` run at `16:31:50Z` (an unrelated retry of
the same LDR commit, done well before this worker was even dispatched at `20:13:59Z`). The watchdog polled trunk health
~9 minutes into dispatch, saw that pre-existing green, and closed the escalation — even though PR #796's own snapshot
(`promote/unified-api-contracts/42feddaaeee6`, frozen at a slightly older LDR commit) has never itself passed
`quality-gates-v2`.

**The code comment at line ~1334 states the (incomplete) intent**: _"A green LDR QG is a fleet-level signal (any commit
could have greened it), but for an escalation that is exactly the intent — the wall the worker was sent to clear is
gone."_ That reasoning holds for a bare `ldr_qg_failure` wall with `pr_number=0` (no PR, LDR trunk itself was red — LDR
going green IS the fix). It does **not** hold when `pr_number > 0`: the wall in that case is "this specific promotion
PR's gate is red," and a promotion PR is a **frozen snapshot** of LDR at dispatch time — LDR moving on and going green
afterward says nothing about whether the frozen PR snapshot's own check ever passed.

## This answers the open question in `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`

That doc's first recommended-decision todo asks whether a staleness/orphan-reap heuristic is what silently archives a
one-shot `cicd` worker's `AgentRow` mid-session (that doc could not confirm the mechanism, only rule out two other
candidates). **This session's evidence points to a fourth, more mundane, and now fully-confirmed mechanism for at least
the `ldr_qg_failure` + `pr_number>0` case**: `_mark_resolved` (called immediately after `_poll_wall_resolution` returns
a verdict) almost certainly also closes out the dispatched worker's session/AgentRow as part of resolving the escalation
— i.e. the AgentRow archival isn't a separate stale-reap bug at all here, it's the watchdog correctly tearing down a
session for an escalation it (incorrectly) believes is done. This doesn't contradict that doc's other three ruled-out
mechanisms; it's simply a fourth, distinct, now-confirmed trigger specific to PR-scoped `ldr_qg_failure` walls.

## Why it matters

- **Silent false-positive resolution, fleet-wide**: any `ldr_qg_failure` escalation tied to a promotion PR
  (`pr_number > 0`) can be marked `resolved: qg_v2_green` purely because LDR trunk moved on and passed its own gate for
  an unrelated later commit — while the specific PR the worker was dispatched to unblock stays red indefinitely.
  Dashboards/operators reading escalation status would see "resolved" and reasonably assume the PR is unblocked.
  Combined with the `*/5` `ldr-to-main-promote-fleet` cron eventually generating a FRESH promote PR against current LDR
  HEAD, an operator might never notice the original PR silently stalled, masked by "resolved" status — this is the same
  failure shape (symptom vs. cause) already named in `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`,
  but a new, distinct root cause within it.
- **Blocks a clean one-shot worker exit**: this is confirmed as (at least) one concrete trigger for the
  `one_shot_complete ... no active agent owns its session` 400 family already tracked across 3 sibling docs — a worker
  whose escalation gets falsely resolved out from under it has no way to signal `/done` for work it may still be
  actively doing.

## Recommended fix

- [ ] [BACKEND] P1. In `_poll_wall_resolution`, when `wall_type == "ldr_qg_failure"` AND `pr_number > 0`: check the **PR
      head's own** `quality-gates-v2` conclusion (e.g. `gh pr checks <pr_number>` or
      `gh api     repos/<owner>/<repo>/commits/<pr_head_sha>/check-runs` filtered to the `quality-gates-v2` context),
      not `ci_reconcile.repo_ldr_qg_conclusion(repo)` (LDR trunk). Only fall back to the LDR-trunk check when
      `pr_number == 0` (the bare-LDR-red case the current code correctly handles). (repo: agent-orchestrator)
- [ ] [BACKEND] P2. Once fixed, audit currently-`resolved: qg_v2_green` `ldr_qg_failure` escalations with
      `pr_number >     0` from the trailing 24-48h for the same false-positive pattern (any whose PR is still open +
      unmerged + its own head check never went green) — this session only confirms one instance (`agt-0cd704`/#796);
      given the fleet-wide billing-wall incident happening the same day (many PR heads red while LDR trunk itself
      intermittently passed), there may be several more silently mis-marked "resolved" right now. (repo:
      agent-orchestrator)
- [ ] [BACKEND] P3. Once the fix lands, re-open `unified-api-contracts` PR #796's `ldr_qg_failure` wall for a fresh,
      correctly-scoped dispatch (or confirm it self-clears via the promote-fleet cron regenerating a fresh PR against
      current LDR HEAD, which would make a fresh dispatch moot). (repo: unified-api-contracts / agent-orchestrator)

## Evidence

- Escalation record: `GET /api/escalations/active?include_resolved_within_hours=6`, entry for `agt-0cd704` (captured
  above).
- PR #796 actual state: `gh pr view 796 --repo IggyIkenna/unified-api-contracts --json state,mergeable,mergeStateStatus`
  → `UNSTABLE`/`MERGEABLE`/`OPEN`, ~21:00Z, 36 min after "resolved_at".
- PR head run history:
  `gh run list --repo IggyIkenna/unified-api-contracts --branch promote/unified-api-contracts/42feddaaeee6 --workflow quality-gates-v2.yml`
  → runs `30468558109` (failure), `30489949022`/`30490035042` (startup_failure) — no success ever recorded for this ref.
- Code: `agent-orchestrator/server/escalation.py:99` (`_CONFLICT_RESOLVER_WALLS` definition), `:1321-1390`
  (`_poll_wall_resolution`), `agent-orchestrator/server/ci_reconcile.py:52,157-179` (`_INTEGRATION_BRANCH` default +
  `repo_ldr_qg_conclusion`).
- `/done` 400 (consequence, not cause): two attempts (`task_id: ""` and `task_id: "agt-0cd704"`), identical
  `"one_shot_complete on slot 9 but no active agent owns its session 'orch-slot-9' ..."`.

## Progress Log

- 2026-07-29 ~21:05Z (cicd escalation `agt-0cd704`, slot 9): filed after confirming via direct API query (per the
  sibling doc's own recommended practice of checking rather than assuming) that the escalation had already been
  false-resolved while PR #796 stays genuinely red. Read `escalation.py`/`ci_reconcile.py` to confirm the exact code
  path; no fix attempted (backend-engineer-scoped, outside a one-shot cicd worker's remit). Not re-attempting `/done`
  again — the escalation is already `status: resolved` server-side regardless of whether that resolution is correct, so
  no further `/done` call will succeed or is needed; ending this turn here.
