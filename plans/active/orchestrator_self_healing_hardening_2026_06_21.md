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

- [x] ✅ [ORCHESTRATOR] P0. **Orphan-wip inherit realigns even when a prior `wip-preserve` ref exists — the ROOT CAUSE
      of the "Slot 4 quarantined — escalation wall starved" alert (2026-06-21 15:57).** The respawn-hygiene inherit path
      (`_orphan.py`) committed a dead predecessor's WIP, then pushed it to a FIXED-name
      `wip-preserve/orchestrator-slot-<N>` ref with `--force-with-lease` and **only realigned the slot to
      `origin/<base>` inside the push-success branch**. That ref already existed from an earlier inherit (`f19aca03`),
      and a Path-B slot has no `refs/remotes/origin/wip-preserve/orchestrator-slot-<N>` tracking ref to satisfy the
      lease → **push REJECTED → realign SKIPPED → the slot was left at the orphan commit on a stale base = DIVERGED
      (ahead 1 / behind 82) → FM5 quarantine → the queued escalation it should have handled was starved.** Fix: a
      **content-unique** preserve ref `wip-preserve/orchestrator-slot-<N>-<sha>` + a **plain push** (a ref named by the
      orphan's own SHA never collides destructively — new content creates it, a retry is `Everything up-to-date`/rc 0),
      so the push always succeeds and the realign (fetch + `checkout -B`, audit-quiet) always runs. The slot is never
      left diverged. — agent-orchestrator@9a09c42 | tests: test_dirty_state_resolution.py
      (`test_resolve_pathb_realigns_even_when_prior_preserve_ref_exists` regression + prefix-match update)
- [x] ✅ [OPS] P0. **Live central-VM remediation (slot-4 incident, 2026-06-21 16:00-16:42).** (1) Manually recovered the
      wedged slot — preserved the orphan commit `c16b36a8` to `wip-preserve/slot-4-orphan-2026-06-21T1557Z`, realigned
      to `origin/live-defi-rollout` (clean, ahead 0/behind 0). (2) Diagnosed why Fix (c)'s auto-heal had NOT recovered
      it: the **running orchestrator PROCESS (started 11:45 UTC) was executing stale in-memory code from before today's
      heal-wiring landed** — the heal was on disk (`b02d65f`) + on LDR but never loaded (proven by the live log emitting
      the pre-heal `(FM5/FM7): {branch dict}` message, not the wired `auto-heal failed: {heal dict}`). (3)
      `pull --ff-only` the service repo to `9a09c42` + `systemctl restart orchestrator.service` (per `agents/main.md`).
      Post-restart verified: all 13 daemon loops up; **the heal is now live and already auto-realigned slot 1**
      (`wrong_branch ->     origin/live-defi-rollout`, the operator's earlier slot-1 quarantine alert); slot 4 `working`
      on `data_completion_to_100_all_ag-009`, all 24 repos clean; 0 open escalation tasks; no new branch-quarantine
      alerts.

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

## Operator follow-up (2026-06-22) — account auth-failure eviction + outage-safe detection

**Operator request (2026-06-22):** when an account is disabled (org turns off Claude Code — e.g. sub-b-iggy2london:
"Your organization has disabled Claude subscription access for Claude Code"), the orchestrator must (1) stop using it
for NEW spawns AND (2) **divert the agents already running on it** to a working account. **Caveat (operator):** a
_missing heartbeat_ must NOT be presumed an account-auth failure — Claude's backend has outages, and a good account must
not be marked bad on a blip; it must be reused once the servers recover. All accounts can be down simultaneously.

### What already exists (verified 2026-06-22 — do NOT rebuild)

- **Detection is authoritative + already classified:** `usage_poller` probes `/usage` per account per tick and
  CLASSIFIES the failure — HTTP **401/403 → `mark_account_auth_failed`** (confirmed token-rejected/disabled); **429 →
  `mark_account_rate_limited`**; **5xx / network / timeout → NOTHING** (explicit code comment: "transient; do NOT
  auth-alert (avoid false positives on a blip)"). So an outage already does NOT mark a good account bad — the caveat's
  core is satisfied at the detection layer.
- **New-spawn avoidance (requirement 1 — DONE):** `account_is_usable` excludes auth-failed-in-cooldown + rate-limited +
  disabled → `pick_headroom_account`/`pick_next_account` skip a bad account.
- **Auto-recovery (the "reuse when servers recover" — DONE):** auth_failed accounts are held out only for an exponential
  cooldown (`AUTH_FAILED_COOLDOWN_BASE_SECONDS=600` → 6h cap), re-enter the pool for a re-probe after, and are CLEARED
  on the next successful probe (`_clear_auth_failed_db`) or a successful worker heartbeat (`slots_worker.py` healing
  path → `clear_account_auth_failed`).
- **Eviction primitive (the fan-out — EXISTS):** `rotate_all_slots_off_account(account_id, *, trigger)` diverts EVERY
  running slot off an account → next usable account (resume-respawn via `spawn_with_account_bg`), with the
  **global-outage guard already built in** (`pick_next_account is None` → logs `account_rotation_no_fallback`, does NOT
  kill) and **no-op-after-moved** (safe to call every tick). `RotationReason` enum already has `auth_failed`;
  `notify_account_rotated` already renders it.
- **All-accounts-down page:** `_fire_all_accounts_down_if_needed` + `all_accounts_unusable` fire one Slack page when
  every account is unusable (reset on ≥1 recovery).

### Gaps (precise — these are the only things to build)

1. **The poller marks auth_failed + pages but does NOT fan out the eviction.** `rotate_all_slots_off_account` is wired
   only to rate-limit/cap triggers (`tmux_pruner` pane-scan, `/api/accounts/.../rate-limited` manual-report,
   usage-refresh) — never to the poller's confirmed-401/403 path. So agents already running on a disabled account are
   NOT diverted; they wedge individually and recover only slowly via the heartbeat-silent reap. **This is requirement
   (2), unfulfilled.**
2. **The spawn-heartbeat watchdog PRESUMES auth_failed on a bare timeout**
   (`_auth_failover.check_spawn_heartbeat_timeouts` → `mark_account_auth_failed`) — exactly the operator's caveat
   violated. During an outage every spawn timeout false-marks its account + churns rotations.
3. **The main-agent keeper has no auth_failed branch** — `main_agent_keeper` fails over only on usage caps
   (`pick_headroom_account` at the cap modal), so a disabled account under the main agent is never diverted.
4. `rotate_all_slots_off_account` hardcodes `RotationReason.rate_limit` — an auth_failed eviction would mis-log /
   mis-alert as a rate-limit.

### Design invariant (operator 2026-06-22 — enforce in code + tests)

**"Account-bad" is a POLLER verdict (classified 401/403), never a heartbeat inference.** Eviction/diversion fires ONLY
on `account_status == "auth_failed"` as set by the poller. A missing heartbeat triggers liveness recovery
(retry/resume), NEVER an account-bad mark. When there is no usable account to divert to (single-account or fleet-wide
outage), DO NOT churn — leave agents in place, fire the all-accounts-down page once, and auto-resume when the poller
clears the flag on recovery.

### Phased todos

- [x] ✅ [ORCHESTRATOR] P1. **Task A — parametrize the eviction primitive.** Added
      `reason: RotationReason =     RotationReason.rate_limit` to `rotate_all_slots_off_account` (`server/server.py`);
      threaded into both `log_activity` `rotation_reason` fields, the `account_rotation_no_fallback` log, and
      `fire_rotation_alert`. Back-compat default keeps the 3 existing rate-limit callers unchanged. —
      agent-orchestrator@30c2828c
- [x] ✅ [ORCHESTRATOR] P1. **Task B — wire poller-confirmed auth_failed → eviction fan-out (requirement 2).**
      `UsagePoller._evict_slots_on_auth_failed(account_id)` (lazy-import + try/except, never raises) folded into
      `_mark_auth_failed_db` (covers both the 401/403 + no-token sites), with
      `reason=RotationReason.auth_failed, trigger="poller-auth-failed"`. Relies on the primitive's built-in
      global-outage guard + no-op-after-moved. — agent-orchestrator@30c2828c
- [x] ✅ [ORCHESTRATOR] P1. **Task C — harden the spawn-heartbeat watchdog (the operator's caveat).**
      `_auth_failover.check_spawn_heartbeat_timeouts` NO LONGER marks `mark_account_auth_failed` on a bare timeout. On
      timeout: if the account is ALREADY poller-confirmed `account_is_auth_failed` → DEFER to the poller's eviction (no
      respawn here, no retry burn); else → retry-respawn on the SAME account (`reason="spawn_timeout_retry"`), bounded
      by `spawn_retry_count`. Activity relabelled (`spawn_heartbeat_retry` /
      `spawn_heartbeat_deferred_to_poller_eviction`). `account_status == "auth_failed"` is now a poller-only signal. —
      agent-orchestrator@30c2828c
- [x] ✅ [ORCHESTRATOR] P1. **Task D — keeper auth_failed branch for the main agent.**
      `main_agent_keeper._handle_auth_failed_account` (runs before the usage-cap modal check) fails main over off a
      poller-confirmed auth_failed account: kill + `--resume` on a usable account (re-points `AgentRow.account_id` to
      prevent a re-failover loop) / kill-for-fresh (no sid) / leave-in-place (no usable account → global-outage guard).
      — agent-orchestrator@30c2828c
- [x] ✅ [ORCHESTRATOR] P2. **Task E — global-outage safety (core verified).** Tests lock: transient/timeout/5xx marks
      NO account + evicts NO slot (`test_transient_error_does_not_evict_slots`); no-usable-account → keeper does NOT
      kill (`test_auth_failed_account_no_usable_left_in_place`); `rotate_all_slots_off_account`'s `next_acc is None`
      guard + `_fire_all_accounts_down_if_needed` are pre-existing. **Stretch SPLIT to a follow-up** (see below). —
      agent-orchestrator@30c2828c
- [x] ✅ [ORCHESTRATOR] P1. **Task F — tests.** New `test_spawn_heartbeat_liveness.py` (retry-same / defer / heartbeated
      no-op, never-marks) + poller eviction tests (`_evict_slots_on_auth_failed` reason, `_mark_auth_failed_db` fan-out,
      skip-on-mark-raise, transient-no-evict) + keeper auth_failed tests (resume / no-usable-frozen / no-sid-fresh /
      healthy-no-failover). Full QG green: **819 passed, 1 skipped**; dashboard tsc + 51 vitest green. —
      agent-orchestrator@30c2828c
- [x] ✅ [ORCHESTRATOR] P3. **Task E stretch — transient fleet-wide-outage detector + page (SHIPPED 2026-06-22).** The
      usage poller now tallies per-tick reachability (`n_probed` / `n_success` / `n_transient_fail`; a 5xx and a
      network/timeout each count transient, 401/403/429 do not) and `_check_likely_outage` fires a distinct disk-deduped
      `notify_likely_claude_outage` page on the clean all-transient signature
      (`n_probed > 0 and n_success == 0 and n_transient_fail == n_probed`), re-arming on the next successful probe. A
      mixed tick (some 401/403 + some transient) neither fires nor re-arms (the marked accounts are the
      all-accounts-down page's job). NO account is marked (operator caveat: a transient outage is not an account fault);
      agents auto-resume on recovery. Routes to Slack #agent-orchestrator-alerts (sibling of
      `notify_all_accounts_unusable`) with an `/accounts` deep-link. — agent-orchestrator@d35c0f09 | tests:
      test_usage_poller_auth_failover.py (+6 cases)
- [x] ✅ [DOC] P2. **Codex SSOT.** Documented the auth-failure eviction flow + the "missing-heartbeat-is-not-auth"
      invariant + global-outage guard + auto-recovery in `codex/04-architecture/agent-orchestrator-worker-liveness.md` §
      "Account auth-failure eviction" + a pointer paragraph in `agent-orchestrator-overview.md` § Watchdog. —
      unified-trading-pm (this commit)

#### Deploy-currency + SQLite hardening (operator 2026-06-23 follow-ups)

- [x] ✅ [OPS] P1. **Deploy-currency wedge alert.** `ao-self-pull.sh` IS scheduled `*/15` (root crontab) + ff-pulls +
      restarts-on-change — but its dirty-gate skips SILENTLY, so a stray dirty `quality-gates-v2.yml` left the
      orchestrator 128 commits behind LDR on stale code, unnoticed (logged only to a file). Added `_alert_wedge`: a
      deduped Slack alert when the self-pull is wedged (dirty/diverged) AND the clone is ≥`AO_DRIFT_ALERT_COMMITS`(10)
      behind LDR — a wedge can never silently drift again. The clone is unwedged + current now (my redeploy stashes
      cleared the dirty `v2.yml`). — agent-orchestrator@77f1873e
- [x] ✅ [ORCHESTRATOR] P2. **SQLite raw-connection busy_timeout.** The main engine (db.py) already has WAL + 120s
      busy_timeout, but two raw `sqlite3.connect()` hot-backup connections in `gcs_sync.py` bypassed it (could
      `database is locked` under writer contention); added `PRAGMA busy_timeout=120000` to both + bumped
      `regen_backlog`'s 30s→120s for parity. The residual boot-spawn-storm lock-STACKING (a spawn holds BEGIN IMMEDIATE
      across the ~75s tmux spawn; stacked spawns exceed 120s) is the separate tracked **spawn-outside-txn** refactor
      (`orchestrator_spawn_reliability_db_lock_2026_06_10`) — transient/non-fatal, the real fix is a careful follow-up.
      — agent-orchestrator@77f1873e

### Incidental finding (2026-06-23) — S3 state-snapshot backup failing (region mismatch)

- [ ] [ORCHESTRATOR] P2. **Off-VM state-snapshot backups to S3 are failing (resilience gap, pre-existing).** The
      auto-snapshot loop writes local `data/state/state.json` fine, but the S3 upload fails:
      `NameResolutionError: Failed to resolve 'uts-orchestrator-state-427895769566.s3.asia-northeast1.amazonaws.com'` →
      `s3_uri: None`, and `aws s3 ls …/snapshots/planning/2026-06-23/` is EMPTY (no snapshots land). Root cause: the
      cloud-agnostic config feeds the **GCP** region name `asia-northeast1` to the **AWS** S3 client, which needs
      `ap-northeast-1` (AWS Tokyo) — so the endpoint hostname is invalid. The orchestrator runs fine on local state, so
      this is non-urgent, BUT on a VM loss the state can't be recovered from S3. Likely fix: set
      `AWS_REGION=ap-northeast-1` for the orchestrator (verify the bucket's region first via
      `aws s3api     get-bucket-location`) OR fix the per-cloud region mapping in the S3 client construction. Owner:
      ops/operator.

## Success criteria

- An account disabled mid-run (poller 401/403) → every running agent on it (workers via `rotate_all_slots_off_account`,
  main via the keeper) is diverted to a usable account within ~1 poll tick; it is excluded from new spawns; it
  auto-recovers into the pool when re-enabled (poller clears on the next good probe).
- A missing heartbeat NEVER marks an account auth_failed (poller-only verdict); a Claude server outage does not sideline
  any good account.
- When no usable account exists (single or fleet-wide outage), no agent is killed/churned; the all-accounts-down page
  fires once; agents auto-resume on recovery.

## Codex SSOT updates

- [x] ✅ [DOC] P2. `codex/04-architecture/agent-orchestrator-worker-liveness.md` — documented all 5 closures (fix a/b/c,
      G3a checkout-not-reset, G3b LoopSupervisor) + the account-selection closures in a "Self-healing hardening
      (2026-06-21)" section. — unified-trading-pm@4dbc4eb1d
- [x] ✅ [DOC] P3. `codex/04-architecture/agent-orchestrator-overview.md` § Watchdog — added a "Self-healing hardening
      (2026-06-21)" paragraph summarising the 5 closures + cross-linking the worker-liveness doc. — unified-trading-pm
      (this commit)

## Live incident + fix (2026-06-22 evening) — slot-3 "Auto-respawn FAILED" spam + cap-burn

**Symptom:** `agent-orchestrator-alerts` fired "Auto-respawn FAILED slot 3 — kick failed, pane='frozen', last_ping>15m /
Attempted: branch-state quarantine (FM5/FM7); respawn skipped" every ~2 min. Root cause: slot-3's `instruments-service`
clone was left on a leftover `_tmp-stage-rebase2` branch (clean, fully merged to origin) from an isolated-worktree
promote → FM7 `wrong_branch` → `should_stop` → the watchdog skipped respawn + paged. Compounded by the watchdog daily
kill-cap (20) being burned by frozen-slot churn → dormant-until-UTC-midnight → fleet stranded.

- [x] ✅ [OPS] P0. **Immediate recovery (live, central VM).** Cleaned slot-3's leftover `_tmp` branch (verified 0
      unpushed-unique commits first); raised `ORCHESTRATOR_WATCHDOG_DAILY_CAP` 20→**50** in `.env.local` (operator
      request) + restarted the orchestrator → dormancy cleared, watchdog resumed, fleet recovered (slots 1/3/5/6 fresh)
      on **dynamically-selected** healthy accounts (`_pick_headroom_account` — not hardcoded; sub-d@100%/auth-failed
      excluded, re-funded accounts auto-rejoin). — central-VM SSM.
- [x] ✅ [ORCHESTRATOR] P1. **FM7 auto-reclaim of a leftover clean+fully-merged throwaway branch** (the slot-3
      respawn-blocker, made automatic). `_branch_state.py::_reclaim_leftover_merged_branch` — a leading-`_` throwaway
      branch (`_tmp-*`/`_backmerge`) that is CLEAN **and** an ancestor of `origin/<base>` (0 unpushed) auto-switches
      back to `<base>` + deletes the leftover (new `reclaimed` non-stop status); a dirty tree, unpushed work, or a
      deliberate branch (`feature/*`, `main`) still STOPs (never loses work). + `config.py` `watchdog_daily_cap` default
      20→50. 5 regression tests (`tests/test_branch_state_reclaim.py`), QG-green. — agent-orchestrator@76970857

### DEPLOY BLOCKER — central-VM orchestrator clone is 128 commits stale + the new code has 2 deploy-time incompatibilities

The deploy clone (`/home/ubuntu/.../agent-orchestrator`, runs the live brain) is **128 commits behind**
`origin/live-defi-rollout` (predates the entire `utl_uac` typed-config refactor) with **no auto-deploy cron**, so the
FM7 fix above is NOT live on the running orchestrator. Two safe-gated catch-up attempts (ff-pull → dry-run → restart →
rollback) on 2026-06-22 surfaced **two distinct new-code incompatibilities with this VM's setup**. Each attempt was
cleanly rolled back to `980217d`; the fleet stayed healthy (4 usable accounts, spawning) on the old code throughout. The
safe-gate (running service untouched until a verified restart) worked as designed.

- [x] ✅ [OPS] P1. **Blocker 1 — GCS internal-key read (SOLVED + validated).** The VM authenticates to GCP with
      `ikenna@odum-research.com`'s **`authorized_user`** ADC (`gcloud auth application-default login`), not a
      service-account. UTL's `cloud_interface/providers/gcp.py::_get_native_client` does
      `storage.Client.from_service_account_json(creds_path)` **whenever `GOOGLE_APPLICATION_CREDENTIALS` is set** —
      which chokes on the authorized_user file (`MalformedError: missing token_uri, client_email`).
      `get_credentials_path()` = `os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")`, so **unsetting that env var** makes
      it fall to `storage.Client(project=…)` default ADC, which loads the same authorized_user creds from the well-known
      path. VALIDATED on the VM:
      `get_storage_client(provider="gcp").download_bytes(orchestrator-creds, internal-private.pem)` → `bytes=241` with
      the env var unset. Fix = remove the (redundant) `GOOGLE_APPLICATION_CREDENTIALS` line from the central VM's
      `.env.local`.
- [x] ✅ [UTL] P1. **Blocker 1b — UTL hardening (SHIPPED).** `_get_native_client` now only calls
      `storage.Client.from_service_account_json` when the creds file is an actual service-account key
      (`type == "service_account"`); a user/authorized_user ADC (or no path) goes through `storage.Client(project=…)` →
      `google.auth.default()`, which handles both cred types — so a user-ADC host works without the env-unset
      workaround. `_is_service_account_json` helper + 2 regression tests (real SA → `from_service_account_json`;
      authorized_user ADC → default path), QG-green. — unified-trading-library@5e413c7f
- [ ] [OPS] P1. **Blocker 2 — account roster file (ROOT CAUSE NAILED; operator-domain fix).** The new code REQUIRES an
      explicit `oauth_token_env_file` per account; the **old code derived** the token path by convention
      (`~/.claude-accounts/<id>.env`), so it spawns fine without the field. The running 4-account state (sub-a/b/c/d,
      from the DB/snapshot) lacks `oauth_token_env_file` → new code = `ACCOUNT POOL EXHAUSTED`. The correctly-schema'd
      roster (WITH `oauth_token_env_file`) lives at **S3 `s3://uts-orchestrator-creds-427895769566/config/accounts.json`
      but is STALE** (2026-05-22; only 3 accounts — sub-a/b/c, missing sub-d) AND is **not present locally** at
      `data/config/accounts.json` (the new code's read path — only `accounts.mock.json` is there; the live one is
      operator-edited/committed and went missing). All 4 token `.env` files exist in `~/.claude-accounts/`. **Fix: place
      a current `data/config/accounts.json` with all 4 accounts each carrying
      `oauth_token_env_file:     ~/.claude-accounts/<id>.env`** (+ refresh the stale S3 copy to match). The schema is
      known (matches the S3 copy); the roster (which accounts / limits / sub-d) is the operator's live account config —
      confirm the roster, then the redeploy runs both validated fixes (unset `GOOGLE_APPLICATION_CREDENTIALS` + this
      file) safe-gated. Owner: operator (account roster).
- [x] ✅ [OPS] P2. **Redeploy DONE (2026-06-23).** Both fixes applied (restored S3 `config/accounts.json` → local
      `data/config/accounts.json` per operator; unset `GOOGLE_APPLICATION_CREDENTIALS`) + ff-pull to current LDR +
      restart. New code LIVE (`a169552`) with the FM7 fix + cap-default + 128 commits: 3 accounts loaded WITH
      `oauth_token_env_file`, no MalformedError, no pool-exhausted, fleet spawning (slots 1/2/3 + agent-main). The
      boot-time `sqlite3 database is locked` tracebacks are transient WAL contention during the spawn-storm — settled.
      **TODO still open: an AO deploy cron** so the brain doesn't silently drift stale again.

### Account self-recovery — poll + auto-clear a returned account (operator 2026-06-23: "it should be polling and checking itself")

- [ ] [ORCHESTRATOR] P1. **Two self-recovery bugs found + fixed.** When sub-b-iggy2london came back up, it stayed
      `auth_failed` (not auto-reused). Root causes: **(1) route gap** — `/api/accounts/{id}/refresh-usage`
      (`routes/accounts.py`) updated usage on a successful probe but **never called `clear_account_auth_failed`** (a
      manual refresh updated usage 43→19% but left `auth_failed` set), unlike the poller's `_tick_once` which clears on
      success; **(2) latency** — `UsagePoller` re-probes every account only every **30 min**
      (`DEFAULT_INTERVAL_MINUTES`), so even with the clear-on-success a returned account waited up to 30 min. Fixes: (a)
      route now `ss.clear_account_auth_failed` on a valid probe (parity with the poller); (b) new
      `UsagePoller._reprobe_unhealthy_once` runs every `_FAST_REPROBE_SECONDS=120` between full ticks, re-probing ONLY
      `auth_failed`/`rate_limited` accounts and clearing them on a successful probe → a returned account self-heals
      within ~2 min, no manual `/refresh-usage`. 3 regression tests. — agent-orchestrator (shipping)

### Operator review (2026-06-23) — incident-cluster hardening (fleet-resilience + outage-recovery + carve-out QG)

Source: 2026-06-23 operator-requested codebase + boot-prompt review after a 3-incident day — account exhaustion →
Anthropic server OUTAGE → a slot-22 `carveout=scripts` commit reddening PM's gate, which **starved the whole fleet**.
Account-exhaustion is already closed (rotation headroom-gate `agent-orchestrator@f296fd4`, failover plan Phase 6) + the
account self-recovery above; outage _detection_ is Task E. These close the remaining **fleet-resilience**,
**outage-RECOVERY**, and **carve-out-QG** gaps. Boot-prompt audit verdict: `worker.md` DOES carry the Pass-1 QG → Pass-2
quickmerge contract (lines 245-262) — the gaps are a stale section + a lane that skips the sentinel, below.

- [x] ✅ [ORCHESTRATOR] P0. **Fleet-resilience — a red PM gate must NOT starve dispatch.** — agent-orchestrator@5406c93
      (`_resolve_plans_dir` snapshots `plans/active` from `origin/live-defi-rollout`, working-tree fallback; +2 tests).
      slot-22's `carveout=scripts` commit `unified-trading-pm@2dc131639` (lifecycle-marker frontmatter on 493 scripts)
      reddened PM `quality-gates-v2` (PR #506 LDR→main) on pre-existing ratchet debt → PM `main` blocked → fleet
      dispatch starved (the central VM's PM clone tracks `main`; `regen_backlog_from_plan` reads its `plans/active/`, so
      a stuck `main` froze the backlog for everyone). Decouple dispatch from PM-`main` currency:
      `regen_backlog_from_plan` reads the PM clone's `live-defi-rollout` content (or falls back to it when `main` is
      behind LDR), so a blocked PM gate degrades gracefully — work keeps dispatching from LDR plans instead of freezing
      the fleet. Repo: agent-orchestrator (`server/regen_backlog_from_plan.py`). +regression test.
- [x] ✅ [ORCHESTRATOR] P1. **Carve-out pushes must still pass LOCAL QG — RESOLVED-BY-DIAGNOSIS (NOT a bug;
      2026-06-24).** The premise was wrong. Verified: PM's `quickmerge` REQUIRES the `.qg_last_passed_sha` sentinel (PM
      has `scripts/quality-gates.sh`; the agent-mode fast-path at `quickmerge.sh:1217+` verifies sentinel==HEAD with NO
      carve-out bypass — grep confirms the only `carve` mention is an unrelated early-exit comment). So slot-22 did NOT
      skip local QG. Its `carveout=scripts` commit `2dc131639` ran local QG, which PASSED on a **warm basedpyright
      incremental cache** — the failure surfaced only on CI's **cold** checkout (full re-typecheck). The real gap is the
      basedpyright local-warm-vs-CI-cold divergence + recurring ratchet trap → that is the item below, NOT a carve-out
      QG-bypass. No code change needed here.
