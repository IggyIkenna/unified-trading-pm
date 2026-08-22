---
doc_type: codex-ssot
title: Multi-Venue Concurrent Routing
summary:
  "execution-service concurrent multi-venue routing — two-leg asyncio.gather execution with imbalance detection and a
  GCS-persisted blocked-spread circuit breaker (concurrent.py), plus SmartOrderRouter cross-DEX quote gathering and
  split routing for large SWAPs (sor.py); per-venue rate limits are hot-reloadable via RateLimitDomainConfig, not
  hardcoded. Sufficient for May-23; venue-level breaker is post-cutover."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [execution, defi, routing, circuit-breaker, self-healing, ssot]
related: [/codex/04-architecture/kill-switch-circuit-breaker.md, /codex/06-coding-standards/config-reloader-pattern.md]
created: 2026-05-20
authoritative_for:
  [
    multi-venue concurrent two-leg routing,
    SmartOrderRouter DEX split routing,
    blocked-spread per-spread circuit breaker,
  ]
referenced_by:
owner:
last_reviewed: 2026-08-22
code_refs:
---

# Multi-Venue Concurrent Routing

## Overview

Execution-service routes orders across multiple venues concurrently via two cooperating components:

- **`concurrent.py`** — two-leg `asyncio.gather` execution with imbalance detection and blocked-spread persistence
- **`algorithms/sor.py`** (`SmartOrderRouter`) — cross-DEX quote gathering + split routing for large SWAP orders

This pattern is **correct and sufficient for May-23** per the 2026-05-20 execution-service audit. Per-venue rate-limit
hardening is managed via hot-reloadable `RateLimitDomainConfig` (see rate-limits section below).

SSOT: `execution-service/execution_service/engine/concurrent.py` + `execution_service/algorithms/sor.py`.

---

## Two-leg concurrent execution (`concurrent.py:12`)

`execute_two_legs_concurrently()` dispatches both legs via `asyncio.gather` with a configurable per-leg timeout.

```
asyncio.gather(
    _execute_leg(leg_a_instruction),
    _execute_leg(leg_b_instruction),
)
```

**Imbalance detection**: if one leg succeeds and the other fails, the function:

1. Emits `CONCURRENT_LEG_IMBALANCE` (WARNING) + `CONCURRENT_LEG_CANCEL_UNCONFIRMED` (CRITICAL) structured events.
2. Marks `spread_id` as blocked in `BlockedSpreadsTracker`.
3. Persists the blocked set to GCS (`execution_gcs_bucket/blocked_spreads/blocked_spreads.json`).

**Blocked spread enforcement**: on subsequent calls, if `spread_id` is in the blocked set,
`execute_two_legs_concurrently()` raises `RuntimeError("Spread {id} is blocked due to prior imbalance")` before
dispatching any leg. Operator must explicitly clear the blocked state to resume.

**Timeout**: per-leg timeout passed as `timeout_ms` (default: caller's choice). Each leg runs under
`asyncio.wait_for(..., timeout=timeout_s)`.

### ConcurrentExecutionResult

```python
@dataclass
class ConcurrentExecutionResult:
    execution_id: str
    leg_a: LegResult
    leg_b: LegResult
    both_succeeded: bool          # True only when both legs return success
    imbalance_detected: bool      # True when exactly one leg failed
    timestamp: datetime
```

---

## SmartOrderRouter (`algorithms/sor.py:47`)

Routes SWAP (DEX) execution across Uniswap V3, Curve, and Balancer.

**Routing algorithm**:

1. Get quotes from all supported DEXs in parallel.
2. If a single venue has the best effective price with acceptable price impact → single-venue.
3. If order is large (price impact exceeds threshold) → split across venues to minimise slippage.
4. Gas costs included in routing decision.

**Key types**:

| Type             | Fields                                                                                        |
| ---------------- | --------------------------------------------------------------------------------------------- |
| `RouteQuote`     | `venue, token_in, token_out, amount_in, amount_out, price_impact_bps, fee_rate, gas_estimate` |
| `OptimizedRoute` | `routes: list[(venue, pct, quote)], total_amount_out, total_price_impact_bps, is_split`       |

**Supported venues** (`SUPPORTED_VENUES`): `UNISWAP_V3` (fee tiers: 100/500/3000/10000 bps), `CURVE`, `BALANCER`.

**Extension**: add a new venue by adding an entry to `SUPPORTED_VENUES` and implementing the quote-fetch method. No
changes to the routing algorithm itself.

---

## Per-venue rate limits (hot-reloadable)

Rate limits are NOT hardcoded. `config_reloaders.py` runs a `DomainConfigReloader[RateLimitDomainConfig]` that watches
the rate-limits domain config in GCS and applies updates atomically via `get_active_rate_limits()`.

```
DomainConfigReloader (domain="rate-limits")
  └─ on reload: _active_rate_limits = config  (atomic swap)
  └─ get_active_rate_limits() → latest config (or None before first load)
```

Rate limits are per-client (via per-process isolation) and per-venue. Adding a new venue's rate config requires only a
GCS config push; no deployment needed.

---

## Circuit breaker pattern

The blocked-spread mechanism in `concurrent.py` acts as a per-spread circuit breaker:

```
first leg imbalance → BLOCKED (no further execution on that spread)
operator clears → UNBLOCKED (execution resumes)
```

For venue-level circuit breaking (temporary venue outage → stop routing to that venue), extend `BlockedSpreadsTracker`
with a venue-keyed blocked set — the GCS persistence pattern composes directly. Per the 2026-05-20 audit (Group H plan
Phase 6), the current pattern is **sufficient for May-23**; venue-level circuit breaking is Phase E.1 (post-cutover).

---

## Not in May-23 cutover scope

> **[DELTA 2026-05-22]** **Current state:** Two-leg concurrent execution and SmartOrderRouter (Uniswap V3 / Curve /
> Balancer) are shipped and correct for the May-23 cutover. Venue-level circuit breaker is not implemented. **Planned
> delta:** `plans/epics/execution_master.md` Phase E.1 owns venue-level circuit breaker post-cutover. **Target
> architecture:** Per-venue circuit breaker extends `BlockedSpreadsTracker` with a venue-keyed blocked set; GCS
> persistence pattern composes directly.

- Venue-level circuit breaker (Phase E.1 — tracked in `plans/epics/execution_master.md`)
- Cross-chain bridge routing through SOR (bridge has its own `BridgeHandler` in `v2/handlers.py`)
- CeFi (CEX) order routing does NOT go through SOR — CEX orders use venue-specific adapters in
  `adapters/order_adapter.py`
