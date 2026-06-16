---
scope: [engineer, admin]
---

# Stale-Blocker Reaper

> Codified 2026-05-30 per `plan_hygiene_silent_failure_capture_2026_05_29.md` Phase 3.

## Purpose

The reaper surfaces tasks that have been `queued` for more than 3 days with at least one unmet prereq. Without the
reaper, such tasks silently accumulate — the dispatcher skips them on every `/boot` cycle but never alerts the operator.

## Background: How Blocking Works in the Orchestrator

There is **no `blocked` status** in the backlog DB. Tasks are blocked implicitly: the dispatcher (`server/dispatch.py`)
calls `_prereqs_met()` on every `queued` task and skips tasks whose `prereqs.completed_tasks` has any entry not yet
`status=done`. A task with unmet prereqs simply stays `queued` indefinitely with no automatic escalation.

Field inventory for the reaper:

| Field                     | Source         | Purpose                            |
| ------------------------- | -------------- | ---------------------------------- |
| `prereqs.completed_tasks` | `backlog.yaml` | The implicit `blocked_on` list     |
| `TaskRow.queued_at`       | SQLite `tasks` | Staleness timestamp                |
| `TaskRow.status`          | SQLite `tasks` | `queued` = candidate; `done` = met |

## Finding Categories

| Category       | Condition                                                         | Action                                          |
| -------------- | ----------------------------------------------------------------- | ----------------------------------------------- |
| `DEADLOCK`     | Blocked task AND its blocker are both `queued` with unmet prereqs | Slack alert; manual fix                         |
| `ORPHAN`       | Prereq task_id NOT found in backlog at all                        | Slack alert; remove from prereqs or re-add task |
| `PHANTOM_DONE` | Blocker is `done` but dependent is still `queued`                 | Info only; resolves on next `/boot` cycle       |

## Script

`unified-trading-pm/scripts/orchestrator/reap_stale_blockers.py`

```
python3 scripts/orchestrator/reap_stale_blockers.py [options]

  --backlog PATH    Path to backlog.yaml (default: agent-orchestrator/data/config/backlog.yaml)
  --db PATH         Path to SQLite state.db (default: agent-orchestrator/data/state/state.db)
  --stale-days N    Stale threshold in days (default: 3)
  --summary-dir D   Directory for daily summary log (default: system temp)
  --dry-run         Print findings; skip Slack + summary write
  --quiet           Suppress stdout
```

Exit 0 = clean or PHANTOM_DONE only. Exit 1 = DEADLOCK or ORPHAN found.

## Cron Schedule

Runs via **systemd timer** on the orchestrator VM at **04:00 UTC daily** (1 hour before the plan-hygiene sweep at 05:00
UTC):

```
systemd unit:  reap-stale-blockers.timer
service unit:  reap-stale-blockers.service
installer:     sudo bash scripts/orchestrator/install_reap_stale_blockers.sh
```

`Persistent=true` — if the VM was down at 04:00, the timer fires within 60 seconds of restart.

Daily summary files: `/var/log/orchestrator/reap_<YYYY-MM-DD>.log`

## Operator Response Guide

### DEADLOCK

Both the blocked task and its blocker are stuck. Causes:

- Two plans each declare the other's task in `prereqs.completed_tasks`
- A prereq task was never dispatched (e.g. `[HUMAN]` task pending operator action)

Resolution: identify which task is truly blocking and either (a) complete it, (b) remove the prereq from the YAML and
re-regen the backlog, or (c) manually flip the blocker to `done` if the work was done outside the orchestrator.

### ORPHAN

A prereq task_id exists in `prereqs.completed_tasks` but not in the backlog. Causes:

- The plan was edited to remove the task's `- [ ]` line without the task being completed
- A regen sweep replaced a task with a new ID (ID drift)

Resolution: either (a) remove the orphan ID from the blocked task's prereqs in the plan YAML + regen, or (b) re-add the
missing task to the plan so it can be completed.

### PHANTOM_DONE

The blocker is `done` but the dependent is still `queued`. This is almost always a transient state that resolves on the
next worker `/boot` cycle. If it persists >2h, check that `_prereqs_met()` is actually being called (no DB corruption).

## Cross-References

- `plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md` — Phase 3 design
- `codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md` — unpushed-plan alert (Phase 2)
- `codex/12-agent-workflow/epic-keyword-surface.yaml` — parent_epic alignment check (Phase 1)
- `scripts/plan-hygiene/run_hygiene_sweep.sh` — the 05:00 UTC sweep that runs in parallel
