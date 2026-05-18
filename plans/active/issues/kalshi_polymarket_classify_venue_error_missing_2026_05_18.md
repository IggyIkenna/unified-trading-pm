---
title: kalshi + polymarket_clob adapters missing classify_venue_error()
created: 2026-05-18
author: ikenna-main (surfaced by harsh slot 5 audit)
source:
  - execution-service/execution_service/sports_execution/adapters/exchanges/kalshi.py
  - execution-service/execution_service/sports_execution/adapters/exchanges/polymarket_clob.py
locked_by: live-defi-rollout
---

## What I found

Both prediction-market adapters (`kalshi.py` 535L, `polymarket_clob.py` 509L) have no
calls to `classify_venue_error()` from UAC, and no `ADAPTER_FETCH_FAILED` event emission.
Per CLAUDE.md: "Every adapter MUST classify errors via UAC `classify_venue_error()` + emit
`ADAPTER_FETCH_FAILED`."

Confirmed via `grep -n "classify_venue_error"` in both files → 0 hits.

## Why it matters

Error classification is mandatory for all adapters. Without it:
- All exchange-level errors surface as unclassified exceptions
- No `ADAPTER_FETCH_FAILED` metric emitted → alerting/monitoring blind
- QG STEP compliance gap (adapter contract enforcement)

Not on May-23 critical path (DeFi archetypes don't use prediction markets), but
should ship in the 2026-05-19 to 2026-05-21 window.

## Recommended decision

Route to execution-service slot owner (Slot 5 or reassigned slot).
Pattern to follow: any CeFi adapter that has `classify_venue_error()` already (e.g.
`binance.py`, `hyperliquid.py`) — apply same pattern to error `except` blocks in both
adapters. ~1.5 cal-days per file.

Files to change:
- `execution_service/sports_execution/adapters/exchanges/kalshi.py`
- `execution_service/sports_execution/adapters/exchanges/polymarket_clob.py`
Also check: `execution_service/sports_execution/prediction_markets/kalshi.py` (separate module)
and `execution_service/trade_execution/adapters/polymarket_adapter.py`.

## Resolution

**RESOLVED 2026-05-18** — execution-service@a2b5eef46

- `kalshi.py`: added `classify_venue_error` + `ErrorAction` imports from UAC
  `canonical.crosscutting.errors`; added `ADAPTER_FETCH_FAILED` + `UNKNOWN_VENUE_ERROR_RECEIVED`
  imports from UTL events; all 5 `except aiohttp.ClientError` handlers in `_submit_order`,
  `cancel_bet`, `get_balance`, `_submit_order_post`, `get_positions`, and `list_open_orders`
  now classify + emit `ADAPTER_FETCH_FAILED`.
- `polymarket_clob.py`: added `classify_venue_error` + `ErrorAction` imports; added
  `ADAPTER_FETCH_FAILED` to existing UTL events import; upgraded all `aiohttp.ClientError`
  and `Exception` handlers in `place_bet`, `cancel_bet`, `place_order`, and `list_open_orders`
  to full SP-12(a) pattern (classify → emit ADAPTER_FETCH_FAILED + UNKNOWN_VENUE_ERROR_RECEIVED).
- `prediction_markets/kalshi.py`: stub only (no HTTP calls) — no fix needed.
- `trade_execution/adapters/polymarket_adapter.py`: delegates to PolymarketCLOBAdapter — fix
  applied upstream; no independent classification needed.
- basedpyright: 0 errors on both files.
- ruff: 0 errors on both files.
- QG pre-existing failures in `trade_converter.py` / `data_loader.py` (E501) are not owned by
  this fix; reported separately.
