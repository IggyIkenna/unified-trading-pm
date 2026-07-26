---
doc_type: issue
title: Prediction fetch ignores lifecycle windows (post-fetch gate) + Polymarket day-catalogue is resolution-day-scoped
summary:
  Prediction backfill adapters load per-market lifecycle bounds BEFORE fetching but apply them AFTER the network call —
  every known conditionId/ticker is attempted every day and inactive days land as attempted `SOURCE_RETURNED_ZERO`
  `empty_confirmed` instead of no-fetch `EXPECTED_*` honest absence. Separately (verified filter, propagation
  unconfirmed), IS's Polymarket CLOB per-day catalogue is scoped to markets whose `end_date_iso` equals the target day —
  if that feeds the MTDS per-day cid list, backfills only ever attempt a market's trades on its RESOLUTION day.
status: open
nature: process
asset_group: [prediction]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [prediction, lifecycle, honest-absence, manifest, data-correctness, polymarket, kalshi, backfill, coverage]
related:
  [
    plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    plans/archive/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md,
    plans/active/issues/phantom_captures_prediction_2026_06_28.md,
    plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
  ]
created: 2026-07-14
parent_epic: predictions_master
priority: P0
source:
  [operator question 2026-07-14 (Honest Coverage panel review), read-only lifecycle-gating investigation (main session)]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-14
locked_since:
---

# Prediction lifecycle pre-fetch gate + resolution-day catalogue scoping (2026-07-14)

> Filed from the operator's question on the Honest Coverage panel ("don't we have a sense of initialization and expiry
> so we don't have to even attempt most days — like options?"). Answer: the machinery exists but is applied at the wrong
> point; and a second, potentially larger catalogue-scoping defect was found while verifying.

## Finding 1 — VERIFIED: lifecycle bounds applied post-fetch, not pre-fetch

- Both prediction adapters load per-market lifecycle bounds **before** fetching, then fetch **unconditionally**, then
  filter rows **after** the network call:
  - `market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py:706-756`
    — `_fetch_trades_for_date` loads `cid_to_lifecycle` then calls `get_trades_batch(list(cid_to_shard.keys()), …)` for
    EVERY known conditionId; gating happens only in `_apply_lifecycle_gate` (`:599-640`), called from
    `_aggregate_trade_results` (`_polymarket_helpers.py:193-234`) after the call.
  - `kalshi_adapter.py:287-327` — identical pattern (`ticker_lifecycles` loaded at `:307`, unconditional
    `get_trades_batch` at `:312`).
- Effect: inactive (market-not-yet-created / already-resolved) days consume real fetch attempts and land as
  `record_empty(SOURCE_RETURNED_ZERO)` `empty_confirmed` — the dominant mass behind the panel's PREDICTION bar (755,943
  shards, 6.0% captured, ~94% empty_confirmed).
- The enumerator side is fine and stays as-is: `enumerate_expected_universe.py:2223-2352` gates the cqg-bundle grain
  with `EXPECTED_INSTRUMENT_NOT_LISTED`/`EXPECTED_INSTRUMENT_DELISTED`; decision-338 (no per-conditionId EU seeding,
  > 50M-row rationale, `cross_ag_never_seeded_backlog_scan_2026_07_06.md` § prediction finding 3) is about denominator
  > bookkeeping and REMAINS IN FORCE — this issue is about attempt cost + honest-absence typing at capture time, which
  > no existing doc addresses.

## Finding 2 — filter VERIFIED, propagation HYPOTHESIS: resolution-day-scoped day-catalogue

- `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/clob.py:319-358`
  (`_fetch_clob_markets`): each per-date call filters the cached ~900K CLOB market list by
  `end_date_iso.startswith(f"{date}T")` — i.e. a backfill day D's catalogue contains ONLY markets **resolving** on D (a
  resolution-day filter, not an active-window filter).
