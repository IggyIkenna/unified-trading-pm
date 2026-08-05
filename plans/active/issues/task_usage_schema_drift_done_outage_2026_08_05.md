---
doc_type: issue
title:
  "task_usage table missing `backfilled` column broke /done fleet-wide for ~2h (create_all_tables() never ALTERs an
  existing table)"
summary: >-
  `TaskUsageRow.backfilled` was added to the ORM model mid-session (agent-orchestrator@b310c68), but the `task_usage`
  table on the live orchestrator VM had already been created by an earlier deploy of the same class, before that field
  existed. `create_all_tables()` (`Base.metadata.create_all`) only creates MISSING tables — it never alters an
  already-existing table's columns — so every subsequent `INSERT ... backfilled` on the real VM has been throwing
  `sqlite3.OperationalError: table task_usage has no column named backfilled` since 2026-08-05T11:02:03Z. Because
  `_record_done_task_usage()` runs unguarded inside the SAME `session_scope()` transaction as `mark_done`/
  `record_slot_history`/`clear_slot_assignment` in `POST /api/slots/{id}/done`, the exception rolled back the ENTIRE
  `/done` submission — not just the usage row — so every real worker's task completion failed with a 500 for ~2 hours
  (11:02:03-12:59:55 UTC), 52 distinct failures across at least 8 slots (2/3/4/5/7/11/13/15). Separately, the new `GET
  /api/backlog/usage/windows` dashboard endpoint (same missing column, SELECT side) also 500'd for the same window.
  Fixed live via a direct `ALTER TABLE task_usage ADD COLUMN backfilled BOOLEAN NOT NULL DEFAULT 0` (safe, additive,
  zero data loss) — verified via 2 real `/done` 200 OKs immediately after. Workers retry `/done` on failure (confirmed
  in the logs — the same slot re-attempts repeatedly), so no task appears to have been permanently lost, but real
  completion throughput was degraded fleet-wide for the full window.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [admin, engineer]
tags: [agent-orchestrator, production-incident, schema-drift, sqlite, done-endpoint, big-finding]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-08-05
author: ikennaigboaka [interactive session]
parent_epic: orchestrator_master
priority: P0
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
source: ["interactive session, found while running backfill_task_usage.py --apply against real production data"]
drift_direction: advance-process
estimate_class: infra
depends_on: []
---

# task_usage schema drift broke /done fleet-wide for ~2h

> **🔴 Live production incident, root-caused and fixed same-session.** `/done` failed for every worker fleet-wide from
> 2026-08-05T11:02:03Z to 12:59:55Z (~2h). Fixed live; verified recovered. The immediate incident is CLOSED — what
> remains open is the systemic gap that let it happen (no schema-migration mechanism), tracked as the P2 todo below.

## What happened

1. `TaskUsageRow` (the per-task token-usage table) was added to `server/orm.py` this session. The
   `backfilled: Mapped[bool]` field was added to that same class — but the exact sequence of deploys to the real
   orchestrator VM meant `task_usage` was first CREATED by an earlier version of the class (via `bootstrap.initialise()`
   → `create_all_tables()` on a service restart), before `backfilled` existed on the model. 11 rows landed successfully
   under that older schema (`completed_at` 10:31:00-10:58:37Z).
2. `agent-orchestrator@b310c68` (adds `backfilled` to the model + every write path) later auto-deployed via
   `ao-self-pull.sh` and restarted the service. `create_all_tables()` is `Base.metadata.create_all(engine)` — idempotent
   per-table by NAME, not per-column: since `task_usage` already existed, SQLAlchemy silently skipped it. The live
   schema stayed frozen on the pre-`backfilled` shape while the running code now unconditionally included `backfilled`
   in every `INSERT`.
3. Every subsequent write failed: `sqlite3.OperationalError: table task_usage has no column named backfilled`. First
   occurrence confirmed via `journalctl -u orchestrator`: **2026-08-05T11:02:03Z**.
4. **Root cause of the FLEET-WIDE (not just usage-tracking) impact**: `_record_done_task_usage()`
   (`server/routes/slots_worker.py:1343`) has no `try`/`except` and runs inside the exact same
   `with session_scope() as session:` block as `ss.mark_done(...)`, `ss.record_slot_history(...)`,
   `ss.clear_slot_assignment(...)`, `ss.update_slot_ping(...)` in `done_slot()`. The uncaught `OperationalError` rolled
   back the WHOLE transaction and propagated to a 500 response — so a real worker's `/done` submission was rejected in
   full, not just its usage telemetry. Confirmed via `journalctl`: 52 distinct `POST /api/slots/{id}/done` 500s across
   slots 2/3/4/5/7/11/13/15 between 11:02:03Z and 12:59:55Z (some slots retried multiple times — 13 at least twice, 3 at
   least three times).
