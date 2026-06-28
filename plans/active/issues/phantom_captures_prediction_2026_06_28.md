---
doc_type: plan
title: "Phantom captures — prediction manifest (2026-06-28)"
created: 2026-06-28
parent_epic: observability_master
assigned_vm: NA
source:
  - reconcile_phantom_manifest_rows_all.py
  - mvp_catalogue_finalization_v10_2026_06_27.md (G3 phantom audit task)
summary: "Manifest: `gcp://market-data-tick-pred-prd-central-element-323112/_index/availability_index.parquet`"
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

# Phantom captures — prediction manifest (2026-06-28)

> Auto-filed by the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py --asset-group prediction --dry-run`)
> run during Phase-0 catalogue finalization. Found 19,482 `capture_status=captured` rows in the MTDS prediction manifest
> (`market-data-tick-pred-prd-central-element-323112/_index/`) with no backing GCS parquet.
> These are NOT catalogue-shape (they are prediction market data records — book_snapshot_5/trades — not instrument
> definition files) → issue doc per plan triage rule.

## What I found

Manifest: `gcp://market-data-tick-pred-prd-central-element-323112/_index/availability_index.parquet`

- Manifest rows total: 679,245
- Captured rows in scope: 37,188
- Unique (date, venue[, chain], hive-vocab) prefixes listed: 3,059
- **Real captures (parquet exists):** 17,706
- **Phantom captures (captured → no parquet):** 19,482 ← will flip to `attempted_failed` on `--apply`

Phantom distribution by data_type (partial — top 2 shown from audit output):

| data_type        | phantom count |
|------------------|--------------|
| book_snapshot_5  | 9,305        |
| trades           | 5,143        |
| (other types)    | ~5,034       |
| **TOTAL**        | **19,482**   |

Note: prediction phantom count (19,482) exceeds real captures (17,706) — meaning more than half of all
"captured" rows in scope are phantoms. This is a significant manifest integrity issue for the prediction AG.

## Why it matters

19,482 phantom rows (52.4% of captured-scope rows) make the prediction availability signal unreliable.
Downstream readers relying on `capture_status=captured` will attempt to read non-existent parquets.
The high ratio of phantoms to real captures suggests a systematic writer failure or manifest/writer 
desynchronisation over a significant historical window.

## Recommended decision

1. **Diagnose root cause**: check prediction fetcher/writer history for the phantom date range. Determine
   if this is a writer failure, a manifest double-booking, or a historical data purge without status update.
2. **Apply fix**: `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group prediction` (no `--dry-run`,
   with `MANIFEST_PER_VM_SHARDS=true VM_NAME=pred-reconcile` per consolidator-SSOT) after `prefix_tpls`
   cover prediction data_type shapes.
3. **Backfill**: if real data gaps exist (fetcher outage), backfill missing prediction shards before flipping
   to `attempted_failed`.

Cold-start context: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` +
`codex/05-infrastructure/manifest-consolidator-ssot.md` +
`codex/02-data/availability-manifest-and-data-status.md`.

## Todos

- [ ] [CODE] P1. Diagnose prediction phantom root cause (19,675 phantoms = 52% of captured scope — systematic failure?).
      Read `codex/02-data/availability-manifest-and-data-status.md` first. Repo: `market-tick-data-service`.
- [x] ✅ [SCRIPT] P1. Apply phantom reconciliation for prediction. **DONE 2026-06-28T04:29Z**: 19,675 phantoms
      flipped (cap→attempted_failed); manifest uploaded (688,494 rows). KALSHI 13,349 + POLYMARKET 6,326.
      Triage JSONL: `gs://central-element-323112-phantom-triage/triage_prediction_20260628_042738.jsonl`.
      Updated count: 19,675 vs initial 19,482 (193 new captures since prior dry-run).
- [ ] [CODE] P2. If real data gaps: backfill missing prediction shards (book_snapshot_5, trades) for affected date range.
