---
doc_type: issue
title:
  Code-read whether the paper/live strategy universe resolver actually restricts itself to UAC's MVP_SCOPE canonical
  definition
summary: >-
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §14 found none of the 5 asset-group plans' own "MVP universe"
  sections state which MVP cells have actually been proven wired through backfill=paper=live, vs. just declared
  in-scope. A precondition for answering that per-AG question is confirming, by direct code read (not assumption), that
  the paper/live strategy universe resolver genuinely restricts itself to UAC's `MVP_SCOPE` canonical definition in the
  first place.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [mvp-scope, strategy-universe, paper-live, batch-live-paper, code-read]
related:
  [
    /codex/02-data/mvp-scope-canonical.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: correct-codex
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §14
depends_on: []
---

# MVP_SCOPE resolver code-read

## Todos

- [x] ✅ [BACKEND] P1. Code-read (not assumption) whether strategy-service's paper/live strategy universe resolver
      actually restricts its instrument/venue universe to UAC's `MVP_SCOPE` canonical definition, or whether it silently
      includes non-MVP cells. — DONE 2026-07-26.

      **Verdict: REFUTED.** strategy-service's paper/live strategy universe resolver does NOT restrict its
                          instrument/venue universe to UAC's `MVP_SCOPE`. `grep -rn "MVP_SCOPE\|is_mvp" strategy-service --include="*.py"`
                          (excluding tests) returns **zero hits**; a repo-wide grep confirms every `is_mvp(...)` consumer in the workspace
                          is `market-data-processing-service`, `market-tick-data-service`, `instruments-service`, `deployment-api`, or UAC
                          itself — strategy-service never appears in that list.

                          **MVP_SCOPE definition (UAC)**: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py:353`
                          — `MVP_SCOPE: Final[dict[str, object]]`, keyed by `asset_group` → typed rule dataclass (`CeFiMvpRule`,
                          `DeFiMvpRule`, `TradFiMvpRule`, `SportsMvpRule`, `PredictionMvpRule`). SSOT predicate:
                          `_mvp_scope_predicate.py::is_mvp(asset_group, venue, instrument_type, data_type, base_ccy=None)` (re-exported via
                          `mvp_scope.py:67`) — "a cell is MVP iff its `(venue, instrument_type)` pair is declared in the rule for its
                          asset_group AND every other declared axis matches" (`mvp_scope.py:17-19`).

                          **Actual resolver path**: `strategy_service/engine/strategies/v2/target_universe/catalog.py` (facade) → per-family
                          builders (`catalog_carry.py`, `catalog_staked_basis.py`, `catalog_yield_defi.py`, `catalog_trading.py`,
                          `catalog_directional.py`), each emitting hardcoded `TargetInstanceSpec` tuples (literal venue/coin/instrument-type
                          combinations) into `TARGET_UNIVERSE`. Loaded via
                          `target_universe/loader.py:51 load_target_universe_into_registries()` and
                          `:77 load_combined_instance_catalog()` — neither filters against `MVP_SCOPE`; they register every catalog-declared
                          spec plus legacy migration specs. The only narrowing filters that exist are: (a) a whole-archetype
                          `PaperUniverseConfig.archetypes` field — unwired (`service_entry.py` never passes `universe_config`, so
                          production always runs the full default universe); (b) per-archetype data-satisfiability gates in
                          `paper_universe.py` (honest-skip when real GCS data is absent); (c) portfolio-allocator economic thresholds
                          (`min_apy_bps`, `top_n`) in `guard_rails.py`/`archetypes_rank.py`. None check `MVP_SCOPE` cell membership — they
                          check data availability and economics, not canonical scope.

                          **Independent corroboration**: already documented at
                          `plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` — "no venue/currency
                          curtailment mechanism exists in production" (Finding 1), plus an already-diverged registry (Finding 3:
                          strategy-service's catalog vs UAC's `archetype_leg_spec_seeds.py` have silently diverged on eligible venues —
                          `aster`/`kalshi-perp`/`polymarket-perp` live in production but absent from UAC's hand-curated set).

                          **Gap filed as a new todo below.**

- [ ] [BACKEND] P2. Add an `is_mvp(asset_group, venue, instrument_type, data_type, base_ccy=...)` filter step inside/
      after `strategy_service/engine/strategies/v2/target_universe/catalog.py`'s `specs_for_archetype()` (or in
      `loader.py`'s `load_target_universe_into_registries()`/`load_combined_instance_catalog()`) that drops any
      catalog-declared spec whose cell is not MVP per UAC's canonical `MVP_SCOPE`, closing the gap where the
      MVP-restriction is currently aspirational (implicit in "the catalog only lists what we intended to run") rather
      than enforced. Cross-reference `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` before
      implementing — that doc already tracks the related curtailment-mechanism gap and may be the better home for the
      actual fix. Source: this doc's audit finding (audited 2026-07-26).
