---
title: Orchestrator v0.7 — multi-VM topology with per-epic isolation + safety + auth-failover + landing dashboard
type: master-plan
status: active
created: 2026-05-21
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-05-21
operator: ikenna
co-operators: [harsh]
estimate_class: infra
estimate_baseline_ai_days: 60
estimate_calibrated_ai_days: 48
assigned_vm: human-planning-vm # this plan IS about VM topology; lives on the planning VM
related_plans:
  # Existing orchestrator plans this supersedes / extends
  - agent_orchestrator_cloud_run_deployment_2026_05_19.md
  - agent_orchestrator_dual_deployment_2026_05_19.md
  - agent_orchestrator_per_spawn_account_isolation_2026_05_20.md
  - agent_orchestrator_workers_on_vms_2026_05_19.md
  - agent_orchestrator_slack_notifications_2026_05_19.md
  - agent_reliability_mitigations_2026_05_20.md
  # Coordination it composes with
  - mtds_mdps_master.md
  - human_work_backlog_2026_05_20.md
  - issues/human_led_audit_pool_2026_05_21.md # NEW (to be created — operator-curated audit pool)
codex_ssots:
  - codex/12-agent-workflow/orchestrator-v07-multi-vm-topology.md # NEW (this plan's permanent SSOT)
---

# Orchestrator v0.7 — multi-VM topology with per-epic isolation

> **Operator vision 2026-05-21**: "topology should be as follows ikenna and harsh pick master plans which agent groups
> tackle over their time with 1 vm. we should be able to change these plans without restarting the vm... each vm and
> epic/master plan has 1 slot main orchestrator agent... 1 slot review agent... x worker agents max within rate limits +
> cpu bound... in the dashboard we want a landing page overview of all the master plans/epics that each vm owns. and
> then when we click through we see the same view we already have... separately we want a planning vm where ikenna and
> harsh can see each others chats... auto refresh works on each vm after one-time /login... 4 accounts per vm, primary
> round-robin across vms so 8 vms each 2 share an account... things should be backed up to gcs/s3 such that on vm
> restarts we get the info we need."

**Operator decisions captured in pre-plan Q&A 2026-05-21**:

- Backend topology: **per-VM backend, dashboard aggregates** (each VM independently resilient).
- VM count: **1 planning VM + 8 epic VMs** as default; flexible per epic count over time; current VM topology lives in
  `unified-trading-pm/orchestrator_vm_registry.yaml` (symlinked from planning VM so both Ikenna+Harsh see + edit it).
- Plan → VM assignment: **frontmatter on plan is source of truth + registry regen script**.
- Failover order: **lowest-weekly-pct-first** across the 3 non-primary accounts.

**Operator follow-up decisions 2026-05-21 r2**:

