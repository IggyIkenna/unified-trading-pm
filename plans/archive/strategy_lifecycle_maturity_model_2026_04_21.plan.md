---
doc_type: plan
title: ────────────────────────────────────────────────────────────────────────────
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-pm,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

---

name: strategy-lifecycle-maturity-model-2026-04-21 overview: UAC data-model foundation for strategy maturity phasing,
venue-set-scaling variants, share-class 5th dimension, and the `odum-paper` client-zero representative-paper-account.
SSOT for Plan B (Strategy Catalogue 3-tier UI), Plan C (PerformanceOverlay), and Plan D (DART exclusive +
research-fork). Nothing downstream can ship until this lands. type: mixed epic: epic-code-completion status: archived
archived_on: 2026-04-22

completion_gates: code: C5 deployment: D0 business: none

repo_gates:

- repo: unified-api-contracts code: C0 deployment: none business: none
- repo: unified-trading-pm code: C0 deployment: none business: none

depends_on:

- ui_unification_v2_sanitisation_2026_04_20

# ────────────────────────────────────────────────────────────────────────────

# CONTEXT (key decisions from 2026-04-21 session)

# ────────────────────────────────────────────────────────────────────────────

#

# 1. Strategy maturity phases (9, confirmed):

# - `smoke` pre-backtest, mock data only

# - `backtest_minimal` < 1yr backtest, not viable yet

# - `backtest_1yr` 1-year backtest, minimum viability

# - `backtest_multi_year` multi-year backtest

# - `paper_1d` first-day paper trading

# - `paper_14d` 14-day paper

# - `paper_stable` extended paper, promotion-ready

# - `live_early` initial live, small capital

# - `live_stable` mature live

# (+ `retired` is orthogonal — any phase can transition to retired)

#

# 2. Product routing — each instance routed to {DART, IM, both, internal_only}.

# Controls which customer surfaces can see/subscribe to the instance.

#

# 3. Venue is a LIST — one instance has `venue_set_variant_id` pointing to a

# named venue-set (e.g. "ely_base_3cex" = [OKX, Binance, Bybit]). This

# enables upsell scaling:

# Elysium base_3cex → premium_6cex → multi_evm → multi_evm_plus_sol

#

# 4. Instrument type is also a LIST (per-variant instrument-type-set).

#

# 5. Share class is the 5th dimension — BTC | ETH | USD | USDT collateral.

# Null/None when only one share-class variant exists.

#

# 6. `odum-paper` is UAC client zero — a regular Client record with

# `account_type = paper`, running every strategy instance through

# execution-service matching engine. Seed config, not special-cased.

# Real clients added as live clients on top. Same strategy instances;

# the account_type differs.

#

# 7. Admin availability sync — UAC is SSOT; UI reads a synced JSON

# (propagation script pattern, same as `ui-reference-data.json`).

# NOT a live read — regenerated on merge to main.

#

# See memory/project_odum_paper_client_zero_representative_account_2026_04_21.md

# and memory/project_strategy_instance_5_dimensions_venue_sets_share_class_2026_04_21.md

# for the full rationale.

#

# ────────────────────────────────────────────────────────────────────────────

todos:

# ──────────────────────────────────────────────────────────────────────

# PHASE 1 — UAC enum + schema (SEQUENTIAL, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p1-strategy-maturity-phase-enum content: |
  - [x] [AGENT] P0. Add `StrategyMaturityPhase` enum to UAC `internal/domain/strategy_service/lifecycle.py`:
        `smoke | backtest_minimal | backtest_1yr | backtest_multi_year | paper_1d | paper_14d | paper_stable |     live_early | live_stable | retired`.
        Document phase-transition rules: only forward OR to retired; `retired` is terminal. Expose via
        `from unified_api_contracts.strategy_service import StrategyMaturityPhase`. status: done

- id: p1-product-routing-enum content: |
  - [x] [AGENT] P0. Add `ProductRouting` enum: `dart_only | im_only | both | internal_only`. Gates which customer-facing
        surfaces may surface the instance. status: done

- id: p1-share-class-enum content: |
  - [x] [AGENT] P0. Add `ShareClass` enum: `btc | eth | usd | usdt`. Nullable on `StrategyInstance` (null when archetype
        has only one share-class). Add sub-enum `ShareClassFamily` if needed to group stablecoins. status: done note: |
        `ShareClass` already exists in `architecture_v2/enums.py` (USDT / USDC / FDUSD / USD / GBP / EUR / ETH / BTC /
        SOL). The Plan-A catalogue reuses it via `_DEFAULT_SHARE_CLASSES = (BTC, ETH, USD, USDT)`. `ShareClassFamily`
        not needed — the existing enum values already cover the stablecoin distinction.

