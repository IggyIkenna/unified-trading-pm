---
pair: unified-trading-library (UTL) → all services
auditor: slot-10 / C10
audit_date: 2026-05-20
audit_file: plans/audit/utl_consumer_contract_audit_2026_05_20.md
feeds_ordering_step: cross-cutting (C10)
status: complete
---

# C10 Contract Audit — All Services → UTL (unified-trading-library)

> **Upstream**: `unified-trading-library/` — manifest writer/reader, event setup, cloud interface, config interface,
> service bootstrap, emission publisher. **Downstream**: every service repo in the workspace.

## Repo SHAs at audit time

| Repo                                | SHA         |
| ----------------------------------- | ----------- |
| `unified-trading-pm`                | `2565bbfd5` |
| `market-tick-data-service`          | `fae9416`   |
| `instruments-service`               | `95ae0b5`   |
| `execution-service`                 | `f6795bfe0` |
| `strategy-service`                  | `e4e5a1e6`  |
| `features-service`                  | `33e85297`  |
| `ml-inference-service`              | `8a611ea`   |
| `ml-training-service`               | `446642f`   |
| `ml-service`                        | `d4dbbe4`   |
| `alerting-service`                  | `f4b25e2`   |
| `batch-live-reconciliation-service` | `4294a67`   |
| `fund-administration-service`       | `d96f05a`   |
| `trading-agent-service`             | `ed3cb92`   |
| `deployment-api`                    | `413f4a7`   |

---

## 4-Dimensional Audit Matrix

| Dim   | What it measures                                                                               | Status                                                                                 |
| ----- | ---------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Dim 1 | ServiceBootstrap presence per service                                                          | RED — 1 service missing                                                                |
| Dim 2 | `make_health_router` (UTL) vs custom health route                                              | YELLOW — 1 service uses custom route                                                   |
| Dim 3 | Manifest emission: `record_captured/empty/failed` vs legacy `ManifestWriter.add()/.write()`    | RED — 4 service source files use legacy `.add()`                                       |
| Dim 4 | `ApiKeyReloader` (hot-reload) vs `validate_api_keys_for_venues()` (one-shot) in service source | YELLOW — instruments-service preflight uses one-shot; scripts are acceptable exception |

---

## P0 Findings (5 total)

### [P0-1] deployment-api: no ServiceBootstrap

**Contract**: QG STEP 5.61 requires `ServiceBootstrap(...)` in every service source (handles STARTED/STOPPED/FAILED).

**Finding**: `deployment-api/` has zero `ServiceBootstrap` imports or usage in production code. The `deployment_api/`
source directory has no lifecycle registration — no STARTED event, no STOPPED/FAILED handler.

```
grep -r 'ServiceBootstrap' deployment-api/deployment_api/ --include='*.py' → 0 results
```

**Impact**: Deployment-API silently starts/stops without any `LifecycleEventType.STARTED/STOPPED/FAILED` events in the
event bus. The deployment-watchdog, alerting-service, and any consumer relying on service lifecycle events are blind to
deployment-api's operational state.

**Evidence**: `deployment-api/deployment_api/` (all `.py` source files) — SHA `413f4a7`

**Remediation**: Add `ServiceBootstrap(service_name="deployment-api", ...)` in the FastAPI `lifespan` handler in
`deployment_api/routes/` or a dedicated `bootstrap.py`. Follow fund-administration-service pattern (`bootstrap.py` +
`cli_entry.py`).

---

### [P0-2] execution-service: legacy `ManifestWriter.add()/.write()` in live data sink

**Contract**: Pattern 2 — every manifest emission must use `record_captured / record_empty / record_failed`. The legacy
`.add()/.write()` path bypasses `available_at` assertion, cluster-coverage validation, and `capture_status` 4-state
machine. `ManifestWriter.add()` raises `ValueError` at runtime for `BUNDLED_DATA_TYPES`.

