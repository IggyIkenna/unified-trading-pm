---
doc_type: issue
title: client-reporting-api invoice-viewing test failures (4) block seed_demo_client's GCS-compliance fix
summary: >-
  `scripts/seed_demo_client.py`'s GCS-compliance fix (raw `google.cloud.storage` -> UTL's
  `get_storage_client().upload_bytes()`, one of the 13 Category-2 files from the fleet-wide GCS-client triage) is
  fixed, ruff/basedpyright clean, and verified -- sitting as an uncommitted working-tree edit in this repo,
  ship-blocked by 4 pre-existing, unrelated failures in `tests/unit/test_invoice_viewing_transitions_analytics.py`
  (expects HTTP 404, gets a different status), confirmed via `git stash`+rerun before this session touched
  anything. Not tracked anywhere in the corpus before this doc. A broader, pre-existing todo
  (`/plans/active/repo_scripts_governance_audit_2026_06_18.md`'s Phase-1 "DEPRECATE remediation" item) already
  tracks fixing `seed_demo_client.py`'s cloud-discipline gap as part of a ~10-script cohort -- this GCS fix
  satisfies that item FOR THIS FILE once shipped, but that item doesn't track or explain these specific blocking
  test failures, which are a different, unrelated bug.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api]
scope: [engineer]
tags: [gcs, test-failure, ship-blocked, invoices]
related:
  [
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
    /plans/active/repo_scripts_governance_audit_2026_06_18.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
assigned_role: infra
effort: low
resolved_by:
drift_direction: advance-code
depends_on:
context_scope:
  [
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
    client-reporting-api/scripts/seed_demo_client.py,
    client-reporting-api/tests/unit/test_invoice_viewing_transitions_analytics.py,
  ]
supersedes:
superseded_by:
source:
  [
    "Surfaced 2026-08-18 during the fleet-wide GCS-client Category-2 remediation session
    (utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md) -- the fix for seed_demo_client.py was
    verified correct + green on ruff/basedpyright, but the repo's own test suite was already red on HEAD before
    this session touched anything (confirmed via `git stash`+rerun, 4 failures in
    test_invoice_viewing_transitions_analytics.py), so it could not be shipped through quality-gates.sh.",
  ]
locked_by:
locked_since:
---

# client-reporting-api invoice-viewing test failures block `seed_demo_client.py`'s GCS-compliance fix

## What's blocked

`scripts/seed_demo_client.py`'s `_persist_treasury_config()` has a real, verified, uncommitted fix sitting in this
repo's working tree: its raw `from google.cloud import storage` client (the file's own docstring previously read
"Uses google-cloud-storage directly (no extra deps required)") is now converted to UTL's
`get_storage_client().upload_bytes(...)` -- part of the same fleet-wide Category-2 raw-SDK-import remediation
documented in `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md` §
"Category-2 remediation results" (5/13 fixed-but-ship-blocked). Confirmed still present via `git diff --
scripts/seed_demo_client.py` (2026-08-18, this tracking session) -- not lost, not yet committed.

## The blocking failure

4 pre-existing failures in `tests/unit/test_invoice_viewing_transitions_analytics.py`: the tests expect an HTTP 404
response and get a different status instead. Unrelated to GCS/cloud-storage in any way -- confirmed red on a clean
HEAD via `git stash`+rerun by the session that found it, before touching `seed_demo_client.py`. Not independently
re-diagnosed by this tracking session (out of scope, see below); the exact 4 test names + the actual status code
returned were not re-captured here -- a future session picking this up should re-run the suite fresh rather than
trust this doc's characterization blindly.

## Relationship to the existing broader cloud-discipline todo

`/plans/active/repo_scripts_governance_audit_2026_06_18.md` already carries an open P2 todo (Phase 1, "DEPRECATE
remediation"):

```
- [ ] [AUDIT] P2. **DEPRECATE remediation** -- fix the ~10 KEEP/PROMOTE scripts carrying the cloud-discipline gap
      (UCI `get_storage_client`/`gcs_*` + `resolve_bucket_name` + `GCP_PROJECT_ID` via `UnifiedCloudConfig`):
      strategy-service DeFi tracers, `seed_demo_client`, `run_client_reporting_cutover`, ...
```

This GCS-compliance fix, once committed, satisfies that item's `seed_demo_client` sub-case specifically (the
broader item still covers ~9 other scripts across other repos). It does NOT cover or explain the invoice-viewing
test failures blocking the commit -- those are a separate, unrelated bug this doc tracks instead. Not editing that
todo's checkbox here (it's still open for the other ~9 scripts); a future session that finishes the whole cohort
should flip it citing all the shipped commits, this one included.

## Explicitly out of scope for this tracking doc

Do not fix the invoice-viewing test failures here -- unrelated to the GCS-client bug this doc's source
investigation was about, needs its own proper investigation into what changed the expected status code (a route
behavior change never reflected in the tests, or a test written against a since-changed contract). Once diagnosed
and fixed, commit `scripts/seed_demo_client.py`'s already-verified GCS fix alongside it (`git diff` will still show
it sitting there, assuming no other session has since started/lost it) -- don't lose it re-diagnosing the test
failures.

## Progress Log

- **2026-08-18**: filed while tracking 5 already-fixed, uncommitted GCS-compliance changes across 4 repos (see
  `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md` § "Category-2
  remediation results"). Verified the GCS fix is still sitting uncommitted and correct in the working tree.
  Confirmed via corpus grep these 4 test failures were NOT tracked anywhere before this doc; found the related
  (but not overlapping) broader cloud-discipline todo in `repo_scripts_governance_audit_2026_06_18.md` and
  cross-linked it. Not investigated/fixed -- `assigned_vm: NA` pending root-cause triage.
