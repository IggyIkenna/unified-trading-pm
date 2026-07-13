---
doc_type: codex-ssot
title: Agent-Orchestrator Alerting — actionable-only channel + daily digest
summary:
  The contract for what reaches the agent-orchestrator-alerts Slack channel. Automatic backend lifecycle events
  (plan-health / escalation dispatches, auto-respawns, recoveries) are NOT paged — they log to AO logs + the GCS ledger
  and are rolled into one daily digest. Only operator-actionable events page (failures, worker BLOCKED questions,
  unresolved escalations). Standing conditions dedup by state-transition (fire on change / RESOLVED / a re-remind
  interval), never every tick.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [alerts, slack, agent-orchestrator, observability, dedup, notifications]
related: [autonomous-recovery-matrix.md, runtime-deployment-topology.md]
created: 2026-07-13
authoritative_for: [agent-orchestrator Slack alert routing, daily-summary digest, git-health guard dedup]
referenced_by:
owner:
last_reviewed: 2026-07-13
code_refs:
  - agent-orchestrator/server/notifications/slack.py
  - agent-orchestrator/server/daily_summary.py
  - agent-orchestrator/scripts/fleet-git-health-guard.sh
---

# Agent-Orchestrator Alerting

The `agent-orchestrator-alerts` Slack channel is **actionable-only**: a message there means _a human should look_.
Everything else lives in AO logs, the GCS alert ledger (`GET /api/alerts`), and the daily digest. This is the standing
contract established by `alert_channel_cleanup_2026_07_13` (a 7-day audit found 1,598 messages / 40 shapes, top-4 = 74%,
of which ~87% were automatic lifecycle churn or one unsuppressed repeat).

## What does NOT page (logged + digested, never Slack)

Automatic backend lifecycle events — the orchestrator handled them, no human is needed:

- `notify_plan_health_dispatched`, `notify_escalation_dispatched` — periodic/automatic dispatch **success**.
- `notify_agent_stuck_respawned` — an auto-respawn (self-healing).
- `notify_slot_recovered`, `notify_spawn_recovered`, `notify_git_staleness_resolved` — recovery/closure bookends.

Each of these calls `logger.info(...)` (the "D11 downgrade" convention) instead of `slack._post(...)`. Their events are
recorded in the DB **activity log** (`log_activity`) by the callers, which is what the digest reads.

## What DOES page (operator-actionable)

- **Failures** — `notify_plan_health_dispatch_failed` (deduped 1h; the plan-health do_spawn failure branch was
  previously Slack-silent), escalation dispatch failure (`autospawn.alert_spawn_failed`), `notify_spawn_failed`,
  unresolved / re-escalation-cap escalations.
- **Worker BLOCKED questions** — `notify_slot_blocked` (a worker asks the main/review agent or the operator). Renders
  the structured `question` + `options` (bulleted) + `recommendation` on their own full-width sections.
- **The digest job failing** — `notify_daily_summary_failed` (a dead digest must not be silent).

**Rule: dispatch/lifecycle SUCCESS is silent; the corresponding FAILURE pages.** Removing a success ping must never
blind the operator to that job failing.

## Daily digest (`DailySummaryLoop`)

`server/daily_summary.py` runs a supervised daemon loop (default 24h, `ORCHESTRATOR_DAILY_SUMMARY_INTERVAL_SECONDS`,
enabled by default via `ORCHESTRATOR_DAILY_SUMMARY_ENABLED`). Each tick rolls the DB activity log since a persisted
cursor (`dedup_state.daily_summary_cursor_path`, key `last_summary`) into one `notify_daily_summary` message — counts by
event type + a failure roll-up + total — then advances the cursor. `_tick_and_report` wraps the tick so any exception
fires `notify_daily_summary_failed`. The cursor makes a digest cover exactly "since the last summary" across restarts.

## Standing-condition dedup (state-transition)

A condition that stays true must not re-page every tick. Two mechanisms:

- **In-process / server:** `server/dedup_state.py` (`diff_keys`, cooldown dicts) — page on the true→false transition + a
  RESOLVED bookend, persisted to `STATE_DIR` so a restart does not re-arm a flood.
- **Per-VM cron (`fleet-git-health-guard.sh`):** a local state file (`GIT_HEALTH_GUARD_STATE_DIR`) holds the last
  problem signature + timestamp. It posts only on a **new/changed** signature, on **RESOLVED**, or on a **re-remind
  interval** (`GIT_HEALTH_GUARD_REMIND_SECS`, default 1h) — not every 15-min tick.
  `bash fleet-git-health-guard.sh --self-test` proves the state machine. The guard is a genuine actionable alert (a real
  fsck failure once produced 369 duplicates in 4 days) — dedup makes it **visible**, it does not downgrade it.
