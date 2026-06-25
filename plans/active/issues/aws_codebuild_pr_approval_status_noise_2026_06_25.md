---
title: AWS CodeBuild posts a "failure" commit-status on automated promote PRs (PR-approval gate) — cosmetic but noisy
created: 2026-06-25
author: ikennaigboaka
source:
  - dashboard promotion stall reasons (2026-06-24)
  - UTL #475 staging→main promote PR (head 53852d11) AWS CodeBuild = failure
  - deployment-service/terraform/modules/cloud-build/aws/main.tf (webhook NOTE, lines 263–275)
locked_by: live-defi-rollout
---

## What I found

The commit-status `AWS CodeBuild ap-northeast-1 (<repo>)` shows **`failure`** on automated
`staging→main` / `LDR→staging` promote PRs (observed on UTL #475, head `53852d11`). It is **not a
broken build** — the status description is verbatim:

> `Build not triggered: Pull request approval required for starting a build`

The CodeBuild GitHub webhook fires on PR events
(`github_webhook_events` default = `PUSH, PULL_REQUEST_CREATED, PULL_REQUEST_UPDATED, PULL_REQUEST_REOPENED`),
but CodeBuild's "require approval to build a pull request" security setting refuses to auto-build an
**unapproved, bot-created** promote PR, and posts a `failure` commit-status for the skipped build.

**Actual builds are healthy** — the LDR-push CodeBuild for the same repo is `success`
(UTL `live-defi-rollout` head `044138192` = AWS CodeBuild success), and on most repos' `main` HEAD
AWS CodeBuild = `success` (strategy / execution / instruments / deployment / features all green).

## Why it matters

- **Non-blocking today**: the only branch-protection required check is `quality-gates-v2`; the AWS
  CodeBuild status is **not required**, so it did not block any merge (UTL #475 / MDPS #380 merged fine).
- **But it is noise**: it renders every automated promote PR as a red `failure` and surfaces as a
  "staging→main not promoting" / red-status signal on the promotion dashboard, costing triage time and
  masking genuine failures.

## Why it is not fixable from a worker right now

1. **No IAM perms**: the `ikenna-worker` IAM user (`arn:aws:iam::427895769566:user/ikenna-worker`) has
   **no `codebuild:*`** — `ListProjects` / `BatchGetProjects` / `ListBuildsForProject` / (by extension)
   `UpdateWebhook` all `AccessDenied`. The webhook/project cannot be inspected or changed via the API.
2. **Terraform is drifted from live**: the module itself warns
   (`deployment-service/terraform/modules/cloud-build/aws/main.tf` §"GitHub Webhook", NOTE lines 267–268):
   > "the LIVE webhooks are currently imperatively managed + DRIFTED from this module — do NOT
   > `terraform apply` blindly (would revert live config). Reconcile TF↔live first (BUILD-FIX P3)."
   So a blind `terraform apply` is unsafe.

## Recommended decision (operator / AWS-perms holder)

Pick one (both are AWS-side, need CodeBuild write access + a TF↔live reconciliation first):

1. **Drop PR events from the webhook** — set `github_webhook_events = "PUSH"` (build on branch push only,
   not on PR open/update). Cleanest: promote PRs never trigger a CodeBuild build → no status to fail.
2. **Set the Gap-5 opt-in filter** — set `github_commit_message_filter = "Build-LDR: true"` (the variable
   already exists for exactly this: *"removes the CodeBuild status from LDR→staging drain PRs"*). Non-opted
   pushes/PRs do not build. Note this also gates LDR image builds to the `quickmerge --build` trailer.

Sequence either fix as: **reconcile TF↔live drift → apply via terraform** (per the BUILD-FIX P3 NOTE), or
apply imperatively with `aws codebuild update-webhook` once the live config is captured back into TF.

Until then this stays **BLOCKED-OPERATOR-DECISION** (needs the AWS-side change; nothing a worker can do).

## Prior tracking (archived — this revives it)

- `plans/archive/issues/ci_pipeline_self_healing_gaps_2026_06_11.md` (Gap 5 — the `Build-LDR: true` filter)
- `plans/archive/issues/dashboard_promotion_drain_visibility_2026_06_11.md` (promotion-status surface)
