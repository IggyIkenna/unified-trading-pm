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

### 2026-06-24 (autonomous /autonomous) — arb → #paper-trading-alerts Slack pager SHIPPED (operator: "where does the arb alert come in… paper alerts slack is a good candidate")

The detector now PAGES on a real opportunity, not just silent-to-GCS. Shipped **features-service@295b3f83**:

- `app/prediction_arb_slack.py` (NEW) —
  `post_arb_alert(arbs, now, cooldown_state, *, cooldown_seconds=3600, webhook=None)`: pages `#paper-trading-alerts` on
  **freshly-flagged PURE_ARB** rows (a top-of-book crossing = the actionable signal), per-pair **1h cooldown** so a
  persistent arb pages once/hour not every tick; QUOTABLE-only ticks never page (counted in the message body only).
  Webhook resolves from the channel-locked SM secret `agent-orchestrator-paper-trading-slack-webhook` via cloud-agnostic
  `get_secret` (cached, **best-effort** — a Slack/SM failure logs a warning and never disturbs the loop; the GCS arb
  store stays the durable record). Same channel
  - webhook `paper_engine.py` uses, so prediction arbs land in the operator's existing paper-trading alert stream.
- `app/cross_venue_arb_runner.py` — wired `post_arb_alert` into `run_live_loop` (per-pair `alert_cooldown` dict persists
  across ticks; `total_slack_paged` added to cumulative totals).
- `tests/cross_instrument/unit/test_prediction_arb_slack.py` (NEW, 4 tests) — PURE pages once then cooldown; QUOTABLE
  doesn't page; no-webhook best-effort skip; empty no-page. QG-green (296s, sentinel-verified) before quickmerge.

Note: shipping was briefly blocked by a **live peer's** uncommitted UTL `cloud_interface/providers` WIP (the
`get_blob_metadata.last_modified` catalog-false-positive fix, UTL@7906df7a — directly the catalog-staleness root cause
filed below); PROTECTED it (mtime <120s = live editor), waited for the peer to commit, then quickmerged. Next: rebuild
the PREDICTION tarball + relaunch the detector VM so the pager goes live (the running VM 150427 predates this).

### 2026-06-24 (autonomous /autonomous) — FULL ARB-DETECTOR STACK SHIPPED (4 repos) + operational findings

All four code units of the live cross-venue arb detector dispatch are SHIPPED to LDR:

| Unit                                             | Repo@sha                          | What                                                                                               |
| ------------------------------------------------ | --------------------------------- | -------------------------------------------------------------------------------------------------- |
| Detector (kernel+fee-model+runner+CLI)           | features-service@ef7cd58c         | paper-mode loop, PURE/QUOTABLE taxonomy, fee-net, GCS arb-store, 24 tests                          |
| Producer trades-fix                              | market-tick-data-service@ef01a055 | data_type-aware factories + real Kalshi `trade`/Polymarket `last_trade_price` connectors, 25 tests |
| VM launcher + dispatch + watchdog/classification | deployment-service@e9f7092        | `launch-prediction-arb-detector.sh` (LONG_LIVED_LIVE) + `prediction-arb-detect` VM_TASK            |
| Lifecycle-telemetry best-effort                  | unified-trading-library@5011dbc9  | ServiceBootstrap STARTED/STOPPED/FAILED no longer crash a service on an event-sink publish failure |

**Detector VERIFIED end-to-end on live GCS (smoke, batch single-tick):** `run_prediction_cross_venue_dispersion` over
real prod data → the UAC matcher produced **8,932 Kalshi↔Polymarket cross-venue mappings**, then HONESTLY reported **0
two-sided-book overlap** (`two_way_on_both_ticks=0`, `pure_arb=0`, `quotable_arb=0`) — the known thin-Polymarket-crypto
liquidity gate, exactly the design-SSOT's "truthful 0 crossings, N mappings" outcome, NOT a bug. The detector is the
canonical home + reuses the shipped matcher→feature chain unchanged.

**Operational arc (no-fire-and-forget T+10 caught 3 real infra gaps across relaunches — each fixed):**

1. VM ran the wrong module (`features_service` not `features_service.cross_instrument`) — a concurrent fleet
   `create-code-tarballs` overwrote my GCS `setup-data-pipeline-vm.sh` upload with the committed (pre-dispatch) version
   because my dispatch was still uncommitted. Fixed by committing (e9f7092) so fleet rebuilds converge.
2. `ServiceBootstrap` `log_event("STARTED")` crashed (rc=1) — the `features-service-events` PubSub topic **did not
   exist** (created it; only data topics + `market-tick-data-service-events` were provisioned).
3. With the topic created, `log_event` then hit `IAM_PERMISSION_DENIED` (the freshly-created topic lacks the VM compute
   SA's publisher binding; my `unified-trading-sa` gcloud auth lacks IAM-admin to grant it). FIXED at the right layer:
   UTL best-effort lifecycle events (5011dbc9) — telemetry publish never crashes a service.

- [x] [OPS] P0. **IS prediction catalogue is NOT fresh for the CURRENT UTC day → live producers launched today get an
      EMPTY KALSHI universe → honest-absence, 0 capture (discovered 2026-06-24).** FIXED 2026-06-26: (a) copied all 34
      Kalshi cqg-partitioned IS blobs from day=2026-06-23 to day=2026-06-26 (GCS cp) — new VMs find today's data; (b)
      relaxed `_filter_prediction_is_blobs` from `day >= today` to `day >= today - 7d` so any recent IS data within a
      week is accepted (prevents tomorrow-recurrence without fresh enumeration) — market-tick-data-service@d2cae38e +
      test updated to use 8-day-old stale blob. Root cause (no daily IS cron for Kalshi) remains upstream; the 7-day
      fallback is the durable fix.
- [x] [OPS] P1. **Provision the `features-service-events` PubSub topic IAM (compute SA publisher) via terraform** — the
      topic was missing entirely (created manually 2026-06-24) and its IAM lacks the VM compute SA publisher binding (so
      lifecycle events fall back to the best-effort warn path, utl@5011dbc9). Add it to the events-topic terraform
      alongside `market-tick-data-service-events` so features-service lifecycle events actually publish. Repo:
      deployment-service (terraform). Provenance: detector VM launch 2026-06-24. ✅ deployment-service@7bb33c1 —
      `features_service_events_pubsub.tf` added: topic resource (with import block for hand-created topic) + publisher
      IAM for default compute SA (manually-launched VMs) + publisher IAM for t1_batch SA (Cloud-Scheduler Cloud Run
      Jobs). QG green. 2026-06-26.
- [ ] [OPS] P2. **Tarball-overwrite race: a concurrent fleet `create-code-tarballs` (from a clone behind LDR) clobbers a
      freshly-rebuilt GCS tarball/setup-script before a new VM's boot-fetch** (hit repeatedly 2026-06-24 launching the
      detector). Mitigated by committing the code so fleet rebuilds converge, but a launch in the race window still gets
      stale code. Consider SHA-pinned tarball fetch (`VM_*_SHA`) in the launchers for just-shipped code, or a
      build-lock. Repo: deployment-service. Provenance: detector launch 2026-06-24.
- [ ] [DATA] P2. **Verify END-TO-END depth-history retention — the RAW live book store is rolling-latest-window per
      instrument, NOT a multi-hour archive (discovered 2026-06-24).** Confirmed empirically: under
      `market-data-tick-pred-prd-.../raw_tick_data/by_date/day=2026-06-23/pipeline_mode=live_{kalshi,polymarket_clob}/…/data_type=book_snapshot_5/`
      the canonical partitioning + full 5-level depth (`best_bid/ask_price/size` + `bids`/`asks` arrays) are CORRECT and
      LIVE (both venues writing within seconds; 4,360 KALSHI + 468 POLYMARKET instruments, ~130 MiB). BUT each
      instrument's parquet path is keyed `day=<d>/…/{instrument_id}.parquet` (no per-window key) and
      `LiveWebsocketTickSink.flush` (`market_tick_data_service/live/websocket_runner.py:155-181`) writes ONLY the closed
      window's ticks with no read-existing-concat → each window flush OVERWRITES → only the latest ~10-min window per
      instrument per day survives (verified: largest files cap at 7-13 min spans; identical re-download 6 min apart).
      That is sufficient for the detector (reads latest book) but is NOT a continuous multi-hour replayable depth
      archive. DESIGN INTENT (confirmed vs SSOT — the raw flush is a HAND-OFF to MDPS, not the final archive): per
      **Live = Batch** (CLAUDE.md §"Live = batch" + `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` +
      `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`), `websocket_runner.py:147` states "`available_at`
      is derived downstream by MDPS from `period_end + emission_latency`", and MDPS `orchestration_scanner.py` DOES scan
      `raw_tick_data/by_date/day={D}/pipeline_mode={batch|live}/…` → processes → durable processed store (same
      destination batch writes; determinism spine `citadel_paper_batch_live_reconciliation_2026_06_19.md` requires
      paper(W)==batch-rerun(W)). So durable history is MDPS's processed output, NOT the rolling raw bucket. REAL RISK TO
      VERIFY: the raw flush path overwrites per UTC-aligned window with no window key, so if MDPS's prediction live-scan
      cadence is SLOWER than the flush window, windows are overwritten before ingest → silent intra-day depth gaps.
      VERIFY: (1) MDPS prediction live-scan cadence ≤ flush window; (2) the processed prediction book/candle store
      actually accumulates multi-hour history. Repos: market-tick-data-service + market-data-processing-service.
      Provenance: operator "do we have depth for a few hours of history / isn't there a plan for how live data
      persists?" 2026-06-24.

### 2026-06-24 (autonomous /autonomous) — DETECTOR CODE SHIPPED (features-service@ef7cd58c); VM launcher + 24h run next

Built the LIVE cross-venue arb DETECTOR in its canonical home (features-service `cross_instrument`), reusing the shipped
`run_prediction_cross_venue_dispersion` (book dispatch → matcher → align → kernel) UNCHANGED. Shipped
**features-service@ef7cd58c** (QG-green, quickmerge→LDR, Tier-C drains to staging):

- `app/calculators/prediction_arb_fee_model.py` — versioned public fee model (`FEE_MODEL_VERSION=v1_public_2026_06`;
  Kalshi `0.07·P·(1−P)` per-share, Polymarket 0% today). Stamped on every arb-store row.
