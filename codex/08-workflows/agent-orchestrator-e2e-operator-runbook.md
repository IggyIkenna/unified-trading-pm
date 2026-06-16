---
scope: [engineer, admin]
title: agent-orchestrator — e2e operator runbook
created: 2026-05-19
author: ikenna-claude-subagent
status: active
execution:
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

> **Cutover state 2026-05-20**: prod is now on a dedicated EC2 VM (`m8i.4xlarge`, `ap-northeast-1`, EIP `13.113.200.22`)
> with its own systemd unit; the original Cloud Run staging in `europe-west4` is being decommissioned. Two-operator
> model in effect: **Ikenna's backend is the EC2 VM**; **Harsh's backend is his laptop**. The Firebase-hosted dashboard
> can switch between them via the backend dropdown — see § "Two-operator coordination" below.

| Environment                           | URL (SPA dashboard / API)                                          | Owner  | Notes                                                                                                                                                                                               |
| ------------------------------------- | ------------------------------------------------------------------ | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Production SPA (primary)**          | `https://agent-orchestrator.odum-research.com`                     | both   | Firebase Hosting serves the SPA; the dashboard's backend dropdown picks which API to hit                                                                                                            |
| **Ikenna VM (prod backend, default)** | `https://api.agent-orchestrator.odum-research.com`                 | Ikenna | EC2 `i-0c9b283b31d6b5ca7`, EIP `13.113.200.22`, `ap-northeast-1c`. systemd unit `orchestrator.service`. Let's Encrypt cert via certbot, auto-renew armed                                            |
| **Harsh laptop (cross-side backend)** | `https://orch.epiphanytechnologies.com`                            | Harsh  | Harsh's local fleet — always-on while his machine is up. Cross-side visibility requires Harsh adds an `ikenna` user to his `users.json` and the dashboard backend dropdown selects "Harsh (laptop)" |
| **Staging SPA (UAT)**                 | `https://agent-orchestrator.staging.odum-research.com`             | both   | Firebase Hosting `agent-orchestrator-uat-site` — same dashboard, points at staging backend if configured                                                                                            |
| **Local dev**                         | `http://localhost:5173` (Vite) → `http://localhost:8765` (backend) | self   | `cd agent-orchestrator && uvicorn server.server:app --port 8765` + `cd dashboard && npm run dev`                                                                                                    |

VM SSH for ops:

```bash
# Mac ~/.ssh/config alias (added 2026-05-19, see docs/ikenna-vm-setup.md)
ssh agent-orchestrator-vm                       # opens shell on the VM
tmux ls                                         # see live spawned workers (orch-slot-<N>)
sudo journalctl -u orchestrator -f              # tail orchestrator logs
```

---

## How to log in

Strict auth is in effect post-2026-05-19 cutover (`ALLOW_ANONYMOUS=False`).

1. Bootstrap your user once on the backend host (one-time setup per machine):

   ```bash
   ssh agent-orchestrator-vm   # or your own host
   cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator
   .venv/bin/python scripts/manage_users.py add <username>   # interactive prompt
   .venv/bin/python scripts/manage_users.py list             # verify
   ```

2. Open `https://agent-orchestrator.odum-research.com`, pick the right backend from the dropdown (Ikenna VM = default),
   sign in with the username + password from step 1.
3. JWT is issued (HS256, signed by `ORCHESTRATOR_JWT_SECRET` — central-VM-only secret loaded from
   `/home/ubuntu/unified-trading-system-repos/agent-orchestrator/.env.local`). The operator JWT validates on the central
   API only and never leaves that VM — central→worker proxy calls use the separate `ORCHESTRATOR_INTERNAL_SECRET`
   (codified 2026-05-29; see `codex/12-agent-workflow/orchestrator-multi-vm-topology.md` § "Auth: two-secret model").

Per-backend bootstrap: each backend has its own `data/config/users.json`, but per the centralized-router model
(2026-05-22) the dashboard only ever logs into the **central** API. Operator JWT is validated there; the central proxies
per-VM calls to workers over the private VPC using a separately-signed internal service token. Adding a new operator
means adding a `users.json` row only on the central VM.

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

**Path A (preferred, fully automated post-2026-05-20 spawn-fix)** — backend handles tmux + claude entirely:

