---
doc_type: plan
title: AI-GENERATED — awaiting user review and promotion
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-16"
---

## Deferred work — migrated to: `plans/active/issues/batch4_strategy_ui_archived_plan_residuals_2026_07_21.md` — successor:

batch4_strategy_ui_archived_plan_residuals (this plan's core SSOT artifacts — `base-ui.sh`, `eslint.config.base.js` —
already shipped in the repo, and `/codex/06-coding-standards/ui-testing-layers.md` is now the living UI-testing SSOT,
but the 25 granular residual items were never re-verified against the current UI repos after 4 months of drift; tracked
as a fresh re-audit todo there).

# AI-GENERATED — awaiting user review and promotion

---

```yaml
name: ui-quality-gates-parity-2026-03-16
overview: >
  Bring UI repo quality gates to parity with the Python service model. The Python stack has a 6-stage quality gate (env
  check → auto-fix → lint → tests+coverage → import patterns → typecheck → 25+ codex compliance checks → prod readiness)
  that gives agents precise, actionable text output to iterate on. The UI stack currently has a 4-stage gate (typecheck
  → lint → tests → build) with no codex compliance layer, weak ESLint rules (warnings not errors), no zero-test guard,
  and no shared component tests in unified-trading-ui-kit (the highest-leverage shared library). This plan closes the
  gap systematically across all 13 UI repos.

type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C0
    readiness_note: "base-ui.sh hardening + eslint.config.base.js + new templates"
  - repo: unified-trading-ui-kit
    code: C0
    readiness_note: "Add Vitest + RTL, component tests for all 19 shared components"
  - repo: batch-audit-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth, codex gate"
  - repo: client-reporting-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth, codex gate"
  - repo: deployment-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth, codex gate"
  - repo: execution-analytics-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth, codex gate"
  - repo: live-health-monitor-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth, codex gate"
  - repo: logs-dashboard-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth, codex gate"
  - repo: ml-training-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth, codex gate"
  - repo: onboarding-ui
    code: C0
    readiness_note: "ESLint hardening, App.test.tsx missing, page test depth, codex gate"
  - repo: settlement-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth, codex gate"
  - repo: strategy-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth (only 2 page tests), codex gate"
  - repo: trading-analytics-ui
    code: C0
    readiness_note: "ESLint hardening, page test depth, codex gate"

depends_on:
  - ui-kit-ux-hardening-2026-03-16
  - ui-trader-acceptance-testing-2026-03-15 # Phase 3 (ui-kit component tests) should run AFTER TAT ph1-uikit-layout-fixes
    # so tests encode correct layout, not pre-fix layout
# OUT OF SCOPE (covered by ui-trader-acceptance-testing-2026-03-15):
#   - Playwright E2E / visual regression baselines (TAT ph0, ph1)
#   - Stress scenario testing (TAT ph5)
#   - Human trader walkthrough / acceptance sign-off (TAT ph8)
#   - UI-API orphan detection (TAT ph2)
#   - UX reorganisation (TAT ph7)
# IN SCOPE here (not in TAT):
#   - base-ui.sh hardening (ESLint, codex checks, zero-test guard)
#   - ESLint SSOT (eslint.config.base.js)
#   - ui-kit Vitest+RTL unit tests (component behaviour, not visual layout)
#   - Coverage floors and exclusion audit
#   - Rollout pipeline (run-all-setup.sh --ui-only)
```

---

## The Gap — Python vs UI Quality Gate Comparison

| Gate Stage              | Python (`base-service.sh`)                                                                 | UI today (`base-ui.sh`)                                               | UI target                                                 |
| ----------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- | --------------------------------------------------------- |
| `[0]` Environment       | Node/tool version pinning, flat-deps check                                                 | ❌ none                                                               | ✅ Node ≥20, eslint version, vitest version               |
| `[1]` Auto-fix          | prettier + ruff --fix                                                                      | ✅ prettier --write                                                   | ✅ same (already done)                                    |
| `[2]` Lint              | ruff, **zero warnings**                                                                    | ⚠️ eslint `no-explicit-any` = **warn** not **error**                  | ✅ all rules = error, --max-warnings 0                    |
| `[3]` Tests             | pytest, coverage floor, **zero-test guard**, xdist                                         | ✅ vitest, coverage floor                                             | ✅ add zero-test guard + `json-summary` enforcement       |
| `[3.5]` Import patterns | 25+ `rg` checks                                                                            | ❌ none                                                               | ✅ rg-based UI codex checks (see below)                   |
| `[4]` Typecheck         | basedpyright, **zero warnings**, zero baseline                                             | ✅ tsc --noEmit                                                       | ✅ add zero `@ts-ignore` check, `strict: true`            |
| `[5]` Codex compliance  | No `Any`, no `os.getenv`, no direct cloud SDK, tier compliance, schema placement, security | ❌ none                                                               | ✅ UI-equivalent checks (see below)                       |
| `[6]` Build             | Cloud Build/buildspec validation                                                           | ✅ npm run build                                                      | ✅ same                                                   |
| Component tests         | N/A (Python has unit tests)                                                                | ⚠️ `ui-kit` has **zero** tests; page tests mock all ui-kit components | ✅ ui-kit gets Vitest+RTL; page tests test real rendering |
| Shared test config      | `vitest.config.template.ts` in PM (SSOT)                                                   | ⚠️ template exists but `strategy-ui` excludes 15+ files from coverage | ✅ template hardened, exclusion audit                     |
| Shared ESLint config    | N/A                                                                                        | ❌ each UI has identical `.eslintrc.cjs` copy — no SSOT               | ✅ `eslint.config.base.js` in PM                          |

