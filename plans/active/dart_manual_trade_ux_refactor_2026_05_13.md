---
title: DART manual-trade UX refactor — Phase C remainder pull-forward into May-23 cutover
type: active-plan
status: active
owner: ikenna
created: 2026-05-13
deadline: 2026-05-23
prior_deadline: post-cutover (operator triage)
deadline_change_reason: |
  Operator direction 2026-05-13: pulled forward into May-23 cutover scope. Workspace has
  throughput margin (~5-6x measured Day-1 2026-05-12); no descope; perfect cutover. The
  3 surfaces shipped at unified-trading-system-ui@`64660edd` (TradeMonitor +
  AutomationToggle + terminal landing) cover the 2 greenfield surfaces, but the Phase C
  remainder (Sheet → route refactor + dart-client.ts unification + full-flow e2e)
  closes the operator-UX gap for Group G Item 23.
horizon: 2026-05-23
companion_to:
  - plans/active/master_to_live_defi_2026_05_23.md (Group G Item 23)
  - plans/active/cross_cutting_may_23_deliverables_2026_05_08.md (Phase 4 BUILD scope)
migrated_from: plans/archive/issues/dart_manual_trade_ui_build_2026_05_10.md (Phase C remainder section)
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: design
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 2.4
effective_concurrent_slots: 1
codex_refs:
  - codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md
  - codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md
  - codex/14-customer-journeys/dart/mode-toggle.md
execution:
  owner: next daily work-split tab on Ikenna side (UI repo familiarity required)
  cadence: one-shot (build-out) + per-PR (regression smoke once shipped) + Playwright e2e against Tier-2 stack pre-cutover
  verifier: Playwright e2e `dart-manual-trade-flow.spec.ts` GREEN end-to-end + manual-trade-panel route surface renders with persona ACL gating
  last_executed: NEVER
---

> **🟢 PULLED FORWARD May-23 cutover (operator direction 2026-05-13)** — the Phase C
> remainder is no longer deferred to a successor-plan triage; it ships pre-cutover.
> Operator rationale: workspace has throughput margin (~5-6x); no descope, perfect
> cutover. ~2.4 cal-AI-days against ~1,880 cal-day capacity in next 9 days.

# DART manual-trade UX refactor — Phase C remainder

## Why this plan exists

Master plan Group G Item 23 (DART manual-trade gate end-to-end visualization) has a
partial shipment at `unified-trading-system-ui@64660edd` per option-c narrow scope:

- `components/dart/trade-monitor.tsx` (greenfield) — shipped.
- `components/dart/automation-toggle.tsx` (greenfield) — shipped.
- `app/(platform)/services/dart/terminal/page.tsx` (slim landing) — shipped, links to
  existing `components/trading/manual/manual-trading-panel.tsx` Sheet.

The Phase C remainder identified in
[`plans/archive/issues/dart_manual_trade_ui_build_2026_05_10.md`](../archive/issues/dart_manual_trade_ui_build_2026_05_10.md)
covers the Sheet → route refactor + unified dart-client.ts + full-flow e2e. Previously
deferred to post-cutover successor-plan triage; pulled forward May-23 per operator
direction 2026-05-13.

## Scope (Phase C remainder — from archived issue doc § "Phase C remainder explicitly DEFERRED")

The 5 deferred items below from the archived issue doc form this plan's todo set. Each
item carries `migrated_from:` provenance to the archive line.

### Phase C.1 — Sheet → dedicated route refactor for ManualTradeForm / TradePreview / ExecutionDispatch

The existing `components/trading/manual/manual-trading-panel.tsx` + `single-order-form.tsx`
+ `mass-quote-panel.tsx` (1,256 lines total) ship the form + preview + dispatch surfaces
as a Sheet. The Phase C remainder ports these into dedicated `/dart/terminal/*` routes
so the manual-trade flow has a first-class operator-UX surface instead of a Sheet over
the trading overview.

- [ ] [AGENT] P1. **Audit existing `manual-trading-panel.tsx` surface** — read the
      1,256-line Sheet implementation end-to-end. Catalog (a) which props it consumes,
      (b) which backend endpoints it hits (`/manual/submit`, `/preview/*`), (c) which
      persona ACL gates apply, (d) which mock-handler fixtures are wired. **Output**:
      one-page "Sheet → route mapping" markdown in `unified-trading-system-ui/docs/`
      (or inline at top of new route file). _(migrated_from: archive doc Phase C remainder
      Items 3+4+5)_
