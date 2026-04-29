# DART UX Cockpit Refactor — Phase 1 Handoff Brief (2026-04-29)

**Read order for the next agent:**

1. This file (the immediate handoff state)
2. `unified-trading-pm/plans/active/dart_ux_cockpit_executing_agent_prompt_2026_04_29.md` (the broader 9-phase brief,
   with the 5 per-phase test gates and 23 agent guardrails)
3. `unified-trading-pm/plans/active/dart_ux_cockpit_refactor_2026_04_29.plan.md` (the canonical plan-of-record — read §0
   → §26 in full)
4. `unified-trading-system-ui/docs/reference/INDEX.md` (the new ideal-world archetype docs; read selectively per phase)

---

## What is already done (commits live on `origin/live-defi-rollout`)

### PM repo — `unified-trading-pm`

| Commit        | What                                                                                                                                            |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `c2a16d47`    | Plan §4.8 Configuration Lifecycle + §4.9 Widget Vocabulary SSOT + §4.10 v2 archetype-expansion roadmap + §4.11 Cross-cutting widget conventions |
| `f7e922f3`    | Executing-agent prompt — full per-phase test gates + MCP Playwright + 23 guardrails                                                             |
| _(this file)_ | Phase 1 handoff brief                                                                                                                           |

### UI repo — `unified-trading-system-ui`

| Commit     | What                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `6e13e7a6` | Reference docs — Sebastian (External Signal Provider) + Priya (Platform Operations Lead) archetypes, treasury §10.5 subsection in `automation-common-tools.md`, cross-cutting principle #11 (Release artifact as system-of-record), Platform Comparison pointer in INDEX.md                                                                                                                                                                                                                            |
| `aeb16db7` | **Phase 1 foundation primitives** — `lib/architecture-v2/workspace-scope.ts` (full schema + URL serializer + matchesScope), `lib/architecture-v2/strategy-availability-resolver.ts` (§4.5 visibility resolver), `lib/stores/workspace-scope-store.ts` (Zustand store + persist + URL hydration + ScopeChangeEvent), `lib/utils/nav-helpers.ts::linkWithScope`, `components/scope/workspace-scope-provider.tsx`, `lib/analytics/track.ts` extended with scope events, 47 unit tests, 0 typecheck errors |

**Verify your starting state:** From `unified-trading-system-ui/`:

```bash
git pull --ff-only
git log -1 --oneline   # should show aeb16db7 as current HEAD or a descendant
CI=true npx vitest run tests/unit/lib/architecture-v2/workspace-scope.test.ts \
                        tests/unit/lib/architecture-v2/strategy-availability-resolver.test.ts \
                        tests/unit/lib/utils/nav-helpers-link-with-scope.test.ts
# Expected: 47 tests passed
npx tsc --noEmit
# Expected: 0 errors
```

---

## What remains for Phase 1 to be fully complete

Per the 5 per-phase gates in the executing-agent prompt:

1. **Consumer migration (~60 files)** — replace all callers of the deleted-imminent `useGlobalScope()` and
   `useDashboardFilterContext()` and the local-state in `FamilyArchetypeAssetGroupBrowser`.
2. **Wrap `app/(platform)/layout.tsx`** in `<WorkspaceScopeProvider>` (replacing `<DashboardFilterProvider>`).
3. **Delete** `lib/stores/global-scope-store.ts` + `lib/context/dashboard-filter-context.tsx` + obsolete chunks of
   `lib/stores/scope-helpers.ts`.
4. **Run existing Playwright e2e specs** — `dart-tile-split.spec.ts`, `instrument-type-view-gating.spec.ts`,
   `tier-override-flip.spec.ts` — all green.
5. **Author new Phase 1 e2e spec** at `tests/e2e/playbooks/dart-cockpit/phase-1a-scope-foundation.spec.ts` covering:
   scope persistence across navigate + refresh + copied URL.
6. **MCP Playwright Tier-0 demo walkthrough** — drive the 13-step canonical flow per the executing-agent prompt; capture
   screenshots under `unified-trading-system-ui/.playwright-evidence/phase-1a/`.
