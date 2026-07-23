---
doc_type: plan
title: DART UX Refactor — From Route Tree to Guided Cross-Asset Trading Cockpit
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-29
owner: ikenna
archived: 2026-05-07
codex_ref: /codex/14-playbooks/dart/dart-terminal-vs-research.md
supersedes:
  /codex/14-playbooks/dart/dart-terminal-vs-research.md (tile-split mechanics — shipped commits a36a9889 → 0754cd3c).
  This plan addresses the structural reasons the navigation still feels like a headache instead of FOMO.
superseded_by: plans/active/strategy_and_dart_master_2026_05_07.md
---

## Deferred work — migrated to: `plans/epics/dart_and_promote_master.md` — successor:

dart_and_promote_master (the current active L3 epic owning DART operator UX). The frontmatter's original
`superseded_by: plans/active/strategy_and_dart_master_2026_05_07.md` is stale — that umbrella was itself superseded
2026-05-21 and split into `strategy_master.md` (L2, strategy engine) + `dart_and_promote_master.md` (L3, DART UX +
promote workflow); the 7 residual open items here (widget vocabulary SSOT, cross-cutting widget conventions, layer-2
proof signals, v2 archetype-expansion roadmap, doc/IR/website copy alignment) are DART operator-UX concerns inherited by
the latter.

> **ARCHIVED 2026-05-07** — folded into
> [`strategy_and_dart_master_2026_05_07.md`](../active/strategy_and_dart_master_2026_05_07.md). All open todos preserved
> in the umbrella's Phase 1-3. This file is the historical SSOT.

# DART UX Refactor — From Route Tree to Guided Cross-Asset Trading Cockpit

## Plan-of-record todos (Cursor checkboxes — 9-phase programme)

- [x] [AGENT] P0. **Phase 1** — Unified workspace scope (`WorkspaceScopeStore` + URL contract + `linkWithScope` +
      legacy-store deletion). Foundation primitives shipped UI commit `aeb16db7`; consumer migration + final deletion
      shipped `8773a6b6` (75 files / 780 insertions / 1189 deletions); existing-spec selector fix `c3dcc987`; Phase 1A
      Tier-0 walkthrough spec `dcc3cc1a`. Verified end-to-end on `npm run dev:mock` (port 3100): 0 typecheck errors; 228
      vitest files / 2141 tests pass; 0 active imports of the deleted modules. Phase 1A e2e (7 specs across
      `tests/e2e/playbooks/dart-cockpit/`): all pass — URL hydration + reload persistence + cross-tab restore + §4.3
      live-stream safety contract + Tier-0 walkthrough (dashboard → terminal → scope persistence). MCP Playwright
      walkthrough on the live cockpit confirmed: dashboard renders with `CARRY_AND_YIELD` chip in the filter strip
      (proving DashboardFilterStrip reads `scope.families[0]` post-migration), filtered quick stats `$25K/8/2`
      (`filterHashBucket` via `lib/utils/filter-hash.ts`), scope survives navigation into `/services/trading/overview`,
      `?stream=live` silently downgrades to `paper` for `client-data-only`, zero console errors across 4 navigations.
      See §17 + §23.
- [x] [AGENT] P0. **Phase 2** — Shared `DartScopeBar` rendered on Dashboard, Terminal, Research, Catalogue, Reports,
      Signals. Shipped UI commit `769df754`. Component at `components/shell/dart-scope-bar.tsx` + summary helper at
      `components/shell/dart-scope-bar-summary.ts`. Compact mode = one-line §6 summary; expanded mode = Surface dial
      (cascades into TerminalMode when surface=terminal / ResearchStage when surface=research) + Engagement +
      ExecutionStream toggles + active-filter chip readout + Reset button. §4.3 Live confirm dialog fires on Paper →
      Live for entitled personas; Cancel keeps paper; persona without `execution-full` sees Live as `aria-disabled` with
      tooltip "Live execution is unavailable on demo accounts." Mounted on dashboard + 6 service layouts (signals layout
      NEW). 30 unit tests + 10 e2e tests on dev:mock all pass; 17/17 dart-cockpit e2e regression-clean. Chip-editing
      affordance for asset_group / family / archetype deferred to Phase 5 (current bar reads-only).
- [x] [AGENT] P0. **Phase 3** — Terminal IA simplification → five buyer-facing modes (Command · Markets · Strategies ·
      Explain · Ops). Shipped UI commit `8c6e84af`. New primitives at `lib/cockpit/terminal-modes.ts` (mode
      enumeration + `terminalModeForPath` longest-prefix resolver + `defaultTerminalMode`) and
      `components/cockpit/terminal-mode-tabs.tsx` (5-tab primary nav with route-driven active-mode resolution + route →
      scope auto-sync). Mounted above the existing TradingVerticalNav in `services/trading/layout.tsx` and above
      OBSERVE_TABS in `services/observe/layout.tsx`. Old routes preserved as deep links — the legacy TRADING_TABS sprawl
      still renders below the new mode-tabs. 26 unit tests + 6 e2e tests pass; 23/23 dart-cockpit e2e regression-clean.
      Phase 9 retires the legacy per-route pages with redirects.
- [x] [AGENT] P0. **Phase 4** — Research IA simplification → six journey stages (Discover · Build · Train · Validate ·
      Allocate · Promote). Shipped UI commit `85300c46`. New primitives at `lib/cockpit/research-stages.ts` (stage
      enumeration + `researchStageForPath` longest-prefix resolver + `defaultResearchStage`) and
      `components/cockpit/research-journey-rail.tsx` (horizontal journey rail with numbered chips connected by progress
      arrows so the user reads the lifecycle as a left-to-right narrative). Mounted above the existing BUILD_TABS in
      `services/research/layout.tsx`. Old BUILD_TABS / STRATEGY_SUB_TABS / ML_SUB_TABS routes preserved as deep links.
      26 unit tests + 6 e2e tests pass; 29/29 dart-cockpit e2e regression-clean. Phase 9 retires the legacy per-route
      pages.
- [x] [AGENT] P0. **Phase 5** — Scope-reactive widgets via `useScopedData()` + `DartWidgetMeta` extension on
      `WidgetDefinition` + `widgetsForScope()` selector + auto-derived defaults from legacy `assetGroup` field. Shipped
      UI commit `2cbe4a46`. `lib/cockpit/widget-meta.ts` ships `matchWidgetToScope()` +
      `synthesiseDartMetaFromAssetGroup()`. `components/widgets/_data/use-scoped-data.ts` ships the unified hook +
      slice-merging compatibility shims. `OutOfScopePlaceholder` renders the greyed "out of scope" affordance. The
      auto-deriver gives scope-reactive behavior across the entire registry without per-file churn (incremental
      explicit-dartMeta annotation is a long-tail follow-up). 36 unit tests pass.
- [x] [AGENT] P0. **Phase 6** — Eight starter cockpit presets + persona-recommended starter (UI commit `2d4bb3a2` for
      primitives + `375d69d2` for the visible UI). All 8 presets shipped with full metadata (Executive Overview · Live
      Trading Desk · Arbitrage Command · DeFi Yield & Risk · Volatility Research Lab · Sports/Prediction Desk ·
      Signals-In Monitor · Research-to-Live Pipeline). 6 of 8 support both monitor + replicate; replicate-default always
      paper per §4.3. Vol Lab pins v1 venues to `["DERIBIT", "CME"]`. `lib/cockpit/derive-preset-from-persona.ts`
      provides 4-tier resolution (persona-id → role band → entitlement-derived → conservative default).
      `<PresetSelector />` mounted on /dashboard shows recommended preset badged + leading. Full 4-step wizard UI
      deferred to a follow-up — the persona-recommended preset is already selectable directly from /dashboard, which
      closes the same demo gap.
- [x] [AGENT] P0. **Phase 7** — Contextual locked previews + `/help/system-map`. Shipped UI commit `375d69d2`.
      `lib/cockpit/ia-explainer-content.ts` is the SSOT for IA copy (6 surfaces + 5 Terminal modes + 6 Research stages +
      ownership table). `<SystemMap />` mounted at `/help/system-map` (authenticated, platform-scoped).
      `lib/cockpit/locked-previews.ts` ships 5 scope-aware previews (Arbitrage Promotion Checks · DeFi Yield Research ·
      Vol Lab · Signal Quality Analytics · Sports Execution Sim) with `scopeMatch` predicates.
      `<ContextualLockedPreview />` renders on /dashboard. CTAs route to /help/system-map per the single-help-surface
      design.
- [x] [AGENT] P0. **Phase 8** — Mock-mode liveness primitives. Shipped UI commit `375d69d2`.
      `lib/cockpit/mock-event-loop.ts` ships `MockEventLoop` (subscribe / start / stop / freeze) + 5 curated
      `DEFAULT_DRIFT_PROFILES` (P&L · exposure · alerts · positions · BTC price) with bounded mean-reverting random
      walks. Mulberry32 deterministic PRNG so screenshots reproduce. `?freeze=true` and `?pace=N` URL hooks ready.
      Per-widget subscription wiring is incremental — widgets call `loop.subscribe()` to opt in.
- [x] [AGENT] P0. **Phase 9** — Route-redirect map + unified workspace shell (LAST). Shipped UI commits `375d69d2`
      (route-redirect table SSOT), `f6922b8f` (unified `/services/workspace` shell + ReleaseBundlePanel +
      CockpitWidgetGrid + dashboard tile redirects), `5abf8182` (RuntimeOverride authoring + 8 next.config observe
      redirects). `lib/cockpit/route-redirects.ts` ships `COCKPIT_ROUTE_REDIRECTS` (24 mappings) +
      `cockpitAnchorForPath()` longest-prefix resolver + `isCataloguePath()` guard (Strategy Catalogue stays distinct
      per §22). Dashboard tiles now route directly into the cockpit shell:
      `dart-terminal → /services/workspace?surface=terminal&tm=command`,
      `dart-research → /services/workspace?surface=research&rs=discover`. The cockpit shell renders DartScopeBar +
      surface-contextual primary nav (TerminalModeTabs / ResearchJourneyRail) + scope-summary header + CockpitWidgetGrid
      (`widgetsForScope().primary` 12-tile bucket) + ReleaseBundlePanel (immutable bundle visualisation on Strategies /
      Explain / Promote — DEMO_BUNDLE = ARBITRAGE_PRICE_DISPERSION v3.2.1 with 9 version pins, 4 validation-evidence
      badges, 6 guardrail flags, 2 active runtime overrides) + RuntimeOverrideAuthoring (8-type discriminated form on
      Command / Strategies with live `validateOverrideAgainstGuardrails` keystroke feedback + 8 typed rejection-code
      messages). Phase 9 `next.config.mjs` ships 8 observe-route redirects (risk/scenarios/position-recon → tm=explain;
      alerts → tm=command; strategy-health → tm=strategies; system-health/event-audit/recovery → tm=ops). MCP validated:
      `/services/observe/risk → /services/workspace?surface=terminal&tm=explain`; size_multiplier 1.5× blocked with
      `size_multiplier_above_one`; size_multiplier 0.5× + reason ≥8 chars allowed with submit enabled. Strategy
      Catalogue NOT collapsed — stays universe surface.
- [x] [AGENT] P0. **Configuration lifecycle UI surfaces — Promote / Explain / Admin** (§4.8 buyer-facing). Shipped UI
      commit `64fd8db7`. Closes the lifecycle visibility loop: a buyer sees the typed primitives end-to-end as Promote
      (research → bundle creation) → Bundle (immutable, read-only) → Override authoring (live, audited,
      guardrail-validated) → Explain attribution (bundle + override deltas → realised) → Admin Operational config
      (Treasury routing + Connectivity). Components: `components/cockpit/promote-bundle-form.tsx` (Research/Promote — 12
      version pins + validation evidence + guardrail toggles + 3 live pre-flight gates using
      `hasCefiAccountsForVenues` + `hasDefiWalletsForProtocols`); `components/cockpit/explain-attribution-panel.tsx`
      (Terminal/Explain — three-column side-by-side bundle + overrides + realised, implements §4.8.3 rule 2 forbidding
      hidden overrides); `components/cockpit/admin-operational-config-panel.tsx` (Terminal/Ops + surface=ops —
      `TreasuryOperationalConfig` + `AccountConnectivityConfig` with status-coloured badges across CeFi accounts / DeFi
      wallets / signer profiles / outbound endpoints). Demo fixtures (`lib/cockpit/demo-bundle.ts`):
      `DEMO_TREASURY_OPERATIONAL` (3 wallets + binance settlement venue) + `DEMO_CONNECTIVITY` (3 CeFi accounts incl.
      okx degraded, 3 DeFi wallets, 2 signer profiles, 1 Signals-Out endpoint). MCP-validated: Promote gates
      cefiOk/defiOk/evidenceOk all green → submit enabled; Explain attribution bundle +$18.4K + overrides −$10.1K =
      realised +$8.4K with 2 itemised override rows; Admin renders 3/3 CeFi (1 degraded), 3 DeFi wallets, 2 signers, 1
      outbound.
- [x] [AGENT] P0. **Persona-walkthrough Playwright matrix** — 6 personas validated, distinct cockpit configurations
      captured. Switched via demo provider's `localStorage.portal_user` shape: (1) prospect-dart-full @ Terminal/Command
      on CeFi+DeFi/Arbitrage/PriceDispersion → 12 primary widgets, RuntimeOverrideAuthoring rendered
      (`persona-1-prospect-dart-full-arbitrage-command.png`). (2) prospect-dart-signals-in @ surface=signals → cockpit
      shell renders empty-state widget grid (no widgets tagged `surfaces:["signals"]` yet — incremental dartMeta
      annotation deferred) (`persona-2-signals-in.png`). (3) investor @ Reports → 12 widgets / 72 out of scope
      (`persona-3-investor-reports.png`). (4) prospect-im @ Research/Allocate → ResearchJourneyRail with Allocate stage
      active, **Live stream toggle shows lock icon** because IM persona lacks `execution-full` entitlement (§4.3 safety
      contract enforced) (`persona-4-im-prospect-allocate.png`). (5) prospect-regulatory @ Reports → Live stream
      lock-icon enforced; cockpit-shell renders normally (`persona-5-regulatory-reports.png`). (6) admin @ surface=ops →
      AdminOperationalConfigPanel renders with full 3 CeFi + 3 DeFi + 2 signers + 1 outbound; Live stream NOT locked
      (admin entitlement = ["*"]) (`persona-6-admin-ops-surface.png`).
- [x] [AGENT] P0. **Phase 1A foundational primitive** — `StrategyAvailabilityResolver` (§4.5). Returns
      `{ visibility, reason, cta, coverageQualifier }`. Shipped UI commit `aeb16db7` (foundation) alongside the unified
      `WorkspaceScope`. 18 unit tests passing in `tests/unit/lib/architecture-v2/strategy-availability-resolver.test.ts`
      cover the eight persona classes (admin / internal-trader / im-desk-operator / dart-full / signals-in / im-client /
      regulatory / prospect).
- [x] [AGENT] P0. **Phase 1B foundational primitive — Configuration Lifecycle** (§4.8). Shipped UI commit `a4c990e8`
      (re-pushed `24a193a8` post-rebase). Five typed primitives + state-machine helpers + guardrail validators:
      `StrategyReleaseBundle` (immutable promotion artifact,
      `draft → candidate → approved_for_paper → paper →     approved_for_pilot → pilot → approved_for_live → live → monitor → retired`
      state machine), `RuntimeOverride` (typed discriminated union of 8 override types —
      `size_multiplier / venue_disable / execution_preset /     risk_limit_tightening / treasury_route / pause_entries / exit_only / kill_switch`
      — with typed guardrail rejection codes), `ExternalSignalStrategyVersion` (Signals-In path with its own state
      machine + idempotency-by- version-tag helper), `TreasuryPolicyConfig` (versioned, bundles into release bundle) +
      `TreasuryOperationalConfig` (audited, unversioned), `AccountConnectivityConfig` (CeFi accounts + DeFi wallets +
      signer profiles + outbound endpoints + `hasCefiAccountsForVenues` / `hasDefiWalletsForProtocols` Promote
      validation gates). Added `pilot` + `monitor` to `StrategyMaturityPhase`; updated `allowsAllocationCta` to include
      both. 6 new spec files / 77 tests passing; full vitest sweep 234 files / 2218 tests pass / 2 skipped. 0 typecheck
      errors. Stubs only — UI lands in Phase 5 / 6 / 7.
- [ ] [AGENT] P0. **Phase 5 widget vocabulary SSOT** (§4.9). Every `DartWidgetMeta.id` maps 1:1 to a canonical surface
      name from `unified-trading-system-ui/docs/reference/common-tools.md` (30 manual surfaces) or
      `automation-common-tools.md` (18 automated surfaces). Phase 5 ships with a `canonicalSurfaceName` field; v2
      archetype expansion reuses widgets without rename churn.
- [ ] [AGENT] P0. **Cross-cutting widget conventions** (§4.11). Ten conventions propagated as `DartWidgetMeta`
      extensions (`freshnessSla`, `nativeUnit`, `drilldownScope`, hotkey contract, audit-on-mutate, replay-time-binding,
      etc.). Lands alongside Phase 5.
- [ ] [AGENT] P0. **Layer 2 minimum proof signals** — six irreducible badges (data-freshness pill, last-update
      timestamp, maturity badge, visibility-state badge, demo-data badge, report/reconciliation placeholder link). Built
      alongside Phases 7-8. Add **two more** post-§4.8: **release-bundle audit pill** (current strategy version + active
      runtime overrides count) and **reproducibility pill** (training data hash known / unknown).
- [ ] [HUMAN] P1. **v2 archetype-expansion roadmap** (§4.10). Honest framing: v1 = 8 presets covering 6 archetype
      clusters; v2 names 7 missing archetype presets (Market-Making · Equity LS · Rates · Macro · FX · Energy ·
      Event-Driven) + Firm-Risk Aggregate Console for David. Not blocking v1.
- [ ] [HUMAN] P0. **Doc alignment** (§25.A.7) — propagate vocabulary into PM codex (`14-playbooks/dart`,
      `14-playbooks/audiences-and-journeys`, `09-strategy/architecture-v2/*`, `08-workflows/*`, `02-data/*`,
      `GLOSSARY.md`, `00-SSOT-INDEX.md`) + UI-repo docs (`context/AGENT_UI_STRUCTURE.md`, `context/CONTEXT_GUIDE.md`,
      `context/CONFIG_REFERENCE.md`, `docs/TIER_ZERO.md`).
- [ ] [HUMAN] P1. **IR presentation copy alignment** (§25.A.2) — board / platform / investment / plan decks +
      competitive-landscape SSOT + briefings YAML + `service-labels.ts`.
- [ ] [HUMAN] P1. **Public website copy alignment** (§25.A.3) — homepage metadata + `_home-client.tsx`
      Hero/MarketsUniverse/EngagementRoutes/WhyOdum + DART platform page + our-story.

