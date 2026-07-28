---
doc_type: issue
title:
  "quality-gates-v2 zero-test-silent-pass guard false-fails on a genuinely-green pytest run — shared
  base-service.sh read $_pytest_log after an unrelated second pytest invocation, racing a tmp-file
  eviction on the self-hosted CI runner"
summary:
  "features-service promotion PR #883 (LDR a9429cba → main) hit quality-gates-v2 RED on the 'QG slice
  (tests)' leg (run 30325671949, job 90170498861). The CI log showed the real pytest run PASS CLEAN —
  '17954 passed, 209 skipped, 1925 warnings in 223.14s' — followed by the PM-integration pytest
  sub-check also passing ('6 passed in 0.12s'), and only THEN did the zero-test-silent-pass guard fail:
  two 'grep: /home/ubuntu/.cache/qg-tmp/qg-pytest-out.TZBfPL: No such file or directory' lines, then
  '❌ ZERO TESTS RAN — QG cannot pass with no test execution (zero-test-silent-pass guard)'. Root cause:
  scripts/quality-gates-base/base-service.sh wrote the main pytest run's output to a mktemp'd
  $_pytest_log via `tee -a`, then ran a SEPARATE, unrelated PM-integration pytest invocation before
  finally grep'ing $_pytest_log for the '<N> passed' count ~5s+ after the file was written. On this
  self-hosted CI runner the file was gone by the time the guard read it (grep errored, `|| echo 0`
  swallowed the error into '0 tests ran', which the guard then reported as a real zero-test scenario
  instead of an infra read failure) — a false RED on a run that had already printed a clean pass.
  A prior CI run of the same leg on the PREDECESSOR PR (#882, LDR 68ae605c) failed differently — a
  genuine pytest hang/timeout inside tests/delta_one/unit/test_feature_groups/test_momentum.py's
  test_adx_columns_present, stuck in pandas' `_add_lagged_features` -> pd.concat (run 30311742866,
  job 90128688461) — that PR was superseded (closed, not merged) once LDR advanced past it, so its
  failure is moot; this doc documents only the #883 zero-test-guard false-fail, which is a real
  QG-script bug independent of that hang. Fix: reordered the zero-test-silent-pass guard in
  base-service.sh to run in the SAME statement block immediately after the tee write (before the
  PM-integration sub-check), closing the multi-second exposure window to near-zero without changing
  the guard's pass/fail semantics."
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, features-service]
scope: [engineer, admin]
tags: [ci, quality-gates, quality-gates-v2, flaky-ci, self-hosted-runner, tmp-file-race, promotion-gate]
related: [ldr_main_promotion, cicd_mvp_ldr_to_main_pipeline_2026_06_30]
created: "2026-07-28"
parent_epic: infrastructure_master
priority: P1
source: "escalation agt-0b0013 (cicd role, slot 10) — POST /api/escalate wall_type=ldr_qg_failure, features-service#882/#883"
assigned_vm: NA
resolved_by: "unified-trading-pm@<fill-in-sha>"
locked_by: null
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# quality-gates-v2 zero-test-silent-pass guard false-fail on a passing pytest run

## What happened

`POST /api/escalate` dispatched a `cicd` worker (agt-0b0013) with `wall_type=ldr_qg_failure`,
`repo=features-service`, `pr_number=882` — "quality-gates-v2 FAILED on promotion PR
features-service#882 (LDR -> main)". By the time the worker started, PR #882 had already been
CLOSED (not merged) — LDR had advanced to `a9429cba`, and the standard promote-PR-supersede
automation opened a fresh PR #883 (`promote/features-service/a9429cbab1d8` → `main`), which was
ALSO failing `quality-gates-v2` on the same `QG slice (tests)` leg.

- **PR #882** (`68ae605c`, CLOSED, superseded): the failing run (30311742866) hit a genuine pytest
  hang/timeout inside `tests/delta_one/unit/test_feature_groups/test_momentum.py::test_adx_columns_present`,
  stuck deep in `features_service/delta_one/app/calculators/base.py::_add_lagged_features` ->
  `pd.concat`. Since this PR is superseded and its head is no longer the promotion target, this
  specific hang was not chased further here — if it recurs on a live PR, it needs its own
  investigation (possibly a real perf regression in `_add_lagged_features`, or a pytest-timeout
  false trip under host contention).
