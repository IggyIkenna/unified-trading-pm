---
doc_type: issue
title: Silent-cap source audit — remaining findings not fixed in the initial dispatch pass
summary: >-
  Full-corpus silent-cap audit (`cross_cutting_satellite_ao_dispatch_batch2_2026_08_09` item 3: "Run the silent-cap
  source audit + FetchEvidence/UnprovenHonestAbsenceError paging sweep across every data source") ran two parallel
  exhaustive sweeps over instruments-service and market-tick-data-service. The highest-confidence, lowest-risk fixes (2
  CRITICAL RPC-error-swallow bugs, a genuine Lighter pagination defect, 3 cap-exhaustion-warning additions, and 5
  mechanical skip-loop additions mirroring an already-shipped sibling pattern) shipped in that same session. This issue
  tracks the REMAINING findings — either higher-risk (needs a live-schema verification or a query-shape redesign before
  touching), lower-priority (dormant code / low real-world exposure), or needing a closer manual read the time-boxed
  audit couldn't complete.
status: open
nature: issue
asset_group: [cross-cutting, defi, prediction, sports]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [silent-cap, pagination, data-correctness, honest-absence, findings-closure]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-08-09
author: claude-code (AO worker slot 25, cross_cutting_satellite_ao_dispatch_batch2 item 3)
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
resolved_by:
locked_by:
locked_since:
source:
  [
    'Two parallel Explore-agent audits (2026-08-09) over instruments-service''s reference_data/adapters/ (5 asset
    groups) and market-tick-data-service''s market_interface/adapters/ + adapters/onchain_perps/ + adapters/_umi_*
    trees, dispatched from cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md item 3. Reference "done right"
    pattern: instruments-service/reference_data/adapters/defi/{uniswap_v3,uniswap_v4,balancer}.py''s while skip <=
    _MAX_SKIP loop; AsterAdapter._fetch_agg_trades_response''s for/else cap-exhaustion warning
    (market-tick-data-service).',
  ]
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: []
---

# Silent-cap source audit — remaining findings

## What I found

The parent todo's audit covered every adapter/fetcher under `instruments_service/reference_data/adapters/`
(instruments-service, 5 asset groups) and `market_tick_data_service/market_interface/adapters/` +
`adapters/onchain_perps/` + `adapters/_umi_*` (market-tick-data-service). Fixed in the same session (not re-listed
here): `onchain_event_poller.py` + `governance_params_event_poller.py` (JSON-RPC error silently coerced to empty →
cursor advanced past errored range, permanent data loss), `_umi_lighter.py`'s `_fetch_lighter_trades_for_symbol` (loop
always broke after one page regardless of whether it reached `start_ms`), `kalshi_adapter.py` + `polymarket_adapter.py`
(page-cap-exhaustion now routes to `attempted_failed` via the existing CF-11 channel), `alchemy_transfers_client.py`
(page-cap-exhaustion warning), and 3 instruments-service DeFi adapters gaining the already-proven
`while skip <= _MAX_SKIP` loop (`uniswap_v2.py`, `uniswap_v3.py`'s 2 orphaned fallback legs, `morpho.py`'s page-cap
warning).

The findings below are what's LEFT — grouped by why they weren't fixed inline.

## Why it matters

Per `/codex/02-data/instruments-foundation-and-catalogue-completeness.md` § 6.2: a silent cap makes missing
instruments/rows look like genuine absence, and `FetchEvidence`/`UnprovenHonestAbsenceError` (defined in
`unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py`) only gates the **zero-rows**
path — it provides **zero protection** against a partial-but-nonzero fetch silently masquerading as a complete universe,
which is exactly what every finding below is.

## Recommended decision

Dispatch each item below as its own bounded todo; group A needs care to avoid a WORSE regression (guessing a vendor
schema wrong could 400 every call), group B is genuinely live-active and higher-value than the closed dormant venue
findings.

## Todos

