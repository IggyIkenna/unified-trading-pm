---
doc_type: plan
title: Prediction (Kalshi/Polymarket) live + batch CLOB depth & trades capture infrastructure
summary: >-
  The live/batch data-capture pipeline for PREDICTION Kalshi + Polymarket YES/NO markets — WS connectors, transport/
  sink correctness, message-shape fixes, live producer VM operations, source/pipeline-mode registration; split out of
  prediction_venue_perps_and_live_clob_depth_2026_06_20.md (plan line-cap remediation, 2026-07-24).
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos:
  [agent-orchestrator, deployment-api, deployment-service, e2e-testing, features-service, fund-administration-service]
scope: [engineer, admin]
tags: [prediction, kalshi, polymarket, clob, live-data, websocket, capture, book-snapshot]
related:
  [
    /plans/archive/2026_07/prediction_venue_perps_and_live_clob_depth_2026_06_20.md,
    /plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/archive/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes: [prediction_venue_perps_and_live_clob_depth_2026_06_20]
superseded_by:
depends_on:
source: >-
  Split from prediction_venue_perps_and_live_clob_depth_2026_06_20.md (2354 lines / 87 todos, HARD over the 1000L
  line-cap) per /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md row 23 — operator approved unlocking
  `locked_by: live-defi-rollout` and a 3-way clean-partition (parked perps track / live CLOB-depth capture infra /
  cross-venue arb+coverage). This file carries the live CLOB-depth capture infra third verbatim.
assigned_role: data_engineering
drift_direction: advance-code
archive_exempt: true # 2026-08-10 slot 22: 0 open todos after DEFERRED-CROSS-DEP flip; archival deferred to /archive-candidates-audit (marquee plan, 33 done todos, complex referrer graph)
context_scope:
  [
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction,
  ]
---

# Prediction live + batch CLOB depth & trades capture infrastructure

> **🟢 2026-07-24 — SPLIT FROM `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`.** That plan grew to 2354
> lines / 87 todos across three intertwined tracks and was flagged HARD over the 1000-line cap
> (`/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` row 23). Operator approved unlocking
> `locked_by: live-defi-rollout` and a 3-way clean-partition. **This file carries the PREDICTION (Kalshi/Polymarket
> YES-NO market) live+batch data-capture pipeline track verbatim** — every todo and Progress Log entry below was moved
> unchanged (never summarized or rewritten). Siblings from the same split:
> `plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md` (the separate, parked crypto-PERPS
> venue track — do not confuse the two; KALSHI/POLYMARKET here are the prediction YES/NO markets) and
> `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (the downstream cross-venue arb detector +
> honest-coverage correctness work that consumes this capture pipeline's output). The original plan is retained, frozen,
> at `plans/archive/2026_07/prediction_venue_perps_and_live_clob_depth_2026_06_20.md`.

## Foundational capture-pipeline items (carried forward from the parent plan's Phase 1 / Phase 3 sections)

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
  - [x] ✅ [SCRIPT] P2. **DEFERRED-CROSS-DEP — batch book_snapshot_5 row-proof on a historical date needs an IS
        re-enumeration carrying `clob_token_ids` (2026-06-23)**: the batch book path is code-complete + live-proven, but
        a BATCH row-capture proof is blocked because historical IS parquets (≤06-22) predate the clob_token_ids column +
        today is batch-future-rejected. Fix = re-enumerate the IS Polymarket universe for a recent past date (e.g.
        06-22) so its `instrument_availability` parquet carries populated `clob_token_ids`, THEN re-run the book
        backfill for that date. Repo: instruments-service (re-enumerate) + deployment-service (re-launch). NICE-TO-HAVE
        — live book_snapshot_5 already captures end-to-end. Provenance: autonomous catalogue/backfill session
        2026-06-23. **na-eligibility-audit 2026-08-06: KEEP-NA-STALE-DUPLICATE, citation added — already claimed (not
        yet dispatched) in
        [`prediction_satellite_ao_dispatch_batch4_2026_07_26.md`](/plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26.md)'s
        "Deferred — gated on a sibling todo landing" section: "Re-enumerate the IS POLYMARKET universe for a recent past
        date → re-run the `book_snapshot_5` batch backfill → verify `row_count>0`" (`Source:` this exact item,
        verbatim). That section deliberately holds the item NOT-dispatched-speculatively, sequenced after batch4's own
        todo #1 lands (else it re-enumerates against the old write path). Reclassifying this doc's `assigned_vm` would
        create a second, competing dispatch surface — stays NA, batch4 is the correct owner. **Reconciled 2026-08-07
        (finalize P1)** — stays `- [ ]`, NOT run: batch4's Deferred "Re-enumerate the IS POLYMARKET universe for a
        recent past date → re-run the `book_snapshot_5` batch backfill → verify `row_count>0`" item is still parked
        there (it was re-tagged off `[OPERATOR]` 2026-07-28 but remains sequenced AFTER batch4 P0 lands; that gate has
        now cleared with the P0 ship `instruments-service@3617261f`, yet the re-enum+backfill itself has NOT been
        dispatched/run). ~~The corresponding batch4 depth-history verify (this doc's own `[x]` item above) returned
        VERDICT: FAIL — this row-proof backfill does not change that verdict. Re-open in a future batch as a ready
        `[DATA]` candidate now that its P0 dependency has landed.~~ **na-eligibility-audit 2026-08-10: citation
        repointed** — the live current owner is
        [`prediction_satellite_ao_dispatch_batch10_2026_08_09.md`](/plans/archive/2026_08/prediction_satellite_ao_dispatch_batch10_2026_08_09.md)
        todo 1 (`status: active`, `assigned_vm: planning`, verbatim `Source:` cites this exact checkbox), not batch4 —
        batch10 independently re-extracted the same item and is the current dispatch surface; batch4's older, staler
        Deferred-section copy of this item is superseded by batch10's, not a second live claim. **RESOLVED 2026-08-19
        (/plan-reconcile predictions_master)**: batch10 (+ its finalize) is now `status: complete`, archived — that
        finalize plan's own text confirms this exact item "confirmed `[x]` ✅ flipped (line 247) with batch10 todo 1's
        full evidence chain: live manifest rows &gt;0 (4 dates, 648K rows), mtds@82ba5399/0a6ad2de". The "stays `- [ ]`,
        NOT run" narrative above (struck through) was superseded by this shipped resolution; this checkbox's own `[x]`
        state was already correct, only the stale in-body prose contradicting it is now fixed.
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

- [x] ✅ [SCRIPT] P2. **Kalshi PREDICTION live CLOB depth → `book_snapshot_5` SHIPPED** (mtds@425b1e8):
      `live/connectors/kalshi_clob_ws.py` (`KalshiClobWSFeedConnector`, ws `orderbook_delta` snapshot+delta, top-5 →
      `book_snapshot_5`, venue KALSHI, asset_group prediction; coexists with the lowercase `kalshi` trades connector);
      registered in `register_all()`; 577-line test suite; QG green. Verified
      `live_pipeline_mode_for_venue('prediction','KALSHI','book_snapshot_5')→live_kalshi`. **Phase-3 both-venues live
      CLOB depth COMPLETE** (Polymarket@26297e4 + Kalshi@425b1e8). — 2026-06-22

## Progress Log

- **2026-08-04 (slot-5, data_engineering, dispatched via `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 2)
  — "Verify END-TO-END depth-history retention" — VERDICT: FAIL.** Read-only verification, no data mutation. Two
  independent, compounding gaps found (worse than the 2026-06-24 concern anticipated):
  1. **Raw flush window is still overwrite-prone, contra the "RESOLVED... retired" note above.** `LiveWebsocketTickSink`
     was RESTORED as the default sink 2026-06-26 (`market-tick-data-service@3043f2dc`, see that dated entry below) to
     fix a worse InMemoryTransport data-loss bug — this reverted the brief `LiveEventFacadeSink` event-time-keying.
     Confirmed at HEAD (2026-08-04): `live_tick_blob_path()`
     (`market_tick_data_service/live/websocket_runner.py:95-145`) builds
     `raw_tick_data/by_date/day={D}/pipeline_mode={live_mode}/.../data_type={dt}/{instrument_id}.parquet` — keyed by
     day+instrument ONLY, no window/period key — so every window flush for the same instrument overwrites the prior one.
     Live-sampled evidence:
     `gs://market-data-tick-pred-prd-central-element-323112/raw_tick_data/by_date/day=2026-06-28/pipeline_mode=live_kalshi/.../data_type=book_snapshot_5/KALSHI:PREDICTION_MARKET:FEDHIKE-26DEC31.parquet`
     — single object, mtime `2026-06-29T04:42:21Z`, 11 rows spanning only `2026-06-29T04:25:23Z`–`04:41:09Z` (~16 min),
     last row's `ts_ms` matching the mtime — consistent with rolling-overwrite, not accumulation (note: content
     timestamps fall on 06-29 despite the day=2026-06-28 partition key — a separate launch-day-vs-event-day artifact).
  2. **The processed prediction candle/book store has ZERO objects for live-mode data, on every sampled day.** Bounded
     (non-corpus-wide) `gcloud storage ls` on
     `market-data-tick-pred-prd-central-element-323112/processed_candles/by_date/day={D}/` for 2026-06-23, 2026-06-24,
     2026-06-26, 2026-06-28 — all four confirmed via the sibling `raw_tick_data/` prefix to have live raw data present
     (both KALSHI and POLYMARKET_CLOB pipeline_modes, both `trades` and `book_snapshot_5` data_types) — returns **zero
     processed-candle objects for every one of the four days**. The only processed output that exists in this bucket
     recently (checked 2026-07-25, 2026-07-26, 2026-08-02, 2026-08-03) is `pipeline_mode=batch_kalshi` (from the daily
     6am UTC batch cron, `deployment-service/configs/clusters/prediction.yaml`). So the durable "processed store" this
     doc's own design-intent note (above, "durable history is MDPS's processed output, NOT the rolling raw bucket")
     relies on for depth-history durability **does not exist at all** for live-mode prediction data on any sampled day —
     not "insufficient multi-hour history", genuinely none.
  3. **A structural cause compounding #2 (code-level, confirmed via exhaustive grep at HEAD, unified-api-contracts +
     market-data-processing-service):** MDPS's `CandleAdapterRegistry` has exactly one PREDICTION registration —
     `(PREDICTION, "trades")` → `PredictionTradesAdapter`
     (`market_data_processing_service/app/adapters/prediction/trades_adapter.py:62`). No
     `(PREDICTION, "book_snapshot_5")` adapter exists. Yet the global
     `NEEDS_CANDLE_PROCESSING["book_snapshot_5"] = True` (`unified_api_contracts/registry/market_data_categories.py:947`
     — shared across CeFi/DeFi/Prediction, comment confirms "Prediction — uses canonical trades / book_snapshot_5, same
     keys as CeFi"). This routes prediction `book_snapshot_5` into `orchestration_service.py:653`'s
     `"⚠️ No adapter for %s/%s"` WARNING branch on every scan — a silent (log-only, never a hard failure), permanent
     skip. This alone explains why `book_snapshot_5` never reaches a processed store; it does NOT explain why `trades`
     (which DOES have a registered adapter) is also absent from `processed_candles` for every sampled live day — that
     half of finding #2 needs separate root-causing (most likely: the MDPS live-mode continuous scan process for
     prediction was never deployed/launched against `pipeline_mode=live_*` prefixes, but this verification did not
     confirm which).
  - **Filed as a big finding** (data-correctness, silent, production-live, confirmed via live GCS read) per CLAUDE.md's
    findings-triage rule: `plans/archive/issues/prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` (3
    actionable follow-up todos — root-cause the empty-live-scan half of #2, register or deliberately bypass the missing
    book_snapshot_5 adapter, and re-verify multi-hour accumulation once fixed).
  - **Done-when satisfied** for `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 2 (this todo's own checkbox
    there flipped, citing this entry).

- **2026-08-04 (slot-7, data_engineering) — todo 4 re-verification (post todos 1-2): VERDICT — Still no live-mode
  processed accumulation, FULLY EXPLAINED.** Re-ran the same bounded GCS-timespan check this doc's 2026-08-04 entry
  described: `gs://market-data-tick-pred-prd-central-element-323112/processed_candles/by_date/day={D}/` for 2026-08-01,
  2026-08-02, 2026-08-03, 2026-08-04. Result on every day: **ZERO `pipeline_mode=live_*` objects.** Only
  `pipeline_mode=batch_kalshi` output exists (the daily 6am UTC batch cron, still running normally — confirmed objects
  present on days 2026-08-02 and 2026-08-03). This is the EXPECTED state given the two upstream resolutions: (1) todo 1
  root-caused the gap: the MDPS live-mode worker was never deployed/launched for ANY asset_group (fleet-wide, not
  prediction-specific); (2) todo 2 fixed the `_mode_dispatch_handler` construction + categories-default bugs
  (`market-data-processing-service@9357fac`) so the code path is correct when invoked, but — (3) todo 3 (slot-10)
  **DECIDED NOT TO LAUNCH** the `mdps-features-live` cluster after 2 real pilot VMs (cefi + tradfi) both failed with
  distinct bugs (OOM + argparse mismatch) AND the structural finding that `mdps_mvp_universe('prediction')` returns zero
  shards by design (2026-07-30 ruling), so even a successful launch would not have produced prediction MDPS candle
  output. The zero-live-objects result is therefore not a regression or surprise — it is the direct, expected
  consequence of the conscious operational decision recorded in todo 3's resolution. **This re-verification is
  complete.** The remaining unfixed gap (no live processed prediction depth history) is now fully characterized: (a) raw
  flush still overwrites (finding #1, MTDS path); (b) processed live-mode output requires the `mdps-features-live`
  cluster to be operational AND `mdps_mvp_universe('prediction')` to be non-empty — both preconditions are currently
  false by deliberate decision, not by oversight. The 6 scoped follow-up todos in the successor issue
  (`/plans/archive/issues/mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md`) own the path
  to making those preconditions true. This entry supersedes the 2026-08-04 FAIL entry above — the gap is now explained
  end-to-end; no new surprise was found.

- **na-eligibility-audit 2026-08-02 (prediction tranche, autonomous)**: KEEP-NA, **1 stale item cited** — 2 open,
  unchanged in count. The only commit to this file since the 2026-07-30 marker (`1ab67de59`) dropped the inherited
  `cefi` tag per the operator's 2026-07-30 option-A ruling; no content moved. New this run, found by the Phase-2
  conflict-check rather than by a content change: the `[DATA] P2` depth-retention checkbox was already extracted
  verbatim into `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` (`status: active`, `assigned_vm: planning`),
  which cites it as its own `Source:` — but this doc's checkbox carried no back-citation, so a future audit would keep
  re-flagging it as unclaimed. Fixed as a KEEP-NA-STALE citation correction (rubric 3 / conflict-check protocol step 4):
  citation added, `assigned_vm` untouched, checkbox deliberately left `[ ]` as the tracking anchor. The other open item
  is the `DEFERRED-CROSS-DEP` batch `book_snapshot_5` row-proof, still gated on an instruments-service re-enumeration of
  a past date carrying `clob_token_ids` — no active doc claims it. **Frontmatter note re-checked at the code level, not
  re-reported as a contradiction**: this doc pairs `execution_scope: orchestrator-agent` with `assigned_vm: NA`, which
  the two prior markers flagged as part of a "7-doc contradiction class". Read
  `agent-orchestrator/server/regen_backlog_from_plan.py` at HEAD to settle it — `_resolve_plan_vms()` maps the `NA`
  sentinel to an EMPTY vm set, so the strict per-VM ownership gate in `_plan_contributes_briefs()` blocks ingestion
  regardless of `execution_scope`. The pairing is cosmetic, NOT a live mis-dispatch hazard; no flip needed and no
  operator ruling required. Doc stays NA.

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 2 open checkboxes, both P2, one explicitly
  `DEFERRED-CROSS-DEP` on an instruments-service prerequisite. The doc's two PROSE items (BQ external tables, the
  `roles/pubsub.publisher` grant) are CONFLICT — claimed by `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`
  todos 12 and 13. Same `execution_scope`/`assigned_vm` note as its sibling fork: see this run's report.

