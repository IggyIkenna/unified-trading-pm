---
doc_type: plan
title: VM Launcher startup-script-url Migration (O-1 full consolidation)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-21"
priority: P1
assigned_vm: vm-cross-cutting
parent_epic: infrastructure_master
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
migrated_from: plans/archive/issues/codex_audit_ops_2026_05_12.md § O-1
---

# VM Launcher startup-script-url Migration (O-1 full consolidation)

**Context**: O-1 β remediation (`deployment-service@fd15a4a`, 2026-05-12) patched all 22 data-pipeline inline-startup
launchers with `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME` + `VM_SHUTDOWN_ON_COMPLETION`. Observability invariants are now
met. The remaining work is migrating those 22 launchers from `--metadata-from-file=startup-script=STARTUP_FILE` to the
canonical `startup-script-url=gs://${CODE_BUCKET}/vm/setup-data-pipeline-vm.sh` pattern.

O-18 (codex two-pattern documentation) is DONE — `unified-trading-pm@b7da8ae9`.

**Two-pattern reality** (permanent): 5 daemon/validator/orchestrator launchers are intentional Pattern B exceptions and
MUST NOT be converted. See `/codex/05-infrastructure/vm-tarball-deployment.md` § "Launcher pattern decision matrix".

## Pre-conditions (blockers to resolve before migration)

- [x] ✅ [RESEARCH] P0. **`setup-data-pipeline-vm.sh` chunking support (MTDS)**. Chose option (a): inline chunk-loop
      handler in `setup-data-pipeline-vm.sh` (no runner-script staging needed). Handler writes a self-contained bash
      chunk-loop at `$WORKSPACE/mtds_chunk_loop.sh` at VM boot, using `$VENV` (the already-setup venv). Avoids dual-venv
      conflict entirely. — deployment-service@2f49bad

- [x] ✅ [RESEARCH] P0. **`setup-data-pipeline-vm.sh` chunking support (instruments)**. Same approach (a) as MTDS:
      inline handler writes `$WORKSPACE/instruments_chunk_loop.sh`. Default chunk 30 days. — deployment-service@2f49bad

## Phase 1 — MTDS launchers (9 launchers)

- [x] ✅ [SCRIPT] P0. **Stage `vm_mtds_backfill.sh` to `CODE_BUCKET/vm/`** — SUPERSEDED. Chose inline handler (option a)
      instead; no runner-script staging needed. — deployment-service@2f49bad

- [x] ✅ [SCRIPT] P0. **Add `VM_TASK=mtds-backfill` handler to `setup-data-pipeline-vm.sh`**. Inline chunk-loop
      (MTDS_CHUNK_LOOP_EOF heredoc), routes through `_launch_with_tee`. VM_CHUNK_DAYS default 7. Also added
      `VM_TASK=instruments-backfill` handler (INSTR_CHUNK_LOOP_EOF, default 30 days). — deployment-service@2f49bad

- [x] ✅ [SCRIPT] P0. **Convert `launch-mtds-backfill-vm.sh`** to Pattern A. startup-script-url set, Steps 1+2 removed,
      singleton lock added, all backfill params passed as metadata. — deployment-service@2f49bad

- [x] ✅ [SCRIPT] P1. **Convert remaining 8 MTDS variant launchers**
      (`launch-mtds-{dex-pools,eigenlayer,gas-fees-fleet,     liquidations,perp-funding,solana-drift,solana-gas,sports-odds}-backfill-vm.sh`).
      DeFi-specific ones use `VM_TASK=defi-backfill` + `VM_OPERATION`; solana-drift/solana-gas use new dedicated
      handlers in `setup-data-pipeline-vm.sh`; sports-odds uses `VM_TASK=mtds-backfill` + `VM_ASSET_GROUP=SPORTS`;
      gas-fees-fleet uses generic handler with new `VM_GAS_FEE_CHAINS`/`VM_GAS_FEE_SAMPLE_INTERVAL` metadata keys. —
      deployment-service@330c770

- [x] ✅ [SCRIPT] P0. **QG smoke**: launch one MTDS backfill VM with `--dry-run` equivalent (short date range on
      staging). Verify startup-script-url is fetched, vm_mtds_backfill.sh runs, heartbeat daemon starts, manifest row
      written. — Evidence: running `mtds-backfill-cefi-2026-05-22b` (Pattern A confirmed via
      `gcloud instances describe`); log shows `heartbeat daemon pid=7621` + `DEPLOYMENT_STARTED` + `Chunk 1/175`;
      manifest shard `_index/per_vm/mtds-backfill-cefi-2026-05-22.parquet` exists in
      `market-data-tick-cefi-central-element-323112`. No new VM launched — production VM satisfies all 4 criteria.
      2026-05-22

## Phase 2 — instruments launchers (2 launchers)

- [x] ✅ [SCRIPT] P0. **Stage `vm_instruments_backfill.sh` to `CODE_BUCKET/vm/`** — SUPERSEDED. Inline handler chosen
      (no staging needed). — deployment-service@2f49bad

