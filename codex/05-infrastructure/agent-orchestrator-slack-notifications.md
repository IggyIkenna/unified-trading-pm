---
doc_type: codex-ssot
title: Agent-Orchestrator Slack Notifications
summary:
  Outbound Slack webhook notifications from agent-orchestrator to the agent-orchestrator-alerts channel — Block Kit
  payloads with retry (3 attempts on 5xx, suppressed on failure), a 13-function Slack / 9-function Telegram inventory
  (the two modules intentionally diverge), and the secret inventory (V1 webhook mounted; signing-secret/OAuth are V2).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, slack, notifications, monitoring, observability, self-healing]
related:
  [
    /codex/12-agent-workflow/orchestrator-safety-mechanisms.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/05-infrastructure/agent-orchestrator-api-host.md,
  ]
created: 2026-05-20
authoritative_for: [agent-orchestrator Slack notification functions + payload/retry contract]
referenced_by:
  [
    /codex/12-agent-workflow/orchestrator-safety-mechanisms.md,
    plans/audit/instructions/orchestrator_master_audit_instructions.md,
  ]
owner:
last_reviewed: 2026-10-25
code_refs:
---

# Agent-Orchestrator Slack Notifications

Outbound webhook push notifications from the agent-orchestrator backend (the central orchestrator VM) to
`#agent-orchestrator-alerts` in the `odum-research` Slack workspace.

---

## Overview

- **Webhook URL source**: `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`, loaded from the VM's `.env.local` (provisioned via the
  `ORCHESTRATOR_ENV_LOCAL` secret in AWS Secrets Manager / GCP Secret Manager `central-element-323112`).
- **Channel**: `#agent-orchestrator-alerts`
- **Slack app ID**: `A0B4N3802N9`
- **Implementation**: `server/notifications/slack.py` — shipped at `agent-orchestrator@cd04fc2` (Block Kit + retry).

---

## Event types (refreshed 2026-06-01)

`server/notifications/slack.py` is sync (suppress on failure); `server/notifications/telegram.py` is async (suppress on
failure). **The two modules no longer expose an identical set** — Slack carries the dashboard-centric alerts
(`notify_unpushed_plans`, `notify_autospawn_flap`, `notify_watchdog_kill`) that Telegram omits, and Telegram carries
`notify_orchestrator_restart_loop` + `notify_sync` that Slack omits. Current inventory: **Slack = 13 funcs, Telegram = 9
funcs** (verified against `rg "^(async )?def notify_" server/notifications/*.py` 2026-06-01). The three OAuth-refresh
notifications (`notify_oauth_token_expiring`, `notify_oauth_refresh_succeeded`, `notify_oauth_refresh_failed`) were
removed in Phase 4b-cleanup 2026-05-28 — see
[`/codex/12-agent-workflow/orchestrator-safety-mechanisms.md`](/codex/12-agent-workflow/orchestrator-safety-mechanisms.md)
§ C.

The S (Slack) / T (Telegram) columns mark which module exports each function.

| Function                           | S   | T   | Wired in                                                      | Trigger                                                               |
| ---------------------------------- | --- | --- | ------------------------------------------------------------- | --------------------------------------------------------------------- |
| `notify_slot_blocked`              | ✓   |     | `server/server.py::blocked_slot`                              | POST /api/slots/{id}/blocked (operator answer needed)                 |
| `notify_slot_stale`                | ✓   |     | `server/health.py` working-stale path                         | HealthMonitor: working slot silent >25 min                            |
| `notify_slot_failed`               | ✓   |     | `server/health.py` idle-stale path                            | HealthMonitor: idle worker process dead                               |
| `notify_spawn_failure`             | ✓   | ✓   | `server/server.py::spawn_slot` exception arm                  | `tmux_spawn.spawn` raised — readwrite/systemd/tmux config issue       |
| `notify_agent_stuck_respawned`     | ✓   | ✓   | `server/worker_liveness.py` auto-respawn happy path           | Stuck-agent detection fired + tmux respawn succeeded                  |
| `notify_agent_stuck_escalation`    | ✓   | ✓   | `server/worker_liveness.py` auto-respawn failure path         | Respawn attempted but new tmux session never registered               |
| `notify_account_rotated`           | ✓   | ✓   | `server/server.py::rotate_all_slots_off_account`              | Slot respawned with a fresh sibling account (rate-limit failover)     |
| `notify_all_accounts_exhausted`    | ✓   | ✓   | `server/server.py::_pick_next_account` (no healthy sibling)   | All accounts past 95% on at least one quota dimension                 |
| `notify_setup_token_expiring`      | ✓   | ✓   | `server/usage_poller.py::_check_setup_token_expiry`           | Long-lived setup-token within 30-day (warn) or 7-day (crit) of expiry |
| `notify_git_staleness_red`         | ✓   | ✓   | `server/health.py` git-status badge integration               | Slot's worktree red >15 min AND no auto-pull within 5 min             |
| `notify_unpushed_plans`            | ✓   |     | `server/health.py` git-staleness path                         | Plan-flip commits sitting unpushed on a slot worktree                 |
| `notify_autospawn_flap`            | ✓   |     | `server/autospawn.py` flap-detector                           | 3 consecutive autospawns within 10 min produced no task claim         |
| `notify_watchdog_kill`             | ✓   |     | `server/worker_liveness_watchdog.py` kill path                | Watchdog killed a stuck/silent/context-full worker (or daily-cap hit) |
| `notify_orchestrator_restart_loop` |     | ✓   | Telegram-only; called from a systemd OnFailure script wrapper | systemd restarted orchestrator >N times in a short window             |
| `notify_sync`                      |     | ✓   | Telegram-only; generic sync/heartbeat broadcast               | Periodic / manual fleet sync notification                             |

