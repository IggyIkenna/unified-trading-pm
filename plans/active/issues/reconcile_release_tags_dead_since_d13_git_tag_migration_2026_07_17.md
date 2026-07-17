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

---

## UPDATE 2026-07-17 — RECOMMENDATION CHANGED: **DELETE it, do not fix it**

The original "Fix" section above proposed re-pointing `_main_version()` at the manifest's `versions` map. **That is
wrong.** Investigating the right version source surfaced that D13's intended model is already written down — in the
sibling tool that WAS migrated. Three findings kill the reconciler outright.

### 1. Its remedy is backwards under D13

`scripts/cicd/assert_version_coherence.py:206-210` (migrated for D13) states the model verbatim:

> _"Phase-2 (D13) dynamic repo: the version SSOT is the git TAG; `versions{}` is the Firestore-projected cache (the
> versions-consolidator keeps `versions{}` == Firestore). Coherence = the tag `v{versions{}}` EXISTS, i.e. tag ==
> Firestore-projection. There is NO pyproject version line to read (dynamic), and staging is not the source. **A
> manifest version with no matching tag IS the split (the cache claims a version never minted).**"_

So under D13, "a manifest version with no tag" means **the cache is lying**, NOT "a tag is missing". The reconciler's
whole remedy — mint a release tag because a JSON file says so — would **invent a release that never happened**. It is
pointed the wrong way, and re-sourcing it from the manifest (the original fix proposal) would have made it _confidently_
wrong rather than harmlessly dead.

### 2. The detection already exists, done correctly, in a migrated tool

`assert_version_coherence.py` already emits a `tag?` column per repo (`tag-ok` / `tag-MISS`) — exactly the check
`reconcile-release-tags` was built for, with the correct D13 semantics. Grep evidence of who was migrated and who was
missed:

| script                        | pyproject refs | git-tag-aware |
| ----------------------------- | -------------- | ------------- |
| `assert_version_coherence.py` | 11             | **5** ✅      |
| `reconcile_release_tags.py`   | 7              | **0** ❌      |
| `sync-manifest-versions.py`   | 28             | **0** ❌      |

D13 migrated one reader and missed the other two. See the sibling issue doc
`d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md`.

### 3. Empirically there is nothing for it to do

Ran `assert_version_coherence.py` against the live fleet: **every repo reports `tag-ok`** — the tag for each manifest
version exists. Independently compared manifest `versions{}` vs the highest real tag across 24 repos:

```
  in sync: 13    manifest LAGS the tag: 9    manifest AHEAD of the tag: 1
```

**Exactly ONE repo** (`unified-trading-pm`, `versions=1.2.596` vs highest tag `v1.2.595`) is in the only state the
reconciler could ever act on — and per D13's model above, that one is a **cache split**, not a missing tag. The real
drift is the opposite direction (9 repos lagging; see the sibling doc), which this workflow cannot address by design.

### Verdict

`reconcile-release-tags` is (a) impossible as written (reads a field D13 deleted), (b) redundant with a migrated tool
that performs the same check correctly, and (c) its remedy inverts D13's direction of truth. **Delete the workflow +
`scripts/cicd/reconcile_release_tags.py`**, per the workspace rule "delete deprecated code (no shims)". That also
removes **~48 no-op runs/day** (`*/30`) — a larger, cheaper win than moving it to the glue pool was.

If a "heal" action is still wanted, it belongs on the **cache/Firestore** side (make `versions{}` match the tags), NOT
on the tag-minting side. That is the sibling doc's subject.

**Do NOT delete blindly**: confirm nothing else keys off the `reconcile-release-tags` workflow name (the
`repository_dispatch: [reconcile-release-tags]` trigger suggests something may dispatch it) before removing.
