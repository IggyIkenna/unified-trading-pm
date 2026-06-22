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

**HYPERLIQUID** (63,077 cells; captured 25,607 / empty 20,921 / expected 12,780 / **attempted_failed 3,769**):
| data_type | captured % | note |
|---|---|---|
| book_snapshot_5 | 59% | still filling (2024/2025 resume VMs running, chunk ~166/190 + ~158/195) |
| derivative_ticker (funding) | 71% | climbing |
| trades | **5%** (946/16,941; 12,426 empty_confirmed) | **BUG #2 — under-capture** |
| liquidations | 0% (916 attempted_failed) | **BUG #3 — HL publishes no liqs → should be empty_confirmed** |
| ohlcv_1m | 0% | out of backfill scope (3 types only: trades/book/deriv) — honest |

**ASTER** (47,651 cells; captured 16,235 / empty 16,315 / expected 11,610 / **attempted_failed 3,491**; all 3 yr VMs exit 0):
| data_type | captured % | note |
|---|---|---|
| trades | 62% | ok |
| derivative_ticker (funding) | 62% | ok |
| book_snapshot_5 | **0%** (0/13,056; 976 attempted_failed) | **BUG #3 — ASTER REST (Binance-compat) has NO historical depth → should be empty_confirmed** |
| liquidations / ohlcv_1m | 0% | honest |

## The 3 bugs

### BUG #1 — `UpstreamTimestampBiasError` whole-chunk rejection (day-bleed) → attempted_failed
Runtime: `Handler OnchainPerpBatchHandler failed … UpstreamTimestampBiasError: expected_day=2024-11-27,
observed_range=[2024-11-26..2024-11-27], n_ticks_seen=153798 — adapter received ticks but ALL fell outside the
requested day after interval filter`.

`market_tick_data_service/raw_tick_hive.py::validate_day_partition_alignment` requires `min==max==expected_day` and
**rejects the entire chunk** (→ `record_failed`) when HL's S3 **hourly partitions bleed a few prior-day ticks** across
the UTC midnight boundary. The guard is correct as a *misalignment* safety net, but the fix is **upstream**: the HL S3
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
2. **BUG #3** (cleanest, raises honest-cov immediately): source-unsupported → `record_empty` in the onchain-perp +
   aster handler paths. MTDS.
3. **BUG #2**: diagnose node_fills route → fix or confirm-honest. MTDS.
Ship via quickmerge (mtds), rebuild tarball, re-run the affected HL/ASTER shards, verify manifest captured climbs +
attempted_failed drops. Continuous-verify: cefi per-data_type captured% in the daily digest.
