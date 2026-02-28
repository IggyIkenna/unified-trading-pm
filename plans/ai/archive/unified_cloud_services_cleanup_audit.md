# Unified Cloud Services (UCS) Cleanup Audit

**Date:** 2026-02-24  
**Purpose:** Audit current state of unified-trading-services against the “clean up by using the other six libraries and focus on cloud-only” plan. Identify remaining bloat and unfinished work.

**Source plan:** [fix_7_unified_libraries_quality_gates.plan.md](fix_7_unified_libraries_quality_gates.plan.md)

---

## 1. Plan Summary (What “Clean Up” Meant)

The plan was to:

- **Focus UCS on cloud-only:** storage, secrets, client factory, error handling, monitoring, GCS FUSE, date/utils. Rely on the other six libraries for config (UCI), events (UEI), domain clients (UDS), market/API clients (UMI), order (UOI), and execution algos (execution-algo-library).
- **Move out of UCS:** domain clients → UDS, config → UCI, event setup → UEI, DataSourceMapping → UMI, ML module → unified-ml-interface (new), and remove the legacy `UnifiedCloudService` monolith.

“Focus on Claude” in your note is interpreted as **focus on cloud** (UCS as the cloud foundation only).

---

## 2. Current UCS Size (Source Only, Excluding Tests)

