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
- [x] ✅ [SCRIPT] P0. **Polymarket LIVE+BATCH token-id fix SHIPPED (IS@1ecf5cb + MTDS@9447c71, 2026-06-22)** — IS now persists clob_token_ids (CLOB tokens[].token_id → side-table → availability parquet; verified 1670/1670 rows populated) + MTDS _is_universe expands it → POLYMARKET:PREDICTION_MARKET:{token_id} per outcome (UAC already parsed it). Pending: re-enumerate IS Polymarket universe + reship live + batch book_snapshot. ORIG: **Polymarket LIVE capture blocked — IS universe lacks CLOB token_ids (DISCOVERED 2026-06-22, T+10 verify of the reshipped shards)**: with the WS `/ws/market` fix the Polymarket live producer now CONNECTS (0 real WS errors), but it skips **all** 28,152 resolved instruments — `PolymarketClob: unknown instrument '0x…' — expected POLYMARKET:PREDICTION_MARKET:{token_id}` — because `_is_universe.prediction_instrument_ids_from_df` feeds the connector **condition_ids** (`0x…64hex`) while the CLOB market WS subscribes by per-outcome **decimal token_id** (2 per binary market). The IS prediction parquet HAS a `clob_token_ids` column but it is **None/unpopulated** — the IS Polymarket gamma adapter (`instruments_service/reference_data/adapters/prediction/polymarket.py`) never captures/persists `clobTokenIds` (gamma `/markets` returns it as a JSON-string array). Per the IS→MTDS contract (IS owns instrument identity), fix = **(1) IS adapter persists `clob_token_ids`** from the gamma response + **(2) re-enumerate the Polymarket universe** so parquets carry token_ids + **(3) MTDS `_is_universe` expands `clob_token_ids` → `POLYMARKET:PREDICTION_MARKET:{token_id}` per outcome** (prefer it over condition_id). Then reship the 2 Polymarket shards. Kalshi live is UNAFFECTED (fully capturing). Repos: instruments-service + market-tick-data-service. Provenance: prediction-hardening reship verification 2026-06-22.
- [x] ✅ [SCRIPT] P0. **Polymarket live universe token_ids OPERATIONALIZED — ROOT CAUSE was a writer/reader path mismatch + a condition_id fallthrough, NOT a stale-write-path (FIXED 2026-06-23, mtds@aed9fb2)**: the prior "GcsEventSink stale-write" diagnosis was WRONG — that log is the OBSERVABILITY event sink, not the data sink. The IS data DID write: `StorageDataSink._build_partition_path` (UTL) `sorted()`s partition keys, so `_write_prediction_venue`'s `{day,venue,canonical_question_group}` lands at `instrument_availability/by_date/canonical_question_group=<G>/day=<D>/venue=POLYMARKET/instruments.parquet` (cqg FIRST) — a path the prior agent never probed (they only looked at bare `day=<D>/venue=…`, the stale 2026-05-12 shape). A `--force` re-enum wrote 135 fresh cqg parquets with **clob_token_ids populated 1560/1560** (verified). The REAL live bug: `_is_universe.prediction_instrument_ids_from_df` for POLYMARKET fell through to instrument_key/condition_id when clob_token_ids was empty (the stale future-dated `day=2027..2029` bare shards), emitting `POLYMARKET:PREDICTION_MARKET:0x<condition_id>` which the CLOB WS rejects (`unknown instrument '0x…'; skipping` — confirmed in the live VM run.logs). FIX: POLYMARKET resolves SOLELY from clob_token_ids; no token_ids → `[]` (honest skip), never a condition_id. Re-tested vs the REAL bucket: **17772 token_ids, ZERO 0x leaks** (was 36879 w/ thousands of 0x). mtds tests + fixtures updated (`_pred_parquet_df`). Foundation IS@1ecf5cb + IS@482b50f + MTDS@9447c71 all correct. — mtds@aed9fb2 | QG green | verified end-to-end against instruments-store-pred-prd. ORIG diagnosis (superseded, kept for trail): the IS+MTDS clob_token_ids code fix is SHIPPED + isolation-verified (live-mode `get_instruments(date=None)` → 1670/1670 rows carry clob_token_ids; `_records_to_dataframe` populates; MTDS `_is_universe` expands → POLYMARKET:PREDICTION_MARKET:{token_id}). BUT operationalizing it for the live producer is blocked by TWO IS-enumeration realities: (1) **batch/date enumeration date-filters out today's active Polymarket markets** — `--mode batch --start-date <today>` ran `_fetch_clob_markets` (scans 863K CLOB history, ~13min) then `filter_instruments_by_date` dropped ALL POLYMARKET instrument records ("0 records after filtering"), so today's `instrument_availability/by_date/day=.../venue=POLYMARKET/instruments.parquet` has only the 382 cqg/OTHER-bucket rows (clob_token_ids=0/382) — the `_records_to_dataframe` token-id path never wrote because it got 0 records; (2) **the live runner `_read_prediction_is_universe_sync` UNIONS ALL historical `instrument_availability/by_date/` blobs** (→28,152 condition-ids), virtually none of which carry clob_token_ids. So the live universe is dominated by token-id-less historical rows. **Root cause**: batch/date mode = markets that ENDED on that historical date (resolved markets); LIVE wants CURRENTLY-active markets = the gamma `get_instruments(date=None)` fetch (which DOES carry clob_token_ids), but `--mode live` is a continuous ScheduledIO loop, not a one-shot universe writer. **Fix options (pick one, IS):** (a) a prediction live-universe writer that runs the gamma active-market fetch (date=None) one-shot and writes today's `by_date` parquet with clob_token_ids (active markets, not date-filtered); OR (b) make the live runner resolve the Polymarket universe from the gamma active set directly (still IS-owned) rather than unioning stale historical batch parquets; OR (c) relax the prediction date-filter so active (future-ending) Polymarket markets are written for the current date. Once any lands → today's parquet carries active-market token_ids → MTDS `_is_universe` (already shipped) expands them → live Polymarket captures. Also unblocks Polymarket BATCH book_snapshot. Repo: instruments-service (+ maybe market-tick-data-service universe-read). Provenance: re-enumeration verify 2026-06-23. **REFINED 2026-06-23 (deeper)**: (1) adapter today-routing FIXED+shipping (IS — `get_instruments` now routes date==today→gamma-active not CLOB-historical, so the enum fetches the active token-id-bearing set: 1657 fetched / 1589 written vs 382 before). (2) BUT the live-runner-read parquet `instrument_availability/by_date/day=<d>/venue=POLYMARKET/instruments.parquet` is a **raw `PolymarketGammaMarket` dump** (46 gamma cols: best_bid/outcome_prices/market_maker_address/clob_token_ids; NO `instrument_key`) — NOT the `_records_to_dataframe(InstrumentRecord)` path my clob_token_ids side-table fix targeted. That dump writes **clob_token_ids=[] (empty)** despite the model carrying them. So the EXACT remaining fix = find the prediction gamma-raw-market df-writer (the one producing that 382-row cqg-bucketed parquet) and ensure it serializes the populated `clob_token_ids` (the model_dump should carry it — investigate why it's []). (3) Also the date-filter logs '0 records after filtering (excluded from expected): POLYMARKET' — a separate expected-universe accounting quirk to confirm benign. Needs a focused fresh-context IS session on the prediction write path. **SHARPEST 2026-06-23**: the live-runner-read parquet `…/day=2026-06-23/venue=POLYMARKET/instruments.parquet` has **mtime 2026-05-12** (month-STALE) and the enum's `--force` run ('wrote 1589 records date=2026-06-23') did NOT update it — batch mode logged 'using GcsEventSink bucket=…-events', so prediction batch instrument records route through an EVENT sink, and the canonical by_date instruments parquet the live runner reads is written/consolidated by a SEPARATE path that isn't refreshing it. So BOTH the clob_token_ids population AND a stale-universe problem live in the prediction batch write/consolidation path. Focused-session targets: (a) why `instruments` batch writes don't refresh `by_date/day/venue=POLYMARKET/instruments.parquet` (GcsEventSink vs direct gated-sink-write; is a consolidation step missing?); (b) ensure that canonical parquet carries the populated clob_token_ids. Shipped foundation this session: IS@1ecf5cb (clob_token_ids persist via _records_to_dataframe+side-table+enrich), IS@482b50f (today→gamma-active routing), MTDS@9447c71 (_is_universe expand) — all correct + green, but blocked from operationalizing by the stale-write-path.
- [x] ✅ [SCRIPT] P0. **Kalshi batch trades 0-capture = REAL BUG (endpoint moved), FIXED (mtds@aed9fb2)**: the 6001 KALSHI `trades` `SOURCE_RETURNED_ZERO` (+ 6001 book_snapshot_5 empty) are ALL dated 2026-06-22/23 (within the ~60-day Kalshi public-API window — NOT the honest old-history case). Live-probed `api.elections.kalshi.com/trade-api/v2`: the adapter's `GET /markets/{ticker}/trades` (path form) returns **`404 page not found`** for EVERY ticker (incl. liquid `KXBTCD-*`, `KXWTAMATCH-*`); the current endpoint is the COLLECTION route `GET /markets/trades?ticker=<t>` → HTTP 200 with real trades (verified 50–100 trades + working cursor + min_ts). FIX: `kalshi_adapter.py::get_trades_with_status` URL → `/markets/trades`, ticker → query param. UAC `KalshiTrade` schema already current (`count_fp`/`yes_price_dollars`/`no_price_dollars`) — endpoint was the sole bug. CF-11 test URL-agnostic (unaffected). Backfill of the post-launch window rides the next prediction backfill VM. Repo: market-tick-data-service. — mtds@aed9fb2 | QG green.
- [x] ✅ [SCRIPT] P0. **Prediction LIVE blocker was a STALE TARBALL, NOT a stale universe — DIAGNOSED + relaunched on fresh tarball (2026-06-23 continuous-flow session).** The prior "IS universe STALE at day=2026-05-22 / no current-day clob_token_ids" premise is **FALSE as of today** — re-measured the REAL bucket the live runner reads (`resolve_bucket_name(kind="instruments-store-prediction")` → env-SHORT `instruments-store-pred-prd-central-element-323112`, NOT the env-less `-prediction-` legacy bucket that was stale): it HAS `day=2026-06-23` (today) + 135 `day>=today` POLYMARKET availability blobs with **clob_token_ids populated 25/25** (the `mtds-prediction-polymarket-20260623-1112` enum VMs refreshed it). Ran the live runner's EXACT prediction universe path (`_filter_prediction_is_blobs` + `collect_keys_from_is_blobs`) against prd: **resolved 17,772 POLYMARKET token-id keys, ZERO 0x-condition-id leaks** — the mtds@aed9fb2 `_is_universe` fix is correct AND the universe is fresh+populated. The env-less/-prediction- bucket (stale 05-22) is a vestigial legacy store the runner does NOT read. **Actual blocker:** the 4 RUNNING `prediction-live-*-20260622-2013` VMs baked the **pre-aed9fb2 tarball** (run.log still emitted `unknown instrument '0xffc5…'; skipping` — the exact pre-fix 0x leak). **FIX:** rebuilt the mtds tarball from clean LDR tip `mtds@5906ebf` (bakes aed9fb2 prediction fix + the oracle fix) → `gs://…/code/mtds-code.tar.gz` @11:26Z (built mtds-only to avoid baking the foreign-dirty deployment-service WIP); deleted the 4 stale VMs; relaunched all 4 shards (`prediction-live-{polymarket,kalshi}-{trades,book_snapshot_5}-20260623-113*`) on the fresh tarball. T+10 verify (universe-resolves + 0-leak + capture) in flight. Repo: market-tick-data-service (tarball) + deployment-service (relaunch). Provenance: continuous-flow session 2026-06-23.
- [ ] [SCRIPT] P1. **Polymarket BATCH book_snapshot_5 launch — backfill launcher hardcodes `VM_DATA_TYPES=trades` (DISCOVERED 2026-06-23)**: now that the live token-id universe resolves, the Polymarket BATCH book_snapshot path (design item 83: REST `clob.polymarket.com/book?token_id=` → top-5 → `book_snapshot_5`) needs a launch path. `deployment-service/scripts/vm/launch-mtds-prediction-backfill-vm.sh` line ~145 hardcodes `VM_DATA_TYPES=trades` — extend it to accept `--data-type book_snapshot_5` (the polymarket_adapter already has the `/book` order-book fetch + `book_microstructure_handler.py` exists). Then launch a recent-date backfill once the live fix is shipped + the universe parquets carry token_ids (already true on prd today). Repo: deployment-service (launcher) + market-tick-data-service (verify book handler routes prediction book_snapshot_5). Provenance: autonomous prediction-capture session 2026-06-23. **NICE-TO-HAVE** — does NOT block live capture (the primary goal); live book_snapshot_5 already captures via the WS connector once token_ids flow.
- [ ] [SCRIPT] P1. **Polymarket-perp enumerator — BLOCKED-UPSTREAM (no public perps API exists yet — CONFIRMED 2026-06-22)**: the perps are LIVE (CFTC-DCM-approved, launched 2026-04-21, beta to restricted users 2026-05-28, up to 20x, S&P500/NVDA/NFLX/HOOD) but **web-UI beta only**; `perps-api.polymarket.com`/`perps.polymarket.com`/`perp.polymarket.com` are ALL NXDOMAIN on Google+Cloudflare (not region, not auth — the host doesn't exist), and the official docs (docs.polymarket.com + llms.txt) have ZERO perps/perpetual/funding entries. So there is NO public REST/WS perps endpoint to build against. Scaffold (`PolymarketPerpReferenceDataAdapter` + MTDS adapter/connector + launcher gating + strategy honest-absence) is shipped at every layer; the REAL unblock is Polymarket publishing the public perps API (or operator-provisioned beta API access). Auto-flows on endpoint availability. Ping: slot_0. Repo: instruments-service.
  - **2026-06-22 unified-CLOB re-verification (operator said "perps ride the unified CLOB `clob.polymarket.com` + Gamma
    `active=true`")**: probed empirically — `clob.polymarket.com/clob-markets` IS reachable (HTTP 200, 38,969 markets,
    opaque short-key schema `r/t/c/mos/mts/mbf/tbf/ao/cbos/aot/ibce/fd`) but Gamma `/markets?active=true` AND
    `/events?active=true` return **ZERO** perp/perpetual/funding markets, and the `tag=crypto-perpetuals` /
    `series_slug=crypto-perpetuals` filters are **silently IGNORED** (tagged vs untagged queries return byte-identical
    regular-Q&A slugs: `new-rhianna-album-before-gta-vi`, `will-bitcoin-hit-1m-before-gta-vi`, …). So perpetuals are
    **not publicly enumerable** via the documented Gamma/CLOB discovery path — corroborating the web-UI-beta-only
    finding. **DISCREPANCY for operator**: the unified-CLOB host works for prediction markets, but the perp product is
    gated (beta/restricted). The unblock is **operator-provisioned beta API credentials** (or Polymarket publishing the
    public perps endpoint), NOT a buildable public path — status stays BLOCKED-CREDENTIALS, not descoped. Kalshi-perp is
    fully live (separate public API). Verified via `prediction-to-100%` drive.
## Phase 2 — historical download (trades) + funding

- [x] ✅ [SCRIPT] P1. market-tick-data-service — perp trades+funding adapters SHIPPED (mtds@88c2f0c + UAC perp-source registration on LDR): `_perp_funding_kalshi_polymarket.py` stage (Kalshi `GET /markets?category=Crypto` → `/markets/{ticker}/funding_rates`, day-windowed, 429/5xx retry, shard-isolated) + `perp_funding_handler.py` wired (`_resolve_pipeline_mode_for_protocol`→`pipeline_mode_for_source`, pre-launch `record_empty(EXPECTED_PRE_VENUE_LAUNCH)` kalshi_perp<2026-05-29 / polymarket_perp<2026-04-21, DEFAULT_PROTOCOLS+chain_map extended); 16 unit tests; QG green (5060 pass, 80.77%). UAC: `PipelineMode.BATCH/LIVE/REPLAY_KALSHI_PERP` + `BATCH/LIVE_POLYMARKET_PERP` + `SOURCE_PRIORITY[(cefi,trades)]+=kalshi_perp,polymarket_perp` (committed LDR). **Kalshi-perp live-ready; Polymarket-perp scaffold BLOCKED-UPSTREAM** (endpoint NXDOMAIN — see enumerator sub-item + slot_0 ping). — 2026-06-21

## Phase 3 — LIVE CLOB depth + quotes (the arb-backtest data)

- [x] ✅ [SCRIPT] P1. market-tick-data-service — perp LIVE CLOB ws connectors SHIPPED (mtds@c487a78 + UAC resolver fix@a6444476): `live/connectors/kalshi_perp_ws.py` (per-ticker `_OrderBook` snapshot+delta, lazy ws, exp-backoff reconnect, registered `KALSHI-PERP`, canonical `book_snapshot` BBO+depth, 37 tests) + `polymarket_perp_ws.py` scaffold (`_ENDPOINT_LIVE=False`, BLOCKED-UPSTREAM, registered `POLYMARKET-PERP`, 28 tests); both in `register_all()`; QG green (5161+65 tests, 81.03%). **UAC FIX**: `live_source_for_venue` perp-venue override (`KALSHI-PERP`→`kalshi_perp` not batch-only `tardis`) — caught + fixed a `live_pipeline_mode_for_venue` ValueError that would have crashed the live runner; regression test added. Kalshi-perp live-ready (`live_kalshi_perp`); Polymarket-perp scaffold BLOCKED-UPSTREAM. — 2026-06-21
- [x] ✅ [SCRIPT] P2. deployment-service — perp CLOB live-recording launcher SHIPPED (deployment-service@86f517d): `scripts/vm/launch-perp-clob-live.sh` — KALSHI-PERP → e2-standard-8 VM (`VM_TASK=mtds-live`/`VM_OPERATION=live_websocket`/`MANIFEST_PER_VM_SHARDS=true`, shard `cefi:KALSHI-PERP:book_snapshot`→slug `cefi-kalshi-perp-book-snapshot`, prefix covered by `mtds-live-cefi-` in vm_zombie_watchdog LONG_LIVED_LIVE), singleton-locked per shard; POLYMARKET-PERP → clean early-exit BLOCKED-UPSTREAM (no doomed VM); live=batch parity (same UAC `book_snapshot`, only pipeline_mode differs live_kalshi_perp vs batch_kalshi_perp); lifecycle marker (Epic predictions_master/permanent). QG green. — 2026-06-21

- [x] ✅ [SCRIPT] P2. **Kalshi PREDICTION live CLOB depth → `book_snapshot_5` SHIPPED** (mtds@425b1e8): `live/connectors/kalshi_clob_ws.py` (`KalshiClobWSFeedConnector`, ws `orderbook_delta` snapshot+delta, top-5 → `book_snapshot_5`, venue KALSHI, asset_group prediction; coexists with the lowercase `kalshi` trades connector); registered in `register_all()`; 577-line test suite; QG green. Verified `live_pipeline_mode_for_venue('prediction','KALSHI','book_snapshot_5')→live_kalshi`. **Phase-3 both-venues live CLOB depth COMPLETE** (Polymarket@26297e4 + Kalshi@425b1e8). — 2026-06-22

## Phase 4 — arb wiring

- [x] ✅ [DESIGN] P2. strategy-service — perp funding wired into funding-rate-arb + basis archetypes SHIPPED (strategy-service@31ba481f): `catalog_carry.py` `_CARRY_BASIS_PERP_VENUE_BUNDLES` (10→12) + `_FUNDING_DISPERSION_VENUES` (4→6) += `(kalshi,KALSHI-PERP,USDC)` + `(polymarket,POLYMARKET-PERP,USDC)` (slot tokens from UAC `_PREDICTION_TOKENS`); 8 tests; QG green. POLYMARKET-PERP wired for honest-absence (BLOCKED-UPSTREAM — flows when endpoint recovers, no code change). — 2026-06-21

## Codex SSOT updates

- [x] ✅ [DOCS] P2. codex/02-data — prediction-perps sourcing doc WRITTEN (`prediction-perps-sourcing.md`) + prediction-data-types-catalog.md cross-links it (KALSHI_PERP/POLYMARKET_PERP). Repo: unified-trading-pm. — 2026-06-21

## Progress Log

### 2026-06-23 (continuous-flow session) — inherited-WIP mtds fixes SHIPPED (mtds@aed9fb2); prediction-live STILL gated on a fresh-today IS token-id universe

The prior session's uncommitted mtds WIP (Kalshi `/markets/trades` endpoint fix + `_is_universe` solely-clob_token_ids
honest-skip + tests) was found dirty in the slot clone, QG-green'd (had to trim `get_trades_with_status` 51L→under-50L
method-size + clear a transient version-alignment drift), and **shipped via quickmerge → mtds@aed9fb2** (LDR; Tier-C
drain → staging ≤15min). So the CODE for prediction live (no 0x pollution) + Kalshi BATCH trades (endpoint 404 fix) is
now on the integration branch + will ride the next tarball.

