# AI-GENERATED — awaiting user review and promotion

---

```yaml
name: ui-kit-ux-hardening-2026-03-16
overview: >
  Systematic UX hardening of the 3 shared UI libraries and all 11 consumer UIs. Fixes dark-theme regressions,
  layout/spacing issues, interactive control polish, viewport filling, and cross-cutting consistency. No structural
  refactoring — targeted, high-impact fixes only. Based on visual inspection of all 11 UIs plus user feedback session on
  2026-03-16.
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-ui-kit
    code: C1
    readiness_note: "Phase 1 globals.css + primitives partially applied 2026-03-16."
  - repo: unified-trading-ui-auth
    code: C0
    readiness_note: "Auth error states + dev script fix done. Form field polish pending."
  - repo: batch-audit-ui
    code: C0
    readiness_note: "Per-UI fixes pending."
  - repo: client-reporting-ui
    code: C0
    readiness_note: "No sidebar — flat tab nav issue. Per-UI fixes pending."
  - repo: deployment-ui
    code: C0
    readiness_note: "BrowserRouter + .env.local + vite dedupe fixes applied. Smoke test pending."
  - repo: execution-analytics-ui
    code: C0
    readiness_note: "Dense form layout, truncated sidebar. Per-UI fixes pending."
  - repo: live-health-monitor-ui
    code: C0
    readiness_note: "Viewport fill issue. Per-UI fixes pending."
  - repo: logs-dashboard-ui
    code: C0
    readiness_note: "Per-UI fixes pending."
  - repo: ml-training-ui
    code: C0
    readiness_note: "Per-UI fixes pending."
  - repo: onboarding-ui
    code: C0
    readiness_note: "Per-UI fixes pending."
  - repo: settlement-ui
    code: C0
    readiness_note: "Critical viewport fill + table overflow issues. Per-UI fixes pending."
  - repo: strategy-ui
    code: C0
    readiness_note: "Viewport fill + sidebar truncation. Per-UI fixes pending."
  - repo: trading-analytics-ui
    code: C0
    readiness_note: "Per-UI fixes pending."

depends_on: []
```

---

## Issues Catalogue (from visual inspection + user feedback 2026-03-16)

### Already Fixed (pre-plan work)

| Fix                                                            | File                                        | Status  |
| -------------------------------------------------------------- | ------------------------------------------- | ------- |
| `color-scheme: dark` on html/body                              | `globals.css`                               | ✅ done |
| Calendar icon visible on date inputs                           | `globals.css` + `input.tsx`                 | ✅ done |
| CardHeader/CardFooter dividers                                 | `card.tsx`                                  | ✅ done |
| Sidebar nav section dividers                                   | `sidebar-nav.tsx`                           | ✅ done |
| Select trigger hover/focus parity with Input                   | `select.tsx`                                | ✅ done |
| Inactive tab readability                                       | `tabs.tsx`                                  | ✅ done |
| Table zebra striping + edge padding                            | `globals.css`                               | ✅ done |
| `.field-group` / `.stat-*` / `.alert-banner-*` utility classes | `globals.css`                               | ✅ done |
| `deployment-ui` BrowserRouter missing                          | `deployment-ui/src/App.tsx`                 | ✅ done |
| `deployment-ui` SKIP_AUTH `.env.local`                         | `deployment-ui/.env.local`                  | ✅ done |
| `vite resolve.dedupe` for react/react-dom/react-router-dom     | all 11 `vite.config.ts`                     | ✅ done |
| `ui-auth` missing `dev` script                                 | `ui-auth/package.json`                      | ✅ done |
| `npm install` for ui-auth in 4 repos                           | batch, deployment, live-health, ml-training | ✅ done |

### User-Reported Issues (session 2026-03-16)

| #   | Issue                                                                            | Affects                                                   |
| --- | -------------------------------------------------------------------------------- | --------------------------------------------------------- |
| U1  | App identity header is on the left side — takes horizontal space with no benefit | All 11 UIs                                                |
| U2  | Input/field labels need left padding to align with field content                 | All 11 UIs                                                |
| U3  | Input fields need more horizontal margin (left/right breathing room in forms)    | All 11 UIs                                                |
| U4  | Native `<select>` dropdown has no dark background — options unreadable           | execution-analytics, trading-analytics, any native select |
| U5  | Buttons without background fill are not clearly recognisable as buttons          | All 11 UIs (ghost/outline variants)                       |
| U6  | Tables too cramped — need more row height and column spacing                     | settlement, live-health, client-reporting, batch-audit    |

### Agent-Observed Issues (visual inspection)

