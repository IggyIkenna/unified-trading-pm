# Trader Acceptance Test (TAT) Checklist

**Purpose:** Manual UAT walkthrough for the Unified Trading System UIs. Run all UIs in mock mode before starting:

```bash
bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock
```

---

## Per-UI Checklist

Repeat the following for each of the 12 UIs listed below.

| #   | UI                     | Port |
| --- | ---------------------- | ---- |
| 1   | batch-audit-ui         | 5174 |
| 2   | client-reporting-ui    | 5175 |
| 3   | deployment-ui          | 5176 |
| 4   | execution-analytics-ui | 5177 |
| 5   | live-health-monitor-ui | 5178 |
| 6   | logs-dashboard-ui      | 5179 |
| 7   | ml-training-ui         | 5180 |
| 8   | onboarding-ui          | 5181 |
| 9   | settlement-ui          | 5182 |
| 10  | strategy-ui            | 5183 |
| 11  | trading-analytics-ui   | 5173 |
| 12  | unified-admin-ui       | 5184 |

---

### 1. batch-audit-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 2. client-reporting-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 3. deployment-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 4. execution-analytics-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 5. live-health-monitor-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 6. logs-dashboard-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 7. ml-training-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 8. onboarding-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 9. settlement-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 10. strategy-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 11. trading-analytics-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

### 12. unified-admin-ui

- [ ] Page loads without errors in mock mode
- [ ] All tabs/routes navigable without blank screens
- [ ] Data tables display realistic mock data (not empty, not placeholder)
- [ ] Numbers use tabular figures and are right-aligned
- [ ] P&L values are color-coded (green positive, red negative)
- [ ] Responsive: no crumpling at 1024px, 768px widths
- [ ] Search/filter controls work
- [ ] Loading states visible when VITE_MOCK_DELAY_MS=2000
- [ ] Stress scenarios don't crash (VITE_STRESS_SCENARIO=BIG_DRAWDOWN)
- [ ] Health status bar visible and accurate
- [ ] No console errors in browser dev tools

---

## Cross-UI Checklist

- [ ] Cross-UI navigation links work between all UIs
- [ ] Config links (strategy -> onboarding, health -> risk) navigate correctly
- [ ] Consistent look and feel across all UIs (same dark theme, same typography, same spacing)
- [ ] Mock mode indicator visible on every page

---

## Data Quality Checklist

- [ ] Positions show multi-client, multi-strategy data
- [ ] P&L waterfall shows attribution buckets
- [ ] Backtest results load with equity curves
- [ ] Deployment history shows realistic entries
- [ ] Alert history shows triggered and resolved alerts

---

## How to Run

### Full mock mode (all UIs):

```bash
bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock
```

### Test loading states:

```bash
VITE_MOCK_DELAY_MS=2000 bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock
```

### Test stress scenarios:

```bash
VITE_STRESS_SCENARIO=BIG_DRAWDOWN bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock
```

### Stop all:

```bash
bash unified-trading-pm/scripts/dev/dev-stop.sh
```

---

## Sign-Off

| Role     | Name | Date | Result      |
| -------- | ---- | ---- | ----------- |
| Tester   |      |      | PASS / FAIL |
| Reviewer |      |      | PASS / FAIL |
