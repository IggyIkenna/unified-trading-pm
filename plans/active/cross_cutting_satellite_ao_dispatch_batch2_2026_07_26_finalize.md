---
doc_type: plan
title: Cross-cutting satellite AO batch 2 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md — machine-held via depends_on +
  gate_on_depends: true until all 14 todos are done. Reconciles each named source doc's checkboxes independently, then
  re-checks batch 2's own Deferred items (3 conflict-gated, 7 operator-gated, 3 time-gated, 9 needs-own-triage-pass),
  actions the two membership/classification findings this audit raised, and archives the batch via the standard 6-step
  ritual.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cross_cutting_satellite_ao_dispatch_batch2_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit cross-cutting re-invocation 2026-07-26, per task_template.md § 4's finalize-plan-coverage rule —
  every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
---

# Cross-cutting satellite AO batch 2 — finalize

> **Status: draft** — flips to `active` only when its parent batch does. **Machine-gated on
> [`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`](/plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md)**
> (`depends_on` + `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 14 of that plan's
> todos are `done`. `sequential: true` because todo 2 needs todo 1's reconciliation finished, and todo 4 (archival) must
> run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile every named source doc's checkboxes.** Batch 2's 14 todos cite ~22 distinct source
      docs (each todo's text ends with `Source:` / `Sources:`). For each: flip the corresponding checkbox or section,
      citing the batch commit that shipped it — verify the commit actually exists before citing it. Several batch-2
      todos flip a source checkbox as **already-landed with re-verification evidence rather than newly-shipped** (the
      dp-audit image-default and `--reclassify-apply` terraform halves, the alerting-subscriber Cloud-Run code ship, the
      `lifecycle-events-sub` terraform codification) — preserve that distinction in the evidence text; do not restate
      them as work this batch performed. After flipping, re-check each source doc for 0 remaining open items (checkbox
      AND prose-form) and only then consider flipping its `status` to `resolved`. **Done when**: every cited source
      checkbox is flipped with verified evidence and no doc's `status` was advanced past what its remaining items
      support. — DONE 2026-07-30 (unified-trading-pm, this commit). Enumerated all 14 `Source:`/`Sources:` citations
      across batch2's 14 todos → 14 distinct source-doc paths (the todo's "~22" was an overcount; several todos cite the
      same doc — `data_pipeline_alert_substrate_residual_2026_07_24.md` alone is cited by 5 different batch2 todos).
      Read every one in full and cross-checked its checkbox/status against batch2's own DONE evidence:
      `issues/catalogue_census_equivalents_inventory_2026_07_24.md`,
      `plans/archive/issues/{coverage_percent_symmetric_inclusion_audit,cli_shard_split_flag_coverage_audit,     mvp_scope_resolver_code_read,features_service_catalogue_completeness_inventory,dp_event_pubsub_delivery_gap,     manifest_hygiene_red_2026_06_27,manifest_hygiene_red_2026_06_29,     read_availability_index_unfiltered_callsite_audit_2026_07_26,     data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27,     gcs_data_access_audit_log_cost_2026_07_24}`,
      `plans/archive/2026_07/{data_pipeline_alert_substrate_residual_2026_07_24,gcs_data_access_audit_log_cost_2026_07_24}`,
      `plans/active/{data_pipeline_self_healing_completion_residual_2026_07_24,     data_pipeline_ag_residual_backfill_decisions_2026_07_24}`.
      **13 of 14 were already correctly reconciled** — prior sessions had flipped each source checkbox in the same turn
      as shipping the citing batch2 todo, with correct already-landed-vs-newly-shipped attribution throughout
      (spot-verified several cited SHAs exist: e.g. `unified-trading-library@d7b3ed7d`, `deployment-service@f2d094e`,
      `alerting-service@62b850c`); docs whose remaining items are genuinely still open correctly stayed
      `status: active`/`open` (`data_pipeline_self_healing_completion_residual_2026_07_24.md`,
      `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`,
      `catalogue_census_equivalents_inventory_2026_07_24.md` — each has a live unflipped batch2 sibling todo or a
      genuinely-new follow-up gap); docs with 0 remaining items were correctly archived with `status: resolved`. **One
      discrepancy found and fixed**: batch2's own todo 8 (UTL `DP_DAILY_DIGEST`/`DP_HYGIENE_SUMMARY` constants + MTDS
      per-source rate-limit event) was still unchecked, but both halves had actually landed 2026-07-30 via the sibling
      `data_pipeline_alert_substrate_residual_2026_07_24_finalize_2026_07_30.md` gated-twin plan
      (`unified-trading-library@0f851fd6`, `market-tick-data-service@7f42c557` — both commits verified to exist) — the
      source doc's own checkboxes were already correctly flipped there, batch2's citing checkbox simply never got
      re-synced. Flipped batch2 todo 8 `[x]` in this same commit with the already-landed attribution preserved (see
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`). The `gcs_data_access_audit_log_cost_2026_07_24.md`
      "duplicate" is not a bug: the `plans/archive/issues/` copy is an intentional `status: superseded` stub pointing at
      the real resolved doc in `plans/archive/2026_07/` — both archive copies are correct as-is.
