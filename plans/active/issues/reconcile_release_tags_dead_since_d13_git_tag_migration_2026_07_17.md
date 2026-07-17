---
doc_type: issue
title:
  reconcile-release-tags has created ZERO tags since the D13 `version_source=git-tag` migration (2026-06-27) — it reads
  the version FROM pyproject.toml to decide which tag to CREATE, but D13 made the version DERIVE FROM the tag, so its
  input no longer exists
summary: >
  `reconcile-release-tags` is the fleet backstop that tags a released `main` whose tag was missed (it exists because
  tags WERE missed — see its own docstring citing the 2026-06-09 UTL reconcile and the 2026-06-11 keystone incident). It
  resolves each repo's version via `_main_version()` (reconcile_release_tags.py:73-93), which GETs
  `repos/{owner}/{repo}/contents/pyproject.toml?ref=main` and regex-matches a STATIC `version = "X.Y.Z"`. On 2026-06-27
  the fleet migrated to git-tag-derived versioning (`f4a3865e` in execution-service, "feat(cicd): migrate to
  version_source=git-tag (Phase-2/D13 fleet rollout)"), which REMOVED the static version from pyproject.toml in favour
  of `dynamic = ["version"]` + `[tool.hatch.version]` (hatch-vcs). `_main_version()` therefore matches nothing and
  returns None for every repo, and the reconciler reports `created 0 tag(s); 24 repo(s) had no main version` — on **20
  of the last 20 runs, character-for-character identical**. This is NOT a regex bug: it is an SSOT contradiction. D13
  made the TAG the source of truth and the version a DERIVED value; the reconciler reads the derived value in order to
  create the source of truth, which is circular and unsatisfiable by construction. Verified fleet-wide: all 6 sampled
  Python repos are `dynamic=1 hatch.version=1 static_version=0`. The auth is NOT the problem (unlike the sibling
  digest-drift-sweep bug) — the workflow correctly passes `GH_TOKEN: ${{ secrets.GH_PAT }}`
  (reconcile-release-tags.yml:70) and the fetch returns HTTP 200. Cadence `*/30` ⇒ ~48 runs/day x ~20 days ≈ 960 nominal
  (~770 at observed ~80% cron delivery) green runs that did nothing. NOT caused by the CI-cost runner flip (that touched
  only `runs-on:`); the flip is merely why the log was read. IMPACT IS BOUNDED: the PRIMARY tagging path
  (update-repo-version.yml) still works — tags exist and match the manifest (execution-service `versions=0.38.1`, tag
  `v0.38.1` present) — so this is a dead safety net, not active breakage. The fix is available in-place: the manifest's
  `versions` map already holds the authoritative version (25 entries), and the script ALREADY reads that manifest for
  the repo LIST (`_manifest_repos`, :154) — so the version lookup should come from the same manifest instead of from a
  field D13 deleted.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    ci-cd,
    release-tags,
    versioning,
    hatch-vcs,
    git-tag,
    d13,
    ssot-contradiction,
    silent-failure,
    green-but-wrong,
    backstop-rot,
  ]
