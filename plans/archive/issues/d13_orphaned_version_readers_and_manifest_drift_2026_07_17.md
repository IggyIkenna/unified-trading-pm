---
doc_type: issue
title:
  The D13 `version_source=git-tag` migration deleted the static pyproject version but only migrated SOME of its readers
  — `sync-manifest-versions.py` and `reconcile_release_tags.py` still read the deleted field, the manifest's
  `versions{}` cache lags the tags for 9 of 24 repos, and the one checker that sees all of it exits 1 while
  quality-gates.sh passes
summary: >
  Phase-2 / D13 (2026-06-27, `f4a3865e` fleet rollout) moved the fleet to `version_source: git-tag` — 23 of 25 manifest
  repos now declare it — which REMOVED the static `version = "X.Y.Z"` line from pyproject.toml in favour of `dynamic =
  ["version"]` + hatch-vcs. The version SSOT became the git TAG, and `workspace-manifest.json`'s `versions{}` became a
  Firestore-projected CACHE. The migration updated `scripts/cicd/assert_version_coherence.py` (11 pyproject refs, 5
  git-tag-aware branches) but left at least two readers still parsing the deleted field: `reconcile_release_tags.py` (7
  pyproject refs, 0 git-tag-aware — dead since D13, see its own issue doc) and
  `scripts/manifest/sync-manifest-versions.py` (28 pyproject refs, 0 git-tag-aware — its docstring still says "Sync
  manifest versions section with pyproject.toml versions"). Separately, the `versions{}` cache has drifted: measured
  against the highest real git tag across 24 repos, 13 are in sync, **9 LAG** (worst: `e2e-testing` manifest 0.6.0 vs
  tag v0.40.0 — 34 minor versions; `system-integration-tests` 0.3.3 vs v0.14.11; `ibkr-gateway-infra` 0.0.74 vs v0.4.5)
  and 1 is AHEAD (`unified-trading-pm` 1.2.596 vs v1.2.595 = a cache claiming a version never minted). A THIRD version
  field, `repositories{}.version` (the vestigial display scalar), disagrees with `versions{}` for 19 repos. `versions{}`
  is not cosmetic — it is consumed by `scripts/quality-gates-base/version-alignment-gate.sh`, `scripts/quickmerge.sh`,
  `assert_version_coherence.py` and the topology/DAG generators. And `assert_version_coherence.py` **exits 1 with 24
  violations across 2 classes today**, yet a full `quality-gates.sh` run passes EXIT=0 — so the one tool that sees the
  whole picture is non-gating and nobody acts on it.
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    ci-cd,
    versioning,
    d13,
    git-tag,
    hatch-vcs,
    manifest,
    workspace-manifest,
    ssot-contradiction,
    silent-failure,
    green-but-wrong,
    migration-debt,
  ]
related:
  [
    /plans/archive/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md,
    /plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md,
    /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-17
parent_epic: deployment_and_user_management_master
priority: P1
source:
  github_actions_ci_cost_reduction_2026_07_15, slot 1, 2026-07-17 — found while looking for the correct version source
  to repair reconcile-release-tags; the repair turned out to be a symptom of a wider migration gap
assigned_vm: NA
execution_scope: local-only
assigned_role: devops
drift_direction: advance-code
last_updated: 2026-07-17
locked_by:
resolved_by:
  remaining steps tracked as open todos in ci_satellite_ao_dispatch_batch1_2026_07_26.md (steps 2/3/7); steps 5-6 parked
  as D16 pending operator review
depends_on: []
---

> **🟢 RESOLVED 2026-07-17 -- every step from this doc's own suggested order of work is now accounted for in properly
> tracked follow-up work. Archived per issue-doc-lifecycle.**

# D13 changed where version truth lives; not everything got the memo

## The model D13 established

From `scripts/cicd/assert_version_coherence.py:206-210` — the one tool that WAS migrated, and therefore the best
statement of intent we have:

> _"Phase-2 (D13) dynamic repo: the version SSOT is the git TAG; `versions{}` is the Firestore-projected cache (the
> versions-consolidator keeps `versions{}` == Firestore). Coherence = the tag `v{versions{}}` EXISTS… There is NO
> pyproject version line to read (dynamic)… A manifest version with no matching tag IS the split (the cache claims a
> version never minted)."_

So after D13 there are **three** places a version appears, in strict order of authority:

| #   | Where                             | Role                          | Authority        |
| --- | --------------------------------- | ----------------------------- | ---------------- |
| 1   | the git **tag** (`vX.Y.Z`)        | the release itself            | **SSOT**         |
| 2   | manifest `versions{}`             | Firestore-projected **cache** | derived          |
| 3   | manifest `repositories{}.version` | vestigial **display scalar**  | derived, ignored |

