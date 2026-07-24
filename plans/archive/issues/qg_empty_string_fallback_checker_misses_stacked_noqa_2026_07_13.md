---
doc_type: issue
title:
  "QG STEP 5.101 (check_no_empty_string_fallback.py) fails to recognize a valid noqa: qg-empty-fallback suppression when
  it's a SECOND, separate noqa comment cluster on the same line — false-positive blocks pushes on already-suppressed
  sites"
summary:
  'Found 2026-07-13 while shipping an unrelated audit script in unified-trading-library: QG STEP 5.101 flagged
  `unified_trading_library/dev_paths.py:27` as a NEW over-baseline empty-string-fallback site, even though that exact
  line already carries `# noqa: qg-empty-fallback` (stacked as a second `# noqa: ...` comment after `# noqa:
  qg-os-env`). Root cause: `check_no_empty_string_fallback.py`''s `_has_empty_fallback_noqa()` uses
  `_NOQA_CODES_PATTERN.search(line)`, which returns only the FIRST `# noqa: ...` match on the line — a second, separate
  `# noqa: qg-empty-fallback` cluster later on the same line is never seen. The docstring even calls out handling "a
  multi-code one (`# noqa: qg-os-environ qg-empty-fallback`, or comma-separated)" — i.e. codes packed into ONE cluster —
  but never the two-SEPARATE-clusters style that this exact repo''s own `dev_paths.py` uses (and that its own docstring,
  "The env-read carries `# noqa` markers so callers do NOT need them", implies is a sanctioned idiom). Worked around by
  merging the two clusters into one (`# noqa: qg-os-env qg-empty-fallback`) in `unified-trading-library@<pending>`,
  which unblocked that push, but the checker bug itself is unfixed and will false-positive on any OTHER file using the
  two-separate-clusters style across the fleet.'
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, ci, false-positive, noqa, tooling-bug]
related:
  [
    /plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    scripts/quality_gates/check_no_empty_string_fallback.py,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P3
source: manifestwriter_unconditional_write_race_data_loss_2026_07_13.md P2 audit session, 2026-07-13
assigned_vm: planning
resolved_by: "slot-10, unified-trading-pm@74a098887"
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: advance-code
depends_on: []
---

## What I found

`check_no_empty_string_fallback.py`'s `_has_empty_fallback_noqa()` (line ~260) does:

```python
match = _NOQA_CODES_PATTERN.search(line)
if not match:
    return False
codes = re.split(r"[,\s]+", match.group(1).strip())
return "qg-empty-fallback" in codes
```

`_NOQA_CODES_PATTERN = re.compile(r"#\s*noqa:\s*([\w,\s-]+)")` and `.search()` returns only the first match. A line with
two SEPARATE `# noqa: X` clusters — e.g. `# noqa: qg-os-env  # noqa: qg-empty-fallback` — has its `qg-empty-fallback`
code sitting in the SECOND cluster, which `.search()` never reaches; `codes` only ever contains the first cluster's
codes (`["qg-os-env"]`), so the check incorrectly reports the line as NOT suppressed.

This is confirmed by direct read of `unified_trading_library/dev_paths.py:27` (pre-existing, last touched 2026-05-18 by
`semver-rollout[bot]`, not something I or any recent slot wrote): the line already carried a syntactically valid
`# noqa: qg-empty-fallback` suppression, yet QG STEP 5.101 reported it as a brand-new, over-baseline violation and
blocked the push.

## Why it matters

This is a **false positive that blocks legitimate pushes fleet-wide**, not scoped to unified-trading-library — ANY
repo/file using the two-separate-`# noqa:`-clusters style (which the gate's OWN docstring for the sibling `qg-os-env`
marker implies is an accepted pattern — see `dev_paths.py`'s own "The env-read carries `# noqa` markers so callers do
NOT need them" comment) will hit the same false block. It wastes agent/operator time re-diagnosing a "violation" that
was already correctly suppressed, and risks someone "fixing" it by rewriting working code instead of fixing the checker.

## Recommended decision

Fix `_has_empty_fallback_noqa()` to scan ALL `# noqa: ...` clusters on the line (e.g.
`_NOQA_CODES_PATTERN.finditer(line)`, union all their code-groups) instead of only the first `.search()` match.
Low-risk, single-function fix; add a regression test with a two-separate-clusters line (exactly `dev_paths.py:27`'s
shape) alongside the existing single-cluster/multi-code-in-one-cluster cases the docstring already documents.

## Todos

- [x] ✅ [BACKEND] P3. Fix `_has_empty_fallback_noqa()` in
      `unified-trading-pm/scripts/quality_gates/check_no_empty_string_fallback.py` to recognize a `qg-empty-fallback`
      code sitting in ANY `# noqa: ...` cluster on the line, not just the first `.search()` match — use
      `_NOQA_CODES_PATTERN.finditer()` and union the codes across all matches. Add a regression test covering the
      two-separate-clusters shape (repo: unified-trading-pm) — SHIPPED `unified-trading-pm@74a098887`. Switched
      `_has_empty_fallback_noqa()` to `finditer()` + union all clusters' codes (was `search()`, first-match-only). Added
      `scripts/quality_gates/test_check_no_empty_string_fallback.py` (new file — none existed for this checker) covering
      all 3 documented noqa shapes (single-code, multi-code-in-one-cluster, two-separate-clusters) plus 3 negative
      cases, 8 tests total, all passing. Full `quality-gates.sh` green, sentinel-verified. Took 14 attempts to actually
      land the push — the PM repo was under extreme fleet write contention this session (a new commit landing roughly
      every 1-3 min), and each rebase quickmerge's Stage-0.4 auto-pull performed created a NEW commit SHA for the same
      content, breaking the Pass-1 sentinel's ancestor-chain check every time (content verified byte-identical across
      all 14 attempts via `git diff`) — an infra/timing issue, not a code defect.

## Progress Log

- **2026-07-13 (slot-7, sonnet/high)** — Found while shipping the P2 audit script for
  `manifestwriter_unconditional_write_race_data_loss_2026_07_13.md`: QG STEP 5.101 blocked the push on 2 pre-existing
  sites in `unified-trading-library` (`dev_paths.py:27`, `pipeline_e2e_check/launcher.py:108`), neither touched by that
  task. Diagnosed `dev_paths.py:27` as a checker false-positive (already suppressed, just via a two-clusters `# noqa:`
  style the regex can't see past the first match) and worked around it in `unified-trading-library` by merging the two
  clusters into one recognized cluster; added a fresh, justified `# noqa: qg-empty-fallback` to `launcher.py:108` (a
  genuine fail-open case, not previously suppressed). Filed this issue for the checker bug itself so the fleet doesn't
  keep re-diagnosing the same false positive on other files using the same style.
