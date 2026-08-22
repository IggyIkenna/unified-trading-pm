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
  agent-orchestrator@32822b79d4. FOLLOW-UP 2026-08-22: the role/reserve-starvation lead was
  FALSIFIED by re-measurement with AO's own dispatch predicates (0 of 349 capacity-waiting
  tasks lack an eligible slot; the original figure ignored generic slots, which accept every
  role), and the real remaining blocker was found on the SUPPLY side — every walk in
  `worktree_clean_check` treated any git-shaped directory under a slot as one of its repos,
  so ship-script leftover worktrees and history-rewrite backup clones, whose 190-231
  uncommittable conflict-marker files the FM9 guard correctly refuses, quarantined whole
  slots permanently with no self-heal: 239 of 355 autospawn failures (67%) and 104 of 141
  escalation-dispatch failures (74%) in 24h, across 10 slots. Fixed by a single enumerator
  plus an operator-paused exemption for `vm-disk-guard.sh`, agent-orchestrator@7f0887d4f9.
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
last_updated: "2026-08-22"
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
- [x] [BACKEND] P1. **Role/reserve starvation — FALSIFIED by re-measurement, closed 2026-08-22.**
      The original claim (infra "1 usable slot for 110 tasks"; 62% of capacity-waiting tasks with
      zero eligible slot) counted only slots whose `slot_role` EQUALS the task's role.
      `dispatch._blocks_craft_role` also passes every slot whose `slot_role` is UNSET, so the 11
      generic slots are universal donors and were all missed. Re-measured with AO's own
      predicates (`first_blocking_filter` over all 349 capacity-waiting tasks, consistent DB
      snapshot): **tasks with zero eligible slot = 0**, and dropping BOTH reserves frees **0**
      more. `slots_with_claimable_task` = 21 of 29 spawnable. The reserve is not a throughput
      constraint; no change needed. Recipe + the two traps (run from the DEPLOYED checkout;
      snapshot via `sqlite3 .backup`): `/home/ubuntu/.ao-measure-slot17/measure_reserve_starvation.py`.
- [ ] [BACKEND] P2. **`explain_blocked` reports slots that can never run anything as "eligible".**
      `_explain_blocked_with_ctx` (`dispatch.py`) iterates every `SlotRow` in `ctx.slot_models`,
      so all 14 human presence slots (9001, 9002, 91002-91006, 92005, 92024-92029 — no worktree,
      so `slot_is_spawnable` is permanently False) plus paused/killed/stale slots appear in the
      "eligible on slot(s) [...]" list on all 352 capacity-wait tasks. The trailing "— waiting for
      one to go idle" is a hardcoded string that never checks idleness. This is diagnostics
      actively misleading the reader: it is why the queue looks like it has capacity waiting for
      it. Iterate dispatchable AO slots only, and say "no idle eligible slot" when that is the
      truth.
- [ ] [BACKEND] P2. **`slot_done_rejected_dirty` — RE-MEASURE FIRST; the 24h count fell to 60
      against 81 accepted `slot_done_verified` (2026-08-22), from the 262-vs-79 first recorded.**
      Workers complete real work, call `/done`, and are rejected because their tree is dirty — the
      task returns to the queue and the whole dispatch is re-spent. That ratio makes it the single
      largest throughput sink after the churn loop. Determine whether the dirty files are the
      worker's own un-shipped output (a worker-discipline bug) or foreign/generated litter it
      never touched (a gate bug), and fix whichever it is. `restored_generated` is already in the
      event payload and should discriminate the two.
- [x] [INFRA] P2. **Stray git dirs permanently quarantine their slot — FIXED. This, not the
      reserve, was the dominant live blocker.** All four walks in `worktree_clean_check`
      hand-rolled `slot_dir.iterdir()` + `(child/".git").exists()`, so ANY git-shaped directory
      under a slot counted as one of its repos: ship-script leftover worktrees (`pm-fix`,
      `pm-ship.MpuQMt`, `oms-wt.oc3YkB`, `unified-trading-pm-current`) and
      `*.stale-pre-history-rewrite-*` backup clones. Each carries 190-231 uncommittable dirty
      files; the FM9 conflict-marker guard correctly refuses them; `resolve_dirty_state` then
      quarantines the WHOLE slot — with no self-heal, so permanently. Measured over the 24h to
      2026-08-22T06:05Z: **239 of 355 autospawn failures (67%) and 104 of 141
      escalation-dispatch failures (74%)** were `dirty-state quarantined`, spanning 10 slots;
      slot 11 alone failed 54 times. Fixed with one enumerator, `classify_slot_dirs`, that every
      walk routes through — a stray lands on `SlotCleanReport.stray_repos` and never enters
      `dirty_repos`. Nothing is deleted or committed: the strays' files are untouched, they just
      stop being mistaken for the slot's own WIP, so no preservation capability is lost (these
      repos were already un-preservable — that is what wedged the slot). Disposition of their
      CONTENT remains operator-owned. — `agent-orchestrator@7f0887d4f9` +
      `tests/test_stray_repo_never_quarantines_slot.py` (source-level guard included)
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
- [x] [INFRA] P2. **The same slot reset also deleted the repo `.venv`** — the gate aborts with
      "no usable .venv/bin/python" and needs a full `uv sync` first. Recurred twice more on
      2026-08-22; root cause fixed by the paused-slot exemption above. General case stays in
      `/plans/active/issues/vm_disk_guard_wipes_active_slot_venvs_2026_08_20.md`.
