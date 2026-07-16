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
    ../active/agent_orchestrator_workers_on_vms_2026_05_19.md,
    ../archive/2026_05/agent_reliability_mitigations_2026_05_20.md,
    ../archive/2026_05/d0_orchestrator_migration_2026_05_20.md,
    ../active/issues/human_led_audit_pool_2026_05_21.md,
  ]
created: 2026-05-21
name: orchestrator_master
tier: L5
priority: P0
assigned_vm: vm-orchestrator
parent: master_to_live_defi_2026_05_23
co_operators: [harsh]
codex_ssots:
  [
    codex/11-project-management/epic-execution-with-sub-agents.md,
    codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
  ]
related_plans:
  - ../active/agent_orchestrator_alert_channel_cleanup_2026_07_13.md
  - ../active/master_to_live_defi_2026_05_23.md
last_updated: 2026-07-12
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
> `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (see also the workspace `CLAUDE.md` system-map
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

| Codex SSOT                                                                                                                                     | Owns                                                                                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`codex/12-agent-workflow/orchestrator-multi-vm-topology.md`](../../codex/12-agent-workflow/orchestrator-multi-vm-topology.md)                 | VM shapes (epic VM + planning VM) + Plan→VM assignment + Registry + Per-VM backend + Backlog auto-gen + Dashboard aggregation + Persistence + VM provisioning |
| [`codex/12-agent-workflow/orchestrator-safety-mechanisms.md`](../../codex/12-agent-workflow/orchestrator-safety-mechanisms.md)                 | Stuck-agent detection + auto-respawn + Auth failover (non-blocking) + Telegram alerts framework + Git staleness ping + Fresh-spawn dirty-commit               |
| [`codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md`](../../codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md) | r3 auth architecture (long-lived `setup-token` via `CLAUDE_CODE_OAUTH_TOKEN`); supersedes the `.credentials.json` swap that caused the 2026-05-21 cascade     |

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
[`codex/12-agent-workflow/orchestrator-multi-vm-topology.md`](../../codex/12-agent-workflow/orchestrator-multi-vm-topology.md).
Implementation work is owned by the assigned active plans below. Status as of 2026-05-21:

| Phase      | Scope                                                                                                                                                                                                                                                                                                                                                                                                                            | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Owned by active plan                                                                             |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 0          | Prerequisites (OAuth auto-refresh + per-account creds swap + Telegram alert framework)                                                                                                                                                                                                                                                                                                                                           | ✅ DONE (agent-orch@4eabf5c + @2de9410); one operator action remaining                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | `d0_orchestrator_migration_2026_05_20`                                                           |
| 1          | Registry yaml + `assigned_vm:` frontmatter + regen script + CLAUDE.md update                                                                                                                                                                                                                                                                                                                                                     | ✅ DONE (PM@e3f11893; updated to v2 2026-05-21)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `d0_orchestrator_migration_2026_05_20`                                                           |
| 2          | Multi-VM dashboard (SPA `/` landing + `/api/vm/summary` endpoint + cross-VM cards + Firebase deploy)                                                                                                                                                                                                                                                                                                                             | ✅ DONE 2026-05-21 (agent-orch@c274059 + @f357132)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | `agent_orchestrator_cloud_run_deployment_2026_05_19`                                             |
| 3          | Safety mechanisms (stuck-detection + auto-respawn + dirty-commit + git-staleness alert)                                                                                                                                                                                                                                                                                                                                          | ✅ DONE 2026-05-21 (agent-orch@72b4b0a)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | `agent_reliability_mitigations_2026_05_20` + `agent_orchestrator_slack_notifications_2026_05_19` |
| 4a         | Spawn path → env-var auth (r3) (`oauth_token_env_file` + `tmux_spawn.py` refactor)                                                                                                                                                                                                                                                                                                                                               | ✅ DONE 2026-05-21 (agent-orch@d7b6ad6)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4b         | r3 env-file routing: roster on SSOT slugs (`sub-a-ikenna`/`sub-b-iggy2london`) + `AccountDef.operator`; spawn + `/usage` probe + `oauth_refresh` all bypass the legacy swap/refresh for any account with `oauth_token_env_file`. Legacy `.credentials.json` path retained for `harsh-primary` until its setup-token lands. Also fixed a silent poller `resets_at`-kwarg `TypeError` that was blocking per-account usage updates. | ✅ DONE 2026-05-21 (agent-orch@5d78133; deployed + env-file `/usage` probe verified: sub-a 8%/4%, sub-b 1%/8%)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4b-cleanup | Remove legacy code once `harsh-primary` migrates to a setup-token: delete `_swap_credentials_for`/`_restore_credentials`, disable `oauth_refresh.refresh()` auto-call, remove `.credentials.<id>.json` files + the `swap_claude_account.sh` reference. CLAUDE.md HARD RULE (no `.credentials.json` copy between machines).                                                                                                       | ✅ DONE 2026-05-28 (agent-orch@d883e41→@8c52691: dropped swap helpers + oauth_refresh + gcs_creds_poller modules + refresh-oauth/sync-from-gcs endpoints + OAuthBadge UI; tightened tmux_spawn/usage_tracker/spawn callers to require env_file; CLAUDE.md HARD RULE landed in PM)                                                                                                                                                                                                                                                                                                                                                                              | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 4c         | Dashboard repurpose (`SetupTokenBadge` shows 1-year expiry warn/crit/expired levels; `notify_setup_token_expiring` fires at ≤30d + ≤7d; `setup_token_expires_at` in accounts.json; all 3 r3 accounts seeded to 2027-05-21)                                                                                                                                                                                                       | ✅ DONE 2026-05-21 (agent-orch@tab/ikennaigboaka/1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 5          | Account roster expansion (operator runs `setup-token` per distinct subscription; verify-distinct-subscription test; GCS distribution)                                                                                                                                                                                                                                                                                            | ✅ DONE 2026-05-28 — All 4 accounts (3 Ikenna + 1 Harsh) have setup-tokens minted + env files distributed to both GCS (`central-element-323112-orchestrator-creds/accounts/`) and S3 (`uts-orchestrator-creds-427895769566/accounts/`), 206 bytes each, verified                                                                                                                                                                                                                                                                                                                                                                                               | `agent_orchestrator_per_spawn_account_isolation_2026_05_20`                                      |
| 6          | Backlog auto-gen from plans (`regen_backlog_from_plan.py` + plan-reload poll + CLAUDE.md hard rule)                                                                                                                                                                                                                                                                                                                              | ✅ DONE 2026-05-28 — `regen_backlog_from_plan.py` + `PlanRegenLoop` (6h cadence, fires within 60s of boot, env-tunable, `POST /api/backlog/regen` for manual) + 29-test suite (agent-orch@2a24c46); content-based dedup fixed an idempotency bug surfaced by the new tests; CLAUDE.md HARD RULE added                                                                                                                                                                                                                                                                                                                                                          | (formerly `agent_orchestrator_workers_on_vms_2026_05_19`, archived)                              |
| 7          | Planning VM provisioning (cloud-hosted; slot 1+2 only; registry symlink; landing-page wired)                                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-28 — Central API EC2 VM (`13.113.200.22`, AWS ap-northeast-1) serves as the planning VM (ikenna-vm role=planning in `backends.json`); cross-VM `/api/fleet/summary` fan-out + `Landing.tsx` cards live in dashboard (verified: HTTPS /health 200 + 12 backends registered); planning VM bootstrap items shipped under archived `epic_vm_fleet_commissioning_2026_05_21`                                                                                                                                                                                                                                                                        | (formerly `agent_orchestrator_workers_on_vms_2026_05_19`, archived)                              |
| 8          | Persistence (SQLite hot-backup → GCS every 6h via `SnapshotLoop`; restore script `scripts/restore_from_gcs.sh`)                                                                                                                                                                                                                                                                                                                  | ✅ DONE 2026-05-21 (agent-orch@tab/ikennaigboaka/1; KMS-encrypted creds pending)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | `agent_orchestrator_dual_deployment_2026_05_19`                                                  |
| 9          | VM provisioning (packer/docker pipeline; immutable image; `bootstrap_vm.sh`; <5min cold-start)                                                                                                                                                                                                                                                                                                                                   | ✅ DONE 2026-05-28 — Packer HCL2 template + provisioner scripts (`deployment-service/packer/agent-orchestrator/`); `bootstrap_vm.sh` detects `/etc/orchestrator-ami-version` marker + rsyncs warm repos + venv from `/opt/orchestrator-warm/` (Steps 1+2+4.5 skipped on prebaked path); `launch-epic-vm-aws.sh` accepts `AMI_ID` env-var override; README + codex DNS-cutover SSOT shipped. Operator runs `packer build` to bake, then `AMI_ID=… launch-epic-vm-aws.sh` to use                                                                                                                                                                                 | (formerly `agent_orchestrator_dual_deployment_2026_05_19`, archived)                             |
| 10         | Review agent role (`agents/review.md` boot prompt; commit-poll logic; auto-merge happy-path)                                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-21 (`agents/review.md` shipped; agent-orch@tab/ikennaigboaka/1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `agent_orchestrator_workers_on_vms_2026_05_19`                                                   |
| 11         | Rollout to 9 epic VMs (provision via Phase 9 pipeline; DNS A records; cut over current single-VM to vm-defi)                                                                                                                                                                                                                                                                                                                     | ✅ DONE 2026-05-28 — Fleet of 10 epic VMs already running (commissioned 2026-05-22→23 via `aws_epic_vm_fleet_2026_05_22`); cut over from single-VM model superseded by central-API-VM-plus-fleet topology (current `backends.json` shows 12 backends, all live); EIP allocation script shipped (`deployment-service/scripts/aws/allocate-orchestrator-eips.sh`) + DNS cutover recipe codified ([agent-orchestrator-dns-cutover.md](../../codex/05-infrastructure/agent-orchestrator-dns-cutover.md)). Operator runs EIP script + adds A records to complete cutover when convenient (not blocking; current ops work fine on dynamic IPs via central API proxy) | (formerly `agent_orchestrator_cloud_run_deployment_2026_05_19`, archived)                        |
| 12         | Cleanup + docs (archive superseded plans; codex SSOTs landed; CLAUDE.md System-First Architecture pointer)                                                                                                                                                                                                                                                                                                                       | ✅ DONE 2026-05-21 — codex SSOTs landed, plans archived (hygiene sweep), CLAUDE.md System-First Architecture pointer already accurate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `d0_orchestrator_migration_2026_05_20`                                                           |

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

### Core AO runtime (the "make AO work properly" scope)

| #   | Issue doc                                                                                                                                    | P   | status                                        | open todos              | Code verdict                                                                                                 |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------- | --- | --------------------------------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------ |
| 1   | [`ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07`](../active/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md)           | P0  | open                                          | 3                       | _verification in flight_                                                                                     |
| 2   | [`ao_skip_blind_spawn_budget_phantom_churn_2026_07_15`](../active/issues/ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md)             | P1  | open                                          | 3                       | _verification in flight_                                                                                     |
| 3   | [`ao_dispatch_residuals_2026_07_15`](../active/issues/ao_dispatch_residuals_2026_07_15.md)                                                   | P1  | open                                          | prose R1–R7             | _verification in flight_                                                                                     |
| 4   | [`ao_operator_message_silent_drop_no_reply_ack_2026_07_08`](../active/issues/ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md)     | P1  | open                                          | 1 (+10 done, re-verify) | _verification in flight_                                                                                     |
| 5   | [`dispatcher_role_eligibility_gap_review_slots_2026_07_13`](../active/issues/dispatcher_role_eligibility_gap_review_slots_2026_07_13.md)     | P2  | open                                          | 2                       | _verification in flight_                                                                                     |
| 6   | ⚠️ [`ao_autospawn_role_blind_dispatch_starvation_2026_07_14`](../archive/issues/ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md)   | —   | **ARCHIVED yet `resolved` with 2 OPEN todos** | 2                       | _verification in flight — archival itself under test_                                                        |
| 7   | [`empty_output_category_count_ssot_contradiction_2026_07_03`](../active/issues/empty_output_category_count_ssot_contradiction_2026_07_03.md) | P2  | open                                          | 1                       | _verification in flight_                                                                                     |
| 8   | [`ao_recovery_audit_layer1_deleted_2026_07_15`](../active/issues/ao_recovery_audit_layer1_deleted_2026_07_15.md)                             | P1  | open                                          | rewire tracker          | **DEFERRED TO LAST** — operator ruled B (re-home producer) 2026-07-16                                        |
| 9   | [`ao_docs_reconciliation_2026_07_15`](../active/issues/ao_docs_reconciliation_2026_07_15.md)                                                 | P1  | open                                          | meta-tracker            | remaining: X1 codex single-VM sweep + F1 (this epic's own `assigned_vm: vm-orchestrator` — stale, see below) |

### AO-adjacent (same repo or AO epic; verify relevance before spending on them)

| #   | Issue doc                                                                                                                                  | P   | status             | open todos | Code verdict                                                                                                         |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------ | --- | ------------------ | ---------- | -------------------------------------------------------------------------------------------------------------------- |
| 10  | [`capability_wizard_analysis_findings_2026_06_11`](../active/issues/capability_wizard_analysis_findings_2026_06_11.md)                     | P2  | open               | 11         | _verification in flight — 5wk old, OBSOLETE is a live possibility_                                                   |
| 11  | [`capability_wizard_gap_discovery_2026_06_11`](../active/issues/capability_wizard_gap_discovery_2026_06_11.md)                             | P2  | open               | 30         | _verification in flight — 5wk old, OBSOLETE is a live possibility_                                                   |
| 12  | [`dp_alert_flood_triage_and_monitor_fixes_2026_06_23`](../active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md)             | P1  | open               | 2          | _verification in flight_                                                                                             |
| 13  | [`long_lived_vm_logs_not_backed_up_2026_07_02`](../active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md)                           | —   | parked             | 3          | _verification in flight_                                                                                             |
| 14  | [`slot_venv_duplication_disk_pressure_2026_06_29`](../active/issues/slot_venv_duplication_disk_pressure_2026_06_29.md)                     | —   | open (`locked_by`) | 1          | _verification in flight — 2026-07-13 recurrence: 2.0 MB free mid-QG_                                                 |
| 15  | [`plan_hygiene_precommit_and_agentic_resolution_2026_06_10`](../active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md) | P2  | open               | 3          | **VERIFIED 2026-07-16 (see Progress Log)** — keystone = prove the `plan-reconciler` (dispatch ~1mo overdue)          |
| 16  | [`issue_docs_remediation_sweep_2026_06_02`](../active/issues/issue_docs_remediation_sweep_2026_06_02.md)                                   | P1  | open               | 12         | **VERIFIED 2026-07-16** — its `## agent-orchestrator` section is 2/2 DONE (ao@1fe3386); all 12 open todos are non-AO |

