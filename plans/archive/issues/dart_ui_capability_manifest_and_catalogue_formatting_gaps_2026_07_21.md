---
doc_type: issue
title:
  dart_ui_strategy_filtering_and_onboarding — 21 genuinely-orphaned residual items (UAC capability-manifest never
  regenerated, catalogue formatting gaps, asset_class rename incomplete)
summary: >-
  Splitting the archived dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md's 67 residual items between its
  two candidate successor plans surfaced that a real chunk has NO successor at all: the original hypothesis that
  capability_wizard_and_manifest_2026_06_11.md owns Phase 9's archetype-capability-taxonomy work is WRONG — that plan
  claims zero of it (confirmed by grep for bespoke/admin_assignment/REPORTING_ONLY etc., all zero hits). Two parallel
  research agents classified all 99 open items across the archived plan's 12 phases; this doc bundles the 21 that came
  back GENUINELY_ORPHANED (real, still-relevant work, no current owner) into one tracked doc per findings-triage rules,
  rather than 21 separate issue docs.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-system-ui]
scope: [engineer]
tags: [plan-discipline, dart, strategy-catalogue, capability-manifest, asset-class-rename]
related:
  [
    plans/active/issues/batch4_strategy_ui_archived_plan_residuals_2026_07_21.md,
    plans/archive/2026_07/capability_wizard_and_manifest_2026_06_11.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: NA
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [batch4_strategy_ui_archived_plan_residuals-006]
resolved_by:
  "unified-api-contracts@e5dc6e7f + unified-trading-pm@7ee0fbb87 (item A: manifest regen),
  unified-api-contracts@08cc94fa + unified-trading-system-ui@bf38c435 (item B: admin assignment model + UI wiring),
  asset_class rename split into its own dedicated plan (asset_class_to_asset_group_rename_2026_07_21.md),
  unified-trading-system-ui@0582398d (item D: formatters) + @7967177b (item E: persona hydration) — all 6 todos DONE;
  the one identified pw:L2 gap was properly split into e2e_login_persona_handoff_helper_stale_2026_07_22.md rather than
  silently claimed"
locked_by:
depends_on: []
---

> **🟢 ARCHIVED 2026-07-28** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule.

# What I found

Two parallel read-only research agents each classified half of the archived
`dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`'s 99 open items (Phases 0-8: onboarding/questionnaire/
FOMO; Phases 9-11 + backlog: archetype-capability taxonomy, instruments resolver, catalogue rendering). Full per-item
evidence lives in the two agents' reports (not reproduced here); this doc groups the **21 GENUINELY_ORPHANED** items by
theme.

## A. UAC capability-manifest was never regenerated after the Phase 9 enum expansion (the big one, ~7 items)

`StrategyArchetype`/`StrategyFamily` gained 19 VOL archetypes, 10 MARKET_MAKING archetypes, and the whole PORTFOLIO
family back in April 2026 (enum-level, confirmed shipped, docstrings cite this plan by name). But
`unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json` — the actual capability-cell data
consumers read — was **never regenerated**: it still has only 23 legacy archetypes, one `VOL_TRADING_OPTIONS` cell, zero
PORTFOLIO cells. `scripts/enumerate_envelope.py`'s own docstring admits the splits/bespoke logic is "currently mocked in
this script — not yet in the UAC capability manifest," citing this now-archived plan as the reason. Confirmed:
`capability_wizard_and_manifest_2026_06_11.md` (the plan the parent issue doc assumed owned this) claims ZERO of it —
its `ARCHETYPE_CAPABILITY_REGISTRY` overlap is about extracting the EXISTING registry into the openapi/manifest
exporter, not adding new archetype cells.

- Regenerate `archetype_capability_manifest.json` with real cells for all 19 VOL / 10 MM / 4 PORTFOLIO archetypes.
- Add a `bespoke_capable: bool` field to `ArchetypeCapabilityClaim`/`ArchetypeCapabilityCell` (currently only a
  script-local `_BESPOKE_CAPABLE` set in `enumerate_envelope.py`).
- Simplify `enumerate_envelope.py` once the above lands (its mocking logic becomes dead code).

## B. Admin strategy-assignment model was never built (~3 items)

