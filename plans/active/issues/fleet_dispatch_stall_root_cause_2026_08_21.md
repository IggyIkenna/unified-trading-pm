---
doc_type: issue
title: >-
  Fleet dispatch stall + mid-task deaths share ONE upstream cause — the orchestrator
  restarts itself ~52x/day on its own commits, and every restart both mass-kills live
  workers and wipes the in-memory guard that suppresses unbootable accounts
summary: >-
  Operator report (2026-08-21, second of the day): "why are normal plan tasks not getting
  dispatched to fleet workers? we have slots available, plenty idle, account headroom on
  claude/gemini/codex/gemma/GLM, and plenty of unblocked ready tasks — also some agents are
  dying mid-task but not all of them." Measured live on the orchestrator VM (all numbers
  from `state.db` `activity_log` + `journalctl`, not inferred): 797 queued / 12-13
  dispatched, 24h `autospawn_failed` 244 vs `autospawn_succeeded` 258 (48.6% spawn failure
  rate), 243 dispatches converting to only 79 `slot_done` (32.5%), `boots_per_done` 3.44,
  362 `tmux_session_lost` in 24h. Neither premise the operator doubted was wrong — slots
  WERE idle and accounts DID have headroom; neither was the constraint. ROOT CAUSE:
  `ao-self-pull.sh` (root cron `*/2`) restarts `orchestrator.service` on EVERY
  agent-orchestrator LDR HEAD move, and the fleet ships its own agent-orchestrator commits
  to LDR — so the fleet restarts itself. 52 restarts on 2026-08-21, median ~14 min apart
  during active hours; 47 of that day's 79 AO commits (59%) touched only
  Dockerfile/scripts/tests, i.e. nothing the running uvicorn process has loaded. Two
  independent, separately-measured failure modes hang off each of those restarts, and
  together they explain both halves of the operator's report. (1) DISPATCH STALL:
  `_recent_spawn_failures`, the ring backing `_provider_health_ok`, is a module-level
  in-memory dict, so every restart wipes the suppression on structurally-broken accounts —
  four Gemini accounts registered in `accounts.json` have no credential env file on disk,
  carry a NULL usage row, and therefore sort FIRST in `_pick_headroom_account`'s
  `(five_hour, weekly, bound_slots)` ranking; 42 of 102 free-provider selections in a 2h
  sample (41%) went to an account that could not possibly boot. (2) MID-TASK DEATHS:
  `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` kills after
  `_IDLE_SESSION_RECLAIM_TICKS` ticks of "idle with a live session", but the counter was
  disk-persisted in 2026-08-18 so tick N-1 can be observed by a DEAD process and tick N by
  a fresh one — and a restart is exactly when every between-tasks worker looks idle at once,
  because their `/heartbeat` polls (the call that assigns a task and flips `idle -> working`)
  were refused during the gap. Every `idle_lingering_session_reclaim` burst in the 12h
  activity log landed 40-55s after a restart and none in between (49 reclaims; 7 slots in
  the 20:04 burst, 9 in the 20:16 one). Each kill SIGTERMs the pane and the slot must
  re-boot, which is the direct driver of `boots_per_done` — and it explains why the deaths
  hit some workers and not others, since only rows sitting at `idle`/`stale` at that instant
  are candidates while a worker mid-heartbeat at `working` is exempt. SCOPE LIMIT, measured
  rather than assumed: this chain fully accounts for the reclaim BURSTS and the
  capacity churn, but only PART of the mid-task task loss — 29 of 123 task-bearing
  `tmux_session_lost` events in a 14h window (24%) fall within 120s of a restart, so
  restart churn is a major contributing cause there, not the sole one; the larger
  unattributed population is tracked in
  `/plans/active/issues/fleet_wide_mid_task_death_root_cause_2026_08_21.md` and needs the
  kill-reason attribution fix listed below. Three further permanent-deadlock bugs found in
  the gate machinery while measuring, all fixed here. Five fixes shipped
  agent-orchestrator@32822b79d4.
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    dispatch-stall,
    autospawn,
    worker-liveness,
    restart-churn,
    auto-park,
    fleet-capacity,
    root-cause,
  ]
