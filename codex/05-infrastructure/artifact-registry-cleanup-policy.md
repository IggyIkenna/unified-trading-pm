---
doc_type: codex-ssot
title: Artifact Registry / ECR Cleanup Policy
summary: >-
  The canonical cleanup policy pattern for Docker-image Artifact Registry (GCP) and ECR (AWS) repos —
  keep-deployed-digests + keep-5-recent floor + delete-older-than-3d. Scoped to ephemeral CI-rebuildable Docker images
  ONLY; must never touch data/model/feature artifact GCS buckets (permanent retention per artifact-versioning.md).
status: current
nature: ssot
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [artifact-registry, ecr, docker-images, cleanup-policy, retention, cicd, storage-cost]
related:
  [
    /codex/04-architecture/artifact-versioning.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
created: 2026-07-29
authoritative_for:
  [artifact-registry cleanup policy pattern, Docker-image retention policy shape, AR-vs-ECR policy mapping]
owner:
last_reviewed: 2026-07-29
referenced_by:
code_refs:
---

# Artifact Registry / ECR Cleanup Policy

> **SSOT for the Docker-image retention policy applied to all GCP Artifact Registry and AWS ECR repos.** Implementation
> plans:
> [docker_artifact_registry_cleanup_policy_2026_07_24.md](/plans/active/docker_artifact_registry_cleanup_policy_2026_07_24.md)
> (parent),
> [docker_artifact_registry_cleanup_side_tracks_2026_07_27.md](/plans/active/docker_artifact_registry_cleanup_side_tracks_2026_07_27.md)
> (satellite).

## Scope — Docker images only, never data artifacts

This policy applies to **ephemeral, CI-rebuildable Docker images** in Artifact Registry (GCP) and ECR (AWS). These
images are gate-passed CI outputs that can be rebuilt from source at any time. The policy explicitly does NOT apply to:

- **Data/model/feature artifacts** stored in GCS — these carry permanent retention for replay per
  [/codex/04-architecture/artifact-versioning.md](/codex/04-architecture/artifact-versioning.md).
- **Code tarballs** in `gs://deployment-scripts-central-element-323112/code/` — these are a different artifact class
  governed by a separate GCS lifecycle rule (see
  [the satellite plan](/plans/active/docker_artifact_registry_cleanup_side_tracks_2026_07_27.md) Phase F).

A lifecycle or cleanup policy scoped to an AR/ECR Docker repo MUST use a `Delete` action rule and MUST NOT be applied to
any GCS bucket containing data artifacts.

## Policy shape — 3 rules (GCP Artifact Registry)

```yaml
# 1. Protect every non-:latest pinned deployed digest — the safety spine
- name: keep-deployed-digests
  action: { type: Keep }
  condition:
    tagState: tagged
    packageNamePrefixes: [<package with pinned tag>]
    tagPrefixes: [<the specific SHA or version tag>]

# 2. Background floor — protects quiet/never-recently-built packages
- name: keep-5-recent
  action: { type: Keep }
  mostRecentVersions:
    keepCount: 5

# 3. The pruner — delete everything beyond keep-5 that is older than 3 days
- name: delete-older-than-3d
  action: { type: Delete }
  condition:
    tagState: any
    olderThan: "259200s"
```

### Key design decisions

1. **`mostRecentVersions.keepCount` is per-package, not per-repo.** Verified against GCP docs (2026-07-24). Omitting
   `packageNamePrefixes` from the keep-5-recent rule applies it repo-wide, keeping 5 versions of each package. A single
   repo-wide rule covers all packages.

2. **`:latest`-tracking consumers are inherently protected.** `keepCount: 5` is a "N most recently _pushed_" rule, not
   date-scoped. Whatever a package's `:latest` tag points to is, by construction, always inside its own top-5. The
   explicit `keep-deployed-digests` rule is only load-bearing for services pinned to a **specific, non-`:latest` tag**
   that isn't being kept fresh by new pushes.

3. **`versionNamePrefixes` matches digest names, not tags.** For tag-based protection, use `tagPrefixes` scoped by
   `packageNamePrefixes`. AR's `condition` fields AND together — a `versionNamePrefixes` check against a git-sha tag
   string silently matches nothing.

4. **`olderThan` uses seconds, not a human-readable duration.** The AR API expects a duration string like `"259200s"` (3
   days), not `"3d"`.

5. **No AR soft-delete/undelete exists.** Deletion of an AR image version is permanent and irreversible. The dry-run
   (`cleanupPolicyDryRun: true`) + deployed-digest cross-check is mandatory before any live flip. The live flip
   (`--no-dry-run`) is **operator-gated** — same human-only hard-stop as force-push-main and wallet keys.

### Application procedure

1. **Phase A — Audit deployed digests.** Enumerate live consumers (Cloud Run services/jobs, GCE VMs) and identify any
   non-`:latest` pinned tags that need explicit `keep-deployed-digests` protection.
2. **Phase B — Draft policy.** Create the JSON file per the shape above. For repos with zero non-`:latest` consumers,
   omit the `keep-deployed-digests` rule (2 rules total).
3. **Phase C — Dry-run.** Apply with `--dry-run`, verify via `gcloud artifacts repositories describe`, replicate the
   policy logic against a live image pull, assert zero-intersection between the flagged-for-deletion set and every
   deployed digest.
4. **Phase D — Operator sign-off + live flip.** Operator reviews dry-run report. Live flip (`--no-dry-run`) is
   human-only.

```
gcloud artifacts repositories set-cleanup-policies <repo> \
  --location=<location> \
  --policy=<policy.json> \
  --dry-run                           # Phase C
gcloud artifacts repositories set-cleanup-policies <repo> \
  --location=<location> \
  --policy=<policy.json> \
  --no-dry-run                        # Phase D (operator-gated)
```

## AWS ECR — adapted 2-rule policy

ECR lifecycle policies differ from GCP AR in several ways. The closest equivalent policy:

```json
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Expire untagged images older than 3 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countNumber": 3,
        "countUnit": "days"
      },
      "action": { "type": "expire" }
    },
    {
      "rulePriority": 2,
      "description": "Keep the 5 most recent tagged images, expire rest",
      "selection": {
        "tagStatus": "tagged",
        "tagPatternList": ["*"],
        "countType": "imageCountMoreThan",
        "countNumber": 5
      },
      "action": { "type": "expire" }
    }
  ]
}
```

### Key ECR differences

| GCP AR feature                                  | ECR equivalent                                            | Notes                                |
| ----------------------------------------------- | --------------------------------------------------------- | ------------------------------------ |
| `mostRecentVersions.keepCount: 5` (per-package) | `imageCountMoreThan: 5` (per-repo)                        | ECR is per-repo, not per-package     |
| `olderThan: 259200s`                            | `sinceImagePushed: 3 days`                                | For untagged images                  |
| `Keep` action                                   | No equivalent — design rules so wanted images don't match | ECR only has `expire`                |
| `tagPrefixes` (keep-deployed-digests)           | No direct equivalent                                      | Protected by `imageCountMoreThan: 5` |

### ECR preview (dry-run analog)

```
aws ecr start-lifecycle-policy-preview --repository-name <repo> \
  --lifecycle-policy-text "file://policy.json"
aws ecr get-lifecycle-policy-preview --repository-name <repo>
```

## GCP-managed repos — out of scope

These AR repos are auto-created by GCP services and do not support custom cleanup policies:

- `cloud-run-source-deploy` (all locations) — Cloud Run source deployments
- `gcf-artifacts` (all locations) — Cloud Functions artifacts
- `firebaseapphosting-images` (all locations) — Firebase Hosting
- `container-registry`, `gae-standard` — legacy GCR/App Engine
- `gcr.io` (all domains) — legacy GCR, shut down

## Code tarballs — GCS lifecycle, not AR

The code-tarball bucket `gs://deployment-scripts-central-element-323112/code/` holds a different artifact class. Its
cleanup is via a GCS lifecycle rule or periodic Python cleanup, governed by the same
[/codex/02-data/gcs-and-manifest-delete-safety-protocol.md](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md):

- **Current-pointers** (`<repo>-code.tar.gz`, `<repo>-code.manifest.json`) — always kept
- **@sha objects** (`<repo>-code@<sha>.tar.gz`, `<repo>-code@<sha>.manifest.json`) — aged out after 30 days
- The `@` character cleanly distinguishes @sha objects from current-pointers

GCS `matchesPattern` condition may not be available for all projects. Fallback: Python SDK cleanup targeting objects
with `@` in the name, `.tar.gz`/`.manifest.json` suffix, older than 30 days. Enable soft-delete (7-day retention) on the
bucket first for reversibility.

## Reference

- Policy JSONs and dry-run reports live alongside the implementation plans in `plans/active/`.
- The reusable standard 2-rule template (no keep-deployed-digests):
  `docker_artifact_registry_cleanup_policy_standard_2rule.json`
- All policy application is via the `unified-trading-sa` service account (self-service IAM: grant
  `roles/artifactregistry.admin` on the target repo if needed).
