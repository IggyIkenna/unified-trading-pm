---
doc_type: issue
title:
  "QG STEP 5.101 (empty-string-fallback ratchet) baseline was seeded 1 site short for unified-trading-pm — blocked ALL
  quickmerge pushes to this repo"
summary: |
  Shipping an unrelated docs-only change (plans/active/issues/manifest_writer_dry_run_gcs_write_leak_2026_07_08.md
  Todo 3 flip) to unified-trading-pm, `bash scripts/quality-gates.sh` failed STEP 5.101 (the new baseline-ratchet
  empty-string-fallback check, shipped same-day in commit 13f17c203 "feat(qg): baseline-ratchet the empty-string-fallback
  check (STEP 5.101) instead of zero-tolerance") with "320 empty-string-fallback site(s) > baseline 319". Verified via a
  detached `git worktree` checked out at the exact seeding commit (13f17c203) that the live count was ALREADY 320 at
  that commit — i.e. the baseline was undercounted by 1 at the moment of its own creation, not drifted afterward. This
  is the same failure class already tracked in
  `plans/active/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` (Todo 3: "Check whether
  other repos have the same latent gap") — confirmed here for unified-trading-pm specifically.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, empty-string-fallback, baseline-ratchet, ci-blocking, seed-bug]
related:
  [
    mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md,
    manifest_writer_dry_run_gcs_write_leak_2026_07_08.md,
  ]
created: 2026-07-08
parent_epic: agent_operating_framework_master
priority: P3
source:
  [
    scripts/quality_gates/check_no_empty_string_fallback.py,
    scripts/quality_gates/no_empty_string_fallback_baseline.yaml,
    scripts/validation/validate-strategy-manifest.py:276,
  ]
assigned_vm: NA
resolved_by: slot-3 (2026-07-08)
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-08
---

## What I found

`scripts/quality-gates.sh` on `unified-trading-pm` failed STEP 5.101 with
`320 empty-string-fallback site(s) > baseline 319`, blocking quickmerge for a completely unrelated docs-only commit. The
`--update-baseline` mechanism cannot fix this by design — it clamps `min(observed, prior)`, so it can only ever ratchet
a baseline DOWN, never up to match a higher live count.

The reported "over-baseline" site (`scripts/validation/validate-strategy-manifest.py:276`) is not reliably "the new
site" — the checker sorts all sites alphabetically and reports whatever falls past index `[baseline:]`
(`check_no_empty_string_fallback.py:main`), so with a 1-off undercount it just reports whichever site happens to sort
last, not necessarily what changed. Confirmed via `git worktree add --detach <tmp> 13f17c203` (the exact commit that
seeded this baseline) + re-running the same checker against that checkout: it also reports 320, with zero code changes
since. **The baseline was undercounted at seed time**, not accumulated afterward.

## Why it matters

Same blast radius as the already-filed `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md`: until
fixed, **every** quickmerge push to `unified-trading-pm` fails QG, regardless of what the push touches.

## Resolution

Read `scripts/validation/validate-strategy-manifest.py:276` in context: `status = str(code.get("status", ""))` followed
by `if status in code_level_map:` (a closed set of `"C0".."C4"`) — an absent `status` key correctly falls through to "no
consistency check for this strategy", which is exactly the sanctioned safe pattern the checker documents ("field may
legitimately be absent; empty string is a meaningful not-present value the rest of the code correctly treats as
falsy/absent"). Annotated it `# noqa: qg-empty-fallback` with a one-line reason, dropping the live count to 319 (==
baseline). Verified: `check_no_empty_string_fallback.py --scope unified-trading-pm` → `[OK] 319 (== baseline)`.

## Todos

- [ ] [VERIFY] P3. Re-run `check_no_empty_string_fallback.py` workspace-wide (no `--scope`) against every repo's seeding
      commit the same way this issue did, to close out
      `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` Todo 3 ("check whether other repos have the
      same latent gap") in one pass instead of discovering them one push at a time. (repo: unified-trading-pm)
