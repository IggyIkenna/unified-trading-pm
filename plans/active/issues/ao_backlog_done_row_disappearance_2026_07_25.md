---
doc_type: issue
title: >-
  37 of 55 genuinely `done` agent-orchestrator backlog tasks vanished from state.db within 6.5 hours, via a path that is
  not in the application code, not logged anywhere, and contradicts the dashboard's own documented invariant
summary: >-
  A live investigation (prompted by the operator noticing the dashboard's Backlog Detail counts shrinking unexpectedly)
  confirmed, via a real historical S3 snapshot cross-referenced against the live DB, that 37 specific tasks which were
  genuinely `status='done'` at 2026-07-25T13:45:21Z are completely absent from `state.db` ~6.5 hours later -- not
  reclassified, not renamed, just gone. The only known deletion code path (`regen_backlog_from_plan.py::_prune_stale`)
  is SQL-filtered to `status IN ('queued','blocked') AND dispatched_to IS NULL` and is confirmed identical between the
  local checkout and the deployed VM -- structurally incapable of touching a `done` row. The dashboard's own tooltip
  text states the intended design outright: "done orphans are audit history" (meant to persist forever). No activity-log
  event, journal line, or known endpoint call explains the disappearance. Root cause NOT yet found -- a live watch
  process has been armed on the orchestrator VM to try to catch a recurrence in the act.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, data-integrity, state-db, backlog, sqlite, audit-history, unexplained, recurring-risk]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Operator noticed the AO dashboard's Backlog Detail modal showing a much-shrunk total count than an earlier screenshot
  and asked "shouldn't the db be over 100 if it didn't delete tasks" -- investigated live this session via a real
  historical S3 DR-backup snapshot, direct SQL queries (after installing sqlite3 on the VM), the deployed service's
  systemd journal, and the /api/activity log, cross-referenced against both the local and the actually DEPLOYED copy of
  the relevant code.
resolved_by:
locked_by:
locked_since:
---

# 37 done backlog tasks vanished from state.db with no known cause

## What's confirmed (hard evidence, not speculation)

1. **A real historical snapshot exists and is unambiguous.** The orchestrator's periodic DR-backup mechanism
   (`server/gcs_sync.py`-adjacent; actual location for this VM is S3,
   `s3://uts-orchestrator-state-427895769566/snapshots/planning/2026-07-25/`) writes a full JSON export of the `tasks`
   table roughly every 15-30 minutes. The file `state_20260725T134522Z.json`
   (`exported_at: 2026-07-25T13:45:21.382738+00:00`) is a near-exact match for the operator's own screenshot timing
   (both show `cancelled: 1`, confirming this is the right moment). It contains **129 total tasks**:
   `done=55, queued=60, dispatched=9, cancelled=1, blocked=4`.
2. **Direct SQL query against the live `state.db` right now** (installed `sqlite3` on the VM for this — it was not
   previously present) shows **41 total tasks**: `done=24, queued=14, blocked=3` — exactly matching what `/api/backlog`
   reports live, confirming that endpoint reflects the true row count with no hidden filtering.
3. **Per-task-id diff.** Extracted the exact 55 task_ids that were `status='done'` in the 13:45 snapshot and checked
   each one against the live `/api/backlog` response right now:
   - **18 still present**, still `done`, untouched.
   - **37 completely absent** — not in the response at all, under any status.
   - The 37 gone: `deployment_registry_firestore_p0_unblock-006/-008`,
     `deployment_api_inventory_cold_path_concurrent_oom-002`,
     `sports_satellite_ao_dispatch_batch2-008/-009/-028/-033/-039` (but sibling `-005` from the SAME plan survived),
     `recovery_plan_source_liveness_probe_gap-002`, `deployment_registry_reaper_not_draining_stale_entries-001`,
     `ao_worker_context_lifecycle_gap-002/-008/-009/-012` (but sibling `-001` from the SAME plan survived),
     `deployment_promote_squash_ancestry_false_negative-001`, `defi_gmx_venue_removal-001/-003`,
     `terminal_status_archival_backlog_sweep-002` through `-015` (all 14 of them),
     `utl_prod_cloud_build_trigger_missing_fleet_stale_base_image-001/-002` (but sibling `-003` survived),
     `cloudbuild_yaml_unescaped_substitution_comments_fleet_wide-001/-002/-003/-004`.
