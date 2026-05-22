# Agent-Orchestrator Slack Notifications

Slash-webhook push notifications from the agent-orchestrator Cloud Run service to `#agent-orchestrator-alerts` in the
`odum-research` Slack workspace.

---

## Overview

- **Webhook URL source**: GCP Secret Manager secret `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` (project
  `central-element-323112`). Mounted as env var on Cloud Run staging + prod.
- **Channel**: `#agent-orchestrator-alerts`
- **Slack app ID**: `A0B4N3802N9`
- **Implementation**: `server/notifications/slack.py` — shipped at `agent-orchestrator@cd04fc2` (Block Kit + retry).

---

## V1 event types

| Function              | Wired in                         | Trigger                         | Message format                                                |
| --------------------- | -------------------------------- | ------------------------------- | ------------------------------------------------------------- |
| `notify_slot_blocked` | `server/server.py` blocked_slot  | POST /api/slots/{id}/blocked    | Block Kit: header + section + dashboard link in context       |
| `notify_slot_stale`   | `server/health.py` working-stale | HealthMonitor: slot silent >25m | Block Kit: header + last-heartbeat section + re-spawn context |
| `notify_slot_failed`  | `server/health.py` idle-stale    | HealthMonitor: idle worker dead | Block Kit: header + error_detail section + re-spawn context   |

### Payload shape (Block Kit)

All three functions produce:

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

| Secret                                    | Mounted on Cloud Run | Used for                                  |
| ----------------------------------------- | -------------------- | ----------------------------------------- |
| `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`        | YES (P3)             | Incoming webhook — POST notifications     |
| `AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET` | not yet (V2)         | Post-cutover slash-command request verification |
| `AGENT_ORCHESTRATOR_SLACK_APP_ID`         | no                   | Reference only (app ID `A0B4N3802N9`)           |
| `AGENT_ORCHESTRATOR_SLACK_CLIENT_ID`      | no                   | OAuth post-cutover use                          |
| `AGENT_ORCHESTRATOR_SLACK_CLIENT_SECRET`  | no                   | OAuth post-cutover use                          |

---

> **[DELTA 2026-05-22]** **Current state:** V1 shipped at `agent-orchestrator@cd04fc2` — outbound webhook notifications for STARTED/STOPPED/FAILED + Block Kit formatting + dashboard link injection. Signing secret, OAuth client credentials, and slash-command verification are NOT mounted (V2 scope). **Planned delta:** V2 bidirectional interactivity tracked under `plans/epics/orchestrator_master.md`. **Target architecture:** Full slash-command request verification + interactive block payloads + per-operator DMs.

## V2 out-of-scope

| Feature                                  | Deferred to                                            |
| ---------------------------------------- | ------------------------------------------------------ |
| Bidirectional interactivity + slash cmds | `agent_orchestrator_slack_interactivity_2026_05_XX.md` |
| Notify on slot_unblocked / agent_stale   | Same interactivity plan                                |
| Direct messages to individual operators  | Same interactivity plan                                |

---

## Unit tests

`tests/test_slack_notifications.py` — 9 tests covering retry, 4xx abort, no-op on empty webhook, Block Kit shape for all
3 event types, and dashboard link presence/absence. Run: `python -m pytest tests/test_slack_notifications.py -v` from
agent-orchestrator root.

---

## SSOT

`plans/active/agent_orchestrator_slack_notifications_2026_05_19.md` (P1+P2 shipped at `agent-orchestrator@cd04fc2`; P3
blocked on operator IAM bind; P4/P5 pending P3).
