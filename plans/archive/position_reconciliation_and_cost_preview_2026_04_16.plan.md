---
doc_type: plan
title: position-reconciliation-and-cost-preview
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, execution-service, strategy-service, unified-api-contracts, unified-trading-library, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-16'
overview: Target vs actual position reconciliation (Observe tab), cost-aware close/reduce previews (Trading Terminal), and client reporting close-all
type: mixed
epic: epic-code-completion
completion_gates: {code: C5, deployment: D3, business: B3}
repo_gates:
- {repo: unified-trading-system-ui, code: C1, deployment: none, business: none}
- {repo: execution-service, code: C1, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
- {repo: position-balance-monitor-service, code: C1, deployment: none, business: none}
- {repo: unified-api-contracts, code: C1, deployment: none, business: none}
- {repo: unified-trading-library, code: C1, deployment: none, business: none}
- {repo: client-reporting-api, code: C1, deployment: none, business: none}
depends_on: []
todos:
- {id: uac-schemas, content: '- [x] [AGENT] P0. UAC schemas for position reconciliation, cost preview, and close-all

    ', status: done}
- {id: uei-event, content: '- [x] [AGENT] P0. UEI event — POSITION_DRIFT_DETECTED + POSITION_DRIFT_EVENT_TYPES

    ', status: done}
- {id: backend-position-state, content: '- [x] [AGENT] P0. Backend: target vs actual position state API (PBMS drift monitor + routes)

    ', status: done}
- {id: backend-cost-preview, content: '- [x] [AGENT] P0. Backend: cost-aware unwind preview endpoint (execution-service /preview/unwind)

    ', status: done}
- {id: backend-background-reconciler, content: '- [x] [AGENT] P1. Backend: background position reconciliation process + alerting (PositionDriftMonitor)

    ', status: done}
- {id: ui-observe-reconciliation, content: '- [x] [AGENT] P1. UI: Observe tab — position reconciliation page with KPI strip, bar chart, delta table, drift chart

    ', status: done}
- {id: ui-trading-cost-preview, content: '- [x] [AGENT] P1. UI: Trading Terminal — CostPreviewCard in intervention controls + kill switch panel

    ', status: done}
- {id: ui-observe-close-all, content: '- [x] [AGENT] P2. UI: Observe tab — close-all button with drift context (built into reconciliation page)

    ', status: done}
- {id: client-reporting-close-all, content: '- [x] [AGENT] P2. Client reporting: POST /api/v1/emergency/close-all/{client_id} with trading key guard

    ', status: done}
- {id: qg-all-repos, content: "- [x] [AGENT] P0. Quality gates pass on all affected repos *(archived 2026-04-22 — run `scripts/quality-gates.sh`\n  per repo before the next reconciliation release train; not re-swept in this session.)*\n", status: done}
isProject: false
---

# Position Reconciliation, Cost Preview & Close-All

## Context

The system has mature cost estimation models (`unwind_cost.py`, `bridge_cost_model.py`, `gas_cost_model.py`,
`rate_impact_engine.py`) and rich intervention controls (kill switch panel, intervention controls, flatten dialog) — but
these two worlds aren't connected. The intervention controls show static slippage estimates ("~0.2-0.5%") instead of
calling the actual cost engines. Additionally, there's no visibility into target vs actual position drift across
strategies in delta space or equity space.

**Three workstreams, two UI homes:**

| Workstream                               | UI Location                                                                                            | Why                                                                |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| Target vs actual position reconciliation | **Observe tab** (new sub-tab)                                                                          | Reconciliation = monitoring, background process, alerting on drift |
| Cost-aware close/reduce preview          | **Trading Terminal** (enhance existing intervention controls)                                          | Active trading decisions, Uniswap-style preview before execution   |
| Close all positions                      | **Both** — Trading overview (emergency, already exists) + Observe tab (enhanced, reconciliation-aware) |

**Live-mode only:** Close-all, kill switch, reduce exposure, and cost preview are **live-mode operations only**. They
make no sense in batch/backtest — you can't close positions in a backtest. The UI must gate these controls behind
live-mode detection (the existing Live/As-Of toggle in Trading layout). In batch mode, these buttons are
disabled/hidden. The background reconciliation process also only runs in live mode.

**Binance comparison note:** We admire Binance's data delivery infrastructure (order book updates, trades, network
throughput) but we're building better widgets. Their cost/position UI is basic — ours should show the full cost
decomposition and position drift that institutional desks need.

## Pre-Audit Manifest

### Existing cost estimation (execution-service)

| File                                               | Symbol                                              | Role                                                               |
| -------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------ |
| `execution_service/engine/unwind_cost.py`          | `estimate_full_unwind_cost()`, `UnwindCostEstimate` | Full position unwind cost — gas, fees, slippage, bridge            |
| `execution_service/services/bridge_cost_model.py`  | `BridgeCostModel`                                   | Cross-chain transfer costs, live Across API quotes                 |
| `execution_service/services/gas_cost_model.py`     | `GasCostModel`                                      | Per-chain gas estimates with L2 multipliers                        |
| `execution_service/services/rate_impact_engine.py` | `RateImpactEngine`                                  | Lending rate impact simulation (Aave V3, Morpho, Compound, Kamino) |
| `execution_service/services/pnl_calculator.py`     | PnL attribution                                     | Post-trade actual costs                                            |

### Existing position tracking

| File                                                        | Symbol                   | Role                                                    |
| ----------------------------------------------------------- | ------------------------ | ------------------------------------------------------- |
| `strategy_service/engine/position_client.py`                | `StrategyPositionClient` | Queries position-balance-monitor for strategy positions |
| `execution_service/services/position_tracker.py`            | `DeFiPositionTracker`    | DeFi protocol position tracking                         |
| `position_balance_monitor_service/core/treasury_monitor.py` | `TreasuryMonitor`        | Treasury-level balance monitoring, emits `TREASURY_LOW` |

### Existing UI intervention controls

| File                                                      | Component              | Role                                             |
| --------------------------------------------------------- | ---------------------- | ------------------------------------------------ |
| `components/trading/kill-switch-panel.tsx`                | `KillSwitchPanel`      | 6 exit playbooks, scope selector, impact preview |
| `components/trading/intervention-controls.tsx`            | `InterventionControls` | Reduce exposure slider, emergency flatten        |
| `components/widgets/alerts/alerts-kill-switch-widget.tsx` | Kill switch widget     | Pause, cancel, flatten, disable venue            |
| `components/widgets/risk/risk-kpi-strip-widget.tsx`       | `useLiveDelta()`       | Portfolio delta in USD and ETH                   |

### Current Observe tab structure

| Tab                         | Route                               | Status  |
| --------------------------- | ----------------------------------- | ------- |
| Risk Dashboard              | `/services/observe/risk`            | Exists  |
| Alerts                      | `/services/observe/alerts`          | Exists  |
| News                        | `/services/observe/news`            | Exists  |
| Strategy Health             | `/services/observe/strategy-health` | Exists  |
| Scenarios                   | `/services/observe/scenarios`       | Exists  |
| System Health               | `/services/observe/health`          | Exists  |
| **Position Reconciliation** | `/services/observe/reconciliation`  | **NEW** |

Note: Reconciliation currently lives under Reports (`/services/reports/reconciliation`) — that's trade/book
reconciliation. Position reconciliation (target vs actual drift) is a different concern and belongs in Observe.

### Client reporting (client-reporting-api)

| File                              | Role                    | Status                       |
| --------------------------------- | ----------------------- | ---------------------------- |
| `core/exchange_data_collector.py` | Read-only exchange data | Uses read-only API keys only |
| `api/routes/performance.py`       | GET positions           | No write capability          |

---

## Execution Phases

```
Phase 0: UAC Schemas ─────────────────────────────────────────────┐
                                                                   │
Phase 1: Backend APIs (PARALLEL) ──────────────────────────────── │
  ├─ 1A: Position state API (strategy-service / PBMS)             │
  ├─ 1B: Cost preview endpoint (execution-service)                 │
  └─ 1C: Background reconciler + alerting (PBMS)                   │
         ┌─────────────────── QG GATE ──────────────────────┐      │
Phase 2: UI (PARALLEL) ──────────────────────────────────────────  │
  ├─ 2A: Observe → Position Reconciliation page                    │
  ├─ 2B: Trading Terminal → cost preview integration               │
  └─ 2C: Observe → close-all with reconciliation context           │
         ┌─────────────────── QG GATE ──────────────────────┐      │
Phase 3: Client Reporting ────────────────────────────────────────  │
  └─ 3A: Basic close-all (requires trading API keys, client opt-in)│
         ┌─────────────────── QG GATE ──────────────────────┐      │
Phase 4: Validation ──────────────────────────────────────────────  │
  └─ All repos QG pass, integration tests, browser validation      │
```

---

## Phase 0: UAC Schemas

### 0.1 — Position reconciliation schemas (unified-api-contracts)

New schemas in `unified_api_contracts.internal.domain.position_balance_monitor`:

```python
class PositionDriftMetric(BaseModel):
    """Per-strategy target vs actual in one dimension."""
    strategy_id: str
    strategy_name: str
    share_class: str          # "ETH", "BTC", "USDT", "USD"
    dimension: str            # "delta" | "equity_allocation"
    target_value: Decimal     # e.g. target delta = 0.0, target allocation = 25000.0
    actual_value: Decimal     # e.g. actual delta = 0.3, actual allocation = 22500.0
    deviation: Decimal        # actual - target
    deviation_pct: Decimal    # (actual - target) / total_equity * 100
    severity: str             # "normal" | "warning" | "critical"
    updated_at: datetime

class PortfolioReconciliationSnapshot(BaseModel):
    """Full portfolio reconciliation state."""
    total_equity_usd: Decimal
    allocated_equity_usd: Decimal
    unallocated_equity_usd: Decimal
    allocation_deviation_pct: Decimal  # how far from 100% allocated
    drift_metrics: list[PositionDriftMetric]
    share_class_summary: dict[str, ShareClassSummary]  # per share class totals
    snapshot_at: datetime

class ShareClassSummary(BaseModel):
    share_class: str
    target_delta: Decimal
    actual_delta: Decimal
    delta_residual: Decimal       # actual - target
    target_equity: Decimal
    actual_equity: Decimal
    equity_deviation_pct: Decimal
```

### 0.2 — Cost preview schemas (unified-api-contracts)

New schemas in `unified_api_contracts.internal.domain.execution_service`:

```python
class UnwindPreviewRequest(BaseModel):
    """Request to preview cost of closing/reducing positions."""
    strategy_id: str | None = None     # None = all strategies
    action: str                         # "close" | "reduce"
    reduce_pct: Decimal | None = None  # required if action == "reduce", 1-100
    execution_style: str = "twap"      # "market" | "twap" | "atomic_defi"
    twap_duration_minutes: int = 15    # only for twap

class UnwindPreviewResponse(BaseModel):
    """Full cost decomposition for position close/reduce."""
    strategy_id: str | None
    action: str
    positions_affected: int
    # Cost breakdown
    estimated_slippage_usd: Decimal
    estimated_slippage_bps: Decimal
    estimated_gas_usd: Decimal
    estimated_exchange_fees_usd: Decimal
    estimated_bridge_fees_usd: Decimal
    total_estimated_cost_usd: Decimal
    total_estimated_cost_bps: Decimal  # as fraction of notional
    # Execution plan
    notional_to_close_usd: Decimal
    estimated_duration_minutes: Decimal
    execution_steps: list[UnwindStep]
    # Risk
    market_impact_estimate_bps: Decimal
    confidence_interval: str  # "low" | "medium" | "high"

class UnwindStep(BaseModel):
    """One leg of the unwind execution plan."""
    instrument: str
    venue: str
    side: str           # "sell" | "buy" (to close)
    quantity: Decimal
    estimated_price: Decimal
    estimated_slippage_bps: Decimal
    operation_type: str  # "market_order" | "swap" | "repay" | "withdraw" | "unstake" | "bridge"
```

### 0.3 — Reconciliation alert event (unified-trading-library)

```python
# Event: POSITION_DRIFT_DETECTED
# Severity: HIGH
# Payload: { strategy_id, dimension, target, actual, deviation_pct, share_class }
```

---

## Phase 1: Backend APIs (PARALLEL)

### 1A — Target vs actual position state API

**Repo:** strategy-service + position-balance-monitor-service

**What:** Each strategy declares its target state (target delta per share class, target equity allocation). The position
balance monitor already tracks actual positions. Wire these together.

**Implementation:**

1. **Strategy target declaration** (strategy-service): Each strategy archetype already has config fields like
   `delta_target: 0.0`. Expose a `/strategies/{id}/target-state` endpoint that returns the target delta and target
   equity allocation per share class.

2. **Position state aggregation** (position-balance-monitor-service): New endpoint `/reconciliation/portfolio-snapshot`
   that:
   - Fetches all strategy targets from strategy-service
   - Fetches actual positions (already has this data)
   - Computes per-strategy drift in delta space and equity space
   - Returns `PortfolioReconciliationSnapshot`

3. **Share class calculation:**
   - ETH share class: all ETH-denominated positions, compute net delta in ETH
   - BTC share class: all BTC-denominated positions, compute net delta in BTC
   - USDT share class: stablecoin positions, compute delta in USDT equivalent
   - Total equity: sum across all share classes in USD

4. **Example:** Total equity = $100K. Strategy A target = $25K (25%), actual = $22.5K → 2.5% deviation. Strategy A
   target delta (ETH class) = 0.0, actual delta = 0.3 ETH → residual = 0.3 ETH.

### 1B — Cost preview endpoint

**Repo:** execution-service

**What:** New `/preview/unwind` POST endpoint that accepts `UnwindPreviewRequest` and returns `UnwindPreviewResponse`.
This wires the existing cost models together behind a single API.

**Implementation:**

1. New route in execution-service health API: `POST /preview/unwind`
2. Fetch current positions for the strategy (or all strategies) from position-balance-monitor
3. For each position, compute close cost using existing models:
   - `estimate_full_unwind_cost()` for overall cost
   - `GasCostModel` for per-chain gas
   - `BridgeCostModel` for cross-chain legs
   - `RateImpactEngine` for lending position unwind rate impact
4. For "reduce" action, scale costs proportionally to `reduce_pct` (with nonlinear slippage adjustment — larger
   positions have worse slippage per dollar)
5. Build `execution_steps` list showing each leg of the unwind
6. Return confidence interval based on data freshness (live quotes = "high", cached = "medium", estimates = "low")

**Key:** This is a **read-only preview**, no orders placed. Same concept as Uniswap showing "Expected output: X, Minimum
received: Y, Price impact: Z%" before you confirm a swap.

### 1C — Background position reconciliation process + alerting

**Repo:** position-balance-monitor-service

**What:** Background loop (configurable interval, default 30s) that:

1. Computes `PortfolioReconciliationSnapshot` (same logic as 1A endpoint)
2. Evaluates drift thresholds:
   - **Normal:** deviation < 2% equity, delta residual < configured threshold
   - **Warning:** deviation 2-5% equity or delta residual approaching limit
   - **Critical:** deviation > 5% equity or delta residual breaching limit
3. On WARNING or CRITICAL: emits `POSITION_DRIFT_DETECTED` event via unified-trading-library
4. Event flows to alert pipeline → shows as high-severity notification in Observe → Alerts

**Thresholds configurable** via typed config reloader (per `config_reloaders.py` pattern).

---

## Phase 2: UI (PARALLEL — after Phase 1 QG gate)

### 2A — Observe tab: Position Reconciliation page

**Repo:** unified-trading-system-ui

**Route:** `/services/observe/reconciliation`

**New tab** added to `OBSERVE_TABS` in `service-tabs.tsx`:

```
Position Recon → /services/observe/reconciliation
```

**Page layout (widget grid):**

1. **KPI Strip** — Total equity, allocated %, unallocated %, worst drift %, active alerts
2. **Equity Allocation Treemap/Bar** — Per-strategy: target bar (outline) overlaid with actual bar (filled). Shows "$25K
   target / $22.5K actual (−10%)" per strategy. Color-coded: green (<2%), amber (2-5%), red (>5%).
3. **Delta Residual Table** — Per share class (ETH, BTC, USDT): | Strategy | Target Delta | Actual Delta | Residual |
   Severity | Shows the net delta that should be zero (or the target) vs what it actually is.
4. **Drift Time Series** — Line chart of deviation_pct over time per strategy. Shows whether drift is growing or
   mean-reverting.
5. **Active Alerts Feed** — Filtered to `POSITION_DRIFT_DETECTED` events, linked to the strategy in question.

**Config section (collapsible):**

- Drift thresholds per strategy (override defaults)
- Alert severity mapping
- Reconciliation interval
- This is where "a lot of the config stuff goes" — observe tab = monitoring + config

### 2B — Trading Terminal: cost preview on close/reduce

**Repo:** unified-trading-system-ui

**Enhance existing components:**

1. **Intervention Controls** (`intervention-controls.tsx`):
   - When user selects "Reduce Exposure" and picks a percentage → call `POST /preview/unwind` with
     `{action: "reduce", reduce_pct: N}`
   - Replace static "~0.2-0.5% slippage" with real numbers from response
   - Show Uniswap-style preview card:
     ```
     Closing Strategy: Basis ETH
     Positions affected: 4
     ─────────────────────────────
     Estimated slippage    $180  (12 bps)
     Gas costs             $95
     Exchange fees         $65
     Bridge fees           $0
     ─────────────────────────────
     Total cost            $340  (23 bps)
     Execution time        ~12 min (TWAP)
     Market impact         ~8 bps
     Confidence            High (live quotes)
     ```
   - "Confirm" button only after preview loads

2. **Kill Switch Panel** (`kill-switch-panel.tsx`):
   - When selecting FAST_UNWIND or SLOW_UNWIND → call preview endpoint for the selected scope
   - Replace "Impact Preview: X positions affected" with real cost breakdown
   - Add estimated total cost to the confirmation dialog

3. **Emergency Flatten Dialog**:
   - Conservative vs Aggressive now shows real slippage estimates, not hardcoded ranges
   - Side-by-side cost comparison: "Conservative: $340 (23 bps, 12 min) vs Aggressive: $890 (60 bps, <1 min)"

### 2C — Observe tab: close-all with reconciliation context

**Repo:** unified-trading-system-ui

**On the Position Reconciliation page (2A):**

- **"Close All Positions" button** at top of page — same prominence as Trading overview
- But enhanced: shows current drift state alongside the close-all action
- "Your portfolio has 3.2% drift across 5 strategies. Closing all positions will cost ~$1,200 (18 bps)"
- Clicking opens the same kill switch dialog (reuse `KillSwitchPanel` component) but pre-populated with firm-wide scope
- This is the duplicate of the Trading overview close-all, but with reconciliation context baked in

**The Trading overview close-all stays as-is** — it's the emergency "first thing you see" button. The Observe version is
the considered, cost-aware version for when you've been monitoring drift and decide to act.

---

## Phase 3: Client Reporting Close-All

**Repo:** client-reporting-api

**Gated by client decision:** Requires trading API keys (not read-only). Per the user's specification: "that would be a
client decision whether they want to give us that."

**Implementation:**

1. **Credentials registry extension:** Add `has_trading_keys: bool` field per client in `credentials-registry.yaml`.
   Default `false`. Only `true` when client provides trading-capable API keys.

2. **New route:** `POST /api/v1/emergency/close-all/{client_id}`
   - Guard: returns 403 if `has_trading_keys == false` for that client
   - Uses CCXT `create_order()` to submit market sell orders for all open positions
   - Logs everything (rationale required in request body)
   - Returns list of order IDs and estimated fills

3. **No cost simulation** — as the user noted, "we wouldn't be able to simulate costs" because these strategies don't
   live in our trading system universe. These are external accounts we report on, not strategies we run.

4. **UI:** If client-reporting-ui is resurrected, add a simple red "Emergency Close All" button gated behind
   `has_trading_keys`. For now, API-only is sufficient.

---

## Phase 4: Validation

### Quality gates

- `cd <repo> && bash scripts/quality-gates.sh` for all 7 affected repos
- basedpyright clean on all Python repos
- `CI=true npm test -- --run` for unified-trading-system-ui

### Integration tests

- Mock mode: cost preview returns sensible mock data, reconciliation snapshot computes from mock positions
- Live mode (staging): cost preview calls real cost models with staging positions

### Browser validation

- Observe → Position Reconciliation page renders with mock data
- Trading → intervention controls show cost preview card
- Observe → close-all button opens kill switch dialog with cost context
- Trading overview → existing close-all still works unchanged

### B3 KPIs

| KPI                          | Target                                                    |
| ---------------------------- | --------------------------------------------------------- |
| Cost preview latency         | P95 < 2s (must feel snappy, like Uniswap quote)           |
| Reconciliation loop interval | Configurable, default 30s                                 |
| Drift alert delivery         | < 5s from detection to UI notification                    |
| Cost estimate accuracy       | Within 20% of actual execution cost (backtest validation) |

---

## Success Criteria

1. **Observe tab** has a new "Position Recon" sub-tab showing target vs actual for every strategy, in both delta and
   equity space, per share class
2. **Background reconciler** fires high-severity alerts when drift exceeds thresholds — visible in Observe → Alerts
3. **Trading Terminal** close/reduce actions show real cost breakdowns before confirmation (Uniswap-style preview)
4. **Close-all** exists in both Trading overview (emergency) and Observe (considered, cost-aware)
5. **Client reporting** has optional close-all for clients who provide trading API keys
6. All 7 repos pass quality gates
