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

Operator 2026-06-20: Kalshi (May–Jun 2026, 13 CFTC crypto perps BTC+alts) and Polymarket (Apr 21 2026 beta,
crypto+stocks, 10–20x) both launched **perpetual futures**. Add them to the universe, map them, download data — for
**basis trades, funding-rate arb, and cross-venue dispersion**. Also: historical prediction data is trades-only, but
**live we can record CLOB quotes + depth** — capture + dump it live for proper arb backtesting.

## Architecture decision (HARD)

Kalshi/Polymarket **perps are crypto perpetuals with funding** — NOT prediction YES/NO markets. They belong in the
**crypto-perp instrument universe** (alongside Binance/Bybit/OKX/Hyperliquid perps), mapping `BTC-PERP`/`ETH-PERP`/… to
the **SAME canonical perp instrument** the CeFi venues use → so funding-rate arb + basis + dispersion work cross-venue
out of the box. Do NOT route them through the prediction question-group canonical (that's the separate Kalshi-Q&A-parser
work, `instruments_mtds_subset_consistency_remediation_2026_06_17.md`). New venue tokens: `KALSHI_PERP` =
`"KALSHI-PERP"` and `POLYMARKET_PERP` = `"POLYMARKET-PERP"` (distinct from prediction `KALSHI`/`POLYMARKET`). Resolved
in P0 research — confirmed separate API infra and product lines.

## Phase 0 — API research (verify before building; no false premises)

- [x] [RESEARCH] P0. Document the Kalshi perps API: market/contract list endpoint, trades (historical window),
      funding-rate endpoint, orderbook/depth (REST + websocket), auth (public read vs RSA-PSS), rate limits. Sources:
      kalshi.com/perps, help.kalshi.com/collections/19654073, trade-api/v2. Repo: instruments-service (research note in
      the plan Progress Log, NOT a summary doc). — unified-trading-pm@2026-06-20 (findings below)
- [x] [RESEARCH] P0. Same for Polymarket perps: contract list, trades, funding, CLOB book/depth (REST + ws), auth,
      limits. Confirm whether perps share the existing Polymarket CLOB/Gamma infra or a new endpoint. Repo:
      instruments-service. — unified-trading-pm@2026-06-20 (findings below)

## Phase 1 — universe + venue mapping (crypto-perp canonical)

- [x] [UAC] P1. Add KALSHI_PERP + POLYMARKET_PERP venues to the crypto-perp universe + `VENUES_BY_ASSET_GROUP`, with
      launch dates (Kalshi ~2026-05-29, Polymarket ~2026-04-21) in `venue_launch_dates.py` + `coverage_starts.py`. Map
      their BTC/ETH/alt perps to the SHARED canonical perp instrument (mirror the CeFi perp instrument universe). Repo:
      unified-api-contracts. ✅ — unified-api-contracts@(shipped 2026-06-20): venue_constants.py, venue_launch_dates.py,
      coverage_starts.py, market_data_categories.py, venue_mapping.py, test_get_perp_venues.py
- [x] ✅ [SCRIPT] P1. instruments-service — perp-contract enumerator for both venues SHIPPED
      (instruments-service@fdc9bad): `KalshiPerpReferenceDataAdapter` (public
      `GET /markets?status=open&category=Crypto`, cursor-paginated, `InstrumentType.PERPETUAL`, 16 unit tests) +
      `PolymarketPerpReferenceDataAdapter` scaffold (22 unit tests); wired into `factory.py`/`router.py`; QG green (cov
      88.29%). Kalshi live endpoint verified. **Polymarket-perp live endpoint BLOCKED-UPSTREAM** — see next item.
- [x] ✅ [SCRIPT] P0. **Polymarket LIVE+BATCH token-id fix SHIPPED (IS@1ecf5cb + MTDS@9447c71, 2026-06-22)** — IS now
      persists clob_token_ids (CLOB tokens[].token_id → side-table → availability parquet; verified 1670/1670 rows
      populated) + MTDS \_is_universe expands it → POLYMARKET:PREDICTION_MARKET:{token_id} per outcome (UAC already
      parsed it). Pending: re-enumerate IS Polymarket universe + reship live + batch book_snapshot. ORIG: **Polymarket
      LIVE capture blocked — IS universe lacks CLOB token_ids (DISCOVERED 2026-06-22, T+10 verify of the reshipped
      shards)**: with the WS `/ws/market` fix the Polymarket live producer now CONNECTS (0 real WS errors), but it skips
      **all** 28,152 resolved instruments —
      `PolymarketClob: unknown instrument '0x…' — expected POLYMARKET:PREDICTION_MARKET:{token_id}` — because
      `_is_universe.prediction_instrument_ids_from_df` feeds the connector **condition_ids** (`0x…64hex`) while the CLOB
      market WS subscribes by per-outcome **decimal token_id** (2 per binary market). The IS prediction parquet HAS a
      `clob_token_ids` column but it is **None/unpopulated** — the IS Polymarket gamma adapter
      (`instruments_service/reference_data/adapters/prediction/polymarket.py`) never captures/persists `clobTokenIds`
      (gamma `/markets` returns it as a JSON-string array). Per the IS→MTDS contract (IS owns instrument identity), fix
      = **(1) IS adapter persists `clob_token_ids`** from the gamma response + **(2) re-enumerate the Polymarket
      universe** so parquets carry token_ids + **(3) MTDS `_is_universe` expands `clob_token_ids` →
      `POLYMARKET:PREDICTION_MARKET:{token_id}` per outcome** (prefer it over condition_id). Then reship the 2
      Polymarket shards. Kalshi live is UNAFFECTED (fully capturing). Repos: instruments-service +
      market-tick-data-service. Provenance: prediction-hardening reship verification 2026-06-22.
