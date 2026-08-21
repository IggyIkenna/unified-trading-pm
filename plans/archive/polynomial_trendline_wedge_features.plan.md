---
doc_type: plan
title: Polynomial Trendline & Wedge Feature Calculator
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-06'
overview: 'Add multi-scale polynomial (quadratic) trendline calculators to features-delta-one-service,

  fitting separate curves to price highs (resistance) and lows (support). Validates curves by

  touch count, detects wedge patterns (converging curves), estimates bars-to-breakout via

  closed-form quadratic intersection, and adds cross-timeframe wedge confluence to

  features-multi-timeframe-service. A sweep of 6 named parameter combos produces 132 new

  columns total — ML model decides what''s most predictive.

  '
todos:
- {id: poly-calc-implementation, content: Implement PolynomialTrendlineCalculator in features-delta-one-service/features_delta_one_service/app/calculators/polynomial_trendline.py. Extend BaseFeatureCalculator (polars-based). Register as @FeatureCalculatorRegistry.register('polynomial_trendlines'). Compute support (local lows) and resistance (local highs) polynomial fits for all 6 POLY_COMBOS. Emit 84 curve columns (14 per combo)., status: done}
- {id: wedge-detector-implementation, content: Implement WedgeDetector in features-delta-one-service/features_delta_one_service/app/calculators/wedge_detector.py. Detect convergence of support and resistance curves. Compute bars_to_convergence via closed-form quadratic intersection formula. Classify wedge type (symmetric/ascending/descending). Emit 42 wedge columns (7 per combo)., status: done}
- {id: delta-one-schema-update, content: 'Update features-delta-one-service/features_delta_one_service/app/output_schemas.py. Add POLYNOMIAL_TRENDLINE_FEATURES (84 columns, generated from POLY_COMBOS) and WEDGE_FEATURES (42 columns). Append both to ALL_FEATURES.', status: done}
- {id: mtf-wedge-confluence, content: 'Implement WedgeConfluenceCalculator in features-multi-timeframe-service/features_multi_timeframe_service/app/calculators/wedge_confluence.py. Join wedge features at 1h/4h/1d timeframes. Emit wedge_confluence_1h_4h, wedge_confluence_1h_4h_1d, wedge_confluence_score, wedge_convergence_alignment binary events. Update MTF output_schemas.py.', status: done}
- {id: poly-unit-tests, content: 'Write 10 unit tests in features-delta-one-service/tests/unit/calculators/test_polynomial_trendline.py covering: insufficient touches → NaN, valid support fit, support break event, resistance break event, curvature sign, time-since delegation, no-lookahead, wedge convergence estimate, all 6 combos present in output, output columns match schema.', status: done}
- {id: poly-quality-gates, content: 'Run quality gates for both repos: ruff check, basedpyright strict (timeout 120), coverage ≥ 70%, no os.getenv/os.environ, no Any types, file size ≤ 900 lines per calculator file.', status: done}
isProject: false
---

# Polynomial Trendline & Wedge Feature Calculator

## Blockers

| Blocker                                            | Type          | Dependency                                                                                |
| -------------------------------------------------- | ------------- | ----------------------------------------------------------------------------------------- |
| `features-delta-one-service` output schema is live | `[INFRA]`     | New columns must be added to `output_schemas.py` before any downstream service reads them |
| MTF wedge confluence                               | `[PLAN_TODO]` | Depends on Parts 1–2 of this plan (delta-one poly + wedge columns must exist first)       |

## Done Criteria

