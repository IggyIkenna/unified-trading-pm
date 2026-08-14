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
last_updated: "2026-08-09"
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: ui_developer
effort: xhigh
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
    /codex/05-infrastructure/deployment-observability.md,
    /codex/03-deployment/data-status-ui-surface.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/11-project-management/,
    /plans/epics/deployment_and_user_management_master.md,
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
[data_status_page_ux_and_canonicalisation_2026_07_16.md](/plans/archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md)
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
Scheduler cron) ·
[issues/deployment_api_prod_disable_auth_true_2026_08_06.md](/plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md)
(retagged from `cross-cutting` → `ui` 2026-08-10 by `meta_plan_corpus_hygiene_ao_dispatch_batch1` todo 1 — live
unauthenticated-prod exposure on `uts-shared-deployment-api`, all 4 fix-steps escalated to
`deployment_api_unauthenticated_prod_p0_2026_08_10.md`).

**Close-out criterion**: Firestore cutover (Phase 3) + at-scale verification (Phase 5) both land; the health-alert gate
gets an independent polling schedule, not just dashboard-open-triggered.

## Track 3 — Observability surfaces (Cost / Artifacts / Consolidators / Alerts) · P1

**Sources**:
[artifact_pipeline_observability_2026_07_17.md](/plans/active/artifact_pipeline_observability_2026_07_17.md) (the
`/artifacts` page — build→artifact→deploy lineage across both clouds; mock-first done, real API+UI wiring in progress) ·
[consolidator_throughput_backlog_monitor_2026_07_09.md](/plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md)
(Consolidators cockpit tab — per-AG backlog + throughput monitor) ·
[issues/cost_observability_deferred_followups_2026_07_10.md](/plans/active/issues/cost_observability_deferred_followups_2026_07_10.md)
(the `/costs` page's own deferred P3 backlog, migrated at plan archival) · **Also see (already resolved, historical —
not live Sources)**:
[issues/alerts_endpoint_per_object_gcs_read_performance_2026_07_23.md](/plans/archive/issues/alerts_endpoint_per_object_gcs_read_performance_2026_07_23.md)
(`/api/alerts` N+1 GCS-read performance bug — reader-side fix shipped live `deployment-api@79a1d36`, remaining
writer-side batching WONT-DO'd 2026-08-01 as cost/list-latency not correctness) · the
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
[issues/deployment_ui_nav_consolidation_2026_07_17.md](/plans/archive/issues/deployment_ui_nav_consolidation_2026_07_17.md)
(RESOLVED + ARCHIVED 2026-08-01 — all 5 todos shipped: 4 nav surfaces → 2, dropdown-vs-bar ruled, 7 duplicate routes
resolved via retiring `?tab=`, 3 dead pages deleted, real 404 added, per-service shell moved onto real routes) ·
[issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md](/plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md)
(RESOLVED 2026-07-31 — the `pw:L2 ✓` gate was RED on LDR from host-contention false positives, not real app drift; fixed
via `playwright.config.ts` `workers: 1`, gate now 424/0 green, archived) ·
[issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md](/plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md)
(8 pre-existing smoke failures — Daily Costs page, mobile nav hamburger, nav-menu-dedup; **retagged here from
`infrastructure` 2026-07-30 — was previously cited in `infra_consolidated_closeout_2026_07_25.md` Track 4, now this
tranche's home instead; RESOLVED + ARCHIVED 2026-08-10**) ·
[issues/deployment_api_live_mock_parity_2026_07_17.md](/plans/archive/issues/deployment_api_live_mock_parity_2026_07_17.md)
(mock mode has drifted from live on 12 of 111 endpoints, incl. an empty coverage-summary — directly relevant to this
session's own local-dev live-vs-mock confusion) ·
[issues/deployment_api_sigabrt_crash_loop_2026_07_24.md](/plans/archive/2026_08/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md)
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
      **Deferred-item cross-reference (added 2026-08-10, batch2 archival):** the still-open business-context-enrichment
      item from `cost_observability_deferred_followups_2026_07_10.md` item 1 (asset_group launcher labeling + AWS
      cost-allocation tags) remains STILL-BLOCKED (not a bounded batch todo) and is NOT covered by any active satellite
      batch. It is tracked as an open `- [ ]` in the source doc + as the standing follow-up todo in
      `issues/vm_launcher_setup_script_freshness_gap_2026_07_31.md`; per the batch-2 Deferred analysis it should
      piggyback on the infra-tranche's `lc_gcloud_create` migration, not fork a parallel effort. A future ui-tranche
      audit must re-measure the infra migration's progress before re-assessing bounded-ness (see
      `/plans/archive/2026_08/ui_satellite_ao_dispatch_batch2_2026_08_08.md`).
- [ ] [REVIEW] P1. Track 4 close-out: nav-surface operator decisions made; smoke-gate failures fixed with `pw:L2 ✓`
      evidence; mock/live parity restored on all 12 drifted endpoints; SIGABRT crash-loop root-caused.
- [ ] [REVIEW] P2. **Corpus-wide `ui` retag audit still owed** — this session's 17-doc retag was a bounded discovery
      pass (repos:-grep + content spot-check), not an exhaustive sweep. Mirror
      `asset_group_ao_ci_infra_schema_expansion_2026_07_27.md`'s methodology: grep the full corpus for
      `infrastructure`/`cross-cutting`/`meta`-tagged docs whose real content is deployment-ui/deployment-api/
      unified-trading-system-ui-primary (candidates already spotted but deliberately deferred:
      `monitoring_control_plane_master_2026_06_10.md` and `ui_build_warm_cache_2026_06_17.md` — both currently `ci`,
      genuinely borderline CI-vs-UI scope; PLUS 2 more found 2026-08-07 by the `ag_closeout_auditor` run —
      `issues/deployment_api_prod_disable_auth_true_2026_08_06.md` (currently `cross-cutting`; content read in full, is
      100% deployment-api-specific, ownership only ambiguous because it also touches the shared
      `unified-trading-library` config surface) and
      `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` (currently `defi`, corroborated by the
      `defi`-tranche's own 2026-08-07 audit finding, not independently re-verified here) — all 4 need a real per-doc
      read before retagging either way, see `issues/ag_closeout_audit_ui_parked_2026_08_07.md` for the 2 newest
      candidates' evidence), retag with the same evidence-cited convention, and re-run `check_ag_closeout_linkage.py` +
      `check_frontmatter_schema.py` after. Done when: `/ag-closeout-audit ui`'s own Phase 0.3 discovery count stops
      changing between two consecutive runs a week apart.
- [x] ✅ [INFRA] P2. First `/ag-closeout-audit ui` + `/plan-reconcile ui` runs, scoped to this tranche — establishes the
      real orphan-projection baseline (this tracker's own todos above are a manual first pass, not a substitute for the
      skill's per-doc Phase 1 judgment) and drafts `ui_satellite_ao_dispatch_batch1_<date>.md` if warranted. — **DONE,
      verified by plan_reconciler 2026-08-10 (dispatch `agt-ec1688`).** `/ag-closeout-audit ui` has now run 4×
      (2026-08-06/07/08/09, all cited above) and drafted batch1. `/plan-reconcile ui` has now run 2× — a first pass
      2026-08-07 (dispatch `agt-a40e5f`, `plans/archive/2026_08/issues/plan_reconciler_findings_2026_08_07.md`) that
      applied zero fixes (grace/lock blocked everything that run) but DID establish the coverage baseline this todo asks
      for, and this 2026-08-10 pass (`plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md`), which applied ~20
      fixes across 10 files. **Correction to several prior Progress Log entries below** (2026-08-07 through 08-09, from
      `ag_closeout_auditor`/`na-eligibility-audit`): those entries state "`/plan-reconcile ui` has still never run" /
      "genuinely has not run yet" — this was factually incorrect from 2026-08-07 onward, contradicted by that same day's
      own `plan_reconciler_findings_2026_08_07.md` (dispatch `agt-a40e5f`, with a full coverage report). Not editing
      those past entries (historical record of what was believed at the time); recording the correction here instead,
      per this workspace's append-don't-replace convention for shared docs.

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
- **context-scout 2026-08-03**: re-verified context_scope (6 entries, all resolving, matches the doc's own "Codex SSOTs"
  list + epic + skill) — coordination-index doc, legitimately code-free; no changes needed.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-06 (ui tranche, dispatch agt-2cd17a)**: KEEP-NA, valid — this is the tranche's own
  consolidated-closeout coordinator; its 5 open `[REVIEW]` todos are explicitly self-declared verification-only / "not
  itself AO-eligible" (same convention as the sibling `infra_consolidated_closeout` doc), matching the bounded-outcome
  bar this skill applies. No reclassification warranted.
- **ag_closeout_auditor 2026-08-06 (ui tranche, dispatch agt-8d6508)**: first-ever `/ag-closeout-audit ui` run — the
  `/ag-closeout-audit` half of the P2 todo above (`/plan-reconcile ui` has NOT run yet, so that todo stays unchecked).
  Phase 1 (12-agent Workflow) classified all 12 tranche-primary docs: 1 `archivable_now`
  (`issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` — fully done, but stuck at a stale
  `status: open` + a `locked_by` timestamp that predates its own `created` date by 2 months; flagged, not fixed here), 2
  `archivable_after_planned_work` (`deployment_registry_firestore_migration_2026_07_14.md`, self-covered by its own
  named P3/P5 phase docs; `issues/deployment_api_sigabrt_crash_loop_2026_07_24.md`, self-dispatched), 9
  `orphaned_never_touched`, 0 partial-coverage, 0 mistags (Orthogonality HARD CHECK clean — all 12 candidates cleanly
  single-tagged `[ui]`). Drafted `ui_satellite_ao_dispatch_batch1_2026_08_06.md` (status: draft, 3 conflict-cleared
  todos) + gated `_finalize`, `unified-trading-pm@a9a85a1cc` — pending operator approval to dispatch. Also found: the
  Track 3/Track 4 close-out criteria above are now partly stale (both still describe already-resolved sub-items — alerts
  N+1, mock/live parity — as open; a future edit should trim them) and the P2 corpus-wide-retag-audit todo above remains
  genuinely untouched (`monitoring_control_plane_master`, `ui_build_warm_cache` still un-triaged). Full reasoning per
  doc: see the batch plan's own Deferred/Findings sections.
- **ag_closeout_auditor 2026-08-07 (ui tranche, dispatch agt-eb521b)**: second `/ag-closeout-audit ui` run. Candidate
  set unchanged (12 docs). Orphan count unchanged at 9 of 12, but composition shifted:
  `data_status_cell_grid_rearchitecture_2026_07_18.md` and `artifact_pipeline_observability_2026_07_17.md` moved
  `orphaned_never_touched` → `orphaned_partial_coverage` (batch1 didn't exist at 2026-08-06's discovery time; today it
  does, and its 3 Todos cite specific items in both — expected drift, not a regression). Corrected a stale todo directly
  in `ui_satellite_ao_dispatch_batch1_2026_08_06.md` (still draft, unshipped — its Todo 2 would have filed a duplicate
  issue doc; redirected to reconciling the source doc's already-stale checkbox instead). 2 more plausible `ui`-mistag
  candidates found (folded into the same corpus-wide-retag todo above, not retagged yet). No batch2 drafted — zero of
  batch1's 11 Deferred items cleared in the 1 day since (verified via git log on all 12 candidate docs); recommend
  approving + dispatching batch1 next, which is still `status: draft` awaiting operator sign-off. Full write-up:
  `issues/ag_closeout_audit_ui_parked_2026_08_07.md`.
- **context-scout 2026-08-07**: re-verified context_scope (6 entries, unchanged) — still a coordination-index doc,
  legitimately code-free; the 2 intervening `ag_closeout_auditor` Progress Log entries are audit-run records, not a
  substantive change to this doc's own reading list (the new satellite batch1/finalize + parked-issue docs they produced
  are the CHILD batch's own reading list, not this umbrella's).
- **na-eligibility-audit 2026-08-07 (ui tranche, dispatch agt-61f967)**: KEEP-NA, valid — re-confirmed (in scope this
  run because `last_updated` (2026-08-07) is newer than the prior 2026-08-06 marker, per the 2 same-day
  `ag_closeout_auditor` Progress Log entries above). Todos 1-4 (Track close-out verification) remain self-declared
  verification-only rollups against work tracked in other docs, not AO-eligible. Todo 5 (corpus-wide `ui` retag audit)
  still requires genuine per-doc judgment, not mechanical retagging — the 2 candidates added 2026-08-07
  (`deployment_api_prod_disable_auth_true_2026_08_06.md`,
  `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`) both need a cross-tranche-ownership call
  (shared-config-surface / same-day sibling-tranche corroboration) a mechanical worker can't resolve alone. Todo 6 is
  accurately self-tracked as partially done (`/ag-closeout-audit ui` has now run twice, 08-06/08-07;
  `/plan-reconcile ui` genuinely has not run yet) — correctly still unchecked, not stale. No reclassification, no
  citation fix, no archival warranted.
- **ag_closeout_auditor 2026-08-08 (ui tranche, dispatch agt-a0f1b7, slot 11)**: third `/ag-closeout-audit ui` run.
  Candidate set grew 12→13 (new member: 2026-08-07's own parked-findings doc, self-classified
  `archivable_after_planned_work` — its recommendations already fully folded into this doc's P2 todo #5 and batch1's
  standing approval gate). Orphan count 9 of 13 (flat vs 2026-08-07's 9 of 12 in raw count; the +1 denominator landed
  non-orphaned, so the tranche's orphan rate improved slightly). A 2026-08-07 operator-rulings commit
  (`unified-trading-pm@f9672e180`) closed 2 items relevant to this tranche:
  `artifact_pipeline_observability_2026_07_17.md`'s Phase 7 investigation (fully resolved, confirmed live) and both of
  `cost_observability_deferred_followups_2026_07_10.md`'s operator-gated items (AWS CUR backfill closed final;
  business-context/asset_group enrichment ruled to proceed). Per this skill's own taxonomy a ruled item "becomes a
  normal batch candidate," but a dedicated scoping check found the enrichment item is NOT safely bounded as one AO todo
  (176 VM launcher scripts, only ~9 through the shared label-injection choke point, a directly-analogous 2026-08-06
  operator ruling on a sibling infra-tranche issue already declined to treat a near-identical file count as one todo) —
  deferred with full evidence rather than drafted blind. Drafted
  `/plans/archive/2026_08/ui_satellite_ao_dispatch_batch2_2026_08_08.md` (1 conflict-cleared todo: the source doc's
  other 4 "unscheduled P3" items, combined per the same-file concurrency rule) + gated finalize — pending operator
  approval, independent of batch1. Also found: `artifact_pipeline_observability_2026_07_17.md` carries an 11th
  genuinely-open item (a prose-only "Still open" sentence trailing an `[x]`-checked parent bullet, line 683) that 2
  prior audit passes and the doc's own na-eligibility-audit pass all missed — not fixed here (outside this skill's
  write-scope for a non-covering candidate doc), flagged for na-eligibility-audit's next pass. **Batch1 is still
  `status: draft`, unapproved, 3 audit runs (08-06/07/08) without operator action** — remains the top recommendation.
  Full write-up: `issues/ag_closeout_audit_ui_parked_2026_08_08.md`.
- **na-eligibility-audit 2026-08-08 (ui tranche)**: KEEP-NA, valid — re-confirmed; only change since the 2026-08-07
  marker is today's `ag_closeout_auditor` Progress Log entry (informational, no todo-content edit). Todos 1-4 remain
  self-declared verification-only rollups against work tracked elsewhere. Todo 5 (corpus-wide retag) still needs genuine
  per-doc judgment on the same 2 cross-tranche-ownership candidates. Todo 6 correctly still unchecked:
  `/ag-closeout- audit ui` has now run 3 times (08-06/07/08) but `/plan-reconcile ui` has still never run on this
  tranche. No reclassification, no citation fix, no archival warranted.
- **ui_satellite_ao_dispatch_batch1_finalize's own todo 3, 2026-08-08 (slot 7)**: a scoped re-measure (not a full
  standalone `/ag-closeout-audit ui` cron pass) run as part of batch1's finalize ritual, after batch1's 3 todos landed
  and batch2 was approved. Candidate set re-derived fresh at **14** (the 12 from the 08-08 `agt-a0f1b7` run plus the
  `..._parked_2026_08_08.md` doc that run itself produced, now itself a candidate). Result: **8 orphaned of 14** (down
  from the 2026-08-06 baseline of 9/12) — `data_status_tab_and_downloads_remediation_2026_06_16.md` moved to
  `archivable_after_planned_work` (batch1_finalize's todo 2 closer-read + its still-open todo 4's migration commitment).
  The other 8 baseline-orphaned docs are unchanged, each with a stated operator-gated/time-gated/too-large reason — full
  per-doc breakdown lives in `ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md`'s own todo 3 completion note, not
  duplicated here. `check_ag_closeout_linkage.py` reconfirmed 0 `ui`-tagged orphans.
- **ag_closeout_auditor 2026-08-09 (ui tranche, dispatch agt-db95b9, slot 24)**: fourth full `/ag-closeout-audit ui`
  run. Candidate set unchanged at 14 (cross-checked via `generate_ag_closeout_audit_candidates.py` + an independent
  manual frontmatter scan). Fresh 14-agent Phase-1 Workflow re-derived every verdict independently (not copied forward)
  — **result identical to the 2026-08-08 baseline: 8 orphaned of 14, zero verdicts changed.** Phase 3: the one plausible
  extraction candidate (`artifact_pipeline_observability_2026_07_17.md`'s closer-read/scoping session) turned out to
  already be explicitly claimed by `ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md`'s own still-open todo 4 (its
  step 1 commits to standing up exactly that as a named standalone plan) — drafting a competing batch would have
  duplicated an already-active claim, so no batch 3 was drafted. Found one bookkeeping gap (batch1_finalize's own
  candidate-summary line for `data_status_tab_and_downloads_remediation` silently drops 1 of its 6 narratively-CLEARED
  items — the low-priority Rollup-difference-clarity tooltip — flagged for whoever executes todo 4) plus 2
  carried-forward findings with no new information (the 2 mistag candidates for this doc's own P2 todo #5; the still-
  stuck `deployment_ui_smoke_failures` lock, 4th consecutive flag). Full write-up:
  `issues/ag_closeout_audit_ui_parked_2026_08_09.md`. `check_ag_closeout_linkage.py` reconfirmed 0 `ui`-tagged orphans
  (10 total corpus orphans, all `ao`/`cross-cutting`/`defi`, baseline 49).
- **na-eligibility-audit 2026-08-09 (ui tranche, dispatch agt-eee16e)**: KEEP-NA, valid — re-confirmed; only change
  since the 2026-08-08 marker is today's `ag_closeout_auditor` Progress Log entry (informational — 4th
  `/ag-closeout-audit ui` run, 8/14 orphaned unchanged, zero verdicts changed, no todo-content edit). Todos 1-4 remain
  self-declared verification-only rollups against work tracked in other docs. Todo 5 (corpus-wide retag) still needs
  genuine per-doc judgment on the same cross-tranche-ownership candidates (unchanged since 2026-08-07). Todo 6 correctly
  still unchecked: `/ag-closeout-audit ui` has now run 4 times (08-06/07/08/09) but `/plan-reconcile ui` has still never
  run on this tranche. No reclassification, no citation fix, no archival warranted.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **plan_reconciler 2026-08-10 (ui tranche, dispatch `agt-ec1688`)**: second `/plan-reconcile ui` run (first was
  2026-08-07, `agt-a40e5f` — zero fixes applied that run due to grace/lock, but it DID read + baseline the tranche,
  contradicting the "still never run" framing several entries above repeated through 2026-08-09; not editing those past
  entries, see Todo 6's own correction note above). This run: 5-hunter fan-out + adversarial self-verification, ~20
  fixes applied across 10 files (missed-flips, stale frontmatter/body contradictions, prosewrap-padding hygiene, 6 codex
  dangling-refs, 2 missing sequential gates, stale batch-naming). Flipped Todo 6 above. New corpus-wide finding:
  `locked_by: live-defi-rollout` (incl. on THIS epic's own child `deployment_ui_smoke_failures` doc) traced to a
  hardcoded placeholder script default, not a real lock — filed
  `issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md`, asked via `/blocked`. 4 items routed to
  the operator (delete-autonomy contradiction, the locked_by ruling, 2 codex-drift items needing new prose / cross-doc
  scope). Full write-up: `issues/plan_reconciler_findings_ui_2026_08_10.md`.
