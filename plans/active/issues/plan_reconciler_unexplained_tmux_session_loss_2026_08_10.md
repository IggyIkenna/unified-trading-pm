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

- [ ] [BACKEND] P2. **Root-cause why `orch-slot-10` and `orch-slot-12`'s tmux sessions vanished between ~00:08:00 and
      00:16:51 UTC on 2026-08-10, with zero orchestrator-side kill-trigger log line, while ~25 sibling sessions spawned
      in the same window (incl. 2 more from the identical reconciler fire) survived.** Candidate angles worth checking
      first: (a) whether the specific `claude` CLI process for these panes crashed/exited on its own (a bug, a transient
      auth/session-id conflict, `--session-id` collision) rather than being killed externally — if so, tmux would
      auto-close the session absent `remain-on-exit on`, exactly matching the empty `pane_death_info` observed (session
      gone entirely, not a pane tmux could still query for an exit code); (b) whether `orch-slot-1` and `orch-slot-13`
      (also lost in the SAME 00:16:51 tmux_pruner discovery batch, a `data_pipeline_failure` custom agent for slot-13)
      share a common trigger with slot-10/12 — 4 sessions dying in the same ~9-minute window across 2 different agent
      kinds is a stronger signal than 2 isolated deaths; (c) whether `tmux_pruner`'s own sweep interval had a gap
      between ~00:08 and 00:16:51 (interval is nominally 60s) that let a genuinely-earlier death go undetected for
      longer than usual, vs. the sessions actually dying right at/after the 00:15:11-00:15:33 restart despite
      `KillMode=process`. **Done when**: either a concrete root cause is identified + fixed, or a documented
      negative-result investigation (checked X/Y/Z, none reproduce/explain it) with a monitoring recommendation (e.g. a
      `tmux_session_lost` rate canary analogous to `PlanReconcilerLivenessCanary`) is recorded. Repo:
      agent-orchestrator.