| Criterion                     | Gate                                                              |
| ----------------------------- | ----------------------------------------------------------------- |
| `basedpyright` strict         | `timeout 120 basedpyright src/` exits 0, zero reportAny           |
| `ruff` clean                  | `ruff check src/` exits 0                                         |
| No `os.getenv` / `os.environ` | `rg 'os\.(getenv\|environ)' src/` empty                           |
| No `Any` types                | `rg ': Any\|-> Any' src/` empty                                   |
| Coverage ≥ 70%                | `pytest --cov=...polynomial_trendline --cov-fail-under=70`        |
| All output columns in schema  | `output_schemas.py` includes all poly + wedge columns             |
| File ≤ 900 lines              | calculator + wedge detector each ≤ 900 lines                      |
| Touch gate works              | Unit test: < min_touches → NaN, not values                        |
| Wedge convergence correct     | Unit test: converging synthetic curves → correct intersection bar |
| Break events fire             | Unit test: close < support*value → `poly*{c}\_support_break = 1`  |

## Core Insight

Fitting separate quadratic curves to highs and lows at multiple history lengths gives the ML model structured trendline
features at several timescales without config tuning. The wedge detector adds higher-order structure: when curves
converge, their geometric intersection forecasts breakout timing — a feature not present anywhere else in the system.
Running a sweep of 6 named combos means ML decides which scale is most predictive rather than the engineer guessing.

---

## Part 1 — Parameter Combos (Multi-Scale Sweep)

Define **6 named combos** in a `POLY_COMBOS` constant. Each combo:
`(fit_window, min_touches, local_window, touch_threshold_atr_mult)`.

```python
POLY_COMBOS: dict[str, tuple[int, int, int, float]] = {
    "micro":     (30,  3, 2, 0.5),   # very short-term parabolas
    "short":     (60,  4, 3, 0.5),   # short-term
    "medium":    (100, 5, 3, 0.5),   # standard
    "long":      (200, 7, 5, 0.5),   # long-term swing
    "sensitive": (100, 3, 2, 0.3),   # loose touch threshold
    "robust":    (150, 7, 5, 1.0),   # strict — only well-tested curves
}
```

Column names are prefixed by combo key: `poly_medium_support_value`, `poly_long_wedge_bars_to_convergence`, etc.

---

## Part 2 — PolynomialTrendlineCalculator

**File:** `features-delta-one-service/features_delta_one_service/app/calculators/polynomial_trendline.py`

**Base:** `BaseFeatureCalculator` (polars) | **Registered as:** `"polynomial_trendlines"`

### Algorithm (per combo, per bar)

```
SUPPORT CURVE (lows):
  1. Precompute local minima for full array: low[i] == min(low[i-local_window : i+local_window+1])
     Use scipy.signal.argrelextrema (vectorized — avoids per-bar re-scan)
  2. For current bar: slice local minima within rolling [x-fit_window, x] → (x_idx, low) pairs
  3. If len(pairs) < min_touches: emit NaN for all poly_{c}_support_* columns, valid=0, skip
  4. numpy.polyfit(x_idx, low_prices, deg=2) → [a, b, c]
  5. Evaluate curve at all x in window → curve_values array
  6. Recount touches: bars where abs(low - curve) < touch_threshold * ATR_20
  7. If touch_count < min_touches: NaN + valid=0
  8. Extrapolate: support_value = a*x² + b*x + c  at current x
  9. slope = 2*a*x + b   (first derivative)
  10. curvature = 2*a    (second derivative; +ve = concave up)
  11. distance_pct = (close - support_value) / close * 100
  12. break = 1 if close < support_value else 0  ← binary event → time_since pipeline

RESISTANCE CURVE (highs):
  Same using `high` + local maxima.
  break = 1 if close > resistance_value else 0
```

### Output Features: 14 columns × 6 combos = 84 total

