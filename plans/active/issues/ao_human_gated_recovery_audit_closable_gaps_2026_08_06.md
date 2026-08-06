---
doc_type: issue
title: >-
  AO human-vs-auto-recover audit (2026-08-06): fleet-wide account failover is fully automatic (8-account blended
  Claude+DeepSeek pool, self-heals through auth-fail/rate-limit/cooldown); only genuine human-gate is a real OAuth
  re-auth. Two closable gaps found in the watchdog's own self-healing, independent of the account layer.
summary: >-
  Operator asked: across agent-orchestrator, catalog every point that requires a human vs auto-recovers, with a target
  of zero human-gates except total exhaustion (every Claude account AND DeepSeek both at zero capacity). A background
  research agent audited the full codebase + live VM. Verdict: the account/provider layer already meets the bar —
  `select_account_for_spawn` (agent-orchestrator/server/autospawn.py) is the single shared selector used by every
  dispatcher (escalation.py, AutoSpawnLoop, plan_health.py, the usage-cap handler, the main-agent keeper), rotates
  across 6 Claude (max20) + 2 DeepSeek (pro/flash) accounts automatically on auth-fail/rate-limit, and even an
  auth_failed account self-heals via a cooldown-expiry re-probe (state_store/account_usage.py
  account_in_auth_failed_cooldown) — `notify_all_accounts_unusable` correctly downgrades to non-paging INFO for pure
  rate-limiting and only pages for a genuine `auth_failed`/`disabled` account needing `claude setup-token` (an
  interactive OAuth handshake — a legitimate, doctrine-consistent human bar). One SEPARATE dispatcher
  (`plan_health.py`'s "no headroom setup-token account available" stall the operator had seen) bypassed this shared
  selector and was DeepSeek-blind — already fixed same-day by someone else (agent-orchestrator@ef44eb9,
  `plan_health_deepseek_fallback_2026_08_06`), verified live on the VM. Two REAL, independent gaps remain, both in
  WorkerLivenessWatchdog's own self-healing (not the account layer) — see Todos. Live capacity check (VM
  i-0c9b283b31d6b5ca7, m8i.4xlarge, 16 vCPU/64GB): memory comfortable (47GB available of 61GB); CPU shows real but
  bursty contention (load avg 8.3/6.4/5.3, a captured vmstat sample briefly saw 43 runnable processes against 16 cores)
  — not saturated, but non-fleet processes (deployment-service/wave_launcher.py, ad-hoc migration scripts) compete on
  the same box as the 16-17 fleet slots, a believable contributor to observed worker stalls even with no single process
  starved.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [self-healing, watchdog, autospawn, account-failover, capacity, resource-contention]
related:
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
created: "2026-08-06"
author: ikennaigboaka [slot-4·laptop]
source: [interactive session, operator question "when do we need a human vs auto recover in AO"]
assigned_vm: NA
execution_scope: local-only
priority: P2
parent_epic: orchestrator_master
drift_direction: advance-code
resolved_by:
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    agent-orchestrator/server/worker_liveness/_auth_failover.py,
    agent-orchestrator/server/autospawn.py,
  ]
---

# AO human-vs-auto-recover audit — two closable watchdog gaps (account layer already fully automatic)

## What I found

Full research-agent report (grounded, file:line cited) is in this session's transcript. Condensed:

**Already fine / irreducible (no action)**: usage-cap freeze (re-probes every tick, auto-resumes), auth-fail eviction
(`rotate_all_slots_off_account`, fully automatic, preserves in-flight task+worktree), auth-fail cooldown self-heal,
`notify_all_accounts_unusable`'s rate-limit-vs-auth-failed split, CI-wall re-escalation cap (defensible judgment bar),
branch-state/wiped-index STOP (explicit data-loss guard, matches CLAUDE.md's own hard rule).

**Already fixed by someone else today**: `plan_health.py`'s DeepSeek-blind account pool (agent-orchestrator@ef44eb9,
verified live).

**Two real, closable gaps — todos below**:

1. `spawn_retry_count` (agent-orchestrator/server/orm.py:157) is written only by the manual `/spawn`/`/respawn` HTTP
   endpoints (routes/slots_ops.py:508,521) — the automatic spawn-success path (autospawn.py:2086-2110, "Shared success
   point for ALL spawn callers") resets `tmux_session`/`last_spawned_at`/`account_id`/the alert latch but NOT this
   field. Once a slot trips `_SPAWN_HEARTBEAT_MAX_RETRIES` (2, worker_liveness/**init**.py:104) once in its life, the
   diagnostic same-account retry-with-pane-diagnosis path (`_auth_failover.py:check_spawn_heartbeat_timeouts`) is
   silently, permanently disabled for that slot — every future spawn attempt falls straight to the coarser Trigger-3
   heartbeat-silent kill+respawn (worker_liveness_watchdog.py) instead, which still works but skips the smarter
   diagnosis. The `notify_spawn_failed` alert text ("slot stays down until manual respawn or reclaim") is also
   misleading — Trigger-3 usually DOES recover it automatically ~15 min later; the alert overstates the dead-end.

2. `_tick_once()`'s daily-kill-cap early-return (worker_liveness_watchdog.py, `if self._daily_cap_reached(): return`)
   sits AFTER `_sweep_dirty_slots`/`_sweep_unpushed_slots` (deliberately moved ahead of it in a prior incident fix — see
   the comment at :675-681) but BEFORE everything else: orphan-session reclaim (own comment says it's cleanup of an
   already-dead worker, NOT a kill — so it's mis-gated), `_reclaim_idle_lingering_sessions`,
   `_release_prereq_blocked_slots`, `_reclaim_orphaned_dispatched_tasks`, `_reclaim_stale_resume_pending_dispatches`,
   `_reconcile_unacked_dispatches`, and all 5 remaining live triggers. Same bug class the codebase already recognized
   once (hence the prior partial fix) — left incomplete. `notify_watchdog_kill`'s cap-hit alert doesn't disclose that
   reclaim/reconcile logic (not just future kills) also goes dormant for the rest of the UTC day. Also: the module
   docstring at :37,41 says the cap defaults to 20; the live config default (config.py:1090) is 50 — stale doc, minor,
   fix in the same pass.

Partial mitigation already in place for #2: `WorkerLivenessKicker` is a separate daemon/class
(worker_liveness/**init**.py:370) not gated by `_DAILY_KILL_CAP` at all, so kick/nudge + its own respawn logic keep
running even on a cap-hit day — the fleet degrades, it doesn't fully paralyze.

## Recommended decision / Todos

- [ ] [SCRIPT] P2. **agent-orchestrator** — reset `spawn_retry_count = 0` in the shared automatic spawn-success path
      (autospawn.py:2086-2110, alongside the other fields already reset there) so a slot's diagnostic retry-with-
      pane-diagnosis capability isn't permanently disabled after one lifetime retry-cap trip. Add a regression test
      mirroring the existing spawn-success-resets-fields tests. Also correct `notify_spawn_failed`'s alert text so it no
      longer implies a dead end when Trigger-3 will, in practice, usually recover the slot ~15 min later.
- [ ] [SCRIPT] P2. **agent-orchestrator** — audit every sub-mechanism inside `_tick_once()` that currently sits AFTER
      the daily-kill-cap early-return; move the ones that are cleanup/reconcile (not a NEW kill decision — same
      rationale as the already-fixed `_sweep_dirty_slots`/`_sweep_unpushed_slots`) ahead of the cap check, starting with
      orphan-session reclaim (whose own comment already states it isn't a kill). For the ones that genuinely ARE
      new-kill triggers (the 5 live triggers), decide deliberately whether they should also survive a cap-hit day or
      correctly stay gated — don't leave the boundary implicit. Fix the stale "default 20" docstring to match the live
      default (50, config.py:1090) in the same commit. Update `notify_watchdog_kill`'s cap-hit alert text to disclose
      which mechanisms actually go dormant.
- [ ] [DOC] P3. **agent-orchestrator (host)** — the live capacity read (load avg ~8.3/6.4/5.3 on 16 vCPU, a captured
      43-runnable-process burst, non-fleet processes — deployment-service wave_launcher.py, ad-hoc migration scripts —
      sharing the box with 16-17 fleet slots) suggests real but bursty CPU contention, not saturation. Not urgent, but
      worth a operator decision: should heavy one-off scripts (migrations, wave_launcher) be barred from running
      directly on the orchestrator host during full-fleet hours, per the existing "heavy compute on shared host" SSOT
      (`/codex/05-infrastructure/vm-launcher-runbook.md`), given they're already sharing CPU with the CPUWeight=4000-
      prioritized orchestrator cgroup?

## Progress Log

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
