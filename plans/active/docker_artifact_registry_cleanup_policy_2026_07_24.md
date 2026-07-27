---
doc_type: plan
title: Artifact Registry / ECR image retention — audit deployed images first, then apply a safe cleanup policy
summary:
  Executable, human-driven fix for the unbounded Docker-image retention issue (4.01 TB, ~$400/mo, no cleanup policy on
  any of 75 GCP AR repos + 20 AWS ECR repos). Audit-first — enumerate which image digests are ACTUALLY deployed in prod
  (deployment-service stable_versions.yaml as the pin oracle, corroborated by live runtime + credential-probe), then
  draft an Artifact Registry cleanup policy that explicitly KEEPS every deployed digest on top of a keep-5-recent floor
  plus delete-older-than-3d, validate via cleanupPolicyDryRun with a zero-intersection check against the deployed set,
  get operator sign-off, flip live, and re-audit savings. Also covers the second artifact class — the GCS code-tarball
  bucket (732 accumulating @sha copies, ~2.4 GB) — fixed via a GCS lifecycle rule, not an AR policy. Local-only —
  operator reviews before any deletion; deletes are human-gated (no soft-delete on AR, deletion is permanent).
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    unified-trading-library,
    deployment-service,
    deployment-api,
    instruments-service,
    strategy-service,
    execution-service,
    ml-service,
    features-service,
    market-data-processing-service,
  ]
scope: [engineer]
tags: [artifact-registry, ecr, docker-images, storage-cost, cleanup-policy, retention, cicd]
related: []
created: 2026-07-24
last_updated: 2026-07-24
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  operator-directed 2026-07-24 — a docker/artifact storage cost audit surfaced 4.01 TB of unbounded-retention images
  with no cleanup policy anywhere; this plan is the executable, safety-gated fix (diagnosis folded into the Diagnosis
  section below)
---

# Artifact Registry / ECR image retention — audit-first, safe cleanup policy

> **Self-contained** — the diagnosis (§ Diagnosis) and the audit-first, safety-gated todo DAG live here; this plan
> supersedes the original issue doc. **Local-only — nothing here is dispatched to the fleet; the operator runs the audit
> and gates every deletion.** No AR soft-delete/undelete exists — deletion is permanent, so the dry-run +
> deployed-digest cross-check is mandatory before any live flip.

## Diagnosis (audit numbers — pulled live via gcloud/aws 2026-07-24, not estimated)

The operator asked for the real storage cost of accumulated Docker images ("using around four, five terabytes"). A
direct pull from `gcloud artifacts repositories list` (all locations, both accessible GCP projects) +
`aws ecr describe-images` (all 20 repos, account `427895769566`) confirmed it, and surfaced the structural cause: **no
repository in either cloud has a cleanup policy configured.**

- **Total: 4.01 TB, ~7,300 images, 75 GCP AR repos + 20 AWS ECR repos** — ~**$400.55/mo (~$4,807/yr)** at
  $0.10/GB-month, storage-only.
- **`unified-trading-system`** (GCP AR, `asia-northeast1`, `central-element-323112`) — the largest, **1.97 TB, 3,477
  images, ~$196.83/mo**; a _shared_ repo, 20 services push as sub-path packages. `describe … cleanupPolicies` returns
  **`null`** (no policy).
  - **`market-tick-data-service`** = 1,958 of those 3,477 (56%), pushing **~17.5 images/day**, almost all git-sha CI
    builds (only 87 semver releases; the semver-agent is currently non-functional).
- **`unified-trading-library`** — **928 GB, 1,129 images, ~$92.76/mo**, same CI-per-commit pattern.
- **AWS ECR** (account `427895769566`, `ap-northeast-1`, 20 repos) — **523 GB logical, 393 images, ~$52/mo**; the figure
  sums each image's `imageSizeInBytes` (double-counts shared layers), so actual billed is likely lower — not yet
  reconciled against Cost Explorer.
