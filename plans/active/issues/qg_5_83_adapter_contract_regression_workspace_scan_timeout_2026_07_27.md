---
doc_type: issue
title:
  "QG STEP 5.83 (adapter contract-call regression ratchet) times out under current host I/O load — HARD-FAILS every
  repo's quality-gates.sh, fleet-wide, since its 2026-07-27 warn-only-to-hard-fail upgrade"
summary: >-
  scripts/quality-gates.sh STEP 5.83 was upgraded from warn-only to a hard `exit 1` on 2026-07-27 (per its own comment,
  motivated by a real regression that "sailed through silently under the warn-only form"). The check shells out to
  `unified-trading-pm/scripts/qg/no_adapter_contract_regression.sh`, wrapped in `run_timeout 60`, which invokes
  `check_adapter_contract_regression.py --workspace-root <ws>` — a full `rglob("*.py")` walk of EVERY repo checked out
  under the slot's `.tabs/<N>/` directory (15-20+ repos). Measured directly (features-service, slot 8, 2026-07-27 ~10:52
  UTC): the scanner process sat in Linux `D` state (uninterruptible disk sleep, i.e. I/O-bound not CPU-bound) for 1m28s+
  before I killed the timing run, well past the 60s `run_timeout` budget quality-gates.sh gives it — meaning the gate
  now HARD-FAILS on every quality-gates.sh invocation on this host regardless of what the committing agent actually
  changed, because the scan can't complete inside its own timeout under current shared-host I/O contention (consistent
  with the pre-existing disk-capacity/multi-slot-concurrent-QG incidents already on record). Reproduced independent of
  any code change: `git stash` (removing my in-flight features-service diff) still hit the identical ❌ at the identical
  step. This blocks shipping ANY commit, in ANY repo, via the mandatory quality-gates.sh → quickmerge flow, fleet-wide,
  until either the timeout budget is raised or the scan is made faster/incremental.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, features-service]