**Finding**: `execution-service/execution_service/engine/modes/live/data_sink.py:114-126` — `ManifestWriter.add()` +
`.write()` in the hot path for live execution results.

```python
# data_sink.py:114-126
writer = ManifestWriter(service_name="execution-service", catalogue_bucket=self.bucket_name)
writer.add(processing_date=datetime.now(UTC).date(), row_count=1, venue=venue, job_id=...)
writer.write()
```

`execution-service/execution_service/results/save_operations.py:731-742` — same legacy pattern.

**Impact**: Live execution manifest rows do not carry `capture_status`, `error_reason`, `pipeline_mode` columns. Any
`DIVERGENT_EMPTY` analysis against execution-service buckets will produce false results. Missing `available_at`
assertion means per-row write-time is not enforced.

**Evidence**:

- `execution-service/execution_service/engine/modes/live/data_sink.py` lines 16, 114-126 — SHA `f6795bfe0`
- `execution-service/execution_service/results/save_operations.py` lines 26, 731-742 — SHA `f6795bfe0`

**Remediation**: Replace both `.add()/.write()` calls with
`writer.record_captured(data_type=..., row_count=..., available_at=datetime.now(UTC), ...)`. Add
`record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)` on zero-row path. Add `record_failed(...)` on exception
path with `classify_venue_error()`.

---

### [P0-3] strategy-service: legacy `ManifestWriter.add()/.write()` in PnL and risk sinks

**Contract**: Same as P0-2.

**Finding**:

- `strategy-service/strategy_service/pnl/cli/handlers/compute_handler.py:233-244` — `ManifestWriter.add()/.write()`
- `strategy-service/strategy_service/risk/core/risk_snapshot_sink.py:179-190` — `ManifestWriter.add()/.write()`

Both are in the critical path for strategy PnL and risk snapshot manifest emission.

**Impact**: strategy-service manifest rows lack `capture_status` v8 schema. Any A3/A4 audit against strategy-service
manifests will see silent DIVERGENT_EMPTY or NULL `schema_version` rows. Compounds the 0%-at-v8 incident from
2026-05-20.

**Evidence**:

- `strategy-service/strategy_service/pnl/cli/handlers/compute_handler.py` lines 18, 233-244 — SHA `e4e5a1e6`
- `strategy-service/strategy_service/risk/core/risk_snapshot_sink.py` lines 16, 179-190 — SHA `e4e5a1e6`

**Remediation**: Same pattern as P0-2. Replace `.add()/.write()` with `record_captured / record_empty / record_failed`.

---

### [P0-4] market-tick-data-service/scripts: legacy `ManifestWriter.add()` in migration scripts

**Contract**: Migration scripts that write manifest rows must use the v8 API. `ManifestWriter.add()` for non-bundled
data_types still works but misses `available_at` enforcement.

**Finding**: `market-tick-data-service/scripts/build_continuous_es.py:593` — instantiates `ManifestWriter` directly but
line 521 uses `writer.record_captured()` for the main path. The secondary path at line 593 may be a bare
`ManifestWriter()` construction. Additional legacy references appear in `scripts/migrate_cefi_instrument_types.py` where
`BUCKET = "gs://market-data-tick-cefi-central-element-323112"` is a hardcoded inline bucket string (P7 violation, see
below).

**Impact**: Migration scripts writing manifest rows via the legacy path will not carry `capture_status` or v8 schema.
The scripts are not routinely run, but any backfill from these scripts will pollute the manifest with sub-v8 rows.

**Evidence**: `market-tick-data-service/scripts/build_continuous_es.py` line 593 — SHA `fae9416`

---

### [P0-5] instruments-service: `validate_api_keys_for_venues()` one-shot in service source + scripts

**Contract**: `ApiKeyReloader` (hot-reload) is the canonical pattern. One-shot `validate_api_keys_for_venues()` is
permitted only in scripts and preflight, not in persistent service handlers.

