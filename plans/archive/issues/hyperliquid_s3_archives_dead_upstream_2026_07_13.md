---
doc_type: issue
title:
  HYPERLIQUID's two public requester-pays S3 archives are genuinely dead/frozen upstream — book_snapshot_5 (l2Book) and
  trades (node_fills) silently return 0 rows for ANY recent day, confirmed via direct S3 `head_object`/`list_objects_v2`
  calls, not a code bug
summary:
  "Triaging `CEFI:HYPERLIQUID:book_snapshot_5`'s force/skip failures in the 2026-07-13 clean re-sweep
  (`data_pipeline_e2e_check_2026_07_10.md` todo 25), a real backfill VM run.log showed `derivative_ticker` (funding, via
  REST fallback) captured 24 real rows for day=2026-07-09 while `book_snapshot_5` silently captured 0 — no error, no
  warning, nothing logged (`HyperliquidS3Downloader.fetch_l2_book`'s per-hour 404/NoSuchKey branch swallows the
  exception with a bare `continue`, never logging). Went directly to AWS S3 with the real `aws-hyperliquid-s3` Secret
  Manager credentials (no VM needed) and confirmed with `head_object`/`list_objects_v2`: the `hyperliquid-archive`
  bucket's `market_data/{date}/{hour}/l2Book/{coin}.lz4` + `asset_ctxs/{date}.csv.lz4` objects exist through 2026-06-04
  and are MISSING for every date checked from 2026-06-05 through 2026-07-09 (today's real date is 2026-07-13); the
  `hl-mainnet-node-data` bucket's `node_fills/hourly/{date}/` trades archive is even more stale — a full un-truncated
  listing shows real date-partitions ONLY from 2025-05-25 through 2025-07-27 and NOTHING after, ~1 year stale. Both
  archives are genuinely dead/discontinued upstream (Hyperliquid stopped publishing to these public buckets), not a lag
  or a code routing bug — every batch-backfill day after these cutoffs will silently return 0 rows for `book_snapshot_5`
  and `trades` regardless of any code fix, because there is no REST fallback for either data type (unlike
  `derivative_ticker`/funding, which has one and keeps working). This is the root cause the prior session's
  `cefi_aster_hyperliquid_bitget_bitfinex_adapter_bugs_2026_07_12.md` (closed/resolved) flagged as an unresolved,
  undistinguished residual for HYPERLIQUID `trades` ('a data_types-ignored dispatch bug ... or an honest fallback-symbol
  absence — not distinguished') — this doc resolves that ambiguity with hard, direct evidence and extends the same root
  cause to `book_snapshot_5`."
status: resolved
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    hyperliquid,
    cefi,
    s3-archive,
    upstream-data-source,
    honest-absence,
    data-correctness,
    observability-gap,
    big-finding,
  ]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    /plans/archive/issues/cefi_aster_hyperliquid_bitget_bitfinex_adapter_bugs_2026_07_12.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    data_pipeline_e2e_check_2026_07_10.md clean re-sweep CEFI cluster triage (2026-07-13),
    real gsutil/run.log evidence,
    direct AWS S3 head_object/list_objects_v2 calls against hl-mainnet-node-data + hyperliquid-archive using the real
    aws-hyperliquid-s3 Secret Manager credential,
  ]
assigned_vm: NA
resolved_by:
  market-tick-data-service@c48096e7 (trades migration) + @01f23b8c/@29db8440/@a813711b (lag classification), real-VM
  verified 2026-07-13
locked_by:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# HYPERLIQUID's public S3 archives are dead upstream — not a code bug

## What was found (real, direct evidence — not inference)

Re-verifying `CEFI:HYPERLIQUID:book_snapshot_5`'s force-leg failure from the 2026-07-13 clean re-sweep
(`mtds-backfill-cefi-pipelinecheck-20260713-113158-954057`, real run.log pulled via
`gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`):

```
2026-07-13 11:34:44,904 INFO HyperliquidS3Downloader: REST API returned 24 funding records for BTC on 2026-07-09
2026-07-13 11:34:49,005 INFO StreamingParquetWriter: uploaded .../data_type=derivative_ticker/BTC-USD@LIN.parquet (24 rows...)
2026-07-13 11:36:12,807 INFO Tier-3 per-instrument sentinel fan-out: venue=HYPERLIQUID dt=book_snapshot_5 date=2026-07-09 rows=1 (expected_instruments=1 captured=0)
2026-07-13 11:36:12,807 INFO Tier-3 per-instrument sentinel fan-out: venue=HYPERLIQUID dt=trades date=2026-07-09 rows=1 (expected_instruments=1 captured=0)
```