- [x] ✅ [REVIEW] P1. **Re-check batch 2's own Deferred items now that time has passed and its todos have landed.** For
      each of the 3 conflict-gated, 7 operator-gated, 3 time-gated and 9 needs-own-triage-pass entries: re-read the
      specific gating ground and decide whether it has cleared. Route each to exactly one of — ready for a batch 3 (note
      it), still genuinely gated (re-confirm with fresh evidence), or belongs to another tranche (name that tranche).
      Three specific re-checks are cheap and high-yield: (a) has `defi_satellite_ao_dispatch_batch2_2026_07_26`'s
      finalize resolved the `defi_collateral_sizing…` retag, which would unblock its 4 todos; (b) has the tradfi
      finalize's own re-check cleared the `phantom_captures_tradfi_2026_06_28.md` double-claim; (c) **RESOLVED
      2026-07-27**: `/plans/archive/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` (infra-claimed) is now
      fully resolved + archived — the execution-service holdout migration shipped (execution-service@`9ce159a7`), all 11
      `--ignore-vuln` entries dropped fleet-wide. **Do NOT re-surface an operator question already asked** — decisions
      #10 and #11 in `issues/autonomous_session_operator_decisions_2026_07_25.md` and the two parked in this audit's own
      report are already queued. **Done when**: every Deferred entry carries a dated re-verification verdict with one of
      the three routings named. — DONE 2026-08-05 (slot 11, unified-trading-pm, this commit).

      **Re-verification verdict (2026-08-05, slot 11):** Parent batch now has all 14 todos `[x]` ✅ — gate condition
                          genuinely met (unlike 2026-07-30 when 5 were still open). All 22 Deferred items re-checked against live filesystem
                          state. Three named high-yield re-checks:

                          **(a) `defi_collateral_sizing` retag — NOT resolved.** Defi finalize
                          (`defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md`) has 0/4 todos done — hasn't executed at all. The doc
                          is still `locked_by: live-defi-rollout`. **Routing: still genuinely conflict-gated — defi finalize owns the retag;
                          lock must clear first.**

                          **(b) `phantom_captures_tradfi` double-claim — RESOLVED.** The doc is now in `plans/archive/issues/` with
                          `status: resolved`. The tradfi finalize's gate hasn't formally cleared (1 bundled OPERATOR todo still open), but
                          the doc itself is already archived as resolved — nothing left for any tranche to claim. **Routing: resolved,
                          belongs to no tranche (archived).**

                          **(c) `aiohttp_cve_2026_34993_vcrpy_deadlock` — CONFIRMED RESOLVED.** In `plans/archive/issues/` as previously
                          reported. **Routing: resolved (already noted 2026-07-27).**

                          ---
                          **Systematic re-verification of all 22 Deferred items:**

                          **CONFLICT-GATED (3):**
                          1. `phantom_captures_tradfi_2026_06_28.md` — **RESOLVED.** Archived with `status: resolved`. No remaining work to
                             batch.
                          2. `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` — **Still conflict-gated.** Lock still
                             holds; defi finalize (0/4 done) owns the retag. Re-check when defi finalize executes.
                          3. `sports_prediction_mvp_writetime_precompute_2026_07_24.md` — **Still conflict-gated, but routing is clear.**
                             Cross-cutting owns it via Track 23 (confirmed: the consolidated closeout still lists it as sole Source of Track
                             23). The sports batch6's "falls through every tranche" premise was refuted by this audit's own Phase 0. Ready for
                             batch3 as cross-cutting-owned once finalize todo 3's membership action formally closes the ownership question.

                          **OPERATOR-GATED (7):**
                          4. `asset_class_to_asset_group_rename_2026_07_21.md` — **Still operator-gated.** BLK-87fc93e4 (2026-07-21) stands:
                             `assigned_vm: NA` by deliberate operator-protective default. Operator must flip `assigned_vm: planning`.
                          5. `consolidator_throughput_backlog_monitor_2026_07_09.md` — **Still operator-gated.** "Cloud Build deploy DEFERRED
                             (operator 2026-07-10)" hold unchanged. WS-3 v2 histogram separately descoped.
                          6. `issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md` — **Still operator-gated.** `status: open`.
                             Todo 1 design decision (which model) still pending; todos 2-4 conditioned on it.
                          7. `issues/locked_plan_deletion_gate_never_runs_on_docs_plans_commits_2026_07_26.md` — **RESOLVED.** Now in
                             `plans/archive/issues/` with `status: resolved`. RULED (a) 2026-07-26 mandatory; mechanism-fix
                             (`check-locked-plan-deletion.sh`, commit-msg stage) shipped and end-to-end verified. Decision #11 is closed.
                          8. `issues/batch_live_reconciliation_service_audit_2026_05_27.md` — **Still operator-gated (by nature).**
                             `status: open`. Prose-form decision ledger; no checkbox todos to extract. Residual is "Needs operator input
                             (material)" by construction.
                          9. `data_status_catalogue_true_source_phase2_2026_07_24.md` — **Still operator-gated.** `status: active`. The
                             replacement projection shape is an undecided design call. The prettier-mangling defect is independent.
                          10. `data_pipeline_alerts_dp_not_v9` manifest mutation — **ALREADY DISPATCHED + DONE** (batch2 todo 13,
                              `[DATA] P2`). Moved from Deferred→dispatchable by the 2026-07-27 operator ruling. DONE 2026-08-04, slot-7:
                              both AGs 100% v9 clean, snapshots preserved.

                          **TIME-/SEQUENCING-GATED (3):**
                          11. `pipeline_mode_partition_migration_2026_06_01.md` — **Still time-gated.** `locked_by: live-defi-rollout`.
                              Single-walk discipline still applies; lands when owning L3 canonicalisation plans walk. Unresolved `[⚠️ NEEDS
                              VERIFICATION 2026-07-21]` marker on cefi/tradfi/prediction owner rows still present.
                          12. `data_pipeline_hardening_self_monitoring_2026_06_22.md` — **Routed away (not returning).** 2026-07-31
                              ownership-conflict sweep confirmed zero matching instances in either cloud. The
                              `/vm-preemption-billing-waste-audit` skill is the execution mechanism. Doc's `status: active` with no
                              `locked_by` — the batch's routing ("belongs with the skill, not a batch todo") was correct and final.
                          13. `data_feed_sla_registry_and_active_self_healing_2026_06_19.md` — **Partially cleared, route to infra/ci.**
                              aiohttp CVE IS resolved (archived, all 11 `--ignore-vuln` entries dropped). msgpack bump still has 1
                              `--ignore-vuln` entry remaining (alerting-service + AO gates). The batch's "route to infra/ci tranche"
                              recommendation was correct and still applies.

                          **NEEDS OWN TRIAGE PASS (9):**
                          14. Track 24 (8 docs, ~121 open todos) — **Still needs dedicated triage.** 4 of 5 `v2_engine_venue_buildout`
                              sub-plans now ARCHIVED (done); only `l2_book_microstructure_capture` still active. The consolidated closeout's
                              "first extraction candidate if line-cap split needed" recommendation stands — this family needs its own
                              extraction + triage pass, not another batch slot.
                          15. `mdps_features_reduced_artifact_tracker_2026_06_28.md` — **RESOLVED.** Archived to
                              `plans/archive/2026_07/`. Plan 3 shipped in full (verified 2026-07-27 correction), 0 own checkbox todos,
                              archival slated in `june_2026_vintage_audit_findings`.
                          16. `data_status_cell_grid_rearchitecture_2026_07_18.md` — **Still needs dedicated triage.** `status: active`.
                              Todo 1 (measure + profile) is bounded but extracting it solo risks the worker treating the design gate (todo 2)
                              as cleared. Better handled by operator splitting deliberately.
                          17. `deployment_redesign_cherrypicks_2026_07_20.md` — **RESOLVED.** Archived to `plans/archive/2026_07/` with
                              `status: complete`. All 5 cherry-picks done with shipped-commit + test evidence. The batch called these
                              "strongest candidates for batch3" — they were completed directly, not batched.
                          18. `bucket_fold_ml_2026_07_17.md` + `monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md` — **Partially
                              cleared.** `monitor_jobs` is now in `plans/archive/issues/` (archived). `bucket_fold_ml` is still
                              `asset_group: [cross-cutting]` — NOT retagged to `[infra]`. Batch1 finalize todo 3 owns both retags; until
                              that executes, `bucket_fold_ml` stays cross-cutting-owned.
                          19. `issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` — **RESOLVED.** Archived
                              to `plans/archive/issues/`. The batch's route-to-CI recommendation was correct.
                          20. `issues/live_mode_event_sink_topic_missing_2026_06_21.md` — **RESOLVED.** `status: resolved`. The fix-shape
                              decision was deferred to the `live_pipeline` epic per the doc's own recommendation. 0 checkbox todos.
                          21. `issues/empty_reprobe_disagreement_2026_06_22.md` — **RESOLVED.** Archived to `plans/archive/issues/` with
                              `status: archived`. The closeout's Track 15 "stale" verdict was correct; retag to `[defi]` already in batch1
                              finalize todo 3.

                          **Summary tally (2026-08-05):** 10 resolved/archived · 5 still operator-gated · 3 still conflict-gated · 2 still
                          time-gated (1 routed away) · 2 still need dedicated triage. The 5 operator-gated items all carry standing rulings
                          — none were re-surfaced. The 3 conflict-gated items have clear owners (defi finalize, cross-cutting Track 23). The
                          2 "needs triage" items (Track 24 family, cell_grid_rearchitecture) genuinely need a human design/extraction step,
                          not another batch slot.

