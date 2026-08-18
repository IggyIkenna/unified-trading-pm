---
doc_type: issue
title: execution-service pydantic extra_forbidden config-validation failure blocks a GCS-compliance fix
summary: >-
  `scripts/run_execution_alpha_measurement.py`'s GCS-compliance fix (raw `google.cloud.storage` -> UTL's
  `get_storage_client().upload_bytes()`, one of the 13 Category-2 files from the fleet-wide GCS-client triage) is
  fixed, ruff/basedpyright clean, and verified -- sitting as an uncommitted working-tree edit in this repo,
  ship-blocked by a pre-existing, unrelated pydantic-settings config-validation failure confirmed via `git
  stash`+rerun before this session touched anything. A settings model rejects real env keys under `extra="forbid"`
  (`market_data_gcs_bucket` / `instruments_store_gcs_bucket` / `unified_cloud_services_gcs_bucket`), breaking
  `tests/unit/test_handler_registry.py` + `tests/unit/v2/test_policy_resolver.py` (11 tests) and
  `tests/unit/test_gcs_live_data_sink.py` + `tests/unit/test_defi_data_loader_coverage.py` (2 more). This is the
  identical failure CLASS (different fields) as strategy-service's `StrategyDomainConfig(extra="forbid")` issue,
  already tracked as a P3 AGENT todo in `/plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` --
  two independent repos hitting the same `extra_forbidden`/pydantic-settings signature within one session, worth a
  human noticing the cross-repo pattern even though the fix will likely be per-repo. NOT fixed here -- deliberately
  out of scope for this tracking pass; needs its own root-cause investigation.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [gcs, config-validation, pydantic, extra-forbidden, ship-blocked, cross-repo-pattern]
related:
  [
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: infrastructure_master
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
    execution-service/scripts/run_execution_alpha_measurement.py,
    execution-service/tests/unit/test_handler_registry.py,
    execution-service/tests/unit/v2/test_policy_resolver.py,
  ]
supersedes:
superseded_by:
source:
  [
    "Surfaced 2026-08-18 during the fleet-wide GCS-client Category-2 remediation session
    (utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md) -- the fix for
    run_execution_alpha_measurement.py was verified correct + green on ruff/basedpyright, but the repo's own
    test suite was already red on HEAD before this session touched anything (confirmed via `git stash`+rerun),
    so it could not be shipped through quality-gates.sh.",
  ]
locked_by:
locked_since:
---

# execution-service pydantic `extra_forbidden` config-validation failure blocks a GCS-compliance fix

## What's blocked

`scripts/run_execution_alpha_measurement.py` has a real, verified, uncommitted fix sitting in this repo's working
tree: its `_write_output()` GCS-write branch converted a local `from google.cloud import storage as gcs` raw-SDK
client to UTL's `get_storage_client(project_id=...).upload_bytes(...)` -- part of the same fleet-wide Category-2
raw-SDK-import remediation documented in
`/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md` § "Category-2
remediation results" (5/13 fixed-but-ship-blocked). Confirmed still present via `git diff --
scripts/run_execution_alpha_measurement.py` (2026-08-18, this tracking session) -- not lost, not yet committed.

## The blocking failure

A pydantic-settings config model in this repo rejects real env keys under `extra="forbid"` -- specifically
`market_data_gcs_bucket`, `instruments_store_gcs_bucket`, `unified_cloud_services_gcs_bucket` (fields the model
doesn't declare, but real config/tests pass them). Breaks:

- `tests/unit/test_handler_registry.py`
- `tests/unit/v2/test_policy_resolver.py`
  (11 tests total across these two)
- `tests/unit/test_gcs_live_data_sink.py`
- `tests/unit/test_defi_data_loader_coverage.py`
  (2 more tests)

Pre-existing and unrelated to the GCS-client fix -- confirmed red on a clean HEAD via `git stash`+rerun by the
session that found it, before touching `run_execution_alpha_measurement.py`.

## Same failure class as a strategy-service issue, already tracked elsewhere

`strategy-service`'s `StrategyDomainConfig(extra="forbid")` breaks `TestStrategySafeFieldAllowList` the identical
way (different specific fields, identical `extra_forbidden`/pydantic-settings root-cause shape) -- already tracked
as:

```
- [ ] [AGENT] P3. Fix `StrategyDomainConfig` (`extra="forbid"`) breaking `TestStrategySafeFieldAllowList` ...
```

in `/plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` (sourced from
`/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`). Two independent repos
hitting the identical failure signature within the same investigation session is worth a human noticing the
cross-repo pattern (shared config base class? shared `.env.example` drift? a fleet-wide default that recently
flipped to `extra="forbid"`?) even though the concrete remediation will likely stay per-repo (different fields,
different call sites). Cross-linked both directions -- see batch15's `related:` should a future session want to add
this doc there too.

## Explicitly out of scope for this tracking doc

Do not fix the pydantic config issue here -- different root cause from the GCS-client bug this doc's source
investigation was about, needs its own proper investigation into why these three GCS-bucket-name fields aren't
declared on the model (or why `extra="forbid"` was chosen over `"ignore"` here). Once diagnosed and fixed, commit
`scripts/run_execution_alpha_measurement.py`'s already-verified GCS fix alongside it (`git diff` will still show it
sitting there, assuming no other session has since started/lost it) -- don't lose it re-diagnosing the config bug.

## Progress Log

- **2026-08-18**: filed while tracking 5 already-fixed, uncommitted GCS-compliance changes across 4 repos (see
  `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md` § "Category-2
  remediation results"). Verified the GCS fix is still sitting uncommitted and correct in the working tree.
  Confirmed via corpus grep this failure class was NOT tracked anywhere before this doc. Not investigated/fixed --
  `assigned_vm: NA` pending root-cause triage; low estimate reflects "probably a one-line `extra="ignore"` swap
  once someone looks," mirroring the strategy-service twin's own estimate shape, but unconfirmed.