- [x] ✅ [SCRIPT] P0. **Polymarket live universe token_ids OPERATIONALIZED — ROOT CAUSE was a writer/reader path
      mismatch + a condition_id fallthrough, NOT a stale-write-path (FIXED 2026-06-23, mtds@aed9fb2)**: the prior
      "GcsEventSink stale-write" diagnosis was WRONG — that log is the OBSERVABILITY event sink, not the data sink. The
      IS data DID write: `StorageDataSink._build_partition_path` (UTL) `sorted()`s partition keys, so
      `_write_prediction_venue`'s `{day,venue,canonical_question_group}` lands at
      `instrument_availability/by_date/canonical_question_group=<G>/day=<D>/venue=POLYMARKET/instruments.parquet` (cqg
      FIRST) — a path the prior agent never probed (they only looked at bare `day=<D>/venue=…`, the stale 2026-05-12
      shape). A `--force` re-enum wrote 135 fresh cqg parquets with **clob_token_ids populated 1560/1560** (verified).
      The REAL live bug: `_is_universe.prediction_instrument_ids_from_df` for POLYMARKET fell through to
      instrument_key/condition_id when clob_token_ids was empty (the stale future-dated `day=2027..2029` bare shards),
      emitting `POLYMARKET:PREDICTION_MARKET:0x<condition_id>` which the CLOB WS rejects
      (`unknown instrument '0x…'; skipping` — confirmed in the live VM run.logs). FIX: POLYMARKET resolves SOLELY from
      clob_token_ids; no token_ids → `[]` (honest skip), never a condition_id. Re-tested vs the REAL bucket: **17772
      token_ids, ZERO 0x leaks** (was 36879 w/ thousands of 0x). mtds tests + fixtures updated (`_pred_parquet_df`).
      Foundation IS@1ecf5cb + IS@482b50f + MTDS@9447c71 all correct. — mtds@aed9fb2 | QG green | verified end-to-end
      against instruments-store-pred-prd. ORIG diagnosis (superseded, kept for trail): the IS+MTDS clob_token_ids code
      fix is SHIPPED + isolation-verified (live-mode `get_instruments(date=None)` → 1670/1670 rows carry clob_token_ids;
      `_records_to_dataframe` populates; MTDS `_is_universe` expands → POLYMARKET:PREDICTION_MARKET:{token_id}). BUT
      operationalizing it for the live producer is blocked by TWO IS-enumeration realities: (1) **batch/date enumeration
      date-filters out today's active Polymarket markets** — `--mode batch --start-date <today>` ran
      `_fetch_clob_markets` (scans 863K CLOB history, ~13min) then `filter_instruments_by_date` dropped ALL POLYMARKET
      instrument records ("0 records after filtering"), so today's
      `instrument_availability/by_date/day=.../venue=POLYMARKET/instruments.parquet` has only the 382 cqg/OTHER-bucket
      rows (clob_token_ids=0/382) — the `_records_to_dataframe` token-id path never wrote because it got 0 records; (2)
      **the live runner `_read_prediction_is_universe_sync` UNIONS ALL historical `instrument_availability/by_date/`
      blobs** (→28,152 condition-ids), virtually none of which carry clob_token_ids. So the live universe is dominated
      by token-id-less historical rows. **Root cause**: batch/date mode = markets that ENDED on that historical date
      (resolved markets); LIVE wants CURRENTLY-active markets = the gamma `get_instruments(date=None)` fetch (which DOES
      carry clob_token_ids), but `--mode live` is a continuous ScheduledIO loop, not a one-shot universe writer. **Fix
      options (pick one, IS):** (a) a prediction live-universe writer that runs the gamma active-market fetch
      (date=None) one-shot and writes today's `by_date` parquet with clob_token_ids (active markets, not date-filtered);
      OR (b) make the live runner resolve the Polymarket universe from the gamma active set directly (still IS-owned)
      rather than unioning stale historical batch parquets; OR (c) relax the prediction date-filter so active
      (future-ending) Polymarket markets are written for the current date. Once any lands → today's parquet carries
      active-market token_ids → MTDS `_is_universe` (already shipped) expands them → live Polymarket captures. Also
      unblocks Polymarket BATCH book_snapshot. Repo: instruments-service (+ maybe market-tick-data-service
      universe-read). Provenance: re-enumeration verify 2026-06-23. **REFINED 2026-06-23 (deeper)**: (1) adapter
      today-routing FIXED+shipping (IS — `get_instruments` now routes date==today→gamma-active not CLOB-historical, so
      the enum fetches the active token-id-bearing set: 1657 fetched / 1589 written vs 382 before). (2) BUT the
      live-runner-read parquet `instrument_availability/by_date/day=<d>/venue=POLYMARKET/instruments.parquet` is a **raw
      `PolymarketGammaMarket` dump** (46 gamma cols: best_bid/outcome_prices/market_maker_address/clob_token_ids; NO
      `instrument_key`) — NOT the `_records_to_dataframe(InstrumentRecord)` path my clob_token_ids side-table fix
      targeted. That dump writes **clob_token_ids=[] (empty)** despite the model carrying them. So the EXACT remaining
      fix = find the prediction gamma-raw-market df-writer (the one producing that 382-row cqg-bucketed parquet) and
      ensure it serializes the populated `clob_token_ids` (the model_dump should carry it — investigate why it's []).
      (3) Also the date-filter logs '0 records after filtering (excluded from expected): POLYMARKET' — a separate
      expected-universe accounting quirk to confirm benign. Needs a focused fresh-context IS session on the prediction
      write path. **SHARPEST 2026-06-23**: the live-runner-read parquet
      `…/day=2026-06-23/venue=POLYMARKET/instruments.parquet` has **mtime 2026-05-12** (month-STALE) and the enum's
      `--force` run ('wrote 1589 records date=2026-06-23') did NOT update it — batch mode logged 'using GcsEventSink
      bucket=…-events', so prediction batch instrument records route through an EVENT sink, and the canonical by_date
      instruments parquet the live runner reads is written/consolidated by a SEPARATE path that isn't refreshing it. So
      BOTH the clob_token_ids population AND a stale-universe problem live in the prediction batch write/consolidation
      path. Focused-session targets: (a) why `instruments` batch writes don't refresh
      `by_date/day/venue=POLYMARKET/instruments.parquet` (GcsEventSink vs direct gated-sink-write; is a consolidation
      step missing?); (b) ensure that canonical parquet carries the populated clob_token_ids. Shipped foundation this
      session: IS@1ecf5cb (clob_token_ids persist via \_records_to_dataframe+side-table+enrich), IS@482b50f
      (today→gamma-active routing), MTDS@9447c71 (\_is_universe expand) — all correct + green, but blocked from
      operationalizing by the stale-write-path.
- [x] ✅ [SCRIPT] P0. **Kalshi batch trades 0-capture = REAL BUG (endpoint moved), FIXED (mtds@aed9fb2)**: the 6001
      KALSHI `trades` `SOURCE_RETURNED_ZERO` (+ 6001 book_snapshot_5 empty) are ALL dated 2026-06-22/23 (within the
      ~60-day Kalshi public-API window — NOT the honest old-history case). Live-probed
      `api.elections.kalshi.com/trade-api/v2`: the adapter's `GET /markets/{ticker}/trades` (path form) returns
      **`404 page not found`** for EVERY ticker (incl. liquid `KXBTCD-*`, `KXWTAMATCH-*`); the current endpoint is the
      COLLECTION route `GET /markets/trades?ticker=<t>` → HTTP 200 with real trades (verified 50–100 trades + working
      cursor + min_ts). FIX: `kalshi_adapter.py::get_trades_with_status` URL → `/markets/trades`, ticker → query param.
      UAC `KalshiTrade` schema already current (`count_fp`/`yes_price_dollars`/`no_price_dollars`) — endpoint was the
      sole bug. CF-11 test URL-agnostic (unaffected). Backfill of the post-launch window rides the next prediction
      backfill VM. Repo: market-tick-data-service. — mtds@aed9fb2 | QG green.
- [x] ✅ [SCRIPT] P0. **Prediction LIVE blocker was a STALE TARBALL, NOT a stale universe — DIAGNOSED + relaunched on
      fresh tarball (2026-06-23 continuous-flow session).** The prior "IS universe STALE at day=2026-05-22 / no
      current-day clob_token_ids" premise is **FALSE as of today** — re-measured the REAL bucket the live runner reads
      (`resolve_bucket_name(kind="instruments-store-prediction")` → env-SHORT
      `instruments-store-pred-prd-central-element-323112`, NOT the env-less `-prediction-` legacy bucket that was
      stale): it HAS `day=2026-06-23` (today) + 135 `day>=today` POLYMARKET availability blobs with **clob_token_ids
      populated 25/25** (the `mtds-prediction-polymarket-20260623-1112` enum VMs refreshed it). Ran the live runner's
      EXACT prediction universe path (`_filter_prediction_is_blobs` + `collect_keys_from_is_blobs`) against prd:
      **resolved 17,772 POLYMARKET token-id keys, ZERO 0x-condition-id leaks** — the mtds@aed9fb2 `_is_universe` fix is
      correct AND the universe is fresh+populated. The env-less/-prediction- bucket (stale 05-22) is a vestigial legacy
      store the runner does NOT read. **Actual blocker:** the 4 RUNNING `prediction-live-*-20260622-2013` VMs baked the
      **pre-aed9fb2 tarball** (run.log still emitted `unknown instrument '0xffc5…'; skipping` — the exact pre-fix 0x
      leak). **FIX:** rebuilt the mtds tarball from clean LDR tip `mtds@5906ebf` (bakes aed9fb2 prediction fix + the
      oracle fix) → `gs://…/code/mtds-code.tar.gz` @11:26Z (built mtds-only to avoid baking the foreign-dirty
      deployment-service WIP); deleted the 4 stale VMs; relaunched all 4 shards
      (`prediction-live-{polymarket,kalshi}-{trades,book_snapshot_5}-20260623-113*`) on the fresh tarball. T+10 verify
      (universe-resolves + 0-leak + capture) in flight. Repo: market-tick-data-service (tarball) + deployment-service
      (relaunch). Provenance: continuous-flow session 2026-06-23.
- [x] ✅ [SCRIPT] P0. **Polymarket CLOB live WS "WS connection error: 0" = oversized single-frame subscribe — FIXED
      (chunked to ≤500 ids/frame, 2026-06-23).** After the stale-tarball relaunch (item above), the polymarket-trades VM
      correctly `resolved 17772 instruments / 0 leaks` but then logged `PolymarketClob: WS connection error: 0` on a
      loop (never captured). DIAGNOSED on the live VM (`sudo …/venv/bin/python` probe, aiohttp 3.13.5): a SINGLE-token
      subscribe gets an ack (`type=1 data=[]`), n=500 still acks, but **n=5000 / n=17772 connect then the server NEVER
      responds** (silently discards the oversized `assets_ids` frame → connector's `receive()` stalls → the swallowed
      exception). The connector sent ALL ~17,772 token-ids in ONE `assets_ids` subscribe frame (1.4 MB). FIX:
      `polymarket_clob_ws.py::_run_ws_session` now chunks `assets_ids` into ≤`_MAX_ASSETS_PER_SUBSCRIBE` (500) frames
      over the one connection; regression test `test_subscribe_chunks_large_universe_into_500_id_frames` (1200 ids → 3
      frames, each ≤500, union==all). QG-green. Needs a fresh tarball + 4-shard relaunch to take effect (the
      113\*-relaunch VMs baked the pre-chunk 11:26Z tarball). Repo: market-tick-data-service. Provenance:
      continuous-flow session 2026-06-23.
- [x] ✅ [SCRIPT] P0. **Polymarket CLOB live captured 0 EVEN with the chunk fix — REAL root cause = `_parse_book_msg`
      message-shape mismatch (FIXED, mtds@db7de3c, 2026-06-23).** After the chunk fix + fresh-tarball relaunch, the
      polymarket-trades VM `resolved 17,772 instruments / 0 leaks` and the WS connected (per-VM shard updating ~195
      entries/tick) but EVERY window stayed `empty_confirmed` (0 captured). Probed the live CLOB `market` channel and
      captured the REAL message shapes vs what the connector parsed: (1) **book** sends `bids`/`asks` as lists of
      **`{"price","size"}` DICTS**, but the connector cast them to `[price,size]` ARRAYS → `_OrderBook.apply_snapshot`
      (indexes `level[0]/[1]`) read nothing → `has_data()` False → no tick; (2) **price_change** sends
      `event_type="price_change"` + a `price_changes` LIST whose entries each carry their OWN
      `asset_id`+`price`+`size`+`side` (NO top-level `asset_id`; field is `price_changes` NOT `changes`) → the connector
      read `msg.get("asset_id")` (absent → None guard) and `msg.get("changes")` (wrong field) → every delta dropped.
      BOTH branches silently produced 0 ticks against the live format. FIX (`polymarket_clob_ws.py`): `_level_pairs()`
      normalises dict-OR-array levels; `_parse_book_msg` now returns `list[ReceivedTick]` (book→1 tick; price_change→one
      tick PER token grouped by `asset_id`); `_parse_msg_ts` normalises ms-epoch; `_drain_ws_messages` iterates the
      list. 5 new/updated regression tests. QG-green. The chunk fix was necessary but NOT sufficient — this is what
      makes capture row_count>0. Effective on the fresh mtds@db7de3c tarball (built + uploaded; VMs relaunched). Repo:
      market-tick-data-service. Provenance: continuous-flow session 2026-06-23.
- [x] ✅ [SCRIPT] P1. **Kalshi live 0-capture = `msg`-envelope + single-sided-ladder parser mismatch — FIXED
      (mtds@9e3bbab, 2026-06-23).** Probed the REAL live Kalshi WS (`api.elections.kalshi.com/trade-api/ws/v2`,
      RSA-PSS-signed, on the kalshi-trades VM) and captured the actual `ticker`/`orderbook_snapshot`/`orderbook_delta`
      message shapes vs the connector parsers — confirmed the SAME class as the Polymarket fix. THREE shape mismatches,
      all silently dropping every tick → 0 capture: (1) **`msg` envelope** — the `type` discriminator + `seq` are
      TOP-LEVEL but every payload field is nested under a `msg` object (`{"type":"ticker","seq":N,"msg":{...}}`); both
      connectors read fields off the top level → all None → dropped. (2) **ticker field names** — real =
      `price_dollars`/`yes_bid_dollars`/`yes_ask_dollars` + `volume_fp`/`open_interest_fp` + ms `ts_ms` (the connector
      read `yes_price_dollars`/`volume`/`open_interest` + treated `ts` as ms). (3) **orderbook is single-sided yes/no
      ladders, NOT bids/asks** — snapshot carries `yes_dollars_fp`/`no_dollars_fp` = `[[price,size],…]` (either/both may
      be absent → empty book → honest no-tick); delta is ONE `{price_dollars, delta_fp, side}` signed-size change (NOT
      bids/asks arrays). FIX: `kalshi_ws.py::_parse_ticker_msg` unwraps `msg` + real field names + ms ts;
      `kalshi_clob_ws.py` `_OrderBook` now keeps yes/no ladders and folds to a canonical YES book (YES bids = yes
      ladder; YES asks = no ladder at `1−price`), `_parse_orderbook_msg` reads the envelope + `yes/no_dollars_fp`
      snapshot + `{price_dollars,delta_fp,side}` delta + ISO/ms ts. Legacy back-compat helpers + tests retained. 13
      new/updated regression tests on the REAL shapes; QG-green (exit 0); 72 connector tests pass. Effective on the
      fresh tarball + relaunch (below). Repo: market-tick-data-service (live/connectors/kalshi_ws.py +
      kalshi_clob_ws.py). Provenance: continuous-flow continuity pass 2026-06-23. — mtds@9e3bbab
- [x] ✅ [SCRIPT] P1. **Polymarket BATCH book_snapshot_5 — SHIPPED + LAUNCHED (2026-06-23)**: (1) **launcher**
      (deployment-service@040e2fc): `launch-mtds-prediction-backfill-vm.sh` accepts
      `--data-types trades|book_snapshot_5|trades,book_snapshot_5` (default trades) → `VM_DATA_TYPES` (was hardcoded).
      (2) **adapter** (mtds@050ce12 + batch=live schema fix @7c849d7): `download_batch` previously IGNORED
      `data_types`+always fetched trades — fixed: `get_books_batch` (semaphore-bounded concurrent
      `clob.polymarket.com/book?token_id=` fetches, CF-11 failure routing), `_build_book_snapshot_5_rows` (canonical
      shape IDENTICAL to the LIVE polymarket_clob_ws — best_bid/ask + bids/asks ladder + msg_type/ts_ms, NOT flat
      bid_px_1..5 — batch=live), `_load_token_ids_from_gcs` (per-date token_ids from IS `clob_token_ids`; empty→honest
      empty, NEVER condition_id fallthrough), `_fetch_books_for_date` writer integration, lifecycle-gated, 3 regression
      tests; basedpyright clean; QG-green. (3) **THREE stale-registry pre-flight gates found+fixed via T+ verify** (each
      caught a silent exit-0/0-row): UAC `expected_coverage._PREDICTION` + `DATA_TYPES_BY_ASSET_GROUP` (uac@1596d4f9)
      AND the REAL gate `VENUE_DATA_TYPE_CAPABILITIES` (`get_expected_data_types_for_venue` reads THIS — uac@1a8e9217,
      book_snapshot_5 start=2026-06-22). After both: pre-flight NO LONGER drops book_snapshot_5 (book5_dropped=0,
      verified on the relaunched VM). (4) **Code + pipeline COMPLETE + LIVE-PROVEN**: the LIVE producers capture
      book_snapshot_5 on prd TODAY (466 live polymarket book parquets verified) via the SAME canonical path
      (batch=live). (5) **Batch-historical-row-proof gated on a date-squeeze cross-dependency** (documented residual,
      NOT a code gap): the batch backfill correctly honest-skips dates whose IS parquet lacks `clob_token_ids` —
      historical dates (≤06-22) were IS-enumerated BEFORE the clob_token_ids fix (no column → honest skip), and today
      (06-23, the only date with clob_token_ids 25/25) is rejected by the batch T-1 rule
      (`DATA_NOT_AVAILABLE: date in the future`). So a batch book row-proof needs an IS re-enumeration of a recent PAST
      date WITH clob_token_ids first (the 2-stage IS→MTDS dependency) — tracked as the residual below. Repo:
      deployment-service (launcher) + market-tick-data-service (adapter) + unified-api-contracts (3 registry gates).
      Provenance: autonomous catalogue/backfill session 2026-06-23.
  - [ ] [SCRIPT] P2. **DEFERRED-CROSS-DEP — batch book_snapshot_5 row-proof on a historical date needs an IS
        re-enumeration carrying `clob_token_ids` (2026-06-23)**: the batch book path is code-complete + live-proven, but
        a BATCH row-capture proof is blocked because historical IS parquets (≤06-22) predate the clob_token_ids column +
        today is batch-future-rejected. Fix = re-enumerate the IS Polymarket universe for a recent past date (e.g.
        06-22) so its `instrument_availability` parquet carries populated `clob_token_ids`, THEN re-run the book
        backfill for that date. Repo: instruments-service (re-enumerate) + deployment-service (re-launch). NICE-TO-HAVE
        — live book_snapshot_5 already captures end-to-end. Provenance: autonomous catalogue/backfill session
        2026-06-23.
- [x] ✅ [SCRIPT] P1. **Prediction BATCH recent-window (05-23→06-22) zero-capture — TWO-LAYER root cause, BOTH FIXED
      (2026-06-23 batch-column-close session)**: (1) **Pre-flight layer (already fixed pre-session, mtds@84504e6 on
      LDR)** — the 28,448 Polymarket-trades manifest rows for 05-23→06-22 are `empty_confirmed[SOURCE_RETURNED_ZERO]`
      (NOT `captured` as item-39 originally framed); the prior framing of a "manifest-vs-data divergence" was imprecise.
      mtds@84504e6 demotes re-attemptable `empty_confirmed` (non-`EXPECTED_*` reasons) OUT of the pre-flight skip set →
      the batch now RE-ATTEMPTS those dates (verified live: VM `mtds-prediction-polymarket-20260623-155710` no longer
      skips, it re-fetches each date). (2) **THE ACTUAL ZERO-CAPTURE ROOT CAUSE — lifecycle-gate off-by-one-day on
      date-only (midnight) settlement (FIXED THIS SESSION, mtds — `polymarket_adapter.py::_apply_lifecycle_gate` +
      `kalshi_adapter.py` gate)**: with re-attempt working, the adapter DID fetch real ticks (e.g. 1687 ticks for 05-23)
      but dropped EVERY one as "post-settlement". Probed the live VM log + the fallback `instrument_availability`
      parquet: Polymarket gamma `end_date_iso = "2026-05-23T00:00:00Z"` (resolution DATE stamped at MIDNIGHT) with empty
      `start_date` (→ `market_created_at=None`). The lifecycle gate's exclusive upper bound
      `tick_ts < settlement_time(=D midnight)` therefore rejected the WHOLE resolution day's ticks
      (`all 1687 ticks fell outside lifecycle window [market_created_at=None, settlement_time=2026-05-23T00:00:00)`).
      FIX: when `settlement_time` is exactly midnight UTC (date-only resolution, no intraday component), extend the
      exclusive upper bound to END of the resolution day (`+1 day`) so day-D ticks are kept; a genuine intraday
      settlement is honoured unchanged. Mirrored into the Kalshi gate (same exclusive-bound shape) defensively. 2
      regression tests added (`test_midnight_settlement_on_resolution_day_keeps_day_ticks` in both adapter
      lifecycle-gating suites). QG-green (sentinel==HEAD). **Ship + relaunch:** SHIPPED 2026-06-23 (mtds@050ce12 — UAC
      was clean by then; landed alongside the Item-38 book_snapshot_5 batch path in one mtds unit, QG-green sentinel
      c11086c). Remaining operational: a fresh mtds tarball + relaunch of the Polymarket batch 05-23→06-22 captures the
      window (rides the next prediction tarball rebuild). Repo: market-tick-data-service
      (`market_interface/adapters/prediction/{polymarket,kalshi}_adapter.py`). Provenance: batch-column-close session
      2026-06-23 + autonomous catalogue/backfill ship 2026-06-23.
- [ ] [SCRIPT] P1. **Polymarket-perp enumerator — BLOCKED-UPSTREAM (no public perps API exists yet — CONFIRMED
      2026-06-22)**: the perps are LIVE (CFTC-DCM-approved, launched 2026-04-21, beta to restricted users 2026-05-28, up
      to 20x, S&P500/NVDA/NFLX/HOOD) but **web-UI beta only**;
      `perps-api.polymarket.com`/`perps.polymarket.com`/`perp.polymarket.com` are ALL NXDOMAIN on Google+Cloudflare (not
      region, not auth — the host doesn't exist), and the official docs (docs.polymarket.com + llms.txt) have ZERO
      perps/perpetual/funding entries. So there is NO public REST/WS perps endpoint to build against. Scaffold
      (`PolymarketPerpReferenceDataAdapter` + MTDS adapter/connector + launcher gating + strategy honest-absence) is
      shipped at every layer; the REAL unblock is Polymarket publishing the public perps API (or operator-provisioned
      beta API access). Auto-flows on endpoint availability. Ping: slot_0. Repo: instruments-service.
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

- [x] ✅ [SCRIPT] P1. market-tick-data-service — perp trades+funding adapters SHIPPED (mtds@88c2f0c + UAC perp-source
      registration on LDR): `_perp_funding_kalshi_polymarket.py` stage (Kalshi `GET /markets?category=Crypto` →
      `/markets/{ticker}/funding_rates`, day-windowed, 429/5xx retry, shard-isolated) + `perp_funding_handler.py` wired
      (`_resolve_pipeline_mode_for_protocol`→`pipeline_mode_for_source`, pre-launch
      `record_empty(EXPECTED_PRE_VENUE_LAUNCH)` kalshi_perp<2026-05-29 / polymarket_perp<2026-04-21,
      DEFAULT_PROTOCOLS+chain_map extended); 16 unit tests; QG green (5060 pass, 80.77%). UAC:
      `PipelineMode.BATCH/LIVE/REPLAY_KALSHI_PERP` + `BATCH/LIVE_POLYMARKET_PERP` +
      `SOURCE_PRIORITY[(cefi,trades)]+=kalshi_perp,polymarket_perp` (committed LDR). **Kalshi-perp live-ready;
      Polymarket-perp scaffold BLOCKED-UPSTREAM** (endpoint NXDOMAIN — see enumerator sub-item + slot_0 ping). —
      2026-06-21

## Phase 3 — LIVE CLOB depth + quotes (the arb-backtest data)

- [x] ✅ [SCRIPT] P1. market-tick-data-service — perp LIVE CLOB ws connectors SHIPPED (mtds@c487a78 + UAC resolver
      fix@a6444476): `live/connectors/kalshi_perp_ws.py` (per-ticker `_OrderBook` snapshot+delta, lazy ws, exp-backoff
      reconnect, registered `KALSHI-PERP`, canonical `book_snapshot` BBO+depth, 37 tests) + `polymarket_perp_ws.py`
      scaffold (`_ENDPOINT_LIVE=False`, BLOCKED-UPSTREAM, registered `POLYMARKET-PERP`, 28 tests); both in
      `register_all()`; QG green (5161+65 tests, 81.03%). **UAC FIX**: `live_source_for_venue` perp-venue override
      (`KALSHI-PERP`→`kalshi_perp` not batch-only `tardis`) — caught + fixed a `live_pipeline_mode_for_venue` ValueError
      that would have crashed the live runner; regression test added. Kalshi-perp live-ready (`live_kalshi_perp`);
      Polymarket-perp scaffold BLOCKED-UPSTREAM. — 2026-06-21
- [x] ✅ [SCRIPT] P2. deployment-service — perp CLOB live-recording launcher SHIPPED (deployment-service@86f517d):
      `scripts/vm/launch-perp-clob-live.sh` — KALSHI-PERP → e2-standard-8 VM
      (`VM_TASK=mtds-live`/`VM_OPERATION=live_websocket`/`MANIFEST_PER_VM_SHARDS=true`, shard
      `cefi:KALSHI-PERP:book_snapshot`→slug `cefi-kalshi-perp-book-snapshot`, prefix covered by `mtds-live-cefi-` in
      vm_zombie_watchdog LONG_LIVED_LIVE), singleton-locked per shard; POLYMARKET-PERP → clean early-exit
      BLOCKED-UPSTREAM (no doomed VM); live=batch parity (same UAC `book_snapshot`, only pipeline_mode differs
      live_kalshi_perp vs batch_kalshi_perp); lifecycle marker (Epic predictions_master/permanent). QG green. —
      2026-06-21

- [x] ✅ [SCRIPT] P2. **Kalshi PREDICTION live CLOB depth → `book_snapshot_5` SHIPPED** (mtds@425b1e8):
      `live/connectors/kalshi_clob_ws.py` (`KalshiClobWSFeedConnector`, ws `orderbook_delta` snapshot+delta, top-5 →
      `book_snapshot_5`, venue KALSHI, asset_group prediction; coexists with the lowercase `kalshi` trades connector);
      registered in `register_all()`; 577-line test suite; QG green. Verified
      `live_pipeline_mode_for_venue('prediction','KALSHI','book_snapshot_5')→live_kalshi`. **Phase-3 both-venues live
      CLOB depth COMPLETE** (Polymarket@26297e4 + Kalshi@425b1e8). — 2026-06-22

## Phase 4 — arb wiring

- [x] ✅ [DESIGN] P2. strategy-service — perp funding wired into funding-rate-arb + basis archetypes SHIPPED
      (strategy-service@31ba481f): `catalog_carry.py` `_CARRY_BASIS_PERP_VENUE_BUNDLES` (10→12) +
      `_FUNDING_DISPERSION_VENUES` (4→6) += `(kalshi,KALSHI-PERP,USDC)` + `(polymarket,POLYMARKET-PERP,USDC)` (slot
      tokens from UAC `_PREDICTION_TOKENS`); 8 tests; QG green. POLYMARKET-PERP wired for honest-absence
      (BLOCKED-UPSTREAM — flows when endpoint recovers, no code change). — 2026-06-21

## Codex SSOT updates

- [x] ✅ [DOCS] P2. codex/02-data — prediction-perps sourcing doc WRITTEN (`prediction-perps-sourcing.md`) +
      prediction-data-types-catalog.md cross-links it (KALSHI_PERP/POLYMARKET_PERP). Repo: unified-trading-pm. —
      2026-06-21

## Progress Log

### 2026-06-23 (autonomous) — P0 lifecycle ROOT CAUSE PROVEN + foundational IS fix shipped; remaining chain scoped

Drove the P0 honest-coverage / NULL-lifecycle finding to a **proven root cause** (prior sessions had only a vague "raw
gamma dump" hypothesis). Empirical findings (real GCS + live gamma API):

- `available_from_datetime`/`available_to_datetime` = **0% populated** on bare-path POLYMARKET catalogue parquets
  (`by_date/day=*/venue=POLYMARKET/instruments.parquet`, 0/452 sampled) and **~16%** on fresh cqg-first parquets
  (`canonical_question_group=*/day=2026-06-23/venue=POLYMARKET/`, 1495/9416). Confirms operator's 0/25 drill-down.
- `classify_lifecycle`'s parse logic is **CORRECT** — 200 live gamma markets (100 active + 100 closed) → **100% would
  classify**. NULLs are NOT a parse bug.
- **REAL root cause**: strict `classify_lifecycle` requires BOTH creation AND resolution ts; batch/date-mode markets are
  enumerated via the **CLOB-history path** (opaque short-key schema `r/t/c/mos/…`) carrying **no gamma lifecycle
  fields** → lifecycle None → both bounds NULL. Only the **gamma-active path** (`get_instruments(date=None)`/today)
  carries them → the ~16%.
- **Honest-coverage MATH confirmed** (`_honest_coverage_logic.compute_honest_coverage`): `empty_confirmed` (incl.
  `EXPECTED_INSTRUMENT_NOT_LISTED`) is NUMERATOR credit → out-of-existence cell scored "honestly answered" → inflates %.
  `was_instrument_alive(available_from, available_to, day)` **already exists** in UAC (`_honest_coverage_logic.py:400`)
  but is only used by the `EmptyFromLiveInstrumentError` backstop, NOT by the empty-emission decision.

**SHIPPED (foundational, strictly-better, verifiable):** IS `polymarket/parsing.py::_parse_market` now populates
`available_from/to` **directly + best-effort from gamma fields** (from = startDate|createdAt, to =
closedTime|endDateIso), preferring the strict lifecycle's settlement-lag-adjusted values when it classifies, else the
raw gamma bound. So the **gamma-active/live universe now fully carries bounds**; partial-gamma markets get a partial
bound (beats NULL). 2 regression tests added; 16/16 lifecycle tests pass; IS QG green. — **instruments-service@be45660**
| QG-green sentinel.

**BIG-FINDING — remaining P0 chain is a deep, fleet-blast-radius multi-stage fix (operator: this is data-correctness,
honest-coverage semantics).** The `_parse_market` tweak is necessary-but-INSUFFICIENT: it does not help CLOB-history
markets carrying NO gamma fields, and does not change the existing 142k manifest empties or the inflated %. Full fix =
the open P0 sub-todos below (item-43a..43d).

- [ ] [SCRIPT] P0. **43a — IS enumeration-merge: enrich EVERY POLYMARKET market with gamma lifecycle**: the batch/CLOB-
      history enumeration path (markets that ended on a historical date, opaque schema) carries no gamma
      startDate/endDate, so `_parse_market`'s new bound-derivation gets None. Fix = fetch the gamma record per
      condition_id during CLOB-history enumeration (or derive `available_to` from the CLOB market's own resolution ts +
      `available_from` from first-trade ts) so ALL catalogue rows carry `available_from/to`, not just the gamma-active
      subset. Verify: re-enumerated POLYMARKET parquet shows `available_from/to` populated ≫16%. Repo:
      instruments-service (`polymarket/markets.py` CLOB-history fetch). Provenance: autonomous P0 root-cause 2026-06-23.
- [ ] [SCRIPT] P0. **43b — emission bounding (MTDS/UTL): only emit a manifest cell within the market's life**: the
      honest-absence emitter (IS `enumerate_expected_universe.py` v2 + MTDS preflight) must call UAC
      `was_instrument_alive(available_from, available_to, day)` so a date OUTSIDE `[available_from, available_to]` is an
      honest BLANK / `expected_unattempted`, NEVER `empty_confirmed[EXPECTED_INSTRUMENT_NOT_LISTED]`. Today the emit is
      driven by per-date catalogue MEMBERSHIP, not lifecycle bounds. Repos: instruments-service +
      market-tick-data-service / unified-trading-library. Provenance: autonomous P0 root-cause 2026-06-23.
- [ ] [UAC] P0. **43c — coverage-math: exclude out-of-existence reasons from the numerator-credit (CROSSCUTTING — fleet
      blast radius)**: `EXPECTED_INSTRUMENT_NOT_LISTED`/`EXPECTED_PRE_VENUE_LAUNCH`/`EXPECTED_INSTRUMENT_DELISTED` are
      "market did not exist", not "honest empty" → exclude from BOTH numerator + denominator (mirror
      `is_resolved_schedule_empty` for FIXTURES), so out-of-life cells read as BLANK, not coverage-success. Bucketing
      lives in deployment-api `services/data_status/coverage_metrics.py` + UTL `manifest_writer/_queries.py` + mtds + IS
      `api/data_status.py` — must change ALL consistently + VERIFY recomputed % on real GCS for EVERY asset_group +
      check CI honest-coverage ratchets don't break (rule 11 — prove fleet-wide before shipping). Repo:
      unified-api-contracts (define `OUT_OF_LIFECYCLE_EXCLUDED_REASONS` + helper) + the 4 consumer bucketers.
      Provenance: operator empty_confirmed drill-down + autonomous P0 root-cause 2026-06-23.
- [ ] [SCRIPT] P0. **43d — re-walk to reclassify the ~49.6k out-of-life empties**: after 43a-c land + a fresh tarball,
      run `market_tick_data_service/scripts/rebuild_prediction_manifest.py --venue {POLYMARKET,KALSHI}` (VM job) to
      physically convert out-of-life `empty_confirmed[EXPECTED_*]` cells → BLANK/`expected_unattempted`; audit whether
      the 93,264 `SOURCE_RETURNED_ZERO` include out-of-lifecycle dates (same root cause). Verify honest % recomputed
      over the in-lifecycle universe. KALSHI lifecycle already flows onto `available_from/to` (`kalshi.py:816-817`) —
      verify it survives the same CLOB-vs-gamma split. Repo: market-tick-data-service. Provenance: autonomous P0
      2026-06-23.

### 2026-06-23 (autonomous) — fixture-level cross-venue linking is FEASIBLE (Kalshi event tickers encode teams+date)

Operator: there's a lot more cross-venue sports/politics we can DIRECTLY link via fixture ids (tennis/NFL/NBA/soccer).
Confirmed feasible — Kalshi GAME-series EVENT tickers encode the fixture cleanly: `KXMLBGAME-26JUN251945AZSTL` =
`KX{LEAGUE}GAME-{YY}{MON}{DD}{HHMM}{AWAY}{HOME}` (title "Arizona vs St. Louis"). So a canonical fixture key
`(league, {away,home} normalized, date)` is extractable per venue. **UAC schema already supports this** —
`PredictionMarketCrossVenueMapping` (`kalshi_event_ticker`/`polymarket_condition_id`/`api_football_fixture_id`/
`odds_api_event_id`/`canonical_event_id`) + `CanonicalPredictionMarket.mapped_sport_event_id` exist but are unpopulated.

- [ ] [DESIGN] P1. **Fixture-level cross-venue PAIRING — parse fixture identity from both venues + link to the sports
      canonical fixture registry**: (1) Kalshi — parse `KX{LEAGUE}GAME-{YYMONDD}{HHMM}{AWAY}{HOME}` (and the per-league
      variants) from the EVENT ticker → `(league, away, home, date)`; map Kalshi team abbreviations → canonical teams.
      (2) Polymarket — parse the equivalent from the gamma slug/title (e.g. `nfl-{away}-{home}-{date}`). (3) Resolve
      BOTH to a canonical fixture id via the existing **sports domain** fixture registry (api-football fixture /
      odds-api event — the system already has canonical sport events), populating `mapped_sport_event_id` +
      `PredictionMarketCrossVenueMapping`. (4) Same-settlement guard (same game/start-time) before pairing. This is the
      per-instrument arb pair WITHIN the shared `SPORTS_{LEAGUE}_{BETTYPE}` cqg category. Extend beyond the 17 mapped
      leagues + to tennis (player-pair) + politics (election/Fed event ids). Build against REAL ticker/slug samples (no
      guessing — per-league formats vary). Repo: unified-api-contracts (fixture parser + mapping populate) +
      features-service/strategy-service (arb pairing) + instruments-service (sports-event link on enum). Provenance:
      operator "parse fixture ids for tennis/nfl/nba/soccer" 2026-06-23. (Supersedes the earlier P2
      per-instrument-pairing todo with the concrete fixture-encoding evidence.)

### 2026-06-23 (autonomous) — P0 DATA-CORRECTNESS: 142k POLYMARKET empty_confirmed inflated by NULL instrument lifecycle (operator drill-down — CONFIRMED)

Operator asked whether the 142,874 POLYMARKET `empty_confirmed` cells are genuine no-data days or instrument-catalogue
mislabeling ("we don't have the right start/end times → labelling empty_confirmed when the market wasn't supposed to
exist"). **CONFIRMED — mislabeling.** Drill-down (`market-data-tick-pred-prd/_index`):

- error_reason: **`EXPECTED_INSTRUMENT_NOT_LISTED` = 47,922** + `EXPECTED_PRE_VENUE_LAUNCH` 974 +
  `EXPECTED_INSTRUMENT_DELISTED` 713 = **~49.6k cells where the market was NOT listed / did not exist** for that date —
  yet recorded `empty_confirmed` (counts in the honest-coverage NUMERATOR). The other 93,264 are `SOURCE_RETURNED_ZERO`
  (legit only if the market existed+traded that day).
- **ROOT CAUSE (verified)**: IS POLYMARKET instrument records carry `available_from_datetime` = **0/25 populated** and
  `available_to_datetime` = **0/25** (all NULL) — the catalogue has NO market start/end times. The POLYMARKET prediction
  enumeration writes a raw `PolymarketGammaMarket` dump that never maps gamma `startDate`/`endDate` → no lifecycle bound
  → expected-universe + honest-absence enumerate (instrument/cqg × date) cells OUTSIDE the market's life →
  out-of-existence dates become `empty_confirmed [EXPECTED_INSTRUMENT_NOT_LISTED]` instead of an honest blank. Exactly
  the operator's call.
- **Impact**: honest coverage (POLYMARKET 95.54%) is over an inflated set including non-existent-market cells; manifest
  is full of meaningless empties rather than blanks-where-data-was-expected.

- [ ] [SCRIPT] P0. **Populate POLYMARKET instrument lifecycle start/end + bound manifest empty-emission to it (honest-
      absence correctness)**: (1) IS — the POLYMARKET prediction enumeration (gamma raw-market write path) MUST set
      `available_from_datetime` from gamma `startDate`/`createdAt` + `available_to_datetime` from `endDate`/`closedTime`
      (today both NULL → 0/25). (2) MTDS/UTL honest-absence — only emit a cell (captured/empty/failed) for dates WITHIN
      `[available_from, available_to]`; outside the market's life = honest BLANK (absence) / `expected_unattempted`,
      NEVER `empty_confirmed`. Reconsider whether `EXPECTED_INSTRUMENT_NOT_LISTED`/`PRE_VENUE_LAUNCH`/`DELISTED` belong
      in `EMPTY_CONFIRMED_REASONS` (UAC) — operator: "better to have the blanks where we expected data." (3) Re-walk
      (`rebuild_prediction_manifest --venue POLYMARKET`) to drop/reclassify the ~49.6k out-of-existence empties so
      honest coverage reflects the in-lifecycle universe; audit whether the 93,264 `SOURCE_RETURNED_ZERO` include
      out-of-lifecycle dates (same root cause). **Same NULL-lifecycle check for KALSHI** (adapter sets
      `market_created_at`/`resolution_time` on MarketLifecycle — verify `available_from/to_datetime` flow onto the
      InstrumentRecord). Repo: instruments-service (gamma lifecycle population) + market-tick-data-service / UTL
      (emission bounding) + unified-api-contracts (EMPTY_CONFIRMED_REASONS taxonomy). Provenance: operator
      empty_confirmed drill-down 2026-06-23. **BIG finding — data-correctness, honest-coverage semantics.**

### 2026-06-23 (autonomous) — FINAL REPORT: P1 cross-venue Kalshi canonicalization RESOLVED + VERIFIED + LIVE; partition-completeness answered (real GCS numbers)

**P1 (cross-venue Kalshi grouping) — DONE + VERIFIED end-to-end.** Root cause was NOT the mapper (comprehensive since
c3bf51d1) — it was the IS Kalshi enum capping at 2000 `status=open` markets FLOODED by `KXMVE*` multivariate parlays →
all crypto/macro/sports pushed out → catalogue all-OTHER. Fixed with **series-scoped enumeration** (fetch the
cross-venue-relevant series via `/markets?series_ticker=`, non-OTHER-filtered, throttled w/ 429 backoff) + the **Kalshi
sports classifier** (per-game → shared `SPORTS_{LEAGUE}_{BETTYPE}`) + **KXRIPPLE→XRP** + **EUR-FX collision fix** + the
**`not historical` guard fix** (a dated `--mode batch` re-enum was skipping series-scoped).

**Shipped (fleet, on LDR):** UAC classifiers.py (sports + KXRIPPLE + EUR + 6 tests) · IS kalshi.py (series-scoped +
throttle + Sports/Politics categories + guard fix + 4 tests). UAC & IS QGs green.

**VERIFIED — real GCS numbers (2026-06-23):**

- **IS catalogue cqg split (`instruments-store-pred-prd`, day=2026-06-23):** venue=KALSHI **1 → 34 cqg partitions** (was
  all-OTHER): crypto BTC/ETH/SOL/XRP/DOGE/BNB/HYPE (up-down + range), indices SPX/NDX/DJIA/RUT, macro
  CPI/FED/GDP/NONFARM_PAYROLLS/PCE/TREASURY, CRUDE_OIL, EUR, **SPORTS_MLB_MATCH/SPREAD/TOTAL + SPORTS_NFL_MATCH +
  SPORTS_WORLD_CUP_MATCH**. venue=POLYMARKET = 27 cqg (unchanged). Re-enum wrote 6887 KALSHI records across 34 groups
  (OTHER=2004 = the KXMVE parlays, correctly).
- **MTDS tick manifest 4-state + honest coverage (UAC `compute_honest_coverage`, `market-data-tick-pred-prd/_index`,
  194,238 rows):**
  - POLYMARKET **95.54%** — 168,259 cells (captured 17,405 / empty_confirmed 142,874 / attempted_failed 7,507 / eu 473).
  - KALSHI **68.55%** — 25,790 cells (captured 18 / empty 17,657 / **attempted_failed 8,112** / eu 3). The 8,112 failed
    cells are the pre-endpoint-fix Kalshi trade/book failures (the `/markets/trades` 404 era + book) — they re-resolve
    to captured/empty on the 1.2 backfill with the fixed adapter.
- **Live evidence:** 4 `prediction-live-*` VMs RUNNING; the 2 KALSHI shards relaunched on the cqg-fixed tarball resolve
  the full **6887-instrument** universe (was 2000-flooded), 0 errors. POLYMARKET shards untouched (unaffected).
- **Cross-venue overlap set (Kalshi ∩ Polymarket, live 2026-06-23) ≈ 18 shared groups** (was ~16; +SPORTS_MLB):
  BTC/ETH/SOL/XRP/DOGE/BNB/HYPE `_UP_DOWN_DAILY`, BTC/ETH/SOL/XRP `_PRICE_RANGE_DAILY`, SPX/DJIA/RUT `_UP_DOWN_DAILY`,
  CRUDE_OIL, **SPORTS_MLB_MATCH/SPREAD/TOTAL**. Kalshi-rich-but-Polymarket-not-live-today: CPI/FED/GDP/payrolls/PCE/
  treasury/NDX (auto-pair when Polymarket lists them — groups are shared). The KXRIPPLE fix specifically enabled XRP
  overlap; the sports classifier enabled the MLB overlap.

**Partition-completeness (operator Q "do partition updates need migrations/backfills for live+batch?"):**

- **No raw-tick GCS migration** (cqg is NOT a raw-tick partition key) ✓ — verified.
- **Catalogue** (cqg-partitioned): today refreshed (34 groups) ✓; recent-window re-enum = tracked todo (rides 1.2).
- **Live**: relaunched ✓ (6887 universe resolved on fixed code).
- **Batch** historical cqg re-walk (`rebuild_prediction_manifest --venue KALSHI`, ~5000s VM job): tracked P1 todo.
- Determinism holds (stable classifier hash) → batch re-walk == live capture.

**Tracked remaining (precise todos filed above):** batch cqg re-walk · recent-window catalogue re-enum · politics/geo
cross-venue canonicalization (wording-sensitive, needs arbability analysis) · per-instrument same-game arb pairing
(strategy layer) · 1.1 Polymarket batch book_snapshot_5 row-proof · 1.2 Kalshi batch recent-window+mid-gap backfill ·
1.3 manifest hygiene (313 lowercase/blank venue + 1,454 v4 rows, NICE-TO-HAVE). Polymarket-perp stays BLOCKED-UPSTREAM.

**Also this session (operator side-requests):** PM synced (was 322 behind on a regen-churn dirty file) · 5 service repos
unblocked from `uv.lock` internal-version-drift churn + durable cron auto-discard shipped (PM PR#512) · prediction alert
triage (`DP_CATALOG_NOT_RUNNING` = stale transient, catalog fresh 17:10Z; the 55 VM_STALL/13 VM_GONE are tradfi/sports).

### 2026-06-23 (autonomous) — Kalshi canonicalization EXPANDED to sports + EUR-FX collision fix (operator: "do proper kalshi / more crossover")

Operator flagged the cross-venue overlap was too narrow (only ~16 crypto/index groups) and wanted MORE — sports,
commodities, FX, politics — wherever both venues have genuinely-arbable (same settlement event+time) markets. Two root
causes found + fixed:

1. **Capture gap** — the series-scoped enumeration only fetched Crypto/Economics/Financials categories → Kalshi's Sports
   (2239 series) + Politics (2049) weren't enumerated at all. FIXED: `_SERIES_CATEGORIES` += Sports, Politics (IS
   kalshi.py); `_MAX_SERIES_TOTAL` 200→350.
2. **Classifier gap** — no Kalshi sports rules. FIXED (UAC classifiers.py): added `_kalshi_sports_group` — maps Kalshi
   per-GAME markets (`KX{LEAGUE}…GAME` / `*SPREAD` / `*TOTAL` / `*NRFI`) to the SAME `SPORTS_{LEAGUE}_{BETTYPE}` groups
   Polymarket uses (reuses the existing `_SPORTS_GROUP`), for the 17 leagues with a canonical group. **Arbability
   judgment (the operator's "you're an LLM, understand the meaning"):** ONLY clean per-game markets map (same game =
   same settlement = pairable); season-futures / draft / awards / within-match props / minor world leagues
   (Liiga/KHL/NPB/…) stay OTHER — no false pairs. Verified vs live `/series?category=Sports`: 91 sports series now map
   (was 0): NFL/NBA/MLB/NHL match+spread+total, EPL/LA_LIGA/SERIE_A/BUNDESLIGA/CHAMPIONS_LEAGUE/WORLD_CUP match, MLB
   NRFI, tennis, boxing. Total Kalshi non-OTHER series 255→342.
3. **EUR-FX collision (pre-existing bug) FIXED**: the greedy `KXEURO` prefix wrongly classified EuroLeague/EuroCup
   basketball + Eurovision as `EUR_UP_DOWN_DAILY`. Dropped bare `KXEURO`; added `KXEURUSD` (the real EUR/USD daily
   series KXEURUSDD etc. were previously UNMAPPED→OTHER). Now KXEUROLEAGUE*/KXEUROCUP*/KXEUROVISION*→OTHER, KXEURUSD*/
   KXEUROIMF→EUR. Regression test added.

Shipping: UAC classifiers.py + tests + IS kalshi.py category expansion. KXRIPPLE→XRP + series-scoped enum + throttle
already on LDR.

**Tracked tail (judgment-heavy, NOT silently deferred):**

- [ ] [UAC] P2. **Politics/geo cross-venue canonicalization** — Kalshi Politics (2049 series: electoral-college
      KXECDJT/KXECKH, KXTRUMPPUTIN, KXSWINGSTATES, KXMAG, geo) don't cleanly align with Polymarket's TRUMP_STATEMENTS /
      TRUMP_APPROVAL / ELECTION_PRESIDENT_2028 / GEO_ISRAEL_IRAN / GEO_RUSSIA_UKRAINE groups — the specific events +
      settlement wording differ, so blanket mapping would create FALSE arb pairs. Needs per-family arbability analysis
      (which Kalshi political series resolve on the SAME event+criteria as a Polymarket group) + possibly the World
      category
  - new shared geo groups. Repo: unified-api-contracts (classifiers + maybe canonical_groups) + instruments-service (add
    "World" category once mapped). Provenance: operator "do proper kalshi / more crossover" 2026-06-23.
- [ ] [DESIGN] P2. **Per-instrument same-game/same-settlement arb PAIRING within a shared cqg group** — the cqg is the
      CATEGORY (discovery); the actual arb pair is two instruments on the SAME real-world event (same NFL game / same
      CPI print / same BTC daily strike+expiry) across venues. The pairing logic (match Kalshi event_ticker ↔ Polymarket
      condition_id by teams+date / strike+expiry / release+date, with a same-settlement-time guard) lives in the
      strategy/features arb layer, NOT the cqg classifier. Repo: strategy-service (arbitrage_price_dispersion) +
      features-service. Provenance: operator 2026-06-23 — "so we can easily pair them up properly".

### 2026-06-23 (autonomous, continuous-flow) — fleet uv.lock unblock + P1 Kalshi-grouping ROOT CAUSE = enumeration KXMVE-flood (NOT the mapper)

**Operator side-requests (DONE first):** (1) PM repo was 322 commits behind, blocked by a dirty
`canonical-dependency-manifest.json` (regen `generatedAt`-timestamp churn) → stashed + FF-pulled to current. (2) **5
service repos stranded 11–54 commits behind on dirty `uv.lock`** (e2e-testing/fund-administration-service/
strategy-service/system-integration-tests/trading-agent-service) — the dirty lock was pure **internal editable-package
`version =` drift** (e.g. strategy-service 0.15→0.36, UAC 0.19→0.47, UTL 0.13→0.35) from a non-frozen
`uv sync`/`uv lock` (setup.sh), which the FF-pull cron's auto-discard set did NOT cover → `[skip:dirty]` → stranded.
Cleared all 5 (stash + FF-pull → now 0/0 clean; entire service fleet 0/0). **Durable fix shipped** (PM PR#512,
auto-merging): added a uv.lock internal-version-drift auto-discard to `scripts/dev/slot-cron-ff-pull.sh`, gated to
"uv.lock diff = `version =` lines only" (a real external floor bump also dirties pyproject.toml → preserved →
skip:dirty). `pm-pull-ff.sh` needs no change (PM has no uv.lock).

**P1 Kalshi canonical grouping — the premise was STALE; the real bug is the ENUMERATION CAPTURE.** Grep-then-read +
empirical verification found: `classify_kalshi_to_canonical_group` (UAC `classifiers.py`) ALREADY carries a
comprehensive `KALSHI_TICKER_PREFIX_TO_GROUP` (landed `c3bf51d1` 2026-06-20) wired into the IS Kalshi adapter
(kalshi.py:658) + IS orchestrator (prediction.py:96) + MTDS adapter. Classifying the LIVE `/series` catalogue (5,802
series across Crypto/Economics/Financials/Politics/Sports) through it: **~255 series correctly map to SHARED Polymarket
groups** (BTC_PRICE_RANGE×37, SPX_UP_DOWN×29, FED×24, CPI×17, SOL×18, ETH×13, EUR×12, NDX×11, DOGE/GDP/GOLD/XRP/…). So
the mapper is NOT the gap. **The ACTUAL root cause**: the catalogue's `venue=KALSHI` day=06-22/06-23 holds only
`canonical_question_group=OTHER` — 2000 markets, **ALL `KXMVE*` (multivariate parlay/cross-category) tickers**. The IS
Kalshi live enumeration caps at `_MAX_PAGES=10` (2000 markets) of `/markets?status=open`, and Kalshi's open universe is
**dominated by auto-generated KXMVE parlay markets**, so the crypto/macro markets (the cross-venue arb universe) get
pushed out of the 2000-cap and are NEVER enumerated. `?category=Crypto` on `/markets` is ignored (still KXMVE-flooded),
but **`/markets?series_ticker=KXBTCD&status=open` works perfectly** → fix = series-scoped enumeration of the
cross-venue-relevant families (in progress, IS kalshi.py).

**Shipped this session:** (a) UAC `classifiers.py` — `KXRIPPLE*` → XRP groups (Kalshi lists XRP under the legacy
"RIPPLE" stem; verified live, was falling to OTHER → split XRP off its Polymarket counterpart) + 2 new tests
(real-live-ticker→shared-group coverage + Kalshi↔Polymarket cross-venue same-group invariant); UAC QG green (252s). (b)
IS `kalshi.py` stale docstring fixed (claimed "override-only→OTHER"; the prefix classifier has been wired since
c3bf51d1). **In progress:** IS series-scoped enumeration so the crypto/macro universe is captured + re-enumerate +
cross-venue overlap report.

### 2026-06-23 (autonomous catalogue/backfill session) — ITEM B book_snapshot_5 batch path: THREE stale-registry gates found+fixed; row-verify in flight

The batch book_snapshot_5 path needed THREE fixes beyond the adapter to actually capture (each found by a T+ verify
catching a silent exit-0/0-row, per no-fire-and-forget): (1) adapter `download_batch` ignored `data_types` → branch
trades/books (mtds@050ce12) + batch=live schema fix to match the live WS shape (mtds@7c849d7); (2) UAC
`expected_coverage._PREDICTION` + `DATA_TYPES_BY_ASSET_GROUP["prediction"]` re-add of book_snapshot_5 (uac@1596d4f9);
(3) **the REAL pre-flight gate** `VENUE_DATA_TYPE_CAPABILITIES` (`get_expected_data_types_for_venue` reads THIS, not
`_PREDICTION`) — book_snapshot_5 added for POLYMARKET+KALSHI start=2026-06-22 (live-onset) (uac@1a8e9217). Rebuilt
UAC+mtds tarballs from clean LDR; relaunched `mtds-prediction-polymarket-20260623-183343`
(`--data-types book_snapshot_5` 06-21→06-22) on the fixed stack — the pre-flight NO LONGER drops book_snapshot_5
(book5_dropped=0 confirmed); row-count verification in flight. Lesson: the prediction data_type registry was stale in 3
places after the 2026-04-19 book_snapshot_5 retirement; the live producers capturing it on prd proved it should never
have been retired.

### 2026-06-23 (autonomous catalogue/aggregation session) — ITEM A: prediction instruments-catalogue daily aggregation DEPLOYED + honest 4-state denominator VERIFIED (99.73%)

**Operator's ITEM-A concern (honest manifest numerators+denominators for prediction, like tradfi/cefi) — RESOLVED.**
Findings + fixes:

- **Catalogue daily-aggregation IS deployed** — two Cloud Run jobs + schedulers per AG:
  `lifecycle-catalogue-regen-prediction` (01:00 UTC, runs `build_instrument_catalogue.py --asset-group prediction` →
  `gs://instruments-store-pred-prd-…/prod/catalog.parquet`, the cumulative `available_from`/`available_to` lifecycle
  catalogue) + `expected-universe-v2-prediction` (01:30 UTC, runs
  `enumerate_expected_universe.py --enumerator-version v2 --apply-write` → seeds `expected_unattempted` at shard grain).
  TF: `lifecycle_catalogue_scheduler.tf` + `expected_universe_v2_scheduler.tf`.
- **GAP 1 (FIXED) — all 5 `lifecycle-catalogue-regen-*-daily` schedulers were PAUSED since 2026-06-14** (intended
  un-pause after the instrument backfill per `instruments_mtds_subset_consistency_remediation_2026_06_17.md` B1) →
  `catalog.parquet` STALE at 2026-06-19 (Kalshi absent, since Kalshi enumeration only started 06-22). Un-paused all 5
  (live).
- **GAP 2 (FIXED, deployment-service@040e2fc) — the `lifecycle-catalogue-regen` SA had NO `run.invoker`** (the same
  silent gap the expected_universe_v2 tf already fixed 06-22) → un-pausing alone would 've failed with scheduler
  `status code 7 (PERMISSION_DENIED)`. Added the `google_cloud_run_v2_job_iam_member` run.invoker block to the tf (all 5
  AGs) + granted it LIVE on all 5 jobs. Verified the scheduler now triggers cleanly (status.code empty, was 7/-1).
- **GAP 3 (FIXED) — stale lowercase `venue=kalshi` dup** (1 by_date blob, day=2026-06-22, 4001 rows, pre-venue-case-fix)
  split the Kalshi catalogue (`KALSHI` 8001 + `kalshi` 4001). Deleted the stale lowercase blob (canonical uppercase
  `KALSHI` 06-22 present alongside). Re-ran the catalogue with `--allow-catalogue-shrink` (the build script's monotonic
  shrink-guard correctly BLOCKED the −4001 corrective shrink with `exit 1`+`CATALOGUE_SHRINK_BLOCKED` — that was the
  "exit(1)" two scheduler runs hit; the override is the documented escape for a legitimate dedup). **Promoted fresh
  catalog: 1,132,497 rows, POLYMARKET 1,124,496 + KALSHI 8001, 0 lowercase, data_types
  trades/market_lifecycle/prediction_canonical_question_group, `available_from` 2025-03-13 → 2026-06-23.**
- **Honest 4-state denominator VERIFIED** — re-ran the v2 enumerator off the fresh catalog (Cloud Run
  `expected-universe-v2-prediction-ggmbt`, Succeeded). The prediction `_index` 4-state: captured 33,150 /
  empty*confirmed 160,491 / expected_unattempted 476 / attempted_failed 50. Fed through the canonical UAC SSOT
  `compute_honest_coverage` (numerator=captured+empty_confirmed+eu_known_empty;
  denominator+=attempted_failed+eu_pending_fetch) → **0.9973**. Denominator is the IS-listed could-exist universe, NOT
  re-derived per consumer (the UAC `_honest_coverage_logic.py` SSOT all consumers call). `empty_confirmed` (genuine
  no-trade-that-day, SOURCE_RETURNED_ZERO) counts as honestly-answered; API-failure → attempted_failed (gap);
  EXPECTED*\* lifecycle → known_empty (numerator).
- **MTDS pre-flight gated to IS universe — CONFIRMED**: live runner
  `_read_prediction_is_universe_sync`/`_filter_prediction_is_blobs` (only resolves IS-listed instruments, honest-skip on
  none) + batch adapters' `_load_market_lifecycle_for_date` (primary `market_lifecycle/by_canonical_group/` +
  `instrument_availability/by_date/venue=X` fallback; "no instruments"→honest skip). Neither invents a non-existent
  instrument.
- **Self-sustaining going forward**: schedulers ENABLED (daily, no `--allow-catalogue-shrink` so they never silently
  shrink — the catalog only grows post-dedup) + run.invoker durable in tf. The 4-state denominator stays fresh daily.

Residual data-correctness items captured as todos below (lowercase-venue manifest rows; v4-schema Kalshi-history tail).

### 2026-06-23 (continuous-flow session) — inherited-WIP mtds fixes SHIPPED (mtds@aed9fb2); prediction-live STILL gated on a fresh-today IS token-id universe

The prior session's uncommitted mtds WIP (Kalshi `/markets/trades` endpoint fix + `_is_universe` solely-clob_token_ids
honest-skip + tests) was found dirty in the slot clone, QG-green'd (had to trim `get_trades_with_status` 51L→under-50L
method-size + clear a transient version-alignment drift), and **shipped via quickmerge → mtds@aed9fb2** (LDR; Tier-C
drain → staging ≤15min). So the CODE for prediction live (no 0x pollution) + Kalshi BATCH trades (endpoint 404 fix) is
now on the integration branch + will ride the next tarball.

**BUT prediction LIVE still captures 0 (honest empty) — the remaining blocker is the IS instrument-availability
universe, NOT code.** Measured 2026-06-23:
`instruments-store-prediction-…/instrument_availability/by_date/ canonical_question_group=*/day=*/venue=POLYMARKET/instruments.parquet`
is STALE at **max day=2026-05-22 across ALL cqg groups**, and the latest parquet (day=2026-05-22 OTHER) has **NO
`clob_token_ids` column** (46 gamma cols, `instrument_key`=0x condition_id). The live runner's
`_filter_prediction_is_blobs` requires `day>=today` → finds NO active token-id universe → `_is_universe` correctly
returns `[]` (honest) → every window `empty_confirmed`. The `expected-universe-v2-prediction` Cloud Run job (triggered
this session, Completed) only seeds `_index` expected_unattempted from
`gs://instruments-store-pred-prd-…/prod/catalog.parquet` — it does NOT write the token-id `instrument_availability`
parquet. `lifecycle-catalogue-regen-prediction` (runs `build_instrument_catalogue.py --asset-group prediction`) is
PAUSED. **This is the "needs a focused fresh-context IS session" item below** — the exact remaining fix is the IS
prediction write/consolidation path that refreshes `by_date/.../venue=POLYMARKET/ instruments.parquet` for the CURRENT
day WITH populated `clob_token_ids` (+ confirm the env-short `instruments-store-pred-prd-` vs env-less
`instruments-store-prediction-` bucket the live runner reads). Note an env-short/env-less bucket split exists between
the catalog (`-pred-prd-`) and the availability store (`-prediction-`) — verify the live runner + the writer agree on
ONE bucket (the defi gotcha class). Until that lands, relaunching the live VMs alone will NOT make them capture (the
universe is honestly empty). Kalshi live UNAFFECTED by this (it had its own batch-endpoint bug, now fixed). Provenance:
continuous-flow session `plans/active/data_completion_to_100_all_ag_2026_06_21.md` 2026-06-23.

### 2026-06-23 (autonomous) — ROOT CAUSE found + FIXED: writer sorts partition keys; live runner condition_id fallthrough poisoned the universe

**The "stale parquet / GcsEventSink" diagnosis was a RED HERRING.** The `Batch mode: using GcsEventSink bucket=…-events`
log is the OBSERVABILITY event sink (`build_event_sink`, for STARTED/STOPPED) — NOT the data sink. The data DID write.
The prior agent only probed `instrument_availability/by_date/day=<d>/venue=POLYMARKET/instruments.parquet` (the stale
bare-shape, mtime 2026-05-12) and concluded "writes don't refresh."

**Actual fact**: `StorageDataSink._build_partition_path` (UTL `protocol_impls.py`) **`sorted()`s the partition keys
alphabetically**. `_write_prediction_venue` passes `partition={day, venue, canonical_question_group}` → the real write
path is `instrument_availability/by_date/canonical_question_group=<G>/day=<D>/venue=POLYMARKET/instruments.parquet` (cqg
FIRST). My `--force` re-enum on 2026-06-23 WROTE 135 cqg parquets there (verified: MISC_NOVELTY = 1560 rows,
**instrument_key + clob_token_ids populated 1560/1560**, each a 2-element decimal-token list). The IS write path
(IS@1ecf5cb + IS@482b50f) is CORRECT — clob_token_ids flow end-to-end.

**The real remaining bug (FIXED)**: the live runner `_filter_prediction_is_blobs` matches suffix
`/venue=POLYMARKET/instruments.parquet` + `day>=today`, which correctly matches the fresh cqg paths BUT ALSO matches ~30
STALE future-dated (`day=2027..2029`) bare/`market=`-shape parquets (2026-05-12, clob_token_ids=`[]`).
`prediction_instrument_ids_from_df` for POLYMARKET, when clob_token_ids was absent/empty, FELL THROUGH to
`instrument_key`/`condition_id` and emitted `POLYMARKET:PREDICTION_MARKET:0x<condition_id>` — which the CLOB WS
connector CANNOT subscribe (it logs `unknown instrument '0x…'; skipping`). End-to-end test: 36879 keys resolved,
thousands were 0x-condition_ids.

**FIX — mtds@aed9fb2** `market_tick_data_service/live/_is_universe.py::prediction_instrument_ids_from_df`: POLYMARKET
now resolves SOLELY from `clob_token_ids`; absent column OR empty token lists → `[]` (honest skip + log), NEVER a
condition_id fallthrough (a bare condition_id is never a valid Polymarket CLOB subscription). Re-tested against the real
bucket: **17772 token_ids resolved, ZERO 0x-condition_ids** (stale future-dated shards cleanly skipped). Regression
tests updated in `tests/unit/test_websocket_runner.py` (`test_prediction_is_columns_map_to_connector_ids` +
`test_kalshi_bare_instrument_key_rebuilt_to_connector_form`) + fixtures (`_pred_parquet_df` writes the realistic
`clob_token_ids` shape). Stale-blob GCS deletion NOT done (4542 legacy-shape blobs incl. past-dated 2025-03 ones the
BATCH historical path may read; the code fix neutralises live pollution honestly — destructive delete unwarranted).

### 2026-06-23 (autonomous) — Kalshi batch trades 0-capture = REAL BUG (endpoint moved), FIXED

The 6001 KALSHI `trades` `SOURCE_RETURNED_ZERO` are ALL dated 2026-06-22/23 (within the ~60-day API window — NOT the
honest old-history case). Live-probed the Kalshi v2 API: `GET /markets/{ticker}/trades` (the adapter's path-form URL)
returns **`404 page not found`** for every ticker; the current endpoint is the COLLECTION route
`GET /markets/trades?ticker=<t>` → HTTP 200 (verified 50–100 real trades + working cursor + min_ts on a liquid market
`KXWTAMATCH-26JUN22…`). **FIX — mtds@aed9fb2** `kalshi_adapter.py::get_trades_with_status`: URL → `/markets/trades`,
`ticker` moved to a query param. The UAC `KalshiTrade` schema already uses the current
`count_fp`/`yes_price_dollars`/`no_price_dollars` fields (parse layer fine — endpoint was the sole bug). CF-11 test
unaffected (mocks `.get` URL-agnostically).

### 2026-06-21 (PM-3) — LIVE prediction: infra PROVEN end-to-end; capture = design-gap tail (documented)

**Live pipeline is fully wired + proven** (7 sequential never-run-before bugs found+fixed): connector case-insensitive
resolve, bucket kind (market-data-tick-prediction flat key), recorder source-derive, row*key day->date, Gamma query
`condition_ids` (was clob_token_ids -> 422), launcher
`*`->`-`VM-name sanitization, CandleBoundaryCrossedEvent data_type enum (book_snapshot -> book_snapshot_5). The live VM now runs clean: connector fetches REAL Gamma prices (HTTP 200, no 422), manifest writes per-VM shards with correct`pipeline_mode=live_polymarket_clob`,
candle boundary flushes without error.

**Remaining: capture is `empty_confirmed` (row_count=0) — a DESIGN GAP, not a bug.** The Polymarket Gamma poller yields
a TOP-OF-BOOK quote (yes_price/no_price/best_bid/best_ask/last_trade_price), but no existing capturable data_type
candle-schema matches it: `trades` = actual trades (a price poll has none -> honest empty), `book_snapshot_5` = depth-5
levels (Gamma gives only top-of-book -> 0-row candle). Connector yields ticks correctly (verified: \_poll_one_cycle ->
\_parse_market_response -> yield); the runner's tick->candle aggregator produces 0-row candles because the tick shape
doesn't fit the data_type schema. NOT spin-fixable by relaunching.

- [x] ✅ [DESIGN] P2. **Polymarket live book = `book_snapshot_5` via the public CLOB order book** (operator decision
      2026-06-22 — NOT heavy design): the Gamma poll only gives top-of-book, BUT `clob.polymarket.com/book?token_id=<T>`
      returns the FULL depth ladder PUBLIC + NO AUTH (verified 2026-06-22: live bids 0.01/0.02/0.03/0.04/… w/ sizes).
      Decision = option (c)+canonical: take top-5 levels → emit `book_snapshot_5` (the exact cefi-canonical name, NO new
      data_type) — batch via REST `/book`, live via CLOB market WS `wss://ws-subscriptions-clob.polymarket.com/ws/`.
      Build = a Polymarket CLOB orderbook connector (depth) + runner tick→candle for book_snapshot_5 so live captures
      row_count>0. This also resolves the prediction side of item 75. Repo: market-tick-data-service (live/connectors +
      runner/sink). — mtds@26297e4 + uac@fb3b6999 | QG: mtds PASSED + uac PASSED — 2026-06-22
- [x] ✅ [DESIGN] P2. **UAC naming: SOURCE_PRIORITY uses `book_snapshot` but DataType enum uses `book_snapshot_5`** —
      FIXED (prediction-side only; cefi untouched per item 75-cefi scope): renamed prediction `book_snapshot` →
      `book_snapshot_5` in `_source_priority_data.py`, `availability_semantics.py`, `_sports_prediction_contracts.py`,
      `required_inputs.py`, 4 test files + added `test_live_pipeline_mode_for_prediction_polymarket_book_snapshot_5`.
      cefi `(cefi, book_snapshot)` entries deliberately preserved pending a separate cefi-handler audit (item 75-cefi).
      uac@fb3b6999 — 2026-06-22

### 2026-06-21 (PM-2) — LIVE prediction LAUNCHED (free Gamma poll) + Kalshi seed running

- [x] ✅ [SCRIPT] P1. LIVE prediction is WIRED + launchable end-to-end (no build needed): `polymarket_ws.py`
  - `kalshi_ws.py` live connectors EXIST + auto-register (`connectors/__init__.py` autoload),
    `launch-mtds-live.sh --asset-group prediction --shard-spec prediction:POLYMARKET:trades` exists, and the live
    `MTDSShardManifestRecorder` (fixed: asset_group is a writer kwarg) stamps `live_polymarket_clob` via the
    venue-source map. Polymarket live = free public Gamma REST poll (30s, no auth). **LAUNCHED**
    `mtds-live-prediction-polymarket-trades-20260621-155845` (10 high-volume active markets) → first-ever LIVE
    prediction rows (LIVE=0 across all AGs before this). Repo: deployment-service + market-tick-data-service.
- [x] ✅ [SCRIPT] P2. Live producer expanded to the FULL IS-enumerated active universe (WS-based) + all 4 prediction
      shards SHIPPED+LAUNCHED (mtds@b10c0fe runner `_resolve_is_universe` resolves the active universe from IS when
      `--instrument-ids` omitted, honest-absence via `record_zero_rows`; deployment@499a86c
      `launch-prediction-live.sh` + zombie-watchdog `prediction-live-` prefix LONG_LIVED_LIVE). **LAUNCHED 4 shards
      (2026-06-22, e2-standard-4, RUNNING)**: POLYMARKET×{trades,book_snapshot_5} + KALSHI×{trades,book_snapshot_5},
      IS-resolved full universe, replacing the old 10-market limited producer. WS-subscription path → no per-request
      rate limit (sidesteps item 128). T+10/+20 verification armed. — 2026-06-22

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
      `REPLAY_KALSHI`;
      `SOURCE_PRIORITY[(prediction, trades|book_snapshot|prediction_canonical_question_group)] += "kalshi"`;
      `SOURCE_MODE_CAPABILITY["kalshi"]={BATCH,LIVE,REPLAY}`; `EMISSION_LATENCY_MS_BY_SOURCE["kalshi"]=200`;
      `live_source_for_venue` prediction venue→source map (KALSHI→kalshi, POLYMARKET→polymarket_clob, unchanged). Test
      mirrors updated (capability `_BLR`, possible-manifest set, source_priority single→multi-source). Verified
      resolving: KALSHI/trades→batch_kalshi, POLYMARKET/trades→polymarket_clob (unchanged), live_kalshi/replay_kalshi.
      Repo: unified-api-contracts. — (shipping)
- [x] ✅ [UTL] P0. `pipeline_mode_resolver._VENUE_OVERRIDES["KALSHI"]` = `BATCH_KALSHI` (was the polymarket stub). Repo:
      unified-trading-library. — (shipping)
- [x] ✅ [SCRIPT] P0. mtds Kalshi bulk-seed converter — **batch=live inline cqg manifest**: emit one
      `record_captured_from_counts(source="kalshi", pipeline_mode=BATCH_KALSHI, asset_group=prediction)` per (day,
      KALSHI, cqg) bundle as it writes (single GCS walk; reads the cqg + available_at the converter already computes),
      unclassified tickers → `record_failed[ClassifierConfidenceLow]`. **Dropped the broken
      `rebuild_prediction_manifest --venue KALSHI` call from the runner** (wrong args + polymarket-cqg-specific
      classifier → would mis-classify Kalshi). 12 unit tests green. Repo: market-tick-data-service. — (shipping)
- [x] ✅ [SCRIPT] P0. mtds `manifest_finalize.py` — **prediction multi-source break-fix**: the live prediction cqg
      writer hardcoded `BATCH_POLYMARKET_CLOB` + auto-stamped source via `default_source` (now returns None for the
      multi-source cell → `MissingSourceError`). Made it venue-aware
      (`_resolve_pipeline_mode_for_sentinel(pred_venue, cqg)` → POLYMARKET=batch_polymarket_clob unchanged /
      KALSHI=batch_kalshi) + explicit `source=source_string_for(pm)`. Repo: market-tick-data-service. — (shipping)
- [x] ✅ [SCRIPT] P0. instruments-service `process_write.py` — **same multi-source break-fix in the IS enumeration cqg
      write path** (the runtime cause of the missing `venue=KALSHI` universe — the IS Kalshi enumeration
      `record_captured` for `prediction_canonical_question_group` raised `MissingSourceError` since cqg became
      multi-source). Added venue-derived `_cqg_pm` (POLYMARKET→`BATCH_POLYMARKET_CLOB` / KALSHI→`BATCH_KALSHI`) +
      `pipeline_mode=_cqg_pm` + explicit `source=source_string_for(_cqg_pm)`. IS QG-green (sentinel 42dd37c7). The
      companion UTL `record_captured_from_counts` `datetime` UnboundLocalError (introduced by the foreign
      DP\_\*/FetchEvidence WIP) was fixed and rode UTL@39f8ec85 to LDR. Repo: instruments-service@07272da4. — 2026-06-22

### 2026-06-22 — DEEPER root-cause chain (the source= fix was necessary but NOT sufficient — found by running the IS Kalshi enumeration end-to-end)

The `venue=KALSHI` universe was STILL silent-empty after the source= fix. Ran the IS prediction enumeration locally
(scoped `--venues KALSHI --start-date 2026-06-22 --force`, real GCS, against a clean UTL@39f8ec85 worktree to bypass a
concurrent UTL-refactor lane) and walked the full fetch→filter→bucket→write→manifest path. Three further bugs, two
fixed + verified, one systemic + still open:

- [x] ✅ [SCRIPT] P0. instruments-service `kalshi.py` — **date-filter silent-drop fix**: the Kalshi adapter's live
      `/markets?status=open` snapshot stamps `open_time` as an INTRADAY timestamp on the current day (e.g.
      `2026-06-22T13:21Z`), but `filter_instruments_by_date` compares `available_from <= date_dt` where
      `date_dt = fromisoformat(date)` = MIDNIGHT → `13:21 > 00:00` dropped EVERY Kalshi market on EVERY day (incl.
      today) → `0 records after filtering` → never reached the cqg write (so the source= error never even fired). Fix:
      floor `available_from_datetime` to the open DATE (a market opening any time on day D belongs to day D's universe;
      precise `market_created_at` still carried on the lifecycle for MTDS tick-gating). **Verified: 6/6 sample markets
      now survive (was 0/6); full enum `KALSHI: 2000 instruments after date filter` → manifest `availability_index` now
      shows KALSHI captured date=2026-06-22 with source=kalshi/pipeline_mode=batch_kalshi.** Repo: instruments-service
      (kalshi.py, QG-green vs clean UTL; ship BLOCKED on the concurrent UTL clone being conflict-marker-broken —
      quickmerge dep pre-flight). — 2026-06-22
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
      (cqg-FIRST, not day-first). Verified present (94KB, venue=KALSHI uppercase — the venue fix). DEBUG_SINKWRITE
      confirmed `rows=2000 wrote=True`. The "stale May-12 Polymarket" was the OLD day-first layout; current writes are
      cqg-sorted. So the full chain WORKS: filter (2000 survive) → cqg bucket → instruments.parquet @venue=KALSHI →
      manifest captured (source=kalshi) → lifecycle. **Kalshi LIVE producers RESOLVED the universe**
      (`prediction-live-kalshi-{trades,book_snapshot_5}` read venue=KALSHI; keep-alive ended 2026-06-22 14:06). No code
      change needed.
- [x] ✅ [SCRIPT] P0. **RESIDUAL — Kalshi live RESOLVES but SKIPS ticks (id-format mismatch)**: the live producers now
      find the Kalshi universe but log
      `KalshiClob: unknown instrument 'KXMVE…' — expected KALSHI:PREDICTION_MARKET:{ticker}; skipping` for every market
      → no real Kalshi ticks captured yet. Root: mtds `live/_is_universe.py::prediction_instrument_ids_from_df`
      short-circuits `if "instrument_key" in df.columns: return bare instrument_key` (line 27-28), and the IS Kalshi
      universe's `instrument_key` is the BARE ticker (the adapter sets `instrument_key=ticker`), while the KalshiClob WS
      connector parses the canonical `KALSHI:PREDICTION_MARKET:{ticker}`. Polymarket is unaffected (its connector
      accepts the bare `condition_id`). **Fix (pick one, Kalshi-scoped to avoid regressing Polymarket)**: (a) make the
      `instrument_key`-wins branch venue-aware — for KALSHI, if the key lacks `:PREDICTION_MARKET:`, rebuild
      `KALSHI:PREDICTION_MARKET:{ticker}`; OR (b) set the IS Kalshi adapter
      `instrument_key = f"KALSHI:PREDICTION_MARKET:{ticker}"` (canonical InstrumentKey form) — cleaner but audit
      cross-consumers (cqg classifier uses the ticker arg, not instrument_key, so likely safe). Verify the live
      connector captures after redeploy. Repo: market-tick-data-service (live/\_is_universe.py) and/or
      instruments-service (kalshi.py). Provenance: prediction-to-100% drive 2026-06-22. — mtds@aed9fb2 (option-a:
      venue-aware instrument_key branch rebuilds bare KALSHI ticker → `KALSHI:PREDICTION_MARKET:{ticker}`; docstring
      "KALSHI silent-empty fix 2026-06-22")

- [x] ✅ [SCRIPT] P3. **DISPLAY-ONLY bug (cosmetic) FIXED** (deployment-service@040e2fc):
      `launch-instruments-backfill-vm.sh` echo now prints `instruments-service-code.tar.gz` (the name
      `setup-data-pipeline-vm.sh` actually fetches), not the stale `instruments-code.tar.gz`. QG-green (isolated
      worktree, 47s). Provenance: prediction-to-100% drive 2026-06-22 → autonomous catalogue/backfill session
      2026-06-23.

**Seed relaunch (corrected stack):** UAC 24706977 + UTL b336478f + mtds fcd6549 all shipped; PREDICTION tarball rebuilt
to fcd6549 (foreign tradfi-lane deployment-service WIP forced `--allow-dirty-tarball`); stale VM (pulled old mtds
884560a) deleted; fresh seed VM `mtds-prediction-kalshibulk-20260621-155058` RUNNING on the verified-fcd6549 stack.

**Cross-cutting findings captured as todos (catalogue/aggregation session 2026-06-23):**

- [ ] [SCRIPT] P1. **Polymarket BATCH book_snapshot_5 backfill — UAC expected-coverage gap FIXED, needs
      re-tarball+relaunch (DISCOVERED+FIXED 2026-06-23)**: the first book_snapshot_5 batch backfill VM
      (`mtds-prediction-polymarket-20260623-180211`) exited 0 but captured 0 rows — pre-flight logged
      `dropping data_types not supported per UAC: ['book_snapshot_5']`. ROOT CAUSE: UAC
      `registry/expected_coverage.py::_PREDICTION` listed only `["trades", "prediction_canonical_question_group"]` for
      POLYMARKET / `["trades"]` for KALSHI — `book_snapshot_5` was retired there 2026-04-19 ("neither adapter captures
      order books") but BOTH venues now capture it (live WS + my batch /book path). FIXED (uac@<shipping>):
      `_PREDICTION` += `book_snapshot_5` for both venues. **REMAINING: re-build the mtds tarball AFTER the UAC ships
      (the 18:02Z tarball had the adapter but NOT this UAC fix) + relaunch the Polymarket book backfill → verify
      captured book_snapshot_5 rows.** Repo: unified-api-contracts (FIXED) + deployment-service (re-tarball+relaunch).
      Provenance: autonomous catalogue/backfill session 2026-06-23.
- [ ] [SCRIPT] P2. **Kalshi RECENT-window (2026-06-20..22) batch trades 0-capture — 2-stage IS-enumeration gap +
      cqg-path fallback (DISCOVERED 2026-06-23)**: the Kalshi recent-window backfill VM
      (`mtds-prediction-kalshi-20260623-180254`) exited 0 / 0 records — the `KalshiAdapter` instrument loader 404s on
      `instrument_availability/by_date/day=2026-06-20/venue=KALSHI/instruments.parquet` (the OLD day-first path shape)
      because (a) the IS writer SORTS partition keys → the real path is cqg-first
      `canonical_question_group=.../day=.../venue=KALSHI/` (the adapter's `instrument_availability` FALLBACK uses the
      stale day-first shape — should prefer the primary venue-agnostic `market_lifecycle/by_canonical_group/` store),
      AND (b) the IS Kalshi enumeration hasn't run for 06-20/06-21 (only 06-22/06-23 exist). Two-part fix: (a) point the
      KalshiAdapter `instrument_availability` fallback at the cqg-first shape (or rely solely on the
      `market_lifecycle/by_canonical_group/` primary), (b) run the IS Kalshi enumeration for the recent window before
      the MTDS backfill (the 2-stage IS→MTDS order). Repo: market-tick-data-service (kalshi_adapter fallback path) +
      instruments-service (recent-window enumeration). Provenance: autonomous catalogue/backfill session 2026-06-23.
      (Composes with the line-339 Kalshi-historical residual.)

- [ ] [DATA] P2. **Residual lowercase `venue=kalshi` + blank/UNKNOWN venue rows in the prediction `_index` manifest**
      (DISCOVERED 2026-06-23 verifying Item A): the consolidated
      `market-data-tick-pred-prd-…/_index/availability_index.parquet` carries ~124 `venue=kalshi` (lowercase,
      pre-venue-case-fix) + ~168 blank-venue + ~21 `UNKNOWN` rows alongside canonical `KALSHI` 25,605 / `POLYMARKET`
      168,249. These split the Kalshi denominator (a lowercase `kalshi` row is a phantom of `KALSHI`). The catalogue
      (instruments-store) was cleaned this session; the MANIFEST (market-data-tick) was NOT (a manual phantom-reconcile
      `--apply` is risky per CLAUDE.md — flips real captured→attempted_failed on a false positive). Fix = a scoped
      manifest canonicalisation that maps lowercase `kalshi`→`KALSHI` + resolves blank/UNKNOWN venue, bundled into the
      next prediction single-walk (NOT a standalone whole-corpus walk — single-walk discipline). Repo:
      market-tick-data-service (manifest canonicalisation). **NICE-TO-HAVE** — ~313 of 194k rows (~0.16%), does not
      materially move the 99.73% denominator.
- [ ] [DATA] P3. **1,454 prediction `_index` rows still at schema v4** (vs 192,713 at v9; DISCOVERED 2026-06-23): the
      Kalshi-history tail not yet re-walked to v9 (the POLYMARKET v9 re-walk completed; Kalshi-bulk seed rode a later
      stack). v9-schema polish only (rows already captured); rides the next prediction canonicalisation walk. Repo:
      market-tick-data-service. **NICE-TO-HAVE.**

**Cross-cutting findings captured as todos:**

- [x] ✅ [SCRIPT] P2. **Self-enforced rate-limit caps (token-bucket) on the prediction REST adapters — SHIPPED
      (mtds@bc31da6, 2026-06-23)**: replaced the REACTIVE 429-backoff-only throttle with a PROACTIVE async token-bucket.
      `base_prediction_adapter._AsyncTokenBucket` (asyncio + `time.monotonic()` refill, non-blocking `await acquire()`);
      per-venue caps Kalshi 8/s burst 8 (conservative vs published ~10 rps basic), Polymarket gamma/CLOB 20/s burst 20;
      `await self._rate_limiter.acquire()` wired before EVERY outbound REST `session.get` in `kalshi_adapter`
      (get_trades_with_status) + `polymarket_adapter` (get_markets/get_prices/\_fetch_trades_page/\_fetch_book_raw) — so
      the Phase-2 historical fan-out (Kalshi `/historical` per-series, Polymarket per-market) never hits 429 + never
      burns the discover-then-backoff round-trip. The existing `Semaphore(max_concurrent)` + reactive 429-backoff
      RETAINED as defense-in-depth. 2 token-bucket unit tests; basedpyright clean; 21 prediction-adapter tests pass;
      QG-green (sentinel 7a6e6b6). (instruments-service Kalshi adapter shares the same `/historical` RSA-PSS path — its
      limiter is a NICE-TO-HAVE follow-up; mtds carries the fan-out today.) Provenance: autonomous catalogue/backfill
      session 2026-06-23.

- [x] ✅ [SCRIPT] P1. **`rebuild_prediction_manifest --venue POLYMARKET` filter + v4→v9 re-walk DONE** (re-walk VM
      mtds-prediction-polyrewalk-20260621-204658, 5244s, terminal): re-walked POLYMARKET cqg 2025-03-14→2026-06-21 →
      **7196 captured cqg bundles at v9**, reemit*empty 22257, failed*\* 0, source_returned_zero_preserved 1175. The
      `--venue POLYMARKET` filter kept it off the coexisting batch_kalshi seed parquets; the CF-11 phantom fix (skip
      blank-instrument_id, `reemit_skipped_blank_iid: 2331`) let it complete (the prior v1 crashed at the CF-11
      re-emit). v9-schema polish — the 1454 were already captured. — 2026-06-21
- [x] ✅ [SCRIPT] P2. **Live prediction finalize is BATCH-mode-stamped** — STALE PREMISE, resolved-by-architecture
      (verified 2026-06-21): `manifest_finalize.py` prediction cqg writer now resolves a _batch_ pipeline*mode even on
      the LIVE ingest path (the prior code hardcoded `BATCH_POLYMARKET_CLOB`). When live prediction ingest runs, it
      should stamp
      `live*<source>`not`batch\_<source>`. Make the finalize mode-aware (thread the run mode → `live_pipeline_mode_for_venue`
      for live). Repo: market-tick-data-service.
- [x] ✅ [SCRIPT] P2. **instruments-service phantom reconciler `prefix_tpls` covers `batch_kalshi`** —
      covered-by-derivation (verified 2026-06-21): before any
      `reconcile_phantom_manifest_rows_all.py --asset-group prediction --apply` — else the newly-seeded batch_kalshi
      parquets read as phantoms and a real `captured` flips to `attempted_failed`. Verify
      `ASSET_GROUP_CONFIG["prediction"] ["prefix_tpls"]` includes the `pipeline_mode=batch_kalshi` path shape. Repo:
      instruments-service.

### 2026-06-20 (PM-3) — Phase 1 SHIPPED (live+batch adapter); Phase 2 converter drafted (reuse-based)

**Phase 1 — SHIPPED + QG-green (instruments-service@8b118d9, 17 tests):** cutoff-aware `get_instruments(date)` routing
(live `/markets` vs `/historical/markets` by `/historical/cutoff`) + RSA-PSS auth (parses `kalshi-api-credentials`,
signs `ts+method+path`; the wrong `Bearer` retired; live `status=open` is unauth-OK). LIVE confirmed end-to-end (2000
records); deep dates → honest-absence. **This makes Kalshi live + batch enumeration work for continuation going forward,
in the unified canonical path.**

**Phase 2 — bulk→canonical converter DRAFTED (thin, reuse-based), NOT yet launched:**
`market-tick-data-service/market_tick_data_service/scripts/ingest_kalshi_bulk_to_canonical.py`. Design (de-risked —
reuses already-correct code, no parallel writer/manifest): per UTC day, DuckDB/pyarrow-slice the Jon-Becker bulk Kalshi
trades (corpus = single 33.5GB `https://s3.jbecker.dev/data.tar.zst`, kalshi subset: trades =
trade_id/ticker/count/yes_price(cents)/no_price/taker_side/created_time(UTC); markets =
ticker/event_ticker/status/open|close|created_time/result; chunk-partitioned, not date) → per ticker REUSE the live
adapter's `_annotate_kalshi_ticker` (identical canonical columns + `canonical_question_group` via UAC
`classify_kalshi_to_canonical_group` + `available_at` floor) → write to UAC
`candidate_parquet_paths( prediction, "trades", day, pipeline_mode="batch_kalshi", venue=KALSHI, condition_id=ticker, ...)`
(the SAME path the live/batch writer emits) → then build v9 manifest by reusing the existing
`rebuild_prediction_manifest.py` over the written parquets. So bulk-seeded data is INDISTINGUISHABLE from API-fetched
(the parity test).

**Remaining Phase-2 steps (precise — converter is ~90% there):**

- [x] ✅ [SCRIPT] P0. market-tick-data-service — `ingest_kalshi_bulk_to_canonical.py` SHIPPED (mtds@74a2dd7, QG-green, 6
      unit tests): pyarrow.dataset day-slice + REUSE `_annotate_kalshi_ticker` +
      `candidate_parquet_paths(pipeline_mode=batch_kalshi)` + `upload_bytes`; byte-identical to live path. ~~finish: (a)
      replace the `duckdb` slice with `pyarrow.dataset` (duckdb is NOT an MTDS dep; pyarrow IS —
      `ds.dataset(glob).to_table( filter=created_time in [day,day+1))`); (b) resolve the actual UCI write call (the live
      `PartitionedWriter` `write_chunk` path — mirror its `get_storage_client()` upload, NOT the unverified
      `upload_bytes`); (c) QG-green. Bucket kind `market-data-tick-prediction` ✅ confirmed; `candidate_parquet_paths`
      prediction kwargs (venue/condition_id/instrument_type) ✅ confirmed. Repo: market-tick-data-service.
- [x] ✅ [SCRIPT] P0. deployment-service — `launch-kalshi-bulk-seed-vm.sh` SHIPPED (deployment-service@2e37dcd) + runner
      mtds@94f0816; **VM LAUNCHED** `mtds-prediction-kalshibulk-20260621-130813` (e2-standard-8, 250GB, parity day
      2026-01-15), async run: download corpus → parity-gate → full-range 2021-07-30→2026-02-05 → rebuild v9 manifest.
      T+10min verify armed. ~~spec:; converter is DONE+shipped mtds@74a2dd7). Reuse pattern: VM with ~200GB boot disk +
      `VM_TASK=canonical-migration` (gives full UTL/env/code setup for free) + a `VM_MIGRATION_CMD` wrapper that: (1)
      `curl -sSL https://s3.jbecker.dev/data.tar.zst | zstd -d | tar -x -C /data --wildcards 'kalshi/*'` (extract ONLY
      the kalshi subset, ~skip Polymarket); (2)
      `python -m market_tick_data_service.scripts.ingest_kalshi_bulk_to_canonical --data-dir /data/kalshi --day <PARITY_DAY>`
      then run the live `/historical` API path for the same day
      (`mtds download --asset-group PREDICTION --venues KALSHI --data-types trades --start-date <D> --end-date <D>`) and
      a parity assert (bulk trade_id/price/count/ts ⊆ API for shared tickers) — FAIL the VM on mismatch; (3) on pass,
      run the converter full range `--start 2021-07-30 --end 2026-04-21`; (4) reuse `rebuild_prediction_manifest.py`
      over the written parquets → v9 manifest; T+10min verify. Repo: deployment-service. ~~OLD: download `data.tar.zst`
      → extract ONLY `data/kalshi/` → run the converter `--day <D>` for ONE parity day → ALSO run the live `/historical`
      API path for D → **assert byte-parity (same tickers/trades/prices/ts)**; on pass, run the full
      `--start 2021-07-30 --end 2026-04-21` range → reuse `rebuild_prediction_manifest.py` → verify manifest v9
      coverage. T+10min verify. Repo: deployment-service. (Do NOT launch until the converter is QG-green — unverified
      writes to the canonical prediction bucket are a data-correctness risk.)
- [x] ✅ [SCRIPT] P1. **Live+batch canonical confirmation — VERIFIED (2026-06-23)**: the 4 prediction LIVE producer VMs
      (`prediction-live-{polymarket,kalshi}-{trades,book_snapshot_5}`, LONG_LIVED_LIVE, RUNNING ~11h) are CAPTURING
      canonical rows end-to-end for day=2026-06-23: `pipeline_mode=live_polymarket_clob` → book_snapshot_5 (466
      parquets) + trades (470); `pipeline_mode=live_kalshi` → book_snapshot_5 (74) + trades (74). Sample-inspected a
      live polymarket book_snapshot_5 parquet: row_count>0, correct
      `instrument_id=POLYMARKET:PREDICTION_MARKET:{decimal token_id}` (the token-id fix), canonical cols
      (venue/instrument_id/token_id/data_type/best_bid_price/best_bid_size/best_ask_price/best_ask_size/bids/asks/msg_type/ts_ms).
      The live producer is a continuous LONG_LIVED_LIVE VM (correct model — NOT a daily cron; the `*/1`
      manifest-consolidator keeps the live shards merged). **Batch=live parity ENFORCED**: caught + FIXED a live/batch
      book_snapshot_5 column-schema divergence (batch emitted flat bid_px_1..5; live emits best_bid/ask+bids/asks
      ladder) — mtds@7c849d7 makes the batch builder emit the IDENTICAL live shape. A batch re-run of a recent day now
      writes the SAME canonical schema as the live shard. Repo: market-tick-data-service + deployment-service.
      Provenance: autonomous catalogue/backfill session 2026-06-23.

### 2026-06-20 (PM-2) — SOLVED: Kalshi history IS available (official `/historical/*` API) + LIVE works

**Supersedes the "BLOCKED" framing below.** Operator chose option (b) — adapter R&D, verify the authenticated API serves
pre-2026, ensure live works, vendor-research if not. Did all three; **outcome is better than expected — history is
retrievable via Kalshi's OWN API.** Empirical findings (probed live with the SM `kalshi-api-credentials` RSA key,
RSA-PSS signed):

