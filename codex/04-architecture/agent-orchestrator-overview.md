---
title: agent-orchestrator — architecture overview
created: 2026-05-19
author: ikenna-claude-subagent
scope: [engineer]
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
`port 8765 locally; agent-orchestrator.odum-research.com prod`).

Cross-links: operator runbook → `codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md`; infra/deploy reference
→ `codex/05-infrastructure/agent-orchestrator-deploy.md`; **central API host** (instance, ports, watchdog, auto-reboot,
resource limits, root-cause history) → `codex/05-infrastructure/agent-orchestrator-api-host.md`.

---

## Tech stack

| Layer    | Technology                                                                                                                                                                                                                                                                                                                                                              |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend  | FastAPI (Python 3.13), uvicorn, SQLAlchemy + SQLite (`data/state/state.db`)                                                                                                                                                                                                                                                                                             |
| Frontend | React + TypeScript + Vite (dashboard served by Firebase Hosting)                                                                                                                                                                                                                                                                                                        |
| Auth     | ES256 JWT (`PyJWT`); argon2 password hashing (`scripts/manage_users.py`). Internal proxy token: ES256 asymmetric, **HS256 retired 2026-06-01** (all 11 VMs sign ES256; private key distributed to every VM via the restricted creds bucket — central-only abandoned). Operator dashboard login JWT: HS256 (`ORCHESTRATOR_JWT_SECRET`, central-only — unaffected).       |
| Workers  | EC2 VMs (10 epic, AWS ap-northeast-1), 8 slots each on epic VMs = 80 worker slots; 1 central/orchestrator VM (id `planning`, `i-0c9b283b`, `13.113.200.22`) + 1 human planning VM (id `human-planning`, `i-0dd9812a`, `35.76.120.160`, 2 interactive slots) — human/central SPLIT 2026-06-12, see `orchestrator_human_central_vm_split_2026_06_12.md`. Total: 82 slots. |
| State    | SQLite (runtime) + `data/state/state.json` snapshot. See § "State persistence" below for cloud-backup specifics.                                                                                                                                                                                                                                                        |
| Deps     | `uv` + `uv.lock` (Python); `npm` + `package.json` (dashboard)                                                                                                                                                                                                                                                                                                           |
| QG       | `bash scripts/check.sh` — ruff + basedpyright + prettier + tsc                                                                                                                                                                                                                                                                                                          |

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
                        │  10 epic EC2 VMs, all :8765              │
                        │  vm-defi / vm-cefi / vm-tradfi / ...     │
                        │  (orchestrator backend per VM)           │
                        └──────────────────────────────────────────┘
```

The browser **never** reaches the epic VMs directly — only the central API has a public TLS endpoint. Per-VM ports
(:8765) are open to 0.0.0.0/0 in the security group as a fallback, but day-to-day traffic flows through the central
proxy. See § "Connectivity model — centralized API router" below.

Historical Cloud Run shape (`agent-orchestrator-{staging|prod}.run.app`, europe-west4) is documented in
[`../05-infrastructure/agent-orchestrator-deploy.md`](../05-infrastructure/agent-orchestrator-deploy.md) § "Cloud Run
service shape (HISTORICAL)" — not running, kept as cloud-agnostic fallback reference.

**Local dev** (port 8765): see § "Local dev" below.

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

## Secrets + buckets (refreshed 2026-05-28)

Three categories of secret / cloud-state surface. AWS is the primary cloud (per § "Fleet topology"); the GCP-side
equivalents are kept in sync for cloud-agnostic re-spin.

| Surface                                      | AWS path                                                                   | GCP path                                                                            | Used for                                                                     |
| -------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Per-VM env (JWT, Telegram, …)                | AWS Secrets Manager `ORCHESTRATOR_ENV_LOCAL`                               | GCP Secret Manager `ORCHESTRATOR_ENV_LOCAL`                                         | `bootstrap_vm.sh` writes `.env.local` on first boot                          |
| Per-account setup-token env files            | `s3://uts-orchestrator-creds-<account>/accounts/<id>.env`                  | `gs://central-element-323112-orchestrator-creds/accounts/<id>.env`                  | `CredsEnvPoller` syncs to local `~/.claude-accounts/` every 5 min            |
| VM lifecycle events (STARTED/STOPPED/FAILED) | `s3://uts-orchestrator-events-<account>/orchestrator/<role>/<vm>/STARTED`  | `gs://<project>-events/orchestrator/<role>/<vm>/STARTED`                            | `bootstrap_vm.sh` emits STARTED; STOPPED/FAILED deferred to SSH-spawn work   |
| State snapshot (state.json + SQLite)         | `s3://<bucket>/` controlled by `ORCHESTRATOR_S3_BUCKET` env (code shipped) | `gs://agent-orchestrator-state-prod/` (controlled by `ORCHESTRATOR_GCS_BUCKET` env) | `SnapshotLoop` in `server/gcs_sync.py` — 30-min auto + shutdown; both clouds |

