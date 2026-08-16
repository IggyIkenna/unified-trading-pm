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
status: resolved
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
resolved_by: market-tick-data-service@102a66de38
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
context_scope:
  [
    instruments-service/instruments_service/reference_data/adapters/cefi/coinbase_cde.py,
    instruments-service/instruments_service/reference_data/adapters/cefi/kalshi_perp.py,
    market-tick-data-service/market_tick_data_service/adapters/_umi_extended.py,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
---

> **🟢 ARCHIVED 2026-08-16** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Every todo shipped, most recently the `UniswapV3Adapter` item
> (`market-tick-data-service@102a66de38`, plus its two preceding commits `6da10ad1`/`c6ceadce`) — see that todo's own
> text for the correction it required (the original finding's repro cited this package's deprecated
> `_defi_graph_models.py`, not the real `unified_api_contracts.external.thegraph` model the adapter actually imports).

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
      `market_interface/adapters/defi/{curve_adapter,balancer_adapter,uniswapv2_adapter, uniswap_v3_adapter,uniswapv4_adapter}.py`
      (swaps + hourly-data + position-data queries, all `first: 1000, skip` loops bounded by The Graph's hard ~5000-skip
      ceiling). Each loops correctly but never distinguishes a genuine short/empty page from a page-fetch call that
      errored at the skip-cap boundary — the page-fetch helper swallows the error as falsy and the
      `while True: if not raw: break` loop treats it exactly like honest exhaustion. Repo: market-tick-data-service.
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
      few per chain), `spark.py` (`markets(first: 100, where: {isActive:true})` — an Aave V3 fork), `aave_v3.py`
      (`_RESERVES_QUERY_TEMPLATE`, `first: 100, where: {isActive: true})`). All three currently sit well under 100 real
      reserves/markets per chain, but none has a runtime count-check or comment acknowledging the boundary the way
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
- [x] ✅ [SCRIPT] P3. **Coinbase CDE futures-universe cap, no guard.**
      `instruments_service/reference_data/adapters/cefi/coinbase_cde.py` `get_instruments` (`limit="250"`, single GET,
      no offset loop or count check) — docstring claims "ALL 99 real live products" today (well under 250) but no
      runtime check protects against growth past 250. Repo: instruments-service. Done when: a runtime check compares the
      returned count against the response's total-count field (if the API exposes one) and logs/pages when the universe
      approaches or hits the 250 cap. — instruments-service@31de8c9bd1: live-probed the endpoint (2026-08-16) and found
      it has no independent "total" field — `num_products` is just the current page's count, always equal to
      `len(products)` — but it DOES genuinely paginate via `pagination.{next_cursor,has_next}` (2 live probes at
      limit=5 confirmed zero product_id overlap across pages). Implemented real cursor-based pagination instead of a
      count-vs-cap heuristic (mirrors `kalshi_perp.py`'s shard-isolation error handling and `raydium.py`'s for/else
      `_MAX_PAGES=10000` safety-net cap-exhaustion warning + `ADAPTER_PAGE_CAP_HIT` emission in this same session) — a
      >1-page universe can no longer be silently truncated at all, which fully closes the finding rather than just
      warning near the old 250 cap. 3 new regression tests: `test_get_instruments_paginates_past_first_page` (2-page
      universe fully collected), `test_get_instruments_logs_page_cap_hit` (page-budget exhaustion emits
      `ADAPTER_PAGE_CAP_HIT`), `test_get_instruments_single_page_response_still_works` (no-`pagination`-key response
      still terminates correctly). Full quality-gates.sh green (141s).
