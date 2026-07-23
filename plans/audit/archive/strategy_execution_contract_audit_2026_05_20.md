---
pair: strategy-service → execution-service
auditor: ikenna / tab-4
audit_date: 2026-05-20
audit_file: plans/audit/strategy_execution_contract_audit_2026_05_20.md
feeds_ordering_step: D6
status: complete
strategy_service_sha: e4e5a1e677b547a41684f8a8552b42e4a4229435
execution_service_sha: f6795bfe0152a3e9bbb42a99f2c3633410fb2146
---

# strategy-service → execution-service Contract Audit — 2026-05-20

> **Trigger**: C-series contract audit step D6 from mega-audit 2026-05-20. strategy-service writes `StrategyInstruction`
> parquets to GCS (strategy-store bucket) and emits trade signals; execution-service reads those parquets and routes
> orders to venues. This audit examines whether the handoff is governed by manifest, whether execution has a preflight
> gate on strategy availability, and whether both services satisfy the 7-pattern architectural contract.

## Architectural contract (SSOT)

```
  ┌─────────────────────────────────────────────────────┐
  │  strategy-service                                   │
  │  ─ generates StrategyInstruction objects per day    │
  │  ─ writes: strategy_instructions/                   │
  │      client_id={cid}/strategy_id={sid}/             │
  │      day={YYYY-MM-DD}/instructions.parquet          │
  │    to: strategy-store-{project_id} (UNIFIED bucket, │
  │      NO asset_group suffix)                         │
  │  ─ manifest emission: ZERO (C2 finding from prior   │
  │    audit) — confirmed in this audit                 │
  └────────────────────┬────────────────────────────────┘
                       │
                       ▼ GCS parquet read (strategy-store)
  ┌─────────────────────────────────────────────────────┐
  │  execution-service                                  │
  │  ─ DependencyChecker declares strategy-service      │
  │    as REQUIRED upstream (UPSTREAM_DEPS dict)        │
  │  ─ checks blob existence at strategy_instructions/  │
  │    prefix (date-pattern scan) — NOT manifest-based  │
  │  ─ backtest_checks.py check_dependencies() raises   │
  │    DependencyError if strategy blobs absent         │
  │  ─ validate_config_can_run() checks per-strategy_id │
  │    blob existence before per-config execution       │
  │  ─ manifest emission: ZERO (confirmed below)        │
  └─────────────────────────────────────────────────────┘
```

**Key contract boundary**: strategy-service → execution-service is a parquet-file handoff via GCS. No Pub/Sub event
carries `StrategyInstruction` at this boundary. execution-service discovers strategy outputs by GCS blob scan, not by
manifest read.

---

## 4-dimensional audit matrix (2026-05-20 snapshot)

### Dim 1 — Upstream adapter coverage per asset_group (strategy-service outputs)

| asset_group | strategy-service writes                                                                    | Consumption by execution-service                                                        | Violation type                                      |
| ----------- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- | --------------------------------------------------- |
| DeFi        | `strategy_instructions/client_id={cid}/strategy_id=DEFI_*/day={date}/instructions.parquet` | `execution_service/strategy_instructions/gcs.py` reads via `download_instructions_df()` | ✅ Reads GCS path; partial P7 violation (see below) |
| CeFi        | Same path, `strategy_id=CEFI_*`                                                            | Same loader, category derived from `strategy_id` prefix                                 | ✅ Covered                                          |
| TradFi      | Same path, `strategy_id=TRADFI_*`                                                          | Same loader                                                                             | ✅ Covered                                          |
| Sports      | No sports strategies                                                                       | N/A                                                                                     | out of scope                                        |
| Prediction  | No prediction strategies                                                                   | N/A                                                                                     | out of scope                                        |

**Evidence:**

```
# execution-service/execution_service/strategy_instructions/gcs.py:66-95
# build_instructions_location() extracts category from strategy_id prefix (DEFI_/CEFI_/TRADFI_)
# then calls config.get_bucket_for_asset_group("strategy", category)
# → P7 partial: bucket resolved via config method, NOT resolve_bucket_name() from UTL
```