`pyproject.toml` is NOT on this list any more — that is the whole point of D13. 23 of 25 repos declare
`version_source: git-tag` (1 `package.json`, 1 unset).

## Problem 1 — orphaned readers still parsing the deleted field

| script                        | pyproject refs | git-tag-aware | state                                                            |
| ----------------------------- | -------------- | ------------- | ---------------------------------------------------------------- |
| `assert_version_coherence.py` | 11             | **5**         | ✅ migrated                                                      |
| `reconcile_release_tags.py`   | 7              | **0**         | ❌ dead since D13 — 20/20 runs `created 0 tag(s)`                |
| `sync-manifest-versions.py`   | 28             | **0**         | ❌ same bug; docstring still says "with pyproject.toml versions" |

`sync-manifest-versions.py` is not wired to any workflow (manual tool), so it fails only when someone reaches for it —
which is worse, because that is exactly when it is trusted. **This table is a sample, not a census** — the D13 rollout
should be re-swept for any other reader of a static `version = "X.Y.Z"`, and each checked against `version_source`.

## Problem 2 — the `versions{}` cache has silently drifted from the tags

Measured live: manifest `versions{}` vs the highest real `vX.Y.Z` tag, 24 repos.

```
  in sync: 13    manifest LAGS the tag: 9    manifest AHEAD of the tag: 1
```

Worst lags — these are not rounding errors:

| repo                       | manifest | highest tag | gap                     |
| -------------------------- | -------- | ----------- | ----------------------- |
| `e2e-testing`              | 0.6.0    | **0.40.0**  | 34 minor versions       |
| `system-integration-tests` | 0.3.3    | **0.14.11** | 11 minor versions       |
| `ibkr-gateway-infra`       | 0.0.74   | **0.4.5**   | 4 minor versions        |
| `instruments-service`      | 0.88.0   | 0.90.0      | 2                       |
| `agent-orchestrator`       | 0.97.0   | 0.98.0      | 1                       |
| `unified-trading-pm`       | 1.2.596  | 1.2.595     | **AHEAD** = cache split |

Note the subtlety: a LAGGING cache is still "coherent" by D13's definition (the tag `v{versions}` does exist — it is
just not the newest), which is why `assert_version_coherence` reports `tag-ok` for all of them. **Coherent and correct
are not the same thing here.** The `versions-consolidator` that is supposed to keep `versions{}` == Firestore appears
not to be closing this gap; worth confirming it runs at all.

This matters because `versions{}` is consumed by, at least: `scripts/quality-gates-base/version-alignment-gate.sh` ·
`scripts/quickmerge.sh` · `scripts/cicd/assert_version_coherence.py` · `scripts/cicd/version_registry_store.py` ·
`scripts/openapi/generate_system_topology.py` · `scripts/manifest/_align_workspace_manifest.py` ·
`scripts/repo-management/run-version-alignment.sh`.

## Problem 3 — the display scalar disagrees with the cache for 19 repos

`assert_version_coherence.py` currently reports `VESTIGIAL_SCALAR_DRIFT` on 19 repos, e.g.
`unified-trading-library: repositories{}.version=0.48.0 != versions{}=0.55.0`, `ml-service: 0.38.0 != 0.50.0`,
`instruments-service: 0.77.0 != 0.88.0`. Its own remedy line says: _"run run-version-alignment.sh --fix (updates the
display scalar) **or delete the field**"_. Given the field is explicitly vestigial, deleting it is likely the right call
— a third version field that nothing trusts is pure drift surface.

## Problem 4 — the checker that sees all of this is non-gating

`.venv/bin/python scripts/cicd/assert_version_coherence.py` today:

```
❌ 24 violation(s) across 2 class(es).
EXIT=1
```

…while a full `bash scripts/quality-gates.sh --no-fix` on the same tree passes **EXIT=0**. It is referenced from
`scripts/quality-gates.sh`, so it runs — but its non-zero exit does not fail the gate. That makes it the **third**
detector in this cluster that measures a real problem and is wired to nothing (the others: PM's
`check_base_image_digest_drift`, warn-only; and the dead `digest-drift-sweep` itself). A detector nobody acts on is
indistinguishable from no detector — and costs more, because it looks like coverage.

## Suggested order of work

1. **Decide the cache-repair direction** — should `versions{}` be reconciled FROM the tags (tags are SSOT ⇒ yes)? If so
   that is a real, needed job, and it is the honest replacement for `reconcile-release-tags`, which currently attempts
   the inverse. `_highest_existing_tag()` already exists in `reconcile_release_tags.py` and could be salvaged for it.
