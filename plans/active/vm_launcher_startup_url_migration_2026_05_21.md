---
title: "VM Launcher startup-script-url Migration (O-1 full consolidation)"
status: active
assigned_vm: vm-cross-cutting
parent_epic: infrastructure_master
locked_by: live-defi-rollout
locked_since: 2026-05-21
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
migrated_from: plans/archive/issues/codex_audit_ops_2026_05_12.md § O-1
---

# VM Launcher startup-script-url Migration (O-1 full consolidation)

**Context**: O-1 β remediation (`deployment-service@fd15a4a`, 2026-05-12) patched all 22 data-pipeline inline-startup
launchers with `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME` + `VM_SHUTDOWN_ON_COMPLETION`. Observability invariants are
now met. The remaining work is migrating those 22 launchers from `--metadata-from-file=startup-script=STARTUP_FILE` to
the canonical `startup-script-url=gs://${CODE_BUCKET}/vm/setup-data-pipeline-vm.sh` pattern.

O-18 (codex two-pattern documentation) is DONE — `unified-trading-pm@b7da8ae9`.

**Two-pattern reality** (permanent): 5 daemon/validator/orchestrator launchers are intentional Pattern B exceptions and
MUST NOT be converted. See `codex/05-infrastructure/vm-tarball-deployment.md` § "Launcher pattern decision matrix".

## Pre-conditions (blockers to resolve before migration)

- [ ] [RESEARCH] P0. **`setup-data-pipeline-vm.sh` chunking support (MTDS)**. `vm_mtds_backfill.sh` uses 7-day
      date-chunks (Tardis API rate limits) with its own venv at `${WORK_DIR}/.venv`. The canonical setup script uses
      `/home/ikennaigboaka/venv` with no chunk loop. Either: (a) add `VM_CHUNK_DAYS` metadata + a chunk-loop handler to
      `setup-data-pipeline-vm.sh`; or (b) modify `vm_mtds_backfill.sh` to use the existing venv path and stage it to
      `CODE_BUCKET/vm/` as a downloadable helper. Option (b) is lower-risk. Document chosen path here before
      implementation.

- [ ] [RESEARCH] P0. **`setup-data-pipeline-vm.sh` chunking support (instruments)**. `vm_instruments_backfill.sh`
      uses 30-day chunks and its own venv. Same two options as above. Can share the same resolution as MTDS if option
      (b) is chosen (stage runner script to GCS, download at VM boot, call from setup-data-pipeline-vm.sh handler).

## Phase 1 — MTDS launchers (9 launchers)

- [ ] [SCRIPT] P0. **Stage `vm_mtds_backfill.sh` to `CODE_BUCKET/vm/`**. Ensure the runner script uses
      `/home/ikennaigboaka/venv` (not a local WORK_DIR venv). Add to `create-code-tarballs.sh` upload step or
      upload separately in the launcher.

- [ ] [SCRIPT] P0. **Add `VM_TASK=mtds-backfill` handler to `setup-data-pipeline-vm.sh`**. Handler: download
      `vm_mtds_backfill.sh` from `CODE_BUCKET/vm/`, invoke with `--asset-group $VM_ASSET_GROUP --start-date
      $VM_START_DATE --end-date $VM_END_DATE --chunk-size ${VM_CHUNK_DAYS:-7}`. Route through `_launch_with_tee`.

- [ ] [SCRIPT] P0. **Convert `launch-mtds-backfill-vm.sh`** to Pattern A (`startup-script-url`). Set
      `VM_TASK=mtds-backfill`. Remove inline `STARTUP_FILE` heredoc + `--metadata-from-file`.

- [ ] [SCRIPT] P1. **Convert remaining 8 MTDS variant launchers** (`launch-mtds-{dex-pools,eigenlayer,gas-fees-fleet,
      liquidations,perp-funding,solana-drift,solana-gas,sports-odds}-backfill-vm.sh`). Each sets appropriate
      `VM_ASSET_GROUP` + `VM_TASK=mtds-backfill`.

