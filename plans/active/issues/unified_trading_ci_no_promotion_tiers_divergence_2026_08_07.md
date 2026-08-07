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

- [ ] [OPERATOR] P2. Decide the target model for unified-trading-ci: real LDR<->main promotion tiers, or enforced
      single-branch (with `live-defi-rollout` pushes blocked/discouraged going forward).
- [ ] [DEVOPS] P2. Once decided: either (a) roll out the standard promote/backmerge workflow templates to this repo and
      reconcile the current 3-vs-3 commit divergence via one careful merge, or (b) add a
      `promotion_model: "single_branch"` (or similar) manifest field + teach `promotion_lag_monitor.py`'s
      `_repos()`/direction-skip logic to exempt it, then reconcile the divergence once and stop pushing to
      `live-defi-rollout` for this repo going forward.
- [ ] [DEVOPS] P3. Audit whether any other repo extracted/created after 2026-08-05 (the last
      `_main_direct_repos()`/manifest promotion-model audit) has the same "branches exist, no promotion workflows, no
      exemption" gap.

## Progress Log

- **2026-08-07**: Found while re-verifying the morning branch-health `PROMOTION LAG > 60m` alert. Not fixed autonomously
  — the correct remedy depends on a design intent only the operator can confirm (does this repo want real promotion
  infra, or was "single-branch" the actual goal and enforcement is what's missing).
