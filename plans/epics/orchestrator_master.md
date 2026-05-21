---
name: orchestrator_master
title: "Orchestrator Master (L5)"
type: epic
tier: L5
status: active
priority: P0
assigned_vm: vm-orchestrator
parent: master_to_live_defi_2026_05_23
co_operators: [harsh]
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../active/agent_orchestrator_cloud_run_deployment_2026_05_19.md
  - ../active/agent_orchestrator_dual_deployment_2026_05_19.md
  - ../active/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md
  - ../active/agent_orchestrator_slack_notifications_2026_05_19.md
  - ../active/agent_orchestrator_workers_on_vms_2026_05_19.md
  - ../active/agent_reliability_mitigations_2026_05_20.md
  - ../active/d0_orchestrator_migration_2026_05_20.md
  - ../active/issues/human_led_audit_pool_2026_05_21.md
codex_ssots:
  - codex/11-project-management/epic-execution-with-sub-agents.md # pointer to plans/epics/README.md (epic-flow SSOT)
  - codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md # operator-shared 2026-05-21: long-lived setup-token pattern
external_references:
  - "Operator-shared 2026-05-21: Claude CLI Multi-Account Headless Authentication Guide (long-lived setup-token via
    CLAUDE_CODE_OAUTH_TOKEN env var, ~1y validity, multi-machine reuse, ANTHROPIC_API_KEY-precedence gotcha) — drives
    the r3 Auth & accounts revision and Phase 4 r3 rewrite"
---

# Orchestrator Master (L5)

**Owns**: agent-orchestrator multi-VM stack (planning-vm + 9 epic VMs); dashboard aggregation; auth failover (long-lived
setup-token pattern); per-spawn account isolation; cross-VM observability; Telegram alert framework; safety mechanisms
(stuck-agent respawn, auth failover without respawn, fresh-spawn dirty-commit, git staleness alerts).

**Assigned VM**: `vm-orchestrator` (self-managing — the agent-orchestrator stack runs the agent-orchestrator stack).

## Scope inherited from `orchestrator_v07_multi_vm_topology_2026_05_21` (promoted 2026-05-21)

This epic was promoted from the active plan `orchestrator_v07_multi_vm_topology_2026_05_21.md` per the epic
consolidation. Detailed design moved to codex SSOTs; implementation phases continue as the assigned active plans listed
below.

## Why this epic exists

Today's orchestrator runs ONE VM, ONE main agent, ONE backlog. It scaled to ~11 slots but hits recurring failure modes:
auth token expiry cascade (2026-05-21 incident), agent staleness without recovery, cross-plan blast radius, no cross-VM
observability, operator cognitive load. The v0.7 fix splits into **per-epic VM fleets** (each isolated, full agent
topology + own backend) + **one planning VM** for human work + a **dashboard landing page** that aggregates.

## Operator vision (verbatim 2026-05-21)

> "Topology should be as follows: ikenna and harsh pick master plans which agent groups tackle over their time with 1
> VM. We should be able to change these plans without restarting the VM. Each VM and epic/master plan has 1 slot main
> orchestrator agent, 1 slot review agent, x worker agents max within rate limits + CPU bound. In the dashboard we want
> a landing page overview of all the master plans/epics that each VM owns, and then when we click through we see the
> same view we already have. Separately we want a planning VM where ikenna and harsh can see each others chats.
> Auto-refresh works on each VM after one-time /login. 4 accounts per VM, primary round-robin across VMs so 8 VMs each 2
> share an account. Things should be backed up to GCS/S3 such that on VM restarts we get the info we need."

## Design SSOTs (codex)

Three codex docs hold the detailed design. The epic body is the planning orchestrator; the active plans drive the
implementation; the codex SSOTs are the architectural truth.

