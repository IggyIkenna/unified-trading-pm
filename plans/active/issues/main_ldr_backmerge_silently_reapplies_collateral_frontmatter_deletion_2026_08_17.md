---
doc_type: issue
title:
  "main->LDR back-merge silently RE-APPLIES a frontmatter key that an earlier promotion dropped as collateral — a clean
  three-way merge, no conflict marker, nothing for a resolver to review"
summary: >-
  Measured 2026-08-17 while resolving PR #3369 (`main -> live-defi-rollout` back-merge, escalation `agt-826e8f`). The
  `author:` key on `plans/active/issues/manifest_hygiene_red_all_2026_08_17.md` was dropped from LDR by `a6e4afc11d` as
  pure collateral of a "kept their side entirely" rebase resolution — never a ruling against the field. The back-merge
  restored it (`86da727f32`). An LDR->main promotion then carried the key-less LDR copy up to `main`, so on the NEXT
  back-merge the three-way base HAD the key, LDR still HAD it, and `main` had "deleted" it — git therefore applied the
  deletion with a CLEAN auto-merge and no conflict marker. A resolver reviewing only the reported conflicts sees
  nothing; the standing `main-backmerge-to-ldr` automation merges unattended, so the regression lands with no human in
  the loop. Caught only because the merged tree was diffed against LDR BEFORE committing (`git diff --stat
  origin/live-defi-rollout <merge-tree-oid>` showed `-1` on a file nobody had touched). Re-added in `ada633620e`; both
  branches now carry it, which ends the ping-pong for THIS key but not the mechanism.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [backmerge, merge-semantics, frontmatter, collateral-deletion, conflict-resolver, ldr-main, silent-regression]
related:
  [
    /plans/archive/2026_08/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-20"
parent_epic: ci_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: high
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /agents/conflict_resolver.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/manifest_hygiene_red_all_2026_08_17.md,
    scripts/quality-gates-base/tests/test-backmerge-silent-revert-loss-guard.sh,
    scripts/docs/docspec.py,
  ]
source: >-
  Found 2026-08-17 by slot 19 while executing escalation `agt-826e8f` (conflict_resolver, PR #3369). Not a hypothesis —
  the deletion was observed in the merge tree and reverted before the commit landed.
---

# main->LDR back-merge silently re-applies a collateral frontmatter deletion

## The mechanism (measured, not inferred)

A key is dropped from LDR as collateral of some unrelated resolution. It is still present on `main` and in the shared
history, so the NEXT back-merge looks like this to git:

| side          | has the key? | git's reading                |
| ------------- | ------------ | ---------------------------- |
| merge base    | yes          | the starting point           |
| LDR (ours)    | yes          | unchanged                    |
| `main`(theirs)| no           | "theirs deliberately deleted" |

One side changed, the other did not ⇒ **clean auto-merge, deletion applied, no conflict marker.** The direction the key
travels is irrelevant; only which side last touched it matters. Round-tripping through an LDR->main promotion flips
which branch is the "deleter", so the same key can be deleted, restored, and deleted again across successive merges.

Concrete instance: `author: "manifest_hygiene_daily.py (data-pipeline daily audit)"` on
`plans/active/issues/manifest_hygiene_red_all_2026_08_17.md`. Dropped by `a6e4afc11d`, restored by `86da727f32`,
silently re-deleted by the `origin/main` merge, restored again in `ada633620e`.

## Why this is worth a guard rather than vigilance

- The standing `main-backmerge-to-ldr` automation merges **unattended** whenever the merge is clean. A clean merge is
  exactly the case nobody inspects — the escalation to a `conflict_resolver` only fires on CONFLICT.
- `agents/conflict_resolver.md` tells the resolver to keep "the merged combination of both sides' genuine work", but
  every instruction in it is scoped to files git REPORTS as conflicted. This class is invisible to that workflow.
- The blast radius is the whole `plans/` + `codex/` corpus, not one file: any frontmatter key, any `- [ ]` todo line,
  any table row that one branch lost as collateral is re-deletable on the next round trip.

## The check that caught it (cheap, reusable)

`git merge-tree --write-tree` gives a tree OID without committing, so the merge result can be diffed against the target
BEFORE anything is recorded:

```bash
TREE=$(git merge-tree --write-tree origin/live-defi-rollout origin/main)
git diff --stat origin/live-defi-rollout "$TREE"     # anything unexpected here is a silent loss
```

Deletions on files the back-merge has no business touching are the signal. `git merge-tree` exits 0 and prints only the
tree OID when the merge is clean, so exit code alone proves nothing about content — that is the proxy trap here.

## Todos

- [x] ✅ [SCRIPT] P2. **Add a silent-deletion guard to the back-merge path** — before `main-backmerge-to-ldr` merges, run
      the `git merge-tree` + `git diff --stat` check above and FAIL (escalate) when the merge deletes lines from files
      whose only change comes from the base-vs-theirs side. Start with frontmatter keys and `- [ ]` todo lines, which
      are the highest-value losses. Provenance: this doc. — unified-trading-ci@6e92bcd (the reusable
      `main-backmerge-to-ldr.yml` every repo's caller resolves against — see that repo's README "One branch: main,
      no LDR tier" for why this shipped as a direct push to `main`, not quickmerge). Adds
      `check_no_silent_frontmatter_or_todo_loss()` scoped to the exact base-vs-theirs-only shape (ours unchanged since
      merge-base, theirs deletes a frontmatter key or `- [ ]` todo line), wired into both the explicit-base and
      default merge paths. Regression test extended:
      `scripts/quality-gates-base/tests/test-backmerge-silent-revert-loss-guard.sh` (12/12 pass, incl. 3 new functional
      cases reproducing this doc's exact `author:` key mechanism) — also fixed 2 pre-existing stale cross-repo/
      relocated-script path bugs discovered while touching it (BACKMERGE_WF pointed at a deleted PM path post the
      2026-08-06 unified-trading-ci extraction; the trailer-stamp structural anchor grepped the wrong file post the
      2026-08-01 `ldr_to_main_fleet_promote.sh` extraction) — both had been silently failing/FATAL-ing.
- [ ] [DOCS] P2. **Teach `agents/conflict_resolver.md` the clean-merge blind spot** — the role currently reviews only
      git-reported conflicts. Add the pre-commit `merge-tree` diff as a mandatory step of its step-2d/step-4, with the
      exit-0-proves-nothing caveat spelled out. Provenance: this doc.
- [ ] [DOCS] P3. **Decide whether `author:` should be REQUIRED rather than elective on generator-emitted issue docs** —
      `scripts/docs/docspec.py` declares it `Req.E`, which is why three separate resolutions could each drop it without
      a single gate complaining. A generator-emitted doc arguably must keep its provenance. Operator/schema-owner call.
      Provenance: this doc.

## Progress log

- **2026-08-17** — Found and reverted in-flight during escalation `agt-826e8f`. Resolution landed on
  `live-defi-rollout`: `86da727f32` (the three PR #3369 conflicts), `4b07cb8b31` (schema-required frontmatter keys),
  `ada633620e` (this silent deletion reverted). PR #3369 merged as `073acbb1c0`. No guard exists yet — the todos above
  are the actual fix.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
