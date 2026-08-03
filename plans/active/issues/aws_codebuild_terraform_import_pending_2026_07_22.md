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
asset_group: [ci]
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
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-30
context_scope:
  [
    deployment-service/terraform/cloud-build/aws/main.tf,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/2026_07/test_fleet_image_builds_from_current_code_2026_06_17.md,
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
  ]
---

> **🟡 STATE 2026-07-30 — backend LIVE, import DELIBERATELY NOT DONE.** The S3 state backend is stood up and
> `terraform init`-verified, but the state is **empty on purpose**: a full dry-run import measured
> `Plan: 19 to add, 22 to change, 0 to destroy`, and four of those diffs would break live CI for all 18 repos.
> Completing the import is now gated on an **operator decision table** (§ "Operator decision required"), not on more
> investigation. **Do not `terraform apply` this module.**
>
> Reclassified `assigned_vm: planning` → `NA` on 2026-07-30: the residual work is a per-attribute "is live right, or is
> the TF right?" judgment call, which is explicitly NOT AO-dispatchable
> (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"). The
> mechanical import becomes AO-eligible again once the table below is answered.

# terraform import of imperatively-created AWS CodeBuild projects + webhooks (2026-07-22)

## What's owed (as scoped 2026-07-22 — items 1 and 3 are now DONE, see the 2026-07-30 section)

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

Found while closing out `/plans/archive/2026_07/test_fleet_image_builds_from_current_code_2026_06_17.md`'s Phase 3
(already fully DONE otherwise — AWS↔GCP trigger parity, zombie cleanup, buildspec rollout, webhook alignment all shipped
2026-06-19). This one item requires standing up a new S3 state backend before any `terraform import` is safe to run —
genuinely new infra scoping, not a continuation of that plan's build-validation work. Migrated here so the parent plan
could archive with zero open todos per `/codex/11-project-management/plan-hygiene.md`'s archive discipline, rather than
being silently dropped.

## 2026-07-30 session — what was done, and why the import stopped

Ran against the operator's own AWS credentials (IAM user `admin_od`, account `427895769566`, `ap-northeast-1`).
Terraform v1.5.7, AWS provider v6.57.1.

**Done and shipped** (`deployment-service@1d25563`, ref fix `@18aa5a6`):

- **S3 state backend is live.** The commented block named `unified-trading-terraform-state-ACCOUNT_ID`, which **has
  never existed** in this account. The bucket that does exist and already holds this estate's real state is
  **`uts-terraform-state-427895769566`** (versioning `Enabled`, SSE-S3 `AES256`, full public-access block) — the
  `uts-terraform-state-{project_id}` template in `configs/bucket_config.yaml`. Pointed the backend there under the fresh
  key `cloud-build/terraform.tfstate`; creating the stubbed name would have forked the convention into a second state
  bucket. Created the missing lock table **`unified-trading-terraform-locks`** (DynamoDB, PAY_PER_REQUEST, `LockID` hash
  key) — same name `terraform/shared/aws/main.tf` already declares, so the two converge rather than fork.
  `terraform init` verified: backend type `s3`, bound.
- **Delta (a) — IAM policy name reconciled, TF side.** Live inline policy on `unified-trading-codebuild-role` is
  `codebuild-permissions`; TF said `unified-trading-codebuild-policy`. **Chose to change the TF, not rename the live
  policy** — renaming live means a put+delete of the inline policy on the role all 18 active CodeBuild projects assume,
  i.e. a window where an in-flight build loses permissions, whereas editing a string is zero-risk for identical
  reconciliation. This alone removed the destroy from the plan (20/21/**1** → 19/22/**0**).
- **Delta (b) — already satisfied, verified not re-done.** The `deployment-ui` dispatch-only comment is already in
  `main.tf` (landed `deployment-service@41d3cf8`), and `deployment-ui/buildspec.aws.yaml` was read and confirmed to be a
  pure dispatch: `aws codebuild start-build --project-name deployment-api --source-version main`, no image build. No
  change needed.
- **DO-NOT-APPLY banner** added at the top of `main.tf` recording the measured plan + the four blocking diffs, so the
  landmine is visible at the point of use.

**Deliberately NOT done: the import.** State is empty. A full dry-run import of all 23 live resources into a throwaway
_local_ state (never written to S3, so nothing was armed) measured:

```
Plan: 19 to add, 22 to change, 0 to destroy
```

Import itself is safe — it only records reality. The reason to stop is that this state would arm an `apply` that
converges live CI onto the TF's assumptions, and four of those would break it.

## Blocking diffs — why apply is unsafe

1. **`aws_iam_role_policy` body** narrows `secretsmanager:GetSecretValue` from live `secret:*` to
   `secret:github-token*`. All 16 Docker projects inject **`GH_PAT`** as a `SECRETS_MANAGER` env var, and buildspecs
   also read `github-pat` + `unified-trading/github-actions-sa-key` — **none match `github-token*`**. Applying revokes
   secret access and fails every build at start. It also drops the live `ecr:CreateRepository` grant.
2. **`aws_codebuild_webhook.services` (18) — nothing to import.** ZERO webhooks exist, CodeBuild-side or GitHub-side
   (`batch-get-projects` `webhook: None` ×18; `GET /repos/IggyIkenna/<r>/hooks` → `[]` for all 18). Builds are
   dispatched by the GitHub Actions router calling `aws codebuild start-build`. Creating these switches on a **second,
   duplicate trigger path** for every repo.
3. **MTDS + UTL compute downgrade** — the two heavy base builds run live on `BUILD_GENERAL1_LARGE` /
   `aws/codebuild/standard:7.0`; TF would force `BUILD_GENERAL1_MEDIUM` / `amazonlinux2-x86_64-standard:5.0`.
4. **`build_timeout`** — live 60 min on 16 of 18; TF would cut to 30/45.

`aws_codestarconnections_connection.github` also has no live counterpart (no connection named `unified-trading-github`
exists in any region) and nothing references it.

## Full per-attribute drift inventory (18 projects, machine-generated from the plan JSON)

| attribute                        | #proj | live                                | TF wants                              |
| -------------------------------- | ----: | ----------------------------------- | ------------------------------------- |
| `description`                    |    18 | absent (17) / custom (MTDS)         | `Build and push Docker image for <k>` |
| `tags` + provider `default_tags` |    18 | none                                | Service/Project/Environment/ManagedBy |
| `source.git_submodules_config`   |    18 | unset                               | `fetch_submodules = false`            |
| `source.report_build_status`     |    18 | `true`                              | unset                                 |
| `logs_config`                    |    17 | absent                              | `/codebuild/unified-trading` + stream |
| `build_timeout`                  |    16 | `60`                                | `30` / `45`                           |
| `source.git_clone_depth`         |    15 | `0`                                 | `1`                                   |
| env-var set / ordering           |     9 | `CLOUD_MOCK_MODE` (MTDS, UTL) etc.  | `CLOUD_BUILD=true`                    |
| `environment.image`              |     2 | `standard:7.0` (MTDS, UTL)          | `amazonlinux2-x86_64-standard:5.0`    |
| `environment.compute_type`       |     2 | `LARGE` (MTDS, UTL)                 | `MEDIUM`                              |
| `source.buildspec`               |     1 | `buildspec.yml` (instruments-svc)   | `buildspec.aws.yaml`                  |
| `environment.privileged_mode`    |     1 | `false` (unified-api-contracts)     | `true`                                |
| `source_version`                 |     1 | **unset** (unified-trading-library) | `live-defi-rollout`                   |

`aws_iam_role`, `aws_codeartifact_domain`, `aws_codeartifact_repository` drift **only** on `default_tags` — cosmetic,
safe. The CodeArtifact domain/repo otherwise match TF exactly.

## Operator decision required

Not investigation — a ruling per row. It is genuinely a mix of both directions: e.g. MTDS/UTL on LARGE looks like a
deliberate live choice TF should adopt, whereas UTL having **no `source_version` at all** and instruments-service still
on the pre-canonical `buildspec.yml` look like **live** is the side that drifted.

- **D1 — IAM policy body**: keep live's broad `secretsmanager:secret:*` (functional, over-broad) or tighten TF's scope
  to the secrets actually read (`GH_PAT`, `github-pat`, `unified-trading/github-actions-sa-key`)? Security-relevant;
  recommend the explicit-allow-list third option rather than either extreme.
- **D2 — webhooks**: delete the 18 `aws_codebuild_webhook` resources from TF (codifying GHA-router dispatch as the only
  trigger path) or actually create them?
- **D3 — compute/timeout/clone-depth/logs/tags**: adopt live into TF, or apply TF onto live?
- **D4 — the two live-side drifts**: fix UTL's missing `source_version` and instruments-service's `buildspec.yml` on the
  live projects?

## Todos

- [x] [INFRA] P3. **Stand up the S3 state backend** — existing bucket `uts-terraform-state-427895769566` (not the
      never-existent stubbed name) + created DynamoDB lock table `unified-trading-terraform-locks`; backend block
      uncommented with real values, `terraform init` verified bound (backend type `s3`). — deployment-service@1d25563
- [x] [INFRA] P3. **Delta (a) — reconcile the `codebuild:StartBuild` / policy-name mismatch** — TF renamed to the live
      `codebuild-permissions` (chose code-side; renaming live IAM would risk in-flight builds). Removed the destroy:
      plan went 20/21/1 → 19/22/0. — deployment-service@1d25563
- [x] [INFRA] P3. **Delta (b) — `deployment-ui` dispatch-only marker** — verified already present in `main.tf` (landed
      @41d3cf8) and confirmed against `deployment-ui/buildspec.aws.yaml`, which only calls
      `aws codebuild start-build --project-name deployment-api`. No change needed.
- [x] [INFRA] P3. **Measure the true import drift** — all 23 live resources imported into a throwaway local state (never
      written to S3): `Plan: 19 to add, 22 to change, 0 to destroy`. Inventory above.
- [ ] [OPERATOR] P3. **Rule D1-D4 above** — one ruling per row, so the residual becomes mechanical. Blocks every
      remaining todo here.
- [ ] [INFRA] P3. **Reconcile `main.tf` to the D1-D4 rulings**, then `terraform import` all 23 resources into the live
      S3 state and prove `terraform plan` is a genuine no-op. Do NOT import before D1-D4 — an imported state plus these
      diffs is an armed destructive apply.
- [ ] [INFRA] P3. **Pin the AWS provider deliberately.** This module's `>= 5.0.0` resolves to v6.57.1 while every
      sibling module pins `~> 5.82` (v5.100.0). v6 also deprecates `data.aws_region.name` (used at `main.tf`
      `locals.region`). Decide v5-align vs deliberate v6 adoption, then commit a multi-platform `.terraform.lock.hcl`
      (the repo commits 10 others; this session's local lock was deleted rather than committing darwin-only hashes that
      would break a linux `init`).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-31** (tranche `ci`, autonomous): **KEEP-NA, valid.** The 2026-07-30 banner earlier in
this doc already documents a dated, cited operator reclassification (`assigned_vm: planning → NA`, citing
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility") — KEEP-NA on
that citation alone. All 3 open todos are consistent with the gate: the `[OPERATOR]` ruling todo blocks the other two
mechanically (`terraform import` explicitly must not run before D1-D4; the provider-pin todo is its own v5-vs-v6
judgment call). Independently corroborated by the sibling `/ag-closeout-audit ci` skill's same-day draft
`ci_satellite_ao_dispatch_batch4_2026_07_31.md` (row D4-6): deferred on the identical D1-D4 rulings table, also noting
batch1's earlier "blocked on AWS credits" framing is now stale (the S3 backend is up; the real blocker is the rulings
table). No reclassification, no stale items to close.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (3 entries).
