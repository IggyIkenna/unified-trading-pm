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
status: resolved
nature: issue
asset_group:
  [ci] # corrected 2026-07-30 (/ag-closeout-audit ci) -- was [cross-cutting]; content is an LDR<->main
  # promote/backmerge pipeline race, squarely ci-tranche (CI/CD pipeline mechanics), not generic cross-AG content.
stage: [meta]
repos: [unified-trading-pm, instruments-service]
scope: [engineer, admin]
tags: [ci-cd, ldr-main, promote, backmerge, git, race-condition, silent-data-loss]
related:
  [
    /plans/active/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md,
    /plans/active/issues/ldr_to_main_promote_churn_fix_verification_2026_07_27.md,
    /plans/archive/issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md,
    /codex/08-workflows/ci-cd-flow.md,
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
  "unified-trading-pm@d3a47773a (Promoted-From-LDR trailer + explicit merge-base + check_no_silent_revert_loss guard,
  fleet-rolled-out 23/24), bounded fleet spot-check (2026-07-30, 3/4 clean, 1/4 explainable churn), and codex doc
  /codex/08-workflows/ci-cd-flow.md updated with the named invariant"
locked_by:
---

> **✅ ARCHIVED 2026-07-30** — all 4 todos `[x]` (root-cause, fix + fleet rollout, bounded fleet spot-check, codex
> documentation). `status: resolved`, `resolved_by` set, unlocked. Moved to `plans/archive/issues/`.

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

## Root cause — CONFIRMED (2026-07-29, slot 8, todo #1)

Ground-truthed against the live `instruments-service` graph (all times UTC; SHAs re-verified reachable):

- fix `2941646c` @14:42:34 — adds the `ENV UV_EXTRA_INDEX_URL…` block.
- revert `8df0e94e` @14:52:52 — removes it; lands on `live-defi-rollout`.
- squash-promote `4fc4900a` @14:54:32 — **single parent `3d8af8c5`** (the _previous_ promote @14:35:12, which predates
  the fix); its squashed tree carries the fix but NOT the revert.
- backmerge `ed04b405` @15:01:35 — merges `main` → LDR.
- **`git merge-base 8df0e94e 4fc4900a` = `3d8af8c5`** (verified), and `3d8af8c5` is a verified ancestor of the fix
  `2941646c` (i.e. pre-fix).

Two mechanics compose:

1. **Frozen-head promote pins a PAST LDR SHA (the ENABLER).** `ldr-to-main-promote-fleet.yml` reads the LDR tip once
   (`LDR_SHA`/`LDR_TREE`), freezes an immutable per-SHA ref `promote/<repo>/<sha>`, and opens the promote PR from that
   frozen ref (workflow lines ~530-540). A promote tick that fired between the fix (14:42) and the revert (14:52) pinned
   `promote/instruments-service/2941646c` and opened a PR; that PR auto-merged at 14:54:32 (squash `4fc4900a`) AFTER the
   revert had already landed on LDR at 14:52:52 — so `main` received pre-revert content even though the revert was
   already on LDR. (The frozen head exists to close a _different_ TOCTOU — the SIT/differ classifying a tree other than
   the one gated, lines ~620-635 — but it opens this stale-content-to-main window.)
2. **The squash's stale merge-base makes the backmerge's 3-way merge blind to the revert (the SILENT-LOSS).** A squash
   commit discards LDR's real ancestry; `4fc4900a`'s only parent is the pre-fix `3d8af8c5`. So when
   `main-backmerge-to-ldr.yml` runs `git merge --no-ff origin/main` into LDR (line ~114), the 3-way merge-base is
   `3d8af8c5`:
   - base `3d8af8c5` (pre-fix): block **ABSENT**
   - ours = LDR tip (fix + revert): block **ABSENT** (net of add-then-revert)
   - theirs = `main` squash `4fc4900a`: block **PRESENT** → base==ours==absent, theirs==present ⇒ git reads it as
     "theirs _added_ new content, ours untouched" ⇒ takes theirs ⇒ the block is re-added to LDR. **No conflict** (ours
     never diverged from base on those lines), so no marker, no failed check — exactly the reported signature (`git log`
     shows the revert; file content does not). The backmerge's no-op guard (`rev-list LDR..main --count == 0`, line ~97)
     does not fire because the squash `4fc4900a` IS a `main` commit absent from LDR's graph.

### Which candidate closes the gap

- **Candidate 1 (shared reference point) — CLOSES it; the correct root fix.** The promote already knows the exact LDR
  SHA it promoted (encoded in `promote/<repo>/<sha>`). Concrete shape: the promote stamps a
  `Promoted-From-LDR: <ldr_sha>` trailer on the squash commit; the backmerge, when the incoming `main` commit carries
  that trailer, uses `<ldr_sha>` as the merge-base instead of the synthetic squash parent. Re-running the confirmed
  graph with base=`2941646c` (the promoted SHA): base=**present**, ours=**removed** (revert), theirs=**present** ⇒ git
  takes ours (removed) ⇒ revert preserved. Gap closed at the source.