| #   | Issue                                                                      | Affects                                      |
| --- | -------------------------------------------------------------------------- | -------------------------------------------- |
| V1  | Stat card labels below number are too small/dim — barely visible           | All 11 UIs                                   |
| V2  | Content not filling viewport — large dead black space                      | settlement-ui, live-health, strategy-ui      |
| V3  | Sidebar text truncated ("Instruments", "Availabilit") — sidebar too narrow | execution, strategy, settlement, live-health |
| V4  | `settlement-ui` table columns overflow/merge — no min-width on cells       | settlement-ui                                |
| V5  | `client-reporting-ui` has no sidebar — flat tab nav loses hierarchy        | client-reporting-ui                          |
| V6  | SELL side badge is green in trading-analytics — should always be red       | trading-analytics-ui                         |
| V7  | recharts Tooltip renders white box on dark bg                              | 7 of 11 UIs                                  |
| V8  | recharts grid/axis colours are default grey, not design tokens             | 7 of 11 UIs                                  |
| V9  | Dialog overlay has no backdrop blur                                        | All 11 UIs                                   |
| V10 | Checkbox has no visible focus ring                                         | All 11 UIs                                   |
| V11 | Badge text clips on longer status strings                                  | All 11 UIs                                   |
| V12 | Mock mode banner is harsh yellow — distracting for daily use               | All 11 UIs                                   |

---

## Todos

### ══ PHASE 1 — ui-kit shared primitives (propagates to all 11 UIs) ══

- [x] **p1-native-select-dark** — `globals.css`: style native `<select>` elements with dark bg, custom chevron SVG,
      `color-scheme: dark` so dropdown options render on `--color-bg-elevated` background. Fixes U4.

- [x] **p1-field-label-padding** — `globals.css` `.field-label`: add `padding-left: 2px` and bump color from
      `--color-text-muted` to `--color-text-secondary` so labels align with field content and are clearly readable.
      Fixes U2.

- [x] **p1-input-horizontal-margin** — `globals.css`: add `.form-row` utility (`display: grid; gap: 16px 20px`) and
      document recommended usage. `input.tsx`: increase `px-3` → `px-3.5` for slightly more internal horizontal padding.
      Fixes U3.

- [x] **p1-stat-card-labels** — `globals.css` `.stat-label`: bump font-size `11px` → `12px`, color `--color-text-muted`
      → `--color-text-secondary`, remove uppercase transform so it reads as a real label not a dim hint. `.stat-value`:
      reduce from `24px` → `22px` to balance the pair. Fixes V1.

- [x] **p1-table-spacing** — `globals.css`: increase `.table-cell` padding `13px 16px` → `14px 18px`. Add
      `min-width: 80px` to prevent column collapse in narrow viewports (fixes V4 settlement table). `.table-header-cell`
      matching increase. Already partially done — verify and tune. Fixes U6, V4.

- [x] **p1-button-ghost-border** — `button.tsx` ghost variant: add
      `border border-transparent hover:border-[var(--color-border-default)]` so ghost buttons have a visible hover
      affordance. Outline variant already has border. Fixes U5 for ghost buttons.

- [ ] **p1-badge-spacing** — `badge.tsx`: increase `px-1.5` → `px-2.5 py-0.5`, add `whitespace-nowrap`. Fixes V11.

- [ ] **p1-checkbox-focus** — `checkbox.tsx`: add
      `focus-visible:ring-2 focus-visible:ring-[var(--color-border-focus)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--color-bg-primary)]`.
      Fixes V10.

- [ ] **p1-dialog-backdrop** — `dialog.tsx` DialogOverlay: apply `bg-[var(--color-bg-overlay)] backdrop-blur-sm`. Fixes
      V9.

- [x] **p1-mock-banner-softer** — `mock-mode-banner.tsx`: use `--color-warning-dim` background + `--color-warning` text
      instead of solid amber. Add session-storage dismiss (persists across nav). Fixes V12.

- [x] **p1-button-icon-sm** — `button.tsx`: add `icon-sm` size variant `h-7 w-7` for table row action buttons. Needed by
      deployment-panel table fix.

### ══ PHASE 2 — Per-UI layout + viewport fixes ══

- [x] **p2-viewport-settlement** — `settlement-ui`: main content area not filling viewport. Check `PageLayout` usage —
      Applied `.table-header-cell`/`.table-cell`/`.table-row` classes. Fixes V2, V4.

- [x] **p2-viewport-live-health** — `live-health-monitor-ui`: same viewport fill issue. Content only uses ~55% of
      Applied table classes. Fixes V2.

