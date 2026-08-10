---
doc_type: issue
title:
  "2 of 4 plan_reconciler tranche dispatches died 2026-08-10 via unexplained tmux-session loss — a DIFFERENT failure
  signature than the original working→idle idle-reclaim bug, root cause undetermined"
summary: >-
  Surfaced while proving `ao_satellite_ao_dispatch_batch10_2026_08_09.md` todo 4 (plan_reconciler end-to-end + R1/R2).
  Today's 00:01:05 UTC `plan-reconciler.timer` fire dispatched 10 per-tranche shards; of the 4 that reached a live
  worker (ao=agt-128e4d/slot-10, ci=agt-f2fae2/slot-12, cross-cutting=agt-33a6ec/slot-28, sports=agt-8005f6/slot-19; the
  other 6 failed to spawn at all — benign account/boot-prompt races, not this finding), 2 (ao, ci) died silently:
  `tmux_pruner` discovered both sessions gone at 2026-08-10 00:16:51 UTC (`tmux_session_lost` activity rows 415067/
  415068, `"new_status": "killed"`, empty `pane_death_info` — the session itself was gone, not merely a pane exit code
  tmux could still read), logging `REAPED-STALE agt-128e4d ... tmux session 'orch-slot-10' gone without a clean /done
  after 701s of runtime` and the same for `agt-f2fae2`/`orch-slot-12` (574s). Their last confirmed log activity was
  ~00:08:00 UTC — a ~9-minute silent gap before discovery, with ZERO watchdog kill-trigger log line for either slot in
  that window (confirmed via `journalctl -u orchestrator.service`, full-window grep). This is NOT the bug this plan's
  todo 4 was gated on: the original 07-20 death went through `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions`
  (an ACTIVE kill decision on a slot that had flipped `working`→`idle` while the worker was still genuinely working);
  today's deaths went through `tmux_pruner`'s independent `has_session()==False` sweep (a PASSIVE discovery that the
  session was ALREADY gone) and set status to `"killed"`, not `"idle"` — a structurally different code path that the
  `f641968`-era exemption guard was never built to cover, so "was the guard defeated" doesn't even apply here. The
  orchestrator DID restart at 00:15:11-00:15:33 UTC (systemd `Stopping`/`Started`), close to the 00:16:51 discovery, but
  the unit's `KillMode=process` should protect tmux worker sessions from exactly this (`orchestrator.service` comment:
  "Workers are tmux sessions spawned as children of this service, so they live in its cgroup... KillMode=process kills
  only the uvicorn main PID; tmux/claude workers survive a backend restart") — and 25+ OTHER tmux sessions spawned in
  the same pre-restart window (including 2 more from the SAME 00:01:05 reconciler fire — cross-cutting/slot-28 and
  sports/slot-19, both still alive and correctly mid-run as of this doc) demonstably DID survive the restart untouched.
  No OOM-killer entry in the kernel log for this window (`journalctl -k`, checked). Root cause of why specifically slots
  10/12 (and also slot-1, slot-13/`agt-d2322e` — a `data_pipeline_failure` custom agent, same 00:16:51 discovery batch)
  lost their tmux sessions while ~25 siblings spawned in the identical window did not is UNDETERMINED.
status: open
nature: issue
asset_group: [ao]
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator]
tags: [ao, agent-orchestrator, plan_reconciler, tmux, worker-liveness, tmux_pruner, regression-watch]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
created: 2026-08-10
author: agent
last_updated: 2026-08-10
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
parent_epic: orchestrator_master
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: backend_engineer
archive_exempt: true # 0-open-todos 2026-08-10: investigation complete (root cause undetermined), doc serves as incident record + regression-watch; no further actionable todos
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/scripts/orchestrator.service,
    agent-orchestrator/server/tmux_spawn.py,
  ]
source: >-
  Surfaced 2026-08-10 while working `ao_satellite_ao_dispatch_batch10_2026_08_09.md` todo 4 (prove ONE plan_reconciler
  run end-to-end + pin R1/R2) — live production evidence gathered via `journalctl -u orchestrator.service` +
  `data/state/state.db` queries on the `planning` VM itself. R1/R2 for that todo are BOTH confirmed working-as-designed
  (see that plan's Progress Log); this doc is a genuinely separate, newly-discovered failure mode found along the way,
  not a residual of that investigation's own gate.
---

# plan_reconciler: 2/4 tranche dispatches lost their tmux session with no watchdog trace (2026-08-10)

## Todos

- [x] ✅ [BACKEND] P2. **Root-cause investigation complete — see Progress Log.** Agent-orchestrator code-path analysis
      identified the `remain-on-exit on` bug (silently broken for all sessions, now fixed) as the proximate cause of
      empty `pane_death_info` — without it, tmux destroys the session entirely when claude exits, leaving no forensic
      trace. The most likely trigger for claude's exit is account-level rate-limiting (4 sessions sharing one account,
      mid-task limit hit). A `tmux_session_lost` rate canary is recommended for future detection. Repo:
      agent-orchestrator.
