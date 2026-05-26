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

> **🛑 ROLLOUT-AGENT HOLD (2026-05-26):** harsh-side (operator-directed) is actively working all findings here
> end-to-end. **Do NOT auto-assign / auto-fix / push to LDR.** See `plans/active/_agent_pings.md`.

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

#### ✅ RESOLVED (CODE) 2026-05-26 — `market-data-processing-service@b67cddd` (local; push pending golden-day)

**Locked design (operator decision 2026-05-26)** — the "session-grid" model. Per-slot decision, applied centrally by
`BaseCandleAdapter._finalize_session_grid` at the `process_to_candles` boundary (so **batch == live**):

| Slot | Signal | Action |
|---|---|---|
| Real trade | source candle present | **Keep** real OHLCV (a trade proves the market was open — never dropped even if `market_state` mislabels it CLOSED) |
| Open, no trade, after first trade | `market_state != CLOSED` & `idx >= first_trade` | **Forward-fill** `o=h=l=c=prev_close`, `volume=0`, `staleness_seconds` set (last-known price — **zero look-ahead, no backfill**) |
| CLOSED, no trade | `market_state == CLOSED` (weekend/holiday/outside-hours via `MarketStateDetector` + `exchange_calendars`) | **Drop** (untradeable → honest absence, NOT a NaN row) |
| Pre-first-trade, no trade | `idx < first_trade` | **Drop** (no prior observation to carry forward — e.g. far-OTM option that lists intraday) |
| Whole window, zero trades | — | Zero-row output → `record_empty_for_shard` (Path A) |

**Why this and not the alternatives** (operator-confirmed):

- **No backfill anywhere.** Backfill (filling pre-first-trade bars) is what creates the "made millions in backtest, live
  sucks" divergence. Forward-fill only reads the past, identical to what a live trader knows → batch == live.
- **`market_state='closed'` ≠ "illiquid no-trade".** The calendar detector already distinguishes them; we forward-fill
  the open-but-illiquid case and drop only the genuinely-closed case.
- **Session-only (variable-length) grid, not a fixed 1440/96/… grid.** Matches ta-lib/backtrader (a 20-bar SMA spans the
  weekend; it never averages closed bars). features-service already filters `market_state` post-read, so it was already
  discarding closed bars — we now do it honestly at the source instead of shipping NaN.
- **Net:** **no NaN OHLC is ever emitted** → the non-nullable schema passes without being relaxed. Resolves all 1.15M
  rejects at the source.

**Shipped (local commit, unit-validated — 1380 unit tests pass):**

- `app/adapters/base_adapter.py` — `_finalize_session_grid()` (the shared transform; generic field-masking via
  `dataclasses.fields`).
- `app/adapters/cefi/trades_adapter.py` + `app/adapters/tradfi/ohlcv_passthrough.py` — wired at `process_to_candles`
  return.
- `schemas/output_schemas.py` — note linking the non-nullable contract to the finalizer.
- `tests/unit/test_tradfi_adapters.py` — 4 new session-grid regression tests (drop-pre-first-trade, ffill-open-no-trade,
  no-NaN, drop-closed) + 3 updated to the session-grid contract.

**Validation gate (not yet done):** full `quality-gates.sh` + reprocess golden day **CME 2025-01-15** to a `-test`
bucket; confirm SCHEMA_VALIDATION_FAILED + NaN-OHLC are gone before pushing to LDR + flipping this item.

**Adapter coverage (audited 2026-05-26):** `_finalize_session_grid` wired into the 3 single-instrument OHLC adapters
that feed the non-nullable trades/ohlcv schema: `CefiTradesAdapter` (cefi/trades, b67cddd), `TradfiOhlcvPassthroughAdapter`
(tradfi/ohlcv_1m|15m|24h, b67cddd), `TradfiTradesAdapter` (tradfi/trades — CME futures, **7cb5fab**; this was the
primary `data_type=trades` reject source and was missed by b67cddd). Chain adapters (`futures_chain`, `options_chain`)
deliberately NOT wired — they retain the fixed-strike Category-D carry-forward grid (see codex contradiction **B1** below).

- [ ] [P2] **DEFERRED — defi/swap_adapter (dex_swaps) latent same-pattern.** `defi/swap_adapter.py:175` uses the same
  `_fill_empty_candles(fill_method="nan")` fixed grid → if the DeFi candle output schema is non-nullable OHLC it will hit
  the identical SCHEMA_VALIDATION_FAILED reject the moment a DeFi backfill runs at scale (not yet observed — the analysed
  VMs were tradfi-only). DeFi is 24/7 + single-pool, so the session-grid model fits (drop pre-first-swap, ffill open
  no-swap = last AMM price, PIT-safe). **Before wiring:** confirm the defi dex_swaps candle schema OHLC nullability +
  that ffill-between-swaps is the desired pool-price semantic. Provenance: adapter audit during Finding-1 completeness
  pass 2026-05-26. (Sports odds adapters also use `fill_method="nan"` but write the odds schema, not OHLC — not affected.)

## Codex contradictions surfaced (operator decision — 2026-05-26 codex audit)

The codex audit (read-only) found the session-grid model is consistent with the workspace "no NaN placeholders" spine
(the 2026-05-05 1440-NaN pattern is uniformly banned). Two points need an operator call before the codex docs are
rewritten:

- **B1 — options/futures fixed-strike grid.** `codex/02-data/honest-absence-downstream-handling.md` (L627-639,
  operator-flagged "volatility-smile constraint") states vol-surface ML training needs a **fixed-width grid per day**
  with a carry-forward bar for **every active-catalog strike** — including far-OTM strikes that never trade intraday.
  Session-grid's "drop pre-first-trade bars" would drop exactly those. **Resolution applied:** the finalizer is wired
  ONLY into single-instrument adapters, NOT the chain adapters — so options/futures chains keep their fixed-strike
  Category-D grid. Operator: confirm this per-data-type split is what you want (chains = fixed-strike; single-instrument
  series = session-grid).
- **B2 — marker column.** Codex docs describe a `zero_activity=True` boolean + `data_freshness=ZERO_ACTIVITY_BAR` on
  carried-forward bars; the shipped finalizer uses `staleness_seconds` (>0 on ffilled bars) + `trade_count=0`. **Verified
  in code:** `zero_activity` is NOT a `CandleOutput` field and NO downstream consumer reads it (grep clean) — so this is
  codex-doc drift, not a live breakage. The docs should be reconciled to `staleness_seconds`/`trade_count==0` (the real
  markers). Operator: OK to standardise on `staleness_seconds`? (cheap downstream filter = `trade_count==0 & staleness>0`.)

Codex edit priority (pending B1/B2 ack): (1) `06-coding-standards/validation-and-errors.md` §1 Path D; (2)
`02-data/honest-absence-downstream-handling.md` (zero-activity-bar shape L603-657 → SUPERSEDED banner + session-grid);
(3) `02-data/availability-manifest-and-data-status.md` Cat-D rows; (4) `05-infrastructure/live-pipeline-architecture.md`
metric naming; (5) `15-runbooks/features-service-launch-verify.md` (expect variable session-length, fixed-1440 = regression).

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
