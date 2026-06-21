---
title: Kalshi + Polymarket perpetual futures + live CLOB depth/quotes (funding/basis/dispersion arb)
created: 2026-06-20
parent_epic: predictions_master
assigned_vm: human-planning
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
locked_by: live-defi-rollout
priority: P2
status: active
---

# Kalshi + Polymarket perps + live CLOB depth

Operator 2026-06-20: Kalshi (May–Jun 2026, 13 CFTC crypto perps BTC+alts) and Polymarket (Apr 21 2026 beta, crypto+stocks, 10–20x) both launched **perpetual futures**. Add them to the universe, map them, download data — for **basis trades, funding-rate arb, and cross-venue dispersion**. Also: historical prediction data is trades-only, but **live we can record CLOB quotes + depth** — capture + dump it live for proper arb backtesting.

## Architecture decision (HARD)

Kalshi/Polymarket **perps are crypto perpetuals with funding** — NOT prediction YES/NO markets. They belong in the **crypto-perp instrument universe** (alongside Binance/Bybit/OKX/Hyperliquid perps), mapping `BTC-PERP`/`ETH-PERP`/… to the **SAME canonical perp instrument** the CeFi venues use → so funding-rate arb + basis + dispersion work cross-venue out of the box. Do NOT route them through the prediction question-group canonical (that's the separate Kalshi-Q&A-parser work, `instruments_mtds_subset_consistency_remediation_2026_06_17.md`). New venue tokens: `KALSHI_PERP` = `"KALSHI-PERP"` and `POLYMARKET_PERP` = `"POLYMARKET-PERP"` (distinct from prediction `KALSHI`/`POLYMARKET`). Resolved in P0 research — confirmed separate API infra and product lines.

## Phase 0 — API research (verify before building; no false premises)

- [x] [RESEARCH] P0. Document the Kalshi perps API: market/contract list endpoint, trades (historical window), funding-rate endpoint, orderbook/depth (REST + websocket), auth (public read vs RSA-PSS), rate limits. Sources: kalshi.com/perps, help.kalshi.com/collections/19654073, trade-api/v2. Repo: instruments-service (research note in the plan Progress Log, NOT a summary doc). — unified-trading-pm@2026-06-20 (findings below)
- [x] [RESEARCH] P0. Same for Polymarket perps: contract list, trades, funding, CLOB book/depth (REST + ws), auth, limits. Confirm whether perps share the existing Polymarket CLOB/Gamma infra or a new endpoint. Repo: instruments-service. — unified-trading-pm@2026-06-20 (findings below)

## Phase 1 — universe + venue mapping (crypto-perp canonical)

- [x] [UAC] P1. Add KALSHI_PERP + POLYMARKET_PERP venues to the crypto-perp universe + `VENUES_BY_ASSET_GROUP`, with launch dates (Kalshi ~2026-05-29, Polymarket ~2026-04-21) in `venue_launch_dates.py` + `coverage_starts.py`. Map their BTC/ETH/alt perps to the SHARED canonical perp instrument (mirror the CeFi perp instrument universe). Repo: unified-api-contracts. ✅ — unified-api-contracts@(shipped 2026-06-20): venue_constants.py, venue_launch_dates.py, coverage_starts.py, market_data_categories.py, venue_mapping.py, test_get_perp_venues.py
- [x] ✅ [SCRIPT] P1. instruments-service — perp-contract enumerator for both venues SHIPPED (instruments-service@fdc9bad): `KalshiPerpReferenceDataAdapter` (public `GET /markets?status=open&category=Crypto`, cursor-paginated, `InstrumentType.PERPETUAL`, 16 unit tests) + `PolymarketPerpReferenceDataAdapter` scaffold (22 unit tests); wired into `factory.py`/`router.py`; QG green (cov 88.29%). Kalshi live endpoint verified. **Polymarket-perp live endpoint BLOCKED-UPSTREAM** — see next item.
- [ ] [SCRIPT] P1. **Polymarket-perp enumerator — BLOCKED-UPSTREAM-OUTAGE**: the Phase-0-documented beta host `perps-api.polymarket.com` does NOT resolve (verified 2026-06-21; control hosts gamma/clob/api.polymarket.com resolve + 200), and no perp path exists under the resolving hosts (`api.polymarket.com/perps/markets`, `/markets`, `clob/perps/markets`, `gamma/perpetuals` all 404). The scaffold ships with best-effort Phase-0 field names + mocked unit tests; finalize the adapter (confirm field names/pagination) + correct the docstring blocker label (currently BLOCKED-CREDENTIALS → should be the live-endpoint gap) ONCE the operator confirms the current live Polymarket perp beta endpoint. Ping: ikenna_orchestrator/pings/slot_0.md. Repo: instruments-service.

## Phase 2 — historical download (trades) + funding

- [x] ✅ [SCRIPT] P1. market-tick-data-service — perp trades+funding adapters SHIPPED (mtds@88c2f0c + UAC perp-source registration on LDR): `_perp_funding_kalshi_polymarket.py` stage (Kalshi `GET /markets?category=Crypto` → `/markets/{ticker}/funding_rates`, day-windowed, 429/5xx retry, shard-isolated) + `perp_funding_handler.py` wired (`_resolve_pipeline_mode_for_protocol`→`pipeline_mode_for_source`, pre-launch `record_empty(EXPECTED_PRE_VENUE_LAUNCH)` kalshi_perp<2026-05-29 / polymarket_perp<2026-04-21, DEFAULT_PROTOCOLS+chain_map extended); 16 unit tests; QG green (5060 pass, 80.77%). UAC: `PipelineMode.BATCH/LIVE/REPLAY_KALSHI_PERP` + `BATCH/LIVE_POLYMARKET_PERP` + `SOURCE_PRIORITY[(cefi,trades)]+=kalshi_perp,polymarket_perp` (committed LDR). **Kalshi-perp live-ready; Polymarket-perp scaffold BLOCKED-UPSTREAM** (endpoint NXDOMAIN — see enumerator sub-item + slot_0 ping). — 2026-06-21

## Phase 3 — LIVE CLOB depth + quotes (the arb-backtest data)

- [x] ✅ [SCRIPT] P1. market-tick-data-service — perp LIVE CLOB ws connectors SHIPPED (mtds@c487a78 + UAC resolver fix@a6444476): `live/connectors/kalshi_perp_ws.py` (per-ticker `_OrderBook` snapshot+delta, lazy ws, exp-backoff reconnect, registered `KALSHI-PERP`, canonical `book_snapshot` BBO+depth, 37 tests) + `polymarket_perp_ws.py` scaffold (`_ENDPOINT_LIVE=False`, BLOCKED-UPSTREAM, registered `POLYMARKET-PERP`, 28 tests); both in `register_all()`; QG green (5161+65 tests, 81.03%). **UAC FIX**: `live_source_for_venue` perp-venue override (`KALSHI-PERP`→`kalshi_perp` not batch-only `tardis`) — caught + fixed a `live_pipeline_mode_for_venue` ValueError that would have crashed the live runner; regression test added. Kalshi-perp live-ready (`live_kalshi_perp`); Polymarket-perp scaffold BLOCKED-UPSTREAM. — 2026-06-21
- [x] ✅ [SCRIPT] P2. deployment-service — perp CLOB live-recording launcher SHIPPED (deployment-service@86f517d): `scripts/vm/launch-perp-clob-live.sh` — KALSHI-PERP → e2-standard-8 VM (`VM_TASK=mtds-live`/`VM_OPERATION=live_websocket`/`MANIFEST_PER_VM_SHARDS=true`, shard `cefi:KALSHI-PERP:book_snapshot`→slug `cefi-kalshi-perp-book-snapshot`, prefix covered by `mtds-live-cefi-` in vm_zombie_watchdog LONG_LIVED_LIVE), singleton-locked per shard; POLYMARKET-PERP → clean early-exit BLOCKED-UPSTREAM (no doomed VM); live=batch parity (same UAC `book_snapshot`, only pipeline_mode differs live_kalshi_perp vs batch_kalshi_perp); lifecycle marker (Epic predictions_master/permanent). QG green. — 2026-06-21

## Phase 4 — arb wiring

- [x] ✅ [DESIGN] P2. strategy-service — perp funding wired into funding-rate-arb + basis archetypes SHIPPED (strategy-service@31ba481f): `catalog_carry.py` `_CARRY_BASIS_PERP_VENUE_BUNDLES` (10→12) + `_FUNDING_DISPERSION_VENUES` (4→6) += `(kalshi,KALSHI-PERP,USDC)` + `(polymarket,POLYMARKET-PERP,USDC)` (slot tokens from UAC `_PREDICTION_TOKENS`); 8 tests; QG green. POLYMARKET-PERP wired for honest-absence (BLOCKED-UPSTREAM — flows when endpoint recovers, no code change). — 2026-06-21

## Codex SSOT updates

- [x] ✅ [DOCS] P2. codex/02-data — prediction-perps sourcing doc WRITTEN (`prediction-perps-sourcing.md`) + prediction-data-types-catalog.md cross-links it (KALSHI_PERP/POLYMARKET_PERP). Repo: unified-trading-pm. — 2026-06-21

## Progress Log

### 2026-06-21 (PM-3) — LIVE prediction: infra PROVEN end-to-end; capture = design-gap tail (documented)

**Live pipeline is fully wired + proven** (7 sequential never-run-before bugs found+fixed): connector
case-insensitive resolve, bucket kind (market-data-tick-prediction flat key), recorder source-derive,
row_key day->date, Gamma query `condition_ids` (was clob_token_ids -> 422), launcher `_`->`-` VM-name
sanitization, CandleBoundaryCrossedEvent data_type enum (book_snapshot -> book_snapshot_5). The live VM
now runs clean: connector fetches REAL Gamma prices (HTTP 200, no 422), manifest writes per-VM shards
with correct `pipeline_mode=live_polymarket_clob`, candle boundary flushes without error.

**Remaining: capture is `empty_confirmed` (row_count=0) — a DESIGN GAP, not a bug.** The Polymarket
Gamma poller yields a TOP-OF-BOOK quote (yes_price/no_price/best_bid/best_ask/last_trade_price), but no
existing capturable data_type candle-schema matches it: `trades` = actual trades (a price poll has none
-> honest empty), `book_snapshot_5` = depth-5 levels (Gamma gives only top-of-book -> 0-row candle).
Connector yields ticks correctly (verified: _poll_one_cycle -> _parse_market_response -> yield); the
runner's tick->candle aggregator produces 0-row candles because the tick shape doesn't fit the data_type
schema. NOT spin-fixable by relaunching.

- [ ] [DESIGN] P2. **Decide the canonical data_type/schema for Polymarket live Gamma quotes** (top-of-book
  yes/no + best_bid/ask + last_trade_price). Options: (a) a new `prediction_quote` data_type + candle
  schema that captures the quote fields; (b) extend book_snapshot_5 aggregation to accept top-of-book
  (partial depth); (c) use the CLOB websocket (auth) for true depth instead of the Gamma poll. Then wire
  the runner's tick->candle for it so live captures row_count>0. Live INFRA is done; this is the
  capture-schema decision. Repo: market-tick-data-service (runner/sink) + UAC (data_type/schema).
- [ ] [DESIGN] P2. **UAC naming: SOURCE_PRIORITY uses `book_snapshot` but DataType enum uses
  `book_snapshot_5`** (pre-existing mismatch surfaced here). Reconcile to one canonical name across
  SOURCE_PRIORITY + DataType + candidate_parquet_paths. Repo: unified-api-contracts.


### 2026-06-21 (PM-2) — LIVE prediction LAUNCHED (free Gamma poll) + Kalshi seed running

- [x] ✅ [SCRIPT] P1. LIVE prediction is WIRED + launchable end-to-end (no build needed): `polymarket_ws.py`
  + `kalshi_ws.py` live connectors EXIST + auto-register (`connectors/__init__.py` autoload),
  `launch-mtds-live.sh --asset-group prediction --shard-spec prediction:POLYMARKET:trades` exists, and the
  live `MTDSShardManifestRecorder` (fixed: asset_group is a writer kwarg) stamps `live_polymarket_clob` via
  the venue-source map. Polymarket live = free public Gamma REST poll (30s, no auth). **LAUNCHED**
  `mtds-live-prediction-polymarket-trades-20260621-155845` (10 high-volume active markets) → first-ever
  LIVE prediction rows (LIVE=0 across all AGs before this). Repo: deployment-service + market-tick-data-service.
- [ ] [SCRIPT] P2. Expand the live producer instrument set (currently 10 high-vol Polymarket markets) to the
  full IS-enumerated active universe + add a KALSHI live shard (`prediction:KALSHI:trades`, kalshi_ws). Repo:
  deployment-service.


### 2026-06-21 — ROOT GAP: Kalshi was never a registered canonical UAC source → registered it (batch=live)

**Discovery (autonomous prediction-to-100% drive):** while wiring the bulk-seed converter's manifest emission, found
that **Kalshi was never registered as a canonical source in UAC at all** — `PipelineMode.BATCH_KALSHI` did not exist, no
`EMISSION_LATENCY_MS_BY_SOURCE["kalshi"]`, no `SOURCE_PRIORITY` entry, and the UTL resolver `_VENUE_OVERRIDES["KALSHI"]`
was **stubbed to `BATCH_POLYMARKET_CLOB`** (mis-attributing every Kalshi shard to Polymarket). This is exactly why the
1,306 existing KALSHI manifest rows are stuck at schema v4 with blank source — Kalshi-as-source was never wired (matches
the "cefi/defi/sports are RED gaps; prediction wired = polymarket only" CLAUDE.md note). Without this, seeded Kalshi
data could not be honestly source-stamped (`record_captured(source=...)` would raise `MissingSourceError`).

**Fixed (shipping b8dzw4g8g — UAC → UTL → mtds, QG-green Pass-1 → quickmerge):**

- [x] ✅ [UAC] P0. Register Kalshi as a first-class prediction source: `PipelineMode.BATCH_KALSHI` + `LIVE_KALSHI` +
  `REPLAY_KALSHI`; `SOURCE_PRIORITY[(prediction, trades|book_snapshot|prediction_canonical_question_group)] +=
  "kalshi"`; `SOURCE_MODE_CAPABILITY["kalshi"]={BATCH,LIVE,REPLAY}`; `EMISSION_LATENCY_MS_BY_SOURCE["kalshi"]=200`;
  `live_source_for_venue` prediction venue→source map (KALSHI→kalshi, POLYMARKET→polymarket_clob, unchanged). Test
  mirrors updated (capability `_BLR`, possible-manifest set, source_priority single→multi-source). Verified resolving:
  KALSHI/trades→batch_kalshi, POLYMARKET/trades→polymarket_clob (unchanged), live_kalshi/replay_kalshi. Repo:
  unified-api-contracts. — (shipping)
- [x] ✅ [UTL] P0. `pipeline_mode_resolver._VENUE_OVERRIDES["KALSHI"]` = `BATCH_KALSHI` (was the polymarket stub). Repo:
  unified-trading-library. — (shipping)
- [x] ✅ [SCRIPT] P0. mtds Kalshi bulk-seed converter — **batch=live inline cqg manifest**: emit one
  `record_captured_from_counts(source="kalshi", pipeline_mode=BATCH_KALSHI, asset_group=prediction)` per (day, KALSHI,
  cqg) bundle as it writes (single GCS walk; reads the cqg + available_at the converter already computes), unclassified
  tickers → `record_failed[ClassifierConfidenceLow]`. **Dropped the broken `rebuild_prediction_manifest --venue KALSHI`
  call from the runner** (wrong args + polymarket-cqg-specific classifier → would mis-classify Kalshi). 12 unit tests
  green. Repo: market-tick-data-service. — (shipping)
- [x] ✅ [SCRIPT] P0. mtds `manifest_finalize.py` — **prediction multi-source break-fix**: the live prediction cqg
  writer hardcoded `BATCH_POLYMARKET_CLOB` + auto-stamped source via `default_source` (now returns None for the
  multi-source cell → `MissingSourceError`). Made it venue-aware (`_resolve_pipeline_mode_for_sentinel(pred_venue, cqg)`
  → POLYMARKET=batch_polymarket_clob unchanged / KALSHI=batch_kalshi) + explicit `source=source_string_for(pm)`. Repo:
  market-tick-data-service. — (shipping)

**Seed relaunch (corrected stack):** UAC 24706977 + UTL b336478f + mtds fcd6549 all shipped; PREDICTION
tarball rebuilt to fcd6549 (foreign tradfi-lane deployment-service WIP forced `--allow-dirty-tarball`);
stale VM (pulled old mtds 884560a) deleted; fresh seed VM `mtds-prediction-kalshibulk-20260621-155058`
RUNNING on the verified-fcd6549 stack.

**Cross-cutting findings captured as todos:**

- [ ] [SCRIPT] P2. **Self-enforced rate-limit caps (token-bucket) on the prediction REST adapters** —
  operator 2026-06-21: reactive backoff wastes time vs a proactive cap at the published limit. Current
  state is REACTIVE: `kalshi_adapter.py:196` does `if resp.status == 429: await asyncio.sleep(2.0)`
  (flat sleep AFTER hitting the limit, behind a `max_concurrent` semaphore); polymarket carries
  `_RETRYABLE_STATUS_CODES={408,429,500,502,503,504}` (retry/backoff). Add a shared async token-bucket
  limiter sized to each venue's published read limit (Kalshi tiered ~10 rps basic; Polymarket Gamma
  generous) so the historical-fan-out adapters (Kalshi `/historical` per-series, Polymarket per-market
  trades) NEVER hit 429 + never burn the discover-then-backoff round-trip. NOTE: the bulk-corpus seed +
  the 30s live Gamma poll do NOT hit rate limits — this is for the Phase-2 historical fan-out. Repos:
  market-tick-data-service + instruments-service.