**BUT prediction LIVE still captures 0 (honest empty) — the remaining blocker is the IS instrument-availability
universe, NOT code.** Measured 2026-06-23: `instruments-store-prediction-…/instrument_availability/by_date/
canonical_question_group=*/day=*/venue=POLYMARKET/instruments.parquet` is STALE at **max day=2026-05-22 across ALL cqg
groups**, and the latest parquet (day=2026-05-22 OTHER) has **NO `clob_token_ids` column** (46 gamma cols,
`instrument_key`=0x condition_id). The live runner's `_filter_prediction_is_blobs` requires `day>=today` → finds NO
active token-id universe → `_is_universe` correctly returns `[]` (honest) → every window `empty_confirmed`. The
`expected-universe-v2-prediction` Cloud Run job (triggered this session, Completed) only seeds `_index`
expected_unattempted from `gs://instruments-store-pred-prd-…/prod/catalog.parquet` — it does NOT write the token-id
`instrument_availability` parquet. `lifecycle-catalogue-regen-prediction` (runs `build_instrument_catalogue.py
--asset-group prediction`) is PAUSED. **This is the "needs a focused fresh-context IS session" item below** — the exact
remaining fix is the IS prediction write/consolidation path that refreshes `by_date/.../venue=POLYMARKET/
instruments.parquet` for the CURRENT day WITH populated `clob_token_ids` (+ confirm the env-short
`instruments-store-pred-prd-` vs env-less `instruments-store-prediction-` bucket the live runner reads). Note an
env-short/env-less bucket split exists between the catalog (`-pred-prd-`) and the availability store
(`-prediction-`) — verify the live runner + the writer agree on ONE bucket (the defi gotcha class). Until that lands,
relaunching the live VMs alone will NOT make them capture (the universe is honestly empty). Kalshi live UNAFFECTED by
this (it had its own batch-endpoint bug, now fixed). Provenance: continuous-flow session
`plans/active/data_completion_to_100_all_ag_2026_06_21.md` 2026-06-23.

