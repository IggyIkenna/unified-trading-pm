# GitHub Projects v2 Schema and Automation Mapping

Defines standardized fields and automation expectations for issues, epics, milestones, and subtasks.

---

## Core Fields

- `status`: pending | in_progress | ready_for_testing | uat_accepted | done
- `priority`: P0-critical | P1-high | P2-medium | P3-low
- `assignee_group`: strategy_ml | sports | infra | pm_spec | hardening_finishline
- `iteration`: weekly cadence slot
- `readiness_tier`: smoke_tested | scale_tested | history_validated | live_stability_validated
- `commercial_stage`: signal_candidate | signal_commercial_ready | strategy_candidate | strategy_commercial_ready
- `uat_required`: yes | no
- `target_cloud`: gcp_primary | aws_backup | dual_cloud_ready
- `historical_completion_note`: free text (for backfilled/retrospective tasks)
- `owner_default`: Ikenna | Harsh | Femi
- `lane`: audit_remediation | capability_request

---

## Auto-Creation Mapping

Input sources:

- audit findings (`fail`, `partial`),
- normalized request cards.

Output artifacts:

- epic (when request spans multiple repositories/services),
- milestone (readiness/commercial stage target),
- issue(s) for executable work,
- subtasks for implementation, tests, docs, observability, and rollout.

---

## Owner Bootstrap Rules

- sports -> Harsh
- strategy_ml -> Ikenna
- infra -> Femi
- pm_spec -> Ikenna
- hardening_finishline -> Harsh

All are defaults only; explicit override remains allowed.

---

## Required Subtask Types

For all major items:

1. implementation
2. tests (unit/integration/regression as appropriate)
3. observability and alerting
4. docs/runbooks
5. checklist and PM sync verification

---

## Synchronization Rule

For gated work, status changes must remain consistent across:

- GitHub Projects v2 field state,
- codex lifecycle expectations,
- deployment checklist YAML status.
