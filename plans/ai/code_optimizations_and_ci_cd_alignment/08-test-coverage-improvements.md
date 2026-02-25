# 08: Test Coverage Improvements

**Status**: ⬜ Not Started  
**Priority**: P3 (Better code quality)  
**Estimated Time**: Ongoing (incremental)  
**Expected Benefit**: Fewer bugs, easier refactoring, better confidence

---

## 📖 Overview

Improve test coverage from ~30% to 50%+ by structuring code for testability and following best practices. Make it easier for LLMs to generate high-quality tests.

### Current State
- Test coverage: ~30% across services
- LLMs struggle to write comprehensive tests
- Large, complex functions hard to test
- Many edge cases untested

### Target State
- Test coverage: 50%+ (recommended per codex)
- Small, focused functions (easy to test)
- Clear interfaces and contracts
- LLMs can generate tests effectively

---

## 🔗 Dependencies

- **Requires**: Quality gates performance (#07) for fast test execution
- **Enables**: Confident refactoring, fewer production bugs

---

## 🚧 Blockers

- [ ] Need to refactor large functions (time-consuming)
- [ ] Need to establish testing patterns
- [ ] Need to train LLMs on good test examples

---

## 🔍 Current Coverage Analysis

### Step 1: Generate Coverage Report

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/instruments-service

# Run tests with coverage
pytest --cov=instruments_service --cov-report=html --cov-report=term-missing

# Open HTML report
open htmlcov/index.html

# Identify files with <50% coverage
```

### Step 2: Analyze Low-Coverage Files

```bash
# Find files with <50% coverage
pytest --cov=instruments_service --cov-report=term-missing | grep -E "^\S+\s+[0-4][0-9]%"

# Example output:
# instruments_service/main.py              35%
# instruments_service/processors/base.py   28%
# instruments_service/adapters/ccxt.py     42%
```

---

## 🛠️ Implementation

### Part 1: Establish Testing Patterns

#### Pattern 1: Small, Testable Functions

❌ **Bad** (hard to test):

```python
def process_all_data(config: dict[str, Any]) -> None:
    """500-line function doing everything."""
    # Load data
    client = storage.Client()
    bucket = client.bucket(config["bucket"])
    blob = bucket.blob(config["path"])
    data = blob.download_as_text()
    df = pd.read_csv(io.StringIO(data))
    
    # Validate
    if df.empty:
        raise ValueError("Empty data")
    if "symbol" not in df.columns:
        raise ValueError("Missing symbol column")
    
    # Transform
    df["canonical_key"] = df["venue"] + "_" + df["symbol"]
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    # Upload
    output_blob = bucket.blob(config["output_path"])
    output_blob.upload_from_string(df.to_parquet())
```

✅ **Good** (easy to test):

```python
def load_data_from_gcs(bucket: str, path: str) -> pd.DataFrame:
    """Load CSV from GCS."""
    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    blob = bucket_obj.blob(path)
    data = blob.download_as_text()
    return pd.read_csv(io.StringIO(data))

def validate_data(df: pd.DataFrame, required_columns: list[str]) -> None:
    """Validate dataframe has required columns."""
    if df.empty:
        raise ValueError("Empty data")
    
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform dataframe."""
    df = df.copy()
    df["canonical_key"] = df["venue"] + "_" + df["symbol"]
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def upload_data_to_gcs(df: pd.DataFrame, bucket: str, path: str) -> None:
    """Upload dataframe to GCS."""
    client = storage.Client()
    bucket_obj = client.bucket(bucket)
    blob = bucket_obj.blob(path)
    blob.upload_from_string(df.to_parquet())

def process_all_data(config: Config) -> None:
    """Orchestrate data processing."""
    df = load_data_from_gcs(config.bucket, config.input_path)
    validate_data(df, required_columns=["venue", "symbol", "timestamp"])
    df = transform_data(df)
    upload_data_to_gcs(df, config.bucket, config.output_path)
```

**Tests** (easy to write):

```python
def test_load_data_from_gcs(mock_storage_client):
    """Test loading data from GCS."""
    df = load_data_from_gcs("test-bucket", "test.csv")
    assert not df.empty
    assert "symbol" in df.columns

def test_validate_data_empty():
    """Test validation fails on empty data."""
    df = pd.DataFrame()
    with pytest.raises(ValueError, match="Empty data"):
        validate_data(df, required_columns=["symbol"])

def test_validate_data_missing_columns():
    """Test validation fails on missing columns."""
    df = pd.DataFrame({"venue": ["BINANCE"]})
    with pytest.raises(ValueError, match="Missing columns"):
        validate_data(df, required_columns=["venue", "symbol"])

def test_transform_data():
    """Test data transformation."""
    df = pd.DataFrame({
        "venue": ["BINANCE"],
        "symbol": ["BTC/USDT"],
        "timestamp": ["2024-01-01 00:00:00"]
    })
    result = transform_data(df)
    assert "canonical_key" in result.columns
    assert result["canonical_key"].iloc[0] == "BINANCE_BTC/USDT"
    assert result["timestamp"].dtype == "datetime64[ns]"
```

#### Pattern 2: Dependency Injection

❌ **Bad** (hard to mock):

```python
def save_results(data: pd.DataFrame) -> None:
    """Save results to GCS."""
    client = storage.Client()  # Hard-coded dependency
    bucket = client.bucket("my-bucket")
    blob = bucket.blob("output.parquet")
    blob.upload_from_string(data.to_parquet())
```

✅ **Good** (easy to mock):

```python
def save_results(data: pd.DataFrame, storage_client: StorageClient) -> None:
    """Save results to GCS."""
    bucket = storage_client.bucket("my-bucket")
    blob = bucket.blob("output.parquet")
    blob.upload_from_string(data.to_parquet())

# Test with mock:
def test_save_results():
    mock_client = Mock(spec=StorageClient)
    save_results(df, mock_client)
    mock_client.bucket.assert_called_once_with("my-bucket")
```

#### Pattern 3: Clear Interfaces

```python
from typing import Protocol

class DataLoader(Protocol):
    """Protocol for data loaders."""
    def load(self, path: str) -> pd.DataFrame: ...

class GCSDataLoader:
    """Load data from GCS."""
    def load(self, path: str) -> pd.DataFrame:
        # Implementation
        pass

class LocalDataLoader:
    """Load data from local filesystem."""
    def load(self, path: str) -> pd.DataFrame:
        # Implementation
        pass

def process_data(loader: DataLoader, path: str) -> pd.DataFrame:
    """Process data from any loader."""
    df = loader.load(path)
    # Process...
    return df

# Tests can use either real or mock loaders:
def test_process_data_gcs():
    loader = GCSDataLoader()
    result = process_data(loader, "gs://bucket/file.csv")
    assert not result.empty

def test_process_data_local():
    loader = LocalDataLoader()
    result = process_data(loader, "/tmp/file.csv")
    assert not result.empty

def test_process_data_mock():
    mock_loader = Mock(spec=DataLoader)
    mock_loader.load.return_value = pd.DataFrame({"col": [1, 2, 3]})
    result = process_data(mock_loader, "any-path")
    assert len(result) == 3
```

### Part 2: Create Test Templates for LLMs

```python
# tests/templates/test_template.py
"""
Test template for LLMs to follow.

This template demonstrates best practices for writing tests.
"""
import pytest
from unittest.mock import Mock, patch
import pandas as pd

# ============================================================================
# Unit Tests (Fast, No External Dependencies)
# ============================================================================

def test_function_happy_path():
    """Test function with valid input."""
    result = my_function(valid_input)
    assert result == expected_output

def test_function_edge_case_empty():
    """Test function with empty input."""
    result = my_function([])
    assert result == []

def test_function_edge_case_null():
    """Test function with null input."""
    with pytest.raises(ValueError, match="Input cannot be None"):
        my_function(None)

def test_function_with_mock():
    """Test function with mocked dependency."""
    mock_client = Mock()
    mock_client.fetch.return_value = {"data": "test"}
    
    result = my_function(mock_client)
    
    mock_client.fetch.assert_called_once()
    assert result["data"] == "test"

# ============================================================================
# Integration Tests (Slower, May Use Real Dependencies)
# ============================================================================

@pytest.mark.integration
def test_integration_with_real_gcs():
    """Test with real GCS (requires credentials)."""
    # Use test bucket
    result = load_from_gcs("test-bucket", "test-file.csv")
    assert not result.empty

# ============================================================================
# Parametrized Tests (Test Multiple Cases)
# ============================================================================

@pytest.mark.parametrize("input,expected", [
    ("BINANCE", "binance"),
    ("Coinbase", "coinbase"),
    ("KRAKEN", "kraken"),
])
def test_normalize_venue(input, expected):
    """Test venue normalization with multiple inputs."""
    assert normalize_venue(input) == expected

# ============================================================================
# Fixtures (Reusable Test Data)
# ============================================================================

@pytest.fixture
def sample_dataframe():
    """Sample dataframe for testing."""
    return pd.DataFrame({
        "venue": ["BINANCE", "COINBASE"],
        "symbol": ["BTC/USDT", "ETH/USD"],
        "price": [50000.0, 3000.0]
    })

def test_with_fixture(sample_dataframe):
    """Test using fixture."""
    result = process_dataframe(sample_dataframe)
    assert len(result) == 2
```

### Part 3: Refactor Low-Coverage Files

**Process**:

1. Identify file with <50% coverage
2. Break large functions into smaller ones
3. Add dependency injection
4. Write tests for each small function
5. Verify coverage improved

**Example**:

```bash
# Before refactoring
pytest --cov=instruments_service/main.py --cov-report=term-missing
# main.py  35%

# Refactor main.py (break into smaller functions)
# Write tests for each function

# After refactoring
pytest --cov=instruments_service/main.py --cov-report=term-missing
# main.py  75%
```

### Part 4: Add Coverage Targets to Quality Gates

```bash
# instruments-service/scripts/quality-gates.sh

echo "Step 4: Running tests with coverage..."
pytest -n auto --cov=instruments_service --cov-report=term-missing --cov-report=html \
    --cov-fail-under=35  # Minimum 35% (blocking per codex)

# For production readiness, use 50%:
# --cov-fail-under=50
```

---

## ✅ Verification

### Test 1: Coverage Improved

```bash
# Before improvements
pytest --cov=instruments_service --cov-report=term-missing
# Coverage: 30%

# After improvements
pytest --cov=instruments_service --cov-report=term-missing
# Coverage: 50%+
```

### Test 2: LLM Can Generate Tests

Prompt LLM:

```
Generate comprehensive tests for this function:

[paste function code]

Follow the test template in tests/templates/test_template.py
```

**Expected**: LLM generates tests covering:
- Happy path
- Edge cases (empty, null, invalid)
- Error conditions
- Mocked dependencies

### Test 3: Tests Are Fast

```bash
# Unit tests should be fast (<30s)
time pytest tests/unit/ -n auto

# Should complete in <30 seconds
```

---

## 📊 Success Metrics

### Coverage Targets (Per Codex)
- [ ] 35% minimum (quality gates - blocking)
- [ ] 50% recommended (production readiness)
- [ ] 80% goal (audit readiness)

### Code Structure
- [ ] Average function length <50 lines
- [ ] No functions >200 lines
- [ ] Dependency injection used
- [ ] Clear interfaces/protocols defined

### Test Quality
- [ ] Unit tests run in <30s
- [ ] Integration tests run in <2 minutes
- [ ] All tests pass consistently
- [ ] No flaky tests

---

## 🔄 Rollback Plan

If refactoring causes issues:

1. Keep old functions alongside new ones
2. Gradually migrate callers
3. Remove old functions when confident
4. Tests provide safety net

---

## 📚 Related Documentation

- ChatGPT conversation: Lines 172-190 (test coverage discussion)
- Test coverage guide: `.cursor/rules/test-coverage-targets.mdc`
- Test quality standards: `.cursor/rules/test-quality-standards.mdc`
- Testing guide: `unified-trading-codex/06-coding-standards/testing.md`

---

## 💡 Tips

1. **Start with critical paths**: Test main workflows first
2. **Use TDD for new code**: Write tests before implementation
3. **Refactor incrementally**: Don't rewrite everything at once
4. **Mock external dependencies**: Keep unit tests fast
5. **Follow test template**: Consistent structure helps LLMs

---

## ✏️ Notes

- Coverage is a means, not an end (quality matters more than %)
- Small functions are easier to test (and understand)
- Dependency injection enables mocking
- LLMs generate better tests with good examples
- Expected outcome: 50%+ coverage, fewer production bugs
- This is an ongoing process (not one-time task)
