---
doc_type: plan
title: Sports satellite AO batch 10 — /ag-closeout-audit orphan extraction (2026-08-06)
summary: >-
  Tenth AO-dispatch batch for sports, produced by a fresh `/ag-closeout-audit sports` run (2026-08-06, scheduled
  tranche-sharded dispatch agt-7b0c34, slot-13): 82 sports AG-primary docs classified via a per-doc Workflow pass (Phase
  1, 82/82 agents, 0 errors), then re-classified for self-dispatched coverage (19 docs are their own dispatch vehicle —
  assigned_vm: planning + active/open — and are covered by themselves, not orphans). Final verdicts: 16 archivable_now,
  25 covered-by-active-work (6 external + 19 self-dispatched), 10 exclude_cross_cutting (genuinely cross-AG/meta
  content, reported not orphaned), and 31 orphaned (20 partial coverage + 11 never touched by any covering plan). Every
  orphaned doc's remaining items were taxonomy-classified against the batch9 (2026-08-04) Deferred record +
  conflict-checked against the full covering-plan set. 4 items across 4 docs cleared the conflict check as genuinely
  uncovered, bounded, and AO-eligible (including 1 doc whose item batch9 had parked conflict-gated but whose competing
  claim — the consolidated closeout's backfill-path fix — provably covered a different code path, leaving the
  capture-path item genuinely open); these became the 4 todos below. The remaining 30 orphaned docs' items stay parked
  in the Deferred section, taxonomy-tagged (operator-gated / time-gated / conflict-gated / too-large-or-risky /
  human-only), referenced against batch9's deeper per-item record where unchanged. Status: active — operator-approved
  2026-08-07, flipped from draft.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, deployment-service, instruments-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-10, satellite-docs, ag-closeout-audit]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
    /plans/archive/2026_08/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/archive/issues/sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md,
    /plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-17"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit sports tranche run, 2026-08-06 — scheduled ag_closeout_auditor dispatch (agt-7b0c34, slot-13).
  Phase 0 (82-doc discovery via generate_ag_closeout_audit_candidates.py: 82 members, 13 covering docs, 16 never-cited
  NA) + Phase 1 (82-doc classification via Workflow fan-out, sonnet/medium, 82/82 agents) + Phase 2 (synthesis: 31
  orphans after self-dispatched reclassification) + Phase 3 (taxonomy + conflict-check vs the batch9 Deferred record and
  the full covering set) per cursor-configs/skills/ag-closeout-audit/SKILL.md's autonomous-mode procedure.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
---

# Sports satellite AO batch 10 — /ag-closeout-audit orphan extraction (2026-08-06)

## Methodology

