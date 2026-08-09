---
doc_type: plan
title: Sports satellite AO batch 9 — /ag-closeout-audit orphan extraction (2026-08-04)
summary: >-
  Ninth AO-dispatch batch for sports, produced by a fresh `/ag-closeout-audit sports` run (2026-08-04): 57 sports
  AG-primary docs classified via a per-doc Workflow pass (Phase 1), 42 came back orphaned (23 partial coverage, 19 never
  touched by any covering plan), and every orphaned doc's remaining items were then taxonomy-classified +
  conflict-checked against the full covering-plan set (batch2/5/6/7/8 + finalizes, the 3 line-cap-split forks, the
  native-AO-extract pair, the legacy-fixtures-path and live-availability pairs, and the consolidated closeout itself)
  via a second Workflow pass (Phase 3). 33 items cleared the conflict-check as genuinely uncovered and bounded; the
  6-item sequential investigation chain in `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md` was
  consolidated to 3 combined todos per the skill's same-source-doc sequencing rule, yielding the 30 todos below. The
  remaining 84 items across the same 42 docs are non-batchable (42 operator-gated, 21 conflict-gated, 14 time-gated, 5
  too-large-or-risky, 2 human-only) and are recorded in the Deferred section, not dropped. One orthogonality mistag
  (`sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`, single-AG+ cross-cutting) was fixed
  directly during Phase 0 (shipped `unified-trading-pm@5051ba2ed`, outside this batch). A second corpus-hygiene fix
  (adding missing `prediction`/`defi` tags to `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`, whose
  residual open work is genuinely those tranches' scope, not sports') shipped alongside this batch's own commit.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    deployment-service,
    unified-trading-library,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
    unified-api-contracts,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-9, satellite-docs, ag-closeout-audit]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/archive/2026_08/issues/instrument_availability_league_and_question_group_partition_shapes_2026_08_03.md,
    /plans/archive/issues/manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md,
    /plans/active/issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md,
    /plans/active/issues/mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md,
    /plans/archive/issues/mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md,
    /plans/archive/issues/ml_service_pipeline_handler_clv_target_bypasses_odds_targets_merge_2026_08_03.md,
    /plans/active/issues/mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md,
    /plans/archive/2026_08/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    /plans/archive/issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md,
    /plans/active/issues/sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md,
    /plans/archive/issues/sports_enrichment_closer_holiday_and_today_false_gaps_2026_08_03.md,
    /plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md,
    /plans/archive/2026_08/issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md,
    /plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md,
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-06"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 5.5
estimate_calibrated_ai_days: 4.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit sports tranche run, 2026-08-04 — scheduled ag_closeout_auditor dispatch (agt-7322c2). Phase 1
  (57-doc classification) + Phase 3 (42-doc taxonomy + conflict-check) both ran via Workflow fan-out per
  cursor-configs/skills/ag-closeout-audit/SKILL.md's documented autonomous-mode procedure.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
---

# Sports satellite AO batch 9 — `/ag-closeout-audit` orphan extraction (2026-08-04)