- [x] [INFRA] P2. **Operator-paused exemption extended to `scripts/vm-disk-guard.sh` — DONE
      2026-08-22.** The guard's three keep-signals (`orch-slot-<N>` tmux session,
      `slot_has_live_process`, `_slot_venv_in_use`) are all INSTANTANEOUS — they answer "is
      something running right now". A paused interactive slot has no tmux session and issues only
      short-lived shell commands, so between two of them every signal reads idle. It wiped slot
      17's venv three times in one session, each costing a full `uv sync` before the gate could
      run. Added a fourth, DURABLE signal: paused slot ids read from `data/state/state.db`,
      mirroring `dispatch.slot_is_operator_paused`. Fails OPEN (no sqlite3 / unreadable DB → fall
      back to the three live signals), deliberately the opposite of `proc_table_readable`'s
      fail-closed stance — reasoning in the function's own comment. The GENERAL bug stays in its
      own doc. — `agent-orchestrator@7f0887d4f9`
- [ ] [DOC] P3. **`ORCHESTRATOR_FLEET_WORKER_CAP=40` is inert.** Every tick logs
      `configured=40 CLAMPED to 25 by slot arithmetic (configured_slots=32 - reserve=7
      [ci=3 + scheduled=4])`. The clamp is by design and already logged loudly, but the live
      `.env.local` still carries a number that has no effect, which is a trap for the next
      operator. Set it to the real ceiling or delete the override.

## Deferred work after 2026-08-22

| Item | State / why deferred | Blocked on |
| --- | --- | --- |
| Re-measure the fleet 24h after the fixes (`[INFRA] P1` above) | **Cannot be done yet** — needs elapsed time; the fixes went live 22:20Z and 4-min-old signals are not evidence | wall-clock only |
| Role/reserve starvation (`[BACKEND] P1`) | **DONE 2026-08-22 — FALSIFIED.** Re-measured with AO's own predicates: 0 of 349 capacity-waiting tasks have no eligible slot, and dropping both reserves frees 0 more. The 62% figure ignored generic slots, which accept every role. No change needed | — |
| Stray git dirs permanently quarantining slots (`[INFRA] P2`) | **DONE 2026-08-22** — the dominant live blocker (239/355 autospawn + 104/141 escalation failures in 24h). One enumerator, `classify_slot_dirs` | — |
| `vm-disk-guard.sh` paused-slot exemption (`[INFRA] P2`) | **DONE 2026-08-22** — a fourth, DURABLE keep-signal; the other three are all instantaneous and read a paused interactive slot as idle | — |
| `prereqs` blocks 439 of 789 queued tasks (56%) | **Not done** — now the largest single fleet-scope blocker by a wide margin, and the natural next lever. Decomposes into the durable-park defect (already fixed once, re-verify) and the two operator rulings below | partly operator |
| `explain_blocked` lists 14 phantom human slots as "eligible" (`[BACKEND] P2`) | **Not done** — diagnostics honesty, no behaviour change | nobody |
| `slot_done_rejected_dirty` (`[BACKEND] P2`) | **Not done**, but MUCH smaller than recorded: fresh 24h count is **60 rejected vs 81 accepted**, not the 262-vs-79 in the todo above. Re-measure before sizing a fix; the stray-dir fix should shrink it further (backup CLONES were blocking `/done`; linked worktrees already were not) | nobody |
| Disposition of the stray dirs' CONTENT (`pm-fix`, `pm-ship.MpuQMt`, `oms-wt.oc3YkB`, `unified-trading-pm-current`, `*.stale-pre-history-rewrite-*`) | **Operator-owned** — they hold 190-231 uncommitted files each. They can no longer wedge a slot, so this is no longer urgent; do NOT blind-delete | operator |
| 35 tasks behind 11 `status: draft` upstream plans (`[OPERATOR] P3`) | **Operator-owned** — only a human `draft`→`active` flip can clear these | operator |
| 6 named prerequisites nothing can ever set (`[OPERATOR] P3`) | **Operator-owned** — needs a ruling on what clears each | operator |
| Interactive-session-in-an-AO-slot hazard (`[INFRA] P1`) | **DONE 2026-08-21** — operator ruled paused = hands off; `agent-orchestrator@3cfd9bcfb8` | — |

