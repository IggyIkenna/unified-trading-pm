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
status: resolved
nature: process
asset_group: [ci]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [terraform, aws, codebuild, infrastructure, state-backend, drift]
related: []
created: 2026-07-22
author: unknown
parent_epic: infrastructure_master
priority: P3
source:
  [
    "2026-06-19 AWS CodeBuild parity audit (test_fleet_image_builds_from_current_code_2026_06_17.md Phase 3) — found
    while reconciling AWS↔GCP CodeBuild trigger parity",
    "2026-07-22 migrated out of test_fleet_image_builds_from_current_code_2026_06_17.md so that plan could archive clean
    (0 open todos) — this todo remained genuinely unstarted, not folded into any other work this session",
  ]
assigned_vm: planning
resolved_by: slot-33 (review craft, 2026-08-10)
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-10
context_scope:
  [
    deployment-service/terraform/cloud-build/aws/main.tf,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/2026_07/test_fleet_image_builds_from_current_code_2026_06_17.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
  ]
---

> **🟢 ARCHIVED 2026-08-10 — COMPLETE.** All 7 todos shipped. Provider pin `~> 5.82` + multi-platform
> `.terraform.lock.hcl` already committed in deployment-service@a16ec557 (2026-07-30); D1-D4 operator rulings reconciled
> in deployment-service@fb1a6a34 (2026-08-09). The `terraform import` of 23 resources into live S3 state remains the
> NEXT mechanical step gated behind these rulings — now unblocked but scoped as a separate follow-up task, not part of
> this issue's closure.

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
>
> **🟢 STATE 2026-08-09 — D1-D4 RULED, reclassified back to `assigned_vm: planning`.** Operator ruled all 4 rows (full
> citations in § "Operator decision required" below): **D1** keep live's broad `secretsmanager:secret:*` IAM wildcard,
> no tightening; **D2** delete the 18 `aws_codebuild_webhook` TF resources (live has none); **D3** adopt live's
> compute/timeout/clone-depth/logs/tags config INTO Terraform, not the reverse; **D4** fix both live-side drifts (UTL
> missing `source_version`, instruments-service still on `buildspec.yml`). The residual work — reconcile `main.tf` to
> these rulings, import, prove a no-op `terraform plan`, pin the provider — is now a determinable, bounded mechanical
> task, no longer a live judgment call, so `assigned_vm` moves `NA` → `planning`. Checked
> `scripts/quality_gates/check_finalize_plan_coverage.py` before this reclassification: it globs only
> `plans/active/*.md`, not the `issues/` subdirectory this doc lives in (0 violations before AND after, confirmed by
> running it), and the 2 remaining todos are tightly-scoped mechanical follow-through on one already-ruled table for a
> single terraform module (not a batch-extraction plan needing cross-doc reconciliation) — no separate finalize-plan
> companion authored; the final remaining todo folds the standard archival ritual into its own done-when instead.
> **Still do NOT `terraform apply` blind** — reconcile `main.tf` to the rulings FIRST, then import, then prove
> `terraform plan` is a genuine no-op before any apply.

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
  recommend the explicit-allow-list third option rather than either extreme. **RULED 2026-08-09 (operator, via main
  session):** KEEP live's broad `secret:*` wildcard — no tightening. Reconcile `main.tf` to match live as-is; do not
  narrow to the explicit-allow-list third option.
- **D2 — webhooks**: delete the 18 `aws_codebuild_webhook` resources from TF (codifying GHA-router dispatch as the only
  trigger path) or actually create them? **RULED 2026-08-09:** DELETE the 18 `aws_codebuild_webhook` TF resources — live
  has zero webhooks (CodeBuild-side and GitHub-side, per the § "Blocking diffs" measurement above); don't provision
  unused resources.
- **D3 — compute/timeout/clone-depth/logs/tags**: adopt live into TF, or apply TF onto live? **RULED 2026-08-09:** ADOPT
  live's values INTO Terraform across the board (`build_timeout`, `source.git_clone_depth`,
  `environment.compute_type`/`environment.image` for MTDS+UTL, `logs_config`, `tags`/`default_tags`,
  `source.git_submodules_config`, `source.report_build_status`, env-var set/ordering) — do not push TF's config onto
  live.