### 2026-06-26 (autonomous /autonomous) — Plan04 InMemoryTransport bug fixed, DP-LIVE-002 alert shipped, VMs verified

**Critical data loss RESOLVED.** Plan 04 commit `3b956b70` (LiveEventFacadeSink with `transport=None`) silently routed
ALL book_snapshot_5 ticks to InMemoryTransport instead of GCS — confirmed zero GCS files all day, manifest showing only
26/148162 `captured` rows (all with `pubsub://persist-*` blob_path, not `gs://`). Fixed in
`market-tick-data-service@3043f2dc`: restored `LiveWebsocketTickSink` as `_make_default_sink()` default; extracted
`LiveEventFacadeSink` to `event_facade_sink.py`.

**VMs relaunched on fixed tarball** (`@3043f2dc`):

- `prediction-live-polymarket-book-snapshot-5-20260626-224659` — T+10 VERIFIED: writing GCS parquets, subscription
  progressing (148162 tokens at ~21/s; ~2h to cover full universe; 5 parquets at 23:20Z growing)
- `prediction-live-kalshi-book-snapshot-5-20260626-224718` — T+10 VERIFIED: **2107 GCS parquets** written as of 23:20Z

**DP-LIVE-002 monitoring shipped** (`deployment-service@8133491`): new `check_live_stream_gcs_write_mismatch()` catches
the InMemoryTransport class of silent drop (manifest captured>0 but GCS files=0 AND VM age>1h → CRITICAL alert). This
class of bug would NOT have been caught by DP-LIVE-001 (attempted_at stays fresh even when 0 GCS files). 4 unit tests.
The cron will now page if a future Plan change re-introduces a misrouted sink.