Local dev: all of the above are no-ops when the corresponding env var is unset; state.json persists to local disk and
creds env files are operator-managed manually.

> **AWS↔S3 snapshot (code shipped 2026-06-01, agent-orchestrator@57dc8c2)**: `server/gcs_sync.py` now has
> `upload_state_to_s3` + `backup_sqlite_to_s3`, mirroring the GCS path and gated on `ORCHESTRATOR_S3_BUCKET` (no-op when
> unset, never-raise). When both `ORCHESTRATOR_GCS_BUCKET` and `ORCHESTRATOR_S3_BUCKET` are set the snapshot lands in
> both clouds. **Remaining operator step**: provision the S3 state bucket + set `ORCHESTRATOR_S3_BUCKET` on the 11 AWS
> VMs so the disaster-recovery loop is live (until then AWS hosts without a reachable GCS bucket still keep state on
> local disk). Tracked: `plans/active/orchestrator_autonomy_audit_remediation_2026_06_01.md` Phase 1.

---

## Auth flip rationale

`server/auth.py::validate_credentials` is currently permissive (`ALLOW_ANONYMOUS=True`) — by operator decision at
launch, trading permissive auth for faster iteration. Strict auth flip recipe (whenever the project is ready):

- Provision `ORCHESTRATOR_JWT_SECRET` (HS256 32-byte random) on the central VM only (operator JWT — never wire to
  workers).
- Provision the ES256 asymmetric key pair for internal proxy tokens (shipped 2026-06-01 via
  `orchestrator_asymmetric_auth`): private key stored in GCP Secret Manager; public key published to GCS
  `gs://central-element-323112-orchestrator-creds/orchestrator/internal-public.pem`. Workers set
  `ORCHESTRATOR_INTERNAL_PUBLIC_KEY_GCS=gs://…/internal-public.pem` in `.env.local`. **Every** orchestrator VM also sets
  `ORCHESTRATOR_INTERNAL_ALG=ES256` + `ORCHESTRATOR_INTERNAL_PRIVATE_KEY_GCS=gs://…/internal-private.pem` (all VMs sign,
  so all hold the private key — central-only abandoned 2026-06-01). **HS256 was RETIRED 2026-06-01** (agent-orchestrator
  @f44b948) once all 11 VMs verified ES256-signing — `decode_token` is ES256-only. (The 48h soak was superseded: the
  real gate is "all-ES256," reached minutes after the last signer flips given the 5-min internal-token TTL.)
- Replace `validate_credentials` with argon2-hashed user list (schema from `scripts/manage_users.py`)
- Flip `auth.ALLOW_ANONYMOUS=False`
- Smoke test: 3-curl sequence (valid creds → 200, wrong password → 401, anonymous → 401)

**AUTH_INVENTORY.md** in the repo has the full flip-day checklist.

---

## State persistence

Runtime state lives in SQLite at `data/state/state.db`. Periodic snapshots (`state.json` mirror + SQLite hot-copy) fire
from `SnapshotLoop` in `server/gcs_sync.py` — environment-controlled cadence (default 30 min auto + shutdown; override
via `ORCHESTRATOR_SNAPSHOT_INTERVAL_SECONDS`). Snapshots are uploaded to GCS when `ORCHESTRATOR_GCS_BUCKET` is set;
otherwise local-only.