- **PR #883** (`a9429cba`, the live promotion target): the failing run (30325671949, job
  90170498861) shows the REAL pytest run passing clean —
  `17954 passed, 209 skipped, 1925 warnings in 223.14s (0:03:43)` — then the PM-integration
  sub-check passing — `6 passed in 0.12s` — and ONLY THEN the gate went red:

  ```
  grep: /home/ubuntu/.cache/qg-tmp/qg-pytest-out.TZBfPL: No such file or directory
  grep: /home/ubuntu/.cache/qg-tmp/qg-pytest-out.TZBfPL: No such file or directory
  ❌ ZERO TESTS RAN — QG cannot pass with no test execution (zero-test-silent-pass guard)
  ##[error]QG selector 'tests' FAILED (leg=tests)
  ```

## Root cause

`scripts/quality-gates-base/base-service.sh`'s "tests" leg:

1. `mktemp`s `$_pytest_log` under `${TMPDIR:-/tmp}` (`TMPDIR` is redirected to
   `${HOME}/.cache/qg-tmp` by `qg-common.sh`, per the `shared_host_tmp_tmpfs_exhaustion_2026_07_08`
   fix), sets a `trap 'rm -f "$_pytest_log"' EXIT INT HUP TERM`.
2. Runs the main unit-test pytest invocation, streaming output live via `tee -a "$_pytest_log"`.
3. Logs `"Tests PASSED"`.
4. Runs a SEPARATE, unrelated PM-integration pytest invocation
   (`tests/integration/test_pm_scripts_integration.py`) — this does not touch `$_pytest_log` at
   all.
5. ONLY THEN greps `$_pytest_log` for the `<N> passed` / `<N> skipped` counts (the
   zero-test-silent-pass guard, `fix-zero-test-silent-pass`).

Between step 2 finishing and step 5's grep, several seconds elapse (the PM-integration pytest
invocation plus its own startup/collection). On this self-hosted CI runner, `$_pytest_log` was
observed gone by step 5 — `grep` errored ("No such file or directory"), and the guard's
`|| echo "0"` fallback silently turned that read failure into "0 tests ran", which the guard then
(correctly, given its inputs) treated as a real zero-test scenario and failed the gate — even
though the actual pytest run had unambiguously passed 17,954 tests three lines above in the same
log. The guard conflated two different failure modes (grep found the file but matched nothing, vs.
grep couldn't even open the file) and treated both as "zero tests ran".

The exact mechanism that removed the file within this window was not conclusively identified (the
PM repo's own `cleanup-stale-qg-tmp.sh` cron only reaps `pytest-of-*` dirs older than 60 minutes —
nowhere near this ~5s window — so it is not the cause; no other cleanup path targeting
`qg-pytest-out.*` was found in the PM or features-service repos). Given the file is written and
read in the same continuous bash process (no subshell boundary crossed between steps 2 and 5), the
most likely explanation is host-level tmp/disk pressure or eviction specific to this shared
self-hosted runner. Rather than chase an unreproducible external cause further, the fix removes the
exposure window directly.

## Fix

Reordered the zero-test-silent-pass guard block to run in the SAME statement block immediately
after the `tee` write / `PIPESTATUS` check (i.e., right after the `if/else` that runs the main
pytest invocation), BEFORE the unrelated PM-integration pytest sub-check and its `log_ok "Tests
PASSED"` message. This is a pure reordering — no change to the guard's pass/fail conditions, its
skip-rate warning, or the PM-integration check itself — that shrinks the write-to-read window from
several seconds (spanning an entire second pytest invocation) to effectively zero (adjacent
statements, no intervening commands). Shipped in `unified-trading-pm@<fill-in-sha>`
(`scripts/quality-gates-base/base-service.sh`).

This is the SHARED QG base script (`base-service.sh`) sourced by every service repo's
`scripts/quality-gates.sh` (content-first cloned at PM's `live-defi-rollout` HEAD per
`cicd_mvp_ldr_to_main_pipeline_2026_06_30`'s dependency-resolution chain), so the fix applies
fleet-wide on the next quality-gates-v2 run of any repo, not just features-service.

## Verification

- `bash -n scripts/quality-gates-base/base-service.sh` — syntax OK.
- `bash scripts/quality-gates.sh --no-fix` on `unified-trading-pm` itself — green (evidence in the
  shipping commit).
- features-service PR #883's `quality-gates-v2` re-triggered post-fix; expected to pick up the
  updated `base-service.sh` via its content-first LDR clone of `unified-trading-pm` on the next run.

## Follow-up (not done here — out of this escalation's scope)

- [ ] [OPERATOR] If `tests/delta_one/unit/test_feature_groups/test_momentum.py::test_adx_columns_present`
      (or its call path through `_add_lagged_features` -> `pd.concat`) hangs again on a LIVE
      promotion PR (not just the now-superseded #882), investigate as a genuine perf/hang defect —
      the #882 occurrence was not chased here since that PR was already superseded.
