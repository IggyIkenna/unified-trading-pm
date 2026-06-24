# Cross-Venue Prediction Arb Detection (Kalshi ↔ Polymarket) — live paper-mode detector + GCS arb store

**Status:** design SSOT (2026-06-25). Owning epic: `predictions_master`. Active plan:
`plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md`. Parent archetype: `arbitrage_price_dispersion`.

> **One line:** the cross-venue arb _finding_ code is already shipped (matcher → dispersion feature → strategy engine).
> What's missing is a **live, normalized, always-on detector** that watches both venues' live books, flags arb
> crossings, and **persists every arb opportunity to GCS over time** so we accumulate an arb-opportunity corpus and can
> prove whether the edge is real and quote-able. Run it paper-mode on a VM for ~a day, report, then make it long-lived.

## Why this exists (the operator's framing, 2026-06-25)

We already stream live books for **both** venues (4 `prediction-live-*` VMs capture `book_snapshot_5`). Order-book
_depth_ is **live-only** on both venues (no historical book API — verified), so the only way to build an arb-backtest
corpus is to **record it ourselves, live, going forward**. So: run the cross-venue dispersion engine in **paper mode**
against the live streams, **normalize** both sides to a common odds format, and **store the arb opportunities to GCS**
as they occur. Even if we don't catch an instant pure arb today, we (a) prove the pipeline streams a good live/paper arb
signal into GCS, and (b) accumulate the opportunity tape over time. If it produces signal for a day → it becomes a
long-lived service that just runs and stores arbs.

## What is ALREADY built (do NOT rebuild — reuse)

| Layer                         | Repo@sha                         | Symbol                                                                                                                                                                                                                                |
| ----------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| per-instrument matcher        | `unified-api-contracts@e618ce96` | `build_cross_venue_mapping`, `match_key`, `PredictionMarketCrossVenueMapping`                                                                                                                                                         |
| two-axis underlying taxonomy  | `unified-api-contracts@098d1698` | `PredictionUnderlying`, `underlying_for_group`, `bet_type_for_group`, `cross_venue_underlying_overlap`                                                                                                                                |
| BOOK dispersion feature       | `features-service@54ea17c8`      | `prediction_cross_venue_dispersion` (`cross_instrument` framework) → `xv_best_edge`, `kalshi_yes_bid/ask`, `polymarket_yes_bid/ask`, `xv_mid_dispersion`                                                                              |
| TRADES/mid dispersion feature | `features-service@839aa585`      | `prediction_cross_venue_trade_dispersion` → `xv_trade_best_edge` (note: reads the mislabeled `trades` path — see P0)                                                                                                                  |
| arb ENGINE + mode             | `strategy-service@06e51ed0`      | `arbitrage_price_dispersion` `dispersion_type="cross-venue-prediction-dispersion"` branch (`engine/strategies/v2/arbitrage_structural/prediction_venue_dispersion.py`); two-leg LEADER_HEDGE on `xv_best_edge`; `prediction_arb` mode |

The matcher pairs by `(underlying, bet_type, settlement_date, strike)` with a same-settlement guard (no false pairs);
each pair is a synthetic instrument `XV:{underlying}:{bet_type}:{settlement}`. The book feature already computes the
normalized YES bid/ask + edge. The engine already emits a two-leg arb signal. **The detector = wire these into the LIVE
path + add the arb-store sink + the long-lived run.**

## Prerequisite FIXES (must land before / alongside the detector)

1. **P0 — producer trades-mislabel (data-correctness).** `raw_tick_data/.../data_type=trades/` parquets currently carry
   **order-book** rows (`msg_type ∈ {orderbook_delta, orderbook_snapshot, price_change, book}`, `data_type` COLUMN =
   `book_snapshot_5`, columns `best_bid_price/best_ask_price/bids/asks` — **no**
   `price/size/yes_price_dollars/count_fp`). The prediction MTDS live producer mis-stamps book ticks under the `trades`
   cluster, so we have **no real trade-print tape**. Fix the producer (`market-tick-data-service` live connectors
   `kalshi_ws.py`/`kalshi_clob_ws.py`/ `polymarket_clob_ws.py` + the manifest data_type routing) so `trades` = real
   trade prints (Kalshi `GET /markets/trades` live/poll; Polymarket trade WS/REST) and `book_snapshot_5` = book. Until
   fixed, the detector uses the BOOK feed for crossings (correct) and the trade feed is unavailable.
2. **IS Kalshi catalogue for past dates** (only for historical trade backtests — NOT a blocker for live detection): the
   Kalshi _batch_ universe needs the IS Kalshi catalogue per past date (the live path resolves fine). Re-enum the IS
   Kalshi universe for any backfill window before a Kalshi batch trades backfill. Tracked at the plan's series-scoped
   historical backfill todo.

## Normalization (CRITICAL — same odds format, same YES semantics)

Both venues → a single **YES probability `p ∈ [0,1]`** before any comparison. A crossing is only real if both legs mean
the **same outcome** of the **same settlement event**.

- **Kalshi**: prices are already YES dollars in `[0,1]` (`yes_dollars` ladder → `best_bid`/`best_ask` are YES bid/ask).
- **Polymarket**: a binary market has 2 tokens; the **YES token** is the join leg. Our matcher/feature bridge
  condition_id → `clob_token_ids[0]` — **VERIFY `[0]` is the YES/up/over token** (read the gamma `outcomes` order; do
  not assume). The YES token's `best_bid`/`best_ask` are the YES bid/ask in `[0,1]`.
