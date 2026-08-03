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

- [x] [AUDIT] P3. **Audit multi_timeframe's feature_builder_registry `depends_on` entries** — for each, check whether
      the dependent calculator's `__init__` accepts an upstream-injected DataFrame (like composite_sr did) vs recomputes
      internally (like delta_one's confluence/risk_reward/wedge_quality). Repo: features-service. Done when: every
      declared dep in `features_service/multi_timeframe/schemas/feature_builder_registry.py` is classified
      real-bug-fixed/confirmed-harmless/deleted-dead-code, with evidence per entry. ✅ — audited, see Progress Log
      2026-08-03 entry (only 1 of 9 registry entries declares a non-empty `depends_on`; classified CONFIRMED-HARMLESS).
- [x] ✅ [AUDIT] P3. **Audit onchain's feature_builder_registry `depends_on` entries** — same method as above. Repo:
      features-service. Done when: every declared dep in `features_service/onchain/schemas/feature_builder_registry.py`
      is classified real-bug-fixed/ confirmed-harmless/deleted-dead-code, with evidence per entry. ✅ — audited, see
      Progress Log 2026-08-03 (onchain) entry (2 of 16 registry entries declare non-empty `depends_on`:
      `aave_rate_impact` CONFIRMED-HARMLESS, `onchain_regime` a genuine unwired-feature-group GAP — new follow-up todo
      added below).
- [ ] [AUDIT] P3. **Audit volatility's feature_builder_registry `depends_on` entries** — same method as above. Repo:
      features-service. Done when: every declared dep in
      `features_service/volatility/schemas/feature_builder_registry.py` is classified real-bug-fixed/
      confirmed-harmless/deleted-dead-code, with evidence per entry.
- [ ] [BACKEND] P1. **New, opened by the onchain audit above.** Wire (or delete) the fully-unwired `onchain_regime`
      feature group in features-service's onchain engine. `compute_onchain_regime_features()`
      (`features_service/onchain/app/calculators/onchain_regime_calculator.py`) is never registered via
      `@FeatureCalculatorRegistry.register`, never appears in `OnChainOrchestrationService._dispatch_feature_group`'s
      feature-group elif chain (`features_service/onchain/engine/orchestrator.py`), and is exercised only by
      `tests/onchain/unit/test_feature_touchup.py` — yet `features_service/onchain/schemas/feature_definitions.yaml`'s
      `regime:` block declares 10 real, fully-specified features (`tvl_regime_bucket`, `utilization_regime_bucket`,
      `health_factor_bucket`, `yield_z_score`, etc.), several `priority: P0`, explicitly consumed by
      `models: [LENDING, RISK, ALL]` per the calculator module's own docstring ("consumed by strategy-service to adapt
      position sizing and risk thresholds"). This is the SAME class of gap as this doc's original `composite_sr` finding
      (a real, designed feature silently never computed) — not the decorative-`depends_on`-only pattern found for
      `aave_rate_impact`/delta_one/multi_timeframe's `tf_risk_reward`. Done when: `onchain_regime` is either (a)
      registered + dispatched like every other onchain feature group, with its 3 declared upstream deps
      (`aave_utilization`, `defillama_tvl`, `aave_lending_rates`) threaded into the `df`
      `compute_onchain_regime_features` expects, and covered by an integration-level test proving it runs end-to-end via
      `OnChainOrchestrationService.process_feature_group("onchain_regime", ...)`; or (b) if the operator rules the
      feature group is no longer wanted, deleted (calculator file, registry entry, yaml block, tests) rather than left
      as misleading unwired documentation. (repo: features-service) — scoped out of THIS audit todo (classification
      only, not a fix) given the larger surface (orchestrator wiring + upstream DataFrame threading + tests), mirroring
      how `composite_sr`'s fix was its own separate unit of work.

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

- **2026-08-03 (multi_timeframe audit, slot 8)**: Read
  `features_service/multi_timeframe/schemas/feature_builder_registry.py`'s `_metadata` table (9 registry entries: the 6
  Phase-0 cross-TF/regime calcs + `wedge_confluence`, `tf_risk_reward`, `tf_confluence_signals`). Only **one** entry
  declares a non-empty `depends_on`: `tf_risk_reward` → `["wedge_confluence"]` — every other entry's `depends_on` is
  `[]`. Classification of that one declared dep: **CONFIRMED-HARMLESS** (decorative, same pattern as delta_one, not a
  live bug like cross_instrument's `composite_sr`). Evidence:
  - `TfRiskRewardCalculator.__init__` (`features_service/multi_timeframe/calculators/tf_risk_reward.py:82-89`) takes
    only `timeframes`/`timeframe`/`mode` — no injectable upstream-DataFrame param. Same for
    `WedgeConfluenceCalculator.__init__` (`wedge_confluence.py:140-147`), and the shared
    `BaseFeatureCalculator.__init__` (`base_calculator.py:45-49`) caps every MTF calculator to `timeframe`/`mode` —
    there is no constructor-injection point anywhere in this engine's calculator hierarchy (unlike cross_instrument's
    `composite_sr`, which genuinely had one that went unwired).
  - `TfRiskRewardCalculator._calculate_features` reads `poly_medium_resistance_value_{tf}`,
    `poly_medium_support_value_{tf}`, `atr_14_{tf}` directly off the shared input `df` (the MTF join-layer frame) — it
    never references any of `wedge_confluence`'s actual OUTPUT columns (`wedge_confluence_score`,
    `wedge_confluence_{lo}_{hi}`, `wedge_convergence_alignment`, `wedge_min_bars_to_convergence`); confirmed via
    `rg -n "wedge_confluence" tf_risk_reward.py` → zero hits. Both calculators independently read raw poly/ATR columns
    off the same pre-joined frame; there is no producer→consumer data relationship between them despite the declared
    `depends_on` edge.
  - `features_service/multi_timeframe/engine/orchestrator.py` sequences calculators via a flat
    `self.config.enabled_feature_groups` list (line ~590, `for group_name in self.config.enabled_feature_groups`) —
    `resolve_build_order()`/`get_all_builders()` are imported by `schemas/__init__.py` and re-exported but never
    actually called by the orchestrator, batch handler, or service (`rg -n "resolve_build_order"` outside the schema
    module itself → 0 call sites), matching the doc's original cross-engine finding.
  - Repo: features-service (no code change — audit-only todo, done_definition is classification with evidence, not
    deletion; leaving the registry file as-is mirrors how delta_one's confirmed-harmless finding was left in this same
    doc, not deleted). Checkbox flipped above.

