---
doc_type: issue
title: >-
  image-build-validate.yml (unified-trading-ci) hardcoded self-hosted [self-hosted, glue] runners that were deregistered
  fleet-wide — every public repo's "validate / GCP Cloud Build" required check has been stuck QUEUED forever since
  before 2026-08-06, silently blocking all LDR→main promotions
summary: >-
  A 4th independently-discovered CI/CD bug found while chasing `alerting-service@4e252b4`'s deploy (see
  `alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md` for layers 1-3). Root cause: two
  correct-at-the-time changes collided.

  1. `self_hosted_runner_public_repo_revert_2026_08_05.md` (todo 21) cleanly deregistered the self-hosted `glue`
     runner pool for all 17 public repos, since their OWN workflows (`quality-gates-v2.yml` etc.) all reverted to
     `ubuntu-latest`. That plan's todo 23 explicitly checked `image-build-gate.yml`/`image-build-validate.yml` and
     correctly found nothing to fix AT THE TIME — the reusable workflow lived in `unified-trading-pm` (itself mostly
     private), so self-hosting it was still valid.
  2. `shared_ci_workflow_repo_extraction_2026_08_06.md` extracted `image-build-validate.yml` out of
     `unified-trading-pm` into a brand-new, PUBLIC repo (`unified-trading-ci`), carrying its
     `runs-on: [self-hosted, glue]` over unchanged. Nobody re-asked "does this still need self-hosting now that its
     new home is public and its callers' pools are gone" — the extraction plan's scope was purely mechanical
     (move the file), not a runner-choice re-audit.

  Net effect: **zero runners anywhere in the fleet** could ever claim this workflow's 3 jobs (`build-gcp`, `build-aws`,
  `gate`) — not the 17 calling repos (deregistered), not the new host repo (never had one registered). Every PR touching
  a public repo has had its required `image-build-gate` check hang in `QUEUED` state forever. Reproduced live on 2+
  repos: `alerting-service` PR #347 (queued since `2026-08-07T05:41:54Z`) and `greeks-service` run `31081812648` (queued
  since `2026-08-06T07:40:14Z`, >24h) — predates and is unrelated to the 2026-08-06/07 GitHub Actions platform incident
  (which is separately confirmed fully resolved).
status: resolved
nature: issue
asset_group: [cross-cutting, ci]
stage: [meta]
repos: [unified-trading-ci, alerting-service, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, promotion-blocked, self-hosted-runners, glue-runners, regression, fleet-wide, deploy-chain]
related:
  [
    /plans/active/issues/alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md,
    /plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md,
    /plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md,
    /plans/active/issues/agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md,
  ]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  "main-session /autonomous loop, found while chasing why alerting-service PR #347's required checks wouldn't clear even
  after the GH Actions incident resolved, 2026-08-07"
resolved_by:
  "unified-trading-ci@a37205d97f3a9b44657e927033a9bc02d4ce651d (live-defi-rollout),
  unified-trading-ci@5bbc277d9b8da9e3cb3e460fc6fba9f470c077f2 (main)"
locked_by:
locked_since:
context_scope:
  [
    /plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md,
    /plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md,
  ]
---

# image-build-validate.yml stranded on deregistered self-hosted runners

## Fix applied

Reverted all 3 jobs (`build-gcp`, `build-aws`, `gate`) in
`unified-trading-ci/.github/workflows/image-build-validate.yml` from `runs-on: [self-hosted, glue]` to
`runs-on: ubuntu-latest` — mirroring the exact reasoning and precedent already established (and successfully applied 18
times) by `self_hosted_runner_public_repo_revert_2026_08_05.md`: none of these 3 jobs run a local build — they only
trigger and poll REMOTE GCP Cloud Build / AWS CodeBuild jobs via `gcloud`/`aws` CLI (both preinstalled on
`ubuntu-latest` images; `google-github-actions/setup-gcloud@v3` installs the SDK regardless), so there is no
self-hosting requirement to begin with. Public-repo GitHub-hosted minutes are unmetered, so this also costs $0.

Shipped as a direct push (no `quickmerge`/`quality-gates.sh` exists in this brand-new, YAML-only repo — confirmed before
pushing):

- `unified-trading-ci@a37205d97f3a9b44657e927033a9bc02d4ce651d` on `live-defi-rollout`.
- Cherry-picked onto `main` as `unified-trading-ci@5bbc277d9b8da9e3cb3e460fc6fba9f470c077f2` (branch protection on this
  repo's `main` has no required-status-checks/PR-only rule, confirmed via
  `gh api repos/IggyIkenna/unified-trading-ci/branches/main/protection` before pushing directly — a direct push was safe
  and the only path, since `alerting-service`'s `image-build-gate.yml` references
  `unified-trading-ci/.../image-build-validate.yml@main`, not `@live-defi-rollout`).

**Live-verified the fix actually works**, not just shipped: pushed an empty retrigger commit to `alerting-service` PR
#347's branch (tree-identical to LDR, zero content change — confirmed via
`git diff HEAD origin/live-defi-rollout --stat` before and after) to force a fresh check run, since the ALREADY-QUEUED
job from before the fix was permanently stuck (a queued job doesn't retroactively pick up a changed `runs-on:` — it
needed a brand new dispatch). Result: `validate / GCP Cloud Build — alerting-service` and
`validate / Dual-cloud image build gate` both flipped `QUEUED` → `SUCCESS` within seconds of the retrigger.

## Still open

- [ ] [INFRA] P2. Fleet-wide sweep: are there OTHER reusable workflows that moved in the same 2026-08-06
      `shared_ci_workflow_repo_extraction_2026_08_06.md` extraction and might have the same
      still-self-hosted-but-now-stranded pattern? This issue only found `image-build-validate.yml` because it happened
      to be directly on the alerting-service deploy-chain critical path — a deliberate sweep of every file that plan
      moved (not just the one that happened to block this session) would catch any siblings before they're discovered
      the same accidental way. `grep -rn 'runs-on:.*self-hosted' unified-trading-ci/.github/workflows/` as a starting
      point (should be empty or intentional-only after this fix).
- [ ] [INFRA] P3. Add a standing check (or extend an existing rollout/extraction script) that flags "a reusable workflow
      file changed HOST REPO visibility (private→public) or its callers' runner registration changed" as a trigger to
      re-audit `runs-on:` choices — this is the second time in two days a repo-visibility/extraction change silently
      stranded a workflow (see the sibling dangling-PM-reference bug in
      `agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md`, same root class: an extraction moved a
      file without re-validating every consumer/runner-registration assumption that moved with it).

## Progress Log

- **2026-08-07 ~07:50 UTC**: found, root-caused, fixed, and live-verified in one pass while supervising
  `alerting-service` PR #347 (part of the `alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md`
  chase — this is that doc's 4th layer, filed separately per its own todo #3 rule). Did NOT chase the "other reusable
  workflows might have the same pattern" question further in this session (see open todo 1) to keep this converging on
  the immediate blocker; flagged for a dedicated follow-up sweep instead.