Per `/cursor-configs/skills/ag-closeout-audit/SKILL.md`'s iterative-drain methodology, this run's Phase 3 first
re-checked the prior batch's (`sports_satellite_ao_dispatch_batch9_2026_08_04.md`) Deferred record before any fresh
triage: the 84 non-batchable items across 42 docs from 2026-08-04 were re-verified against today's live doc state, and
every orphaned doc's remaining items were re-classified + conflict-checked. 4 items became conflict-cleared batch todos;
30 orphaned docs remain parked (their items are unchanged since batch9's record unless noted). The full Phase 1 verdict
set (82 docs) is recorded in this run's report, which was carried in the dispatch's `/done` evidence string.

## Todos

- [x] ✅ DONE 2026-08-16 (slot-23, same session as the source doc) — root cause + fix: instruments-service@5f2f3ca619
      pinned `encoding="utf-8"` on every `resp.json(content_type=None)` call site in
      `instruments_service/reference_data/adapters/sports/adapters/{base,api_football,transfermarkt}.py` (aiohttp falls
      back to charset-guessing without it, which mis-decoded the incident's UTF-8 Polish name as Latin-1 mojibake — the
      write site was in **instruments-service, not MTDS** as this todo's own text guessed). Regression test added; full
      `quality-gates.sh` green. Not independently re-verified against a fresh live blob sample (needs LDR→main
      promotion + Cloud Build rebuild first) — corrupted historical rows are re-fetchable, so the routine catalogue
      regen cadence corrects them once deployed, satisfying this todo's re-captureable-window OR-clause. Full evidence +
      Progress Log: `/plans/archive/2026_08/issues/sports_catalog_dp_catalog_001_junk_name_crash_2026_08_06.md`
      (archived same session).
- [x] ✅ [CONFIG] P2. Close the sports trigger-tier residual gap — add `odds_t12h`, `odds_t4h`, `odds_t2h` forward
      snapshot triggers to `deployment-service/configs/sports-trigger-tiers.yaml`'s `pre_match.triggers` (following the
      existing `odds_t24h`/`t6h`/`t1h` pattern, `cloud_run_job_name: "uts-prod-market-tick-data-service-fast-t1-recon"`,
      tolerances ±30min T-12h / ±15min T-4h/T-2h). Shipped `deployment-service@9e1fd57ae` (config + 3 regression tests
      in `tests/unit/test_sports_trigger_tiers_config.py`, all passing; full `quality-gates.sh` green). Source:
      `sports_features_layer_findings_sweep_2026_07_18.md`. **Correction to this todo's VM-relaunch sub-step (stale
      architectural premise, found this session)**: the original text instructed relaunching a standalone
      sports-scheduler VM via `deployment-service/scripts/vm/launch-sports-scheduler-vm.sh`. Live investigation
      (`gcloud compute instances list --filter='name~"^sports-scheduler-"'` → empty) plus
      `sports_satellite_ao_dispatch_batch11_2026_08_09.md`'s independent, matching finding confirm production actually
      runs sports-scheduler as the Cloud Run **Job** `uts-prod-sports-scheduler`, dispatched every 5 minutes by Cloud
      Scheduler cron `uts-prod-sports-scheduler-cron` — not a VM. `deployment-service/Dockerfile:64`
      (`COPY configs/ ./configs/`) bakes the config into the image, and `cloudbuild.yaml`'s sports-scheduler build steps
      tag it both `:${COMMIT_SHA}` and `:latest`; Cloud Run **Jobs** (unlike Services) re-resolve `:latest` fresh on
      every execution (independently confirmed via `gcloud run jobs executions describe` in
      `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`), so the new triggers activate automatically on the
      next cron tick after the standard LDR→main→Cloud-Build pipeline rebuilds the image — no VM action exists to take,
      and running the stale script would have stood up a spurious duplicate scheduler double-dispatching every trigger.
      Not executed. Live-prod verification (image rebuild landed + a sample day's manifest shows all 6 horizons with
      per-fixture coverage) is split into todo 2a below since it depends on an async multi-stage pipeline that cannot
      complete synchronously in one session.