**Recommended NEXT item: the `prereqs` fleet-scope blocker.** With the reserve falsified and the
quarantine wedge fixed, this is what is actually holding the queue: 439 of 789 queued tasks fail
`_prereqs_met`, so no slot can claim them regardless of capacity. Start by splitting that 439 into
(a) genuine upstream-incomplete, (b) durable-park conditions never cleared, (c) the 6 unsettable
named prerequisites — only (b) is a code bug, and it has been fixed once already, so verify before
re-diagnosing. (a) is mostly the 11 draft plans, which is an operator flip.

**Do NOT re-open the reserve or role-matching angle** without first re-reading why it was falsified:
`craft_role` is CAPABILITY-scoped because AutoSpawn re-roles a slot at spawn, and a slot with an
unset `slot_role` accepts every role. "Role-matching idle slots" is not the question dispatch asks.

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

**2026-08-22 (interactive session, slot 17)** — Picked up the `[BACKEND] P1` role/reserve item as
the planned next step and **falsified it**. Rather than re-deriving the counts by hand I drove
AO's own predicates (`first_blocking_filter` over the real `_FILTERS` table) against a
`sqlite3 .backup` snapshot of the live DB and the live `backlog.yaml`. Result: of 349
capacity-waiting tasks, **zero** have no eligible slot, and dropping both reserves would free
**zero** more. The original 62% figure came from counting only slots whose `slot_role` EQUALS the
task's role — but `_blocks_craft_role` passes any slot whose `slot_role` is unset, so the 11
generic slots are universal donors and were all missed. Lesson worth keeping: `craft_role` is
CAPABILITY-scoped precisely because AutoSpawn re-roles a slot at spawn, so "role-matching slots"
is not the question dispatch asks. The reserve needs no change.

That freed the search to find what IS blocking, and the answer was not on the demand side at all.
`autospawn_failed` over 24h: **239 of 355 (67%) `dirty-state quarantined`**, plus 104 of 141
escalation-dispatch failures — spanning 10 slots, slot 11 alone 54 times, and still firing at
06:05Z. Cause: all four walks in `worktree_clean_check` hand-rolled `slot_dir.iterdir()`, so any
git-shaped directory under a slot counted as one of its repos. The offenders are ship-script
leftover linked worktrees and `*.stale-pre-history-rewrite-*` backup clones carrying 190-231
uncommittable dirty files; the FM9 conflict-marker guard refuses them (correctly), and the whole
slot is then quarantined forever with no self-heal. Notably `check_slot_clean`'s own docstring
already said a linked worktree flat under a slot dir "is always a stray", and the `/done` gate
already filtered on it — only the dirty-PRESERVE path never did. Fixed with one enumerator
(`classify_slot_dirs`) plus a source-level test that no fifth walk can re-hand-roll `iterdir`.
Verified the classification against all 10 affected slot dirs read-only before changing anything:
26/26 canonical repos matched their origin, 6/6 strays flagged, zero false positives.

Two rule-design notes, both changed after first writing them the other way. (1) "Origin unreadable"
does NOT mean stray — absence of evidence is not evidence, and the safe answer is the pre-existing
behaviour (treat it as the slot's repo). Both stray rules are positive-evidence only. (2) The
origin name is read from `.git/config` as a FILE, not via `git remote get-url`: this runs per
directory per slot per sweep tick, and a subprocess each would add ~1000 forks per sweep.

Measurement traps hit this session, recorded so they are not re-paid: (a) `task_done` is not an
event type — the real one is `slot_done_verified`, and querying the wrong name produced a
spectacular-looking "0 tasks completed in 24h" that was pure artifact (true figure: 81/24h,
cross-checked against `tasks.done_at`). Always enumerate the event vocabulary first. (b) A
backgrounded `... ; tail -3 log` reports **tail's** exit code, so the harness said "completed exit
code 0" for a gate run that had actually ABORTED — the durable `QG_EXIT_CODE=$?` marker in the log
is the only trustworthy signal. (c) The tmux server was found dead with zero live workers, which
looks like the headline cause but is downstream: every spawn attempt was failing at the
dirty-state gate before ever reaching tmux, so no session was ever created to keep it alive.