- **2026-08-03 (onchain audit, slot 11)**: Read `features_service/onchain/schemas/feature_builder_registry.py`'s
  `_metadata` table (15 entries) + the manually-appended `onchain_regime` `BuilderEntry` (16 total). **Two** entries
  declare a non-empty `depends_on`:
  - **`aave_rate_impact`** → `["aave_lending_rates", "aave_utilization"]`. Classification: **CONFIRMED-HARMLESS**
    (decorative, same pattern as delta_one/multi_timeframe's `tf_risk_reward`). Evidence:
    `AaveRateImpactCalculator.__init__` (`aave_rate_impact_calculator.py:147-160`) takes only `our_position_usd`/
    `synthetic_delay_us` — no injectable upstream-DataFrame param; its `fetch_data()` does its OWN async fetch
    (DefiLlama Yields API + MTDS `lending_indices` directly), never reading either declared dependency's output. The
    calculator IS live in production — dispatched as feature_group `"rate_impact"` via
    `OnChainOrchestrationService._dispatch_feature_group` (`orchestrator.py:148-150`) — so this is a real-but-decorative
    `depends_on` edge on an otherwise-wired calculator, not dead code.
  - **`onchain_regime`** → `["aave_utilization", "defillama_tvl", "aave_lending_rates"]`. Classification: **GAP —
    genuine unwired feature group**, a materially different (and more severe) finding than every other entry audited in
    this doc so far. `compute_onchain_regime_features(df)` (`onchain_regime_calculator.py:107`) is a plain function,
    never decorated with `@FeatureCalculatorRegistry.register` (confirmed:
    `rg -n "register.*onchain_regime\|class.*Regime" onchain_regime_calculator.py` → 0 hits), never appears in
    `_dispatch_feature_group`'s feature-group elif chain (13 groups enumerated: macro_sentiment/lending_rates/
    lst_yields/onchain_perps/utilization/rewards/risk_params/flash_loan_availability/health_factor/
    liquidation_events/rate_impact/perp_funding_rates/lst_native_rates — `onchain_regime` absent), and its only caller
    anywhere in the repo is `tests/onchain/unit/test_feature_touchup.py` (confirmed via
    `rg -rn "compute_onchain_regime_features" .` across the whole repo — zero production call sites,
    `rg -rln "regime" features_service/onchain/ --include="*.py" | grep -v tests` → only the calculator file + its
    `__init__.py` re-export + the registry file itself). This is NOT a decorative `depends_on` edge like
    `aave_rate_impact` — the ENTIRE feature group is dead in production, despite
    `features_service/onchain/schemas/feature_definitions.yaml`'s `regime:` block declaring 10 fully-specified real
    features (`tvl_regime_bucket`, `utilization_regime_bucket`, `health_factor_bucket`, `chain_congestion_flag`,
    `oracle_deviation_flag`, `yield_z_score`, `yield_protocol_pct`, etc.), several `priority: P0`, consumed by
    `models: [LENDING, RISK, ALL]` — and the calculator module's own docstring says "These features are consumed by
    strategy-service to adapt position sizing and risk thresholds to current on-chain conditions." Same failure class as
    this doc's original `composite_sr` finding (a real, designed feature silently never computed) — scoped as its own
    follow-up todo below rather than fixed inline here, since wiring it correctly (register + dispatch + thread the 3
    upstream DataFrames + add an integration test) is a materially larger unit of work than this audit todo's
    classification-only done_definition.
  - Repo: features-service (no code change in THIS todo — audit-only, classification with evidence; the new gap gets a
    separate tracked `[BACKEND] P1` todo per CLAUDE.md's "every follow-up is a tracked todo, never prose" rule).
    Checkbox flipped above.