- [ ] [SCRIPT] P0. **QG smoke**: launch one MTDS backfill VM with `--dry-run` equivalent (short date range on
      staging). Verify startup-script-url is fetched, vm_mtds_backfill.sh runs, heartbeat daemon starts, manifest
      row written.

## Phase 2 — instruments launchers (2 launchers)

- [ ] [SCRIPT] P0. **Stage `vm_instruments_backfill.sh` to `CODE_BUCKET/vm/`**. Fix venv path to use
      `/home/ikennaigboaka/venv`.

- [ ] [SCRIPT] P0. **Add `VM_TASK=instruments-backfill` handler** (if not already present) to
      `setup-data-pipeline-vm.sh`. Similar shape to mtds-backfill handler.

- [ ] [SCRIPT] P0. **Convert `launch-cefi-instruments-backfill-vm.sh` + `launch-api-football-backfill-vm.sh`** to
      Pattern A.

## Phase 3 — sports/prediction/migration launchers (remaining ~11)

- [ ] [SCRIPT] P1. **Audit remaining inline launchers** (sports entity-sweep, full-sweep, instruments-reference;
      prediction features + pipeline; cefi-migration, gcs-migration-bundle). For each: determine if `VM_TASK` routing
      already exists in `setup-data-pipeline-vm.sh` or needs a new handler. File sub-items here after audit.

- [ ] [SCRIPT] P1. **Convert sports launchers** (3): `launch-sports-{entity-sweep,full-sweep,
      instruments-reference}-vm.sh` → Pattern A using existing or new `VM_TASK` handlers.

- [ ] [SCRIPT] P1. **Convert prediction launchers** (2): `launch-prediction-{features,pipeline}-vm.sh` → Pattern A.

- [ ] [SCRIPT] P2. **Convert migration launchers** (2): `launch-{cefi-migration,gcs-migration-bundle}-vm.sh`. These
      run custom Python scripts not in the standard service tarball path. Option: add `VM_TASK=script-runner` handler
      that reads `VM_MIGRATION_CMD` and runs it verbatim (this handler already exists as `VM_TASK=sports-manifest-rescan`
      which runs `VM_MIGRATION_CMD` in a specific dir — generalise it).

## Pattern B confirmed exceptions (do NOT convert)

The following 5 launchers are PERMANENT Pattern B exceptions per the decision matrix:

| Launcher                                     | Reason                                     |
| -------------------------------------------- | ------------------------------------------ |
| `launch-cefi-fwd-daily-cron-vm.sh`           | Cron daemon; installs crontab              |
| `launch-tradfi-fwd-daily-cron-vm.sh`         | Cron daemon; installs crontab              |
| `launch-planning-vm.sh`                      | Orchestrator FastAPI daemon                |
| `launch-aave-lending-rate-validation-vm.sh`  | Heartbeat-only validator, no manifest writes |
| `launch-amm-golden-fixture-validation-vm.sh` | Heartbeat-only validator, no manifest writes |

## Full Execution Criterion

Plan is operationally complete when:

1. All 22 data pipeline inline launchers use `startup-script-url=gs://${CODE_BUCKET}/vm/setup-data-pipeline-vm.sh`.
2. QG smoke for at least one launcher per phase passes (manifest row written, heartbeat received, VM self-deletes).
3. `grep -l 'metadata-from-file=startup-script' deployment-service/scripts/vm/launch-*.sh` returns only the 5
   confirmed Pattern B exceptions.
4. `codex/05-infrastructure/vm-tarball-deployment.md` updated if the decision matrix needs revision.

## Temporary states + their canonical follow-up plans

- **β observability invariants** (MANIFEST_PER_VM_SHARDS + VM_SHUTDOWN_ON_COMPLETION patches from fd15a4a): remain in
  effect until Phase 1–3 conversions land. These are load-bearing during the migration gap.
- **O-18 codex doc** (`b7da8ae9`): permanent — documents the two-pattern reality which persists even after full
  migration (5 Pattern B exceptions remain).