- [x] ✅ [DOC] P2. **Action the two membership/classification findings this audit raised.** —
      unified-trading-pm@512a1c983 (1) Membership-scope gap recorded in closeout Progress Log + SKILL.md reinforced. (2)
      Sports batch6 deferred item corrected with Track-23 evidence — doc IS cross-cutting-owned via Track membership.
      (1) **The tranche-membership gap.** batch1's Phase-1 scope was 59 docs against a real membership of 142 (104
      non-peer-claimed), which is why the closeout's Tracks 16-24 went almost entirely un-triaged — those Tracks were
      added by the 2026-07-25 corpus-wide sweep AFTER batch1's candidate corpus had been scoped from the earlier 68-doc
      epic filter. Record this in `cross_cutting_consolidated_closeout_2026_07_25.md`'s Progress Log so the next
      `/ag-closeout-audit` derives membership from the closeout's Track/Sources lists UNION the epic filter, not the
      epic filter alone, and consider a one-line note in the skill's cross-cutting membership section. (2) **The
      `sports_prediction_mvp_writetime_precompute` ownership question.**
      `sports_satellite_ao_dispatch_batch6_2026_07_26.md` parked it as "falls through every tranche's audit …
      `cross-cutting`'s audit will not pick it up either", recommending reassignment to `infra`. That premise is
      **measurably wrong**: the skill's cross-cutting rule admits a doc by the epic filter **OR** explicit membership in
      the closeout's Tracks, and this doc is the sole Source of **Track 23 — Manifest schema bump: write-time MVP
      precompute**, so cross-cutting does pick it up (this audit found it that way). Reply to that parked item with this
      evidence rather than retagging to `infra`; if the operator still prefers `infra`, Track 23 must be removed from
      the cross-cutting closeout in the same change so the doc is not double-claimed. **Done when**: the membership note
      is in the closeout's Progress Log, the sports batch6 parked item carries the Track-23 correction, and no doc ends
      up claimed by two tranches.