- UNVERIFIED (P0 verify below): whether this day-catalogue feeds the MTDS per-day trades cid list and the
  `market_lifecycle/by_canonical_group/day={date}` store consumed by `_load_lifecycles_from_gcs`
  (`base_prediction_adapter.py:91-218`). If it does, backfills only ever attempt each market's trades on its resolution
  day — active-life trading volume is structurally never captured, which would be a major real coverage gap beneath the
  honest-absence story (Layer-2 reachable coverage was 22.73% on 2026-07-06).

## Todos

- [x] ✅ [VERIFY] P0. Trace the propagation: IS lifecycle/catalogue cron → `market_lifecycle/by_canonical_group/day=`
      store → `_load_lifecycles_from_gcs` → `cid_to_shard` (Polymarket) and the Kalshi equivalent. Quantify the
      distribution of (attempted day − market `end_date`) over a sampled backfill window; pull the existing
      `rejected_pre`/`rejected_post` gate counters from Cloud Logging rather than re-deriving. Gate: a one-page
      confirmed data-flow diagram + counts, appended here. — evidence: `unified-trading-pm@dea6c88fa` (Progress Log
      data-flow + real-GCS-partition A/B + Cloud Logging attempt, see entry above); verdict CONDITIONALLY CONFIRMED
      (resolution-day-scoped for backfilled dates, active-window for live-captured dates).
- [x] ✅ [CODE] P1. Pre-fetch lifecycle gate in both adapters: filter `cid_to_shard`/`ticker_lifecycles` to ids whose
      bounds overlap the target day BEFORE `get_trades_batch`, reusing `_apply_lifecycle_gate`'s bounds comparison as a
      pre-check. Skipped combos write typed no-fetch honest absence (`EXPECTED_INSTRUMENT_NOT_LISTED` /
      `EXPECTED_INSTRUMENT_DELISTED` via the sentinel path), NOT attempted `SOURCE_RETURNED_ZERO`; shard atom unchanged;
      decision-338 untouched (no new EU seeding). Gate: unit test — a pre-genesis and a post-resolution day for a
      fixture market produce zero network calls + EXPECTED_* rows; QG green. — evidence:
      `market-tick-data-service@abe0904d` (shared `compute_lifecycle_window_ts`/`classify_lifecycle_prefetch_skip`/
      `prefilter_ids_by_lifecycle_window` in `base_prediction_adapter.py`; pre-fetch gate in
      `polymarket_adapter.py::_fetch_trades_for_date` + `_polymarket_helpers.py::_prefilter_trade_cids`;
      `kalshi_adapter.py::_fetch_trades_for_date`; typed sentinel-path routing in
      `engine/orchestrator/sentinels.py::_emit_tier3_for_dt` via new
      `engine/orchestrator/     prediction_tier3_lifecycle.py`; fail-open coverage guard for the 07-01-outage class; 45
      new/updated unit tests across `test_polymarket_adapter_lifecycle_gating.py` /
      `test_kalshi_adapter_lifecycle_gating.py` / `test_sentinels_prediction_lifecycle_tier3.py`, all green; QG
      `.qg_last_passed_sha=f4b19bad2` == HEAD before quickmerge; 173 total tests re-run clean (36 new/touched + 137
      broader prediction/sentinel regression sweep, 0 failures)).
