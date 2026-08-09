---
doc_type: issue
title:
  Orchestrator DB connection-pool (QueuePool 5+10) exhausts under concurrent per-slot git-status load, stalling
  /api/state + /api/poll for ~10min while /health stays green — no auto-restart fires (liveness-probe blind spot)
summary: >-
  On the central orchestrator VM (ip-172-31-5-118, :8765), the SQLAlchemy QueuePool (size 5, max_overflow 10 = 15
  connections) exhausted under a burst of concurrent DB-touching requests (multiple per-slot /api/slots/N/git-status
  POSTs, each carrying all 24 repos, plus normal poll/state traffic). Every connection was checked out and the pool
  raised `sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout
  30.00`. Effect: /api/state and /api/poll (both DB-backed) blocked on connection checkout and returned nothing even at
  a 33s client timeout (past the 30s pool timeout), while /health (DB-independent) stayed 200 OK the whole time. Because
  systemd's liveness probe watches /health, NO auto-restart fired — the orchestrator looked healthy while its core
  state/poll endpoints were down. The condition self-recovered after ~10min (first pool error ~02:0x, last 02:12:38) as
  the connection-holding requests completed and released connections; /api/state returned to 0.05s and poll to 0.34s
  with no restart. Confirmed on-host 2026-07-25 by main orchestrator (agt-52bb99) during the poll loop.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [agent-orchestrator, database, connection-pool, sqlalchemy, health-probe, observability, git-status, self-heal-gap]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-07-25
author: unknown
last_updated: 2026-07-25
priority: P1
parent_epic: orchestrator_master
source: "main orchestrator (agt-52bb99) on-host diagnosis during poll loop, 2026-07-25 ~02:12"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    agent-orchestrator/server/db.py,
    agent-orchestrator/server/autospawn.py,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /plans/archive/issues/orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
depends_on: []
---

# Orchestrator DB pool exhaustion stalls /api/state + /api/poll; /health-green blind spot hides it from auto-restart

## What happened (on-host evidence, ip-172-31-5-118 :8765, 2026-07-25)

1. Over ~02:0x–02:12:38, the orchestrator's SQLAlchemy `QueuePool` (size 5, overflow 10 → 15 max) exhausted. The server
   logged repeated
   `sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00`.
