---
doc_type: codex-ssot
title: Agent Orchestrator — AutoSpawn Architecture
summary:
  AutoSpawnLoop — orchestrator background thread that wakes a worker on an idle slot when all 5 gates pass (queue
  CLAIMABLE (not merely queued — R1 2026-07-16), no active worker, account headroom <95%, slot configured, not in
  cooldown); per-slot spawn params from _spawn_param_plan (R2); model-tier-aware opus routing, anti-flap 1h backoff +
  Slack alert.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [orchestrator, self-healing, role-registry, model-tier, slack, infrastructure]
related:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
  ]
created: 2026-05-30
authoritative_for: [agent-orchestrator AutoSpawn worker-spawn architecture]
referenced_by:
  [
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    plans/audit/instructions/orchestrator_master_audit_instructions.md,
  ]
owner:
last_reviewed: 2026-07-16
code_refs:
---

# Agent Orchestrator — AutoSpawn Architecture

> **SSOT**: `agent-orchestrator/server/autospawn.py` **Plan**: `plans/active/autospawn_idle_vms_2026_05_30.md`
> **Overview pointer**: `/codex/04-architecture/agent-orchestrator-overview.md` § "Auto-spawn lifecycle"

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

> **Gate 1 is CLAIMABLE, not merely queued (R1, 2026-07-16).** The table above describes the raw SQL shape; the live
> gate asks whether a queued task is claimable by **any** worker slot — see § Spawn budget below. A queue of
> un-claimable tasks reads as `queue_empty` for spawn purposes and correctly spawns nothing.

---

## Spawn budget — count work a slot can actually CLAIM (R1, 2026-07-16)

**One claimable task warrants one spawn.** The budget is `len(dispatch.claimable_queued_task_ids(...))`
(`autospawn._queued_undispatched_count` delegates to it), then capped by the fleet-worker headroom.

**The rule that matters:** the budget and the dispatcher MUST answer the same question from the same place. They did
not, and it cost the fleet its throughput. AutoSpawn applied 2 filters (queued+undispatched, prereqs-met) while
`pick_next_task` applied 9, so the budget counted work dispatch would immediately reject. Every phantom bought a spawn:
the worker booted on a real account, was handed nothing, parked, and the watchdog reaped it. Measured over 24h before
the fix: **~1014 autospawns / 1184 boots / 954 worker-deaths → 217 dispatches / 101 tasks done**, with the spawn budget
at 6 against 1 genuinely-claimable task.

Both consumers now derive from one filter table (`dispatch._FILTERS`), each row declaring a `FilterScope`:

| Scope        | Meaning                                                                                  | `pick_next_task` | Spawn budget                  |
| ------------ | ---------------------------------------------------------------------------------------- | ---------------- | ----------------------------- |
| `FLEET`      | same answer for every slot (prereqs, DEFER brief, repo/collision)                        | must pass        | must pass                     |
| `SLOT`       | varies by slot; AutoSpawn **cannot** change it (`slot_skips`, affinity pin, review slot) | must pass        | passes if **any** slot passes |
| `CAPABILITY` | varies by slot; AutoSpawn **can spawn one that passes** (model tier, craft role)         | must pass        | **ignored**                   |

**`CAPABILITY` is the subtle one — do not "simplify" it away.** Filtering model tier or craft role into the budget looks
symmetric and starves the fleet: an opus task is not un-claimable because every live slot is sonnet — the next spawn can
BE opus. Zeroing the budget means the opus/infra worker never spawns and the task waits forever, which is worse than the
over-count R1 fixed; for craft role it reintroduces the exact starvation `agent-orchestrator@8a423bb` fixed. Guarded by
`tests/test_dispatch_filter_table.py`; `_Filter.scope` has no default, so a new rule cannot be added without classifying
it.

**Add an eligibility rule to `_FILTERS`, never as an inline check in a caller** — that asymmetry IS how R1 happened.

---

## Slot candidate ordering — round-robin fairness (2026-07-25)

**Which slots the budget's spawn attempts LAND on is a separate question from how big the budget is** (the section
above). `_run_one_tick` orders candidate `SlotRow`s via `select(SlotRow).order_by(SlotRow.slot_id)` then stable-sorts by
a tuple `(recent_failure_count, last_attempt_at)` — failure-count first (doomed slots go to the back, unchanged since
`ao_task_lifecycle` Phase C 2026-07-09), then **least-recently-ATTEMPTED** (never-attempted sorts first via an epoch
sentinel).

**Why the second key matters**: with only the failure-count key, slots tied at zero failures kept the raw ascending
`slot_id` order from the ORM query. Combined with `fleet_worker_cap()` (`ORCHESTRATOR_FLEET_WORKER_CAP`, 8 on the
planning VM) and the budget-exhaustion early-skip (`if len(to_spawn) >= spawn_budget: continue` — fires BEFORE
`_should_spawn`, so a skipped slot gets no `autospawn_failed`/`autospawn_succeeded` activity row at all, not even a skip
reason), this permanently favored low-numbered slots whenever fleet-wide demand kept refilling headroom before the scan
reached the tail. Live-confirmed: slots 13/14/15 measured ZERO AutoSpawn activity for 378min-27168min while
lower-numbered slots cycled continuously (`plans/archive/2026_07/ao_fleet_throughput_incident_2026_07_25.md` todo 2).
Fixed in `agent-orchestrator@18d8538` — `self._last_attempt_at` (already tracked for the cooldown gate) now also drives
the tie-break, so a chronically at-cap fleet rotates through every idle slot instead of starving the tail forever.
Regression: `tests/test_autospawn.py::test_tick_rotates_through_idle_slots_when_chronically_at_cap`.