See the "Secrets + buckets" table above for the current cloud bucket layout + the AWS↔S3 known-gap on state snapshots.

---

## Dashboard URLs

| Environment    | URL                                                            | Notes                                                                |
| -------------- | -------------------------------------------------------------- | -------------------------------------------------------------------- |
| Production SPA | https://agent-orchestrator.odum-research.com                   | Firebase Hosting; talks to central API below                         |
| Central API    | https://api.agent-orchestrator.odum-research.com               | EC2 VM `13.113.200.22`, nginx → app :8765 (verified live 2026-05-28) |
| Local dev      | http://localhost:5173 (Vite) + http://localhost:8765 (backend) | see § "Local dev"                                                    |

---

## Fleet git-health page (shipped 2026-06-10)

`GET /api/fleet/git-health?scope=fleet|local` (`server/server.py`) aggregates every slot's stored `SlotGitStatus`
(`POST/GET /api/slots/{id}/git-status`) into a hosts → slots → repos surface. `scope=fleet` (default) merges this host's
local view with every registered VM's `scope=local` view via the existing `/api/vms/<id>/*` proxy fan-out (the
`/api/fleet/summary` pattern); `scope=local` is the per-VM leaf (no recursion). Derivations beyond the per-slot badge:

- `reporter_stale` — `reported_at` older than 10 min (a dead `slot-git-status-report.sh` cron is a first-class red
  state, not a silent gap).
- `ff_cron_stale` — `git_status_ff_pull_last_run` older than 15 min, **only when attested** (the reporter posts
  `ff_pull_last_run`/`ff_pull_last_result` from the host-global result file `slot-cron-ff-pull.sh` writes each sweep);
  un-attested = honest-unknown, never falsely "dead".
- `drift_violation` — per repo, state `ahead`/`diverged` vs `origin/live-defi-rollout` (the Path-B invariant from
  `scripts/cicd/slot_drift_check.py`); rolled up to `drift_violations[]`.
- `vm_errors[]` — honest per-VM proxy failure (unreachable/bad-payload), never a fabricated row.

Dashboard: the `/fleet-git` SPA route (`dashboard/src/FleetGit.tsx`) — summary chips + per-host slot rows with
worst-first badges (reporter-dead / ff-pull-dead / drift / dirty / behind) + expandable per-repo detail. Per operator
decision v2 (2026-06-10) the PRIMARY operator view is mirrored into **deployment-ui** (`/fleet` tab, via deployment-api
`GET /api/repo-ci/fleet-git-health` proxying this endpoint with the SM `ORCHESTRATOR_API_TOKEN`); this orchestrator page
stays for worker-ops use. Plan: `fleet_git_health_orchestrator_2026_06_10.md`; full division-of-surfaces + click-through
contract: `codex/03-observability/monitoring-control-plane.md`.

---

## Local dev — port 8765

Port 8765 is registered in `unified-trading-pm/scripts/dev/ui-api-mapping.json`.

```bash
cd agent-orchestrator

# One-time setup
uv venv && uv sync
.venv/bin/pre-commit install --install-hooks
cd dashboard && npm install && cd ..

# Boot everything (backend :8765 + Vite dashboard :5173)
scripts/dev.sh          # live mode
scripts/dev.sh --mock   # demo mode
```

Note: the central API VM listens on `127.0.0.1:8765` behind nginx (TLS terminated at :443). Fleet VMs listen on
`0.0.0.0:8765` directly (no nginx, no per-VM TLS — the central API proxies to them over the private VPC). Local dev uses
:8765 per the workspace port registry. Vite dev server is always `:5173` locally.

**Quality gates**: `bash scripts/check.sh` (ruff + basedpyright + prettier + tsc). No standard `quality-gates.sh`
integration — operator tooling exemption.

---

## Slack notifications

Block Kit push notifications to `#agent-orchestrator-alerts` via incoming webhook. Shipped at
`agent-orchestrator@cd04fc2` (Block Kit + retry + `blocked_id` dashboard link).

