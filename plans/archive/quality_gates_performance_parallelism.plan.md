---
doc_type: plan
title: "07: Quality Gates Performance"
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service, market-data-processing-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-02-25"
---

# 07: Quality Gates Performance

> **🛑 SUPERSEDED 2026-06-02 →
> [`plans/active/quality_gates_resource_contention_speedup_2026_06_02.md`](../active/quality_gates_resource_contention_speedup_2026_06_02.md).**
> This plan was an orphan in `plans/cicd/` (no `parent_epic:` / `assigned_vm:` / estimate frontmatter → invisible to the
> active inventory + orchestrator backlog), referenced dead `Documents/repos` paths + a ChatGPT convo, and its entire
> thesis was **add more per-run parallelism** (`pytest -n auto` everywhere, parallelize ruff). On a host running 8 slots
> × 2 sides of parallel agents, every slot already fires `-n auto` and they **contend** for the same CPU/RAM — more
> per-run parallelism makes aggregate oversubscription/thrash _worse_, not better. The successor plan reframes the goal
> as reducing/queueing aggregate resource consumption (cross-slot governor, slot-aware worker caps, do-less-work
> incremental gates, warm processes, persistent caches). Salvageable levers (slow-test marks, uv cache, selective
> testing) are carried forward there. Do NOT execute this file.

**Status**: ⬜ Superseded **Priority**: P2 (Faster feedback loops) **Estimated Time**: 2-3 hours **Expected Benefit**:
5-10 min/run, 30+ min/day saved

---

## 📖 Overview

Optimize quality gate execution to complete in <3 minutes (per codex standards). Use parallel execution, selective
testing, and caching to speed up feedback loops.

### Current State

- Quality gates take 5-15 minutes
- Run all tests every time
- No caching of dependencies
- Sequential execution

### Target State

- Quality gates complete in <3 minutes
- Parallel test execution (pytest-xdist)
- Selective testing (only changed files)
- Cached dependencies (uv cache)
- Quick mode for fast iteration

---

## 🔗 Dependencies