- **Outcome alignment**: confirm the matched pair's "YES" means the same thing (e.g. "BTC up on day D" YES on both, same
  strike/threshold direction). The matcher pairs same-settlement; the normalizer asserts the YES _direction_ matches (if
  one venue quotes "down/under", invert: `p_yes = 1 − p_no`). Reject a pair whose YES semantics can't be confirmed
  (honest absence, never a false cross).
- **Fees/ticks**: a _pure_ arb must clear fees. Carry both the **raw** crossing and the **net-of-fee** edge (Kalshi +
  Polymarket maker/taker fees from the venue capability declarations / UAC). A raw cross with negative net edge is a
  "quotable" signal, not an executable arb.

## Arb-signal taxonomy (what to flag + store)

Per matched pair, per tick, with both sides two-way (a bid AND an ask on each venue):

- **PURE_ARB (bid crosses offer)** — `kalshi_yes_bid > polymarket_yes_ask` (sell Kalshi YES @ bid, buy Polymarket YES @
  ask) OR the reverse. Executable now (subject to size + fees): `raw_edge = max(k_bid − p_ask, p_bid − k_ask)`,
  `net_edge = raw_edge − fees`. Flag `is_executable = net_edge > 0`.
- **QUOTABLE_ARB (mid crosses mid)** — both two-way but books don't cross at top-of-book, yet `kalshi_mid` vs
  `polymarket_mid` diverge beyond a threshold → you could _quote into_ the arb if fast enough.
  `mid_dispersion = |k_mid − p_mid|`; flag when `> entry_threshold`.
- **ONE_SIDED / NO_OVERLAP** — a leg missing a bid or ask, or no shared tick → **no signal, logged reason** (never a
  fabricated number). This is the common case today (Polymarket crypto is thin/one-sided at ~0.001).

## GCS arb-opportunity store (the persistent corpus)

Append every flagged opportunity to a dated, partitioned GCS store (batch=live; via `resolve_bucket_name` + the UTL
writegate / manifest emission — NOT a hand-rolled `gs://` write). Suggested canonical shape (align with the existing
features cross-instrument output if cleaner):

```
gs://<features-cross-instrument-bucket>/cross_venue_arb/by_date/day=YYYY-MM-DD/
  underlying=<U>/bet_type=<B>/<XV-instrument>.parquet
```

Row schema (one per flagged tick):
`ts_utc, xv_instrument_id, canonical_event_id, underlying, bet_type, settlement, kalshi_market_ticker, polymarket_condition_id, polymarket_yes_token_id, kalshi_yes_bid, kalshi_yes_ask, polymarket_yes_bid, polymarket_yes_ask, kalshi_mid, polymarket_mid, raw_edge, net_edge_after_fees, mid_dispersion, signal_type ∈ {PURE_ARB, QUOTABLE_ARB}, is_executable, both_two_way, fee_model_version`.
Honest-absence: a tick with no crossing writes nothing (the store is the opportunity tape, not a full quote tape — the
book tape already lives in `raw_tick_data`).

## Run plan (paper → validate → long-lived)

1. **Build/extend the LIVE path**: the `cross_instrument` `live_handler` (features-service) consuming the live book
   stream → the `prediction_cross_venue_dispersion` computation in real time → the arb-store sink. OR run the
   `strategy-service` `arbitrage_price_dispersion` engine in **PAPER mode** (`prediction_arb`) consuming the live
   feature, with the paper InstructionLedger capturing the would-be two-leg fills + the arb-store recording every
   signal. Prefer reusing the shipped engine/feature; add only the live wiring + the store.
2. **Launch a VM** (`deployment-service/scripts/vm/` launcher; `LONG_LIVED_LIVE` lifecycle class; VM prefix registered
   in `vm_zombie_watchdog.VM_PREFIX_TO_BUCKET`; classified deployment target). Run ~24h paper.
3. **Monitor** per the strict rules (exit_code from the persisted run.log + log-mtime advancement + heartbeat; never
   infer success from "VM gone"). Report: # pairs with two-way-on-both, # PURE_ARB events (raw + net-of-fee), #
   QUOTABLE_ARB events, the edge distribution, and the GCS store row count.
4. **Decide long-lived**: if it streams meaningful signal (even just sustained two-way overlap), promote to a permanent
   running service (a `SCHEDULED_RECURRING`/`LONG_LIVED_LIVE` VM or Cloud Run) that just runs + appends to the arb
   store. Wire its health into the deployment-observability surface + Slack.

## Verification (definition of done)

- Producer trades-mislabel fixed: `data_type=trades/` carries real trade prints (`price`/`size`/taker side), `data_type`
  column == `trades`; QG-green.
- The live detector runs paper ~24h on a VM, exits clean, and the GCS arb store has rows (or an honest "0 crossings, N
  two-way ticks observed, here's the mid-dispersion distribution" with the reason).
- A report (in the plan Progress Log — NOT a summary doc) with the real numbers.
- If promoted: the long-lived service is registered, classified, health-surfaced, and accumulating the corpus.

## Composes with

`codex/09-strategy/architecture-v2/archetypes/` (arbitrage_price_dispersion) ·
`codex/02-data/availability-manifest-and-data-status.md` (honest absence) ·
`codex/05-infrastructure/vm-tarball-deployment.md` + `deployment-observability.md` (VM run + classify) ·
`codex/12-agent-workflow/async-wait-and-poll-discipline.md` (monitoring) · the live-only-book + matcher findings in the
active plan's Progress Log (2026-06-25).
