---
doc_type: plan
title: Sports satellite AO batch 14 — finalize (reconcile source docs)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch14_2026_08_16.md — machine-held via depends_on +
  gate_on_depends: true until all 10 of that plan's todos are done. Mirrors the batch2-12-finalize pattern: reconcile
  each of the 11 distinct source docs' checkboxes once its batch-14 todo lands (archiving the ones that end up with
  zero remaining open work; leaving genuinely-partial docs open with their evidence added), then archive both docs.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-14, satellite-docs, ag-closeout-audit]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch14_2026_08_16.md,
    /plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md,
    /plans/active/issues/sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    /plans/active/issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md,
    /plans/active/issues/sports_track_o_attempted_at_keys_extinct_2026_08_14.md,
    /plans/active/sports_taxonomy_p2_consumer_inventory_2026_08_12.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/issues/sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md,
    /plans/active/issues/sports_honest_coverage_gap_closure_2026_08_14.md,
    /plans/active/issues/dp_vm_001_mdps_sports_2026_staleness_guard_and_timeouts_2026_08_16.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.7
estimate_calibrated_ai_days: 0.28
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch14_2026_08_16]
gate_on_depends: true
source: >-
  ag-closeout-audit sports pass (2026-08-16, dispatch agt-6704de), per task_template.md §4's finalize-plan-coverage
  rule — every assigned_vm: planning plan needs a companion gated finalize plan. Authored status: active from the
  start (not draft) per the 2026-07-30 no-double-gate finding: gate_on_depends already machine-holds every todo below
  regardless of the parent batch's own status (including while it still sits draft), so a second manual flip on this
  doc would be redundant.
assigned_role: data_engineering
effort: medium
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch14_2026_08_16.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports satellite AO batch 14 — finalize (reconcile source docs)

## Todos

- [ ] [DATA] P3. Reconcile `footystats_matches_predictions_fetch_gaps_2026_07_08.md` — once batch-14 todo 1 lands,
      flip its todo #4 checkbox with the cited evidence; if no other open items remain, archive it (6-step ritual).
      Source: `footystats_matches_predictions_fetch_gaps_2026_07_08.md`. Done when: the checkbox is flipped with
      evidence, and the doc is archived if fully done.
- [ ] [DATA] P3. Reconcile `sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md` AND
      `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`'s Track-V item — once batch-14 todo 2
      lands, flip both docs' respective checkboxes with the cited row-count/diagnosis evidence. Archive
      `sports_catalogue_reroll_2019_corpus_scale_killed_2026_08_15.md` if that was its only open item.
      `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md` stays open (its §M and G-ops items remain
      unaddressed). Sources: both docs above. Done when: both checkboxes are flipped with evidence, and the fully-done
      doc is archived.
- [ ] [DATA] P3. Reconcile `sports_cf8_available_at_backfill_regression_2026_07_13.md` — once batch-14 todo 3 lands,
      flip its checkbox with the cited post-run verification for both surfaces; archive if no other open items
      remain. Source: `sports_cf8_available_at_backfill_regression_2026_07_13.md`. Done when: the checkbox is flipped
      with evidence, and the doc is archived if fully done.
- [ ] [DATA] P3. Reconcile `sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`
      — once batch-14 todo 4 lands, flip both its open items' checkboxes with the cited root-cause/fix and
      ownership-resolution evidence; archive if no other open items remain. Source:
      `sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`. Done when: both
      checkboxes are flipped with evidence, and the doc is archived if fully done.
- [ ] [DATA] P3. Reconcile `sports_track_o_attempted_at_keys_extinct_2026_08_14.md` — once batch-14 todo 5 lands, flip
      its checkbox (and the "Recommended decision" prose step, converted to a checkbox by todo 5 itself) with the
      cited dry-run join result; archive if no other open items remain. Source:
      `sports_track_o_attempted_at_keys_extinct_2026_08_14.md`. Done when: the checkbox is flipped with evidence, and
      the doc is archived if fully done.
- [ ] [DATA] P3. Reconcile `sports_taxonomy_p2_consumer_inventory_2026_08_12.md` — once batch-14 todo 6 lands, flip
      the §6/cross-cutting-finding-#5 item with the cited commit + regression test; archive only if this was
      confirmed to be the doc's sole remaining open item. Source: `sports_taxonomy_p2_consumer_inventory_2026_08_12.md`.
      Done when: the checkbox is flipped with evidence, and the doc's remaining-open-work status is confirmed
      (archived if none, left open with a note if other items remain).
- [ ] [DATA] P3. Reconcile `sports_league_id_namespace_migration_2026_07_20.md` — once batch-14 todo 7 lands, flip
      the per-fixture `league_id`-resolution-bug item with the cited commit + regression test. Do NOT archive — Track
      H and STEP 9's human-gated delete remain genuinely open in this doc. Source:
      `sports_league_id_namespace_migration_2026_07_20.md`. Done when: the one checkbox is flipped with evidence and
      the doc is confirmed to remain open (Track H / STEP 9 untouched).
- [ ] [DATA] P3. Reconcile `sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md` — once batch-14 todo 8
      lands, write the census result (real vs. phantom population, row counts) into item 1 and flip its checkbox. Do
      NOT archive — item 2 (the operator rewrite-vs-accept decision) remains open. Source:
      `sports_odds_data_type_casing_wider_than_odds_api_2026_08_15.md`. Done when: item 1's checkbox is flipped with
      the census evidence and the doc is confirmed to remain open.
- [ ] [DATA] P3. Reconcile `sports_honest_coverage_gap_closure_2026_08_14.md` — once batch-14 todo 9 lands, flip
      items 1, 2, and 4's checkboxes with the cited evidence. Do NOT archive and do NOT touch items 3 or 5 — both
      remain genuinely open (item 3 self-dispatched elsewhere, item 5 operator-gated). Source:
      `sports_honest_coverage_gap_closure_2026_08_14.md`. Done when: items 1/2/4 are flipped with evidence and items
      3/5 are confirmed untouched.
- [ ] [DATA] P3. Reconcile `dp_vm_001_mdps_sports_2026_staleness_guard_and_timeouts_2026_08_16.md` — once batch-14
      todo 10 lands, flip items 2 and 3's checkboxes with the cited commit/test + investigation conclusion. Do NOT
      archive and do NOT touch item 1 (time/operator-gated). Source:
      `dp_vm_001_mdps_sports_2026_staleness_guard_and_timeouts_2026_08_16.md`. Done when: items 2/3 are flipped with
      evidence and item 1 is confirmed untouched.
- [ ] [PROCESS] P2. Archive `sports_satellite_ao_dispatch_batch14_2026_08_16.md` + this finalize doc once all 10
      reconciliations above are done and batch-14's own 10 todos are all `[x]`. Done when: both docs sit in
      `plans/archive/2026_08/` with the archive-ritual citation.

## Codex SSOTs

- /plans/active/task_template.md §4 — finalize-plan-coverage rule
- /codex/12-agent-workflow/plan-completion-and-archival-discipline.md — the 6-step archival ritual

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries) -- re-verified both entries still
  resolve on disk; no change.
