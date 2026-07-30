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
- [ ] [REVIEW] P1. **Re-check batch 2's own Deferred items now that time has passed and its todos have landed.** For
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
      the three routings named.
- [ ] [DOC] P2. **Action the two membership/classification findings this audit raised.** (1) **The tranche-membership
      gap.** batch1's Phase-1 scope was 59 docs against a real membership of 142 (104 non-peer-claimed), which is why
      the closeout's Tracks 16-24 went almost entirely un-triaged — those Tracks were added by the 2026-07-25
      corpus-wide sweep AFTER batch1's candidate corpus had been scoped from the earlier 68-doc epic filter. Record this
      in `cross_cutting_consolidated_closeout_2026_07_25.md`'s Progress Log so the next `/ag-closeout-audit` derives
      membership from the closeout's Track/Sources lists UNION the epic filter, not the epic filter alone, and consider
      a one-line note in the skill's cross-cutting membership section. (2) **The
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