### 2026-06-23 (autonomous) — ROOT CAUSE found + FIXED: writer sorts partition keys; live runner condition_id fallthrough poisoned the universe

**The "stale parquet / GcsEventSink" diagnosis was a RED HERRING.** The `Batch mode: using GcsEventSink bucket=…-events` log is the OBSERVABILITY event sink (`build_event_sink`, for STARTED/STOPPED) — NOT the data sink. The data DID write. The prior agent only probed `instrument_availability/by_date/day=<d>/venue=POLYMARKET/instruments.parquet` (the stale bare-shape, mtime 2026-05-12) and concluded "writes don't refresh."

**Actual fact**: `StorageDataSink._build_partition_path` (UTL `protocol_impls.py`) **`sorted()`s the partition keys alphabetically**. `_write_prediction_venue` passes `partition={day, venue, canonical_question_group}` → the real write path is `instrument_availability/by_date/canonical_question_group=<G>/day=<D>/venue=POLYMARKET/instruments.parquet` (cqg FIRST). My `--force` re-enum on 2026-06-23 WROTE 135 cqg parquets there (verified: MISC_NOVELTY = 1560 rows, **instrument_key + clob_token_ids populated 1560/1560**, each a 2-element decimal-token list). The IS write path (IS@1ecf5cb + IS@482b50f) is CORRECT — clob_token_ids flow end-to-end.

