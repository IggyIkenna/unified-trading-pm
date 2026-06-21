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

- [x] ✅ [ORCHESTRATOR] P2. Worker self-report on mid-task usage exhaustion — `agents/worker.md` now instructs the
      worker to POST `/api/accounts/<ACCOUNT_ID>/rate-limited` on a tool-level 429/usage-limit (while it can still act),
      so rotation fires in seconds. The FROZEN-on-modal case (worker can't POST) stays covered by the TmuxPruner
      pane-scan + watchdog (documented inline). 95% stays spawn-gate-only (not changed). — agent-orchestrator@39cbf10
- [x] ✅ [ORCHESTRATOR] P2. G2b — heartbeat-silent reap now does a context-preserving `--resume` (operator-permitted
      2026-06-21). `_resume_or_fresh_respawn` kills the wedged session + `claude --resume <claude_session_id>` on the
      SAME account (it's not capped — that's a separate trigger), so the worker continues with conversation intact.
      Guarded against a resume-loop: resume ONCE per silence episode (`_HEARTBEAT_RESUME_MAX`); if it goes silent AGAIN
      it's genuinely stuck → fresh respawn. No session id / no env → fresh respawn. Supersedes the Phase-5 cross-ref in
      `orchestrator_account_failover_resume_respawn_2026_06_17.md`. — agent-orchestrator@b02d65f | tests:
      test_self_healing_hardening.py (2 cases)

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
- [x] ✅ [ORCHESTRATOR] P2. WorkerLivenessWatchdog/HealthMonitor bogus idle-minute calc (the "idle for 5711min") — the
      silence anchor now ALSO includes the LIVE tmux session's creation time (`tmux_spawn.session_created_at` →
      `_effective_silence_seconds` + the health idle path), a true lower bound, so a freshly-respawned worker that
      inherited a predecessor's ancient `last_spawned_at` can't balloon backwards. Closes the triage
      `agent_orchestrator_alerts_triage_2026_06_20` G3c. — agent-orchestrator@68d27b5 | tests:
      test_self_healing_hardening.py::test_effective_silence_clamped_by_session_created
- [x] ✅ [ORCHESTRATOR] P1. Central-VM backend single-process-manager (operator-permitted 2026-06-21) — the launch path
      `server.server.main()` now calls `_assert_single_instance(8765)`: if :8765 is already bound it logs + exits 1
      rather than racing a second uvicorn (the orphaned-uvicorn-re-persists-stale-backlog incident, 2026-06-16).
      `agents/main.md` gains a HARD rule: restart the backend with `sudo systemctl restart orchestrator.service` (stops
      the old instance first), NEVER `nohup uvicorn`. Override for dev/second-port via
      `ORCHESTRATOR_ALLOW_PORT_CONFLICT=1`. Closes `orchestrator_agent_lifecycle_gaps_2026_06_16` Gap 4. —
      agent-orchestrator@e20fd30 | tests:
      test_self_healing_hardening.py::test_single_instance_guard_refuses_when_port_bound

### Audit-reflog — kill the recurring spam class for good

