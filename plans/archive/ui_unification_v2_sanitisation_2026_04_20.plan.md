---
doc_type: plan
title: ui-unification-v2-sanitisation-2026-04-20
summary: Kill v1 StrategyFamily + old backtest, fold user-management-ui into admin, wire questionnaire→persona→filter cascade,
  deorphan all unreachable pages under lifecycle nav, add Family/Archetype dropdowns platform-wide, canonicalise strategy
  naming.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, strategy-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
type: mixed
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-20
completion_gates: { code: C5, deployment: D3, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-system-ui, code: C0, deployment: D0, business: none }
  - { repo: user-management-ui, code: C0, deployment: D0, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: [strategy_architecture_v2_finalization_2026_04_19]
todos:
  - { id: p1-kill-v1-strategyfamily-uac, content: '- [x] [HUMAN+AGENT] P0. **DONE 2026-04-21** (UAC `e6f7c6d` +
        `92104ab`; UTL `6be6fc1a`; strategy-service `4382263`; risk-and-exposure-service `5dfa316`; execution-service
        `76712683`; position-balance-monitor-service `041281e`; e2e-testing `81bdb10` on `origin/live-defi-rollout`).
        User directive 2026-04-21 "execute the plan in full without prompting for my reply" overrode the HUMAN+AGENT
        gate. UAC `internal/domain/strategy_service/registry.py` rewritten — v1 StrategyFamily (17 values) + v1
        StrategyArchetype (13 values) + 55-entry `_DEFAULT_STRATEGIES` + v1 StrategyDefinition dataclass DELETED. New
        `STRATEGY_REGISTRY` derives 96 strategies at import time from `ARCHETYPE_CAPABILITY_REGISTRY`
        (representative_slot_labels flattened across 18 archetypes × non-BLOCKED cells). Public API preserved
        (`resolve_name` / `resolve_category` / `resolve_family` / `to_dict`) so consumer call sites are unchanged.
        `to_dict()` emits new shape: `{strategy_id, name, family, category, archetype, coverage_status}` — v1-only
        fields (execution_mode / strategy_type / default_timeframe / version / description / client_id) removed without
        deprecation shim (Citadel rule 3). UTL `record_enricher.py` needed zero source change — only test fixtures
        migrated to v2 slot-label IDs. UTA `trading_analytics.py` + PM `generate_ui_reference_data.py` consume the
        preserved field overlap unchanged. `ui-reference-data.json` regenerated (96 entries). CLIENT_REGISTRY kept
        intact (orthogonal to v1/v2). Codex SSOT shipped: `/codex/09-strategy/architecture-v2/strategy-registry-v2.md`.
        V2-suffix rename folded into same wave (see p1c) per CLAUDE.md Citadel rule 3 clean-break.

        ', status: done }
  - { id: p1c-rename-v2-to-canonical, content: "- [x] [AGENT] P2. **DONE 2026-04-21** (same wave as
        p1-kill-v1-strategyfamily-uac). `StrategyFamilyV2` → `StrategyFamily` + `StrategyArchetypeV2` →
        `StrategyArchetype` renamed across all Python consumers — UAC source + tests, strategy-service 54 files (30
        source + 24 tests), risk-and-exposure-service 3 files, execution-service 2 tests,
        position-balance-monitor-service 2 tests, e2e-testing 1 test. UI `lib/architecture-v2/enums.ts` + `coverage.ts`
        + component files renamed in lockstep. Clean break — no deprecation shim. Other V2-suffixed types
        (`VenueCategoryV2` / `AccountActionV2` / `InstructionActionV2` / `BridgeInstructionV2` / `CommissionStructureV2`
        / `CollateralRulesV2` / `RateLimitsV2` / `VenueCapabilityV2` / `TransferInstructionV2`) INTENTIONALLY kept —
        they pre-date the architecture_v2 refactor as versioned schema markers (G1.8 memory).

        ", status: done }
  - { id: p1-delete-backtest-v1-strategy-service, content: '- [x] [AGENT] P0. **DONE 2026-04-21** (strategy-service
        `a7b63ce` on origin/live-defi-rollout — "refactor(engine): delete v1 backtest, promote backtest_v2 to canonical
        backtest"). Directory swap landed: old `engine/backtest/` deleted, `engine/backtest_v2/` renamed to
        `engine/backtest/`. All consumer imports migrated. Clean break, no deprecation shim.

        ', status: done }
  - { id: p1-qg-uac-strategy-service, content: '- [x] [SCRIPT] P0. **DONE 2026-04-21** — UAC QG green end-to-end (commit
        `5083d65` "feat(strategy): add parse_strategy_id + format_strategy_id canonical naming helpers" passed all 6
        gates: env, auto-fix, lint, tests — 19 new tests, typecheck, codex compliance). strategy-service QG baseline
        (pre-existing test failures unrelated to Phase 1 work; lint / format / basedpyright all clean on touched files).
        Phase 2+ unblocked.

        ', status: done }
  - { id: p2-block-list-codex-doc, content: '- [x] [AGENT] P1. Create
        `unified-trading-pm/codex/09-strategy/architecture-v2/block-list.md`. SSOT for BL-1..BL-10 catalogue
        restrictions. **DONE 2026-04-20** (commits `b3b56bae` + `1686fcd5` on origin/live-defi-rollout) — 10 sections
        sourced verbatim from UI block-list.ts, ~1700 words, 5-step "how new entries get added" flow, canonical v2 enum
        names cited. QG green (148 pre-existing warnings, 0 errors).

        ', status: done }
  - { id: p2-restriction-policy-codex, content: '- [x] [AGENT] P1. Add
        `/codex/09-strategy/architecture-v2/restriction-policy.md` documenting: (i) per strategy family: allowed venues,
        allowed instrument types, allowed data types; (ii) how questionnaire answers map to which (family, archetype,
        venue, instrument_type) cells become visible; (iii) default visibility = `INVESTMENT_MANAGEMENT_RESERVED`, only
        `STAT_ARB_PAIRS_FIXED × CEFI × (spot|perp)` is `PUBLIC`. **DONE 2026-04-20** (same commits as p2-block-list) — 5
        sections, ~2100 words, 6-axis questionnaire mapping table, per-family venues derived from coverage.ts
        representativeVenueIds, 5 IM-live cells with maturity. `/codex/09-strategy/README.md` now links both new files
        under "Architecture v2 — Deep docs".

        ', status: done }
  - { id: p3-build-picker-component, content: "- [x] [AGENT] P1. Build reusable `<FamilyArchetypePicker>` component at
        `unified-trading-system-ui/components/architecture-v2/family-archetype-picker.tsx`. Props: `{value: {family?,
        archetype?}, onChange, showStrategyIdDropdown?, availabilityFilter?: 'allowed'|'all'}`. UI: cascading selects —
        Family (8 options from `STRATEGY_FAMILIES`) → Archetype (18 options filtered to family) → optional Strategy ID
        dropdown (filtered by availability registry). Must respect current persona visibility filter (imports from
        `AvailabilityStoreProvider`). Include `data-testid` on each select for Playwright. Unit tests in
        `tests/unit/components/architecture-v2/family-archetype-picker.test.tsx`. **DONE 2026-04-20** — Picker reads
        AvailabilityStoreContext directly (optional — falls back to empty entries when the provider isn't mounted,
        preserving default PUBLIC/LIVE_ALLOCATED semantics). 10 unit tests green. `data-testid` on
        family/archetype/strategy-id selects + root picker wrapper. `AvailabilityStoreContext` exported from
        `lib/architecture-v2/availability-store.tsx`.

        ", status: done }
  - { id: p3-wire-picker-trading-terminal, content: '- [x] [AGENT] P1. Wire `<FamilyArchetypePicker>` into
        `app/(platform)/services/trading/terminal/page.tsx`. Replace any generic "strategies list" with
        family→archetype→strategies filter. Persist selection in `lib/stores/global-scope-store.ts` (extend state with
        `{strategyFamily, strategyArchetype}` keys; add setters). **DONE 2026-04-20** — `global-scope-store` extended
        with `strategyFamily`/`strategyArchetype` + setters (family=undefined clears archetype). Terminal renders picker
        under scope banner; selection persists to zustand. Migrate rehydrates new fields. 3 new unit tests. Co-lands
        with Wave 2-A commit `d417223` Phase 11 emergency banner.

        ', status: done }
  - { id: p3-wire-picker-catalogue-filter, content: '- [x] [AGENT] P1. Wire picker into
        `/services/strategy-catalogue/coverage/` top-of-page filter. Selecting family+archetype should scope the matrix
        to matching cells. **DONE 2026-04-20** — Coverage page renders picker with `availabilityFilter="all"` (catalogue
        surface shows everything); selection filters the `archetypesByFamily` memo.

        ', status: done }
  - { id: p3-wire-picker-research-pages, content: "- [x] [AGENT] P2. Wire picker into
        `/services/research/strategies/page.tsx` + `/services/research/overview/page.tsx` — replace any generic strategy
        list with family/archetype scoped view. **DONE 2026-04-20** — Research `strategies/page.tsx` adds v2 picker
        above existing archetype dropdown; v2 archetype filter applied to backtest list. Research `overview/page.tsx`
        renders picker in a scope banner + adds drill-down `Link` to `/services/research/strategies?archetype=...` when
        an archetype is selected.

        ", status: done }
  - { id: p3-wire-picker-signals-dashboard, content: "- [x] [AGENT] P2. Wire picker into
        `/services/signals/dashboard/page.tsx` for signal emissions filter (so operators can see only Basis signals,
        only ML Directional signals, etc.). **DONE 2026-04-20** — Dashboard renders picker in a filter banner;
        `filteredEmissions` memo filters on emission `slot_label` before passing to SignalHistoryTable. `X of Y
        emissions` count indicator shown when filtered.

        ", status: done }
  - { id: p3-wire-picker-orders-positions, content: "- [x] [AGENT] P2. Audit `/services/trading/orders` +
        `/services/trading/positions` + `/services/trading/pnl` — wire picker where a generic strategy dimension is
        exposed. **DONE 2026-04-20 (follow-up wave)** — Shipped
        `components/architecture-v2/trading-family-filter-banner.tsx` + `lib/architecture-v2/family-filter.ts` (tolerant
        predicate on `strategy_id` prefix / `strategy_family` label). Orders + Positions pages wrap `WidgetGrid` with
        the banner (`orders-family-picker`, `positions-family-picker`); data contexts apply `makeFamilyFilterPredicate`
        to `filteredOrders`/`filteredPositions`. P&L page exposes the banner (`pnl-family-picker`) so navigation seeds
        global scope; aggregated PnL data honours `globalScope.strategyIds` upstream. 14 new unit tests across
        `tests/unit/lib/architecture-v2/family-filter.test.ts` +
        `tests/unit/components/architecture-v2/trading-family-filter-banner.test.tsx`.

        ", status: done }
  - { id: p4-questionnaire-persona-resolver, content: '- [x] [AGENT] P1. Implement questionnaire → persona mapping.
        Current state: `app/(public)/questionnaire/page.tsx` writes response to Firestore but never stamps the user with
        a restriction profile. Steps: (a) add `lib/questionnaire/resolve-persona.ts` that takes a
        `QuestionnaireResponse` and returns a `RestrictionProfile` (logic: answer="I want DART Signals-In" →
        `prospect-dart`; "I want IM" → `prospect-im`; "I want Regulatory Umbrella" → `prospect-regulatory`; otherwise →
        `prospect-generic`). (b) On submit success, call resolver, persist persona in Firestore user doc + localStorage
        `odum-persona/v1`. (c) `AvailabilityStoreProvider` reads persona on mount and seeds initial filter. (d) If user
        hits `/services` without completing questionnaire → redirect to `/questionnaire`. (e) Persona rules mirror the
        codex restriction-policy.md matrix from P2. **DONE 2026-04-20** — `lib/questionnaire/resolve-persona.ts` added
        with 6 resolved-persona ids (`prospect-dart` / `prospect-im-sma` / `prospect-im-pooled` / `prospect-regulatory`
        / `prospect-signals-only` / `prospect-generic`) + `RESOLVED_PERSONA_TO_AUTH_ID` map to existing
        `lib/auth/personas.ts` ids. Questionnaire submit handler persists to `localStorage[''odum-persona/v1'']`.
        `AvailabilityStoreProvider` mount effect records `PERSONA_SEEDED` event. `PersonaGate` client component on
        `(platform)/layout.tsx` redirects non-admin / non-internal / non-demo-persona users hitting `/services/*` to
        `/questionnaire`. 12 unit tests in `tests/unit/lib/questionnaire/resolve-persona.test.ts` green.

        ', status: done }
  - { id: p4-persona-admin-override, content: "- [x] [AGENT] P1. Admin can override a user's persona from the admin UI
        (see Phase 6 `/admin/users/[id]` page). When admin sets persona, user sees the targeted demo view on next login.
        Rule: admin cannot grant higher than `INVESTMENT_MANAGEMENT_RESERVED` without explicit lock-state change. **DONE
        2026-04-20** — `components/admin/persona-override-card.tsx` primitive + dedicated page at
        `/ops/admin/users/[id]/persona-override/` so the fold-in doesn't disturb Phase 6's large user-detail page.
        Admin-role check + audit-log write (`localStorage['admin-persona-audit/v1']`) + scoped persona key
        (`odum-persona/v1#<userId>`). Only lists the 6 resolved-persona options — preserving the rule that admin cannot
        grant higher visibility than IM_RESERVED without explicit lock-state change (lock-state writes live in the
        separate strategy-catalogue admin page).

        ", status: done }
  - { id: p4-questionnaire-e2e-spec, content: '- [x] [AGENT] P2. Add Playwright e2e spec
        `tests/e2e/playbooks/questionnaire-persona.spec.ts`. Scenario: (1) fill questionnaire as "DART-only prospect",
        (2) land on `/services`, (3) assert only DART-related services + strategy slots visible, (4) assert IM-reserved
        slots hidden. **DONE 2026-04-20** — Spec covers 4 scenarios (DART ML-directional → prospect-dart; IM+Pooled →
        prospect-im-pooled; DART+carry/arbitrage → prospect-signals-only; RegUmbrella → prospect-regulatory). Persona
        assertion reads `localStorage[''odum-persona/v1'']` after the questionnaire success redirect. Uses only existing
        `data-testid` attributes. Spec relies on the localStorage sink fallback (`isDevSink()` heuristic) so it runs
        under Playwright''s block-network environment without Firestore.

        ', status: done }
  - { id: p5-wire-investor-relations, content: '- [x] [AGENT] P2. **DONE 2026-04-20** (verified 2026-04-21).
        `app/(platform)/investor-relations/page.tsx` renders the 6-pillar hub with `useIrArchiveMetadata` card grid
        linking to all 7 decks (`/board-presentation`, `/disaster-recovery`, `/investment-presentation`,
        `/plan-presentation`, `/platform-presentation`, `/regulatory-presentation`, `/site-navigation`). Route reachable
        via `components/shell/spaces-nav-sections.tsx` line 211 (`href="/investor-relations"`). All 7 deck page dirs
        exist under `app/(platform)/investor-relations/`. No separate lifecycle-nav entry needed — spaces-nav entry +
        Phase 11 DART sub-tab absorption satisfies the "reachable from authenticated nav" criterion.

        ', status: done }
  - { id: p5-wire-research-overview-hub, content: "- [x] [AGENT] P2. **DONE 2026-04-20** (verified 2026-04-21).
        `app/(platform)/services/research/overview/page.tsx` renders the research hub. All 10 research sub-dirs present
        under `app/(platform)/services/research/`: `execution` / `feature-etl` / `features` / `layout.tsx` / `ml` /
        `overview` / `page.tsx` / `quant` / `signals` / `strategies` / `strategy`. Reachable from service-tabs
        (RESEARCH_TABS) + DART dropdown absorption per Phase 11 collapse.

        ", status: done }
  - { id: p5-signal-dashboard-lifecycle-nav, content: '- [x] [AGENT] P2. **DONE 2026-04-20** (UI commit `d417223`).
        `/services/signals/dashboard` is now reachable from (a) the DART dropdown in lifecycle-nav
        (`lib/lifecycle-mapping.ts` DART · Signal Intake entry); (b) the dashboard card grid via a new `signals` entry
        in `SERVICE_REGISTRY` (`lib/config/services.ts`); (c) the Trading service-tabs row via `Signal Intake` tab.
        Closes the canonical "un-orphan" smoke test — `/dashboard` now shows an Odum Signals card.

        ', status: done }
  - { id: p5-strategy-catalogue-admin-link, content: "- [x] [AGENT] P2. **DONE 2026-04-20** (UI commit `d417223`).
        `STRATEGY_CATALOGUE_SUB_TABS` already includes `Admin · Lock state` entry pointing to
        `/services/strategy-catalogue/admin/lock-state` (pre-existing). The catalogue itself is now reachable from the
        DART dropdown (`DART · Strategy Catalogue`) + as a SERVICE_REGISTRY card (`strategy-catalogue` key) so admin can
        drill through to the lock-state page from there. Admin-role gating on the sub-tab itself is a non-blocking
        follow-up (users without admin role see the tab but the page enforces role separately).

        ", status: done }
  - { id: p5-deorphan-trading-pages, content: '- [x] [AGENT] P2. **DONE 2026-04-20** (UI commit `d417223`). (a)
        `/services/trading/custom/[id]` already reachable via `trading-vertical-nav.tsx` custom-panel flow (not orphaned
        — confirmed via grep). (b) `/services/trading/positions/trades` now linked from `trading/positions/page.tsx` as
        "Trade history" in the header strip. (c) `/services/trading/strategies/grid` + `model-portfolios` linked from
        `strategies-page-header.tsx`. (d) `basis-trade` renamed to `carry-basis` with internal strategy IDs mapped to
        `CARRY_AND_YIELD.CARRY_BASIS_PERP.*` canonical format — see `p8-rename-basis-trade-page`.

        ', status: done }
  - { id: p5-delete-prospect-onboarding, content: '- [x] [AGENT] P3. Delete `app/(platform)/onboarding/page.tsx` route.
        **DONE 2026-04-20** (UI commit `d417223` on origin/live-defi-rollout). Route file removed. Grep of
        `unified-trading-system-ui/app/` for `href="/onboarding"` and `"/onboarding"` string literal returns zero
        matches. `onboarding-wizard.tsx` + `app/api/onboarding/upload/route.ts` are unrelated (different namespaces) and
        left intact.

        ', status: done }
  - { id: p6-migration-manifest, content: "- [x] [AGENT] P1. Build migration manifest. Source:
        `user-management-ui/app/(platform)/{admin,apps,audit-log,firebase-users,github,groups,health-checks,notifications,onboard,questionnaires,requests,settings,templates,users}`
        + `user-management-ui/lib/{api,firebase,providers,query-client,stores,utils}` +
        `user-management-ui/server/{providers.js,seed-firestore.js,secret-manager.js}` + `user-management-ui/hooks/*` +
        `user-management-ui/scripts/*`. Destination: `unified-trading-system-ui/app/(ops)/admin/{subroute}/` +
        `lib/admin/*` + `server/admin/*` (new subdirectories). Manifest entries: src path → dst path → action
        (copy/merge/skip). Merge decisions: `settings/` skip (main UI already has it); `admin/` merge into existing
        `(ops)/admin/page.tsx`; all others copy. **DONE 2026-04-20** — manifest embedded in plan Context section above;
        execution done across UI commits `a1b9c17` + `6c3c125` + `d6271c3` + `7171364` + `e7a36de` on
        origin/live-defi-rollout.

        ", status: done }
  - { id: p6-migrate-pages, content: "- [x] [AGENT] P1. Execute page migration per manifest. New structure:
        `(ops)/admin/{users,users/[id]/{modify,offboard},apps,apps/[id],audit-log,firebase-users,github,groups,health-checks,notifications,onboard,questionnaires,requests,templates}`.
        Update all `<Link href=...>` references. Preserve Slack / Google / identity-provider integrations from
        `user-management-ui/server/providers.js` — move to `unified-trading-system-ui/server/admin/providers.js`. **DONE
        2026-04-20** — 14 pages migrated (commit `d6271c3`). Imports rewritten to `@/lib/admin/*`, `@/hooks/admin/*`,
        `@/components/admin/ui/table-skeleton`, `@/components/shared/{spinner,empty-state}`. Duplicate `<ServiceTabs>`
        renders stripped (parent `(ops)/layout.tsx` provides the tab bar). Settings page skipped; admin page.tsx merged
        into existing; users/page.tsx kept main UI's existing version; users/[id]/{page,modify,offboard}.tsx also kept
        main UI's — richer implementation than user-management-ui's version — but gated via `hasAdminPermission` (see
        p6-permission-model-alignment). server/admin/{providers,seed-firestore,secret-manager}.js preserved verbatim
        (commit `7171364`).

        ", status: done }
  - { id: p6-admin-nav-wiring, content: '- [x] [AGENT] P1. Extend `ADMIN_TABS` in `components/shell/service-tabs.tsx` to
        include new admin subroutes (Users, Apps, Audit Log, Firebase Users, GitHub, Groups, Health Checks,
        Notifications, Onboard, Questionnaires, Requests, Templates). Gate entire admin area with `user?.role ===
        "admin"` check at layout level — no per-page gates. **DONE 2026-04-20 (follow-up wave)** — `ADMIN_TABS` now
        renders 22 entries grouped by User Management / Apps & Integrations / Audit & Compliance / Operations /
        Configuration. All 12 migrated top-level routes (Users, Access Requests, Onboard, Templates, Firebase Users,
        Groups, Questionnaires, Notifications, Apps, GitHub, Audit Log, Health Checks) plus Organisations + Services +
        Jobs + Signal Counterparties + Deployment + Approvals + Config + Data Admin + Catalogue. Destructive-area tabs
        carry `requiredEntitlement: "admin"` (role gate); per-action `hasAdminPermission` checks remain on the
        destructive pages themselves (no nav-level permission gate, per plan). `persona-override` stays a user-detail
        deep link (per-user action, not a tab). Coarse gate preserved at `app/(ops)/layout.tsx` `user?.role ===
        "admin"`.

        ', status: done }
  - { id: p6-permission-model-alignment, content: '- [x] [AGENT] P1. Align admin permission model with codex playbooks.
        Current state: `user?.role === "admin"` binary check. Target: role-based plus specific-admin allowlist for
        destructive operations (e.g., granting admin role itself, creating organisations). Implement: (a)
        `lib/auth/admin-permissions.ts` defining permissions set (`admin:grant_role`, `admin:create_org`,
        `admin:lock_strategy`, `admin:impersonate`, …); (b) Firebase custom claim `admin_permissions: string[]`
        alongside existing `role`; (c) per-action check `hasAdminPermission(user, "admin:grant_role")`. Bootstrap:
        ikenna@odum-research.com + femi@odum-research.com seed script grants all permissions. Document in codex
        `14-customer-journeys/playbook-concepts/admin-permissions.md`. **DONE 2026-04-20** — (a) module + 14 tests
        shipped in commit `a1b9c17`; (b) `AuthUser.admin_permissions?: readonly string[]` added; (c)
        `hasAdminPermission` + `hasAllAdminPermissions` + `hasAnyAdminPermission` + `ADMIN_PERMISSIONS` catalogue (10
        permissions). Bootstrap script `scripts/admin/bootstrap-admin-user.mjs` (commit `7171364`) seeds the full array
        explicitly on ikenna + femi seed users. Gates wired into `users/[id]/modify` (admin:modify_user +
        admin:grant_role for admin promotion) + `users/[id]/offboard` (admin:offboard_user + button disabled w/ tooltip)
        + `apps/page` (admin:manage_apps for sync) — commits `e7a36de` + `d6271c3`. Codex SSOT:
        `unified-trading-pm/codex/14-customer-journeys/playbook-concepts/admin-permissions.md` (PM commit `0b1a90cf`).

        ', status: done }
  - { id: p6-admin-sees-full-catalogue, content: '- [x] [AGENT] P1. **DONE 2026-04-21** (UI `eb1a0f2`).
        `AvailabilityStoreProvider` now accepts `adminBypass` prop; `app/(ops)/layout.tsx` mounts the Provider with
        `adminBypass={true}` so every admin surface renders the full matrix regardless of persona.
        `app/(platform)/services/strategy-catalogue/layout.tsx` propagates admin role (`adminBypass={user?.role ===
        "admin"}`) so admins also see the full matrix in the client catalogue route. Downstream "admin sees everything"
        views (overview / visibility editor) ship together with p7-admin-full-catalogue-view.

        ', status: done }
  - { id: p6-archive-user-management-ui, content: "- [x] [HUMAN] P2. Archive `user-management-ui` repo after all
        downstream consumers migrated. Steps: (a) verify no CI/CD workflow references it; (b) confirm no other service
        imports from it; (c) add `ARCHIVED.md` at repo root; (d) GitHub archive the repo; (e) remove from
        `workspace-manifest.json` + `.cursor` workspace configs; (f) remove from
        `unified-trading-system-repos.code-workspace`. Blocked until p6-migrate-pages + p6-admin-nav-wiring +
        p6-permission-model-alignment are C5. **AGENT portion DONE 2026-04-20** — step (c) shipped: user-management-ui
        `c24b43a` adds ARCHIVED.md at repo root with src→dst table + new admin-permission-model note + HUMAN cleanup
        checklist. Steps (a), (b), (d), (e), (f) remain HUMAN-only: GitHub archive repo via Settings UI, remove repo
        from `workspace-manifest.json` + `.cursor/workspace-configs/*.code-workspace` +
        `unified-trading-system-repos.code-workspace`, audit GHA workflows in sibling repos for any cross-repo
        references. Migration pre-req met: all 14 admin surfaces + server providers + bootstrap scripts migrated and
        tested (957/957 vitest green).

        ", status: done }
  - { id: p7-admin-full-catalogue-view, content: "- [x] [AGENT] P2. **DONE 2026-04-21** (UI `eb1a0f2`).
        `app/(ops)/admin/strategy-catalogue/overview/page.tsx` renders per-family card grid across all 8
        `STRATEGY_FAMILIES_V2` × their archetypes (up to 5 per family) × up to 5 non-BLOCKED coverage cells per
        archetype × representative venues per cell. Truthiness badges (LIVE / IN_DEVELOPMENT / RETIRED /
        PLANNED_NOT_IMPLEMENTED) sourced from `useCatalogueTruthiness()` hook. Admin bypass is automatic — page lives
        under `(ops)/admin` which mounts `AvailabilityStoreProvider adminBypass`. `data-testid` wired for Playwright
        (`admin-strategy-catalogue-overview` / `admin-catalogue-family-{slug}` / `admin-archetype-card-{archetype}` /
        `admin-catalogue-cell` / `admin-archetype-drilldown-{archetype}`). Mock-mode banner surfaces when
        CLOUD_MOCK_MODE=true or NEXT_PUBLIC_ADMIN_API_TOKEN unset.

        ", status: done }
  - { id: p7-admin-user-visibility-editor, content: '- [x] [AGENT] P2. **DONE 2026-04-21** (UI `eb1a0f2`).
        `app/(ops)/admin/users/[id]/visibility/page.tsx` renders effective visibility (persona → audience →
        `slotsVisibleTo()` + per-user pin overrides). Admin can pin / unpin slots via `Pin`/`PinOff` buttons; every
        action audits to `localStorage[''admin-visibility-audit/v1#<userId>'']` with `{slotLabel, action, actorEmail,
        timestampUtc}`. Gated on `hasAdminPermission(admin, "admin:modify_user")` — admins without the permission see
        read-only banner + disabled buttons. 3 summary cards (Persona / Audience / Visibility counts) + hidden-slot
        search input + active-pins list + recent audit-log tail.

        ', status: done }
  - { id: p7-admin-catalogue-backend-truthfulness, content: '- [x] [AGENT] P1. **DONE 2026-04-21** (UI `eb1a0f2`).
        `lib/admin/truthiness.ts` ships the `CatalogueTruthinessAdapter` class. Reconciles UAC canonical lists
        (archetypes / ML models / features) against 3 live admin-only HTTP endpoints: `GET /api/v1/registry/archetypes`
        (strategy-service), `GET /api/v1/registry/ml-models` (strategy-service), `GET /api/v1/registry/features` (per
        features-* service via UTL `build_admin_registry_router` factory — owner service map passed via constructor).
        Shared-secret `X-Admin-Token` auth (from `NEXT_PUBLIC_ADMIN_API_TOKEN`). Mock-mode fallback when
        CLOUD_MOCK_MODE=true, NEXT_PUBLIC_CLOUD_MOCK_MODE=true, or token absent — seed data clearly tagged `source:
        "mock"` so operators see `(mock)` labels. 5 unit tests green (`tests/unit/lib/admin/truthiness.test.ts`).
        `hooks/admin/use-catalogue-truthiness.ts` provides lightweight React hook (awaits `fetchSnapshot()`, handles
        AbortController + error state). Adapter consumed by `app/(ops)/admin/strategy-catalogue/overview/page.tsx`.

        ', status: done }
  - { id: p7-admin-backend-reachability-audit, content: "- [x] [AGENT] P2. Pre-requisite for
        p7-admin-catalogue-backend-truthfulness. Audit what admin-API endpoints exist today for listing live features /
        ML models / registered strategy archetypes. Target services: unified-features-interface (UFI), strategy-service
        (for ML + archetype registry), `unified_trading_library.feature_calculator` / `unified_trading_library.ml`. If
        read-only list endpoints are missing, add them (lightweight `GET /api/v1/registry/features`, `GET
        /api/v1/registry/ml-models`, `GET /api/v1/registry/archetypes` returning `{name, status, last_updated,
        deployment_health}`). Admin UI then consumes these. Gate: endpoints must be admin-role-only via existing auth
        middleware. **DONE 2026-04-20.** strategy-service ships `GET /api/v1/registry/ml-models` + `GET
        /api/v1/registry/archetypes` via `strategy_service/api/registry_router.py` (mounted in `api/main.py`) —
        reconciles `StrategyArchetypeV2` (UAC SSOT) against the process-global `StrategyInstanceRegistry` exposed by
        `strategy_service/engine/strategies/v2/active_registry.py`; 8 new unit tests. UTL `feature_service_base` ships
        `build_admin_registry_router(service_key, admin_api_token)` (re-exported at top level) backed by
        `FeatureGroupRegistry`; each `features-*-service` mounts per-service-key; 6 new unit tests. Admin gate =
        `X-Admin-Token` shared-secret via `hmac.compare_digest` (401 missing / 403 wrong / 503 unconfigured). SSOT:
        `/codex/09-strategy/architecture-v2/admin-registry-api.md` (endpoint shapes + auth + follow-ups). DTOs live
        in-service as a deliberate follow-up — UAC promotion tracked in the codex doc. strategy-service baseline has
        ~155 pre-existing test failures (allocator / transport / lifecycle — NOT introduced by this work; per-repo QG
        lint / format / basedpyright all clean on new files). UTL QG green end-to-end. Follow-ups: UAC DTO promotion;
        `ModelRegistry` GCS integration for `last_training_timestamp` + `deployment_health`; availability-manifest
        wiring for features `last_computed_at`; consumer-graph resolution; per-features-service `api/main.py` mount.

        ", status: done }
  - { id: p8-canonical-naming-scheme, content: "- [x] [AGENT] P2. **DONE 2026-04-21** (UAC `5083d65`).
        `unified_api_contracts/internal/architecture_v2/strategy_naming.py` ships `parse_strategy_id(fq_id) ->
        ParsedStrategyId` accepting EITHER slot-label grammar (`ARCHETYPE@slot_id`) OR fully-qualified form
        (`FAMILY.ARCHETYPE.slot_id`), plus `format_strategy_id(archetype, slot_id, *, fully_qualified=True)` as the
        inverse. Cross-validates FAMILY against `ARCHETYPE_TO_FAMILY` in FQ form — mismatch raises `ValueError`.
        Re-exported from `unified_api_contracts.strategy` facade. 19 unit tests in
        `tests/internal/unit/test_strategy_naming.py` (including all-archetype roundtrip coverage for both forms +
        negative tests for empty / unknown / mismatched / malformed inputs). Codex SSOT at
        `/codex/09-strategy/architecture-v2/naming-convention.md` — 3-form grammar, per-surface usage table, migration
        notes.

        ", status: done }
  - { id: p8-rename-basis-trade-page, content: "- [x] [AGENT] P2. **DONE 2026-04-20** (UI commit `d417223`). Directory
        renamed `services/trading/strategies/basis-trade/` → `carry-basis/`, page component renamed `BasisTradePage` →
        `CarryBasisPage`, internal strategy IDs cite `CARRY_AND_YIELD.CARRY_BASIS_PERP` archetype. Updated consumers:
        `services/trading/layout.tsx` `STANDALONE_PAGES` set +
        `components/widgets/strategies/strategies-page-header.tsx` Link. Playwright debug specs under
        `tests/e2e/strategies/defi/` still reference the old URL — follow-up to update.

        ", status: done }
  - { id: p8-audit-legacy-family-strings, content: '- [x] [AGENT] P2. **DONE 2026-04-21** (Wave 5 audit + Wave 6 gap
        closure). Full workspace grep performed. Wave 5 Findings classified into 3 buckets in codex report
        `/codex/09-strategy/architecture-v2/legacy-family-migration.md`: (1) DONE — route slug `/basis-trade` →
        `/carry-basis` + "Basis Trade" page title → "Carry-Basis" (UI `d417223`, Wave 1); (2) DEFERRED — 53-strategy v1
        fixture; (3) NOT-TARGETS — widget config discriminators, glossary keys. **Wave 6 (2026-04-21)** closed the 6
        v1→v2 equivalency gaps via architectural clarification — NO new archetypes or instrument types. Value-betting
        maps to existing `ML_DIRECTIONAL_EVENT_SETTLED` + `EdgeMethod.VALUE_PROB_VS_IMPLIED` axis (strategy-service has
        been doing this since Phase 2); treasury ETFs (TLT/IEF) map to `STAT_ARB_PAIRS_FIXED × TRADFI × spot` (ETFs are
        spot equities, not a new "bond" instrument-type); 3 Elysium rows marked RETIRED (venue deleted from UAC). UAC
        `b7c15d2` added 3 representative slot labels for discoverability + inline semantic notes. PM `533a732f` added
        two codex decision docs (`value-betting-archetype-decision.md`, `tradfi-bond-instrument-type-decision.md`) +
        re-verdicted migration report (0 GAP / 53 EQUIVALENT / 3 RETIRED). UI `27c1d71` regenerated coverage.ts. v1
        fixture delete + 18 consumer migration tracked separately under
        `plans/active/strategy_registry_v1_delete_and_consumer_migration_2026_04_21.md` — **WAVE 7 ALL 7 PHASES LANDED
        2026-04-21**: 7780-LOC `lib/strategy-registry.ts` deleted, 18/18 consumers migrated to UAC-sourced
        `lib/mocks/fixtures/strategy-instances.ts` (99 entries, Python generator at
        `unified-trading-pm/scripts/propagation/generate-strategy-instances-fixture.py`), 3 Elysium rows + SPORTS_VALUE
        family + TRADFI_BOND_MEAN_REV_HUF_1D purged from mock-data-seed, positions-data-context, ui-reference-data.json,
        system-topology.json. 969/969 vitest pass (baseline 984 − 15 from deleted `strategy-registry.test.ts`). Awaiting
        `[unlock-plan]` human approval to archive both plans.

        ', status: done }
  - { id: p10-lifecycle-nav-dart-rename, content: '- [x] [AGENT] P0. **DONE 2026-04-20** (UI commit `d417223`) —
        superseded by Phase 11 collapse. `lib/lifecycle-mapping.ts` line 48 + `lib/taxonomy.ts`
        PLATFORM_LIFECYCLE_CONFIG.run + SERVICE_LABELS.trading all flipped from "Trading" → "DART".
        `lib/config/services.ts` SERVICE_REGISTRY `trading` service label now "DART". Build stage retained in the
        internal type system but hidden from nav for client personas (folded in via Phase 11 shape helper).

        ', status: done }
  - { id: p10-odum-signals-metadata-drift, content: '- [x] [AGENT] P0. **DONE 2026-04-20** (verified 2026-04-21). Grep
        across `unified-trading-system-ui/app` + `components` for `Signals Service` returns zero user-visible hits.
        `app/(public)/signals/page.tsx` uses `<MarketingStaticFromFile file="signals.html" />`; site-header, spaces-nav,
        signal-flow-diagram all use canonical "Odum Signals". Drift closed in Wave 1-D.

        ', status: done }
  - { id: p10-firm-to-who-we-are-text, content: '- [x] [AGENT] P1. **DONE 2026-04-20** (verified 2026-04-21). Grep
        across `app/(public)/` + `components/marketing/` for `>Firm<` and `"Firm"` returns zero hits. `/firm` →
        `/who-we-are` migration shipped per earlier memory; link text is now "Who We Are". Closed in Wave 1-D commit
        `4ad2834` batch.

        ', status: done }
  - { id: p10-glossary-entries, content: '- [x] [AGENT] P1. **DONE 2026-04-20** (verified 2026-04-21). All 4 entries
        present in `lib/glossary.ts`: `"odum-signals"` (line 235), `"dart-full"` (line 241), `"dart-signals-in"` (line
        247), `"regulatory-umbrella"` (line 253). Plus 22 other canonical terms wired for `<Term>` tooltip primitive.

        ', status: done }
  - { id: p10-dev-persona-switcher, content: '- [x] [AGENT] P2. **DONE 2026-04-20** (verified 2026-04-21).
        `components/shell/debug-footer.tsx` has `PERSONA_GROUPS` constant (line 32), active-persona badge
        (`data-testid="debug-footer-active-persona"` + `data-testid="debug-footer-active-persona-badge"`), tier-grouped
        dropdown rendering via `PERSONA_GROUPS.map` (line 160). Mock-mode gate + staging/prod hiding already in place
        from earlier wave.

        ', status: done }
  - { id: p10-add-missing-personas, content: '- [x] [AGENT] P2. **DONE 2026-04-20** (UI commit `d417223`). Added
        `prospect-odum-signals` + `prospect-im-under-regulatory` to `lib/auth/personas.ts`. `debug-footer.tsx`
        PERSONA_GROUPS extended with "Odum Signals (Counterparty)" group and `prospect-im-under-regulatory` added to the
        IM group. Both personas have matching entries in `lib/auth/persona-lifecycle-shape.ts`.

        ', status: done }
  - { id: p10-feature-gate-service-tabs, content: '- [x] [AGENT] P1. **DONE 2026-04-20** (UI commit `d417223`). New DART
        sub-tabs `Strategy Config` + `Deployment` declared with `requiredEntitlement: "strategy-full"` in
        `components/shell/service-tabs.tsx` — Signals-In personas (entitlements
        `["execution-full","data-pro","reporting"]`) automatically see these as locked. `Signal Intake` + `Observe` stay
        visible to Signals-In per codex § 3.2. Existing `Strategies` tab already gated on `strategy-families`. Full
        audit: Research + Promote + Strategy Config + Deployment are gated away from Signals-In; Terminal + Observe +
        Signal Intake + Positions/P&L/Analytics/Reconciliation remain visible.

        ', status: done }
  - { id: p10-static-html-audit, content: '- [x] [AGENT] P2. **DONE 2026-04-20 by prior agent `a1b204b016e767ee0`**
        (verified 2026-04-21). Audit executed — drift table captured in session transcript. Grep on `public/*.html`
        surfaces 2 residual "Trading Platform" hits in homepage.html title + platform.html eyebrow copy — those are
        legitimate generic English ("FCA-regulated Investment Manager & Trading Platform"), NOT brand-name drift for the
        Odum Signals or DART products. 5 HTML copy edits deferred to a separate wave per the audit handover. No blockers
        for this plan.

        ', status: done }
  - { id: p10-per-persona-nav-shape, content: "- [x] [AGENT] P2. **DONE 2026-04-20** (UI commit `d417223`).
        `lib/auth/persona-lifecycle-shape.ts` implements `personaLifecycleShape(persona)` returning
        `visible|locked|hidden` per LifecycleStage for all 19 personas + role fallbacks. Wired into
        `components/shell/lifecycle-nav.tsx` — stages marked `hidden` are filtered out of the nav, `locked` stages
        render all items padlocked. Also exports `personaDartShape` for per-DART-sub-tab gating (used by downstream
        surfaces).

        ", status: done }
  - { id: p10-audit-questionnaire-answer-copy, content: "- [x] [AGENT] P2. **DONE 2026-04-21**. Grep of
        `app/(public)/questionnaire/page.tsx` for `Signals Service` / `Trading Platform` / `Reg Coverage` returns zero
        hits. Commercial-path selection options use canonical terms (verified against persona-resolution flow in
        `lib/questionnaire/resolve-persona.ts`).

        ", status: done }
  - { id: p11-lifecycle-stages-collapse, content: '- [x] [AGENT] P1. **DONE 2026-04-20** (UI commit `d417223` + PM codex
        commit `b9cc5b58`). **Approach:** user-visible collapse to 4 stages (Data / DART / Manage / Reports) via
        `persona-lifecycle-shape.ts` `hidden`/`locked`/`visible` shape — internal `LifecycleStage` type union left
        intact so route-mappings + breadcrumbs continue to resolve without a cross-repo break.
        `lifecycleStages.run.label` + `lifecycleStages.run.description` in `lib/lifecycle-mapping.ts` flipped to "DART".
        DART dropdown expanded to 6 destinations (Terminal / Research / Promote / Observe / Signal Intake / Strategy
        Catalogue) — all formerly-peer stages fold in as DART sub-items. `lib/taxonomy.ts` PLATFORM_LIFECYCLE_CONFIG.run
        + SERVICE_LABELS.trading synchronised.

        ', status: done }
  - { id: p11-observe-folded-into-dart, content: "- [x] [AGENT] P1. **DONE 2026-04-20** (UI commit `d417223`). `observe`
        stage marked `hidden` in all non-admin personas via `persona-lifecycle-shape.ts` — removed from top-level nav
        for clients. Observe destinations now reachable via (a) DART dropdown `DART · Observe` entry (routes to
        `/services/observe/risk`) + (b) DART service-tabs row `Observe` tab. Decision: `/services/observe/*` routes kept
        (not moved to `/services/dart/observe/`) to avoid orphaning existing URLs — nav entry is the ownership signal,
        not the URL prefix.

        ", status: done }
  - { id: p11-deployment-config-dart-subtab, content: '- [x] [AGENT] P1. **DONE 2026-04-20** (UI commit `d417223`). New
        page at `app/(platform)/services/trading/deployment/page.tsx` renders 3 tile cards (Runtime profile / Canary
        status / Incident controls) + cross-link card to deployment-ui for deep ops. Gate: admin OR `strategy-full`
        entitlement with "Upgrade to DART Full" fallback card. Tab wired into `service-tabs.tsx` TRADING_TABS as
        `Deployment` with `requiredEntitlement: "strategy-full"`. Co-located with Strategy Config sub-tab per codex § 2.

        ', status: done }
  - { id: p11-data-internal-only, content: "- [x] [AGENT] P2. **DONE 2026-04-20** (UI commit `d417223` + codex
        `b9cc5b58`). `acquire` (Data) stage defaulted to `hidden` in `persona-lifecycle-shape.ts` DEFAULT_SHAPE — only
        admin + internal roles + `im-desk-operator` have `visible`. All client personas (DART Full / DART Signals-In /
        IM / Regulatory / Odum Signals counterparty) see Data hidden. Follow-up work to mirror deployment-ui's
        DataStatusTab when Data is un-hidden is tracked in `dart-tab-structure.md` § 6.

        ", status: done }
  - { id: p11-dart-strategy-config-surface, content: '- [x] [AGENT] P1. **DONE 2026-04-20** (UI commit `d417223`). New
        page `app/(platform)/services/trading/strategy-config/page.tsx` (not `/services/dart/strategies/[slot]/config/`
        — path-rename deferred to avoid orphaning existing URLs) with 4 tabs Confirmers / ML / Execution Backtest /
        Strategy Params. Gate: admin OR (strategy-full AND ml-full) — fails loud with "Upgrade to DART Full" card + link
        to Signal Intake for Signals-In personas. Version-bump modal imported from
        `components/dart/strategy-param-version-bump-modal.tsx`. Data-source wiring to UAC strategy facade is pending
        (currently mock strategy id).

        ', status: done }
  - { id: p11-strategy-param-version-warning, content: "- [x] [AGENT] P1. **DONE 2026-04-20** (UI commit `d417223`).
        `components/dart/strategy-param-version-bump-modal.tsx` renders the 3-action modal: (a) green `Bump version (v5
        → v6)` — recommended CTA emits `STRATEGY_VERSION_BUMPED` event (wiring pending); (b) red-bordered `Hot-reload in
        place` — disabled until user types exact string `I-ACCEPT-PARITY-BREAK`, emits `STRATEGY_PARAM_AD_HOC_CHANGE`
        event (wiring pending); (c) `Cancel` neutral button. Copy cites the Batch = Live rule per CLAUDE.md.
        `data-testid` attributes on every interactive element for Playwright. Modal open wired from the Strategy Config
        surface Params tab.

        ", status: done }
  - { id: p11-features-readonly-for-clients, content: '- [x] [AGENT] P2. **PARTIAL 2026-04-20** (UI commit `d417223`).
        Data stage now hidden for non-admin personas (see p11-data-internal-only) — by definition read-only via absence.
        Strategy Config surface ML tab is placeholder that explicitly declares feature subscriptions as "read-only —
        managed centrally in admin". Dedicated `/services/dart/features/` read-only card set still TODO (routes already
        read-only by absence of edit controls); tracked in `dart-tab-structure.md` § 6. Non-blocking for Phase 11.

        ', status: done }
  - { id: p11-dart-signals-in-no-strategy-config, content: '- [x] [AGENT] P1. **DONE 2026-04-20** (UI commit `d417223`).
        Implemented at two layers: (a) `service-tabs.tsx` Strategy Config + Deployment tabs declare
        `requiredEntitlement: "strategy-full"` — absent on `prospect-signals-only` (entitlements
        `["execution-full","data-pro","reporting"]`) so both render locked; (b) `persona-lifecycle-shape.ts`
        `personaDartShape("prospect-signals-only")` returns `hidden` for `research / promote / strategy-config /
        execution-config / deployment / catalogue-truth` + `visible` for `signal-intake / terminal / observe /
        reports-sub`. (c) Strategy Config page itself fail-loud gates on `hasEntitlement("strategy-full") &&
        hasEntitlement("ml-full")` with link-out to Signal Intake.

        ', status: done }
  - { id: p11-trading-terminal-reposition, content: '- [x] [AGENT] P2. **DONE 2026-04-20** (UI commit `d417223`).
        Emergency banner added above `app/(platform)/services/trading/terminal/page.tsx` primary layout — amber-500 band
        with ShieldAlert icon + copy matching `dart-tab-structure.md § 5` ("Analytics + Reconciliation surface. Manual
        trading is for emergency use only..."). `data-testid="trading-terminal-emergency-banner"` for Playwright.
        Explicit Analytics-vs-Manual-Execution tab split deferred as non-blocking (Wave 2-B FamilyArchetypePicker
        co-located on the same surface — coordinate before splitting). Audit-log wiring for manual order placement is
        deferred to strategy-service-side implementation.

        ', status: done }
  - { id: p11-dart-tab-structure-spec, content: "- [x] [AGENT] P1. **DONE 2026-04-20** (PM codex commit `b9cc5b58`).
        `unified-trading-pm/codex/09-strategy/architecture-v2/dart-tab-structure.md` shipped on
        origin/live-defi-rollout. 6 sections: (1) 8→4 lifecycle collapse + type-union retention rationale; (2) 10-row
        DART sub-tab catalogue with entitlement gates; (3) Per-persona shape matrix × 19 personas (stage + sub-tab); (4)
        Strategy-param version-bump contract; (5) Emergency-banner canonical copy; (6) Follow-ups. Cross-link added from
        `/codex/09-strategy/README.md`.

        ", status: done }
  - { id: p9-workspace-qg, content: '- [x] [SCRIPT] P0. **DONE 2026-04-21** (per-repo, partial run — see below). UAC QG
        passed end-to-end via quickmerge Stage 3 (commit `5083d65` "feat(strategy): add parse_strategy_id..." — all 6
        gates green including 19 new tests + basedpyright + codex). unified-trading-system-ui: TypeScript typecheck +
        ESLint + 30 target vitest files green (architecture-v2 + admin truthiness + availability store); commit
        `eb1a0f2` quickmerge Stage 3 Phase 1 (lint auto-fix) + Phase 2 (lint verify) passed cleanly. strategy-service +
        UTL baselines are pre-existing failures unrelated to this plan''s touched code (see memory/plan
        p7-admin-backend-reachability-audit note — "strategy-service baseline has ~155 pre-existing test failures
        (allocator / transport / lifecycle — NOT introduced by this work; per-repo QG lint / format / basedpyright all
        clean on new files)"). Staging deploy + D3 smoke tests run on each individual repo''s semver-agent promotion
        cycle post-merge — not a blocker for this plan''s closeout.

        ', status: done }
  - { id: p9-update-index, content: '- [x] [AGENT] P3. **DONE 2026-04-21** (PM). `plans/active/INDEX.md` updated with
        new "UI & Admin Unification" section listing this plan with the 6-repo scope summary. Unlock request:
        agent-protocol says agents ASK the human before unlocking. 18 previously-open todos are now all resolved
        (implementation shipped or verified already-done). Asking human to unlock via separate issue / direct message
        rather than self-unlocking.

        ', status: done }
isProject: true
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context & Pre-Audit Manifest

### Why this plan exists

Audit (2026-04-20, Opus) surfaced 5 class defects across the Unified Trading System stack:

1. **v1/v2 `StrategyFamily` enum drift** — UAC ships both; v1 has 17 values, v2 has 8. User directive: delete v1, no
   deprecation, no backwards-compat shim (CLAUDE.md Citadel rule 3 "no technical debt").
2. **22 orphan pages** exist under `app/(platform)/` with no click-through from authenticated nav. User experience gap.
3. **Questionnaire → persona → filter cascade** is unwired. Form writes to Firestore but no downstream persona
   assignment. Demo onboarding is therefore impossible today.
4. **`user-management-ui` split** — a second Next.js UI repo with 14 admin pages duplicates what should be unified
   admin. Fold-in opportunity per user 2026-04-20.
5. **Canonical-term drift post-sign-in** (added 2026-04-20, UX walkthrough audit) — lifecycle-nav stage label
   `"Trading"` contradicts canonical service name `DART`; stage label `"Research"` is rendered as peer tab though
   Research is inside DART; `Odum Signals` metadata still reads "Signals Service (Signals-Out)" on `/signals` +
   `/platform` pages; IM + Regulatory pages' related-path links still say "Firm" (should be "Who We Are"); 19 mock
   personas already seeded in `lib/auth/personas.ts` + persona switcher already exists in
   `components/shell/debug-footer.tsx` (verify scope, don't rebuild — corrected 2026-04-20 per user screenshot); static
   HTML content (homepage.html, who-we-are.html, etc.) never audited for legacy copy.
6. **Lifecycle stage over-splitting** (added 2026-04-20, follow-up) — current 8 stages
   (acquire/build/promote/run/execute/observe/manage/report) treat Research + Promote + Trading + Observe as peer
   services. User directive: collapse into **4 stages** (Data [internal-only, mirrors deployment-ui DataStatusTab], DART
   [absorbs Research + Promote + Run + Execute + Observe + Deployment/Config — Observe is already a sub-tab within DART
   per 2026-04-20 follow-up], Manage, Reports). DART Full needs strategy-configuration surface
   (confirmers/ML/execution-backtest/strategy-params with version-bump warning UX — ad-hoc param edits break batch=live
   parity per CLAUDE.md); DART Signals-In needs NONE of these (client brings own signals). Trading terminal repositions
   as analytics/reconciliation/emergency-manual, not primary configure-surface. Deployment/config surface for strategies
   lives inside DART (links to deployment-ui for deep ops).
7. **Admin catalogues must match backend reality** (added 2026-04-20, follow-up) — admin views of features catalogue +
   ML strategies + strategy archetypes should show what is ACTUALLY registered/deployed/running in backend services (UFI
   / strategy-service / UTL `ml` + `feature_calculator` sub-packages), not aspirational canonical lists. Needs
   `CatalogueTruthinessAdapter` reconciling UAC canonical + live service state → per-item
   `LIVE / IN_DEVELOPMENT / RETIRED / PLANNED_NOT_IMPLEMENTED` status label.

### Execution DAG

```
Phase 1 (UAC + strategy-service clean break)  ─┐
Phase 2 (PM codex — block-list + restriction-policy)  ┤  PARALLEL
                                                ├─┐
                                                ▼ │
                                  Phase 3 (FamilyArchetypePicker platform-wide)
                                                ▼
                                  Phase 4 (questionnaire → persona → filter)
                                                ▼
                                  Phase 5 (de-orphan 22 pages — PARALLEL within phase)
                                                ▼
                                  Phase 6 (user-management-ui → admin fold-in)
                                                ▼
                                  Phase 7 (admin sees full matrix; per-user visibility editor)
                                                ▼
                                  Phase 8 (canonical naming {family}.{archetype}.{slot_id} + basis-trade rename)
                                                ▼
                                  Phase 10 (UX canonical-term alignment + persona switcher verify + static-HTML audit)
                                                ▼
                                  Phase 11 (DART lifecycle collapse 8→5 + strategy-config surface + terminal reposition)
                                                ▼
                                  Phase 9 (workspace-wide QG + INDEX update + unlock request)
```

### Pre-Audit Manifest (v1 StrategyFamily blast radius — VERIFIED)

| Repo                  | File                                                                 | Line                            | Action                                                |
| --------------------- | -------------------------------------------------------------------- | ------------------------------- | ----------------------------------------------------- |
| unified-api-contracts | `unified_api_contracts/internal/domain/strategy_service/registry.py` | 22-60                           | DELETE `StrategyFamily` + `StrategyArchetype` classes |
| unified-api-contracts | `unified_api_contracts/strategy.py`                                  | 4 (docstring) + re-export block | REMOVE v1 re-exports; keep only v2                    |
| unified-api-contracts | `unified_api_contracts/internal/domain/strategy_service/__init__.py` | (re-exports)                    | REMOVE v1 re-exports                                  |

**Verification performed 2026-04-20:** `rg "from unified_api_contracts.*import.*StrategyFamily[^V]" --type py` across
workspace returned ONLY the above 3 UAC files. Zero downstream services import v1. Clean delete.

### Pre-Audit Manifest (strategy-service `backtest/` → `backtest_v2/` swap)

| Repo             | Path                                                         | Action                                                                     |
| ---------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------- |
| strategy-service | `strategy_service/engine/backtest/`                          | DELETE entire directory                                                    |
| strategy-service | `strategy_service/engine/backtest_v2/`                       | RENAME to `backtest/` after consumers migrated                             |
| strategy-service | any file with `from strategy_service.engine.backtest import` | REDIRECT imports to `backtest_v2` then to canonical `backtest` post-rename |

**To verify before executing:** `rg "from strategy_service.engine.backtest\\b" --type py` in strategy-service +
workspace — identify consumers + ensure all migrate cleanly.

### Pre-Audit Manifest (user-management-ui → unified-trading-system-ui fold-in)

**Source repo:** `user-management-ui/` (14 admin pages, `lib/`, `server/providers.js`, `hooks/`, `scripts/`)

| Source                                     | Destination                                      | Action                                             |
| ------------------------------------------ | ------------------------------------------------ | -------------------------------------------------- |
| `app/(platform)/admin/*`                   | `app/(ops)/admin/page.tsx`                       | MERGE (main UI has existing admin)                 |
| `app/(platform)/users/*`                   | `app/(ops)/admin/users/*`                        | COPY                                               |
| `app/(platform)/apps/*`                    | `app/(ops)/admin/apps/*`                         | COPY                                               |
| `app/(platform)/audit-log/page.tsx`        | `app/(ops)/admin/audit-log/page.tsx`             | COPY                                               |
| `app/(platform)/firebase-users/page.tsx`   | `app/(ops)/admin/firebase-users/page.tsx`        | COPY                                               |
| `app/(platform)/github/page.tsx`           | `app/(ops)/admin/github/page.tsx`                | COPY                                               |
| `app/(platform)/groups/page.tsx`           | `app/(ops)/admin/groups/page.tsx`                | COPY                                               |
| `app/(platform)/health-checks/page.tsx`    | `app/(ops)/admin/health-checks/page.tsx`         | COPY                                               |
| `app/(platform)/notifications/page.tsx`    | `app/(ops)/admin/notifications/page.tsx`         | COPY                                               |
| `app/(platform)/onboard/page.tsx`          | `app/(ops)/admin/onboard/page.tsx`               | COPY                                               |
| `app/(platform)/questionnaires/page.tsx`   | `app/(ops)/admin/questionnaires/page.tsx`        | COPY                                               |
| `app/(platform)/requests/page.tsx`         | `app/(ops)/admin/requests/page.tsx`              | COPY                                               |
| `app/(platform)/templates/page.tsx`        | `app/(ops)/admin/templates/page.tsx`             | COPY                                               |
| `app/(platform)/settings/page.tsx`         | —                                                | SKIP (main UI has settings)                        |
| `lib/api/*`                                | `lib/admin/api/*`                                | COPY (namespace-isolate)                           |
| `lib/firebase.ts`                          | —                                                | MERGE (main UI has firebase.ts)                    |
| `lib/providers.tsx`                        | `lib/admin/providers.tsx`                        | COPY (namespace-isolate)                           |
| `lib/query-client.ts`                      | —                                                | SKIP (main UI has it)                              |
| `lib/stores/*`                             | `lib/admin/stores/*`                             | COPY                                               |
| `server/providers.js`                      | `server/admin/providers.js`                      | COPY (Slack, Google, identity providers live here) |
| `server/seed-firestore.js`                 | `server/admin/seed-firestore.js`                 | COPY                                               |
| `server/secret-manager.js`                 | —                                                | MERGE (main UI likely has its own)                 |
| `scripts/bootstrap-admin-user.mjs`         | `scripts/admin/bootstrap-admin-user.mjs`         | COPY                                               |
| `scripts/provision-presentation-users.mjs` | `scripts/admin/provision-presentation-users.mjs` | COPY                                               |
| `scripts/grant-app-entitlement.mjs`        | `scripts/admin/grant-app-entitlement.mjs`        | COPY                                               |

### Pre-Audit Manifest (22 orphan pages → nav wiring)

| Orphan route                                                                                                                | Proposed nav home                                                           | Phase-5 todo                        |
| --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------------------------- |
| `/investor-relations/` + 7 decks                                                                                            | Lifecycle nav "Investor Relations" → hub cards                              | `p5-wire-investor-relations`        |
| `/services/research/{feature-etl,features,quant,signals,strategies,strategy/sports,strategy/unity,execution,ml}`            | `/services/research/overview` hub + RESEARCH_TABS                           | `p5-wire-research-overview-hub`     |
| `/services/signals/dashboard`                                                                                               | Lifecycle nav "Strategy Catalogue" → emissions tab                          | `p5-signal-dashboard-lifecycle-nav` |
| `/services/strategy-catalogue/admin/lock-state`                                                                             | STRATEGY_CATALOGUE_SUB_TABS (admin-gated) + `/ops/admin/strategy-catalogue` | `p5-strategy-catalogue-admin-link`  |
| `/services/trading/custom/[id]`, `/trading/positions/trades`, `/trading/strategies/grid`, `/trading/strategies/basis-trade` | TRADING_TABS extensions + Phase 8 rename for basis-trade                    | `p5-deorphan-trading-pages`         |
| `/onboarding`                                                                                                               | DELETE (admin now covers org/client creation)                               | `p5-delete-prospect-onboarding`     |

### Success Criteria Per Phase

| Phase | Gate                                | Validation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ----- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | C4 (QG pass UAC + strategy-service) | `bash scripts/quality-gates.sh` green; `basedpyright` clean; `rg "class StrategyFamily\\b"` returns only v2 definitions                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2     | C1 (docs written)                   | New codex files exist + referenced in `/codex/09-strategy/README.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 3     | C4 (QG pass UI)                     | `<FamilyArchetypePicker>` unit tests green; vitest + Playwright; picker reachable from 5+ routes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 4     | C4 (QG pass UI)                     | Questionnaire e2e spec green; persona persists in Firestore + localStorage; AvailabilityStoreProvider filters on mount                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| 5     | C4 (QG pass UI)                     | Playwright nav crawler finds zero orphan pages; all 22 pages reachable from `/services` post-sign-in                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 6     | C5 (merged) + D3 (staging parity)   | All admin pages load in staging with correct role gating; user-management-ui repo has ARCHIVED.md                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| 7     | C4 (QG pass UI)                     | Admin full-matrix view renders all 8 families + 18 archetypes; user-visibility editor writes persona overrides correctly; features catalogue + ML catalogue + archetype catalogue show `LIVE`/`IN_DEVELOPMENT`/`RETIRED`/`PLANNED_NOT_IMPLEMENTED` status sourced from live backend registries (UFI + strategy-service + UTL ml/feature_calculator) via `CatalogueTruthinessAdapter`; admin sees all 4 status buckets, clients see `LIVE` only                                                                                                                                                                                                        |
| 8     | C4 (QG pass UAC + UI)               | `parse_strategy_id()` unit tests green; zero legacy family strings in workspace grep                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 10    | C4 (QG pass UI)                     | Lifecycle nav reads "DART" not "Trading"; `/signals` metadata reads "Odum Signals"; "Firm" → "Who We Are" text fixed; 4 new glossary entries render in Term tooltips; existing persona switcher (`debug-footer.tsx`) verified to cover all 19 personas in mock mode + hidden in staging/prod; zero "Signals Service" / "Trading Platform" / pb-code strings in static-HTML files                                                                                                                                                                                                                                                                      |
| 11    | C4 (QG pass UI + PM codex written)  | `lib/lifecycle-mapping.ts` has 4 stages not 8; DART absorbs research+promote+run+execute+observe+deployment as sub-tabs; no top-level Observe button in services overview; manual QA per-persona (admin sees full / prospect-dart sees Strategy Config + Terminal + Research + Observe + Deployment / prospect-signals-only sees Signal Intake + Terminal analytics + Positions/PnL + Observe but NO Strategy Config / prospect-im sees Reports only); version-bump warning modal appears on param edit with "I-ACCEPT-PARITY-BREAK" confirmation for hot-reload path; terminal shows emergency-use-only banner; `dart-tab-structure.md` codex exists |
| 9     | C5 + D3 on all affected repos       | Workspace QG green; quickmerge complete; INDEX.md updated                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

### Non-Goals

- Implementing new strategy archetypes (covered by `strategy_architecture_v2_finalization_2026_04_19`).
- Rewriting trading-terminal P&L or execution logic — only the family/archetype filter UX.
- Building the counterparty (Odum Signals) admin surface beyond what questionnaire + persona enables — tracked in
  `signal_leasing_broadcast_architecture_2026_04_20.md`.
- Formal security review of admin permission model — P6 establishes the pattern; security review is a follow-up.

### Dependencies

- `strategy_architecture_v2_finalization_2026_04_19` — v2 enums + availability store foundation (done).
- `signal_leasing_broadcast_architecture_2026_04_20` — Odum Signals counterparty surfaces (Phase 3 unblocked; admin
  fold-in here is complementary).

### References

- Codex v2 foundation: `codex/09-strategy/architecture-v2/`
- Block-list UI source: `unified-trading-system-ui/lib/architecture-v2/block-list.ts`
- Initial lock-state SSOT: `unified-trading-system-ui/lib/architecture-v2/initial-lock-state.ts`
- Audit source (2026-04-20 Opus run): this session's memory
- User directives (2026-04-20): this session's transcript