- **Legacy GCR bucket** `gs://artifacts.central-element-323112.appspot.com` — 8.9 GiB, ~$0.22/mo, leftover from the 2025
  GCR→AR migration.
- **The retained images are already gate-passed** (confirmed by reading the pipeline, not assumed): in
  `market-tick-data-service/cloudbuild.yaml` the `push` step's
  `waitFor: ["quality-gates", "image-import-smoke", "sha-tag-guard"]` aborts before push if a gate fails, and that Cloud
  Build run only fires after GitHub Actions' `quality-gates-v2` passed. So this is a **retention** problem, not a
  "storing broken builds" problem. (Historical aside, not in scope: a 2026-07-20 incident where the in-image
  `quality-gates` step passed _vacuously_ let 4 dependency-skewed images through before `image-import-smoke` hardened it
  — the gate is solid today.)
- **No soft-delete / versioning / undelete on GCP AR** (confirmed vs GCP docs 2026-07-24) — deletion is immediate and
  permanent; cleanup policies run as a ~daily background job. **Any policy MUST be validated via
  `cleanupPolicyDryRun: true` before going live** — there is no recovery path if the scoping is wrong.
- **Expected outcome** — time-based deletion scales with each service's push rate: MTDS (~17.5/day) retains ~52 images
  (a real 3-day rollback window, not the ~7 hours a flat keep-5 gives it) while quiet services stay on the 5-image
  floor; extrapolated `unified-trading-system` ≈ **~160 images, down from 3,477 (~95% cut)**.

## Why audit-first (the correction that makes this safe)

The naive "keep-5-recent + delete-older-than-3d" policy has a real hole. **The deployed image is not "the latest push"**
— it is whatever deployment-service pins in `stable_versions.yaml` (e.g. market-tick-data-service deploys
"via-dispatch": its `cloudbuild.yaml` only _notifies_ deployment-service, it does not deploy). That pin can lag many
builds behind HEAD. For MTDS at ~17.5 builds/day, keep-5 ≈ the last ~7 hours; a service that has been stable on an older
pin for >3 days falls through **both** rules and its running image gets deleted.

What actually happens on deletion (grounds the design):

- **An already-running process keeps running** — its image layers are already on the node's local disk; deleting from
  the registry does not reach a live node. Nothing dies at the moment of deletion.
- **The next _pull_ is the failure** — a restart/reboot, autoscale-up, crash-reschedule, node replacement, or a fresh
  deploy/rollback re-pulls from the registry and fails (`ImagePullBackOff` / a Cloud Run revision that cannot launch).
  Silent until the thing scales or restarts.
- **Blast radius is narrow** — per
  [/codex/05-infrastructure/vm-tarball-deployment.md](/codex/05-infrastructure/vm-tarball-deployment.md), the backfill /
  migration / forward-poll / smoke fleet (most MTDS ingestion) runs from **tarballs, not AR images**, so image deletion
  is irrelevant to it. Only **long-lived Docker-image services** (strategy, execution, auto-scaling production batch)
  are exposed, and only on a re-pull event.
- **And those two are currently idle** — operator-stated + spot-checked read-only on 2026-07-24: `strategy-service` and
  `execution-service` have **no GCE instance and no Cloud Run service** on GCP (the only RUNNING GCE VMs are two
  `mtds-dex-swaps-backfill` tarball VMs; all else TERMINATED). Nothing pulls their GCP AR images right now → those
  sub-paths are low-risk to prune. **Not checked: AWS ECS/Fargate** — if either runs there it pulls from ECR (Phase E),
  not GCP AR; Phase A still confirms the deployed set before any flip.

**Fix:** the audit produces the set of actually-deployed digests, and the policy adds an explicit `Keep` for each one.
Then the policy is correct-by-construction regardless of pin staleness, and keep-5 + 3-day are just the background
floor.

## The second artifact class — code tarballs (GCS, not AR)

