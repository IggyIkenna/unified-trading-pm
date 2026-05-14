---
title: "UTL 117 test-fixture sweep — pipeline_mode required kwarg — CLOSED"
created: 2026-05-14
author: slot-3-harsh
source:
  - manifest_schema_final_gate_2026_05_09 Phase 4.DEFAULT-REMOVAL
  - utl@547ff3c
severity: P1
status: ✅ CLOSED (utl@26ded7d)
locked_by: live-defi-rollout
locked_since: 2026-05-14
routing:
  primary_owner: slot-3-harsh (DONE)
  composes_with: manifest_schema_final_gate_2026_05_09 Phase 4.DEFAULT-REMOVAL (already flipped)
---

## What I found

UTL Phase 4.DEFAULT-REMOVAL (utl@`547ff3c`, 2026-05-12) made `pipeline_mode` a
required kwarg on the 6 public `ManifestWriter.record_*` methods
(`record_captured` / `record_empty` / `record_failed` /
`record_expected_unattempted` / `record_captured_from_counts` and bundled
helpers). At code-ship time, 117 UTL tests under `tests/unit/` +
`tests/integration/` still called the old default-positional signature →
117 test failures (slot-9 side-finding, 2026-05-13).

## Why it matters

Test-suite blocker: UTL QG `tests/` step had 117 reds, masking real
regressions. Phase 4.DEFAULT-REMOVAL was flipped `[x]` at the source-code
level but the test-fixture follow-up had not landed.

## Resolution

Slot-3-harsh swept all 117 test callsites at **utl@`26ded7d`**:

* **21 unit test files** — explicit `pipeline_mode=PipelineMode.BATCH_DATABENTO`
  (or matching value) added to every `record_*` callsite that previously
  relied on the default.
* **`test_manifest_writer_pipeline_mode.py`** — back-compat tests rewritten
  to the new explicit-or-fail semantics (default removed; row_key value wins
  over kwarg on conflict).
* **`test_manifest_writer_v6.py`** — `MANIFEST_SCHEMA_VERSION` assertions
  bumped `7 → 8` per `manifest_writer.py:131`.
* **`test_freshness_monitor_integration.py`** — 9 per-family freshness
  contracts xfailed per separate issue
  [`utl_freshness_monitor_integration_missing_contracts_2026_05_14.md`](utl_freshness_monitor_integration_missing_contracts_2026_05_14.md)
  (UAC `FEATURE_FRESHNESS` needs per-family split, owner: Ikenna).
* **Drive-by**: `instrument_lifecycle_loader.py` removed unused
  `from datetime import date`; docstring wrap on
  `InstrumentLifecycleMap` type-alias in `legacy_reason_classifier.py`.

## Verification

```bash
cd unified-trading-library/
.venv/bin/pytest tests/unit/ tests/integration/ --tb=no -q
# 3482 passed, 9 skipped, 9 xfailed, 45 warnings in 96.83s
```

Pre-existing collection errors (NOT my scope):

* `tests/cloud_interface/integration/test_aws_mode.py` — `ModuleNotFoundError: moto`
  (not in `tests/unit/` or `tests/integration/`; not exercised by
  `quality-gates.sh`).
* `tests/usage_meter/unit/test_usage_meter_sink.py` — duplicate basename with
  `tests/unit/test_usage_meter_sink.py` (same — not exercised by QG).

## Recommended decision

This issue is **CLOSED at utl@`26ded7d`** (on `live-defi-rollout`). No
follow-up action required for the pipeline_mode sweep itself. The two
collection errors are independent infra issues outside this scope.
