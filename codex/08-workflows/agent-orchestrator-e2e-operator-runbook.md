---
title: agent-orchestrator — e2e operator runbook
created: 2026-05-19
author: ikenna-claude-subagent
status: active
owner: ikenna
cadence: continuous (always-on dashboard)
verifier: ikenna + harsh (cross-operator)
last_executed: P1 first-deploy 2026-05-19
---

# agent-orchestrator — E2E Operator Runbook

> **Workspace-level wrapper.** Ground-truth for repo-local workflows lives in `agent-orchestrator/docs/OPERATIONS.md`
> and `agent-orchestrator/README.md`. This doc adds workspace-specific context, URL registry, and the standard runbook
> governance fields required by CLAUDE.md "Runbook Execution-Owner SSOT" HARD RULE.
>
> Architecture SSOT: `codex/04-architecture/agent-orchestrator-overview.md` Infra/deploy reference:
> `codex/05-infrastructure/agent-orchestrator-deploy.md` Plan-of-record:
> `plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md`

---

## Where to access

| Environment                         | URL                                                                     | Status                                                                            |
| ----------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Staging (UAT) — **current primary** | `https://agent-orchestrator-staging-1060025368044.europe-west4.run.app` | Live (P1 shipped 2026-05-19)                                                      |
| Staging custom domain               | `https://agent-orchestrator.staging.odum-research.com`                  | **LIVE** — P2 shipped 2026-05-19 (Firebase Hosting + Cloud Run rewrites verified) |
| Production                          | `https://agent-orchestrator.odum-research.com`                          | Pending P5 prod cutover                                                           |
| Legacy fallback                     | `https://orch.epiphanytechnologies.com`                                 | Harsh's laptop; 1-day fallback after P5, then decommissioned                      |
| Local dev                           | `http://localhost:5173` (Vite) + backend `http://localhost:8026`        | `bash scripts/dev.sh` from `agent-orchestrator/`                                  |

Until P5 cutover, use the staging URL for daily work. The legacy fallback is authoritative for live state (Harsh's
laptop holds `state.db`).

---

## How to log in

**Pre-P3 (current)**: Auth is permissive — `ALLOW_ANONYMOUS=True`. Any non-empty credentials work on the staging Cloud
Run endpoint. No bootstrap step needed today.

**Post-P3 (strict auth flip)**:

1. Bootstrap your user once: `.venv/bin/python3 scripts/manage_users.py add <username>` on the server's host (or against
   the staging Cloud Run DB via exec).
2. Log in with that username + password at the dashboard sign-in page.
3. JWT is issued (HS256, signed by `ORCHASTRATOR_JWT_SECRET` from GCP Secret Manager).

Full flip-day checklist: `agent-orchestrator/docs/AUTH_INVENTORY.md`.

---

## Morning startup (local dev)

> Skip for Cloud Run access — the staging backend is always running.

Full procedure in `agent-orchestrator/docs/OPERATIONS.md` § "Morning startup". Summary:

```bash
# Step 0: refresh PM inventory (PM-integration mode only)
python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py

# Step 1: start the stack
cd agent-orchestrator
ORCHESTRATOR_MODE=live ./.venv/bin/python3 -m uvicorn server.server:app --port 8026
cd dashboard && npm run dev &  # opens http://localhost:5173
```

---

## How to spawn a worker from the dashboard

Full procedure: `agent-orchestrator/docs/OPERATIONS.md` § "Register your three core agents" and § "Spawn worker slots".
Summary:

1. Open the dashboard Fleet panel → **+ Spawn worker**.
2. Pick a slot ID (e.g. 2), account (e.g. `harsh-primary`), click **Copy**.
3. Open a fresh Claude Code session: `claude`
4. Paste the boot prompt. The agent calls `/api/slots/{id}/boot` and receives its first task.
5. Repeat for as many slots as needed (typical: 5–10 workers).

---

## How to spawn a main / review / backup agent

Full procedure: `agent-orchestrator/docs/OPERATIONS.md` § "Register your three core agents". Summary:

1. Open a fresh Claude Code session: `claude`
2. Inside the session: `/remote-control` — copy the printed URL.
3. Dashboard → Agents panel → **+ Spawn agent**.
4. Fill: Role (`main`/`review`/`backup`), Label, RC URL → **Copy** → paste into the Claude session.
5. Agent registers via `/api/agents/register`, starts its 60s poll cycle.

Expected Agents panel after setup: `Agents · 3/3 online — [main 1] [review 1] [backup 1]`.

---

## How to load the day's backlog

From the dashboard Agents panel → `main` chat tab, send:

> Read `plans/active/master_to_live_defi_2026_05_23.md` and add the next 20 tasks to the backlog. Use
> `/api/backlog/reload` after editing.

The main agent edits `data/config/backlog.yaml` and replies when done. Workers pick up new tasks on their next
`/heartbeat` (≤60s gap).

---

## How to handle blocked questions

Worker raises `/blocked` → appears in dashboard **Blocked questions** panel.

1. Read the worker's question + options (recommended option highlighted).
2. Click an option or type a custom answer.
3. Pick the role you're answering as: `main`, `review`, or `operator`.
4. Click **Send**.

Worker receives the answer on its next `/progress` and continues. API: `POST /api/blocked/{id}/answer`.

---

## How to recover stale slots

HealthMonitor detects stale slots within 65s (working slot silent >25 min → `status=stale`; idle slot silent >60 min →
`status=stale`).

**Dashboard**: stale slot row turns red with `[Reassign]` button.

**Three primitives** (from `agent-orchestrator/docs/OPERATIONS.md` § "Skip a task vs. reassign"):

| Operation                                            | Worker process | Slot status after | Task status                      | When                          |
| ---------------------------------------------------- | -------------- | ----------------- | -------------------------------- | ----------------------------- |
| `POST /api/slots/{id}/skip-current-task`             | stays alive    | `idle`            | back to `queued` (slot excluded) | Worker can't do THIS task     |
| `POST /api/slots/{id}/reassign` (default)            | killed         | `killed`          | back to `queued`                 | Worker broken / wrong account |
| `POST /api/slots/{id}/reassign {kill_worker: false}` | stays alive    | `idle`            | back to `queued`                 | Park for inspection           |

```bash
# Skip current task (worker keeps running, task re-queued for other slots)
curl -sS -X POST http://localhost:8026/api/slots/${SLOT}/skip-current-task \
  -H 'Content-Type: application/json' \
  -d '{"reason": "worktree missing; task deferred"}'
```

---

## How to view activity

Dashboard **Activity** tab (last 20 events, searchable). API: `GET /api/activity`.

Key events to watch:

| Event                      | Meaning                                                         |
| -------------------------- | --------------------------------------------------------------- |
| `slot_done_verified`       | Worker completed a task — always emitted                        |
| `slot_done_no_plan_flip`   | Task closed but plan checkbox not flipped — HARD RULE violation |
| `slot_done_dirty_worktree` | Uncommitted files after /done                                   |
| `slot_scope_warning`       | Worker committed outside declared repos                         |
| `slot_stale`               | Worker went silent                                              |
| `condition_set`            | Phase gate flipped                                              |

---

## How to chat with main / review / backup

**Async (dashboard)**: Agents panel → role tab → compose box → Send (or Cmd/Ctrl+Enter). Message delivered on next 60s
poll. Use for: "check worker #4", "hot-reload backlog", "promote backup → main".

**Real-time (Remote Control)**: click `↗ claude.ai/code` button in agent chat header. Opens the agent's RC session in
browser. Use for: deep technical discussion, PR review walk-through, time-sensitive decisions.

---

## How to handle account rotation

Each slot is assigned an `account_id` from `data/config/accounts.json`. When an account hits the Claude rate limit:

1. Dashboard Accounts panel: amber/red status dot on the account row.
2. Auto-detection: `usage_reporter` agent (if running) posts usage every 30 min.
3. Dispatcher automatically skips new boots/dispatches for rate-limited accounts.
4. **Recovery**: click **Clear** on account row when the window resets, or reassign affected slots to a different
   account via `POST /api/slots/{id}/reassign` + spawn with a new `account_id`.

**Named successor plan** for full multi-account failover:
`plans/active/agent_orchestrator_multi_account_failover_2026_05_XX.md` (post-P5 scope).

