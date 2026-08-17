---
doc_type: issue
title: slot 9's unified-trading-ci clone is checked out on main (not live-defi-rollout) carrying 3 unpushed commits attributed to slot-2/main-agent
summary: >-
  Slot 9's unified-trading-ci repo clone violates the Path-B invariant (every slot repo
  should be checked out directly on live-defi-rollout) — it is currently on local branch
  `main` (ahead 3 / behind 1 vs origin/main), while its local `live-defi-rollout` branch
  sits 27 commits behind origin/live-defi-rollout, untouched. The 3 ahead commits are
  authored `ikennaigboaka [slot-2·laptop]` and `ikennaigboaka [main·laptop]` — NOT slot 9
  — meaning this is cross-slot/cross-identity contamination, not slot 9's own work. Given
  the unclear provenance and the wrong-branch state, not pushing or otherwise mutating this
  repo myself; flagging for infra triage rather than guessing.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-ci]
scope: [engineer, admin]
tags: [infra, git, wrong-branch, cross-slot, per-tab-worktrees, provenance]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-17"
author: slot-9 (data_engineering)
last_updated: "2026-08-17"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: infra
drift_direction: none
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by: slot-1 (infra craft), 2026-08-17 — direct git repair of slot 9's clone + unified-trading-pm@2d746128d0
source: >-
  Discovered via the orchestrator's own "GIT STATUS RED" auto-nudge (message_ids 9204,
  9208) delivered on /boot to slot 9 while picking up an unrelated data_engineering task;
  investigated per the nudge's own instruction before acting, since the standard remedy
  (`git add . && git commit && git push`) does not cleanly apply to a wrong-branch,
  foreign-attributed state.
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
---

# slot 9's unified-trading-ci clone: wrong branch + cross-slot unpushed commits

> 🟢 **RESOLVED 2026-08-17 (slot 1, infra).** By the time this was picked up, local `main` in slot 9's clone was
> already byte-identical to `origin/main` (verified `git rev-parse` on both sides) — the fleet's normal promotion
> pipeline had already landed the flagged content in the hours since this doc was filed, so there was nothing left
> to reconcile or discard. Re-checked out the clone onto `live-defi-rollout` and fast-forwarded to
> `origin/live-defi-rollout`, restoring the Path-B invariant. Also hardened `agents/worker.md`'s fresh-pull loop
> with a branch-identity WARN so a future wrong-branch clone surfaces immediately instead of silently no-op'ing.
> See Progress Log for full evidence.

## What I found

`cd .tabs/9/unified-trading-ci && git status --porcelain=v1 --branch`:

```
## main...origin/main [ahead 3, behind 1]
```

`git branch -vv`:

```
  live-defi-rollout 2c48c4b [origin/live-defi-rollout: behind 27] fix(semver): base the squash-promote PATCH-fallback on repo-wide source_touched, not SOURCE_DIR-prefix
* main              403c921 [origin/main: ahead 3, behind 1] fix: update before downstream merge
```

The clone is currently checked out on `main`, not `live-defi-rollout` — a direct violation of the Path-B
topology invariant (`/codex/05-infrastructure/per-tab-worktrees.md`: "each slot `.tabs/<N>/<repo>` is its OWN
`git clone --reference` checked out **directly on `live-defi-rollout`**"). The local `live-defi-rollout` branch
exists but is 27 commits stale — nobody has advanced it in this clone in some time (my session's own
fresh-pull loop this morning fast-forward-merged `origin/live-defi-rollout` onto whatever branch was checked
out at the time, silently succeeding without verifying branch identity — worth noting as a secondary gap in
the fresh-pull script itself, since it never asserts `git branch --show-current == live-defi-rollout`).

The 3 commits ahead of `origin/main`:

```
403c921 2026-08-16T19:03:20+01:00 ikennaigboaka [slot-2·laptop] fix: update before downstream merge
799f0f3 2026-08-16T19:10:14+01:00 ikennaigboaka [main·laptop] chore: merge origin/main into live-defi-rollout (sync Slack alert streak-sha linking commit)
3932f64 2026-08-16T19:09:31+01:00 ikennaigboaka [main·laptop] ci: add self_hosted_runner_labels input to image-build-validate.yml
```

None of these carry a `slot-9` identity — they're attributed to `slot-2` and the `main` agent, both on a
`laptop` host, not this VM. This is NOT slot 9's own in-flight work sitting here; it is either (a) leftover
state from when this clone (or its underlying `--reference` object store) was used by a different
slot/session before being reassigned to slot 9, or (b) some cross-checkout contamination worth its own root
cause. The commit subjects themselves look like real, intentional work (a semver-related merge-reconciliation
+ a CI workflow input addition), not scratch/garbage — i.e. this is probably real work that never finished
landing, not something safe to just discard.

## Why it matters

Per CLAUDE.md's Multi-agent safety section, a slot's HEAD must stay ancestor-or-equal of
`origin/live-defi-rollout` — this clone currently satisfies neither that invariant (wrong branch entirely) nor
does pushing the 3 `main`-branch commits obviously reconcile it, since their content and authorship don't
belong to this slot. Blindly pushing risks landing foreign, possibly-stale work under unclear conditions;
blindly discarding risks losing real work. Left as a standing GIT STATUS RED nudge, this will keep
re-triggering the orchestrator's auto-nudge on every dispatch to slot 9 without ever resolving, since the
standard remedy doesn't fit.

## Recommended decision

An infra-craft worker (or the main agent, given two of the three commits are attributed to it) should
determine: (1) whether these 3 commits' content is already landed elsewhere under a different sha (in which
case this branch state is just stale and can be reset to track `live-defi-rollout` cleanly), or (2) whether
they represent real unlanded work that needs to be cherry-picked/reconciled onto `live-defi-rollout` properly
via quickmerge, or (3) whether slot 9's `unified-trading-ci` clone itself needs to be re-cloned/repaired to
restore the Path-B invariant. Not resolving this myself — outside my task's scope and craft, and the
provenance is too unclear to act on unilaterally.