- [x] ✅ [SCRIPT] P3. **Dormant prediction-market hard page-count ceilings — activate-on-re-enable risk.**
      `instruments_service/reference_data/adapters/cefi/{kalshi_perp,polymarket_perp}.py` both define `_PAGE_LIMIT=200`,
      `_MAX_PAGES=10` (hard 2000-contract ceiling — NOT exhaustion-driven, stops even when `has_more`/cursor says more
      data exists) but are currently `_REPOINT_PENDING = True` (return `[]` before any network call) — dormant risk that
      activates the moment either venue is re-enabled (Kalshi Phase 2 / Polymarket Phase 3 per module docstrings). Repo:
      instruments-service. Done when: `range(_MAX_PAGES)` is replaced with a genuinely cursor-exhaustion-driven loop (a
      large safety-net page count, e.g. mirroring `polymarket/clob.py`'s `_CLOB_MAX_PAGES = 10000` "safety cap against
      runaway loop" pattern which already correctly exits on the CLOB's own cursor sentinel) BEFORE either venue's
      `_REPOINT_PENDING` flag flips to re-enable it. — instruments-service@9e201ee0dd: raised `_MAX_PAGES` 10→10000 on
      both adapters (safety-net, mirrors `clob.py`'s `_CLOB_MAX_PAGES=10000` pattern) so each loop is exhaustion-driven
      off its own cursor/`has_more` signal, not a page-count ceiling; added a for/else cap-exhaustion warning +
      `ADAPTER_PAGE_CAP_HIT` emission (mirrors `coinbase_cde.py`'s pattern from this same session) so genuine safety-net
      exhaustion is loud, not silent. 4 new regression tests (2 per adapter): proves pagination past the old 10-page/
      2000-contract ceiling (12 pages fully collected) and proves genuine safety-net exhaustion emits
      `ADAPTER_PAGE_CAP_HIT`. Full quality-gates.sh green (202s).
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
- [x] ✅ [CODE] P3. **Morpho Blue first-party API — verify `skip` support before implementing real pagination.** This
      session added a page-cap WARNING to `morpho.py` (not full pagination) because Morpho Blue's `blue-api.morpho.org`
      GraphQL schema is first-party (not The Graph) and its `skip`/cursor support was NOT verified against a live schema
      — guessing wrong risks a 400 on every call, worse than today's top-1000-by-SupplyAssets truncation. Repo:
      instruments-service. Done when: a live GraphQL introspection query against `blue-api.morpho.org` confirms whether
      `markets(skip: Int, ...)` is a valid argument; if yes, implement the same `while skip <= _MAX_SKIP` loop already
      proven in `uniswap_v2.py`/`uniswap_v3.py`; if no, document the confirmed absence in the code comment and leave the
      warning-only mitigation in place. — instruments-service@c9b7943f: live introspection (2026-08-16) of
      `blue-api.morpho.org` confirmed `markets(skip: Int, ...)` IS a valid argument (`Query.markets.args` includes
      `skip: Int`), and a functional 2-page live probe (`first:3/skip:0` vs `first:3/skip:3`) returned zero `marketId`
      overlap — genuinely works, not just schema-present. Replaced the warning-only mitigation with a real
      `while skip <= _MAX_SKIP` loop (variables-based query, `_MAX_SKIP=5000` mirroring `uniswap_v2.py`/`uniswap_v3.py`),
      plus a for/else safety-cap warning + `ADAPTER_PAGE_CAP_HIT` emission on genuine exhaustion (mirrors
      `coinbase_cde.py`/`kalshi_perp.py` this session). Updated the pre-existing single-page-cap test to
      `test_get_instruments_paginates_past_first_page` (2-page universe fully collected, not truncated) and added
      `test_get_instruments_hits_skip_safety_cap_emits_warning` (genuine safety-net exhaustion emits the warning +
      `ADAPTER_PAGE_CAP_HIT`). Full quality-gates.sh green (123-126s).
- [x] ✅ [REVIEW] P3. **Sports adapters with no pagination keywords found — confirm no hidden vendor-side default page
      cap.**
      `instruments_service/reference_data/adapters/sports/adapters/{api_football, base,footystats,understat,soccerfootball_info,transfermarkt,open_meteo,api_football_reference}.py`
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
- [x] ✅ [SCRIPT] P3. **Market-tick-data-service prediction/transfer bounded max-page loops — same cap-exhaustion-warning
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
      → `attempted_failed` pattern; if it's the same file already fixed, close this as duplicate. — CLOSED AS DUPLICATE
      (2026-08-16): fresh grep of `market_tick_data_service/market_interface/adapters/prediction/{kalshi_adapter,
      polymarket_adapter}.py` confirms both ALREADY carry the `for/else` cap-exhaustion → `attempted_failed` pattern
      (`_log_page_cap_exhausted()` helper, cursor-based pagination, CF-11 routing) — `git log` on both files shows the
      most recent touch is `c6b9113b fix(defi): CF-11 swallow-fixes in manifest recorder, liquidations GraphQL,
      polymarket catalogue`, i.e. these ARE the same-session fix this todo asked to re-confirm, not a distinct
      unfixed implementation. `market_interface/clients/alchemy_transfers_client.py` also confirmed to already carry
      its warning-only mitigation (2 `logger.warning` cap-exhaustion sites, no `attempted_failed` plumbing — matches
      the todo's own note that none exists for this client). No code change needed; no new implementation to ship.
- [x] ✅ [SCRIPT] P3. **`_umi_extended.py` candle-window pagination — currently safe, latent risk if call graph changes.**
      `market_tick_data_service/adapters/_umi_extended.py::_extended_candle_params` logs a truncation warning and clips
      to `_EXTENDED_CANDLE_PAGE_CAP=2800` bars but issues only ONE request (never chunks) when `needed` exceeds the cap
      — currently safe because both call sites always pass a 1-day `PT1M` window (≤1440 bars). Repo:
      market-tick-data-service. Done when: either the function gains real chunking so a future wider-window caller can't
      silently truncate, or (if genuinely out of scope) a code comment states the current call-graph invariant that
      keeps this safe, so a future caller change is forced to notice the constraint. — market-tick-data-service@01912df09c:
      confirmed both call sites (`_fetch_extended_candles_for_symbol`, `fetch_extended_candles`) always pass
      `interval="PT1M"` over a single UTC day; added a docstring to `_extended_candle_params` stating this call-graph
      invariant explicitly and warning any future caller that widens the window/interval to either add real
      multi-request chunking or make the cap-exceeded branch fail loud/route to attempted_failed instead of relying on
      the existing warning-only clip. No behavior change (comment-only), QG green.
- [x] ✅ [CODE] P3. **`UniswapV3Adapter._download_swaps`/`_download_pool_hourly_data` — CORRECTION: the described
      `AttributeError` does not reproduce against the model this adapter actually imports.** The original finding's
      repro cited `_defi_graph_models.py` (this package's own copy, snake_case-field + `alias="camelCase"`) — but
      `uniswap_v3_adapter.py` imports `GraphUniswapSwap`/`GraphSwapTransaction`/`GraphPoolHourData` from
      `unified_api_contracts.external.thegraph` instead (`_defi_graph_models.py` is dead code per its own
      "TODO(GH-BACKLOG): replace with UAC imports and delete" docstring). UAC's models declare these fields as the
      literal camelCase GraphQL name directly — no alias — so `swap.amountUSD`/`item.periodStartUnix`/etc. (the
      ORIGINAL, pre-this-todo code) were already correct. A first attempt (market-tick-data-service@6da10ad1) "fixed"
      the code to snake_case attribute access, matching the wrong (unused) model, which broke the adapter against its
      real import — caught live by the new regression tests themselves (`AttributeError: 'GraphPoolHourData' object
      has no attribute 'period_start_unix'. Did you mean: 'periodStartUnix'?`) before shipping further, then corrected
      (`market-tick-data-service@c6ceadce` reverts to camelCase against the real UAC model + rewrites the existing
      `test_uniswap_v3_bar_edge.py` fixtures to build real `unified_api_contracts` model instances instead of the
      deprecated local module; `market-tick-data-service@102a66de38` fixes a wrong test assertion — UAC's
      `GraphPoolHourData` doesn't declare `feeGrowthGlobal0X128`/`1X128` at all, so the adapter's output has always
      silently carried `"0"` for those two regardless of the wire value, a genuine but separate, out-of-scope-here gap
      that would need a UAC schema change). Full regression coverage now exists exercising `_download_swaps`/
      `_download_pool_hourly_data` end-to-end with a non-empty page against the real model (previously untested in
      either direction) — QG green, 10934 passed. `UniswapV3Adapter` remains dormant (nothing in production
      instantiates it; `dex_swaps_handler.py`'s cascade is the real V3 swap/hourly path), so this closes as "already
      safe, now proven" rather than "bug fixed."

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
- **context-scout 2026-08-14**: populated context_scope (5 entries).
- 2026-08-16 (slot 12, data_engineering): shipped the Coinbase CDE futures-universe cap todo — see the todo's own
  evidence line above for detail. instruments-service@31de8c9bd1, QG green (141s), quickmerge landed + ancestry-verified
  on origin/live-defi-rollout. Remaining todos in this doc are still open.
- 2026-08-16 (slot 31, data_engineering): shipped the dormant prediction-market hard page-count ceiling todo (KALSHI-PERP
  / POLYMARKET-PERP) — see the todo's own evidence line above for detail. instruments-service@9e201ee0dd, QG green
  (202s), quickmerge landed + ancestry-verified on origin/live-defi-rollout. Also fixed a mechanical
  `xfail_skip_tracked_baseline.yaml` line-number drift (two pre-existing skip markers in the touched test files shifted
  from the new test code inserted above them — corrected the `line:` values only, scoped to the two instruments-service
  entries; did NOT run `--baseline-write` fleet-wide, which would have silently dropped every other repo's baselined
  entries). Remaining todos in this doc are still open.
- 2026-08-16 (slot 25, data_engineering): shipped the Morpho Blue skip-pagination-verification todo — see the todo's
  own evidence line above for detail. instruments-service@c9b7943f, QG green (123-126s), quickmerge landed +
  ancestry-verified on origin/live-defi-rollout. Remaining todos in this doc are still open.
- 2026-08-16 (slot 10, data_engineering): closed the MTDS prediction/transfer bounded max-page-loops todo as
  duplicate — see the todo's own evidence line above for detail. No code shipped (nothing to fix; both files already
  carry the CF-11 fix from a prior session). 2 todos remain open in this doc (`_umi_extended.py` candle-window
  chunking, `UniswapV3Adapter` aliased-field `AttributeError`).
- 2026-08-16 (slot 20, data_engineering): shipped the `_umi_extended.py` candle-window pagination todo (documentation
  option) — see the todo's own evidence line above for detail. market-tick-data-service@01912df09c, QG green,
  quickmerge landed + ancestry-verified on origin/live-defi-rollout (repo under heavy concurrent push churn today —
  took 5 quickmerge attempts, the first 4 killed mid-run by an AO server restart at 05:58, 5th succeeded after the
  server stabilized). 1 todo remains open in this doc (`UniswapV3Adapter` aliased-field `AttributeError`).

## Codex SSOTs

`/codex/02-data/instruments-foundation-and-catalogue-completeness.md` § 6.2/6.5,
`/codex/02-data/honest-absence-downstream-handling.md`.
