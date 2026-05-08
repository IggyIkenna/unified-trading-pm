---
title: "VM launcher + Cloud Run consolidation audit — 30 ad-hoc launchers + 3 Cloud Run deploys to migrate"
created: 2026-05-08
author: ikenna-tab1-main
source:
  - cursor-configs/CLAUDE.md § "VM launcher script SSOT (codified 2026-05-07)"
  - cursor-configs/CLAUDE.md § "VM Naming Convention"
  - plans/ai/launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md (referenced in CLAUDE.md but
    pending execution)
  - workspace-wide grep for `gcloud compute instances create` + `gcloud run deploy` + `aws ec2 run-instances`
    (2026-05-08 14:45 UTC, Tab 1 audit)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# VM-launcher + Cloud Run consolidation audit

> **Severity**: P1 — operator-direction 2026-05-08 ("migrate the service/scripts which deploy anything to
> deployment-service/scripts; for e2e-testing just have wrapper scripts that wrap deployment-service scripts IF they
> are launching VMs; want VM + Cloud Run stuff in one place"). **Blast radius**: every script in the workspace that
> launches GCE VMs OR deploys Cloud Run services. **Suggested owner**: defi_master / Tab 1 (next session) +
> Tab 5 (governance) cross-handshake.

## Audit results (2026-05-08 14:45 UTC)

Workspace-wide grep `gcloud compute instances create | gcloud run deploy | aws ec2 run-instances | gcloud builds submit`:

### Tier A — `deployment-service/scripts/vm/` (canonical home; 53 scripts)

These are CORRECT. No migration needed. Examples: `launch-mtds-{lst-rates,lending-indices,gas-fees,vault,prediction,...}-backfill-vm.sh`,
`launch-{cefi,defi,tradfi,prediction,sports}-{backfill,forward-poll,migration,instruments-backfill,...}.sh`,
`launch-mdps-{backfill,sharded-backfill,sports-bucket}-vm.sh`, `launch-features-{backfill,sports-backfill,sports-parallel-backfill}-vm.sh`,
`launch-{sfi,footystats,api-football,understat,transfermarkt,openmeteo}-{backfill,forward-poll}-vm.sh`,
`launch-vm-zombie-watchdog.sh`, `launch-manifest-consolidator-vm.sh`, etc.

### Tier B — pending migration (CLAUDE.md "Migration in flight 2026-05-07" — 30 scripts)

#### B.1 — `e2e-testing/scripts/common/` (4 launchers)

| Script | Action | Maps to deployment-service equivalent |
|--------|--------|---------------------------------------|
| `launch_cefi_migration_vm.sh` | Replace with wrapper | `deployment-service/scripts/vm/launch-cefi-migration-vm.sh` (exists) |
| `launch_defi_backfill_vm.sh` | Replace with wrapper | `deployment-service/scripts/vm/launch-defi-backfill-vm.sh` (exists) |
| `launch_instruments_backfill_vms.sh` | Replace with wrapper | `deployment-service/scripts/vm/launch-instruments-backfill-vm.sh` (exists) |
| `launch_mtds_category_backfill_vm.sh` | Replace with wrapper | `deployment-service/scripts/vm/launch-mtds-backfill-vm.sh` (exists; canonical asset_group entry-point) |

#### B.2 — `e2e-testing/scripts/defi/` (10 launchers)

| Script | Action | Maps to deployment-service equivalent |
|--------|--------|---------------------------------------|
| `launch_dex_pools_vm.sh` | Replace with wrapper | `launch-mtds-dex-pools-backfill-vm.sh` (exists) |
| `launch_eigenlayer_rewards_vm.sh` | Replace with wrapper | `launch-mtds-eigenlayer-rewards-backfill-vm.sh` (exists) |
| `launch_gas_fees_fleet.sh` | Migrate fleet-launcher | `launch-mtds-gas-fees-backfill-vm.sh` (per-VM exists; fleet wrapper needed) |
| `launch_gas_fees_vm.sh` | Replace with wrapper | `launch-mtds-gas-fees-backfill-vm.sh` (exists) |
| `launch_lending_indices_vm.sh` | Replace with wrapper | `launch-mtds-lending-indices-backfill-vm.sh` (exists) |
| `launch_liquidations_vm.sh` | Migrate (no equivalent yet) | NEW: `launch-mtds-liquidations-backfill-vm.sh` |
| `launch_lst_rates_vm.sh` | Replace with wrapper | `launch-mtds-lst-rates-backfill-vm.sh` (exists) |
| `launch_perp_funding_vm.sh` | Migrate (no equivalent) | NEW: `launch-mtds-perp-funding-backfill-vm.sh` |
| `launch_solana_drift_vm.sh` | Replace with wrapper | `launch-mtds-solana-drift-backfill-vm.sh` (exists) |
| `launch_solana_gas_vm.sh` | Migrate or merge | Merge into `launch-mtds-gas-fees-backfill-vm.sh` if same shape, else NEW |

#### B.3 — `e2e-testing/scripts/prediction/` (4 launchers)

| Script | Action |
|--------|--------|
| `launch_prediction_backfill_vm.sh` | Replace with wrapper → `launch-mtds-prediction-backfill-vm.sh` |
| `launch_prediction_features_vm.sh` | Migrate (no equivalent) → NEW |
| `launch_prediction_pipeline_vm.sh` | Migrate (orchestrator-style, may need re-design) |
| `setup-backfill-vm.sh` | Audit if it actually launches a VM or just configures |

#### B.4 — `e2e-testing/scripts/sports/` (10 launchers)

| Script | Action |
|--------|--------|
| `launch_fss_features_v3.sh` | Replace with wrapper → `launch-features-sports-backfill-vm.sh` |
| `launch_fss_features_vm.sh` | Replace with wrapper |
| `launch_fss_phase3_backfill.sh` | Migrate or merge |
| `launch_instruments_reference_v3.sh` | Replace with wrapper → `launch-sports-instruments-reference-vm.sh` |
| `launch_instruments_reference_vm.sh` | Replace with wrapper |
| `launch_mdps_phase3_bucketing.sh` | Migrate or merge |
| `launch_mdps_reprocess_vm.sh` | Replace with wrapper → `launch-mdps-sports-bucket-vm.sh` |
| `launch_mtds_backfill_vm.sh` | Replace with wrapper → `launch-mtds-sports-odds-backfill-vm.sh` |
| `full_api_football_sweep.sh` | Audit — likely orchestrator (calls multiple VMs) |
| `full_sports_entity_sweep.sh` | Audit — likely orchestrator |

#### B.5 — Other repos (3 launchers)

| Script | Action |
|--------|--------|
| `features-sports-service/scripts/launch_parallel_backfill.sh` | Replace with wrapper → `launch-features-sports-parallel-backfill-vm.sh` (exists) |
| `deployment-service/scripts/deploy-dashboard-gce-vm.sh` | **Move into** `deployment-service/scripts/vm/launch-dashboard-vm.sh` (intra-repo migration; remove from non-vm/ subdir) |
| `e2e-testing/scripts/prediction/setup-backfill-vm.sh` | Audit |

### Tier C — Cloud Run deploys (3 scripts; NOT in deployment-service/scripts/)

| Script | What it does | Action |
|--------|--------------|--------|
| `unified-trading-pm/scripts/dev/deploy-shared-cloudrun.sh` | Deploy shared Cloud Run services | **Move to** `deployment-service/scripts/cloud-run/deploy-shared.sh` |
| `unified-trading-pm/scripts/deployment/canary-deploy.sh` | Cloud Run canary | **Move to** `deployment-service/scripts/cloud-run/canary-deploy.sh` |
| `unified-trading-system-ui/scripts/deploy-cloud-run.sh` | UI Cloud Run deploy | **Move to** `deployment-service/scripts/cloud-run/deploy-ui.sh` (or keep in repo + add wrapper) |

### Tier D — Audit-only (false positives + library-internal scripts)

| Script | Why it grep'd |
|--------|---------------|
| `deployment-api/deployment_api/routes/*.py` | API routes that call OUT to launcher scripts (consumer, not launcher) |
| `deployment-service/scripts/bootstrap/bootstrap_gcp.sh` | One-off GCP project bootstrap; OK in current home |
| `unified-trading-pm/scripts/quality-gates-base/base-service.sh` | QG framework, OK in current home |
| `unified-trading-pm/scripts/propagation/add-cloudbuild-deploy-via-dispatch.py` | Workspace propagation tooling (PM lives elsewhere) |
| `deployment-ui/scripts/dev-tiers.sh` | Local dev tiers, NOT a deploy |
| `market-tick-data-service/.../migrate_mtds_defi_legacy_venue_underscore.py` | Local data migration, doesn't launch VMs |

## Consolidation pattern (the shape of every wrapper)

Every Tier B wrapper follows this 4-line shape (replaces the e2e-testing legacy script entirely):

```bash
#!/usr/bin/env bash
# Wrapper around canonical deployment-service launcher.
# Original e2e-testing-resident launcher migrated 2026-05-08 per
# CLAUDE.md "VM launcher script SSOT". Edits to this script must instead
# go to deployment-service/scripts/vm/<name>.sh — this wrapper is a
# 1-liner pass-through preserving operator workflow.
exec bash "$(dirname "$0")/../../../deployment-service/scripts/vm/<canonical-name>.sh" "$@"
```

This is the smallest possible migration:

- Preserves operator's existing `bash e2e-testing/scripts/...` muscle memory.
- Single SSOT for the actual launch logic (deployment-service).
- Wrapper scripts become trivial; no logic drift.
- Watchdog dict is registered ONCE in the canonical version.

## Why this matters

1. **Operator surface SSOT**: every launchable thing lives in `deployment-service/scripts/`. Searching the workspace
   for "what can I launch?" returns one directory. Today it returns 5+ directories.
2. **No-drift invariant**: when a launcher changes (env var, machine type, prefix), the change lands in ONE place.
   Today drift between e2e-testing duplicates + deployment-service canonical is undetected.
3. **VM_PREFIX_TO_BUCKET registration**: every canonical launcher in `deployment-service/scripts/vm/` SHOULD have its
   prefix registered in `vm_zombie_watchdog.py`. e2e-testing duplicates that emit different prefixes silently zombie.
4. **Cloud Run unification**: same SSOT story for Cloud Run deploys. Today they're scattered across 3+ repos.

## Recommended migration order (priority)

### Phase 1 — same-shape e2e-testing → deployment-service wrappers (~5 AI-days mechanical)

The 16 Tier B scripts that map cleanly to existing deployment-service equivalents. Each is a 4-line wrapper. Phase 1
is pure mechanical migration with zero logic risk.

### Phase 2 — Tier B scripts needing NEW deployment-service launchers (~3 AI-days)

The 8 Tier B scripts in defi/prediction/sports without existing equivalents. Each needs a real port to
deployment-service + watchdog dict + wrapper.

### Phase 3 — orchestrator scripts (~2 AI-days)

`full_api_football_sweep.sh`, `full_sports_entity_sweep.sh`, `launch_gas_fees_fleet.sh`, `launch_prediction_pipeline_vm.sh`
— these orchestrate multiple VMs. Need re-design as deployment-service composite launchers (call N canonical sub-launchers).

### Phase 4 — Cloud Run deploys (~1 AI-day)

Move 3 Cloud Run deploy scripts to `deployment-service/scripts/cloud-run/` + wire workspace QG to verify imports.

### Phase 5 — intra-repo migration

`deployment-service/scripts/deploy-dashboard-gce-vm.sh` → `deployment-service/scripts/vm/launch-dashboard-vm.sh`.
Pure rename + path-update.

## Cross-references

- Plan: `plans/ai/launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md` (referenced in CLAUDE.md
  but not yet executed; promote to `plans/active/` when this audit is folded in).
- Sister governance issue: `runbook_execution_governance_gaps_2026_05_08.md` (the silent-rot issue this surfaced from).
- CLAUDE.md SSOTs: "VM launcher script SSOT (codified 2026-05-07)", "VM Naming Convention", "Singleton-locked
  launchers".

## Recommended decision

1. **Operator**: assign Phase 1 to next Tab 1 session (Phase 1 is pure mechanical, low-risk, high-leverage).
2. **Phase 1 SAMPLE shipped this session by Tab 1 main**: 4-5 representative wrappers (defi flavor) to demonstrate the
   pattern + verify the wrapper shape works end-to-end. Remaining Phase 1 tomorrow's split.
3. **Phase 2-5**: tomorrow's split as separate Tab assignments.