- **Candidate 2 (post-backmerge content-diff) — does NOT close it as written ("flag, not block"): the stale content
  still lands on LDR.** Upgraded to a _blocking_ pre-push guard it closes it and is the right defense-in-depth: before
  the FF push (line ~153), if the merge result reintroduces on any path lines that an LDR commit within the promote
  window removed, ABORT the silent push and route to the existing visible conflict-PR + orchestrator escalation the
  backmerge already has (lines ~176-211). Repo-agnostic; catches residual cases the trailer cannot (a promote missing
  the trailer, or a genuine `main`-only revert).
- **Candidate 3 (document) — necessary, insufficient.** Does not change behavior; still required so the invariant is
  named (todo P3).

**Verdict:** ship Candidate 1 (trailer + merge-base) as the root closure AND Candidate 2-blocking as the safety net;
keep Candidate 3 as the doc. Implementation is tracked as its own todo below — this todo was root-cause +
confirm-fix-shape only.

## Todos

- [x] ✅ [SCRIPT] P1. Root-cause the exact squash-promote/backmerge mechanics that let step 5's merge silently
      reintroduce content step 3 removed with no conflict — read `ldr-to-main-promote.yml` + `main-backmerge-to-ldr.yml`
      (or their PM-hosted reusable equivalents) to find where the source-range/merge-base boundary is computed, and
      confirm which of the 3 candidates above (or another fix) actually closes the gap. Repo: unified-trading-pm
      (workflows), cross-repo impact. **DONE 2026-07-29 (slot 8)** — root cause confirmed + ground-truthed (see "Root
      cause — CONFIRMED" section above): frozen-head promote pins a pre-revert LDR SHA to `main`, and the squash's stale
      merge-base (`merge-base(revert, squash)`=`3d8af8c5`, verified pre-fix) makes the backmerge's 3-way merge take
      `main`'s re-added block with no conflict. **Candidate 1 (promote stamps `Promoted-From-LDR: <sha>` trailer →
      backmerge uses it as merge-base) is the fix that actually closes the gap**; Candidate 2 closes it only if upgraded
      to a blocking pre-push guard (best as defense-in-depth); Candidate 3 is necessary-but-insufficient documentation.
      Evidence: `unified-trading-pm` (this doc) — analysis only, no workflow code changed by this todo (implementation
      is the P1 todo below).
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-29 (slot 15).** Core fix implemented + shipped: `unified-trading-pm@d3a47773a`
      (`.github/workflows/ldr-to-main-promote-fleet.yml` stamps `Promoted-From-LDR: <sha>` on all 3 squash-merge
      arm/re-arm sites; `scripts/workflow-templates/main-backmerge-to-ldr.yml` + PM's own `.github/workflows/` copy read
      that trailer and force the 3-way merge onto that explicit base via
      `git merge-tree --write-tree     --merge-base=<sha>` instead of git's stale computed one; added
      `check_no_silent_revert_loss()` as a narrowly-scoped Candidate-2 defense-in-depth safety net — flags a merge that
      fully discards LDR's own last commit's effect, independent of the trailer). New regression test
      `scripts/quality-gates-base/tests/test-backmerge-silent-revert-loss-guard.sh` reproduces the CONFIRMED
      instruments-service graph shape with real git operations (control: default merge-base reintroduces the revert;
      fix: explicit-base preserves it; extracted real `check_no_silent_revert_loss()` correctly flags the buggy result
      and not the fixed one) — 7/7 assertions pass. **Scope note**: did NOT touch `ldr-to-main-promote.yml` (PM-only
      bot) — it uses `--merge`, not `--squash`, so it keeps real ancestry and carries no trailer; it is not vulnerable
      to this bug class at all. **Fleet rollout in progress**:
      `rollout-workflow-templates.sh --template main-backmerge-to-ldr.yml` synced all 24 sibling repo copies (verified
      only `unified-trading-pm` itself — deliberately excluded from that script — needed a manual sync, done, preserving
      its pre-existing `runs-on: ubuntu-latest` rather than silently flipping it to `[self-hosted, glue]` to match the
      canonical template, since that's an unrelated, out-of-scope drift). **23/24 shipped + content-verified** (fetched
      `origin/live-defi-rollout` and diffed against the canonical template for every repo — not just trusting a log
      line; this caught 2 commits the orchestrator's own branch-state-quarantine safety net had silently reset off their
      branches mid-session, both recovered from their `refs/wip-preserve/cascade-*` refs and re-shipped — see
      `issues/wip_preserve_refs_silently_unrecovered_2026_07_29.md`). **1/24 (`unified-trading-system-ui`) correctly NOT
      shipped** — its commit is made locally (`dc04a015`) but genuinely blocked behind `RB-036ef626`: a pre-existing,
      unrelated `tests/unit/wizard/parity-gates.test.ts` UAC-manifest-hash-mismatch red (confirmed via
      `git checkout HEAD~1` to fail identically before this fix's commit), already tracked in
      `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` +
      `archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` — the repo-blocker mechanism will notify
      on green, at which point `quickmerge --agent --files '.github/workflows/main-backmerge-to-ldr.yml'` ships it (no
      further diagnosis needed). Original todo text below, preserved for context:
      `unified-trading-pm/scripts/workflow-templates/`: (a) `ldr-to-main-promote-fleet.yml` (+
      `ldr-to-main-promote.yml`) — stamp a `Promoted-From-LDR: <LDR_SHA>` trailer on the squash-promote commit body (the
      SHA is already captured as `$LDR_SHA` at the content gate). (b) `main-backmerge-to-ldr.yml` — when an incoming
      `main` commit carries the `Promoted-From-LDR:` trailer, use that SHA as the merge-base (e.g.
      `git merge-recursive`/explicit base) so downstream LDR reverts are preserved; AND add a blocking pre-push guard:
      before the FF push, if the merge result reintroduces lines a recent LDR commit removed, abort the silent push and
      route to the existing conflict-PR + orchestrator escalation instead. Roll out via `rollout-workflow-templates.sh`
      (all copies committed + pushed). Add a regression test reproducing the confirmed instruments-service graph
      (add→revert→stale-squash→backmerge ⇒ revert must survive). Repo: unified-trading-pm (workflows), cross-repo
      impact.
- [x] ✅ [DATA] P2. **DONE 2026-07-30 (bounded spot-check, `live-defi-rollout` HEAD each repo).** Spot-checked 4 recent
      `revert(...)`/`Revert "..."` commits across 3 repos beyond this incident's own instruments-service commit: (1)
      `unified-api-contracts@bd8a46e9` (`revert(alerting): drop AlertCode.DEPLOYMENT_DIGEST`) — clean,
      `grep     DEPLOYMENT_DIGEST` on current `unified_api_contracts/canonical/crosscutting/alerting/codes.py` returns 0
      hits, the revert held. (2) `unified-trading-library@f5eb0c86`
      (`revert(deps): restore fastapi ceiling to <0.137.0`) — clean, current `pyproject.toml` reads
      `fastapi>=0.137.0,<1.0.0`, a later DELIBERATE version bump superseding the revert entirely (not a resurrection of
      the exact reverted `<0.138.0` ceiling). (3) `deployment-service@d8695e3`
      (`revert:     relocate deployments_registry.py to unified-trading-library`) — clean, the relocation was later
      legitimately RE-LANDED by its own explicit follow-up commit (`0676ba1`, "re-land the UTL relocation"), not a
      silent backmerge-driven reappearance. (4) `instruments-service@32a4df34`
      (`Revert "ci(workflow-templates): bump     create-github-app-token v1→v3"`) — **INCONCLUSIVE, not pursued further
      (bounded scope)**: current `.github/workflows/main-backmerge-to-ldr.yml` has `@v3`, matching what this specific
      revert removed, BUT `git log --follow -p` on that one line shows 8+ v1↔v3 oscillations across the file's history —
      this is a template-sync file (`rollout-workflow-templates.sh` repeatedly overwrites it from the canonical source),
      so repeated back-and-forth is expected churn from normal template iteration, not the clean single
      add→revert→stale-squash→backmerge shape this issue's root cause describes; also predates (2026-06-15) the
      confirmed bug window this issue traces (fix landed 2026-07-29). **Net**: 3/4 clean, 1/4 ambiguous-but-explainable
      by legitimate churn, 0/4 a confirmed NEW instance of the silent-resurrection pattern. Not exhaustive (this was
      explicitly scoped as "a handful," not a full-fleet census) — if a future agent wants full confidence, the
      `check_no_silent_revert_loss()` guard now shipped in `main-backmerge-to-ldr.yml` (see todo above) is the standing,
      ongoing defense rather than a one-off retrospective sweep.
- [x] ✅ [SCRIPT] P3. **DONE 2026-07-30 — `/codex/08-workflows/ci-cd-flow.md`** ("Named invariant: a revert landing near
      a promote-cycle boundary must survive the backmerge" section, added right after the "Convergence +
      conflict-resolution model" subsection): documents the mechanism (frozen-head promote pins a past LDR SHA, squash
      discards ancestry, backmerge's 3-way merge computes a stale base), the shipped fix (`Promoted-From-LDR:` trailer +
      explicit merge-base + `check_no_silent_revert_loss()` guard, `unified-trading-pm@d3a47773a`), and the practical
      takeaway (verify file CONTENT post-backmerge after a revert near a promote boundary, not just `git log` ancestry)
      — so this race is now a named, discoverable risk rather than something each agent has to rediscover from scratch.

## Progress Log

**2026-07-29T16:2xZ (slot 15).** Core fix + regression test shipped: `unified-trading-pm@d3a47773a` (root fix —
`Promoted-From-LDR` trailer stamp on all 3 squash-merge sites in `.github/workflows/ldr-to-main-promote-fleet.yml`;
explicit-base `git merge-tree --merge-base=<sha>` + `check_no_silent_revert_loss()` defense-in-depth safety net in
`scripts/workflow-templates/main-backmerge-to-ldr.yml` + PM's own `.github/workflows/` copy, preserving its pre-existing
`runs-on: ubuntu-latest` deliberately — never touched). New test
`scripts/quality-gates-base/tests/test-backmerge-silent-revert-loss-guard.sh` reproduces the CONFIRMED
instruments-service graph shape with real git operations (control: default merge-base reintroduces the revert; fix:
explicit-base preserves it; the extracted real `check_no_silent_revert_loss()` flags the buggy result and not the fixed
one) — 7/7 assertions pass, verified by running it directly. Scope note: `ldr-to-main-promote.yml` (PM-only, uses
`--merge` not `--squash`) intentionally NOT touched — it keeps real ancestry and is not vulnerable to this bug class.

**Fleet rollout — COMPLETE 2026-07-29T20:1xZ (slot 15), 23/24 shipped, 1 legitimately blocked.** Ran in TOPOLOGICAL
(dependency) order (`unified-api-contracts`/`unified-trading-library` first — quickmerge's pre-flight audit fails a
dependent repo whose own path deps still carry uncommitted changes; `deployment-api` hit this once against
`deployment-service` despite the manifest's own topo order listing them the other way — shipped `deployment-service`
first, then retried `deployment-api` clean). Final verification (fetched `origin/live-defi-rollout` fresh and diffed
each repo's `.github/workflows/main-backmerge-to-ldr.yml` byte-for-byte against the canonical template — not a
log/status check):

- **23/24 VERIFIED SHIPPED**: `unified-api-contracts`, `unified-trading-library`, `instruments-service`,
  `alerting-service`, `execution-service`, `features-service`, `fund-administration-service`, `greeks-service`,
  `market-data-processing-service`, `market-tick-data-service`, `ml-service`, `strategy-service`,
  `trading-agent-service`, `client-reporting-api`, `unified-trading-api`, `batch-live-reconciliation-service`,
  `deployment-api`, `deployment-service`, `deployment-ui`, `agent-orchestrator`, `e2e-testing`, `ibkr-gateway-infra`,
  `system-integration-tests`.
- **1/24 NOT shipped, correctly**: `unified-trading-system-ui` — commit `dc04a015` made locally, blocked behind
  repo-blocker `RB-036ef626` (pre-existing, unrelated `parity-gates.test.ts` UAC-manifest-hash red — verified via
  `git checkout HEAD~1` that it fails identically without this fix's commit; already tracked in 2 other open issue
  docs). The repo-blocker mechanism will message on green; ship then via
  `quickmerge --agent --files '.github/workflows/main-backmerge-to-ldr.yml'` from `.tabs/*/unified-trading-system-ui`.
- **2 near-misses caught by the fresh-diff verification, not by trusting a "SHIPPED" log line**:
  `unified-trading-library` and (from a prior, unrelated task) `strategy-service` both had a real commit silently reset
  off `origin/live-defi-rollout` by the orchestrator's own branch-state-quarantine safety net (working as designed — it
  preserves rather than destroys, to a `refs/wip-preserve/cascade-<repo>-<sha>` ref) after a mid-task session death.
  `unified-trading-library`'s was recovered and re-shipped in this task; `strategy-service`'s (unrelated, from
  2026-07-28) was left for its own todo — see `issues/wip_preserve_refs_silently_unrecovered_2026_07_29.md`.
- Transient host-governor SIGTERM kills (2 occurrences, `fund-administration-service` + one retry) and 2 UI repos
  needing a one-time `npm install` (missing `node_modules`, unrelated to this fix) were retried/fixed manually — none
  were genuine code problems.

**Driver scripts** (`ship_backmerge_rollout.sh`, `ship_backmerge_rollout2.sh`) lived in slot-15's scratchpad —
ephemeral, not promoted (regenerate by re-running `rollout-workflow-templates.sh --template main-backmerge-to-ldr.yml`
then, per dirty/ahead repo, commit → `quality-gates.sh` → `quickmerge --agent --files`, in topological order, verifying
each ship by fetching + diffing against the canonical template rather than trusting the push-succeeded return code
alone).
