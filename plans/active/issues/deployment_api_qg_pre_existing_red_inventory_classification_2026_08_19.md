---
doc_type: issue
title: >-
  `deployment-api`'s full `quality-gates.sh` is RED on 3 pre-existing `test_route_deployments_inventory.py` failures —
  blocks shipping unrelated work via the mandated Pass-1-green quickmerge flow
summary: >-
  While shipping an unrelated fix (venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md's open aggregate-budget
  BACKEND todo), Pass-1 `quality-gates.sh` failed 3x in a row (both BEFORE and AFTER my change, byte-identical
  failure set both times) on 3 tests in `tests/unit/test_route_deployments_inventory.py`. Confirmed pre-existing and
  unrelated via a clean-tree comparison (RULES.md §4b protocol). Two of the three are a DETERMINISTIC assertion
  mismatch (not the known socket/timeout flakiness the existing `fleet_wide_qg_self_hosted_runner_capacity_crisis_
  2026_07_27.md` doc already tracks for the third test) — a distinct, seemingly undiagnosed root cause.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [qg-red, deployment-api, deployments-inventory, test-failure, pre-existing]
related:
  [
    /plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
  ]
created: "2026-08-19"
author: backend_engineer-worker-slot7
parent_epic: security_and_cross_cutting_master
resolved_by:
locked_by:
locked_since:
source: >-
  Discovered as a repo-blocker while shipping venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md's open BACKEND
  P0 todo (row-group parallel decode) — RULES.md §4b qg_red protocol.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: []
context_scope:
  [
    deployment-api/tests/unit/test_route_deployments_inventory.py,
    deployment-api/deployment_api/routes/deployments_inventory/_classification.py,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
  ]
---

# `deployment-api` QG red: pre-existing inventory-classification test failures

## What I found

Running `bash scripts/quality-gates.sh` (full, no skip flags) on `deployment-api` at `origin/live-defi-rollout` HEAD
(`a69dad3`, my own unrelated commit) failed 3x in a row on the same 3 tests in
`tests/unit/test_route_deployments_inventory.py`. Verified pre-existing and unrelated to my change per RULES.md §4b:
reverted my diff to the parent commit (`a69dad3~1`), re-ran full `quality-gates.sh` — **byte-identical 3-test failure
set** (`3 failed, 5438 passed` pre-fix vs `3 failed, 5439 passed` post-fix, the +1 being my own new test).

Two distinct failure mechanisms, not one:

1. **`test_build_inventory_classifies_vms_and_jobs`** (line 130) and
   **`test_build_inventory_launched_by_provenance_for_cloud_run_jobs`** (line 479) — DETERMINISTIC assertion
   mismatches, reproduced identically on every run, not a timeout/socket symptom:
   - `assert 'prd-manifest-consolidator' == 'manifest-consolidator'` — the classifier is returning the job name WITH
     its `prd-` env prefix still attached, where the test expects it stripped.
   - `assert 'adhoc' == 'deployment-api'` — the `launched_by` provenance classifier is returning `adhoc` where the
     test expects `deployment-api` for the same `prd-manifest-consolidator-cefi` fixture.
   - Classification logic lives in `deployment_api/routes/deployments_inventory/_classification.py`. Its git history
     shows no recent commit (`git log` — last 2 touches are `95a7a19`/`75584a8`, both older, a managed-by-label
     feature and a file-size-cap split, neither obviously related) — this does NOT look like a fresh regression from
     a nearby commit. Candidate root causes NOT yet investigated: an env-prefix-stripping helper (UAC or local) that
     changed behavior without this module/its tests being updated, or a genuinely stale test fixture vs an
     intentional naming-convention change elsewhere in the fleet. Root cause not established — flagging rather than
     guessing further, per this workspace's measurement-claims discipline.