```
# execution-service/execution_service/utils/dependency_checker.py:207-211
# UPSTREAM_DEPS["strategy-service"]["bucket_template"] = "strategy-store-{project_id}"
# → P7 violation: hardcoded bucket template string, NOT resolve_bucket_name()
```

### Dim 2 — Downstream handler upstream-consumption status

| Component                                                                      | Status                                                                                                               | Citation      |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | ------------- |
| `execution_service/strategy_instructions/gcs.py`                               | ✅ Reads via `download_instructions_df()` + fallback 404 handling                                                    | lines 127-165 |
| `execution_service/strategy_instructions/loader.py`                            | ✅ Validates `benchmark_price` for executable instructions; raises `InvalidBenchmarkPriceError` on NaN/zero/negative | lines 140-179 |
| `execution_service/utils/dependency_checker.py::DependencyChecker`             | ⚠ Blob-existence check only — does NOT consult strategy manifest; no `record_captured` status check                  | lines 207-230 |
| `execution_service/cli/backtest_checks.py::check_dependencies()`               | ⚠ Calls `DependencyChecker.check_dependencies()` which checks prefix existence, NOT per-`strategy_id` blob           | lines 48-95   |
| `execution_service/utils/dependency_checker.py::check_strategy_instructions()` | ✅ Checks per-`strategy_id` + date blob existence; raises `DependencyError` on miss (required=True)                  | lines 466-484 |
| `execution_service/utils/dependency_checker.py::validate_config_can_run()`     | ✅ Calls `check_strategy_instructions()` + `check_market_tick_data()` + `check_instrument_definitions()`             | lines 619-662 |

**Critical gap**: `check_dependencies()` (called from `backtest_checks.py`) only scans the `strategy_instructions/`
prefix for date-pattern hits — it does NOT call `check_strategy_instructions()` which is the per-`strategy_id`/date
specific check. The general batch preflight will pass if ANY strategy instruction exists for the day, even if the
specific `strategy_id` is missing.

---

### Dim 3 — Manifest emission per component

| Component                                                                    | Status                                                                                                          | Evidence      |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------- |
| `strategy_service/engine/core/gcs_storage_service.py::write_instructions()`  | ❌ **ZERO manifest emission** — writes parquet to GCS with NO `record_captured/record_empty/record_failed` call | lines 159-198 |
| `strategy_service/cli/handlers/batch_handler.py` (batch completeness check)  | ⚠ Calls `validate_batch_completeness()` only; no manifest recorder used                                         | lines 492-510 |
| `execution_service/strategy_instructions/gcs.py::download_instructions_df()` | ❌ **ZERO manifest emission** — reads file; 404 → empty DataFrame with no `record_empty`                        | lines 127-165 |
| `execution_service/utils/dependency_checker.py`                              | ❌ **ZERO manifest emission** — checks blob existence with no manifest record                                   | lines 318-370 |

**Pre-audit grep evidence:**

```bash
# rg 'record_captured|record_empty|record_failed' execution-service/ --type py | head -20
# → 0 results (zero manifest emission in all execution-service source)

# rg 'record_captured|record_empty|record_failed' strategy-service/strategy_service/ --type py | head -20
# → 0 results (zero manifest emission in strategy_service/ production code)
```

**This is the P0 finding from prior C2 audit, CONFIRMED here with additional context:**

1. strategy-service writes `instructions.parquet` with no `record_captured` → no availability index entry
2. execution-service reads the same file with no `record_empty(reason=...)` on 404 → silent empty
3. The combination means: if strategy-service failed to write instructions for a day, execution-service silently
   receives an empty DataFrame, produces no trades, and no manifest row surfaces the gap.

---

### Dim 4 — Manifest schema version per bucket

