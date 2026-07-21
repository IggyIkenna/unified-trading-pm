---
doc_type: codex-ssot
title: UI Testing Layers
summary: >-
  The 8-layer UI testing strategy (L0 contract-alignment → L5 performance) across UI repos: what each layer tests, where
  it lives, credentials, triggers, gate-enforcement-by-branch, and the `pw:L2 ✓` + regression-spec plan-tick evidence
  rule.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-ui, e2e-testing, unified-api-contracts, unified-trading-pm, unified-trading-system-ui]
scope: [engineer]
tags: [ui, quality-gates, validation, frontend]
related:
  [integration-testing-layers.md, ../02-data/vcr-cassette-ownership.md, ../14-customer-journeys/testing/README.md]
created: 2026-04-24
authoritative_for: [8-layer UI testing strategy]
referenced_by:
  [
    codex/06-coding-standards/test-coverage-data-status.md,
    codex/06-coding-standards/testing.md,
    codex/06-coding-standards/ui-branding.md,
    codex/06-coding-standards/ui-service-separation.md,
  ]
owner:
last_reviewed: 2026-07-21
code_refs: [deployment-ui/tests/smoke/alerts-page.spec.ts]
---

# UI Testing Layers

**Last Updated:** 2026-04-24 **SSOT for:** The 8-layer UI testing strategy across all UI repos
(`unified-trading-system-ui`, `deployment-ui`). **Cross-refs:**

- Backend testing SSOT: [`06-coding-standards/integration-testing-layers.md`](integration-testing-layers.md)
- Playbook testing (L3a subset): [`14-customer-journeys/testing/README.md`](../14-customer-journeys/testing/README.md),
  [`14-customer-journeys/testing/test-matrix.md`](../14-customer-journeys/testing/test-matrix.md)
- VCR cassette policy: [`02-data/vcr-cassette-ownership.md`](../02-data/vcr-cassette-ownership.md)
- UI functionality + API wiring:
  [`05-infrastructure/ui-functionality-requirements.md`](../05-infrastructure/ui-functionality-requirements.md)
- UI repo quality gates rule: workspace `.claude/rules/ui.md`

---

## Overview

Eight testing layers, each with a distinct purpose, location, dependency profile, and trigger point. Layers are
cumulative: Layer N+1 is meaningless if Layer N fails. L0–L3b mirror the backend 5-layer model one-to-one; L4–L5 are
UI-specific extensions (visual/a11y, performance).

```
Layer 0:   Contract Alignment         (OpenAPI ↔ TS types ↔ fixtures; no network; fast)
Layer 1:   Schema Robustness          (pure fns, hooks, validators, formatters; no DOM; fast)
Layer 1.5: Component / Widget Harness (one widget + mocked data-context; no route; fast–medium)
Layer 2:   Infrastructure Verify      (every route 200, no console errors, auth/redirects)
Layer 3a:  Playbook Specs             (canonical click paths × persona × environment)
Layer 3b:  Trader Workflow E2E        (strategy flow: select → metrics → execute → history)
Layer 4:   Visual + a11y              (screenshot diffs, axe-core violations — scoped)
Layer 5:   Performance                (bundle size, Lighthouse, TTI — scoped)
```

**Why 8 layers and not 5.** Backend's 5-layer model maps cleanly to UI for the correctness axis (L0–L3b). UI has two
additional quality axes without backend analogues: visual correctness (L4) and user-perceived performance (L5). Those
don't collapse into L3 cleanly — they have different tooling, different baselines, different failure modes — so they get
their own layers.

---

## Layer 0 — Contract Alignment

**Question answered:** Do the OpenAPI spec, TypeScript types, WS channel schemas, webhook schemas, and mock fixtures all
agree about the shape of every endpoint and message?

**What it tests:**

- `lib/types/api-generated.ts` is up to date with `lib/registry/openapi.json`
- Every fixture in `lib/mocks/fixtures/**` parses cleanly through its Zod schema derived from OpenAPI
- Every recorded cassette under `tests/contract/cassettes/**` parses cleanly through the same Zod schema
- Every WS channel consumed by the UI has a typed schema in `lib/registry/ws-channels.ts`; recorded WS sessions replay
  cleanly through their Zod schema
- Every webhook payload the UI receives (alerts, notifications, execution callbacks) has a typed schema; recorded
  payloads replay cleanly
- Breaking changes to any of the above fail fast with a diff and a changelog entry

**Where it lives:**

- `tests/contract/test_openapi_type_alignment.spec.ts` — TS types ↔ OpenAPI
- `tests/contract/test_fixture_schema_alignment.spec.ts` — fixtures ↔ Zod (HTTP)
- `tests/contract/test_cassette_schema_alignment.spec.ts` — cassettes ↔ Zod (HTTP, when live backend lands)
- `tests/contract/test_ws_channel_alignment.spec.ts` — recorded WS sessions ↔ Zod channel schemas
- `tests/contract/test_webhook_payload_alignment.spec.ts` — recorded webhook payloads ↔ Zod schemas
- `tests/contract/cassettes/` — recorded staging HTTP responses
- `tests/contract/ws-sessions/` — recorded WS sessions (JSONL per channel)
- `tests/contract/webhook-payloads/` — recorded webhook POST bodies

