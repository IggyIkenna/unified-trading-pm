---
title: client-reporting-api test coverage below 70% floor
created: 2026-05-14
author: harsh-slot-7
source:
  - QG step 3/6 run during Phase 0 B008 sweep (2026-05-14)
severity: P2
suggested_owner: "operator or next slot assigned to client-reporting-api"
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

# client-reporting-api test coverage below 70% floor

## What I found

Running `bash scripts/quality-gates.sh` in `client-reporting-api` produces:

```
FAIL Required test coverage of 70% not reached. Total coverage: 64.06%
358 passed, 8 skipped
```

8 tests skipped in `tests/unit/test_core_coverage.py` with reason "No backfilled client data present".
These skips reduce effective coverage below the 70% floor. The 64% figure is pre-existing (workspace-manifest.json
showed `ci_status: LOCAL_PASS` before my lint sweep, suggesting coverage was near the floor but
may have dipped with recent additions to service code without matching tests).

## Why it matters

QG step 3/6 fails → `bash scripts/quality-gates.sh` exits non-zero → repo blocks quickmerge pipeline.
Other slots that run QG on this repo will see coverage FAILING.

## Recommended decision

Two options:
1. **Add unit tests** for untested paths in new attribution/invoice routes (estimated 2-4h of test work).
2. **Lower the coverage floor** for this repo to 65% temporarily via `pyproject.toml [tool.coverage.report] fail_under = 65`
   with a plan todo to raise it back once the backfill data tests can run.

Option 2 is the faster unblock; option 1 is the correct long-term fix.

## Note on skipped tests

The 8 skipped tests in `test_core_coverage.py` require real backfilled client data (GCS parquets from
live environment). They're correctly marked `skip` in dev without data. These tests would cover significant
additional surface if run in integration mode.