- [x] ✅ [ORCHESTRATOR] P1. **Outage-aware flap-guard + force-resume-on-recovery.** — agent-orchestrator@039889b
      (main-keeper + review-ensure flap-guards now gate on `autospawn.outage_active` (the poller's likely-outage
      sentinel); failures during an active outage don't trip/are released → agents respawn within one keeper tick of
      recovery, not after a stale 1h backoff. AutoSpawn workers were already fine. Force-resume deemed unnecessary: the
      ≤60s keeper tick after the poller clears the sentinel (≤120s reprobe) gives ≤~3min recovery vs the old ~1h. +2
      tests.) Outage DETECTION exists (Task E: 5xx/timeout/connection = transient, never `auth_failed`/`rate_limit`;
      `_check_likely_outage` pages once). The RECOVERY gap (the "by the time they came online the test was over"
      symptom): repeated spawn failures INTO a known outage trip the 1h flap-backoff, and there is NO "outage cleared →
      release backoff + force a spawn tick" signal → agents sit in backoff after the API returns. Fix: (a) the
      flap-guard does not count spawn failures that occur during an active likely-outage window; (b) the poller's
      recovery signal (first successful re-probe / `clear_likely_outage_alerted`) clears `_flap_backoff_until`
      fleet-wide + triggers an immediate AutoSpawn tick, so agents resume within seconds of recovery, not after a stale
      1h backoff. Repo: agent-orchestrator (`server/autospawn.py` + `server/usage_poller.py`). +tests.
