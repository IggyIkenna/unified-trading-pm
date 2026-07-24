---
doc_type: audit-result
title: Dependency Fail-Propagation Audit — 2026-05-20
summary:
  Read-only dependency fail-propagation audit (MTDS/features/strategy/execution/ml) — overall pipeline RED; two P0
  wiring gaps (execution-service assert_market_data_fresh + strategy-service assert_feature_fresh defined but zero
  engine call-sites) let live orders route on stale/failed upstream data; StaleUpstreamError not defined anywhere.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
  ]
scope: [engineer, admin]
tags: [audit, data-correctness, execution, strategy, mtds, features, live-trading, data-pipeline]
related: [/plans/audit/results/archive/dependency_propagation_2026_05_20_summary.md]
created: 2026-05-20
audited_scope:
  Read-only source inspection (excl .venv/tests) of MTDS, features-service, strategy-service, execution-service,
  ml-service dependency-check paths (batch pre-flight + live staleness gate), plus UAC/UTL
  DependencyError/DataStalenessError definitions
date: 2026-05-20
auditor: Slot 3 sub-agent
parent_epic: infrastructure_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# Dependency Fail-Propagation Audit — 2026-05-20

**Audit type**: Read-only code inspection (Phase A5 of mega-audit) **Auditor**: Slot 3 sub-agent **Scope**:
market-tick-data-service, features-service, strategy-service, execution-service, ml-service **Source files scanned**:
service source dirs only (excluded `.venv*`, `tests/`, `__pycache__`)

---

## Audit scope

### What was scanned exhaustively

- All `*.py` files under `{service}/` (source), excluding `.venv*`, `__pycache__`, and `tests/`
- UAC (`unified-api-contracts/`) for error class definitions
- UTL (`unified-trading-library/`) for `DependencyError`, `BaseDependencyChecker`, `emit_preflight_skip`

### What was skipped

- Tests were excluded from pattern scans (included only for call-site discovery where source came up empty)
- `execution-service/execution_service/validation/freshness_gate.py` was read in full to confirm behavior
- `market-data-processing-service` was not audited (not in scope list; MTDS is the upstream consumer of IS)

### Key files read in full

- `UTL/unified_trading_library/core/dependency_checker.py` — `BaseDependencyChecker` + `DependencyError`
- `UAC/unified_api_contracts/internal/reference/data_freshness.py` — `DataStalenessError` definition
- `market-tick-data-service/engine/orchestrator.py` — batch preflight (lines 1975–2086)
- `features-service/delta_one/cli/handlers/batch_handler.py` — batch DependencyError flow
- `features-service/delta_one/app/core/dependency_checker.py` — upstream dependency check method
- `features-service/common/manifest_window_guard.py` — manifest `capture_status` reader
- `strategy-service/manifest_allocation_guard.py` — manifest `capture_status` reader (full)
- `strategy-service/validation/freshness_gate.py` — `DataStalenessError` wiring
- `execution-service/engine/preflight.py` — pre-session checks (full)
- `execution-service/validation/freshness_gate.py` — `assert_market_data_fresh` definition
- `ml-service/inference/cli/handlers/batch_handler.py` — ml batch DependencyError flow
- `ml-service/inference/app/core/dependency_checker.py` — ml upstream deps

---

## Per-service × mode matrix

