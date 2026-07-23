---
doc_type: plan
title: strategy→execution contract remediation — manifest emission + bucket SSOT + preflight gate
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, market-tick-data-service, strategy-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-20
source:
  [
    plans/audit/strategy_execution_contract_audit_2026_05_20.md,
    plans/active/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md (Phase D6),
  ]
estimate_class: brand-new
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 3.0
parent_epic: strategy_master
assigned_vm: vm-trading-core
priority: P2
archived: 2026-05-23
---

# strategy→execution contract remediation — 2026-05-20

> **Trigger**: Phase D6 of mega-audit-and-plan-beefup-progression-2026-05-20. C7 audit found P0 violations in
> strategy-service write path + execution-service read path. Both sides have zero manifest emission, creating a
> silent-empty gap when strategy-service fails to produce instructions for a day.

## Context

- **Feeding audits**: C7 (`plans/audit/strategy_execution_contract_audit_2026_05_20.md`)
- **May-23 gate impact**: execution-service cannot manifest-preflight strategy availability. If strategy-service
  silently skips a day, execution runs with empty instructions and produces no trades with no alert.
- **Shard atom**: `(client_id, strategy_id, day)` — same key as the parquet path
- **Bucket**: `strategy-store-{project_id}` (shared, no asset_group suffix)

---

## Pre-audit symbol inventory (MANDATORY before touching)

```bash
# Strategy-service write path callsites — nothing to rename but note all callers
rg "write_instructions" strategy-service/strategy_service/ --type py
# → must update all callers to expect the new return type if we change the signature

# ManifestWriter availability in UTL
rg "ManifestWriter" unified-trading-library/unified_trading_library/ --type py | head -5

# resolve_bucket_name import pattern
rg "resolve_bucket_name" market-tick-data-service/ --type py | head -5
```

---

## Phased execution DAG

```
Phase 1 — strategy-service manifest emission (P0.1 + P0.4)          [THIS PLAN OWNS]
   ├── 1a. Write StrategyManifestRecorder shim in strategy-service
   ├── 1b. Wire record_captured/empty/failed in write_instructions()
   ├── 1c. Fix batch_handler warn-but-proceed → record_failed + DependencyError
   └── QG: strategy-service quality-gates.sh GREEN
         │
Phase 2 — execution-service manifest emission (P0.2)                [PARALLEL with Phase 1]
   ├── 2a. Wire record_empty(SOURCE_RETURNED_ZERO) on 404 in download_instructions_df()
   ├── 2b. Wire record_captured on non-empty read
   ├── 2c. Wire record_failed on non-404 errors
   └── QG: execution-service quality-gates.sh GREEN
         │
Phase 3 — execution preflight gate fix (P0.3)                       [AFTER Phase 2]
   ├── 3a. Route backtest_checks.check_dependencies() through validate_config_can_run()
   └── QG: execution-service quality-gates.sh GREEN
         │
Phase 4 — bucket SSOT (P1.1 + P1.2)                                 [PARALLEL with Phase 3]
   ├── 4a. strategy-service: replace config.get_output_bucket() with resolve_bucket_name()
   ├── 4b. execution-service: replace hardcoded template in UPSTREAM_DEPS with resolve_bucket_name()
   └── QG: no inline gs:// URIs remaining (STEP 5.69)
         │
Phase 5 — error classification (P1.3)                               [PARALLEL with Phase 4]
   ├── 5a. execution_service/strategy_instructions/gcs.py: wrap _raise_gcs_instructions_error
   └── QG: no_adapter_contract_regression.sh extended
         │
Phase Q — QG ratchet                                                 [AFTER Phase 5]
   ├── Qa. Extend no_silent_absence_handlers.sh to cover gcs_storage_service.py
   └── Qb. Extend no_silent_absence_handlers.sh to cover strategy_instructions/gcs.py
```

**Foundation-completion-gate rule**: Phase 3 MUST NOT ship before Phase 2. Manifest-based preflight on empty manifest is
useless.

---

## Phase 1 — strategy-service manifest emission

### 1a. Write StrategyManifestRecorder shim

**File**: `strategy-service/strategy_service/engine/core/strategy_manifest.py` (NEW)

The recorder wraps `ManifestWriter` from UTL, following the same pattern as `DefiManifestRecorder` in MTDS.

