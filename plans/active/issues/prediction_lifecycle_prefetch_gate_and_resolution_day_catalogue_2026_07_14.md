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
    plans/active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md,
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

- [ ] [VERIFY] P0. Trace the propagation: IS lifecycle/catalogue cron → `market_lifecycle/by_canonical_group/day=` store
      → `_load_lifecycles_from_gcs` → `cid_to_shard` (Polymarket) and the Kalshi equivalent. Quantify the distribution
      of (attempted day − market `end_date`) over a sampled backfill window; pull the existing
      `rejected_pre`/`rejected_post` gate counters from Cloud Logging rather than re-deriving. Gate: a one-page
      confirmed data-flow diagram + counts, appended here.
- [ ] [CODE] P1. Pre-fetch lifecycle gate in both adapters: filter `cid_to_shard`/`ticker_lifecycles` to ids whose
      bounds overlap the target day BEFORE `get_trades_batch`, reusing `_apply_lifecycle_gate`'s bounds comparison as a
      pre-check. Skipped combos write typed no-fetch honest absence (`EXPECTED_INSTRUMENT_NOT_LISTED` /
      `EXPECTED_INSTRUMENT_DELISTED` via the sentinel path), NOT attempted `SOURCE_RETURNED_ZERO`; shard atom unchanged;
      decision-338 untouched (no new EU seeding). Gate: unit test — a pre-genesis and a post-resolution day for a
      fixture market produce zero network calls + EXPECTED_* rows; QG green.
- [ ] [CODE] P1 (contingent on the P0 VERIFY confirming propagation). Widen the per-day catalogue derivation from
      resolution-day-only to active-window (`created_at ≤ day ≤ end_date`) — MUST land together with (or after) the
      pre-fetch gate, otherwise attempt volume explodes. Gate: sampled day's cid list contains active non-resolving
      markets; attempt volume bounded by the gate; QG green.
- [ ] [VERIFY] P2. Post-fix: re-measure prediction attempted/captured trajectory on a sampled window; append
      before/after counts here and to the coverage docs if the model description changes.

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

- 2026-07-14 [CODE P1 — SHIPPED]: Implemented the pre-fetch lifecycle gate exactly as scoped (adapters only, no
  catalogue widening). See `## Catalogue-widening scope (contingent P1 — NOT implemented this pass)` below for the item
  deliberately deferred per the task's explicit instruction.

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
- **Kalshi side**: Kalshi's IS adapter
  (`instruments-service/instruments_service/reference_data/adapters/prediction/ kalshi.py`) was NOT inspected for an
  equivalent per-date filter in this pass — must be checked for the same resolution-day-vs-active-window distinction
  before/alongside the Polymarket fix (Kalshi's MTDS-side lifecycle store is fed by the SAME
  `market_lifecycle/by_canonical_group/` writer, so if Kalshi's IS-side catalogue fetch has an analogous per-date
  filter, it needs the identical widening).
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
