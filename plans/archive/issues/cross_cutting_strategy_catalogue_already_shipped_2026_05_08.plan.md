---
title:
  "✅ RESOLVED 2026-05-09 — Option A migration shipped (was: parallel SSOTs in cross_cutting_may_23_deliverables Items
  #1 + #2)"
created: 2026-05-08
resolved: 2026-05-09
author: uac-strategy-catalogue-ids-tab6a
status: resolved
source:
  - plans/active/cross_cutting_may_23_deliverables_2026_05_08.md (deliverables #1 + #2)
  - plans/epics/cross_cutting_may_23_2026.epic.md (epic deliverables #1 + #2)
  - unified-api-contracts/unified_api_contracts/strategy.py (existing 207-line root facade)
  - unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py (StrategyFamily — 9 members,
    StrategyArchetype — 46 members, ARCHETYPE_TO_FAMILY)
  - unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_naming.py (parse_strategy_id +
    format_strategy_id, commit 5083d65)
  - unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability.py
    (ARCHETYPE_CAPABILITY_REGISTRY + ArchetypeCapability + ArchetypeCapabilityCell + ArchetypeInstrumentType +
    CoverageStatus + RollMode)
  - unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/registry.py (STRATEGY_REGISTRY +
    StrategyDefinition + StrategyRegistry + Category + ExecutionMode)
  - unified-api-contracts/unified_api_contracts/_instrument_enums.py (InstrumentType — 24 members)
  - unified-api-contracts/unified_api_contracts/internal/architecture_v2/capital_allocation.py (NEW; CapitalAllocation
    migrated)
locked_by: live-defi-rollout
locked_since: 2026-05-08
operator_decision: option_a_extend_v2
operator_decision_date: 2026-05-08
---

## ✅ RESOLUTION 2026-05-09

Per cluster 9 retry audit 2026-05-09: Option A migration verified shipped on origin. Parallel `canonical/domain/client/`
greenfield package reverted; `CapitalAllocation` + `AllocationViolationError` + `validate_allocation_respect` +
`is_within_allocation` + `CAPITAL_ALLOCATION_SEED` migrated into `internal/architecture_v2/capital_allocation.py`
sibling to `client_registry.py`. Tests migrated. `client.py` root facade re-exports from architecture_v2 path.

Issue P0 BLOCKER status no longer applies; Option A shipped per operator decision. Issue ready for archive.

---

# Original issue (resolved — kept for archaeology)

# cross_cutting_may_23_deliverables Items #1 + #2 are already shipped under UAC architecture_v2 — plan body redesigns parallel SSOTs

> **✅ OPERATOR DECISION 2026-05-08 — OPTION A APPROVED.** Extend existing UAC `internal/architecture_v2/` +
> `internal/domain/strategy_service/` SSOTs; re-export through existing `strategy.py` facade. Reverse the parallel
> `canonical/domain/client/` greenfield package shipped in `uac@3591037` (delete `canonical/domain/client/__init__.py`
>
> - `model.py` + root `client.py` facade); migrate `CapitalAllocation` + `AllocationViolationError` +
>   `validate_allocation_respect` + `is_within_allocation` + `CAPITAL_ALLOCATION_SEED` into
>   `internal/architecture_v2/capital_allocation.py` (sibling to `client_registry.py`); re-export through `strategy.py`.
>   Migrate `tests/unit/test_client_model.py` → `tests/unit/test_capital_allocation.py` (CapitalAllocation tests stand;
>   `Client` + `VenueAccount` test cases deleted). NEW P0 todo to seed `ArchetypeConfig` in
>   `internal/architecture_v2/archetype_config.py` for May-23 live archetypes (CARRY_STAKED_BASIS Solana + Ethereum;
>   CARRY_BASIS_PERP × 6 perp venues; ML_DIRECTIONAL_CONTINUOUS for OKX + Binance + Bybit) with
>   `{collateral, hedge_ratio, position_cap_usd, kill_switch_drawdown_pct, kill_switch_position_breach_pct}` fields.
>   Update codex `strategy-summary.md` 8-family / 18-archetype baseline → 9-family / 46-archetype shape per current
>   registry. Tab 6.A is **UNBLOCKED** under Option A scope. See `plans/active/operator_decisions_2026_05_08.md` §
>   "Detail — strategy catalogue Option A migration sequencing" for the 7-step pickup recipe.

> **Severity**: P0 — Sub-agent (Tab 6.A) was assigned to ship UAC SSOTs that already exist in a more complete shape, and
> the plan-of-record specifies dataclass + helper names that would create duplicate (and contradictory) SSOTs in the
> same repo. Implementing as written violates "Single Source of Truth" + "System-First Architecture" workspace rules.
>
> **Blast radius**: UAC repo (would create `canonical/domain/strategy/{catalogue,ids}.py` parallel to
> `internal/architecture_v2/{enums,strategy_naming}.py` + `internal/domain/strategy_service/registry.py`); Tab 6
> work-split (Ikenna + Harsh both have items consuming Tab 6.A's output); cross_cutting epic (deliverables #1 + #2 are 2
> of 5 non-negotiable May-23 items, framing depends on whether plan body or existing SSOTs are canonical).
>
> **Suggested owner**: operator triage (Ikenna) — needs an architectural call about whether the plan-of-record gets
> rewritten to consume existing v2 SSOTs OR existing v2 SSOTs get migrated/extended to match the plan-body shape.

## What I found

The cross_cutting plan-of-record (`plans/active/cross_cutting_may_23_deliverables_2026_05_08.md`) names the following
items as DESIGN+UAC work for Tab 6.A:

- **#1 Catalogue UAC schema** — "archetype × venue × instrument-type matrix shape; per-archetype config schema
  (collateral, hedge ratios, position caps, kill-switch thresholds)"
- **#2 Strategy ID UAC schema** — "canonical naming convention + versioning + (archetype, venue, instrument-type,
  client) → ID derivation function"

The Tab 6.A spawn prompt expanded these into concrete deliverables: `StrategyFamily` (8-member), `StrategyArchetype`
(18-member), `InstrumentType`, `LiveVsBacktest`, `ArchetypeConfig`, `CatalogueRow`, `STRATEGY_CATALOGUE_SEED`,
`StrategyId` dataclass, `format_strategy_id` returning `<archetype>.<venue>.<instrument_type>.v<N>`,
`STRATEGY_ID_REGISTRY`, `is_archetype_live`, `filter_catalogue`, `derive_strategy_id`, `is_strategy_id_known` — landed
under `unified_api_contracts/canonical/domain/strategy/` + a new root facade `unified_api_contracts/strategy.py`.

**Every one of those symbols already exists in UAC under `internal/architecture_v2/` +
`internal/domain/strategy_service/`, and a 207-line `unified_api_contracts/strategy.py` root facade is already in
place.** The existing shape is RICHER and more complete than the plan-body design:

| Plan-body deliverable                                                                             | Already-shipped equivalent                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Delta                                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `StrategyFamily` (8-member StrEnum, lowercase values)                                             | `unified_api_contracts.internal.architecture_v2.enums.StrategyFamily` — **9 members, UPPERCASE** (`ML_DIRECTIONAL` / `RULES_DIRECTIONAL` / `CARRY_AND_YIELD` / `ARBITRAGE_STRUCTURAL` / `MARKET_MAKING` / `EVENT_DRIVEN` / `VOL_TRADING` / `STAT_ARB_PAIRS` / `PORTFOLIO`)                                                                                                                                                                                                                                                      | Existing surface has **PORTFOLIO** that the plan-body 8-list omits, and uses UPPERCASE values to match slot-label grammar. The codex `strategy-summary.md` family count of 8 is OUT-OF-DATE relative to the v2 enum (PORTFOLIO added 2026-04-25 per phase 9 of the dart_ui_strategy_filtering_and_onboarding plan). |
| `StrategyArchetype` (18 archetypes per architecture-v2/archetypes/ ls)                            | Same enum module — **46 archetypes** with `ARCHETYPE_TO_FAMILY` dict — covers every archetype in the v2 codex including the 18 listed in `architecture-v2/archetypes/` PLUS 28 more (VOL family expanded 1→18, MM family expanded 2→9, PORTFOLIO 4 added, MEV 4 added, etc.).                                                                                                                                                                                                                                                   | Plan body asks for "full 18-archetype enumeration"; v2 already at 46. Picking 18 is a regression.                                                                                                                                                                                                                   |
| `InstrumentType` StrEnum (SPOT/PERP/OPTION/etc.)                                                  | `unified_api_contracts._instrument_enums.InstrumentType` (24 UPPERCASE members SPOT_PAIR / PERPETUAL / FUTURE / OPTION / POOL / LENDING / LST / YIELD_BEARING / A_TOKEN / DEBT_TOKEN / STAKING / SPOT_ASSET / ETF / EQUITY / COMMODITY / CURRENCY / INDEX / BOND / CDS / EVENT_CONTRACT / COMBO / PREDICTION_MARKET / EXCHANGE_ODDS / FIXED_ODDS / PROP) AND `archetype_capability.ArchetypeInstrumentType` (8 narrower archetype-scoped members spot / perp / dated_future / option / lending / staking / lp / event_settled). | Two SSOTs, intentionally different. The capability matrix uses the narrower one.                                                                                                                                                                                                                                    |
| `LiveVsBacktest` StrEnum                                                                          | `archetype_capability.CoverageStatus` (`SUPPORTED` / `PARTIAL` / `BLOCKED`) — per-cell, not per-row tag. Live vs research distinction handled via `RestrictionProfile` + `Phase` + `Env` enums in `internal/architecture_v2/restriction_profiles.py`.                                                                                                                                                                                                                                                                           | Different model — coverage isn't a per-row tag, it's a per-(archetype, asset_group, instrument_type) cell.                                                                                                                                                                                                          |
| `ArchetypeConfig` frozen dataclass (collateral / hedge*ratio / position_cap_usd / kill_switch*\*) | Not present at this exact name. Per-archetype operational config is split across `archetype_capability.ArchetypeCapabilityCell` (status / venue_ids / signal_variants / roll_mode / block_list_refs / representative_slot_labels / notes), per-archetype derivation logic in `architecture_v2/derivation*.py`, and runtime config in `strategy_service`'s repo.                                                                                                                                                                 | **This is the one genuine gap.** Operational risk knobs (position_cap_usd / kill_switch_drawdown_pct / kill_switch_position_breach_pct) are NOT centralised in UAC under a single `ArchetypeConfig` dataclass — they live in strategy-service runtime config + risk-and-exposure-service.                           |
| `CatalogueRow` frozen dataclass                                                                   | `internal.domain.strategy_service.registry.StrategyDefinition` (strategy_id / name / family / asset_group / archetype / coverage_status).                                                                                                                                                                                                                                                                                                                                                                                       | Existing shape is row-level; the plan-body asks for richer per-row config.                                                                                                                                                                                                                                          |
| `STRATEGY_CATALOGUE_SEED: tuple[CatalogueRow, ...]`                                               | `STRATEGY_REGISTRY` populated from `ARCHETYPE_CAPABILITY_REGISTRY` × per-cell `representative_slot_labels` — derived at module import time, not a static seed tuple, but the same data.                                                                                                                                                                                                                                                                                                                                         | Different shape (registry vs static tuple) but same role.                                                                                                                                                                                                                                                           |
| `get_archetype_family(archetype)` helper                                                          | `ARCHETYPE_TO_FAMILY[archetype]` dict + `StrategyRegistry.resolve_family(strategy_id)`                                                                                                                                                                                                                                                                                                                                                                                                                                          | Equivalent.                                                                                                                                                                                                                                                                                                         |
| `is_archetype_live(archetype)` helper                                                             | `StrategyRegistry.get_by_archetype(archetype)` returning rows whose cells have non-BLOCKED coverage_status                                                                                                                                                                                                                                                                                                                                                                                                                      | Equivalent.                                                                                                                                                                                                                                                                                                         |
| `filter_catalogue(asset_group, archetype, venue, live_only)` helper                               | `StrategyRegistry.get_by_family / get_by_asset_group / get_by_archetype` + `archetypes_for_pair` + `archetypes_for_venue` + `capability_for` (all in archetype_capability module + strategy.py facade)                                                                                                                                                                                                                                                                                                                          | Multiple slice helpers, more granular than a single 4-arg `filter_catalogue`.                                                                                                                                                                                                                                       |
| `StrategyId` dataclass + `__str__` returning `<archetype>.<venue>.<instrument_type>.v<N>`         | `internal.architecture_v2.strategy_naming.ParsedStrategyId` (frozen dataclass: family / archetype / slot_id / source_form) + `parse_strategy_id(fq_id)` + `format_strategy_id(archetype, slot_id, fully_qualified=True)` returning `FAMILY.ARCHETYPE.slot_id` (or `ARCHETYPE@slot_id` slot-label form). Slot grammar: `archetype@venue-asset-instrument-period-quote-env`.                                                                                                                                                      | **Different + richer grammar.** Existing slot grammar (6-axis) carries period + quote + env; plan-body proposes 4-axis (archetype.venue.instrument_type.v<N>) which is a regression — drops period / quote / env / version-as-config.                                                                               |
| `derive_strategy_id(row, version=1)` helper                                                       | `format_strategy_id(archetype, slot_id, fully_qualified=True)` — shipped in commit 5083d65 ("feat(strategy): add parse_strategy_id + format_strategy_id canonical naming helpers")                                                                                                                                                                                                                                                                                                                                              | Equivalent function-shape, different grammar.                                                                                                                                                                                                                                                                       |
| `STRATEGY_ID_REGISTRY: frozenset[StrategyId]`                                                     | `frozenset(s.strategy_id for s in STRATEGY_REGISTRY.all())` — derivable, not eagerly cached.                                                                                                                                                                                                                                                                                                                                                                                                                                    | Equivalent, derivable.                                                                                                                                                                                                                                                                                              |
| `is_strategy_id_known(sid)` helper                                                                | `STRATEGY_REGISTRY.get(strategy_id) is not None`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Equivalent.                                                                                                                                                                                                                                                                                                         |
| Root facade `unified_api_contracts/strategy.py` re-exporting public API                           | **ALREADY EXISTS** — 207-line facade re-exporting STRATEGY_REGISTRY / StrategyFamily / StrategyArchetype / Category / ExecutionMode / ArchetypeCapability / parse_strategy_id / format_strategy_id / ClientRegistry / RestrictionProfile / ServiceFamily / etc.                                                                                                                                                                                                                                                                 | **Direct collision.** A new `unified_api_contracts/strategy.py` would clobber the existing facade.                                                                                                                                                                                                                  |

The existing v2 architecture-v2 SSOT is the workspace canonical surface — referenced by:

- `unified_trading_library.utils.record_enricher.RecordEnricher` (stamps strategy_name / asset_group / strategy_family
  on exec/pos records)
- `unified_trading_api.routes.trading_analytics` (`/api/trading/strategies/catalog` UI route)
- `unified_trading_pm.scripts.openapi.generate_ui_reference_data` (emits `ui-reference-data.json` for UI pipeline)
- `unified-trading-system-ui/lib/architecture-v2/coverage.ts` (UI matrix kept in sync via
  `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh`)

The plan-of-record's design appears unaware of this surface. If the plan was written intending to extend / refactor the
v2 SSOTs, that intent isn't captured anywhere in the body — every Tab 6.A todo reads as greenfield.

## Why it matters

1. **Single Source of Truth (workspace HARD RULE)** — implementing the plan-body design as written would create parallel
   UAC SSOTs:
   - `canonical/domain/strategy/catalogue.py` (`StrategyFamily` 8-member) AND `internal/architecture_v2/enums.py`
     (`StrategyFamily` 9-member, including PORTFOLIO).
   - `canonical/domain/strategy/ids.py` (`StrategyId` archetype.venue.instrument_type.v<N>) AND
     `internal/architecture_v2/strategy_naming.py` (`ParsedStrategyId` 6-axis slot grammar).
   - `STRATEGY_CATALOGUE_SEED` (static tuple) AND `STRATEGY_REGISTRY` (capability-derived registry).
   - The `strategy.py` facade collision is the worst case — overwriting a 207-line live-consumed surface that downstream
     services + the UI pipeline read from. **Even creating the new facade as `strategy_v2.py` or similar wouldn't fix
     it; downstream consumers would split between two facades and the OpenAPI / UI generation pipeline would break.**

2. **System-First Architecture (workspace HARD RULE) + No Technical Debt (Citadel-Grade Planning Standards § 3)** — the
   rule is "USE the existing system; FIX the library if missing a feature; ADD to the library if a capability is absent.
   Do NOT build a parallel solution." A net-new `canonical/domain/strategy/` greenfield is the ad-hoc parallel-solution
   anti-pattern.

3. **Cross_cutting deliverables #1 + #2 framing is correct, but plan body redesigns wrong layer** — the epic-level
   intent ("Strategy catalogue covering all archetype × venue combinations + Strategy IDs as stable machine-readable
   identifiers") is not in dispute. The execution shape is. The right shape is **extend the existing v2 SSOTs** (e.g.
   add `ArchetypeConfig` for the missing operational risk knobs, add seeding for May-23 live archetypes' venue cells,
   expose any UI/data-status filter helpers that aren't yet on the facade) — NOT redesign parallel UAC modules.

4. **Tab 6.A vs Tab 6.B (Harsh) work-split impact** — Harsh T6 is supposed to consume my UAC output
   (`STRATEGY_CATALOGUE_SEED` → catalogue rows population, `STRATEGY_ID_REGISTRY` → ID refactor sweep, etc.). If Harsh's
   tab consumes my net-new modules while existing v2 surface stays in place, the sweep is doubled / confused. If Harsh's
   tab consumes the existing v2 surface, my modules are dead-on-arrival. Neither outcome is correct. **Tab 6 needs a
   re-spec from the operator before Harsh's tab consumes anything.**

5. **Codex `strategy-summary.md` is stale** — 8-family / 18-archetype baseline (referenced by both the cross_cutting
   epic + the plan-of-record's "See also") doesn't reflect 2026-04-25 PORTFOLIO addition + 2026-04-21 v1→v2 sanitisation
   that produced the 9-family / 46-archetype shape. Codex SSOT drift is a separate find, but it's why the plan body
   designed against the wrong target.

## Recommended decision

Operator-pick (request — needs Ikenna's call):

**Option A (recommended)** — **Rewrite Tab 6.A scope to extend existing v2 SSOTs**:

- Genuine gap to ship as P0: lift operational risk knobs (collateral, hedge_ratio, position_cap_usd,
  kill_switch_drawdown_pct, kill_switch_position_breach_pct) from strategy-service runtime config into a new
  `ArchetypeConfig` frozen dataclass in `unified_api_contracts/internal/architecture_v2/archetype_config.py`, seeded for
  the May-23 live archetypes (CARRY_STAKED_BASIS Solana + Ethereum + CARRY_BASIS_PERP across 6 perp venues +
  ML_DIRECTIONAL_CONTINUOUS for CeFi-ML). Re-export through `strategy.py` facade.
- Verify `STRATEGY_REGISTRY` covers May-23 live archetype rows (audit the `representative_slot_labels` for the 18
  archetype docs in `architecture-v2/archetypes/`); add missing rows.
- Add a `live_archetypes_for_may_23` helper or `is_live_archetype(archetype, asset_group)` slice if absent.
- Update codex `strategy-summary.md` to 9-family / 46-archetype shape and remove drift.
- Skip the parallel `canonical/domain/strategy/` greenfield entirely.

**Option B** — Redesign-and-migrate: deprecate `internal/architecture_v2/` modules + migrate every consumer (UTL
record_enricher, trading-api routes, PM OpenAPI pipeline, UI coverage.ts sync). Citadel-grade clean break, but
multi-week effort across multiple repos and the May-23 deadline already-tight.

**Option C** — Ship the plan-body design verbatim, accept the parallel-SSOT debt, plan a consolidation post-May-23.
**Not recommended** — it's the exact anti-pattern the workspace rules prohibit, and the `strategy.py` facade collision
means the plan can't ship without overwriting downstream-consumed code.

The plan-of-record `## Open questions` already has the question shape "Strategy ID versioning rule: hash-based /
sequential / semver-style?" — but the more fundamental question is "do we extend the existing v2 grammar
(`ARCHETYPE@venue-asset-instrument-period-quote-env` + `FAMILY.ARCHETYPE.slot_id` FQ) or replace it with a new 4-axis
grammar?" The plan body assumes the answer to that is "replace" without surfacing the question.

Until the operator picks Option A / B / C, Tab 6.A is **🟡 BLOCKED** and CANNOT ship code without violating workspace
SSOT rules. The right next step is operator triage on this issue doc + a redraft of the cross_cutting plan-of-record's
deliverables #1 + #2 todos to reflect the extension-not-greenfield path.

## Composes with

- "System-First Architecture (No Ad-Hoc Solutions)" — `SUB_AGENT_MANDATORY_RULES.md` § 0.
- "Single Source of Truth" — Citadel-Grade Planning Standards § 7.
- "No Technical Debt" — Citadel-Grade Planning Standards § 3.
- "Two teammates × multiple parallel agents — don't edit unfamiliar files" — both halves of CLAUDE.md.

## Addendum 2026-05-08 — Tab 6.B (Client model + capital allocation) overlap

> **Severity addendum**: P0 — Tab 6.B shipped before Tab 6.A's finding surfaced. Same root cause (greenfield design vs
> existing v2 SSOTs); same fix shape under Option A.

**What 6.B shipped** (`uac@3591037` `feat(uac): client model + capital allocation matrix SSOT — cross_cutting #3`,
pushed to live-defi-rollout):

- `unified_api_contracts/canonical/domain/client/__init__.py` — empty package marker
- `unified_api_contracts/canonical/domain/client/model.py` — `Client` + `VenueAccount` + `CapitalAllocation` +
  `CLIENTS_SEED` + `CAPITAL_ALLOCATION_SEED` + `AllocationViolationError` + 6 helper functions
- `unified_api_contracts/client.py` — NEW root facade re-exporting the public API
- `tests/unit/test_client_model.py` — 36 unit tests passing

**The parallel-SSOT overlap.** Searched 2026-05-08 post-ship — 2 of the 3 schemas duplicate existing UAC v2 SSOTs:

| 6.B-shipped symbol                                         | Existing UAC equivalent (pre-existing)                                                                                                                                                                                                                                                                                       | Status                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Client` (canonical/domain/client/model.py:155)            | `ClientDefinition` (`internal/domain/strategy_service/client_registry.py:36`) — frozen dataclass `client_id` / `name` / `entity` / `account_type` / `share_classes` / `is_active` / `seed`. **Re-exported through live `unified_api_contracts/strategy.py:97`**.                                                             | **PARALLEL SSOT.** Existing model is consumed by `RecordEnricher.stamp_client_name`, the trading-api routes, `generate_ui_reference_data` (UI pipeline), and the architecture-v2 derivation chain. 6.B's `Client` would split the `client_id → display name` resolution path across two SSOTs. The UAC `ClientRegistry` is the canonical workspace surface.             |
| `VenueAccount` (canonical/domain/client/model.py:126)      | `TradingAccount` + `AccountType` + `WalletRole` (`internal/domain/account.py:16+72`) — frozen dataclass with composite key `{client_id}:{venue}:{account_label}`, `AccountType` enum (CEFI_EXCHANGE / DEFI_WALLET / TRADFI_BROKER / SPORTS_BOOKMAKER / PREDICTION_MARKET), `WalletRole` enum (TREASURY / TRADING / RESERVE). | **PARALLEL SSOT.** Existing model "flows through execution → position → risk → P&L so every service agrees on what 'an account' is." 6.B's `VenueAccount` (`venue` + `account_id` + `is_subaccount` + `parent_account_id`) misses `WalletRole` (treasury / trading / reserve), the granular `AccountType` taxonomy across asset_groups, and the composite-key contract. |
| `CapitalAllocation` (canonical/domain/client/model.py:193) | **No equivalent.** Closest is `internal/domain/strategy_service/client_config.py` `ClientStrategyOverride` + `ClientConfigRegistry` (per-(client, strategy) config overrides) — but no per-(client, archetype, venue) capital allocation matrix with bounds-validated position cap + drawdown cap.                           | **GENUINE GAP** — 6.B's contribution here closes it. Right shape per Option A: lift `CapitalAllocation` + `validate_allocation_respect` + `is_within_allocation` into `internal/architecture_v2/capital_allocation.py` (alongside `client_registry.py`) and re-export through existing `strategy.py` facade — NOT through a new `client.py` facade.                     |

**Why this matters.** Same workspace HARD RULE collisions as the original Tab 6.A finding above: "Single Source of
Truth" (parallel `Client` + parallel `VenueAccount`); "System-First Architecture" (greenfield `canonical/domain/client/`
parallel to existing `internal/domain/strategy_service/client_registry.py` + `internal/domain/account.py`); "No
Technical Debt" (Citadel-Grade § 3 — duplicate dataclasses + competing facade re-exports `client.py` vs `strategy.py`).
Reference incidents in MEMORY.md auto-memory: this is the same parallel-SSOT-debt pattern the workspace has burned on 3+
times previously.

**Recommended decision (extends Option A above).** When the operator picks Option A:

1. Migrate `CapitalAllocation` + `AllocationViolationError` + `validate_allocation_respect` + `is_within_allocation` +
   `CAPITAL_ALLOCATION_SEED` from `unified_api_contracts/canonical/domain/client/model.py` →
   `unified_api_contracts/internal/architecture_v2/capital_allocation.py` (sibling to `client_registry.py`).
2. Re-export those 5 symbols through existing `unified_api_contracts/strategy.py` facade (alongside the existing
   `ClientDefinition` / `ClientRegistry` re-exports).
3. Delete `unified_api_contracts/canonical/domain/client/__init__.py` + `model.py` + `unified_api_contracts/client.py`
   (the 3 net-new parallel-SSOT files).
4. Migrate `tests/unit/test_client_model.py` → `tests/unit/test_capital_allocation.py` updating imports to the new path
   (the `CapitalAllocation` test cases stand; `Client` + `VenueAccount` test cases get deleted).
5. Re-shape `CapitalAllocation.archetype: ArchetypeRef = str` → `archetype: StrategyArchetype` (tightening the
   placeholder string type to the existing UAC enum). 6.B used `type ArchetypeRef = str` PEP-695 alias as an explicit
   migration point — single-edit widening.
6. Update the deliverable #3 [DESIGN+UAC] checkboxes in `cross_cutting_may_23_deliverables_2026_05_08.md` to reflect the
   partial revert: keep "Capital allocation matrix declared" flipped (genuine gap closed) + un-flip "Client model in UAC
   stable" (parallel SSOT — work already covered by existing `ClientRegistry` re-export).

**Until operator triages**: 6.B's `uac@3591037` + plan-flip `pm@366c66a4` stand on `live-defi-rollout`. Foreign agents
should NOT consume `from unified_api_contracts.client import Client` or `VenueAccount` — those imports will be reverted
under Option A. Consumers needing client identity should continue using
`from unified_api_contracts.strategy import ClientDefinition, ClientRegistry`. Consumers needing capital allocation
should defer until the migration to `strategy.py` re-export lands.

**Reference**: 6.B's commits + report:

- `uac@3591037` — `feat(uac): client model + capital allocation matrix SSOT — cross_cutting #3`
- `pm@366c66a4` — `docs(plans): cross_cutting Tab 6.B — ship client model + capital allocation UAC`

The parallel agent landed cleanly per the workspace cadence; the issue is upstream of 6.B (the Tab 6 main agent's spawn
prompt didn't pre-audit existing UAC v2 SSOTs before delegating). Same root cause as Tab 6.A's finding above — the codex
`strategy-summary.md` 8-family / 18-archetype baseline is stale and the Tab 6 plan-body was drafted against it without
auditing `unified_api_contracts/strategy.py` + `internal/architecture_v2/` + `internal/domain/strategy_service/`.
