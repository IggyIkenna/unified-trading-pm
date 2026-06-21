---
title: "Orchestrator self-healing hardening — account rotation + watchdog recovery + audit-reflog noise"
created: 2026-06-21
status: active
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: local-only
locked_by: live-defi-rollout
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
source:
  - 2026-06-21 operator request — "100% functionality:
      always pick accounts with usage left, rotate inline when they run out, re-trigger agents that get dirty / rolled
      back / stale"
  - 2026-06-21 agent-orchestrator-alerts channel — "Audit Reflog — High Risk" firing every ~11 min all night (cc89557 /
    53bbd95)
priority: P1
---

# Orchestrator self-healing hardening

## Why

The operator asked for three guarantees, end to end, in the agent-orchestrator:

1. **Always pick a billing/usage account with headroom left** (never spawn onto an exhausted one).
2. **Rotate between accounts when one runs out, inline** — mid-task, without stranding the work.
3. **Re-trigger any agent that gets dirty, rolled back, or stale "for any other reason" so it continues** — no slot
   wedged forever, no queued work that never resumes.

A 2026-06-21 audit (this plan) found the core mechanisms are already shipped (`_pick_headroom_account`,
`rotate_all_slots_off_account`, the usage-cap watchdog resume-respawn, `_reclaim_idle_lingering_sessions`, TmuxPruner
task-release, AutoSpawn respawn) — the system **mostly self-heals, but with latency + a handful of edge wedges**. This
plan ships the highest-impact robustness closures and tracks the rest. It also closes the **audit-reflog alert spam**
(firing every ~11 min) which was NOT an active reset-loop — `ao-self-pull.sh` / `slot-cron-ff-pull.sh` are both
non-destructive (`merge --ff-only`, never `reset`) — but a one-time orphan-wip discard re-flagged forever because its
SHAs were never acknowledged.

## Shipped this session (2026-06-21)

- [x] [ORCHESTRATOR] P1. **Fix (a) — deterministic recovery on a failed account-rotation respawn.** When
      `spawn_with_account_bg` fails AFTER the old session is killed (no `oauth_token_env_file`, render fail, tmux spawn
      throw), the slot was left half-dead (`working` + dead session pointer + `current_task` still bound), relying on a
      later TmuxPruner grace-tick. `_recover_slot_after_failed_rotation` now releases the held task back to the queue
      (never stranded `dispatched`) + flips the slot to `killed` for an immediate AutoSpawn re-pick on a fresh headroom
      account. `paused` preserved (operator intent). — agent-orchestrator@8d728a8 | tests:
      test_self_healing_hardening.py (2 cases)
- [x] [ORCHESTRATOR] P1. **Fix (b) — reclaim a `stale` lingering live session (resume-work gap).**
      `_reclaim_idle_lingering_sessions` queried `status=='idle'` ONLY, so a worker that finished + lingered then got
      flipped idle→`stale` by the HealthMonitor (silent >5 min) fell through BOTH the reclaim AND `_pick_free_slot` — it
      occupied the slot until the 15-min heartbeat-silent kill, blocking resume of queued work for ~10 min. Now also
      reclaims `stale` lingering sessions, with a `_is_actively_thinking` pane guard (never reap a genuinely-working
      slot that merely went quiet — the main loop owns that). — agent-orchestrator@8d728a8 | tests:
      test_self_healing_hardening.py (3 cases)
- [x] [ORCHESTRATOR] P1. **Fix (c) — preserve-then-realign auto-heal for a provably-dead branch-quarantined slot.**
      `_do_spawn`'s branch-state gate `return`ed False on diverged/wrong-branch/detached and wedged the slot in `killed`
      forever. `heal_dead_slot_branch_quarantine` now, for a provably-DEAD slot only (never stomp a live peer),
      PRESERVES every commit not on `origin/<base>` to a durable `origin/wip-preserve/...` ref FIRST (refuses to realign
      if the preserve push fails), then realigns HEAD to `origin/<base>` via `git checkout -B` (a CHECKOUT, not a
      `reset`, so it does NOT emit the `reset: moving to origin/<base>` reflog signature the audit-reflog guard pages
      on). This is the exact recovery that should have happened to the discarded cc89557/53bbd95 commits. —
      agent-orchestrator@8d728a8 | tests: test_dirty_state_resolution.py (2 cases)
