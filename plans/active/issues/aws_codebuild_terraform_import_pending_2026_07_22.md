---
doc_type: issue
title: "terraform import of imperatively-created AWS CodeBuild projects + webhooks still owed — TF SSOT not apply-clean"
summary:
  "terraform/cloud-build/aws/main.tf's locals.services was reconciled to the live 1:1 CodeBuild project set 2026-06-19
  (deployment-service@2dddfc7), but the projects + webhooks themselves were created imperatively (out-of-band), not from
  this TF, and the module's S3 state backend is commented out — so there is no live Terraform state today and `terraform
  import` was never run. Two live-only deltas need bundling in at the same time: (a) the codebuild:StartBuild grant on
  the deployment-api project (live on unified-trading-codebuild-role's codebuild-permissions inline policy — note the
  live policy name differs from the TF's unified-trading-codebuild-policy), and (b) a comment marking deployment-ui as a
  dispatch-only entry (no standalone image; its SPA is bundled into deployment-api's image instead)."
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [terraform, aws, codebuild, infrastructure, state-backend, drift]
related: []
created: 2026-07-22
parent_epic: infrastructure_master
priority: P3
source:
  [
    "2026-06-19 AWS CodeBuild parity audit (test_fleet_image_builds_from_current_code_2026_06_17.md Phase 3) — found
    while reconciling AWS↔GCP CodeBuild trigger parity",
    "2026-07-22 migrated out of test_fleet_image_builds_from_current_code_2026_06_17.md so that plan could archive clean
    (0 open todos) — this todo remained genuinely unstarted, not folded into any other work this session",
  ]
assigned_vm:
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-22
---

# terraform import of imperatively-created AWS CodeBuild projects + webhooks (2026-07-22)

## What's owed

1. Stand up the commented-out S3 state backend for `deployment-service/terraform/cloud-build/aws` (no live TF state
   exists today for this module).
2. `terraform import` the imperatively-created AWS CodeBuild projects + their GitHub webhooks into the reconciled
   `locals.services` set (18 live projects, 1:1 with the GCP-parity build model per the 2026-06-19 audit) so the TF SSOT
   becomes apply-clean instead of drift-only-documentation.
3. Bundle in the two live-only deltas the reconciliation already found but couldn't land (blocked at the time by an
   unrelated pre-existing UAC `0.21.0→0.22.0` dep-floor drift in deployment-service's quickmerge):
   - `codebuild:StartBuild` grant on the `deployment-api` project, live on `unified-trading-codebuild-role`'s
     `codebuild-permissions` inline policy — note the **live policy name differs** from the TF's
     `unified-trading-codebuild-policy` (needs reconciling, not just importing).
   - A comment marking `deployment-ui` as a dispatch-only entry (no standalone image — its SPA is bundled into
     `deployment-api`'s image; `deployment-ui`'s own `buildspec.aws.yaml` is a dispatch that calls
     `aws codebuild start-build --project-name deployment-api --source-version main`, not a real build).

## Why this wasn't done in-session (2026-07-22)

Found while closing out `test_fleet_image_builds_from_current_code_2026_06_17.md`'s Phase 3 (already fully DONE
otherwise — AWS↔GCP trigger parity, zombie cleanup, buildspec rollout, webhook alignment all shipped 2026-06-19). This
one item requires standing up a new S3 state backend before any `terraform import` is safe to run — genuinely new infra
scoping, not a continuation of that plan's build-validation work. Migrated here so the parent plan could archive with
zero open todos per `codex/11-project-management/plan-hygiene.md`'s archive discipline, rather than being silently
dropped.
