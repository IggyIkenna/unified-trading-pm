---
title:
  "CeFi processed_candles: manifest ↔ file disconnect (manifest claims captured for venues with no files; corpus
  written without/with-stale manifest emission)"
created: 2026-05-25
source:
  - plans/active/features_input_manifest_migration_2026_05_25.md
  - features-service@2965bbda (manifest-driven read migration that surfaced this)
locked_by: live-defi-rollout
status:
  ABSORBED into cefi_manifest_canonicalisation_2026_06_01.md (slot-3, 2026-06-03) — archives when the master's CF-11
  "MTDS processed_candles phantom-captured reconcile" todo is GREEN
priority: P2
---

> **🟩 ABSORBED INTO THE CEFI MASTER — slot-3, 2026-06-03.** Operator moved CeFi end-to-end to slot 3 (harsh out for the
> day). SSOT for this work is now `cefi_manifest_canonicalisation_2026_06_01.md` (the CeFi master orchestrator) §CF-11.
> The earlier ROLLOUT-AGENT HOLD is **LIFTED** (no longer harsh-held). Harsh: ack on return — see
> `plans/active/_agent_pings.md`.
>
> **🔬 ROOT CAUSE CORRECTED — direct `_index` query (slot-3 2026-06-03).** The "manifest claims `captured` for
> processed*candles with no file" framing below is a **category error, not manifest corruption.** The cefi `_index`
> (2,640,864 rows) **already disambiguates surfaces via `data_type`**: RAW tick (`trades` 1.19M etc., `service_name=`
> market-tick-data-service) vs CANDLE (`ohlcv_1m/5m/…`, only **8,715 rows**, mostly market-data-processing-service). The
> observations below cross-checked `processed_candles/` FILES against **`trades`-captured** rows — but a `trades`
> `captured` row (MTDS) correctly means the **RAW** file exists (verified: day=2026-05-02 BITFINEX/BITGET/KRAKEN raw
> `trades` present; those venues have NO `ohlcv` rows). So MTDS writes no phantom candle rows; the
> `reconcile→attempted_failed` fix would wrongly demote correct raw rows. **Real residuals** (now tracked as 3 sub-todos
> in the master §CF-11): (1) read-side contract — candle consumers must key off
> `ohlcv*\*`, not `trades`/`processed_candles/`path (features-service); (2) real partial cefi candle backfill (MDPS); (3) verify MDPS`ohlcv`
> row-vs-file faithfulness. This doc archives when those are GREEN. Diagnosis below retained for context.

## What I found

Surfaced while migrating features-service delta_one to read the v8 availability manifest of the canonical CeFi tick
bucket `gs://market-data-tick-cefi-prd-central-element-323112`.

**Direct, verified observations (2026-05-02, -prd bucket):**

- The manifest marks many venues' `trades` rows `capture_status="captured"` — BITGET, KRAKEN-SPOT (24), KRAKEN-FUTURES
  (2), BITFINEX-FUTURES (9), BITFINEX-SPOT (1) — all `schema_version=8`, `service_name="market-tick-data-service"`,
  `written_at` ~2026-05-07/08, nonzero counts.
- BUT actual `processed_candles/` files exist for **only BITGET-FUTURES + BITGET-SPOT**. KRAKEN/BITFINEX have **zero
  files in any of the 3 buckets** (`-prd`, legacy no-env, `-test`).
- Real venue coverage VARIES by date (1m/trades, -prd): 2026-03-26 = BITGET+UPBIT; 2026-04-10 =
  BINANCE+BITGET+DERIBIT+UPBIT; 2026-05-01/03/04 = **BITGET only**. → backfill looks incomplete/in-progress, yet the
  manifest pre-marks not-yet-written venues `captured`.

**Background-agent lead (PARTIAL — agent stalled, NOT verified, no issue evidence attached):**

- The current canonical writer path is correct (`record_captured` AFTER the file write, single SSOT).
- ~2,957 MDPS rows have no `service_emission_state` and stale dates (≤2026-04-14), suggesting the **production
  processed_candles corpus was written by an OLDER MDPS code path / VM run that bypassed manifest emission** — i.e.
  possibly **backfill VMs running stale (un-pulled) `live-defi-rollout` code**.

The two views converge on a **manifest ↔ file disconnect driven by production code/version drift**, not a simple
"phantom captured row."

## Why it matters