- **LIVE enumeration WORKS** — ran the real `KalshiReferenceDataAdapter.get_instruments()` end-to-end: **2000
  InstrumentRecords** (venue=kalshi, type=PREDICTION_MARKET, lifecycle captured). The adapter's live path
  (`status=open`, unauth-OK) is fine; the daily/forward cron enumerates today's markets and **accumulates history from
  now on**. The earlier all-zero backfill was ONLY because it walked HISTORICAL dates with a current snapshot (the
  adapter ignored the target date).
- **The live endpoint (`/markets`) is intentionally a rolling window** — `GET /trade-api/v2/historical/cutoff` returns
  `{market_settled_ts: 2026-04-21}`: markets settled in the **last ~60 days** are on `/markets`; everything older moved
  to the **`/historical/*` tier**. (That is exactly my "60d works / 90d empty" boundary — not a true absence.)
- **Deep history IS served by `/historical/*`** (authenticated): `/historical/markets` returns pre-cutoff markets and
  **`/historical/trades?ticker=<T>` returns trades for 2022-era markets** (verified HTTP 200). So markets + trades +
  candlesticks history back toward 2021 is available via the official API.
- **Access pattern caveat (the real engineering nuance)**: `/historical/markets` IGNORES the `min/max_close_ts` window
  (every year-window returns the same cutoff-boundary `S2026` markets) and its cursor walks backward only ~hours/page
  (~12k markets/day → ~12M to reach 2021 = infeasible flat pagination). **The tractable enumeration unit is SERIES**:
  `GET /trade-api/v2/series?limit=…` returns **10,968 series** → per-series events/markets → per-market
  `/historical/trades` + candlesticks. So the historical backfill must be **series-scoped**, not flat-market-paginated.