- `admin_assignment.py` (`AdminStrategyAssignment` model) doesn't exist anywhere in `unified-api-contracts`.
- `AdminStrategyAssignmentTable.tsx` + `app/(ops)/admin/strategy-assignments/page.tsx` don't exist in the UI repo.
- `lib/entitlements/strategy-route.ts`'s resolvers (`resolveSlotAccess`/`resolveArchetypeAccess`) are a UI-side
  entitlement APPROXIMATION per the file's own docstring — there's no real admin-assignment backing store to project
  from. `canEnterTerminal()` in that same file is defined but never called anywhere (dead code — the terminal-blocking /
  "Reports access only — upgrade for terminal" UX was never wired).

## C. `AssetClass` → `AssetGroup` rename never executed repo-wide (~4 items)

The rename direction is set (newer code — `envelope-loader.ts`, `EnvelopeBrowser.tsx`,
`lib/architecture-v2/ terminology.ts` — already uses `assetGroup`/`ASSET_GROUP`), but the actual sweep never ran:
`AssetClass` is still live in ~20 UAC Python files (`_instrument_enums.py`, `canonical/crosscutting/ledger/_enums.py`,
`internal/reference/instrument.py`, ...) and ~19+15 UI files/identifiers, plus "asset class" prose in marketing content.
Tied together: codex terminology sweep (P11.1.4) can't happen until the code-level rename does.

## D. Strategy-catalogue UI formatting gaps (~3 items, Phase 2)

`lib/strategy-display.ts`'s formatters (`formatFamily`/`formatArchetype`/`formatSlotLabel`) are NOT applied everywhere
the plan required:

- `StrategyCatalogueSurface.tsx`'s `AdminUniverseGrid` renders raw `{instance.family}` / `{instance.archetype}`
  unformatted (only `getArchetypePlanTier` is imported, not the display formatters).
- `components/signal-broadcast/signal-history-table.tsx` renders raw `{emission.slot_label}` (no `formatSlotLabel`).
- `app/(ops)/admin/strategy-universe/page.tsx`'s admin table shows raw `instance.instanceId`, no slot-label column at
  all.
- The phase's own success gate ("zero raw underscore identifiers visible to clients") is not met.

## E. Demo persona → instrument hydration built but never wired (~2 items, Phase 10)

`lib/auth/derive-persona-instruments.ts` implements exactly the spec'd `derivePersonaInstruments(persona)` and has a
real regression test (`tests/unit/lib/auth/demo-provider-instruments.test.ts`). But `personaToAuthUser()` in
`demo-provider.ts` is still synchronous and never calls it; `AuthUser` has no `instruments` field. The
`QUESTIONNAIRE_PRESEEDS` mock object the cleanup step was supposed to remove is still there (`demo-provider.ts: 90-143`,
unremoved).

## F. Other orphans (~2 items)

- `enumerate_envelope.py`/`enumerate_catalogue.py` aren't wired into `scripts/dev/dev-start.sh` (N1 from the archived
  plan's trailing backlog).
- Phase 3's `seedFiltersFromQuestionnaire()` has no `instrument_types` passthrough — `StrategyCatalogueFilter` has zero
  `instrumentType` dimension.

# Why it matters

Item A (the capability-manifest regeneration gap) is the highest-leverage one: it means the capability wizard, the
prospectus generator, and any consumer reading `archetype_capability_manifest.json` as the archetype-coverage SSOT are
all working off data that's 3 months stale relative to the actual enum surface — 29 of 52+ archetypes have NO capability
cell at all. Items B/C are real, scoped, still-wanted product work with zero current owner. Items D/E/F are smaller
UI-polish gaps.

# Recommended decision

File as a standalone P3 tracking doc (this one) rather than force-fitting into either successor plan, since neither
`marketing_site_three_route_consolidation` nor `capability_wizard_and_manifest` actually claims this scope. A future
plan-authoring pass can pull items A-C into a real "capability manifest v2 / admin assignment model" plan when someone
has bandwidth; items D-F are small enough to fold into whichever plan next touches `StrategyCatalogueSurface.tsx` /
`demo-provider.ts`.

## Todos

- [x] [BACKEND] P2. Regenerate `archetype_capability_manifest.json` with real cells for the 19 VOL / 10 MM / 4 PORTFOLIO
      archetypes added in Phase 9 (currently only 23 legacy archetypes have cells); add `bespoke_capable: bool` to
      `ArchetypeCapabilityClaim`. (repo: unified-api-contracts) — ✅ unified-api-contracts@e5dc6e7f (manifest 23→53
      archetypes, `bespoke_capable` field, `CROSS_CATEGORY` enum fix for the new PORTFOLIO cells) +
      unified-trading-pm@7ee0fbb87 (30 codex narrative sections, new Family 9: Portfolio). Full `quality-gates.sh` green
      in both repos; `test_archetype_capability_manifest_parity.py` (17/17) +
      `test_archetype_capability_may_23_coverage.py` pass. `enumerate_envelope.py` simplification (issue-doc prose
      bullet, not a separate todo) deferred — its mocking logic is now dead code but simplifying it was not part of this
      checkbox's scope.
