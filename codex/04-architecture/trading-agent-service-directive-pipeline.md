---
scope: [engineer, admin]
---

# Trading-Agent Service — Directive Pipeline Architecture

> **Created**: 2026-05-20 — Phase 8 of `trading_agent_service_architecture_unlock_2026_05_22.md` **Status**:
> Architecture shipped (Phases 1-6.5 done); production logic post-cutover. **Tier**: Tier-1 architecture-only (data flow
> wired by May-23; production allocator logic post-cutover).

---

## Overview

trading-agent-service is a layer-7 subscriber-emitter in the unified trading system. It subscribes to
`StrategyPnlStreamEvent` (from strategy-service) and feature events (from features-service, including the
`performance_features` subdomain). It emits `ArchetypeAllocationDirective` consumed by strategy-service
`StrategyDirectiveReloader`. The service is **off-by-default** for the May-23 cutover — data flow is wired end-to-end
but no directive is emitted unless explicitly enabled. Production allocator logic (ML/LLM integration, automatic
re-weighting, multi-archetype engines) ships post-cutover via epic `plans/epics/trading_agent_master.md` (canonical
post-cutover SSOT; the old forward pointer to `strategy_and_dart_master_SUPERSEDED_2026_05_21.md` §1.7 Phase 10.7 was
updated 2026-05-22 to point at `trading_agent_master.md` — `strategy_and_dart_master_SUPERSEDED_2026_05_21.md` is
superseded as of 2026-05-21).

### Closed-loop diagram

```
features-service (performance_features)
       |
       ↓ FeaturesComputedEvent (feature_group=performance_features)
trading-agent-service
       |
       | AllocationLoopEntry (AllocationDirectiveLoop)
       |   reads: StrategyPnlStreamEvent (from strategy-service)
       |   reads: FeaturesComputedEvent (from features-service)
       |   emits: ArchetypeAllocationDirective (off-by-default; no-op stub May-23)
       ↓
strategy-service StrategyDirectiveReloader
       |
       | get_directive(archetype_id) → ArchetypeAllocationDirective | None
       ↓
BaseArchetypeEngineV2.weight_with_directive()
       |
       ↓ modified allocation weights (no-op when directive absent)
execution-service
```

---

## Data Flow

### 1. Strategy → trading-agent (PnL stream)

strategy-service engines (carry + APD archetypes, May-23) emit `StrategyPnlStreamEvent` per tick:

```python
from unified_api_contracts.internal import StrategyPnlStreamEvent
log_event(UTL.STRATEGY_PNL_STREAM, details=StrategyPnlStreamEvent(...).model_dump())
```

trading-agent-service `AllocationDirectiveLoop` subscribes and accumulates. See UAC:
`unified_api_contracts/internal/strategy_pnl_stream.py`.

Narrative form:

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

### 2. Features → trading-agent (performance features)

features-service `performance_features/` subdomain (Phase-H scaffold) emits passthrough PnL features:

```
gs://{features-bucket}/by_date/day={date}/feature_group=performance_features/features.parquet
```

Off-by-default for May-23: no upstream PnL stream wired yet → `record_empty(reason=EXPECTED_NO_PNL_STREAM)`.

Narrative form:

```
features-service performance_features
  → [performance feature events]
      → trading-agent-service (AllocationDirectiveLoop context)
```

### 3. trading-agent → strategy (AllocationDirective)

trading-agent-service `AllocationDirectiveLoop` emits `ArchetypeAllocationDirective` per archetype:

```python
from unified_api_contracts.internal import ArchetypeAllocationDirective
directive = ArchetypeAllocationDirective(
    archetype_id="carry_staked_basis",
    allocation_weight=Decimal("0.5"),
    enabled=True,
    valid_from=now,
    valid_until=now + timedelta(hours=1),
    source="trading-agent-service",
    available_at=now,
)
```

strategy-service `StrategyDirectiveReloader.inject_directive(directive)` receives it. See UAC:
`unified_api_contracts/internal/strategy_directives.py`.

### 4. strategy-service applies directive

```python
directive = reloader.get_directive(archetype_id)  # None if absent/expired
weight = engine.weight_with_directive(directive)   # fallback to static config if None
```

TTL eviction: directives with `valid_until < now` are silently evicted. Caller uses static config as fallback.
`enabled=False` directives are stored and returned; caller must check `.enabled`.

---

## UAC Contracts

- `unified_api_contracts.internal.strategy_pnl_stream.StrategyPnlStreamEvent` — PnL stream emitted by strategy-service
  per archetype per tick. Shipped: uac@82b7ad55 (Phase 1) + uac@2bdc0f07 (Phase 4 facade).
- `unified_api_contracts.internal.strategy_directives.ArchetypeAllocationDirective` — directive consumed by
  strategy-service `StrategyDirectiveReloader`. Named `ArchetypeAllocationDirective` (not `AllocationDirective`) to
  avoid collision with existing `internal/architecture_v2/schemas.py:390` full post-cutover multi-client schema.

### Schemas table

| Schema                         | Location                                                | Purpose                                   |
| ------------------------------ | ------------------------------------------------------- | ----------------------------------------- |
| `StrategyPnlStreamEvent`       | `unified_api_contracts/internal/strategy_pnl_stream.py` | PnL per-tick stream from strategy → agent |
| `ArchetypeAllocationDirective` | `unified_api_contracts/internal/strategy_directives.py` | Directive from agent → strategy reloader  |

Both are in `unified_api_contracts.internal` (not public surface) — internal coordination types. Import:
`from unified_api_contracts.internal import StrategyPnlStreamEvent, ArchetypeAllocationDirective`.

