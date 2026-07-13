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

The `Activity` list shows the **top-25 event types by frequency**. A failure-typed row (name contains `fail` / `error` /
`abandon`) that ranks below #25 is **appended anyway** (🔴-marked) rather than truncated — the fail-count line points
the operator "see the counts below", so hiding the very failures it announces would defeat the digest
(`alert_channel_cleanup` WS-B follow-up).

## Digest anatomy — field reference

Each digest (`notify_daily_summary` → the `:bar_chart: AO daily activity digest` message) has these fields:

| Field                                                 | Meaning                                                                                                                                                                                                                                 |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Since**                                             | Window start — the timestamp of the previous digest (the persisted `last_summary` cursor). The window is `[Since, now]`; the next digest's `Since` is this run's `now`. So every event is counted exactly once across the whole series. |
| **Total events**                                      | Count of **all** activity-log rows in the window (the sum of every row in the Activity list, including types beyond the shown top-25). This is total orchestrator throughput, not an error count.                                       |
| **N failure event(s)** / _No failures ✅_             | `fail_total` = the summed **count** (not the number of distinct types) of every event type whose name contains `fail` / `error` / `abandon`. `:rotating_light:` when non-zero; a green check when clean.                                |
| **Activity (by type, most frequent first)**           | `event_type — count`, top-25 by count, plus any 🔴-marked failure rows pulled up from below #25 (see above). `count` is occurrences in the window.                                                                                      |
| **Footer** (`open dashboard \| from: <host> \| <ts>`) | `open dashboard` links the AO dashboard; `from:` is the emitting host (e.g. `vm-planning` = the central orchestrator VM); `<ts>` is when the digest was rendered (UTC).                                                                 |

## Digest event glossary — what each `event_type` means

Every row is a DB activity-log event (`log_activity`). Most only appear in the digest (they no longer page — that is the
point of the actionable-only contract); `slot_blocked` and any failure-typed row **also** page live. Grouped by
lifecycle stage (code ref = the `log_activity` call site in `agent-orchestrator/`):

**Boot / spawn**

- `slot_boot` — a worker slot booted and confirmed its mandatory role read-files; it is registered and ready
  (`server/routes/slots_worker.py`).
- `boot_read_unconfirmed` — a boot handshake was **rejected** (HTTP 428) because the worker didn't confirm reading the
  expected role prompts; slot state was left unmutated and the worker must re-boot (`slots_worker.py`).
- `autospawn_succeeded` — the AutoSpawn loop launched a worker into a slot that had queued work (`server/autospawn.py`).

**Task lifecycle**

- `task_dispatched` — a queued task was assigned to a slot (routine) (`slots_worker.py`, `routes/slots_worker.py`).
- `slot_task_skipped` — a slot's assigned task was released back to the queue / cleared (with a `reason`, e.g. an
  orphaned stale marker) (`server/routes/slots_ops.py`).
- `slot_progress` — a worker reported forward progress (a heartbeat carrying a state delta) (`slots_worker.py`,
  `worker_liveness_watchdog.py`).
- `slot_done` — a worker signalled its task complete (`slots_worker.py`).
- `slot_done_verified` — the completion claim was verified (review-agent / watchdog confirmed) (`slots_worker.py`).
- `agent_replied` — an agent posted a reply (e.g. the main/review agent answered a worker) (`server/routes/agents.py`).
- `agent_message_sent` — an inter-agent message was sent (`routes/agents.py`).

**Git health**

- `git_status_reported` — a slot's `slot-git-status-report.sh` cron posted its per-repo git status (`host`,
  `repo_count`). A high-volume, purely informational heartbeat — usually the #1 row (`server/routes/git_health.py`).
- `idle_blocker_inferred` — for an **idle** slot the orchestrator inferred _why_ it is blocked (top blockers + blocked
  task count); logged on change or hourly while still blocked (`server/worker_liveness/_git_alerts.py`).

**Liveness / self-healing** (the watchdog auto-recovers; these are informational — no manual action)

- `worker_kicked` — the WorkerLivenessKicker nudged a wedged worker and **verified** it resumed (spinner appeared or the
  heartbeat advanced past its pre-kick value). Its failure counterpart `worker_kick_failed` is a failure-typed row
  (`server/worker_liveness/__init__.py`).
- `slot_idle_stale` — a slot went silent past the idle threshold and was marked `stale` (`server/health.py`).
- `worker_polling_dead` — operator-tier signal: a worker hasn't heartbeat'd in N min; the watchdog auto-reclaims the
  wedged session and AutoSpawn respawns it when work is queued (no manual action needed) (`server/health.py`).
- `watchdog_heartbeat_resumed` — the watchdog resumed a slot after heartbeat-silence, context intact
  (`worker_liveness_watchdog.py`).
- `tmux_session_lost` — a slot's tmux session disappeared / was pruned (`server/tmux_pruner.py`).
- `slot_compacted` — a worker's context window was compacted (`slots_worker.py`).
- `session_checkpoint` — a periodic GCS session checkpoint was written (`server/gcs_sync.py`).
- `slot_retire_audit_needed` — a slot's task queue is exhausted; signals the review agent to run the 6-step retire audit
  (`slots_worker.py`).

**Plan-health / escalation** (the automatic backend jobs WS-A stopped paging individually — see "What does NOT page")

- `plan_health_dispatch_initiated` — the plan-health job started a dispatch cycle (`server/plan_health.py`).
- `escalation_dispatch_initiated` — an escalation dispatch cycle started (`server/escalation.py`).
- `escalation_dispatched` — an escalation was dispatched (`escalation.py`).
- `escalation_resolved` — an escalation closed / resolved (`escalation.py`).
- `slot_blocked` — a worker posted a **BLOCKED question** (needs main/review-agent or operator input). This is the one
  digest row that **also pages** live via `notify_slot_blocked`; the digest simply counts it like any other activity row
  (`slots_worker.py`, `worker_liveness_watchdog.py`).

**Reading a digest:** a healthy window is dominated by `git_status_reported` + `worker_kicked` + `slot_boot` (heartbeat
churn) with `No failure events ✅`. A `:rotating_light:` line means look at the 🔴-marked rows: `*_fail` / `*_failed` /
`*_error` / `*_abandon*` events are the ones worth investigating (most page individually too, so the digest is a
cross-check, not the primary signal).

## Standing-condition dedup (state-transition)

A condition that stays true must not re-page every tick. Two mechanisms:

- **In-process / server:** `server/dedup_state.py` (`diff_keys`, cooldown dicts) — page on the true→false transition + a
  RESOLVED bookend, persisted to `STATE_DIR` so a restart does not re-arm a flood.
- **Per-VM cron (`fleet-git-health-guard.sh`):** a local state file (`GIT_HEALTH_GUARD_STATE_DIR`) holds the last
  problem signature + timestamp. It posts only on a **new/changed** signature, on **RESOLVED**, or on a **re-remind
  interval** (`GIT_HEALTH_GUARD_REMIND_SECS`, default 1h) — not every 15-min tick.
  `bash fleet-git-health-guard.sh --self-test` proves the state machine. The guard is a genuine actionable alert (a real
  fsck failure once produced 369 duplicates in 4 days) — dedup makes it **visible**, it does not downgrade it.
