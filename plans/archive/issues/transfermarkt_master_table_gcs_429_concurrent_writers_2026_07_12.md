---
doc_type: issue
title: Transfermarkt master.parquet hits GCS per-object mutation rate limit under concurrent closer runs
summary: >-
  While closing the sports_p2 item #6 transfermarkt residual (2026-07-12), 3 slots (6/8/9) ran
  sports_daily_enum_residual_closer_2026_07_12.py concurrently against the same TM residual dates. Each writes to the
  SAME non-sharded reference tables (sports_reference/master/entity={player_values, teams,team_mapping}/master.parquet)
  on every league/date iteration. Concurrent writers triggered GCS 429 "exceeded the rate limit for object mutation
  operations" on entity=player_values and entity=team_mapping (8 occurrences total, all CRITICAL-severity in the event
  log). All observed occurrences were transparently retried (max_retries=3) and succeeded on the next write a moment
  later — no confirmed data loss this session — but this is a latent risk if retries are ever exhausted or if
  concurrency increases further.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, agent-orchestrator]
scope: [engineer, admin]
tags: [infrastructure, gcs, rate-limit, sports, transfermarkt, concurrent-writers]
related: [plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md]
created: 2026-07-12
parent_epic: sports_master
priority: P2
source: [slot-6, sports_p2_history_reference_and_odds_2015_to_present-002]
assigned_vm: planning
resolved_by: instruments-service@7b79bb8a, agent-orchestrator@5d35b4c
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Transfermarkt master.parquet GCS 429 under concurrent closer runs

## What I found

While monitoring the item #6 TM residual closer (PID 3181371,
`sports_daily_enum_residual_closer_2026_07_12.py --conc 6`) to completion, I found two OTHER slots (8 and 9)
independently running the exact same closer script concurrently against the same 25-date TM residual
(`slot8-tm-closer-20260712`, `slot9-tm-residual-closer`) — each in its own slot worktree, each with its own
`MANIFEST_PER_VM_SHARDS` per-VM shard (safe, isolated writers for the _manifest_ rows). However,
`_fetch_transfermarkt_data`'s team/roster fetch path ALSO writes to 3 shared, non-sharded reference tables per
league/date iteration:

- `instruments-store-sports-prd-central-element-323112/sports_reference/master/entity=player_values/master.parquet`
- `.../entity=teams/master.parquet`
- `.../entity=team_mapping/master.parquet`

These are single objects (not per-VM sharded), so all 3 concurrent closers were read-modify-writing the SAME objects.
GCS enforces roughly 1 mutation/sec per object; the concurrent write pressure produced 8 `429 rateLimitExceeded` errors
in my process's log alone (4× `entity=player_values`, 4× `entity=team_mapping`) between 11:03:36–11:03:37 UTC. Each was
logged as `severity: critical` with `recovery_strategy: alert`, `max_retries: 3`. In every case observed, the very next
write to the same entity succeeded within ~1 second — the closer's own retry wrapper absorbed it transparently, and the
final manifest gate re-check confirmed transfermarkt fully resolved (`pending_fetch=0`, `af=0`) — so this did NOT cause
data loss this run.

## Why it matters

- This is a previously-unseen failure mode: `sports_daily_enum_residual_closer_2026_07_12.py`'s own docstring/design
  assumed one-at-a-time execution (it was written to close a single, one-off residual), but nothing prevents — and this
  session accidentally demonstrated — 3 slots dispatching it concurrently. If concurrency increases further (more slots,
  or a future scheduled/forward-poll job overlapping a manual closer run), retries could exhaust and a write could be
  silently dropped for the master reference table (distinct from the availability manifest, which IS per-VM sharded and
  safe).
