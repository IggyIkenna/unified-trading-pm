# DeFi Strategy UI Verification Plan

**Objective:** Automate the process of verifying that a DeFi strategy's UI widgets are fully functional with mocked
data. For each strategy, verify that input changes propagate correctly to dependent output values.

**Scope:** Any strategy in `/codex/09-strategy/defi/` folder

**Reusable Process:**

1. Read strategy specification
2. Identify required UI components
3. Check component existence and mock data setup
4. Use browser MCP to test form interactions
5. Verify dynamic value updates (input → dependent outputs)
6. Generate readiness report

---

## Phase 1: Strategy Analysis

### Task 1.1: List Available Strategies

- Location: `/codex/09-strategy/defi/*.md`
- Current available:
  - aave-lending.md ✅ DONE
  - basis-trade.md
  - staked-basis.md
  - recursive-staked-basis.md
  - ethena-benchmark.md
  - market-making-lp.md
  - omnichain-transfers.md
  - multi-chain-lending-yield.md
  - cross-chain-yield-arb.md
  - And 8 more variants (SOL, BTC, L2 versions)

### Task 1.2: Parse Strategy Spec

- Read strategy from codex
- Extract:
  - **Strategy ID** (e.g., `AAVE_LENDING`, `BASIS_TRADE`)
  - **Operations** (LEND, BORROW, SWAP, TRADE, etc.)
  - **Key inputs** (amount, asset, max_slippage, protocol)
  - **Key outputs** (expected_output, health_factor, position_value, pnl)
  - **Data sources** (features, rates, balances)
  - **Risk metrics** (health_factor, liquidation_threshold, margin)

### Task 1.3: Identify Required UI Components

- Pattern: `components/widgets/defi/{strategy-slug}-widget.tsx`
- Example: `aave-lending.md` → `defi-lending-widget.tsx`
- Also check for:
  - Data context provider (e.g., `defi-data-context.tsx`)
  - Mock fixtures (e.g., `lib/mocks/fixtures/defi-*.ts`)
  - Type definitions (e.g., `lib/types/defi.ts`)

---

## Phase 2: Component Verification

### Task 2.1: Check Widget Existence

- [ ] UI component file exists
- [ ] Component is exported and importable
- [ ] Component accepts `WidgetComponentProps`
- [ ] Component renders without errors

### Task 2.2: Check Mock Data Setup

- [ ] Protocol mock data exists
- [ ] Asset parameters defined (collateral factors, APY rates, prices)
- [ ] Trade history fixture exists
- [ ] Risk profile fixture exists
- [ ] Treasury snapshot fixture exists

### Task 2.3: Check Data Context

- [ ] Data context provider exists
- [ ] Mock data is properly injected into context
- [ ] State hooks are available (setAmount, setAsset, executeTrade, etc.)
- [ ] Trade history is stateful (not hardcoded)

---

## Phase 3: Dynamic Value Testing

### Task 3.1: Test Form Inputs

For each **input field**:

- [ ] Input accepts numeric values
- [ ] Input validates constraints (min/max, decimals)
- [ ] Input clearing works
- [ ] Input state persists across renders

**Inputs to test:**

- Amount
- Asset selector
- Operation type
- Max slippage
- Protocol selector

### Task 3.2: Test Dependent Outputs

For each **output field**, verify it changes when **inputs change**:

**Pattern: Amount → Expected Output**

```
- Change amount: 10 → 20
- Expected output should change: 9.95 → 19.90 (with 1% slippage)
- Status: PASS/FAIL
```

**Pattern: Asset → APY Rates**

```
- Change asset: ETH → USDC
- APY display should update: "4.50% / 5.20%" → "3.20% / 4.10%"
- Status: PASS/FAIL
```

**Pattern: Asset → Health Factor**

```
- Operation: LEND
- Asset 1 (ETH, 82% CF): 2.35 → 2.42
- Asset 2 (USDC, 77% CF): 2.35 → 2.39
- ETH should have larger HF impact (higher collateral factor)
- Status: PASS/FAIL
```

**Pattern: Operation → Expected Output Format**

```
- LEND 13 ETH → "12.87 aETH" (aToken form)
- BORROW 13 ETH → "12.87 ETH" (underlying)
- WITHDRAW 13 aETH → "13.06 ETH" (includes yield ~0.5%)
- REPAY 13 ETH → "13.04 ETH" (includes interest ~0.3%)
- Status: PASS/FAIL
```

**Pattern: Amount → Health Factor**

```
- LEND: amount ↑ → HF ↑
- BORROW: amount ↑ → HF ↓
- WITHDRAW: amount ↑ → HF ↓
- REPAY: amount ↑ → HF ↑
- Status: PASS/FAIL
```

### Task 3.3: Test Trade Execution

- [ ] Execute button is disabled when amount = 0
- [ ] Execute button fires when amount > 0
- [ ] New trade appears in trade history
- [ ] Trade seq number is correct (incremental)
- [ ] Trade timestamp is current
- [ ] Trade shows correct operation type, asset, amount
- [ ] Running P&L updates correctly

