---
doc_type: codex-ssot
title: agent-orchestrator — service-implementation reference
summary:
  Service-implementation reference for agent-orchestrator — tech stack, auth model (ES256 internal / HS256 dashboard),
  the centralized-API connectivity model, secrets/buckets, state persistence, dashboard, local dev, deploy scripts, the
  AgentKeeper + agent-type oversight surfaces, and the service-vs-trading boundary. The architecture & operating model
  (topology, the two worker classes, worker/task lifecycle, dispatch, regen) lives in the single-VM SSOT; this doc is
  the implementation layer under it. Explicitly NOT a trading service.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, deployment-api, deployment-service, deployment-ui]
scope: [engineer]
tags: [orchestrator, infrastructure, auth, connectivity, secrets, dashboard, agentkeeper, service-reference]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/05-infrastructure/agent-orchestrator-api-host.md,
  ]
created: 2026-05-19
authoritative_for: [agent-orchestrator service-implementation reference, agent-orchestrator auth + connectivity model]
referenced_by:
  [
    /codex/00-getting-started/E2E_WORKFLOW_UNIFIED.md,
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/05-infrastructure/agent-orchestrator-api-host.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
  ]
owner:
last_reviewed: 2026-07-18
code_refs:
author:
---

# agent-orchestrator — service-implementation reference

**Repo**: `IggyIkenna/agent-orchestrator`.

**What it is**: operator tooling for the Claude Code worker fleet — a FastAPI + Vite-dashboard HTTP server. Workers call
`/boot`, `/progress`, `/done`, `/blocked`, `/heartbeat` instead of the retired file-based orchestration (LEDGER.md +
ping files + manual dispatch). State persists in SQLite (`data/state/state.db`); config (backlog, accounts, backends) is
YAML/JSON under `data/config/`.

**Architecture & operating model live in the SSOT**:
[`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`](/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md)
— topology (one central VM, N in-process slots), the two worker classes (plan-driven backlog workers vs standing/
event-driven agents), and the four behaviour domains (worker lifecycle, task lifecycle, dispatch, regen). **This doc is
the implementation layer under it**: stack, auth, connectivity, secrets, state, dashboard, deploy, keeper.

**NOT a trading service** — see § "Difference vs trading services".

Cross-links: operator runbook → `/codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md`; deploy/infra →
[`/codex/05-infrastructure/agent-orchestrator-deploy.md`](/codex/05-infrastructure/agent-orchestrator-deploy.md);
central API host (instance, ports, watchdog, auto-reboot) →
[`/codex/05-infrastructure/agent-orchestrator-api-host.md`](/codex/05-infrastructure/agent-orchestrator-api-host.md).

---

## Tech stack

| Layer    | Technology                                                                                                                                                                                |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend  | FastAPI (Python 3.13), uvicorn, SQLAlchemy + SQLite (`data/state/state.db`)                                                                                                               |
| Frontend | React + TypeScript + Vite (dashboard served by Firebase Hosting)                                                                                                                          |
| Auth     | ES256 JWT for internal proxy tokens; HS256 for the operator dashboard login JWT (`ORCHESTRATOR_JWT_SECRET`, central-only). See § "Auth model".                                            |
| Host     | ONE central orchestrator VM (id `planning`, EC2 `13.113.200.22`, ap-northeast-1) running the backend + N slot workers as in-process tmux sessions. Topology SSOT: single-VM architecture. |
| State    | SQLite (runtime) + `data/state/state.json` snapshot, mirrored to S3/GCS by `SnapshotLoop`. See § "State persistence".                                                                     |
| Deps     | `uv` + `uv.lock` (Python); `npm` + `package.json` (dashboard)                                                                                                                             |
| QG       | `bash scripts/check.sh` — ruff + basedpyright + prettier + tsc (operator-tooling exemption from the standard `quality-gates.sh`)                                                          |

## Deployment shape

Firebase Hosting SPA + one central API VM:

```
        Firebase Hosting  →  agent-orchestrator.odum-research.com          (dashboard SPA)
                                        │ HTTPS
        api.agent-orchestrator.odum-research.com  (nginx :443 → backend :8765, EC2 13.113.200.22)
                                        │  in-process
                              N slot workers (tmux orch-slot-N)
```

The browser reaches only the central API's public TLS endpoint; slots are in-process tmux sessions on the same VM, not
separate hosts. The `/api/vms/<id>/*` proxy + `/api/fleet/summary` fan-out endpoints remain in the code as a single-node
degenerate case — they were the multi-VM router; there is no fleet to fan out to today. The historical Cloud Run shape
is documented in
[`/codex/05-infrastructure/agent-orchestrator-deploy.md`](/codex/05-infrastructure/agent-orchestrator-deploy.md) as
cloud-agnostic fallback reference — not running.

## Service bootstrap exemptions

Two QG steps are exempted (operator tooling, not a trading service):

- **STEP 5.61 (ServiceBootstrap)** — no `--asset-group`/`--mode` trading CLI; uvicorn-only startup.
- **STEP 5.34 (typed config_reloaders)** — `server/config.py` is module-level env-driven functions.

`/health` + `/readiness` (STEP 5.62) ARE registered via UTL `make_health_router` with a `data_freshness` callback
(state.json mtime + DB/backlog checks).

## Auth model

Two independent secrets/keys, deliberately separated so an upstream compromise cannot impersonate the operator:

- **`ORCHESTRATOR_JWT_SECRET`** (HS256) — operator dashboard login JWT only, validated at the public edge. Central-only,
  never wired into a worker.
- **ES256 asymmetric key pair** (`ORCHESTRATOR_INTERNAL_ALG=ES256`) — internal proxy auth. HS256 was retired 2026-06-01;
  `decode_token()` and `_issue_internal_token()` are ES256-only. Private key via the restricted creds bucket
  (`ORCHESTRATOR_INTERNAL_PRIVATE_KEY_GCS`), public key via `ORCHESTRATOR_INTERNAL_PUBLIC_KEY_GCS`. The raw
  `ORCHESTRATOR_INTERNAL_SECRET` is RETAINED as the pre-shared key for `verify_internal_secret()` → `POST /api/escalate`
  (the GHA→orchestrator CI-wall dispatch) — do not delete it.

**Current posture**: `auth.ALLOW_ANONYMOUS=True` (permissive, operator decision at launch; the `:8765` port has no
public inbound rule, so reads come from localhost or the dashboard proxy). Strict-auth flip recipe (provision the
operator JWT secret + argon2 user list, flip `ALLOW_ANONYMOUS=False`, 3-curl smoke test) and the full endpoint
inventory: `agent-orchestrator/docs/AUTH_INVENTORY.md`.

### Auth flip rationale

The flip is deferred by operator decision (permissive trades auth for iteration speed while the API is not publicly
reachable). When ready: provision `ORCHESTRATOR_JWT_SECRET` on the central VM only, keep the ES256 pair for internal
tokens, replace `validate_credentials` with the argon2 user list, flip `ALLOW_ANONYMOUS=False`, and smoke-test (valid
creds → 200, wrong password → 401, anonymous → 401).

## Connectivity model — centralized API router

The dashboard talks to ONE backend (the central API), which owns per-slot control server-side. Slots need no public IP,
no per-VM TLS, no DNS. Auth flow: the operator hits central with their HS256 JWT; central validates it at the perimeter,
terminates it, then mints a short-lived (5 min, role=worker) ES256-signed internal token for any upstream call
(`server/server.py::proxy_to_vm` + `auth.get_internal_service_token()`). Registry: `data/config/backends.json` (static
`url` + `private_url`) merged with the dynamic `fleet_registry.json`. This model was designed for a multi-node fleet;
with the single-VM topology it degenerates to local calls, but the auth separation is kept as the security boundary.

## Secrets + buckets

AWS is primary; GCP paths kept in sync for cloud-agnostic re-spin. All are no-ops when the corresponding env var is
unset (local dev keeps state on local disk).

