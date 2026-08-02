---
doc_type: codex-ssot
title: Live strategy-config hot-reload
summary:
  "strategy-service hot-applies config deltas mid-session without restart via
  strategy_service/config_reloaders.py (UTL DomainConfigReloader family, same shape as ApiKeyReloader), emitting
  CONFIG_CHANGED / INSTRUMENT_UNIVERSE_CHANGED on atomic swap. The documented safe-field allow-list and
  UnsafeConfigChangeError are DESIGN INTENT ONLY — neither exists in code, and the instrument universe is hot-swapped
  today despite being listed unsafe. Batch and live share the same config object."
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
authoritative_for: [live strategy-config hot-reload, strategy-service config_reloaders entry points]
referenced_by:
  [
    /codex/03-observability/lifecycle-events.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/ml-experiment-lifecycle.md,
    /codex/04-architecture/ml-lifecycle.md,
  ]
owner:
last_reviewed: 2026-09-26
code_refs:
---

# Live strategy-config hot-reload

## Why hot-reload matters

A live strategy runs continuously. Operators tune sizing, gating, risk caps, and venue-routing parameters mid-session
based on observed P&L attribution. Restarting strategy-service to pick up a config change loses in-memory state (open
positions, pending orders, in-flight signals), forces an order rebuild, and creates a window where strategy and
execution disagree on what's working. Hot-reload eliminates the restart.

## Pattern — as shipped (verified 2026-07-31)

> **Naming correction.** There is no `StrategyConfigReloader` class. The shipped implementation is
> `strategy-service/strategy_service/config_reloaders.py`, built on UTL's generic
> `DomainConfigReloader` (`unified_trading_library/domain_config_reloader.py`) — the same family as `ApiKeyReloader`,
> `LifecycleReloader` and `InstrumentLifecycleCacheDeltaReloader`.

Entry points (module-level functions, not a single class):

| Function                                             | Role                                                         |
| ---------------------------------------------------- | ------------------------------------------------------------ |
| `start_domain_config_reloaders(service_config)`      | Starts the strategies + instruments domain reloaders          |
| `stop_domain_config_reloaders()`                     | Teardown                                                      |
| `get_active_strategy_config()` / `get_active_instruments()` | Read the current atomically-swapped snapshot           |
| `register_instrument_change_callback(...)`           | Subscribe an engine to instrument-universe deltas             |
| `start_version_governance_reloader()` (`VersionGovernanceReloader`) | Strategy-version governance refresh             |
| `start_directive_reloader(poll_interval_seconds=60)` (`StrategyDirectiveReloader`) | Directive polling               |

On reload the callbacks perform an **atomic swap** of the module-level snapshot, then emit lifecycle events. The
instruments path additionally computes an added/removed delta against the previous snapshot and fans it out to
registered callbacks (shard-isolated: one callback failing does not block the others).

**Events actually emitted** — `CONFIG_CHANGED` (with `details.domain` = `strategies` | `instruments`) and
`INSTRUMENT_UNIVERSE_CHANGED` (added/removed counts + a 5-item sample). There is **no `STRATEGY_CONFIG_RELOADED`
event**; that name appears nowhere in the workspace.

## What can hot-reload safely

> **⚠️ This table is the DESIGN INTENT and is not enforced anywhere (verified 2026-07-31).** `config_reloaders.py`
> contains no safe-list, allow-list, or unsafe-change guard — `rg -in 'unsafe|safe_list|allow_list|restart'` over the
> module returns nothing. **`UnsafeConfigChangeError` does not exist in the workspace.** Every reload is applied
> unconditionally via atomic swap. Treat the "NO" rows below as operator discipline, not as a guard-rail the code will
> enforce for you.

| Field class                  | Hot-reload safe? | Notes                                                                  |
| ---------------------------- | ---------------- | ---------------------------------------------------------------------- |
| Sizing (notional, weights)   | Yes              | Applies to next signal; existing orders untouched                      |
| Risk caps (per-position max) | Yes              | Cap drops trigger an immediate halt of orders that exceed              |
| Venue-routing weights        | Yes              | Applies to next signal                                                 |
| Signal-filter thresholds     | Yes              | Applies to next signal                                                 |
| Kill-switch flags            | Yes              | Immediate; in-flight orders paused                                     |
| Strategy archetype family    | NO (unenforced)  | Family change = different code path; restart required                  |
| Underlying instruments       | ⚠️ CONTRADICTED  | See below — the shipped reloader DOES hot-swap the instrument universe |

**The "Underlying instruments = NO" row contradicts shipped behaviour.** `_on_instruments_reload()` atomically swaps
`_active_instruments`, computes the added/removed delta, and notifies strategy engines via
`INSTRUMENT_UNIVERSE_CHANGED` — i.e. an instrument-universe change is hot-applied today, with no restart and no error
raised. Either the code is doing something the design considers unsafe for position-state continuity, or the design row
is obsolete. Resolve before relying on either statement:
`/plans/active/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md`.

## Live = batch

Backtest replays consume the same config object. A config change in batch is just a new run; live applies it via
hot-reload. **Caveat (2026-07-31):** the claim that "the SAME validation rules apply both paths so a config rejected by
batch validation never reaches live" is aspirational — the live reload path applies an unconditional atomic swap with
no validation gate, so there is currently nothing that would reject a bad config on the live side.

## Cross-references

- Config reloader pattern (workspace standard):
  [`/codex/06-coding-standards/config-reloader-pattern.md`](/codex/06-coding-standards/config-reloader-pattern.md)
- Instrument lifecycle delta:
  [`instrument-lifecycle-cache-delta-hot-reload.md`](instrument-lifecycle-cache-delta-hot-reload.md)
- ApiKeyReloader (sibling pattern): unified-trading-library `api_key_reloader.py`; the generic base this actually uses
  is `domain_config_reloader.py` (`DomainConfigReloader`)
- Strategy summary: [`/codex/09-strategy/strategy-summary.md`](/codex/09-strategy/strategy-summary.md)
- DART boundary: [`research-service-and-dart-integration.md`](research-service-and-dart-integration.md)
