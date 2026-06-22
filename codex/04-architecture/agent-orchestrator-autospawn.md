---
scope: [engineer, admin]
last_reviewed: 2026-05-30
---

# Agent Orchestrator — AutoSpawn Architecture

> **SSOT**: `agent-orchestrator/server/autospawn.py` **Plan**: `plans/active/autospawn_idle_vms_2026_05_30.md`
> **Overview pointer**: `codex/04-architecture/agent-orchestrator-overview.md` § "Auto-spawn lifecycle"

## Problem statement

The orchestrator process can run on a VM with healthy accounts and a non-empty task queue but no active worker — because
spawning was never triggered. Queued tasks sit indefinitely until an operator manually runs `/api/slots/<id>/spawn`.
`AutoSpawnLoop` eliminates that gap: the fleet self-heals.

---

## Trigger contract

A worker is auto-spawned on slot N when **all 5 gates** are true on a given tick:

| Gate               | Condition                                                                    | Skip reason           |
| ------------------ | ---------------------------------------------------------------------------- | --------------------- |
| 1 Queue not empty  | `tasks WHERE status='queued' AND dispatched_to IS NULL` is non-empty         | `queue_empty`         |
| 2 No active worker | `tmux has-session orch-slot-N` → false                                       | `worker_active`       |
| 3 Account headroom | ≥1 usable account: `five_hour_pct < 95` AND `weekly_pct < 95` (null pct = 0) | `no_account_headroom` |
| 4 Slot configured  | `slots` row has `worktree` + `branch` + `operator`                           | `slot_not_configured` |
| 5 Not in cooldown  | Last attempt for this slot > cooldown window ago                             | `cooldown`            |

Headroom check: null `five_hour_pct` or `weekly_pct` is treated as 0 (fresh accounts with no usage data are assumed
healthy — pessimistic only on observed data). This prevents false-blocking new accounts before their first `/usage`
refresh.

---

## Account-pick rotation

`_pick_headroom_account()` runs inside the tick for Gate 3:

1. Load `accounts.json`.
2. Filter: `account_is_usable(session, acc.id)` (not rate-limited, `status=healthy`).
3. Filter: `five_hour_pct < five_hour_ceiling` AND `weekly_pct < weekly_ceiling`.
4. Sort ascending by `(five_hour_pct, weekly_pct)` — spreads load to the least-used accounts first; weekly usage as a
   tiebreaker.
5. Return the first account, or `None` if no candidates.

The same `account_is_usable` source of truth used by the dispatcher's rotation logic ensures account health definitions
are consistent across both spawn paths.

---

## Spawn execution

`_do_spawn(slot, account)` mirrors `server._spawn_with_account_bg`:

1. **Render boot prompt**: `prompts.render("worker", ...)` — same template as the manual `/api/slots/<id>/spawn`
   endpoint. Template is the canonical source of truth for the worker contract.
2. **Spawn tmux session**: `tmux_spawn.spawn(slot_id, boot_prompt, env_file, cwd, ...)` — in-process direct call, no JWT
   round-trip.
3. **Log result**: `log_activity(..., event_type="autospawn_succeeded"|"autospawn_failed")`.

The spawned worker's first `/heartbeat` or `/boot` call updates the `SlotRow` state — `_do_spawn` intentionally does not
touch `SlotRow` to avoid a race.

---

## Anti-flap and Slack alert

Options-book-thin problem: a worker can spawn successfully but exit immediately (crash-loop, boot-prompt parsing
failure, auth issue). Without the flap guard, `AutoSpawnLoop` would re-spawn on every 60 s tick indefinitely.

**Flap detection logic** (in-memory, per slot):

- After each successful spawn, append a `SpawnAttempt(ts, success=True)` to the history for that slot.
- If the last `flap_threshold` (default 3) attempts were all successful **within** `flap_window_seconds` (default 600 s,
  10 min) **and** the worker never claimed a task between spawns → `notify_autospawn_flap()` fires.
- The slot enters a `_flap_backoff_until` for `flap_backoff_seconds` (default 3600 s, 1 hour) — Gate 5 blocks all
  further spawns during backoff.
- A mixed success/failure sequence resets the consecutive streak.

`notify_autospawn_flap()` posts to the configured Slack channel (same alert pattern as `notify_account_rotated`) with VM
name, slot ID, and dashboard link.

---

## Failure modes and recovery

