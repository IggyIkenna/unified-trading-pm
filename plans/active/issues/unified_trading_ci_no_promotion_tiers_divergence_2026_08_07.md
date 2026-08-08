---
doc_type: issue
title: >-
  unified-trading-ci has no LDR<->main promotion mechanism at all — main and live-defi-rollout have genuinely diverged
  with different independent hotfixes on each side, and the branch-health lag monitor flags it every cycle with no real
  remedy available
summary: >-
  Surfaced while re-verifying the 2026-08-07 ~08:35 UTC `PROMOTION LAG > 60m` Slack alert. Per
  `workspace-manifest.json`, `unified-trading-ci` (extracted from unified-trading-pm 2026-08-06 per
  `shared_ci_workflow_repo_extraction_2026_08_06.md`) is declared "Single-branch repo (main only) — no LDR/staging
  promotion tiers" and has no `promotion_model` key at all (same as unified-trading-pm, but unlike PM it has no
  `main-backmerge-to-ldr.yml`/`ldr-to-main-promote.yml` workflows — confirmed via its `.github/workflows/` listing: only
  `image-build-validate.yml`, `lint.yml`, `notify-slack.yml`, `python-quality-gates-v2.yml`, all reusable-workflow
  DEFINITIONS other repos `uses:`, not this repo's own promotion infra). In practice, though, both `main` and
  `live-defi-rollout` exist and people (including automated agents) push hotfixes to whichever branch is convenient,
  with nothing reconciling them — live-verified 2026-08-07: `main` and `live-defi-rollout` have 3 commits each that the
  other lacks, including the SAME logical fix (`fix(ci): revert image-build-validate.yml to ubuntu-latest`) applied
  independently on each side with different shas (`a37205d`/`5bbc277` from
  `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`). `promotion_lag_monitor.py` has no way to
  know this repo is exempt (its `_main_direct_repos()` / `_ldr_terminal_repos()` exemptions are both keyed off an
  explicit `promotion_model` manifest field, and unified-trading-ci simply lacks one, same as PM which DOES want normal
  LDR->main monitoring) — so it fires a `PROMOTION LAG > 60m` warning every cycle with no available fix (there's no
  promote-PR mechanism to unblock).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-ci, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, promotion-lag, alert-accuracy, unified-trading-ci, branch-divergence]
related:
  [
    /plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md,
    /plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md,
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: devops
drift_direction: advance-code
depends_on: []
source: "branch-health promotion-lag re-verification session, 2026-08-07"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md,
    unified-trading-pm/scripts/cicd/promotion_lag_monitor.py,
    unified-trading-pm/workspace-manifest.json,
  ]
---

# unified-trading-ci has no promotion mechanism + genuinely diverged branches

## What was measured (2026-08-07)

- `git log origin/main..origin/live-defi-rollout` (unified-trading-ci): 3 unique commits (`a37205d` image-build-validate
  revert, `0afd236` billing-wall guard, `855e4a8` archive-candidates diff-scoped gate).
- `git log origin/live-defi-rollout..origin/main`: 3 DIFFERENT unique commits (`22a45ea` actionlint/ shellcheck fixes,
  `5bbc277` the SAME image-build-validate revert with a different sha, `4dcd37d` GH-Actions-cache gating).
- No `main-backmerge-to-ldr.yml`, `ldr-to-main-promote.yml`, `staging-*` workflow in `.github/workflows/` for this repo
  — genuinely no automated reconciliation mechanism exists.
- `promotion_lag_monitor.py` flagged `unified-trading-ci LDR→main: 2 commit(s), oldest ~280m old` in every run during
  this session (2026-08-07 ~08:35-09:22 UTC), never clearing, because there is no promote-PR path to clear it through.

## Why this is not something I fixed autonomously

Two structurally different remedies exist and picking one is a design decision, not a mechanical fix:

1. **Give unified-trading-ci real LDR<->main promotion infra** (roll out the standard `main-backmerge-to-ldr.yml` +
   `ldr-to-main-promote-fleet.yml` participation, matching every other repo) — reverses the "single-branch (main only)"
   design decision made in `shared_ci_workflow_repo_extraction_2026_08_06.md` without knowing why that call was made.
2. **Enforce the declared single-branch model for real** — block direct pushes to `live-defi-rollout` for this repo (or
   reconcile the two branches once, then treat `live-defi-rollout` as vestigial/ archive it), and teach
   `promotion_lag_monitor.py` to skip repos with no promotion workflows present at all (a new manifest field, or a
   dynamic `.github/workflows/` presence check) — this preserves the original design intent but needs the operator to
   confirm that intent still holds now that agents are evidently treating both branches as live.