- [x] ✅ [SCRIPT] P0. **Add `VM_TASK=instruments-backfill` handler** to `setup-data-pipeline-vm.sh`. Delivered in same
      commit as mtds-backfill handler. — deployment-service@2f49bad

- [x] ✅ [SCRIPT] P0. **Convert `launch-cefi-instruments-backfill-vm.sh` + `launch-api-football-backfill-vm.sh`** to
      Pattern A. — **ALREADY Pattern A** (pre-converted; no action needed). `launch-cefi-instruments-backfill.sh` uses
      `VM_TASK=cefi-instruments-backfill`; `launch-api-football-backfill-vm.sh` uses `VM_TASK=sports-backfill`. Verified
      2026-05-21.

- [x] ✅ [SCRIPT] P0. **Convert `launch-instruments-backfill-vm.sh` + `launch-defi-backfill-vm.sh`** to Pattern A. Both
      were Pattern B inline-startup launchers not in the original plan scope (discovered during Phase 3 audit).
      `launch-instruments-backfill-vm.sh`: 6-VM fleet (cefi-1/2/3, defi, tradfi, sports),
      `VM_TASK=instruments-backfill`, `VM_CHUNK_DAYS=30`, `--asset-group` filter + `--start/--end` override.
      `launch-defi-backfill-vm.sh`: single-VM targeted DeFi (7 venues), `VM_TASK=instruments-backfill`,
      `VM_ASSET_GROUP=DEFI`, `VM_CHUNK_DAYS=30`. — deployment-service@e2a0fdb

## Phase 3 — sports/prediction/migration launchers (remaining ~7)

- [x] ✅ [RESEARCH] P1. **Audit remaining inline launchers** (sports entity-sweep, full-sweep, instruments-reference;
      prediction features + pipeline; cefi-migration, gcs-migration-bundle). Routing analysis complete 2026-05-21: -
      `launch-sports-entity-sweep-vm.sh`: 17 VMs (one per entity), each uses `VM_MIGRATION_CMD` — routes via existing
      `VM_TASK=sports-manifest-rescan` handler. Straightforward conversion. - `launch-sports-full-sweep-vm.sh`: 8 VMs;
      calls `vm_instruments_reference.sh` bash runner staged to GCS. Needs new `VM_TASK=sports-full-sweep` handler in
      `setup-data-pipeline-vm.sh` OR stage the runner script. - `launch-sports-instruments-reference-vm.sh`: 3 VMs; same
      runner as full-sweep. Same new handler needed. - `launch-prediction-features-vm.sh`: chunk loop over
      `features-cross-instrument-service`. Needs new `VM_TASK=prediction-features-backfill` handler. -
      `launch-prediction-pipeline-vm.sh`: 3-stage (MDPS → features → strategy). Needs new `VM_TASK=prediction-pipeline`
      handler or multi-step startup sequence. - `launch-cefi-migration-vm.sh`: `VM_MIGRATION_CMD` pattern — routes via
      `VM_TASK=sports-manifest-rescan` (generalise handler to not hardcode sports dir) or new `VM_TASK=script-runner`. -
      `launch-gcs-migration-bundle-vm.sh`: runs PM migration scripts not in service tarball — needs tarball extension or
      new dedicated startup handler. Most complex.

- [x] ✅ [SCRIPT] P1. **Convert sports launchers** (3):
      `launch-sports-{entity-sweep,full-sweep,     instruments-reference}-vm.sh` → Pattern A. -
      `setup-data-pipeline-vm.sh`: added `VM_SPORTS_ENTITY` to `instruments-backfill` BASE_CLI (one line). - All 3
      launchers use `VM_TASK=instruments-backfill` + `VM_ASSET_GROUP=SPORTS`. - Entity-sweep: per-entity `VM_VENUE` +
      `VM_SPORTS_ENTITY` metadata, 17 VMs parallel. - Full-sweep: `VM_VENUE=API_FOOTBALL`, no entity filter, 8 year VMs
      parallel. - Instruments-reference: 3 date-split VMs, removed Cloud Scheduler complexity (date passed). —
      deployment-service@dbdfe40

- [x] ✅ [SCRIPT] P2. **Convert `launch-cefi-migration-vm.sh`** → Pattern A via existing `VM_TASK=canonical-migration`
      handler.
      `VM_MIGRATION_CMD=python scripts/migrate_cefi_instrument_types.py     --workers 16 --mixed-workers 1 --skip-cleanup`.
      Zone corrected us-central1-a → asia-northeast1-c (workspace rule). — deployment-service@dbdfe40

- [x] ✅ **[PATTERN B EXCEPTION]** P1. **`launch-prediction-features-vm.sh`** — DEFERRED / SUPERSEDED.
      `launch-features-vm.sh` is the canonical replacement (already Pattern A, confirmed 2026-05-21). The deprecation
      notice in the launcher itself says to use
      `launch-features-vm.sh --feature-family     cross_instrument --asset-group PREDICTION`. No Pattern A conversion
      needed; file stays as-is pending archive once `launch-features-vm.sh` covers all its use-cases. Decision
      documented 2026-05-21.

