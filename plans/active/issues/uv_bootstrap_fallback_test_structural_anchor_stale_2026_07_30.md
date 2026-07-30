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
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, testing, staleness, setup-sh, uv]
related: []
created: 2026-07-30
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
depends_on: []
source:
  - "found via git-stash pre-existing-failure baseline check while verifying
    scripts/quality-gates-base/base-service.sh/quickmerge.sh changes for ci_satellite_ao_dispatch_batch2 todo 1
    (2026-07-30) — confirmed identical failure on the unmodified tree, root-caused, not fixed inline (unrelated to that
    todo's scope)"
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

- [ ] [SCRIPT] P3. Fix `scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh`'s structural-anchor
      `case` pattern (line 50) to match `setup.sh`'s current pip-fallback wording (unquoted `uv==0.10.8`, `--quiet`,
      `$PYTHON_CMD -m` prefix) instead of the stale quoted-literal expectation. Done when:
      `bash     scripts/quality-gates-base/tests/test-setup-sh-uv-bootstrap-fallback.sh` reports 5/5 passed.
