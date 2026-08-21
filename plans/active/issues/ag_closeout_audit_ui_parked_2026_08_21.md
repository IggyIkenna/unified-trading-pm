---
doc_type: issue
title: ag-closeout-audit ui 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit ui tranche Phase 1 audit (1 batch, 17 candidate docs). Compact orphan table.
status: open
nature: issue
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, ui, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/ui_consolidated_closeout_2026_07_30.md]
created: 2026-08-21
author: claude-session-2026-08-21
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: human
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: ["2026-08-21 — /ag-closeout-audit ui, 1 Phase-1 batch, 17 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit ui 2026-08-21

17 candidates, 1 batch (`ui` is the newest tranche, added 2026-07-30 — corpus-wide retag pass still owed). Counts:
archivable_now 2 · archivable_after_planned_work 3 · orphaned_partial_coverage 1 · orphaned_never_touched 11 ·
exclude_cross_cutting 0.

## Orphaned — compact table

| Doc | Taxonomy |
|---|---|
| `artifact_pipeline_observability_2026_07_17.md` | misattributed-VM-origin fix covered by batch3; 2 other items non-dispatchable/sequencing-blocked |
| `consolidator_throughput_backlog_monitor_2026_07_09.md` | 2 REVIEW deploy-gate closers, deferred to unnamed milestone |
| `data_status_tab_and_downloads_remediation_2026_06_16.md` | DeFi phantom-row audit + APPLY-GATE sign-off, gated on a still-open 2026-08-07 operator HOLD |
| `deployment_registry_firestore_p3_cutover_2026_07_14.md` | **carried finding, 7 re-confirmations since 2026-07-30** — see cross-tranche big findings item 15 |
| `deployment_registry_firestore_p5_verify_2026_07_14.md` (draft) | correctly gated behind P3 |
| `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` | dead e2e fixture ID + generator/UI structural-skew investigation |
| `issues/cost_observability_deferred_followups_2026_07_10.md` | business-context enrichment, 176 launcher scripts, only ~9 through choke point — recommend piggyback on infra tranche |
| `issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md` | **carried finding, 6 consecutive passes; also a declared-but-unwired instance** — see cross-tranche big findings item 14 |
| `issues/plan_reconciler_findings_ui_2026_08_10.md` | scope 3 orphaned Firestore-migration successors + undefined soak-window duration |
| `issues/plan_reconciler_findings_ui_2026_08_18.md` | context-scout script bug + P0-finalize dispatch-inactivity check |
| `issues/plan_reconciler_findings_ui_2026_08_19.md` | run killed 18min in by the AO singleton-dedup bug — re-run needed |
| `issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` | provision Firebase Admin credential/emulator + re-run gated e2e |

## Mechanical hygiene flags

- Covering-set completeness gap: `deployment_api_true_catalogue_expected_universe_projection_ao_dispatch_2026_08_16.md`
  (+finalize) is real active coverage for `data_status_catalogue_true_source_phase2_2026_07_24.md` but is absent
  from the ui tranche's `covering_paths` — likely a symptom of the still-owed corpus-wide retag pass.
- Context-scout script bug (missing `- ` bullet marker on 2026-08-17-dated Progress Log entries) confirmed across
  ≥4 docs in this corpus — filed but unfixed, root cause outside `plans/**`.
- `deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md`: zero dispatch activity for 9+ days despite its
  `depends_on` gate being satisfied since 2026-08-10/11 — flagged repeatedly, never resolved.
- Confirmed load-bearing context (not this tranche's own finding): `plan_reconciler` is treated as a system-wide
  singleton by AO's `reap_orphan_agents()` dedup, which killed 2 of 3 concurrently-running tranche-sharded
  `plan_reconciler` workers mid-task on 2026-08-19 — the exact bug this session fixed earlier today
  (`agent-orchestrator@e8d83540`, see `ao_singleton_agent_kind_dedup_kills_concurrent_tranche_workers_2026_08_20.md`).

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit ui Phase-1 sweep (1 batch). No
  mechanical fixes applied yet.
