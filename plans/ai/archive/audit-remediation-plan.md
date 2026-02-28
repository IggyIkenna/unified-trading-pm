# Audit Remediation Plan — 2026-02-27

Source: `INDEPENDENT_AUDIT_REPORT_2026-02-27.md` (40+ FAIL, 18 WARN)
Secondary: Pass-2 auditor gap analysis (G1–G8, NEW-1–3, F1–F15).
Target: 0 FAIL (CI gate), then WARNs for A-grade.

---

## Status Legend

- ✅ DONE — verified in current codebase (post-wave execution)
- 🔄 IN PROGRESS — agents working on it
- ❌ REMAINING — still needs work
- ⚠️ NEW — found in pass-2 audit, not in original plan

---

## Completed (verified by codebase search)

| ID | Finding | Evidence |
|----|---------|----------|
| W1-ruff | typing.List/Dict, print(), utcnow() | ruff auto-fix applied across 8 repos |
| W2a | .gitignore credential allowlist | grep returns null — fixed |
| W3a | Dockerfile `\|\| true` | removed in risk-and-exposure-service |
| W3b | `except Exception: pass` | all 8+ instances removed |
| W3c-partial | try/except ImportError | 214 → ~130 (39% reduction) |
| W3d-partial | pip install → uv pip install | market-tick-data-handler, others |
| W4b-partial | Any types | execution-results-api, strategy-service partial |
| W4c | naive datetime | 47 → ~0 remaining (85%+ reduction) |
| W5a | conftest GCP auth | unified-trading-services, instruments-service |
| G1 | E722 global ruff ignore | grep returns null — already fixed |
| G3 | api-contracts files >900L | aws_schemas=272, venue_manifest=9, binance=7 — already split |
| G4/F6 | uv.lock gitignored | grep returns null — already fixed or never present |
| G5/F5 | ThreadPoolExecutor unlimited | grep returns null — fixed |
| F2 | .gitignore credential allowlist | null — fixed |
| F14 | naive datetime remaining | grep returns empty — fixed |

---

## Wave 1 — Automated ruff (DONE) ✅

ruff UP006/UP035/T201/UP017 applied across all 8 target repos via agents.

---

## Wave 2 — Security P0

### 2a. ✅ Credential allowlist in .gitignore — DONE
### 2b. 🔄 GOOGLE_CLOUD_PROJECT remaining (F8) — 6 prod files
Still present in execution-services production code:
- `execution_services/utils/dependency_checker.py:212`
- `execution_services/service_config.py:426`
- `execution_services/config/grid_generator.py:1712`
- `execution_services/visualizer-api/app/core/config.py:35`
- `execution_services/visualizer-api/app/services/data_service.py:23`
- `execution_services/visualizer-ui/backend/instruction_api.py:47`
Fix: Replace `GOOGLE_CLOUD_PROJECT` → `GCP_PROJECT_ID`; update imports to use config class.

### 2c. ✅ os.getenv empty fallback — DONE (confirmed by wave execution)

### 2d. ❌ central-element hardcoded in PRODUCTION code (F9) — 19 instances
**NOT in tests — in production unified_cloud_services modules:**
- `unified_cloud_services/utils/id_conventions.py:224,227,270,274`
- `unified_cloud_services/core/gcsfuse_helper.py:19,22,240,245,270,271`
- `unified_cloud_services/core/cloud_config.py:22,25,28,34`
- `unified_cloud_services/core/cloud_auth_factory.py:83`
- `unified_cloud_services/cli.py:43,44,268,269`
Fix: Replace with `GCP_PROJECT_ID` env var lookup or move to test-only config.

### 2e. ✅ uv.lock gitignored — DONE

---

## Wave 3 — Error handling P0

### 3a. ✅ Dockerfile `|| true` — DONE
### 3b. ✅ `except Exception: pass` — DONE
### 3c. ❌ try/except ImportError remaining (F7) — ~130 files
Progress from 214→130. All key service files done. Remaining in lower-priority scripts.
### 3d. ❌ pip install in CI/Dockerfiles (F1) — 50+ instances (count grew)
**New Dockerfiles added without uv standard:**
- `execution-services/Dockerfile:42`, `execution-services/visualizer-api/Dockerfile:14,17`
- `ml-training-service/Dockerfile:33`, `features-*/Dockerfile:27`
- `unified-trading-deployment-v3/Dockerfile:63-68`
- `execution-services/.github/workflows/quality-gates.yml:72`
Fix: Replace `pip install` → `uv pip install` in all CI and Dockerfiles.