> **Status: active** — operator-approved 2026-08-06, dispatching. This draft sat unreviewed for 2 days with zero
> Progress Log entries; a governance-sweep activation-readiness check spot-checked 3 code-citing todos and found 2
> already shipped (now struck below, citing the landing commits) — the odds-coverage-filter todo and the
> SPOT-provisioning-flag todo. **The remaining 28 todos were NOT individually re-verified in that pass** (only
> spot-checked, per the check's own scope) — if a dispatched worker finds one already done, strike it with a citation
> the same way rather than treating this banner as a guarantee every other todo is still current. All 30 todos are
> same-priority-independent and touch distinct files/repos (verified individually per todo during Phase 3's
> conflict-check; the one internally-sequential exception,
> `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`'s 3 combined todos, is called out inline) so
> they are safe to dispatch concurrently.

## Methodology

Full `/ag-closeout-audit sports` Phase 0-3 run, 2026-08-04. Phase 0 discovered 23 real covering docs (consolidated
closeout + batch2/5/6/7/8 + finalizes + the 3 line-cap-split forks + the native-AO-extract pair + the legacy-fixtures
and live-availability pairs). Phase 0.3's Orthogonality HARD CHECK caught and fixed one single-AG+cross-cutting mistag
(shipped separately, `unified-trading-pm@5051ba2ed`). Phase 1 classified all 57 sports AG-primary candidate docs (21
deterministically excluded as multi-AG/cross-cutting pre-filter, plus 2 more excluded by real-content judgment) via a
per-doc Workflow agent: 3 archivable_now, 10 archivable_after_planned_work (already covered by an open todo elsewhere),
23 orphaned_partial_coverage, 19 orphaned_never_touched. Phase 3 ran the shared conflict-check protocol
(`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) against all 42 orphaned docs'
remaining items (117 total), taxonomy-classifying each: 33 ao_eligible (conflict-clear, bounded), 42 operator_gated, 21
conflict_gated (already claimed elsewhere), 14 time_gated, 5 too_large_or_risky, 2 human_only.

## Todos

- [x] ✅ [SCRIPT] P1. Run the shipped ramp-to-429 rate-limit calibration harness
      (`instruments-service/scripts/calibrate_source_rate_limit.py`) from a throwaway ephemeral VM IP for understat /
      transfermarkt / open_meteo / soccer_football_info / polymarket_clob / polymarket_gamma_api (never a prod IP), then
      transcribe each measured `safe_rate_rpm` + `recovery_seconds` into `launch_budget_registry.py`
      (`SOURCE_RATE_LIMITS_RPM` for fleet-divided sources, `SOURCE_PER_IP_LIMITS` for per-IP sources), flip
      `calibrated=True`, and drop the `# TODO: empirically calibrate` markers. Source:
      `data_completion_sports_2026_07_24.md`. Done when: the probe has run to completion for all 6 sources,
      `launch_budget_registry.py` carries measured safe_rate_rpm/recovery_seconds with `calibrated=True` for each, and
      the measured table is recorded in the plan's Progress Log. — deployment-service@0eb9c36 + instruments-service
      secret-fix quickmerged (rapidapi-key → soccer-football-info-api-key). See Progress Log below.
- [ ] [DATA][BLOCKED-UPSTREAM-OUTAGE] P2. Re-launch the instruments-service Transfermarkt PLAYER_VALUES backfill scoped
      to the golden window (2025-09-01..2025-11-30) with skip-fresh enabled so only the 256 `attempted_failed` cells (as
      of the 2026-06-24 measurement) are re-attempted, then re-measure coverage. Source:
      `data_completion_sports_2026_07_24.md`. Done when: the scoped relaunch VM completes cleanly (exit_code=0) and a
      post-run manifest re-measurement of the golden window shows the `attempted_failed` PLAYER_VALUES cell count has
      dropped from the 256 baseline (either to 0, or the residual is re-classified with a stated reason). **2026-08-08
      (slot 14): the exact-scoped VM (`tm-backfill-20260807-233040`) was already running (launched by an earlier,
      unrelated dispatch at 2026-08-07T23:30:47Z) — do NOT re-launch. It was killed after confirming zero progress in
      1h45m against a confirmed, still-live vendor outage**
      (`transfermarkt-football-data-api.p.rapidapi.com/api/v1/competitions/standings` returning HTTP 502 continuously
      since 2026-08-07T10:17Z, still 502 at 2026-08-08T01:20Z via a direct probe with the adapter's real params — 15h+
      outage). Tracked + tagged BLOCKED-UPSTREAM-OUTAGE in
      `/plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (todo + Progress Log, both docs
      cross-referenced). **Next worker**: verify the endpoint returns 200 (see that doc's probe recipe) before
      relaunching; do not relaunch blind.
- [x] ✅ [DIAG] P2. Re-measure the golden-window (2025-09-01..2025-11-30) ODDS+PREDICTIONS blank-reason
      `empty_confirmed` residual (~3,062/3,078 cells as of the 2026-06-24 measurement, later ~3,255 combined) against
      the live manifest, and file a scoped issue doc
      (`plans/active/issues/sports_odds_predictions_golden_window_empty_confirmed_residual_<date>.md`) capturing the
      root cause + fix options — read-only/diagnosis only, no code or manifest change. Source:
      `data_completion_sports_2026_07_24.md`. Done when: the live-manifest re-measurement figures are recorded and a new
      scoped issue doc exists describing the root-cause candidates and fix options for the residual. — **DONE 2026-08-09
      (slot-20): 0 blank-reason cells remain**, already resolved by prior shipped typing work. See
      `plans/archive/issues/sports_odds_predictions_golden_window_empty_confirmed_residual_2026_08_09.md`.
- [x] ✅ [DATA] P2. Apply the already-tool-extended historical migration for prediction's two confirmed-historical-only
      legacy `instrument_availability` shapes — **DONE 2026-08-09 (slot-22)**. Fresh dry-run confirmed 13,282 flat
      candidates (matching the 2026-08-03 sizing); `--apply-prod --confirm-prod-write` copy-and-verify completed **0
      failed** (13,280 `already_present_verified` + 2 `content_mismatch`, left in place per the existing
      content_mismatch policy). `canonical-cutover-register.md` §6b updated with the applied result. Evidence:
      `unified-trading-pm@<see commit>`.
- [x] ✅ [DIAG] P1. Root-cause the sports-prd manifest consolidator's frozen canonical rows_out — FALSE ALARM, confirmed
      2026-08-06 (slot 5). **Root cause**: `dedup_dropped` is DERIVED arithmetic, not an independent measurement —
      `manifest_consolidator.py:1028` (`dedup_dropped=rows_in - rows_out`). When all incoming shard rows match existing
      canonical rows on their dedup key (`_resolve_dedup_cols`, line 2127: `(date, venue, data_type, service_name)` +
      optional dims), the merge UPDATEs them in place via `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` with
      last-write-wins — row COUNT is conserved, `dedup_dropped` rises in lockstep with the shard purely because the
      shard is growing. This is the EXPECTED signature of idempotent re-capture, documented as SSOT "Diagnostic caveat
      #2" (`/codex/05-infrastructure/manifest-consolidator-ssot.md` lines 267-285). The 2026-08-04 freeze was transient:
      the source issue doc (`manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md`, archived 2026-08-05,
      status=false-positive) already self-identified as likely false alarm citing the identical prior investigation in
      `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`. **Reproduction confirmation**
      (2026-08-06T18:15-19:58Z): `rows_out` is now actively growing — 10,377,663 → 10,432,192 (+54,529 rows across 10
      cycles, ~5-7k per cycle). No code change needed. The upstream backfill skip-logic fix (`check_shard_freshness`
      source/data_type blindness) identified in the 07-29 doc is the actual defect; the consolidator itself is working
      correctly.
- [ ] [DATA] P3. Re-run `ManifestWriter.lookup()` for exactly 2025-09-04 and 2025-11-13 against the completed VM run
      `mdps-sports-bucket-20260803-134154` (use a pyarrow/polars venv via `run-bounded-analysis.sh`, one lookup call per
      date, memory-bounded per the existing recipe in this doc), record the authoritative per-date manifest status
      (`captured` vs `attempted_failed`) for both dates in
      `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`, and reconcile the doc's resolved-date
      list to match whichever of slot-9's or slot-16's prior read is correct. Source:
      `mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`. Done when: both dates' authoritative status is
      recorded in the doc with the ManifestWriter query evidence cited, the resolved-vs-still-attempted_failed date list
      in the doc is corrected to be internally consistent, and the todo itself is checked off as settled.
- [x] ✅ [DATA] P2. Implement the ruled option A (2026-08-02 operator ruling, cited in
      `/plans/active/issues/mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`) in
      `live_workers_chain.py::_write_or_record_empty_timeframe` and
      `live_workers_streaming.py::_record_streaming_empty_timeframe`: route the `SOURCE_RETURNED_ZERO`-fallback case
      from `classify_sports_empty_reason` to `record_failed_for_shard` instead of `record_empty`, matching the existing
      CEFI/DEFI/TRADFI reference implementation (`batch_workers.py::_handle_empty_tick_data`, 2026-06-22 operator
      decision). Source: `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`. Done when: a SPORTS
      honest-absence candle timeframe produces a real manifest row (not a WARNING log with zero rows written), proven on
      one re-run day in `market-data-processing-service`. — **DONE 2026-08-09 (slot-29)**:
      `market-data-processing-service@9c23178`. Both call sites now branch on the `classify_sports_empty_reason` result
      — `SOURCE_RETURNED_ZERO` routes to `record_failed_for_shard` (`NO_RAW_TICK_DATA_FOR_SHARD`), any other typed
      calendar reason still routes to `record_empty_for_shard`. 2 new + 2 updated unit tests assert the routing directly
      (`tests/unit/test_live_workers_coverage2.py`); full `quality-gates.sh` green on the shipped SHA. See Progress Log
      in the source issue doc for the re-run-day proof.
- [x] ✅ [DIAG] P1. Investigate the MDPS SPORTS `~50/N "Unknown error"` crash (findings 3+4 of
      `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`, combined into one sequential pass per
      the skill's same-source-doc rule) in `market-data-processing-service`: (1) grep the failing VM's `run.log` (e.g.
      `mdps-backfill-sports-pipelinecheck-20260801-134301-2bf067`) for `❌ Exception processing` to locate the
      file-level exception `batch_workers.py:513` should log before the summary block (finding 4's
      `_collect_future_result` lead); (2) if inconclusive, reproduce locally against known-bad instrument_ids (e.g.
      `FOOTBALL:bovada:h2h:soccer_argentina_primera_division:2025/2026:Racing Club-Estudiantes::AWAY`) for dates
      `2025-12-18`/`2025-12-24`; (3) if still inconclusive, read
      `_streaming_filter_slice`/`_streaming_resolve_inst_info` (`live_workers_streaming.py:777-823`) line-by-line for a
      raise that stringifies to `""` (finding 3's residual lead). Do NOT relaunch `mdps-backfill-sports-` for
      2025-12-24/2025-12-18 until this investigation's conclusion lands. Source:
      `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`. Done when: the raising frame/exception
      is named (via whichever step first identifies it) and documented in the doc's Progress Log, or all 3 steps are
      exhausted with a documented "raise-free, cause still unknown" conclusion. — **RESOLVED 2026-08-06 (slot-4). Root
      cause: findings 3+4 = same bug as finding 1, fixed by `market-data-processing-service@33b323c`/`8358b9f` (already
      shipped 2026-08-01).** The 50 `ticks_migrated_*.parquet` files (eager path) are 100% honest-absence (all rows
      outside the pre-match horizon) → `processed_timeframes=[]`, `errors=[]` → the PRE-fix formula
      `success = len(errors)==0 and len(processed_timeframes)==len(valid_tfs)` yields `success=False` with
      `error_message=None` → `process_handler.py:468` prints "Unknown error". No exception is ever raised (0 hits in
      `134301` run.log for `❌ Exception processing` / `❌ Error processing` / `classify_and_emit_error` /
      `falling back to eager` / `⚠️ Error in` / `Traceback`). The 588 `ticks.parquet` files (streaming path,
      `success=error_count==0` correct since `1cdf3ecf`) succeeded — 50+588=638 exactly matches the summary. The
      finding-3/4 VMs ran a floating (unpinned) MDPS tarball lacking the fix (TARBALL_PINS.mdps floating; the doc's
      "HEAD=`0fc0448`" reference is a `_backmerge` commit not on LDR). Local repro (slot-4) on current LDR HEAD: the
      exact failing file → `success=True`; concurrent `_process_files_parallel(max_workers=4)` over all 50
      `ticks_migrated` files → `failed=0`. No code change needed — fix already shipped. The `[SCRIPT]` no-relaunch STOP
      in the source doc is now cleared. See source doc Progress Log 2026-08-06.
- [ ] [CODE] P2. Investigate-then-fix finding 5 of
      `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md` in `market-data-processing-service`:
      first grep findings-3/4's VM `run.log`s (e.g. `mdps-backfill-sports-pcskip-20260801-130846-2bf067` /
      `mdps-backfill-sports-pipelinecheck-20260801-134301-2bf067`) for `[partition_mismatch]` to check whether any of
      the 50-52 "Unknown error" instruments share finding 5's venue-mismatch root cause (fold findings if confirmed
      shared); then in `candle_write_mixin.py::_build_candle_output_path`, gate the `input_venue.upper()` shortcut
      (line 286) on `category != MarketAssetGroup.SPORTS` so SPORTS always resolves `venue` via
      `_venue_token_from_canonical_id(instrument_id, asset_group=category)` regardless of whether `input_venue` is
      truthy. Source: `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`. Done when: the
      shared-root-cause check result is recorded, the code fix lands, and a from-scratch
      `pipeline_e2e_check.py --asset-group SPORTS --data-types odds_horizon_bucket` force run against day=2026-04-14
      produces 0 `[partition_mismatch]` rejects for the SPORT888/BETONLINEAG/CORAL (`US_CATANZARO_1929-MODENA`) and
      UNIBET (`SOUTHAMPTON-BLACKBURN`) cells. **2026-08-09 (slot-2): grep+code-fix legs DONE
      (`market-data-processing-service@551ca82`, unit-tested); e2e leg BLOCKED — see
      [`mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check_2026_08_09.md`](/plans/archive/2026_08/issues/mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check_2026_08_09.md) +
      the source doc's Progress Log for the full run evidence. **2026-08-09: that doc's own todos are now both done
      (staleness guard fixed) but re-verification surfaced a DISTINCT, deeper partition_mismatch root cause — see
      [`mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md`](/plans/active/issues/mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md).
      Checkbox stays unflipped pending THAT fix.**
- [ ] [DATA] P3. Root-cause the 216 residual poll-key-duplicate canonical sports MDT odds objects (1,266 duplicate-key
      groups where both home AND away team-id legs vary simultaneously, left untouched by the
      single-team-resolution-split rule shipped in `scripts/dedup_odds_api_poll_key_duplicates_2026_07_26.py`) and
      either implement a new decidable de-dup rule or confirm genuine non-automatability. Regenerate the current
      undecidable-cell set via a fresh (not `--affected-cells-file`) run of
      `dedup_odds_api_poll_key_duplicates_2026_07_26.py` in `market-tick-data-service`, investigate whether the
      both-legs-varying pattern is a systematic club-prefix normalization difference, checking in particular the
      10+-cell same-day concentration on `2022-04-15/PRIMEIRA_LIGA` for a shared root cause. Source:
      `mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md`. Done when: EITHER (a) a new decidable rule is
      implemented, applied, and re-verified to leave 0 duplicate-key groups remaining among the 216-object population,
      with a regression test covering the new rule, OR (b) the both-legs-varying pattern is confirmed genuinely
      non-automatable (documented root-cause reasoning) and each of the 1,266 duplicate-key groups is resolved manually
      with the resolution recorded in the doc's Progress Log.
- [ ] [CODE] P3. In ml-service, wire `extra_args_fn=_add_ml_training_args` (and the other training-specific
      `ServiceBootstrap` kwargs that `ml_service/training/cli/main.py::main()` already passes) into the consolidated
      `ml_service/cli/main.py::run_cli`, so the installed `ml-service` console script can parse training-operation flags
      identically to the working `python -m ml_service.training.cli.main` invocation. Source:
      `ml_service_pipeline_handler_clv_target_bypasses_odds_targets_merge_2026_08_03.md`. Done when:
      `ml-service --operation pipeline --asset-group SPORTS --family pregame_clv_family --target-types clv --timeframes fixture --start-date <d> --end-date <d>`
      no longer fails with `error: unrecognized arguments`, and a regression test proves the console-script entrypoint
      accepts the training-specific args; ml-service quality-gates.sh green.
- [ ] [DIAG] P3. In ml-service, re-verify the fixture/date-count discrepancy for the SPORTS 2026-04-01..17 window across
      the 3 known loader code paths (PipelineHandler._load_features → 758 fixtures/13 dates; TrainingOrchestrator's own
      feature-loading path via `--operation train` → 597 fixtures/9 dates; the original direct-verification session's
      loader → 2,383 fixtures/17 dates) against real prod GCS data. Confirm whether the gap is data staleness or a
      regression in the fixture_id join-key-sibling-frame mechanism, and fix if it's a genuine bug; otherwise document
      the root-cause explanation. Source:
      `ml_service_pipeline_handler_clv_target_bypasses_odds_targets_merge_2026_08_03.md`. Done when: a concrete,
      evidence-backed root cause is stated for the count discrepancy, and either a fix ships + is verified with matching
      counts across the 3 paths, or the doc records why the counts are legitimately expected to differ.
- [ ] [CODE] P3. In ml-service, add a `task_type` default/validation guard for sports 3-class targets (`clv`,
      `swing_high`, `swing_low`, which produce `{-1,0,1}`-valued targets) so `--operation pipeline`/`train` either
      default `task_type` to `regression` for these target types, or fail fast at config-build time with a clear error,
      instead of silently accepting `--task-type classification` and crashing deep in `lightgbm.basic.LightGBMError`.
      Add a regression test covering both behaviors. Source:
      `ml_service_pipeline_handler_clv_target_bypasses_odds_targets_merge_2026_08_03.md`. Done when: running with
      `--task-type classification` for these target types either auto-corrects to regression with a logged notice or
      fails fast with an actionable error before reaching hyperparameter tuning, proven by a new regression test;
      ml-service quality-gates.sh green.
- [ ] [DATA] P3. Exclude `odds_horizon_bucket` from `market-tick-data-service/scripts/pipeline_e2e_check.py`'s
      SPORTS/ODDS_API raw-data_type enumeration, since UAC `SOURCE_PRIORITY[('sports','ODDS_HORIZON_BUCKET')]` registers
      only `mdps_odds_horizon_bucket` (MDPS-derived) as its source and no raw-vendor source is registered for it at all.
      Source: `mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md`. Done when: `pipeline_e2e_check.py`'s
      SPORTS/ODDS_API enumeration no longer yields an `odds_horizon_bucket` cell, and a quality-gates-green commit lands
      in `market-tick-data-service`.
- [x] ✅ [DOCS] P3. Archive
      `plans/archive/2026_08/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md` per the 6-step
      archival ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): `git mv` it to
      `plans/archive/2026_08/`, add an archived/superseded banner citing the archive date and reason (all todos done,
      doc unlocked), then fix every corpus referrer that still points at the old active path (the doc's own 2026-08-03
      note enumerates 10). Source: `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`. Done when:
      the doc lives at its new `plans/archive/2026_08/` path with an archived banner,
      `regenerate_active_plan_inventory.py` shows zero orphan/broken-referrer count for this doc's old path, all 10
      referrer paths resolve to the new location, and the hygiene sweep is green.
- [x] ✅ [DATA] P2. Scope and execute the GCS-object-level residual cleanup for the 8,937 manifest-dropped rows removed
      2026-08-04 (`canonicalize_sports_league_id_schema_2026_06_24.py --drop-out-of-universe --apply`; snapshot
      `gs://instruments-store-sports-prd-central-element-323112/_index/snapshots/pre_league_id_canonicalize_20260804T075724Z.parquet`)
      — dropping a manifest row does NOT delete the underlying GCS parquet object. Derive the candidate object list
      directly from the dropped-rows snapshot (never a new whole-corpus GCS walk), then apply the full five-part proof
      per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, including a FRESH same-run
      `gcs_bucket_soft_delete_retention_seconds()` check ≥604800s before any delete (path (c) reversibility-verified, no
      `[OPERATOR]` gate needed once this holds). Source:
      `sports_curated_universe_domestic_selection_remaining_2026_07_25.md`. Done when: every one of the 8,937
      dropped-row objects is either confirmed genuinely orphaned and deleted (evidence recorded per the delete-safety
      checklist) or confirmed NOT safe to delete with the reason recorded. — **ALREADY DONE, pre-dates this batch's
      dispatch (2026-08-09, slot 10, pre-task plan/issue conflict check).** This exact cleanup was executed 2026-08-04
      (slot 14) under its source doc BEFORE that doc was archived: `instruments-service@48d3b10c` (script
      `scripts/gcs_orphan_cleanup_sports_curated_universe_2026_08_04.py`, five-part proof per the delete-safety
      protocol) — deleted=7,998 orphaned league-specific objects, failed=0, skipped=8 (mixed-content risk, left in
      place), 11,186 already not-found. Full evidence:
      `/plans/archive/issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md` lines 582-601 (todo
      closed + doc archived 2026-08-06). The batch9 `/ag-closeout-audit` run (2026-08-04) that generated this todo
      sourced it from the pre-archival, pre-closure state of that doc — this checkbox flip is a no-op correction, not
      new work: no new GCS deletes were performed this session.
- [ ] [DIAG] P3. Investigate why the sports `_index` dedup rate jumped from ~11% (June baseline) to 45% (2026-08-03)
      during the `canonicalize_sports_league_id_schema_2026_06_24.py --apply` re-key run. Determine whether the jump is
      a one-time artifact of the concurrent curated-universe-backfill VM campaign or a genuine consolidator gap. Source:
      `sports_curated_universe_domestic_selection_remaining_2026_07_25.md`. Done when: root cause is identified, or the
      jump is ruled out as a one-time campaign artifact — and if a real consolidator gap is confirmed, a follow-up todo
      is filed against it.
- [ ] [DATA] P2. Verify the 2026-08-04 sports honest-coverage rollup (VM `measure-honest-coverage-20260804-110554`)
      completed by confirming `gs://central-element-323112-honest-coverage/2026-08-04/coverage.json`'s `generated_at`
      advanced past `09:38:21Z`, then re-read `GET /api/data-status/distinct-values/sports` and compare against the
      expected result (venues 3/13 non-canonical, or fewer if FOOTBALL already cleared; instrument_types 0/37;
      data_types 0/10). Source: `sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`. Done when: the
      coverage.json timestamp and the live endpoint response are both captured in the doc's Progress Log with any
      deviation from the expected counts explicitly noted.
- [ ] [DIAG] P3. Query the sports manifest for `venue=FOOTBALL capture_status=attempted_failed` rows (baseline 194)
      after the `market-data-processing-service@595a1ff` `live_workers.py` fix. If the count has dropped to 0 on natural
      retry, record it cleared; if rows persist, diagnose whether the remaining failure is a distinct root cause before
      deciding on a manifest phantom-row cleanup. Source:
      `sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`. Done when: a fresh manifest query result
      for `venue=FOOTBALL attempted_failed` is recorded in the doc's Progress Log, either confirming 0 rows or
      documenting the specific root cause of any remaining failures.
- [x] ✅ [INFRA] P3. **DONE-ELSEWHERE 2026-08-06 (governance-sweep activation-readiness check).** Already shipped:
      `deployment-service@dfbb8c39` ("fix(vm): add SPOT provisioning to launch-sports-is-gap-fill.sh") + `d683f80b`
      ("feat(vm): add --on-demand CLI flag..."), both 2026-08-05. Verified live — `launch-sports-is-gap-fill.sh` has
      SPOT-default `PROVISIONING_FLAGS` logic (line 122-124) and the `--on-demand` opt-out (line 48). Source doc's own
      checkbox already `[x]` citing `d683f80`. No action needed. Original text preserved below for record. **Add a
      `--provisioning-model` flag (default `SPOT`, `--on-demand` opt-out) to
      `deployment-service/scripts/vm/launch-sports-is-gap-fill.sh`'s `gcloud compute instances create` call.**
- [x] ✅ [CODE] P2. **DONE-ELSEWHERE 2026-08-06 (governance-sweep activation-readiness check).** Already shipped:
      `deployment-service@1c1e445` ("feat(sports): filter market-tick-data-service from pre-match triggers for non-odds
      leagues") + follow-ups `dce296a9`/`f78531e7`, 2026-08-05. Verified live — `_league_has_odds_coverage()` present
      (line 25) and wired into `evaluate_pre_match_triggers` (line 126), plus a full regression suite
      (`tests/unit/test_sports_trigger_odds_coverage_filter.py`, 8 unit tests). Source doc's own checkbox already `[x]`
      citing `f78531e`. No action needed. Original text preserved below for record. **Add a league odds-coverage filter
      to deployment-service's `evaluate_pre_match_triggers`.**
- [ ] [DIAG] P2. Run a scoped blast-radius check on `uts-prod-market-tick-data-service-fast-t1-recon` to determine
      whether PREDICTION and/or DEFI dispatches through the same shared Cloud Run Job carry the same OOM risk class as
      the confirmed SPORTS-specific unscoped-multi-league-fetch bug, using the same method as
      `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s prior DeFi/Prediction check. Source:
      `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`. Done when: a written verdict states, for each of
      PREDICTION and DEFI, whether the same OOM risk class is present (with cited log/code evidence) or confirmed
      absent, and if present, a new issue doc is filed for the affected asset_group(s).
- [ ] [CODE] P2. Soften the manifest-consolidator staleness error text in
      `unified_trading_library/manifest_writer/_read_index.py` (~lines 289-297) to distinguish a genuinely-DOWN
      consolidator (no recent successful Cloud Run Job execution) from a too-tight staleness budget (consolidator
      executing successfully, index merely older than `MANIFEST_CONSOLIDATED_STALENESS_SEC`). Source:
      `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`. Done when: the error message/log
      distinguishes the two cases with different text, a unit test covers both branches, and quality-gates.sh is green.
- [ ] [DATA] P2. Run a manifest census on the exact 61 `rateLimit` `attempted_failed` cells produced during the
      2026-07-18 15:27-15:57Z api-football 5-VM concurrency window (entities
      FIXTURE_EVENTS/FIXTURE_LINEUPS/FIXTURE_STATS/PLAYER_STATS in `instruments-sports`) and confirm each (date, entity)
      cell has since transitioned to `captured`/`empty_confirmed`; for any still `attempted_failed`, trigger an explicit
      re-attempt. Source: `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`. Done when: a written
      per-cell verdict is recorded for all 61 original rows, with zero remaining `rateLimit` `attempted_failed` rows
      attributable to that window.
- [ ] [PROCESS] P2. Codify the lesson "before launching a `--force` whole-corpus refetch to fix ONE column, check
      whether a surgical column-filler script already exists" into a codex SSOT (e.g.
      `/codex/05-infrastructure/vm-launcher-runbook.md`), citing the ~1,800x-call-volume-reduction precedent
      (`backfill_sports_fixture_round_2026_07_17.py`'s ~600-700 total calls vs the full `--force --entity FIXTURES`
      backfill's ~1,260,000 calls). Source: `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`. Done
      when: the chosen codex SSOT carries this lesson as a named rule/heuristic with the cited precedent, and a grep for
      the lesson text returns a hit.
- [ ] [CODE] P2. Extend `emit_empty_gaps_for_entity` in
      `instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py` so its expected-league
      denominator for the 4 per-fixture enrichment entities (FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/PLAYER_STATS)
      branches by data_type: use the MVP-scoped `SPORTS_ENTITY_LEAGUE_COVERAGE` set for these 4 entities instead of the
      full 383-league `get_expected_leagues_for_source("api_football")` set. Source:
      `sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md`. Done when: the 4 entities' honest-absence
      gap emission uses the MVP-scoped denominator, a regression test pins the narrower expected-count for at least one
      of the 4 entities, and quality-gates.sh is green.
- [ ] [DIAG] P3. Re-measure whether the same static-default `expected_universe_start_date` pattern
      (`deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf`) produces the same
      zero-`expected_unattempted`-before-window artifact for cefi/defi/tradfi/prediction that was confirmed for sports.
      Read-only: one column-projected manifest read per asset_group. Source:
      `/plans/archive/2026_08/issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md`. Done
      when: for each of cefi/defi/tradfi/prediction, the per-data_type cell-seeding ratio + the zero-vs-nonzero split is
      measured and reported, with no manifest writes.
- [ ] [DIAG] P3. Investigate the FIXTURES/FIXTURES_OUTCOMES/ODDS-specific distinct `league_id` growth (88→924, 88→926,
      51→384 respectively, vs the ~4x baseline other sports data_types show) to classify it as genuine coverage
      expansion vs a duplicate/near-duplicate league_id seeding artifact isolated to those 3 data_types. Read-only
      manifest query only. Source:
      `/plans/archive/2026_08/issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md`. Done
      when: a per-data_type verdict (genuine-expansion / seeding-artifact / mixed) is reached and documented for each of
      the 3 outlier data_types.
- [x] ✅ [SCRIPT] P1. Extend UAC `EXPECTED_BOOKMAKER_MARKET_SETS` / `LEAGUE_ID_TO_TIER`
      (`unified_api_contracts/canonical/crosscutting/_honest_coverage_clusters.py`) to cover the 28 currently-unmapped
      league_ids — unified-api-contracts@6d72669b. All 28 league_ids mapped: 6 to tier_1_domestic (ALLSVENSKAN,
      ELITESERIEN, J1_LEAGUE, K_LEAGUE_1, LIGA_MX, MLS + SOCCER_* aliases), 2 to tier_2_domestic (EKSTRAKLASA,
      SUPER_LIG + SOCCER_POLAND_EKSTRAKLASA), 13 to no_expectation (zero observed coverage). QG green, 4 new regression
      tests pass. LEAGUE_ID_TO_TIER now exported from honest_coverage facade. Source:
      `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`.
- [ ] [DOC] P3. Reconcile the sports live-wiring sequencing cross-reference between
      `sports_odds_feature_naming_canonicalization_2026_07_21.md` and
      `sports_predictions_live_mode_activation_readiness_2026_07_21.md` — the readiness plan's "Prerequisites already
      tracked elsewhere" section currently describes this naming migration as "not yet executed," stale since 8 of 10
      todos are done as of 2026-08-04. Update the stale line, add cross-references between both docs' `related:`
      frontmatter, and record the sequencing-constraint confirmation. Source:
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`. Done when: the readiness plan's stale status line is
      corrected, both docs' `related:` frontmatter cross-references each other, and this doc's Progress Log records the
      sequencing-constraint confirmation.

## Deferred — non-batchable (84 items across the same 42 orphaned docs, taxonomy-tagged)

Per the skill's iterative-drain methodology: before any future `batch10` triage, re-check the conflict-gated entries
below first (cheap — a few greps + reads) since a competing claim may have shipped/superseded by then. Operator-gated
and human-only entries need a real ruling, not re-triage. Time-gated entries need elapsed time/credentials, not
re-triage. Too-large-or-risky entries need their own dedicated plan.

### Operator-gated (undecided design/judgment call or explicit sign-off requirement) (42)

- **canonical_player_stats_fixture_events_quality_2026_07_16.md** — Defect 3: instrument_count manifest-index semantic
  drift across writer generations (2019-era '1' marker vs true row count): Live doc's own 'Proposed fix' section is
  explicit: 'decide the ONE semantic (row count, per the writer), then backfill/normalise instrument_count across eras
  in a single[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10
  Progress Log (2026-08-06)]
- **canonical_player_stats_fixture_events_quality_2026_07_16.md** — Open P3 todo: decide + execute manifest
  reconciliation for ~1,298 captured-but-no-GCS-object player_stats cells (1,210 2018-2020-era + 88 2025-era): The
  todo's own text is a 'decide + execute' ask: 'relabel to an honest capture_status, or document why captured with no
  object is the correct historical record for that[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **instrument_availability_league_and_question_group_partition_shapes_2026_08_03.md** — Todo 1 [OPERATOR]: rule on
  canonical target position for prediction's canonical_question_group= key: Live doc confirms this todo's sports half is
  already resolved and its remaining scope is narrowed to prediction only: an explicit [OPERATOR] sign-off on[citation
  truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md** — Fix the identified bug in
  manifest_consolidator.py, then verify rows_out resumes moving via the doc's reproduction command: This is a live
  production write-path change to `manifest_consolidator.py`, the exact same shared merge function
  (`_write_consolidated`) and the exact same Cloud Run job[citation truncated — conflict-claim not fully recoverable
  from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md** — [CODE] P3 — wire vs. drop ml-service's
  --family training-scope flag (unresolved design decision): Live-doc-confirmed still true: grep -rn '\.family\b'
  ml_service/training/ (excluding tests) still returns zero hits outside the argparse definition — the flag is[citation
  truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md** — _build_fixture_league_map_from_gcs mapping-coverage
  gap (af_league_id→canonical league mapping): The live doc's todo (line 196-210) explicitly states this is 'NOT fixed
  in this pass — needs an operator/architecture decision on whether the mapping should use the[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md** — Historical re-stamp GCS path + manifest
  for LADBROKES_UK→LADBROKES / SPORT888→BET888SPORT (31,046 real captured rows) — [OPERATOR] tag pending, AO-dispatch vs
  human-run undecided: The live doc's own todo 2 text carries an explicit, unresolved `[OPERATOR] tag pending -- confirm
  AO-dispatch vs human-run before executing (this doc currently[citation truncated — conflict-claim not fully
  recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_enrichment_closer_holiday_and_today_false_gaps_2026_08_03.md** — Extend enrichment closer's
  independently-provable bar to close Christmas/today/07-12..14 false-positive cells (OR file a targeted FIXTURES
  honest-absence backfill for the 4 holiday dates first): The doc's own 'Recommended decision' section presents an
  explicit two-path fork with no evidence-based tiebreaker: (a) extend[citation truncated — conflict-claim not fully
  recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_features_layer_findings_sweep_2026_07_18.md** — §E [MODEL] P2 — consider adding T-6h or T-2h as a MODEL
  horizon: Live doc line 600 phrases this as an explicit 'Consider adding T-6h or T-2h as a MODEL horizon' suggestion —
  a modelling/product design call, not a checkable fact or[citation truncated — conflict-claim not fully recoverable
  from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md** — Runtime re-division / mid-flight rate
  rebalancing for already-running api-football fleet VMs (§ M, narrowed residual): Verified live in § M: '[ ] [CODE] P1.
  Runtime re-division: VMs should read the CURRENT fleet size (or lease a share from a central budget) and re-throttle
  when the fleet[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10
  Progress Log (2026-08-06)]
- **sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md** — R [PROCESS] P1 — codify an
  entity-rename/split consumer-migration authoring rule: The live doc (line 406-411) explicitly frames this as 'a
  proposed workspace process rule, not yet codified into a codex doc ... Not batchable — codifying a new
  authoring[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress
  Log (2026-08-06)]
- **sports_fixtures_schedule_wrong_schema_day_2026_04_14.md** — OPERATOR decision: register (or leave unmapped) the 35
  leagues with no canonical UAC registry entry as LeagueDefinitions (P3): Verified in the live doc
  (plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md, 'Open work' section, line 453-458): the
  todo is explicitly tagged[citation truncated — conflict-claim not fully recoverable from this record; re-verified in
  batch10 Progress Log (2026-08-06)]
- **sports_legacy_duplicate_triage_2026_07_22.md** — Todo 7 [REVIEW] P3 — policy decision: 5,028
  non-Prediction-tier-league v2 legacy rows have no canonical per-league write target at all: The doc's own text names
  this explicitly as 'a genuine judgment call, not a mechanical migration' with a stated two-option fork and no
  evidence-based tiebreaker: (a)[citation truncated — conflict-claim not fully recoverable from this record; re-verified
  in batch10 Progress Log (2026-08-06)]
- **sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md** — Execute the
  FINAL decided fix (retire OR scaffold-with-BLOCKED-CREDENTIALS) for markets/outcomes/settlements/arbitrage_opportunity
  capability entries — gated on BLK-c545ae54 operator sign-off: The live doc's own [CODE] P2 todo text is explicit and
  unambiguous: 'Gated on the operator's FINAL decision (not just the DECISION todo's recommendation above) — do
  NOT[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log
  (2026-08-06)]
- **sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md** — Extend
  sports_closeout_exchange_fixed_odds_fork's EXCHANGE_ODDS/FIXED_ODDS venue→class mapping to the 19 previously-unmapped
  bookmaker venues: The live doc's sole open todo (line ~255-263) explicitly self-identifies as a judgment call, not a
  mechanical fact: 'classify each as EXCHANGE_ODDS or FIXED_ODDS ...[citation truncated — conflict-claim not fully
  recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_phantom_audits_reference_not_marketdata_2026_07_14.md** — Build a data_type-aware cross-bucket branch in
  _audit_sports() to fix the two-card phantom/reprobe audit-split design gap (sub-item 1, prose-only, no checkbox): This
  is a code change to instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:283 (_audit_sports()), and the
  doc's own 'Decision' section records an[citation truncated — conflict-claim not fully recoverable from this record;
  re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §1: define decay-window statistic (bps vs fraction):
  The doc's own todo #1 already states a recommendation ('recommend: both — absolute bps ... for a min-viable-edge
  floor, fraction for the decay-CURVE shape') but this is[citation truncated — conflict-claim not fully recoverable from
  this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §1: define window boundaries (signal→fill
  measurement point) + sampling granularity: Todo #2 in §1 explicitly frames a three-option fork ('(a) first-leg fill,
  (b) last-leg fill, or (c) each leg independently') with a stated recommendation but no[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §1: define data source (fill-time odds re-snapshot /
  possible new instruction field): Todo #3 explicitly asks whether a NEW field on the instruction/fill record is needed
  and defers naming it precisely to 'the implementer' — this is design judgment[citation truncated — conflict-claim not
  fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §1: define output shape (decay curve, bucketed by
  outcome-set size): Todo #4 states a design recommendation (bucket by outcome-set size to avoid conflating structural
  3-way decay with a real venue-speed regression) but, like todos #1-3,[citation truncated — conflict-claim not fully
  recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §2: define gate statistic (realized_edge_bps_net;
  mean vs p25): Todo #1 of §2 explicitly states 'this is a real risk-appetite decision, not a mechanical one' and §3's
  second open question restates it verbatim as needing operator[citation truncated — conflict-claim not fully
  recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §2: define minimum sample size + soak duration: Todo
  #2 of §2 poses an open question ('is 7 days the right unit for a strategy that might only see a handful of qualifying
  fixtures... or should the gate instead require[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §2: define pass/fail threshold value + its UAC
  thresholds-module location: Todo #3 of §2 explicitly ties to §3's third open question: 'Confirm the provisional
  threshold-value approach ... is acceptable, or whether the operator wants to set the[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §2: define acceptance test
  (true-positive/true-negative fixture scenarios): Todo #4 of §2 recommends a hermetic test design against the existing
  fixture harness but this depends on the prior three §2 design decisions (gate statistic, sample[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §3 open question: assigned_role/repo-split for
  eventual implementation: Explicitly framed in the doc as an open question for operator sign-off before implementation
  dispatches: 'Is quant_dev the right assigned_role ... or does the fill-time[citation truncated — conflict-claim not
  fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §3 open question: p25-vs-mean risk-appetite
  decision: Doc text verbatim: 'this is a real risk-appetite decision, not a mechanical one' — canonical operator_gated
  case, duplicate framing of §2 todo 1 above.
- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — §3 open question: provisional fixture-derived
  threshold vs real soak data before shipping: Doc text verbatim: 'Confirm the provisional threshold-value approach ...
  is acceptable, or whether the operator wants to set the real number before any code ships (i.e.[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md** — E8 legacy-delete
  --drop-stale/--apply firing for pre-canonical sports GCS objects (irreversible delete, BLOCKED-OPERATOR): Live doc
  (lines 319-349) confirms: the delete MECHANISM is already implemented+unit-tested+dry-run-verified twin-safe (shipped
  via sports_satellite_ao_dispatch_batch5,[citation truncated — conflict-claim not fully recoverable from this record;
  re-verified in batch10 Progress Log (2026-08-06)]
- **sports_catalog_league_grain_only_scope_2026_07_08.md** — Extend catalog build to invoke sports reference-data
  adapters (api_football_reference.py, betfair.py) or confirm manifest-only path + correct SPORTS_INSTRUMENTS.md instead
  (P3): Live doc: `- [ ] [DATA] P3. Extend the catalog build to also invoke reference-data adapters ... or confirm the
  manifest-only path ... remains the intended source of[citation truncated — conflict-claim not fully recoverable from
  this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_catalog_league_grain_only_scope_2026_07_08.md** — Post-decision codex alignment check on
  availability-manifest-and-data-status.md / honest-coverage-model.md once grain changes (P3, [REVIEW], contingent on
  the above landing): Live doc: `- [ ] [REVIEW] P3. Post-decision codex alignment check: if the manifest/catalog grain
  changes, /codex/02-data/availability-manifest-and-data-status.md and[citation truncated — conflict-claim not fully
  recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_fixtures_browser_single_catalogue_source_2026_07_24.md** — Confirm catalogue regen cadence for the fixtures
  browser and either accept+label the live-status lag or add a live-day overlay for today's fixtures ([DATA] P2): Read
  the live doc (plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md, lines 93-96): this is the
  sole remaining open todo, explicitly framed as[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_group_c_execution_backtest_harness_2026_07_21.md** — Resolve SportsMatchingEngine vs L0Matcher duplication
  (todo 3, blocking gate): Live doc todo 3 ([DESIGN] P3) is an explicit two-option fork with no evidence-based
  tiebreaker: (a) delete `SportsMatchingEngine`[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_group_c_execution_backtest_harness_2026_07_21.md** — Add run_sports_backtest CLI wiring to
  execution_service/cli/backtest_domains.py (todo 1, gated on todo 3): Doc's own todo 3 explicitly gates this ('Do this
  BEFORE building the CLI above'), and todo 3 is an unresolved operator/architect decision (SportsMatchingEngine
  vs[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log
  (2026-08-06)]
- **sports_group_c_execution_backtest_harness_2026_07_21.md** — Wire sports/prediction fixture data source into
  execution-service's catalog layer (todo 2, gated on todo 3): Same gating chain as todo 1: this data-wiring step only
  makes sense once the CLI/matcher target is fixed by todo 3's design decision (build against the right matcher
  and[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log
  (2026-08-06)]
- **sports_group_c_execution_backtest_harness_2026_07_21.md** — Add hermetic test asserting non-trivial
  execution_alpha_bps (todo 4, gated on todo 3): This test asserts behavior of `run_sports_backtest`, which does not
  exist until todos 1-3 land; it is transitively blocked by the same unresolved[citation truncated — conflict-claim not
  fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_group_c_execution_backtest_harness_2026_07_21.md** — Decide docs/BACKTESTS.md verification-surface placement
  vs manual one-off (todo 5, untouched by any covering plan): Live doc todo 5 ([DESIGN] P3) is an explicit 'decide
  whether X or Y' ask — whether the future harness belongs in the routine docs/BACKTESTS.md verification
  surface[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress
  Log (2026-08-06)]
- **sports_odds_bookmaker_coverage_enumeration_2026_06_20.md** — P2: Decide + implement the `trades` cluster-validation
  gap (register `trades` in BUNDLED_DATA_TYPES vs accept static-audit-only gate): Verified live at lines 253-257
  (checkbox still `- [ ]`). The item is explicitly phrased as a decision fork with two mutually-exclusive options and no
  evidence-based[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10
  Progress Log (2026-08-06)]
- **sports_odds_bookmaker_coverage_enumeration_2026_06_20.md** — P0 flagged regression-test-deletion discrepancy on Todo
  2/Todo 3: operator decide (a) restore tests or (b) accept coverage + update citations: Verified live at lines 125-140
  (banner explicitly present, unresolved). The banner states in terminal language: 'A human should decide whether to (a)
  restore equivalent[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10
  Progress Log (2026-08-06)]
- **sports_predictions_live_mode_activation_readiness_2026_07_21.md** — Todo 5: run a sports archetype through the
  promote-workflow CLI chain, gated on the Group-C execution-alpha harness landing: Read live: Todo 5 (REVIEW P3,
  unchecked) requires the sports archetype to reach CANDIDATE phase via (a) a passing Group-B backtest AND (b) the
  Group-C execution-alpha[citation truncated — conflict-claim not fully recoverable from this record; re-verified in
  batch10 Progress Log (2026-08-06)]
- **sports_predictions_live_mode_activation_readiness_2026_07_21.md** — Todo 6: permanent [OPERATOR] final go-ahead to
  flip sports/prediction paper→live (human hard-stop by design): Read live: Todo 6 is explicitly tagged [OPERATOR] P3,
  'Final explicit go-ahead to flip sports (and separately, prediction...) from paper to live trading -- requires
  the[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log
  (2026-08-06)]
- **sports_prelaunch_cf5_verify_residual_2026_07_24.md** — C3 pre-launch-window corpus (10,345 objects) — extend
  SOURCE_COVERAGE_START footystats 2019-01-01→2018-01-01 + api_football sub-entity windows, propagate, re-run
  backfill_orphan_class_e_sports.py: Live doc confirms todo 2 (lines 95-102) is still open, plain either/or
  'operator-gated' framing, not yet retagged. batch5_finalize (lines 649-682) records a 2026-07-28[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_track_h_denominator_prereqs_2026_07_28.md** — MDPS odds_horizon_bucket reprocess (Step 7) — path A/B design
  fork: Read the live doc's todo 1 in full (lines 68-116). A 2026-07-29 (slot-6) investigation already ran a real
  --force test-window apply and root-caused the exact mechanism:[citation truncated — conflict-claim not fully
  recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]

### Time-gated (elapsed-time/credential/vendor dependency not yet reached) (14)

- **data_completion_sports_2026_07_24.md** — API-Football daily-quota bump to 1.5M/day (line ~851-859): Read live doc
  L851-859: the branch decision itself is resolved (operator RULED 2026-07-28: proceed with the quota bump), but what
  remains is 'the vendor account-tier[citation truncated — conflict-claim not fully recoverable from this record;
  re-verified in batch10 Progress Log (2026-08-06)]
- **footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md** — Production hold-verification
  (≥2 consecutive days post-deploy) that footystats league-coverage fix zeroes pending_fetch for
  CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA + 11 related PREDICTIONS leagues: The live doc's remaining
  unchecked item is the [DIAG] P3 todo: 'once unified-api-contracts@2a674aa8 + instruments-service@69391ea9 have run
  through at least one[citation truncated — conflict-claim not fully recoverable from this record; re-verified in
  batch10 Progress Log (2026-08-06)]
- **instrument_availability_league_and_question_group_partition_shapes_2026_08_03.md** — Todo 4 [DATA]: historical
  migration of ~172,592 sports league= objects to the ruled canonical shape: The migration tool is already extended to
  recognize + copy this shape (instruments-service@ba87cc32, sibling doc todo 2), but applying it is explicitly gated on
  the[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log
  (2026-08-06)]
- **mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md** — Hold: do not relaunch
  mdps-backfill-sports- for 2025-12-24/2025-12-18 until the crash fix lands: This [SCRIPT] P3 item is not itself
  executable work with a bounded outcome -- it is a standing prohibition ('do NOT relaunch... until the above lands')
  gating a future[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10
  Progress Log (2026-08-06)]
- **sports_af_full_entity_completion_2026_08_03.md** — Launch FIXTURE_LINEUPS all-leagues backfill (gated on
  FIXTURE_STATS converging): Doc lines 172-173 gate this explicitly on FIXTURE_STATS converging first. This is literally
  backlog task `sports_af_full_entity_completion-003`, which per the Progress[citation truncated — conflict-claim not
  fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_af_full_entity_completion_2026_08_03.md** — Re-census all 8 in-scope entities to confirm convergence, then
  close doc + notify operator (blocked: manifest-consolidator frozen): The doc's own latest Progress Log entry
  (2026-08-04T13:37Z) states this outright: the manifest-consolidator's canonical `rows_out` has been frozen at
  9,239,513 for 5+[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10
  Progress Log (2026-08-06)]
- **sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md** — Launch the ~1-month sports odds gap backfill
  (2026-06-27..07-15 total-gap window + 2026-07-16..07-25 granularity-loss window) via the Odds-API historical endpoint:
  Read the live doc's item 1 (lines 254-303 of sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md): as
  of 2026-07-29 the doc itself states both the[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md** — Live-verify the --league scoping fix
  (deployment-service@4e0e03d): Live doc (lines 244-284) shows this todo has been re-dispatched 6+ times (slots
  4/9/10/3/15/2) all self-skipping GATED. 2 of 3 done-when criteria are now met (--league[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md** — Live-verify the pre-flight source-scoping fix
  (market-tick-data-service@afa8eaec): Live doc (lines 387-458, plus the slot-11/8/4 re-checks at lines 395-694)
  confirms this fix is shipped and QG-green on origin/live-defi-rollout but has NOT reached[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md** — Backfill/re-fetch the capture gap for
  2026-07-27/28/30/31 + 08-02: Live doc (lines 432-458 and the slot 11/8 re-check notes at 441-457) explicitly gates
  this behind both live-verify todos above being confirmed live-healthy first --[citation truncated — conflict-claim not
  fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_halftime_odds_sfi_vs_inplay_2026_07_16.md** — Reconcile market-data-sports manifest for 2,436 deleted T-0
  shards (blocked on unmerged cutover T6.1 shard): Live-doc verification: the target doc's open checkbox (line ~196)
  states the market-data-sports manifest still reads 2,436 deleted T-0 shards as `captured` instead of[citation
  truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_odds_api_scattered_multiyear_gaps_2026_07_27.md** — P1: launch odds_api backfill VM to close remaining ~300
  missing days: Live doc line 162-190: checkbox is explicitly tagged BLOCKED-CREDENTIALS as of 2026-08-02 (slot 14, task
  -004) — the-odds-api.com account is OUT_OF_USAGE_CREDITS[citation truncated — conflict-claim not fully recoverable
  from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_odds_api_scattered_multiyear_gaps_2026_07_27.md** — P2 VERIFY: re-run data_type-aware census once P1 lands to
  confirm 0 genuine gaps, then archive the doc: Live doc line 275-295: this VERIFY todo is explicitly stated as 'Depends
  on the P1 backfill above' and is itself tagged BLOCKED-CREDENTIALS as of 2026-08-02 (slot 13) —[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_stats_delayed_live_capture_still_dead_post_fix_2026_07_29.md** — VERIFY P2: re-run Step-3 manifest query once
  a real Understat-covered-league fixture fires stats_delayed live: Read the live doc's open todo at line 478-596. This
  is explicitly and repeatedly confirmed gated on elapsed real time: Understat only covers 5 leagues[citation truncated
  — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]

### Conflict-gated (already claimed by an open todo elsewhere in the covering set) (21)

- **instrument_availability_league_and_question_group_partition_shapes_2026_08_03.md** — Todo 2 [DATA]: re-verify
  prediction's canonical_question_group= shape is genuinely historical-only across all 78 prefixes: This exact
  investigation ground is already covered by the sibling issue doc[citation truncated — conflict-claim not fully
  recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **instrument_availability_league_and_question_group_partition_shapes_2026_08_03.md** — Todo 3 [DATA]: locate + fix the
  sports writer codepath emitting day=/league=/venue=: Already done. Sibling issue doc
  instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md's todo 2 (closed [x]) is
  the exact same[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10
  Progress Log (2026-08-06)]
- **ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md** — [ML] P2 — retrain 3 CLV model variants
  (doc's own checkbox still unflipped; underlying work completed via a sibling doc): Verified the underlying work is
  fully DONE: the sibling doc
  plans/archive/2026_08/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md's own [ML] P2
  todo[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log
  (2026-08-06)]
- **mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md** — [OPERATOR] P2 the-odds-api.com
  credential/quota-exhaustion ask (checkbox unflipped): Verified in the live doc: the unchecked `[OPERATOR] P2` item at
  lines 182-187 asks for a credential check + quota top-up/key rotation for the `the-odds-api.com`[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md** — Verify whether
  odds_home_close/odds_draw_close/odds_away_close are populated or always-null in the real odds_features export for
  every currently-emitting model horizon: Live-doc check: the doc's 'Recommended decision' section is actually ONE
  combined checkbox item ('[DATA] P3. Verify whether[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md** — If always-null: file a
  structurally-separated-export fix for CLVTargetBuilder, OR confirm pregame_clv_family is unused in any real retrain
  and close this doc as moot: Same single live-doc checkbox as item 1 (the conditional 'if always-null' branch of the
  one combined todo) -- not a separate checkbox. Same conflict-check result: no[citation truncated — conflict-claim not
  fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md** — If populated: close this doc, no gap
  exists: Same single live-doc checkbox as items 1-2 (the 'if populated' branch). Same conflict-check result -- the
  doc's own frontmatter already makes the full[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md** — Real-backfill timing verification for the
  manifest-slice (check_api_football_dependency) + cached/batched (sports_fixtures.py:356) fixes: This exact item is
  already an open todo in the covering-plan set: plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md
  line 153, '- [ ] [VERIFY] P2.[citation truncated — conflict-claim not fully recoverable from this record; re-verified
  in batch10 Progress Log (2026-08-06)]
- **sports_features_layer_findings_sweep_2026_07_18.md** — §E [CONFIG] P1 — forward fix: start capture earlier / poll
  densely enough that every declared horizon window is actually sampled: Live doc (lines 586-592) explicitly states this
  item is gated: 'sports_live_availability_and_source_latency_2026_07_24.md ... now describes a Tier-3
  odds_t24h/t6h/t1h[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10
  Progress Log (2026-08-06)]
- **sports_features_layer_findings_sweep_2026_07_18.md** — §F [AUDIT] P2 — extend the canonical-naming audit (§F1-F6
  methodology) to league/fixture/betting-market identifier columns: Live doc lines 691-701 show this checkbox already
  flipped to [x] with an explicit annotation: 'DE-DUPLICATED here 2026-08-02 by /na-eligibility-audit (sports
  tranche),[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress
  Log (2026-08-06)]
- **sports_features_layer_findings_sweep_2026_07_18_part2_2026_07_26.md** — Catalogue snapshot re-roll
  (build_instrument_catalogue.py --asset-group sports --since 2019-01-01) to pick up +26,894 round rows: The doc's own §
  G 'Step 4' annotation states this is 'owned by plans/active/sports_consolidated_closeout_2026_07_19.md Track V ... Not
  duplicated here, owned by Track[citation truncated — conflict-claim not fully recoverable from this record;
  re-verified in batch10 Progress Log (2026-08-06)]
- **sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md** — R/R-FIXED [DIAG] P0 duplicate pair — audit +
  repoint ~9 stale entity=fixtures consumers: Both occurrences of this item in the live doc (line 396 and line 449) are
  already explicitly annotated 'Owned by sports_consolidated_closeout_2026_07_19.md Track E ...[citation truncated —
  conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md** — Y [CODE] P2 — fix launch-features-vm.sh's
  404 post-backfill bucket hint + swap to additive merge_manifest_from_canonical_paths(): Live doc line 782-786
  explicitly states: 'Owned by sports_satellite_ao_dispatch_batch6_2026_07_26.md todo 3 — that todo ships the fix and
  flips this checkbox as part of[citation truncated — conflict-claim not fully recoverable from this record; re-verified
  in batch10 Progress Log (2026-08-06)]
- **sports_halftime_odds_sfi_vs_inplay_2026_07_16.md** — Blank fixture_id raw generation -- fix upstream ODDS_API writer
  (owner: MTDS): Live-doc verification: the target doc's own open checkbox (line ~185) says the ODDS_API capture path
  still emits `fixture_id=""` and names the writer as unfixed, owner[citation truncated — conflict-claim not fully
  recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_halftime_odds_sfi_vs_inplay_2026_07_16.md** — Retrain CLV models after the ODDS_FEATURES recompute: Live-doc
  verification: the target doc's open checkbox (line ~200) says to retrain the CLV models now that the ODDS_FEATURES
  recompute prerequisite is done, with the 3[citation truncated — conflict-claim not fully recoverable from this record;
  re-verified in batch10 Progress Log (2026-08-06)]
- **sports_legacy_duplicate_triage_2026_07_22.md** — Todo 6 [DATA] P3 — root-cause and retire the 764
  pipeline_mode=batch_api_football-tagged duplicate copies written into sports_reference_v2/by_date/: The doc's own text
  already concedes the pre-floor half of this exact 764-count population was wiped 2026-08-03 (deployment-service's
  wipe_pre_floor_sports_2026_07_21.py[citation truncated — conflict-claim not fully recoverable from this record;
  re-verified in batch10 Progress Log (2026-08-06)]
- **sports_phantom_audits_reference_not_marketdata_2026_07_14.md** — Spot-check the unexamined ~1,335-row (0.19%)
  phantom residual (STANDINGS 460/TEAMS 460/XG 300/WEATHER 106/MATCHES 7/FIXTURES 2): Live doc's own Todos section
  (checkbox [DATA] P3) already carries an explicit 2026-07-30 amendment: 'DO NOT dispatch/investigate this item
  independently' — the operator[citation truncated — conflict-claim not fully recoverable from this record; re-verified
  in batch10 Progress Log (2026-08-06)]
- **sports_catalog_league_grain_only_scope_2026_07_08.md** — Design manifest schema extension for per-fixture capture
  presence tracking (P2, ACTIVE scope per 2026-07-14 operator ruling): Live doc confirms this todo is still open
  (`- [ ] [DATA] P2. Design the manifest schema extension needed to track per-fixture capture presence...`). The doc's
  own 🟡[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log
  (2026-08-06)]
- **sports_catalog_league_grain_only_scope_2026_07_08.md** — Write build_sports_fixture_catalogue_from_manifest()
  fixture-grain catalogue builder, gated on the schema extension (P2): Live doc:
  `- [ ] [DATA] P2. Write build_sports_fixture_catalogue_from_manifest() ... gated on the manifest extension above`.
  This todo is explicitly sequenced after item[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_odds_feature_naming_canonicalization_2026_07_21.md** — FSS-output <-> ml-service-input <->
  strategy-service-input naming parity test (todo 9): Live doc confirms this is still open (line 197-200 of
  sports_odds_feature_naming_canonicalization_2026_07_21.md, `- [ ] [REVIEW] P3`). Conflict-check grep of the[citation
  truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_predictions_live_mode_activation_readiness_2026_07_21.md** — Todo 3: launch-mdps-features-live.sh
  cross-cutting exec-dispatch wiring (production deployment of MDPS+FSS live path): Read live: the sports doc's Todo 3
  (unchecked INFRA P3, last edited 2026-07-29) still describes 'the remaining launcher work is
  launch-mdps-features-live.sh[citation truncated — conflict-claim not fully recoverable from this record; re-verified
  in batch10 Progress Log (2026-08-06)]

### Too-large-or-risky-for-a-batch-todo (own dedicated migration/design pass needed) (5)

- **sports_af_full_entity_completion_2026_08_03.md** — Launch PLAYER_STATS MVP-96 backfill (attempts in progress, not
  yet converged): This doc itself is `assigned_vm: planning` and is already the live, actively-executing AO dispatch
  surface for exactly this work -- the Progress Log shows[citation truncated — conflict-claim not fully recoverable from
  this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_af_full_entity_completion_2026_08_03.md** — Launch INJURIES all-leagues backfill (not yet started): Per the
  Sequencing note (doc lines 219-224), INJURIES shares the SAME af-backfill/af-audit singleton lock as
  FIXTURE_STATS/LINEUPS/PLAYER_STATS -- explicitly 'a[citation truncated — conflict-claim not fully recoverable from
  this record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_af_full_entity_completion_2026_08_03.md** — Launch STANDINGS all-leagues backfill (not yet started): Same
  singleton-lock sequential campaign as INJURIES/TEAMS/PLAYER_STATS/FIXTURE_STATS/LINEUPS (Sequencing note, doc lines
  219-224) -- shares the one-VM-at-a-time AF quota[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_af_full_entity_completion_2026_08_03.md** — Launch TEAMS all-leagues backfill (not yet started): Same
  singleton-lock sequential campaign (Sequencing note, doc lines 219-224), plus TEAMS carries its own unresolved caveat
  (doc lines 146-154: unverified per-league vs[citation truncated — conflict-claim not fully recoverable from this
  record; re-verified in batch10 Progress Log (2026-08-06)]
- **sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md** — Launch + verify the real production
  run of job (2)'s historical expected_unattempted backfill (2020-06-06 floor, 7 calendar-year VM chunks): This is the
  doc's own open `[DATA] P2` checkbox (line 226-237). The Progress Log shows it is a LIVE, actively-worked multi-day
  campaign: a data_engineering worker (slot[citation truncated — conflict-claim not fully recoverable from this record;
  re-verified in batch10 Progress Log (2026-08-06)]

### Genuinely human-only (dispatch-scope eligibility rule excludes it outright) (2)

- **manifest_consolidator_frozen_canonical_rows_out_sports_2026_08_04.md** — Extend ConsolidatorLivenessMonitor to check
  output correctness (rows_out actually advancing), not just heartbeat age: This item is prose only in the live doc
  ('The existing ConsolidatorLivenessMonitor watchdog only checks heartbeat AGE ... not output correctness'), not an
  explicit[citation truncated — conflict-claim not fully recoverable from this record; re-verified in batch10 Progress
  Log (2026-08-06)]
- **sports_track_h_denominator_prereqs_2026_07_28.md** — batch_footystats copy+swap — data complete/verified, code ship
  blocked (RB-166e706f): Read the live doc's todo 2 (lines 118-132) and the full 2026-07-28 (slot-14) Progress Log entry
  (lines 143-201) describing a real, detailed 16,970-object PROD copy+swap:[citation truncated — conflict-claim not
  fully recoverable from this record; re-verified in batch10 Progress Log (2026-08-06)]

## Progress Log

### 2026-08-06 — P1 ramp-to-429 calibration (slot 7)

Two-pass probe via ephemeral VM (never prod IP 13.113.200.22):

- **Pass 1** VM `uts-rate-calibration-probe-20260806-195143`: probed open_meteo, polymarket_clob, polymarket_gamma_api.
  Crashed at soccer_football_info due to wrong GCP secret name (`rapidapi-key` → corrected to
  `soccer-football-info-api-key`; fix quickmerged to instruments-service).
- **Pass 2** VM `uts-rate-calibration-probe2-20260806-195923`: probed soccer_football_info, transfermarkt, understat
  with the corrected script.

| source               | break_rpm     | last_ok_rpm | safe_rpm     | recovery_s   | probe_vm                                    | probed_at_utc        |
| -------------------- | ------------- | ----------- | ------------ | ------------ | ------------------------------------------- | -------------------- |
| open_meteo           | 600           | 540         | 480          | 1.24         | uts-rate-calibration-probe-20260806-195143  | 2026-08-06T19:54:30Z |
| polymarket_clob      | null (>=3600) | 3600        | 2880 (floor) | null         | uts-rate-calibration-probe-20260806-195143  | 2026-08-06T19:55:43Z |
| polymarket_gamma_api | 2040          | 1980        | 1632         | 1.01         | uts-rate-calibration-probe-20260806-195143  | 2026-08-06T19:56:18Z |
| soccer_football_info | 240           | 180         | 192          | null (>120s) | uts-rate-calibration-probe2-20260806-195923 | 2026-08-06T20:04:19Z |
| transfermarkt        | null (>=3600) | 3600        | 2880 (floor) | null         | uts-rate-calibration-probe2-20260806-195923 | 2026-08-06T20:05:38Z |
| understat            | null (>=3600) | 3600        | 2880 (floor) | null         | uts-rate-calibration-probe2-20260806-195923 | 2026-08-06T20:07:31Z |

Notes: `null (>=3600)` = probe hit max_rpm=3600 with no reject; safe floor = 0.8x 3600 = 2880. `soccer_football_info`
recovery > 120s (probe limit); `polymarket_clob` recovery null (no break observed). GCS artifacts:
`gs://deployment-scripts-central-element-323112/vm-logs/uts-rate-calibration-probe*/`.

Both probe VMs self-deleted. Registry updated: deployment-service@0eb9c36.

### 2026-08-06 — findings-3+4 MDPS "Unknown error" crash root-caused (slot-4)

Closed the `[DIAG] P1` todo (findings 3+4 of `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`)
— **the crash is the SAME bug as finding 1, already fixed by `market-data-processing-service@33b323c`/`8358b9f`**. The
50 `ticks_migrated_*.parquet` files (eager path; 100% honest-absence — every row dropped by the pre-match-horizon
filter) produced `processed_timeframes=[]`, `errors=[]`, so the PRE-fix formula
`success = len(errors)==0 and len(processed_timeframes)==len(valid_tfs)` gave `success=False` with `error_message=None`
→ `process_handler.py:468`'s `or "Unknown error"`. No exception is ever raised (null greps for `❌ Exception processing`
/ `❌ Error processing` / `classify_and_emit_error` / `falling back to eager` / `⚠️ Error in` / `Traceback` in
`134301`'s run.log). The 588 `ticks.parquet` files (streaming, `success=error_count==0` correct since `1cdf3ecf`)
succeeded — 588+50=638 matches the summary exactly. The finding-3/4 VMs ran a floating MDPS tarball lacking the fix
(TARBALL_PINS.mdps unpinned; the doc's "HEAD=`0fc0448`" claim is a `_backmerge` commit not on LDR). Local repro on
current LDR HEAD (slot-4): the exact failing file → `success=True`; concurrent `_process_files_parallel(max_workers=4)`
over all 50 `ticks_migrated` files → `failed=0`. **No code change needed** — the fix is already shipped; the source
doc's `[SCRIPT]` P3 no-relaunch STOP is cleared.

- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — added the conflict-check protocol codex doc
  (`ao-dispatch-batch-naming-and-conflict-check.md`, Phase 3 of this batch's own methodology ran it) alongside the 4
  pre-existing entries. `*_satellite_ao_dispatch_batchN_*` coordinator shape (30 todos spanning 8 repos, each with its
  own inline `Source:` citation) — no single source path is appropriate per SKILL.md's dispatch-batch-coordinator
  exemption.

### 2026-08-07..08 — P2 PLAYER_VALUES Transfermarkt backfill (VM `tm-backfill-20260807-233040`) — intermediate status

Launch + two pre-compact status snapshots while the VM cycled through Transfermarkt 502 retries, extracted to
`/plans/archive/2026_08/sports_satellite_ao_dispatch_batch9_progress_log_history_2026_08_09.md` (line-cap remediation
2026-08-09) — fully superseded by the terminal outcome in the "Todo 2 — BLOCKED-UPSTREAM-OUTAGE" entry immediately below
(VM killed 2026-08-08 after a confirmed 15h+ vendor-endpoint outage).

## Codex SSOTs

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the full Phase 0-3 procedure this batch executes.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the shared conflict-check protocol
  (§3) Phase 3 ran against the covering-plan set.
- `plans/active/task_template.md` §4 — finalize-plan-coverage rule + dispatch-scope eligibility test.
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual (todo "Archive
  sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md").
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a — reversibility-verified delete path (the
  curated-universe GCS cleanup todo).
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator merge/dedup mechanics (the rows_out-freeze
  root-cause todo).

### 2026-08-08 — Todo 2 (Transfermarkt PLAYER_VALUES golden-window relaunch) — BLOCKED-UPSTREAM-OUTAGE (slot 14)

Dispatched `sports_satellite_ao_dispatch_batch9-002`. Found the exact-scoped VM (`tm-backfill-20260807-233040`,
`--sports-provider TRANSFERMARKT --sports-entity PLAYER_VALUES --start-date 2025-09-01 --end-date 2025-11-30`, no
`--force`) already launched by an earlier, unrelated dispatch (2026-08-07T23:30:47Z) — the launcher's own singleton lock
correctly would have refused a second one anyway. `run.log` showed 1h45m of zero productive progress: every per-league
`get_teams` call was exhausting all 10 retry-with-backoff attempts against `GET /api/v1/competitions/standings` with
HTTP 502, then moving to the next league and repeating identically — 0 rows written, 0 leagues captured.
Cross-referenced `/plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md`, which already
tagged this exact endpoint `BLOCKED-UPSTREAM-OUTAGE` the day before (first failure 2026-08-07T10:17Z, confirmed still
down at 12:21Z) and recorded a prior session killing an identical stuck VM after 2h17m of zero progress. Direct-probed
the endpoint myself with the adapter's real params (`id=GB1&season=2025`) — still HTTP 502 at 2026-08-08T01:20Z (~52s
latency before the error), confirming a sustained 15h+ outage, not a transient blip. Killed
`tm-backfill-20260807-233040` (heartbeat-blob-confirmed alive but zero useful progress — same justified basis as the
prior kill) rather than let it keep burning GCE billing against a call that cannot succeed. Did not relaunch. Todo 2
annotated in place with this citation and tagged `BLOCKED-UPSTREAM-OUTAGE`; stays unchecked — completion requires the
vendor endpoint to recover first (verify via the convergence doc's probe recipe before any future relaunch).

### 2026-08-09 — Todo 3 (golden-window ODDS+PREDICTIONS blank-reason `empty_confirmed` re-measurement) — RESOLVED, 0 residual (slot-20)

Bounded, column-pruned + row-filtered live-manifest re-measurement (not a whole-corpus walk): **0 blank-reason cells
remain** — all 11,334 in-window `empty_confirmed` cells (ODDS 3,663 / PREDICTIONS 7,671) now carry a typed reason.
Already resolved by prior shipped typing scripts (2026-06-24..07-06 range), no new fix needed. Full measurement +
root-cause citation in
`plans/archive/issues/sports_odds_predictions_golden_window_empty_confirmed_residual_2026_08_09.md`. Flagged there (not
actioned, out of scope): `data_completion_sports_2026_07_24.md`'s own duplicate P2 line for this residual should be
struck by whoever next touches that plan.

### 2026-08-09 — Todo "Scope and execute the GCS-object-level residual cleanup for the 8,937 manifest-dropped rows" — STALE DUPLICATE, flipped without new work (slot-10)

Pre-task plan/issue conflict check (grep before starting, per CLAUDE.md HARD RULE) found this exact cleanup was already
executed 2026-08-04 (slot 14) under its own source doc, BEFORE that doc's 2026-08-06 archival:
`instruments-service@48d3b10c` (script `scripts/gcs_orphan_cleanup_sports_curated_universe_2026_08_04.py`, full
five-part proof per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) — deleted=7,998 orphaned
league-specific objects, failed=0, skipped=8 (mixed-content risk, left in place), 11,186 already not-found. Closed +
evidenced at `/plans/archive/issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md` lines 582-601.
The batch9 `/ag-closeout-audit sports` run that generated this todo (2026-08-04, same day) sourced it from that doc's
pre-closure state — a same-day race between the closing commit and the audit's classification pass, not a genuine gap.
Checkbox flipped citing the existing evidence; no new GCS deletes performed this session (redoing a completed
five-part-proof delete against already-deleted/already-not-found objects would be pure waste, not a safety concern).
