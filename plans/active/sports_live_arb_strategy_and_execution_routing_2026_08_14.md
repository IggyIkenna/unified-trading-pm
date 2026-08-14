---
doc_type: plan
title: Sports live arb — strategy detection migration + execution routing
summary: |
  Migrates the arb detection, lifecycle and sizing logic out of e2e-testing's live_arb_scanner into strategy-service's
  existing sports arb archetype, and wires execution routing per the operator model — Betfair direct, Unity for its own
  child books, SharpAPI-served books as wired stubs. Detection runs on the live union feed MTDS produces, matching books
  as they appear rather than against a fixed pair list.
status: active
nature: process
asset_group: [sports]
stage: [strategy]
repos: [strategy-service, execution-service, unified-api-contracts, e2e-testing]
scope: [engineer]
tags: [sports, arb, strategy, execution, live-trading, betfair, unity, sharpapi]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/02-venues/unity-integration.md,
    /codex/04-architecture/client-funds-isolation.md,
    /codex/04-architecture/promote-workflow-architecture.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
context_scope:
  [
    e2e-testing/scripts/sports/live_arb_scanner.py,
    strategy-service/strategy_service/adapters/sports/arbitrage_detector.py,
    strategy-service/strategy_service/position/core/sports_arb_engine.py,
    strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/sports_arb_dutching.py,
    strategy-service/strategy_service/adapters/sports_feature_subscriber.py,
    execution-service/execution_service/sports_execution/adapters/,
    unified-api-contracts/unified_api_contracts/internal/unity_child_books.py,
    /codex/02-venues/unity-integration.md,
  ]
depends_on:
  [
    sports_venue_universe_and_capability_route_axis_2026_08_14,
    mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14,
  ]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
source: Operator arb-scope ruling, 2026-08-14
---

# Sports live arb — strategy detection migration + execution routing

> **Track**: LOCAL / human plan (`assigned_vm: NA`). Hand to a Sonnet-5 worker; audit on completion.
>
> **Gated on** both the registry plan and the MTDS feeds plan — detection has nothing to consume until the union feed
> lands. `gate_on_depends: true`.

## What already exists (do not rebuild)

A `sports_arb` strategy mode is already declared in `strategy_service/config.py`, and these production modules exist:

| Module                                                                              | Role today                         |
| ----------------------------------------------------------------------------------- | ---------------------------------- |
| `strategy_service/adapters/sports/arbitrage_detector.py`                            | detection entry point              |
| `strategy_service/position/core/sports_arb_engine.py`                               | position/stake bookkeeping         |
| `strategy_service/engine/strategies/v2/arbitrage_structural/sports_arb_dutching.py` | the v2 archetype slot              |
| `strategy_service/adapters/sports_feature_subscriber.py`                            | consumes the sports feature stream |
| `strategy_service/risk/engine/sports_risk.py`, `pnl/engine/sports_pnl.py`           | risk + PnL legs                    |

Execution already has `sports_execution/adapters/`: `exchanges/betfair.py` (+ `betfair_order_mapping.py`),
`exchanges/matchbook.py`, `exchanges/kalshi.py`, `exchanges/polymarket_clob.py`, `bookmaker_api/onexbet.py`,
`aggregator/odds_api.py`, `paper/paper_betting.py`, and a complete `unity/` package (`bridge`, `multiplex`, `sidecar`,
`fill_reports`, `rollover_tracker`, `turnover_tracker`).

**The gap is not "no arb code" — it is that the e2e scanner carries materially more detection surface than production.**
The three production modules total ~646 lines; `live_arb_scanner.py` is ~2,900 and implements 3-way, back-lay,
draw-no-bet and 2-way-pair detection plus opportunity lifecycle tracking, staleness gating and stake allocation. Read
both sides before writing code and record the actual delta.

## What migrates, and where it lands

From `live_arb_scanner.py`, into strategy-service:

- `scan_arbs_for_event` — the per-event scan entry point
- `_check_3way_arb`, `_check_back_lay_arbs`, `_check_dnb_arbs`, `_check_2way_arbs`, `_check_2way_pair` — the detection
  family
- `_track_arb` — opportunity lifecycle (open / persist / close, and duration accounting)
- `_calc_stakes` — stake allocation across legs
- `_best_fresh_odds`, `_is_refreshed` — the staleness gate that stops an arb being "found" against a dead quote
- `_american_to_decimal` — price normalisation; check UAC does not already own this before porting

Explicitly NOT migrating: the scanner's feed runners (`_run_sharpapi_feed`, `_run_betfair_stream`,
`_run_polymarket_feed`, `_seed_oddsapiio_rest`) and its event-matching family — those are the MTDS plan's scope, and
duplicating them here is the failure this split exists to prevent.

## Execution routing model (operator, 2026-08-14)

> "Execution we go direct on Betfair, for Unity covers their bookmakers, for SharpAPI would be stubs but still wired."

| Route      | Venues                                                                      | Adapter                                                     |
| ---------- | --------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Direct     | `BETFAIR` (and the existing `MATCHBOOK` / `KALSHI` / `POLYMARKET` adapters) | `sports_execution/adapters/exchanges/`                      |
| Broker     | Unity's 10 child books                                                      | `sports_execution/adapters/unity/` multiplex                |
| Wired stub | SharpAPI-served books with no execution path                                | new stub adapter — registered, Protocol-conforming, no fill |

A wired stub must reject an order loudly with a typed reason and never paper-fill silently — a silent fill in a live
strategy is a fabricated position.

