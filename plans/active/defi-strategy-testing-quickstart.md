# DeFi Strategy Testing - Quick Start Guide

**Complete automation for testing any DeFi strategy: UI verification + E2E test generation + regression protection.**

---

## What You Get

### 🎯 Phase 1: UI Verification
Agent verifies the strategy widget works:
- ✅ Form inputs respond correctly
- ✅ Output values change when inputs change
- ✅ Expected output differs by operation
- ✅ Health factor/risk metrics calculated correctly
- ✅ Mock data is realistic

**Output:** Readiness report + fixed widget + updated mock data

### 🧪 Phase 2: E2E Test Generation
Agent auto-generates Playwright tests covering:
- ✅ Widget rendering
- ✅ Form input interactions (amount, asset, operation)
- ✅ Output propagation (expected output, APY, health factor)
- ✅ Health factor per asset (collateral factor applied)
- ✅ Trade execution & history updates
- ✅ Edge cases (zero amount, rapid changes)

**Output:** `tests/e2e/strategies/defi/{strategy}.spec.ts`

### ▶️ Phase 3: Run Tests
Agent runs Playwright tests and reports:
- ✅ All tests pass / Some failed
- ✅ Coverage: X test cases
- ✅ Execution time: Ys

### 🔄 Phase 4: Regression Protection
Tests commit to CI/CD:
- On every PR: Tests run automatically
- ❌ If widget breaks: Tests fail → blocks merge
- ✅ If widget works: Tests pass → PR can merge

---

## How to Use

### **Option A: Quick Test (UI Only)**
```
"Verify {STRATEGY_NAME} UI"

Example: "Verify basis-trade UI"
```

→ Runs Phase 1 only (UI verification)  
→ Reports readiness + any fixes needed  
→ No tests generated (quick check)

### **Option B: Full Automation (UI + Tests)**
```
"Test {STRATEGY_NAME} end-to-end"

Example: "Test recursive-staked-basis end-to-end"
```

→ Runs Phase 1 (UI verification)  
→ Runs Phase 2 (test generation)  
→ Runs Phase 3 (execute tests)  
→ Runs Phase 4 (commit tests)  
→ Complete protection for future changes ✅

---

## Available Strategies

From `/codex/09-strategy/defi/`:

**Lending Strategies**
- `aave-lending` ✅ (already done)
- `eth-lending-yield`
- `btc-lending-yield`
- `sol-lending-yield`
- `multi-chain-lending-yield`

**Basis Trade Strategies**
- `basis-trade`
- `btc-basis-trade`
- `l2-basis-trade`
- `sol-basis-trade`

**Staking Strategies**
- `staked-basis`
- `recursive-staked-basis`
- `ethena-benchmark`

**Other**
- `market-making-lp`
- `omnichain-transfers`
- `cross-chain-yield-arb`
- `cross-chain-sor-rebalancing`

---

## Example: Test Basis Trade

```
User: "Test basis-trade end-to-end"

Agent:
  Phase 1: Reading basis-trade.md spec...
  - Operations: SWAP, TRADE (long/short)
  - Inputs: amount, asset, venues, hedge_ratio
  - Outputs: expected_output, margin_usage, funding_rate_impact
  
  Phase 1: Checking UI component...
  - Found: components/widgets/defi/defi-trade-widget.tsx ✅
  - Checking mock data...
  - Created/updated: lib/mocks/fixtures/defi-basis-trade.ts ✅
  
  Phase 1: Testing UI interactions...
  - SWAP 10 USDC → expected_output updates ✅
  - Switch asset (ETH) → funding rates change ✅
  - Change amount → margin_usage recalculates ✅
  - Operation TRADE → output format differs ✅
  
  Phase 1: ✅ READY
  Readiness report saved to: defi-basis-trade-readiness-2026-04-01.txt
  
  Phase 2: Generating tests...
  - Widget rendering test ✅
  - Asset selection → APY update test ✅
  - Amount → expected output test ✅
  - Margin calculation per asset test ✅
  - Funding rate impact test ✅
  - Trade execution & history test ✅
  - Edge cases (zero, rapid changes) test ✅
  
  Test file created: tests/e2e/strategies/defi/basis-trade.spec.ts (8 tests)
  
  Phase 3: Running tests...
  ✅ widget renders with initial state (245ms)
  ✅ asset selection updates funding rates (312ms)
  ✅ amount input updates margin usage (198ms)
  ✅ expected output differs by operation (426ms)
  ✅ funding rate impact calculated per asset (567ms)
  ✅ trade execution adds to history (298ms)
  ✅ edge case: zero amount disables button (124ms)
  ✅ rapid input changes handled correctly (213ms)
  
  Phase 3: ✅ ALL TESTS PASSED (8/8)
  Execution time: 2.4s
  
  Phase 4: Committing...
  ✅ Committed to git:
    - lib/mocks/fixtures/defi-basis-trade.ts
    - components/widgets/defi/defi-trade-widget.tsx
    - tests/e2e/strategies/defi/basis-trade.spec.ts
  
  Message: "feat(basis-trade): UI verification + E2E tests
           - Verified basis-trade widget with dynamic testing
           - All form inputs → outputs propagate correctly
           - Generated 8 Playwright E2E tests
           - All tests passing"
  
  ✅ COMPLETE
  Basis trade widget is now protected by regression tests
  Future changes will be caught by CI/CD pipeline
```

