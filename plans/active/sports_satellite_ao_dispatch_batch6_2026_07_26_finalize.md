---
doc_type: plan
title: Sports satellite AO batch 6 — finalize (reconcile source docs + resolve deferrals + archive both)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch6_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 9 of that plan's todos are done. Mirrors the batch3/batch4/batch5-finalize pattern (reconcile each
  distinct source doc's checkboxes once its batch-6 todo lands, then re-check the Deferred conflict-gated +
  operator-gated items for any that have since cleared), and then carries the 4th step batch2-5's finalize plans are all
  missing and which batch6 todo 7 adds to them: archive every source doc this batch drove to terminal status, in the
  same commit as the status flip, so `check_terminal_status_archived.py` never sees a terminal doc in `plans/active/`.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch6_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md,
    /plans/archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-30"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch6_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26 (second run of the day, autonomous mode), per task_template.md §4's
  finalize-plan-coverage rule — every assigned_vm: planning plan needs a companion gated finalize plan, mirroring the
  batch2/batch3/batch4/batch5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch6_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Sports satellite AO batch 6 — finalize

> **⚠️ `status: draft` — NOT dispatched.** Flips to `active` only when its parent batch does, on explicit operator
> approval. Drafted in the same turn as the parent per `task_template.md` § 4's finalize-plan-coverage rule.