- [x] ✅ [INFRA] P2. Verify the `odds_t12h`/`odds_t4h`/`odds_t2h` triggers are live in production and firing — confirmed
      the deployed image + config, code-level correctness, and a cited reason why zero live fires have been observed yet
      (slot-13, 2026-08-10). **Image**: `uts-prod-sports-scheduler:latest` currently resolves to digest
      `sha256:6f59ec20…`, tagged with commit `309f75e8` (`gcloud artifacts docker tags list` cross-referenced against
      `gcloud run jobs describe`) — newer than the `b4a8f1ba` fix commit the prior session confirmed;
      `git show 309f75e8:configs/sports-trigger-tiers.yaml` re-confirms `odds_t12h`/`odds_t4h`/`odds_t2h` present.
      **Code correctness**: a synthetic unit test (6 fake fixtures, one per horizon, each at its exact `fire_at`
      instant) against the live `SportsTriggerScheduler.evaluate_pre_match_triggers` returns all 8 expected events
      (`odds_t24h`, `odds_t12h`, `odds_t6h`, `odds_t4h`, `odds_t2h`, `odds_t1h`, `features_pre_match`,
      `inference_pre_match`) — the evaluator itself is proven correct for the 3 new horizons, not just by inspection.
      **Live production evidence for the identical code path**: `gcloud logging read` on `uts-prod-sports-scheduler`
      shows the sibling MTDS-only pre-match triggers firing copiously — `odds_t6h` 1320 fires/24h (1152 in the narrower
      1d sample), `odds_t1h` 876, `odds_t24h` 1802/3d — proving the shared evaluation/dispatch mechanism
      (`evaluate_pre_match_triggers` → `fire_trigger` → Cloud Run Job trigger) works end-to-end in prod. **Cited reason
      for zero `t12h`/`t4h`/`t2h` fires to date**: an uncapped `list_blobs` sweep of all 3 candidate fixture-parquet
      path patterns shows the near-future fixture calendar is genuinely empty — 0 parquets for `day=2026-08-10` and
      `day=2026-08-11`, only 1 for `day=2026-08-12` — even though `uts-prod-instruments-service-sports-fixtures`
      completed successfully minutes before this check (01:25:55Z→01:27:13Z). The real-params
      `get_upcoming_fixtures(horizon_hours=48, lookback_hours=2.0)` call (exactly what `run_once()` uses) returns 0
      fixtures right now, matching the scheduler's own `"0 pre-match"` tick logs (61/70 sampled ticks over the last 24h
      fired 0 pre-match events — a normal sports- calendar lull, not a defect: leagues have off-days). The 3 new
      triggers only entered the deployed config ~4h ago (2026-08-09T21:23:17Z), so they've had far fewer real-world
      opportunities than the day/weeks-old `t24h`/`t6h`/ `t1h` — once a fixture with a kickoff 12h/4h/2h out re-enters
      the calendar, the proven-correct evaluator will fire it on the next 5-min tick. No code or deploy defect found;
      nothing further to fix. Evidence: `sha256:6f59ec20c3bb8fbf8472387a065ce34755ef2972a86d9fc0672fc2faf38eb391` tagged
      `309f75e8`.
- [x] ✅ [INFRA] P3. **DONE 2026-08-16 (slot-19, data_engineering, adopted infra craft)** — filed
      `/plans/active/issues/mtds_live_vm_tarball_freshness_default_proposal_2026_08_16.md`. Investigated current state
      before writing the recommendation: found the original `enforce` premise (filed 2026-08-04 against a `warn`
      default) is now superseded — `deployment-service@c1e0481` (2026-08-06) already flipped the shared library
      default `warn`→`auto`, and `deployment-service@450b212` (2026-08-07) fixed `auto` mode's own silent-skip bug so
      it now correctly blocks a launch on residual staleness. Recommendation: pin `LC_TARBALL_FRESHNESS=auto`
      explicitly (not `enforce`) at the 4 `mtds-live-*`/perp-clob-live launcher call sites — `auto` already gives the
      same never-launch-on-stale-code guarantee with self-heal instead of a hard abort; `enforce` offered as the
      explicit alternative if the operator wants a hard-block posture instead. Also fixed a stale doc-comment finding
      in `launcher_common.sh` (still said `warn` was the default) hit while researching —
      `deployment-service@8eae625c` (verified on origin). Implementation of the pin itself left as a follow-up todo in the new doc
      (`assigned_vm: NA` pending operator read of the auto-vs-enforce tradeoff), since this todo's own done-when only
      required the proposal doc to exist. Source:
      `sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`.
- [x] ✅ [DATA] P1. Verify-then-fix the ODDS_API CAPTURE path's blank-`fixture_id` raw generation — VERIFIED ALREADY
      FIXED via code read (option b, 2026-08-07): the capture path routes `_route_sports()` → `download_batch()` →
      `_build_fixture_rows()` — the SAME function fixed by `market-tick-data-service@3401c0ab` (2026-07-25);
      `odds_api_adapter.py:808` stamps `"fixture_id": str(af_fixture_id) if af_fixture_id is not None else ""`. Live WS
      path also fixed by `market-tick-data-service@d6d539a8` (2026-07-29) via `odds_api_ws.py:196`
      `"fixture_id": event_id`. Halftime doc checkbox flipped with code citations —
      `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` [DATA] P1 now ✅.

## Deferred — non-batchable (30 orphaned docs with parked items + 1 fully extracted, taxonomy-tagged)

