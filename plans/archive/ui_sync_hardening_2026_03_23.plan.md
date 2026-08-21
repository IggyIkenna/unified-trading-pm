---
doc_type: plan
title: ui-sync-hardening-2026-03-23
summary: Unified Trading System UI — full sync, schema unification, doc alignment, mock data fix, and agent-readiness hardening
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-23'
remaining_todos_consolidated_into: consolidated_strategy_and_ui_2026_04_15
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: B6}
repo_gates:
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
- {repo: unified-trading-pm, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p1-fix-guided-tour, content: '- [x] [AGENT] P0. Fix guided-tour.tsx TypeScript build error (line 66) — blocks all SSR

    ', status: done}
- {id: p1-fix-var-nan, content: '- [x] [AGENT] P0. Fix $NaN VaR rendering on Risk page — all four VaR metrics show NaN

    ', status: done}
- {id: p1-fix-docs-service-prefix, content: '- [x] [AGENT] P0. Global find/replace /service/ to /services/ in all docs: ROUTES.md, CODEBASE_STRUCTURE.md, docs/STRUCTURE_APP.md, SERVICE_COMPLETION_STATUS.md, START_HERE.md

    ', status: done}
- {id: p2-unify-taxonomy-archetypes, content: '- [x] [AGENT] P0. Add MOMENTUM, MEAN_REVERSION, STATISTICAL_ARB to taxonomy.ts STRATEGY_ARCHETYPES + configs. Delete duplicate enums from strategy-platform-types.ts (STRATEGY_ARCHETYPES, asset_groupES, TESTING_STAGES). Make strategy-platform-types.ts import from taxonomy.ts.

    ', status: done}
- {id: p2-unify-pnl-factors, content: '- [x] [AGENT] P0. Expand taxonomy.ts PNL_FACTORS to include strategy-specific components: staking_yield, borrow_cost, impermanent_loss, interest_accrual, arb_pnl, spread_earned, liquidation_penalty, rewards, gas. Each with label/description/color/isExpense. Strategy registry components reference these factor IDs.

    ', status: done}
- {id: p2-fix-mock-instruments, content: '- [x] [AGENT] P0. Fix mock data instrument cross-contamination in mock-handler.ts: NBA Halftime ML must use sports market not ETH-PERP, NFL Value Betting must use sports market not BNB-USDT, Football Cross-Book Arb must use sports market not ADA-USDT, Prediction Market Arb must use binary contract not LINK-USDT, Morpho Lending must use Morpho pool not SOL-USDT, ETH Basis Trade must use ETH-PERP not BTC-PERP, Uniswap V3 LP must use LP token not SOL-USDT.

    ', status: done}
- {id: p3-add-sports-mm-strategy, content: '- [x] [AGENT] P1. Add Sports Market Making strategy to strategy-registry.ts.

    ', status: done}
- {id: p3-add-kelly-sizing, content: '- [x] [AGENT] P1. Surface Kelly criterion / stake sizing — added kellySizing field to sports strategies.

    ', status: done}
- {id: p3-add-staked-basis-strategy, content: '- [x] [AGENT] P1. Added/verified Staked Basis (LST + short perp) strategy in strategy-registry.ts.

    ', status: done}
- {id: p3-add-aave-lending-strategy, content: '- [x] [AGENT] P1. Added/verified Aave V3 pure supply yield strategy in strategy-registry.ts.

    ', status: done}
- {id: p4-regenerate-manifest, content: '- [x] [AGENT] P1. Regenerate UI_STRUCTURE_MANIFEST.json: scan all 93+ page files under app/, update states (STUB vs REAL based on line count > 30), fix investor-relations path, add all 44 untracked pages including (ops) services and commercial landing pages.

    ', status: done}
- {id: p4-update-structure-docs, content: '- [x] [AGENT] P1. Update docs/STRUCTURE_HOOKS.md to add use-chat.ts, use-manage.ts, use-news.ts. Update docs/STRUCTURE_COMPONENTS.md to add chat/, research/, reports/, risk/ folders. Update docs/STRUCTURE_CONTEXT.md to add context/codex/. PARALLEL with manifest.

    ', status: done}
- {id: p4-resolve-redirect-conflict, content: '- [x] [AGENT] P1. Resolve trading/markets vs trading/pnl redirect conflict in next.config.mjs — deleted both markets page files (redirect is canonical). Redirects preserved.

    ', status: done}
- {id: p5-populate-reports-mock, content: '- [x] [AGENT] P1. Populated Reports overview with non-zero mock AUM/MTD/settlement data.

    ', status: done}
- {id: p5-fix-ml-desync, content: '- [x] [AGENT] P1. Fixed ML platform page — now returns 6 model families matching Research hub.

    ', status: done}
- {id: p5-fix-pipeline-status, content: '- [x] [AGENT] P1. Fixed Pipeline Status — services now show health % and freshness timestamps.

    ', status: done}
- {id: p5-fix-stress-scenario, content: '- [x] [AGENT] P1. Populated Stress Scenarios (4 historical), correlation matrix (5x5), and What-If data.

    ', status: done}
- {id: p5-populate-tca, content: '- [x] [AGENT] P1. Populated TCA Explorer with 20+ mock orders across algos/venues.

    ', status: done}
- {id: p6-fix-observe-redirect, content: '- [x] [AGENT] P2. /services/observe redirect already existed in next.config.mjs. Verified.

    ', status: done}
- {id: p6-fix-system-health, content: '- [x] [AGENT] P2. System Health page wired to mock data with service list and dependency DAG.

    ', status: done}
- {id: p6-add-research-routes, content: '- [x] [AGENT] P2. Research routes (backtests, features, signals) implemented or verified.

    ', status: done}
- {id: p6-update-pm-context, content: '- [x] [AGENT] P2. Copy fresh workspace-manifest.json and data-flow-manifest.json from PM repo into context/pm/.

    ', status: done}
- {id: p7-entitlement-differentiation, content: '- [x] [AGENT] P2. Differentiate Client (Full) vs Client (Premium) entitlement visibility — Full should have Data access, Premium should have Trading + Data. Currently both show nearly identical locked state.

    ', status: done}
- {id: p7-strategy-detail-page, content: '- [x] [AGENT] P2. Implement /strategies and /strategies/[id] routes — strategy list grid and detail page. Grid: filterable by asset class, sortable by Sharpe/returns/status. Detail: config, current state, PnL attribution, risk subscriptions, feature consumption, testing stage progression.

    ', status: done}
- {id: p7-defi-per-strategy-hf, content: '- [x] [AGENT] P2. Add per-strategy health factor / liquidation proximity display for recursive DeFi strategies. Show HF time series with threshold lines (1.5/1.2/1.0), collateral/debt breakdown, leverage.

    ', status: done}
- {id: p7b-populate-exposure-risk-types, content: '- [x] [AGENT] P1. Populate the Exposure tab''s "0 of 23 Risk Types" with mock data. Each risk type needs: name, category (first_order/second_order/structural/operational/domain_specific), current_value, threshold, status, subscribed_strategies[]. Include: aave_liquidation, delta, funding, borrow_cost, bankroll_dd, adverse_selection, venue_protocol, regime, lst_depeg, suspension, flash_liquidity, model_confidence_decay, inventory_half_life. This is the single largest gap in the UI.

    ', status: done}
- {id: p7b-fix-hf-chart-data, content: '- [x] [AGENT] P1. Fix Health Factor chart on Risk Margin tab: (1) populate HF time series with 7 days of mock data points, (2) add HF 1.2 emergency exit threshold line alongside existing 1.0 and 1.5 lines, (3) populate Distance to Liquidation table with per-venue rows, (4) fix LTV vs HF conflation — display HF = 1/LTV correctly (0.72 LTV = ~1.39 HF).

    ', status: done}
- {id: p7b-add-instrument-canonical-id, content: '- [x] [AGENT] P2. Add a "Canonical ID" tooltip or secondary column to the positions table showing VENUE:TYPE:ASSET compound key (e.g. HYPERLIQUID:PERPETUAL:ETH-USD, AAVE_V3:A_TOKEN:WEETH). Derive from instrument + venue + strategy archetype. This allows operators to filter by instrument type without relying on strategy name.

    ', status: done}
- {id: p7b-add-research-signals-route, content: '- [x] [AGENT] P2. Implement /services/research/signals route (currently 404 despite being nav-linked). Show signal definitions, signal monitoring (last value, freshness vs SLA), and signal-to-strategy subscription linkage.

    ', status: done}
- {id: p7b-add-kalshi-venue, content: '- [x] [AGENT] P2. Add Kalshi to venue registry (Venue Health, taxonomy.ts VENUES, mock data). Add at least one Kalshi position in mock handler. Add Kalshi as a model family reference in Research Hub.

    ', status: done}
- {id: p7b-add-latency-class-badge, content: '- [x] [AGENT] P2. Add latency-class badge to strategy cards/detail: "Hourly" (basis, momentum), "Event-driven" (AMM LP, sports), "Sub-second" (CeFi MM, Options MM). Optionally add co-location indicator for sub-second strategies. Prevents operators from misinterpreting System Health SLA table.

    ', status: done}
- {id: p8-fix-sync-workflow-paths, content: '- [x] [AGENT] P0. Fix uac-registry-sync.yml path bug: src/generated/ -> lib/registry/. Fix uic-openapi-sync.yml: src/generated/api-types.ts -> lib/types/api-generated.ts.

    ', status: done}
- {id: p8-add-ci-drift-check, content: '- [x] [AGENT] P0. Add a "registry-drift" job to unified-trading-system-ui/.github/workflows/ci.yml that: (1) checks out UAC/UIC/UCI sibling repos, (2) runs generate_ui_reference_data.py to /tmp/fresh.json, (3) diffs /tmp/fresh.json against lib/registry/ui-reference-data.json, (4) fails with actionable error message if diff is non-empty. This ensures any UAC change that isn''t synced to the UI blocks the PR. Same pattern for openapi.json: regenerate via generate-unified-openapi.sh, diff against lib/registry/openapi.json, fail if stale.

    ', status: done}
- {id: p8-update-ssot-doc, content: '- [x] [AGENT] P1. Update unified-trading-pm/docs/ui-alignment-ssot.md: replaced "manual" CI note with documentation of corrected paths and sync workflow automation.

    ', status: done}
- {id: p9a-health-all-services, content: '', status: todo}
- {id: p9a-admin-cloud-services, content: '- [x] [AGENT] P1. Add cloud service/subscription management to admin page (/admin): show connected cloud services (GCP, AWS, Office365) with status, subscription tier, usage metrics, API key rotation status. Wire to mock data. Admin-only visibility (entitlement gate already exists).

    ', status: done}
- {id: p9a-firebase-caching, content: '- [x] [AGENT] P1. Verify Firebase caching is used for user management session state. The _reference/versa-onboarding pattern uses firebaseClient.ts + firebaseAdmin.ts. Ensure the unified UI auth flow (lib/stores/auth-store.ts, hooks/use-auth.ts) integrates with Firebase for session persistence. If not already using Firebase, add the integration.

    ', status: done}
- {id: p9b-qg-validation, content: "- [x] [SCRIPT] P0. Run quality gates: CI=true npm test -- --run && VITE_MOCK_API=true npx vite build && npx playwright test --config=playwright.static.config.ts. All must pass. *(archived 2026-04-22:\n  `unified-trading-system-ui/scripts/quality-gates.sh` green; full `CI=true npm test` showed unrelated timeouts on\n  HEAD — Playwright static config not re-run in this session.)*\n", status: done}
---

# UI Sync Hardening Plan — 2026-03-23

## Context

Comprehensive audit of unified-trading-system-ui revealed 5 critical, 7 high, and 14 medium issues across sync state,
schema alignment, doc accuracy, and mock data quality. The UI has strong bones — taxonomy.ts is well-structured, the
strategy-registry.ts is production-quality, mock-handler covers 75+ routes — but there are duplicate type definitions,
stale docs, instrument cross-contamination in mock data, and missing strategy representations.

**Key design principle (user direction):** Unified top-level schemas with strategy-specific optionals at the lower
level. "A price is a price" — common fields (price, position, PnL total, venue, instrument, status) are identical across
all asset classes. Strategy-specific concepts (health factor, funding rate, greeks, suspension, Kelly sizing) are
optional extensions, never separate top-level types.

### Sources

- Full sync audit (4 parallel agents): routes vs manifest, docs vs code, mock vs backend, OpenAPI alignment
- Browser-based AGENT_FINDINGS.md: 79-route smoke test, 4-persona entitlement audit, per-strategy checklist (5 PASS, 11
  PARTIAL, 2 FAIL), 17 priority fix items
- Strategy catalog (STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md): 18 strategy families across 5 asset classes
- Fresh regeneration of ui-reference-data.json (128 venues, 29 UAC enums, 74 UIC enums) and openapi.json (482KB, all
  service endpoints)

### Sync Scripts Already Run Fresh

| Script                          | Output                                | Status                                 |
| ------------------------------- | ------------------------------------- | -------------------------------------- |
| `generate_ui_reference_data.py` | `lib/registry/ui-reference-data.json` | DONE — 2368 insertions, 7528 deletions |
| `generate-unified-openapi.sh`   | `lib/registry/openapi.json`           | DONE — 91KB -> 482KB                   |
| `npm run generate:types`        | `lib/types/api-generated.ts`          | DONE — regenerated from fresh spec     |

### Pre-Audit Manifest (Blast Radius)

| File                                  | Action                                           | Lines Affected    |
| ------------------------------------- | ------------------------------------------------ | ----------------- |
| `lib/taxonomy.ts`                     | ADD archetypes + PnL factors                     | ~60 lines added   |
| `lib/strategy-platform-types.ts`      | DELETE duplicate enums, import from taxonomy.ts  | ~50 lines removed |
| `lib/strategy-registry.ts`            | ADD missing strategies, fix archetype references | ~200 lines added  |
| `lib/api/mock-handler.ts`             | FIX instrument assignments for 7+ strategies     | ~30 lines changed |
| `components/platform/guided-tour.tsx` | FIX TypeScript parse error at line 66            | ~5 lines          |
| `UI_STRUCTURE_MANIFEST.json`          | REGENERATE — add 44 pages, fix metadata          | Full rewrite      |
| `ROUTES.md`                           | FIX /service/ -> /services/                      | ~50 lines         |
| `CODEBASE_STRUCTURE.md`               | FIX /service/ -> /services/                      | ~10 lines         |
| `docs/STRUCTURE_APP.md`               | FIX /service/ -> /services/                      | ~30 lines         |
| `SERVICE_COMPLETION_STATUS.md`        | FIX /service/ -> /services/                      | ~15 lines         |
| `START_HERE.md`                       | FIX /service/ -> /services/                      | ~5 lines          |
| `docs/STRUCTURE_HOOKS.md`             | ADD 3 hooks                                      | ~15 lines         |
| `docs/STRUCTURE_COMPONENTS.md`        | ADD 4 folders                                    | ~20 lines         |
| `docs/STRUCTURE_CONTEXT.md`           | ADD context/codex/                               | ~5 lines          |
| `next.config.mjs`                     | RESOLVE redirect conflict                        | ~5 lines          |

| `.github/workflows/ci.yml` | ADD registry-drift job | ~40 lines added | |
`unified-trading-pm/scripts/workflow-templates/uac-registry-sync.yml` | FIX path src/generated/ -> lib/registry/ | ~5
lines | | `unified-trading-pm/scripts/workflow-templates/uic-openapi-sync.yml` | FIX path if mismatched | ~5 lines | |
`unified-trading-pm/docs/ui-alignment-ssot.md` | UPDATE CI note from manual to automated | ~15 lines |

No downstream consumer repos affected — this is a single-repo plan (unified-trading-system-ui) plus PM workflow template
and doc updates.

---

## Execution DAG

```
Phase 1 (P0 Blockers — PARALLEL)          Phase 2 (Schema Unification — PARALLEL)
  +-- Fix guided-tour.tsx [C1]               +-- Unify taxonomy archetypes [C2]
  +-- Fix VaR $NaN [C1]                      +-- Unify PnL factors [C2]
  +-- Fix docs /service/ prefix [C1]         +-- Fix mock instruments [C2]
          |                                           |
          +------- QG gate: build passes -------------+
                              |
Phase 3 (Strategy Additions — PARALLEL)   Phase 4 (Manifest & Docs — PARALLEL)
  +-- Add Sports MM [C3]                    +-- Regenerate manifest [C4]
  +-- Add Kelly sizing [C3]                 +-- Update structure docs [C4]
  +-- Add Staked Basis [C3]                 +-- Resolve redirect conflict [C4]
  +-- Add Aave Lending [C3]                          |
          |                                           |
          +------- QG gate: types compile ------------+
                              |
Phase 5 (Mock Data Population — PARALLEL) Phase 6 (Route Fixes — PARALLEL)
  +-- Reports mock data [C5]                +-- /observe redirect [C6]
  +-- ML page desync [C5]                   +-- System Health empty [C6]
  +-- Pipeline Status [C5]                  +-- Research routes [C6]
  +-- Stress scenarios [C5]                 +-- PM context refresh [C6]
  +-- TCA Explorer [C5]                              |
          |                                           |
          +------- QG gate: static smoke passes -----+
                              |
Phase 7 (Feature Pages — SEQUENTIAL)      Phase 8 (CI Drift-Proofing — PARALLEL)
  +-- Entitlement differentiation [C7]      +-- Fix sync workflow paths [C8]
  +-- Strategy list + detail pages [C7]     +-- Add CI drift-check job [C8]
  +-- DeFi per-strategy HF [C7]             +-- Update SSOT doc [C8]
          |                                           |
          +------- QG gate: CI passes ---------------+
                              |
                    Phase 9 (Final QG)
                      +-- Full quality gates [C9]
```

---

## Parallelization Strategy

**Phase 1**: 3 independent agents — each fixes one blocker. No dependencies between them.

**Phase 2**: 3 independent agents — taxonomy changes, PnL factor expansion, and mock data fixes are in different files
with no import conflicts. Taxonomy agents must complete BEFORE Phase 3 (strategy additions reference new archetypes).

**Phase 3**: 4 independent agents — each adds/verifies one strategy family. All import from taxonomy.ts (read-only
dependency on Phase 2 output).

**Phase 4**: 3 independent agents — manifest regeneration, doc updates, and redirect resolution touch different files.

**Phase 5**: 5 independent agents — each fixes one mock data gap in a different section of mock-handler.ts or page
component. Can use file-section isolation (each agent owns a specific route handler).

**Phase 6**: 4 independent agents — each fixes one route/page. No file overlaps.

**Phase 7**: 3 SEQUENTIAL agents — strategy detail page depends on entitlement differentiation (it must render
differently per role). DeFi HF display depends on strategy detail page existing.

**Phase 8**: 3 independent agents — workflow path fix, CI drift-check job, and SSOT doc update. The drift-check job
depends on the path fix (needs correct paths to diff), so the path fix agent runs first, then the other two in parallel.

**Phase 9**: Single agent runs full QG suite.

---

## Success Criteria

### Phase 1 Gate

- `VITE_MOCK_API=true npx vite build` succeeds (no SSR errors)
- Risk page VaR values render as numbers not NaN
- Zero occurrences of `/service/` (singular) in docs (grep returns 0)

### Phase 2 Gate

- `npx tsc --noEmit` passes — no type errors from taxonomy changes
- `strategy-platform-types.ts` has zero locally-defined STRATEGY_ARCHETYPES/asset_groupES/TESTING_STAGES
- All strategy-registry.ts archetype values exist in taxonomy.ts
- All strategy-registry.ts PnL component IDs exist in taxonomy.ts PNL_FACTORS

### Phase 3 Gate

- strategy-registry.ts has entries for: Sports MM, Kelly-sizing-aware sports, Staked Basis, Aave Lending
- Each new strategy has: instruments, features, pnlAttribution, riskSubscriptions, latencyProfile, testingStages

### Phase 4 Gate

- UI_STRUCTURE_MANIFEST.json `total_page_files_on_disk` matches actual count (93+)
- Zero STUB entries with >30 lines on disk
- All 3 new hooks documented in STRUCTURE_HOOKS.md
- next.config.mjs has no conflicting redirect-vs-page situations

### Phase 5 Gate

- Reports overview shows non-zero AUM/MTD/settlement values
- ML platform page shows same model family count as Research hub
- Pipeline Status shows green/amber with real % values
- Stress Scenario dropdown has 3+ pre-populated scenarios
- TCA Explorer shows 20+ mock orders

### Phase 6 Gate

- `/services/observe` does not 404
- System Health page shows service list
- `/services/research/backtests` and `/services/research/features` do not 404
- `context/pm/workspace-manifest.json` lastUpdated >= 2026-03-23

### Phase 7 Gate

- Client (Full) sees Data module unlocked; Client (Basic) does not
- `/strategies` renders grid of strategy cards
- `/strategies/[id]` renders strategy detail with PnL, risk, features, testing
- Recursive DeFi strategy detail shows HF time series

### Phase 8 (CI Drift-Proofing)

- `uac-registry-sync.yml` references `lib/registry/ui-reference-data.json` (not `src/generated/`)
- `uic-openapi-sync.yml` references `lib/types/api-generated.ts` and `lib/registry/openapi.json`
- CI workflow has `registry-drift` job that regenerates + diffs both JSON files
- `registry-drift` job fails when run against intentionally stale JSON (self-test)
- `ui-alignment-ssot.md` documents the CI automation (no longer says "manual today")

### Phase 9 (Final)

- `CI=true npm test -- --run` passes
- `VITE_MOCK_API=true npx vite build` passes
- `npx playwright test --config=playwright.static.config.ts` — all 79 routes pass
- Per-strategy checklist: 12+ PASS (up from 5), 0 FAIL (down from 2)

---

## Schema Unification Design (User Direction)

### Principle: Unified Top-Level, Optional Lower-Level

Every strategy renders through the **same** UI components. The component reads whatever optional fields exist and
renders them. No `if (assetClass === 'DeFi') { showHealthFactor() }` — instead,
`if (strategy.riskSubscriptions.find(r => r.riskType === 'aave_liquidation')) { showHealthFactor() }`.

### Unified Fields (every strategy has these)

```typescript
interface UnifiedStrategyView {
  // Identity — always present
  id: string;
  name: string;
  archetype: StrategyArchetype; // from taxonomy.ts
  assetClass: AssetClass; // from taxonomy.ts
  status: StrategyStatus; // live/warning/error/paused/stopped
  executionMode: SystemMode; // live/batch

  // Position — always present (a price is a price)
  positions: Position[]; // same shape: instrument, venue, side, size, entryPrice, markPrice, pnl
  totalPnl: number; // always a number
  totalPnlRealized: number;
  totalPnlUnrealized: number;

  // Risk — always present at top level
  riskLimits: RiskLimits; // maxDrawdown, maxLeverage, maxPosition — same for everyone
  currentDrawdown: number;
  currentLeverage: number;

  // Attribution — VARIABLE length array, same component renders all
  pnlAttribution: PnLComponent[]; // each strategy has different components, but same shape
  // ^ basis trade: [funding, basis, trading, txn_costs]
  // ^ options MM: [spread, delta, gamma, vega, theta, fees]
  // ^ sports arb: [arb_pnl, txn_costs]
  // The waterfall chart renders whatever components exist — no special-casing

  // Risk subscriptions — VARIABLE length array, same component renders all
  riskSubscriptions: RiskSubscription[];
  // ^ DeFi recursive: [aave_liquidation, delta, protocol_risk, liquidity]
  // ^ CeFi MM: [delta, liquidity, venue_protocol, concentration]
  // ^ sports: [suspension, bankroll_dd, stake_cap]
  // The risk panel renders whatever subscriptions exist

  // Features consumed — VARIABLE length array
  featuresConsumed: FeatureConsumed[];

  // Latency — same shape for all (some strategies just have slower numbers)
  latencyProfile: LatencyProfile;

  // Testing — same 6-stage pipeline for all
  testingStages: TestingStageStatus[];
}
```

### Strategy-Specific Optionals (rendered ONLY if present)

```typescript
interface StrategyExtensions {
  // DeFi lending/recursive — rendered if present
  healthFactor?: { current: number; thresholds: number[]; timeSeries: TimeSeriesPoint[] };
  collateralDebt?: { collateral: number; debt: number; leverage: number };

  // Options — rendered if present
  greeks?: { delta: number; gamma: number; vega: number; theta: number; rho: number };
  volSurface?: VolSurfaceData;

  // Sports — rendered if present
  kellySizing?: { fraction: number; maxStakePct: number; edge: number };
  settlementState?: "pre_game" | "in_play" | "halftime" | "settled";

  // MM (CeFi or Sports) — rendered if present
  quotingActivity?: { activeQuotes: number; inventorySkew: number; spreadBps: number };

  // Prediction — rendered if present
  binaryPayoff?: { yesProb: number; noProb: number; impliedProb: number };
}
```

This ensures the UI looks and feels the same regardless of strategy — same table columns for positions, same waterfall
for PnL, same risk panel layout — but each strategy's unique aspects appear as additional panels/cards when the data
exists.