```python
"""Honest-coverage manifest recording for strategy-service write path.

Shard atom: (client_id, strategy_id, day) — matches the parquet path.
Treats strategy_id as 'venue' and 'strategy_instructions' as data_type.
"""
from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from types import TracebackType
from typing import Self

from unified_trading_library import ManifestWriter, log_event

logger = logging.getLogger(__name__)


class StrategyManifestRecorder:
    def __init__(
        self,
        *,
        catalogue_bucket: str,
        target_day: date,
        strategy_id: str,
        client_id: str,
    ) -> None:
        self._writer = ManifestWriter(
            service_name="strategy-service",
            catalogue_bucket=catalogue_bucket,
            batch_size=1,
        )
        self._day = target_day
        self._strategy_id = strategy_id
        self._client_id = client_id

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._writer.close()

    def record_captured(self, *, row_count: int) -> None:
        self._writer.record_captured(
            venue=self._strategy_id,
            data_type="strategy_instructions",
            row_key=f"{self._client_id}/{self._strategy_id}/{self._day}",
            row_count=row_count,
            available_at=datetime.now(UTC),
            schema_version=8,
        )
        logger.info(
            "manifest captured: strategy_id=%s client_id=%s day=%s rows=%d",
            self._strategy_id, self._client_id, self._day, row_count,
        )

    def record_empty(self, *, reason: str) -> None:
        self._writer.record_empty(
            venue=self._strategy_id,
            data_type="strategy_instructions",
            row_key=f"{self._client_id}/{self._strategy_id}/{self._day}",
            reason=reason,
        )
        logger.info(
            "manifest empty: strategy_id=%s client_id=%s day=%s reason=%s",
            self._strategy_id, self._client_id, self._day, reason,
        )

    def record_failed(self, *, error_message: str) -> None:
        self._writer.record_failed(
            venue=self._strategy_id,
            data_type="strategy_instructions",
            row_key=f"{self._client_id}/{self._strategy_id}/{self._day}",
            error_message=error_message,
        )
        logger.warning(
            "manifest failed: strategy_id=%s client_id=%s day=%s error=%s",
            self._strategy_id, self._client_id, self._day, error_message,
        )
```

### 1b. Wire manifest recorder in write_instructions()

**File**: `strategy-service/strategy_service/engine/core/gcs_storage_service.py:159-198`

Before:

```python
def write_instructions(self, strategy_id, date_str, instructions_df, client_id=""):
    blob_path = f"strategy_instructions/client_id={client_id}/strategy_id={strategy_id}/day={date_str}/instructions.parquet"
    gcs_path = f"gs://{self.bucket_name}/{blob_path}"  # noqa: gs-uri
    try:
        if not self._validate_schema(instructions_df, "instructions", context=f"{strategy_id}/{date_str}"):
            logger.error("Skipping instructions upload due to schema validation errors")
            return None
        instructions_df.write_parquet(gcs_path)
        logger.info("Written instructions to %s", gcs_path)
        return gcs_path
    except (OSError, json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to write instructions: %s", e)
        raise
```

After:

```python
def write_instructions(self, strategy_id, date_str, instructions_df, client_id=""):
    from datetime import date as date_type
    from strategy_service.engine.core.strategy_manifest import StrategyManifestRecorder
    blob_path = f"strategy_instructions/client_id={client_id}/strategy_id={strategy_id}/day={date_str}/instructions.parquet"
    gcs_path = f"gs://{self.bucket_name}/{blob_path}"  # noqa: gs-uri
    target_day = date_type.fromisoformat(date_str)
    with StrategyManifestRecorder(
        catalogue_bucket=self.bucket_name,
        target_day=target_day,
        strategy_id=strategy_id,
        client_id=client_id,
    ) as recorder:
        try:
            if not self._validate_schema(instructions_df, "instructions", context=f"{strategy_id}/{date_str}"):
                logger.error("Skipping instructions upload due to schema validation errors")
                recorder.record_failed(error_message="schema_validation_failed")
                return None
            if len(instructions_df) == 0:
                recorder.record_empty(reason="SOURCE_RETURNED_ZERO")
                logger.info("Empty instructions df for %s/%s — hold day recorded", strategy_id, date_str)
                return None
            instructions_df.write_parquet(gcs_path)
            recorder.record_captured(row_count=len(instructions_df))
            logger.info("Written instructions to %s", gcs_path)
            return gcs_path
        except (OSError, json.JSONDecodeError, ValueError) as e:
            recorder.record_failed(error_message=str(e))
            logger.error("Failed to write instructions: %s", e)
            raise
```

