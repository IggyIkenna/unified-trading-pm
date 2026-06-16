---
scope: [engineer, admin]
last_reviewed: 2026-05-28
---

# Orchestrator Multi-VM Topology (SSOT)

> **Permanent SSOT** for the agent-orchestrator multi-VM design — VM shapes, plan→VM assignment, registry, per-VM
> backend, dashboard aggregation, persistence + provisioning. Codified 2026-05-21 from the
> `orchestrator_v07_multi_vm_topology` plan that was promoted into `plans/epics/orchestrator_master.md`. The epic body
> now points here for design detail; implementation phases live in active plans under
> `parent_epic: orchestrator_master`.
>
> Composes with: [`claude-cli-multi-account-headless-auth.md`](claude-cli-multi-account-headless-auth.md) (auth model —
> long-lived setup-token), [`orchestrator-safety-mechanisms.md`](orchestrator-safety-mechanisms.md) (stuck-agent +
> failover + git staleness + dirty-commit), [`../../plans/epics/README.md`](../../plans/epics/README.md) (epic-flow SSOT
> — 19 epics × 5 tiers × 10-VM mapping), [`../../orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml)
> (registry SSOT).

## Operator vision (verbatim 2026-05-21)

> "Topology should be as follows: ikenna and harsh pick master plans which agent groups tackle over their time with 1
> VM. We should be able to change these plans without restarting the VM. Each VM and epic/master plan has 1 slot main
> orchestrator agent, 1 slot review agent, x worker agents max within rate limits + CPU bound. In the dashboard we want
> a landing page overview of all the master plans/epics that each VM owns, and then when we click through we see the
> same view we already have. Separately we want a planning VM where ikenna and harsh can see each others chats.
> Auto-refresh works on each VM after one-time /login. 4 accounts per VM, primary round-robin across VMs so 8 VMs each 2
> share an account. Things should be backed up to GCS/S3 such that on VM restarts we get the info we need."

## Target topology (refreshed 2026-05-28 to match centralized-router reality)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Dashboard SPA (Firebase Hosting)                                                │
│  https://agent-orchestrator.odum-research.com                                    │
│                                                                                  │
│  [Landing] = cross-VM overview cards + cross-VM alerts panel                     │
│   ├── Click VM card →  /vm/<vm_id>  → single-VM view (slots+backlog+activity)   │
└──────────────────────────────────────────┬──────────────────────────────────────┘
                                           │ HTTPS + operator JWT
                                           │ ALL calls go to ONE host:
                                           │ api.agent-orchestrator.odum-research.com
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Central / Orchestrator VM (id `planning`, EC2 13.113.200.22, AWS ap-northeast-1)│
│  (SPLIT 2026-06-12 — see orchestrator_human_central_vm_split_2026_06_12.md;      │
│   NO humans here — humans are on the human-planning VM, box below)               │
│  nginx :443 (Let's Encrypt) → orchestrator backend :8765                          │
│                                                                                  │
│  Acts as:                                                                        │
│   - Auth boundary: operator JWT validated here against ORCHESTRATOR_JWT_SECRET   │
│     (central-only key); never leaves this perimeter                              │
│   - Server-side fan-out: /api/fleet/summary calls each VM in parallel + merges  │
│   - Per-VM proxy: /api/vms/<id>/<path> → forwards to <id>'s private_url over     │
│     the VPC, mints a fresh internal service token signed with                    │
│     ORCHESTRATOR_INTERNAL_SECRET (fleet-shared key) for the upstream             │
│     Authorization header — workers validate against the same internal key       │
│   - Orchestrator roles: review · CI-escalation · plan-health · AutoSpawn         │
└──────────────────────────────────────────┬──────────────────────────────────────┘
                                           │ HTTP private VPC (vpc-6ee70e08)
                                           │ Bearer <internal-service-token>
                                           │  (the human-planning VM, id `human-planning`,
                                           │   EC2 35.76.120.160 m7i.2xlarge, slots 1-2 =
                                           │   Ikenna + Harsh interactive, self-registers
                                           │   with this central VM — owns no EIP/DNS/API)
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  10 epic VMs (AWS EC2 ap-northeast-1, same VPC + subnet as central)              │
│  vm-defi / vm-cefi / vm-tradfi / vm-sports / vm-prediction /                     │
│  vm-ml / vm-trading-core / vm-operator-ops / vm-cross-cutting / vm-orchestrator │
│                                                                                  │
│  Each VM:                                                                        │
│   - orchestrator backend on 0.0.0.0:8026 (no nginx, no per-VM TLS)              │
│   - private_url = 172.31.x.x:8026 (what the central calls)                       │
│   - Public IP (currently dynamic; EIPs ship under Phase 11 deferred)             │
│   - Slot 1: main (Opus 4.7 1M)                                                  │
│   - Slot 2: review (Sonnet 4.6)                                                 │
│   - Slot 3-?: workers (Sonnet 4.6); count tunable per VM env                    │
│   - Per-account env files synced from creds bucket via CredsEnvPoller            │
│   - Owns: <epic> master plan per orchestrator_vm_registry.yaml                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

The browser never reaches an epic VM directly — every `/api/...` call from the dashboard has its baseUrl rewritten to
`<central>/api/vms/<id>` (or stays at the central origin for fleet-wide endpoints), so per-VM control travels through
the central API's proxy. Code: `dashboard/src/App.tsx::backendBaseUrl` + `server/server.py::proxy_to_vm`.

### Auth: asymmetric ES256 model (codified 2026-06-01, shipped `orchestrator_asymmetric_auth`)

The auth boundary above runs on **two independent keys** — codifying the "operator JWT never reaches workers" invariant
the topology depends on:

- **`ORCHESTRATOR_JWT_SECRET`** — operator dashboard login JWT only (HS256). **Lives on the central VM only.** Validates
  the Bearer token on every authed request that enters at the public edge. Workers don't have it.
- **ES256 asymmetric key pair** — central↔worker proxy auth. `ORCHESTRATOR_INTERNAL_ALG=ES256`. Central holds the
  private key (GCP Secret Manager). Workers set
  `ORCHESTRATOR_INTERNAL_PUBLIC_KEY_GCS=gs://central-element-323112-orchestrator-creds/orchestrator/internal-public.pem`
  in `.env.local`; the public key is fetched at startup via the GCS Storage client (works because workers have
  `GOOGLE_APPLICATION_CREDENTIALS` from bootstrap).
- **Flow per request**: operator → central with Bearer<operator-JWT>. Central validates against
  `ORCHESTRATOR_JWT_SECRET`, terminates that token, mints a fresh 5-min ES256 JWT (claims:
  `role=worker, machine=central-proxy, sub=orchestrator`), forwards THAT in the upstream Authorization. Worker validates
  against the public key. The operator's token never leaves the central VM.
- **Dual-accept during 48h soak**: `decode_token()` tries ES256 first, then falls back to HS256
  (`ORCHESTRATOR_INTERNAL_SECRET` legacy value) so workers migrated out-of-order still validate. Remove HS256 path after
  soak period ends.

Failure mode if keys get out of sync: workers 401 on every authed proxy call (`/api/vms/<id>/api/state`,
`/api/backends`, etc.) and the dashboard bounces back to the login screen. Diagnosis: SSH to a worker + check the
journal for `"Loaded internal central↔worker public key from GCS."` startup line. Absence → `.env.local` missing the
GCS URI or `GOOGLE_APPLICATION_CREDENTIALS` not set.

## Per-VM agent shape (epic VMs)

| Slot     | Role                  | Model                 | Purpose                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| -------- | --------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**    | **main orchestrator** | Opus 4.7 (1M context) | Delivers plan work to workers; auto-resolves /blocked questions via DO-IT-PROPERLY rubric (NOT time-constrained shortcuts); has explicit credentials to spawn VMs, run GitHub Actions, etc — same authority operator has, only blocker is plan-stated dependencies.                                                                                                                                                                                                                                     |
| **2**    | **review agent**      | Sonnet 4.6            | Reviews each worker commit against the master plan + the task's `done_definition` (plan-vs-commit + QG-flow discipline; pings the worker back to fix). **Path-B (2026-06-08): does NOT FF-merge branches** — quickmerge pushes slots straight to LDR and the 5-min FF-pull cron keeps worktrees on latest LDR but SKIPS dirty ones, so the review agent also watches `/api/fleet/git-health` for long-dirty worktrees + diagnoses stuck-on-blocked vs stale/dead worker (`agents/review.md` § tick 3d). |
| **3-18** | **workers**           | Sonnet 4.6 (default)  | Pick up backlog tasks for the VM's master plan. Min 8 spawned, up to 16 based on rate-limit + CPU bound (1 CPU per agent minimum).                                                                                                                                                                                                                                                                                                                                                                      |

## Central / Orchestrator VM + Human Planning VM (SPLIT 2026-06-12 — two VMs, was one merged VM 2026-05-22 → 2026-06-12)

Human/central were split into **two distinct live VMs** by operator decision 2026-06-12
(`orchestrator_human_central_vm_split_2026_06_12.md`; supersedes the 2026-06-05 merged "Central API VM == Planning VM").

**Central / Orchestrator VM (id `planning`, `i-0c9b283b31d6b5ca7`, `13.113.200.22` EIP):** runs the **central API** that
the dashboard talks to (nginx :443 → app :8765) plus the orchestrator roles — **NO human daily work**. That central API:

- Validates the operator JWT (auth perimeter)
- Serves fleet-wide endpoints directly: `/api/fleet/summary`, `/api/auth/login`, `/api/backends`, `/api/accounts`, etc.
- Proxies per-VM endpoints (`/api/vms/<id>/<path>`) over the private VPC, minting a fresh internal service token for the
  upstream Authorization header so the operator JWT never reaches an epic VM
- Owns CI-escalation (`/api/escalate`), plan-health (`/api/plan-health/dispatch`), review, and **AutoSpawn for workers**

**Human Planning VM (id `human-planning`, `i-0dd9812a96cdda5dc`, `35.76.120.160`, m7i.2xlarge,
`ssh human-planning-vm`):** the two interactive slots, separate box, self-registers with the central VM (owns no
EIP/DNS/central-API; `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH=true` — never auto-adopts fleet plans).

| Slot                 | VM               | Role               | Model    | Purpose                                                                                                       |
| -------------------- | ---------------- | ------------------ | -------- | ------------------------------------------------------------------------------------------------------------- |
| **1**                | `human-planning` | Ikenna interactive | Opus 4.7 | Human session for plan curation, audit work, architectural decisions.                                         |
| **2**                | `human-planning` | Harsh interactive  | Opus 4.7 | Human session. Both Ikenna+Harsh can see each other's chats via shared /api/agents/by-role/main/history view. |
| (no spawned workers) | `human-planning` |                    |          | The human-planning VM doesn't execute backlog tasks; it produces master plans that get delegated to epic VMs. |

## Plan → VM assignment

### Frontmatter (source of truth)

Every epic in `plans/epics/<slug>.md` declares:

```yaml
---
name: <slug>
type: epic
assigned_vm: vm-<id> # planning = central/orchestrator (no humans); human-planning = Ikenna/Harsh interactive; vm-defi / vm-cefi / vm-ml / ... = epic VMs (SPLIT 2026-06-12)
---
```

Operators edit + commit to LDR to change assignment. No VM restart needed; backends re-poll the registry every 60s (or
operator hits `POST /api/plans/reload` for instant pickup).

### Registry (derived, symlinked)

[`unified-trading-pm/orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml) is the inverted index over
every epic's `assigned_vm:` frontmatter. **Regen script**:
`unified-trading-pm/scripts/orchestrator/regen_vm_registry.py` greps every epic's frontmatter + writes the yaml. Runs in
pre-commit hook + on-demand. Hard rule: no two epic VMs may own the same master plan (registry validator enforces).

**Symlink for planning VM visibility**: `~/.orchestrator/vm-registry.yaml` on planning VM →
`unified-trading-pm/orchestrator_vm_registry.yaml`. Ikenna + Harsh both see + edit the same source of truth.

### Naming convention

VMs use descriptive ids (`vm-defi`, `vm-cefi`, `vm-ml`, etc.) matching the epic they own. The `label:` field in the
registry yaml is what shows in the dashboard dropdown so humans see "DeFi master plan fleet" not "vm-defi". `ssh_host:`
matches a Host directive in `~/.ssh/config` for direct VSCode SSH (operator-pref: reuse the existing
`agent-orchestrator-key` identity file — same access model as the current VM).

## Per-VM backend (independent)

Each VM runs its own orchestrator backend (FastAPI + uvicorn + systemd, same shape across the fleet). The central VM
fronts them as documented in § "Target topology" above; epic VMs are not browser-reachable.

- **Listen port** — fleet VMs: `0.0.0.0:8026` (no nginx, no per-VM TLS); central VM: `127.0.0.1:8765` behind nginx :443
  with Let's Encrypt at `api.agent-orchestrator.odum-research.com`. Local dev = `:8026` on the operator's box.
- **VM identity** — `ORCHESTRATOR_VM_ID` env var (e.g. `vm-defi`); included in every agent event so dashboard
  aggregation can group by VM.
- **Public URL** — fleet VMs declare their public IP in `data/config/backends.json` `url`; private IP in `private_url`
  (used by the central proxy when `ORCHESTRATOR_USE_PRIVATE_URLS=true`). Per-VM FQDNs
  (`api-<vm-id>.agent-orchestrator .odum-research.com`) are deferred (Phase 11) — operator runs
  `allocate-orchestrator-eips.sh` + adds DNS A records when IP-stability + direct-curl ergonomics warrant the operator
  time (recipe:
  [`../05-infrastructure/agent-orchestrator-dns-cutover.md`](../05-infrastructure/agent-orchestrator-dns-cutover.md)).
- **Backlog source** — each VM auto-derives its own backlog.yaml from `plans/active/*.md` (see Phase 6 section below);
  not pointed at by env var.
- **State.db per VM** — each VM has its own sqlite state + activity log (NO cross-VM shared store).

### Backlog auto-generation per VM (Phase 6 — shipped 2026-05-28)

`backlog.yaml` is **derived from plans, not hand-edited**. Source of truth is `- [ ]` checkbox lines in
`plans/active/*.md`; regen turns them into BacklogTask rows. The HARD RULE is in CLAUDE.md ("Agent-orchestrator backlog
is plan-driven"): operators may field-tune derived tasks (priority / repos / target_slot / collision_group) but should
not hand-add new tasks — write the todo in the plan file.

**Module**: `agent-orchestrator/server/regen_backlog_from_plan.py` (not in the PM repo — it runs inside the orchestrator
process so SQLite + in-process state stay in sync after the YAML write).

- Walks `plans/active/*.md` (non-recursive; skips `INDEX.md`, `_*.md`, subdirectories like `issues/`).
- Parses unchecked `- [ ]` lines, ignoring YAML frontmatter, fenced code blocks, and `~~struck~~` lines.
- Extracts `P<0-3>` tag and maps to `BacklogTask.priority` (P0→10, P1→20, P2→50, P3→80, none→100).
- Title strips the redundant `[CATEGORY] P<N>.` prefix for clean dashboard display; brief keeps the raw line.
- **Content-based idempotency** (fixed 2026-05-28): dedup by `BacklogTask.brief == raw todo line`. Re-running the regen
  is a no-op for already-derived todos; editing a todo's wording creates a new task (old one keeps its dispatch state);
  flipping to `- [x]` simply removes the todo from regen's view, leaving the existing BacklogTask intact.

**Background poll**: `PlanRegenLoop` daemon thread in the same module. Fires once 60s after server startup, then every
`ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` (default **1800 = 30 min**, 0 disables; changed from 6h 2026-06-01 via
`plan_hygiene_silent_failure_capture` Phase 6). A complementary `pm-pull.timer` systemd unit FF-pulls
`unified-trading-pm` from LDR every 5 min, so the effective push-to-pickup latency is ≤35 min (was "≤6h"). After each
tick, a callback refreshes `_state["backlog"]` and re-syncs SQLite via `bootstrap.sync_backlog_to_db`.

**Manual trigger**: `POST /api/backlog/regen` (authed) for operator-initiated immediate refresh.

Trade-off: hand-authored ad-hoc backlog entries (added via the dashboard's "Add task" or direct YAML edits) co-exist
with derived ones but won't survive a clean re-derivation. Plans are the durable artifact; treat backlog.yaml as cache.

## Dashboard aggregation

### Landing page

URL `/` shows:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Agent Orchestrator — Fleet Overview                                         │
├──────────────────────────┬─────────────────────────────────────────────────┤
│  🚨 CROSS-VM ALERTS (3)  │  Tap to expand                                    │
│   • vm-defi: 2 OAuth expiring within 1h                                       │
│   • vm-cefi: main agent stale (30m no ping)                                   │
│   • vm-ml: 4 workers stale (auth-broken after acct swap)                      │
├──────────────────────────┴─────────────────────────────────────────────────┤
│  ┌─ vm-defi ─────────────┐ ┌─ vm-cefi ─────────────┐ ┌─ vm-tradfi ──────┐  │
│  │ Owner: defi_master    │ │ Owner: cefi_master    │ │ Owner: tradfi    │  │
│  │ 12 slots (8 working)  │ │ 14 slots (10 working) │ │ 6 slots (4 work) │  │
│  │ Backlog: 44 queued    │ │ Backlog: 22 queued    │ │ Backlog: 8 queue │  │
│  │ Account: ikenna@odum  │ │ Account: iggy2london  │ │ Account: harshKw │  │
│  │ Last activity: 2m ago │ │ Last activity: 30s    │ │ Last activity 12m│  │
│  └───────────────────────┘ └───────────────────────┘ └──────────────────┘  │
│  ┌─ planning (Ikenna+Harsh interactive) ─────────────────────────────┐   │
│  │ Slot 1: Ikenna (active, ctx 65%, last msg 4m ago)                     │   │
│  │ Slot 2: Harsh  (idle since 2h)                                        │   │
│  │ Today: 12 plan edits, 3 new audit issues filed                        │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

Clicking a VM card → `/vm/<vm_id>` = single-VM view (slots panel + backlog panel + activity feed + accounts panel).

### Aggregation API

Per-VM endpoint: `GET /api/vm/summary` returns a `VmSummary` (current shape in `server/models.py::VmSummary`):

```json
{
  "vm_id": "vm-defi",
  "fqdn": "172.31.2.75:8026",
  "role": "epic",
  "master_plans": ["defi_master.md", "manifest_master.md"],
  "slots_total": 12,
  "slots_working": 8,
  "slots_idle": 2,
  "slots_stale": 2,
  "slots_paused": 0,
  "backlog_total": 56,
  "backlog_queued": 44,
  "backlog_done": 11,
  "backlog_dispatched": 1,
  "primary_account": "sub-a-ikenna",
  "primary_account_pct": 74,
  "last_activity_at": "2026-05-28T07:59:20Z",
  "alerts": [{ "severity": "warn", "kind": "slots_stale", "detail": "2 slots stale" }]
}
```

Dashboard fan-out (centralized model — refreshed 2026-05-22): the dashboard calls `GET /api/fleet/summary` on the
**central API** which fans out **server-side** to each VM's `/api/vm/summary` in parallel via the proxy machinery
(`server/server.py::fleet_summary` → httpx). Browser sees one request, central makes 10 internal calls in parallel,
merges, returns. ~200ms total. Falls back per VM with a "VM unreachable" card when an individual backend doesn't
respond. The earlier model (browser fetches per-VM FQDNs) was superseded by the central-proxy model 2026-05-22.

## Persistence + VM provisioning

### State backup (GCS + S3)

Each VM backs up state every 6h to its own per-VM bucket path:

- GCS: `gs://agent-orchestrator-state-<env>/<vm_id>/snapshots/<ts>.tar.gz`
- S3: `s3://agent-orchestrator-state-<env>-<aws-acct>/<vm_id>/snapshots/<ts>.tar.gz`

Contents:

- `state.db` (sqlite)
- `backlog.yaml` (current state)
- `accounts.json`
- `~/.claude-accounts/<id>.env` (KMS-encrypted before upload — env file payload per the auth SSOT)
- `.tabs/<N>/<repo>/.git/refs/heads/tab/<op>/<N>` (slot branch refs only — full repos already in GitHub)

Retention: 7 days; one snapshot per day kept for 30 days.

**Restore script**: `scripts/orchestrator/restore_from_snapshot.sh <vm_id> <ts>` — used on VM recreation or DR
scenarios.

### VM provisioning (immutable image)

Goal: spinning a new VM into a slot in the topology takes <5 min and requires zero hand-install.

**Per-VM bootstrap script** (`scripts/orchestrator/bootstrap_vm.sh`):

1. Read VM id from cloud-init metadata
2. Pull pre-built tarball from `gs://agent-orchestrator-images/<latest>.tar.gz`:
   - claude CLI binary
   - orchestrator backend (.venv pre-built)
   - dashboard SPA dist (only if VM serves a backend)
   - all dependencies
3. Restore from latest snapshot for this VM id
4. systemd unit `orchestrator.service` boots
5. systemd unit `auto-pull.timer` enables FF-pull cron
6. systemd unit `usage-poller.timer` enables OAuth-refresh + /usage cron

Time budget: <5 min cold start. The tarball is built by a packer/docker pipeline triggered on each agent-orchestrator
LDR push.

### Account state continuity

When a VM restarts:

1. State.db restored from snapshot → slot statuses, accounts, agents preserved
2. `~/.claude-accounts/*.env` restored from KMS-decrypted snapshot → all accounts usable immediately
3. Worktrees may need re-pulling LDR (auto-pull cron handles on first tick)
4. tmux sessions are gone (process-dead) → main agent + review agent + workers respawn from boot prompts (state.db has
   their definitions)

## Plan workflow

### Audit-pool dispatch

`plans/active/issues/human_led_audit_pool_<date>.md` is operator-curated. Ikenna+Harsh process rows on the planning VM
(slot 1 + slot 2 interactive). For each row:

1. Read the audit prompt
2. Cross-reference existing plans (grep for conflicts) + codex SSOTs + code reality
3. Author OR update an active plan
4. Add the plan's `parent_epic: <slug>` frontmatter
5. Commit to LDR
6. Regen registry: `python3 scripts/orchestrator/regen_vm_registry.py`
7. Run epic body populator: `python3 scripts/plans/populate_epic_bodies_2026_05_21.py`
8. Target VM's main agent picks up the new/updated plan on next 60s reload tick

### Master plan delegation flow

```
Audit row → planning VM (Ikenna or Harsh) → active plan edit/create
            → frontmatter parent_epic: <slug>
            → commit + push to LDR
            → registry regen + populator regen
            → target VM's PlanRegenLoop tick (≤35 min: pm-pull 5-min + regen 30-min;
              or operator POST /api/backlog/regen for immediate)
            → regen_backlog_from_plan.regen() appends new `- [ ]` items as
              BacklogTask rows + content-dedupes already-derived ones
            → on_regen callback re-syncs SQLite + _state["backlog"]
            → workers pick up new tasks on their next /boot or /done
              (dispatch.pick_next_task filters by status='queued', prereqs,
              repo collision, affinity)
```

No VM restart. No operator manual intervention beyond the plan edit.

## VM registry (current state)

10 VMs serving 19 epics. Full mapping in [`../../orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml).

| VM                 | Owns epics                                                                                                                 | Primary account              |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `planning`         | (central / orchestrator — review · CI-escalation · plan-health · AutoSpawn; SPLIT 2026-06-12, NO humans)                   | ikennaigboaka@gmail.com      |
| `human-planning`   | (none — Ikenna/Harsh interactive; SPLIT 2026-06-12)                                                                        | ikennaigboaka@gmail.com      |
| `vm-defi`          | `defi_master` + `manifest_master`                                                                                          | ikenna@odum-research.com     |
| `vm-cefi`          | `cefi_master` + `instruments_master`                                                                                       | iggy2london@gmail.com        |
| `vm-tradfi`        | `tradfi_master`                                                                                                            | harshkantariyawork@gmail.com |
| `vm-sports`        | `sports_master`                                                                                                            | ikenna@odum-research.com     |
| `vm-prediction`    | `predictions_master`                                                                                                       | iggy2london@gmail.com        |
| `vm-ml`            | `mtds_mdps_master` + `features_and_ml_master`                                                                              | ikennaigboaka@gmail.com      |
| `vm-trading-core`  | `strategy_master` + `execution_master` + `trading_agent_master`                                                            | ikenna@odum-research.com     |
| `vm-operator-ops`  | `dart_and_promote_master` + `deployment_and_user_management_master`                                                        | harshkantariyawork@gmail.com |
| `vm-cross-cutting` | `infrastructure_master` + `observability_master` + `batch_live_symmetry_master` + `client_isolation_and_governance_master` | iggy2london@gmail.com        |
| `vm-orchestrator`  | `orchestrator_master`                                                                                                      | ikennaigboaka@gmail.com      |

Account round-robin: each of 4 accounts is primary on 2-3 VMs (failover-only on the others). Runtime failover selection
is `lowest-weekly-pct-first` across the VM's 3 non-primary accounts (see
[`orchestrator-safety-mechanisms.md § Auth failover`](orchestrator-safety-mechanisms.md)).

## Out of scope (post-v0.7)

- Multi-region VMs (today: all asia-northeast1)
- Per-VM separate Telegram channels (today: single shared chat)
- Cross-VM dependency graph (e.g. vm-ml waits on vm-features); today operators coordinate via epic prereqs
- Auto-scaling worker count based on backlog depth (today: fixed at 8-16 per VM)
- Cloud Run / serverless orchestrator backend (today: VM-bound systemd); defer until VM ops become painful
- Per-VM RBAC (today: every operator sees every VM); revisit if external collaborators get dashboard access

## Composes with

- [`claude-cli-multi-account-headless-auth.md`](claude-cli-multi-account-headless-auth.md) — long-lived setup-token auth
  pattern; the authoritative auth model
- [`orchestrator-safety-mechanisms.md`](orchestrator-safety-mechanisms.md) — stuck-agent + failover + git staleness +
  dirty-commit
- [`../11-project-management/epic-execution-with-sub-agents.md`](../11-project-management/epic-execution-with-sub-agents.md)
  — epic-flow SSOT pointer (resolves to [`../../plans/epics/README.md`](../../plans/epics/README.md))
- [`../../plans/epics/orchestrator_master.md`](../../plans/epics/orchestrator_master.md) — the L5 epic whose body points
  here; assigned active plans hold implementation phases
- [`../../orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml) — registry SSOT (the inverted index over
  every epic's `assigned_vm:`)