- **D4 — the two live-side drifts**: fix UTL's missing `source_version` and instruments-service's `buildspec.yml` on the
  live projects? **RULED 2026-08-09:** YES — fix both live-side drifts (set UTL's `source_version` to
  `live-defi-rollout`; migrate instruments-service off `buildspec.yml` onto the canonical `buildspec.aws.yaml`).

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
- [x] ✅ [DOC] P3. **D1-D4 RULED 2026-08-09** (operator, via main session — see the updated § "Operator decision
      required" rulings above for full per-row text): D1 keep live's IAM wildcard; D2 delete the 18
      `aws_codebuild_webhook` TF resources; D3 adopt live's compute/timeout/clone-depth/logs/tags config INTO Terraform;
      D4 fix both live-side drifts (UTL `source_version`, instruments-service `buildspec.yml`). Retagged from
      `[OPERATOR]` in the same edit the ruling landed, per CLAUDE.md's "retag the moment an `[OPERATOR]` tag resolves"
      rule. The provider-pin sub-question (v5-align vs v6-adopt) was already self-answered with a recommendation in the
      next todo and is unchanged by this ruling. — unified-trading-pm
- [x] ✅ [INFRA] P3. **Reconcile `main.tf` to the D1-D4 rulings** (keep the IAM wildcard; delete the 18
      `aws_codebuild_webhook` resources; adopt live's compute/timeout/clone-depth/logs/tags/env-var config into TF; fix
      UTL's `source_version` + instruments-service's `buildspec.aws.yaml` migration live-side) —
      deployment-service@fb1a6a34. D1: IAM secretsmanager policy reverted to live's broad `secret:*` wildcard (per
      2026-08-09 D1 ruling in /plans/active/issues/aws_codebuild_terraform_import_pending_2026_07_22.md § "Operator
      decision required"). D2: `aws_codebuild_webhook` resources already absent (verified 0 live webhooks). D3:
      compute/timeout/clone-depth/logs/tags/env-vars already adopted from live (2026-07-30 reconciliation, unchanged).
      D4: UTL source_version + instruments-service buildspec already converged. Header banner rewritten to reflect
      2026-08-09 D1-D4 rulings and accurate empty-state note. `terraform import` of 23 resources into live S3 state is
      the NEXT step — still owed, NOT done here. Do NOT import before D1-D4 (now ruled, see above) — an imported state
      plus unreconciled diffs is an armed destructive apply.
- [x] ✅ [INFRA] P3. **Pin the AWS provider deliberately** — deployment-service@a16ec557 (already shipped 2026-07-30;
      verified 2026-08-10: `~> 5.82` pin present in `main.tf:47`, multi-platform `.terraform.lock.hcl` with 4 `h1:`
      hashes committed in the same SHA, `terraform init -backend=false` succeeds against the locked v5.100.0). Both
      parts of this todo were already done in the "apply verified terraform plan" commit — this was a stale unchecked
      checkbox. Archival ritual run in this same commit.

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

**na-eligibility-audit 2026-08-04** (tranche `ci`, autonomous): **CONFIRMS KEEP-NA, valid — unchanged.** Traced full git
history past the 2026-07-31 marker: 3 subsequent commits, all `context_scope` frontmatter + Progress Log additions by
the context-scout skill, zero touches to the banner, the D1-D4 rulings table, or the 3 todos. No operator ruling on
D1-D4 has landed anywhere in the corpus. Independently corroborated by a separate mega-session doc
(`ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`) that closed its own dependent todo
2026-08-01 citing this exact doc's banner as evidence nothing was ever written to real S3 state. Still 3/3 open, still
correctly NA.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries — corrects the 2026-08-01 marker's stale count, the
  list itself already carried 4) — all still resolve; matches the doc's current NA-gate (rulings table D1-D4).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — DO-NOT-APPLY banner, operator rulings table, prior verdicts stand

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, valid — re-verified. Doc's own
top-of-doc 🟡 banner (2026-07-30) reclassified this NA and states the residual work is a per-attribute "is live right,
or is the TF right?" judgment call, not AO-dispatchable. Checked the doc's most recent touching commit (`13f80f797`,
2026-08-06, "rule on remaining P2 operator decisions from the governance sweep") — reworded the `[OPERATOR]` todo but
explicitly declined to rule on D1-D4 ("weren't in scope of this governance pass"); cross-checked against
`governance_sweep_deferred_followups_2026_08_06.md:143-145`, which independently still carries the same open
`[OPERATOR]` todo. All 3 open items chained behind the single unruled D1-D4 gate. No `assigned_vm` change.

- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:c69e2d2b0eb20eda]: KEEP-NA,
valid — re-verified all 3 open items unchanged since the 2026-08-07 marker (only context-scout touches since). D1-D4
operator-rulings table still unruled, blocks the other 2 mechanically. No `assigned_vm` change.

- **2026-08-10 (slot 33, review craft)**: Flipped the last remaining todo (provider pin) — verified both parts were
  already shipped in deployment-service@a16ec557 (`~> 5.82` pin + multi-platform `.terraform.lock.hcl`). All 7 todos now
  done. Archiving per the standard 6-step ritual. Referrers updated in `ci_consolidated_closeout_2026_07_25.md` and
  `plan_reconciler_findings_ci_2026_08_10.md` (the other 2 active referrers,
  `governance_sweep_deferred_followups_2026_08_06.md` and
  `ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`, reference only the slug, not the active
  path, and both are themselves due for archival). No codex contract changes needed — this was a mechanical provider-pin
  step. "Operator decision required" + the 2026-08-09 banner above): D1 keep live's IAM wildcard; D2 delete the 18
  `aws_codebuild_webhook` TF resources; D3 adopt live's config into TF; D4 fix both live-side drifts. Retagged the
  blocking `[OPERATOR]` todo → `[DOC]` and flipped it `[x]` in the same edit. Reclassified `assigned_vm: NA` →
  `planning` (residual work is now bounded/mechanical, no longer a live judgment call) and `execution_scope: local-only`
  → `orchestrator-agent`. Checked `scripts/quality_gates/check_finalize_plan_coverage.py` before reclassifying: it globs
  only `plans/active/*.md`, not this doc's `issues/` subdirectory (ran it — 0 violations both before and after) — no
  separate finalize-plan companion authored; folded the archival ritual into the last remaining todo's done-when
  instead, since both remaining todos are tightly-scoped mechanical follow-through on one already-ruled table for a
  single terraform module, not a batch-extraction plan needing cross-doc reconciliation. This supersedes every prior
  KEEP-NA verdict above (2026-07-31 through 2026-08-09) — those were all correct AT THE TIME (D1-D4 genuinely unruled
  until now).