- [x] ✅ [CICD] P1. **basedpyright ratchet/cache fragility — DIAGNOSED + interim fix SHIPPED
      (`unified-trading-pm@22b2f89d7`, PR #523): basedpyright is now WARN-ONLY for PM `scripts/` (removed the 1555
      ceiling — operator decision 2026-06-24), permanently ending the recurring fleet-tripping ratchet-bump. Longer-term
      exclude-scan-vs-annotate is a P3 NICE-TO-HAVE in the owner plan. ROUTED to
      `pm_scripts_typecheck_debt_2026_06_11.md` (2026-06-24).** VERIFIED root cause (not inference): the slot-22 drain
      failed PM `quality-gates-v2` at the **`QG slice (lint-codex)`** step; the unblock was commit `1e6ec188e` _"bump PM
      basedpyright ratchet 1539→1555 — frontmatter cache-bust surfaced pre-existing debt"_. The ratchet has been bumped
      **four times** (1511→1517→1523→1539→1555) — `quality-gates.sh`'s own comments name the **recurring trap**: PM's
      _metadata-only fast-path skips the full basedpyright typecheck_ on docs/plan merges, so `scripts/` typing debt
      accumulates invisibly, then any full run (cache-bust / unblocked drain / scripts change) surfaces it all at once →
      red gate → ratchet bump. The incident itself is **MITIGATED** (ratchet at 1555; PM `quality-gates-v2` green on the
      latest runs). The DURABLE fix is a **design fork with fleet blast-radius** (rule 11) — NOT a safe speculative
      autonomous edit — and contradicts the lifecycle-marker SSOT (`scripts/` = ruff YES / basedpyright NO): options are
      (a) annotate the ~1555 `scripts/` reportUnknown\*/reportAny to ratchet → 0, (b) exclude PM `scripts/` from
      basedpyright per the SSOT, or (c) run the full typecheck on the fast-path so debt is caught incrementally. This
      belongs to the **existing owner plan `plans/active/issues/pm_scripts_typecheck_debt_2026_06_11.md`** (already
      tracks "ratchet back down") — folded there rather than duplicated here; the SSOT-vs-QG contradiction + the
      fast-path-skip recurring-trap diagnosis are the new inputs for that plan's decision.