## Todos

### P0 — establish the delta

- [ ] [BACKEND] P0. Read `live_arb_scanner.py` and the three production arb modules side by side and write the
      function-level delta into this plan's Progress Log — DoD: a table naming, for each scanner function listed above,
      whether production already has an equivalent symbol, a partial one, or nothing.
- [ ] [BACKEND] P0. Confirm whether `_american_to_decimal` and the stake-allocation maths already exist in UAC or UTL
      before porting either — DoD: cite the grep; if an equivalent exists, the port reuses it rather than adding a
      second implementation.
- [ ] [BACKEND] P0. Capture a golden fixture from the scanner — a recorded multi-book quote set with known arb outcomes
      — DoD: a fixture file plus expected opportunities, so the migrated detector can be proven equivalent rather than
      merely green.

### P1 — migrate detection

- [ ] [BACKEND] P1. Port the detection family (3-way, back-lay, DNB, 2-way, 2-way-pair) into the existing
      `sports_arb_dutching` archetype slot, keeping the scanner's semantics and adding the archetype's typed signal
      output — DoD: the golden fixture produces the same opportunity set as the scanner, asserted
      opportunity-for-opportunity.
- [ ] [BACKEND] P1. Port the staleness gate (`_best_fresh_odds` / `_is_refreshed`) so a quote older than its
      per-provider freshness bound can never form an arb leg — DoD: a test where one leg is stale produces zero
      opportunities, and the freshness bound is config, not a literal.
- [ ] [BACKEND] P1. Port opportunity lifecycle tracking (`_track_arb`) into the archetype so an opportunity has
      open/close/duration state rather than being a per-tick boolean — DoD: a replayed quote sequence yields one
      opportunity with a measured duration, not N duplicates.
- [ ] [BACKEND] P1. Point detection at the live union feed the MTDS plan produces, matching books as they appear — the
      detector must not assume a fixed venue pair list — DoD: adding a venue to the registry brings it into scanning
      with no strategy-service code change; prove with a test that injects a new venue.
- [ ] [BACKEND] P1. Wire stake allocation through the existing `allocation_sizer` / `sports_arb_engine` rather than the
      scanner's standalone `_calc_stakes` path — DoD: sizing respects the existing per-client allocation guard, and a
      cross-client stake is impossible per `/codex/04-architecture/client-funds-isolation.md`.

### P1 — execution routing

- [ ] [BACKEND] P1. Build the venue-to-execution-route resolver keyed off the capability record's route axis from the
      registry plan — DoD: every canonical sports venue resolves exactly one of direct / broker / wired-stub, and an
      unroutable venue raises rather than defaulting.
- [ ] [BACKEND] P1. Route Unity's 10 child books through the existing `unity/multiplex.py` — DoD: an order for a Unity
      child book reaches the multiplex with the correct `child_venue_id`, verified against `UNITY_CHILD_BOOKS` rather
      than a hardcoded list.
- [ ] [BACKEND] P1. Ship the SharpAPI wired-stub adapter — registered in the execution adapter registry,
      Protocol-conforming, rejecting orders with a typed unsupported-route reason — DoD: a test asserts the stub never
      returns a fill and the rejection carries a typed reason code.
- [ ] [BACKEND] P1. Confirm the Betfair direct adapter covers the back-lay legs detection can now emit — DoD: a back-lay
      opportunity produces a valid Betfair order pair through `betfair_order_mapping.py`, or the gap is filed as a
      tracked todo here.
- [ ] [BACKEND] P1. Carry Unity's per-book commission into opportunity economics — commissions run 0% to 3% on wins per
      `UNITY_CHILD_BOOKS` and an arb that ignores them is not an arb — DoD: a fixture opportunity that is profitable
      gross and unprofitable net of commission is rejected; commissions come from the UAC record, not a constant.

### P2 — prove it before it trades

- [ ] [BACKEND] P2. Run the whole path in paper mode against the live feed and record opportunities without placing —
      DoD: a dated paper run with a non-zero opportunity count and per-opportunity provenance (which books, which
      prices, which timestamps).
- [ ] [BACKEND] P2. Reconcile paper against a batch rerun of the same window per the determinism spine — DoD:
      `paper(W) == batch-rerun(W)` for the recorded window, or a written explanation of every divergence; see
      `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`.
- [ ] [BACKEND] P2. Wire the archetype into the kill-switch bus so a feed outage stops new signals while allowing exits
      — DoD: simulating a dead provider trips `stop_new_signals` and existing opportunities can still close.
- [ ] [OPERATOR] P2. Decide the promotion gate from paper to live for this archetype — live sports betting moves real
      funds through a broker holding a single central wallet, so promotion is an operator call, not a plan default —
      DoD: the decision is recorded here with the criteria used.
- [ ] [BACKEND] P2. Retire `live_arb_scanner.py`'s detection half once production is equivalent, leaving a pointer —
      DoD: no second arb implementation survives, per the delete-deprecated-code rule; the scanner's feed half is
      retired by the MTDS plan, not this one.

## Definition of done for the whole plan

Arb detection runs inside the strategy-service archetype on the live union feed with staleness gating, lifecycle
tracking and commission-aware economics; every sports venue resolves exactly one execution route; Betfair executes
directly, Unity's books execute through the multiplex, SharpAPI books reject loudly; and a dated paper run reconciles
against a batch rerun of the same window.

## Progress Log

_(append dated entries here)_
