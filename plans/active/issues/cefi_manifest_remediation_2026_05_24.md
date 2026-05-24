---
title: "CeFi manifest remediation — legacy markers + fresh failures 2026-05-24"
created: 2026-05-24
author: slot-2
source:
  - plans/epics/mtds_mdps_master.md (MTDS-3.2.A-V findings)
parent_epic: mtds_mdps_master
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
assigned_vm: vm-ml
---

# CeFi manifest remediation — 2026-05-24

## What I found

MTDS-3.2.A-V CeFi verify gate run 2026-05-24 against `market-data-tick-cefi-central-element-323112` (34,933,247 total
rows).

v8 schema upgrade **COMPLETED** 2026-05-24 19:08 UTC: 34,839,742 rows upgraded to schema_version=8. Remaining issues:

### Legacy markers (2,086,000 rows, ~6% of manifest)

| error_reason                             | count | action                                                   |
| ---------------------------------------- | ----- | -------------------------------------------------------- |
| `bait_sentinel_may4_burst_no_parquet`    | ~960K | MTDS retry VM_FORCE=true OR relabel SOURCE_RETURNED_ZERO |
| `LegacyBlankErrorReasonError`            | ~674K | Relabeling pass via `legacy_reason_classifier.py`        |
| `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` | ~452K | Investigate → relabel or retry                           |

### Fresh failures (106K rows)

| venue        | count  | data_types                                 | years     | attempted_at | action                          |
| ------------ | ------ | ------------------------------------------ | --------- | ------------ | ------------------------------- |
| BINANCE-SPOT | 15,036 | book_snapshot_5, trades                    | 2020–2026 | 2026-05-06   | Tardis probe → retry or relabel |
| DERIBIT      | 51,730 | book_snapshot_5, derivative_ticker, trades | all       | various      | Relabel EXPECTED_NO_SOURCE_DATA |
| HYPERLIQUID  | ~17K   | various                                    | all       | various      | Relabel EXPECTED_NO_SOURCE_DATA |
| Other        | ~22K   | various                                    | various   | various      | Triage per-venue                |

## Why it matters

The MTDS-3.2.A-V gate blocks `MDPS-3.3.CeFi` CeFi reprocessor VM launch. CeFi reprocessed candles are required for
strategy back-testing. 2.09M legacy rows + 106K fresh failures misrepresent the manifest state — consumers see
`attempted_failed` and skip cells that may be legitimately absent, causing silent data holes.

## Remediation todos

### P0 — LegacyBlankErrorReason relabeling (674K rows)

- [ ] [SCRIPT] P0. Run `legacy_reason_classifier.py` across CeFi manifest to relabel 674K `LegacyBlankErrorReasonError`
      rows to typed `EmptyConfirmedReason` values. Script path:
      `unified-trading-library/unified_trading_library/legacy_reason_classifier.py`. Dry-run first, then apply. Write
      updated parquet back to `market-data-tick-cefi-central-element-323112/_index/availability_index.parquet`.

### P0 — LEGACY_THIRDKEY_DRIFT_RECON investigation (452K rows)

- [ ] [SCRIPT] P0. Investigate `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` rows: sample 20 rows across
      venues/dates/data_types. Determine if GCS parquet exists at candidate paths. If parquet exists → reclassify as
      `captured`. If absent → reclassify as `empty_confirmed[EXPECTED_NO_SOURCE_DATA]` OR queue for Phase-11
      re-backfill.

### P0 — DERIBIT/HYPERLIQUID relabeling (69K rows)

- [ ] [SCRIPT] P0. Relabel 51,730 DERIBIT + ~17K HYPERLIQUID `attempted_failed[VENUE_FETCH_FAILED]` rows to
      `empty_confirmed[EXPECTED_NO_SOURCE_DATA]`. These are expected historical gaps — Deribit was founded 2016 (no data
      before ~2018-Q3) and Hyperliquid launched 2023. All rows pre-date service availability dates. Requires inline
      script writing to parquet.

### P1 — BINANCE-SPOT Tardis probe (15K rows)

- [ ] [SCRIPT] P1. Sample 10 BINANCE-SPOT `VENUE_FETCH_FAILED` rows (book_snapshot_5/trades, scattered years). Check
      Tardis endpoint for those specific (date, symbol) combos. If data absent → relabel as
      `empty_confirmed[EXPECTED_NO_SOURCE_DATA]`. If data present → mark for MTDS retry with `VM_FORCE=true` on a
      targeted date-range VM.

### P1 — bait_sentinel retry decision (960K rows)

- [ ] [AGENT] P1. Decision: relaunch MTDS CeFi VM with `VM_FORCE=true` targeting the 2020-2026 date range for
      `book_snapshot_5` + `trades` data types that are currently `bait_sentinel_may4_burst_no_parquet`. Per operator
      constraint MTDS-3.3.CeFi is `BLOCKED-OPERATOR-DECISION` — do NOT auto-launch. Flag findings to operator; get
      explicit direction on whether to (a) retry via FORCE=true VM or (b) accept as confirmed-absent.

## Verification criterion (gate is GREEN when)

- 0 rows with `LegacyBlankErrorReasonError` reason
- 0 rows with `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` reason
- DERIBIT/HYPERLIQUID rows reclassified as `empty_confirmed` with typed reason
- BINANCE-SPOT disposition determined (retry or relabel)
- bait_sentinel rows: operator-acked decision on retry vs relabel
- 100% schema_version=8 (already GREEN as of 2026-05-24)

## Temporary states + their canonical follow-up plans

- Bait sentinel MTDS retry: depends on operator ack on MTDS-3.3.CeFi launch (per epic § BLOCKED-OPERATOR-DECISION)
- Once gate GREEN: MDPS-3.3.CeFi can be unblocked per epic
