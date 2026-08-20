---
doc_type: issue
title: "P1 ISSUE — FILL_COMPLETED schema rename broke strategy-service fill consumer (fix shipped)"
summary: >-
  execution-service P2.1 (SHA 08808415) changed the FILL_COMPLETED PubSub event format from a flat dict with `fill_id`
  at top level to a nested `details`-wrapper with `trade_key`; strategy-service's
  `fill_event_consumer._parse_fill_event` was reading `data["fill_id"]` directly — KeyError on every live fill after the
  execution-service rollout. Fix shipped in strategy-service@f1a98416 as part of the P2.2 todo in
  citadel_satellite_ao_dispatch_batch1_2026_08_08.md. Blast-radius assessment pending operator review.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [live]
repos: [execution-service, strategy-service]
scope: [engineer]
tags: [OPERATOR, live-trading, data-correctness, cross-cutting, execution-service, strategy-service]
related:
  [
    /plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-11"
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: issue
estimate_baseline_ai_days: 0.0
estimate_calibrated_ai_days: 0.0
assigned_role: operator
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  "2026-08-08: identified during P2.2 citadel_satellite_ao_dispatch_batch1 — FILL_COMPLETED schema break between
  execution-service@08808415 and strategy-service@f1a98416"
resolved_by:
context_scope:
  [
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    strategy-service/strategy_service/position/core/fill_event_consumer.py,
    strategy-service/strategy_service/adapters/fill_subscriber.py,
  ]
---

# P1 ISSUE — FILL_COMPLETED event schema break broke strategy-service fill consumer

## What happened

`execution-service` P2.1 (SHA `08808415`, 2026-08-08) changed how FILL_COMPLETED events are published to PubSub:

**Before (legacy flat format):**

```json
{
  "fill_id": "venue-fill-123",
  "order_id": "ord-456",
  "side": "BUY",
  "quantity": "1.5",
  "price": "50000",
  "timestamp": "2026-08-08T12:00:00+00:00",
  ...
}
```

**After (UTL log_event envelope with details + trade_key):**

```json
{
  "timestamp": "2026-08-08T12:00:00+00:00",
  "service_name": "execution-service",
  "severity": "INFO",
  "details": {
    "trade_key": "BINANCE:BTC-USDT|inst-001-00000001|2026-08-08T12:00:00.000000+00:00",
    "order_id": "ord-456",
    "instrument_id": "BINANCE:BTC-USDT",
    "side": "BUY",
    "qty": "1.5",
    "price": "50000",
    "fees_in_quote": "0.0",
    "venue": "BINANCE"
  }
}
```

Two concurrent renames: (1) `fill_id` → `trade_key` inside `details`; (2) `quantity` → `qty`; (3) flat dict → `details`
wrapper.

`strategy-service`'s `fill_event_consumer._parse_fill_event` read `data["side"]` from the top-level dict — KeyError
after rollout, causing the position-tracking PubSub consumer to crash on every live FILL_COMPLETED message.

## Detection

Identified during P2.2 code review (`citadel_satellite_ao_dispatch_batch1_2026_08_08.md` task TODO P1 / P2.2) when
tracing the full message path from execution-service to strategy-service.

## Fix status

**SHIPPED** — `strategy-service@f1a98416` (2026-08-08):

- `_parse_fill_event` now unwraps the `details` envelope (with fallback to legacy flat format for in-flight pre-rollout
  messages)
- `fill_id` set to `trade_key` (UAC canonical key) with `fill_id` fallback
- `qty` → `quantity` fallback handled
- `_extract_correlation_id` now returns `trade_key` (non-sequential) when available
- 2 new unit tests assert `fill_id == trade_key` and `correlation_id == trade_key`
- Legacy flat-format backwards-compat test added
- QG green

The fill subscriber (`adapters/fill_subscriber.py`) was already fixed at strategy-service@4b3f5b0c for the `qty`/`price`
key rename; this fix covers the position-tracking consumer path.

## Blast radius

- **Live DeFi fill tracking**: any FILL_COMPLETED events published after execution-service@08808415 landed and before
  strategy-service@f1a98416 landed would have caused `_process_message` to raise `KeyError`, the error would be caught
  by `_handle_loop_error`, and the fill would be silently dropped from position tracking. PubSub message acknowledgment
  happens AFTER processing, so unprocessed messages are re-delivered — however the error handler calls
  `asyncio.sleep(1)` and retries, so if the consumer was live during the gap, fills were not processed for the gap
  window.

- **[OPERATOR]** Operator action required: confirm whether there was a live strategy-service instance running between
  execution-service@08808415 and strategy-service@f1a98416 deployment. If yes, verify position state is still accurate
  (FillDB fill_id column, LocalFillRecord counts) and reconcile any gap fills manually or via replay.

- **Paper/backtest fills**: NOT affected — the paper path uses `ledger_emit.py` which already calls `make_trade_key()`
  directly, independent of the PubSub consumer.

## TODO for operator

- [ ] [OPERATOR] P1. Confirm the live-trading gap window: was strategy-service running against live
      execution-service@08808415 before strategy-service@f1a98416 was deployed? If yes: audit FillDB for missing fills
      in the gap window and reconcile.

## Progress Log

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- the sole open todo is an `[OPERATOR]`
  P1 live-trading data-correctness call (confirm whether a live strategy-service instance ran against the broken
  execution-service window, and if so audit FillDB/reconcile position state) -- a real-money live-trading
  judgment/investigation call, not a bounded mechanical fix.
- **context-scout 2026-08-09**: populated context_scope (4 entries).