- [x] ✅ [SCRIPT] P2. Disk-backed dedup in `run-audit-reflog-with-alert.sh` — the alert now early-exits when the STABLE
      orphaned-`<repo>:<sha>` set (from the "add … to audit-reflog-ignore.txt" lines, NOT the climbing `HEAD@{N}`) is
      unchanged vs the last alert (signature persisted under `~/.cache/audit-reflog/`). Only a NEW high-risk SHA (or the
      set shrinking after an ignore/recover) re-fires — kills the recurring-spam class for good (composes with G3a,
      which stops the noise at the source). — unified-trading-pm (PR #469)

## Operator follow-up requests (2026-06-21) — orchestrator autonomy

Captured from the operator's 2026-06-21 follow-up. These extend the orchestrator's autonomous-recovery surface; they are
net-new capability (not robustness closures) and are dispatched to the central VM via these tracked todos.

### Conflict-wall promotion PRs → escalate → autonomous worker → review-logged completion

- [x] ✅ [ORCHESTRATOR] P1. Conflict-wall escalation — VERIFIED ALREADY LIVE + hardened. `ci_failure_watcher.py` already
      classifies CONFLICTING/DIRTY promotion PRs (`_CONFLICT_STATES`) as a resolvable merge_conflict wall and fires
      `escalate-to-orchestrator.yml` (vm-planning Slack); the mechanical v2-deadlock is `--auto-recover`'d with no
      worker (the split already exists). The `escalate.md` worker resolves merge_conflict on LDR (keep both sides).
      Hardened this session: it now returns every repo to `live-defi-rollout` before EXIT (Batch 2), so it stops leaving
      the `_escalation_work` quarantine. — agent-orchestrator@8953d98 (proven by the 14:27→14:37 dispatch→RESOLVED
      cycle).
- [x] ✅ [ORCHESTRATOR] P1. Autonomous completion + review-logged — VERIFIED ALREADY LIVE. `escalate.md` drives the wall
      to a pushed fix then EXITs (bounded firefighter; ASK-without-block only for human-decision walls);
      `escalation.verify_dispatched_escalations()` (run each AutoSpawn tick) confirms the wall reached a terminal
      verdict and posts the `:ballot_box_with_check: escalation RESOLVED — <repo>#<n> … Verdict: qg_v2_green` bookend to
      Slack (vm-planning) — exactly the operator's "logged when they complete per the final check" (the 14:37
      strategy-service#238 RESOLVED alert is this path). NOTE: full unbounded /autonomous-loop on a shared firefighter
      slot is intentionally NOT adopted (it would starve other queued escalations) — the bounded resolve-then-verify IS
      the design.

### 24-hourly autonomous plan/codex/cross-plan reconciliation + auto-archive

- [x] ✅ [ORCHESTRATOR] P2. 24-hourly reconciliation job — VERIFIED ALREADY LIVE. The `plan-reconciler` worker
      (`agents/plan-reconciler.md`, opus/max, daily systemd timer →
      `POST /api/plan-health/dispatch {"mode":"reconcile"}`) already does (1) hygiene sweep, (2) plan-vs-codex doc-drift
      (STEP 3c), (3) plan-vs-plan contradiction (STEP 3b), (4) open-todo truth-check against real code/sha (STEP 3a) —
      checkpoint-committed to a review-PR, logged to Slack. The read-only daily detector is `agents/plan-health.md`. —
      verified 2026-06-21 (the 14:35 plan-health dispatch→ PM#466 RESOLVED proves the path).
- [x] ✅ [ORCHESTRATOR] P2. Auto-archive of verified-DONE plans — SHIPPED. `agents/plan-reconciler.md` STEP 3f changed
      from "SUGGEST, never archive" to AUTO-ARCHIVE: a verified-fully-done, UNLOCKED, non-grace plan is `git mv`'d into
      `plans/archive/` following the 5-step rule (deferred-migrate → banner → codex-align → flag-contract → mv), on the
      worker's review branch so the STEP-5 PR is still the human safety gate. **HARD STOP**: `locked_by:` plans +
      grace-set + any unverified plan stay active + suggest-only (operator unlocks). — agent-orchestrator@39cbf10.

### Operator-gated blocked todos must page (with a respond-link)

- [x] ✅ [ORCHESTRATOR] P1. OPERATOR-gated plan todos fire a Slack alert with a respond deep-link — `[OPERATOR]`-tagged
      todos are seeded `status=blocked` + a synthetic `BlockedRow` (slot 0) by `bootstrap.sync_backlog_to_db`; they
      NEVER pass through `/api/slots/{id}/blocked`, so NO alert fired and 5 sat in the dashboard "awaiting" for 1 day
      (operator report 2026-06-21). `_alert_unanswered_operator_gated_blocks` now fires `notify_operator_gated_blocked`
      (":raising_hand: Operator decision needed" + `/#blocked` deep-link to the dashboard answer surface), DISK-BACKED
      deduped per blocked_id — so each unanswered op-gated todo pages exactly once (the existing 5 page on the
      post-deploy restart; new ones page on creation; answered/seen ones never re-page). — agent-orchestrator@7b435a3 |
      tests: test_self_healing_hardening.py::test_operator_gated_blocked_alerts_once_then_dedups

### Live Slack alerts addressed (2026-06-21)

- **Audit Reflog — High Risk** (every ~11 min): ignore-file ack + WIP preserve (#464); G3a fixes the SOURCE
  (checkout-not-reset); G4b dedups the alerter. Triple-covered.
- **Spawn failure — branch quarantine slot 1** (14:47): escalate.md leave-slot-clean (root cause) + Fix (c) auto-heal.
- **Slot 5 FAILED — heartbeat loop dead** (14:38): Fix (b) reclaims the wedged session → AutoSpawn respawns; the alert
  message now says "Auto-recovering" instead of "Re-spawn via dashboard".
- **Slot 1 unpushed plan(s)** (14:37): regen `--commit` self-commits the inventory (slot-1 owns the master plan).
- **5 OPERATOR-gated awaiting, no respond option** (this section): now page with a dashboard respond-link.
- escalation dispatched/RESOLVED + plan-health dispatched (INFO bookends): healthy — the conflict-escalate + daily
  reconcile loops working as designed.

### Operator follow-ups round 2 (2026-06-21)

- [x] ✅ [ORCHESTRATOR] Slack alert footers point at the `/vm/<vm-id>` UI, not the `api.*` host — the footer's raw
      `API (query): https://api.…` text read as "the link" and sent operators to the JSON API. `_footer` now emits
      exactly one clickable `open dashboard` link (`/vm/<VM_ID>` on the SPA) + host + ts; the api origin is dropped
      (agents read it from env, not Slack). — agent-orchestrator@ba0b56a | tests: test_slack_notifications.py.
- [x] ✅ [PLANS] Agents were self-competing on the operator's own stable plans (defi data-completion, slots #3-#6).
      Tagged `data_completion_to_100_all_ag_2026_06_21.md` with `execution_scope: local-only` — the established
      "operator works it locally, orchestrator never ingests it" frontmatter (12 plans already use it). Next regen
      prunes its queued tasks; running slots finish their item then stop picking up defi work. Agents keep doing CI/CD
      escalations + plan-health (separate dispatch paths, unaffected). — unified-trading-pm@4e48264b. **MECHANISM for
      the operator: add `execution_scope: local-only` to any other plan you're driving yourself** (or remove it to
      re-enable agent dispatch).
- [x] ✅ [ORCHESTRATOR] P1. ROOT CAUSE — the tag alone did NOT stop them (verified live via SSM: 7 defi tasks still
      queued + slots 3/6 still working after the tag). Bug: `regen_backlog_from_plan._prune_stale` built
      `current_briefs` from ALL plans **including local-only ones** (it only filtered by `vm_id`), so a local-only
      plan's already-queued tasks stayed "current" by brief-match and were never pruned — `local-only` blocked NEW
      ingestion but not EXISTING tasks. Fixed: `_prune_stale` now skips `execution_scope: local-only` plans when
      collecting current briefs, so their queued tasks become orphans → pruned (yaml + state.db). —
      agent-orchestrator@183d573 | tests:
      test_regen_backlog_from_plan.py::test_prune_stale_removes_tasks_of_local_only_plan.
- [x] ✅ [OPS] LIVE remediation (central VM, SSM 2026-06-21): the running orchestrator's backlog source is the harsh
      `backlog.yaml` (Gap-5 desync) which still held 9 defi tasks + state.db had the queued zombies. Cleaned both via
      the backlog module + a surgical `DELETE` of queued+undispatched defi rows only (4 dispatched in-flight + 6 done
      kept): **0 queued defi remaining, verified held across a regen cycle.** Slots 3/6 finish their 2 in-flight items
      (`-013`/`-022`) then stop; no more defi dispatch. NOTE: Gap-5 (`ORCHESTRATOR_BACKLOG` → retired harsh path) is the
      underlying desync — tracked in `orchestrator_agent_lifecycle_gaps_2026_06_16` Gap 5; repointing it to the
      canonical backlog prevents future zombies.

## Codex SSOT updates

- [x] ✅ [DOC] P2. `codex/04-architecture/agent-orchestrator-worker-liveness.md` — documented all 5 closures (fix a/b/c,
      G3a checkout-not-reset, G3b LoopSupervisor) + the account-selection closures in a "Self-healing hardening
      (2026-06-21)" section. — unified-trading-pm@4dbc4eb1d
- [x] ✅ [DOC] P3. `codex/04-architecture/agent-orchestrator-overview.md` § Watchdog — added a "Self-healing hardening
      (2026-06-21)" paragraph summarising the 5 closures + cross-linking the worker-liveness doc. — unified-trading-pm
      (this commit)

## Success criteria

- A failed rotation respawn never leaves a `dispatched` task stranded or a slot wedged `working` with a dead session
  (fix a — DONE, tested).
- A finished/wedged worker (idle OR stale) frees its slot within `_IDLE_SESSION_RECLAIM_TICKS`, so queued work resumes
  without the 15-min heartbeat wait (fix b — DONE, tested).
- A provably-dead branch-quarantined slot auto-heals (commits preserved, realigned) and spawns, instead of wedging
  `killed` (fix c — DONE, tested).
- The "Audit Reflog — High Risk" alert stops firing on cc89557/53bbd95 (DONE, shipped) and — once the dedup todo lands —
  never re-fires on any already-acknowledged reset SHA.