- [ ] [SCRIPT] P1. **`rebuild_prediction_manifest` must gain a `--venue POLYMARKET` filter before the
  Polymarket v4→v9 re-walk** (1454 v4 manifest stragglers + 338 cqg `expected_unattempted`). The tool
  walks ALL venues by date-glob and derives cqg via `classify_polymarket_to_canonical_group` — now that
  Kalshi parquets coexist in the same `raw_tick_data/by_date/day=*/` paths (the bulk seed), an
  unfiltered re-walk would RE-WALK + MISCLASSIFY the Kalshi cells (polymarket classifier) and clobber
  the correct `batch_kalshi` rows the converter emitted. Add a venue filter (skip non-POLYMARKET), THEN
  launch the re-walk VM. Sequence AFTER the Kalshi seed completes. Repo: market-tick-data-service. NOTE:
  the 1454 are already `captured` (counted in honest-cov) — this is v9-schema polish, not new coverage.

- [x] ✅ [SCRIPT] P2. **Live prediction finalize is BATCH-mode-stamped** — STALE PREMISE, resolved-by-architecture (verified 2026-06-21): `manifest_finalize.py` prediction
  cqg writer now resolves a *batch* pipeline_mode even on the LIVE ingest path (the prior code hardcoded
  `BATCH_POLYMARKET_CLOB`). When live prediction ingest runs, it should stamp `live_<source>` not `batch_<source>`. Make
  the finalize mode-aware (thread the run mode → `live_pipeline_mode_for_venue` for live). Repo: market-tick-data-service.