### Status/todo contradictions under the AO epic (PM-QG hygiene, not AO runtime)

| #   | Issue doc                                                                                                                                                             | P   | contradiction                                  | Code verdict             |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- | ---------------------------------------------- | ------------------------ |
| 17  | ⚠️ [`qg_step_5_101_baseline_seed_undercount_unified_trading_pm_2026_07_08`](../active/issues/qg_step_5_101_baseline_seed_undercount_unified_trading_pm_2026_07_08.md) | P3  | `status: resolved` **but 1 open todo**         | _verification in flight_ |
| 18  | ⚠️ [`qg_pytest_testpaths_excludes_scripts_quality_gates_2026_07_14`](../active/issues/qg_pytest_testpaths_excludes_scripts_quality_gates_2026_07_14.md)               | P3  | `status: open` **but 0 open todos, 5 done**    | _verification in flight_ |
| 19  | ⚠️ [`prettier_emphasis_mangling_corpus_corruption_2026_07_14`](../active/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md)                           | P1  | `resolved` + 0 open **but still in `active/`** | _verification in flight_ |
| 20  | ⚠️ [`qg_host_governor_severe_contention_2026_07_13`](../active/issues/qg_host_governor_severe_contention_2026_07_13.md)                                               | P2  | `resolved` + 0 open **but still in `active/`** | _verification in flight_ |

### Known stale field in THIS epic (finding F1, `ao_docs_reconciliation_2026_07_15`)

This epic's own frontmatter still declares `assigned_vm: vm-orchestrator` — a pre-2026-06-27 multi-VM host id retired by
the single-VM pivot. Valid values are `{planning, NA}` only. The sibling `agent_operating_framework_master` already
carries the corrected `assigned_vm: planning` (+ an inline note recording the same class of fix). Repointing this one is
tracked as X1/F1 in `ao_docs_reconciliation_2026_07_15` — **not** silently fixed here, so the reconciliation doc stays
the single audit trail.

## Assigned active plans

_2 active plans declare `parent_epic: orchestrator_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md)

**status**: active · **estimate**: 3.6 cal AI-days (class: design) **title**: May-23 Cutover Master — Live DeFi Trading
by 2026-05-23

## P1 — important; post-current-gate

### [`agent_orchestrator_alert_channel_cleanup_2026_07_13`](../active/agent_orchestrator_alert_channel_cleanup_2026_07_13.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra)

## P2 — useful; opportunistic

_(no plans currently assigned at this priority)_

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
