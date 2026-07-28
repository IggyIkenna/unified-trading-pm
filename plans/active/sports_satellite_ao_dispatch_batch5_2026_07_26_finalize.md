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
      to the archived path. Source: `archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-28 — unified-trading-pm (this commit).** Re-checked all Deferred items from
      batch5's own doc via direct reads of every named target/blocker doc (not trusting batch5's own dated ruling-text
      at face value — several turned out stale). **Count correction found at pickup**: `grep -c '^- \*\*'` under
      batch5's own "## Deferred — operator decision needed" section returns **11**, not 12 — the doc's frontmatter/prose
      "12 operator-gated" claim is itself stale (same self-reported-count-drift class this session already fixed once on
      `sports_consolidated_closeout_2026_07_19.md`'s "96 open todos" note). So the real total is **4 conflict-gated + 11
      operator-gated = 15**, not 16; flagging rather than silently padding a 16th. **Conflict-gated (4)**: (1)
      `sports_legacy_duplicate_triage_2026_07_22.md` — part (a) of its RULED-2026-07-28 note is CONFIRMED DONE (§7 todo
      1 is `[x]` in the live doc); part (b) — amending the two colliding Track S snapshot-then-cull todos
      (`sports_consolidated_closeout_2026_07_19.md:519`, `sports_consolidated_native_ao_extract_2026_07_25.md:196`) to
      exclude the pre-floor range / gate on the resolved decision — is STILL UNDONE, both still read as plain
      unconditioned `[CLEANUP] P2` todos. **Ready for `batch6` extraction.** (2)
      `sports_phantom_audits_reference_not_marketdata_2026_07_14.md` — still deferred; its owning re-check
      (`batch4_finalize` todo 2) has not run — `batch4_finalize` is still `status: draft`, never dispatched. Confirmed
      still open. (3) `sports_catalog_league_grain_only_scope_2026_07_08.md` — still deferred; no operator ruling found
      on the Track S/E/V sequencing fork. Confirmed still open. (4)
      `sports_legacy_fixtures_path_migration_2026_07_24.md` — still deferred;
      `autonomous_session_operator_decisions_2026_07_25.md` (entry #7's host doc) is still `status: open` with no entry
      #7 resolution found. Confirmed still open. **Operator-gated (11)**: (5) `data_completion_sports_2026_07_24.md` —
      MIXED: the rate-limit calibration-probe todo (line 397) was already downgraded `[OPERATOR]`→`[SCRIPT] P1`
      AO-dispatchable on 2026-07-27 (finding E, vm-launcher-runbook.md), independent of and predating batch5's
      RULED-2026-07-28 note on it (redundant, not wrong). The API-Football quota-bump todo (line 801) is still plain
      `[DATA] P2` text, NOT yet retagged to reflect the RULED "proceed with bump" decision + its operator-only
      vendor-account residual. **Ready for `batch6` extraction** (the quota-bump retag half only). (6)
      `plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` — **ALREADY
      FULLY DONE, batch5's RULED-2026-07-28 note is stale.** Direct read: todos 12/13/14 are ALL `[x]` — 12 done
      2026-07-24 (found on HEAD 2026-07-27), 13 confirmed via behavioral evidence, 14 EXECUTED 2026-07-27T01:11:27Z; doc
      `status: resolved`. The remediation attempt batch5's ruling authorizes had already completed a day before the
      ruling was written. **Nothing to extract — already closed.** (7)
      `fixtures_manifest_duplicate_collision_residual_2026_07_24.md` — RULED 2026-07-28 (option 2, scoped verified
      DELETE) but NOT yet retagged: doc still `status: open`, todo still plain `[ ]` `[DIAG] P2` "decide + execute".
      **Ready for `batch6` extraction.** (8) `sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md` —
      confirmed still the correct human-only hard-stop (irreversible prod GCS delete, execution-only remaining, stays
      `[OPERATOR]`). (9) `sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md` — no new AO todo warranted: (B) is
      a doc-hygiene note per its own analysis, not new work; (C) confirmed still correctly owned by `batch2_finalize`'s
      own re-check todo (that plan is `status: active`/dispatched, but no evidence found either way that its specific
      C-extraction sub-step has run yet — correctly left to that mechanism, not front-run here); (D) confirmed still
      needs an operator design ruling, no new evidence. (10)
      `sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md` — still
      deferred; BLK-c545ae54 confirmed still only has interim guidance recorded (line 148), no final ruling found. (11)
      `sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` — still deferred; genuine multi-part design decision
      (BLK-b567ce7d), no operator ruling found. (12) `sports_group_c_execution_backtest_harness_2026_07_21.md` — still
      deferred; todo 3 (`SportsMatchingEngine` vs `L0Matcher`) confirmed still `[ ]`, no operator ruling found. (13)
      `sports_live_availability_and_source_latency_2026_07_24.md` — **ALREADY DONE.** Confirmed the doc's own todo
      (line 141) already carries the RULED-2026-07-28 retag directly as a live `[DATA] P2` AO todo, exactly as batch5's
      note claimed. **Nothing to extract — already a normal dispatchable todo in its own doc.** (14)
      `sports_predictions_live_mode_activation_readiness_2026_07_21.md` — still deferred; no operator ruling found on
      Todo 1 (pursue live sports-odds ingestion). (15) `sports_prelaunch_cf5_verify_residual_2026_07_24.md` — RULED
      2026-07-28 (option a, extend windows + backfill) but NOT yet retagged: todo 2 still reads the plain either/or
      "operator-gated" framing. **Ready for `batch6` extraction** (full-completion mandate: `SOURCE_COVERAGE_START`
      window edit + api_football sub-entity windows + propagate through consumers + re-run
      `backfill_orphan_class_e_sports.py`). **Summary**: 2 items already fully resolved (6, 13, no further action); 4
      items ready for `batch6` extraction (1b, 5-quota-bump-half, 7, 15 — named here, not drafted, per this todo's own
      instruction); 9 items confirmed still genuinely deferred (2, 3, 4, 8, 9, 10, 11, 12, 14). Every one of the 15 real
      items now carries either a ready-for-extraction note or a re-verified still-open confirmation. Repo:
      unified-trading-pm.
- [ ] [DOC] P1. **Archive `sports_satellite_ao_dispatch_batch5_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 3 above
      should have already resolved or re-confirmed all 16 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for
      every referrer of `sports_satellite_ao_dispatch_batch5_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