- **Planning VM**: cloud-hosted (NOT operator's mac); SSH from VSCode like every other VM. Named
  **`human-planning-vm`**. SSH config pattern:
  `Host human-planning-vm / HostName <ip> / User ubuntu / IdentityFile ~/.ssh/agent-orchestrator-key` (reuse the
  existing key — same access model as `agent-orchestrator-vm`).
- **VM naming**: keep current `agent-orchestrator-vm` (becomes vm-0 / the existing DeFi-focused fleet); add `vm-1`,
  `vm-2`, ... `vm-N` as epics are spun up. Dashboard landing page shows a dropdown listing every VM in the registry.
- **DNS**: single UI URL (`agent-orchestrator.odum-research.com`) is non-negotiable. API endpoints live under the
  sub-domain — wildcard `*.agent-orchestrator.odum-research.com` is acceptable if it saves work over per-VM A records
  (operator-pref: less work). Per-VM API URLs become `api-vm-N.agent-orchestrator.odum-research.com` (matching the
  numeric VM id).
- **KMS**: same key per VM (one shared `agent-orchestrator-state-encrypt` key in GCP, one in AWS). Less rotation
  overhead.
- **Cold-start**: <5 min target confirmed.
- **Per-VM RBAC**: out of scope for v0.7 (no current need — every operator sees every VM). Revisit if/when contractors
  or external collaborators get dashboard access.

## Why this plan exists

Today's orchestrator runs ONE VM, ONE main agent, ONE backlog. It has scaled to ~11 slots but hits recurring failure
modes:

1. **Auth token expiry cascade** (2026-05-21 incident): both account OAuth tokens expired ~8h after login, every new
   slot spawn 401'd, the main agent went stale. Single-account-active-at-a-time design caused fleet-wide outage.
2. **Agent staleness without recovery**: workers get stuck (no compaction, no pings, frozen pane) and sit dead until
   manual operator intervention.
3. **Cross-plan blast radius**: one bad change to backlog.yaml or shared state affects every slot; no isolation between
   epic workstreams.
4. **No cross-VM observability**: as scope expands beyond DeFi master plan (CeFi, TradFi, Sports, Prediction, infra,
   ML), we'd need 5+ epic-scoped fleets running in parallel, each with its own master plan, but currently the dashboard
   can only show one.
5. **Operator cognitive load**: every blocked question or stuck agent pings the operator. No isolation between planning
   work (Ikenna+Harsh thinking) and execution work (agents executing plans).

v0.7 fixes this by splitting into **per-epic VM fleets** (each isolated, with full agent topology + own backend) + **one
planning VM** for human work + a **dashboard landing page** that aggregates.

## Target topology

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Dashboard SPA (Firebase Hosting)                                                │
│  https://agent-orchestrator.odum-research.com                                    │
│                                                                                  │
│  [Landing] = cross-VM overview cards + cross-VM alerts panel                     │
│   ├── Click VM card →  /vm/<vm_id>  → current single-VM view (slots+backlog+...) │
└─────────────────────────────────────────────────────────────────────────────────┘
       │ /api/vms/list                                          │ /api/* per VM
       ▼                                                        ▼
┌──────────────────────────────┐                       ┌──────────────────────────────┐
│  human-planning-vm           │                       │  agent-orchestrator-vm (vm-0)│
│  api-human-planning.<domain> │                       │  api-vm-0.<domain>           │
│                              │                       │                              │
│  Slot 1: Ikenna iact         │                       │  Slot 1: main (Opus 1M)      │
│  Slot 2: Harsh iact          │                       │  Slot 2: review (Sonnet)     │
│  (no centralised slots)      │                       │  Slot 3-18: workers          │
│                              │                       │  4 accounts (1 primary,      │
│  4 accounts (shared visi)    │                       │   3 failover)                │
│                              │                       │  Owns: defi master plan      │
└──────────────────────────────┘                       └──────────────────────────────┘
                                                                ⋮
                                                       ┌──────────────────────────────┐
                                                       │  vm-N                        │
                                                       │  api-vm-N.<domain>           │
                                                       │  Same shape                  │
                                                       │  Owns: <epic> master plan    │
                                                       └──────────────────────────────┘
```

### Per-VM agent shape (epic VMs)

| Slot     | Role                  | Model                 | Purpose                                                                                                                                                                                                                                                                   |
| -------- | --------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**    | **main orchestrator** | Opus 4.7 (1M context) | Delivers plan work to workers; auto-resolves /blocked questions via the DO-IT-PROPERLY rubric (NOT time-constrained shortcuts); has explicit credentials to spawn VMs, run GitHub Actions, etc — same authority operator has, only blocker is plan-stated dependencies.   |
| **2**    | **review agent**      | Sonnet 4.6            | Reviews each worker commit against the master plan + ensures FF merge of slot branches into LDR. Knows which commits are from which agents (slot branch = `tab/<operator>/<N>`). Auto-pull cron every 5 min keeps worktrees in sync with LDR (except when locally dirty). |
| **3-18** | **workers**           | Sonnet 4.6 (default)  | Pick up backlog tasks for the VM's master plan. Min 8 spawned, up to 16 based on rate-limit + CPU bound (1 CPU per agent minimum).                                                                                                                                        |

### Planning VM shape

| Slot                     | Role               | Model    | Purpose                                                                                                       |
| ------------------------ | ------------------ | -------- | ------------------------------------------------------------------------------------------------------------- |
| **1**                    | Ikenna interactive | Opus 4.7 | Human session for plan curation, audit work, architectural decisions.                                         |
| **2**                    | Harsh interactive  | Opus 4.7 | Human session. Both Ikenna+Harsh can see each other's chats via shared /api/agents/by-role/main/history view. |
| (no centralised workers) |                    |          | Planning VM doesn't execute code; it produces master plans that get delegated to epic VMs.                    |

## Plan → VM assignment

### Frontmatter (source of truth)

Every master plan (`plans/epics/*.md` + `plans/active/*master*.md`) declares:

```yaml
---
title: ...
assigned_vm: vm-0 # vm-0 .. vm-7 = epic VMs (see registry for current label mapping); human-planning-vm = humans only
---
```

Ikenna+Harsh edit + commit to LDR to change assignment. No VM restart needed; backends re-poll the registry every 60s
(or operator hits `POST /api/plans/reload` for instant pickup).

### Registry (derived, symlinked)

`unified-trading-pm/orchestrator_vm_registry.yaml` (committed to LDR):

```yaml
version: 1
generated_at: 2026-05-21T12:00:00Z # bumped by regen script
vms:
  - id: human-planning-vm
    fqdn: api-human-planning.agent-orchestrator.odum-research.com
    role: planning
    ssh_host: human-planning-vm # matches ~/.ssh/config Host directive
    label: "Planning (Ikenna + Harsh interactive)"
    operators: [ikenna, harsh]
    accounts:
      {
        primary: ikennaigboaka@gmail.com,
        failover: [ikenna@odum-research.com, iggy2london@gmail.com, harshkantariyawork@gmail.com],
      }
    master_plans: [] # planning VM doesn't execute
  - id: vm-0 # the current agent-orchestrator-vm (kept; just numbered into the topology)
    fqdn: api-vm-0.agent-orchestrator.odum-research.com
    role: epic
    ssh_host: agent-orchestrator-vm
    label: "DeFi master plan fleet (existing)"
    accounts:
      {
        primary: ikenna@odum-research.com,
        failover: [iggy2london@gmail.com, harshkantariyawork@gmail.com, ikennaigboaka@gmail.com],
      }
    master_plans:
      - plans/active/mtds_mdps_master.md
      - plans/active/master_to_live_defi_2026_05_23.md
  - id: vm-1
    fqdn: api-vm-1.agent-orchestrator.odum-research.com
    role: epic
    ssh_host: vm-1
    label: "CeFi master plan fleet"
    accounts:
      {
        primary: iggy2london@gmail.com,
        failover: [harshkantariyawork@gmail.com, ikennaigboaka@gmail.com, ikenna@odum-research.com],
      }
    master_plans:
      - plans/epics/cefi_master.md
  # ...vm-2 .. vm-7 as epics get spun up
```

Naming convention: VMs are numeric (`vm-0` = current `agent-orchestrator-vm`, `vm-1` ... `vm-N` as epics land). The
`label:` field is what shows in the dashboard dropdown so humans see "DeFi master plan fleet" not "vm-0". `ssh_host:`
matches a Host directive in `~/.ssh/config` for direct VSCode SSH (operator-pref: reuse the existing
`agent-orchestrator-key` identity file — same access model as the current VM).

**Regen script**: `unified-trading-pm/scripts/orchestrator/regen_vm_registry.py` greps every master plan's
`assigned_vm:` frontmatter + writes the yaml. Runs in pre-commit hook + on-demand. Hard rule: no two epic VMs may own
the same master plan (registry validator enforces).

**Symlink for planning VM visibility**: `~/.orchestrator/vm-registry.yaml` on planning VM →
`/home/<op>/unified-trading-system-repos/unified-trading-pm/orchestrator_vm_registry.yaml`. Ikenna + Harsh both see +
edit the same source of truth.

## Per-VM backend (independent)

Each VM runs its own orchestrator backend (FastAPI + uvicorn + systemd, same shape as today). New:

- **FQDN per VM**: `api-<vm-id>.agent-orchestrator.odum-research.com` (e.g. `api-defi.*`, `api-cefi.*`,
  `api-planning.*`). DNS A record per VM.
- **Public URL env var**: `ORCHESTRATOR_PUBLIC_URL` = this VM's fqdn so telegram alerts + spawn-event links point at the
  right backend.
- **VM identity**: `ORCHESTRATOR_VM_ID` env var (e.g. `vm-defi`); included in every agent event so dashboard aggregation
  can group by VM.
- **Backlog source**: each VM points `ORCHESTRATOR_BACKLOG` at its own backlog.yaml; that file is auto-generated from
  the master plan's todo items (see "Backlog auto-generation" section below).
- **State.db per VM**: each VM has its own sqlite state + activity log (NO cross-VM shared store — operator-decided
  per-VM-backend choice).

### Backlog auto-generation per VM

Currently `backlog.yaml` is hand-edited. With master plans assigned to VMs, we need backlog to derive from the plan's
`- [ ]` items so that:

1. Operator+Harsh+main-agent edit the master plan (single source)
2. Backlog regenerates on next plan-reload poll
3. New `- [ ]` items appear as queued tasks; flipped `- [x]` items mark `done`

**Script**: `unified-trading-pm/scripts/orchestrator/regen_backlog_from_plan.py`:

- Reads the VM's assigned master plans
- Parses `- [ ] [TIER] PNN. <title>` lines per `plans/PLAN_FORMAT.md`
- Emits `backlog.yaml` with `target_slot`, `tier`, `priority` derived from the plan items
- Idempotent — preserves task statuses already done in the VM's state.db

Trade-off: hand-authored ad-hoc backlog entries (like the 36 HUMAN-_ + ADAPTER-_ we landed yesterday) need to be ALSO in
a plan to survive regen. Acceptable — plans are the durable artifact.

## Dashboard aggregation

### Landing page (NEW)

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
│  │ Owner: data_pipeline  │ │ Owner: cefi_master    │ │ Owner: tradfi    │  │
│  │ 12 slots (8 working)  │ │ 14 slots (10 working) │ │ 6 slots (4 work) │  │
│  │ Backlog: 44 queued    │ │ Backlog: 22 queued    │ │ Backlog: 8 queue │  │
│  │ Account: ikenna@odum  │ │ Account: iggy2london  │ │ Account: harshKw │  │
│  │ Last activity: 2m ago │ │ Last activity: 30s    │ │ Last activity 12m│  │
│  └───────────────────────┘ └───────────────────────┘ └──────────────────┘  │
│  ┌─ vm-ml ────────────┐ ┌─ vm-sports ──────────┐ ┌─ vm-prediction ────┐    │
│  │ ...                │ │ ...                  │ │ ...                │    │
│  └────────────────────┘ └──────────────────────┘ └────────────────────┘    │
│  ┌─ planning-vm (Ikenna+Harsh interactive) ─────────────────────────────┐   │
│  │ Slot 1: Ikenna (active, ctx 65%, last msg 4m ago)                     │   │
│  │ Slot 2: Harsh  (idle since 2h)                                        │   │
│  │ Today: 12 plan edits, 3 new audit issues filed                        │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

Clicking a VM card → `/vm/<vm_id>` = current single-VM view (slots panel + backlog panel + activity feed + accounts
panel).

### Aggregation API

New endpoint **on each backend**: `GET /api/vm/summary` returns:

```json
{
  "vm_id": "vm-defi",
  "fqdn": "api-defi.agent-orchestrator.odum-research.com",
  "role": "epic",
  "master_plans": ["mtds_mdps_master.md"],
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

## Safety mechanisms

### A) Stuck-agent detection + auto-respawn

Three signals classify a slot as STUCK (action: respawn after Telegram alert):

1. **No compaction within 15 min** (and context_used_pct > 70%). Workers compact every ~5-10 min at that load; 15 min
   silence with high context = wedged.
2. **No pings/heartbeats within 15 min** AND no current_task that's properly /blocked. Workers self-direct via
   /heartbeat every 60s; 15 min silence = process gone.
3. **No git_status updates within 15 min** AND last status was red. Indicates auto-pull cron stopped firing OR worker
   can't reach orchestrator.

**Exemptions** (do NOT respawn even if signals trigger):

- Slot is `paused` (operator-intentional).
- Slot is `blocked` and the /blocked event has `awaiting_response_from: orchestrator` set.
- Review agent slot when no commits to review for the configured idle window (e.g. >2h).
- Slot has an in-flight long tool call (>15 min OK if last activity log shows tool execution).

**Respawn recipe** (in this order; abort if any step fails):

1. Telegram alert: `🔄 Auto-respawn slot <N> — stuck for <signal>`
2. Try to commit + push any dirty WIP in the slot's worktree (see § "Fresh-spawn dirty-commit" below)
3. `tmux kill-session -t orch-slot-<N>`
4. `POST /api/slots/<N>/spawn` with the slot's current account (or failover if expired)
5. Verify new tmux session within 30s; if not, escalate to operator (Telegram + dashboard banner)

### B) Auth failover (non-blocking)

When the active credentials for a slot 401 OR Anthropic returns billing/rate-limit error:

1. Detect at spawn time (slot pane shows `401 Invalid authentication credentials`) OR mid-session (agent's tool call
   returns 401).
2. **Do NOT respawn the agent** — that loses context.
3. Switch the per-account creds file via `swap_claude_account.sh` to the next failover account (lowest-weekly-pct-first
   across the VM's 3 non-primary accounts).
4. The IN-MEMORY claude session still has the dead token — kicker sends `/clear` or `/login` nudge so claude re-reads
   creds from disk (new behavior — Anthropic's CLI doesn't auto-detect creds change but a /clear forces fresh session
   init).
5. If /clear works (verified by next heartbeat succeeding) → done.
6. If /clear doesn't work (e.g. CLI doesn't re-read) → respawn the slot as above.

**Failover selection algorithm** (`server/account_failover.py`):

```python
def pick_failover_account(vm_id, current_account, exclude=None):
    candidates = registry[vm_id].failover_accounts
    candidates = [a for a in candidates if a != current_account and a not in (exclude or [])]
    # Filter out exhausted (weekly_pct >= 95, sonnet_pct >= 95, 5h_pct >= 95) + rate_limited_until > now
    healthy = [a for a in candidates if account_healthy(a)]
    if not healthy:
        return None  # Telegram alert: all-VM-accounts-exhausted
    # Sort by remaining headroom (lowest_weekly_pct first)
    return min(healthy, key=lambda a: account_state[a].weekly_pct)
```

### C) Telegram alerts (NEW + existing)

| Event                            | When                                                      | Severity |
| -------------------------------- | --------------------------------------------------------- | -------- |
| `notify_agent_stuck_respawned`   | Auto-respawn fired per § A                                | warn     |
| `notify_agent_stuck_escalation`  | Respawn failed; operator needs to intervene               | crit     |
| `notify_account_failover`        | Active account swapped per § B                            | info     |
| `notify_all_accounts_exhausted`  | Failover ran out of healthy accounts                      | crit     |
| `notify_oauth_token_expiring`    | Token within 1h of expiry (existing)                      | warn     |
| `notify_oauth_refresh_succeeded` | Auto-refresh worked (existing)                            | info     |
| `notify_oauth_refresh_failed`    | Refresh failed; operator /login needed (existing)         | crit     |
| `notify_git_staleness_red`       | Slot git_status red >15 min AND no auto-pull within 5 min | warn     |
| `notify_vm_unreachable`          | Dashboard's /api/vm/summary 5xx'd for >5 min              | warn     |

All channels: same group chat (`-5288420200`) for now. Per-VM channels deferred.

### D) Git staleness ping + alert

Auto-pull cron on each VM runs every 5 min: FF-pull from origin/LDR per worktree, EXCEPT when locally dirty (preserves
WIP). Cron records last-run timestamp.

Dashboard's git status badge already shows red/yellow/green per slot. New: orchestrator polls the cron timestamp file
per slot every 60s. If git_status is RED AND last-pull was >15 min ago AND no manual fix has happened → fire
`notify_git_staleness_red` once per slot-30min.

### E) Fresh-spawn dirty-commit (NEW — overrides CLAUDE.md foreign-files rule for this case)

**Problem**: when a slot's worker dies mid-work and respawns, the worktree has uncommitted changes from the predecessor
agent. The new agent reads CLAUDE.md "Never touch files outside your clear context" and refuses to commit them. Result:
perpetually dirty worktrees that block further work + contain potentially valuable WIP.

**Fix**: at the START of every fresh spawn, the spawn endpoint:

1. Walks each repo worktree in `.tabs/<N>/<repo>/`
2. For any dirty repo:
   - Stages everything: `git add -A`
   - Commits with `chore(orphan-wip): inherited WIP from predecessor on slot <N> at <ts>` + the predecessor's last-known
     agent_id if available
   - Pushes to the slot's branch: `git push origin tab/<operator>/<N>`
3. Logs an activity event `slot_orphan_wip_committed` with the SHA + repo list
4. Tells the new claude session via boot prompt: "Predecessor WIP committed to your branch at SHA <X>. Review for
   relevance to your next task; if useful, reference; if not, ignore (it's preserved in git history)."

This makes the foreign-files rule consistent: it remains true for ACTIVE-WORK files in OTHER slots, but a respawned slot
owns its predecessor's WIP and ships it cleanly.

**Compose with**: existing `worktree_clean_check.py` pre-spawn gate. Today it REFUSES spawn on dirty state OR stashes
(with `dirty_state_resolution: stash`). New default mode: `commit_and_push` (the behavior above), with stash + refuse
remaining as overrides.

## Auth & accounts

### 4 accounts (rename to email-derived ids)

Current per-account snapshots:

- `~/.claude/.credentials.ikenna-backup.json` → rename to `~/.claude/.credentials.ikennaigboaka_at_gmail.com.json`
- `~/.claude/.credentials.harsh-primary.json` → rename to `~/.claude/.credentials.ikenna_at_odum-research.com.json`

New accounts to add (operator one-time `claude /login` per VM):

- `iggy2london_at_gmail.com` (operator can auth)
- `harshkantariyawork_at_gmail.com` (Harsh needs to auth)

Naming convention: replace `@` with `_at_` for filesystem safety. Display name in dashboard = the real email (with `@`).

**`accounts.json` per VM** (lives at `<VM>/agent-orchestrator/accounts.json`):

```json
[
  {
    "account_id": "ikennaigboaka@gmail.com",
    "label": "Ikenna (personal)",
    "tier": "max20",
    "weekly_msg_limit": 1200,
    "primary_email": "ikennaigboaka@gmail.com"
  },
  { "account_id": "ikenna@odum-research.com", ... },
  { "account_id": "iggy2london@gmail.com", ... },
  { "account_id": "harshkantariyawork@gmail.com", ... }
]
```

### Primary round-robin across VMs

| VM (id)           | Label (dashboard dropdown)            | Primary                      | Failover #1   | Failover #2   | Failover #3   |
| ----------------- | ------------------------------------- | ---------------------------- | ------------- | ------------- | ------------- |
| vm-0              | DeFi master plan fleet (existing)     | ikenna@odum-research.com     | iggy2london   | harshKw       | ikennaigboaka |
| vm-1              | CeFi master plan fleet                | iggy2london@gmail.com        | harshKw       | ikennaigboaka | ikenna@odum   |
| vm-2              | TradFi master plan fleet              | harshkantariyawork@gmail.com | ikennaigboaka | ikenna@odum   | iggy2london   |
| vm-3              | ML/features master plan fleet         | ikennaigboaka@gmail.com      | ikenna@odum   | iggy2london   | harshKw       |
| vm-4              | Sports master plan fleet              | ikenna@odum-research.com     | iggy2london   | harshKw       | ikennaigboaka |
| vm-5              | Prediction master plan fleet          | iggy2london@gmail.com        | harshKw       | ikennaigboaka | ikenna@odum   |
| vm-6              | Infra master plan fleet               | harshkantariyawork@gmail.com | ikennaigboaka | ikenna@odum   | iggy2london   |
| vm-7              | Agent-orchestrator master plan fleet  | ikennaigboaka@gmail.com      | ikenna@odum   | iggy2london   | harshKw       |
| human-planning-vm | Planning (Ikenna + Harsh interactive) | ikennaigboaka@gmail.com      | ikenna@odum   | iggy2london   | harshKw       |

Labels are operator-editable in the registry yaml (the human-readable dropdown name); ids are immutable once a VM is
provisioned.

Each account is primary on 2 VMs (failover-only on the other 7). Failover order in the table is the STATIC fallback;
runtime selection is `lowest-weekly-pct-first` per § B.

### Auto-refresh polling (per VM)

`usage_poller` extension (already wired for one VM in agent-orch@4eabf5c). Each VM polls all 4 accounts every 30 min:

1. For each account: `_monitor_and_refresh_oauth()` — refresh if within 1h of expiry
2. Then `claude /usage` probe (current behavior)

**One-time bootstrap per VM**: operator runs `claude /login` for primary account (and one-time `claude /login` for each
failover) on the VM, then `cp ~/.claude/.credentials.json ~/.claude/.credentials.<email>_at_<domain>.json`. After that
the auto-refresher keeps tokens alive indefinitely.

Harsh's `harshkantariyawork@gmail.com` requires Harsh action (browser auth). Once per VM where it's deployed. Telegram
alert when refresh fails so operator knows to act.

## Plan workflow

### Audit issue pool (NEW)

`plans/active/issues/human_led_audit_pool_2026_05_21.md` is operator-curated. Format:

```yaml
---
title: Human-led audit pool — Ikenna+Harsh continuous review queue
type: issue-pool
status: active
created: 2026-05-21
operators: [ikenna, harsh]
---

# Pending audits → master plan promotion

- [ ] **AUDIT-2026-05-21-001** — DeFi paper-trade execution path review (Ikenna)
  - Source: data_pipeline_master_coordination Phase 12 review request
  - Outcome target: promote to plans/epics/defi_paper_trade_execution_2026_05_22.md
  - Status: queued

- [ ] **AUDIT-2026-05-21-002** — CeFi venue restriction matrix completeness (Harsh)
  - ...
```

Ikenna+Harsh process these on the planning VM (slot 1 + slot 2 interactive). For each:

1. Read the audit prompt
2. Cross-reference existing plans (grep for conflicts) + codex SSOTs + code reality
3. Author OR update a master plan
4. Add the plan's `assigned_vm: vm-<epic>` frontmatter
5. Commit to LDR
6. Regen registry: `python3 scripts/orchestrator/regen_vm_registry.py`
7. Target VM's main agent picks up the new/updated plan on next 60s reload tick

### Master plan delegation flow

```
Audit issue → planning VM (Ikenna or Harsh) → master plan edit/create
            → frontmatter assigned_vm: vm-<epic>
            → commit LDR
            → registry regen
            → target VM's main agent polls registry every 60s
            → main agent re-reads master plan
            → regen_backlog_from_plan.py expands - [ ] items into backlog
            → /api/backlog/reload
            → workers pick up new tasks on next /boot
```

No VM restart. No operator manual intervention beyond the plan edit.

## Persistence + VM provisioning

### State backup (GCS + S3)

Each VM backs up state every 6h to its own per-VM bucket path:

- GCS: `gs://agent-orchestrator-state-<env>/<vm_id>/snapshots/<ts>.tar.gz`
- S3: `s3://agent-orchestrator-state-<env>-<aws-acct>/<vm_id>/snapshots/<ts>.tar.gz`

Contents:

- `state.db` (sqlite)
- `backlog.yaml` (current state)
- `accounts.json`
- `~/.claude/.credentials.*.json` (encrypted via Cloud KMS / AWS KMS before upload)
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
2. `.credentials.*.json` restored from KMS-decrypted snapshot → all accounts usable immediately
3. Worktrees may need re-pulling LDR (auto-pull cron handles on first tick)
4. tmux sessions are gone (process-dead) → main agent + review agent + workers respawn from boot prompts (state.db has
   their definitions)

## Migration plan (current → target)

### Phase 0 — prerequisites (DONE / IN PROGRESS)

- [x] OAuth auto-refresh + dashboard badge (agent-orch@4eabf5c)
- [x] Per-account creds swap (agent-orch@2de9410)
- [x] Telegram alert framework (`server/notifications/telegram.py`)
- [ ] Operator action: `claude /login` for ikenna-backup + harsh-primary on current VM to restore refresh tokens
      (one-time recovery from 2026-05-21 cascade)

### Phase 1 — registry + frontmatter (1 cal AI-day)

- [x] Add `assigned_vm:` frontmatter to every existing master plan in `plans/epics/*.md` + the coordinator + key
      actives. Default for unassigned plans: `vm-defi` (current single VM). (PM@e3f11893)
- [x] Author `unified-trading-pm/orchestrator_vm_registry.yaml` (initial: just `vm-0` = current setup + `human-planning-vm`
      placeholder). (PM@e3f11893)
- [x] Write `scripts/orchestrator/regen_vm_registry.py` + add to pre-commit hook. (PM@e3f11893)
- [x] CLAUDE.md addition: "Master plans MUST declare `assigned_vm:` in frontmatter." (PM@e3f11893)

### Phase 2 — multi-VM dashboard (3 cal AI-days)

- [ ] New SPA route `/` (landing) + `/vm/<vm_id>` (current single-VM view).
- [ ] New endpoint per backend: `GET /api/vm/summary`.
- [ ] Landing page component: cross-VM cards + cross-VM alerts panel.
- [ ] VM-list config in SPA (read from registry on initial load).
- [ ] Deploy to Firebase.

### Phase 3 — safety mechanisms (3 cal AI-days)

- [ ] Implement stuck-detection per § A in `worker_liveness.py`. New env var `ORCHESTRATOR_STUCK_THRESHOLD_MINUTES=15`.
- [ ] Implement auto-respawn flow with telegram alert.
- [ ] Implement fresh-spawn dirty-commit per § E (replace REFUSE default with `commit_and_push`).
- [ ] Implement git-staleness alert per § D.

### Phase 4 — auth failover (2 cal AI-days)

- [ ] Implement `account_failover.py` with `pick_failover_account()` per § B.
- [ ] Wire failover into existing 401-detection paths in `worker_liveness.py` + spawn endpoint.
- [ ] Add `notify_account_failover` + `notify_all_accounts_exhausted` telegram helpers.
- [ ] Rename existing accounts to email-derived ids (data migration script).

### Phase 5 — account roster expansion (1 cal AI-day + operator action)

- [ ] Add `iggy2london@gmail.com` + `harshkantariyawork@gmail.com` to `accounts.json` on current VM.
- [ ] Operator: `claude /login` for iggy2london (Ikenna can do).
- [ ] Harsh: `claude /login` for harshkantariyawork (Harsh's own action).
- [ ] Auto-refresher picks up new accounts on next tick.

### Phase 6 — backlog auto-gen from plans (2 cal AI-days)

- [ ] Write `scripts/orchestrator/regen_backlog_from_plan.py`.
- [ ] Wire to plan-reload poll (every 60s OR on `POST /api/plans/reload`).
- [ ] Migrate the current ad-hoc backlog entries (HUMAN-_ + ADAPTER-_) into their respective master plan source
      documents.
- [ ] Hard rule in CLAUDE.md: "Backlog tasks come from master plans, not direct backlog.yaml edits."

### Phase 7 — planning VM (2 cal AI-days)

- [ ] Provision planning VM (could be operator's mac via existing slot-1-pause pattern, OR a dedicated GCP/AWS VM).
- [ ] Run own orchestrator backend (no centralised slots; just slot 1 + slot 2 for Ikenna+Harsh).
- [ ] Symlink registry: `~/.orchestrator/vm-registry.yaml` → PM repo's `orchestrator_vm_registry.yaml`.
- [ ] Wire planning VM's backend into the landing page.

### Phase 8 — persistence (2 cal AI-days)

- [ ] Implement state-backup cron (every 6h) per § "State backup".
- [ ] Encrypt creds via Cloud KMS before upload.
- [ ] Write restore script + test on a throwaway VM.

### Phase 9 — VM provisioning (4 cal AI-days)

- [ ] Author packer/docker pipeline for the immutable image.
- [ ] CI workflow on agent-orchestrator LDR push → build + push to GCS.
- [ ] `bootstrap_vm.sh` reads cloud-init metadata + pulls latest image.
- [ ] Test cold-start: launch new VM, verify <5 min until backend serving.

### Phase 10 — review agent role (3 cal AI-days)

- [ ] Author `agents/review.md` boot prompt template.
- [ ] Review agent logic: poll for new commits on slot branches, validate against master plan, ensure FF-merge to LDR.
- [ ] Auto-merge happy-path; flag conflicts for operator.

### Phase 11 — rollout to 8 epic VMs (5 cal AI-days)

- [ ] Provision 8 epic VMs via Phase 9 pipeline.
- [ ] Configure DNS A records: `api-<id>.agent-orchestrator.odum-research.com`.
- [ ] Assign master plans to VMs per the table in § "Primary round-robin".
- [ ] Land 1 VM at a time; verify before moving to next.
- [ ] Cut over current single-VM work to vm-defi (its target home).

### Phase 12 — cleanup + docs (2 cal AI-days)

- [ ] Archive superseded plans (Phase 0 prereqs section).
- [ ] Author codex SSOT: `codex/12-agent-workflow/orchestrator-v07-multi-vm-topology.md`.
- [ ] Update CLAUDE.md § "System-First Architecture" with new topology pointer.
- [ ] CONTRIBUTING.md style docs for the planning workflow.

## Total estimate

~30 cal AI-days (after the 0.8 multiplier for infra-class). Wall-clock with parallelism (multiple slots): ~10-14
calendar days end-to-end.

## Out of scope (post-v0.7)

- Multi-region VMs (today: all asia-northeast1).
- Per-VM separate Telegram channels (today: single shared chat).
- Cross-VM dependency graph (e.g. vm-ml waits on vm-features). Today: humans coordinate via master plan prereqs.
- Auto-scaling worker count based on backlog depth (today: fixed at 8-16 per VM).
- Cloud Run / serverless orchestrator backend (today: VM-bound systemd). Defer until Phase 11+1 if VM ops become
  painful.

## Composes with

- `CLAUDE.md § "Local slot host = VM slot host"` — extends from one VM to N.
- `CLAUDE.md § "Commit + Push + Flip Plan Checkboxes As You Ship Each Item"` — review agent enforces.
- `CLAUDE.md § "Capture Discoveries As Plan Todos Immediately"` — backlog auto-gen from plans makes this the only path.
- `codex/12-agent-workflow/` — existing agent workflow docs.
- `plans/active/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md` — earlier per-spawn HOME-shim plan;
  superseded by Phase 4 of this plan (auth failover without respawn).
- `plans/active/agent_reliability_mitigations_2026_05_20.md` — Phase 2 dirty-state gate; superseded by Phase 3
  (commit_and_push default).

## All operator decisions captured

1. ✅ **Planning VM host**: cloud VM named `human-planning-vm`; SSH from VSCode reusing the existing
   `agent-orchestrator-key` identity. Same shape as the current `agent-orchestrator-vm`.
2. ✅ **DNS**: wildcard `*.agent-orchestrator.odum-research.com` (operator-pref: less work over per-VM A records).
   Single dashboard UI URL non-negotiable; APIs live under the sub-domain as
   `api-<vm-id>.agent-orchestrator.odum-research.com`. Phase 11 verifies the wildcard is provisioned (or files a
   one-time DNS change ticket).
3. ✅ **GCS/S3 KMS key**: same shared key per cloud (one in GCP, one in AWS). Less rotation overhead.
4. ✅ **Cold-start budget**: <5 min target confirmed.
5. ✅ **Per-VM operator RBAC**: out of scope for v0.7 (no current need — Ikenna + Harsh both see all VMs). Revisit if
   external collaborators ever get dashboard access.

6. ✅ **VM numbering for the existing fleet**: registry-mapping only. `id: vm-0 → ssh_host: agent-orchestrator-vm` in
   `orchestrator_vm_registry.yaml`. Do NOT rename the VM in systemd or `~/.ssh/config` — operator's existing SSH config
   keeps working unchanged. The `ssh_host:` field bridges the new numeric id convention to the existing Host directive.
   Phase 1 implements this.

**No open questions remaining.** Plan is ready for phase pickup.
