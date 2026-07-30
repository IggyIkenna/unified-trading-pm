---
doc_type: issue
title:
  "test_sports_catalog_reader_timeout.py's stall-timeout test flakes under shared-host QG contention (39.2s vs 35s
  threshold)"
summary: >-
  market-tick-data-service's `test_timeout_skips_stalled_shard_and_continues` asserts the sports catalog reader's
  per-blob stall guard fires and completes within `stall_secs=35` wall-clock seconds. Under fleet-wide shared-host
  contention (concurrent quality-gates.sh runs from other slots) the full 7245-item suite run measured 39.2s (assert
  failed); re-run in isolation immediately after, on the SAME tree, measured 30.37s (passed). Same class as
  `adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md` — a fixed wall-clock threshold
  assertion racing against variable host load, not a real regression.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [quality-gates, flaky-test, timeout, sports-catalog-reader, shared-host-contention]
related: [/plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
  "market-tick-data-service@4aaeab69 (+ 43017f64, 5bf8a3c7) — a stronger fix than requested (monkeypatch the real
  _BLOB_TIMEOUT_SECS cap down instead of widening the margin, removing host-load sensitivity entirely); re-verified
  2026-07-29 batch closeout pass, 2 passed in 0.64s"
source: >-
  measured 2026-07-27 while shipping sports_error_reason_free_text_census_2026_07_27.py
  (sports_satellite_ao_dispatch_batch3_2026_07_25.md todo 10, an unrelated new-script-only diff). quickmerge's
  full-suite re-gate (7245 items) failed at this one test; re-running the SAME test standalone on the SAME tree
  immediately after passed (30.37s < 35s threshold, vs 39.2s during the contended full-suite run).
---

> **✅ ARCHIVED 2026-07-29** (batch closeout pass, market-tick-data-service docs batch). Already shipped by another
> session — `market-tick-data-service@4aaeab69` monkeypatches `_BLOB_TIMEOUT_SECS` down for the test instead of just
> widening the wall-clock margin, which removes the host-load sensitivity entirely (stronger than this doc's own
> recommendation). Re-verified: `2 passed in 0.64s`.

# test_sports_catalog_reader_timeout.py flakes under fleet-wide shared-host contention

## What was found

Verified pre-existing/unrelated per the RULES.md §4b protocol before filing: `git log` confirms the diff being shipped
(a new, isolated script file, `market-tick-data-service/scripts/sports_error_reason_free_text_census_2026_07_27.py`)
never touches `market_tick_data_service/engine/sports_catalog_reader.py` or its test file. The failing assertion:

```
tests/unit/engine/test_sports_catalog_reader_timeout.py:120: in test_timeout_skips_stalled_shard_and_continues
    assert elapsed < stall_secs, (...)
E   AssertionError: list_instruments blocked for 39.2s >= stall_secs=35 — the per-blob timeout did not fire
```

Re-running the identical test on the identical (uncommitted-diff) tree standalone, immediately after, passed:
`1 passed in 30.37s`. The gap (39.2s vs 30.37s, both against a `stall_secs=35` fixed threshold) is host-load contention
(the full 7245-item xdist suite was running concurrently with — per this session's own observation — another slot's full
`market-data-processing-service` quality-gates.sh run finishing around the same time), not a code defect. The test
measures a real 30-second `asyncio.sleep`-backed stall + a bounded timeout guard, so its margin against the 35s
assertion threshold is only ~5s — too tight to survive shared-host CPU/IO contention, same root-cause class as the
sibling `adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md` finding.

## Why it matters

A flaky red on an unrelated diff burns a re-run cycle and risks a worker mis-diagnosing a real regression, or (worse) an
agent "fixing" a phantom bug in the timeout-guard code that was never actually broken.

## Recommended decision

- [x] ✅ [CODE] P3. **DONE — already shipped, verified 2026-07-29.** `market-tick-data-service@4aaeab69` ("test:
      monkeypatch sports catalog reader blob timeout instead of real sleep(35)") monkeypatches
      `sports_catalog_reader_module._BLOB_TIMEOUT_SECS` down to `0.1` for the test and stalls for
      `patched_timeout_secs + 8` — genuinely fast AND host-load-independent, not just a wider margin. Re-ran:
      `2 passed in 0.64s`. Repo: market-tick-data-service.