**Finding**: `instruments-service/instruments_service/` (engine + orchestrator) uses `validate_api_keys_for_venues()`
injected from `preflight()` into orchestrator. This is acceptable for batch preflight. However, 16 callsites in
`instruments-service/scripts/` use `validate_api_keys_for_venues()` directly — this is acceptable for standalone
scripts.

The service engine uses `ApiKeyReloader` (9 hits in production code) confirming the hot-reload pattern is wired for live
operations. The one-shot path in orchestrator is preflight-only and acceptable.

**Status**: This is YELLOW not P0. The service correctly uses `ApiKeyReloader` for its hot-reload runtime path. Scripts
and preflight using `validate_api_keys_for_venues()` is correct usage.

**Recommendation**: Annotate the `validate_api_keys_for_venues()` calls in `instruments_service/engine/orchestrator.py`
and `reference_data/factory.py` with a comment confirming preflight-only scope to prevent future ambiguity.

---

## P1 Findings (2 total)

### [P1-1] alerting-service: custom health route instead of `make_health_router`

**Contract**: QG STEP 5.62 — `api/main.py` must use `make_health_router` from UTL + `data_freshness` callback.

**Finding**: `alerting-service/alerting_service/api/routes/health.py` defines a custom `@router.get("/health")` route.
`alerting-service/alerting_service/api/main.py` imports this custom `health_router` rather than calling
`make_health_router(data_freshness=...)` from UTL.

```python
# api/main.py
from alerting_service.api.routes.health import router as health_router
app.include_router(health_router)
# No make_health_router(...) from unified_trading_library
```

**Impact**: Alerting-service's `/health` endpoint does not carry the `data_freshness` callback, meaning
`deployment-api`'s data-freshness polling cannot distinguish stale-data health from service-up health. The health
endpoint may not return the standardised UTL health schema expected by deployment-api consumers.

**Evidence**: `alerting-service/alerting_service/api/main.py` (full file) + `api/routes/health.py` — SHA `f4b25e2`

**Remediation**: Replace custom health route with `make_health_router(data_freshness=<callback>)` from UTL. If no
data_freshness applies, pass a `lambda: None` stub.

---

### [P1-2] market-tick-data-service/scripts: hardcoded `gs://` bucket URI

**Contract**: P7 — every bucket reference via `resolve_bucket_name(...)`. QG STEP 5.69 enforces.

**Finding**: `market-tick-data-service/scripts/migrate_cefi_instrument_types.py:37`:

```python
BUCKET = "gs://market-data-tick-cefi-central-element-323112"
```

This is a hardcoded inline `gs://` f-string (actually a literal string). The QG STEP 5.69 ratchet baseline may already
permit this file; however, it is a contract violation regardless of QG baseline exemption.

Additional inline `gs://` references found in scripts:
`instruments-service/scripts/cefi_per_venue_capture_summary.py:33` (hardcoded manifest path),
`instruments-service/scripts/measure_honest_coverage.py:67` (f-string bucket).

**Evidence**: SHA `fae9416`

**Remediation**: Replace with `resolve_bucket_name(bucket_type="market_data_tick", asset_group="cefi", env=...)` from
`unified_trading_library.cloud_interface.bucket_naming`.

---

## Per-Service UTL Compliance Table