The AR policy above targets Docker images only. The tarball fleet keeps its own artifacts in
`gs://deployment-scripts-central-element-323112/code/`, and they accumulate the same way (verified read-only
2026-07-24): a current-pointer `<repo>-code.tar.gz` (overwritten each refresh) **plus 732 per-commit
`<repo>-code@<sha>.tar.gz` copies** + manifests that are never cleaned up. Bucket **versioning is off**, so this is
explicit per-SHA key accumulation, not GCS object-version buildup.

- **Scale is tiny** — the whole `code/` prefix is **~~2.39 GB (~~$0.24/mo)** vs 4 TB of images. Worth fixing for hygiene
  - to stop the growth, not for cost.
- **Different mechanism** — it is a GCS bucket, so the fix is a **GCS lifecycle rule** (age-based delete of old `@sha`
  copies), governed by
  [/codex/02-data/gcs-and-manifest-delete-safety-protocol.md](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md)
  (human-gated prod delete), NOT an AR cleanup policy.
- **What must survive** — the current-pointer `<repo>-code.tar.gz` per repo (that is what a VM downloads by
  `VM_SERVICE`) and any `@sha` tarball a live VM / launcher / deployment-registry JSON still references. Same
  deployed-set-keep principle as the images. (Related, out of scope here: the same bucket's `vm-logs/` prefix also
  accumulates — flag for a follow-up sweep, do not fold in.)

## Policy shape (target)

Three rules per Artifact Registry Docker repo, `Keep` taking precedence over `Delete`:

```yaml
# 1. Protect every image that is actually deployed (from Phase A audit) — the safety spine
- name: keep-deployed-digests
  action: { type: Keep }
  condition:
    versionNamePrefixes: [<each deployed digest/tag from stable_versions.yaml + live runtime>]

# 2. Background floor — protects quiet/never-recently-built services
- name: keep-5-recent
  action: { type: Keep }
  mostRecentVersions:
    keepCount: 5

# 3. The pruner
- name: delete-older-than-3d
  action: { type: Delete }
  condition:
    tagState: any
    olderThan: "3d"
```