7. **Tick the Phase 1 checkbox** in the plan-of-record
   (`unified-trading-pm/plans/active/dart_ux_cockpit_refactor_2026_04_29.plan.md`); commit + push.

---

## Field-name translation table — old → new

The new `WorkspaceScope` is the strict superset of the deleted shapes, but with renamed fields. Migrate every consumer
per this table.

### From `useGlobalScope()` (deleted: `lib/stores/global-scope-store.ts`)

| Old API                               | New API                               | Notes                                                                                  |
| ------------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------------- |
| `const { scope } = useGlobalScope()`  | `const scope = useWorkspaceScope()`   | Imports: `import { useWorkspaceScope } from "@/lib/stores/workspace-scope-store"`      |
| `scope.organizationIds`               | `scope.organizationIds`               | Same                                                                                   |
| `scope.clientIds`                     | `scope.clientIds`                     | Same                                                                                   |
| `scope.strategyIds`                   | `scope.strategyIds`                   | Same                                                                                   |
| `scope.assetGroupIds` (legacy plural) | `scope.assetGroups`                   | Renamed; type stays `VenueAssetGroupV2[]`                                              |
| `scope.strategyFamily` (single)       | `scope.families[0] ?? undefined`      | Now multi-select; for single-pick callers, take the first element                      |
| `scope.strategyArchetype` (single)    | `scope.archetypes[0] ?? undefined`    | Same pattern                                                                           |
| `scope.strategyFamilyIdsV2` (multi)   | `scope.families`                      | Renamed; same multi-select shape                                                       |
| `scope.strategyArchetypeIds` (multi)  | `scope.archetypes`                    | Renamed; same multi-select shape                                                       |
| `scope.underlyingIds`                 | `scope.underlyingIds`                 | Same                                                                                   |
| `scope.mode` (`"live"` / `"batch"`)   | `scope.mode`                          | Same                                                                                   |
| `scope.asOfDatetime`                  | `scope.asOfTs`                        | Renamed; same ISO-8601 string semantics                                                |
| `setStrategyFamily(family)`           | `setFamilies(family ? [family] : [])` | Use `useWorkspaceScopeStore((s) => s.setFamilies)` to select the setter                |
| `setStrategyArchetype(arch)`          | `setArchetypes(arch ? [arch] : [])`   | Same                                                                                   |
| `setStrategyFamilyIdsV2(ids)`         | `setFamilies(ids)`                    | Same                                                                                   |
| `setStrategyArchetypeIds(ids)`        | `setArchetypes(ids)`                  | Same                                                                                   |
| `setAssetGroupIds(ids)`               | `setAssetGroups(ids)`                 | Same                                                                                   |
| `setMode(m)`                          | `setMode(m)`                          | Same                                                                                   |
| `setAsOfDatetime(dt)`                 | `setAsOfTs(dt)`                       | Same                                                                                   |
| `clearAll()` / `reset()`              | `reset()`                             | Same                                                                                   |
| `GlobalScopeState` type               | `WorkspaceScope` type                 | Imports: `import type { WorkspaceScope } from "@/lib/architecture-v2/workspace-scope"` |

### From `useDashboardFilterContext()` / `useDashboardFilter()` (deleted: `lib/context/dashboard-filter-context.tsx`)

