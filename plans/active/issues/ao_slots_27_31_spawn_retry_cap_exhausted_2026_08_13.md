---
doc_type: issue
title: AO slots 27 and 31 — spawn retry cap exhausted, ~44h silent, unrelated to the tmux-socket investigation
summary: >-
  Spotted in the activity feed while working an unrelated AO tmux-socket investigation
  (`ao_tmux_session_loss_mid_task_root_cause_2026_08_10`): slot #31 logged `spawn retry cap reached retry 2/2 ·
  pane=no_session · 159240s silent` and slot #27 logged the same pattern at `159890s silent`, both around 2026-08-13
  17:30 UTC. 159240-159890s is ~44.2-44.4 hours — predates that day's tmux incidents by roughly two days, so this is
  very likely a distinct, pre-existing problem, not the same root cause. Neither slot had a currently-registered agent
  record at the time (`GET /api/agents` returned no match for either), consistent with them sitting idle/unclaimed in
  the backlog with exhausted automatic retry, rather than being actively stuck-but-running. Not investigated further at
  the time — flagged and deferred rather than pulled into an unrelated investigation's scope.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, fleet-efficiency, spawn-retry, stuck-slot]
related:
  - /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md
  - /codex/04-architecture/agent-orchestrator-scheduled-jobs.md
  - /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md
context_scope:
  - agent-orchestrator/server/worker_liveness_watchdog.py
  - /codex/04-architecture/agent-orchestrator-scheduled-jobs.md
created: "2026-08-13"
author: main (Claude Code, interactive session)
parent_epic: orchestrator_master
resolved_by:
locked_by:
locked_since:
source: >-
  Operator pasted a live activity-feed dashboard dump mid-turn on 2026-08-13 (~17:30 UTC), asking for any issues in the
  last 17 minutes to be flagged. This finding was one of two flagged (the other, slot #18's dirty-worktree `/done`
  failure, was a transient in-progress condition and not tracked separately). Deferred rather than chased down given the
  primary investigation in progress at the time.
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
---

# AO slots 27 and 31 — spawn retry cap exhausted, silent ~44h

## What was observed

Activity feed entries, both around 2026-08-13 17:30:2x-3x UTC:

- `#31 spawn retry cap reached — retry 2/2 · pane=no_session · 159240s silent`
- `#27 spawn retry cap reached — retry 2/2 · pane=no_session · 159890s silent`

159240-159890 seconds is approximately 44.2-44.4 hours — placing the START of whatever silence this measures around
2026-08-11 ~21:00-22:00 UTC, roughly two days before that day's `ao_tmux_session_loss_mid_task_root_cause` incidents
began. This timing makes it very unlikely to share that investigation's root cause (the `tmpfs-disk-cleanup.sh` denylist
gap and the split-brain socket fallback were both first-observed 2026-08-13, and the earliest confirmed incident under
that investigation was 2026-08-12 21:47Z — this predates even that).

A quick check via `GET /api/agents` (AO's local API, queried through SSM per `/check-agent-orchestrator`'s pattern)
found **no currently-registered agent record** for either `orch-slot-27` or `orch-slot-31` at query time — consistent
with both slots sitting idle/unclaimed in the backlog with exhausted automatic retry, not with an
actively-running-but-stuck worker.

## What this is NOT

- Not the tmux-socket split-brain (timing predates it by ~2 days; that investigation's supervisor instrumentation was
  not yet armed at the time this silence would have started).
- Not confirmed to be the SAME underlying cause as each other — both slots showing the identical
  `retry 2/2 · pane=no_session` pattern at similar durations is suggestive but not proof of a shared mechanism.

## Todo

- [ ] [INFRA] P2. Determine what task (if any) slots 27 and 31 were last assigned, and whether that work is still needed
      / has since been picked up by another slot — check `backlog.yaml`-derived state or the dashboard's per-slot
      history for the relevant window (~2026-08-11 21:00-22:00 UTC onward).
- [ ] [INFRA] P2. Root-cause why the spawn retry cap (2/2) was reached and never recovered — check `spawn-failed` /
      `WorkerLivenessWatchdog` logs for that window; confirm whether this is a recurring pattern across other slots
      (search activity_log for other `spawn retry cap reached` + long `silent` durations) or isolated to these two.
- [ ] [INFRA] P3. Once root-caused, decide whether these two slots need a manual respawn/reclaim or whether a fix to the
      retry/backoff logic is needed to prevent silent multi-day slot loss going forward.

## Progress Log

- 2026-08-13: doc created from a chat-only finding surfaced while working an unrelated investigation — flagged, not
  chased, per the operator's own framing at the time ("I don't want to burn time chasing that down fully right now"). No
  further investigation performed yet.
- **context-scout 2026-08-14**: populated context_scope (2 entries).
