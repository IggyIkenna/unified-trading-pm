---
doc_type: issue
title: >-
  Prediction cross-venue arb has NO live execution path — the AtomicInstruction→adapter bridge does not exist (blocks
  LIVE for the existing 2-venue Kalshi↔Polymarket arb AND the new 3-venue Betfair arb); Betfair place_bet is BACK-only
  (no LAY)
summary: >-
  The v2 ARBITRAGE_PRICE_DISPERSION cross-venue-prediction engine emits a correct AtomicInstruction (LEADER_HEDGE box,
  per-venue legs), and the features+strategy layers are now 3-venue-wired (features@ce02e093 kernel/de-vig reader +
  strategy@137604c0 N-venue scan / Betfair leg / EPL template, PAPER-verified). But NOTHING executes it: the v2
  AtomicHandler.handle is observability-only (returns metadata + a compensation_watcher followup, calls NO adapter), and
  no code iterates instruction.legs → a concrete execution adapter. The legacy live path
  (cli/handlers/live_execution_handler.py) routes by params["operation"] and needs a pre-built bet_order + a registered
  BettingAdapter — a prediction AtomicLeg (no operation=BET, no bet_order) never reaches it; and the live sports factory
  registers only betfair+matchbook (the kalshi/polymarket CLOB adapters exist but are unwired). On top of that, Betfair
  place_bet hardcodes side="B" (BACK) and BetOrder has no side field (the BACK/LAY BetSide enum exists but is unused),
  so the SELL-YES (lay) hedge leg is inexpressible even once bridged. Net: the 3-venue (and even the pre-existing
  2-venue) prediction arb is PAPER/BACKTEST-only until this bridge is built. Separately, the downstream
  cross_venue_arb_detector.py computes net_edge_after_fees + max_arb_contracts on the Kalshi/Polymarket legs ONLY, so a
  Betfair-cheap-BUY opportunity currently surfaces as a NON-executable PURE_ARB flag until the detector/runner are
  extended to fee-net + size the Betfair leg.
status: open
nature: issue
asset_group: [prediction]
stage: [strategy]
repos: [execution-service, strategy-service, features-service, unified-api-contracts]
scope: [engineer, admin]
tags: [prediction-arb, cross-venue, betfair, execution-bridge, atomic-instruction, football-arb, live-blocker]
related: [prediction_consolidated_closeout_2026_07_18.md]
created: 2026-07-20
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 4.0
assigned_role: strategy
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source:
  [
    "discovered 2026-07-20 during the operator-authorized football 3-venue arb wiring (Kalshi↔Polymarket↔Betfair); the
    design investigation traced the emitted AtomicInstruction end-to-end and found no leg→adapter executor",
  ]
---

# Prediction cross-venue arb — the missing live execution bridge

**This is the gate to a LIVE prediction arb (2-venue or 3-venue). The signal side is done + verified; the execution side
does not exist.** Everything below was traced read-only against HEAD; file:line anchors are exact.

## What EXISTS (verified, working, PAPER)

- **Signal / features** — `features-service@ce02e093`: the cross-venue kernel is 3-venue (kalshi/polymarket/betfair YES
  bid/ask, all-pairs directional edges, `xv_best_edge`), and a de-vig reader (`prediction_cross_venue_betfair.py`) turns
  persisted Betfair h2h BACK odds → `betfair_yes_ask` (joined by `af_fixture_id`). Betfair absent → byte-identical to
  the 2-venue baseline. De-vig math hand-verified.
- **Strategy / engine** — `strategy-service@137604c0`: N-venue best-pair scan (`prediction_venue_dispersion.py`), engine
  leg-routing includes Betfair (`price_dispersion.py::_on_tick_cross_venue_prediction`), + a PAPER-only EPL config
  template (`configs/prediction_arb_epl.yaml`, every money/league field flagged OPERATOR-DECISION).
- **Betfair execution adapter** — `execution_service/sports_execution/adapters/exchanges/betfair.py`: a REAL impl
  (`place_bet` L491, `get_odds` L279, `_submit_place_orders` L398), `is_execution_venue: True`
  (`uac registry/_odds_api_maps.py` L170), reachable via `SportsExecutionRouter.get_adapter("betfair")`
  (`sports_execution/routing.py` L152-210).

## What is MISSING (the live blocker) — 5 components

