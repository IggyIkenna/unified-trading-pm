> **SUPERSEDED (archived 2026-07-27).** Blank, never-executed test-matrix template. Superseded by
> `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` +
> `plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md`.

---

title: "E2E Test: risk-management-service" service: risk-management-service date: 2026-03-22 status: pending
---

# E2E Test: risk-management-service

Follows `procedure.md`. Pipeline position: N/A -- minimal service, not a full pipeline service.

## Service Overview

**MINIMAL SERVICE.** The risk-management-service repo contains a single Python file:

```
risk_management_service/auth_s2s.py
```

This file delegates to UCI's shared S2S auth middleware:

```python
from unified_cloud_interface import create_s2s_auth_dependency
verify_service_token = create_s2s_auth_dependency("risk-management-service")
```

There is no CLI, no `main.py`, no handlers, no operations, no `pyproject.toml` at the repo root, no tests, no
`scripts/quality-gates.sh`. The repo has no service runtime, no ServiceCLI integration, and no pipeline role.

**This is not a standalone pipeline service.** It appears to be either:

1. **An auth middleware module** consumed by other risk-related services (risk-and-exposure-service) as an import
2. **A stub repo** that was created but never populated with service logic
3. **An API-only service** whose API code has not been written yet

## What Exists

| File                                  | Purpose                                               |
| ------------------------------------- | ----------------------------------------------------- |
| `risk_management_service/auth_s2s.py` | S2S auth dependency for FastAPI `Depends()` injection |

The `verify_service_token` callable is designed to be used as a FastAPI dependency:

```python
from risk_management_service.auth_s2s import verify_service_token

@app.get("/risk/limits", dependencies=[Depends(verify_service_token)])
async def get_risk_limits(): ...
```

## Test Matrix

### Phase 1: Import Validation

Since there is no CLI or service runtime, Phase 1 tests only that the module imports correctly.

| #   | Test                                                                | Expected                                    | Status |
| --- | ------------------------------------------------------------------- | ------------------------------------------- | ------ |
| 1.1 | `from risk_management_service.auth_s2s import verify_service_token` | Import succeeds, callable returned          |        |
| 1.2 | `verify_service_token` is a FastAPI dependency                      | Callable that validates S2S tokens          |        |
| 1.3 | UCI `create_s2s_auth_dependency` available                          | No ImportError from unified_cloud_interface |        |

### Phases 2-5: Not Applicable

There is no CLI, no operations, no modes, no categories, no live mode, no dry-run. These phases cannot be executed.

| Phase | Reason skipped                                    |
| ----- | ------------------------------------------------- |
| 2     | No CLI entry point, no `--dry-run` flag           |
| 3     | No data writes, no GCS interaction                |
| 4     | No `--asset-group` flag, no venue routing         |
| 5     | No `--mode live`, no WebSocket/PubSub consumption |

### Phase 6: Mock Mode

| #   | Test                                     | Expected                                       | Status |
| --- | ---------------------------------------- | ---------------------------------------------- | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true` + import auth_s2s | Import succeeds, no credentials required       |        |
| 6.2 | `CLOUD_PROVIDER=local` + import auth_s2s | Import succeeds, no cloud calls at import time |        |

### Phase 7: Observability

| #   | Check                    | Expected                                           | Status |
| --- | ------------------------ | -------------------------------------------------- | ------ |
| 7.1 | No runtime observability | No ServiceRuntime, no UEI events, no metrics       |        |
| 7.2 | Auth failure logging     | UCI S2S middleware logs auth failures when invoked |        |

## Known Issues Audit

| Pattern                       | Finding                                                                     |
| ----------------------------- | --------------------------------------------------------------------------- |
| No `pyproject.toml`           | Repo has no package metadata, cannot be installed via `uv pip install -e .` |
| No `scripts/quality-gates.sh` | Cannot run QG -- not a testable service                                     |
| No `__init__.py`              | Package may not be importable depending on directory setup                  |
| No tests                      | Zero test coverage                                                          |
| No CLI / no main.py           | Cannot be deployed as a standalone Cloud Run service                        |

## Architectural Assessment

This repo likely needs one of:

1. **Merge into risk-and-exposure-service** -- the `auth_s2s.py` module becomes `risk_and_exposure_service/auth_s2s.py`
   and this repo is archived
2. **Populate with risk management API** -- add FastAPI app, risk limit endpoints, position limit checks, drawdown
   circuit breakers. The `auth_s2s.py` would then serve its intended purpose as the auth middleware for those endpoints
3. **Reclassify as a library** -- if it is intended to be imported by multiple risk services, it should follow library
   conventions (proper `pyproject.toml`, tests, QG script)

Until one of these paths is chosen, there is nothing to E2E test beyond import validation.

## AWS Testing

Not applicable -- no service runtime, no cloud interactions beyond the S2S auth dependency.

## Frontend API Integration

Not applicable -- no API endpoints exist. If risk management endpoints are needed, they are likely served by
risk-and-exposure-service instead.

## Issues Found

| Issue                                           | Severity  | Fixed?                             |
| ----------------------------------------------- | --------- | ---------------------------------- |
| Repo contains only auth_s2s.py -- not a service | P2 (arch) | No -- needs architectural decision |
| No pyproject.toml                               | P2        | No                                 |
| No quality-gates.sh                             | P2        | No                                 |
| No tests                                        | P2        | No                                 |

## Next Service

After risk-management-service is assessed, proceed to the next service in pipeline order (alerting-service or whichever
is next in `procedure.md` service order).