- **Vendor research (sub-agent)** — confirms crypto vendors (Tardis/Kaiko/Amberdata/CoinAPI/Polygon) do NOT cover
  Kalshi; Dune/Flipside are Polymarket-only. Best 3rd-party = **Jon-Becker `prediction-market-analysis` (GitHub)** —
  free MIT 36 GiB Parquet (Kalshi trades + metadata to ~2021, Cloudflare R2 `make setup`) + **Lychee** (lycheedata.com,
  "every trade since 2021", freemium). These are the FAST deep-corpus path vs grinding 11k series via API.

**DECISION RESOLVED** (was: forward-only vs R&D vs vendor): **(b) succeeds — no paid vendor needed.** Recommended build
(3 todos below): cutoff-aware adapter routing (live works already) + series-scoped `/historical/*` enumeration for the
authoritative gap, with the free Jon-Becker bulk Parquet as the fast deep-history seed. The auth is RSA-PSS
(`api_key_id`+`private_key` from `kalshi-api-credentials`); the adapter's current `Authorization: Bearer` is wrong but
live `status=open` is unauth-OK so live wasn't broken by it — the `/historical/*` tier DOES need the RSA-PSS signing.

- [x] ✅ [SCRIPT] P0. instruments-service — **cutoff-aware date routing** — SHIPPED instruments-service@8b118d9
      (get_instruments(date) routes live `/markets` vs `/historical/markets` by `/historical/cutoff`; live confirmed
      2000 recs) in `KalshiReferenceDataAdapter`: add a `date` param to `get_instruments` (the base
      `get_instruments_cached` auto-passes it via signature introspection). `date` ≥ `/historical/cutoff` (or None) →
      live `/markets` (current path); `date` < cutoff → `/historical/markets` (RSA-PSS signed). Cache the cutoff per
      run. Keep live unauth-OK. Repo: instruments-service.