| Codex SSOT                                                                                                                                     | Owns                                                                                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`codex/12-agent-workflow/orchestrator-multi-vm-topology.md`](../../codex/12-agent-workflow/orchestrator-multi-vm-topology.md)                 | VM shapes (epic VM + planning VM) + Plan→VM assignment + Registry + Per-VM backend + Backlog auto-gen + Dashboard aggregation + Persistence + VM provisioning |
| [`codex/12-agent-workflow/orchestrator-safety-mechanisms.md`](../../codex/12-agent-workflow/orchestrator-safety-mechanisms.md)                 | Stuck-agent detection + auto-respawn + Auth failover (non-blocking) + Telegram alerts framework + Git staleness ping + Fresh-spawn dirty-commit               |
| [`codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`](../../codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md) | r3 auth architecture (long-lived `setup-token` via `CLAUDE_CODE_OAUTH_TOKEN`); supersedes the `.credentials.json` swap that caused the 2026-05-21 cascade     |

Registry SSOT: [`../../orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml) — 10 VMs × 19 epics × 4
accounts.

## Operator decisions captured

- **Backend topology**: per-VM backend, dashboard aggregates (each VM independently resilient).
- **VM count**: 1 planning VM + 9 epic VMs as default; flexible per epic count over time; current topology in
  `orchestrator_vm_registry.yaml`.
- **Plan → VM assignment**: frontmatter on plan is source of truth + registry regen script.
- **Failover order**: lowest-weekly-pct-first across the 3 non-primary accounts.
- **Planning VM**: cloud-hosted (NOT operator's mac); SSH from VSCode like every other VM.
- **VM naming**: descriptive ids (`vm-defi`, `vm-cefi`, ...). Dashboard `label:` field is the human-readable dropdown
  name. `ssh_host:` matches `~/.ssh/config`.
- **DNS**: single UI URL `agent-orchestrator.odum-research.com`. API endpoints under
  `*.agent-orchestrator.odum-research.com` (wildcard A record acceptable).
- **KMS**: same key per VM (one shared `agent-orchestrator-state-encrypt` key in GCP, one in AWS).
- **Cold-start**: <5 min target.
- **Per-VM RBAC**: out of scope; revisit if external collaborators get dashboard access.

## Implementation roadmap (Phase status + active plan ownership)

Detailed Phase 0-12 design lives in
[`codex/12-agent-workflow/orchestrator-multi-vm-topology.md`](../../codex/12-agent-workflow/orchestrator-multi-vm-topology.md).
Implementation work is owned by the assigned active plans below. Status as of 2026-05-21:

| Phase      | Scope                                                                                                                                                                                                                                                                                                                                                                                                                            | Status                                                                                                                                                                                                    | Owned by active plan                                                                             |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 0          | Prerequisites (OAuth auto-refresh + per-account creds swap + Telegram alert framework)                                                                                                                                                                                                                                                                                                                                           | ✅ DONE (agent-orch@4eabf5c + @2de9410); one operator action remaining                                                                                                                                    | `d0_orchestrator_migration_2026_05_20`                                                           |
| 1          | Registry yaml + `assigned_vm:` frontmatter + regen script + CLAUDE.md update                                                                                                                                                                                                                                                                                                                                                     | ✅ DONE (PM@e3f11893; updated to v2 2026-05-21)                                                                                                                                                           | `d0_orchestrator_migration_2026_05_20`                                                           |
| 2          | Multi-VM dashboard (SPA `/` landing + `/api/vm/summary` endpoint + cross-VM cards + Firebase deploy)                                                                                                                                                                                                                                                                                                                             | ✅ DONE 2026-05-21 (agent-orch@c274059 + @f357132)                                                                                                                                                        | `agent_orchestrator_cloud_run_deployment_2026_05_19`                                             |
| 3          | Safety mechanisms (stuck-detection + auto-respawn + dirty-commit + git-staleness alert)                                                                                                                                                                                                                                                                                                                                          | ✅ DONE 2026-05-21 (agent-orch@72b4b0a)                                                                                                                                                                   | `agent_reliability_mitigations_2026_05_20` + `agent_orchestrator_slack_notifications_2026_05_19` |
| 4a         | Spawn path → env-var auth (r3) (`oauth_token_env_file` + `tmux_spawn.py` refactor)                                                                                                                                                                                                                                                                                                                                               | ✅ DONE 2026-05-21 (agent-orch@d7b6ad6)                                                                                                                                                                   | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4b         | r3 env-file routing: roster on SSOT slugs (`sub-a-ikenna`/`sub-b-iggy2london`) + `AccountDef.operator`; spawn + `/usage` probe + `oauth_refresh` all bypass the legacy swap/refresh for any account with `oauth_token_env_file`. Legacy `.credentials.json` path retained for `harsh-primary` until its setup-token lands. Also fixed a silent poller `resets_at`-kwarg `TypeError` that was blocking per-account usage updates. | ✅ DONE 2026-05-21 (agent-orch@5d78133; deployed + env-file `/usage` probe verified: sub-a 8%/4%, sub-b 1%/8%)                                                                                            | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4b-cleanup | Remove legacy code once `harsh-primary` migrates to a setup-token: delete `_swap_credentials_for`/`_restore_credentials`, disable `oauth_refresh.refresh()` auto-call, remove `.credentials.<id>.json` files + the `swap_claude_account.sh` reference. CLAUDE.md HARD RULE (no `.credentials.json` copy between machines).                                                                                                       | 🟡 PENDING (blocked on Phase 5 harsh setup-token)                                                                                                                                                         | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4c         | Dashboard repurpose (`SetupTokenBadge` shows 1-year expiry warn/crit/expired levels; `notify_setup_token_expiring` fires at ≤30d + ≤7d; `setup_token_expires_at` in accounts.json; all 3 r3 accounts seeded to 2027-05-21)                                                                                                                                                                                                       | ✅ DONE 2026-05-21 (agent-orch@tab/ikennaigboaka/1)                                                                                                                                                       | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 5          | Account roster expansion (operator runs `setup-token` per distinct subscription; verify-distinct-subscription test; GCS distribution)                                                                                                                                                                                                                                                                                            | 🟡 PARTIAL — Ikenna 3 accounts live (sub-a/sub-b/sub-c env files + expiry dates set). Harsh pending: run `claude setup-token` + send token → add to ~/.claude-accounts/harsh-primary.env + accounts.json. | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 6          | Backlog auto-gen from plans (`regen_backlog_from_plan.py` + plan-reload poll + CLAUDE.md hard rule)                                                                                                                                                                                                                                                                                                                              | 🟡 PENDING                                                                                                                                                                                                | `agent_orchestrator_workers_on_vms_2026_05_19`                                                   |
| 7          | Planning VM provisioning (cloud-hosted; slot 1+2 only; registry symlink; landing-page wired)                                                                                                                                                                                                                                                                                                                                     | 🟡 PENDING                                                                                                                                                                                                | `agent_orchestrator_workers_on_vms_2026_05_19`                                                   |
| 8          | Persistence (SQLite hot-backup → GCS every 6h via `SnapshotLoop`; restore script `scripts/restore_from_gcs.sh`)                                                                                                                                                                                                                                                                                                                  | ✅ DONE 2026-05-21 (agent-orch@tab/ikennaigboaka/1; KMS-encrypted creds pending)                                                                                                                          | `agent_orchestrator_dual_deployment_2026_05_19`                                                  |
| 9          | VM provisioning (packer/docker pipeline; immutable image; `bootstrap_vm.sh`; <5min cold-start)                                                                                                                                                                                                                                                                                                                                   | 🟡 PENDING                                                                                                                                                                                                | `agent_orchestrator_dual_deployment_2026_05_19`                                                  |
| 10         | Review agent role (`agents/review.md` boot prompt; commit-poll logic; auto-merge happy-path)                                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-21 (`agents/review.md` shipped; agent-orch@tab/ikennaigboaka/1)                                                                                                                           | `agent_orchestrator_workers_on_vms_2026_05_19`                                                   |
| 11         | Rollout to 9 epic VMs (provision via Phase 9 pipeline; DNS A records; cut over current single-VM to vm-defi)                                                                                                                                                                                                                                                                                                                     | 🟡 PENDING                                                                                                                                                                                                | `agent_orchestrator_cloud_run_deployment_2026_05_19`                                             |
| 12         | Cleanup + docs (archive superseded plans; codex SSOTs landed; CLAUDE.md System-First Architecture pointer)                                                                                                                                                                                                                                                                                                                       | ✅ DONE 2026-05-21 — codex SSOTs landed, plans archived (hygiene sweep), CLAUDE.md System-First Architecture pointer already accurate                                                                     | `d0_orchestrator_migration_2026_05_20`                                                           |

## Composition with other epics

- **Orchestrates all 18 other epics**: every epic VM in the registry hosts an instance of the agent-orchestrator stack
  this epic owns. Topology changes (new VM, account roster expansion, planning VM moves) ripple to every other epic.
- **Audit-pool flow**: every audit row in `plans/active/issues/human_led_audit_pool_*.md` flows through the planning VM
  (defined here) → wrapper plans → target epic VM dispatch. See
  [`../../plans/epics/README.md`](../../plans/epics/README.md) for the audit→plan→epic flow.
- **Cross-cutting partnerships**: `infrastructure_master` (VM tarballs + provisioning + cloud bootstrap underpins this
  epic's VM lifecycle); `observability_master` (alerting-service + Telegram alerts + monitoring composes with § C
  Telegram alerts framework); `client_isolation_and_governance_master` (per-spawn account isolation per
  `agent_orchestrator_per_spawn_account_isolation_2026_05_20` enforces governance at the spawn boundary).

## Out of scope (post-v0.7)

- Multi-region VMs (today: all asia-northeast1)
- Per-VM separate Telegram channels (today: single shared chat)
- Cross-VM dependency graph (e.g. vm-ml waits on vm-features); today operators coordinate via epic prereqs
- Auto-scaling worker count based on backlog depth (today: fixed at 8-16 per VM)
- Cloud Run / serverless orchestrator backend (today: VM-bound systemd); defer until VM ops become painful
- Per-VM RBAC

## Assigned active plans

_7 active plans declare `parent_epic: orchestrator_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority)_