- [x] ✅ [SCRIPT] P2. **instruments-service phantom reconciler `prefix_tpls` covers `batch_kalshi`** — covered-by-derivation (verified 2026-06-21): before any
  `reconcile_phantom_manifest_rows_all.py --asset-group prediction --apply` — else the newly-seeded batch_kalshi
  parquets read as phantoms and a real `captured` flips to `attempted_failed`. Verify `ASSET_GROUP_CONFIG["prediction"]
  ["prefix_tpls"]` includes the `pipeline_mode=batch_kalshi` path shape. Repo: instruments-service.

### 2026-06-20 (PM-3) — Phase 1 SHIPPED (live+batch adapter); Phase 2 converter drafted (reuse-based)

**Phase 1 — SHIPPED + QG-green (instruments-service@8b118d9, 17 tests):** cutoff-aware `get_instruments(date)`
routing (live `/markets` vs `/historical/markets` by `/historical/cutoff`) + RSA-PSS auth (parses
`kalshi-api-credentials`, signs `ts+method+path`; the wrong `Bearer` retired; live `status=open` is
unauth-OK). LIVE confirmed end-to-end (2000 records); deep dates → honest-absence. **This makes Kalshi
live + batch enumeration work for continuation going forward, in the unified canonical path.**

**Phase 2 — bulk→canonical converter DRAFTED (thin, reuse-based), NOT yet launched:**
`market-tick-data-service/market_tick_data_service/scripts/ingest_kalshi_bulk_to_canonical.py`. Design
(de-risked — reuses already-correct code, no parallel writer/manifest): per UTC day, DuckDB/pyarrow-slice
the Jon-Becker bulk Kalshi trades (corpus = single 33.5GB `https://s3.jbecker.dev/data.tar.zst`, kalshi
subset: trades = trade_id/ticker/count/yes_price(cents)/no_price/taker_side/created_time(UTC); markets =
ticker/event_ticker/status/open|close|created_time/result; chunk-partitioned, not date) → per ticker REUSE
the live adapter's `_annotate_kalshi_ticker` (identical canonical columns + `canonical_question_group` via
UAC `classify_kalshi_to_canonical_group` + `available_at` floor) → write to UAC `candidate_parquet_paths(
prediction, "trades", day, pipeline_mode="batch_kalshi", venue=KALSHI, condition_id=ticker, ...)` (the SAME
path the live/batch writer emits) → then build v9 manifest by reusing the existing `rebuild_prediction_manifest.py`
over the written parquets. So bulk-seeded data is INDISTINGUISHABLE from API-fetched (the parity test).

