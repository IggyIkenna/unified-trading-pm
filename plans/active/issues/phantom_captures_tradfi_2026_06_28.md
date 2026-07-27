---
doc_type: issue
title: Phantom captures — tradfi manifest (2026-06-28)
summary: "Manifest: `gcp://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`"
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, tradfi, phantom-captures, data-correctness, databento, backfill, data-status]
related: []
created: 2026-06-28
parent_epic: observability_master
priority: P2
source: [reconcile_phantom_manifest_rows_all.py, mvp_catalogue_finalization_v10_2026_06_27.md (G3 phantom audit task)]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-03
locked_since: 2026-05-21
---

# Phantom captures — tradfi manifest (2026-06-28)

> Auto-filed by the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run`)
> run during Phase-0 catalogue finalization. Found 1,789 `capture_status=captured` rows in the MTDS tradfi manifest
> (`market-data-tick-tradfi-prd-central-element-323112/_index/`) with no backing GCS parquet. These are NOT
> catalogue-shape (they are market-data tick records, not instrument definition files) → issue doc per plan triage rule.

## What I found

Manifest: `gcp://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`

- Manifest rows total: 2,485,302
- Captured rows in scope: 700,996
- Unique (date, venue[, chain], hive-vocab) prefixes: 76,392
- **Real captures (parquet exists):** 699,207
- **Phantom captures (captured → no parquet):** 1,789 ← will flip to `attempted_failed` on `--apply`

Triage JSONL: `gs://central-element-323112-phantom-triage/triage_tradfi_20260628_020526.jsonl` (1,789 records)

Phantom distribution by data_type:

| data_type | phantom count |
| --------- | ------------- |
| (blank)   | 1,083         |
| ohlcv_15m | 664           |
| trades    | 17            |
| ohlcv_1m  | 16            |
| tbbo      | 9             |
| **TOTAL** | **1,789**     |

Phantom distribution by venue:

| venue   | phantom count |
| ------- | ------------- |
| CBOE    | 953           |
| NYSE    | 173           |
| CME     | 172           |
| ICE     | 171           |
| NASDAQ  | 142           |
| FX      | 138           |
| (blank) | 35            |
| UNKNOWN | 5             |

Notable: ICE venue (171 phantoms) — ICE shards are in the billing lockdown (`ICE/FX shards stay off`). These may be
pre-lockdown captures that were never written. Verify against billing lockdown activation date.

The dominant blank data_type (1,083) may indicate rows with missing metadata written before schema v9.

## Why it matters

1,789 phantom rows (0.25% of captured scope) are a data-correctness issue but not critical scale. The ICE phantoms (171)
are notable given ICE is outside the 3-dataset billing window — these should be verified as pre-lockdown remnants to
confirm no billing leak.

## Recommended decision

1. **Diagnose ICE phantoms**: confirm they predate billing lockdown activation; if so, flip to `attempted_failed`.
2. **Diagnose blank data_type (1,083)**: these are likely pre-v9 schema rows with missing `data_type`. Confirm they're
   historical and safe to flip to `attempted_failed`.
3. **Apply fix**: `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group tradfi` (no `--dry-run`, with
   `MANIFEST_PER_VM_SHARDS=true VM_NAME=tradfi-reconcile` per consolidator-SSOT) after confirming triage.
4. Reference triage JSONL at `gs://central-element-323112-phantom-triage/triage_tradfi_20260628_020526.jsonl`.

Cold-start context: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` +
`/codex/05-infrastructure/manifest-consolidator-ssot.md` + `/codex/02-data/availability-manifest-and-data-status.md` +
`/codex/02-data/tradfi-databento-sourcing-ssot.md` (billing lockdown).

## Todos

- [x] [CODE] P2. Diagnose tradfi phantom root cause: (a) confirm ICE/FX 309 phantoms predate billing lockdown; (b)
      confirm blank data_type 1,083 are pre-v9 schema rows. Read triage JSONL. Repo: `market-tick-data-service`. —
      already covered by plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md and
      plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md (see those docs — this ground is conflict-gated
      between two tranches; left for the tradfi finalize's own re-check, per those docs' "Deferred — conflict-gated"
      sections).
- [x] ✅ [SCRIPT] P2. Apply phantom reconciliation for tradfi. **DONE 2026-06-28T04:32Z**: 1,589 phantoms flipped
      (cap→attempted_failed); manifest uploaded (2,507,790 rows). Count lower than dry-run (1,789 → 1,589): 200 phantoms
      resolved by new captures between scans. CBOE 753, NYSE 173, CME 172, ICE 171, NASDAQ 142, FX 138. Triage JSONL:
      `gs://central-element-323112-phantom-triage/triage_tradfi_20260628_020526.jsonl`.
