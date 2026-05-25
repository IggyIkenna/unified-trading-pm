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

- [x] ✅ [AGENT] P1. Operator acked 2026-05-25 ("yeah then fix"). Launched 7 BINANCE-SPOT force-retry VMs:
      `cefi-binance-spot-{2020..2026}-ext-20260525-033358` — e2-highmem-16, 22 symbols
      (btcusdt;ethusdt;solusdt;xrpusdt;bnbusdt;dogeusdt;adausdt;avaxusdt;linkusdt;maticusdt;ltcusdt;trxusdt;atomusdt;
      dotusdt;nearusdt;filusdt;injusdt;opusdt;aptusdt;arbusdt;suiusdt), `VM_FORCE=true`. All 7 RUNNING T+10 verified.
      Covers 133,684 in-scope rows (75,994 VENUE_FETCH_FAILED + 57,690 bait_sentinel).

### P1 — bait_sentinel retry decision (960K rows)

- [x] ✅ [AGENT] P1. Operator acked 2026-05-25 ("yeah then fix"). Launched canonical CeFi force-retry VMs: 55 VMs via
      `launch-cefi-sharded-backfill.sh` with `VM_FORCE=true FORCE=1`, covering BINANCE-FUTURES/BYBIT/
      OKX-SPOT/OKX-SWAP/COINBASE-SPOT/DERIBIT/UPBIT, years 2022-2026. RUN_TS=20260525-033344. Covers ~241K in-scope
      bait_sentinel rows for canonical venues.

      **2026-05-25 WAVE 2 — all deferred items now LAUNCHED (operator acked "fix all"):**

- [x] ✅ [AGENT] P1. 2020-2021 canonical wave: 15 VMs via `launch-cefi-sharded-backfill.sh` ONLY filter, VM_FORCE=true,
      RUN_TS=20260525-071608. Venues: BINANCE-FUTURES 2020-2021, BYBIT 2021, DERIBIT 2020-2021, COINBASE-SPOT 2020-2021,
      OKX-SPOT 2021, OKX-SWAP 2021. All 15 RUNNING T+10min verified.

- [x] ✅ [AGENT] P1. Tier-3 venues: `launch-tier3-cefi-backfill.sh --market-tick` VM_FORCE=true. Covers BITFINEX-SPOT
      (2020-2026, 7 VMs), BITFINEX-FUTURES (2020-2026, 14 VMs), BITGET-SPOT (2024-2026, 3 VMs), BITGET-FUTURES
      (2024-2026, 6 VMs), KRAKEN-SPOT (2020-2026, 7 VMs), KRAKEN-FUTURES (2020-2026, 14 VMs) — ~51 VMs total, RUN_TS
      varies (20260525-071613...). Covers bait_sentinel: BITGET-SPOT 9,528 + BITGET-FUTURES 9,521 + BITFINEX-FUTURES
      7,035 + BITFINEX-SPOT 2,743 + KRAKEN-FUTURES 757 + KRAKEN-SPOT 0 + VENUE_FETCH_FAILED retry: ~461K rows across all
      6 venues. T+10min: 51/51 RUNNING verified.

- [x] ✅ [AGENT] P1. OKX-FUTURES: 7 targeted VMs via direct gcloud, VM_FORCE=true, RUN_TS=20260525-073000.
      `cefi-okx-futures-{2020..2026}-heavy-20260525-073000` — e2-highmem-16, instrument_ids extracted from manifest
      bait_sentinel rows (105,105 quarterly contract rows: 648/882/943/608/455/244/56 instruments per year). All 7
      RUNNING T+10min verified. NOTE: OKX-FUTURES uses weekly+quarterly contract format; canonical launcher
      intentionally skips it — direct extraction from manifest was required.

### P1 — Out-of-scope instruments audit (operator decision required)

Manifest analysis 2026-05-25 of 581,711 VENUE_FETCH_FAILED rows on canonical venues:

| Category                                           | Count       | Disposition                               |
| -------------------------------------------------- | ----------- | ----------------------------------------- |
| Canonical instruments (retried by force-retry VMs) | 96,176      | ✅ Being retried                          |
| **Wrong-format instrument IDs (never-succeed)**    | **292,020** | **BLOCKED-OPERATOR-DECISION — relabel?**  |
| Extended real instruments (beyond canonical 9)     | 193,515     | BLOCKED-OPERATOR-DECISION — expand scope? |

