---
scope: [engineer]
---

# Schema validation (write-side)

## Purpose

Every adapter / calculator / writer that writes parquet to GCS must validate **per-row** against the canonical schema
before calling `record_captured`. Schema drift detected at read-time is too late — by then a downstream service has
already consumed garbage. This doc names the per-row validation pattern.

## SSOT — UAC schema declarations

The canonical schema for each `data_type` lives in UAC under `unified_api_contracts/canonical/domain/<asset_group>/`.
Adapters import the schema and validate before writing:

```python
from unified_api_contracts.canonical.domain.cefi.ohlcv_1m import OHLCV1mRow

def _write_row(row: dict, manifest: ManifestWriter, row_key: ShardKey) -> None:
    try:
        validated = OHLCV1mRow.model_validate(row)        # Pydantic per-row
    except ValidationError as exc:
        manifest.record_failed(
            row_key=row_key,
            error=SchemaValidationFailedError(
                data_type=row_key.data_type,
                row_index=...,
                pydantic_errors=exc.errors(),
            ),
            attempted_at=now(),
        )
        return  # Do not append the row to the parquet writer.

    parquet_writer.append(validated.model_dump())
```

## Why per-row, not per-batch

Per-batch validation (validate the dataframe at the end) catches a schema drift bug, but loses the bad row's identity —
you get one error for "100 rows failed" with no clue which 100. Per-row validation:

- Records `record_failed` with the exact row's `row_key` and the per-row error reason.
- Lets the rest of the batch ship cleanly (the bad row doesn't poison the parquet).
- Surfaces partial failures in the manifest as `attempted_failed` with `error_reason=SCHEMA_VALIDATION_FAILED`.

## SCHEMA_VALIDATION_FAILED reason

`SCHEMA_VALIDATION_FAILED` is a typed `error_reason` in the manifest taxonomy (closed set; canonical list in UAC
`EMPTY_CONFIRMED_REASONS` + `ATTEMPTED_FAILED_REASONS`). The reason carries the Pydantic error path so operators can
debug from manifest reads alone.

## What MUST validate

Every write-time adapter:

- MTDS adapters (per-instrument tick fetchers, per-bar OHLCV builders).
- MDPS calculators (per-bar OHLC reshape, per-bar features).
- features-service calculators (every BaseCalculator subclass).
- instruments-service catalog refresh adapters.
- ml-training-service feature loaders (validate inputs before training; bad inputs corrupt the model).

## What does NOT validate at write-time

- Pure passthrough services that read a parquet and re-write a derived parquet — they trust the read-time schema (which
  was already validated at write).
- Backfill scripts that operate on already-validated parquets.

## Cross-references

- Honest absence (read-side):
  [`../02-data/honest-absence-downstream-handling.md`](../02-data/honest-absence-downstream-handling.md) — how
  downstream consumers handle `attempted_failed` rows.
- Manifest reason taxonomy:
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) §
  "Reason taxonomy"
- Error handling pattern (general): [`error-handling.md`](error-handling.md)
- BaseCalculator (where the validation hook lives):
  [`feature-service-pattern.md`](feature-service-pattern.md)
- Cluster validation (additional pillar at `record_captured`):
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) §
  "Cluster validation MANDATORY at record_captured"