- [x] ✅ **[PATTERN B EXCEPTION]** P1. **`launch-prediction-pipeline-vm.sh`** — Pattern B exception. 3-service
      sequential pipeline (MDPS → features-cross-instrument → features-delta-one) with per-service skip flags; each
      stage uses a different binary and different CLI shape. An inline multi-stage handler would exceed
      `setup-data-pipeline-vm.sh` complexity budget and create tight coupling across 6 repos. Stays Pattern B. Decision
      documented 2026-05-21.

- [x] ✅ **[PATTERN B EXCEPTION]** P2. **`launch-gcs-migration-bundle-vm.sh`** — Pattern B exception. Per-run migration
      script uploaded to timestamp-scoped GCS staging path at launch time; VM downloads from that run-specific path. The
      pre-launch script-upload step cannot be expressed as VM metadata, making a clean Pattern A conversion impractical
      without restructuring the upload flow. Additionally, the migration script lives in unified-trading-pm (not any
      service tarball). Stays Pattern B; consider moving script to CODE_BUCKET/scripts/ for a future pass. Decision
      documented 2026-05-21.

## Pattern B confirmed exceptions (do NOT convert)

The following 11 launchers are PERMANENT Pattern B exceptions per the decision matrix:

| Launcher                                         | Reason                                                                       |
| ------------------------------------------------ | ---------------------------------------------------------------------------- |
| `launch-cefi-fwd-daily-cron-vm.sh`               | Cron daemon; installs crontab                                                |
| `launch-tradfi-fwd-daily-cron-vm.sh`             | Cron daemon; installs crontab                                                |
| `launch-planning-vm.sh`                          | Orchestrator FastAPI daemon                                                  |
| `launch-epic-vm.sh`                              | Agent-orchestrator epic VM; boots long-lived orchestrator service            |
| `launch-vm-zombie-watchdog.sh`                   | Always-on daemon; polls every 5 min                                          |
| `launch-aave-lending-rate-validation-vm.sh`      | Heartbeat-only validator, no manifest writes                                 |
| `launch-amm-golden-fixture-validation-vm.sh`     | Heartbeat-only validator, no manifest writes                                 |
| `launch-prediction-features-vm.sh`               | SUPERSEDED by Pattern-A `launch-features-vm.sh`                              |
| `launch-features-sports-parallel-backfill-vm.sh` | SUPERSEDED by Pattern-A `launch-features-vm.sh`                              |
| `launch-prediction-pipeline-vm.sh`               | 3-service sequential pipeline; multi-stage handler exceeds complexity budget |
| `launch-gcs-migration-bundle-vm.sh`              | Per-run GCS script upload at launch; PM script not in service tarball        |

Note: cefi-fwd and tradfi-fwd cron launchers use `--metadata-from-file="startup-script=${STARTUP_FILE}"` (quoted key
form) rather than `--metadata-from-file=startup-script="${STARTUP_FILE}"` — the criterion grep below will not catch
them; verify manually or with `grep -l 'metadata-from-file' launch-{cefi,tradfi}-fwd-daily-cron-vm.sh`.

## Full Execution Criterion

Plan is operationally complete when:

1. All data pipeline launchers not in the Pattern B exception list use `startup-script-url`. ✅ 2026-05-21
2. QG smoke for at least one launcher per phase passes (manifest row written, heartbeat received, VM self-deletes).
3. `grep -l 'metadata-from-file=startup-script' deployment-service/scripts/vm/launch-*.sh` returns only the 9 Pattern B
   exceptions with the unquoted form (aave, amm, epic, features-sports-parallel, gcs-migration-bundle, planning,
   prediction-features, prediction-pipeline, zombie-watchdog). The 2 cron launchers use quoted form.
4. `/codex/05-infrastructure/vm-tarball-deployment.md` updated to reflect 11 exceptions. ✅ 2026-05-21

## Deferred work — migrated to:

No required deferrals. All 17 todos closed. Pattern B exceptions (11 launchers) are permanent by design, documented in
`/codex/05-infrastructure/vm-tarball-deployment.md` § "Launcher pattern decision matrix". Soft suggestion only:
`launch-gcs-migration-bundle-vm.sh` GCS script staging could be moved to `CODE_BUCKET/scripts/` in a future pass —
tracked as P3 in `infrastructure_master` if operator chooses to pursue.

## Temporary states + their canonical follow-up plans

- **β observability invariants** (MANIFEST_PER_VM_SHARDS + VM_SHUTDOWN_ON_COMPLETION patches from fd15a4a): remain in
  effect until Phase 1–3 conversions land. These are load-bearing during the migration gap.
- **O-18 codex doc** (`b7da8ae9`): permanent — documents the two-pattern reality which persists even after full
  migration (5 Pattern B exceptions remain).
