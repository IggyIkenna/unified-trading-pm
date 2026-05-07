---
name: launcher_scripts_consolidation_into_deployment_service_2026_05_07
overview:
  Consolidate the 29 ad-hoc VM launcher scripts scattered across e2e-testing/ + features-sports-service/ into the
  deployment-service/scripts/vm/ SSOT, and audit deployment-api data-status / drilldown / deploy_missing services for
  GCS-only call sites that need the unified cloud storage facade. Premise: deployment-UI is the eventual SSOT for
  launching VMs; today's ad-hoc scripts exist because deployment-UI hasn't been mature.
type: code
epic: epic-deployment
completion_gates:
  code: C5
  deployment: D3
  business: none
repo_gates:
  - repo: deployment-service
    code: C2
    deployment: none
    business: none
  - repo: deployment-api
    code: C2
    deployment: none
    business: none
  - repo: deployment-ui
    code: C2
    deployment: none
    business: none
  - repo: e2e-testing
    code: C2
    deployment: none
    business: none
  - repo: features-sports-service
    code: C2
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C2
    deployment: none
    business: none
depends_on:
  - aws_migration_defi_first_2026_05_07.plan.md
related:
  - aws_migration_defi_first_2026_05_07.plan.md
  - data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md
  - deploy_missing_auto_launch_2026_05_07.plan.md
todos: []
isProject: false
---

# Launcher-script consolidation + deployment-api cloud-agnostic audit

## Why

Two related concerns from the user (2026-05-07):

1. The Deploy-Missing flow shipped in `data_status_drilldown_shard_atom_alignment_2026_05_07` Phase 3 references
   launcher scripts under `deployment-service/scripts/vm/` (e.g.
   `launch-mtds-backfill-vm.sh`). This is the right SSOT — the deployment-UI / deployment-api are converging on a
   single place that owns "how do we launch a VM."
2. **But** the workspace currently has **29 ad-hoc launcher scripts** outside `deployment-service/scripts/vm/`:

   ```
   e2e-testing/scripts/common/launch_cefi_migration_vm.sh
   e2e-testing/scripts/common/launch_defi_backfill_vm.sh
   e2e-testing/scripts/common/launch_instruments_backfill_vms.sh
   e2e-testing/scripts/common/launch_mtds_category_backfill_vm.sh
   e2e-testing/scripts/defi/launch_dex_pools_vm.sh
   e2e-testing/scripts/defi/launch_eigenlayer_rewards_vm.sh
   e2e-testing/scripts/defi/launch_gas_fees_fleet.sh
   e2e-testing/scripts/defi/launch_gas_fees_vm.sh
   e2e-testing/scripts/defi/launch_lending_indices_vm.sh
   e2e-testing/scripts/defi/launch_liquidations_vm.sh
   e2e-testing/scripts/defi/launch_lst_rates_vm.sh
   e2e-testing/scripts/defi/launch_perp_funding_vm.sh
   e2e-testing/scripts/defi/launch_solana_drift_vm.sh
   e2e-testing/scripts/defi/launch_solana_gas_vm.sh
   e2e-testing/scripts/prediction/launch_prediction_backfill_vm.sh
   e2e-testing/scripts/prediction/launch_prediction_features_vm.sh
   e2e-testing/scripts/prediction/launch_prediction_pipeline_vm.sh
   e2e-testing/scripts/prediction/setup-backfill-vm.sh
   e2e-testing/scripts/sports/full_api_football_sweep.sh
   e2e-testing/scripts/sports/full_sports_entity_sweep.sh
   e2e-testing/scripts/sports/launch_fss_features_v3.sh
   e2e-testing/scripts/sports/launch_fss_features_vm.sh
   e2e-testing/scripts/sports/launch_fss_phase3_backfill.sh
   e2e-testing/scripts/sports/launch_instruments_reference_v3.sh
   e2e-testing/scripts/sports/launch_instruments_reference_vm.sh
   e2e-testing/scripts/sports/launch_mdps_phase3_bucketing.sh
   e2e-testing/scripts/sports/launch_mdps_reprocess_vm.sh
   e2e-testing/scripts/sports/launch_mtds_backfill_vm.sh
   features-sports-service/scripts/launch_parallel_backfill.sh
   ```

   These exist because deployment-UI hasn't been mature enough to render every recovery flow. The Deploy-Missing
   button is the first production-grade flow that renders + emits launcher invocations from the UI; every script in
   the list above is a candidate for the same shape.

