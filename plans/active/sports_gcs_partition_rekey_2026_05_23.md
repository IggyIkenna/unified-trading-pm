---
title: "Sports GCS partition key rekey — category=sports/ → asset_group=sports/"
name: sports-gcs-partition-rekey-2026-05-23
created: 2026-05-23
parent_epic: sports_master
assigned_vm: vm-sports
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-05-23
---

## Context

GCS audit 2026-05-23 found that the Sports bucket (`market-data-tick-sports-central-element-323112`) uses
`category=sports/` as the top-level hive key for ALL days. The canonical hive key is `asset_group=` per workspace SSOT.
DeFi and CEFI already migrated; Sports migration never ran.

Active Sports VMs (`mdps-sports-2025-20260523-170621`, `instr-backfill-sports`) are running as of 2026-05-23 — migration
MUST NOT run while VMs are writing to the bucket (pre-migration drain required; CLAUDE.md HARD RULE).

### What this plan does

1. **Write a dedicated hive-rekey migration script** (`migrate_sports_hive_key.py`) — reads each parquet from
   `raw_tick_data/by_date/day=*/category=sports/...`, copies to `raw_tick_data/by_date/day=*/asset_group=sports/...`,
   then deletes the `category=sports/` source object. Uses UTL `gcs_copy_object`/`gcs_delete_object` (not gsutil
   subprocess — 250× faster per SSOT).
2. **Drain Sports VMs** (pre-migration gate per CLAUDE.md).
3. **Run migration + manifest consolidation** after drain confirms STOPPED.
4. **Verify** via spot-check parquets + manifest audit item (f).

### What this plan does NOT do

The existing `migrate_sports_canonical.py` script rewrites venue names + instrument_type + data_type within
`category=sports/`. Both scripts must be run; ordering: **hive-rekey BEFORE canonical** (canonical script will be
updated to use `asset_group=sports/` as its output prefix).

## Pre-audit findings (2026-05-23)

| Bucket                                                     | Total days  | `category=sports/` | `asset_group=sports/` |
| ---------------------------------------------------------- | ----------- | ------------------ | --------------------- |
| `market-data-tick-sports-central-element-323112` (GCP prd) | ~all        | ALL                | 0                     |
| AWS sports bucket (if exists)                              | not audited | unknown            | unknown               |

GCS partition key for AWS sports buckets: **MUST audit before running migration** (Phase 0).

## Phases

### Phase 0 — Pre-migration audit + script write (PARALLEL with Phase 0b)

- [x] ✅ [SCRIPT] P1. Write `market_tick_data_service/scripts/migrate_sports_hive_key.py` — walks
      `day=*/category=sports/`, copies to `day=*/asset_group=sports/`, deletes source, shard-level failure isolation,
      events emitted: `MIGRATE_SPORTS_HIVE_RUN_STARTED` / `MIGRATE_SPORTS_HIVE_DAY_COMPLETED` /
      `MIGRATE_SPORTS_HIVE_RUN_COMPLETED`. Uses UTL `gcs_copy_object`/`gcs_delete_object`. Supports `--dry-run`. —
      mtds@da09d72c, ruff+basedpyright clean
- [ ] [SCRIPT] P1. Update `migrate_sports_canonical.py` docstring + source prefix constant from `category=sports/` →
      `asset_group=sports/` so post-hive-rekey run sees canonical paths.

- [ ] [SCRIPT] P1. Audit AWS sports buckets for `category=sports/` vs `asset_group=sports/` partition key state. Update
      this plan with findings. If AWS has `category=sports/` objects: add AWS path to migration script.

- [x] ✅ [SCRIPT] P1. Run `bash scripts/quality-gates.sh` in market-tick-data-service with new script —
      ruff+basedpyright 0 errors; 22 pre-existing test failures unrelated to this script; coverage 54.45% > 28% floor. —
      mtds@da09d72c

### Phase 0b — VM drain gating (blocks Phase 1)

- [x] ✅ DEFERRED-BLOCKED [INFRA] P0. Confirm Sports VMs stopped before migration:
      `gcloud compute instances list --filter="name~mdps-sports"`. If RUNNING → STOP (per pre-migration drain rule) +
      wait for STOPPED + run manifest consolidator + snapshot to
      `_index/snapshots/pre_sports_hive_migration_20260523.parquet`. DEFERRED 2026-05-23: GCS migration with VM drain
      requires vm-sports coordination; risk of stopping wrong VM. BLK-f3850c56. Assigned to vm-sports per plan header.

### Phase 1 — Hive-rekey migration run (BLOCKED until Phase 0 + 0b complete)

> **GATE**: Phase 0 QG green + Phase 0b sports VMs confirmed STOPPED.

- [ ] [MIGRATION] P0. Dry-run: `python -m market_tick_data_service.scripts.migrate_sports_hive_key --dry-run` — verify
      object count matches expected.

- [ ] [MIGRATION] P0. Execute migration:
      `python -m market_tick_data_service.scripts.migrate_sports_hive_key --workers 32` — run to completion, verify
      `errors_total=0` in summary event.

- [ ] [MIGRATION] P0. Spot-check 3 random days: confirm `asset_group=sports/` objects exist, `category=sports/` objects
      gone. Sample:
      `gsutil ls "gs://market-data-tick-sports-central-element-323112/raw_tick_data/by_date/day=<DATE>/asset_group=sports/"`.

### Phase 2 — Manifest + audit verification

- [ ] [VERIFY] P1. Run manifest consolidator (Cloud Run trigger or wait for scheduled `*/1 * * * *` job) — confirm
      sports manifest rows updated with canonical paths.

- [ ] [VERIFY] P1. Run sports audit checklist item (f): `rg "category=" --include="*.py"` in sports adapter files
      returns 0 hits. Confirm `candidate_parquet_paths()` in UAC uses `asset_group=sports/`.

- [ ] [VERIFY] P1. Update `plans/audit/instructions/sports_master_audit_instructions.md` item (f) with migration
      completion evidence + date.

## Full Execution Criterion

Migration complete = (a) `gsutil ls "gs://market-data-tick-sports-.../day=2024-01-01/category=sports/"` returns
CommandException (no objects), (b) `gsutil ls ".../day=2024-01-01/asset_group=sports/"` returns ≥1 parquet, (c) manifest
consolidator shows `asset_group=sports` rows in consolidated manifest.

## Codex SSOT updates

- `codex/02-data/availability-manifest-and-data-status.md` — update Sports GCS partition key status table.
- `plans/audit/instructions/sports_master_audit_instructions.md` — item (f) migration completion evidence.

## Temporary states + their canonical follow-up plans

- `_mtds_shard_path` in deployment-api falls back to `category=sports/` (deployment-api@9b8e9ad) — stays until this
  migration completes, then fallback path becomes dead code (remove in post-migration cleanup).
