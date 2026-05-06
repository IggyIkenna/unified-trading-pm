---
orphan_candidate: true
orphan_reason:
  "Workflow/process guide (446 lines, 0 checkboxes, no frontmatter). Belongs in codex/14-playbooks/ or
  codex/08-workflows/, not plans/active/."
reconciliation_date: 2026-04-25
---

> **ORPHAN CANDIDATE 2026-04-25.** Scope appears unconnected to the live system. Reason: Workflow/process guide (446
> lines, 0 checkboxes, no frontmatter). Belongs in codex/14-playbooks/ or codex/08-workflows/, not plans/active/. See
> `_reconciliation_evidence_map_2026_04_25.md` for the integration check.

# DeFi Strategy E2E Testing Automation

**Objective:** Complete automation pipeline for DeFi strategy UI verification → E2E test generation → test execution →
regression protection.

**Scope:** Any strategy in `/codex/09-strategy/defi/` folder

**Output:**

1. UI readiness report
2. Generated Playwright E2E test file
3. Test execution results
4. Committed changes (fixtures + tests)

---

## Phase 1: UI Readiness Verification

Execute: `defi-strategy-ui-verification.plan.md`

**Deliverables:**

- ✅ Widget component verified
- ✅ Mock data verified/created
- ✅ Dynamic input → output tested
- ✅ Trade execution tested
- ✅ Readiness report generated

**Output files after Phase 1:**

- `lib/mocks/fixtures/defi-{strategy}.ts` (mock data - may be created/updated)
- `components/widgets/defi/{widget}.tsx` (component - verified working)
- Console: "UI Readiness: READY / IN_PROGRESS / BLOCKED"

---

## Phase 2: Generate Playwright E2E Tests

Based on the strategy spec and Phase 1 test results, automatically generate comprehensive E2E tests.

### Task 2.1: Parse Test Cases from Phase 1

From the UI verification, extract:

- **Form inputs tested:** amount, asset, protocol, operation, slippage
- **Output assertions:** expected_output, health_factor, apy_rates
- **Operations tested:** LEND, BORROW, WITHDRAW, REPAY (or relevant to strategy)
- **Edge cases found:** zero amount, rapid changes, protocol switch
- **Trade execution:** execute button → trade history update

### Task 2.2: Generate Test File Structure

```
File: `tests/e2e/strategies/defi/{strategy}.spec.ts`

Structure:
├── Test Suite: "DeFi {STRATEGY_NAME} UI E2E"
│   ├── beforeEach: Navigate to widget, setup browser context
│   ├── Test 1: Widget renders with initial state
│   ├── Test 2: Form inputs accept values
│   ├── Test 3: Asset selection updates APY
│   ├── Test 4: Amount changes update expected output
│   ├── Test 5: Expected output differs by operation
│   ├── Test 6: Health factor updates correctly
│   ├── Test 7: Operation type affects calculations
│   ├── Test 8: Trade execution works
│   ├── Test 9: Trade appears in history
│   ├── Test 10: Edge cases (zero, rapid changes, etc.)
│   └── afterEach: Cleanup
```

### Task 2.3: Template E2E Test Generation

Generate tests following this pattern:

**Test 1: Widget Renders**

```typescript
test("widget renders with initial state", async ({ page }) => {
  await page.goto("/services/trading/defi");
  await expect(page.locator('[data-testid="defi-lending-widget"]')).toBeVisible();
  await expect(page.locator("text=Protocol")).toBeVisible();
  await expect(page.locator("text=Amount")).toBeVisible();
});
```

**Test 2: Asset Selection → APY Updates**

```typescript
test("asset selection updates APY display", async ({ page }) => {
  await page.goto("/services/trading/defi");

  // Get initial APY for ETH
  const initialApy = await page.locator("text=Supply").first().textContent();

  // Switch asset to USDC
  await page.locator('[data-testid="asset-select"]').click();
  await page.locator("text=USDC").click();

  // Verify APY changed
  const newApy = await page.locator("text=Supply").first().textContent();
  expect(newApy).not.toBe(initialApy);
});
```

**Test 3: Amount → Expected Output Updates**

```typescript
test("amount input updates expected output", async ({ page }) => {
  await page.goto("/services/trading/defi");

  // Enter amount 10
  await page.locator('[data-testid="amount-input"]').fill("10");
  let expectedOutput = await page.locator("text=Expected output").nth(1).textContent();
  expect(expectedOutput).toContain("9.95"); // 10 * (1 - 0.005 slippage)

  // Change to 20
  await page.locator('[data-testid="amount-input"]').clear();
  await page.locator('[data-testid="amount-input"]').fill("20");
  expectedOutput = await page.locator("text=Expected output").nth(1).textContent();
  expect(expectedOutput).toContain("19.90"); // 20 * (1 - 0.005 slippage)
});
```

**Test 4: Operation Type → Expected Output Format**

