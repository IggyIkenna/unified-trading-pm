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

---

## UPDATE 2026-07-20 (autonomous run) — items [1]–[4] SHIPPED; the LIVE seam is now the single blocker

Operator answered the gating questions (**paper-only, no Betfair account yet**, all soccer, `entry_threshold` 0.03,
`stake_fraction` 0.05, `max_position_usdc` 1000, `edge_size_cap` 0.10) and authorised building the bridge. Shipped +
adversarially verified since:

- **[1] BetOrder LAY + lay-capable odds model + Betfair fee** — `unified-api-contracts@de6409e5`
  (`BetOrder.side: BetSide=BACK`, `CanonicalOdds.*_lay_odds`, `BETFAIR_COMMISSION_FRACTION=0.05` + `betfair_fee()`).
- **[2]+[3] the leg dispatcher + venue registration** — `execution-service@db75d51d`: new `v2/atomic_leg_executor.py`
  (`atomic_leg_to_bet_order` + `AtomicLegExecutor.execute` honouring LEADER_HEDGE: leader first, hedge within
  `hedge_deadline_ms`, `CLOSE_LEADER_IF_HEDGE_FAILS` → leader unwound, `naked_position=False`), adapter obtained via
  `create_sports_adapter(mode)` **defaulting to `OperationalMode.PAPER` → `PaperBettingAdapter`** (paper-safe by
  construction), plus kalshi/polymarket added to `_LIVE_VENUE_CONFIGS`.
- **[4] detector fee-net + 3-venue sizing** — `features-service@158515f3` (Betfair commission expr, best-pair net edge,
  Betfair back-only ⇒ BUY-side-only, no false-executable).
- **Entry gate GROSS→NET** — `strategy-service@31d6bb0d`: `select_prediction_arb_direction` now gates on
  `net_edge = edge − fee(buy_leg) − fee(sell_leg)` via the public UAC fee helpers; `signal.edge` stays GROSS (sizing +
  attestations) with a new `net_edge` field, pinned by test to equal `net_edge_sell_kalshi` /
  `net_edge_sell_polymarket`.
- **PAPER BACKTEST IS PROVEN WORKING** — `test_prediction_arb_3venue_paper_proof.py`: a crossed
  Kalshi/Polymarket/Betfair box **fires one LEADER_HEDGE `AtomicInstruction` and settles TWO benchmark fills with
  non-zero P&L** through the real paper runtime (`GroupBRunner` + `BenchmarkFillEngine`), plus a determinism test
  (identical fills across re-runs, `execution_alpha_bps == 0`). Config: `strategy-service@d07e7240` (all-soccer PAPER
  template, operator values).

### The single remaining LIVE blocker (needs an OPERATOR-DIRECTED architectural decision)

**There is no paper-LIVE / live tick runtime that routes an emitted `AtomicInstruction` to `AtomicLegExecutor`.** Traced
end-to-end: `emit_instructions` (`base.py:336-340`) only records; `V2EngineOrchestrator.on_tick` returns the list "for
the caller to forward to execution-service"; the ONLY realized caller is `GroupBRunner._process_tick`
(`backtest/runner.py:234-254`) → `BenchmarkFillEngine.settle` (the backtest/paper path, now proven). `AtomicLegExecutor`
and `V2InstructionRouter` are both **unwired** in production, and the legacy `live_execution_handler` speaks the old
single-`BET` `Instruction`, not `AtomicInstruction`/LEADER_HEDGE. **Tier rules forbid strategy-service importing
execution-service**, so the seam cannot be a direct call — it needs a transport decision (the UTL `EventTransport`
event-log seam is the architecturally-indicated option: strategy publishes envelopes, execution subscribes and routes
each atomic to the executor). That decision is the operator's; the cross-repo integration test belongs in
`e2e-testing`/`system-integration-tests` (which may import both).

### Smaller open items (documented, not blocking paper)

- **✅ FIXED 2026-07-20 — Compensation for a MATCHED leader**: the unwind was issuing `cancel_bet`, which is a NO-OP at
  the venue on already-matched stake — so the report could have claimed `naked_position=False` over a real open position
  (a false clean report on the real-money path). The unwind is now **status-aware**: `PENDING`/`PLACED` -> `cancel_bet`
  (genuinely pulls a resting order) · `MATCHED` -> a **real offsetting bet** on the opposite `BetSide` (a matched BACK
  is closed by a LAY) sized to the **FILLED** stake, not the requested stake · `PARTIALLY_MATCHED` -> cancel the resting
  remainder FIRST, then offset the filled portion · `SETTLED_*`/`REJECTED`/`CANCELLED` -> no open exposure, nothing to
  unwind (classified explicitly so a rejected leg cannot raise a FALSE naked alarm). `naked_position=False` is now
  reported **only when the venue confirmed the unwind** — a cancel returning False, a rejected offset, a venue that
  cannot express the opposite side, or a `PARTIALLY_MATCHED` result with no `filled_stake` to size the offset all fail
  safe to `naked_position=True` plus a reason in `compensation_detail`. Sizing is never guessed: guessing would under-
  or over-hedge real money. Tests: 23/23 green, covering matched-offset, offset-rejection-reports-naked, and
  partial-fill-cancel-then-offset.
- **Two-sided Betfair odds ([5])**: persisted odds remain BACK-only, so `betfair_yes_bid` is always None → Betfair is
  BUY-YES-only; SELL-Betfair lights up automatically once a back+lay exchange book is persisted (kernel edge already
  wired). Needs a Betfair-exchange book source (the Odds-API aggregator is back-only).
- **Betfair fee proxy**: `betfair_fee` takes _net winnings_; entry-time code passes the YES-bid premium as the proxy — a
  documented deterministic approximation, operator-tunable.
- **`entry_threshold` semantics moved**: values were calibrated against GROSS edge and now gate on NET, so the same
  number is strictly more selective (0.03 = 3% NET). Intended, but re-tune with eyes open.
- **✅ FIXED 2026-07-20 — CI integrity**: the global pytest hook that silently skipped the whole unit backtest suite is
  now scoped to its own `tests/e2e/` subtree, so `tests/unit/engine/backtest/` (GroupBRunner, BenchmarkFillEngine, the
  paper-run suites — the settlement engine underwriting `paper(W) == batch-rerun(W)`) actually RUNS in the gate: **58
  passed, 0 failed**, no `requires_data` marks needed. Turning the lights on immediately exposed a genuinely BROKEN test
  (`NameError: _STRAT_JITO`, a missed 3-site rename from the 2026-07-16 Solana-perp-DEX cull) which was also fixed. See
  `strategy_global_pytest_hook_skips_backtest_suite_2026_07_20.md` (now `status: resolved`). **This matters for the arb
  proof specifically**: it means the green gate now genuinely covers the benchmark-fill path the 3-venue paper proof
  depends on, instead of merely appearing to.
