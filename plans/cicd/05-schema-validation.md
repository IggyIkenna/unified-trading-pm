# 05: Schema Validation (GCS + BigQuery)

**Status**: ⬜ Not Started **Priority**: P2 (Catch data drift early) **Estimated Time**: 2-3 hours **Expected Benefit**:
10-20 min/day saved, prevent production data issues

---

## 📖 Overview

Validate that data in Google Cloud Storage (GCS) and BigQuery matches your defined schemas. Catch schema drift before it
causes production issues.

### Current State

- Schemas defined in `schemas/output_schemas.py` files
- No automated validation of actual data
- Schema mismatches discovered at runtime
- Manual inspection required

### Target State

- Automated schema validation in quality gates
- Fast validation (sample-based, not full scan)
- Clear error messages when schema drift detected
- Integration with CI/CD pipeline

---

## 🔗 Dependencies

- **Requires**: Data in GCS/BigQuery to validate against
- **Blocks**: None (informational checks)

---

## 🚧 Blockers

- [ ] **CRITICAL**: Need actual data in GCS/BigQuery
  - If no data exists, validation will fail
  - Must run data pipeline first to populate GCS/BQ
  - Or use sample data for testing

- [ ] Need GCP credentials configured locally
- [ ] Need to identify which buckets/datasets to validate

---

## 🔍 Current State Analysis

### Step 1: Check for Existing Data

```bash
# Check GCS buckets
gsutil ls gs://central-element-323112-unified-trading-data/

# Check BigQuery datasets
bq ls --project_id=central-element-323112

# Check specific tables
bq show --project_id=central-element-323112 unified_trading_data.instruments
bq show --project_id=central-element-323112 unified_trading_data.market_data
```

**If no data exists**: Must populate first before validation can work.

### Step 2: Inventory Schema Definitions

```bash
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos

# Find all schema files
find . -name "output_schemas.py" -o -name "schemas.py" | grep -v ".venv" | grep -v "node_modules"

# Example schemas to validate:
# - instruments-service/schemas/output_schemas.py
# - market-tick-data-handler/schemas/output_schemas.py
# - market-data-processing-service/schemas/output_schemas.py
# - features-*/schemas/output_schemas.py
```

---

## 🛠️ Implementation

### Part 1: Create Schema Validator Module

