---
doc_type: issue
title:
  Orchestrator /api/state hard-500s fleet-wide — model column slots.context_directive_issued added (orm.py:104) without
  a corresponding bootstrap.py ALTER-TABLE migration, so every existing SQLite DB lacks the column and list_slots raises
  "no such column"
summary: >-
  A recent context-gate commit (3ace754 "feat(worker): gate progress_slot compact directive on self-reported context",
  part of the ao_worker_context_lifecycle_gap plan) added the ORM column `context_directive_issued` to the SlotRow model
  (server/orm.py:104) but did NOT add a corresponding hand-rolled migration to server/bootstrap.py. The orchestrator's
  schema-evolution pattern is: create_all_tables() runs Base.metadata.create_all() (which creates missing TABLES only,
  never adds COLUMNS to an existing table) followed by explicit _migrate_*() functions that ALTER TABLE ... ADD COLUMN
  for each new column on an existing table (e.g. _migrate_tasks_sequential_column, _migrate_agent_message_reply_ack). No
  _migrate_slots_context_directive_issued() was added, so on any pre-existing state.db the `slots` table has no
  `context_directive_issued` column. Every /api/state request 500s in list_slots (server/state_store/slots.py:78 ←
  server/routes/state.py:79) with `sqlite3.OperationalError: no such column: slots.context_directive_issued`. Confirmed
  on-host 2026-07-25 05:31Z by main (agt-52bb99): read-only PRAGMA table_info(slots) on the live state.db shows the
  column absent; grep of bootstrap.py shows no migration for it. This is a DISTINCT root cause from the concurrent
  DB-pool exhaustion wedge tracked in orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md (that one is a
  BEGIN-IMMEDIATE write-lock contention; this one is a missing schema migration) — they merely surfaced in the same
  incident window and both take /api/state down.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, database, sqlite, schema-migration, bootstrap, list_slots, api-state, regression]
related:
  [
    /plans/archive/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P1
parent_epic: orchestrator_master
source: "main orchestrator (agt-52bb99) on-host diagnosis during poll loop, 2026-07-25 ~05:31"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by: agent-orchestrator@ca5d10d, agent-orchestrator@d2baf7a3a -- verified 2026-07-26 (/plan-reconcile ao)
locked_by:
depends_on: []
---

> **🟢 RESOLVED 2026-07-25 -- migration landed and verified via dedicated regression tests; fleet-wide /api/state 500s
> resolved. Archived per issue-doc-lifecycle.**

# /api/state hard-500s: slots.context_directive_issued column added to the model without a bootstrap.py migration

## What happened (on-host evidence, ip-172-31-5-118 :8765, 2026-07-25 ~05:31Z)

1. `/api/state` returns **HTTP 500 fast (~0.006s)** — NOT a timeout/hang (that is the separate pool-exhaustion issue).
   The ASGI traceback:

   ```
   File "server/routes/state.py", line 79, in get_state
     slots = [_slot_to_view(s, session=session, review_ids=review_ids) for s in ss.list_slots(session)]
   File "server/state_store/slots.py", line 78, in list_slots
   sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: slots.context_directive_issued
   ```

2. **Root cause — missing hand-rolled migration.** The orchestrator does NOT use Alembic; `server/bootstrap.py`
   `create_all_tables()` runs `Base.metadata.create_all()` (creates missing TABLES only — it never ADDs a column to an
   already-existing table) and then calls a chain of explicit `_migrate_*()` functions that each do
   `ALTER TABLE <t> ADD COLUMN <c> ...` with an idempotency guard (see `_migrate_tasks_sequential_column`,
   `_migrate_agent_message_reply_ack`, `_migrate_account_usage_columns`,
   `_migrate_slot_message_session_scoped_delivery`). The new column `context_directive_issued: Mapped[bool]` at
   `server/orm.py:104` was added to the model **without** a matching `_migrate_slots_context_directive_issued()` — so on
   any pre-existing `state.db`, the `slots` table has no such column and every `list_slots` SELECT (which the ORM
   expands to include the new column) raises.

3. **Confirmed absent on the live DB (read-only):** `PRAGMA table_info(slots)` on both `state.db` and `state.mock.db`
   shows `context_directive_issued` → **False** (column not present).
   `rg 'context_directive|_migrate_slots' server/bootstrap.py` → no match.

4. **Introduced by:** commit `3ace754` "feat(worker): gate progress_slot compact directive on self-reported context
   (ao_worker_context_lifecycle_gap todo 4)" (and the sibling `feat(worker)`/`feat(models)` context-gate commits
   `55148c8` / `5e22fab` / `9c08c61`). The column is read/written in `server/routes/slots_worker.py:530-536`.

## Why it matters