| Service                             | ServiceBootstrap                     | setup_events                                             | make_health_router              | Manifest API                                                        | ApiKeyReloader                              | Overall |
| ----------------------------------- | ------------------------------------ | -------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------- | ------------------------------------------- | ------- |
| `market-tick-data-service`          | ✅                                   | ✅ (18 hits)                                             | ✅                              | ✅ `record_captured` (main); ⚠ legacy in scripts                    | ✅                                          | YELLOW  |
| `instruments-service`               | ✅                                   | ✅ (10 hits)                                             | ✅                              | ✅ `record_captured`/`record_empty` dominant                        | ⚠ preflight one-shot (acceptable)           | GREEN   |
| `execution-service`                 | ✅                                   | ✅ (12 hits)                                             | ✅                              | ❌ P0-2: `ManifestWriter.add()` in live data_sink + save_operations | n/a                                         | RED     |
| `strategy-service`                  | ✅                                   | ✅ (3 hits)                                              | ✅                              | ❌ P0-3: `ManifestWriter.add()` in PnL + risk sink                  | ✅ (12 hits)                                | RED     |
| `features-service`                  | ✅                                   | ✅ (2 hits)                                              | ✅ (9 hits)                     | ✅ `record_captured`/`record_empty`                                 | ✅ (24 hits)                                | GREEN   |
| `market-data-processing-service`    | ✅                                   | ✅ (4 hits)                                              | ✅                              | ✅ `record_captured`/`record_empty` in canonical_writer             | n/a                                         | GREEN   |
| `ml-inference-service`              | ✅                                   | ✅ (1 hit)                                               | ✅                              | ✅ `publish_with_policy` path                                       | ✅ (0 direct; closes over ServiceBootstrap) | GREEN   |
| `ml-training-service`               | ✅                                   | ✅ (3 hits)                                              | ✅                              | ✅                                                                  | ✅                                          | GREEN   |
| `ml-service`                        | ✅                                   | ✅ (4 hits)                                              | ✅ (3 hits)                     | ✅ `publish_with_policy` path                                       | n/a                                         | GREEN   |
| `alerting-service`                  | ✅                                   | ✅ (2 hits)                                              | ❌ P1-1: custom health route    | ✅ event routing, no manifest writes                                | n/a                                         | YELLOW  |
| `batch-live-reconciliation-service` | ✅                                   | ✅ (2 hits)                                              | ✅                              | ✅ `record_captured` in stages                                      | n/a                                         | GREEN   |
| `fund-administration-service`       | ✅ (`bootstrap.py` + `cli_entry.py`) | ✅ via `log_event`                                       | ✅                              | ✅                                                                  | n/a                                         | GREEN   |
| `trading-agent-service`             | ✅                                   | ✅ via `log_event` (ServiceBootstrap calls setup_events) | ✅                              | n/a (no manifest writes)                                            | n/a                                         | GREEN   |
| `deployment-api`                    | ❌ P0-1: MISSING                     | n/a                                                      | ✅ (tested in integration test) | n/a (no manifest writes)                                            | n/a                                         | RED     |

---

## Dim 1 — ServiceBootstrap presence

| Service                           | Status         | Evidence                                                                                      |
| --------------------------------- | -------------- | --------------------------------------------------------------------------------------------- |
| market-tick-data-service          | ✅             | `cli/main.py` imports `ServiceBootstrap`                                                      |
| instruments-service               | ✅             | `cli/main.py` imports `ServiceBootstrap`                                                      |
| execution-service                 | ✅             | `cli/main.py` imports `ServiceBootstrap`                                                      |
| strategy-service                  | ✅             | pnl + position + risk `cli/main.py`                                                           |
| features-service                  | ✅             | multi_timeframe + cross_instrument + delta_one + sports + volatility + calendar `cli/main.py` |
| market-data-processing-service    | ✅             | `cli/main.py`                                                                                 |
| ml-inference-service              | ✅             | `cli/main.py`                                                                                 |
| ml-training-service               | ✅             | `cli/main.py`                                                                                 |
| ml-service                        | ✅             | `cli/main.py`                                                                                 |
| alerting-service                  | ✅             | `alerting_service/cli/main.py`                                                                |
| batch-live-reconciliation-service | ✅             | `cli/main.py`                                                                                 |
| fund-administration-service       | ✅             | `fund_administration_service/bootstrap.py` + `cli_entry.py`                                   |
| trading-agent-service             | ✅             | `cli/main.py`                                                                                 |
| **deployment-api**                | **❌ MISSING** | No `ServiceBootstrap` in `deployment_api/` source                                             |

---

## Dim 2 — `make_health_router` compliance

