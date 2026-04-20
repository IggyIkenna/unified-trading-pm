---
name: ui-unification-v2-sanitisation-2026-04-20
overview:
  Kill v1 StrategyFamily + old backtest, fold user-management-ui into admin, wire questionnaire→persona→filter cascade,
  deorphan all unreachable pages under lifecycle nav, add Family/Archetype dropdowns platform-wide, canonicalise
  strategy naming.
type: mixed
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-20

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-system-ui
    code: C0
    deployment: D0
    business: none
  - repo: user-management-ui
    code: C0
    deployment: D0
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - strategy_architecture_v2_finalization_2026_04_19

todos:
  # ──────────────────────────────────────────────────────────────────────
  # PHASE 1 — Kill v1 StrategyFamily + old backtest engine (PARALLEL)
  # ──────────────────────────────────────────────────────────────────────
  - id: p1-kill-v1-strategyfamily-uac
    content: |
      - [ ] [HUMAN+AGENT] P0. **REVISED SCOPE 2026-04-20 after agent pre-audit surfaced true blast radius.** Original pre-audit grep `rg "from unified_api_contracts.*import.*StrategyFamily[^V]"` was too narrow — missed transitive `STRATEGY_REGISTRY` + `CLIENT_REGISTRY` consumers + `_DEFAULT_STRATEGIES` catalogue (55 v1-valued entries) + `StrategyDefinition` typed fields. Deleting v1 requires coordinated 4-repo change — needs human GO before dispatch. **Scope:** (1) UAC — delete `StrategyFamily` + `StrategyArchetype` enums + `StrategyDefinition` dataclass + `_DEFAULT_STRATEGIES` + `STRATEGY_REGISTRY` singleton + `CLIENT_REGISTRY` singleton from `unified_api_contracts/internal/domain/strategy_service/registry.py` + `__init__.py` + facade `strategy.py`. Provide v2 replacement registry exposing `resolve_name(strategy_id)`, `resolve_category(strategy_id)`, `resolve_family(strategy_id)`, `to_dict()` (either by promoting strategy-service `engine/strategies/v2/registry.py` to UAC OR by building Python SSOT from `architecture_v2/coverage`). (2) unified-trading-library — migrate `unified_trading_library/utils/record_enricher.py:16-22` to new v2 registry API. (3) unified-trading-api — migrate `unified_trading_api/routes/trading_analytics.py:8,373` — `/api/trading/strategies/catalog` endpoint needs v2 shape; UI consumer may need update. (4) unified-trading-pm — migrate `scripts/openapi/generate_ui_reference_data.py:538,540,554,556` — this writes `ui-reference-data.json` consumed by UI; schema change must land in lockstep. Dep-order commit: UAC → UTL → unified-trading-api → unified-trading-pm → UI regeneration. **V2→canonical rename DEFERRED** to new p1c todo — rename touches 30+ files across 5 repos (verified grep 2026-04-20), too big for this todo.
    status: blocked
    blocked_by: human-go
    note:
      "Blocked on human GO — 4-repo coordinated change, blast radius larger than original audit. Agent 2026-04-20
      pre-audit surfaced STRATEGY_REGISTRY + CLIENT_REGISTRY downstream consumers. Proposed path: dedicated 1-day agent
      session on 4 repos in dep order."
  - id: p1c-rename-v2-to-canonical
    content: |
      - [ ] [AGENT] P2. **Follow-up to p1-kill-v1-strategyfamily-uac.** After v1 is deleted + consumers migrated, rename `StrategyFamilyV2` → `StrategyFamily` + `StrategyArchetypeV2` → `StrategyArchetype` across all consumers. Blast radius (grep 2026-04-20): 30+ files across 5 repos — UAC (runtime + tests), strategy-service (5 files inc. portfolio_allocator + backtest tests), position-balance-monitor-service (1 test), unified-trading-system-ui (coverage.ts auto-generated + 4 component files), unified-trading-pm (codex + plans + propagation script `sync_archetype_capability_to_ui.py`). Commit order: UAC → strategy-service → PBMS → PM scripts → UI regeneration via `sync_archetype_capability_to_ui.py`. Coordinated wave, not standalone.
    status: todo
  - id: p1-delete-backtest-v1-strategy-service
    content: |
      - [ ] [AGENT] P0. Delete `strategy-service/strategy_service/engine/backtest/` directory. `backtest_v2/` exists alongside and is the replacement. Steps: (a) audit imports: `rg "from strategy_service.engine.backtest\\b" --type py` across workspace — redirect any consumer to `backtest_v2`; (b) after all consumers migrated, rename `backtest_v2/` → `backtest/` (drop the _v2 suffix so the module becomes canonical); (c) update test imports; (d) run `bash scripts/quality-gates.sh` in strategy-service. Rationale: per user 2026-04-20, "V2 exists, delete the other one to avoid confusion and technical debt" — clean break, no deprecation shim.
    status: todo
  - id: p1-qg-uac-strategy-service
    content: |
      - [ ] [SCRIPT] P0. Run `bash scripts/quality-gates.sh` in both unified-api-contracts AND strategy-service. Gate: Phase 2+ cannot start until both pass. Quickmerge each with `--agent` flag.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 2 — Block-list codex doc (PARALLEL with Phase 1; PM-only)
  # ──────────────────────────────────────────────────────────────────────
  - id: p2-block-list-codex-doc
    content: |
      - [x] [AGENT] P1. Create `unified-trading-pm/codex/09-strategy/architecture-v2/block-list.md`. SSOT for BL-1..BL-10 catalogue restrictions. **DONE 2026-04-20** (commits `b3b56bae` + `1686fcd5` on origin/live-defi-rollout) — 10 sections sourced verbatim from UI block-list.ts, ~1700 words, 5-step "how new entries get added" flow, canonical v2 enum names cited. QG green (148 pre-existing warnings, 0 errors).
    status: done
  - id: p2-restriction-policy-codex
    content: |
      - [x] [AGENT] P1. Add `codex/09-strategy/architecture-v2/restriction-policy.md` documenting: (i) per strategy family: allowed venues, allowed instrument types, allowed data types; (ii) how questionnaire answers map to which (family, archetype, venue, instrument_type) cells become visible; (iii) default visibility = `INVESTMENT_MANAGEMENT_RESERVED`, only `STAT_ARB_PAIRS_FIXED × CEFI × (spot|perp)` is `PUBLIC`. **DONE 2026-04-20** (same commits as p2-block-list) — 5 sections, ~2100 words, 6-axis questionnaire mapping table, per-family venues derived from coverage.ts representativeVenueIds, 5 IM-live cells with maturity. `codex/09-strategy/README.md` now links both new files under "Architecture v2 — Deep docs".
    status: done

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 3 — FamilyArchetypePicker component + platform-wide wiring
  # ──────────────────────────────────────────────────────────────────────
  - id: p3-build-picker-component
    content: |
      - [ ] [AGENT] P1. Build reusable `<FamilyArchetypePicker>` component at `unified-trading-system-ui/components/architecture-v2/family-archetype-picker.tsx`. Props: `{value: {family?, archetype?}, onChange, showStrategyIdDropdown?, availabilityFilter?: 'allowed'|'all'}`. UI: cascading selects — Family (8 options from `STRATEGY_FAMILIES`) → Archetype (18 options filtered to family) → optional Strategy ID dropdown (filtered by availability registry). Must respect current persona visibility filter (imports from `AvailabilityStoreProvider`). Include `data-testid` on each select for Playwright. Unit tests in `tests/unit/components/architecture-v2/family-archetype-picker.test.tsx`.
    status: todo
  - id: p3-wire-picker-trading-terminal
    content: |
      - [ ] [AGENT] P1. Wire `<FamilyArchetypePicker>` into `app/(platform)/services/trading/terminal/page.tsx`. Replace any generic "strategies list" with family→archetype→strategies filter. Persist selection in `lib/stores/global-scope-store.ts` (extend state with `{strategyFamily, strategyArchetype}` keys; add setters).
    status: todo
  - id: p3-wire-picker-catalogue-filter
    content: |
      - [ ] [AGENT] P1. Wire picker into `/services/strategy-catalogue/coverage/` top-of-page filter. Selecting family+archetype should scope the matrix to matching cells.
    status: todo
  - id: p3-wire-picker-research-pages
    content: |
      - [ ] [AGENT] P2. Wire picker into `/services/research/strategies/page.tsx` + `/services/research/overview/page.tsx` — replace any generic strategy list with family/archetype scoped view.
    status: todo
  - id: p3-wire-picker-signals-dashboard
    content: |
      - [ ] [AGENT] P2. Wire picker into `/services/signals/dashboard/page.tsx` for signal emissions filter (so operators can see only Basis signals, only ML Directional signals, etc.).
    status: todo
  - id: p3-wire-picker-orders-positions
    content: |
      - [ ] [AGENT] P2. Audit `/services/trading/orders` + `/services/trading/positions` + `/services/trading/pnl` — wire picker where a generic strategy dimension is exposed.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 4 — Questionnaire → persona → filter cascade
  # ──────────────────────────────────────────────────────────────────────
  - id: p4-questionnaire-persona-resolver
    content: |
      - [ ] [AGENT] P1. Implement questionnaire → persona mapping. Current state: `app/(public)/questionnaire/page.tsx` writes response to Firestore but never stamps the user with a restriction profile. Steps: (a) add `lib/questionnaire/resolve-persona.ts` that takes a `QuestionnaireResponse` and returns a `RestrictionProfile` (logic: answer="I want DART Signals-In" → `prospect-dart`; "I want IM" → `prospect-im`; "I want Regulatory Umbrella" → `prospect-regulatory`; otherwise → `prospect-generic`). (b) On submit success, call resolver, persist persona in Firestore user doc + localStorage `odum-persona/v1`. (c) `AvailabilityStoreProvider` reads persona on mount and seeds initial filter. (d) If user hits `/services` without completing questionnaire → redirect to `/questionnaire`. (e) Persona rules mirror the codex restriction-policy.md matrix from P2.
    status: todo
  - id: p4-persona-admin-override
    content: |
      - [ ] [AGENT] P1. Admin can override a user's persona from the admin UI (see Phase 6 `/admin/users/[id]` page). When admin sets persona, user sees the targeted demo view on next login. Rule: admin cannot grant higher than `INVESTMENT_MANAGEMENT_RESERVED` without explicit lock-state change.
    status: todo
  - id: p4-questionnaire-e2e-spec
    content: |
      - [ ] [AGENT] P2. Add Playwright e2e spec `tests/e2e/playbooks/questionnaire-persona.spec.ts`. Scenario: (1) fill questionnaire as "DART-only prospect", (2) land on `/services`, (3) assert only DART-related services + strategy slots visible, (4) assert IM-reserved slots hidden.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 5 — De-orphan all unreachable pages (PARALLEL within phase)
  # ──────────────────────────────────────────────────────────────────────
  - id: p5-wire-investor-relations
    content: |
      - [ ] [AGENT] P2. Wire 7 Investor Relations deck pages from hub. Edit `app/(platform)/investor-relations/page.tsx` to render card grid linking to: `/board-presentation`, `/disaster-recovery`, `/investment-presentation`, `/plan-presentation`, `/platform-presentation`, `/regulatory-presentation`, `/site-navigation`. Add lifecycle nav entry "Investor Relations" in `components/shell/lifecycle-nav.tsx` so `/investor-relations` is reachable from the authenticated nav. User 2026-04-20: "fold all of the orphaned Investor Relations decks into /investor-relations for now, I'll clean it up later" — don't over-polish.
    status: todo
  - id: p5-wire-research-overview-hub
    content: |
      - [ ] [AGENT] P2. Make `/services/research/overview/page.tsx` the hub for all research orphans. Render link cards to: `/services/research/feature-etl`, `/services/research/features`, `/services/research/quant`, `/services/research/signals`, `/services/research/strategies`, `/services/research/strategy/sports`, `/services/research/strategy/unity`, `/services/research/execution`, `/services/research/ml`. Extend `RESEARCH_TABS` in `components/shell/service-tabs.tsx` so each is reachable from the in-service tab bar.
    status: todo
  - id: p5-signal-dashboard-lifecycle-nav
    content: |
      - [ ] [AGENT] P2. Move `/services/signals/dashboard` into lifecycle nav under "Strategy Catalogue" group (user 2026-04-20: signals overview = strategy catalogue). Add secondary tab "Emissions" on the catalogue landing that deep-links to `/services/signals/dashboard`. Alternatively, rename the route to `/services/strategy-catalogue/signals-out/` if cleaner — discuss in PR.
    status: todo
  - id: p5-strategy-catalogue-admin-link
    content: |
      - [ ] [AGENT] P2. Link `/services/strategy-catalogue/admin/lock-state` from admin area (see Phase 6). Also add to `STRATEGY_CATALOGUE_SUB_TABS` as an admin-only tab gated by `user?.role === "admin"`.
    status: todo
  - id: p5-deorphan-trading-pages
    content: |
      - [ ] [AGENT] P2. De-orphan trading pages: (a) `/services/trading/custom/[id]` — link from trading strategies list as "custom strategies" tab; (b) `/services/trading/positions/trades` — link from positions page detail; (c) `/services/trading/strategies/grid` — decision: is grid an archetype or UX gimmick? If archetype-like, map to `MARKET_MAKING_CONTINUOUS`; if UX, link from strategies hub; (d) `/services/trading/strategies/basis-trade` — rename + migrate per Phase 8 (this is a v1-family artifact).
    status: todo
  - id: p5-delete-prospect-onboarding
    content: |
      - [ ] [AGENT] P3. Delete `app/(platform)/onboarding/page.tsx` route. User 2026-04-20 (follow-up): "I think we should delete it" — admin UI now handles org/client creation, prospect onboarding is covered by `/questionnaire` → persona flow. No HUMAN confirmation needed. Grep `rg "href=\"/onboarding\"" unified-trading-system-ui` and remove every link reference. Grep `rg "/onboarding" unified-trading-system-ui/app` to confirm no downstream router uses the slug.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 6 — Fold user-management-ui into unified-trading-system-ui admin
  # ──────────────────────────────────────────────────────────────────────
  - id: p6-migration-manifest
    content: |
      - [ ] [AGENT] P1. Build migration manifest. Source: `user-management-ui/app/(platform)/{admin,apps,audit-log,firebase-users,github,groups,health-checks,notifications,onboard,questionnaires,requests,settings,templates,users}` + `user-management-ui/lib/{api,firebase,providers,query-client,stores,utils}` + `user-management-ui/server/{providers.js,seed-firestore.js,secret-manager.js}` + `user-management-ui/hooks/*` + `user-management-ui/scripts/*`. Destination: `unified-trading-system-ui/app/(ops)/admin/{subroute}/` + `lib/admin/*` + `server/admin/*` (new subdirectories). Manifest entries: src path → dst path → action (copy/merge/skip). Merge decisions: `settings/` skip (main UI already has it); `admin/` merge into existing `(ops)/admin/page.tsx`; all others copy.
    status: todo
  - id: p6-migrate-pages
    content: |
      - [ ] [AGENT] P1. Execute page migration per manifest. New structure: `(ops)/admin/{users,users/[id]/{modify,offboard},apps,apps/[id],audit-log,firebase-users,github,groups,health-checks,notifications,onboard,questionnaires,requests,templates}`. Update all `<Link href=...>` references. Preserve Slack / Google / identity-provider integrations from `user-management-ui/server/providers.js` — move to `unified-trading-system-ui/server/admin/providers.js`.
    status: todo
  - id: p6-admin-nav-wiring
    content: |
      - [ ] [AGENT] P1. Extend `ADMIN_TABS` in `components/shell/service-tabs.tsx` to include new admin subroutes (Users, Apps, Audit Log, Firebase Users, GitHub, Groups, Health Checks, Notifications, Onboard, Questionnaires, Requests, Templates). Gate entire admin area with `user?.role === "admin"` check at layout level — no per-page gates.
    status: todo
  - id: p6-permission-model-alignment
    content: |
      - [ ] [AGENT] P1. Align admin permission model with codex playbooks. Current state: `user?.role === "admin"` binary check. Target: role-based plus specific-admin allowlist for destructive operations (e.g., granting admin role itself, creating organisations). Implement: (a) `lib/auth/admin-permissions.ts` defining permissions set (`admin:grant_role`, `admin:create_org`, `admin:lock_strategy`, `admin:impersonate`, …); (b) Firebase custom claim `admin_permissions: string[]` alongside existing `role`; (c) per-action check `hasAdminPermission(user, "admin:grant_role")`. Bootstrap: ikenna@odum-research.com + femi@odum-research.com seed script grants all permissions. Document in codex `14-playbooks/cross-cutting/admin-permissions.md`.
    status: todo
  - id: p6-admin-sees-full-catalogue
    content: |
      - [ ] [AGENT] P1. Admin catalogue view (`/ops/admin/strategy-catalogue/`) must show the full (family × archetype × category × instrument-type) matrix with representative strategy IDs + representative venues per cell — regardless of any persona filter. This is the "admin sees everything" view. Customer visibility remains persona-gated downstream. User 2026-04-20: "When we're in admin, we should see all the possible strategy families and archetypes, with example strategy IDs for each, for some representative list of venues for those strategies."
    status: todo
  - id: p6-archive-user-management-ui
    content: |
      - [ ] [HUMAN] P2. Archive `user-management-ui` repo after all downstream consumers migrated. Steps: (a) verify no CI/CD workflow references it; (b) confirm no other service imports from it; (c) add `ARCHIVED.md` at repo root; (d) GitHub archive the repo; (e) remove from `workspace-manifest.json` + `.cursor` workspace configs; (f) remove from `unified-trading-system-repos.code-workspace`. Blocked until p6-migrate-pages + p6-admin-nav-wiring + p6-permission-model-alignment are C5.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 7 — Admin reveals all families/archetypes/example strategy IDs
  # ──────────────────────────────────────────────────────────────────────
  - id: p7-admin-full-catalogue-view
    content: |
      - [ ] [AGENT] P2. In admin `/ops/admin/strategy-catalogue/overview/page.tsx` render per-family card grid: {Family name, 8 total} × {archetypes under it, up to 5} × {representative strategy IDs, up to 3 per archetype} × {representative venues per strategy}. Data source: UAC strategy registry + availability store. Admin bypass flag on AvailabilityStoreProvider to return full matrix regardless of persona.
    status: todo
  - id: p7-admin-user-visibility-editor
    content: |
      - [ ] [AGENT] P2. In `/ops/admin/users/[id]/visibility/page.tsx` render the user's effective visibility: which (family × archetype × category × instrument_type × venue) cells they can see based on their current persona + any admin overrides. Editor: admin can pin/unpin specific slots for this user (persona override). Audit-log entry on every change.
    status: todo
  - id: p7-admin-catalogue-backend-truthfulness
    content: |
      - [ ] [AGENT] P1. Admin catalogues must match backend reality, not aspiration. User 2026-04-20 (follow-up): "The type of the features catalogue, the machine learning strategies available as admin (for example, which should be all-encompassing), should also make sense versus what is actually available". Scope: three admin catalogue surfaces must reflect what is ACTUALLY registered / deployed / running in the backend. **(1) Features catalogue** (`/ops/admin/features/` or similar) — source: unified-features-interface (UFI) + feature-calculator registry in UTL; mark each feature as `LIVE` / `IN_DEVELOPMENT` / `RETIRED` / `PLANNED_NOT_IMPLEMENTED`; admin sees all four buckets, clients see LIVE only. **(2) ML strategies catalogue** (`/ops/admin/ml-models/` or `/ops/admin/strategies/ml/`) — source: strategy-service ML model registry + `unified_trading_library.ml` sub-package; mark status + last-training-timestamp + deployment health. **(3) Strategy archetypes catalogue** (already covered by p6-admin-sees-full-catalogue + p7-admin-full-catalogue-view) — extend to pull STATUS from live strategy-service registry, not just UAC canonical definitions: an archetype declared in UAC but never deployed to strategy-service is `PLANNED_NOT_IMPLEMENTED`. Implementation: add a `CatalogueTruthinessAdapter` in `lib/admin/truthiness.ts` that reconciles UAC/UFI/UTL canonical lists against live service state (via admin-API calls) and produces status labels. If backend is unreachable in mock mode, fall back to seeded mock state (admin sees `(mock) STATUS` with clear labelling).
    status: todo
  - id: p7-admin-backend-reachability-audit
    content: |
      - [ ] [AGENT] P2. Pre-requisite for p7-admin-catalogue-backend-truthfulness. Audit what admin-API endpoints exist today for listing live features / ML models / registered strategy archetypes. Target services: unified-features-interface (UFI), strategy-service (for ML + archetype registry), `unified_trading_library.feature_calculator` / `unified_trading_library.ml`. If read-only list endpoints are missing, add them (lightweight `GET /api/v1/registry/features`, `GET /api/v1/registry/ml-models`, `GET /api/v1/registry/archetypes` returning `{name, status, last_updated, deployment_health}`). Admin UI then consumes these. Gate: endpoints must be admin-role-only via existing auth middleware.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 8 — Strategy naming canonicalisation
  # ──────────────────────────────────────────────────────────────────────
  - id: p8-canonical-naming-scheme
    content: |
      - [ ] [AGENT] P2. Codify canonical strategy naming in UAC: `{FAMILY}.{ARCHETYPE}.{strategy_id}` where FAMILY is one of the 8 v2 values, ARCHETYPE is one of the 18 v2 values, strategy_id is the specific run config (e.g., `CARRY_AND_YIELD.CARRY_BASIS_PERP.eth-perp-binance-10m`). Add to codex `09-strategy/architecture-v2/naming-convention.md`. Validate in UAC: `parse_strategy_id(fq_id) -> (family, archetype, slot_id)`.
    status: todo
  - id: p8-rename-basis-trade-page
    content: |
      - [ ] [AGENT] P2. Rename `/services/trading/strategies/basis-trade/` → `/services/trading/strategies/carry-basis/` (or similar v2 name). Update all `<Link>` refs. Map the page's internal strategy IDs to canonical `CARRY_AND_YIELD.CARRY_BASIS_PERP.{id}` format.
    status: todo
  - id: p8-audit-legacy-family-strings
    content: |
      - [ ] [AGENT] P2. Grep across UI + services for any legacy lowercase family strings like `basis-trade`, `mean-reversion`, `sports-arb`, `prediction-ml` used as route slugs, filter values, or display labels. Migrate to v2 names. This ensures the strategy surface is fully aligned with the v2 enum.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 10 — UX canonical-term alignment + dev persona switcher + static-HTML audit
  # ──────────────────────────────────────────────────────────────────────
  - id: p10-lifecycle-nav-dart-rename
    content: |
      - [ ] [AGENT] P0. Rename lifecycle-nav stages to canonical terms. Edit `unified-trading-system-ui/lib/lifecycle-mapping.ts` line 49: `label: "Trading"` → `label: "DART"`; update description to `"Trading, research, execution, analytics — the full DART platform"`. Decision for the `build` stage (line 37, currently `label: "Research"`): two options — (a) rename to `label: "Build"` keeping Research as a description phrase ("Features, ML, and strategy research — inside DART"), or (b) collapse `build` + `run` into a single `dart` stage. Default recommendation: (a) keep the stage separation since lifecycle nav uses stages not services; the single "DART" stage label applies at run stage only; research-stage sub-tabs remain reachable under Build. User 2026-04-20: "Calling something 'trading' when it should be 'DART' doesn't make much sense". Propagate label change to every cascading consumer: breadcrumbs, service hub H1s, tab bar titles. After edit, grep `rg "\"Trading\"" unified-trading-system-ui/lib` + `rg "label: \"Trading\"" unified-trading-system-ui/components` to catch any other drift.
    status: todo
  - id: p10-odum-signals-metadata-drift
    content: |
      - [ ] [AGENT] P0. Fix "Signals Service (Signals-Out)" → "Odum Signals" drift at user-visible surfaces. Edit (a) `app/(public)/signals/page.tsx` line 7 metadata `title`; (b) `app/(public)/platform/page.tsx` line 142 related-paths link text. Site header, spaces-nav, and signal-flow-diagram already use canonical "Odum Signals" — verify via grep `rg "Signals Service" unified-trading-system-ui --type tsx` and fix every user-visible hit. Internal comments, codebase identifiers, and the phrase "Signals-Out" as a directional descriptor in diagrams may remain. User 2026-04-20 voice correction: "Autumn signals we should call it Autumn signals [= Odum Signals] also in the life cycle overview".
    status: todo
  - id: p10-firm-to-who-we-are-text
    content: |
      - [ ] [AGENT] P1. Fix stale "Firm" link text at `app/(public)/investment-management/page.tsx` line 233 and `app/(public)/regulatory/page.tsx` line 207. Both hrefs correctly point to `/who-we-are` but link text still reads "Firm" (legacy pre-rename). Change text to "Who We Are". Grep-sweep for any other `>Firm<` or `"Firm"` string label in `app/(public)/` and `components/marketing/`.
    status: todo
  - id: p10-glossary-entries
    content: |
      - [ ] [AGENT] P1. Add missing glossary entries to `unified-trading-system-ui/lib/glossary.ts`: (a) `odum-signals` — "Odum's outbound signal-leasing service. Odum-generated trading signals delivered to counterparty webhook or REST-pull endpoints under HMAC-signed envelopes."; (b) `dart-full` — "DART Full: unrestricted platform access — research, ML, strategy promotion, execution, analytics, reporting."; (c) `dart-signals-in` — "DART Signals-In: restricted DART tier. Client provides trading instructions via signal webhooks; Odum executes. No research, ML, or strategy-promote access."; (d) `regulatory-umbrella` (verify absence first) — "Odum's FCA-regulated wrapper allowing clients to operate regulated activity under Odum's permissions (AIFM, AR, MiFID II coverage)."; (e) `investment-management` alias to existing `im` entry so `<Term id="investment-management">` works. Confirm `<Term>` primitive renders hover tooltips for all new entries.
    status: todo
  - id: p10-dev-persona-switcher
    content: |
      - [ ] [AGENT] P2. **Verify + extend existing persona switcher** (not build). User 2026-04-20 (follow-up w/ screenshot): a "Switch Persona" dropdown already exists in mock mode — confirmed to live in `components/shell/debug-footer.tsx`. Tasks: (a) audit `debug-footer.tsx` to confirm it lists all 19 personas grouped by tier (Admin / Internal / DART Full / DART Signals-In / IM Pooled / IM SMA / Regulatory / Counterparty / DeFi-demo); (b) confirm visibility gate — switcher must render ONLY when mock-auth active, NEVER in staging/prod builds (user: "Staging doesn't need that, because in staging we're going to get people off of Firebase"); (c) confirm on-select updates AvailabilityStoreProvider + re-renders lifecycle nav per persona-lifecycle-shape (p10-per-persona-nav-shape); (d) if grouping/labelling is missing, extend with tier-grouped menu + active-persona badge (email + tier). Not in scope: building a new component — one exists.
    status: todo
  - id: p10-add-missing-personas
    content: |
      - [ ] [AGENT] P2. Add any missing personas to `lib/auth/personas.ts` for complete 5-path coverage: (a) `prospect-odum-signals` (counterparty receiving outbound signals — entitlements: `["execution-full","reporting"]`, role: `client`); (b) `prospect-im-under-regulatory` (IM client running under Regulatory Umbrella — different entitlements than direct IM, represents the hybrid case). Verify existing personas cover: DART Full client (✓ prospect-dart), DART Signals-In client (✓ prospect-signals-only), IM SMA client (✓ prospect-im-sma), IM Pooled client (✓ prospect-im-pooled), Regulatory Umbrella client (✓ prospect-regulatory), Admin (✓ admin@odum.internal), Internal trader (✓ trader@odum.internal), DeFi demo (✓ patrick@bankelysium.com). Commit: "feat(auth): add odum-signals-counterparty + im-under-regulatory personas for complete 5-path coverage".
    status: todo
  - id: p10-feature-gate-service-tabs
    content: |
      - [ ] [AGENT] P1. Audit and fix feature-gating in `components/shell/service-tabs.tsx` so DART Signals-In personas do NOT see tabs requiring DART Full entitlements. Specifically the "Strategies" tab (line ~393), any Research-sub tabs, any ML/Promote tabs. Rule: tab is visible iff `persona.entitlements` contains ALL entitlements declared by the tab's `requiredEntitlements` field. Add `requiredEntitlements` field to tab config if missing. Verification: with persona switcher (p10-dev-persona-switcher), switch to `ops@defihf.com` (prospect-signals-only) and confirm Strategies/Research/Promote tabs are hidden. Switch to `sarah.quant@examplehedge.com` (prospect-dart) and confirm all tabs visible.
    status: todo
  - id: p10-static-html-audit
    content: |
      - [ ] [AGENT] P2. Audit static HTML files rendered via `<MarketingStaticFromFile>`. Find all static HTML sources: `rg "MarketingStaticFromFile" unified-trading-system-ui --type tsx -l` → for each file prop, read the corresponding HTML (likely in `unified-trading-system-ui/public/static-marketing/` or `content/` — confirm path). Audit every HTML file for: (a) legacy terms ("Signals Service" → "Odum Signals", "Trading Platform" → "DART", "Firm" → "Who We Are"); (b) POD affiliate naming (must say "regulated affiliate" publicly, POD is internal-only per memory); (c) pricing leaks (any £3k/£4k/30-35% figures are INTERNAL); (d) pb-code references (`pb3a`, `pb-*`); (e) company brand — "Odum" / "Odum Research" canonical, never "Autumn" (which was only a voice-transcription artifact). Flag findings in a companion HTML-drift report or fix inline. Scope: homepage.html, who-we-are.html, and all other `content/*.html` files.
    status: todo
  - id: p10-per-persona-nav-shape
    content: |
      - [ ] [AGENT] P2. Implement per-persona lifecycle-nav visibility filtering. Each of the 8 lifecycle stages (Data/Build/Promote/DART/Execute/Observe/Manage/Reports) should be either VISIBLE, LOCKED (rendered with padlock + "Upgrade to unlock" hover), or HIDDEN per persona tier. Target shapes (per audit 2026-04-20): Admin = all visible; DART Full client = Data+Build+Promote+DART+Observe+Reports visible, Manage LOCKED; DART Signals-In client = Data+DART (restricted)+Observe+Reports visible, Build+Promote+Manage LOCKED; IM client = Data+Observe+Reports visible, others LOCKED; Regulatory Umbrella client = Data+Observe+Manage+Reports visible, DART+Build+Promote LOCKED; Odum Signals counterparty = separate shell (not standard lifecycle nav — signals-only dashboard). Implement in `components/shell/lifecycle-nav.tsx` with `personaLifecycleShape(persona): {[stageId]: "visible" | "locked" | "hidden"}` helper in `lib/auth/persona-lifecycle-shape.ts`. User 2026-04-20 target-nav map in audit report.
    status: todo
  - id: p10-audit-questionnaire-answer-copy
    content: |
      - [ ] [AGENT] P2. Quick audit of `app/(public)/questionnaire/page.tsx` answer options. Verify all commercial-path selection options use canonical terms: "DART Full", "DART Signals-In", "Odum Signals", "Investment Management", "Regulatory Umbrella". Flag any legacy synonyms (e.g., "Signals Service", "Trading Platform", "Reg Coverage"). This is the entry point for persona resolution (see p4-questionnaire-persona-resolver) — incorrect labels here cascade into wrong persona assignments.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 11 — DART lifecycle collapse + strategy configuration surface
  # ──────────────────────────────────────────────────────────────────────
  - id: p11-lifecycle-stages-collapse
    content: |
      - [ ] [AGENT] P1. Collapse lifecycle stages 8 → 4. User 2026-04-20 (follow-up): "Research should be folded into DART. I agree there's no point calling it a different thing, research and promote". Follow-up 2 (same day): "Observe shouldn't remain separate service button in the services overview... gut kind of tells me to wrap it into DART, to be honest. Since Observe is already a tab within DART anyway" + "deployment and such, that's probably where you want to be able to set your strategy config and execution config for DART". Current 8 stages: `acquire (Data) / build (Research) / promote (Promote) / run (Trading) / execute (Execute) / observe (Observe) / manage (Manage) / report (Reports)`. **New 4 stages**: `Data` (internal-only; see p11-data-internal-only), `DART` (absorbs Research + Promote + Run + Execute + **Observe** + **Deployment/Config** — the single umbrella for everything strategy + execution + monitoring + config), `Manage`, `Reports`. Implementation: edit `lib/lifecycle-mapping.ts` stage definitions; migrate all `acquire`/`build`/`promote`/`run`/`execute`/`observe` consumers to the new 4-stage vocab. Sub-tabs INSIDE DART: Research / Promote / Terminal / Execute / Backtest / Strategy Config / Execution Config / Deployment / **Observe (risk/alerts/health/PnL live)** / Signal Intake — so NO functionality is orphaned. Per user: "amalgamation of all the functionality". Supersedes earlier p10-lifecycle-nav-dart-rename Build-stage rename decision.
    status: todo
  - id: p11-observe-folded-into-dart
    content: |
      - [ ] [AGENT] P1. Explicit removal of Observe from top-level services overview + placement as DART sub-tab. Tasks: (a) remove "Observe" from lifecycle-nav top bar in `components/shell/lifecycle-nav.tsx`; (b) remove from `service-tabs.tsx` as a peer service; (c) add under DART sub-tabs (alongside Research/Promote/Terminal/etc.) — covers risk monitoring, alerts, health, live PnL-watch; (d) ensure all existing `/services/observe/*` routes are either renamed under `/services/dart/observe/*` OR kept at `/services/observe/*` with the nav entry moved (prefer rename to reflect DART ownership — avoids the user's "orphaned page" concern). Grep `rg "services/observe" unified-trading-system-ui` to find all link refs and update them.
    status: todo
  - id: p11-deployment-config-dart-subtab
    content: |
      - [ ] [AGENT] P1. Deployment / config surface lives INSIDE DART, not as separate nav. User 2026-04-20: "that's probably where you want to be able to set your strategy config and execution config for DART". Tasks: (a) add DART sub-tab `Deployment` pointing to `/services/dart/deployment/` — renders a lightweight view of per-strategy runtime config (runtime_profile, chaos controller, kill-switch state) **without duplicating deployment-ui**; (b) embed link to full deployment-ui for deep operations (iframe OR external-link card per shell policy — keep it out of scope to rebuild); (c) ensure p11-dart-strategy-config-surface (Strategy Params / Confirmers / ML / Execution Backtest) is co-located with this Deployment sub-tab so "configure strategy" and "configure deployment" live together inside DART. Gated by admin OR `strategy-full` entitlement.
    status: todo
  - id: p11-data-internal-only
    content: |
      - [ ] [AGENT] P2. Mark `Data` lifecycle stage as INTERNAL-ONLY for now. User 2026-04-20: "data can remain as a lifecycle service, but it's probably not even going to be exposed to the public for now. It's effectively going to end up becoming what the Data Status tab in the deployment UI is anyway, which is quite a big ship. Since the appointment UI [deployment-ui] is working, we don't need to necessarily do that now anyway." Tasks: (a) gate Data stage visibility to `admin` + `internal` roles only in `persona-lifecycle-shape` (p10-per-persona-nav-shape); (b) add code comment in `lib/lifecycle-mapping.ts` referencing the canonical source `deployment-ui/src/components/DataStatusTab.tsx` + `DataStatusDrilldown.tsx` — when Data stage is un-hidden for clients, it should mirror deployment-ui's approach rather than rebuild; (c) no UI work this phase beyond hiding stage from non-admin personas. Tracks as follow-up; not a blocker for Phase 11.
    status: todo
  - id: p11-dart-strategy-config-surface
    content: |
      - [ ] [AGENT] P1. Build DART Strategy Configuration surface. User 2026-04-20: DART Full users must configure across all areas — "confirmers, that they can run a strategy, machine learning, and execution backtest if they have those rights". Scope: under `/services/dart/strategies/[slot]/config/` (new route group after lifecycle rename), render tabs: **Confirmers** (pre-trade sanity checks), **ML** (model selection + retrain schedule + feature subscriptions READ-ONLY — see p11-features-readonly), **Execution Backtest** (matching-engine simulation config), **Strategy Params** (live strategy parameters with version-bump warning UX — see p11-strategy-param-version-warning). Entitlement gate: visible iff persona has `strategy-full` + `ml-full`. Data source: UAC strategy facade + strategy-service live config. Fail-loud if persona lacks required entitlement ("Upgrade to DART Full to configure strategies" card). Cross-reference codex `09-strategy/architecture-v2/` for which configs are valid per archetype.
    status: todo
  - id: p11-strategy-param-version-warning
    content: |
      - [ ] [AGENT] P1. Version-bump warning UX on strategy parameter changes. User 2026-04-20: "it should come with a warning, because technically they should only really change strategy parameters if you're changing the strategy version, so it should go from, like, v5 to v6 or whatever, rather than just ad-hoc changing it. Otherwise you're no longer able to match backtest with live, which defeats a lot of the point." Implementation: when a user edits a live strategy parameter in the config surface, show a modal with three actions: **(a) Bump version (v5 → v6)** — recommended, preserves backtest/live parity, opens a version-dialog; **(b) Hot-reload in place** — red-bordered "ad-hoc change, breaks backtest/live parity" warning, requires typing "I-ACCEPT-PARITY-BREAK" to confirm; **(c) Cancel**. Config hot-reload already works (UTL `ApiKeyReloader` / config-reloader pattern per CLAUDE.md), so (b) is technically available. Warning copy must cite "Batch = Live: Unified Pipeline Architecture" codex rule from workspace CLAUDE.md. Audit log every ad-hoc change with persona email + param diff + timestamp.
    status: todo
  - id: p11-features-readonly-for-clients
    content: |
      - [ ] [AGENT] P2. Data + feature subscriptions are READ-ONLY for all non-admin personas. User 2026-04-20: "They're not really configuring data and feature subscriptions; that's just given to them. They can view it." Ensure any `/services/dart/features/` or `/services/dart/data/` pages render read-only cards (subscription status, last update, delivery SLA) — no edit controls for non-admin. Admin only can mutate via `/ops/admin/feature-subscriptions/`.
    status: todo
  - id: p11-dart-signals-in-no-strategy-config
    content: |
      - [ ] [AGENT] P1. DART Signals-In personas must NOT see the strategy configuration surface AT ALL. User 2026-04-20: "If it signals, they don't need to be able to configure strategies, because it's their own signals". Tab visibility: entire `Strategy Config` tab hidden under DART for `prospect-signals-only` + any persona without `strategy-full` entitlement. Confirmers / ML / Execution Backtest tabs also hidden. Visible tabs for Signals-In inside DART: **Signal Instruction Intake** (their inbound signals), **Terminal** (see p11-trading-terminal-reposition), **Positions**, **P&L**, **Analytics**, **Reconciliation**. Verify via persona switcher: switching to `ops@defihf.com` shows only Signals-In-appropriate DART tabs.
    status: todo
  - id: p11-trading-terminal-reposition
    content: |
      - [ ] [AGENT] P2. Reposition Trading Terminal as analytics / reconciliation / emergency-manual surface. User 2026-04-20: "The trading [terminal] then mainly comes about analytics, reconciliation, and manual trading in case of an emergency, or it should be avoided like unless emergency". Tasks: (a) `/services/dart/terminal/` landing page shows a warning banner above primary layout: "This surface is for analytics + reconciliation. Manual trading should be avoided except in emergency — all routine execution happens via strategy schedulers."; (b) split terminal tabs into two visual groups — **Analytics** (positions, P&L, market view, reconciliation) primary; **Manual Execution** (place order, cancel order) secondary with a collapsed-by-default section + "Emergency use only" hover tooltip; (c) audit-log every manual order placement with warning-banner-acknowledged timestamp. Does NOT remove manual trading — just deprioritises the UX. Family/Archetype picker (Phase 3) stays on the terminal landing since it scopes all views.
    status: todo
  - id: p11-dart-tab-structure-spec
    content: |
      - [ ] [AGENT] P1. Write the canonical DART tab structure spec. New codex file `unified-trading-pm/codex/09-strategy/architecture-v2/dart-tab-structure.md` declaring for each persona tier what tabs are visible inside DART. Template reflecting 4-stage collapse: `DART Full: [Research, Promote, Strategy Config, Execution Config, Terminal (analytics+recon), Signals Intake (optional), Observe (risk/alerts/health/live-PnL), Deployment (runtime profile + chaos + kill-switch, links to deployment-ui), Reports-sub]`; `DART Signals-In: [Signal Intake, Terminal (analytics+recon), Positions, P&L, Analytics, Reconciliation, Observe (read-only)]`; `Admin: all of the above + catalogue-truthiness views`; `Internal trader: all DART Full tabs`. This doc replaces any ambiguity between old lifecycle stages (acquire/build/promote/run/execute/observe) and the new collapsed DART umbrella. Cross-link from existing codex `09-strategy/README.md` + `14-playbooks/` playbooks.
    status: todo

  # ──────────────────────────────────────────────────────────────────────
  # PHASE 9 — Workspace-wide QG validation + INDEX update
  # ──────────────────────────────────────────────────────────────────────
  - id: p9-workspace-qg
    content: |
      - [ ] [SCRIPT] P0. Run `bash scripts/quality-gates.sh` in all affected repos (unified-api-contracts, strategy-service, unified-trading-system-ui) — Pass 1 (full). Then quickmerge each with `--agent`. Verify staging deploy succeeds + smoke tests green (D3 gate for UI repos).
    status: todo
  - id: p9-update-index
    content: |
      - [ ] [AGENT] P3. Update `unified-trading-pm/plans/active/INDEX.md` to list this plan under "UI & Admin Unification" section. After C5 reached on all repos + D3 on UI repos, submit unlock request per agent-unlock protocol.
    status: todo

isProject: true
---

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
| 2     | C1 (docs written)                   | New codex files exist + referenced in `codex/09-strategy/README.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
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
  `signal_leasing_broadcast_architecture_2026_04_20.plan.md`.
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