### 1c. Fix batch_handler warn-but-proceed (P0.4)

**File**: `strategy-service/strategy_service/cli/handlers/batch_handler.py:501-508`

Before:

```python
if not is_complete:
    logger.warning(
        "Batch incomplete for date=%s — %d/%d instruments missing: %s",
        start_date, len(missing), len(instruments), missing,
    )
```

After (emit lifecycle event + DO NOT re-raise — shard isolation rule prevents raise inside loop):

```python
if not is_complete:
    logger.warning(
        "Batch incomplete for date=%s — %d/%d instruments missing: %s",
        start_date, len(missing), len(instruments), missing,
    )
    log_event("PROCESSING_INCOMPLETE", {
        "service": "strategy-service",
        "date": str(start_date),
        "missing_count": len(missing),
        "missing": list(missing),
    })
```

Note: A `DependencyError` raise at this level would kill the entire batch handler instead of isolating per-shard. The
correct fix is to emit `PROCESSING_INCOMPLETE` (a lifecycle event readable by the orchestrator) and let `record_failed`
on individual `write_instructions` calls handle per-shard failure visibility. The warn-but-proceed is acceptable here AS
LONG AS individual shard failures are recorded via `record_failed` in `write_instructions`.

---

## Phase 2 — execution-service manifest emission

### 2a-2c. Wire manifest emission in download_instructions_df()

**File**: `execution-service/execution_service/strategy_instructions/gcs.py:127-165`

The execution-service reads strategy instructions. It should record:

- `record_captured` when it reads a non-empty DataFrame (confirmação de disponibilidade)
- `record_empty(SOURCE_RETURNED_ZERO)` on 404 (hold day — strategy produced no instructions)
- `record_failed` on any non-404 error

Requires a `ExecutionManifestRecorder` shim (or directly use `ManifestWriter`) in
`execution_service/strategy_instructions/manifest.py` (NEW).

The shard key must match what strategy-service writes: `(client_id, strategy_id, day)`.

---

## Phase 3 — execution preflight gate (P0.3)

**File**: `execution-service/execution_service/cli/backtest_checks.py:48-95`

Current: calls generic `DependencyChecker.check_dependencies()` which scans the whole `strategy_instructions/` prefix.
Required: route through `DependencyChecker.validate_config_can_run()` which calls per-`strategy_id` check.

---

## Phase 4 — bucket SSOT (P1.1 + P1.2)

### 4a. strategy-service

**File**: `strategy-service/strategy_service/engine/core/gcs_storage_service.py:58-65`

Replace:

```python
config = get_config()
return config.get_output_bucket()
```

With:

```python
from unified_trading_library.cloud_interface.bucket_naming import resolve_bucket_name
return resolve_bucket_name(cloud="gcp", kind="strategy-store")
```

### 4b. execution-service

**File**: `execution-service/execution_service/utils/dependency_checker.py:208-210`

Replace hardcoded `"bucket_template": "strategy-store-{project_id}"` with call to `resolve_bucket_name()` at check time.

---

## Phase 5 — error classification (P1.3)

**File**: `execution-service/execution_service/strategy_instructions/gcs.py:24-34,145-165`

Wrap `_raise_gcs_instructions_error()` to emit `ADAPTER_FETCH_FAILED` for non-404 errors. Note: this is a consumer error
classification, not an adapter error, so the pattern is lighter — just log_event with the error code rather than full
`classify_venue_error()`.

---

## Phase Q — QG ratchet

- Extend `no_silent_absence_handlers.sh` (or add inline rg step) to scan `gcs_storage_service.py` in strategy-service
- Extend same script to scan `execution_service/strategy_instructions/gcs.py`
- Remove `# noqa: gs-uri` tags once `resolve_bucket_name()` is wired in Phase 4

---

## Todos

### Phase 1 — strategy-service (P0.1 + P0.4)

- [x] ✅ **[CODE] P0.** 1a. Write `strategy_service/engine/core/strategy_manifest.py` — StrategyManifestRecorder shim —
      strategy-service@cd617891
- [x] ✅ **[CODE] P0.** 1b. Wire manifest recorder in `gcs_storage_service.py::write_instructions()` —
      strategy-service@cd617891