| Pattern                            | Type    | Description                              |
| ---------------------------------- | ------- | ---------------------------------------- |
| `poly_{c}_support_value`           | Float64 | Extrapolated support at current bar      |
| `poly_{c}_support_slope`           | Float64 | First derivative (curve velocity)        |
| `poly_{c}_support_curvature`       | Float64 | Second derivative; +ve = concave up      |
| `poly_{c}_support_distance_pct`    | Float64 | % gap: (close − curve) / close           |
| `poly_{c}_support_touches`         | Int32   | Validated touch count in window          |
| `poly_{c}_support_valid`           | Int8    | 1 if touches ≥ min_touches               |
| `poly_{c}_support_break`           | Int8    | Binary break event → time_since pipeline |
| `poly_{c}_resistance_value`        | Float64 |                                          |
| `poly_{c}_resistance_slope`        | Float64 |                                          |
| `poly_{c}_resistance_curvature`    | Float64 |                                          |
| `poly_{c}_resistance_distance_pct` | Float64 |                                          |
| `poly_{c}_resistance_touches`      | Int32   |                                          |
| `poly_{c}_resistance_valid`        | Int8    |                                          |
| `poly_{c}_resistance_break`        | Int8    | Binary break event → time_since pipeline |

**Auto-generated by base class pipeline** (no extra code): `time_since_poly_{c}_support_break`,
`time_since_poly_{c}_resistance_break`, `time_since_poly_{c}_support_valid`, `time_since_poly_{c}_resistance_valid`

---

## Part 3 — WedgeDetector

**File:** `features-delta-one-service/features_delta_one_service/app/calculators/wedge_detector.py`

Called from `PolynomialTrendlineCalculator` after both curves computed.

### Wedge Algorithm (per combo, per bar)

```
INPUTS: [a_s, b_s, c_s] (support) and [a_r, b_r, c_r] (resistance), both valid

CONVERGENCE:
  current_gap = resistance_value_now - support_value_now
  past_gap    = resistance_value[x - fit_window//4] - support_value[x - fit_window//4]
  converging  = 0 < current_gap < past_gap

BREAKOUT TIMING (closed-form quadratic intersection):
  (a_s - a_r)*x² + (b_s - b_r)*x + (c_s - c_r) = 0
  discriminant = (b_s-b_r)² - 4*(a_s-a_r)*(c_s-c_r)
  If discriminant < 0: bars_to_convergence = NaN  (curves never meet)
  Else: take root > current_x; bars_to_convergence = root - current_x

WEDGE TYPE:
  support_slope > 0 AND resistance_slope < 0 → symmetric (1)
  support_slope > 0 AND resistance_slope ≥ 0 → ascending (2)
  support_slope ≤ 0 AND resistance_slope < 0 → descending (3)
  else → invalid (0)
```

### Output Features: 7 columns × 6 combos = 42 total

| Pattern                              | Type    | Description                                       |
| ------------------------------------ | ------- | ------------------------------------------------- |
| `poly_{c}_wedge_valid`               | Int8    | 1 if both curves valid and converging             |
| `poly_{c}_wedge_type`                | Int8    | 0=invalid, 1=symmetric, 2=ascending, 3=descending |
| `poly_{c}_wedge_current_gap_pct`     | Float64 | (resistance − support) / close %                  |
| `poly_{c}_wedge_compression_ratio`   | Float64 | current_gap / past_gap (< 1 = compressing)        |
| `poly_{c}_wedge_bars_to_convergence` | Float64 | Extrapolated bars until curve intersection        |
| `poly_{c}_wedge_total_touches`       | Int32   | support_touches + resistance_touches              |
| `poly_{c}_wedge_breakout_imminent`   | Int8    | 1 if bars_to_convergence < 10 (binary event)      |

**Auto-generated:** `time_since_poly_{c}_wedge_breakout_imminent`

**Grand total: 126 columns** (84 curve + 42 wedge) across 6 combos.

---

## Part 4 — Multi-Timeframe Wedge Confluence

**File:** `features-multi-timeframe-service/features_multi_timeframe_service/app/calculators/wedge_confluence.py`

Consumes poly features at 1h / 4h / 1d. For each combo, checks if 2+ timeframes simultaneously show
`poly_{c}_wedge_valid=1` with matching `wedge_type`. Emits:

```python
WEDGE_CONFLUENCE_FEATURES = [
    "wedge_confluence_1h_4h",       # Int8: binary event → time_since
    "wedge_confluence_1h_4h_1d",    # Int8: binary event → time_since
    "wedge_confluence_score",       # Int8: count of TFs with valid wedge (0–3)
    "wedge_convergence_alignment",  # Int8: all valid TFs agree on wedge_type
    "time_since_wedge_confluence_1h_4h",    # auto from binary
    "time_since_wedge_confluence_1h_4h_1d", # auto from binary
]
```

---

## Part 5 — Unit Tests

**File:** `features-delta-one-service/tests/unit/calculators/test_polynomial_trendline.py`

| #   | Test                  | Assert                                                                       |
| --- | --------------------- | ---------------------------------------------------------------------------- |
| 1   | Insufficient touches  | `poly_medium_support_value` is NaN                                           |
| 2   | Valid support fit     | value in price range, touches ≥ 5                                            |
| 3   | Support break         | close < support_value → `poly_medium_support_break = 1`                      |
| 4   | Resistance break      | close > resistance_value → `poly_medium_resistance_break = 1`                |
| 5   | Curvature sign        | bowl-up: curvature > 0; arch-down: curvature < 0                             |
| 6   | Time-since delegation | `time_since_poly_medium_support_break` in output, NaN before first break     |
| 7   | No lookahead          | fit window contains only rows ≤ current index                                |
| 8   | Wedge convergence     | two synthetic converging lines → correct intersection bar                    |
| 9   | All 6 combos          | output has columns for all combo keys in `POLY_COMBOS`                       |
| 10  | Schema match          | `set(output.columns) == set(POLYNOMIAL_TRENDLINE_FEATURES + WEDGE_FEATURES)` |

---

## Part 6 — Performance Notes

- **Local extrema**: `scipy.signal.argrelextrema` (vectorized once for full array; then slice per bar)
- **Polynomial fit**: `numpy.polyfit` (C-backed; no numba needed initially)
- **Wedge intersection**: pure arithmetic (quadratic formula) — no iterative solve
- **Batch combos**: loop over `POLY_COMBOS.items()` in a single pass per bar (amortize Python overhead)
- **`numpy.RankWarning`** (rank-deficient fit) → catch → return NaN row, log at DEBUG
- `numpy` + `scipy` should already be in `pyproject.toml`; verify before adding

---

## Architecture Summary

```
features-delta-one-service
  calculators/
    polynomial_trendline.py   ← NEW  (84 curve columns, 6 combos)
    wedge_detector.py         ← NEW  (42 wedge columns)
  output_schemas.py           ← ADD 126 columns

features-multi-timeframe-service
  calculators/
    wedge_confluence.py       ← NEW  (6 confluence columns)
  output_schemas.py           ← ADD 6 columns
```

```
OHLCV candles
  → PolynomialTrendlineCalculator (6 combos × 14 = 84)
       → WedgeDetector (6 combos × 7 = 42)
  → BaseClass pipeline: time_since_* auto for all binary columns
  → features-multi-timeframe-service
       → WedgeConfluenceCalculator (6 columns, MTF join)
```

---

## Verification

```bash
cd features-delta-one-service
ruff check src/
timeout 120 basedpyright src/
pytest tests/unit/calculators/test_polynomial_trendline.py -v
pytest --cov=features_delta_one_service.app.calculators.polynomial_trendline \
       --cov=features_delta_one_service.app.calculators.wedge_detector \
       --cov-fail-under=70
rg 'os\.(getenv|environ)' src/
rg ': Any|-> Any' src/
wc -l src/features_delta_one_service/app/calculators/polynomial_trendline.py
wc -l src/features_delta_one_service/app/calculators/wedge_detector.py

cd ../features-multi-timeframe-service
ruff check src/
timeout 120 basedpyright src/
pytest tests/unit/calculators/test_wedge_confluence.py -v
```