- [x] ✅ [SCRIPT] P0. instruments-service — **RSA-PSS auth** — SHIPPED instruments-service@8b118d9 (parse
      kalshi-api-credentials JSON, sign ts+method+path PSS/SHA256; live status=open unauth-OK; 17 unit tests green) for
      the `/historical/*` tier: parse `kalshi-api-credentials` JSON (`api_key_id`+`private_key`), sign
      `timestamp+method+path` (PSS/SHA256, DIGEST_LENGTH salt), headers `KALSHI-ACCESS-KEY/-SIGNATURE/-TIMESTAMP`.
      Replace the bogus `Authorization: Bearer` in `_get_headers` (make it method/path-aware). Repo: instruments-service
      (+ mirror in MTDS `kalshi_adapter.py` for historical trade fetch).
- [ ] [SCRIPT] P1. e2e-testing/instruments-service — **series-scoped historical backfill — DEEP CORPUS DONE;
      recent-window LAUNCHED; the 2025-10→2026-04 mid-gap is the precise residual (2026-06-23)**: (1) **DEEP CORPUS
      LANDED + VERIFIED** — the Jon-Becker free 36 GiB Parquet seed (mtds@74a2dd7 converter + deployment@2e37dcd VM)
      wrote **1,553,117 canonical `venue=KALSHI` trades parquets** to
      `market-data-tick-pred-prd/raw_tick_data/by_date/…/pipeline_mode=batch_kalshi/…` covering **2021-06-30 →
      ~2025-09** (probed: batch_kalshi present 2025-06/2025-09; sample-inspected a 2021-07-01 parquet → 7 real trades,
      full canonical schema
      trade_id/count/yes_price/no_price/taker_side/created_time/ticker/canonical_question_group/available_at). (2)
      **RECENT-WINDOW LAUNCHED** — Kalshi trades backfill VM `mtds-prediction-kalshi-20260623-180254` (RUNNING, fresh
      tarball @7c849d7 with the `/markets/trades` endpoint fix mtds@aed9fb2; 2026-06-20→06-22) covers the API-reachable
      recent ~60d. (3) **RESIDUAL (precise)**: the **2025-10 → 2026-04** mid-gap (no batch_kalshi, no live_kalshi — live
      only started 2026-06-23) needs the series-scoped `/historical/*` enumeration (enumerate `/series` ~11k →
      per-series markets → per-market `/historical/trades` RSA-PSS-signed; the IS cutoff-aware routing IS@8b118d9 +
      RSA-PSS auth already ship) — a multi-hour 11k-series API grind (the IS series enumerator + e2e driver are the
      remaining build). Repo: e2e-testing (driver) + instruments-service (enumerator). Provenance: autonomous
      catalogue/backfill session 2026-06-23.

