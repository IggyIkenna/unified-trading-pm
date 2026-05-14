---
title: "deployment-api: 13 test failures — SHARD_AXIS_MATRIX UAC alignment drift"
created: 2026-05-14
author: harsh-slot-5
source:
  - deployment-api Phase 0 C901 lint sweep (slot 5, 2026-05-14)
locked_by: live-defi-rollout
locked_since: 2026-05-14
severity: P1
suggested_owner: UAC + deployment-api (cross-repo; needs UAC changes first)
---

## What I found

During the Phase 0 C901 lint sweep (`deployment-api@3040a1b`), 13 tests fail in a stable pre-existing manner (confirmed
via `git stash` before/after to isolate from my changes):

```
FAILED tests/unit/test_data_status_drilldown_axis_depth.py — 8 failures
FAILED tests/unit/test_data_status_axis_matrix.py — 1 failure
FAILED tests/unit/test_data_status_hierarchical.py — 1 failure
FAILED tests/unit/test_feature_group_breakdown_uac.py — 3 failures
```

Root cause: `data_status_drilldown.py` calls `SHARD_AXIS_MATRIX` from UAC to resolve drilldown axes per
`(service, asset_group)`. The tests assert specific axis shapes that no longer match the current UAC `SHARD_AXIS_MATRIX`
registry state. The registry has been updated (new services, renamed axes, added asset_groups) but `deployment-api`
hasn't been re-aligned.

Specific patterns of drift (from test output):

- `test_data_status_drilldown_axis_depth.py` — 8 `(service, asset_group)` combinations expected specific drilldown depth
  that doesn't match current UAC `SHARD_AXIS_MATRIX` entries.
- `test_data_status_axis_matrix.py` — 1 assertion on matrix shape/keys mismatch.
- `test_data_status_hierarchical.py` — 1 assertion on hierarchical axis ordering.
- `test_feature_group_breakdown_uac.py` — 3 assertions on feature_group breakdown columns that reference UAC constants
  that have been renamed or restructured.

This is a cross-repo alignment issue: UAC `SHARD_AXIS_MATRIX` is the canonical source (per shard-granularity SSOT in
CLAUDE.md) and deployment-api must be a consumer of it. Fixing requires:

1. Reading current UAC `SHARD_AXIS_MATRIX` to see actual shape.
2. Updating deployment-api test fixtures OR the `data_status_drilldown.py` lookup code to match.
3. Running QG to verify all 13 tests pass.

These failures existed BEFORE my C901 lint sweep (verified by `git stash` isolation).

## Why it matters

The deployment-ui "Data Status" drilldown panel uses these endpoints to show hierarchical data status. If
`SHARD_AXIS_MATRIX` mapping is stale, the drilldown silently shows wrong axis columns or returns wrong depth — a data
correctness issue for operators using the UI to verify manifest health.

Severity P1 (not P0) because: drilldown falls back gracefully; manifest data itself is not corrupted. But the UI shows
misleading depth/axis hierarchy which operators rely on for deployment decisions.

## Recommended decision

**Owner**: UAC team (read what the current `SHARD_AXIS_MATRIX` looks like) + deployment-api slot.

Steps:

1. UAC owner: confirm `SHARD_AXIS_MATRIX` current keys/shape (it may have been updated in a recent session without
   deployment-api sync).
2. deployment-api slot: re-read `data_status_drilldown.py` lookup code + update test fixtures to match current UAC
   shape. ~1-2 hours once UAC shape is confirmed.
3. QG clean (all 13 pass).
4. Commit + push + flip plan checkbox in `deployment_and_qg_strategy_implementation_2026_05_13.md` § Cluster D (or file
   as sub-todo there if appropriate).

**Do NOT** patch the tests to match stale UAC state. Fix the alignment.

## Resolution (2026-05-14 ikenna-slot-8)

- [x] Fixed — deployment-api@40f7769

Root cause confirmed: UAC consolidated all features-\* sub-family service names (`features-delta-one-service`,
`features-volatility-service`, `features-onchain-service`, `features-sports-service`) into `features-service` in
`data_status_axis_matrix.py` and `EXPECTED_FEATURE_GROUPS_BY_SERVICE`. Tests were using stale sub-family names.

Fixes applied to 4 test files:

- `test_drilldown_axis_depth_matches_ssot.py`: 8 stale sub-family pairs → features-service equivalents
- `test_data_status_axis_matrix.py`: features-sports-service → features-service
- `test_data_status_hierarchical.py`: features-onchain-service → features-service in parametrize
- `test_feature_group_breakdown_uac.py`: all features-onchain-service refs → features-service; len(out) == 12 → dynamic
  lookup from UAC constant (now 83 feature_groups)

All 13 previously-failing tests now pass.
