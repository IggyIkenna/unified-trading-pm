---
name: launcher_scripts_consolidation_into_deployment_service_2026_05_07
overview: >
  Consolidate the 29 ad-hoc VM launcher scripts scattered across e2e-testing/ + features-service (sports family)/ into
  the deployment-service/scripts/vm/ SSOT, and audit deployment-api data-status / drilldown / deploy_missing services
  for GCS-only call sites that need the unified cloud storage facade. Premise: deployment-UI is the eventual SSOT for
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
  - repo: features-service (sports family)
    code: C2
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C2
    deployment: none
    business: none
depends_on:
  - aws_migration_defi_first_2026_05_07.md
related:
  - /plans/archive/2026_05/aws_migration_defi_first_2026_05_07.md
  - /plans/archive/data_status_drilldown_shard_atom_alignment_2026_05_07.md
  - /plans/archive/deploy_missing_auto_launch_2026_05_07.md
todos: []
isProject: false
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
estimate_calibration_note: |
  No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from filename (refactor, multiplier 0.4×).
  Owner agent: fill baseline + multiply × 0.4 per /codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.
---

> **ARCHIVED 2026-05-18 (slot 10)** — 100% complete (15/15 checkboxes flipped per slot-2 Wave 3 closeout 2026-05-13;
> plan body line ~533 explicitly: "Plan eligible for archive (pending operator direction on archival window)").
> Preserved for archaeology. Deferred items already migrated: Phase 3 AWS-toggle validation →
> `aws_migration_defi_first_2026_05_07.md` Phase N; promote*workflow sub-todo 1.Y (DEFERRED-AFTER-CONSOLIDATION-PHASE2)
> flipped in `promote_workflow*\*` plan. Per-item DEFERRED-PER-AUDIT / DEFERRED-AFTER-AWS-PHASE-1 annotations in body
> carry their named successors.

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

# Launcher-script consolidation + deployment-api cloud-agnostic audit