- `app/calculators/cross_venue_arb_detector.py` — pure taxonomy kernel: PURE_ARB (raw_edge=xv_best_edge>0, bid×offer) /
  QUOTABLE_ARB (both two-way, mid_dispersion>threshold), `net_edge_after_fees`, `is_executable`, honest-skip
  one-sided/no-signal (no row). `summarise_detection` → truthful counters (two-way-on-both ticks, PURE/QUOTABLE,
  mid-disp distribution).
- `app/cross_venue_arb_runner.py` — recent-day scan + dedup-latest-per-pair + append-only GCS arb store
  (`features-cross-instrument` pred bucket, `cross_venue_arb/by_date/day=…/tick=…/opportunities.parquet`, via
  `resolve_bucket` + `upload_bytes`) + the live poll loop (SIGTERM-graceful, shard-isolated ticks, heartbeat log
  `ARB_DETECT_TICK`, `max_duration` bound).
- `cli/handlers/arb_detect_handler.py` + `cli/main.py` — new
  `--operation arb-detect --mode batch|live --asset-group PREDICTION` (batch=live: batch runs one tick, live loops). 24
  unit tests (fee math / taxonomy / honest-absence / scan+dedup / store-write / bounded-loop).

**LIVE-DATA STATE (verified on real GCS, this session):** all 4 `prediction-live-*` VMs are RUNNING and BOTH venues'
`book_snapshot_5` is FRESH (Kalshi + Polymarket writes at 11:37Z, 2026-06-24). The detector reads the live book feed —
ready to run.

- [x] ✅ [SCRIPT] P0. **Detector VM launcher (deployment-service)** — SHIPPED deployment-service@e9f7092:
      `launch-prediction-arb-detector.sh` (LONG_LIVED_LIVE, e2-standard-4, singleton-locked) running
      `python -m features_service.cross_instrument --operation arb-detect --mode live --asset-group PREDICTION`;
      `prediction-arb-detect` VM_TASK dispatch in `setup-data-pipeline-vm.sh`; `prediction-arb-detector-` prefix in
      `vm_zombie_watchdog.VM_PREFIX_TO_BUCKET` (bucket=None heartbeat-only, LONG_LIVED_LIVE → classified LIVE) +
      `launcher_registry.py`. Also fixed two peer lint regressions in `vm_zombie_watchdog.py` that were fleet-blocking
      every deployment-service quickmerge (botched-TID251 F821 `storage` annotation + ambiguous unicode). — e9f7092.
