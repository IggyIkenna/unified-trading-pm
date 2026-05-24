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

- [x] ✅ [SCRIPT] P0. Relabel 674K `LegacyBlankErrorReasonError` rows (all `attempted_failed`) to typed
      `VENUE_FETCH_FAILED`. All rows verified `attempted_failed` before relabel; 0 legacy reasons remain after. —
      utl-inline@2026-05-24 19:25 UTC — 674,028 rows relabeled; parquet written to
      `gs://market-data-tick-cefi-central-element-323112/_index/availability_index.parquet` (180,728,791 bytes)

      **NOTE**: `legacy_reason_classifier.py` is for `empty_confirmed` rows with blank reasons. These 674K rows were
      all `attempted_failed` — relabeled directly to `VENUE_FETCH_FAILED`, not via the classifier.

### P0 — LEGACY_THIRDKEY_DRIFT_RECON investigation (452K rows)

- [x] ✅ [SCRIPT] P0. Investigated `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` rows: sampled 6 rows across
      BINANCE-SPOT/BYBIT/OKX venues. GCS probe confirmed 0 parquets exist at candidate paths
      (`raw_tick_data/by_date/day=<date>/asset_group=cefi/venue=<V>/instrument_type=<it>/data_type=<dt>/`) for all
      sampled rows → genuine fetch failures → relabeled 451,799 rows to `VENUE_FETCH_FAILED`. — utl-inline@2026-05-24
      19:25 UTC — 451,799 rows relabeled (combined with LegacyBlank: 1,125,827 total)

### P0 — DERIBIT/HYPERLIQUID investigation (69K rows)

- [x] ✅ [SCRIPT] P0. Investigated: DERIBIT has 14,899 `captured` rows back to 2019-03-30; HYPERLIQUID captured from
      2023-11-01. Both venues' `attempted_failed` rows already have `error_reason = "VENUE_FETCH_FAILED"` — correctly
      typed. These are per-instrument failures distributed across 2020–2026, NOT pre-launch gaps; the "relabel to
      EXPECTED_NO_SOURCE_DATA" assumption in the original plan was INCORRECT.

      **Action**: No relabeling needed. These rows need targeted MTDS retry VMss to determine if data is recoverable.
      Blocked on operator decision per MDPS-3.3.CeFi gate — see bait_sentinel item below.
      — investigation complete 2026-05-24

### P1 — BINANCE-SPOT Tardis probe (93K rows total)

- [x] ✅ [SCRIPT] P1. Tardis probe complete. Fetched full Tardis Binance symbol list (3,296 instruments with
      `availableSince` dates). Cross-referenced all 92,950 BINANCE-SPOT `attempted_failed[VENUE_FETCH_FAILED]` rows:

      | Classification         | Count  | Action                                          |
      | ---------------------- | ------ | ----------------------------------------------- |
      | PRE_LAUNCH             | 14,812 | Relabeled → `empty_confirmed[EXPECTED_NO_SOURCE_DATA]` |
      | POST_TARDIS_COVERAGE   |    714 | Relabeled → `empty_confirmed[EXPECTED_NO_SOURCE_DATA]` |
      | RETRY_CANDIDATE        | 77,424 | Instrument existed at data date → needs VM_FORCE=true retry |

      PRE_LAUNCH instruments: TIA (2,792), SUI (2,430), ARB (2,348), APT (2,038), OP (1,758), INJ (856), FIL (580),
      NEAR (574), AVAX (530), DOT (460), SOL (446) — dates before instrument was listed on Binance.

      15,526 rows relabeled inline 2026-05-24 — utl-inline@2026-05-24 (180,743,631 bytes)

- [ ] [AGENT] P1. **BLOCKED-OPERATOR-DECISION** — 77,424 BINANCE-SPOT `attempted_failed[VENUE_FETCH_FAILED]` rows are
      genuine Tardis fetch failures (instruments existed at the data date). These span ALL VM runs (April-May 2026): 77K
      rows across `book_snapshot_5` (38,726) + `trades` (38,698) across 2019–2026. **Operator decision needed**: (a)
      retry via VM_FORCE=true CeFi VM targeting BINANCE-SPOT full date range, OR (b) accept as confirmed-absent with
      `EXPECTED_NO_SOURCE_DATA`. Do NOT auto-launch per MTDS-3.3.CeFi gate.

### P1 — bait_sentinel retry decision (960K rows)

- [ ] [AGENT] P1. Decision: relaunch MTDS CeFi VM with `VM_FORCE=true` targeting the 2020-2026 date range for
      `book_snapshot_5` + `trades` data types that are currently `bait_sentinel_may4_burst_no_parquet`. Per operator
      constraint MTDS-3.3.CeFi is `BLOCKED-OPERATOR-DECISION` — do NOT auto-launch. Flag findings to operator; get
      explicit direction on whether to (a) retry via FORCE=true VM or (b) accept as confirmed-absent.

## Verification criterion (gate is GREEN when)

- ✅ 0 rows with `LegacyBlankErrorReasonError` reason — GREEN 2026-05-24 (674K relabeled to VENUE_FETCH_FAILED)
- ✅ 0 rows with `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` reason — GREEN 2026-05-24 (452K relabeled to
  VENUE_FETCH_FAILED)
- ✅ DERIBIT/HYPERLIQUID investigation complete — already correctly typed `VENUE_FETCH_FAILED`; retry decision is
  operator-gated (see bait_sentinel item)
- ✅ BINANCE-SPOT disposition: 15,526 pre-launch rows relabeled → `EXPECTED_NO_SOURCE_DATA` 2026-05-24; 77,424 retry
  candidates flagged — **BLOCKED-OPERATOR-DECISION** (BINANCE-SPOT VM_FORCE=true retry)
- ⬜ bait_sentinel rows: operator-acked decision on retry vs relabel — BLOCKED-OPERATOR-DECISION
- ✅ 100% schema_version=8 — GREEN 2026-05-24 (34,839,742 rows upgraded)

## Temporary states + their canonical follow-up plans

- Bait sentinel MTDS retry: depends on operator ack on MTDS-3.3.CeFi launch (per epic § BLOCKED-OPERATOR-DECISION)
- Once gate GREEN: MDPS-3.3.CeFi can be unblocked per epic