---

## ⚠️ NEW Wave 3e — asyncio.run() in sync utility methods (NEW-1, P0)

`asyncio.run()` inside non-CLI functions raises `RuntimeError: This event loop is already running`
when called from async context. These are P0 runtime crashes.

**BAD instances (not CLI entry points):**
- `execution_services/backtest/engine.py:773` — `_setup_catalog_and_instrument()` sync method
- `execution_services/backtest/engine.py:1811` — same file, setup path
- `execution_services/results/serializer.py:813` — `_upload_to_gcs_sync()` static method
- `execution_services/data/config_builder.py:1187,1899` — config builder
- `execution_services/data/config/book_builder.py:207` — book builder
- `unified_market_interface/adapters/defi/uniswapv2_adapter.py:150` — `fetch_markets()` sync
- `unified_market_interface/adapters/defi/uniswapv4_adapter.py:164` — same pattern

**OK instances (CLI entry points — leave alone):**
- `execution_services/cli/handlers/live_execution_handler.py:60`
- `execution_services/cli/handlers/execute_handler.py:17`
- `execution_services/cli/batch_backtest.py:96,134`
- `execution_services/cli/backtest.py:430,469`

Fix pattern for sync utility methods wrapping async:
```python
def _safe_async_run(coro):
    """Run coroutine safely: handles both sync and async calling contexts."""
    try:
        asyncio.get_running_loop()
        # Already inside event loop — run in thread pool to avoid deadlock
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        return asyncio.run(coro)
```

Add `_safe_async_run` to `unified-trading-services` utils. Replace all non-CLI `asyncio.run()`.

---

## ⚠️ NEW Wave 3f — Lifecycle event names wrong (NEW-2, data loss)

UTD v2 event parser silently drops `UPLOAD_STARTED` / `UPLOAD_COMPLETED` events.
Canonical names: `PERSISTENCE_STARTED` / `PERSISTENCE_COMPLETED` + `DATA_BROADCAST`.

**19 files using wrong names:**
- `strategy-service/strategy_service/cli/main.py`
- `strategy-service/strategy_service/cli/service_entry.py`
- `features-onchain-service/features_onchain_service/cli/handlers/batch_handler.py`
- `features-volatility-service/features_volatility_service/cli/handlers/batch_handler.py`
- `features-calendar-service/features_calendar_service/cli/handlers/batch_handler.py`
- `position-balance-monitor-service/position_balance_monitor_service/cli/handlers/monitor_handler.py`
- `market-data-processing-service/market_data_processing_service/app/core/output_writer_service.py`
- `market-data-processing-service/market_data_processing_service/app/core/orchestration_service.py`
- `market-data-processing-service/market_data_processing_service/adapters/gcs_data_sink.py`
- `market-data-processing-service/market_data_processing_service/cli/handlers/live_mode_handler.py`
- `unified-trading-deployment-v3/api/utils/service_utils.py`
- `unified-trading-deployment-v3/api/utils/service_events.py`
- `execution-services/execution_services/engine/backtest/runner.py`
- `execution-services/execution_services/backtest/runner.py`
- `market-tick-data-handler/market_data_tick_handler/cli/handlers/download_handler.py`
- `instruments-service/instruments_service/cli/handlers/instrument_handler.py`
- `ml-training-service/ml_training_service/cli/main.py`
- `unified-internal-contracts/unified_internal_contracts/events.py` — enum members wrong
- `api-contracts/api_contracts/internal/events.py` — enum members wrong

Fix: Replace `UPLOAD_STARTED` → `PERSISTENCE_STARTED`, `UPLOAD_COMPLETED` → `PERSISTENCE_COMPLETED`.
Ensure `DATA_BROADCAST` is emitted before `PERSISTENCE_STARTED` when writing.
Update enum definitions first, then string usages.

---

## Wave 4 — Code quality P1

### 4a. ❌ Split engine.py (2826 lines → max 900) (F3)
File: `execution-services/execution_services/backtest/engine.py`
**Blocked by asyncio.run() fixes in Wave 3e — fix asyncio first, then split.**
Split plan:
- `engine/core.py` — BacktestEngine class, main run loop
- `engine/order_router.py` — order routing and venue dispatch
- `engine/position_tracker.py` — position state management
- `engine/metrics.py` — PnL + evaluation metrics
- `engine.py` → thin re-export shim