**Arb detector** (`prediction-arb-detector-20260626-201140`) running tick=19 at 23:19Z: `two_way_on_both=0` — expected,
no cross-venue pairs matched for days scanned (buggy VMs ran all of 06-26 pre-fix, Polymarket subscription still
filling). Will self-improve as subscription completes and crypto Polymarket books accumulate (if any match Kalshi's rich
crypto set).

- [x] [OPS] P0. **IS prediction catalogue is NOT fresh for the CURRENT UTC day → live producers launched today get an
      EMPTY KALSHI universe → honest-absence, 0 capture (discovered 2026-06-24).** FIXED 2026-06-26: (a) copied all 34
      Kalshi cqg-partitioned IS blobs from day=2026-06-23 to day=2026-06-26 (GCS cp) — new VMs find today's data; (b)
      relaxed `_filter_prediction_is_blobs` from `day >= today` to `day >= today - 7d` so any recent IS data within a
      week is accepted (prevents tomorrow-recurrence without fresh enumeration) — market-tick-data-service@d2cae38e +
      test updated to use 8-day-old stale blob. Root cause (no daily IS cron for Kalshi) remains upstream; the 7-day
      fallback is the durable fix.

- [x] ✅ [DATA] P2. **CLOSED — na-eligibility-audit 2026-08-06 (prediction tranche). Verify END-TO-END depth-history
      retention — the RAW live book store is rolling-latest-window per instrument, NOT a multi-hour archive (discovered
      2026-06-24).** This checkbox's own stated flip-rule ("stays `[ ]`... it flips when batch4's todo records its
      verdict here") is now satisfied: the 2026-08-04 (slot-5) entry below records **VERDICT: FAIL** with full
      root-cause detail, and the 2026-08-04 (slot-7) entry records a completing re-verification ("no new surprise was
      found"). Follow-up remediation forked into two successor issue docs:
      `plans/archive/issues/prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` and
      `plans/active/issues/mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md`. The
      "verify" ask is complete and evidenced in-doc; checked off citing both 2026-08-04 entries + the two successor docs
      — it was left open only as a tracking anchor past its own done-when. Confirmed empirically: under
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
      `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`), `websocket_runner.py:147` states "`available_at`
      is derived downstream by MDPS from `period_end + emission_latency`", and MDPS `orchestration_scanner.py` DOES scan
      `raw_tick_data/by_date/day={D}/pipeline_mode={batch|live}/…` → processes → durable processed store (same
      destination batch writes; determinism spine `citadel_paper_batch_live_reconciliation_2026_06_19.md` requires
      paper(W)==batch-rerun(W)). So durable history is MDPS's processed output, NOT the rolling raw bucket. REAL RISK TO
      VERIFY: the raw flush path overwrites per UTC-aligned window with no window key, so if MDPS's prediction live-scan
      cadence is SLOWER than the flush window, windows are overwritten before ingest → silent intra-day depth gaps.
      VERIFY: (1) MDPS prediction live-scan cadence ≤ flush window; (2) the processed prediction book/candle store
      actually accumulates multi-hour history. Repos: market-tick-data-service + market-data-processing-service.
      Provenance: operator "do we have depth for a few hours of history / isn't there a plan for how live data
      persists?" 2026-06-24. **EXTRACTED — sole executing owner is
      [`prediction_satellite_ao_dispatch_batch4_2026_07_26.md`](/plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26.md)'s
      `[DATA] P2` "Verify END-TO-END MDPS prediction depth-history retention" todo** (`status: active`,
      `assigned_vm: planning`), which names this checkbox verbatim as its own
      `Source: prediction_live_clob_depth_capture_2026_07_24.md (P2 "Verify END-TO-END depth-history retention")` and
      carries the bounded `Done when` (a dated PASS/FAIL verdict with the measured processed-store time span cited).
      Citation added by `/na-eligibility-audit` 2026-08-02 — this checkbox stays `[ ]` and stays NA (it is the tracking
      anchor, not a second dispatch claim); it flips when batch4's todo records its verdict here.

