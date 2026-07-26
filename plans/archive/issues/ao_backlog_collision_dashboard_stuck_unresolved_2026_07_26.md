---
doc_type: issue
title:
  Backlog Integrity panel showed genuinely-resolved collisions as unresolved forever — the Fix button's 404 path never
  logged a resolution event
summary:
  The dashboard's "Backlog Integrity" panel (ao_backlog_collision_alert_and_remediation_ui_2026_07_26 todo 4) pairs
  backlog_sibling_reset_guard_refused activity events with a later ...reminted event to decide what is still unresolved.
  remint_backlog_collision's 404-already-resolved path (server/routes/backlog.py) never logged a reminted event on that
  branch — so a collision that cleared EXTERNALLY (a later regen tick moved the checkbox off that id, or a manual
  todo-text reword forced a fresh id elsewhere, neither going through this endpoint) stayed permanently stuck in the
  panel — clicking Fix silently 404'd, refreshed, and produced zero visible change, forever. Confirmed live on two real
  collisions that had genuinely resolved hours earlier — both kept 404ing and both kept showing as unresolved.
status: resolved
nature: record
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, backlog, dashboard, ui, collision, sqlite]
related:
  [
    /plans/archive/issues/ao_review_agent_spawn_db_lock_under_load_2026_07_26.md,
    /plans/archive/issues/ao_dispatch_health_idle_slot_thrash_2026_07_26.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
source:
  Operator screenshot of the live dashboard showing 2 unresolved collisions, both clicking Fix with visibly no effect.
  Reproduced directly by curling the endpoint for both real task_ids — both returned 404 "already resolved or
  superseded" (confirming the underlying collision WAS actually clear), yet the dashboard kept showing them.
resolved_by:
  interactive session, 2026-07-26, agent-orchestrator@8842cd2 (shipped + deployed + verified live — both stuck
  collisions confirmed to have logged a reminted event and cleared from the panel)
locked_by:
supersedes:
superseded_by:
---

> **🟢 RESOLVED 2026-07-26** — fix shipped, deployed to the live orchestrator VM, and verified end-to-end (both real
> stuck collisions confirmed cleared).

# Backlog Integrity panel stuck-unresolved bug

## What I found

Operator reported the "Backlog Integrity" panel showing 2 unresolved collisions
(`hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install-004` and
`slot_stale_spawn_base_role_stuck_task_less-004`) where clicking "Fix" visibly did nothing.

Called `POST /api/backlog/{task_id}/remint-collision` directly for both: both returned
`404 {"detail": "... already resolved or superseded"}` — confirming the underlying collision had genuinely cleared (the
endpoint's own re-validation found the yaml no longer holds that exact colliding brief at that id). Cross-referenced the
full activity log (`/api/activity?types=backlog_sibling_reset_guard_refused,...collision_reminted`): both task_ids had
many `_refused` events (one recurring for ~3 hours straight) but **zero** `_reminted` events ever, despite having
stopped colliding hours before the screenshot was taken.

**Root cause**: `dashboard/src/layout.tsx::unresolvedBacklogCollisions()` builds the panel's list by pairing each
`_refused` event with a LATER `_reminted` event for the same task_id — if no `_reminted` event exists, it's shown as
unresolved, permanently, regardless of whether regen has since moved on.
`server/routes/backlog.py::remint_backlog_collision`'s 404-already-resolved branch (the case where the collision cleared
some way OTHER than this endpoint) never logged ANYTHING — so the pairing logic had no signal the collision was ever
over. The panel's own docstring already documented the INTENDED behavior ("the row is dropped by the caller's own
refetch") but the code never delivered on it.

A naive fix (log the event inside the same session about to raise the 404) would have been silently discarded:
`session_scope()` rolls back on ANY exception, and the function is about to raise one. A second naive fix (open a nested
`session_scope()` before raising) would have deadlocked on SQLite's single-writer lock — the SAME class of bug fixed in
`ensure_review_agents` earlier the same day (`ao_review_agent_spawn_db_lock_under_load_2026_07_26`).

## Fix

Restructured `remint_backlog_collision` into: (1) a `read_only_session_scope()` pass to fetch the flagged collision
record (no write lock taken), (2) if already-resolved, log the `backlog_sibling_reset_guard_collision_reminted` event in
its OWN freshly-opened `session_scope()` (committed independently, opened only after the read-only session has closed),
THEN raise the 404 — so the event is durably persisted regardless of the exception that follows, and (3) the actual
remint (still-colliding case) unchanged, in its own `session_scope()`.

- [x] ✅ [BACKEND] P1. Fix `remint_backlog_collision`'s 404-already-resolved path to log a `reminted` event
      (`resolution: "external"` in details, distinguishing it from a real remint). Regression test
      `test_remint_already_resolved_404_logs_a_reminted_event` added to `tests/test_backlog_remint_collision.py`;
      bug-injected (reverted the fix, kept the test) — confirmed it fails at the exact intended assertion; restored, all
      6 tests green; full `bash scripts/quality-gates.sh` green (1763 tests + dashboard tsc/vitest). (repo:
      agent-orchestrator) — agent-orchestrator@8842cd2
- [x] ✅ [OPS] P1. Deployed to the live orchestrator VM (`git pull --ff-only` on the VM's own checkout, per
      `/codex/05-infrastructure/agent-orchestrator-deploy.md`) — confirmed via `systemctl show` that
      `ActiveEnterTimestamp` did NOT change (a clean internal uvicorn `--reload`, not a forced restart — no repeat of
      the same-day stuck-shutdown incident, see `ao_dispatch_health_idle_slot_thrash_2026_07_26.md`). Re-called the
      endpoint for both real stuck task_ids post-deploy: both now log a `reminted` event with `resolution: "external"`,
      confirming the fix works end-to-end against production data.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — backlog/dispatch model this bug and fix both
  live in.