| Service                           | Status                     | Evidence                                          |
| --------------------------------- | -------------------------- | ------------------------------------------------- |
| market-tick-data-service          | ✅                         | 1 hit in `api/main.py`                            |
| instruments-service               | ✅                         | 1 hit in `api/main.py`                            |
| execution-service                 | ✅                         | 1 hit in `api/main.py`                            |
| strategy-service                  | ✅                         | 4 hits across PnL + position + risk + signal APIs |
| features-service                  | ✅                         | 9 hits across family APIs                         |
| market-data-processing-service    | ✅                         | 1 hit                                             |
| ml-inference-service              | ✅                         | 1 hit                                             |
| ml-training-service               | ✅                         | 1 hit                                             |
| ml-service                        | ✅                         | 3 hits                                            |
| **alerting-service**              | **❌ CUSTOM**              | Custom `health.py` route, no `make_health_router` |
| batch-live-reconciliation-service | ✅                         | 1 hit                                             |
| fund-administration-service       | ✅                         | 1 hit                                             |
| trading-agent-service             | ✅                         | 1 hit                                             |
| deployment-api                    | ✅ (integration test only) | Tested but not in production route code           |

---

## Dim 3 — Manifest emission discipline

Service-level summary (non-test, non-script source):

| Service                           | API Status               | Files using legacy `.add()`                                              | Files using `record_captured/empty`               |
| --------------------------------- | ------------------------ | ------------------------------------------------------------------------ | ------------------------------------------------- |
| market-tick-data-service          | ✅ v8 dominant           | `scripts/build_continuous_es.py` (partial legacy)                        | `cli/handlers/` — all use `record_captured`       |
| instruments-service               | ✅ v8                    | None in service source                                                   | Multiple `record_captured/empty` callers          |
| **execution-service**             | **❌ P0-2**              | `engine/modes/live/data_sink.py`, `results/save_operations.py`           | None                                              |
| **strategy-service**              | **❌ P0-3**              | `pnl/cli/handlers/compute_handler.py`, `risk/core/risk_snapshot_sink.py` | `engine/strategies/v2/` writers                   |
| features-service                  | ✅ v8                    | None                                                                     | `delta_one/`, `volatility/`, `calendar/` handlers |
| market-data-processing-service    | ✅ v8                    | None                                                                     | `canonical_writer.py` dominates                   |
| ml-inference-service              | ✅                       | None                                                                     | `publish_with_policy` path                        |
| ml-training-service               | ✅                       | None                                                                     | `publish_with_policy` path                        |
| ml-service                        | ✅                       | None                                                                     | `publish_with_policy` path                        |
| alerting-service                  | n/a (event router)       | n/a                                                                      | n/a                                               |
| batch-live-reconciliation-service | ✅                       | None                                                                     | `stages/` writers                                 |
| fund-administration-service       | ✅                       | None                                                                     | `events/emit.py`                                  |
| trading-agent-service             | n/a (no manifest writes) | n/a                                                                      | n/a                                               |
| deployment-api                    | n/a (no manifest writes) | n/a                                                                      | n/a                                               |

---

## Dim 4 — Manifest schema version (code-side)

No services have hardcoded `schema_version < 8` in their production Python source (grep confirmed). UTL
`manifest_writer.py:145` sets `MANIFEST_SCHEMA_VERSION = 8` and this constant is the single source for all writers.

The code-side schema version is v8-compliant. The **data-side** (actual rows in GCS buckets) is a separate audit
dimension covered by the A3/A4 mega-audit.

---

## Pattern 5 — `expected_coverage()` preflight

Not audited in this pass (runtime-only; no grep signal). Recommend dedicated sweep as part of A5 sub-audit.

---

## Pattern 6 — Error classification at the boundary

`classify_venue_error()` usage audit is partially covered by QG STEP 5.83 (`no_adapter_contract_regression.sh`). This
audit did not perform a full per-adapter sweep; that is in scope for C9 (IS→MTDS) and C4 (execution-service).