| Surface                          | AWS path                                                  | GCP path                                      | Used for                                                           |
| -------------------------------- | --------------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------ |
| Per-VM env (JWT, Telegram, …)    | Secrets Manager `ORCHESTRATOR_ENV_LOCAL`                  | Secret Manager `ORCHESTRATOR_ENV_LOCAL`       | `bootstrap_vm.sh` writes `.env.local` on first boot                |
| Per-account setup-token env      | `s3://uts-orchestrator-creds-<account>/accounts/<id>.env` | `gs://…-orchestrator-creds/accounts/<id>.env` | `CredsEnvPoller` syncs to `~/.claude-accounts/` every 5 min        |
| State snapshot (state.json + DB) | `s3://<ORCHESTRATOR_S3_BUCKET>/`                          | `gs://<ORCHESTRATOR_GCS_BUCKET>/`             | `SnapshotLoop` in `server/gcs_sync.py` (default 30-min + shutdown) |

Cloud I/O goes through UTL `get_storage_client(provider=…)` — never a raw `boto3`/`google.cloud.storage` import; extend
UTL if a new capability is needed.

## State persistence

Runtime state is SQLite at `data/state/state.db`. `SnapshotLoop` (`server/gcs_sync.py`) writes a `state.json` mirror +
SQLite hot-copy on a cadence (`ORCHESTRATOR_SNAPSHOT_INTERVAL_SECONDS`, default 30 min + shutdown), uploaded to S3/GCS
when the bucket env is set. On the AWS host, `ORCHESTRATOR_S3_BUCKET=uts-orchestrator-state-427895769566` is the
disaster-recovery target (a VM restart otherwise loses `state.db`). Snapshot _recency_ is not currently asserted — a
broken loop looks like a working one until state is lost (tracked in the AO close-out plan).

### Schema changes to an EXISTING table — the migration-dict + completeness-test convention (HARD RULE)

