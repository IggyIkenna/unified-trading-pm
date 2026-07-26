---
doc_type: issue
title: >-
  hatch-vcs version on `main` is computed from a tag NOT reachable from main's squashed history — breaks any fresh
  cross-repo `pip install -e` of UAC against a package requiring the current release floor
summary: >-
  Extending unified-trading-system-ui's registry-drift CI job (defi_wizard_batch2_018_residual_findings-004), `pip
  install -e _deps/unified-api-contracts -e _deps/unified-trading-library` (a pre-existing, unrelated step also used by
  the established ui-reference-data.json check) hard-fails with `ResolutionImpossible` on a FRESH checkout of UAC's
  `main` branch: hatch-vcs resolves `unified-api-contracts` to `0.71.1.dev158+gb22f9fca2`, but unified-trading-library
  declares `unified-api-contracts<1.0.0,>=0.72.0` — a real version floor the fresh-clone resolves BELOW. Root cause
  (confirmed via `git describe --tags` + `git merge-base --is-ancestor`): the `v0.72.0` tag is NOT an ancestor of UAC's
  `main` HEAD (`b22f9fca`) — `git merge-base --is-ancestor v0.72.0 origin/main` returns false — while it IS an ancestor
  of `live-defi-rollout` (`git describe --tags origin/live-defi-rollout` → `v0.72.0-646-g2ded0993`). `main`'s
  squash-merge promotion history (each promote is one squash commit whose parent is the PREVIOUS squash commit, not the
  individual LDR commits) has structurally "lost" the ancestor path to that tag, so `git describe`/hatch-vcs walking
  `main`'s own graph falls back to the older `v0.71.0` and computes a dev-distance from there instead — permanently
  below any downstream floor pinned at `>=0.72.0`, for as long as this ancestry gap persists on `main`. **This is NOT
  the "528 commits behind" false alarm I almost filed** — `git diff --stat origin/main origin/live-defi-rollout` and
  `git rev-parse origin/main^{tree}` vs `origin/live-defi-rollout^{tree}` for UAC (and UTL, unified-trading-system-ui,
  strategy-service, execution-service, features-service, checked as a sanity sweep) are all byte-identical trees right
  now — content-wise `main` is fully caught up (the promotion pipeline itself is healthy); this is purely a
  **version-string** defect caused by squash-merge breaking `git describe`'s tag-ancestor walk, distinct from (but same
  class as, and possibly related to) the tag-mechanism issues already tracked in
  `reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md` and
  `promotion_lag_alert_hides_provenance_block_2026_07_17.md`.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, unified-trading-pm, unified-trading-system-ui]
scope: [engineer]
tags: [cicd, hatch-vcs, versioning, git-tag, squash-merge, pip, dependency-resolution, registry-drift]
related:
  [
    /plans/active/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md,
    /plans/active/issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md,
    /plans/active/issues/defi_wizard_batch2_018_residual_findings_2026_07_26.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-26
parent_epic: infrastructure_master
priority: P2
estimate_class: infra
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
source:
  [
    unified-trading-system-ui/.github/workflows/ci.yml,
    unified-api-contracts/pyproject.toml,
    unified-trading-library/pyproject.toml,
  ]
---

## What I found

While verifying the `registry-drift` CI job extension for `capability-manifest.json`
(`defi_wizard_batch2_018_residual_findings-004`) against a real GHA run, the pre-existing
`pip install -e _deps/unified-api-contracts -e _deps/unified-trading-library` step (used by BOTH the established
`ui-reference-data.json` drift check and my new `capability-manifest.json` one) failed with:

```
ERROR: Cannot install unified-api-contracts 0.71.1.dev158+gb22f9fca2 (from editable ...) and
unified-trading-library==0.57.1.dev5+gc2ce80145 because these package versions have conflicting
dependencies.
The conflict is caused by:
    The user requested unified-api-contracts 0.71.1.dev158+gb22f9fca2
    unified-trading-library 0.57.1.dev5+gc2ce80145 depends on unified-api-contracts<1.0.0 and >=0.72.0