scope: [engineer, admin]
tags: [quality-gates, qg-5.83, adapter-contract-regression, timeout, fleet-wide, shipping-blocked, disk-io]
related:
  [
    /plans/active/issues/mtds_dex_pools_adapter_contract_baseline_stale_2026_07_26.md,
    /plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  measured 2026-07-27 (slot 8) while attempting to ship features-service@<pending> for
  features_by_date_root_canonicalisation_2026_07_21.md todo 6 — real host measurement, not inferred.
depends_on: []
---

# QG STEP 5.83 hard-fails fleet-wide on a 60s timeout it can't meet under current host I/O load

## What was found

1. `bash scripts/quality-gates.sh --no-fix` in `features-service` (slot 8) halted with:
   `❌ Adapter contract-call regression — see plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md`
   at STEP `[5.83/6] ADAPTER CONTRACT-CALL REGRESSION RATCHET`, exit 1, with the script terminating immediately after
   (no further steps ran — this is a hard, script-terminating failure, not a warning).
2. `scripts/quality-gates.sh:161-169` wraps this:
   `run_timeout 60 bash "${QG_SCRIPTS_DIR}/no_adapter_contract_regression.sh" "${WORKSPACE_ROOT}" || { log_fail ...; exit 1; }`.
   Its own comment states the check "was warn-only through 2026-07-27" and was upgraded to hard-fail after a real
   regression on MTDS's `phoenix_orderbook_handler.py` "sailed through silently under the warn-only form."
3. `no_adapter_contract_regression.sh` invokes `check_adapter_contract_regression.py --workspace-root <ws>`, which walks
   EVERY repo directory under `--workspace-root` with a `.git` (15-20+ repos in this multi-repo slot workspace) via
   `root.rglob("*.py")`, reading every non-excluded `.py` file's full text once per repo scanned.
4. Verified independent of my in-flight diff: `git stash` (removing my `features-service` changes entirely) reproduced
   the IDENTICAL failure at the identical step — this is not caused by any content regression in my commit.
5. Ran the underlying scanner directly, unwrapped by any timeout, to measure its real duration:
   `python3 unified-trading-pm/scripts/quality_gates/check_adapter_contract_regression.py --workspace-root <slot-8-tabs-dir>`.
   The process (PID 3221592) sat in Linux `D` state (uninterruptible sleep — i.e. blocked on disk I/O, not CPU-bound
   regex/compute) continuously from launch through at least 1m28s elapsed — well past the 60s budget `run_timeout 60`
   gives it in the real quality-gates.sh invocation. `D`-state, not high-CPU, strongly indicates this is disk I/O
   contention (consistent with the already-documented multi-slot shared-host disk-capacity pressure — many agents run
   `quality-gates.sh`/pytest concurrently on this host per CLAUDE.md's "Shared-host ≤2 full QGs at once" guidance and
   the disk-full incidents on record), not a logic bug in the scanner's regex/walk itself.
6. Net effect: on this host, right now, EVERY `quality-gates.sh` run in EVERY repo hits this same 60s-budgeted,
   full-workspace-walk step, and the walk cannot reliably complete inside 60s under current I/O contention — so the gate
   hard-fails regardless of what the committing agent changed. This is fleet-wide, not features-service-specific: the
   same STEP 5.83 block exists (or is templated into) every repo's `scripts/quality-gates.sh` per the shared QG
   entrypoint convention.

## Why this matters (do not descope)

This is currently **blocking shipping of ANY commit in ANY repo** via the mandatory `quality-gates.sh` → `quickmerge`
flow — the only sanctioned path for code to reach `live-defi-rollout` (a raw `git push` of code is banned). Until
resolved, every worker on this host that reaches a real, otherwise-green QG run will hit this same wall at STEP 5.83.
This is exactly the kind of cross-cutting, fleet-wide blocker CLAUDE.md's "big finding" triage rule calls for immediate
operator notification on.

## Recommended decision (not actioned here — outside data_engineering craft scope; needs infra/CI ownership)

Two independent, non-exclusive fixes:

1. **Raise or make the `run_timeout 60` budget host-load-aware** (or simply raise it — e.g. to 180-300s) so a slow-but-
   genuinely-passing scan isn't misreported as a "regression." A timeout should never map to the SAME `log_fail` message
   as a genuine content regression — today a timeout and a real per-file count drop are indistinguishable to the
   committing agent, which will mislead whoever picks this up into chasing a phantom code regression.
2. **Make the scan itself faster/incremental** — e.g. cache per-file mtimes+counts across runs and only re-scan changed
   files (git-diff-driven), or scope the scan to only the repos the current commit actually touches instead of every
   repo under `--workspace-root` every time. A full 15-20-repo `rglob` + full-file-read on every single
   `quality-gates.sh` invocation, in every repo, is the kind of repeated full-corpus-equivalent walk the data-pipeline
   craft's "single-walk discipline" principle would flag if this were GCS data instead of local source — the same "don't
   rescan what didn't change" logic applies.

## Todos

- [ ] 1. [INFRA] P2 (downgraded from P0 — see progress log 2026-07-27 cicd/slot-5: todo 2's fix alone resolved the
      timeout, this is now optional defense-in-depth, not a blocker). Raise `run_timeout 60` in
      `scripts/quality-gates.sh` STEP 5.83 (per-repo file, not templated — a fleet-wide bump means editing every
      consuming repo's copy) as extra headroom against pathological host I/O contention. (repo: unified-trading-pm +
      every consuming repo)
- [x] 2. [INFRA] P1. Make `check_adapter_contract_regression.py`'s scan stop walking the full workspace — read only the
      baseline's own files (`read_baseline_files()`), scoped to present repos, instead of `rglob("*.py")`-ing every file
      in every repo. Runtime is now O(baseline size ≈ 332 files), not O(workspace size) — measured 0.5-0.65s standalone
      AND via the real `quality-gates.sh` STEP 5.83 invocation path, down from a >120s reproduction (was hitting the 60s
      `run_timeout`). `scan_workspace()` (the full walk) is retained but now used only by `--regenerate-baseline`, an
      explicit non-CI operator action. Pass/fail semantics unchanged (existing test suite + 1 new regression test lock
      in that the check path never calls `scan_workspace`). — unified-trading-pm@91e9865b9
- [ ] 3. [INFRA] P2. Distinguish a genuine "count dropped below baseline" failure from a "scan timed out / didn't
      complete" failure in the emitted message — the current `log_fail "Adapter contract-call regression..."` text is
      identical for both, which will send whoever hits this chasing a nonexistent code regression instead of an infra
      timeout. Lower urgency now that todo 2 makes a genuine timeout very unlikely, but still worth doing for the rare
      pathological case. (repo: unified-trading-pm)

## Progress Log

- **2026-07-27 (slot 8, data_engineering)**: Filed while attempting to ship a real fix (`features-service` delta_one
  candle-reader `pipeline_mode` threading, for `features_by_date_root_canonicalisation_2026_07_21.md` todo 6's blocking
  P0). QG hard-failed at STEP 5.83 before my commit could ship; confirmed pre-existing/unrelated to my diff via
  `git stash` reproduction; confirmed the underlying scanner is I/O-bound (`D` state) and genuinely exceeds the 60s
  budget under current host load, not a logic bug. Escalating per CLAUDE.md's cross-cutting "big finding" rule — this
  blocks shipping fleet-wide, not just my task. NOT actioned (raising the timeout / making the scan incremental) — out
  of `data_engineering` craft scope (infra/CI ownership of `scripts/quality-gates.sh` + the shared QG script template),
  and I should not unilaterally raise a shared QG timeout without infra sign-off given it's rolled out via
  `rollout-workflow-templates.sh`-style propagation to every repo.
- **2026-07-27 (cicd, slot 5, escalation RB-6696c2a9)**: Reproduced independently —
  `check_adapter_contract_regression.py` exceeded 120s standalone in slot 5's workspace too, confirming this isn't
  purely transient host contention: the full `rglob` walk is inherently too slow for a 60s budget on a 25-repo
  workspace, contention or not. Root-caused: the scan only needs the ~332 baseline-listed files' counts, not every `.py`
  file in every repo — `scan_workspace()` was doing O(workspace size) I/O to answer an O(baseline size) question.
  Shipped `read_baseline_files()` (targeted reads of just the baseline's files, scoped to present repos) as the check
  path's data source; `scan_workspace()` is now reserved for `--regenerate-baseline` only. Verified: 8/8 unit tests pass
  (7 existing + 1 new regression test asserting the check path never calls `scan_workspace`), ruff + basedpyright clean,
  unified-trading-pm's own `quality-gates.sh --no-fix` passed (123s, unrelated warn-only findings only), and the real
  STEP 5.83 invocation path (`no_adapter_contract_regression.sh` from within `features-service`) now completes in 0.65s.
  Shipped directly to `live-defi-rollout` (unified-trading-pm@91e9865b9) under the PM `scripts/**` pipeline-unblock
  direct-push carve-out (CLAUDE.md § Git discipline). Todo 2 done; todo 1 downgraded to optional defense-in-depth (no
  longer needed to clear the wall); todo 3 still open as a lower-urgency polish item. Wall RESOLVED — this was NOT a
  false alarm or pure host contention, it was a genuine O(workspace) vs O(baseline) inefficiency in the scanner.