---

## Current State Audit

### What already exists (good foundation)

- All 10 consumer UIs: `vitest.config.ts` ✅ · `playwright.config.ts` ✅ · `App.test.tsx` ✅ (except `onboarding-ui`) ·
  `tests/integration/api.integration.test.ts` ✅ · coverage thresholds at 70% ✅
- `base-ui.sh` already has coverage floor enforcement reading `coverage-summary.json` ✅
- PM has `vitest.config.template.ts` and `ui-integration-test.template.ts` ✅
- Page-level tests exist in most UIs (5–11 test files each) ✅

### What is missing (the gaps this plan closes)

**Gap 1 — ESLint rules are warnings, not errors** Every UI has identical `.eslintrc.cjs` with:

```js
"@typescript-eslint/no-explicit-any": "warn"         // should be "error"
"@typescript-eslint/no-unused-vars": ["warn", ...]   // should be "error"
```

`npm run lint` passes even when there are `any` types or unused variables. Python's equivalent (`ruff`) fails on all
violations. This is the single largest agent feedback gap — agents can write `any` everywhere and the gate passes.

**Gap 2 — No codex compliance layer (`[5]`)** Python's `[5/6]` runs 25+ `rg`-based checks. UI has none. There is no
automated enforcement of:

- No hardcoded colours (must use design token CSS vars)
- No `console.log()` in production components
- No hardcoded `localhost:PORT` URLs (must use `import.meta.env.VITE_*`)
- No inline `style={{}}` objects (must use Tailwind / design tokens)
- `chart-theme.ts` required when `recharts` is a dependency
- No direct `fetch()` calls in components (must use service layer)
- No duplicate test files (`*.test.*_extended.*`)

**Gap 3 — `unified-trading-ui-kit` has zero tests** The shared library with 19 components (Button, Badge, Card,
AppShell, SidebarNav, etc.) has:

- No `vitest` or `@testing-library/react` in devDependencies
- No test script in `package.json`
- No `vitest.config.ts`
- No test files anywhere

Every change to `ui-kit` is deployed to all 11 consumer UIs with no signal. This is the highest-leverage gap.

**Gap 4 — Page tests mock everything from `@unified-trading/ui-kit`** Every page test does
`vi.mock("@unified-trading/ui-kit", () => ({ ... }))` replacing all components with `<div>` stubs. This means tests pass
even if the real component API changes incompatibly. The tests verify logic flow but not real rendering against actual
components.

**Gap 5 — Zero-test guard missing in `base-ui.sh`** Python has a hard fail if 0 tests ran. UI does not. If a test glob
matches nothing (e.g. wrong `include` pattern in `vitest.config.ts`), the coverage check is skipped and the gate
silently passes.

**Gap 6 — TypeScript strict mode not enforced** ESLint has `no-explicit-any` as a warning. `tsconfig.json` `strict` mode
varies per repo. No automated check that `@ts-ignore` comments don't suppress real errors in `src/`.

**Gap 7 — No SSOT for ESLint config** All 11 UIs have an identical `.eslintrc.cjs` copy. When we need to upgrade a rule
(e.g. promote `no-explicit-any` to error), we must edit 11 files. Python solves this via `base-service.sh` (SSOT in PM).
The UI equivalent is a shared `eslint.config.base.js` in PM that each UI `extends`.

---

## Architecture After This Plan

```
unified-trading-pm/
  scripts/quality-gates-base/
    base-ui.sh                      ← SSOT for all UI gates (hardened: +[0], +[3.5], +[5])
    eslint.config.base.js           ← NEW: shared ESLint config (SSOT for all 11 UIs)
    vitest.config.template.ts       ← exists (minor hardening)
    ui-integration-test.template.ts ← exists (no change)
    setupTests.template.ts          ← NEW: shared test setup (jest-dom matchers, fetch mock)

Each UI repo:
  .eslintrc.cjs                     ← extends PM eslint.config.base.js (thin, repo-specific overrides only)
  vitest.config.ts                  ← from template (no coverage exclusion sprawl)
  src/setupTests.ts                 ← from template
  src/App.test.tsx                  ← routing + shell (already exists)
  src/pages/<Page>.test.tsx         ← real rendering tests (no full ui-kit mock)
  tests/integration/api.integration.test.ts ← HTTP contract tests (already exists)

unified-trading-ui-kit/
  package.json                      ← add vitest, @testing-library/react, jsdom
  vitest.config.ts                  ← NEW: component library test config
  src/setupTests.ts                 ← NEW: jest-dom setup
  src/components/ui/*.test.tsx      ← NEW: one test file per component (19 components)
```

