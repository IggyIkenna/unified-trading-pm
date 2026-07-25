---
doc_type: issue
title:
  "`git merge-base --is-ancestor <ldr-sha> origin/main` produces false 'not live' verdicts after a squash-merge promote
  — caused 3 wasted review dispatches across 2 plans"
summary: >-
  [REVIEW] The standard ad-hoc recipe reviewers reach for to answer "is commit X live" — checking whether the ORIGINAL
  LDR commit SHA is an ancestor of `origin/main` — is structurally wrong whenever the LDR→main promote squash-merges (as
  `deployment-api`'s `ldr-to-main-promote-fleet.yml` / "Option-B direct" promote does). The squash produces a NEW
  synthetic commit on `main` (e.g. `chore(promote): LDR → main`) whose SHA is never equal to, and never has as a parent,
  the original LDR commit — so the ancestor check reports "not an ancestor" FOREVER, even the instant after the content
  lands and deploys. This produced 3 consecutive false "not live" verdicts this session (slot 2, slot 6, slot 10 on
  `deployment_api_sigabrt_crash_loop_2026_07_24.md`'s todo 2; slot 2 again on
  `deployment_registry_firestore_p0_unblock_2026_07_14.md`'s Resources-column todo) even though the fixes in question
  (`deployment-api@1adf54b`, `@96f5eb5`) had already been live and deployed for hours in both cases. CLAUDE.md already
  warns about a RELATED trap ("verify by CONTENT... not squash-inflated ahead_by") but that guidance is scoped to
  overall repo drift counts, not to "is this specific commit's content live" checks — which is the far more common thing
  a reviewer actually needs to verify, and where this session's agents (including this one, initially) kept reaching for
  the wrong recipe.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [verification-methodology, ci-cd, promote, squash-merge, review-process]
related:
  - /plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md
  - /plans/active/deployment_registry_firestore_p0_unblock_2026_07_14.md
created: 2026-07-25
priority: P2
parent_epic: observability_master
source:
  "[REVIEW] slot-10 discovery while re-verifying deployment_registry_firestore_p0_unblock_2026_07_14.md's
  Resources-column todo — the 'NOT YET LIVE' verdict from slot 2 (04:50Z) didn't match a direct content-diff of
  origin/main, which led to tracing the same false-negative pattern back through 2 more dispatches on the sibling
  SIGABRT plan."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# Squash-merge breaks naive SHA-ancestry "is it live" checks (2026-07-25)

## What I found

Both `deployment_api_sigabrt_crash_loop_2026_07_24.md` and `deployment_registry_firestore_p0_unblock_2026_07_14.md`
carried `[REVIEW]` todos asking "confirm `deployment-api@<sha>` is live" before doing further verification work. Three
dispatches (slot 2, slot 6, then this session again) all used the same recipe:

```bash
git merge-base --is-ancestor <sha> origin/main   # reports "no" — but this is NOT evidence of absence post-squash
```

...and all three concluded "not live yet, image tag unchanged, waiting on the fleet promote." That conclusion was
**wrong** in both cases. `deployment-api`'s promote (`ldr-to-main-promote-fleet.yml`, "Option-B direct")
**squash-merges** LDR into `main` — every promote PR title is literally `chore(promote): LDR → main (Option-B direct)`,
and the merge commit SHA (e.g. `273c951`) is a NEW commit that is content-identical to LDR at that point in time but is
NEVER a descendant of any individual original LDR commit in the git graph sense the ancestor check relies on. So:

- `git merge-base --is-ancestor <original-ldr-sha> origin/main` will return **false forever**, regardless of whether the
  content shipped 5 minutes ago or 5 months ago.
- The live Cloud Run image tag is literally the squash-commit SHA (`273c951`), which does not visually resemble the
  original commit sha either (`1adf54b`, `96f5eb5`) — reinforcing the "unchanged tag ⇒ still not live" misread, when
  actually the SAME tag can validly mean "already includes the fix, just no NEWER promote has landed since."

**Ground truth, checked directly**: `git show origin/main:<path> | grep <marker>` for both fixes shows the marker
present and byte-identical to `origin/live-defi-rollout`'s copy — content-diff is unambiguous and cheap (one `git show`

- `grep`), versus the ancestor check which is actively misleading here. The Cloud Run revision's
  `metadata .creationTimestamp` (`gcloud run revisions describe`) cross-referenced against the promote PR's `mergedAt`
  (`gh pr list --json mergedAt`) confirms the deploy happened minutes after the specific squash-merge that carried the
  content.

This is a variant of a trap CLAUDE.md ALREADY names — "verify by CONTENT `gh api …/compare/main...live-defi-rollout`,
not squash-inflated `ahead_by`" — but that guidance is phrased around aggregate drift-count checks
(`ahead_by`/`behind_by` between two branches), not the much more common "is commit X's fix live" question a reviewer
actually asks. Reviewers (this session's slots 2, 6, and this one, initially) reach for the intuitive `is-ancestor`
check instead, because nothing in RULES.md/review.md's playbook explicitly names this specific failure mode or gives the
content-diff alternative as the default recipe for THIS question shape.

## Why it matters

- Produced 3 wasted redispatch cycles on one todo (SIGABRT plan) before this session finally recognized the pattern —
  each burning a full slot-dispatch + review turn on a re-check that could never have yielded new information given the
  (wrong) method being used.
- Worse than wasted cycles: it produced a **wrong operational conclusion** that blocked real diagnostic progress — the
  SIGABRT crash-loop investigation (a P1, compounding a separate reaper-drain P0) sat "waiting for deploy" for over 2
  hours after the fix had actually been live, delaying the actual next diagnostic step (reading the faulthandler dump)
  by that same margin.
- Any other in-flight plan with a "confirm `<repo>@<sha>` is live" todo against a squash-merge-promoted repo
  (`deployment-api` uses "Option-B direct"; check which other repos share this promote mode) is at risk of the exact
  same false negative today.

## Recommended decision

Fix in `unified-trading-pm/agents/review.md` and/or `RULES.md` — add the correct recipe as the DEFAULT for "is commit X
live" checks, not just the aggregate-drift-count case already covered:

- [ ] [DOCS] P2. In `unified-trading-pm/agents/review.md`'s "Evidence-backed completion" section (or a new subsection
      near it), add an explicit recipe for "is commit `<sha>` from repo `<r>`'s LDR history actually live on
      `main`/deployed" that does NOT rely on `git merge-base --is-ancestor <sha> origin/main` alone. Recommended recipe:
      (a) identify the specific file(s)/lines the fix touches; (b) `git show origin/main:<path>` and grep for the fix's
      marker (a distinctive line/string introduced by the fix); compare byte-for-byte against
      `origin/live-defi-rollout`'s copy of the same path; (c) cross-reference the deployed artifact's build/deploy
      timestamp (`gcloud run revisions describe ... --format='value(metadata.creationTimestamp)'` for Cloud Run repos)
      against the promote PR's `mergedAt` (`gh pr list --state merged --json mergedAt,number`) to confirm the deploy
      happened AFTER (not before) the relevant squash-merge. Explicitly call out that an unchanged image tag/revision
      name across two checks does NOT imply "still not deployed" — it can mean "deployed once, no NEWER promote since,"
      which is functionally different. (repo: unified-trading-pm)
- [x] ✅ [DOCS] P3. Cross-check which OTHER repos use the same "Option-B direct" squash-merge promote mode (grep
      `.github/workflows/` or the fleet promote workflow's repo list in `unified-trading-pm` for `ldr_main` /
      "Option-B") vs a merge-commit-preserving mode — if the split is meaningful, note in
      `codex/08-workflows/ci-cd-flow.md` which mode applies where, so a reviewer knows up front whether the ancestor
      check is even valid for a given repo. (repo: unified-trading-pm) — unified-trading-pm@1b6fdc147 (see Progress
      Log).
- [ ] [REVIEW] P3. Sweep currently-open plans/issue docs for other "confirm `<repo>@<sha>` is live" todos phrased around
      the ancestor check specifically, and re-verify each via the content-diff method above — there may be other false
      "not live" verdicts sitting in the backlog right now beyond the 2 corrected today. (repo: unified-trading-pm)

## Progress Log

- **2026-07-25T05:52Z (slot 4, review)** — Shipped todo 2 (`unified-trading-pm@1b6fdc147`). Cross-checked every promote
  path's merge-arm step: `workspace-manifest.json` shows all 24 non-PM repos are `promotion_model: ldr_main` today (none
  currently staging-routed) — those go through `ldr-to-main-promote-fleet.yml`, which unconditionally arms
  `gh pr merge --auto --squash --delete-branch` (no rebase attempt, ever — "LDR carries merge commits from the
  backmerge-sink design; not rebaseable"). PM's own `ldr-to-main-promote.yml` (Option-B, no staging) is the same —
  unconditional `--squash`. The staging-routed hops (`ldr-to-staging-promote.yml` LDR→staging, `staging-to-main.yml`
  staging→main) both attempt `--rebase` FIRST and only fall back to `--squash`/`--merge` on conflict — so the ancestor
  check is "sometimes" valid there, never guaranteed. Net: the split IS meaningful (direct-fleet promote = always squash
  = ancestor check always invalid; staging-routed = rebase-first = sometimes valid) but has zero practical effect right
  now since 100% of repos are `ldr_main` direct — documented the table + the caveat in
  `codex/08-workflows/ci-cd-flow.md` § "Which repos squash vs. rebase on promote". Did not touch `agents/review.md`
  (todo 1, separate task, not yet dispatched to this slot). (Correction: the codex commit's SHA was rewritten by a
  `git pull --rebase --autostash` needed to reconcile branch drift before this flip could push — first cited
  `1ed215b31`, corrected here to the actually-reachable `1b6fdc147`.)

- **2026-07-25T05:28Z (slot 10, review)** — Filed after discovering + correcting the false-negative verdict on
  `deployment_registry_firestore_p0_unblock_2026_07_14.md`'s Resources-column todo, then tracing the same pattern back
  through 2 prior dispatches on `deployment_api_sigabrt_crash_loop_2026_07_24.md`'s todo 2 (corrected in that doc
  directly). No code shipped — this doc is the tracked follow-up for the process/docs fix; the 2 concrete plan
  corrections already happened inline in their own docs.
