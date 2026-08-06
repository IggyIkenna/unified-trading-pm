---
doc_type: plan
title: TradFi satellite AO batch 2 — finalize (reconcile source docs + re-check remaining deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch2_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 11 of that plan's todos are done. Mirrors the batch1_finalize pattern (reconcile each of the 11
  distinct source docs' checkboxes independently — corrected 2026-07-25 plan-reconcile, the doc list below always had 11
  entries but the prose said 9), plus one batch2-specific addition: re-check the 8 still-genuinely-conflicted Deferred
  items + the 1 operator-gated item once the operator has ruled on the queued FX-sequencing / mvp_mode decisions, and
  recommend whether `tradfi_manifest_content_recovery_completion_2026_07_24.md` (excluded from both batch1 and batch2)
  is ready for its own dedicated triage/design pass yet.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
parent_epic: tradfi_master
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
depends_on: [tradfi_satellite_ao_dispatch_batch2_2026_07_25]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi re-triage session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# TradFi satellite AO batch 2 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 11 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-08-06 (slot-10, review)** — Reconcile all 11 distinct source docs' checkboxes.** For
      each of `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s 11 now-done todos: flip the corresponding
      checkbox/section in its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-2
      commit(s) that shipped it — verify the actual shipped commit exists before citing it. The 11 source docs:
      `data_completion_tradfi_2026_07_15.md` (2 checkboxes, 1 combined todo),
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (7 checkboxes, 1 combined todo),
      `tradfi_backfill_throughput_followups_2026_07_24.md` (3 checkboxes, 1 combined todo — plus confirm the
      `issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md`-sourced todo also flipped this doc's own P2
      candidate on the 182,407-cell cohort), `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md`,
      `archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md`,
      `issues/tradfi_backfill_oom_remediation_2026_06_24.md`,
      `archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md` (resolved + archived 2026-07-30),
      `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`,
      `issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md`,
      `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`,
      `/plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md`. For each: after flipping, re-check whether it
      now has 0 open todos remaining. Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open todos
      (checkbox AND prose-form). **Done when**: all 11 source docs' corresponding checkboxes/sections are flipped with
      verified evidence, and any doc that genuinely reaches 0 open todos is flipped to `status: resolved`.

      **Evidence (slot-10 review, 2026-08-06)** — Verified ALL 11 source docs' batch2-corresponding
          checkboxes/sections are flipped, each cited shipped commit confirmed present on
          `origin/live-defi-rollout` via `git cat-file -e <sha>^{commit}` (no fabricated cites): (1)
          `data_completion_tradfi_2026_07_15.md` — 2 checkboxes [x] (line-54 drift-verify + E6 CF-7 relabel), stays `active`
          (15 genuine open); (2) `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — all 7 combined-todo items [x]
          (incl. Deferred-work row #2 for `uac@599acf93` + G1-refinements contradiction fix), stays `active` (5 genuine
          open); (3) `tradfi_backfill_throughput_followups_2026_07_24.md` — 3 checkboxes [x] (`deployment-service@872ac2f`,
          `@545ff76`, CME per-root re-measure) + the 182,407-cell P2 candidate [x], stays `active` (1 genuine open INFRA
          leg); (4) `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md` — no checkboxes by construction, `status:
          resolved` + archived 2026-07-31 (all 3 remediation items done); (5)
          `archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md` — [AUDIT] P2 [x] (`batch2-005`) +
          Progress Log entry, `status: resolved`; (6) `issues/tradfi_backfill_oom_remediation_2026_06_24.md` — memray [TRADFI]
          P2 [x] (`market-tick-data-service@live-defi-rollout`, diagnostic), **stays `status: open`** — it carries 1
          genuinely open todo (`* [ ] [DATA] P3. MDPS's own candle-writer`, line 412, asterisk-form caught in the
          prose-form check); (7) `archive/issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md` — codex
          `manifest-consolidator-ssot.md` § "Pause-first applies to ANY canonical read-modify-write" (lines 671-695) present,
          doc `status: resolved` + archived 2026-07-30; (8)
          `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md` — [INVESTIGATE] P1 [x] + follow-up issue
          `tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`, `status: resolved`; (9)
          `issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md` — all todos [x]
          (`instruments-service@31cf3952`+`@5104befc`, `unified-trading-library@080a84a0`, `deployment-service@841f464`),
          `status: resolved`; (10)
          `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` — batch2 orphan-cleanup
          recorded in Progress Log (2026-07-28, slot 7) + "Resolution" section citing `market-tick-data-service@c24db4cf`,
          **stays `status: open`** (1 genuine open `[DESIGN] P2. aggregate ohlcv_15m/24h` decision); (11)
          `/plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md` — [TEST] P3 [x]
          (`deployment-service@077a063`), `status: complete`. **No source-doc checkbox was left unflipped; no doc reaching
          0 open todos was left un-resolved.**
          own Deferred section**, now that time has passed and the operator may have ruled on the queued decisions in
          `autonomous_session_operator_decisions_2026_07_25.md`. For each of the 5 docs listed there
          (`data_completion_tradfi_2026_07_15.md`, `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`,
          `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`,
          `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`,
          `/plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md`, plus
          `issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` (**RULED 2026-07-29: wire via forward-poll opt-in
          flag, see the issue doc — this one of the 6 is now pre-resolved, the other 5 still need the live re-check
          below**): re-read the specific conflicting todo in `tradfi_consolidated_closeout_2026_07_18.md` to check if it has
          since shipped (resolving the conflict by making the item redundant/already-covered) or if an operator ruling
          clarified which side should execute — if either, extract the item as a new tracked todo in a follow-up batch3. If
          still genuinely unresolved, leave it explicitly deferred. Also separately re-review
          `tradfi_manifest_content_recovery_completion_2026_07_24.md` (still flagged too-large/risky, excluded from both
          batch1 and batch2) and recommend whether it warrants its own dedicated batch3 triage pass yet, or whether its
          in-flight migration state still makes that premature. **Done when**: each of the 8 conflict-gated items + the 1
          operator-gated item has either (a) a new tracked todo/plan created because a conflict cleared or a ruling landed,
          or (b) an explicit re-verified confirmation the conflict/decision is still open; and a fresh recommendation is
          recorded for the large/risky doc.

- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved all resolvable ones — verify none remain unaccounted-for) → add the archive banner →
      run the codex-alignment check → grep the corpus for every referrer of
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.