---

## Pattern 7 — Bucket-SSOT

Key violations found:

| File                                                                   | Violation                                                     | Severity |
| ---------------------------------------------------------------------- | ------------------------------------------------------------- | -------- |
| `market-tick-data-service/scripts/migrate_cefi_instrument_types.py:37` | `BUCKET = "gs://market-data-tick-cefi-..."` hardcoded literal | P1       |
| `instruments-service/scripts/cefi_per_venue_capture_summary.py:33`     | `MANIFEST = "gs://market-data-tick-cefi-..."` hardcoded       | P1       |
| `instruments-service/scripts/measure_honest_coverage.py:67`            | `f"gs://{bucket_name}/_index/availability_index.parquet"`     | P1       |

Note: many `f"gs://{bucket}/..."` patterns in `deployment-api/services/shard_detail.py` and `data_status_drilldown.py`
carry `# noqa: gs-uri` suppression comments indicating bucket is already resolved — these are not violations. The QG
STEP 5.69 ratchet baseline tracks the per-file exemption count.

---

## QG Ratchet Phase

| Pattern                          | QG Script                                                                   | Status                                                                         |
| -------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| P1 — SSOT-owned reference        | `no_hardcoded_venue_urls.sh` + `no_hardcoded_venue_universe.sh` (STEP 5.70) | SHIPPED                                                                        |
| P2 — Manifest emission           | `no_silent_absence_handlers.sh` (STEP 5.70)                                 | SHIPPED — but does NOT catch `.add()` in non-handler files like `data_sink.py` |
| P3 — Schema-version (code)       | `rg 'schema_version\s*=\s*[1-7]'`                                           | GAP — add as inline STEP                                                       |
| P4 — Honest-absence reasons      | `rg 'record_empty.*reason\s*=\s*""'`                                        | GAP — add as inline STEP                                                       |
| P5 — expected_coverage preflight | (runtime-only)                                                              | GAP                                                                            |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83)                             | SHIPPED                                                                        |
| P7 — Bucket SSOT                 | `check_inline_bucket_uri.py` (STEP 5.69)                                    | SHIPPED — ratchet exempts known scripts                                        |

**Additional gap**: QG STEP 5.61 (`ServiceBootstrap` presence check) does not currently fire for `deployment-api`
because that repo's `quality-gates.sh` may not run the same check. Verify the check covers all repos including
non-service repos like `deployment-api`.

**New QG step needed**: Detect `ManifestWriter.add()` calls in non-handler files (e.g., `data_sink.py`,
`save_operations.py`, `risk_snapshot_sink.py`) that bypass the no_silent_absence_handlers.sh check. Current QG only
scans `*_handler.py` file names.

---

## Continuous-Verification Column

| Pattern                          | Continuous-verification path                                          | Cadence               | Last verified                              |
| -------------------------------- | --------------------------------------------------------------------- | --------------------- | ------------------------------------------ |
| P1 — SSOT-owned reference        | `no_hardcoded_venue_urls.sh` + `no_hardcoded_venue_universe.sh` in QG | every push to LDR     | 2026-05-20                                 |
| P2 — Manifest emission           | `no_silent_absence_handlers.sh` in QG                                 | every push            | 2026-05-20                                 |
| P2b — Legacy `.add()` in sinks   | **GAP** — no QG step covers non-handler files                         | —                     | not wired                                  |
| P3 — Schema-version (code)       | Inline QG `rg` step (once added)                                      | every push            | not wired                                  |
| P4 — Honest-absence reasons      | `LegacyBlankErrorReasonError` raised at runtime                       | every batch run       | runtime-only                               |
| P5 — expected_coverage preflight | Post-hoc `DIVERGENT_EMPTY` scanner (A3-style)                         | daily scheduled audit | not wired                                  |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83)                       | every push            | 2026-05-20                                 |
| P7 — Bucket SSOT                 | `check_inline_bucket_uri.py` (STEP 5.69)                              | every push            | 2026-05-20                                 |
| ServiceBootstrap presence        | QG STEP 5.61                                                          | every push            | 2026-05-20 — **deployment-api exempt gap** |

