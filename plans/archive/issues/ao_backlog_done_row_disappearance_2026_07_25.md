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
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, data-integrity, state-db, backlog, sqlite, audit-history, resolved]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: 2026-07-25
last_updated: 2026-07-28
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
resolved_by: agent-orchestrator@b926a9262c4ef592f1bfe644b0c0e03cac3335ef
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

## Root cause CONFIRMED + FIXED (2026-07-28)

Two independent methods converged on the same mechanism:

1. **Forensic re-run of this doc's own method, widened to 2026-07-25 → 2026-07-28** (the live-watch process described
   below had silently died — see "Live watch — retired" — so this was done by pulling every `snapshots/planning/*.json`
   state export from S3 for the whole window and diffing every consecutive pair, exactly as points 1-9 above did for a
   single evening). Found **706 anomalies across the 4 days — 599 full-vanish, 107 regression — covering 686 distinct
   task_ids**, i.e. this was a continuously recurring condition, not a one-off, and far larger in scope than first
   noticed. 90% of the regressions **preserved `done_sha`/`done_at`** after the status flip — a field-signature that
   rules out the one known reset path (which clears those fields) and instead matches
   `server/state_store/tasks.py::release_task_to_queue()`, which touches only `status`/`dispatched_to`/`queued_at` and
   never `done_sha`/`done_at`.
2. **A fresh code audit of every caller of `release_task_to_queue`** (not just the previously-cleared
   `regen_backlog_from_plan.py::_prune_stale`) found it had **no guard against being called on an already-terminal
   task**. Several callers derive the `task_id` from a SLOT's `current_task`/`dispatched_to` pointer rather than
   re-checking the task's own current status: `server.py::_recover_slot_after_failed_rotation` (only checks
   `slot.status != "paused"`), `worker_liveness_watchdog.py`'s prereq-blocked release (only checks
   `held_task is not None`), `state_store/slots.py::claim_slot_for_typed_agent`'s teardown loop (queries
   `TaskRow.dispatched_to == slot_id` with **no status filter at all**), and the `/reassign` + `/skip-current-task`
   endpoints (both use `slot.current_task` directly). If any of these pointers is stale — e.g. a worker's own `/done`
   call already completed the task, but a concurrent slot-teardown/watchdog/reassign path still holds the old
   `current_task` reference — calling `release_task_to_queue` unconditionally flips the genuinely-done task back to
   `queued` (the **regression**, `done_sha`/`done_at` untouched, exactly matching finding 1). Once `queued` with
   `dispatched_to=NULL`, the row now satisfies `_prune_stale`'s own correctly-scoped DELETE filter on the very next
   regen tick (**the vanish** — a legitimate-looking two-step "reset-then-prune" that never touches the one known
   DELETE's own guard, which is why the original investigation's DELETE-site audit correctly cleared it and still missed
   the real mechanism).

**The fix**: a guard added directly inside `release_task_to_queue()` (not just the individual call sites, so every
current AND future caller is covered) refuses — logs a warning, makes no change, returns `None` — when the row is
already `done`/`cancelled`. The one legitimate caller that means to undo a terminal status on purpose
(`/api/backlog/{id}/reopen`) opts in explicitly via a new `allow_terminal=True` kwarg. `/reassign` and
`/skip-current-task` now surface a `409` instead of silently proceeding as if a live task had been reassigned/skipped.
Shipped: `agent-orchestrator@b926a9262c4ef592f1bfe644b0c0e03cac3335ef` (`server/state_store/tasks.py`,
`server/routes/slots_ops.py`, `server/routes/backlog.py`, `server/server.py`, `server/worker_liveness_watchdog.py`) + 17
new/covering tests (`tests/test_release_task_to_queue_guard.py`) — full local suite green (1902 passed), full
`quality-gates.sh` green, landed on `live-defi-rollout` via quickmerge. **Confirmed live in production**: the
orchestrator VM (`i-0c9b283b31d6b5ca7`) tracks `live-defi-rollout` directly, pulled + `--reload`-restarted onto this
exact commit within ~2 minutes of the push (journal: reload fired 18:46:05Z picking up
`slots_ops.py`/`backlog.py`/`worker_liveness_watchdog.py`/`state_store`/etc.; service confirmed `active` and serving
traffic normally afterward).

