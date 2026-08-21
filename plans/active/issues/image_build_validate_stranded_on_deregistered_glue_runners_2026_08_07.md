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
status:
  open # the blocking P0 fix landed + is live-verified (see "Fix applied"); 2 non-blocking P2/P3 follow-up
  # sweep/hardening todos remain open below
nature: issue
asset_group:
  [ci] # corrected 2026-08-09 (/ag-closeout-audit ci) -- was [cross-cutting, ci]; content is a GitHub Actions
  # self-hosted-runner/workflow-strand incident blocking LDR->main promotion, squarely ci-tranche (CI/CD pipeline
  # mechanics) -- already flagged as a mistag by the 2026-08-08 cross-cutting tranche run, never retagged until now
stage: [meta]
repos: [unified-trading-ci, alerting-service, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, promotion-blocked, self-hosted-runners, glue-runners, regression, fleet-wide, deploy-chain]
related:
  [
    /plans/archive/2026_08/issues/alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md,
    /plans/archive/2026_08/self_hosted_runner_public_repo_revert_2026_08_05.md,
    /plans/archive/2026_08/shared_ci_workflow_repo_extraction_2026_08_06.md,
    /plans/archive/2026_08/issues/agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md,
  ]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: cicd
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
    /plans/archive/2026_08/self_hosted_runner_public_repo_revert_2026_08_05.md,
    /plans/archive/2026_08/shared_ci_workflow_repo_extraction_2026_08_06.md,
    unified-trading-ci/.github/workflows/image-build-validate.yml,
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