`AGENT_ORCHESTRATOR_SLACK_WEBHOOK` is loaded from the per-VM `.env.local` (provisioned via the `ORCHESTRATOR_ENV_LOCAL`
secret). `_post()` no-ops when the webhook URL is empty so local dev / mock runs don't require Slack credentials.
async→sync httpx conversion was applied 2026-05-21 to fix an asyncio.run-in-sync-endpoint bug that was silently
suppressing all calls.

**SSOT**: `codex/05-infrastructure/agent-orchestrator-slack-notifications.md` (event table, payload shape, retry logic,
secret inventory, V2 out-of-scope).

---

## Deployment scripts

Two paths today (AWS is primary; GCP retained for cloud-agnostic re-spin):

| Target                      | Script                                                              | Cloud                   |
| --------------------------- | ------------------------------------------------------------------- | ----------------------- |
| Epic VM launch              | `deployment-service/scripts/vm/launch-epic-vm-aws.sh`               | AWS                     |
| Epic VM launch              | `deployment-service/scripts/vm/launch-epic-vm.sh`                   | GCP                     |
| Per-VM bootstrap            | `agent-orchestrator/scripts/bootstrap_vm.sh` (CLOUD_PROVIDER aware) | both                    |
| Central API VM systemd unit | `agent-orchestrator/scripts/install-orchestrator-service.sh`        | AWS (EC2 13.113.200.22) |

Historical Cloud Run deploy script `deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh` is retained in
the repo (referenced in `codex/05-infrastructure/launcher-script-ssot.md` § "Cloud Run launchers") for re-spin
optionality; the Cloud Run shape is **not currently deployed** — see
[`../05-infrastructure/agent-orchestrator-deploy.md`](../05-infrastructure/agent-orchestrator-deploy.md) § "Cloud Run
service shape (HISTORICAL)".

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
`server/regen_backlog_from_plan.py`. Background `PlanRegenLoop` fires 60s after server boot, then every 30 min
(`ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` default 1800, 0 disables). A complementary `pm-pull.timer` systemd unit
FF-pulls `unified-trading-pm` from LDR every 5 min, so the effective push-to-pickup latency is ≤35 min. Manual immediate
trigger: `POST /api/backlog/regen`.

Idempotency is content-based (dedup by `BacklogTask.brief == raw todo line`); editing a todo's wording creates a new
task, flipping to `- [x]` simply stops the regen from seeing it (existing BacklogTask state in SQLite is preserved via
`dispatched_to`, `done_sha`, etc.). Hand-tuning derived tasks' `priority` / `repos` / `target_slot` / `collision_group`
post-regen is supported; the dedup key is the brief, not the tuning fields.

**`execution_scope` frontmatter (codified 2026-06-02)** gates ingestion at the plan level. A plan with
`execution_scope: local-only` is skipped entirely by `regen_backlog_from_plan.py` (regardless of `assigned_vm`) — use it
for coordination / design / operator-driven plans whose work is done + verified locally, not dispatched to a worker. The
field is optional; absent ⇒ `orchestrator-agent` (ingested as normal, so no backfill of existing plans). It is a closed
set of two — there is no `hybrid`. Enforced by `_parse_frontmatter_execution_scope`. SSOT: `plans/PLAN_FORMAT.md` §
"YAML Frontmatter Schema".

CLAUDE.md HARD RULE "Agent-orchestrator backlog is plan-driven" (added 2026-05-28) is the workspace contract. SSOTs:
[`../12-agent-workflow/orchestrator-multi-vm-topology.md`](../12-agent-workflow/orchestrator-multi-vm-topology.md) §
"Backlog auto-generation per VM"; `server/regen_backlog_from_plan.py` + `tests/test_regen_backlog_from_plan.py` (29-test
suite).

---

## Auth — long-lived setup-tokens (Phase 4b-cleanup, shipped 2026-05-28)

Every account in `data/config/accounts.json` authenticates via an `oauth_token_env_file` (`~/.claude-accounts/<id>.env`,
containing `CLAUDE_CODE_OAUTH_TOKEN=<sk-ant-oat01-...>` + `unset ANTHROPIC_API_KEY`). Spawn paths (workers, agents,
`/usage` probes) all source the env file before `exec claude` and refuse with HTTP 400 when the env file is missing.
Legacy `.credentials.json` swap path + `oauth_refresh` module + `gcs_creds_poller` are gone; only `creds_env_poller`
(5-min cross-cloud bucket sync) remains.