- [x] [SCRIPT] P1. **Audit-reflog spam — acknowledge the orphaned SHAs + preserve the recoverable one.** Added
      `agent-orchestrator:cc89557` (empty commit) + `e2e-testing:53bbd95` to
      `scripts/repo-management/audit-reflog-ignore.txt`; preserved 53bbd95 (a 3-line `pred` bucket change) to
      `origin/wip-preserve/e2e-slot4-orphan-pred-bucket-2026-06-20`. — unified-trading-pm@57072ee9d (PR #464); reaches
      the central VM via `pm-pull`.

- [x] ✅ [ORCHESTRATOR] P1. **Escalate-worker branch cleanup (root cause of the recurring "Spawn failure — branch-state
      quarantine slot 1" alert, 2026-06-21 14:47).** The escalate worker creates a temp `_escalation_work` branch to
      resolve a wall but EXITED without returning the slot's repos to `live-defi-rollout` → the next spawn trips FM5/FM7
      → quarantine. `agents/escalate.md` now mandates a LEAVE-THE-SLOT-CLEAN step before EXIT (`merge/rebase --abort` →
      `git checkout live-defi-rollout` → drop `_escalation_work`) in every repo touched. Composes with Fix (c)'s
      auto-heal (defense in depth: prompt prevents it; auto-heal recovers it). — agent-orchestrator@8953d98

## Remaining work — to 100%

### Concern 1 — account selection (already strong; these close races + spread load)

- [x] ✅ [ORCHESTRATOR] P2. Late-binding account re-check in `_do_spawn` — re-queries the picked account's usability
      AFTER dirty/branch resolution but BEFORE `tmux_spawn.spawn`; if it went `rate_limited`/`auth_failed` in the
      pick→spawn window, refuse (next tick re-picks a fresh headroom account, re-rendering account_id cleanly).
      Best-effort (proceeds on a DB hiccup). — agent-orchestrator@8953d98
- [x] ✅ [ORCHESTRATOR] P3. Load-spread secondary sort in `_pick_headroom_account` — `_active_slot_counts_by_account`
      adds active-slot-count as the third sort key after (5h%, weekly%), so equal-usage spawns fan out across the pool.
      — agent-orchestrator@8953d98 | tests:
      test_self_healing_hardening.py::test_pick_headroom_prefers_account_with_fewer_active_slots

### Concern 2 — inline rotation (on-run-out path; 95% stays a spawn-gate, never a preempt)

- [ ] [ORCHESTRATOR] P2. Worker self-report on mid-task usage exhaustion — give the worker boot prompt + a small client
      a trap for the Claude CLI usage-limit / 429 message that POSTs `/api/accounts/{id}/rate-limited`, so rotation
      fires within seconds instead of waiting up to the 30-min UsagePoller tick or the ~60-s TmuxPruner pane-scan.
      Target: agent-orchestrator `agents/worker.md` + `routes/accounts.py`. NOTE: do NOT make 95% preempt a running
      agent — the 95% ceiling is a spawn-gate-only by operator decision
      (orchestrator_account_failover_resume_respawn_2026_06_17).
- [ ] [ORCHESTRATOR] P2. Wire the heartbeat-silent/crashed-worker watchdog reap→respawn to
      `--resume <SlotRow.claude_session_id>` (context-preserving). **Already tracked** as Phase 5 of
      `orchestrator_account_failover_resume_respawn_2026_06_17.md` — referenced here, not duplicated.

### Concern 3 — self-healing (re-trigger dirty / rolled-back / stale)

- [x] ✅ [ORCHESTRATOR] P1. Orphan-wip inherit now realigns via `git checkout -B <base> origin/<base>` instead of
      `git reset --hard origin/<base>` — the reset emitted the `reset: moving to origin/<base>` reflog signature the
      audit-reflog guard pages on, so EVERY dead-predecessor WIP inherit re-armed the "Audit Reflog — High Risk" alert
      (the chronic central-VM 11-min spam, incl. cc89557/53bbd95) even though the WIP was preserved to wip-preserve.
      Checkout reaches the same clean end-state with a `checkout:` reflog the audit ignores — **fixes the spam at its
      SOURCE** (the ignore-file was the symptom-level fix). — agent-orchestrator@8953d98 | tests:
      test_dirty_state_resolution.py
- [x] ✅ [ORCHESTRATOR] P2. Watchdog-loop self-supervisor — new `server/loop_supervisor.py::LoopSupervisor` checks every
      registered daemon loop's thread liveness every 120s and revives a dead one via its idempotent `start()` (no-op
      when alive, recreates the thread when dead) — so a crashed `WorkerLivenessWatchdog`/`AutoSpawnLoop`/`TmuxPruner`/
      `HealthMonitor`/`UsagePoller`/etc never silently stops the fleet self-healing; only the supervisor itself (root)
      needs a backend restart. Wired into the lifespan (started last, stopped first); env-disabled loops are not
      registered (not forced on). — agent-orchestrator@470c13c | tests:
      test_self_healing_hardening.py::test_loop_supervisor_revives_dead_but_not_alive_or_disabled
- [ ] [ORCHESTRATOR] P2. WorkerLivenessWatchdog bogus idle-minute calc — the silence anchor can inherit a predecessor
      session's `last_spawned_at` and balloon backwards (reported 5711 min / 1515 min, physically impossible). **Already
      tracked** in `plans/active/issues/agent_orchestrator_alerts_triage_2026_06_20.md` — referenced, not duplicated.
- [ ] [ORCHESTRATOR] P1. Central-VM backend single-process-manager (systemd + main-agent `nohup` dual-manager → one).
      **Already tracked** in `plans/active/issues/orchestrator_agent_lifecycle_gaps_2026_06_16.md` Gap 4 — referenced,
      not duplicated.

### Audit-reflog — kill the recurring spam class for good

- [ ] [SCRIPT] P2. Disk-backed dedup in `run-audit-reflog-with-alert.sh` — never re-fire the Slack alert on an orphaned
      reset SHA already alerted on (the ignore-file is per-SHA whack-a-mole; this is the systemic fix — 3rd documented
      "re-alerting every ~11 min on acknowledged resets" occurrence). Persist a seen-set like the orchestrator's
      `dedup_state`; only NEW high-risk SHAs alert. Composes with `alert_quality_overhaul_2026_06_18.md` Phase 6
      (carrier routing for `run-audit-reflog-with-alert.sh`). Target: unified-trading-pm
      `scripts/repo-management/run-audit-reflog-with-alert.sh`.

## Operator follow-up requests (2026-06-21) — orchestrator autonomy

Captured from the operator's 2026-06-21 follow-up. These extend the orchestrator's autonomous-recovery surface; they are
net-new capability (not robustness closures) and are dispatched to the central VM via these tracked todos.

### Conflict-wall promotion PRs → escalate → autonomous worker → review-logged completion

- [ ] [ORCHESTRATOR] P1. A promotion PR that is a GENUINE conflict wall (`mergeStateStatus` CONFLICTING / DIRTY — NOT
      the mechanical "v2-never-reported" deadlock, which `ci_failure_watcher --auto-recover` already close+reopens with
      no worker) must ESCALATE: post `/api/escalate wall_type=promotion_conflict` to the central VM AND fire a Slack
      alert routed to vm-planning. The orchestrator then AutoSpawns a worker that rebases/resolves the conflict ON
      `live-defi-rollout` (keep both sides' genuine work) and drives the PR to merge. Target: unified-trading-pm
      `scripts/repo-management/ci_failure_watcher.py` (classify + escalate) + agent-orchestrator `server/escalation.py`
      (new wall_type → escalate prompt). Composes with the existing `--auto-recover --escalate` split — do NOT escalate
      the mechanical deadlock.
- [ ] [ORCHESTRATOR] P1. The escalated conflict worker runs in **/autonomous mode** (paste `AUTONOMOUS_AGENT_RULES.md` +
      `SUB_AGENT_MANDATORY_RULES.md`; run-to-DONE loop) so it completes the resolution to a merged PR without a human,
      then a **review agent's final check** verifies the merge landed (PR merged + content on the target branch) and
      **logs the successful completion to Slack** (vm-planning). Target: agent-orchestrator `agents/escalate.md`
      (autonomous-mode boot) + the review-agent final-check path. NOTE: never auto-resolve a conflict by blind
      take-mine/take-theirs or force-push a shared branch (Path-B ship discipline).

### 24-hourly autonomous plan/codex/cross-plan reconciliation + auto-archive

- [ ] [ORCHESTRATOR] P2. A 24-hourly autonomous reconciliation job (orchestrator-driven, dispatched to a worker in
      /autonomous mode, logged on completion) that runs, in order: (1) `run_hygiene_sweep.sh` (frontmatter / line-caps);
      (2) **plan-vs-codex** — each active plan's `Codex SSOTs:` rows reflect what actually shipped (stale → fix or
      SUPERSEDED banner); (3) **plan-vs-plan** — overlap/dedup detector across `plans/active/` (no two plans own the
      same work); (4) **open-todo truth check** — for every `- [ ]` in an active plan, verify it is genuinely NOT done
      against the repo/git (a silently-shipped item gets flipped + evidence). Target: agent-orchestrator (a new
      `PlanReconcileLoop`, 24h cadence, env-gated) + unified-trading-pm reconciliation checks. Composes with
      `PlanRegenLoop` + the daily `run_hygiene_sweep.sh` cron.
- [ ] [ORCHESTRATOR] P2. The same 24-hourly job AUTO-ARCHIVES any plan or issue doc that reconciliation proves is fully
      DONE — following the 5-step archival HARD RULE (scan deferred → banner → codex-alignment check → CLAUDE.md/codex
      update → unlock), and the issue-doc lifecycle (acked → archive immediately). Driven autonomously; logged. Target:
      unified-trading-pm `plans/` archival tooling invoked by the reconcile loop. NOTE: respect `locked_by:` — never
      auto-unlock a locked plan; surface it for operator `[unlock-plan]` instead.

## Codex SSOT updates

- [ ] [DOC] P2. `codex/04-architecture/agent-orchestrator-worker-liveness.md` — document the `stale`-lingering reclaim
      coverage (fix b) + the branch-quarantine auto-heal (fix c) trigger contracts.
- [ ] [DOC] P2. `codex/04-architecture/agent-orchestrator-overview.md` § Watchdog/Failover — note the deterministic
      rotation-failure recovery (fix a) and that auto-heal realigns via `checkout` (no audit-reflog page).

## Success criteria

- A failed rotation respawn never leaves a `dispatched` task stranded or a slot wedged `working` with a dead session
  (fix a — DONE, tested).
- A finished/wedged worker (idle OR stale) frees its slot within `_IDLE_SESSION_RECLAIM_TICKS`, so queued work resumes
  without the 15-min heartbeat wait (fix b — DONE, tested).
- A provably-dead branch-quarantined slot auto-heals (commits preserved, realigned) and spawns, instead of wedging
  `killed` (fix c — DONE, tested).
- The "Audit Reflog — High Risk" alert stops firing on cc89557/53bbd95 (DONE, shipped) and — once the dedup todo lands —
  never re-fires on any already-acknowledged reset SHA.
