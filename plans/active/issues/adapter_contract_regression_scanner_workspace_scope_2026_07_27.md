---
doc_type: issue
title:
  STEP 5.83 adapter-contract-regression scanner hard-fails in EVERY per-repo CI job — baseline entries for repos not
  cloned into that job's narrow workspace read as "regressed" instead of "out of scope"
summary: >
  market-tick-data-service quality-gates-v2 went RED on live-defi-rollout (ldr_qg_failure escalation, no PR) with 155
  `[FAIL] ... (file missing or renamed)` lines from `check_adapter_contract_regression.py`, spanning 9 OTHER repos
  (execution-service, instruments-service, features-service, deployment-api, deployment-service, alerting-service,
  market-data-processing-service, strategy-service, unified-trading-system-ui). Zero failures belonged to
  market-tick-data-service itself. Root cause: the scanner walks every immediate sub-dir of `--workspace-root` with a
  `.git` and treats ANY baseline-listed file it can't find as a regression — correct for a full multi-repo workspace
  (e.g. a `.tabs/N/` slot clone, which is what `mtds_phoenix_orderbook_handler_contract_call_regression_2026_07_27.md`
  used to verify "0 failures fleet-wide" before flipping MTDS's own call-site to hard-fail), but WRONG for a per-repo CI
  job's `quality-gates-v2.yml`, which by design (T4 depends only on UTL/UAC — no service↔service deps) clones only the
  target repo + its declared `dep_repos` + `unified-trading-pm`. Any baseline entry belonging to a repo outside that
  narrow clone set is unconditionally unresolvable and was being counted as "regressed" rather than "not in scope for
  this job". Confirmed via exact reproduction: symlinking only market-tick-data-service + unified-trading-library +
  unified-api-contracts + unified-trading-pm into a scratch workspace and re-running the scanner reproduced exactly 155
  failures (matching CI to the file); the 177 baseline entries belonging to the 4 present repos all passed. This means
  the earlier hard-fail flip's fleet-wide verification (full local workspace) never actually exercised the real CI clone
  footprint, so the flip was silently guaranteed to hard-fail on the very next CI run regardless of any code change.
status: resolved
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer]
tags: [quality-gates, contract-regression, ci-cd, workspace-scope, false-positive, step-5.83]
related:
  [
    /plans/archive/issues/mtds_phoenix_orderbook_handler_contract_call_regression_2026_07_27.md,
    /plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md,
    /plans/archive/issues/mtds_adapter_contract_regression_stale_baseline_2026_07_13.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: cicd
drift_direction: advance-code
locked_by:
resolved_by:
  diagnosed by cicd escalation agt-ea08cf (slot 15); fix independently/concurrently shipped by slot-1,
  unified-trading-pm@34b7066ae (same root cause + fix shape — scoped baseline evaluation to present repos — plus a
  bundled fix for the unrelated RB-8cb21a60 finalize-plan-coverage blocker this issue's own shipping path hit)
source: POST /api/escalate wall_type=ldr_qg_failure, repo=market-tick-data-service, PR #0, 2026-07-27
depends_on: []
---

# STEP 5.83 adapter-contract-regression scanner — workspace-scope false positive

## What broke

`market-tick-data-service` `quality-gates-v2` failed on `live-defi-rollout` (run `30230179214`, job "QG slice (checks)")
with 155 `[FAIL] <repo>/... : 0 contract calls < baseline N (file missing or renamed)` lines. Every single failing
file's top-level path segment named a repo the CI job never clones:

```
alerting-service: 1   deployment-api: 3   deployment-service: 4   execution-service: 27
features-service: 27  instruments-service: 64  market-data-processing-service: 17
strategy-service: 10  unified-trading-system-ui: 2                         → 155 total
```

`quality-gates-v2.yml`'s inputs for this job: `dep_repos: unified-trading-library unified-api-contracts`, plus the
target repo itself and an always-cloned `unified-trading-pm` — i.e. exactly 4 repos on disk. The baseline
(`adapter_contract_baseline.yaml`) has entries for 13 repos (332 files total; 177 belong to the 4 repos actually cloned
here). `check_adapter_contract_regression.py`'s `main()` iterated every baseline entry regardless of whether its owning
repo was even present in `--workspace-root`, so the other 155 were unconditionally "file missing" → FAIL.

## Root cause

Design mismatch, not a code regression: the scanner's `scan_workspace()` is workspace-wide by design (walk every `.git`
sub-dir), matching how `--regenerate-baseline` is meant to be run (from a full multi-repo checkout). MTDS's
`scripts/quality-gates.sh` STEP 5.83 was flipped from `log_warn` to hard `exit 1` in `market-tick-data-service@bab22376`
(same-day, see `mtds_phoenix_orderbook_handler_contract_call_regression_2026_07_27.md`), verified safe via
`check_adapter_contract_regression.py --workspace-root <ws>` returning "OK — 332 baselined file(s) ... 0 failures" — but
that verification ran against a full local multi-repo workspace (all 13 repos present as siblings), which is NOT the
shape of a real `quality-gates-v2.yml` job's workspace. The flip was therefore guaranteed to hard-fail on its very next
real CI run, independent of any code change in market-tick-data-service.

## Fix

Shipped as `unified-trading-pm@34b7066ae` (slot-1, concurrent with this issue's own investigation — see `resolved_by`):
`unified-trading-pm/scripts/quality_gates/check_adapter_contract_regression.py` gained `present_repo_names()` (same
immediate-subdir-with-`.git` filter as `scan_workspace()`) and, in `main()`, skips any baseline entry whose leading path
segment (repo name) is not in that set — reported as a
`[INFO] N baseline entry(ies) skipped — their repo isn't present under --workspace-root (...)` line, distinct from both
`OK` and `FAIL`. Baseline entries for repos that ARE present are evaluated exactly as before (no change to real
regression-catching power). `--regenerate-baseline` is unaffected (unconditionally early-returns before this filtering).
This escalation (agt-ea08cf) independently converged on the identical diagnosis + an equivalent fix shape; the local
draft was discarded in favor of the already-shipped commit rather than landing a duplicate. The same commit also
authored the 2 missing gated finalize-plan companions
(`deployment_registry_firestore_p0_unblock_2026_07_14_finalize_2026_07_27.md`,
`sports_derived_features_postfloor_residue_purge_2026_07_27_finalize_2026_07_27.md`) that had been blocking
`quickmerge --agent` fleet-wide via `check_finalize_plan_coverage.py` (repo-blocker `RB-8cb21a60`, unrelated to this
issue but the reason this issue's own fix couldn't ship via standard quickmerge either — see Progress Log).

## Verification

- Reproduced exactly: symlinked only `market-tick-data-service` + `unified-trading-library` + `unified-api-contracts` +
  `unified-trading-pm` into a scratch dir, ran the unpatched scanner against it → 155 failures, byte-for-byte the same
  file list as the CI log.
- Post-fix (`unified-trading-pm@34b7066ae`), same scratch workspace → exit 0,
  `"OK — 177 baselined file(s) at or above minimum; 14 new file(s) not yet baselined."`
- Post-fix, full local `.tabs/15/` workspace (all 13 repos present) → exit 0,
  `"OK — 332 baselined file(s) at or above minimum; 18 new file(s) not yet baselined."` — identical evaluated-file count
  to pre-fix (0 skipped, since all repos present), confirming no loss of regression-catching power for the
  full-workspace case.
- `check_finalize_plan_coverage.py` (the unrelated RB-8cb21a60 blocker) re-checked post-pull → exit 0,
  `"At baseline (0)."`
- `ruff check` / `ruff format --check` / `basedpyright` on this escalation's own (discarded) draft of the same fix:
  clean — confirms the fix shape is sound independent of whose implementation shipped.
- market-tick-data-service `bash scripts/quality-gates.sh` full run at HEAD+fix: see Progress Log / commit evidence.

## Why it matters beyond this one wall

`mtds_phoenix_orderbook_handler_contract_call_regression_2026_07_27.md` Todo 4 (still open) proposes flipping the SAME
warn-only → hard-fail wiring in `execution-service`, `instruments-service`, `features-service` (+ MTDS-family worktree
copies), gated on "confirming that repo's current fleet-wide baseline compliance is clean" via the same full-workspace
scan this issue shows is an incomplete check. Without this fix, flipping any of those repos' call-sites to hard-fail
would hit the identical false-positive wall the very next time their own `quality-gates-v2` ran in CI — this fix is a
prerequisite for that follow-up todo actually being safe, not just the current MTDS wall.

## Todos

- [x] [SCRIPT] P1. Diagnose root cause (scanner workspace-scope bug, not a market-tick-data-service code regression) —
      confirmed via exact-match reproduction (155/155) in a symlinked scratch workspace mirroring CI's real clone
      footprint. (repo: unified-trading-pm)
- [x] [SCRIPT] P1. Fix `check_adapter_contract_regression.py` to skip baseline entries whose owning repo isn't present
      in `--workspace-root`, instead of treating them as regressions. ✅ Shipped `unified-trading-pm@34b7066ae` (slot-1,
      landed concurrently with this escalation's own equivalent draft — see Fix section). Verified both the narrow
      (CI-shaped) and full local workspace scans exit 0 with unchanged regression-catching power for in-scope repos.
      (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. Follow-up (not this escalation's scope): re-attempt
      `mtds_phoenix_orderbook_handler_contract_call_regression_2026_07_27.md` Todo 4 (flip
      execution-service/instruments-service/features-service warn-only → hard-fail) now that this scope bug is fixed —
      still gate each flip on that repo's own CI-shaped verification (its actual `dep_repos` clone set), not just a full
      local workspace scan. (repo: execution-service, instruments-service, features-service, unified-trading-pm)
