---
title:
  "CeFi processed_candles: manifest ↔ file disconnect (manifest claims captured for venues with no files; corpus
  written without/with-stale manifest emission)"
created: 2026-05-25
source:
  - plans/active/features_input_manifest_migration_2026_05_25.md
  - features-service@2965bbda (manifest-driven read migration that surfaced this)
locked_by: live-defi-rollout
status: OPEN — incomplete audit (background agent stalled); needs MTDS/MDPS owner (Ikenna)
priority: P2
---

> **🛑 ROLLOUT-AGENT HOLD (2026-05-26):** harsh-side (operator-directed) is actively working this end-to-end. **Do NOT
> auto-assign / auto-fix / push to LDR.** See `plans/active/_agent_pings.md`.

> **🟦 OPERATOR DECISION LEDGER — 2026-06-01 (Ikenna, recorded slot-1).** This is **manifest-canonicalisation work** —
> SSOT is `cefi_manifest_canonicalisation_2026_06_01.md` and it is **actively held by harsh** (banner above). **Slot 7
> takes NO action here** — no investigation, no implementation, no archive-flip — to avoid colliding with the in-flight
> harsh work. The intended direction (when harsh resumes): investigate MTDS pre-marking of `captured`, then reconcile
> `captured` → `attempted_failed` / `expected_unattempted` for unwritten shards (honest-absence). Recorded for SSOT
> continuity only.

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