- [x] ✅ [CODE] P1. **Polymarket instruments-service top-2000-by-volume cap (highest-priority remaining finding — LIVE
      code path).** `instruments_service/reference_data/adapters/prediction/polymarket/adapter.py` `get_instruments`
      live-mode loop + `markets.py` (`_MAX_PAGES_ACTIVE=20`, `_PAGE_LIMIT=100` → hard 2000-market ceiling,
      `order=volume24hr desc` on the underlying Gamma `/markets` call). Unlike the Kalshi sibling adapter, there is no
      comment/mitigation acknowledging this boundary and no supplemental fetch for markets outside the top 2000. Repo:
      instruments-service. Done when: either `_MAX_PAGES_ACTIVE` is raised to a safety-net value and the loop continues
      until a genuinely short page (true exhaustion, not a hard page-count ceiling), or a Kalshi-style
      category/series-scoped supplemental fetch recovers markets outside the top 2000; a regression test proves
      a >2000-market universe is no longer silently truncated. — instruments-service@57c71bd4f: raised
      `_MAX_PAGES_ACTIVE` 20→10000 (safety-net, mirrors `clob.py`'s `_CLOB_MAX_PAGES=10000` pattern) so the loop is
      exhaustion-driven; added a for/else cap-exhaustion warning (mirrors AsterAdapter); regression test
      `test_get_instruments_beyond_2000_market_hard_ceiling_not_truncated` proves a 2537-market/26-page universe is no
      longer truncated.
- [x] ✅ [CODE] P1. **Betfair `listMarketCatalogue` sorted-by-start-time top-1000 cap (LIVE, real risk).**
      `instruments_service/reference_data/adapters/sports/adapters/betfair.py` `_fetch_markets_raw` (`maxResults=1000`,
      `sort: "FIRST_TO_START"`, effectively "all markets" filter). Betfair's API hard-caps `maxResults` at 1000 with NO
      offset pagination on this call — the only way past it is to narrow the `filter` (per `eventTypeId` / per rolling
      time window) and merge multiple scoped calls. Betfair typically has well over 1000 concurrently-listed markets, so
      later-starting markets are silently dropped today. Repo: instruments-service. Done when: the single "all markets"
      call is split into multiple `filter`-scoped calls (e.g. per sport `eventTypeId`) and merged; a regression test
      proves a >1000-market universe across 2+ event types is no longer truncated. — instruments-service@b8668094:
      enumerates event types (sports) live via `listEventTypes` (no hardcoded id list) and scopes each
      `listMarketCatalogue` call to one `eventTypeId`, raising the effective ceiling from 1000 markets globally to 1000
      per sport; a residual per-sport cap hit now logs `ADAPTER_PAGE_CAP_HIT` instead of staying silent; per-event-type
      fetch failures are shard-isolated (partial results kept; only all-failed raises to `attempted_failed`). 3 new
      regression tests: `test_get_instruments_pages_across_event_types` (2 sports merged),
      `test_get_instruments_logs_page_cap_hit` (ceiling-hit observability),
      `test_get_instruments_partial_event_type_failure_keeps_results` (shard isolation).
- [x] ✅ [CODE] P2. **TradFi/DeFi Aave-history caps in market-tick-data-service (protocol-outage + risk-parameter blind
      spots).** Two files: (a) `market_interface/adapters/defi/protocol_outage_adapter.py`'s
      `_AAVE_V2_RESERVE_HISTORY_QUERY` (`reserveConfigurationHistoryItems`, whole-history no time filter,
      `orderBy: timestamp asc`, `first: 1000`) — ordered ASCENDING with no window filter means if Aave V2's
      cross-reserve freeze/unfreeze history ever exceeds 1000 total events, only the OLDEST 1000 are kept and the NEWEST
      (most operationally relevant, e.g. a recent freeze) are silently dropped — this is a protocol-**outage detector**,
      so missing a recent freeze defeats its purpose. (b) `market_interface/adapters/defi/aave_positions.py`'s
      `_RESERVE_PARAMS_HISTORY_QUERY` (`reserveParamsHistoryItems` per reserve per 1-day window, `first: 1000`, no skip)
      — a high-activity reserve (USDC/WETH mainnet) can exceed 1000 interactions/day, silently truncating the day's
      rate-index history. Repo: market-tick-data-service. Done when: (a) switches to a `skip`-paginated or
      DESCENDING-ordered query (recent-first) so a cap-hit preserves the operationally-relevant tail; (b) gains a `skip`
      pagination loop mirroring the already-fixed `_dex_swaps_queries.py` timestamp-cursor pattern; both get a
      regression test proving a >1000-event day is no longer truncated. — market-tick-data-service@0b6a13d5: (a) added a
      genuine `skip`-paginated loop (`_AAVE_V2_HISTORY_MAX_SKIP=5000`, mirrors `uniswap_v2.py`'s proven pattern) so no
      history is dropped rather than just reordering; cap-exhaustion warning on exhaustion. (b) added timestamp-cursor
      pagination within the 1-day window (mirrors `_dex_swaps_queries.py`'s `_paginate_swaps`). New regression tests:
      `test_history_beyond_1000_items_not_truncated` in both `test_protocol_outage_adapter.py` and the new
      `test_aave_positions.py`, each proving a >1000-item multi-page response is fully collected, not truncated to the
      first page. Full quality-gates.sh green (10286+ tests passed).
- [x] ✅ [SCRIPT] P2. **Graph `skip`-based pagination loops in market-tick-data-service treat a skip-cap GraphQL error
      identically to "no more data."** 9 call sites across
      `market_interface/adapters/defi/{curve_adapter,balancer_adapter,uniswapv2_adapter,     uniswap_v3_adapter,uniswapv4_adapter}.py`
      (swaps + hourly-data + position-data queries, all `first: 1000, skip` loops bounded by The Graph's hard ~5000-skip
      ceiling). Each loops correctly but never distinguishes a genuine short/empty page from a page-fetch call that
      errored at the skip-cap boundary — the page-fetch helper swallows the error as falsy and the
      `while True: if not     raw: break` loop treats it exactly like honest exhaustion. Repo: market-tick-data-service.
      Done when: each of the 9 call sites detects a GraphQL/HTTP error response distinctly from a genuinely empty page
      and logs/routes it as an incomplete fetch (mirroring the `for/else` cap-exhaustion pattern already shipped for
      Kalshi/Polymarket this session) rather than silently treating it as "done." — market-tick-data-service@60c61bbb
      (fix content at d63f436c, refactored for QG file/method size gates at 60c61bbb): fixed all 9 sites across 3 code
      shapes — (1) `curve_adapter.py`/ `balancer_adapter.py`: the page-fetch helper already returned `None` distinctly
      on error, but the caller's `if not raw: break` collapsed `None`/`[]` into the same falsy branch — split into
      `if raw is None: warn+break` / `if not raw: break`; (2) `uniswapv2_adapter.py`/`uniswapv4_adapter.py` (2 sites
      each): the helper itself collapsed a genuinely empty page into `None` (`return swaps if swaps else None`) — fixed
      to `return swaps` (preserve `[]`), plus the same distinct-warning split in the caller; (3) `uniswap_v3_adapter.py`
      (3 sites): goes through the shared `_execute_graphql()` (never returns `None`; errors surface via
      `data["errors"]`) — added an explicit `if data.get("errors"): warn+break` before the empty-page check. Each error
      path now logs `"... pagination stopped early at skip=%d ... results may be truncated"` distinctly from the silent
      genuine-exhaustion break. New regression tests (`test_defi_dex_swaps_pagination_error_handling.py`, 10 tests, 2
      per adapter file): proves an error page logs the truncation warning and a genuinely empty page does not. Follow-up
      P3 todo added below for a separate, pre-existing (not part of this finding) dormant AttributeError bug discovered
      in `uniswap_v3_adapter.py` while adding this test coverage.
- [x] ✅ [SCRIPT] P2. **Instruments-service `first: 100` lending-market discovery caps, no guard.** Three files,
      ascending real-world risk: `compound_v3.py` (`markets(first: 100)` — lowest risk, Comet deployments are inherently
      few per chain), `spark.py` (`markets(first: 100, where:     {isActive:true})` — an Aave V3 fork), `aave_v3.py`
      (`_RESERVES_QUERY_TEMPLATE`, `first: 100,     where: {isActive: true})`). All three currently sit well under 100
      real reserves/markets per chain, but none has a runtime count-check or comment acknowledging the boundary the way
      Kalshi's historical-mode cap does. Repo: instruments-service. Done when: each gains either a `skip` pagination
      loop (mirrors this session's `uniswap_v2.py`/`morpho.py` fixes) OR, if a live schema check confirms `skip` isn't
      supported, a loud warning when `len(results) >= 100` (mirrors this session's `morpho.py` warning-only fix) plus a
      code comment stating which mitigation was chosen and why. — instruments-service@58ede81d: all three query
      `gateway.thegraph.com` (the same genuine-The-Graph infra already proven to support `skip` in `uniswap_v2.py`/
      `uniswap_v3.py`, unlike Morpho's unverified first-party API), so each gained a real `while skip <= _MAX_SKIP`
      (5000, matching the sibling adapters) pagination loop rather than a warning-only mitigation. New regression tests
      (`test_get_instruments_paginates_past_first_page` in `test_defi_adapters_comprehensive.py` ×2 and
      `test_spark_metadata.py`) prove a >`_FETCH_LIMIT`-market/reserve universe across a full + short page is fully
      collected, not truncated. Full quality-gates.sh green (155s).
- [x] ✅ [CODE] P2. **Raydium REST pagination not wired despite a paged API contract.**
      `instruments_service/reference_data/adapters/defi/raydium.py` `_fetch_active_pools` hardcodes `page="1"` with no
      loop to `page=2,3,…`, even though the endpoint is an explicit `page`/`pageSize` REST API whose response wrapper
      carries its own `count` total (never compared against `len(pools)` to detect truncation). Repo:
      instruments-service. Done when: the fetcher loops `page += 1` while `len(pools) == pageSize` (or compares against
      the response's `count` field) and a regression test proves a >1-page pool universe is no longer truncated to the
      first page. — instruments-service@5502e9e7: loop now pages `page += 1` while the page is full
      (`len(pools) == _RAYDIUM_PAGE_SIZE`) and the response's `count` isn't yet reached, mirroring the for/else
      cap-exhaustion pattern already shipped for Polymarket/Kalshi this session (`_RAYDIUM_MAX_PAGES=10000` safety-net).
      New regression test `test_get_instruments_paginates_past_first_page` proves a 2-page/3-pool universe is no longer
      truncated to the first page. Full quality-gates.sh green (107s).
- [ ] [SCRIPT] P3. **Coinbase CDE futures-universe cap, no guard.**
      `instruments_service/reference_data/adapters/cefi/coinbase_cde.py` `get_instruments` (`limit="250"`, single GET,
      no offset loop or count check) — docstring claims "ALL 99 real live products" today (well under 250) but no
      runtime check protects against growth past 250. Repo: instruments-service. Done when: a runtime check compares the
      returned count against the response's total-count field (if the API exposes one) and logs/pages when the universe
      approaches or hits the 250 cap.
- [ ] [SCRIPT] P3. **Dormant prediction-market hard page-count ceilings — activate-on-re-enable risk.**
      `instruments_service/reference_data/adapters/cefi/{kalshi_perp,polymarket_perp}.py` both define `_PAGE_LIMIT=200`,
      `_MAX_PAGES=10` (hard 2000-contract ceiling — NOT exhaustion-driven, stops even when `has_more`/cursor says more
      data exists) but are currently `_REPOINT_PENDING = True` (return `[]` before any network call) — dormant risk that
      activates the moment either venue is re-enabled (Kalshi Phase 2 / Polymarket Phase 3 per module docstrings). Repo:
      instruments-service. Done when: `range(_MAX_PAGES)` is replaced with a genuinely cursor-exhaustion-driven loop (a
      large safety-net page count, e.g. mirroring `polymarket/clob.py`'s `_CLOB_MAX_PAGES = 10000` "safety cap against
      runaway loop" pattern which already correctly exits on the CLOB's own cursor sentinel) BEFORE either venue's
      `_REPOINT_PENDING` flag flips to re-enable it.
- [x] ✅ [REVIEW] P3. **Kalshi instruments-service nested series-scoped mitigation caps — verify against live API before
      trusting the current mitigation is sufficient.**
      `instruments_service/reference_data/adapters/prediction/kalshi.py`'s live snapshot already mitigates the top-2000
      cap via a category/series-scoped supplemental fetch (`_fetch_series_scoped_batch`), but that mitigation has its
      OWN nested caps: `_MAX_SERIES_PAGES=5` per series (≤1000 markets/series) and `_MAX_SERIES_TOTAL=362` total series
      — if a single series ever exceeds 1000 open markets, or non-OTHER series count across
      Crypto/Economics/Financials/Sports/Politics ever exceeds 362, the excess is silently dropped with only a log line,
      no completeness proof. Also `_fetch_series_for_category` (`/series?category=X`) is itself a single unpaginated
      call — unverified whether Kalshi's `/series` endpoint has its own hidden page cap. Repo: instruments-service. Done
      when: a live (or sandbox) probe of Kalshi's `/series` endpoint confirms whether it paginates; if the nested caps
      are provably safe at current real-world series/market counts, document the measured headroom in a code comment; if
      not, extend the pagination the same way. — instruments-service@74763c05: live probes (2026-08-10) confirmed
      `/series` is non-paginating (no cursor, `limit` ignored, full category list in one response) and measured BOTH
      nested caps already being silently exceeded — 447 non-OTHER series vs `_MAX_SERIES_TOTAL=362` (old cap dropped
      ~85, mostly the Politics tail: only 1 of its 86 fetched), and KXNASDAQ100U holding 2800+ open markets vs the
      1000-market/series page budget (old budget silently dropped ~1800 markets for that one series). Raised
      `_MAX_SERIES_TOTAL` 362→1000 and `_MAX_SERIES_PAGES` 5→50 (10k/series safety-net, mirrors clob.py's
      `_CLOB_MAX_PAGES`); both cap-hits now log a warning + emit `ADAPTER_PAGE_CAP_HIT` (for/else on page-budget
      exhaustion; empty-page honest-exhaustion break added); measured headroom documented in code comments. 6 new
      regression tests (460-series universe not truncated at old cap; 7-page/1400-market series fully collected;
      page-budget + total-cap-hit emit the event; constant guards vs measured counts). Full quality-gates.sh green
      (127s).
- [ ] [CODE] P3. **Morpho Blue first-party API — verify `skip` support before implementing real pagination.** This
      session added a page-cap WARNING to `morpho.py` (not full pagination) because Morpho Blue's `blue-api.morpho.org`
      GraphQL schema is first-party (not The Graph) and its `skip`/cursor support was NOT verified against a live schema
      — guessing wrong risks a 400 on every call, worse than today's top-1000-by-SupplyAssets truncation. Repo:
      instruments-service. Done when: a live GraphQL introspection query against `blue-api.morpho.org` confirms whether
      `markets(skip: Int, ...)` is a valid argument; if yes, implement the same `while skip <= _MAX_SKIP` loop already
      proven in `uniswap_v2.py`/`uniswap_v3.py`; if no, document the confirmed absence in the code comment and leave the
      warning-only mitigation in place.
- [x] ✅ [REVIEW] P3. **Sports adapters with no pagination keywords found — confirm no hidden vendor-side default page
      cap.**
      `instruments_service/reference_data/adapters/sports/adapters/{api_football,     base,footystats,understat,soccerfootball_info,transfermarkt,open_meteo,api_football_reference}.py`
      have zero grep hits for `page`/`offset`/`cursor`/`has_more`/`MAX_` — each call appears naturally bounded by its
      query scope (one date's fixtures, one team's squad), but the audit did NOT exhaustively verify each vendor's API
      docs for a hidden default page size on a list-style endpoint called with no explicit `limit`/`page` param
      (vendor-side default silently applies). Repo: instruments-service. Done when: each vendor's API docs (or a live
      probe) confirms whether any unparented list-style call in these files can silently truncate; document the finding
      per file (even a "confirmed no cap" note closes this out) or fix any confirmed cap. —
      instruments-service@2d7c19827: vendor-doc review (2026-08-10) confirmed TWO hidden caps fixed + one conditional
      cap + documented no-caps: (a) FootyStats `/todays-matches` returns max 500 matches/page and paginates by default
      (`&page=N`) — added `_fetch_todays_matches` page loop (get_fixtures / get_fixture_predictions /
      get_fixture_odds_snapshot all rewired), short-page exhaustion + `_TODAYS_MATCHES_MAX_PAGES` safety-net; documented
      `/league-teams` (100/page, safe for ~18-40-team leagues) + `/league-list` (no documented page param). (b) SFI
      `/championships/list/` paginates unconditionally (`p` param, 100/page, ~1954 total) and `/matches/day/basic/`
      paginates for present/future days (100/page) — added shared `_fetch_paginated` loop (get_leagues +
      get_match_descriptors_for_date; short-page + count-confirmed + safety-net termination; unpaginated historical-day
      responses stop after page 1). (c) api-football endpoints used are documented single-page but the `paging` envelope
      was ignored — added `_warn_on_unfetched_pages` guard so a future vendor-side page cap is LOUD, not silent. (d)
      confirmed-no-cap documented per file for transfermarkt (Apify dataset items have no default limit; standings
      naturally bounded), understat (full-season single response, no pagination concept), open_meteo (point+date-range
      timeseries), api_football_reference (wrapper, delegates), base (shared HTTP layer). 5 new regression tests
      prove >page-size universes are no longer truncated (footystats 700-match date; SFI 150-championship list +
      250-match present-day + 2 pagination-parser units). Full quality-gates.sh green (exit 0, 173s first run / 35s
      content-sentinel re-run), quickmerge landed + ancestry-verified on origin/live-defi-rollout.
- [ ] [SCRIPT] P3. **Market-tick-data-service prediction/transfer bounded max-page loops — same cap-exhaustion-warning
      gap as this session's Kalshi/Polymarket fix, lower priority given confirmed call-graph usage.**
      `market_interface/clients/alchemy_transfers_client.py::get_all_transfers` already got a warning-only fix this
      session (no attempted_failed plumbing exists in this client).
      `market_interface/adapters/prediction/{kalshi_adapter,polymarket_adapter}.py` in market-tick-data-service
      (DIFFERENT files from the instruments-service adapters of the same name, and DIFFERENT from the ones already fixed
      this session under `market_interface/adapters/prediction/` in market-tick-data-service itself — verify which
      repo's copy this refers to before touching) — re-confirm via a fresh grep whether MTDS carries its OWN separate
      Kalshi/Polymarket trades-fetch implementation distinct from the ones fixed this session, since the parent audit's
      file paths for these overlapped with the ones already patched. Repo: market-tick-data-service. Done when: a fresh
      grep confirms whether a distinct MTDS-side implementation exists; if so, apply the same `for/else` cap-exhaustion
      → `attempted_failed` pattern; if it's the same file already fixed, close this as duplicate.
- [ ] [SCRIPT] P3. **`_umi_extended.py` candle-window pagination — currently safe, latent risk if call graph changes.**
      `market_tick_data_service/adapters/_umi_extended.py::_extended_candle_params` logs a truncation warning and clips
      to `_EXTENDED_CANDLE_PAGE_CAP=2800` bars but issues only ONE request (never chunks) when `needed` exceeds the cap
      — currently safe because both call sites always pass a 1-day `PT1M` window (≤1440 bars). Repo:
      market-tick-data-service. Done when: either the function gains real chunking so a future wider-window caller can't
      silently truncate, or (if genuinely out of scope) a code comment states the current call-graph invariant that
      keeps this safe, so a future caller change is forced to notice the constraint.
- [ ] [CODE] P3. **`UniswapV3Adapter._download_swaps`/`_download_pool_hourly_data` (market-tick-data-service) crash with
      `AttributeError` on ANY successful non-empty page — dormant because nothing in production instantiates
      `UniswapV3Adapter`.** Discovered while adding regression coverage for this doc's Graph-pagination-error-vs-empty
      todo (item 4, now shipped). `_parse_swap_record` reads `swap.amountUSD`/`swap.sqrtPriceX96`/
      `swap.transaction.blockNumber` and `_convert_v3_hourly_item` reads `item.periodStartUnix` etc., but the backing
      pydantic models (`GraphUniswapSwap`/`GraphSwapTransaction`/`GraphPoolHourData` in `_defi_graph_models.py`) declare
      those fields under their snake_case Python name with a camelCase GraphQL `alias` (e.g.
      `amount_usd: ... = Field(alias="amountUSD")`) — pydantic v2 attribute access uses the field name, not the alias,
      so `swap.amountUSD` raises `AttributeError` (confirmed via a live `.venv` repro, not just a read). Live V3
      swap/hourly capture is unaffected TODAY because `dex_swaps_handler.py`'s cascade
      (`build_swaps_cascade`/`_dex_swaps_queries.py`) is the actual production path for Uniswap V3 and does not use this
      adapter class — `grep -rn "UniswapV3Adapter("` outside its own file hits only one test file. Repo:
      market-tick-data-service. Done when: every aliased-model attribute access in `_parse_swap_record` and
      `_convert_v3_hourly_item` is switched to the model's actual (snake_case) field name, and a regression test
      exercises `_download_swaps`/`_download_pool_hourly_data` with a non-empty page (previously impossible without
      hitting this crash) to prove the class is safe if it's ever wired into production.

## Progress Log (append-only)

- 2026-08-09 (slot 30, data_engineering): shipped the Aave-history pagination todo — see the todo's own evidence line
  above for detail. market-tick-data-service@0b6a13d5. Remaining todos in this doc are still open.
- 2026-08-09 (slot 30, data_engineering): shipped item 4 (Graph skip-pagination error-vs-empty-page distinction, 9 call
  sites) — see the todo's own evidence line above. market-tick-data-service@60c61bbb (fix content d63f436c, size-gate
  refactor 60c61bbb), QG green (265s), quickmerge landed + ancestry-verified on origin/live-defi-rollout. Filed a new P3
  follow-up todo for a separate, pre-existing dormant `AttributeError` bug in `UniswapV3Adapter` discovered while adding
  test coverage (not part of the silent-cap finding itself — a field-name/alias mismatch). Remaining todos in this doc
  are still open.
- 2026-08-09 (slot 24, data_engineering): shipped the `first: 100` lending-market discovery cap todo (compound_v3.py,
  spark.py, aave_v3.py) — see the todo's own evidence line above for detail. instruments-service@58ede81d, QG green
  (155s), quickmerge landed + ancestry-verified on origin/live-defi-rollout. Remaining todos in this doc are still open.
- 2026-08-09 (slot 31, data_engineering): shipped the Raydium REST pagination todo — see the todo's own evidence line
  above for detail. instruments-service@5502e9e7, QG green (107s), quickmerge landed + ancestry-verified on
  origin/live-defi-rollout. Remaining todos in this doc are still open.
- 2026-08-10 (slot 19, review): shipped the Kalshi nested series-scoped mitigation caps todo — see the todo's own
  evidence line above for detail. instruments-service@74763c05, QG green (127s), quickmerge landed + ancestry-verified
  on origin/live-defi-rollout. Remaining todos in this doc are still open.
- 2026-08-10 (slot 19, review): shipped the sports-adapters hidden-vendor-page-cap todo — see the todo's own evidence
  line above for detail. instruments-service@2d7c19827, QG green (exit 0), quickmerge landed + ancestry-verified on
  origin/live-defi-rollout. Remaining todos in this doc are still open.

## Codex SSOTs

`/codex/02-data/instruments-foundation-and-catalogue-completeness.md` § 6.2/6.5,
`/codex/02-data/honest-absence-downstream-handling.md`.