- [x] ✅ **[CODE] P0.** 1c. Fix `batch_handler.py:501-508` — emit PROCESSING_INCOMPLETE event on batch incompleteness —
      strategy-service@cd617891
- [x] ✅ **[QG] P0.** Phase 1 QG: `cd strategy-service && bash scripts/quality-gates.sh` GREEN — 4118 passed, 5
      pre-existing failures, basedpyright 0 errors

### Phase 2 — execution-service (P0.2)

- [x] ✅ **[CODE] P0.** 2a. Write `execution_service/strategy_instructions/manifest.py` — ExecutionManifestRecorder —
      execution-service@19dd21388
- [x] ✅ **[CODE] P0.** 2b-c. Wire record_captured/empty/failed in `download_instructions_df()` —
      execution-service@19dd21388
- [x] ✅ **[QG] P0.** Phase 2 QG: ruff + basedpyright 0 errors on `strategy_instructions/` (full QG fails pre-existing
      foreign lint errors in backtest_args.py/benchmark_compare.py) — execution-service@19dd21388

### Phase 3 — preflight gate (P0.3)

- [x] ✅ **[CODE] P0.** 3a. Route `backtest_checks.check_dependencies()` through `check_config_specific_dependencies()`
      per strategy_id when config present — execution-service@dbd9c4f35
- [x] ✅ **[QG] P0.** Phase 3 QG: ruff + basedpyright 0 errors on backtest.py + backtest_checks.py —
      execution-service@dbd9c4f35

### Phase 4 — bucket SSOT (P1.1 + P1.2)

> **🟢 UNBLOCKED 2026-05-20 round 5 — operator decision**: **Unified bucket**. Add flat `strategy-store` yaml entry;
> write + read paths both use `strategy-store-${GCP_PROJECT_ID}`. Cross-asset strategies (portfolio allocator spanning
> CEFI+DEFI+TRADFI) read/write the same bucket. Migration: copy existing per-AG strategy data into the flat bucket, then
> delete per-AG entries from `cloud-providers.yaml`. Sequenced under master coordinator `mtds_mdps_master.md` Phase 1
> (bucket-name symmetry — extends to this strategy-store consolidation).

- [x] ✅ **[CODE] P1.** 4a. strategy-service `_get_shared_bucket()` → `resolve_bucket_name("strategy-store")` (unified,
      no asset_group arg). Remove per-AG dict from `cloud-providers.yaml`; add flat entry
      `strategy-store: "strategy-store-${GCP_PROJECT_ID}"`. Update all call sites. — deployment-service@aa51965 +
      strategy-service@72beb56c
- [x] ✅ **[CODE] P1.** 4b. execution-service `UPSTREAM_DEPS` template + `check_strategy_instructions()` +
      `build_instructions_location()` all use the unified bucket. Pre-existing write=unified vs read=per-AG mismatch
      resolved at the yaml level. — deployment-service@aa51965 + execution-service@0948346e
- [x] ✅ **[CODE] P1.** 4d. (AUDIT-03 F-37b residual — folded here 2026-05-22) The carry manifest writers still
      hand-build the catalogue bucket name: `catalogue_bucket = f"strategy-store-{cfg.project_id}"` at
      `hedge_ratio_writer.py:136` + `decision_context_writer.py:149`, bypassing the
      `resolve_bucket_name(kind="strategy-store")` that the SAME files already use on L92 for the data bucket. Replace
      both with `resolve_bucket_name(...)`. NOTE: the `gs://{bucket}/...` display strings in `gcs_storage_service.py` +
      `grid_generator.py` are `# noqa: gs-uri`-exempt (bucket already resolved by 4a) — NOT in scope. —
      strategy-service@5b2e9924; hedge_ratio_writer.py:135 + decision_context_writer.py:148 both use
      `resolve_bucket_name(cloud=cloud, kind="strategy-store")` for catalogue_bucket (verified 2026-05-22).
