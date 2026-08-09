---
doc_type: issue
title:
  "agent-orchestrator's `main` and `live-defi-rollout` workflow files have re-diverged for 3 files, caught live by the
  new rollout-workflow-templates.sh parity check"
created: 2026-08-09
author: slot-15
assigned_vm: planning
status: open
tags: [ci-cd, promotion-blocked, dangling-reference, code-conflict, agent-orchestrator, cross-repo, workflow-parity]
source:
  [
    citadel/cicd task "Rollout-process gap" (todo 4 of
    agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md),
    first real-world run of the new post-rollout parity check that todo added to rollout-workflow-templates.sh,
  ]
summary:
  "The parity check added in this same session (rollout-workflow-templates.sh's new check_main_ldr_parity, todo 4 of
  agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md) found agent-orchestrator's `main` and
  `live-defi-rollout` have re-diverged for 3 workflow files — despite that issue doc's todos 1-3 having closed this
  exact class of drift on 2026-08-07. Reproducing the exact rollout-process gap todo 4 was built to catch, live, on its
  first real run."
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
related:
  [
    /plans/active/issues/agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md,
    /plans/archive/2026_08/issues/alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
parent_epic: infrastructure_master
resolved_by:
locked_by:
locked_since:
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
---

# agent-orchestrator: main <-> live-defi-rollout workflow-file drift, caught by the new parity check

## What I found

Implementing todo 4 of `agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md` (extend
`rollout-workflow-templates.sh` with a post-rollout `origin/main` vs `origin/live-defi-rollout` byte-compare pass), I
ran the new check fleet-wide (`bash scripts/workflow-templates/rollout-workflow-templates.sh --dry-run`, read-only — no
files written) to validate it end-to-end against real repo state. It found 3 mismatches, ALL in `agent-orchestrator`
(every other repo in the fleet is clean):

1. **`.github/workflows/notify-slack.yml` — present on `main`, MISSING on `live-defi-rollout` entirely.** Confirmed via
   `git show origin/live-defi-rollout:.github/workflows/notify-slack.yml` → `fatal: path ... does not exist`. This is
   the exact file PR #814 (`agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md` todo 2) merged into
   `main` on 2026-08-07T06:38:37Z — that merge landed the file on `main` only; nothing subsequently rolled it out to (or
   pushed it onto) `live-defi-rollout`. Currently nothing on `live-defi-rollout` calls it (`git grep` for
   `notify-slack.yml` across LDR's `.github/workflows/` returns zero hits, vs 2 callers on `main`:
   `main-backmerge-to-ldr.yml`, `semver-agent.yml`), so this is not breaking any LDR workflow TODAY — but it is a real,
   silent gap in the shared CI-alerting carrier's fleet propagation this exact issue class was supposed to have closed.
2. **`.github/workflows/image-build-gate.yml` — comment-only drift.** `main`'s copy still reads "Calls PM-hosted
   reusable workflow image-build-validate.yml"; `live-defi-rollout`'s copy reads "Calls unified-trading-ci-hosted
   reusable workflow image-build-validate.yml (extracted from unified-trading-pm 2026-08-06 ...)" — the LDR copy already
   reflects the 2026-08-06 shared-CI-repo extraction, `main`'s does not. Comment-only (the functional `uses:` line was
   not diffed as differing), but it's the same staleness signature as the other two.
3. **`.github/workflows/quality-gates-v2.yml` — functional drift.** `main`'s copy triggers on `push: branches: [main]` ;
   `live-defi-rollout`'s copy triggers on `push: branches: [live-defi-rollout]` (plus 2 extra explanatory comment blocks
   about the `ldr_terminal`/`CI_TRIGGER_BRANCH` exception). This is NOT an intentional per-branch difference —
   `rollout-workflow-templates.sh`'s `get_ci_trigger_branch()` renders the SAME content for a given repo regardless of
   which branch is checked out locally when the script runs (the value comes from `workspace-manifest.json`'s per-repo
   `ci_trigger_branch` field, not from the current branch). `main`'s copy is simply a stale pre-`ldr_terminal`-flip
   render that was never re-rolled-out + pushed after `agent-orchestrator`'s `promotion_model` flipped to `ldr_terminal`
   (2026-08-05, per `agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`).

All 3 reproduce the identical shape `agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md` already
described and fixed once (2026-08-07) — the fix did not stick because nothing keeps `main` and `live-defi-rollout` in
sync going forward; only a one-time reconciliation was done. This is why todo 4 (the parity check itself) exists; this
finding is its first real catch, not a new distinct root cause.

## Why it matters

`agent-orchestrator` is `ldr_terminal` (promotion terminates at LDR, no LDR->main promotion PR in the normal sense per
`agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`), so there is currently no automatic mechanism that would ever
re-surface or fix this drift the way a normal `ldr_main` repo's promotion-PR gate would. Left alone, `main` keeps
silently drifting further from `live-defi-rollout`'s actual CI configuration — which matters because
`main-backmerge-to-ldr.yml` and `semver-agent.yml` (both real, in-use workflows) still live on `main` and reference
`notify-slack.yml`, so `main`'s own workflow surface is not merely a stale mirror; it is independently executed.

## Recommended decision

Reconcile `agent-orchestrator`'s `main` branch's `.github/workflows/` to match what `rollout-workflow-templates.sh`
would currently render (the 3 files above), the same way todo 1/3 of the source issue did the first time — then re-run
this doc's own parity check to confirm green. This is NOT a `rollout-workflow- templates.sh` bug (the script is doing
its job correctly and read-only here); it is stale content on one specific repo's `main` branch that the script has no
push/reconciliation step for by design (operator ruling in the source issue: the script "does not push", per its own
header comment).

- [ ] [CICD] P2. Open a PR against `agent-orchestrator@main` that adds `.github/workflows/notify-slack.yml` (copy
      verbatim from `scripts/workflow-templates/notify-slack.yml` — same content already correctly on
      `live-defi-rollout`) and updates `image-build-gate.yml` + `quality-gates-v2.yml` to match the current
      `live-defi-rollout` render (re-run `rollout-workflow-templates.sh --repo agent-orchestrator` against a
      `main`-checked-out worktree, or hand-port the 3 diffs shown above). Verify via `quality-gates-v2` going green on
      the PR. Repo: agent-orchestrator.
- [ ] [CICD] P3. Re-run `rollout-workflow-templates.sh --dry-run --repo agent-orchestrator` (see § "Recommended
      decision" above for the full command) after the above lands and confirm the parity check reports 0 mismatches for
      agent-orchestrator. Record the result in this doc's Progress Log. Repo: unified-trading-pm.

## Progress Log

- 2026-08-09 (slot-15, cicd): Filed while implementing + validating todo 4 of
  `agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md` (the new post-rollout parity check). Ran the
  new check fleet-wide read-only (`--dry-run`, no writes) as part of validating the implementation; it found these 3
  real mismatches, confirmed independently via direct `git show origin/<branch>:<path>` reads (not just the script's own
  output) before filing. Every other repo in the fleet reported 0 mismatches. Not fixed inline — out of todo 4's own
  scope (which is the check itself, not fleet reconciliation), and fixing agent-orchestrator's `main` branch CI files is
  a distinct, separately-scoped change.