## Progress Log

- **2026-08-06 (slot-10, review — todo 1 reconciliation executed)** — Ran the 11-source-doc checkbox reconciliation. All
  11 docs' batch2-corresponding checkboxes/sections were ALREADY flipped by the batch2 workers "in the same commit" (as
  their own evidence records); this session VERIFIED each flip + confirmed every cited shipped commit exists on LDR
  (`git cat-file -e` across market-tick-data-service / instruments-service / deployment-service /
  market-data-processing-service / unified-trading-library). No missing flip found; no doc reaching 0 open todos was
  left un-resolved — `tradfi_backfill_oom_remediation_2026_06_24.md` and
  `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` each retain 1 genuinely-open todo
  (MDPS candle-writer P3; aggregate-ohlcv DESIGN P2) and correctly stay `status: open`; docs 1/2/3 stay `active` with
  their genuine open todos. Full per-doc evidence in the flipped todo 1 above.
- **2026-07-30 (gate re-check, this session)** — Re-read `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` fresh (not
  from a stale prior read) to determine whether this finalize plan is now unblocked. **Result: still correctly gated,
  NOT unblocked.** Batch2 has 12 total checkboxes, 11 `[x]` done and exactly 1 (`grep -n "^- \["` confirms, line 436)
  still `[ ]`: the bundled `[OPERATOR] P2` todo ("Resolve the still-conflict-gated / operator-gated / too-large
  candidates below"). That todo carries 3 sub-parts: (a) the 8 still-genuinely-conflict-gated candidates across 5 docs —
  unresolved; (b) the `tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` operator-gated design call — **NOW
  RESOLVED**, ruled 2026-07-29 and implemented 2026-07-30 (`deployment-service@c847395e`, verified live: commit exists,
  matches the issue doc's (i)-(iv) plan exactly — `launch-tradfi-forward-poll.sh` opt-in `--mvp-mode` flag,
  `setup-data-pipeline-vm.sh` `VM_MVP_MODE` metadata plumbing, 3 new regression tests in
  `deployment-service/tests/unit/test_vm_launcher_scripts.py`, issue doc's 4 todos all `[x]` with matching evidence);
  (c) the `tradfi_manifest_content_recovery_completion_2026_07_24.md` too-large-or-risky recommendation — unresolved.
  Since (a) and (c) remain genuinely open and are unrelated to the mvp_mode ruling, the bundled todo as a whole cannot
  be flipped `[x]`, and the AO dispatcher's actual gate mechanism
  (`agent-orchestrator/server/regen_backlog_from_plan.py::_parse_open_todos`) counts any unchecked checkbox without a
  `BLOCKED-*`/`DEFERRED-BY-DESIGN`/stretch marker as genuinely open regardless of its `[TAG]` — confirmed this todo's
  continuation block carries none of those markers, so it is NOT excluded from the open-todo count. **Conclusion: batch2
  is not yet all-done; this finalize plan's `depends_on`/`gate_on_depends: true` hold is correct and unchanged. No todos
  executed in this doc — leaving as-is for the agent actively working batch2 to resolve (a) and (c), or for this gate to
  naturally clear once they do.**
- **context-scout 2026-08-03**: re-verified context_scope (5 entries, all resolving) — finalize gate, code-free; no
  changes needed.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
