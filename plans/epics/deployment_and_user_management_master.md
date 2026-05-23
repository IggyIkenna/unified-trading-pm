---
name: deployment_and_user_management_master
title: "Deployment And User Management Master"
type: epic
tier: L3
status: active
priority: P0
assigned_vm: vm-operator-ops
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../archive/2026_05/deployment_ui_lifecycle_tabs_2026_05_08.md
---

# Deployment And User Management Master

**Owns**: deployment-api + deployment-ui + user-management-service + user-management-ui

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## UI Verification Contract (HARD RULE — codified 2026-05-23)

All active plans under this epic that touch any UI repo (`deployment-ui`, `user-management-ui`,
`unified-trading-system-ui`) MUST pass the playwright verification gate before any todo is ticked ✅ done. Per
`plans/PLAN_FORMAT.md` § 9 and `codex/06-coding-standards/ui-testing-layers.md` § "Plan-Level Enforcement":

- **`[UI]` tag**: every UI-touching todo MUST use `[AGENT][UI]` or `[HUMAN][UI]` (not bare `[AGENT]`).
- **pw:L2 ✓**: `npx playwright test --project=chromium tests/smoke/` exits 0 before tick.
- **regression guard**: spec written/updated in `tests/e2e/`, `tests/playbooks/`, `tests/widgets/`, or `tests/smoke/`
  matched to the change layer (widget→L1.5, route→L2, playbook flow→L3a, visual→L4).
- **Evidence format**: `— repo@sha | pw:L2 ✓ | regression: tests/path/spec.ts` appended to tick line.
- **Reviewer rejects** ticks missing `pw:` or `regression:` — same weight as a missing `docs(plans):` flip.

Key deployment/user-management UI surfaces and their required layers:

| Surface                           | Layer | Regression guard path                         |
| --------------------------------- | ----- | --------------------------------------------- |
| Deployment-ui route loads         | L2    | `tests/smoke/routes.spec.ts`                  |
| Data-status panel honest-coverage | L2    | `tests/smoke/routes.spec.ts`                  |
| User-management form / auth flow  | L3a   | `tests/playbooks/auth_flow.spec.ts`           |
| Deployment lifecycle widget       | L1.5  | `tests/widgets/deployment-lifecycle.test.tsx` |

## Codex SSOTs

| Doc                                                      | Owns                                                                                                        |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `codex/08-workflows/deployment-flow.md`                  | Operator promotion path (dev → staging → main + paper → live); full promotion lifecycle                     |
| `codex/04-architecture/promote-workflow-architecture.md` | Strategy promote path; `MinimalCandidateManifest`; `POST /api/promote/{strategy_id}/{manifest_id}` contract |
| `codex/04-architecture/batch-live-architecture.md`       | Mode-toggle invariant (batch vs live); same-codepath requirement                                            |
| `codex/03-deployment/data-status-ui-surface.md`          | Data-status UI honest-coverage surface; deployment-ui freshness display                                     |

## Assigned active plans

_1 active plans declare `parent_epic: deployment_and_user_management_master` in their frontmatter. Workers pick up in
priority order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority)_

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

### [`gap_2_4_d_deployment_api_reader_repoint_2026_05_22`](../archive/2026_05/gap_2_4_d_deployment_api_reader_repoint_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — Code half shipped (deployment-api reader repointed to env-tiered bucket names).
Remaining execution half tracked in `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.1 — merges in Phase
0d window. · **estimate**: 0.8 cal AI-days (class: infra)

### [`deployment_ui_lifecycle_tabs_2026_05_08`](../archive/2026_05/deployment_ui_lifecycle_tabs_2026_05_08.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases A-H shipped (Slots 6+7); H4/G2/G3 DEFERRED-OPERATOR-DECISION (DNS gate) ·
**estimate**: 30 cal AI-days (class: brand-new)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