`derivative_ticker` (funding) captured 24 real rows via its REST fallback; `book_snapshot_5` and `trades` silently
captured **0**, with **zero log lines** anywhere in the run about the l2Book/trades fetch attempt — no warning, no
error, nothing. Tracing `HyperliquidS3Downloader.fetch_l2_book`/`fetch_trades`
(`market_tick_data_service/adapters/hyperliquid_s3.py`) explains why: both iterate 24 hourly S3 keys per day, and on a
`NoSuchKey`/404/"does not exist" exception the code does a bare `continue` with **no log call at all** (only a non-404
exception logs, at `DEBUG`) — a day where every single hourly key is genuinely missing produces an entirely silent empty
return.

**Direct S3 verification (no VM needed — real `aws-hyperliquid-s3` Secret Manager credential, `boto3`,
requester-pays):**

```python
# hyperliquid-archive bucket (l2Book + asset_ctxs)
20260601  l2Book EXISTS      1,454,487 bytes   (LastModified 2026-06-03)
20260604  l2Book EXISTS
20260605  l2Book MISSING (404)
20260701  l2Book MISSING (404)
20260705  l2Book MISSING (404)
20260709  l2Book MISSING (404)   # this sweep's day
# same MISSING pattern for asset_ctxs/{date}.csv.lz4 on 20260605/20260701/20260705/20260709
# (derivative_ticker only survives via HyperliquidS3Downloader's REST-API fallback on a 404)

# hl-mainnet-node-data bucket (trades / node_fills)
list_objects_v2(Prefix="node_fills/hourly/", StartAfter="node_fills/hourly/2025", Delimiter="/")
  → 64 real date-partitions, EXACTLY 2025-05-25 .. 2025-07-27, IsTruncated=False
list_objects_v2(Prefix="node_fills/hourly/", StartAfter="node_fills/hourly/2026", Delimiter="/")
  → 0 results
```

Today's real date (per this session's own `date -u` + every genuine GCS/Cloud Run timestamp pulled this pass) is
**2026-07-13**. So:

- `hyperliquid-archive` (l2Book + asset_ctxs): real content exists through **2026-06-04**, dead for every date checked
  from **2026-06-05** onward (~5-6 weeks stale as of this finding).
- `hl-mainnet-node-data` (trades/node_fills): real content exists **only 2025-05-25 → 2025-07-27** (a fixed 64-day
  window) and **nothing at all after** — genuinely dead for **~1 year**, not a recent lag.

Neither is a credentials/permissions problem (the `head_object`/`list_objects_v2` calls succeed cleanly and return real
data for the in-range dates using the exact same credential) and neither is a code bug in how the key/prefix is built
(the in-range dates resolve with the identical key format `market_data/{date}/{hour}/l2Book/{coin}.lz4` /
`node_fills/hourly/{date}/{hour}/` the adapter already uses). This is Hyperliquid genuinely having stopped publishing to
these specific public buckets.

## Why `derivative_ticker` (funding) is unaffected but `book_snapshot_5`/`trades` are permanently broken

