---
doc_type: issue
title: feature_builder_registry resolve_build_order() is dead code in 5 of 6 features-service engines
summary: >-
  Only sports/tracking's feature_builder_registry.resolve_build_order() is actually called by its orchestrator.
  cross_instrument, delta_one, multi_timeframe, onchain, and volatility each carry the same
  registry+depends_on+resolve_build_order() scaffolding, but grep confirms no orchestrator/service in those 5 ever calls
  resolve_build_order() or otherwise honors depends_on — it's pure dead documentation, not a wired pipeline stage.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [features]
repos: [features-service]
scope: [engineer]
tags: [features-service, dag, dead-code, audit, cross-cutting]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/colocated_feature_pipeline_in_memory_handoff_2026_06_21.md,
  ]
created: "2026-08-01"
source: >-
  Discovered mid-task while implementing the in-memory DAG handoff fix for cross_instrument's
  composite_sr/flow_interaction (cross_cutting_satellite_ao_dispatch_batch1-003).
assigned_vm: planning
execution_scope: orchestrator-agent
parent_epic: features_and_ml_master
priority: P2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
last_updated: "2026-08-01"
locked_by:
locked_since:
resolved_by:
---

# feature_builder_registry DAG scaffolding is dead code outside sports

## What I found

While wiring cross_instrument's `composite_sr`/`flow_interaction` in-memory hand-off (fixed: `composite_sr` was ALWAYS
null in production because nothing ever threaded its `wall_df`/`cluster_df` constructor args), I checked whether the
same gap existed elsewhere. `rg -rn "resolve_build_order"` across `features_service/` shows every engine
(`cross_instrument`, `delta_one`, `multi_timeframe`, `onchain`, `volatility`, `calendar`) carries a near-identical
`schemas/feature_builder_registry.py` — a `BUILDER_REGISTRY`

- `depends_on` metadata + `resolve_build_order()` topological sort. Only `sports/tracking/feature_builder_registry.py`'s
  own docstring says "the pipeline exporter calls `resolve_build_order()`" — and only sports's actual exporter does.
  None of the other 5 engines' orchestrators/batch-handlers/services ever call `resolve_build_order()` or
  `get_all_builders()` to sequence work; each just iterates its own flat `feature_groups` list.

For cross_instrument this was a real correctness bug (composite_sr's constructor DOES accept the upstream frame — just
never received it — fixed this session, `features-service@b457ee43`). For **delta_one** specifically, I checked the 3
declared-dependent groups (`risk_reward`, `wedge_quality`, `confluence` — depend on
`polynomial_trendlines`/`volatility_realized`/`technical_indicators`/`volume_analysis`/ `market_structure` per the
registry): none of their calculator classes override `__init__` to accept an upstream-injected DataFrame — they
recompute everything from raw OHLCV internally (e.g. `Confluence`'s `_compute_directional_signals`). So delta_one's
`depends_on` metadata looks like **stale/decorative documentation, not a live bug** — but I did not check
`multi_timeframe`, `onchain`, or `volatility`'s declared deps the same way; only cross_instrument (confirmed bug, fixed)
and delta_one (confirmed harmless) were actually verified.

## Why it matters

- A registry that claims a dependency but is never enforced is a trap: the NEXT calculator added to one of these 5
  engines with a REAL constructor-injection point (like `composite_sr`) will silently repeat the exact bug this session
  just fixed, because nothing in the orchestrator path consults `depends_on`.
- Conversely, if `multi_timeframe`/`onchain`/`volatility`'s declared deps turn out to be decorative (like delta_one's),
  the dead `resolve_build_order()`/registry code in those 3 engines is unnecessary upkeep surface with no functional
  purpose — a candidate for deletion once confirmed.

## Recommended decision

Audit `multi_timeframe`, `onchain`, and `volatility`'s `schemas/feature_builder_registry.py` depends_on entries the same
way this session checked cross_instrument (found: real bug) and delta_one (found: harmless) — for each declared
dependency, check whether the dependent calculator's `__init__` actually accepts an injectable upstream DataFrame. Any
real gap gets the same fix pattern applied here (reorder + thread the frame through the request/service layer); any
decorative-only registry gets its dead `resolve_build_order()`/`depends_on` scaffolding either wired for real or
deleted, not left as misleading documentation.

## Todos

- [ ] [AUDIT] P3. **Audit multi_timeframe's feature_builder_registry `depends_on` entries** — for each, check whether
      the dependent calculator's `__init__` accepts an upstream-injected DataFrame (like composite_sr did) vs recomputes
      internally (like delta_one's confluence/risk_reward/wedge_quality). Repo: features-service. Done when: every
      declared dep in `features_service/multi_timeframe/schemas/feature_builder_registry.py` is classified
      real-bug-fixed/confirmed-harmless/deleted-dead-code, with evidence per entry.
- [ ] [AUDIT] P3. **Audit onchain's feature_builder_registry `depends_on` entries** — same method as above. Repo:
      features-service. Done when: every declared dep in `features_service/onchain/schemas/feature_builder_registry.py`
      is classified real-bug-fixed/ confirmed-harmless/deleted-dead-code, with evidence per entry.
- [ ] [AUDIT] P3. **Audit volatility's feature_builder_registry `depends_on` entries** — same method as above. Repo:
      features-service. Done when: every declared dep in
      `features_service/volatility/schemas/feature_builder_registry.py` is classified real-bug-fixed/
      confirmed-harmless/deleted-dead-code, with evidence per entry.

## Progress Log

- **na-eligibility-audit 2026-08-01**: RECLASSIFY, `assigned_vm: NA` → `planning` — all 3 remaining todos are
  structurally identical, mechanical grep-and-read audits (inspect a dependent calculator's `__init__` for an injectable
  upstream DataFrame param) with a stated per-entry done-when, and the exact method was already demonstrated twice in
  this same doc by a single agent in one session (cross_instrument: real bug found + fixed; delta_one: confirmed
  harmless) — no design call, no redirect banner, no `depends_on` gate, doc created today so no prior-revert history.
  Conflict-check run against features_and_ml_master (zero currently-active `assigned_vm: planning` docs in this epic)
  and the cross-cutting consolidated closeout (zero mentions of feature_builder_registry) — cleared. Added
  `assigned_role: backend_engineer` (was missing). `doc_type: issue` — exempt from the finalize-plan-coverage rule, no
  companion finalize doc authored.
