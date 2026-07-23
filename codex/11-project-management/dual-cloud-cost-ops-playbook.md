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
last_reviewed: 2026-05-17
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