`HyperliquidS3Downloader.fetch_asset_ctxs` (funding/OI) has a REST-API fallback (`_fetch_funding_via_rest`, via the
`hyperliquid` Python SDK's public `Info` client) that fires automatically whenever the S3 `asset_ctxs/{date}.csv.lz4`
key 404s — which is why funding kept working in the very same run that silently zeroed out book_snapshot_5/trades.
`fetch_l2_book` and `fetch_trades` have **no REST fallback at all** — S3 is their only source. So for ANY day after each
archive's respective dead-date, `book_snapshot_5` and `trades` will keep silently returning 0 rows forever, regardless
of any dispatch/routing fix, until either (a) the archives resume being published (outside this system's control), or
(b) a REST-based historical-data path is built for these two data types (if Hyperliquid's REST API even exposes
historical L2 book snapshots / fills at all — not confirmed in this pass), or (c) this is accepted as a permanent,
honest per-data-type gap for this venue going forward.

## Relationship to `cefi_aster_hyperliquid_bitget_bitfinex_adapter_bugs_2026_07_12.md` (closed, resolved)

That doc's HYPERLIQUID section fixed a real, distinct epoch-ms/nanosecond timestamp-collapse bug
(`market-tick-data-service@db635632`) and, in its own real-VM verification, surfaced this exact residual as an open,
undistinguished question for `trades`: _"trades specifically still shows 0 captured even though derivative_ticker
succeeds in the same run (a data_types-ignored dispatch bug, same class as the already-fixed FX/KRX one, or an honest
fallback-symbol absence — not distinguished, flagged for a dedicated trace)."_ That doc is already closed/resolved (the
timestamp bug it targeted IS fixed and verified) — this is a **new, separate finding** filed fresh rather than reopening
it. This doc supplies the dedicated trace: **it is neither a dispatch bug nor a fallback-symbol absence — it is a dead
upstream archive**, and the same root cause also explains `book_snapshot_5` (this session's actual scope), which that
doc never separately investigated.

## Recommended next steps (not attempted this session — needs an operator/engineering decision, not a quick fix)

1. **Cheap, safe, universally-correct observability fix** (does not require deciding anything about (b)/(c) above):
   `fetch_l2_book`/`fetch_trades` should log at INFO (not silently `continue`) when EVERY hourly key for a day 404s,
   e.g.
   `"HyperliquidS3Downloader: no S3 {l2Book|trades} data for any hour on {date} (archive may be stale/discontinued)"` —
   mirrors the already-shipped `DATABENTO_EMPTY_BUT_VALID` precedent
   (`tradfi_databento_ohlcv_silent_zero_rows_2026_07_12.md`) so a silent zero-row day is visible in the run.log instead
   of indistinguishable from "genuinely queried and found nothing interesting."
2. **Confirm the archives are truly discontinued, not intermittently republished** — a one-off `head_object` scan covers
   only the dates checked in this pass; a wider scan (or a Hyperliquid docs/support check) would confirm whether this is
   permanent.
3. **Decide the honest-absence framing for MVP/coverage purposes**: whether `book_snapshot_5`/`trades` for HYPERLIQUID
   should be reclassified as `EXPECTED_SOURCE_ARCHIVE_DISCONTINUED` (a new, specific empty_confirmed reason, analogous
   to the existing `EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` used for ASTER's book_snapshot_5) rather than silently
   producing `SHARD_INCOMPLETE`/no-report forever.
4. **Investigate whether Hyperliquid's REST API exposes any historical L2-book or fills endpoint** that could replace
   the dead S3 path (unconfirmed either way this pass) — if not, (3) is the only honest framing available.

## Not done this session

No code was changed for this finding (observability-only fix #1 above is safe/small but was not applied — time-boxed
after the CEFI cluster's other real bugs this pass); no attempt was made to distinguish a permanent shutdown from a
possible future republish (item 2); no REST-alternative was investigated (item 4).

## 2026-07-13 (later, independent re-verification pass, HYPERLIQUID:book_snapshot_5 assigned scope) — CORRECTION to the l2Book date range + a major new finding for `trades`

Re-verifying this doc's own claims with fresh, direct `aws s3api head-object` calls (not `gsutil`/boto3 listing —
literal per-hour, per-date HTTP HEAD requests against `hyperliquid-archive`), **the "l2Book dead since 2026-06-05" claim
above is factually wrong** — real, non-empty `l2Book/BTC.lz4` objects exist for EVERY date checked from `20260601`
through `20260629` inclusive (`20260605`/`20260610`/`20260620`/`20260625`/`20260628`/`20260629` all `HeadObject` 200,
hours 0/1/12 checked for each), all with `LastModified` timestamps clustered around **2026-07-01 19:06-19:37 UTC** (a
single batch upload run) — NOT the 2026-06-01/06-04-only picture this doc's item reports. `20260630` onward (through
`20260713`, checked explicitly) is genuinely `404` for the same key shape. **Corrected picture:
`hyperliquid-archive/market_data` is NOT a dead/discontinued archive — it is a real, still-active archive with a rolling
~2-week PUBLISH LAG** (as of this check on 2026-07-13, the freshest available day is 2026-06-29, uploaded in a batch on
2026-07-01). A backfill request for any day within that trailing ~2-week window will honestly find nothing YET (not
"never"), which is architecturally the same shape as this codebase's existing `_SOURCE_COVERAGE_START`
(start-of-archive) gate, just at the ROLLING recent end instead of a fixed historical start — today's
`pipeline_e2e_check` day (2026-07-09) falls inside that lag window, which is why the original force-leg
`book_snapshot_5` failure reproduced. This doesn't change the practical outcome for THIS sweep (2026-07-09 still
genuinely has no data yet either way), but it changes the recommended framing in item 3 above:
`EXPECTED_SOURCE_ARCHIVE_DISCONTINUED` would be the WRONG reason code for `book_snapshot_5` specifically (it isn't
discontinued) — a `EXPECTED_SOURCE_NOT_YET_PUBLISHED`-style rolling-lag reason would be the honest one instead, and any
future backfill of a day older than ~3 weeks ago should be expected to succeed.

**Separately, a major, actionable correction to the `trades`/`node_fills` "permanently dead ~1 year" framing**: the
`hl-mainnet-node-data` bucket has a SIBLING prefix, `node_fills_by_block/hourly/`, that this doc's scan never checked —
and it is genuinely LIVE, current through **today** (`20260713/12.lz4`, `LastModified` within the last hour of this
check, ~26-60MB per hourly file). Downloaded and decompressed a real sample
(`node_fills_by_block/hourly/20260713/12.lz4`): it is real per-BLOCK JSON-lines data
(`{"local_time":..., "block_time":..., "block_number":..., "events": [[address, {"coin":"xyz:SKHX","px":"1249.3","sz":"1.836","side":"B", "time":1783943999804,"dir":"Close Short","closedPnl":"-3.84642","hash":"0x...","tid":8751204920050,"fee":"-0.006881", ...}], ...]}`)
— a genuinely DIFFERENT schema from the old per-symbol `node_fills/hourly/{date}/{hour}/` files
`HyperliquidS3Downloader.fetch_trades` reads (which really did stop at 2025-07-27, confirming that part of this doc's
finding). **This strongly suggests Hyperliquid migrated their public fills archive from `node_fills` to
`node_fills_by_block` around mid-2025 and our adapter was never updated to follow** — meaning `trades` for HYPERLIQUID
is very likely NOT a permanent, un-fixable upstream gap as recommendation (c) above frames it, but a genuine, scoped,
buildable fix: re-point `fetch_trades` at `node_fills_by_block/hourly/{date}/{hour}.lz4`, parse the new
per-block/events-array shape (filter `events` entries by `coin` matching the target symbol, one JSON line per block
rather than one blob per symbol), and re-verify against a real day. Not attempted this pass (a real schema-migration
adapter change, correctly out of scope for a same-pass triage fix) — but this changes recommendation (c) from "accept as
permanent" to "build the `node_fills_by_block` adapter" as the clear next step, ahead of (b)/(c). Recommendation #1 (the
safe INFO-log observability fix) still stands as-is and is unaffected by this correction. (repo:
market-tick-data-service — investigation/correction only, no code changed this pass; real `aws s3api head-object` +
downloaded/decompressed real sample evidence, not inference)

