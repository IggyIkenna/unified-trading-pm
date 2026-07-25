---
doc_type: plan
title: TradFi satellite AO batch 3 — gap-check extraction from 8 previously-untriaged docs
summary: >-
  Third AO-dispatch batch for tradfi, produced by the `/ag-closeout-audit` skill's gap-check step (batchN methodology,
  step 2 — "check whether entirely new orphans appeared since the last audit") rather than a re-check of batch2's own
  Deferred section (that re-check ran first: all 8 of batch2's still-genuinely-conflicted candidates remain unresolved
  as of this pass — the closeout's own Phase A2/Phase C content moved to a new fork
  (`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`) between batch2 and this pass, but the competing claims
  themselves are unchanged, just relocated — see this doc's Deferred section for the current status). A gap-check
  Workflow (`wf_d28e7756-0ed`, 8 agents, 0 errors) classified 8 tradfi docs never named as a source by batch1 or batch2
  (the corpus's current 26 non-admin tradfi candidate docs minus the 18 batch1/2 already named) against the full
  covering-plan family (closeout + its 4 forked children + batch1/2 + native-extract). 6 of 8 are genuinely orphaned
  (`orphaned_partial_coverage` or `orphaned_never_touched`); 5 conflict-clear, ready-now, bounded items across 5
  distinct docs are extracted here (combined into 3 todos on same-file-collision grounds); 1 item is conflict-gated
  against an already-deferred batch2 candidate (same underlying FX manifest-id defect, broader scope — not
  re-dispatched, see Deferred); several more are genuinely dependency-gated on still-open upstream prerequisites, not
  conflict-gated (also in Deferred, distinguished from the conflict-gated class per the skill's non-batchable taxonomy).
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, features-service, market-tick-data-service]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-3, satellite-docs, gap-check]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
    /plans/active/issues/tradfi_docs_reconciliation_findings_2026_07_21.md,
    /plans/active/issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md,
    /plans/active/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md,
    /plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
    /plans/active/issues/tradfi_t1_no_working_mtds_job_2026_07_17.md,
    /plans/active/issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit tradfi gap-check pass, 2026-07-25, per the skill's "batchN methodology" step 2 (check for entirely
  new orphans since the last audit, run only after re-checking the prior batch's own Deferred section first — that
  re-check found all 8 of batch2's conflict-gated candidates still unresolved, see Deferred below). Workflow
  `wf_d28e7756-0ed` (8 agents, 0 errors, 851,907 tokens) classified the 8 tradfi docs never named by batch1 or batch2's
  Todos/Deferred sections against the full covering-plan family.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 3 — gap-check extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 3 todos below are same-priority and touch distinct files (verified against the classification
> workflow's own per-doc coverage citations) so they are safe to dispatch concurrently once activated.

## Todos

- [ ] [REVIEW] P2. **Close two independent gaps in `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s own
      content, combined into ONE todo because both edit the SAME doc file and would collide if dispatched as two
      concurrent AO todos**: (1) Flip the "Full MTDS+IS adapter smoke findings re-verify" checkbox (Phase A2, citing
      `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`, `instruments_remaining_work_audit_2026_07_10.md`,
      `uac_data_type_validity_combinator_fragmentation_2026_07_07.md`) — the substance is ALREADY investigated and
      resolved: `tradfi_consolidated_native_ao_extract_2026_07_25.md` independently found 0 genuinely tradfi-scoped open
      work remains across all 3 cited docs, but its own recommendation to "flip this checkbox on the closeout" is stale
      — that checkbox no longer lives on the parent (`tradfi_consolidated_closeout_2026_07_18.md`), it was forked
      verbatim into THIS doc on 2026-07-25. Re-verify the native-extract's 0-open-work finding still holds (a quick
      re-check, not a fresh investigation), then flip THIS doc's checkbox citing that evidence. (2) Run the adversarial
      AO-dispatch-readiness pass (`task_template.md` §3's finding taxonomy A-S) against THIS doc's own Phase A2 + Phase
      C content — the closeout's own equivalent pass (2026-07-25) covered the pre-fork parent; this doc is a fresh fork
      of that content and has never had its own pass run. Repo: unified-trading-pm (doc-only). **Done when**: (a) the
      "Full MTDS+IS adapter smoke findings" checkbox is flipped `[x]` citing the native-extract's re-confirmed
      0-open-work finding; (b) a filed finding list (or a stated "clean" verdict) covering every defect class in
      `task_template.md` §3 exists for this doc's A2+Phase C content, with any fixes applied directly or filed as
      follow-up todos. Source: `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (self-audit obligation, its own
      content).

- [ ] [SCRIPT] P2. **Wire the 2 still-open feature-dispatch gaps in
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` into features-volatility-service, combined into ONE
      todo because both touch the same CLI-dispatch file family**: (1) Wire `realized_vol` into the features-volatility
      CLI dispatch (add the `FEATURE_GROUPS` entry, the `data_loader` path, the dispatch branch, and unit tests — 4
      explicit steps already scoped in the source doc's own P2 item). (2) Wire `vix`/`realized_vol_vix` into
      `FEATURE_GROUPS` + `_calculate_features` dispatch (steps 3/4 of the source doc's VIX-cash-index-gap item,
      explicitly still open per that doc's own latest note superseding the cash-index approach). Both are pure
      code-scaffolding changes independent of the doc's separate, still-blocked P0 data-run items (see Deferred — those
      remain gated on `data_completion_tradfi_2026_07_15.md`'s unresolved instrument_availability gap, NOT re-dispatched
      here). Repo: features-service. **Done when**: both feature groups are dispatchable via the features-volatility CLI
      with passing unit tests covering the new dispatch branches; `quality-gates.sh` green in features-service; the 2
      corresponding P2 checkboxes in `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` are flipped in the same
      commit. Source: `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`.

- [ ] [DOC] P2. **Two independent doc-hygiene corrections, combined into ONE todo because both are small and the third
      finding names the second doc as its own recommender (no file collision — 3 distinct PM doc files, bundled purely
      for batch efficiency, verify no collision before dispatch if split later)**: (1) Correct
      `issues/tradfi_canonical_path_migration_design_2026_07_19.md`'s stale "Massive removal" section, Sequencing steps
      4-6, and "Hard-stops" section — all three still describe the 1.47M-object `batch_massive` purge as PENDING and
      gated on a Databento backfill of "571 Massive-only shards" FIRST, but the purge already EXECUTED 2026-07-20/21
      under operator Option C (accepted-permanent-loss; RUN_TS=20260720-193849, 1,701,422→0 objects, 0 collateral) and
      the 571 no-twin shards were accepted as permanent loss, NOT backfilled first. This exact correction was already
      recommended by `issues/tradfi_docs_reconciliation_findings_2026_07_21.md` but the applied fix
      (unified-trading-pm@1dd1a22fd) only touched codex docs, never this file — verify that citation still holds, then
      rewrite the 3 sections to state the purge as executed with the RUN_TS/object-count evidence. (2) Reconcile
      `issues/tradfi_t1_no_working_mtds_job_2026_07_17.md`'s stale `status: open`/blank `resolved_by` frontmatter — its
      own 2026-07-25 "Status note" left it open pending the SIGKILL follow-up in
      `tradfi_backfill_throughput_followups_2026_07_24.md`, but that follow-up is now `[x]` "RE-VERIFIED LIVE
      2026-07-25, NOT REPRODUCING" (5 consecutive trading-day executions, 0 failures) — re-verify that evidence still
      holds, then flip `status: resolved` and fill `resolved_by` citing the shipped commits + both RE-VERIFIED-LIVE
      evidence blocks (the nightly cron `SUCCEEDED_COUNT=1` for 4+ consecutive nights, and the SIGKILL non-reproduction
      run). Repo: unified-trading-pm (doc-only). **Done when**: (a) all 3 stale sections in
      `tradfi_canonical_path_migration_design_2026_07_19.md` state the purge as executed, citing RUN_TS + object counts;
      (b) `tradfi_t1_no_working_mtds_job_2026_07_17.md`'s `status` reads `resolved` with `resolved_by` populated citing
      real commits/evidence. Source: `issues/tradfi_canonical_path_migration_design_2026_07_19.md` (also cites
      `issues/tradfi_docs_reconciliation_findings_2026_07_21.md` as the original recommender) and
      `issues/tradfi_t1_no_working_mtds_job_2026_07_17.md`.

- [ ] [BACKEND] P2. **Add a manifest-vs-disk consistency check** to market-tick-data-service so a `captured` row with no
      object on disk fails loudly — prevents the exact phantom-row class that previously produced both 3,615 real
      phantoms and a contaminated 16,389-row candidate list from recurring silently. Wire the check into either the
      manifest-write path or a periodic audit job (worker's judgment on placement — the doc doesn't prescribe one).
      Repo: market-tick-data-service. **Done when**: a manifest row with `capture_status=="captured"` and no
      corresponding GCS object present is detected and fails loudly (a raised error, a structured alert event, or an
      audit-report flag — not a silent pass), with a unit/integration test proving the detection fires on a synthetic
      mismatch; `quality-gates.sh` green. Source:
      `issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md`.

## Deferred — conflict-gated (NOT dispatched; same ground as an already-deferred batch2 candidate)

- `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`'s FX/cash-type manifest `instrument_id` bug
  (`_build_tradfi_cash` UAC builder branch never populating manifest `instrument_id` for `spot_pair`/currency/bond/
  commodity/cds) is the SAME underlying defect as `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`'s
  "fix the FX write path + backfill the manifest `instrument_id` column" candidate — already conflict-gated in
  `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s own Deferred section against the closeout's (now
  `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s) still-open "two live defects" finding, competing claim
  still unshipped. Per the operator's explicit "never silently resolve a conflict" instruction, not re-dispatched here
  under a different doc name — this is the same ground, just discovered via a second, broader-scope source doc.

## Deferred — dependency-gated (NOT conflict-gated; genuinely not yet actionable, no re-triage will change this)

- `issues/tradfi_docs_reconciliation_findings_2026_07_21.md`'s 3 remaining doc/codex-hygiene rewrites (supersede banner
  on the closeout's Ground-truth verdict; retire a stale reconciliation-findings line item now closed via a sibling
  fork; rewrite `canonical-cutover-register.md` §4's closing paragraph) are all explicitly sequenced behind Surfaces C+D
  (GCS filename + tick parquet content) landing at scale — `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s
  own `--apply AT SCALE STILL PENDING` P0 todo. All 3 are AO-eligible in isolation but not yet actionable; re-check once
  that prerequisite ships (a natural batch4 candidate).
- `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`'s 3 P0 run tasks (MDPS `build-continuous`,
  `features-delta-one-service` run, `features-volatility-service` run) and its 3 P3 backtest/smoke tasks are tagged
  `BLOCKED-OPERATOR-DECISION`/`BLOCKED-UPSTREAM` in the source doc, but that tag is STALE — the actual architecture
  decision (MDPS passthrough, Option B) already shipped via the archived
  `tradfi_mdps_passthrough_dependency_gap_2026_06_28.md`. The REAL remaining blocker is
  `data_completion_tradfi_2026_07_15.md`'s still-unresolved finding that `instruments-store-tradfi` has 0
  `instrument_availability` dates for historical TradFi — itself not yet AO-dispatched (that doc is excluded from
  batch1/batch2 as a large, mixed-coverage doc). These 6 items are genuinely dependency-gated, not conflict-gated: once
  the upstream `instrument_availability` gap clears, this doc has 6 more AO-eligible run/backtest todos ready for a
  future batch — flagged here as a fresh finding for operator awareness, not dispatched prematurely against an unmet
  real prerequisite.

## Already archivable — no batch3 action needed

- `issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md` (`archivable_after_planned_work`): every
  AO-eligible fragment of its 4 decision items is already covered by `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`
  (the EXCHANGE_CODE_TO_NAME audit, and the legacy-twin dry-run/claim-check); the substantive decisions themselves (ICE
  remediation strategy, chain-manifest retire `--apply` sign-off) remain correctly human-only. Becomes archivable once
  batch1(+finalize) completes and the operator answers items 1-3.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_satellite_ao_dispatch_batch3_finalize_2026_07_25.md`
(`depends_on: [tradfi_satellite_ao_dispatch_batch3_2026_07_25]` — `gate_on_depends: true`), mirroring the batch1/batch2
finalize-plan pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc.
