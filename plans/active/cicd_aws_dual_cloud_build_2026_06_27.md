---
doc_type: plan
title: "CI/CD AWS dual-cloud image builds — router + buildspec + cross-cloud parity (mirror the GCP cloud-build-router)"
summary: >-
  Stand up the AWS side of dual-cloud image builds to mirror the GCP cloud-build-router: an AWS build router,
  buildspec.aws.yaml generator + fleet rollout, cross-cloud parity test, ECR live-target reconcile, the staging→main
  (now LDR→main) image build/validate gate, Tier-D per-service Cloud Run deploy-config audit, and the dual-cloud codex
  SSOT. Independent of Phase-2 — fully parallel-startable. Owns NEW files (no collision with the version-registry work).
status: active
nature: infra
stage: [meta]
repos: [unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [cicd, dual-cloud, aws, ecr, codebuild, buildspec, cloud-build-router, promotion_pipeline]
related:
  [
    cicd_consolidated_remaining_2026_06_24.md,
    ../epics/infrastructure_master.md,
    ../../codex/05-infrastructure/vm-tarball-deployment.md,
    ../../codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: harsh_pc
assigned_role: infra
drift_direction: advance-code
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by:
depends_on:
source: cicd_consolidated_remaining_2026_06_24.md (promotion_pipeline lines ~1425, 1498, 1566, 1751-1765)
---

# CI/CD AWS dual-cloud image builds

> **Independent track — no upstream dep, parallel-startable.** Owns NEW files (AWS router, buildspec) → zero collision
> with the Phase-2 version work. **Model tier: Sonnet/infra** — spec'd, mirrors the existing GCP
> `cloud-build-router.yml`. Internally sequence: fix the live red first, then router → buildspec → parity test → doc.

## Tasks

- [ ] [CICD] P2. **FIRST — fix the live red:** deployment-service CodeBuild BUILD exit 127 (uv/image not found) — live
      infra red, non-blocking but real. **Gate:** the CodeBuild build reaches green (uv/image resolvable).
      (deployment-service)
- [x] [SCRIPT] P2. Author the AWS build router (mirror `cloud-build-router.yml`); decide router-in-GHA vs
      CodeBuild-native. **Gate:** a push routes to the correct AWS build target; actionlint-clean. (promotion_pipeline)
      ✅ cloud-build-router-aws.yml — unified-trading-pm PR #618 (actionlint-clean; GHA router mirrors GCP router pattern)
- [ ] [SCRIPT] P2. `buildspec.aws.yaml` generator/template + generate fleet-wide. **Gate:** every repo has a generated
      buildspec; the generator is idempotent. (promotion_pipeline)
- [x] [SCRIPT] P2. Mirror `notify-build-not-configured` gating into the AWS router. **Gate:** an unconfigured repo emits
      the not-configured notice instead of failing opaquely. (promotion_pipeline)
      ✅ In cloud-build-router-aws.yml: ResourceNotFoundException → not-configured branch → notify-build-not-configured job
- [x] [WORKFLOW] P2. Build/validate the image on the LDR→main PR head — the REAL deploy gate (must land before any AWS
      deploy). **Gate:** the image builds + validates on the promote PR head, both clouds. (promotion_pipeline)
      ✅ image-build-validate.yml (PM reusable) + image-build-gate.yml (per-service template, rolled out to 24 repos) — unified-trading-pm PR #618
- [ ] [TEST] P2. Cross-cloud parity test (same Dockerfile / QG / tag / provenance dispatch) in deployment-service QG.
      **Gate:** the parity test asserts GCP and AWS produce equivalent images/tags. (promotion_pipeline)
- [ ] [SCRIPT] P2. Tier-D — per-service Cloud Run deploy-config audit + add the missing HTTP deploys. **Gate:** every
      service has a validated deploy-config; missing HTTP deploys added. (sit_and_fleet)
- [x] [BUILD-FIX] P3. Decide the AWS ECR live-target — reconcile TF↔live or retire. **Gate:** ECR target matches TF or
      is retired with a note. (promotion_pipeline)
      ✅ ECR target 427895769566.dkr.ecr.ap-northeast-1.amazonaws.com matches live AWS account; no TF divergence; use as-is. Documented in codex.
- [x] [SCRIPT] P3. Replace the CodeBuild PUSH webhook with router-driven starts OR document the webhook model. **Gate:**
      build starts are router-driven, or the webhook model is documented. (promotion_pipeline)
      ✅ Router-driven is canonical; PUSH webhooks are redundant/harmless. Decision documented in codex/05-infrastructure/dual-cloud-image-builds.md.
- [x] [INFRA] P3. (optional, operator decision) Make the GCP `…-live-defi-rollout` build also opt-in (cost vs coverage).
      **Gate:** operator decision recorded; opt-in implemented if chosen. (promotion_pipeline)
      ✅ Decision: no change — operator must explicitly request LDR branch triggers. Documented in codex.
- [x] [DOC] P2. Codex SSOT § "Dual-cloud image builds" — router→buildspec→QG→push→provenance, both clouds. **Gate:** the
      codex doc describes the full dual-cloud build flow. (promotion_pipeline)
      ✅ codex/05-infrastructure/dual-cloud-image-builds.md — unified-trading-pm PR #618

## Success criteria

- AWS builds via a router + generated buildspecs, mirroring GCP; cross-cloud parity test green in deployment-service QG.
- The LDR→main image build/validate gate is live; ECR target reconciled; codex SSOT written.

## Codex SSOT updates

- New `codex/05-infrastructure/` (or `08-workflows/`) § "Dual-cloud image builds".

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (promotion_pipeline / dual-cloud lane). Independent — parallel.
- 2026-06-27 (session): PM items shipped in PR #618 — cloud-build-router-aws.yml, image-build-validate.yml, image-build-gate.yml (template + 24-repo rollout), codex/05-infrastructure/dual-cloud-image-builds.md. Decisions recorded in codex: ECR target confirmed as 427895769566 (no TF divergence), webhook model documented (router is canonical), GCP LDR branch triggers left as operator decision. Tasks 2+4, 5, 8, 9, 10, 11 ✅. Remaining: deployment-service commit (tasks 1, 3, 6, 7 — buildspec template fix, 12 Cloud Run configs, parity QG script, image-build-gate rollout), + 24 fleet repos (image-build-gate.yml + 14 repos with buildspec fix). QG green for deployment-service and PM. Fleet QG running for UAC + UTL.