| Bucket                                            | Schema version state                                                                                                  | Action                                                                           |
| ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `strategy-store-{project_id}`                     | **NOT APPLICABLE** — strategy-service emits zero manifest rows. No availability_index parquet exists for this bucket. | P2 remediation must ADD manifest emission before schema version can be assessed. |
| `execution-store-{cefi,defi,tradfi}-{project_id}` | Not assessed in this audit (execution outputs are trade fills, not data-capture outputs)                              | out of scope for D6                                                              |

---

## Pattern assessments

### Pattern 1 — SSOT-owned reference flowing down

**Status: ✅ Verified clean for strategy→execution direction.**

execution-service does NOT re-enumerate strategies from instruments-service or re-call strategy APIs. It reads the GCS
output path that strategy-service produced. The IS→strategy contract (C1 audit) covers strategy's consumption of IS.
This pair's Pattern 1 is clean.

### Pattern 2 — Manifest emission discipline

**Status: ❌ P0 — BOTH services have zero manifest emission for this handoff.**

- strategy-service `write_instructions()` writes parquet with no manifest recorder
- execution-service `download_instructions_df()` reads parquet with no manifest recorder
- `DependencyChecker` performs blob-existence checks without manifest integration

**Impact on May-23 gate**: execution cannot run a manifest preflight on strategy instructions. If strategy-service
silently skips a day (e.g., `validate_batch_completeness` logs a warning but continues — confirmed at
`batch_handler.py:501-508`), execution proceeds with an empty DataFrame producing no trades but emitting no alert. This
is a DIVERGENT_EMPTY without diagnosis.

### Pattern 3 — Schema-version compliance

**Status: ⚠ BLOCKED — cannot assess until P2 remediation adds manifest emission.**

No `schema_version` column exists in any output at this boundary. Once manifest emission is added, schema_version=8 must
be declared from first write.

### Pattern 4 — Honest-absence reason taxonomy

**Status: ❌ P0 — no `record_empty(reason=...)` calls exist.**

When `download_instructions_df()` receives a 404, it returns `pd.DataFrame()` with no manifest emission. This hides
hold-days vs missing-days vs strategy-failure-days — all produce identical silent empty results. Required fix:
execution-service must call `record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)` on 404 and
`record_failed(...)` on non-404 errors.

### Pattern 5 — `expected_coverage()` preflight + `DIVERGENT_EMPTY` post-hoc check

**Status: ❌ P0 — no `expected_coverage()` call anywhere in this handoff.**

DependencyChecker checks GCS blob existence but does NOT call `expected_coverage(venue, data_type, date)`. No post-hoc
divergence scanner covers the `strategy-store` bucket.

### Pattern 6 — Error classification at the boundary

**Status: ❌ — NO `classify_venue_error()` or `ADAPTER_FETCH_FAILED` emission.**

`execution_service/strategy_instructions/gcs.py` has bare exception handling that wraps errors in `RuntimeError` via
`_raise_gcs_instructions_error()` without calling `classify_venue_error()` or emitting `ADAPTER_FETCH_FAILED`.
strategy-service `write_instructions()` also has bare `except (OSError, json.JSONDecodeError, ValueError)` with no
classify/emit.

**Evidence:**

```bash
# rg 'classify_venue_error|ADAPTER_FETCH_FAILED' execution-service/execution_service/ --type py | grep -v test
# → 0 results
```

**Note**: execution-service is primarily a consumer, not a data-capture adapter. The P6 requirement applies primarily to
the strategy-service GCS write path and the execution read path. For execution, the applicable requirement is P2
(manifest emission) rather than P6 (which is designed for external-API adapter error classification).

### Pattern 7 — Bucket-SSOT

**Status: ❌ P7 violations in both services.**

**execution-service/execution_service/utils/dependency_checker.py:207-210:**

```python
"strategy-service": {
    "bucket_template": "strategy-store-{project_id}",  # hardcoded template, NOT resolve_bucket_name
    ...
}
```

**execution-service/execution_service/strategy_instructions/gcs.py:86-92:**

