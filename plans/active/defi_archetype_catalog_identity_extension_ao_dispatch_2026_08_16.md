---
doc_type: plan
title: Extend canonical instrument_type/asset_group identity to all ~26-29 DeFi strategy-archetype catalog rows
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 7) on
  defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md's open scope/sequencing question: extend to ALL
  ~26-29 archetypes now, not just the already-`_ENGINE_DRIVABLE_ARCHETYPES` subset (7-19 of them). Per-archetype
  catalog builders (CARRY/YIELD/ARBITRAGE/DIRECTIONAL) currently have NO stored `instrument_type`/`asset_group`
  identity in `initial_config` — it's implicit in engine `on_tick()` logic only. `asset_group` must be derived
  per-VENUE (some archetypes mix CeFi+DeFi venues in one archetype) via a UAC venue→asset_group classifier composed
  from `unified_api_contracts.registry.defi_venues.ALL_DEFI_VENUES` + CeFi/TradFi venue sets — no such single
  ready function exists yet. Do NOT guess values — a wrong guess silently mis-filters the live/paper production
  strategy universe.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [strategy-service, unified-api-contracts]
scope: [engineer]
tags: [defi, canonicalization, instrument_type, asset_group, strategy-catalog]
related:
  [
    /plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 7, 2026-08-16 — operator ruling: extend to all ~26-29 rows"
locked_by:
context_scope:
  [
    /plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py,
    strategy-service/strategy_service/cli/handlers/paper_universe.py,
    unified-api-contracts/unified_api_contracts/registry/defi_venues.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_predicate.py,
  ]
locked_since:
resolved_by:
---

# Extend canonical instrument_type/asset_group identity to all DeFi archetype catalog rows

## Todos

- [ ] [BACKEND] P2. **RULED 2026-08-16 (operator): build for all ~26-29 archetypes now, not just the
      `_ENGINE_DRIVABLE_ARCHETYPES` subset.** (1) Build a UAC venue→asset_group classifier composed from
      `unified_api_contracts.registry.defi_venues.ALL_DEFI_VENUES` + the existing CeFi/TradFi venue sets (no such
      single ready function exists today) — needed because some archetypes (e.g. `CARRY_BASIS_PERP`) mix CeFi and
      DeFi venues in the same archetype, so `asset_group` must be derived per-venue, not per-archetype. (2) Extend
      every CARRY/YIELD/ARBITRAGE/DIRECTIONAL catalog builder's `initial_config` with a canonical
      `instrument_type` (UAC enum: `SPOT_PAIR`/`PERPETUAL`/`OPTION`, not the 3 existing non-canonical lowercase
      values) and derived `asset_group` identity per row — mirrors how `_VENUE_IDENTITY_KEYS`/
      `_CURRENCY_IDENTITY_KEYS` already reconcile each archetype's own literal config-key names for the
      venue/currency axes. Do NOT guess any value — verify against real engine behavior per archetype the same way
      Finding 1's venue-containment check was built. (3) Once identity exists, wire the real `is_mvp()`-backed
      curtailment reason (`not_mvp_scope`) into `_resolve_drivable()`, alongside the existing
      `curtailed_by_operator_constraint`. Repos: strategy-service, unified-api-contracts.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 7, operator ruling)**: extracted from
  `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`'s "NEW finding 2026-07-28" todo; operator chose
  the full-scope option (all ~26-29 rows) over starting with the smaller already-drivable subset.