- **Requires**: CI/CD alignment (#03) for consistent performance
- **Enables**: Faster development iteration

---

## 🚧 Blockers

- [ ] Need to benchmark current performance
- [ ] Need to identify bottlenecks
- [ ] Need to ensure parallel tests are safe

---

## 🔍 Current Performance Analysis

### Step 1: Benchmark Current Performance

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service

# Time each step
time bash scripts/quality-gates.sh

# Expected output:
# Step 1: Ruff format ... (5s)
# Step 2: Ruff check ... (8s)
# Step 3: Basedpyright ... (15s)
# Step 4: Pytest ... (120s)
# Total: ~150s (2.5 minutes)
```

### Step 2: Identify Bottlenecks

```bash
# Profile pytest
pytest --durations=10 tests/

# Shows slowest 10 tests
# Example:
# 15.3s test_full_pipeline_integration
# 8.2s test_databento_api_real
# 5.1s test_process_all_instruments
```

### Step 3: Check Test Parallelization

```bash
# Check if pytest-xdist installed
pytest --version | grep xdist

# If not installed:
uv pip install pytest-xdist
```

---

## 🛠️ Implementation

### Part 1: Enable Parallel Test Execution

```bash
# instruments-service/scripts/quality-gates.sh

# Update pytest step to use parallel execution
echo "Step 4: Running tests..."
if [ "$QUICK_MODE" = "true" ]; then
    # Quick mode: skip slow tests, use all cores
    pytest -n auto -m "not slow" --cov=instruments_service --cov-report=term-missing --cov-report=html
else
    # Full mode: all tests, use all cores
    pytest -n auto --cov=instruments_service --cov-report=term-missing --cov-report=html
fi
```

**Expected speedup**: 2-4x faster (depending on CPU cores).

### Part 2: Implement Selective Testing

```bash
# instruments-service/scripts/quality-gates.sh

# Add selective testing option
if [ "$SELECTIVE" = "true" ]; then
    echo "Detecting changed files..."
    CHANGED_FILES=$(git diff --name-only main...HEAD | grep "\.py$" | grep -v "tests/" || true)

    if [ -z "$CHANGED_FILES" ]; then
        echo "No Python files changed, running all tests"
        TEST_ARGS=""
    else
        echo "Changed files:"
        echo "$CHANGED_FILES"

        # Convert file paths to test paths
        TEST_PATHS=""
        for file in $CHANGED_FILES; do
            # Convert src file to test file
            # Example: instruments_service/main.py → tests/unit/test_main.py
            TEST_FILE=$(echo "$file" | sed 's|instruments_service/|tests/unit/test_|' | sed 's|\.py$|\.py|')
            if [ -f "$TEST_FILE" ]; then
                TEST_PATHS="$TEST_PATHS $TEST_FILE"
            fi
        done

        if [ -z "$TEST_PATHS" ]; then
            echo "No corresponding test files found, running all tests"
            TEST_ARGS=""
        else
            echo "Running tests: $TEST_PATHS"
            TEST_ARGS="$TEST_PATHS"
        fi
    fi

    pytest -n auto $TEST_ARGS --cov=instruments_service --cov-report=term-missing
else
    # Run all tests
    pytest -n auto --cov=instruments_service --cov-report=term-missing
fi
```

Usage:

```bash
# Run only tests for changed files
SELECTIVE=true bash scripts/quality-gates.sh
```

### Part 3: Add Dependency Caching

```yaml
# .github/workflows/quality-gates.yml

jobs:
  quality-gates:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Cache uv dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.cache/uv
            .venv
          key: ${{ runner.os }}-uv-${{ hashFiles('**/pyproject.toml', '**/uv.lock') }}
          restore-keys: |
            ${{ runner.os }}-uv-

      - name: Cache ruff
        uses: actions/cache@v3
        with:
          path: ~/.cache/ruff
          key: ${{ runner.os }}-ruff-${{ hashFiles('**/*.py') }}
          restore-keys: |
            ${{ runner.os }}-ruff-

      # Rest of workflow...
```

**Expected speedup**: 30-60s saved on dependency installation.

### Part 4: Mark Slow Tests

```python
# tests/integration/test_full_pipeline.py

import pytest

@pytest.mark.slow
def test_full_pipeline_integration():
    """
    Full end-to-end pipeline test.

    Marked as slow - skipped in quick mode.
    """
    # Test implementation
    pass

@pytest.mark.slow
def test_databento_api_real():
    """
    Real API call to Databento.

    Marked as slow - skipped in quick mode.
    """
    # Test implementation
    pass
```

Update pytest config:

```toml
# pyproject.toml

[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
]
```

### Part 5: Optimize Ruff Execution

```bash
# instruments-service/scripts/quality-gates.sh

# Run ruff check and format in parallel
echo "Step 1-2: Running ruff (parallel)..."
(
    ruff format instruments_service/ tests/ &
    RUFF_FORMAT_PID=$!

    ruff check --fix instruments_service/ tests/ &
    RUFF_CHECK_PID=$!

    wait $RUFF_FORMAT_PID
    wait $RUFF_CHECK_PID
)
```

**Expected speedup**: 2-3s saved.

### Part 6: Create Performance Monitoring

```bash
# deployment-service/scripts/benchmark-quality-gates.sh
#!/bin/bash

set -e

echo "=== Quality Gates Performance Benchmark ==="
echo ""

SERVICES=(
    "instruments-service"
    "market-tick-data-handler"
    "market-data-processing-service"
    "unified-trading-services"
)

RESULTS_FILE="quality-gates-benchmark-$(date +%Y%m%d-%H%M%S).csv"
echo "Service,Total,Ruff,Basedpyright,Pytest" > "$RESULTS_FILE"

for service in "${SERVICES[@]}"; do
    if [ ! -d "$service" ]; then
        echo "⚠️  Skipping $service (not found)"
        continue
    fi

    echo "Benchmarking $service..."
    cd "$service"

    # Time total
    TOTAL_START=$(date +%s)

    # Time ruff
    RUFF_START=$(date +%s)
    ruff format . > /dev/null 2>&1 || true
    ruff check --fix . > /dev/null 2>&1 || true
    RUFF_END=$(date +%s)
    RUFF_TIME=$((RUFF_END - RUFF_START))

    # Time basedpyright
    PYRIGHT_START=$(date +%s)
    basedpyright . > /dev/null 2>&1 || true
    PYRIGHT_END=$(date +%s)
    PYRIGHT_TIME=$((PYRIGHT_END - PYRIGHT_START))

    # Time pytest
    PYTEST_START=$(date +%s)
    pytest -n auto -m "not slow" > /dev/null 2>&1 || true
    PYTEST_END=$(date +%s)
    PYTEST_TIME=$((PYTEST_END - PYTEST_START))

    TOTAL_END=$(date +%s)
    TOTAL_TIME=$((TOTAL_END - TOTAL_START))

    echo "$service,$TOTAL_TIME,$RUFF_TIME,$PYRIGHT_TIME,$PYTEST_TIME" >> "../$RESULTS_FILE"

    echo "  Total: ${TOTAL_TIME}s (Ruff: ${RUFF_TIME}s, Pyright: ${PYRIGHT_TIME}s, Pytest: ${PYTEST_TIME}s)"

    cd ..
done

echo ""
echo "✅ Benchmark complete: $RESULTS_FILE"
echo ""
echo "Summary:"
column -t -s',' "$RESULTS_FILE"
```

Make executable:

```bash
chmod +x deployment-service/scripts/benchmark-quality-gates.sh
```

---

## ✅ Verification

### Test 1: Parallel Execution Works

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service

# Run with parallel execution
time pytest -n auto tests/

# Should use all CPU cores
# Check with: top or htop during execution
```

### Test 2: Quick Mode Skips Slow Tests

```bash
# Run quick mode
time pytest -n auto -m "not slow" tests/

# Should be significantly faster than full run
```

### Test 3: Selective Testing Works

```bash
# Make a change to one file
echo "# test change" >> instruments_service/main.py

# Run selective tests
SELECTIVE=true bash scripts/quality-gates.sh

# Should only run tests related to main.py
```

### Test 4: Performance Target Met

```bash
# Run full quality gates
time bash scripts/quality-gates.sh --quick

# Should complete in <3 minutes (180 seconds)
```

---

## 📊 Success Metrics

### Before Optimization

- Total time: 5-15 minutes
- Ruff: 10-15s
- Basedpyright: 15-20s
- Pytest: 120-180s (sequential)

### After Optimization

- [ ] Total time: <3 minutes (target)
- [ ] Ruff: 5-8s (parallel format + check)
- [ ] Basedpyright: 10-15s (unchanged)
- [ ] Pytest: 30-60s (parallel, quick mode)

### Additional Metrics

- [ ] Parallel execution enabled (pytest-xdist)
- [ ] Slow tests marked and skippable
- [ ] Selective testing works
- [ ] CI caching reduces install time by 30-60s
- [ ] 5-10 min saved per run
- [ ] 30+ min saved per day (6+ runs)

---

## 🔄 Rollback Plan

If optimizations cause issues:

1. Disable parallel execution (remove `-n auto`)
2. Run all tests (remove selective testing)
3. Remove slow test markers
4. Keep caching (no downside)

---

## 📚 Related Documentation

- ChatGPT conversation: Lines 167-171 (quality gates performance)
- Quality gates guide: `unified-trading-/codex/06-coding-standards/quality-gates.md`
- Quality gate optimization: `.cursor/rules/quality-gate-optimization.mdc`
- pytest-xdist docs: https://pytest-xdist.readthedocs.io

---

## 💡 Tips

1. **Use quick mode for iteration**: `--quick` flag skips slow tests
2. **Mark integration tests as slow**: Keep unit tests fast
3. **Profile regularly**: Run benchmark script monthly
4. **Cache aggressively**: Dependencies rarely change
5. **Parallelize everything**: Ruff, pytest, even basedpyright (if possible)

---

## ✏️ Notes

- Target: <3 minutes per codex standards
- Parallel execution gives 2-4x speedup
- Quick mode gives another 2-3x speedup
- Combined: 4-12x faster (15 min → 1-4 min)
- Expected to save 30+ min/day
- Faster feedback = faster development