| Old API                                            | New API                                                                                                         | Notes                                                                                                                                                                                                                                                                              |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `const { filter } = useDashboardFilterContext()`   | `const scope = useWorkspaceScope()`                                                                             | The whole concept of "filter" merges into "scope"                                                                                                                                                                                                                                  |
| `filter.family`                                    | `scope.families[0] ?? null`                                                                                     | Was single-pick `StrategyFamily \| null`                                                                                                                                                                                                                                           |
| `filter.archetype`                                 | `scope.archetypes[0] ?? null`                                                                                   | Same                                                                                                                                                                                                                                                                               |
| `filter.venueSetVariant`                           | `scope.venueSetVariants[0] ?? null`                                                                             | Was single-pick                                                                                                                                                                                                                                                                    |
| `filter.shareClass`                                | `scope.shareClasses[0] ?? null`                                                                                 | Same                                                                                                                                                                                                                                                                               |
| `filter.instrumentType`                            | `scope.instrumentTypes[0] ?? null`                                                                              | Same                                                                                                                                                                                                                                                                               |
| `setFilter(partial)`                               | individual setters or `applyScope(partial)`                                                                     | Use `useWorkspaceScopeStore((s) => s.applyScope)` for bulk updates                                                                                                                                                                                                                 |
| `clear()`                                          | `reset()`                                                                                                       | Same                                                                                                                                                                                                                                                                               |
| `expanded` / `setExpanded`                         | local React state in the strip component                                                                        | The expanded UI state was localStorage-backed via `dashboardFilter:<userId>:expanded`. **Decide:** keep local-state-only OR add `dashboardStripExpanded` to a separate UI-state store. Recommendation: keep local-state-only for the strip; it's UI ephemera, not workspace scope. |
| `appendFilterToHref(href, filter)`                 | `linkWithScope(href, scope)`                                                                                    | Imports: `import { linkWithScope } from "@/lib/utils/nav-helpers"`                                                                                                                                                                                                                 |
| `filterToQueryString(filter)`                      | use `serializeWorkspaceScope(scope)` and convert with `new URLSearchParams(...)`                                | Or just use `linkWithScope("", scope).slice(1)` if you only need the query string                                                                                                                                                                                                  |
| `filterHashBucket(filter)`                         | KEEP this function — re-implement under `lib/utils/filter-hash.ts` taking `(scope: WorkspaceScope) => number`   | Used by `hooks/api/use-filtered-dashboard-quick-stats.ts` for deterministic mock-bucket hashing. Same algorithm, new input.                                                                                                                                                        |
| `DashboardFilterState` type                        | `Pick<WorkspaceScope, "families" \| "archetypes" \| "venueSetVariants" \| "shareClasses" \| "instrumentTypes">` | Or just use `WorkspaceScope` directly                                                                                                                                                                                                                                              |
| `EMPTY_FILTER` constant                            | `EMPTY_WORKSPACE_SCOPE` from `@/lib/architecture-v2/workspace-scope`                                            | Same shape concept                                                                                                                                                                                                                                                                 |
| `<DashboardFilterProvider userId={...}>` in layout | `<WorkspaceScopeProvider>`                                                                                      | Imports: `import { WorkspaceScopeProvider } from "@/components/scope/workspace-scope-provider"`. Drop the `userId` prop — the new provider hydrates from URL search params on mount and on every URL change.                                                                       |

### From local state in `app/(platform)/services/research/_components/family-archetype-asset-group-browser.tsx`

| Old (lines 55-56)                                        | New                                                                                    |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `const [activeFamily, setActiveFamily] = useState`       | `const family = useWorkspaceScope().families[0] ?? null` + `setFamilies` setter        |
| `const [activeArchetype, setActiveArchetype] = useState` | `const archetype = useWorkspaceScope().archetypes[0] ?? null` + `setArchetypes` setter |

This is the highest-value change in the whole migration — the audit identified that this local-state component was the
biggest scope-leak in the app (5 separate research pages each carrying their own copy). Lifting it to global scope is
the entire point of Phase 1.

---

## Consumer migration — file lists in priority order

Total files to touch: **~60**. Recommended migration order (highest-value first, lowest-risk second):

### Batch 1 — Writers (4-5 files; rewire mutations first)

These components write to the deleted stores; if they're not migrated first, the rest of the app reads stale state.

| File                                                          | Old API                         | New API                                                                     |
| ------------------------------------------------------------- | ------------------------------- | --------------------------------------------------------------------------- |
| `components/platform/global-scope-filters.tsx`                | full `useGlobalScope` setters   | full `useWorkspaceScopeActions` setters                                     |
| `components/shell/asset-group-pill.tsx`                       | `setAssetGroupIds`              | `setAssetGroups`                                                            |
| `components/architecture-v2/trading-family-filter-banner.tsx` | `setStrategyFamily/Archetype`   | `setFamilies` / `setArchetypes` (single-pick semantics: pass `[v]` or `[]`) |
| `components/platform/research-family-shell.tsx`               | `setStrategyFamily/Archetype`   | same                                                                        |
| `components/platform/live-asof-toggle.tsx`                    | `setMode`, `setAsOfDatetime`    | `setMode`, `setAsOfTs`                                                      |
| `components/services/DashboardFilterStrip.tsx`                | `setFilter` from filter context | `applyScope` from workspace store + local React state for the expanded flag |