- [x] ✅ [ORCHESTRATOR] P2. **`worker.md` stale G6 section.** — agent-orchestrator@5406c93 (replaced the retired AO
      `check.sh`/direct-push exception with the standard Pass-1 QG → Pass-2 quickmerge flow). Lines ~281-291 still
      describe the retired AO "no `staging` branch yet / use `check.sh` / quickmerge not wired" exception — AO migration
      is COMPLETE (staging + `quickmerge.sh` are live on AO). A worker following it would mis-ship AO. Replace with the
      standard Pass-1 `quality-gates.sh` → Pass-2 `quickmerge --agent --files` flow, same as any repo. Repo:
      agent-orchestrator (`agents/worker.md`).

## Success criteria

- A failed rotation respawn never leaves a `dispatched` task stranded or a slot wedged `working` with a dead session
  (fix a — DONE, tested).
- A finished/wedged worker (idle OR stale) frees its slot within `_IDLE_SESSION_RECLAIM_TICKS`, so queued work resumes
  without the 15-min heartbeat wait (fix b — DONE, tested).
- A provably-dead branch-quarantined slot auto-heals (commits preserved, realigned) and spawns, instead of wedging
  `killed` (fix c — DONE, tested).
- The "Audit Reflog — High Risk" alert stops firing on cc89557/53bbd95 (DONE, shipped) and — once the dedup todo lands —
  never re-fires on any already-acknowledged reset SHA.