4. **The one known code path cannot explain it.** `server/regen_backlog_from_plan.py::_prune_stale` issues the only
   `DELETE FROM tasks` statement in the entire codebase (confirmed via `grep -rn "DELETE FROM tasks" server/` on BOTH
   the local checkout and the actually-deployed VM copy — byte-identical). The statement:
   `DELETE FROM tasks WHERE task_id IN (...) AND status IN ('queued','blocked') AND dispatched_to IS NULL`. Its own
   docstring states outright: _"done/dispatched rows are NEVER touched."_ This is architecturally correct per the code —
   it cannot be the mechanism.
5. **Systemd journal cross-check.** Pulled every `Plan regen complete` / `PlanRegenLoop tick complete` line from 13:00Z
   to ~19:00Z. Every `pruned_db` value logged in that window (5, 5, 40, 1, 5, 30, 1, 1, ...) sums to approximately the
   TOTAL row-count drop (129→41 ≈ 88) — but that arithmetic is satisfied by `queued`/`blocked` deletions alone (the
   confirmed mechanism), consistent with the one large legitimate batch at `16:21:34Z` (`pruned_db=40`, all 40 IDs are
   `terminal_status_archival_backlog_sweep-056` through `-096` — never-dispatched archive-todos whose own plan had just
   been archived, exactly the zombie-GC shape `_prune_stale` is designed for). **This total-row arithmetic balancing is
   a coincidence of the numbers, not proof of a single mechanism** — the per-ID diff in point 3 proves specific `done`
   rows are ALSO gone, which the queued/blocked-only prune cannot do, meaning the true picture is (a) the confirmed
   queued/blocked GC (real, sanctioned, working as designed) PLUS (b) a second, unidentified mechanism removing `done`
   rows, offset by enough newly-ingested/newly-completed tasks in the same window that the net total still lines up.
6. **No activity-log trace.** Pulled up to 5000 `/api/activity` events spanning 09:07Z–20:00Z today. Zero events of type
   `backlog_task_deleted` (the one endpoint — `DELETE /api/backlog/{task_id}`, `server/routes/backlog.py:257` — that CAN
   remove a `done` row on operator request always logs this event type) and zero events matching
   `prune`/`reset`/`restore`/`backup`/`regen`/`vacuum`/`delet`/`remov`/`clean`/`purge`/`gc_` in the event name.
7. **Shell history inconclusive, not exculpatory.** No interactive SSH login session today near the relevant window
   (`last -F` shows the most recent at Jul 24 08:46–09:05). `.bash_history` has zero `sqlite3`/`DELETE FROM` hits — but
   SSM `send-command` and tmux-driven sessions (the way any agent, including the one investigating this, would actually
   run something) do not reliably populate `.bash_history`, so this does not rule out an out-of-band manual operation.
8. **The system's own documented design contradicts the observation.** `dashboard/src/App.tsx:2244`'s tooltip: _"Queued
   orphans clear on the next regen prune; done orphans are audit history."_ This is the intended guarantee — done rows
   are meant to be permanent. The pattern also rules out "the whole plan got archived so its rows got wiped" as a clean
   explanation: within the identical plan, some task_ids survived while immediate numeric siblings vanished (see
   point 3) — a plan-level wipe would be uniform, not selective.
9. **A second, related pattern was live-caught the same evening — status REGRESSION, not full vanish.** The watch (v1)
   showed `done` drop 24→21 between two 60s polls (2026-07-25T22:10:24Z → 22:11:23Z) with zero full-vanish alert (the 3
   task_ids were still present, just no longer `status='done'`). Investigated the responsible window directly:
   `PlanRegenLoop tick complete` fired at 22:01:36Z and 22:06:38Z (both `pruned_db=0`) and not again until 22:11:41Z —
   **18 seconds AFTER** the regression was already visible — so no regen tick caused it. Zero `reopen`-type activity
   events anywhere in the log either. **Root cause for this specific instance NOT found** — v1 only tracked aggregate
   counts, not the specific task_ids or their content, so there is nothing left to inspect after the fact. This gap is
   fixed in v2 (see below). Do not assume this is definitely the same mechanism as points 1-8 (full vanish) — flag as a
   related-but-distinct pattern until a v2 catch proves or disproves the connection.

## Process nuance found during this investigation — NOT the anomaly, but worth flagging to avoid a false-positive read of the watch log

