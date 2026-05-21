---
title: agent-orchestrator — architecture overview
created: 2026-05-19
author: ikenna-claude-subagent
scope: infrastructure
status: active
last_reviewed: 2026-05-19
---

# agent-orchestrator — architecture overview

**Repo**: `IggyIkenna/agent-orchestrator` (renamed from `orchestrator-service` 2026-05-19)

**What it is**: Operator tooling for parallel Claude Code worker agents. A FastAPI + Vite-dashboard HTTP server that
replaces file-based orchestration (LEDGER.md + ping files + manual dispatch). Worker agents call `/boot`, `/progress`,
`/done`, `/blocked`, `/heartbeat` instead of reading/writing markdown files. State persists in SQLite
(`data/state/state.db`). Config (backlog, accounts, backends) is YAML/JSON under `data/config/`.

**NOT a trading service.** No asset_group, no batch/live modes, no kill-switch surface, no event-bus emission to UTL.
See § "Difference vs trading services" below.

**Repo map pointer**: events → UTL · schemas → UAC · **orchestration → agent-orchestrator** (see
`cursor-configs/CLAUDE.md` § "System-First Architecture" —
`port 8026 locally; agent-orchestrator.odum-research.com prod`).

Cross-links: operator runbook → `codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md`; infra/deploy reference
→ `codex/05-infrastructure/agent-orchestrator-deploy.md`.

---

## Tech stack

| Layer      | Technology                                                                           |
| ---------- | ------------------------------------------------------------------------------------ |
| Backend    | FastAPI (Python 3.13), uvicorn, SQLAlchemy + SQLite (`data/state/state.db`)          |
| Frontend   | React + TypeScript + Vite (dashboard served by Firebase Hosting post-P2)             |
| Auth       | HS256 JWT (`PyJWT`); argon2 password hashing (`scripts/manage_users.py`)             |
| Workers    | tmux-spawn on operator's laptop (pre-P5); dedicated GCE VMs post workers-on-VMs plan |
| State      | SQLite (runtime) + `data/state/state.json` snapshot (30-min auto + shutdown)         |
| GCS backup | `gs://agent-orchestrator-state-prod/` — set via `ORCHESTRATOR_GCS_BUCKET` env        |
| Deps       | `uv` + `uv.lock` (Python); `npm` + `package.json` (dashboard)                        |
| QG         | `bash scripts/check.sh` — ruff + basedpyright + prettier + tsc                       |

---

## Deployment shape

Mirrors `unified-trading-system-ui` (DART): Firebase Hosting in front of Cloud Run, single GCP project
`central-element-323112`, two env tiers (staging/prod as separate Cloud Run services).

```
Firebase Hosting  →  Cloud Run: agent-orchestrator-{staging|prod}  →  GCS state bucket
       |                           (europe-west4)
agent-orchestrator.staging.odum-research.com
agent-orchestrator.odum-research.com
```

Both domains are live (DNS + SSL provisioned 2026-05-19; see
`plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md` Phase 2).

**Prior deployment** (active until P5 prod cutover): laptop nginx + Let's Encrypt at `orch.epiphanytechnologies.com` —
1-day fallback after prod cutover, then decommissioned.

**Local dev** (port 8026): see § "Local dev" below.

---

## Service bootstrap exemptions

Two QG steps are exempted (operator decision 2026-05-19):

- **QG STEP 5.61 (ServiceBootstrap)** — orchestrator has no `--asset-group`/`--mode` trading CLI; uvicorn-only startup.
  Source comment in `client-reporting-api` confirms the bootstrap is a token gesture; exempt here.
- **QG STEP 5.34 (typed config_reloaders.py)** — `server/config.py` is module-level env-driven functions; full
  compliance requires a config-class refactor deferred post-cutover.

`/health` + `/readiness` endpoints (QG STEP 5.62) are registered via UTL `make_health_router` with `data_freshness`
callback (state.json mtime + DB/backlog checks) — `agent-orchestrator@8e5a7e2`.

---

## Secret model — GCP Secret Manager

| Secret                    | Contents                       | Bound to                            |
| ------------------------- | ------------------------------ | ----------------------------------- |
| `ORCHASTRATOR_JWT_SECRET` | 32-byte random signing key     | Cloud Run service account (per env) |
| `ORCHESTRATOR_GCS_BUCKET` | env var (not SM) — bucket name | set via `--set-env-vars` at deploy  |

Secrets bound via `gcloud run services update --update-secrets=...`. Staging and prod use separate secrets. Local dev:
set in `.env.local` (gitignored).

---