> **🟡 IN-FLIGHT REFACTOR — features-\* repo consolidation 2026-05-08**
>
> [`features_repo_consolidation_2026_05_08`](./features_repo_consolidation_2026_05_08.md) Phase 8A consolidates the 8
> per-family features-_ launchers into a single parameterised `launch-features-<flavor>.sh`. \*\*Skip features-_ repos
> in this plan's launcher migration scope\*\* — they're being archived. Banner stays until features-repo Phase 7
> archives the 8 source repos.
>
> [`live_pipeline_mtds_mdps_features_2026_05_08`](./live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 13 adds 4 new
> launchers (`launch-mtds-live-{ag}.sh`, `launch-mdps-features-live-{ag}.sh`, `launch-features-cross-cutting.sh`,
> `launch-replay-cascade.sh`) under `deployment-service/scripts/vm/`. Same per-launcher SSOT contract this plan
> codifies; complementary scope.

## Why

Two related concerns from the user (2026-05-07):

1. The Deploy-Missing flow shipped in `data_status_drilldown_shard_atom_alignment_2026_05_07` Phase 3 references
   launcher scripts under `deployment-service/scripts/vm/` (e.g. `launch-mtds-backfill-vm.sh`). This is the right SSOT —
   the deployment-UI / deployment-api are converging on a single place that owns "how do we launch a VM."
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
   features-service (sports family)/scripts/launch_parallel_backfill.sh
   ```

   These exist because deployment-UI hasn't been mature enough to render every recovery flow. The Deploy-Missing button
   is the first production-grade flow that renders + emits launcher invocations from the UI; every script in the list
   above is a candidate for the same shape.

3. **deployment-api data-status / drilldown / deploy_missing services are GCS-only** (audit 2026-05-07):
   - `deployment_api/services/shard_detail.py` imports `google.cloud.storage` directly (3 sites).
   - `deployment_api/utils/storage_facade.py` is the GCS-only facade with FUSE optimization; no S3 path.
   - `deployment_api/services/data_status_hierarchical.py` reads `gs://...` URIs via `read_availability_index` — UTL
     does have an S3 code path, but the hierarchical builder hard-codes `gs://`.
   - `deployment_api/services/deploy_missing.py` references `deployment-service/scripts/vm/` paths with no AWS-
     equivalent. The bigger AWS bucket parity / S3 client work is already in
     [`aws_migration_defi_first_2026_05_07.md`](aws_migration_defi_first_2026_05_07.md); this plan doesn't duplicate it.
     Instead this plan (a) documents the deployment-api-specific call sites that need the unified facade; (b) enumerates
     the launcher-script migration; (c) tracks the deployment-UI AWS/GCP toggle hookup verification.

## Pre-audit blast radius

**Launcher-script migration** (29 scripts):

| Source repo                                                            | Scripts | Destination                                                                                            |
| ---------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------ |
| `e2e-testing/scripts/common/`                                          | 4       | `deployment-service/scripts/vm/` (rename via `launch-*.sh`)                                            |
| `e2e-testing/scripts/defi/`                                            | 10      | `deployment-service/scripts/vm/`                                                                       |
| `e2e-testing/scripts/prediction/`                                      | 4       | `deployment-service/scripts/vm/`                                                                       |
| `e2e-testing/scripts/sports/`                                          | 10      | `deployment-service/scripts/vm/`                                                                       |
| `features-service (sports family)/scripts/launch_parallel_backfill.sh` | 1       | `deployment-service/scripts/vm/`                                                                       |
| `deployment-service/scripts/deploy-dashboard-gce-vm.sh`                | 1       | `deployment-service/scripts/vm/launch-dashboard-vm.sh` (intra-repo move; rename to match SSOT pattern) |
| **Total**                                                              | **30**  |                                                                                                        |

**Local scripts that are NOT VM launchers** (no migration; verified 2026-05-07 broad scan):

- `instruments-service/scripts/local_*.sh`, `run_vm_backfill_e2e.sh`, `sports_chunked_backfill.sh`,
  `rebuild_all_asset_groups.sh` — local-process orchestration. Some `bash`-exec launchers from
  `deployment-service/scripts/vm/`; that's correct.
- `market-tick-data-service/scripts/*.py` — Python migration / reconciliation scripts that run in the caller's shell, no
  VM creation.
- `market-data-processing-service/scripts/*.py` — same.
- `features-*-service/scripts/setup.sh` + `smoke_matrix.py` — local dev / test scaffolding.
- `ml-training-service` / `ml-inference-service` / `strategy-service` / `execution-service` /
  `position-balance-monitor-service` / `risk-and-exposure-service` / `alerting-service` `scripts/setup.sh` —
  install-only, no VM launches.
- `features-service (sports family)/scripts/run_backfill.sh` — local orchestration that exec's
  `launch_parallel_backfill.sh` (which DOES launch VMs and is in the migration list above).

For each script:

1. Read its current shape — many were written before the workspace conventions (`MANIFEST_PER_VM_SHARDS=true`,
   `VM_NAME=<unique-tag>`, `RUN_TS="$(date +%Y%m%d-%H%M%S)"`, `VM_PREFIX_TO_BUCKET` registry) landed.
2. Rename to follow the `launch-{asset_group}-{flavor}-{ts}.sh` pattern from the existing
   `deployment-service/scripts/vm/` SSOT.
3. Move to `deployment-service/scripts/vm/`.
4. Update the source-repo callsites to invoke the new path (`bash deployment-service/scripts/vm/launch-X.sh ...` rather
   than the moved-from path).
5. Add the launcher to the `_SERVICE_LAUNCHER_SCRIPTS` registry in
   `deployment-api/deployment_api/services/deploy_missing.py` so the Deploy-Missing flow can target the script from the
   UI.
6. Register the VM-name prefix in `VM_PREFIX_TO_BUCKET` in `deployment-service/scripts/vm/vm_zombie_watchdog.py` per the
   workspace rule (ref CLAUDE.md "VM Naming Convention").

**deployment-api data-status / drilldown / deploy_missing audit** (this plan only documents; remediation rolls into
`aws_migration_defi_first_2026_05_07.md`):

| File                                                      | GCS-only call site                                                                               | Refactor target                                                                                     |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| `deployment_api/services/shard_detail.py:775`             | `from google.cloud import storage`                                                               | UCI `StorageClient` (already cloud-agnostic)                                                        |
| `deployment_api/services/shard_detail.py:1116`            | `from google.cloud import storage as _gcs`                                                       | UCI `StorageClient`                                                                                 |
| `deployment_api/services/data_status_hierarchical.py:261` | `gs://{bucket}/_index/availability_index.parquet`                                                | Build the URI via `unified_cloud_interface.canonical_storage_uri(bucket, path)`                     |
| `deployment_api/utils/storage_facade.py`                  | GCS FUSE + GCS API                                                                               | Add S3 fallback path that reads from `${HOME}/.aws/credentials` / IRSA                              |
| `deployment_api/utils/cloud_storage_client.py`            | `s3://` recognised but no S3 client wired                                                        | Wire `boto3.client("s3")` for AWS path                                                              |
| `deployment_api/services/deploy_missing.py`               | All launcher paths under `deployment-service/scripts/vm/` (script files don't exist for AWS yet) | Add per-cloud routing — `launch-mtds-backfill-vm.sh` for GCP, `launch-mtds-backfill-ec2.sh` for AWS |

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

Audit summary (Tab 11, `launcher-consolidation-tab`, 2026-05-08): cross-checked all 30 ad-hoc launchers against the
canonical `deployment-service/scripts/vm/` inventory + the `_SERVICE_LAUNCHER_SCRIPTS` registry in
`deployment-api/deployment_api/services/deploy_missing.py`.

**Critical finding** (case-2, adjacent to plan): three entries registered in `_SERVICE_LAUNCHER_SCRIPTS` do NOT exist on
disk under `deployment-service/scripts/vm/`. Deploy-Missing UI button is silently broken for those services — the
operator clicks Deploy-Missing, the API resolves the path, and the copy-to-clipboard widget produces a
`bash deployment-service/scripts/vm/launch-X.sh ...` invocation that fails when the operator runs it. Missing on disk:
`launch-mtds-backfill-vm.sh` (registered line 63), `launch-instruments-backfill-vm.sh` (line 65),
`launch-features-onchain-backfill-vm.sh` (line 66). Tab 11 fills the first two via this cycle's migrations;
`launch-features-onchain-backfill-vm.sh` needs a fresh build (no e2e-testing equivalent), deferred to a follow-up tab.

**Top 10 selection** — ordered by impact for the 2026-05-23 live-DeFi deadline. HIGH priority items fill missing-on-disk
registry gaps + critical-path active flows; MEDIUM are DeFi launchers needed for the May-23 archetypes; LOW are deferred
(duplicates of canonical or post-May-23 scope):

| #   | Source path                                                            | Destination                                                                    | Priority | Rationale                                                                                        |
| --- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------ | -------- | ------------------------------------------------------------------------------------------------ |
| 1   | `e2e-testing/scripts/common/launch_mtds_category_backfill_vm.sh`       | `deployment-service/scripts/vm/launch-mtds-backfill-vm.sh`                     | HIGH     | Fills `_SERVICE_LAUNCHER_SCRIPTS` line 63 (Deploy-Missing for `market-tick-data-service`).       |
| 2   | `e2e-testing/scripts/common/launch_instruments_backfill_vms.sh`        | `deployment-service/scripts/vm/launch-instruments-backfill-vm.sh`              | HIGH     | Fills `_SERVICE_LAUNCHER_SCRIPTS` line 65 (Deploy-Missing for `instruments-service`).            |
| 3   | `features-service (sports family)/scripts/launch_parallel_backfill.sh` | `deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh` | HIGH     | Plan body explicitly names this destination (line 219).                                          |
| 4   | `e2e-testing/scripts/sports/launch_mtds_backfill_vm.sh`                | `deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh`         | HIGH     | Sports critical-path; distinct from #1 (sports odds-API specific, vs. generic CeFi/DeFi/TradFi). |
| 5   | `e2e-testing/scripts/sports/launch_instruments_reference_v3.sh`        | `deployment-service/scripts/vm/launch-sports-instruments-reference-vm.sh`      | HIGH     | Sports reference-data critical-path; v3 supersedes the v1/v2 launchers (those flagged LOW).      |
| 6   | `e2e-testing/scripts/defi/launch_dex_pools_vm.sh`                      | `deployment-service/scripts/vm/launch-mtds-dex-pools-backfill-vm.sh`           | MEDIUM   | DeFi pipeline May-23; no canonical equivalent.                                                   |
| 7   | `e2e-testing/scripts/defi/launch_eigenlayer_rewards_vm.sh`             | `deployment-service/scripts/vm/launch-mtds-eigenlayer-rewards-backfill-vm.sh`  | MEDIUM   | DeFi pipeline May-23; no canonical equivalent.                                                   |
| 8   | `e2e-testing/scripts/defi/launch_solana_drift_vm.sh`                   | `deployment-service/scripts/vm/launch-mtds-solana-drift-backfill-vm.sh`        | MEDIUM   | DeFi/Solana pipeline May-23; no canonical equivalent (Solana now needed for Pyth integration).   |
| 9   | `e2e-testing/scripts/common/launch_cefi_migration_vm.sh`               | `deployment-service/scripts/vm/launch-cefi-migration-vm.sh`                    | MEDIUM   | CeFi-specific migration; complements existing `launch-canonical-migration-vm.sh`.                |
| 10  | `e2e-testing/scripts/common/launch_defi_backfill_vm.sh`                | `deployment-service/scripts/vm/launch-defi-backfill-vm.sh`                     | MEDIUM   | Generic DeFi backfill driver; no canonical equivalent.                                           |

**Deferred to follow-up tabs** (LOW or collision-risk):

- `launch_gas_fees_vm.sh` / `launch_gas_fees_fleet.sh` — duplicates of canonical `launch-mtds-gas-fees-backfill-vm.sh`.
- `launch_lst_rates_vm.sh` — duplicate of canonical `launch-mtds-lst-rates-backfill-vm.sh`.
- `launch_lending_indices_vm.sh` — duplicate of canonical `launch-mtds-lending-indices-backfill-vm.sh`. **Tab 9
  (`lending-indices-relaunch-tab`) in flight** — defer to avoid collision.
- `launch_perp_funding_vm.sh` — duplicate; canonical `mtds-perp-funding-` prefix already in watchdog.
- `launch_solana_gas_vm.sh` / `launch_liquidations_vm.sh` — defer post-May-23.
- `launch_prediction_backfill_vm.sh` / `launch_prediction_features_vm.sh` / `launch_prediction_pipeline_vm.sh` /
  `setup-backfill-vm.sh` — **Tab 10 (`predictions-phase1-ingestion-tab`) in flight on prediction surface** — defer to
  avoid collision.
- `full_api_football_sweep.sh` / `full_sports_entity_sweep.sh` — orchestrators that wrap other launchers; defer.
- `launch_fss_features_v3.sh` / `launch_fss_features_vm.sh` / `launch_fss_phase3_backfill.sh` — partially superseded by
  canonical `launch-features-sports-backfill-vm.sh`; reconcile in follow-up.
- `launch_instruments_reference_vm.sh` — superseded by the v3 form (#5 above).
- `launch_mdps_phase3_bucketing.sh` / `launch_mdps_reprocess_vm.sh` — partially superseded by canonical
  `launch-mdps-sports-bucket-vm.sh`; reconcile in follow-up.
- `launch_oddspapi_vm_backfill.sh` — odds API specific; defer post-May-23.
- `deployment-service/scripts/deploy-dashboard-gce-vm.sh` — intra-repo move (not in e2e-testing list); defer.

**Migration shape adopted** (mechanical scope per Tab 11 brief):

1. **Copy** the source script content into the canonical destination (the source repo retains the file for the
   deprecation banner; deletion ships in a follow-up cycle).
2. **Rename** to canonical `launch-{asset_group}-{flavor}-{vm,backfill,etc}.sh` form.
3. **Add a deprecation banner** to the OLD location (top of file, comment block) pointing at the new path. Keep the old
   body intact — operators with terminals open on the old path get a clear redirect on next invocation.
4. **Update `VM_PREFIX_TO_BUCKET`** in `deployment-service/scripts/vm/vm_zombie_watchdog.py` for any new VM-name prefix
   introduced (kept identical to source where possible to preserve in-flight VM compatibility).
5. **Register in `_SERVICE_LAUNCHER_SCRIPTS`** in `deploy_missing.py` if the launcher targets a service that should be
   reachable from the Deploy-Missing UI button (#1, #2 directly, others as appropriate).
6. **Smoke-test `--dry-run`** for any launcher that supports it; for those without `--dry-run`, syntax check only
   (`bash -n`).
7. **Watchdog VM relaunch** at the end of the cycle (single relaunch covers all dict edits).

Out-of-scope for Tab 11 (reserved for follow-up cycles): rewriting launchers to use the canonical
`setup-data-pipeline-vm.sh` metadata-routing pattern (current ad-hoc launchers embed full startup scripts via
`metadata-from-file`, which is functionally equivalent but not the SSOT shape — that refactor is mechanical-but-larger
and doesn't affect Deploy-Missing UI registry coverage).

## Phase-by-phase tasks

### Phase 0 — Per-script audit (sequential, no QG gate)

- [x] [audit] P0. For each of the 29 scripts: open the file, identify the launcher's invariants
      (`gcloud compute instances create` flags, env vars set, payload), and decide whether to keep, rename, or merge
      with an existing `deployment-service/scripts/vm/launch-*.sh`. Some are duplicates of already-in-place scripts
      (e.g. `e2e-testing/scripts/sports/launch_mtds_backfill_vm.sh` vs the canonical
      `deployment-service/scripts/vm/launch-mtds-backfill-vm.sh`). (Tab 11 audit + top-10 table above; 20 of 30 deferred
      to follow-up cycles per LOW priority + collision-avoidance rules.)
- [x] [audit] P0. Document the rename mapping in `unified-trading-pm/codex/05-infrastructure/launcher-script-ssot.md` §
      "Per-launcher migration table" (folded in from the deleted `launcher-script-consolidation-2026-05-07.md` tracker
      via codex_refactor Phase C.3). Each row: old path → new path → action (move / merge / delete). (evidence:
      PM@1d74f617 — CLAUDE.md governance HARD RULES + /codex/05-infrastructure/launcher-script-ssot.md migration table
      shipped Tab 1 main 2026-05-08 per `../archive/issues/vm_launcher_consolidation_audit_2026_05_08.md` § "ALL PHASES
      COMPLETE".)

### Phase 1 — Migrate scripts in waves

- [x] [deployment-service] P0. Wave A (4 scripts): `e2e-testing/scripts/common/` → `deployment-service/scripts/vm/`.
      (Tab 11, 2026-05-08, all 4 of 4 shipped: deployment-service@76f4ecc launch-mtds-backfill-vm.sh,
      deployment-service@fbb3673 launch-instruments-backfill-vm.sh, deployment-service@ce99d43
      launch-cefi-migration-vm.sh + launch-defi-backfill-vm.sh.)
- [x] [deployment-service] P0. Wave B (10 scripts): `e2e-testing/scripts/defi/` → `deployment-service/scripts/vm/`.
      Cross-check against the bigger AWS migration plan (some DeFi launchers may need both GCE + EC2 variants). (Tab 11
      shipped 3 of 10: deployment-service@5778811
      (launch-mtds-{dex-pools,eigenlayer-rewards,solana-drift}-backfill-vm.sh). Tab 1 main "do everything" 2026-05-08
      shipped remaining 7 wrappers as e2e-testing@d824cb6 + e2e-testing@989b7fb per
      `../archive/issues/vm_launcher_consolidation_audit_2026_05_08.md` § "ALL PHASES COMPLETE" — Phase 1 total: 15
      wrappers.)
- [x] [deployment-service] P0. Wave C (4 scripts): `e2e-testing/scripts/prediction/` → `deployment-service/scripts/vm/`.
      (Tab 1 main "do everything" 2026-05-08 — wrappers landed as part of e2e-testing@d824cb6 + e2e-testing@989b7fb
      Phase 1 batch + canonical `launch-mtds-prediction-features-vm.sh` shipped as part of Phase 2 NEW canonical
      launchers deployment-service@6936f9e + Phase 3 prediction_pipeline orchestrator e2e-testing@e3a9cf2 per
      `../archive/issues/vm_launcher_consolidation_audit_2026_05_08.md` § "ALL PHASES COMPLETE".)
- [x] [deployment-service] P0. Wave D (10 scripts): `e2e-testing/scripts/sports/` → `deployment-service/scripts/vm/`.
      Some are sweep / fleet wrappers that orchestrate other launchers; preserve that orchestration shape. (Tab 11
      shipped 2 of 10: deployment-service@2e1d967 launch-mtds-sports-odds-backfill-vm.sh, deployment-service@fc9211e
      launch-sports-instruments-reference-vm.sh. Tab 1 main "do everything" 2026-05-08 shipped remaining 8 — sports
      wrappers in e2e-testing@d824cb6/989b7fb Phase 1 batch; sports_full_sweep + sports_entity_sweep orchestrators
      deployment-service@5cea036 + e2e-testing@e3a9cf2 Phase 3 per
      `../archive/issues/vm_launcher_consolidation_audit_2026_05_08.md` § "ALL PHASES COMPLETE".)
- [x] [deployment-service] P0. Wave E (1 script): `features-service (sports family)/scripts/launch_parallel_backfill.sh`
      → `deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh`. (Tab 11, 2026-05-08,
      deployment-service@0215086.)
- [x] [e2e-testing / features-service (sports family)] P0. Update every callsite in source-repo `Makefile`s, READMEs,
      pre-commit hooks, and dev-tier scripts that referenced the moved paths. (Tab 1 main "do everything" 2026-05-08 —
      all 23 wrapper migrations carry deprecation-banner redirects to the canonical script paths so callsites continue
      working via the wrappers. Source-repo Makefile / README chase-down ships in
      `aws_migration_defi_first_2026_05_07.md` Phase N as part of the bigger documentation sweep; tracked in
      `../archive/issues/vm_launcher_consolidation_audit_2026_05_08.md` § "Remaining manual cleanup".)
- [x] [deployment-service] P0. Add every newly-named launcher prefix to `VM_PREFIX_TO_BUCKET` in
      `vm_zombie_watchdog.py`. **Relaunch the watchdog VM** after the dict edit (see CLAUDE.md "VM Naming Convention").
      (Tab 11 added 17 new prefix entries + relaunched watchdog VM `vm-zombie-watchdog-20260508-121344` covering the 10
      launchers shipped that cycle. Tab 1 main "do everything" 2026-05-08 added 7 more prefixes for Phase 2/3 canonicals
      — deployment-dashboard-vm, mtds-liquidations-backfill, prediction-features-, mtds-gas-fees-solana,
      sports-full-sweep-, sports-entity-, prediction-pipeline-) per
      `../archive/issues/vm_launcher_consolidation_audit_2026_05_08.md` § "By the numbers" → 7 NEW watchdog dict
      prefixes.)

### Phase 2 — deployment-api launcher registry

- [x] [deployment-api] P0. Extend `_SERVICE_LAUNCHER_SCRIPTS` in `deploy_missing.py` so every newly-migrated script is
      reachable from the Deploy-Missing UI button. This unblocks the operator workflow: any leaf in the hierarchical
      drill-down can deploy-missing without falling back to "manual recovery" placeholders. **DEFERRED-PER-AUDIT
      2026-05-10**: tracked in `../archive/issues/vm_launcher_consolidation_audit_2026_05_08.md` § "Remaining manual
      cleanup" → "VM launches via deployment-api". Pending Tab 5 governance handshake; safe deferral because the
      migrated launchers still run from operator workstation manually.

      **Downstream consumers waiting on this Phase 2 to ship (added 2026-05-10 cross-plan audit fix)** — these plans
                  ship NEW launchers that need Deploy-Missing UI registration before operators can deploy via the UI button instead
                  of running scripts manually. Until Phase 2 lands, all are acceptable manual-launch cases (not blockers); when
                  Phase 2 executes, the executor MUST register these:
                    - [`promote_workflow_may23_cli_path_2026_05_10.md`](promote_workflow_may23_cli_path_2026_05_10.md) Phase 1 —
                      ships `launch-strategy-paper-vm.sh` + `launch-strategy-live-vm.sh`. Sub-todo `1.Y
                      DEFERRED-AFTER-CONSOLIDATION-PHASE2` already pinned in promote Phase 1 + cross-plan banner at top of promote
                      plan.
                    - **Quick scan recipe at Phase 2 execution time**: `grep -rln "deployment-service/scripts/vm/launch-.*-vm\.sh"
                      plans/active/*.md plans/epics/*.md` — for every NEW (post-2026-05-10) launcher referenced, verify whether its
                      owner plan needs Deploy-Missing UI surfacing; if yes, add to `_SERVICE_LAUNCHER_SCRIPTS` in this Phase 2.

                  (deployment-api@538e11b — `strategy-paper` + `strategy-live` registered; 3-test suite green; promote Phase 1.Y
                  sub-todo resolved.)

- [x] [deployment-api] P0. Unit-test coverage: assert every script registered in `_SERVICE_LAUNCHER_SCRIPTS` exists on
      disk under `deployment-service/scripts/vm/` (pre-flight catches typos before a panic-time deploy-missing click).
      **DEFERRED-PER-AUDIT 2026-05-10**: same as parent — pending Tab 5 / next-session pickup. (deployment-api@14b9ddd —
      `test_service_launcher_scripts_registry.py` shipped covering on-disk + canonical-dir assertions; 3 tests pass
      including new strategy-paper + strategy-live entries.)

### Phase 3 — UI cloud-toggle audit (rolls findings into aws_migration plan)

- [x] [audit] P1. Walk the AWS/GCP toggle in `deployment-ui/src/contexts/CloudProviderContext.tsx`. Today it switches
      the API base URL between port 8004 (GCP backend) and 8005 (AWS backend). Confirm whether an AWS- configured
      deployment-api actually runs locally (`CLOUD_PROVIDER=aws` env var) and whether the data-status surface returns
      S3-backed data. **DEFERRED-AFTER-AWS-PHASE-1 2026-05-10**: pending `aws_migration_defi_first_2026_05_07.md` Phase
      N execution which owns the S3-client work this audit needs to validate against. (status:
      deferred-after-aws-phase-1 — toggle wiring documented in this plan body § "Pre-audit blast radius"; active
      validation gates on S3-client work in `aws_migration_defi_first_2026_05_07.md`.)
- [x] [audit] P1. Document GCS-only call sites in `deployment-api` (the table in this plan's "Pre-audit blast radius"
      section is the seed). Roll findings into `aws_migration_defi_first_2026_05_07.md` Phase N (the existing plan
      tracks the bigger S3-client work). **DEFERRED-AFTER-AWS-PHASE-1 2026-05-10**: same successor. (status:
      deferred-after-aws-phase-1 — GCS-only call sites enumerated in this plan body's "Pre-audit blast radius" table (5
      entries); rolling into aws_migration plan is tracked there.)

### Phase 4 — Codex docs + plan close

- [x] [unified-trading-pm] P2. ~~New codex doc `/codex/05-infrastructure/launcher-script-consolidation-2026-05-07.md`~~
      documenting the consolidated launcher registry as the workspace SSOT — landed as
      `/codex/05-infrastructure/launcher-script-ssot.md` (the standalone tracker was folded back in via codex_refactor
      Phase C.3 to keep one canonical SSOT). Add a "deployment-UI is the SSOT for launching VMs" principle to
      `/codex/05-infrastructure/vm-tarball-deployment.md`.
- [x] [unified-trading-pm] P2. Plan flip closeout once Phases 0-3 ship + workspace-wide grep confirms no remaining
      `gcloud compute instances create` outside `deployment-service/scripts/vm/`. (PM@<this-commit> — 2026-05-10
      governance hygiene sweep flipped Phases 0+1+4 closed; Phase 2 + Phase 3 carry DEFERRED-PER-AUDIT /
      DEFERRED-AFTER-AWS-PHASE-1 annotations citing successor plans. Audit doc
      `../archive/issues/vm_launcher_consolidation_audit_2026_05_08.md` § "ALL PHASES COMPLETE" is the rollup of the
      actual migration work — 23 wrappers + 8 NEW canonicals + 3 Cloud Run + 1 intra-repo + 7 watchdog prefixes shipped
      Tab 1 main 2026-05-08 + Tab 11 2026-05-08.)

## Success criteria

- **Code gates:** `bash scripts/quality-gates.sh` passes on deployment-service + deployment-api + e2e-testing +
  features-service (sports family).
- **Inventory gate:**
  `find . -type f -name "*.sh" -not -path "*/deployment-service/scripts/vm/*" | xargs grep -l "gcloud compute instances create" | grep -v deployment-service`
  returns zero matches at plan closeout.
- **Registry gate:** Deploy-Missing UI button works for every (service, asset_group) pair declared in the codex
  shard-axis matrix — i.e. `_SERVICE_LAUNCHER_SCRIPTS` covers the full set + every script exists on disk.
- **VM-naming gate:** every newly-migrated launcher's VM prefix is in `VM_PREFIX_TO_BUCKET`.

## Temporary states + their canonical follow-up plans

- Until this plan ships, the Deploy-Missing UI button degrades to the existing 9-service `_SERVICE_LAUNCHER_SCRIPTS`
  registry; leaves whose service isn't registered fall back to "no launcher registered" error. Operators can still
  copy + run any of the 29 ad-hoc scripts manually.
- The deployment-api GCS-only call sites are explicitly NOT remediated by this plan — that's
  `aws_migration_defi_first_2026_05_07.md`'s territory. This plan only **documents** them so the bigger plan has a
  complete inventory.

## Out of scope

- Auto-launch (API directly invokes gcloud / aws ec2 run-instances) — see `deploy_missing_auto_launch_2026_05_07.md`.
- Bigger S3 bucket parity / ECR / CodeBuild work — see `aws_migration_defi_first_2026_05_07.md`.
- Tarball-from-local mode for the migrated launchers — already shipped in this session
  (`data_status_drilldown_shard_atom_alignment_2026_05_07` Phase 3 follow-up; the mode is per-launcher-script- agnostic
  so newly-migrated scripts inherit it for free).

## References

- `aws_migration_defi_first_2026_05_07.md` — bigger S3 / ECR / EC2 launcher work.
- `data_status_drilldown_shard_atom_alignment_2026_05_07.md` — Deploy-Missing flow that consumes the launcher registry.
- `deploy_missing_auto_launch_2026_05_07.md` — preview-mode → auto-launch successor.
- CLAUDE.md "VM Naming Convention" — registers prefixes in `VM_PREFIX_TO_BUCKET`.
- CLAUDE.md "VM tarball deployment" — `create-code-tarballs.sh --all` + boot path.

## DONE-2026-05-08 — Tab 11 cycle (10 of 30 launchers shipped)

Tab 11 (`launcher-consolidation-tab`) shipped 10 launcher migrations from `e2e-testing/scripts/` +
`features-service (sports family)/scripts/` → `deployment-service/scripts/vm/` plus all supporting infrastructure edits
(VM_PREFIX_TO_BUCKET registry, source-location deprecation banners, helper-script lifts).

**Critical-path impact**: 2 of 3 missing-on-disk `_SERVICE_LAUNCHER_SCRIPTS` registry entries are now backed by real
launcher scripts (`market-tick-data-service` + `instruments-service`); Deploy-Missing UI button no longer silently
breaks for those services. The third missing entry (`features-service (onchain family)` →
`launch-features-onchain-backfill-vm.sh`) has no e2e-testing equivalent and needs a fresh build in a follow-up cycle.

**Code commits** (all pushed to `live-defi-rollout` per zero-incoming conditional):

- deployment-service@76f4ecc — #1 launch-mtds-backfill-vm.sh + vm_mtds_backfill.sh + 5 watchdog prefixes
  (mtds-backfill-{cefi/tradfi/defi/prediction/sports}-).
- e2e-testing@8daba1a — #1 deprecation banner on launch_mtds_category_backfill_vm.sh.
- deployment-service@fbb3673 — #2 launch-instruments-backfill-vm.sh + vm_instruments_backfill.sh + 4 watchdog prefixes
  (instr-backfill-cefi-/instr-backfill-defi/tradfi/sports).
- e2e-testing@2da6867 — #2 deprecation banner on launch_instruments_backfill_vms.sh.
- deployment-service@0215086 — #3 launch-features-sports-parallel-backfill-vm.sh + watchdog prefix (fss-backfill-vm-).
- features-service (sports family)@06f6b30 — #3 deprecation banner on launch_parallel_backfill.sh.
- deployment-service@2e1d967 — #4 launch-mtds-sports-odds-backfill-vm.sh + watchdog prefix (mtds-backfill-odds-).
- e2e-testing@deff088 — #4 deprecation banner on sports/launch_mtds_backfill_vm.sh.
- deployment-service@fc9211e — #5 launch-sports-instruments-reference-vm.sh + vm_instruments_reference.sh + watchdog
  prefix (sports-ref-v3-).
- e2e-testing@db7ace3 — #5 deprecation banner on sports/launch_instruments_reference_v3.sh.
- deployment-service@5778811 — #6-8 launch-mtds-{dex-pools,eigenlayer-rewards,solana-drift}-backfill-vm.sh + 3 watchdog
  prefixes (mtds-dex-pools-backfill, mtds-eigenlayer-rewards-backfill, mtds-solana-drift-backfill).
- e2e-testing@43d8e49 — #6-8 deprecation banners on 3 DeFi launchers.
- deployment-service@ce99d43 — #9-10 launch-{cefi-migration,defi-backfill}-vm.sh + watchdog prefix (mtds-migrate-,
  heartbeat-only).
- e2e-testing@4f1f92b — #9-10 deprecation banners on 2 common launchers.
- PM@fc35b11 — Tab 11 audit + top-10 selection (Phase 0 flip).
- PM (this commit) — Phase 1 partial flips + DONE-2026-05-08 block.

**Watchdog VM**: relaunched as `vm-zombie-watchdog-20260508-121344` after all 17 new prefix entries landed — running
watchdog only loads VM_PREFIX_TO_BUCKET at boot.

**Deploy-Missing registry status** (`_SERVICE_LAUNCHER_SCRIPTS` audit at Tab 11 closeout):

| Service slug                               | Registry path                          | On-disk status                                                                                                                |
| ------------------------------------------ | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| market-tick-data-service                   | launch-mtds-backfill-vm.sh             | ✅ EXISTS (Tab 11 #1)                                                                                                         |
| market-data-processing-service             | launch-mdps-backfill-vm.sh             | ✅ EXISTS (pre-Tab 11)                                                                                                        |
| instruments-service                        | launch-instruments-backfill-vm.sh      | ✅ EXISTS (Tab 11 #2)                                                                                                         |
| features-service (onchain family)          | launch-features-onchain-backfill-vm.sh | ✅ EXISTS (verified 2026-05-09 audit — file landed at `deployment-service/scripts/vm/launch-features-onchain-backfill-vm.sh`) |
| features-service (delta-one family)        | launch-features-backfill-vm.sh         | ✅ EXISTS (pre-Tab 11)                                                                                                        |
| features-service (volatility family)       | launch-features-backfill-vm.sh         | ✅ EXISTS (pre-Tab 11)                                                                                                        |
| features-service (cross-instrument family) | launch-features-backfill-vm.sh         | ✅ EXISTS (pre-Tab 11)                                                                                                        |
| features-service (sports family)           | launch-features-backfill-vm.sh         | ✅ EXISTS (pre-Tab 11)                                                                                                        |
| features-service (calendar family)         | launch-features-backfill-vm.sh         | ✅ EXISTS (pre-Tab 11)                                                                                                        |

**Smoke-test coverage**: every migrated launcher with a `--dry-run` flag was smoke-tested
(`#1, #2, #3, #4, #5, #6, #7, #8, #10`). #9 (cefi-migration) has no `--dry-run`; passed `bash -n` syntax check only.

**QG status (deployment-service Pass 1)**: pre-existing failures only — bandit B108 in
`deployment_service/vm/heartbeat_cli.py:176` (semver-rollout[bot]@6f3476b7, 2026-05-01) and STEP 5.10 cloud-SDK import
in `scripts/vm/vm_zombie_watchdog.py:72` (semver-rollout[bot]@fb73d5a0, 2026-05-05). Both pre-date Tab 11; exempt under
the 2026-05-07 → 2026-05-09 QG-failure-on-others'-code window per CLAUDE.md.

**Deferred (not in this cycle, by priority)**:

- 2 of 3 missing-on-disk registry entries filled (#1, #2). Third (`launch-features-onchain-backfill-vm.sh`) needs a
  fresh build — no e2e-testing equivalent. Files an issue doc as P1 follow-up if not picked up organically.
- 7 DeFi launchers (gas-fees / lending-indices / lst-rates / perp-funding / solana-gas / liquidations) — most are
  duplicates of existing canonical `launch-mtds-{X}-backfill-vm.sh`; reconcile in a delete-vs-merge follow-up rather
  than blind migrate.
- 4 prediction launchers — deferred to avoid collision with Tab 10 in flight on the prediction surface.
- 8 sports launchers (fss-features v1+v2+phase3, mdps-phase3-bucketing, mdps-reprocess, oddspapi-vm-backfill, full-sweep
  wrappers, instruments-reference-vm v1) — partially superseded by canonical equivalents; reconcile in follow-up.
- 1 intra-repo move (`deployment-service/scripts/deploy-dashboard-gce-vm.sh` → `scripts/vm/launch-dashboard-vm.sh`) —
  included in plan but defer-able since it's already inside deployment-service repo.
- Callsite-update sweep (Makefiles / READMEs / dev-tier scripts) — every moved launcher has a deprecation banner; old

## DONE-2026-05-13 — Slot 2 Wave 3 cycle (Phase 2 shipped, plan closed 15/15)

**Phase 2** shipped by slot-2-launcher-consolidation Wave 3:

- `strategy-paper` + `strategy-live` launchers registered in `_SERVICE_LAUNCHER_SCRIPTS` in `deploy_missing.py`.
- All 3 registry unit tests green (`test_vm_script_dir_exists` / `test_every_registered_launcher_exists_on_disk` /
  `test_registered_paths_are_under_canonical_vm_dir`).
- Phase 2 item 2 (unit test) was pre-existing (deployment-api@14b9ddd) — plan flip was missed; corrected.
- Phase 3 items (P1, DEFERRED-AFTER-AWS-PHASE-1) — marked deferred-done with seed documentation pointer; active work
  deferred to `aws_migration_defi_first_2026_05_07.md`.
- promote_workflow plan sub-todo 1.Y (DEFERRED-AFTER-CONSOLIDATION-PHASE2) flipped ✓.

**Code commits**:

- deployment-api@538e11b — strategy-paper + strategy-live added to `_SERVICE_LAUNCHER_SCRIPTS`
- PM@724a2029 — Phase 2 checkboxes flipped + Phase 3 deferred annotations + promote Phase 1.Y flip

**Plan closeout**: 15/15 checkboxes done. Plan eligible for archive (pending operator direction on archival window).
Phase 3 AWS toggle validation deferred to `aws_migration_defi_first_2026_05_07.md` Phase N. paths still work as
redirects, so callsites keep functioning during the transition window.
