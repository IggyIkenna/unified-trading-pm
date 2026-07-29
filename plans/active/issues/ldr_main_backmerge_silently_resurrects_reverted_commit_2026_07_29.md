---
doc_type: issue
title:
  LDR<->main promote/backmerge race silently resurrected a just-reverted commit (instruments-service Dockerfile) — a
  revert landing within ~15min of a squash-promote can be lost without any conflict marker
summary: >-
  While fixing a broken instruments-service Cloud Build (uv/pip.conf gap, see the related doc), shipped a fix
  (`2941646c`), verified it live-regressed a different resolution step, and reverted it (`8df0e94e`) — both via the
  normal quickmerge flow to `live-defi-rollout`. Minutes later, the SAME reverted content reappeared on `live-defi-
  rollout`'s Dockerfile with no new edit from me. Root cause: an LDR->main squash-promote (`4fc4900a`, created
  `2026-07-29T14:54:32Z`) squashed LDR's state from a point AFTER my fix (`2941646c`, ~14:33Z) but BEFORE my revert
  (`8df0e94e`, ~14:50Z) landed — a normal race given the promote fires on its own ~15min cadence, not on every push. The
  standing `main-backmerge-to-ldr` merge (`ed04b405`) then merged that stale `main` state back into `live-defi-
  rollout`. Confirmed via `git merge-base --is-ancestor 8df0e94e origin/live-defi-rollout` == YES (the revert commit IS
  in history) while the live Dockerfile content still had the reverted block — i.e. the merge was CONTENT-clean (no
  conflict markers, nothing for a human/agent to notice or resolve) yet still discarded the revert's actual effect. This
  is NOT a one-off quirk of my specific commits — any revert (or any fix-then-immediate-correction pair) landing on LDR
  within roughly one promote cycle of each other is structurally exposed to the same silent-loss pattern, because a
  squash-promote's source range and the backmerge's merge-base are computed independently of each other's timing.
  Re-reverted the Dockerfile a second time (`c5e8572a`) to restore the correct state; this doc tracks the PIPELINE bug,
  not the Dockerfile content itself (that's the sibling doc's scope).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, instruments-service]
scope: [engineer, admin]
tags: [ci-cd, ldr-main, promote, backmerge, git, race-condition, silent-data-loss]
related:
  [
    /plans/active/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md,
    /plans/active/issues/ldr_to_main_promote_churn_fix_verification_2026_07_27.md,
    /plans/active/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md,
  ]
created: 2026-07-29
priority: P1
parent_epic: infrastructure_master
source:
  "worker, slot 6, data_engineering — discovered mid-session while shipping + reverting an instruments-service
  Dockerfile fix, found the revert had been silently undone by the promote/backmerge pipeline within ~15 minutes"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# LDR<->main promote/backmerge can silently resurrect a reverted commit

## What happened, in order

1. `instruments-service@2941646c` — shipped a Dockerfile fix via quickmerge to `live-defi-rollout`, ~2026-07-29T14:33Z.
2. Verified live (manually re-triggered the Cloud Build) — the fix partially worked but regressed a different resolution
   step (`hatchling`/`hatch-vcs`).
3. `instruments-service@8df0e94e` — reverted the fix via quickmerge to `live-defi-rollout`, ~2026-07-29T14:50Z.
4. `instruments-service@4fc4900a` (`chore(promote): LDR → main (Option-B direct)`, squash) — created
   `2026-07-29T14:54:32Z`, parent `3d8af8c5`. This promote's squashed diff for `Dockerfile` shows step 1's fix ADDED but
   does NOT show step 3's revert — meaning the promote's source range ended sometime between step 1 and step 3.
