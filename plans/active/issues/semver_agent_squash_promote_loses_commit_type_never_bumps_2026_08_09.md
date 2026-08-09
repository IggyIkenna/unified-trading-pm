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

- [ ] [INFRA] P0. Patch `unified-trading-pm/.github/workflows/semver-agent.yml`'s Step 2/3 commit-range + bump
      classification per recommendation 1 and/or 2 above, add a regression test/dry-run against a synthetic squash-only
      commit range, then roll out via `scripts/cicd/rollout-workflow-templates.sh` to every repo. Repo:
      unified-trading-pm (template) + rollout to all.
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
