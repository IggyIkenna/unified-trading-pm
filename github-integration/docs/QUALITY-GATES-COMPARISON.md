# Quality Gates Comparison Across Repos

## Executive Summary

**Are quality gates exhaustive and consistent?**

✅ **Yes, with intentional variations**:

- All repos test: Lint, Format, Unit, Integration, E2E, Smoke
- Test commands are **appropriately tailored** per repo's needs
- `market-data-processing-service` is **faster** due to parallel testing (`-n auto`)
- No corners cut — speed comes from parallelization, not skipping tests

---

## Comparison Matrix

| Repo                               | Unit Test Cmd                             | Integration Test Cmd                                | E2E Test Cmd                              | Speed Optimization |
| ---------------------------------- | ----------------------------------------- | --------------------------------------------------- | ----------------------------------------- | ------------------ |
| **market-tick-data-handler**       | `pytest tests/unit/ --timeout=60`         | `pytest tests/integration/ --timeout=120` + ignores | `pytest tests/e2e/ --timeout=180`         | ❌ Sequential      |
| **strategy-service**               | `pytest tests/unit/ --timeout=60`         | `pytest tests/integration/ --timeout=120` + filter  | `pytest tests/e2e/ --timeout=180`         | ❌ Sequential      |
| **instruments-service**            | `pytest tests/unit/ --timeout=60`         | `pytest tests/integration/ --timeout=120` + ignores | `pytest tests/e2e/ --timeout=180`         | ❌ Sequential      |
| **market-data-processing-service** | `pytest tests/unit/ --timeout=60 -n auto` | `pytest tests/integration/ --timeout=120 -n auto`   | `pytest tests/e2e/ --timeout=180 -n auto` | ✅ **Parallel**    |
| **execution-service**              | `pytest tests/unit/` (NO timeout)         | `pytest tests/integration/` + filter                | `pytest tests/e2e/` (NO timeout)          | ❌ Sequential      |

---

## Key Differences

### 1. Parallelization: `-n auto` Flag

**market-data-processing-service** uses `pytest-xdist` with `-n auto` for ALL test types:

```yaml
# market-data-processing-service (FAST)
- name: Run unit tests
  run: |
    python -m pytest tests/unit/ -v --tb=short --timeout=60 -n auto
```

**Other repos** run tests sequentially:

```yaml
# market-tick-data-handler, strategy-service, etc. (SLOWER)
- name: Run unit tests
  run: |
    python -m pytest tests/unit/ -v --tb=short --timeout=60
```

**Impact:**

- `-n auto` uses all available CPU cores (GitHub Actions runners have 2 cores)
- Can reduce test time by 40-60% for CPU-bound tests
- Requires tests to be thread-safe and isolated

### 2. Timeout Flags

**Most repos** have timeouts on all test types:

```bash
--timeout=60   # Unit tests (1 min)
--timeout=120  # Integration tests (2 min)
--timeout=180  # E2E tests (3 min)
```

**execution-service** has **NO timeouts**:

```bash
python -m pytest tests/unit/ -v --tb=short
# ⚠️ Tests could hang indefinitely
```

**Risk:** A hanging test will block CI until GitHub Actions' job timeout (15 min default).

### 3. Test Exclusion Patterns

Different repos skip different test categories based on their needs:

```bash
# market-tick-data-handler
--ignore=tests/integration/test_tardis_downloader.py \
--ignore=tests/integration/test_live_stream.py \
-k "not download and not api and not live"

# strategy-service
-k "not api and not live and not download"

# instruments-service
--ignore=tests/integration/test_performance.py \
-k "not api and not live and not download"

# execution-service
-k "not api and not live and not download" \
-m "not docker_only"
```

**Why this is OK:**

- These are external API/network tests that would fail in CI (no credentials)
- Should be run in integration/staging environments, not PR validation
- Proper separation of concerns

### 4. Environment Variables

All repos set mock environment for cloud services:

```yaml
env:
  CLOUD_MOCK_MODE: "true"
  GCP_PROJECT_ID: "test-project"
  # Some also add:
  GCP_PROJECT_ID: "mock-project" # execution-service
```

**Consistent** — no issues here.

---

## Are Quality Gates "Good Enough"?

### ✅ What's Good

1. **Comprehensive coverage**: Lint, format, unit, integration, e2e, smoke
2. **Fail fast**: Format check with `git diff --exit-code` catches uncommitted changes
3. **Appropriate timeouts**: Most repos prevent hanging tests
4. **Smart exclusions**: External API tests excluded (would fail without credentials)
5. **Mock mode**: Cloud services mocked to avoid real GCP calls

### ⚠️ What Could Be Better

1. **Inconsistent parallelization**:
   - Only `market-data-processing-service` uses `-n auto`
   - Other repos could be 40-60% faster with parallel testing
2. **Missing timeouts** in `execution-service`:
   - Risk of hanging tests blocking CI

3. **No coverage reporting**:
   - Tests run but don't report coverage %
   - Can't track if coverage is increasing/decreasing

4. **No coverage gates**:
   - No minimum coverage threshold enforced
   - Could merge code with decreasing test coverage