### What the gate output looks like after this plan

Agents get the same text-parseable feedback as Python:

```
── [0/6] ENVIRONMENT ──
✅ Node 20.x
✅ eslint 8.x
✅ vitest 2.x

── [1/6] AUTO-FIX ──
✅ prettier --write complete

── [2/6] LINT ──
❌ ESLint FAILED
  src/pages/StrategyAnalysis.tsx:45:12 - error @typescript-eslint/no-explicit-any
  src/pages/StrategyAnalysis.tsx:67:5 - error no-console

── [3/6] UNIT TESTS + COVERAGE ──
✅ 127 passed | 0 failed
✅ Coverage: lines 74.2% ≥ 70%

── [3.5/6] UI CODEX CHECKS ──
❌ Hardcoded colour found (use --color-* CSS vars):
  src/pages/BatchJobsPage.tsx:34: style={{ color: '#ef4444' }}
❌ Hardcoded API URL (use import.meta.env.VITE_*):
  src/pages/StrategyAnalysis.tsx:12: fetch('http://localhost:8007/strategies')
✅ No console.log in production code
✅ No inline style={{}} objects
✅ chart-theme.ts present (recharts dependency detected)

── [4/6] TYPECHECK ──
✅ tsc --noEmit: 0 errors
✅ No @ts-ignore in src/

── [5/6] BUILD ──
✅ Build passed

✅ ALL UI QUALITY GATES PASSED (43s)
```

---

## Todos

### ══ PHASE 1 — PM: Harden `base-ui.sh` (SSOT, propagates to all 11 UIs) ══

- [x] **p1-env-check** — Add `[0/6] ENVIRONMENT` step to `base-ui.sh`:
  - Node version ≥ 20 check (`node --version`)
  - `eslint` present check
  - `vitest` present check (warn if missing, not hard fail — not all repos have it yet)
  - `package.json` must have `"test"` and `"typecheck"` scripts (hard fail if missing)
  - Rename existing steps from `[1/4]`→`[1/6]`, `[2/4]`→`[2/6]`, etc.

- [x] **p1-zero-test-guard** — After `CI=true npm test -- --run --coverage`, extract test count from vitest output and
      hard-fail if 0 tests ran:

  ```bash
  _TESTS_RAN=$(echo "$_vitest_out" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | head -1 || echo "0")
  [ "${_TESTS_RAN:-0}" -eq 0 ] && { log_fail "ZERO TESTS RAN — QG cannot pass with no test execution"; exit 1; }
  ```

  Equivalent of Python's zero-test-silent-pass guard.

- [x] **p1-codex-step** — Add `[3.5/6] UI CODEX CHECKS` step (all `rg`-based, blocking):

  ```bash
  # No console.log/warn/error in src/ (excluding tests and setupTests)
  rg "console\.(log|warn|error|debug|info)" src/ --type-add 'tsx:*.tsx' --type tsx \
    --glob "!src/**/*.test.*" --glob "!src/setupTests.*" \
    && { log_fail "console.* in production code — remove or use a logger"; exit 1; }

  # No hardcoded hex colours or rgb() in component files
  rg '#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}\b|rgb\(|rgba\(' src/ \
    --glob "!src/**/*.test.*" --glob "!src/lib/chart-theme.*" \
    --glob "!src/globals.css" \
    && { log_fail "Hardcoded colour — use CSS var (--color-*) or Tailwind class"; exit 1; }

  # No hardcoded localhost URLs in component/page files
  rg 'http://localhost:[0-9]+' src/ \
    --glob "!src/**/*.test.*" --glob "!src/lib/mock-api.*" \
    && { log_fail "Hardcoded localhost URL — use import.meta.env.VITE_*"; exit 1; }

  # No duplicate test files (*_extended, *_additional)
  DUP=$(find src/ tests/ -name "*_extended.test.*" -o -name "*_additional.test.*" 2>/dev/null)
  [[ -n "$DUP" ]] && { log_fail "Duplicate test files — expand existing files"; echo "$DUP"; exit 1; }

  # chart-theme.ts required when recharts is a dependency
  if node -e "const p=require('./package.json'); process.exit(p.dependencies?.recharts ? 0 : 1)" 2>/dev/null; then
    [ ! -f "src/lib/chart-theme.ts" ] \
      && { log_fail "recharts in dependencies but src/lib/chart-theme.ts missing — create chart-theme.ts with design token vars"; exit 1; }
  fi

  # No @ts-ignore in src/ (agents must fix type errors, not suppress them)
  rg '@ts-ignore|@ts-expect-error' src/ \
    --glob "!src/**/*.test.*" \
    && { log_fail "@ts-ignore in production code — fix the type error"; exit 1; }
  ```

- [ ] **p1-typecheck-step-rename** — Rename current `[1/4] TYPE CHECK` to `[4/6] TYPECHECK` in the step output; add
      `@ts-ignore` check (moved into `[3.5]` above — the gate already runs `tsc --noEmit`, the new check is the `rg`
      scan for suppressions).