- [x] ✅ [CODE] P1 (contingent on the P0 VERIFY confirming propagation). Widen the per-day catalogue derivation from
      resolution-day-only to active-window (`created_at ≤ day ≤ end_date`) — MUST land together with (or after) the
      pre-fetch gate, otherwise attempt volume explodes. Gate: sampled day's cid list contains active non-resolving
      markets; attempt volume bounded by the gate; QG green. — evidence: `instruments-service@41ca79d7`
      (`clob.py::_fetch_clob_markets` active-window overlap + new `_clob_market_window_ts` bounds helper mirroring
      MTDS's `compute_lifecycle_window_ts` comparison; creation-date fields `start_date`/`startDate`/`created_at`/
      `createdAt` with `accepting_order_timestamp`/`game_start_time` fallback, fail-OPEN on unknown creation,
      fail-CLOSED on unknown `end_date_iso`; 7 new + 1 updated unit tests in
      `tests/unit/test_polymarket_boost.py::TestFetchClobMarkets` — active-not-resolving included / pre-created excluded
      / post-resolution excluded / resolution-day unchanged / creation fail-open / end-date fail-closed / fallback-field
      consulted — all green in full QG, exit 0, `.qg_last_passed_sha=7d8b1ed8`==pre-quickmerge HEAD; sampled-day gate
      PROVEN on real data: 2026-07-06 NEW catalogue = 97,113 markets of which only 10,089 resolve that day, see the
      quantification section below; Kalshi IS adapter audited — NO equivalent defect, already active-window, see the
      widening-scope section). Kalshi verdict: no change needed.
- [ ] [VERIFY] P2. Post-fix: re-measure prediction attempted/captured trajectory on a sampled window; append
      before/after counts here and to the coverage docs if the model description changes.
- [ ] [INFRA] P1 [BLOCKED-OPERATOR-DECISION]. Launch the historical prediction re-backfill under the widened catalogue —
      cost estimate in `## Re-backfill cost quantification` below (≈16.1M additional (conditionId × day) fetch attempts
      over 2025-03-14→2026-07-14, ≈9–11 days single-process wall-clock at the adapter's 20 req/s cap, ÷N for N sharded
      VMs; expected NEW captured cells order 10^6); operator go/no-go — this launch decision is explicitly reserved by
      the operator's 2026-07-14 dispatch (quantify, don't fire).

## Progress log

- 2026-07-14: Filed. Finding 1 verified read-only (file:line above); Finding 2's filter verified by direct read of
  `clob.py:335-341`, propagation deliberately left as the P0 VERIFY. Operator notified in the main session (big-finding
  rule: data-correctness class). No code changed.

