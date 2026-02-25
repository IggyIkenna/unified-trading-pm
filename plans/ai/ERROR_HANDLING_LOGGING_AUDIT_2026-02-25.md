# Error Handling and Logging Audit

**Date:** 2026-02-25  
**Scope:** All Python repos (services and libraries) in unified-trading-system-repos  
**Focus:** Bare exceptions, silent failures, logging violations, fallback patterns, error propagation

---

## Executive Summary

| Category | Count | Severity |
|----------|-------|----------|
| Bare/Generic Exception Handlers | 22 | P1–P2 |
| Silent Failures (pass/return without log) | 8 | P1 |
| Print Instead of Logger | 28 files, ~350+ calls | P2 |
| Fallback Patterns (try-except with defaults) | 6 | P1–P2 |
| Error Swallowing (return []/None on failure) | 5 | P1 |
| Missing Error Context | 2 | P2 |
| Batch Operations Without Failure Logging | 2 | P2 |

**Overall:** No bare `except:` found. Several `except Exception:` and `except ImportError:` patterns exist. Most critical issues are in scripts (PM, .cursor, .lobster) and a few service/library locations.

---

## 1. Violations by Category

### 1.1 Bare/Generic Exception Handlers

| File | Line | Pattern | Severity |
|------|------|---------|----------|
| `unified-trading-pm/scripts/check-import-patterns-v2.py` | 130 | `except Exception as e: pass` | **P1** |
| `instruments-service/scripts/find_subgraph_ids.py` | 62 | `except Exception: pass` | **P1** |
| `features-volatility-service/features_volatility_service/app/core/volatility_orchestration.py` | 129 | `except Exception as e:` (logs, continues) | P2 |
| `features-volatility-service/features_volatility_service/cli/handlers/base_handler.py` | 70 | `except Exception as e:` (logs warning) | P2 |
| 14+ script files | various | `except Exception as e: print(...)` | P2 |

**Note:** No `except:` (bare) found. Codex rule forbids `except Exception` in production; scripts use it for CLI error handling.

### 1.2 Silent Failures

| File | Line | Issue |
|------|------|-------|
| `instruments-service/scripts/find_subgraph_ids.py` | 62 | `except Exception: pass` — HTTP/API errors not logged |
| `unified-trading-pm/scripts/check-import-patterns-v2.py` | 130 | `except Exception as e: pass` — parsing errors ignored |
| `unified-trading-pm/scripts/check-file-size.py` | 13 | `except OSError: pass` — file read errors skipped |
| `unified-trading-pm/plans/ai/tasks_claude_code/simple-parser.py` | 86 | `except (json.JSONDecodeError, KeyError): continue` — malformed JSON skipped without log |
| `ml-training-service/tests/test_training_orchestrator_full_coverage.py` | 48 | `except (ValueError, AssertionError): pass` — test swallows assertion (acceptable in tests) |

### 1.3 Print Instead of Logger

**Files with `print()` usage (mostly scripts):**

| Location | Count | Notes |
|----------|-------|-------|
| `unified-trading-pm/scripts/` | ~150 | Rollout, fix, import scripts |
| `.cursor/scripts/` | ~150 | Duplicates of PM scripts |
| `.lobster/scripts/` | ~25 | Task/coverage scripts |
| `unified-trading-pm/plans/ai/tasks_claude_code/simple-parser.py` | 9 | Uses print for CLI output |

**Services/Libraries:** No `print()` in production service code. Scripts use print for CLI output, which is acceptable for one-off tools.

### 1.4 Fallback Patterns

| File | Line | Pattern |
|------|------|---------|
| `features-volatility-service/features_volatility_service/cli/handlers/batch_handler.py` | 9–19 | `except ImportError:` → defines `should_skip_date`/`get_earliest_valid_date` returning defaults |
| `unified-cloud-services/unified_cloud_services/__init__.py` | 37–49 | `except ImportError: pass` for dotenv, gcsfuse (optional deps) |
| `unified-cloud-services/unified_cloud_services/core/async_gcp_clients.py` | 24–31 | `except ImportError:` → `GCLOUD_AIO_AVAILABLE = False` (lazy optional dep) |
| `strategy-service/strategy_service/cli/main.py` | 18–20 | `except ImportError: pass` for dotenv |
| `ml-training-service/ml_training_service/cli/main.py` | 15–17 | `except ImportError: pass` for dotenv |
| `features-volatility-service/tests/conftest.py` | 27–29 | `except ImportError: pass` for dotenv |

**Assessment:** ImportError fallbacks for optional deps (dotenv, gcloud-aio) are acceptable. The `batch_handler` fallback for `should_skip_date`/`get_earliest_valid_date` hides missing `unified-domain-services` and returns `False`/`"1970-01-01"` — **P1**: should fail or log clearly.