| Service               | Upstream                 | Batch: pre-flight check?                                                                                           | Batch: uses DependencyError?                                                                            | Live: StaleUpstreamError?                                                                                           | Verdict |
| --------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------- |
| **MTDS**              | instruments-service (IS) | ⚠ GCS blob check only (not manifest capture_status)                                                                | ❌ Not raised on IS fail; falls back to UAC MVP seed                                                    | ❌ No `StaleUpstreamError`; reconnect stamped as `STALE` in manifest only                                           | YELLOW  |
| **features-service**  | MTDS                     | ✅ `BaseDependencyChecker.check_dependencies()` + `manifest_window_guard` (capture_status aware)                   | ✅ `DependencyError` raised when `fail_on_missing=True` (default)                                       | ❌ No `StaleUpstreamError`; live handler passes to PubSub subscriber without staleness gate                         | YELLOW  |
| **strategy-service**  | features-service         | ✅ `manifest_allocation_guard.check_allocation_manifest()` reads capture_status; skips on `attempted_failed`       | ⚠ Skips + alerts but does NOT raise `DependencyError`; returns `should_skip_live=True` (caller decides) | ⚠ `DataStalenessError` defined + imported but **no call sites found in engine code** for live mode                  | YELLOW  |
| **execution-service** | strategy-service         | ❌ No upstream manifest check before trade execution; preflight only checks secrets, API keys, risk-service health | ❌ `DependencyError` not used; no strategy manifest dependency check                                    | ⚠ `assert_market_data_fresh()` defined and exported but **no engine call sites found**; only exists in tests        | RED     |
| **ml-service**        | features-service         | ✅ `BaseDependencyChecker.check_dependencies()` + `DependencyError` raised on missing required deps                | ✅ `DependencyError` raised when `fail_on_missing=True`                                                 | ❌ No `StaleUpstreamError`; live inference stale window handled via `STRICT_FAIL` suppression (not raised as error) | YELLOW  |

---

## Detailed findings per service

### MTDS (market-tick-data-service) — YELLOW

**Batch mode — pre-flight check**:

The batch orchestrator (`engine/orchestrator.py` lines 1975–2045) reads the MTDS _own_ manifest to skip already-captured
shards (via `read_availability_index`). The skip-states are `CAPTURED` + `EMPTY_CONFIRMED` only; `ATTEMPTED_FAILED` rows
are explicitly retried (confirmed at line 1992 and comments at line 2003).

However, the **upstream IS (instruments-service) check** (`_check_instruments_available`, line 234) reads a raw GCS
parquet file and returns `True/False` on file existence + row count. It does NOT read the IS manifest `capture_status`.
If IS wrote a parquet with `attempted_failed` in the IS manifest (because IS partially succeeded), MTDS sees the parquet
as "available" and proceeds — no `DependencyError` is raised.

**Critical gap**: If IS manifest shows `attempted_failed` but a partial parquet exists, MTDS proceeds with degraded
instrument coverage. No `DependencyError` on this path.

**Fallback behavior on IS miss** (line 2062–2086): When IS data is fully absent:

- Has UAC MVP seed → falls back to hardcoded seed symbols (logged as WARNING, not raised as error)
- No UAC seed → logs ERROR and skips venue via `skipped_shards[venue] = skip_reason` (no DependencyError)

**Live mode**: No `StaleUpstreamError`. Live WebSocket reconnect is stamped `data_freshness="STALE"` in the manifest
window boundary row, which is correct behavior per the stale-not-missing rule. But downstream consumers
(features-service live) do not check this `STALE` flag in the MTDS output manifest.

---

### features-service — YELLOW

**Batch mode — pre-flight check**:

The `BatchHandler._check_dependencies()` (batch_handler.py:127) uses `BaseDependencyChecker.check_dependencies()` which
probes GCS blob existence at `processed_candles/by_date/day={date}/` in the MTDS bucket. This is a GCS blob probe, **not
a manifest `capture_status` read**.

A separate `manifest_window_guard.check_window_manifest()` (`common/manifest_window_guard.py`) DOES read the MTDS
manifest `capture_status`:

- `attempted_failed` → emits `record_empty(reason=NO_INPUT_AVAILABLE)` + skips (correct)
- `empty_confirmed` → adjusts denominator (correct)

The two checks work independently:

1. `_check_dependencies()`: GCS blob probe → `DependencyError` if no blobs (blocks shard write entirely)
2. `manifest_window_guard`: manifest capture_status read → `record_empty` if `attempted_failed` (graceful per-calc skip)

**Gap**: The blob probe does NOT check whether the found blobs' upstream manifest rows are `attempted_failed`. A partial
day where some shards wrote parquets but also have `attempted_failed` rows will pass the blob probe, proceed to
calculation, and `manifest_window_guard` will catch the `attempted_failed` at the per-calc level (emitting
`record_empty`). This is the CORRECT behavior for the rolling-window case.

**However**: The `_check_dependencies()` calls `BaseDependencyChecker` which probes the wrong upstream bucket path. The
features dependency checker hardcodes `processed_candles/by_date/day={date}/` (market-data-processing-service output),
NOT the MTDS raw_tick_data path. This means it checks the MDPS (market-data-processing-service) output, not MTDS
directly.