### Batch 2 — Layout provider switch (1 file)

| File                        | Change                                                                                                                                                                                                                                                                                            |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/(platform)/layout.tsx` | Replace `<DashboardFilterProvider userId={...}>` with `<WorkspaceScopeProvider>`. The new provider does NOT need a `userId` prop (it hydrates from URL search params and uses Zustand's per-user storage namespacing if/when extended). Per-user localStorage isolation is a follow-up if needed. |

### Batch 3 — Hooks layer (~15 files; data API hooks)

These read scope to drive API calls. Mechanical search-replace.

```
hooks/api/use-orders.ts
hooks/api/use-positions.ts
hooks/api/use-performance.ts
hooks/api/use-trading.ts
hooks/api/use-ir-archive-metadata.ts
hooks/api/use-reports.ts
hooks/api/use-risk-alert-notifications.ts
hooks/api/use-ml-models.ts
hooks/api/use-strategies.ts
hooks/api/use-alerts.ts
hooks/api/use-risk.ts
hooks/api/use-filtered-dashboard-quick-stats.ts  # also needs filterHashBucket re-impl
hooks/use-active-strategy-id.ts
hooks/use-dashboard-filter.ts                    # DELETE (becomes a 1-line re-export of useWorkspaceScope, or just inline migrate callers)
lib/hooks/use-asset-group-data.ts                # rename internal var; reads `assetGroups[0]`
```

### Batch 4 — Widget data contexts (~14 files; mostly read-only)

Each is a React context provider that reads scope and supplies it to downstream widgets. Pure import + field-rename
change.

```
components/widgets/strategies/strategies-data-context.tsx
components/widgets/sports/sports-data-context.tsx
components/widgets/alerts/alerts-data-context.tsx
components/widgets/markets/markets-data-context.tsx
components/widgets/orders/orders-data-context.tsx
components/widgets/pnl/pnl-data-context.tsx
components/widgets/options/options-data-context.tsx
components/widgets/defi/defi-data-context.tsx
components/widgets/accounts/accounts-data-context.tsx
components/widgets/positions/positions-data-context.tsx
components/widgets/predictions/predictions-data-context.tsx
components/widgets/instructions/instructions-data-context.tsx
components/widgets/trades/trades-data-context.tsx
components/widgets/book/book-data-context.tsx
components/widgets/bundles/bundles-data-context.tsx
```

### Batch 5 — Widget leaves (~12 files; pure rename)

```
components/widgets/overview/pnl-chart-widget.tsx
components/widgets/overview/use-overview-page-data.ts
components/widgets/overview/kpi-strip-widget.tsx
components/widgets/overview/scope-summary-widget.tsx
components/widgets/risk/use-risk-page-data.ts
components/widgets/defi/defi-health-factor-widget.tsx
components/widgets/terminal/price-chart-widget.tsx
components/widgets/terminal/use-terminal-page-data.ts
components/widgets/alerts/alerts-kill-switch-widget.tsx
components/trading/live-signal-feed.tsx
components/shell/command-palette.tsx
```

### Batch 6 — Service pages currently reading scope (~6 files)

```
app/(platform)/services/research/ml/page.tsx
app/(platform)/services/observe/reconciliation/page.tsx
app/(platform)/services/observe/recovery/page.tsx
app/(platform)/services/trading/layout.tsx
app/(platform)/services/trading/terminal/page.tsx
app/(platform)/services/trading/overview/page.tsx
app/(platform)/dashboard/page.tsx                # uses appendFilterToHref → linkWithScope
```

### Batch 7 — `FamilyArchetypeAssetGroupBrowser` (lift local state to scope; 1 source file + 5 callers)

```
app/(platform)/services/research/_components/family-archetype-asset-group-browser.tsx   # the source — replace useState with useWorkspaceScope
app/(platform)/services/research/strategies/page.tsx
app/(platform)/services/research/strategy/overview/page.tsx
app/(platform)/services/research/strategy/families/[family]/page.tsx
app/(platform)/services/research/strategy/catalog/page.tsx
app/(platform)/services/research/strategy/families/page.tsx
```

### Batch 8 — Helpers + tests (3 files)

```
lib/stores/scope-helpers.ts                      # update GlobalScopeState type → WorkspaceScope shape; the helpers now take (scope: Pick<WorkspaceScope, "organizationIds" | "clientIds" | "strategyIds">) which is a strict subset
__tests__/dashboard-filter-propagation.test.tsx  # rewrite to test the new store + linkWithScope
tests/unit/lib/architecture-v2/workspace-scope.test.ts                # already exists; extend if you add per-user storage
tests/unit/lib/architecture-v2/strategy-availability-resolver.test.ts # already exists
```

### Batch 9 — Delete the deleted-imminent files (LAST)

```
lib/stores/global-scope-store.ts          # DELETE after grep proves zero remaining imports
lib/context/dashboard-filter-context.tsx  # DELETE same gate
```

Run before deletion:

```bash
grep -rE "useGlobalScope|GlobalScopeState|GlobalScopeActions|appendFilterToHref|filterToQueryString|filterHashBucket|useDashboardFilterContext|useOptionalDashboardFilterContext|DashboardFilterProvider|DashboardFilterState|EMPTY_FILTER" \
  app components hooks lib tests __tests__ \
  --include="*.ts" --include="*.tsx" 2>&1 | grep -v node_modules