```python
# unified-trading-services/validation/schema_validator.py
"""
Schema validation for GCS and BigQuery data.

Usage:
    from unified_trading_services.validation import validate_gcs_schema, validate_bq_schema

    # Validate GCS file
    validate_gcs_schema(
        bucket="central-element-323112-unified-trading-data",
        path="instruments/cefi/2024-01-01.parquet",
        expected_schema=INSTRUMENTS_SCHEMA,
        sample_size=100
    )

    # Validate BigQuery table
    validate_bq_schema(
        project_id="central-element-323112",
        dataset="unified_trading_data",
        table="instruments",
        expected_schema=INSTRUMENTS_BQ_SCHEMA
    )
"""
from typing import Protocol
import pandas as pd
from google.cloud import storage, bigquery
from pydantic import BaseModel

class SchemaField(BaseModel):
    """Schema field definition."""
    name: str
    dtype: str  # pandas dtype or BigQuery type
    nullable: bool = True
    description: str = ""

class SchemaDefinition(BaseModel):
    """Complete schema definition."""
    name: str
    fields: list[SchemaField]

    def to_pandas_dtypes(self) -> dict[str, str]:
        """Convert to pandas dtype dict."""
        return {field.name: field.dtype for field in self.fields}

    def to_bq_schema(self) -> list[bigquery.SchemaField]:
        """Convert to BigQuery schema."""
        return [
            bigquery.SchemaField(
                name=field.name,
                field_type=field.dtype,
                mode="NULLABLE" if field.nullable else "REQUIRED",
                description=field.description
            )
            for field in self.fields
        ]

def validate_gcs_schema(
    bucket: str,
    path: str,
    expected_schema: SchemaDefinition,
    sample_size: int = 100,
    project_id: str | None = None
) -> tuple[bool, list[str]]:
    """
    Validate GCS file schema against expected schema.

    Args:
        bucket: GCS bucket name
        path: Path to file in bucket
        expected_schema: Expected schema definition
        sample_size: Number of rows to sample (for speed)
        project_id: GCP project ID (optional)

    Returns:
        (is_valid, errors) tuple
    """
    errors = []

    try:
        # Read sample from GCS
        gcs_path = f"gs://{bucket}/{path}"

        if path.endswith('.parquet'):
            df = pd.read_parquet(gcs_path, nrows=sample_size)
        elif path.endswith('.csv'):
            df = pd.read_csv(gcs_path, nrows=sample_size)
        else:
            errors.append(f"Unsupported file format: {path}")
            return False, errors

        # Check columns exist
        expected_cols = set(field.name for field in expected_schema.fields)
        actual_cols = set(df.columns)

        missing = expected_cols - actual_cols
        if missing:
            errors.append(f"Missing columns: {missing}")

        extra = actual_cols - expected_cols
        if extra:
            errors.append(f"Unexpected columns: {extra}")

        # Check dtypes
        expected_dtypes = expected_schema.to_pandas_dtypes()
        for col, expected_dtype in expected_dtypes.items():
            if col not in df.columns:
                continue

            actual_dtype = str(df[col].dtype)
            if actual_dtype != expected_dtype:
                errors.append(
                    f"Column '{col}': expected {expected_dtype}, got {actual_dtype}"
                )

        # Check nullability
        for field in expected_schema.fields:
            if not field.nullable and field.name in df.columns:
                null_count = df[field.name].isnull().sum()
                if null_count > 0:
                    errors.append(
                        f"Column '{field.name}': found {null_count} nulls (not nullable)"
                    )

        return len(errors) == 0, errors

    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, errors

def validate_bq_schema(
    project_id: str,
    dataset: str,
    table: str,
    expected_schema: SchemaDefinition
) -> tuple[bool, list[str]]:
    """
    Validate BigQuery table schema against expected schema.

    Args:
        project_id: GCP project ID
        dataset: BigQuery dataset name
        table: BigQuery table name
        expected_schema: Expected schema definition

    Returns:
        (is_valid, errors) tuple
    """
    errors = []

    try:
        client = bigquery.Client(project=project_id)
        table_ref = client.get_table(f"{project_id}.{dataset}.{table}")

        # Get actual schema
        actual_fields = {field.name: field for field in table_ref.schema}
        expected_fields = {field.name: field for field in expected_schema.to_bq_schema()}

        # Check fields exist
        missing = set(expected_fields.keys()) - set(actual_fields.keys())
        if missing:
            errors.append(f"Missing fields: {missing}")

        extra = set(actual_fields.keys()) - set(expected_fields.keys())
        if extra:
            errors.append(f"Unexpected fields: {extra}")

        # Check field types
        for name, expected_field in expected_fields.items():
            if name not in actual_fields:
                continue

            actual_field = actual_fields[name]

            if actual_field.field_type != expected_field.field_type:
                errors.append(
                    f"Field '{name}': expected {expected_field.field_type}, "
                    f"got {actual_field.field_type}"
                )

            if actual_field.mode != expected_field.mode:
                errors.append(
                    f"Field '{name}': expected {expected_field.mode}, "
                    f"got {actual_field.mode}"
                )

        return len(errors) == 0, errors

    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, errors
```

### Part 2: Define Schemas for Validation