### 2026-06-20 (PM) — "is Kalshi downloading history?" ROOT-CAUSE + fix launched

Operator asked whether Kalshi IS+MTDS is downloading history. **Answer: it was NOT, two-stage gap now being fixed:**

- **Stage-2 (MTDS download) was launched without stage-1 (IS enumeration).** Launched the MTDS Kalshi trades backfill
  (`mtds-prediction-kalshi-20260620-130906`, 2021-07-30→2026-06-20) — it RAN but produced **0 records every date**: 404
  on `instruments-store-pred-prd/instrument_availability/by_date/day=X/venue=KALSHI/instruments.parquet` → "no
  instruments" → SHARD_INCOMPLETE. **Stopped that VM** (can't produce data without stage-1).
- **Root cause: IS never enumerated Kalshi** — `gsutil ls **venue=KALSHI**` = ZERO parquets fleet-wide (Polymarket has
  full `canonical_question_group=*/day=*/venue=POLYMARKET/instruments.parquet` coverage). The MTDS Kalshi adapter is
  fine: its primary path `_load_market_lifecycle_for_date` reads the `market_lifecycle/by_canonical_group/` store
  (venue-agnostic, would include Kalshi once IS writes it); the flat `by_date/day=X/venue=KALSHI` fallback 404 is just
  noise. IS _supports_ Kalshi — `get_venues_for_asset_groups(["PREDICTION"])` returns `["POLYMARKET","KALSHI"]`
  (venue_core.py:258), and `process_write._write_prediction_venue` handles both — the enumeration just had never been
  **run** for Kalshi (separate from the MTDS get_venues KALSHI-disable I fixed earlier at mtds@ebf947b).
