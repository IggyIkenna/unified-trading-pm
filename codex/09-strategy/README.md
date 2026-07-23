---
scope: [engineer, admin]
---

# 09 — Strategy Documentation

> **SSOT:** [`architecture-v2/`](architecture-v2/README.md) is the canonical organisation for every trading strategy in
> the Unified Trading System. Legacy category-based docs (cefi / defi / sports / tradfi / templates + 7 absorbed
> cross-cutting docs) have moved to [`_archived_pre_v2/`](_archived_pre_v2/README.md) with pointers.

## Where to go first

- **Architecture v2 README**: [`architecture-v2/README.md`](architecture-v2/README.md) — full taxonomy (9 families × 57
  archetypes × 7 axes × 10 cross-cutting concerns) + Capital Flow Lifecycle. SSOT for counts: UAC `StrategyFamily` (9) /
  `StrategyArchetype` (57) / `InstructionActionV2` (14) enums. _(57 as of 2026-05-18 taxonomy V-1; was 55 pre V-1.)_
- **Migration audit**: [`architecture-v2/MIGRATION.md`](architecture-v2/MIGRATION.md) — every legacy doc / code module /
  config mapped to its v2 placement. Nothing is silently dropped.
- **Archive index**: [`_archived_pre_v2/README.md`](_archived_pre_v2/README.md) — if you're looking for a legacy doc.

### Architecture v2 — Deep docs

- [`architecture-v2/block-list.md`](architecture-v2/block-list.md) — BL-1..BL-10 hard-blocked (archetype × category ×
  instrument) combos with rationale, remediation, and UAC gap refs. Mirrored at runtime by
  `unified-trading-system-ui/lib/architecture-v2/block-list.ts`.
- [`architecture-v2/restriction-policy.md`](architecture-v2/restriction-policy.md) — per-family restriction matrix
  (allowed venues / instrument types / data types), lock-state default policy (PUBLIC vs
  `INVESTMENT_MANAGEMENT_RESERVED`), and the 6-axis questionnaire → visible-cells mapping.
- [`architecture-v2/dart-tab-structure.md`](architecture-v2/dart-tab-structure.md) — authoritative per-persona
  lifecycle-stage + DART sub-tab visibility matrix (8→4 lifecycle collapse, Observe/Research/Promote folded into DART,
  strategy-param version-bump contract, terminal emergency-banner copy). Mirrored at runtime by
  `unified-trading-system-ui/lib/auth/persona-lifecycle-shape.ts`.
- [`architecture-v2/strategy-registry-v2.md`](architecture-v2/strategy-registry-v2.md) — SSOT for the post-v1-delete
  `STRATEGY_REGISTRY` (UAC `internal/domain/strategy_service/registry.py`). 96 slot-labelled entries derived from
  `ARCHETYPE_CAPABILITY_REGISTRY`, `to_dict()` shape change manifest, downstream consumer mapping (7 repos), and the
  V2-suffix rename rationale.
- [`architecture-v2/admin-registry-api.md`](architecture-v2/admin-registry-api.md) — SSOT for the Phase 7 admin-only
  HTTP surfaces (`/api/v1/registry/{archetypes,ml-models,features}`) that let the UI `CatalogueTruthinessAdapter`
  reconcile UAC canonical lists against live backend registries. Endpoints owned by strategy-service (archetypes + ML
  models) and every `features-*-service` (features). Shared-secret `X-Admin-Token` auth, safe-by-default 503 when
  unconfigured.
- [`architecture-v2/naming-convention.md`](architecture-v2/naming-convention.md) — canonical strategy-id format
  (`FAMILY.ARCHETYPE.slot_id` fully-qualified OR `ARCHETYPE@slot_id` slot-label), parse + format contracts
  (`unified_api_contracts.strategy.parse_strategy_id` / `format_strategy_id`), per-surface usage table (UI URLs →
  fully-qualified, registry / records → slot-label), and legacy-migration notes.