**Tier:** UI repo owns this layer. Cassette + recording ownership mirrors backend:
[`02-data/vcr-cassette-ownership.md`](../02-data/vcr-cassette-ownership.md) — UI records from staging, commits
recordings, L0 replays against Zod, no duplicates.

**Credentials needed:** None (hermetic replay).

**Trigger:** Pre-commit on changes to `lib/registry/openapi.json`, `lib/types/api-generated.ts`,
`lib/registry/ws-channels.ts`, `lib/mocks/fixtures/**`, `tests/contract/**`. CI on every PR.

**Naming alignment rule (applies to HTTP, WS, and webhook schemas equally):**

Backend has 40+ repos with Pydantic + SQLAlchemy + GCS + PubSub schemas coupled to snake_case wire names. The UI fast
path (live data-contexts, stream handlers, render-hot hooks) uses **backend wire-shape names verbatim** — no conversion,
no renaming. The slow path (form submit, one-shot mutations) may use a mapping adapter in
`lib/api/adapters/<service>.ts`. User-facing labels come from `ui-reference-data.json` generated by
[`unified-api-contracts/scripts/generate_ui_reference_data.py`](../../../unified-api-contracts/scripts/generate_ui_reference_data.py).

**Rename policy (applied during the Phase 3 naming audit):**

- If a field is referenced in **≥5 places** in the UI, rename UI usage to match backend wire-shape. Zero runtime
  conversion cost; better grep-ability across the boundary.
- If a field is referenced in **<5 places**, decide per-field. Rename if convenient; otherwise map in the adapter.
- This applies uniformly to HTTP response fields, WS message fields, and webhook payload fields. WS is the hottest path
  of the three; zero-conversion matters most there.

**Same-repo backend future:** When FastAPI ships in the same repo, the pipeline becomes:

```
pytest backend/  →  regen openapi.json + ws-channels.json  →  openapi-typescript regen  →
L0 contract diff  →  changelog entry  →  UI consumers update
```

Any OpenAPI or WS-channel change that would break UI consumers fails L0 and blocks the PR until fixtures + TS consumers
update. `scripts/generate-api-changelog.py` diffs the last two `openapi.json` commits (and `ws-channels.json` when it
lands) and writes to `docs/api-changelog.md`. Pydantic ↔ SQLAlchemy alignment remains backend's own L0 (covered by the
backend 5-layer SSOT).

**Implementation pattern (HTTP):**

```typescript
// tests/contract/test_fixture_schema_alignment.spec.ts
import { test, expect } from "vitest";
import { schemaFor } from "@/lib/types/generated-zod";
import positionsFixture from "@/lib/mocks/fixtures/positions.json";

test("positions fixture matches OpenAPI schema", () => {
  const schema = schemaFor("GET /api/positions");
  expect(() => schema.parse(positionsFixture)).not.toThrow();
});
```

**Implementation pattern (WS):**

```typescript
// tests/contract/test_ws_channel_alignment.spec.ts
import { test, expect } from "vitest";
import { channelSchema } from "@/lib/registry/ws-channels";
import { readSession } from "./helpers/read-ws-session";

test("market-ticks channel messages match registered schema", () => {
  const schema = channelSchema("market-ticks");
  for (const msg of readSession("tests/contract/ws-sessions/market-ticks.jsonl")) {
    expect(() => schema.parse(msg)).not.toThrow();
  }
});
```

**What's out of scope for UI L0:**

- Asserting that PubSub actually delivers messages end-to-end — that's the backend [e2e-testing](../../../e2e-testing)
  pipeline (real GCS, real Pub/Sub, 11 local service processes). UI L0 only asserts message shape on arrival.
- Asserting that backend actually POSTs webhooks — backend's concern.

---

## Layer 1 — Schema Robustness (Unit)

**Question answered:** Do pure functions, hooks, form validators, and reducers fail fast on bad input and handle
optional fields correctly?

**What it tests:**

- Formatters (currency, date, percentage) handle edge cases (NaN, negative, extreme values, missing locale)
- Hooks with reducers or internal state transitions behave correctly under all input paths
- Zod form schemas reject invalid input and produce actionable error messages
- Route guards correctly allow/deny based on persona + entitlement + lock_state
- Email template rendering produces the expected payload shape for Resend

**Where it lives:**

- `tests/unit/**/*.test.ts` — colocated by module (`tests/unit/hooks/`, `tests/unit/formatters/`, etc.)

**Credentials needed:** None.

**Run command:**

```bash
CI=true npm test -- --run tests/unit/
```