5. Separately, `GET /api/backlog/usage/windows` (the SELECT side, backing the dashboard's new Task Usage Windows panel)
   also 500'd for the same window with `sqlite3.OperationalError: no such column: task_usage.backfilled`.
6. **Fixed live, 2026-08-05T12:59:55Z**: `ALTER TABLE task_usage ADD COLUMN backfilled BOOLEAN NOT NULL DEFAULT 0` via
   AWS SSM against `data/state/state.db` — safe (additive, SQLite-native, zero data loss; all 11 existing rows default
   to `backfilled=0`, correct since they were genuinely live-captured, not backfilled). **Verified recovered**: the next
   two `/done` calls (slot 2 at 13:00:20Z, slot 5 at 13:00:33Z) both returned `200 OK`.

## Blast radius — what was and wasn't lost

- **No evidence of permanently lost work.** Workers retry `/done` on failure (visible in the logs — the same slot
  resubmits repeatedly rather than giving up), and the fleet state immediately after the fix showed no slot stuck in an
  anomalous limbo (mix of idle/working/blocked, nothing orphaned). This reads as degraded throughput (workers stuck
  retrying instead of picking up new work), not data loss.
- **Real cost**: ~2 hours of fleet-wide `/done` failures — an unknown but real amount of delayed task completion across
  at least 8 slots. Not independently confirmed whether any worker gave up retrying and is still stuck as of this
  writing — see todo below.
- **The per-task usage telemetry itself** (the actual feature this session was building) has a real, bounded gap:
  whatever real tasks completed between 11:02:03Z and 12:59:55Z either failed to record usage (if `/done` also failed)
  or — for the very few that might have raced past — inconsistently. The `backfill_task_usage.py` script (itself fixed
  for a separate performance bug this same session, see the DeepSeek routing plan's Progress Log) will recover this
  retroactively from transcripts once run again with `--apply`.

## Todos

- [x] ✅ [INFRA] P0. **RESOLVED same-session.** Apply
      `ALTER TABLE task_usage ADD COLUMN backfilled BOOLEAN NOT NULL     DEFAULT 0` on the live orchestrator VM's
      `data/state/state.db`. Done when: schema confirmed via `.schema     task_usage`, and a real `/done` call succeeds.
      — Both confirmed: schema shows the new column; `/done` 200 OK for slots 2 and 5 immediately after (13:00:20Z,
      13:00:33Z).
- [x] ✅ [INFRA] P1. Confirm no slot is CURRENTLY stuck unable to complete. — Spot-checked `GET /api/state` post-fix:
      slots 3/4 actively `working` with fresh `last_ping` timestamps (13:02:04Z, well after the 12:59:55Z fix), slot 2
      `killed` (a normal post-completion state, `worker_alive=true`/`tmux_alive=false`, not evidence of being stuck). No
      slot showed an anomalous limbo. Not an exhaustive per-slot audit of all 52 individual incident- window failures —
      a proportionate check given every retried `/done` call observed post-fix succeeded.
- [x] ✅ [INFRA] P1. **Guard `_record_done_task_usage()` so a usage-write failure can never roll back the rest of
      `/done` again** (`server/routes/slots_worker.py`, called from `done_slot()`). Moved to its OWN independent
      `session_scope()`, called BEFORE the main completion transaction starts (not nested inside it — SQLite only
      supports one writer at a time, so nesting risked lock contention/deadlock, not just a rolled-back commit), wrapped
      in `try/except SQLAlchemyError` (logged, not raised). Proven via a new
      `tests/test_record_done_task_usage_isolation.py` (3 tests: a simulated `record_task_usage` failure doesn't raise,
      a real write still persists correctly, `task_usage=None` is a clean no-op) plus the full existing suite (2403
      passed) and all 129 `/done`-tagged tests green. — `agent-orchestrator@7a7dd8d`, deployed live via an operator-safe
      `systemctl restart orchestrator` (verified: `KillMode=process`, all worker tmux sessions survived, `/api/mode` 200
      within 8s).
- [ ] [INFRA] P2. **Systemic gap, not just this one field**: this codebase has no schema-migration mechanism beyond
      `create_all_tables()`/`Base.metadata.create_all()`, which only creates missing TABLES, never alters existing ones.
      ANY future additive `Mapped[...]` field on an existing ORM class risks this exact failure mode on any environment
      where the table already exists (which is every long-lived deployed VM, by definition). Options worth evaluating:
      (a) a lightweight startup migration step that diffs `PRAGMA table_info` against the ORM model and
      `ALTER TABLE ADD COLUMN`s anything missing (safe for pure-additive changes, which is the common case here), (b) a
      real migration tool (Alembic) if schema changes become frequent enough to justify the overhead, (c) at minimum, a
      documented codex runbook: "adding a column to an EXISTING table needs a manual `ALTER TABLE` on every
      already-deployed DB, `create_all_tables()` will NOT do it for you." Done when: either (a)/(b) ships, or (c) is
      documented and cross-referenced from wherever ORM changes are made.

## Progress Log

- **2026-08-05 — found, root-caused, and fixed live in the same interactive session** while running
  `backfill_task_usage.py --apply` against real production data (see
  `/plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md`'s `[OPERATOR] P2` todo). The `--apply` run's
  own `OperationalError` was the first signal; grepping `journalctl -u orchestrator` for the same error surfaced the
  much larger fleet-wide `/done` impact, not just a backfill-script problem. Fixed via a direct, safe `ALTER TABLE` (no
  code deploy needed — this is a live-data schema fix, not a code change). Verified recovered via real `/done` 200s
  immediately after. Full timeline, root cause, and blast-radius assessment written up above rather than left as a chat
  note, per this workspace's "big finding → notify operator + issue doc" rule.
- **2026-08-05 (later, same session) — deeper isolation fix shipped + deployed live; backfill re-run to completion.**
  Shipped `agent-orchestrator@7a7dd8d` (see the P1 todo above for detail), pulled onto the VM, and deployed via a
  verified-safe `systemctl restart orchestrator` (all worker tmux sessions survived). Re-ran
  `backfill_task_usage.py --since 2026-07-29 --apply`: `matched=1236 unmatched=0`, completed in 42s (the performance fix
  from earlier the same session — see the DeepSeek routing plan — made this practical at all). Verified live via
  `GET /api/backlog/usage/windows`: real windowed data across 1h/5h/24h/7d/lifetime (1,252 lifetime tasks). Both this
  incident's immediate fix and its direct follow-on code hardening are now fully shipped and verified; only the broader
  systemic P2 (a real schema-migration mechanism) remains open.