**Verified (Phase B, todo 4 — RESOLVED 2026-07-24):** `mostRecentVersions.keepCount` applies **per package, not per
repo**. Per the GCP docs
([Configure cleanup policies](https://docs.cloud.google.com/artifact-registry/docs/repositories/cleanup-policy)): "To
apply the keep policy to all packages in your repository, omit the `packageNamePrefixes` condition. The specified number
of recent versions of each package in your repository are kept." — i.e. `keepCount: 5` with no `packageNamePrefixes`
keeps 5 versions **of each package**, not 5 total across the repo. **Decision: repo-wide `keep-5-recent` (todo 5's
policy shape, `packageNamePrefixes` omitted) is correct as drafted — no per-package expansion needed.** 3 rules total
for `unified-trading-system` (`keep-deployed-digests` + `keep-5-recent` + `delete-older-than-3d`), not 21. Operator
confirmed intent 2026-07-24: never drop the latest/deployed image for any package, but trimming version history past 5
per package is fine to keep total volume reasonable — this is exactly what the verified per-package semantics deliver.
`versionNamePrefixes`/`packageNamePrefixes` are still **prefix** matches — a footgun if any two package names share a
prefix; use exact names and confirm in the dry-run (todo 6).

## Operator decisions (2026-07-24 — FINAL)

Ratified by the operator; **settled, not open for re-litigation** by the next shift:

- **Retention knobs = keep-5 floor + 3-day delete window.** FINAL. The Phase-C dry-run still shows the concrete impact,
  but these values are decided — do not propose alternatives.
- **No separate semver protection.** FINAL. git-sha images are treated as sufficient; the `keep-deployed-digests` +
  `keep-5-recent` rules are the safety net, not a semver carve-out — this holds even if the semver-agent is later
  restored. Do not add a semver-only Keep rule.

The one genuinely open verification is AR per-package semantics (Phase B, todo 4) — a checkable fact, not a decision.

## Plan

Operator-driven, run top-to-bottom (audit → verify → draft → dry-run → gate → apply → verify → extend). Deletes are
human-only.

### Phase A — Audit which images are actually deployed (read-only)

- [ ] 1. [DATA] P1. Enumerate the currently-pinned image digest/tag per service from deployment-service
      `stable_versions.yaml` (the pin oracle). Done-when: a committed table of service → pinned digest → push-age for
      every service, saved beside this plan.
- [ ] 2. [DATA] P1. Corroborate the pinned set against live runtime — Cloud Run revisions / any GKE workloads /
      long-lived Docker VMs — plus the `credential-probe.sh` "all prod VMs on pinned SHA" check; flag any digest
      running-but-not-in `stable_versions.yaml`. Done-when: every drift between pinned and actually-running is listed,
      or "no drift" is stated with the evidence.
- [ ] 3. [DATA] P1. Label each of the top repos (MTDS, unified-trading-library, and the next 3 by size) as
      Docker-runtime vs tarball-runtime, so we know which are image-deletion-safe by construction. Done-when: each top
      repo tagged Docker-runtime or tarball-only with a one-line basis.

### Phase B — Verify AR semantics + draft the policy

- [x] 4. [INFRA] P2. Verify against current GCP docs whether `mostRecentVersions.keepCount` applies per-package or
      per-repo — this decides 2 rules vs 20 keep rules for `unified-trading-system`. Done-when: the cited GCP doc
      statement + the recorded decision (repo-wide keep-5 vs per-package rules). ✅ 2026-07-24 — per-package, confirmed
      via [GCP docs](https://docs.cloud.google.com/artifact-registry/docs/repositories/cleanup-policy); decision:
      repo-wide `keep-5-recent` with `packageNamePrefixes` omitted (see § Policy shape). Operator confirmed intent
      matches: never drop latest/deployed per package, trim history past 5 per package.
- [ ] 5. [INFRA] P2. Draft the `unified-trading-system` cleanup policy JSON/YAML: `keep-deployed-digests` (from Phase
      A) + `keep-5-recent` floor + `delete-older-than-3d` (tagState any). Done-when: the policy file is committed beside
      this plan.

### Phase C — Dry-run + operator gate

- [ ] 6. [INFRA] P2. Apply the policy with `cleanupPolicyDryRun: true`; capture the flagged image-count + bytes AND
      assert a ZERO intersection between the flagged-for-deletion set and the Phase-A deployed-digest set. Done-when:
      the dry-run report is committed and the zero-intersection assertion passes (or the offenders it would delete are
      listed for an explicit added Keep).
- [ ] 7. [OPERATOR] P2. Present the dry-run report + the zero-intersection result to the operator for sign-off before
      any real deletion. Done-when: operator approves in-thread.

### Phase D — Apply + verify (human-gated, irreversible)

- [ ] 8. [OPERATOR] P2. Flip `unified-trading-system`'s policy live — human-only, permanent, no AR soft-delete/undelete;
      same human-gate discipline as
      [/codex/02-data/gcs-and-manifest-delete-safety-protocol.md](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md).
      **Note (2026-07-27): that doc's §3a reversibility carve-out does NOT apply here** — §3a's fresh-check
      (`gcs_bucket_soft_delete_retention_seconds`) is specific to GCS bucket objects; Artifact Registry Docker images
      have no equivalent soft-delete/undelete mechanism at all, which is exactly why this todo already states the
      correct AR-specific reason (irreversible, no undo) rather than the GCS reversibility question §3a addresses.
      Done-when: `gcloud artifacts repositories describe unified-trading-system --format="yaml(cleanupPolicies)"` shows
      the live policy.
- [ ] 9. [INFRA] P2. Re-run the storage audit at T+2 days (cleanup runs as a ~daily background job) and confirm the
      actual GB/$ drop vs the dry-run projection AND that no `ImagePullBackOff` / failed-deploy / failed-scale incident
      fired in the window. Done-when: a re-audit CSV shows the reduction and the incident check is clean.

### Phase E — Extend to the rest of the estate

- [ ] 10. [INFRA] P3. Repeat Phases A–D for `unified-trading-library` (928 GB) — profile it sub-path-by-sub-path first,
      then apply the same deployed-digest-keep + floor + 3-day pattern. Done-when: `unified-trading-library` carries a
      live policy verified via `describe`.
- [ ] 11. [DATA] P3. Profile the remaining ~73 GCP Artifact Registry repos (see
      `docker_artifact_storage_audit_2026_07_24.csv`) and apply the same pattern to any showing the
      unbounded-CI-retention shape. Done-when: each remaining repo is either policied or explicitly marked out-of-scope
      with a reason.
- [ ] 12. [INFRA] P3. Design the AWS ECR lifecycle policy for the 20 ECR repos — ECR syntax differs (JSON rule-priority
      list, `countType`/`tagStatus`), and its dry-run analog is `aws ecr start-lifecycle-policy-preview` /
      `get-lifecycle-policy-preview`; apply the same deployed-digest-keep principle. Done-when: a previewed ECR policy
      is presented to the operator for the same sign-off gate as Phase C.
- [ ] 13. [OPERATOR] P3. Delete the legacy GCR bucket `gs://artifacts.central-element-323112.appspot.com` (8.9 GiB, GCR
      is shut down). This is a whole-BUCKET destroy, which is never reversibility-qualified regardless of soft-delete
      config (delete-safety-protocol §3a) — stays `[OPERATOR]`-gated (confirmed live 2026-07-27: the bucket itself
      carries `soft_delete_policy.retentionDurationSeconds=604800`, but that only protects individual objects/versions
      inside a bucket, not the bucket resource itself once deleted). Per §3a's approve-executes flow: stage the exact
      delete command, open a structured BLOCKED question recommending "approve — execute now"; a FINAL operator answer
      authorizes the SAME worker session to run it immediately (no second agent, no manual operator execution) — not the
      old "an agent must never run it, a human runs it separately" framing. Done-when: the bucket is gone and the
      re-audit no longer lists it.
- [ ] 14. [INFRA] P3. Stub `/codex/05-infrastructure/artifact-registry-cleanup-policy.md` — the per-package scoping
      decision, the keep-deployed-digest + keep-floor + delete-window pattern, and an explicit disambiguation of
      **Docker images (ephemeral, CI-rebuildable, prunable) vs data/model artifacts (permanent retention per
      artifact-versioning.md)**, stating the delete policy is scoped to AR Docker repos ONLY and must never touch the
      data-artifact GCS buckets. Done-when: the codex doc exists and is linked from this plan.

### Phase F — Code-tarball bucket retention (GCS lifecycle, human-gated)

- [ ] 15. [DATA] P3. Determine which `@sha` tarballs in `gs://deployment-scripts-central-element-323112/code/` are still
      referenced — by a live VM (`gcloud compute instances list`), a launcher default, or a `deployments/active/*.json`
      registry entry — so the lifecycle rule never deletes a referenced copy. Done-when: the referenced-`@sha` set (or
      "only current-pointers referenced") is listed.
- [ ] 16. [INFRA] P3. Draft a GCS lifecycle rule on the `code/` prefix that ages out old `@sha` tarballs + manifests
      (e.g. `age > 30d` AND not the current-pointer AND not in the Phase-15 referenced set); the per-repo
      `<repo>-code.tar.gz` current-pointer is always kept. Done-when: the lifecycle JSON is committed and a dry
      enumeration shows only stale `@sha` objects in scope.
- [ ] 17. [OPERATOR] P3. Apply the tarball lifecycle rule live — human-gated prod delete, cite the delete-safety
      protocol. Done-when: `gcloud storage buckets describe` shows the rule and the `code/` prefix size stops growing.

## Review findings this plan encodes

Review of the original "keep-5 + delete-older-than-3d" proposal. All are addressed by the phases above.

1. **[Safety — highest] Neither rule protects a currently-deployed-but-old image.** The deployed version is not the
   latest push — it is whatever deployment-service pins in `stable_versions.yaml` (MTDS deploys "via-dispatch": its
   `cloudbuild.yaml` only notifies deployment-service). For a busy service, a pin older than 3 days sits outside both
   the keep-5-recent set (~7 hours for MTDS) and the 3-day window → **deleted, irreversibly**. An already-running
   process survives (image is on the node's disk); the failure is the next _pull_ — restart, autoscale-up, reschedule,
   node replacement, or a rollback. → Audit the deployed set first + add an explicit `keep-deployed-digests` rule
   (Phases A/B), making the policy correct-by-construction. Blast radius is narrow (tarball fleet unaffected;
   `strategy-service`/`execution-service` are GCP-idle as of 2026-07-24) but the audit still gates the flip.
2. **[Design] The 20-per-package-rules rationale likely misreads AR semantics.** `mostRecentVersions.keepCount` is
   believed to apply per package, not per repo — if so a single repo-wide keep-5 already yields 5-per-service (2 rules,
   not 21). `packageNamePrefixes` is a prefix match (footgun on shared prefixes). → Verify against GCP docs + the
   dry-run before committing to 20 rules (Phase B, todo 4).
3. **[Cross-ref] Codex already governs "artifact" retention — with the opposite rule, for a different artifact.**
   [/codex/04-architecture/artifact-versioning.md](/codex/04-architecture/artifact-versioning.md) mandates "permanent
   retention for replay" — but for _data/model/feature_ artifacts, not Docker images. → The new codex stub must
   disambiguate, and the 3-day delete must be scoped to AR Docker repos only, never the data-artifact GCS buckets (todo
   14).
4. **[Scope] The proposal was AR-only and missed the code-tarball bucket.** `gs://deployment-scripts-…/code/` keeps a
   current-pointer per repo **plus 732 accumulating `@sha` copies** (versioning off), ~~2.39 GB (~~$0.24/mo) — same
   disease, tiny cost, different fix (a GCS lifecycle rule under the delete-safety protocol, not an AR policy) → Phase
   F.
5. **[Minor] Loose ends** — legacy GCR bucket can just be deleted (GCR is shut down, todo 13); ECR has its own dry-run
   analog (`start-lifecycle-policy-preview` / `get-lifecycle-policy-preview`, todo 12); the supporting CSV/HTML exist at
   the workspace root but are uncommitted.

## Codex SSOTs

- [/codex/05-infrastructure/vm-tarball-deployment.md](/codex/05-infrastructure/vm-tarball-deployment.md) — tarball vs
  Docker-image runtime split (defines the blast radius).
- [/codex/05-infrastructure/deployment-and-qg-strategy.md](/codex/05-infrastructure/deployment-and-qg-strategy.md) —
  image-only prod deploys + "all prod VMs on pinned image SHA" gate.
- [/codex/04-architecture/artifact-versioning.md](/codex/04-architecture/artifact-versioning.md) — "permanent retention
  for replay" applies to DATA/model artifacts, NOT Docker images; the new stub must not conflict.
- [/codex/02-data/gcs-and-manifest-delete-safety-protocol.md](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md)
  — human-gated-delete discipline the AR image deletes follow.
- **To create (todo 14):** `/codex/05-infrastructure/artifact-registry-cleanup-policy.md`.

## Supporting artifacts

The original audit output lives at the **workspace root, outside any git repo** — so it does NOT travel with this plan:

- `/active/unified-trading-system-repos/docker_artifact_storage_audit_2026_07_24.csv` — full 75-row matrix.
- `/active/unified-trading-system-repos/docker_artifact_storage_audit_2026_07_24.html` — interactive sortable report.

If absent when the next shift picks this up, **regenerate** via the read-only pull that produced them
(`gcloud artifacts repositories list` across both projects + `aws ecr describe-images` across the 20 repos); the numbers
in § Diagnosis are the reference. (Todo 11 uses the CSV only as a convenience index of the ~73 remaining repos.)