`create_all_tables()` (`server/bootstrap.py`) is `Base.metadata.create_all(engine)` — idempotent per-table by NAME, not
per-column: it only creates a table that's missing entirely, it never `ALTER TABLE`s a table that already exists. Every
long-lived deployed VM has every current table already created, so a NEW field added to an EXISTING ORM class (`SlotRow`
/ `AgentRow` / `TaskUsageRow` / `AccountUsageRow`) is invisible on that VM until something explicit runs an
`ALTER TABLE ADD COLUMN` — this has caused two real production incidents from the identical mistake ("added the ORM
field, forgot the matching entry"): `context_directive_issued`/`context_directive_grace_reports` (2026-07-25) and
`task_usage.backfilled` (2026-08-05, `/plans/archive/2026_08/task_usage_schema_drift_done_outage_2026_08_05.md` — a ~2h
fleet-wide `/done` outage).

**The convention**: `_add_missing_columns()` + one named per-table dict constant (`_SLOTS_MIGRATION_COLUMNS` /
`_AGENTS_MIGRATION_COLUMNS` / `_TASK_USAGE_MIGRATION_COLUMNS`, all in `server/bootstrap.py`, called from
`create_all_tables()`) does the column-existence-check + `ALTER TABLE` for any table that predates a given column — safe
to run on every startup. **Every additive field on an existing ORM class needs an entry in the matching dict in the SAME
commit** — this is a hand-maintained mirror of the ORM model, not an automatic diff, so it depends on the author
remembering the second edit. A true automatic `PRAGMA table_info` vs. ORM-model differ was considered (2026-08-05,
`/plans/archive/2026_08/ao_fleet_cache_tokens_and_task_count_2026_08_05.md`) and deliberately deferred as more
novel/riskier code on the live startup path for no incremental safety benefit once the completeness test below exists.

**The safety net**: `tests/test_migration_completeness.py` statically compares each covered ORM class's declared columns
against its `_BASELINE_*_COLUMNS` (the table's ORIGINAL shape, pre-migration-tooling — free via `create_all_tables()` on
any environment new enough to lack the table) union its migration dict — a column in neither set fails the test by name,
before it ships. Adding a NEW table gets its whole initial column set for free (baseline case); adding a column to an
EXISTING table needs an `_add_missing_columns(...)` dict entry, or this test catches it.

## Auth — long-lived setup-tokens

Every account in `data/config/accounts.json` authenticates via an `oauth_token_env_file` (`~/.claude-accounts/<id>.env`
with `CLAUDE_CODE_OAUTH_TOKEN=…` + `unset ANTHROPIC_API_KEY`). Every spawn path sources the env file before
`exec claude` and refuses HTTP 400 when it is missing. Only `creds_env_poller` (5-min cross-cloud bucket sync) remains
of the legacy auth machinery. Model SSOT:
[`/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`](/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md);
rate-limit/auth failover:
[`/codex/12-agent-workflow/orchestrator-safety-mechanisms.md`](/codex/12-agent-workflow/orchestrator-safety-mechanisms.md)
§ B + [`agent-orchestrator-worker-liveness.md`](agent-orchestrator-worker-liveness.md) § "Account auth-failure
eviction".

## AgentKeeper + agent-type oversight

`server/main_agent_keeper.py` (`AgentKeeper`) is the single daemon that guarantees the mandatory Class-B agents every
tick: the singleton **main** (`orch-agent-main`) and the **review** agent(s) (`ORCHESTRATOR_REVIEW_SLOTS`) —
`autospawn.ensure_review_agents()` brings review up even when AutoSpawn is off. AutoSpawn handles only Class-A task
workers + escalation drains.

- **Two-axis agent classification** (`AgentRow`, set at spawn) — the implementation of the two worker classes (single-VM
  SSOT § "The two worker classes"): `agent_kind`
  (main/review/cicd/conflict_resolver/data_pipeline_failure/plan_health/plan_reconciler/monitor/worker) carries
  identity; `lifecycle` (persistent | one_shot | scheduled) tells the reaper/watchdog that a one_shot/scheduled session
  ending is EXPECTED, not a stale-agent incident; `role` stays the chat/promote lane (main/review/custom).
- **Fleet vs AGENT TYPES — two dashboard surfaces**: the **Fleet** shows `SlotRow`s (worker slots); the **AGENT TYPES**
  panel shows `AgentRow`s grouped by kind. A plain task worker has a `SlotRow` and no `AgentRow`; a typed Class-B agent
  registers an `AgentRow` and may BORROW a free slot while it runs (no dedicated cicd/plan_health slot). Each keeper
  tick reconciles rows against tmux reality: ghost-reap of a typed agent whose slot a worker reused, account backfill,
  and slot-takeover (re-queues a displaced worker's task).
- **Fleet-worker cap**: `ORCHESTRATOR_FLEET_WORKER_CAP` (default 10) bounds concurrent on-demand workers; main+review
  are not counted against it.
- **Role-dispatch**: a dispatched task's `assigned_role` → `prompts.render_worker` prepends `agents/<role>.md` to
  `worker.md` and reads the role file's model/thinking as the task tier (explicit plan `model_tier` wins; fail-soft to
  the generic worker when the role is unset/missing).
- **Show log** reads Claude's durable transcript JSONL (`server/transcript_log.py`) by the stored `claude_session_id` —
  the full respawn-proof conversation, not the ~24-line tmux frame. Repo-local detail: `docs/SLOTS_AGENTS_AND_FLEET.md`.
- **Recovery-audit note**: the `recovery_audit` agent-kind was removed from the AO roster, but the Layer-1
  recovery-audit-signoff FUNCTION is not retired — its consuming half is live but producer-less/mock-fed, producer
  rewire DEFERRED (operator 2026-07-16). See `recovery-defence-in-depth-layers.md` § Layer 1 +
  `plans/archive/issues/ao_recovery_audit_layer1_deleted_2026_07_15.md`.

## Blocked-questions, authority, and prerequisites

Three concepts kept apart in the model (agents conflating them is a recurring bug):

- **Blocked-question** (`BlockedRow` / `blocked_queue`): an agent needs a human/main answer to proceed. Carries an
  `authority` field (`main_agent` | `operator`). The main agent auto-answers only `authority=main_agent`; an
  `authority=operator` row is a hard-stop that must reach a human (rich Slack payload on creation).
  - **Answer retrieval, durable path (2026-08-19)**: `GET /api/slots/{slot_id}/messages` delivers the answer as a
    task-scoped `SlotMessageRow` notification — if the slot's `current_task` gets reassigned (force-reassign/
    skip-current-task) between posting `/blocked` and the answer landing, `take_pending_messages` orphans that
    notification permanently (`blocked_message_orphaned_by_reassign` in `state_store/activity.py`; reproduced live
    4x, `plans/archive/issues/plan_reconciler_blocked_answer_and_result_post_gaps_2026_08_16.md`). The underlying
    `BlockedRow.answer`/`answered_by`/`answered_at` is never deleted once answered, so
    `GET /api/blocked/{blocked_id}` (`server/routes/backlog.py::get_blocked_endpoint`, `agent-orchestrator@4a0753791a`)
    is a durable point-lookup by the row's own primary key — poll it by the `blocked_id` captured from the original
    `/blocked` POST response whenever `/messages` comes back empty/absent for a question you know was answered.