**The real remaining bug (FIXED)**: the live runner `_filter_prediction_is_blobs` matches suffix `/venue=POLYMARKET/instruments.parquet` + `day>=today`, which correctly matches the fresh cqg paths BUT ALSO matches ~30 STALE future-dated (`day=2027..2029`) bare/`market=`-shape parquets (2026-05-12, clob_token_ids=`[]`). `prediction_instrument_ids_from_df` for POLYMARKET, when clob_token_ids was absent/empty, FELL THROUGH to `instrument_key`/`condition_id` and emitted `POLYMARKET:PREDICTION_MARKET:0x<condition_id>` — which the CLOB WS connector CANNOT subscribe (it logs `unknown instrument '0x…'; skipping`). End-to-end test: 36879 keys resolved, thousands were 0x-condition_ids.

**FIX — mtds@aed9fb2** `market_tick_data_service/live/_is_universe.py::prediction_instrument_ids_from_df`: POLYMARKET now resolves SOLELY from `clob_token_ids`; absent column OR empty token lists → `[]` (honest skip + log), NEVER a condition_id fallthrough (a bare condition_id is never a valid Polymarket CLOB subscription). Re-tested against the real bucket: **17772 token_ids resolved, ZERO 0x-condition_ids** (stale future-dated shards cleanly skipped). Regression tests updated in `tests/unit/test_websocket_runner.py` (`test_prediction_is_columns_map_to_connector_ids` + `test_kalshi_bare_instrument_key_rebuilt_to_connector_form`) + fixtures (`_pred_parquet_df` writes the realistic `clob_token_ids` shape). Stale-blob GCS deletion NOT done (4542 legacy-shape blobs incl. past-dated 2025-03 ones the BATCH historical path may read; the code fix neutralises live pollution honestly — destructive delete unwarranted).