---

## State backup and recovery

### Today (pre-P5): laptop disk

State lives on Harsh's laptop at `data/state/state.db` + `data/state/state.json`.

```bash
# Manual snapshot (writes state.json + git commit)
curl -sX POST http://localhost:8026/api/snapshot

# End-of-day snapshot
curl -sX POST "http://localhost:8026/api/snapshot?reason=eod"
```

Auto-snapshot (`SnapshotLoop`) runs every 30 min; writes `state.json` to disk and uploads to GCS if
`ORCHESTRATOR_GCS_BUCKET` is set. Does NOT auto-commit to git (manual snapshots only).

Backup: `tar czf ~/backups/orchestrator-$(date +%Y%m%d).tar.gz -C /opt/orchestrator data/`

Recovery: stop server → restore tarball → restart. SQLite + state.json + backlog all come back.

### Post-P5: GCS bucket

`gs://agent-orchestrator-state-prod/` (asia-northeast1, 30-day retention — workspace GCS SSOT per CLAUDE.md). Set
`ORCHESTRATOR_GCS_BUCKET=agent-orchestrator-state-prod` on prod Cloud Run. Every snapshot auto- uploads. No nightly cron
needed.

---

## Flip a phase gate (conditions)

Conditions are named boolean gates in `data/config/backlog.yaml` that block groups of tasks.

**Three ways to flip**:

1. Dashboard Conditions panel — toggle the row.
2. `POST /api/conditions/{name}` with `{"value": true}`.
3. Edit `backlog.yaml` + `POST /api/backlog/reload` (only for newly-added conditions; stored values are not overwritten
   by reload).

```bash
curl -sS -X POST http://localhost:8026/api/conditions/data-schema-shipped \
  -H 'Content-Type: application/json' -d '{"value": true}'
```

---

## When to escalate

Escalate to the other operator or stop autonomous work when:

| Situation                                                           | Action                                                                                          |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `state.db` shows sign of corruption (queries fail, bootstraps fail) | STOP server; manually inspect via `sqlite3 data/state/state.db`; restore from tarball if needed |
| ≥3 `slot_dual_flip_pattern_violation` events in 4h                  | Review those slot's plan-flip discipline; reassign if needed                                    |
| Auth lockout on Cloud Run (403 on all endpoints)                    | Check Secret Manager `ORCHASTRATOR_JWT_SECRET` value; verify IAM binding on Cloud Run SA        |
| Repeated stale slots from the same slot ID                          | Check tmux session health; consider worker-on-VM migration (successor plan)                     |
| Slack webhook 401 errors in Cloud Run logs                          | Rotate `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in Secret Manager                                     |

For data-correctness issues (trading pipeline, manifest, GCS parquets): those are outside this service's scope —
escalate via `plans/active/_agent_pings.md`.

---

## Validation smoke tests

From `agent-orchestrator/docs/OPERATIONS.md` § "Validation smoke tests":

```bash
# Pre-flight check
curl -sf http://localhost:8026/api/healthz | python3 -m json.tool
curl -s  http://localhost:8026/api/state | python3 -m json.tool

# /blocked round-trip (Test E — fastest, no Claude session needed)
# See OPERATIONS.md for full curl sequence
```

---

## Quick reference endpoints

| Endpoint                        | Purpose                                           |
| ------------------------------- | ------------------------------------------------- |
| `GET /api/healthz`              | Server alive? Returns mode + uptime_seconds       |
| `GET /health`                   | UTL-standard health probe (workspace convention)  |
| `GET /readiness`                | Cloud Run readiness probe (DB + backlog checks)   |
| `GET /api/state`                | Slots, blocked queue, conditions, backlog summary |
| `GET /api/activity`             | Activity feed (searchable)                        |
| `POST /api/backlog/reload`      | Re-read backlog.yaml from disk                    |
| `POST /api/conditions/{name}`   | Toggle a phase gate                               |
| `POST /api/snapshot`            | Force state.json write                            |
| `POST /api/slots/{id}/reassign` | Kill and release slot's task                      |
| `POST /api/blocked/{id}/answer` | Answer a blocked question                         |
