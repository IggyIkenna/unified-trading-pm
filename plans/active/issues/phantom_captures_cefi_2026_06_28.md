---
doc_type: issue
title: Phantom captures — cefi manifest (2026-06-28)
summary: "Manifest: `gcp://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`"
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, cefi, phantom-captures, data-correctness, backfill, data-status, single-walk]
related: [mvp_backfill_cefi_tick_v10_2026_06_27]
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
last_updated: 2026-06-27
locked_since: 2026-05-21
---

# Phantom captures — cefi manifest (2026-06-28)

> Auto-filed by the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run`)
> run during Phase-0 catalogue finalization. Found 13,404 `capture_status=captured` rows in the MTDS cefi manifest
> (`market-data-tick-cefi-prd-central-element-323112/_index/`) with no backing GCS parquet. These are NOT
> catalogue-shape (they are market-data tick records, not instrument definition files) → issue doc per plan triage rule.

## What I found

Manifest: `gcp://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`

- Manifest rows total: 5,037,888
- Captured rows in scope: 2,794,416
- Unique (date, venue[, chain], hive-vocab) prefixes: 260,520
- **Real captures (parquet exists):** 2,781,012
- **Phantom captures (captured → no parquet):** 13,404 ← will flip to `attempted_failed` on `--apply`

Triage JSONL: `gs://central-element-323112-phantom-triage/triage_cefi_20260628_021110.jsonl` (13,404 records)

Phantom distribution by data_type:

| data_type         | phantom count |
| ----------------- | ------------- |
| (blank)           | 9,757         |
| trades            | 2,522         |
| book_snapshot_5   | 490           |
| derivative_ticker | 401           |
| futures_chain     | 223           |
| liquidations      | 9             |
| options_chain     | 2             |
| **TOTAL**         | **13,404**    |

Phantom distribution by venue (top 15):

| venue           | phantom count |
| --------------- | ------------- |
| BYBIT           | 1,993         |
| UPBIT           | 1,824         |
| BINANCE-FUTURES | 1,778         |
| OKX-SWAP        | 1,740         |
| HYPERLIQUID     | 1,628         |
| BINANCE-SPOT    | 1,519         |
| OKX-SPOT        | 863           |
| COINBASE-SPOT   | 852           |
| DERIBIT         | 669           |
| OKX-FUTURES     | 419           |
| BYBIT-FUTURES   | 45            |
| (blank)         | 34            |
| KRAKEN-FUTURES  | 20            |
| COINBASE        | 7             |
| OKX             | 7             |

Notable: blank data_type (9,757 = 72.8% of phantoms) likely represents pre-v9 schema rows where `data_type` was
null/empty. These may be pre-schema-migration historical captures.

## Why it matters

13,404 phantom rows (0.48% of captured scope) mean the cefi availability signal overstates actual data. The cefi
backfill plan (`mvp_backfill_cefi_tick_v10_2026_06_27.md`) will re-run coverage analysis; these phantoms will show as
gaps and the backfill will attempt to fill them — which is correct behavior but should be preceded by flipping them to
`attempted_failed` to keep manifest state honest.

## Recommended decision

1. **Apply fix before cefi backfill**: `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi` (no
   `--dry-run`, with `MANIFEST_PER_VM_SHARDS=true VM_NAME=cefi-reconcile` per consolidator-SSOT) to flip 13,404 phantoms
   to `attempted_failed`. Do this BEFORE the cefi backfill G0 gap analysis.
2. **Diagnose blank data_type (9,757)**: confirm these are pre-v9 schema rows; cross-check the manifest hygiene script's
   `schema_version_not_v9: 349,861` finding from `manifest_hygiene_red_2026_06_28.md`.
3. Reference triage JSONL at `gs://central-element-323112-phantom-triage/triage_cefi_20260628_021110.jsonl`.