### Payload shape (Block Kit)

All 13 Slack functions produce (Block Kit is Slack-specific; Telegram's 9 functions use a separate, non-Block-Kit
payload shape in `server/notifications/telegram.py`):

```json
{
  "text": "<emoji> Slot N <EVENT> [timestamp]",
  "blocks": [
    {"type": "header", "text": {"type": "plain_text", "text": "<emoji> Slot N <EVENT>"}},
    {"type": "section", "fields": [...]},
    {"type": "context", "elements": [{"type": "mrkdwn", "text": "..."}]}
  ]
}
```

`text` is the fallback for notification-only clients. `blocks` provides the rich Block Kit view. `notify_slot_blocked`
adds a concrete dashboard link (`{ORCHESTRATOR_PUBLIC_URL}/api/blocked/{blocked_id}`) in the context block when both
`blocked_id` and `_PUBLIC_URL` are available.

---

## Retry behaviour

`_post()` makes up to 3 attempts on Slack 5xx responses:

- Attempt 1: immediate
- Attempt 2: after 0.5 s
- Attempt 3: after 1.0 s

4xx (including 403 webhook-not-found): abort immediately, no retry.

All call sites wrap in `contextlib.suppress(Exception)` — Slack outage or webhook misconfiguration never propagates to
the server process or health monitor.

---

## Non-fatal pattern + local dev

If `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is empty or unset, `_post()` returns immediately (no-op). No mock or stub required
in local dev; unit tests patch `_WEBHOOK_URL` directly.

---

## Secret inventory (all in `central-element-323112`)

| Secret                                    | In VM `.env.local` | Used for                              |
| ----------------------------------------- | ------------------ | ------------------------------------- |
| `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`        | YES                | Incoming webhook — POST notifications |
| `AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET` | not yet (V2)       | V2 slash-command request verification |
| `AGENT_ORCHESTRATOR_SLACK_APP_ID`         | no                 | Reference only (app ID `A0B4N3802N9`) |
| `AGENT_ORCHESTRATOR_SLACK_CLIENT_ID`      | no                 | V2 (OAuth) — not yet used             |
| `AGENT_ORCHESTRATOR_SLACK_CLIENT_SECRET`  | no                 | V2 (OAuth) — not yet used             |

---

> **[DELTA 2026-05-22]** **Current state:** V1 shipped at `agent-orchestrator@cd04fc2` — outbound webhook notifications
> for STARTED/STOPPED/FAILED + Block Kit formatting + dashboard link injection. Signing secret, OAuth client
> credentials, and slash-command verification are NOT mounted (V2 scope). **Planned delta:** V2 bidirectional
> interactivity tracked under `plans/epics/orchestrator_master.md`. **Target architecture:** Full slash-command request
> verification + interactive block payloads + per-operator DMs.

## V2 out-of-scope

| Feature                                  | Deferred to                                        |
| ---------------------------------------- | -------------------------------------------------- |
| Bidirectional interactivity + slash cmds | a future Slack-interactivity plan (not yet scoped) |
| Notify on slot_unblocked / agent_stale   | Same interactivity plan                            |
| Direct messages to individual operators  | Same interactivity plan                            |

---

## Unit tests

`tests/test_slack_notifications.py` covers retry, 4xx abort, no-op on empty webhook, Block Kit shape, and dashboard link
presence/absence. The test count has grown beyond the original V1 trio as additional functions landed; run
`python -m pytest tests/test_slack_notifications.py -v` from agent-orchestrator root to see the current set.

---

## SSOT

`plans/active/agent_orchestrator_slack_notifications_2026_05_19.md` (P1+P2 shipped at `agent-orchestrator@cd04fc2`; P3
blocked on operator IAM bind; P4/P5 pending P3).