### 2026-06-23 (autonomous) — Kalshi batch trades 0-capture = REAL BUG (endpoint moved), FIXED

The 6001 KALSHI `trades` `SOURCE_RETURNED_ZERO` are ALL dated 2026-06-22/23 (within the ~60-day API window — NOT the honest old-history case). Live-probed the Kalshi v2 API: `GET /markets/{ticker}/trades` (the adapter's path-form URL) returns **`404 page not found`** for every ticker; the current endpoint is the COLLECTION route `GET /markets/trades?ticker=<t>` → HTTP 200 (verified 50–100 real trades + working cursor + min_ts on a liquid market `KXWTAMATCH-26JUN22…`). **FIX — mtds@aed9fb2** `kalshi_adapter.py::get_trades_with_status`: URL → `/markets/trades`, `ticker` moved to a query param. The UAC `KalshiTrade` schema already uses the current `count_fp`/`yes_price_dollars`/`no_price_dollars` fields (parse layer fine — endpoint was the sole bug). CF-11 test unaffected (mocks `.get` URL-agnostically).

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

- [x] ✅ [DESIGN] P2. **Polymarket live book = `book_snapshot_5` via the public CLOB order book** (operator decision 2026-06-22 — NOT heavy design): the Gamma poll only gives top-of-book, BUT `clob.polymarket.com/book?token_id=<T>` returns the FULL depth ladder PUBLIC + NO AUTH (verified 2026-06-22: live bids 0.01/0.02/0.03/0.04/… w/ sizes). Decision = option (c)+canonical: take top-5 levels → emit `book_snapshot_5` (the exact cefi-canonical name, NO new data_type) — batch via REST `/book`, live via CLOB market WS `wss://ws-subscriptions-clob.polymarket.com/ws/`. Build = a Polymarket CLOB orderbook connector (depth) + runner tick→candle for book_snapshot_5 so live captures row_count>0. This also resolves the prediction side of item 75. Repo: market-tick-data-service (live/connectors + runner/sink). — mtds@26297e4 + uac@fb3b6999 | QG: mtds PASSED + uac PASSED — 2026-06-22
- [x] ✅ [DESIGN] P2. **UAC naming: SOURCE_PRIORITY uses `book_snapshot` but DataType enum uses `book_snapshot_5`** — FIXED (prediction-side only; cefi untouched per item 75-cefi scope): renamed prediction `book_snapshot` → `book_snapshot_5` in `_source_priority_data.py`, `availability_semantics.py`, `_sports_prediction_contracts.py`, `required_inputs.py`, 4 test files + added `test_live_pipeline_mode_for_prediction_polymarket_book_snapshot_5`. cefi `(cefi, book_snapshot)` entries deliberately preserved pending a separate cefi-handler audit (item 75-cefi). uac@fb3b6999 — 2026-06-22


### 2026-06-21 (PM-2) — LIVE prediction LAUNCHED (free Gamma poll) + Kalshi seed running

- [x] ✅ [SCRIPT] P1. LIVE prediction is WIRED + launchable end-to-end (no build needed): `polymarket_ws.py`
  + `kalshi_ws.py` live connectors EXIST + auto-register (`connectors/__init__.py` autoload),
  `launch-mtds-live.sh --asset-group prediction --shard-spec prediction:POLYMARKET:trades` exists, and the
  live `MTDSShardManifestRecorder` (fixed: asset_group is a writer kwarg) stamps `live_polymarket_clob` via
  the venue-source map. Polymarket live = free public Gamma REST poll (30s, no auth). **LAUNCHED**
  `mtds-live-prediction-polymarket-trades-20260621-155845` (10 high-volume active markets) → first-ever
  LIVE prediction rows (LIVE=0 across all AGs before this). Repo: deployment-service + market-tick-data-service.
- [x] ✅ [SCRIPT] P2. Live producer expanded to the FULL IS-enumerated active universe (WS-based) + all 4 prediction shards SHIPPED+LAUNCHED (mtds@b10c0fe runner `_resolve_is_universe` resolves the active universe from IS when `--instrument-ids` omitted, honest-absence via `record_zero_rows`; deployment@499a86c `launch-prediction-live.sh` + zombie-watchdog `prediction-live-` prefix LONG_LIVED_LIVE). **LAUNCHED 4 shards (2026-06-22, e2-standard-4, RUNNING)**: POLYMARKET×{trades,book_snapshot_5} + KALSHI×{trades,book_snapshot_5}, IS-resolved full universe, replacing the old 10-market limited producer. WS-subscription path → no per-request rate limit (sidesteps item 128). T+10/+20 verification armed. — 2026-06-22
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
- [x] ✅ [SCRIPT] P0. instruments-service `process_write.py` — **same multi-source break-fix in the IS enumeration cqg
  write path** (the runtime cause of the missing `venue=KALSHI` universe — the IS Kalshi enumeration `record_captured`
  for `prediction_canonical_question_group` raised `MissingSourceError` since cqg became multi-source). Added
  venue-derived `_cqg_pm` (POLYMARKET→`BATCH_POLYMARKET_CLOB` / KALSHI→`BATCH_KALSHI`) + `pipeline_mode=_cqg_pm` +
  explicit `source=source_string_for(_cqg_pm)`. IS QG-green (sentinel 42dd37c7). The companion UTL
  `record_captured_from_counts` `datetime` UnboundLocalError (introduced by the foreign DP_*/FetchEvidence WIP) was
  fixed and rode UTL@39f8ec85 to LDR. Repo: instruments-service@07272da4. — 2026-06-22

### 2026-06-22 — DEEPER root-cause chain (the source= fix was necessary but NOT sufficient — found by running the IS Kalshi enumeration end-to-end)

The `venue=KALSHI` universe was STILL silent-empty after the source= fix. Ran the IS prediction enumeration locally
(scoped `--venues KALSHI --start-date 2026-06-22 --force`, real GCS, against a clean UTL@39f8ec85 worktree to bypass a
concurrent UTL-refactor lane) and walked the full fetch→filter→bucket→write→manifest path. Three further bugs, two
fixed + verified, one systemic + still open:

- [x] ✅ [SCRIPT] P0. instruments-service `kalshi.py` — **date-filter silent-drop fix**: the Kalshi adapter's live
  `/markets?status=open` snapshot stamps `open_time` as an INTRADAY timestamp on the current day (e.g.
  `2026-06-22T13:21Z`), but `filter_instruments_by_date` compares `available_from <= date_dt` where
  `date_dt = fromisoformat(date)` = MIDNIGHT → `13:21 > 00:00` dropped EVERY Kalshi market on EVERY day (incl. today) →
  `0 records after filtering` → never reached the cqg write (so the source= error never even fired). Fix: floor
  `available_from_datetime` to the open DATE (a market opening any time on day D belongs to day D's universe; precise
  `market_created_at` still carried on the lifecycle for MTDS tick-gating). **Verified: 6/6 sample markets now survive
  (was 0/6); full enum `KALSHI: 2000 instruments after date filter` → manifest `availability_index` now shows KALSHI
  captured date=2026-06-22 with source=kalshi/pipeline_mode=batch_kalshi.** Repo: instruments-service (kalshi.py,
  QG-green vs clean UTL; ship BLOCKED on the concurrent UTL clone being conflict-marker-broken — quickmerge dep
  pre-flight). — 2026-06-22
- [x] ✅ [SCRIPT] P0. instruments-service `kalshi.py` — **venue-case fix (venue ≠ source)**: the Kalshi adapter's
  `venue` property returned the lowercase SOURCE name `"kalshi"` while Polymarket returns `"POLYMARKET"`. So the
  instrument-parquet partition wrote `venue=kalshi` (lowercase) while the MTDS live runner
  (`websocket_runner._read_prediction_is_universe_sync`) searches `venue={venue}.upper()/instruments.parquet` =
  `venue=KALSHI` → the universe would never be found even once written. Canonical venue is `KALSHI` (UAC
  `partition_paths` "POLYMARKET / KALSHI"; manifest already uppercased via `.upper()`). Fixed `venue → "KALSHI"`; 15
  adapter tests updated + green vs clean UTL. Repo: instruments-service (kalshi.py). — 2026-06-22
- [x] ✅ **FALSE ALARM (resolved 2026-06-22) — instruments.parquet DOES persist; I was checking the wrong path key
  order.** `_build_partition_path` SORTS partition keys alphabetically, so the instruments universe lands at
  `instrument_availability/by_date/canonical_question_group=OTHER/day=2026-06-22/venue=KALSHI/instruments.parquet`
  (cqg-FIRST, not day-first). Verified present (94KB, venue=KALSHI uppercase — the venue fix). DEBUG_SINKWRITE confirmed
  `rows=2000 wrote=True`. The "stale May-12 Polymarket" was the OLD day-first layout; current writes are cqg-sorted. So
  the full chain WORKS: filter (2000 survive) → cqg bucket → instruments.parquet @venue=KALSHI → manifest captured
  (source=kalshi) → lifecycle. **Kalshi LIVE producers RESOLVED the universe** (`prediction-live-kalshi-{trades,book_snapshot_5}`
  read venue=KALSHI; keep-alive ended 2026-06-22 14:06). No code change needed.
- [x] ✅ [SCRIPT] P0. **RESIDUAL — Kalshi live RESOLVES but SKIPS ticks (id-format mismatch)**: the live producers now
  find the Kalshi universe but log `KalshiClob: unknown instrument 'KXMVE…' — expected KALSHI:PREDICTION_MARKET:{ticker}; skipping`
  for every market → no real Kalshi ticks captured yet. Root: mtds `live/_is_universe.py::prediction_instrument_ids_from_df`
  short-circuits `if "instrument_key" in df.columns: return bare instrument_key` (line 27-28), and the IS Kalshi
  universe's `instrument_key` is the BARE ticker (the adapter sets `instrument_key=ticker`), while the KalshiClob WS
  connector parses the canonical `KALSHI:PREDICTION_MARKET:{ticker}`. Polymarket is unaffected (its connector accepts the
  bare `condition_id`). **Fix (pick one, Kalshi-scoped to avoid regressing Polymarket)**: (a) make the `instrument_key`-wins
  branch venue-aware — for KALSHI, if the key lacks `:PREDICTION_MARKET:`, rebuild `KALSHI:PREDICTION_MARKET:{ticker}`; OR
  (b) set the IS Kalshi adapter `instrument_key = f"KALSHI:PREDICTION_MARKET:{ticker}"` (canonical InstrumentKey form) —
  cleaner but audit cross-consumers (cqg classifier uses the ticker arg, not instrument_key, so likely safe). Verify the
  live connector captures after redeploy. Repo: market-tick-data-service (live/_is_universe.py) and/or instruments-service
  (kalshi.py). Provenance: prediction-to-100% drive 2026-06-22. — mtds@aed9fb2 (option-a: venue-aware instrument_key branch
  rebuilds bare KALSHI ticker → `KALSHI:PREDICTION_MARKET:{ticker}`; docstring "KALSHI silent-empty fix 2026-06-22")

- [ ] [SCRIPT] P3. **DISPLAY-ONLY bug (cosmetic, ≤2min)**: `deployment-service/scripts/vm/launch-instruments-backfill-vm.sh:83` echoes `Tarball: gs://.../instruments-code.tar.gz` but the VM setup (`setup-data-pipeline-vm.sh:311`) actually fetches `instruments-service-code.tar.gz` (correct). The echo misleads tarball-freshness debugging — fix the echo string. Provenance: prediction-to-100% drive 2026-06-22. Repo: deployment-service.

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

- [x] ✅ [SCRIPT] P1. **`rebuild_prediction_manifest --venue POLYMARKET` filter + v4→v9 re-walk DONE** (re-walk VM mtds-prediction-polyrewalk-20260621-204658, 5244s, terminal): re-walked POLYMARKET cqg 2025-03-14→2026-06-21 → **7196 captured cqg bundles at v9**, reemit_empty 22257, failed_* 0, source_returned_zero_preserved 1175. The `--venue POLYMARKET` filter kept it off the coexisting batch_kalshi seed parquets; the CF-11 phantom fix (skip blank-instrument_id, `reemit_skipped_blank_iid: 2331`) let it complete (the prior v1 crashed at the CF-11 re-emit). v9-schema polish — the 1454 were already captured. — 2026-06-21
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

### 2026-06-21 23:50 — Polymarket v9 re-walk COMPLETE + book_snapshot naming diagnosed
- **Re-walk v2 DONE** (VM 204658, terminal): 7196 POLYMARKET cqg bundles re-walked to v9 (2025-03-14→2026-06-21), CF-11 phantom fix confirmed working (reemit_skipped_blank_iid 2331, failed_* 0). The v1 crash (MalformedRowKeyError) is resolved.
- **book_snapshot naming (item 75)**: diagnosed canonical=`book_snapshot_5`; bare `book_snapshot` is the stale mismatch BUT reconciliation is entangled with item 69 (prediction = top-of-book, not 5-level) + carries cross-AG cefi blast radius → kept tracked with the full diagnosis + safe phased path (decide 69 → reconcile in one audited breaking change). No current prediction data impact.
- **Kalshi seed (deliverable)** still converting (at 2025-02-10 of ~2025-11 target; ~72M trades day-by-day, healthy). Re-arming a single long watcher; honest-coverage verification + flip 196/240 fire on seed completion.

### 2026-06-22 11:05 — LIVE PREDICTION PRODUCING (Polymarket full universe) — reader fix verified
- After the 3-bug live-path saga (Redis/launcher af4d0f2, IS-path 4ef4e02, reader column-mapping dfaada5) + clearing the fleet MTDS QG-red (option B), the 4 live shards re-launched on the fixed tarball:
  - **POLYMARKET trades + book_snapshot_5: ✅ RESOLVED 19,117 instruments** (full active IS universe), per-VM manifest shards writing (2044/1059 entries, ~215 new/10s). Live prediction producing end-to-end via the unified CLOB.
  - **KALSHI trades + book_snapshot_5: 🟡 keep-alive (IS universe empty)** — the Kalshi IS enumeration had never run for current days (venue=KALSHI universe absent). Launched the IS prediction enumeration for today (launch-instruments-backfill-vm.sh --asset-group PREDICTION) → once venue=KALSHI universe lands, the Kalshi keep-alive auto-resolves (no relaunch needed).
- Net: live prediction is WORKING for Polymarket (the larger venue) at full universe, both data types; Kalshi follows on its IS enumeration. The reader fix correctly maps condition_id→POLYMARKET:PREDICTION_MARKET:{cid} / ticker→KALSHI:... from the cqg/day-partitioned IS store.