**Live mode**: `LiveHandler.run()` uses a PubSub subscriber — no staleness gate. If MTDS WebSocket has a stale
reconnect, features-service live will receive old candle events but has no `StaleUpstreamError` or freshness assertion
before processing.

---

### strategy-service — YELLOW

**Batch mode — manifest check**:

`manifest_allocation_guard.check_allocation_manifest()` reads the upstream features-service manifest via
`read_availability_index(bucket)`. It correctly classifies `capture_status`:

- `captured` → proceed
- `attempted_failed` → set `should_skip_live=True` + `should_alert_live=True`
- `empty_confirmed` → set `should_skip_backtest=True` (forgiving skip)
- `unknown` (read error or absent) → fail-open (proceed)

This is correct behavior for **batch (backtest mode)**: skips on both `attempted_failed` and `empty_confirmed`.

**Gap — DependencyError not raised**: The guard returns `AllocationManifestResult` with a boolean `should_skip_live`.
The _caller_ decides whether to skip. There is no `DependencyError` raised by the guard itself. If a caller ignores the
`should_skip_live=True` result (which can happen with partial feature coverage), signals may still be emitted on top of
failed upstream data.

**Live mode — DataStalenessError**: `strategy_service/validation/freshness_gate.py` defines `assert_feature_fresh()`
which raises `DataStalenessError` when `age_seconds >= contract.max_age_seconds`. The function is defined and
re-exported via `strategy_service.validation.__init__`. However, rg found **zero call sites** in strategy-service's
non-test engine code. The function is declared but not wired into the live signal generation path. This is a **CRITICAL
gap for live mode**.

---

### execution-service — RED

**Batch mode**: execution-service has no batch data pipeline and does not write manifest rows for upstream strategy
data. This is by design — execution-service consumes strategy instructions via API/event. Not applicable.

**Live mode — upstream strategy freshness**:

`execution-service/engine/preflight.py` runs 5 startup checks: secret_manager, venue_api_keys, risk_service_health,
position_state_loaded, risk_limits_loaded. **None of these check whether strategy-service is alive or whether the
upstream strategy manifest has recent captured rows.**

`execution-service/validation/freshness_gate.py` defines `assert_market_data_fresh()` which raises `DataStalenessError`
for stale market data. However, **rg found zero call sites in execution-service engine code** (only in tests). The
function is declared but not called in any live execution path.

This means execution-service can receive and act on instructions from strategy-service without any stale-upstream gate.
If strategy-service emits stale signals based on failed upstream features data, execution-service will execute those
signals without any freshness check.

**Finding severity**: This is a **review-blocking** gap for the May-23 live DeFi gate. The execution layer has no
data-dependency freshness gate before submitting orders.

---

### ml-service — YELLOW

**Batch mode**:

`ml-service/inference/cli/handlers/batch_handler.py` uses the same `BaseDependencyChecker` + `DependencyError` pattern
as features-service. The inference dependency checker (`inference/app/core/dependency_checker.py`) probes two upstream
paths:

- `ml-training-store-{asset_group_lower}-{project_id}/models/by_date/day={date}/` (trained models)
- `features-delta-one-store-{asset_group_lower}-{project_id}/features/by_date/day={date}/` (features)

Both are GCS blob probes — not manifest `capture_status` reads. This has the same gap as features-service: if
features-service wrote partial data with `attempted_failed` rows but some parquets exist, ml-service will proceed with
degraded inputs.

**Live mode**: `ml-service/inference/app/core/prediction_publisher.py` comment mentions a `STRICT_FAIL` mode that
suppresses predictions when "the upstream feature window was stale or absent." This is a soft suppression, not a
`StaleUpstreamError` raise. No `StaleUpstreamError` class was found anywhere in the workspace.

---

## Silent-swallow findings (review-blocking)

### Finding 1 — execution-service: zero upstream freshness gate (P0, review-blocking for live)

**Location**: `execution-service/execution_service/validation/freshness_gate.py` +
`execution_service/engine/preflight.py`

**Issue**: `assert_market_data_fresh()` is defined but has **zero call sites in the engine source**. The preflight
checks venues/secrets/risk-service but NOT upstream strategy signal freshness. If strategy-service emits a stale signal
(because features were `attempted_failed`), execution-service will blindly execute it.