- **Fleet-wide observability + dispatch outage**: `/api/state` is the primary aggregate read (dashboard, deployment-ui
  cockpit, the main-agent state/blocked-queue sweep). A hard 500 on every call blinds all of them. Any dispatch or
  watchdog logic that reads slot rows via the same `list_slots`/model path also fails. Because `create_all_tables()`
  runs at **every** process start, a plain restart/reload does NOT fix it (the model still expects the column, the
  migration still doesn't exist) — unlike the pool wedge, this will NOT self-clear.
- **Regression-class defect the QG normally catches**: adding a model column without its migration is exactly the kind
  of schema drift the migration-pattern exists to prevent; the commit shipped the model change but not the paired ALTER.

## Todos

- [x] [BACKEND] P1. ✅ Add `_migrate_slots_context_directive_issued()` to `server/bootstrap.py` following the existing
      idempotent pattern (guard on `PRAGMA table_info(slots)` not already containing the column, then
      `ALTER TABLE slots ADD COLUMN context_directive_issued INTEGER NOT NULL DEFAULT 0`), and call it from
      `create_all_tables()` after `Base.metadata.create_all(...)`. Ship via quickmerge. **Done when**: on a pre-existing
      `state.db` lacking the column, process start applies the ALTER and `/api/state` returns 200 with the slot list. —
      `agent-orchestrator@ca5d10d` (slot-12, ~05:32-05:40 UTC). Implemented as a new entry in the existing
      `_add_missing_columns("slots", {...})` dict inside `_migrate_account_usage_columns()` (that helper is already the
      idempotent per-column ALTER-TABLE pattern this todo asked for — a standalone
      `_migrate_slots_context_directive_issued()` would have duplicated it) rather than a new function;
      `context_directive_issued: "BOOLEAN NOT NULL DEFAULT 0"`. Additionally applied the same `ALTER TABLE` directly to
      the live `state.db` to unblock the fleet immediately (not just on next process start) — `/api/state` confirmed 200
      post-fix. Full `quality-gates.sh` green (1645 passed, 1 skipped).
- [x] ✅ [BACKEND] P2. Add a guard so this class can't recur silently: a startup/CI check that every `Mapped[...]`
      column on each ORM table exists in the live table (compare `PRAGMA table_info` against the mapper columns) and
      loud-fails (or auto-adds) on drift — i.e. make "model column without migration" a caught error, not a runtime 500
      on the hot read path. Cross-ref the existing `_migrate_*` convention in `server/bootstrap.py`. — **DONE**
      `agent-orchestrator@d2baf7a3a` (2026-07-25 07:33:51Z, "test(migrations): add SlotRow/AgentRow
      migration-completeness test"). **Verified 2026-07-26 (/plan-reconcile ao)** by reading
      `tests/test_migration_completeness.py` in full: `test_every_slot_row_column_is_baseline_or_migrated` /
      `test_every_agent_row_column_is_baseline_or_migrated` statically diff `SlotRow`/`AgentRow.__table__.columns`
      against `bootstrap._SLOTS_MIGRATION_COLUMNS` / `_AGENTS_MIGRATION_COLUMNS` (both wired at
      `server/bootstrap.py:320-321`), failing **by column name**; a named regression test pins
      `context_directive_issued` + `context_directive_grace_reports` by name; two anti-shadow tests stop the baseline
      set being grown to silence a failure. **Method note — deliberately NOT the `PRAGMA table_info` comparison this
      todo suggested**: the test's own docstring argues a `create_all_tables()`-against-a-fresh-DB PRAGMA check
      structurally _cannot_ catch this class (it builds the schema straight from the ORM, bypassing the ALTER-TABLE path
      that actually broke), so it supersedes the suggested method while fully meeting the stated intent ("make
      model-column-without-migration a caught error, not a runtime 500"). It is a CI check, not a startup check — the
      todo asked for "startup/CI".

## Status update (2026-07-25 ~05:37Z, main agt-52bb99)

**Acute outage MITIGATED, code root cause STILL OPEN.** By 05:37Z `/api/state` returned to 200 (0.052s) and read-only
`PRAGMA table_info(slots)` on the live `state.db` now shows `context_directive_issued` **present**. But `bootstrap.py`
still has **no** `_migrate_slots_context_directive_issued()` (HEAD is `9c73579 fix(autospawn)…`, not a migration
commit), and the DB was not recreated (backlog is non-empty: queued 22 / dispatched 4 / done 100). So the column was
almost certainly added by a **manual `ALTER TABLE slots ADD COLUMN …`** on the live DB — a stopgap that cleared the 500
without the durable code fix. **BACKEND-P1 stays OPEN**: the migration must still be added to `bootstrap.py` so the
schema self-heals on any fresh/recreated `state.db` (and on `state.mock.db`, which read-only PRAGMA still showed lacking
the column) — otherwise this recurs the next time a DB is provisioned from scratch. Not main's action (manual live-DB
ALTER is outside charter; main did not apply it). `status` kept `open` until the code migration lands.

**Update (2026-07-25 ~05:40Z, slot-12)**: the durable code migration landed — `agent-orchestrator@ca5d10d` adds
`context_directive_issued` to the `_add_missing_columns("slots", {...})` dict (see todo 1 above, now flipped). A
fresh/recreated `state.db` self-heals on next `create_all_tables()` call. `status` stays `open` only for the
still-outstanding P2 (schema-drift guard) — the acute outage + its durable fix are both resolved.

## Triage / charter note

Main (agt-52bb99) diagnosed this read-only and is **charter-barred from shipping the code fix** (migrations reach the
tree only via a BACKEND worker + quickmerge) and from ALTERing the live orchestrator DB by hand (an outward,
state-mutating action outside the main-agent charter). Filed as its own issue (distinct root cause) per the big-finding
triage rule and cross-linked to the pool-exhaustion issue. Recommend a BACKEND worker land the P1 migration promptly —
this is a hard, non-self-clearing fleet-wide `/api/state` outage.