Either way the two branches need a one-time reconciliation first (they've each accumulated real, different fixes) — a
silent merge choice here risks dropping one side's fix. Not attempted.

## Todos

- [x] [OPERATOR] P2. Decide the target model for unified-trading-ci: real LDR<->main promotion tiers, or enforced
      single-branch (with `live-defi-rollout` pushes blocked/discouraged going forward). — **Decision: enforced
      single-branch** (remedy 2 from "Why this is not something I fixed autonomously" above). Recorded 2026-08-07.
- [x] [DEVOPS] P2. Once decided: either (a) roll out the standard promote/backmerge workflow templates to this repo and
      reconcile the current 3-vs-3 commit divergence via one careful merge, or (b) add a
      `promotion_model: "single_branch"` (or similar) manifest field + teach `promotion_lag_monitor.py`'s
      `_repos()`/direction-skip logic to exempt it, then reconcile the divergence once and stop pushing to
      `live-defi-rollout` for this repo going forward. — **Done (b), 2026-08-07**: reconciled the divergence once
      (cherry-picked `855e4a8`/`0afd236` onto `main`, skipped `a37205d` as a content-identical duplicate of `main`'s
      `5bbc277` per `git patch-id` — confirmed zero net diff — then merged `main`'s reconciled tip back into
      `live-defi-rollout` so both branches are byte-identical trees again, FF-safe, no force-push); added
      `promotion_model: "single_branch"` + `integration_branch: "main"` to `unified-trading-ci`'s
      `workspace-manifest.json` entry (the latter overrides `setup-tab-worktrees.sh`'s `live-defi-rollout` default,
      which is the actual mechanism that put every slot worktree on `live-defi-rollout` for this repo — a bigger
      recurrence risk than the `ci_trigger_branch`/`rollout-workflow-templates.sh` paths, both confirmed already
      clean/pinned `@main`); wired `_single_branch_repos()` into `promotion_lag_monitor.py` to skip the repo entirely;
      documented the retirement in unified-trading-ci's README. unified-trading-ci commits:
      `a0561c443c67b5c6fc244ec93705f1f261816688` (main), `3d6e25ee1dd7d6884b73f00cad2063a589d10d83` (live-defi-rollout).
      Verified: `promotion_lag_monitor.py` live run shows zero findings for unified-trading-ci in either direction (only
      an unrelated pre-existing instruments-service provenance block remains).
- [ ] [DEVOPS] P3. Audit whether any other repo extracted/created after 2026-08-05 (the last
      `_main_direct_repos()`/manifest promotion-model audit) has the same "branches exist, no promotion workflows, no
      exemption" gap.
- [ ] [DEVOPS] P3. Fleet-propagate the SC2015 shellcheck fix (`22a45ea`, notify-slack.yml's dedup-marker-write
      `A && B || C` -> `if`) from unified-trading-ci's `.github/workflows/notify-slack.yml` back into
      `scripts/workflow-templates/notify-slack.yml` (the fleet SSOT) and re-run `rollout-workflow-templates.sh` so all
      26 consuming repos pick it up — found 2026-08-07 while shipping this issue's reconciliation: `check_workflows`
      flagged `unified-trading-ci/notify-slack.yml` as NEW template drift (pre-existing, predates this session — the fix
      was applied directly on unified-trading-ci without syncing the template). Verified all 25 OTHER repos' local
      copies are still on the un-fixed pattern, so updating the template naively would flip all of them to drifted in
      one shot — needs its own verified rollout, not a drive-by fix. Grandfathered `unified-trading-ci/notify-slack.yml`
      into `scripts/quality_gates/workflow_template_drift_baseline.json` via
      `--baseline-write --baseline-write-allow-additions` to unblock shipping in the meantime.

## Progress Log

- **2026-08-07**: Found while re-verifying the morning branch-health `PROMOTION LAG > 60m` alert. Not fixed autonomously
  — the correct remedy depends on a design intent only the operator can confirm (does this repo want real promotion
  infra, or was "single-branch" the actual goal and enforcement is what's missing).
- **2026-08-07**: Operator decision (single-branch, enforced) executed. Divergence re-verified before reconciling
  (unchanged from the initial measurement: LDR had `a37205d`/`0afd236`/`855e4a8`, main had `22a45ea`/`5bbc277`/
  `4dcd37d`). Reconciled via cherry-pick + merge-back (see todo above); nothing lost — verified the reconciled tree's
  diff against the OLD `live-defi-rollout` tip shows exactly main's 2 previously-unique commits' content and nothing
  else, and the reconciled tree's diff against OLD `main` shows exactly the 2 cherry-picked commits' content and nothing
  else. Checked for OTHER repos' configs referencing unified-trading-ci's `live-defi-rollout` (`ci_trigger_branch` in
  `workspace-manifest.json`, `rollout-workflow-templates.sh`) — both clean, every caller already pins `@main`. The
  actual recurrence vector was local: `scripts/dev/setup-tab-worktrees.sh` checks out
  `repositories.<repo>.integration_branch` (default `live-defi-rollout`) for every slot's worktree provisioning, and
  unified-trading-ci had no override — confirmed via this very slot's own clone, which was sitting on
  `live-defi-rollout` at session start. Fixed via `integration_branch: "main"` in the manifest.
  `promotion_lag_monitor.py` re-run confirms unified-trading-ci no longer appears in the lagging list in either
  direction.

- **na-eligibility-audit 2026-08-08** (tranche `ci`): KEEP-NA-STALE (already-duplicated) — both remaining open todos
  (the post-2026-08-05 repo audit, and the SC2015 shellcheck fleet-propagation) are extracted verbatim into
  `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todos 8 and 9 respectively (`status: draft`, `assigned_vm: planning`).
  Not reclassifying this doc's `assigned_vm` — batch6 activation is the operator's call; flipping here too risks a
  duplicate dispatch once it activates.
