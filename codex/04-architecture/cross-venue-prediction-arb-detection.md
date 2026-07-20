---
doc_type: codex-ssot
title:
  Cross-Venue Prediction Arb — N-venue detector (Kalshi / Polymarket / Betfair), net-of-fees gate, GCS arb store,
  execution bridge
summary:
  "SSOT for the N-venue cross-venue prediction arb: normalize every venue to YES probability (incl. the Betfair Exchange
  de-vig), flag PURE_ARB/QUOTABLE_ARB over ALL venue pairs, gate entry on NET-of-fees edge, persist the raw per-venue
  quotes to a dated GCS arb store, and route the emitted LEADER_HEDGE AtomicInstruction through the paper-default
  atomic_leg_executor. Betfair is BUY-YES-only until a lay book is persisted; no LIVE runtime seam yet."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [prediction, arbitrage, cross-venue, betfair, sports, features, execution, mtds, data-correctness]
related:
  [
    ../09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    strategy-execution-protocol.md,
    paper-vs-live-execution-seam.md,
    ../09-strategy/architecture-v2/cross-cutting/prediction-markets.md,
    ../02-data/availability-manifest-and-data-status.md,
    ../05-infrastructure/vm-tarball-deployment.md,
    ../05-infrastructure/deployment-observability.md,
    ../12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
created: 2026-06-24
authoritative_for:
  [
    cross-venue prediction arb detection (N-venue Kalshi/Polymarket/Betfair),
    the GCS arb-opportunity store schema,
    the net-of-fees prediction-arb entry gate,
    the Betfair de-vig YES normalization,
  ]
referenced_by:
owner:
last_reviewed: 2026-07-20
code_refs:
  - features-service/features_service/cross_instrument/app/calculators/
  - strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/
  - execution-service/execution_service/v2/atomic_leg_executor.py
  - unified-api-contracts/unified_api_contracts/canonical/domain/predictions/
  - unified-api-contracts/unified_api_contracts/canonical/domain/sports/
---

# Cross-Venue Prediction Arb — N-venue detector, net-of-fees gate, GCS arb store, execution bridge

**Status:** SHIPPED (2026-07-20), paper-proven end-to-end. Owning epic: `predictions_master`. Parent archetype:
[`arbitrage_price_dispersion`](../09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md)
(`dispersion_type = "cross-venue-prediction-dispersion"`).

> **One line:** the same real-world outcome is quoted as a YES probability on several venues; we normalize them all to
> one YES scale, scan **every venue pair** for the best box (richest YES bid = SELL, cheapest YES ask = BUY), gate entry
> on the edge **net of both legs' fees**, persist every flagged opportunity to a dated GCS tape, and hand the resulting
> `LEADER_HEDGE` `AtomicInstruction` to a paper-default execution bridge.

> **⚠️ Was 2-venue.** Until 2026-07-20 this doc (and the code) described a **Kalshi ↔ Polymarket two-leg** arb on a
> **gross** edge. Both are superseded: the scan is N-venue including **Betfair Exchange**, and the entry gate is
> **net-of-fees**. See § Net-of-fees entry gate for the config-calibration consequence.

## Venue model — execution venues vs data-only references

Not every venue in the odds corpus is tradeable. The distinction is UAC data (`registry/_odds_api_maps.py`,
`is_execution_venue`), not a code branch:

| Venue                                   | `is_execution_venue` | Role in this arb                                                                                           |
| --------------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Kalshi**                              | ✅                   | Two-sided YES CLOB. Can be BUY or SELL leg.                                                                |
| **Polymarket**                          | ✅                   | Two-sided YES CLOB. Can be BUY or SELL leg.                                                                |
| **Betfair Exchange**                    | ✅                   | Two-sided back+lay **exchange**. `BETFAIR` maps to `betfair_ex_uk` / `_eu` / `_au`. **BUY-YES-only today** |
| Pinnacle / FanDuel / DraftKings / other | ❌                   | **Sportsbooks — data only.** Fair-value / sharp reference. Never an arb leg.                               |

A sportsbook price is a reference, not a quote we can hit. Treating one as an executable leg is review-blocking.

## Normalization (CRITICAL — one YES scale, same outcome, same settlement)

Every venue → a single **YES probability `p ∈ [0,1]`** before any comparison. A crossing is only real if both legs mean
the **same outcome** of the **same settlement event**.

- **Kalshi** — prices are already YES dollars in `[0,1]` (`yes_dollars` ladder → `best_bid`/`best_ask` are the YES
  bid/ask).
- **Polymarket** — a binary market has 2 tokens; the **YES token** is the join leg (condition_id → `clob_token_ids[0]`;
  verify `[0]` is the YES/up/over token against the gamma `outcomes` order — do not assume). Its `best_bid`/`best_ask`
  are the YES bid/ask.
- **Betfair Exchange — de-vig (book-sum overround normalization).** Betfair quotes **decimal odds per runner**, not a
  probability, and the raw implied probabilities sum to >1 (the vig). Our persisted source is the sports ODDS_API `h2h`
  (== MATCH_ODDS) tick frame, which is **BACK-only**. For the runner `r` matching the prediction YES outcome:

  ```
  betfair_yes_ask = (1 / back_odds_r) / Σ_runners (1 / back_odds_i)      # BUY-YES price  — SHIPPED
  betfair_yes_bid = (1 / lay_odds_r)  / Σ_runners (1 / lay_odds_i)       # SELL-YES price — formula only, no data yet
  ```

  Works identically for 3-way (home/draw/away) and 2-outcome books. Joined to the prediction pair by **`af_fixture_id`**
  (the API-Football fixture id — see § Identity). The YES outcome side (home/away/draw) is resolved **conservatively**:
  anything ambiguous yields **honest `None`**, never a guessed side.

- **Betfair is BUY-YES-ONLY today (the load-bearing limitation).** Because only the BACK book is persisted,
  `betfair_yes_bid` is **always `None`** — Betfair can be the **cheap-ask / BUY** side of a pair but **never** the SELL
  side. The lay-side formula above is documented and **the kernel's SELL-Betfair edge is already wired**, so
  SELL-Betfair activates automatically the moment a back+lay exchange book is persisted. No code change needed — only
  the data.
- **Outcome alignment** — confirm the matched pair's "YES" means the same thing on every leg (if one venue quotes
  down/under, invert `p_yes = 1 − p_no`). Reject any pair whose YES semantics can't be confirmed (honest absence, never
  a false cross).