| Failure                     | How handled                                                                         | Recovery                                                                  |
| --------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Boot-prompt render failed   | `_do_spawn` returns `(False, error_str)`; `autospawn_failed` logged; cooldown reset | Fix prompt template; auto-retries after cooldown                          |
| `tmux_spawn.spawn()` raises | Caught; `spawn_failures` counter incremented; cooldown set                          | Investigate tmux/Claude CLI; auto-retries                                 |
| All accounts at ceiling     | Gate 3 blocks with `no_account_headroom`; tick skips                                | Wait for 5h window reset; no action needed                                |
| Slot not configured         | Gate 4 blocks; operator must configure slot row                                     | `POST /api/slots/<id>` with worktree + branch + operator                  |
| Flap detected               | 1-hour backoff; Slack alert fires                                                   | Investigate why worker exits; fix and wait for backoff, or manually spawn |
| AutoSpawnLoop thread dies   | Not auto-restarted within process; requires orchestrator restart                    | Systemd `Restart=always` restarts the process                             |

---

## Environment variables

| Variable                                       | Default | Purpose                                         |
| ---------------------------------------------- | ------- | ----------------------------------------------- |
| `ORCHESTRATOR_AUTOSPAWN_ENABLED`               | `false` | Master on/off switch — must be `true` to enable |
| `ORCHESTRATOR_AUTOSPAWN_INTERVAL_SECONDS`      | `60`    | Tick cadence (seconds between full slot scans)  |
| `ORCHESTRATOR_AUTOSPAWN_COOLDOWN_SECONDS`      | `300`   | Per-slot retry gap (5 min default)              |
| `ORCHESTRATOR_AUTOSPAWN_FIVE_HOUR_PCT_CEILING` | `95`    | Skip if account `five_hour_pct` ≥ this (was 50) |
| `ORCHESTRATOR_AUTOSPAWN_WEEKLY_PCT_CEILING`    | `95`    | Skip if account `weekly_pct` ≥ this (was 80)    |
| `ORCHESTRATOR_AUTOSPAWN_FLAP_THRESHOLD`        | `3`     | Consecutive spawns before flap declared         |
| `ORCHESTRATOR_AUTOSPAWN_FLAP_WINDOW_SECONDS`   | `600`   | Window for consecutive-spawn counting           |
| `ORCHESTRATOR_AUTOSPAWN_FLAP_BACKOFF_SECONDS`  | `3600`  | Backoff duration on flap detection              |

---

## Rollout procedure

Enable per-VM via systemd drop-in (one VM at a time; canary on vm-orchestrator first):

```ini
# /etc/systemd/system/orchestrator.service.d/autospawn.conf
[Service]
Environment=ORCHESTRATOR_AUTOSPAWN_ENABLED=true
```

Rollout script: `unified-trading-pm/scripts/orchestrator/enable_autospawn.sh`.

Fleet rollout: `unified-trading-pm/scripts/orchestrator/run_fleet_enable_autospawn.sh` (sequential, canary abort on
vm-orchestrator failure; captures per-VM enable-time and first-autospawn-time).

---

## Verification

To verify autospawn is working on a VM:

```bash
# 1. Confirm the orchestrator has a queued task
curl -s -H "Authorization: Bearer $JWT" http://localhost:8765/api/tasks?status=queued | jq length

# 2. Kill the current worker
tmux kill-session -t orch-slot-1

# 3. Wait ≤ 60 s (one tick interval); verify the session re-appears
sleep 70 && tmux ls | grep orch-slot-1
```

Expected: `orch-slot-1` session recreated within 60–120 s of the kill.

---

## Anti-patterns (do not do these)

- **Do NOT spawn while a worker is active** — race condition; dispatcher may have just claimed but tmux `has-session`
  returns stale.
- **Do NOT spawn at ≥ 80% weekly usage** — burning rate limits on a fleet rollout is worse than leaving a slot idle.
- **Do NOT spawn more than once per cooldown per slot** — operator may have explicit reasons for an idle slot
  (maintenance, debug).
- **Do NOT bypass `prompts.render()`** — baking a second boot-prompt template in the autospawner creates drift from the
  manual spawn path.

---

## Relationship to related systems

| System                                       | Interaction                                                                                                                                        |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `harsh_pc_dispatch_failover`                 | Handles HOST down (heartbeat > 10 min silent). AutoSpawn handles WORKER down on running host. Different triggers, both required for full autonomy. |
| `agent_orchestrator_backlog_state_alignment` | Zombie cleanup prerequisite: without zombie cleanup, "queue not empty" fires on zombie rows and autospawn flaps.                                   |
| Manual `/api/slots/<id>/spawn`               | Same code path (`tmux_spawn.spawn` + `prompts.render`). AutoSpawn is a scheduled wrapper; manual API is on-demand.                                 |
| Account rotation dispatcher                  | Same `account_is_usable` source of truth. AutoSpawn's `_pick_headroom_account` adds the `five_hour_pct`/`weekly_pct` ceiling layer on top.         |
