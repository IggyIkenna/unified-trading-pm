---
doc_type: issue
title: Processed-candles storage layout audit — read-amplification + consolidation candidates
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service, market-data-processing-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-27
author: harsh-side phase-1 agent
source: [features_calc_efficiency_and_correctness_2026_05_27.md]
locked_by: live-defi-rollout
---

> **✅ ARCHIVED 2026-05-27 `[unlock-plan]`** — CAPTURED — audit (explicitly 'not a decision'); Task 1.1 in-memory
> resample shipped features@2b20c795; storage-consolidation candidates recorded in
> `plans/active/features_calc_efficiency_and_correctness_2026_05_27.md` (needs-design + blocked-on-migration-window).
>
> Operator-authorized archival 2026-05-27 (issue-doc lifecycle: work shipped or fully captured in a named plan). Lock
> `live-defi-rollout` removed via `[unlock-plan]` in the archival commit.

## What I found

### 1. Per-timeframe object cardinality + byte size

All three asset groups (cefi / defi / tradfi) use the same hive layout:
`processed_candles/by_date/day=YYYY-MM-DD/timeframe={tf}/data_type={dt}/venue={V}/{instrument_id}.parquet`

Measured from live GCS (2026-05-27) against cefi bucket `market-data-tick-cefi-central-element-323112`, defi bucket
`market-data-tick-defi-central-element-323112`, tradfi bucket `market-data-tick-tradfi-central-element-323112`.

#### CeFi (BITGET-FUTURES, 2026-05-03, `data_type=trades`, BTCUSDT sample)

| timeframe | rows/file | bytes/file (typical) | files/instrument/year |
| --------- | --------- | -------------------- | --------------------- |
| 24h       | 1         | ~11.8 KB             | 365                   |
| 4h        | 6         | ~12.4 KB             | 365                   |
| 1h        | 24        | ~14.2 KB             | 365                   |
| 15m       | 96        | ~20.0 KB             | 365                   |
| 5m        | 288       | ~33 KB               | 365                   |
| 1m        | 1440      | ~96 KB               | 365                   |
| 15s       | 5760      | ~350 KB              | 365                   |

Notes:

- 24h ≈ 11.8 KB (not 6.6 KB as the plan pre-grounded — the grounded number was from an older, sparser layout; current
  MDPS writer includes more columns). Row count confirmed at exactly 1.
- 4h ≈ 12.4 KB / 6 rows, 1h ≈ 14.2 KB / 24 rows — these are near-identical to 24h in bytes but have 6× / 24× more rows
  because of header/footer overhead per parquet file; marginal storage gain from consolidation at this tier.
- 15s ≈ 350 KB / 5760 rows — already fine-grained and the largest daily file; no consolidation benefit.

#### DeFi (UNISWAP_V2-ETHEREUM, 2026-01-24, `data_type=dex_swaps`)

| timeframe | bytes/file (sample) | rows (est.)           |
| --------- | ------------------- | --------------------- |
| 15s       | ~14–50 KB           | varies (sparse pools) |
| 24h       | ~12 KB (est.)       | 1                     |

DeFi pool files are sparse (not all 5760 15s slots have swaps) so 15s file sizes vary widely (11 KB–50 KB in sample).
All 7 timeframes present for recent days (2026-01-24 is the last day in defi bucket as of 2026-05-27). The defi bucket
has 323 day-partitions (vs cefi 457 / tradfi 712).

#### TradFi (CME, NASDAQ, 2026-01-21, `data_type=trades`)

TradFi 24h: e.g. `CME/E1AG6_C7050.parquet` (options chain). TradFi 1h: `NASDAQ:EQUITY:ETHA.parquet`. File sizes not
separately measured but expected to be in the same 12–20 KB range for 24h/1h, ~350 KB for 15s. TradFi has 712
day-partitions going back further (equities have older history than crypto).

**Key confirmed facts:**

- 24h = 1 row/file, ~12 KB; reading 1 year of daily candles = 365 GCS GET requests, ~4.3 MB total data
- 4h = 6 rows/file, ~12 KB; reading 1 year = 365 GCS GET requests
- 15s = 5760 rows/file, ~350 KB; reading 1 year = 365 GCS GET requests