- **Honest absence is the default** — a venue whose quote is missing, non-positive or one-sided is **skipped**, never
  synthesized. With Betfair absent (the common non-sports case) every Betfair pair drops out via null-skipping and the
  emitted rows are byte-identical to the old two-venue detector.

## Fee model (UAC — versioned, stamped per row)

`unified_api_contracts.predictions` owns the public per-venue fee model; `PREDICTION_VENUE_FEE_MODEL_VERSION` is stamped
on every arb-store row so a schedule change is auditable across the stored corpus. Bump it whenever a coefficient moves.

| Venue      | Per-leg fee (YES price units)                   | Note                                                        |
| ---------- | ----------------------------------------------- | ----------------------------------------------------------- |
| Kalshi     | `KALSHI_FEE_COEFF · P · (1−P)` (coeff `0.07`)   | Convex, mid-heavy: max ~1.75¢ at `P=0.5`, →0 at the tails   |
| Polymarket | `0`                                             | CLOB maker + taker currently zero; gas/relay is off-book    |
| Betfair    | `BETFAIR_COMMISSION_FRACTION · max(net_win, 0)` | 5% exchange commission on **net winnings**, not on notional |

Betfair's commission is on winnings, so BUYING (backing) YES at `P` costs `BETFAIR_COMMISSION_FRACTION · (1−P)` in
YES-price units. Helpers: `kalshi_fee()`, `polymarket_fee()`, `betfair_fee()`, `net_edge_sell_kalshi()`,
`net_edge_sell_polymarket()`.

## Arb-signal taxonomy (what to flag + store)

Per matched pair, per tick, over **all venue pairs** across {kalshi, polymarket, betfair}:

- **PURE_ARB** — a bid crosses an offer: `raw_edge = xv_best_edge > 0` (sell YES on the rich-bid venue, buy YES on the
  cheap-ask venue). `net_edge_after_fees` = the max over every **ordered** pair `(sell S @ bid, buy B @ ask)` of
  `S_bid − B_ask − fee_S(sell) − fee_B(buy)`, each pair **masked to null unless its required quotes are live** so a
  phantom edge off an absent/0.0 quote can never win. `is_executable = net_edge > 0`.
- **QUOTABLE_ARB** — no top-of-book cross (`raw_edge <= 0`) but the mids diverge beyond `entry_threshold`
  (`mid_dispersion > entry_threshold`, default `0.03`) → quote-able if fast enough.
- **ONE_SIDED / NO_OVERLAP** — a leg missing a quote, or no cross + sub-threshold dispersion → **no row**, logged
  reason. This is the common case (Polymarket crypto is thin/one-sided).

