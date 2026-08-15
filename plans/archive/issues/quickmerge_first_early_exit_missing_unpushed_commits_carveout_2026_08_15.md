---
doc_type: issue
title:
  quickmerge.sh's FIRST early-exit (line ~1420) lacks the unpushed-commits-ahead-of-live-defi-rollout carve-out the
  SECOND early-exit (line ~2257) already has — a fix commit whose content matches origin/main silently fails to push
summary: >-
  Hit live 2026-08-15 while shipping a fix that reverted an accidental duplicate-commit collision back to
  content-identical with origin/main: quickmerge.sh's STAGE-3-adjacent early-exit at line ~1420 (`git diff origin/main
  --quiet`) exits 0 ("Nothing to commit — exiting fast") whenever the working tree matches origin/main, with NO check
  for commits already ahead of origin/live-defi-rollout. The second, later early-exit at line ~2257-2275 was fixed for
  exactly this scenario on 2026-06-10 (see its own comment: "Committed-ahead fall-through ... a clean tree with UNPUSHED
  commits used to early-exit here, stranding pre-committed QG-green work"), but that fix was never mirrored onto the
  first, earlier check, which runs first and short-circuits before the fixed check is ever reached.
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quickmerge, ci-cd, early-exit, shipping-pipeline, bug]
related: [/plans/active/issues/axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md]
created: 2026-08-15
author: slot-29 (backend_engineer)
source: ["axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md todo 2, dedup-collision cleanup"]
assigned_vm: planning
resolved_by: slot-14 (backend_engineer), unified-trading-pm@d66d9997f6, 2026-08-15
locked_by:
locked_since:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.06
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-15
parent_epic: agent_operating_framework_master
priority: P2
---

> **🟢 ARCHIVED 2026-08-15** — `status: resolved` with zero open todos; archived per
> [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)'s
> archive-on-resolve rule. Single `[x]` todo shipped: `_qm_early_exit_nothing_to_commit()` carve-out
> (unified-trading-pm@d66d9997f6) + hermetic bats regression coverage — no remaining prose open item.

# quickmerge.sh's first early-exit is missing the unpushed-commits-ahead-of-LDR carve-out

## What I found

Two slots (28 and 29) independently picked up the same plan todo (a dispatcher race — both booted the task before
either's commit was visible to the other) and both implemented the identical fix in `deployment-api`. Slot-28's commit
(`82b0469a7e`) landed first via quickmerge. Slot-29's commit (`7564785dd8`) landed moments later on top of it, unaware,
producing a duplicated `filters` variable declaration and a duplicate test method name (silently shadowing the first in
the same class — functionally harmless since both computed the same list, but genuine dead code).

Cleaning this up meant reverting the file back to content byte-identical with `82b0469a7e` — which, by the time the fix
was ready, had already promoted to `origin/main` via the routine LDR→main drain. So the cleanup commit's working-tree
content exactly matched `origin/main`, even though `origin/live-defi-rollout` (LDR, the actual integration trunk) still
carried the broken duplicate at its tip.

`scripts/quickmerge.sh` has TWO separate "nothing to merge" early-exit checks:

1. **Line ~1420** (before dependency install, early in the script):

   ```bash
   if [ "$NO_PR" != "true" ] && [ -z "$(git status --porcelain)" ] && git diff origin/main --quiet 2>/dev/null; then
     echo "[$REPO_NAME] Nothing to commit — exiting fast"
     exit 0
   fi
   ```

   This checks ONLY working-tree-vs-`origin/main` content. It has no awareness of `origin/live-defi-rollout` at all, and
   no carve-out for "clean tree, but HEAD has unpushed commits ahead of the integration branch."

2. **Line ~2257-2275** (later, inside STAGE 0.4/before STAGE 5): the same class of check, but this one — per its own
   comment — was fixed on 2026-06-10 for precisely this scenario:
   ```bash
   if [ -z "$(git status --porcelain)" ]; then
     # Committed-ahead fall-through (fixed 2026-06-10): a clean tree with UNPUSHED commits
     # used to early-exit here, stranding pre-committed QG-green work ...
     _UNPUSHED=$(git rev-list --count origin/live-defi-rollout..HEAD 2>/dev/null || echo 0)
     if [ "${_UNPUSHED:-0}" != "0" ]; then
       echo "[$REPO_NAME] clean tree with ${_UNPUSHED} unpushed commit(s) ahead of origin/live-defi-rollout — shipping the committed work"
       ...
   ```

Check 1 runs FIRST and unconditionally `exit 0`s before check 2 is ever reached, so its fixed logic never gets a chance
to apply. Any QG-green, committed, clean-tree fix whose end-state content happens to match `origin/main` (a realistic
case: reverting/undoing a bad commit, or a fix that converges back to already-promoted content) is silently dropped —
`quickmerge` reports success (exit 0, "Nothing to commit") without ever pushing the commit to LDR.

**Live impact measured 2026-08-15**: my cleanup commit (`709278c`, later rebased to `328d9bd`) sat unpushed while
`origin/live-defi-rollout`'s tip still had the broken duplicate. Had a routine LDR→main promotion cycle run before I
noticed and worked around it, the DUPLICATE/broken code would have been promoted onto `main`, silently regressing
already-clean content. Confirmed via `git diff origin/main -- <touched files>` returning empty on the affected commit
while `git rev-list --count origin/live-defi-rollout..HEAD` was 1.

**Workaround used (not a fix)**: bundled a genuine typing improvement (`filters: list[tuple[str, str, str]] = ...`) into
the same commit so it had real diff content vs `origin/main`, which let it through the first early-exit and land
normally via the standard quickmerge STAGE 5 push. This is a real, honest improvement, not filler — but it's an accident
that a fix was available to reach for; a pure revert-to-clean-state fix would have had no such escape hatch without
violating the raw-push ban.

## Why it matters

This is a fleet-wide gap — every repo ships through this same `quickmerge.sh` (symlinked from the PM SSOT), so ANY agent
shipping a commit whose net content converges back to what's already on `origin/main` (reverts, dedup fixes, undoing an
errant commit) can silently fail to land on LDR while quickmerge reports success. The failure mode is dangerous
specifically because it's SILENT (exit 0, a benign-sounding "Nothing to commit" message) rather than a hard failure an
agent would investigate — the standard `/done` verify step
(`git merge-base --is-ancestor "$SHA" origin/live-defi-rollout`) does catch it, but only if the agent actually runs that
check rather than trusting quickmerge's own "success" message (CLAUDE.md already warns against trusting quickmerge's own
message alone for a DIFFERENT reason — the STAGE-5-regate case — this is a second, distinct way the same
trust-but-verify rule pays off).

## Recommended decision

Mirror the line ~2257-2275 unpushed-commits carve-out onto the line ~1420 early-exit, OR simply delete the line ~1420
check entirely (the later, already-correct check at line ~2257 covers the same "nothing to merge" case correctly — the
earlier check appears to only exist as a cheap fast-path before the dependency-install step, so removing it costs one
`uv pip install -e .` call on the rare truly-nothing-to-ship path, which is a fine trade for closing a silent-data-loss
gap).

## Open work (tracked todos)

- [x] ✅ [BACKEND] P2. In `unified-trading-pm/scripts/quickmerge.sh`, fix the early-exit at line ~1420: either (a) add
      the same `git rev-list --count origin/live-defi-rollout..HEAD` unpushed-commits carve-out the line ~2257-2275
      check already has (skip the exit when `$_UNPUSHED != 0`), or (b) delete the line ~1420 check entirely and rely on
      the already-correct line ~2257 check. Add a regression test / manual repro: commit a change that reverts
      working-tree content back to `origin/main`-identical while `origin/live-defi-rollout` differs, confirm quickmerge
      now proceeds to STAGE 5 instead of silently exiting 0. (repo: unified-trading-pm) — unified-trading-pm@d66d9997f6.
      Extracted the check into `_qm_early_exit_nothing_to_commit()` (option a) mirroring the line ~2265 carve-out; added
      `tests/test_quickmerge_first_early_exit_unpushed_carveout.bats` (4 tests, hermetic, extracts + evals the real
      function) covering the exact bug scenario plus dirty-tree and content-diff non-regression cases.