### 1.5 Error Swallowing (Return Default on Failure)

| File | Line | Pattern |
|------|------|---------|
| `strategy-service/strategy_service/app/core/gcs_storage_service.py` | 410–412 | `except (OSError, ValueError): logger.error(...); return []` |
| `strategy-service/strategy_service/app/core/gcs_storage_service.py` | 439–441 | `except (...): logger.error(...); return None` |
| `unified-cloud-services/unified_cloud_services/core/async_gcp_clients.py` | 236–237 | `upload_batch`: `return [not isinstance(r, Exception) for r in results]` — failures not logged |
| `unified-cloud-services/unified_cloud_services/core/async_gcp_clients.py` | 250–252 | `download_batch`: `return [None if isinstance(r, Exception) else r for r in results]` — failures not logged |
| `ml-inference-service/ml_inference_service/app/core/model_loader.py` | 125–127 | `except (...): logger.error(...); return None` |
| `ml-training-service/ml_training_service/ml/model_registry.py` | 230–232 | `except (...): logger.error(...); return None` |

**Assessment:** GCS `list_backtest_runs` and `load_backtest_summary` return `[]`/`None` on error but log. Callers may not distinguish "empty" from "error". `upload_batch`/`download_batch` return success flags/None but do not log which blobs failed.

### 1.6 Missing Error Context

| File | Line | Issue |
|------|------|-------|
| `unified-trading-pm/scripts/check-file-size.py` | 13 | `except OSError: pass` — no message, no re-raise |
| `instruments-service/scripts/find_subgraph_ids.py` | 62 | `except Exception: pass` — no message, no log |

### 1.7 Missing Logging at Critical Points

- **Event logging:** Codex requires `tests/unit/test_event_logging.py` with `SERVICE_SPECIFIC_EVENTS`. No `test_event_logging.py` files found in services.
- **Lifecycle events:** Services use `setup_events`/`log_event` from unified-events-interface. Coverage not fully audited.
- **Batch operations:** `AsyncGCSStorage.upload_batch` and `download_batch` use `asyncio.gather(..., return_exceptions=True)` but do not log which tasks failed.

---

## 2. Top 20 Critical Error Handling Issues

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| 1 | `instruments-service/scripts/find_subgraph_ids.py` | 62 | `except Exception: pass` — silent API failure | **P1** |
| 2 | `unified-trading-pm/scripts/check-import-patterns-v2.py` | 130 | `except Exception as e: pass` — parsing errors ignored | **P1** |
| 3 | `features-volatility-service/.../batch_handler.py` | 9–19 | ImportError fallback defines stub returning False/1970-01-01 | **P1** |
| 4 | `strategy-service/.../gcs_storage_service.py` | 410–412 | `list_backtest_runs` returns `[]` on error — caller can't distinguish | **P1** |
| 5 | `strategy-service/.../gcs_storage_service.py` | 439–441 | `load_backtest_summary` returns `None` on error | **P1** |
| 6 | `unified-cloud-services/.../async_gcp_clients.py` | 236 | `upload_batch` — failures not logged | **P1** |
| 7 | `unified-cloud-services/.../async_gcp_clients.py` | 251 | `download_batch` — failures not logged | **P1** |
| 8 | `unified-trading-pm/plans/ai/.../simple-parser.py` | 86 | Malformed JSON skipped without log | **P1** |
| 9 | `unified-trading-pm/scripts/check-file-size.py` | 13 | `except OSError: pass` — file errors skipped | **P2** |
| 10 | `features-volatility-service/.../volatility_orchestration.py` | 129 | `except Exception` — logs but continues (in-flight pattern) | P2 |
| 11 | `ml-inference-service/.../model_loader.py` | 63–65 | Model registry init failure → `self.model_registry = None` | P2 |
| 12 | `ml-inference-service/.../model_loader.py` | 125–127 | `load_model` returns None on error | P2 |
| 13 | `ml-training-service/.../model_registry.py` | 97–99 | Cloud service init failure → `self.cloud_service = None` | P2 |
| 14 | `ml-training-service/.../model_registry.py` | 166–167 | Metadata store failure → warning only, continues | P2 |
| 15 | `ml-training-service/.../model_registry.py` | 230–232 | `load_model` returns None on error | P2 |
| 16 | `.cursor/scripts/check-import-patterns-v2.py` | 130 | Same as #2 (duplicate) | **P1** |
| 17 | Multiple rollout/fix scripts | various | `except Exception: print(...)` — use logger for scripts | P2 |
| 18 | `features-volatility-service/.../main.py` | 60–73 | `except (OSError, ValueError): pass` in shutdown — acceptable | OK |
| 19 | `unified-cloud-services/.../async_gcp_clients.py` | 78–79 | `AsyncGCSBlob.exists` returns False on error — no log | P2 |
| 20 | `unified-trading-pm/scripts/check-import-patterns.py` | 105, 144 | `except Exception` with conditional print (verbose) | P2 |