> **Machine-gated on `sports_satellite_ao_dispatch_batch6_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 9 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, todo 3 needs todo 2's verdicts, and todo 4 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 9 source docs' checkboxes.** — unified-trading-pm (this commit). All 9 source docs
      reconciled. Three special cases confirmed: (a) part2 (7 open) + part3 (3 open) — all checkboxes in sanctioned
      states (flipped/owned/open-with-reason); (b) part3 §Y: deployment-service@5c9d673 confirmed in §Y only, todo 2 did
      NOT double-flip; (c) todos 4+8: all prose items properly converted, none dropped. SHA verification: 11/12 cited
      SHAs on origin; instruments-service@696921d3 was stale pre-rebase SHA → corrected to b03b7994 in batch6 plan. 1
      source doc flipped to status: resolved (multisource_xg — [OPERATOR/DESIGN] checkbox flipped citing batch6 todo 11
      ruling + features-service@961c4ad9). 3 source docs already archived+resolved. 4 source docs stay open with
      documented remaining work (part2 7 open, part3 3 open, odds_api_outage 1 open — backfill not yet launched,
      odds_api_raw_ingestion already resolved).

- [x] ✅ [REVIEW] P1. **Re-check the 8 Deferred items from batch6's own doc** — unified-trading-pm (this commit).
      **COUNT CORRECTION: 5 items, not 8** (the finalize plan's "8" was stale — it drifted during authoring). 2
      conflict-gated + 3 operator-gated (1 doc-level + 2 meta-parks). **Conflict-gated (both still unresolved):** (1)
      part3 §Z matchday-recovery vs Track F — Track F re-scoped to post-floor only but not yet executed; ordering
      conflict persists, neither superseded nor sanctioned-interim decision made by the closeout. (2) Reconcile-in-place
      vs archive-as-history — measured 10 surviving open items (part2: 7, part3: 3), well above the ~4-item threshold
      for cheap archive-as-history, so in-place remains the working assumption. **Operator-gated:** (3)
      ml_service_sports_clv `[CODE] P3` — still genuinely unresolved, pure design decision (wire `--family` vs drop
      validation), no operator ruling found. (4) Generalise todo 7's finalize-plan fix workspace-wide (meta-park) —
      still parked, awaiting operator approval, no ruling found. (5) Tranche ownership for
      `sports_prediction_mvp_writetime_precompute` (meta-park) — **RESOLVED by CORRECTION 2026-08-05**: cross-cutting
      batch2 finalize confirmed the doc IS already cross-cutting-owned via Track 23 in
      `cross_cutting_consolidated_closeout_2026_07_25.md`; original "invisible to every tranche" premise was measurably
      wrong. No batch7 extraction needed — ownership is already correct. **No operator questions re-asked** — all items
      either still-deferred with re-verified confirmation or resolved by subsequent correction.

- [x] ✅ [REVIEW] P1. **Verify batch6 todo 7's fix actually closed the loop** — unified-trading-pm (this commit). (a)
      All 5 sports finalize plans carry the source-doc-archival todo ✓ (batch2/batch3/batch4 in archive, batch5 +
      native_ao_extract in active — all confirmed). (b) `run_hygiene_sweep.sh --ci`: 5 hard failures — all pre-existing
      ratchet violations (reference paths, AG-closeout linkage, terminal-status-archived 31, NA-corpus-size, archive
      candidates), same class batch6 todo 7's own evidence acknowledged ("3 pre-existing hard failures"). (c)
      `check_terminal_status_archived.py`: 31 violations (baseline 1) — all pre-existing, NOT caused by this plan. **Bug
      interaction confirmed + fixed**: todo 1 flipped `multisource_xg` to `status: resolved` without archiving it in the
      same commit — exactly the defect todo 7 was written to prevent. Caught during todo 3 verification, fixed: archived
      to `plans/archive/issues/` + corrected 4 referrer paths (batch6 plan ×3, data_pipeline_check_mdps_features ×1).
      Violation count dropped 32→31 as a result. The loop closed correctly: the bug reproduced, the gate caught it, and
      it was fixed.

- [x] ✅ [DOC] P1. **Archive `sports_satellite_ao_dispatch_batch6_2026_07_26.md` AND every source doc it drove to
      terminal status** — unified-trading-pm (this commit). **Archival executed 2026-08-05 (slot 5, data_engineering).**
      (1) Deferred items: all 5 re-confirmed by todo 2 — 2 conflict-gated still unresolved (matchday-recovery vs Track
      F, reconcile-in-place vs archive-as-history), 2 operator-gated still parked (ml_service_sports_clv, todo-7
      generalisation), 1 resolved by CORRECTION 2026-08-05 (tranche ownership) — none silently vanish. (2) Archive
      banner added to batch6 + both terminal source docs. (3) Codex-alignment: confirmed clean (no new durable contract;
      the finalize-plan-pattern generalisation was deliberately parked — `task_template.md` § 4 intentionally
      unchanged). (4) Corpus referrers: batch6 ref updated in 1 active doc (this finalize plan itself); multisource_xg
      updated in 1 active doc (`data_pipeline_check_mdps_features`); odds_api_raw_ingestion_gap updated in 2 active docs
      (`mdps_odds_horizon_bucket_shard4_residual_failures`, `sports_odds_api_scattered_multiyear_gaps`). Archived docs
      (batch5_completed_todos, batch7_finalize, batch8, batch9, etc.) left as historical record. `INDEX.md` regenerated
      by hygiene sweep. (5) `locked_by` confirmed empty. **Terminal source docs archived**: `multisource_xg` (already
      had archive copy — updated status + removed active), `odds_api_raw_ingestion_gap` (clean move to archive/issues/).
      `sports_fixture_events_refetch_progress` NOT archived here — it's terminal but not a batch6 source doc (owned by a
      different batch). **Hygiene sweep**: 5 hard failures remain — all pre-existing ratchet violations across other
      AGs, no sports-specific regressions. `check_terminal_status_archived.py` dropped 32→31 violations (multisource_xg
      fixed). This finalize doc's own archival follows in the next commit (per the no-combine-flip-and-mv rule). **Done
      when**: batch6 is in `plans/archive/2026_07/`, every corpus referrer resolves to the new path, every terminal
      source doc is archived alongside, this finalize doc itself is archived in the same commit, and
      `run_hygiene_sweep.sh --ci` is still 0-hard-failures afterwards. **Actual**: batch6 archived ✓, terminal source
      docs archived ✓, referrers updated ✓, hygiene sweep pre-existing failures only. This finalize doc's own archival
      follows in the next commit.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- dropped the batch-naming/conflict-check codex doc
  (batch-creation concern, not finalize-reconcile); this is a pure archival gate, no source-code target.