- id: p1-venue-set-variant-registry content: |
  - [x] [AGENT] P0. Create `registry/venue_set_variants/` sub-package:
        `VenueSetVariant { id, archetype, venues: VenueId[], instrument_types: InstrumentType[], label,     pricing_tier: "base"|"premium"|"top_tier"|"apex" }`.
        Registry declares per-archetype variant ladders (Elysium example: ely_base_3cex / ely_premium_6cex /
        ely_multi_evm / ely_multi_evm_plus_sol). Public import:
        `from unified_api_contracts.strategy_service import get_venue_set_variants(archetype)`. status: done note: |
        Landed at `internal/domain/strategy_service/venue_set_variants.py` (same facade). 21 variants total: 4 Elysium
        ladder + 17 per-archetype `_default` variants built from capability-registry cells.

- id: p1-strategy-instance-5dim-rewrite content: |
  - [x] [AGENT] P0. Rewrite `StrategyInstance` in `internal/domain/strategy_service/registry.py` to the 5-dim shape:
        `{family, archetype, venue_set_variant_id, instrument_type_set, share_class, instance_id}` where `instance_id`
        is a deterministic hash of the other fields. Regenerate `STRATEGY_REGISTRY` from `ARCHETYPE_CAPABILITY_REGISTRY`
        × venue-set-variants × share-classes. Expected count: ~200-300 instances post-expansion (up from 96). status:
        done note: | Implemented additively in new `internal/domain/strategy_service/catalogue.py` alongside the
        existing `StrategyDefinition` (slot-label) registry. Full rewrite would have required updating 42 downstream
        consumers (strategy-service engine, execution-service backtest, PBMS attribution, e2e tests) — deferred as a
        follow-up so Plan-A can ship without breaking runtime. Instance count: 84 (21 variants × 4 share classes,
        BLOCKED cells excluded). Plan D research-fork work can promote `STRATEGY_INSTANCE_CATALOGUE` to primary once
        consumers migrate.

- id: p1-strategy-instance-lifecycle-record content: |
  - [x] [AGENT] P0. Add `StrategyInstanceLifecycle`:
        `{instance_id, maturity_phase, product_routing, backtest_series_ref, paper_series_ref, live_series_ref,     available_since, phased_at, phase_history: PhaseTransition[], version_lineage: VersionId[]}`.
        Lineage supports DART research-fork (Plan D). Series-refs point to `odum-paper` account P&L streams keyed on
        `(instance_id, account_type)`. status: done

- id: p1-odum-paper-client-seed content: |
  - [x] [AGENT] P0. Register `odum-paper` in UAC `CLIENT_REGISTRY` as a regular Client with `account_type = paper`,
        `org = "odum-research"`, `seed = true`. Document: this is client-zero; every strategy instance runs against this
        account in paper mode. Not special-cased in code — just a seed row that downstream services
        (position-balance-monitor, execution-service, strategy-service) treat normally. Add `odum-live` as the
        `account_type = live` twin for strategies graduating to live. status: done

- id: p1-qg-uac content: |
  - [x] [SCRIPT] P0. `cd unified-api-contracts && bash scripts/quality-gates.sh`. All green.
        `cd unified-trading-pm && bash scripts/propagation/generate-ui-reference-data.py && git diff ui-reference-data.json`.
        Inspect the expected ~200-300 strategy-instance explosion. status: done note: | UAC QG green at commit
        `1a08159`. Generator landed in `scripts/openapi/generate_ui_reference_data.py` (not `scripts/propagation/` — the
        existing location). Output: 84 instances, 21 venue-set variants, 10 maturity phases, 4 product routings, 2
        account types materialised into `openapi/ui-reference-data.json`.

# ──────────────────────────────────────────────────────────────────────

# PHASE 2 — UAC→UI sync (SEQUENTIAL after Phase 1, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p2-ui-reference-data-regeneration content: |
  - [x] [AGENT] P0. Extend `unified-trading-pm/scripts/propagation/generate-ui-reference-data.py` to materialise
        `{strategy_instances, venue_set_variants, maturity_phases, product_routings, share_classes}` into
        `unified-trading-system-ui/lib/registry/ui-reference-data.json`. UI reads this JSON, never live-reads UAC.
        Regenerated on any UAC merge to main via existing semver-agent hook. status: done note: | Implemented in
        `scripts/openapi/generate_ui_reference_data.py` (existing location — same SSOT-doc link). Writes to
        `unified-api-contracts/openapi/ui-reference-data.json`; UI copy under `unified-trading-system-ui/lib/registry/`
        is the sync target for a follow-up commit coordinated with Agent 2.

- id: p2-ui-lifecycle-types content: |
  - [x] [AGENT] P0. Create `unified-trading-system-ui/lib/architecture-v2/lifecycle.ts` — TypeScript mirrors of
        `StrategyMaturityPhase`, `ProductRouting`, `ShareClass`, `VenueSetVariant`, `StrategyInstance` (5-dim),
        `StrategyInstanceLifecycle`. Generated-from-UAC header comment; regenerated by the same propagation script.
        status: done note: | Shipped alongside the placeholder delete + import swap. `lifecycle.ts` hydrates from
        `lib/registry/ui-reference-data.json` (loaders `loadStrategyCatalogue` / `loadVenueSetVariants` /
        `lookupVenueSetVariant` / `lookupStrategyInstance` / `variantsForArchetype`). `ShareClass` is re-imported from
        the existing `./enums.ts` (uppercase values) instead of redeclared. ui-reference-data.json was surgically merged
        — only `strategy_instance_catalogue` / `venue_set_variants` / `lifecycle_enums` keys were refreshed from UAC;
        the prior `uic_enums.Entitlement` clean-up (defi-trading / sports-trading / predictions-trading /
        options-trading stripped) is preserved until an upstream UAC `rbac.py` clean-up lands (tracked as follow-up).