- **Prerequisite** (`PrerequisiteRow` / task `prereqs`): a task gated by EARLIER tasks WAITS — it does not escalate.
- The `condition`→`prerequisite` rename (agent-orchestrator@9758270) is end-to-end across ORM/API/dashboard; English
  prose ("race condition") is preserved.

Task-state + dispatch consequences: single-VM SSOT § "Task lifecycle".

## Dashboard URLs

| Environment    | URL                                                            |
| -------------- | -------------------------------------------------------------- |
| Production SPA | https://agent-orchestrator.odum-research.com                   |
| Central API    | https://api.agent-orchestrator.odum-research.com               |
| Local dev      | http://localhost:5173 (Vite) + http://localhost:8765 (backend) |

## Fleet git-health page

`GET /api/fleet/git-health?scope=fleet|local` aggregates each slot's stored `SlotGitStatus` into a hosts→slots→repos
surface (`reporter_stale` / `ff_cron_stale` / `drift_violation` / dirty / behind badges). Dashboard route `/fleet-git`
(`dashboard/src/FleetGit.tsx`). **deployment-ui's `/fleet` tab was DELETED 2026-07-27** (Fleet-tab consolidation,
`/plans/archive/issues/deployment_ui_fleet_tab_removal_2026_07_27.md`) — this orchestrator page (`/fleet-git`) is now
the ONLY operator view for fleet git-health. Division-of-surfaces SSOT:
`/codex/03-observability/monitoring-control-plane.md`.

## Host-offline failover (dormant on single-VM)

`FailoverLoop` (`server/failover.py`) re-homes soft-pinned queued tasks off a host that has gone silent >10 min. It was
built for the multi-host era (e.g. an operator laptop going offline); with one central VM there is no second host to
fail over to, so it is effectively dormant. `failover_allowed: false` on a task opts it out permanently. The loop still
initialises at boot (`server/server.py`) and its runtime status is on `GET /api/ops/failover`, but it takes no action
while the fleet is single-host.

## Local dev — port 8765

```bash
cd agent-orchestrator
uv venv && uv sync
.venv/bin/pre-commit install --install-hooks
cd dashboard && npm install && cd ..
scripts/dev.sh          # live mode (backend :8765 + Vite :5173)
scripts/dev.sh --mock   # demo mode
```

Quality gates: `bash scripts/check.sh` (ruff + basedpyright + prettier + tsc). No standard `quality-gates.sh`
integration — operator-tooling exemption.

## Slack notifications

Block Kit push to `#agent-orchestrator-alerts` via incoming webhook (`AGENT_ORCHESTRATOR_SLACK_WEBHOOK` from
`.env.local`; `_post()` no-ops when empty). The channel is **actionable-only** — automatic lifecycle events log + feed
the daily digest, they never page; a standing condition pages once on the false→true transition with a RESOLVED bookend
(persisted dedup, `server/dedup_state.py`). SSOT:
[`/codex/05-infrastructure/agent-orchestrator-slack-notifications.md`](/codex/05-infrastructure/agent-orchestrator-slack-notifications.md)