- [ ] [AGENT] P1. **`app/(platform)/services/dart/terminal/manual/page.tsx`** — NEW
      dedicated route hosting ManualTradeForm (extracted from manual-trading-panel.tsx
      body). Reads `?archetype=&venue=` URL params; mounts form + preview pane side by
      side or stacked per UX wireframe. Persona ACL: DART-Full plan required; non-DART
      personas redirect to `/dart/locked?from=manual`. _(migrated_from: archive doc Phase C remainder
      Item 3 — ManualTradeForm)_
- [ ] [AGENT] P1. **`components/dart/manual-trade-form.tsx`** — extracted form component
      from `manual-trading-panel.tsx`. Fields per archived spec: archetype dropdown +
      venue dropdown (filtered by `ARCHETYPE_CAPABILITY_REGISTRY[archetype].supported_venues`)
      + side toggle + size_pct_nav + limit_price + algo dropdown + dry_run checkbox.
      Submit → calls `POST /preview/<archetype>` then routes to
      `/dart/terminal/manual/preview/<correlation_id>`. _(migrated_from: archive doc Phase C
      remainder Item 3)_
- [ ] [AGENT] P1. **`components/dart/trade-preview.tsx`** — extracted preview component.
      Receives preview response from `POST /preview/*`; displays projected fill price /
      slippage / collateral required / max-drawdown impact / risk-check pass-fail per
      rule. Confirm button → calls `POST /manual/submit`; Cancel returns to form.
      _(migrated_from: archive doc Phase C remainder Item 4)_
- [ ] [AGENT] P1. **`components/dart/execution-dispatch.tsx`** — extracted dispatch
      glue (typed fetch wrapper + error handling + correlation_id capture). Returns
      `instruction_id` + redirects to `/dart/terminal/manual/[instructionId]/page.tsx`.
      _(migrated_from: archive doc Phase C remainder Item 5)_

### Phase C.2 — Per-instruction monitor route

- [ ] [AGENT] P1. **`app/(platform)/services/dart/terminal/manual/[instructionId]/page.tsx`** —
      NEW per-instruction monitor route. Currently the inline `?instruction=<id>`
      URL-param pattern renders TradeMonitor on the landing page. Dedicated route gives
      first-class deep-linking, browser-history support, and proper persona ACL gate at
      the route level. Mounts `<TradeMonitor instructionId={params.instructionId} />`.
      _(migrated_from: archive doc Phase C remainder Item 6)_

### Phase C.3 — Unified `lib/api/dart-client.ts`

- [ ] [AGENT] P1. **`lib/api/dart-client.ts`** (~100 lines) — typed wrappers around the
      4 backend endpoints (`/preview`, `/manual/submit`, `/manual/instructions/{id}/status`,
      `/api/archetypes/{id}/operational-mode`). Mirrors the `lib/api/strategy-versions.ts`
      shape. Consumers: `manual-trade-form.tsx`, `trade-preview.tsx`, `trade-monitor.tsx`,
      `automation-toggle.tsx`. Replaces ad-hoc fetch calls scattered across the 4
      components. _(migrated_from: archive doc Phase C remainder Item 9)_
- [ ] [AGENT] P1. **`lib/api/mocks/dart.ts`** (~150 lines) — mock fixtures for the 4
      endpoints (preview response, submit response, status poll, mode flip). Wired into
      `mock-handler.ts` so widgets render against fixtures when `VITE_MOCK_API=true`.
      _(migrated_from: archive doc Phase C remainder Item 10)_

### Phase C.4 — Full-flow e2e Playwright spec

- [ ] [AGENT] P1. **`tests/e2e/dart-manual-trade-flow.spec.ts`** (~200 lines) — Playwright
      spec covering full submit → preview → confirm → monitor flow end-to-end. Replaces
      / extends the current `tests/e2e/playbooks/dart-cockpit/phase-c-terminal-flow.spec.ts`
      (which covers page-mount + monitor surface only). Required cases per archived spec:
      form validation (size > 0, archetype required, venue must be supported by
      archetype); preview displays risk-check + slippage estimate; confirm submits to
      `/manual/submit` and routes to monitor; monitor renders status updates (poll-driven
      test against mock fixture); automation toggle confirms before flipping to LIVE;
      persona ACL gates `prospect-signals-only` → 404 / locked redirect. _(migrated_from:
      archive doc Phase C remainder Item 11)_

### Phase D — Codex audit + master plan flip (~0.25 AI-day)

- [ ] [AGENT] P1. Update `codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md`
      with shipped surface paths (new dedicated route + dart-client.ts unification).
- [ ] [AGENT] P1. Update `codex/09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md`
      with the shipped Sheet → route migration.
- [ ] [AGENT] P0. Flip master Group G Item 23 row in `plans/active/master_to_live_defi_2026_05_23.md`
      to remove the "full UX flow refactor DEFERRED to successor plan" annotation. Update
      `Last verified` date.
