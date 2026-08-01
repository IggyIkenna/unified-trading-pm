---
doc_type: issue
title:
  "Backlog regen silently reverted the manual park on `live_event_log_warm_sink_recovery_and_cold_compaction-011` (P1.2)
  — task re-dispatched to slot 12 despite unmet preconditions, recurrence of
  `backlog_regen_drops_handtuned_prereqs_2026_07_12.md`"
summary: >-
  On 2026-07-31 (~22:20Z) main answered BLK-085fef5e (Option A) and manually parked backlog task
  `live_event_log_warm_sink_recovery_and_cold_compaction-011` ([DATA] P1.2 in
  `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`) after 3 workers (slot-14, slot-8, slot-6) had
  already churned on it with zero possible progress — set `priority: 999` + `priority_override: true` + a false gating
  prerequisite `p1-2-preconditions-met`, per the plan's own Progress Log. At `2026-08-01T00:55:27Z` (~2h35m later) the
  task was dispatched to slot 12 anyway: live `GET /api/backlog` shows `priority: 20` (the plan-derived value, not 999)
  and the raw `data/config/backlog.yaml` entry shows `prereqs.prerequisites: []` (empty — the `p1-2-preconditions-met`
  attachment is gone). Both preconditions remain unmet regardless (only ~3h45m elapsed since the P1.1 redeploy
  `2026-07-31T21:14Z`, vs the required 24h; no paper run confirmed per the sibling issue doc below), so this is a live
  recurrence of the exact bug class `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` was supposed to have fixed
  (`agent-orchestrator@8dd5763`) — the fix either doesn't cover this code path or has regressed.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog, regression, park, prerequisites, plan-regen, fleet-churn]
related:
  [
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
    /plans/active/issues/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md,
  ]
created: "2026-08-01"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
drift_direction: none
assigned_role: infra
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found 2026-08-01 (slot 12) on /boot dispatch: task returned with `dispatch_reason: "resume"` / `already_in_progress:
  true` for a todo the plan's own Progress Log records as parked by main just ~2h35m earlier. Cross-checked `GET
  /api/backlog` (priority=20) and the live `data/config/backlog.yaml` entry (read-only, root `agent-orchestrator` clone)
  directly (`prereqs.prerequisites: []`), and independently re-verified the time-gate precondition is still unmet
  (~3h45m of the required 24h elapsed).
---

# Backlog regen reverted the manual park on P1.2 — recurrence of a previously-fixed bug class

## What I found

`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`'s `[DATA] P1.2` todo (the
`paper(W)==batch-rerun(W)` determinism recheck for BINANCE-FUTURES/ASTER/OKX-FUTURES) was manually parked by main on
2026-07-31 after this exact scenario had already churned through 3 workers in ~90 minutes with zero possible progress
(both preconditions — a 24h accumulation window since the `2026-07-31T21:14Z` P1.1 redeploy, and an active paper run
trading these 3 venues — were, and remain, unmet). Main's answer to `/blocked` (**BLK-085fef5e**, logged in the plan's
Progress Log) was Option A: set `priority: 999` + `priority_override: true` on backlog task
`live_event_log_warm_sink_recovery_and_cold_compaction-011`, plus a false gating prerequisite `p1-2-preconditions-met`,
so the fleet stops churning on it until both preconditions are genuinely met.

At `2026-08-01T00:55:27Z` this worker (slot 12) received this exact task on `/boot` (`dispatch_reason: "resume"`,
`already_in_progress: true`). Live-checked:

- `GET http://localhost:8765/api/backlog` → the task's entry shows `"priority": 20`, not `999`.
- The live `data/config/backlog.yaml` (read-only — root `agent-orchestrator` clone, the process cwd of the actual
  running `uvicorn server.server:app` — PID confirmed via `/proc/<pid>/cwd`) entry for
  `live_event_log_warm_sink_recovery_and_cold_compaction-011` shows `prereqs.prerequisites: []` (empty) — the
  `p1-2-preconditions-met` attachment is gone.
- Independently re-verified both underlying preconditions are STILL unmet regardless of the park state: only ~3h45m have
  elapsed since the `2026-07-31T21:14Z` P1.1 redeploy (need 24h, clears ~`2026-08-01T21:14Z`), and no paper run trading
  these venues has been confirmed to exist (see the sibling issue doc, which found this may be a standing gap, not just
  a timing one).

This is a live recurrence of `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` — the exact bug class
`agent-orchestrator@8dd5763` was supposed to have fixed (hand-tuned `priority_override` + `prereqs.prerequisites`
silently dropped by a regen tick). Either that fix does not cover whatever regen code path ran between
`~2026-07-31T22:20Z` (when main applied the park) and `2026-08-01T00:55:27Z` (this dispatch), or it has regressed.

## Why it matters

Without a fix, EVERY worker who gets dispatched this task will re-discover the exact same two unsatisfiable
preconditions main already ruled on — pure fleet churn, the precise failure mode the original park was created to stop.
This is now the 4th worker touched by this todo in <24h (slot-14, slot-8, slot-6, now slot-12) purely because the park
did not stick, and it will keep recurring every regen tick until the underlying regen-code gap is fixed, not just
re-applied by hand again.

## Recommended decision

- [ ] [OPERATOR] P0. Re-apply the park on backlog task `live_event_log_warm_sink_recovery_and_cold_compaction-011`:
      `priority: 999` + `priority_override: true` + `prereqs.prerequisites: [p1-2-preconditions-met]` in
      `agent-orchestrator/data/config/backlog.yaml` (root clone — requires main/operator-level write access; a
      dispatched worker's slot-scope rules forbid editing root clones), and confirm
      `POST /api/prerequisites/p1-2-preconditions-met {"value": false, "set_by": "main"}` is (re-)set false. Verify it
      actually stuck after the next `PlanRegenLoop` tick / `POST /api/backlog/regen` (not just `/reload`), per the exact
      verification recipe in `unified-trading-pm/agents/RULES.md` § 4.
- [ ] [AO] P1. Root-cause why the `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` fix
      (`agent-orchestrator@8dd5763`) did not prevent this reversion (repo: agent-orchestrator). Check whether
      `PlanRegenLoop` / `regen_backlog_from_plan.py` ran between `~2026-07-31T22:20Z` (park applied) and
      `2026-08-01T00:55:27Z` (this dispatch), and whether the preserved-field set that fix introduced covers BOTH
      `priority`/`priority_override` AND `prereqs.prerequisites` on every regen code path (`/api/backlog/regen` and
      `/api/backlog/reload` both, not just one) — this occurrence lost BOTH fields simultaneously, which the original
      fix should have carried forward for at least `priority_override`. Ship a fix + a regression test asserting a
      hand-tuned `priority_override: true` + `prereqs.prerequisites` entry survives a `PlanRegenLoop` tick unchanged.
- [ ] [SCRIPT] P2. Consider a standing assertion (hygiene sweep or a lightweight periodic check) that flags any backlog
      entry whose plan-todo text starts with "**⏸ PARKED" but whose live `priority` != 999 or `priority_override` !=
      true — this exact drift is otherwise silent until a worker happens to notice and file a doc like this one (repo:
      agent-orchestrator or unified-trading-pm, whichever owns the hygiene-sweep surface for this check).
