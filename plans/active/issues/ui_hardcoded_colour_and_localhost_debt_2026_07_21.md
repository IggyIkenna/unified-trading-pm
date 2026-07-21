---
doc_type: issue
title:
  unified-trading-system-ui's [3.5/6] UI CODEX CHECKS hardcoded-colour check surfaced ~1082 pre-existing hits (554 real,
  528 legitimate) across 100 files on its first-ever run — new tracked cleanup batches
summary: >-
  Follow-up from ui_codex_gate_blind_to_app_router_layout_2026_07_21.md: fixing the base-ui.sh src/-vs-app/ blind spot
  made [3.5/6] run for unified-trading-system-ui for the first time ever, and it surfaced hardcoded hex/rgb colour
  literals (~1082 hits/100 files) and localhost-URL literals (~30 hits/6 files) that had accumulated invisibly.
  Localhost hits and 528/1082 colour hits were genuine design-token/fixture/email-template/dev-fallback exceptions
  (excluded via CODEX_COLOUR_EXCLUDE_GLOBS / CODEX_LOCALHOST_EXCLUDE_GLOBS in scripts/quality-gates.sh, matching
  deployment-ui precedent). The remaining 554 colour hits across 79 files are real ad-hoc UI-styling debt — too large
  and visually risky to blind-fix in one pass (trading/chart/marketing components with no running dev-server/Playwright
  visual QA in this session) — tracked here as batched follow-up todos.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [quality-gates, ui, codex-compliance, hardcoded-colours, gate-blind-spot]