- [ ] [AGENT] P0. Flip `cross_cutting_may_23_deliverables_2026_05_08.md` Phase 4 BUILD
      checkboxes (BUILDs 1-5 ML-training-control surfaces are SEPARATE — this Phase C
      remainder is the manual-trade route refactor scope only).

## Done-definition (full-execution criterion per CLAUDE.md HARD RULE)

- ✅ `/dart/terminal/manual/page.tsx` route renders ManualTradeForm; form validation
  passes per archived spec.
  - **What ran**: `cd unified-trading-system-ui && npx playwright test tests/e2e/dart-manual-trade-flow.spec.ts`
    against Tier-2 mock stack.
  - **Verification**: all 6 Playwright cases green; no console errors; persona-ACL
    redirect verified for `prospect-signals-only`.
- ✅ `/dart/terminal/manual/[instructionId]/page.tsx` renders TradeMonitor with deep-link
  support (reload-persistent).
  - **What ran**: Playwright `dart-manual-trade-flow.spec.ts` `it("deep-link to monitor")` case.
- ✅ `lib/api/dart-client.ts` consolidates the 4 endpoint calls; consumers migrated.
  - **What ran**: `cd unified-trading-system-ui && CI=true npm test -- --run` + `grep -r "fetch.*\\(/manual\\|/preview\\|/api/archetypes" components/dart components/trading/manual lib/`
    returns calls routed only through dart-client.ts.
- ✅ Master plan Group G Item 23 row flipped (DEFERRED annotation removed; Last verified
  bumped).
- ✅ Codex `dart-manual-trade-spec.md` + `operational-modes-matrix.md` updated.

## Composes with (HARD RULES)

- `master_to_live_defi_2026_05_23.md` Group G Item 23 (this plan owns the Phase C
  remainder portion).
- `cross_cutting_may_23_deliverables_2026_05_08.md` Phase 4 BUILD scope (separate scope
  — BUILDs 1-5 ML-training-control are not this plan).
- `Two teammates × multiple parallel agents — don't edit unfamiliar files` HARD RULE —
  UI repo has extensive parallel-agent conventions (mock-handler, persona ACL, Firebase
  emulator, widget shell). Read-first list lives in archived issue doc § "Read-first
  list (before any UI edit)".
- `Plans Run To Actual Completion` HARD RULE — Phase D plan-flip waits for Playwright
  GREEN against the shipped backend, not just code-shipped.
- `Capture Discoveries As Plan Todos Immediately` HARD RULE — discoveries during
  Sheet → route extraction (UX-pattern drift, persona-ACL edge cases, mock-fixture
  gaps) go inline as `- [ ] **DEFERRED**` annotations, not chat.

## Risks + collision callouts

- **Foreign-edit risk HIGH** on `unified-trading-system-ui` repo. Per CLAUDE.md
  "Two teammates × multiple parallel agents": single dedicated UI tab, no parallel
  fan-out across widget shell + manual-trade form + Playwright spec in the same logical
  unit. Stage edits per Phase C.1/C.2/C.3/C.4 separately.
- **Sheet-as-Sheet preservation** — DO NOT delete `manual-trading-panel.tsx` Sheet
  surface in this plan; it remains as the trading-overview-Sheet alternative entry. The
  Phase C remainder adds the dedicated `/dart/terminal/manual/*` route surface alongside.
  Sheet retirement is post-cutover polish.
- **Backend routes already shipped** — `/manual/submit`, `/preview/*`,
  `/manual/instructions/{id}/status`, `/api/archetypes/{id}/operational-mode` all already
  exist per archived audit. This plan is UI-only.

## Out-of-scope (explicit deferrals)

- **Sheet (`manual-trading-panel.tsx`) retirement** — post-cutover polish; both surfaces
  coexist for May-23.
- **Multi-archetype concurrent monitor** — dashboard for many in-flight instructions is
  a post-cutover polish item.
- **Telemetry / OpenTelemetry traces** — covered by execution-service's existing trace
  wiring; no UI-side trace work needed for MVP.
- **Real-backend integration testing against staged secrets / Tenderly fork** —
  exercised by operator first-trades on 2026-05-22 dress rehearsal, not by this plan's
  Playwright suite (mock fixtures only).

## Quality gates (per phase)

- `cd unified-trading-system-ui && CI=true npm test -- --run` GREEN
- `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build` GREEN
- `cd unified-trading-system-ui && npx playwright test tests/e2e/dart-manual-trade-flow.spec.ts` GREEN
- `cd unified-trading-system-ui && bash scripts/quality-gates.sh` GREEN (workspace-wide
  lint / format / typecheck / route smoke).