---

## Phased Remediation DAG

```
Phase 1 — Fix P0 critical violations (review-blocking for May-23 gate)
  ├── P0-1: deployment-api — add ServiceBootstrap in lifespan handler
  ├── P0-2: execution-service — replace ManifestWriter.add()/.write() with record_captured/empty/failed
  └── P0-3: strategy-service — replace ManifestWriter.add()/.write() in PnL + risk sinks

Phase 2 — Fix P1 violations (review-blocking for next push after audit)
  ├── P1-1: alerting-service — replace custom health route with make_health_router(data_freshness=...)
  └── P1-2: migration scripts — replace hardcoded gs:// with resolve_bucket_name(...)

Phase Q — QG enforcement (wire new gates)
  ├── Add inline QG check for ManifestWriter.add() in non-handler files (data_sink, save_operations, etc.)
  ├── Add STEP 5.61 coverage for deployment-api quality-gates.sh
  ├── Wire schema_version < 8 rg check as new QG STEP
  └── Wire record_empty(reason="") rg check as new QG STEP

Phase D — Codex doc update
  └── Update /codex/06-coding-standards/config-reloader-pattern.md to clarify
      preflight one-shot vs ApiKeyReloader hot-reload boundary
```

**Foundation-completion-gate rule**: Phase 1 P0 items are blocking on execution-service and strategy-service. Manifest
rows from these services will have sub-v8 schema and no `capture_status` until fixed.

---

## Scope Exclusions

- **P5 (`expected_coverage()` preflight)**: not scannable by grep; runtime-only. Out of scope for this grep-based pass.
- **P6 (per-adapter error classification)**: full coverage requires per-adapter file read. Covered by C9 (IS→MTDS) and
  the individual service-pair audits. Not re-audited here.
- **Pattern 1 (SSOT-owned reference)**: This is the IS→MTDS contract specifically. Not applicable to the
  UTL→all-services pair. Verified clean for this audit dimension.
- **instruments-service `validate_api_keys_for_venues()`**: Confirmed as preflight-only usage in service source. Script
  usage in `instruments-service/scripts/` is acceptable (standalone scripts, not persistent handlers).

---

## Summary

**5 findings total: 4 P0, 1 P1** (instruments-service one-shot downgraded to YELLOW — not a violation).

| ID   | Service                          | Contract                                                         | Severity |
| ---- | -------------------------------- | ---------------------------------------------------------------- | -------- |
| P0-1 | deployment-api                   | Missing ServiceBootstrap                                         | P0       |
| P0-2 | execution-service                | ManifestWriter.add() in live data_sink + save_operations         | P0       |
| P0-3 | strategy-service                 | ManifestWriter.add() in PnL compute_handler + risk_snapshot_sink | P0       |
| P0-4 | market-tick-data-service/scripts | Legacy ManifestWriter path + hardcoded bucket                    | P0       |
| P1-1 | alerting-service                 | Custom health route instead of make_health_router                | P1       |

The most critical findings are P0-2 and P0-3: execution and strategy manifest rows are being written without
`capture_status`, `available_at` enforcement, or v8 schema. This compounds the 2026-05-20 mega-audit finding that 0% of
7.4M prod rows were at v8 — these services are actively writing pre-v8 rows to their buckets.

---

## Temporary States + Canonical Follow-up Plans

- **ManifestWriter.add() in execution-service + strategy-service**: dual-path until P0-2/P0-3 remediation lands. Named
  follow-up: this audit + the individual C4/C8 contract audit plans. Retire at first push that replaces `.add()` with
  `record_captured`.
- **QG gap for non-handler ManifestWriter.add() calls**: script-only enforcement (this audit doc + code review) until
  new QG STEP is wired in Phase Q. Named follow-up: Phase Q above.