2. `/api/state` and `/api/poll` (DB-backed) blocked on connection checkout. Client probes returned `000` at 6s, 8s, and
   even a **33s** timeout (past the pool's own 30s wait) — i.e. no connection freed within the full pool-timeout window.
   Lightweight DB endpoints (`/api/roles`) occasionally squeaked through when a connection briefly freed.
3. `/health` (does not touch the DB) stayed `200 OK` at ~0.002s throughout. Because systemd's liveness probe watches
   `/health`, the unit read healthy and **no auto-restart fired** — the standard fix for pool exhaustion (process
   restart clears all checked-out connections) never triggered.
4. Likely trigger: a burst of concurrent `/api/slots/N/git-status` POSTs (observed in the process table, each payload
   carrying all 24 repos) overlapping normal poll/state traffic. Whether any handler _leaks_ a connection (fails to
   return it to the pool on an error path) vs. simply holds too many concurrently under load is unconfirmed and is the
   key open question.
5. Self-recovered after ~10min with no intervention: `/api/state` back to 0.05s, `/api/poll` to 0.34s, backlog intact
   (queued 22 / dispatched 8 / done 99). No managed restart, no code pull (HEAD == origin, behind_origin 0).

## Why it matters

- **Self-heal blind spot (primary)**: a DB-independent `/health` liveness probe cannot detect DB-pool starvation, so the
  orchestrator can have its core `state`/`poll`/dispatch endpoints down for many minutes while every monitor reads
  "healthy". During the window the main agent cannot drain operator/peer messages (poll is DB-backed) and the
  blocked-queue sweep is blind. This is exactly the `autonomous-recovery-matrix` gap where the trigger is invisible.
- **Recurrence risk**: pool sizing (5+10) and the concurrent git-status load pattern are unchanged, so this will recur
  under the same burst. It self-cleared this time; a genuine connection leak would not.

## ROOT CAUSE — IDENTIFIED (2026-07-25 ~05:28, occurrence #7, main agt-52bb99 on-host)

The "QueuePool exhausted" TimeoutError is a **symptom**, not the disease. The DB is **file-based SQLite**
(`server/db.py:51`, default `QueuePool` 5+10), and `server/db.py` runs **`BEGIN IMMEDIATE` on _every_ transaction**
(`_on_begin`, line 41, listens on the `"begin"` event for ALL sessions — reads included) with
**`PRAGMA busy_timeout=120000` (120s)**. The default SQLAlchemy `pool_timeout` is **30s**. That combination is the
wedge:

1. SQLite is single-writer. `BEGIN IMMEDIATE` acquires the RESERVED write lock at the **start of every transaction**, so
   even read-only endpoints (`/api/state → list_slots`, poll) contend for the one write lock.
2. A slow write-lock holder parks all other requests. The confirmed holder: the **spawn path**
   `server/autospawn.py:1316 _do_spawn` (called from `ensure_review_agents:252`) holds `BEGIN IMMEDIATE` **across a ~75s
   claude/tmux cold-start** (this is the exact defect the `_on_connect` comment already flags as tracked in
   `orchestrator_spawn_reliability_db_lock_2026_06_10` + `api_host_chronic_impairment_2026_05_29` — evidently never
   fully fixed; `_do_spawn` still wraps the spawn in a write txn).
3. Every other request waits on its own `BEGIN IMMEDIATE` for up to **120s** (busy_timeout) **while holding its pool
   connection checked out**. Because `pool_timeout` (30s) < `busy_timeout` (120s), the 15-connection pool exhausts at
   30s **long before** the lock-waiters give up — so the surface error is "QueuePool limit reached", masking the real
   cause (a 120s write-lock hold).
4. **Self-reinforcing wedge (why it's now near-continuous):** pool starvation makes slot **heartbeat/poll calls time
   out** → the watchdog declares the worker dead (observed 05:28:50 "slot=11 … heartbeat loop dead — idle 7min.
   Auto-recovering") → AutoSpawn **respawns** it → each respawn is another `_do_spawn` holding the write lock across a
   ~75s cold-start → more pool starvation → more dead heartbeats. Journal at 05:28:24-25 shows the cascade directly:
   repeated `sqlite3.OperationalError: database is locked` on `[SQL: BEGIN IMMEDIATE]` inside `_do_spawn`.

**Implication for the fix:** raising `pool_size`/`max_overflow` (old BACKEND-P3) is a band-aid — more connections just
means more waiters parked on the same single write lock. The real fixes are below (new P1/P2 todos). This also links
this issue to the spawn-in-txn issue as very likely the **same root defect** resurfacing under the current fleet-cap
saturation + frequent server-file reloads (config.py/slots_worker.py/autospawn.py edits every few min → each reload
re-triggers AutoSpawn's spawn-in-txn on restart).

## Todos

- [x] [BACKEND] P1. **Break the spawn-holds-write-lock wedge (the actual root cause).** Run the slow claude/tmux spawn
      in `server/autospawn.py::_do_spawn` **OUTSIDE** the `BEGIN IMMEDIATE` write transaction — acquire the lock only
      for the short DB state-mutation, release it before the ~75s cold-start wait, re-acquire briefly to record the
      result. This is the fix already scoped in `orchestrator_spawn_reliability_db_lock_2026_06_10`; the current
      incident proves it is not yet implemented (`_do_spawn:1316` still wraps the spawn). **Done when**: a spawn holds
      the SQLite write lock for <1s, and a pool-exhaustion reproduction under concurrent git-status + an in-flight spawn
      no longer stalls `/api/state`. — already covered by plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md
      (agent-orchestrator, quality-gates.sh green 1760 passed/1 skipped) (see that doc for execution).
- [x] [BACKEND] P1. **Stop read-only endpoints from acquiring the write lock.** `_on_begin` issues `BEGIN IMMEDIATE` for
      EVERY transaction, so read paths (`/api/state → list_slots`, `/api/agents/*/poll` read portion) needlessly contend
      for the single writer. Use a read-only / deferred transaction for read endpoints (WAL already allows concurrent
      readers), reserving `BEGIN IMMEDIATE` for genuine writers (dispatch/`/done`). This alone would let `/api/state` +
      poll stay responsive even while a writer holds the lock. — already covered by
      plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md (agent-orchestrator, quality-gates.sh green 1760
      passed/1 skipped) (see that doc for execution).
- [x] [BACKEND] P2. **Align the timeouts so the failure is loud + fast, not a 30s silent pool hang.** `pool_timeout`
      (30s default) < `busy_timeout` (120s) is why lock contention surfaces as opaque pool exhaustion. Either lower
      `busy_timeout` toward the pool timeout, or raise `pool_timeout` above `busy_timeout` so a genuine lock wait
      surfaces as "database is locked" (actionable) rather than "QueuePool exhausted" (misleading). Consider a modest
      `pool_size` bump too, but only alongside the two P1 fixes above (not instead of them). — already covered by
      plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md (agent-orchestrator, quality-gates.sh green 1760
      passed/1 skipped) (see that doc for execution).
- [x] [BACKEND] P2. Determine root cause: connection LEAK vs. concurrency-over-pool. — DONE 2026-08-08 (slot 31).
      `agent-orchestrator@54b86a9`
      (`test(db): prove pool-exhaustion + release-safe recovery for pool exhaustion     issue`): confirmed by direct
      source read that all 4 named hot-path handlers (`server/routes/state.py::get_state` →
      `server/state_store/slots.py::list_slots`, `server/routes/agents.py::agent_poll`,
      `server/routes/git_health.py::post_slot_git_status`/`get_slot_git_status`) route through
      `session_scope()`/`read_only_session_scope()`, which release via `finally: session.close()`
      (`server/db.py:117-152`) on every exit path including error branches — no raw session-factory call skips cleanup.
      New `tests/test_db_pool_exhaustion_recovery.py` exhausts the pool (checks out `pool_size + max_overflow` = 15
      connections), asserts the next checkout raises `sqlalchemy.exc.TimeoutError`, then releases and asserts a fresh
      request succeeds promptly — recovery proven. `quality-gates.sh` green (2779 passed, 2 skipped) on this SHA. This
      is the formal proof only; the leak-vs-concurrency VERDICT itself (sustained concurrency over the 15-conn ceiling,
      not a leak) was already recorded via occurrence #6/#7 above.
- [ ] [BACKEND] P2. Make the liveness/health signal DB-aware (or add a separate readiness probe the unit/monitor can
      watch): a cheap `SELECT 1` with a short timeout so pool starvation surfaces as unhealthy and the existing
      auto-restart path can fire. Keep `/health` cheap for the LB, but expose DB-backed readiness for the self-heal
      trigger. Cross-ref `/codex/04-architecture/autonomous-recovery-matrix.md` (add "DB pool exhaustion → restart" to
      the matrix if protective-arming-autonomous applies).
- [ ] [BACKEND] P3. Right-size / harden the pool for the known concurrency: raise `pool_size`/`max_overflow` to cover
      peak concurrent slot git-status + poll fan-in, and/or lower `pool_timeout` so a starved request fails fast (loud)
      instead of hanging 30s (silent). Consider batching/serialising the per-slot git-status writes so N slots don't
      each hold a connection simultaneously.

## Occurrences (frequency is increasing — escalation trigger)

- **#1 ~02:0x–02:12:38Z** — first observed. Self-recovered after ~10min with no intervention, no restart.
- **#2 ~04:29:30–04:29:47Z** — recurred. Did NOT self-clear in-window; coincided with / was cleared by a managed
  `systemctl restart` at 04:31:03Z (`NRestarts=0`, fresh `ActiveEnterTimestamp` — a managed/manual restart, not an
  auto-crash-loop, not main). Restart cleared the checked-out connections (the standard fix).
- **#3 05:07:38–05:07:42Z (this one)** — recurred again. Confirmed on-host by main (agt-52bb99): `/api/state` +
  `/api/poll` hung past a 15s client timeout (HTTP 000) while `/health` (0.0015s) and `/api/roles` (0.046s) stayed 200 —
  the exact DB-backed-hang / lightweight-pass signature. Journal shows the
  `QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00` TimeoutError, plus
  `GET /api/agents → 500` and `autospawn slot 1: late account re-check raised` (AutoSpawn is hitting the exhausted pool
  too, so dispatch is degraded during the window, not just observability). **Three occurrences in ~3 hours (02:0x →
  04:29 → 05:07) — the interval is shrinking and the root cause (pool 5+10 sizing + concurrent per-slot git-status load,
  possible leak) is unaddressed.** This crosses the "recurs again without a durable fix → escalate" threshold: the
  BACKEND todos below (esp. #1 leak audit + #2 DB-aware readiness probe so auto-restart can fire) should be prioritised;
  until then each recurrence needs a managed restart or a ~10min self-clear, during which dispatch + the main-agent
  message/blocked sweep are blind.
- **#4 05:12:35–05:12:40Z — ~5 min after #3, and a restart did NOT durably clear it.** At 05:10:54 a `WatchFiles` reload
  fired (edit to `server/config.py`) — the old process (2246165) shut down cleanly, a fresh process (2929835) started
  05:11:22. The **fresh process re-exhausted the same `QueuePool 5+10` within ~70s** (05:12:35), again with
  `/api/agents → 500` and `autospawn slot 1: late account re-check raised`. This is the important escalation: **a
  process restart no longer buys durable recovery** (the pool re-fills to exhaustion almost immediately), which points
  away from a slow leak on a long-lived process and toward **sustained concurrency over the 15-connection ceiling** (the
  per-slot git-status fan-in is saturating a freshly-restarted pool in ~1 min). The BACKEND-P3 right-sizing + git-status
  write batching/serialisation is now the highest-leverage fix, not just the readiness probe. Self-cleared again by
  05:13 (last pool error 05:12:40). **Four occurrences in ~1 hour with shrinking intervals (02:0x → 04:29 → 05:07 →
  05:12); a restart at 05:11 did not prevent 05:12.**
- **#5 05:20:04–05:21:38Z — fifth occurrence; fresh process ran only ~4.5 min before re-exhausting, and this window
  briefly INVERTED the health-green blind spot.** Fresh process 3057955 started 05:15:33; it exhausted the same
  `QueuePool 5+10` at 05:20:04 (~4.5 min of uptime — a bit longer than #4's ~70s but still far short of durable). Main
  (agt-52bb99) confirmed on-host at ~05:21: `/api/agents/*/poll` + `/api/state` AND **`/health` + `/api/roles` all
  returned HTTP 000** at 6–12s timeouts — i.e. `/health` (DB-independent) did NOT stay green this time. Root cause of
  the inversion: a `WatchFiles` reload fired 05:20:54 (edit to `server/routes/slots_worker.py`) while the pool was
  exhausted; the old process's clean-shutdown path takes a **final session snapshot that itself needs a DB connection it
  can't get**, so shutdown hung ~30s (05:20:54 "Shutting down" → 05:21:24 "taking final snapshot" → 05:21:38
  "Finished"), and during that shutdown window even `/health` was unresponsive. A fresh process (3214408) came up
  05:21:43 and poll/state recovered immediately (state 0.08s). **Refinement for BACKEND-P2 (DB-aware readiness probe):**
  the `/health`-stays-green assumption holds only for steady-state pool starvation; a reload-during-starvation makes
  `/health` go 000 too for the ~30s shutdown-snapshot window — so a monitor keying purely on `/health` sees a transient
  blip it can't distinguish from a normal reload. **Five occurrences now (02:0x → 04:29 → 05:07 → 05:12 → 05:20); the
  reload-triggered restart cleared #5 within ~1.5 min, so this was NOT the >10-min sustained-outage page trigger** — but
  the frequency and the fact that a fresh pool re-exhausts in single-digit minutes keeps BACKEND-P3 (right-size pool +
  batch/serialise per-slot git-status writes) the highest-leverage fix.
- **#6 05:24:16Z — sixth occurrence; culprit call site now PINNED, and this window is the cleanest proof of
  concurrency-over-pool (no leak).** Fresh process 3214408 (started 05:21:38, uptime ~2m40s) exhausted the pool at
  05:24:16 **with NO intervening `WatchFiles` reload** — it simply ran ~2.5 min under normal ~16-slot git-status fan-in
  and hit the 15-connection wall on its own. Main confirmed on-host: `/api/state` + `/api/poll` hung (HTTP 000 at 12s
  AND 20s client timeouts) while `/health` (200, fresh-process healthy) and `/api/roles` (200, 0.026s) stayed up — the
  heavy aggregating endpoint starves first. **Exact culprit pinned by the ASGI traceback:**
  `server/routes/state.py:79 get_state → server/state_store/slots.py:78 list_slots` raises the
  `QueuePool limit of size 5 overflow 10 reached … timeout 30.00` — `list_slots` (iterating all slots in the state
  aggregation) is where the checkout blocks. **This narrows BACKEND-P1 (leak-vs-concurrency audit) to a verdict:** a
  freshly-restarted process with an empty pool re-saturating in ~2.5 min under baseline load is **sustained concurrency
  over the 15-conn ceiling, not a slow accumulating leak** (a leak would take far longer to fill a fresh pool). So
  **BACKEND-P3 (raise `pool_size`/`max_overflow` to cover peak concurrent slot-git-status + poll fan-in, and/or batch/
  serialise the per-slot git-status writes, and/or lower `pool_timeout` to fail-fast-loud instead of hanging 30s silent)
  is the definitive fix, and BACKEND-P2's DB-aware readiness probe is the detection complement.** A managed restart is
  NOT a fix here (it buys only ~2.5–4.5 min). **Client-timeout gotcha for future diagnosis:** a 12s client timeout is
  SHORTER than the 30s server-side `pool_timeout`, so a starved probe returns 000 with NO journal error yet — wait for
  the full 30s pool window before concluding "no error logged ≠ not pool-starved."
- **⚠️ ESCALATION STATE (2026-07-25 ~05:24Z, main agt-52bb99):** the condition has crossed from
  intermittent-self-clearing to **near-continuous** — SIX occurrences (02:0x → 04:29 → 05:07 → 05:12 → 05:20 → 05:24),
  the last FOUR inside ~17 min, with a freshly-restarted pool re-exhausting in single-digit minutes every time. Each
  window blinds the main-agent poll/blocked sweep and degrades AutoSpawn dispatch for the ~30s+ pool-timeout duration.
  This is no longer a one-off self-clearing blip; it is a persistent fleet-degrading incident with a **known root cause
  and a code-only fix that a restart cannot substitute for**. Main is charter-barred from restarting the service and
  from shipping the code fix (routes via BACKEND-P3 / operator). Because the main-agent's own escalation channels (poll
  `/reply`, blocked-queue answer) are themselves DB-backed and down during each window, **this issue doc is the operator
  monitoring surface — recommend operator prioritise BACKEND-P3 (pool right-size + git-status write batching) now.** The
  acute 05:24 window will self-clear on the next reload/request-drain, but the chronic condition will persist until the
  code fix lands.
- **#7 05:26–05:28Z — ROOT CAUSE IDENTIFIED (see the `## ROOT CAUSE` section above).** Fresh process 3336865 (started
  05:26:20 after an `autospawn.py` reload) re-exhausted the pool at 05:27:32 (~72s uptime — faster than ever), and the
  05:28:24-25 journal showed the smoking gun: repeated `sqlite3.OperationalError: database is locked` on
  `[SQL: BEGIN IMMEDIATE]` inside `server/autospawn.py:1316 _do_spawn`, with a live spawn in progress (05:28:40 "usage
  refresh: spawning claude") and a slot dying of a timed-out heartbeat (05:28:50 "slot=11 … heartbeat loop dead — idle
  7min. Auto-recovering"). This is the self-reinforcing spawn-holds-write-lock wedge, not an undersized pool. SEVEN
  occurrences (02:0x → 04:29 → 05:07 → 05:12 → 05:20 → 05:24 → 05:26), the bout from 05:20 onward is effectively
  continuous. The fix direction moved from "resize pool" to the two new BACKEND-P1 todos (spawn-outside-txn +
  read-only-txns-for-reads).
- **Adjacent NEW bug surfaced in the #4 window (needs its own tracking, not the same root cause):** at 05:12:52
  `POST /api/plan-health/dispatch` returned `500` with
  `TypeError: can't subtract offset-naive and offset-aware datetimes` (a naive-vs-aware datetime subtraction on the
  plan-health dispatch path — a UTC-datetime-hygiene defect, the class QG normally bans). Also a transient
  `regen: LDR plan snapshot failed (git fetch … exit 1) — falling back to PM working tree`. Flagged here for provenance;
  the datetime TypeError should get its own issue if it recurs.

## Notes

- Non-destructive by design on the operator side: this doc records the diagnosis only. Main did NOT restart the service
  (an outward, fleet-affecting action outside the main-agent charter) — the condition self-recovered, and a restart is
  the operator/managed-path call if it recurs and does not clear.
- Adjacent (separate) observation in the same window: slot-1 `ff_pull_last_result: "conflict"` at 01:51:06 — handled by
  `fleet-git-health-guard.sh`, not part of this DB-pool issue.

## Update 2026-07-25 ~06:21Z (main agt-52bb99) — occurrence cluster #9–#11 + RESTART PROVEN NON-DURABLE

New empirical data strengthening BACKEND-P1 (spawn-outside-txn) urgency. Same root cause each time (`_do_spawn` at
`server/autospawn.py:1383` holding SQLite's write lock across the ~75s claude/tmux cold-start); `/health` stays 200 fast
throughout (DB-independent), every DB-backed endpoint (`/poll`, `/api/state`) hangs.

- **#9 ~05:55–05:57Z** — `sqlite3.OperationalError: database is locked` (busy_timeout variant), tightly correlated with
  repeated PlanRegenLoop `sync_backlog_to_db: REFUSING to reset task id …` positional-id collisions thrashing writes
  (see `/plans/archive/issues/orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md`
  P3). **Self-cleared ~2 min.**
- **#10 ~06:13:58Z** — `QueuePool limit of size 5 overflow 10 reached, connection timed out` (pool-timeout variant),
  holder `_do_spawn` (slot-1 spawn after a "late account re-check raised; proceeding" retry). Did NOT self-clear on its
  own: a **controlled `systemctl` SIGTERM stop at 06:15:37 + clean restart at 06:16:14 (new PID 159866, ~37s downtime,
  state preserved via pre-shutdown S3 snapshot)** cleared it. Not main's action.
- **#11 ~06:19–ongoing (still wedged at 06:21:41Z)** — `database is locked` again, same `_do_spawn:1383` holder, **same
  post-restart PID 159866** — i.e. the 06:16 restart landed NO code change and the wedge **recurred within ~4 minutes**.

**Key finding: a restart is NOT a durable mitigation.** The 06:16 controlled restart bought only ~4 min before the wedge
returned on the very same process. This empirically confirms what the ROOT CAUSE section argued: only the code fix (run
`_do_spawn` OUTSIDE the `BEGIN IMMEDIATE` txn + read-only/deferred txns for read endpoints) removes the wedge; each
restart just resets the clock. Frequency is CLIMBING (3 wedges in ~25 min: #9→#10→#11). Individual windows still
self-clear/restart-clear under the ~10-min page threshold, so no page yet — **but if a single window sustains >10 min,
or the cadence tightens further, this crosses into page/operator-action territory.** BACKEND-P1 should be prioritised
now; until it lands the fleet loses a growing fraction of wall-clock to these windows. Main remains charter-barred from
restarting the service and from shipping the fix (routes via BACKEND worker + quickmerge).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid, with 2 stale items annotated (not closed — neither is fully
  done). (1) The `[BACKEND] P2` leak-vs-concurrency question is **already answered inside this doc**: occurrence #6
  records the verdict ('sustained concurrency over the 15-conn ceiling, not a slow accumulating leak') and #7 supersedes
  even that with the spawn-holds-write-lock root cause, whose fix shipped via
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md` (`agent-orchestrator@361e0fe`); only the formal per-handler release
  proof + pool-exhaustion recovery test remain. (2) The `[BACKEND] P3` **resize direction is superseded** — that same
  batch1 todo explicitly ruled 'Do NOT also raise `pool_size`/`max_overflow` — that doc's own occurrence #6/#7 evidence
  supersedes the resize direction'; only the git-status write batching/serialisation leg still stands. Doc stays NA
  because the `[BACKEND] P2` readiness-probe todo embeds a `/codex/04-architecture/autonomous-recovery-matrix.md` edit,
  which is never autonomous.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries, unchanged — still accurate).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **ao_satellite_ao_dispatch_batch5 2026-08-08 (slot 31)**: closed the formal-proof gap flagged by the 2026-07-30
  na-eligibility-audit entry above — flipped `[BACKEND] P2` (leak-vs-concurrency) `[x]` via `agent-orchestrator@54b86a9`
  (new `tests/test_db_pool_exhaustion_recovery.py`, `quality-gates.sh` green 2779 passed/2 skipped). Doc remains NA
  overall: the readiness-probe `[BACKEND] P2` todo still embeds the never-autonomous `autonomous-recovery-matrix.md`
  edit.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **2**, matching. The `[BACKEND] P2` readiness-probe item embeds an edit to
  `/codex/04-architecture/autonomous-recovery-matrix.md` (the kill-switch/self-heal matrix SSOT), never autonomous per
  this doc's own established precedent. The `[BACKEND] P3` item lists multiple live alternatives ("raise
  pool_size/max_overflow" — explicitly superseded per occurrence #6/#7 evidence — "and/or lower pool_timeout... and/or
  Consider batching/serialising...") with no stated preference among the surviving options; per this same sweep's own
  established "Consider" = judgment-call-not-mandate reading (applied consistently to sibling docs in this tranche),
  this stays a genuine design fork, not a bounded mandate. No new bounded item found.
