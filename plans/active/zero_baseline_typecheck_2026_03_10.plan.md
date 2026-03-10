# Zero Baseline Typecheck — Full Remediation Plan

**Created:** 2026-03-10 **Status:** IN PROGRESS **SSOT-INDEX:** register under `08-type-safety` **Linked codex
section:** `unified-trading-codex/06-coding-standards/README.md`

## Goal

Eliminate ALL `.basedpyright-baseline.json` suppression across every repo. Every repo must pass
`basedpyright <source_dir>/` with **0 errors and an empty (or absent) baseline file**. This makes `reportAny = "error"`,
`reportUnknownMemberType = "error"`, etc. truly enforced — no hidden violations.

## Current State (2026-03-10)

| Repo                              | Baseline Errors | Root Cause                                                             |
| --------------------------------- | --------------- | ---------------------------------------------------------------------- |
| execution-service                 | 15,231          | nautilus stubs return `object`; internal algorithms/engine unannotated |
| deployment-api                    | 2,962           | google-auth/redis/cachetools untyped; internal code unannotated        |
| market-data-processing-service    | 1,348           | polars/pyarrow/numba untyped; pandas cascade                           |
| ml-training-service               | 504             | scipy/lightgbm/ta-lib no stubs; shap untyped                           |
| features-sports-service           | 429             | unified-feature-calculator internal lib untyped                        |
| execution-results-api             | 39              | unused imports, private API access, unnecessary casts                  |
| unified-trade-execution-interface | 32              | ccxt/ib_insync no stubs; aiohttp param mismatches                      |
| strategy-service                  | 3               | unused import + 2 numpy/scipy `reportAny` in math_utilities            |
| **TOTAL**                         | **20,548**      |                                                                        |

---

## Phase 1 — Trivial Repos (74 errors) ✅ Target: 0

### strategy-service (3 errors)

- [ ] `strategy_service/cli/main.py`: delete unused import (1 `reportAny`)
- [ ] `strategy_service/engine/core/components/math_utilities.py`: type numpy/scipy returns (2 `reportAny`)
- [ ] Delete `.basedpyright-baseline.json`
- [ ] Commit: `fix: zero basedpyright baseline in strategy-service`

### execution-results-api (39 errors)

- [ ] Remove unused imports in `execution_results_api/main.py`
- [ ] Replace private FastAPI access with public APIs
- [ ] Remove unnecessary cast in `analysis_service.py`
- [ ] Fix remaining ~36 errors with proper type annotations
- [ ] Delete `.basedpyright-baseline.json`
- [ ] Commit: `fix: zero basedpyright baseline in execution-results-api`

### unified-trade-execution-interface (32 errors)

- [ ] Define `Protocol` for ccxt.Exchange fields actually accessed
- [ ] Define `Protocol` for ib_insync contract objects
- [ ] Fix aiohttp/httpx parameter type mismatches (11 `reportArgumentType`)
- [ ] Delete `.basedpyright-baseline.json`
- [ ] Commit: `fix: zero basedpyright baseline in unified-trade-execution-interface`

---

## Phase 2 — Expand Nautilus Stubs (−3,000+ errors in execution-service)

### `stubs/nautilus_trader/cache.pyi`

- [ ] `Cache.account(venue) -> Account | None` (was `object`)
- [ ] `Cache.positions() -> list[Position]` (was `list[object]`)
- [ ] `Cache.orders() -> list[Order]`
- [ ] `Cache.order(client_order_id) -> Order | None`
- [ ] `Cache.instrument(instrument_id) -> Instrument | None`
- [ ] `Cache.instruments() -> list[Instrument]`
- [ ] `Cache.bar(bar_type) -> Bar | None`
- [ ] `Cache.quote_tick(instrument_id) -> QuoteTick | None`
- [ ] `Cache.trade_tick(instrument_id) -> TradeTick | None`

### `stubs/nautilus_trader/model/objects.pyi`

- [ ] `Price.__mul__` → `Price` (was `float`)
- [ ] `Price.__add__` → `Price`
- [ ] `Price.__sub__` → `Price`
- [ ] `Price.__truediv__` → `Decimal`
- [ ] `Quantity.__mul__` → `Quantity` (was `float`)
- [ ] `Quantity.__add__` → `Quantity`
- [ ] `Money.__add__` → `Money`
- [ ] `Money.__sub__` → `Money`

### `stubs/nautilus_trader/model/events.pyi` (new or expand)

- [ ] `OrderAccepted`, `OrderRejected`, `OrderFilled`
- [ ] `OrderCanceled`, `OrderExpired`, `OrderModifyRejected`
- [ ] `PositionOpened`, `PositionChanged`, `PositionClosed`

### New stub files

- [ ] `stubs/nautilus_trader/model/portfolio.pyi` — Portfolio class with typed methods
- [ ] `stubs/nautilus_trader/model/account.pyi` — Account class
- [ ] `stubs/nautilus_trader/model/position.pyi` — Position class with typed attrs

### Commit

- [ ] `feat: expand nautilus_trader stubs — concrete types for Cache, Portfolio, events`
- [ ] Regenerate baseline → measure reduction

---

## Phase 3 — Internal Library Stubs: features-sports-service (429 errors)

- [ ] Investigate: does `unified-feature-calculator-library` have `py.typed`?
  - If yes: activate via pyproject.toml; no stubs needed
  - If no: create `stubs/unified_feature_calculator/__init__.pyi`
