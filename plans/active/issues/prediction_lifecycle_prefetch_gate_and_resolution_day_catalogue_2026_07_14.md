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