Cold-start context: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` +
`codex/05-infrastructure/manifest-consolidator-ssot.md` + `codex/02-data/availability-manifest-and-data-status.md`.

## Todos

- [ ] [SCRIPT] P1. Apply cefi phantom reconciliation (372 rows → `attempted_failed`) after CeFi wave-1 VMs complete.
      **Re-dry-run 2026-06-28T04:31Z (slot-10):** phantom count is NOW **372** (not 13,404 — prior count had false
      positives due to stale UAC path template coverage; `canonical_path_templates` update resolved 13,032 rows). All
      372 real phantoms are HYPERLIQUID: `derivative_ticker`=170, `book_snapshot_5`=114, `trades`=88. Triage JSONL:
      `gs://central-element-323112-phantom-triage/triage_cefi_20260628_043158.jsonl`. **When to run --apply:** AFTER
      wave-1 VMs (BINANCE/OKX/BYBIT/COINBASE-SPOT/UPBIT 2025+2026) reach TERMINATED state. Running while VMs are active
      risks overwriting the consolidator's shard merges (race condition on main index). Command:
      `GCP_PROJECT_ID=central-element-323112 .venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi`
      Repo: `instruments-service`.
- [x] ✅ [CODE] P2. Diagnose blank data_type phantoms (9,757): RESOLVED — these were FALSE POSITIVES. The
      `canonical_path_templates` update in UAC CF-15/V0 now covers the pre-v9 pipeline_mode prefix variants that were
      missing from the hand-list. The re-dry-run confirms: blank data_type phantoms = 0 (all resolved). No code change
      needed. — instruments-service (slot-10 2026-06-28T04:31Z)

## 2026-07-15 corroboration — ⚠️ POSSIBLE CONTRADICTION, exact count 9,757 reappears live 17 days after "RESOLVED"

Triaging a `#data-pipeline-alerts` `DP_RUN_MOSTLY_EMPTY` batch (window 2026-07-14 23:50Z–2026-07-15 00:19Z) turned up a
cefi cell described only as "blank/empty data_type" at **9,757/9,757 attempted_failed (100.0%)** against
`market-data-tick-cefi-prd-central-element-323112`. That count is **byte-identical** to this doc's original 2026-06-28
finding ("blank data_type (9,757 = 72.8% of phantoms)") — which the very next todo above claims was fully RESOLVED as a
false-positive of the phantom-audit tool's `canonical_path_templates` coverage, re-verified down to **0** phantoms the
same day.

This is flagged, not re-diagnosed (read-only manifest-count triage only, no live GCS/manifest query run in this pass) —
but the exact-match recurrence 17 days later is suspicious enough to be worth a real look, for one of a few reasons,
none of them mutually exclusive:

1. The 2026-06-28 fix only re-verified the **phantom-audit tool's own dry-run classification** (i.e., confirmed the TOOL
   no longer flags these 9,757 rows as false-positive phantoms) — it may never have touched whatever ALREADY-WRITTEN
   `attempted_failed` rows exist in the live manifest with a genuinely blank `data_type`. If so, "0 phantoms" and "9,757
   attempted_failed with blank data_type" can both be true simultaneously (the tool stopped mis-flagging CAPTURED rows
   as phantom-captured, but a separate, real population of blank-`data_type` `attempted_failed` rows was never addressed
   and is exactly what the alert's `DP_RUN_MOSTLY_EMPTY` check is now surfacing).
2. Alternatively, a coincidentally-identical count from an unrelated, newly-recurring cause (e.g., a writer regressing
   back to emitting blank-`data_type` rows, mirroring the tradfi CF-7 "aggregate Tier-1 sentinel writer" pattern
   documented in `tradfi_manifest_cf4_source_and_cf7_phantom_gaps_2026_07_07.md`, which found and killed an analogous
   tradfi writer bug).
3. The DP_RUN_MOSTLY_EMPTY alert's "blank/empty data_type" label may not be measuring the same manifest slice this doc's
   `data_type` column phantom-count measured (worth confirming the alert's query definition before assuming (1) or (2)).

**Recommend**: a live re-query of the cefi manifest for
`capture_status='attempted_failed' AND (data_type='' OR data_type IS NULL)` to get a fresh count + venue/date breakdown,
and diff it against this doc's original `triage_cefi_20260628_021110.jsonl` / `triage_cefi_20260628_043158.jsonl` triage
JSONLs to determine which of the 3 explanations above actually holds. Given this doc's own 2026-06-28 resolution claimed
0 remaining and the live alert count now exactly matches the pre-fix number, this reads as a genuine data-correctness
discrepancy worth operator visibility, not routine triage noise — surfacing per the workspace's "big finding" rule (a
"resolved" checkbox whose claimed end-state doesn't hold in production).