## Auth flip rationale

`server/auth.py::validate_credentials` is currently permissive (`ALLOW_ANONYMOUS=True`) — by operator decision at
launch, trading permissive auth for faster iteration. Strict auth flip is Phase 3 of the Cloud Run deployment plan:

- Create `ORCHASTRATOR_JWT_SECRET` in Secret Manager
- Replace `validate_credentials` with argon2-hashed user list (schema from `scripts/manage_users.py`)
- Flip `auth.ALLOW_ANONYMOUS=False`
- Smoke test: 3-curl sequence (valid creds → 200, wrong password → 401, anonymous → 401)

**AUTH_INVENTORY.md** in the repo has the full flip-day checklist.

---

## GCS state mirror

Phase 5 (prod cutover) moves `data/state/state.json` from laptop disk to `gs://agent-orchestrator-state-prod/`
(asia-northeast1, 30-day version retention — workspace GCS SSOT per CLAUDE.md). Until P5:

- State persists on Harsh's laptop disk
- `SnapshotLoop` in `server/gcs_sync.py` runs every 30 min; uploads to GCS if `ORCHESTRATOR_GCS_BUCKET` is set

**Off-laptop continuity**: set `ORCHESTRATOR_GCS_BUCKET=agent-orchestrator-state-prod` on prod Cloud Run → state
survives a laptop outage. This is P5's primary reliability guarantee.

---

## Dashboard URLs

| Environment     | URL                                                  | Notes                               |
| --------------- | ---------------------------------------------------- | ----------------------------------- |
| Production      | https://agent-orchestrator.odum-research.com         | P5 target — pending prod cutover    |
| Staging (UAT)   | https://agent-orchestrator.staging.odum-research.com | P1-P4 target                        |
| Local dev       | http://localhost:5173 (Vite dashboard)               | see § "Local dev"                   |
| Legacy fallback | https://orch.epiphanytechnologies.com                | active until P5+1 day, then removed |

---

## Local dev — port 8026

Port 8026 is registered in `unified-trading-pm/scripts/dev/ui-api-mapping.json`.

```bash
cd agent-orchestrator

# One-time setup
uv venv && uv sync
.venv/bin/pre-commit install --install-hooks
cd dashboard && npm install && cd ..

# Boot everything (backend :8026 + Vite dashboard :5173)
scripts/dev.sh          # live mode
scripts/dev.sh --mock   # demo mode
```

Note: Cloud Run uses `PORT=8080` internally (set in Dockerfile). Local dev uses 8026 per the workspace port registry.
The Vite dev server for the dashboard is always on `:5173` locally.

**Quality gates**: `bash scripts/check.sh` (ruff + basedpyright + prettier + tsc). No standard `quality-gates.sh`
integration — operator tooling exemption per the deployment plan.

---

## Slack notifications

Block Kit push notifications to `#agent-orchestrator-alerts` via incoming webhook. Shipped at
`agent-orchestrator@cd04fc2` (Block Kit + retry + `blocked_id` dashboard link).

**Wired on Cloud Run staging 2026-05-21** (`@07e42e2`): `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` +
`AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET` mounted on `agent-orchestrator-staging`. async→sync httpx conversion applied
(asyncio.run in sync FastAPI endpoint suppressed all calls; smoke test confirmed on revision `00011-mtg` with 350-460ms
latency).

**SSOT**: `codex/05-infrastructure/agent-orchestrator-slack-notifications.md` (event table, payload shape, retry logic,
secret inventory, V2 out-of-scope).

---

## Deployment script

`deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh` (created at P1 of the Cloud Run deployment plan).
Shape mirrors `deploy-ui.sh`:

- Rejects missing `--env` flag
- Supports `--env=prod|uat`
- Reads `config/docker-build.env.{production,uat}` for build env vars

Registered in `codex/05-infrastructure/launcher-script-ssot.md` § "Cloud Run launchers".

---

## Difference vs trading services

| Axis                      | Trading service (e.g. MTDS, features-service) | agent-orchestrator                            |
| ------------------------- | --------------------------------------------- | --------------------------------------------- |
| Purpose                   | Produce market data / signals / fills         | Coordinate Claude Code workers                |
| Asset group               | Required (`cefi`/`defi`/`tradfi`/…)           | None — operator tooling only                  |
| Batch/live modes          | Identical code path, env toggles              | Not applicable                                |
| Kill-switch surface       | UTL kill-switch bus checked at each tick      | None                                          |
| Event-bus emission        | `log_event()` to GCS + PubSub on every action | None (activity stored in SQLite)              |
| ServiceBootstrap (5.61)   | Required — handles STARTED/STOPPED/FAILED     | Exempt — operator decision 2026-05-19         |
| config_reloaders (5.34)   | Required — typed config class                 | Exempt — env-driven functions                 |
| make_health_router (5.62) | Required                                      | Applied — see §"Service bootstrap exemptions" |
| Schema provenance (UAC)   | All domain types from UAC                     | `server/models.py` local (operator tooling)   |

