---
doc_type: issue
title:
  "A killed/idle one-shot slot holding committed-but-unpushed work has no automated push-or-inherit path — the commits
  sit at drift_violation indefinitely when the backlog is gate-dominated"
summary:
  slot16 spent ~3h (03:28-06:38Z 2026-07-21) in a frozen-kick loop (watchdog soft-kicked ~55 times — 29 worker_kicked +
  19 worker_polling_dead + 7 worker_kick_failed, post_kick_classification=frozen every ~5-6 min — before it finally
  escalated to a hard-kill) and left 4 committed-but-unpushed commits behind (agent-orchestrator ahead=2,
  unified-trading- pm diverged=2, on the active plan ao_uniform_agent_liveness_contract_2026_07_20.md). After the
  hard-kill the slot went killed -> idle with worker_alive=false. There is no automated path that pushes those commits -
  orphan_reap.py has no git logic (it reaps processes/tmux only), git_health.py only _maybe_send_sync_nudge()s a LIVE
  worker (a dead worker's nudge is a no-op), and with a gate-dominated backlog (13/0/13, zero dispatchable) AutoSpawn
  has no task to re-occupy slot16 with, so no live worker ever lands on the clone to push. The work is durable
  (committed in the slot's local .git, not lost unless the clone dir is wiped) but stranded off-origin at a standing
  drift_violation. Operator was already notified via the server's own unpushed_plans_alert_sent (06:02Z).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, self-healing, watchdog, git-drift, orphaned-work, recovery-gap, liveness]
related:
  [
    plans/active/ao_uniform_agent_liveness_contract_2026_07_20.md,
    plans/active/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-07-21
priority: P2
parent_epic: infrastructure_master
source: "review(slot1) msg 1538 to main orchestrator + main live diagnosis, 2026-07-21"
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## What happened

review(slot1) flagged (msg 1538, 06:37Z) that slot16 had been stuck in a frozen-kick loop for 3+ hours. Timeline
reconstructed from the event stream + live /api/state and /api/fleet/git-health:

- slot16 was a one-shot cicd-escalation dispatch (agt-a2c243, already resolved); a stray backlog task was then
  heartbeat-dispatched onto it in error and skipped.
- 03:49Z watchdog hard-killed once (stuck_at_prompt, kills_today=1/50); 03:50Z tmux_session_lost.
- 03:50Z -> 06:32Z: ~55 recovery events (29 worker_kicked + 19 worker_polling_dead + 7 worker_kick_failed),
  post_kick_classification=frozen every ~5-6 min, **zero progress** — the soft-kick/reap cycle kept firing without
  recovering the worker.
- ~06:38Z watchdog finally escalated to a hard-kill: slot went worker_alive=false, tmux_alive=false, status=killed, then
  status=idle.
- Throughout, slot16 held committed-but-unpushed work: agent-orchestrator state=ahead ahead=2, unified-trading-pm
  state=diverged ahead=2 (origin advanced past it, so pm now needs a rebase), on
  ao_uniform_agent_liveness_contract_2026_07_20.md. Server sent unpushed_plans_alert_sent at 06:02Z.

## The gap (two parts)

**1. Recovery latency — soft-kick never escalates.** The watchdog kicked ~55 times over ~3h on a slot that presented as
idle/tmux-alive/frozen before it escalated to a hard-kill. A frozen worker that fails N consecutive
post_kick_classification=frozen checks should escalate to hard-kill + respawn far sooner than 3h, not keep soft-kicking
on a fixed ~5-6 min cadence indefinitely. (kills_today=1/50 shows the daily hard-kill budget was nowhere near exhausted
— the escalation logic simply wasn't triggering.)

**2. Orphaned committed work has no automated push/inherit path.** Once the slot is killed/idle with no live worker, its
ahead/diverged commits are stranded:

- `orphan_reap.py` reaps processes/tmux only — no git awareness.
- `git_health.py` detects the drift and calls `_maybe_send_sync_nudge()`, but a nudge targets a **live** worker; the
  worker here is dead, so the nudge is a no-op.
- With a gate-dominated backlog (measured 13/0/13, zero dispatchable), AutoSpawn has no task to re-occupy slot16 with,
  so no live worker ever lands on the clone to push.

Net: the committed work sits at a standing `drift_violation` off-origin until an operator or a coincidentally
re-occupying worker pushes it. It is durable (committed in the slot's local `.git`; only a clone-dir wipe loses it) but
it never reaches `origin/live-defi-rollout` on its own.

## Proposed fixes

- [ ] [INFRA] P2. Escalate the watchdog from soft-kick to hard-kill + respawn after N consecutive
      `post_kick_classification=frozen` observations (e.g. N=3, ~15-20 min) instead of soft-kicking indefinitely; the
      daily hard-kill budget (50) is ample. SSOT: `/codex/04-architecture/autonomous-recovery-matrix.md`.
- [ ] [INFRA] P2. Add a reclaim-and-push (or inherit) path for a killed/idle slot that git-health reports as
      ahead/diverged with `unpushed_plans`: either (a) AutoSpawn prioritises re-occupying a slot with a standing
      `drift_violation` even when the backlog is otherwise gated, tasking the fresh worker to rebase (if diverged) +
      push the orphaned commits; or (b) a dedicated reaper that inherits the commits onto a live slot. Committed work
      must not strand off-origin indefinitely.
- [x] [INFRA] P3. ✅ **DONE — the one-shot defect is resolved (verified 2026-07-23), with one wording correction.**
      `server/worker_liveness/_git_alerts.py::maybe_alert_unpushed_plans` re-fires on a 1800s (30-min)
      `persist_throttle`-backed cooldown for as long as `unpushed_plans` stays non-empty, and its caller in
      `worker_liveness/__init__.py` runs it for EVERY `SlotRow` carrying `git_status_json` with **no liveness or status
      filter** (docstring: "Coverage gap fixed 2026-07-14 … including slots with no live tmux worker") — so a dead slot
      is covered, which is exactly what this todo asked for. Shipped 2026-07-14, before the 2026-07-21 incident.
      **Correction to this todo's wording**: the re-remind is NOT a repeated Slack page — `notify_unpushed_plans` was
      D11-downgraded to `logger.info` only (2026-06-25, "git housekeeping"), so the recurring signal is an
      `unpushed_plans_alert_sent` activity event (AO log + dashboard) every 30 min. If a repeated PAGE was the intent,
      that is a separate, still-unbuilt ask — file it rather than reopening this. Original item: make the
      `unpushed_plans_alert` re-remind (state-transition dedup) while the drift persists on a **dead** slot, so a
      one-shot 06:02Z alert doesn't become the only signal for work that stays stranded for hours.

## Triage

Non-blocking for the fleet (backlog is healthy 13/0/13; the loop has stopped — slot is idle, not looping). Operator
already notified via the server's unpushed_plans_alert. Main orchestrator is barred from push/respawn, so remediation
routes through these todos + operator action to land slot16's `ao_uniform_agent_liveness_contract` commits. Filed on
review(slot1)'s behalf per the async-wait/stuck-recovery watchdog guidance.

## Recurrences

- **2026-07-25 ~02:33Z — slot 10** (flagged again by review/slot1, confirmed by main read-only). Same class: slot 10
  died **idle** (prereq-blocked on `sports_satellite_ao_dispatch_batch2-005/-007/-011`) with
  `worker_alive=false, tmux_alive=false`, holding one committed-but-unpushed commit `ed24ea184`
  (`chore(orphan-wip): inherited WIP …`, authored 02:34:08Z) on branch `plan_reconciler/agt-be8370-archive` (no
  upstream): `unified-trading-pm` ahead=1 / behind=22 vs origin/live-defi-rollout, HEAD not an ancestor. Files are 2
  plan docs (`plan_reconciler_findings_2026_07_25.md` +95, `docs_retrieval_layer_reconcile_2026_07_23.md` +7); worktree
  CLEAN so no uncommitted loss. `unpushed_plans_alert_sent` fired 02:32:16Z (operator surfaced). Confirms the open
  `[INFRA] P2` reclaim-and-push todo is still unbuilt and the gap recurs. Note: main tried the sanctioned
  `POST /api/agents/by-role/conflict_resolver/message` route (03:09Z) — it logged `agent_message_sent` but did **not**
  spawn a one-shot conflict_resolver (a by-role thread message is not a dispatch), so that is not a viable ad-hoc
  remediation either; still routes through the todo + operator. Landing needs judgment (is
  `plan_reconciler_findings_2026_07_25.md` superseded by a newer scheduled run? + a 22-behind rebase of another agent's
  branch) → correctly an operator/human call, not an auto-dispatched todo.
- **2026-07-25 ~04:48Z — slot 5** (flagged by review/slot1 msg 1931, confirmed read-only by main on-host
  ip-172-31-5-118). Same class: slot 5 died **idle** (prereq-blocked on
  `sports_satellite_ao_dispatch_batch2-007/-011/-015`) in the 04:28:17Z `tmux_session_lost` burst (slots 4/5/8/9 + a
  review predecessor, correlated with the orchestrator server reload — self-healing, tasks auto-requeued), now
  `worker_alive=false, tmux_alive=false, last_ping 04:27:38Z`. Holds **2 committed-but-unpushed `docs(plans):` commits**
  on `live-defi-rollout` (`3a44c523c` flip Eastern-Europe/UEFA checkbox — uac@dbd64914; `79dda3cc8` flip Eastern-Europe
  todo + close finalize-plan Phase-0 coverage gap): `unified-trading-pm` ahead=2 / behind=10 vs
  origin/live-defi-rollout, HEAD **not** an ancestor. **Worktree CLEAN, NO rebase state** — so this is not a stuck
  rebase blocking the FF-pull cron (review's alternate hypothesis ruled out); the cron simply cannot fast-forward a
  2-ahead diverged HEAD. Work is durable (committed in the slot's local `.git`) but stranded off-origin. These are
  doc-only plan-flip commits (low-stakes, no code), but landing them still needs a rebase-of-a-shared-branch that the
  unbuilt `[INFRA] P2` reclaim-and-push todo would automate; main is barred from push/respawn, so remediation routes
  through that todo + operator action. Second same-day recurrence (slot 10 ~02:33Z, slot 5 ~04:48Z) — the gap is
  actively recurring.