- alerting policy [`agent-orchestrator-alerting.md`](agent-orchestrator-alerting.md).

## Deployment scripts

| Target                   | Script                                                              |
| ------------------------ | ------------------------------------------------------------------- |
| Central VM bootstrap     | `agent-orchestrator/scripts/bootstrap_vm.sh` (CLOUD_PROVIDER aware) |
| Central VM systemd unit  | `agent-orchestrator/scripts/install-orchestrator-service.sh`        |
| Continuous deploy (code) | `agent-orchestrator/scripts/ao-self-pull.sh` (root cron — read the crontab for the interval) |

**Deploy currency**: `ao-self-pull.sh` FF-pulls `origin/live-defi-rollout` (ff-only) and `systemctl restart`s the
orchestrator only when HEAD moved **and the move touched a restart-relevant path** (`RESTART_RELEVANT_PATHS` =
`server/ config/ pyproject.toml uv.lock`), or when the running process predates the newest restart-relevant commit.
The relevance gate is a HARD RULE, not a tuning preference — restarting on any HEAD move made the fleet restart itself
on its own commits and each restart mass-disrupts live workers; see
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Deploy currency" and
`/plans/active/issues/fleet_dispatch_stall_root_cause_2026_08_21.md`. Three deduped Slack alert
conditions, each with its own dedup statefile so none suppresses the others: (1) `_alert_wedge` fires when the pull is
wedged (dirty/diverged) AND the clone is `≥AO_DRIFT_ALERT_COMMITS` (10) commits behind — a COMMIT-DISTANCE gate; (2)
`_track_stale_process`/`_STALE_TICKS_STATE` fires after `AO_STALE_PROCESS_ALERT_TICKS` (3) consecutive ticks where the
checkout is current but the RUNNING PROCESS still predates HEAD (the self-heal restart isn't resolving it) — closes the
older "current-checkout-but-stale-process" gap this note used to flag as open; (3) `_track_dirty_tick`/
`_DIRTY_TICKS_STATE` (added 2026-07-30,
`/plans/archive/issues/ao_self_pull_stalled_by_untracked_backup_files_2026_07_29.md`) fires after `AO_DIRTY_ALERT_TICKS`
(4) consecutive dirty-skip ticks regardless of how many commits LDR moved meanwhile — closes
the blind spot where `_alert_wedge`'s commit-distance gate never trips during a quiet LDR window even though the tree
has been silently stuck dirty for hours (the incident that doc found: 2+ hours, 10 consecutive ticks, never alerted).
**`launch-epic-vm*.sh` REMOVED 2026-07-24** (operator ruling: per-epic VMs are deprecated and unused since the
2026-06-27 single-VM pivot — no re-spin optionality is worth the code debt; recreate from git history,
`deployment-service@7438ec5^`, if the per-epic model ever returns). Disaster recovery for the single central/planning VM
is the separate, already-covered `launch-central-brain-aws.sh` (from-scratch relaunch + EIP reassociation) — see its
header comment for the current recovery procedure.

### What a self-pull ACTUALLY deploys — the generator-inert boundary (HARD RULE)

The core of `ao-self-pull.sh` is `git merge --ff-only` plus a RELEVANCE-GATED `systemctl restart orchestrator`. It
runs a few self-heal steps around that (memory-cap rescale, worktree realign, `uv sync` on a lock move, and
`install-orchestrator-service.sh` unconditionally so a unit-file-only commit cannot sit unapplied), but **it re-runs
no OTHER installer** — this section's "generator-inert" boundary is about those. So a fix only reaches the live VM if
it lives in a file the running process reads directly:

| Change lands in…                                       | Live after a self-pull?                                                                                   |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `server/**.py`                                         | **YES — but ONLY via the restart.** The unit's `--reload` was removed 2026-07-30 (`ee98ccb`); the live process runs plain `uvicorn server.server:app`. `server/` is in `RESTART_RELEVANT_PATHS` precisely so this stays true |
| Other in-repo Python/data the process imports at start | **YES** — on the restart                                                                                  |
| `scripts/install-*.sh`, `scripts/bootstrap_vm.sh`      | **NO** — generator scripts; inert until re-run on that host                                               |
| `/etc/systemd/system/orchestrator.service`             | **NO** — the installed unit is a rendered COPY; needs `install-orchestrator-service.sh` + `daemon-reload` |
| `.env.local` on the VM                                 | **NO** — only `bootstrap_vm.sh` rewrites it                                                               |
| `~/.bashrc` / shell-env installers                     | **NO** — one-time manual per host                                                                         |

**Why this keeps biting**: a plan ticks "fixed + shipped + sha on LDR" and the fix is genuinely correct, but the live
VM's behaviour never changes — and nothing fails loudly. Two live examples (2026-07-20): the `ORCHESTRATOR_DB_PATH`
purge from `bootstrap_vm.sh`, and the `QG_GOVERNOR_MODE=reservation` block — both correct, both inert on an
already-bootstrapped host.

**The sharp edge**: if you migrate state (e.g. `/var/lib/orchestrator/*.db` → `data/state/`) and restart WITHOUT
re-running `install-orchestrator-service.sh`, the restart uses the still-installed old unit, whose `Environment=` still
points at the old — now empty — path. That reproduces the exact wrong-DB incident the migration exists to fix.

**So**: when a todo's gate is "the fix is live", the evidence must be a **measured read of the running system** (SSM
`git merge-base --is-ancestor <sha> HEAD` on the VM checkout, `systemctl show -p ExecMainStartTimestamp`, or a
`curl localhost:8765/api/...`) — never "the sha is on LDR".