Consequence: Do NOT add `--asset-group` flags, backtest modes, or emit STARTED/STOPPED events to this service. Do NOT
add it to the trading-pipeline DAG (instruments-service → MTDS → features → strategy → execution). It is purely an
operator coordination surface.

---

## Reliability layer (shipped 2026-05-20)

Five mitigations added to close gaps in the multi-agent loop. All live on the Ikenna VM backend.

| #   | Mitigation                          | Mechanism                                                                                  | Failure mode it closes                                                                       |
| --- | ----------------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| 1   | Mirror-failure → orchestrator alert | `tab-mirror-to-ldr.yml` POSTs every outcome to `/api/mirror-events`                        | Push to tab branch silently fails to cascade to LDR; downstream agents read stale plan state |
| 2   | Pre-spawn dirty-state gate          | `spawn_slot()` runs `worktree_clean_check.py` first; HTTP 409 + per-repo manifest on dirty | New agent silently inherits another agent's WIP                                              |
| 3   | Per-agent `.agent-claim` file       | `.tabs/<N>/.agent-claim` JSON written on spawn, refreshed by heartbeat                     | Context-reset agent can't tell own predecessor's WIP from foreign WIP                        |
| 4   | Heartbeat in-flight files           | `HeartbeatRequest.in_flight_files` persisted to `SlotRow.in_flight_files_json`             | Successor agent into a dead slot has no record of WIP file list                              |
| 5   | On-demand artifact pattern          | Worktrees code-only; venvs / node_modules built on first need                              | ~160G of duplicated venvs across 12 slots; SSD bloat                                         |

Plan + per-phase commits: `plans/active/agent_reliability_mitigations_2026_05_20.md`. Detailed § "Reliability layer" in
the operator runbook: `codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md`.

## Two-operator topology

The system is **multi-master**. Each operator runs a fully autonomous backend:

| Operator | Backend host                                             | Public URL                                         | State                                             |
| -------- | -------------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------- |
| Ikenna   | EC2 `m8i.4xlarge`, EIP `13.113.200.22`, `ap-northeast-1` | `https://api.agent-orchestrator.odum-research.com` | Independent `state.db`, users, slots, claim files |
| Harsh    | Personal laptop                                          | `https://orch.epiphanytechnologies.com`            | Independent `state.db`, users, slots, claim files |

The Firebase-hosted SPA at `https://agent-orchestrator.odum-research.com` is the SHARED entrypoint; the backend dropdown
lets either operator pick which API the SPA hits. Login is per-backend (each `users.json` is distinct). There is no
shared runtime state between backends — cross-side coordination happens through:

- `unified-trading-pm/plans/active/_agent_pings.md` (workspace-shared cross-side log)
- Daily work-split files `plans/active/work_split_<date>_<operator>.md`
- Git: tab branches + `live-defi-rollout` auto-FF via `tab-mirror-to-ldr.yml`

## Plan reference

Full deployment plan (P0–P6): `plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md` (P5 cutover
re-targeted from Cloud Run to dedicated EC2 VM 2026-05-19; see `docs/ikenna-vm-setup.md` for VM provisioning log).

Active successor plans:

- `plans/active/agent_reliability_mitigations_2026_05_20.md` — the 5-mitigation reliability layer (Phases 1-5 shipped;
  auto `uv sync` hook deferred)
- `plans/active/agent_orchestrator_slack_notifications_2026_05_19.md` — Slack push notifications (P1 + P2 shipped)
- `plans/active/agent_orchestrator_workers_on_vms_2026_05_XX.md` — worker execution on VMs (planning)
- `plans/active/agent_orchestrator_multi_account_failover_2026_05_XX.md` — multi-account failover (planning)

Resolved/closed issues:

- `plans/active/issues/orchestrator_spawn_tmux_silent_failure_2026_05_20.md` (RESOLVED 2026-05-20 — spawn endpoint tmux
  daemon silent-fail + workspace-trust prompt unhandled; fix shipped at `agent-orchestrator@e975f19` +
  `scripts/install-orchestrator-service.sh` at `agent-orchestrator@dc535b2` to prevent recurrence)