**Trigger:** Pre-commit on changed files (affected tests via Vitest's `--changed`). CI full on every PR.

**Pool configuration:** `pool: "forks"` per workspace UI rule — threads leak zombie node processes in this stack.

**Implementation pattern:**

```typescript
// tests/unit/formatters/format-currency.test.ts
import { describe, it, expect } from "vitest";
import { formatCurrency } from "@/lib/reference-data";

describe("formatCurrency", () => {
  it("handles zero", () => expect(formatCurrency(0)).toBe("0.00"));
  it("handles negative", () => expect(formatCurrency(-1234.5)).toBe("-1,234.50"));
  it("handles NaN without throwing", () => expect(formatCurrency(NaN)).toBe("—"));
  it("handles extreme magnitudes", () => expect(formatCurrency(1e12)).toBe("1,000,000,000,000.00"));
});
```

---

## Layer 1.5 — Component / Widget Harness

**Question answered:** Does this widget, rendered in isolation with a mocked data-context, correctly produce its UI and
respond to user interaction?

**What it tests:**

- Widget mounts with mocked provider values and renders expected structure
- Button enable/disable reacts to input correctly
- Input changes propagate to the expected output field (e.g., amount → expected-output preview)
- Edge cases: empty state, loading state, error state
- No live routes, no multi-widget layouts, no navigation

**Where it lives:**

- `tests/widgets/**/*.test.tsx` — one file per widget in `components/widgets/widget-registry.ts`

**Tooling (split by need, not dogma):**

| Widget type                                          | Tool                                                       | Why                                                                           |
| ---------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Pure data display, formatters, forms, reducers       | Vitest + happy-dom                                         | 10× faster than a browser; jsdom-shape is sufficient                          |
| Drag/drop, scroll virtualization, chart interactions | Playwright component (`@playwright/experimental-ct-react`) | Real browser fidelity; jsdom can't fake `scrollTop`, `ResizeObserver`, canvas |

**Credentials needed:** None (data-contexts are mocked; no network).

**Run commands:**

```bash
# fast — Vitest
CI=true npm test -- --run tests/widgets/

# browser — Playwright component (opt-in per widget)
npx playwright test --project=widgets-ct
```

**Trigger:** Last local gate in quickmerge. CI on every PR.

**NOT in scope for L1.5:**

- Real routes (→ L2)
- Multi-widget data-context wiring across pages (→ L3)
- Live APIs or cassettes (→ L0 covers schema shape; L3b covers end-to-end flow)

**Hermeticity:** Playwright component specs MUST run with `page.route('**', route => route.abort())` for all non-asset
requests. Any widget attempting a real fetch fails the test — forces the widget to consume its data-context, not hit the
network directly.

**WebSocket widgets:** Widgets that consume live WS feeds (via `useWebSocket`, `useSportsLiveUpdates`, or similar) get a
mocked WS global in their L1.5 harness. Assertions: subscribe/unsubscribe payload shape, reconnect on close,
disabled-in-mock-mode behavior ([hooks/use-websocket.ts](../../../unified-trading-system-ui/hooks/use-websocket.ts) —
`isMockDataMode()` currently disables the connection; the harness asserts this). Use the recorded session files from
`tests/contract/ws-sessions/` as the message stream the mock WS pushes to the widget.

**Implementation pattern (Vitest):**

```typescript
// tests/widgets/orders/orders-kpi-strip.test.tsx
import { render, screen } from "@testing-library/react";
import { OrdersDataContext } from "@/components/widgets/orders/orders-data-context";
import { OrdersKpiStripWidget } from "@/components/widgets/orders/orders-kpi-strip-widget";

test("renders all six KPI metrics from mocked context", () => {
  const value = { summary: { total: 10, open: 3, partial: 1, filled: 5, rejected: 0, failed: 1 }, isLoading: false, error: null };
  render(
    <OrdersDataContext.Provider value={value}>
      <OrdersKpiStripWidget />
    </OrdersDataContext.Provider>,
  );
  expect(screen.getByText("Total Orders")).toBeInTheDocument();
  expect(screen.getByText("10")).toBeInTheDocument();
});
```

**Coverage gate:** Every widget registered in `components/widgets/widget-registry.ts` MUST have at least one L1.5 spec.
CI grep-coverage enforces: for each entry in the registry, a matching file under `tests/widgets/` must exist.

---

## Layer 2 — Infrastructure Verify (Route Smoke)

**Question answered:** Does every route in the deployed UI load without error, mount its primary content, and enforce
the right auth/redirect behavior?

**What it tests:**

- Every route in `app/**` returns HTTP 200 (or the correct auth redirect)
- Zero console errors / unhandled rejections on load
- Primary `data-testid` for the route mounts within the timeout
- Middleware redirects work (unauth → login, locked → padlock, etc.)
- Static assets resolve (no 404 on images, CSS, fonts)

**Where it lives:**

- `tests/smoke/routes.spec.ts` — parametrised over the route manifest
- `tests/smoke/redirects.spec.ts` — auth + lock redirects

**Tooling:** Playwright `chromium` project (route smoke files live under `tests/smoke/**` and are picked up
automatically). Headless, single worker, aggressive timeout (5s per route). See
[Playwright Projects](#playwright-projects) below.

**WebSocket + webhook smoke (post-deploy staging only):**

- Open each WS channel the UI consumes; assert connection event within 3s, disconnect cleanly.
- If backend emits webhooks to UI callbacks, hit the callback endpoint with a recorded payload; assert 2xx.
- These smokes only run in the `staging` project — they need real endpoints.

**Credentials needed:**

- **Local / pre-push:** none (`NEXT_PUBLIC_MOCK_API=true`)
- **Staging post-deploy:** staging Firebase / test persona seeds

**Trigger:**

- Pre-push gate on `feat/*` branches
- CI on every PR (mock mode)
- Post-deploy on staging (live mode) — the UI equivalent of backend's L2

**Implementation pattern:**

```typescript
// tests/smoke/routes.spec.ts
import { test, expect } from "@playwright/test";
import { ROUTES } from "@/lib/registry/route-manifest";

for (const route of ROUTES) {
  test(`${route.path} loads without console errors`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    await page.goto(route.path);
    await expect(page.getByTestId(route.rootTestId)).toBeVisible();
    expect(errors).toEqual([]);
  });
}
```

**Coverage gate:** Every route in `app/**` MUST appear in `lib/registry/route-manifest.ts`. CI fails if a new route is
added without a manifest entry.

---

## Layer 3a — Playbook Specs

**Question answered:** Does the canonical click path for each playbook work correctly for each persona, with visibility
slicing applied?

This layer already has an SSOT at [`14-customer-journeys/testing/README.md`](../14-customer-journeys/testing/README.md).
This section delegates — do not duplicate. The rule from that SSOT stands:

> When a playbook doc changes, the matching Playwright spec MUST be updated in the same PR.

**Where it lives:** `tests/playbooks/**` in `unified-trading-system-ui`.

**Credentials needed:** Local tier 0 always; local tier 1 when backend-dependent; staging manual (pre-Firebase).

**Trigger:** CI on every PR; staging manual post-deploy.

See the playbook testing SSOT for scaffolding helpers (`seed-persona.ts`, `expect-service-tile-locked.ts`,
`expect-click-path.ts`) and the playbook × persona × environment test matrix.

---

## Layer 3b — Trader Workflow E2E

**Question answered:** Can a trader execute a given strategy end-to-end without the UI breaking?

**What it tests:**

One spec per strategy, following the SSOT canonical instruction sequence from
[`09-strategy/architecture-v2/`](../09-strategy/). Each spec simulates exactly what a trader does manually:

1. Navigate to the strategy route
2. Select protocol / asset / operation
3. Verify all relevant metrics appear (APY, health factor, cost of carry, net APY, expected output, etc.)
4. Enter trade amount
5. Click Execute
6. Verify the trade appears in the trade history table
7. For multi-leg strategies (STAKE → PLEDGE → BORROW → SHORT PERP), repeat steps 2–6 per leg

**What does NOT belong here** (push to L1 or L1.5 instead):

- Button enable/disable state checks → L1.5
- Reactive input / output-updates-when-amount-changes → L1.5
- Slippage option counts, combobox open/close → L1.5
- Strict-mode / accessibility correctness → L4

**Where it lives:**

- `tests/e2e/strategies/defi/**` — DeFi strategies (active)
- `tests/e2e/strategies/cefi/**` — CeFi strategies (when the phase starts)

**Tooling:** Playwright `chromium` (CI) and `human` (demo / manual review). The `human` project uses slow-motion +
`demoHighlight()` for visual feedback.

**Credentials needed:** Mock in CI; staging for demo runs.

**Trigger:** CI nightly; manual on demand for demos.

**Spec template:**

```
beforeAll: navigate to route, seed auth, dismiss overlays, wait for root widget
afterAll: close page

test("baseline — all panels visible before entry"): assert widget root, metric panels, execute disabled
test("leg 1 — [OPERATION] [ASSET]"): fill amount → assert expected output → assert key metric → execute → assert trade row
test("leg 2 — [OPERATION]"): (if multi-leg)
test("leg N — [OPERATION]"): (if multi-leg)
test("metric gap discovery"): assert any additional panels the trader would check
```

**Secondary purpose — gap discovery.** Running `--project=human` on a strategy spec should reveal missing input fields,
missing metric panels, missing trade history columns, or backend gaps (execute → no row = ledger not connected). Gaps
get filed as issues or added to `docs/audits/e2e-strategy-tests-ssot-alignment.md`.

---

## Layer 4 — Visual + Accessibility

**Question answered:** Did a UI change introduce a visual regression or an a11y violation?

**What it tests:**

- **Visual (scoped):** screenshot diffs for marketing pages + 5 key dashboard states (trader home, strategy detail,
  reports, deployment, admin). Full-app visual regression is flaky-tax heavy; start narrow, expand if we actually catch
  bugs.
- **a11y (full coverage):** `@axe-core/playwright` run on every route in the L2 smoke. Zero critical / serious
  violations tolerated; moderate + minor tracked with a backlog.

**Where it lives:**

- `tests/visual/*.spec.ts` — screenshot diffs, co-located with the route smoke
- `tests/smoke/routes.spec.ts` — a11y runs inline on the same L2 page loads (no duplicate navigation cost)

**Tooling:** Playwright screenshot comparison; `@axe-core/playwright` for a11y.

**Baseline policy:** Screenshots are baselined on `main` after a successful green CI. PR diffs are compared against the
last green baseline; the baseline updates only on merge to `main`.

**Credentials needed:** None (mock mode).

**Trigger:** CI on every PR; baseline refresh on merge to `main`.

**Expansion policy:** Add a visual spec ONLY when a change causes a visible regression that the existing layers missed.
Do not prophylactically add screenshots.

---

## Layer 5 — Performance

**Question answered:** Is the UI getting slower or heavier over time?

**What it tests:**

- **Bundle size budget** per route chunk (fail the build if a route exceeds its budget)
- **Lighthouse CI** on marketing pages (SEO matters) and one representative dashboard page
- **TTI baseline** on the trader landing page

**Where it lives:**

- `lighthouserc.js` — budgets per route
- `scripts/ci/check-bundle-budget.ts` — post-build gate
- `tests/perf/` — custom perf assertions (rare)

**Tooling:** Lighthouse CI GitHub Action; `next build` bundle analyzer; `@playwright/test` trace for custom perf.

**Credentials needed:** None.

**Trigger:** Every PR (bundle budget); weekly cron (Lighthouse). Failing bundle budget blocks the PR; Lighthouse
regressions open an issue, do not block.

---

## When Each Layer Runs

All triggers below run on every branch. What differs is **whether a failure blocks** — see
[Gate Enforcement by Branch](#gate-enforcement-by-branch) below. Entries in the "Blocks on main merge" column describe
the gate's behavior at main-merge quality gates; on `feat/*` branches the same gate emits a warning and does not block.

| Layer             | Trigger                                     | In quickmerge?        | Credentials      | Blocks on main merge             |
| ----------------- | ------------------------------------------- | --------------------- | ---------------- | -------------------------------- |
| 0                 | Pre-commit on openapi/types/fixtures change | Yes                   | None             | Main merge gate                  |
| 1                 | Pre-commit on changed files; CI PR          | Yes (last local gate) | None             | Main merge gate                  |
| 1.5               | Quickmerge last local gate; CI PR           | Yes                   | None             | Main merge gate                  |
| 2 (pre-push / PR) | Pre-push on `feat/*`; CI PR                 | Yes (pre-push)        | None (mock mode) | Main merge gate                  |
| 2 (post-deploy)   | Staging deploy trigger                      | No                    | Staging creds    | "Deployment healthy" status      |
| 3a                | CI PR; staging manual                       | Yes (mock mode)       | None in CI       | Main merge gate                  |
| 3b                | CI nightly; manual demo                     | No                    | None in CI       | Nightly green; release readiness |
| 4                 | CI PR (a11y blocking; visual non-blocking)  | Yes (a11y)            | None             | Main merge gate (a11y only)      |
| 5                 | PR (bundle); weekly cron (Lighthouse)       | Yes (bundle)          | None             | Main merge gate (bundle only)    |

---

## Gate Enforcement by Branch

Mirrors the three-tier branch model from
[`workspace-workflow.md`](../../../.claude/rules/workspace-workflow.md#quickmerge-mandatory-for-all-merges): `feat/*` →
QG only, `staging` → convergence for breaking changes, `main` → always stable. UI is in early development and iterates
rapidly; failures on feature branches must not slow down the inner loop, but main must stay green.

| Branch              | Policy                                                                                               | Rationale                                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `feat/*`            | All layers run. Failures emit **warnings** in CI output and pre-commit hooks; **do NOT block** push. | Early-development UI; rapid iteration matters more than gate purity. Developer sees warnings and fixes inline. |
| `staging` (adopted) | All layers run. Failures on L0, L1, L1.5, L2 pre-deploy **block** the merge.                         | Staging is the convergence branch for breaking changes; must stay deployable.                                  |
| `main`              | All layers run via quality gates. **Any layer failure blocks the merge.**                            | Main is always stable — this is the contract with downstream consumers.                                        |

**Operational notes:**

- The same CI job runs on every branch; only the **exit code** differs. A single `GATE_MODE={warn,block}` env var
  inferred from the branch name controls behavior.
- Pre-commit hooks on feature branches print warnings but exit 0. Use `GATE_MODE=block` locally to simulate the main
  merge gate before opening a PR.
- Flaky tests are a separate concern from this policy — zero-tolerance, `test.fixme` + issue, same as the playbook
  testing SSOT. A flaky test is not a "warn me on feat/\*" problem; it's a fix-or-remove problem.
- When backend changes break UI L0 (OpenAPI drift), this policy still applies: backend's PR to UI appears as a `feat/*`
  branch with L0 warnings; merge to main requires UI consumers to be updated in the same PR.

**What never warns, always blocks — even on `feat/*`:**

- TypeScript compile errors (`tsc --noEmit`) — un-stub at
  [package.json:20-23](../../../unified-trading-system-ui/package.json); a broken compile is not a warning condition.
- ESLint **errors** (not warnings) — same rationale.
- Test failures in tests that actually ran the code under change — "my L1 test for the hook I just wrote fails" is not a
  "warn me later" situation.

The distinction: gates that check _the whole surface_ (every widget, every route, every fixture) warn-only on feat/\*;
gates that check _what you just touched_ still block.

---

## Playwright Projects

Three top-level projects. Test-file location inside `tests/` determines which project picks a spec up — no opt-in flags,
no `--project` juggling for day-to-day runs.

| Project    | Picks up                                                                   | Mode                        | Purpose                                                            |
| ---------- | -------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------ |
| `chromium` | `tests/smoke/**`, `tests/widgets/**`, `tests/playbooks/**`, `tests/e2e/**` | `NEXT_PUBLIC_MOCK_API=true` | Default CI PR gate. Runs every layer that doesn't need live infra. |
| `staging`  | `tests/smoke/**`, `tests/e2e/strategies/**`                                | Live APIs                   | Post-deploy staging gate. The only project that hits real backend. |
| `human`    | `tests/e2e/strategies/**`                                                  | Mock or staging             | Demo / manual review. Slow-motion + `demoHighlight()` visual aid.  |

**Sub-configs inside `chromium`** (not separate top-level projects):

- Widget component tests (`@playwright/experimental-ct-react`) — picked up via file naming `*.ct.spec.tsx` inside
  `tests/widgets/`. Most widgets stay on Vitest (see L1.5); `.ct.spec.tsx` is opt-in per widget for browser-specific
  behavior.
- Visual regression screenshots — `tests/visual/*.spec.ts` under the same project, Playwright native screenshots with
  baselines committed to `tests/visual/__screenshots__/`.
- a11y assertions — inline in `tests/smoke/routes.spec.ts` via `@axe-core/playwright`, not a separate project.

**Why three and not seven:** each top-level project costs CI minutes and dev onboarding complexity. The three we have
represent three genuinely different execution environments (mock, staging, demo). Everything else is organizational and
lives inside `chromium` via file paths.

---

## Credential Hermeticity Rule

Mirrors backend's `CLOUD_MOCK_MODE=true` + `--block-network` rule.

- **L0, L1, L1.5, L2 (pre-deploy), L3a (CI), L4, L5** MUST pass with `NEXT_PUBLIC_MOCK_API=true` and no outbound network
  calls.
- Playwright specs enforce this with
  `page.route('**', route => { if (isExternal(route.request().url())) route.abort(); else route.continue(); })`.
- Tests connecting to local emulators (e.g., a Resend dev inbox) use an explicit opt-in fixture with a comment
  explaining why.
- **L2 (post-deploy)** and **L3b on staging** are the only layers allowed to hit live APIs.

---

## Mock → Live Data Transition

**Today (2026-04):** `NEXT_PUBLIC_MOCK_API=true` everywhere. All hooks serve from `lib/mocks/fixtures/**` seeded by
`lib/config/services/*.config.ts` constants.

**Intermediate (per-service migration):**

```
NEXT_PUBLIC_USE_LIVE_API="orders,positions"
```

Hooks check the allowlist. An endpoint in the list uses the real fetcher; anything else falls back to fixtures. This
lets us migrate one endpoint at a time without flag soup, and L3b specs can re-run against a partially-live backend with
`NEXT_PUBLIC_USE_LIVE_API=orders` to isolate which endpoint broke.

**Staging:** everything live. L2 + L3b run against the real backend as `staging-smoke` and `staging-workflow` jobs.

**Prod:** no automated tests. Admin smoke only, matching backend policy.

**Staging data provenance:** staging's backend data is seeded by the [e2e-testing](../../../e2e-testing) live pipeline
(real GCS, real Pub/Sub, 11 local service processes). UI L3b on staging reads whatever that pipeline wrote. The UI repo
does not integrate with `e2e-testing` directly — it just consumes the data that lands in staging as a result.

**Cassette flow** (from live → hermetic):

1. On staging deploy, a nightly `scripts/record-cassettes.ts` runs a scripted session against the live staging backend
   with Playwright request-interception capture (HTTP) and WS frame capture (JSONL per channel).
2. HTTP cassettes written to `tests/contract/cassettes/<endpoint>.json`; WS sessions to
   `tests/contract/ws-sessions/<channel>.jsonl`; webhook payloads to `tests/contract/webhook-payloads/<event>.json`.
   Committed via PR, mirrors backend VCR flow.
3. L0 replays all three against Zod on every PR — no credentials, no network.
4. Fixtures under `lib/mocks/fixtures/` regenerate from the same recordings via a codegen script, guaranteeing
   mock-shape parity with live.

**No duplicates.** Recording is SSOT; fixture is derived. Do not hand-edit fixtures after the recording flow lands.

---

## Same-Repo Backend Integration (when applicable)

When FastAPI ships in the same repo as the UI, L0 extends to cover schema drift between backend and UI.

**Flow on backend change:**

```
backend code changes  →  pytest backend/ (backend L0–L1.5)  →  regen openapi.json  →
openapi-typescript regen  →  L0 contract diff  →  changelog entry  →  UI consumers update
```

**What each tool owns:**

- `pytest` — Pydantic ↔ SQLAlchemy alignment, per backend's existing L0
- `openapi-typescript` — OpenAPI → TS type regen
- `scripts/generate-api-changelog.py` — diffs the last two `openapi.json` commits, writes to `docs/api-changelog.md`
- `tests/contract/` — TS types ↔ OpenAPI ↔ fixtures ↔ cassettes

**Gate:** a backend commit that changes OpenAPI in a way that breaks UI consumers fails L0 on the UI side. The PR is
blocked until the UI is updated in the same PR (monorepo pattern).

---

## Coverage Gates

Extends the rule from [`14-customer-journeys/testing/README.md`](../14-customer-journeys/testing/README.md) ("every
playbook doc has a matching spec"):

| Coverage requirement                                                | Where enforced                                                           |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| Every playbook doc has a matching L3a spec                          | Grep check in pre-commit: doc name → expected spec file (existing)       |
| Every widget in `widget-registry.ts` has an L1.5 harness spec       | Grep check in pre-commit: registry entry → `tests/widgets/<id>.test.tsx` |
| Every hook in `hooks/api/` has an L1 unit test                      | Grep check: `hooks/api/use-X.ts` → `tests/unit/hooks/use-X.test.ts`      |
| Every route in `app/**` appears in `lib/registry/route-manifest.ts` | Next.js build plugin fails if a route page is missing from the manifest  |
| Every endpoint in `openapi.json` has a fixture + L0 schema pair     | CI fails if `openapi.paths` has keys with no matching fixture + Zod      |
| Every endpoint in `openapi.json` has a cassette (when live)         | CI warn (first 30 days), CI fail thereafter — same ramp as backend VCR   |

---

## Fast-Iteration Loop

Matches backend's two-pass agent model (`--agent` quickmerge) at the UI layer.

**Inner loop (seconds):**

- `npm run dev` with hot reload
- IDE LSP typecheck on save (un-stub of `package.json:20`)
- `npm run test:watch` running Vitest on affected tests only

**Pre-push (minutes):**

```bash
bash scripts/quickmerge.sh "feat: ..."
```

Runs L0 + L1 + L1.5 + L2 pre-deploy (mock mode). On `feat/*`, gate failures emit warnings and do NOT block push — see
[Gate Enforcement by Branch](#gate-enforcement-by-branch). On merge to `main`, the same gates block.

**Agent shortcut:**

```bash
bash scripts/quickmerge.sh "feat: ..." --agent
```

Skips L2 locally (CI re-runs it). Matches backend `--agent` flag semantics.

**CI (PR on `feat/*`):** L0 + L1 + L1.5 + L2 + L3a + L4 a11y + L5 bundle. Warnings only (annotations on the PR); does
not block the PR from landing on the feature branch.

**CI (merge to `main`):** Same layers. **Blocking** — red gate prevents the merge.

**CI (nightly on `main`):** L3b + L4 visual baseline refresh + L5 Lighthouse. Non-blocking to PRs; alerts on regression
open an issue.

**Flaky tests:** zero-tolerance. Isolate with `test.fixme`, file an issue, fix within the sprint. Matches the rule in
the playbook testing SSOT.

---

## Testing Ownership by Surface

UI repo owns all layers. The surface split determines which layers apply most heavily.

| Surface            | L0  | L1  | L1.5 | L2  | L3a | L3b | L4  | L5  |
| ------------------ | --- | --- | ---- | --- | --- | --- | --- | --- |
| Marketing / public | —   | ✓   | —    | ✓   | ✓   | —   | ✓   | ✓   |
| Auth / email       | ✓   | ✓   | ✓    | ✓   | ✓   | —   | —   | —   |
| Onboarding         | ✓   | ✓   | ✓    | ✓   | ✓   | —   | —   | —   |
| Dashboard shell    | —   | ✓   | ✓    | ✓   | ✓   | —   | ✓   | ✓   |
| Trading widgets    | ✓   | ✓   | ✓    | ✓   | —   | ✓   | —   | —   |
| Deployment UI      | ✓   | ✓   | ✓    | ✓   | ✓   | —   | —   | —   |

- Marketing has no L0 because it consumes no backend APIs today (it's a questionnaire + static pages + Resend).
- **Deployment UI is a separate React Router + Vite app (`deployment-ui`), not the Next.js `app/**` this doc's L2/L3a
  examples above are written against** — its own `tests/smoke/*.spec.ts` + `playwright.config.ts` + a frontend-side
  `mock-api.ts` (no route-manifest.ts, no `NEXT_PUBLIC_MOCK_API`). `deployment-ui/tests/smoke/alerts-page.spec.ts` is a
  canonical example of the pattern: URL-backed filter/sort/date-range state asserted via `page.goto` + `getByTestId`
  against the Vite dev server, mock data fixed in `mock-api.ts` rather than cassettes — see
  [ci-alerting.md](../04-architecture/ci-alerting.md) § "The `/alerts` page UI contract" for the feature-level detail.
- L3a = playbook/persona flows; applies to user-journey surfaces (marketing, auth, onboarding, dashboard shell).
- L3b = trader strategy workflows; applies only to the trading surface.
- L4 visual is scoped to marketing + dashboard shell (where layout regressions are most visible to external users).
- L5 perf is scoped to the same surfaces — marketing for SEO, dashboard shell for TTI.

---

## Ordering in the Plan

```
Phase 1 — foundation gates (un-stub + L0 skeleton)
  - Un-stub typecheck + lint (remove `|| true` from package.json)
  - Create tests/contract/ skeleton with first fixture ↔ Zod pair (positions, as pilot)
  - Create tests/widgets/ skeleton with first L1.5 (defi-lending-widget, as pilot)
  - Land route-manifest.ts and L2 route smoke

Phase 2 — widget harness rollout
  - L1.5 spec per widget in the registry (~125 widgets)
  - Coverage gate: grep check enforcing registry ↔ spec pairing

Phase 3 — contract + cassette pipeline + naming alignment
  - 3a. Drift gate: unified-api-contracts/openapi/*.json is SSOT; UI pulls via scripts/sync-openapi.ts; L0 fails on diff
  - 3b. Fast-path naming audit: scripts/audit-field-naming.ts walks hooks + widgets, diffs field references against
        OpenAPI keys with use-counts, emits docs/audits/naming-alignment.md. ≥5 places → rename to wire-shape;
        <5 places → per-field decision. Applies uniformly to HTTP, WS, webhook field names.
  - 3c. Mapping layer (slow path only): lib/api/adapters/<service>.ts for form → request body and response → UI shape
        on slow-path mutations. Fast-path hooks return wire-shape directly (no mapping).
  - 3d. Changelog automation: scripts/generate-api-changelog.py diffs openapi.json + ws-channels.json commits, writes
        docs/api-changelog.md. PR template seeds its "API impact" section from this.
  - 3e. Cassette + WS session + webhook payload recording against staging; fixtures regenerate from recordings
  - 3f. Same-repo backend future (if/when it lands): pytest backend/ → regen openapi.json → openapi-typescript →
        L0 diff → UI consumers update in the same PR. See Same-Repo Backend Integration section.

Phase 4 — visual + perf
  - Baseline marketing + 5 dashboard screenshots
  - Lighthouse CI on marketing
  - Bundle budget per route

Phase 5 — staging smoke + release readiness
  - staging-smoke job (post-deploy L2 + L3b)
  - Release-readiness gate (all layers green on last 3 nightly runs)
```

---

## Plan-Level Enforcement (codified 2026-05-23)

This document defines **what** each layer tests and **when** it runs. The plan-level enforcement — what must be true
before a plan todo can be ticked done — lives in `plans/PLAN_FORMAT.md` § 9 (UI Verification Gate). The two documents
compose:

| Layer(s) that changed | Required regression guard location                  | Plan-tick evidence tag            |
| --------------------- | --------------------------------------------------- | --------------------------------- |
| L1.5 (widget)         | `tests/widgets/<widget-id>.test.tsx`                | `regression: tests/widgets/...`   |
| L2 (route smoke)      | `tests/smoke/routes.spec.ts` or `redirects.spec.ts` | `regression: tests/smoke/...`     |
| L3a (playbook)        | `tests/playbooks/<flow>.spec.ts`                    | `regression: tests/playbooks/...` |
| L3b (trader workflow) | `tests/e2e/strategies/<archetype>.spec.ts`          | `regression: tests/e2e/...`       |
| L4 (visual/a11y)      | `tests/visual/<component>.spec.ts`                  | `regression: tests/visual/...`    |

**The mandatory ✅ tick evidence format:**

```markdown
- [x] ✅ [AGENT][UI] P1. <description> — <repo>@<sha> | pw:L2 ✓ | regression: <spec-path>
```

**`pw:L2 ✓`** means `npx playwright test --project=chromium tests/smoke/` exited 0 in the agent's local environment. If
the agent cannot run a dev server, the todo stays `- [ ] [BLOCKED-PLAYWRIGHT]` until a slot with UI access verifies.

Any plan todo for a UI repo that is ticked `✅` without `pw:` + `regression:` evidence is **review-blocking**. Agents
and reviewers MUST enforce this — it is equivalent in weight to the `docs(plans):` flip rule.

**Quick cross-check checklist before ticking any UI todo done:**

1. `- [ ]` My change is in `unified-trading-system-ui/`, `deployment-ui/`, or `user-management-ui/`? → Must add `[UI]`
   to role tag.
2. `- [ ]` Did I run `npx playwright test --project=chromium tests/smoke/` and it exited 0? → Append `pw:L2 ✓`.
3. `- [ ]` Did I write or update a spec that would catch reverting my change? → Append
   `regression: tests/<layer>/<spec>.ts`.
4. `- [ ]` Is the spec path real and the assertions non-vacuous? → Reviewer will read the diff.

---

## References

- **Backend SSOT (mirror target):** [`06-coding-standards/integration-testing-layers.md`](integration-testing-layers.md)
- **Playbook testing (L3a):** [`14-customer-journeys/testing/README.md`](../14-customer-journeys/testing/README.md),
  [`14-customer-journeys/testing/test-matrix.md`](../14-customer-journeys/testing/test-matrix.md)
- **VCR cassette policy (cassette ownership rule):**
  [`02-data/vcr-cassette-ownership.md`](../02-data/vcr-cassette-ownership.md)
- **UI functionality + API wiring:**
  [`05-infrastructure/ui-functionality-requirements.md`](../05-infrastructure/ui-functionality-requirements.md)
- **Workspace UI rule:** `.claude/rules/ui.md`
- **Strategy testing coverage plan:** `unified-trading-pm/plans/ai/ui_e2e_strategy_coverage_audit_2026_04_22.plan.md`
