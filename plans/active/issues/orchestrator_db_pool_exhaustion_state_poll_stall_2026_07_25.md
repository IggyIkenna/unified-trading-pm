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
asset_group: [cross-cutting]
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
last_updated: 2026-07-25
priority: P2
parent_epic: orchestrator_master
source: "main orchestrator (agt-52bb99) on-host diagnosis during poll loop, 2026-07-25 ~02:12"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
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

## Todos

- [ ] [BACKEND] P2. Determine root cause: connection LEAK vs. concurrency-over-pool. Audit every DB-session usage on the
      hot paths (`/api/slots/*/git-status`, `/api/agents/*/poll`, `/api/state`) for a session/connection that isn't
      returned to the pool on all exit paths (missing `with Session(...)` / context-manager / `finally` close,
      especially on error branches). **Done when**: each hot-path handler is proven to release its connection on success
      AND error, with a test that exhausts the pool and asserts recovery.
- [ ] [BACKEND] P2. Make the liveness/health signal DB-aware (or add a separate readiness probe the unit/monitor can
      watch): a cheap `SELECT 1` with a short timeout so pool starvation surfaces as unhealthy and the existing
      auto-restart path can fire. Keep `/health` cheap for the LB, but expose DB-backed readiness for the self-heal
      trigger. Cross-ref `/codex/04-architecture/autonomous-recovery-matrix.md` (add "DB pool exhaustion → restart" to
      the matrix if protective-arming-autonomous applies).
- [ ] [BACKEND] P3. Right-size / harden the pool for the known concurrency: raise `pool_size`/`max_overflow` to cover
      peak concurrent slot git-status + poll fan-in, and/or lower `pool_timeout` so a starved request fails fast (loud)
      instead of hanging 30s (silent). Consider batching/serialising the per-slot git-status writes so N slots don't
      each hold a connection simultaneously.

## Notes

- Non-destructive by design on the operator side: this doc records the diagnosis only. Main did NOT restart the service
  (an outward, fleet-affecting action outside the main-agent charter) — the condition self-recovered, and a restart is
  the operator/managed-path call if it recurs and does not clear.
- Adjacent (separate) observation in the same window: slot-1 `ff_pull_last_result: "conflict"` at 01:51:06 — handled by
  `fleet-git-health-guard.sh`, not part of this DB-pool issue.