- [x] ✅ [INFRA] P2. Fleet-wide sweep: are there OTHER reusable workflows that moved in the same 2026-08-06
      `shared_ci_workflow_repo_extraction_2026_08_06.md` extraction and might have the same
      still-self-hosted-but-now-stranded pattern? — `unified-trading-pm@39e71f811` (citation corrected 2026-08-09,
      `ci_satellite_ao_dispatch_batch6_finalize` todo 1 — the placeholder "this commit" resolved to the actual flip
      commit, verified ancestor of `origin/live-defi-rollout`). **Finding: none found.** Swept all 5 extracted files
      (`python-quality-gates-v2.yml`, `notify-slack.yml`, `image-build-validate.yml`,
      `.github/actions/setup-python-tools/action.yml`, `.github/actions/setup-agent-tools/action.yml`) in
      `unified-trading-ci`. `grep -rn 'runs-on:.*self-hosted' unified-trading-ci/.github/workflows/` → 0 hits (the only
      prior hit, `image-build-validate.yml`, is already fixed — confirmed all 3 jobs `runs-on: ubuntu-latest`).
      `notify-slack.yml` → `runs-on: ubuntu-latest`. The 2 composite actions have no `runs-on:` of their own (they run
      in the calling job's runner) and no self-hosted/glue references at all. `python-quality-gates-v2.yml` is the one
      file that still references self-hosted (`glue`) runners, but only via the parameterized
      `self_hosted_runner_labels` input that **defaults to `ubuntu-latest`** — this is the deliberate, working canary
      from `github_actions_operator_gated_followups_2026_07_17.md`'s quality-gates-v2 self-host decision, not the broken
      hardcoded-no-fallback pattern `image-build-validate.yml` had. Its only current non-empty-value callers
      (`strategy-service`, `execution-service`, `features-service`, `agent-orchestrator`, `e2e-testing`,
      `market-tick-data-service`, `ml-service`) are private repos never touched by
      `self_hosted_runner_public_repo_revert_2026_08_05.md` (that revert scoped to PUBLIC repos only) — their glue
      registration is unaffected by this extraction, so this is not a stranding case.
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
- **2026-08-07 ~08:35-08:50 UTC**: fleet-wide sweep for other promotion PRs stuck on this same symptom (dispatched agent
  task, not the open todos above — a same-day mechanical retrigger, not new tracked work). Confirmed the fix is live on
  `unified-trading-ci@main` (`5bbc277` at `2026-08-07T06:49:24Z`, all 3 jobs `runs-on: ubuntu-latest`). Checked every
  open `chore(promote): LDR → main` PR across every `ldr_main` repo in `workspace-manifest.json`
  (`unified-trading-library`/`instruments-service` excluded — separate agent owns a different provenance-gate issue on
  those two).
  - `batch-live-reconciliation-service` PR #315 (queued since `06:35:37Z`, predates the fix) — **self-healed, no manual
    action needed**: the fleet's own `uts-ci-poller[bot]` closed #315 + its head ref at `08:28:49Z`, a short-lived #316
    also got closed at `08:37:24Z`, and a fresh #317 (created `08:37:27Z`) merged clean at `08:37:51Z` with
    `validate / GCP Cloud Build` passing in 14s on a GitHub-hosted runner — the stale-PR-recycle cycle re-dispatched the
    check against the now-fixed workflow on its own before I intervened.
  - `market-data-processing-service` PR #603 (queued since `05:30:44Z`, predates the fix) — **still stuck, no
    self-heal**; applied the identical #347 recovery (verified via `gh pr view 347 --json commits`: an empty,
    tree-identical `git commit --allow-empty` pushed directly to the PR branch, not a quickmerge/code change). Pushed
    `5bbd18ed` to `promote/market-data-processing-service/5891de922ef6`. Result: `validate / GCP Cloud Build` flipped
    `pending` → `pass` (14s, GitHub-hosted runner) within seconds; the retrigger also re-ran the full QG slice (expected
    side effect of a new commit), which came back clean. `mergeStateStatus` remained `BLOCKED` only on
    `sit-gate/fleet-green` not yet having reported for the new commit (its own 15-min cadence) — not this symptom.
  - `strategy-service` PR #501 — not stuck: its `validate / GCP Cloud Build` check ran and passed at
    `2026-08-06T22:41:33Z`, inside the broken window (`f20c59f` extraction `04:18:31Z` → `5bbc277` fix `06:49:24Z`),
    landing on runner `glue-ip-172-31-3-59-1` — at least one glue runner was evidently still transiently reachable
    during part of the "zero runners" window, which is why some PRs got lucky and others hung forever. No action needed.
  - `client-reporting-api` PR #654 (created `08:10:53Z`, after the fix) and `deployment-ui` PR #480 — not affected:
    neither ever triggered `image-build-gate.yml` for their PR branch (no run exists at all — path/job-condition
    dependent, `deployment-ui` is Vercel-deployed and doesn't build a Cloud Build image); their `BLOCKED`/`DIRTY` states
    trace to unrelated causes (a real merge conflict on #654; `sit-gate/fleet-green` cadence on #480). Also noted for
    the record: `validate / GCP Cloud Build` is **not** in any of these repos' native branch-protection
    `required_status_checks` ruleset (only `Quality Gates (…) / quality-gates-v2` + `sit-gate/fleet-green` are) — it
    still matters because the fleet promote automation and the downstream deploy chain (per the alerting-service layer-4
    chase) treat it as a hard gate even where GitHub's ruleset doesn't.
  - Full sweep covered all 20 remaining `ldr_main`/other repos in the manifest with zero other open `chore(promote)` PRs
    at sweep time.

- **na-eligibility-audit 2026-08-08** (tranche `ci`): Mixed verdict on the 2 open todos. Todo 1 (fleet-wide sweep for
  other stranded self-hosted `runs-on:` in `unified-trading-ci`) is KEEP-NA-STALE (already-duplicated) — extracted
  verbatim into `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 5 (`status: draft`, `assigned_vm: planning`); not
  reclassifying this doc's `assigned_vm` — batch6 activation is the operator's call, and flipping here too risks a
  duplicate dispatch. Todo 2 (standing check for repo-visibility/runner-registration drift as a re-audit trigger) stays
  KEEP-NA, valid — a genuine design decision (what mechanism, where implemented), not extracted anywhere.

- **2026-08-08**: ran the batch6-dispatched sweep (todo 1 above, `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo
  5). Finding: none found — see the flipped checkbox above for the full grep evidence. No code fix needed in
  `unified-trading-ci`; `python-quality-gates-v2.yml`'s remaining self-hosted reference is a safe, parameterized,
  intentional canary, not a stranded hardcoded pattern.
- **context-scout 2026-08-09**: populated/refreshed context_scope (2 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:5dc1e65cce36b844]: KEEP-NA,
valid — the sole open item (todo 2, standing-check design decision) remains a genuine, un-scoped design call. No
`assigned_vm` change.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:3e4d55f31a632aea]: KEEP-NA,
valid — 1 open todo (line 125, P3 INFRA: a standing check for 'workflow moved private->public / caller
runner-registration changed' as a re-audit trigger). Re-confirmed as a genuine open design/architecture call, not a
bounded spec -- it requires designing a NEW detection heuristic from scratch (there is no existing historical-state
tracker for repo visibility or cross-repo runner registration to diff against), matching the 2 prior
na-eligibility-audit confirmations (2026-08-08, 2026-08-09). Corroborating cross-reference found this run:
plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md's own todo 10 independently raises the
SAME 'should we build a standing visibility-change alert' question and was itself independently classified 'genuine...
design/priority call, not a bounded spec...

- **context-scout 2026-08-17**: re-verified context_scope (2 entries), unchanged.

**na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid -- The doc's blocking P0 fix (image-build-validate.yml self-hosted→ubuntu-latest revert) landed and is live-verified with resolved_by SHAs in frontmatter; the P2 fleet-wide sweep todo is `[x]` DONE with 0 findings. The sole open todo (line 125, INFRA P3) asks for a brand-new standing check that flags a workflow's host-repo visibility change or a caller's runner-registration drift as a re-audit trigger for `runs-on:` choices. The most recent audit (2026-08-10) found this requires 'designing a...
- **context-scout 2026-08-20**: refreshed context_scope (3 entries).

**na-eligibility-audit 2026-08-21** (ci tranche wave 2): KEEP-NA, valid — unchanged since the 2026-08-18 verdict
(5th+ consecutive confirmation). Sole open todo (line ~126, P3) asks for a brand-new standing check flagging a
workflow's host-repo visibility change or a caller's runner-registration drift as a re-audit trigger for `runs-on:`
choices — requires designing a new detection heuristic from scratch (no existing historical-state tracker to diff
against), independently corroborated by `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`'s own
todo 10 raising the identical question. No `assigned_vm` change.
