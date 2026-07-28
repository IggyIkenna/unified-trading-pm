---
doc_type: issue
title:
  "QG STEP 5.83 (ADAPTER CONTRACT-CALL REGRESSION RATCHET) flakes under shared-host QG contention — 60s run_timeout too
  short"
summary: >-
  features-service's quality-gates.sh STEP 5.83 wraps scripts/qg/no_adapter_contract_regression.sh in `run_timeout 60`.
  Under normal fleet-wide shared-host contention (multiple slots running quality-gates.sh concurrently), the script's
  real wall-clock time measured at 2m21s (vs 12s user CPU time — the gap is disk/IO contention, not script logic), so
  the 60s timeout fires and STEP 5.83 is treated as a HARD FAIL even though the check itself is logically green
  (`[check_adapter_contract_regression] OK`). This produced 2 of 4 full quality-gates.sh runs failing on an unrelated
  diff (features-service orchestrator.py pipeline_mode fix) purely due to this flake.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, features-service]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, adapter-contract-regression, ci, shared-host-contention]
related: [/plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  measured 2026-07-27 while shipping delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md todo 1
  (features-service). 2 of 4 full quality-gates.sh --no-fix runs on an unrelated diff failed at STEP [5.83/6] with
  "Adapter contract-call regression"; running scripts/qg/no_adapter_contract_regression.sh standalone (same tree, same
  moment) exited 0 both times, and `time` measured real=2m21.478s / user=0m12.093s — real, not inferred.
---

# QG STEP 5.83 (adapter contract-call regression ratchet) flakes under fleet-wide shared-host contention

## What was found

While shipping a features-service fix (`delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md` todo 1 —
threading `pipeline_mode` through `_load_and_validate_candles`, a diff that touches only
`features_service/delta_one/engine/orchestrator.py` and a new unit test file), `bash scripts/quality-gates.sh --no-fix`
failed on 2 of 4 consecutive full runs at:

```
── [5.83/6] ADAPTER CONTRACT-CALL REGRESSION RATCHET ──
❌ Adapter contract-call regression — see plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md
```

with no further detail (the step only echoes the fixed fail string on non-zero exit — see
`features-service/scripts/quality-gates.sh` line 167-168:
`run_timeout 60 bash "${QG_SCRIPTS_DIR}/no_adapter_contract_regression.sh" ... || { log_fail ...; exit 1; }`).

Running `unified-trading-pm/scripts/qg/no_adapter_contract_regression.sh "${WORKSPACE_ROOT}"` standalone, on the SAME
tree state, immediately after each QG-run failure, exited **0** both times with
`[check_adapter_contract_regression] OK — 332 baselined file(s) at or above minimum; 18 new file(s) not yet baselined.`
— the check itself is logically green.

Timed the standalone run explicitly (`time bash .../no_adapter_contract_regression.sh ...`) while the fleet was under
load (3-7 concurrent `quality-gates.sh` processes across other slots, confirmed via `pgrep -af quality-gates.sh`):

```
real    2m21.478s
user    0m12.093s
sys     0m1.444s
```

The **user** time (actual CPU work) is 12s — comfortably under the step's `run_timeout 60`. The **real** (wall-clock)
time is 2m21s — over double the timeout. The gap is disk/IO contention: the script walks many repos' files (`git diff`,
`find`, per-file grep for contract-call patterns) against a baseline of 332+ files, and under concurrent QG runs from
other slots doing similar heavy filesystem work on the same shared host, that walk is I/O-bound, not CPU-bound.
`run_timeout 60` kills the process on wall-clock, not CPU-clock, so it fires under exactly this condition regardless of
whether the check would ultimately pass.

## Why this matters

This is a **flaky quality gate** — `STEP 5.83` is coded as a HARD FAIL (`exit 1` on the whole `quality-gates.sh` run)
specifically because a prior real regression
(`/plans/archive/issues/mtds_phoenix_orderbook_handler_contract_call_regression_2026_07_27.md`) sailed through silently
under an earlier warn-only form. Making it a hard blocker was the right fix for that gap — but a 60s wall-clock timeout
on a shared multi-tenant host, where several agent slots legitimately run full `quality-gates.sh` concurrently by design
(per `CLAUDE.md` § "Shared-host ≤2 full QGs at once" — a soft guideline, not enforced, and the observed fleet routinely
runs more), means this specific step will periodically block **unrelated, correct diffs** from shipping, forcing wasted
re-runs (each full QG run costs ~10-20 minutes). It already cost 2 of 4 attempts (~30+ min) on a diff that never touched
an adapter/handler file.

## Todos

- [x] ✅ 1. [INFRA] P2. Raise `run_timeout 60` to a longer wall-clock budget (e.g. 180-300s) for STEP 5.83 in
      `features-service/scripts/quality-gates.sh` (and any other per-repo `quality-gates.sh` copies that wrap the same
      `no_adapter_contract_regression.sh` call with the same 60s timeout — grep for
      `run_timeout 60.*no_adapter_contract_regression` across all repos' `scripts/quality-gates.sh`) to absorb realistic
      shared-host I/O contention without weakening the hard-fail semantics itself. — features-service,
      execution-service, and instruments-service were already fixed to 300s by prior work (commit
      `chore(qg): raise STEP 5.83     adapter-contract-regression run_timeout 60->300s` in each). This todo closes the
      last remaining repo: `market-tick-data-service@57dfccc7` (same fix, same commit message). Verified via corpus-wide
      grep for `run_timeout.*no_adapter_contract_regression` across every repo in the workspace — no other copies remain
      at 60s.
- [ ] 2. [INFRA] P3. Consider whether `no_adapter_contract_regression.sh`'s per-file walk can be made faster/more
      I/O-light (e.g. operating on `git     diff --name-only` against the baseline commit instead of a broader
      filesystem walk, if it isn't already) so the check is less exposed to contention regardless of the timeout value.
- [ ] 3. [INFRA] P3. If GH Actions / promote-PR CI also runs this same QG step (not just local/slot `quality-gates.sh`),
      confirm whether CI runners see the same contention profile — if CI is single-tenant per run, the flake may be
      slot-worktree-specific only; scope todo 1's fix accordingly (repo-wide `quality-gates.sh` vs a CI-only override).

## Progress Log

- **2026-07-27** — Filed while shipping `delta_one_cefi_candle_reader_never_threads_pipeline_mode_2026_07_27.md` todo 1.
  Diagnosed via direct standalone re-run + `time` measurement, not inferred. Did not fix inline (out of scope for the
  delta_one task; this is a QG-infra gap affecting the whole fleet, filed per findings-triage as its own issue). My
  actual task's fix (orchestrator.py pipeline_mode threading) is unaffected — pytest (17900 passed, 0 failed) and
  basedpyright typecheck both passed clean on a full run; only this ratchet step flaked.
- **2026-07-28** — Todo 1 completed. Corpus-wide grep (`run_timeout.*no_adapter_contract_regression` across every repo's
  `scripts/quality-gates.sh`) found `execution-service`, `features-service`, and `instruments-service` already fixed to
  `run_timeout 300` by prior work; only `market-tick-data-service` still had `run_timeout 60`. Fixed there —
  `market-tick-data-service@57dfccc7`, full `quality-gates.sh` green (sentinel-verified), shipped via quickmerge. No
  other repo in the workspace still wraps the check at 60s.