- 2026-07-14 [VERIFY P0 — CONFIRMED, CONDITIONALLY]: Traced the full propagation + read real GCS partitions (read-only,
  no mutation). **Verdict: was active-life trading structurally never attempted? YES for backfilled historical days; NO
  for days captured by the live daily cron.** The catalogue scoping (resolution-day-only vs active-window) is not a
  fixed property of the pipeline — it's a property of WHICH CODE PATH populated a given day's catalogue.

  **Data-flow (confirmed, file:line):**
  1. `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/adapter.py:118-178`
     (`PolymarketReferenceDataAdapter.get_instruments`) branches on `date < today` (`:136-141` vs `:142-176`):
     - **PAST date** (`date < today` — i.e. any retroactive backfill run): `_fetch_clob_markets(date, now)` →
       `clob.py:319-358` → resolution-day-scoped filter (`end_date_iso.startswith(f"{date}T")`).
     - **TODAY/live** (`date is None` or `date == today`): Gamma API `active=true&closed=false` full active-markets
       listing (`:142-161`) — the FULL active-window universe, not resolution-day-scoped. (A same-day CLOB supplement at
       `:165-175` only registers `clob_token_ids` side-effect; it does not narrow the returned universe.)
  2. That day's catalogue (`_group_df_clean` in
     `instruments-service/instruments_service/engine/orchestrator/ process_write.py:280-406`) feeds BOTH stores MTDS
     reads, from the identical per-day DataFrame:
     - `market_lifecycle/by_canonical_group/day={date}/group={g}/venue={V}/market_lifecycle.parquet` via
       `_write_market_lifecycle` (`instruments-service/instruments_service/engine/orchestrator/writers.py:411-484`,
       called at `process_write.py:398-406`).
     - `instrument_availability/by_date/.../instruments.parquet` (same function, `:330-344`).
  3. MTDS reads BOTH for the SAME day: `cid_to_shard` ← `_load_instruments_from_gcs` (Polymarket
     `polymarket_adapter.py:805-811`, reads `instrument_availability`); `cid_to_lifecycle`/`ticker_lifecycles` ←
     `_load_lifecycles_from_gcs` → `_load_market_lifecycle_for_date`
     (`market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/ base_prediction_adapter.py:91-218`,
     PRIMARY path reads `market_lifecycle/by_canonical_group/day={date}/`). Since both GCS stores are written from the
     identical per-day IS catalogue snapshot, **both inherit whichever scoping that day's IS catalogue fetch used** —
     there is no independent widening/narrowing between the two stores.

  **Empirical GCS reads (bucket `instruments-store-pred-prd-central-element-323112`, read-only):**
  - `day=2026-07-06/group=BTC_UP_DOWN_DAILY/market_lifecycle.parquet`: 318 rows — 268 resolve ON 2026-07-06, **50 are
    active but resolve LATER** (non-resolution-day markets present). Every row's `available_at` ≈
    `2026-07-06T14:19:58Z`/`14:20:35Z` — i.e. **written ON that same calendar day** → this partition was populated by
    the LIVE/current-day Gamma active-markets path (confirms active-window scoping for live-captured days).
  - `day=2026-07-06/group=CPI_PRINT_PER_MONTH`: 1 row, `market_created_at=2026-06-10`, `settlement_time=2026-07-15`
    (resolves 9 days LATER, not that day) — a genuinely long-lived active market correctly present in a live-captured
    day's snapshot.
  - `day=2025-03-14/group=BTC_UP_DOWN_DAILY/market_lifecycle.parquet`: **1 row**, resolves EXACTLY on 2025-03-14
    (`settlement_time=2025-03-14T02:00:00Z`), `available_at=2026-06-26T17:38:10Z` — **written 15+ months after the
    partition's own day** → this was a retroactive BACKFILL run. The row set is 100% resolution-day-scoped: zero
    active-non-resolving rows, exactly the failure mode Finding 2 hypothesized.
  - `day=2026-06-28` through `day=2026-07-03`: **zero objects** (`gcloud storage ls` → "matched no objects") — the known
    cron-paused gap (`prediction_capture_incident_remediation_2026_07_06.md`); confirms these days were never attempted
    at all (not a resolution-day artifact — genuinely absent).

  **Distribution / counts**: not quantified as a full-corpus histogram (would require a whole-store walk, which is
  review-blocking per single-walk discipline outside a dedicated backfill/audit plan) — the two-partition A/B comparison
  above (a definitively LIVE-captured day vs a definitively BACKFILLED day) is sufficient to CONFIRM the conditional
  propagation mechanism with direct evidence rather than inference. A full quantification (what fraction of the corpus
  is backfill-scoped vs live-scoped) is exactly what the contingent catalogue-widening item below would need to size —
  see its write-up.

  **Cloud Logging (`rejected_pre`/`rejected_post` counters)**: attempted via `gcloud logging read` against project
  `central-element-323112`. Broad `resource.type="gce_instance" AND textPayload:"..."` queries reliably TIMED OUT
  (>60-90s) even at 1-2 day freshness with `limit=5`; a baseline no-filter query returned in <1s, confirming the
  project's Cloud Logging is reachable but full-text `textPayload:` search is prohibitively slow without a `logName`
  restriction. Narrowed to `logName="projects/central-element-323112/logs/python"` (the stream carrying this workspace's
  live/paper Python process logs) — that query returns fast but **zero matches** for `"PolymarketAdapter"`,
  `"KalshiAdapter"`, or `"lifecycle gating"` over a 90-day freshness window. Verdict: **not reachable** — prediction
  backfill VM runs either don't ship structured logs to this sink, or none ran with this log line active in the sampled
  90-day window. Per the todo's "if reachable" qualifier, this is a clean negative rather than a blocker; the
  GCS-partition A/B comparison above is the load-bearing evidence for this VERIFY.

