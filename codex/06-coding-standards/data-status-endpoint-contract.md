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

## Exemption — non-coverage `/data-status` endpoints

The contract governs endpoints that report **manifest coverage** (a `captured / (captured + empty + failed + …)`
ratio over a bucket). Some endpoints live under the `/api/data-status/*` namespace but return a different kind of
payload — access **rules**, credential/key **status**, or static metadata — with no bucket and no manifest to read.
The coverage helper does not apply to them, and calling it would fabricate a meaningless ratio (a banned pattern
above).

Such an endpoint declares the inline marker `# QG-allow: data-status-no-coverage` with a one-line reason on (or
directly above) its route decorator. STEP 5.90 then skips that file. Example:

```python
# QG-allow: data-status-no-coverage — returns Tardis free-tier access RULES + key status, not coverage.
@router.get("/api/data-status/venue-tardis-windows", response_model=VenueTardisWindowsResponse)
async def get_venue_tardis_windows() -> VenueTardisWindowsResponse: ...
```

The marker is the only sanctioned way to exempt a `/data-status` route — never drop the route from the namespace or
inline-fake a coverage field to dodge the gate. Reach for it ONLY when the endpoint genuinely returns no coverage; a
real coverage endpoint must use the canonical helper.

## Enforcement

QG STEP 5.90 (`check_data_status_endpoint_canonical.sh`) scans every `*.py` file in `SOURCE_DIR` that defines a
`GET /data-status` route. If any such file does not import `compute_coverage_for_bucket` or `compute_honest_coverage`
(and does not carry the `# QG-allow: data-status-no-coverage` exemption marker), the QG step fails.

SSOT: `honest_coverage_formula_consolidation_2026_05_19.md` Phase 1 P1.
