---
doc_type: plan
title: Sports satellite AO batch 3 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch3_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 12 of that plan's todos are done. Mirrors sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md's
  pattern (reconcile each of the 8 distinct source docs' checkboxes independently), plus one batch3-specific addition:
  re-check the 6 conflict-gated Deferred items once the operator has ruled on the queued decision in
  autonomous_session_operator_decisions_2026_07_25.md — some may become dispatchable once the operator confirms which
  side (the narrow batch3-style fix vs. the master closeout's broader claim) should execute first.
status: draft
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
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
depends_on: [sports_satellite_ao_dispatch_batch3_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan, mirroring the batch2/batch2_finalize precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 3 — finalize

> **Machine-gated on `sports_satellite_ao_dispatch_batch3_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 12 tasks in that plan are `done`. `sequential: true` because
> todo 2 (conflict-gated re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P2. **Reconcile all 8 distinct source docs' checkboxes.** For each of
      `sports_satellite_ao_dispatch_batch3_2026_07_25.md`'s 12 now-done todos: flip the corresponding checkbox/ section
      in its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-3 commit(s) that
      shipped it — verify the actual shipped commit exists before citing it. The 8 source docs:
      `issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`,
      `issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md`,
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md` (6 of the 12 todos),
      `data_completion_sports_2026_07_24.md`, `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` (2
      todos). For each: after flipping, re-check whether it now has 0 open todos remaining (unlikely for most — batch3
      was a small conflict-cleared slice of each doc's real remaining work). Only flip a doc's `status` to `resolved` if
      it genuinely reaches 0 open todos (checkbox AND prose-form — do not trust checkbox count alone). **Done when**:
      all 8 source docs' corresponding checkboxes/sections are flipped with verified evidence, and any doc that
      genuinely reaches 0 open todos is flipped to `status: resolved`.
- [ ] [REVIEW] P2. **Resolve the conflict-gated Deferred section from batch3's own doc**, now that the operator has
      (presumably) ruled on the queued decision in `autonomous_session_operator_decisions_2026_07_25.md`. For each of
      the 6 conflict-gated docs (`data_completion_sports_2026_07_24.md` 2 items,
      `sports_legacy_fixtures_path_migration_2026_07_24.md` 1 item,
      `issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md` 1 item,
      `issues/fixtures_manifest_legacy_backfill_2026_07_24.md` 1 item,
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md` 1 item,
      `issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` 1 item): re-read the specific conflicting
      todo in `sports_consolidated_closeout_2026_07_19.md` to check if it has since shipped (which would resolve the
      conflict by making the narrower item redundant/already-covered) or if the operator's ruling clarified which side
      should execute — if either, either mark the item covered (cite the shipped commit) or extract it as a new tracked
      todo in a follow-up batch. If still genuinely unresolved, leave it explicitly deferred (not speculative). Also
      separately review the 2 `doc_too_large_or_risky_for_batch` docs
      (`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`,
      `issues/sports_features_layer_findings_sweep_2026_07_18.md`) and recommend whether they warrant their own
      dedicated batch4 triage pass. **Done when**: each of the 6 conflict-gated items has either (a) a new tracked
      todo/plan created because the conflict cleared, or (b) an explicit re-verified confirmation the conflict is still
      open; and a recommendation is recorded for whether the 2 large/risky docs need their own batch4 pass.
- [ ] [DOC] P3. **Archive `sports_satellite_ao_dispatch_batch3_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved all 6 — verify none remain) → add the archive banner → run the codex-alignment check
      (does `sports-features-bucket-path-ssot.md` under `codex/02-data/`, created by this batch's own todo 5, need any
      further cross-referencing) → grep the corpus for every referrer of
      `sports_satellite_ao_dispatch_batch3_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