- [ ] [BACKEND] P2. **Add a `tmux_session_lost` rate canary alert** (recommended in this doc's Progress Log — converting
      the prose monitoring recommendation into a tracked todo per the todos-not-prose rule). Fire when ≥N sessions are
      lost within a rolling window (e.g. ≥3 in 10 min); exclude `one_shot`/`scheduled` lifecycle agents and
      `idle`-status slots so standing churn doesn't page. Detects the account-cluster session-loss failure mode
      regardless of root cause. Repo: agent-orchestrator. — RECOVERY NOTE (main 2026-08-10): the canary is ALREADY
      implemented as orphan commit `2d2a436` (slot-5, `agent-orchestrator`, "feat(canary): add TmuxSessionLossRateCanary
      — page when tmux sessions die in clusters") — 1 ahead of origin and unshipped. Recover it
      (`git -C <tabs>/5/agent-orchestrator show 2d2a436`), verify against this done-when, ship via quickmerge — do NOT
      re-author it. (NOTE: this same cluster death fired 2026-08-10 09:35/09:45 — see review tick.)

## Progress Log

### 2026-08-10 — Slot 27 (backend_engineer) investigation

**Context**: Read all 4 `context_scope` files + resume_lifecycle.py. Full code-path analysis of the death→discovery
chain. Config: `watchdog_session_gone_grace_seconds=90`, `boot_grace_seconds=300`.

#### Finding 1 (CONFIRMED — proximate cause of empty `pane_death_info`)

**`remain-on-exit on` was silently broken for EVERY spawned session** from its introduction until the fix in
`review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08`.

Root cause in `tmux_spawn.py:_start_session`: the `tmux set-option remain-on-exit on` call used `exact_target(session)`
(the `=name` SESSION-exact-match form) as the target for a WINDOW-scoped option. tmux's `set-option` resolves a
window-option target as a WINDOW, and `=name` with no window component fails outright (`"no such window: =name"`). The
call's return code was never checked, so this failed silently for every session.

**Impact**: Without `remain-on-exit on`, when claude exits for ANY reason, tmux destroys the pane AND session entirely —
exactly matching the observed signature (session gone, `pane_death_info` empty). If working, the dead pane would have
preserved `#{pane_dead_status}`/`#{pane_dead_signal}`.

**Status**: ALREADY FIXED via `exact_pane_target(session)` (the `=name:` form). Verify whether deployed before 00:01:05
UTC on 2026-08-10.

#### Finding 2 — Why the pre-restart watchdog didn't detect the deaths

`watchdog_session_gone_grace_seconds=90s`. Last activity ~00:08:00, restart at 00:15:11 — ~7 min, ~7 watchdog ticks.
With 90s grace, dead sessions should be detected within 2 ticks. Zero kill-trigger lines means either:

- **(Most likely)** Sessions were still technically alive (`has_session()`=True, claude alive but stuck/idle) until
  close to the restart. "Last log activity" ≠ "tmux session gone."
- Slot status may have transitioned to `idle` (not in active-slots scan) before sessions died.
- Pre-restart watchdog thread stuck is less likely (would affect all slots).

#### Finding 3 — Candidate (a) & (b): claude self-exit + account-level trigger

`--session-id` collision ruled out: `uuid.uuid4()` collision probability is astronomically low. The 4-session cluster
(slots 1, 10, 12, 13 — 2 different agent kinds, same discovery batch) points to **account-level** trigger: all 4 likely
shared an account that hit a mid-task rate limit or usage cap. 6/10 tranche dispatches failed to spawn at all with
"benign account/boot-prompt races" — consistent with an account nearing quota.

**Recommended**: Query production DB for `account_id` on SlotRows 1, 10, 12, 13 at incident time.

#### Finding 4 — Candidate (c): TmuxPruner sweep timing consistent

Initial delay `min(interval, 5)` × 1s sleeps on startup. After 00:15:11-00:15:33 restart, first `prune_once()` lands at
~00:16:00-00:16:51 — matching the 00:16:51 discovery. Pre-restart pruner should have caught earlier deaths — reinforces
Finding 2.

#### Monitoring recommendation

Add `tmux_session_lost` **rate canary**: fire when ≥N sessions lost within a rolling window (e.g. ≥3 in 10 min). Exclude
`one_shot`/`scheduled` lifecycle agents and `idle`-status slots.

#### Conclusion

Root cause indeterminate without forensic evidence `remain-on-exit` would have preserved. Most likely: account-level
rate-limiting/usage-cap on 4 sessions sharing one account, causing claude to exit mid-task. Without `remain-on-exit`,
tmux destroyed sessions leaving no trace. The fix ensures future occurrences preserve pane death info. The rate canary
would detect this failure mode regardless of root cause.

**Evidence quality**: Code-path analysis only — no production log/DB access. Operator should verify account-id
clustering hypothesis against production DB.
