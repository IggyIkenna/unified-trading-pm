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
assigned_vm:
  NA # corrected 2026-08-10 (plan_reconciler, cross-cutting tranche, generalising the 2026-08-02/06 § 2e
  # ruling already applied to agent_operating_framework_master/orchestrator_master/plan_hygiene_master);
  # PLAN_FORMAT.md:211 -- NA is the expected value on every current epic, a legacy vm-<id> is optional-historical only.
  # (was: vm-operator-ops)
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../active/data_status_catalogue_true_source_phase2_2026_07_24.md
  - ../active/data_status_cell_grid_rearchitecture_2026_07_18.md
  - ../active/data_status_tab_and_downloads_remediation_2026_06_16.md
  - ../active/github_actions_operator_gated_followups_2026_07_17.md
  - ../active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md
  - ../active/sports_prediction_mvp_writetime_precompute_2026_07_24.md
  - ../active/test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md
  - ../active/ui_consolidated_closeout_2026_07_30.md
  - ../active/ui_satellite_ao_dispatch_batch1_2026_08_06.md
  - ../active/ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md
  - ../active/ui_satellite_ao_dispatch_batch2_2026_08_08.md
  - ../active/ui_satellite_ao_dispatch_batch2_finalize_2026_08_08.md
last_updated: 2026-07-30
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Deployment And User Management Master

**Owns**: deployment-api + deployment-ui (was: also user-management-service + user-management-ui — dropped 2026-07-12:
both ARCHIVED per `codex/DEPRECATED_UIS_NOTICE.md` + `/codex/05-infrastructure/ui-functionality-requirements.md` ("User
Management | user-management-ui | archived") + CLAUDE.md's system map ("`user-management-ui` ARCHIVED"); no
`user-management-service` repo exists in the workspace. Findings #314/#385, plan-reconciliation
`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling.)

**Status**: populated (was: "stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with
P0/P1/P2/P3 priority blocks listing all assigned active plans." — left in place after fill, corrected 2026-07-25, same
class as batch_live_symmetry_master.md's finding id 311, §A2 B-queue ruling). Body below (UI Verification Contract,
codex SSOT table, 7 active plans in P0-tier blocks) is populated as of `last_updated: 2026-07-30`; this line is no
longer describing an empty stub. **2026-07-30 refresh**: `populate_epic_bodies_2026_05_21.py --apply` found the prior
fill stale — 5 of the 12 listed plans had already been archived
(`deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13`, `deployment_redesign_cherrypicks_2026_07_20`,
`github_actions_ci_cost_reduction_2026_07_15`, `github_actions_cost_reduction_options_analysis_2026_07_15`,
`github_actions_staging_machinery_shutdown_2026_07_24`) but were still shown as active; regenerated to the 7
genuinely-active plans. The epic itself (ownership, UI verification contract, codex SSOTs) is current and usable — only
the plan-list body had drifted.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## UI Verification Contract (HARD RULE — codified 2026-05-23)

All active plans under this epic that touch any UI repo (`deployment-ui`, `unified-trading-system-ui` — was: also
`user-management-ui`, ARCHIVED, see "Owns" note above, corrected 2026-07-12) MUST pass the playwright verification gate
before any todo is ticked ✅ done. Per `plans/PLAN_FORMAT.md` § 9 and `/codex/06-coding-standards/ui-testing-layers.md`
§ "Plan-Level Enforcement":

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

| Doc                                                       | Owns                                                                                                        |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `/codex/08-workflows/deployment-flow.md`                  | Operator promotion path (dev → staging → main + paper → live); full promotion lifecycle                     |
| `/codex/04-architecture/promote-workflow-architecture.md` | Strategy promote path; `MinimalCandidateManifest`; `POST /api/promote/{strategy_id}/{manifest_id}` contract |
| `/codex/04-architecture/batch-live-architecture.md`       | Mode-toggle invariant (batch vs live); same-codepath requirement                                            |
| `/codex/03-deployment/data-status-ui-surface.md`          | Data-status UI honest-coverage surface; deployment-ui freshness display                                     |

## Assigned active plans

_12 active plans declare `parent_epic: deployment_and_user_management_master` in their frontmatter. Workers pick up in
priority order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`data_status_tab_and_downloads_remediation_2026_06_16`](../active/data_status_tab_and_downloads_remediation_2026_06_16.md)

**status**: active · **estimate**: 1.2 cal AI-days (class: refactor) **title**: Data-status tab + instruments download
remediation (deployment-api / deployment-ui / CeFi universe)

### [`github_actions_operator_gated_followups_2026_07_17`](../active/github_actions_operator_gated_followups_2026_07_17.md)

**status**: active · **estimate**: 4 cal AI-days (class: infra) **title**: GitHub Actions CI cost reduction —
operator-gated followups (D2/D3/D4 decisions, verification-pending items)

## P1 — important; post-current-gate

### [`data_status_catalogue_true_source_phase2_2026_07_24`](../active/data_status_catalogue_true_source_phase2_2026_07_24.md)

**status**: active · **estimate**: 1.8 cal AI-days (class: design) **title**: Data-status catalogue explorer — Phase 2
true-catalogue (expected-universe) source

### [`test_impact_fleet_wide_measurement_and_rollout_2026_08_03`](../active/test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: research) **title**: Test-impact / selective execution —
fleet-wide eligibility measurement, then staged rollout

### [`ui_consolidated_closeout_2026_07_30`](../active/ui_consolidated_closeout_2026_07_30.md)

**status**: active · **estimate**: 3.2 cal AI-days (class: infra)

### [`ui_satellite_ao_dispatch_batch1_2026_08_06`](../active/ui_satellite_ao_dispatch_batch1_2026_08_06.md)

**status**: active · **estimate**: 0.9 cal AI-days (class: infra)

### [`ui_satellite_ao_dispatch_batch1_finalize_2026_08_06`](../active/ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md)

**status**: active · **estimate**: 0.5 cal AI-days (class: infra)

## P2 — useful; opportunistic

### [`data_status_cell_grid_rearchitecture_2026_07_18`](../active/data_status_cell_grid_rearchitecture_2026_07_18.md)

**status**: active · **estimate**: 3 cal AI-days (class: design) **title**: Data-status manifest cell-grid
re-architecture — bound / stream / precompute the full-history view

### [`sports_fixtures_browser_single_catalogue_source_2026_07_24`](../active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md)

**status**: active · **estimate**: 0.9 cal AI-days (class: design) **title**: Sports fixtures browser — switch to the
single-file catalogue source (P10-B backend + follow-ups)

### [`sports_prediction_mvp_writetime_precompute_2026_07_24`](../active/sports_prediction_mvp_writetime_precompute_2026_07_24.md)

**status**: active · **estimate**: 0.9 cal AI-days (class: design) **title**: Sports/prediction MVP write-time
precompute — manifest schema v9→10 stamp + historical backfill

### [`ui_satellite_ao_dispatch_batch2_2026_08_08`](../active/ui_satellite_ao_dispatch_batch2_2026_08_08.md)

**status**: active · **estimate**: 1.1 cal AI-days (class: infra)

### [`ui_satellite_ao_dispatch_batch2_finalize_2026_08_08`](../active/ui_satellite_ao_dispatch_batch2_finalize_2026_08_08.md)

**status**: active · **estimate**: 0.4 cal AI-days (class: infra)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
