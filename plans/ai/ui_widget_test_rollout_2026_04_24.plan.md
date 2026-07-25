---
name: ui-widget-test-rollout
overview:
  Scale UI test coverage across stable widgets following the 8-layer SSOT. Pilot a pattern on defi-lending, roll out in
  waves by product focus (DeFi first), skip fragile/in-dev surfaces (predictions, sports, CeFi) until their backends are
  live.
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none

ssot:
  - /codex/06-coding-standards/ui-testing-layers.md
  - /codex/06-coding-standards/integration-testing-layers.md
  - /codex/14-customer-journeys/testing/README.md
  - unified-trading-system-ui/docs/manifest/widget-certification/*.json
---

# UI widget test rollout — scale L1/L1.5 coverage on stable widgets

## Context

- **Testing SSOT**: `/codex/06-coding-standards/ui-testing-layers.md` — 8-layer model (L0–L5), branch-tier gate policy
  (feat warn, main block), hermeticity rule, naming alignment rule.
- **Widget cert**: `unified-trading-system-ui/docs/manifest/widget-certification/*.json` — 115 widgets, 9 cert levels
  (L0–L8). Cert L6 "Tested" is null for all widgets. This plan fills cert L6.
- **Readiness signal**: cert L0 + L1 + L7 all `pass` means the widget is stable enough for L1.5 harness tests
  (rendering + basic interaction). L3/L4/L5 partials are fine — those are human-verification gates for execute flow, not
  rendering.
- **Readiness distribution** (as of 2026-04-24):
  - 107 / 115 widgets pass L0+L1+L7
  - DeFi: 15/17 ready (live-defi-rollout branch is current product focus)
  - Common trading tabs: ~21 ready (orders, positions, trades, book, pnl, alerts, overview, accounts)
  - **Deferred domains**: predictions (11), sports (9), some CeFi — backend still fluid
- **Foundation debt**:
  - `package.json:20-23` — typecheck + lint stubbed with `|| true`
  - 19 TS errors across 5 files (mostly missing Firebase Admin types)
  - 89 lint errors + 350 warnings

## Decisions locked in (plan-mode Q&A, 2026-04-24)

- **Don't test everything.** Lots of surface is still under active development. Cover only what's stable. User rule:
  "whatever that we have done should be covered properly."
- **Primary target is L1.5 widget harness** (cert L6 fill). Vitest + happy-dom for most widgets; Playwright component
  only for browser-specific behavior (drag, virtualization, canvas).
- **L1 unit tests** for shared formatters/hooks land alongside L1.5 work as opportunistic coverage.
- **Defer** the following until explicitly unblocked:
  - L0 contract pipeline with live backend (cassettes, WS sessions, webhook payloads) — wait for live backend
  - Predictions + sports widget tests — backend contracts fluid
  - CeFi strategy widgets — out of current product focus
  - L4 visual regression — user explicitly deprioritized
  - L5 performance — user explicitly deprioritized
- **Pilot first, scale second.** One widget end-to-end before rolling out to waves. 2–3 hours up front saves refactor
  cost at widget #15.
- **Commit cadence**: one commit per phase completion; `feat/*` branch with `--agent` quickmerge.

## Scope

### In scope (107 candidate widgets)

| Domain       | Ready | Priority | Phase |
| ------------ | ----- | -------- | ----- |
| overview     | 8     | wave 1   | 2     |
| orders       | 2     | wave 1   | 2     |
| positions    | 2     | wave 1   | 2     |
| book         | 3     | wave 1   | 2     |
| pnl          | 3     | wave 1   | 2     |
| alerts       | 3     | wave 1   | 2     |
| accounts     | 5     | wave 1   | 2     |
| defi         | 15    | wave 2   | 3     |
| markets      | 8     | wave 3   | 5     |
| terminal     | 8     | wave 3   | 5     |
| risk         | 13    | wave 4   | 5     |
| options      | 6     | wave 4   | 5     |
| instructions | 3     | wave 4   | 5     |
| strategies   | 9     | wave 4   | 5     |
| bundles      | 1     | wave 4   | 5     |

### Out of scope (explicitly skipped this rollout)

| Domain                                                        | Reason                                                                                    |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| predictions                                                   | Prediction market backend contracts fluid; 11 widgets deferred until stable               |
| sports                                                        | Sports pipeline still mocked; 7 widgets deferred                                          |
| CeFi-specific                                                 | Current product focus is DeFi; CeFi deferred                                              |
| Visual regression (L4)                                        | User deprioritized — "find fast when we have a bug" rather than prophylactic              |
| Performance (L5)                                              | User deprioritized — revisit after waves 1–4                                              |
| L0 cassette replay                                            | Requires live backend + recording pipeline — deferred                                     |
| L3b trader workflow extensions beyond existing strategy specs | Separate plan at `ui_e2e_strategy_coverage_audit_2026_04_22.plan.md` already tracks these |

### Individual widget exclusions

- `positions-trades-table` — cert L0 or L1 not passing (not in READY set)
- `defi-yield-chart`, `defi-atomic-bundle` — cert L0 or L1 not passing
- Any widget whose cert has open `knownIssues` entries blocking L0/L1 — test only after cert fix

## Phases

### Phase 0 — Foundation (blocks all test work)

**Deliverables:**

1. Un-stub `typecheck` in `package.json`:
   ```
   "typecheck": "tsc --noEmit"
   ```
2. Fix all 19 TS errors:
   - Install missing type declarations (`firebase-admin`, `firebase-functions`, `@google-cloud/storage`)
   - Fix `AuthUser.firebase_uid` shape in `lib/auth/`
   - Export `DashboardTileId` from `lib/auth/persona-dashboard-shape`
   - Fix `.ts` extension import in `scripts/orphan-audit.ts`
   - Fix implicit `any` on sort callbacks in `lib/onboarding/doc-store.ts`
3. Un-stub `lint` in `package.json` at errors-only:
   ```
   "lint": "eslint . --max-warnings Infinity"
   ```
4. Fix all 89 lint errors (mostly `react-hooks/set-state-in-effect` — React 19 strict-mode style)
5. Land `GATE_MODE` env var wiring (branch-tier policy): `feat/*` → `warn`, `main` → `block`. Exit-code gated.

**Commit:** `chore(quality): un-stub typecheck + lint, fix TS + lint errors`

**Exit criteria:** `npm run typecheck` exits 0; `npm run lint` exits 0; both wired into `scripts/quickmerge.sh` with
GATE_MODE respected.

### Phase 1 — Pattern pilot (defi-lending)

**Why defi-lending:** richest behavior profile of any ready widget — form inputs, reactive output (health factor
preview), APY calculation, execute button enable/disable on validation, 4 operations (LEND/BORROW/WITHDRAW/REPAY). Cert
`docs/manifest/widget-certification/defi-lending.json` is detailed and green at L0/L1/L7.

**Deliverables:**

1. Establish `tests/widgets/` directory + Vitest config project (`pool: "forks"` per workspace UI rule).
2. Write mock data-context helper pattern in `tests/widgets/_helpers/mock-data-context.tsx` — reusable provider mocker
   for the widget-family data contexts.
3. Write `tests/widgets/defi/defi-lending-widget.test.tsx` — 6–10 tests covering:
   - Renders with mock context (no crash, testid mounts)
   - Operation toggle updates form state
   - Amount input reflects in expected-output preview
   - Execute button disabled when amount is empty/invalid
   - Execute button enabled with valid input
   - Empty state when no protocols (AlertTriangle path from cert L0.7)
   - Loading state propagates to FormWidget (cert L0.6 check)
4. Write `scripts/audit-widget-cert-coverage.ts` — grep-coverage gate:
   - Reads `docs/manifest/widget-certification/*.json`
   - For each cert with L0+L1+L7 pass, asserts a matching test file exists under `tests/widgets/`
   - Fails CI on main with missing tests; warns on feat/\*
5. Update `defi-lending.json` cert L6 to `pass` with `by: "agent+tests"`.

**Commit:** `test(widgets): pilot L1.5 harness for defi-lending, land helper + coverage gate`

**Exit criteria:** pilot test passes in CI; coverage gate script runs; cert L6 updated; pattern documented in
`tests/widgets/README.md` with copy-paste template.

### Phase 2 — Wave 1: Common trading tabs (21 widgets)

Widgets users see every day. Highest test-value-per-hour.

**Widgets:**

- `overview`: alerts-preview, health-grid, kpi-strip, pnl-attribution, pnl-chart, recent-fills, scope-summary,
  strategy-table
- `orders`: orders-kpi-strip, orders-table
- `positions`: positions-kpi-strip, positions-table
- `book`: book-hierarchy-bar, book-order-entry, book-trade-history
- `pnl`: pnl-factor-drilldown, pnl-time-series, pnl-waterfall
- `alerts`: alerts-kill-switch, alerts-kpi-strip, alerts-table

**Deliverables:**

1. One `tests/widgets/<domain>/<widget-id>.test.tsx` per widget. Each file ~6–10 tests covering render + primary
   interactions from cert L0/L1/L4 checks.
2. Shared data-context mocks for each family (`_helpers/mock-orders-context.tsx`, etc.) — avoid per-test setup
   duplication.
3. Update cert L6 to `pass` with `by: "agent+tests"` for each widget.
4. Identify + fix issues discovered during test authoring (e.g., stale types, dead branches, missing accessibility
   attrs). Cert `findings[]` updated per widget.

**Commit cadence:** one commit per domain (7 commits: overview, orders, positions, book, pnl, alerts, accounts).

**Exit criteria:** `npm test -- --run tests/widgets/overview/` etc. all green; coverage gate from Phase 1 passes for
these 21 widgets; certs updated.

### Phase 3 — Wave 2: DeFi tab (15 widgets)

Current product focus per `live-defi-rollout` branch. Phase 1 pilot was one of these; 14 remaining.

**Widgets:**

- defi-flash-loans, defi-funding-matrix, defi-health-factor, defi-liquidity, defi-rates-overview, defi-reward-pnl,
  defi-staking, defi-staking-rewards, defi-strategy-config, defi-swap, defi-trade-history, defi-transfer,
  defi-waterfall-weights, enhanced-basis-dashboard

**Same pattern as Phase 2.** Some widgets share the `useDeFiData` context — reuse mocks from Phase 1's helper.

**Commit cadence:** one commit per batch of 3–5 widgets; 3–4 commits total.

**Exit criteria:** all 15 DeFi widgets have L1.5 specs; certs updated; no regressions in existing DeFi strategy specs.

### Phase 4 — L0 contract alignment (fixture ↔ Zod pairs)

Landable without live backend — fixtures can be validated against OpenAPI-derived Zod schemas today. Cassette replay
comes later.

**Deliverables:**

1. Add `openapi-zod-client` (or equivalent) to dev deps; generate Zod schemas from `lib/registry/openapi.json` into
   `lib/types/generated-zod.ts`.
2. Write `tests/contract/test_fixture_schema_alignment.spec.ts` parametrised over every fixture in
   `lib/mocks/fixtures/**`.
3. Write `scripts/sync-openapi.ts` — one-way pull from `unified-api-contracts/openapi/*.json` to
   `lib/registry/openapi.json`, regen TS + Zod. Land drift gate.
4. Add coverage gate: every endpoint in `openapi.json` has a matching fixture + Zod pair. Warn on feat/\*; block on
   main.
5. Land `scripts/generate-api-changelog.py` — diffs last two `openapi.json` commits, writes `docs/api-changelog.md`.

**Commit:** `feat(contract): L0 fixture ↔ Zod alignment + drift gate + changelog`

**Exit criteria:** `npm run test:contract` all green; drift between UI `openapi.json` and contracts SSOT reduced to
zero; new endpoints fail L0 until fixture added.

### Phase 5 — Wave 3 + 4: Markets, terminal, risk, options, strategies, instructions, bundles (~48 widgets)

Only after Waves 1+2 have proven the pattern and caught the majority of pattern-level issues.

**Ordering:**

- **Wave 3** (16 widgets): markets, terminal — orderbook-adjacent, common trader gaze
- **Wave 4** (32 widgets): risk, options, strategies, instructions, bundles

**Same pattern as Phase 2/3.** Commit per domain batch.

**Stop condition for Wave 4:** if mid-rollout we discover a domain is more fragile than certs suggest, pause that
domain, update the cert to reflect reality, defer the widget.

**Exit criteria:** every READY widget in scope has a passing L1.5 spec; coverage gate passes cleanly on main.

### Phase 6 — Naming alignment audit (deferred to post-wave; documented here for completeness)

Per `ui-testing-layers.md` Phase 3b: `scripts/audit-field-naming.ts` walks hooks + widgets, diffs field references
against OpenAPI keys with use-counts. `≥5 places → rename to backend wire-shape; <5 places → per-field decision.`

**Kept deferred** until waves 1+2 complete — renames should happen AFTER tests exist, so the tests catch regressions
from the rename.

## Verification

Per phase:

- **Phase 0**: `npm run typecheck` exits 0; `npm run lint` exits 0; `GATE_MODE=block npm run lint` exits 0 on all green
  files.
- **Phase 1**: `npm test -- --run tests/widgets/defi/defi-lending-widget.test.tsx` passes; coverage gate script runs;
  `tests/widgets/README.md` exists with template.
- **Phase 2–5**: for each domain batch — `npm test -- --run tests/widgets/<domain>/` passes; coverage gate passes for
  that domain; cert L6 updated for each widget.
- **Phase 4**: `npm run test:contract` passes; sync script converges UI `openapi.json` to contracts SSOT.

Coverage gate enforces the SSOT rule from `ui-testing-layers.md`: every READY widget (cert L0+L1+L7 pass) must have a
matching `tests/widgets/` file.

## Risks and mitigations

| Risk                                                    | Mitigation                                                                                                                                                   |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Test pattern doesn't scale past pilot                   | Phase 1 exit criteria includes a documented template in `tests/widgets/README.md`. If scaling hits friction, revise the template before rolling out further. |
| Cert claims pass but widget actually broken during test | Fix during test authoring + update `findings[]` in cert. This is why we test — to catch this.                                                                |
| Test runtime balloons with 107 widgets                  | Vitest `pool: "forks"` + affected-tests-only in watch mode. Full suite on CI only. Budget: total suite <60s on CI.                                           |
| Live backend arrives mid-rollout and breaks fixtures    | L0 fixture ↔ Zod pair (Phase 4) catches drift immediately. Tests continue to pass because they use mocked contexts, not real fetches.                        |
| Flaky tests from React 19 strict-mode re-renders        | Use `@testing-library/react` primitives; no manual rerender; fail loudly on act() warnings.                                                                  |
| Scope creep into predictions/sports                     | This plan explicitly excludes them. If requested mid-rollout, file a separate plan rather than extending this one.                                           |

## Non-goals

- **No L0 cassette replay** until live backend lands.
- **No L3b trader workflow extensions** beyond `ui_e2e_strategy_coverage_audit_2026_04_22.plan.md`.
- **No visual regression, no Lighthouse, no bundle budget** in this rollout.
- **No backend testing.** UI repo owns fixture ↔ OpenAPI alignment only.
- **No email flow testing.** Playbook testing SSOT covers this if needed.
- **No rename of field names.** Deferred to Phase 6 post-waves.

## References

- **UI testing SSOT**: `/codex/06-coding-standards/ui-testing-layers.md`
- **Backend testing SSOT**: `/codex/06-coding-standards/integration-testing-layers.md`
- **Playbook testing SSOT**: `/codex/14-customer-journeys/testing/README.md`
- **Widget cert index**: `unified-trading-system-ui/docs/manifest/widget-certification/*.json`
- **Strategy coverage plan (sibling)**: `unified-trading-pm/plans/ai/ui_e2e_strategy_coverage_audit_2026_04_22.plan.md`
- **Workspace UI rule**: `.claude/rules/ui.md`
- **Workspace workflow rule**: `.claude/rules/workspace-workflow.md`