- 2026-07-14 [CODE P1 — SHIPPED, `market-tick-data-service@abe0904d`]: Implemented the pre-fetch lifecycle gate exactly
  as scoped (adapters + the Tier-3 sentinel-path typed reason; no catalogue widening — see below).
  - **Shared bounds SSOT**: extracted `compute_lifecycle_window_ts` / `classify_lifecycle_prefetch_skip` /
    `prefilter_ids_by_lifecycle_window` into `base_prediction_adapter.py` — the exact bounds comparison
    `_apply_lifecycle_gate` (Polymarket) and `_collect_kalshi_frames` (Kalshi) already used for the post-fetch gate, now
    reused for the NEW pre-fetch gate so both layers can never disagree. Both post-fetch gates were refactored to call
    the shared helper (behavior-preserving; only a sub-second-truncation edge case, already Polymarket's convention, is
    now uniform across both venues).
  - **Pre-fetch gate**: `polymarket_adapter.py::_fetch_trades_for_date` (+
    `_polymarket_helpers.py:: _prefilter_trade_cids`) and `kalshi_adapter.py::_fetch_trades_for_date` (new, extracted
    from `download_batch` to stay ≤50L) now filter the known-id list to ids whose lifecycle window overlaps the target
    day BEFORE `get_trades_batch` — zero network calls for out-of-window ids. Fail-open guard
    (`_MIN_LIFECYCLE_COVERAGE_FRACTION=0.5`): an empty or suspiciously-small lifecycle map bypasses gating entirely for
    that day (fetches every known id, logs a WARNING) — the 07-01-outage-class guard the task required.
  - **Typed no-fetch honest absence via "the sentinel path"**: `engine/orchestrator/sentinels.py::_emit_tier3_for_dt`
    (new `engine/orchestrator/prediction_tier3_lifecycle.py` module, extracted to stay ≤900L) now classifies each
    expected-but-uncaptured POLYMARKET/KALSHI `trades` instrument_id via the SAME bounds comparison and routes to
    `record_expected_empty(reason=EXPECTED_INSTRUMENT_NOT_LISTED|EXPECTED_INSTRUMENT_DELISTED)` instead of the fallback
    `record_empty(reason=SOURCE_RETURNED_ZERO)` — scoped to POLYMARKET/KALSHI `trades` only (verified via a dedicated
    regression test that BINANCE/other dts never touch the new lifecycle loader). Decision-338 untouched: no new
    manifest rows/EU-seeding at per-conditionId grain in the enumerator — this only re-types the reason on rows that
    already exist in the Tier-3 fan-out today.
  - **Post-fetch gate kept as defense-in-depth** (unchanged behavior, just refactored onto the shared helper).
  - **Tests**: 45 new/updated unit tests (pre-genesis / post-resolution / empty-map-bypass / active-window-fetched ×
    both adapters + 6 new sentinels.py Tier-3 tests) — all green; a 137-test broader regression sweep across
    prediction/sentinel/manifest-finalize/CF-11 test files — 0 failures. QG `.qg_last_passed_sha=f4b19bad2` ==
    pre-quickmerge HEAD; quickmerge landed `abe0904d` on `live-defi-rollout` (confirmed ancestor of
    `origin/live-defi-rollout`).
  - See `## Catalogue-widening scope (contingent P1 — NOT implemented this pass)` below for the item deliberately
    deferred per the task's explicit instruction (now CONFIRMED necessary by the P0 VERIFY, not merely hypothesized).