---

## Key Modules

- `trading_agent_service/core/allocation_directive_loop.py` — main subscriber loop; subscribes to PnL + feature streams;
  emits no-op directive by default (Phase 6).
- `strategy_service/config_reloaders.py:StrategyDirectiveReloader` — in-memory directive store with TTL eviction +
  thread-safe access (Phase 5).
- `strategy_service/portfolio_allocator/archetypes.py:weight_with_directive()` — consumes directive from reloader; falls
  through to static config when no directive present (Phase 5).
- `trading_agent_service/replay/` — backtest-replay infrastructure: `inference_cache.py`, `directive_log.py`,
  `cutoff_clamp.py` (Phase 6.5).

---

## Backtest-Replay Infrastructure

`trading_agent_service/replay/` provides lookahead-bias-safe replay for backtests:

- `inference_cache.py` — caches directive decisions keyed by (archetype_id, as_of_ts); read-only after cutoff.
- `directive_log.py` — append-only log of emitted directives with timestamps for audit + replay.
- `cutoff_clamp.py` — enforces that no directive emitted after `cutoff_ts` is visible to the backtest harness.

UAC contracts for replay: uac@20567882 + trading-agent@33a7ae9.

---

## Off-by-Default Safety

Two layers of safety ensure the service cannot accidentally affect live trading before it is explicitly enabled:

1. **No directive present**: `weight_with_directive()` in `AllocatorArchetypeEngine` detects absent directive via
   `StrategyDirectiveReloader.get_directive(archetype_id)` returning `None` → falls through to static config weight
   unchanged.
2. **`enabled=False` directive**: if a directive is present but has `enabled=False`, `weight_with_directive()` returns a
   zero-weight snapshot — archetype is effectively paused.

The service is wired as off-by-default in the May-23 live run: no upstream emitter sends a non-no-op directive unless
the operator explicitly configures one.

**Flip from off to on**: operator sets `DIRECTIVE_EMISSION_ENABLED=true` env var on trading-agent VM after paper-trade
validation confirms signal quality. No code change required.

---

## Post-Cutover Scope

The following items are explicitly out of May-23 scope and tracked in `plans/epics/trading_agent_master.md` (canonical
post-cutover SSOT, supersedes `strategy_and_dart_master_SUPERSEDED_2026_05_21.md`):

- Production allocator logic (PnL-weighted, Sharpe-weighted, Risk-Parity, Kelly, Min-CVaR engines)
- LLM/ML integration (slow features, narrative context, regime detection)
- IM-side UI (human-approved weight changes, multi-sign workflows, audit trail)
- Trading-platform-side UI (client target weight vector → auto-apply directives)
- Automatic re-weighting cadence (DAILY / HOURLY / WEEKLY / ON_EVENT scheduler)
- Shadow mode (primary + shadow allocator instance per client)
- NAV reads from PBMS
- Cross-share-class NAV conversion + audit log retention per directive

---

## Foundation Gate Ordering

| Layer | Service               | Gate                                                                   | Status                   |
| ----- | --------------------- | ---------------------------------------------------------------------- | ------------------------ |
| 4     | UAC                   | `StrategyPnlStreamEvent` + `ArchetypeAllocationDirective` schemas land | ✅ uac@82b7ad55          |
| 5     | strategy-service      | `StrategyDirectiveReloader` ships; PnL emission wired                  | ✅ strategy@afd17fe9     |
| 6     | trading-agent-service | `AllocationDirectiveLoop` scaffold + ServiceBootstrap + Health API     | ✅ trading-agent@119fa74 |
| 6.5   | trading-agent-service | Backtest-replay infrastructure (inference cache + directive log)       | ✅ trading-agent@33a7ae9 |
| 7     | trading-agent-service | CI green on `live-defi-rollout` (GH_PAT rotation needed)               | ⏳ BLOCKED-CREDENTIALS   |
| 8     | PM                    | Codex + plan updates (this file)                                       | ✅ this commit           |

---

## Successor Plans

- **Production allocator logic**: `plans/epics/trading_agent_master.md` — Allocator-as-shared-service split +
  post-cutover allocation engines. (`strategy_and_dart_master_SUPERSEDED_2026_05_21.md` was the prior pointer;
  superseded 2026-05-21.)
- **UTL lift**: `strategy_repo_consolidation_2026_05_19.md` — `StrategyDirectiveReloader` → `make_directive_reloader()`
  post-cutover.
- **Multi-archetype PnL emission**: per-archetype plans (cefi/defi/sports/predictions/tradfi masters) — each adds
  `StrategyPnlStreamEvent` emission in their own schedule.
- **features performance_features real derivations**: post-cutover, after production allocator ships.

---

## Continuous Verification

At any point in time, all of the following MUST be true:

1. `rg "StrategyDirectiveReloader" strategy-service/strategy_service/config_reloaders.py` → match exists.
2. `rg "StrategyPnlStreamEvent" strategy-service/strategy_service/` → ≥2 call sites (carry + APD engines).
3. `rg "AllocationDirectiveLoop" trading-agent-service/trading_agent_service/` → match exists.
4. `cd strategy-service && bash scripts/quality-gates.sh` → passes (includes 4 StrategyDirectiveReloader unit tests).
5. `cd trading-agent-service && bash scripts/quality-gates.sh` → passes (includes ≥5 AllocationDirectiveLoop tests).

QG STEP enforcement: steps 5.61 (ServiceBootstrap) + 5.62 (Health API) verified per-commit on both services.
