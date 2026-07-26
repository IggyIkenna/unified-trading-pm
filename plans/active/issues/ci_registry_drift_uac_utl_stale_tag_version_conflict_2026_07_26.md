---
doc_type: issue
title:
  unified-trading-system-ui's registry-drift CI job has been silently broken since 2026-07-21 (UAC/UTL stale-tag pip
  conflict)
summary: >-
  unified-trading-system-ui's ci.yml `registry-drift` job (the only CI-level drift check for
  lib/registry/ui-reference-data.json) has failed on EVERY push to main since at least 2026-07-21 — the `pip install -e`
  of UAC+UTL default-branch checkouts hits a ResolutionImpossible: UAC's main HEAD resolves (via hatch-vcs git-describe)
  to a stale "0.71.1.devNNN" version because tag v0.72.0 is NOT an ancestor of UAC's current main branch, which fails
  UTL's `unified-api-contracts>=0.72.0` pip constraint. Found while scoping
  defi_wizard_batch2_018_residual_findings-004/-005 (extending this same job to also drift-check
  capability-manifest.json/capability-verdict-matrix.json) — a scratch PR reproduced the identical failure on completely
  unmodified code, proving it predates and is unrelated to that work. A partial fix (fetch-depth:0 on the UAC/UTL
  checkouts, fixing a separate shallow-clone/no-tags-at-all failure mode) is shipped, but the deeper stale-tag- ancestry
  issue remains open and needs a cicd/infra-scoped investigation.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-system-ui, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [ci, registry-drift, hatch-vcs, dynamic-versioning, pip, cross-repo]