### Task 3.4: Test Edge Cases

- [ ] Amount = 0 (no change to outputs)
- [ ] Amount = very large (outputs scale correctly)
- [ ] Amount = decimal (e.g., 0.5 ETH)
- [ ] Rapid input changes (no lag/double renders)
- [ ] Protocol switch (all outputs update)
- [ ] Asset not available in protocol (fallback to first asset)

---

## Phase 4: Mock Data Verification

### Task 4.1: Protocol Parameters

For each protocol in mock data:

- [ ] All assets have collateral factors defined
- [ ] Collateral factors are realistic (0.5 - 0.95 range)
- [ ] APY rates are reasonable for asset class
- [ ] Liquidation thresholds are > collateral factors
- [ ] Asset prices are current (within 24h)

### Task 4.2: Trade History

- [ ] Initial mock trade history loads
- [ ] New trades append to history (not replace)
- [ ] Running P&L calculates correctly
- [ ] Trade seq numbers are unique
- [ ] Timestamps are valid ISO format

---

## Phase 5: Reporting

### Task 5.1: Generate Readiness Report

- **Strategy:** {STRATEGY_ID}
- **Spec Location:** `codex/09-strategy/defi/{strategy}.md`
- **Widget Location:** `components/widgets/defi/{widget}.tsx`
- **Status:** READY / IN_PROGRESS / BLOCKED
- **Test Results:**
  - Input validation: ✅ PASS / ❌ FAIL / ⏭️ SKIP
  - Output propagation: ✅ PASS / ❌ FAIL / ⏭️ SKIP
  - Trade execution: ✅ PASS / ❌ FAIL / ⏭️ SKIP
  - Mock data quality: ✅ PASS / ❌ FAIL / ⏭️ SKIP
- **Issues Found:** (list any broken behaviors)
- **Next Steps:** (what needs to be fixed)

### Task 5.2: Create Fixes (if needed)

If any test fails:

- [ ] Read the widget component
- [ ] Identify why the output didn't change
- [ ] Create/update mock data OR fix component logic
- [ ] Re-run failing test to verify fix
- [ ] Commit changes

---

## Execution

### Command Pattern

```
Agent: "Verify DeFi strategy UI readiness for {STRATEGY_NAME}"

Input strategy from: /codex/09-strategy/defi/{STRATEGY_NAME}.md
Output: readiness report + any fixes applied
```

### Example: Basis Trade

```
Strategy: BASIS_TRADE
Operations: SWAP, TRADE (long/short hedge)
Key inputs: amount, asset, venues, hedge_ratio
Key outputs: expected_output, margin_usage, funding_rate_impact, position_pnl
Mock data check: basis-trade fixture exists? collateral factors set? APYs reasonable?
Widget test: change amount → expected_output updates? switch asset → funding rates change?
Trade history: execute → appears in history with correct seq/timestamp?
Status: PASS/FAIL
```

---

## Checklist Template (Per Strategy)

```
Strategy: {NAME}
Date: {TODAY}

Phase 1: Analysis
- [ ] Spec read and parsed
- [ ] Operations identified: {LIST}
- [ ] Key inputs identified: {LIST}
- [ ] Key outputs identified: {LIST}

Phase 2: Components
- [ ] Widget file exists
- [ ] Data context exists
- [ ] Mock data exists
- [ ] Types defined

Phase 3: Dynamic Testing
- [ ] Input 1 → Output 1: PASS/FAIL
- [ ] Input 2 → Output 2: PASS/FAIL
- [ ] Input 3 → Output 3: PASS/FAIL
- [ ] Operation A behavior: PASS/FAIL
- [ ] Operation B behavior: PASS/FAIL
- [ ] Trade execution: PASS/FAIL
- [ ] Trade history: PASS/FAIL

Phase 4: Mock Data
- [ ] Protocol params realistic
- [ ] APY rates reasonable
- [ ] Asset prices current
- [ ] Trade history valid

Phase 5: Report
- [ ] Readiness: READY / IN_PROGRESS / BLOCKED
- [ ] Issues: {COUNT}
- [ ] Fixes applied: {COUNT}

Sign-off: {AGENT_NAME} | {TIMESTAMP}
```

---

## Success Criteria

A strategy is **READY** when:

1. ✅ All UI components exist and render
2. ✅ All inputs properly bound to state
3. ✅ All outputs update when inputs change
4. ✅ Expected output differs by operation type
5. ✅ Health factor / risk metrics update correctly
6. ✅ Trade execution works (button → history update)
7. ✅ Mock data is realistic and consistent
8. ✅ No errors in browser console
9. ✅ No broken dependencies (imports, types)

---

## Notes for Future Runs

- **Browser MCP:** Use Playwright to navigate to widget, interact with form, screenshot outputs
- **Screenshot comparison:** Capture state A (amount=10), state B (amount=20), compare output values
- **Automation level:** Full automation possible—read spec → identify tests → run tests → report
- **Reuse:** This plan can be applied to all strategies in `/codex/09-strategy/defi/`
