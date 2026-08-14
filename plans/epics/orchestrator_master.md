---
doc_type: epic
title: Orchestrator Master (L5)
summary:
  L5 epic owning the agent-orchestrator multi-VM runtime — central 'planning' VM + human-planning VM + slot workers
  (human/central split 2026-06-12), dashboard aggregation, long-lived setup-token auth failover, per-spawn account
  isolation, cross-VM observability, and self-healing safety (stuck-agent respawn, dirty-commit, git-staleness alerts);
  strict per-plan assigned_vm matching now owned by WS-G.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos:
  [agent-orchestrator, alerting-service, deployment-service, execution-service, features-service, instruments-service]
scope: [engineer, admin]
tags: [orchestrator, role-registry, self-healing, observability, infrastructure, escalation, slack]
related:
  [
    ../archive/2026_05/agent_orchestrator_cloud_run_deployment_2026_05_19.md,
    ../archive/2026_05/agent_orchestrator_dual_deployment_2026_05_19.md,
    ../archive/2026_05/agent_orchestrator_per_spawn_account_isolation_2026_05_20.md,
    ../archive/agent_orchestrator_slack_notifications_2026_05_19.md,
    ../archive/agent_orchestrator_workers_on_vms_2026_05_19.plan.md,
    ../archive/2026_05/agent_reliability_mitigations_2026_05_20.md,
    ../archive/2026_05/d0_orchestrator_migration_2026_05_20.md,
    ../active/issues/human_led_audit_pool_2026_05_21.md,
  ]
created: 2026-05-21
name: orchestrator_master
tier: L5
priority: P0
assigned_vm: NA # corrected 2026-08-06 (operator ruling during /plan-reconcile ao, generalising the 2026-08-02 § 2e ruling on plan_reconcile_parked_operator_decisions_2026_08_02.md); PLAN_FORMAT.md:204 — NA is the expected value on every current epic. (was: planning — corrected 2026-07-16 from vm-orchestrator, ao_docs_reconciliation F1; vm-orchestrator was a pre-2026-06-27 multi-VM host id retired by the single-VM pivot. Matches the agent_operating_framework_master precedent.)
parent: master_to_live_defi_2026_05_23
co_operators: [harsh]
codex_ssots:
  [
    /codex/11-project-management/epic-execution-with-sub-agents.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
  ]
related_plans:
  - ../active/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize_2026_08_08.md
  - ../active/ao_open_issues_consolidated_close_out_2026_07_17.md
  - ../archive/2026_08/ao_satellite_ao_dispatch_batch10_2026_08_09.md
  - ../active/ao_satellite_ao_dispatch_batch10_finalize_2026_08_09.md
  - ../active/ao_satellite_ao_dispatch_batch12_2026_08_09.md
  - ../active/ao_satellite_ao_dispatch_batch12_finalize_2026_08_09.md
  - ../active/ao_satellite_ao_dispatch_batch14_2026_08_09.md
  - ../active/ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md
  - ../active/ao_satellite_ao_dispatch_batch2_2026_07_30.md
  - ../active/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md
  - ../active/ao_satellite_ao_dispatch_batch3_2026_07_31.md
  - ../active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md
  - ../active/ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md
  - ../active/ao_satellite_ao_dispatch_batch5_2026_08_03.md
  - ../active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md
  - ../archive/2026_08/ao_satellite_ao_dispatch_batch6_2026_08_04.md
  - ../archive/2026_08/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md
  - ../active/ao_satellite_ao_dispatch_batch7_2026_08_06.md
  - ../active/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md
  - ../active/ao_satellite_ao_dispatch_batch8_2026_08_08.md
  - ../active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md
  - ../active/ao_satellite_ao_dispatch_batch9_2026_08_08.md
  - ../active/ao_satellite_ao_dispatch_batch9_finalize_2026_08_08.md
  - ../active/ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md
  - ../active/content_derived_backlog_task_ids_2026_08_08.md
  - ../active/content_derived_backlog_task_ids_2026_08_08_finalize.md
  - ../active/deepseek_claude_blended_provider_routing_2026_07_28.md
  - ../active/deepseek_flash_ab_routing_test_2026_08_05.md
  - ../active/quality_gates_quickmerge_timing_baseline_2026_07_31.md
  - ../active/quality_gates_quickmerge_timing_baseline_2026_07_31_finalize_2026_08_08.md
  - ../active/review_agent_evidence_gated_write_capability_2026_08_09.md
last_updated: 2026-07-16
locked_by: live-defi-rollout
locked_since: 2026-05-21
external_references:
  [
    "Operator-shared 2026-05-21: Claude CLI Multi-Account Headless Authentication Guide (long-lived setup-token via
    CLAUDE_CODE_OAUTH_TOKEN env var, ~1y validity, multi-machine reuse, ANTHROPIC_API_KEY-precedence gotcha) — drives
    the r3 Auth & accounts revision and Phase 4 r3 rewrite",
  ]
---

# Orchestrator Master (L5)

> **🟡 IN-FLIGHT REFACTOR — UTL/UAC reuse consolidation** (guardrails phase:
> [`utl_reuse_phase0_guardrails_2026_07_13`](../archive/2026_07/utl_reuse_phase0_guardrails_2026_07_13.md); compose
> phases: `utl_reuse_phase1_strategy_risk_hwm_2026_07_13` (strategy risk/HWM),
> `utl_reuse_phase3_ml_model_registry_2026_07_13` (ml ModelRegistry),
> `utl_reuse_phase4_features_builder_registry_2026_07_13` (features builder_registry)). Concurrent slots: do not
> re-touch the strategy risk-eval, ml-registry, or features-builder-registry surfaces until those phase plans land —
> check them first.

**Owns**: agent-orchestrator multi-VM stack (central/orchestrator VM `planning` + human planning VM `human-planning` + 9
epic VMs — human/central SPLIT 2026-06-12, see `plans/active/orchestrator_human_central_vm_split_2026_06_12.md`);
dashboard aggregation; auth failover (long-lived setup-token pattern); per-spawn account isolation; cross-VM
observability; Telegram alert framework; safety mechanisms (stuck-agent respawn, auth failover without respawn,
fresh-spawn dirty-commit, git staleness alerts).

