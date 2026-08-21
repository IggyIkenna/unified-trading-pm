---
doc_type: plan
title: zero-baseline-typecheck-2026-03-10
summary: Eliminate all .basedpyright-baseline.json suppressions across every repo so basedpyright runs with 0 errors and
  empty/absent baseline files.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    client-reporting-api,
    deployment-api,
    execution-service,
    instruments-service,
    market-data-processing-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-10"
type: code
epic: epic-code-completion
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - {
      repo: execution-service,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: deployment-api,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: market-data-processing-service,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: ml-training-service,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: features-sports-service,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: strategy-service,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: execution-results-api,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: unified-trade-execution-interface,
      code: C4,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
depends_on: [position_precision_pnl_hardening_2026_03_11]
todos:
  - {
      id: phase9-type-ignore-triage,
      content: "Phase 9: enumerate and triage remaining # type: ignore in production source; fix fixable ones",
      status: done,
      note: "All fixable type:ignore resolved 2026-03-11",
    }
  - {
      id: phase9-funding-recon-severity,
      content: "execution-service/services/funding_recon_engine.py:214 — fix severity arg-type with AlertSeverity enum",
      status: done,
      note: "Fixed 2026-03-11: narrowed _publish_alert severity param to Literal type (Phase C confirmed done)",
    }
  - {
      id: phase9-yield-recon-severity,
      content: "execution-service/services/yield_recon_engine.py:280 — same severity arg-type pattern",
      status: done,
      note: "Fixed 2026-03-11: narrowed _publish_alert severity param to Literal type",
    }
  - {
      id: phase9-instruments-override,
      content: "instruments-service/instrument_processing_handlers.py:71 — # type: ignore[override] UTL-DEC-02 mixin",
      status: done,
      note: "Already fixed (no type:ignore present)",
    }
  - {
      id: phase9-client-reporting-pnl-reader,
      content: "client-reporting-api/core/pnl_reader.py:63 — df.to_dict cast to list[dict[str, object]]",
      status: done,
      note: "Fixed 2026-03-11: replaced type:ignore with cast()",
    }
  - {
      id: phase9-deployment-api-state,
      content: "deployment-api/services/deployment_state.py:269,293,324,358,436 — _reportPrivateUsage on sync helpers",
      status: done,
      note:
        "Fixed 2026-03-11: renamed 5 _sync functions to public in routes/deployment_state.py; updated imports in
        services + tests",
    }
isProject: false
---

# Zero Baseline Typecheck — Full Remediation Plan

**Created:** 2026-03-10 **Completed:** 2026-03-11 **Status:** ALL PHASES COMPLETE ✅ **SSOT-INDEX:** register under
`08-type-safety` **Linked codex section:** `unified-trading-/codex/06-coding-standards/README.md`

> ⚠️ **M3 SEQUENCING NOTE (2026-03-11):** Phase 9 TODO items in `funding_recon_engine.py:214` and
> `yield_recon_engine.py:280` (severity arg-type fixes) depend on `position_precision_pnl_hardening` Phase C being
> committed first — those files were created by that plan. Do not attempt the `funding_recon_engine.py` and
> `yield_recon_engine.py` Phase 9 fixes until Phase C from `position_precision_pnl_hardening_2026_03_11` is confirmed
> merged.

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

## Phase 1 — Trivial Repos (74 errors) ✅ COMPLETE (2026-03-10)

All three repos were already at 0 errors with no baseline files (fixed in prior sessions). Verified: `basedpyright` on
each repo shows `0 errors, 0 warnings, 0 notes`.

### strategy-service — DONE ✅ (0 errors, no baseline)

### execution-results-api — DONE ✅ (0 errors, no baseline)

### unified-trade-execution-interface — DONE ✅ (0 errors, no baseline)

**Execution-service broken imports also fixed (2026-03-10):**

- Commit `1c1551f3` in execution-service: resolved 15 broken ImportErrors blocking coverage recalibration
  - `dump_to_csv` → `CSVSampler().sample()` (defi.py, tick_data.py, result_formatter.py)
  - `get_unified_monitor` → `logger.debug()` (trades_builder.py)
  - `DataCompletionChecker`: import directly from UTL with Protocol pattern (validation.py)
  - `validate_config`: UTC → UCI (grid_generator_v2.py)
  - Removed dead cleanup functions in grid_utils.py
  - `get_project_identifier` → `get_project_id` (initializer.py)
  - DeribitAdapter: `venues.cefi` → `venues.deribit`
  - nautilus_trader: correct module paths for TradingNodeConfig, TradingNode, InstrumentProvider
  - binance: `binance.um_futures.UMFutures` → `binance.futures.Futures`
  - Removed AlphaComparator/AMMFillSimulator (never existed)
  - Created `execution_service/config/live_loader.py`
- Commit `8c7829c` in unified-domain-client: added `py.typed` marker

---

## Phase 2 — Expand Nautilus Stubs (−3,000+ errors in execution-service)

### `stubs/nautilus_trader/cache.pyi`

- [x] `Cache.account(venue) -> Account | None` (was `object`)
- [x] `Cache.positions() -> list[Position]` (was `list[object]`)
- [x] `Cache.orders() -> list[Order]`
- [x] `Cache.order(client_order_id) -> Order | None`
- [x] `Cache.instrument(instrument_id) -> Instrument | None`
- [x] `Cache.instruments() -> list[Instrument]`
- [x] `Cache.bar(bar_type) -> Bar | None`
- [x] `Cache.quote_tick(instrument_id) -> QuoteTick | None`
- [x] `Cache.trade_tick(instrument_id) -> TradeTick | None`

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
- [ ] Update `unified-trading-/codex/06-coding-standards/README.md`: baseline files must be absent
- [ ] Add CI enforcement: QG fails if baseline has entries (all 8 repos)
- [ ] Register this plan completion in `unified-trading-codex/00-SSOT-INDEX.md`
- [ ] Commit: `chore: enforce zero baseline policy in CI + codex SSOT`

---

## Progress Tracking

- [x] Plan created
- [x] Phase 1 complete — strategy-service ✅, execution-results-api ✅, UTEI ✅ (2026-03-10)
- [x] Phase 2 complete — nautilus stubs expanded (33+ .pyi files in execution-service/stubs/) (2026-03-10)
- [x] Phase 3 complete — features-sports-service 40 → 0 errors (commit 91e9a4c) (2026-03-10)
- [x] Phase 4 complete — deployment-api 2,962 → 0 errors, no baseline (commits ce897d3..c97a69e) (2026-03-10)
- [x] Phase 5 complete — market-data-processing-service 1,348 → 0 errors, no baseline (commit 7cf0b39) (2026-03-10)
- [x] Phase 6 complete — ml-training-service 504 → 0 errors, no baseline (commit 87808ac) (2026-03-10)
- [x] Phase 7 complete — execution-service 15,231 → 0 errors, no baseline (2026-03-11)
  - engine/: commits 611b42df, 3407b400, 80f51dfc, 30bbc114 + others
  - data/: commit 1f0f2e27; results/: commit 1f0f2e27; config/: commit ad4aa25e
  - venues/: commit 20be66f5; cli/: commit ab567824; algorithms/: commit 80b1fd5a
  - benchmark/: 622→0; instruments/+strategy_instructions/: 530→0 (commit 1195e4bd)
  - utils/+models/: 361→0 (commit 2bacb062); services/+orders/+api/+validation/+adapters/: commit a5cb7bb4
- [x] Phase 8 complete — zero baseline verified all repos (2026-03-11)
  - UDC baseline deleted 2026-03-10 (89ff721) — 0 real errors
  - instruments-service baseline deleted 2026-03-10 (774d0c6) — 0 real errors
  - execution-service baseline deleted — 0 real errors across full tree
  - `find . -name ".basedpyright-baseline.json"` → empty (workspace-wide verification ✅)
  - **GOAL ACHIEVED: 0 errors, 0 baseline files across all repos**
- [ ] Phase 9 — enumerate remaining `# type: ignore` in production source (2026-03-11)

---

## Phase 9 — Enumerate & Triage Remaining `# type: ignore` in Production Source

**Added:** 2026-03-11 (2026-03-11 full audit found 100+ instances across ~10 repos) **Goal:** Every `# type: ignore`
must have a comment justifying it. Unjustified ones get a todo to fix root cause.

**Categorised inventory** (from audit 2026-03-11):

### ALLOWED — third-party stubs incomplete (no action)

These arise because google-auth, google-cloud-build, and nautilus_trader have incomplete or absent type stubs.
Suppression is correct; fixing would require contributing stubs upstream.

- `deployment-api/deployment_api/routes/service_status.py:23` — `google.auth` import-untyped (google-auth stubs
  incomplete) ✅
- `deployment-api/deployment_api/routes/service_status.py:59,62,63,74` — google-auth untyped ✅
- `deployment-api/deployment_api/routes/cloud_builds.py` — CloudBuild stubs partial (14 occurrences) ✅
- `deployment-api/deployment_api/utils/artifact_registry.py:58,63,64` — google-auth stubs incomplete ✅

### ALLOWED — Protocol empty-body stubs (no action)

Required by basedpyright when Protocol/ABC methods have `...` body.

- `execution-service/execution_service/algorithms/impl/passive_aggressive_core.py:45` ✅
- `execution-service/execution_service/algorithms/impl/passive_aggressive_execution.py:104,107,110` ✅
- `execution-service/execution_service/algorithms/impl/twap_pricing.py:33` ✅
- `execution-service/execution_service/algorithms/impl/vwap_core.py:55,58` ✅

### ALLOWED — hasattr-guarded union-attr (no action)

`hasattr(x, "attr")` check precedes attribute access; basedpyright doesn't narrow through `hasattr`.

- `execution-service/execution_service/algorithms/impl/vwap_execution.py:279,297,319,384,403` ✅
- `deployment-api/deployment_api/routes/cloud_builds.py:561,563` ✅

### ALLOWED — pandas generic type-arg (pd.Series without type param, deployment-api dynamic objects)

pandas-stubs does not support fully generic `pd.Series[T]` in all contexts.

- `market-data-processing-service/...base_adapter.py:30,33,35,153,211,213,215,495` ✅
- `market-data-processing-service/.../rewards_adapter.py:137,141,146` ✅
- `features-sports-service/...` — 6 `dtype=object` suppressions ✅
- `deployment-api/...deployment_manager.py` — dynamic object dispatch (runtime polymorphism via importlib) ✅
- `deployment-api/...sync_service.py,auto_sync.py,event_processor.py` — dynamic backend objects ✅

### ALLOWED — elysium-defi-system (standalone fork, not production service)

- `elysium-defi-system/src/...` — 6 occurrences in strategies/adapters: adapter.fetch_prices() returns `object`
  (Protocol stub) ✅

### TODO — fixable with proper typing

- [ ] `execution-service/execution_service/services/funding_recon_engine.py:214` — `severity` arg-type: verify
      AlertSeverity enum is imported; fix with explicit cast or correct type annotation
- [ ] `execution-service/execution_service/services/yield_recon_engine.py:280` — same pattern as above
- [ ] `instruments-service/...instrument_processing_handlers.py:71` — `# type: ignore[override]` UTL-DEC-02 decorated
      mixin: investigate whether Protocol or overload can resolve without suppression
- [ ] `client-reporting-api/client_reporting_api/core/pnl_reader.py:63` — `df.to_dict(orient="records")` typed as
      `list[dict[str, object]]`; basedpyright infers `list[dict[str, Any]]`; fix with explicit
      `cast(list[dict[str, object]], df.to_dict(orient="records"))`
- [ ] `deployment-api/deployment_api/services/deployment_state.py:269,293,324,358,436` — `_reportPrivateUsage` on sync
      helpers: expose as semi-private (`_func`) or move to module scope

**Tracking:** Each TODO above → open as individual fix PR once Phase 8 is stable. No rush — none are architectural
violations.
