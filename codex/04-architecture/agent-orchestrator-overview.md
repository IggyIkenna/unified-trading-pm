---
title: agent-orchestrator — architecture overview
created: 2026-05-19
author: ikenna-claude-subagent
scope: infrastructure
status: active
last_reviewed: 2026-05-28
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

| Layer        | Technology                                                                                                                                |
| ------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Backend      | FastAPI (Python 3.13), uvicorn, SQLAlchemy + SQLite (`data/state/state.db`)                                                               |
| Frontend     | React + TypeScript + Vite (dashboard served by Firebase Hosting)                                                                          |
| Auth         | HS256 JWT (`PyJWT`); argon2 password hashing (`scripts/manage_users.py`)                                                                  |
| Workers      | 10 epic EC2 VMs (AWS ap-northeast-1), 8 slots each = 80 worker slots; 1 central API VM (`13.113.200.22`, 2 planning slots).               |
| State        | SQLite (runtime) + `data/state/state.json` snapshot (30-min auto + shutdown)                                                              |
| Cloud backup | S3 / GCS — current fleet uses `s3://uts-orchestrator-creds-…` + `s3://uts-orchestrator-events-…`; GCS path retained for cloud-agnostic re-spin |
| Deps         | `uv` + `uv.lock` (Python); `npm` + `package.json` (dashboard)                                                                             |
| QG           | `bash scripts/check.sh` — ruff + basedpyright + prettier + tsc                                                                            |

---

## Deployment shape (refreshed 2026-05-28)

Current production shape — Firebase Hosting SPA + central API VM + private-VPC proxy to fleet:

```
                        Firebase Hosting
                        agent-orchestrator.odum-research.com   (dashboard SPA)
                                │ HTTPS
                                ▼
                        api.agent-orchestrator.odum-research.com   (HTTPS, nginx :443)
                        Central API VM (EC2 13.113.200.22, ap-northeast-1)
                        nginx → orchestrator backend :8765
                                │ private VPC (172.31.x.x)
                                │ ORCHESTRATOR_USE_PRIVATE_URLS=true
                                ▼
                        ┌──────────────────────────────────────────┐
                        │  10 epic EC2 VMs, all :8026              │
                        │  vm-defi / vm-cefi / vm-tradfi / ...     │
                        │  (orchestrator backend per VM)           │
                        └──────────────────────────────────────────┘
```

The browser **never** reaches the epic VMs directly — only the central API has a public TLS endpoint. Per-VM ports
(:8026) are open to 0.0.0.0/0 in the security group as a fallback, but day-to-day traffic flows through the central
proxy. See § "Connectivity model — centralized API router" below.

Historical Cloud Run shape (`agent-orchestrator-{staging|prod}.run.app`, europe-west4) is documented in
[`../05-infrastructure/agent-orchestrator-deploy.md`](../05-infrastructure/agent-orchestrator-deploy.md) §
"Cloud Run service shape (HISTORICAL)" — not running, kept as cloud-agnostic fallback reference.

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

| Environment     | URL                                                  | Notes                                                                |
| --------------- | ---------------------------------------------------- | -------------------------------------------------------------------- |
| Production SPA  | https://agent-orchestrator.odum-research.com         | Firebase Hosting; talks to central API below                         |
| Central API     | https://api.agent-orchestrator.odum-research.com     | EC2 VM `13.113.200.22`, nginx → app :8765 (verified live 2026-05-28) |
| Local dev       | http://localhost:5173 (Vite) + http://localhost:8026 (backend) | see § "Local dev"                                          |

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

## Backlog auto-generation from plans (Phase 6 — shipped 2026-05-28)

`data/config/backlog.yaml` is **derived from `plans/active/*.md` `- [ ]` checkboxes**, not hand-edited. Source module:
`server/regen_backlog_from_plan.py`. Background `PlanRegenLoop` fires 60s after server boot, then every 6h
(`ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS`, 0 disables). Manual immediate trigger: `POST /api/backlog/regen`.

Idempotency is content-based (dedup by `BacklogTask.brief == raw todo line`); editing a todo's wording creates a new
task, flipping to `- [x]` simply stops the regen from seeing it (existing BacklogTask state in SQLite is preserved
via `dispatched_to`, `done_sha`, etc.). Hand-tuning derived tasks' `priority` / `repos` / `target_slot` /
`collision_group` post-regen is supported; the dedup key is the brief, not the tuning fields.

CLAUDE.md HARD RULE "Agent-orchestrator backlog is plan-driven" (added 2026-05-28) is the workspace contract. SSOTs:
[`../12-agent-workflow/orchestrator-multi-vm-topology.md`](../12-agent-workflow/orchestrator-multi-vm-topology.md) §
"Backlog auto-generation per VM"; `server/regen_backlog_from_plan.py` + `tests/test_regen_backlog_from_plan.py`
(29-test suite).

---

## Auth — long-lived setup-tokens (Phase 4b-cleanup, shipped 2026-05-28)

Every account in `data/config/accounts.json` authenticates via an `oauth_token_env_file`
(`~/.claude-accounts/<id>.env`, containing `CLAUDE_CODE_OAUTH_TOKEN=<sk-ant-oat01-...>` + `unset
ANTHROPIC_API_KEY`). Spawn paths (workers, agents, `/usage` probes) all source the env file before `exec claude`
and refuse with HTTP 400 when the env file is missing. Legacy `.credentials.json` swap path + `oauth_refresh`
module + `gcs_creds_poller` are gone; only `creds_env_poller` (5-min cross-cloud bucket sync) remains.