| Metric | Value |
|--------|--------|
| **Total Python source (unified_trading_services/**.py)** | **~18,516 lines** |
| **Largest files** | See below |
| **Plan “after restructure” target** | ~16,467 lines (then ~6,097 lines moved/removed) |

### 2.1 Largest / Problematic Files

| File | Lines | Issue |
|------|--------|--------|
| `core/unified_cloud_service.py` | **1,700** | **Over 1500-line limit (COD-SIZE);** plan Phase 0.3: remove entirely |
| `__init__.py` | 672 | Very large surface; re-exports + optional split-library imports |
| `core/config.py` | 670 | Plan 0.4: migrate to UCI; still holds `UnifiedCloudServicesConfig` |
| `core/error_handling.py` | 749 | Large but core cloud behavior; keep |
| `domain/standardized_service.py` | 725 | Wraps `UnifiedCloudService`; depends on Phase 0.3 |
| `core/storage_abstraction.py` | 596 | Core; keep |
| `core/logging.py` | 445 | Plan 0.5: deprecate `setup_cloud_logging`; still present |
| **ml/** (total) | **~1,425** | Plan 0.7: move to unified-ml-interface |

So the main “old stuff” and “too many lines” are:

1. **UnifiedCloudService** (1,700 lines) – legacy monolith, should be removed.
2. **UnifiedCloudServicesConfig** in `core/config.py` (670 lines) – should live in UCI only.
3. **setup_cloud_logging** in `core/logging.py` – deprecated in plan; callers should use UEI `setup_events`.
4. **ml/** module (~1,428 lines) – should move to unified-ml-interface.
5. **__init__.py** (672 lines) – re-exports and optional split-library imports; can be thinned as migrations complete.

---

## 3. What’s Already Done (vs Plan)

| Plan item | Status in plan | Actual state |
|-----------|----------------|--------------|
| Phase 1 circular import (domain/clients) | completed | N/A – domain clients no longer in UCS (see below) |
| Phase 1 codex violations | completed | — |
| Remove DataSourceMapping | completed | **Done** – no `data_source_mapping.py` or references in UCS |
| Move domain clients to UDS | **pending** in plan | **Done in code** – UCS has no `domain/clients.py`; UDS has `unified_domain_client/clients.py`. Plan todo is stale. |
| Config migration to UCI | completed | Services use UCI `UnifiedCloudConfig`; UCS still contains `UnifiedCloudServicesConfig` (see “Remaining” below) |
| Deprecate setup_cloud_logging | completed | Deprecation decided; implementation still in UCS and exported |

---

## 4. What’s Still There (Old / To Clean)

### 4.1 Still in UCS (Should Leave or Shrink)

| Area | What’s there | Plan action | Notes |
|------|----------------|-------------|--------|
| **core/unified_cloud_service.py** | 1,700-line legacy class | Remove (0.3); refactor `StandardizedDomainCloudService` to use `get_storage_client` etc. | **Blocking:** file exceeds 1500-line limit |
| **core/config.py** | `UnifiedCloudServicesConfig`, `get_unified_config`, `unified_config` | Migrate to UCI; remove from UCS (0.4) | Still exported from `__init__.py`; ml-training-service may still use UCS config |
| **core/logging.py** | `setup_cloud_logging` | Deprecate; callers → UEI `setup_events` (0.5) | Still used by UTDv2/UTDv3 and quality-gates.sh |
| **domain/factories.py** | Factory functions returning `UnifiedCloudService` | Remove with UnifiedCloudService (0.3) | Tightly coupled to legacy class |
| **domain/standardized_service.py** | Wrapper around `UnifiedCloudService` | Refactor to use storage/secret primitives only (0.3) | 725 lines |
| **ml/** | ModelRegistry, config_schema, models, etc. | Move to unified-ml-interface (0.7) | ~1,428 lines |
| **__init__.py** | Re-exports of config, logging, UEI/UCI optional imports | Thin as each migration completes | 672 lines |

### 4.2 Optional Re-exports (Split Libraries)

`__init__.py` still does optional imports and assigns:

- `setup_events`, `publish_coordination_event`, `subscribe_coordination_events` (UEI)
- `load_config` (UCI)

and documents that “Re-exports removed Feb 2026 - migration complete, no consumers via UCS.” So these can be removed from UCS once all consumers use UEI/UCI directly (and any remaining references are updated).

### 4.3 No Longer in UCS (Confirmed)

- **DataSourceMapping** – removed.
- **domain/clients.py** – removed; domain clients live in UDS.
- **observability** – no `observability/` package in UCS; events/observability are UEI.
- **API clients (Tardis, Databento, etc.)** – canonical home is UMI; no `clients/` in UCS package layout.

---

## 5. Plan Todos Still Pending (Relevant to UCS)

From the plan YAML:

- **ucs_remove_unified_cloud_service** – Remove `UnifiedCloudService`; refactor `StandardizedDomainCloudService` to use primitives. **High impact (1,700 lines + factories + standardized_service).**
- **ucs_stop_api_clients** – Confirm UCS build does not ship any `clients/`; UMI is canonical. (Likely already true; needs verification.)
- **ucs_ml_split** – Move `ml/` to unified-ml-interface (~1,428 lines).
- **ucs_domain_clients_uds** – Mark **completed** in plan; code already moved to UDS.

Phase 4 (dependency matrix), Phase 5 (docs), Phase 6 (merge order) and UMI-specific todos are separate from “UCS cleanup” but depend on the above.

---

## 6. Quality Gate / Codex Notes

- **File size:** `core/unified_cloud_service.py` at 1,700 lines fails the 1,500-line limit (file-splitting-guide.md / COD-SIZE). Removing the file (Phase 0.3) resolves this.
- **QUALITY_GATE_BYPASS_AUDIT.md** still mentions `domain/clients.py` and “Phase 0.3 removes UnifiedCloudService”; update when 0.3 and 0.7 are done.
- Lazy-import whitelist in quality-gates.sh still references `domain/clients`; can be cleaned once any remaining references are gone.

---

## 7. Recommendations (Priority)

1. **Update plan status** – Mark `ucs_domain_clients_uds` as **completed** (domain clients already in UDS).
2. **Phase 0.3 (UnifiedCloudService removal)** – Highest impact:
   - Refactor `StandardizedDomainCloudService` to use `get_storage_client`, `get_secret_client`, `CloudTarget`, and existing primitives only.
   - Remove `core/unified_cloud_service.py` and `domain/factories.py`; update `domain/standardized_service.py` and any tests (e.g. `testing/test_uniform_config_access.py`).
3. **Phase 0.7 (ML split)** – Create unified-ml-interface, move `unified_trading_services/ml/` into it, update ml-training-service and ml-inference-service imports.
4. **Thin config and logging in UCS** – After confirming no remaining callers of `UnifiedCloudServicesConfig` / `get_unified_config` from UCS, remove or reduce in UCS and rely on UCI. Similarly, finish migration from `setup_cloud_logging` to UEI `setup_events` and remove or thin from UCS.
5. **Thin __init__.py** – Remove optional UEI/UCI re-exports and any other symbols that now live only in split libraries; keep UCS to cloud-only public API.
6. **Verify 0.6** – Confirm UCS package does not ship a `clients/` directory; document in plan/docs.

---

## 8. References

- Plan: [fix_7_unified_libraries_quality_gates.plan.md](fix_7_unified_libraries_quality_gates.plan.md)
- Dependency matrix: `unified-trading-codex/05-infrastructure/unified-libraries/dependency-matrix.md`
- File size rule: `.cursor/rules/file-size-limit.mdc` (1500 lines)
- Config/events: workspace `.cursorrules` (UnifiedCloudConfig, setup_events from UEI)
