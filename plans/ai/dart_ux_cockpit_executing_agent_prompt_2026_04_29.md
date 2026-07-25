# Execute the DART UX Cockpit Refactor — full completion + full test discipline

You're an implementation agent picking up a 9-phase UX refactor that has been planned in detail. The plan is the
canonical brief; do not re-derive its decisions, do not "boil the ocean", do not skip the agent guardrails, and do NOT
mark a phase done without all three test layers green.

## Definition of "fully complete" — non-negotiable per-phase gates

A phase is NOT complete until ALL of these are green AND the work is pushed to origin/live-defi-rollout:

1. **Unit tests (Vitest):** every new file gets a unit-test sibling. Coverage for the public API surface of the new
   module ≥ 90%. Run with `cd unified-trading-system-ui && CI=true npm test -- --run`.
2. **Type check + lint:** `npx tsc --noEmit` + `npm run lint` clean.
3. **Existing Playwright e2e specs still pass:** `tests/e2e/playbooks/` — especially `dart-tile-split.spec.ts`,
   `instrument-type-view-gating.spec.ts`, `tier-override-flip.spec.ts`. Run with the project's playwright command; never
   `--update-snapshots` without explicit user authorisation.
4. **New Playwright e2e spec for the phase:** every phase introduces at least one new e2e spec under
   `tests/e2e/playbooks/dart-cockpit/` covering the phase's acceptance criteria from the plan.
5. **MCP Playwright Tier-0 demo walkthrough (the "demo prospect" verification):** Use the `mcp__playwright__*` tools to
   drive a real browser through the full Tier-0 demo flow at http://localhost:3000 with the Tier-0 dev stack running.
   Verify that the change feels right end-to-end as a demo prospect would experience it — not just that tests pass.
   Specifics per phase below.
6. **Per-chunk commits + pushes (NO QUICKMERGE):** each logical chunk is its own
   `git add <specific files> && git commit && git push origin live-defi-rollout`. The user has explicitly opted out of
   quickmerge for this programme. Verify dep repos are clean before each push (skip the push if a dep repo is dirty
   unless explicitly authorised).

If any gate fails, stop. Diagnose the root cause. Do NOT skip hooks (--no-verify), do NOT silence type errors with
`// @ts-ignore`, do NOT shortcut the resolver. The plan's §26 guardrails are absolute.

## MCP Playwright Tier-0 demo verification — what this means concretely

Before each phase is marked done, drive a real browser session via `mcp__playwright__browser_navigate` / `_click` /
`_fill_form` / `_snapshot` / `_console_messages` / `_network_requests` and walk the Tier-0 demo flow. The flow must
succeed without console errors, without 4xx/5xx network errors on mocked endpoints, and without visual regressions of
pinned widgets.

**Canonical Tier-0 demo walkthrough (run after every phase, not just Phase 9):**

1. `mcp__playwright__browser_navigate` → `http://localhost:3000/login`
2. Login as `desmondhw@gmail.com` / `demo123` (DART-Full persona).
3. Verify redirect to `/dashboard`. Snapshot the dashboard.
4. Click "DART Terminal" tile. Verify the cockpit loads with the recommended preset.
5. Walk the scope-bar: change asset_group chip, verify scope persistence in URL + on refresh.
6. Toggle Engagement: Monitor → Replicate. Verify the widget bundle swaps without flicker; layout positions preserved.
7. Toggle Stream: Paper → Live. Verify the §4.3 confirm dialog fires; cancel stays paper.
8. Open a locked preview. Verify scope-specific copy.
9. Visit `/help/system-map`. Verify the IA explainer renders and links work.
10. Tier-override flip Desmond DART-Full → Signals-In. Verify Research stages padlock + Signals-In Monitor preset
    surfaces.
11. Logout. Re-login as `patrick@bankelysium.com` (DeFi-Full). Verify DeFi Yield & Risk preset auto-selects.
12. `mcp__playwright__browser_console_messages` — must show zero errors.
13. `mcp__playwright__browser_network_requests` — must show no 4xx/5xx against mock-handler endpoints.

Capture screenshots via `mcp__playwright__browser_take_screenshot` for each phase's acceptance evidence. Save under
`unified-trading-system-ui/.playwright-evidence/phase-<N>/`. Do NOT commit these screenshots (they are evidence for the
user, not the repo).

## Where to find everything

**Workspace root:** `/Users/ikennaigboaka/Code/unified-trading-system-repos/`

**Canonical plan-of-record (read FULLY before writing any code):**

- `unified-trading-pm/plans/active/dart_ux_cockpit_refactor_2026_04_29.plan.md` (~2,500 lines including
  §4.8/§4.9/§4.10/§4.11)