```typescript
test("operation type determines expected output format", async ({ page }) => {
  await page.goto("/services/trading/defi");

  // LEND: should show aToken
  await page.locator('button:has-text("LEND")').click();
  await page.locator('[data-testid="amount-input"]').fill("13");
  let output = await page.locator("text=Expected output").nth(1).textContent();
  expect(output).toMatch(/a[A-Z]+/); // aETH, aUSDC, etc.

  // WITHDRAW: should show underlying + yield
  await page.locator('button:has-text("WITHDRAW")').click();
  output = await page.locator("text=Expected output").nth(1).textContent();
  const amount = parseFloat(output!);
  expect(amount).toBeGreaterThan(13); // Includes yield
});
```

**Test 5: Health Factor Updates by Asset**

```typescript
test("health factor updates correctly per asset", async ({ page }) => {
  await page.goto("/services/trading/defi");

  await page.locator('button:has-text("LEND")').click();
  await page.locator('[data-testid="amount-input"]').fill("13");

  // Get HF change for ETH (high collateral factor)
  const ethHf = await page.locator('[data-testid="after-hf"]').textContent();

  // Switch to USDT (lower collateral factor)
  await page.locator('[data-testid="asset-select"]').click();
  await page.locator("text=USDT").click();

  const usdtHf = await page.locator('[data-testid="after-hf"]').textContent();

  // ETH should improve HF more than USDT
  expect(parseFloat(ethHf!)).toBeGreaterThan(parseFloat(usdtHf!));
});
```

**Test 6: Trade Execution → History Update**

```typescript
test("executing trade adds it to history", async ({ page }) => {
  await page.goto("/services/trading/defi");

  await page.locator('button:has-text("LEND")').click();
  await page.locator('[data-testid="amount-input"]').fill("10");

  // Get initial trade count
  const initialCount = await page.locator('[data-testid="trade-history-row"]').count();

  // Execute trade
  await page.locator('button:has-text("LEND")').last().click(); // Execute button

  // Wait for trade to appear
  await page.waitForTimeout(500);

  // Verify new row added
  const newCount = await page.locator('[data-testid="trade-history-row"]').count();
  expect(newCount).toBe(initialCount + 1);

  // Verify trade details
  const lastRow = page.locator('[data-testid="trade-history-row"]').last();
  await expect(lastRow.locator("text=LEND")).toBeVisible();
  await expect(lastRow.locator("text=10")).toBeVisible();
});
```

---

## Phase 3: Test File Creation & Execution

### Task 3.1: Create Test File

- Generate `tests/e2e/strategies/defi/{strategy}.spec.ts`
- Ensure all test cases from Phase 1 are covered
- Add data-testid attributes to component if missing
- Use consistent naming: `{strategy}-{test-case}`

### Task 3.2: Run Generated Tests

```bash
npx playwright test tests/e2e/strategies/defi/{strategy}.spec.ts
```

**Success criteria:**

- ✅ All tests pass on first run
- ✅ No timeout errors
- ✅ No selector errors
- ✅ No assertion failures

### Task 3.3: Generate Test Report

- Test count: X passed, 0 failed
- Execution time: YYs
- Coverage: All form inputs, all operations, all outputs
- Visual regression: None detected

---

## Phase 4: Component Updates (if needed)

If tests fail due to missing selectors, update component:

### Task 4.1: Add Test Identifiers

```tsx
// Add to widget components
<div data-testid="defi-lending-widget">
  <input data-testid="amount-input" />
  <select data-testid="asset-select" />
  <button data-testid="execute-trade-button" />
  <div data-testid="expected-output">...</div>
  <div data-testid="current-hf">...</div>
  <div data-testid="after-hf">...</div>
  <div data-testid="trade-history-row" />
</div>
```

### Task 4.2: Ensure State Management

- Verify state updates trigger re-renders
- Ensure trade history appends (not replaces)
- Confirm health factor recalculates on input change

---

## Phase 5: Commit & Documentation

### Task 5.1: Commit Changes

```bash
git add lib/mocks/fixtures/defi-{strategy}.ts
git add components/widgets/defi/{widget}.tsx
git add tests/e2e/strategies/defi/{strategy}.spec.ts
git commit -m "feat({strategy}): UI verification + E2E tests for {STRATEGY_NAME}

- Verified {STRATEGY_NAME} widget with dynamic form testing
- Created mock data: collateral factors, APY rates, asset prices
- Generated 10+ Playwright E2E tests covering all operations
- All tests passing: form inputs, output propagation, trade execution
- Ready for regression testing in CI/CD pipeline"
```

### Task 5.2: Update Test Index

File: `tests/e2e/strategies/defi/README.md`

Add entry:

```markdown
## {STRATEGY_NAME}

**File:** `{strategy}.spec.ts` **Status:** ✅ Ready **Coverage:** 10 tests

- Widget rendering
- Form inputs (amount, asset, operation, slippage)
- Output propagation (expected_output, APY, health factor)
- Health factor by asset (collateral factor applied)
- Trade execution & history
- Edge cases (zero amount, rapid changes) **Last verified:** {TODAY} **Last run:**
  `npx playwright test tests/e2e/strategies/defi/{strategy}.spec.ts`
```

### Task 5.3: Document Test Patterns

Create file: `tests/e2e/strategies/defi/PATTERNS.md`

Document reusable test patterns:

- Asset selection → output update
- Amount change → expected output scales
- Operation type → output format differs
- Health factor → asset collateral factor applied
- Trade execution → history append

---

## Execution Flow (Complete Pipeline)

```
User Input: "Verify and test {STRATEGY_NAME}"
    ↓
Phase 1: UI Readiness Verification
    ├─ Read spec
    ├─ Check components
    ├─ Test form interactions
    ├─ Verify outputs update dynamically
    └─ Report: READY / BLOCKED
    ↓
Phase 2: Generate E2E Tests
    ├─ Parse test cases from Phase 1
    ├─ Generate test file
    ├─ Add test identifiers to component
    └─ Create test templates
    ↓
Phase 3: Run Tests
    ├─ Execute Playwright tests
    ├─ Verify all pass
    ├─ Generate coverage report
    └─ Log execution time
    ↓
Phase 4: Fix Failures (if any)
    ├─ Update component selectors
    ├─ Fix state management issues
    ├─ Re-run tests
    └─ Confirm all pass
    ↓
Phase 5: Commit & Document
    ├─ Git commit with conventional format
    ├─ Update test index
    ├─ Document patterns
    └─ Report: "✅ Complete"
    ↓
Output: Strategy is now protected by E2E tests
        Future changes will be caught by CI/CD
```

---

## Test File Template

```typescript
import { test, expect } from "@playwright/test";

/**
 * DeFi {STRATEGY_NAME} UI E2E Tests
 *
 * This test suite was auto-generated by the DeFi Strategy E2E Automation plan.
 * It verifies that:
 * 1. Form inputs (amount, asset, operation, slippage) work correctly
 * 2. Output values update when inputs change
 * 3. Expected output differs by operation type
 * 4. Health factor updates per asset collateral factor
 * 5. Trade execution updates history
 *
 * To run: npx playwright test tests/e2e/strategies/defi/{strategy}.spec.ts
 */

test.describe("DeFi {STRATEGY_NAME} UI E2E", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to widget
    await page.goto("http://localhost:3100/services/trading/defi");

    // Wait for widget to load
    await expect(page.locator('[data-testid="defi-{strategy}-widget"]')).toBeVisible({ timeout: 5000 });
  });

  // Tests generated from Phase 1 verification
  // {TEST_CASES_HERE}
});
```

---

## Success Criteria

✅ **Phase 1:** UI readiness READY + all dynamic tests pass ✅ **Phase 2:** Test file generated with 10+ test cases ✅
**Phase 3:** All tests execute and pass in Playwright ✅ **Phase 4:** No failures requiring fixes ✅ **Phase 5:** Code
committed with conventional message + tests in CI/CD

---

## Regression Testing (Next Time)

After setup is complete, next time just run:

```bash
# Run single strategy tests
npx playwright test tests/e2e/strategies/defi/{strategy}.spec.ts

# Run all DeFi strategy tests
npx playwright test tests/e2e/strategies/defi/

# With reporter
npx playwright test tests/e2e/strategies/defi/ --reporter=html
```

Tests will catch:

- ❌ Form inputs broken (input not accepting values)
- ❌ Outputs not updating (amount entered but expected_output unchanged)
- ❌ Health factor not calculating (operation doesn't affect HF)
- ❌ Trade execution broken (button click doesn't add to history)
- ❌ Component removed or renamed (selectors fail)

---

## Notes

- **Test IDs:** Component must have `data-testid` attributes for Playwright selectors to work
- **Timing:** Tests should wait for state updates (use `waitForTimeout()` or `waitForSelector()`)
- **Isolation:** Each test is independent; beforeEach resets state
- **CI Integration:** These tests run automatically on PR to catch regressions
- **Maintenance:** If component changes, update selectors in tests (IDE refactor will help)

---

## Example Output

```
Running 10 tests from tests/e2e/strategies/defi/aave-lending.spec.ts

✅ widget renders with initial state (245ms)
✅ asset selection updates APY display (312ms)
✅ amount input updates expected output (198ms)
✅ expected output differs by operation (426ms)
✅ health factor updates by asset (567ms)
✅ amount scales output proportionally (213ms)
✅ operation type affects health factor direction (342ms)
✅ trade execution adds to history (298ms)
✅ trade history shows correct sequence (156ms)
✅ edge case: zero amount disables button (124ms)

Test run complete: 10 passed, 0 failed (3.3s)
Coverage: All form inputs, all outputs, all operations verified ✅
```