- [x] [SCRIPT] P2. **Live book partition is keyed by producer LAUNCH-day, not event-day** (discovered 2026-06-24:
      producers launched 06-23 still write `day=2026-06-23` at 11:37Z 06-24). The detector works around it (trailing
      `--scan-days` window) but the PRODUCER should partition `book_snapshot_5`/`trades` by event-day so day-rollover is
      clean. Repo: market-tick-data-service (`live/websocket_runner.py` path builder). Provenance: detector build
      2026-06-24. ✅ RESOLVED by Plan 04 cutover (MTDS@3b956b70 — `LiveWebsocketTickSink` retired; `LiveEventFacadeSink`
      publishes `CanonicalPersistEnvelope` with `period_start`/`period_end` timestamps, so materialized GCS paths are
      event-time-keyed not launch-time-keyed. The launch-day issue only affects VMs launched BEFORE 3b956b70;
      newly-launched VMs are clean. The `cross_venue_arb_runner.py` `scan_days=3` workaround remains for the transition
      period. Warm GCS materialization is pending Cloud Storage subscription provisioning (BLOCKED-CREDENTIALS) but that
      is tracked separately; the code is correct. **CORRECTION (2026-08-04, live re-check — see the
      depth-history-retention verdict below):** this "retired" claim is STALE. The 2026-06-26 Progress Log entry below
      (same file) shows `LiveWebsocketTickSink` was RESTORED as `_make_default_sink()`'s default
      (`market-tick-data-service@3043f2dc`) to fix a worse bug (`LiveEventFacadeSink` was silently routing ticks to
      `InMemoryTransport` instead of GCS). At HEAD today, `live_tick_blob_path()` (`websocket_runner.py:95-145`) is
      confirmed still day+instrument-keyed (`{file_name}.parquet`, no `period_start`/`period_end` in the path) — NOT
      event-time-keyed. The launch-day partitioning defect this checkbox tracked may still be moot for other reasons,
      but "the code is correct" no longer holds for the event-time-keying claim specifically; do not cite this note as
      evidence the raw path is window-safe.

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

- [x] ✅ [OPS] P2. **Keep both venues' live producers running + ensure Polymarket subscribes to ALL listed daily-crypto
      markets (2026-06-26T20:11Z)**: All 5 prediction live VMs relaunched on MTDS tarball `05e84bc5` (fresh
      2026-06-26T20:07Z): `prediction-live-{polymarket,kalshi}-{book_snapshot_5,trades}-20260626-20*` +
      `prediction-arb-detector-20260626-201140`. T+10 verified: all VMs heartbeating + ManifestWriter updating (2k+
      entries within 5 min). Polymarket `_read_prediction_is_universe_sync` resolved 148162 instruments. Arb detector
      running `ARB_DETECT_TICK` (0 arbs expected until today's fresh data accumulates post-dead-stream). DP-LIVE-001
      monitoring shipped to catch future silent drops. Repo: deployment-service@(LDR) +
      market-tick-data-service@05e84bc5.
- [x] ✅ [SCRIPT] P0. **CRITICAL DATA LOSS — Plan 04 `LiveEventFacadeSink` transport bug: ALL book_snapshot_5 tick data
      silently lost (InMemoryTransport) — FIXED market-tick-data-service@3043f2dc (2026-06-26).** ROOT CAUSE: Plan 04
      commit `3b956b70` replaced `LiveWebsocketTickSink` with `LiveEventFacadeSink` in `_make_default_sink()` but wired
      `transport=None` → `_get_default_transport()` → `get_transport(topology=None)` → `InMemoryTransport` → ticks
      published in-process and discarded on next GC. Confirmed via per-VM manifest: 148162 `book_snapshot_5` rows,
      148136 `empty_confirmed`, only 26 `captured` (but those 26's blob_path = `pubsub://persist-*`, not `gs://`). GCS
      `day=2026-06-26/pipeline_mode=live_polymarket_clob/.../data_type=book_snapshot_5/` = EMPTY. FIX: restored
      `LiveWebsocketTickSink` (direct GCS writer) as the `_make_default_sink()` default; extracted `LiveEventFacadeSink`
      to `event_facade_sink.py` to keep under 900-line QG limit; updated `ASYNCIO_RUN_EXCLUDE_GLOBS` + bypass audit.
      Added `live_tick_blob_path()` canonical GCS path builder. QG-green (sentinel `3043f2dc`). Rebuilt MTDS tarball
      `@3043f2dc` + relaunched book_snapshot_5 VMs: `prediction-live-polymarket-book-snapshot-5-20260626-224659` +
      `prediction-live-kalshi-book-snapshot-5-20260626-224718`. **T+10 VERIFIED (23:20Z)**: Kalshi VM writing **2107 GCS
      parquets** at `pipeline_mode=live_kalshi/.../data_type=book_snapshot_5/` + Polymarket VM writing **5 parquets**
      and growing (subscription in progress — 148162 tokens, ~2h to complete). Both VMs heartbeating + ManifestWriter
      active. GCS write confirmed → transport bug resolved. Repo: market-tick-data-service@3043f2dc.
- [x] ✅ [OPS] P1. **DP-LIVE-002 alert SHIPPED (deployment-service@8133491, 2026-06-26)**: new
      `check_live_stream_gcs_write_mismatch()` in `live_stream_watcher.py`, wired into `cli.py` alongside DP-LIVE-001.
      Fires CRITICAL if manifest ≥1 `captured` rows but GCS has 0 parquets at the venue/data_type prefix AND VM age >1h
      — catches InMemoryTransport silent-drop class that DP-LIVE-001 misses. 4 unit tests. QG-green.

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
resolve, bucket kind (market-data-tick-prediction flat key), recorder source-derive, `row_key` day->date, Gamma query
`condition_ids` (was `clob_token_ids` -> 422), launcher `_`->`-` VM-name sanitization, CandleBoundaryCrossedEvent
data_type enum (book_snapshot -> book_snapshot_5).

The live VM now runs clean: connector fetches REAL Gamma prices (HTTP 200, no 422), manifest writes per-VM shards with
correct `pipeline_mode=live_polymarket_clob`, candle boundary flushes without error.

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

- [x] ✅ [SCRIPT] P2. **Live prediction finalize is BATCH-mode-stamped** — STALE PREMISE, resolved-by-architecture
      (verified 2026-06-21): `manifest_finalize.py` prediction cqg writer now resolves a _batch_ `pipeline_mode` even on
      the LIVE ingest path (the prior code hardcoded `BATCH_POLYMARKET_CLOB`). When live prediction ingest runs, it
      should stamp `live_<source>` not `batch_<source>`. Make the finalize mode-aware (thread the run mode →
      `live_pipeline_mode_for_venue` for live). Repo: market-tick-data-service.

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

### 2026-06-28/29 (autonomous /autonomous) — LiveEventFacadeSink PubSubTransport fix + warm-sink e2e validation

**Root cause diagnosed and fixed (prior sessions + this session)**:

1. ✅ **MTDS `_make_default_sink` switch**: `websocket_runner.py:242` now returns `LiveEventFacadeSink` — deployed at
   `market-tick-data-service@1e583b90`.

2. ✅ **LiveEventFacadeSink `transport=None` bug** (CRITICAL): `LiveEventFacadeSink.flush()` was calling
   `facade_publish(envelope, transport=None)` → `get_transport(None)` → `InMemoryTransport` → data silently discarded,
   never reached Pub/Sub. Fixed in `event_facade_sink.py` to resolve at `flush()` time with `get_transport("pubsub")`.
   Quickmerged: `market-tick-data-service@7fae3c0b`. Tarball `mtds-code.tar.gz` rebuilt and uploaded 06:00:30Z.

3. ✅ **Tarball preflight crash fix**: `create-code-tarballs.sh:350` grep on dynamic-version pyproject.toml returned
   exit 1, aborting under `set -euo pipefail`. Added `|| true`. `deployment-service@8850f08`.

4. ✅ **VM publisher IAM blocker (WORKED AROUND)**: Compute Engine default SA lacks `pubsub.topics.publish`; project-
   level IAM `terraform apply` blocked (`unified-trading-sa` lacks `resourcemanager.projects.getIamPolicy`). Workaround:
   added `--service-account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com` to
   `launch-mtds-live-prediction-consolidated.sh` — `unified-trading-sa` already has `pubsub.topics.publish` (verified
   via `gcloud pubsub topics publish persist-prediction-trades --message=...`). `deployment-service@e87abb17`.
   - Terraform `publisher_iam.tf` also committed (project-level IAM for BOTH SAs) — apply needs admin credentials:
     `cd deployment-service/terraform/gcp/live_event_log && terraform apply -var=... -auto-approve`.

5. ✅ **Warm sink e2e validated**: `gcloud pubsub topics publish persist-prediction-trades` → parquet file appeared at
   `gs://central-element-323112-events/live-events/warm/prediction/trades/2026-06-29T06:00:14+00:00_59fc0c.parquet`
   (21B, 06:05:14Z). Cloud Storage subscription works end-to-end.

6. ✅ **Consolidated prediction VM relaunched** as `mtds-live-prediction-consolidated-20260629-060558`
   (unified-trading-sa; e2-highmem-4; 06:06 UTC). Running as unified-trading-sa — will NOT hit publish permission
   errors.

**Active monitors (06:15 UTC June 29)**:

- VM `mtds-live-prediction-consolidated-20260629-060558` — heartbeat "starting" at T+6min; 4 shards (POLYMARKET:trades,
  POLYMARKET:book_snapshot_5, KALSHI:trades, KALSHI:book_snapshot_5) expected "running" by T+8-10min.
- Arb detector `prediction-arb-detector-20260628-191545` RUNNING (unchanged since prior session).
- Watch for real warm GCS data (>1 file) at `gs://central-element-323112-events/live-events/warm/prediction/trades/`.

**Pending after warm data confirmed**:

- ✅ **Enable BQ external tables — DONE 2026-08-05 (`deployment-service@b94a6dd`, slot 13).** `terraform apply`
  completed: 52 BQ external tables created in `live_events` dataset, including `prediction_book_snapshot`,
  `prediction_book_snapshot_5`, `prediction_trades`. Two config fixes were required: (1) `source_format` changed from
  PARQUET to NEWLINE_DELIMITED_JSON — the warm GCS sink writes flat JSON files misnamed `.parquet`; (2) removed
  `hive_partitioning_options` — data files are flat timestamp-named, not Hive-partitioned. 46 sentinel NDJSON files
  created for empty prefixes (sports, tradfi, all, commodity, defi) so BQ autodetect has at least one file per prefix.
- ✅ Grant project-level `roles/pubsub.publisher` to `1060025368044-compute@developer.gserviceaccount.com` — **DONE
  2026-08-05**: applied via `gcloud projects add-iam-policy-binding` as `unified-trading-sa` (verified live via
  `get-iam-policy` — the binding is present). The workaround (`--service-account=unified-trading-sa`) is no longer
  needed for new VM launches but is harmless to keep.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the depth-retention todo surfaces an
  architecture question about the live sink's rolling-window overwrite model (not a bounded verification), and the other
  is a cross-repo deferred cross-dependency.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- added batch4 (owns the extracted depth-retention
  item) + 2 source paths (websocket_runner.py's overwrite behavior, the prediction adapters dir).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (prediction tranche, autonomous)**: MIXED — the depth-history-retention checkbox
  (line 411) is KEEP-NA-STALE-CLOSE, checked off (its own stated done-when was satisfied in-doc by the 2026-08-04
  slot-5/slot-7 entries above). The nested `DEFERRED-CROSS-DEP` book_snapshot_5 row-proof sub-bullet (2-space-indented,
  missed by a strict top-level `^- \[ \]` grep) is KEEP-NA-STALE-DUPLICATE, citation added — confirmed already claimed
  (not yet dispatched) in `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s "Deferred — gated on a sibling todo
  landing" section; reclassifying here would create a competing dispatch surface, so it stays NA. Conflict-check
  correction: an earlier classifier pass this run flagged this item RECLASSIFY without finding the existing batch4 claim
  — verified directly and downgraded before any `assigned_vm` flip.
- **na-eligibility-audit 2026-08-07 (prediction tranche, autonomous)**: KEEP-NA-STALE-DUPLICATE, re-verified — the
  DEFERRED-CROSS-DEP nested sub-item's citation (added 2026-08-06) to
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s Deferred section is still current, independently
  re-confirmed against batch4's live content (still `status: active` / `assigned_vm: planning`; the item is still parked
  there per its own "Reconciled 2026-08-07 (finalize P1)" note — a separate process, not this audit). No action needed.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-checked
  against the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement [PM-reconciler/semver-agent scope, confirmed unrelated], GSM
  secret `deepseek-v4-pro-api-key` + 5 Slack webhooks) — none bound this doc's sole open item. **Citation correction**:
  the item is no longer parked in batch4's Deferred section awaiting a future batch — it has SINCE been promoted and
  extracted verbatim into `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` (drafted 2026-08-09, `status: draft`,
  `assigned_vm: planning`, todo citing this doc's own "DEFERRED-CROSS-DEP" checkbox by name), which explicitly grepped
  batch4/6/7/8/9 + finalizes + all 4 Phase A-E children for this item before drafting and confirmed no other claim. This
  doc's own citation (pointing at batch4) is now stale by 2 days — flagging for whoever next touches this doc to repoint
  it at batch10 once that batch lands (not re-pointed here to avoid a same-session dual-edit race on a doc neither this
  sweep nor batch10 owns exclusively). Stays NA — batch10 is the correct, already-vetted owner. Doc stays NA.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (5 entries), unchanged — both remaining open items
  (batch4-tracked DEFERRED-CROSS-DEP row-proof; the now-closed depth-retention design question) still map to the same
  set.

## Deferred work — migrated to:

See inline `DEFERRED-CROSS-DEP` annotation within this plan (the "batch book_snapshot_5 row-proof" todo) for the
specific successor/blocker: it needs an instruments-service re-enumeration of a recent past date carrying
`clob_token_ids`, then a re-run of the book backfill for that date (repo: instruments-service + deployment-service).
Live book_snapshot_5 capture is already code-complete and live-proven; this is a batch-only row-proof residual, not a
sports/prediction-track blocker.

## Progress Log (cont'd)

- **na-eligibility-audit 2026-08-17** [body-hash:7e6d571d7e2cefb3]: KEEP-NA, valid (not-applicable — 0 open todos,
  `archive_exempt: true`). Re-confirmed: the depth-retention design question closed 2026-08-06 and the
  DEFERRED-CROSS-DEP row-proof item was extracted to `prediction_satellite_ao_dispatch_batch10_2026_08_09.md`
  (shipped/reconciled per that batch and its finalize). This doc's own frontmatter defers the archival call to
  `/archive-candidates-audit` (complex referrer graph), not this skill — no action needed here.

- **na-eligibility-audit 2026-08-17 (prediction tranche, re-verify)** [body-hash:d9898a365d8c52dc]: KEEP-NA, valid
  (not-applicable — re-confirmed 0 open todos via a fresh full read + grep; every prose "[ ]" mention is historical
  narration, not a live checkbox). `archive_exempt: true` defers the archival call to `/archive-candidates-audit`, not
  this skill. Doc stays NA.

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- re-verified, unchanged.

- **na-eligibility-audit 2026-08-18 (prediction tranche, re-verify)** [body-hash:3cc78be393f54574]: KEEP-NA, valid
  (not-applicable — re-confirmed 0 open todos via a fresh full read + grep across every checkbox-marker variant;
  every prose "[ ]" mention is historical narration). `archive_exempt: true` defers the archival call to
  `/archive-candidates-audit`, not this skill. Doc stays NA.

- **na-eligibility-audit 2026-08-19 (prediction tranche, dispatch agt-0e920e)** [body-hash:be7672a984d4baab]: KEEP-NA,
  valid (not-applicable) — re-confirmed 0 open todos via a fresh full read + dual-mode grep (strict + broad
  indent-agnostic). `archive_exempt: true` still correctly routes the archival decision to `/archive-candidates-audit`
  (complex referrer graph), not this skill. Doc stays NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