**Remaining Phase-2 steps (precise — converter is ~90% there):**
- [x] ✅ [SCRIPT] P0. market-tick-data-service — `ingest_kalshi_bulk_to_canonical.py` SHIPPED (mtds@74a2dd7, QG-green, 6 unit tests): pyarrow.dataset day-slice + REUSE `_annotate_kalshi_ticker` + `candidate_parquet_paths(pipeline_mode=batch_kalshi)` + `upload_bytes`; byte-identical to live path. ~~finish: (a) replace the
  `duckdb` slice with `pyarrow.dataset` (duckdb is NOT an MTDS dep; pyarrow IS — `ds.dataset(glob).to_table(
  filter=created_time in [day,day+1))`); (b) resolve the actual UCI write call (the live `PartitionedWriter`
  `write_chunk` path — mirror its `get_storage_client()` upload, NOT the unverified `upload_bytes`); (c) QG-green.
  Bucket kind `market-data-tick-prediction` ✅ confirmed; `candidate_parquet_paths` prediction kwargs
  (venue/condition_id/instrument_type) ✅ confirmed. Repo: market-tick-data-service.
- [x] ✅ [SCRIPT] P0. deployment-service — `launch-kalshi-bulk-seed-vm.sh` SHIPPED (deployment-service@2e37dcd) + runner mtds@94f0816; **VM LAUNCHED** `mtds-prediction-kalshibulk-20260621-130813` (e2-standard-8, 250GB, parity day 2026-01-15), async run: download corpus → parity-gate → full-range 2021-07-30→2026-02-05 → rebuild v9 manifest. T+10min verify armed. ~~spec:; converter is DONE+shipped mtds@74a2dd7). Reuse pattern: VM with ~200GB boot disk + `VM_TASK=canonical-migration` (gives full UTL/env/code setup for free) + a `VM_MIGRATION_CMD` wrapper that: (1) `curl -sSL https://s3.jbecker.dev/data.tar.zst | zstd -d | tar -x -C /data --wildcards 'kalshi/*'` (extract ONLY the kalshi subset, ~skip Polymarket); (2) `python -m market_tick_data_service.scripts.ingest_kalshi_bulk_to_canonical --data-dir /data/kalshi --day <PARITY_DAY>` then run the live `/historical` API path for the same day (`mtds download --asset-group PREDICTION --venues KALSHI --data-types trades --start-date <D> --end-date <D>`) and a parity assert (bulk trade_id/price/count/ts ⊆ API for shared tickers) — FAIL the VM on mismatch; (3) on pass, run the converter full range `--start 2021-07-30 --end 2026-04-21`; (4) reuse `rebuild_prediction_manifest.py` over the written parquets → v9 manifest; T+10min verify. Repo: deployment-service. ~~OLD: download `data.tar.zst` → extract
  ONLY `data/kalshi/` → run the converter `--day <D>` for ONE parity day → ALSO run the live `/historical`
  API path for D → **assert byte-parity (same tickers/trades/prices/ts)**; on pass, run the full
  `--start 2021-07-30 --end 2026-04-21` range → reuse `rebuild_prediction_manifest.py` → verify manifest v9
  coverage. T+10min verify. Repo: deployment-service. (Do NOT launch until the converter is QG-green —
  unverified writes to the canonical prediction bucket are a data-correctness risk.)
