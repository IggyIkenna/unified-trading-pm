---
scope: [engineer, admin]
last_reviewed: 2026-05-21
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

## Target topology

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Dashboard SPA (Firebase Hosting)                                                │
│  https://agent-orchestrator.odum-research.com                                    │
│                                                                                  │
│  [Landing] = cross-VM overview cards + cross-VM alerts panel                     │
│   ├── Click VM card →  /vm/<vm_id>  → single-VM view (slots+backlog+activity)   │
└─────────────────────────────────────────────────────────────────────────────────┘
       │ /api/vms/list                                          │ /api/* per VM
       ▼                                                        ▼
┌──────────────────────────────┐                       ┌──────────────────────────────┐
│  planning-vm                 │                       │  vm-defi / vm-cefi / vm-N   │
│  api-planning.<domain>       │                       │  api-<id>.<domain>          │
│                              │                       │                              │
│  Slot 1: Ikenna interactive  │                       │  Slot 1: main (Opus 1M)     │
│  Slot 2: Harsh interactive   │                       │  Slot 2: review (Sonnet)    │
│  (no centralised workers)    │                       │  Slot 3-18: workers         │
│                              │                       │  4 accounts (1 primary +    │
│  4 accounts (shared visi)    │                       │   3 failover)               │
│                              │                       │  Owns: <epic> master plan   │
└──────────────────────────────┘                       └──────────────────────────────┘
```

## Per-VM agent shape (epic VMs)

| Slot     | Role                  | Model                 | Purpose                                                                                                                                                                                                                                                                   |
| -------- | --------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**    | **main orchestrator** | Opus 4.7 (1M context) | Delivers plan work to workers; auto-resolves /blocked questions via DO-IT-PROPERLY rubric (NOT time-constrained shortcuts); has explicit credentials to spawn VMs, run GitHub Actions, etc — same authority operator has, only blocker is plan-stated dependencies.       |
| **2**    | **review agent**      | Sonnet 4.6            | Reviews each worker commit against the master plan + ensures FF merge of slot branches into LDR. Knows which commits are from which agents (slot branch = `tab/<operator>/<N>`). Auto-pull cron every 5 min keeps worktrees in sync with LDR (except when locally dirty). |
| **3-18** | **workers**           | Sonnet 4.6 (default)  | Pick up backlog tasks for the VM's master plan. Min 8 spawned, up to 16 based on rate-limit + CPU bound (1 CPU per agent minimum).                                                                                                                                        |

## Planning VM shape

| Slot                     | Role               | Model    | Purpose                                                                                                       |
| ------------------------ | ------------------ | -------- | ------------------------------------------------------------------------------------------------------------- |
| **1**                    | Ikenna interactive | Opus 4.7 | Human session for plan curation, audit work, architectural decisions.                                         |
| **2**                    | Harsh interactive  | Opus 4.7 | Human session. Both Ikenna+Harsh can see each other's chats via shared /api/agents/by-role/main/history view. |
| (no centralised workers) |                    |          | Planning VM doesn't execute code; it produces master plans that get delegated to epic VMs.                    |

## Plan → VM assignment

### Frontmatter (source of truth)

Every epic in `plans/epics/<slug>.md` declares:

```yaml
---
name: <slug>
type: epic
assigned_vm: vm-<id> # planning-vm = humans only; vm-defi / vm-cefi / vm-ml / ... = epic VMs
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

Each VM runs its own orchestrator backend (FastAPI + uvicorn + systemd, same shape as today). New:

- **Local dev port**: `8026` (standard across all dev machines — `http://localhost:8026`). CLAUDE.md § "System-First
  Architecture" references this as the authoritative port for local interactive sessions.
- **FQDN per VM**: `api-<vm-id>.agent-orchestrator.odum-research.com` (e.g. `api-defi.*`, `api-cefi.*`,
  `api-planning.*`). DNS A record per VM, or wildcard `*.agent-orchestrator.odum-research.com`.
- **Public URL env var**: `ORCHESTRATOR_PUBLIC_URL` = this VM's fqdn so Telegram alerts + spawn-event links point at the
  right backend.
- **VM identity**: `ORCHESTRATOR_VM_ID` env var (e.g. `vm-defi`); included in every agent event so dashboard aggregation
  can group by VM.
- **Backlog source**: each VM points `ORCHESTRATOR_BACKLOG` at its own backlog.yaml; that file is auto-generated from
  the master plan's todo items (see "Backlog auto-generation" below).
- **State.db per VM**: each VM has its own sqlite state + activity log (NO cross-VM shared store — operator-decided
  per-VM-backend choice).

### Backlog auto-generation per VM

Currently `backlog.yaml` is hand-edited. With master plans assigned to VMs, backlog derives from the plan's `- [ ]`
items so that:

1. Operator + Harsh + main agent edit the master plan (single source)
2. Backlog regenerates on next plan-reload poll
3. New `- [ ]` items appear as queued tasks; flipped `- [x]` items mark `done`

**Script**: `unified-trading-pm/scripts/orchestrator/regen_backlog_from_plan.py`:

- Reads the VM's assigned master plans
- Parses `- [ ] [TIER] PNN. <title>` lines per `plans/PLAN_FORMAT.md`
- Emits `backlog.yaml` with `target_slot`, `tier`, `priority` derived from plan items
- Idempotent — preserves task statuses already done in the VM's state.db

Trade-off: hand-authored ad-hoc backlog entries need to be ALSO in a plan to survive regen. Acceptable — plans are the
durable artifact.

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
│  ┌─ planning-vm (Ikenna+Harsh interactive) ─────────────────────────────┐   │
│  │ Slot 1: Ikenna (active, ctx 65%, last msg 4m ago)                     │   │
│  │ Slot 2: Harsh  (idle since 2h)                                        │   │
│  │ Today: 12 plan edits, 3 new audit issues filed                        │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

Clicking a VM card → `/vm/<vm_id>` = single-VM view (slots panel + backlog panel + activity feed + accounts panel).

### Aggregation API

New endpoint **on each backend**: `GET /api/vm/summary` returns:

```json
{
  "vm_id": "vm-defi",
  "fqdn": "api-defi.agent-orchestrator.odum-research.com",
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
  "primary_account": "ikenna@odum-research.com",
  "primary_account_pct": 74,
  "last_activity_at": "2026-05-21T12:34:56Z",
  "alerts": [{ "severity": "warn", "kind": "oauth_expiring", "detail": "iggy2london@gmail.com expires in 45m" }]
}
```

Dashboard SPA fetches `/api/vm/summary` from EACH known VM's fqdn in parallel (URLs from the registry). ~200ms total
assuming 8 VMs respond in <100ms each. Falls back to "VM unreachable" card if any fail.

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
            → commit LDR
            → registry regen + populator regen
            → target VM's main agent polls every 60s
            → main agent re-reads epic + new active plan
            → regen_backlog_from_plan.py expands `- [ ]` items into VM backlog
            → /api/backlog/reload
            → workers pick up new tasks on next /boot
```

No VM restart. No operator manual intervention beyond the plan edit.

## VM registry (current state)

10 VMs serving 19 epics. Full mapping in [`../../orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml).

| VM                 | Owns epics                                                                                                                 | Primary account              |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `planning-vm`      | (none — interactive)                                                                                                       | ikennaigboaka@gmail.com      |
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
