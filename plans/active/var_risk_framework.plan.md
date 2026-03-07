---
name: VaR/CVaR Risk Framework
overview: |
  Implement a production-grade Value-at-Risk (VaR) and Conditional Value-at-Risk (CVaR)
  framework in risk-and-exposure-service. Covers parametric VaR, historical VaR, CVaR,
  multi-horizon scaling (1-day, 10-day), stress scenario simulation (GFC_2008,
  COVID_2020, CRYPTO_BLACK_THURSDAY_2020), and pre-trade VaR limit enforcement via the
  existing PreTradeCheckEngine. All calculations are pure-function stdlib-only — no
  ML/stats libraries, no I/O.
todos:
  - id: var-calculator-core
    content:
      "Implement risk-and-exposure-service/risk_and_exposure_service/core/var_calculator.py with four pure functions:
      historical_var(returns, confidence, horizon_days), parametric_var(returns, confidence, horizon_days),
      cvar(returns, confidence, horizon_days), stress_var(returns, scenario). Use stdlib statistics + math only. No Any
      types. No I/O. Confidence defaults: 0.99. Horizon defaults: 1-day; 10-day via sqrt(10) scaling."
    status: completed
  - id: var-cvar-stress-tests
    content:
      "Write tests/unit/core/test_var_calculator.py covering: (1) historical_var returns negative float for known-loss
      returns list, (2) parametric_var for normal distribution, (3) cvar >= var in absolute value (CVaR always at least
      as bad), (4) 10-day scaling = sqrt(10) * 1-day VaR, (5) stress_var returns larger loss than historical_var for
      same returns, (6) all three stress scenarios (GFC_2008, COVID_2020, CRYPTO_BLACK_THURSDAY_2020) execute without
      error."
    status: completed
  - id: var-pretrade-integration
    content:
      "Integrate VaR limit enforcement into PreTradeCheckEngine._run_all_checks(): add a var_limit check that calls
      historical_var() on recent returns and rejects the trade if the resulting VaR exceeds the configured var_limit
      (from RiskLimits or config). Emit PRE_TRADE_VAR_BREACH event via log_event() on rejection. Add var_limit field to
      RiskLimits model or read from config."
    status: pending
  - id: var-api-endpoint
    content:
      "Add GET /risk/var endpoint to risk-and-exposure-service/api/main.py. Request params: client_id, confidence
      (default 0.99), horizon_days (default 1), scenario (optional). Returns: {var: float, cvar: float, stress_var:
      float | None, confidence: float, horizon_days: int}. Fetch recent returns from position-monitor-service or accept
      returns[] in request body. Wire through existing FastAPI router pattern."
    status: pending
  - id: var-coverage-gate
    content:
      "Achieve >=70% test coverage on var_calculator.py and the updated pre_trade_check_engine.py. Run: pytest
      tests/unit/ --cov=risk_and_exposure_service/core/var_calculator
      --cov=risk_and_exposure_service/core/pre_trade_check_engine --cov-report=term-missing. Confirm all VaR/CVaR
      branches are hit."
    status: pending
isProject: false
---

# VaR/CVaR Risk Framework

**Day:** 9–11 (March 13–15) **Scope:** risk-and-exposure-service (var_calculator.py, pre-trade integration, API
endpoint, tests) **Blocks:** Phase 1 live trading readiness; safety_and_risk_controls.plan.md risk-test-coverage gate
**Owner:** Person B

---

## Purpose

Quantify portfolio loss risk using statistically rigorous methods. VaR answers: "What is the maximum expected loss over
N days at X% confidence?" CVaR (Expected Shortfall) answers: "Given that we exceed VaR, what is the average loss?"
Stress VaR stress-tests the portfolio under historical crisis multipliers.

---

## Design

### Confidence Levels

| Level | Interpretation                              |
| ----- | ------------------------------------------- |
| 95%   | 95 out of 100 days losses do not exceed VaR |
| 99%   | 99 out of 100 days losses do not exceed VaR |

### Horizons

| Horizon | Scaling method                            |
| ------- | ----------------------------------------- |
| 1-day   | Raw VaR from daily returns distribution   |
| 10-day  | `VaR_10d = VaR_1d * sqrt(10)` (Basel III) |

### Stress Scenarios

| Scenario                     | Multiplier | Basis                                         |
| ---------------------------- | ---------- | --------------------------------------------- |
| `GFC_2008`                   | 3.5x       | S&P 500 peak-to-trough drawdown ~57%          |
| `COVID_2020`                 | 2.5x       | March 2020 30-day drawdown ~34%               |
| `CRYPTO_BLACK_THURSDAY_2020` | 5.0x       | BTC/ETH single-day drop ~50% (March 12, 2020) |

Stress VaR = `historical_var(returns, confidence=0.99) * multiplier`

---

## Implementation Location

| Artifact              | Path                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------ |
| Core calculator       | `risk-and-exposure-service/risk_and_exposure_service/core/var_calculator.py`         |
| Pre-trade integration | `risk-and-exposure-service/risk_and_exposure_service/core/pre_trade_check_engine.py` |
| API endpoint          | `risk-and-exposure-service/risk_and_exposure_service/api/main.py`                    |
| Unit tests            | `risk-and-exposure-service/tests/unit/core/test_var_calculator.py`                   |

---

## API Spec

```
GET /risk/var?client_id=&confidence=0.99&horizon_days=1&scenario=GFC_2008

Response 200:
{
  "var": -12500.00,
  "cvar": -15200.00,
  "stress_var": -43750.00,
  "confidence": 0.99,
  "horizon_days": 1,
  "scenario": "GFC_2008"
}
```

---

## Blockers

| Blocker                                        | Type       | Resolution                                                                                       |
| ---------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------ |
| Returns data source not defined                | `[DESIGN]` | Phase 1: accept returns[] in request body. Phase 2: fetch from position-monitor returns history. |
| RiskLimits model does not have var_limit field | `[STUB]`   | Add var_limit: Decimal field to RiskLimits or read from UnifiedCloudConfig as config default.    |

---

## Gate Criteria

- [x] `var_calculator.py` implemented: historical_var, parametric_var, cvar, stress_var all present
- [x] All four methods are pure functions (no I/O, no side effects, no external deps beyond stdlib)
- [x] No `Any` types anywhere in var_calculator.py
- [x] `test_var_calculator.py` passes all 6 test cases
- [x] CVaR >= VaR in absolute value for all test inputs (invariant enforced by test)
- [x] 10-day VaR = sqrt(10) \* 1-day VaR (within floating-point tolerance, tested)
- [x] All three stress scenarios execute without error
- [ ] Pre-trade check engine rejects trades breaching var_limit (PRE_TRADE_VAR_BREACH emitted)
- [ ] GET /risk/var endpoint returns correct structure
- [ ] > =70% coverage on var_calculator.py confirmed
