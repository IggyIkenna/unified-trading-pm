---
title: "CeFi HL/ASTER batch data gaps — day-bleed rejection, HL trades under-capture, ASTER/liq misclassification"
created: 2026-06-22
parent_epic: mtds_mdps_master
source:
  - cefi manifest audit 2026-06-22 (per-data_type breakdown via consolidated + per-VM shards)
  - cefi-hyperliquid-2024-resume / cefi-aster-* run.log runtime evidence
locked_by: live-defi-rollout
priority: P2
status: active
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

## BUG #4 — universe capped + impossible-datatype empties (operator audit 2026-06-22)

**Two operator questions resolved by code+GCS trace:**

### (A) ASTER unavailable data_types — keep-LIVE vs DROP
- **ASTER `book_snapshot_5` + `liquidations`**: ASTER's LIVE API is Binance-Futures-compatible WS
  (`wss://fstream.asterdex.com`, confirmed in the IS aster adapter + UAC SCHEMA_VERSIONS) which DOES stream
  `<symbol>@depth` (order book) + `!forceOrder@arr` (liquidations). Batch-historical REST genuinely cannot serve them,
  but LIVE can → **KEEP as LIVE-ONLY data_types**: capture going forward via a native asterdex WS connector; mark them
  live-only so BATCH never attempts → no `empty_confirmed`/`SOURCE_DOES_NOT_OFFER` for the historical batch cells (the
  honest model is "live-only", not "impossible").
- **HYPERLIQUID `liquidations`**: HL publishes NO liquidation feed anywhere — not S3, not REST, not the `/info` WS
  (hyperliquid_s3.py header states this explicitly). → **DROP entirely** (remove from the expected universe + manifest +
  code path) so it becomes a hard system constraint, never an attempt → no empty_confirmed noise.

### (B) Instrument universe is capped at 9 — should be ~100–150 per venue. THREE stacked caps:
1. **MTDS catalogue-reader PATH BUG (keystone).** `engine/cefi_catalog_reader.py::_CATALOG_PREFIX =
   "reference_data/instruments/asset_group=cefi/"` — that prefix **does not exist** in `instruments-store-cefi-prd`.
   The real catalogue is `prod/catalog.parquet` (aggregated) + `_catalogue/instruments-service/day=*/` (daily shards).
   So `_load_latest_catalog()` returns None → the reader **falls back to the UAC static ~9-coin seed** (its own
   docstring). FIX: point the reader at `prod/catalog.parquet` (or latest `_catalogue/` day). Instantly lifts the
   attempt universe from 9 → whatever the catalogue holds.