5. `instruments-service@ed04b405` (`Merge remote-tracking branch 'origin/main' into _backmerge`) — the standing
   `main-backmerge-to-ldr` job merged `main` (now carrying step 4's stale, pre-revert content) back into
   `live-defi- rollout`. This merge produced NO conflict — git's 3-way merge concluded the `ENV UV_EXTRA_INDEX_URL...`
   block was "new" relative to whatever merge-base it computed, so it re-added the exact lines step 3 had removed.
6. Result: `live-defi-rollout`'s `Dockerfile` had the reverted block back, discovered only because I happened to re-read
   the file for an unrelated reason and noticed the mismatch — `git log` correctly showed `8df0e94e` in history, but the
   file's actual content did not reflect it. **A `git log`-only check would have missed this entirely** — only checking
   actual file content caught it.
7. Re-reverted a second time: `instruments-service@c5e8572a`.

## Why this is a structural gap, not a one-off

The squash-promote (step 4) and the backmerge (step 5) are two INDEPENDENT scheduled jobs with their own cadence —
neither one is aware of the other's exact timing, and neither is aware of a human/agent's commit landing on LDR in the
gap between them. Any commit-then-immediate-correction pair (a revert, a hotfix-of-a-hotfix, a quick follow-up commit)
that lands on LDR within roughly one promote-cycle's width of each other is exposed to the SAME pattern: the promote
squashes an intermediate state, and the backmerge can silently re-import that intermediate (stale) state's content back
into LDR without any conflict marker, because a squash commit's diff looks like ordinary new content to a 3-way merge,
not like "this specific block was deliberately removed downstream."

This is NOT specific to Dockerfiles or to this instruments-service commit pair — it is a property of the promote+
backmerge topology itself. Any repo, any file, any revert is exposed if the timing lines up.

## Why it matters

This is a **silent correctness gap in the LDR<->main promotion pipeline** that the workspace's own CI-CD discipline
(`/codex/08-workflows/ci-cd-flow.md`) has not previously documented. It means:

- A worker's revert can be undone without their knowledge, and without any signal (no conflict, no failed check) — the
  ONLY way to catch it is noticing the live file content doesn't match `git log`, which nobody routinely checks.
- This could re-introduce ANY previously-reverted bug (not just a build config bug) into production if the timing
  happens to line up — a genuine, if narrow-window, correctness risk for the whole fleet's git discipline.

## Recommended decision

Not a design call — this needs someone with deeper knowledge of the squash-promote + backmerge implementation
(`ldr-to-main-promote.yml` / `main-backmerge-to-ldr.yml`) to decide the actual fix shape. Candidates, not mutually
exclusive:

1. Make the squash-promote's source range boundary and the backmerge's merge-base computation share a common reference
   point (e.g. both always operate relative to the LDR tip at trigger time, never a stale snapshot), so a promote
   started before a revert lands can't produce a backmerge that undoes it.
2. Add a post-backmerge content-diff sanity check: after `main-backmerge-to-ldr` runs, diff the backmerge result against
   LDR's pre-merge tip for any file touched by a commit in the last N minutes, and flag (not block) if content was
   reintroduced that a recent commit had removed.
3. At minimum, document this race in `/codex/08-workflows/ci-cd-flow.md` so future agents know to re-verify FILE CONTENT
   (not just `git log`) after a revert that lands close to a promote cycle boundary.

## Todos

- [ ] [SCRIPT] P1. Root-cause the exact squash-promote/backmerge mechanics that let step 5's merge silently reintroduce
      content step 3 removed with no conflict — read `ldr-to-main-promote.yml` + `main-backmerge-to-ldr.yml` (or their
      PM-hosted reusable equivalents) to find where the source-range/merge-base boundary is computed, and confirm which
      of the 3 candidates above (or another fix) actually closes the gap. Repo: unified-trading-pm (workflows),
      cross-repo impact.
- [ ] [DATA] P2. Fleet sanity sweep: given this pattern could have silently reintroduced OTHER reverted commits
      undetected (not just this session's), spot-check a handful of recent revert commits across the fleet
      (`git log     --grep='^revert' --all` per repo) and confirm their reverted content is still actually absent on
      both `main` and `live-defi-rollout` (content check, not just `git log` ancestry) — this exact "log says reverted,
      file says not" mismatch is the failure signature to search for.
- [ ] [SCRIPT] P3. Once the root cause + fix shape is confirmed, document the invariant in
      `/codex/08-workflows/ci-cd-flow.md` (or wherever the promote/backmerge mechanics are the SSOT) so this class of
      race is a known, named risk rather than something each agent has to rediscover.