- [ ] Create `stubs/unified_market_interface/__init__.pyi` for factory return types used
- [ ] Add `stubsPath = "stubs"` + `reportMissingTypeStubs = false` to pyproject.toml `[tool.basedpyright]`
- [ ] Delete `.basedpyright-baseline.json`
- [ ] Commit: `feat: add type stubs for internal libs in features-sports-service`

---

## Phase 4 — Deployment-api (2,962 errors)

- [ ] Add `types-redis>=4.5.0,<5.0.0` to dev deps (−~100 errors)
- [ ] Create `stubs/google/auth/_helpers.pyi` for private attrs accessed (OR refactor to public API)
- [ ] Create `stubs/cachetools/__init__.pyi` — `TTLCache[K,V]`, `LRUCache[K,V]`
- [ ] Add `stubsPath = "stubs"` to pyproject.toml `[tool.basedpyright]`
- [ ] Systematically annotate `deployment_api/routes/`, `deployment_api/workers/`, `deployment_api/services/`,
      `deployment_api/utils/`, `deployment_api/clients/`
- [ ] Delete `.basedpyright-baseline.json`
- [ ] Commit: `feat: zero basedpyright baseline in deployment-api`

---

## Phase 5 — Market-data-processing-service (1,348 errors)

- [ ] Verify polars inline types activated in basedpyright config
- [ ] Create `stubs/pyarrow/__init__.pyi` — `Table`, `Schema`, `Field`, `ChunkedArray`, `RecordBatch`
- [ ] Annotate `numba_kernels.py` with explicit return types / numba typed hints
- [ ] Add type annotations to `market_data_processing_service/app/` source files
- [ ] Delete `.basedpyright-baseline.json`
- [ ] Commit: `feat: zero basedpyright baseline in market-data-processing-service`

---

## Phase 6 — ML-training-service (504 errors)

- [ ] Create `stubs/scipy/__init__.pyi` + `stubs/scipy/stats/__init__.pyi` (functions actually called)
- [ ] Create `stubs/lightgbm/__init__.pyi` — `LGBMClassifier`, `LGBMRegressor`, `Dataset`, `train()`
- [ ] Create `stubs/talib/__init__.pyi` — indicator functions used by service
- [ ] Create `stubs/shap/__init__.pyi` — `TreeExplainer`, `Explainer`, `.shap_values()`
- [ ] Add `stubsPath = "stubs"` to pyproject.toml `[tool.basedpyright]`
- [ ] Annotate internal `ml_training_service/` code
- [ ] Delete `.basedpyright-baseline.json`
- [ ] Commit: `feat: zero basedpyright baseline in ml-training-service`

---

## Phase 7 — execution-service Internal Code (~12,000 remaining errors)

After Phase 2 stubs land, re-measure. Then annotate in order of error count:

- [ ] `algorithms/impl/passive_aggressive_execution.py` (677 errors) — add event param types
- [ ] `algorithms/impl/vwap_execution.py` (516 errors)
- [ ] `algorithms/impl/hybrid_optimal.py` (456 errors)
- [ ] `engine/backtest/actors/signal_driven_v3_handlers.py` (407 errors)
- [ ] `algorithms/impl/almgren_chriss.py` (358 errors)
- [ ] `results/extractor.py` (351 errors) — define `NautilusEngineProtocol`
- [ ] `algorithms/impl/pov_dynamic.py` (320 errors)
- [ ] `config/grid_v2_registry.py` (294 errors)
- [ ] `engine/backtest/node_builder.py` (294 errors)
- [ ] `data/loader_gcs.py` (283 errors)
- [ ] `results/timeline.py` (281 errors)
- [ ] Remaining files sorted by error count
- [ ] Delete `.basedpyright-baseline.json` when clean
- [ ] Commit per module: `fix: type-annotate execution-service algorithms/impl`

**Key patterns:**

```python
# Event handler params (applies to all on_* methods)
from nautilus_trader.model.events import OrderAccepted
def on_order_accepted(self, event: OrderAccepted) -> None: ...

# Engine Protocol (for extractor, evaluator)
class NautilusEngineProtocol(Protocol):
    cache: Cache
    portfolio: Portfolio
```

---

## Phase 8 — Verify and Lock Zero Baseline

- [ ] Run basedpyright in each repo — 0 errors required
- [ ] Delete or verify-empty `.basedpyright-baseline.json` in all 8 repos
- [ ] Run `bash scripts/quality-gates.sh` in each repo
- [ ] Update `unified-trading-codex/06-coding-standards/README.md`: baseline files must be absent
- [ ] Add CI enforcement: QG fails if baseline has entries (all 8 repos)
- [ ] Register this plan completion in `unified-trading-codex/00-SSOT-INDEX.md`
- [ ] Commit: `chore: enforce zero baseline policy in CI + codex SSOT`

---

## Progress Tracking

- [x] Plan created
- [ ] Phase 1 complete (strategy-service ✗, execution-results-api ✗, UTEI ✗)
- [ ] Phase 2 complete (nautilus stubs expanded)
- [ ] Phase 3 complete (features-sports-service)
- [ ] Phase 4 complete (deployment-api)
- [ ] Phase 5 complete (market-data-processing)
- [ ] Phase 6 complete (ml-training)
- [ ] Phase 7 complete (execution-service core)
- [ ] Phase 8 complete (zero baseline verified all repos)