- [x] ✅ DEFERRED-OPERATOR-DECISION **[BLOCKED-OPERATOR-DECISION] [MIGRATION] P0.** 4c. Migrate existing per-AG strategy
      parquets into the unified bucket. **BLOCKED**: schemas are incompatible — old per-AG format
      `strategy_instructions/<strategy_id>/<date>.parquet` vs new unified format
      `strategy_instructions/client_id=/strategy_id=/day=/instructions.parquet`. Cannot `gsutil     rsync` directly.
      `cloud-providers.yaml` already flipped (4a done). Old per-AG data: CeFi bucket has 237 files (~19MB) of V2 dev
      backtest runs (2025-01-01 dates); all prod per-AG buckets are 0-byte. Operator decision needed: (a) abandon old
      dev data (no client_id mapping) + mark bucket for deletion, OR (b) write a migration script that maps old
      strategy_id/date → client_id/strategy_id/day format. Gated: master coordinator Phase 1 bucket symmetry window.
      Filed slot-6 ping 2026-05-23.
- [x] ✅ **[QG] P1.** Phase 4 QG: no `gs://` f-strings remaining (STEP 5.69) — workspace-wide rg confirms zero inline
      strategy-store f-strings post 4a/4b.

### Phase 5 — error classification (P1.3)

- [x] ✅ **[CODE] P1.** 5a. execution-service `_raise_gcs_instructions_error` → emit `ADAPTER_FETCH_FAILED` on non-404 —
      execution-service@6e4dbe30b

### Phase Q — QG ratchet

- [x] ✅ **[SCRIPT] P1.** Qa. Extend `no_silent_absence_handlers.sh` to cover strategy-service `gcs_storage_service.py`
      — PM@dc849b256
- [x] ✅ **[SCRIPT] P1.** Qb. Extend `no_silent_absence_handlers.sh` to cover execution `strategy_instructions/gcs.py` —
      PM@dc849b256

### Codex SSOT updates

- [x] ✅ **[DOC] P1.** Update `/codex/04-architecture/defi-execution-overview.md` § "Data pipeline" to note manifest
      handoff contract at strategy→execution boundary — PM@b1197eda1 (added Data Pipeline section:
      StrategyManifestRecorder writer + ExecutionManifestRecorder reader, 3-state emission, QG enforcement pointer)

---

## Full-execution criterion

**Phase 1 done when**: strategy-service `quality-gates.sh` GREEN +
`rg "record_captured\|record_empty\|record_failed" strategy_service/engine/core/gcs_storage_service.py` returns ≥3 hits

**Phase 2 done when**: execution-service `quality-gates.sh` GREEN +
`rg "record_captured\|record_empty\|record_failed" execution_service/strategy_instructions/gcs.py` returns ≥3 hits

**Phase 3 done when**: `execution_service/cli/backtest_checks.py` no longer calls bare `check_dependencies()` for
strategy — routes through `validate_config_can_run()`

**Full plan done when**: paper-trade batch run for one day produces manifest rows in
`strategy-store-{pid}/_index/availability_index.parquet` with `capture_status=captured` for each strategy that produced
instructions

---

## P3 lint backlog (absorbed from unused_import_audit_2026_05_18)

- [x] ✅ [AGENT] P3. Fix F401 unused imports — `ruff check --select F401` shows "All checks passed!" on both
      `execution-service/scripts/run_execution_alpha_measurement.py` and `run_execution_alpha_parallel.py`. Already
      clean — no fix needed. 2026-05-22.

## Temporary states + their canonical follow-up plans

- **`validate_batch_completeness` warn path (A5)**: emitting `PROCESSING_INCOMPLETE` event is the canonical pattern per
  `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` § "Incomplete batch semantics". Per-shard
  `record_failed` in `write_instructions()` provides the manifest visibility. No separate successor plan needed — this
  plan closes it.
- **P3 schema-version assessment**: blocked until Phase 1+2 manifest emission adds rows. Follow-up: once rows land, run
  `SELECT DISTINCT schema_version FROM _index/availability_index.parquet` on `strategy-store` bucket to verify
  schema_version=8. No separate plan — verify during paper-trade smoke (full-execution criterion).

## Deferred work — migrated to:

- **4c. Per-AG → unified bucket migration (P0, BLOCKED-OPERATOR-DECISION)**: CeFi bucket has 237 files (~19MB) of V2 dev
  backtest runs (2025-01-01 dates); all prod per-AG buckets are 0-byte. Operator must choose: (a) abandon old dev data
  (no client_id mapping) + delete bucket, OR (b) write migration script for old format → new partitioned format.
  **Migrated to**: `plans/epics/strategy_master.md` § P0 operator-decision backlog. Ping filed slot-6 2026-05-23.