related:
  [
    plans/active/github_actions_ci_cost_reduction_2026_07_15.md,
    plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md,
    codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-17
parent_epic: deployment_and_user_management_master
priority: P1
source:
  github_actions_ci_cost_reduction_2026_07_15 overnight validation, slot 1, 2026-07-17 — found while checking that the
  flipped workflows do REAL work rather than merely going green on the glue pool
assigned_vm: NA
execution_scope: local-only
assigned_role: devops
drift_direction: advance-code
last_updated: 2026-07-17
locked_by:
resolved_by:
depends_on: []
---

# reconcile-release-tags: the D13 migration deleted its input, and it has said "0 tags" ever since

## The contradiction, in one line

D13 made **the tag the source of truth** and the version a value **derived from it**. `reconcile-release-tags` reads
**the derived value** in order to **create the source of truth**. That is circular, and cannot ever succeed.

## Evidence

**20 of the last 20 runs, byte-identical:**

```
Release-tag reconcile: created 0 tag(s); 24 repo(s) had no main version.
```

A backstop reporting `created 0` is indistinguishable from a healthy backstop with nothing to do. That is why this sat
unnoticed for ~20 days. **`24 repo(s) had no main version` is the tell** — not the `0`.

**The cause is dated.** In `execution-service`:

```
f4a3865e 2026-06-27 feat(cicd): migrate to version_source=git-tag (Phase-2/D13 fleet rollout)
```

**Fleet-wide, not a one-repo quirk** — sampled `main` pyproject.toml:

| repo                | `dynamic = ["version"]` | `[tool.hatch.version]` | static `version = "X.Y.Z"` |
| ------------------- | ----------------------- | ---------------------- | -------------------------- |
| execution-service   | yes                     | yes                    | **none**                   |
| instruments-service | yes                     | yes                    | **none**                   |
| agent-orchestrator  | yes                     | yes                    | **none**                   |
| ml-service          | yes                     | yes                    | **none**                   |
| strategy-service    | yes                     | yes                    | **none**                   |
| features-service    | yes                     | yes                    | **none**                   |

`_VERSION_RE` requires a literal `version = "X.Y.Z"`. Post-D13 there is nothing for it to match.

**Auth is NOT the cause** — worth stating explicitly, because the sibling finding
(`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`) looks identical from the outside and is NOT the same
bug. Here the workflow correctly passes `GH_TOKEN: ${{ secrets.GH_PAT }}` (reconcile-release-tags.yml:70) and the fetch
returns HTTP 200 with real file content. The read succeeds; the field is simply gone.

## Impact — bounded, but the net is dead

The PRIMARY tagging path still works. `update-repo-version.yml` creates tags, and they are present and correct:

```
execution-service    manifest versions=0.38.1   tags: v0.38.1, v0.38.0, v0.37.0 …
instruments-service  tags: v0.90.0, v0.89.0 …
agent-orchestrator   tags: v0.98.0, v0.97.0 …
```

So nothing is actively broken today. What is gone is the **recovery path**: if `update-repo-version.yml` ever misses a
tag, nothing catches it any more — and this reconciler exists precisely because that has happened before (its docstring
cites the 2026-06-09 UTL reconcile and the ~20-version backlog drained during the 2026-06-11 keystone). We are running
without the safety net that those incidents motivated.

## Fix

**Do not "fix the regex" — there is no version in pyproject.toml to match.** Re-point the version lookup at the SSOT D13
actually left in place: `workspace-manifest.json`'s `versions` map, which holds 25 live entries
(`execution-service = 0.38.1`, …). The script **already reads that manifest** for the repo list (`_manifest_repos`,
:154), so this is a source swap inside `_main_version()` (:73-93), not a redesign.

Sequencing note: the first correct run will drain whatever real backlog has accumulated since 2026-06-27 — bounded by
the existing `--max-creates 5` cap, so it self-throttles across ticks rather than tagging the fleet at once. Confirm the
first run with `--dry-run` (the workflow already exposes a `dry_run` input) before letting the cron do it.

## Also fix the silent-failure class

Same lesson as the digest-drift-sweep finding, and the reason both went unseen for weeks: **a backstop that cannot look
must not report the same thing as a backstop that looked and found nothing.**

- `_main_version()` returning `None` conflates "repo has no pyproject" (benign — e.g. the TypeScript UIs), "fetch
  failed" (an error), and "version field absent" (a contract change). Distinguish them.
- Make the summary self-auditing: if `created == 0` **and** `skipped == len(repos)` — i.e. EVERY repo landed in the
  fallback bucket — that is not a healthy no-op, it is a broken lookup. Exit non-zero. That single assertion would have
  caught this on 2026-06-27, and would equally have caught the digest sweep.

## Cross-reference — a pattern worth naming

Two of the ten workflows audited for the CI-cost flip turned out to be long-dead silent no-ops, and **both are
backstops** (`digest-drift-sweep` = the digest-drift net; this = the missed-tag net). Neither was caused by the flip.
The common shape: **a safety net's healthy output and its dead output are the same string**, so the only thing that ever
reads it is a human who went looking. Both want the same remedy — an assertion that "I did nothing" and "I could not
look" are different states. Worth a codex note under the honest-absence rule
(`codex/02-data/honest-absence-downstream-handling.md`), which states this principle for data but is evidently a general
one.
