---
scope: infrastructure
status: active
last_reviewed: 2026-05-19
---

# agent-orchestrator — architecture overview

**Repo**: `IggyIkenna/agent-orchestrator` (renamed from `orchestrator-service` 2026-05-19)

**What it is**: A FastAPI + Vite-dashboard HTTP server that replaces file-based orchestration
(LEDGER.md + ping files + manual dispatch). Worker agents call `/boot`, `/progress`, `/done`,
`/blocked`, `/heartbeat` instead of reading/writing markdown files. State persists in SQLite
(`data/state/state.db`). Config (backlog, accounts, backends) is YAML/JSON under `data/config/`.

**Repo map pointer**: events → UTL · schemas → UAC · **orchestration → agent-orchestrator**
(see `cursor-configs/CLAUDE.md` § "System-First Architecture").

---

## Deployment shape

Mirrors `unified-trading-system-ui` (DART): Firebase Hosting in front of Cloud Run, single GCP
project `central-element-323112`, two env tiers (staging/prod as separate Cloud Run services).

```
Firebase Hosting  →  Cloud Run: agent-orchestrator-{staging|prod}  →  GCS state bucket
       |                           (europe-west4)
agent-orchestrator.staging.odum-research.com
agent-orchestrator.odum-research.com
```

Both domains are live (DNS + SSL provisioned 2026-05-19; see
`plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md` Phase 2).

**Prior deployment** (active until P5 prod cutover): laptop nginx + Let's Encrypt at
`orch.epiphanytechnologies.com` — 1-day fallback after prod cutover, then decommissioned.

**Local dev** (port 8026): see § "Local dev" below.

---

## Service bootstrap exemptions

Two QG steps are exempted (operator decision 2026-05-19):

- **QG STEP 5.61 (ServiceBootstrap)** — orchestrator has no `--asset-group`/`--mode` trading CLI;
  uvicorn-only startup. Source comment in `client-reporting-api` confirms the bootstrap is a
  token gesture; exempt here.
- **QG STEP 5.34 (typed config_reloaders.py)** — `server/config.py` is module-level env-driven
  functions; full compliance requires a config-class refactor deferred post-cutover.

`/health` + `/readiness` endpoints (QG STEP 5.62) are registered via UTL `make_health_router`
with `data_freshness` callback (state.json mtime + DB/backlog checks) — `agent-orchestrator@8e5a7e2`.

---

## Secret model — GCP Secret Manager

| Secret                        | Contents                          | Bound to                              |
| ----------------------------- | --------------------------------- | ------------------------------------- |
| `ORCHASTRATOR_JWT_SECRET`     | 32-byte random signing key        | Cloud Run service account (per env)   |
| `ORCHESTRATOR_GCS_BUCKET`     | env var (not SM) — bucket name    | set via `--set-env-vars` at deploy    |

Secrets bound via `gcloud run services update --update-secrets=...`. Staging and prod use separate
secrets. Local dev: set in `.env.local` (gitignored).

---

## Auth flip rationale

`server/auth.py::validate_credentials` is currently permissive (`ALLOW_ANONYMOUS=True`) — by
operator decision at launch, trading permissive auth for faster iteration. Strict auth flip is
Phase 3 of the Cloud Run deployment plan:

- Create `ORCHASTRATOR_JWT_SECRET` in Secret Manager
- Replace `validate_credentials` with argon2-hashed user list (schema from `scripts/manage_users.py`)
- Flip `auth.ALLOW_ANONYMOUS=False`
- Smoke test: 3-curl sequence (valid creds → 200, wrong password → 401, anonymous → 401)

**AUTH_INVENTORY.md** in the repo has the full flip-day checklist.

---

## GCS state mirror

Phase 5 (prod cutover) moves `data/state/state.json` from laptop disk to
`gs://agent-orchestrator-state-prod/` (europe-west4, 30-day version retention). Until P5:

- State persists on Harsh's laptop disk
- `SnapshotLoop` in `server/gcs_sync.py` runs every 30 min; uploads to GCS if
  `ORCHESTRATOR_GCS_BUCKET` is set

**Off-laptop continuity**: set `ORCHESTRATOR_GCS_BUCKET=agent-orchestrator-state-prod` on prod
Cloud Run → state survives a laptop outage. This is P5's primary reliability guarantee.

---

## Dashboard URLs

| Environment     | URL                                                 | Notes                                |
| --------------- | --------------------------------------------------- | ------------------------------------ |
| Production      | https://agent-orchestrator.odum-research.com        | P5 target — pending prod cutover     |
| Staging (UAT)   | https://agent-orchestrator.staging.odum-research.com | P1-P4 target                        |
| Local dev       | http://localhost:5173 (Vite dashboard)              | see § "Local dev"                    |
| Legacy fallback | https://orch.epiphanytechnologies.com               | active until P5+1 day, then removed  |

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

Note: Cloud Run uses `PORT=8080` internally (set in Dockerfile). Local dev uses 8026 per the
workspace port registry. The Vite dev server for the dashboard is always on `:5173` locally.

**Quality gates**: `bash scripts/check.sh` (ruff + basedpyright + prettier + tsc). No standard
`quality-gates.sh` integration — operator tooling exemption per the deployment plan.

---

## Deployment script

`deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh` (created at P1 of the
Cloud Run deployment plan). Shape mirrors `deploy-ui.sh`:

- Rejects missing `--env` flag
- Supports `--env=prod|uat`
- Reads `config/docker-build.env.{production,uat}` for build env vars

Registered in `codex/05-infrastructure/launcher-script-ssot.md` § "Cloud Run launchers".

---

## Plan reference

Full deployment plan (P0–P6):
`plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md`

Successor plans (post-P5):
- `plans/active/agent_orchestrator_workers_on_vms_2026_05_XX.md` — worker execution on VMs
- `plans/active/agent_orchestrator_multi_account_failover_2026_05_XX.md` — multi-account failover
- `plans/active/agent_orchestrator_slack_notifications_2026_05_XX.md` — Slack push notifications
