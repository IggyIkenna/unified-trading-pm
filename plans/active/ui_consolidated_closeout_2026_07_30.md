---
doc_type: plan
title:
  UI consolidated close-out — deployment-ui / deployment-api / unified-trading-system-ui, launched as its own tranche
summary: >-
  New "topic tranche" (10th sibling to the 5 asset groups + cross-cutting + ao + ci + infra) for deployment-ui,
  deployment-api, and unified-trading-system-ui work — the operator surfaced that UI work had no dedicated tracker the
  way cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra each do (`ui` was previously invisible to
  `/ag-closeout-audit` and `/plan-reconcile`'s topic-scoped shards, only reachable via the
  `deployment_and_user_management_master` EPIC — which neither skill audits: epics live in `plans/epics/`, outside Phase
  0's `plans/active/<ag>_consolidated_closeout_*.md` discovery pattern, and aren't part of the asset_group partition at
  all). `ui` is added 2026-07-30 as a genuine 11th `asset_group` enum value (full parity with the 2026-07-27
  `ao`/`ci`/`infrastructure` expansion, not a cheaper `infrastructure`-tag workaround) — see
  `docspec.py`/`PLAN_FORMAT.md`/`doc-frontmatter-schema.md` §5 and both skills' tranche lists. 17 active docs discovered
  + retagged this session as the initial member set (bounded discovery — a full corpus-wide retag audit, mirroring
  `asset_group_ao_ci_infra_schema_expansion_2026_07_27.md`, is still owed and tracked below).
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [deployment-ui, deployment-api, unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, deployment-ui, deployment-api, close-out, consolidation, observability, tranche-launch]
related:
  [
    /plans/epics/deployment_and_user_management_master.md,
    /plans/epics/observability_master.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_07/deployment_ui_observability_ux_tracker_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: ui_developer
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator-driven session 2026-07-30 — asked why UI work had no consolidated-closeout tracker like the other 9 tranches;
  confirmed the `deployment_and_user_management_master` epic (though real and current, refreshed same session) is
  invisible to `/ag-closeout-audit`/`/plan-reconcile`'s tranche mechanism by construction; operator ruled full parity
  (new `asset_group: ui` enum value + skill wiring), not the cheaper `infrastructure`-tag route.
context_scope:
  [
    /plans/epics/deployment_and_user_management_master.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/03-deployment/data-status-ui-surface.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# UI consolidated close-out

> **Purpose.** One place to see all deployment-ui / deployment-api / unified-trading-system-ui work — the tenth topic
> tranche, sibling to the 5 asset groups + cross-cutting + ao + ci + infra. This plan **references** the source docs; it
> does not duplicate their content. `parent_epic: deployment_and_user_management_master` (the real, current epic that
> owns this same repo scope — refreshed 2026-07-30, see its own Progress Log) is a secondary hint only;
> `asset_group: [ui]` on each member doc is the primary signal `/ag-closeout-audit ui` and scoped `/plan-reconcile ui`
> runs will use.

## Reachability map

1. **Data-status page/tab** (deployment-ui + deployment-api, instruments/manifest-backed) → Track 1
2. **Deployment registry + Deployments tab health** → Track 2
3. **Observability surfaces** (Cost / Artifacts / Consolidators / Alerts pages) → Track 3
4. **Nav / smoke-test / mock-parity hygiene** → Track 4

## Track 1 — Data-status page/tab · P1

**Sources**:
[data_status_tab_and_downloads_remediation_2026_06_16.md](/plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md)
(data-status tab UI bugs + instruments CSV download regressions, gated on v9 manifest migration) ·
[data_status_page_ux_and_canonicalisation_2026_07_16.md](/plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md)
(honest-coverage fix shipped + P2-P8 UX/canonicalisation follow-ups) ·
[data_status_catalogue_true_source_phase2_2026_07_24.md](/plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md)
(Phase 2 true-catalogue/expected-universe source for the catalogue explorer) ·
[data_status_cell_grid_rearchitecture_2026_07_18.md](/plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md)
(bound/stream/precompute the full-history manifest cell-grid — root-causing the repeated deployment-api OOMs).

**Close-out criterion**: data-status tab download regressions fixed; honest-coverage P2-P8 follow-ups shipped; the
true-catalogue Phase 2 source lands; the cell-grid re-architecture ships so full-history renders without OOM.

## Track 2 — Deployment registry + Deployments tab health · P1

**Sources**:
[deployment_registry_firestore_migration_2026_07_14.md](/plans/active/deployment_registry_firestore_migration_2026_07_14.md)
(OVERVIEW — GCS-object-per-VM → Firestore migration; the phase index) ·
[deployment_registry_firestore_p3_cutover_2026_07_14.md](/plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md)
(Phase 3 — cutover to Firestore-only + decommission the GCS registry) ·
[deployment_registry_firestore_p5_verify_2026_07_14.md](/plans/active/deployment_registry_firestore_p5_verify_2026_07_14.md)
(Phase 5 — verify at scale + codex SSOT update) ·
[issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md](/plans/active/issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md)
(the D.3 health-alert gate only fires as a side effect of someone having the Deployments tab open — no dedicated Cloud
Scheduler cron).

**Close-out criterion**: Firestore cutover (Phase 3) + at-scale verification (Phase 5) both land; the health-alert gate
gets an independent polling schedule, not just dashboard-open-triggered.

## Track 3 — Observability surfaces (Cost / Artifacts / Consolidators / Alerts) · P1

**Sources**:
[artifact_pipeline_observability_2026_07_17.md](/plans/active/artifact_pipeline_observability_2026_07_17.md) (the
`/artifacts` page — build→artifact→deploy lineage across both clouds; mock-first done, real API+UI wiring in progress) ·
[consolidator_throughput_backlog_monitor_2026_07_09.md](/plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md)
(Consolidators cockpit tab — per-AG backlog + throughput monitor) ·
[issues/cost_observability_deferred_followups_2026_07_10.md](/plans/active/issues/cost_observability_deferred_followups_2026_07_10.md)
(the `/costs` page's own deferred P3 backlog, migrated at plan archival) ·
[issues/alerts_endpoint_per_object_gcs_read_performance_2026_07_23.md](/plans/active/issues/alerts_endpoint_per_object_gcs_read_performance_2026_07_23.md)
(`/api/alerts` N+1 GCS-read performance bug — 2 stopgaps shipped, root cause per-object read pattern still open).

**Also see (already resolved, historical — not live Sources)**: the
[deployment-ui observability & UX tracker](/plans/archive/2026_07/deployment_ui_observability_ux_tracker_2026_07_17.md)
and its 7 split children (cost/day accuracy, date-range filter+search, VM log viewer, alerts ingestion+rebuild, durable
operational data, Fleet-tab consolidation) — all archived complete 2026-07-20→28, `parent_epic: observability_master` (a
distinct epic from this tranche's `deployment_and_user_management_master`, both real and both covering overlapping
deployment-ui/deployment-api ground; no action needed, cited for continuity).

**Close-out criterion**: the `/artifacts` page's real API+UI wiring ships; the Consolidators tab's v2
truthful-throughput histogram lands (or stays intentionally descoped per its own doc); the Cost Observability deferred
followups triaged; the alerts N+1 read pattern fixed at the root, not just the two stopgaps.

## Track 4 — Nav / smoke-test / mock-parity hygiene · P1

**Sources**:
[issues/deployment_ui_nav_consolidation_2026_07_17.md](/plans/active/issues/deployment_ui_nav_consolidation_2026_07_17.md)
(4 nav surfaces → 2, shipped; 7 duplicate routes + a dropdown-vs-bar call remain operator-owned) ·
[issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md](/plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md)
(RESOLVED 2026-07-31 — the `pw:L2 ✓` gate was RED on LDR from host-contention false positives, not real app drift; fixed
via `playwright.config.ts` `workers: 1`, gate now 424/0 green, archived) ·
[issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md](/plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md)
(8 pre-existing smoke failures — Daily Costs page, mobile nav hamburger, nav-menu-dedup; **retagged here from
`infrastructure` 2026-07-30 — was previously cited in `infra_consolidated_closeout_2026_07_25.md` Track 4, now this
tranche's home instead**) ·
[issues/deployment_api_live_mock_parity_2026_07_17.md](/plans/active/issues/deployment_api_live_mock_parity_2026_07_17.md)
(mock mode has drifted from live on 12 of 111 endpoints, incl. an empty coverage-summary — directly relevant to this
session's own local-dev live-vs-mock confusion) ·
[issues/deployment_api_sigabrt_crash_loop_2026_07_24.md](/plans/active/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md)
(deployment-api container SIGABRT roughly every 20-40 min, undiagnosed, compounding the reaper-drain P0).

**Close-out criterion**: the operator nav-surface decisions (dropdown-vs-bar, the 7 duplicate routes) made; the
smoke-gate failures fixed with `pw:L2 ✓` regression specs; mock/live contract parity restored on all 12 drifted
endpoints; the SIGABRT crash-loop root-caused and fixed.

## Codex SSOTs (read before touching a track)

`/codex/05-infrastructure/deployment-observability.md`, `/codex/03-deployment/data-status-ui-surface.md`,
`/codex/06-coding-standards/ui-testing-layers.md`, `/codex/11-project-management/`.

## Todos

> Verification-only — measures whether the tranche is actually done, not new work to dispatch (`assigned_vm: NA`, not
> itself AO-eligible), same convention as `infra_consolidated_closeout_2026_07_25.md`'s own Todos section.

- [ ] [REVIEW] P1. Track 1 close-out: data-status tab/download regressions fixed; honest-coverage P2-P8 shipped; true-
      catalogue Phase 2 lands; cell-grid re-architecture ships (no full-history OOM).
- [ ] [REVIEW] P1. Track 2 close-out: Firestore registry cutover (Phase 3) + at-scale verification (Phase 5) land; the
      health-alert gate gets an independent poll schedule.
- [ ] [REVIEW] P1. Track 3 close-out: `/artifacts` real API+UI wiring ships; Consolidators v2 histogram lands or stays a
      documented descope; Cost Observability deferred followups triaged; alerts N+1 read pattern fixed at root.
- [ ] [REVIEW] P1. Track 4 close-out: nav-surface operator decisions made; smoke-gate failures fixed with `pw:L2 ✓`
      evidence; mock/live parity restored on all 12 drifted endpoints; SIGABRT crash-loop root-caused.
- [ ] [REVIEW] P2. **Corpus-wide `ui` retag audit still owed** — this session's 17-doc retag was a bounded discovery
      pass (repos:-grep + content spot-check), not an exhaustive sweep. Mirror
      `asset_group_ao_ci_infra_schema_expansion_2026_07_27.md`'s methodology: grep the full corpus for
      `infrastructure`/`cross-cutting`/`meta`-tagged docs whose real content is deployment-ui/deployment-api/
      unified-trading-system-ui-primary (candidates already spotted but deliberately deferred this session:
      `monitoring_control_plane_master_2026_06_10.md` and `ui_build_warm_cache_2026_06_17.md` — both currently `ci`,
      genuinely borderline CI-vs-UI scope, need a real per-doc read before retagging either way), retag with the same
      evidence-cited convention, and re-run `check_ag_closeout_linkage.py` + `check_frontmatter_schema.py` after. Done
      when: `/ag-closeout-audit ui`'s own Phase 0.3 discovery count stops changing between two consecutive runs a week
      apart.
- [ ] [INFRA] P2. First `/ag-closeout-audit ui` + `/plan-reconcile ui` runs, scoped to this tranche — establishes the
      real orphan-projection baseline (this tracker's own todos above are a manual first pass, not a substitute for the
      skill's per-doc Phase 1 judgment) and drafts `ui_satellite_ao_dispatch_batch1_<date>.md` if warranted.

## Progress Log

- **2026-07-30** — Tranche launched. Operator asked whether the existing `deployment_and_user_management_master` epic
  could serve as the UI tracker the other 9 tranches have; audited it first (found genuinely stale — 5 of 12 listed
  "active" plans had already archived without the epic being updated, refreshed via
  `populate_epic_bodies_2026_05_21.py --apply`, `unified-trading-pm@63138c058`) but confirmed by reading
  `ag-closeout-audit`/`plan-reconcile`/`docs-reconcile`'s own SKILL.md files that none of the three would ever audit an
  epic doc as a tranche tracker: `ag-closeout-audit` hardcodes discovery to
  `plans/active/<ag>_consolidated_closeout_*.md` and the asset_group enum (never `plans/epics/`); `plan-reconcile`'s
  topic-scoped shards use the identical partition (only its unscoped `all` run touches epics, and only for generic
  checkbox-sync, not completeness projection); `docs-reconcile` is out of scope for plan/epic lifecycle entirely.
  Operator ruled full parity — add `ui` as a genuine 11th `asset_group` enum value (mirroring the 2026-07-27
  `ao`/`ci`/`infrastructure` expansion), not the cheaper `infrastructure`-tag route. Schema changes:
  `docspec.py`/`PLAN_FORMAT.md`/`doc-frontmatter-schema.md` §5 (10→11 values); skill wiring:
  `ag-closeout-audit/SKILL.md` (9→10 tranches throughout, new `ui` classification-mechanism paragraph) and
  `plan-reconcile/SKILL.md` (9→10 tranches, corrected the sibling ao/ci/infrastructure description which had gone stale
  describing the pre-2026-07-27 workaround); helper scripts `generate_ag_closeout_audit_candidates.py` +
  `generate_na_doc_tranche_inventory.py`'s `NON_AG_TRANCHES` both extended. Seeded this tranche with 17 active docs (9
  plans + 8 issues) discovered via a `repos:`-grep across `plans/active/{*.md,issues/*.md}` for
  `deployment-ui`/`deployment-api`, filtered by real content read (not just the grep hit) to exclude docs where those
  repos are incidental (e.g. broad data-pipeline docs merely touching deployment-api peripherally) — each retag cites
  its evidence inline on the frontmatter line. Two borderline docs (`monitoring_control_plane_master`,
  `ui_build_warm_cache`) were deliberately left un-retagged pending a real per-doc read, tracked as a todo above rather
  than guessed. `infra_consolidated_closeout_2026_07_25.md`'s Track 4 still cites 2 of the retagged docs
  (`deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md`, `artifact_pipeline_observability_2026_07_17.md`)
  — left as-is, a legitimate cross-tranche mention (same pattern every other tranche's Sources list uses for docs it
  doesn't primarily own), not a dangling reference.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