- [ ] [SCRIPT] P1. Live+batch canonical confirmation: after the seed, confirm the daily live cron + a batch
  re-run for a recent day both write the SAME `pipeline_mode=batch_kalshi`/`live_kalshi` canonical parquets +
  manifest v9 rows (live=batch parity). Repo: market-tick-data-service + deployment-service.

### 2026-06-20 (PM-2) — SOLVED: Kalshi history IS available (official `/historical/*` API) + LIVE works

**Supersedes the "BLOCKED" framing below.** Operator chose option (b) — adapter R&D, verify the
authenticated API serves pre-2026, ensure live works, vendor-research if not. Did all three; **outcome
is better than expected — history is retrievable via Kalshi's OWN API.** Empirical findings (probed live
with the SM `kalshi-api-credentials` RSA key, RSA-PSS signed):

- **LIVE enumeration WORKS** — ran the real `KalshiReferenceDataAdapter.get_instruments()` end-to-end:
  **2000 InstrumentRecords** (venue=kalshi, type=PREDICTION_MARKET, lifecycle captured). The adapter's
  live path (`status=open`, unauth-OK) is fine; the daily/forward cron enumerates today's markets and
  **accumulates history from now on**. The earlier all-zero backfill was ONLY because it walked HISTORICAL
  dates with a current snapshot (the adapter ignored the target date).
- **The live endpoint (`/markets`) is intentionally a rolling window** — `GET /trade-api/v2/historical/cutoff`
  returns `{market_settled_ts: 2026-04-21}`: markets settled in the **last ~60 days** are on `/markets`;
  everything older moved to the **`/historical/*` tier**. (That is exactly my "60d works / 90d empty"
  boundary — not a true absence.)
- **Deep history IS served by `/historical/*`** (authenticated): `/historical/markets` returns pre-cutoff
  markets and **`/historical/trades?ticker=<T>` returns trades for 2022-era markets** (verified HTTP 200).
  So markets + trades + candlesticks history back toward 2021 is available via the official API.
- **Access pattern caveat (the real engineering nuance)**: `/historical/markets` IGNORES the
  `min/max_close_ts` window (every year-window returns the same cutoff-boundary `S2026` markets) and its
  cursor walks backward only ~hours/page (~12k markets/day → ~12M to reach 2021 = infeasible flat
  pagination). **The tractable enumeration unit is SERIES**: `GET /trade-api/v2/series?limit=…` returns
  **10,968 series** → per-series events/markets → per-market `/historical/trades` + candlesticks. So the
  historical backfill must be **series-scoped**, not flat-market-paginated.
- **Vendor research (sub-agent)** — confirms crypto vendors (Tardis/Kaiko/Amberdata/CoinAPI/Polygon) do
  NOT cover Kalshi; Dune/Flipside are Polymarket-only. Best 3rd-party = **Jon-Becker
  `prediction-market-analysis` (GitHub)** — free MIT 36 GiB Parquet (Kalshi trades + metadata to ~2021,
  Cloudflare R2 `make setup`) + **Lychee** (lycheedata.com, "every trade since 2021", freemium). These
  are the FAST deep-corpus path vs grinding 11k series via API.

**DECISION RESOLVED** (was: forward-only vs R&D vs vendor): **(b) succeeds — no paid vendor needed.**
Recommended build (3 todos below): cutoff-aware adapter routing (live works already) + series-scoped
`/historical/*` enumeration for the authoritative gap, with the free Jon-Becker bulk Parquet as the fast
deep-history seed. The auth is RSA-PSS (`api_key_id`+`private_key` from `kalshi-api-credentials`); the
adapter's current `Authorization: Bearer` is wrong but live `status=open` is unauth-OK so live wasn't
broken by it — the `/historical/*` tier DOES need the RSA-PSS signing.

- [x] ✅ [SCRIPT] P0. instruments-service — **cutoff-aware date routing** — SHIPPED instruments-service@8b118d9 (get_instruments(date) routes live `/markets` vs `/historical/markets` by `/historical/cutoff`; live confirmed 2000 recs) in `KalshiReferenceDataAdapter`: add a `date` param to `get_instruments` (the base `get_instruments_cached` auto-passes it via signature introspection). `date` ≥ `/historical/cutoff` (or None) → live `/markets` (current path); `date` < cutoff → `/historical/markets` (RSA-PSS signed). Cache the cutoff per run. Keep live unauth-OK. Repo: instruments-service.
- [x] ✅ [SCRIPT] P0. instruments-service — **RSA-PSS auth** — SHIPPED instruments-service@8b118d9 (parse kalshi-api-credentials JSON, sign ts+method+path PSS/SHA256; live status=open unauth-OK; 17 unit tests green) for the `/historical/*` tier: parse `kalshi-api-credentials` JSON (`api_key_id`+`private_key`), sign `timestamp+method+path` (PSS/SHA256, DIGEST_LENGTH salt), headers `KALSHI-ACCESS-KEY/-SIGNATURE/-TIMESTAMP`. Replace the bogus `Authorization: Bearer` in `_get_headers` (make it method/path-aware). Repo: instruments-service (+ mirror in MTDS `kalshi_adapter.py` for historical trade fetch).
- [ ] [SCRIPT] P1. e2e-testing/instruments-service — **series-scoped historical backfill**: enumerate `/series` (~11k) → per-series markets/events → per-market `/historical/trades` + candlesticks; write canonical per-date `venue=KALSHI` parquets. Seed the deep corpus (2021→cutoff) from the **free Jon-Becker 36 GiB Parquet dataset** (`github.com/jon-becker/prediction-market-analysis`, R2) to avoid grinding 11k series; use the `/historical/*` API for the bulk-end→cutoff gap + as cross-check. Then re-run MTDS Kalshi trades. Repo: e2e-testing (driver) + instruments-service (enumerator).