**Required fix**: Wire `assert_market_data_fresh()` into the live order submission path (before routing to venue
adapters). Also add a strategy-manifest freshness check in `run_preflight_checks()`.

---

### Finding 2 — strategy-service: DataStalenessError defined but not called in live path (P0)

**Location**: `strategy-service/strategy_service/validation/freshness_gate.py`

**Issue**: `assert_feature_fresh()` raises `DataStalenessError` when `age_seconds >= contract.max_age_seconds`. Zero
call sites in strategy-service engine code (confirmed via rg over all non-test source). This means live signal
generation never checks upstream feature freshness before emitting orders.

**Required fix**: Call `assert_feature_fresh()` in the strategy signal generation pipeline, at the point where feature
data is read. Abort signal emission if the SLA is exceeded.

---

### Finding 3 — MTDS: IS dependency check reads GCS blob, not manifest capture_status (P1)

**Location**: `market-tick-data-service/market_tick_data_service/engine/orchestrator.py:_check_instruments_available()`

**Issue**: The instruments-service dependency probe reads a raw parquet file and checks `table.num_rows > 0`. It does
not read the IS manifest `capture_status`. If IS wrote a partial parquet but marked the row as `attempted_failed`, MTDS
proceeds with a degraded instrument universe without raising `DependencyError`.

**Additional gap**: When IS data is absent AND UAC MVP seed is available, MTDS falls back silently with a `WARNING` log.
This is a degraded-but-not-failed state that may produce incorrect tick data completeness.

---

### Finding 4 — features-service / ml-service: GCS blob probe does not check upstream manifest capture_status (P1)

**Location**: `UTL/unified_trading_library/core/dependency_checker.py:BaseDependencyChecker._check_gcs_availability()`

**Issue**: `BaseDependencyChecker.check_dependencies()` probes GCS blob existence only. It does NOT read the upstream
manifest `capture_status`. A partial write where some parquets exist but the manifest shows `attempted_failed` will pass
the dependency check.

**Mitigation that partially covers this**: `features-service/common/manifest_window_guard.py` reads the manifest
directly for per-calc decisions. But this only covers rolling-window feature families. New feature families that don't
use `manifest_window_guard` will be blind to upstream `attempted_failed`.

**Required fix**: `BaseDependencyChecker` should optionally read the upstream service's manifest `capture_status`
instead of (or in addition to) the GCS blob probe. Add `check_manifest: bool = False` parameter.

---

### Finding 5 — features-service live mode: no MTDS staleness gate (P1)

**Location**: `features-service/features_service/delta_one/cli/handlers/live_handler.py`

**Issue**: Live mode connects to PubSub and processes candle events without checking whether MTDS live stream has had a
stale reconnect. If MTDS live connector reconnects (stamping `data_freshness="STALE"` in its manifest), features-service
live will continue processing candles from the stale feed without any upstream freshness check.

---

## DependencyError / StaleUpstreamError existence

### DependencyError

- **Defined in**: `UTL/unified_trading_library/core/dependency_checker.py:32` (`class DependencyError(Exception)`)
- **No `fail_fast=True` parameter**: The workspace SSOT says `DependencyError(fail_fast=True)` but the actual class
  takes no arguments beyond the message string. The "fail_fast" behavior is controlled by the caller (whether they
  `raise DependencyError` or log and continue). The `ErrorRecoveryStrategy.FAIL_FAST` enum exists in UAC schemas but is
  not wired to `DependencyError`.
- **Used by**: features-service (batch), ml-service (batch), features-service (onchain orchestrator)
- **Not used by**: MTDS (uses skip/fallback), strategy-service (returns `should_skip_live`), execution-service

### StaleUpstreamError

- **NOT defined anywhere in the workspace** (UAC, UTL, or any service)
- The equivalent mechanism is `DataStalenessError` (UAC
  `unified_api_contracts/internal/reference/data_freshness.py:309`)
- `DataStalenessError` is raised by `strategy_service.validation.freshness_gate.assert_feature_fresh()` and
  `execution_service.validation.freshness_gate.assert_market_data_fresh()` — but **neither function is called in engine
  code**

### DataStalenessError call wiring status

