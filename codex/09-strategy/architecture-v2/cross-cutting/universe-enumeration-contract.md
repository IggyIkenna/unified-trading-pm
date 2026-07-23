---
doc_type: codex-ssot
title: Universe Enumeration Contract
summary:
  "Strategy universe-enumeration contract: archetypes enumerate their tradeable universe via instruments-service
  `InstrumentRecord` queries (no hardcoded instrument lists), with mandatory `asset_group` / `is_active` /
  `instrument_type` filters, ≤60min cache invalidated on `INSTRUMENT_UNIVERSE_CHANGED`; universe size sets expected
  cluster count."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service]
scope: [engineer]
tags: [instruments, strategy, catalogue, manifest, uac]
related:
  [
    ../../../04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md,
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-execution-runtime.md,
  ]
created: 2026-05-22
authoritative_for:
  [strategy universe-enumeration contract (InstrumentRecord query rules + no-hardcoded-lists + cache/refresh)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-execution-runtime.md,
    /codex/09-strategy/architecture-v2/cross-cutting/treasury-trading-wallet-invariant.md,
  ]
owner:
last_reviewed: 2026-05-22
code_refs:
---

# Universe Enumeration Contract

> **[DELTA 2026-05-22]** **Current state:** Universe enumeration is done via instruments-service but the contract (how
> strategies enumerate valid instruments) is undocumented at codex level. Discovery via
> `strategy_archetype_logic_audit_2026_05_20.md`. **Planned delta:** Full enumeration contract per `strategy_master.md`.
> **Target architecture:** Canonical: strategies enumerate universe via `InstrumentRecord` query to instruments-service;
> no hardcoded instrument lists.

## Context

Covers how strategy archetypes enumerate their tradeable universe via the instruments-service SSOT. The contract governs
what queries are valid, what filters must be applied, and what caching semantics apply.

## Current State

Universe enumeration is implemented via instruments-service `InstrumentRecord` queries. Archetypes call the
instruments-service API or use a cached local snapshot. The specific query shape, required filters, and caching TTL are
not centralised in a codex doc.

## The Contract

**Rule 1 — No hardcoded instrument lists.** Strategies MUST NOT embed instrument IDs, ticker lists, or venue-pair maps
in code or config. All universe membership is derived from `InstrumentRecord` at runtime.

**Rule 2 — Query via instruments-service, not MTDS.** The instruments-service is the SSOT for reference data
(`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`). MTDS is market data only.

**Rule 3 — Mandatory filters at query time.** Every universe query MUST supply:

- `asset_group` — limits scope to the archetype's domain
- `is_active=True` — excludes delisted / expired instruments
- `instrument_type` — matches the archetype's trading instrument class (PERPETUAL / SPOT / STAKED / etc.)

**Rule 4 — Cache with TTL, refresh on `INSTRUMENT_UNIVERSE_CHANGED` event.** Archetypes MAY cache the universe snapshot
for up to 60 minutes. They MUST subscribe to the `INSTRUMENT_UNIVERSE_CHANGED` event from instruments-service and
invalidate on receipt.

**Rule 5 — Cluster validation must match universe cardinality.** The universe enumeration result sets the `expected_*`
cluster count used in `record_captured(cluster_validation=...)`. Drift between universe size and expected cluster count
is a manifest correctness bug.

## Canonical query shape (target)

```python
from unified_trading_library.instruments_client import InstrumentsClient

client = InstrumentsClient(config=...)
universe = client.enumerate_universe(
    asset_group="defi",
    instrument_type="STAKED",
    is_active=True,
)
# returns list[InstrumentRecord]
```

Full spec (including pagination, partial-failure handling, fallback to cached snapshot on IS outage) is owned by
`plans/epics/strategy_master.md`.

## See also

- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`
- `plans/epics/strategy_master.md`
- `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`
- `/codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md`