- [x] [BACKEND] P3. Build the `admin_assignment.py` (`AdminStrategyAssignment`) model. (repo: unified-api-contracts) —
      ✅ unified-api-contracts@08cc94fa: `AdminStrategyAssignment` (assignment_id/scope/scope_id/route/org_id/
      config_version/notes/created_at/created_by, frozen Pydantic per `archetype_capability.py` conventions) +
      `AdminStrategyAssignmentWriter.validate()` enforcing the archived-plan's `ORG_CONFLICT_ON_STRATEGY` exclusivity
      rule (a `LOCKED` route on a `scope_id` excludes every other org on that `scope_id`); wired into both
      `architecture_v2/__init__.py` and the canonical `internal/__init__.py` re-export surface; 7 new unit tests. Full
      `quality-gates.sh` green. This checkbox originally bundled a UAC Python model with 3 UI/TypeScript deliverables
      (Table, page, resolver wiring) under one `[BACKEND]`-tagged item + `assigned_role: backend_engineer` dispatch — a
      craft-scope mismatch per `unified-trading-pm/agents/backend_engineer.md`'s `does_not: UI /     TypeScript work`,
      and per `/codex/06-coding-standards/ui-testing-layers.md` any UI tick needs a `pw:L2` regression spec a
      backend_engineer worker isn't positioned to author. Split the remaining scope into the todo below (assigned_role:
      ui_developer) rather than silently claiming it done.
