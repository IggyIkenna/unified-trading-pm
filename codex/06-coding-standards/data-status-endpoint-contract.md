# Data-Status Endpoint Contract

## Rule

Every service's `/api/data-status` HTTP endpoint MUST call `compute_coverage_for_bucket()` (UTL) or
`compute_honest_coverage()` (UAC). It MUST NOT re-implement the manifest read or the coverage formula inline.

## Rationale

Before this contract, each service implemented its own manifest-read + coverage-percentage logic, producing drift
between the CLI `--operation=status` output, the deployment-api panel, and the UI display. The canonical formula is
owned by UAC (`compute_honest_coverage`) and wrapped by UTL (`compute_coverage_for_bucket`). Any service-local
re-implementation is silently stale the moment the canonical formula is updated.

## Required pattern

```python
from unified_trading_library import compute_coverage_for_bucket  # UTL wrapper

# Inside the GET /api/data-status handler:
counts, ratio = compute_coverage_for_bucket(bucket, asset_group=asset_group, data_type=dt)
return {
    "counts": counts._asdict(),
    "coverage": round(ratio, 6),
}
```

Alternatively, higher-level consumers may call `compute_honest_coverage(counts)` directly after assembling
`CaptureStatusCounts` from their own manifest read, provided the manifest read itself uses
`read_capture_status_counts()` from UTL.

## Banned patterns

- Computing `captured / (captured + empty + failed)` inline — missing the `expected_unattempted_known_empty` numerator
  credit and the `expected_unattempted_pending_fetch` denominator term.
- Reading the manifest parquet directly and computing a coverage ratio without going through UTL helpers.
- Returning `{"coverage_pct": ...}` or `{"completion_pct": ...}` as the primary coverage field — use
  `{"coverage": float}` for the canonical 5-field ratio.

## Enforcement

QG STEP 5.90 (`check_data_status_endpoint_canonical.sh`) scans every `*.py` file in `SOURCE_DIR` that defines a
`GET /data-status` route. If any such file does not import `compute_coverage_for_bucket` or `compute_honest_coverage`,
the QG step fails.

SSOT: `honest_coverage_formula_consolidation_2026_05_19.md` Phase 1 P1.
