---
title: "CeFi HL/ASTER batch data gaps — day-bleed rejection, HL trades under-capture, ASTER/liq misclassification"
created: 2026-06-22
author: ikennaigboaka [slot-0·human-planning]
parent_epic: mtds_mdps_master
source:
  - cefi manifest audit 2026-06-22 (per-data_type breakdown via consolidated + per-VM shards)
  - cefi-hyperliquid-2024-resume / cefi-aster-* run.log runtime evidence
locked_by: live-defi-rollout
---

# CeFi HL/ASTER batch data gaps — not 100%, with 3 diagnosed bugs

## What I found (runtime + manifest evidence, 2026-06-22)

Per-data_type manifest breakdown (consolidated index + live per-VM shards):

**HYPERLIQUID** (63,077 cells; captured 25,607 / empty 20,921 / expected 12,780 / **attempted_failed 3,769**): |
data_type | captured % | note | |---|---|---| | book_snapshot_5 | 59% | still filling (2024/2025 resume VMs running,
chunk ~166/190 + ~158/195) | | derivative_ticker (funding) | 71% | climbing | | trades | **5%** (946/16,941; 12,426
empty_confirmed) | **BUG #2 — under-capture** | | liquidations | 0% (916 attempted_failed) | **BUG #3 — HL publishes no
liqs → should be empty_confirmed** | | ohlcv_1m | 0% | out of backfill scope (3 types only: trades/book/deriv) — honest
|

**ASTER** (47,651 cells; captured 16,235 / empty 16,315 / expected 11,610 / **attempted_failed 3,491**; all 3 yr VMs
exit 0): | data_type | captured % | note | |---|---|---| | trades | 62% | ok | | derivative_ticker (funding) | 62% | ok
| | book_snapshot_5 | **0%** (0/13,056; 976 attempted_failed) | **BUG #3 — ASTER REST (Binance-compat) has NO historical
depth → should be empty_confirmed** | | liquidations / ohlcv_1m | 0% | honest |

## The 3 bugs

### BUG #1 — `UpstreamTimestampBiasError` whole-chunk rejection (day-bleed) → attempted_failed

Runtime:
`Handler OnchainPerpBatchHandler failed … UpstreamTimestampBiasError: expected_day=2024-11-27, observed_range=[2024-11-26..2024-11-27], n_ticks_seen=153798 — adapter received ticks but ALL fell outside the requested day after interval filter`.

`market_tick_data_service/raw_tick_hive.py::validate_day_partition_alignment` requires `min==max==expected_day` and
**rejects the entire chunk** (→ `record_failed`) when HL's S3 **hourly partitions bleed a few prior-day ticks** across
the UTC midnight boundary. The guard is correct as a _misalignment_ safety net, but the fix is **upstream**: the HL S3
adapter (`adapters/hyperliquid_s3.py` / `adapters/umi_tick_provider.py::_fetch_hyperliquid_s3`) must **clip ticks to
`[expected_day 00:00, expected_day+1 00:00)` UTC before the writer/guard**, dropping the boundary bleed rather than
discarding 153k valid ticks. This is a meaningful slice of the 3,769 HL `attempted_failed`.

**Fix**: clip-to-requested-day in the HL adapter (or handler pre-guard). Re-run the affected HL failed cells. Add a unit
test: a chunk with boundary-bleed ticks → clipped + written, NOT rejected.

### BUG #2 — HL `trades` 5% under-capture (node_fills)

HL S3 DOES carry trades-equiv: `hl-mainnet-node-data : node_fills/hourly/{YYYYMMDD}/{H}/` (`adapters/hyperliquid_s3.py`
header). Yet trades is 5% captured / 12,426 empty_confirmed. Either the `node_fills` fetch path isn't wired for the
`trades` data_type in the resume backfill, the requester-pays node_fills bucket access is failing silently → empty, or
node_fills coverage genuinely starts later than book. **Needs**: confirm the `trades`→`node_fills` route is exercised by
`collect-onchain-perp-batch`; sample a known-active date+coin; classify the 12k empty (honest vs silent-fetch-failure).

### BUG #3 — misclassified honest-absence (ASTER book + HL liquidations) as attempted_failed