- [x] [UI] P3. ✅ Wire `AdminStrategyAssignment` as the real backing store for `lib/entitlements/strategy-route.ts`'s
      resolvers. — `unified-trading-system-ui@bf38c435`. All 5 scoped deliverables shipped: (1) Firestore-backed
      `app/api/v1/admin-strategy-assignments/{route,[id]/route,resolved/route}.ts` +
      `lib/admin/server/strategy-assignments.ts`, porting `AdminStrategyAssignmentWriter.validate()`'s
      `ORG_CONFLICT_ON_STRATEGY` rule verbatim (same-scope_id + either-side-LOCKED = reject); new
      `admin_strategy_assignments` Firestore collection registered in `lib/admin/server/collections.ts`, following the
      `groupsCollection()` pattern exactly. (2) `lib/admin/api/strategy-assignments.ts` (`apiClient` wrapper, mirrors
      `groups.ts`) + `hooks/api/use-strategy-assignments.ts` (TanStack Query, mirrors pattern B). (3)
      `AdminStrategyAssignmentTable.tsx` (a genuine flat `Table`, not the groups page's inline-Card pattern — the todo
      named a dedicated Table component) + `app/(ops)/admin/strategy-assignments/page.tsx` with create/edit/delete
      dialogs; wired into `ADMIN_TABS` in `components/shell/service-tabs.tsx` (required — the orphan-route audit
      correctly caught the page as unreachable before this). (4) `resolveAssignedSlotsForOrg()` expands instance-scope
      assignments directly (scope_id IS the slot key per the UAC model's docstring) and archetype/family-scope
      assignments via `strategy_instruments.json` (fetched through the new `/api/v1/admin-strategy-assignments/resolved`
      endpoint using `req.nextUrl.origin`, since `envelope-loader.ts`'s loader is browser-relative-fetch-only and
      unusable from a Route Handler); both `lib/auth/demo-provider.ts::personaToAuthUser()` and
      `lib/auth/firebase-provider.ts::enrichUserFromBackend()` now prefer the store's result over the persona-stub
      `assigned_strategies`, falling back to the stub on any fetch failure (network/non-200/parse error) so login never
      regresses on this lookup. (5) Wired the terminal order-entry submit gate — **deviated from a literal
      `canEnterTerminal(user, linkedStrategyId)` call**: confirmed via read that `linkedStrategyId` (from
      `lib/mocks/fixtures/strategy-instances.ts`, format `{archetype}@venue-asset-instrument-period-quote-env`) does not
      match the `strategy_instruments.json` slot-key format `assigned_strategies` is populated with
      (`{archetype}@{category}-{instrument}-{venue}`) — calling `canEnterTerminal` with the mismatched format would have
      exact-matched nothing and silently locked EVERY org with real `assigned_strategies` out of the terminal entirely,
      a functional regression this todo would have introduced rather than fixed. Used
      `resolveArchetypeAccess(user, linkedStrategyId.split("@")[0])` instead — format-agnostic (every known slotKey
      format agrees on "archetype before the first `@`") — with the disabled-state reason surfaced via `ACCESS_LABELS`.
      Documented inline in `order-entry-widget.tsx`.

  **QG**: full `quality-gates.sh` green (typecheck/lint/286 vitest+50.92% coverage/build/orphan-audit — required a
  second pass: the orphan-audit correctly flagged `/admin/strategy-assignments` + the 2 new API routes as new orphans;
  fixed by wiring the nav tab (real fix) + whitelisting the 2 machine-only API-HANDLER routes per the documented triage
  rule). `tests/widgets/terminal/order-entry.test.tsx` (13/13, pre-existing, unmodified) still green — the new `user`
  field on `TerminalData` is additive and the mock helper's own doc comment says exactly this class of addition
  shouldn't break it. Full vitest suite: 3286 passed, 2 pre-existing skips (unchanged baseline).

  **`pw:L2` — NOT obtained, and I'm flagging why rather than silently claiming it.** Wrote
  `tests/e2e/admin-strategy-assignments.spec.ts` (Tier 1 page-render, Tier 2-5 create→edit→delete lifecycle +
  `ORG_CONFLICT_ON_STRATEGY` UI rejection, modeled on `user-management.spec.ts`), but it times out at login in this
  environment. Verified this is NOT a regression from my change: the **untouched** `tests/e2e/user-management.spec.ts`
  fails identically (21/21, same `waitForURL("**/dashboard**")` timeout). Root-caused: `app/(public)/login/page.tsx` has
  no `?persona=` handling at all (only an `?email=`+`#pwd=` fragment handoff) — the shared `loginAsAdmin` E2E helper
  convention is stale repo-wide. Probing the real handoff format directly also failed (redirects externally to
  `uat.odum-research.com` even under `pnpm dev:mock`) — a second, deeper pre-existing issue. Filed
  `plans/active/issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md` (P2, 3 todos: diagnose the UAT-redirect
  branch, repair the shared login helper, then retroactively re-run this spec) rather than block this ticket on an
  unrelated, pre-existing E2E-infra break outside its scope. `pw:L2` evidence is deferred to that issue doc's item 3.

  **Retroactive-`pw:L2` reconciliation (2026-08-10,
  `e2e_login_persona_handoff_helper_stale_2026_07_22_finalize_2026_08_10.md` todo 2): NO `pw:L2 ✓` is recordable for
  this item.** The source doc's deferred re-run (its item 3) was resolved 2026-08-10 with the blocker outcome, not a
  clean pass — three independent re-runs (slots 20/6/4, documented on the source doc's todo) + the finalize plan's own
  slot-31 re-verification all hit the documented Firebase-Admin-creds/dev-server-instability class (2 failed / 1 passed:
  `waitForURL("**/dashboard**")` first-navigation compile-latency timeout + `/api/v1/*` Firebase-Admin-creds 500 on the
  LOCKED status-update). This item stands without `pw:L2 ✓`; the fix owner is
  `/plans/active/issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md`.

- [x] BLOCKED-SUPERSEDED [CODE] P3. ~~Execute the `AssetClass` → `AssetGroup` rename repo-wide~~ — SUPERSEDED
      2026-07-21: the real blast radius is 9+ repos (not 2), touches a persisted-schema-adjacent field, and risks
      conflating two distinct `AssetClass` enums (domain vs. `LedgerAssetClass`). See
      `plans/archive/issues/asset_class_to_asset_group_rename_scope_underestimated_2026_07_21.md` (the investigation)
      and `plans/active/asset_class_to_asset_group_rename_2026_07_21.md` (the dedicated 6-todo phased plan that owns
      this work now — human plan, `assigned_vm: NA`, pending operator dispatch decision). Non-dispatchable — do not
      execute this line as scoped. (repo: unified-api-contracts, unified-trading-system-ui) — already covered by
      plans/active/asset_class_to_asset_group_rename_2026_07_21.md (see that doc for execution).
- [x] [CODE] P3. ✅ Apply `lib/strategy-display.ts` formatters (`formatFamily`/`formatArchetype`/`formatSlotLabel`) in
      `StrategyCatalogueSurface.tsx`'s `AdminUniverseGrid`, `signal-history-table.tsx`, and
      `admin/strategy-universe/page.tsx` — currently render raw underscore identifiers. (repo:
      unified-trading-system-ui) — `unified-trading-system-ui@0582398d`.

  `StrategyCatalogueSurface.tsx` had the raw-render gap in TWO grids, not one: `AdminUniverseGrid` (the todo's named
  target) AND `AdminEditorGrid` (same file, same `instance.family`/`instance.archetype` pattern, not named in the todo
  but fixed in the same commit — same file, same bug). Both now call `formatFamily()`/`formatArchetype()`.
  `signal-history-table.tsx` had it in TWO places too: the table body's `emission.slot_label` cell AND the slot-filter
  `<Select>` dropdown's option labels — both now `formatSlotLabel()`; the raw value is kept on the table cell's `title`
  attribute for copy-paste, matching `lib/strategy-display.ts`'s own documented admin-table convention ("may show the
  monospace slot label as a subtitle/hover... but the primary label must be formatted"). Verified via read (not
  grep-and-conclude) that `RealityPositionCard.tsx`/`FomoTearsheetCard.tsx` already call these formatters correctly — no
  gap there. `admin/strategy-universe/page.tsx` itself has zero direct raw-render code — it only mounts
  `<StrategyCatalogueSurface viewMode="admin-universe" />`, so the finding's "no slot-label column" note was about the
  rendered _view_ (i.e. `AdminUniverseGrid`, now fixed), not literal code in that file; did not invent a separate
  synthesized slot-label column since `StrategyInstance.instanceId` is a content hash (not an `archetype@venue-scope`
  string `formatSlotLabel()` can parse) — that would be a distinct feature build beyond "apply the formatters," out of
  this P3 todo's scope. Full `quality-gates.sh` green (259s: typecheck/lint/ 3284 unit tests/build/DeFi-citation all
  passed, colour count unaffected at 96). Added 4 focused RTL/vitest assertions (2 per touched component file) asserting
  the formatted text renders and the raw underscore identifiers do not — no Playwright spec, since this is a
  `[CODE]`-tagged pure text-formatting fix with no CSS-var-resolution risk (unlike the `[UI]`-tagged colour-migration
  batches), already fully typechecked; RTL asserting real rendered DOM text is the higher-precision guard for this
  change class. **Concurrent-peer reconciliation during ship**: hit the sentinel-invalidated-by-peer-commit case twice
  in a row (another slot landed `feat(auth): wire derivePersonaInstruments()` — this same issue doc's item E — then a
  third slot landed Batch 5 of the colour-migration issue doc, 28 files) — re-ran `quality-gates.sh` fresh against each
  rebased HEAD (whole-program typecheck/tests, not just my files) before retrying `quickmerge`, per the documented
  peer-commit recipe; no conflicts, no guessing.