SSOTs: [`../12-agent-workflow/claude-cli-multi-account-headless-auth.md`](../12-agent-workflow/claude-cli-multi-account-headless-auth.md)
(the auth model) + [`../12-agent-workflow/orchestrator-safety-mechanisms.md`](../12-agent-workflow/orchestrator-safety-mechanisms.md)
§ B (rate-limit failover — slot respawn with new env file, not mid-session token swap).

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

## Fleet topology (refreshed 2026-05-28)

Current state: **1 central API VM + 10 epic VMs, all on AWS EC2 `ap-northeast-1`**, all running orchestrator
v0.6.0+. The GCP fleet that was commissioned 2026-05-21 was decommissioned during the 2026-05-22→23 AWS migration;
no GCP VMs are running today.

Current per-VM addresses + slot counts: see
[`../05-infrastructure/agent-orchestrator-worker-topology.md`](../05-infrastructure/agent-orchestrator-worker-topology.md)
§ "Current fleet — AWS EC2 ap-northeast-1" — that doc is the authoritative IP / instance-id table and the only
place these numbers should live (avoid duplicating here so the two don't drift). Live runtime backends + account
mapping live in `agent-orchestrator/data/config/backends.json`.

Total worker capacity: 2 (central / planning slots) + 80 (10 × 8) = **82 slots**. Registry SSOT:
`unified-trading-pm/orchestrator_vm_registry.yaml`.

**Cloud-agnostic posture**: AWS is the current and only running cloud. The bootstrap (`bootstrap_vm.sh`),
launchers (`launch-epic-vm-aws.sh` / `launch-epic-vm.sh`), and secrets / event-bus code all support a
`CLOUD_PROVIDER=aws|gcp` toggle — the GCP path is fully maintained so the fleet can be re-spun on GCE if AWS ever
becomes unavailable or pricing changes the calculus, but **there is no plan to switch back**. New work targets AWS
by default.

## Connectivity model — centralized API router (2026-05-22)

The dashboard talks to **one** backend: the central API (`api.agent-orchestrator.odum-research.com`), which **proxies to
every worker VM server-side over the private VPC**. The browser never reaches a worker VM directly — so workers need
**no public IP, no per-VM TLS, no DNS**; only the central API has a public HTTPS endpoint. Same shape as
unified-trading-system (one API fronts the UI; services isolated behind it). The central API is a **router, not a wall**
— full per-VM control is preserved via the proxy.

- **Fleet view**: `GET /api/fleet/summary` fans out to each backend's `/api/vm/summary` server-side (httpx, parallel).
- **Per-VM control**: `<central>/api/vms/<id>/<path>` → forwarded to that VM's `private_url` over the VPC (spawn / kill
  / pause / message / state / logs). The dashboard sets `baseUrl = <central>/api/vms/<id>` so existing `/api/*` calls
  route through unchanged.
- **Auth**: one JWT secret (`ORCHESTRATOR_JWT_SECRET` env var) shared fleet-wide; one login → one token valid on every
  (incl. proxied) call. `JWT_ALGORITHM` env-driven (HS256 now; RS256/ES256 seam for later). GCS-based hot-reload
  (`ORCHESTRATOR_JWT_SECRET_GCS`) is code-complete but VMs' ADC lacks `storage.objectViewer` on the creds bucket — P3
  deferred; SSOT until then is the `ORCHESTRATOR_JWT_SECRET` env var distributed to all VMs.
- **Routing**: `ORCHESTRATOR_USE_PRIVATE_URLS=true` on the central API makes the proxy target each backend's
  `private_url` (`172.31.x.x`, all VMs in `vpc-6ee70e08`/`subnet-fc09eca6`, ap-northeast-1).
- **Registry**: `data/config/backends.json` (static, with `url` + `private_url`) merged with `fleet_registry.json`
  (dynamic). VMs **self-register** on boot via outbound `POST /api/vms/register` (`bootstrap_vm.sh` step 10).

**Registry/worker drift resolved**: the earlier `orchestrator_vm_registry.yaml` per-VM-FQDN model (browser→each-VM) is
**superseded** by this centralized model — workers do NOT get per-VM FQDNs; the central API reaches them by private IP.
`worker.md`'s outbound-POST mental model is the correct one. Plan:
`plans/active/multi_backend_fleet_connectivity_2026_05_22.md`.

Cross-side coordination:

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
- `plans/active/aws_epic_vm_fleet_2026_05_22.md` — AWS EC2 fleet (CLOUD_PROVIDER toggle; GCP working, AWS in progress)
- `plans/epics/orchestrator_master.md` — multi-VM topology epic (SSH-spawn, DNS, preflight deferred items)

Archived plans:

- `plans/archive/epic_vm_fleet_commissioning_2026_05_21.plan.md` — GCP fleet commissioning (DONE 2026-05-22)
- `plans/archive/agent_orchestrator_workers_on_vms_2026_05_19.plan.md` — old asymmetric model (superseded)

Resolved/closed issues:

- `plans/archive/issues/orchestrator_spawn_tmux_silent_failure_2026_05_20.md` (RESOLVED 2026-05-20 — spawn endpoint tmux
  daemon silent-fail + workspace-trust prompt unhandled; fix shipped at `agent-orchestrator@e975f19` +
  `scripts/install-orchestrator-service.sh` at `agent-orchestrator@dc535b2` to prevent recurrence)
