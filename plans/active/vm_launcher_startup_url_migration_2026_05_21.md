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

- [x] ✅ [RESEARCH] P0. **`setup-data-pipeline-vm.sh` chunking support (MTDS)**. Chose option (a): inline chunk-loop
      handler in `setup-data-pipeline-vm.sh` (no runner-script staging needed). Handler writes a self-contained
      bash chunk-loop at `$WORKSPACE/mtds_chunk_loop.sh` at VM boot, using `$VENV` (the already-setup venv). Avoids
      dual-venv conflict entirely. — deployment-service@2f49bad

- [x] ✅ [RESEARCH] P0. **`setup-data-pipeline-vm.sh` chunking support (instruments)**. Same approach (a) as MTDS:
      inline handler writes `$WORKSPACE/instruments_chunk_loop.sh`. Default chunk 30 days. — deployment-service@2f49bad

## Phase 1 — MTDS launchers (9 launchers)

- [x] ✅ [SCRIPT] P0. **Stage `vm_mtds_backfill.sh` to `CODE_BUCKET/vm/`** — SUPERSEDED. Chose inline handler (option
      a) instead; no runner-script staging needed. — deployment-service@2f49bad

- [x] ✅ [SCRIPT] P0. **Add `VM_TASK=mtds-backfill` handler to `setup-data-pipeline-vm.sh`**. Inline chunk-loop
      (MTDS_CHUNK_LOOP_EOF heredoc), routes through `_launch_with_tee`. VM_CHUNK_DAYS default 7. Also added
      `VM_TASK=instruments-backfill` handler (INSTR_CHUNK_LOOP_EOF, default 30 days). — deployment-service@2f49bad

- [x] ✅ [SCRIPT] P0. **Convert `launch-mtds-backfill-vm.sh`** to Pattern A. startup-script-url set, Steps 1+2
      removed, singleton lock added, all backfill params passed as metadata. — deployment-service@2f49bad

- [x] ✅ [SCRIPT] P1. **Convert remaining 8 MTDS variant launchers** (`launch-mtds-{dex-pools,eigenlayer,gas-fees-fleet,
      liquidations,perp-funding,solana-drift,solana-gas,sports-odds}-backfill-vm.sh`). DeFi-specific ones use
      `VM_TASK=defi-backfill` + `VM_OPERATION`; solana-drift/solana-gas use new dedicated handlers in
      `setup-data-pipeline-vm.sh`; sports-odds uses `VM_TASK=mtds-backfill` + `VM_ASSET_GROUP=SPORTS`;
      gas-fees-fleet uses generic handler with new `VM_GAS_FEE_CHAINS`/`VM_GAS_FEE_SAMPLE_INTERVAL` metadata keys.
      — deployment-service@330c770

- [ ] [SCRIPT] P0. **QG smoke**: launch one MTDS backfill VM with `--dry-run` equivalent (short date range on
      staging). Verify startup-script-url is fetched, vm_mtds_backfill.sh runs, heartbeat daemon starts, manifest
      row written.

## Phase 2 — instruments launchers (2 launchers)

- [x] ✅ [SCRIPT] P0. **Stage `vm_instruments_backfill.sh` to `CODE_BUCKET/vm/`** — SUPERSEDED. Inline handler chosen
      (no staging needed). — deployment-service@2f49bad

- [x] ✅ [SCRIPT] P0. **Add `VM_TASK=instruments-backfill` handler** to `setup-data-pipeline-vm.sh`. Delivered in
      same commit as mtds-backfill handler. — deployment-service@2f49bad

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