- [x] [CODE] P3. ✅ Wire `derivePersonaInstruments()` into `personaToAuthUser()` (make it async, populate a new
      `AuthUser.instruments` field); remove the now-redundant `QUESTIONNAIRE_PRESEEDS` mock once wired. (repo:
      unified-trading-system-ui) — `unified-trading-system-ui@7967177b`

  `personaToAuthUser()` (`lib/auth/demo-provider.ts`) is now `async`, awaits `derivePersonaInstruments(persona)`, and
  populates a new `AuthUser.instruments?: readonly string[]` field (`lib/auth/types.ts`) when non-empty. Both call sites
  updated: `restore()` (constructor fire-and-forget `void this.restore()`, now itself `async`) and `login()` (already
  `async`, trivial `await`).

  **Verified the "now-redundant" claim before removing** the `QUESTIONNAIRE_PRESEEDS` block from `login()` — grepped
  `tests/e2e/` + `tests/unit/` for `desmond-signals-in`/`desmond-dart-full`/`elysium-defi`/`elysium-defi-full` and for
  `questionnaire-response-v1`: no test asserts the preseed is written on login for these personas; the
  `questionnaire-response-v1` key IS exercised elsewhere (`demo-perp-funding-journey.spec.ts`,
  `refactor-g1-10-questionnaire.spec.ts`) but through the REAL questionnaire-submission flow for unrelated personas
  (`prospect-perp-funding`), not this login-time mock. Safe to remove.

  Typecheck clean, full `npx vitest run` (whole repo): 3282/3284 passed (2 pre-existing skips, unrelated
  `ECONNREFUSED`/socket-hangup noise from an unrelated integration test's external-service probe). Shipped +
  quality-gates.sh green.

## Codex SSOTs

`/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`,
`codex/06-coding-standards/ strategy-display-conventions.md`.
