---
doc_type: plan
title: Cross-cutting satellite AO batch 1 — finalize (reconcile source docs + resolve deferrals + archive both parts)
summary: >-
  Gated closeout for cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md AND its sibling
  cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md — machine-held via depends_on + gate_on_depends: true until
  all 31 todos across both parts are done. Reconciles each distinct source doc's checkboxes independently, then
  re-checks the Deferred conflict-gated/operator-gated/time-gated items (4/13/2) plus the 7 mistags and 2 archivable_now
  docs found during Phase 0/1, then archives both batch docs via the standard 6-step ritual.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
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
depends_on:
  [cross_cutting_satellite_ao_dispatch_batch1_2026_07_26, cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched
  plan needs a companion gated finalize plan; this one gates on BOTH halves of the split batch.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md,
  ]
---

# Cross-cutting satellite AO batch 1 — finalize

> **Machine-gated on BOTH `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (16 todos) AND
> `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (15 todos)** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 31 tasks across both parts are `done`. `sequential: true`
> because todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all distinct source docs' checkboxes across both batch parts.** For each of the 31
      now-done todos (across batch1 + batch1b): flip the corresponding checkbox/section in its named source doc (each
      todo's text ends with "Source: `<doc>.md`"), citing the batch commit(s) that shipped it — verify the actual
      shipped commit exists before citing it. For each source doc: after flipping, re-check whether it now has 0 open
      todos remaining (checkbox AND prose-form). Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open
      todos. **Done when**: all 31 source-doc checkboxes/sections are flipped with verified evidence.
- [ ] [REVIEW] P1. **Re-check the 4 conflict-gated + 13 operator-gated + 2 time-gated Deferred items** (all in
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s own Deferred sections — batch1b defers to that same
      doc, not a duplicate), now that time has passed and batch1/1b's own todos have landed. For each of the 19 Deferred
      items: re-read the specific gating ground to check if it has since cleared — if so, extract it as a new tracked
      todo in a follow-up `batch2`; if still genuinely unresolved, leave it explicitly deferred, do not re-surface an
      already-asked operator question a second time. **Done when**: each of the 19 Deferred items has either (a) a note
      that it's ready for `batch2` extraction, or (b) an explicit re-verified confirmation the gate is still open.
- [ ] [DOC] P2. **Action the 6 remaining mistags + 2 archivable_now docs found during Phase 0/1** (was 7 mistags;
      `shared_host_tmp_tmpfs_exhaustion_2026_07_26.md` resolved + archived to
      `plans/archive/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_26.md` in the 2026-07-26 terminal-status sweep — no
      retag needed, drop it from this list). **CORRECTED 2026-07-27 (`/plan-vintage-audit` archival pass)**: 2 of the
      named docs are now MOOT — `empty_reprobe_disagreement_2026_06_22.md` and
      `live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md` are both fully archived (
      `/plans/archive/issues/empty_reprobe_disagreement_2026_06_22.md`,
      `/plans/archive/issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md`) — no retag needed, drop both from
      this list. `monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md` is ALSO now fully archived
      (`/plans/archive/issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md`) — drop it too. (1) Retag
      the remaining 3 genuinely infra-scoped docs (`plans/active/bucket_fold_ml_2026_07_17.md`,
      `plans/archive/2026_08/bucket_iam_write_protection_per_tier_2026_06_09.md`,
      `plans/active/infra_capture_and_devops_leftovers_finalize_2026_07_25.md` → `[infra]` or fold into
      `infra_consolidated_closeout_2026_07_25.md`'s Sources list per that doc's own convention) — read each doc's real
      content first to confirm before retagging (do not blind-apply), then re-run
      `scripts/plan-hygiene/check_ag_closeout_linkage.py` after each retag. (2) Archive
      `plans/archive/2026_07/bucket_estate_fold_design_2026_07_13.md` via the standard 6-step ritual. (3) **⚠️ CORRECTED
      2026-07-26 (`/ag-closeout-audit cross-cutting` re-invocation) — do NOT run the archival ritual on
      `gcs_data_access_audit_log_cost_2026_07_24.md`; DELETE the stale active duplicate instead.** Measured: that
      filename exists in BOTH `plans/active/issues/` (364L, `status: open`, 1 open `[DEVOPS] P2`) AND
      `plans/archive/2026_07/` (368L, `status: resolved`,
      `resolved_by: operator (ikenna@odum-research.com, 2026-07-25)`, **0 open todos**) — the archived copy is the
      later, authoritative one, and the cross-cutting closeout's own Track 6 already records the operator completing the
      `setIamPolicy` `auditConfigs` removal on 2026-07-25. Running the ritual on the active copy would overwrite that
      resolved archived copy with the stale open one. Correct action: delete
      `plans/active/issues/gcs_data_access_audit_log_cost_2026_07_24.md` (`locked_by` is empty — verified — so no
      `[unlock-plan]` is needed), repoint any referrer at the archive path, and re-run
      `.venv/bin/python scripts/plan-hygiene/regenerate_active_plan_inventory.py` (the duplicate is currently inflating
      the inventory by one doc and one phantom open todo). (was: "Archive `plans/active/bucket_estate_fold_design…` and
      `plans/active/issues/gcs_data_access_audit_log_cost…` (both `archivable_now`) via the standard 6-step ritual.")
      **Done when**: all 6 retags are applied with `check_ag_closeout_linkage.py` passing 0 new orphans,
      `bucket_estate_fold_design_2026_07_13.md` is archived with every corpus referrer fixed, and only the archive copy
      of `gcs_data_access_audit_log_cost_2026_07_24.md` remains with the inventory regenerated.
- [ ] [DOC] P1. **Archive `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`** via the standard 6-step
      ritual (per CLAUDE.md's plan-archival rule). **Corrected 2026-08-18 (plan_reconciler cross-cutting)**: this
      todo used to say "archive both" — batch1
      (`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`) is ALREADY archived (confirmed present at
      `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`; this doc's own `related:`
      frontmatter already cited that archived path correctly, line 19). Only batch1b (currently down to 1 open todo,
      grep-verified) still needs the ritual run. Steps: migrate any remaining Deferred items to a tracked todo
      elsewhere (todo 2 above should have already resolved or re-confirmed all 19 — verify none silently vanish) →
      add the archive banner → run the codex-alignment check (no new durable contract from this batch, confirm still
      true) → grep the corpus for every referrer of batch1b and fix each path to point at the archived location →
      clear `locked_by` (already empty, confirm). **Done when**: batch1b is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **2026-07-30 (slot 14, review-craft-adopted) — todo 1 PARTIAL, NOT flipped: the "31 now-done" premise is stale/false
  right now.** Picked up finalize-001 via `/boot`. Before reconciling, checked the live backlog (`GET /api/backlog`)
  against the two `depends_on` plans this doc's own `gate_on_depends: true` should have blocked on: **9 of batch1's
  current 19 todos and 11 of batch1b's current 18 todos are still `queued`, not `done`** — 20 still-open backlog tasks
  total (real count now 37 todos across both docs, not the original "31"; both docs grew via mid-flight splits, e.g.
  batch1's `-017`). The gate did not actually hold — this is the SAME recurring `gate_on_depends` wiring gap already
  tracked (this exact batch1/batch1b dual-gate case was already documented twice, by slot 7 and slot 12, with
  byte-identical 9/19 + 6/18 counts) at
  `plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` — no new issue doc filed (a
  first pass here mistakenly created a duplicate, since deleted).
  - **What I did anyway (real, bounded, verified progress)**: identified every todo across both docs that IS currently
    `[x]` done (~15), and for each, verified whether its named `Source:` doc's own checkbox/section was already
    reconciled (most workers already did this inline as part of shipping their todo) or still needed a real edit.
    Result: **13 of the ~15 were already correctly reconciled** (verified via direct read, not trusted blindly) —
    `distinct_values_noncanonical_audit_2026_07_20.md` (archived, line-191),
    `instruments_completion_tracker_2026_07_06.md` (46/61 checked, 15 genuinely still open, matches its own text),
    `cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md` (archived, resolved),
    `datapoint_validation_results_bucket_missing_2026_07_21.md` (archived, resolved),
    `features_service_coverage_and_script_canon_2026_06_10.md` (flipped, cites features-service@25932d23),
    `silent_wrong_answer_audit_candidates_2026_07_20.md` (archived, resolved),
    `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (R5-fix-5 flipped),
    `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` (§#7 correctly left unchecked — partial
    scope, no false-completion), `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (per-item citations already
    appended, GATE 0 correctly still open), `legacy_bucket_dual_write_decommission_2026_07_24.md` (both lead items
    closed-with-evidence). **2 needed real edits, done this session**:
    `instrument_record_schema_completeness_extra_forbid_2026_07_18.md` (todos 1-2 flipped `[x]` with the authoritative
    field-list + per-field disposition-table evidence from batch1's DATA/P1 todo, citing `instruments-service@ee2d6c75`;
    todos 3/4 annotated PARTIAL — REMOVE-subset done, `min_order_size` still ambiguous/unresolved so ADD/final-flip stay
    open; verified `ee2d6c75` is a real ancestor commit before citing it) and
    `instruments_foundation_completeness_2026_06_24.md` (DeFi completeness ORACLE P0 item annotated PARTIAL — only the
    §9 schema-only rollout slice landed, `unified-api-contracts@1407b7fd` verified as a real commit; the checkbox
    correctly stays unchecked since probe implementation + `--use-defi-oracle` wiring are still unbuilt). **1 item
    (`DATA P0` CF-1…CF-12) explicitly should NOT be flipped** — batch1's own text already reasoned this correctly
    (partial 4-of-5-AG coverage, flipping would overclaim); no action needed, confirmed correct as-is.
  - **Not attempted**: the ~22 still-open batch1/batch1b todos have no `Source:` reconciliation to do yet (they aren't
    done). This todo's own checkbox stays `[ ]` — flipping it now would be a false-completion claim (workspace HARD
    RULE: plans run to actual completion). **Re-dispatch this todo once batch1 + batch1b actually reach 0 open todos**
    to catch the remaining ~22 source-doc reconciliations in one pass.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (5 entries) -- finalize gate doc, code-free
  by rule, existing links (both gated source docs + parent closeout + skill + recurring wiring-gap issue) still resolve
  and are the minimal correct set.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
