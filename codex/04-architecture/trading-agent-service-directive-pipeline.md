# Trading-Agent Service — Directive Pipeline Architecture

## Overview

trading-agent-service is a layer-7 subscriber-emitter in the unified trading system. It subscribes to
`StrategyPnlStreamEvent` (from strategy-service) and feature events (from features-service, including the
`performance_features` subdomain). It emits `ArchetypeAllocationDirective` consumed by strategy-service
`StrategyDirectiveReloader`. The service is **off-by-default** for the May-23 cutover — data flow is wired end-to-end
but no directive is emitted unless explicitly enabled. Production allocator logic (ML/LLM integration, automatic
re-weighting, multi-archetype engines) ships post-cutover via epic `strategy_and_dart_master_2026_05_07.md` §1.7 Phase
10.7 + § Allocator service.

## Data Flow

```
strategy-service
  → [STRATEGY_PNL_STREAM event / StrategyPnlStreamEvent]
      → trading-agent-service (AllocationDirectiveLoop)
          → [ArchetypeAllocationDirective]
              → strategy-service StrategyDirectiveReloader
                  → portfolio_allocator AllocatorArchetypeEngine.weight_with_directive()
                      → strategy execution (live + continuous paper)
                          → emits PnL → feeds back to top
```

features-service (`performance_features` subdomain) also feeds trading-agent-service:

```
features-service performance_features
  → [performance feature events]
      → trading-agent-service (AllocationDirectiveLoop context)
```

## UAC Contracts

- `unified_api_contracts.internal.strategy_pnl_stream.StrategyPnlStreamEvent` — PnL stream emitted by strategy-service
  per archetype per tick. Shipped: uac@82b7ad55 (Phase 1) + uac@2bdc0f07 (Phase 4 facade).
- `unified_api_contracts.internal.strategy_directives.ArchetypeAllocationDirective` — directive consumed by
  strategy-service `StrategyDirectiveReloader`. Named `ArchetypeAllocationDirective` (not `AllocationDirective`) to
  avoid collision with existing `internal/architecture_v2/schemas.py:390` full post-cutover multi-client schema.

## Key Modules

- `trading_agent_service/core/allocation_directive_loop.py` — main subscriber loop; subscribes to PnL + feature streams;
  emits no-op directive by default (Phase 6).
- `strategy_service/config_reloaders.py:StrategyDirectiveReloader` — in-memory directive store with TTL eviction +
  thread-safe access (Phase 5).
- `strategy_service/portfolio_allocator/archetypes.py:weight_with_directive()` — consumes directive from reloader; falls
  through to static config when no directive present (Phase 5).
- `trading_agent_service/replay/` — backtest-replay infrastructure: `inference_cache.py`, `directive_log.py`,
  `cutoff_clamp.py` (Phase 6.5).

## Backtest-Replay Infrastructure

`trading_agent_service/replay/` provides lookahead-bias-safe replay for backtests:

- `inference_cache.py` — caches directive decisions keyed by (archetype_id, as_of_ts); read-only after cutoff.
- `directive_log.py` — append-only log of emitted directives with timestamps for audit + replay.
- `cutoff_clamp.py` — enforces that no directive emitted after `cutoff_ts` is visible to the backtest harness.

UAC contracts for replay: uac@20567882 + trading-agent@33a7ae9.

## Off-by-Default Safety

Two layers of safety ensure the service cannot accidentally affect live trading before it is explicitly enabled:

1. **No directive present**: `weight_with_directive()` in `AllocatorArchetypeEngine` detects absent directive via
   `StrategyDirectiveReloader.get_directive(archetype_id)` returning `None` → falls through to static config weight
   unchanged.
2. **`enabled=False` directive**: if a directive is present but has `enabled=False`, `weight_with_directive()` returns a
   zero-weight snapshot — archetype is effectively paused.

The service is wired as off-by-default in the May-23 live run: no upstream emitter sends a non-no-op directive unless
the operator explicitly configures one.

## Post-Cutover Scope

The following items are explicitly out of May-23 scope and tracked in
`plans/epics/strategy_and_dart_master_2026_05_07.md` §1.7 Phase 10.7 + § Allocator service:

- Production allocator logic (PnL-weighted, Sharpe-weighted, Risk-Parity, Kelly, Min-CVaR engines)
- LLM/ML integration (slow features, narrative context, regime detection)
- IM-side UI (human-approved weight changes, multi-sign workflows, audit trail)
- Trading-platform-side UI (client target weight vector → auto-apply directives)
- Automatic re-weighting cadence (DAILY / HOURLY / WEEKLY / ON_EVENT scheduler)
- Shadow mode (primary + shadow allocator instance per client)
- NAV reads from PBMS
- Cross-share-class NAV conversion + audit log retention per directive