3. **deployment-api data-status / drilldown / deploy_missing services are GCS-only** (audit 2026-05-07):
   - `deployment_api/services/shard_detail.py` imports `google.cloud.storage` directly (3 sites).
   - `deployment_api/utils/storage_facade.py` is the GCS-only facade with FUSE optimization; no S3 path.
   - `deployment_api/services/data_status_hierarchical.py` reads `gs://...` URIs via `read_availability_index` — UTL
     does have an S3 code path, but the hierarchical builder hard-codes `gs://`.
   - `deployment_api/services/deploy_missing.py` references `deployment-service/scripts/vm/` paths with no AWS-
     equivalent.
   The bigger AWS bucket parity / S3 client work is already in
   [`aws_migration_defi_first_2026_05_07.plan.md`](aws_migration_defi_first_2026_05_07.plan.md); this plan
   doesn't duplicate it. Instead this plan (a) documents the deployment-api-specific call sites that need the
   unified facade; (b) enumerates the launcher-script migration; (c) tracks the deployment-UI AWS/GCP toggle
   hookup verification.

## Pre-audit blast radius

**Launcher-script migration** (29 scripts):

| Source repo | Scripts | Destination |
|-------------|---------|-------------|
| `e2e-testing/scripts/common/` | 4 | `deployment-service/scripts/vm/` (rename via `launch-*.sh`) |
| `e2e-testing/scripts/defi/` | 10 | `deployment-service/scripts/vm/` |
| `e2e-testing/scripts/prediction/` | 4 | `deployment-service/scripts/vm/` |
| `e2e-testing/scripts/sports/` | 10 | `deployment-service/scripts/vm/` |
| `features-sports-service/scripts/launch_parallel_backfill.sh` | 1 | `deployment-service/scripts/vm/` |
| `deployment-service/scripts/deploy-dashboard-gce-vm.sh` | 1 | `deployment-service/scripts/vm/launch-dashboard-vm.sh` (intra-repo move; rename to match SSOT pattern) |
| **Total** | **30** | |

**Local scripts that are NOT VM launchers** (no migration; verified 2026-05-07 broad scan):

* `instruments-service/scripts/local_*.sh`, `run_vm_backfill_e2e.sh`, `sports_chunked_backfill.sh`,
  `rebuild_all_asset_groups.sh` — local-process orchestration. Some `bash`-exec launchers from
  `deployment-service/scripts/vm/`; that's correct.
* `market-tick-data-service/scripts/*.py` — Python migration / reconciliation scripts that run in the
  caller's shell, no VM creation.
* `market-data-processing-service/scripts/*.py` — same.
* `features-*-service/scripts/setup.sh` + `smoke_matrix.py` — local dev / test scaffolding.
* `ml-training-service` / `ml-inference-service` / `strategy-service` / `execution-service` /
  `position-balance-monitor-service` / `risk-and-exposure-service` / `alerting-service` `scripts/setup.sh` —
  install-only, no VM launches.
* `features-sports-service/scripts/run_backfill.sh` — local orchestration that exec's
  `launch_parallel_backfill.sh` (which DOES launch VMs and is in the migration list above).

For each script:
1. Read its current shape — many were written before the workspace conventions
   (`MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=<unique-tag>`, `RUN_TS="$(date +%Y%m%d-%H%M%S)"`,
   `VM_PREFIX_TO_BUCKET` registry) landed.
2. Rename to follow the `launch-{asset_group}-{flavor}-{ts}.sh` pattern from the existing
   `deployment-service/scripts/vm/` SSOT.
3. Move to `deployment-service/scripts/vm/`.
4. Update the source-repo callsites to invoke the new path
   (`bash deployment-service/scripts/vm/launch-X.sh ...` rather than the moved-from path).
5. Add the launcher to the `_SERVICE_LAUNCHER_SCRIPTS` registry in
   `deployment-api/deployment_api/services/deploy_missing.py` so the Deploy-Missing flow can target the script
   from the UI.
6. Register the VM-name prefix in `VM_PREFIX_TO_BUCKET` in
   `deployment-service/scripts/vm/vm_zombie_watchdog.py` per the workspace rule (ref CLAUDE.md "VM Naming Convention").

**deployment-api data-status / drilldown / deploy_missing audit** (this plan only documents; remediation rolls into
`aws_migration_defi_first_2026_05_07.plan.md`):