The read-count per year is the same (365) across ALL timeframes — the cost difference is **request latency**, not bytes
(GCS GET ~30–100ms each; 365 GETs = 10–37 seconds of pure latency for one year / one instrument).

### 2. Read-amplification map

Baseline: `_process_feature_group` loop in `batch_handler.py:882-895` (commit 7bd77525) calls
`orchestration_service.process_feature_group(timeframe=out_tf, ...)` once PER output timeframe. Each call leads to
`data_loader.load_candles_with_buffer()` → `_collect_daily_frames()` → one GET per day in the lookback window.

For a delta_one CEFI backfill with `output_timeframes = [15s,1m,5m,15m,1h,4h,24h]`:

- **Base timeframe read** (e.g. `15s`): 1 GET × (buffer_days + 1) days per instrument
- **6 additional TF reads**: 6 GETs × (buffer_days + 1) days per instrument

For a 30-day backfill with a 30-day buffer window, per instrument:

- Today: `7 TFs × 60 days = 420 GETs/instrument` (7BD77525 baseline)
- Minimum: `1 TF × 60 days = 60 GETs/instrument` → 7× improvement possible

For 200 instruments × 420 GETs = **84,000 GETs** (current) vs 12,000 (optimal). At 50ms average GET latency, with no
parallelism: current = 70 min, optimal = 10 min. Even with concurrency this is the budget blower.

### 3. Consolidation candidates (cost/benefit only — NOT a decision)

#### (a) 24h/daily → yearly file per instrument

**Concept:** Instead of `day=2026-05-03/timeframe=24h/.../BTCUSDT.parquet` (1 row), emit
`year=2026/timeframe=24h/.../BTCUSDT.parquet` (365 rows).

- **Read-count delta:** 365 GETs/year → 1 GET/year. For 200 instruments: 73,000 GETs → 200. The biggest gain.
- **Bytes/GET:** 12 KB → 4.3 MB. Still trivial to download.
- **Write-path blast radius:**
  - MDPS writer: `market_data_processing_service/app/core/candle_write_mixin.py` +
    `market_data_processing_service/app/core/output_path_helpers.py::build_processed_candle_path` — the
    `processed_prefix` currently encodes `day=YYYY-MM-DD`. Changing to yearly requires a new prefix template and a new
    write mode (append or overwrite). This is **non-trivial**: live MDPS writes one day at a time; a yearly file must be
    appended-to each day or rewritten, which removes write-idempotency.
  - Manifest shard-granularity SSOT: currently shard = `(date, instrument)`. A yearly file changes the shard atom to
    `(year, instrument)`, requiring downstream manifest consumers (features-service `dependency_checker.py`,
    `LookbackValidator`, `read_availability_index`) to be updated.
  - WriteGate: `_publish_emission_check` is keyed by `(date, feature_group)`. Changing to yearly partitions breaks this.
  - Downstream readers: `data_loader._collect_daily_frames` iterates `current_date += timedelta(days=1)` — this whole
    loop becomes a single read.
- **Single-walk-discipline constraint:** This is a whole-corpus schema/partition key change. Per the HARD RULE in
  `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`, any proposal to rewalk the existing 365×N objects
  must bundle into the Phase 2 scheduled migration window. **Cannot be done outside that window.**
- **Recommendation framing:** `needs-design + blocked-on-migration-window` — biggest read-count gain but requires MDPS
  writer refactor (append semantics) + manifest shard redefinition + migration of existing 24h objects. Must go into a
  scheduled migration slot.

#### (b) 4h/1h/5m/15m → monthly file per instrument

**Concept:** Merge daily files into `month=2026-05/timeframe=4h/.../BTCUSDT.parquet` (~180 rows for 4h).

- **Read-count delta:** 30 GETs/month → 1 GET/month. For a 30-day lookback: 30 → 1 GETs.
- **Bytes/GET:** 4h: 12 KB × 30 = ~360 KB; 1h: ~426 KB; 5m: ~990 KB; 15m: ~600 KB — all fine.
- **Write-path blast radius:** Same issues as (a) — MDPS writer requires append-or-rewrite semantics. Partition key
  changes from `day=` to `month=`. Also affects `_collect_daily_frames` loop.
- **Recommendation framing:** `needs-design + blocked-on-migration-window`.