Per the skill's iterative-drain methodology: before any future `batch11` triage, re-check the conflict-gated entries
below first (cheap — a few greps + reads) since a competing claim may have shipped/superseded by then. Operator-gated
and human-only entries need a real ruling, not re-triage. Time-gated entries need elapsed time/credentials, not
re-triage. Too-large-or-risky entries need their own dedicated plan. Where an entry was already recorded in
`sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s Deferred (the 84-item, 42-doc record), this section carries the
doc-level verdict + category and references that record; entries NOT in batch9's record are flagged `NEW`.

### Operator-gated (undecided design/judgment call or explicit sign-off requirement) (13 docs)

- **sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md** — design-only spec, 11 open items (§1-§3), exists
  BECAUSE of operator ruling BLK-b567ce7d (2026-07-21) requiring operator/spec sign-off before implementation dispatch.
  (batch9 record: 11 operator-gated items.) Not re-triageable.
- **sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md** — E8 legacy-delete irreversible
  `--apply`/`--drop-stale` firing for pre-canonical sports GCS objects — BLOCKED-OPERATOR pending explicit sign-off +
  the hard-stop-#2 carve-out contradiction + Part-5 100%-canonical-twin-coverage proof. (batch9: operator-gated.)
- **sports_catalog_league_grain_only_scope_2026_07_08.md** — 4 open todos: manifest-schema-extension DESIGN (operator
  ruling 2026-07-14), the gated builder, reference-data adapter extension, post-decision codex alignment — design +
  sequencing gated. (batch9: operator + conflict.)
- **sports_fixtures_browser_single_catalogue_source_2026_07_24.md** — freshness-cadence either/or: accept+label
  live-status lag vs build a live-day overlay — a design fork with no evidence-based tiebreaker. (batch9:
  operator-gated.)
- **sports_group_c_execution_backtest_harness_2026_07_21.md** — all 5 todos open (CLI wiring, fixture data source with
  CatalogManager branch decision, SportsMatchingEngine-vs-L0Matcher duplication resolution, docs placement) — each
  involves an undecided design/architecture call. (batch9: 5 operator-gated.)
- **sports_odds_bookmaker_coverage_enumeration_2026_06_20.md** — P1 Todo 2 (extend EXPECTED_BOOKMAKER_MARKET_SETS to 28
  unmapped league_ids OR add a tier_3_global/no_expectation tier) is an either/or design fork; P1 Todo 4 `trades`
  cluster-validation is a decide+implement. (batch9: 2 operator-gated.)
- **sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md** — [DATA] P0 extend venue→class mapping to 19
  unmapped venues (292,117 shards / 51.3M rows) — explicitly an operator/data-engineering decision. (batch9:
  operator-gated.)
- **sports_predictions_live_mode_activation_readiness_2026_07_21.md** — Todo 5 (run a sports archetype through the live
  path) + Todo 6 (permanent [OPERATOR] final go-ahead for live mode) + Todo 2(b) ODDS quota/second-source decision.
  (batch9: operator + conflict.)
- **sports_prelaunch_cf5_verify_residual_2026_07_24.md** — C3 pre-launch-window corpus decision (10,345 objects) —
  either/or fork explicitly operator-gated in the doc's own todo text. (batch9: operator-gated.)
- **ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md** — [CODE] P3 wire-vs-drop `--family` scope
  flag — unresolved design decision. (batch9: operator + conflict.)
- **sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md** — `_build_fixture_league_map_from_gcs` mapping-coverage
  gap (22-82 real leagues vs 0-2 overlapping) — doc's own text: "needs an operator/architecture decision on whether the
  mapping should use the…". (batch9: operator + conflict.)
- **sports_features_layer_findings_sweep_2026_07_18.md** — §E [MODEL] P2 (T-6h/T-2h as MODEL horizons) — a model design
  call (the §E [CONFIG] P2 trigger-tier item was extracted into todo 2 above). (batch9: operator + conflict.)
- **sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md** — R [PROCESS] P1 codify an entity-rename/split
  consumer-migration authoring rule into codex — operator/codex-authoring ruling required. (batch9: operator +
  conflict.)

### Conflict-gated (already claimed by an open todo elsewhere in the covering set) (5 docs)

- **sports_odds_feature_naming_canonicalization_2026_07_21.md** — todo 9 [REVIEW] P3 FSS↔ml-service↔strategy-service
  naming parity test — explicitly sequenced after the still-unshipped 3-repo four-way naming migration (see the
  too-large entry for `sports_odds_feature_naming_four_way_mismatch` below); not dispatchable ahead of it. (batch9:
  conflict-gated; the batch9 citation text is truncated mid-sentence — re-checked this run, no live claiming todo exists
  yet, the gate is the sequencing dependency itself.)
- **instrument_availability_league_and_question_group_partition_shapes_2026_08_03.md** — Todo 4 [DATA] P1 historical
  migration of ~172,592 sports `league=` instrument_availability objects — batch9 defers Time-gated (league_id namespace
  migration prereqs) + conflict-gated (batch9's own prediction-migration todo covers part of the same migration
  ground) + operator-gated (Todo 1 canonical question_group target ruling).
- **sports_halftime_odds_sfi_vs_inplay_2026_07_16.md** — (a) reconcile the market-data-sports manifest for 2,436 deleted
  T-0 shards — owned by the in-flight bucket cutover (its unmerged shard must not be merged by anyone else); (b) retrain
  the 3 quarantined CLV models post-ODDS_FEATURES-recompute — time-gated on the recompute landing. (The blank-fixture_id
  capture-path item was extracted into todo 4 above — batch9's conflict-gated citation for it is truncated, and the
  closeout's competing claim provably covered the backfill path, not the capture path.)
- **footystats_matches_predictions_fetch_gaps_2026_07_08.md** — sole open todo #4 (re-verify + re-dispatch footystats
  backfill VM) is BLOCKED-PREREQUISITES on the fix tracked in its sibling self-dispatched doc
  `footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md` (a permanently-regenerating
  422-row 4-league population needing a real fix, not a re-verify) — conflict-gated on the sibling claim, and the doc's
  own na-eligibility entries confirm KEEP-NA. NEW (not in batch9's Deferred record as a sports entry).
- **sports_predictions_live_mode_activation_readiness_2026_07_21.md** — Todo 3 launch-mdps-features-live.sh
  cross-cutting exec-dispatch wiring — production deployment of the MDPS+FSS live path claimed by the
  consolidated-closeout Track V open todos. (batch9: conflict + operator.)

### Time-gated (elapsed-time/credential/vendor dependency not yet reached) (2 docs)

- **data_completion_sports_2026_07_24.md** — item 4: API-Football daily-quota bump to 1.5M/day — the branch decision is
  RULED (2026-07-28) but the vendor account-tier upgrade + spend is the outstanding credential-gated action. (batch9:
  time-gated.) Items 1-3 are covered by batch9's open todos.
- **sports_odds_feature_naming_four_way_mismatch_2026_07_21.md** — the 3-repo four-way naming migration (UAC schema +
  features-service producer + ml-service loader + strategy-service consumers) — too-large-or-risky for a batch todo
  (cross-repo schema change with blast radius), needs its own dedicated migration plan; ALSO the sequenced-gate for the
  parity-test item above. NEW (not in batch9's Deferred record).

### Too-large-or-risky-for-a-batch-todo (own dedicated migration/design pass needed) (1 doc)

- **sports_catalog_league_grain_only_scope_2026_07_08.md** — (also operator-gated, above — listed once, both tags apply:
  schema-extension design + fixture-grain catalogue builder are a dedicated design+migration pass, not batch todos.)

### Genuinely human-only / multi-tranche index (report-only per primary-owner rule) (6 docs)

The following docs are `assigned_vm: NA` multi-tranche indexes / findings ledgers whose remaining sports-scoped items
could not be resolved to a bounded AO-eligible extraction this run. Per the skill's primary-owner rule (parent_epic),
the OWNING tranche for the instruments-master-parented docs below is NOT sports — this tranche reports their sports
orphan verdict; writes/retags belong to the owning tranche's audit. All NEW (not in batch9's Deferred record):

- **instruments_remaining_work_audit_2026_07_10.md** — multi-tranche synthesis index (all 5 AGs + cross-cutting,
  parent_epic: instruments_master); open sports-scoped work items cited but each resolves to a sibling doc's claim (e.g.
  mtds_is_full_adapter_smoketest_findings as the 12-open-todo master record) — needs the owning tranche's fold-in, not a
  sports batch todo.
- **mtds_is_full_adapter_smoketest_findings_2026_07_07.md** — cross-tranche master findings ledger (12 open todos incl.
  P0 crash classes); sports slice not cleanly separable into a bounded batch item without re-reading every finding —
  owning tranche: instruments_master.
- **instruments_docs_audit_outstanding_items_2026_07_08.md** — multi-tranche index with open sports-scoped work
  (fixture/player catalogue items) — owning tranche: instruments_master.
- **adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md** — sole remaining open item is the
  [DECISION] P2 reconciliation-cadence todo — operator decision (tradfi batch7 (2026-08-06) independently reached the
  same verdict); also claimed in tradfi's consolidated closeout Sources list.
- **estate_orphan_assessment_2026_07_21.md** — sports-scoped work complete; the open item is the cross-tranche cefi/defi
  CONTESTED todo 6 (KEEP-NA vs RECLASSIFY) — claimed by cefi batch7 + tradfi batch7 records; owning tranche:
  instruments_master.
- **predictions_ml_walk_forward_and_arb_2026_06_20.md** — 4 open todos, one chained walk-forward/arb research arc —
  sports/prediction dual-tag (the historically-confirmed same-work pairing); parent_epic: predictions_master → the
  prediction tranche is the owner; its consolidated closeout + prediction batch6 already cite it.

### Fully extracted this batch (1 doc)

- **sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md** — sole remaining open todo (the [INFRA] P3
  LC_TARBALL_FRESHNESS proposal) was extracted into todo 3 above; all other todos closed (LADBROKES re-stamp DONE
  2026-08-05, honest-coverage rollup DONE, capture-VM fix DONE). The doc's batch9 operator-gated record (LADBROKES
  re-stamp) is resolved since.

## Progress Log

- **slot-13 (ag_closeout_auditor agt-7b0c34) 2026-08-06**: Full `/ag-closeout-audit sports` run per SKILL.md autonomous
  mode. Phase 0: `generate_ag_closeout_audit_candidates.py --tranche sports` — 82 members, 13 covering docs, 16
  never-cited (all NA). Phase 1: Workflow pipeline over all 82 docs (sonnet/medium) — 82/82 agents completed, 0 errors.
  Phase 2: self-dispatched reclassification (19 docs, assigned_vm: planning + active/open) — final: 16 archivable_now,
  25 covered (6 + 19), 10 exclude_cross_cutting, 31 orphaned (20 partial + 11 never-touched). Phase 3: taxonomy mapping
  vs batch9's Deferred (84 items/42 docs) + per-candidate conflict-check (grep covering set for every candidate's
  claims: halftime fixture_id → closeout Track E's fix provably covers the BACKFILL path, capture path genuinely open;
  parity test → sequenced after the too-large migration; footystats → sibling self-dispatched claim;
  instrument_availability league= → league_id migration prereqs; etc.). 4 conflict- cleared bounded items → this batch's
  4 todos (flipped `active` 2026-08-07, operator-approved). 30 orphaned docs' items parked in Deferred above (29 with
  non-batchable taxonomy entries + 1 fully extracted); ledger: parked_findings = 29 doc-level entries written in this
  Deferred section (plus 6 report-only multi-tranche index docs counted separately as report-only, not parked). No
  retags, no shared doc writes performed this run (classification + draft only — no multi-tranche doc was edited).
  OOM-directive acknowledgment (2026-08-06 operator broadcast): no heavy RAM/IO-bound local process was launched by this
  session — Phase 1 ran as subagent model calls only; nothing OOM-killed on this slot; no progress-log event to record
  beyond this statement.
- **Observation for the operator**: several batch9 Deferred citations are truncated mid-sentence with a trailing "…"
  (e.g. the halftime fixture_id, parity-test, and CLV-retrain entries), making the 08-04 conflict claims not fully
  recoverable from the record — this run re-verified each affected item live instead (see the per-item notes above), but
  a future audit would benefit from batch9's Deferred entries being completed or explicitly retired.

## Codex SSOTs

- /plans/active/task_template.md §4 — finalize-plan-coverage rule + dispatch-scope eligibility test
- /plans/PLAN_FORMAT.md — `status: draft` semantics, frontmatter schema
- /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md § "Dispatch-scope eligibility"
- /codex/11-project-management/ — findings triage, archival ritual
- /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 2-3 — primary-owner rule + the shared
  conflict-check protocol
- /cursor-configs/skills/ag-closeout-audit/SKILL.md — this skill (procedure SSOT)
- /codex/02-data/honest-absence-downstream-handling.md — blank-but-present column anti-pattern (todo 4)
- /codex/05-infrastructure/data-pipeline-alerts.md + /codex/04-architecture/shard-level-failure-isolation.md —
  DP-CATALOG-001 context (todo 1)

## Progress Log

- **Operator ruling 2026-08-07**: APPROVED — flipped `status: draft` → `active`. Pre-flip investigation (read-only)
  confirmed 82-doc Phase-1 classification + Phase-3 conflict-check against the full covering set, 4 todos targeting 4
  distinct files/repos with no overlap, no rename/archival ops among them.
- **slot-17 2026-08-09**: Worked todo 2 (trigger-tier residual gap). Shipped `deployment-service@9e1fd57ae` — added
  `odds_t12h`/`odds_t4h`/`odds_t2h` to `configs/sports-trigger-tiers.yaml`'s `pre_match.triggers` + 3 new regression
  tests (`tests/unit/test_sports_trigger_tiers_config.py`, all passing; full `quality-gates.sh` green). **Did not**
  execute the todo's VM-relaunch sub-step: `gcloud compute instances list --filter='name~"^sports-scheduler-"'` returned
  empty, and cross-referencing `sports_satellite_ao_dispatch_batch11_2026_08_09.md` (independent, matching finding),
  `deployment-service/Dockerfile:64`, and `cloudbuild.yaml`'s sports-scheduler build steps confirmed production runs
  sports-scheduler as the Cloud Run Job `uts-prod-sports-scheduler` on a 5-min cron, not a standalone VM — the config
  ships automatically via the standard image-rebuild path, and the VM launch script would have created a harmful
  duplicate scheduler. Corrected the todo text in place rather than executing it as literally written; split live-prod
  verification into new todo 2a (async pipeline, can't complete synchronously this session).
- **slot-23 2026-08-09 (todo 2a, partial — image rebuild + deploy confirmed, manifest coverage still pending)**: Worked
  the "verify odds_t12h/t4h/t2h live in production" todo. Confirmed the full async pipeline through image rebuild +
  first live execution:
  - Promote PR #809 (`chore(promote): LDR → main`, carrying `deployment-service@9e1fd57ae`) merged 2026-08-09T21:19:25Z
    (`sit-gate/fleet-green` + `quality-gates-v2` + semver-agent all green, auto-merge armed).
  - New sports-scheduler image built + tagged `:latest` at 2026-08-09T21:23:17Z, digest tag
    `b4a8f1baf20c99e32ca67feb0477352041cad707` — confirmed via `git show b4a8f1ba:configs/sports-trigger-tiers.yaml`
    that the deployed tree contains `odds_t12h` (and by extension `odds_t4h`/`odds_t2h`, same commit).
  - First Cloud Run Job execution on the new image: `uts-prod-sports-scheduler-4lckr`, started 21:25:09Z, completed
    successfully 21:26:32Z (`status.conditions[0].type=Completed, status=True`) — confirms the rebuilt image runs clean,
    not just that it built.
  - **Manifest coverage for the 3 NEW horizons (odds_t12h/t4h/t2h) not yet observable**: polled `gcloud logging read`
    against the scheduler's own `TRIGGER [odds_t12h|odds_t4h|odds_t2h]` log lines across 5 execution ticks spanning
    21:23:17Z→21:51:03Z (~28 min, 6 scheduler cycles) — zero fires. This is NOT a bug signal: `odds_t1h` (a
    pre-existing, already-working horizon) is confirmed firing correctly in the SAME execution window via historical log
    evidence (e.g. `TRIGGER [odds_t1h] fixture=1493047 ...` at 18:45:42Z), so the trigger-evaluation mechanism itself
    works — the 3 new horizons simply need a real fixture's kickoff to land inside their (T-12h±30min / T-4h±15min /
    T-2h±15min) window, which hasn't happened yet in the ~28 min since deploy. This is genuinely time-gated on the
    sports fixture schedule, not something a longer synchronous session can force. Released back to queue
    (`reason_code: GATED`) rather than holding the session for an unbounded wait — the next dispatch should re-run the
    same `gcloud logging read ... textPayload:"odds_t12h" OR "odds_t4h" OR "odds_t2h"` query (window start
    `2026-08-09T21:23:17Z`) and, once at least one fire is observed per horizon, pull that day's manifest to confirm
    per-fixture coverage and close this todo.
- **slot-13 2026-08-10 (todo 2a, closed — deploy/code verified correct; zero fires explained by a real fixture-calendar
  gap, not a defect)**: Re-ran the same live check ~4h post-deploy; still zero `odds_t12h`/`t4h`/`t2h` fires
  (`gcloud logging read` over both 1d and 3d windows). Went one level deeper than the prior session to rule out a
  code/deploy regression rather than re-releasing GATED again:
  - Confirmed the CURRENTLY-live image (`uts-prod-sports-scheduler:latest` → digest `sha256:6f59ec20…`) is tagged
    `309f75e8` — a commit newer than the `b4a8f1ba` fix commit — and
    `git show 309f75e8:configs/sports-trigger-tiers.yaml` still carries all 3 new triggers. Ruled out "the old image
    never got replaced" as an explanation.
  - Wrote a synthetic unit test calling the live `SportsTriggerScheduler.evaluate_pre_match_triggers` with one fake
    fixture per horizon, each positioned exactly at its `fire_at` instant — all 8 expected events fire correctly
    (including `odds_t12h`/`t4h`/`t2h`). This rules out a latent evaluator bug: the code is proven correct, not just
    "looks right by inspection".
  - Compared against sibling MTDS-only pre-match triggers with the IDENTICAL evaluation/dispatch code path:
    `odds_t6h`/`odds_t1h`/`odds_t24h` fire copiously (1320/876/1802 over their respective sample windows) — proves the
    shared mechanism (evaluate → fire_trigger → Cloud Run Job dispatch) works end-to-end in prod; the difference is not
    "pre-match triggers are broken", only these 3 specific ones.
  - Root cause of the zero count: an uncapped `list_blobs` sweep of all 3 fixture-parquet path patterns shows the
    near-future fixture calendar (`day=2026-08-10`, `day=2026-08-11`) has 0 parquets — genuinely no scheduled fixtures —
    even though `uts-prod-instruments-service-sports-fixtures` had JUST completed successfully (01:25:55Z→01:27:13Z) at
    check time. `get_upcoming_fixtures(horizon_hours=48, lookback_hours=2.0)` — the exact call `run_once()` makes —
    returns 0 fixtures right now, matching the scheduler's own `"0 pre-match"` tick logs (61/70 sampled ticks over 24h).
    This is a normal sports-calendar lull (leagues have off-days), not a pipeline defect — and it applies to ALL
    pre-match horizons equally, not selectively to the 3 new ones; `t6h`/`t1h`/`t24h` simply had days-to-weeks of prior
    opportunities before this lull started, vs. ~4h for the new triggers.
  - **Conclusion**: no code or deploy defect exists; the mechanism is proven correct and will fire the first time a
    fixture with a kickoff 12h/4h/2h out re-enters the calendar. Flipped todo 2a `- [x]` on this evidence per the todo's
    own "or a cited reason why a horizon cannot fire" done-when clause — an unbounded wait for a specific live fixture
    to materialize is not further-session-actionable work.
- **context-scout 2026-08-14**: populated context_scope (4 entries).
- **context-scout 2026-08-17**: re-verified; context_scope unchanged (4 entries, all resolve) — dispatch-batch
  coordinator, genuinely code-free (every open todo is a checkbox-reconciliation against named source docs already in
  `related:`).
