---
title:
  "MDPS tradfi backfill — VM run.log analysis: 4 distinct bugs (non-nullable-OHLC schema reject, 429 empty_confirmed
  writes, instrument_type=UNKNOWN partition mismatch, +cosmetic)"
created: 2026-05-26
source:
  - plans/active/features_service_e2e_pipeline_test_2026_05_26.md (finding A0)
  - VM run.logs gs://deployment-scripts-central-element-323112/vm-logs/mdps-tradfi-{2020,2024,2025}/run.log
locked_by: live-defi-rollout
status: OPEN — needs MDPS owner (Ikenna); blocks tradfi candle reprocess
priority: P2
---

## How this was analysed (transparency)

Stream-grepped (no full download) the 3 substantial `mdps-tradfi` VM `run.log` files — **2020 (1.4 GB), 2024 (2.0 GB),
2025 (1.4 GB)** — via `gcloud storage cat | grep`, capturing error/warning/exception/anomaly lines. (2022-08 + 2025-04
produced no GCS log — launched later, month-only ranges, negligible output.) Counts below are across those 3 logs. These
are the MDPS backfill VMs stopped 2026-05-26 (services killed, VMs kept running — see
`features_service_e2e_pipeline_test_2026_05_26.md` A0-action + `_agent_pings.md`).

## Findings (by severity / volume)

### 🔴 FINDING 1 — Non-nullable OHLC schema REJECTS no-trade candles (DOMINANT: 1,155,231 errors)

`ERROR ❌ SCHEMA_VALIDATION_FAILED: <instrument> <data_type> <tf> - Schema validation failed for processed_candles: Column 'close'/'open'/'high'/'low' has N NaN/null values but is NOT NULLABLE for data_type=trades|ohlcv_1m, category=tradfi`.

- **1.15M** schema-validation rejections across the 3 logs. Per-column (2020 alone): close 443,808 · open 443,132 · low
  370,894 · high 370,894.
- **Root cause = the A0 no-trade-bar NaN colliding with a NON-NULLABLE OHLC schema.** No-trade intervals produce NaN
  OHLC (no forward-fill); the processed_candles schema marks O/H/L/C non-nullable → validation fails → **the candle is
  REJECTED, not written.** So the corpus isn't merely "NaN-filled" — for these shards it is **absent** (explains the
  sparse/zero-object day-partitions seen in the e2e sizing).
- **Fix:** the A0 forward-fill (`o=h=l=c=prev_close, volume=0` on no-trade bars) makes OHLC non-null → passes the
  non-nullable schema. (Do NOT relax the schema to nullable — that would propagate NaN downstream. Forward-fill is the
  correct fix; non-nullable is the right contract.)

### 🔴 FINDING 2 — `empty_confirmed` manifest writes throttled by GCS HTTP 429 (158,747)

`WARNING MDPS canonical_writer: empty_confirmed manifest write failed for <instrument> day=… tf=…: 429 POST https://storage.googleapis.com/upload/storage/v1/b/market-data-tick-tradfi-central-element-323112/o?uploadType=multipart`

- **158,747** HTTP **429 (rate-limit)** failures. MDPS records each genuinely-empty shard as `empty_confirmed`, but it
  writes **per (instrument × day × timeframe)** — for thousands of illiquid CME strikes × days × 7 timeframes that is a
  torrent of tiny writes to the same bucket/manifest objects → GCS 429-throttles → **the empty_confirmed rows are LOST**
  (honest-absence not durably recorded).
- **Fix:** batch the empty_confirmed manifest writes (one batched write per shard-group / per VM, not per-tf-per-day),
  and/or exponential-backoff retry on 429. Composes with the per-VM-shard manifest pattern. Note: writes target the
  **legacy** `market-data-tick-tradfi-central-element-323112` bucket (no `-prd`) — confirm that's intended vs the `-prd`
  canonical.

### 🟠 FINDING 3 — `instrument_type=UNKNOWN` partition vs typed id → StreamingParquetWriter reject (58,432 partition_mismatch / 56,167 chain-streaming write fails)

`ERROR Chain-streaming write failed … StreamingParquetWriter pre-write validation failed: … [partition_mismatch] N row(s) inconsistent with partition_path 'day=…/category=tradfi/venue=CME/instrument_type=UNKNOWN/data_type=ohlcv_Nm': instrument_type mismatch in 'CME:FUTURE:NQ-…': partition declares unknown, id has future; … 'CME:COMBO:WTI': partition declares unknown, id has combo …`

- The partition path is written with **`instrument_type=UNKNOWN`** but the canonical instrument_id carries the real type
  (**FUTURE / COMBO**) → pre-write validation rejects. CME futures + combos (NQ, GC, CL, WTI spreads) affected.
- Likely related to the tradfi instrument-type classification feeding the partition key (the partition writer doesn't
  resolve `instrument_type` from the id). Cross-ref the tradfi instrument-id re-normalization (MDPS@fa39207) — that
  fixed 2-segment legacy ids; this is the partition-key `instrument_type` derivation, a separate gap.
- **Fix:** derive `instrument_type` for the partition path from the canonical id (FUTURE/COMBO/OPTION/…), never write
  `UNKNOWN` when the id is typed.

### ⚪ FINDING 4 — cosmetic / low-priority

- `WARNING faulthandler.dump_traceback failed: fileno` (6,207) — faulthandler can't write under nohup (no TTY).
  Harmless; silence by disabling faulthandler stderr dump in headless VM mode.
- `WARNING ⚠️ TIMESTAMP_DEBUG … ts_col=timestamp_out …` — debug-level, not an error.
- The earlier "1m file with 139,680 rows" observation was NOT corroborated by a distinct log line (the grep hit was a
  coincidental line-number match). Likely a mis-partitioned multi-day accumulation tied to Finding 3 (UNKNOWN partition
  collecting many instruments' rows under one path) — verify during the reprocess, not a separate confirmed bug.

## Why it matters

The tradfi processed_candles corpus is broken three ways at once: (1) most no-trade candles are **rejected** by the
non-nullable schema (1.15M), (2) the honest-absence fallback (`empty_confirmed`) is **throttled away** (158k × 429), and
(3) typed CME futures/combos are **rejected** on a partition `instrument_type=UNKNOWN` mismatch (58k). Net: the corpus
is mostly-absent + manifest is incomplete — consistent with the e2e measurement (CME 15s 100% NaN/absent, 88% of 1m
rejected). Reprocessing must fix all three or it will reproduce the same failures.

## Recommended fix order (all in MDPS — Ikenna territory; coordinate via mtds_mdps_master)

1. **A0 forward-fill** (`o=h=l=c=prev_close, volume=0`, OI/funding=last-value) on no-trade bars → resolves Finding 1
   (non-null OHLC passes schema) and shrinks Finding 2 (fewer empty_confirmed needed).
2. **Batch + backoff the empty_confirmed manifest writes** → resolves Finding 2 (429).
3. **Resolve `instrument_type` for the partition key from the canonical id** → resolves Finding 3.
4. **Timeframe-vs-liquidity scoping** (don't generate 15s for instruments trading a few×/day) → reduces the volume of
   all three at the source.
5. THEN reprocess the full tradfi corpus (~712 days 2020→2026, ~2–4M objects) with VMs running current code.

## Cross-refs

- `plans/active/features_service_e2e_pipeline_test_2026_05_26.md` — finding A0 (no-trade NaN root cause + forward-fill).
- `plans/active/issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md` — sibling CeFi manifest↔file gap.
- `plans/active/_agent_pings.md` — 5 mdps-tradfi VMs stopped (services killed, VMs kept; do not relaunch until fix).