**A secondary, minority candidate was checked and ruled out, not just assumed clear**: `server/bootstrap.py`'s
sibling-id-reuse reset (`sync_backlog_to_db`, guarded at line ~431 by `status=='done' and done_sha is not None`) could
theoretically produce the ~10% of regressions where `done_sha` WAS cleared, if its guard were ever bypassed (e.g. a
`done` row somehow lacking `done_sha`). Traced `mark_done()` back to the very first commit — it has always set
`done_sha` unconditionally alongside `status='done'`, so this path is structurally closed in current code; deploy parity
was spot-checked directly on the live VM (`grep` confirms the exact guard line present at the same line number in the
deployed checkout, which is running this session's own HEAD). Not the dominant mechanism, and not currently exploitable
— noted here rather than silently dropped.

**A related, independently-confirmed bug was found and fixed in the same pass**: the SQLite DR backup (the actual
restorable artifact, distinct from the lighter `state.json` snapshot) had not landed in **4+ days** in prod
(`SnapshotRecencyCanary` correctly detected + paged this — its breach sentinel was `true` — but nothing had yet
explained _why_ the backup itself had stopped). Root cause: `gcs_sync.SnapshotLoop`'s 6h cadence was tracked by a plain
in-process `tick` int, reset to 0 on every process restart — and this service restarts on every `--reload` code-change
pickup, observed in prod restarting every **15-70 minutes**, far short of accumulating the 12 ticks (6h) needed before
resetting again. The backup could structurally never fire under that restart cadence. Fixed by tracking elapsed
wall-clock time since the last successful backup instead, persisted to a sentinel file under `data/state/` (survives
restarts the same way `state.db` itself does) — shipped in the same commit, covered by
`tests/test_sqlite_backup_wallclock_cadence.py`.

## Live watch — retired (2026-07-28)

The v2 watch process described below was found **dead** at the start of this session (`pgrep` found nothing, its log
file was 0 bytes) — it was launched via a bare `setsid nohup` with no systemd unit, and silently died (most likely a
VM/service restart) without ever catching a recurrence. Its intended purpose — catch a live recurrence to identify the
cause — is superseded: the cause is now identified and fixed at the source (above), and the forensic **snapshot-diff
method is strictly more powerful anyway** (it needs no continuously-running process at all; the `state.json` trail
already lands independently every ~30min regardless, and can be diffed retroactively on demand whenever a concern arises
— which is exactly how the 2026-07-28 root-cause finding above was actually produced). Keeping a bare unmanaged
background process as the primary mitigation was itself an instance of the same restart-fragility class this whole
investigation was about. **`scripts/done_row_disappearance_watch.py` has been deleted** per its own `Delete-when` marker
(issue resolved) — `git log -- scripts/done_row_disappearance_watch.py` in `agent-orchestrator` has its full history if
anyone wants the code again.

## Todos

- [x] [SCRIPT] P1. Check the watch log for an `!!! ANOMALY` line. — Found the process dead (not running) rather than
      catching a live anomaly; superseded by re-running the forensic snapshot-diff method directly against the existing
      S3 `state.json` trail instead, which is what actually produced the root-cause finding above. Evidence: SSM check
      on 2026-07-28, `pgrep -af done_row_disappearance_watch` empty, log file 0 bytes.
- [x] [BACKEND] P2. Root-cause the actual code path/process and fix it. — Done, see "Root cause CONFIRMED + FIXED"
      above. Evidence: `agent-orchestrator@b926a9262c4ef592f1bfe644b0c0e03cac3335ef`, confirmed live on the deployed VM.
- [x] [BACKEND] P3. Defense-in-depth guard against illegal done-row mutation. — Implemented as an application-level
      guard inside `release_task_to_queue()` (refuses + logs, returns `None`) rather than a raw SQLite `BEFORE DELETE`
      trigger — this covers BOTH the vanish (via the reset-then-prune two-step) and the regression (the direct status
      flip) in one place, at the exact point the illegal transition would occur, with full context in the log line
      (task_id + refused status), which a bare SQL trigger error could not provide as usefully. Evidence: same commit;
      `tests/test_release_task_to_queue_guard.py` (7 tests) prove the guard fires for `done`/`cancelled`, does not break
      the legitimate `dispatched`→`queued` case, and that `/reassign`+`/skip-current-task` 409 honestly instead of
      silently succeeding.
- [x] [BACKEND] P3. Audit the DR-backup/snapshot cadence. — Audited and found genuinely broken (4+ day gap, root-caused
      above as the tick-counter/restart interaction) rather than merely "not frequent enough" — fixed via a wall-clock
      persisted sentinel in the same commit. Evidence: `tests/test_sqlite_backup_wallclock_cadence.py` (9 tests);
      confirmed via S3 listing that the last SQLite backup pre-fix was `2026-07-24T19:30:45Z`.

## Codex SSOTs

- None required an update — this is a bugfix in existing application code (an unguarded state-transition function), not
  a new architectural pattern or contract. `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` and
  `/codex/04-architecture/agent-orchestrator-alerting.md` (cited above) already correctly describe the
  regen/prune/alerting architecture this fix operates within; nothing about that architecture changed.

## Progress Log

- **2026-08-01** (`ao_satellite_ao_dispatch_batch1_2026_07_26.md` residual todo): shipped the narrower raw-SQL-delete
  backstop this doc's `[BACKEND] P3` explicitly scoped OUT ("rather than a raw SQLite `BEFORE DELETE` trigger"). Added
  `agent-orchestrator/server/bootstrap.py::_migrate_done_task_delete_trace()` — an idempotent migration creating
  `deleted_done_tasks_trace` + an `AFTER DELETE ON tasks WHEN OLD.status = 'done'` trigger that records `task_id` /
  `plan_ref` / `done_sha` / `done_at` / `deleted_at` for ANY delete of a done row, including a bare out-of-band SQL
  delete the application-level guard in `release_task_to_queue()` cannot see (that guard only catches an illegal
  status-transition through the ORM, not a raw `DELETE`). The trigger only INSERTs, never raises — confirmed the
  sanctioned `DELETE /api/backlog/{task_id}` path still succeeds unconditionally and is traced, not blocked. 4 new tests
  in `tests/test_done_task_delete_trace.py` (raw-SQL delete traced, sanctioned operator delete traced + still succeeds,
  non-done delete leaves no trace, migration idempotent across repeated `create_all_tables()` calls). This is pure
  defense-in-depth on top of the already-complete application-level fix above — no behavior change for any existing
  caller.