#### (c) Leave 15s/1m per-day (no change)

- **15s:** 350 KB/day — fine as-is. Reading 30 days of 15s for one instrument = 10.5 MB, reasonable.
- **1m:** 96 KB/day — fine as-is.
- **Recommendation framing:** `no-brainer` — do not change.

### 4. Where the rewrite lands (SSOT files)

**MDPS writer (canonical partition-key construction):**

- `market-data-processing-service/market_data_processing_service/app/core/output_path_helpers.py::build_processed_candle_path`
  — line 53-75. The `processed_prefix` argument carries
  `processed_candles/by_date/day={D}/timeframe={T}/data_type={DT}`. Any partition-key change requires changing the
  caller that builds `processed_prefix`.
- `market-data-processing-service/market_data_processing_service/app/core/candle_write_mixin.py` — calls
  `build_processed_candle_path`; this is where the write-mode (create vs append) would need to change for yearly files.

**Features-service reader:**

- `features-service/features_service/delta_one/app/core/data_loader.py::_collect_daily_frames` — lines 300-335. This
  iterates `current_date += timedelta(days=1)` and calls `_resolve_blob_paths` per day. For consolidated files, this
  loop would become a single read per year/month.
- `features-service/features_service/delta_one/app/core/data_loader.py::_build_blob_path` — lines 513-552. Builds the
  canonical path `processed_candles/by_date/day={D}/timeframe={T}/data_type={DT}/venue={V}/{instrument_id}.parquet`.
  This must be updated for any new partition scheme.

**Manifest shard SSOT:**

- `/codex/02-data/availability-manifest-and-data-status.md` — declares shard atom as `(date, instrument)`. Any partition
  change requires a codex update here.
- `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` — the single-walk-discipline HARD RULE document.

### 5. Recommendation framing (for operator)

| Candidate                              | Tag                                          | Rationale                                                                                                                                                          |
| -------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 24h → yearly                           | `needs-design + blocked-on-migration-window` | Biggest gain (365× read reduction), but MDPS write semantics + manifest shard must change.                                                                         |
| 4h/1h/5m/15m → monthly                 | `needs-design + blocked-on-migration-window` | Good gain (30× for monthly lookbacks), same blast radius as above.                                                                                                 |
| 15s/1m → keep per-day                  | `no-brainer`                                 | Already fine; no benefit from consolidation.                                                                                                                       |
| In-memory resample in features-service | `no-brainer`                                 | Read base TF (15s or 1m) once; OHLC-resample to {5m,15m,1h,4h,24h} in-memory. Eliminates 6/7 reads **today** with zero MDPS changes. This is Task 1.1 of the plan. |

**Operator call needed:** The in-memory-resample path (Task 1.1) is a pure features-service change and is the fastest
path to fixing the 7× read problem. Storage consolidation (a, b) is the correct long-term fix but requires a migration
window. Recommend Task 1.1 ships first; schedule (a)+(b) into the Phase 2 migration window.

## Why it matters

The 7× read amplification caused the 10-min e2e timeout on the features pipeline. The in-memory resample fix (Task 1.1)
reduces this to 1× without any MDPS changes. The storage consolidation candidates are the follow-up optimisation once
the migration window opens.

## Recommended decision

1. **Ship Task 1.1** (in-memory OHLC resample in features-service): 7 reads → 1, zero MDPS changes required.
2. **Defer storage consolidation** until the scheduled Phase 2 migration window — add as a P2 todo in the parent plan
   with `needs-design + blocked-on-migration-window` tag.
3. **No MDPS changes** on this plan's timeline.

## Coverage transparency

- Sampled cefi bucket exhaustively for all 7 timeframes on day=2026-05-03 (BITGET-FUTURES venue).
- Sampled defi bucket for the most recent day available (2026-01-24, UNISWAP_V2-ETHEREUM, dex_swaps).
- Sampled tradfi bucket for the most recent day available (2026-01-21, CME + NASDAQ, trades).
- Did not walk all 457+323+712 day-partitions; extrapolated from samples. Byte sizes may vary ±20% across instruments.
- DeFi + TradFi buckets have **zero** actual parquet objects at the directory level in older prefixes (the `--long` flag
  returns empty unless navigating directly to the instrument file). Confirmed actual objects exist at leaf level.