```

Confirmed via `gh run view --log` this has been failing this exact way (or a shallow-clone variant, see below) on every
`registry-drift` run on `unified-trading-system-ui`'s `main`/promote PRs going back to at least 2026-07-21 — pre-dating
and unrelated to my capability-manifest.json work.

**Two layered bugs, not one:**

1. **Shallow-clone fallback (I fixed this half in the CI job)**: the sibling checkouts (UAC, UTL, execution-service,
   features-service, strategy-service) didn't set `fetch-depth: 0`, so hatch-vcs saw NO tags at all and fell back to a
   bogus `0.1.dev1+<sha>`. Fixing `fetch-depth: 0` surfaced the REAL version instead (`0.71.1.dev158+gb22f9fca2`) —
   progress, but still below the `>=0.72.0` floor, so the install still fails.

2. **Tag-ancestry gap on `main` (this is the actual remaining blocker, NOT mine to fix)**:

   ```
   $ git describe --tags origin/main            # v0.71.0-158-gb22f9fca
   $ git describe --tags origin/live-defi-rollout # v0.72.0-646-g2ded0993
   $ git merge-base --is-ancestor v0.72.0 origin/main            # NOT an ancestor
   $ git merge-base --is-ancestor v0.72.0 origin/live-defi-rollout # IS an ancestor
   ```

   The `v0.72.0` tag exists in the repo but is unreachable from `main`'s own commit graph. UAC's `main` is built
   entirely from LDR→main squash-merge commits (each promote = one squash commit whose parent is the PREVIOUS squash
   commit on `main` — per `ci-cd-flow.md`'s "LDR is the backmerge sink; not rebaseable" squash design). If `v0.72.0` was
   tagged on an LDR commit (or a main commit later superseded by a squash that doesn't include it as an ancestor),
   `git describe`/hatch-vcs walking `main`'s linear squash-commit history will never find it, and falls back to the next
   reachable tag (`v0.71.0`) — computing a version permanently below the current real release floor, for as long as this
   specific gap persists.

**This is NOT a promotion-lag / stalled-pipeline problem** — I initially mismeasured this as "UAC main is 528 commits
behind live-defi-rollout" using `git rev-list --count origin/main..origin/live-defi-rollout`, which is exactly the
squash-inflated `ahead_by` metric `ci-cd-flow.md` and `promotion_lag_alert_hides_provenance_block_2026_07_17.md` already
warn against (squash merges break commit-count ancestry even when content is fully caught up). Redid it with the correct
content-diff check and confirmed **all 6 repos I sampled (UAC, UTL, unified-trading-system-ui, strategy-service,
execution-service, features-service) have byte-identical trees between `main` and `live-defi-rollout` right now**
(`git rev-parse origin/main^{tree}` == `origin/live-defi-rollout^{tree}` for every one). The promotion pipeline itself
is healthy; only the derived VERSION STRING is wrong for UAC specifically, because of the tag ancestry gap above.

## Why it matters

Any fresh CI checkout of `main` (not `live-defi-rollout`) that does `pip install -e unified-api-contracts` alongside a
package pinned to the current real floor (`unified-trading-library` requires `>=0.72.0`) will permanently fail to
resolve, regardless of how many times the checkout is retried — it's not flaky, it's a structural consequence of the
tag-ancestry gap. This currently blocks:

- The established `ui-reference-data.json` registry-drift check (confirmed broken since ≥2026-07-21).
- My new `capability-manifest.json` registry-drift check (this session).
- Potentially any OTHER cross-repo consumer that checks out UAC's `main` fresh and pip-installs it editable alongside a
  version-floor-pinned sibling.

## Recommended decision

- [ ] [DEVOPS] P2. Diagnose exactly how/when `v0.72.0` was tagged and why it isn't an ancestor of `main`'s current
      squash-commit chain (repo: unified-api-contracts). Likely candidates: tag minted on an LDR commit directly
      (bypassing the squash boundary), or minted on an earlier `main` commit that a LATER squash-merge's parent chain
      doesn't include. Check `semver-agent.yml`'s tag-minting step (`push:[main]`) against the actual squash-commit
      timeline around when `v0.72.0` was created.
- [ ] [DEVOPS] P2. Once root-caused, decide the fix direction: (a) always tag on `main`'s own HEAD right after each
      squash-promote lands (never on an LDR-only commit), or (b) reconcile the existing gap by re-tagging `v0.72.0` (or
      a corrected release tag) onto current `main` HEAD if the tag is meant to represent "what's actually released on
      main" — do NOT silently move an existing tag without checking downstream consumers that may have already resolved
      a wheel against the old tag sha.
- [ ] [SCRIPT] P3. Once the tag-ancestry gap is fixed, re-run the `registry-drift` job on unified-trading-system-ui's
      `main`/next promote PR and confirm
      `pip install -e     _deps/unified-api-contracts -e _deps/unified-trading-library` succeeds (both the
      `ui-reference-data.json` AND `capability-manifest.json` diff steps should then execute for real, rather than the
      whole job dying at the install step).
- [ ] [DOCS] P3. Cross-link this doc from `reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md` and
      `promotion_lag_alert_hides_provenance_block_2026_07_17.md` — same hatch-vcs/git-tag subsystem, adjacent failure
      modes, worth a shared "known rough edges" note so the next diagnosis doesn't restart from zero.

## Provenance

Found 2026-07-26 while executing `defi_wizard_batch2_018_residual_findings-004` (extend `registry-drift` for
`capability-manifest.json`) — verifying the new CI job end-to-end against real GHA runs per that todo's explicit
instruction ("do not assume a config-only guess is correct"). Diagnosed read-only: `gh run view --log`,
`git describe --tags`, `git merge-base --is-ancestor`, `git diff --stat`, `git rev-parse ^{tree}` across 6 repos. No
repo was touched by this investigation; the `fetch-depth: 0` half-fix IS shipped as part of
`defi_wizard_batch2_018_residual_findings-004`'s own commit (unrelated bug, fixed because it blocked verifying my own
change and is a genuine independent improvement either way).
