---
doc_type: epic
title: Deployment And User Management Master
summary:
  L3 epic owning deployment-api + deployment-ui + user-management (deploy/launch consoles, data-status honest-coverage
  surface, promote endpoints, auth flow); every UI-touching todo gated by the playwright pw:L2 verification contract
  before tick.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, infrastructure, data-status, verification, observability]
related: [../archive/2026_05/deployment_ui_lifecycle_tabs_2026_05_08.md]
created: 2026-05-21
name: deployment_and_user_management_master
tier: L3
priority: P0
assigned_vm: vm-operator-ops
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans: [../archive/2026_05/deployment_ui_lifecycle_tabs_2026_05_08.md]
last_updated: 2026-07-14
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Deployment And User Management Master

**Owns**: deployment-api + deployment-ui (was: also user-management-service + user-management-ui — dropped 2026-07-12:
both ARCHIVED per `codex/DEPRECATED_UIS_NOTICE.md` + `codex/05-infrastructure/ui-functionality-requirements.md` ("User
Management | user-management-ui | archived") + CLAUDE.md's system map ("`user-management-ui` ARCHIVED"); no
`user-management-service` repo exists in the workspace. Findings #314/#385, plan-reconciliation
`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling.)

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## UI Verification Contract (HARD RULE — codified 2026-05-23)

All active plans under this epic that touch any UI repo (`deployment-ui`, `unified-trading-system-ui` — was: also
`user-management-ui`, ARCHIVED, see "Owns" note above, corrected 2026-07-12) MUST pass the playwright verification gate
before any todo is ticked ✅ done. Per `plans/PLAN_FORMAT.md` § 9 and `codex/06-coding-standards/ui-testing-layers.md` §
"Plan-Level Enforcement":

- **`[UI]` tag**: every UI-touching todo MUST carry a `[UI]` marker — either combined (`[AGENT][UI]`/`[HUMAN][UI]`) or
  bare `[UI]` (the established convention in this epic's own child plans); a role tag with no `UI` marker at all (bare
  `[AGENT]`/`[HUMAN]`) is what's disallowed. **[Corrected 2026-07-14, finding 55]** (was: text required ONLY the
  combined form, contradicting a corpus grep showing bare `[UI]` is the majority-used, already-accepted tag on
  evidence-backed shipped ticks, e.g. `data_status_tab_and_downloads_remediation_2026_06_16.md:152`; the substantive
  gate — `pw:L2 ✓` + `regression:` evidence below — is unchanged and still mandatory).
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

_3 active plans declare `parent_epic: deployment_and_user_management_master` in their frontmatter. Workers pick up in
priority order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

> **Corrected 2026-07-12 (was: banner + P0/P2 blocks below showed 0 active plans, unrun since the two plans below were
> created)** — manually resynced against a live grep of `plans/active/*.md` `parent_epic:` frontmatter (the populator
> script's own `WORKSPACE` path is hardcoded to a different host and scans all 19 epics at once, out of scope for this
> single-file reconciliation pass; the entries below reproduce its documented output format). Finding #314,
> plan-reconciliation `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified"
> blanket ruling.

> **Corrected 2026-07-14, finding 54** (was: roster + count above still said "2 active plans" / omitted the
> `deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13` plan entirely) — that plan was created 2026-07-13,
> one day after the prior resync above, with `status: active`, `priority: P0`,
> `parent_epic: deployment_and_user_management_master` matching this epic's own inclusion criteria; re-synced against a
> fresh grep of `plans/active/*.md`.

## P0 — must complete before next foundation gate

### [`data_status_tab_and_downloads_remediation_2026_06_16`](../active/data_status_tab_and_downloads_remediation_2026_06_16.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: refactor) · **title**: Data-status tab + instruments download
remediation (deployment-api / deployment-ui / CeFi universe)

### [`deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13`](../active/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md)

**status**: active · **estimate**: 3.6 cal AI-days (class: design) · **title**: deployment-api cache OOM + UI latency
remediation — bounded caching architecture that fits 4GB. **[Added 2026-07-14, finding 54]**

## P1 — important; post-current-gate

_(no plans currently assigned at this priority)_

## P2 — useful; opportunistic

### [`test_fleet_image_builds_from_current_code_2026_06_17`](../active/test_fleet_image_builds_from_current_code_2026_06_17.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: research) · **title**: Test fleet image builds from current
code — local (amd64) → GCP → AWS, base-first, no-deploy

### [`gap_2_4_d_deployment_api_reader_repoint_2026_05_22`](../archive/2026_05/gap_2_4_d_deployment_api_reader_repoint_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — Code half shipped (deployment-api reader repointed to env-tiered bucket names).
Remaining execution half tracked in `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.1 — merges in Phase
0d window. · **estimate**: 0.8 cal AI-days (class: infra)

### [`deployment_ui_lifecycle_tabs_2026_05_08`](../archive/2026_05/deployment_ui_lifecycle_tabs_2026_05_08.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases A-H shipped (Slots 6+7); H4/G2/G3 DEFERRED-OPERATOR-DECISION (DNS gate) ·
**estimate**: 30 cal AI-days (class: brand-new)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
