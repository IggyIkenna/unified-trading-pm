---
doc_type: plan
title: Sports satellite AO batch 5 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch5_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 25 of that plan's todos are done. Mirrors batch3/batch4-finalize's pattern (reconcile each distinct
  source doc's checkboxes independently once its batch-5 todo lands, then re-check the Deferred conflict-gated +
  operator-gated items for any that have since cleared), then archives batch5 via the standard 6-step ritual.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch4_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: sports_master
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
depends_on: [sports_satellite_ao_dispatch_batch5_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched
  plan needs a companion gated finalize plan, mirroring the batch2/batch3/batch4 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 5 — finalize

> **Machine-gated on `sports_satellite_ao_dispatch_batch5_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 25 tasks in that plan are `done`. `sequential: true` because
> todo 2 (source-doc archival) needs todo 1's reconciliation done first (a doc can only be archived once its status is
> genuinely flipped to `resolved`), todo 3 (deferred re-check) needs todo 1's reconciliation too, and todo 4 (archival
> of this batch's own plan) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-28 (slot-2, `data_engineering`).** Verified all 24 distinct source docs (23 from
      the archived completed-todos history + the `sports_curated_universe_faroe_wales_leagues` item, plus the 2
      additional docs behind the "2 todos cite two source docs" note —
      `sports_odds_feature_naming_canonicalization_2026_07_21.md` todo 8 and its sibling
      `sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md`) via 8 parallel read-only research
      passes cross-checking every cited commit SHA against live git history, then applied 6 fixes for genuine drift
      found (most of the 24 were already correctly flipped): (1) filled an unfilled `<sha>` placeholder in
      `mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md` with the verified real SHA
      `market-tick-data-service@25916f6e`; (2) flipped `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s
      todo 8 (`ml-service@10e219f`, verified); (3) annotated
      `sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md` noting its todo's sub-parts 1+2
      are now moot (already independently reconciled) while sub-part 3 stays a genuine judgment call; (4) updated
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`'s E8 line — was still untouched
      reading "UNIMPLEMENTED stub" despite the code shipping — added the DONE-FOR-CODE/ BLOCKED-OPERATOR state
      (`market-tick-data-service@08439787`+`@236d945e`, verified), checkbox correctly stays unchecked (apply not fired);
      (5) flipped 2 stale-but-actually-shipped checkboxes + added a SUPERSEDED note to a stale RE-TRIAGE section in
      `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` (`features-service@4f365d23`, verified) — sub-item (c) retrain
      correctly stays open; (6) flipped 2 stale-but-shipped checkboxes in
      `sports_t6_8_oneoff_retirement_residual_2026_07_25.md` (`instruments-service@5ff530f9`+`@4987e465`, both
      verified + live re-confirmed zero workspace-wide `include_legacy_archive` hits) and flipped that doc's own
      `status` to `resolved` (0 open todos remaining). Every other doc checked (14 more) was already correctly
      flipped/archived with 0 open todos where genuinely done, or correctly left open/partial where real work remains
      (e.g. `canonical_player_stats_fixture_events_quality_2026_07_16.md` — Finding 1 resolved but Finding 2/Defect 3
      genuinely still open; `sports_features_layer_findings_sweep_2026_07_18.md`'s 3-part split — 23 genuinely open
      across the 3 parts). No doc was flipped to `resolved` status without independently re-verifying it reaches 0 open
      todos (checkbox AND prose-form). **Reconcile all 25 distinct source docs' checkboxes.** For each of
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s now-done todos: flip the corresponding checkbox/section in
      its named source doc(s) (each todo's text ends with "Source: `<doc>.md`" — 2 todos cite two source docs each, the
      ml-service odds-feature-naming migration and the T2.9/T2.10 MDT schema-drift fix; flip both cited docs for those),
      citing the batch-5 commit(s) that shipped it — verify the actual shipped commit exists before citing it. For each
      source doc: after flipping, re-check whether it now has 0 open todos remaining (checkbox AND prose-form — do not
      trust checkbox count alone). Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open todos. **Done
      when**: all 25+ source-doc checkboxes/sections are flipped with verified evidence, and any doc that genuinely
      reaches 0 open todos is flipped to `status: resolved`.
- [ ] [DOC] P1. **Archive every source doc todo 1 drives to `status: resolved`/`complete` — in the same commit as the
      flip, never left sitting in `plans/active/`.** `check_terminal_status_archived.py` HARD-fails on any doc whose
      frontmatter reads a terminal status while it still lives under `plans/active/` (including `plans/active/issues/`)
      — the omission of this exact step across the sports finalize-plan family already forced one such HARD-fail: the
      `plan_health` gate's own remediation (`unified-trading-pm@57ed9271c`, escalation `agt-9a5061`, PR #1545)
      auto-archived 11 docs nobody's plan owned. For every source doc todo 1 flips to `resolved` with 0 open todos:
      re-verify the 0-open-todos count and the resolution banner one more time, then archive it to
      `plans/archive/2026_07/` IN THE SAME COMMIT as the status flip — fix every corpus referrer of the archived doc's
      pre-archive path (grep for the basename). If todo 1 already ran before this todo existed in the plan, archive any
      already-`resolved`-but-still-active doc now, noting the flip predated this rule. **Done when**: no source doc this
      plan drives to a terminal status remains under `plans/active/`,
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures, and every corpus referrer resolves
      to the archived path. Source: `issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2.
- [ ] [REVIEW] P1. **Re-check the 4 conflict-gated + 12 operator-gated Deferred items from batch5's own doc**, now that
      time has passed and batch5's own todos have landed (some of which may resolve a Deferred item's blocker as a side
      effect — e.g. `sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`'s item C is explicitly gated on
      batch2_finalize's own re-check mechanism, which may have already run by the time this executes). For each of the
      16 Deferred items: re-read the specific conflicting/gating ground to check if it has since shipped, been ruled on
      by the operator, or otherwise cleared — if so, extract it as a new tracked todo in a follow-up `batch6` (do not
      draft it directly here, this finalize plan's own scope is reconciliation not fresh drafting); if still genuinely
      unresolved, leave it explicitly deferred (not speculative) — do not re-surface it as a fresh operator-decision
      entry a second time if already asked, just note the re-check happened and it's still awaiting an answer. **Done
      when**: each of the 16 Deferred items has either (a) a note that it's ready for `batch6` extraction because its
      blocker cleared, or (b) an explicit re-verified confirmation the conflict/decision is still open.
- [ ] [DOC] P1. **Archive `sports_satellite_ao_dispatch_batch5_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 3 above
      should have already resolved or re-confirmed all 16 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for
      every referrer of `sports_satellite_ao_dispatch_batch5_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