Confirmed separately (unrelated to points 1-9): manually flipping a plan-file checkbox to `[x]` (marking a todo done in
the source `.md` only, e.g. via a direct `Edit`) does **NOT** itself update the corresponding `TaskRow.status` to
`'done'` in `state.db` — there is no code path that syncs a checkbox edit into a DB status change; only an actual worker
completion (or an explicit "mark done" action) does that. If the task's DB row was `blocked`/`queued` (dispatched_to IS
NULL) at the time, the next regen tick correctly treats it as an orphan (its brief no longer matches any open todo) and
the confirmed, sanctioned `_prune_stale` GC removes it — same as any other blocked/queued zombie. **The task_id then
disappears from `/api/backlog` entirely, but this is expected, not a recurrence of the anomaly** — it never became a
`done` orphan because it was never marked `'done'` in the DB, only in the plan file's prose. Confirmed live 2026-07-25:
`sports_satellite_ao_dispatch_batch2-014` (flipped via plan-file edit only, `unified-trading-pm@17acbca53`) is now fully
absent from `/api/backlog`, distinguishable from points 1-9 by being explainable (it was never `done` in the DB) rather
than unexplained. **Lesson for future checkbox-only completions**: if DB-level `done` audit history matters for a given
task, also call whatever "mark done" mechanism exists for it (e.g. the parked-task `mark-done` endpoint for
`[OPERATOR]`-tagged tasks), not just the plan-file edit.

## What is NOT yet known

- The actual code path or process responsible for removing `done` rows. Every known application-level DELETE site has
  been read (locally and on the deployed VM) and none fits.
- Whether this is a single past incident or an ongoing, recurring condition.
- Whether any OTHER shared session/slot on this same VM ran a direct, out-of-band SQL operation against `state.db`
  (plausible given this is a heavily multi-agent-shared host, but unproven either way).

## Live watch armed (in progress as of this doc)

A detached background process is running on the orchestrator VM (`i-0c9b283b31d6b5ca7`, launched via `setsid nohup`,
survives independent of any one SSM session), currently on **v2** (`agent-orchestrator@a90d3fc`), polling `/api/backlog`
every **60s** (tightened from an initial 180s ahead of a large incoming task batch). v2 tracks the FULL task record per
poll (not just id→status) and immediately logs full before/after JSON for either of two patterns, each triggering
capture of the last 10 minutes of the `orchestrator` systemd journal + a full process list into the same log:

1. **Full vanish** — a `done` task_id disappears from the response entirely (the original pattern, points 1-8 above).
2. **Regression** — a `done` task_id is still present but its status is no longer `'done'` (point 9 above; v1 could not
   capture the specific task_id or content for this pattern, only the aggregate count change).

- Script: `agent-orchestrator/scripts/done_row_disappearance_watch.py` (this issue's investigation tool).
- Live log: `/home/ubuntu/done_row_disappearance_watch.log` on the orchestrator VM.
- State file: `/home/ubuntu/done_row_disappearance_watch_state.json` (v2 format: full per-task-id records, not just id
  lists — v2 auto-detects and discards a stale v1-format state file rather than crashing on it).
- Confirmed running: v2 baseline poll logged at 2026-07-25T22:36:25Z after cleanly migrating past the v1 state file.

## Todos

- [ ] [OPERATOR] P1. **Check the watch log periodically** (`ssh`/SSM into the VM,
      `cat /home/ubuntu/done_row_disappearance_watch.log`) for an `!!! ANOMALY` line. If one fires, the captured
      journalctl + process-list block immediately following it is the best chance at identifying the actual cause — read
      it before the trail goes cold (the journal itself eventually rotates).
- [ ] [BACKEND] P2. Once (if) a recurrence is caught: root-cause the actual code path or process and fix it. Until then,
      do not guess at a fix for an unconfirmed mechanism.
- [ ] [BACKEND] P3. Consider adding a lightweight SQLite trigger
      (`CREATE TRIGGER ... BEFORE DELETE ON tasks WHEN     OLD.status='done' ...`) that raises/logs loudly on any
      attempt to delete a done row, regardless of call site — defense in depth so this class of event is caught
      immediately in the future rather than requiring a post-hoc forensic investigation like this one.
- [ ] [BACKEND] P3. Audit whether the DR-backup/snapshot cadence (currently ~15-30min, per
      `snapshots/planning/2026-07-25/`) is frequent enough to reliably bracket a future occurrence to a narrow enough
      window — if not, consider tightening it specifically while this issue is open.

## Codex SSOTs

- None directly own this (it's a gap in the orchestrator's own operational data integrity, not a documented pipeline
  correctness domain) — if a root cause is found, the fix should get a proper SSOT reference added here.