**Assigned VM**: `vm-orchestrator` (self-managing — the agent-orchestrator stack runs the agent-orchestrator stack).

## Scope inherited from `orchestrator_v07_multi_vm_topology_2026_05_21` (promoted 2026-05-21)

This epic was promoted from the active plan `orchestrator_v07_multi_vm_topology_2026_05_21.md` per the epic
consolidation. Detailed design moved to codex SSOTs; implementation phases continue as the assigned active plans listed
below.

> **Sync 2026-07-12** (finding 325, §A2 B-queue ruling): frontmatter `last_updated` was 2026-05-21 while the body
> already carried dated entries through 2026-07-12 (e.g. the `auth_failed` cooldown fix DONE 2026-06-10 —
> `agent-orchestrator@68116f7`, plus later notices below) — bumped `last_updated` to 2026-07-12 (was: 2026-05-21) to
> match the doc's own latest content.

> **Partial-supersede notice (VM-assignment scope — 2026-06-25):** The `assigned_vm:` mandatory frontmatter rule
> (introduced by the v07 plan) and the strict per-plan VM matching (fail-closed dispatch, D1–D6) are now owned and
> enforced by `plans/active/orchestrator_consolidated_remaining_2026_06_25.md` (WS-G). The epic-delegation path
> (`_resolve_plan_vms` reading `parent_epic`) has been DROPPED; strict backend-id == plan.assigned_vm is the only
> matching mode. See WS-G for the live design decisions. This note is a pointer — NOT a wholesale supersede of this
> epic's other scope. **(Stale-path note, corrected 2026-07-14, finding 203):** the WS-G target
> (`orchestrator_consolidated_remaining_2026_06_25.md`) has itself since been archived (`status: superseded`, now at
> `archive/orchestrator_consolidated_remaining_2026_06_25.plan.md`) with its open items further migrated onward; a
> sibling epic (`agent_operating_framework_master.md` W1) separately still points at a DIFFERENT, also-archived owner
> (`dispatch_strict_vm_matching_2026_06_24.md`, `status: superseded`) for this same D1–D6 scope. In practice this is
> moot: per the very next notice below, the whole multi-VM `assigned_vm==backend` matching premise this scope existed
> for was itself superseded by the 2026-06-27 single-VM pivot (dispatch is now role/skill-based, not per-VM matching),
> so neither archived owner needs reviving.

> **Fleet-description supersede notice (2026-07-11):** The multi-VM / 9-epic-VM fleet description used throughout this
> epic — including the **Owns** section above and the `assigned_vm: vm-orchestrator` frontmatter — is SUPERSEDED by the
> single-VM role-based dispatch architecture (2026-06-27): ONE central orchestrator VM (id `planning`) with N slot
> workers, dispatch by role/skill, no per-epic VMs. SSOT:
> `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (see also the workspace `CLAUDE.md` system-map
> summary). The historical multi-VM / 9-epic-VM text below (incl. "Owns", "Why this epic exists", and the assigned-VM
> frontmatter) is KEPT for context only — it does NOT describe the current architecture. Finding + adversarial
> verification trail: `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` (finding 349).

## Why this epic exists

Today's orchestrator runs ONE VM, ONE main agent, ONE backlog. It scaled to ~11 slots but hits recurring failure modes:
auth token expiry cascade (2026-05-21 incident), agent staleness without recovery, cross-plan blast radius, no cross-VM
observability, operator cognitive load. The v0.7 fix splits into **per-epic VM fleets** (each isolated, full agent
topology + own backend) + a **planning/human role on its OWN VM** + a **dashboard landing page** that aggregates. The
planning/human role is now its own dedicated VM (`human-planning`), separate from the central/orchestrator VM (id
`planning`) that runs the central API + AutoSpawn + CI-escalation + plan-health (human/central SPLIT 2026-06-12 — see
`plans/active/orchestrator_human_central_vm_split_2026_06_12.md`).

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

| Codex SSOT                                                                                                                                       | Owns                                                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`](/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md) | VM shapes (epic VM + planning VM) + Plan→VM assignment + Registry + Per-VM backend + Backlog auto-gen + Dashboard aggregation + Persistence + VM provisioning |
| [`/codex/12-agent-workflow/orchestrator-safety-mechanisms.md`](/codex/12-agent-workflow/orchestrator-safety-mechanisms.md)                       | Stuck-agent detection + auto-respawn + Auth failover (non-blocking) + Telegram alerts framework + Git staleness ping + Fresh-spawn dirty-commit               |
| [`/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`](/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md)       | r3 auth architecture (long-lived `setup-token` via `CLAUDE_CODE_OAUTH_TOKEN`); supersedes the `.credentials.json` swap that caused the 2026-05-21 cascade     |

Registry SSOT: [`../../orchestrator_vm_registry.yaml`](../../orchestrator_vm_registry.yaml) — 10 VMs × 4 accounts; epic
count is NOT hardcoded here — see [`epics/README.md`](README.md) registry, regenerated 2026-07-12 (plan-reconciliation
finding 339) for the true, current epic count.

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
[`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`](/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md).
Implementation work is owned by the assigned active plans below. Status as of 2026-05-21:

| Phase      | Scope                                                                                                                                                                                                                                                                                                                                                                                                                            | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Owned by active plan                                                                             |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 0          | Prerequisites (OAuth auto-refresh + per-account creds swap + Telegram alert framework)                                                                                                                                                                                                                                                                                                                                           | ✅ DONE (agent-orch@4eabf5c + @2de9410); one operator action remaining                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | `d0_orchestrator_migration_2026_05_20`                                                           |
| 1          | Registry yaml + `assigned_vm:` frontmatter + regen script + CLAUDE.md update                                                                                                                                                                                                                                                                                                                                                     | ✅ DONE (PM@e3f11893; updated to v2 2026-05-21)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | `d0_orchestrator_migration_2026_05_20`                                                           |
| 2          | Multi-VM dashboard (SPA `/` landing + `/api/vm/summary` endpoint + cross-VM cards + Firebase deploy)                                                                                                                                                                                                                                                                                                                             | ✅ DONE 2026-05-21 (agent-orch@c274059 + @f357132)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `agent_orchestrator_cloud_run_deployment_2026_05_19`                                             |
| 3          | Safety mechanisms (stuck-detection + auto-respawn + dirty-commit + git-staleness alert)                                                                                                                                                                                                                                                                                                                                          | ✅ DONE 2026-05-21 (agent-orch@72b4b0a)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | `agent_reliability_mitigations_2026_05_20` + `agent_orchestrator_slack_notifications_2026_05_19` |
| 4a         | Spawn path → env-var auth (r3) (`oauth_token_env_file` + `tmux_spawn.py` refactor)                                                                                                                                                                                                                                                                                                                                               | ✅ DONE 2026-05-21 (agent-orch@d7b6ad6)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4b         | r3 env-file routing: roster on SSOT slugs (`sub-a-ikenna`/`sub-b-iggy2london`) + `AccountDef.operator`; spawn + `/usage` probe + `oauth_refresh` all bypass the legacy swap/refresh for any account with `oauth_token_env_file`. Legacy `.credentials.json` path retained for `harsh-primary` until its setup-token lands. Also fixed a silent poller `resets_at`-kwarg `TypeError` that was blocking per-account usage updates. | ✅ DONE 2026-05-21 (agent-orch@5d78133; deployed + env-file `/usage` probe verified: sub-a 8%/4%, sub-b 1%/8%)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4b-cleanup | Remove legacy code once `harsh-primary` migrates to a setup-token: delete `_swap_credentials_for`/`_restore_credentials`, disable `oauth_refresh.refresh()` auto-call, remove `.credentials.<id>.json` files + the `swap_claude_account.sh` reference. CLAUDE.md HARD RULE (no `.credentials.json` copy between machines).                                                                                                       | ✅ DONE 2026-05-28 (agent-orch@d883e41→@8c52691: dropped swap helpers + oauth_refresh + gcs_creds_poller modules + refresh-oauth/sync-from-gcs endpoints + OAuthBadge UI; tightened tmux_spawn/usage_tracker/spawn callers to require env_file; CLAUDE.md HARD RULE landed in PM)                                                                                                                                                                                                                                                                                                                                                                                    | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4c         | Dashboard repurpose (`SetupTokenBadge` shows 1-year expiry warn/crit/expired levels; `notify_setup_token_expiring` fires at ≤30d + ≤7d; `setup_token_expires_at` in accounts.json; all 3 r3 accounts seeded to 2027-05-21)                                                                                                                                                                                                       | ✅ DONE 2026-05-21 (agent-orch@tab/ikennaigboaka/1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 5          | Account roster expansion (operator runs `setup-token` per distinct subscription; verify-distinct-subscription test; GCS distribution)                                                                                                                                                                                                                                                                                            | ✅ DONE 2026-05-28 — All 4 accounts (3 Ikenna + 1 Harsh) have setup-tokens minted + env files distributed to both GCS (`central-element-323112-orchestrator-creds/accounts/`) and S3 (`uts-orchestrator-creds-427895769566/accounts/`), 206 bytes each, verified                                                                                                                                                                                                                                                                                                                                                                                                     | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 6          | Backlog auto-gen from plans (`regen_backlog_from_plan.py` + plan-reload poll + CLAUDE.md hard rule)                                                                                                                                                                                                                                                                                                                              | ✅ DONE 2026-05-28 — `regen_backlog_from_plan.py` + `PlanRegenLoop` (6h cadence, fires within 60s of boot, env-tunable, `POST /api/backlog/regen` for manual) + 29-test suite (agent-orch@2a24c46); content-based dedup fixed an idempotency bug surfaced by the new tests; CLAUDE.md HARD RULE added                                                                                                                                                                                                                                                                                                                                                                | (formerly `agent_orchestrator_workers_on_vms_2026_05_19`, archived)                              |
| 7          | Planning VM provisioning (cloud-hosted; slot 1+2 only; registry symlink; landing-page wired)                                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-28 — Central API EC2 VM (`13.113.200.22`, AWS ap-northeast-1) serves as the planning VM (ikenna-vm role=planning in `backends.json`); cross-VM `/api/fleet/summary` fan-out + `Landing.tsx` cards live in dashboard (verified: HTTPS /health 200 + 12 backends registered); planning VM bootstrap items shipped under archived `epic_vm_fleet_commissioning_2026_05_21`                                                                                                                                                                                                                                                                              | (formerly `agent_orchestrator_workers_on_vms_2026_05_19`, archived)                              |
| 8          | Persistence (SQLite hot-backup → GCS every 6h via `SnapshotLoop`; restore script `scripts/restore_from_gcs.sh`)                                                                                                                                                                                                                                                                                                                  | ✅ DONE 2026-05-21 (agent-orch@tab/ikennaigboaka/1; KMS-encrypted creds pending)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | `agent_orchestrator_dual_deployment_2026_05_19`                                                  |
| 9          | VM provisioning (packer/docker pipeline; immutable image; `bootstrap_vm.sh`; <5min cold-start)                                                                                                                                                                                                                                                                                                                                   | ✅ DONE 2026-05-28 — Packer HCL2 template + provisioner scripts (`deployment-service/packer/agent-orchestrator/`); `bootstrap_vm.sh` detects `/etc/orchestrator-ami-version` marker + rsyncs warm repos + venv from `/opt/orchestrator-warm/` (Steps 1+2+4.5 skipped on prebaked path); `launch-epic-vm-aws.sh` accepts `AMI_ID` env-var override; README + codex DNS-cutover SSOT shipped. Operator runs `packer build` to bake, then `AMI_ID=… launch-epic-vm-aws.sh` to use                                                                                                                                                                                       | (formerly `agent_orchestrator_dual_deployment_2026_05_19`, archived)                             |
| 10         | Review agent role (`agents/review.md` boot prompt; commit-poll logic; auto-merge happy-path)                                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-21 (`agents/review.md` shipped; agent-orch@tab/ikennaigboaka/1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | `agent_orchestrator_workers_on_vms_2026_05_19`                                                   |
| 11         | Rollout to 9 epic VMs (provision via Phase 9 pipeline; DNS A records; cut over current single-VM to vm-defi)                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-28 — Fleet of 10 epic VMs already running (commissioned 2026-05-22→23 via `aws_epic_vm_fleet_2026_05_22`); cut over from single-VM model superseded by central-API-VM-plus-fleet topology (current `backends.json` shows 12 backends, all live); EIP allocation script shipped (`deployment-service/scripts/aws/allocate-orchestrator-eips.sh`) + DNS cutover recipe codified ([agent-orchestrator-dns-cutover.md](/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md)). Operator runs EIP script + adds A records to complete cutover when convenient (not blocking; current ops work fine on dynamic IPs via central API proxy) | (formerly `agent_orchestrator_cloud_run_deployment_2026_05_19`, archived)                        |
| 12         | Cleanup + docs (archive superseded plans; codex SSOTs landed; CLAUDE.md System-First Architecture pointer)                                                                                                                                                                                                                                                                                                                       | ✅ DONE 2026-05-21 — codex SSOTs landed, plans archived (hygiene sweep), CLAUDE.md System-First Architecture pointer already accurate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `d0_orchestrator_migration_2026_05_20`                                                           |

## Composition with other epics

- **Orchestrates all 22 other epics** (corrected 2026-08-06, /plan-reconcile ao — was: "18 other epics"; live registry
  is 23 epics total per `epics/README.md`, 23 − 1 self = 22): the single central orchestrator VM (id `planning`) this
  epic owns runs the agent-orchestrator stack that dispatches role/skill-based work for every other epic — there is no
  longer one epic VM per epic (single-VM architecture, 2026-06-27; was: "every epic VM in the registry hosts an instance
  of the agent-orchestrator stack this epic owns"). Topology changes (slot count, account roster expansion, planning VM
  moves) ripple to every other epic.
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

## AO issue register — 2026-07-16 reconciliation sweep

> **Why this section exists.** The AO issue corpus had rotted into false-open/false-resolved claims: docs asserting
> `resolved` while the bug is still live in code, and docs sitting `open` whose subject the backend deleted weeks ago.
> Three separate meta-trackers (`issue_docs_remediation_sweep_2026_06_02`, `ao_docs_reconciliation_2026_07_15`,
> `ao_dispatch_residuals_2026_07_15`) each exist _because_ of this — it is a pattern, not bad luck. Operator ruling
> 2026-07-16: enumerate every AO issue doc HERE so none is missed, **re-verify each against CODE (ground truth, not the
> doc)**, archive what is genuinely fixed, and fold the survivors into a small number of plans. Rationale (operator):
> _"the stale docs are not going to help us much in terms of solving the current issues we have in AO. there have been
> many updates on the ao backend and its behaviour and if we keep working on old issue docs its possible we would add
> more regression then fixing it."_
>
> **Enumeration method (do not regress it).** The list below is the union of THREE axes, because no single axis is
> complete: (1) `rg -l '^repos:.*agent-orchestrator' plans/active/issues/`; (2)
> `parent_epic ∈ {orchestrator_master, agent_operating_framework_master}` — this axis alone caught 5 docs the `repos:`
> filter misses; (3) `plans/archive/issues/` re-scanned for AO docs that are archived **yet still carry open `- [ ]`
> todos**. A filename-prefix (`ao_*`) filter is NOT sufficient — it undercounted this corpus by 5 on 2026-07-15.
>
> **Verdict column** is filled from per-doc CODE verification (every todo, open _and_ claimed-done, must cite
> `file:line`). `⚠️` marks a status/todo contradiction found during enumeration.

### Verification outcome — 2026-07-16 (all 20 docs code-verified)

**Headline: the corpus does NOT over-claim fixes.** Every single `- [x]` claimed-done todo re-verified across all 20
docs was **genuinely present in code** (message-redelivery 10/10, fleet-stall 3/3, prettier 3/3, qg-governor 4/4,
qg-testpaths 5/5, dp-alert-flood 10/10). Not one false "done". The corpus fails in **four other ways**, each of which
this sweep found and each of which is more dangerous than a false done, because a false done is at least _checkable_:

1. **Fixes scoped narrower than the doc's title.** `ao_operator_message_silent_drop` fixed `agent_messages`
   (main/review/custom chat agents) and left the parallel `SlotMessageRow` channel — the one **craft task workers** use
   — with the identical silent-drop bug (`state_store/activity.py:227-238`: `delivered_at` stamped on take, no
   `answered_at`, no reply-ack, no redelivery). Reading the doc's title, you would conclude operator messaging is fixed.
2. **Follow-ups orphaned by archival.** `ao_autospawn_role_blind_dispatch_starvation` was archived `resolved` with 2
   live-code bugs open and **no `superseded_by`** — so the work was not tracked forward, it was independently
   **re-discovered a day later** and re-filed as a duplicate doc.
3. **Remedies that are wrong, and in two cases dangerous.** Three separate docs prescribe fixes that current code
   contradicts — see the table below. This is the concrete form of the operator's 2026-07-16 concern that "if we keep
   working on old issue docs it's possible we would add more regression then fixing it".
4. **Deployment never verified.** Code shipped, doc marked done, the thing never actually turned on: the tradfi
   wave-launcher cron **PAUSED 21 days**, `install-prune-uv-cache-cron.sh` **never installed**, the qg-host-governor
   measured `MODE=token` (not `reservation`) on the real orchestrator VM. Each took one command to check.

#### ⚠️ Do NOT implement these docs' literal remedies (code-verified 2026-07-16)

| Doc                                            | Its written remedy                                           | Why it is wrong / dangerous                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ---------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dispatcher_role_eligibility_gap_review_slots` | "add a `slot_role`-based filter to exclude non-worker slots" | `slot_role` is a **craft** field, only set in `render_worker()`. Review/main **never** have it — so the filter no-ops for exactly the slots it targets. **Worse**: `dispatch.py:95-96` notes `slot_role` is empty for **most ordinary worker slots too**, so refusing dispatch on falsy `slot_role` would **break the majority of normal worker dispatch, fleet-wide.** Correct fix = join `AgentRow.role` (a separate column `dispatch.py` never touches), keeping the craft gate as a distinct upstream check → R6. |
| `capability_wizard_analysis_findings` (F48)    | "register the missing VOL\_\*/MARKET_MAKING\_\* engines"     | Directly contradicts a deliberate design decision now encoded in `market_making/__init__.py`: _"Registering an un-backtested engine would make the verdict matrix LIE."_ The real fix shipped as a **third option the doc never considered** — the generator live-probes `ARCHETYPE_ENGINE_REGISTRY` and flags `not_registered`. Following the doc would **reintroduce the dishonesty the code now guards against.**                                                                                                  |
| `ao_dispatch_residuals` (R7, "larger fix")     | "switch task-id generation to a content hash"                | Blast radius across `existing_ids` bookkeeping, `slot_skips` (keyed by task_id), dashboard/API id refs, and `done_sha` history. The **dangerous half of R7 is already fixed** (`agent-orchestrator@4695db6`, `brief_hash` reset-on-mismatch); the residue needs an external race and explains none of the operator's symptoms. **R7 goes DOWN the priority list, not up.**                                                                                                                                            |

### Core AO runtime (the "make AO work properly" scope)

| #   | Issue doc                                                                                                                                     | P   | Code verdict (2026-07-16)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Disposition                                                                         |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------- | --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1   | [`ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07`](../active/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md)            | P0  | **PARTIALLY-FIXED.** 3/3 done genuinely in code (RC-1/2/3; one _understates_ its fix — a later `69870f4` added a real queue-side role filter). 3 open **STILL-BROKEN** = R2 (mixed-tier spawn), R3 (monitor over-generalises a gate), R4 (Opus/Sonnet mixing guidance).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | → plan (R2/R3/R4)                                                                   |
| 2   | [`ao_skip_blind_spawn_budget_phantom_churn_2026_07_15`](../active/../archive/issues/ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md)   | P1  | **STILL-OPEN = R1**, the best-specified description of the core defect (carries the live measurement: budget=6 vs claimable=1; **1014 autospawns / 954 worker-deaths → 101 done in 24h**). `rg slot_skip server/autospawn.py` → **0 hits**.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | → plan (R1 — keystone)                                                              |
| 3   | [`ao_dispatch_residuals_2026_07_15`](../active/issues/ao_dispatch_residuals_2026_07_15.md)                                                    | P1  | **All of R1–R7 STILL-BROKEN**, R7 narrower than framed (its dangerous half fixed @`4695db6`). Canonical residual list. Missing a `related:` link to `backlog_regen_id_reuse_stale_status_2026_07_15`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | → plan (canonical spec)                                                             |
| 4   | [`ao_operator_message_silent_drop_no_reply_ack_2026_07_08`](../active/issues/ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md)      | P1  | **PARTIALLY-FIXED — 10/10 done verified in code.** 1 open (tmux nudge single-shot, no retry) genuinely open. **NEW (no doc covers it):** the `SlotMessageRow` task-worker channel still has the identical silent-drop bug; and `needs_operator_count` is computed (`routes/agents.py:226-231`) but **rendered nowhere** — 0 hits in the dashboard `.tsx`, no Slack wiring. A stuck agent is invisible.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | → plan (+ 2 new items)                                                              |
| 5   | [`dispatcher_role_eligibility_gap_review_slots_2026_07_13`](../active/issues/dispatcher_role_eligibility_gap_review_slots_2026_07_13.md)      | P2  | **STILL-OPEN = R6.** Repro found: `prompts.py::_compose` unconditionally emits `STEP 0 — POST /api/slots/{id}/heartbeat` whenever `slot_id is not None`, and `ensure_review_agents`→`_do_spawn` **does** pass one for review slots → the review agent is told by its own boot prompt to call the endpoint that dispatches it worker tasks. Contradicts `test_slotless_render_skips_slot_boot_steps`'s comment. **Its own remedy is dangerous — see table above.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | → plan (R6)                                                                         |
| 6   | [`ao_autospawn_role_blind_dispatch_starvation_2026_07_14`](../archive/issues/ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md)       | —   | **Was FALSELY ARCHIVED** — `resolved` with 2 live bugs and no `superseded_by`. Headline fix (`8a423bb`) IS live; archival was right, only incomplete.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | ✅ **CLOSED 2026-07-16** — todos struck + forwarded to R1/R5; `superseded_by` added |
| 7   | [`empty_output_category_count_ssot_contradiction_2026_07_03`](../archive/issues/empty_output_category_count_ssot_contradiction_2026_07_03.md) | P2  | **Already fixed 2026-07-12** by `unified-trading-pm@4d42f50c2` (its own recommended option A). The doc's note claiming "NOT auto-applied" was wrong the day it was written.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | ✅ **ARCHIVED 2026-07-16** — zero work                                              |
| 8   | [`ao_recovery_audit_layer1_deleted_2026_07_15`](../archive/issues/ao_recovery_audit_layer1_deleted_2026_07_15.md)                             | P1  | Operator ruled **B (re-home the producer)** 2026-07-16. Consuming half of Layer-1 is live; only the producer is gone.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | **DEFERRED TO LAST** (operator)                                                     |
| 9   | [`ao_docs_reconciliation_2026_07_15`](../archive/2026_08/ao_docs_reconciliation_2026_07_15.md)                                                | P1  | Meta-tracker. Its own tracked `- [ ]` items reached zero (both were stale checkboxes vs. already-shipped commits) — archived 2026-08-04. The X1/F1 prose items it never itself tracked as todos are now **CLOSED** (re-verified 2026-08-06, `/plan-reconcile ao`): F1 (this epic's `assigned_vm`) is fixed to `NA` (see frontmatter line 32 + the "Known stale field" section above); X1's 6 named codex targets were independently re-checked and all read **CURRENT** — `canonical-plan-flow.md` (explicit 2026-07-23 correction banner), `agent-orchestrator-overview.md` (documents epic-VM removal + a "Host-offline failover" section correctly marked dormant-on-single-VM), `agent-orchestrator-backlog-state-alignment.md` (flags any `vm-*` value as a STALE multi-VM-era artifact), the worker-liveness doc (no "10/11 VMs" string), `runtime-deployment-topology.md` (`status: current`, no stale multi-VM strings), `agent-orchestrator-autospawn.md` (current skip-budget/spawn-budget docs). No open gap remains. | ✅ **ARCHIVED 2026-08-04**                                                          |

### AO-adjacent — verified NOT AO-runtime; do not pull into AO remediation

| #     | Issue doc                                                                                                                                   | Code verdict (2026-07-16)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Disposition                                                                                                                                                        |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 10-11 | `capability_wizard_analysis_findings_2026_06_11` + `capability_wizard_gap_discovery_2026_06_11`                                             | **OUT OF AO SCOPE — verified.** Of **41** open todos, exactly **one** touches `agent-orchestrator` (F40 `accounts.json` gitignore) and it is **already fixed** (`6385056`). The rest are UAC / strategy-service / execution-service / UI. The wizard is **alive and shipping today** (576-node manifest, commits landing 2026-07-16) — _not_ obsolete. But **~25 of 41 todos are already shipped and never checked off**: stale by **under-reporting**, the inverse of the expected failure.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | **Remove from AO scope.** Do NOT archive — the work is real. Needs its own reconciliation pass before anyone dispatches against it.                                |
| 12    | [`dp_alert_flood_triage_and_monitor_fixes_2026_06_23`](../archive/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md)             | 10/10 done verified. **🔴 NEW, live, undocumented: `uts-prod-tradfi-wave-launcher-cron` is `state: PAUSED` since `2026-06-24T22:44Z` (21 days), 0 `tradfi-bf-*` VMs running.** The OOM fix is real but **nothing has run to exercise it**. The doc's open todo #12 waits on a backfill that is not happening; the doc never mentions the pause. Its other open todo (stale-image risk) is **OBSOLETE** — `:latest` rebuilt today.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | **NOT AO SCOPE — data-pipeline owner (Ikenna) owns this.** Recorded because the sweep measured it; the AO remediation does not depend on it and must not chase it. |
| 13    | [`long_lived_vm_logs_not_backed_up_2026_07_02`](../active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md)                            | **STILL-OPEN and accurate** — nothing drifted. Explicitly operator-parked. Not AO-runtime relevant.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | leave parked                                                                                                                                                       |
| 14    | [`slot_venv_duplication_disk_pressure_2026_06_29`](../archive/issues/slot_venv_duplication_disk_pressure_2026_06_29.md)                     | ~~LIVE, RECURRING~~ **RESOLVED + ARCHIVED 2026-07-17** (remediated by `ao_host_disk_pressure_2026_07_16`: prune cron installed+fixed, guard cadence 2h proven on a live 83%→51% excursion, B2 shell gap closed cross-host `pm@86dea79d5`, stale 30G cache deleted — 18G measured freed). Original finding: **and a second independent cause of the operator's symptom.** Measured on the real orchestrator VM (`i-0c9b283b31d6b5ca7`) via SSM: disk cycles **65% → 95% every 6–18h**, self-healing via `vm-disk-guard.sh` each time, never durably below ~60%. Hardlink dedup IS working (inode links=81 confirmed). But the 2026-07-13 evidence — `OSError: could not create numbered dir ... after 10 tries` — is **a worker's pytest/QG dying mid-task, indistinguishable from "the agent gave up"**. Two "shipped" fixes measured NOT live: `crontab \| grep prune-uv` → **NONE_FOUND**; `qg-host-governor.sh --status` → **`MODE=token`**, not `reservation`. | → **separate infra plan**                                                                                                                                          |
| 15    | [`plan_hygiene_precommit_and_agentic_resolution_2026_06_10`](../archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md) | Verified 2026-07-16. Its 2026-06-12 audit findings are **STALE** — the daily Haiku GHA is green **10/10** and the Cloud Run sweep green **8/8**. Real gap: the deep `plan-reconciler` (the only layer that checks docs ↔ **CODE STATE**) is built, installer shipped, **never proven, never installed**; its proving dispatch was due 2026-06-17 (**~1 month overdue**). It runs **as an AO worker** → gated behind AO dispatch correctness.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | keep open — sequence **after** the AO fixes                                                                                                                        |
| 16    | [`issue_docs_remediation_sweep_2026_06_02`](../active/issues/issue_docs_remediation_sweep_2026_06_02.md)                                    | Verified: its `## agent-orchestrator` section is **2/2 DONE** (`ao@1fe3386`). All 12 open todos are **non-AO**.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | out of AO scope                                                                                                                                                    |

### Status/todo contradictions under the AO epic — ALL CLOSED 2026-07-16

All four were PM-QG hygiene sitting under the AO epic by `parent_epic`, not AO-runtime concerns. Every claimed fix was
code-verified before archival (not trusted):

| #   | Issue doc                                                              | Verdict                                                                                                                                                                | Disposition                                                                                                                   |
| --- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 17  | `qg_step_5_101_baseline_seed_undercount_unified_trading_pm_2026_07_08` | Named problem genuinely fixed (live re-run `[OK] unified-trading-pm: 319 == baseline`). Its 1 open todo was a **duplicate** of `mtds_empty_string_fallback…` Todo 3.   | ✅ **ARCHIVED** — duplicate struck + routed to the single owner; **the sweep it asked for was then actually run** (see below) |
| 18  | `qg_pytest_testpaths_excludes_scripts_quality_gates_2026_07_14`        | **ALL-FIXED**, 5/5 verified, live suite **255 passed**. Was `status: open` with **0 open todos** — a _false-open_ claim, the mirror image of the false-resolved class. | ✅ **FLIPPED + ARCHIVED**                                                                                                     |
| 19  | `prettier_emphasis_mangling_corpus_corruption_2026_07_14`              | **ALL-FIXED**, 3/3 verified, all 10 cited SHAs real, gate script live at 3 call sites.                                                                                 | ✅ **ARCHIVED**                                                                                                               |
| 20  | `qg_host_governor_severe_contention_2026_07_13`                        | **ALL-FIXED**, 4/4 verified + absorbed by a named successor plan. Done twice over.                                                                                     | ✅ **ARCHIVED**                                                                                                               |

**Side-effect of closing #17 — a real regression surfaced.** Its struck duplicate asked for a fleet-wide QG STEP 5.101
sweep "in one pass instead of discovering them one push at a time". **Nobody had run it in the 8 days since.** Run
2026-07-16 across 25 repos: 19 OK, 5 WARN (ratchet DOWN), and **1 FAIL — `agent-orchestrator` at 26 > baseline 25**
(`server/worker_liveness/_git_alerts.py:364`), meaning **AO's own `quality-gates.sh` is currently red for every push**,
in the very repo the remediation work is about to touch. Recorded as a P1 todo on the owning doc
[`mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08`](../archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md),
along with 5 unbanked DOWN-ratchets (incl. market-tick-data-service **199→62**, a 137-site improvement never banked —
unbanked headroom is exactly how `agent-orchestrator` reached 26 unnoticed).

### Known stale field in THIS epic — RESOLVED 2026-08-06 (was open under finding F1, `ao_docs_reconciliation_2026_07_15`)

Historical: this section originally flagged that this epic's own frontmatter still declared
`assigned_vm: vm-orchestrator` — a pre-2026-06-27 multi-VM host id retired by the single-VM pivot — tracked as X1/F1 in
`ao_docs_reconciliation_2026_07_15` and deliberately **not** silently fixed here, so that doc stayed the single audit
trail. Two corrections landed since: `vm-orchestrator` → `planning` (2026-07-16, the F1 fix), then `planning` → `NA`
(2026-08-06, operator ruling during `/plan-reconcile ao`, generalising the 2026-08-02 § 2e ruling on
`plan_reconcile_parked_operator_decisions_2026_08_02.md` — `NA` is the expected value on every current epic per
`PLAN_FORMAT.md`; see line 32). No open gap remains — this section is kept only as the historical pointer for
`ao_docs_reconciliation_2026_07_15`'s audit trail, not as a live to-do.

## Assigned active plans

_31 active plans declare `parent_epic: orchestrator_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`ao_open_issues_consolidated_close_out_2026_07_17`](../active/ao_open_issues_consolidated_close_out_2026_07_17.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: infra)

## P1 — important; post-current-gate

### [`ao_satellite_ao_dispatch_batch10_finalize_2026_08_09`](../active/ao_satellite_ao_dispatch_batch10_finalize_2026_08_09.md)

**status**: active · **estimate**: 0.32 cal AI-days (class: infra) **title**: AO satellite AO batch 10 — finalize

### [`ao_satellite_ao_dispatch_batch12_finalize_2026_08_09`](../active/ao_satellite_ao_dispatch_batch12_finalize_2026_08_09.md)

**status**: active · **estimate**: 0.4 cal AI-days (class: infra) **title**: AO satellite AO batch 12 — finalize

### [`ao_satellite_ao_dispatch_batch19_2026_08_10`](../active/ao_satellite_ao_dispatch_batch19_2026_08_10.md)

**status**: active · **estimate**: 0.32 cal AI-days (class: infra) **title**: AO satellite AO batch 19 —
dispatch-ordering unpark + TmuxPruner

### [`ao_satellite_ao_dispatch_batch19_finalize_2026_08_10`](../active/ao_satellite_ao_dispatch_batch19_finalize_2026_08_10.md)

**status**: active · **estimate**: 0.16 cal AI-days (class: infra) **title**: AO satellite AO batch 19 — finalize

### [`ao_satellite_ao_dispatch_batch2_2026_07_30`](../active/ao_satellite_ao_dispatch_batch2_2026_07_30.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: refactor) **title**: AO satellite AO batch 2 — second
dispatch batch extracted from the AO tranche's satellite docs

### [`ao_satellite_ao_dispatch_batch2_finalize_2026_07_30`](../active/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md)

**status**: active · **estimate**: 0.4 cal AI-days (class: infra) **title**: AO satellite AO batch 2 — finalize

### [`ao_satellite_ao_dispatch_batch3_2026_07_31`](../active/ao_satellite_ao_dispatch_batch3_2026_07_31.md)

**status**: active · **estimate**: 1.4 cal AI-days (class: refactor) **title**: AO satellite AO batch 3 — third dispatch
batch extracted from the AO tranche's satellite docs

### [`ao_satellite_ao_dispatch_batch3_finalize_2026_07_31`](../active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md)

**status**: active · **estimate**: 0.4 cal AI-days (class: infra) **title**: AO satellite AO batch 3 — finalize

### [`ao_satellite_ao_dispatch_batch5_2026_08_03`](../active/ao_satellite_ao_dispatch_batch5_2026_08_03.md)

**status**: active · **estimate**: 1.4 cal AI-days (class: refactor) **title**: AO satellite AO batch 5 — fifth dispatch
batch extracted from the AO tranche's satellite docs

### [`ao_satellite_ao_dispatch_batch5_finalize_2026_08_03`](../active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md)

**status**: active · **estimate**: 0.4 cal AI-days (class: infra) **title**: AO satellite AO batch 5 — finalize

### [`ao_satellite_ao_dispatch_batch6_2026_08_04`](../archive/2026_08/ao_satellite_ao_dispatch_batch6_2026_08_04.md)

**status**: active · **estimate**: 1.4 cal AI-days (class: refactor) **title**: AO satellite AO batch 6 — sixth dispatch
batch extracted from the AO tranche's satellite docs

### [`ao_satellite_ao_dispatch_batch6_finalize_2026_08_04`](../archive/2026_08/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md)

**status**: active · **estimate**: 0.4 cal AI-days (class: infra) **title**: AO satellite AO batch 6 — finalize

### [`ao_satellite_ao_dispatch_batch7_2026_08_06`](../active/ao_satellite_ao_dispatch_batch7_2026_08_06.md)

**status**: active · **estimate**: 0.48 cal AI-days (class: refactor) **title**: AO satellite AO batch 7 — seventh
dispatch batch extracted from the AO tranche's satellite docs

### [`ao_satellite_ao_dispatch_batch7_finalize_2026_08_06`](../active/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md)

**status**: active · **estimate**: 0.32 cal AI-days (class: infra) **title**: AO satellite AO batch 7 — finalize

### [`ao_satellite_ao_dispatch_batch8_2026_08_08`](../active/ao_satellite_ao_dispatch_batch8_2026_08_08.md)

**status**: active · **estimate**: 1.68 cal AI-days (class: research) **title**: AO satellite AO batch 8 — eighth
dispatch batch extracted from the AO tranche's satellite docs

### [`ao_satellite_ao_dispatch_batch8_finalize_2026_08_08`](../active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md)

**status**: active · **estimate**: 0.32 cal AI-days (class: infra) **title**: AO satellite AO batch 8 — finalize

### [`ao_satellite_ao_dispatch_batch9_2026_08_08`](../active/ao_satellite_ao_dispatch_batch9_2026_08_08.md)

**status**: active · **estimate**: 0.12 cal AI-days (class: refactor) **title**: AO satellite AO batch 9 — ninth
dispatch batch, one gate-clearance finding from batch6-finalize's re-check

### [`ao_satellite_ao_dispatch_batch9_finalize_2026_08_08`](../active/ao_satellite_ao_dispatch_batch9_finalize_2026_08_08.md)

**status**: active · **estimate**: 0.08 cal AI-days (class: infra) **title**: AO satellite AO batch 9 — finalize

### [`content_derived_backlog_task_ids_2026_08_08`](../active/content_derived_backlog_task_ids_2026_08_08.md)

**status**: active · **estimate**: 1.6 cal AI-days (class: refactor)

### [`deepseek_claude_blended_provider_routing_2026_07_28`](../active/deepseek_claude_blended_provider_routing_2026_07_28.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: DeepSeek/Claude blended provider routing
for agent-orchestrator

### [`review_agent_evidence_gated_write_capability_2026_08_09`](../active/review_agent_evidence_gated_write_capability_2026_08_09.md)

**status**: active · **estimate**: 0.6 cal AI-days (class: design) **title**: Review agent gets evidence-gated write
capability — revert false-done claims + patch small fixes

## P2 — useful; opportunistic

### [`ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize_2026_08_08`](../active/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08_finalize_2026_08_08.md)

**status**: active · **estimate**: 0.16 cal AI-days (class: refactor) **title**: audit-false-done 14 false-done rows +
1,013 unresolved plan_refs — finalize

### [`ao_satellite_ao_dispatch_batch10_2026_08_09`](../archive/2026_08/ao_satellite_ao_dispatch_batch10_2026_08_09.md)

**status**: active · **estimate**: 1.6 cal AI-days (class: infra) **title**: AO satellite AO batch 10 — 6 bounded items
extracted from 3 non-qualifying `ao`-tranche NA docs

### [`ao_satellite_ao_dispatch_batch12_2026_08_09`](../active/ao_satellite_ao_dispatch_batch12_2026_08_09.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: AO satellite AO batch 12 — 11 bounded items
extracted from 4 non-covered `ao`-tranche docs (orchestrator_master)

### [`ao_satellite_ao_dispatch_batch14_2026_08_09`](../active/ao_satellite_ao_dispatch_batch14_2026_08_09.md)

**status**: active · **estimate**: 0.4 cal AI-days (class: infra) **title**: AO satellite AO batch 14 — re-source
ANTHROPIC_AUTH_TOKEN from the now-live GSM secret (orchestrator_master epic)

### [`ao_satellite_ao_dispatch_batch14_finalize_2026_08_09`](../active/ao_satellite_ao_dispatch_batch14_finalize_2026_08_09.md)

**status**: active · **estimate**: 0.24 cal AI-days (class: infra) **title**: AO satellite AO batch 14 — finalize

### [`ao_satellite_ao_dispatch_batch4_finalize_2026_08_01`](../active/ao_satellite_ao_dispatch_batch4_finalize_2026_08_01.md)

**status**: active · **estimate**: 0.24 cal AI-days (class: infra) **title**: AO satellite AO batch 4 — finalize

### [`ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09`](../active/ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: AO scheduled-jobs review-gate backlog
drain + cross-job sharding/health audit

### [`content_derived_backlog_task_ids_2026_08_08_finalize`](../active/content_derived_backlog_task_ids_2026_08_08_finalize.md)

**status**: active · **estimate**: 0.2 cal AI-days (class: refactor) **title**: Content-derived backlog task ids — gated
finalize (verify the migration actually held, then archive)

### [`deepseek_flash_ab_routing_test_2026_08_05`](../active/deepseek_flash_ab_routing_test_2026_08_05.md)

**status**: active · **estimate**: 0.8 cal AI-days (class: infra) **title**: DeepSeek flash-vs-pro A/B routing test —
cost, throughput, and completion-quality comparison

### [`quality_gates_quickmerge_timing_baseline_2026_07_31`](../active/quality_gates_quickmerge_timing_baseline_2026_07_31.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: research) **title**: quality-gates.sh / quickmerge.sh timing
baseline (PM repo) — single-host vs planning-vm

### [`quality_gates_quickmerge_timing_baseline_2026_07_31_finalize_2026_08_08`](../active/quality_gates_quickmerge_timing_baseline_2026_07_31_finalize_2026_08_08.md)

**status**: active · **estimate**: 0.32 cal AI-days (class: infra) **title**: quality-gates.sh / quickmerge.sh timing
baseline — finalize

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