| Function                                         | Defined | Wired in engine | Test coverage |
| ------------------------------------------------ | ------- | --------------- | ------------- |
| `assert_feature_fresh()` (strategy-service)      | Yes     | ❌ NO           | Tests only    |
| `assert_market_data_fresh()` (execution-service) | Yes     | ❌ NO           | Tests only    |

---

## Remediation required

### P0 — Review-blocking (must fix before May-23 live gate)

1. **execution-service: Wire `assert_market_data_fresh()` into live order submission path**
   - File: `execution_service/engine/live/orchestrator.py` or equivalent order-routing path
   - Check before routing to any venue adapter
   - If stale: reject order with `DataStalenessError`, emit `ADAPTER_FETCH_FAILED`

2. **execution-service: Add strategy-service freshness to `run_preflight_checks()`**
   - Add a new preflight check: reads strategy-service manifest for latest captured row
   - If no rows in last N minutes (configurable), emit `PREFLIGHT_FAILED` + raise `PreflightCheckError`
   - File: `execution_service/engine/preflight.py`

3. **strategy-service: Wire `assert_feature_fresh()` into live signal generation path**
   - Find the feature-read callsite in strategy signal pipeline
   - Call `assert_feature_fresh()` after reading each feature; abort signal on `DataStalenessError`

### P1 — Data correctness (fix before May-23, non-blocking for initial paper trading)

4. **MTDS: Upgrade `_check_instruments_available()` to read IS manifest capture_status**
   - Current: `pq.read_table(gcs_path); return table.num_rows > 0`
   - Required: Also check IS manifest; if `attempted_failed`, log WARNING + use UAC seed (same as now), but emit a
     `DependencyError` event so operators are aware
   - File: `market_tick_data_service/engine/orchestrator.py:_check_instruments_available()`

5. **UTL: Add manifest capture_status probe to `BaseDependencyChecker`**
   - Add optional `check_manifest_capture_status: bool = False` to `_check_single_dependency()`
   - When enabled, read the upstream service's `_index/*.parquet` manifest and verify
     `capture_status != attempted_failed` before reporting dependency as available
   - This would fix features-service and ml-service dependency checks in one place

6. **features-service live: Add MTDS stream staleness check before processing candle events**
   - In `PubSubSubscriber` or `LiveHandler`: check MTDS live manifest for last `data_freshness` = `FRESH`
   - If MTDS was `STALE` in the last window, log WARNING and optionally suppress feature emission

### P2 — Architecture debt (post-May-23)

7. **strategy-service: `manifest_allocation_guard` should raise `DependencyError` on `attempted_failed`, not just return
   `should_skip_live=True`**
   - Current: returns flag, caller decides
   - Required: raise `DependencyError` to enforce fail-fast across all callers
   - File: `strategy_service/manifest_allocation_guard.py`

8. **Introduce `StaleUpstreamError` as a named class in UAC**
   - Currently, `DataStalenessError` covers both stream-time and batch staleness
   - A distinct `StaleUpstreamError` for stream-time upstream failures would enable more targeted error handling

---

## Summary scorecard

| Service           | Batch verdict                                                              | Live verdict                                                            | Blocking for May-23?                        |
| ----------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------- |
| MTDS              | YELLOW (GCS blob probe, no IS manifest check, fallback path)               | YELLOW (STALE stamped in manifest, no raise)                            | No — degraded quality risk, not hard fail   |
| features-service  | YELLOW (GCS probe + manifest_window_guard; two separate checks)            | YELLOW (no MTDS staleness gate in live)                                 | No — rolling-window guard covers most cases |
| strategy-service  | YELLOW (manifest read correct; DependencyError not raised, only skip flag) | RED (assert_feature_fresh defined but unwired)                          | YES for live mode                           |
| execution-service | N/A (no batch pipeline)                                                    | RED (assert_market_data_fresh unwired, no strategy freshness preflight) | YES — highest severity                      |
| ml-service        | YELLOW (GCS blob probe, same gap as features)                              | YELLOW (STRICT_FAIL suppression, no StaleUpstreamError)                 | No — inference is upstream of strategy      |

**Overall pipeline verdict: RED** — Two P0 wiring gaps in execution-service and strategy-service live mode mean the live
DeFi pipeline can submit orders based on stale/failed upstream data without any gate.
