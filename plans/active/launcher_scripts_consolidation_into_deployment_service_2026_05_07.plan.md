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

## Tab 11 audit + top-10 selection (2026-05-08)

Audit summary (Tab 11, `launcher-consolidation-tab`, 2026-05-08): cross-checked all 30 ad-hoc
launchers against the canonical `deployment-service/scripts/vm/` inventory + the
`_SERVICE_LAUNCHER_SCRIPTS` registry in `deployment-api/deployment_api/services/deploy_missing.py`.

**Critical finding** (case-2, adjacent to plan): three entries registered in `_SERVICE_LAUNCHER_SCRIPTS`
do NOT exist on disk under `deployment-service/scripts/vm/`. Deploy-Missing UI button is silently
broken for those services — the operator clicks Deploy-Missing, the API resolves the path, and the
copy-to-clipboard widget produces a `bash deployment-service/scripts/vm/launch-X.sh ...` invocation
that fails when the operator runs it. Missing on disk: `launch-mtds-backfill-vm.sh` (registered
line 63), `launch-instruments-backfill-vm.sh` (line 65), `launch-features-onchain-backfill-vm.sh`
(line 66). Tab 11 fills the first two via this cycle's migrations; `launch-features-onchain-backfill-vm.sh`
needs a fresh build (no e2e-testing equivalent), deferred to a follow-up tab.

**Top 10 selection** — ordered by impact for the 2026-05-23 live-DeFi deadline. HIGH priority items
fill missing-on-disk registry gaps + critical-path active flows; MEDIUM are DeFi launchers needed for
the May-23 archetypes; LOW are deferred (duplicates of canonical or post-May-23 scope):

| # | Source path | Destination | Priority | Rationale |
|---|-------------|-------------|----------|-----------|
| 1 | `e2e-testing/scripts/common/launch_mtds_category_backfill_vm.sh` | `deployment-service/scripts/vm/launch-mtds-backfill-vm.sh` | HIGH | Fills `_SERVICE_LAUNCHER_SCRIPTS` line 63 (Deploy-Missing for `market-tick-data-service`). |
| 2 | `e2e-testing/scripts/common/launch_instruments_backfill_vms.sh` | `deployment-service/scripts/vm/launch-instruments-backfill-vm.sh` | HIGH | Fills `_SERVICE_LAUNCHER_SCRIPTS` line 65 (Deploy-Missing for `instruments-service`). |
| 3 | `features-sports-service/scripts/launch_parallel_backfill.sh` | `deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh` | HIGH | Plan body explicitly names this destination (line 219). |
| 4 | `e2e-testing/scripts/sports/launch_mtds_backfill_vm.sh` | `deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh` | HIGH | Sports critical-path; distinct from #1 (sports odds-API specific, vs. generic CeFi/DeFi/TradFi). |
| 5 | `e2e-testing/scripts/sports/launch_instruments_reference_v3.sh` | `deployment-service/scripts/vm/launch-sports-instruments-reference-vm.sh` | HIGH | Sports reference-data critical-path; v3 supersedes the v1/v2 launchers (those flagged LOW). |
| 6 | `e2e-testing/scripts/defi/launch_dex_pools_vm.sh` | `deployment-service/scripts/vm/launch-mtds-dex-pools-backfill-vm.sh` | MEDIUM | DeFi pipeline May-23; no canonical equivalent. |
| 7 | `e2e-testing/scripts/defi/launch_eigenlayer_rewards_vm.sh` | `deployment-service/scripts/vm/launch-mtds-eigenlayer-rewards-backfill-vm.sh` | MEDIUM | DeFi pipeline May-23; no canonical equivalent. |
| 8 | `e2e-testing/scripts/defi/launch_solana_drift_vm.sh` | `deployment-service/scripts/vm/launch-mtds-solana-drift-backfill-vm.sh` | MEDIUM | DeFi/Solana pipeline May-23; no canonical equivalent (Solana now needed for Pyth integration). |
| 9 | `e2e-testing/scripts/common/launch_cefi_migration_vm.sh` | `deployment-service/scripts/vm/launch-cefi-migration-vm.sh` | MEDIUM | CeFi-specific migration; complements existing `launch-canonical-migration-vm.sh`. |
| 10 | `e2e-testing/scripts/common/launch_defi_backfill_vm.sh` | `deployment-service/scripts/vm/launch-defi-backfill-vm.sh` | MEDIUM | Generic DeFi backfill driver; no canonical equivalent. |

**Deferred to follow-up tabs** (LOW or collision-risk):

