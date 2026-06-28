---
doc_type: plan
title: "Phantom captures — sports manifest (2026-06-28)"
created: 2026-06-28
parent_epic: observability_master
assigned_vm: NA
source:
  - reconcile_phantom_manifest_rows_all.py
  - mvp_catalogue_finalization_v10_2026_06_27.md (G3 phantom audit task)
summary: "Manifest: `gcp://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`"
status: active
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Phantom captures — sports manifest (2026-06-28)

> Auto-filed by the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py --asset-group sports --dry-run`)
> run during Phase-0 catalogue finalization. Found 27,593 `capture_status=captured` rows in the IS sports manifest
> (`instruments-store-sports-prd-central-element-323112/_index/`) with no backing GCS parquet.
> These are NOT catalogue-shape (they are sports data records, not instrument definition files) → issue doc per plan triage rule.

## What I found

Manifest: `gcp://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`

- Manifest rows total: 5,942,773
- Captured rows in scope: 519,268
- Unique (date, venue, hive-vocab) prefixes listed: 4,175 unique days
- **Real captures (parquet exists):** 491,675
- **Phantom captures (captured → no parquet):** 27,593 ← will flip to `attempted_failed` on `--apply`

Phantom distribution by data_type (top 7 shown):

| data_type     | phantom count |
|---------------|--------------|
| ODDS          | 26,220       |
| TEAMS         | 448          |
| STANDINGS     | 448          |
| PLAYER_VALUES | 312          |
| FIXTURES      | 163          |
| (blank)       | 1            |
| WEATHER       | 1            |
| **TOTAL**     | **27,593**   |

ODDS dominates (95% of phantoms). These are sports data records (odds feeds, team/standings/fixture updates)
where the manifest recorded a `captured` status but the parquet was never written or was purged.

Note: the axis-9 coverage clip excluded 63,589 pre-launch + 0 known-gap rows from the phantom check.

## Why it matters

27,593 phantom rows mean the sports availability signal shows more data than actually exists on GCS.
Any downstream reader querying `capture_status=captured` for these (date, venue, data_type) combinations
will attempt to read a non-existent parquet. This is a data-correctness issue in the sports manifest.

The ODDS phantom count (26,220) suggests a wholesale fetcher or writer failure on many dates across venues.

## Recommended decision

1. **Diagnose root cause**: compare phantom date range vs sports fetcher operational history. If a fetcher/writer
   outage caused these captures to be logged but never written, treat as `attempted_failed` via `--apply`.
2. **Apply fix**: `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group sports` (no `--dry-run`,
   with `MANIFEST_PER_VM_SHARDS=true VM_NAME=sports-reconcile` per consolidator-SSOT) after `prefix_tpls`
   verified to cover the sports data_type shapes.
3. **Verify**: re-run dry-run post-apply to confirm 0 phantoms.

Cold-start context: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` + 
`codex/05-infrastructure/manifest-consolidator-ssot.md` + 
`codex/02-data/availability-manifest-and-data-status.md`.

## Todos

- [x] ✅ [CODE] P2. Diagnose sports phantom root cause (26,220 ODDS phantoms — fetcher outage or writer failure?).
      Read `codex/02-data/availability-manifest-and-data-status.md` first. Repo: `instruments-service`.
      **DIAGNOSIS 2026-06-28T05:02Z (slot-10)**: Analyzed triage JSONL `triage_sports_20260628_042535.jsonl`.
      - All 27,595 phantoms have blank venue + blank instrument_id (sports aggregated-level rows)
      - ODDS=26,220 | TEAMS=448 | STANDINGS=448 | PLAYER_VALUES=314 | FIXTURES=163
      - Date range: 2018-01-01 → 2026-07-04 (3,060 dates). All `manifest_capture_time` ~2026-05-07
      **ROOT CAUSE**: Decision #6 WIPE — footystats ODDS GCS parquets were deleted in decision #6.
      Manifest rows were left as `captured` (no parquet exists). The IS footystats ODDS capture code
      was also deleted in #6 and the #6-REVERSED plan (2026-06-27) only restored UAC type mapping
      (`unified-api-contracts@c75101be`) but NOT the IS capture code (~1000 lines in footystats.py).
      **This is a code-incomplete-reversal, not a transient outage.** Full diagnosis and fix plan in:
      `plans/active/issues/sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md`
      **Backfill gate**: IS footystats ODDS capture code must be restored BEFORE backfill.
- [x] ✅ [SCRIPT] P2. Apply phantom reconciliation for sports. **DONE 2026-06-28T04:26Z**: 27,595 phantoms
      flipped (cap→attempted_failed); manifest uploaded to GCS. Slight count diff from initial dry-run (27,593
      vs 27,595) due to 2 new manifest rows between scans. Triage JSONL:
      `gs://central-element-323112-phantom-triage/triage_sports_20260628_042535.jsonl`.
