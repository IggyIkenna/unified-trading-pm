---
title: Orchestrator spawn reliability — zombie-session wedge, boot-paste race, SQLite write-lock cascade
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P0
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-10
locked_by: live-defi-rollout
source:
  - chat/2026-06-10 operator: two HEADROOM EXHAUSTED escalation alerts (execution-service#250, deployment-service#46)
  - vm-0 live diagnosis 2026-06-10 (SSM)
---

# Orchestrator spawn reliability — the HEADROOM-EXHAUSTED wedge

> **Incident (2026-06-10):** `/api/escalate` 503'd repeatedly ("HEADROOM EXHAUSTED — no free slot") for
> execution-service#250 + deployment-service#46. vm-0 had **6 tmux sessions** (slots 1,2,4,5,9,10) all running idle
> Claude REPLs at the blank welcome prompt, every slot row `status=killed` / `tmux_session=NULL`. No worker was doing
> any work, yet every slot read as occupied → no capacity → escalations 503.

## Root-cause chain (three compounding bugs)

1. **SQLite write-lock cascade.** Every transaction uses `BEGIN IMMEDIATE` (db.py `_on_begin`) — even read-only loop
   queries take the single WAL writer lock. The spawn path (`escalation.escalate` / `autospawn._tick_once`) runs the
   **entire slow `tmux_spawn.spawn`** (subprocess + multi-second dialog/paste waits) **inside** its `session_scope`
   transaction, holding the write lock for the whole spawn. Under the 429-driven heartbeat storm a hold exceeds the 30s
   `busy_timeout` → `sqlite3.OperationalError: database is locked` → the `WorkerLivenessWatchdog` + `TmuxPruner` ticks
   crash (watchdog `_tick_once` line 344, observed 11:13/11:27/11:46), so the reap→teardown→respawn cycle never
   completes.
2. **Boot-paste races claude startup.** `tmux_spawn.spawn` dismisses startup dialogs with a fixed-timeout poll (10s)
   then pastes the boot prompt. Claude's startup auto-update ("✗ Auto-update failed", claude 2.1.146 on the VM) pushes
   the input-ready marker past 10s → the dismiss poll times out → `_paste_prompt` fires before the pane is ready →
   `tmux paste-buffer failed: can't find pane` → `do_spawn` returns failure. But `_start_session` **already created the
   tmux session** running idle claude → orphan session, `slot.tmux_session` never set (stays NULL, status stays
   `killed`).
3. **Watchdog blind to the wedge class.** The reap loop only scans `status IN {working, dispatched, stale}`. The orphan
   from (2) is `status=killed` → never evaluated → **never torn down**. `_pick_free_slot`/AutoSpawn count the live
   session as occupied (`has_session=True`) → the slot is lost to AutoSpawn AND `/api/escalate` permanently → HEADROOM
   EXHAUSTED.

## Immediate ops done (2026-06-10, vm-0)

- [x] [OPS] P0. Reclaimed the 6 zombie slots (`tmux kill-session`), restarted `orchestrator.service`,
      `wal_checkpoint (TRUNCATE)` (drained a 4 MB WAL). Capacity restored.
- [x] [OPS] P0. Attempted to disable claude auto-update (appended `DISABLE_AUTOUPDATER=1` to the 4
      `~/.claude-accounts/*.env` + seeded `autoUpdates:false` into the per-slot CLAUDE_CONFIG_DIRs). **NOTE: claude
      2.1.146 ignored it — "Auto-update failed" still shows.** → see Phase 2 (find the mechanism that actually works /
      pin the CLI).

## Phase 1 — code fixes SHIPPED this change (agent-orchestrator)

- [x] [CODE] P0. **Watchdog orphan-session reclaim** (`worker_liveness_watchdog.py`): a pre-pass before the main reap
      loop tears down any `status=killed` slot whose canonical tmux session is still alive and whose `last_spawned_at`
      is older than `_ZOMBIE_RECLAIM_GRACE_SECONDS` (180s; NULL = ∞ = immediate). NOT cap/cooldown-gated — it is cleanup
      of an already-dead worker, so AutoSpawn can cleanly retry. **This is the self-healing safety net: zombies become
      transient, never a permanent wedge.**
- [x] [CODE] P0. **Boot-paste resilience** (`tmux_spawn.py`): dismiss-prompt readiness window 10s→20s (returns the
      instant the ready marker appears, so the fast path is unchanged); `_paste_prompt` retries load+paste
      (`_PASTE_MAX_ATTEMPTS=3`, re-checking `has_session` between attempts) instead of raising on a
      momentarily-not-ready pane. **Capped at 20s deliberately** — the spawn still runs inside the BEGIN-IMMEDIATE
      transaction, so the wait holds the write lock; staying under the 30s `busy_timeout` avoids re-triggering the lock
      cascade (Phase 2 removes that cap).

## Phase 2 — durable follow-ups (the DB-lock ROOT + deterministic startup) [P0/P1]

- [ ] [CODE] P0. **Move the slow spawn OUT of the write transaction** (`escalation.escalate` + `autospawn._tick_once`):
      read the needed slot fields (model/effort/thinking/account) into plain values inside a SHORT transaction, run
      `tmux_spawn.spawn` OUTSIDE any `session_scope`, then a SHORT transaction to persist
      `tmux_session`/`last_spawned_at`. Eliminates the multi-second write-lock hold → no more "database is locked"
      crashing the watchdog/pruner, and lets the boot readiness wait be unbounded (raise the 20s cap from Phase 1).
      Watch for `DetachedInstanceError` (the reason it was in-session originally — the fix is to extract scalars, not
      pass the ORM row out).
- [ ] [OPS] P1. **Deterministically disable claude auto-update OR pin the CLI.** `DISABLE_AUTOUPDATER=1` +
      `autoUpdates:false` did not stop it on 2.1.146. Find the honored mechanism for the deployed CLI, or pin/upgrade
      the fleet CLI so startup is fast + deterministic (removes the primary source of the boot-paste timing miss).
      Target: vm-0 spawn env / deployment.
- [ ] [CODE] P1. **Verify the boot actually landed** post-paste: capture-pane after submit and confirm the prompt left
      the empty state; if still empty, re-deliver once. Closes the residual window where a paste "succeeds" (rc 0) but
      the TUI dropped it.
- [ ] [TEST] P1. Unit/integration test for the watchdog orphan-reclaim (killed + live session + stale spawn → session
      reclaimed) and the paste-retry (transient pane-miss → eventual success). Target: agent-orchestrator tests.

## Success criteria

- A spawn whose boot-paste momentarily misses self-heals within one watchdog interval (no permanent
  `killed`+live-session wedge); `/api/escalate` no longer 503s while idle slots exist.
- No `database is locked` in the orchestrator journal under normal spawn load (Phase 2).
- A fresh AutoSpawn/escalation worker reliably reaches a working state (boots its task), verified on vm-0.

## Temporary states + their canonical follow-up plans

- **Boot readiness wait capped at 20s** — TEMPORARY (holds the DB write lock); canonical fix = Phase 2 "move spawn out
  of the transaction", which removes the cap.
- **claude auto-update still firing on vm-0** — TEMPORARY; canonical fix = Phase 2 "disable/pin the CLI".