2. **Confirm why the versions-consolidator is not closing the 9-repo gap.**
3. **Fix or delete `sync-manifest-versions.py`** — do not leave a manual tool that reads a deleted field.
4. ~~**Delete `reconcile-release-tags`**~~ — ⛔ **SUPERSEDED 2026-07-26**: the script was **repurposed, not deleted**
   (`unified-trading-pm@6c4ee4d0c`, ancestor-verified) and is now the fleet's release-**stall alarm**; codex has ruled
   it so (`/codex/08-workflows/ci-cd-flow.md:1004`, corrected 2026-07-25). Do not delete it. Full evidence in its own
   issue doc's top banner:
   [/plans/archive/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md](/plans/archive/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md).
5. **Delete the vestigial `repositories{}.version` scalar**, per the checker's own remedy.
6. **Make `assert_version_coherence.py` gate** once 1-5 land — otherwise this recurs silently.
7. **Re-sweep for other D13 orphans** — the table above is a sample, not a census.

## Census addendum (2026-07-31, ci_satellite_ao_dispatch_batch1-019, steps 3 + 7)

**Step 3 resolution — `sync-manifest-versions.py` DELETED**, not fixed. Live-measured before deletion:
`get_repo_type`/`read_pyproject_version` sweep across all 24 manifest repos shows only ONE (`unified-trading-pm` itself)
still carries a static `[project].version` line — every other `version_source: git-tag` repo has been fully migrated to
`dynamic = ["version"]` (hatch-vcs), so the script silently skipped all 22 of them (harmless-but-vacuous). For the one
repo it could still act on, running it live (`python3.13 scripts/manifest/sync-manifest-versions.py`) produced
`DRIFT: unified-trading-pm manifest=1.2.655 pyproject=1.2.596` exit=1 — and `--apply` would have overwritten the
manifest's more-current, tag-derived value (1.2.655) with the STALE, un-migrated pyproject line (1.2.596), i.e. active
data loss in the wrong direction (D13's model: the tag is SSOT, pyproject is not). The tool was not just inert, it was
actively harmful in its one remaining live case. Confirmed zero dangling referrers before deletion: no
workflow/script/test invokes it (only historical mentions in archived plans/docs); `assert_version_coherence.py`
(already wired into `scripts/quality-gates.sh:979`, git-tag-aware, correct-direction) fully supersedes its function.
Deleted via `unified-trading-pm@<see plan checkbox for sha>`.

**Step 7 re-sweep — 2 more D13 orphans found beyond the original sample table** (broader grep for
`project.get("version")` / `data["project"]["version"]` across all repos' `scripts/`):

| script                                   | repo                  | reads                      | state                                                                                                                                                                                                                                                                                                                     |
| ---------------------------------------- | --------------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `server/config.py::app_version()`        | agent-orchestrator    | own installed dist version | ❌ was dead (KeyError → always `"unknown"`, silently regressing the dashboard version pill since D13) — **FIXED live 2026-07-31** to `importlib.metadata.version("orchestrator")`, the established D13 API-2 pattern already used by `deployment-api/deployment_api/__init__.py`.                                         |
| `check_workspace_pyproject_pin_drift.py` | unified-trading-pm    | ALL repos' own version     | ❌ vacuous for the same reason as `sync-manifest-versions.py` (dynamic repos never populate `name_to_version`) — NOT wired to `quality-gates.sh` or any workflow today (grep-confirmed), so currently inert rather than actively harmful. Followup todo filed.                                                            |
| `check_sdk_version_alignment.py`         | unified-api-contracts | api-contracts' own version | ❌ `_get_api_contracts_version()` always returns `""` for the (git-tag/dynamic) api-contracts repo; `_version_satisfies_spec` treats empty as "always satisfies", so the api-contracts-version-overlap check silently no-ops. NOT wired to any workflow today (grep-confirmed) — inert, not harmful. Followup todo filed. |

`agent-orchestrator/server/config.py` was fixed inline (small, clear, high-value — a live user-visible regression with
an already-established fix pattern elsewhere in the fleet). The other two are NOT wired to anything today, so lower
urgency; followup todos filed in `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md` rather than fixed inline
to keep this unit bounded. Also found (unrelated to D13, hit as a side effect while deleting the dead script): a
false-positive in the `block_destructive_commands.py` PreToolUse guardrail's recursive-rm regex — tracked separately at
`/plans/active/issues/destructive_rm_guardrail_regex_false_positive_on_hyphenated_filenames_2026_07_31.md`.

Census now closed — the table above plus the original sample table cover every repo's `scripts/` tree for a
`tomllib`-based reader of `[project].version` (broader sweep also checked `grep`/`sed`-based static-line readers in
shell/workflow files; none found beyond the fleet-standard
`semver-agent`/`request-major-bump`/`update-dependency- version` workflow set, which are already correctly git-tag-aware
post-D13).
