---
doc_type: issue
title: >
  instruments-service QG RED — reconcile_lending_indices_phantom.py _audit_captured_rows() gained a required
  client=StorageClient first param (commit 0d2ea24f, 2026-07-13) but its 3 unit tests were never updated, so
  quality-gates.sh fails repo-wide (blocks the green-tree ship gate for every slot working this repo)
summary:
  "instruments-service::scripts/reconcile_lending_indices_phantom.py::_audit_captured_rows() was given a new required
  first parameter `client: StorageClient` in commit 0d2ea24fb (2026-07-13, bundled into an unrelated sports
  TEAMS/STANDINGS fix) but tests/scripts/test_reconcile_lending_indices_phantom.py's 3 call sites
  (test_phantom_detection_dry_run_no_writes, test_real_capture_left_alone,
  test_audit_translates_uppercase_venue_to_lowercase_slug_for_gcs_prefix) still call it with the old 4-arg signature
  (bucket, df, captured_idx, workers=1), producing `TypeError: _audit_captured_rows() missing 1 required positional
  argument: 'captured_idx'`. Verified byte-identical on a clean tree at LDR HEAD (stash-and-rerun) — this is NOT caused
  by any in-flight sports work; it fails `bash scripts/quality-gates.sh` for EVERY slot touching this repo since the
  gate requires a full green run before quickmerge writes the sentinel."
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [quality-gates, regression, test-drift, lending-indices, repo-blocker]
related: []
created: 2026-07-14
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
source: [slot-12 data_engineering worker, discovered while shipping sports_p2_history_apifootball_2015_to_present-005]
resolved_by: slot-4 data_engineering (instruments-service@4d8dfb8e, 2026-07-14)
locked_by:
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# instruments-service QG RED — lending-indices phantom-audit signature drift

> **NOTIFY-OPERATOR (repo-wide ship blocker).** `bash scripts/quality-gates.sh` for `instruments-service` currently
> exits 1 on a clean `live-defi-rollout` tree (verified via stash-and-rerun, 2026-07-14) — 3 tests in
> `tests/scripts/test_reconcile_lending_indices_phantom.py` call `_audit_captured_rows()` with a stale 4-arg signature.
> Since QG must be FULLY green before `quickmerge --agent` writes its sentinel (no `--skip-*` carve-out permitted), this
> blocks quickmerge for EVERY slot shipping ANY instruments-service change, not just this one.

## What I found

`scripts/reconcile_lending_indices_phantom.py::_audit_captured_rows()` signature (current, at
`scripts/reconcile_lending_indices_phantom.py:156-162`):

```python
def _audit_captured_rows(
    client: StorageClient,
    bucket_name: str,
    df: pd.DataFrame,
    captured_idx: pd.Index[int],
    workers: int,
) -> dict[int, tuple[bool, str]]:
```

`git blame` shows the `client: StorageClient` first param was added by commit `0d2ea24fb` (2026-07-13, slot-3,
`fix(sports): api_football TEAMS/STANDINGS — widen writer from 33-league Prediction-tier filter to full 94-league source coverage`)
— an unrelated sports commit that bundled in this DeFi-lending-indices signature change without updating its tests.

The 3 failing call sites (`tests/scripts/test_reconcile_lending_indices_phantom.py`) still call the OLD 4-arg form:

```python
audit = _mod._audit_captured_rows(bucket, df, df.index, workers=1)
```

producing on every run:

```
TypeError: _audit_captured_rows() missing 1 required positional argument: 'captured_idx'
```

Failing tests:

- `test_phantom_detection_dry_run_no_writes` (line 110)
- `test_real_capture_left_alone` (line 138)
- `test_audit_translates_uppercase_venue_to_lowercase_slug_for_gcs_prefix` (line 339)

**Verified pre-existing, not caused by my in-flight work**: stashed my sports_p2_history_apifootball-005 diff (4 files,
sports-only), re-ran `PYTEST_UNIT_DIR="tests/" bash scripts/quality-gates.sh` on the clean tree — byte-identical 3
failures, same error message. Restored my stash afterward.

## Why it matters

- `quickmerge --agent` refuses to ship (sentinel not written) while `quality-gates.sh` exits non-zero, and the HARD RULE
  forbids `--skip-*` carve-outs — so this red blocks EVERY slot's instruments-service ship, not just lending/DeFi work.
- The underlying production code path (`_audit_captured_rows` itself, called from `main()` at
  `scripts/reconcile_lending_indices_phantom.py:384` with the correct 5-arg form) is NOT broken — only the tests
  drifted. This is pure test debt, not a live data-correctness bug.

## Recommended decision

Fix the 3 test call sites to pass a mocked `client: StorageClient` as the first positional arg (matching the production
caller's usage at line 384: `_audit_captured_rows(client, bucket_name, df, captured_idx, args.workers)`). A
`MagicMock()`/appropriately-scoped fake `StorageClient` should suffice given `_audit_captured_rows` only uses `client`
for GCS blob-existence checks inside its per-row loop (`scripts/reconcile_lending_indices_phantom.py:171+`).

## Todos

- [x] ✅ [SCRIPT] P0. Fix `tests/scripts/test_reconcile_lending_indices_phantom.py`'s 3 stale `_audit_captured_rows()`
      call sites to pass a `client` arg (mocked `StorageClient`) matching the current 5-param production signature;
      re-run `bash scripts/quality-gates.sh` for instruments-service to confirm green. (repo: instruments-service) —
      instruments-service@4d8dfb8e

## Progress log

- 2026-07-14: Filed by slot-12 (data_engineering) while shipping `sports_p2_history_apifootball_2015_to_present-005`
  (the GW enrichment false-empty manifest fix). Declaring a repo-blocker (`qg_red`) so the backend polls for green and I
  resume shipping the moment this clears, per RULES.md § 4b.
- 2026-07-14: Fixed by slot-4 (data_engineering) — `instruments-service@4d8dfb8e`. Root cause: the mock
  `_mock_bucket_with_blobs()` helper's inner `_list_blobs()` didn't accept the `bucket_name` positional param that the
  real `StorageClient.list_blobs(bucket_name, prefix=..., max_results=...)` signature requires, so passing a mock client
  positionally at the 3 call sites needed that helper fixed too. `quality-gates.sh` green (exit 0), sentinel written at
  `03f53b80`, shipped via quickmerge.