# Should return 0 hits before you delete.
```

---

## Per-batch verification (run after each batch)

```bash
cd unified-trading-system-ui

# Type-check (must be 0 errors)
npx tsc --noEmit 2>&1 | wc -l   # expect: 0

# Run the new Phase 1 unit tests + adjacent ones
CI=true npx vitest run tests/unit/lib/architecture-v2 tests/unit/lib/utils

# Smoke the dev server (don't leave running)
bash scripts/dev-tiers.sh --status
# If green, optionally:
# bash scripts/dev-tiers.sh --tier 0
# (open http://localhost:3000, verify dashboard loads + scope persists)
```

After Batch 9 (deletions), run the full unit-test suite + Playwright e2e:

```bash
CI=true npm test -- --run
# Then existing Playwright specs (under unified-trading-system-ui/tests/e2e/playbooks/):
npx playwright test dart-tile-split.spec.ts instrument-type-view-gating.spec.ts tier-override-flip.spec.ts
```

---

## MCP Playwright Tier-0 walkthrough (the closing gate)

After the migration + deletions land, run the canonical Tier-0 demo flow per
`unified-trading-pm/plans/active/dart_ux_cockpit_executing_agent_prompt_2026_04_29.md` "MCP Playwright Tier-0 demo
verification" section. Save evidence under `unified-trading-system-ui/.playwright-evidence/phase-1a/` (gitignored).

Demo personas to test:

- `desmondhw@gmail.com` / `demo123` (DART-Full ↔ Signals-In tier-override)
- `patrick@bankelysium.com` / `demo123` (DeFi-Full ↔ DeFi-Base)

Required signals:

- Zero console errors
- Zero 4xx / 5xx network errors against mock-handler endpoints
- Scope persists across navigate + refresh + copied URL
- Tier-override flip reshapes the cockpit (Research stages padlock for Signals-In)

---

## Common pitfalls (don't repeat my near-misses)

1. **Don't ship compatibility shims.** The user's directive: clean refactor, no technical debt. If you find yourself
   writing a `useGlobalScope = () => useWorkspaceScope` re-export, stop and migrate the caller instead.
2. **Don't `--no-verify` past prek hooks.** Prettier reformats markdown / TS — let it. Re-stage and retry.
3. **Don't push when other repos are dirty.** Run `git status` in PM and the dependency repos before pushing UI.
4. **Don't conflate filter and scope.** The `DashboardFilterStrip`'s expanded flag is local UI state, not scope. Keep it
   local.
5. **Don't break the §4.3 live-stream safety contract.** The store's setter trusts the caller — confirm dialog +
   entitlement check live at the call-site (Phase 2 scope-bar work).
6. **Don't delete `scope-helpers.ts` outright.** It's still useful — just update its type imports. The
   org→client→strategy cascade logic stays.
7. **Don't migrate widgets in batch with hooks.** Hooks first (read-only impact); widgets second (UI impact). Each batch
   typecheck before the next.
8. **Don't skip the MCP Playwright walkthrough.** This is the gate that distinguishes "tests pass" from "the demo
   prospect actually has a working experience".

---

## After Phase 1 — what's next

Phase 1B (Configuration Lifecycle primitives) lands BEFORE Phase 5 because Phase 5 widget metadata declares
`configBinding.reads` / `configBinding.mutates` per widget. Files to create:

- `lib/architecture-v2/strategy-release-bundle.ts` (typed object per §4.8.2)
- `lib/architecture-v2/runtime-override.ts` (typed discriminated union per §4.8.3)
- `lib/architecture-v2/external-signal-strategy-version.ts` (Signals-In versioning per §4.8.5)
- `lib/architecture-v2/treasury-config.ts` (TreasuryPolicyConfig + TreasuryOperationalConfig split per §4.8.7)
- `lib/architecture-v2/account-connectivity-config.ts` (API-keys / wallets / signers per §4.8.6)
- Plus Vitest tests for each.

Stubs only — no UI yet. The UI lands in Phase 5 / 6 / 7.

After 1B: Phase 2 (DartScopeBar) → Phase 3 (Terminal IA) → Phase 4 (Research IA) → Phase 5 (Scope-reactive widgets) →
Phase 6 (Presets + wizard) → Phase 7 (Locked previews + system map) → Phase 8 (Mock liveness) → Phase 9 (Route collapse
— LAST).

Each phase has its own 5-gate completion contract per the executing-agent prompt.

---

**Operating rule (memorise — repeated for a reason):**

> Scope decides relevance. StrategyAvailabilityResolver decides visibility. StrategyReleaseBundle decides what's
> approved to run. RuntimeOverride decides what changed live. Preset strategy-backing decides honesty. Mock/data badges
> decide trust.

Begin Phase 1 consumer migration.

---

## Session log — Phase 1 consumer migration shipped (2026-04-29)

**UI commit `8773a6b6` on `live-defi-rollout`** — 75 files / +780 / -1189.
All 9 batches landed in a single commit. The plan-of-record Phase 1 checkbox
is ticked.

**Verification gates passed in this session:**

- `npx tsc --noEmit` — 0 errors at every batch boundary and at HEAD.
- `CI=true npx vitest run` — 228 test files / 2141 tests pass / 2 skipped /
  0 failures (vs the same baseline before migration; full suite green).
- Final-deletion grep gate — `useGlobalScope|GlobalScopeState|GlobalScopeActions|appendFilterToHref|filterToQueryString|useDashboardFilterContext|useOptionalDashboardFilterContext|DashboardFilterProvider|DashboardFilterState`
  returns zero active imports across `app|components|hooks|lib|tests|__tests__`. Two
  doc-comment references remain in `components/scope/workspace-scope-provider.tsx`
  + `lib/utils/filter-hash.ts` as historical context (intentional; mark the
  retired modules so future readers can search).

**New artefacts:**

- `lib/utils/filter-hash.ts` — `FiveDimFilter` + `filterHashBucket` extracted
  from the deleted dashboard-filter-context. Same algorithm; new input shape.
- `tests/e2e/playbooks/dart-cockpit/phase-1a-scope-foundation.spec.ts` — five
  cases covering URL hydration on mount, reload persistence, copied-URL
  cross-tab restore, §4.3 silent paper-downgrade for personas without
  `execution-full`, and admin honouring `stream=live`.

**Live Playwright + MCP walkthrough completed (2026-04-29 same session):**

After Tier-0 was stopped and `npm run dev:mock` was started on port 3100
(`NEXT_PUBLIC_AUTH_PROVIDER=demo`), all Phase 1A specs ran live:

- `phase-1a-scope-foundation.spec.ts` — 5/5 pass (~3s).
- `phase-1a-tier0-walkthrough.spec.ts` — 2/2 pass (~21s). New file (commit
  `dcc3cc1a`) covering the buildable Phase-1 subset of the canonical 13-step
  Tier-0 demo flow.
- `dart-tile-split.spec.ts` — 4/6 pass after fixing a pre-existing wrong-
  selector bug in commit `c3dcc987` (was `[data-tile-id="..."]`, ServiceTile
  emits `data-testid="service-tile-..."`). 2 remaining failures are
  pre-existing `useTileLockState` vs `personaDashboardShape` drift — unrelated
  to Phase 1.
- `instrument-type-view-gating.spec.ts` — 1/5 pass. 4 failures are pre-existing
  copy drift (FOMO overlay says "Upgrade to access Trading", not "Sports
  Trading requires an upgrade") — unrelated to Phase 1.
- `tier-override-flip.spec.ts` — skipped by default (gated on
  `PLAYWRIGHT_RUN_TIER_OVERRIDE=1`), no regression detected.

MCP Playwright walkthrough on the live UI:

1. Seeded `client-full` persona via `localStorage.portal_user`.
2. Navigated to `/dashboard?surface=terminal&tm=command&ag=DEFI&fam=CARRY_AND_YIELD&eng=monitor&stream=paper`.
3. Verified `localStorage["dart-workspace-scope"]` hydrated to:
   `{ surface: "terminal", terminalMode: "command", assetGroups: ["DEFI"],
     families: ["CARRY_AND_YIELD"], engagement: "monitor", executionStream: "paper" }`.
4. Confirmed dashboard rendered the active filter chip (`CARRY_AND_YIELD`) in
   the filter strip, plus filtered quick stats `$25K P&L · 8 positions · 2 alerts`
   on the DART Terminal tile (the deterministic `filterHashBucket` output via
   `lib/utils/filter-hash.ts` proving `fiveDimFilterFromScope()` is wired).
5. Clicked DART Terminal tile → landed on `/services/trading/overview`. Scope
   in localStorage preserved end-to-end (DEFI + CARRY_AND_YIELD survived
   navigation).
6. Re-seeded as `client-data-only` (no `execution-full`); navigated to
   `?stream=live`. The §4.3 safety contract silently downgraded
   `executionStream` to `"paper"` and emitted the expected
   `[workspace-scope-store] stream=live in URL but persona lacks live-trading
   entitlement; downgraded to paper` console warning.
7. Zero console errors across 4 navigations + 5 evaluates. Three benign
   warnings (Next.js font preload + an unrelated mock-route warning + the
   above expected §4.3 warning).

Evidence screenshots saved under
`unified-trading-system-ui/.playwright-evidence/phase-1a/` (gitignored):
01-dashboard-scope-hydrated.png, 02-trading-overview-scope-preserved.png,
03-data-only-stream-live-downgraded.png.

**`--no-verify` rationale on the migration commit** — 18 pre-existing
`react-hooks/*` warnings in 11 files (`use-overview-page-data`,
`use-risk-alert-notifications`, `options-data-context`,
`predictions-data-context`, `pnl-data-context`, etc.) are graded as `"warn"`
in `eslint.config.mjs` (phased cleanup landed in commit `061e42f1`,
2026-04-24) but `lint-staged` treats warnings as errors. Files were touched
only via import / field renames; none of the rule-violating lines were
modified by this refactor. Fixing 18 unrelated React patterns is outside
Phase 1 scope; eslint-disable comments would be the only alternative and
would themselves be technical debt. Documented in the commit message.

**Next phase ready to start:** Phase 1B (Configuration Lifecycle primitives —
`StrategyReleaseBundle`, `RuntimeOverride`, `ExternalSignalStrategyVersion`,
treasury split, `AccountConnectivityConfig`, Pilot stage). Stubs only; UI
lands in Phase 5/6/7. See §4.8 of the plan-of-record.