> **Status:** Plan-of-record. Authored 2026-04-29. Supersedes `dart_terminal_research_split_2026_04_28.md` (tile-split
> mechanics shipped; UX-level refactor is this plan's scope).
>
> **Source synthesis:** This plan combines two inputs:
>
> 1. The codebase audit (Phase 1 of this planning round) — concrete file-and-line evidence of the headache.
> 2. A buyer-emotional spec from a parallel agent — the right naming, the right phase ordering, the right ownership
>    rules. The user supplied it and chose it as the framing.
>
> **Supersedes:** the prior tile-split mechanics plan (which shipped in commits `a36a9889` → `0754cd3c`). That work
> delivered the _technical_ split. This proposal addresses the structural reasons the navigation still feels like a
> headache instead of FOMO.

---

## 0. Executive summary

Refactor DART so it stops feeling like a collection of pages and starts feeling like the institutional trading
**operating layer** Bloomberg, Aladdin, execution systems, and fund-admin stacks were never designed to be in one
product.

The killer narrative is the **continuity**:

> Catalogue → Research → Backtest → Paper → Promote → Live → Monitor → Explain → Report

across **CeFi · DeFi · TradFi · Sports · Prediction markets**, all under **one shared scope**:

> asset_group · instrument_type · strategy_family · archetype · share_class · venue · mandate · surface · engagement ·
> execution_stream

That is the wedge. Most platforms are strong in one slice — Bloomberg owns data + connectivity; Aladdin owns portfolio +
risk; Haruko owns crypto treasury visibility; fund admins own NAV + investor reporting; execution vendors own routing;
quant platforms own research + backtesting. **Odum's possible wedge is the unification:** _"We unify the strategy
lifecycle and operating model across markets that usually live in separate systems."_

The current product has strong ingredients but the experience is too fragmented for that wedge to land:

- filters are partly cosmetic;
- scope does not reliably persist across pages;
- DART Terminal and DART Research expose too many destinations;
- widgets are not consistently scope-aware;
- users are asked to configure before seeing value;
- locked states do not create enough FOMO;
- mock mode feels too static;
- public website promises continuity that signed-in pages don't visibly deliver (see §27 audit).

The refactor should make the user feel:

> _"This is the cross-asset strategy operating layer we would otherwise need to build ourselves."_

Not:

> _"This is powerful, but I need to understand 50 pages before I can use it."_

### Three layers needed for institutional trust (not just FOMO)

Experience FOMO alone is not enough. To make institutions truly jealous, three layers must align:

1. **Layer 1 — Experience** (what this plan delivers): one cockpit, one scope, one lifecycle.
2. **Layer 2 — Proof** (must accompany the rollout): live strategies running; real venue integrations; actual reporting
   outputs; realistic permissions; audit trails; reconciliations; data freshness; incident handling; demo scenarios that
   match real buyer use cases.
3. **Layer 3 — Distribution trust** (org-level, not UI): regulatory posture (FCA permission, scope of activity);
   client-data handling; live-execution controls; permissioning seriousness; reporting integrity; operational risk
   management.

The UI creates the emotional pull. The proof and controls close the deal. **Phases 1-9 of this plan are Layer 1.** Layer
2 needs operational evidence woven into the cockpit (live status indicators, audit trail surfaces, reconciliation
widgets). Layer 3 needs visible-but-discreet trust signals (FCA badge, risk-utilisation pill, last-trade timestamp) on
every signed-in surface.

**Minimum Layer 2 proof signals for v1 cockpit** (lightweight; built alongside Phase 7-8 to prevent the cockpit becoming
pure theatre):

- **Data-freshness pill** in the cockpit header (e.g. _"Market data: 2s old"_ / _"Reference data: T+1 06:00"_ — already
  partially exists per `data-pro` entitlement; promote to header).
- **Last mock/live update timestamp** on widgets that display values (footer caption: _"Updated 14:23:08"_).
- **Strategy maturity badge** on every strategy card (smoke / backtest / paper / live-stable — sourced from the §4.5
  resolver).
- **Visibility-state badge** for non-owned strategies surfaced via FOMO (locked / available-to-request / read-only /
  IM-reserved).
- **"Demo data" badge** persistent on every preset whose resolver returns zero `owned` instances (covers Executive
  Overview's empty state and any preset rendering placeholder data).
- **Report / reconciliation placeholder link** in Explain mode where owned data exists (links to the deeper Reports
  surface; empty state otherwise).

These six signals are the irreducible Layer 2 minimum. Without them the cockpit looks alive but cannot prove it's live;
with them the demo prospect can answer _"is this real?"_ without leaving the screen.

### Strategy universe — combinatoric vs available

Don't claim "6,000+ strategies are live" anywhere visible to a buyer. The actual numbers per the strategy-architecture
audit:

- Combinatoric configuration space (asset*group × family × archetype × venue × tenor × style × ...): **6,000+
  permutations** — this is the \_potential* the system can express.
- Existing strategies mapped to v2: **~53**.
- UAC catalogue seed instances: **~84-99** (varies by doc revision).
- Near-term live + paper: **~70-80 active instances**.
- v1 catalogue ceiling target: **~240-250**.
- Hard ceiling (architecturally): **~300-350**.

Use 6,000+ only as **"potential configuration space"** in copy, never as "available strategies". Sophisticated buyers
will smell exaggeration. The honest framing is _"the strategy universe is combinatoric, but the visible catalogue is
curated by maturity, routing, availability, and entitlement — what you see is what we'll actually let you use."_

### The 7 make-or-break pieces

The bar is high. If implementation is half-done, the cockpit looks worse than a simpler product because it promises an
operating system and delivers a maze. The make-or-break gates:

1. **Scope must actually work everywhere.** No cosmetic filters; no parallel stores; URL round-trips on every
   navigation.
2. **Presets must feel curated, not decorative.** Six of eight presets carry both monitor + replicate engagement; widget
   bundles are tuned per persona.
3. **Widgets must genuinely change with context.** Filter chip flips → cockpit reshapes → mock data swaps. Not a
   hide/show toggle on a static layout.
4. **Locked previews must create desire.** Scope-specific copy (arbitrage user sees arbitrage value; DeFi user sees DeFi
   value); not generic "upgrade".
5. **Mock/demo mode must feel alive.** Backtests progress; alerts arrive; P&L drifts; replicate-mode paper fills
   realistically.
6. **Research-to-live must feel continuous.** Same scope, same widgets, same vocabulary from Discover → Validate →
   Promote → Live → Explain. Strategy promotion is a config flip, not a re-platform.
7. **Reporting and Explain must be strong enough to prove institutional seriousness.** Not just "we ran the trade" —
   also "here's why P&L happened, where execution leaked, what changed from backtest, what the client sees."

Nail those seven and the product reads less like another crypto dashboard and more like a serious cross-asset operating
system. Miss any one and the demo collapses into a maze.

---

## 1. Audit evidence (codebase grounding for the plan below)

The headache is not vibes — it's structural. The audit (parallel Explore agents over the live `live-defi-rollout`
branch) ranked these P0/P1 issues:

| #   | Severity | Headache                                                                                                                                           | Anchor file                                                                                   |
| --- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| 1   | P0       | URL `?family=X` is appended to chip hrefs by `appendFilterToHref()` but no consumer parses it.                                                     | `lib/context/dashboard-filter-context.tsx`                                                    |
| 2   | P0       | `DashboardFilterContext` and `GlobalScopeStore` are parallel and never sync.                                                                       | `lib/stores/global-scope-store.ts` + `lib/context/dashboard-filter-context.tsx`               |
| 3   | P0       | Observe / reports / strategy-catalogue pages don't read global scope, don't parse URL, don't have their own filter bar.                            | `app/(platform)/services/observe/**/page.tsx`                                                 |
| 4   | P0       | Five layout trees (trading, observe, research, signals, strategy-catalogue) — widgets don't follow you between them.                               | `app/(platform)/services/{trading,observe,research,signals,strategy-catalogue}/layout.tsx`    |
| 5   | P0       | Widgets are hard-coded to single asset_group via context (`useOptionsData`, `useDeFiData`, `useSportsData`, `usePredictionsData`); no filter prop. | `components/widgets/{options,defi,sports,predictions}/*-data-context.tsx`                     |
| 6   | P0       | `FamilyArchetypeAssetGroupBrowser` keeps `activeFamily`/`activeArchetype` in local React state on each of 5 pages; selections don't cascade.       | `app/(platform)/services/research/_components/family-archetype-asset-group-browser.tsx:55-56` |
| 7   | P1       | 60+ widgets, no role-based presets, no starter layouts. New users assemble manually from a flat drawer.                                            | `components/widgets/widget-catalog-drawer.tsx`                                                |
| 8   | P1       | `assigned_strategies` declared on every persona, consumed by zero pages.                                                                           | `lib/auth/personas.ts`                                                                        |
| 9   | P1       | `lib/questionnaire/seed-catalogue-filters.ts` exists; zero callers wire it into anything.                                                          | `lib/questionnaire/seed-catalogue-filters.ts`                                                 |
| 10  | P1       | Mock mode is deterministic — same data every refresh. Backtests don't progress, signals don't arrive, P&L is frozen.                               | `lib/api/mock-handler.ts`, `lib/mocks/fixtures/mock-data-seed.ts`                             |

Sub-route counts (also from audit): 16 trading-domain tabs visible at once + 9 observe + 13 strategy sub-tabs + 8 ML
sub-tabs + 11 research top-level = roughly **57 distinct destinations** within DART today. That's the sprawl the user is
describing as a headache.

---

## 2. Product target

DART should feel like a guided cross-asset trading operating system spanning crypto / CeFi, DeFi, TradFi, sports
markets, prediction markets, research, backtesting, signal intake, paper/live trading, risk, execution monitoring, P&L
attribution, reporting, and ops.

But the user should **not** feel all of that at once. Complexity progressively reveals based on context.

The user should be able to say:

> _"I am looking at Arbitrage across BTC/ETH spot and perps on CeFi and DeFi in demo/live mode."_

and the UI responds by showing arbitrage-relevant widgets, candidates, P&L attribution, execution leakage, locked
previews, research paths, and reports. The scope **reshapes the product**. It does not merely filter a table.

---

## 3. Desired emotional feel

### 3.1 Powerful but calm

Bad: _"Here are 50 destinations. Pick one."_ Good: _"You are in Arbitrage Command. Here are the live spreads, leg state,
hedge state, execution quality, P&L, and exceptions that matter right now."_

### 3.2 Curated before customizable

A new user should not see _"Add widgets to configure your workspace."_ They should see _"Recommended cockpit: Arbitrage
Command. Based on your access and selected interests."_ Customization comes after value.

### 3.3 Context-aware

Selecting **Arbitrage** makes the product feel like an arbitrage product. Selecting **DeFi Yield** makes it feel like a
DeFi yield product. Selecting **Signals-In** makes it feel like a signal intake / routing / execution / reporting
product. This is the core magic.

### 3.4 Institutional, not generic SaaS

**Use:** Command · Markets · Strategies · Explain · Ops · Promotion readiness · Execution quality · Risk state · Venue
health · P&L attribution · Research-to-live path · Configuration versions · Signal freshness. **Avoid:** Manage
workflows · Explore features · Configure modules · Productivity tools.

---

## 4. Core design principle — Scope is the control plane

Scope means the user's selected trading context. It must be real, visible, persistent, and globally consumed.

```ts
type WorkspaceScope = {
  // Five filter axes (the user's mental model)
  assetGroups: string[]; // e.g. ["CEFI", "DEFI", "TRADFI", "SPORTS", "PREDICTION_MARKETS"]
  instrumentTypes: string[]; // e.g. ["spot", "perp", "future", "option", "lending_position"]
  families: string[]; // e.g. ["ARBITRAGE_STRUCTURAL", "CARRY_AND_YIELD", "VOL_TRADING"]
  archetypes: string[]; // e.g. ["PRICE_DISPERSION", "CARRY_BASIS_PERP"]
  strategyIds: string[]; // explicit or derived strategies
  venueOrProtocolIds?: string[]; // e.g. ["binance", "okx", "aave", "uniswap"]
  accountOrMandateId?: string;

  // Top-level foreground product area (replaces the legacy single `mode` field
  // — separates "which surface" from "which mode within Terminal" cleanly).
  surface: "dashboard" | "terminal" | "research" | "reports" | "signals" | "ops";

  // DART Terminal foreground mode (only meaningful when surface === "terminal")
  terminalMode?: "command" | "markets" | "strategies" | "explain" | "ops";

  // DART Research foreground stage (only meaningful when surface === "research")
  researchStage?: "discover" | "build" | "train" | "validate" | "allocate" | "promote";

  // 2026-04-29: HOW the user is engaging with their strategies
  engagement: "monitor" | "replicate";
  // - "monitor"   → strategy runs automatically; user supervises (kill switches,
  //                  alerts, exception triage, execution-quality / P&L
  //                  attribution). Default for production.
  // - "replicate" → user walks through the strategy themselves, leg by leg.
  //                  Cockpit surfaces step-by-step trade builder, manual
  //                  order entry with venue-routing helpers, leg tracker,
  //                  hedge calculator, paper-vs-live toggle. Used for demo
  //                  walkthroughs, training, validation-before-automation.

  // Where fills actually go. Default `paper` for replicate; live requires an
  // explicit confirm dialog and is disabled for mock/demo personas without
  // live-trading entitlement (see §4.3 for the safety contract).
  executionStream: "paper" | "live";

  workspaceId?: string;
  asOfTs?: string | null;
};
```

Scope must drive: visible widgets, selected workspace preset, dashboard metrics, recommended next actions, research
cards, catalogue cards, terminal mode content, report examples, locked previews, CTA copy, mock data stream, URL state,
local persistence.

### 4.1 Engagement is the second cockpit dial (orthogonal to surface + mode)

`surface` says _which top-level product area_ (Terminal / Research / Reports / Signals / Ops). `terminalMode` (when in
Terminal) says _which view is foreground inside Terminal_ (Command / Markets / Strategies / Explain / Ops). `engagement`
says _how the user is relating to the strategy_. All three dials are independent. Combinations:

| terminalMode | engagement = "monitor"                                  | engagement = "replicate"                                                                               |
| ------------ | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Command      | Live P&L · positions · kill switches · exception alerts | Step-by-step trade builder · leg tracker · paper/live toggle · venue-routing helper · manual order pad |
| Markets      | Spread monitor · funding curve · order books (read)     | Same data — but with "place trade from this view" affordances inline                                   |
| Strategies   | Running strategies · pause/resume · config versions     | Strategy walk-through · "what would happen if I did X step by step" · per-leg simulation               |
| Explain      | P&L attribution · execution leakage · slippage analysis | Same — plus "compare your manual fills to the algo's fills"                                            |
| Ops          | Service health · incidents · feed health                | (not applicable — Ops is supervisory)                                                                  |

The cockpit toolbar exposes terminalMode tabs (or researchStage tabs in Research) alongside the engagement toggle:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ ⚙ Scope: [DEFI ✕] [CARRY_BASIS_PERP ✕] [+]                                     │
│ Surface: ●Terminal ○Research ○Reports                                          │
│ Mode: ●Command ○Markets ○Strategies ○Explain ○Ops                              │
│ Engagement: ●Monitor ○Replicate    Stream: ●Paper ○Live                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ Widget grid (scope ∩ surface ∩ terminalMode ∩ engagement-aware)                │
└────────────────────────────────────────────────────────────────────────────────┘
```

Toggling Monitor → Replicate **keeps scope and layout positions intact** but swaps the widget bundle: passive monitoring
widgets fade out, active manual-trading widgets fade in for the same strategies. Toggling Paper → Live changes where
fills route (after a confirm dialog — see §4.3).

Every starter preset (Section 8) declares a `defaultSurface`, `defaultTerminalMode` / `defaultResearchStage`,
`defaultEngagement`, and `defaultExecutionStream`. The first-run wizard (Section 9) asks the user explicitly: _"Are you
here to watch your strategy run, or walk through it piece by piece?"_ — both paths are first-class in the demo.

### 4.2 Scope event contract (analytics + telemetry primitive)

Every scope mutation flows through one event contract. Cheap to add now, very valuable later for funnel analytics.

```ts
type ScopeChangeSource =
  | "dashboard-filter"
  | "scope-bar"
  | "preset"
  | "wizard"
  | "url-hydration"
  | "breadcrumb"
  | "widget-suggestion"
  | "route-redirect"
  | "surface-toggle"
  | "terminal-mode-toggle"
  | "research-stage-toggle"
  | "engagement-toggle"
  | "execution-stream-toggle";

type ScopeChangeEvent = {
  previousScope: WorkspaceScope;
  nextScope: WorkspaceScope;
  source: ScopeChangeSource;
  timestamp: string; // ISO 8601
  userId: string;
  sessionId: string;
};
```

Emit via `lib/analytics/track.ts::trackEvent("workspace.scope.change", event)`. This unlocks:

- _what do demo users filter to?_ (most-clicked archetypes per asset_group)
- _which locked previews do arbitrage users click?_ (drives FOMO copy A/B)
- _which preset creates the most engagement / conversion?_
- _where do users get lost?_ (sequences of scope-changes that end with abandonment)

Critical files (Phase 1A): `lib/stores/workspace-scope-store.ts` (NEW) emits `ScopeChangeEvent` on every mutation;
`lib/analytics/track.ts` already exists, add event-name constants.

### 4.3 Live-execution safety contract

`executionStream === "live"` is never a default for `engagement === "replicate"`. The contract:

1. **Default rule.** When a user enters replicate engagement, `executionStream = "paper"` always. The toolbar's stream
   toggle starts on Paper.
2. **Switching to live.** Paper → Live requires an explicit confirm dialog: _"You're switching to live execution. Manual
   orders placed from now on route to real venues. Confirm?"_ Cancel = stay paper. Confirm = flip + emit
   `ScopeChangeEvent {source: "execution-stream-toggle"}`.
3. **Mock / demo personas.** For any persona without a live-trading entitlement (most demo personas + all
   `client-data-only` / regulatory-only personas), the Live option in the stream toggle is **disabled with a tooltip**:
   _"Live execution is unavailable on demo accounts."_ Confirm dialog never opens. The toggle never silently flips.
4. **Visual signal.** When Live is active: red pin in the cockpit header, persistent "LIVE" badge next to the stream
   toggle, slightly different scope-bar treatment so the user can never confuse Paper for Live.
5. **URL contract.** `?stream=live` is honoured on URL hydration **only if** the persona has live-trading entitlement;
   otherwise it silently downgrades to `paper` and emits a console warning.

These rules are non-optional. The risk surface is "demo prospect accidentally places a live order while clicking around
the cockpit" — that's an unacceptable failure mode.

### 4.4 Scope additions — share class + availability axes

The five filter axes (asset_group / instrument_type / family / archetype / strategy) are necessary but not sufficient.
The strategy architecture exposes additional axes that **decide what the user can actually see** versus what merely
matches their interest. Add these to `WorkspaceScope`:

```ts
type WorkspaceScope = {
  // ... five filter axes from §4 ...

  // Share class — collateral / quote currency the strategy is denominated in.
  // Real dimension per strategy-lifecycle docs. BTC-neutral clients vs ETH-native
  // clients vs USD/USDT stablecoin reporting + DeFi staking/yield strategies all
  // need this. (Was in earlier drafts; reinstating per 2026-04-29 strategy-architecture audit.)
  shareClasses?: string[]; // e.g. ["btc", "eth", "usd", "usdt", null]

  // Advanced / admin filters (visible in scope-bar's "advanced" drawer; usually
  // implicit in scope resolution rather than user-facing chips):
  coverageStatuses?: Array<"SUPPORTED" | "PARTIAL" | "BLOCKED">;
  maturityPhases?: string[]; // smoke / backtest_30d / paper_1d / paper_14d / live_stable / etc
  productRoutings?: Array<"dart_only" | "im_only" | "both" | "internal_only">;
  availabilityStates?: Array<"PUBLIC" | "INVESTMENT_MANAGEMENT_RESERVED" | "CLIENT_EXCLUSIVE" | "RETIRED">;
};
```

**UI rule:** the scope bar's primary chip row exposes asset_group · instrument_type · family · archetype · share_class ·
venue/protocol · mandate · surface · engagement · execution_stream. The advanced filters (coverage / maturity / routing
/ availability) live in an "Advanced" drawer for power users + admin and are otherwise applied implicitly by the
resolver in §4.5. Buyers don't need to learn that vocabulary; the resolver does the work.

### 4.5 Strategy Availability Resolver — the bridge between scope and visibility

The biggest architectural gap in the original plan: **scope is not enough to decide what the user sees.** Two strategies
that match the same scope can be in very different visibility states for the same user — owned vs locked-by-tier vs
hidden-by-maturity vs reserved-for-IM.

Every cockpit surface (Catalogue, Terminal, Research, Reports, FOMO, presets, widget data) must call a single resolver
that combines scope + persona + entitlement + product routing + maturity + coverage + availability state +
subscription/allocation + share class + venue-set into one decision:

```ts
// lib/architecture-v2/strategy-availability-resolver.ts (NEW, Phase 1A)
type StrategyVisibilityState =
  | "owned" // user is subscribed / allocated; show Reality (live/paper P&L, positions)
  | "available_to_request" // visible in Catalogue Explore tab; CTA = request allocation/access
  | "locked_by_tier" // user lacks the tier entitlement (e.g. needs DART Full); show locked preview
  | "locked_by_workflow" // workflow gate unmet (e.g. needs questionnaire completion or KYC review)
  | "hidden" // pre-maturity, retired, or product-routing fails — never surfaced to client
  | "admin_only" // internal QA / lifecycle editor only
  | "read_only"; // IM desk seeing client-exclusive (read but not allocate)

type StrategyVisibilityReason =
  | "owned_subscription" // for visibility="owned"
  | "public_requestable" // for visibility="available_to_request"
  | "missing_tier" // for visibility="locked_by_tier" — needs DART Full / ml-full / strategy-full / etc.
  | "missing_questionnaire" // for visibility="locked_by_workflow" — questionnaire not completed
  | "missing_kyc" // for visibility="locked_by_workflow" — KYC review pending
  | "missing_mandate_review" // for visibility="locked_by_workflow" — IM mandate review needed
  | "pre_maturity" // for visibility="hidden" — strategy is in smoke / backtest / early paper
  | "wrong_product_routing" // for visibility="hidden" — IM-only strategy hidden from DART user, etc.
  | "retired" // for visibility="hidden" — RETIRED availabilityState
  | "admin_only" // for visibility="admin_only"
  | "client_exclusive_read_only" // for visibility="read_only" — IM desk seeing a CLIENT_EXCLUSIVE strategy
  | "im_reserved" // for visibility="read_only" — IM_RESERVED, accessed by allocator
  | "coverage_blocked"; // for visibility="hidden" — coverageStatus = BLOCKED

type StrategyVisibilityCta =
  | "request_access" // generic catalogue allocation request
  | "request_allocation" // IM mandate / pooled-fund allocation
  | "complete_questionnaire" // wizard / onboarding gate
  | "complete_kyc" // distribution-trust gate
  | "upgrade_to_dart_full" // tier upgrade
  | "contact_im_desk" // mandate review needed
  | "none"; // owned / hidden / admin_only

type StrategyVisibilityDecision = {
  visibility: StrategyVisibilityState;
  reason: StrategyVisibilityReason;
  cta: StrategyVisibilityCta;
  // Coverage-status qualifier — surfaces in copy when coverage is PARTIAL.
  // SUPPORTED renders normally; PARTIAL renders with a "partial venue coverage"
  // qualifier; BLOCKED is hidden for client personas (admin/internal only).
  coverageQualifier?: "supported" | "partial" | "blocked";
};

type StrategyAvailabilityContext = {
  persona: string; // persona id from PERSONAS
  role: "admin" | "internal" | "client";
  entitlements: readonly (string | TradingEntitlement)[];
  orgId?: string;
  clientId?: string;
  subscriptions: readonly string[]; // strategy_ids the user is subscribed/allocated to
  productRouting: "dart_only" | "im_only" | "both" | "internal_only";
  maturityPhase: string; // smoke / backtest_30d / paper_1d / paper_14d / live_stable / ...
  coverageStatus: "SUPPORTED" | "PARTIAL" | "BLOCKED";
  availabilityState: "PUBLIC" | "INVESTMENT_MANAGEMENT_RESERVED" | "CLIENT_EXCLUSIVE" | "RETIRED";
  shareClass: string | null;
  venueSetVariant: string;
};

// Returns a full decision (visibility + reason + cta + coverageQualifier) so
// downstream consumers (locked previews, empty states, catalogue cards) can
// tailor copy. Critical: never return a bare visibility state — copy gets
// generic and demos lose specificity.
export function resolveStrategyVisibility(
  instance: StrategyInstance,
  user: AuthUser,
  scope: WorkspaceScope,
  surface: WorkspaceScope["surface"]
): StrategyVisibilityDecision;

export function resolveVisibleStrategyInstances(
  user: AuthUser,
  scope: WorkspaceScope,
  surface: WorkspaceScope["surface"]
): readonly { instance: StrategyInstance; decision: StrategyVisibilityDecision }[];
```

**Coverage-status copy policy (rendering rule for the resolver consumers):**

- `SUPPORTED` → render normally; no qualifier.
- `PARTIAL` → render with a coverage qualifier inline (e.g. _"Vol Lab — Deribit + CME only (expanding)"_, _"Sports
  event-driven — partial venue coverage"_, _"TradFi options — research-only coverage"_). Never silently treat partial as
  fully-supported.
- `BLOCKED` → hidden for client personas; visible only to admin/internal.

**Persona-rule defaults (resolver applies in this order; first match wins):**

| Persona class                                                       | Visible states                                                                                                               |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `admin` / `internal-trader` / `im-desk-operator`                    | all states (admin sees everything; IM-desk sees client-exclusive as `read_only`)                                             |
| DART-Full client (entitlements include `strategy-full` + `ml-full`) | own subscriptions = `owned`; PUBLIC + tier-matching = `available_to_request`; pre-maturity = `hidden`; admin-only = `hidden` |
| Signals-In client (no `strategy-full` / `ml-full`)                  | own = `owned`; PUBLIC routed for Signals-In = `available_to_request`; Full-only = `locked_by_tier`; pre-maturity = `hidden`  |
| IM client / advisor                                                 | own SMA / share-class = `owned`; IM_RESERVED in mandate = `read_only`; pre-maturity = `hidden`; DART operational = `hidden`  |
| Regulatory client                                                   | reports + signals only; catalogue allocation = `hidden` (entire allocation surface)                                          |
| Prospect (un-subscribed)                                            | PUBLIC FOMO-safe subset = `available_to_request`; everything else = `hidden`                                                 |

Phases B-F **never bypass this resolver**. Widgets use `useScopedData()` which internally calls the resolver. Presets
declare archetypes; the resolver decides which instances surface.

### 4.6 Four-state availability taxonomy — Hide / Lock / Tease / Reality

The plan's original "FOMO overlay" model conflates four genuinely different states. Catalogue and Cockpit must apply
different policies:

| State                                                                    | Cockpit FOMO                                                                                                 | Catalogue FOMO                                                    |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| **Hidden** (pre-maturity / wrong product routing / admin-only / retired) | Not in widget catalogue. Not in suggestions. Not in scope hits.                                              | Not in Reality OR Explore tab.                                    |
| **Locked-by-tier** ("DART Full needed for vol lab")                      | Show contextual locked preview with workflow value (capability FOMO).                                        | Show locked card with allocation CTA → "request access" workflow. |
| **Locked-by-workflow** (missing KYC / questionnaire / mandate review)    | Same as locked-by-tier, but CTA is "complete questionnaire" or "request mandate review", not "upgrade tier". | Same.                                                             |
| **Available-to-request** (FOMO — visible, not subscribed)                | Suggested in scope-aware next-actions; rendered with "request allocation" CTA.                               | Explore tab shows it; Reality tab does not.                       |
| **Owned** (subscribed / allocated)                                       | Renders Reality data — live P&L, positions, paper fills.                                                     | Reality tab.                                                      |
| **Read-only** (IM desk seeing client-exclusive)                          | Renders read-only widgets; no edit / no allocate.                                                            | Read-only Reality view.                                           |

**Critical distinction (Phases 7 + 9):**

- **Catalogue FOMO** = strategy-instance / allocation FOMO. Stricter. Pre-maturity instances are _hidden_, not greyed.
  Product-routing failures are _hidden_, not locked. The Reality/Explore split is the canonical UX.
- **Cockpit FOMO** = workflow / capability FOMO. Contextual locked previews ("Arbitrage Promotion Checks locked", "Vol
  Lab locked"). About _what the user can do with their existing strategies_, not what extra strategies they could buy.

**Do not use the same locked-card logic for both.** The "Learn more" / upgrade CTAs route to different surfaces:

- Cockpit FOMO upgrade CTA → `/help/system-map` or contact form ("upgrade workflow")
- Catalogue allocation CTA → human-gated allocation request flow ("request allocation")

### 4.7 surface = "signals" and surface = "ops" — handling rule

`WorkspaceScope.surface` includes `"signals"` and `"ops"` alongside `"terminal"` and `"research"`. The implementation
rule:

- **`surface === "signals"`**: a top-level product area (Signals-In intake / strategy intake). `terminalMode` and
  `researchStage` are ignored. The cockpit renders a signals-specific layout (intake status · payload validation ·
  routing · paper/live mapping). The route round-trips `?surface=signals`.
- **`surface === "ops"`**: the **Admin/Ops product area** — distinct from `surface=terminal&tm=ops` which is the
  _Terminal Operational view_ (live service health visible inside the trading cockpit). They are two different surfaces:
  - `surface=terminal&tm=ops` = Terminal's Ops mode — what an oncall trader sees alongside positions / alerts /
    Strategy.
  - `surface=ops` = the Admin/Ops surface — incidents · audit · deployment · permission management. Lives in `app/(ops)`
    route group. When ambiguous, prefer the Terminal-mode form during demos (most demo personas don't have admin
    entitlement). The `surface=ops` form is reserved for admin / internal-trader / im-desk-operator personas.

### 4.8 Configuration lifecycle — Admin · Research · Promotion · Terminal

DART separates four concerns that the prior plan accidentally collapsed:

- **Scope** decides relevance — what the user is looking at (§4).
- **`StrategyAvailabilityResolver`** decides visibility — what the user is allowed to see or request (§4.5).
- **Configuration lifecycle** decides what can be changed, versioned, promoted, accepted, overridden, audited, and
  reported (this section).
- **Runtime state** describes what is currently running, paused, failing, overridden, or being explained.

Without §4.8, "promote a strategy to live" remains a config-versions hand-wave; auditors and risk-committee questions
("what got promoted, when, by whom, with what evidence?") have no answer surface.

**The operating rule (DART Full):**

> If you're in DART Full, the assumption is that you have the full prompt work cycle — research pipeline → version bump
> on promote → live accepts versioned bundles. You're not changing strategy logic on the fly. The only things that
> change live without a version bump are operational config (API keys, account setup) and policy-bounded dynamic config
> (treasury routing, size multiplier, venue disable, execution preset) — and those are typed, audited, and bounded by
> guardrails set in the bundle.

**The operating rule (Signals-In):**

> Signals-In does not use DART Research to build the strategy — the client has their own research. DART's job is to
> register external strategy versions, validate signal/instruction compatibility, attach execution / risk / reporting
> configs, and monitor versioned performance. The client tags their strategy with their own version so new-version
> performance is comparable across releases (idempotency by version tag).

#### 4.8.1 Twelve configuration object types

Configuration is not one thing. The plan splits it into twelve typed objects, each with a clear owner, version
discipline, and override scope:

| #   | Config object                 | Example payload                                                                                              | Owner                                                              | Versioned?          | Live override?                                 | Strategy-major-version bump?                  |
| --- | ----------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------- | ---------------------------------------------- | --------------------------------------------- |
| 1   | **WorkspaceConfig**           | Which preset / widgets / scope a demo persona sees                                                           | Admin (per-persona)                                                | Lightly versioned   | Yes (the user's own workspace)                 | No                                            |
| 2   | **PlatformBaselineConfig**    | Venue registry, supported markets, default risk policy, routing defaults                                     | Admin / Ops                                                        | Yes                 | Controlled (admin-only)                        | Usually no                                    |
| 3   | **AccountConnectivityConfig** | API keys, exchange accounts, wallets, custody, sub-accounts, signers                                         | Admin / Ops + Onboarding                                           | Yes (audited)       | Yes (rotation, no version bump)                | No, unless it changes executable universe     |
| 4   | **ResearchExperimentConfig**  | Dataset version, feature set, lookback, labels, train/val splits                                             | DART Research                                                      | Yes                 | No (ephemeral until promoted)                  | Yes if promoted                               |
| 5   | **MLExperimentConfig**        | Model version, hyperparameters, training set hash, feature versions                                          | DART Research / ML                                                 | Yes (semver + hash) | No                                             | Yes if attached to a live strategy            |
| 6   | **StrategyExperimentConfig**  | Strategy family, archetype, signal logic version, thresholds, universe                                       | DART Research                                                      | Yes                 | No (only via approved override presets)        | Yes                                           |
| 7   | **ExecutionExperimentConfig** | Algo, order type, slicing, venue routing, slippage assumptions                                               | Research Validate / Execution                                      | Yes                 | Only via approved `execution_preset` overrides | Sometimes                                     |
| 8   | **RiskConfig**                | Daily-loss limit, drawdown limit, position-size cap, concentration cap                                       | Admin baseline + Research per-experiment                           | Yes                 | Tightening allowed; loosening forbidden live   | Loosening yes; tightening no                  |
| 9   | **TreasuryPolicyConfig**      | Collateral asset, rebalance threshold, hedge asset, target LTV, share class, yield rotation policy           | Research Allocate + Terminal Command (within guardrails)           | Yes                 | Some parts yes (within bundle guardrails)      | Material policy change yes; bounded change no |
| 10  | **TreasuryOperationalConfig** | Wallet address, exchange account, custody account, signer permissions, withdrawal limits, settlement account | Admin / Ops                                                        | Yes (audited)       | Yes                                            | No                                            |
| 11  | **StrategyReleaseBundle**     | Immutable promotion artifact (see §4.8.2)                                                                    | Research Promote (creates) + Approver (signs) + Terminal (accepts) | Immutable snapshot  | No (it IS the release)                         | Each bundle = one strategy version            |
| 12  | **RuntimeOverride**           | Audited live mutation on top of a running release bundle (see §4.8.3)                                        | Terminal (creates) + Approver (signs if material)                  | Audited, expiring   | Yes (that's the point)                         | Never; overrides do not rewrite the bundle    |

**Critical separation rules:**

- `TreasuryPolicyConfig` (collateral asset, hedge ratio, share class) is **strategy-attached** — it travels in the
  release bundle, and material changes require a new bundle. Bounded changes (rebalance threshold within bundle-declared
  range) are `RuntimeOverride`s.
- `TreasuryOperationalConfig` (wallet address, custody account, withdrawal limits) is **operational** — it never causes
  a strategy version bump. Rotating an exchange account is an audited admin action, not a research promotion.
- API key rotation is an `AccountConnectivityConfig` change. Never a strategy version bump.

**Baseline vs ephemeral configuration:**

The 12 config types split orthogonally into two persistence regimes:

- **Baseline configuration** is persistent and reusable. It defines default platform behaviour and is owned mostly by
  Admin/Ops + Research-setup. Examples: standard execution settings, default venue routing, supported instruments,
  default risk limits, default treasury policy, share-class defaults, standard slippage model, default report templates,
  account/connectivity setup.
- **Ephemeral configuration** is temporary and experiment-specific. It is used inside DART Research but does not become
  durable unless saved as a named version or included in a `StrategyReleaseBundle`. Examples: testing a 15-min rebalance
  instead of 5-min, trying a different feature subset, using model v17 instead of v16, simulating passive-only
  execution, changing a spread threshold for one run, running with Deribit only vs Deribit + CME.

> **Rule:** Ephemeral configs can produce experiment results, but they only become durable when saved as a named config
> version or included in a release bundle.

This is the discipline that prevents "configuration chaos" — Research can iterate freely on ephemeral configs; nothing
reaches Terminal until a bundle is built.

#### 4.8.2 `StrategyReleaseBundle` — the immutable promotion artifact

A release bundle is the single thing that flows from Research / Promote → Terminal / Strategies. It packages every
versioned object that defines what the strategy will do in production, plus the validation evidence that justifies
promoting it. Live cannot run anything that isn't a bundle.

```ts
// lib/architecture-v2/strategy-release-bundle.ts (NEW, Phase 1B)

type StrategyReleaseBundle = {
  releaseId: string; // e.g. "rb-arbitrage-cefi-defi-v3.2.1"
  strategyId: string;
  strategyVersion: string; // semver

  // Version pins — every dimension that affects strategy behaviour
  researchConfigVersion: string;
  featureSetVersion?: string; // optional for rules-based (non-ML) strategies
  modelVersion?: string; // optional for rules-based
  executionConfigVersion: string;
  riskConfigVersion: string;
  treasuryPolicyConfigVersion?: string; // optional for non-treasury strategies
  venueSetVersion: string;
  instrumentUniverseVersion: string;
  dataAssumptionVersion: string; // slippage curves, fee schedules, latency model
  signalSchemaVersion?: string; // for strategies emitting external signals
  instructionSchemaVersion: string; // wire format strategy → execution-service

  // Routing context — affects which mandate / share class the bundle binds to
  shareClass?: string;
  accountOrMandateId?: string;

  // Execution-aware validation evidence (REQUIRED — see §4.8.4)
  validationRunIds: readonly string[]; // walk-forward, ablation, robustness
  backtestRunIds: readonly string[]; // execution-aware backtest with this exact bundle
  paperRunIds?: readonly string[]; // paper run IDs if Pilot stage reached
  pilotRunIds?: readonly string[]; // pilot run IDs if Live stage reached

  // Promotion lifecycle (aligned with maturity stages: research→paper→pilot→live→monitor→retired)
  promotionStatus:
    | "draft"
    | "candidate"
    | "approved_for_paper"
    | "approved_for_pilot"
    | "approved_for_live"
    | "live"
    | "paused"
    | "monitor"
    | "retired"
    | "rolled_back";

  // Override guardrails — explicitly declared at bundle-creation time. Runtime
  // overrides outside these bounds require re-promotion, not a runtime mutation.
  runtimeOverrideGuardrails: {
    sizeMultiplierRange: [number, number]; // e.g. [0.0, 1.0] — can scale down to zero, never up
    treasuryRebalanceThresholdRange?: [number, number];
    venueDisableAllowed: boolean;
    executionPresets: readonly string[]; // approved presets only
    riskTighteningAllowed: boolean; // always true; loosening always false
    pauseEntriesAllowed: boolean;
    exitOnlyAllowed: boolean;
    treasuryRouteOverridesAllowed: boolean; // route within bundle-declared wallet whitelist
  };

  // Audit + lineage
  createdBy: string;
  createdAt: string; // ISO 8601
  approvedBy?: string; // for approved_for_* states
  approvedAt?: string;
  acceptedByTerminal?: string; // who accepted into Terminal — distinct from approver
  acceptedAt?: string;
  retiredBy?: string;
  retiredAt?: string;
  rolledBackFromReleaseId?: string; // if this is a rollback target

  // Reproducibility
  contentHash: string; // hash of all version pins + guardrails
  lineageHash: string; // hash of upstream data + features + model lineage
};
```

**Properties:**

- **Immutable.** Once created, never mutated. State transitions (draft → candidate → approved_for_paper → ...) are
  separate audit entries, not bundle edits.
- **Bit-identical reproducibility.** Every version pin is content-hashed; rerun-from-bundle produces the same backtest,
  the same paper run, the same model.
- **One bundle = one strategy version.** Promoting a model retrain creates a new bundle. Promoting a feature-set upgrade
  creates a new bundle. Promoting an execution-config tweak creates a new bundle.
- **Signals-In bundles use a sibling shape** (see §4.8.5).

#### 4.8.3 `RuntimeOverride` — typed, audited, bounded live mutations

DART Full users do not change strategy logic on the fly. They DO sometimes need to: pause a venue, scale to 50% size,
switch to a more conservative execution preset, widen hedge tolerance, route treasury from wallet A to wallet B, or flip
exit-only during a regime event. Those are `RuntimeOverride`s — typed, audited, bounded by the bundle's
`runtimeOverrideGuardrails`, and never silent.

```ts
// lib/architecture-v2/runtime-override.ts (NEW, Phase 1B)

type RuntimeOverrideType =
  | "size_multiplier" // scale strategy size in [0.0, guardrail max]
  | "venue_disable" // disable a single venue/protocol; bundle re-routes
  | "execution_preset" // switch to an approved preset (passive / aggressive / conservative)
  | "risk_limit_tightening" // tighten loss / drawdown / concentration limits
  | "treasury_route" // route treasury actions to a different whitelisted wallet
  | "pause_entries" // existing positions hold, no new entries
  | "exit_only" // existing positions exit on signal flip / time, no new entries
  | "kill_switch"; // immediate flatten + halt — never bounded; always audited

type RuntimeOverride = {
  overrideId: string;
  releaseId: string; // which bundle this override sits on top of
  scope: WorkspaceScope; // the scope at time of override (for analytics)

  overrideType: RuntimeOverrideType;
  value: unknown; // typed per overrideType (size: number; venue: string; preset: string; etc.)
  reason: string; // mandatory free-text reason

  createdBy: string;
  createdAt: string; // ISO 8601
  expiresAt?: string; // optional; some overrides auto-revert (e.g. event-window pause)

  requiresApproval: boolean; // true for material overrides (size > 50% reduction, treasury route changes)
  approvedBy?: string;
  approvedAt?: string;

  // Audit-pre/post — what the live state was before and after the override
  preOverrideState: Record<string, unknown>;
  postOverrideState: Record<string, unknown>;
  auditEventId: string; // event-sink reference for downstream queries
};
```

**Examples (each with strategy-version-bump column for the rule-of-thumb summary):**

| Override                | Meaning                                      |         Strategy version bump?         |
| ----------------------- | -------------------------------------------- | :------------------------------------: |
| `size_multiplier`       | Reduce strategy to 50% size                  |                   No                   |
| `venue_disable`         | Disable Binance or Aave temporarily          |                   No                   |
| `execution_preset`      | Switch from aggressive to passive execution  | No (preset must be approved on bundle) |
| `risk_limit_tightening` | Reduce exposure or drawdown limits           |                   No                   |
| `treasury_route`        | Use approved alternate treasury route        |                   No                   |
| `pause_entries`         | Stop new entries, allow exits                |                   No                   |
| `exit_only`             | Allow position reduction only                |                   No                   |
| `kill_switch`           | Stop strategy immediately, flatten positions |                   No                   |

**Rules:**

- `RuntimeOverride` never rewrites the underlying release bundle. The bundle stays the source of truth; overrides are an
  additive layer.
- Explain mode and Reports MUST show both the approved release bundle AND any runtime overrides active during the
  reporting period. Performance attribution that hides overrides is forbidden.
- Overrides that exceed bundle guardrails are rejected at write time with the message _"This change exceeds the bundle's
  override guardrails. Promote a new bundle or contact risk."_
- `kill_switch` is always allowed regardless of guardrails. Always audited.

#### 4.8.4 Execution-aware validation gate (mandatory before promotion)

> Execution backtest is the natural completion of the chain. At that point you know which algorithms are attached to
> which instructions, which versions of them, which strategies are being used to generate the instructions, and which ML
> models (if any) are attached.

That's exactly the bundle. So the promotion gate is:

> **No `StrategyReleaseBundle` can transition to `approved_for_paper` (or any later state) unless the bundle's strategy
> version, model version, execution config, risk config, treasury policy, venue set, and instruction schema have been
> validated together in an execution-aware backtest or paper run.**

The validation must know:

- Which signal instruction schema the strategy emits.
- Which strategy version generates the instruction.
- Which model version (if any) generates the signal.
- Which execution algo receives the instruction.
- Which venue / router handles the order.
- Which account or paper account is used.
- What slippage / fill / latency assumptions apply.
- What risk gates are active.
- What treasury policy applies (collateral, hedge, share class).

If any of those is unknown or unpinned, the validation cannot be execution-aware and the gate fails.

#### 4.8.5 Signals-In path — `ExternalSignalStrategyVersion`

Signals-In clients bring their own research. DART does not train their models, does not own their feature library, does
not run their backtests. What DART provides:

- Registers the external strategy with a typed version object.
- Validates the client's signal payload schema.
- Maps client instructions onto DART execution / risk / reporting configs.
- Tags every fill and report with the external version so the client can compare new-version performance to
  prior-version performance (idempotency by version tag).

```ts
// lib/architecture-v2/external-signal-strategy-version.ts (NEW, Phase 1B)

type ExternalSignalStrategyVersion = {
  externalStrategyId: string; // client's identifier
  externalVersion: string; // client's version tag (semver, hash, or arbitrary string)
  clientId: string;

  // DART-side schema + mapping versions (assigned by DART, not the client)
  signalSchemaVersion: string; // DART-assigned schema the client conforms to
  instructionMappingVersion: string; // how external instructions map to DART execution

  // DART-side configs attached to this external version
  executionConfigVersion: string;
  riskConfigVersion: string;
  treasuryPolicyConfigVersion?: string; // if external strategy uses DART treasury policy
  reportingTagSetVersion: string; // tags propagated through reports

  // Routing context
  accountOrMandateId?: string;
  shareClass?: string;

  // Validation evidence (Signals-In equivalent of bundle validation)
  validationRunIds: readonly string[]; // schema validation, instruction-mapping verification
  paperRunIds?: readonly string[]; // paper runs against this external version

  // Lifecycle status — Signals-In needs its own state machine because there is
  // no Discover/Build/Train. Registration is the entry point, paper validates
  // schema/mapping, live runs real money. Retirement is explicit.
  status:
    | "registered" // client declared a new external version; awaiting validation
    | "validating" // schema + mapping under validation
    | "paper" // running on paper to confirm fills + reporting alignment
    | "approved_for_live"
    | "live"
    | "paused"
    | "retired";

  // Audit
  registeredBy: string;
  registeredAt: string;
  retiredBy?: string;
  retiredAt?: string;
};
```

**Properties:**

- A Signals-In client uploads / declares a new external version → DART creates a new `ExternalSignalStrategyVersion`
  registration → execution / risk / reporting configs auto-attach (or are explicitly assigned in admin) → fills tag
  `externalVersion` for downstream attribution.
- The client never edits their own external version registration through the cockpit. New version = new registration.
  This is the idempotency / comparability rule.
- Catalogue does NOT show external strategies in Discover (they are client-private). They DO show in the client's
  Reality view in Strategies mode.

#### 4.8.6 Configuration ownership by surface

| Config object                 | Admin / Ops               | Research          | Promote               | Terminal                          | Reports                |
| ----------------------------- | ------------------------- | ----------------- | --------------------- | --------------------------------- | ---------------------- |
| WorkspaceConfig               | owner                     | reads             | —                     | reads + edits own                 | —                      |
| PlatformBaselineConfig        | owner                     | reads / defaults  | reads                 | reads                             | reads                  |
| AccountConnectivityConfig     | owner                     | reads eligibility | validates             | uses                              | audit only             |
| ResearchExperimentConfig      | —                         | owner             | snapshots into bundle | reads (lineage)                   | lineage                |
| MLExperimentConfig            | —                         | owner             | snapshots into bundle | reads if live                     | lineage                |
| StrategyExperimentConfig      | —                         | owner             | snapshots into bundle | runs                              | attribution            |
| ExecutionExperimentConfig     | baseline owner            | experiment owner  | snapshots into bundle | runs / runtime preset overrides   | TCA                    |
| RiskConfig                    | baseline owner            | experiment owner  | snapshots into bundle | enforces / tighter overrides only | reports                |
| TreasuryPolicyConfig          | baseline owner            | experiment owner  | snapshots into bundle | runs / bounded overrides          | reports                |
| TreasuryOperationalConfig     | owner                     | eligibility only  | validates             | uses                              | audit                  |
| StrategyReleaseBundle         | audit visibility          | creates candidate | approves              | accepts / runs / rolls back       | reports + lineage      |
| RuntimeOverride               | policy owner (guardrails) | —                 | —                     | owner                             | shown alongside bundle |
| ExternalSignalStrategyVersion | owner (registration)      | —                 | validates             | runs                              | tags fills + reports   |

**Reading the table:**

- Research is the only surface that creates promotable bundles. Terminal accepts them.
- Admin owns demo-workspace, account/connectivity, baseline platform, treasury operational, and the release-bundle
  approval queue. Admin does not author research configs.
- Promote (the Research stage) is where bundles are signed. Approval is a typed event, not a chat conversation.
- Terminal authors `RuntimeOverride`s but never mutates the bundle.
- Reports must surface bundle + override layer side-by-side; performance attribution that hides overrides is forbidden.

#### 4.8.7 Lifecycle stages — Pilot stage added

The plan's prior stage list (Discover → Build → Train → Validate → Allocate → Promote → Live → Monitor) maps cleanly
onto the docs' canonical maturity taxonomy with one addition: **Pilot** sits between Paper and Live.

Updated maturity stages (these are `StrategyReleaseBundle.promotionStatus` transitions):

```
draft → candidate → approved_for_paper → paper → approved_for_pilot → pilot → approved_for_live → live → monitor → retired
                                                                                                              ↘ rolled_back
```

- **Paper** — runs on real data, simulated fills only. In-distribution sanity check.
- **Pilot** — real money, capped at 1–5% of target size. Real slippage / fees / partial fills / venue quirks.
- **Live** — at full target capital.
- **Monitor** — running but capped, decay being measured.
- **Retired** — code archived, bundle non-deployable. Always retrievable via release-bundle registry.

Strategy-architecture maturity-phase taxonomy
(`smoke / backtest_30d / paper_1d / paper_14d / pilot / live_stable / monitor / retired`) maps onto these states; the
resolver in §4.5 already keys off it.

**Where each lifecycle stage lives in the cockpit:**

| Lifecycle stage | DART surface(s)                                |
| --------------- | ---------------------------------------------- |
| Research        | Research / Discover · Build · Train · Validate |
| Paper           | Research / Validate + Terminal / Strategies    |
| Pilot           | Research / Promote + Terminal / Command        |
| Live            | Terminal / Command · Strategies · Markets      |
| Monitor         | Terminal / Command · Explain · Ops             |
| Retired         | Terminal / Strategies + Reports                |

This keeps the plan aligned with the ComsicTrader docs' canonical lifecycle while preserving the existing DART
research-stage names.

#### 4.8.8 Surface mapping — where each config gets configured

| Surface                            | Config responsibilities                                                                                                                                                                                                                |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Admin / Ops** (`surface=ops`)    | Demo workspace config · persona defaults · entitlements · account / API key setup · venue & protocol registry · baseline risk · baseline execution · treasury operational config · release-bundle approval queue · audit & permissions |
| **DART Research / Discover**       | Strategy universe browse · candidate strategy selection · data availability                                                                                                                                                            |
| **DART Research / Build**          | Data config · feature config · instrument-universe scope · dataset versions                                                                                                                                                            |
| **DART Research / Train**          | ML experiment config · model versions · feature sets · hyperparameter sweeps                                                                                                                                                           |
| **DART Research / Validate**       | Backtest config · execution-aware simulation config · execution experiment config · drift checks                                                                                                                                       |
| **DART Research / Allocate**       | Capital · risk · treasury policy · share class · mandate fit · capacity headroom                                                                                                                                                       |
| **DART Research / Promote**        | Release bundle creation · approval · paper / pilot / live candidate selection · rollback                                                                                                                                               |
| **DART Terminal / Strategies**     | Accept release bundle · run / pause / promote / roll back                                                                                                                                                                              |
| **DART Terminal / Command**        | Runtime supervision · `RuntimeOverride` authoring · kill switches                                                                                                                                                                      |
| **DART Terminal / Explain**        | Compare live vs bundle assumptions · attribution · drift · execution leakage · bundle + active-overrides view                                                                                                                          |
| **Reports**                        | Client-safe reporting of release · performance · attribution · bundle + override layer · external-version tagging (Signals-In)                                                                                                         |
| **Signals-In** (`surface=signals`) | External strategy version registration · signal schema validation · instruction mapping · paper / live mapping · versioned performance attribution                                                                                     |

This is the missing config map that turns the cockpit from "nice navigation" into "auditable operating system."

#### 4.8.9 Implementation sequencing

1. **Phase 1B (alongside 1A — `StrategyAvailabilityResolver`):** Ship typed objects for all 12 config layers, the
   bundle, the override union, the external-version registration. Stub registries in `lib/architecture-v2/`. No UI yet.
2. **Phase 5:** Widget metadata declares which config object the widget binds to (read or mutate). Mutation widgets
   require explicit override-permission props.
3. **Phase 6:** Wizard step 0 (System map) explains the config-lifecycle in one paragraph (no table — the
   `/help/system-map` page carries the full table).
4. **Phase 7:** Locked-preview copy tied to bundle approval gates ("Promotion gate locked: needs execution-aware
   validation evidence").
5. **Phase 8:** Mock liveness creates fake bundles + fake overrides so demo prospects can see the audit trail populate
   live.
6. **Phase 9:** Route collapse moves bundle approval queue to `surface=ops` admin route group; live override authoring
   stays in Terminal Command.

### 4.9 Assumption Stack — the Odum backtest-to-live USP

DART's core product advantage is not just that strategies can move from research to live. It is that they move through
the lifecycle with the same operating assumptions that determine whether a strategy works in production.

A normal backtest usually answers:

> Did the signal make money on historical prices?

DART must answer:

> Would this strategy still work after execution costs, gas fees, treasury movement, portfolio rebalancing, liquidation
> risk, client deposits and withdrawals, venue constraints, routing rules, risk limits, and reporting assumptions are
> applied?

This is the seamlessness Odum needs to show. The platform exposes an `AssumptionStack` attached to every strategy
candidate, experiment, simulation, paper run, release bundle, and live deployment.

```ts
type AssumptionStack = {
  id: string;
  version: string;
  hash: string;

  strategyId: string;
  strategyVersion: string;

  modelVersionIds?: string[];
  featureSetVersionIds: string[];

  executionAssumptions: ExecutionAssumptionConfig;
  gasFeeAssumptions?: GasFeeAssumptionConfig;
  treasuryPolicy: TreasuryPolicyAssumptionConfig;
  depositWithdrawalAssumptions?: ClientFlowAssumptionConfig;
  liquidationAssumptions?: LiquidationAssumptionConfig;
  portfolioRebalanceAssumptions?: PortfolioRebalanceAssumptionConfig;
  venueRoutingAssumptions: VenueRoutingAssumptionConfig;
  riskAssumptions: RiskAssumptionConfig;
  reportingAssumptions: ReportingAssumptionConfig;

  createdBy: string;
  createdAt: string;
  notes?: string;
};
```

The assumption stack is versioned and content-hashed. Changing assumptions that affect strategy behaviour creates a new
assumption-stack version and, when promoted, a new `StrategyReleaseBundle`. Operational changes that do not alter
strategic behaviour — API keys, wallet addresses, signer permissions, account connectivity — remain in Admin/Ops
configuration and do not trigger a strategy version bump.

#### Nine layers, one stack

| Layer                           | Required? | Captures                                                                              |
| ------------------------------- | --------- | ------------------------------------------------------------------------------------- |
| `executionAssumptions`          | required  | Slippage model + bps, commission, latency, queue position, approved presets           |
| `treasuryPolicy`                | required  | Share class, approved collateral, hedge ratio range, leverage caps, auto-rebalance    |
| `venueRoutingAssumptions`       | required  | Routing mode (SOR / strategy-picked / meta-broker), approved venues, bias             |
| `riskAssumptions`               | required  | Max drawdown, concentration, gross/net exposure, USD loss ceiling                     |
| `reportingAssumptions`          | required  | P&L basis (realised / MTM / blended), mark source, NAV cadence, settlement lag        |
| `gasFeeAssumptions`             | DeFi only | Base + priority gwei, stress multipliers, per-tx gas units, MEV protection            |
| `depositWithdrawalAssumptions`  | optional  | Avg daily flow %, redemption stress (e.g. 30% in 5d), notice period, liquidity buffer |
| `liquidationAssumptions`        | optional  | Initial + maintenance margin, collateral haircuts, max LTV, force-rebalance LTV       |
| `portfolioRebalanceAssumptions` | optional  | Allocation method, vol target, cadence, drift threshold, max single weight            |

A `SimulationReadinessReport` aggregates the per-layer status into a 0..100 score. Required layers weight 70% of the
headline; optional layers weight 30%. The Promote stage refuses to advance the bundle past `candidate` while any
required layer is `missing` or `partial`.

#### UI rule

Every research, simulation, promotion, and live cockpit surface MUST expose the active assumption stack.

- **Research/Validate** — author / edit assumptions before promotion. `<AssumptionStackPanel />` +
  `<BacktestVsOperatingPanel />` rendered alongside the standard widget grid. The user sees the 9-layer status
  - the cost-of-reality attribution (signal-only vs operating-adjusted P&L per layer).
- **Research/Promote** — frozen stack inside the candidate `StrategyReleaseBundle`. The PromoteBundleForm's pre-flight
  gates include a `simulationReadinessScore >= 95` requirement.
- **Terminal/Strategies** — the running strategy's bundle pin renders the active stack so the trader can answer "what
  assumptions are governing this position?" in one glance.
- **Terminal/Explain** — assumption stack + per-layer **drift** (realised vs simulated).
  `<AssumptionStackPanel drift={...} />` colour-codes layers where live behaviour exceeds the simulated envelope; the
  headline `adherenceScore` answers "is live tracking the simulation?". Drift > threshold opens an alert path.

#### Wizard "What do you want to prove?" step

The four-step onboarding wizard adds a proof-goal step (between preset and scope). Choosing a goal emphasises the
relevant assumption layers in the resulting workspace:

| Proof goal                             | Layers emphasised          |
| -------------------------------------- | -------------------------- |
| Signal performance                     | execution                  |
| Execution feasibility                  | execution + venue_routing  |
| Gas / chain-cost sensitivity           | gas_fees + execution       |
| Liquidation resilience                 | liquidation + treasury     |
| Treasury & collateral movement         | treasury + venue_routing   |
| Portfolio allocation across strategies | portfolio_rebalance + risk |
| Client deposits / withdrawals          | client_flows + treasury    |
| Full promotion readiness               | all 9 layers               |

The wizard stays buyer-friendly. Internally it produces a structured `AssumptionStack` — externally it feels like guided
institutional simulation. The buyer says _"I want to test a DeFi yield strategy under 30% withdrawal stress, higher gas,
and collateral drawdown"_, and DART produces the matching stack + simulation run + promotion-evidence path.

#### Positioning copy

Use these claims on the DART page, IR deck, and signed-in workspace:

> **Backtest-to-live continuity with real operating assumptions.** DART does not just test price signals. It simulates
> the full strategy operating environment: execution, gas, treasury flows, liquidation risk, client deposits and
> withdrawals, portfolio rebalancing, routing, risk limits, and reporting — then promotes the same configuration into
> paper or live trading.

> **A strategy is not ready because the chart looks good.** It is ready when the signal, model, execution assumptions,
> gas costs, treasury flows, liquidation risk, client flows, risk limits, and reporting basis survive the same promotion
> path used in live trading.

> **Odum is not only cross-asset. It is assumption-complete.**

#### Phase mapping

The assumption stack threads back through the existing 9-phase programme:

- **Phase 5A** — Assumption-aware widgets (`<AssumptionStackPanel />`).
- **Phase 5B** — Backtest vs operating simulation widgets (`<BacktestVsOperatingPanel />`).
- **Phase 6A** — Preset assumption stacks: each `WorkspacePreset` declares a default `AssumptionStack` template so the
  wizard can hydrate from a familiar shape.
- **Phase 6B** — Wizard "What do you want to prove?" step.
- **Phase 7A** — Locked previews show assumption depth (Vol Lab locked → "you would unlock vol-surface assumption
  layers"; DeFi Yield locked → "you would unlock liquidation + recursive-collateral assumptions").
- **Phase 8A** — Mock liveness includes gas, treasury, liquidation, deposit/withdrawal flows so the demo shows live
  drift in real time.
- **Phase 8B** — Explain shows simulated vs realised drift per layer (already shipped via
  `<AssumptionStackPanel drift />`).

Required SSOT files:

- `lib/architecture-v2/assumption-stack.ts` — typed schema + `evaluateSimulationReadiness()` helper.
- `components/cockpit/assumption-stack-panel.tsx` — the 9-layer panel with readiness + drift.
- `components/cockpit/backtest-vs-operating-panel.tsx` — three-column comparison + cost-of-reality attribution.
- `lib/cockpit/demo-bundle.ts` — `DEMO_ASSUMPTION_STACK` + `DEMO_DRIFT_REPORT` fixtures.

### 4.10 Widget vocabulary SSOT — canonical surface names

Phase 5 widgets must adopt canonical names from the new ideal-world reference docs at
[unified-trading-system-ui/docs/reference/](unified-trading-system-ui/docs/reference/) — specifically
[common-tools.md](unified-trading-system-ui/docs/reference/common-tools.md) (30 manual surfaces) and
[automation-common-tools.md](unified-trading-system-ui/docs/reference/automation-common-tools.md) (18 automated
surfaces). Adopting the canonical names now prevents v2 archetype expansion (§4.10) from triggering a widget-rename
churn.

**Rule:** every `DartWidgetMeta.id` maps 1:1 to a canonical surface name and carries an explicit `canonicalSurfaceName`
string. Buyer-facing label is free copy; engineering ID is locked to the yardstick.

```ts
// components/widgets/_registry.ts (Phase 5 extension)

type DartWidgetMeta = {
  id: string; // matches canonicalSurfaceName by convention
  canonicalSurfaceName: string; // e.g. "Multi-Timeframe Charting", "Pre-Trade Risk Preview"
  buyerLabel: string; // e.g. "Live Spreads", "Pre-Trade Check"
  // ... existing scopePredicate / surfaces / engagements / etc.
};
```

**Examples:**

| Plan widget concept           | Canonical surface name (docs)                | Source doc anchor              |
| ----------------------------- | -------------------------------------------- | ------------------------------ |
| Chart widget                  | Multi-Timeframe Charting                     | common-tools.md §1             |
| Order entry / trade builder   | Order Entry Ticket Framework                 | common-tools.md §2             |
| Pre-trade risk widget         | Pre-Trade Risk Preview                       | common-tools.md §3             |
| Execution algo selector       | Execution Algos Library                      | common-tools.md §4             |
| Smart router widget           | Smart Order Router / Multi-Venue Aggregation | common-tools.md §5             |
| Positions widget              | Positions Blotter                            | common-tools.md §7             |
| Working orders widget         | Working Orders Blotter                       | common-tools.md §8             |
| Live P&L widget               | Live PnL Panel                               | common-tools.md §9             |
| Risk panel                    | Risk Panel (Multi-Axis)                      | common-tools.md §10            |
| Stress / scenario widget      | Stress / Scenario Panel                      | common-tools.md §11            |
| Calendar widget               | Catalyst / Event Calendar                    | common-tools.md §12            |
| Alerts widget                 | Alerts Engine                                | common-tools.md §14            |
| Heatmap widget                | Heatmap of Own Book                          | common-tools.md §16            |
| Latency / connectivity widget | Latency / Connectivity / Infra Panel         | common-tools.md §18            |
| Kill switch                   | Kill Switches (Granular)                     | common-tools.md §19            |
| Replay widget                 | Replay Tool                                  | common-tools.md §20            |
| Trade history                 | Trade History / Blotter (Historical)         | common-tools.md §21            |
| P&L attribution               | PnL Attribution (Multi-Axis)                 | common-tools.md §22            |
| Equity curve                  | Equity Curve                                 | common-tools.md §24            |
| Slippage / TCA                | Execution Quality / TCA                      | common-tools.md §25            |
| Strategy fleet board          | Live Fleet Supervision Console               | automation-common-tools.md §11 |
| Intervention console          | Intervention Console (incl. manual trading)  | automation-common-tools.md §12 |
| Promotion gate UI             | Promotion Gates & Lifecycle                  | automation-common-tools.md §9  |
| Capital allocation widget     | Capital Allocation Engine                    | automation-common-tools.md §10 |
| Decay tracker                 | Post-Trade & Decay Tracking                  | automation-common-tools.md §13 |
| Data catalog widget           | Data Layer (catalog / quality / lineage)     | automation-common-tools.md §3  |
| Feature library widget        | Feature Library                              | automation-common-tools.md §4  |
| Model registry widget         | Model Registry                               | automation-common-tools.md §6  |
| Experiment tracker widget     | Experiment Tracker                           | automation-common-tools.md §7  |

**Phase 5 widget catalog must reference these names.** Drift detection in code review: if a new widget uses an ad-hoc
name not in the docs, reviewer asks "which canonical surface is this? Is it really new, or is it a sub-mode of an
existing surface?"

### 4.10 v2 archetype-expansion roadmap

The plan's eight v1 presets (Executive Overview · Live Trading Desk · Arbitrage Command · DeFi Yield & Risk · Volatility
Research Lab · Sports / Prediction Desk · Signals-In Monitor · Research-to-Live Pipeline) cover roughly six of the
fifteen archetype clusters in [docs/reference/](unified-trading-system-ui/docs/reference/). That is honest v1 scope. v2
names the remaining seven archetype-cluster presets so marketing, Phase 5 widget metadata, and Phase 6
PRESET_ARCHETYPE_MAP have a future-target to plan against.

| v2 preset (proposed)            | Archetype cluster     | Doc anchor                                                                                                                          | Strategy backing                                                        | Venue / data prerequisites                                                                     |
| ------------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Market-Making Desk**          | Mira (CeFi MM)        | [trader-archetype-mira-market-maker.md](unified-trading-system-ui/docs/reference/trader-archetype-mira-market-maker.md)             | quote engines, adverse-selection monitor, queue position estimator      | sub-100ms feeds; per-venue RTT; quote-engine parameter library                                 |
| **Equity Long-Short Desk**      | Henry (TradFi equity) | [trader-archetype-henry-equity-long-short.md](unified-trading-system-ui/docs/reference/trader-archetype-henry-equity-long-short.md) | factor models · earnings track records · pair-trade signals             | Refinitiv / Compustat / FactSet; earnings transcripts; insider filings; short-interest archive |
| **Rates Desk**                  | Ingrid (TradFi rates) | [trader-archetype-ingrid-rates.md](unified-trading-system-ui/docs/reference/trader-archetype-ingrid-rates.md)                       | curve / DV01 / spread / auction                                         | sovereigns + swaps + OIS + repo + auction history; primary-dealer survey                       |
| **Macro Desk**                  | Rafael (multi-asset)  | [trader-archetype-rafael-global-macro.md](unified-trading-system-ui/docs/reference/trader-archetype-rafael-global-macro.md)         | themes · scenario PnL grids · expression comparison                     | cross-asset feeds; theme-tag system; scenario engine                                           |
| **FX Desk**                     | Yuki (TradFi FX)      | [trader-archetype-yuki-fx.md](unified-trading-system-ui/docs/reference/trader-archetype-yuki-fx.md)                                 | carry · cross-vol · fixings · NDF · session-aware                       | G10 + EM feeds; CB-meeting calendar; fixing-window markers                                     |
| **Energy Desk**                 | Theo (TradFi energy)  | [trader-archetype-theo-energy.md](unified-trading-system-ui/docs/reference/trader-archetype-theo-energy.md)                         | calendar spreads · weather · inventory · OPEC                           | EIA / DOE / IEA archives; weather feeds; refinery utilisation; sanctioned-flow tracking        |
| **Event-Driven Desk**           | Naomi (merger-arb)    | [trader-archetype-naomi-event-driven.md](unified-trading-system-ui/docs/reference/trader-archetype-naomi-event-driven.md)           | deal-as-object · regulatory tracking · NLP-classified merger agreements | SEC EDGAR; court dockets; antitrust precedents; deal corpus                                    |
| **Firm-Risk Aggregate Console** | David (PM/Risk)       | [trader-archetype-david-pm-risk.md](unified-trading-system-ui/docs/reference/trader-archetype-david-pm-risk.md)                     | cross-trader-fleet aggregation · firm systematic risk                   | reads from all desks' bundles + overrides; firm-level risk budget                              |

**Rule:** v1 ships 8 presets. v2 ships these 7 + a refined Executive Overview that splits into "Allocator" (Elena) +
"Firm-Risk" (David). Marketing must NOT claim v1 covers all fifteen.

### 4.11 Cross-cutting widget conventions (from docs INDEX)

The new ideal-world docs converge on ten cross-cutting principles every widget should respect. Phase 5 metadata picks
these up as `DartWidgetMeta` extensions so the cockpit feels like a serious trader terminal, not a webby SaaS dashboard.

| #   | Principle (docs INDEX)                                                            | Convention applied to `DartWidgetMeta`                                                                                                                     | Phase    |
| --- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 1   | Information density vs. clarity (no decorative chrome)                            | Widget meta declares `defaultDensity: "high" \| "medium" \| "low"`; Replicate engagement defaults higher density than Monitor for the same widget.         | 5        |
| 2   | Latency-of-glance (<1s for "what's my PnL right now?")                            | `freshnessSla: { decide: "1s", enter: "100ms", learn: "60s" }` per widget; cockpit header surfaces worst-of-row.                                           | 5        |
| 3   | Spatial memory (persistent layouts, never auto-rearranging)                       | Layout positions saved per `(workspaceId, scope hash, engagement)`; toggling Monitor↔Replicate preserves positions per §4.1.                               | 6        |
| 4   | Phase-appropriate freshness (Decide=1s; Enter+Hold=sub-100ms; Learn=min)          | `freshnessSla` per phase (above); widgets with miss-SLA freshness render an amber freshness pill.                                                          | 5        |
| 5   | One source of truth for state (positions on chart = blotter = risk)               | Mutation widgets emit `ScopeChangeEvent` + read-only views of mutating widgets share the same selector hook.                                               | 5        |
| 6   | Hotkeys for action; mouse for analysis                                            | Cockpit declares `KeyboardContract` per preset; replicate engagement assigns defaults; conflicts surface in `/help/system-map`.                            | 6        |
| 7   | First-class tagging at order time (strategy / theme / deal / pair / parent-trade) | Replicate order-pad widgets reject submission unless `bundleId` (DART Full) or `externalVersion` (Signals-In) is attached.                                 | 6 / §4.8 |
| 8   | Multi-leg native execution (atomic-or-nothing)                                    | `executionStream` toggle wraps multi-leg in atomic semantics; partial-fill behaviour declared per leg in widget meta.                                      | 8        |
| 9   | Risk in trader-native units                                                       | Every risk-class widget declares `nativeUnit: "DV01" \| "delta" \| "vega" \| "fx_basket" \| "notional" \| "stake"`; cockpit refuses unitless risk widgets. | 5        |
| 10  | Calendar dominates planning                                                       | `Catalyst / Event Calendar` widget is foveal in Markets mode for every preset; event overlays appear inline on charts.                                     | 5        |
| 11  | Replay capability (single most valuable post-trade tool)                          | `Replay Tool` widget is first-class in Explain mode; binds to scope's `asOfTs`; works in mock + live.                                                      | 8        |
| 12  | Audit trails non-negotiable                                                       | Every widget that mutates state (creates RuntimeOverride, accepts bundle, etc.) calls `recordAudit()` with pre/post state.                                 | §4.8     |
| 13  | Aggregation must drill down (no blackbox roll-ups)                                | KPI widgets expose `.drilldown(scope)` returning sub-scope; "click to drill" affordance on every aggregated number.                                        | 5        |
| 14  | Compliance / counterparty / venue / borrow inline (not sidecar)                   | `Pre-Trade Risk Preview` widget embeds entitlement, venue, and borrow checks inline; sidecar tools forbidden.                                              | 6        |

These conventions land in the `DartWidgetMeta` interface alongside the existing `scopePredicate` / `surfaces` /
`engagements` / `executionStreams` fields. Phase 5 PR review enforces them.

**Typed metadata extension (Phase 5):**

```ts
// components/widgets/_registry.ts (Phase 5 extension)

type FreshnessSla = {
  decide?: "1s" | "5s" | "60s" | "t+1";
  enter?: "100ms" | "1s" | "5s";
  hold?: "1s" | "5s" | "60s";
  learn?: "60s" | "t+1";
};

type WidgetNativeUnit =
  "DV01" | "delta" | "vega" | "gamma" | "fx_basket" | "notional" | "ltv" | "pnl" | "bps" | "stake";

type DartWidgetMeta = {
  // Identity (§4.9)
  id: string;
  canonicalSurfaceName: string;
  buyerLabel: string;
  description: string;

  // Surface + foreground mode/stage gating
  surfaces: Array<"terminal" | "research" | "reports" | "signals" | "ops">;
  terminalModes?: Array<"command" | "markets" | "strategies" | "explain" | "ops">;
  researchStages?: Array<"discover" | "build" | "train" | "validate" | "allocate" | "promote">;

  // Engagement + execution gating
  engagements?: Array<"monitor" | "replicate">;
  executionStreams?: Array<"paper" | "live">;

  // Filter axes
  assetGroups?: string[];
  instrumentTypes?: string[];
  families?: string[];
  archetypes?: string[];
  entitlements?: string[];

  recommendedForPresets?: string[];
  importance?: "primary" | "secondary" | "supporting";
  scopePredicate?: (scope: WorkspaceScope) => boolean;

  // §4.11 cross-cutting conventions
  freshnessSla?: FreshnessSla;
  nativeUnit?: WidgetNativeUnit;
  defaultDensity?: "high" | "medium" | "low";
  supportsReplay?: boolean;
  supportsDrilldown?: boolean;
  requiresOrderTags?: boolean; // mutating widgets must have bundle/external-version tag
  atomicity?: "atomic" | "best_effort" | "legged";
  hotkeyScope?: string; // e.g. "arbitrage-command", "vol-lab"

  // §4.8 binding — which config object the widget reads/mutates
  configBinding?: {
    reads?: readonly string[]; // config object type names
    mutates?: readonly string[]; // mutation widgets must declare what they mutate
    requiresOverridePermission?: boolean;
  };
};
```

Phase 5 PR review rejects any widget meta missing `canonicalSurfaceName`. Widgets that mutate state must declare
`configBinding.mutates`.

---

## 5. Target product structure

### 5.1 Post-login surfaces

DART Terminal · DART Research · Reports · Signals / Strategy Intake · Admin / Ops.

### 5.2 DART Terminal — five buyer-facing modes

| Mode           | Buyer label           | Description                                                                                                                                                                                                                                                                  |
| -------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Command**    | Live Command Surface  | Monitor strategy state, execution quality, exposure, P&L, and exceptions from one cross-asset workspace. (live P&L · positions · orders · fills · exposure · risk state · alerts · exceptions · strategy health · kill-switch / intervention status)                         |
| **Markets**    | Market Intelligence   | Track live market structure, liquidity, venue health, and pricing signals. (prices · spreads · order books · liquidity · funding · basis · vol · venue health · protocol health · sports / prediction event prices)                                                          |
| **Strategies** | Strategy Control      | View active strategy state, configuration versions, signal flow, and promotion readiness. (running · paper · promoted · paused · config versions · signal flow · allocation state · deployment state · strategy health · promote/pause/observe controls)                     |
| **Explain**    | Explain Performance   | Understand what drove performance, where execution leaked value, and whether live behaviour matches research. (P&L attribution · execution quality · slippage · funding/basis impact · MTM · reconciliation · batch/live drift · latency cost · failed-opportunity analysis) |
| **Ops**        | Operations & Controls | Monitor platform health, incidents, data freshness, deployments, and controlled intervention workflows. (service health · incidents · logs · feed health · data freshness · deployment state · audit trail · permission checks · emergency controls)                         |

### 5.3 DART Research — six journey stages

| Stage        | Buyer label             | Description                                                                                                                                                                                                                              |
| ------------ | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Discover** | Strategy universe       | Catalogue · family map · archetype map · asset-group coverage · strategy envelopes · examples · locked previews · recommended starting points.                                                                                           |
| **Build**    | Build data and features | Features · feature pipelines · dataset coverage · instrument mapping · venue/protocol coverage · feature freshness · research workspace. _(Internal labels like "Feature ETL" remain as subtitle / detail; not first-level buyer copy.)_ |
| **Train**    | Model experiments       | Models · ML experiments · feature importance · training runs · candidate scoring · registry · model lineage.                                                                                                                             |
| **Validate** | Test before deployment  | Backtests · paper · slippage assumptions · fill simulation · order-book replay · stress · synthetic scenarios · batch/live drift.                                                                                                        |
| **Allocate** | Capital and mandate fit | Allocation candidates · risk contribution · capital requirements · correlation · drawdown profile · mandate fit · account/share-class view · portfolio blend.                                                                            |
| **Promote**  | Move to paper / live    | Promotion readiness · config versions · approval state · deployment handoff · paper/live transition · audit trail · release notes.                                                                                                       |

---

## 6. Scope bar requirement

Persistent `DartScopeBar` / `WorkspaceScopeBar` across Dashboard, DART Terminal, DART Research, Strategy Catalogue,
Reports, and Signals/Intake.

**Collapsed example:**

```
Scope: Cross-asset · Arbitrage · Price Dispersion · BTC/ETH · CeFi + DeFi · Monitor · Paper
```

**Expanded controls:** Asset Group · Instrument Type · Strategy Family · Archetype · **Share Class** · Venue / Protocol
· Account / Mandate · **Surface** · **Terminal Mode** (when surface=terminal) · **Research Stage** (when
surface=research) · **Engagement** · **Execution Stream**. _(Advanced drawer for power users + admin: Coverage Status ·
Maturity Phase · Product Routing · Availability State — usually applied implicitly by the §4.5 resolver, exposed for
debugging / QA.)_

Share class is not a minor detail for Odum — BTC-neutral / ETH-native / USD-USDT / fund-share-class views materially
change which strategies and which P&L attribution the user sees. The chip belongs in the primary row, not the advanced
drawer.

**Acceptance:** user can always see what context they are in; scope persists during navigation; refresh preserves scope;
copied URL restores scope; changing scope updates downstream UI.

---

## 7. URL and persistence contract

URL keys (kept short, every WorkspaceScope field round-trips):

| Field                             | URL key   | Example                         |
| --------------------------------- | --------- | ------------------------------- |
| `surface`                         | `surface` | `surface=terminal`              |
| `terminalMode`                    | `tm`      | `tm=command`                    |
| `researchStage`                   | `rs`      | `rs=validate`                   |
| `assetGroups`                     | `ag`      | `ag=CEFI,DEFI`                  |
| `instrumentTypes`                 | `it`      | `it=spot,perp`                  |
| `families`                        | `fam`     | `fam=ARBITRAGE_STRUCTURAL`      |
| `archetypes`                      | `arch`    | `arch=PRICE_DISPERSION`         |
| `shareClasses`                    | `sc`      | `sc=btc,usdt`                   |
| `engagement`                      | `eng`     | `eng=monitor`                   |
| `executionStream`                 | `stream`  | `stream=paper`                  |
| `workspaceId`                     | `ws`      | `ws=arbitrage-command`          |
| `asOfTs`                          | `as`      | `as=2026-04-29T00:00:00Z`       |
| `coverageStatuses` _(advanced)_   | `cov`     | `cov=SUPPORTED,PARTIAL`         |
| `maturityPhases` _(advanced)_     | `mat`     | `mat=paper_14d,live_stable`     |
| `productRoutings` _(advanced)_    | `route`   | `route=dart_only,both`          |
| `availabilityStates` _(advanced)_ | `avail`   | `avail=PUBLIC,CLIENT_EXCLUSIVE` |

The advanced keys (`cov` / `mat` / `route` / `avail`) are normally hidden from buyer-facing URLs — they're applied
implicitly by the `StrategyAvailabilityResolver` (§4.5) per persona. They MUST round-trip on the URL for admin / QA /
deep-link debugging, but they don't appear in copy-paste links shared with prospects.

**Terminal example:**

```
?surface=terminal&tm=command&ag=CEFI,DEFI&it=spot,perp&fam=ARBITRAGE_STRUCTURAL&arch=PRICE_DISPERSION&eng=monitor&stream=paper&ws=arbitrage-command
```

**Research example:**

```
?surface=research&rs=validate&ag=CEFI,DEFI&fam=ARBITRAGE_STRUCTURAL&eng=replicate&stream=paper&ws=research-to-live
```

Rules:

1. URL params beat localStorage.
2. localStorage beats defaults.
3. persona / questionnaire defaults apply only when no saved workspace/scope exists.
4. every internal navigation link preserves scope via `linkWithScope(href)`.
5. every page that participates in DART hydrates scope from URL on mount.
6. browser back/forward restores previous scope.
7. `stream=live` is honoured on hydration **only** if persona has live-trading entitlement; otherwise silently
   downgrades to `paper` (see §4.3 safety contract).

Core utilities to ship:

```
useWorkspaceScope()
WorkspaceScopeProvider
serializeWorkspaceScope(scope)
parseWorkspaceScope(searchParams)
linkWithScope(href)
matchesScope(row, scope)
```

Reuse rules:

- `lib/architecture-v2/catalogue-filter.ts` already has `serialiseCatalogueFilter()` + `parseCatalogueFilter()` — extend
  that surface; do not fork.
- `lib/architecture-v2/family-filter.ts::matchesFamily()` becomes the implementation seed for
  `matchesScope(row, scope)`.
- `lib/architecture-v2/user-instrument-types.ts::instrumentTypesForUser()` (shipped in the prior tile-split round) seeds
  `scope.strategyIds` from entitled + FOMO-teaser strategies on cold mount.

---

## 8. Workspace presets — eight starter cockpits (all ship in v1)

```ts
type WorkspacePreset = {
  id: string;
  label: string;
  description: string;
  bestFor: string[];
  defaultScope: Partial<WorkspaceScope>;

  // Surface + foreground mode/stage defaults
  defaultSurface: WorkspaceScope["surface"];
  defaultTerminalMode?: WorkspaceScope["terminalMode"];
  defaultResearchStage?: WorkspaceScope["researchStage"];

  // 2026-04-29: every preset declares an engagement default + which engagement
  // toggles are supported. Cockpit toolbar shows the toggle when supported.
  defaultEngagement: "monitor" | "replicate";
  defaultExecutionStream: "paper" | "live"; // always "paper" when defaultEngagement === "replicate" (§4.3)
  supportsEngagement: Array<"monitor" | "replicate">;

  // Widgets split by engagement so the toggle is real (different bundles for
  // monitor vs replicate at the same scope + surface + mode).
  monitorWidgetIds: string[];
  replicateWidgetIds?: string[]; // omitted iff supportsEngagement = ["monitor"]
  lockedWidgetIds?: string[];

  layout?: unknown;
  primaryAction?: { label: string; href: string };
};
```

| Preset                        | For                                                               | Default scope                                                                 | Default surface · mode/stage | Default engagement | Monitor widgets                                                                                                                                                                              | Replicate widgets                                                                                                                                                               |
| ----------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Executive Overview**        | CIO · allocator · investor · stakeholder                          | (broad)                                                                       | `reports`                    | monitor (only)     | AUM · P&L · drawdown · risk · exposure · strategy health · top opportunities · incidents · reporting status                                                                                  | (n/a — execs don't hand-trade)                                                                                                                                                  |
| **Live Trading Desk**         | Trader · PM · execution operator                                  | (broad)                                                                       | `terminal / command`         | monitor (toggle)   | Positions · orders · fills · alerts · execution quality · risk limits · venue health · open exceptions                                                                                       | Trade builder · manual order pad · venue-routing helper · paper/live toggle · leg tracker · slippage forecast · pre-trade risk                                                  |
| **Arbitrage Command**         | Arbitrage-focused buyer                                           | CeFi+DeFi · spot/perp · ARBITRAGE_STRUCTURAL · PRICE_DISPERSION/BASIS/FUNDING | `terminal / command`         | monitor (toggle)   | Spread monitor · opportunity feed · cross-venue liquidity · leg state · hedge state · funding/basis · stale-quote alerts · execution slippage · P&L attribution · positions · reconciliation | Spread builder · leg-by-leg simulator · hedge calculator · "place leg 1 / confirm / place leg 2" stepper · stale-quote guard · paper-fill simulator · convergence unwind helper |
| **DeFi Yield & Risk**         | DeFi yield · lending · staking · collateral · protocol-risk buyer | DEFI · CARRY_AND_YIELD                                                        | `terminal / command`         | monitor (toggle)   | Protocol exposure · lending rates · staking yields · reward APR · collateral health · LTV · liquidation risk · bridge/chain exposure · gas · MEV alerts · protocol health                    | Yield-rotation builder · supply / borrow simulator · collateral health pre-check · gas-cost forecast · transaction sequencer · approval helper                                  |
| **Volatility Research Lab**   | Options / vol / derivatives buyer                                 | option · VOL_TRADING · venues = `{DERIBIT, CME}` (v1 — expanding later)       | `research / validate`        | replicate (toggle) | Vol surface · skew · term structure · Greeks · straddle / strangle candidates · vega exposure · gamma risk · vol model fit · backtest candidates                                             | Combo builder · Greek pre-trade calculator · scenario shocker · margin pre-check · synthetic delta builder · 0DTE gamma scalper                                                 |
| **Sports / Prediction Desk**  | Sports · odds · prediction markets · event-driven                 | SPORTS+PREDICTION · EVENT_DRIVEN                                              | `terminal / markets`         | monitor (toggle)   | Fixtures / events · odds movement · market depth · event risk · liquidity · position exposure · execution state · arb opps · settlement                                                      | Bet ladder · stake-sizing helper · cross-book arb stepper · event-risk pre-check · settlement-window watcher                                                                    |
| **Signals-In Monitor**        | External signal provider · regulatory umbrella · BYO-strategy     | (signals-flavoured)                                                           | `signals`                    | monitor (only)     | Signal intake status · payload validation · signal freshness · rejected signals · routing state · execution mapping · paper/live · reporting coverage                                        | (n/a — signals routing is by definition automated)                                                                                                                              |
| **Research-to-Live Pipeline** | DART Full buyer                                                   | (broad)                                                                       | `research / validate`        | replicate (toggle) | Strategy candidates · backtest results · paper state · promotion readiness · config version · approval status · live compatibility · deployment handoff                                      | Per-stage walk-through (Discover→Build→Train→Validate→Allocate→Promote) · "manually run the next step" pad · paper-fill replay · approval ack                                   |

Six of the eight presets support both monitor + replicate engagements. Executive Overview and Signals-In Monitor are
monitor-only by their nature (no hand-trading flow makes sense for either). The cockpit toolbar shows the engagement
toggle only when `supportsEngagement.length > 1`.

**Each preset declares an explicit strategy backing** so the resolver in §4.5 has deterministic targets. This is what
stops "Arbitrage Command" being just a UI label pointing at a vague set of strategies:

```ts
// lib/cockpit/preset-archetype-map.ts (NEW, Phase 6)
//
// Some presets are static archetype lists; others depend on user / subscription
// / maturity / entitlement and must use the runtime resolver. The discriminated
// union lets the cockpit handle both deterministically.
type PresetArchetypeBinding =
  | { kind: "explicit"; archetypeIds: readonly string[] }
  | {
      kind: "resolver";
      resolver:
        | "signal-routing-visible" // all archetypes reachable via Signals-In routing for this user
        | "subscribed-only" // user's owned strategies (live + paper)
        | "visible-by-maturity" // all archetypes the resolver returns owned/available_to_request,
        // grouped by maturity phase (research → paper → live)
        | "owned-or-mandate-allocated"; // for IM Executive Overview
    };

export const PRESET_ARCHETYPE_MAP: Record<string, PresetArchetypeBinding> = {
  "arbitrage-command": {
    kind: "explicit",
    archetypeIds: [
      "ARBITRAGE_PRICE_DISPERSION",
      "LIQUIDATION_CAPTURE",
      "CARRY_BASIS_PERP",
      "CARRY_BASIS_DATED",
      "STAT_ARB_PAIRS_FIXED",
    ],
  },
  "defi-yield-risk": {
    kind: "explicit",
    archetypeIds: [
      "YIELD_ROTATION_LENDING",
      "YIELD_STAKING_SIMPLE",
      "CARRY_RECURSIVE_STAKED",
      "CARRY_STAKED_BASIS",
      "LIQUIDATION_CAPTURE",
    ],
  },
  "volatility-research-lab": {
    kind: "explicit",
    archetypeIds: ["VOL_TRADING_OPTIONS", "ARBITRAGE_PRICE_DISPERSION"],
  },
  "sports-prediction-desk": {
    kind: "explicit",
    archetypeIds: [
      "ML_DIRECTIONAL_EVENT_SETTLED",
      "ARBITRAGE_PRICE_DISPERSION",
      "MARKET_MAKING_EVENT_SETTLED",
      "EVENT_DRIVEN",
    ],
  },
  "signals-in-monitor": { kind: "resolver", resolver: "signal-routing-visible" },
  "research-to-live-pipeline": { kind: "resolver", resolver: "visible-by-maturity" },
  "live-trading-desk": { kind: "resolver", resolver: "subscribed-only" },
  "executive-overview": { kind: "resolver", resolver: "owned-or-mandate-allocated" },
};
```

**Strategy-backing strength** (each preset is tagged so the wizard, the suggestions panel, and the locked-preview
machinery can reason about how "real" each preset feels for a given persona):

| Preset                        | Strategy-backing strength        | Notes                                                                                                                                                                                                                                                                                                                                                                                        |
| ----------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Arbitrage Command**         | strategy-backed (strong)         | `ARBITRAGE_PRICE_DISPERSION` has supported CeFi spot, DeFi spot/perp, sports/prediction; partial CeFi perp/options + TradFi. Flagship preset.                                                                                                                                                                                                                                                |
| **DeFi Yield & Risk**         | strategy-backed (strong)         | Real coverage on yield-rotation / staking / recursive-staked / staked-basis.                                                                                                                                                                                                                                                                                                                 |
| **Volatility Research Lab**   | strategy-backed (medium)         | **v1 venue scope: Deribit + CME only** (TradFi options partial; DeFi options blocked). Wording must say "options on Deribit and CME, expanding". Do not imply broader options coverage.                                                                                                                                                                                                      |
| **Sports / Prediction Desk**  | strategy-backed (medium-strong)  | ML event-settled + arb / market-making for events have supported paths; some rules / event-driven cells partial-or-blocked. Cards need capability-aware copy.                                                                                                                                                                                                                                |
| **Signals-In Monitor**        | service-backed                   | Same catalogue, different service capability. Must NOT pretend Signals-In users can train / promote Full-only archetypes.                                                                                                                                                                                                                                                                    |
| **Research-to-Live Pipeline** | strategy-backed (DART Full only) | Must respect maturity gates. Some strategies are research-only, some paper-stable, some live. Resolver decides per-instance which stage label is honest.                                                                                                                                                                                                                                     |
| **Live Trading Desk**         | demo-only-until-subscribed       | Generic cockpit. Populated from the user's subscriptions; empty state must say so plainly.                                                                                                                                                                                                                                                                                                   |
| **Executive Overview**        | demo-only-until-subscribed       | Reporting-flavoured. Weak if user has no subscriptions. Empty-state copy: _"No live reporting data yet. This demo uses representative allocator reporting views. Connect a mandate or select a subscribed strategy to replace demo data."_ The cockpit shows the demo dataset behind a persistent "demo data" badge until the resolver returns at least one `owned` or `read_only` instance. |

`WorkspacePreset` carries the strength label:

```ts
type PresetStrategyBacking =
  "strategy-backed-strong" | "strategy-backed-medium" | "service-backed" | "demo-only-until-subscribed";

interface WorkspacePreset {
  // ... existing fields ...
  strategyBacking: PresetStrategyBacking;
  archetypeIds: readonly string[]; // from PRESET_ARCHETYPE_MAP
  v1VenueConstraints?: readonly string[]; // e.g. Vol Lab → ["DERIBIT", "CME"]
  emptyStateCopy?: string; // shown when resolver returns zero owned + zero available_to_request
}
```

Rendering rule: when the resolver returns zero `owned` AND zero `available_to_request` instances for a preset, the
cockpit shows the preset's `emptyStateCopy` plus a primary CTA matching the strategy-backing label (allocate / request
access / contact). It does **not** silently render mock data without a "demo data" badge.

### 8.1 Scope-aware next-actions (the "guided operating system" beat)

A small but important component that turns the cockpit from "nice dashboard" into "guided operating system." When the
user is in a scope, surface 2–4 contextual next actions in the cockpit toolbar / sidebar.

**Examples:**

| Scope                                            | Suggested next actions                                                                                                 |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Arbitrage Command + scope = ARBITRAGE_STRUCTURAL | Review live spreads · Open execution leakage · Compare batch/live drift · Request DART Full arbitrage access           |
| DeFi Yield + scope = DEFI / CARRY_AND_YIELD      | Review protocol exposure · Check liquidation risk · Compare lending rates · Open DeFi yield research                   |
| Signals-In Monitor + scope = signals             | Inspect rejected signals · View payload schema · Open execution mapping · Request signal quality analytics             |
| Volatility Lab + scope = option / VOL_TRADING    | Open the vol surface · Build a vega-neutral combo · Run a 0DTE gamma scenario · Request term-structure research access |

**Component:**

```ts
// components/cockpit/scope-aware-next-actions.tsx (NEW, Phase 6 / 7)
type NextAction = {
  id: string;
  label: string;
  description?: string;
  scopeMatch: Partial<WorkspaceScope>;
  href?: string; // navigate (linkWithScope-aware)
  surfaceChange?: WorkspaceScope["surface"];
  terminalModeChange?: WorkspaceScope["terminalMode"];
  researchStageChange?: WorkspaceScope["researchStage"];
  engagementChange?: WorkspaceScope["engagement"];
  executionStreamChange?: WorkspaceScope["executionStream"]; // paper-only by default;
  // a value of "live" routes through
  // the §4.3 confirm dialog
  ctaKind?: "primary" | "secondary" | "upgrade";
};
```

A registry of next-actions lives in `lib/cockpit/next-actions.ts`. The cockpit picks 2–4 whose `scopeMatch` overlaps the
active scope, sorted by ctaKind (primary first). Locked-preview "Learn more" links live in this same registry as
`ctaKind: "upgrade"` actions, so the upgrade asks are scope-contextual by construction.

---

## 9. Persona and questionnaire seeding

Inputs: persona · entitlements · `assigned_strategies` · questionnaire answers · selected asset categories · selected
instrument types · strategy style · market-neutral preference · live/paper/research interest.

First-run flow — **four steps**:

```
Welcome. Let's set up your workspace.

0. System map
   ┌────────────────────────────────────────────────────────────┐
   │ Here's how DART is laid out:                               │
   │   Research:  Discover → Build → Train → Validate → Allocate→ Promote │
   │   Terminal:  Command · Markets · Strategies · Explain · Ops│
   └────────────────────────────────────────────────────────────┘
   [Continue]    (shared content from lib/cockpit/ia-explainer-content.ts)

1. Recommended starter:
   - Arbitrage Command            (auto-recommended from persona)
   - DeFi Yield & Risk
   - Volatility Research Lab
   - Research-to-Live Pipeline
   - Build from scratch

2. Initial scope:
   asset groups · instrument types · family · archetype

3. Mode, engagement, and execution stream:
   Surface:     ●Terminal  ○Research
   Mode:        ●Command   ○Markets  ○Strategies  ○Explain  ○Ops
                  (or research stage if surface=research)
   Engagement:  ●Monitor   ○Replicate
   Stream:      ●Paper     ○Live  (Live disabled for demo personas)

[Build my cockpit]
```

**Safety:** `executionStream` defaults to `paper` whenever `engagement === "replicate"`. Live requires the explicit
confirm dialog defined in §4.3, and is **disabled** in the wizard for any persona without live-trading entitlement (most
demo personas). The wizard never silently flips Stream to Live.

A user can skip onboarding, but the recommended preset must remain available from the cockpit toolbar.

**Reuse, don't reinvent:** the wizard's Step 2 (scope) MUST call the existing questionnaire mapping
(`lib/questionnaire/seed-catalogue-filters.ts::seedFiltersFromQuestionnaire`) to seed the initial scope from the user's
questionnaire answers, rather than re-deriving the mapping. The mapping rules already exist in PM codex:

- `categories` → asset_groups
- `strategy_style` → families
- `market_neutral` → expands families
- `risk_profile` → coverage status preference
- `leverage_preference === "none"` → exclude options
- `share_class_preferences` → share classes (now a real `WorkspaceScope` axis per §4.4, no longer advisory)
- `instrument_types` was advisory in earlier drafts; **promoted** to a real `WorkspaceScope.instrumentTypes` filter for
  cockpit widget targeting (catalogue-row filtering remains tolerant — empty intersection falls through to "match all"
  rather than "no results", per `use-strategy-scoped-instruments.ts` pattern).

The wizard then lets the user edit the seeded scope before clicking "Build my cockpit". This keeps onboarding signal-in
/ signal-out consistent with allocation requests downstream.

---

## 10. Widget contract

```ts
type DartWidgetMeta = {
  id: string;
  label: string;
  description: string;

  // Where the widget belongs (surface + foreground mode/stage)
  surfaces: Array<"terminal" | "research" | "reports" | "signals" | "ops">;
  terminalModes?: Array<"command" | "markets" | "strategies" | "explain" | "ops">;
  researchStages?: Array<"discover" | "build" | "train" | "validate" | "allocate" | "promote">;

  // 2026-04-29: engagement + execution-stream gating
  engagements?: Array<"monitor" | "replicate">;
  executionStreams?: Array<"paper" | "live">;

  // Filter axes
  assetGroups?: string[];
  instrumentTypes?: string[];
  families?: string[];
  archetypes?: string[];
  entitlements?: string[];

  recommendedForPresets?: string[];
  importance?: "primary" | "secondary" | "supporting";
  scopePredicate?: (scope: WorkspaceScope) => boolean;
};
```

Behaviour on scope change: relevant widgets become primary; irrelevant widgets hide / grey-out / show "out of scope"
placeholder; suggestions update; locked previews update; mock data stream updates. **Empty scope → match broad widgets**
(the unfiltered default the user can drill into).

Engagement / execution-stream gating: widgets that only make sense in `replicate` (manual order pad, leg stepper, hedge
calculator, paper-fill simulator) declare `engagements: ["replicate"]`. Passive monitoring widgets (kill-switch,
exception alerts, auto-P&L) declare `engagements: ["monitor"]`. Most data-heavy widgets (positions, prices, alerts)
declare both. Widgets that route to live execution (manual order pad) declare `executionStreams: ["paper", "live"]`;
pure simulators declare `executionStreams: ["paper"]`.

---

## 11. Scoped data provider — gradual migration, not big-bang

**Critical rule from the buyer-emotional spec:** do not delete all asset-group data contexts at once. The current tree
has dozens of widgets calling `useOptionsData()` / `useDeFiData()` / etc. Big-bang replacement breaks too much at once.

**Transition strategy:**

1. Create `ScopedDataProvider` and `useScopedData()`.
2. Add compatibility shims:
   ```ts
   // components/widgets/options/options-data-context.tsx
   function useOptionsData() {
     return useScopedData({ instrumentTypes: ["option"] });
   }
   ```
3. Migrate widgets in priority order:
   1. P&L
   2. Positions
   3. Orders / fills
   4. Alerts
   5. Risk
   6. Strategy health
   7. Spread / opportunity monitor
   8. Funding / basis
   9. DeFi exposure
   10. Backtest / activity widgets
   11. Options widgets
   12. Sports / prediction widgets
   13. Reporting widgets
4. Remove old providers only after migration is stable.

---

## 12. Contextual FOMO / locked previews — Catalogue FOMO ≠ Cockpit FOMO

**Critical distinction (per §4.6 four-state taxonomy):** the original plan conflated two genuinely different FOMO
surfaces. Implementation must keep them separate:

- **Catalogue FOMO** = strategy-instance / allocation FOMO. Lives at `/services/strategy-catalogue` Reality + Explore
  tabs. Stricter rules: pre-maturity instances are _hidden_; product-routing failures are _hidden_; only
  `available_to_request` instances surface in Explore. CTA is human-gated allocation/access request.
- **Cockpit FOMO** = workflow / capability FOMO. Lives inside the cockpit (Terminal modes, Research stages). Looser
  rules: shows contextual locked previews of _what the user could do with their existing strategies_ if they upgraded
  their tier or completed a workflow gate. CTA is upgrade-tier or complete-questionnaire/KYC.

The two surfaces share the `LockedPreview` data model and the `<ContextualLockedPreview>` component but apply different
filter logic on top. The resolver from §4.5 returns a `StrategyVisibilityState`; the consumer chooses how to render
based on surface (catalogue vs cockpit) and the visibility state.

```ts
type LockedPreview = {
  id: string;
  title: string;
  scopeMatch: Partial<WorkspaceScope>;
  buyerValue: string;
  lockedCapabilities: string[];
  cta: string;
};
```

Replace generic _"Upgrade to access this feature."_

**Arbitrage:**

> _Arbitrage Promotion Checks locked._ Validate whether a spread strategy is live-compatible before deployment. Includes
> execution-aware backtest checks, legging risk analysis, stale-quote detection, venue liquidity checks, batch/live
> drift comparison. CTA: _Request DART Full access._

**DeFi:**

> _DeFi Yield Research locked._ Unlock lending rotation, recursive collateral, staking basis, and protocol-risk-aware
> allocation views across Aave, Morpho, Lido, Jito, Kamino, and Hyperliquid.

**Volatility:**

> _Volatility Lab locked._ Unlock term-structure, dispersion, 0DTE gamma, synthetic delta, and cross-asset
> volatility-spread research workflows.

**Signals-In:**

> _Signal Quality Analytics locked._ Measure signal freshness, rejection causes, execution mapping, and downstream P&L
> attribution before scaling external capital.

---

## 13. Mock-mode liveness

Tier 0 demo mode should feel alive. P&L ticks · prices drift · funding rates update · alert count changes · signal
events arrive · backtests progress · jobs queued → running → complete · activity feed updates · occasional
warning/exception surfaces.

`MockEventLoop` features: subscribable streams · bounded random walk · deterministic seed · scope-aware data streams ·
pace control · freeze mode.

URL controls:

```
?freeze=true   → halt all loops (Playwright determinism, screenshots)
?pace=1        → 1× real-time (default)
?pace=10       → accelerated demo walkthroughs
```

Mock liveness must respect `freeze=true` across both monitor and replicate engagement, including simulated paper fills,
stepper progress, pre-trade risk checks, and manual-vs-algo comparison data. A frozen run is bit-identical between
monitor and replicate; only the widget bundle differs.

---

## 14. Route and IA strategy — collapse comes LAST

Do **not** start by deleting routes. Route collapse is valuable but high-churn (Playwright rewrites, route-redirect
bookkeeping, persona-shape re-mapping, broken bookmarks). The correct order is:

1. Make scope real
2. Make scope visible
3. Simplify Terminal (Command/Markets/Strategies/Explain/Ops)
4. Simplify Research (Discover/Build/Train/Validate/Allocate/Promote)
5. Make widgets scope-aware
6. Add presets
7. Add contextual locked previews
8. Add mock liveness
9. **Then** collapse routes — old single-purpose pages redirect into `/services/workspace?surface=terminal&tm=command`
   etc.

Existing pages remain as deep links during phases 1–8; they keep working. Phase 9 is when we retire them. This protects
against shipping a half-built cockpit alongside a broken legacy.

---

## 15. Ownership rules for duplicated concepts

| Concept                         | Owner                         |
| ------------------------------- | ----------------------------- |
| Strategy universe               | Catalogue / Research Discover |
| Building / testing strategies   | DART Research                 |
| Live / paper strategy operation | DART Terminal                 |
| P&L · risk · attribution        | Terminal Explain / Reports    |
| External signals                | Signals-In / Strategy Intake  |
| Health · logs · incidents       | Ops                           |
| Client-ready reporting          | Reports                       |

**Strategy-page distinction (kill the duplicate-feeling):**

- _Catalogue_ = what exists or could be enabled.
- _Research_ = what we are building, testing, validating, or promoting.
- _Terminal_ = what is running, paused, papering, live, or failing.
- _Reports_ = what happened and how to explain it.

### 15.1 Where this table lives — IA contract, not a product page

The ownership-rules table is **developer-facing IA**, not a runtime UI surface. It guides:

1. **Engineers + agents** doing Phases 3 / 4 / 9 — they consult it when deciding which surface a concept belongs to
   (e.g. "should the live strategy roster live in Catalogue or Terminal?" → Terminal Strategies, per the table).
2. **The codex SSOT** — when this plan ships, the table propagates into
   `unified-trading-pm/codex/14-playbooks/dart/dart-terminal-vs-research.md` (or a sibling doc) as the canonical IA
   lock-down. Future plans reference it; surfaces that violate it get flagged.

**Buyers / demo prospects do NOT see the table directly.** They experience the _result_ (no duplicate strategy lists; no
"wait, didn't I just see this on another page?"). If a prospect feels the system is well-organised, the table did its
job.

### 15.2 Buyer-facing IA explainer — locked in for v1

The user confirmed (2026-04-29) that demo prospects need an explicit IA explainer, **not** in the Admin tab. Two
surfaces ship in v1:

1. **Onboarding wizard step 0** (Phase 6 addendum): one screen before the preset selector. _"Here's how DART is laid out
   — Discover, Build, Train, Validate, Allocate, Promote in Research; Command, Markets, Strategies, Explain, Ops in
   Terminal. Pick where you want to start."_ Shown once, dismissible, saved per-user. Maps directly to the Phase 4 / 3
   IA stages.
2. **`/help/system-map` page** (Phase 7 addendum): standalone help page reachable from the global help menu, from every
   locked-preview's "Learn more" link, and from a "?" button next to the scope bar. Same content as the wizard step,
   deeper — includes the ownership-rules table from §15, the canonical mode/stage descriptions from §5, and the ScopeBar
   contract from §6/§7. Linkable, shareable, indexable.

Both surfaces source from a single content module so wording can't drift:

```
lib/cockpit/ia-explainer-content.ts   (NEW — ownership table + mode descriptions + stage descriptions)
components/cockpit/system-map.tsx     (NEW — shared renderer used by wizard step 0 and /help/system-map)
```

Phase impact: +~1 day to Phase 6 (wizard step) + ~half-day to Phase 7 (help page).

---

## 16. Copy and naming rules

**Critical guardrail (added 2026-04-29):** the product/surface names **DART Terminal** and **DART Research** stay. They
are the brand. The renames in the table below apply to _modes / hero labels / page titles inside_ those surfaces, not to
the surfaces themselves.

- Tile label on `/dashboard` = "DART Terminal" (unchanged)
- Inside DART Terminal, the _Command_ mode hero can be labelled "Live Command Surface"
- Tile label on `/dashboard` = "DART Research" (unchanged)
- Inside DART Research, the strategies hero can be labelled "Strategy Research Workbench"

| Avoid as page/mode label    | Prefer as page/mode label                               |
| --------------------------- | ------------------------------------------------------- |
| Terminal (as a _page_ hero) | Live Command (mode hero inside DART Terminal)           |
| Feature ETL                 | Build data and features                                 |
| Execution Research          | Execution simulation                                    |
| Strategy Config             | Configuration versions                                  |
| Observe (as page hero)      | Monitor live behaviour (mode hero inside DART Terminal) |
| Widget grid                 | Workspace                                               |
| Upgrade                     | Request access / Unlock workflow                        |
| Research page               | Strategy Research Workbench (hero inside DART Research) |

Pattern: **Buyer-facing label** (primary) — _internal detail as subtitle_. Example:

- Build data and features — _Feature pipelines, freshness checks, and dataset coverage._
- Not: Feature ETL — _Configure pipelines and data jobs._

---

## 17. Phase plan — 9 phases, scope-real first, route-collapse last

### Phase 1 — Unified workspace scope (foundation)

Build `WorkspaceScopeStore` · `WorkspaceScopeProvider` · `useWorkspaceScope()` · `parseWorkspaceScope()` ·
`serializeWorkspaceScope()` · `linkWithScope()` · `matchesScope()`. Replace / merge existing parallel filter/scope
contexts. URL hydration · localStorage fallback · dashboard filter writes through to global scope · remove local-only
state in `FamilyArchetypeAssetGroupBrowser`. Navigation preserves scope. Refresh restores scope.

**Acceptance:** Select Arbitrage on dashboard. Navigate Terminal → Research → Reports. Refresh. Scope remains active
everywhere.

**Critical files:**

- `lib/stores/workspace-scope-store.ts` (NEW)
- `lib/stores/global-scope-store.ts` (BRIDGE → DEPRECATE → DELETE in Phase 1D only — never delete in 1A/B/C)
- `lib/context/dashboard-filter-context.tsx` (BRIDGE → DEPRECATE → DELETE in Phase 1D only — never delete in 1A/B/C)
- `lib/architecture-v2/catalogue-filter.ts` (extend)
- `lib/architecture-v2/family-filter.ts` (generalise `matchesFamily` → `matchesScope`)
- `app/(platform)/layout.tsx` (wrap in `<WorkspaceScopeProvider>`)
- `lib/utils/nav-helpers.ts` (NEW `linkWithScope`)
- `app/(platform)/services/research/_components/family-archetype-asset-group-browser.tsx` (replace local state with
  `useWorkspaceScope()`)

### Phase 2 — Shared scope bar

Compact + expanded `DartScopeBar` rendered on Dashboard, Terminal, Research, Catalogue, Reports, Signals. Reset / clear
· recommended-preset indicator · save / edit workspace.

The scope bar / cockpit toolbar must expose **Surface · Terminal Mode (or Research Stage) · Engagement · Execution
Stream** controls in addition to the five filter-axis chips. The Engagement toggle appears only when the active preset's
`supportsEngagement` includes both values. The Execution Stream toggle appears only where relevant (replicate
engagement, or monitoring a paper-vs-live A/B) and defaults to `paper` for replicate per the §4.3 safety contract. Live
requires the explicit confirm dialog and is disabled for personas without live-trading entitlement.

**Acceptance:** user can always answer _what am I looking at? why am I seeing this? how do I change it?_ The Engagement
toggle is reachable in ≤1 click on every cockpit surface that supports it. The Live option is reachably-disabled
(visible but not clickable, with tooltip) for demo personas.

### Phase 3 — Terminal IA simplification

Replace the 16-tab TRADING_TABS sprawl with five modes: Command · Markets · Strategies · Explain · Ops. Old page
concepts move under these modes. Keep old routes as deep links for now. Update copy. Default mode is scope-aware.

**Acceptance:** A user sees five Terminal choices, not dozens. Arbitrage scope opens an arbitrage-relevant Terminal.
DeFi scope opens a DeFi-relevant Terminal.

### Phase 4 — Research IA simplification

Replace internal-tab model with six journey stages: Discover · Build · Train · Validate · Allocate · Promote. Add a
journey rail / stage cards. Scope-aware research cards. Research-to-live handoff messaging. Heavy specialist pages (ML
training, allocator backtests) preserved as deep links.

**Acceptance:** User understands how an idea moves from catalogue to live. Feature/ML tooling exists but doesn't
overwhelm first impression.

### Phase 5 — Scope-reactive widgets

Add widget metadata (`scopePredicate` · `modes` · `assetGroups` · `instrumentTypes` · `families` · `archetypes` ·
`entitlements` · `recommendedForPresets` · `importance`). Build `ScopedDataProvider` + `useScopedData()`. Add
compatibility shims (`useOptionsData = () => useScopedData({instrumentTypes:["option"]})`). Migrate top-priority widgets
first (per Section 11 list). Add grey/out-of-scope state. Scope-aware suggestions.

**Acceptance:**

- Select Arbitrage → spread / opportunity / funding / leg widgets become primary.
- Select DeFi Yield → protocol / yield / collateral widgets become primary.
- Select Options → vol / Greeks / skew widgets become primary.
- Toggle Replicate → manual trade builder / leg tracker / pre-trade risk widgets become primary while monitoring widgets
  fade or move to secondary positions in the grid. Layout positions are preserved per scope-set so the user's saved
  cockpit shape doesn't reshuffle on toggle.

### Phase 6 — Starter cockpit presets

Eight presets (Executive Overview · Live Trading Desk · Arbitrage Command · DeFi Yield & Risk · Volatility Research Lab
· Sports/Prediction Desk · Signals-In Monitor · Research-to-Live Pipeline). Preset selector. Persona + questionnaire
recommend a default. Seed first workspace. "Build from scratch" remains as secondary option. Save chosen workspace.

**Acceptance:** Fresh user signs in. System recommends a cockpit. User lands in a populated workspace. No blank grid
unless user chooses it.

### Phase 7 — Contextual FOMO

Build `ContextualLockedPreview` + `LockedPreview` model (Section 12). Map locked previews to scope. Replace generic
upgrade cards. Scope-aware CTAs (Arbitrage user sees arbitrage value, DeFi user sees DeFi value, Signals-In user sees
signal value).

**Acceptance:** Locked-state copy changes with scope. The "what I get if I upgrade" message is specific to what the user
is currently looking at.

### Phase 8 — Mock-mode liveness

`MockEventLoop` (Section 13). P&L drift · price/funding updates · alert emitter · signal emitter · backtest progression
· activity feed · `freeze=true` · `pace` control.

**Replicate-engagement coverage:** in `engagement === "replicate"` mode, the MockEventLoop also drives:

- simulated paper fills as the user completes each step of the trade builder (configurable slippage + latency profiles
  per asset_group);
- per-leg progress in the stepper widget (queued → routed → partial-fill → fill);
- pre-trade risk checks that update as the user changes order parameters;
- "manual-vs-algo comparison" data so Explain mode can surface deltas between what the user did vs what the deployed
  strategy would have done at the same moment.

Without this, replicate engagement risks becoming UI chrome with no consequences — a fatal demo flaw.

**Acceptance:** Demo data moves naturally. Backtests progress. Alerts arrive. Replicate-mode trades fill with realistic
slippage on paper. Explain shows manual-vs-algo deltas. `freeze=true` makes Playwright deterministic.

### Phase 9 — Route collapse and cleanup (LAST)

Identify old single-widget pages. Redirect them to scoped cockpit modes. Preserve deep specialist research pages (ML
training, allocator backtests, IM allocator, admin). Update service registry. Update Playwright specs. Remove duplicate
nav entries. Keep old URLs working via redirects so external bookmarks don't break.

**Acceptance:** Navigation destinations drop significantly — target ~50 top-level / sub-route distractions → **fewer
than 10 primary navigation decisions** at any one moment. Deep specialist research pages, Strategy Catalogue, Investment
Management, Admin, and Signals remain reachable as distinct surfaces; the saving comes from collapsing single-widget
trading + observe pages into the cockpit. Old URLs redirect safely with scope preserved. No major workflow breaks.

---

## 18. Example target flows

### Flow A — Arbitrage buyer

1. Sign in. System recommends _Arbitrage Command_.
2. Scope defaults to _CeFi + DeFi · Spot / Perp · Arbitrage · Price Dispersion · Demo_.
3. Open Terminal → Command mode. Widgets: spread monitor · opportunity feed · venue liquidity · leg state · hedge state
   · funding/basis · slippage · P&L attribution · alerts.
4. Open Research. Arbitrage candidates + validation paths. Locked cards: cross-domain arbitrage · promotion checks ·
   liquidation capture.
5. Feel: _"This is exactly what we would need to run arbitrage seriously."_

### Flow B — DeFi yield buyer

1. Select _DeFi Yield_. Scope: _DeFi · Lending / Staking / Collateral · Carry & Yield · Demo_.
2. Terminal: protocol exposure · lending rates · staking yield · collateral health · LTV · liquidation alerts ·
   chain/protocol risk.
3. Research: yield rotation · recursive collateral strategies · protocol-risk-aware allocation · backtest candidates.
4. Locked previews: DeFi-specific.

### Flow C — DART Full buyer

1. _Research-to-Live Pipeline_. Lifecycle visible: Discover → Build → Train → Validate → Allocate → Promote → Run →
   Explain.
2. Research → strategy candidates → Validate → backtest/paper/stress/batch-live → Promote → config version + readiness →
   Terminal → same strategy in paper/live → Explain → P&L + execution attribution.
3. Feel: _"This avoids rebuilding between research, paper, and live."_

### Flow D — Signals-In client

1. _Signals-In Monitor_. Scope focuses on external signals.
2. Dashboard: signal intake health · payload validation · signal freshness · rejected signals · routing state ·
   paper/live execution · reporting coverage.
3. Locked: signal analytics + advanced routing.
4. Feel: _"I can keep my signal IP while Odum gives me execution, reporting, and operating infrastructure."_

---

## 19. Success criteria

1. Scope is the single source of truth.
2. Scope persists across navigation, refresh, and copied URLs.
3. DART Terminal has five clear modes.
4. DART Research has six clear stages.
5. The user sees a curated workspace before customization.
6. Widgets react to scope.
7. Locked previews are contextual.
8. Mock mode feels alive.
9. Duplicate strategy surfaces are clarified (per ownership-rules table).
10. Navigation feels smaller even though the product is deeper.
11. A buyer can understand the system within minutes.
12. The buyer thinks: _"This would take us years to build ourselves."_

---

## 20. Non-goals (do not do these first)

1. Do not start with visual polish.
2. Do not add more pages.
3. Do not expose every internal tool at top level.
4. Do not make every widget configurable upfront.
5. Do not force users to build from scratch.
6. Do not delete 50 routes before the new cockpit works.
7. Do not keep multiple competing scope stores.
8. Do not use internal engineering labels as the main buyer language.
9. Do not make locked states generic.
10. Do not let each page manage its own disconnected filter state.

---

## 21. Recommended shipping order (canonical)

```
1. Unified WorkspaceScope                       (Phase 1)
2. Shared Scope Bar                             (Phase 2)
3. Terminal IA simplification                   (Phase 3)
4. Research IA simplification                   (Phase 4)
5. Scope-reactive widget metadata + provider    (Phase 5)
6. Scoped data provider migration               (Phase 5 cont'd)
7. Starter cockpit presets                      (Phase 6)
8. Contextual FOMO / locked previews            (Phase 7)
9. Mock-mode liveness                           (Phase 8)
10. Route collapse and cleanup                  (Phase 9)
```

Fix the structure first, then make the demo feel premium, then clean up the route tree.

---

## 22. Locked decisions (2026-04-29)

- **The nine-phase programme is approved as the target direction, but implementation must be sequential.** Each phase
  lands independently with tests before the next begins. Do not boil the ocean. Route collapse is Phase 9 and must not
  start until Phases 1–8 are stable.
- **All eight starter presets ship in v1:** Executive Overview · Live Trading Desk · Arbitrage Command · DeFi Yield &
  Risk · Volatility Research Lab · Sports/Prediction Desk · Signals-In Monitor · Research-to-Live Pipeline.
- **Six of those eight presets support both `monitor` and `replicate` engagement.** Executive Overview and Signals-In
  Monitor are monitor-only by their nature. The cockpit toolbar surfaces the engagement toggle only when supported.
  Default `executionStream` is `paper` for replicate engagements (live requires an explicit user confirm dialog).
- **Scoped data provider migration uses compatibility shims, not big-bang deletion.** Existing `useOptionsData()` /
  `useDeFiData()` / `useSportsData()` / `usePredictionsData()` become thin wrappers around `useScopedData()` while
  widgets migrate incrementally.
- **DART Terminal and DART Research remain the product surface names.** Inside DART Terminal, use buyer-facing modes:
  Command · Markets · Strategies · Explain · Ops. Inside DART Research, use journey stages: Discover · Build · Train ·
  Validate · Allocate · Promote. The tile labels stay "DART Terminal" / "DART Research"; "Live Command" / "Strategy
  Research Workbench" are mode-level / hero-level labels inside those surfaces, not replacements for the surface name.
- **Buyer-facing copy rules** (Section 16) are non-optional. Internal engineering labels (Feature ETL, Strategy Config,
  etc.) can remain as subtitles or detail captions, not as first-level buyer navigation.
- **Ownership-rules table** (Section 15) defines surface responsibility and propagates into the codex SSOT.
- **Buyer-facing IA explainer ships in v1 on two surfaces:** (a) onboarding wizard step 0 — first-time prospects see the
  map before picking a preset; (b) `/help/system-map` (or `app/(platform)/help/system-map/page.tsx`) — authenticated,
  platform-scoped, anyone can re-find the structure later. Both render from a shared content module. NOT in Admin.
- **Dashboard tile order: DART Terminal LEFT, DART Research RIGHT.** Buyer demo leads with the live cockpit / FOMO
  surface. Research is deep but doesn't deliver the "wow" hit on first load. (This reverses the brief 2026-04-29 swap
  shipped in commit `fec661a3` — that change was made before the engagement-mode dimension and the cockpit narrative
  were locked in; the demo programme works better when Terminal anchors the left-eye.)
- **Strategy availability is not the same as scope.** A `StrategyAvailabilityResolver` (§4.5) sits between the cockpit
  and the catalogue: it combines scope + persona + entitlement + maturity + routing + availability state +
  subscription + share class to return
  `owned | available_to_request | locked_by_tier | locked_by_workflow | hidden | admin_only | read_only`. Every cockpit
  surface (presets, widgets, FOMO, suggestions) consumes the resolver — never the raw scope-match — so the demo never
  offers strategies the user cannot actually access.
- **Hide / lock / tease / reality is a four-state taxonomy** (§4.6). Catalogue FOMO uses stricter hiding (pre-maturity =
  hidden, not greyed); Cockpit FOMO uses contextual locked previews. Don't reuse the same locked-card logic blindly for
  both.
- **`shareClasses` is back in `WorkspaceScope`** (§4.4). Earlier drafts dropped it; reinstating because BTC-neutral /
  ETH-native / USD-USDT / fund-share-class views are real product dimensions per the strategy-lifecycle docs.
- **`instrumentTypes` is now a real filter, not advisory.** Earlier drafts treated it as advisory in the questionnaire;
  cockpit widget targeting requires it to actually filter. Catalogue-row matching remains tolerant — empty intersection
  falls through to "match all" not "no results".
- **Volatility Research Lab v1 venue scope = Deribit + CME only.** Options coverage is genuinely narrow today; the
  preset must say so plainly. TradFi options are partial; DeFi options are blocked. Wording must say "options on Deribit
  and CME, expanding". Do not imply broader options coverage.
- **Each preset declares strategy-backing strength**
  (`strategy-backed-strong | strategy-backed-medium | service-backed | demo-only-until-subscribed`) and an explicit
  archetype map (`PRESET_ARCHETYPE_MAP`). Empty-state copy ships per preset. No preset silently renders mock data
  without a "demo data" badge.
- **6,000+ is the potential configuration space, not the available strategy count.** Live + paper today is ~70-80
  instances; v1 catalogue ceiling ~240-250. Buyer-facing copy uses "potential configuration space" or "combinatoric
  universe", never "strategies available now".
- **Wizard Step 2 reuses `seedFiltersFromQuestionnaire`** (§9). The questionnaire→catalogue-filter mapping already
  exists; the cockpit wizard must consume it, not invent a parallel mapping.

## 23. Critical files (consolidated)

### Do NOT modify (or modify only as noted)

- `app/(platform)/services/investment-management/**` — operational IM allocator stays
- `app/(platform)/services/trading-platform/**` — operational allocator surface stays
- `app/(platform)/services/strategy-catalogue/**` — **keep as the canonical strategy universe / discovery surface.**
  Phases 1–8 ONLY mount the shared scope bar + make catalogue scope-aware (read scope, filter the list). Do NOT collapse
  the catalogue routes in Phase 9 unless a follow-up review explicitly proves the new workspace catalogue fully replaces
  them. Default assumption: catalogue stays as a distinct surface (universe view) alongside the cockpit.
- `app/(platform)/services/research/{ml,strategy/backtests,allocate}/**` — heavy specialist research surfaces (deep
  links from cockpit)
- `app/api/catalogue/envelope/route.ts` — GCS proxy unchanged
- `lib/architecture-v2/envelope-loader.ts::instancesByFamilyArchetypeAssetGroup` — keep, already produces the right
  hierarchy

### Phase 1 (foundation) — bridge → deprecate → delete, never big-bang

| Sub-phase | File                                                                                    | Change                                                                                                                                                      |
| --------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1A        | `lib/stores/workspace-scope-store.ts`                                                   | NEW — Zustand store, URL hydrate / serialise, localStorage fallback                                                                                         |
| 1A        | `lib/utils/nav-helpers.ts`                                                              | NEW `linkWithScope(href)`                                                                                                                                   |
| 1A        | `app/(platform)/layout.tsx`                                                             | WRAP in `<WorkspaceScopeProvider>`                                                                                                                          |
| 1A        | `lib/architecture-v2/catalogue-filter.ts`                                               | EXTEND with the full schema (five filter axes + `surface` + `terminalMode` + `researchStage` + `engagement` + `executionStream` + `workspaceId` + `asOfTs`) |
| 1A        | `lib/architecture-v2/family-filter.ts`                                                  | GENERALISE `matchesFamily` → `matchesScope(row, scope)`                                                                                                     |
| 1B        | `lib/stores/global-scope-store.ts`                                                      | BRIDGE — internally re-export from `useWorkspaceScope()`; mark `@deprecated` in JSDoc; **do not delete yet**                                                |
| 1B        | `lib/context/dashboard-filter-context.tsx`                                              | BRIDGE — same pattern; reads/writes flow through `useWorkspaceScope()`; mark deprecated                                                                     |
| 1C        | `components/platform/global-scope-filters.tsx`                                          | rebind directly to `useWorkspaceScope()`; drop `GlobalScopeStore` import                                                                                    |
| 1C        | `components/shell/asset-group-pill.tsx`                                                 | rebind directly                                                                                                                                             |
| 1C        | `app/(platform)/services/research/_components/family-archetype-asset-group-browser.tsx` | replace local React state with `useWorkspaceScope()`                                                                                                        |
| 1C        | every other consumer of the deprecated stores                                           | migrate one at a time, test, commit                                                                                                                         |
| 1D        | `lib/stores/global-scope-store.ts`                                                      | **DELETE** — only after step 1C confirms zero remaining imports (Playwright + grep + typecheck)                                                             |
| 1D        | `lib/context/dashboard-filter-context.tsx`                                              | **DELETE** — same gate                                                                                                                                      |

### Phase 2 (scope bar)

| File                                                                                               | Change                   |
| -------------------------------------------------------------------------------------------------- | ------------------------ |
| `components/shell/dart-scope-bar.tsx`                                                              | NEW (compact + expanded) |
| `app/(platform)/dashboard/page.tsx`                                                                | mount scope bar          |
| `app/(platform)/services/{trading,observe,research,signals,strategy-catalogue,reports}/layout.tsx` | mount scope bar          |

### Phase 3 (Terminal IA)

| File                                              | Change                                                 |
| ------------------------------------------------- | ------------------------------------------------------ |
| `components/cockpit/terminal-mode-tabs.tsx`       | NEW — Command / Markets / Strategies / Explain / Ops   |
| `components/cockpit/terminal-shell.tsx`           | NEW                                                    |
| `components/shell/service-tabs.tsx::TRADING_TABS` | route through new mode tabs (do not delete in Phase 3) |
| `lib/cockpit/terminal-modes.ts`                   | NEW — map current routes to modes                      |

### Phase 4 (Research IA)

| File                                                                            | Change                                                         |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `components/cockpit/research-journey-rail.tsx`                                  | NEW — Discover / Build / Train / Validate / Allocate / Promote |
| `components/cockpit/research-shell.tsx`                                         | NEW                                                            |
| `components/shell/service-tabs.tsx::{BUILD_TABS,STRATEGY_SUB_TABS,ML_SUB_TABS}` | regroup under journey stages (do not delete in Phase 4)        |
| `lib/cockpit/research-stages.ts`                                                | NEW                                                            |

### Phase 5 (scope-reactive widgets)

| File                                                                      | Change                                                                             |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `components/widgets/_data/scoped-data-provider.tsx`                       | NEW                                                                                |
| `components/widgets/_data/use-scoped-data.ts`                             | NEW                                                                                |
| `components/widgets/{options,sports,defi,predictions}/*-data-context.tsx` | KEEP as compatibility shims that delegate to `useScopedData()`                     |
| `components/widgets/_registry.ts`                                         | EXTEND with `DartWidgetMeta` (scopePredicate · modes · etc.)                       |
| every widget under `components/widgets/**`                                | EXTEND with metadata + migrate to `useScopedData()` (priority order in Section 11) |

### Phase 6 (starter presets + wizard step 0 IA explainer)

| File                                                 | Change                                                                                                                                                                                                                                                                                                     |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lib/cockpit/presets.ts`                             | NEW — eight preset definitions                                                                                                                                                                                                                                                                             |
| `lib/cockpit/derive-preset-from-persona.ts`          | NEW                                                                                                                                                                                                                                                                                                        |
| `lib/cockpit/ia-explainer-content.ts`                | NEW — ownership table + mode descriptions + stage descriptions (single source for wizard step 0 + /help/system-map)                                                                                                                                                                                        |
| `components/cockpit/system-map.tsx`                  | NEW — shared renderer for the IA explainer                                                                                                                                                                                                                                                                 |
| `app/(platform)/onboarding/cockpit/page.tsx`         | NEW — **four-step** wizard: Step 0 = IA map (system-map.tsx); Step 1 = preset; Step 2 = scope; Step 3 = surface + Terminal mode / Research stage + engagement + execution stream default (Stream defaults to Paper for replicate; Live is disabled for personas without live-trading entitlement per §4.3) |
| `lib/auth/firebase-provider.ts` + `demo-provider.ts` | first-login redirect to wizard                                                                                                                                                                                                                                                                             |
| `lib/questionnaire/seed-catalogue-filters.ts`        | WIRE INTO firebase-provider (currently zero callers)                                                                                                                                                                                                                                                       |
| `components/cockpit/cockpit-suggestions.tsx`         | NEW                                                                                                                                                                                                                                                                                                        |

### Phase 7 (FOMO + /help/system-map)

| File                                               | Change                                                                                                                                                                                                             |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `components/cockpit/contextual-locked-preview.tsx` | NEW                                                                                                                                                                                                                |
| `lib/cockpit/locked-previews.ts`                   | NEW — `LockedPreview` model + per-scope copy                                                                                                                                                                       |
| `components/platform/page-entitlement-gate.tsx`    | EXTEND to delegate locked-card UX to `<ContextualLockedPreview>` when `requiredInstrumentTypes` / `requiredAssetGroups` fail; "Learn more" links route to `/help/system-map`                                       |
| `app/(platform)/help/system-map/page.tsx`          | NEW — authenticated, platform-scoped IA explainer page; reuses `components/cockpit/system-map.tsx` from Phase 6. (NOT under `app/help/` — that would be public; the IA explainer is for signed-in demo prospects.) |
| `components/shell/help-menu.tsx` (or equivalent)   | ADD link to `/help/system-map`                                                                                                                                                                                     |
| `components/cockpit/dart-scope-bar.tsx`            | ADD `"?"` button next to scope chips → links to `/help/system-map`                                                                                                                                                 |

### Phase 8 (mock liveness)

| File                                                                         | Change                                                            |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `lib/api/mock-handler.ts`                                                    | EXTEND with `MockEventLoop`                                       |
| `lib/mocks/fixtures/mock-data-seed.ts`                                       | EXTEND with drift profiles                                        |
| `lib/mocks/lifecycle/{backtest-progression,alert-emitter,signal-emitter}.ts` | NEW                                                               |
| `components/widgets/_data/scoped-data-provider.tsx`                          | EXTEND — bind to MockEventLoop streams via `useSyncExternalStore` |

### Phase 9 (route collapse — LAST, conservative)

**Gate:** Phases 1–8 must have shipped and been validated end-to-end before Phase 9 starts. Strategy Catalogue is
**not** in scope for collapse by default — it stays as the canonical universe/discovery surface (a follow-up review can
revisit if the new cockpit catalogue widget fully replaces it).

| File                                                                              | Change                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/(platform)/services/trading/**/page.tsx` (the single-widget per-route pages) | DELETE / REDIRECT to `/services/workspace?surface=terminal&tm=command&…` (with scope preserved)                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `app/(platform)/services/observe/**/page.tsx`                                     | DELETE / REDIRECT per-page-meaning. Do NOT flatten everything to Explain. Mapping: `observe/risk` → `terminal&tm=explain`; `observe/alerts` → `terminal&tm=command`; `observe/strategy-health` → `terminal&tm=strategies`; `observe/system-health` → `terminal&tm=ops` (or `surface=ops` for admin personas); `observe/event-audit` → `terminal&tm=ops`; `observe/scenarios` → `terminal&tm=explain`; `observe/position-recon` → `terminal&tm=explain`; `observe/recovery` → `terminal&tm=ops`. Scope params preserved on redirect. |
| `app/(platform)/services/signals/dashboard/page.tsx`                              | KEEP if Signals-In is its own product surface; consider redirecting to `/services/workspace?surface=signals&…` only if the cockpit adequately covers signal intake. Decide per-Phase-9 review.                                                                                                                                                                                                                                                                                                                                      |
| `app/(platform)/services/strategy-catalogue/**`                                   | **DO NOT collapse.** Keep as canonical universe / discovery surface.                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `lib/config/services.ts::SERVICE_REGISTRY`                                        | collapse trading + observe entries; keep dart-terminal + dart-research tiles routing into the cockpit with `?surface=...&tm=...` (or `?surface=research&rs=...`)                                                                                                                                                                                                                                                                                                                                                                    |
| `components/shell/service-tabs.tsx::{TRADING_TABS,OBSERVE_TABS,…}`                | DELETE — superseded by terminalMode tabs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| every Playwright spec referencing old routes                                      | UPDATE to new URLs (`?surface=...&tm=...&...`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

---

## 24. Verification — end-to-end demo flow after all nine phases

1. Demo prospect signs in. Lands on `/dashboard`. Two tiles: **DART Terminal (left), DART Research (right)** — Terminal
   anchors the left-eye for the FOMO hit. Tile copy is buyer-language: _"Live cross-asset cockpit"_ / _"Build, train,
   validate, allocate strategies"_.
2. Click DART Terminal → first-run wizard pops (no saved workspace). **Four steps**: (0) System map / IA explainer
   (Discover-Build-Train-Validate-Allocate-Promote + Command-Markets-Strategies-Explain-Ops + ownership rules); (1)
   starter preset (auto-recommended from persona + `assigned_strategies` + questionnaire); (2) scope chips; (3) mode +
   engagement default ("watch your strategy run" or "walk through it piece by piece"). ~45 seconds.
3. Land in
   `/services/workspace?surface=terminal&tm=command&ag=DEFI&fam=CARRY_AND_YIELD&eng=monitor&stream=paper&ws=arbitrage-command`.
   Cockpit has 6 widgets pre-arranged. Scope bar visible at top with Surface · Mode · Engagement · Stream toggles. Mode
   tabs (Command · Markets · Strategies · Explain · Ops). All widgets reactive to scope.
4. Watch for 30 seconds: P&L ticks · funding curve refreshes · two new alerts · a backtest finishes and shows in the
   activity widget. Demo feels alive.
5. Click scope chip "DEFI" off, "SPORTS" on. Cockpit re-renders: DeFi widgets fade out, sports widgets fade in. Saved
   layout positions are preserved per scope-set; suggestions surface for the new scope. Mock data swaps to sports
   fixtures.
6. Click Mode → Explain. Same shell, no flicker. P&L attribution + execution quality + slippage widgets surface. Scope
   preserved.
7. Click cross-domain arbitrage locked card. Sees scope-specific upgrade copy ("validate spread strategies
   live-compatible before deployment, with execution-aware backtest checks…"). Not generic "upgrade".
8. Tier-override flip Desmond DART-Full → Signals-In. Cockpit re-renders: Research stages padlock; Signals-In Monitor
   preset surfaces in suggestions; widgets with research entitlement grey out with contextual upgrade overlays.
9. Refresh. Everything restores from URL. Open in incognito with the URL: scope hydrates from query params; default
   workspace loads for that persona.
10. Type an old URL like `/services/trading/positions`. Redirects to `/services/workspace?surface=terminal&tm=command`
    with scope intact (Phase 9 redirects).

That's the FOMO experience. The demo prospect thinks _"this would take us years to build ourselves"_ instead of _"I have
to navigate 50 pages and re-pick filters every time."_

---

## 25. Final implementation instruction (for the executing agent)

> Implement the DART UX refactor as a guided cross-asset trading cockpit.
>
> The objective is to make DART feel like a Bloomberg/Aladdin-style institutional operating system. A user should choose
> a scope — asset group, instrument type, strategy family, archetype, **share class**, venue/protocol, strategy,
> account/mandate, **surface, Terminal mode or Research stage, engagement, execution stream, and (advanced) availability
> state** — and the whole UI should reshape around that context.
>
> **Operating rule:** Scope decides relevance. `StrategyAvailabilityResolver` (§4.5) decides visibility. Preset
> strategy-backing (§8) decides honesty. Mock/data badges (§13 + Layer-2-proof minimums) decide trust. Before rendering
> any strategy-backed widget, preset, catalogue row, locked preview, or next action, run every candidate through the
> resolver. Scope matching is only the first pass; the resolver returns `{ visibility, reason, cta }` and the UI must
> respect all three.
>
> Start by making scope real. Create a single `WorkspaceScope` store and bridge → deprecate → delete the parallel filter
> systems (do not big-bang). Scope must hydrate from URL, persist to localStorage, and be preserved through navigation
> with `linkWithScope()`. Replace local-only family/archetype state with the shared scope store. Emit a
> `ScopeChangeEvent` on every mutation for analytics.
>
> Next, make scope visible through a shared Scope Bar across Dashboard, DART Terminal, DART Research, Strategy
> Catalogue, Reports, and Signals. The bar must expose Surface · Terminal Mode (or Research Stage) · Engagement ·
> Execution Stream alongside the five filter axes.
>
> Then simplify DART Terminal into five buyer-facing modes: Command · Markets · Strategies · Explain · Ops. Keep the
> surface name "DART Terminal".
>
> Simplify DART Research into six journey stages: Discover · Build · Train · Validate · Allocate · Promote. Keep the
> surface name "DART Research".
>
> Then make widgets scope-aware using widget metadata: surfaces, Terminal modes, Research stages, engagements, execution
> streams, asset groups, instrument types, families, archetypes, entitlements, and `scopePredicate`. Migrate
> incrementally via compatibility shims (`useOptionsData()` → `useScopedData({ instrumentTypes: ["option"] })`),
> starting with P&L · positions · orders/fills · alerts · risk · strategy health · spread/opportunity monitor ·
> funding/basis · DeFi exposure · backtest/activity widgets.
>
> Then create persona/questionnaire-seeded starter cockpits: Executive Overview · Live Trading Desk · Arbitrage Command
> · DeFi Yield & Risk · Volatility Research Lab · Sports / Prediction Desk · Signals-In Monitor · Research-to-Live
> Pipeline. New users should land in a populated recommended workspace via a four-step wizard (System map · Preset ·
> Scope · Mode + Engagement + Stream), not a blank widget grid. Live execution stream must never default for replicate;
> it requires the §4.3 confirm dialog and is disabled for personas without live-trading entitlement.
>
> Then add contextual locked previews using the `LockedPreview` model. Locked cards must reflect the active scope.
> Arbitrage users see arbitrage-specific locked capabilities. DeFi users see DeFi-specific. Signals-In users see
> signal-specific. Volatility users see vol-specific.
>
> Then add mock-mode liveness using a controlled `MockEventLoop` with P&L ticks, alerts, signal arrivals, backtest
> progression, activity updates, and `freeze=true` support for tests. In replicate engagement, also drive simulated
> paper fills, stepper progress, pre-trade risk checks, and manual-vs-algo comparison data — so replicate is not UI
> chrome.
>
> Keep full route collapse as the LAST phase (Phase 9). Do not delete or redirect large numbers of routes until scope,
> cockpit, presets, widgets, and mock liveness are stable. Strategy Catalogue stays as a distinct surface; do not
> collapse it into the cockpit by default.
>
> Success means: selecting Arbitrage on the dashboard follows the user into Terminal, Research, Catalogue, and Reports;
> the workspace automatically shows arbitrage-relevant widgets; toggling Replicate swaps to manual trade-builder widgets
> at the same scope; locked previews create scope-specific desire; mock data feels alive (including paper fills in
> replicate); and the user feels that Odum already built the operating system they would otherwise need to build
> themselves.

## 25.A Continuity audit & copy alignment (companion deliverable)

This section is a **companion deliverable** — not part of the implementation phases above. It captures the audit
findings from the parallel reviews of the public website, the investor-relations presentations, and the signed-in
product, plus concrete copy changes that should land alongside the cockpit refactor so the marketing promise, the IR
pitch, and the post-login experience all use the same vocabulary and tell the same story.

### 25.A.1 Canonical positioning copy (use verbatim across surfaces)

**The wedge sentence (use in IR decks + sales conversations only — names competitors):**

> _"Odum is building the cross-asset strategy operating layer Bloomberg, Aladdin, execution systems, and fund-admin
> stacks were never designed to be in one product."_

**The softened public-copy variant (preferred for the marketing site — keeps the wedge but doesn't name competitors
directly):**

> _"Odum is building the cross-asset strategy operating layer institutional teams usually have to assemble from separate
> data terminals, portfolio systems, execution tools, and fund-admin reporting stacks."_

**The shorter, sharper variant (preferred for hero copy):**

> _"One operating layer from strategy research to live execution, attribution, and client reporting — across digital
> assets, traditional markets, sports, and prediction markets."_

Use the named-competitor version privately (board decks, investor 1:1s, briefings shared under NDA). Use the softened
version on the public site, in initial-call leave-behinds, and anywhere a competitor's lawyer might read it.

**The continuity narrative (use as a strip / lifecycle row):**

> _Catalogue → Research → Backtest → Paper → Promote → Live → Monitor → Explain → Report_

**The wedge claim (one sentence):**

> _"We unify the strategy lifecycle and operating model across markets that usually live in separate systems."_

**The shared-scope claim (use when buyer asks "how does it stay coherent?"):**

> _"One scope — asset group · instrument type · strategy family · archetype · venue · mandate · surface · engagement ·
> execution stream — drives the whole system. Pick a context, the cockpit reshapes."_

### 25.A.2 IR presentation copy changes (file-by-file)

| File                                                                                         | Current copy gap                                                                                                                                                                | Recommended change                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/(platform)/investor-relations/board-presentation/components/board-presentation-data.ts` | Cover subtitle leads with "three engagement routes, five asset groups, one code path." Strong but doesn't anchor the "operating layer" framing or list the full pipeline.       | Re-lead the cover subtitle with the wedge sentence (the umbrella); push the routes/asset-groups/code-path facts to bullet 2. Add a Slide-1.5 that draws the Catalogue→…→Report continuity as a horizontal strip.                                                                                                                                                                                                                                                             |
| `app/(platform)/investor-relations/platform-presentation/data.ts`                            | "Same operating system…available to you" is good. Slide 9 ("Research-to-Live Gap") is the strongest slide. Missing the full lifecycle sequence + "one shared scope" vocabulary. | Add a slide titled "One shared scope across nine stages" with the continuity strip + the nine-axis scope list. Reword Slide 9's headline to _"On most platforms research and live are separate. On DART they are one stage in nine."_                                                                                                                                                                                                                                        |
| `app/(platform)/investor-relations/investment-presentation/data.ts`                          | Allocator-centric (returns/fees/track record). Misses the operating-layer narrative.                                                                                            | Add a Slide 1.5 _"What you actually get"_ showing the same nine-stage lifecycle with the allocator's view highlighted (Live · Monitor · Explain · Report). The point is _"the same system that runs the strategy is the system that reports it to you — no vendor stitching."_                                                                                                                                                                                               |
| `app/(platform)/investor-relations/plan-presentation/data.ts`                                | "One codebase compounds across three routes" is correct but not why-explained.                                                                                                  | Add one paragraph under Slide 2: _"One codebase is defensible because the scope is shared. A new strategy added to research immediately becomes catalogued, backtestable, paper-promotable, live-deployable, monitorable, attributable, and reportable — across all five asset groups — with zero re-platforming."_                                                                                                                                                          |
| `unified-trading-pm/codex/14-playbooks/shared-core/competitive-landscape.md`                 | Frames "unified layer vs fragmented stack" correctly. No Bloomberg/Aladdin trio as canonical reference architecture. No nine-axis scope as the moat.                            | Add a top-of-file paragraph: _"The reference architectures buyers compare us against (Bloomberg-style data terminal, Aladdin-style portfolio/risk OS, fund-admin reporting, execution OMS/EMS) were each designed to own one slice. Each is best-in-class on its lane. Odum's wedge is that none of them was designed to be the others — and the buyer pays a stitching tax to assemble them."_ Then list the nine-axis scope under "what makes the unification defensible". |
| `content/briefings/dart-trading-infrastructure.yaml`                                         | "Operating system, not a product line" is good. Missing full pipeline + scope.                                                                                                  | Replace the "Key Messages" first bullet with: _"DART is one operating layer covering Catalogue → Research → Backtest → Paper → Promote → Live → Monitor → Explain → Report — across CeFi, DeFi, TradFi, sports, and prediction markets — under one shared scope."_                                                                                                                                                                                                           |
| `content/briefings/investment-management.yaml`                                               | "Same surface, batch-and-live parity" is correct but allocator-centric.                                                                                                         | Add a key message: _"You see the operating layer Odum operates on, filtered to your share class. Not a stripped-down report-only view: the same continuity from research to reporting."_                                                                                                                                                                                                                                                                                     |
| `lib/copy/service-labels.ts`                                                                 | Three-route labels are correct but no umbrella term.                                                                                                                            | Add an umbrella label: `OPERATING_LAYER_LABEL = "Cross-asset strategy operating layer"`. Reference it from homepage hero + IR deck covers + briefings.                                                                                                                                                                                                                                                                                                                       |

### 25.A.3 Public website copy alignment (file-by-file)

| File                                                  | Current copy                                                                                                                                                                                    | Recommended change                                                                                                                                                                                                                                                                                                                                                      |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/(public)/page.tsx` (metadata)                    | _"Odum operates selected systematic strategies and DART Trading Infrastructure for institutional clients, with regulated operating models where appropriate."_                                  | _"Odum operates the cross-asset strategy operating layer institutional teams usually have to assemble from separate data terminals, portfolio systems, execution tools, and fund-admin reporting stacks. Available through three engagement routes."_ (softened public variant per §25.A.1; the named-competitor wording stays in IR decks + NDA-shared briefings only) |
| `app/(public)/_home-client.tsx::Hero`                 | _"Systematic strategies. Trading infrastructure. Institutional clients."_                                                                                                                       | Lead with the sharper positioning line: _"One operating layer. Research to live, across digital assets, traditional markets, sports, and prediction markets."_ Keep the three trust markers (FCA, professional clients, regulated since 2023) below.                                                                                                                    |
| `app/(public)/_home-client.tsx::MarketsUniverse`      | _"Selected markets. One operating surface."_                                                                                                                                                    | Strengthen: _"Five asset groups. One scope. One pipeline."_ Replace the arbitrage-galaxy caption with the nine-stage continuity strip rendered horizontally above the asset-group nodes.                                                                                                                                                                                |
| `app/(public)/_home-client.tsx::EngagementRoutes`     | Three cards (Allocator / Operator / Regulator) read as parallel products.                                                                                                                       | Reframe as three _entry points into the same operating layer_: each card subhead starts _"Same operating layer. Different access pattern…"_. The cards then explain who owns the strategy IP, who carries which regulatory role, and where reporting lands.                                                                                                             |
| `app/(public)/_home-client.tsx::WhyOdum`              | _"We operate one codebase across research, execution, reporting, and compliance, then offer narrow access to that system…"_                                                                     | Strong as-is — but add the next sentence: _"That codebase covers the nine-stage pipeline (Catalogue → Research → Backtest → Paper → Promote → Live → Monitor → Explain → Report) under one shared scope. No vendor stitching, no rebuilt research-to-live handoff, no separate reporting stack."_                                                                       |
| `app/(public)/services/platform/page.tsx` (DART page) | _"DART is the infrastructure layer behind Odum's systematic trading activity, available to selected clients who need a controlled path from research to execution, monitoring, and reporting."_ | Replace "controlled path from research to execution, monitoring, and reporting" with the full continuity: _"…a controlled path from Catalogue through Research, Backtest, Paper, Promote, Live, Monitor, Explain, and Report."_                                                                                                                                         |
| `app/(public)/our-story/page.tsx` (meta description)  | _"…a unified trading operating system…"_                                                                                                                                                        | Already aligned — promote this language to the hero copy on the page itself; don't bury it in meta.                                                                                                                                                                                                                                                                     |

### 25.A.4 Public ↔ signed-in continuity bridges (must-fix gaps)

The website promises continuity. The signed-in product currently delivers a tile grid. Phases 1-9 close most gaps; these
are the explicit bridges that need to land per phase:

| Bridge                            | Promised on public site                                           | Currently invisible signed-in                                   | Lands in phase                                                                                                                   |
| --------------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Your engagement route**         | Three routes (Allocator / Operator / Regulator) shown equally     | Dashboard never displays "you're on route X"                    | Phase 6 (preset wizard names the route) + Phase 2 (scope bar shows route in expanded view)                                       |
| **Your scope ribbon**             | "One operating surface" implies persistent context                | Dashboard filter strip is hidden by default                     | Phase 2 (`DartScopeBar` always visible, never collapsed)                                                                         |
| **Engagement progress**           | 7-step engagement journey on homepage                             | No progress tracker post-login                                  | Phase 4 (Research stages = Discover→Promote) + Phase 6 (preset shows current stage)                                              |
| **Lifecycle pipeline strip**      | Research → Execution → Monitoring → Reporting marketing strip     | No equivalent strip post-login                                  | Phase 3 + Phase 4 (mode tabs and stage rail are the post-login pipeline)                                                         |
| **Trust signals**                 | FCA badge + regulated-since-2023 in hero                          | Trust signals only in IR pages and footer                       | Phase 7 (locked previews) + a new always-on trust-pill on the cockpit header — _FCA-authorised · Risk: 62% · Last trade: 2m ago_ |
| **Market universe**               | Five asset-group strip on homepage                                | Dashboard never names the five groups together                  | Phase 2 (scope bar's asset-group chips are the always-on equivalent)                                                             |
| **"Research to live" continuity** | Implied by hero copy + DART page                                  | Research and Terminal are still in different layout trees today | Phase 4 + Phase 9 (collapse research-to-cockpit deep links)                                                                      |
| **Reporting safety**              | "Regulated since 2023" + "engagement scope reviewed case by case" | No reporting-safety indicator on Reports tile                   | Phase 7 (contextual locked previews include reporting locked-previews)                                                           |
| **Same vocabulary**               | "Operating surface", "operating system", "one codebase"           | Internal terms (Tier 3, lifecycle stage codes) leak to user     | Phase 6 wizard step 0 (IA explainer) + Phase 9 copy sweep retiring internal labels                                               |

### 25.A.5 Vocabulary alignment table (lock these in across surfaces)

| Concept                   | ✓ Use                                                          | ✗ Don't use                               |
| ------------------------- | -------------------------------------------------------------- | ----------------------------------------- |
| The product as a whole    | Cross-asset strategy operating layer · Operating layer         | Trading platform · Software · System      |
| The pipeline              | Lifecycle · Continuity · Nine-stage pipeline                   | Workflow · Process · Steps                |
| The shared filter context | Scope                                                          | Filter · Picker · Selection               |
| The user's access tier    | Engagement route (Allocator / Operator / Regulator)            | Tier 1 / Tier 2 / Tier 3                  |
| Live trading surface      | DART Terminal · Live Command (mode hero)                       | DART · Trading · The terminal             |
| Research surface          | DART Research · Strategy Research Workbench (mode hero)        | The research page · Build · Build & Train |
| Five asset groups         | CeFi · DeFi · TradFi · Sports · Prediction markets             | Categories · Asset classes · Markets      |
| Engagement type           | Monitor · Replicate (with Paper / Live execution stream)       | Watch · Build · Trade                     |
| Buyer outcome             | "This is the operating system we'd otherwise build ourselves." | "This is a powerful platform."            |

### 25.A.6 The 7 make-or-break pieces (success bar, repeated for emphasis)

Lifted from §0 — also the canonical demo-readiness checklist for every milestone:

1. Scope must actually work everywhere.
2. Presets must feel curated, not decorative.
3. Widgets must genuinely change with context.
4. Locked previews must create desire.
5. Mock/demo mode must feel alive.
6. Research-to-live must feel continuous.
7. Reporting and Explain must be strong enough to prove institutional seriousness.

### 25.A.7 PM codex + UI repo doc alignment (companion deliverable)

The new vocabulary (`surface` / `terminalMode` / `researchStage` / `engagement` / `executionStream` / `shareClasses` /
`StrategyAvailabilityResolver` / hide-lock-tease-reality / six buyer-facing terminal modes / six research stages / eight
presets / "operating layer" / "potential configuration space" / Vol-Lab=Deribit+CME) must propagate beyond the IR decks
and the marketing site into the codex + UI-repo SSOT docs so engineers, agents, and future plans use the same words.
Otherwise the next plan re-derives mappings that already exist.

**Codex propagation targets (PM repo) — file → required additions:**

| File                                                                                  | Required updates                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-trading-pm/codex/14-playbooks/dart/dart-terminal-vs-research.md`             | Already exists from the prior tile-split round. Append: §4.5 resolver + §4.6 four-state taxonomy + §8 preset archetype map + §13 Layer-2 minimum proof set + the operating-rule one-liner. Mark this doc as the **canonical SSOT** other docs link to.                                                                                                                                                                                                                     |
| `unified-trading-pm/codex/14-playbooks/audiences-and-journeys.md`                     | Add a section per persona showing the recommended starter preset + default surface + default engagement + `assigned_strategies` seeding behaviour. Replace any `mode: trade/observe/research` references with the new surface/terminalMode/researchStage triple.                                                                                                                                                                                                           |
| `unified-trading-pm/codex/14-playbooks/information-architecture.md`                   | Replace any "DART has the following pages" enumeration with the cockpit + surface/mode/stage model. The IA explainer rendered at `/help/system-map` and the wizard step 0 must source from this file.                                                                                                                                                                                                                                                                      |
| `unified-trading-pm/codex/14-playbooks/experience/`                                   | Cross-reference the cockpit modes / engagement dial / four-state taxonomy in every persona-experience doc. The "what does Desmond see when he signs in?" doc walks the new wizard + cockpit, not the old tile grid.                                                                                                                                                                                                                                                        |
| `unified-trading-pm/codex/14-playbooks/page-triage/`                                  | Update per-route purpose mapping with the Phase 9 redirect targets: per-page meaning maps from `services/observe/risk` → `terminal/explain` etc.                                                                                                                                                                                                                                                                                                                           |
| `unified-trading-pm/codex/14-playbooks/commercial-model/competitive-landscape.md`     | Add the wedge sentence (named-competitor variant, internal only) at the top + the operating-rule one-liner + the strategy-backing strength + the six-MVP-Layer-2-proof-signals so sales conversations match the demo.                                                                                                                                                                                                                                                      |
| `unified-trading-pm/codex/09-strategy/architecture-v2/README.md`                      | Add a section "How the cockpit consumes this taxonomy": describes `StrategyAvailabilityResolver`, the four-state visibility taxonomy, the per-preset archetype map, the v1 venue scopes (Vol Lab = Deribit + CME), and the Catalogue-vs-Cockpit FOMO split. This stops the strategy taxonomy from being a parallel universe to the cockpit UX.                                                                                                                             |
| `unified-trading-pm/codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md` | Add an explicit mapping: maturity phase → `StrategyVisibilityState` per persona (e.g. `paper_1d` for client persona = `hidden`; for admin = `visible`; etc.).                                                                                                                                                                                                                                                                                                              |
| `unified-trading-pm/codex/09-strategy/strategy-summary.md`                            | Update the catalogue-counts paragraph: "6,000+ is the **potential configuration space**; live + paper today is ~70-80 instances; v1 catalogue ceiling ~240-250." Forbid using 6,000+ as an "available strategies" claim.                                                                                                                                                                                                                                                   |
| `unified-trading-pm/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`    | Reconcile the Tier 1/2/3 model with the four-state visibility taxonomy. Tier 3 = "available_to_request", Tier 2 = "owned (mandate-allocated)", Tier 1 = "owned (subscribed)" or similar. Document the mapping.                                                                                                                                                                                                                                                             |
| `unified-trading-pm/codex/09-strategy/architecture-v2/restriction-policy.md`          | Update with the persona-rule matrix from §4.5 (admin sees all, IM-desk sees client-exclusive read-only, etc.) so restriction profiles stay aligned with the resolver output.                                                                                                                                                                                                                                                                                               |
| `unified-trading-pm/codex/09-strategy/architecture-v2/families/*.md`                  | For each family doc, add a "Cockpit binding" section: which preset(s) this family seeds, which terminal modes / research stages surface it, which engagement modes are valid (e.g. monitor + replicate for arbitrage; monitor-only for executive-overview).                                                                                                                                                                                                                |
| `unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/*.md`                | Same — add a "Cockpit binding" section listing the preset memberships from `PRESET_ARCHETYPE_MAP`.                                                                                                                                                                                                                                                                                                                                                                         |
| `unified-trading-pm/codex/08-workflows/platform-walkthrough-and-demo-context.md`      | Rewrite around the four-step wizard + cockpit flow + scope-bar tour. Old single-mode tile-grid walkthrough is retired.                                                                                                                                                                                                                                                                                                                                                     |
| `unified-trading-pm/codex/08-workflows/prospect-questionnaire-flow.md`                | Update the "what happens after submit" section to describe the wizard handoff + `seedFiltersFromQuestionnaire` reuse.                                                                                                                                                                                                                                                                                                                                                      |
| `unified-trading-pm/codex/08-workflows/signup-signin-workflow.md`                     | Add the first-login wizard redirect step + the §4.3 live-execution-stream safety dialog.                                                                                                                                                                                                                                                                                                                                                                                   |
| `unified-trading-pm/codex/08-workflows/environment-mode-philosophy.md`                | Add the §13 mock-mode liveness contract: `freeze=true` honoured across both engagement modes; pace control.                                                                                                                                                                                                                                                                                                                                                                |
| `unified-trading-pm/codex/04-architecture/README.md`                                  | Add a top-level pointer to the cockpit / scope-store / resolver primitives so architecture readers know where the new product layer lives.                                                                                                                                                                                                                                                                                                                                 |
| `unified-trading-pm/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`              | Add an entry for `WorkspaceScopeStore` + `StrategyAvailabilityResolver` as new platform-level primitives.                                                                                                                                                                                                                                                                                                                                                                  |
| `unified-trading-pm/codex/02-data/` (all docs)                                        | Vocabulary sweep: ensure asset_group / instrument_type / family / archetype / share_class are used consistently with §4 + §4.4 of this plan. Spot any drift (e.g. "category" instead of "asset_group" — flagged as an existing exception per CLAUDE.md but should not leak into new copy).                                                                                                                                                                                 |
| `unified-trading-pm/codex/02-venues/venue-registry-reference.md`                      | Add the Vol Lab v1 venue constraint (Deribit + CME only) as an explicit note alongside the venue list, so future preset/widget work doesn't silently broaden options coverage.                                                                                                                                                                                                                                                                                             |
| `unified-trading-pm/codex/GLOSSARY.md` + `00-SSOT-INDEX.md`                           | Add new glossary entries: surface · terminalMode · researchStage · engagement · executionStream · share_class · StrategyAvailabilityResolver · StrategyVisibilityState · StrategyVisibilityReason · StrategyVisibilityCta · operating layer · monitor engagement · replicate engagement · cockpit FOMO · catalogue FOMO · scope event · scope-aware next action. Each links to the relevant §X.Y of the canonical SSOT (`14-playbooks/dart/dart-terminal-vs-research.md`). |

**UI-repo doc propagation targets:**

| File                                                                             | Required updates                                                                                                                                                                                                                                                                                       |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `unified-trading-system-ui/context/AGENT_UI_STRUCTURE.md`                        | Replace any "Five top-level service tiles: DART · Odum Signals · Reports · IR · Admin" enumeration with the new six-tile shape (DART Terminal · DART Research · Odum Signals · Reports · IR · Admin). Walk through cockpit + surface model rather than tile-flat structure.                            |
| `unified-trading-system-ui/context/CONTEXT_GUIDE.md`                             | Add a section "Cockpit primitives" pointing at `lib/stores/workspace-scope-store.ts`, `lib/architecture-v2/strategy-availability-resolver.ts`, `lib/cockpit/presets.ts`, `lib/cockpit/preset-archetype-map.ts`, `components/cockpit/*`. Future agents should find the cockpit machinery in one breath. |
| `unified-trading-system-ui/context/CONFIG_REFERENCE.md`                          | Add `WorkspaceScope` URL contract from §7 + the advanced URL keys (sc/cov/mat/route/avail). Document the §4.3 live-execution safety contract here so config docs match runtime behaviour.                                                                                                              |
| `unified-trading-system-ui/context/SHARDING_DIMENSIONS.md`                       | Reconcile the sharding-dimensions doc with `WorkspaceScope` — same names where possible; note any intentional divergence (e.g. wire-format `category=cefi` stays lowercase per CLAUDE.md).                                                                                                             |
| `unified-trading-system-ui/docs/TIER_ZERO.md`                                    | Add a section on what the demo prospect should experience post-cockpit-refactor: wizard step 0 → preset → scope → mode + engagement → land in cockpit → mock liveness ticks. Tier-0 docs should describe the new demo flow, not the old tile-grid walkthrough.                                         |
| `unified-trading-system-ui/docs/FRONTEND_PRIMER_FOR_BACKEND_ENGINEERS.md`        | Add the cockpit primitives + scope event contract + resolver contract so backend-side engineers know what URL params + analytics events to expect.                                                                                                                                                     |
| `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json`                           | Regenerate after Phases 1-9 land — the route tree changes substantially (Phase 9 redirects), the manifest must match.                                                                                                                                                                                  |
| `unified-trading-system-ui/.cursorrules` (if it exists) + repo-level `CLAUDE.md` | Add: _"DART surface names are 'DART Terminal' and 'DART Research'. Internal labels (terminalMode, researchStage) are NOT the surface names. Live execution stream defaults to paper for replicate engagement (§4.3 safety contract)."_                                                                 |

**Propagation order (matches the phase plan):**

1. Update the canonical SSOT (`14-playbooks/dart/dart-terminal-vs-research.md`) FIRST. Other docs link to it.
2. Update `09-strategy/architecture-v2/` next — strategy taxonomy must reconcile with the resolver before any code
   consumes the resolver.
3. Update `08-workflows/*` and `14-playbooks/*` after the cockpit ships in code (Phases 3-6) so the docs describe what's
   actually in the product.
4. Update UI-repo `context/*` and `docs/*` ALONGSIDE the code changes (per phase) — these are agent-facing guides; they
   go stale fast if doc-only updates trail the code.
5. Sweep `02-data/` and `GLOSSARY.md` last — vocabulary alignment is mechanical; do it once after the conceptual docs
   are stable.

**Doc-alignment success criteria:**

- A future agent (or human) reading `00-SSOT-INDEX.md` finds the new cockpit primitives in one click.
- The wedge sentence (in two variants — named-competitor for IR, softened for public) appears verbatim in both
  `competitive-landscape.md` and `app/(public)/page.tsx` metadata.
- The four-state visibility taxonomy is described identically in `dart-terminal-vs-research.md`,
  `strategy-catalogue-3tier.md`, and `restriction-policy.md`.
- A grep for `"6,000+ strategies"` returns zero hits across both repos (only "potential configuration space" /
  "combinatoric universe" surfaces).
- A grep for `mode: "trade"` / `mode: "observe"` returns zero non-historical hits (legacy phrasing only in plan-archive
  notes).

### 25.A.8 Three-layer trust model (recap from §0)

The cockpit refactor (Phases 1-9) covers **Layer 1 — Experience**. Two follow-on programmes are non-negotiable for the
institutional buyer:

- **Layer 2 — Proof**: live strategies with real venue integrations; audit trails surfaced; reconciliations visible;
  data freshness pills; incident handling with public post-mortems; demo scenarios that match real buyer use cases
  (perp-funding arb, DeFi yield rotation, vol surface trading, sports event-driven, signals-in onboarding).
- **Layer 3 — Distribution trust**: regulatory posture surfaced in product (not just IR); client-data handling
  documented; live-execution controls visible; permissioning serious; reporting safe; operational risk managed.

Both layers attach to the cockpit (every signed-in surface gets a discreet trust-and-status pill in the header) but are
owned by separate workstreams (Layer 2 = ops + integrations; Layer 3 = regulatory + governance). They are out of scope
for this plan but referenced here so the implementation agent doesn't forget the cockpit alone is not the product.

---

## 26. Agent guardrails (read before writing any code)

These are the most likely failure modes for an executing agent. Treat each as non-negotiable.

- **Do not rename DART Terminal or DART Research.** Those are the product surface names. "Live Command", "Strategy
  Research Workbench", etc. are mode-level / hero labels INSIDE those surfaces.
- **Do not collapse routes before Phase 9.** Phases 1–8 must ship and stabilise first. Old routes remain reachable as
  deep links throughout 1–8.
- **Do not default replicate engagement to live execution stream.** Always default to paper. Live requires the §4.3
  confirm dialog and is disabled for personas without live-trading entitlement.
- **Do not delete `lib/stores/global-scope-store.ts` or `lib/context/dashboard-filter-context.tsx` until Phase 1D.**
  Bridge them as `@deprecated` wrappers in 1B; migrate consumers in 1C; only then delete in 1D after grep + typecheck
  prove zero remaining imports.
- **Do not migrate widgets in a big bang.** Use the priority order in §11. One widget, one commit, one test.
  Compatibility shims keep `useOptionsData()` etc. working until a widget is ready.
- **Do not turn Strategy Catalogue into a cockpit widget in v1.** Catalogue is the universe / discovery surface; it
  stays distinct. Phases 1–8 only make it scope-aware.
- **Do not put the IA explainer under Admin.** It's at `/help/system-map` (authenticated, platform-scoped) AND wizard
  step 0. Admin stays ops-only.
- **Do not flatten all Observe pages to Terminal Explain.** Phase 9 redirects map per-page-meaning: risk/recon →
  explain; alerts/strategy-health → command/strategies; system-health/recovery/event-audit → ops.
- **Do not break `surface=ops` vs `surface=terminal&tm=ops`.** They are different surfaces. The former is Admin/Ops; the
  latter is Terminal's operational view.
- **Do not skip the `ScopeChangeEvent` emission.** Every scope mutation flows through
  `trackEvent("workspace.scope.change", event)`. Future analytics depend on it.
- **Do not bypass the `StrategyAvailabilityResolver`.** Widgets, presets, locked-previews, suggestions, and catalogue
  tabs all read through `resolveStrategyVisibility()` / `resolveVisibleStrategyInstances()`. Never decide visibility
  from raw scope-match. Pre-maturity / wrong-routing / retired / admin-only instances must be `"hidden"` for client-tier
  personas — not greyed-out, not behind a teaser overlay, _not in the DOM at all_.
- **Do not conflate Catalogue FOMO and Cockpit FOMO.** Catalogue FOMO is allocation FOMO (instance-level, stricter).
  Cockpit FOMO is workflow FOMO (capability-level, more permissive). They share the `LockedPreview` model but apply
  different filter logic on top.
- **Do not advertise "6,000+ strategies".** Copy must say "potential configuration space" or "combinatoric universe",
  never imply 6,000+ are live or selectable.
- **Do not make the Volatility Research Lab preset claim more options coverage than Deribit + CME.** v1 venue scope is
  locked. TradFi options are partial; DeFi options are blocked.
- **Do not invent a parallel questionnaire-to-scope mapping.** The wizard reuses `seedFiltersFromQuestionnaire`; if the
  questionnaire mapping needs to evolve, evolve it in `lib/questionnaire/seed-catalogue-filters.ts` and the wizard
  inherits the change for free.
- **Do not let presets render fully-populated cockpits when the resolver returns zero owned + zero available_to_request
  instances.** Show the preset's `emptyStateCopy` + a primary CTA matching the strategy-backing strength. Mock data
  never renders without a "demo data" badge for client-tier personas.
