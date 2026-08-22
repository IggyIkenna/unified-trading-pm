---
doc_type: codex-ssot
title: Live strategy-config hot-reload
summary:
  "strategy-service hot-applies config deltas mid-session without restart via strategy_service/config_reloaders.py (UTL
  DomainConfigReloader family, same shape as ApiKeyReloader), emitting CONFIG_CHANGED / INSTRUMENT_UNIVERSE_CHANGED on
  atomic swap. The strategies-domain safe-field allow-list (SAFE_STRATEGY_RELOAD_FIELDS) and UnsafeConfigChangeError are
  now IMPLEMENTED (2026-08-14): strategy_params changes hot-reload, enabled_strategies changes are rejected (previous
  config stays active). The instruments domain has the SAME shape of guard (2026-08-21, SAFE_INSTRUMENT_RELOAD_FIELDS
  / UnsafeConfigChangeError): subscription_list membership (add/remove) hot-swaps live, any other field change
  (an existing instrument's definition) is rejected and requires a restart. Batch and live share the same config
  object."
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
last_reviewed: 2026-08-21
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
> `strategy-service/strategy_service/config_reloaders.py`, built on UTL's generic `DomainConfigReloader`
> (`unified_trading_library/domain_config_reloader.py`) — the same family as `ApiKeyReloader`, `LifecycleReloader` and
> `InstrumentLifecycleCacheDeltaReloader`.

Entry points (module-level functions, not a single class):

| Function                                                                           | Role                                                 |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `start_domain_config_reloaders(service_config)`                                    | Starts the strategies + instruments domain reloaders |
| `stop_domain_config_reloaders()`                                                   | Teardown                                             |
| `get_active_strategy_config()` / `get_active_instruments()`                        | Read the current atomically-swapped snapshot         |
| `register_instrument_change_callback(...)`                                         | Subscribe an engine to instrument-universe deltas    |
| `start_version_governance_reloader()` (`VersionGovernanceReloader`)                | Strategy-version governance refresh                  |
| `start_directive_reloader(poll_interval_seconds=60)` (`StrategyDirectiveReloader`) | Directive polling                                    |

On reload the callbacks perform an **atomic swap** of the module-level snapshot, then emit lifecycle events. The
instruments path additionally computes an added/removed delta against the previous snapshot and fans it out to
registered callbacks (shard-isolated: one callback failing does not block the others).

**Events actually emitted** — `CONFIG_CHANGED` (with `details.domain` = `strategies` | `instruments`) and
`INSTRUMENT_UNIVERSE_CHANGED` (added/removed counts + a 5-item sample). There is **no `STRATEGY_CONFIG_RELOADED`
event**; that name appears nowhere in the workspace.

## What can hot-reload safely

> **✅ Enforced for BOTH the strategies and instruments domains — strategies landed 2026-08-14
> (`strategy-service@48bd3717`), instruments landed 2026-08-21 (`strategy-service@21d46d75`) per the
> operator ruling below; NOT the same commit as strategies despite an earlier version of this doc's false claim that
> `48bd3717` already shipped both.**
> `config_reloaders.py` carries `SAFE_STRATEGY_RELOAD_FIELDS = frozenset({"strategy_params"})` for strategies and
> `SAFE_INSTRUMENT_RELOAD_FIELDS` (subscription_list membership only) for instruments, both backed by
> `UnsafeConfigChangeError`. `_on_strategies_reload` diffs the incoming `StrategyDomainConfig` field-by-field
> (skipping the first-ever load, which has no baseline to diff against); a change to `strategy_params` swaps
> atomically as before, a change to `enabled_strategies` raises `UnsafeConfigChangeError` and the previously active
> config stays in effect. `_on_instruments_reload` calls `_reject_unsafe_instrument_change()` the same way: an
> add/remove of `instrument_id`s in `subscription_list` hot-swaps live as before, but a change to any OTHER field —
> i.e. the DEFINITION of an instrument that stays in the universe — raises `UnsafeConfigChangeError` and the
> previous config stays active. In both cases the reloader base's `FieldFilteredCallbackRegistry.notify` catches the
> `RuntimeError` subclass and logs it — the process does not crash and no restart is forced automatically; an
> operator still has to actually perform the restart to apply the rejected change.

| Field class                                | Hot-reload safe?  | Notes                                                                                                                           |
| ------------------------------------------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Sizing (notional, weights)                 | Yes               | `strategy_params` — applies to next signal; existing orders untouched                                                           |
| Risk caps (per-position max)               | Yes               | `strategy_params` — cap drops trigger an immediate halt of orders that exceed                                                   |
| Venue-routing weights                      | Yes               | `strategy_params` — applies to next signal                                                                                      |
| Signal-filter thresholds                   | Yes               | `strategy_params` — applies to next signal                                                                                      |
| Kill-switch flags                          | Yes               | `strategy_params` — immediate; in-flight orders paused                                                                          |
| Strategy archetype family                  | **NO — enforced** | `enabled_strategies` change raises `UnsafeConfigChangeError`; restart required                                                  |
| Underlying instruments — add/remove        | **Yes**           | `subscription_list` membership change hot-swaps live (`_on_instruments_reload()` delta + `INSTRUMENT_UNIVERSE_CHANGED` fan-out) |
| Underlying instruments — definition change | **NO — enforced** | any other field on an existing instrument raises `UnsafeConfigChangeError`; restart required                                    |

**RESOLVED 2026-08-21 — corrected from an earlier stale "option B, unconditional" framing.** An intermediate version
of this doc briefly said the operator ruled the live hot-swap unconditional and intentional for ALL instrument-domain
changes ("option B"). That was imprecise — the actual ruling (confirmed directly by the operator, and matching what
the code has done since 2026-08-14) is: **hot-swap applies to `subscription_list` membership only (adding/removing
instrument_ids); changing the DEFINITION of an existing instrument requires a restart and is rejected, not silently
applied.** This is exactly what `_reject_unsafe_instrument_change()` in `config_reloaders.py` now enforces (shipped
strategy-service `21d46d75`, 2026-08-21). **Correction to this doc's own prior text**: an earlier
version of this section claimed the instruments guard shipped in `48bd37175989be9031eccc1b5dca0c7ab387abb3` — that
commit's own diff (`git show 48bd3717 -- strategy_service/config_reloaders.py`) contains zero occurrences of
`SAFE_INSTRUMENT_RELOAD_FIELDS`/`_reject_unsafe_instrument_change`; it shipped ONLY the strategies-domain guard. The
instruments guard did not exist until the 2026-08-21 shipment cited above — verified by measurement, not assumed. See
`/plans/archive/2026_08/issues/instrument_universe_hotswap_position_state_safety_unruled_2026_08_14.md` for the
archived judgment-call history and `/codex/04-architecture/cross-domain-state-fabric.md` §14 for the cross-reference.

## Live = batch

Backtest replays consume the same config object. A config change in batch is just a new run; live applies it via
hot-reload. **Caveat (2026-08-14, updated):** the strategies-domain reload path now has a validation gate
(`SAFE_STRATEGY_RELOAD_FIELDS` / `UnsafeConfigChangeError`) — an `enabled_strategies` change is rejected on the live
side. Batch has no equivalent gate (a batch run just picks up whatever config it's given), so this is not yet "the SAME
validation rules apply both paths", only a live-side-only guard against one specific unsafe field. The instruments
reload path has the SAME class of guard as of 2026-08-21 (see above — its guard shipped a week after the
strategies-domain one, not the same date); the clients reload path still applies an unconditional atomic swap with no
validation gate.

## Cross-references

- Config reloader pattern (workspace standard):
  [`/codex/06-coding-standards/config-reloader-pattern.md`](/codex/06-coding-standards/config-reloader-pattern.md)
- Instrument lifecycle delta:
  [`instrument-lifecycle-cache-delta-hot-reload.md`](instrument-lifecycle-cache-delta-hot-reload.md)
- ApiKeyReloader (sibling pattern): unified-trading-library `api_key_reloader.py`; the generic base this actually uses
  is `domain_config_reloader.py` (`DomainConfigReloader`)
- Strategy summary: [`/codex/09-strategy/strategy-summary.md`](/codex/09-strategy/strategy-summary.md)
- DART boundary: [`research-service-and-dart-integration.md`](research-service-and-dart-integration.md)