```python
# instruments-service/schemas/validation_schemas.py
"""
Schema definitions for validation.

These are used by the schema validator to check actual data.
"""
from unified_trading_services.validation.schema_validator import SchemaDefinition, SchemaField

INSTRUMENTS_SCHEMA = SchemaDefinition(
    name="instruments",
    fields=[
        SchemaField(name="canonical_key", dtype="object", nullable=False),
        SchemaField(name="venue", dtype="object", nullable=False),
        SchemaField(name="symbol", dtype="object", nullable=False),
        SchemaField(name="base_asset", dtype="object", nullable=True),
        SchemaField(name="quote_asset", dtype="object", nullable=True),
        SchemaField(name="instrument_type", dtype="object", nullable=False),
        SchemaField(name="market_category", dtype="object", nullable=False),
        SchemaField(name="date", dtype="object", nullable=False),
        SchemaField(name="timestamp", dtype="datetime64[ns]", nullable=False),
    ]
)

INSTRUMENTS_BQ_SCHEMA = SchemaDefinition(
    name="instruments",
    fields=[
        SchemaField(name="canonical_key", dtype="STRING", nullable=False),
        SchemaField(name="venue", dtype="STRING", nullable=False),
        SchemaField(name="symbol", dtype="STRING", nullable=False),
        SchemaField(name="base_asset", dtype="STRING", nullable=True),
        SchemaField(name="quote_asset", dtype="STRING", nullable=True),
        SchemaField(name="instrument_type", dtype="STRING", nullable=False),
        SchemaField(name="market_category", dtype="STRING", nullable=False),
        SchemaField(name="date", dtype="DATE", nullable=False),
        SchemaField(name="timestamp", dtype="TIMESTAMP", nullable=False),
    ]
)
```

### Part 3: Add Validation to Quality Gates

```bash
# instruments-service/scripts/quality-gates.sh

# Add schema validation step (optional, skip in --quick mode)
if [ "$QUICK_MODE" != "true" ]; then
    echo "Step 6: Schema Validation..."
    python -c "
from schemas.validation_schemas import INSTRUMENTS_SCHEMA
from unified_trading_services.validation.schema_validator import validate_gcs_schema

# Validate latest instruments file
is_valid, errors = validate_gcs_schema(
    bucket='central-element-323112-unified-trading-data',
    path='instruments/cefi/2024-01-01.parquet',
    expected_schema=INSTRUMENTS_SCHEMA,
    sample_size=100
)

if not is_valid:
    print('❌ Schema validation failed:')
    for error in errors:
        print(f'  - {error}')
    exit(1)
else:
    print('✅ Schema validation passed')
"
fi
```

### Part 4: Create Standalone Validation Script

```python
# deployment-service/scripts/validate-all-schemas.py
"""
Validate all schemas across all services.

Usage:
    python scripts/validate-all-schemas.py
    python scripts/validate-all-schemas.py --service instruments-service
    python scripts/validate-all-schemas.py --quick  # Skip slow validations
"""
import argparse
from pathlib import Path
import sys

# Import schemas from each service
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from instruments_service.schemas.validation_schemas import INSTRUMENTS_SCHEMA
from market_tick_data_handler.schemas.validation_schemas import MARKET_DATA_SCHEMA
# Add more as needed

from unified_trading_services.validation.schema_validator import (
    validate_gcs_schema,
    validate_bq_schema
)

def validate_instruments():
    """Validate instruments data."""
    print("Validating instruments...")

    # GCS validation
    is_valid, errors = validate_gcs_schema(
        bucket="central-element-323112-unified-trading-data",
        path="instruments/cefi/2024-01-01.parquet",
        expected_schema=INSTRUMENTS_SCHEMA,
        sample_size=100
    )

    if not is_valid:
        print("❌ GCS validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✅ GCS validation passed")

    # BigQuery validation
    is_valid, errors = validate_bq_schema(
        project_id="central-element-323112",
        dataset="unified_trading_data",
        table="instruments",
        expected_schema=INSTRUMENTS_SCHEMA
    )

    if not is_valid:
        print("❌ BigQuery validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✅ BigQuery validation passed")
    return True

def validate_market_data():
    """Validate market data."""
    print("Validating market data...")
    # Similar pattern
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--service", help="Validate specific service only")
    parser.add_argument("--quick", action="store_true", help="Skip slow validations")
    args = parser.parse_args()

    all_passed = True

    if args.service is None or args.service == "instruments-service":
        all_passed &= validate_instruments()

    if args.service is None or args.service == "market-tick-data-handler":
        all_passed &= validate_market_data()

    # Add more services

    if all_passed:
        print("\n✅ All schema validations passed!")
        sys.exit(0)
    else:
        print("\n❌ Some schema validations failed")
        sys.exit(1)
```

