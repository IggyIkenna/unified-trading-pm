---
doc_type: codex-ssot
title: Live strategy-config hot-reload
summary:
  "strategy-service registers a StrategyConfigReloader (same shape as ApiKeyReloader) that hot-applies config deltas
  mid-session — sizing / risk-caps / venue-routing / signal-filters / kill-switch flags — without restart; archetype
  family and underlying-instrument changes are NOT hot-reloadable (raise UnsafeConfigChangeError). Batch and live share
  the same validation."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-library]
scope: [engineer, admin]
tags: [strategy, live-trading, self-healing, execution, ssot]
related:
  [
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md,
    /codex/04-architecture/research-service-and-dart-integration.md,
    /codex/09-strategy/strategy-summary.md,
  ]
created: 2026-05-08
authoritative_for: [live strategy-config hot-reload, StrategyConfigReloader safe-field allow-list]
referenced_by:
  [
    /codex/03-observability/lifecycle-events.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/ml-experiment-lifecycle.md,
    /codex/04-architecture/ml-lifecycle.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Live strategy-config hot-reload

## Why hot-reload matters

A live strategy runs continuously. Operators tune sizing, gating, risk caps, and venue-routing parameters mid-session
based on observed P&L attribution. Restarting strategy-service to pick up a config change loses in-memory state (open
positions, pending orders, in-flight signals), forces an order rebuild, and creates a window where strategy and
execution disagree on what's working. Hot-reload eliminates the restart.

## Pattern (same shape as ApiKeyReloader)

Strategy-service registers a `StrategyConfigReloader` at startup. The reloader:

1. Subscribes to a config-update event (Pub/Sub or Redis Stream — same channel pattern as
   [`/codex/06-coding-standards/config-reloader-pattern.md`](/codex/06-coding-standards/config-reloader-pattern.md)).
2. On event, fetches the new config from the SSOT (Firestore for strategy archetype configs, Secret Manager for
   credential refs).
3. Diffs against in-memory state and applies the delta — no full reload.
4. Emits `STRATEGY_CONFIG_RELOADED` lifecycle event with the diff so operators see what changed in
   unified-events-interface.

This is the same shape as instrument lifecycle delta hot-reload
([`instrument-lifecycle-cache-delta-hot-reload.md`](instrument-lifecycle-cache-delta-hot-reload.md)) — "service is
effectively a config" applies to strategies the same way it applies to catalogs and API keys.

## What can hot-reload safely

| Field class                  | Hot-reload safe? | Notes                                                                  |
| ---------------------------- | ---------------- | ---------------------------------------------------------------------- |
| Sizing (notional, weights)   | Yes              | Applies to next signal; existing orders untouched                      |
| Risk caps (per-position max) | Yes              | Cap drops trigger an immediate halt of orders that exceed              |
| Venue-routing weights        | Yes              | Applies to next signal                                                 |
| Signal-filter thresholds     | Yes              | Applies to next signal                                                 |
| Kill-switch flags            | Yes              | Immediate; in-flight orders paused                                     |
| Strategy archetype family    | NO               | Family change = different code path; restart required                  |
| Underlying instruments       | NO               | Position-state continuity is broken; restart required (rare operation) |

The `StrategyConfigReloader` validates the diff against the safe-list before applying. Unsafe-field changes raise
`UnsafeConfigChangeError` and require a planned restart through DART.

## Live = batch

Backtest replays consume the same config object. A config change in batch is just a new run; live applies it via
hot-reload. The SAME validation rules apply both paths so a config rejected by batch validation never reaches live.

## Cross-references

- Config reloader pattern (workspace standard):
  [`/codex/06-coding-standards/config-reloader-pattern.md`](/codex/06-coding-standards/config-reloader-pattern.md)
- Instrument lifecycle delta:
  [`instrument-lifecycle-cache-delta-hot-reload.md`](instrument-lifecycle-cache-delta-hot-reload.md)
- ApiKeyReloader (sibling pattern): unified-trading-library `api_key_reloader.py`
- Strategy summary: [`/codex/09-strategy/strategy-summary.md`](/codex/09-strategy/strategy-summary.md)
- DART boundary: [`research-service-and-dart-integration.md`](research-service-and-dart-integration.md)