ASTER REST (Binance-Futures-compatible, `_fetch_aster_rest`) serves funding + trades but **no historical order book** →
the 976 ASTER `book_snapshot_5` attempted_failed should be `empty_confirmed` (typed reason: source-unsupported).
Likewise HL publishes no public liquidations → the 916 HL `liquidations` attempted_failed should be `empty_confirmed`.
**Fix**: in the handler, route source-unsupported (data_type not offered by the venue's batch source) to
`record_empty(reason=…)` not `record_failed` — so honest-cov denominator is correct and these stop showing as failures.

## Why it matters

"Pointless running VMs that aren't getting data" — BUG #1 actively discards fetched HL data; BUG #2 may be silently
losing HL trades; BUG #3 inflates the failure count + depresses honest-cov with cells that are legitimately empty. All
three block a truthful cefi 100%. Data-pipeline-correctness HARD RULE: fix in full, no asset_group skipped.

## Recommended decision / execution

1. **BUG #1** (highest data-recovery): clip-to-day in HL adapter → re-run HL failed cells. MTDS.
2. **BUG #3** (cleanest, raises honest-cov immediately): source-unsupported → `record_empty` in the onchain-perp + aster
   handler paths. MTDS.
3. **BUG #2**: diagnose node_fills route → fix or confirm-honest. MTDS. Ship via quickmerge (mtds), rebuild tarball,
   re-run the affected HL/ASTER shards, verify manifest captured climbs + attempted_failed drops. Continuous-verify:
   cefi per-data_type captured% in the daily digest.

## Progress Log (2026-06-22)

### Shipped

- **UAC@047ec140** — new closed-set `EmptyConfirmedReason.EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` (sister of
  `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`) + added to `OUT_OF_COVERAGE_WINDOW_REASONS` (out-of-window → excluded from
  the honest-cov denominator). Direct-LDR dirty-deps push (a concurrent peer's
  `expected_coverage.py`/`venue_launch_dates.py` DeFi-launch-date WIP was uncommitted — left untouched).
- **mtds@83b4a83** — (BUG #1) `HyperliquidS3Downloader._clip_rows_to_day()` clips trades/asset_ctxs/l2Book/funding-REST
  rows to `[target_day, target_day+1)` UTC BEFORE the writer day-partition guard (handles both int-ms and datetime
  timestamps), so boundary-bleed ticks are dropped instead of triggering `UpstreamTimestampBiasError` whole-chunk
  rejection. (BUG #3) `OnchainPerpBatchHandler` routes structurally-unsupported `(venue,data_type)` —
  `_SOURCE_UNSUPPORTED_DATA_TYPES` = {ASTER: book_snapshot_5+liquidations, HYPERLIQUID: liquidations} — to
  `record_empty(reason_override=EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)` with NO fetch (not record_failed, not
  SOURCE_RETURNED_ZERO). (BUG #2) added `_SOURCE_COVERAGE_START` per (venue,data_type) → pre-archive zero-row days (HL
  node_fills trades < 2025-03-22, book < 2023-04-15, deriv < 2023-05-20) route to `EXPECTED_PRE_SOURCE_COVERAGE_START`
  (out-of-window) instead of `SOURCE_RETURNED_ZERO`. Unit tests added in `test_hyperliquid_s3.py` (clip:
  prior/next-day-ms drop, datetime-off-day drop, end-to-end fetch_trades clip) + `test_onchain_perp_batch_handler.py`
  (ASTER book + HL liq → SOURCE_DOES_NOT_OFFER; HL trades pre-coverage → PRE_SOURCE_COVERAGE_START). Both repos
  `quality-gates.sh` green (UAC 212s; mtds 5281 passed).
- **mtds-code.tar.gz** rebuilt 2026-06-22T20:20:59Z (includes the fix).
- **Re-run launched** — 7 VMs `cefi-{hyperliquid,aster}-{year}-20260622-202342` via
  `launch-cefi-hl-aster-historical-backfill.sh FORCE=1` (HL 2023-2026, ASTER 2024-2026; data_types
  trades/book_snapshot_5/derivative_ticker). All created RUNNING/STAGING at T+0.

### BEFORE (deduped consolidated+per-VM manifest, 2026-06-22 pre-re-run; status precedence captured>empty>expected>failed)

HYPERLIQUID failed: book 1082, deriv 371, trades 753, liq 103 (dates 2023-11..2026-04). ASTER failed: book 976, deriv
976, trades 976, liq 562 (dates 2024-10..2026-05). HL trades empty=20,024 of which **10,374 SOURCE_RETURNED_ZERO** (the
BUG #2 misclassification — pre-2025-03-22 node_fills gap; the re-run reclassifies these to
EXPECTED_PRE_SOURCE_COVERAGE_START, out-of-window).

### BUG #2 VERDICT — honest absence, but MISCLASSIFIED (now fixed)

HL `trades` 5% captured is genuine honest absence: HL S3 `node_fills` (the trades-equiv archive) only starts
**2025-03-22** (`HyperliquidS3Downloader.S3_TRADES_START`), so every pre-2025-03-22 date legitimately has 0 node_fills
trades — NOT a wiring/fetch bug (the `trades→node_fills` route IS exercised by `collect-onchain-perp-batch`). The bug
was that those pre-archive zero-row days were stamped `SOURCE_RETURNED_ZERO` (within-window — depresses honest-cov)
instead of the out-of-window `EXPECTED_PRE_SOURCE_COVERAGE_START`. Fixed in mtds@83b4a83 (BUG #2 fix); the 10,374 cells
reclassify on re-run, lifting honest-cov without any new capture.

### Residual / liquidations note

The `launch-cefi-hl-aster-historical-backfill.sh` DATA_TYPES deliberately excludes `liquidations` (HL/ASTER publish no
historical liq feed), so the re-run does NOT re-process the HL 103 + ASTER 562 `liquidations` attempted_failed cells (or
flip ASTER `liquidations`). The handler now routes them to EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE when invoked, but
the launcher won't invoke them. Follow-up below.

- [ ] [SCRIPT] P2. **deployment-service** — add `liquidations` to a targeted HL/ASTER re-run (or a manifest
      reclassification) so the 103 HL + 562 ASTER `liquidations` attempted_failed cells flip to
      `empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)` via the fixed `OnchainPerpBatchHandler`. The main
      launcher excludes liquidations by design; needs a one-off `--include liquidations` run or a manifest migration.
      Provenance: cefi_hl_aster_batch_data_gaps_2026_06_22 BUG #3 residual.