SSOTs:
[`../12-agent-workflow/claude-cli-multi-account-headless-auth.md`](../12-agent-workflow/claude-cli-multi-account-headless-auth.md)
(the auth model) +
[`../12-agent-workflow/orchestrator-safety-mechanisms.md`](../12-agent-workflow/orchestrator-safety-mechanisms.md) § B
(rate-limit failover — slot respawn with new env file, not mid-session token swap).

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

## Fleet topology (refreshed 2026-06-01; SPLIT 2026-06-12)

Current state: **1 central/orchestrator VM (id `planning`, `i-0c9b283b`) + 1 human planning VM (id `human-planning`,
`i-0dd9812a`) + 10 epic VMs**, all on AWS EC2 `ap-northeast-1`, all running orchestrator v0.6.0+ (human/central SPLIT
2026-06-12 — see `orchestrator_human_central_vm_split_2026_06_12.md`; supersedes the prior merged "central API/planning
VM"). The GCP fleet that was commissioned 2026-05-21 was decommissioned during the 2026-05-22→23 AWS migration; no GCP
VMs are running today.

Current per-VM addresses + slot counts: see
[`../05-infrastructure/agent-orchestrator-worker-topology.md`](../05-infrastructure/agent-orchestrator-worker-topology.md)
§ "Current fleet — AWS EC2 ap-northeast-1" — that doc is the authoritative IP / instance-id table and the only place
these numbers should live (avoid duplicating here so the two don't drift). Live runtime backends + account mapping live
in `agent-orchestrator/data/config/backends.json`.

Total worker capacity: 2 (human-planning VM interactive slots) + 80 (10 epic VMs × 8) = **82 slots**. (Since the
2026-06-12 split the central / orchestrator VM (id `planning`) serves the central API/routing + orchestrator roles with
no human daily work; the 2 interactive slots counted above live on the separate `human-planning` VM.) Registry SSOT:
`unified-trading-pm/orchestrator_vm_registry.yaml`.

**Cloud-agnostic posture**: AWS is the current and only running cloud. The bootstrap (`bootstrap_vm.sh`), launchers
(`launch-epic-vm-aws.sh` / `launch-epic-vm.sh`), and secrets / event-bus code all support a `CLOUD_PROVIDER=aws|gcp`
toggle — the GCP path is fully maintained so the fleet can be re-spun on GCE if AWS ever becomes unavailable or pricing
changes the calculus, but **there is no plan to switch back**. New work targets AWS by default.

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
- **Auth (asymmetric model, codified 2026-06-01)**: the central API uses two independent secrets/keys:
  - `ORCHESTRATOR_JWT_SECRET` — operator dashboard login JWT only. **Central-only** (never wired into worker
    `.env.local`). HS256. Validates the Bearer token on every authed request that enters at the public edge.
  - **ES256 asymmetric key pair** (`ORCHESTRATOR_INTERNAL_ALG=ES256`) — central↔worker proxy auth. **HS256 RETIRED
    2026-06-01** (agent-orchestrator@f44b948): `decode_token()` accepts ES256-only and `_issue_internal_token()` signs
    ES256-only (raises without a private key — no HS256 fallback). Verified across all 11 orchestrator VMs (each
    `INTERNAL_ALG=ES256`, private key resolvable, orchestrator active). **Key distribution changed (central-only
    abandoned, operator decision 2026-06-01):** because every orchestrator VM proxies to its own slots and therefore
    signs, the private key is distributed to ALL VMs via the restricted creds bucket
    (`ORCHESTRATOR_INTERNAL_PRIVATE_KEY_GCS=gs://central-element-323112-orchestrator-creds/orchestrator/internal-private.pem`)
    - public key via `ORCHESTRATOR_INTERNAL_PUBLIC_KEY_GCS=.../internal-public.pem`. NB: the raw
      `ORCHESTRATOR_INTERNAL_SECRET` object is RETAINED (NOT deleted) — it is the pre-shared key for
      `verify_internal_secret()` → `POST /api/escalate` (GHA→orchestrator dispatch); only the HS256 _JWT_ accept/sign
      paths were retired.
  - **Flow**: operator hits central with their JWT. The central validates against `ORCHESTRATOR_JWT_SECRET` at the
    perimeter, terminates that token, then mints a fresh short-lived (5 min, role=worker, machine=central-proxy) JWT
    signed with the ES256 private key and forwards THAT in the upstream `Authorization` header. Workers validate against
    their copy of the public key only — they never see the operator secret. (`server/server.py::proxy_to_vm`;
    `auth.get_internal_service_token()`.)
  - Operator-credential exposure is bounded to the central VM. An upstream VM compromise can't impersonate the operator.
- **Routing**: `ORCHESTRATOR_USE_PRIVATE_URLS=true` on the central API makes the proxy target each backend's
  `private_url` (`172.31.x.x`, all VMs in `vpc-6ee70e08`/`subnet-fc09eca6`, ap-northeast-1).
- **Registry**: `data/config/backends.json` (static, with `url` + `private_url`) merged with `fleet_registry.json`
  (dynamic). VMs **self-register** on boot via outbound `POST /api/vms/register` (`bootstrap_vm.sh` step 10).

**Registry/worker drift resolved**: the earlier `orchestrator_vm_registry.yaml` per-VM-FQDN model (browser→each-VM) is
**superseded** by this centralized model — workers do NOT get per-VM FQDNs; the central API reaches them by private IP.
`worker.md`'s outbound-POST mental model is the correct one. Plan shipped under archived
`plans/archive/2026_05/multi_backend_fleet_connectivity_2026_05_22.md`.

Cross-side coordination:

- `unified-trading-pm/plans/active/_agent_pings.md` (workspace-shared cross-side log)
- Daily work-split files `plans/active/work_split_<date>_<operator>.md`
- Git: tab branches + `live-defi-rollout` auto-FF via `tab-mirror-to-ldr.yml`

## Auto-spawn lifecycle (AutoSpawnLoop — shipped 2026-05-30)

`server/autospawn.py` — `AutoSpawnLoop` — periodic background thread (default 60 s tick) that wakes a worker on idle
slots so the fleet self-heals without operator intervention.

### Trigger contract (all 5 must be true to spawn)

| #   | Gate                 | Implementation                                                                                                                 |
| --- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1   | **Queue not empty**  | `SELECT task_id FROM tasks WHERE status='queued' AND dispatched_to IS NULL LIMIT 1` → non-empty                                |
| 2   | **No active worker** | `tmux has-session orch-slot-N` returns false                                                                                   |
| 3   | **Account headroom** | At least one usable account: `five_hour_pct < 50` AND `weekly_pct < 80`. Null pct treated as 0 (fresh account assumed healthy) |
| 4   | **Slot configured**  | `slots` table has `worktree` + `branch` + `operator` set                                                                       |
| 5   | **Not in cooldown**  | Last autospawn attempt for this slot was > 5 min ago (`ORCHESTRATOR_AUTOSPAWN_COOLDOWN_SECONDS`, default 300)                  |

### Account-pick rotation

`_pick_headroom_account()` — scans `accounts.json`, filters by `account_is_usable()` + headroom gates, sorts by
`(five_hour_pct ASC, weekly_pct ASC)`. First account in the sorted list wins. Spreads load across the rotation pool;
skips any account that is rate-limited or beyond the ceiling thresholds.

### Spawn execution

`_do_spawn()` calls `prompts.render("worker", ...)` to get the boot prompt (same template as the manual
`/api/slots/<id>/spawn` endpoint), then `tmux_spawn.spawn()` — same in-process path used by the manual API. The spawned
worker's first `/heartbeat` or `/boot` call updates the `SlotRow`.

### Anti-flap / Slack alert

After 3 consecutive successful spawns on the same slot within 10 min (`DEFAULT_FLAP_THRESHOLD=3`,
`DEFAULT_FLAP_WINDOW_SECONDS=600`) without a task claim — `notify_autospawn_flap()` fires a Slack alert and the slot
enters a 1-hour backoff (`_flap_backoff_until[slot_id]`). A mixed success/failure sequence resets the streak.

### Failure modes and logging

| Failure                   | How handled                                                                              |
| ------------------------- | ---------------------------------------------------------------------------------------- |
| Boot-prompt render failed | `_do_spawn()` returns `(False, error_str)`; logged as `autospawn_failed` activity event  |
| Spawn HTTP 4xx (via tmux) | `tmux_spawn.spawn()` raises; caught → `spawn_failures` counter incremented, cooldown set |
| tmux create failed        | Same as above                                                                            |
| All accounts at ceiling   | Gate 3 blocks; tick skips with `no_account_headroom` reason                              |
| Slot not configured       | Gate 4 blocks; tick skips with `slot_not_configured` reason                              |

Every spawn attempt logs to `log_activity` with `autospawn_succeeded` or `autospawn_failed` event type.

### Environment variables

| Variable                                   | Default | Purpose                            |
| ------------------------------------------ | ------- | ---------------------------------- |
| `ORCHESTRATOR_AUTOSPAWN_ENABLED`           | `false` | Master on/off switch               |
| `ORCHESTRATOR_AUTOSPAWN_INTERVAL_SECONDS`  | `60`    | Tick cadence                       |
| `ORCHESTRATOR_AUTOSPAWN_COOLDOWN_SECONDS`  | `300`   | Per-slot retry gap                 |
| `ORCHESTRATOR_AUTOSPAWN_FIVE_HOUR_CEILING` | `50`    | Max 5h usage % before skipping     |
| `ORCHESTRATOR_AUTOSPAWN_WEEKLY_CEILING`    | `80`    | Max weekly usage % before skipping |

Enable via systemd drop-in: `Environment=ORCHESTRATOR_AUTOSPAWN_ENABLED=true` in
`/etc/systemd/system/orchestrator.service.d/autospawn.conf` — one VM at a time. Rollout script:
`unified-trading-pm/scripts/orchestrator/enable_autospawn.sh`.

SSOT: `server/autospawn.py` + `plans/active/autospawn_idle_vms_2026_05_30.md`.

### AutoSpawnLoop — extended failure modes

The table above lists 5 failure modes. A 6th is handled by the watchdog layer (see § below):

| Failure                                  | How handled                                                                                                            |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| tmux alive but stuck/silent/context-full | **Handled by WorkerLivenessWatchdog** — watchdog kills tmux; AutoSpawnLoop respawns on next tick (60–180 s round trip) |

## Worker liveness watchdog (WorkerLivenessWatchdog — shipped 2026-06-01)

`server/worker_liveness_watchdog.py` — daemon thread (60s tick) that **kills** tmux sessions invisible to
`AutoSpawnLoop` (which only checks `tmux has-session`). After kill, AutoSpawnLoop respawns within 60s.

### Three trigger contracts

| Pattern              | Signal                                                                                      | Threshold              |
| -------------------- | ------------------------------------------------------------------------------------------- | ---------------------- |
| **Stuck-at-prompt**  | Pane has non-empty text after `❯` AND pane content unchanged across 3 consecutive ticks     | **180s** (3 × 60s)     |
| **Heartbeat-silent** | `slot.last_heartbeat_at` older than threshold AND tmux alive AND `slot.status != 'blocked'` | **>900s** (15 min)     |
| **Context-full**     | Pane matches `/clear to save .{1,10}k tokens/i`                                             | **Immediate** (1 tick) |

### Anti-thrash gates

- Per-slot 5-min kill cooldown.
- Per-VM daily cap of 20 kills → Slack alert + watchdog dormancy until operator reset.

### Debounce vs WorkerLivenessKicker

`WorkerLivenessKicker` (`server/worker_liveness.py`) **nudges** via keystroke injection first; the watchdog **kills**
directly on independent thresholds. The two compose: kicker for shallow freezes; watchdog for deeper stuck/silent/full
patterns. If `WorkerLivenessKicker` kicked within the debounce window, the watchdog skips that slot.

### Environment variables

| Variable                               | Code default | Systemd-deployed default        |
| -------------------------------------- | ------------ | ------------------------------- |
| `ORCHESTRATOR_WORKER_WATCHDOG_ENABLED` | `false`      | `true` on 10/11 VMs (see below) |

**Known gap**: `vm-ml` has a broken SSM path — watchdog not yet installed there. All other 10 VMs have the systemd
drop-in enabled. Track: `plans/active/agent_orchestrator_worker_liveness_watchdog_2026_06_01.md`.

SSOT: `codex/04-architecture/agent-orchestrator-worker-liveness.md` (full trigger contracts, anti-thrash, kill
execution, interaction with AutoSpawnLoop).

## Host-offline failover lifecycle (FailoverLoop — design 2026-05-30)

Addresses the case where a host (e.g. harsh-pc) goes offline and its soft-pinned tasks would otherwise sit indefinitely.
The `FailoverLoop` runs in `server/failover.py` on vm-orchestrator only (single decision source; per-VM enables would
race).

### Trigger contract

| Gate                | Condition                                                                                                               |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Host offline        | `last_heartbeat_age > 600s` (10 min) for the source host — conservative threshold for laptop sleep / brief network gaps |
| Task soft-pinned    | `target_slot IS NULL` OR `target_slot.failover_allowed = true`                                                          |
| Task not dispatched | `dispatched_to IS NULL` AND `status = 'queued'`                                                                         |
| Fleet VM available  | At least one fleet VM passes affinity-match AND account-headroom check (re-uses AutoSpawnLoop § 3 contract)             |

### Affinity-matching algorithm

For each eligible task, pick the best fleet VM by priority:

1. **Repo overlap**: `task.repos` ⊆ `vm.master_plans` entries (per `orchestrator_vm_registry.yaml`)
2. **Asset group**: `task.asset_group` matches `vm.asset_group`
3. **Collision group**: `task.collision_group` not already active on the target
4. **Least loaded**: fewest `status='queued'` tasks in target VM's `state.db`

First VM that passes all applicable filters wins. On tie, random among finalists.

### Soft vs hard pin distinction

- **Soft pin** (`failover_allowed: true`, default for all tasks): eligible for failover.
- **Hard pin** (`failover_allowed: false`): NEVER failovered — operator may have explicit reasons (debug, audit, manual
  run). Hard pins are opt-in, set via `failover_allowed: false` in the source plan task YAML.

Re-assignment writes `task.target_slot = <fleet_vm_slot_id>` + `task.failover_origin = "<offline_host>"` for audit.

### Rollback on heartbeat-return

When the offline host's heartbeat returns:

- For each failovered task with `failover_origin = <host>` AND `dispatched_to IS NULL` (still unclaimed on fleet
  target): restore `target_slot` to original harsh-pc value + clear `failover_origin`.
- Already-claimed or already-done tasks stay where they ran — no rollback.
- Rollback fires within one `FailoverLoop` tick (default 60s) of heartbeat resuming.

### Audit trail

`task.failover_origin` persists the source host name. The cached last heartbeat snapshot from the offline host is
**never deleted** on failover — it remains visible in `/api/fleet/summary` as audit evidence of what was stranded.

### Env vars

| Variable                                            | Default | Effect                             |
| --------------------------------------------------- | ------- | ---------------------------------- |
| `ORCHESTRATOR_FAILOVER_ENABLED`                     | `false` | Must be `true` to arm FailoverLoop |
| `ORCHESTRATOR_FAILOVER_INTERVAL_SECONDS`            | `60`    | Tick interval                      |
| `ORCHESTRATOR_FAILOVER_HEARTBEAT_THRESHOLD_SECONDS` | `600`   | Offline threshold (10 min)         |

Enable via drop-in: `/etc/systemd/system/orchestrator.service.d/failover.conf` on vm-orchestrator only. Rollout script:
`unified-trading-pm/scripts/orchestrator/enable_failover.sh` (Phase 4).

### Anti-patterns

- **Never failover hard-pinned tasks** (`failover_allowed: false`)
- **Never failover dispatched tasks** (`dispatched_to IS NOT NULL`) — steal-attempt = race + duplicate work
- **Never failover api-host queue** — planning VM, not worker-dispatched
- **Never delete the cached heartbeat snapshot** on failover

SSOT: `server/failover.py` (Phase 3) + `plans/active/harsh_pc_dispatch_failover_2026_05_30.md`.

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
