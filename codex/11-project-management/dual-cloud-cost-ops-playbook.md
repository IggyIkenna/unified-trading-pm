---
doc_type: codex-ssot
title: Dual-Cloud and Cost Operations Playbook
summary:
  Operational guidance for dual-cloud (GCP-primary/AWS-backup) readiness gates, rollback + immutable version-tagging
  requirements, AWS-credits backup posture tracking, and low-cost agent/Cursor operating practices.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [dual-cloud, cost-ops, rollback, aws, dr, cost]
related:
  [
    /codex/11-project-management/secrets-migration-tracking.md,
    /codex/11-project-management/defi-bucket-sizes-2026-05-07.md,
  ]
created: 2026-03-27
authoritative_for: [dual-cloud readiness gates, rollback and version-tagging requirements]
referenced_by:
owner:
last_reviewed: 2026-08-11
code_refs:
---

# Dual-Cloud and Cost Operations Playbook

Operational guidance for dual-cloud readiness, rollback/version control, AWS-credit fallback planning, and low-cost
execution practices.

---

## Dual-Cloud Readiness Model

Primary model:

- GCP primary runtime
- AWS backup posture for resilience and negotiating leverage

**DeFi compute — AWS ECS decommission in progress, cited 2026-08-11.** `features-service`, `execution-service`, and
`strategy-service` ran as live AWS ECS Fargate tasks (`uts-defi-prod` cluster) against AWS S3 buckets that were empty —
real data always lived in GCS — driving ongoing cross-cloud egress cost on top of AWS compute itself. This superseded
the mid-2026-05 "DeFi client mandate on AWS" placement
(`/plans/archive/2026_05/aws_migration_defi_first_2026_05_07.md`), whose AWS-co-located data-and-compute premise was
never completed. As of 2026-08-10, all 3 services are cut over to GCP Cloud Run and confirmed healthy; AWS ECS compute
is scaled to 0 (`uts-strategy-service-prod`'s ECS service already deleted). The `uts-defi-prod` cluster + remaining
service/task-definition teardown is gated on a multi-day observation window, not yet executed. Full record:
`/plans/active/defi_compute_gcp_migration_2026_08_08.md`.

Readiness must be codified in:

1. codex standards,
2. deployment checklist YAMLs,
3. GitHub PM fields/milestones.

---

## Required Dual-Cloud Gates

- Cloud-agnostic abstractions in use (storage/secrets/core clients)
- Environment config has no hardcoded project/account identifiers
- DR runbook includes cross-cloud fallback workflow
- Service deployment artifacts can be reproduced in backup cloud baseline
- Data portability/export path validated for critical datasets

---

## Rollback and Version Tagging

- Every deployment has immutable version tag (git SHA + semantic release tag when used).
- Rollback procedure must define:
  - automated rollback trigger thresholds,
  - manual rollback command path,
  - max rollback completion SLO.
- Rollback readiness is a hard gate for live-critical services.

---

## Shared Local Quality and Quickmerge (Machine-Agnostic)

- Provide shell-based scripts with no hard dependency on Docker for local execution.
- Keep scripts deterministic and repo-relative.
- Use quality-gates + quickmerge wrappers that work across macOS/Linux shells.
- Validate required tools at script start and fail with actionable messages.

---

## AWS Credits Backup Posture

- Track credit application status as PM artifact, not an informal note.
- Link planned AWS fallback experiments to milestones and checklist gates.
- Keep fallback scope minimal until credits and security controls are confirmed.

---

## Low-Cost Agent and Cursor Operating Guidance

- Prefer scoped request cards over broad prompts to reduce iteration cost.
- Reuse normalized templates and unknowns checklists to reduce rework.
- Batch documentation updates, then perform single PM sync cycle.
- Keep external model-API jobs scheduled and bounded; log usage by workload type.
