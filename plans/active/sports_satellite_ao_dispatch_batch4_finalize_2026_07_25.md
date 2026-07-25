---
doc_type: plan
title: Sports satellite AO batch 4 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch4_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 3 of that plan's todos are done. Mirrors sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md's
  pattern (reconcile each distinct source doc's checkboxes independently), plus the same batch3-style addition: re-check
  the 4 conflict-gated Deferred items once the operator has ruled on entries #5-8 in
  autonomous_session_operator_decisions_2026_07_25.md — some may become dispatchable as a batch5 once the operator
  confirms which side (the narrow batch-style fix vs. the master closeout's broader claim) should execute first, or how
  the ambiguous phantom-audit/decision-16 overlap should be sequenced.
status: draft
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch4_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan, mirroring the batch2/batch3 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 4 — finalize

> **Machine-gated on `sports_satellite_ao_dispatch_batch4_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 3 tasks in that plan are `done`. `sequential: true` because
> todo 2 (conflict-gated re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P2. **Reconcile all 3 distinct source docs' checkboxes.** For each of
      `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s 3 now-done todos: flip the corresponding checkbox/section in
      its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-4 commit(s) that shipped
      it — verify the actual shipped commit exists before citing it. The 3 source docs:
      `issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md`,
      `issues/fixtures_manifest_legacy_backfill_2026_07_24.md`,
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`. For each: after flipping, re-check whether it now
      has 0 open todos remaining (checkbox AND prose-form — do not trust checkbox count alone). Only flip a doc's
      `status` to `resolved` if it genuinely reaches 0 open todos. **Done when**: all 3 source docs' corresponding
      checkboxes/sections are flipped with verified evidence, and any doc that genuinely reaches 0 open todos is flipped
      to `status: resolved`.
- [ ] [REVIEW] P2. **Resolve the 4 conflict-gated Deferred items from batch4's own doc**, now that the operator has
      (presumably) ruled on entries #5-8 in `autonomous_session_operator_decisions_2026_07_25.md`. For each of the 4
      items (`data_completion_sports_2026_07_24.md` Transfermarkt re-attempt [entry #5],
      `data_completion_sports_2026_07_24.md` ODDS+PREDICTIONS blank-reason measurement [entry #6],
      `sports_legacy_fixtures_path_migration_2026_07_24.md` fixtures-path census [entry #7],
      `issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` phantom spot-check [entry #8]): re-read the
      specific conflicting todo in `sports_consolidated_closeout_2026_07_19.md` to check if it has since shipped (which
      would resolve the conflict by making the narrower item redundant/already-covered) or if the operator's ruling
      clarified which side should execute — if either, either mark the item covered (cite the shipped commit) or extract
      it as a new tracked todo in a follow-up `batch5`. If still genuinely unresolved (operator hasn't answered yet),
      leave it explicitly deferred (not speculative) — do not re-surface it as a fresh operator-decision entry a second
      time, just note the re-check happened and it's still awaiting an answer. **Done when**: each of the 4 items has
      either (a) a new tracked todo/plan created because the conflict cleared, or (b) an explicit re-verified
      confirmation the conflict/decision is still open.
- [ ] [DOC] P3. **Archive `sports_satellite_ao_dispatch_batch4_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved all 4 or confirmed them still-open — verify none silently vanish) → add the archive
      banner → run the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the
      corpus for every referrer of `sports_satellite_ao_dispatch_batch4_2026_07_25` and fix each path to point at the
      archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