related:
  [
    /plans/active/issues/fleet_dispatch_stall_gemini_proxy_alias_mismatch_2026_08_21.md,
    /plans/active/issues/fleet_wide_mid_task_death_root_cause_2026_08_21.md,
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /plans/active/issues/backlog_durable_park_never_unparked_2026_08_21.md,
    /plans/active/issues/ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md,
    /plans/active/issues/autospawn_fleet_cap_headroom_throttling_routine_sla_miss_2026_08_09.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/15-runbooks/safe-service-restart-procedures.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.5
locked_by:
context_scope:
  [
    agent-orchestrator/scripts/ao-self-pull.sh,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/auto_park.py,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /plans/active/issues/fleet_wide_mid_task_death_root_cause_2026_08_21.md,
    /plans/active/issues/fleet_dispatch_stall_gemini_proxy_alias_mismatch_2026_08_21.md,
  ]
source:
  "slot-17, interactive session, 2026-08-21 — operator asked why normal plan tasks were not
  dispatching to fleet workers given idle slots, account headroom and unblocked ready tasks,
  and why some agents were dying mid-task while others were not"
---

# Fleet dispatch stall + mid-task deaths — one upstream cause

## The causal chain, in one picture

```
fleet ships an agent-orchestrator commit to LDR
   └─ ao-self-pull.sh (root cron */2) sees HEAD move → systemctl restart orchestrator
        │                                              52x on 2026-08-21 (~14 min apart)
        ├─ [A] in-memory _recent_spawn_failures ring wiped
        │       └─ credential-less accounts re-win _pick_headroom_account (NULL usage row
        │          ⇒ sorts first) → spawn hard-fails at the last step → budget burned,
        │          slot's spawn_retry_count bumped  ────────────────────►  DISPATCH STALL
        │
        └─ [B] fresh WorkerLivenessWatchdog, first tick at T+~45s
                └─ every between-tasks worker still reads `idle` (its /heartbeat was
                   refused during the gap) + disk-persisted tick counter already at N-1
                   → threshold trips on ONE post-restart tick → kill_session → SIGTERM
                   → tmux_pruner sees a dead pane holding a dispatched task → requeue
                                                              ────────────►  MID-TASK DEATHS
```

Both branches feed back into the top: a requeued task is re-dispatched, a burned spawn is
retried, and the resulting commits keep LDR moving. This is why the condition is *stable*
rather than self-correcting, and why raising the fleet cap or adding accounts never helped.

## What was measured (not inferred)

| Metric | Value | Source |
| --- | --- | --- |
| Queued / dispatched | 797 / 12-13 | `GET /api/backlog` |
| `autospawn_failed` vs `_succeeded` (24h) | 244 vs 258 — **48.6% failure** | `activity_log` |
| `task_dispatched` → `slot_done` (24h) | 243 → 79 — **32.5% conversion** | `activity_log` |
| `boots_per_done` | 3.44 (baseline 3.48, conversion 38.7% vs 47.3%) | `/api/fleet-kpis` |
| `tmux_session_lost` (24h / 7d) | 362 / 2172 | `activity_log` |
| Orchestrator restarts (2026-08-21) | **52** | `/var/log/ao-self-pull.log` |
| AO commits that day needing a restart | 32 of 79 — **47 (59%) did not** | `git log -- server/ pyproject.toml uv.lock` |
| `idle_lingering_session_reclaim` (12h) | 49, **100% within 40-55s of a restart** | `activity_log` × restart log |
| Spawn failures: missing credential env file | 90 of 244 (**37%**) | `activity_log.details_json` |
| Spawn failures: dirty-state quarantine | 63 of 244 (**26%**) | `activity_log.details_json` |
| `slot_done_rejected_dirty` (24h) | **262** vs 79 accepted `slot_done` | `activity_log` |

The restart↔kill correlation is the load-bearing measurement. Restarts at 16:40, 17:04,
17:20, 17:34, 17:40, 17:54, 18:08, 19:00, 19:12, 19:44, 20:04, 20:16 each have a reclaim
burst 40-55s later; the intervals between them have zero. That rules out the "slow tick /
git-lock stall batches the reclaims" hypothesis that the 2026-08-20 reordering fix in
`worker_liveness_watchdog.py` was written for — the watchdog demonstrably ticks in between
(`unpushed-sweep` lines at 20:10:50 and 20:14:10 in the same window).

### What this chain does NOT explain — stated so nobody over-reads it

The restart→reclaim correlation is 100% for the reclaim events themselves. It is NOT 100%
for mid-task task LOSS, and the difference matters:

| Population (14h window) | Count | Restart-adjacent (<=120s) |
| --- | --- | --- |
| `idle_lingering_session_reclaim` | 49 (12h) | **100%** |
| `tmux_session_lost` total | 269 | — |
| ...carrying a task (incl. escalation one-shots, `slot_id` null) | 123 | **29 (24%)** |
| ...with `resume_decision: requeue` | 39 | — |

So: restart churn is the whole story for the capacity churn (slots torn down and re-booted,
which is what `boots_per_done` 3.44 measures), and a major contributing cause of mid-task
loss — roughly double the by-chance rate — but not its sole cause. The remaining majority is
the already-tracked attribution problem: only ~5 of ~20 `kill_session` call sites emit an
activity event, so `kill_session(reason=...)` exists solely in a journal that retains ~1
hour. A same-session forensic pass put the resulting unattributed population at 285 of 728
deaths over 48h, 124 of them mid-task — that split is NOT independently re-verified here
(re-deriving it means re-implementing `tmux_pruner`'s classifier) and is cited as that pass's
figure, not this doc's. What IS verified here: 726 `tmux_session_lost` in 48h at a mean
14.8/hr, of which 178 (25%) fall inside a burst of >=3 distinct slots within any 60s window.
See the `kill_session(reason=...)` todo below and
`/plans/active/issues/fleet_wide_mid_task_death_root_cause_2026_08_21.md`.

Also ruled out by measurement, so nobody re-chases them: kernel OOM (279/279
`unexplained_death_forensics` rows report `oom_kill_suspected: false`; `dmesg` and
`journalctl -k` both empty; cgroup `oom_kill: 0`), disk pressure (`/` at 81%, 133G free),
tmux server death (1 event in 48h; `tmux_server_alive: true` on all 439 slot deaths that
recorded it), and `tmpfs-disk-cleanup` (a promising 19:40 coincidence, falsified by the
identical 20:10 sweep producing zero deaths).

## Fixes shipped (agent-orchestrator@32822b79d4)

1. **`scripts/ao-self-pull.sh` — restart-relevance gate.** Restart only when the FF actually
   moved `server/`, `config/`, `pyproject.toml` or `uv.lock`. `scripts/orchestrator.service`
   is deliberately excluded: `install-orchestrator-service.sh` already owns the unit file and
   restarts only when it genuinely applies a change. The stale-process self-heal now compares
   the process start time against the newest **restart-relevant** commit rather than plain
   HEAD — otherwise it would re-trigger, one tick later, every restart the gate just skipped.
   Fails safe (unknown sha / git error ⇒ restart). Expected effect: ~59% fewer restarts.
2. **`server/worker_liveness_watchdog.py` — post-restart observation grace.** An
   idle-lingering reclaim may not KILL until the current process has itself been watching for
   `interval x _IDLE_SESSION_RECLAIM_TICKS`. The counter still accumulates and still persists
   while held, so this defers a genuine reclaim by at most one grace window rather than
   resetting progress — irrelevant to the 15+ HOUR lingering sessions the 2026-08-18
   disk-backing fix was written for, which stays intact.
3. **`server/autospawn.py` — stateless credential pre-flight at SELECTION time.**
   `_account_credential_file_missing()` is checked in `_pick_headroom_account` and
   `_live_free_combo_ids` *before* the headroom check, because an unprovisioned account has a
   NULL usage row and therefore reads as maximum headroom. Scoped to DECLARED-but-absent
   only: an account with no `oauth_token_env_file` at all is left to `_do_spawn`'s existing
   guard, because that field means "unset / not applicable" across the codebase and the test
   corpus, and all four genuinely-broken live accounts declare a path (no registered account
   has a null value, so the narrowing costs nothing). Deliberately NOT added to
   `_account_meets_dispatch_headroom`, which is also the mid-session proactive-kill predicate:
   a running worker already has its env loaded, so a creds file vanishing under it is not a
   reason to kill live work. Stateless by design — an account self-heals into the pool the
   moment the env file appears, with no restart and no un-disable step to remember.
   **This closes the open `[BACKEND] P1` "mark an account unusable after a structural spawn
   failure" todo** in `/plans/active/issues/fleet_dispatch_stall_gemini_proxy_alias_mismatch_2026_08_21.md`,
   including the "confirm against the shipped code first" instruction it carried: confirmed —
   `account_is_usable()`/`capability_tier()` have no concept of a credential file, and
   `_do_spawn` is the only place that checks, at the very last step after the pick has already
   consumed a concurrent-spawn slot.
4. **`server/auto_park.py` — `unpark_task` now clears the DB condition.** `_prereqs_met` gates
   a park on BOTH the yaml prereq list and a DB-only backstop; `_park_task` sets both,
   `unpark_task` cleared only the yaml half. Every operator entry point (`/unpark`,
   `/park/redispatch`, `/park/mark-done`) therefore handed the task back into a still-False
   condition, and because `mark_unparked` also drops `parked_condition` the reconciler could
   never revisit it and both routes began 404-ing. A one-way door with 60 tasks in it (55 with
   the park as their SOLE blocker), aged up to 23.2 days, median 5.5 — and strictly monotonic,
   since `maybe_auto_park`'s self-repair only re-fires on a *further* decline, which requires
   the dispatch the park prevents.
5. **`server/dispatch.py` — a `cancelled` upstream satisfies a `completed_tasks` prereq.** The
   check was `row.status == "done"`, so a cancelled upstream (terminal — it can never become
   `done`) deadlocked its downstream permanently. The adjacent pruned-upstream branch already
   encodes exactly this judgement; the two now agree via `_TERMINAL_TASK_STATUSES`, pinned
   equal to `state_store.tasks._TERMINAL_STATUSES` by test.

Regression tests: `tests/test_watchdog_post_restart_reclaim_grace.py` (both directions — the
grace must hold a fresh process AND must not become a way to never reap),
`tests/test_autospawn_account_credential_preflight.py`, plus new cases in
`tests/test_auto_park.py` and `tests/test_dispatch_completed_prereqs.py`.

Worth noting for anyone auditing why a bug this simple survived: both halves of the park gate
WERE tested and the seam between them was not. The pre-existing `unpark_task` tests assert
`priority_override` and the yaml prereq list (both of which the buggy version got right), and
a separate test asserts the DB-only gate blocks/unblocks correctly — but it drives the
condition with a direct `set_prerequisite` rather than through `unpark_task`. The new test
asserts the end-to-end property instead: after `unpark_task`, `prereqs_met` is True.

## Corrections to sibling docs

- `/plans/active/issues/backlog_durable_park_never_unparked_2026_08_21.md` concluded "(b) does
  not apply — there is no auto-clearing setter for any of them to be buggy". That is wrong, and
  two observations it explained away are the fingerprints of fix 4 above: "10 of 12 show
  `priority_override: false`" is `unpark_task` having run, not backlog.yaml drift; "3 of 12 have
  no parked row" is `mark_unparked` having run, not a cooldown-row-keyed scan set. Its open
  todo-2 premise is therefore false. Corrected in that doc.
- `/plans/active/issues/fleet_wide_mid_task_death_root_cause_2026_08_21.md`'s open `[DOC] P3`
  asks whether mass-death bursts recur post-fix. They do — and this doc gives the cause. Its
  `[OPERATOR] P1` credential todo recorded the operator's explicit "defer for now" decision and
  disabled two of the four accounts; fix 3 makes that deferral free rather than costly, and
  covers all four (the two that were NOT disabled — `gemini-3-5-flash-lite-proj5` and
  `gemini-3-7-flash-proj4` — were still being selected and failing at 20:15 and 20:20 UTC).

## Still open

- [ ] [INFRA] P1. **Re-measure the fleet 24h after these fixes land** and record the delta on
      the five headline metrics (spawn-failure rate, dispatch→done conversion, `boots_per_done`,
      `tmux_session_lost`/day, restarts/day). The claim "this fixes the stall" is a hypothesis
      backed by root-cause analysis until that measurement exists; state the measured numbers,
      not "looks better". If restarts/day has not dropped by roughly the predicted 59%, the
      relevance gate's path set is wrong and needs widening — check what the remaining restarts
      cite in `/var/log/ao-self-pull.log`.
      HOW TO MEASURE (the ad-hoc scripts this session used lived in a tmpfs scratchpad and were
      reaped — this is the recipe so nobody re-derives it). All five come from two durable
      sources; `journalctl -u orchestrator` is NOT one of them, it retains only ~1h here.
      `sqlite3 "file:agent-orchestrator/data/state/state.db?mode=ro"` then
      `SELECT event_type, count(*) FROM activity_log WHERE ts > datetime('now','-24 hours')
      GROUP BY event_type` — spawn-failure rate is `autospawn_failed` vs `autospawn_succeeded`,
      conversion is `task_dispatched` vs `slot_done`, deaths are `tmux_session_lost`; and
      `grep -c 'restarting orchestrator' /var/log/ao-self-pull.log` (filtered by date) for
      restarts/day. `boots_per_done` reads straight off `GET /api/fleet-kpis`. The pre-fix
      baseline to compare against is the measurement table above.
- [ ] [BACKEND] P1. **Role/reserve partitioning starves two craft roles to one usable slot
      each.** Deriving each queued task's `assigned_role` from its `craft_role` block list: infra
      110 tasks, data_engineering 108, backend_engineer 106. Against live slot roles, `infra` has
      5 slots — one paused, two in `scheduled_reserve`, one in `ci_escalation_reserve` — leaving
      **1 usable for 110 tasks**; `data_engineering` has 3, of which one IS the review slot and
      one is scheduled-reserved, leaving **1 for 108**. 62% of the 352 capacity-wait tasks had
      ZERO genuinely-idle non-reserved eligible slots at sample time. Reserves are selected by
      highest slot id (`config.ci_escalation_reserved_slot_ids` / `scheduled_task_reserved_slot_ids`),
      which is role-blind — it happened to capture 3 of 5 infra slots. Make reserve selection
      role-aware, or refuse to reserve the last slot of any craft role.
- [ ] [BACKEND] P2. **`explain_blocked` reports slots that can never run anything as "eligible".**
      `_explain_blocked_with_ctx` (`dispatch.py`) iterates every `SlotRow` in `ctx.slot_models`,
      so all 14 human presence slots (9001, 9002, 91002-91006, 92005, 92024-92029 — no worktree,
      so `slot_is_spawnable` is permanently False) plus paused/killed/stale slots appear in the
      "eligible on slot(s) [...]" list on all 352 capacity-wait tasks. The trailing "— waiting for
      one to go idle" is a hardcoded string that never checks idleness. This is diagnostics
      actively misleading the reader: it is why the queue looks like it has capacity waiting for
      it. Iterate dispatchable AO slots only, and say "no idle eligible slot" when that is the
      truth.
- [ ] [BACKEND] P2. **262 `slot_done_rejected_dirty` in 24h against 79 accepted `slot_done`.**
      Workers complete real work, call `/done`, and are rejected because their tree is dirty — the
      task returns to the queue and the whole dispatch is re-spent. That ratio makes it the single
      largest throughput sink after the churn loop. Determine whether the dirty files are the
      worker's own un-shipped output (a worker-discipline bug) or foreign/generated litter it
      never touched (a gate bug), and fix whichever it is. `restored_generated` is already in the
      event payload and should discriminate the two.
- [ ] [INFRA] P2. **Stray nested repo directories permanently quarantine their slot.** Four
      leftover working copies inside slot checkouts — `.tabs/5/.qg-old-4YMi23`,
      `.tabs/11/pm-fix`, `.tabs/16/oms-wt.oc3YkB`, `.tabs/23/unified-trading-pm-current` — are
      treated as repos by the dirty-state preserver, which then refuses to spawn over them
      ("refused: HEAD already 1 commit(s) ahead of origin ... age < 900s guard", and for slot 23
      genuine conflict markers in two issue docs). Slots 5, 11, 16 and 23 all failed to spawn in
      the single 20:20:27 tick for this reason. Decide the disposition of each (they contain
      uncommitted work — do NOT blind-delete), then make the preserver ignore directories that
      are not in `workspace-manifest.json` so a stray copy cannot take a slot out of the fleet.
- [ ] [INFRA] P2. **`ORCHESTRATOR_WORKER_MEMORY_MAX=10G` is set but not applied.** Every spawn
      logs `systemd-run --user unavailable — spawning worker UNCAPPED` (26 occurrences in one
      hour). The host shows cgroup `memory.high` throttling active (counter 613,421) with 6 GB of
      swap in use at load 12/16 cores, so the cap is doing nothing while the pressure it exists to
      bound is real. Either enable lingering for the `ubuntu` user (`loginctl enable-linger`) so
      `systemd-run --user` works, or move the cap to a mechanism that does.
- [ ] [INFRA] P2. **The orchestrator journal retains ~1 hour.** `/var/log/journal` is absent, so
      journald is volatile, and AO logs every HTTP request at INFO — flooding its own journal.
      `SESSION-TEARDOWN ... reason=` is the single most diagnostic line for a worker death and is
      unrecoverable past ~60 minutes; three separate investigations have now each had to
      re-derive fleet history from `activity_log` because of this. Enable persistent journald
      storage and drop uvicorn access logging to WARNING.
- [ ] [BACKEND] P2. **`kill_session(reason=...)` never reaches the DB.** Only ~5 of ~20
      `kill_session` call sites emit an activity event, so the reason string exists solely in the
      volatile journal above; 285 of 728 slot deaths over 48h classified as "unexplained"
      (124 of them mid-task) purely for want of that attribution. Persist the reason on every
      call site.
- [ ] [BACKEND] P3. **`escalation_dispatch_failed`: 431 of 602 (72%) are one config error** —
      `server_url unresolved: server_url() resolved to the PRODUCTION default
      ('http://localhost:8765') on a standalone instance (vm_id='', ORCHESTRATOR_STANDALONE...)`.
      Separate from this doc's chain but the largest single failure class in that queue.
- [ ] [OPERATOR] P3. **35 queued tasks are gated behind 11 `status: draft` upstream plans.**
      `_upstream_plan_open_on_disk` correctly treats a draft as unconditionally open (a draft is
      never ingested, so it can emit no tasks), which means these can only ever clear by a human
      flipping `status: draft` → `active`. Decide per plan: flip, or drop the dependency. List:
      `sports_satellite_ao_dispatch_batch14_2026_08_16` (11 downstream),
      `tradfi_satellite_ao_dispatch_batch19_2026_08_19` (3),
      `prediction_satellite_ao_dispatch_batch14_2026_08_19` (3),
      `prediction_satellite_ao_dispatch_batch15_2026_08_19` (3),
      `defi_satellite_ao_dispatch_batch14_2026_08_16` (3),
      `cefi_satellite_ao_dispatch_batch22_2026_08_19` (3),
      `defi_satellite_ao_dispatch_batch18_2026_08_19` (2),
      `cross_cutting_satellite_ao_dispatch_batch19_2026_08_19` (2),
      `cross_cutting_satellite_ao_dispatch_batch20_2026_08_19` (2),
      `tradfi_satellite_ao_dispatch_batch9_2026_08_16` (2),
      `defi_instruments_store_v9_gate_c_apply_write_2026_08_16` (1).
- [ ] [OPERATOR] P3. **Six named prerequisites gate tasks with nothing that can ever set them** —
      `registry_drift_run_observable`, `repo_scripts_governance_audit_phase1_landed`,
      `cve-remediation-005-scope-decision`, `defi-mvp-backfill-full-coverage`,
      `cefi_content_migration_fleet_44_complete`, `tardis-vm-slot-free-cefi-forward-poll`. None
      appears anywhere in the plan corpus and no code sets any of them. Either document what
      clears each, or `POST /api/prerequisites/{name} {"value": true}` and drop it.
- [x] [INFRA] P1. **An interactive session working in an AO-managed slot gets its WIP harvested
      mid-session.** Hit live while writing this doc: every uncommitted change in slot 17 — 11
      agent-orchestrator files and 8 unified-trading-pm files — was committed away and both
      checkouts reset to `origin/live-defi-rollout` at 21:04:05Z. Nothing was lost — that is the
      design working: the commits were pushed to `wip-preserve/orchestrator-slot-17-87b29a6d`
      (AO) and `wip-preserve/orchestrator-slot-17-aeb2d92a88` (PM), and `git cherry-pick
      --no-commit <sha>` restored both trees with zero conflicts.
      — **DONE 2026-08-21, `agent-orchestrator@3cfd9bcfb8`. The operator answered the decision this
      todo was holding: slot 17 was ALREADY `paused`, and a paused slot must not be touched by AO
      at all.** Slots are paused for exactly two reasons — an interactive debugging session, or a
      capacity restriction — and both mean hands off. That is a cleaner rule than any of the three
      options sketched here: it needs no `.agent-claim` (so it costs no fleet capacity, unlike
      option (a)), no mtime heuristic (option (b)), and no reserved slot range (option (c)).
      ROOT CAUSE, once the premise was checked: the dispatch side already honoured `paused`
      (`slot_is_spawnable`, `escalation`, `stale_dispatch`, `tmux_pruner`,
      `worker_liveness._respawn` — 8 call sites), but the three worktree-MUTATING sweeps in
      `worker_liveness_watchdog` each ran a bare `select(SlotRow)` with no status filter and gated
      only on *"does this slot have a live tmux session?"* — which a paused slot never has, making
      it indistinguishable from an abandoned dirty slot.
      FIX: one predicate `dispatch.slot_is_operator_paused()` (+ `OPERATOR_PAUSED_STATUS`, which
      `slot_is_spawnable` now also uses so there is a single definition), applied via a shared
      SQL-filtered `worker_liveness_watchdog._worktree_maintenance_slots()` in all three sweeps
      (`_sweep_dirty_slots`, `_flag_orphaned_sibling_dirty_repos`, `_sweep_unpushed_slots`), plus
      guards on `_preserve_wip_before_kill` and `server._commit_slot_wip_before_rotation` (the two
      paths that stash / reset-after-preserve). Filtered in the QUERY rather than by a per-row
      `continue` so a fourth sweep cannot silently forget it.
      Test: `tests/test_paused_slot_worktree_immunity.py` — the predicate truth table, the shared
      helper, all three sweeps, the pre-kill stash, a regression guard that `slot_is_spawnable`
      still excludes paused, and a SOURCE-level check that fails the moment any sweep re-introduces
      a bare `select(SlotRow)`. Each behavioural test also asserts the ordinary slot IS still swept,
      so this can never degrade into a blanket disable.
      Recovery recipe written into `/codex/05-infrastructure/per-tab-worktrees.md` § FM9 as this
      todo asked.
      ACCEPTED TRADE-OFF, recorded so it is not rediscovered as a bug: genuinely-abandoned WIP in a
      slot that is THEN paused stays un-preserved until the slot is unpaused.
- [ ] [INFRA] P2. **The same slot reset also deleted the repo `.venv`**, so the next
      `quality-gates.sh` aborted with "no usable .venv/bin/python" and needed a full `uv sync`
      before it could gate anything. Same class as the already-open
      `/plans/active/issues/vm_disk_guard_wipes_active_slot_venvs_2026_08_20.md` — recording a
      fresh 2026-08-21 occurrence rather than re-diagnosing it.
- [ ] [INFRA] P2. **Extend the operator-paused exemption to `agent-orchestrator/scripts/vm-disk-guard.sh`.**
      The paused-slot rule shipped in `agent-orchestrator@3cfd9bcfb8` covers AO's Python
      worktree sweeps; the disk guard is a separate shell script that reclaims
      `.tabs/<N>/*/.venv` and decides "idle" with the SAME flawed liveness proxy the sweeps
      used — "does an `orch-slot-<N>` tmux session exist". A paused slot never has one, so an
      operator's interactive slot is judged idle and its venv swept mid-session; it wiped slot
      17's venv twice on 2026-08-21, each time costing a full `uv sync` before
      `quality-gates.sh` could run at all. The live script (203 lines) HAS been hardened since
      its own issue doc was written — it now also checks `slot_has_live_process` and
      `_slot_venv_in_use` (argv/CWD referencing the slot path) — but neither caught a VS Code
      interactive session, and neither knows about `paused`. Fix: read paused slot ids from
      `data/state/state.db` and skip them, mirroring `dispatch.slot_is_operator_paused`. Track
      the GENERAL bug (its idle test matches every slot on this VM, so every venv is swept) in
      its own doc — this todo is only the paused-slot half.
- [ ] [DOC] P3. **`ORCHESTRATOR_FLEET_WORKER_CAP=40` is inert.** Every tick logs
      `configured=40 CLAMPED to 25 by slot arithmetic (configured_slots=32 - reserve=7
      [ci=3 + scheduled=4])`. The clamp is by design and already logged loudly, but the live
      `.env.local` still carries a number that has no effect, which is a trap for the next
      operator. Set it to the real ceiling or delete the override.

## Deferred work after 2026-08-21

| Item | State / why deferred | Blocked on |
| --- | --- | --- |
| Re-measure the fleet 24h after the fixes (`[INFRA] P1` above) | **Cannot be done yet** — needs elapsed time; the fixes went live 22:20Z and 4-min-old signals are not evidence | wall-clock only |
| Role/reserve starvation: 1 usable slot for 110 infra + 1 for 108 data_engineering tasks (`[BACKEND] P1`) | **Not done** — the largest remaining throughput lever; reserve selection is by highest slot id and is role-blind | nobody; pick this up next |
| `vm-disk-guard.sh` paused-slot exemption (`[INFRA] P2`) | **Not done** — small, same rule as the shipped fix, needs its own gate run | nobody |
| `explain_blocked` lists 14 phantom human slots as "eligible" (`[BACKEND] P2`) | **Not done** — diagnostics honesty, no behaviour change | nobody |
| 262 `slot_done_rejected_dirty`/24h vs 79 accepted (`[BACKEND] P2`) | **Not done** — needs the dirty-files-provenance split (worker's own output vs foreign litter) before a fix is choosable | nobody |
| Stray nested repos quarantining slots 5/11/16/23 (`[INFRA] P2`) | **Operator-owned** — the dirs hold uncommitted work; disposition is a human call, do NOT blind-delete | operator |
| 35 tasks behind 11 `status: draft` upstream plans (`[OPERATOR] P3`) | **Operator-owned** — only a human `draft`→`active` flip can clear these | operator |
| 6 named prerequisites nothing can ever set (`[OPERATOR] P3`) | **Operator-owned** — needs a ruling on what clears each | operator |
| Interactive-session-in-an-AO-slot hazard (`[INFRA] P1`) | **DONE** this session — operator ruled paused = hands off; shipped `agent-orchestrator@3cfd9bcfb8` | — |

**Recommended NEXT item: the role/reserve starvation `[BACKEND] P1`.** Everything else on this
list is either waiting on the clock, operator-owned, or diagnostics. That one is the binding
constraint on throughput now that the churn loop is broken — 62% of capacity-waiting tasks had
ZERO idle, non-reserved, role-matching slots at sample time, and reserving by highest slot id
happened to capture 3 of the 5 infra slots.

## Progress Log

**2026-08-21 (interactive session, slot 17)** — Operator asked for the root cause of normal
plan tasks not dispatching, plus the mid-task deaths, "check the flow end-to-end". Mapped the
full dispatch path (plan markdown → `PlanRegenLoop` → `backlog.yaml` → `sync_backlog_to_db` →
the SUPPLY side `AutoSpawnLoop` and the DEMAND side `pick_next_task`, which runs inside the
worker's own `/boot`|`/heartbeat` request — dispatch is PULL-based; nothing pushes to an idle
slot). Five parallel read-only investigations converged independently on the restart-churn
loop. Key measurement that settled it: every `idle_lingering_session_reclaim` burst in a 12h
window lands 40-55s after an `ao-self-pull.sh` restart and none in between.

Two of my own intermediate numbers were wrong and are corrected here: an early
"24h" `journalctl` grep actually covered only the ~1h the volatile journal retains, and
`tmux_session_lost`/`OOM`/`Killed` counts from that grep were matching the `/api/activity`
query string in access-log lines rather than real events. All figures in this doc come from
`activity_log` in `state.db`, which is durable. Kernel OOM was checked and ruled out
(279/279 `unexplained_death_forensics` rows report `oom_kill_suspected: false`; `dmesg` and
`journalctl -k` both empty) — every death with a readable pane tail was SIGTERM (143) or
SIGKILL from AO's own `kill_session`.

**2026-08-22 (`/ao-watchdog` scheduled run, slot 29) — partial answer to the "still open" P1
re-measure todo above.** Not a full five-metric re-measurement (spawn-failure rate and
`tmux_session_lost`/day were not re-pulled this run — `GET /api/activity` with a `types=`/`since=`
filter is a known-flaky route per this skill's own Step 10 notes, not attempted here to keep this
run bounded), but two of the five headline metrics were measured directly and both confirm the fix
held:

- **Restarts/day, from `/var/log/ao-self-pull.log` directly (exact grep, `orchestrator restarted`
  vs `NOT restarting`, not a substring guess)**: 2026-08-20 (full day, entirely pre-fix baseline) =
  **80 restarts, 0 skips**. 2026-08-21 (mixed day — the restart-relevance gate's first "NOT
  restarting" skip line is timestamped `22:34:00Z`, i.e. the gate was only live for the day's last
  ~1.5h) = 59 restarts, 2 skips in that window. 2026-08-22 (fully post-fix, ~2h sampled so far) =
  **0 restarts, 4 of 4 relevant fast-forwards correctly skipped**. Small post-fix sample, but
  directionally this beats the doc's own predicted "~59% fewer restarts" — every relevant-check
  since the gate went fully live has been a correct skip.
- **`GET /api/fleet-kpis?window_hours=24`'s own `current` vs `baseline` halves** (this is "yesterday
  vs the day before" in that route's now-anchored sense, not calendar-day, but it brackets the same
  transition): `baseline` (pre-window) boots=543, dispatches=313, done=119, conversion_pct=38.0,
  boots_per_done=4.56, boots_to_dispatch_ratio=1.73 → `current` (last 24h) boots=262 (-51.8%),
  dispatches=217 (-30.7%), done=105 (-11.8%), conversion_pct=48.4 (+10.4pp), boots_per_done=2.5
  (-45.2%), boots_to_dispatch_ratio=1.21 (-30.1%). `regression_alert` was `null` (no regression, and
  this delta is the opposite direction — an improvement past the 5x-regression trigger's threshold
  would never fire on a get-better move anyway, noted so nobody misreads the null as "nothing
  happened").

Still outstanding from the original todo: spawn-failure rate and `tmux_session_lost`/day were not
re-measured this run — a future pass (this skill's next daily run, or a manual check) should pull
those two via `activity_log` (`autospawn_failed`/`autospawn_succeeded`, `tmux_session_lost` counts)
to complete the five-metric set. Also, while checking the fleet for this run,
`ao_dispatch_skew_root_cause_and_session_cleanup_2026_08_21.md`'s D30-ruling todo (re-disable both
`gemini-3-5-flash-lite-proj4` and `gemini-3-7-flash-proj4`) was found only half-applied —
`gemini-3-7-flash-proj4` was still `healthy`, disabled this run (see that doc's Progress Log/todo
for detail) — unrelated to this doc's own chain, noted here only because it was found in the same
pass.