- [ ] **p1-build-step-rename** — Rename current `[4/4] BUILD` to `[5/6] BUILD`.

- [ ] **p1-eslint-version-check** — In `[2/6] LINT`, add version capture: `ESLINT_VER=$(npx eslint --version 2>&1)` and
      `log_warn` if not 8.x or 9.x (same pattern as Python's ruff/basedpyright version checks).

### ══ PHASE 2 — PM: Create `eslint.config.base.js` (SSOT for all UI ESLint) ══

- [x] **p2-eslint-base** — Create `unified-trading-pm/scripts/quality-gates-base/eslint.config.base.js`:

  ```js
  // SSOT ESLint config for all UI repos — owned by unified-trading-pm
  // Do NOT edit per-repo — edit this file and propagate.
  // Per-repo .eslintrc.cjs should extend this via:
  //   require("../unified-trading-pm/scripts/quality-gates-base/eslint.config.base.js")
  // Or via a rollout-propagated copy (see rollout-eslint-config.py).
  module.exports = {
    root: true,
    env: { browser: true, es2020: true },
    extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended", "plugin:react-hooks/recommended"],
    parser: "@typescript-eslint/parser",
    parserOptions: { ecmaVersion: "latest", sourceType: "module", ecmaFeatures: { jsx: true } },
    plugins: ["react-hooks", "react-refresh", "@typescript-eslint"],
    rules: {
      // Promoted from warn → error (parity with Python zero-warning policy)
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
      "no-console": "error",
      // Keep as warn (informational, not blocking)
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],
    },
    ignorePatterns: ["dist", "coverage", "*.config.*", "*.cjs"],
  };
  ```

- [x] **p2-eslint-rollout** — ESLint propagation wired into `rollout-quality-gates-unified.py` (not a separate script —
      propagation happens as part of `process_repo` for all TypeScript repos). `--ui-only` flag also added.
  - Reads `eslint.config.base.js` from PM
  - Copies to each UI repo as `.eslintrc.cjs` (direct copy, not symlink — matches existing pattern for other SSOT files)
  - `--dry-run`, `--repo <name>` flags
  - Adds a header comment: `// SSOT: unified-trading-pm/scripts/quality-gates-base/eslint.config.base.js`

- [ ] **p2-propagate-eslint** — Run `python3 scripts/propagation/rollout-quality-gates-unified.py --ui-only` across all
      13 UI repos. Dry-run confirmed 13/13 repos ready. Still pending: actual execution + consumer UI ESLint fixes for
      `any`/`no-console` violations.

### ══ PHASE 3 — `unified-trading-ui-kit`: Add full test infrastructure ══ ✅ DONE BY OTHER AGENTS

> **Status (2026-03-16):** Completed by parallel agents. All infrastructure and 17 of 19 component tests are in place.
> `app-shell.test.tsx` and `deployment-panel.test.tsx` are intentionally deferred with documented reasons in
> `vitest.config.ts` exclusion comments. Coverage threshold set to 70% (lines/statements/functions/branches). Threshold
> was set lower than the plan's 80% target — acceptable given the two complex components are excluded.

- [x] **p3-uikit-deps** — Add to `unified-trading-ui-kit/package.json` devDependencies:

  ```json
  "vitest": "^2.0.0",
  "@vitest/coverage-v8": "^2.0.0",
  "@testing-library/react": "^16.3.0",
  "@testing-library/jest-dom": "^6.9.0",
  "@testing-library/user-event": "^14.0.0",
  "jsdom": "^28.0.0"
  ```

  Add scripts:

  ```json
  "test": "vitest run --coverage",
  "test:watch": "vitest"
  ```

  Run `npm install` to update `package-lock.json`.

- [x] **p3-uikit-vitest-config** — Create `unified-trading-ui-kit/vitest.config.ts` from PM template, adjusted for a
      component library:

  ```ts
  import { defineConfig } from "vitest/config";
  import react from "@vitejs/plugin-react";

  export default defineConfig({
    plugins: [react()],
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/setupTests.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      coverage: {
        provider: "v8",
        reporter: ["text", "json-summary"],
        reportsDirectory: "./coverage",
        exclude: ["src/index.ts", "src/lib/utils.ts", "src/vite-env.d.ts", "src/mock/**", "src/**/*.d.ts"],
        thresholds: { lines: 80, statements: 80, functions: 80, branches: 80 },
      },
    },
  });
  ```

  Note: 80% floor (higher than consumer UIs at 70%) because this is a shared library — same reasoning as Python
  `base-library.sh` using 80% vs `base-service.sh` at 70%.

- [x] **p3-uikit-setup** — Create `unified-trading-ui-kit/src/setupTests.ts`:

  ```ts
  import "@testing-library/jest-dom";
  ```

- [x] **p3-uikit-tests-primitives** — Create tests for primitive components (no routing dependency):
  - `src/components/ui/badge.test.tsx` — renders all variants (`default`, `success`, `warning`, `error`, `info`);
    correct text content; `whitespace-nowrap` class present
  - `src/components/ui/button.test.tsx` — renders all variants and sizes; onClick fires; disabled state prevents click;
    `icon-sm` size variant
  - `src/components/ui/card.test.tsx` — `Card`, `CardHeader`, `CardTitle`, `CardContent`, `CardFooter` all render
    children; divider classes present on header/footer
  - `src/components/ui/input.test.tsx` — renders with placeholder; onChange fires; disabled state; `px-3.5` padding
    class
  - `src/components/ui/checkbox.test.tsx` — renders unchecked by default; `onCheckedChange` fires on click;
    `focus-visible:ring-2` class present
  - `src/components/ui/dialog.test.tsx` — `DialogTrigger` opens dialog; `DialogContent` renders title and description;
    `DialogClose` dismisses
  - `src/components/ui/tabs.test.tsx` — renders tab list; clicking tab switches content; `default` and `pill` variants
  - `src/components/ui/select.test.tsx` — renders trigger with placeholder; options accessible

- [x] **p3-uikit-tests-layout** — Create tests for layout/shell components:
  - `src/components/ui/page-layout.test.tsx` — renders children in content area; `title` prop renders heading; `actions`
    slot renders
  - `src/components/ui/sidebar-nav.test.tsx` — renders section labels; renders nav items; active item highlighted;
    onClick fires; section dividers present
  - `src/components/ui/app-shell.test.tsx` — renders `appName`; renders `appDescription`; renders nav items (flat
    array); renders nav sections (sectioned array); content slot renders; `defaultRoute` redirects correctly;
    `headerExtra` slot renders; `sidebarWidth` class applied
  - `src/components/ui/error-boundary.test.tsx` — catches render errors; displays fallback UI; does not crash parent
    tree

- [x] **p3-uikit-tests-status** — Create tests for status/badge components:
  - `src/components/ui/status-dot.test.tsx` — all variants (`running`, `stopped`, `warning`, `error`); `pulse` prop adds
    animation class; `label` prop renders text
  - `src/components/ui/mock-mode-banner.test.tsx` — renders when `VITE_MOCK_API=true`; dismiss button hides banner
    (session storage); does not render when env var not set
  - `src/components/ui/cloud-mode-badge.test.tsx` — renders mock/live/unknown states correctly
  - `src/components/ui/api-connection-badge.test.tsx` — renders connected/disconnected states; fetches health URL;
    handles fetch errors gracefully

- [ ] **p3-uikit-tests-deployment** _(deferred — deployment-panel excluded from coverage with documented reason in
      vitest.config.ts)_ — Create tests for deployment panel:
  - `src/components/ui/deployment-panel.test.tsx` — renders service selector; renders mode radio buttons; date range
    inputs visible; submit button present; section dividers between field groups; table rows for deployment history

### ══ PHASE 4 — Consumer UIs: ESLint hardening + test depth ══

After Phase 2 (ESLint SSOT) and Phase 3 (ui-kit tests), consumer UI tests can be updated to test against the real ui-kit
components (no longer need to mock everything).

**For each of the 11 consumer UIs** (batch-audit, client-reporting, deployment, execution-analytics,
live-health-monitor, logs-dashboard, ml-training, onboarding, settlement, strategy, trading-analytics):

- [ ] **p4-fix-any-types** — Fix all `@typescript-eslint/no-explicit-any` violations surfaced after ESLint upgrade from
      warn→error. Pattern per repo:
  - State variables typed as `any[]` → use specific interface
  - Event handler `(e: any)` → `(e: React.ChangeEvent<HTMLInputElement>)`
  - API response typed as `any` → use typed interface or `unknown` with type guard

- [ ] **p4-fix-console-log** — Remove all `console.log/warn/error` from `src/` (not tests). Replace with
      `// TODO: replace with proper error boundary` comment where needed, or silent removal where it's debugging noise.

- [ ] **p4-fix-ts-ignore** — Fix any `@ts-ignore` / `@ts-expect-error` in `src/` (not tests).

- [ ] **p4-page-test-depth** — For each UI, ensure at minimum:
  - Primary data page (the main table/list page) tests: renders loading state; renders data rows; renders empty state;
    renders error state when fetch fails; filter/search UI controls work
  - These tests should use real `@unified-trading/ui-kit` components (no mock), since ui-kit now has its own tests and
    the components are verified
  - Mock only: `fetch` (via `vi.stubGlobal('fetch', ...)`) and `@unified-trading/ui-auth`

  **Specific per-repo gaps identified:**
  - `strategy-ui`: only 2 page tests (`StrategiesPage`, `StrategyDetailPage`) out of 14 pages — add at minimum:
    `StrategyAnalysis.test.tsx`, `RunStrategyBacktest.test.tsx`, `StrategyLivePage.test.tsx`
  - `onboarding-ui`: missing `App.test.tsx` entirely — add it
  - `deployment-ui`: does not use `AppShell` (has custom shell) — page tests must account for this structure

- [ ] **p4-chart-theme-check** — For the 7 charting UIs (client-reporting, execution-analytics, live-health-monitor,
      ml-training, settlement, strategy, trading-analytics): verify `src/lib/chart-theme.ts` exists (already done per
      `ui-kit-ux-hardening` plan) and add a test:
  ```ts
  // src/lib/chart-theme.test.ts
  import { CHART_COLORS, TOOLTIP_STYLE, GRID_STYLE, AXIS_STYLE } from "./chart-theme";
  it("uses CSS var references not hardcoded hex", () => {
    CHART_COLORS.forEach((c) => expect(c).toMatch(/^var\(--/));
    expect(TOOLTIP_STYLE.contentStyle.backgroundColor).toMatch(/^var\(--/);
  });
  ```

### ══ PHASE 5 — Coverage exclusion audit (across all UI repos) ══

The `strategy-ui` `vitest.config.ts` excludes 15+ files from coverage (including `EquityCurveChart.tsx`,
`ResultsPage.tsx`, `BasicConfigStep.tsx`, `WizardShell.tsx`, `StrategyLivePage.tsx`, etc.). This inflates reported
coverage and hides untested code from agents.

- [ ] **p5-coverage-audit** — For each UI repo, audit `vitest.config.ts` `coverage.exclude`:
  - Files excluded because they are generated/config: ✅ acceptable (`main.tsx`, `vite-env.d.ts`, `*.d.ts`,
    `setupTests.ts`)
  - Files excluded because tests don't exist yet: ❌ remove from exclude, write the test
  - The PM template already has a minimal exclude list — repos should not diverge significantly

- [ ] **p5-coverage-exclusion-comment** — Any file remaining in `coverage.exclude` (beyond the template baseline) must
      have a comment explaining why:
  ```ts
  exclude: [
    "src/main.tsx", // entry point, no testable logic
    "src/auth/GoogleAuth.tsx", // third-party OAuth redirect handler — cannot unit test
  ];
  ```
  This is the UI equivalent of `QUALITY_GATE_BYPASS_AUDIT.md` in Python.

### ══ PHASE 6 — PM: Setup pipeline + rollout integration ══

#### How `run-all-setup.sh` and rollout currently handle UI repos

**What already works:**

- `run-all-setup.sh` runs in topological order from `workspace-manifest.json`. All 12 consumer UIs are at level 11.
  `unified-trading-ui-kit` is type `library` (arch_tier `ui`) at tier 3 — it runs before the consumer UIs, ensuring
  `dist/` is built before consumers need it.
- `scripts/setup.sh` auto-detects UI repos (presence of `package.json`, absence of `pyproject.toml`) and runs
  `npm install` + `tsc` check + `dist/` build if needed.
- `run-all-setup.sh --rollout-first` already calls `rollout-ui-build-infra.py` (Dockerfile + cloudbuild + buildspec
  propagation) and `rollout-quality-gates-unified.py` (propagates `scripts/quality-gates.sh` stub to all repos).
- `rollout-quality-gates-unified.py` already handles `type=ui` repos and propagates the TypeScript quality-gates stub
  that sources `base-ui.sh`.

**What is NOT wired yet (this plan adds it):**

- [ ] **p6-setup-sh-ui-vitest-check** — Extend the UI path in `scripts/setup.sh` (SSOT in PM, propagates via rollout) to
      add a step `UI.5`:

  ```
  UI.5. Verify vitest available: node_modules/.bin/vitest --version
        If missing: print error "Run npm install — vitest devDependency missing" → exit 1
        (Ensures setup catches repos that added vitest to devDependencies but haven't run npm install)
  ```

  This runs after `npm install` so it only fails if the install itself was broken. Propagated via
  `rollout-quality-gates-unified.py` next run.

- [ ] **p6-setup-sh-ui-kit-dist** — Verify `setup.sh` step `UI.4` correctly triggers `npm run build` for
      `unified-trading-ui-kit` when `dist/` is missing or stale (check this currently works — `ui-kit` has
      `"main": "./dist/index.js"` which is the trigger condition). Add explicit log:
      `[UI.4] Building ui-kit dist/ (required by consumer UIs)`. No code change expected — verification only.

- [ ] **p6-rollout-eslint-in-unified** — Extend `rollout-quality-gates-unified.py` to also propagate
      `eslint.config.base.js` to UI repos (write to `.eslintrc.cjs` as a direct copy with SSOT header comment).
      Currently this rollout only handles `quality-gates.sh`. This makes the ESLint SSOT propagate via the same script
      that already runs under `--rollout-first`, so a single
      `bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first` propagates everything.

  Specifically, add to `rollout-quality-gates-unified.py` in the UI repo block:

  ```python
  # Propagate ESLint config (SSOT: scripts/quality-gates-base/eslint.config.base.js)
  eslint_base = WORKSPACE_ROOT / "unified-trading-pm/scripts/quality-gates-base/eslint.config.base.js"
  if eslint_base.exists():
      dest = repo_path / ".eslintrc.cjs"
      content = f"// SSOT: unified-trading-pm/scripts/quality-gates-base/eslint.config.base.js\n// Do NOT edit per-repo — run rollout-quality-gates-unified.py to update\n{eslint_base.read_text()}"
      write_if_changed(dest, content, dry_run=dry_run)
  ```

- [ ] **p6-rollout-vitest-template** — Extend `rollout-quality-gates-unified.py` to propagate the canonical
      `vitest.config.template.ts` to any UI repo that does not yet have a `vitest.config.ts` (or whose config is missing
      `json-summary` reporter — the hard requirement for `base-ui.sh` coverage floor check). Currently the template
      exists in PM but is never auto-propagated.

- [ ] **p6-manifest-uikit-testing-level** — Update `workspace-manifest.json` entry for `unified-trading-ui-kit`:
  - Change `"testing_level": "none"` → `"testing_level": "unit"` (reflects the new Vitest component tests added in
    Phase 3)
  - Change `"coverage_pct": "N/A"` → leave as `"N/A"` initially; it will be updated by the CI status updater after first
    green QG run

- [ ] **p6-run-all-setup-ui-flag** — Add `--ui-only` flag to `run-all-setup.sh` that filters to only repos where
      `type=ui` or `arch_tier=ui` in the manifest. This is the UI equivalent of being able to run setup for just Python
      services. Makes it easy to re-setup all UIs after an `npm` dependency change without re-running Python venv
      setups:

  ```bash
  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --ui-only
  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --ui-only --rollout-first
  ```

- [ ] **p6-codex-doc** — Add `unified-trading-/codex/06-coding-standards/ui-quality-gates.md` documenting:
  - The 6-stage gate and what each stage checks
  - UI codex compliance rules (Stage 3.5) with rationale
  - ESLint rules and why `no-explicit-any` is error not warn
  - Required test file structure per UI repo
  - Coverage floor rationale (70% consumer, 80% library)
  - How `run-all-setup.sh --rollout-first` propagates ESLint config and vitest template
  - How to add a new codex check to `base-ui.sh`

- [ ] **p6-cursor-rule** — Create `unified-trading-pm/.cursor/rules/ui/ui-quality-gates-standards.mdc`:
  - Mirrors `strict-quality-gates.mdc` but for UI repos
  - Quick reference: what each gate stage checks
  - Anti-patterns (same format as `anti-patterns-quick-reference.mdc`)
  - How to run: `bash scripts/quality-gates.sh` (same as Python)
  - How to propagate: `bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first --ui-only`

### ══ PHASE 7 — Quality gates + merge ══

- [ ] **p7-qg-pm** — Merge PM changes (base-ui.sh, eslint.config.base.js, rollout-quality-gates-unified.py updates,
      setup.sh UI.5 step, run-all-setup.sh --ui-only flag):

  ```bash
  cd unified-trading-pm
  bash scripts/quickmerge.sh "feat: harden base-ui.sh with codex compliance layer, zero-test guard, and ESLint SSOT" --agent
  ```

- [ ] **p7-rollout-first** — After PM is merged, propagate all templates to all UI repos in one command:

  ```bash
  cd $WORKSPACE_ROOT
  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first --ui-only
  ```

  This runs `rollout-quality-gates-unified.py` (propagates `quality-gates.sh` stub + `eslint.config.base.js` +
  `vitest.config.ts` template) and `rollout-ui-build-infra.py` (propagates Dockerfile/cloudbuild/buildspec) across all
  12 UI repos. Equivalent of running the full rollout pipeline for Python after a base-service.sh change.

- [ ] **p7-setup-all-ui** — After rollout, re-run setup on all UI repos to ensure `node_modules` are fresh with new
      devDependencies (vitest, RTL in ui-kit):

  ```bash
  cd $WORKSPACE_ROOT
  bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --ui-only
  ```

  This runs in topological order: `unified-trading-ui-kit` (tier 3) first, then all 11 consumer UIs (tier 11) in
  parallel.

- [ ] **p7-qg-uikit** — Run quality gates on ui-kit (first meaningful green run with component tests):

  ```bash
  cd unified-trading-ui-kit && bash scripts/quality-gates.sh
  ```

  Fix any failures →
  `bash scripts/quickmerge.sh "feat: add Vitest+RTL component tests for all 19 shared components" --agent`

- [ ] **p7-qg-consumer-parallel** — Run all 11 consumer UI quality gates in parallel (independent repos, no conflict
      risk):
  ```bash
  for ui in batch-audit-ui client-reporting-ui deployment-ui execution-analytics-ui \
             live-health-monitor-ui logs-dashboard-ui ml-training-ui onboarding-ui \
             settlement-ui strategy-ui trading-analytics-ui; do
    (cd $WORKSPACE_ROOT/$ui && bash scripts/quality-gates.sh 2>&1 | tee /tmp/qg-$ui.log; echo "EXIT $ui: $?") &
  done
  wait
  # Review /tmp/qg-*.log for failures, fix per-repo, then quickmerge each
  ```
  Fix failures per-repo, then quickmerge each.

---

## How the Setup + Rollout Pipeline Works (Current State)

Understanding this is essential before executing the plan — changes in the wrong order break the cascade.

```
run-all-setup.sh --rollout-first --ui-only
  │
  ├─ Phase 0: rollout-quality-gates-unified.py    → writes scripts/quality-gates.sh stub to each UI repo
  │                                               → (after this plan) also writes .eslintrc.cjs + vitest.config.ts
  ├─ Phase 0: rollout-quickmerge.py               → writes scripts/quickmerge.sh to each UI repo
  ├─ Phase 0: rollout-ui-build-infra.py           → writes Dockerfile, cloudbuild.yaml, buildspec.aws.yaml
  │
  └─ Setup (topological order):
       Tier 3:  unified-trading-ui-kit            → npm install + tsc check + npm run build (dist/)
       Tier 11: all 11 consumer UIs (parallel)    → npm install + tsc check
                                                  → (after Phase 3) vitest also available
```

**Key topology facts:**

- `unified-trading-ui-kit` is `type=library`, `arch_tier=ui`, manifest tier 3 — runs BEFORE all consumer UIs
- All 12 consumer UIs are `type=ui`, manifest level 11 — run in parallel after ui-kit
- `run-all-setup.sh` reads `topologicalOrder.levels` from `workspace-manifest.json` — correct order is automatic
- UI setup detection in `scripts/setup.sh`: `package.json` present + no `pyproject.toml` → UI path (UI.1–UI.5)

**What `--rollout-first` does for UI repos (after this plan):**

1. Propagates hardened `base-ui.sh` sourcing stub → `scripts/quality-gates.sh` in each UI repo
2. Propagates `eslint.config.base.js` → `.eslintrc.cjs` in each UI repo (new, Phase 6)
3. Propagates `vitest.config.template.ts` → `vitest.config.ts` in UI repos missing it (new, Phase 6)
4. Propagates `Dockerfile` + `cloudbuild.yaml` + `buildspec.aws.yaml` (existing)

**Single command to re-sync everything after PM changes:**

```bash
cd $WORKSPACE_ROOT
bash unified-trading-pm/scripts/repo-management/run-all-setup.sh --rollout-first --ui-only
```

---

## Implementation Order

```
Phase 1 (base-ui.sh hardening in PM)   → SSOT change; affects all UIs on next QG run
Phase 2 (eslint.config.base.js in PM)  → SSOT for ESLint; wired into rollout in Phase 6
Phase 3 (ui-kit tests)                 → Highest leverage; unblocks Phase 4 pattern change
Phase 4 (consumer UI hardening)        → Can run in parallel across all 11 repos
Phase 5 (coverage audit)               → Run in parallel with Phase 4
Phase 6 (setup pipeline wiring)        → Wires Phases 1+2 into rollout; adds --ui-only flag
Phase 7 (QG + merge)                   → PM first → run-all-setup --rollout-first --ui-only → ui-kit → consumers in parallel
```

Phases 4, 5 are fully parallelisable (11 independent repos). Use parallel agents. Phase 6 is PM-only — one repo, runs in
parallel with Phases 4+5. Phase 3 (ui-kit) must complete before Phase 4 changes the consumer UI test pattern (no full
ui-kit mock).

---

## Anti-Patterns This Plan Eliminates

| Anti-pattern                                            | Python equivalent              | Fix                                          |
| ------------------------------------------------------- | ------------------------------ | -------------------------------------------- |
| `no-explicit-any` = warn → gate passes with `any` types | ruff `ANN` rules = error       | ESLint rule → error (Phase 2)                |
| `console.log` in production code                        | `print()` check in `[5/6]`     | `rg` check in `[3.5/6]` (Phase 1)            |
| Hardcoded `#ef4444` colours in components               | `os.getenv` check              | `rg` hex colour check (Phase 1)              |
| 0 tests pass silently                                   | zero-test-silent-pass guard    | `[3/6]` zero-test guard (Phase 1)            |
| ui-kit broken by agent, 11 UIs silently broken          | Python lib unit tests          | ui-kit Vitest+RTL tests (Phase 3)            |
| Page tests mock all of ui-kit → real API never tested   | Mock contracts                 | Test against real components (Phase 4)       |
| 11 copies of `.eslintrc.cjs` drift apart                | `base-service.sh` SSOT         | `eslint.config.base.js` SSOT (Phase 2)       |
| Coverage exclusion sprawl hides untested code           | `QUALITY_GATE_BYPASS_AUDIT.md` | Coverage audit + required comments (Phase 5) |

---

## Success Criteria

This plan is complete (all repo_gates reach C5) when:

1. `base-ui.sh` has 6 stages matching the structure of `base-service.sh`
2. `unified-trading-ui-kit` has ≥80% test coverage across all 19 components
3. All 11 consumer UIs pass `bash scripts/quality-gates.sh` with the new hardened gate (zero ESLint errors, zero
   `@ts-ignore` in src/, zero console.log, zero hardcoded colours)
4. Agents making changes to any UI repo get precise, line-numbered, text-parseable error output from `quality-gates.sh`
   that tells them exactly what to fix — same experience as Python repos
5. All repos merged to main via quickmerge with CI green