- 2026-07-14 [CONTINGENT CODE P1 — SHIPPED, `instruments-service@41ca79d7`]: Widened `clob.py::_fetch_clob_markets` from
  resolution-day-only to active-window overlap, exactly per the widening-scope section below (which is now historical:
  "NOT implemented this pass" refers to the abe0904d pass).
  - **Filter**: keep a market when its `[created, resolved)` window overlaps `[day 00:00Z, day+1 00:00Z)`. New
    `_clob_market_window_ts()` mirrors MTDS `base_prediction_adapter.compute_lifecycle_window_ts` bit-for-bit (date-only
    settlement extended to end-of-day) — REIMPLEMENTED locally, not imported (no T4 service→service dep).
  - **Fields chosen** (verified against the UAC `PolymarketGammaMarket` schema + `markets.py`'s 43a enrichment note):
    creation = first non-empty of `start_date`/`startDate`/`created_at`/`createdAt`, falling back to
    `accepting_order_timestamp`/`game_start_time` (the raw CLOB `/markets` shape usually lacks the gamma creation fields
    entirely — the fallbacks are the CLOB-native listing-date proxies). Unknown creation → FAIL OPEN (include from
    earliest known; per the dispatch instruction). Settlement = `end_date_iso` (raw key, `endDateIso` alias fallback);
    unknown settlement → FAIL CLOSED (the old filter already required it; fail-open here would put unbounded markets in
    EVERY day's catalogue).
  - **Kalshi IS adapter audited — NO defect** (see the widening-scope section's Kalshi bullet):
    `kalshi.py:: _fetch_markets_page:463-471` already keeps `open_d <= target <= close_d` (active-window), and deep
    pre-cutoff dates route to honest-absence, not a narrowed catalogue. No change made.
  - **Tests**: 7 new + 1 updated in `tests/unit/test_polymarket_boost.py::TestFetchClobMarkets` (active-not-resolving
    included / pre-created excluded / post-resolution excluded / resolution-day unchanged / creation fail-open /
    end-date fail-closed / `game_start_time` fallback consulted / validation-error continue) — all green inside full QG
    (`--no-fix`, exit 0, `.qg_last_passed_sha=7d8b1ed8` == pre-quickmerge HEAD, re-run FRESH after `31c15d88`/`7d8b1ed8`
    moved the tree mid-session); quickmerge landed `41ca79d7` on `live-defi-rollout` (confirmed ancestor of origin).
    Test docstrings state the volume rationale: attempt volume stays bounded because the MTDS pre-fetch gate (abe0904d)
    re-applies the same bounds before any network call.
  - **Quantification**: see `## Re-backfill cost quantification` below — measured by running BOTH filter predicates (the
    shipped code, not a model) over a real 1,801,017-market CLOB scan for 6 sampled days; ≈16.1M additional (cid × day)
    attempts for a full-history re-backfill, ≈9–11 days single-process at 20 req/s (÷N sharded), new captured cells
    order 10^6. The launch itself is the new [INFRA] P1 BLOCKED-OPERATOR-DECISION todo.

## Catalogue-widening scope (contingent P1 — NOT implemented this pass)

Per the P0 VERIFY above, this item is now CONFIRMED necessary (not merely hypothesized) for the backfilled portion of
the historical corpus. Scope, written up per instruction rather than implemented:

- **What changes**:
  `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/ clob.py:319-358`
  (`_fetch_clob_markets`) filters `raw_markets` by `end_date_iso.startswith(f"{date}T")` (resolution day only). Widen to
  an ACTIVE-WINDOW filter: keep a market when `start_date ≤ day_end AND end_date_iso > day_start` (i.e. the market's
  `[created, resolved)` window overlaps the requested day) — the SAME semantics the new `market-tick-data-service`
  shared helper `base_prediction_adapter.classify_lifecycle_prefetch_skip`/`compute_lifecycle_window_ts` already encode
  for MTDS's gates (2026-07-14, this issue's Finding 1 fix); IS's widened filter should mirror that comparison so both
  services agree on "what counts as active that day."
- **Kalshi side — AUDITED, NO DEFECT FOUND (2026-07-14)**:
  `instruments-service/instruments_service/reference_data/ adapters/prediction/kalshi.py::KalshiReferenceDataAdapter._fetch_markets_page`
  (`:369-479`) already implements an ACTIVE-WINDOW filter for a dated (historical) call, not a resolution-day filter:
  `:463-471` parses `open_time` / `close_time` per raw market and keeps it only when
  `open_d is not None and close_d is not None and open_d <= target <= close_d` — i.e. the market's `[open, close]`
  trading window must SPAN the target date, the exact active-window semantics Polymarket's `_fetch_clob_markets` lacked.
  Kalshi's `get_instruments(date=...)` (`:271-367`) routes a PAST date to `/historical/markets` (signed, newest-first
  cursor pagination, `_MAX_HISTORICAL_PAGES=40`) with this per-page filter applied client-side; deep pre-cutoff dates
  beyond `_HISTORICAL_GAP_EDGE_DAYS=3` from the live/historical boundary return honest-absence (`:303-316`) rather than
  a false-narrow catalogue, so there is no resolution-day-scoping analog to fix. **No code change made to `kalshi.py`.**
- **Ordering dependency (why this waits on Finding 1's fix, not the reverse)**: the MTDS pre-fetch gate MUST land BEFORE
  (or with) this widening — otherwise widening the catalogue explodes attempt volume: EVERY (venue, active-window-day)
  pair becomes a fetch attempt again, undoing the whole point of this issue. With the pre-fetch gate live (shipped this
  pass), a widened catalogue instead produces MORE `cid_to_shard` entries per day, but the pre-fetch gate still filters
  to the ones actually in-window — net effect is bounded, not explosive.
- **Backfill cost**: widening the catalogue for FUTURE backfill runs is cheap (same CLOB scan, different filter
  predicate — `_get_raw_clob_markets_cached` already caches the full ~900K-market scan per process). The bigger cost is
  RE-BACKFILLING the historical corpus that was ALREADY captured resolution-day-scoped (e.g. the 2025-03-14 partition
  above) — that is a full re-run of IS's catalogue step for every historical day, which is exactly the kind of
  multi-week compute-cost decision that needs an operator call, not an autonomous one.
- **Verification gate** (per the original todo text): a sampled day's cid list must contain active non-resolving markets
  after the fix (repeat the `day=2025-03-14`-style A/B read above and confirm the resolving-vs-active-not- resolving
  ratio now resembles the `day=2026-07-06` live-captured shape); attempt volume must stay bounded by the MTDS pre-fetch
  gate (already shipped); QG green in instruments-service.
- **Recommended sequencing**: (1) already done — MTDS pre-fetch gate (this issue, Finding 1). (2) Kalshi IS-adapter
  audit for the same defect. (3) Widen `_fetch_clob_markets` (+ Kalshi equivalent if found) behind an operator-reviewed
  plan, since it changes attempt volume materially and gates a historical re-backfill cost/benefit call. (4) Re-measure
  per this issue's P2 VERIFY todo.

## Re-backfill cost quantification (2026-07-14, contingent-P1 pass — real data, read-only)

**Method.** One bounded full CLOB `/markets` scan (the SAME scan every IS backfill process pays once —
`_get_raw_clob_markets_cached`), then for each of 6 sampled days, both filter predicates were executed over the
identical in-memory corpus: (a) OLD = the pre-fix resolution-day predicate (`end_date_iso.startswith(f"{date}T")`), (b)
NEW = the shipped `instruments-service@41ca79d7` active-window `_fetch_clob_markets` (actual production code, not a
reimplementation). NEW_w/lifecycle = the subset of NEW producing a strict `MarketLifecycle` row (`classify_lifecycle()`
— exactly what the `market_lifecycle/by_canonical_group/` store MTDS's pre-fetch gate reads is built from). Scan
measured **1,801,017 markets in 660.7 s** (~11 min; the "~900K" figure in older docs is stale). No GCS whole-corpus walk
(single-walk discipline): the only GCS reads were the 6 day-partitions (bounded).

**Measured per-day counts:**

| day        | OLD (resolution-day) | NEW (active-window) | NEW w/ strict lifecycle row | additional (NEW−OLD) | lifecycle coverage of NEW |
| ---------- | -------------------: | ------------------: | --------------------------: | -------------------: | ------------------------: |
| 2025-03-14 |                  157 |               6,030 |                       4,343 |                5,873 |                       72% |
| 2025-06-15 |                  378 |               8,107 |                       6,426 |                7,729 |                       79% |
| 2025-09-15 |                1,250 |              14,807 |                      13,257 |               13,557 |                       90% |
| 2025-12-15 |                1,301 |              31,637 |                      30,327 |               30,336 |                       96% |
| 2026-03-15 |                8,317 |              62,625 |                      61,769 |               54,308 |                     98.6% |
| 2026-07-06 |               10,089 |              97,113 |                      96,757 |               87,024 |                     99.6% |

**MTDS pre-fetch gate interaction (abe0904d):** every NEW market's lifecycle window overlaps its day BY CONSTRUCTION
(IS's widened filter mirrors the gate's own bounds comparison), so the gate passes ~all of NEW; the (NEW −
NEW_w/lifecycle) sliver lacks a strict lifecycle row and FAILS OPEN in the gate (fetched anyway). Lifecycle coverage of
NEW is ≥72% on every sampled day — comfortably above the gate's 50% fail-open-bypass threshold, so gating stays ACTIVE
(no bypass day). Net: **per-day fetch attempts ≈ NEW**; what the gate protects against is the pre-widening
catalogue×gate mismatch and out-of-window ids, not this in-window growth.

**Extrapolation (trapezoid over the 6 samples, 2025-03-14 → 2026-07-14 = the existing 482-partition corpus):**

- Additional (conditionId × day) fetch attempts: **≈ 16.1M** (segment sums 0.63M + 0.98M + 2.00M + 3.81M + 7.99M +
  0.70M). OLD-filter total ≈ 1.77M → NEW total ≈ 17.9M ≈ **10.1×** the old attempt volume.
- Wall-clock at the adapter's observed/configured throughput (MTDS `_POLYMARKET_RATE_PER_SEC = 20` req/s token bucket,
  `get_trades_batch max_concurrent=10`; inactive-day cids cost 1 data-api request each): 16.1M ÷ 20/s ≈ 805 ks ≈ **9.3
  days single-process**; ~11 days at a pagination-inclusive ~1.2 req/pair. Sharded across N workers (Polymarket rate
  limits are per-process/IP; no Tardis-style fleet cap applies): **÷N — e.g. ~2.5–3 days on 4 SPOT VMs**. The IS
  catalogue re-derivation itself is negligible: one ~11-min CLOB scan per process + in-memory per-day filtering.
- Expected NEW captured rows (order-of-magnitude): the current corpus captures 6.0% of attempts under
  resolution-day-biased scoping (where trade incidence peaks); mid-life days trade less for most markets, but every
  widening addition is definitionally an open, live market. At a 3–10% ≥1-trade incidence band on the 16.1M additional
  attempts: **~0.5M–1.6M new captured (cid × day) cells — order 10^6**. Trade-ROW volume is dominated by the small
  high-volume cohort (crypto up/down, major politics), so cell count is the honest metric.

**Caveats:** (1) The NEW/OLD ratio FALLS over time (38× → 10×) — recent days are dominated by short-cycle (5m/15m
up-down, per-match ITF) markets that live <1 day and appear in exactly one day's catalogue under BOTH filters; the
widening's additional mass is multi-day markets. (2) Mid-month spot samples; sports-calendar variance not modeled. (3)
Window = the existing backfilled corpus (2025-03-14 →); extending earlier grows the numbers — no partitions exist there
today. (4) Cross-check: the 2025-03-14 GCS partition (backfilled) holds 155 rows vs OLD live-count 157 (2 parse-dropped)
— corpus↔live-API consistent; the 2026-07-06 LIVE-captured partition holds 4,592 rows vs NEW=97,113, i.e. even
live-captured days would widen ~20× on re-backfill (the live Gamma path snapshots currently-tradeable markets, not the
full CLOB active-window universe).