### 4b. ❌ Any types (20+ files)
Replace `dict[str, Any]`/`-> Any` with TypedDict or Pydantic.
Document necessary exceptions in QUALITY_GATE_BYPASS_AUDIT.md.

### 4c. ✅ Naive datetime (47 occurrences) — DONE

### ⚠️ NEW 4d. validate_timestamp not fail-fast (NEW-3)
Files:
- `strategy-service/strategy_service/app/core/cloud_strategy_storage.py:188` — logs warning, doesn't raise
- `execution-services/execution_services/results/result_formatter.py:470` — logs error, continues
Fix: Replace `if not result.valid: logger.warning(...)` with:
```python
result = validate_timestamp_date_alignment(df, date=processing_date)
if not result.valid:
    raise ValueError(f"Timestamp alignment check failed: {result.reason}. Refusing GCS write.")
```

---

## Wave 5 — Tests + Schema P1

### 5a. ✅ conftest GCP auth pattern — DONE (instruments-service, unified-trading-services)
### ❌ 5a-remaining: conftest still has pytest.skip (F10)
- `market-data-processing-service/tests/` (3 files) — still credential-based skip
- `unified-trade-execution-interface/tests/integration/test_api_contracts_integration.py`
Fix: Apply google.auth.default() 3-step fallback per gcp-auth-in-tests.mdc.

### 5b. ✅ validate_timestamp conditional — partially in Wave 4d above (raises now)

### ❌ 5c. central-element in tests (F11) — 50+ unchanged
- `execution-services/tests/` (15+ files)
- `unified-trading-services/tests/conftest.py:101`
- `features-volatility-service/tests/conftest.py:58-64`
Fix: Replace `"central-element-323112"` → `"test-project"`.

### ❌ 5d. Non-canonical venue names (G6/F12) — 100+ unchanged
Lowercase `"binance"` in production code. Requires careful audit (comments vs code).
Fix: rg -l "\"binance\"" --type py → selective replace venue key strings only.

### ❌ 5e. # type: ignore suppressions (G2/F13) — 100+ files undocumented
Each must be either removed + type fixed, or documented in QUALITY_GATE_BYPASS_AUDIT.md.

---

## Wave 6 — Observability P2

### 6a. ❌ setup_cloud_logging remaining (F15)
File: `features-delta-one-service/features_delta_one_service/cli/main.py:20`
Fix: Replace with `setup_events()` from `unified_events_interface`.

### 6b. ✅ STOPPED/FAILED lifecycle events in features services — DONE

### ⚠️ NEW 6c. git push origin main in scripts (G7)
- `unified-trading-deployment-v3/scripts/deploy-dashboard.sh:179` — echo statement (not executed)
- `unified-trading-codex/scripts/create-repo-skeletons.sh` — one-time op script
Fix: Add comment block explaining these are manual one-time ops and must use quickmerge for
automated deployments. Replace example commands in echo with quickmerge pattern.

---

## Quality Gate Hardening (NEW — prevents recurrence)

Add to quality-gates.sh ruff checks:
- `ASYNC100` — asyncio.run() inside async (if ruff-asyncio plugin available)
- Custom grep check: `grep -rn "asyncio\.run(" src/ | grep -v "def main\|if __name__"` → FAIL if found
- Custom grep check: `grep -rn "UPLOAD_STARTED\|UPLOAD_COMPLETED" src/` → FAIL
- Custom grep check: `grep -rn "git push origin main" scripts/` → WARN

---

## Execution Order (Current Pass)

**Immediate (parallel 4 agents):**
1. unified-trading-services — central-element in prod code (F9)
2. Lifecycle events batch 1 — market-data-processing-service, features-*, position-balance-monitor
3. asyncio.run() + validate_timestamp — unified-market-interface defi adapters + strategy/exec-services
4. Lifecycle events batch 2 — instruments-service, market-tick-data-handler, ml-training, execution-services runners

**Next pass:**
5. engine.py split (Wave 4a) — after asyncio cleanup
6. central-element in tests (5c) — straightforward rg+replace
7. pip install remaining (F1) — Dockerfile sweeps

Each wave uses parallel agents per repo. Commit via `bash scripts/quickmerge.sh` — never standalone git push.