1. Open the dashboard Fleet panel → **+ Spawn worker**.
2. Pick a slot ID (e.g. 5), role (`worker` / `main` / `monitor` / etc.), model (`sonnet` / `opus` / `haiku`).
3. (Optional) preview the rendered boot prompt — dashboard fetches via `GET /api/spawn/preview?slot_id=<N>&...`.
4. Click **Spawn**. Backend:
   - Runs pre-spawn dirty-state gate; if dirty, returns 409 with per-repo manifest + offers
     `dirty_state_resolution=stash`
   - `tmux new-session -d -s orch-slot-<N> -c .tabs/<N>/ claude --dangerously-skip-permissions --model <X>`
   - Auto-dismisses workspace-trust prompt (Enter) + bypass-permissions warning (`2`)
   - Pastes the boot prompt via `tmux load-buffer` + `tmux paste-buffer` + Enter
   - Writes `.tabs/<N>/.agent-claim` JSON (agent_id, role, model, operator, expires_at)
5. Within ~30s the worker calls `/api/slots/<N>/boot` and receives its first task.

Tail the live session: `ssh agent-orchestrator-vm && tmux attach -t orch-slot-<N>`.

**Path B (legacy fallback)** — manual paste into a `claude` session, no backend orchestration:

1. Dashboard → **+ Spawn worker** → click **Copy boot prompt** (instead of Spawn).
2. Open a `claude` session locally and paste. Agent calls `/api/slots/{id}/boot` and is dispatched.

Use Path B only if Path A returns 409 from a dirty-state-gate-block you don't want to stash through, or if the backend
is unreachable but you want to keep working.

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

## Reliability layer — 5 mitigations shipped 2026-05-20

All 5 are live on the Ikenna VM backend. The original plan + per-phase commit shas are in
[`plans/active/agent_reliability_mitigations_2026_05_20.md`](../../plans/active/agent_reliability_mitigations_2026_05_20.md).

| #   | Mitigation                          | Surface                                                                                                    | What it does                                                                                                                                                                                                                                |
| --- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Mirror-failure → orchestrator alert | `POST /api/mirror-events` (public webhook) + `GET /api/mirror-events` + `POST /api/mirror-events/<id>/ack` | `.github/workflows/tab-mirror-to-ldr.yml` POSTs every outcome to the orchestrator. Skip/race-lost surface as alerted=true so the dashboard can show "LDR mirror blocked on `<repo>@<sha>`" instead of work sitting orphaned on a tab branch |
| 2   | Pre-spawn dirty-state gate          | `spawn_slot()` runs `server/worktree_clean_check.py` before tmux                                           | Refuses spawn (HTTP 409) when slot worktrees have uncommitted changes. Returns per-repo dirty manifest + 3 resolution options. `dirty_state_resolution=stash` auto-stashes                                                                  |
| 3   | Per-agent `.agent-claim` file       | `.tabs/<N>/.agent-claim` JSON; `GET /api/slots/<N>/claim`                                                  | Distinguishes "my predecessor's WIP (context reset)" from "another teammate's WIP (foreign)". 1h TTL refreshed by heartbeat. Agent on boot reads claim to decide ownership                                                                  |
| 4   | Heartbeat in-flight files           | `HeartbeatRequest.in_flight_files`; `GET /api/slots/<N>/in-flight-files`                                   | Each heartbeat carries `{repo, path, intent, last_touched}` per file the worker is touching. Persists past tmux death so a successor agent can resume the predecessor's WIP                                                                 |
| 5   | On-demand artifact pattern          | `.tabs/<N>/` code-only; venvs / node_modules built on first need                                           | Verified 2026-05-20 on VM: 12 slots × 27 repos = 3.7G total (would be ~160G if venvs eagerly built). See `codex/05-infrastructure/per-tab-worktrees.md` § "On-demand artifact pattern"                                                      |

## Two-operator coordination — Ikenna VM ↔ Harsh laptop

The system is **multi-master**: Ikenna and Harsh each run their own backend with their own state. The Firebase-hosted
SPA + the dashboard's backend dropdown let either operator switch perspective. There is **no shared state** between
backends — each is authoritative for its own slot fleet. Cross-side coordination happens at the **plan layer**, not the
runtime state layer.