## 2026-07-13 (implementation pass — trades migration + observability + rolling-lag honesty SHIPPED)

All three buildable items from the correction section landed, real-S3-verified (aws-hyperliquid-s3 requester-pays, no VM
needed for the adapter proof):

- **`market-tick-data-service@c48096e7`** (`adapters/hyperliquid_s3.py` + tests):
  - **Archive coverage re-probed** (direct `list_objects_v2`): `node_fills_by_block/hourly/` = 546 date partitions,
    FIRST **2025-07-27**, LAST **2026-07-13** (today) — LIVE. Legacy `node_fills/hourly/` = 2025-05-25..2025-07-27.
    l2Book latest published day probed = **2026-06-29** (confirms the ~2-week rolling lag).
  - **TWO pre-existing legacy-path bugs found by the migration — HL `trades` NEVER captured via this adapter**: the
    legacy prefix was listed with a trailing slash (`node_fills/hourly/{d}/{h}/`) matching zero real `{h}.lz4` keys, and
    the legacy parser assumed a flat dict while real lines are `[address, fill]`.
  - **`fetch_trades` migrated + date-routed** (≤2025-07-27 legacy shape, after → by_block block/events shape), one
    shared `_fill_to_trade_row` → identical canonical schema both paths; epoch-ms preserved (db635632 1970-collapse NOT
    reintroduced). **Real proof**: `fetch_trades(BTC, 2026-07-10)` = **729,174 rows** (by_block); `(BTC, 2025-07-26)` =
    **349,680 rows** (legacy); real `20260710/12.lz4` parses 33,226 BTC + 13,378 ETH events.
  - **Observability (rec #1)**: loud INFO when EVERY hourly key 404s (trades + l2Book), DATABENTO_EMPTY_BUT_VALID style.
    **Rolling-lag hook (rec #3)**: cached `_latest_published_l2_book_date()` probe + public
    `l2_book_day_within_publish_lag(day)`. 93 unit tests pass incl. real-data fixtures.
- **Manifest classification WIRED** (same session, follow-up commit): `onchain_perp_batch_handler._record_empty` now
  consults the lag hook for zero-row `(HYPERLIQUID, book_snapshot_5)` days and stamps **`EXPECTED_SOURCE_DELIVERY_LAG`**
  (existing UAC EmptyConfirmedReason — exact semantic match, chosen over a new member per the prefer-existing rule)
  instead of `SOURCE_RETURNED_ZERO`; 2 regression tests. **`unified-trading-pm@a0cefb6b7`**: the QG closed-set mirror
  was drift-missing this member — added.
- **Residuals**: (1) coverage-denominator decision (operator): `EXPECTED_SOURCE_DELIVERY_LAG` is WITHIN-window, so the
  trailing ~2-week l2Book lag reads as a coverage dip until the archive catches up — moving it OUT-of-window (or a
  dedicated out-of-window reason) is an operator-gated denominator change, deliberately not made unilaterally; (2) QG
  mirror drift: 6 more EmptyConfirmedReason members still absent from KNOWN_REASONS (EXPECTED_NOT_ENOUGH_TVL,
  EXPECTED_CHAIN_AGGREGATE, EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE, EXPECTED_NO_PROVIDER_COVERAGE, EXPECTED_NO_MAPPING,
  EXPECTED_WRITE_GATE_NAN_THRESHOLD_EXCEEDED) — separate mirror-sync fix; (3) `S3_TRADES_START` (2025-03-22) vs real
  legacy start (2025-05-25) left in sync with the handler's `_SOURCE_COVERAGE_START` mirror — the 03-22..05-24 window
  now at least emits the honest all-404 INFO; (4) real-VM re-verification of a HYPERLIQUID trades force-leg (post
  tarball refresh) is the parent plan's targeted re-run item. Doc kept `open` pending (4); everything else here is
  shipped + QG-green.

## RESOLVED 2026-07-13 — real-VM verification of both data_types

- **trades**: force leg PASSED on a real VM (fresh tarball) — manifest row `captured` for `BTC-USD@LIN`, the FIRST
  successful HL trades capture through this adapter ever (the legacy path was doubly broken; see the implementation
  entry above). `CEFI:HYPERLIQUID:trades | force | passed`.
- **book_snapshot_5**: the identical shard that stamped `SOURCE_RETURNED_ZERO` pre-fix now writes
  `empty_confirmed | EXPECTED_SOURCE_DELIVERY_LAG` (real per-VM shard row, VM
  `mtds-backfill-cefi-pipelinecheck-20260713-200629-954057`) with the loud lag-aware INFO in the run.log — the honest
  classification this doc's recommendation 3 called for. NOTE the classification is emitted by the ORCHESTRATOR Tier-3
  sentinel (mirroring the NASDAQ/NYSE delivery-lag precedent, BLK-d385496b), not the handler — both sites are now wired
  (01f23b8c handler, 29db8440 sentinel).
- Checker-side residual (tracked on the parent plan, not this doc): the MTDS force leg has no honestly-empty-pass path,
  so a lag-window day still _reports_ `no_parquet_under` even when the manifest row is the honest lag classification —
  the MTDS analogue of the IS benign-pass shipped in instruments-service@526d2ffd.