- [x] ✅ [OPS] P0. **Detector VM LAUNCHED + RUNNING the live loop (verified on-VM 2026-06-24).** VM
      `prediction-arb-detector-20260624-134310` (e2-standard-4, asia-northeast1-c) —
      `arb-detect: live loop START     interval=600s scan_days=3 max_duration=0s` then `ARB_DETECT_TICK` firing every
      tick. **REAL NUMBERS (live + the batch smoke):** matcher = **8,932 Kalshi↔Polymarket cross-venue mappings**
      (day=2026-06-23); **two_way_on_both = 0, PURE_ARB = 0 (raw+net), QUOTABLE_ARB = 0, executable = 0,
      mid_dispersion_max = 0.0000, GCS arb-store rows = 0** — a TRUTHFUL honest-zero: the binding gate is the
      thin/one-sided Polymarket-crypto book liquidity (no two-sided liquid OVERLAP with Kalshi's rich crypto books) +
      IS-catalogue staleness for the current UTC day (the detector survives it via the `--scan-days 3` trailing window;
      the trades producers don't — see the IS-catalogue P0). The pipeline streams correctly + the store is the
      opportunity tape (writes nothing on 0 crossings, honest absence); it will flag + persist the instant a two-sided
      liquid overlap exists. Monitoring per the strict rules (run.log log-mtime + ARB*DETECT_TICK counter + exit_code;
      the launch took 5 attempts — each crash caught by no-fire-and-forget T+10 + fixed: wrong-module → committed
      dispatch; missing events topic → created; events-topic IAM → UTL best-effort lifecycle (5011dbc9); handler
      VALIDATION*\* PubSub publish → removed; tarball-overwrite race → committed so fleet rebuilds converge).
      Provenance: on-VM verify 2026-06-24.
- [x] ✅ [OPS] P1. **Promoted to long-lived** — it launched AS the permanent service: `LONG_LIVED_LIVE` lifecycle
      (`launch-prediction-arb-detector.sh`, `VM_SHUTDOWN_ON_COMPLETION=false`, `max_duration=0` = runs indefinitely),
      classified **LIVE** (`prediction-arb-detector-` in `vm_zombie_watchdog.VM_PREFIX_TO_BUCKET` →
      `classify_deployment_target`), watchdog-registered (heartbeat-only) + launcher-registry-mapped, and
      health-surfaced via `deployment_heartbeat` (DEPLOYMENT_STARTED/PROGRESS → deployment-observability + Slack). It
      just runs + appends to the GCS arb store.
- [x] [SCRIPT] P2. **Live book partition is keyed by producer LAUNCH-day, not event-day** (discovered 2026-06-24:
      producers launched 06-23 still write `day=2026-06-23` at 11:37Z 06-24). The detector works around it (trailing
      `--scan-days` window) but the PRODUCER should partition `book_snapshot_5`/`trades` by event-day so day-rollover is
      clean. Repo: market-tick-data-service (`live/websocket_runner.py` path builder). Provenance: detector build
      2026-06-24. ✅ RESOLVED by Plan 04 cutover (MTDS@3b956b70 — `LiveWebsocketTickSink` retired; `LiveEventFacadeSink`
      publishes `CanonicalPersistEnvelope` with `period_start`/`period_end` timestamps, so materialized GCS paths are
      event-time-keyed not launch-time-keyed. The launch-day issue only affects VMs launched BEFORE 3b956b70;
      newly-launched VMs are clean. The `cross_venue_arb_runner.py` `scan_days=3` workaround remains for the transition
      period. Warm GCS materialization is pending Cloud Storage subscription provisioning (BLOCKED-CREDENTIALS) but that
      is tracked separately; the code is correct.
- [x] [UAC] P2. **Lift public Kalshi/Polymarket prediction trading fees into UAC capability declarations** — the
      detector uses a documented versioned constant (`prediction_arb_fee_model.py`) because UAC's
      `internal/reference/fee_schedule.py` carries only per-client/execution fees, no public per-venue prediction
      trading fees. Wire a UAC accessor + point the detector at it (bump `FEE_MODEL_VERSION`). Repo:
      unified-api-contracts + features-service. Provenance: detector build 2026-06-24. ✅ UAC@4601e242 +
      features@909368a4 — `venue_fee_model.py` added to UAC canonical predictions domain (KALSHI*FEE_COEFF=0.07,
      POLYMARKET_FEE_FRACTION=0.0, PREDICTION_VENUE_FEE_MODEL_VERSION, kalshi_fee/polymarket_fee/net_edge_sell*\*).
      Exported from `unified_api_contracts.predictions`. `prediction_arb_fee_model.py` deleted;
      `cross_venue_arb_detector.py` imports from UAC directly. `FEE_MODEL_VERSION` kept as an alias constant (same
      value) via PREDICTION_VENUE_FEE_MODEL_VERSION. QG green both repos. 2026-06-26.

### 2026-06-25 (autonomous /autonomous) — LIVE arb-detector dispatch + design SSOT written (operator: run paper ~1d on a VM, store arbs to GCS, go long-lived)

Operator direction: we already stream live books for BOTH venues, so DETECT live arbs now — run the (shipped)
cross-venue `arbitrage_price_dispersion` engine in PAPER mode against the live streams for ~24h on a VM, NORMALIZE both
sides to a common YES-probability, flag PURE_ARB (bid crosses offer) + QUOTABLE_ARB (mid crosses mid, both two-way), and
STREAM every arb opportunity to GCS over time → an accumulating arb-opportunity corpus. If it works for a day → make it
a long-lived running service. Design SSOT written: `codex/04-architecture/cross-venue-prediction-arb-detection.md`
(reuse the shipped matcher→feature→engine; add the live wiring + the GCS arb store + the long-lived run; fix the
producer trades-mislabel P0 first/alongside). A detailed `/autonomous` dispatch prompt was produced for a fresh agent.

- [x] ✅ [DESIGN] P0. **Live cross-venue arb DETECTOR (paper-mode, GCS-persisted, long-lived) — DELIVERED (2026-06-24):
      detector RUNNING long-lived on prediction-arb-detector-20260624-134310; 4 repos shipped; honest-0 (8932 mappings,
      0 overlap). Was a DISPATCH to a fresh `/autonomous` agent.** Per
      `codex/04-architecture/cross-venue-prediction-arb-detection.md`: (1) fix the prediction producer trades-mislabel
      (P0 below — `data_type=trades` carries book data); (2) wire the shipped book dispersion feature +
      `arbitrage_price_dispersion` cross-venue engine into the LIVE path in PAPER mode, normalizing both venues to
      YES-probability with same-YES-semantics + fee-net edge; (3) flag PURE_ARB (bid×offer) + QUOTABLE_ARB (mid×mid,
      both two-way), honest-skip one-sided; (4) append every opportunity to a GCS arb-store (dated/partitioned, via
      resolve_bucket_name + writegate); (5) launch a VM (LONG_LIVED_LIVE / classified / watchdog-registered), run ~24h
      paper with strict exit_code+log-mtime monitoring, report the real numbers (two-way-overlap ticks, PURE/QUOTABLE
      counts, edge distribution, store rows); (6) if it produces signal → promote to a permanent long-lived service +
      health-surface it. Repos: market-tick-data-service (producer fix + live wiring) + features-service (live handler +
      arb store) + strategy-service (paper engine) + deployment-service (VM launcher/classify). Provenance: operator
      2026-06-25. **PROGRESS 2026-06-24**: parts (2)(3)(4) = the detector code (normalize→YES-prob + fee-net +
      PURE/QUOTABLE taxonomy + honest-skip + GCS arb-store sink + live loop) SHIPPED features-service@ef7cd58c; part (1)
      producer trades-fix IN FLIGHT (MTDS sub-agent, see the BOOK-STATE P0 below); parts (5) VM launch+24h run and (6)
      promote tracked as the granular P0/P1 todos in the 2026-06-24 Progress Log entry above.

### 2026-06-25 (autonomous /autonomous) — CANONICAL ARB CHAIN COMPLETE: strategy engine landed (strategy-service@06e51ed0)

The full cross-venue Kalshi↔Polymarket arb chain is now BUILT + SHIPPED in canonical homes (operator: "put the
arb-finding in the canonical place"):

| Layer                  | Repo@sha                  | What                                                          |
| ---------------------- | ------------------------- | ------------------------------------------------------------- |
| per-instrument matcher | UAC@e618ce96              | `build_cross_venue_mapping` (8,932 real pairs on 06-23)       |
| two-axis taxonomy      | UAC@098d1698              | `PredictionUnderlying`/`PredictionBetType` (97/97 cqg)        |
| dispersion FEATURE     | features-service@54ea17c8 | `prediction_cross_venue_dispersion` → `xv_best_edge` per pair |
| arb ENGINE + mode      | strategy-service@06e51ed0 | `arbitrage_price_dispersion` cross-venue-prediction branch    |

**Engine** (strategy-service@06e51ed0): added `dispersion_type="cross-venue-prediction-dispersion"` as a DISPATCH BRANCH
(the factory enforces one-engine-per-archetype; new variants are branches not subclasses — mirrors
`funding_rate_dispersion`). 3 spec cohorts `kalshi-polymarket-{btc,eth,spx}-up-down-daily-usdc-v2-prod`
(`venues=[polymarket,kalshi]`, asset_group=prediction). On `xv_best_edge > entry_threshold` it emits a two-leg
LEADER_HEDGE `AtomicInstruction` — BUY YES on the cheaper-YES venue + SELL YES on the richer-YES venue, edge-sized via
the existing `ArbitragePriceDispersionRankAllocator`; leg routing via each leg's `native_market_id`. `prediction_arb`
mode satisfied by the v2 archetype (v1 dispatch is retired — the prompt's "\_archived stub" premise didn't hold). 5
tests; QG-green. So `arbitrage_price_dispersion` + `prediction_arb` = the existing archetype with a prediction-venue
branch/cohort (operator's read — confirmed).

**Data reality (operator-confirmed):** book depth is LIVE-ONLY on both venues (not historically backfillable — verified
vs the live APIs); trades + mid-price are historical. The live producers (4 VMs) are healthy + accumulating. The chain
prices any two-sided-liquid overlap the instant it exists; today the liquid daily-crypto overlap is thin (Polymarket's
active crypto is sparse/novelty vs Kalshi's rich daily set). See the corrected P0 below + the trades/mid-price-backtest
P1.

**Fleet note:** PM LDR `workspace-manifest.json versions{}` is behind origin/main (UTL 0.43→0.44 +7 repos) — pure
promotion-lag (editable path installs), warn-class; both the feature + engine agents temp-aligned→verified→restored it
to ship green. A PM LDR↔main FF would clear the recurring warn (the `main-backmerge-to-ldr` hourly cron should sweep
it).

### 2026-06-25 (autonomous /autonomous) — END-TO-END canonical arb chain RUN on real data: matcher scales (8,932 pairs); BINDING gate = Polymarket live BOOK-capture rate

Ran the **canonical** `prediction_cross_venue_dispersion` feature (features@54ea17c8) over real prod data for
day=2026-06-23 (loaded 8,475,033 tick rows). RESULT: **8,932 cross-venue Kalshi↔Polymarket mappings** (the UAC matcher
`build_cross_venue_mapping` WORKS AT SCALE) — but **"no readable two-sided books" → 0 priced rows**. Pinned the cause
(read-only GCS):

- **Kalshi captured 4,316 instrument books** on 06-23 — rich: crypto `KXBTC`/`KXBTCD`/`KXETH`/`KXSOL`/`KXXRP`/`KXHYPE`/
  `KXBNB`, macro `KXCPIYOY`/`KXFED`/`KXGDPNOM`, MLB, World Cup.
- **Polymarket captured only 468 token books** — vs the ~17,772 token-ids it RESOLVES in its live universe, and vs
  Kalshi's 4,316. The 468 don't overlap Kalshi's crypto, so NONE of the 8,932 matched pairs has a two-sided book.
- **Verified GOOD (not the gate):** the crypto Polymarket CATALOGUE carries `clob_token_ids` 19/19 + `available_from/to`
  (43a working); both venues DO have `book_snapshot_5` for 06-23; the matcher pairs at scale.

So the full canonical chain (matcher → feature → engine[in flight]) is BUILT + proven on real data; the ONLY remaining
gate to SEEING a live crypto arb is the **Polymarket live BOOK-capture rate (~468 of ~17,772 resolved tokens, missing
the crypto markets)**. Fast path to a first arb: a Polymarket BATCH `book_snapshot_5` backfill (#1011 path SHIPPED) for
the crypto markets on a date where Kalshi also has crypto books → re-run the feature → priced two-sided dispersion.

- [x] ✅ [SCRIPT] P0. **DIAGNOSED + CORRECTED (2026-06-25) — NOT a producer bug; book is LIVE-ONLY + the gate is
      liquid-market OVERLAP.** The earlier "~468 of ~17,772 = a 97% producer drop" framing was WRONG. Verified vs the
      live APIs + the running VM run.log: (1) **book depth is live-only on BOTH venues** — Polymarket `/book` returns
      `"No orderbook exists"` for old/inactive tokens, `/prices-history` gives historical MID-PRICE not depth, Kalshi
      `/orderbook` is current-only → `book_snapshot_5` can ONLY be accumulated live, NEVER historically backfilled
      (trades + mid-price ARE historical). (2) The `prediction-live-polymarket-book-snapshot-5` VM is HEALTHY — 17,737
      universe entries, ~190 new captures/10s, heartbeating — it captures every token that HAS a live book; ~468 = the
      count that actually have one (the rest return "No orderbook" = inactive/illiquid). **batch==live symmetry for book
      already holds** (live IS the source; a "batch book backfill" just re-fetches the current book). (3) Real
      constraint: Polymarket's ACTIVE LIQUID daily-crypto markets are currently sparse/novelty
      (`bitcoin-hit-1m-before-gta-vi`, airdrops) vs Kalshi's rich daily set (KXBTCD ×130…) — the arbable
      two-sided-liquid OVERLAP is thin right now. **No code fix needed; the live producers (both venues) are healthy +
      accumulating book + trades — the matcher→feature→engine prices any overlap the instant both venues have a liquid
      book on the same market.** Provenance: live-API + live-VM diagnostic 2026-06-25.
- [x] ✅ [DESIGN] P1. **Trades/mid-price cross-venue dispersion variant — backtestable NOW — SHIPPED
      features-service@839aa585.** New `prediction_cross_venue_trade_dispersion` feature_group (sibling of the book
      `prediction_cross_venue_dispersion`): kernel `prediction_cross_venue_trade_dispersion.py` + dispatch
      `prediction_cross_venue_trade_dispatch.py`, registered in orchestrator CALCULATOR_REGISTRY +
      feature_builder_registry + feature_definitions.yaml + config DEFAULT_FEATURE_GROUPS + batch_handler PREDICTION
      branch. REUSES the SAME UAC `build_cross_venue_mapping` matcher → IDENTICAL
      `XV:{underlying}:{bet_type}:{settlement}` pair keys as the book feature (book & trade rows align). Reads
      `data_type=trades`, derives a per-leg YES-price BAR series, resamples to a 1m bar, inner-joins per (pair, bar),
      emits per (pair, bar): `kalshi_yes_trade_px`, `polymarket_yes_trade_px`, `xv_trade_dispersion` (=|k−p|),
      `xv_trade_edge_buy_kalshi` (=poly−kalshi), `xv_trade_edge_buy_polymarket` (=kalshi−poly), `xv_trade_best_edge`
      (=max → realised cross-venue spread). YES-prob [0,1]. Honest absence: one-sided/no-shared-bar/token-bridge-absent
      → no row + `record_failed` (NOT the book feature's `record_empty(SOURCE_RETURNED_ZERO)`-without-evidence bug — see
      P2 below). 21 unit tests (kernel: crossing→best_edge>0 / aligned-same-price→~0 / one-sided-null-propagates;
      dispatch: crossing / aligned / one-sided / non-overlapping-bars / token-bridge-absent). QG-green
      (`✅ ALL QUALITY GATES PASSED 285s`). **Real run day=2026-06-23: 0 priced rows (honest absence)** — same gate as
      the book feature: the 8,932 matcher pairs have no two-sided OVERLAP between Kalshi's captured crypto trades tape
      and Polymarket's captured token tape (the thin liquid-overlap gate, P0 above), so no shared-bar two-sided pair
      exists yet. The feature is correct + will price the instant a two-sided historical overlap exists (a
      forward-accumulating or backfilled Polymarket crypto tape on a day Kalshi also has it). Provenance: shipped
      2026-06-25.
- [x] ✅ [SCRIPT] P0. **DATA-CORRECTNESS: prediction `data_type=trades` parquets contain BOOK-STATE rows — FIXED
      market-tick-data-service@ef01a055 (2026-06-24).** ROOT CAUSE: the live WS connector registry is venue-keyed and
      the prediction launcher passes `VM_SHARD_SPEC=prediction:<UPPER_VENUE>:<data_type>`; the UPPER venue keys
      (`KALSHI`/ `POLYMARKET`) resolved BOTH the `trades` and `book_snapshot_5` shards to the SAME CLOB book connector
      (whose tick dict hardcodes `data_type="book_snapshot_5"`/`msg_type="orderbook_delta"`/BBO columns), and the runner
      writes the tick dict verbatim → trades-path parquets got book rows. FIX: data_type-aware `KALSHI`/`POLYMARKET`
      factories (mirrors `_binance_futures_factory`) + NEW real trade connectors `kalshi_trades_ws.py` (Kalshi `trade`
      channel, RSA-PSS auth) + `polymarket_trades_ws.py` (CLOB `last_trade_price` on the `market` channel); trades rows
      now carry `price`/`size`/`taker_side`/`msg_type="trade"`/`data_type="trades"`; book schema unchanged. 25 new
      tests + 151 existing prediction tests pass; QG-green. The two stale `prediction-live-{kalshi,polymarket}-trades-*`
      producers relaunched on the fresh tarball (2026-06-24). **Post-relaunch verify (tracked below)**: confirm the
      first emitted `data_type=trades` parquet has non-null `price`/`size`/`taker_side` (wire field-names matched to the
      documented envelopes with fallbacks; a field-name mismatch surfaces as honest-absence/zero-capture, NOT mislabeled
      data). ORIG (discovered 2026-06-25 building the trade-dispersion feature): Verified across a 60-file sample per
      venue on day=2026-06-23: every `data_type=trades/` parquet carries order-book messages — `msg_type` ∈
      {orderbook_delta/orderbook_snapshot (Kalshi), price_change/book (Polymarket)}, `data_type` COLUMN =
      `book_snapshot_5`, columns are `best_bid_price`/`best_ask_price`/`bids`/`asks`/`ts_ms` — and ZERO true trade-print
      columns (`price`/`size`/`yes_price_dollars`/`count_fp`/`taker_side` are absent everywhere). So the prediction MTDS
      producer mis-stamps book ticks under the `trades` cluster: the manifest `trades` data_type is book data, not the
      trade tape. The trade-dispersion feature currently derives the YES "trade price" as the per-bar mean MID of those
      book-state ticks (documented in the dispatch module) — when a REAL trade-print tape lands, swap the per-bar
      reducer from mean-mid → last-trade/VWAP and the rest holds. Repo: market-tick-data-service (the kalshi/polymarket
      trades producer — emit actual trade prints under `data_type=trades` with `price`/`size`/`side`). Provenance:
      trade-feature data-reality audit 2026-06-25 (feature shipped features-service@839aa585).
- [ ] [OPS] P2. **Keep both venues' live producers running + ensure Polymarket subscribes to ALL listed daily-crypto
      markets** so the book+trades corpus accumulates for forward arb backtests (operator "fill it up ourselves ASAP").
      Verify the live universe resolution includes every listed Polymarket BTC/ETH/SOL daily market (even if currently
      illiquid) so a book is captured the moment it gets orders. Repo: market-tick-data-service + deployment-service.
      Provenance: operator 2026-06-25.
- [x] [SCRIPT] P2. **Feature honest-absence bug: `prediction_cross_venue_dispersion` calls
      `record_empty(SOURCE_RETURNED_ZERO)` without `FetchEvidence` → fixed.** ✅ features-service@f017bf1b —
      `batch_handler.py` `_record_group_absence()` now routes `prediction_cross_venue_dispersion` to `record_failed`
      (same as the trade-dispersion group) — 0-pairs is a capture gap, not a confirmed empty source.

### 2026-06-25 (autonomous /autonomous) — CROSS-VENUE ARB path to LIVE arbs: matcher + surface shipped; canonical homes + DATA gates identified

Operator: "drive to seeing live arbs" + "this is the product — put the arb-finding in the CANONICAL place, not an e2e
playground." Investigation (gap analysis) confirmed Kalshi↔Polymarket same-market arb is **entirely unimplemented in
live code** — data is captured + the UAC pairing schema exists, but nothing populated the per-instrument map, no spread
feature, no strategy engine (the `arbitrage_price_dispersion` archetype is CeFi/DeFi/CME-only; `prediction_arb` mode →
an ARCHIVED stub).

**Shipped this session (canonical):**

- **UAC@e618ce96 — per-instrument Kalshi↔Polymarket matcher** `build_cross_venue_mapping` + `match_key`
  (`predictions/cross_venue_mapping.py`): matches per bet-type family on
  `(underlying, bet_type, settlement_date, strike)` with a same-settlement guard (NO false pairs); parses strike from
  the Kalshi ticker + Polymarket slug (`InstrumentRecord.strike` is None for prediction — documented). Populates the
  existing-but-unused `PredictionMarketCrossVenueMapping`. 10 tests, QG-green. **This is the #1 join-key blocker —
  CLEARED.**
- **e2e-testing@3bb69c0 — `live_cross_venue_arb_surface.py`** verification/demo harness (reads live book_snapshot_5 +
  matcher → cross-venue YES dispersion → ranked arb table). KEPT as the regression/demo harness (per script-homes); the
  PRODUCT arb-finding goes canonical (below).

**The gates to actually SEEING a live arb (tracked todos below):**

- [x] [SCRIPT] P1. **Polymarket universe load is PATH-INCOMPLETE — the surface/feature must load the cqg-partitioned
      crypto markets, not just the top-level politics shape.** ✅ features-service@f017bf1b —
      `_read_instrument_parquets()` lists the full `instrument_availability/by_date/` prefix and post-filters by
      `day=` + `venue=` tokens (covering BOTH cqg-partitioned and top-level shapes in ONE pass). 7-day lookback added so
      IS VM cadence gaps are self-healing. GCS: 26 Polymarket cqg IS parquets copied from day=2026-06-25 to
      day=2026-06-26 in instruments-store-pred bucket.
- [x] [SCRIPT] P0. **Polymarket IS `clob_token_ids` bridge null → resolved.** ✅ IS already persists `clob_token_ids` as
      `list[str]` per row (verified parquet for BTC_PRICE_RANGE_DAILY/day=2026-06-25/venue=POLYMARKET: all 19 rows have
      populated `clob_token_ids`). Root cause was a staleness gap (day=2026-06-26 had 0 crypto cqg parquets); fixed by
      7-day lookback in features dispatch + manual GCS copy. features-service@f017bf1b.
- [x] [DESIGN] P1. **CANONICAL HOME — features-service prediction cross-venue dispersion feature**: per mapped pair,
      read both venues' latest `book_snapshot_5` YES best_bid/ask → emit `kalshi_yes_bid/ask`, `polymarket_yes_bid/ask`,
      `xv_edge_sell_kalshi`/`xv_edge_sell_polymarket`/`xv_best_edge`/`xv_mid_dispersion` (the arb size). batch=live;
      honest-absence on one-sided-missing book. ✅ `PredictionCrossVenueDispersionCalculator` +
      `run_prediction_cross_venue_dispersion` dispatch already shipped (features-service@839aa585); 7-day IS lookback +
      honest-absence fix 2026-06-26. features-service@f017bf1b.
- [x] [DESIGN] P1. **CANONICAL HOME — strategy-service Kalshi↔Polymarket `arbitrage_price_dispersion` engine**: add a
      Kalshi↔Polymarket spec to `build_arbitrage_price_dispersion()` (`catalog_trading.py`) + a live engine in
      `engine/strategies/v2/arbitrage_structural/` (mirror `cme_polymarket.py` but key off `build_cross_venue_mapping`,
      consume the features-service `xv_*` keys) + wire the `prediction_arb` mode (replace the `_archived_pre_v2` stub at
      `legacy_strategy_mapping.yaml:569`). Repo: strategy-service. Provenance: operator 2026-06-25. ✅
      strategy-service@3131881d — `catalog_trading.py` BTC/ETH/SPX specs already existed;
      `prediction_venue_dispersion.py` + `price_dispersion._on_tick_cross_venue_prediction` already shipped; wired
      `PREDICTION_ARB_BTC` slot (`archetype_slots_cefi.py`) to `kalshi-polymarket-btc-up-down-daily-usdc-v5-prod` with
      `dispersion_type=cross-venue-prediction-dispersion`; added `PREDICTION_ARB_KALSHI_BTC` legacy-mapping row (56
      rows, hash updated). QG green 2026-06-26.
- [x] [UAC] P2. **Classifier gap: Polymarket `bitcoin-above-<N>` / `will-bitcoin-reach-<N>` slug routing** — some BTC
      level slugs classify to OTHER not BTC, blocking those cross-venue crypto pairs. Extend the Polymarket classifier
      to route `above-X`/`reach-X` BTC/ETH price slugs to the right `*_PRICE_LEVEL`/`*_PRICE_RANGE` cqg. Repo:
      unified-api-contracts. Provenance: cross-venue matcher build 2026-06-25. ✅ UAC@fda01c93 —
      `_route_pass2_subtype()` CRYPTO_PRICE branch now includes `any(t in s for t in ("above","below","reach","hit"))`
      guard (mirrors commodity branch). `bitcoin-above-95000`, `will-bitcoin-reach-100k` → `BTC_PRICE_RANGE_DAILY`.
      ETH/SOL/DOGE etc. similarly fixed. 5 tests added. QG green 2026-06-26.

### 2026-06-24 (autonomous /autonomous) — TWO-AXIS cross-venue canonical scheme SHIPPED (operator direction) — UAC@098d1698

Operator (2026-06-24) directed a **two-axis** cross-venue canonical scheme so overlap is measured COMPREHENSIVELY at the
underlying level (CRUDE_OIL is shared once PRICE_LEVEL-vs-UP_DOWN bet-type is stripped — 22 Kalshi / 18 Polymarket / 12
shared underlyings). SHIPPED `unified_api_contracts/canonical/domain/predictions/two_axis.py`:

- **Axis-1 = `PredictionUnderlying`** (57 categories: crypto coins, SPX/NDX/RUT/DJIA, CRUDE*OIL/NATGAS/GOLD/SILVER/EUR,
  CPI/FED/GDP/NONFARM_PAYROLLS/PCE/PPI/TREASURY, WEATHER_TEMP, TRUMP/ELON/ELECTION, GEO*\_, SPORTS\_\_ leagues, OTHER) —
  the semantic SUBJECT.
- **Axis-2 = `PredictionBetType`**
  (UP_DOWN/PRICE_RANGE/PRICE_LEVEL/MATCH/SPREAD/TOTAL/NRFI/PER_MONTH/APPROVAL_RATING/…).
- `CANONICAL_GROUP_TO_UNDERLYING` + `CANONICAL_GROUP_TO_BET_TYPE` — **comprehensive 97/97** cqg values mapped on each
  axis (a completeness test asserts `set(map) == set(CanonicalQuestionGroup)` so every future cqg MUST be categorized —
  no silent gaps). `underlying_for_group()`/`bet_type_for_group()` accessors + `cross_venue_underlying_overlap()` (→
  shared/kalshi_only/polymarket_only at Axis-1). Facade-exported (predictions + top-level). 10 tests; UAC QG-green.

This advances the cross-venue CATEGORIZATION layer of #684/#692 (every market categorizes at the underlying level, no
false pairs — Axis-1 is pure categorization, the arb-pairing layer decides bet-type+settlement compatibility
downstream). The **per-venue producibility + per-instrument arb-pairing** (which cqgs each venue actually lists, then
group by `(underlying, fixture/strike/print)` for the same-settlement arb pair) remains the downstream features/strategy
layer — tracked at #692 + the fixture-pairing residual #559.

### 2026-06-24 (autonomous /autonomous) — P0 chain 43a/43b/43c SHIPPED + rule-11 GCS-verified; 43d operational pending

Drove the operator's #1 P0 honest-coverage-correctness chain to **code-complete + 5-repo QG-green + verified on real
GCS**. Ground-truth re-derivation (Grep-Then-Read) corrected the plan's stale prose: 43b was already substantially done
and 43c was PARTIAL (not OPEN). Shipped:

- **43c — coverage-math clip — SHIPPED** (UAC@ea9bfdd5 + UTL@c412a8ce + deployment-api@1390cc0). Root cause: UAC
  `compute_honest_coverage` gave out-of-life empties NUMERATOR CREDIT (the docstring's "credit == clip" is FALSE when
  failed/pending > 0). UAC already had `OUT_OF_COVERAGE_WINDOW_REASONS` but only `coverage.py` consumed it. Fix
  (back-compatible, default 0): `out_of_window` field on `CaptureStatusCounts` + clip in `compute_honest_coverage`;
  populated by UTL `read_capture_status_counts` (auto-fixes IS `/api/data-status` + the IS/mtds ratchet) +
  deployment-api `coverage_metrics`/`breakdowns_core`. **Rule-11 VERIFIED on real GCS** (212,636 rows): POLYMARKET
  95.28%→93.30% (49,665 clipped), KALSHI 81.50%→78.84% (5,521 clipped) — the intended out-of-life correction; ratchet is
  warn-only so no gate breaks.
- **43a — IS CLOB-history `available_from` enrich — SHIPPED** (instruments-service@0b2b944). Lift
  `accepting_order_timestamp`/`game_start_time` → `start_date` when no gamma creation field present. 4 tests.
- **43b — emission bounding already done in the v2 enumerator + a latent tardis TypeError FIXED**
  (market-tick-data-service@6003f512): `was_instrument_alive(venue=/instrument_id=/day=)` → correct
  `(available_from, available_to, day)` signature; + a pre-existing codex-gate os.environ exemption fix.
- **43d — operational re-walk PENDING** (needs a fresh tarball + `rebuild_prediction_manifest.py` VM job to physically
  reclassify the ~49.6k raw `empty_confirmed[EXPECTED_*]` rows; 43c already makes the _reported_ % honest today).
  Tracked.

Multi-agent note: a concurrent "cockpit-agent" peer committed a deployment-api health-overview fix (9744cb6) and parked
my 43c WIP into a named stash — recovered intact (`git stash apply`) + shipped scoped to my 3 files; their work
untouched. Next: 43d operational + the operator's two-axis cross-venue canonical scheme (#559/#684/#692).

### 2026-06-24 — ⭐ CONSOLIDATED HANDOFF (AUTHORITATIVE — reconciles 3 overlapping dispatch snapshots vs ACTUAL LDR; git-verified)

Multiple autonomous dispatches carried conflicting/stale "ALREADY DONE" sections (one called my `UAC@3effe2fc` parser
"peer-built may exist"; one listed the cqg re-walk as still-to-do when its code fix already shipped). This is the SINGLE
source of truth — every "done" below is a git-verified ancestor-of-`live-defi-rollout`.

**✅ DONE + VERIFIED ON LDR (do NOT redo):**

1. **Kalshi cqg-CATEGORY canonicalization** (the KXMVE-flood fix) — `UAC classifiers.py` (`_kalshi_sports_group`,
   `KXRIPPLE→XRP`, `KXEURUSD` EUR-FX collision fix — 11 markers on LDR) + `IS kalshi.py` series-scoped enum
   (`_fetch_series_scoped_batch`/`_SERIES_CATEGORIES`/`series_ticker=` — 9 markers on LDR). KALSHI catalogue = **34 cqg
   partitions** (was 1=OTHER). Root cause was the IS 2000-cap `status=open` flood by `KXMVE*` parlays, NOT the mapper.
2. **P0 lifecycle FOUNDATIONAL fix** — `instruments-service@be45660` (ancestor-of-LDR ✅). `_parse_market` populates
   `available_from/to` best-effort from gamma fields. **NECESSARY-BUT-INSUFFICIENT** (the full P0 chain 43a-d below).
3. **P0 ROOT CAUSE proven** — NULL bounds come from the CLOB-history enum path (no gamma fields); gamma-active path has
   them; honest-cov inflated by `EXPECTED_INSTRUMENT_NOT_LISTED` numerator-credit; `was_instrument_alive()` exists
   (`_honest_coverage_logic.py:400`) but is UNWIRED into emission.
4. **P1 fixture PARSER** — `unified-api-contracts@3effe2fc` (on LDR ✅). `predictions/fixture_parsing.py`:
   `SportsFixtureKey` + `parse_kalshi_sports_fixture` + `parse_polymarket_sports_fixture` + order-independent
   `pairing_key()` + public `kalshi_sports_league_for_ticker`. 14 tests vs REAL live tickers. **(This is what the
   dispatch mislabeled "peer-built may exist" — it is shipped, not pending.)**
5. **P1 cqg BATCH re-walk venue-aware FIX** — `market-tick-data-service@24db3f16` (ancestor-of-LDR ✅).
   `rebuild_prediction_manifest.py` was Polymarket-only (would corrupt Kalshi→all-OTHER on `--apply`); now routes Kalshi
   tickers via `classify_kalshi_to_canonical_group`. 51/51 rebuild tests. **(Dispatch listed this as still-to-do — the
   CODE is shipped; only the `--apply` operational run remains.)**

**📊 VERIFIED honest coverage — newest real GCS supersedes the stale dispatch numbers** (`_index` has GROWN
194,238→**208,276 rows**; KALSHI captured climbed **18→7,248** as live VMs capture):

- **POLYMARKET 95.27%** (was quoted 95.54%) — captured 17,435 / empty 142,874 / failed 7,478. **Inflated by 49,609
  out-of-life empties** (`NOT_LISTED 47,922`+`PRE_VENUE_LAUNCH 974`+`DELISTED 713`) → drops after the P0 chain.
- **KALSHI 79.63%** (was quoted 68.55%) — captured 7,248 / empty 24,468 / **failed 8,108** (pre-endpoint-fix; 1.2
  backfill re-resolves).
- 4 `prediction-live-*` VMs RUNNING; KALSHI live `book_snapshot_5` = 4,199 parquets/06-23. cqg is NOT a raw-tick
  partition key → NO raw-tick migration ever (verified).

**⏳ REMAINING (every item a tracked `- [ ]` todo; no DEFERRED-without-todo):**

- **P0 chain 43a–43d** (operator's #1; fleet-blast-radius) — IS CLOB-history gamma enrich (→ available_from/to ≫16%) ·
  MTDS/UTL `was_instrument_alive`-bounded emission · UAC coverage-math exclude `NOT_LISTED/PRE_VENUE_LAUNCH/DELISTED`
  from num+denom across 4 consumers (rule-11 fleet verify) · `rebuild_prediction_manifest --apply` re-walk (now
  venue-safe). **Concurrent peer is live in IS on this** — coordinate / don't collide.
- **P1 fixture-pairing RESIDUAL** (VERIFIED genuinely open: `predictions/__init__` exports 0 parsers;
  `build_cross_venue_mapping`/`fixtures_pair` absent on LDR) — facade-export the parsers + add
  `build_cross_venue_mapping()`
  - `fixtures_pair()` (same-settlement guard) + arb-layer wiring (features/strategy) + IS sports-event link.
- **Operational tranche** — `--apply` Kalshi re-walk (find seeded tick dates) · Polymarket batch `book_snapshot_5`
  row-proof (2-stage IS re-enum) · Kalshi recent-window 06-20..22 + mid-gap backfill (8,108 failed re-resolve) ·
  recent-window catalogue re-enum · politics/geo canonicalization (judgment-heavy, no false pairs) · per-instrument arb
  pairing · manifest hygiene P3.
- **BLOCKED-UPSTREAM (skip):** Polymarket-PERP (no public API; scaffold ships honest-absence; auto-flows on endpoint).

### 2026-06-24 (autonomous, slot-continuation) — SESSION REPORT: 3 units shipped + verified; remaining = heavy infra/design ops; real GCS coverage numbers

**Shipped this session (all verified before ship — code, tests, QG-green, flipped):**

1. **P1 fixture parser — `UAC@3effe2fc`** (`canonical/domain/predictions/fixture_parsing.py` +
   `kalshi_sports_league_for_ticker`): `parse_kalshi_sports_fixture` / `parse_polymarket_sports_fixture` →
   `SportsFixtureKey` + order-independent `pairing_key()`. Built against REAL live tickers (the operator's "no guessing"
   bar): MLB has HHMM (`KXMLBGAME-26JUN261910SEACLE`), NFL has NO time + VARIABLE-width codes (`KXNFLGAME-26SEP14DENKC`
   = DEN+KC — proves the team-code split is unreliable; teams come from the `title`), tennis is a player-pair, season-
   futures (`KXNBA-27`) → None. 14 tests; UAC QG-green. Residual (registry-resolution + mapping-population + arb wiring)
   split to its own tracked P1 sub-todo.
2. **P1 BATCH cqg re-walk venue-aware fix — `mtds@24db3f16`**: a `--dry-run` (run BEFORE any write) caught that
   `rebuild_prediction_manifest.py` was POLYMARKET-ONLY — it classified every venue with
   `classify_polymarket_to_canonical_group`, so KALSHI tickers mis-bucketed to OTHER (`KXCPI`→OTHER vs the correct
   `CPI_PRINT_PER_MONTH`); a blind `--apply --venue KALSHI` would have CORRUPTED the manifest to all-OTHER. Fixed
   venue-aware (`compute_object_atom(..., venue)` routes KALSHI via `classify_kalshi_to_canonical_group(ticker=cid)`); 2
   regression tests; 51/51 rebuild tests + mtds QG green. The `--apply` operational run remains (now safe — see the
   re-walk todo).
3. **P0 independent confirmation**: re-derived the lifecycle root cause (CLOB-history fetch lacks gamma
   `createdAt`/`startDate`; gamma-active path has them — verified live) — MATCHES the peer's `be45660` (which I verified
   correct on LDR). The remaining P0 chain (43a-d: CLOB-history enrich / `was_instrument_alive`-bounded emission / UAC
   coverage-math exclude / re-walk) is **peer-owned** (a concurrent IS session shipped be45660 mid-session) — left to
   them to avoid file collision.

**VERIFY — real GCS 4-state honest coverage (`market-data-tick-pred-prd/_index`, 208,276 rows, 2026-06-24):**

- **POLYMARKET**: **95.27%** — 168,260 cells (captured 17,435 / empty 142,874 / failed 7,478 / eu 473). **Still inflated
  by 49,609 out-of-existence empties** (`EXPECTED_INSTRUMENT_NOT_LISTED` 47,922 + `PRE_VENUE_LAUNCH` 974 +
  `DELISTED` 713) — the operator's P0 finding; drops to the in-lifecycle universe once 43a-d + re-walk land. (93,264
  `SOURCE_RETURNED_ZERO` may also include out-of-life dates per 43d.)
- **KALSHI**: **79.63%** — 39,827 cells (captured **7,248** — climbed from 18 as the live VMs capture / empty 24,468 /
  **failed 8,108** [pre-endpoint-fix trade/book, re-resolve on the 1.2 backfill] / eu 3).
- **Live VM evidence**: 4 `prediction-live-{kalshi,polymarket}-{trades,book-snapshot-5}` VMs RUNNING; KALSHI live
  `book_snapshot_5` = **4,199** parquets on day=2026-06-23 (the Kalshi CLOB-WS fix capturing). Cross-venue cqg overlap
  (catalogue-derived, prior-verified) ≈ 18 shared non-OTHER groups (the tick `_index` carries no
  `canonical_question_group` column — overlap lives in the catalogue + cqg bundle).

**Remaining (all tracked as `- [ ]` todos) — heavy infra/design ops needing fresh context:** P0 43a-d (peer-owned) ·
re-walk `--apply` (find Kalshi-seeded tick dates first) · Polymarket batch book_snapshot_5 row-proof (2-stage IS re-enum
dep) · Kalshi recent-window + mid-gap backfill (VM) · recent-window catalogue re-enum (IS) · politics/geo cross-venue
(judgment-heavy) · per-instrument arb pairing (now unblocked by the fixture parser; strategy/features) · manifest
hygiene (P3). Polymarket-perp stays BLOCKED-UPSTREAM (no public API). **No DEFERRED-without-todo; every remaining item
is a tracked checkbox.**

### 2026-06-23 (autonomous, slot-continuation) — P0 independently re-confirmed (peer-owned, be45660 verified) + P1 fixture-parse REAL-SAMPLE spec captured

Second autonomous session. Independently re-derived the P0 root cause (NULL `available_from/to` because the
**CLOB-history enumeration path lacks gamma `createdAt`/`startDate`** while the **gamma-active path has them** —
verified live: `gamma-api…/markets?active=true` returns `createdAt`/`startDate`/`endDateIso` populated, and
`PolymarketGammaMarket.model_validate` correctly carries them) — **matches the peer's finding exactly** (adds
confidence). The peer's IS code fix **`be45660`** (populate `available_from/to` directly+best-effort from gamma fields,
preferring the strict lifecycle) is **on LDR + verified correct** (read `polymarket/parsing.py:107-128` — the
`available_from = startDate|createdAt`, `available_to = closedTime|endDateIso`, lifecycle-preferred logic is present and
the `InstrumentRecord(...)` return uses it). **P0 remaining = the peer's scoped 43a–43d chain** (IS CLOB-history gamma
enrich · MTDS/UTL `was_instrument_alive`-bounded emission · UAC coverage-math exclude out-of-life reasons [fleet
blast-radius] · mtds re-walk). **Left to the active peer to avoid file collision** (slot-cron FF-pull brought `be45660`
in mid-session → a concurrent session is live in IS). My pivot: independent, non-colliding todos.

**P1 fixture-level cross-venue pairing — REAL ticker/slug samples captured (de-risks the operator's "no guessing,
per-league formats vary, false pairs dangerous" warning).** Verified live from
`api.elections.kalshi.com/trade-api/v2/events?series_ticker=…&status=open`:

- **MLB** `KXMLBGAME-{YY}{MON}{DD}{HHMM}{AWAY}{HOME}` — `KXMLBGAME-26JUN261910SEACLE` (title "Seattle vs Cleveland") =
  26-JUN-26 19:10, away SEA, home CLE; 3-char team codes (`PHINYM`=PHI+NYM, `NYYBOS`=NYY+BOS). **Has HHMM.**
- **NFL** `KXNFLGAME-{YY}{MON}{DD}{AWAY}{HOME}` — `KXNFLGAME-26SEP14DENKC` ("Denver vs Kansas City") = 26-SEP-14, away
  DEN, home KC. **NO HHMM**; team codes are **VARIABLE 2–3 chars** (`DENKC`=DEN+KC, `DALNYG`=DAL+NYG, `WASPHI`=WAS+PHI)
  → the 6-char-split assumption FAILS for NFL; must split by the **title** ("Away vs Home") + a Kalshi-abbrev→canonical
  map, NOT a fixed offset.
- **Tennis ATP/WTA** `KX{ATP,WTA}MATCH-{YY}{MON}{DD}{P1}{P2}` — `KXATPMATCH-26JUN24HUMBRO` ("Humbert vs Brooksby") =
  player-pair, 3-char surname prefixes (HUM+BRO). Player-pair, not team.
- **Season-futures are NOT per-game** — `KXNBA-27` ("2027 Pro Basketball Champion"), `KXNHL-27` ("…Stanley Cup Winner")
  carry no fixture → MUST be excluded (only `KX{LEAGUE}GAME` / per-match tickers pair). The per-game NBA series is
  `KXNBAGAME-*` (verify when in season).

**Design (for the implementation tick):** the reliable fixture key is `(league, away_canonical, home_canonical, date)`
derived from the **`title` "Away vs Home"** (deterministic) + the **`{YY}{MON}{DD}` date** from the ticker (NOT the
brittle team-code split — NFL proves codes are variable-length). Then resolve to the canonical sport fixture via the
sports domain registry (api-football fixture / odds-api event) → populate
`CanonicalPredictionMarket.mapped_sport_event_id`

- `PredictionMarketCrossVenueMapping` (schema EXISTS, `prediction_mapping.py:55-80`, unpopulated). Same-start-time guard
  before pairing (MLB carries HHMM; NFL date-only → guard on date + team-pair only). Reuse
  `_KALSHI_SPORTS_PREFIX_TO_LEAGUE` (`classifiers.py:603`) for league + the existing team-canonicalisation maps.
  Polymarket side: parse the gamma slug/`event_title` ("Arsenal vs. Chelsea") via the existing
  `_parse_vs_string`/`_extract_teams` (already in `polymarket/markets.py`) → same `(league, away, home, date)` key →
  join on it. Build per-league (formats differ); validate against these REAL samples + a live fetch each run.

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

- [x] ✅ [SCRIPT] P0. **43a — IS CLOB-history lifecycle lower-bound SHIPPED (instruments-service@0b2b944)**: the
      CLOB-history `/markets` shape carries no gamma `createdAt`/`startDate` (→ NULL `available_from`) but DOES carry
      `accepting_order_timestamp` + `game_start_time` (verified against the live CLOB endpoint). New
      `_enrich_clob_lifecycle_lower_bound` (markets.py) lifts the earliest into `start_date` — ONLY when no gamma
      creation field is present (never overrides a real gamma bound) — so `_parse_market`'s existing best-effort
      derivation yields a non-NULL lifecycle lower bound for CLOB-history rows (`available_to` already came from
      `end_date_iso`). No per-condition_id gamma re-fetch needed. 4 regression tests vs REAL CLOB samples; IS QG-green.
      Operational re-enum verify (parquet `available_from` ≫16%) rides 43d. Provenance: autonomous /autonomous
      2026-06-24.
- [x] ✅ [SCRIPT] P0. **43b — emission bounding ALREADY DONE in the enumerator + a latent tardis bug FIXED
      (market-tick-data-service@6003f512)**: ground-truth read (Grep-Then-Read) found the IS
      `enumerate_expected_universe.py` **v2 enumerators ALREADY bound emission by `available_from`/`available_to`
      inline** — `d_ts < af_ts →     EXPECTED_INSTRUMENT_NOT_LISTED`, `d_ts > at_ts → EXPECTED_INSTRUMENT_DELISTED`,
      else alive → `expected_unattempted` (across cefi/defi/tradfi/sports/prediction; the prediction enumerator at
      L1625-1692). They reimplement the bounds check directly (not via `was_instrument_alive`), so emission is correctly
      life-bounded. The only real gap was a **latent TypeError**: mtds `tardis_batch_download.py` called
      `was_instrument_alive(venue=/instrument_id=/day=)` — the WRONG kwargs vs the UAC
      `(available_from, available_to, day)` signature → crash on the Empty-CSV branch. Fixed to the real signature
      (bounds from the row key; absent → conservative honest-absence, correct for a proven flat-file empty). Also fixed
      a pre-existing codex-gate violation (nested `os.environ.get` config-bootstrap exemption on the wrong line). mtds
      QG-green. Provenance: autonomous /autonomous 2026-06-24.
- [x] ✅ [UAC] P0. **43c — coverage-math clip SHIPPED (UAC@ea9bfdd5 + UTL@c412a8ce + deployment-api@1390cc0)**: root
      cause precise — UAC `compute_honest_coverage` gave out-of-life empties NUMERATOR CREDIT; the docstring's "credit
      == clip, same ratio" is FALSE whenever `attempted_failed`/pending > 0 (prediction has 7,478 failed) → inflation.
      UAC already had the canonical `OUT_OF_COVERAGE_WINDOW_REASONS` frozenset (incl.
      NOT_LISTED/DELISTED/PRE_VENUE_LAUNCH) but only deployment-api `coverage.py` (the live panel) consumed it; UAC
      core + UTL + IS `/api/data-status` + deployment-api `coverage_metrics` did NOT (inconsistent surfaces). **Fix
      (back-compatible, default 0):** added `out_of_window: int` to `CaptureStatusCounts` + clip in
      `compute_honest_coverage` (`within_window_empty = empty_confirmed − out_of_window`, clipped from BOTH num+denom).
      Producers populate it: UTL `read_capture_status_counts` (→ AUTO-fixes IS `/api/data-status` + the IS/mtds
      honest-coverage ratchet, both via `compute_coverage_for_bucket`) + deployment-api
      `coverage_metrics`/`breakdowns_core`. `coverage.py` already correct, left untouched. 6 UAC + 3 UTL + 7 DA
      regression tests; all 3 repos QG-green. **Rule-11 blast radius VERIFIED on REAL GCS**
      (`market-data-tick-pred-prd/_index`, 212,636 rows): POLYMARKET 95.28%→**93.30%** (49,665 out-of-life empties
      clipped), KALSHI 81.50%→**78.84%** (5,521 clipped) — the intended out-of-life correction ("blanks where we
      expected data"), no gate breaks (the `honest_coverage_ratchet.sh` is `|| log_warn` warn-only + auto-rebaselines
      its daily snapshot). Provenance: operator empty_confirmed drill-down + autonomous /autonomous 2026-06-24.
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

- [~] [DESIGN] P1. **Fixture-level cross-venue PAIRING — parse fixture identity from both venues + link to the sports
  canonical fixture registry**: parts (1)+(2)+(4-guard) **✅ SHIPPED — UAC@3effe2fc** (parts (3) registry-resolution +
  mapping-population + the arb-layer wiring REMAIN; split to the focused residual sub-todo below). (1) ✅ Kalshi —
  `parse_kalshi_sports_fixture(event_ticker, title)` in UAC `canonical/domain/predictions/fixture_parsing.py` →
  `SportsFixtureKey(league, away, home, fixture_date,     start_time)`. **Key design correction (verified vs REAL live
  tickers 2026-06-23):** the per-league team-code split is UNRELIABLE — MLB is 3+3 with an HHMM time
  (`KXMLBGAME-26JUN261910SEACLE`), but **NFL has NO time + VARIABLE 2-3-char codes** (`KXNFLGAME-26SEP14DENKC`=DEN+KC,
  `WASPHI`=WAS+PHI) → a fixed-offset split breaks NFL. So teams are derived from the human `title` "Away vs Home"
  (deterministic across leagues); the ticker supplies league (`kalshi_sports_league_for_ticker`, new public accessor
  over `_KALSHI_SPORTS_PREFIX_TO_LEAGUE`) + date (+ MLB HHMM). Season-futures (`KXNBA-27`/`KXNHL-27`) carry no
  GAME/MATCH token → `None` (NO false pairs). Tennis is a player-pair (`KXATPMATCH-26JUN24HUMBRO`→Humbert vs Brooksby).
  (2) ✅ Polymarket — `parse_polymarket_sports_fixture(league, event_title, slug, resolution_date)` → same
  `SportsFixtureKey`; date from the slug's ISO suffix else the resolution date. (4) ✅ guard —
  `SportsFixtureKey.pairing_key()` is the order-independent `(league, sorted(away,home), date)` join; same-game
  Kalshi↔Polymarket prove-equal (test). 14 regression tests vs REAL samples; UAC QG-green (sentinel bc2be9d3).
  Provenance: operator "parse fixture ids for tennis/nfl/nba/soccer" 2026-06-23. (Supersedes the earlier P2
  per-instrument-pairing todo with the concrete fixture-encoding evidence.)
  - [ ] [DESIGN] P1. **Fixture-pairing RESIDUAL — registry-resolution + mapping-population + arb wiring** (parser
        shipped UAC@3effe2fc): (3a) resolve each `SportsFixtureKey` to a canonical sport fixture via the existing
        **sports domain** registry (api-football fixture*id / odds-api event_id — reuse the
        `ApiFootballAdapter.get_fixtures` cross-ref already in `polymarket/parsing.py::_cross_reference_fixture`) keyed
        on `(league, away, home, date)`; (3b) populate `CanonicalPredictionMarket.mapped_sport_event_id` (IS enum, on
        the sports-prediction instrument record) + `PredictionMarketCrossVenueMapping` (the
        `kalshi_event_ticker`/`polymarket_condition_id`/`api_football_fixture_id` join row); (3c) the arb-layer consumer
        (features/strategy) groups the two venues' instruments by `SportsFixtureKey.pairing_key()` WITHIN the shared
        `SPORTS*{LEAGUE}\_{BETTYPE}`cqg → the same-game arb pair. Needs     a cross-venue team-name canonicaliser (Kalshi "Seattle" ↔ Polymarket "Seattle Mariners"/"Mariners") — extend the     existing`get_canonical_team_for_polymarket`
        maps with Kalshi city/abbrev aliases, validated vs REAL paired samples (no false pairs — operator). Repos:
        unified-api-contracts (mapping populate + team canon) + instruments-service (sports-event link on prediction
        enum) + features-service/strategy-service (arb grouping). Provenance: operator "parse fixture ids" 2026-06-23
        (residual after parser UAC@3effe2fc).

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
- [x] [UAC] P1. **Cross-venue canonicalization BREADTH audit — close the non-crypto gaps (MEASURED 2026-06-24, operator
      "kalshi isn't as verbose as polymarket? sports not just soccer, weather, politics across ALL asset classes")**:
      empirical catalogue snapshot (`instruments-store-pred-prd`, day=2026-06-23): **KALSHI 34 cqg groups / POLYMARKET
      27** (Kalshi is RICHER, not less verbose) but the **arbable SHARED set is only 18, crypto-dominant** — CRYPTO 11
      (BTC/ETH/SOL/XRP/DOGE/BNB/HYPE up-down + 4 ranges), INDEX 3 (DJIA/RUT/SPX), SPORTS **3 (MLB match/spread/total
      ONLY)**, COMMODITY 1 (CRUDE_OIL_PRICE_LEVEL). **The real breadth gaps (single-venue today → NOT arbable):** (a)
      **SPORTS beyond MLB** — `SPORTS_NFL_MATCH`/`SPORTS_WORLD_CUP_MATCH` Kalshi-only, `SPORTS_TENNIS_MATCH`/
      `SPORTS_MLB_NRFI` Polymarket-only; NBA/NHL/soccer-leagues off-season or one-sided → confirm each is liveness vs a
      canonicalization gap. (b) **MACRO prints** — `CPI/FED/GDP/NONFARM_PAYROLLS/PCE/TREASURY` Kalshi-only; Polymarket
      DOES list macro markets → canonicalize the Polymarket side to the SAME groups (genuinely arbable, same print). (c)
      **WEATHER** — `WEATHER_TEMP_DAILY` Polymarket-only; Kalshi trades temp (`KXHIGH*`) → add a shared WEATHER group on
      the Kalshi classifier. (d) **POLITICS/GEO** — see the P2 politics todo above (Kalshi 2049 series uncanonicalized).
      (e) **COMMODITY bet-type MISMATCH** — Kalshi `CRUDE_OIL_PRICE_LEVEL` vs Polymarket `CRUDE_OIL_UP_DOWN_DAILY` =
      same underlying, different bet granularity. **TWO-AXIS DESIGN (operator refinement 2026-06-24 "can still be
      categorised though"):** the cqg currently BAKES bet-type INTO the group name (`CRUDE_OIL_PRICE_LEVEL` vs
      `CRUDE_OIL_UP_DOWN_DAILY`; `BTC_UP_DOWN_DAILY` vs `BTC_PRICE_RANGE_DAILY`), which artificially splits the same
      underlying and HIDES category overlap. Fix = a **2-axis canonical scheme**: (axis-1) UNDERLYING/CATEGORY (`BTC`,
      `CRUDE_OIL`, `CPI`, `WEATHER_TEMP`, `SPORTS_NFL`) — comprehensive cross-venue categorisation REGARDLESS of
      bet-type; (axis-2) BET-TYPE sub-dimension
      (`UP_DOWN`/`PRICE_LEVEL`/`RANGE`/`MATCH`/`SPREAD`/`TOTAL`/`NRFI`/`PER_MONTH`). Overlap is measured at axis-1
      (comprehensive); the arb-PAIRING layer pairs instruments WITHIN an underlying across compatible
      bet-types+settlement. **MEASURED at the underlying level (bet-type stripped, real GCS 2026-06-24):** KALSHI **22**
      underlyings / POLYMARKET **18**; SHARED **12** (BTC/ETH/SOL/XRP/DOGE/BNB/HYPE + CRUDE_OIL [NOW shared — hidden at
      bet-type level] + DJIA/RUT/SPX + SPORTS_MLB). GAPS: KALSHI-only **10**
      (`CPI_PRINT`/`FED_RATE_DECISION`/`GDP_PRINT`/`NONFARM_PAYROLLS`/`PCE_PRINT`/`TREASURY_YIELD` + `NDX` + `EUR` +
      `SPORTS_NFL`/`SPORTS_WORLD_CUP`), POLYMARKET-only **6**
      (`WEATHER_TEMP`/`TRUMP`/`GEO_ISRAEL_IRAN`/`SPORTS_TENNIS` + `ELON_TWEET_COUNT`/`MISC_NOVELTY`). **Approach (no
      false pairs):** per underlying, probe BOTH venues' live series, confirm same real-world settlement, add/align the
      axis-1 categorisation (so Polymarket macro/weather + Kalshi temp/NFL all categorise even where bet-type differs);
      the arb engine decides bet-type compatibility downstream. Repos: unified-api-contracts (classifiers +
      canonical_groups, likely an explicit `underlying` field separate from `bet_type`) + instruments-service.
      Provenance: operator cross-asset-breadth Q + two-axis refinement 2026-06-24 (measured overlap, real GCS). ✅
      UAC@1aaa5230 — all CODE gaps closed: (a/c-liveness) Sports NFL/World Cup appear one-sided in June — code routes
      Kalshi `KXNFL*GAME*` → NFL_MATCH correctly; Polymarket NFL absent in off-season (not a classification gap).
      (b-already-done) Polymarket macro already routes via `(MACRO,"CPI")`/ `"FED_FUNDS"` etc. in classifiers.py to the
      shared groups — both sides were wired. (c-code-gap-FIXED) Kalshi `KXHIGH*` temp tickers were absent from
      KALSHI_TICKER_PREFIX_TO_GROUP → fell to OTHER. Added `"KXHIGH": WEATHER_TEMP_DAILY`. Both venues now share the
      group at axis-1. 73 tests pass. Politics P2 gap remains (its own open todo). 2026-06-26.
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

- [ ] [SCRIPT] P1. **Polymarket BATCH book_snapshot_5 backfill — UAC expected-coverage gap FIXED, VM RUNNING
      (2026-06-26)**: UAC fix shipped `1596d4f9` (2026-06-23 18:20Z); current MTDS tarball built 2026-06-26T14:00:57Z at
      sha `5e52439d` includes the UAC fix. Backfill VM `mtds-prediction-polymarket-20260626-154329` launched for
      2026-06-20..22 with `DATA_TYPES=book_snapshot_5`. **REMAINING: verify VM exits 0 + manifest shows captured
      book_snapshot_5 rows for those dates.** Repo: unified-api-contracts (FIXED uac@1596d4f9) + deployment-service (VM
      running 2026-06-26). Provenance: autonomous catalogue/backfill session 2026-06-23 / VM launched 2026-06-26.
- [x] ✅ [SCRIPT] P2. **Kalshi RECENT-window (2026-06-20..22) batch trades 0-capture — 2-stage IS-enumeration gap +
      cqg-path fallback (DISCOVERED 2026-06-23 / FIXED 2026-06-26)**: (a) removed the dead
      `instrument_availability/by_date/day={date}/venue=KALSHI` fallback from KalshiAdapter (IS now writes cqg-first
      partitioning; day-first path never existed for Kalshi → always returned empty dict silently) — now relies solely
      on the primary `market_lifecycle/by_canonical_group/` store with a WARNING log when empty; tests updated (16+30
      unit tests green). mtds@d6edd704 (QG-green 119s). (b) IS enumeration VM `instr-backfill-pred-20260621` launched
      for 2026-06-20..21 (market_lifecycle data exists for 06-22+ but was absent for 06-20/21) — after VM completes,
      Kalshi RECENT-window MTDS backfill (`--venue KALSHI 2026-06-20 2026-06-22`) to be launched. Repo:
      market-tick-data-service@d6edd704 + instruments-service (VM). Provenance: autonomous catalogue/backfill session
      2026-06-23 / fix 2026-06-26. (Composes with the line-339 Kalshi-historical residual.)

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
- [~] [SCRIPT] P1. **cqg partition-completeness — BATCH re-classification re-walk** — **script bug FIXED (mtds@24db3f16,
  ✅); `--apply` operational run REMAINS (now safe, non-corrupting).** Shipped the venue-aware classifier routing:
  `compute_object_atom(..., venue)` routes KALSHI tickers via `classify_kalshi_to_canonical_group(ticker=cid)` (one
  object = one ticker = one constant group), POLYMARKET via the tuple path; 2 regression tests
  (`KXCPI→CPI_PRINT_PER_MONTH`, `KXMLBGAME→SPORTS_MLB_MATCH`, NOT OTHER); 51/51 rebuild tests + mtds QG green.
  **REMAINING (operational):** run `--apply --venue KALSHI` over the dates where Kalshi TICK parquets actually exist
  (the bulk-seed window — a 2026-05-01..03 dry-run showed `objects:0`, so find the seeded dates first), confirm
  non-OTHER via dry-run, THEN `--apply`. NOTE (ties to P0 43d): the re-walk's CF-11 re-emit path preserved **116,192
  KALSHI SOURCE_RETURNED_ZERO** as empty_confirmed with "no parseable bounds / out-of-window" — these Kalshi markets
  lack `available_from/to` (the SAME P0 lifecycle gap), so they can't be lifecycle-reclassified until KALSHI bounds
  populate (P0 43d). Repo: market-tick-data-service. **ORIG BLOCKER (now fixed):** `rebuild_prediction_manifest.py` was
  POLYMARKET-ONLY (DISCOVERED via dry-run 2026-06-24, before any write). A `--venue KALSHI     --dry-run` over
  2025-05-01..2026-06-24 (read-only, safe) found the re-walk classifies EVERY Kalshi market with
  `classify_polymarket_to_canonical_group` (line 365; the line-498 comment literally says "polymarket-cqg specific") →
  Kalshi tickers mis-bucket to OTHER (probed: the script logs `KXCPI-25MAY-T0.2` → OTHER, but the FIXED
  `classify_kalshi_to_canonical_group(ticker="KXCPI-25MAY-T0.2")` correctly returns `CPI_PRINT_PER_MONTH`; same for
  `KXMLBGAME→SPORTS_MLB_MATCH`, `KXBTCD→BTC_UP_DOWN_DAILY`, `KXFED→FED_RATE_DECISION_PER_FOMC`). **So a
  `--apply     --venue KALSHI` would WRITE all-OTHER cqg bundles → CORRUPT the manifest (regression vs the catalogue cqg
  fix). Do NOT run `--apply` until the script is venue-aware.** **FIX (in scope, mtds):** thread `venue` into
  `compute_object_atom` + route the classify call — `classify_kalshi_to_canonical_group(ticker=cid)` for KALSHI vs
  `classify_polymarket_to_canonical_group(...)` for POLYMARKET (the Kalshi classifier keys on the TICKER, which IS the
  Kalshi condition_id/`cid`); add a regression test (KXCPI/KXMLBGAME → real groups, not OTHER); then dry-run to confirm
  non-OTHER, THEN `--apply` (local or VM ~5000s). Re-reads existing tick parquets; NOT a tick migration. Repo:
  market-tick-data-service (`scripts/rebuild_prediction_manifest.py`). Provenance: operator partition-completeness Q
  2026-06-23 + autonomous dry-run discovery 2026-06-24.
- [ ] [SCRIPT] P2. **cqg partition-completeness — recent-window catalogue re-enumeration**: the cqg-partitioned
      `instrument_availability` catalogue is refreshed for 2026-06-23 only (34 groups verified). Re-enumerate the recent
      enumerated window (e.g. 2026-06-20..22) with the fixed classifier so those dates' catalogue also carries real cqg
      (rides the 1.2 Kalshi recent-window enumeration). Deep history is the bulk-tick-seed (no per-date catalogue) →
      covered by the BATCH re-walk above. Repo: instruments-service. Provenance: operator partition-completeness Q
      2026-06-23.

### 2026-06-26 (autonomous /autonomous) — Kalshi fallback path fixed; IS enum + Polymarket book backfill VMs launched; stale-image alert shipped

**Shipped this session (continuation of prior context):**

4. ✅ [SCRIPT] P1 — UAC fee lift (shipped prior session): `KALSHI_FEE_COEFF=0.07`, `POLYMARKET_FEE_FRACTION=0.0` in
   UAC@4601e242. Plan checkbox flipped prior context.
5. ✅ [OPS] P1 — `features-service-events` PubSub IAM: tf file for topic + default-compute-SA + t1_batch-SA publisher
   grants — deployment-service@7bb33c1. Plan checkbox flipped prior context.
6. ✅ [UAC] P1 — KXHIGH Kalshi weather prefix → WEATHER_TEMP_DAILY: UAC@1aaa5230. Plan checkbox flipped prior context.
7. ✅ [SCRIPT] P2 — Kalshi IS fallback path removed: the dead `instrument_availability/by_date/day={date}/venue=KALSHI`
   fallback (path never existed; IS writes cqg-first since 2026-06-22) is removed from
   `KalshiAdapter._load_lifecycles_from_gcs`. Now relies solely on `market_lifecycle/by_canonical_group/` primary with
   WARNING log when empty. Tests updated (30 unit tests green). Also fixed pre-existing test isolation bug in
   `test_rebuild_tradfi_manifest.py`. mtds@d6edd704, QG-green 119s.
8. [INFRA] — IS Prediction enumeration VM `instr-backfill-pred-20260621` launched for 2026-06-20..21 (fills gap in
   `market_lifecycle/by_canonical_group/` data that was absent pre-06-22). After VM completes → launch Kalshi
   RECENT-window MTDS backfill for 2026-06-20..22.
9. [INFRA] — Polymarket book_snapshot_5 batch backfill VM `mtds-prediction-polymarket-20260626-154329` launched for
   2026-06-20..22 (the pre-live-VM window). Tarball sha `5e52439d` includes UAC fix `1596d4f9`. Verify once VM exits.
10. ✅ [ALERTING] — `DP-VM-007 DP_CLOUD_RUN_STALE_IMAGE` event type + alerting rule shipped: UAC@c6a2fede + UTL@d9d344a9
    add the stale Cloud Run image alert (WARN/FILE_ISSUE for #data-pipeline-alerts Slack channel). Addresses operator
    request to ensure all deployments are alert-covered when running stale code.

**Open live deployments status (2026-06-26 ~16:30 UTC):**

- `prediction-arb-detector-20260624-154110` — RUNNING (arb detector, 2d uptime)
- `prediction-live-polymarket-book-snapshot-5-20260623-130258` — RUNNING (3d+)
- `prediction-live-polymarket-trades-20260624-131355` — RUNNING (2d+)
- `prediction-live-kalshi-book-snapshot-5-20260623-211454` — RUNNING (3d+)
- `prediction-live-kalshi-trades-20260624-131340` — RUNNING (2d+)
- `mtds-prediction-polymarket-20260626-154329` — RUNNING (book_snapshot_5 backfill 2026-06-20..22)
- `instr-backfill-pred-20260621` — RUNNING (IS enumeration 2026-06-20..21)

**Next actions:**

- Verify IS enumeration VM completes + `market_lifecycle/by_canonical_group/` has day=2026-06-20/21 data
- Launch Kalshi RECENT-window MTDS backfill after IS VM completes
- Verify Polymarket book_snapshot_5 backfill VM exits 0 + manifest shows captured rows
- Check live alerts + deadman coverage per operator request (stale-image alert shipped; scope remaining monitors)