## Todos

- [x] ✅ [INFRA] P2. **RESOLVED — content already landed, no reconcile/discard needed.** Verified `origin/main`
      exactly matched local `main` in slot 9's `unified-trading-ci` clone (`git rev-parse` both sides identical:
      `c0d10ba6cfe437ac299eebb26f38f2e5ff5dd758`) — disposition (1) from this doc's own recommended-decision list.
      `origin/main`'s log shows the two content commits present under new shas but matching author + timestamp +
      subject exactly (`c0d10ba`="fix: update before downstream merge" @ 2026-08-16T19:03:20+01:00 [slot-2·laptop];
      `e88304a`="ci: add self_hosted_runner_labels input to image-build-validate.yml" @ 2026-08-16T19:09:31+01:00
      [main·laptop]) — landed via the fleet's normal promotion pipeline in the hours since this doc was filed,
      most likely rebased/rewritten in the process (hence the new shas). The third commit (a `main`→
      `live-defi-rollout` sync merge for a Slack alert streak-sha feature) is independently present on
      `origin/main` via `7000ac0` ("link QG-fail and QG-recovered Slack alerts by a shared streak-start sha").
      Confirmed no live process in `.tabs/9` before touching anything (no `.agent-claim` file; a `claude`-process
      cwd scan against every live pid found no match under `.tabs/9/`), and the working tree was clean, so the
      branch switch carried zero risk of losing anything. Re-checked out `live-defi-rollout` and fast-forwarded to
      `origin/live-defi-rollout` (`git merge --ff-only`, `2c48c4b..3209654`, clean FF, 11 files touched — CI
      workflow + `.gitleaks.toml`/`.pre-commit-config.yaml` additions). Confirmed done-condition: `git branch -vv`
      now shows `* live-defi-rollout 3209654 [origin/live-defi-rollout]` (zero ahead/behind) and
      `main c0d10ba [origin/main]` (zero ahead) — no stray `main`-branch ahead commits remain.
- [x] ✅ [INFRA] P3. Added a branch-identity guard to `agents/worker.md`'s fresh-pull loop (§ "1b) FRESH-PULL") —
      unified-trading-pm@2d746128d0. Before the `git status --porcelain` dirty-check, the loop now reads
      `git branch --show-current` and compares it against `$base` (`live-defi-rollout`), WARNing and skipping the
      pull for that repo (never hard-failing) when they differ, naming the actual checked-out branch — instead of
      silently no-op'ing or, worse, `git merge --ff-only` succeeding onto a misnamed branch, which is exactly the
      gap that let this slot 9 state go undetected. Kept WARN-only per this workspace's established pattern for
      git-hygiene detection (the `SessionStart` collision check, the commit-time Quickmerge-provenance hook) — a
      worker mid-investigation of a wrong-branch clone (e.g. this very incident) must not be blocked by its own
      fresh-pull step. No separate codex-doc update: `/codex/05-infrastructure/per-tab-worktrees.md` already
      states the branch-identity invariant this guard enforces ("checked out **directly on `live-defi-rollout`**")
      — the guard hardens DETECTION of an existing rule, it doesn't establish a new one.

## Progress Log

- **2026-08-17 (slot 9, data_engineering)**: filed after investigating a recurring "GIT STATUS RED" auto-nudge
  (message_ids 9204, 9208) that didn't fit the standard remedy. Not pushed/reset/touched — flagging for infra
  triage given foreign commit provenance and unclear resolution.
- **2026-08-17 (slot 1, infra craft) — both todos resolved.** Investigated read-only first: confirmed no live
  process occupies `.tabs/9` (no `.agent-claim`, no matching `claude`-process cwd), then found local `main` in
  slot 9's `unified-trading-ci` clone is byte-identical to `origin/main` (exact `git rev-parse` match on both
  sides) — the 3 originally-flagged commits' content is already safely on origin, landed by the normal fleet
  pipeline sometime after this doc was filed this morning. Nothing to reconcile or discard; switched the clone to
  `live-defi-rollout` and fast-forwarded it (safe: zero divergent local content, clean working tree). Also fixed
  the secondary gap this doc's own "What I found" section flagged — `worker.md`'s fresh-pull loop never asserted
  branch identity — by adding a WARN-only guard (unified-trading-pm@2d746128d0). Archiving now per
  `/codex/11-project-management/issue-doc-lifecycle.md` (ACKED-INTO-CODE — both fixes are shipped/verified, no
  reason to leave this in `active/issues/`); this is a single-repo (mode-1) doc so the same-commit flip+archive
  shape is sanctioned per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. Corpus grep for
  this doc's filename found zero referrers — no referrer-fixup needed.
