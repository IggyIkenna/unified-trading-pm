---
doc_type: issue
title: PM VERSION_SPLIT blocks every quickmerge CODE commit to unified-trading-pm (docs still land via safe-doc-push)
summary: >-
  quickmerge's dependency validation hard-failed on VERSION_SPLIT: PM is a version_source=git-tag repo, so its manifest
  versions{} is a CACHE of the minted tag — and it claimed 1.2.741 when the highest tag ever minted is v1.2.740.
  pyproject is never read for such repos. Fixed by aligning the cache to the real tag. Docs kept landing throughout
  (safe-doc-push skips dep validation), hiding the blockage.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quickmerge, versioning, workspace-manifest, ssot-contradiction, blocked]
related: [/codex/08-workflows/ci-cd-flow.md, /codex/06-coding-standards/semver.md]
created: 2026-08-10
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: infra
effort: medium
drift_direction: none
source: Hit while shipping the tool-call batching hook; quickmerge STAGE 1 refused the commit, 2026-08-10.
depends_on: []
last_updated: 2026-08-20
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    scripts/cicd/assert_version_coherence.py,
    scripts/repo-management/run-version-alignment.sh,
    workspace-manifest.json,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/semver.md,
  ]
---

# PM VERSION_SPLIT blocks quickmerge code commits

## Measured 2026-08-10 ~23:45

```
unified-trading-pm    1.2.741    1.2.509    NO-TAG    tag-MISS   <-- SPLIT
```

Columns are `versions | staging | source | tag?`. PM is declared **`version_source: git-tag`** in the manifest, which
changes what "source" means entirely:

| Surface                        | Value        | Relevant?                              |
| ------------------------------ | ------------ | -------------------------------------- |
| manifest `versions{}`          | **1.2.741**  | YES — it is a CACHE of the minted tag  |
| highest tag actually on origin | **v1.2.740** | YES — the real SSOT                    |
| `pyproject.toml` version       | 1.2.596      | **NO — never read for a git-tag repo** |

## Root cause

For a `version_source: git-tag` repo the git TAG is the version SSOT and `versions{}` is the Firestore-projected cache.
`assert_version_coherence.py` says it plainly: _"A manifest version with no matching tag IS the split (the cache claims
a version never minted)."_ The cache had run one release ahead of the tag — most likely a manifest update landing before
semver-agent minted `v1.2.741`.

**A wrong turn worth recording**: the checker's printed remedy is "Reconcile source pyproject.version FORWARD to the
manifest SSOT", which is the LEGACY static-version path and does not apply to a git-tag repo. Following it (editing
pyproject 1.2.596 -> 1.2.741) changed a file the checker never reads and left the split intact. `gh auth` was also
verified, ruling out a false `tag-MISS` from an API failure — worth checking, because `_has_tag()` returns False on any
API error, so an unauthenticated shell manufactures this exact symptom.

## Fix applied 2026-08-10

`versions{}` for unified-trading-pm: **1.2.741 -> 1.2.740** (align the cache to the highest minted tag), plus PM's
vestigial display scalar 1.2.724 -> 1.2.740. Two lines, no reformatting. This corrects a stale CACHE to match reality —
it is not a version bump, and it does not touch semver-agent's minting.

If the versions-consolidator later re-projects 1.2.741 from Firestore, that means Firestore also believes in an unminted
version, and the real defect is upstream in minting rather than here.

## Why the fix was kept narrow

- **Operator override, explicit.** CLAUDE.md's "NEVER bump manually (semver-agent)" rule was raised as a concern and the
  operator directed the hand edit three times. Recorded rather than silently done. What was actually changed is narrower
  than a bump: a projected CACHE corrected DOWN to the tag that exists.
- **Blast radius.** `workspace-manifest.json` is shared by every repo and 286 commits landed in four hours from
  concurrent agents, so the edit was kept to two lines with zero reformatting. An earlier attempt used `json.dumps()`
  and churned 82 unrelated lines (re-encoding `—` as `\u2014`); that was reverted. Never rewrite this file wholesale.
- **The 18 remaining vestigial-scalar drifts were left alone.** They are a display field the checker itself calls
  vestigial, they did not block the commit once the SPLIT cleared, and the documented remedy
  (`run-version-alignment.sh --fix`) rewrites dependency alignment across 19 repos — far more blast radius than the
  symptom warrants mid-session.

- [ ] [INFRA] P2. **Confirm the versions-consolidator does not re-project the unminted 1.2.741.** If it does, Firestore
      also believes in a version that was never tagged and the real defect is upstream in minting, not in this cache.
      **Done when**: a consolidator run leaves `versions{}` at a value with a matching tag, or the upstream minting gap
      is filed.
- [ ] [INFRA] P2. **Make the docs-vs-code asymmetry visible.** A repo whose code path is fully blocked while its docs
      path is wide open reads as healthy from commit volume alone; this hid for at least four hours while 286
      `docs(plans):` commits landed. **Done when**: something surfaces "code commits blocked" for a repo in this state
      (CI-status view, or a warn from safe-doc-push).
- [ ] [INFRA] P3. **Fix the checker's remedy text for `version_source: git-tag` repos.** It prints the legacy "reconcile
      pyproject.version FORWARD" advice, which for a git-tag repo edits a file it never reads and leaves the split
      intact — it cost a wrong fix here before the cause was found. **Done when**: the remedy branches on
      `version_source` and tells a git-tag repo to reconcile the cache/tag instead.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:5ca4525102390afb]: RECLASSIFY_WHOLE —
  `assigned_vm: NA` → `planning`. All 3 open todos are bounded engineering tasks with stated done-when bars; no
  operator gate, banner, or `depends_on` found. Root cause of the underlying incident already fixed.

- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
