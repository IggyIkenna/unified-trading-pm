---
doc_type: issue
title:
  live-strategy-config-hot-reload.md documents a safe-field allow-list and UnsafeConfigChangeError that do not exist —
  and the shipped reloader hot-swaps the instrument universe the doc lists as restart-required
summary: >-
  `/codex/04-architecture/live-strategy-config-hot-reload.md` (status `current`, `authoritative_for` the live
  strategy-config hot-reload contract) described a `StrategyConfigReloader` class that validates each config diff
  against a safe-field allow-list and raises `UnsafeConfigChangeError` for unsafe fields. Verified 2026-07-31 against
  `strategy-service/strategy_service/config_reloaders.py`: the capability IS shipped but under a different shape —
  module-level `start_domain_config_reloaders()` built on UTL `DomainConfigReloader` — and **none of the safety
  machinery exists**. There is no `StrategyConfigReloader`, no `UnsafeConfigChangeError` anywhere in the workspace, and
  no safe-list / allow-list / restart guard in the module (`rg -in 'unsafe|safe_list|allow_list|restart'` returns
  nothing). Every reload is an unconditional atomic swap. Most importantly, the doc's table lists "Underlying
  instruments = NO (position-state continuity is broken; restart required)", but `_on_instruments_reload()` hot-swaps
  `_active_instruments`, computes an added/removed delta, and fans it out via `INSTRUMENT_UNIVERSE_CHANGED` — so the
  exact change the doc calls unsafe is applied live today with no error raised.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [strategy]
repos: [strategy-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [strategy, live-trading, hot-reload, config, ssot-contradiction, safety]
related:
  [
    /codex/04-architecture/live-strategy-config-hot-reload.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md,
  ]
created: 2026-07-31
priority: P2
parent_epic: infrastructure_master
source: "slot-3, codex freshness re-review shard-B, discovered re-reviewing live-strategy-config-hot-reload.md, 2026-07-31"
execution_scope: local-only
drift_direction: needs-decision
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# Documented hot-reload safety machinery does not exist; instrument-universe row contradicts shipped behaviour

## Doc vs shipped (measured 2026-07-31)

| Doc claim                                                   | Shipped reality                                                                     |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| `StrategyConfigReloader` class registered at startup        | Module-level `start_domain_config_reloaders(service_config)` on UTL `DomainConfigReloader` |
| Emits `STRATEGY_CONFIG_RELOADED`                            | Emits `CONFIG_CHANGED` (`details.domain`) + `INSTRUMENT_UNIVERSE_CHANGED`           |
| Validates diff against a safe-field allow-list              | **No allow-list exists**; unconditional atomic swap                                 |
| Unsafe fields raise `UnsafeConfigChangeError`               | **Symbol does not exist anywhere in the workspace**                                 |
| "Underlying instruments — NO, restart required"             | `_on_instruments_reload()` hot-swaps the universe + notifies engines via delta       |
| "SAME validation rules apply batch and live"                | No validation gate on the live reload path at all                                    |

Also shipped but undocumented: `VersionGovernanceReloader` / `start_version_governance_reloader()` and
`StrategyDirectiveReloader` / `start_directive_reloader(poll_interval_seconds=60)`.

## Why this matters beyond naming

This doc is the SSOT an operator or agent would consult before changing a live strategy's config. It currently promises
a guard-rail that is not there. Two concrete risks:

1. **False confidence in a safety net.** An operator reading "unsafe-field changes raise `UnsafeConfigChangeError` and
   require a planned restart through DART" may push an archetype-family or instrument-universe change to a live
   strategy expecting the system to refuse it. Nothing refuses it.
2. **Unclear correctness on instrument swaps.** The design asserts that swapping the underlying instrument set breaks
   position-state continuity. The code does exactly that swap, live. Either the design concern is real (and we have a
   live correctness hazard on every instrument-universe reload), or the concern is obsolete (and the doc is scaring
   operators off a supported operation). Both readings are currently defensible from the corpus, which is precisely the
   problem.

Interim mitigation already applied: the codex doc now documents the shipped entry points and carries explicit ⚠️ blocks
stating that the allow-list and error type do not exist and that the instrument row is contradicted.

## Decision needed

- **A** — Implement the documented guard: add a safe-field allow-list + `UnsafeConfigChangeError` to
  `config_reloaders.py` so the codex contract becomes true. Preferred if the position-state-continuity concern is real.
- **B** — Retire the guard from the design: confirm instrument-universe hot-swap is intentional and safe (the delta
  callbacks suggest it was built deliberately), and rewrite the table to describe what is actually enforced.
- **C** — Split: keep hot-swap for the instrument universe (already relied on) but gate archetype-family changes only.

## Follow-ups

- [ ] [OPERATOR] P2. Rule between A / B / C — specifically, confirm whether a live instrument-universe swap is
      position-state-safe. Provenance: codex freshness re-review shard-B, 2026-07-31.
- [ ] [DOC] P3. Document `VersionGovernanceReloader` + `StrategyDirectiveReloader` in
      `/codex/04-architecture/live-strategy-config-hot-reload.md` — both are shipped and currently absent from the SSOT.
