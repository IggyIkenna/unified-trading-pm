---
doc_type: plan
title:
  Sports satellite AO batch 2 — finalize (reconcile all 15 source docs + resolve deferred-gate follow-ups + archive)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch2_2026_07_24.md — machine-held via depends_on + gate_on_depends:
  true until all 36 of that plan's todos are done, so this never dispatches early. Unlike
  sports_closeout_batch1_finalize_2026_07_24.md (which reconciles ONE parent — the master closeout plan), batch 2 was
  extracted from 15 DIFFERENT satellite plans/issues, so this finalize plan reconciles each of those 15 docs'
  corresponding checkboxes independently, checks batch 2's own "Deferred" section (4 real AO-eligible todos that were
  gated on something else at extraction time — 3 gated on sibling todos in this same batch, 1 gated on a human/operator
  decision) to see if any became dispatchable and should be spun into a new todo/plan, and only then runs the standard
  archival ritual on batch 2. This is the completeness pass — the goal is zero orphaned sports satellite work once this
  plan's own todos are done: every source doc's real remaining work is either shipped, re-tracked as a new explicit
  todo, or confirmed still correctly gated on a human decision.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/sports_closeout_batch1_finalize_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch2_2026_07_24]
gate_on_depends: true
source: >-
  Operator request 2026-07-24: mirror sports_closeout_batch1_finalize_2026_07_24.md's gated-reconcile-then-archive
  pattern for batch 2, so all sports satellite work is fully accounted for (no orphaned issues/docs) once every AO batch
  is dispatched, with correct parallel-vs-sequential tagging throughout.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# Sports satellite AO batch 2 — finalize

> **Machine-gated on `sports_satellite_ao_dispatch_batch2_2026_07_24.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 36 tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred-gate follow-ups) needs todo 1's reconciliation done first (to know which source docs still have real
> open work vs. are now fully closed), and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 15 source docs' checkboxes.** For each of
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s 36 now-done todos: flip the corresponding checkbox in its
      named source doc (each todo's text ends with "Source: `<doc>.md`") to `[x]`, citing the batch-2 commit(s) that
      shipped it as evidence — verify the actual shipped commit exists (`git log`/`git show`) before citing it, do not
      just copy batch-2's own evidence line. The 15 source docs are:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`,
      `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`,
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`, `data_completion_sports_2026_07_24.md`,
      `sports_legacy_cutover_closeout_tasks_2026_07_24.md`, `sports_prelaunch_cf5_verify_residual_2026_07_24.md`,
      `sports_fixtures_browser_single_catalogue_source_2026_07_24.md`,
      `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`,
      `issues/sports_legacy_duplicate_triage_2026_07_22.md`,
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`,
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`,
      `issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`,
      `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`,
      `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`, `issues/sports_league_id_namespace_migration_2026_07_20.md`.
      For each doc: after flipping, re-check whether it now has 0 open todos remaining (batch 2 was a PARTIAL extraction
      for most of these — several source docs still carry human-only/design-gated todos batch 2 deliberately excluded,
      so most will NOT reach 0). Only flip a doc's `status` to `resolved` if it genuinely reaches 0 open todos (checkbox
      AND prose-form remaining work — do not trust checkbox count alone; several docs in this corpus express real work
      as numbered prose lists, a confirmed false-hygiene-flip trap this session already hit once). **Done when**: all 15
      source docs' corresponding checkboxes are flipped with verified evidence, and any doc that genuinely reaches 0
      open todos (checkbox + prose) is flipped to `status: resolved` with `resolved_by` citing the batch-2 commit(s).
- [ ] [REVIEW] P1. **Resolve the 4 deferred-gate follow-ups from batch 2's own "Deferred" section.** For each: (1) the
      FSS↔ml-service↔strategy-service parity test (gated on 5 sibling naming-migration todos in batch 2 landing) — if
      all 5 shipped (per todo 1 above), add it as a new `- [ ]` todo in a follow-up plan (or this doc, if small enough —
      a single todo doesn't need its own plan) and dispatch it; (2) the `FixturesBrowser.tsx` relabel (gated on the
      `fixtures_browser.py` backend todo) — same treatment; (3) the `sports_dependency_check` real-backfill timing
      verification (gated on 2 sibling implementation todos) — same treatment; (4) the 3
      `sports_group_c_execution_backtest_harness_2026_07_21.md` todos (gated on the still-unmade
      SportsMatchingEngine-vs-L0Matcher human/operator decision) — check whether that decision has since been made (grep
      the source doc + `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`-style ruling docs for
      a resolution); if yes, extract those 3 as a new small AO batch; if no, leave them explicitly deferred and do NOT
      dispatch speculatively. **Done when**: each of the 4 deferred items has either (a) a new tracked todo/plan created
      and dispatched because its gate cleared, or (b) an explicit, re-verified confirmation that its gate is still open
      (not just inherited from the original extraction — re-checked as of this todo's execution).
- [ ] [DOC] P2. **Archive `sports_satellite_ao_dispatch_batch2_2026_07_24.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any DEFERRED items to a tracked todo elsewhere (todo 2 above should have
      already cleared all 4 — verify none remain) → add the archive banner → run the codex-alignment check (do any codex
      docs need a status update now that these 36 items shipped — e.g. the WEATHER layout fix, the odds-feature naming
      migration) → update CLAUDE.md/codex if any new durable contract resulted → grep the corpus for every referrer of
      `sports_satellite_ao_dispatch_batch2_2026_07_24` (including this doc's own `depends_on` self-reference and any of
      the 15 source docs' `related:` links added during extraction) and fix each path to point at the archived location
      → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`,
      every corpus referrer resolves to the new path, and this doc itself gets archived alongside it in the same commit
      (both batch 2 and its finalize plan are done at that point — no reason to keep the finalize plan active once it
      has nothing left to gate).