## Net-of-fees entry gate (SEMANTICS CHANGE — recalibrate configs)

`select_prediction_arb_direction` (strategy-service) gates on **net** edge:

```
gross edge = best_yes_bid − best_yes_ask          # richest YES bid across venues − cheapest YES ask
net_edge   = gross − fee(buy_leg) − fee(sell_leg) # per-venue UAC fee model, per leg
fire iff  net_edge >= entry_threshold  AND  buy_venue != sell_venue
```

- The signal still carries the **gross** `edge` (engine sizing + attestations read it) alongside a new `net_edge` field.
  Pinned by test to equal `net_edge_sell_kalshi` / `net_edge_sell_polymarket`.
- **⚠️ Existing `entry_threshold` numbers were calibrated on GROSS and now gate on NET** — the gate is strictly more
  selective. Re-derive any inherited threshold rather than carrying it forward.
- Determinism: on a tie the first venue in `_VENUE_YES_KEYS` order wins (kalshi > polymarket > betfair), matching the
  prior 2-way tie-break.
- Backward compatibility: with only Kalshi + Polymarket present and non-crossed per-venue books, the N-venue scan
  reduces exactly to the prior 2-way behaviour.

## GCS arb-opportunity store (the persistent corpus)

Every flagged opportunity appends to a dated, partitioned GCS store (batch=live; via `resolve_bucket_name` + the UTL
writegate / manifest emission — **never** a hand-rolled `gs://` write):

```
gs://<features-cross-instrument-bucket>/cross_venue_arb/by_date/day=YYYY-MM-DD/
  underlying=<U>/bet_type=<B>/<XV-instrument>.parquet
```

Row schema (`ARB_STORE_COLUMNS`, one row per flagged tick):

`ts_utc, xv_instrument_id, canonical_event_id, underlying, bet_type, settlement, kalshi_market_ticker, polymarket_condition_id, polymarket_yes_token_id, kalshi_yes_bid, kalshi_yes_ask, polymarket_yes_bid, polymarket_yes_ask, betfair_yes_bid, betfair_yes_ask, kalshi_bid_size, kalshi_ask_size, polymarket_bid_size, polymarket_ask_size, betfair_ask_size, max_arb_contracts, kalshi_title, polymarket_title, kalshi_settlement_method, polymarket_settlement_method, kalshi_mid, polymarket_mid, raw_edge, net_edge_after_fees, mid_dispersion, signal_type ∈ {PURE_ARB, QUOTABLE_ARB}, is_executable, both_two_way, fee_model_version`

**The store (and the Slack body) persist the RAW per-venue quotes, not just the derived edge** — including
`betfair_yes_bid` / `betfair_yes_ask` / `betfair_ask_size`. Before this, a Betfair-influenced row was **unauditable**:
you could not re-derive its `net_edge_after_fees` / `both_two_way` / `max_arb_contracts` leg-by-leg. Persisting derived
fields only is the anti-pattern; a stored row must be reproducible from its own persisted inputs. Betfair columns are
honest-`None` when the venue is absent.

Honest-absence: a tick with no crossing writes **nothing** — the store is the opportunity tape, not a full quote tape
(the book tape already lives in `raw_tick_data`).

## Execution bridge — `AtomicInstruction` → adapter (PAPER-default)

The strategy emits a two-leg `LEADER_HEDGE` `AtomicInstruction` (BUY YES on the cheap venue = leader; SELL YES on the
rich venue = hedge). `execution-service/execution_service/v2/atomic_leg_executor.py` is the **first actual execution
path** for it — see [`strategy-execution-protocol.md`](strategy-execution-protocol.md) § ATOMIC for the protocol side.

- **Translation** — `AtomicLeg` → `BetOrder`: `side = BACK` if BUY else `LAY`;
  `fixture_id = params["native_market_id"]`.
- **`LEADER_HEDGE`** — leader placed first; hedge only if the leader is accepted, within `hedge_deadline_ms`; on hedge
  failure/timeout `CLOSE_LEADER_IF_HEDGE_FAILS` unwinds the leader so no naked position remains
  (`naked_position=False`).
- **PAPER-safe by construction** — the adapter comes from `create_sports_adapter(mode)` **defaulting to
  `OperationalMode.PAPER` → `PaperBettingAdapter`** (simulated fills, zero network I/O). A missing/`None` mode is PAPER;
  live requires an explicit `OperationalMode.LIVE` **and** Secret-Manager credentials that are not provisioned. Kalshi
  and Polymarket are registered in `_LIVE_VENUE_CONFIGS`.

