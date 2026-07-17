---
doc_type: issue
title:
  The regen prune GC'd a 4 KB empty file instead of the live state.db for 7 days — 190 orphan task rows accumulated and
  made the Backlog KPI ("145 in queue") contradict the detail modal ("17")
summary: |
  The operator opened the Backlog tab's Details modal and saw 17 queued while the header KPI read 145. The modal was
  RIGHT and the KPI was the lie: 128 of those 145 queued rows were undispatchable orphans. Root cause is an SSOT
  contradiction — TWO env vars name one concept, set in TWO different files, and they drifted:
  `ORCHESTRATOR_DB_PATH=/var/lib/orchestrator/state.db` (systemd unit, the real DB) vs
  `ORCHESTRATOR_REGEN_DB_PATH=<repo>/data/state/state.db` (.env.local, a 4 KB file with no `tasks` table).
  WHY the second var existed at all: `PlanRegenLoop.__init__` left `self._db_path = None` when the override was unset —
  i.e. "prune zombies by default" silently resolved to a YAML-ONLY prune that GC'd nothing — so bootstrap F12
  (2026-06-07) baked a literal copy of the DB path to compensate. The DB later moved to /var/lib/orchestrator via the
  systemd unit; the baked copy was left pointing into the repo checkout. Every 5 min the loop then pruned the yaml,
  failed the DB GC with `no such table: tasks`, SWALLOWED it as a WARNING, and logged
  `RegenSummary(pruned_db=0)` as success — 393 times in 7 days, unread, while 190 orphans (128 queued / 62 done) piled
  up. `/api/backlog` walked backlog.yaml ONLY while `/api/state`'s KPI counted TaskRows, so one surface counted the
  orphans and the other could not see them, with nothing reconciling the two.
  NOT a UI bug: the 20 tasks in backlog.yaml were correct all along (the excluded plan todos are `BLOCKED-*` /
  stretch-optional, which `_parse_open_todos` deliberately skips as non-dispatchable).
  FIXED IN `acc112f`: (1) `resolve_prune_db_path()` is one resolver for loop + /regen endpoint + CLI, defaulting to the
  server's OWN db — an unset override can no longer mean "prune nothing"; (2) a GC target with no `tasks` table is now
  an ERROR naming BOTH paths, not a swallowed warning; (3) bootstrap RETIRES the F12 bake and actively REMOVES the
  stale override (leaving it set on an already-bootstrapped host silently re-breaks the GC); (4) `/api/backlog` serves
  backlog.yaml UNION TaskRows with `orphan=true` so the modal and the KPI count the same set — the prune alone could
  NOT fix this, since it never deletes `done` rows and `done` would read 64-vs-2 forever.
  VERIFIED LIVE 2026-07-17 06:00 UTC on the central VM: the new ERROR fired once at 05:57 and printed its own fix
  instructions; at 06:00:25 `prune_stale: removed ... 128 state.db rows` -> `pruned_db=128`; queued 145 -> 17; modal
  and KPI now agree on all four statuses (queued 17/17, dispatched 1/1, done 64/64, cancelled 0/0); 62 `done` orphans
  remain BY DESIGN and are now flagged rather than invisible; 0 GC errors since; no hand DB edit.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, backlog, plan-regen, prune, zombie-tasks, ssot-drift, silent-failure, dashboard, fleet-view]
related:
  [
    ../../codex/04-architecture/agent-orchestrator-overview.md,
    ../../codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    ../ao_dispatch_hardening_2026_07_16.md,
    ../../epics/orchestrator_master.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: orchestrator_master
priority: P1
assigned_vm: NA
execution_scope: local-only
resolved_by:
  - "agent-orchestrator@acc112f — resolve_prune_db_path() SSOT (loop/endpoint/CLI agree, defaults to the server's own
    db); wrong-DB GC target is ERROR not WARNING; bootstrap retires + removes the F12 bake; /api/backlog serves yaml
    UNION TaskRows with orphan=true; modal gains an orphan filter + Plan column; 5 regression tests, all bug-injection
    verified"
locked_by:
locked_since:
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
source:
  Operator report 2026-07-17 — "in the backlog tab at the top there is a details button ... right now there 145 in queue
  but it says only only 17 in queue slot"
---

# The regen prune GC'd the wrong database for 7 days

## What the operator saw

Backlog tab → **Details**: `17` queued. Backlog header KPI: `145` in queue. Same page, same moment.