| File | GCS-only call site | Refactor target |
|------|-------------------|-----------------|
| `deployment_api/services/shard_detail.py:775` | `from google.cloud import storage` | UCI `StorageClient` (already cloud-agnostic) |
| `deployment_api/services/shard_detail.py:1116` | `from google.cloud import storage as _gcs` | UCI `StorageClient` |
| `deployment_api/services/data_status_hierarchical.py:261` | `gs://{bucket}/_index/availability_index.parquet` | Build the URI via `unified_cloud_interface.canonical_storage_uri(bucket, path)` |
| `deployment_api/utils/storage_facade.py` | GCS FUSE + GCS API | Add S3 fallback path that reads from `${HOME}/.aws/credentials` / IRSA |
| `deployment_api/utils/cloud_storage_client.py` | `s3://` recognised but no S3 client wired | Wire `boto3.client("s3")` for AWS path |
| `deployment_api/services/deploy_missing.py` | All launcher paths under `deployment-service/scripts/vm/` (script files don't exist for AWS yet) | Add per-cloud routing — `launch-mtds-backfill-vm.sh` for GCP, `launch-mtds-backfill-ec2.sh` for AWS |

## Phased execution DAG

```
Phase 0 (audit)            Phase 1 (script-by-script migration)
─────────────────          ────────────────────────────────────
Per-script shape audit  →  Move 29 scripts to
+ rename mapping           deployment-service/scripts/vm/
                           Update source callsites
                           Update VM_PREFIX_TO_BUCKET
                                    ↓
                           Phase 2 (deployment-api registry)
                           ────────────────────────────────────
                           Add migrated launchers to
                           _SERVICE_LAUNCHER_SCRIPTS in
                           deploy_missing.py so Deploy-Missing
                           can target each from the UI
                                    ↓
                           Phase 3 (UI cloud-toggle verification)
                           ─────────────────────────────────────
                           Audit AWS/GCP toggle wiring; document
                           which surfaces are still GCS-only
                           (rolls findings into the existing
                           aws_migration_defi_first plan)
                                    ↓
                           Phase 4 (codex docs + plan close)
                           ─────────────────────────────────
```

## Phase-by-phase tasks

### Phase 0 — Per-script audit (sequential, no QG gate)

- [ ] [audit] P0. For each of the 29 scripts: open the file, identify the launcher's invariants
      (`gcloud compute instances create` flags, env vars set, payload), and decide
      whether to keep, rename, or merge with an existing
      `deployment-service/scripts/vm/launch-*.sh`. Some are duplicates of already-in-place scripts (e.g.
      `e2e-testing/scripts/sports/launch_mtds_backfill_vm.sh` vs the canonical
      `deployment-service/scripts/vm/launch-mtds-backfill-vm.sh`).
- [ ] [audit] P0. Document the rename mapping in
      `unified-trading-pm/codex/05-infrastructure/launcher-script-consolidation-2026-05-07.md`. Each row:
      old path → new path → action (move / merge / delete).

### Phase 1 — Migrate scripts in waves

- [ ] [deployment-service] P0. Wave A (4 scripts): `e2e-testing/scripts/common/` → `deployment-service/scripts/vm/`.
- [ ] [deployment-service] P0. Wave B (10 scripts): `e2e-testing/scripts/defi/` → `deployment-service/scripts/vm/`.
      Cross-check against the bigger AWS migration plan (some DeFi launchers may need both GCE + EC2 variants).
- [ ] [deployment-service] P0. Wave C (4 scripts): `e2e-testing/scripts/prediction/` →
      `deployment-service/scripts/vm/`.
- [ ] [deployment-service] P0. Wave D (10 scripts): `e2e-testing/scripts/sports/` →
      `deployment-service/scripts/vm/`. Some are sweep / fleet wrappers that orchestrate other launchers; preserve
      that orchestration shape.
- [ ] [deployment-service] P0. Wave E (1 script): `features-sports-service/scripts/launch_parallel_backfill.sh` →
      `deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh`.
- [ ] [e2e-testing / features-sports-service] P0. Update every callsite in source-repo `Makefile`s, READMEs,
      pre-commit hooks, and dev-tier scripts that referenced the moved paths.
- [ ] [deployment-service] P0. Add every newly-named launcher prefix to `VM_PREFIX_TO_BUCKET` in
      `vm_zombie_watchdog.py`. **Relaunch the watchdog VM** after the dict edit (see CLAUDE.md "VM Naming
      Convention").

### Phase 2 — deployment-api launcher registry

- [ ] [deployment-api] P0. Extend `_SERVICE_LAUNCHER_SCRIPTS` in `deploy_missing.py` so every newly-migrated
      script is reachable from the Deploy-Missing UI button. This unblocks the operator workflow: any leaf in the
      hierarchical drill-down can deploy-missing without falling back to "manual recovery" placeholders.
- [ ] [deployment-api] P0. Unit-test coverage: assert every script registered in `_SERVICE_LAUNCHER_SCRIPTS`
      exists on disk under `deployment-service/scripts/vm/` (pre-flight catches typos before a panic-time
      deploy-missing click).

### Phase 3 — UI cloud-toggle audit (rolls findings into aws_migration plan)

- [ ] [audit] P1. Walk the AWS/GCP toggle in `deployment-ui/src/contexts/CloudProviderContext.tsx`. Today it
      switches the API base URL between port 8004 (GCP backend) and 8005 (AWS backend). Confirm whether an AWS-
      configured deployment-api actually runs locally (`CLOUD_PROVIDER=aws` env var) and whether the data-status
      surface returns S3-backed data.
- [ ] [audit] P1. Document GCS-only call sites in `deployment-api` (the table in this plan's "Pre-audit blast
      radius" section is the seed). Roll findings into
      `aws_migration_defi_first_2026_05_07.plan.md` Phase N (the existing plan tracks the bigger S3-client work).

### Phase 4 — Codex docs + plan close

- [ ] [unified-trading-pm] P2. New codex doc
      `codex/05-infrastructure/launcher-script-consolidation-2026-05-07.md` documenting the consolidated launcher
      registry as the workspace SSOT. Add a "deployment-UI is the SSOT for launching VMs" principle to
      `codex/05-infrastructure/vm-tarball-deployment.md`.
- [ ] [unified-trading-pm] P2. Plan flip closeout once Phases 0-3 ship + workspace-wide grep confirms no
      remaining `gcloud compute instances create` outside `deployment-service/scripts/vm/`.

## Success criteria

- **Code gates:** `bash scripts/quality-gates.sh` passes on deployment-service + deployment-api + e2e-testing +
  features-sports-service.
- **Inventory gate:**
  `find . -type f -name "*.sh" -not -path "*/deployment-service/scripts/vm/*" | xargs grep -l "gcloud compute instances create" | grep -v deployment-service`
  returns zero matches at plan closeout.
- **Registry gate:** Deploy-Missing UI button works for every (service, asset_group) pair declared in the codex
  shard-axis matrix — i.e. `_SERVICE_LAUNCHER_SCRIPTS` covers the full set + every script exists on disk.
- **VM-naming gate:** every newly-migrated launcher's VM prefix is in `VM_PREFIX_TO_BUCKET`.

## Temporary states + their canonical follow-up plans

- Until this plan ships, the Deploy-Missing UI button degrades to the existing
  9-service `_SERVICE_LAUNCHER_SCRIPTS` registry; leaves whose service isn't registered fall back to "no launcher
  registered" error. Operators can still copy + run any of the 29 ad-hoc scripts manually.
- The deployment-api GCS-only call sites are explicitly NOT remediated by this plan — that's
  `aws_migration_defi_first_2026_05_07.plan.md`'s territory. This plan only **documents** them so the bigger plan
  has a complete inventory.

## Out of scope

- Auto-launch (API directly invokes gcloud / aws ec2 run-instances) — see
  `deploy_missing_auto_launch_2026_05_07.plan.md`.
- Bigger S3 bucket parity / ECR / CodeBuild work — see `aws_migration_defi_first_2026_05_07.plan.md`.
- Tarball-from-local mode for the migrated launchers — already shipped in this session
  (`data_status_drilldown_shard_atom_alignment_2026_05_07` Phase 3 follow-up; the mode is per-launcher-script-
  agnostic so newly-migrated scripts inherit it for free).

## References

- `aws_migration_defi_first_2026_05_07.plan.md` — bigger S3 / ECR / EC2 launcher work.
- `data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md` — Deploy-Missing flow that consumes the
  launcher registry.
- `deploy_missing_auto_launch_2026_05_07.plan.md` — preview-mode → auto-launch successor.
- CLAUDE.md "VM Naming Convention" — registers prefixes in `VM_PREFIX_TO_BUCKET`.
- CLAUDE.md "VM tarball deployment" — `create-code-tarballs.sh --all` + boot path.