- `launch_gas_fees_vm.sh` / `launch_gas_fees_fleet.sh` — duplicates of canonical `launch-mtds-gas-fees-backfill-vm.sh`.
- `launch_lst_rates_vm.sh` — duplicate of canonical `launch-mtds-lst-rates-backfill-vm.sh`.
- `launch_lending_indices_vm.sh` — duplicate of canonical `launch-mtds-lending-indices-backfill-vm.sh`. **Tab 9 (`lending-indices-relaunch-tab`) in flight** — defer to avoid collision.
- `launch_perp_funding_vm.sh` — duplicate; canonical `mtds-perp-funding-` prefix already in watchdog.
- `launch_solana_gas_vm.sh` / `launch_liquidations_vm.sh` — defer post-May-23.
- `launch_prediction_backfill_vm.sh` / `launch_prediction_features_vm.sh` / `launch_prediction_pipeline_vm.sh` / `setup-backfill-vm.sh` — **Tab 10 (`predictions-phase1-ingestion-tab`) in flight on prediction surface** — defer to avoid collision.
- `full_api_football_sweep.sh` / `full_sports_entity_sweep.sh` — orchestrators that wrap other launchers; defer.
- `launch_fss_features_v3.sh` / `launch_fss_features_vm.sh` / `launch_fss_phase3_backfill.sh` — partially superseded by canonical `launch-features-sports-backfill-vm.sh`; reconcile in follow-up.
- `launch_instruments_reference_vm.sh` — superseded by the v3 form (#5 above).
- `launch_mdps_phase3_bucketing.sh` / `launch_mdps_reprocess_vm.sh` — partially superseded by canonical `launch-mdps-sports-bucket-vm.sh`; reconcile in follow-up.
- `launch_oddspapi_vm_backfill.sh` — odds API specific; defer post-May-23.
- `deployment-service/scripts/deploy-dashboard-gce-vm.sh` — intra-repo move (not in e2e-testing list); defer.

**Migration shape adopted** (mechanical scope per Tab 11 brief):

1. **Copy** the source script content into the canonical destination (the source repo retains the file
   for the deprecation banner; deletion ships in a follow-up cycle).
2. **Rename** to canonical `launch-{asset_group}-{flavor}-{vm,backfill,etc}.sh` form.
3. **Add a deprecation banner** to the OLD location (top of file, comment block) pointing at the new
   path. Keep the old body intact — operators with terminals open on the old path get a clear redirect
   on next invocation.
4. **Update `VM_PREFIX_TO_BUCKET`** in `deployment-service/scripts/vm/vm_zombie_watchdog.py` for any
   new VM-name prefix introduced (kept identical to source where possible to preserve in-flight VM
   compatibility).
5. **Register in `_SERVICE_LAUNCHER_SCRIPTS`** in `deploy_missing.py` if the launcher targets a service
   that should be reachable from the Deploy-Missing UI button (#1, #2 directly, others as appropriate).
6. **Smoke-test `--dry-run`** for any launcher that supports it; for those without `--dry-run`, syntax
   check only (`bash -n`).
7. **Watchdog VM relaunch** at the end of the cycle (single relaunch covers all dict edits).

Out-of-scope for Tab 11 (reserved for follow-up cycles): rewriting launchers to use the canonical
`setup-data-pipeline-vm.sh` metadata-routing pattern (current ad-hoc launchers embed full startup
scripts via `metadata-from-file`, which is functionally equivalent but not the SSOT shape — that
refactor is mechanical-but-larger and doesn't affect Deploy-Missing UI registry coverage).

## Phase-by-phase tasks

### Phase 0 — Per-script audit (sequential, no QG gate)

- [x] [audit] P0. For each of the 29 scripts: open the file, identify the launcher's invariants
      (`gcloud compute instances create` flags, env vars set, payload), and decide
      whether to keep, rename, or merge with an existing
      `deployment-service/scripts/vm/launch-*.sh`. Some are duplicates of already-in-place scripts (e.g.
      `e2e-testing/scripts/sports/launch_mtds_backfill_vm.sh` vs the canonical
      `deployment-service/scripts/vm/launch-mtds-backfill-vm.sh`). (Tab 11 audit + top-10 table above; 20
      of 30 deferred to follow-up cycles per LOW priority + collision-avoidance rules.)
- [ ] [audit] P0. Document the rename mapping in
      `unified-trading-pm/codex/05-infrastructure/launcher-script-consolidation-2026-05-07.md`. Each row:
      old path → new path → action (move / merge / delete).

### Phase 1 — Migrate scripts in waves

- [x] [deployment-service] P0. Wave A (4 scripts): `e2e-testing/scripts/common/` → `deployment-service/scripts/vm/`.
      (Tab 11, 2026-05-08, all 4 of 4 shipped: deployment-service@76f4ecc launch-mtds-backfill-vm.sh,
      deployment-service@fbb3673 launch-instruments-backfill-vm.sh, deployment-service@ce99d43 launch-cefi-migration-vm.sh
      + launch-defi-backfill-vm.sh.)
- [ ] [deployment-service] P0. Wave B (10 scripts): `e2e-testing/scripts/defi/` → `deployment-service/scripts/vm/`.
      Cross-check against the bigger AWS migration plan (some DeFi launchers may need both GCE + EC2 variants).
      **PARTIAL** (3 of 10 shipped Tab 11, 2026-05-08): deployment-service@5778811
      (launch-mtds-{dex-pools,eigenlayer-rewards,solana-drift}-backfill-vm.sh). Remaining 7 deferred to
      follow-up cycles per the audit table at the top of this plan body — most are duplicates of canonical
      launch-mtds-* scripts already in deployment-service/scripts/vm/.
- [ ] [deployment-service] P0. Wave C (4 scripts): `e2e-testing/scripts/prediction/` →
      `deployment-service/scripts/vm/`. **DEFERRED** (Tab 10 `predictions-phase1-ingestion-tab` in flight on the
      prediction surface; held for collision-avoidance per Tab 11 audit table).
- [ ] [deployment-service] P0. Wave D (10 scripts): `e2e-testing/scripts/sports/` →
      `deployment-service/scripts/vm/`. Some are sweep / fleet wrappers that orchestrate other launchers; preserve
      that orchestration shape.
      **PARTIAL** (2 of 10 shipped Tab 11, 2026-05-08): deployment-service@2e1d967 launch-mtds-sports-odds-backfill-vm.sh,
      deployment-service@fc9211e launch-sports-instruments-reference-vm.sh.
- [x] [deployment-service] P0. Wave E (1 script): `features-sports-service/scripts/launch_parallel_backfill.sh` →
      `deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh`.
      (Tab 11, 2026-05-08, deployment-service@0215086.)
- [ ] [e2e-testing / features-sports-service] P0. Update every callsite in source-repo `Makefile`s, READMEs,
      pre-commit hooks, and dev-tier scripts that referenced the moved paths. **DEFERRED** to follow-up cycle —
      Tab 11 left deprecation banners on every moved file (per CLAUDE.md plan-body) but did not chase down
      Makefile / README references; safe because the old files still work as redirects.
- [ ] [deployment-service] P0. Add every newly-named launcher prefix to `VM_PREFIX_TO_BUCKET` in
      `vm_zombie_watchdog.py`. **Relaunch the watchdog VM** after the dict edit (see CLAUDE.md "VM Naming
      Convention").
      **PARTIAL** (Tab 11 added 17 new prefix entries across migrations #1-10 + relaunched watchdog VM
      `vm-zombie-watchdog-20260508-121344` — covers the 10 launchers shipped this cycle. Remaining prefixes
      land alongside their launchers in follow-up cycles.)

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

## DONE-2026-05-08 — Tab 11 cycle (10 of 30 launchers shipped)

Tab 11 (`launcher-consolidation-tab`) shipped 10 launcher migrations from `e2e-testing/scripts/` +
`features-sports-service/scripts/` → `deployment-service/scripts/vm/` plus all supporting infrastructure
edits (VM_PREFIX_TO_BUCKET registry, source-location deprecation banners, helper-script lifts).

**Critical-path impact**: 2 of 3 missing-on-disk `_SERVICE_LAUNCHER_SCRIPTS` registry entries are now backed
by real launcher scripts (`market-tick-data-service` + `instruments-service`); Deploy-Missing UI button no
longer silently breaks for those services. The third missing entry (`features-onchain-service` →
`launch-features-onchain-backfill-vm.sh`) has no e2e-testing equivalent and needs a fresh build in a
follow-up cycle.

**Code commits** (all pushed to `live-defi-rollout` per zero-incoming conditional):

* deployment-service@76f4ecc — #1 launch-mtds-backfill-vm.sh + vm_mtds_backfill.sh + 5 watchdog prefixes
  (mtds-backfill-{cefi/tradfi/defi/prediction/sports}-).
* e2e-testing@8daba1a — #1 deprecation banner on launch_mtds_category_backfill_vm.sh.
* deployment-service@fbb3673 — #2 launch-instruments-backfill-vm.sh + vm_instruments_backfill.sh + 4 watchdog
  prefixes (instr-backfill-cefi-/instr-backfill-defi/tradfi/sports).
* e2e-testing@2da6867 — #2 deprecation banner on launch_instruments_backfill_vms.sh.
* deployment-service@0215086 — #3 launch-features-sports-parallel-backfill-vm.sh + watchdog prefix
  (fss-backfill-vm-).
* features-sports-service@06f6b30 — #3 deprecation banner on launch_parallel_backfill.sh.
* deployment-service@2e1d967 — #4 launch-mtds-sports-odds-backfill-vm.sh + watchdog prefix
  (mtds-backfill-odds-).
* e2e-testing@deff088 — #4 deprecation banner on sports/launch_mtds_backfill_vm.sh.
* deployment-service@fc9211e — #5 launch-sports-instruments-reference-vm.sh + vm_instruments_reference.sh +
  watchdog prefix (sports-ref-v3-).
* e2e-testing@db7ace3 — #5 deprecation banner on sports/launch_instruments_reference_v3.sh.
* deployment-service@5778811 — #6-8 launch-mtds-{dex-pools,eigenlayer-rewards,solana-drift}-backfill-vm.sh +
  3 watchdog prefixes (mtds-dex-pools-backfill, mtds-eigenlayer-rewards-backfill, mtds-solana-drift-backfill).
* e2e-testing@43d8e49 — #6-8 deprecation banners on 3 DeFi launchers.
* deployment-service@ce99d43 — #9-10 launch-{cefi-migration,defi-backfill}-vm.sh + watchdog prefix
  (mtds-migrate-, heartbeat-only).
* e2e-testing@4f1f92b — #9-10 deprecation banners on 2 common launchers.
* PM@fc35b11 — Tab 11 audit + top-10 selection (Phase 0 flip).
* PM (this commit) — Phase 1 partial flips + DONE-2026-05-08 block.

**Watchdog VM**: relaunched as `vm-zombie-watchdog-20260508-121344` after all 17 new prefix entries landed —
running watchdog only loads VM_PREFIX_TO_BUCKET at boot.

**Deploy-Missing registry status** (`_SERVICE_LAUNCHER_SCRIPTS` audit at Tab 11 closeout):

| Service slug | Registry path | On-disk status |
|--------------|---------------|----------------|
| market-tick-data-service | launch-mtds-backfill-vm.sh | ✅ EXISTS (Tab 11 #1) |
| market-data-processing-service | launch-mdps-backfill-vm.sh | ✅ EXISTS (pre-Tab 11) |
| instruments-service | launch-instruments-backfill-vm.sh | ✅ EXISTS (Tab 11 #2) |
| features-onchain-service | launch-features-onchain-backfill-vm.sh | ❌ MISSING (deferred) |
| features-delta-one-service | launch-features-backfill-vm.sh | ✅ EXISTS (pre-Tab 11) |
| features-volatility-service | launch-features-backfill-vm.sh | ✅ EXISTS (pre-Tab 11) |
| features-cross-instrument-service | launch-features-backfill-vm.sh | ✅ EXISTS (pre-Tab 11) |
| features-sports-service | launch-features-backfill-vm.sh | ✅ EXISTS (pre-Tab 11) |
| features-calendar-service | launch-features-backfill-vm.sh | ✅ EXISTS (pre-Tab 11) |

**Smoke-test coverage**: every migrated launcher with a `--dry-run` flag was smoke-tested (`#1, #2, #3, #4,
#5, #6, #7, #8, #10`). #9 (cefi-migration) has no `--dry-run`; passed `bash -n` syntax check only.

**QG status (deployment-service Pass 1)**: pre-existing failures only — bandit B108 in
`deployment_service/vm/heartbeat_cli.py:176` (semver-rollout[bot]@6f3476b7, 2026-05-01) and STEP 5.10 cloud-SDK
import in `scripts/vm/vm_zombie_watchdog.py:72` (semver-rollout[bot]@fb73d5a0, 2026-05-05). Both pre-date
Tab 11; exempt under the 2026-05-07 → 2026-05-09 QG-failure-on-others'-code window per CLAUDE.md.

**Deferred (not in this cycle, by priority)**:

- 2 of 3 missing-on-disk registry entries filled (#1, #2). Third (`launch-features-onchain-backfill-vm.sh`)
  needs a fresh build — no e2e-testing equivalent. Files an issue doc as P1 follow-up if not picked up
  organically.
- 7 DeFi launchers (gas-fees / lending-indices / lst-rates / perp-funding / solana-gas / liquidations) — most
  are duplicates of existing canonical `launch-mtds-{X}-backfill-vm.sh`; reconcile in a delete-vs-merge
  follow-up rather than blind migrate.
- 4 prediction launchers — deferred to avoid collision with Tab 10 in flight on the prediction surface.
- 8 sports launchers (fss-features v1+v2+phase3, mdps-phase3-bucketing, mdps-reprocess, oddspapi-vm-backfill,
  full-sweep wrappers, instruments-reference-vm v1) — partially superseded by canonical equivalents;
  reconcile in follow-up.
- 1 intra-repo move (`deployment-service/scripts/deploy-dashboard-gce-vm.sh` → `scripts/vm/launch-dashboard-vm.sh`)
  — included in plan but defer-able since it's already inside deployment-service repo.
- Callsite-update sweep (Makefiles / READMEs / dev-tier scripts) — every moved launcher has a deprecation
  banner; old paths still work as redirects, so callsites keep functioning during the transition window.
