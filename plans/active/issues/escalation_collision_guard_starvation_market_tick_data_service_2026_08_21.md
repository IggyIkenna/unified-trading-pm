---
doc_type: issue
title: >-
  Escalation agt-934add (market-tick-data-service, data_pipeline_failure) permanently starved by
  the repo-collision guard for 51+ min / 24+ attempts — identical shape to the 2026-08-15
  unified-trading-pm starvation that got a narrow per-repo exemption; market-tick-data-service is
  NOT in that exemption
summary: >-
  /escalation-queue-reconcile Step 1-2 (2026-08-21, this session) found escalation `agt-934add`
  (market-tick-data-service, data_pipeline_failure, no PR) stuck `status=queued`,
  `dispatched_at=null`, `resolved_at=null`, `resolution=null`, attempts climbing 21 -> 24 across the
  session, `last_error="repo 'market-tick-data-service' already active on another slot — not
  dispatching"`. This is `escalation.py:779`'s repo-collision dispatch guard, not the
  "no free configured slot" mechanism `ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md` diagnosed
  for a DIFFERENT MTDS escalation on 2026-08-18 (different `last_error` string, different code path
  — that one is closed on its own root cause; this is a new, distinct finding on the same repo).
  escalation.py's tuning constants are confirmed NOT drifted, and the reconcile/verify pass is
  confirmed live and working (a sibling escalation, agt-a5d400, correctly transitioned to
  `still_red_reescalated` ~9 min before this check). The guard itself is working as designed — the
  open question is whether `market-tick-data-service` should get the same narrow collision-guard
  exemption `unified-trading-pm` received on 2026-08-15
  (`escalation.py:778`, `_pm_escalation_collision_exempt`) after that repo's high concurrent-session
  traffic made the guard "close to an invariant," starving CI-escalation dispatch 15-45+ min at a
  time — the exact symptom shape now recurring here. A live Step-3 ask to `main`
  (`BLK-c4ad9761`) timed out unanswered after ~120s / 6 polls, so this is filed for the operator per
  the skill's own timeout-to-operator path.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao-watchdog, escalation-queue-reconcile, stuck-escalation, collision-guard]
related:
  [
    /plans/archive/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
    /plans/archive/2026_08/issues/escalation_queue_autospawn_enqueue_lag_45min_2026_08_15.md,
    /cursor-configs/skills/escalation-queue-reconcile/SKILL.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-21"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
assigned_role: infra
drift_direction: none
source: >-
  Scheduled escalation_queue_reconciler dispatch (dispatch_id agt-1f1440, slot 28), 2026-08-21 —
  GET /api/escalations/active surfaced the stuck row; escalation.py read directly to rule out
  mechanism drift and locate the existing unified-trading-pm exemption; live process tree
  (systemctl status orchestrator.service cgroup) confirmed genuine concurrent QG activity on
  market-tick-data-service, ruling out a stale/ghost lock.
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/escalation.py,
    cursor-configs/skills/escalation-queue-reconcile/SKILL.md,
    /plans/archive/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
  ]
---

# Escalation agt-934add starved by the repo-collision guard — market-tick-data-service needs the same exemption unified-trading-pm got, or a documented reason not to

## The row (last pulled 2026-08-21 ~09:52 UTC, re-confirmed fresh right before filing)

```json
{
  "escalation_id": "agt-934add",
  "status": "queued",
  "repo": "market-tick-data-service",
  "pr_number": 0,
  "wall_type": "data_pipeline_failure",
  "slot_id": null,
  "created_at": "2026-08-21T08:52:13.370953+00:00",
  "dispatched_at": null,
  "resolved_at": null,
  "resolution": null,
  "attempts": 24,
  "reescalations": 0,
  "last_error": "repo 'market-tick-data-service' already active on another slot — not dispatching"
}
```

`reescalations=0` and `resolved_at=null` rule out the re-escalation-aware exception in the
`/escalation-queue-reconcile` skill's own Step 1 (that exception is for a `queued` row reached via
`_mark_unresolved_and_maybe_reescalate` — this row never reached that cycle at all, because it has
never once been dispatched). Attempts climbed 21 -> 24 over the ~10 minutes of this session with
zero successful dispatches, on top of the 21 it already carried when first observed — roughly one
failed attempt every 2-3 minutes since `created_at` (~60 min ago at time of filing), all with the
identical `last_error`.

## What's confirmed NOT the cause

- **Tuning-constant drift**: `RESOLUTION_DEADLINE_MINUTES=45`, `MAX_REESCALATIONS=10`,
  `PAGE_AFTER_REESCALATIONS=2`, `RECONCILE_UNRESOLVED_WINDOW_HOURS=24` — all match the documented
  expected values exactly (`escalation.py:2165,2177,2185,2194`).