## Identity — `af_fixture_id` is the strong join key

`af_fixture_id` (API-Football fixture id) now flows **catalogue → features → matcher**, which is what makes the Betfair
odds join deterministic:

- instruments-service catalogue rollup carries the 6 fixture columns; features `_records_from_universe` populates them.
- UAC `match_key` **prefers** `af_fixture_id` → `SPORTS_FIX::{af_fixture_id}::{bet_type}`; the fuzzy team-name pairing
  is preserved as the fallback. Only the `SPORTS_FIX::` form carries a parseable id — a fuzzy `SPORTS::…` match means
  Betfair is honest-absent for that pair.
- MTDS stamps canonical `PREDICTION_MARKET` as the per-CID `instrument_type`; the prediction universe reads are pinned
  to the PROD catalogue.

**Seasonality caveat:** `af_fixture_id` only populates **in-season**. July is the European soccer off-season → honest-
`None` is the expected reading, not a bug.

## Proofs (what is actually verified)

- **strategy-service** `test_prediction_arb_3venue_paper_proof.py` — a crossed 3-venue box FIRES one `LEADER_HEDGE`
  `AtomicInstruction` and SETTLES two benchmark fills with non-zero P&L through the **real paper runtime**
  (`GroupBRunner` + `BenchmarkFillEngine`), deterministic (`execution_alpha_bps == 0`, per
  [Rule 5 benchmark fills](strategy-execution-protocol.md)).
- **execution-service** `test_atomic_leg_executor.py` — executor paper proof: BACK/LAY translation + hedge-fail unwind.
- A cross-repo e2e loop proof (features → engine → executor, paper) lands in `e2e-testing`.

## Standing caveats + open items (do NOT read this as complete)

1. **No LIVE runtime seam.** Nothing routes an emitted `AtomicInstruction` to the executor in a live/paper-live tick
   loop. Backtest/paper settles via `GroupBRunner` + `BenchmarkFillEngine`, and the **T4 tier ban forbids a
   strategy→execution import** ([`tier-and-import-architecture.md`](tier-and-import-architecture.md)) — so the seam
   needs an operator-directed `EventTransport` decision
   ([`../02-data/live-data-persistence-and-event-log.md`](../02-data/live-data-persistence-and-event-log.md)).
2. **Betfair two-sided book needs Betfair Exchange API credentials.** The Odds-API aggregator is BACK-only; until a lay
   book is persisted, SELL-Betfair stays honestly absent (the formula + kernel edge are already in place).
3. **Compensation for an already-MATCHED leader.** `cancel_bet` pulls a _resting_ order; it does **not** offset a filled
   position. A matched leader needs a real offsetting bet on the opposite `BetSide`. Being addressed separately —
   reporting `naked_position=False` off a bare cancel would be a false-clean report on the real-money path.
4. **Live flip** needs a Betfair account, credentials, and a jurisdiction decision (operator-gated).
5. **Producer trades-mislabel (P0, data-correctness).** `raw_tick_data/.../data_type=trades/` parquets have carried
   **order-book** rows (`data_type` COLUMN = `book_snapshot_5`), so there is no real trade-print tape. The detector uses
   the BOOK feed for crossings (correct); the trade feed is unavailable until the MTDS prediction live producers +
   manifest data_type routing are fixed.
6. **IS Kalshi catalogue for past dates** — needed only for historical _trade_ backtests (the live path resolves fine).
   Re-enumerate the IS Kalshi universe for any backfill window before a Kalshi batch trades backfill.

## Composes with

[`arbitrage-price-dispersion.md`](../09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md) (parent
archetype) · [`strategy-execution-protocol.md`](strategy-execution-protocol.md) (the `AtomicInstruction` contract) ·
[`paper-vs-live-execution-seam.md`](paper-vs-live-execution-seam.md) (mode divergence lives only at the fill source) ·
[`../09-strategy/architecture-v2/cross-cutting/prediction-markets.md`](../09-strategy/architecture-v2/cross-cutting/prediction-markets.md)
(prediction venues as a three-role surface) ·
[`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) (honest
absence) · [`../05-infrastructure/deployment-observability.md`](../05-infrastructure/deployment-observability.md) (VM
run

- classify) ·
[`../12-agent-workflow/async-wait-and-poll-discipline.md`](../12-agent-workflow/async-wait-and-poll-discipline.md)
(monitoring a long-lived detector run).
</content>

</invoke>