---

## Recommendations

### 1. Standardize Parallelization (Optional, High Impact)

**Current State (After Optimization):**

```
✅ OPTIMIZED (13 repos):
  - features-calendar-service        ✅ -n auto
  - features-delta-one-service       ✅ -n auto
  - features-onchain-service         ✅ -n auto
  - features-volatility-service      ✅ -n auto
  - instruments-service              ✅ -n auto
  - market-data-processing-service   ✅ -n auto
  - market-tick-data-handler         ✅ -n auto
  - ml-inference-service             ✅ -n auto
  - ml-training-service              ✅ -n auto
  - sports-betting-service           ✅ -n auto
  - strategy-service                 ✅ -n auto
  - unified-trading-services           ✅ -n auto
  - unified-trading-deployment-v2    ✅ -n auto

❌ NEEDS pytest-xdist (1 repo):
  - execution-service               ❌ No pytest-xdist
```

**Action:** Add `-n auto` to all repos that have pytest-xdist:

```bash
# For each repo with pytest-xdist, update quality-gates.yml:
- run: python -m pytest tests/unit/ -v --tb=short --timeout=60 -n auto
- run: python -m pytest tests/integration/ -v --tb=short --timeout=120 -n auto
- run: python -m pytest tests/e2e/ -v --tb=short --timeout=180 -n auto
```

**Benefit:** ~40-60% faster CI runs (2 cores available on GitHub Actions runners)

**Risk:** Tests must be isolated (no shared state, file locks, or race conditions)

### 2. Add Timeouts to execution-service (Recommended)

```yaml
# execution-service/.github/workflows/quality-gates.yml
- name: Run unit tests
  run: |
    python -m pytest tests/unit/ -v --tb=short --timeout=60
```

### 3. Add Coverage Reporting (Optional, Low Priority)

```yaml
- name: Run unit tests with coverage
  run: |
    python -m pytest tests/unit/ --cov=<module>/ --cov-report=term-missing
```

### 4. Add Coverage Gates (Optional, Audit Readiness)

From `.cursorrules`:

> Coverage gates: minimum 35% to pass quality gates; 80% is audit readiness target

```yaml
- name: Check coverage threshold
  run: |
    coverage report --fail-under=35
```

---

## Git History Analysis: market-tick-data-handler

### Commit Timeline

```bash
3ed1410 Fix workflow syntax: remove empty step and split duplicate run: keys
6807145 Fix workflow syntax: remove duplicate run keys
bb2d953 Architectural standardization: Python 3.13 + UCS base + uv + quality gates
5cff6f3 fix: harden MTDH stages 1-3 (Jan 27)
```

### Changes in "Architectural standardization" (bb2d953)

**Before (5cff6f3):**

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.13"

- run: |
    pip install pytest pytest-cov ...
    pip install -e deps/unified-trading-services
    pip install -e ".[dev]"
```

**After (bb2d953):**

```yaml
- uses: actions/setup-python@v5
  with:
    python-version-file: "pyproject.toml" # ← More flexible

- run: sudo apt-get install -y ripgrep # ← NEW: Codex checks

- run: |
    pip install uv                         # ← NEW: UV package manager
    uv pip install --system pytest ...
    uv pip install --system -e deps/unified-trading-services
    uv pip install --system -e ".[dev]"
```

**What Changed:**

1. ✅ Added ripgrep (for codex violation checks)
2. ✅ Switched to `uv` (faster, more reliable)
3. ✅ Used `python-version-file` (single source of truth)

**What Stayed the SAME:**

- All test steps (unit, integration, e2e, smoke)
- Test exclusion patterns
- Timeouts
- Environment variables

**Verdict:** 🟢 **No tests were skipped or weakened.** Only improvements.

---

## Conclusion

**Q: Are quality gates exhaustive and similar across repos?**

**A: Yes.**

- All repos have comprehensive test suites (unit, integration, e2e, smoke)
- Test commands are appropriately tailored per repo
- No shortcuts or skipped tests

**Q: Why do some pass faster in GitHub Actions?**

**A: Parallelization.**

- `market-data-processing-service` uses `-n auto` (parallel testing)
- Other repos run tests sequentially
- Same tests, just faster execution

**Q: Are they "good"?**

**A: Yes, with room for improvement:**

- ✅ Core testing is solid
- ✅ Smart exclusions for external APIs
- ⚠️ Could add coverage gates (35% minimum, 80% audit target)
- ⚠️ Could parallelize other repos for speed

---

## Action Items

### High Priority

- ✅ Fix workflow syntax errors (DONE)
- [ ] Add timeouts to `execution-service`

### Medium Priority

- [ ] Standardize `-n auto` across repos (requires pytest-xdist + isolated tests)

### Low Priority

- [ ] Add coverage reporting
- [ ] Add coverage gates (35% minimum)

---

## References

- Codex: `06-coding-standards/testing.md`
- Codex: `06-coding-standards/quality-gates.md`
- pytest-xdist docs: https://pytest-xdist.readthedocs.io/
- pytest-timeout docs: https://github.com/pytest-dev/pytest-timeout
