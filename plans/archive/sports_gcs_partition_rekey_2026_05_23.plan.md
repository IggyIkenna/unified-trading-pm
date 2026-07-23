---
doc_type: plan
title: Sports GCS partition key rekey — category=sports/ → asset_group=sports/
summary:
status: complete
nature: record
asset_group: [sports]
stage: [meta]
repos: [deployment-api, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-23
parent_epic: sports_master
assigned_vm: vm-sports
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
locked_since: 2026-05-23
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Deferred work — none (all items completed)

> Migration was a no-op — GCS bucket already used asset_group=sports/ throughout (verified dry-run 2026-05-24).

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

## Pre-audit findings (2026-05-23) — REVISED 2026-05-24

| Bucket                                                     | Total days | `category=sports/` | `asset_group=sports/`   |
| ---------------------------------------------------------- | ---------- | ------------------ | ----------------------- |
| `market-data-tick-sports-central-element-323112` (GCP prd) | 2139       | **0** (none exist) | ALL (already canonical) |
| `market-data-tick-sports-prd-427895769566` (AWS)           | 0          | n/a (empty bucket) | n/a                     |

**Revised finding (2026-05-24)**: Dry-run confirmed `found=0` across all 2139 days (2020-06-06 → 2026-04-14). Bucket
already uses `asset_group=sports/` throughout — two path structures observed:

- Early data (2020): `day=*/asset_group=sports/data_source=ODDS_API/...`
- Later data: `day=*/pipeline_mode=batch_api_football/asset_group=sports/venue=*/...`

Migration is a no-op — bucket was already canonical. Original GCS audit from 2026-05-23 appears to have been incorrect.

## Phases

### Phase 0 — Pre-migration audit + script write (PARALLEL with Phase 0b)

- [x] ✅ [SCRIPT] P1. Write `market_tick_data_service/scripts/migrate_sports_hive_key.py` — walks
      `day=*/category=sports/`, copies to `day=*/asset_group=sports/`, deletes source, shard-level failure isolation,
      events emitted: `MIGRATE_SPORTS_HIVE_RUN_STARTED` / `MIGRATE_SPORTS_HIVE_DAY_COMPLETED` /
      `MIGRATE_SPORTS_HIVE_RUN_COMPLETED`. Uses UTL `gcs_copy_object`/`gcs_delete_object`. Supports `--dry-run`. —
      mtds@da09d72c, ruff+basedpyright clean
- [x] ✅ [SCRIPT] P1. Update `migrate_sports_canonical.py` docstring + source prefix constant from `category=sports/` →
      `asset_group=sports/` so post-hive-rekey run sees canonical paths. — mtds@224f91da

- [x] ✅ [SCRIPT] P1. Audit AWS sports buckets for `category=sports/` vs `asset_group=sports/` partition key state.
      Findings: `market-data-tick-sports-prd-427895769566` (AWS) is EMPTY (KeyCount=0). No migration needed for AWS. GCP
      PRD bucket is the only one that needs hive-rekey.

- [x] ✅ [SCRIPT] P1. Run `bash scripts/quality-gates.sh` in market-tick-data-service with new script —
      ruff+basedpyright 0 errors; 22 pre-existing test failures unrelated to this script; coverage 54.45% > 28% floor. —
      mtds@da09d72c

### Phase 0b — VM drain gating (blocks Phase 1)

- [x] ✅ [INFRA] P0. Confirm Sports VMs stopped before migration:
      `gcloud compute instances list --filter="name~mdps-sports"`. VERIFIED 2026-05-24: NO `mdps-sports-*` VMs running
      (all TERMINATED). `instr-backfill-sports` is RUNNING but writes to `instruments-store-sports-*` (NOT
      `market-data-tick-sports-*`) — different bucket, no conflict. Gate OPEN.

### Phase 1 — Hive-rekey migration run (BLOCKED until Phase 0 + 0b complete)

> **GATE**: Phase 0 QG green + Phase 0b sports VMs confirmed STOPPED.

- [x] ✅ [MIGRATION] P0. Dry-run: `python -m market_tick_data_service.scripts.migrate_sports_hive_key --dry-run` —
      verify object count matches expected. RESULT 2026-05-24:
      `days_total=2139, found=0, copied=0, deleted=0, errors=0,     elapsed=53.8s`. Bucket already canonical — NO
      migration needed.

- [x] ✅ [MIGRATION] P0. Execute migration: N/A — dry-run confirms 0 objects at `category=sports/` across all 2139 days.
      No migration to run. Full-execution criterion (a) already met: `category=sports/` returns CommandException.

- [x] ✅ [MIGRATION] P0. Spot-check 3 random days: confirm `asset_group=sports/` objects exist, `category=sports/`
      objects gone. — day=2020-06-06: `asset_group=sports/data_source=ODDS_API/` ✓, no `category=sports/` ✓ —
      day=2024-01-01: `pipeline_mode=batch_api_football/asset_group=sports/venue=ODDS_API/` ✓, no `category=sports/` ✓ —
      day=2024-03-15: `pipeline_mode=batch_api_football/asset_group=sports/venue=ODDS_API/` ✓, no `category=sports/` ✓
      Full-execution criterion (b): `asset_group=sports/` ≥1 path — CONFIRMED.

### Phase 2 — Manifest + audit verification

- [x] ✅ [VERIFY] P1. Run manifest consolidator — Cloud Run scheduler fires `*/1 * * * *`; tick-data bucket already
      canonical so no manifest rows changed paths. Sports manifest consolidator verifying existing `asset_group=sports`
      rows (no path change needed).

- [x] ✅ [VERIFY] P1. Sports audit checklist item (f): `rg "category=" --include="*.py"` in sports adapter files
      (`market_interface/adapters/sports/*.py`, `engine/sports_catalog_reader.py`) returns 0 hits. Confirmed.
      `candidate_parquet_paths()` in UAC is for `instruments-store-sports-*` bucket (sports reference data with
      `sports_reference/` prefix) — different bucket, different path structure. GCS tick bucket already canonical.

- [x] ✅ [VERIFY] P1. Update `plans/audit/instructions/sports_master_audit_instructions.md` item (f) — see update below
      (evidence: dry-run 2026-05-24, found=0 across 2139 days; bucket never used category=sports/ in tick data).

## Full Execution Criterion

Migration complete = (a) `gsutil ls "gs://market-data-tick-sports-.../day=2024-01-01/category=sports/"` returns
CommandException (no objects), (b) `gsutil ls ".../day=2024-01-01/asset_group=sports/"` returns ≥1 parquet, (c) manifest
consolidator shows `asset_group=sports` rows in consolidated manifest.

## Codex SSOT updates

- `/codex/02-data/availability-manifest-and-data-status.md` — update Sports GCS partition key status table.
- `plans/audit/instructions/sports_master_audit_instructions.md` — item (f) migration completion evidence.

## Temporary states + their canonical follow-up plans

- `_mtds_shard_path` in deployment-api falls back to `category=sports/` (deployment-api@9b8e9ad) — stays until this
  migration completes, then fallback path becomes dead code (remove in post-migration cleanup).