related:
  [
    /plans/archive/issues/defi_wizard_batch2_018_residual_findings_2026_07_26.md,
    /plans/active/issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md,
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
drift_direction: advance-code
depends_on: []
source:
  [
    unified-trading-system-ui/.github/workflows/ci.yml,
    unified-api-contracts/pyproject.toml,
    unified-trading-library/pyproject.toml,
  ]
---

## What I found

While scoping `defi_wizard_batch2_018_residual_findings-004`/`-005` (extend the `registry-drift` CI job to also
drift-check `capability-manifest.json`/`capability-verdict-matrix.json`, mirroring the existing `ui-reference-data.json`
check), I pushed a scratch branch + draft PR (#354, then #356 after a partial fix, both closed without merging) to
verify the new steps against a real GitHub Actions run. The job failed before it ever reached my new steps — at the
PRE-EXISTING `Install generator deps (UAC + UTL — the generator imports both)` step
(`pip install -e _deps/unified-api-contracts -e _deps/unified-trading-library`), completely unmodified by my change.

**Confirmed pre-existing, not caused by my work**: `gh run list --workflow "CI - Test & Lint" --branch main --limit 10`
shows the `registry-drift` job has failed on the last 10 consecutive pushes to `main`, going back to **2026-07-21**.
`e2e` also fails consistently on the same runs (separate, not investigated here — `ci.yml` is not the required check,
`quality-gates-v2.yml` is, so this has gone unnoticed operationally).

**Root cause, in two layers:**

1. **Shallow-clone / no-tags-at-all (FIXED this session).** `actions/checkout@v5`'s default is a shallow clone with no
   tags. UAC and UTL both use `hatch-vcs` (git-describe-against-tags) dynamic versioning. With no reachable tags, the
   resolved version was a placeholder `0.1.dev1+g<sha>` — which trivially fails UTL's
   `unified-api-contracts<1.0.0,>=0.72.0` constraint (0.1 < 0.72). Fix: add `fetch-depth: 0` to the UAC/UTL checkout
   steps (`unified-trading-system-ui@8c2f3590`, shipped).

2. **Stale reachable tag (STILL OPEN, deeper).** After the fetch-depth fix, the version resolves correctly to a REAL
   git-describe value — but it's still wrong: `0.71.1.dev158+gb22f9fca2`. `gb22f9fca2` is UAC's actual current `main`
   HEAD (confirmed via `gh api repos/IggyIkenna/unified-api-contracts/commits/main`). Tag `v0.72.0` exists in the repo
   (confirmed via `gh api repos/IggyIkenna/unified-api-contracts/tags`) but
   `git merge-base --is-ancestor <v0.72.0-sha> b22f9fca2` returns **false** — v0.72.0 was tagged on a commit that is
   **not an ancestor of UAC's current main branch**. `git describe` therefore falls back to an older tag
   ("v0.71.1"-ish), and UTL's `>=0.72.0` constraint correctly (if unhelpfully) rejects it. This is NOT a shallow-clone
   artifact — `fetch-depth: 0` does not fix it, because the tag genuinely isn't reachable from main's actual history.

**Why this matters beyond CI noise**: `ci.yml`'s `registry-drift` job is the ONLY thing that would catch
`lib/registry/ui-reference-data.json` going stale vs UAC/UIC (per `unified-trading-pm/docs/ui-alignment-ssot.md` §1's
"next automation step" note). It has been unable to run successfully for 5+ days — meaning that drift check has been
silently non-functional this whole time, on top of the separate capability-manifest.json/capability-verdict-matrix.json
gap already documented in `docs/ui-alignment-ssot.md` §1a.

**Not investigated / not this doc's job**: WHY v0.72.0 isn't an ancestor of main (a release-tagging/branch-topology
question — possibly related to the semver-agent retarget off `staging` noted in workspace CLAUDE.md § "Git discipline",
though the dates don't line up cleanly enough to be certain) is a cicd/infra-scoped release-process question, not
something this UI-craft-scoped investigation should hand-fix by loosening a version constraint or minting a tag.

## Why it matters

A silently-broken, non-required CI job is exactly the kind of thing that stays broken indefinitely because nothing pages
on it — this one has already gone 5+ days unnoticed. It also fully blocks verifying
`defi_wizard_batch2_018_residual_findings-004`/`-005`'s CI-check design in real GitHub Actions (the design itself is
proven correct via local reproduction — see that issue doc — but never successfully executed end-to-end in CI).

## Recommended decision

- [x] ✅ [SCRIPT] P3. **DONE 2026-07-26 (slot 2), `unified-trading-system-ui@8c2f3590`.** Shipped the fetch-depth:0 fix
      (layer 1) — it's a genuine, real, independently valuable fix regardless of layer 2's resolution (correct version
      strings resolve now instead of a nonsense placeholder), full `quality-gates.sh` green.
- [x] ✅ [CICD] P2. **DONE 2026-07-26 (slot 6)** — root-caused in the sibling doc
      `/plans/active/issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` § "Root cause
      diagnosed": `v0.72.0` was a MANUAL one-off D13-migration baseline tag placed on an LDR-side `_backmerge` merge
      commit (`4ac8be3f`), never on `main`'s own graph — not a semver-agent bug, not a stalled promotion (content was
      byte-identical on `main`'s own squash commit `b52aea5d`, ~2h later, which is what should have been tagged). `main`
      only advances via single-parent squash commits, so an LDR-side tag can never become a `main` ancestor no matter
      how many further promotions land — this will NOT resolve on its own via (a). Adjacent finding also logged there:
      `semver-agent` is correctly retargeted to `push:[main]` since 2026-07-25 and would self-heal this class going
      forward, but its bump-rate circuit breaker is currently tripped, so no new tag has actually landed yet. Fix
      direction (re-tag vs. wait-for-breaker-clear) is the sibling doc's still-open todo 2 — not duplicated here.
- [ ] [SCRIPT] P3. Once the above is resolved, re-verify `registry-drift` goes green on `main` for 3 consecutive pushes
      (not just once — confirm it's not still flaky), THEN pick up the already-designed
      capability-manifest.json/capability-verdict-matrix.json CI-check extension from
      `defi_wizard_batch2_018_residual_findings-004`/`-005` (the YAML is fully drafted and locally-verified — see that
      issue doc's evidence — just needs a clean real-CI run to merge with confidence). Repos: unified-trading-system-ui,
      unified-trading-pm.