- **Reconcile/verify pass not running**: neither `retry_queued_escalations`,
  `verify_dispatched_escalations`, nor `reconcile_stale_unresolved_escalations` emit any
  `logger.*`/`log_activity` calls that would show up in `journalctl -u orchestrator.service` by
  function name — that absence is a (minor, secondary) observability gap in its own right, not
  evidence of non-liveness. Functional proof the pass IS running and working correctly: escalation
  `agt-a5d400` (market-tick-data-service, `ldr_qg_failure`, PR 1200)
  correctly transitioned to `status=queued`, `resolution=still_red_reescalated`, `resolved_at`
  ~09:34:27 UTC — about 9 minutes before this check — which is exactly
  `_mark_unresolved_and_maybe_reescalate`'s documented behavior firing live.
- **A stale/ghost repo-lock**: the systemd cgroup process tree for `orchestrator.service`, captured
  live during this session, showed a real, currently-running `pytest ... --cov=market_tick_data_service`
  QG process under a different slot's worktree — `market-tick-data-service` genuinely has an active
  worker on it right now, not a leaked reservation nothing ever released.

## Root cause: the repo-collision guard, working as designed, with no exemption for this repo

`escalation.py:765-791` (`_active_repos_excluding` check inside the escalation dispatch path):

```python
active_repos = _active_repos_excluding(session, _get_backlog(), exclude_slot=slot_id)
_pm_escalation_collision_exempt = repo == "unified-trading-pm"
if not _pm_escalation_collision_exempt and any(repo in repos for repos in active_repos.values()):
    if queue_on_no_capacity:
        return _queue_escalation(session, payload, escalation_id, f"repo {repo!r} already active elsewhere")
    log_activity(session, "escalation_dispatch_failed", slot_id=slot_id, details={...})
    raise EscalationError(f"repo {repo!r} already active on another slot — not dispatching")
```

The `_pm_escalation_collision_exempt` carve-out was added 2026-08-15
(`escalation_queue_autospawn_enqueue_lag_45min_2026_08_15.md`, now archived) because
`unified-trading-pm`'s exceptionally high concurrent-session traffic made "another slot already
active on unified-trading-pm" close to an invariant, starving CI-escalation dispatch on that one
repo for 15-45+ minutes at a stretch. The fix was scoped deliberately narrowly — "this repo only,
this function only" — reasoning that escalation workers do a narrow single-wall diagnose/fix, not
broad plan-doc churn, so exempting them from the collision guard is a smaller blast radius than the
general backlog-dispatch collision case the guard otherwise protects.

**`market-tick-data-service` is now showing the identical starvation shape** (repo not exempted,
guard permanently blocking a queued escalation for 50+ minutes with double-digit attempts) but it
is a *different* repo, and the same "narrow blast radius" reasoning applies equally to it (this
escalation is also a single-wall `data_pipeline_failure` fix, not broad churn). What is **not**
established from a single ~60-minute observation window is whether `market-tick-data-service`'s
traffic is genuinely "close to an invariant" the way `unified-trading-pm`'s is (every worker's
plan-doc flip touches PM; MTDS is a busy service repo but doesn't have that same structural
"every worker touches it every cycle" property) — or whether this is a temporary spike (several
slots happening to run heavy MTDS QG/backfill work concurrently right now) that will clear on its
own. Widening a dispatch-safety guard on the strength of one window felt like the wrong call to make
unilaterally.

## Step 3 attempted — no answer, deferred here per the skill's own timeout path

Posted `POST /api/slots/28/blocked` (`blocked_id: BLK-c4ad9761`, `authority: main_agent`) with the
above evidence and two options (extend the exemption vs. hold off pending more observation),
recommending "extend." Polled `GET /api/slots/28/messages` every ~15s for ~120s (6 polls,
heartbeating each), with `{"messages":[]}` throughout — no answer arrived inside the skill's 2-minute
bounded wait. Per Step 3, stopping here rather than holding the slot, and filing this doc as the
timeout-to-operator path.

## Open decision for the operator

- [ ] [OPERATOR] P1. Decide: extend `escalation.py:778`'s collision-guard exemption to include
      `market-tick-data-service` (mirrors the accepted `unified-trading-pm` precedent exactly — same
      narrow-blast-radius reasoning, same symptom shape), OR hold off and let this specific
      escalation clear naturally once the repo frees up, revisiting only if the pattern recurs across
      multiple future `/escalation-queue-reconcile` runs (which would itself be the multi-window
      evidence this session's single observation lacks). (repo: agent-orchestrator)
- [ ] [SCRIPT] P2. If the operator approves extending the exemption: widen the
      `_pm_escalation_collision_exempt` check (`escalation.py:778-779`) to a small allowlist
      (`repo in {"unified-trading-pm", "market-tick-data-service"}`), ship via the normal
      QG + quickmerge path, and re-verify `agt-934add` (or whatever escalation is live at fix time)
      actually dispatches on the next tick. (repo: agent-orchestrator)
- [ ] [SCRIPT] P3. Whichever way the P1 decision goes, consider adding a `logger.info`/`log_activity`
      call inside `retry_queued_escalations` (and the collision-guard branch specifically) so a
      future `/escalation-queue-reconcile` run doesn't have to fall back to functional-inference
      (a sibling row's state transition) to confirm the reconcile/verify pass is live — a direct log
      line would make Step 2's "is the pass actually running" check a straight `journalctl` grep
      instead of indirect reasoning. Small, non-urgent observability gap, not blocking. (repo:
      agent-orchestrator)
