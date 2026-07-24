---
doc_type: codex-ssot
title: Adapter dead-code, runtime-fallback, and duplicate-implementation ban
summary: >-
  States explicitly what no existing mechanism states: adapter/handler modules (instruments-service reference-data
  adapters, MTDS market-interface adapters, execution-service trade-execution adapters) must not carry dead
  (referenced-but-never-scheduled) code, must not mask a real upstream failure behind a silent runtime fallback, and
  must not maintain two parallel implementations of the same venue/chain without a stated, live-routing reason for both.
  Closes a real gap found 2026-07-24: cefi's execution-service adapters have unaudited parallel
  `*_ccxt.py`/`*_native.py` pairs per venue (binance/bybit/okx) whose live-routing status is unaddressed anywhere.
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service, execution-service, unified-api-contracts]
scope: [engineer]
tags: [dead-code, fallback, duplicate-adapter, adapters, quality-gates, vulture]
related:
  [
    /codex/06-coding-standards/quality-gates.md,
    /codex/06-coding-standards/thin-adapters-pattern.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
authoritative_for: [adapter dead-code / runtime-fallback / duplicate-implementation ban]
created: "2026-07-24"
last_updated: "2026-07-24"
referenced_by:
owner:
last_reviewed:
code_refs:
---

# Adapter dead-code, runtime-fallback, and duplicate-implementation ban

## Why this doc exists

Three existing mechanisms each cover part of this ground but none covers adapters specifically, and the gap is real:

- **`vulture`** (dead-code detection, advisory — see `quality-gates.md` § "Dead Code Detection (vulture)") is
  corpus-wide and blind to code that IS referenced somewhere (e.g. registered in a factory/dispatch table) but never
  actually scheduled/invoked at runtime — exactly the shape a stale duplicate adapter takes.
- **`scripts/quality_gates/check_no_fallback_imports.py`** bans only import-time fallback shims
  (`try/except ImportError`), not runtime fallback logic (a request handler catching a real adapter error and silently
  routing to a degraded/legacy path instead of surfacing the failure).
- **The UTL/UAC reuse audit** targets service-vs-library duplication (should this logic live in a shared library instead
  of being reimplemented per-service) — not adapter-vs-adapter duplication within the SAME service/venue.

None of the three would have caught, or would catch going forward, two parallel adapter implementations for the same
venue silently diverging (one live-routed, one dead code nobody remembers to delete) — the cefi
`*_ccxt.py`/`*_native.py` case found 2026-07-24 (see `/plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md` §1)
is the concrete instance that surfaced this gap.

## The rule

For every adapter/handler module under an asset group's:

- `instruments-service/instruments_service/reference_data/adapters/<ag>/`
- `market-tick-data-service/market_tick_data_service/market_interface/adapters/<ag>/` (and the `_live`/`onchain*`
  siblings where they exist)
- `execution-service/execution_service/trade_execution/adapters/` (venue files scoped to that AG)

three things must hold, and an audit finding is required (not optional) whenever they don't:

1. **No dead code** — a module/class/function that is defined and registered somewhere (an adapter factory, a venue
   dispatch table, a `VENUE_TO_ADAPTER_KEY` entry) but never actually reached by any live code path is dead code, even
   though `vulture` won't flag it (it IS referenced). Either delete it or document why it's intentionally kept (e.g.
   behind a feature flag with a stated activation path).
2. **No runtime fallback masking a real failure** — a handler that catches an adapter-level error and silently
   substitutes degraded/stale/legacy behavior instead of surfacing the failure (loudly, per this workspace's general
   fail-loud convention) is banned. A genuine, intentional fallback (e.g. a documented multi-source failover) must be
   named as such and logged/alerted when it fires — not a silent catch-and-continue.
3. **No duplicate implementation without a stated reason** — if two files implement the SAME venue/chain (the
   `*_ccxt.py`/`*_native.py` pattern), the doc/code must state explicitly which is live-routed, whether both are (and
   why — e.g. one is a migration in progress, one is a documented A/B), or that one is dead and pending deletion.
   Silence on this question is itself the violation — "we have two files and nobody knows which one runs" is never an
   acceptable resting state.

## Enforcement (current: manual audit, not yet automated)

This rule is enforced today by the per-AG adapter audit todos tracked in each asset group's consolidated closeout plan
(`tradfi_consolidated_closeout_2026_07_18.md`, `defi_consolidated_closeout_2026_07_18.md`,
`cefi_consolidated_closeout_2026_07_18.md`, `prediction_consolidated_closeout_2026_07_18.md`,
`sports_consolidated_closeout_2026_07_19.md` — see each plan's audit todo added per
`/plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md` §1), not by a standalone script. A future automated
check (e.g. a registered-but-uncalled-in-production static analysis pass, or a runtime coverage instrumentation pass
over a full backfill run) is out of scope for this doc — file it as its own todo against the owning plan if pursued.

## Cross-links

Referenced from `README.md`'s Document Map (see the "Forbidden code patterns" row, repointed here 2026-07-24 — the row's
original target, `STANDARDS.md`, never existed in this directory) and from `quality-gates.md`'s vulture section (adapter
dead code is exactly the blind spot vulture has — see "Why this doc exists" above).