## The two surfaces, two sources

| Surface                        | Source                             | Read  |
| ------------------------------ | ---------------------------------- | ----- |
| Header KPI (`/api/state`)      | `summarise_backlog` → **TaskRows** | `145` |
| Details modal (`/api/backlog`) | walked **backlog.yaml** only       | `17`  |

Nothing reconciled them. 190 rows existed in `state.db` with no `backlog.yaml` entry (128 queued, 62 done). The
dispatcher walks `backlog.tasks`, so those 128 queued rows were **undispatchable** — the modal was showing the truth.

## Root cause — one concept, two vars, two files

```
ORCHESTRATOR_DB_PATH       = /var/lib/orchestrator/state.db      <- systemd unit  (41 MB, the real DB)
ORCHESTRATOR_REGEN_DB_PATH = <repo>/data/state/state.db          <- .env.local    (4 KB, no `tasks` table)
```

The second var only existed to paper over a bad default: `PlanRegenLoop.__init__` left `self._db_path = None` when the
override was unset, so "prune zombies by default" resolved to a **yaml-only prune**. bootstrap F12 baked a literal copy
of the path to compensate — and a literal copy is exactly what drifts. The DB later moved to `/var/lib/orchestrator`;
the baked copy stayed behind.

The failure was **loud but unread**, which is the same thing as silent:

```
393x in 7 days:
  WARNING prune_stale: state.db GC failed (yaml pruned, db skipped): no such table: tasks
  INFO    PlanRegenLoop tick complete: RegenSummary(..., pruned_yaml=0, pruned_db=0)   <- reported as success
```

## What was NOT the bug

`backlog.yaml` holding only 20 tasks from 422 scanned plans is **correct**. The plans that contribute nothing (e.g.
`mtds_available_at_cross_asset_backfill_2026_07_13`, 9 open todos) carry only `BLOCKED-OPERATOR-DECISION` /
`_(stretch, optional)_` items, which `_parse_open_todos` deliberately excludes as non-dispatchable. Verified by running
the regen's own gate against the live LDR snapshot.

## The fix (`acc112f`)

1. **`resolve_prune_db_path()`** — one resolver for the loop, `/api/backlog/regen`, and the CLI, defaulting to
   `config.db_path()`. An unset override can no longer mean "prune nothing", so the workaround var is unnecessary.
2. **Wrong target is an ERROR**, naming both paths and the remedy. A missing `tasks` table is a permanent
   misconfiguration, not a transient sqlite error.
3. **bootstrap retires F12** and actively `_remove_env`s the stale override — leaving it set on an already-bootstrapped
   host silently re-breaks the GC.
4. **`/api/backlog` serves yaml UNION TaskRows** with `orphan=true`. Required independently of the prune: the prune
   never deletes `done` rows, so `done` would read 64-vs-2 forever. Modal gains an orphan filter, an orphan badge, and a
   **Plan** column.

A test asserted the bug — `assert loop2._db_path is None` — two lines under a comment reading _"the running server
prunes zombies by default"_. Rewritten; all 5 new tests bug-injection verified.

## Live evidence (central VM, 2026-07-17)

```
05:57:20 ERROR prune_stale: GC target .../data/state/state.db is not an orchestrator DB (no `tasks` table)
               ... The server's own DB is /var/lib/orchestrator/state.db. Unset ORCHESTRATOR_REGEN_DB_PATH.
               RegenSummary(..., pruned_db=0)
06:00:25 INFO  prune_stale: removed 0 orphan yaml entries, 128 state.db rows
               RegenSummary(..., pruned_db=128)

queued 145 -> 17     modal vs KPI: queued 17/17, dispatched 1/1, done 64/64, cancelled 0/0  = RECONCILED
62 `done` orphans remain by design, now flagged.   0 GC errors since.   DB backed up pre-GC.
```

## Follow-up (not fixed here)

`ORCHESTRATOR_DB_PATH` lives ONLY in the systemd unit, not `.env.local`. Any tooling run from the shell
(`python -m server.regen_backlog_from_plan --prune-stale`, ad-hoc probes) therefore resolves `config.db_path()` to the
empty in-repo `data/state/state.db` — the same family of footgun that caused this incident, and it bit twice while
diagnosing it. Consider having bootstrap write `ORCHESTRATOR_DB_PATH` into `.env.local` too so the service and the shell
agree.