```python
bucket = config.get_bucket_for_asset_group("strategy", category)
# Uses config method, not resolve_bucket_name() from UTL
# canonical pattern = resolve_bucket_name(cloud="gcp", kind="strategy-store", asset_group=...)
```

**strategy-service/strategy_service/engine/core/gcs_storage_service.py:183:**

```python
gcs_path = f"gs://{self.bucket_name}/{blob_path}"  # noqa: gs-uri
# bucket_name obtained from config.get_output_bucket(), not resolve_bucket_name()
```

The `# noqa: gs-uri` tags suppress QG STEP 5.69 for the inline URI construction, but the root cause is that
`resolve_bucket_name()` from UTL is not used to obtain `bucket_name`.

---

## Known prior findings confirmed / extended

### C2: strategy-service zero manifest emission (confirmed + scope extended)

**Prior finding**: `strategy-service/strategy_service/engine/core/gcs_storage_service.py` has zero manifest emission for
strategy output.

**This audit confirms**: AND adds that execution-service also has zero manifest emission when reading strategy
instructions. The C2 fix must cover BOTH the write path (strategy-service) AND the read path (execution-service). A fix
only on the write side still leaves execution with no preflight gate.

### A5: strategy `batch_handler.py` warn-but-proceed

**Prior finding**: `batch_handler.py:130,502` warn-but-proceed (doesn't raise `DependencyError`).

**This audit locates precisely**:

- Line 127-140: `elif failures: logger.warning(...) ... emit_preflight_skip(DEPENDENCIES_MISSING_CONTINUE)` —
  warn-and-continue when `fail_on_missing=False`
- Line 501-508: `validate_batch_completeness` is called after the loop; on incomplete result, logs `logger.warning(...)`
  but returns `_build_handle_result(all_results, errors)` without raising.

**Relationship to this audit**: when strategy-service warn-proceeds on a batch-incompleteness, it writes partial
instructions (or no instructions) for some strategies. Because there is no manifest emission, execution-service has no
way to distinguish "strategy wrote heartbeat/hold" from "strategy failed to write."

### C3: execution-service InstrumentDefinitionsLoader gates on IS but not strategy manifest

**Prior finding**: execution-service `InstrumentDefinitionsLoader` gates on IS availability.

**This audit confirms**: The IS gate is via `check_instrument_definitions()` in `DependencyChecker`. This correctly
raises `DependencyError` if IS data is absent. However, strategy instructions have a WEAKER gate: the general
`check_dependencies()` call (from `backtest_checks.py`) scans the entire `strategy_instructions/` prefix without
verifying the specific `strategy_id`. The per-`strategy_id` check (`check_strategy_instructions()`) is only invoked via
`validate_config_can_run()`, which is not called in the main `check_dependencies()` path used by `backtest_checks.py`.
This creates a scenario where batch preflight passes (some strategy instructions found at prefix) but the specific
strategy has no instructions for that day.

---

## P0 findings summary

| #    | Finding                                                                                                                              | Severity                                      | File(s)                                                                                                    | Required fix                                                                                                                                                                |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P0.1 | strategy-service writes instructions with zero manifest emission                                                                     | P0 — May-23 critical                          | `strategy_service/engine/core/gcs_storage_service.py:159-198`                                              | Add `record_captured()` on success, `record_failed()` on exception, `record_empty(reason=SOURCE_RETURNED_ZERO)` when df is empty                                            |
| P0.2 | execution-service reads instructions with zero manifest emission                                                                     | P0 — May-23 critical                          | `execution_service/strategy_instructions/gcs.py:127-165`                                                   | Add `record_empty(reason=SOURCE_RETURNED_ZERO)` on 404, `record_failed()` on other errors, `record_captured()` on non-empty read                                            |
| P0.3 | `check_dependencies()` does NOT check per-`strategy_id` instructions; general prefix scan may pass when specific strategy is missing | P0 — silently runs with wrong/missing signals | `execution_service/cli/backtest_checks.py:48-95` + `execution_service/utils/dependency_checker.py:371-378` | Route backtest preflight through `validate_config_can_run()` (which calls `check_strategy_instructions()`) rather than generic `check_dependencies()`                       |
| P0.4 | batch_handler warn-but-proceed on batch incompleteness (A5) — strategy writes partial output without manifest signal                 | P0 — connects to C2                           | `strategy_service/cli/handlers/batch_handler.py:501-508`                                                   | On `not is_complete`: emit `record_failed()` for missing instrument/strategy cells and raise `DependencyError` (or emit at minimum `PROCESSING_INCOMPLETE` lifecycle event) |

---

## P1 findings summary

| #    | Finding                                                                   | Severity                  | File(s)                                                                      | Required fix                                                                                               |
| ---- | ------------------------------------------------------------------------- | ------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| P1.1 | strategy-service bucket obtained from config, not `resolve_bucket_name()` | P1 — P7 violation         | `strategy_service/engine/core/gcs_storage_service.py:58-65` + `gcs.py:86-92` | Replace `config.get_output_bucket()` with `resolve_bucket_name(cloud="gcp", kind="strategy-store")`        |
| P1.2 | execution DependencyChecker uses hardcoded bucket template string         | P1 — P7 violation         | `execution_service/utils/dependency_checker.py:208-210`                      | Replace template with `resolve_bucket_name(...)` call at check time                                        |
| P1.3 | error classification missing from execution read path                     | P1 — P6 partial violation | `execution_service/strategy_instructions/gcs.py:24-34,145-165`               | Wrap `_raise_gcs_instructions_error` with classify pattern; emit `ADAPTER_FETCH_FAILED` for non-404 errors |

---

## Scope exclusions

- **P3 (schema-version)**: not assessable — manifest emission must be added first (P0.1/P0.2 fixes are prerequisites).
- **P5 (expected_coverage preflight)**: not applicable to strategy-service — this service generates signals, not data
  captures. `expected_coverage()` is a data-capture pattern. Strategy instruction availability should be gated by the
  manifest `capture_status` read in execution-service's preflight (once P0.2 adds emission).
- **DeFi archetype coverage matrix**: strategy-service adapter coverage (carry_staked_basis, arbitrage_price_dispersion)
  is covered by the IS→strategy audit (C1). This audit focuses only on the strategy→execution handoff contract.

---

## QG-ratchet phase

### Phase Q — QG enforcement (strategy→execution boundary)

| Pattern                                 | QG script                                       | Status in execution-service QG                                                                                                                                              |
| --------------------------------------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P2 — Manifest emission (strategy write) | `no_silent_absence_handlers.sh`                 | **GAP** — strategy-service `write_instructions()` is not an `_handler.py` file; the script doesn't scan `gcs_storage_service.py`. Must extend script or add inline rg step. |
| P2 — Manifest emission (execution read) | `no_silent_absence_handlers.sh`                 | **GAP** — execution-service has no handlers in the scanned path; `gcs.py` not included.                                                                                     |
| P6 — Error classification               | `no_adapter_contract_regression.sh` (STEP 5.83) | **GAP** — strategy write path + execution read path not covered by this step.                                                                                               |
| P7 — Bucket SSOT                        | `check_inline_bucket_uri.py` (STEP 5.69)        | **PARTIAL** — `# noqa: gs-uri` tags suppress detection; root cause (not using `resolve_bucket_name`) is not caught.                                                         |

---

## Continuous-verification column

| Pattern                     | Continuous-verification path                                                                                             | Cadence         | Last verified             |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------- | ------------------------- |
| P2 — Manifest emission      | After fix: `no_silent_absence_handlers.sh` extended to include `gcs_storage_service.py` + `strategy_instructions/gcs.py` | every push      | not yet wired             |
| P3 — Schema-version         | After fix: inline QG rg step for `schema_version=[1-7]`                                                                  | every push      | n/a until P0.1/P0.2 fixed |
| P4 — Honest-absence reasons | After fix: `LegacyBlankErrorReasonError` raised at runtime if blank reason passed                                        | every batch run | n/a until P0.1/P0.2 fixed |
| P6 — Error classification   | After fix: `no_adapter_contract_regression.sh` extended                                                                  | every push      | not yet wired             |
| P7 — Bucket SSOT            | `check_inline_bucket_uri.py` (STEP 5.69) — once `resolve_bucket_name` wired, noqa tags can be removed                    | every push      | open violation            |

---

## Phased remediation DAG

```
Phase 1 — Add manifest emission to strategy-service write path (P0.1)
   ─ gcs_storage_service.py::write_instructions() → record_captured/record_empty/record_failed
   ─ batch_handler.py::validate_batch_completeness warn path → record_failed per missing cell
   │
Phase 2 — Add manifest emission to execution-service read path (P0.2)  [PARALLEL with Phase 1]
   ─ strategy_instructions/gcs.py::download_instructions_df() → record_empty on 404, record_captured on rows
   │
Phase 3 — Fix preflight gate (P0.3)
   ─ backtest_checks.py::check_dependencies() → route to validate_config_can_run() per strategy_id
   ─ Depends on Phase 2 (manifest must exist before manifest-based preflight makes sense)
   │
Phase 4 — Bucket SSOT (P1.1 + P1.2)  [PARALLEL with Phase 3]
   ─ strategy-service: replace config.get_output_bucket() with resolve_bucket_name()
   ─ execution-service: replace UPSTREAM_DEPS template with resolve_bucket_name() at call time
   │
Phase 5 — Error classification (P1.3)  [PARALLEL with Phase 4]
   ─ execution_service/strategy_instructions/gcs.py: wrap _raise_gcs_instructions_error with classify pattern
   │
Phase Q — QG enforcement
   ─ Extend no_silent_absence_handlers.sh to cover gcs_storage_service.py + strategy_instructions/gcs.py
   ─ Extend no_adapter_contract_regression.sh to execution read path

Phase D — Codex doc update
   ─ Update /codex/04-architecture/defi-execution-overview.md to note manifest handoff contract
```

**Foundation-completion-gate rule**: Phase 3 preflight-gate fix MUST NOT ship before Phase 1+2 manifest emission fixes.
A manifest-based preflight gate on empty manifests is useless. Phases 1+2 are prerequisites.

---

## Temporary states + their canonical follow-up plans

- **`validate_batch_completeness` warn path (A5)**: current temporary state is warn-but-continue. Successor plan: once
  manifest emission is added (Phase 1), the warn path should emit `record_failed` per missing cell and can optionally
  re-raise depending on operator policy. Track in `plans/active/strategy_manifest_writegate_YYYY_MM_DD.md` when that
  plan is created.
- **General `check_dependencies()` prefix scan (P0.3)**: temporary state until Phase 3 routes through
  `validate_config_can_run()`. No separate successor plan needed — fix is in Phase 3 of this audit's DAG.

---

## Sampling / coverage transparency

- **Grep coverage**: exhaustive search of `execution_service/` (all .py) and `strategy_service/strategy_service/` (all
  .py) for `record_captured`, `record_empty`, `record_failed`, `resolve_bucket_name`, `classify_venue_error`,
  `ADAPTER_FETCH_FAILED`, `validate_can_run`, `check_dependencies`. All patterns returned 0 hits in production source
  (grep output above).
- **Read coverage**: read all files in `execution_service/strategy_instructions/` (3 files),
  `execution_service/utils/dependency_checker.py` (678 lines), `execution_service/cli/backtest_checks.py` (248 lines),
  `strategy_service/engine/core/gcs_storage_service.py` (578 lines), `strategy_service/cli/handlers/batch_handler.py`
  (first 510 lines + line 502 region).
- **Not sampled**: `execution_service/cli/handlers/live_execution_handler.py` — live path not explicitly audited; same
  patterns expected to apply. Flag for follow-up.
- **Bucket actual-state**: bucket schema versions not sampled (strategy-store has no manifest parquet → no rows to
  check; this is itself the P0.1 finding).