2. **`test_inventory_route_live_path_mocks_registry_and_cloud_run`** (line 1406) — `assert []` (empty). Captured
   stderr shows the AWS EC2/Batch/ECS/Lambda census calls degrading to empty because
   `pytest_socket` blocked an outbound `socket.socket.connect()` (e.g. `"A test tried to use socket.socket.connect()
   with host \"52.195.202.156\"..."`). This DOES match the already-tracked pattern in
   `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (same test name, same "mocked path degrades to
   an honest-empty result under contention" signature) — but that doc's own entry for this test describes a
   **timeout** (`Failed: Timeout (>150.0s)`) clearing on a clean local retest, whereas here the SAME test fails
   **every single run** (3/3) with a blocked-socket warning, not a timeout. Whether this is the same underlying
   mechanism (host contention making a normally-mocked path attempt a real connect) or a distinct regression in the
   AWS census mocking setup is not established here — flagging for whoever picks this up to correlate with that
   doc's existing incident log rather than treating it as automatically the same root cause.

Confirmed NOT caused by my change: my commit only touches `deployment_api/services/manifest_source.py` (adds a
bounded `ThreadPoolExecutor` to `iter_manifest_row_groups`) and its own unit test file — neither touches
`deployments_inventory` code, AWS census mocking, or any shared fixture these 3 tests depend on.

## Why it matters

`quality-gates.sh` must exit 0 on the FULL suite before `quickmerge --agent` will ship (RULES.md's mandated Pass-1
sentinel gate) — a red, unrelated test blocks EVERY future commit to `deployment-api` from shipping via the sanctioned
path, not just mine. This is currently stalling
`venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`'s open BACKEND P0 todo (the parallel row-group decode
fix, already committed at `deployment-api@a69dad3` on this slot's local clone, verified correct in isolation, just
unable to pass the FULL-suite gate to reach `origin/live-defi-rollout`).

## Recommended decision

- Root-cause + fix `_classification.py`'s prefix-stripping / launched-by-provenance logic (or update the 2 tests'
  fixtures, if the naming convention change was intentional and just never propagated to these tests) — items 1
  above.
- Correlate item 2 against `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s existing incident log;
  determine whether this is the same contention class recurring, or a new AWS-census-mocking regression, and update
  whichever doc is authoritative.
- Once green, re-run `bash scripts/quality-gates.sh` (full) to confirm, which also unblocks the venue-year-coverage
  fix's own shipping.

## Todos

- [x] ✅ [BACKEND] P1. Root-cause + fix the `prd-` prefix / `launched_by` provenance mismatch in
      `deployment_api/routes/deployments_inventory/_classification.py` (or its test fixtures in
      `tests/unit/test_route_deployments_inventory.py`, if the naming change was intentional) so
      `test_build_inventory_classifies_vms_and_jobs` and
      `test_build_inventory_launched_by_provenance_for_cloud_run_jobs` pass deterministically. Repo: deployment-api — deployment-service@a0005a55 + deployment-api@29c4e47 (root cause: manifest-consolidator `{kind}-{ag}` registry-stem mismatch, not a prefix-strip regression).
- [ ] [BACKEND] P2. Determine whether `test_inventory_route_live_path_mocks_registry_and_cloud_run`'s repeated
      (3/3, not intermittent) blocked-socket failure is the same class as
      `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s entry for this test (a timeout there, an
      immediate blocked-connect here) or a distinct regression; fix or fold into that doc accordingly. Repo:
      deployment-api.

## Progress Log

- **2026-08-19 (slot 7, backend_engineer)**: Filed while blocked shipping an unrelated fix. Verified pre-existing +
  unrelated via clean-tree byte-identical reproduction (RULES.md §4b). Declaring a `qg_red` repo-blocker for
  `deployment-api` referencing this doc.
- **2026-08-19 (slot 1, backend_engineer)**: Root-caused + closed P1. NOT a `prd-`-strip regression — the
  manifest-consolidator Cloud Run job name gained a `{kind}` segment (`{env_prefix}-manifest-consolidator-{kind}-{ag}`)
  while `deployment_service`'s `CLOUD_RUN_JOBS` registry still listed bare `manifest-consolidator-{ag}` stems, so
  `_classification.py`'s `_match_registered_job` (correctly prefix-agnostic via `stem in job_name`) fell through to the
  `adhoc` default → `service` with the prefix intact + `launched_by=adhoc`. Already fixed on origin/live-defi-rollout by
  parallel work: `deployment-service@a0005a55` (real `{kind}-{ag}` stems) + `deployment-api@29c4e47` (fixtures →
  `prd-manifest-consolidator-market-data-cefi`). Verified: both P1 tests + the full 113-test file pass (113 passed in
  7.63s). No code change needed; checkbox flipped.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
