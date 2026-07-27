---
doc_type: issue
title:
  Does an equivalent distinct-values census exist for the strategy catalogue, features catalogue, fixtures catalogue,
  and UAC registries beyond the 4 axes _distinct_values.py/_axis_census.py already cover?
summary:
  Written-inventory ask (no code changes) from `data_pipeline_e2e_milestones_gate_2026_07_24.md` §2 — the manifest's
  distinct-values census (venues/instrument_types/data_types/chains) is well-established, but it's unclear whether an
  analogous drift-detection census exists for other catalogues (strategy registry, features-service's per-family
  registries, sports fixtures catalogue) or UAC registries beyond those 4 axes.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api, strategy-service, features-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [census, distinct-values, catalogue, drift-detection, inventory]
related:
  [
    /plans/active/distinct_values_noncanonical_audit_2026_07_20.md,
    /codex/02-data/reconciliation-census-and-compute-tiers.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §2
depends_on: []
---

# Census equivalents beyond the 4 manifest axes

## Todos

- [x] ✅ [REVIEW] P2. Written inventory (no code changes): for each of the strategy catalogue (strategy-service
      registry), the features catalogue (features-service's per-family declarative registries), the sports fixtures
      catalogue, and any UAC registry not already covered by `_distinct_values.py`/`_axis_census.py`'s 4 axes
      (venues/instrument_types/data_types/chains) — determine whether an equivalent drift-detection census (comparing
      live registered values against a canonical set) exists today. — DONE 2026-07-26 (read-only, no code changes).

      **Baseline** (`deployment-api`): `routes/data_status/_axis_census.py::get_axis_value_census` — raw distinct-value +
                          row-count census over manifest columns `venue`/`chain`/`instrument_type`/`data_type`/`source`/`pipeline_mode`/
                          `timeframe`. `routes/data_status/_distinct_values.py::get_distinct_values`/`enumerate_distinct_values` —
                          per-asset_group raw distinct `venues`/`instrument_types`/`data_types`/`chains` from the honest-coverage rollup,
                          each badged `is_canonical` against UAC's `VENUES_BY_ASSET_GROUP`/`DATA_TYPES_BY_ASSET_GROUP`/`InstrumentType`/
                          `MAINNET_CHAIN_IDS` (with an accepted-exceptions carve-out). Both cover only the 4 manifest axes.

                          1. **Strategy catalogue — YES.** `strategy-service/strategy_service/api/registry_router.py` (route
                             `GET /api/v1/registry/archetypes`, module docstring: "Phase 7 — Admin registry read endpoints for
                             catalogue-truthiness reconciliation") iterates the UAC canonical `StrategyArchetype` enum and cross-checks each
                             against the runtime `StrategyInstanceRegistry` (`engine/strategies/v2/active_registry.py::get_active_strategy_instance_registry`),
                             badging each archetype `LIVE` vs `PLANNED_NOT_IMPLEMENTED` — the same canonical-list-vs-live-registration shape
                             as the manifest axis census.
                          2. **Features catalogue — NO.** Each of the ~9 family modules (`cross_instrument`, `calendar`, `sports`/`tracking`,
                             `multi_timeframe`, `volatility`, `onchain`, `delta_one`, `cefi`, `performance_features`) has its own
                             `BuilderEntry`/`FeatureSpec` declarative registry (e.g.
                             `features-service/features_service/cross_instrument/schemas/feature_builder_registry.py::BUILDER_REGISTRY`,
                             `.../delta_one/app/features/registry.py::build_full_registry`), but no cross-family census exists comparing
                             registered features against a canonical expected-feature manifest. The only drift-shaped mechanism found —
                             `delta_one/app/features/status_report.py --check-drift` (backed by `formula_hash.py::compute_formula_hash`) —
                             checks FORMULA-hash drift (has a calculator's implementation silently diverged from its recorded hash), not
                             registration-vs-canonical drift. **Gap filed as a new todo below.**
                          3. **Sports fixtures catalogue — YES.** `instruments-service/instruments_service/sports/fixture_completeness.py::validate_fixture_completeness`
                             validates captured fixture rows for a `(league_id, season_year)` against UAC's
                             `unified_api_contracts.canonical.domain.sports.season_structure::get_season_structure`, emitting a
                             `CompletenessReport` with 5 typed `FixtureDefect` kinds (`MISSING_FIXTURES`, `TEAM_COUNT_MISMATCH`,
                             `UNEXPECTED_GAP`, `SEASON_WINDOW_DRIFT`, `RESCHEDULE_STALE_TIME`) — a genuine drift/completeness detector.
                          4. **UAC registries beyond the 4 axes — NO (every registry checked).** ~130+ registries exist under
                             `unified_api_contracts/registry/` and `.../canonical/` (`VENUE_TO_ADAPTER_KEY` via `venue_adapter_keys.py`,
                             `MVP_SCOPE`/`mvp_scope.py`, `capability.py`/`capability_data.py`, `venue_manifest/*`, `defi_venues.py`,
                             `tradfi_instrument_universe.py`, `sports/league_registry.py`, etc.) with zero drift-detection surface found
                             (only one docstring hit referencing "Axis Value Census" by name in `market_data_categories.py:308`, no
                             implementation). A registered-but-unadapted venue, an adapter key with no matching capability declaration, or
                             an MVP-scope entry with no live producer would go undetected today. **Gap filed as a new todo below.**

- [ ] [DATA] P3. Build a features-catalogue drift census: enumerate each family's actually-registered
      `BuilderEntry`/`FeatureSpec` set (cross_instrument, calendar, sports/tracking, multi_timeframe, volatility,
      onchain, delta_one, cefi, performance_features) and flag entries missing from / extra vs. a canonical
      expected-feature manifest, mirroring `_axis_census.py`'s shape (repo: features-service). Source: this doc's
      finding 2 (audited 2026-07-26).
- [ ] [DATA] P3. Build a UAC-registry drift census covering `VENUE_TO_ADAPTER_KEY`, `MVP_SCOPE`, capability-declaration
      registries, and per-asset-group venue-manifest tables: flag a registered-but-unadapted venue, an adapter key with
      no matching capability declaration, or an MVP-scope entry with no live producer (repo: unified-api-contracts, or a
      deployment-api admin route reading it). Source: this doc's finding 4 (audited 2026-07-26).