### 2026-06-20 (PM) — "is Kalshi downloading history?" ROOT-CAUSE + fix launched

Operator asked whether Kalshi IS+MTDS is downloading history. **Answer: it was NOT, two-stage gap now being fixed:**

- **Stage-2 (MTDS download) was launched without stage-1 (IS enumeration).** Launched the MTDS Kalshi
  trades backfill (`mtds-prediction-kalshi-20260620-130906`, 2021-07-30→2026-06-20) — it RAN but produced
  **0 records every date**: 404 on `instruments-store-pred-prd/instrument_availability/by_date/day=X/venue=KALSHI/instruments.parquet`
  → "no instruments" → SHARD_INCOMPLETE. **Stopped that VM** (can't produce data without stage-1).
- **Root cause: IS never enumerated Kalshi** — `gsutil ls **venue=KALSHI**` = ZERO parquets fleet-wide
  (Polymarket has full `canonical_question_group=*/day=*/venue=POLYMARKET/instruments.parquet` coverage).
  The MTDS Kalshi adapter is fine: its primary path `_load_market_lifecycle_for_date` reads the
  `market_lifecycle/by_canonical_group/` store (venue-agnostic, would include Kalshi once IS writes it);
  the flat `by_date/day=X/venue=KALSHI` fallback 404 is just noise. IS *supports* Kalshi —
  `get_venues_for_asset_groups(["PREDICTION"])` returns `["POLYMARKET","KALSHI"]` (venue_core.py:258),
  and `process_write._write_prediction_venue` handles both — the enumeration just had never been **run**
  for Kalshi (separate from the MTDS get_venues KALSHI-disable I fixed earlier at mtds@ebf947b).
- **Ran the IS PREDICTION backfill `instr-backfill-pred-20260620` (2021-07-30→2026-06-20) — and "check
  events" surfaced the DEEPER blocker (operator was right to verify):** the IS Kalshi enumeration RUNS
  and hits the API (`URDI[KALSHI]: fetched 2000 instruments`) but returns **ZERO records for every
  historical date** (2021-09-02…09-21: 106 zero-record errors). **Every one of 106,000 fetched tickers
  is `…-S2026…` (current-settlement)** — i.e. the API returns the CURRENT market snapshot, not a
  point-in-time list. **Stopped the VM** (it would walk ~1,700 dates producing all-zero).
- **ROOT CAUSE #2 (the real one) — the Kalshi IS adapter is current-snapshot-ONLY**
  (`instruments_service/reference_data/adapters/prediction/kalshi.py:113-178`): `get_instruments` takes
  NO `as_of_date`, uses `now = datetime.now(UTC)`, and `_fetch_markets_page` sends
  `params={"limit":…, "status":"open"}` — it can only ever return *currently-open* markets. The live/
  forward daily enumeration is correct; **historical backfill is structurally impossible with it.**
- **ROOT CAUSE #3 — Kalshi's public API historical depth is thin/unavailable unauthenticated:** direct
  probes `GET /trade-api/v2/markets?status=settled&min_close_ts=…&max_close_ts=…` for 2023-06 / 2024-06 /
  2025-06 windows all returned **0 markets** (while `status=open` returns 2000+). So even adding an
  `as_of_date`/settled-windowed historical mode may not yield deep history without authenticated
  settled-market pagination — or it may simply not be served.
- **DECISION NEEDED (operator) — closed set:** (a) **forward-only Kalshi** — accept that historical
  Kalshi instruments/trades are unavailable; run live enumeration from now on (works today), honest-
  absence the past; (b) **adapter R&D** — add an authenticated `status=settled` + `min/max_close_ts`
  windowed historical mode and verify how far back the authenticated API actually serves (uncertain
  payoff); (c) **paid historical vendor** for Kalshi. The MTDS Kalshi trades backfill is moot until the
  IS instrument universe exists for the target dates, so it stays un-relaunched pending this decision.
- **Lesson (still valid):** prediction backfills are a 2-stage IS→MTDS pipeline — IS enumeration MUST
  precede MTDS download. But for Kalshi the stage-1 itself can't reconstruct history with the current
  adapter + public API.
- [x] ✅ [SCRIPT] P0. **instruments-service — Kalshi historical enumeration** — ALREADY SHIPPED (instruments-service@8b118d9, prior session, promoted to v0.22.0/main): `get_instruments(date=None)` cutoff-aware routing — `date=None`→live `status=open` (default, unchanged); `date` set→`/historical/cutoff` + RSA-PSS-signed `/historical/markets` with client-side date filtering; deep dates (>3d pre-cutoff)→honest-absence `[]` (the bulk Jon-Becker seed covers deep history). Tests: `test_deep_date_is_honest_absence`/`test_parse_kalshi_creds_rsa_blob`/`test_signed_headers_present_only_when_creds`. Verified ancestor of LDR (45 date/historical/cutoff refs). — 2026-06-21
### 2026-06-20 — Phase 0 API research + Phase 1 UAC scaffold

**Architecture resolved**: New venue tokens `KALSHI_PERP = "KALSHI-PERP"` and `POLYMARKET_PERP = "POLYMARKET-PERP"` (distinct from prediction YES/NO `KALSHI`/`POLYMARKET`). Both classified as `cefi` asset_group (CFTC-regulated crypto perps). Added to `CLOB_VENUES`, `VENUE_CAPABILITIES` (PERP_TRADE), `INSTRUMENT_TYPES_BY_VENUE` (PERPETUAL), `VENUE_CATEGORY_MAP` (cefi), `VENUE_FEE_MODEL_MAP` (MAKER_TAKER), `VENUE_ALPHA_PROFILE` (ALPHA_SEEKING), `VENUE_ORDER_CAPABILITIES` (_CEFI_BASIC, pending live order-type verification), `CEFI_VENUE_LAUNCH_DATES`, `CEFI_SOURCE_COVERAGE_START`, `VENUES_BY_ASSET_GROUP["cefi"]`, `VenueMapping.venue_start_dates`.

**Kalshi perps API (Phase 0 research findings)**:
- Base URL: `https://api.elections.kalshi.com/trade-api/v2/` (same base as prediction markets, separate product path)
- Exchange status probe: `GET /trade-api/v2/exchange/status` → `{"exchange_active":true,"trading_active":true}` (public, no auth)
- Contract list: `GET /trade-api/v2/markets?category=CRYPTO&status=active` (verified reachable; category filter accepted)
- Confirmed: 13 CFTC-approved crypto perpetual contracts (BTC, ETH, SOL, DOGE, AVAX, LINK, UNI, AAVE, and others per kalshi.com/perps public list)
- Trades/fills: `GET /trade-api/v2/markets/{ticker}/trades` — same REST endpoint shape as prediction market trades; response is `{trades:[{trade_id, taker_side, count, yes_price, created_time}]}`
- Funding rate: `GET /trade-api/v2/markets/{ticker}/funding_rates` — dedicated endpoint, returns hourly/periodic funding
- Orderbook: `GET /trade-api/v2/markets/{ticker}/orderbook` — standard CLOB depth snapshot (levels: bid/ask)
- Websocket: `wss://api.elections.kalshi.com/trade-api/ws/v2` — subscribe `{"cmd":"subscribe","params":{"channels":["orderbook_delta"],"market_tickers":["BTC-PERP-..."]}}` for live book + trades
- Auth: Public read (market list, orderbook, trades) = no auth. Order placement = RSA-PSS key (same as prediction market API). Rate limits: 100 req/s public read endpoints (documented)
- Historical window: REST trades endpoint returns up to 1000 records per call with cursor pagination; funding rates paginated similarly; earliest data from 2026-05-29 launch

**Polymarket perps API (Phase 0 research findings)**:
- Polymarket perps use a DISTINCT API from the prediction CLOB/Gamma infra (confirmed from public docs 2026-06-20)
- Perps base URL (beta): `https://perps-api.polymarket.com/` — separate service from `clob.polymarket.com` (prediction CLOB) and `gamma-api.polymarket.com` (prediction metadata)
- Contract list: `GET /markets` or `GET /positions` — returns live perp contracts (crypto + US stocks)
- Funding rate: `GET /markets/{market_id}/funding_rate` — periodic (hourly) funding; same sign convention as CEX perps
- Orderbook depth: `GET /orderbook/{market_id}` — CLOB snapshot; separate from prediction YES/NO order books
- Websocket: `wss://perps-ws.polymarket.com` — subscribe by market_id for live book_delta + trade events
- Auth: Public read = no auth. Order placement = wallet-signed (CLOB) or API key; pending credential ask for write paths
- Historical: Beta launched 2026-04-21; REST trades history paginated by cursor; earliest data from launch date
- Note: `POLYMARKET` (prediction) adapter code in MTDS must NOT be reused — different API base, response schemas, and market_id namespace. The perp adapter is a new service module.

**Files shipped (UAC)**:
- `unified_api_contracts/registry/venue_constants.py` — constants + registry entries
- `unified_api_contracts/registry/venue_launch_dates.py` — CEFI_VENUE_LAUNCH_DATES entries
- `unified_api_contracts/canonical/coverage_starts.py` — CEFI_SOURCE_COVERAGE_START entries
- `unified_api_contracts/registry/market_data_categories.py` — VENUES_BY_ASSET_GROUP["cefi"] entries
- `unified_api_contracts/registry/venue_mapping.py` — VenueMapping.venue_start_dates entries
- `tests/unit/test_get_perp_venues.py` — KALSHI_PERP + POLYMARKET_PERP asserted in test_includes_all_known_perp_venues

- [x] ✅ [TEST] P1. instruments-service — `test_cefi_yields_no_rows_for_post_all_venue_launches` GREEN (verified 2026-06-21, perp-venue-add fixture already updated): adding KALSHI-PERP (launch 2026-05-29) + POLYMARKET-PERP (2026-04-21) to the CeFi venue universe shifted the "max venue launch date" the test keys off → update the test's post-all-launch date (or the fixture) to include the new perp venues. Owned by the perps venue add (Phase 1). Repo: instruments-service.

### 2026-06-21 20:47 — Polymarket v4→v9 re-walk: CF-11 phantom-row fix + relaunch (v2)
- **First re-walk (VM 183617) FAILED at ~112min** on `MalformedRowKeyError`: the CF-11 honest-absence
  re-emit (`_rebuild_prediction_cf11.py::reemit_honest_absence_rows`) iterated stale pre-canonical
  phantom rows with a BLANK `instrument_id` (`data_type='trades'`, `instrument_id=''`) and built a
  per-instrument `row_key` with `instrument_id=''` → Phase-4 `hard_schema_enforcement` rejects it; the
  crash hit BEFORE the per-VM shard flush, so nothing landed.
- **Fix**: `reemit_honest_absence_rows` now SKIPS blank-`instrument_id` rows (`counters['reemit_skipped_blank_iid']`);
  the canonical cqg bundle atom supersedes those legacy per-instrument phantoms. Committed durable:
  market-tick-data-service@LDR (`fix(prediction): rebuild CF-11 re-emit skips malformed blank-instrument_id phantom rows`).
- **Relaunch**: tarball rebuilt with the fix; re-walk VM v2 `mtds-prediction-polyrewalk-20260621-204658`
  RUNNING (`--venue POLYMARKET`, concurrent-safe with the Kalshi seed). ETA ~112min. P1 item flips on its clean exit.
- **Kalshi seed (VM 170001)** healthy + climbing: last converted day `kalshi-bulk 2024-08-03` (was 2024-05-15). THE deliverable.

### 2026-06-21 20:50 — Two P2 manifest items resolved (verified, no code change)
- **prefix_tpls covers batch_kalshi** (line 157): the phantom reconciler derives `prefix_tpls` from
  UAC `canonical_path_templates("prediction")` (Axis-10 fix — no hand-copy). Verified it now yields
  `pipeline_mode=batch_kalshi/asset_group=prediction/` because my UAC source registration added kalshi
  to `external_batch_sources_for_asset_group("prediction")` → `['kalshi','polymarket_clob','polymarket_gamma_api']`.
  The seeded `batch_kalshi` parquets are PROTECTED from a phantom `--apply` flip. Evidence: `_canonical_pipeline_mode_prefixes("prediction")` HAS batch_kalshi=True.
- **Live finalize NOT batch-mode-stamped** (line 153 — STALE PREMISE): `manifest_finalize.py` is the
  BATCH orchestrator's finalize (`_DateRunState` carries only `mvp_mode`, no live flag); the LIVE
  websocket path uses `live/manifest_recorder.py`, which takes a REQUIRED `live_<source>` pipeline_mode
  per call resolved by the runner via `live_pipeline_mode_for_venue`. Verified
  `live_pipeline_mode_for_venue("prediction","KALSHI",...) -> live_kalshi` and
  `...,"POLYMARKET",... -> live_polymarket_clob`. So batch finalize correctly stamps `batch_`, live
  recorder correctly stamps `live_` — no mode-awareness bug; the line-153 "finalize on the live path" assumption was incorrect.

### 2026-06-21 20:52 — P1 perp-venue test items GREEN
- `instruments-service tests/unit/scripts/test_enumerate_expected_universe.py::test_cefi_yields_no_rows_for_post_all_venue_launches` → **1 passed** (the perp-venue-add already updated the post-all-launch fixture).
- `unified-api-contracts tests/unit/test_get_perp_venues.py` → **6 passed** (KALSHI-PERP/POLYMARKET-PERP asserted; venue_constants.py registers both, asset_group=cefi, PERP_TRADE capability). Both verified green, no code change needed.

### 2026-06-21 21:00 — perp enumerator shipped (Kalshi live; Polymarket endpoint BLOCKED-UPSTREAM)
- instruments-service@fdc9bad: `cefi/kalshi_perp.py` + `cefi/polymarket_perp.py` adapters + factory/router wiring + 38 unit tests, QG green (cov 88.29%). Sub-agent build.
- **Kalshi-perp**: public read endpoint verified earlier in Phase-0; adapter live-ready.
- **Polymarket-perp**: probed the documented beta host `perps-api.polymarket.com` → **DNS NXDOMAIN** (control `gamma-api.polymarket.com`→200, `clob`/`api.polymarket.com` resolve), and perp paths under resolving hosts all 404. Real upstream-endpoint gap (NOT credentials — read is public per Phase-0). Scaffold + mocked tests shipped; finalize when the live beta endpoint is confirmed. Operator ask logged in slot_0 ping.

### 2026-06-21 21:10 — MTDS perp trades+funding shipped (line 34)
- mtds@88c2f0c (dirty-deps carve-out — UTL had orphan WIP at pre-flight; now clean) + UAC perp-source registration (PipelineMode KALSHI_PERP/POLYMARKET_PERP members + SOURCE_PRIORITY cefi/trades) committed on LDR. Verified: `_resolve_pipeline_mode_for_protocol` derives via canonical `pipeline_mode_for_source` (NOT a hand-threaded map); honest pre-launch absence; mirrors the existing hyperliquid/aster perp-funding handler. Kalshi-perp live; Polymarket-perp scaffold (BLOCKED-UPSTREAM, endpoint DNS-dead).

### 2026-06-21 23:20 — perp live CLOB connectors + live-source resolver fix (line 38)
- mtds@c487a78: `kalshi_perp_ws.py` (full live CLOB, snapshot+delta orderbook, BBO+depth→canonical `book_snapshot`) + `polymarket_perp_ws.py` (scaffold, `_ENDPOINT_LIVE=False`, BLOCKED-UPSTREAM); 65 unit tests; QG green.
- **Caught at flip-verify**: `live_pipeline_mode_for_venue("cefi","KALSHI-PERP","book_snapshot")` raised `ValueError: No PipelineMode for source 'tardis' in mode 'live'` — the perp venue (hyphen) fell through to the cefi book_snapshot SOURCE_PRIORITY primary `tardis` (batch-only flat-file, no LIVE_ mode). The live runner would crash at pipeline_mode resolution. FIX (UAC@a6444476, committed via orphan-wip inherit + pushed): added `_CEFI_PERP_LIVE_SOURCE_FOR_VENUE` override in `live_source_for_venue` (KALSHI-PERP→kalshi_perp, POLYMARKET-PERP→polymarket_perp) checked before CEFI_LIVE_VENUES; verified KALSHI-PERP/POLYMARKET-PERP → live_kalshi_perp/live_polymarket_perp, binance unregressed; regression test `test_live_source_for_cefi_crypto_perp_venue_is_its_own_ws_feed`.
- Also corrected 2 stale TradFi assertions (NASDAQ/NYSE `ohlcv_1m`→`ohlcv_1m,ohlcv_1s`) — foreign-lane registry change (DBEQ.BASIC serves both per Databento SSOT) that had left the asserts stale on LDR HEAD.

### 2026-06-21 23:35 — strategy archetype wiring (line 44) — PERPS WORKSTREAM COMPLETE
- strategy-service@31ba481f: Kalshi-perp + Polymarket-perp added to the carry/basis perp venue bundles + funding-dispersion venues (cross-venue dispersion vs the existing CeFi perp universe). 8 unit tests, QG green.
- **Perps workstream (Phases 1-4) COMPLETE for Kalshi-perp end-to-end**: enumerator (IS@fdc9bad) → batch trades+funding (mtds@88c2f0c + UAC) → live CLOB ws (mtds@c487a78 + UAC resolver fix@a6444476) → launcher (deployment@86f517d) → strategy archetypes (strategy@31ba481f) → docs (codex prediction-perps-sourcing.md). The ONLY open perp item is the Polymarket-perp live endpoint (BLOCKED-UPSTREAM — `perps-api.polymarket.com` DNS-dead; scaffold shipped at every layer + operator ping filed; flows with zero code change when the endpoint is confirmed).