| Concern                                   | Mechanism                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Whose slot is whose?                      | Ikenna's slots live on the EC2 VM (`api.agent-orchestrator.odum-research.com`); Harsh's slots live on his laptop backend (`orch.epiphanytechnologies.com`). Slot IDs CAN collide between sides — there is no global slot ID space. Per Harsh's 2026-05-20 fleet topology: slots 1-20 = main agents (PM-only worktrees), slots 21-30 = workers (all 25 repos) — see `feat(worktrees): role-encode slot branches` in PM (200bbe774) |
| Branch naming                             | Role-encoded prefix per `setup-tab-worktrees.sh` (200bbe774): `tab/${OPERATOR}m/<N>` for main (e.g. `tab/hkm/3`), `tab/${OPERATOR}/<N>` for worker (e.g. `tab/hk/21`). Ikenna picks his own prefixes — currently `tab/ikenna/<N>` legacy, migrating to role-encoded form                                                                                                                                                          |
| Both backends visible from dashboard      | `data/config/backends.json` in each backend's repo declares the cross-side URLs. Dashboard dropdown shows both; clicking switches the API the SPA talks to. Login is per-backend — see § "How to log in"                                                                                                                                                                                                                          |
| Cross-side pings (work coordination)      | Workspace-shared `plans/active/_agent_pings.md` (Ikenna ↔ Harsh, persistent until both ack). Per-slot pings stay intra-side under `<side>_orchestrator/pings/slot_<N>.md`                                                                                                                                                                                                                                                        |
| Daily work-split                          | Each operator owns `plans/active/work_split_<YYYY_MM_DD>_<side>.md`. Slot 1 main on each side is authoritative for its own work-split; cross-side handoffs via pings                                                                                                                                                                                                                                                              |
| Mirror events (cross-side via shared LDR) | `.github/workflows/tab-mirror-to-ldr.yml` runs in every repo; both operators' pushes to `tab/**` cascade through. Mirror events from either side land in **both** orchestrator backends if both are reachable (each repo POSTs to the SSOT webhook URL `https://api.agent-orchestrator.odum-research.com/api/mirror-events` — Harsh's backend currently doesn't accept; see Open Items)                                           |

## Deploying SSOT systemd unit changes

Whenever `agent-orchestrator/scripts/orchestrator.service` is updated in the SSOT, push the changes to a VM via:

```bash
ssh agent-orchestrator-vm
cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator
git pull --ff-only origin main
bash scripts/install-orchestrator-service.sh --operator ubuntu --dry-run    # preview rendered unit
bash scripts/install-orchestrator-service.sh --operator ubuntu --restart    # apply + restart
```

The install script:

- Substitutes `User=hk` / `/home/hk/` for `--operator <name>` paths
- Diffs against current installed unit at `/etc/systemd/system/orchestrator.service`
- `sudo cp` + `daemon-reload`; `--restart` also bounces the service
- **KillMode=process** in the SSOT means already-spawned workers SURVIVE the restart (tmux sessions persist)

Closes the historical drift footgun: pre-2026-05-20 the VM's installed unit lacked `ReadWritePaths=/tmp`, causing every
spawn to silently fail. Root-cause + fix tracked in
[`plans/archive/issues/orchestrator_spawn_tmux_silent_failure_2026_05_20.md`](../../plans/archive/issues/orchestrator_spawn_tmux_silent_failure_2026_05_20.md).

## When to escalate

Escalate to the other operator or stop autonomous work when:

| Situation                                                           | Action                                                                                          |
| ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `state.db` shows sign of corruption (queries fail, bootstraps fail) | STOP server; manually inspect via `sqlite3 data/state/state.db`; restore from tarball if needed |
| ≥3 `slot_dual_flip_pattern_violation` events in 4h                  | Review those slot's plan-flip discipline; reassign if needed                                    |
| Auth lockout (401 on all endpoints) post-deploy                     | Check `~/.config/agent-orchestrator/jwt-secret` exists + matches `.env.local`; restart unit     |
| Repeated stale slots from the same slot ID                          | Check tmux session health (`tmux ls`); inspect `.agent-claim`; reassign if claim is fresh       |
| Slack webhook 401 errors                                            | Rotate `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` in Secret Manager + `.env.local`                      |
| Mirror-events stop landing in `GET /api/mirror-events`              | GHA workflow may have errored — check Actions tab on a recent tab-branch push                   |
| Spawn returns 30s `did not become ready`                            | Verify `/tmp` is in `ReadWritePaths`; re-run `install-orchestrator-service.sh --restart`        |

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