Every downstream consumer that trusts `capture_status` (features-service — now manifest-driven — plus ml-training,
strategy, and the data-status UI) will either (a) try to read files that don't exist (404, as features-service does for
KRAKEN/Bitfinex), or (b) skip real files that have no manifest row. ~42% of manifest-`captured` instruments on the -prd
CeFi bucket for the test date had no file. This blocks the May-23 data-pipeline-correctness gate for CeFi and is the
kind of divergence the `Data Pipeline Correctness Is The Heartbeat` HARD RULE forbids.

## Recommended decision (for MTDS/MDPS owner)

1. Verify whether production CeFi backfill VMs are running current `live-defi-rollout` code (stale-code →
   manifest-emission bypass is the leading hypothesis).
2. Run `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run` to quantify
   divergence across venues/dates exhaustively (the background audit did NOT complete this).
3. Decide: complete the CeFi backfill (process all venues per date) + re-emit manifest rows from the corpus, OR
   reconcile `captured`→`attempted_failed`/`expected_unattempted` for un-written shards.
4. Confirm raw-capture (MTDS) vs processed-candles (MDPS) manifest semantics aren't sharing one `_index` with
   conflicting `capture_status` meaning.

## features-service side (separate, this plan)

features-service reads correctly for data that exists (BITGET validated). A robustness follow-up: treat
manifest-`captured`-but-file-404 as honest-absence (skip + warn) instead of erroring (`NoneType has no len()`). Tracked
in `features_input_manifest_migration_2026_05_25.md`.

## UPDATE — verified 2026-05-25 (corrects the stalled-agent hypothesis)

Verified by reading MDPS code + querying the manifest directly (NOT the stalled agent's guess):

- **MDPS writer is CORRECT.** `market_data_processing_service/io/writer.py:write_candles` → `write_candle_parquet`
  co-emits the parquet AND the `ManifestWriter` row in one call,
  `manifest_service_name="market-data-processing-service"`, returns `None` (no row) on empty input. So MDPS does NOT
  mark `captured` without a file. The earlier "stale MDPS code bypassing emission" lead is **disproved**.
- **The phantom `captured` rows are written by MTDS, not MDPS.** For 2026-05-02 `data_type=trades` `captured`, ALL rows
  (BITGET real + KRAKEN/BITFINEX phantom) have `service_name="market-tick-data-service"`. BITGET has processed_candle
  files; KRAKEN/BITFINEX do not.
- **OPEN (needs MTDS-side trace — do NOT guess):** why does MTDS write `capture_status="captured"` (with row counts) for
  KRAKEN/BITFINEX under `processed_candles/` when no processed file exists? Leading hypotheses to confirm: (a) MTDS
  raw-capture rows and MDPS processed-candle rows share ONE `_index/availability_index.parquet` with conflicting
  `captured` semantics (raw captured ≠ processed available), so a processed-candle consumer over-trusts MTDS raw rows;
  (b) backfill genuinely incomplete and MTDS marks `captured` ahead of MDPS processing. Real venue coverage grows by
  date (2026-04-10 = 5 venues; 2026-05-01/03/04 = BITGET only), consistent with in-progress backfill.
- **features-service handles it safely now** (honest-absence skip via blob_exists; features@c35e5e72) — reads all real
  data, skips phantoms without crashing.

## UPDATE — 2026-05-26 (e2e Phase 0 GCS object-listing — sharper phantom quantification)

Directly listed GCS objects under `processed_candles/by_date/` on the canonical `-prd` CeFi bucket (not just manifest
rows), confirming the disconnect with concrete counts:

- **2026-04-26 / -27 / -28**: manifest marks **17 venues** `captured` (BINANCE/BYBIT/OKX/DERIBIT/COINBASE/HYPERLIQUID/
  KRAKEN/BITGET/BITFINEX/UPBIT/LIGHTER-ZKSYNC/PACIFICA-SOLANA/...) but **ZERO actual processed_candle files exist**.
  Pure phantom rows.
- **2026-05-03**: manifest marks 8 venues `captured`; actual files exist for **4** (BITGET-FUTURES/SPOT real;
  BITFINEX-FUTURES + KRAKEN-FUTURES partial). At the candle source (`timeframe=1m`/`data_type=trades`) only the **48
  BITGET instruments** have files.
- Pattern: recent dates have real files for few venues; late-April dates are fully phantom. Consistent with in-progress
  backfill + MTDS pre-marking `captured` ahead of MDPS processing (hypothesis (b) above).

This is why `features_service_e2e_pipeline_test_2026_05_26.md` Phase 0.5 backfills more venues before the calculators
can be tested across instruments. Still needs the MTDS-side trace (why `captured` is written with no processed file) —
unchanged from the OPEN item above.
