---
doc_type: issue
title: >-
  agent-orchestrator's `main` still references the deleted `unified-trading-pm` reusable CI workflows (dangling
  post-shared-CI-extraction reference) AND carries a genuine unrelated multi-file code conflict vs `live-defi-rollout` —
  both block promotion; found as a 4th layer while chasing the notify-slack.yml backmerge deadlock
summary: >-
  Discovered as a byproduct of the fleet-wide `notify-slack.yml` backmerge-chicken-and-egg audit (see
  `alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md` and
  `strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md` § "Fleet-wide audit"). Two DISTINCT,
  independent problems block `agent-orchestrator`'s LDR→main promotion right now:

  1. **Dangling reusable-workflow reference**: `agent-orchestrator`'s `main` branch `quality-gates-v2.yml` and
     `image-build-gate.yml` still reference
  `IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates-v2.yml@live-defi-rollout`
     / `image-build-validate.yml` — both confirmed ABSENT from `unified-trading-pm@live-defi-rollout` (moved to
     `unified-trading-ci` by the 2026-08-06 shared-CI-repo extraction). Every OTHER repo in the fleet already points at
     `unified-trading-ci` (via LDR); `agent-orchestrator`'s `main` is the only one of the 10 backmerge-deadlocked repos
     that hasn't received that repoint AT ALL — not even via a stuck promote PR, because its promote PR (#813, see
     below) has never merged. Net effect: `quality-gates-v2` 0s-fails with the same "workflow file issue" signature as
     the notify-slack.yml bug, but for a DIFFERENT file and requiring a content edit (repoint the `uses:` reference),
     not adding a missing file — a distinct fix.
  2. **Genuine unrelated code conflict**: `agent-orchestrator`'s promote PR #813 (`main` ← `live-defi-rollout`) has a
     real, large, multi-file content conflict — `dashboard/src/layout.tsx`, `dashboard/src/types.ts`,
  `server/config.py`,
     `server/context_lifecycle.py`, `server/main_agent_keeper.py`, `server/models/agents.py`, `server/routes/agents.py`,
     plus test files — genuine parallel-development divergence between `main` and LDR, NOT a mechanical version-pin
     bump. This needs an owning engineer/agent to actually reconcile the two sides, not a scripted take-LDR resolution.

  A scoped, single-file `notify-slack.yml`-only PR (#814, off `main`, touching nothing else) was opened to at least
  clear the backmerge-deadlock class for this repo — it is correct and harmless but WILL NOT MERGE until problem 1 above
  is separately fixed, since `quality-gates-v2` on `main`-based branches fails regardless of PR content. Problem 2
  additionally blocks the repo's *actual* promotion (PR #813) independent of PR #814's fate.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, unified-trading-ci]
scope: [engineer, admin]
tags: [ci-cd, promotion-blocked, dangling-reference, code-conflict, agent-orchestrator, cross-repo]
related:
  [
    /plans/active/issues/alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md,
    /plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
  ]
created: 2026-08-06
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  "fleet-wide notify-slack.yml backmerge-deadlock audit sub-agent, 2026-08-06 ~16:30-17:00 UTC, reported as a 4th layer
  per explicit instruction not to chase it autonomously"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md,
    /plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md,
    /plans/archive/issues/ao_fleet_health_investigation_followups_2026_08_06.md,
    agent-orchestrator/.github/workflows/,
    agent-orchestrator/server/routes/agents.py,
    /scripts/workflow-templates/rollout-workflow-templates.sh,
  ]
---

# agent-orchestrator: dangling PM workflow reference + genuine code conflict block promotion

## Background

Not urgent/blocking anything else today — `agent-orchestrator` was simply the one repo (of the 10 affected by the
`notify-slack.yml` backmerge deadlock) where the scoped single-file fix could not fully resolve the repo's promotion
state, because two OTHER, older, unrelated problems sit underneath it. Neither problem was introduced by today's
notify-slack.yml work; both pre-date it and were only surfaced by the audit.

## Todos

- [x] [CICD] P2. Repointed `agent-orchestrator@main`'s `.github/workflows/quality-gates-v2.yml` and
      `image-build-gate.yml` from
      `IggyIkenna/unified-trading-pm/.github/workflows/{python-quality-gates-v2,image-build-validate}.yml@live-defi-rollout`
      to `IggyIkenna/unified-trading-ci/.github/workflows/{python-quality-gates-v2,image-build-validate}.yml@main` —
      exactly matching the form `live-defi-rollout` already carries for both files. Followed the doc's own
      already-tested guidance: NOT a raw direct push (confirmed still rejected by the ruleset,
      `required_status_checks: ["Quality Gates (agent-orchestrator) / quality-gates-v2", "sit-gate/fleet-green"]`) —
      opened as a minimal PR off `main` touching only these two lines. Evidence: agent-orchestrator PR #817
      (`fix/repoint-main-ci-to-unified-trading-ci`, commit 781f31f). Its own `quality-gates-v2` run correctly picked up
      the fixed reference from the PR's own branch (same-repo PR, not a fork) and dispatched real QG-slice jobs instead
      of the instant "workflow file issue" 0s-fail — self-resolving as expected. (repo: agent-orchestrator)