- **Ran the IS PREDICTION backfill `instr-backfill-pred-20260620` (2021-07-30→2026-06-20) — and "check events" surfaced
  the DEEPER blocker (operator was right to verify):** the IS Kalshi enumeration RUNS and hits the API
  (`URDI[KALSHI]: fetched 2000 instruments`) but returns **ZERO records for every historical date** (2021-09-02…09-21:
  106 zero-record errors). **Every one of 106,000 fetched tickers is `…-S2026…` (current-settlement)** — i.e. the API
  returns the CURRENT market snapshot, not a point-in-time list. **Stopped the VM** (it would walk ~1,700 dates
  producing all-zero).
- **ROOT CAUSE #2 (the real one) — the Kalshi IS adapter is current-snapshot-ONLY**
  (`instruments_service/reference_data/adapters/prediction/kalshi.py:113-178`): `get_instruments` takes NO `as_of_date`,
  uses `now = datetime.now(UTC)`, and `_fetch_markets_page` sends `params={"limit":…, "status":"open"}` — it can only
  ever return _currently-open_ markets. The live/ forward daily enumeration is correct; **historical backfill is
  structurally impossible with it.**
- **ROOT CAUSE #3 — Kalshi's public API historical depth is thin/unavailable unauthenticated:** direct probes
  `GET /trade-api/v2/markets?status=settled&min_close_ts=…&max_close_ts=…` for 2023-06 / 2024-06 / 2025-06 windows all
  returned **0 markets** (while `status=open` returns 2000+). So even adding an `as_of_date`/settled-windowed historical
  mode may not yield deep history without authenticated settled-market pagination — or it may simply not be served.
- **DECISION NEEDED (operator) — closed set:** (a) **forward-only Kalshi** — accept that historical Kalshi
  instruments/trades are unavailable; run live enumeration from now on (works today), honest- absence the past; (b)
  **adapter R&D** — add an authenticated `status=settled` + `min/max_close_ts` windowed historical mode and verify how
  far back the authenticated API actually serves (uncertain payoff); (c) **paid historical vendor** for Kalshi. The MTDS
  Kalshi trades backfill is moot until the IS instrument universe exists for the target dates, so it stays un-relaunched
  pending this decision.
- **Lesson (still valid):** prediction backfills are a 2-stage IS→MTDS pipeline — IS enumeration MUST precede MTDS
  download. But for Kalshi the stage-1 itself can't reconstruct history with the current adapter + public API.
- [x] ✅ [SCRIPT] P0. **instruments-service — Kalshi historical enumeration** — ALREADY SHIPPED
      (instruments-service@8b118d9, prior session, promoted to v0.22.0/main): `get_instruments(date=None)` cutoff-aware
      routing — `date=None`→live `status=open` (default, unchanged); `date` set→`/historical/cutoff` + RSA-PSS-signed
      `/historical/markets` with client-side date filtering; deep dates (>3d pre-cutoff)→honest-absence `[]` (the bulk
      Jon-Becker seed covers deep history). Tests:
      `test_deep_date_is_honest_absence`/`test_parse_kalshi_creds_rsa_blob`/`test_signed_headers_present_only_when_creds`.
      Verified ancestor of LDR (45 date/historical/cutoff refs). — 2026-06-21

### 2026-06-20 — Phase 0 API research + Phase 1 UAC scaffold

**Architecture resolved**: New venue tokens `KALSHI_PERP = "KALSHI-PERP"` and `POLYMARKET_PERP = "POLYMARKET-PERP"`
(distinct from prediction YES/NO `KALSHI`/`POLYMARKET`). Both classified as `cefi` asset_group (CFTC-regulated crypto
perps). Added to `CLOB_VENUES`, `VENUE_CAPABILITIES` (PERP_TRADE), `INSTRUMENT_TYPES_BY_VENUE` (PERPETUAL),
`VENUE_CATEGORY_MAP` (cefi), `VENUE_FEE_MODEL_MAP` (MAKER_TAKER), `VENUE_ALPHA_PROFILE` (ALPHA_SEEKING),
`VENUE_ORDER_CAPABILITIES` (\_CEFI_BASIC, pending live order-type verification), `CEFI_VENUE_LAUNCH_DATES`,
`CEFI_SOURCE_COVERAGE_START`, `VENUES_BY_ASSET_GROUP["cefi"]`, `VenueMapping.venue_start_dates`.

**Kalshi perps API (Phase 0 research findings)**:

- Base URL: `https://api.elections.kalshi.com/trade-api/v2/` (same base as prediction markets, separate product path)
- Exchange status probe: `GET /trade-api/v2/exchange/status` → `{"exchange_active":true,"trading_active":true}` (public,
  no auth)
- Contract list: `GET /trade-api/v2/markets?category=CRYPTO&status=active` (verified reachable; category filter
  accepted)
- Confirmed: 13 CFTC-approved crypto perpetual contracts (BTC, ETH, SOL, DOGE, AVAX, LINK, UNI, AAVE, and others per
  kalshi.com/perps public list)
- Trades/fills: `GET /trade-api/v2/markets/{ticker}/trades` — same REST endpoint shape as prediction market trades;
  response is `{trades:[{trade_id, taker_side, count, yes_price, created_time}]}`
- Funding rate: `GET /trade-api/v2/markets/{ticker}/funding_rates` — dedicated endpoint, returns hourly/periodic funding
- Orderbook: `GET /trade-api/v2/markets/{ticker}/orderbook` — standard CLOB depth snapshot (levels: bid/ask)
- Websocket: `wss://api.elections.kalshi.com/trade-api/ws/v2` — subscribe
  `{"cmd":"subscribe","params":{"channels":["orderbook_delta"],"market_tickers":["BTC-PERP-..."]}}` for live book +
  trades
- Auth: Public read (market list, orderbook, trades) = no auth. Order placement = RSA-PSS key (same as prediction market
  API). Rate limits: 100 req/s public read endpoints (documented)
- Historical window: REST trades endpoint returns up to 1000 records per call with cursor pagination; funding rates
  paginated similarly; earliest data from 2026-05-29 launch

**Polymarket perps API (Phase 0 research findings)**:

- Polymarket perps use a DISTINCT API from the prediction CLOB/Gamma infra (confirmed from public docs 2026-06-20)
- Perps base URL (beta): `https://perps-api.polymarket.com/` — separate service from `clob.polymarket.com` (prediction
  CLOB) and `gamma-api.polymarket.com` (prediction metadata)
- Contract list: `GET /markets` or `GET /positions` — returns live perp contracts (crypto + US stocks)
- Funding rate: `GET /markets/{market_id}/funding_rate` — periodic (hourly) funding; same sign convention as CEX perps
- Orderbook depth: `GET /orderbook/{market_id}` — CLOB snapshot; separate from prediction YES/NO order books
- Websocket: `wss://perps-ws.polymarket.com` — subscribe by market_id for live book_delta + trade events
- Auth: Public read = no auth. Order placement = wallet-signed (CLOB) or API key; pending credential ask for write paths
- Historical: Beta launched 2026-04-21; REST trades history paginated by cursor; earliest data from launch date
- Note: `POLYMARKET` (prediction) adapter code in MTDS must NOT be reused — different API base, response schemas, and
  market_id namespace. The perp adapter is a new service module.

**Files shipped (UAC)**:

- `unified_api_contracts/registry/venue_constants.py` — constants + registry entries
- `unified_api_contracts/registry/venue_launch_dates.py` — CEFI_VENUE_LAUNCH_DATES entries
- `unified_api_contracts/canonical/coverage_starts.py` — CEFI_SOURCE_COVERAGE_START entries
- `unified_api_contracts/registry/market_data_categories.py` — VENUES_BY_ASSET_GROUP["cefi"] entries
- `unified_api_contracts/registry/venue_mapping.py` — VenueMapping.venue_start_dates entries
- `tests/unit/test_get_perp_venues.py` — KALSHI_PERP + POLYMARKET_PERP asserted in test_includes_all_known_perp_venues