**Canonical codex SSOT:**

- `unified-trading-pm/codex/14-customer-journeys/dart/dart-terminal-vs-research.md`

**New ideal-world reference docs (read selectively per phase):**

- `unified-trading-system-ui/docs/reference/INDEX.md` (start here — has the Platform Comparison pointer back to the
  plan)
- `unified-trading-system-ui/docs/reference/manual-trader-workflow.md`
- `unified-trading-system-ui/docs/reference/common-tools.md` (30 manual surfaces — canonical widget vocabulary for §4.9)
- `unified-trading-system-ui/docs/reference/automation-common-tools.md` (18 automated surfaces + §10.5 Treasury — the
  canonical config split for Phase 1B)
- `unified-trading-system-ui/docs/reference/trader-archetype-sebastian-external-signal-provider.md` (Signals-In
  archetype — read before Phase 1B's ExternalSignalStrategyVersion + before Phase 6's Signals-In Monitor preset)
- `unified-trading-system-ui/docs/reference/trader-archetype-priya-platform-ops-lead.md` (Platform-ops archetype — read
  before any Admin/Ops surface work)

**Strategy taxonomy:**

- `unified-trading-pm/codex/09-strategy/architecture-v2/README.md`
- `unified-trading-pm/codex/09-strategy/architecture-v2/families/`
- `unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/`
- `unified-trading-pm/codex/09-strategy/strategy-summary.md`

**Catalogue artefacts:**

- `catalogue_envelope.md` (workspace root)
- `catalogue_snapshot.md` (workspace root)
- GCS proxy: `unified-trading-system-ui/app/api/catalogue/envelope/route.ts` → consumes
  `gs://strategy-store-cefi-central-element-323112/catalogue/strategy_instruments.json`

**UI codebase you'll be editing:** `unified-trading-system-ui/`

**Branch:** `live-defi-rollout` in both PM and UI repos. Do NOT switch branches. Do NOT use quickmerge.

## Read these in order (~250k tokens of core context — non-negotiable)

1. The plan-of-record — §0 → §26 in FULL. New sections to read carefully:
   - §4.8 Configuration lifecycle (12 config types, StrategyReleaseBundle, RuntimeOverride,
     ExternalSignalStrategyVersion, Pilot stage)
   - §4.9 Widget vocabulary SSOT (canonical surface names from the new reference docs)
   - §4.10 v2 archetype-expansion roadmap (honest v1 vs v2 framing)
   - §4.11 Cross-cutting widget conventions (FreshnessSla, nativeUnit, configBinding)
   - §26 Agent guardrails (every line is non-negotiable)