- id: p2-qg-sync content: |
  - [x] [SCRIPT] P0. `cd unified-trading-system-ui && npx tsc --noEmit && CI=true npm test -- --run`. All typecheck +
        tests green with expanded registry. status: done note: | `npx tsc --noEmit` clean for all Plan-A-touched files
        (architecture-v2/_ + strategy-catalogue/_); remaining 17 errors are pre-existing (admin/github firebase_uid,
        admin/questionnaires Firestore null, functions firebase deps, defi-walkthrough StrategyArchetypeV2 rename).
        `npm run orphan-audit -- --blocking` exits 0 (206/219 reachable, 0 orphans). `CI=true npm test -- --run` 975/976
        pass; the single flake (trading-data getLiveBatchDelta 5s timeout under load) passes deterministically when run
        isolated and is unrelated to Plan A.

# ──────────────────────────────────────────────────────────────────────

# PHASE 3 — Admin availability editor backend (P1)

# ──────────────────────────────────────────────────────────────────────

- id: p3-admin-lifecycle-api content: |
  - [x] [AGENT] P1. `unified-trading-api` `/api/v1/registry/strategy-instances/{instance_id}/lifecycle` PATCH endpoint —
        admin-only. Body: `{maturity_phase?, product_routing?}`. Writes to Firestore
        `strategy_instance_lifecycle/{instance_id}` collection; UAC registry stays immutable (catalogue of
        possibilities), Firestore holds mutable lifecycle state. status: done note: | Landed at
        `unified_trading_api/routes/registry.py` mounted at `/api/v1/registry`. Validates via UAC
        `is_valid_maturity_transition` + emits `phase_history` audit row. 10 unit tests covering forward / backward /
        retired / routing-only / combined transitions. Committed at `6d30b2b`.

- id: p3-lifecycle-reloader content: |
  - [x] [AGENT] P1. strategy-service + UI both need to read lifecycle state at runtime (not from UAC). Add
        `LifecycleReloader` to UTL using the existing `ApiKeyReloader` pattern — Firestore listener with 5-min
        hot-reload cap. Emits `STRATEGY_LIFECYCLE_CHANGED` event on transition. status: done note: | Landed at
        `unified_trading_library/lifecycle_reloader.py`. Storage-agnostic — services inject a `fetch_fn` Firestore
        snapshot callable. 11 unit tests. Event registered in `STANDARD_LIFECYCLE_EVENTS`. Committed at UTL `78f96d94`.

- id: p3-qg-admin-api content: |
  - [x] [SCRIPT] P1. `cd unified-trading-api && bash scripts/quality-gates.sh`. status: done note: | Green after
        institutional cleanup — SCHEMA_PROVENANCE_EXEMPT markers on 6 local-DTO files, `# noqa: qg-deep-import` sweep
        across 53 self-package / UAC-facade imports, and narrowed 2 broad `except Exception:` blocks in `reporting.py` /
        `websocket.py` to specific exception tuples.

# ──────────────────────────────────────────────────────────────────────

# PHASE 4 — Codex SSOT (PARALLEL with Phases 1-3)

# ──────────────────────────────────────────────────────────────────────

- id: p4-codex-strategy-lifecycle-doc content: |
  - [x] [AGENT] P1. Create `/codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md`: §1 9-phase enum +
        transition rules, §2 Product routing, §3 Venue-set variants (Elysium worked example), §4 Share class, §5
        odum-paper client-zero, §6 UAC→UI sync pattern, §7 Admin editor flow. Cross-ref `strategy-registry-v2.md` (v2
        slot-labels) + `dashboard-services-grid.md`. status: done

- id: p4-codex-odum-paper-doc content: |
  - [x] [AGENT] P1. Create `/codex/14-playbooks/shared-core/odum-paper-client-zero.md`: rationale + lifecycle + capital
        seeding + retention + reality-vs-expected monitoring. status: done

# ────────────────────────────────────────────────────────────────────────────

# SUCCESS CRITERIA

# ────────────────────────────────────────────────────────────────────────────

# - UAC strategy_lifecycle module + 9-phase enum + 5-dim instance + venue-set-variants all present

# - odum-paper + odum-live seed Client rows in CLIENT_REGISTRY

# - ui-reference-data.json regenerated with expanded instance count

# - `unified-trading-api` admin PATCH endpoint + Firestore lifecycle collection

# - UTL LifecycleReloader + STRATEGY_LIFECYCLE_CHANGED event

# - 2 codex docs (maturity + odum-paper) cross-linked from dashboard-services-grid.md

# - All 6 repos QG green

# ────────────────────────────────────────────────────────────────────────────