## P1 — important; post-current-gate

### [`d0_orchestrator_migration_2026_05_20`](../active/d0_orchestrator_migration_2026_05_20.md)

**status**: active · **estimate**: 0.2 cal AI-days (class: refactor) **title**: D0 — agent-orchestrator migration plan

## P2 — useful; opportunistic

### [`agent_orchestrator_cloud_run_deployment_2026_05_19`](../active/agent_orchestrator_cloud_run_deployment_2026_05_19.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: infra)

### [`agent_orchestrator_dual_deployment_2026_05_19`](../active/agent_orchestrator_dual_deployment_2026_05_19.md)

**status**: active · **estimate**: 0.6 cal AI-days (class: design)

### [`agent_orchestrator_per_spawn_account_isolation_2026_05_20`](../active/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md)

**status**: active · **estimate**: 2.0 cal AI-days (class: brand-new)

### [`agent_orchestrator_slack_notifications_2026_05_19`](../active/agent_orchestrator_slack_notifications_2026_05_19.md)

**status**: active · **estimate**: 2.0 cal AI-days (class: infra)

### [`agent_orchestrator_workers_on_vms_2026_05_19`](../active/agent_orchestrator_workers_on_vms_2026_05_19.md)

**status**: active · **estimate**: 6.4 cal AI-days (class: infra)

### [`agent_reliability_mitigations_2026_05_20`](../active/agent_reliability_mitigations_2026_05_20.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: infra)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