2. The codex SSOT (`dart-terminal-vs-research.md`).
3. New reference docs (in this order):
   - INDEX.md (pay attention to "Platform Comparison" + "Cross-cutting principle #11 Release artifact as
     system-of-record")
   - manual-trader-workflow.md (the abstraction underneath cockpit modes)
   - common-tools.md (widget vocabulary)
   - automation-common-tools.md (automation vocabulary + §10.5 Treasury)
   - sebastian (Signals-In archetype)
   - priya (Platform-ops archetype)
4. UI repo context:
   - `unified-trading-system-ui/context/AGENT_UI_STRUCTURE.md`
   - `unified-trading-system-ui/context/CONTEXT_GUIDE.md`
5. Existing primitives you'll extend:
   - `unified-trading-system-ui/lib/architecture-v2/envelope-loader.ts`
   - `unified-trading-system-ui/lib/auth/personas.ts`, `lib/auth/persona-dashboard-shape.ts`,
     `lib/auth/tier-override.ts`, `lib/auth/default-landing.ts`
   - `unified-trading-system-ui/lib/config/services.ts`
   - `unified-trading-system-ui/components/shell/service-tabs.tsx`
   - `unified-trading-system-ui/app/(platform)/dashboard/page.tsx`
   - `unified-trading-system-ui/components/platform/page-entitlement-gate.tsx`

## The operating rule (memorise — repeated for a reason)

> **Scope decides relevance.** **StrategyAvailabilityResolver decides visibility.** **StrategyReleaseBundle decides
> what's approved to run.** **RuntimeOverride decides what changed live.** **Preset strategy-backing decides honesty.**
> **Mock/data badges decide trust.**

If you ever find yourself rendering a strategy purely from a scope match without going through the resolver, stop. If
you ever find Terminal mutating strategy logic without producing a new release bundle, stop. If runtime state changes
are silent or untyped, stop.

## The phase plan (sequential, do not interleave)

```
Phase 1A — Unified workspace scope foundation + StrategyAvailabilityResolver
Phase 1B — Configuration Lifecycle primitives (NEW per §4.8):
   StrategyReleaseBundle + RuntimeOverride + ExternalSignalStrategyVersion +
   12-config-object typed registries + Pilot stage in maturity taxonomy.
   Stub registries in lib/architecture-v2/; no UI yet. Lands BEFORE Phase 5
   because Phase 5 widget metadata declares which config object the widget
   binds to (configBinding.reads / configBinding.mutates).
Phase 1C — Bridge old stores (global-scope-store + dashboard-filter-context)
   as @deprecated wrappers. Migrate consumers one-at-a-time.
Phase 1D — Delete old stores after grep + typecheck prove zero remaining
   imports. NEVER skip ahead to 1D.
Phase 2 — Shared DartScopeBar (Surface · Mode/Stage · Engagement · Stream
   + share class chip in primary row)
Phase 3 — Terminal IA (Command · Markets · Strategies · Explain · Ops)
Phase 4 — Research IA (Discover · Build · Train · Validate · Allocate ·
   Promote)
Phase 5 — Scope-reactive widgets via ScopedDataProvider + compatibility
   shims. EVERY DartWidgetMeta carries canonicalSurfaceName from the new
   reference docs (§4.9) + §4.11 conventions (freshnessSla, nativeUnit,
   configBinding, etc.)
Phase 6 — Eight starter presets + four-step wizard (system map → preset →
   scope → mode + engagement + stream)
Phase 7 — Contextual locked previews (LockedPreview model) + /help/system-map
Phase 8 — Mock-mode liveness (MockEventLoop) + replicate-engagement paper
   fills + fake bundle-promotion + fake runtime-override audit trail (so
   demos see the audit feed populate live)
Phase 9 — Route collapse + cleanup (LAST; only after 1-8 stable)
```

Each phase must pass ALL FIVE gates above before the next phase begins.

## Workspace conventions (CLAUDE.md highlights)

- `cd <repo> && bash scripts/quality-gates.sh` for QG (uses repo .venv); never run `pytest` directly.
- `npm test` / `npx tsc --noEmit` for UI.
- **No quickmerge for this programme.** Per-chunk
  `git add <specific files> && git commit && git push origin live-defi-rollout`.
- **Don't push when local dep repos are dirty** unless the user explicitly authorises.
- Cursor checkboxes (`- [x]` / `- [ ]`) on every plan-of-record todo as you complete it (in the plan file at the top —
  that's the visible progress surface).
- `asset_group` is the venue axis (not `category`); dict KEYS stay lowercase (`cefi`/`defi`/...). GCS path segments stay
  literal.

## Agent guardrails (non-negotiable — copied + extended from §26 of the plan)

1. **Do not rename DART Terminal or DART Research.** Surface names locked.
2. **Do not collapse routes before Phase 9.**
3. **Do not default replicate engagement to live execution stream.**
4. **Do not delete `lib/stores/global-scope-store.ts` or `lib/context/dashboard-filter-context.tsx` until Phase 1D.**
5. **Do not migrate widgets in a big bang.** Use the priority order in §11.
6. **Do not turn Strategy Catalogue into a cockpit widget in v1.**
7. **Do not put the IA explainer under Admin.** It's at `app/(platform)/help/system-map/page.tsx` AND wizard step 0.
8. **Do not flatten all Observe pages to Terminal Explain.** Phase 9 redirects map per-page-meaning per the plan's §23
   file table.
9. **Do not break `surface=ops` vs `surface=terminal&tm=ops`.**
10. **Do not skip `ScopeChangeEvent` emission.**
11. **Do not bypass the `StrategyAvailabilityResolver`.**
12. **Do not conflate Catalogue FOMO and Cockpit FOMO.**
13. **Do not advertise "6,000+ strategies".** Combinatoric / configuration space framing only.
14. **Do not make the Volatility Research Lab preset claim more options coverage than Deribit + CME** in v1.
15. **Do not invent a parallel questionnaire-to-scope mapping.** Wizard reuses `seedFiltersFromQuestionnaire`.
16. **Do not let presets render fully-populated cockpits when the resolver returns zero owned + zero
    available_to_request instances.** Show `emptyStateCopy` + a primary CTA.
17. **Do not bypass the StrategyReleaseBundle.** Terminal accepts bundles; it never mutates strategy logic directly.
    Live changes are typed `RuntimeOverride`s within bundle-declared guardrails.
18. **Do not silent-flip live execution.** Every Stream toggle to Live goes through the §4.3 confirm dialog AND the
    persona's live-trading entitlement check.
19. **Do not conflate TreasuryPolicyConfig with TreasuryOperationalConfig.** Policy travels in the bundle (versioned).
    Operations are audited but never bump strategy versions.
20. **Do not let Signals-In personas register external versions without going through the ExternalSignalStrategyVersion
    typed registration.** Idempotency by `(externalVersion, signalId)` is the safety contract.
21. **Do not commit MCP Playwright evidence screenshots to the repo.** They live in `.playwright-evidence/phase-<N>/`
    (gitignored).
22. **Do not run `pytest` directly** anywhere (Python QG uses `bash scripts/quality-gates.sh` per repo).
23. **Do not skip pre-commit hooks (--no-verify, --no-gpg-sign).** Investigate failures, fix root cause, retry.

## Tier-0 dev (must be running before you start)

- `cd unified-trading-system-ui && bash scripts/dev-tiers.sh --status`
- If not running: `bash scripts/dev-tiers.sh --tier 0`
- Dev: http://localhost:3000 · Emulator UI: http://localhost:4000
- Demo persona passwords: `demo123`. Real-email demos:
  - desmondhw@gmail.com (DART-Full ↔ Signals-In tier-override)
  - patrick@bankelysium.com (DeFi-Full ↔ DeFi-Base)
- Mock state mode: `interactive` (persists across sessions)
- Existing Playwright specs to honour:
  - `dart-tile-split.spec.ts`
  - `instrument-type-view-gating.spec.ts`
  - `tier-override-flip.spec.ts`

## Per-phase test deliverables (target file paths)

- Phase 1A:
  - Unit: `lib/stores/__tests__/workspace-scope-store.test.ts`,
    `lib/architecture-v2/__tests__/strategy-availability-resolver.test.ts`,
    `lib/architecture-v2/__tests__/family-filter.test.ts`, `lib/utils/__tests__/nav-helpers.test.ts`
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-1a-scope-foundation.spec.ts`
  - MCP demo: scope persistence across navigate + refresh + copied URL
- Phase 1B:
  - Unit: `lib/architecture-v2/__tests__/strategy-release-bundle.test.ts`,
    `lib/architecture-v2/__tests__/runtime-override.test.ts`,
    `lib/architecture-v2/__tests__/external-signal-strategy-version.test.ts`,
    `lib/architecture-v2/__tests__/treasury-config-split.test.ts`
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-1b-config-lifecycle.spec.ts` (typed object round-trip via JSON in
    localStorage stub)
  - MCP demo: no UI yet — verify console emits expected `recordAudit` calls
- Phase 1C:
  - Unit: every consumer of the deprecated stores gets a migration test
  - MCP demo: same Tier-0 walkthrough as 1A still passes
- Phase 1D:
  - Unit: grep / typecheck proof in CI; no remaining imports
  - MCP demo: full Tier-0 walkthrough still passes
- Phase 2:
  - Unit: `components/shell/__tests__/dart-scope-bar.test.tsx`
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-2-scope-bar.spec.ts`
  - MCP demo: scope bar visible on Dashboard / Terminal / Research / Catalogue / Reports / Signals; Engagement toggle
    reachable in ≤1 click where supported; Live option disabled with tooltip for demo personas.
- Phase 3:
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-3-terminal-modes.spec.ts`
  - MCP demo: Command/Markets/Strategies/Explain/Ops all reachable; arbitrage scope opens arbitrage-relevant Terminal;
    DeFi scope opens DeFi-relevant Terminal.
- Phase 4:
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-4-research-stages.spec.ts`
  - MCP demo: Discover→Promote rail visible; clicking a stage routes correctly with scope preserved.
- Phase 5:
  - Unit: every migrated widget gets a scope-reactivity test
    (`components/widgets/__tests__/<widget>-scope-reactivity.test.tsx`)
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-5-widgets-scope-aware.spec.ts`
  - MCP demo: select Arbitrage → spread/leg/funding widgets become primary; DeFi Yield → protocol/yield/collateral
    widgets become primary; toggle Replicate → manual trade builder widgets fade in for the same strategies.
- Phase 6:
  - Unit: `lib/cockpit/__tests__/presets.test.ts`, `lib/cockpit/__tests__/preset-archetype-map.test.ts`,
    `app/(platform)/onboarding/cockpit/__tests__/wizard.test.tsx`
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-6-presets-wizard.spec.ts`
  - MCP demo: fresh Desmond DART-Full → wizard 4 steps → land in Arbitrage Command preset with 6 widgets pre-arranged.
- Phase 7:
  - Unit: `components/cockpit/__tests__/contextual-locked-preview.test.tsx`,
    `lib/cockpit/__tests__/locked-previews.test.ts`
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-7-locked-previews.spec.ts`
  - MCP demo: Arbitrage scope shows arbitrage-specific locked preview copy; `/help/system-map` renders for authenticated
    users.
- Phase 8:
  - Unit: `lib/api/__tests__/mock-event-loop.test.ts`, `lib/mocks/lifecycle/__tests__/*.test.ts`
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-8-mock-liveness.spec.ts` (uses `?freeze=true` for deterministic
    snapshots)
  - MCP demo: 30-second observation — P&L ticks; alerts arrive; backtest progresses; in Replicate mode, simulated paper
    fills land with realistic slippage.
- Phase 9:
  - E2E: `tests/e2e/playbooks/dart-cockpit/phase-9-route-collapse.spec.ts`
  - MCP demo: typing legacy URL `/services/trading/positions` redirects to
    `/services/workspace?surface=terminal&tm=command&...` with scope intact; legacy bookmarks don't break.
  - Final 9-phase regression: full Tier-0 demo walkthrough end-to-end.

## Companion deliverables (HUMAN-tagged in plan-of-record — do NOT auto-apply)

- IR presentation copy alignment (§25.A.2)
- Public website copy alignment (§25.A.3)
- PM codex + UI repo doc propagation (§25.A.7)
- Phase 9.5 evaluation track — comparison docs per archetype cluster (DART-as-it-is vs Marcus / Sasha / Julius / Diego /
  Aria / Elena / Sebastian / Priya ideal-world). Not blocking; surface findings as you go.

These are HUMAN-tagged in the plan-of-record's todo list. Don't auto-apply them as code edits unless the user explicitly
asks.

## Phase 1 starts here

Read the plan in FULL first (§0 → §26). Then read the new reference docs (INDEX → manual-trader-workflow → common-tools
→ automation-common-tools including §10.5 Treasury → sebastian → priya). Then:

1. Use TodoWrite to set up phase-level todos: Phase 1A → 1B → 1C → 1D → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 With explicit
   sub-todos per phase: implement → unit tests → e2e spec → MCP Playwright Tier-0 walkthrough → commit & push.
2. Verify Tier-0 dev is running (or start it).
3. Verify dep repos are clean (`git status` per repo) before any push. Stop and report if any are dirty unless user
   authorises.
4. Start with Phase 1A:
   - Create `lib/stores/workspace-scope-store.ts` (NEW Zustand store + URL hydrate/serialise + localStorage fallback +
     `ScopeChangeEvent` emission via `lib/analytics/track.ts`).
   - Create `lib/architecture-v2/strategy-availability-resolver.ts` (NEW — returns
     `StrategyVisibilityDecision { visibility, reason, cta, coverageQualifier }` per §4.5).
   - Add `linkWithScope()` in `lib/utils/nav-helpers.ts`.
   - Wrap `app/(platform)/layout.tsx` in `<WorkspaceScopeProvider>`.
   - Extend `lib/architecture-v2/catalogue-filter.ts` with the full scope schema (5 filter axes + share class +
     surface + mode + stage + engagement + stream + advanced axes).
   - Generalise `lib/architecture-v2/family-filter.ts::matchesFamily` → `matchesScope(row, scope)`.
5. Run all five gates (unit / typecheck / existing e2e / new e2e / MCP Tier-0 walkthrough). Capture screenshots under
   `.playwright-evidence/phase-1a/`.
6. Commit + push (per-chunk; do not batch). Use a descriptive message referencing §17 Phase 1A and §4.5 resolver.
7. Tick the Phase 1A checkbox in the plan-of-record at the top of
   `unified-trading-pm/plans/active/dart_ux_cockpit_refactor_2026_04_29.plan.md` (use Edit tool; commit + push the plan
   tick separately to PM repo).
8. Move to Phase 1B — Configuration Lifecycle primitives (StrategyReleaseBundle, RuntimeOverride,
   ExternalSignalStrategyVersion, treasury config split, AccountConnectivityConfig, Pilot stage). Stubs only — no UI
   yet.

When in doubt, re-read the plan. Do NOT skip the new §4.8 — it's the configuration spine that Phase 5 widget metadata,
Phase 6 presets, Phase 7 locked previews, and Phase 9 route collapse all depend on.

**Operating rule again, because it matters:**

> Scope decides relevance. StrategyAvailabilityResolver decides visibility. StrategyReleaseBundle decides what's
> approved to run. RuntimeOverride decides what changed live. Preset strategy-backing decides honesty. Mock/data badges
> decide trust.

Begin.
