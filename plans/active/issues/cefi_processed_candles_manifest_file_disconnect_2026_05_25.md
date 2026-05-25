---
title: "CeFi processed_candles: manifest ↔ file disconnect (manifest claims captured for venues with no files; corpus written without/with-stale manifest emission)"
created: 2026-05-25
author: harsh (features-input-migration investigation)
source:
  - plans/active/features_input_manifest_migration_2026_05_25.md
  - features-service@2965bbda (manifest-driven read migration that surfaced this)
locked_by: live-defi-rollout
status: OPEN — incomplete audit (background agent stalled); needs MTDS/MDPS owner (Ikenna)
---

## What I found

Surfaced while migrating features-service delta_one to read the v8 availability manifest of the
canonical CeFi tick bucket `gs://market-data-tick-cefi-prd-central-element-323112`.

**Direct, verified observations (2026-05-02, -prd bucket):**

- The manifest marks many venues' `trades` rows `capture_status="captured"` — BITGET, KRAKEN-SPOT (24),
  KRAKEN-FUTURES (2), BITFINEX-FUTURES (9), BITFINEX-SPOT (1) — all `schema_version=8`,
  `service_name="market-tick-data-service"`, `written_at` ~2026-05-07/08, nonzero counts.
- BUT actual `processed_candles/` files exist for **only BITGET-FUTURES + BITGET-SPOT**. KRAKEN/BITFINEX
  have **zero files in any of the 3 buckets** (`-prd`, legacy no-env, `-test`).
- Real venue coverage VARIES by date (1m/trades, -prd): 2026-03-26 = BITGET+UPBIT; 2026-04-10 =
  BINANCE+BITGET+DERIBIT+UPBIT; 2026-05-01/03/04 = **BITGET only**. → backfill looks incomplete/in-progress,
  yet the manifest pre-marks not-yet-written venues `captured`.

**Background-agent lead (PARTIAL — agent stalled, NOT verified, no issue evidence attached):**

- The current canonical writer path is correct (`record_captured` AFTER the file write, single SSOT).
- ~2,957 MDPS rows have no `service_emission_state` and stale dates (≤2026-04-14), suggesting the
  **production processed_candles corpus was written by an OLDER MDPS code path / VM run that bypassed
  manifest emission** — i.e. possibly **backfill VMs running stale (un-pulled) `live-defi-rollout` code**.

The two views converge on a **manifest ↔ file disconnect driven by production code/version drift**, not a
simple "phantom captured row."

## Why it matters

Every downstream consumer that trusts `capture_status` (features-service — now manifest-driven — plus
ml-training, strategy, and the data-status UI) will either (a) try to read files that don't exist (404, as
features-service does for KRAKEN/Bitfinex), or (b) skip real files that have no manifest row. ~42% of
manifest-`captured` instruments on the -prd CeFi bucket for the test date had no file. This blocks the
May-23 data-pipeline-correctness gate for CeFi and is the kind of divergence the
`Data Pipeline Correctness Is The Heartbeat` HARD RULE forbids.

## Recommended decision (for MTDS/MDPS owner)

1. Verify whether production CeFi backfill VMs are running current `live-defi-rollout` code (stale-code →
   manifest-emission bypass is the leading hypothesis).
2. Run `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run` to
   quantify divergence across venues/dates exhaustively (the background audit did NOT complete this).
3. Decide: complete the CeFi backfill (process all venues per date) + re-emit manifest rows from the
   corpus, OR reconcile `captured`→`attempted_failed`/`expected_unattempted` for un-written shards.
4. Confirm raw-capture (MTDS) vs processed-candles (MDPS) manifest semantics aren't sharing one `_index`
   with conflicting `capture_status` meaning.

## features-service side (separate, this plan)

features-service reads correctly for data that exists (BITGET validated). A robustness follow-up: treat
manifest-`captured`-but-file-404 as honest-absence (skip + warn) instead of erroring (`NoneType has no
len()`). Tracked in `features_input_manifest_migration_2026_05_25.md`.