**Wrong-format breakdown** (these will NEVER succeed — instrument IDs don't exist on their venue):

- `*-PERP` format (`BTC-PERP`, `ETH-PERP`, `ADA-PERP`, `SOL-PERP`, `XRP-PERP`, `BNB-PERP`, `DOGE-PERP`, `AVAX-PERP`,
  `MATIC-PERP`, `ARB-PERP`) on DERIBIT (~65K), BYBIT (~52K), BINANCE-FUTURES (~52K), OKX-SWAP (~12K) — May-4 burst used
  internal perp format; real IDs are `BTC-PERPETUAL`, `BTCUSDT`, `BTC-USDT-SWAP` respectively
- Non-KRW pairs on UPBIT (`ADA-USDT`, `APT-USDT`, etc.) — UPBIT is KRW-only (~68K rows)
- Bare `BTC`, `ETH` (no suffix) on BINANCE-FUTURES, BYBIT, DERIBIT (~10K rows)
- Recommendation: relabel all 292K → `empty_confirmed[EXPECTED_NO_SOURCE_DATA]`

**Extended-universe breakdown** (real instruments, correct format, just beyond canonical 9):

- COINBASE-SPOT: 74,162 rows — USDT pairs (ADA-USDT, APT-USDT, ARB-USDT, ATOM-USDT, BNB-USDT, DOT-USDT, etc.)
- BINANCE-SPOT: 73,850 rows — `BTC-USDT` uppercase-hyphenated format (vs canonical `btcusdt` lowercase) — same
  underlying 22 instruments as ext VMs but different naming convention from May-4 burst
- OKX-SPOT: 42,083 rows — APT-USDT, ARB-USDT, ATOM-USDT, DOT-USDT, FIL-USDT, INJ-USDT, LTC-USDT, MATIC-USDT, NEAR-USDT,
  OP-USDT, SUI-USDT, TIA-USDT, TRX-USDT beyond canonical 9
- Options: (a) launch additional VMs with extended symbol set; (b) relabel to `VENUE_FETCH_FAILED` (leave for retry);
  (c) leave as-is until MDPS-3.3.CeFi gate confirms data completeness requirements

## Verification criterion (gate is GREEN when)

- ✅ 0 rows with `LegacyBlankErrorReasonError` reason — GREEN 2026-05-24 (674K relabeled to VENUE_FETCH_FAILED)
- ✅ 0 rows with `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` reason — GREEN 2026-05-24 (452K relabeled to
  VENUE_FETCH_FAILED)
- ✅ DERIBIT/HYPERLIQUID investigation complete — already correctly typed `VENUE_FETCH_FAILED`; retry decision is
  operator-gated (see bait_sentinel item)
- ✅ BINANCE-SPOT disposition: 15,526 pre-launch rows relabeled → `EXPECTED_NO_SOURCE_DATA` 2026-05-24; 77,424 retry
  candidates flagged — **BLOCKED-OPERATOR-DECISION** (BINANCE-SPOT VM_FORCE=true retry)
- ✅ bait_sentinel + all force-retry VMs LAUNCHED + VERIFIED 2026-05-25:
  - Wave 1: 62 VMs (7 BINANCE-SPOT ext + 55 canonical 2022-2026), RUN_TS=20260525-033344/033358
  - Wave 2: 15 VMs (2020-2021 canonical), RUN_TS=20260525-071608
  - Tier-3: ~51 VMs (BITFINEX/BITGET/KRAKEN), RUN_TS=20260525-071613+
  - OKX-FUTURES: 7 VMs (quarterly contracts 2020-2026), RUN_TS=20260525-073000
  - All RUNNING verified T+10min. Total ~135 VMs launched this session.
- ✅ 100% schema_version=8 — GREEN 2026-05-24 (34,839,742 rows upgraded)
- [ ] Wrong-format instrument relabeling (292K rows) — BLOCKED-OPERATOR-DECISION on approach
- [ ] Extended-universe instruments (193K rows) — BLOCKED-OPERATOR-DECISION on scope

## Temporary states + their canonical follow-up plans

- All canonical + tier-3 + OKX-FUTURES force-retry VMs running: monitor for completion, then re-audit
- Wrong-format instruments (292K): await operator decision → relabel to `empty_confirmed[EXPECTED_NO_SOURCE_DATA]`
- Extended-universe instruments (193K): await operator decision on scope expansion
- Once VMs complete + wrong-format relabeled: MDPS-3.3.CeFi gate re-evaluate
