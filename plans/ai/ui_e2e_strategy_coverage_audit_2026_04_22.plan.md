---
name: ui-e2e-strategy-coverage-audit
overview:
  Audit + extend Playwright strategy coverage in unified-trading-system-ui against codex architecture-v2 SSOT — fix
  misalignment on 5 existing execution specs, add observation-widget verification, extend to remaining 13 archetypes + 8
  families
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
  - /codex/09-strategy/architecture-v2/README.md
  - codex/09-strategy/architecture-v2/archetypes/*.md
  - codex/09-strategy/architecture-v2/families/*.md
  - /codex/09-strategy/architecture-v2/strategy-registry-v2.md
---

# UI e2e strategy coverage — audit + extension against architecture-v2 SSOT

## Context

`unified-trading-system-ui` currently has:

- **5 Playwright execution specs** (`tests/e2e/strategies/defi/*.spec.ts`) for `YIELD_ROTATION_LENDING`,
  `YIELD_STAKING_SIMPLE`, `CARRY_BASIS_PERP`, `CARRY_STAKED_BASIS`, `AMM_LP_PROVISION` — each backed by a JSON fixture
  under `tests/e2e/fixtures/strategies/`.
- **1 parametric detail-view spec** (`tests/e2e/strategies/detail-view.spec.ts`) covering 12 detail-view archetypes
  shallowly (tab triggers + 6 KPI cards; no tab-panel content check).
- **Strategy registry SSOT** at `tests/e2e/_shared/strategy-registry.ts` — 18 archetypes, 5 `coverage: "execution"`, 13
  `coverage: "detail-view"`.

After reading the v2 SSOT archetype docs in `unified-trading-pm/codex/09-strategy/architecture-v2/`, several gaps
between the canonical instruction flows and what the tests actually exercise were identified. This plan reconciles them.

## Decisions locked in (plan-mode Q&A, 2026-04-22)

- **Commit cadence** — one commit per phase (3 commits total).
- **Phase 1 sequencing** — audit doc lands as a separately reviewable artifact within Phase 1, then fixture/widget
  fixes. Both ship under one commit.
- **YIELD_STAKING_SIMPLE** — wire up the existing `DeFiStakingWidget` (confirmed present in
  `components/widgets/defi/defi-staking-widget.tsx` with full STAKE/UNSTAKE operation state, `executeDeFiOrder` wired).
  Add `data-testid` attributes, mount on `/services/trading/defi/staking` as a new card above the tabs, add STAKE +
  UNSTAKE scenarios.
- **AMM_LP_PROVISION → MARKET_MAKING_CONTINUOUS rename** — match SSOT. Registry key becomes `MARKET_MAKING_CONTINUOUS`
  with `subMode: "amm_lp"`. Fixture, spec, and playbook filenames follow.

## Findings — SSOT vs current tests

| Archetype                | SSOT canonical instruction flow                                                                      | Current test covers                                                               | Gap                                                                                                                                               |
| ------------------------ | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `YIELD_ROTATION_LENDING` | `LEND` + `WITHDRAW` + `BRIDGE` across (protocol, chain)                                              | LEND 1000, WITHDRAW 500, protocol switch, asset switch                            | ✅ Actions covered. ❌ No observation-widget update assertion (wallet-summary, rates-overview, yield-chart, reward-pnl). ❌ No `BRIDGE` scenario. |
| `YIELD_STAKING_SIMPLE`   | `STAKE` + `UNSTAKE`                                                                                  | Clicks Positions / Validators / Rewards / Unstaking tabs on a read-only dashboard | ❌ Never STAKEs or UNSTAKEs. Test is a dashboard render, not an execution path.                                                                   |
| `CARRY_BASIS_PERP`       | Paired `TRADE spot` + `TRADE perp` (ATOMIC or LEADER_HEDGE)                                          | SWAP only                                                                         | ❌ Missing perp short leg and pair verification. No funding-matrix widget assertion post-execute.                                                 |
| `CARRY_STAKED_BASIS`     | 4-leg: `STAKE` → `PLEDGE` (LEND as collateral) → `BORROW` → `SHORT PERP`                             | 2-leg: SWAP USDC→weETH + TRANSFER USDC to a placeholder address                   | ❌ Missing STAKE, PLEDGE, BORROW, PERP short. Current test stubs strategy as "swap + send".                                                       |
| `AMM_LP_PROVISION`       | **Archetype does not exist in SSOT** — v2 folds AMM LP under `MARKET_MAKING_CONTINUOUS` sub-mode B/C | ADD_LIQUIDITY, REMOVE_LIQUIDITY, pool switch, fee tier                            | ⚠️ Registered under a non-SSOT archetype key. Actions themselves are reasonable.                                                                  |

**Observation widgets (all strategies)**: no current spec asserts `defi-health-factor-widget`,
`defi-funding-matrix-widget`, `defi-reward-pnl-widget`, `defi-wallet-summary-widget`, `defi-yield-chart-widget`,
`defi-rates-overview-widget`, `defi-waterfall-weights-widget`, `defi-staking-rewards-widget`, `defi-flash-loans-widget`,
or `enhanced-basis-widget` update after executing.

**13 detail-view archetypes**: covered by the parametric spec which clicks tabs and asserts 6 KPI cards — no tab-panel
content check, no archetype-analytics panel check for 10 of the 13 (only 3 have `detailViewKpis` populated today).

## Scope — 3 phases

### Phase 1 — Reconcile 5 existing execution specs against SSOT

Audit-first, then mechanical fixes.

**P1.1 — Write the audit doc.** Produce `docs/audits/e2e-strategy-tests-ssot-alignment.md` in the UI repo with one table
per archetype — columns: `SSOT instruction sequence`, `current test coverage`, `gap`, `fix`,
`status (pending / landed)`. Checkbox rows. This becomes the living index for phases 1–3.

**P1.2 — Rename `AMM_LP_PROVISION`.** Merge into `MARKET_MAKING_CONTINUOUS` with a `subMode: "amm_lp"` flag on the
registry entry — or, if that's too invasive, rename the registry key to `MARKET_MAKING_CONTINUOUS_AMM_LP` with a note in
the audit doc. Renames cascade to:

- `tests/e2e/_shared/strategy-registry.ts`
- `tests/e2e/fixtures/strategies/amm-lp-provision.json` → `market-making-continuous-amm-lp.json`
- `tests/e2e/strategies/defi/amm-lp-provision.spec.ts` → same rename
- `docs/trading/defi/playbooks/amm-lp-provision.md`

**P1.3 — Fix `YIELD_STAKING_SIMPLE`.** Two options; pick one after verifying what widgets exist:

- Option A: there is a stake/unstake widget somewhere in the app — add STAKE + UNSTAKE scenarios that actually execute
  through it.
- Option B: there isn't — downgrade this archetype's `coverage` to `detail-view` in the registry. The dashboard spec
  becomes an observation-only smoke, not an execution test.

**P1.4 — Extend `CARRY_BASIS_PERP` to cover the perp leg.** After the SWAP scenario, add a `TRADE perp` scenario:
navigate to the perp widget surface (likely `/services/trading/cefi` or the paired-trade detail panel), drive a
short-perp entry on the same notional, assert both ledger rows share a `correlation_id` or that the basis-metrics panel
surfaces the paired state. Requires identifying the widget — research step.

**P1.5 — Extend `CARRY_STAKED_BASIS` to cover the 4 legs.** Sequence: STAKE → PLEDGE (LEND as collateral on Aave) →
BORROW USDC → SHORT PERP. Each leg may live on a different widget today; spec needs to walk through them in order within
one session. Verify which widgets exist (stake widget, defi-lending-widget with PLEDGE operation, borrow widget,
defi-swap-widget in basis mode) before committing to scenarios.

**Checkpoint**: commit audit doc + renames + fixes. Human review before Phase 2.

### Phase 2 — Observation-widget verification

After each execute, the right observation widgets should reflect the new state. This is the "updated data in all
widgets" piece the user asked about.

**P2.1 — Per-archetype `observationWidgets` list on each fixture JSON.** Add field:

```json
{
  "observationWidgets": [
    { "testid": "defi-wallet-summary-widget", "assertVisible": true, "assertsUpdatedAfter": ["LEND", "WITHDRAW"] },
    { "testid": "defi-rates-overview-widget", "assertVisible": true }
  ]
}
```

**P2.2 — Shared verify helper `verifyObservationWidgets(page, fixture, afterAction)`.** Lives in
`tests/e2e/_shared/verify.ts`. Asserts each listed widget is visible; for widgets tagged with `assertsUpdatedAfter`,
captures a pre-execute snapshot of a stable attribute (row count, a specific KPI textContent) and asserts it changed
post-execute.

**P2.3 — Per-archetype mapping based on SSOT P&L-attribution sections**:

- `YIELD_ROTATION_LENDING` → wallet-summary, rates-overview, yield-chart, reward-pnl
- `YIELD_STAKING_SIMPLE` (if kept as execution) → staking-rewards, wallet-summary
- `CARRY_BASIS_PERP` → funding-matrix, enhanced-basis, wallet-summary
- `CARRY_STAKED_BASIS` → health-factor, funding-matrix, reward-pnl, wallet-summary
- `MARKET_MAKING_CONTINUOUS_AMM_LP` → waterfall-weights, wallet-summary, reward-pnl

**P2.4 — Route-level observation smoke.** New spec `tests/e2e/strategies/defi-observation.spec.ts` — walks to each DeFi
route, asserts every observation widget on that route renders its testid anchor (independent of any execute). Catches
widgets that ship broken.

**Checkpoint**: commit Phase 2. Human review.

### Phase 3 — Extend to 13 detail-view archetypes + 8 families

**P3.1 — Backfill instance-catalogue coverage.** For each of the 13 detail-view archetypes, verify
`lib/mocks/fixtures/strategy-instances.ts` has at least one mock row matching the SSOT archetype doc's
`Example instances`. Add missing ones. SSOT typically lists 2–7 example instances per archetype; today we have 1–3.

**P3.2 — Backfill `detailViewKpis`.** 10 archetypes in the registry have no `detailViewKpis`: `CARRY_BASIS_DATED`,
`ARBITRAGE_PRICE_DISPERSION`, `LIQUIDATION_CAPTURE`, `ML_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_EVENT_SETTLED`,
`RULES_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_EVENT_SETTLED`, `EVENT_DRIVEN`, `VOL_TRADING_OPTIONS`,
`STAT_ARB_PAIRS_FIXED`, `STAT_ARB_CROSS_SECTIONAL`. Populate from each archetype doc's P&L-attribution section (typical
Sharpe, drawdown, kill-switch metrics).

**P3.3 — Tab-panel content check.** Extend the parametric detail-view spec: for each of 7 tabs (P&L Attribution,
Instruments, Data & Features, Risk, Configuration, Testing Status, Decisions), click in and assert the expected panel
widget renders (P&L waterfall, instrument table, data-features list, risk-layers panel, config table, testing-status
table, decisions timeline).

**P3.4 — Family-level parametric spec.** New spec `tests/e2e/strategies/family-view.spec.ts` iterates over the 8
families from `lib/architecture-v2/families.ts`. For each family page, asserts the family header renders and the
archetype list matches the SSOT (8 families × their archetypes per README).

**P3.5 — Slot-label assertion.** Every mock instance id should match the SSOT slot-label grammar:
`ARCHETYPE@venue-asset-instrument-period-quote-env`. Add a unit test that validates every entry in
`strategy-instances.ts` parses against the grammar.

**Checkpoint**: commit Phase 3. Human review.

## Critical files

- `unified-trading-system-ui/tests/e2e/_shared/strategy-registry.ts` — SSOT for test coverage config
- `unified-trading-system-ui/tests/e2e/fixtures/strategies/*.json` — fixture per execution archetype
- `unified-trading-system-ui/tests/e2e/strategies/defi/*.spec.ts` — execution specs
- `unified-trading-system-ui/tests/e2e/strategies/detail-view.spec.ts` — parametric detail spec
- `unified-trading-system-ui/tests/e2e/_shared/verify.ts` — shared verify helpers
- `unified-trading-system-ui/lib/mocks/fixtures/strategy-instances.ts` — mock catalog
- `unified-trading-system-ui/lib/architecture-v2/` — client-side SSOT mirror of codex architecture-v2
- `unified-trading-system-ui/docs/audits/e2e-strategy-tests-ssot-alignment.md` — NEW, audit living index

## Verification per phase

**Phase 1**

- Audit doc exists with all 5 archetype rows filled.
- `rg "AMM_LP_PROVISION"` outside archive returns 0 hits after rename.
- `npx playwright test --project=chromium tests/e2e/strategies/defi/` all green.
- `npx tsc --noEmit` clean.

**Phase 2**

- Each execution spec calls `verifyObservationWidgets` at least once per mutating scenario.
- New `defi-observation.spec.ts` green on chromium + human projects.

**Phase 3**

- `npx playwright test tests/e2e/strategies/` green across all 18 archetypes + family spec.
- Slot-label grammar unit test green.

## Out of scope (explicit)

- 7 axes + 10 cross-cutting concern pages — not strategy-centric, separate audit.
- Backend contract verification — UI tests verify UI state only; API contract tests live in interface repos per
  workspace rules.
- Legacy `/codex/09-strategy/{cefi,defi,sports,tradfi,prediction}/` docs — SSOT is `architecture-v2/`, legacy is
  reference-only per SSOT README.
- Rebasing against upstream — user-side only (sandbox blocks).
- Pushing — local commits only per git-commit skill + universal rules.