1. **AtomicInstruction → leg → adapter DISPATCHER (does not exist — the core gap).** The engine emits an
   `AtomicInstruction`/`AtomicLeg`s (`strategy .../price_dispersion.py` L324-356), the v2 router accepts it
   (`execution_service .../v2/router.py` L103-120), but `AtomicHandler.handle` (`execution_service .../v2/handlers.py`
   L287-308) is **observability-only** — it returns venue/legs metadata + `followups=("compensation_watcher",)` and
   **calls no adapter**. No code anywhere iterates `instruction.legs` and maps each `AtomicLeg.venue` → a concrete
   adapter + a venue-native order. **This blocks the existing 2-venue live arb too, not just Betfair.** → Build the leg
   dispatcher (leg.venue → `SportsExecutionRouter.get_adapter` / prediction-CLOB adapter → construct + submit the native
   order; wire the compensation/hedge-deadline path).
2. **Live sports factory registers only betfair+matchbook**
   (`sports_execution/adapters/sports_factory.py::_LIVE_VENUE_CONFIGS` L23-36). The kalshi/polymarket CLOB adapters
   exist (`sports_execution/adapters/exchanges/kalshi.py`, `polymarket_clob.py`; router `_build_adapter` supports
   `kalshi_direct`/`polymarket_clob` routing.py L202-203) but are **not wired into the live factory**. → Register
   kalshi/polymarket/betfair.
3. **Betfair LAY not expressible** — `_build_place_instruction` hardcodes `side="B"` (BACK) (`exchanges/betfair.py`
   L458-468), and `BetOrder` (`sports/betting.py` L76-97) has **no side field** (the `BetSide` BACK/LAY enum L29-33
   exists, unused). So even once bridged, the SELL-YES (lay) hedge leg cannot be placed. → Add `side: BetSide` to
   `BetOrder` + honour it in `_build_place_instruction`.
4. **Downstream detector fee-nets + sizes only the 2-venue legs** — `cross_venue_arb_detector.py` (features-service, NOT
   touched by the wiring) consumes the Betfair-influenced `xv_best_edge` as `raw_edge` but computes
   `net_edge_after_fees` + `max_arb_contracts` on the Kalshi/Polymarket legs only; `is_executable` stays gated on the
   2-venue net edge (so **no false-executable is emitted** — safe), but a Betfair-cheap-BUY opportunity surfaces as a
   non-executable `PURE_ARB` until the detector + runner are extended to fee-net (incl. Betfair commission) + size the
   Betfair leg. → Extend the detector/runner.
5. **Two-sided (back+lay) Betfair odds source** — the persisted `CanonicalOdds` (`sports/odds.py` L73-99) is BACK-only
   (`_get_best_back_price`), so `betfair_yes_bid` is always None → Betfair can be the BUY-YES side but never the
   SELL-YES side. The lay-side de-vig is already documented + the kernel edge is already wired, so **SELL-Betfair lights
   up automatically once a lay book lands**. → Widen `CanonicalOdds` to carry lay + persist the exchange back+lay book
   (MTDS sports-odds pipeline) OR read `BetfairAdapter.get_odds` live.

## Also true / context

- **Data is seasonal**: `betfair_yes_ask` (and `af_fixture_id` on the prediction side) only populate when there are live
  fixtures + captured odds — off-season European soccer (e.g. July EPL) → honest-None → 2-venue fallback. Verify
  in-season.
- **Economics**: `entry_threshold` must clear Betfair exchange commission (~2-5% on net lay winnings) +
  Kalshi/Polymarket taker fees before edge is real profit — an operator-set number in the EPL template, not a code
  constant.
- **OPERATOR DECISIONS (not code)**: leagues / `canonical_question_group`, `stake_fraction`, `entry_threshold`,
  `edge_size_cap`, `max_position_usdc`, paper-vs-live promotion (May-23 gate), and Betfair account funding + API
  credentials + jurisdiction/regulatory sign-off for real-money sports betting.

## Suggested ordering (its own plan when scheduled)

`[1]` BetOrder `side: BetSide` + Betfair LAY (small, unblocks the hedge leg) → `[2]` the AtomicInstruction→adapter leg
dispatcher (the core; also unblocks 2-venue live) → `[3]` register kalshi/polymarket in the live sports factory → `[4]`
extend `cross_venue_arb_detector` + the runner to fee-net + size the Betfair leg → `[5]` two-sided back+lay odds
persistence for SELL-Betfair. `[1]`–`[3]` deliver a live 2-venue (and BUY-Betfair) arb; `[4]`–`[5]` complete the full
3-way. Gate the whole thing behind paper→live promotion + the operator's account/credential/jurisdiction sign-off.