- [ ] [DOC] P1. **Archive `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`** via the standard 6-step ritual:
      migrate any still-Deferred item to a tracked todo elsewhere (todo 2 above should have routed all 22 — verify none
      silently vanishes) → add the archive banner → run the codex-alignment check (this batch introduces no new durable
      contract; confirm that is still true, noting that the UTL writer-side canonical-path assert DOES tighten a writer
      invariant documented in `/codex/02-data/availability-manifest-and-data-status.md`, so re-read that doc before
      concluding no update is needed) → grep the corpus for every referrer of this batch or this finalize and fix each
      path → confirm `locked_by` is empty on both (it is). **Done when**: both docs are in `plans/archive/2026_07/`,
      every corpus referrer resolves to the new path, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports
      0 hard failures and 0 orphans.

## Progress Log

- 2026-07-30 (slot 7, worker on `assigned_role: review`, dispatch `...finalize-002`): **HOLDING OFF — same
  `gate_on_depends` wiring gap as the tracked recurring bug.** Todo 1 is genuinely done (verified above). But batch2's
  own plan file shows only 10/15 todos checked `[x]` (5 still `- [ ]`: the features-service catalogue inventory, the
  dp-audit OOM driver fix, the two bounded data-pipeline-alert bug fixes, the retagged `[DATA]` P2 item, and the
  unfiltered-callsite-audit item) — not the "all 14 done" this finalize plan's own header requires before ANY of its
  todos dispatch. `GET /api/backlog/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26_finalize-002/blockers` →
  `"ready (no blockers)"` confirms the gate did not hold. Same bug as
  `plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` (added as a new recurrence there
  rather than re-investigating from scratch — this is the 2nd distinct plan pair I've hit this exact bug on in one
  session, after `prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize`). Not flipping todo 2's checkbox — its
  own "Done when" (a dated re-verification verdict for every Deferred entry) is a genuine, non-trivial audit that the
  plan's authors explicitly intended to run only after the full batch lands, and re-checks (a)/(b) in its own text
  reference OTHER tranches' finalizes whose state I have not verified either. Skipped back to the queue.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (6 entries, corrected count from the prior
  marker) -- finalize gate doc, code-free by rule; existing links (gated source + parent closeout + 2 archival/naming
  codex SSOTs + skill) still resolve and remain the minimal correct set.