- [x] **p2-viewport-strategy** — `strategy-ui`: right side strategy cards float in black void. Check grid layout in
      `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`. Fixes V2.

- [x] **p2-sidebar-width-execution** — `execution-analytics-ui`: sidebar too narrow, nav labels truncate. Increase
      `sidebarWidth="w-72"`. Fixes V3.

- [x] **p2-sidebar-width-strategy** — `strategy-ui`: same sidebar truncation issue. Fixes V3.

- [x] **p2-sell-badge-color** — `trading-analytics-ui`: SELL side badge uses green colour class. Should use Already
      correct (BUY=success, SELL=error). Fixes V6.

- [ ] **p2-client-reporting-sidebar** — `client-reporting-ui`: currently uses flat tab nav at top with no sidebar.
      Evaluate whether adding a `SidebarNav` with sections (Reports / Generate / Performance / Deployments) improves
      hierarchy. If the flat tab nav is intentional, at minimum add `gap-1` between tabs and a bottom border to the tab
      bar. Fixes V5.

- [ ] **p2-deployment-panel-layout** — `unified-trading-ui-kit` `deployment-panel.tsx`: the Deploy Service card packs
      too many fields with no sub-section grouping. Add `border-t border-[--color-border-subtle]` sub-section dividers
      between Mode / Date range / Asset scope / Live fields. Use `.field-group` / `.field-label` classes. Apply
      `.table-row` / `.table-cell` to deployment history table. Use `size="icon-sm"` for row action buttons.

### ══ PHASE 3 — recharts theme consistency (7 charting UIs) ══

- [ ] **p3-recharts-chart-theme** — In each of the 7 UIs with recharts (client-reporting, execution-analytics,
      live-health-monitor, ml-training, settlement, strategy, trading-analytics): create `src/lib/chart-theme.ts` with:
  - `CHART_COLORS`: array of design token CSS var strings (`--color-accent-cyan`, `--color-accent-green`, etc.)
  - `TOOLTIP_STYLE`: `contentStyle` object for `<Tooltip>` with `--color-bg-elevated` bg, `--color-border-default`
    border, `border-radius: var(--radius-md)`
  - `GRID_STYLE`: `CartesianGrid` stroke = `var(--color-border-subtle)`
  - `AXIS_STYLE`: `XAxis`/`YAxis` tick fill = `var(--color-text-muted)`, axisLine stroke = `var(--color-border-default)`

- [ ] **p3-recharts-apply** — Apply `chart-theme.ts` tokens to every `<Tooltip>`, `<CartesianGrid>`, `<XAxis>`,
      `<YAxis>` in each charting UI. Replace any hardcoded hex colour strings in chart series with `CHART_COLORS[n]`.

### ══ PHASE 4 — ui-auth + misc ══

- [ ] **p4-auth-error-structured** — `ui-auth`: wrap auth error states (token expired, network fail) in structured
      `{ code, message, detail }` shape. Consumer UIs can then render `.alert-banner-error` consistently.

- [ ] **p4-auth-form-dark** — `ui-auth`: audit if any login/callback HTML is rendered directly. If yes, apply
      `color-scheme: dark` + design token styles. If no DOM rendered by ui-auth, mark N/A.

### ══ PHASE 5 — quality gates + merge ══

- [ ] **p5-qg-uikit** — `cd unified-trading-ui-kit && bash scripts/quality-gates.sh` → quickmerge when green.

- [ ] **p5-qg-uiauth** — `cd unified-trading-ui-auth && bash scripts/quality-gates.sh` → quickmerge if Phase 4 changes
      were made.

- [ ] **p5-qg-consumer-uis** — For each consumer UI with page-level fixes: `bash scripts/quality-gates.sh` → quickmerge.
      Run all 11 in parallel (independent repos).

---

## Implementation Order

```
Phase 1 (ui-kit)   → edit globals.css + component files → HMR propagates to all 11 UIs instantly
Phase 2 (per-UI)   → fix layout/viewport issues in individual repos
Phase 3 (recharts) → 7 charting UIs (can run in parallel with Phase 2)
Phase 4 (ui-auth)  → minor auth library changes
Phase 5 (QG)       → quality gates + quickmerge all repos
```

Phases 2 and 3 are fully parallelisable. Phase 5 runs after all others.

## How Changes Propagate

```
Edit unified-trading-ui-kit/src/  →  tsc --watch rebuilds dist/
                                  →  Consumer Vite dev servers HMR pick up new dist/
                                  →  Changes visible in browser without restart
```

Dev watchers are started automatically by `bash unified-trading-pm/scripts/dev/dev-start.sh --all --frontend-only`.