- The master tables are a convenience/lookup layer (team ID → league/season mapping used by the adapter itself, not the
  availability-manifest gate this plan's item #6 checks), so a dropped write here would not show up in the
  manifest-based gate check — it would surface later as a stale/missing team mapping for a specific league-season, a
  silent-looking gap distinct from the `capture_status` machinery the workspace's honest-absence rules already guard.

## Recommended decision

1. Either (a) make the master-table write path idempotent-safe under concurrency by sharding it the same way the
   availability manifest already is (per-VM shard + periodic consolidation), or (b) add a serialization guard (e.g. a
   lightweight GCS-object lock, or simply documenting "run at most one instance of this closer script at a time" in its
   own docstring/`# Lifecycle:` header) so operators/dispatchers don't accidentally fan out concurrent copies of a
   script that was designed for single-instance use.
2. Since this script is itself a one-off (`# Lifecycle: ONE-OFF` per its header, delete-when the residual reaches zero —
   which it now has, per this session's gate re-check), a full sharding fix may not be worth the investment for this
   specific script. The more durable fix is (b): if any FUTURE one-off residual-closer script writes to a shared
   non-sharded reference table, its docstring should say so explicitly and the backlog/dispatcher should avoid fanning
   the same script out to multiple slots for the same residual.

## Todos

- [x] ✅ [SCRIPT] P2. Add a one-line concurrency-safety note to `_fetch_transfermarkt_data`'s master-table write helper
      (or wherever `Transfermarkt master/<entity>: N rows written` is logged from) documenting that these 3 tables are
      NOT per-VM sharded and should not be written from more than one concurrent process — grep
      `instruments-service/instruments_service/reference_data/adapters/sports/adapters/transfermarkt.py` for the write
      call sites. (repo: instruments-service) — instruments-service@7b79bb8a: added concurrency note to
      `_write_master_append`'s docstring in `instruments_service/engine/orchestrator/transfermarkt.py` (the actual
      shared write helper for all 3 master-table entities; the reference_data/adapters path named in the todo doesn't
      exist — the function lives under `engine/orchestrator/`).
- [x] ✅ [INFRA] P3. Consider whether the backlog/dispatcher should detect + prevent fanning out the same one-off
      backfill/closer script to multiple slots concurrently for the same residual (this session had 3 slots
      independently pick up `sports_daily_enum_residual_closer_2026_07_12.py` against the identical TM residual —
      redundant work, and the root cause of this issue's 429s). (repo: agent-orchestrator) — agent-orchestrator@5d35b4c:
      yes, via the EXISTING (but structurally dead) `collision_group` mutex. Investigated `server/dispatch.py`'s
      per-repo/collision-group guards — they already exist (`_repos_collide` + `task.collision_group in active_groups`)
      but `regen_backlog_from_plan.py` hard-coded `repos=[]`/`collision_group=None` on every auto-derived task, so the
      guard was a no-op for all normally-dispatched work; a blanket per-repo fix was explicitly rejected 2026-05-18 as
      too restrictive for the fleet's real parallelism. Shipped a targeted fix instead: `regen_backlog_from_plan.py` now
      derives `collision_group="script:<name>"` when a todo's brief names a `.py`/`.sh` script file, so two todos naming
      the SAME script become mutually exclusive via the existing dispatch guard (scoped to the script name, not the repo
      — other work in the same repo still parallelizes freely). Hand-set `collision_group` values are preserved across
      regen ticks. 9 new unit tests (derivation, reconcile-preserves-hand-tune, end-to-end regen). `quality-gates.sh`
      green (1199 passed, basedpyright clean); shipped via quickmerge.

## Progress Log

### 2026-07-12 ~11:1x UTC — slot-6: filed while closing item #6

Found while monitoring my own slot's TM residual closer to completion for
`sports_p2_history_reference_and_odds_2015_to_present-002`. No data loss confirmed (all 8 occurrences retried
successfully within ~1s), so not blocking the item #6 gate flip — filing per the findings-closure hard rule since I'm
not fixing this inline (out of this VERIFY task's scope). transfermarkt PLAYER_VALUES manifest gate itself is now
confirmed clean (`pending_fetch=0`, `af=0`) independent of this master-table finding.

### 2026-07-12 13:5x UTC — slot-8 (infra): closed todo #2, resolved

Investigated `agent-orchestrator/server/dispatch.py`'s existing collision guards before building anything new —
`_repos_collide` + `task.collision_group in active_groups` already exist, but `regen_backlog_from_plan.py` hard-coded
`repos=[]` / `collision_group=None` on every plan-derived task, so both guards were structurally dead for all normal
dispatch. Populating `repos` from plan frontmatter was considered and rejected: `dispatch.py`'s own comment records that
blanket per-repo blocking was explicitly loosened 2026-05-18 as too restrictive for the fleet's actual parallelism
pattern (multiple slots legitimately work the same repo on different files concurrently), so reintroducing it would
regress a deliberate prior decision. Shipped the narrower fix instead: auto-derive `collision_group="script:<name>"`
from a `.py`/`.sh` filename named in the todo's own brief text — this closes exactly the incident's shape (two todos
naming the identical one-off script become mutually exclusive) without touching repo-level parallelism at all.
`agent-orchestrator@5d35b4c`, quality-gates.sh green (1199 passed, basedpyright clean), 9 new tests. All todos in this
issue doc are now closed → `status: resolved`.
