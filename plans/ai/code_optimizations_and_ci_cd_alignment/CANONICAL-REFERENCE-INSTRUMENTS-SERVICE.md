# Canonical Reference: instruments-service

**Status**: ✅ Hardened to Audit Quality  
**Purpose**: Use as template/reference for all other services  
**Last Updated**: 2026-02-24

---

## Why instruments-service is Canonical

**instruments-service has been hardened to audit quality standards:**

1. **Quality Gates**: Complete implementation with act simulation
2. **GitHub Actions**: Proper workflow with all quality checks
3. **PR Watcher**: (Check implementation) - LLM feedback via PR comments
4. **Dependencies**: Correct path dependency setup
5. **Type Checking**: basedpyright with strict settings
6. **Test Coverage**: Meets audit standards
7. **File Structure**: All files under limits
8. **Configuration**: Proper config class usage (no os.getenv)
9. **Error Handling**: No silent failures
10. **Event Logging**: Complete lifecycle events

---

## What to Copy from instruments-service

### 1. Quality Gates Script

**Location**: `instruments-service/scripts/quality-gates.sh`

**Key Features**:
- Uses `act` for local GitHub Actions simulation
- Docker parity (same environment as CI)
- 300s timeout enforcement
- Proper dependency installation order
- basedpyright for type checking
- Coverage thresholds enforced

### 2. GitHub Actions Workflow

**Location**: `instruments-service/.github/workflows/quality-gates.yml`

**Key Features**:
- Timeout: 15 minutes (900s) for GitHub, but actual quality gates timeout at 300s
- Proper dependency cloning to `../` (matches pyproject.toml)
- Uses `uv pip install --system` after `pip install uv` bootstrap
- basedpyright (not pyright)
- pytest with `-n auto` (parallel execution)
- Coverage fail-under: 35%
- ripgrep installed for codex checks

### 3. pyproject.toml Configuration

**Location**: `instruments-service/pyproject.toml`

**Key Sections**:
```toml
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.basedpyright]
typeCheckingMode = "standard"
reportAny = "error"
pythonVersion = "3.13"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers --tb=short"
```

### 4. Dependency Management

**pyproject.toml dependencies**:
```toml
[project]
dependencies = [
    "pydantic>=2.10.4,<3.0.0",
    "pydantic-settings>=2.7.1,<3.0.0",
    # ... all explicit dependencies
]

[tool.uv.sources]
unified-cloud-services = { path = "../unified-cloud-services" }
unified-config-interface = { path = "../unified-config-interface" }
unified-events-interface = { path = "../unified-events-interface" }
unified-domain-services = { path = "../unified-domain-services" }
unified-market-interface = { path = "../unified-market-interface" }
api-contracts = { path = "../api-contracts" }
```

### 5. quickmerge Script

**Location**: `instruments-service/scripts/quickmerge.sh`

**Key Features**:
- Pre-flight audit (dependency validation)
- Uses act for quality gates (Stage 4 in Master Plan)
- Handles failures inline (max 3 attempts)
- Creates PR with auto-merge
- Proper branch management

### 6. PR Watcher (Verify Implementation)

**Location**: Check `.github/workflows/` for pr-watcher or similar

**Expected Features**:
- Runs on `pull_request` events
- LLM analysis of PR diff
- Posts feedback as PR comments (separate context)
- Blocks merge if critical issues
- Uses CURSOR_API_KEY or ANTHROPIC_API_KEY

---

## How to Use as Reference

### For New Services

1. **Copy structure**:
   ```bash
   cp instruments-service/scripts/quality-gates.sh my-service/scripts/
   cp instruments-service/.github/workflows/quality-gates.yml my-service/.github/workflows/
   ```

2. **Adapt for service-specific needs**:
   - Update service name
   - Update dependencies in pyproject.toml
   - Update test paths if different
   - Keep timeout at 300s

3. **Verify alignment**:
   ```bash
   cd my-service
   bash scripts/quality-gates.sh
   act -j quality-gates --secret-file ~/.secrets
   ```

### For Existing Services

1. **Compare with instruments-service**:
   ```bash
   diff my-service/scripts/quality-gates.sh instruments-service/scripts/quality-gates.sh
   diff my-service/.github/workflows/quality-gates.yml instruments-service/.github/workflows/quality-gates.yml
   ```

2. **Identify gaps**:
   - Missing act simulation?
   - Wrong timeout (not 300s)?
   - Using pyright instead of basedpyright?
   - Missing ripgrep for codex checks?

3. **Update to match**:
   - Copy pattern from instruments-service
   - Test locally with act
   - Verify in CI

---

## Verification Checklist

Use this to verify a service matches instruments-service standards:

- [ ] quality-gates.sh uses `act` for local simulation
- [ ] quality-gates.sh timeout: 300s
- [ ] GitHub Actions timeout: 15 min (900s), but quality gates fail at 300s
- [ ] Uses basedpyright (not pyright)
- [ ] Dependencies cloned to `../` (matches pyproject.toml)
- [ ] Uses `uv pip install --system` after `pip install uv`
- [ ] pytest runs with `-n auto` (parallel)
- [ ] Coverage threshold: 35% minimum
- [ ] ripgrep installed (for codex checks)
- [ ] No os.getenv in production code (use config classes)
- [ ] No silent failures (all exceptions logged)
- [ ] Event logging complete (12 lifecycle events)
- [ ] Files under 1500 LOC limit
- [ ] Tests passing (0 failures)
- [ ] PR watcher workflow exists (check)

---

## Common Patterns from instruments-service

### 1. Config Classes (Not os.getenv)

```python
from unified_config_interface import UnifiedCloudConfig

class InstrumentsServiceConfig(UnifiedCloudConfig):
    service_name: str = "instruments-service"
    # ... service-specific config
    
config = InstrumentsServiceConfig()
# Use: config.gcp_project_id (not os.getenv("GCP_PROJECT_ID"))
```

### 2. Error Handling (Never Silent)

```python
try:
    risky_operation()
except SpecificError as e:
    logger.error("Operation failed", extra={"error": str(e)})
    raise  # or handle appropriately, but NEVER silently pass
```

### 3. Event Logging

```python
from unified_events_interface import setup_events, log_event

setup_events(service_name="my-service", mode="batch")
log_event("STARTED")
# ... lifecycle events
log_event("STOPPED")
```

### 4. Type Annotations

```python
def process_data(
    data: list[dict[str, str]],  # Modern syntax (not List[Dict[...]])
    batch_size: int = 1000
) -> dict[str, int]:  # Explicit return type
    """Always include docstring with types."""
    pass
```

---

## When instruments-service Changes

If instruments-service quality gates or configuration changes:

1. **Document the change** here
2. **Update Master CI/CD Plan** if workflow changes
3. **Notify all teams** - other services should adopt changes
4. **Update this reference doc** within 24 hours

---

## Related Documentation

- **Master CI/CD Plan**: `.cursor/plans/code_optimizations_and_ci_cd_alignment/00-MASTER-CICD-PLAN.md`
- **Dependency Matrix**: `.cursor/plans/code_optimizations_and_ci_cd_alignment/DEPENDENCY-MATRIX-CANONICAL.json`
- **Standards Guide**: `AUDIT_TO_A_GRADE_ROADMAP/STANDARDS_COMPLIANCE_GUIDE.md`
- **Codex**: `unified-trading-codex/06-coding-standards/`

---

**Rule**: When in doubt, check instruments-service first. It's audit-quality hardened.