- **2026-08-05 (slot 11, `assigned_role: review`, dispatch `...finalize-002`): Todo 2 DONE — full re-verification of all
  22 Deferred items.** Parent batch now has all 14 todos `[x]` ✅ (gate condition genuinely met, unlike 2026-07-30).
  Re-checked every deferred item against live filesystem state (not cached reads). Three named high-yield re-checks: (a)
  `defi_collateral_sizing` retag NOT resolved — defi finalize 0/4 done, lock still holds; (b) `phantom_captures_tradfi`
  double-claim RESOLVED — doc archived with `status: resolved`; (c) `aiohttp_cve` CONFIRMED still resolved. **State
  changes since 2026-07-26**: 7 deferred items have cleared (archived/resolved): `phantom_captures_tradfi`,
  `locked_plan_deletion` (decision #11 RULED mandatory, fix shipped), `mdps_features_reduced_artifact_tracker`,
  `deployment_redesign_cherrypicks` (all 5 done), `monitor_jobs_auto_repin`, `hatch_vcs`, `live_mode_event_sink`,
  `empty_reprobe_disagreement`. Plus `data_pipeline_alerts_dp_not_v9` mutation was dispatched + done (batch2 todo 13).
  **Final tally**: 10 resolved/archived · 5 still operator-gated · 3 still conflict-gated · 2 still time-gated (1 routed
  away) · 2 still need dedicated triage. No operator questions re-surfaced. Full verdict inline in todo 2 above.
