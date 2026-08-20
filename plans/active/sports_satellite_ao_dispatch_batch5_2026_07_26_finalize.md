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
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch4_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-08-20"
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
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/archive/issues/defi_batch8_finalize_gate_bypass_missing_upstream_task_2026_08_02.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
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
- [ ] [DOC] P1. **BLOCKED 2026-07-29 (slot-8) — same gate as todo 4 below (operator ruling Option A, BLK-c6efc083).**
      This finalize closeout stays parked until `sports_satellite_ao_dispatch_batch5_2026_07_26` reaches 0 open todos
      (its 2 open active items, lines 79 + 91). Checkbox stays `[ ]`; original task follows. **Reconfirmed
      2026-07-30T00:35Z (slot 11, data_engineering): gate still genuinely open, not stale.** Direct re-read of
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md`: line 79 is now `[x]` (done 2026-07-29, slot-15 — the odds-api
      backfill re-run). But its other active item (the `[DATA] P2` zombie-tick purge/re-derive + ML-readiness
      gate-semantics fix) is still `[ ]` — genuinely unexecuted real work (not a time-based wait), so batch5 has 1 open
      todo, not 0. Its own prerequisite (batch4's read-only sweep report) IS now available (batch4's `[DIAG] P1` sweep
      todo shipped `market-tick-data-service@76ca401f`, done 2026-07-27) — so the remaining batch5 todo is itself now
      dispatchable, it just hasn't been picked up/executed yet. This finalize closeout has nothing further for THIS todo
      to do until that separate batch5 todo lands. Releasing via `/skip-current-task {"reason_code": "GATED"}`. Next
      dispatch: re-check once batch5's zombie-tick todo flips `[x]`. **Reconfirmed 2026-07-31 (slot 3,
      data_engineering): gate still open, zero drift since slot 11's check.** Direct re-read of
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md` shows its zombie-tick todo still `[ ]`, no commits landed
      against it in the interim. Also pre-resolved the archiving requirement below: the one doc todo 1 flipped to
      `status: resolved` (`sports_t6_8_oneoff_retirement_residual_2026_07_25.md`) is already archived at
      `plans/archive/issues/sports_t6_8_oneoff_retirement_residual_2026_07_25.md` — nothing outstanding there. Releasing
      again via `/skip-current-task {"reason_code": "GATED"}`. **Reconfirmed 2026-07-31T10:57Z (slot 16,
      data_engineering): gate still open, zero drift since slot 3's check.** Direct re-read of
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md`: the zombie-tick purge/re-derive + ML-readiness gate-semantics
      todo (line 107) is still `[ ]` — no commits landed against it. Confirmed no `slot_done` activity in the last 30
      events references this todo or batch5 either. Its own input (batch4's read-only sweep report,
      `market-tick-data-service@76ca401f`, done 2026-07-27) remains available, so that todo is itself dispatchable as
      its own backlog task derived from batch5's doc — just not yet picked up/executed. Releasing again via
      `/skip-current-task {"reason_code": "GATED"}`. **Reconfirmed 2026-08-02 (slot 14, data_engineering) — root cause
      of the 4+ day stall found: it was never "not yet picked up," it structurally could not be picked up.** A full
      `GET /api/backlog` scan (1337 tasks) found **zero** tasks matching this todo's content anywhere — the only task
      ever derived for `sports_satellite_ao_dispatch_batch5_2026_07_26.md` is an orphan
      (`sports_satellite_ao_dispatch_batch5-024`, `done_at: 2026-07-26T01:27:01Z`, done 3 minutes after queuing —
      clearly a much simpler pre-reword version of this todo). The regen correctly orphaned the stale row once the text
      was expanded to today's substantial multi-part description, but never derived a fresh task for the new wording —
      every prior "genuinely dispatchable, just not picked up" verdict (slots 11/3/16) was a reasonable read at the time
      but is now known to be off by one level: dispatchability itself was the missing piece. Filed as corroborating
      evidence (not a new doc — same shape, second independent case) in
      `/plans/archive/issues/defi_batch8_finalize_gate_bypass_missing_upstream_task_2026_08_02.md`'s Progress Log
      (unified-trading-pm commit follows) — both this todo and that doc's affected todo share the identical shape
      (bolded multi-clause description immediately after the priority marker, followed by lettered sub-parts spanning
      many lines), strengthening that doc's own parser-shape hypothesis. Releasing again via
      `/skip-current-task {"reason_code": "GATED"}` — nothing this data_engineering task can do until the
      agent-orchestrator backend fix lands and a fresh task actually derives. **Reconfirmed 2026-08-02 (slot 9,
      data_engineering): zero drift, and the shared root cause is now narrower than the parser-shape hypothesis.**
      Fresh-pulled to latest `live-defi-rollout` first. The zombie-tick todo text (this doc's line 114-138) is still
      `[ ]`, and `GET /api/backlog` still shows only the same stale orphan (`sports_satellite_ao_dispatch_batch5-024`,
      `done_at: 2026-07-26T01:27:01Z`) — no fresh task derived. The sibling defi doc's own investigation (todo 1, slot
      15, `2026-08-02T16:03Z`) has since REFUTED the parser-shape hypothesis for its own case and found a different,
      narrower cause instead (a word-order bug in `_is_non_dispatchable`'s `BLOCKED-<TOKEN>` stale-marker lookback —
      only catches keyword-before-marker phrasing). Checked whether that exact mechanism applies here too: this todo's
      own continuation block (lines 114-138) contains **no `BLOCKED-` token at all** — so this is likely a genuinely
      DIFFERENT non-derivation cause sharing only the surface symptom, not automatically fixed by that same regex patch
      once it lands. Flagging for whoever picks up the defi doc's todo 2 fix: re-test THIS todo specifically after the
      word-order patch, don't assume one fix covers both. Separately: this is dispatch #6 for this exact gated todo
      (slots 8, 11, 3, 16, 14, now 9) — the todo's own text above cites an auto-park threshold of 3 BLOCKED/GATED
      declines, which this has exceeded by 2x without auto-parking; noting as a possible second, independent dispatcher
      gap, not investigating further (outside this task's scope). Releasing again via
      `/skip-current-task {"reason_code": "GATED"}`. **Reconfirmed 2026-08-02T16:14Z (slot 10, data_engineering) —
      dispatch #7, zero drift, escalated for a manual park.** `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s
      zombie-tick todo still `[ ]`; `agent-orchestrator` HEAD still `2b0b9e9` (same as when the defi sibling's fix was
      last checked this session) — neither the parser-shape nor the word-order-bug fix has landed yet. This is now 7
      dispatches (slots 8, 11, 3, 16, 14, 9, now 10) against a stated auto-park-at-3 threshold, more than double with no
      auto-park firing. Rather than re-confirm a 8th time later, messaged main directly requesting a manual park (per
      RULES.md § "Park a task" — a main/operator action, not something this data_engineering task should hand-edit)
      until the backend fix lands. Releasing again via `/skip-current-task {"reason_code": "GATED"}`. **Archive every
      source doc todo 1 drives to `status: resolved`/`complete` — in the same commit as the flip, never left sitting in
      `plans/active/`.** `check_terminal_status_archived.py` HARD-fails on any doc whose frontmatter reads a terminal
      status while it still lives under `plans/active/` (including `plans/active/issues/`) — the omission of this exact
      step across the sports finalize-plan family already forced one such HARD-fail: the `plan_health` gate's own
      remediation (`unified-trading-pm@57ed9271c`, escalation `agt-9a5061`, PR #1545) auto-archived 11 docs nobody's
      plan owned. For every source doc todo 1 flips to `resolved` with 0 open todos: re-verify the 0-open-todos count
      and the resolution banner one more time, then archive it to `plans/archive/2026_07/` IN THE SAME COMMIT as the
      status flip — fix every corpus referrer of the archived doc's pre-archive path (grep for the basename). If todo 1
      already ran before this todo existed in the plan, archive any already-`resolved`-but-still-active doc now, noting
      the flip predated this rule. **Done when**: no source doc this plan drives to a terminal status remains under
      `plans/active/`, `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures, and every corpus
      referrer resolves to the archived path. Source:
      `archive/issues/sports_plan_reconcile_operator_decisions_2026_07_26.md` § 2.
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
      `sports_legacy_fixtures_path_migration_2026_07_24.md` (now archived at `/plans/archive/2026_08/`) — still
      deferred; `autonomous_session_operator_decisions_2026_07_25.md` (entry #7's host doc) is still `status: open` with
      no entry #7 resolution found. Confirmed still open. **Operator-gated (11)**: (5)
      `data_completion_sports_2026_07_24.md` — MIXED: the rate-limit calibration-probe todo (line 397) was already
      downgraded `[OPERATOR]`→`[SCRIPT] P1` AO-dispatchable on 2026-07-27 (finding E, vm-launcher-runbook.md),
      independent of and predating batch5's RULED-2026-07-28 note on it (redundant, not wrong). The API-Football
      quota-bump todo (line 801) is still plain `[DATA] P2` text, NOT yet retagged to reflect the RULED "proceed with
      bump" decision + its operator-only vendor-account residual. **Ready for `batch6` extraction** (the quota-bump
      retag half only). (6)
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
- [ ] [DOC] P1. **CORRECTED 2026-08-19 (`/plan-reconcile sports_master`): the gate below cleared 2026-08-09, ten
      days ago — this BLOCKED framing is stale.** Direct re-read of `sports_satellite_ao_dispatch_batch5_2026_07_26.md`
      today: both its `## Todos` items are now `[x]` (line 79's odds-api backfill done 2026-07-29 per that doc's own
      text; the zombie-tick/ML-readiness todo flipped 2026-08-09 per
      `sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`'s Progress Log,
      "Flipping `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s zombie-tick checkbox now"). Batch5 itself
      already carries a matching 2026-08-12 banner confirming 0 open todos, but explicitly left the archival to
      "whoever clears the finalize twin's remaining gates" — this doc is that clearing, not yet executed. The gate
      condition below (`sports_satellite_ao_dispatch_batch5_2026_07_26` reaching 0 open todos) IS satisfied — what
      remains is the substantial reconciliation work itself (25+ distinct source-doc checkboxes per todo 1 above),
      which this pass did not attempt (out of scope for a doc-reconciliation audit). Flagging as ready-to-dispatch,
      not archiving unilaterally.
      **Original BLOCKED note (2026-07-29 (slot-8, `data_engineering`), superseded by the correction above, kept for
      history):** batch5 is NOT archivable yet; premature (operator
      ruling Option A, BLK-c6efc083).** `sports_satellite_ao_dispatch_batch5_2026_07_26.md` still carries **2
      genuinely-open active `[ ]` todos** in its `## Todos` section (NOT the Deferred sections todo 3 re-confirmed), so
      archiving it now would violate the plans-run-to-actual-completion HARD RULE ("not smoke-test green"): (line 79)
      `[DATA] P2` **credential-blocked (at the time)** odds-api backfill of 3 leagues — odds-api key deactivated, fully tracked in
      the now-`/plans/archive/issues/sports_odds_api_key_deactivated_2026_07_26.md` — **UPDATE 2026-07-29: the
      credential itself is now fixed** (operator rotated `odds-api-key` to a new 5,000,000-credits/month-subscription
      key, live-verified HTTP 200) — line 79 is no longer `BLOCKED-CREDENTIALS`/operator-gated, it's a genuinely
      dispatchable P1 backfill re-run that just hasn't executed yet. **FURTHER UPDATE 2026-07-29 (slot-15): line 79 IS
      now done** — backfill re-run executed and verified (UCL + CHINA_SUPER_LEAGUE fully captured, 0 `attempted_failed`;
      RUSSIA_PREMIER_LEAGUE confirmed a permanent vendor coverage gap, not a defect — see
      `/plans/archive/issues/sports_odds_api_key_deactivated_2026_07_26.md`). Only line 91 remains open now — still
      gated on batch4's sweep report, so this BLOCKED verdict (batch5 not yet archivable) still stands; and (line 91)
      `[DATA] P2` zombie-tick purge/re-derive + ML-readiness gate-semantics fix — **active-not-started**, gated on
      `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s read-only P1 sweep report (batch4 still `status: active`, 1
      open todo, so line 91 cannot even start). Neither qualifies for the 6-step ritual's DEFERRED-migration (line 91 is
      active-not-started; line 79 is now dispatchable-but-not-yet-run) — do NOT archive, do NOT migrate-to-pass (Option
      B rejected as the smoke-test-green anti-pattern). **Depends on `sports_satellite_ao_dispatch_batch5_2026_07_26`
      reaching 0 open todos** (lines 79 + 91 closed). Structural note: this todo was dispatched prematurely because
      `gate_on_depends` gates ARCHIVAL + documents ordering but does NOT block DISPATCH — expected to self-heal via the
      auto-park machinery (`server/auto_park.py`, threshold=3 BLOCKED/GATED declines). Checkbox stays `[ ]`. Original
      task follows. **Archive `sports_satellite_ao_dispatch_batch5_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 3 above
      should have already resolved or re-confirmed all 16 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for
      every referrer of `sports_satellite_ao_dispatch_batch5_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- added the actual root-cause doc for this plan's
  own multi-dispatch GATED stall (dispatcher never derives a fresh task for the reworded batch5 zombie-tick todo).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries) -- 4th scout pass; re-verified all 6
  entries still resolve on disk and remain the correct minimal set; unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