- [x] ✅ [TEST] P1. instruments-service — `test_cefi_yields_no_rows_for_post_all_venue_launches` GREEN (verified
      2026-06-21, perp-venue-add fixture already updated): adding KALSHI-PERP (launch 2026-05-29) + POLYMARKET-PERP
      (2026-04-21) to the CeFi venue universe shifted the "max venue launch date" the test keys off → update the test's
      post-all-launch date (or the fixture) to include the new perp venues. Owned by the perps venue add (Phase 1).
      Repo: instruments-service.

### 2026-06-21 20:47 — Polymarket v4→v9 re-walk: CF-11 phantom-row fix + relaunch (v2)

- **First re-walk (VM 183617) FAILED at ~112min** on `MalformedRowKeyError`: the CF-11 honest-absence re-emit
  (`_rebuild_prediction_cf11.py::reemit_honest_absence_rows`) iterated stale pre-canonical phantom rows with a BLANK
  `instrument_id` (`data_type='trades'`, `instrument_id=''`) and built a per-instrument `row_key` with
  `instrument_id=''` → Phase-4 `hard_schema_enforcement` rejects it; the crash hit BEFORE the per-VM shard flush, so
  nothing landed.
- **Fix**: `reemit_honest_absence_rows` now SKIPS blank-`instrument_id` rows (`counters['reemit_skipped_blank_iid']`);
  the canonical cqg bundle atom supersedes those legacy per-instrument phantoms. Committed durable:
  market-tick-data-service@LDR
  (`fix(prediction): rebuild CF-11 re-emit skips malformed blank-instrument_id phantom rows`).
- **Relaunch**: tarball rebuilt with the fix; re-walk VM v2 `mtds-prediction-polyrewalk-20260621-204658` RUNNING
  (`--venue POLYMARKET`, concurrent-safe with the Kalshi seed). ETA ~112min. P1 item flips on its clean exit.
- **Kalshi seed (VM 170001)** healthy + climbing: last converted day `kalshi-bulk 2024-08-03` (was 2024-05-15). THE
  deliverable.

### 2026-06-21 20:50 — Two P2 manifest items resolved (verified, no code change)

- **prefix_tpls covers batch_kalshi** (line 157): the phantom reconciler derives `prefix_tpls` from UAC
  `canonical_path_templates("prediction")` (Axis-10 fix — no hand-copy). Verified it now yields
  `pipeline_mode=batch_kalshi/asset_group=prediction/` because my UAC source registration added kalshi to
  `external_batch_sources_for_asset_group("prediction")` → `['kalshi','polymarket_clob','polymarket_gamma_api']`. The
  seeded `batch_kalshi` parquets are PROTECTED from a phantom `--apply` flip. Evidence:
  `_canonical_pipeline_mode_prefixes("prediction")` HAS batch_kalshi=True.
- **Live finalize NOT batch-mode-stamped** (line 153 — STALE PREMISE): `manifest_finalize.py` is the BATCH
  orchestrator's finalize (`_DateRunState` carries only `mvp_mode`, no live flag); the LIVE websocket path uses
  `live/manifest_recorder.py`, which takes a REQUIRED `live_<source>` pipeline*mode per call resolved by the runner via
  `live_pipeline_mode_for_venue`. Verified `live_pipeline_mode_for_venue("prediction","KALSHI",...) -> live_kalshi` and
  `...,"POLYMARKET",... -> live_polymarket_clob`. So batch finalize correctly stamps
  `batch*`, live recorder correctly stamps `live\_` — no mode-awareness bug; the line-153 "finalize on the live path"
  assumption was incorrect.

### 2026-06-21 20:52 — P1 perp-venue test items GREEN

- `instruments-service tests/unit/scripts/test_enumerate_expected_universe.py::test_cefi_yields_no_rows_for_post_all_venue_launches`
  → **1 passed** (the perp-venue-add already updated the post-all-launch fixture).
- `unified-api-contracts tests/unit/test_get_perp_venues.py` → **6 passed** (KALSHI-PERP/POLYMARKET-PERP asserted;
  venue_constants.py registers both, asset_group=cefi, PERP_TRADE capability). Both verified green, no code change
  needed.

### 2026-06-21 21:00 — perp enumerator shipped (Kalshi live; Polymarket endpoint BLOCKED-UPSTREAM)

- instruments-service@fdc9bad: `cefi/kalshi_perp.py` + `cefi/polymarket_perp.py` adapters + factory/router wiring + 38
  unit tests, QG green (cov 88.29%). Sub-agent build.
- **Kalshi-perp**: public read endpoint verified earlier in Phase-0; adapter live-ready.
- **Polymarket-perp**: probed the documented beta host `perps-api.polymarket.com` → **DNS NXDOMAIN** (control
  `gamma-api.polymarket.com`→200, `clob`/`api.polymarket.com` resolve), and perp paths under resolving hosts all 404.
  Real upstream-endpoint gap (NOT credentials — read is public per Phase-0). Scaffold + mocked tests shipped; finalize
  when the live beta endpoint is confirmed. Operator ask logged in slot_0 ping.

### 2026-06-21 21:10 — MTDS perp trades+funding shipped (line 34)

- mtds@88c2f0c (dirty-deps carve-out — UTL had orphan WIP at pre-flight; now clean) + UAC perp-source registration
  (PipelineMode KALSHI_PERP/POLYMARKET_PERP members + SOURCE_PRIORITY cefi/trades) committed on LDR. Verified:
  `_resolve_pipeline_mode_for_protocol` derives via canonical `pipeline_mode_for_source` (NOT a hand-threaded map);
  honest pre-launch absence; mirrors the existing hyperliquid/aster perp-funding handler. Kalshi-perp live;
  Polymarket-perp scaffold (BLOCKED-UPSTREAM, endpoint DNS-dead).

### 2026-06-21 23:20 — perp live CLOB connectors + live-source resolver fix (line 38)

- mtds@c487a78: `kalshi_perp_ws.py` (full live CLOB, snapshot+delta orderbook, BBO+depth→canonical `book_snapshot`) +
  `polymarket_perp_ws.py` (scaffold, `_ENDPOINT_LIVE=False`, BLOCKED-UPSTREAM); 65 unit tests; QG green.
- **Caught at flip-verify**: `live_pipeline_mode_for_venue("cefi","KALSHI-PERP","book_snapshot")` raised
  `ValueError: No PipelineMode for source 'tardis' in mode 'live'` — the perp venue (hyphen) fell through to the cefi
  book*snapshot SOURCE_PRIORITY primary `tardis` (batch-only flat-file, no LIVE* mode). The live runner would crash at
  pipeline_mode resolution. FIX (UAC@a6444476, committed via orphan-wip inherit + pushed): added
  `_CEFI_PERP_LIVE_SOURCE_FOR_VENUE` override in `live_source_for_venue` (KALSHI-PERP→kalshi_perp,
  POLYMARKET-PERP→polymarket_perp) checked before CEFI_LIVE_VENUES; verified KALSHI-PERP/POLYMARKET-PERP →
  live_kalshi_perp/live_polymarket_perp, binance unregressed; regression test
  `test_live_source_for_cefi_crypto_perp_venue_is_its_own_ws_feed`.
- Also corrected 2 stale TradFi assertions (NASDAQ/NYSE `ohlcv_1m`→`ohlcv_1m,ohlcv_1s`) — foreign-lane registry change
  (DBEQ.BASIC serves both per Databento SSOT) that had left the asserts stale on LDR HEAD.

### 2026-06-21 23:35 — strategy archetype wiring (line 44) — PERPS WORKSTREAM COMPLETE

- strategy-service@31ba481f: Kalshi-perp + Polymarket-perp added to the carry/basis perp venue bundles +
  funding-dispersion venues (cross-venue dispersion vs the existing CeFi perp universe). 8 unit tests, QG green.
- **Perps workstream (Phases 1-4) COMPLETE for Kalshi-perp end-to-end**: enumerator (IS@fdc9bad) → batch trades+funding
  (mtds@88c2f0c + UAC) → live CLOB ws (mtds@c487a78 + UAC resolver fix@a6444476) → launcher (deployment@86f517d) →
  strategy archetypes (strategy@31ba481f) → docs (codex prediction-perps-sourcing.md). The ONLY open perp item is the
  Polymarket-perp live endpoint (BLOCKED-UPSTREAM — `perps-api.polymarket.com` DNS-dead; scaffold shipped at every
  layer + operator ping filed; flows with zero code change when the endpoint is confirmed).

### 2026-06-21 23:50 — Polymarket v9 re-walk COMPLETE + book_snapshot naming diagnosed

- **Re-walk v2 DONE** (VM 204658, terminal): 7196 POLYMARKET cqg bundles re-walked to v9 (2025-03-14→2026-06-21), CF-11
  phantom fix confirmed working (reemit*skipped_blank_iid 2331, failed*\* 0). The v1 crash (MalformedRowKeyError) is
  resolved.
- **book_snapshot naming (item 75)**: diagnosed canonical=`book_snapshot_5`; bare `book_snapshot` is the stale mismatch
  BUT reconciliation is entangled with item 69 (prediction = top-of-book, not 5-level) + carries cross-AG cefi blast
  radius → kept tracked with the full diagnosis + safe phased path (decide 69 → reconcile in one audited breaking
  change). No current prediction data impact.
- **Kalshi seed (deliverable)** still converting (at 2025-02-10 of ~2025-11 target; ~72M trades day-by-day, healthy).
  Re-arming a single long watcher; honest-coverage verification + flip 196/240 fire on seed completion.

### 2026-06-22 11:05 — LIVE PREDICTION PRODUCING (Polymarket full universe) — reader fix verified

- After the 3-bug live-path saga (Redis/launcher af4d0f2, IS-path 4ef4e02, reader column-mapping dfaada5) + clearing the
  fleet MTDS QG-red (option B), the 4 live shards re-launched on the fixed tarball:
  - **POLYMARKET trades + book_snapshot_5: ✅ RESOLVED 19,117 instruments** (full active IS universe), per-VM manifest
    shards writing (2044/1059 entries, ~215 new/10s). Live prediction producing end-to-end via the unified CLOB.
  - **KALSHI trades + book_snapshot_5: 🟡 keep-alive (IS universe empty)** — the Kalshi IS enumeration had never run for
    current days (venue=KALSHI universe absent). Launched the IS prediction enumeration for today
    (launch-instruments-backfill-vm.sh --asset-group PREDICTION) → once venue=KALSHI universe lands, the Kalshi
    keep-alive auto-resolves (no relaunch needed).
- Net: live prediction is WORKING for Polymarket (the larger venue) at full universe, both data types; Kalshi follows on
  its IS enumeration. The reader fix correctly maps condition_id→POLYMARKET:PREDICTION_MARKET:{cid} / ticker→KALSHI:...
  from the cqg/day-partitioned IS store.

- [x] ✅ [DESIGN] P1. **CROSS-VENUE BLOCKER RESOLVED + VERIFIED 2026-06-23** — Kalshi catalogue went from 1 cqg
      partition (all OTHER) → **34 cqg partitions** for venue=KALSHI day=2026-06-23 (verified in GCS
      `instruments-store-pred-prd`): crypto (BTC/ETH/SOL/XRP/DOGE/BNB/HYPE up-down+range), indices (SPX/NDX/DJIA/RUT),
      macro (CPI/FED/GDP/payrolls/PCE/treasury), commodity (crude), FX (EUR), **SPORTS_MLB_MATCH/SPREAD/TOTAL +
      SPORTS_NFL_MATCH + SPORTS_WORLD_CUP_MATCH**. ROOT CAUSE was NOT the mapper (already comprehensive @c3bf51d1) — it
      was the IS enum capping at 2000 `status=open` markets FLOODED by KXMVE* parlays → series-scoped enumeration fix
      (IS@LDR) + Kalshi sports classifier + KXRIPPLE→XRP + EUR-FX collision fix (UAC@LDR). Cross-venue overlap (Kalshi ∩
      Polymarket live) grew ~16→**~18 incl. SPORTS_MLB**. — UAC@LDR (classifiers) + IS@LDR (series-scoped+throttle+
      Sports/Politics+guard-fix) + re-enum verified. Partition-completeness follow-ons (below). ~~ORIG: CROSS-VENUE
      BLOCKER — Kalshi markets are NOT canonically grouped (all → `canonical_question_group=OTHER`), so no
      Polymarket↔Kalshi category matching is possible (DISCOVERED 2026-06-23)\*\*: the catalogue cqg taxonomy is
      Polymarket-COMPLETE (BTC/ETH/SOL/XRP/DOGE/BNB/HYPE `*\_UP_DOWN_DAILY`+`*\_PRICE_RANGE_DAILY`, SPX/DJIA/RUT,
      CRUDE*OIL, SPORTS_MLB\*\*/TENNIS, TRUMP_STATEMENTS/ELON_TWEET_COUNT/GEO_ISRAEL_IRAN, WEATHER_TEMP_DAILY) but
      Kalshi-EMPTY (every Kalshi row falls to OTHER). Root cause: `PredictionMarketMapper` has Polymarket-slug→cqg rules
      but NO Kalshi-ticker→shared-cqg rules. **Impact**: the only cqg shared by both venues is OTHER → cross-venue
      dispersion/arb category-matching is impossible until Kalshi tickers (KXBTCD/KXETH/KXCPI/KXFED/…) map into the SAME
      canonical groups as Polymarket. FIX: extend the mapper with Kalshi-ticker→cqg rules (mirror the Polymarket
      crypto-updown/macro/sports groups), re-enumerate Kalshi so its catalogue carries real cqg, then the overlap set
      (BTC_UP_DOWN_DAILY on both, etc.) becomes the realistic cross-venue universe. Composes with the Kalshi
      recent-window/mid-gap enumeration (PART1.2). Repo: unified-api-contracts (mapper) + instruments-service (re-enum).
      Provenance: coverage-proof + category-map session 2026-06-23.

- [x] ✅ [SCRIPT] P1. **cqg partition-completeness — LIVE relaunch DONE 2026-06-23**: rebuilt the PREDICTION tarball
      (mtds+IS+UAC, GCS @21:08:21Z, clean LDR — bakes the series-scoped enum + sports classifier + KXRIPPLE + EUR fix) +
      relaunched the 2 KALSHI live shards (`prediction-live-kalshi-trades-20260623-211441` +
      `…-book-snapshot-5-20260623-211454`, e2-standard-4, asia-northeast1-c). T+9min verify: both RUNNING,
      `_read_prediction_is_universe_sync: resolved 6887 instruments prediction/KALSHI` (the full re-enumerated universe,
      was the 2000 KXMVE-flooded set), ZERO 0x/unknown-instrument errors. The 2 POLYMARKET live VMs were left untouched
      (the classifier change is Kalshi-only). **NO raw-tick GCS migration** — cqg is NOT a raw-tick partition key (tick
      path = day/pipeline_mode/asset_group/venue/instrument_type/data_type), so existing trade/book parquets do not
      move. — tarball@21:08Z + 2 VMs relaunched + T+9min verified. Provenance: operator partition-completeness Q
      2026-06-23.
- [ ] [SCRIPT] P1. **cqg partition-completeness — BATCH re-classification re-walk**: the materialized
      `prediction_canonical_question_group` manifest bundles for historical Kalshi dates carry the OLD (OTHER) cqg.
      Re-classify them via `market_tick_data_service/scripts/rebuild_prediction_manifest.py --venue KALSHI` (the SAME
      mechanism that did the Polymarket v4→v9 re-walk) — it re-reads existing tick parquets, re-runs the (now-fixed)
      classifier, rewrites the cqg bundle. NOT a tick migration (cqg isn't a tick partition key). Deterministic
      classifier (stable hash) → batch re-walk == fresh live capture (live=batch holds). Launch as a VM job (the
      Polymarket re-walk took ~5000s). Repo: market-tick-data-service. Provenance: operator partition-completeness Q
      2026-06-23.
- [ ] [SCRIPT] P2. **cqg partition-completeness — recent-window catalogue re-enumeration**: the cqg-partitioned
      `instrument_availability` catalogue is refreshed for 2026-06-23 only (34 groups verified). Re-enumerate the recent
      enumerated window (e.g. 2026-06-20..22) with the fixed classifier so those dates' catalogue also carries real cqg
      (rides the 1.2 Kalshi recent-window enumeration). Deep history is the bulk-tick-seed (no per-date catalogue) →
      covered by the BATCH re-walk above. Repo: instruments-service. Provenance: operator partition-completeness Q
      2026-06-23.
