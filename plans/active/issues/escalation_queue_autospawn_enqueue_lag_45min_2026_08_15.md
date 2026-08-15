---
doc_type: issue
title: >-
  AO's one-worker-per-repo collision-safety check starves CI-escalation dispatch on unified-trading-pm specifically —
  repo's own exceptionally high concurrent traffic means "another slot already active" is nearly always true
summary: >-
  Found + ROOT-CAUSED live during a `/autonomous` 2-hour watch on the 2026-08-15 promote-PR QG debounce realignment
  (`unified-trading-ci@a7e4980`). A genuine, real, ~2.5-hour continuous `quality-gates-v2` failure on
  `unified-trading-pm`'s promote-PR path (root cause: a prettier proseWrap continuation-padding ratchet violation,
  `[hard] FAIL`, being actively hand-repaired by other sessions in parallel — corpus baseline visibly dropping 3655→2617
  over the investigation window) correctly triggered the streak-based debounce and repeatedly escalated to AO as
  `wall_type=promote_qg_failure` — confirming that mechanism (built 2026-08-13, threshold realigned today) is working
  exactly as designed. But every one of those escalations sat `status: "queued"`, `attempts: 0`, for 15-45+ minutes —
  confirmed via `GET /api/escalations/active` on the orchestrator (i-0c9b283b31d6b5ca7).

  **Root cause, confirmed via `journalctl -u orchestrator.service`**: this is NOT a dead/broken `AutoSpawnLoop` — it IS
  ticking (every ~60s per `ORCHESTRATOR_AUTOSPAWN_INTERVAL_SECONDS` default) and IS attempting `retry_queued_
  escalations()` on every tick. The repeated, consistent log line is `escalation retry <id>: slot-specific spawn failure
  (repo 'unified-trading-pm' already active on another slot — not dispatching); skipping to next queued wall` — a
  legitimate collision-safety check (mirrors this workspace's own "same file/repo never runs two agents at once" hard
  rule) correctly refusing to spawn a SECOND worker into `unified-trading-pm` while ANY other slot is already active
  there. The bug isn't in the check — it's that `unified-trading-pm` has such exceptionally high concurrent traffic
  today (confirmed independently all session: `ps aux` showed 5-9+ live Claude sessions rooted at this exact repo
  checkout, 32-35+ autostash entries from repeated collision-quarantine cycles, near-continuous quickmerge activity)
  that "another slot is active on unified-trading-pm" is very close to an INVARIANT right now, not an occasional
  condition — so escalation dispatch for this repo can queue effectively indefinitely even though the retry loop is
  functioning exactly as coded, tick after tick. This is a genuine, real starvation pattern, but the starving mechanism
  is a correct safety check meeting an unusually busy repo, not a defect in the mechanism itself — distinct from the
  debounce mechanism itself, which is validated working correctly (§ separate finding above). General AO worker-pool
  health is unaffected: `check-ao-backlog-status.sh` shows `LIVE_WORKER_SESSIONS=13` and ordinary backlog dispatch
  (`dispatched: 8`) proceeding normally the whole time — this is specific to escalation-targeted spawns hitting the
  same-repo collision guard.
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, escalation-queue, autospawn, worker-liveness, ci-reconcile]
related:
  [
    /cursor-configs/skills/ci-reconcile/SKILL.md,
    /codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.72
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope: [agent-orchestrator/server/escalation.py, agent-orchestrator/server/]
source: >-
  Found live during a `/autonomous` 2-hour polling watch on the 2026-08-15 CI-alert debounce realignment
  (unified-trading-ci@a7e4980), scheduled from an earlier same-day /ci-reconcile session.
---

# AO one-worker-per-repo collision guard starves unified-trading-pm escalations

## Todos

- [x] [SCRIPT] P1. **Diagnose why escalation-queue entries for unified-trading-pm weren't dispatching despite a healthy
      general worker pool.** ✅ **DONE 2026-08-15** — root-caused via live `journalctl -u orchestrator.service` log
      evidence (see summary): NOT a dead/broken `AutoSpawnLoop`; it ticks every ~60s and calls
      `retry_queued_escalations()` correctly. The repeated blocker is a legitimate slot-collision guard
      (`repo 'unified-trading-pm' already active on another slot — not dispatching`) meeting this repo's own
      exceptionally high concurrent-session traffic. Full trace in the summary above.
- [ ] [OPERATOR] P1. **Policy decision: should CI-escalation dispatch get an exemption from (or a reserved-slot
      carve-out around) the one-worker-per-repo collision guard specifically for `unified-trading-pm`, given how often
      that repo has an active slot at any given moment?** Two real options, both with tradeoffs: (a) exempt
      escalation-targeted spawns from this specific guard for this specific repo (risks the exact collision the guard
      exists to prevent — two workers editing unified-trading-pm concurrently — though escalation workers are typically
      diagnosing/CI-fixing rather than doing broad plan-doc churn, a narrower blast radius than the general case the
      guard was built for); (b) leave the guard as-is and accept that unified-trading-pm CI escalations may routinely
      wait tens of minutes to hours for a quiet slot window — which may already be acceptable given the streak-based
      Slack CRITICAL (today's fix) already tells a human directly at 30min, independent of whether AO ever gets a worker
      slot to act on it. **Done when**: the operator picks a direction (or explicitly rules "acceptable as-is, Slack
      CRITICAL is the real signal for this repo") and, if (a), the exemption is scoped + implemented in
      `agent-orchestrator/server/escalation.py`'s slot-selection logic.
- [ ] [DOCS] P2. **Once a direction is picked, document it** in
      `/codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md` (or the appropriate AO architecture doc)
      so a future `/ci-reconcile` § 5 check knows this is a KNOWN, understood tradeoff for unified-trading-pm
      specifically (not a fresh mystery to re-diagnose) — a healthy general worker pool does not imply a healthy
      escalation drain for this one repo, and that's expected given its traffic, not a bug to keep re-finding.