- [`architecture-v2/legacy-family-migration.md`](architecture-v2/legacy-family-migration.md) — audit report for
  `p8-audit-legacy-family-strings`: lists UI files still using v1-era family strings (`basis-trade` / `mean-reversion` /
  `sports-arb` / `prediction-ml`), classifies each finding as DONE / DEFERRED-TO-PHASE-11 / NOT-A-TARGET, and records
  the route migrations already landed (`/basis-trade` → `/carry-basis` in UI `d417223`).

## What's still in this directory (not archived)

These docs remain live because they cover non-strategy concerns or operational playbooks that v2 explicitly links out
to, rather than absorbing:

### `cross-cutting/` — still authoritative

- [`cross-cutting/client-onboarding.md`](/codex/08-workflows/client-onboarding.md) — client-specific onboarding
  workflow. Referenced from `architecture-v2/cross-cutting/capital-client-isolation.md`.
- [`cross-cutting/client-strategy-config.md`](operational/client-strategy-config.md) — per-client strategy config
  surface. Extended by `architecture-v2/cross-cutting/portfolio-allocator.md`.
- [`cross-cutting/instrument-filtering.md`](operational/instrument-filtering.md) — major-asset whitelist + pool TVL
  rules. Referenced by every DeFi-touching archetype.
- [`cross-cutting/onboarding-checklist.md`](operational/onboarding-checklist.md) — operational checklist.
- [`cross-cutting/operational-modes-matrix.md`](architecture-v2/cross-cutting/operational-modes-matrix.md) — batch/live
  mode matrix. Referenced from `architecture-v2/cross-cutting/benchmark-fills.md`.
- [`cross-cutting/pnl-attribution.md`](architecture-v2/cross-cutting/pnl-attribution.md) — strategy-alpha vs
  execution-alpha split. Enhanced with benchmark-fills contract.
- [`cross-cutting/prediction-markets.md`](architecture-v2/cross-cutting/prediction-markets.md) —
  prediction-market-specific details.
- [`cross-cutting/rate-impact-model.md`](architecture-v2/cross-cutting/rate-impact-model.md) — rate impact curves.
  Referenced by Carry & Yield archetypes.
- [`cross-cutting/reward-lifecycle.md`](architecture-v2/cross-cutting/reward-lifecycle.md) — DeFi reward lifecycle.

### Top-level

- [`TIER_ZERO_UI_DEMO_AND_PARITY.md`](TIER_ZERO_UI_DEMO_AND_PARITY.md) — UI Tier-0 playbook (fixtures, cross-strategy
  UX, promotion path). UI-facing; not superseded by v2.

## What moved

Every category-organised strategy doc (`cefi/`, `defi/`, `sports/`, `tradfi/`, `templates/`) and the 7 cross-cutting
docs absorbed into v2's axes / cross-cutting primitives now live under
[`_archived_pre_v2/`](_archived_pre_v2/README.md). Git history is preserved; the archive README lists the v2 target for
each archived doc.

Three top-level docs that were superseded are in the archive too:

- `strategy-registry.md` → UAC `StrategyInstanceDefinition` + `StrategyInstanceIdentity` types are the registry now.
- `STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md` → superseded by
  [`architecture-v2/MIGRATION.md`](architecture-v2/MIGRATION.md).
- `execution-modes.md` → absorbed into
  [`/codex/04-architecture/backtest-groups.md`](/codex/04-architecture/backtest-groups.md)
  - [`architecture-v2/cross-cutting/benchmark-fills.md`](architecture-v2/cross-cutting/benchmark-fills.md).

## Legacy implementation code

Legacy strategy code in `strategy-service/strategy_service/engine/strategies/{cefi,defi,sports,tradfi,...}/` is still
load-bearing via the batch-dispatch factory `cli/handlers/batch_utils.create_strategy_instance()`. **Do not delete it
yet** — deletion is gated on the factory cutover to v2 archetype engines + shadow-deployment promotion per
`architecture-v2/MIGRATION.md` § 15 ("Legacy Code Deletion Schedule"). Tracked separately in
[`architecture-v2/MIGRATION.md`](architecture-v2/MIGRATION.md).