2. **Catalogue enumeration is itself short.** `prod/catalog.parquet` carries only **33 ASTER + 33 HYPERLIQUID**
   instruments (vs the venues' ~100+ ASTER / ~150+ HL perps). The IS adapters DO hit HL `/info` meta (`data.universe`)
   + ASTER `exchangeInfo`, but the CatalogueBuilder output is capped (likely a majors subset / a hardcoded list). FIX:
   make the IS CefI CatalogueBuilder enumerate the FULL exchangeInfo/meta universe with per-instrument
   `available_from_datetime`/`available_to_datetime` (a one-off "fetch all symbols + probe earliest funding date"
   bootstraps the lifecycle windows for history; live/forward stays meta-driven).
3. **Backfill launcher static-9.** `launch-cefi-hl-aster-historical-backfill.sh` passes a hardcoded
   `SYMBOLS=BTC;ETH;SOL;XRP;BNB;DOGE;ADA;AVAX;LINK`. FIX: drive the backfill universe from the catalogue (post-fix #1),
   not the static list — so all instruments (funding rates for small coins included) are attempted.

**Net**: funding rates (valuable even for small/illiquid instruments) for ~90 ASTER + ~120 HL instruments are currently
NOT captured at all (not even expected_unattempted). Fixing #1 (reader path) is the keystone; #2 (full enumeration) +
#3 (catalogue-driven backfill) complete it; (A) keeps ASTER book/liq live + drops HL liq.

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

- [x] ✅ [SCRIPT] P2. **deployment-service** — made `DATA_TYPES` env-overridable in
      `launch-cefi-hl-aster-historical-backfill.sh` (deployment-service@62cbb72) + launched a targeted
      `DATA_TYPES=liquidations FORCE=1` re-run (7 VMs `cefi-{hl,aster}-{year}-20260622-202736`) so the HL 103 + ASTER
      562 `liquidations` attempted_failed cells flip to `empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)` via
      the fixed `OnchainPerpBatchHandler` structural-unsupported path. Provenance: BUG #3 residual.

## BUG #4 Progress Log (2026-06-23)

### Code shipped (continued the prior interrupted WIP — assessed, completed, gated, shipped)

- **mtds@d43fd62** — BUG #4 keystone + (A) + (B): (1) `engine/cefi_catalog_reader.py` reads the REAL catalogue
  (`{env}/catalog.parquet`, prod/staging/dev probe order) via `download_bytes`, NOT the never-populated
  `reference_data/instruments/asset_group=cefi/` prefix → no more fall-back to the 9-coin UAC seed; accepts both the
  canonical `build_instrument_catalogue.py` schema (`instrument_id`/`available_from`/…) and the legacy CatalogueBuilder
  column names. (2) `cli/handlers/onchain_perp_batch_handler.py` — `ALL` sentinel → `_resolve_venue_symbols` →
  `_catalogue_symbols_for_venue` enumerates the FULL per-venue active-perp universe from the catalogue (falls back to
  static defaults only if unreadable — never zeroes the backfill); `_batch_data_types_for_venue` EXCLUDES per-venue
  LIVE-ONLY (ASTER book/liq) + DROPPED (HL liq) data_types from the batch universe entirely (never attempted, never an
  empty cell). Removed the now-dead `_SOURCE_UNSUPPORTED_DATA_TYPES` record_empty path (superseded by the
  exclude-from-universe model). (3) `live/connectors/aster_book_liq_ws.py` (NEW; supersedes `aster_ws.py` which is
  DELETED) — ASTER live WS connectors for trades + book_snapshot_5 (`@depth5@100ms`) + liquidations (`!forceOrder@arr`),
  Binance-compat shape, ASTER-tagged; single venue factory dispatches all three data_types; `connectors/__init__.py`
  registers the new module. (4) Tests rewritten to the new model: `test_onchain_perp_batch_handler.py` (ASTER book / HL
  liq → excluded-not-recorded; `_batch_data_types_for_venue` + catalogue-`ALL` unit coverage), `test_aster_ws_connector.py`
  (book/liq parse + factory dispatch), `test_cefi_pre_listing_not_listed.py` (canonical `prod/catalog.parquet` schema,
  full-universe-not-capped keystone proof). mtds `quality-gates.sh --no-fix` GREEN (whole-tree, peer prediction WIP
  stashed during the gate then restored untouched).
- **instruments-service@6031902** — BUG #4 full enumeration: `aster.py` (exchangeInfo) + `hyperliquid.py` (/info meta)
  drop the `CEFI_BASE_ASSET_UNIVERSE` majors whitelist → every active perp on a canonical quote (ASTER) / every
  non-`isDelisted` perp (HL) is catalogued (funding valuable for small coins). `test_cefi_tradfi_comprehensive.py`
  updated to the full-enumeration contract (obscure base on USDC kept, BTC-quote dropped; HL delisted skipped).
  IS `quality-gates.sh --no-fix` GREEN.

### Lane-isolation notes (peer WIP left untouched, per brief)

- The peer prediction-lane WIP in mtds (`live/_is_universe.py` POLYMARKET clob_token_ids, `kalshi_adapter.py`,
  `test_websocket_runner.py`, `scripts/run_polymarket_v9_rewalk.sh`) is a DIFFERENT lane — NOT shipped here; preserved
  uncommitted in the shared clone (stashed only during my QG run, restored).
- The peer observability-lane WIP in deployment-service (`data_pipeline_monitors/cli.py` + new `launcher_registry.py`,
  `# Epic: observability_master`) is NOT BUG #4 — left untouched.
- **Pre-existing warn-only MTDS adapter-contract regression** flagged by the IS cross-repo gate
  (`lending_indices_handler.py` 5<6, `live/websocket_runner.py` 8<11) — warn-only, did NOT block; outside BUG #4 scope.

### Smoke verification (2026-06-23, pre-migration)

- **IS enumeration (fix #2) PROVEN against live public APIs**: ASTER `exchangeInfo` → **483 active perps**, HYPERLIQUID
  `/info` meta → **178 active perps** (both EXCEED the ~100+/~150+ target; 474 ASTER / 169 HL non-majors now enumerated —
  small/illiquid coins like 1000BONK, 1000PEPE, kPEPE, AIXBT included). The end-to-end IS write path
  (`_write_all_venues`) wrote `{ASTER: 483, HYPERLIQUID: 178}` to
  `instrument_availability/by_date/day=2026-06-22/venue={ASTER,HYPERLIQUID}/instruments.parquet`; the catalogue rollup
  dry-run rolled 223,300 rows (monotonic ACCEPT vs current 222,703).
- **MTDS backfill smoke VM** `cefi-aster-smoke-bug4-20260623-104240` (ASTER, 2026-05-01→31, SYMBOLS=ALL, new tarballs):
  - ✅ **Keystone reader fix confirmed**: `cefi_catalog_reader: loaded 222703 catalogue rows from
    instruments-store-cefi-prd/prod/catalog.parquet` — reads the REAL catalogue, NOT the 9-coin seed fallback.
  - ✅ **Catalogue-driven universe confirmed** (not static-9): `catalogue-driven universe for ASTER on 2026-05-01 = 19
    symbols` (19 = the OLD live catalogue's active-on-2026-05 ASTER count; the NEW 483 lands after the migration promotes
    the rebuilt catalogue — the smoke proves the MECHANISM pre-promote).
  - ✅ **ASTER book_snapshot_5 EXCLUDED from batch** (BUG #4 A): `excluding ASTER/book_snapshot_5 from batch universe
    (live-only) — not attempted` + ZERO ASTER book parquets written.
  - ✅ funding (derivative_ticker) + trades captured for the catalogue universe.
- **HL-liq + ASTER-book/liq manifest purge** (`instruments-service/scripts/purge_cefi_live_only_and_dropped_manifest_rows_2026_06_23.py`,
  one-off): dry-run reports **48,701 stale batch cells to purge** — consolidated index 47,876 (ASTER book 14,827 + ASTER
  liq 14,412 + HL liq 18,637) + per-VM `_legacy_seed` 825 — sweeps consolidated `_index/availability_index.parquet` +
  all `_index/per_vm/` shards via UTL `gcs_*` ops (manifest-row DELETE, not a masking empty write).

### BUG #4 (B) earliest-funding-date probe + ordered migration (2026-06-23)

- **instruments-service@05dc8be** — BUG #4 (B): per-instrument earliest-funding-date probe in both cefi adapters
  (`hyperliquid.py` `fundingHistory startTime=0` genesis entry; `aster.py` Binance-compat `fundingRate` with an explicit
  pre-history `startTime` — `startTime=0` clamps to "recent", so a 2020-01-01 floor returns the ascending genesis) →
  each perp's `available_from_datetime` = its true listing date (bounded concurrency + retry/backoff; UNRESOLVED falls
  back to the venue launch date = the SAFE over-attempt direction, never lost data). `build_instrument_catalogue.py`
  rollup now honours the row's declared `available_from_datetime` as the `available_from` lower bound (MIN of observed
  first-snapshot-day and declared date) — so a perp observed on one recent snapshot still carries its historical window.
  Plus the HL-liq/ASTER-book-liq manifest purge tool. IS `quality-gates.sh --no-fix` GREEN.
- **Probe resolution**: HL 165/178, ASTER ~all resolved (BTCUSDT 2021-08-27, 1000PEPE 2023-05-05, HYPE 2025-09-22,
  AIXBT 2025-01-01, ANIME 2025-01-21, 0G 2025-09-22 — accurate genesis dates).

### Ordered migration EXECUTED (operator infra authority)

- **(a) Catalogue PROMOTED** — `build_instrument_catalogue.py --asset-group cefi` rolled up + promoted
  `instruments-store-cefi-prd/prod/catalog.parquet` (223,300 rows, monotonic ACCEPT). Reader now returns the
  history-accurate universe that GROWS over time: ASTER 82→90→480 / HL 114→135→159→178 across 2024-06 → 2026-06 (was
  capped ~33/33). The 480/178 latest-date universe exceeds the ~100+/~150+ target.
- **(b) MTDS full re-run LAUNCHED** — `launch-cefi-hl-aster-historical-backfill.sh FORCE=1` (SYMBOLS=ALL,
  catalogue-driven) → 7 VMs `cefi-{hyperliquid-2023..2026,aster-2024..2026}-20260623-113700`, all RUNNING; new tarballs
  (mtds@d43fd62, IS-probe@05dc8be). Multi-hour backfill; captured climbs toward the full universe as VMs process. The
  prior `cefi-*-20260622-202342` re-run VMs (old code) left untouched per brief; new RUN_TS → separate per-VM shards.
- **(c) Manifest PURGED** — `purge_cefi_live_only_and_dropped_manifest_rows_2026_06_23.py --apply` removed **48,701**
  stale batch cells (consolidated index 5,272,834 → 5,224,958: ASTER book_snapshot_5 14,827 + ASTER liquidations 14,412
  + HL liquidations 18,637; + per-VM `_legacy_seed` 825). VERIFIED: HL/liquidations = 0, ASTER/book_snapshot_5 = 0,
  ASTER/liquidations = 0 cells in the batch manifest. ASTER book/liq are LIVE-ONLY (the new `aster_book_liq_ws.py` WS
  connector captures them forward); HL liq DROPPED as a hard system constraint.

### Remaining (operational completion in flight)

- The 7-VM full re-run is mid-backfill — captured funding/trades climbing (ASTER deriv 8175→9223+, HL deriv 20736→20929+
  already). Full per-instrument coverage lands when the VMs complete (multi-hour). The catalogue-driven universe means
  every active perp on each date is attempted (small-coin funding history captured).

---

## EXPANDED PROGRAM — full cefi catalogue (ALL venues) + daily-job verification + MTDS run (operator 2026-06-23)

Generalises BUG#4 from {HL,ASTER} to **all cefi venues**. Tardis access re-verified live: SSOT secret **`tardis-api-key`**
(academic-unlimited, 62 venues, genesis 2019 → 2027, `dataPlan:unlimited`); the dup `tardis-api-key-full`/`-backup`
(byte-identical) DELETED. IS Tardis reference-data now uses the **free no-auth** `api.tardis.dev/v1/exchanges/{exchange}`
metadata for enumeration (no key consumed) — shipped instruments-service@`b99e586` (tested no-key enumeration).

**Schedulers ALREADY exist** (both ENABLED): `uts-prod-instruments-cefi-t1-schedule` (06:00 UTC → Cloud Run job
`uts-prod-instruments-service-cefi-t1-recon`, the daily IS fetch → daily shards `_catalogue/instruments-service/day=*/`)
+ `instrument-catalogue-regen-nightly` (02:00 UTC → job `instrument-catalogue-regen`, aggregates daily shards →
`prod/catalog.parquet`). Both jobs currently run image `market-tick-data-service:latest` — the b99e586 no-auth fix
reaches them only after that image rebuilds (resolve at redeploy step P1).

### Gated sequence (each step waits on the prior)

- [ ] [INFRA] P0. **GATE**: HL/ASTER since-genesis re-run (7 VMs `cefi-*-20260623-113700`) completes — captured-coverage
      manifest re-read confirms full per-day universe captured. (Monitored; ~25–60% as of write.)
- [ ] [DEPLOY] P1. **Redeploy the IS no-auth fix (b99e586)** to the catalogue jobs' image so tomorrow's 02:00 + 06:00
      runs use no-key enumeration. Resolve which image the `instrument-catalogue-regen` + `cefi-t1-recon` jobs run
      (currently `market-tick-data-service:latest`) and rebuild/repoint to carry the IS enumeration code.
- [ ] [INFRA] P1. **Manually trigger BOTH IS jobs** (`gcloud run jobs execute uts-prod-instruments-service-cefi-t1-recon`
      then `... instrument-catalogue-regen`) AFTER P0+P1 → confirm: daily shards written for ALL cefi venues (full
      symbol universe per venue, not a subset) + `prod/catalog.parquet` aggregated. Verify row count + per-venue symbol
      breadth (binance/bybit/okx[okex-swap]/deribit/kraken/coinbase/... each full universe with available_from/to).
- [ ] [INFRA] P2. **Tomorrow-verify (2026-06-24)**: confirm both schedulers fired on the new day (02:00 + 06:00 UTC) +
      produced fresh shards + aggregate on the new code. Flip only after 100% confirmed.
- [ ] [MTDS] P2. **MTDS run for all cefi/Tardis venues** — since-genesis batch + live, full catalogue-driven universe.
      (Tardis batch billing gate LIFTED — operator paid; access confirmed unlimited.) Year×data_type×venue shard.
- [ ] [MTDS] P2. **Empty/failed re-analysis**: classify which existing `empty_confirmed`/`attempted_failed` cells were
      caused by the prior SMALL (≤33) instrument catalogue vs genuine absence → re-fetch the catalogue-caused ones now
      that the full universe is known.
