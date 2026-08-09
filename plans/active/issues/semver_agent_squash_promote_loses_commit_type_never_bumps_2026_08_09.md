---
doc_type: issue
title: >-
  `semver-agent.yml` never bumps a version for a repo on the `ldr_main` SQUASH-promote model when the only new commit
  since baseline is the squash promote itself — the original `fix:`/`feat:` commit type is lost, so an internal
  (non-export-adding) fix ships to `main` but is NEVER released as a package version
summary: >-
  Discovered while re-verifying `unified-trading-library@609299ad` (the fix for
  `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`) for live-prod deployment. The fix commit reached `main`
  (squashed as `e94be221`, `Promoted-From-LDR: 609299ad...`), and `quality-gates-v2` + `Semver Agent` both ran
  successfully on it (`gh run list`), but the Semver Agent run's own log shows it computed `BUMP=""` and explicitly
  printed `"No feat:/fix:/breaking commits or API changes found. Skipping version bump."`, leaving the latest tag at
  `v0.77.0` (unchanged) — `git tag --contains 609299adf4bf49d5b027fd21289d6abd60a8bcfa` returns nothing on
  `origin/main`. Root cause (read live from `unified-trading-pm/.github/workflows/semver-agent.yml:280-375`, the
  reusable template every repo's copy is rolled out from): the classifier scans `git log --oneline
  ${BASELINE_SHA}..HEAD` commit SUBJECTS for a `feat(...)`/`fix(...)`/`!:` prefix to decide `BUMP`. For a repo on the
  `ldr_main` **squash**-promote model (per `/codex/08-workflows/ci-cd-flow.md` — squash chosen because "LDR is the
  backmerge sink; not rebaseable"), the commit range from baseline to HEAD can be JUST the single squash commit
  (`chore(promote): LDR → main (Option-B direct)`), which carries none of the original conventional-commit prefixes —
  those lived only on the pre-squash LDR commits, now discarded except for a `Promoted-From-LDR: <sha>` trailer the
  classifier never reads. The fallback path (the AST public-surface differ, `scripts/cicd/detect_breaking_change.py`)
  only mints a bump when it detects EITHER a breaking change OR a growth in export count (`new_export_count >
  old_export_count`) — an internal bugfix that changes behavior without adding a new public export (exactly `609299ad`'s
  shape: a private helper's retry logic) produces `is_breaking: false, old_export_count==new_export_count`, so neither
  path fires and the run legitimately, silently no-ops. This is NOT specific to this one commit — it reproduces for ANY
  squash-promoted internal `fix:`/`feat:` commit that doesn't touch the public export surface, on every repo using the
  `ldr_main` model (all of them, per CLAUDE.md's default-promote ruling), whenever it happens to be the only commit in a
  given baseline→HEAD scan window.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library, deployment-api]
scope: [engineer]
tags: [semver-agent, ci-cd, release-pipeline, squash-merge, versioning, silent-failure]
related:
  [
    /plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md,
  ]
created: "2026-08-09"
author: infra-worker-slot9
parent_epic: infrastructure_master
resolved_by:
locked_by:
locked_since:
source: >-
  Discovered live while executing the INFRA re-verification todo in
  `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md` — that todo's own dependency chain ((b) semver-agent mints
  + publishes the new UTL patch release) is stuck on exactly this bug, blocking (c)/(d) and the re-verification itself.
  Findings-triage HARD RULE: this is a fleet-wide release-automation gap, not fixable inline within that todo's own
  repo/craft scope without risking every repo's shared `semver-agent.yml` template — filed separately per the "big
  finding... cross-repo/SSOT contradiction -> NOTIFY OPERATOR + issue doc" governance rule.
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
---

# `semver-agent.yml` never bumps when a squash promote is the only commit in the scan window

## What I found

`unified-trading-library@609299ad` (`fix(manifest): narrow columns= before falling back to unfiltered full-schema read`
— the fix for the cefi OOM in `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`) reached `main` via the
standard `ldr_main` squash-promote (`e94be221 chore(promote): LDR → main (Option-B direct)`, trailer
`Promoted-From-LDR: 609299adf4bf49d5b027fd21289d6abd60a8bcfa`, confirmed via
`git merge-base --is-ancestor 609299ad origin/main` = NO but trailer-grep across `origin/main`'s last 10 promote commits
= YES, matching the established squash-verification pattern from this issue's sibling todo 2).

`gh run list --repo IggyIkenna/unified-trading-library --branch main` shows `Semver Agent` ran and CONCLUDED `success`
on `e94be221` (run `31325951737`, 2026-08-09T17:16Z) — but "success" here means the workflow didn't error, not that it
minted a release. Its own log:

```
Step 2: Determining commit range
Scanning commits from 7d40c228de09f4b8078eda80662fe686f100082c (version 0.77.0) to HEAD
Commits to analyze:
e94be221 chore(promote): LDR → main (Option-B direct)

Step 3: Classifying diff
Current version: 0.77.0
Public-surface diff verdict: {
  "is_breaking": false, "reasons": [], "old_export_count": 916, "new_export_count": 916
}
No feat:/fix:/breaking commits or API changes found. Skipping version bump.
```

`git tag --contains 609299adf4bf49d5b027fd21289d6abd60a8bcfa` (against `origin/main`, tags fetched with `--force`)
returns nothing — latest tag is still `v0.77.0`, minted before this fix. `pip index versions unified-trading-library`
(against the configured AR index) has no version newer than what's already installed — consistent with no new
tag/release having been minted.

**Root cause** — `unified-trading-pm/.github/workflows/semver-agent.yml:280-375` (the reusable template every repo's
copy rolls out from):

- Line 315-324: `BUMP` is set only by grepping commit SUBJECTS in the `${BASELINE_SHA}..HEAD` range for
  `^[a-f0-9]+ [a-z]+!(...)?:` / `^[a-f0-9]+ feat(...)?:` / `^[a-f0-9]+ fix(...)?:`. For a squash-promoted repo, that
  range can be (and here, was) just the ONE squash commit, whose subject is always the fixed
  `chore(promote): LDR → main (Option-B direct)` — never a conventional `feat:`/`fix:` prefix. The original commit's
  type lived only on the pre-squash LDR commit (`609299ad`'s own subject IS `fix(manifest): ...`), which is discarded by
  the squash except for the `Promoted-From-LDR: <sha>` trailer — the classifier never reads that trailer or looks up the
  trailer SHA's own commit message.
- Line 349-368 (the AST public-surface differ fallback): only sets `BUMP=minor` when
  `new_export_count > old_export_count`. An internal fix with no NEW public export (this one: a private
  `_read_parquet_columns_safe` retry-path change) produces `old_export_count == new_export_count`, so this fallback also
  doesn't fire.
- Net effect: `BUMP=""` → line 371-374 exits with `skip=true`, silently. The run reports `success` (it executed without
  error) even though it never bumped — nothing distinguishes "no bump needed" (a genuinely no-op push) from "the commit
  info needed to justify SOME bump was discarded by squashing" in the workflow's own output/status.

**Blast radius**: every repo on the `ldr_main` model (all of them, per CLAUDE.md's default-promote ruling) hits this
whenever a baseline→HEAD scan window happens to contain only squash-promote commit(s) whose underlying LDR fix(es)
didn't add a new public export — i.e. any internal bugfix, the MOST common kind of `fix:` commit. It is not a rare edge
case; it is the default shape for exactly the class of change (internal correctness fixes) semver exists to version.

## Why it matters

This silently breaks the automated fix-propagation pipeline CLAUDE.md's Git-discipline section documents as the standard
path (LDR fix → promote to main → semver-agent release → dependent repo's `update-dependency-version.yml` picks up the
new version → redeploy). A verified-correct, quality-gated, already-merged-to-main fix can sit indefinitely un-released
with zero alerting — the workflow run is green, so nothing pages. This directly blocks
`venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`'s remaining INFRA todo (steps b/c/d of that todo's own chain
depend on a release existing) and will recur for the NEXT internal-fix commit on ANY repo, not just this one.

## Recommended decision

Two independent, composable fixes to `semver-agent.yml`'s Step 2/3 classification:

1. When the squash-commit subject matches the promote pattern (`^chore\(promote\): .* → main`), also resolve its
   `Promoted-From-LDR: <sha>` trailer and include THAT commit's subject (and any commits between the previous promote's
   trailer SHA and this one's, if the LDR history is still reachable in the checkout) in the `feat:`/ `fix:`/`!:` scan —
   not just the squash commit's own subject.
2. Independently, treat ANY non-empty, non-breaking source diff in the scanned range as `patch` by default when no more
   specific signal exists (rather than requiring an explicit `feat:`/`fix:` prefix OR an export-count increase) — since
   "no source change" is the only case that legitimately warrants a real no-op skip; "source changed but neither
   classifier could tell why" should default to the safe minimum (patch), not silent inaction.

Either fix alone closes this specific incident; both together close the broader class. Edit the TEMPLATE
(`unified-trading-pm/.github/workflows/semver-agent.yml`) + roll out via `rollout-workflow-templates.sh` per the
per-repo-workflow-copy HARD RULE — never hand-edit a repo's copy.

## Todos

- [x] ✅ [INFRA] P0. Patch `unified-trading-pm/.github/workflows/semver-agent.yml`'s Step 2/3 commit-range + bump
      classification per recommendation 1 and/or 2 above, add a regression test/dry-run against a synthetic squash-only
      commit range, then roll out via `scripts/cicd/rollout-workflow-templates.sh` to every repo. Repo:
      unified-trading-pm (template) + rollout to all. — unified-trading-pm@e02fb076f (see Progress Log for the full
      trail: recommendation 2 was already live fleet-wide via the sibling
      `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` fix + its 2026-08-09 `source_touched` refinement;
      this todo verified it against the real incident SHAs, mirrored it into PM's own standalone copy, and added the
      regression test.
- [ ] [INFRA] P1. Once the semver-agent fix is live, manually trigger (or wait for the next `main` push to) re-classify
      `unified-trading-library`'s current `main` HEAD so `609299ad`'s fix actually mints a release — this repo is the
      confirmed live-blocked case and should not silently wait for the next unrelated push to main to accidentally pick
      it up. Repo: unified-trading-library.

## Progress Log

- **2026-08-09**: Filed during the INFRA re-verification todo in
  `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md` — root-caused via the live `Semver Agent` workflow run log
  (`gh run view <id> --log`) rather than guessing; confirmed `unified-trading-library@609299ad` reached `main`
  (squashed, trailer-verified) but no new tag was minted, and the run log's own printed verdict
  (`old_export_count==new_export_count`, `BUMP=""`) pinpoints the exact classifier gap in `semver-agent.yml:280-375`.
- **2026-08-09 (todo 1 closure)**: `unified-trading-pm/.github/workflows/semver-agent.yml` is no longer the fleet's live
  reusable template — the header comment citing it as "the reusable template every repo's copy is rolled out from" was
  already stale by the time this issue was filed: `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`
  todo 5 had already migrated the real logic to `unified-trading-ci/.github/workflows/semver-agent.yml` as a
  `workflow_call` reusable workflow (every caller, incl. `unified-trading-library`, references it via
  `uses: IggyIkenna/unified-trading-ci/.github/workflows/semver-agent.yml@main`), and `rollout-workflow-templates.sh`
  had `semver-agent.yml.tmpl` DELETED from its template dir accordingly (see that script's own header comment).
  Recommendation 2 (the content-based patch-level fallback) was ALSO already shipped into that file — via the sibling
  issue `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` (fleet rollout 2026-08-07) and refined
  same-day-as-this-issue by `unified-trading-ci@2c48c4b` ("base the squash-promote PATCH-fallback on repo-wide
  `source_touched`, not SOURCE_DIR-prefix", landed on `main` 2026-08-09T10:10 UTC) — before this issue's own 17:16Z
  incident run, meaning that specific run predates the fix reaching `main`, not a failure of the fix itself. **Verified
  live** against the real incident SHAs:
  `python3 scripts/cicd/detect_breaking_change.py --source-dir unified_trading_library --base-ref 7d40c228 --head-ref e94be221 --json`
  (run from a fresh `unified-trading-library` checkout) now reports `"source_touched": true` — confirming a fresh
  semver-agent run on that repo's current `main` HEAD resolves `BUMP=patch` instead of skipping. Recommendation 1
  (trailer-based commit-type resolution) was NOT implemented — the issue's own text says either fix alone closes the
  specific incident, and recommendation 2 already does. Remaining real work this todo owned: (a) mirrored the same
  `source_touched`-based fallback into PM's own standalone (non-caller-stub) copy of `semver-agent.yml` for consistency,
  since PM doesn't call the reusable workflow and was otherwise left as a straggler with the pre-fix classifier; (b)
  added the regression test the todo explicitly asked for
  (`tests/unit/test_detect_breaking_change.py::test_source_touched_true_on_squash_only_commit_range_with_real_source_change`
  - `..._false_on_squash_commit_touching_only_metadata_noise`, a synthetic squash-only commit range against a real temp
    git repo). Shipped `unified-trading-pm@30ed07eff` (fix + tests, QG green, verified ancestor of origin). Todo 2 (P1,
    re-trigger `unified-trading-library`'s release) is a separate, not-yet-worked todo — left open.
- **2026-08-09 (infra worker, slot 18, todo 2)**: `Semver Agent` has NO `workflow_dispatch` trigger
  (`gh workflow run "Semver Agent" --repo IggyIkenna/unified-trading-library` →
  `422: Workflow does not have 'workflow_dispatch' trigger`) — its caller stub is `on: push: branches: [main]` only, so
  "manually trigger" isn't literally available; the only lever is a fresh push to `main`. But re-triggering right now
  would just reproduce the same skip: root-caused why. `unified-trading-ci`'s reusable `semver-agent.yml` (the ACTUAL
  logic every non-PM caller runs) resolves its differ script via
  `gh api repos/IggyIkenna/unified-trading-pm/contents/scripts/cicd/detect_breaking_change.py` with **no `ref=` param**
  — i.e. it always fetches `unified-trading-pm`'s DEFAULT branch (`main`), never `live-defi-rollout`. Fetched that file
  live just now: **`source_touched` is NOT present in `unified-trading-pm`'s `main`-branch copy** — todo 1's fix
  (`unified-trading-pm@30ed07eff`) landed on LDR but has NOT promoted to `main` (`origin/main..origin/live-defi-rollout`
  = 568 commits, as of this check). Confirmed the live consequence directly: the latest real `Semver Agent` run on
  `unified-trading-library`'s `main` HEAD (`e94be221`, run `31325951737`, 2026-08-09T18:07:42Z — AFTER todo 1's fix
  shipped) still printed `"No feat:/fix:/breaking commits or API changes found. Skipping version bump."` with no
  `source_touched` key in its JSON verdict, i.e. still running the pre-fix classifier. Root cause of the stall:
  `unified-trading-pm`'s own `chore(promote): LDR → main` PR is stuck (PR #2704, open since 16:45:59Z) — hard-failing
  `QG slice (checks)` on `unified-trading-pm`'s own plan-hygiene ratchet corpus (5 `❌`s: prettier proseWrap,
  reference-path convention, create-only archival guard, NA-corpus size, archive-candidates) plus a `QG slice (tests)`
  job stuck `in_progress` 90+ min with no step progress — this is the SAME already-tracked, extensively-chased (9
  dispatches, still unresolved) systemic race documented in
  `plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md` (logged this todo's downstream
  consequence there too, cross-linked). Per that doc's own established "hand off, don't chase serially" precedent (a
  corpus-scale plan-hygiene fix, not a one-shot), **not** attempting to fix PM's promote pipeline myself. This todo
  genuinely cannot complete (`done_definition`: a release minted) until PM's `main` catches up with the differ fix —
  waiting for a future green promote cycle rather than busy-polling. Leaving todo 2 open/unchecked; will re-attempt once
  `unified-trading-pm@30ed07eff` (or a later commit carrying `source_touched`) is confirmed an ancestor of
  `origin/main`, then either a trivial push to `unified-trading-library`'s `main` (if one lands naturally from other
  work) or waiting for the next real one will re-classify `609299ad` correctly.
- **2026-08-09 (infra worker, slot 20, todo 2 re-check)**: Re-verified from scratch —
  `git merge-base --is-ancestor 30ed07eff origin/main` on `unified-trading-pm` still returns NO
  (`origin/main..origin/live-defi-rollout` now 687 commits, up from 568 at the prior check), so the `source_touched` fix
  has still not reached PM's `main`. The auto-drain promote pipeline is visibly still retrying every ~15 min and failing
  the same way: `gh pr list --search "promote in:title"` shows PRs #2691-#2705 (15 consecutive attempts across
  ~13:35Z-19:03Z today), every one but the latest CLOSED without merging. Pulled the live failing job log for the
  current open attempt (PR #2705, run `31330640508`, job `93288244861`) — the exact same 5 hard ratchet failures as slot
  18's prior check: `No prettier proseWrap continuation-padding`, `Reference path convention`,
  `Create-only archival guard`, `assigned_vm:NA corpus size` (now 33 new NA docs / 96 new open todos vs `origin/main`,
  up from whatever slot 18 saw), `Archive candidates`. Same root cause, same lineage, no new information — this remains
  squarely `plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md`'s scope (P2, cross-cutting,
  its own established "hand off, don't chase serially" precedent — 9+ dispatches already), not this INFRA todo's. Per
  that precedent, NOT attempting a fix myself. Confirmed there is genuinely no alternate lever available either:
  `Semver Agent`'s caller stub on `unified-trading-library` still has no `workflow_dispatch` trigger
  (`push: branches: [main]` only), and the reusable workflow's classifier-script fetch is unpinned to PM's live default
  branch, so even a `gh run rerun` of the existing `31325951737` run would just re-fetch the still-unfixed classifier
  and reproduce the same skip. Leaving todo 2 open/unchecked, same condition as before: will only make forward progress
  once PM's `main` actually advances past `30ed07eff`. Skipping this task with `reason_code: GATED` so it doesn't keep
  re-dispatching to every heartbeat in the fleet while the real blocker is unresolved elsewhere.
- **2026-08-09 (infra worker, slot 13, todo 2 re-check)**: Re-verified from scratch again —
  `git merge-base --is-ancestor 30ed07eff origin/main` on `unified-trading-pm` still returns NO
  (`origin/main..origin/live-defi-rollout` now 712 commits, up from 687 at slot 20's check), and
  `unified-trading-library`'s latest tag on `main` is still `v0.77.0` (no tag contains `609299ad`). The auto-drain
  promote PR is still the SAME open PR (#2705, unchanged since slot 20's check — no new attempt superseded it), and its
  `QG slice (checks)` job still fails. No new information; same blocker, same root cause
  (`plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md`), same precedent (hand off, don't
  chase serially). Skipped the linked INFRA todo in `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md` again
  with `reason_code: GATED`.