## Branch model — LDR → main (direct)

`agent-orchestrator` ships via `quickmerge --agent --files` onto `live-defi-rollout` like every repo. Promotion is **LDR
→ `main` DIRECT** (the fleet-default `ldr_main` toggle; `staging` is bypassed unless a breaking bump routes a repo
through it). Slot clones are Path-B reference-clones on `live-defi-rollout`; `main`-behind-LDR is normal promotion lag,
not drift. The gate on the promotion PR is `quality-gates-v2`. CI/CD SSOT: `/codex/08-workflows/ci-cd-flow.md`.

## Difference vs trading services

| Axis                    | Trading service (MTDS, features-service)  | agent-orchestrator                          |
| ----------------------- | ----------------------------------------- | ------------------------------------------- |
| Purpose                 | Produce market data / signals / fills     | Coordinate Claude Code workers              |
| Asset group             | Required (`cefi`/`defi`/`tradfi`/…)       | None — operator tooling only                |
| Batch/live modes        | Identical code path, env toggles          | Not applicable                              |
| Kill-switch surface     | UTL kill-switch bus checked each tick     | None                                        |
| Event-bus emission      | `log_event()` to GCS + PubSub each action | None (activity stored in SQLite)            |
| ServiceBootstrap (5.61) | Required                                  | Exempt                                      |
| Schema provenance (UAC) | All domain types from UAC                 | `server/models.py` local (operator tooling) |

Consequence: do NOT add `--asset-group` flags, backtest modes, or STARTED/STOPPED events; do NOT add it to the
trading-pipeline DAG. It is purely an operator coordination surface.

## Plan reference

Architecture & operating model SSOT:
[`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`](/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md).
Behaviour-domain docs: [`agent-orchestrator-autospawn.md`](agent-orchestrator-autospawn.md) (spawn) ·
[`agent-orchestrator-worker-liveness.md`](agent-orchestrator-worker-liveness.md) (liveness + account failover) ·
[`agent-orchestrator-backlog-state-alignment.md`](agent-orchestrator-backlog-state-alignment.md) (dispatch + regen +
task state). In-flight remediation of the open items:
`plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md`. Epic: `plans/epics/orchestrator_master.md`.