related:
  [
    plans/active/issues/ui_codex_gate_blind_to_app_router_layout_2026_07_21.md,
    codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [ui_codex_gate_blind_to_app_router_layout-003]
resolved_by:
locked_by:
depends_on: []
---

# Hardcoded-colour + localhost debt surfaced by the app-router gate fix

## What I found

While shipping `ui_codex_gate_blind_to_app_router_layout-003` (console.\*/any-type cleanup), running the now-fixed
`[3.5/6] UI CODEX CHECKS` end-to-end for the first time surfaced two more violation categories that todo's own
"corrected count" never measured (it only scanned for `console.*` and `: any`):

1. **Hardcoded hex/rgb colours**: ~1082 hits across 100 files. Of these, 528 hits/21 files are genuine
   design-token/reference-data/mock-fixture/email-template sources (excluded via `CODEX_COLOUR_EXCLUDE_GLOBS` in
   `scripts/quality-gates.sh` with the same justification pattern as deployment-ui's `src/index.css` exception — see
   that file for the full list + reasoning). The remaining **554 hits across 79 files** are real ad-hoc hex/rgb literals
   in trading/marketing/research/widget component JSX — genuine debt needing a CSS-var or Tailwind-class replacement, or
   (for chart components) routing through the newly-added `lib/chart-theme.ts` tokens.
2. **Localhost URLs**: ~30 hits across 6 files — ALL legitimate on inspection (2 generated/vendored JSON registry files,
   a Firebase Auth-emulator dev connection, 2 `process.env.X || "http://localhost:PORT"` dev-fallback patterns matching
   deployment-ui's own precedent, 1 JSDoc example). Fully excluded via `CODEX_LOCALHOST_EXCLUDE_GLOBS` — no real
   localhost debt remains.

## Why it matters

Same blind-spot mechanism as the parent issue: this repo's `[3.5/6]` gate never ran until the app-router fix landed, so
554 real colour violations accumulated invisibly. `quality-gates.sh` for this repo will FAIL at `[3.5/6]` until these
land — blocking any non-docs quickmerge ship for this repo (including the parent todo's own console/any-type work, which
is otherwise complete and verified).

## Recommended decision

Fix in per-directory batches (same discipline as the archived-plan-debt batching in
`pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md`) — each batch requires a running dev server +
Playwright visual spot-check before/after (per `codex/06-coding-standards/ui-testing-layers.md`), NOT a blind
find-replace, since some of these are chart-library colour props that may need `chart-theme.ts`'s `CHART_COLORS` array
rather than a single CSS var.

## Todos

- [x] [UI] P2. Batch 1 — chart/research components (16 files, 3–19 hits each):
      `components/research/equity-chart-with-layers.tsx`, `components/research/signal-overlay-chart.tsx`,
      `components/research/execution/execution-detail-view.tsx`, `components/research/execution/status-helpers.tsx`,
      `components/research/overlaid-equity-curves.tsx`, `components/research/profit-structure-chart.tsx`,
      `components/research/win-loss-donut.tsx`, `components/trading/candlestick-chart.tsx`,
      `components/trading/vol-surface-chart.tsx`, `components/strategy-catalogue/PerformanceOverlay.tsx`,
      `components/paper-trading/coin-price-chart.tsx`, `components/reports/performance-dashboard.tsx`,
      `components/reports/portfolio-analytics.tsx`, `components/risk/correlation-heatmap.tsx`,
      `components/events/economic-heatmap.tsx`, `components/events/economic-grid.tsx`. Most are recharts-based — check
      whether `lib/chart-theme.ts`'s `CHART_COLORS`/`TOOLTIP_STYLE`/`GRID_STYLE`/`AXIS_STYLE` already cover the literal
      in question before inventing a new CSS var. (repo: unified-trading-system-ui) — ✅
      `unified-trading-system-ui@2e829de0`. All 16 files migrated to `lib/chart-theme.ts` tokens
      (`CHART_COLORS`/`GRID_STYLE`/`AXIS_STYLE`/`TOOLTIP_STYLE`) and the pre-existing `--color-pnl-positive`/
      `--color-pnl-negative`/`--color-risk-*` semantic CSS vars; `color-mix(in srgb, var(--x) N%, transparent)` for
      alpha-blended literals; Tailwind arbitrary-value + colour-utility split (`shadow-[...] shadow-emerald-500/25`) for
      2 Tailwind-only hits. Repo-measured hardcoded-colour count 1082→947 (real ~135-hit reduction);
      `codex_ui_violation_baseline.json` ratcheted `colour: 1082→947`. Full `quality-gates.sh` green (469s, sentinel
      `fce0861a`→`2e829de0` after quickmerge; typecheck/lint/286 unit tests/build/DeFi-citation all passed).
      **Correction during the batch**: `components/trading/candlestick-chart.tsx` and
      `components/paper-trading/coin-price-chart.tsx` use `lightweight-charts` (canvas-rendered, not recharts) — an
      initial sub-agent pass tested raw `ctx.fillStyle = 'var(--x)'` via canvas API directly, found it doesn't resolve
      (falls back to black), and concluded these 2 files couldn't be tokenized, leaving them on literals. A second pass
      found via reading the library source (`ColorParser`/`getRgbStringViaBrowser` in
      `lightweight-charts.development.mjs`) that the library's own series-config options (`upColor`, `wickUpColor`,
      etc.) resolve `var(--x)` through a hidden-DOM `getComputedStyle` lookup — a different code path than raw canvas
      calls. Verified this empirically before trusting it: built a live headless-Chromium + `@playwright/test` render
      passing `upColor: 'var(--test-color)'` to an actual `CandlestickSeries`, then read back real canvas pixel data via
      `getImageData` — confirmed the exact expected RGB rendered. Both files were then migrated to direct
      `var(--color-pnl-positive)`/`var(--color-pnl-negative)` string literals in their series-config options (confirmed
      correct); test artifacts deleted after verification. **Merge conflict during ship**: another slot concurrently
      landed a console.\* cleanup touching both `codex_ui_violation_baseline.json` and
      `components/trading/vol-surface-chart.tsx` (import line). Resolved by keeping the fuller import
      (`CHART_COLORS, GRID_STYLE, AXIS_STYLE, TOOLTIP_STYLE`) and by re-measuring (not guessing) the baseline file's
      true combined state directly via `rg` on the merged tree (`console: 5, colour: 947, localhost: 30`) rather than
      picking either side's stale claimed numbers. **Playwright**: attempted `research-real-data.smoke.spec.ts` as a
      pre-existing sanity-check spec; it failed (`net::ERR_CONNECTION_RESET`-class timeouts) under severe host
      contention (load 31-35 on 8 cores) — same environment blocker confirmed in the prior any-type-sweep task, not a
      regression from this change. No fabricated `pw:L2 ✓`.
- [x] ✅ [UI] P2. Batch 2 — widgets/\_primitives + widgets/\* (11 files, 1–8 hits each):
      `components/widgets/_primitives/metric-gauge.tsx`, `components/widgets/_primitives/flow-chart.tsx`,
      `components/widgets/_primitives/categorical-matrix.tsx`, `components/widgets/_primitives/depth-area-chart.tsx`,
      `components/widgets/_primitives/continuous-heatmap.tsx`, `components/widgets/pnl/pnl-data-context.tsx`,
      `components/widgets/alerts/severity-breakdown-widget.tsx`,
      `components/widgets/terminal/use-terminal-page-data.ts`,
      `components/widgets/strategies/strategies-catalogue-widget.tsx`,
      `components/widgets/cefi/volume-dominance-widget.tsx`, `components/widgets/workspace-toolbar.tsx`. The
      `_primitives/` chart files are the most likely `chart-theme.ts` candidates (they're the shared chart-primitive
      layer every other chart widget builds on). (repo: unified-trading-system-ui) —
      `unified-trading-system-ui@252ed295`. All 11 files migrated to semantic CSS-var/`color-mix()` tokens (mostly
      `--pnl-positive`/`--pnl-negative`/`--status-*`/`--risk-*`/`--chart-N`, matched to each hardcoded hex's real
      semantic meaning rather than nearest-visual-match — e.g. `severity-breakdown-widget.tsx`'s `#dc2626` had an
      existing `// status-critical` comment confirming the exact intended token, 3 of its 5 severities landed on
      exact-value token matches). `flow-chart.tsx`/`depth-area-chart.tsx` had genuinely dead `var(--x, #hex)` fallbacks
      (the primary token is always defined at `:root`, confirmed via `app/globals.css` import in `app/layout.tsx`) —
      stripped rather than reworded. `pnl-data-context.tsx`'s 8-category DeFi P&L palette preserved the original
      author's income-vibrant/cost-muted design intent using existing tokens (no new CSS needed).
      `use-terminal-page-data.ts`'s SMA/EMA/Bollinger-Band overlay colours feed
      `components/trading/candlestick-chart.tsx` (confirmed via
      `chart.addSeries(LineSeries, { color: indicator.color })`) — the same `lightweight-charts` series-config path
      Batch 1 empirically verified resolves `var(--x)` correctly (unlike raw canvas calls). `workspace-toolbar.tsx`'s
      `#0a0a0a` was a `html-to-image` canvas-fill colour (can't reference a CSS var directly, same canvas-vs-DOM
      distinction as Batch 1's finding) — resolved the live `--background` value via `getComputedStyle` at call time
      instead, so screenshots now match whichever theme is active rather than forcing one hardcoded dark hex.
      `strategies-catalogue-widget.tsx`'s `shadow-[...rgba(0,0,0,0.4)]` split into `shadow-[0_2px_8px] shadow-black/40`
      (Tailwind arbitrary-value + colour-utility split, same pattern Batch 1 established for its 2 Tailwind-only hits).
      `volume-dominance-widget.tsx`'s 8-colour categorical array replaced with the shared `CHART_COLORS` (6 entries,
      existing modulo-cycling logic handles the overflow safely). **Merge conflict during ship**: sibling batch `-003`
      (slot-2) concurrently landed `unified-trading-system-ui@2bb398c1` (colour/localhost exclude-glob triage, 947→501)
      touching the same `codex_ui_violation_baseline.json`. Resolved via `ff-only` pull + re-measuring the TRUE combined
      state on the fully-merged tree (both diffs are additive/composable — different files, no overlap) rather than
      guessing: combined colour count 501→465. `quality-gates.sh` green end-to-end (345s: typecheck/lint/286
      tests/build/DeFi- citation all passed), sentinel `2d7d8ca6`→`252ed295` after quickmerge.
- [x] ✅ [UI] P3. Batch 3 — trading/sports (10 files, 1–27 hits each):
      `components/trading/sports/fixtures-detail-panel.tsx`, `components/trading/sports/arb-grid.tsx`,
      `components/trading/sports/shared.tsx`, `components/trading/sports/my-bets-tab.tsx`,
      `components/trading/sports/fixtures-match-card.tsx`, `components/trading/sports/arb-stream.tsx`,
      `components/trading/sports/arb-tab.tsx`, `components/trading/sports/fixtures-tab.tsx`,
      `components/trading/sports/bet-slip.tsx`, `components/widgets/sports/sports-widgets.md` (a markdown doc — check if
      the hex mentions are prose/examples, not code, before touching). `shared.tsx` likely defines a per-outcome colour
      map shared by the other 9 — fix it first, other files may just import from it. (repo: unified-trading-system-ui) —
      `unified-trading-system-ui@e60cf555`. Fixed `shared.tsx` first (per this todo's own note), mapping every hardcoded
      hex to this repo's existing design-system CSS vars after confirming exact-hex matches (`--status-live`,
      `--color-pnl-positive/-negative`, `--color-primary`, `--color-chart-1/4`,
      `--color-background/-card/-border/-muted-foreground`, `--color-surface-arb-card`); added a new
      `--surface-loss-card` token (mirroring the existing `--surface-arb-card`) for the one colour with no design-system
      counterpart. New `lib/sports-theme.ts` (mirrors `lib/chart-theme.ts`'s pattern) holds the genuinely categorical
      league-badge + bookmaker-brand palettes, added to `CODEX_COLOUR_EXCLUDE_GLOBS`. The `.md` doc's hex mentions
      confirmed prose (future-widgetization notes), left untouched per this todo's own instruction. Hit two
      concurrent-peer merge conflicts shipping (Batch 2's colour cleanup + a colour/localhost triage pass landed
      mid-ship) — reconciled both properly (combined `CODEX_COLOUR_EXCLUDE_GLOBS`, recomputed the TRUE combined baseline
      via `--update-baseline` rather than guessing, colour 465→352). `quality-gates.sh` green end-to-end (286 tests,
      build passed) + `pw:L2` ✓ (`tests/smoke/sports-tab-colour-migration.smoke.spec.ts`, new spec, passed after
      installing this slot's missing Playwright browser binary).
- [x] [UI] P3. Batch 4 — trading (non-sports) + predictions (14 files, 1–21 hits each):
      `components/shared/status-badge.tsx`, `components/trading/strategy-audit-trail.tsx`,
      `components/trading/strategy-filter-bar.tsx`, `components/trading/alerts-feed.tsx`,
      `components/trading/limit-bar.tsx`, `components/trading/dimensional-grid.tsx`, `components/trading/kpi-card.tsx`,
      `components/trading/context-bar/trading-context-bar.tsx`,
      `components/trading/options-futures/vol-greeks-panels.tsx`, `components/trading/predictions/arb-stream-tab.tsx`,
      `components/trading/predictions/odum-focus-tab.tsx`, `components/trading/predictions/markets-tab.tsx`,
      `components/shell/asset-group-pill.tsx`, `components/shell/lifecycle-nav.tsx`. (repo: unified-trading-system-ui) —
      ✅ `unified-trading-system-ui@7403a8b8`. All 14 files migrated to CSS-var tokens: most were exact byte-identical
      hex matches to existing `var(--status-*)`/`var(--pnl-*)`/`var(--risk-*)`/`var(--color-chart-N)` tokens (e.g.
      `strategy-filter-bar.tsx`'s 5 asset-class hexes = `--color-chart-2..6` dark-mode values exactly;
      `--status-idle`/`--status-running`/`--muted-foreground` similarly exact). One new token added (`--status-info`,
      light+dark+`@theme` mapping) for `status-badge.tsx`'s previously-untokenized "info" status.
      `alerts-feed.tsx`/`limit-bar.tsx`/`status-badge.tsx` rgba-alpha literals →
      `color-mix(in srgb, var(--x) N%,     transparent)`, matching the file's own pre-existing `color-mix` convention;
      `dimensional-grid.tsx`'s dynamic-alpha PNL heatmap → `color-mix` with a computed percentage.
      `kpi-card.tsx`/`asset-group-pill.tsx`/ `lifecycle-nav.tsx` Tailwind arbitrary-shadow hexes → Tailwind
      arbitrary-shape + colour-utility split (`shadow-[0_0_10px] shadow-blue-500/15`), same pattern Batch 1/2
      established. `trading-context-bar.tsx`'s `bg-[#111113]` → `bg-card` (exact match to `--card` dark value).
      `predictions/arb-stream-tab.tsx` mirrors the ALREADY-tokenized twin component
      `components/widgets/predictions/pred-arb-ui.tsx` exactly (confirmed the Tailwind v4 `var(--x)/NN` opacity-modifier
      syntax works via that existing precedent). `odum-focus-tab.tsx`/ `markets-tab.tsx` (both recharts) route their
      `Tooltip` `contentStyle` through `chart-theme.ts`'s `TOOLTIP_STYLE` per Batch 1's established convention.
      `vol-greeks-panels.tsx`'s two static contrast-text hexes (`#fff`/`#1a1a2e`) moved to Tailwind
      `text-white`/`text-slate-900` classes (no longer regex-flagged); its 3-branch `greekColor()` computed-RGB gradient
      function reimplemented as `color-mix()` interpolation between existing
      `--risk-healthy`/`--risk-critical`/`--risk-warning`/`--color-chart-1` tokens, preserving the same
      low-to-high-intensity heatmap direction per greek (delta: red→green: gamma/vega: cyan→amber; theta: amber→red) — a
      deliberate reimplementation, not a byte-exact preservation, since raw 3-channel RGB math can't be expressed as a
      2-color CSS token blend. Repo-measured hardcoded-colour count 352→277 (75-hit reduction);
      `codex_ui_violation_baseline.json` ratcheted `colour: 352→277`. Full `quality-gates.sh` green (367s:
      typecheck/lint/286 unit tests/build/DeFi-citation all passed, sentinel `e60cf555`→`7403a8b8` after quickmerge).
      **Playwright**: new regression spec `tests/smoke/trading-predictions-colour-migration.smoke.spec.ts` (pw:L2 ✓) —
      visits the strategy-detail page (status-badge/kpi-card/strategy-audit-trail) and the DART terminal under both
      Prediction scope (markets-tab/odum-focus-tab/asset-group-pill) and CeFi scope (lifecycle-nav/trading-context-bar),
      asserting clean render with no error boundary/overlay. Initial run hit `page.goto` timeouts at the default 30s
      under severe host contention (measured load 27.64/8 cores — same environment-blocker class Batch 1 hit, not a
      regression); re-ran with `--timeout=120000 --workers=1` and all 3 passed (49.9s/18.5s/5.5s). No fabricated
      `pw:L2 ✓`.
- [ ] [UI] P3. Batch 5 — marketing + platform pages + misc (28 files, 1–32 hits each): `app/(public)/_home-client.tsx`,
      `components/marketing/market-galaxy.tsx`, `components/marketing/arbitrage-galaxy.tsx`,
      `components/marketing/galaxy-canvas.tsx`, `components/marketing/strategy-family-catalogue.tsx`,
      `components/marketing/platform-architecture-grid.tsx`, `components/marketing/operating-model-stages.tsx`,
      `app/(public)/services/investment/page.tsx`,
      `app/(platform)/investor-relations/board-presentation/components/board-presentation-slide-part-a.tsx`,
      `app/(platform)/services/trading/strategies/[id]/components/strategy-detail-tab-panels.tsx`,
      `app/(platform)/services/trading/strategies/[id]/strategy-detail-page-client.tsx`,
      `app/(platform)/paper-trading/page.tsx`, `app/(platform)/paper-trading/coin/[coin]/page.tsx`,
      `app/(platform)/services/research/strategy/heatmap/page.tsx`,
      `app/(platform)/services/research/ml/components/run-analysis-compare-panel.tsx`, `app/opengraph-image.tsx`,
      `app/layout.tsx`, `app/(ops)/seed-demo/page.tsx`, `lib/api/mock-handler.ts` (11 hits — dev-only mock infra, check
      if these are legit fixture data like the already-excluded mock fixtures, or real UI styling literals, before
      fixing), `lib/config/services/pnl.config.ts`, `lib/config/services/strategies.config.ts`,
      `lib/dashboards/executive/executive-dashboard-data.ts` (path: `components/dashboards/executive/`),
      `components/promote/paper-trading-ledger-panels.tsx`, `components/ops/venue-connectivity.tsx`,
      `components/staging-gate.tsx`, `components/briefings/strategy-coverage-matrix.tsx`,
      `components/research/strategies/strategy-detail-panel.tsx`, `components/cockpit/cockpit-widget-grid.tsx`. (repo:
      unified-trading-system-ui)

## Codex SSOTs

`codex/06-coding-standards/ui-testing-layers.md`, `codex/06-coding-standards/quality-gates.md`.
