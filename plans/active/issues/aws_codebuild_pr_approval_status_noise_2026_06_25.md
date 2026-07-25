---
doc_type: issue
title: AWS CodeBuild posts a "failure" commit-status on automated promote PRs (PR-approval gate) — cosmetic but noisy
summary:
  "The commit-status `AWS CodeBuild ap-northeast-1 (<repo>)` shows **`failure`** on automated `staging→main` /
  `LDR→staging` promote PRs (observed on UTL #475, head `53852d11`). It is **not a broken build** — CodeBuild's own
  status description says the build was never triggered because it requires PR approval first; cosmetic noise, not a
  real CI failure."
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, infrastructure, observability, escalation]
related: []
created: 2026-06-25
parent_epic: infrastructure_master
priority: P2
source:
  [
    dashboard promotion stall reasons (2026-06-24),
    UTL,
    "deployment-service/terraform/modules/cloud-build/aws/main.tf (webhook NOTE, lines 263–275)",
  ]
assigned_vm:
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

> **[2026-07-12 correction, findings 347 (P1) + 86 (P2, near-duplicate), §A2 B-queue**
> (`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`)**]**: this doc's "`staging→main` /
> `LDR→staging` promote PRs" framing below (was written 2026-06-25, last updated 2026-06-27) describes a staging-routed
> pipeline shape that is now stale. Per `plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` (operator-reaffirmed
> 2026-06-30, the current pipeline SSOT): **staging is DORMANT** — the MVP default is LDR→main DIRECT (SIT-green +
> quality-gates-v2 + quickmerge-provenance only), not `LDR→staging`/`staging→main`. Separately, hard evidence further
> moots the noise this issue describes: **all native GitHub webhooks on the 18 CodeBuild projects in AWS account
> `427895769566`/ap-northeast-1 were deleted 2026-07-03** (verified commits `f22fde880` "disable AWS image builds per
> operator 2026-07-03" + `d93388305` "AWS image builds behind `AWS_BUILDS_ENABLED` switch... +
> `toggle-aws-image-builds.sh`", both in this repo's history; no commits since have touched
> `scripts/cicd/toggle-aws-image-builds.sh` or the AWS build workflows, so the switch remains OFF as of 2026-07-12) —
> with the webhooks gone, CodeBuild no longer fires on PR events at all, so the `failure` commit-status this issue
> tracks should no longer be posted on new promote PRs regardless of pipeline shape. Status left `open` here
> (closing/resolving is an operator-scope call, not a mechanical doc-sync); this annotation only corrects the stale
> pipeline-shape framing + adds the newer evidence for whoever re-triages it next.

## What I found

The commit-status `AWS CodeBuild ap-northeast-1 (<repo>)` shows **`failure`** on automated `staging→main` /
`LDR→staging` promote PRs (observed on UTL #475, head `53852d11`). It is **not a broken build** — the status description
is verbatim:

> `Build not triggered: Pull request approval required for starting a build`

The CodeBuild GitHub webhook fires on PR events (`github_webhook_events` default =
`PUSH, PULL_REQUEST_CREATED, PULL_REQUEST_UPDATED, PULL_REQUEST_REOPENED`), but CodeBuild's "require approval to build a
pull request" security setting refuses to auto-build an **unapproved, bot-created** promote PR, and posts a `failure`
commit-status for the skipped build.

**Actual builds are healthy** — the LDR-push CodeBuild for the same repo is `success` (UTL `live-defi-rollout` head
`044138192` = AWS CodeBuild success), and on most repos' `main` HEAD AWS CodeBuild = `success` (strategy / execution /
instruments / deployment / features all green).

## Why it matters

- **Non-blocking today**: the only branch-protection required check is `quality-gates-v2`; the AWS CodeBuild status is
  **not required**, so it did not block any merge (UTL #475 / MDPS #380 merged fine).
- **But it is noise**: it renders every automated promote PR as a red `failure` and surfaces as a "staging→main not
  promoting" / red-status signal on the promotion dashboard, costing triage time and masking genuine failures.

## Why it is not fixable from a worker right now

1. **No IAM perms**: the `ikenna-worker` IAM user (`arn:aws:iam::427895769566:user/ikenna-worker`) has **no
   `codebuild:*`** — `ListProjects` / `BatchGetProjects` / `ListBuildsForProject` / (by extension) `UpdateWebhook` all
   `AccessDenied`. The webhook/project cannot be inspected or changed via the API.
2. **Terraform is drifted from live**: the module itself warns
   (`deployment-service/terraform/modules/cloud-build/aws/main.tf` §"GitHub Webhook", NOTE lines 267–268):
   > "the LIVE webhooks are currently imperatively managed + DRIFTED from this module — do NOT `terraform apply` blindly
   > (would revert live config). Reconcile TF↔live first (BUILD-FIX P3)." So a blind `terraform apply` is unsafe.

## Recommended decision (operator / AWS-perms holder)

Pick one (both are AWS-side, need CodeBuild write access + a TF↔live reconciliation first):

1. **Drop PR events from the webhook** — set `github_webhook_events = "PUSH"` (build on branch push only, not on PR
   open/update). Cleanest: promote PRs never trigger a CodeBuild build → no status to fail.
2. **Set the Gap-5 opt-in filter** — set `github_commit_message_filter = "Build-LDR: true"` (the variable already exists
   for exactly this: _"removes the CodeBuild status from LDR→staging drain PRs"_). Non-opted pushes/PRs do not build.
   Note this also gates LDR image builds to the `quickmerge --build` trailer.

Sequence either fix as: **reconcile TF↔live drift → apply via terraform** (per the BUILD-FIX P3 NOTE), or apply
imperatively with `aws codebuild update-webhook` once the live config is captured back into TF.

Until then this stays **BLOCKED-OPERATOR-DECISION** (needs the AWS-side change; nothing a worker can do).

## Prior tracking (archived — this revives it)

- `plans/archive/issues/ci_pipeline_self_healing_gaps_2026_06_11.md` (Gap 5 — the `Build-LDR: true` filter)
- `plans/archive/issues/dashboard_promotion_drain_visibility_2026_06_11.md` (promotion-status surface)
