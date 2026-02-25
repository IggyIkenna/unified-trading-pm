# Quality Gates Hardening Summary

**Date:** 2026-02-23  
**Task:** Harden quality gates for unified-cloud-services and unified-config-interface to match instruments-service standards

---

## Changes Completed

### unified-cloud-services

#### ✅ 1. Fixed line-length in pyproject.toml
- **Before:** `line-length = 100`
- **After:** `line-length = 120`
- **Reason:** Match instruments-service standard (E501 enforced at 120 chars)

#### ✅ 2. Removed E501 from ignore list
- **Before:** `ignore = ["E501", "E402"]`
- **After:** `ignore = ["E402"]`
- **Reason:** E501 (line too long) must NOT be ignored; enforced at 120 chars

#### ✅ 3. Created QUALITY_GATE_BYPASS_AUDIT.md
- **Location:** `unified-cloud-services/QUALITY_GATE_BYPASS_AUDIT.md`
- **Documented:** 7 type ignores (5 `arg-type`, 1 psutil, 1 pandas)
- **Status:** All bypasses justified with removal plans

#### ✅ 4. Verified 12 codex compliance checks present
- All checks from instruments-service template present in quality-gates.sh
- Includes: print(), os.getenv(), datetime.now(), bare except, empty fallbacks, lazy imports, Any types, gitignore credentials, hardcoded project IDs, broad except, file size, pip-audit

#### ✅ 5. Verified CI/CD validators (CI-02, CI-03, CI-04) present
- CI-02: Local importability (BLOCKING)
- CI-03: GitHub installability (BLOCKING)
- CI-04: Artifact Registry readiness (BLOCKING)
- Already implemented in quality-gates.sh Step 5

---

### unified-config-interface

#### ✅ 1. Standardized Python version in GitHub Actions
- **Before:** `python-version: '3.13.9'`
- **After:** `python-version: '3.13'`
- **Reason:** Match instruments-service standard (use major.minor, not patch)

#### ✅ 2. Created QUALITY_GATE_BYPASS_AUDIT.md
- **Location:** `unified-config-interface/QUALITY_GATE_BYPASS_AUDIT.md`
- **Documented:** 6 type ignores (2 reportMissingImports, 2 reportAttributeAccessIssue, 3 test-only)
- **Status:** All bypasses justified with removal plans

#### ✅ 3. Verified all codex compliance checks present
- All 12 checks from instruments-service template present
- Already implemented in quality-gates.sh Step 4

#### ✅ 4. Verified CI/CD validators present
- CI-02, CI-03, CI-04 already implemented in Step 5
- Production readiness validators present in Step 6

---

## Quality Gate Results

### unified-cloud-services: ❌ FAILED (Pre-existing Issues)

**Blocking Issues:**
1. **Circular import error** (5 violations)
   - `unified_cloud_services/domain/clients.py` imports from `__init__.py`
   - `__init__.py` imports from `domain/clients.py`
   - **Impact:** Import sanity check fails, CI-02 validator fails

2. **Imports inside functions** (5 violations)
   - `domain/clients.py`: `import warnings` (2x)
   - `domain/date_validation.py`: circular import + `import math`
   - `domain/standardized_service.py`: `import threading`

3. **Any type usage** (5 violations)
   - `ml/model_registry.py`: `model: object` (2x)
   - `io/connection_pool.py`: `clients: list[Any]`, `get_client() -> Any`
   - `core/gcp_clients.py`: `__init__(self, native_blob: Any)`

4. **Hardcoded project IDs in tests** (5 violations)
   - `tests/integration/test_cloud_api_correctness.py:17`
   - `tests/conftest.py:103, 111, 118, 254`

5. **Broad except Exception** (5 violations)
   - `domain/standardized_service.py`, `ml/models.py`, `cli.py`, `__init__.py` (2x)

6. **File size violations** (2 files)
   - `core/unified_cloud_service.py`: 1750 lines (max 1500)
   - `domain/clients.py`: 1562 lines (max 1500)

**Total Violations:** 27

---

### unified-config-interface: ❌ FAILED (Pre-existing Issues)

**Blocking Issues:**
1. **Test failures** (3 tests)
   - `test_reloader.py`: 3 tests fail due to unified-cloud-services circular import
   - **Root cause:** unified-cloud-services import error propagates to UCI tests

2. **Empty string fallbacks** (3 violations)
   - `persistence.py:` `v.get("timestamp", "")`
   - `execution_config_schema.py:` `inst_config_typed.get("algorithm", "")`
   - `cloud_config.py:` `bucket_map.get((domain, ""))`

3. **CI-02 validator failure**
   - 2 libraries not locally importable (unified-cloud-services, unified-config-interface)
   - **Root cause:** unified-cloud-services circular import

**Total Violations:** 6

---

## Root Cause Analysis

Both repos fail quality gates due to **unified-cloud-services circular import**:

```python
# unified_cloud_services/__init__.py (line 152)
from unified_cloud_services.core.cloud_data_provider import CloudDataProviderBase

# unified_cloud_services/core/cloud_data_provider.py (line 25)
from unified_cloud_services.domain.standardized_service import StandardizedDomainCloudService

# unified_cloud_services/domain/clients.py (line 24)
from unified_cloud_services import get_instruments_bucket_for_category, get_storage_client
```

**Impact:**
- ❌ unified-cloud-services: Import sanity check fails
- ❌ unified-cloud-services: CI-02 validator fails (not locally importable)
- ❌ unified-config-interface: 3 tests fail (depend on UCS import)
- ❌ unified-config-interface: CI-02 validator fails (UCS dependency broken)

---

## Remediation Required

### Priority 1: Fix Circular Import (Blocking Both Repos)

**File:** `unified_cloud_services/domain/clients.py:24`

**Current:**
```python
from unified_cloud_services import get_instruments_bucket_for_category, get_storage_client
```

**Fix Options:**
1. **Move imports to function scope** (lazy import)
2. **Import from specific module** (not `__init__.py`)
3. **Refactor to remove circular dependency**

**Recommended:** Option 2 - Import from specific module
```python
from unified_cloud_services.core.gcp_clients import get_storage_client
from unified_cloud_services.domain.bucket_helpers import get_instruments_bucket_for_category
```

---

### Priority 2: Fix unified-cloud-services Violations

1. **Imports inside functions** (5 violations)
   - Move `import warnings`, `import math`, `import threading` to top of file
   - Document lazy imports with whitelist if needed for circular deps

2. **Any type usage** (5 violations)
   - `ml/model_registry.py`: Use `BaseModel` or specific type instead of `object`
   - `io/connection_pool.py`: Use `TypeVar` for generic client type
   - `core/gcp_clients.py`: Use proper GCS blob type

3. **Hardcoded project IDs** (5 violations)
   - Replace `central-element-323112` with `test-project` in tests

4. **Broad except Exception** (5 violations)
   - Use `@handle_api_errors` decorator or specific exceptions

5. **File size** (2 files)
   - Split `unified_cloud_service.py` (1750 lines) by SRP
   - Split `clients.py` (1562 lines) by domain client type

---

### Priority 3: Fix unified-config-interface Violations

1. **Empty string fallbacks** (3 violations)
   - `persistence.py`: Fail loud if timestamp missing
   - `execution_config_schema.py`: Fail loud if algorithm missing
   - `cloud_config.py`: Use None instead of empty string

---

## Standards Alignment Summary

| Standard | instruments-service | unified-cloud-services | unified-config-interface |
|----------|---------------------|------------------------|--------------------------|
| **Ruff line-length** | 120 | ✅ 120 (fixed) | ✅ 120 |
| **E501 enforced** | ✅ Yes | ✅ Yes (fixed) | ✅ Yes |
| **QUALITY_GATE_BYPASS_AUDIT.md** | ✅ Present | ✅ Created | ✅ Created |
| **12 codex checks** | ✅ All present | ✅ All present | ✅ All present |
| **CI/CD validators** | ✅ CI-02, CI-03, CI-04 | ✅ Present | ✅ Present |
| **Python version (GH Actions)** | 3.13 | N/A (no GH Actions) | ✅ 3.13 (fixed) |
| **Quality gates pass** | ✅ Pass | ❌ Fail (27 violations) | ❌ Fail (6 violations) |

---

## Next Steps

1. **Fix circular import** in unified-cloud-services (Priority 1 - blocks both repos)
2. **Fix empty fallbacks** in unified-config-interface (Priority 3 - quick win)
3. **Fix remaining violations** in unified-cloud-services (Priority 2 - larger effort)
4. **Re-run quality gates** to verify all checks pass
5. **Commit changes** via quickmerge

---

## Files Modified

### unified-cloud-services
- ✅ `pyproject.toml` - line-length 100 → 120, removed E501 from ignore
- ✅ `QUALITY_GATE_BYPASS_AUDIT.md` - created (7 type ignores documented)

### unified-config-interface
- ✅ `.github/workflows/quality-gates.yml` - Python 3.13.9 → 3.13
- ✅ `QUALITY_GATE_BYPASS_AUDIT.md` - created (6 type ignores documented)

---

## Commit Status

**Ready to commit:**
- ✅ unified-cloud-services: pyproject.toml, QUALITY_GATE_BYPASS_AUDIT.md
- ✅ unified-config-interface: .github/workflows/quality-gates.yml, QUALITY_GATE_BYPASS_AUDIT.md

**Blocked by pre-existing issues:**
- ❌ Quality gates fail due to circular import and other violations
- ❌ Cannot use quickmerge until quality gates pass

**Recommendation:** Commit documentation changes separately, then fix violations in follow-up PRs.