- [ ] [CICD] P2. Confirm PR #817 (todo 1) merges to `main` cleanly once its checks finish, then confirm PR #814
      (notify-slack.yml-only, already open, harmless) can now pass `quality-gates-v2` and merges too.
- [x] [ENG] P2. Reconciled PR #813's real code conflict (`dashboard/src/layout.tsx`, `dashboard/src/types.ts`,
      `server/config.py`, `server/context_lifecycle.py`, `server/main_agent_keeper.py`, `server/models/agents.py`,
      `server/routes/agents.py`, test files) between `main` and `live-defi-rollout` — read both sides' actual diverged
      history rather than a scripted take-one-side pass; full detail + the one real bug caught along the way (a
      reintroduced `pick_headroom_account` fallback the auto-merge would have silently un-fixed) is in
      `ao_fleet_health_investigation_followups_2026_08_06.md`'s own PR #791 todo (same underlying fix — this doc's
      Problem 2 and that doc's #791 backmerge are the same conflict, closed together). Evidence:
      agent-orchestrator@5872b3e5. (repo: agent-orchestrator)
- [ ] [DEVOPS] P3. Rollout-process gap (flagged by the same audit, not `agent-orchestrator`-specific): today is the
      SECOND time in one day a shared-CI-repo-extraction/rollout event landed new/moved workflow files on
      `live-defi-rollout` without every affected repo's `main` (or even every repo's own LDR — see the 3-repo
      sub-finding in the strategy-service doc's "Fleet-wide audit" section) being caught up in the same pass, each time
      reproducing the identical chicken-and-egg (the file's absence breaks the one mechanism — `main-backmerge-to-ldr` —
      that would normally deliver it). `scripts/workflow-templates/rollout-workflow-templates.sh` only writes local
      files into whichever branch happens to be checked out per-repo at run time; it does not verify parity across
      `main` and every repo's `live-defi-rollout`, and does not push. Consider having the rollout script (or the fleet
      bot's health check) assert that every repo's `main` carries the files its own `main-backmerge-to-ldr.yml` needs
      before a rollout is considered complete. Operator/rollout-process-owner decision on whether to build this now or
      accept the recurring cost.

## Progress Log

- **2026-08-07**: Closed todos 1 and 3 (Problem 1 dangling workflow ref + Problem 2 code conflict) — found while
  finishing `ao_fleet_health_investigation_followups_2026_08_06.md`'s PR #791 todo and following its cross-reference
  here. PR #817 opened for todo 1 (self-resolving fix — a same-repo PR picks up its own branch's corrected workflow
  content); PR #813's underlying conflict resolved via a fresh main→LDR backmerge (agent-orchestrator@5872b3e5), PR #791
  now `state: MERGED`. Todo 2 (confirm #817 + #814 actually merge) and todo 4 (rollout-process gap, operator decision)
  remain open — this doc is NOT ready to archive yet.
- **2026-08-06 ~17:20 UTC**: filed as its own dated issue doc per this session's `/autonomous` tracking-doc rule ("if a
  4th layered CI/CD blocker surfaces, file it as its own dated issue doc rather than growing this one indefinitely") —
  content sourced from the fleet-wide-audit sub-agent's findings (originally landed as prose in
  `strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md`'s "Fleet-wide audit" section, commit
  `21a698c09`), converted here into tracked `- [ ]` todos per the workspace's "every deferral is a todo, never prose"
  rule. Not chased further in the main session — correctly out of scope for the notify-slack.yml fix itself, and
  `agent-orchestrator`'s own promotion isn't blocking the alerting-service deploy-chain goal.

- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries) -- was under-scoped at 1 entry for 4 open
  todos spanning 2 repos. Added the parent tracking doc (this doc was filed as its "4th layer" per that doc's own todo
  3), the two workflow files' directory (todo 1's repoint target), one representative conflicted file from PR #813's
  7-file list (`server/routes/agents.py`, also independently a hotspot in a sibling agent-orchestrator issue), and the
  rollout script named by todo 4.
- **context-scout 2026-08-07 (fingerprint cross-reference, batch 8)**: confirmed step-4a match — this doc's PR #813
  literal is the SAME `agent-orchestrator` PR independently tracked in
  `/plans/active/issues/ao_fleet_health_investigation_followups_2026_08_06.md` (same date), which attributes #813's
  stall to the still-unresolved main↔LDR backmerge PR #791. Complementary, not duplicate: that doc doesn't yet know
  about this doc's Problem 1 (dangling PM-workflow ref) or Problem 2 (the genuine 7-file code conflict) blocking #813
  independently of #791. Added to `context_scope` (now 6 entries); added the reverse pointer on that doc too.