---

## ✅ Verification

### Test 1: Validate Sample Data

```python
# Create sample data for testing
import pandas as pd

sample_data = pd.DataFrame({
    "canonical_key": ["BINANCE_BTC_USDT_SPOT"],
    "venue": ["BINANCE"],
    "symbol": ["BTC/USDT"],
    "base_asset": ["BTC"],
    "quote_asset": ["USDT"],
    "instrument_type": ["SPOT"],
    "market_category": ["CEFI"],
    "date": ["2024-01-01"],
    "timestamp": [pd.Timestamp.now()]
})

# Save to GCS
sample_data.to_parquet("gs://central-element-323112-unified-trading-data/test/sample.parquet")

# Validate
from unified_trading_services.validation.schema_validator import validate_gcs_schema
from instruments_service.schemas.validation_schemas import INSTRUMENTS_SCHEMA

is_valid, errors = validate_gcs_schema(
    bucket="central-element-323112-unified-trading-data",
    path="test/sample.parquet",
    expected_schema=INSTRUMENTS_SCHEMA
)

print(f"Valid: {is_valid}")
if not is_valid:
    for error in errors:
        print(f"  - {error}")
```

### Test 2: Detect Schema Drift

```python
# Intentionally break schema
bad_data = pd.DataFrame({
    "canonical_key": ["KEY"],
    "venue": ["BINANCE"],
    # Missing required columns
})

bad_data.to_parquet("gs://central-element-323112-unified-trading-data/test/bad.parquet")

# Validate (should fail)
is_valid, errors = validate_gcs_schema(
    bucket="central-element-323112-unified-trading-data",
    path="test/bad.parquet",
    expected_schema=INSTRUMENTS_SCHEMA
)

assert not is_valid
assert len(errors) > 0
print("✅ Schema drift detected correctly")
```

---

## 📊 Success Metrics

- [ ] Schema validator module created in unified-trading-services
- [ ] All services have validation schemas defined
- [ ] Validation script runs successfully
- [ ] Can detect missing columns
- [ ] Can detect wrong dtypes
- [ ] Can detect nullability violations
- [ ] Validation integrated into quality gates (optional step)
- [ ] Zero schema-related production issues

---

## 🔄 Rollback Plan

If validation causes issues:

1. Remove validation step from quality gates
2. Keep validator as standalone tool
3. Run manually before deployments
4. Fix schemas incrementally

---

## 📚 Related Documentation

- ChatGPT conversation: Lines 126-141 (schema validation discussion)
- Schema governance: `unified-trading-/codex/02-data/schema-governance.md`
- GCS validation: Google Cloud docs

---

## 💡 Tips

1. **Start with sample validation**: 100 rows is enough to catch most issues
2. **Run in CI, not blocking**: Make validation informational first
3. **Update schemas when data changes**: Keep schemas in sync
4. **Validate before major deployments**: Catch drift early
5. **Use in development**: Validate after running data pipelines locally

---

## ✏️ Notes

- **BLOCKER**: Requires actual data in GCS/BigQuery
- If no data exists, must run data pipeline first
- Sample-based validation is fast (<5 seconds)
- Full validation can be slow (skip in --quick mode)
- Expected to save 10-20 min/day catching schema issues early
