---
scope: [engineer, admin]
title: Cloud-Agnostic Build Lineage
status: stub-post-cutover
created: 2026-05-07
authoritative_for:
  How Docker images, VM tarballs, and code tarballs are built, tagged, and tracked across BOTH GCP Artifact Registry and
  AWS ECR so that a single git SHA produces parity-verified artifacts on both clouds.
referenced_by:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/aws_migration_defi_first_2026_05_07.md
related:
  - codex/05-infrastructure/vm-tarball-deployment.md
  - codex/05-infrastructure/launcher-script-ssot.md
  - codex/05-infrastructure/cloud-agnostic-script-pattern.md
last_reviewed: 2026-05-17
---

# Cloud-Agnostic Build Lineage

> **[DELTA 2026-05-22]** **Current state:** Dual-cloud artifact parity is NOT YET implemented. VM tarball deployment is
> the live path (see `codex/05-infrastructure/vm-tarball-deployment.md`). No cross-cloud image mirror or SHA-pinned
> artifact registry exists yet. **Planned delta:** Dual-cloud build lineage tracked under
> `plans/epics/infrastructure_master.md`. **Target architecture:** Single git SHA produces parity-verified Docker images
> in both GCP Artifact Registry and AWS ECR + code tarballs on both S3 and GCS.

> **Status:** STUB (post-cutover) — created 2026-05-07 to anchor forward-references from active plans. Body to be filled
> in as the work progresses post-cutover.

## Purpose

Define the SSOT for how a single git commit on `live-defi-rollout` (or `main`) produces a deterministic set of artifacts
— Docker images, VM tarballs, code tarballs — pushed to BOTH GCP Artifact Registry and AWS ECR / S3. Any artifact
running in production must trace back to a known git SHA + builder run on both clouds.

## Scope

- Docker image build pipeline (per-service `Dockerfile` → multi-cloud push).
- VM code tarball pipeline (`deployment-service/scripts/vm/create-code-tarballs.sh` → GCS + S3 upload).
- Lineage metadata: image tags, manifest digests, build timestamps, builder identity (GHA vs Cloud Build vs CodeBuild).
- Cross-cloud parity verification (digest-equal artifacts on both clouds for the same SHA).
- Rollback semantics — pinning a service to a specific lineage record.

## Outline (planned sections)

1. **Artifact taxonomy** — Docker images, VM tarballs, code tarballs, contract bundles. Per-asset-group flavor matrix.
2. **Build sources** — GitHub Actions (primary), GCP Cloud Build (legacy), AWS CodeBuild (parity). Trigger conventions.
3. **Tag conventions** — `<sha>` immutable + `latest` floating. Per-cloud registry path templates.
4. **Lineage metadata schema** — JSONL record per artifact:
   `{sha, repo, builder, build_ts, gcp_uri, aws_uri, digest_gcp, digest_aws}`.
5. **Parity verification** — `verify-build-parity.sh` runs `docker manifest inspect` on both clouds, asserts digest
   equality.
6. **VM launchers** — how `setup-data-pipeline-vm.sh` resolves cloud-specific tarball URI from the registry's lineage
   record.
7. **Rollback procedure** — pin a service to an older SHA across both clouds; verify pin held after a redeploy.

## Cross-references

- **Plan(s) implementing this:**
  [`master_to_live_defi_2026_05_23`](../../plans/active/master_to_live_defi_2026_05_23.md) work-stream F,
  [`aws_migration_defi_first`](../../plans/active/aws_migration_defi_first_2026_05_07.md).
- **Related codex SSOTs:** [`vm-tarball-deployment`](./vm-tarball-deployment.md),
  [`launcher-script-ssot`](./launcher-script-ssot.md),
  [`cloud-agnostic-script-pattern`](./cloud-agnostic-script-pattern.md).
- **Code:** `deployment-service/scripts/vm/create-code-tarballs.sh`, `.github/workflows/build-and-push-*.yml`.

## Open questions

- Does GHA push directly to AWS ECR, or do we relay via Cloud Build → cross-cloud copy? (cost vs latency tradeoff)
- Where does the lineage JSONL live — GCS bucket, S3, or both with consolidator? (recommend: write to both, reconcile)
- Do we sign images (cosign / notation) on both clouds for supply-chain provenance? (post-cutover work? see
  `infrastructure_master.md`)
- How do we test parity in CI vs only at promote-time? (per-PR vs per-merge)
