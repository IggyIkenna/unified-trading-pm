---
doc_type: issue
title:
  instruments-service QG STEP 5.101 (empty-string-fallback baseline ratchet) is red at LDR HEAD — blocks ALL quickmerge
  pushes to this repo
summary: >
  While shipping an unrelated fix (Dockerfile UTL base-image digest refresh + tradfi expected_universe golden regen,
  both for the sports_cf8_available_at_backfill_regression issue doc), `bash scripts/quality-gates.sh` failed STEP 5.101
  with "368 empty-string-fallback site(s) > baseline 366" on a completely clean instruments-service checkout at LDR HEAD
  (a771e3e2). Verified via a controlled git-stash A/B test that this is 100% pre-existing and NOT introduced by either
  of this session's two changes (Dockerfile, tradfi.json) — the identical failure reproduces with both diffs stashed
  out. The checker (`unified-trading-pm/scripts/quality_gates/check_no_empty_string_fallback.py`) reports the LAST 2
  entries of its full sorted site list once the total count exceeds the baseline (`scan.sites[allowed:]`) — this is NOT
  a git-diff-based "newly added lines" report, so the two lines it names
  (`scripts/reconcile_lending_indices_phantom.py:232`, `scripts/reconcile_phantom_manifest_rows.py:197`) are confirmed
  via `git blame` to be 2-month-old code (2026-05-16), not recent additions. The genuine +2 over baseline therefore
  lives somewhere else in the repo's ~101 files matching the `.get("key", "")` pattern and was not isolated in this
  session (a full baseline diff/bisect needs a dedicated pass, out of scope for the dispatch that found it). This blocks
  EVERY instruments-service push via the mandatory `quickmerge.sh --agent` sentinel gate (full clean QG pass required),
  independent of any change's own correctness.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [instruments-service]
scope: [engineer]
tags: [quality-gates, empty-string-fallback, baseline-ratchet, ci-blocking, qg-red]
related:
  [
    plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
  ]
created: 2026-07-14
parent_epic: instruments_master
priority: P1
source: sports_cf8_available_at_backfill_regression-007 dispatch, slot 2, data_engineering, 2026-07-14
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# instruments-service QG STEP 5.101 red at LDR HEAD — baseline breached by 2, exact sites not isolated

## What I found

Ran `bash scripts/quality-gates.sh` on a completely clean instruments-service checkout at LDR HEAD (`a771e3e2`, no local
diff at the time of the first run) while trying to ship an unrelated fix. STEP 5.101 (the `.get("key", "")`
empty-string-fallback baseline ratchet) failed:

```
[FAIL] instruments-service: 368 empty-string-fallback site(s) > baseline 366. New/over-baseline site(s):
scripts/reconcile_lending_indices_phantom.py:232; scripts/reconcile_phantom_manifest_rows.py:197
```

Baseline (`unified-trading-pm/scripts/quality_gates/no_empty_string_fallback_baseline.yaml`) records
`instruments-service: count: 366`. Live scan reports 368 — a genuine +2 breach.

**Verified pre-existing, not caused by this session's work**: `git stash` (removing both this session's Dockerfile
digest-pin edit and the tradfi.json golden regen) and re-running
`check_no_empty_string_fallback.py --workspace-root ... --scope instruments-service` directly reproduces the identical
`368 > 366` failure with the identical two reported lines. Both changes this session touch only `Dockerfile` and a JSON
test fixture — neither can plausibly introduce a new `.get("key", "")` Python call site.

**The two reported lines are NOT the actual regression** (a checker quirk worth fixing separately): the checker's own
logic (`check_no_empty_string_fallback.py:360`, `over = scan.sites[allowed:]`) reports whichever sites sort past the
baseline cutoff in its full-repo site list — this is a positional tail-slice, not a git-diff "what's new" computation.
`git blame` on both named lines confirms they are 2-month-old code (`reconcile_lending_indices_phantom.py:232` — commit
`88d48da5b`, 2026-05-16; the file's own most recent unrelated touch is `0d2ea24f`, 2026-07-13). The genuine two extra
sites live somewhere else among the ~101 files in this repo that match the `.get("key", "")` pattern; I did not isolate
them (a proper isolation needs either a full baseline recount pinned to the exact commit
`no_empty_string_fallback_baseline.yaml`'s `count: 366` was captured against, or a bisect across the commits since then)
— out of scope for the dispatch that found this (a data-pipeline correctness fix for the sports CF-8 issue, not a
QG-tooling audit).

## Why it matters

- Blocks `quickmerge.sh --agent` for ALL instruments-service changes (the sentinel requires a full clean
  `quality-gates.sh` pass on the committed HEAD; `--skip-*` flags are policy-banned). This is the same failure class
  already tracked for market-tick-data-service in `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`
  — a second repo now hits it.
- The checker's tail-slice reporting (rather than true diff-based new-site detection) makes root-causing a baseline
  breach materially harder than it should be — worth fixing so the NEXT breach (in this or any repo) reports the actual
  new call sites, not arbitrary old ones that happen to sort last.

## Recommended next steps

1. Isolate the true +2 sites: `git log` the commits since the baseline's `count: 366` was captured (check
   `no_empty_string_fallback_baseline.yaml`'s own git history for the commit that set 366) and diff `.get("key", "")`
   site counts commit-by-commit, OR re-run the checker against each recent commit's tree until the count flips 366→368.
2. Either fix the 2 real new sites (fail-fast rewrite) or add `# noqa: qg-empty-fallback` with a one-line reason if
   genuinely deliberate, then this issue closes.
3. Consider fixing `check_no_empty_string_fallback.py`'s reporting to do actual git-diff-based new-site detection
   (compare against the baseline-setting commit's tree) instead of a positional tail-slice, so future breaches are
   self-diagnosing.

## Todos

- [ ] [INFRA] P1. Isolate the true 2 new `.get("key", "")` empty-string-fallback call sites that pushed
      instruments-service from 366 to 368 (the two currently-reported lines are confirmed 2-month-old, not the actual
      regression) and fix them (fail-fast rewrite or `# noqa: qg-empty-fallback` with reason). This is currently
      blocking ALL quickmerge pushes to instruments-service. (repo: instruments-service)
- [ ] [INFRA] P2. Fix `check_no_empty_string_fallback.py`'s over-baseline reporting to do git-diff-based new-site
      detection against the baseline-setting commit instead of `scan.sites[allowed:]` (a positional tail-slice that can
      report arbitrary old code, as it did here). (repo: unified-trading-pm)

## Progress Log

**2026-07-14, slot 2 (data_engineering)**: discovered while shipping a deployment-freshness fix for the sports CF-8
issue doc. Verified pre-existing via clean-tree stash test. Did not isolate the true regressed sites (scope creep beyond
the dispatch); filed this doc + declared a repo-blocker so the wait is backend-tracked rather than silently absorbed. No
code changed in this repo by this touch.