---

## 3. Examples of Silent Failures

### 3.1 instruments-service/scripts/find_subgraph_ids.py:62

```python
    except Exception:
        pass

    return False
```

**Problem:** HTTP errors, timeouts, JSON decode errors are swallowed. Caller gets `False` with no indication of cause.

**Fix:** Log and optionally re-raise or return a result type that indicates failure reason.

### 3.2 unified-trading-pm/scripts/check-import-patterns-v2.py:130

```python
        except Exception as e:
            pass  # Ignore parsing errors

        return issues
```

**Problem:** Parsing errors are ignored. Issues list may be incomplete without caller knowing.

**Fix:** Log at debug/warning and optionally add a generic issue entry.

### 3.3 features-volatility-service batch_handler fallback

```python
try:
    from unified_domain_services.date_utils import get_earliest_valid_date, should_skip_date
except ImportError:

    def should_skip_date(...) -> bool:
        return False

    def get_earliest_valid_date(...) -> str:
        return "1970-01-01"
```

**Problem:** If `unified-domain-services` is missing, code silently uses stubs. Date filtering and validation may be wrong.

**Fix:** Fail at import or log a clear warning and fail at runtime when these are used.

### 3.4 unified-cloud-services async_gcp_clients upload_batch/download_batch

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
return [not isinstance(r, Exception) for r in results]  # upload_batch
return [None if isinstance(r, Exception) else r for r in results]  # download_batch
```

**Problem:** Exceptions are converted to False/None. Caller does not know which blobs failed or why.

**Fix:** Log each exception (e.g. `logger.warning("Upload failed for %s: %s", path, e)`) and optionally return structured results with failure details.

---

## 4. Missing Logging at Critical Points

| Location | Missing |
|----------|---------|
| `test_event_logging.py` | No such test files found; Codex requires per-service `tests/unit/test_event_logging.py` with `SERVICE_SPECIFIC_EVENTS` |
| `AsyncGCSStorage.upload_batch` | No log of which uploads failed |
| `AsyncGCSStorage.download_batch` | No log of which downloads failed |
| `AsyncGCSBlob.exists` | Returns False on error without logging |
| Scripts (PM, .cursor, .lobster) | Use `print()` instead of `logging` — acceptable for CLI, but errors should go to stderr or logger |

---

## 5. Severity Scoring

| Severity | Definition | Count |
|----------|------------|-------|
| **P1** | Silent failure, wrong fallback, or error swallowing that can cause incorrect behavior | 8 |
| **P2** | Missing logs, broad exception handling, or inconsistent patterns | 12 |
| **OK** | Acceptable (e.g. optional deps, shutdown handling, in-flight validation) | 6 |

---

## 6. Recommendations

1. **P1 – Fix immediately**
   - `instruments-service/scripts/find_subgraph_ids.py`: Log and optionally re-raise or return structured failure.
   - `unified-trading-pm/scripts/check-import-patterns-v2.py`: Log parsing errors (and optionally add to issues).
   - `features-volatility-service` batch_handler: Remove ImportError fallback or fail clearly when `unified-domain-services` is missing.
   - `unified-cloud-services` `upload_batch`/`download_batch`: Log each failed task with blob path and exception.

2. **P2 – Address in next sprint**
   - Add `test_event_logging.py` to services per Codex.
   - Replace `except Exception: print(...)` with `logger.exception(...)` or `logger.error(...)` in scripts.
   - `strategy-service` GCS methods: Consider returning `Result`-style types or raising for critical failures instead of `[]`/`None`.
   - `AsyncGCSBlob.exists`: Log when returning False due to exception.

3. **Acceptable as-is**
   - `except ImportError: pass` for optional deps (dotenv, gcloud-aio).
   - Shutdown `except (OSError, ValueError): pass` when streams are closed.
   - In-flight validation in volatility orchestration (log and continue).
   - `print()` in CLI scripts for user-facing output (errors should use logger or stderr).

---

## 7. Files Audited

- **Services:** instruments-service, strategy-service, ml-training-service, ml-inference-service, features-volatility-service, features-onchain-service, features-delta-one-service, execution-services
- **Libraries:** unified-cloud-services, unified-events-interface, unified-config-interface, unified-domain-services
- **Scripts:** unified-trading-pm/scripts, .cursor/scripts, .lobster/scripts, .cursor/workspace-configs

---

*Generated by error handling and logging audit across unified-trading-system-repos.*