---

## What Tests Look Like

After running, the generated test file will look like:

```typescript
test.describe('DeFi Basis Trade UI E2E', () => {
  test('asset selection updates funding rates', async ({ page }) => {
    // Navigate to widget
    await page.goto('http://localhost:3100/services/trading/defi');
    
    // Get initial funding rate
    const initialRate = await page.locator('[data-testid="funding-rate"]').textContent();
    
    // Switch asset to ETH
    await page.locator('[data-testid="asset-select"]').click();
    await page.locator('text=ETH').click();
    
    // Verify funding rate changed
    const newRate = await page.locator('[data-testid="funding-rate"]').textContent();
    expect(newRate).not.toBe(initialRate);
  });

  test('trade execution adds to history', async ({ page }) => {
    // Fill form
    await page.locator('[data-testid="amount-input"]').fill('10');
    
    // Get initial trade count
    const initialCount = await page.locator('[data-testid="trade-history-row"]').count();
    
    // Execute
    await page.locator('button:has-text("TRADE")').click();
    
    // Verify new trade added
    const newCount = await page.locator('[data-testid="trade-history-row"]').count();
    expect(newCount).toBe(initialCount + 1);
  });
  
  // ... more tests
});
```

---

## Next Time: Run Tests Again

After tests are generated and committed, running them next time is simple:

```bash
# Run single strategy tests
npx playwright test tests/e2e/strategies/defi/basis-trade.spec.ts

# Run all DeFi tests
npx playwright test tests/e2e/strategies/defi/

# With visual report
npx playwright test tests/e2e/strategies/defi/ --reporter=html
```

**Tests will automatically catch:**
- ❌ Widget UI broken
- ❌ Form inputs don't work
- ❌ Outputs don't update when inputs change
- ❌ Health factor / margin calculations wrong
- ❌ Trade execution broken
- ❌ Components removed or renamed

---

## Tips

1. **First strategy takes longest** (UI verification + test generation + fixes) ~10-15 min
2. **Subsequent strategies faster** (patterns reusable) ~5-8 min each
3. **Tests run fast** (Playwright headless) ~2-3 sec per strategy
4. **CI integration automatic** (tests commit to repo, run on every PR)
5. **Component changes easy** (if widget refactored, update test selectors once, tests catch future breaks)

---

## Next Steps

1. Choose a strategy from the list above
2. Tell the agent: `"Test {STRATEGY_NAME} end-to-end"`
3. Wait for completion
4. Tests will be in CI/CD ✅

---

## Troubleshooting

**"Widget not found"**
- Component doesn't exist yet
- Agent will create it as part of Phase 1

**"Test selector error"**
- Add `data-testid` attributes to component
- Agent will do this automatically

**"Test timeouts"**
- Widget taking too long to load
- Add explicit waits in beforeEach
- Agent will handle this

**"All tests pass locally but fail in CI"**
- Environment differences (localhost vs deployed)
- CI uses production URLs, not localhost:3100
- Agent will create correct URLs in test setup

---

## Plans Reference

- **Phase 1 only:** `defi-strategy-ui-verification.plan.md`
- **Full pipeline:** `defi-strategy-e2e-automation.plan.md`
- **This guide:** `defi-strategy-testing-quickstart.md`

---

**Ready? Pick a strategy and let's test it!** 🚀
