---
doc_type: issue
title: test-setup-sh-uv-bootstrap-fallback.sh's structural anchor is stale against setup.sh's current wording
summary: >-
  Discovered as a pre-existing-failure baseline check while shipping the qg_sentinel_environment_blind_2026_07_23.md fix
  (ci_satellite_ao_dispatch_batch2 todo 1) — confirmed via `git stash` that this test fails identically with my changes
  stashed out, so it is unrelated and pre-existing, not a regression. Root-caused: the test's structural-anchor `case`
  pattern expects the literal substring `pip install "uv==0.10.8"` (quoted), but `setup.sh`'s actual current
  pip-fallback line is `"$PYTHON_CMD" -m pip install uv==0.10.8 --quiet 2>/dev/null || pip install uv==0.10.8 --quiet
  2>/dev/null` (unquoted, with `--quiet` + a `$PYTHON_CMD -m` prefix branch) — setup.sh's wording drifted since the test
  was last aligned. The BEHAVIOR is still correct (both fixture cases in the same test file pass — pinned-version
  realignment via the astral installer, pip-last-resort fallback both work); only the anchor's exact-string match is
  stale.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, testing, staleness, setup-sh, uv]
related: []
created: 2026-07-30
author: unknown
priority: P3
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: correct-codex
assigned_role: infra
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
locked_by:
resolved_by:
  unified-trading-pm@eff7413da (2026-08-06, ci_satellite_ao_dispatch_batch4); runtime-verified 2026-08-09 (5 passed / 0
  failed)
depends_on: []
source:
  - "found via git-stash pre-existing-failure baseline check while verifying
    scripts/quality-gates-base/base-service.sh/quickmerge.sh changes for ci_satellite_ao_dispatch_batch2 todo 1
    (2026-07-30) — confirmed identical failure on the unmodified tree, root-caused, not fixed inline (unrelated to that
    todo's scope)"
context_scope:
  [
    scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh,
    scripts/setup.sh,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
  ]
---

# uv-bootstrap-fallback test's structural anchor drifted from setup.sh's current text

## What I found

`scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh`'s structural-anchor assertion (line 50)
expects the extracted `[3] BOOTSTRAP UV` block from `setup.sh` to contain the literal substring
`pip install "uv==0.10.8"` (quoted). The actual current line in `setup.sh` is:

```bash
"$PYTHON_CMD" -m pip install uv==0.10.8 --quiet 2>/dev/null || pip install uv==0.10.8 --quiet 2>/dev/null
```

— unquoted, with a `--quiet` flag and a `$PYTHON_CMD -m` prefix branch the anchor pattern doesn't expect. Confirmed via
`bash scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh`: 4/5 assertions pass (both BEHAVIORAL
fixture cases — drifted-version realignment via the astral installer, already-pinned skip — are green); only the
structural anchor fails, and only because of this exact-substring mismatch. Verified pre-existing via `git stash` on an
unrelated session's changes: identical failure on the clean, unmodified tree.

## Why it matters

Low severity — the actual uv-pin-realignment BEHAVIOR this test protects is still correct and still covered by the two
passing fixture cases. But a permanently-red regression test is a broken window: it trains whoever next touches this
file to expect (and ignore) a failure here, which is exactly how a REAL future regression in this logic could slip
through unnoticed.

## Recommended decision

Update the `case` pattern at `scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh:50` to match the
current wording — e.g. drop the quote-and-adjacency assumption around `pip install "uv==0.10.8"` in favor of a looser
but still meaningful anchor (e.g. `*"pip install"*"uv==0.10.8"*`, matching presence + rough ordering without pinning the
exact quoting/flags), so a genuine future rewording of this line doesn't require another manual re-alignment.

## Todos

- [x] ✅ [SCRIPT] P3. Fix `scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh`'s structural-anchor
      `case` pattern (line 50) to match `setup.sh`'s current pip-fallback wording (unquoted `uv==0.10.8`, `--quiet`,
      `$PYTHON_CMD -m` prefix) instead of the stale quoted-literal expectation. Done when:
      `bash     scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh` reports 5/5 passed. **DONE —
      shipped via `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md`: `unified-trading-pm@eff7413da`
      (2026-08-06T17:18:14Z, "fix(qg): update uv bootstrap fallback test structural anchor to match setup.sh's current
      pip fallback"), confirmed a real ancestor of `origin/live-defi-rollout`. Live-verified 2026-08-09 (stale-recheck
      sweep): re-ran the test directly — `── result: 5 passed / 0 failed ──`. Batch4's own doc had already flipped this
      checkbox at the source (`status: active`) — this doc's citation-copy was simply never updated to match; closing
      that gap now.**

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-31** (tranche `ci`, autonomous): **KEEP-NA-STALE (already-duplicated).** This is a
textbook bounded/deterministic fix on its own merits (live-reverified: still 4/5 passed, same root cause). But the
sibling `/ag-closeout-audit ci` skill's same-day draft
`/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md` has **already extracted this exact sole todo
verbatim**, citing
`Source: issues/uv_bootstrap_fallback_test_structural_ anchor_stale_2026_07_30.md (sole todo) — never cited by any covering doc; a clean, small, previously-untriaged orphan.`
Reclassifying this doc's own `assigned_vm` now would open a second, independent dispatch path to the identical one-line
fix once batch4 activates. Staying NA until batch4 ships it or is archived unshipped (then re-open as RECLASSIFY on the
next pass). Same cross-skill population-overlap finding as `deployment_flow_doc_stale_pre_ldr_direct_mvp_2026_07_30.md`
— tracked in `/plans/active/issues/na_and_ag_closeout_audit_population_overlap_2026_07_31.md`.

**na-eligibility-audit 2026-08-02** (tranche `ci`, autonomous): **CONFIRMS KEEP-NA-STALE, unchanged.** Re-verified the
holding condition live rather than trusting the prior verdict: `ci_satellite_ao_dispatch_batch4_2026_07_31.md` still
carries this exact sole todo verbatim and is still `status: draft` — neither shipped nor archived-unshipped, so the
"re-open as RECLASSIFY" trigger has NOT fired. The only change to this doc since the last marker is the 2026-08-01
context-scout `context_scope` backfill (metadata only); the underlying defect is unchanged. Citation fix applied to the
open checkbox above this run.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA-STALE — fix extracted to ci_satellite_ao_dispatch_batch4_2026_07_31.md
(draft); re-open as RECLASSIFY if batch4 archives unshipped