**This does NOT change the fleet cap itself** — `fleet_worker_cap()` still bounds how many slots run AT ONCE (an
intentional, documented ceiling); the fix only changes WHICH idle slots take turns filling that ceiling. A slot with
genuinely no claimable task in the current queue (a `SLOT`/`CAPABILITY`-scope filter rejection, see above) still won't
spawn regardless of ordering — fairness only applies among slots that are otherwise equally eligible.

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

## Model-tier-aware dispatch (opus-required routing — 2026-06-29)

A plan's `model_tier: opus-required` (regen → `BacklogTask.model`) must reach an **Opus** worker. Before 2026-06-29 it
didn't: a slot spawned **Sonnet** (the tick's top-task model) could be handed an opus-required task, and the worker's
SSOT self-check would STOP ("Sonnet on opus-required" — CLAUDE.md HARD RULE) and **wedge the slot for an operator**.
Symptom: opus-required plans block slot after slot, no Opus worker ever appears, even with idle capacity. Four
mechanisms now route the model end-to-end (`server/autospawn.py` + `server/dispatch.py`):

1. **PER-SLOT spawn params — `_spawn_param_plan` (R2, 2026-07-16; was `_top_queued_task_params`, now DELETED).** The
   plan yields one `(model, effort, thinking, role)` entry per CLAIMABLE task — same
   `dispatch.claimable_queued_task_ids` SSOT the budget counts, so the plan and the budget cannot disagree about what is
   servable — ordered starved-role-first then by dispatch's own tie-break `(tier, priority, plan_order, plan_ref)`. The
   i-th slot spawned this tick takes the i-th entry, so the fleet comes up sized and crafted as the queue actually asks.
   **Until 2026-07-16 the tick resolved ONE tuple and booted every slot at it** — a limitation the code documented in a
   docstring and never fixed: 1 opus P0 above 29 sonnet tasks made every worker in the tick opus (burning opus quota on
   work the plans intended to run cheap), and a mixed-ROLE queue booted everyone at the top task's craft, so the
   dispatch role-gate stranded every other role behind a fleet that could not claim it. `assigned_role` now travels
   per-slot through `to_spawn`; it used to be one tick-wide value closed over by the slow section, which is what made
   the craft uniform.
2. **Per-slot UPGRADE — `_slot_required_model`.** Before spawning slot N, scan its `current_task` PLUS any QUEUED
   **affinity-high** task TARGETING slot N (prereqs met); if the highest such task outranks that slot's PLAN model,
   spawn slot N at that task's tier. Covers a task returned to the queue via `/reassign` — `current_task` is cleared but
   `target_slot` + `affinity=high` remain — so the sole eligible runner doesn't respawn Sonnet and starve. Runs AFTER
   the plan pick, so a pinned slot still outranks its plan entry.
3. **Dispatch model-tier gate — `dispatch.pick_next_task` (`_task_outranks_slot`).** A slot never CLAIMS a task whose
   model outranks its own. Opus tasks stay queued for an Opus spawn; because Sonnet slots never claim them, they are
   never plan-claim-pinned to a Sonnet slot → no affinity deadlock.
4. **Upgrade-only — `_higher_model`.** All model selection UPGRADES (opus > sonnet > haiku); never downgrades a slot
   below the tick model.

Together these close every path — fresh-spawn AND live-handoff — so opus-required work routes to Opus workers and never
wedges a Sonnet slot. **Verified live 2026-06-29**: an autospawned Opus slot picked up and executed an opus-required
task (`mdps_polars_engine_cost_sharpening`). Commits: dispatch gate `agent-orchestrator@c627276`; prereq-aware +
affinity upgrade `@5929815` (extends the original spawn-time pinned upgrade). Tests:
`tests/test_dispatch_model_gate.py`, `tests/test_autospawn.py::test_*model*`/`*pinned*`/`*required*`. Cross-refs:
`unified-trading-pm/agents/<role>.md` (per-role `model` frontmatter defaults),
`/codex/06-coding-standards/model-tier-selection.md` (the tier SSOT).

**Quota note.** Opus is genuinely available (Max-20 accounts carry Opus headroom; there is **no** opus-budget guard in
code), but Opus burns the weekly quota faster — so `opus-required` is rightly reserved for cross-repo/schema work, and
only the slots pinned to opus tasks upgrade (the rest stay Sonnet).

**Known follow-up (NOT yet fixed).** The pinned-slot UPGRADE only fires when `_should_spawn` actually (re)spawns the
target slot. A live-but-idle Sonnet slot that is an opus task's affinity target is not killed by autospawn, so it won't
self-upgrade until it goes idle/dead and respawns. If opus tasks linger queued with no Opus slot appearing despite
headroom, the suspect is `_should_spawn` not reviving the specific pinned slot — a clean follow-up, not more live
hot-patching.

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

Enable on the central orchestrator VM (id `planning`) via systemd drop-in:

```ini
# /etc/systemd/system/orchestrator.service.d/autospawn.conf
[Service]
Environment=ORCHESTRATOR_AUTOSPAWN_ENABLED=true
```

Rollout script: `unified-trading-pm/scripts/orchestrator/enable_autospawn.sh` (single central VM since 2026-06-27; the
`run_fleet_enable_autospawn.sh` multi-VM sequencer is a multi-VM-era holdover, unused on single-VM).

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
