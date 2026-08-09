---
doc_type: plan
title: TradFi satellite AO batch 7 — fresh /ag-closeout-audit extraction (4 clean orphans)
summary: >-
  Seventh AO-dispatch batch for tradfi, produced by a fresh `/ag-closeout-audit tradfi` pass on 2026-08-06 (autonomous
  mode, scheduled `ag_closeout_auditor` worker, sharded-tranche dispatch). Phase 0 rediscovered the covering set as 11
  docs (via `generate_ag_closeout_audit_candidates.py`, cross-verified against the dependency-graph path) and enumerated
  54 real tradfi-primary candidates. Phase 1 ran a 54-agent Workflow classifying every candidate against the 11-doc
  covering set: 1 excluded (genuine mistag — `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` is 100%
  defi/cefi-scoped), 15 archivable now, 2 archivable-after-planned-work (already self-dispatched or genuinely covered),
  and 36 orphaned (11 partial-coverage, 25 never-touched) — up from batch6's 12, mostly because this pass read every
  candidate fresh rather than re-using batch6's 2026-08-01 snapshot, and 5 days of new findings landed since (2 new
  issue docs created 2026-08-03/04, plus several existing docs' "latest dated section" moved since batch6 last read
  them). Of those 36, 4 cleared the Phase-3 conflict-check as bounded, conflict-free, AO-eligible work and are drafted
  below (from 5 distinct source docs — 2 combined into one todo, see rationale below). The rest stay deferred across 5
  categories (too-large-or-risky, operator-gated, self-dispatched-already/stale-tag, already-drafted-elsewhere-pending-
  promotion, and cross-tranche-owned) — see the Deferred/Flagged sections for the full accounting (36 orphans = 5
  drafted + 31 deferred/flagged, reconciled below).

  **Important standing-state note this batch surfaces**: `tradfi_satellite_ao_dispatch_batch6_2026_08_01.md` has sat
  `status: draft`, unreviewed, for 5 days. This batch does not depend on batch6 landing first (drafts are inert and
  independently reviewable), but the operator should know both are queued.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, features-service, instruments-service]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-7, satellite-docs, conflict-checked]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch6_2026_08_01_finalize.md,
    /plans/archive/issues/tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md,
    /plans/active/issues/tradfi_recovery_quarantine_registration_gap_2026_07_27.md,
    /plans/active/issues/tradfi_fx_krw_usd_triplicate_venue_partitions_2026_08_04.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
    /plans/active/issues/features_delta_one_instrument_type_filter_stg_bucket_404_and_swing_outcome_targets_dispatch_gap_2026_08_03.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit tradfi run 2026-08-06 (autonomous / AO-dispatched mode, sharded daily `ag_closeout_auditor` worker,
  dispatch agt-7d91ed, slot 3, operator away). Phase 0 used `generate_ag_closeout_audit_candidates.py` (the shipped SSOT
  tool) for the covering-plan + candidate-member discovery, extended with a direct Python dump of the full 54-member
  candidate list (the CLI only prints the never-cited subset). Phase 1 classified all 54 real tradfi-primary candidates
  via a `Workflow` (54 agents, 0 errors, 726 tool calls, ~1.41M ms wall-clock). Phase 3 re-checked batch6's own Deferred
  sections first per the skill's iterative-drain methodology (batch5's MDPS `continuous_future` re-test did ship
  2026-08-03 but the result — 20.8% hit rate, up from 18.9% — did NOT clear the `tradfi_sp500_ml_and_arb_...` blocker,
  so that doc correctly stays deferred), then ran the conflict-check against the full 11-doc covering family plus a live
  corpus-wide grep before drafting any todo below. Two premises were independently re-verified against live source
  before drafting: `migrate_tradfi_canonical_2026_07.py`'s `_rel()` still unconditionally does `path.find(marker)` with
  no `_quarantine/`-prefix guard (confirmed live read), and the same file carries zero `_VENUE_REMAP`-equivalent
  validation while its predecessor `migrate_tradfi_to_hive.py` does (confirmed via grep diff).
assigned_role: data_engineering
effort: max
sequential: false
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_canonical_2026_07.py,
    instruments-service/scripts/cleanup_legacy_twins.py,
    features-service/features_service/delta_one/engine/orchestrator.py,
  ]
---

# TradFi satellite AO batch 7 — fresh audit extraction

> **Status: active — operator-approved 2026-08-06, dispatching.** Per the ag-closeout-audit skill's autonomous-mode
> contract, a freshly-drafted batch always ships `status: draft` regardless of how clean the conflict-check came back;
> flipping to `active` to actually dispatch it is an operator decision, never autonomous.
>
> All 4 todos below are same-priority-independent and were checked for file collisions (see the matrix near the bottom)
> — all 4 touch distinct repos/files, no overlap.

## Why this batch exists

This is the first fresh `/ag-closeout-audit tradfi` pass since batch6 (2026-08-01), run as a full independent Phase 0-3
pass (not a delta) per this dispatch's autonomous-mode instructions. batch6 itself is still unapproved (`status: draft`,
5 days old) — this batch does not wait on it.

1. **4 genuinely new, bounded, conflict-free findings surfaced** that batch6 could not have seen (2 source docs postdate
   batch6's 2026-08-01 cutoff entirely; 2 more are prose-only recommendations added to existing docs' Progress Logs on
   2026-08-04/05, after batch6 last read them):
   - `tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`'s final P3 investigation (RE-VERIFIED 2026-08-05) concluded none
     of the 3 existing tradfi migration scripts can backfill the pre-existing blank-`instrument_id` CME chain-bundle
     manifest rows — a new, dedicated script is needed and none of the 11 covering-family docs claim it.
   - `tradfi_recovery_quarantine_registration_gap_2026_07_27.md`'s Progress Log (2026-08-04) names a latent `_rel()`
     prefix-stripping bug in `migrate_tradfi_canonical_2026_07.py` as a "separate preventative fix," never filed.
   - `tradfi_fx_krw_usd_triplicate_venue_partitions_2026_08_04.md` (created 2026-08-04) root-caused a sibling gap in the
     SAME file — no `_VENUE_REMAP`-equivalent venue-token validation, unlike the predecessor script it replaced.
   - `features_delta_one_instrument_type_filter_stg_bucket_404_and_swing_outcome_targets_dispatch_gap_2026_08_03.md`'s
     Progress Log (2026-08-05) recommends a `-test-`-aware gap-tolerance relaxation for the sparse dev-tier TRADFI
     candle corpus, never converted into a checkbox.
2. **One item batch6_finalize's own todo 2 explicitly anticipated is now ready.** batch6 deferred
   `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s 0%-twin-coverage root-cause investigation, writing
   "before either a batch7 todo or a direct operator ask" — this batch is that batch7. (Confirmed distinct from the
   separately- already-resolved `tradfi_legacy_twin_candidate_set_995_to_900_unexplained_shrink_2026_08_05.md`, which
   explains a different question — why the candidate _population_ shrank, not why the loaded rows show 0%
   twin-coverage.)
3. **One re-verification ruled a candidate back OUT.** `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` was
   batch6's explicit "strong batch7+ candidate the moment [batch5's todo 2] ships" — that todo did ship (2026-08-03),
   but its result (continuous_future hit rate 18.9%→20.8%, still 79.2% `empty_confirmed`) shows the underlying data gap
   is real and did NOT close. Stays deferred, not drafted.

## Todos

- [x] ✅ [DATA] P2. **DONE 2026-08-09 — `market-tick-data-service@63cff354`.** Build + run a manifest-metadata
      reconciliation script for CME chain-bundle rows with a blank `instrument_id`. **Live census (2026-08-09) differs
      materially from this todo's original 28,307+111-for-ES-alone figure**: a fresh count against the LIVE manifest
      (not the 2026-07-30 snapshot) found only 3,267 candidate rows across 41 distinct (underlying, data_type) roots —
      10 days of continued backfill/recapture activity with the fixed writer had already superseded most of the original
      population with correctly-tagged twins (confirmed: 2,492 of the 3,267 restamped rows deduped against a
      pre-existing correctly-tagged row for the same (date, data_type, instrument_id) key). Full per-root breakdown in
      the Progress Log below. Script: `scripts/restamp_tradfi_cme_chain_bundle_blank_instrument_id_2026_08_09.py` —
      reads the manifest index, selects `venue=CME` + `instrument_type in {futures_chain, options_chain}` +
      `data_type in {ohlcv_1m, ohlcv_1s}` + `capture_status=captured` + blank `instrument_id` + non-blank `underlying` +
      `instrument_count>0`, derives the canonical bundle id via the already-shipped
      `_resolve_chain_bundle_manifest_id(venue, instrument_type, underlying, data_type)`, CAS-rewrites
      (`if_generation_match`) with a pre-write snapshot
      (`_index/backups/availability_index.pre_cme_chain_bundle_blank_id_restamp_20260809T144613Z.parquet`). Applied to
      production: 3,267/3,267 resolved (0 quarantined), 2,492 deduped, generation `1786286566278323→1786286789218193`.
      **Fresh independent post-apply census confirms 0 remaining blank-`instrument_id` rows** for this exact scope and 0
      duplicate (date, data_type, instrument_id) keys. 12 regression tests added
      (`tests/unit/scripts/test_restamp_tradfi_cme_chain_bundle_blank_instrument_id_2026_08_09.py`), `quality-gates.sh`
      green. Repo: market-tick-data-service. **Scope note — 2 adjacent larger populations found, deliberately NOT
      touched**: `instrument_type=combo` (~301K rows) is by-design id-less (confirmed via `_tradfi_manifest_shard.py`'s
      own comment — a spread bundle has no single resolvable per-bundle id); `instrument_type=FUTURE` (~19.6K rows,
      singular/canonical-cased — a DIFFERENT, non-chain-bundle write path) is a distinct root cause outside this todo's
      literal wording ("CME futures_chain/options_chain shards") — follow-up issue doc:
      `issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`. Source:
      `issues/tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`.

- [x] ✅ [DATA] P2. **DONE 2026-08-09 — `market-tick-data-service@ff6c2f4a` (hardening) +
      `market-tick-data-service@e72feb7c` (unrelated STEP 5.95 unblock, pushed sha for the locally-committed `8c5fe244`,
      amended by quickmerge to add the `Quickmerge:` trailer).** Harden `migrate_tradfi_canonical_2026_07.py` against 2
      confirmed recurrence risks — combined into ONE todo because both edit the same file.** (1) `_rel()` (lines
      ~159-163) unconditionally does `path.find(marker)` with no `_quarantine/`-prefix guard, so re-running the
      migration against an already-quarantined object silently reverts its computed rel-path to the pre-quarantine
      location instead of recognizing it's already quarantined — confirmed still live via direct source read 2026-08-06.
      Add a `_quarantine/`-prefix-aware branch so an already-quarantined object's rel path is computed correctly. This
      bug is inherited by `rebundle_tradfi_chains_2026_07.py` too (confirmed: it imports `_rel` directly from this
      module), so the one-file fix closes both. (2) The script has zero venue-token validation against
      `VENUES_BY_ASSET_GROUP['tradfi']` — unlike its predecessor `migrate_tradfi_to_hive.py`, which has a `_VENUE_REMAP`
      dict (confirmed via grep diff 2026-08-06: zero hits in the current script, present in the predecessor) — so a
      future run that encounters a wrong/stray venue token (as already happened once for the KRW-USD FX case) would
      again promote it verbatim into a canonical GCS path + manifest row with no guard. Add a `_VENUE_REMAP`-equivalent
      normalization/validation step mirroring the predecessor's pattern. Repo: market-tick-data-service. **Done when**:
      both fixes are shipped with regression tests (one exercising an already-quarantined-object `_rel()` call, one
      exercising a non-canonical venue token being rejected/remapped instead of silently promoted), and
      `quality-gates.sh` is green. Source: `issues/tradfi_recovery_quarantine_registration_gap_2026_07_27.md`,
      `issues/tradfi_fx_krw_usd_triplicate_venue_partitions_2026_08_04.md`.

- [ ] [DATA] P2. **Investigate why the tradfi legacy-twin bucket-delete dry-run measures 0% canonical-twin coverage
      instead of the expected near-100% — root-cause only, no delete/apply.** The 2026-07-30 dry-run of
      `instruments-service/scripts/cleanup_legacy_twins.py --asset-group tradfi --report-uri     _index/audit/orphan_sweep_tradfi.parquet --dry-run`
      loaded 900 class-B legacy-twin candidate rows and found 0 deletable — every single row reported reason "canonical
      twin NOT captured in manifest," reconfirmed unchanged by na-eligibility-audit passes on 2026-07-31 and 2026-08-02.
      A genuine manifest-registration gap is the leading hypothesis (per the gating doc's own Progress Log) but has
      never been directly investigated. Trace a representative sample of the 900 blocked rows: confirm whether their
      claimed canonical twins genuinely are absent from the manifest (a real registration gap — identify which
      writer/backfill should have registered them and didn't), or whether the twin-lookup logic in
      `cleanup_legacy_twins.py` itself has a matching bug (e.g. an id-shape mismatch between the legacy row's derived
      canonical id and how the manifest actually stores the twin). Do NOT run `--apply` or any delete — this todo is
      diagnostic only; the delete stays gated on this investigation's outcome plus a fresh 100%-coverage re-run. Repos:
      instruments-service, market-tick-data-service. **Done when**: a dated finding is recorded in
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s Progress Log identifying the root cause (registration
      gap vs. lookup-logic bug) for a representative sample, with enough detail that a follow-up fix (in whichever repo
      owns the actual defect) can be scoped as its own todo. Source:
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`.

- [ ] [CODE] P3. **Relax `_filter_market_state`'s gap-tolerance check for the sparse dev-tier TRADFI candle corpus.**
      features-service's delta_one `orchestrator.py::_filter_market_state` uses `boundary_tolerance = max(2, 4)` (4 NaN
      candles max within trading hours) — correctly tuned for production-density data, but too strict for the current
      sparse dev-tier TRADFI corpus (confirmed via direct GCS evidence: only 3-4 equity instruments total in
      `market-data-tick-tradfi-prd`, 0-4 per date, no `-test-`-bucket candle data at all). Add a `-test-`/`IS_TEST_RUN`-
      aware relaxation (or a documented skip) of this specific check — the validator itself is correct (data IS
      genuinely sparse, no code defect), a dev-tier run that will never have dense data shouldn't fail on a
      production-density assumption. Repo: features-service. **Done when**: the relaxation/skip is implemented, gated
      behind the existing `-test-`/`IS_TEST_RUN` signal (not a blanket loosening of the production check), with a
      regression test covering both the relaxed dev-tier path and the unchanged production-density path, and
      `quality-gates.sh` is green. Source:
      `issues/features_delta_one_instrument_type_filter_stg_bucket_404_and_swing_outcome_targets_dispatch_gap_2026_08_03.md`.

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo)

- **`data_completion_tradfi_2026_07_15.md`** — unchanged from batch1-6. Phase 0 layout audit, ~133K-cell NASDAQ/NYSE
  backfill, G1 `--apply-write` denominator-seed execution (gate-b still frozen), and the catalogue-scheduler terraform
  wiring stay too large/interdependent for a batch todo.
- **`issues/tradfi_canonical_path_migration_design_2026_07_19.md`** — unchanged from batch1-6. Steps 5-6 are explicit
  `[GATE]` operator-go items over a 2.73M-object corpus; the whole sequencing (steps 4-8) stays deferred as one unit.
- **`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s full CME instrument-definitions re-fetch** (~2,368 days) —
  unchanged from batch6, still "a real backfill campaign... needs its own dedicated plan/VM launch." (3 of this doc's
  other items — ES_OPT launch, anomalous-Sundays investigation — are already drafted in batch6, still pending operator
  approval; not re-drafted here.)
- **`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`** — re-confirmed still `orphaned_never_touched` and still
  conflict-gated. batch5's blocking todo (MDPS `continuous_future` hit-rate re-test) DID ship 2026-08-03, but the result
  (20.8%, up from 18.9%) shows the gap is real and did not close (still 79.2% `empty_confirmed`). All 7 remaining items
  stay deferred until the underlying MDPS data gap itself is addressed as its own project.
- **`tradfi_pred_manifest_consolidator_cron_stuck_paused_2026_07_29.md`'s P3 auto-resume item** — implementing bounded
  auto-resume in UTL's `consolidator_liveness` watchdog means editing a shared T0 dependency to actively mutate live
  production Cloud Scheduler state — the source doc's own text calls this "a real, fleet-wide-blast-radius design
  decision," explicitly out of a single batch todo's scope. Also multi-AG (`[tradfi, prediction]`).
- **`phantom_audit_estate_coverage_gap_2026_07_10.md`** — making the phantom audit's bucket list dynamic (42 un-audited
  manifests across all 5 AGs, only 3 tradfi-specific) needs a runtime/parallelism design call (fan-out over ~20 buckets
  of full-corpus GCS walks vs. the weekly single-walk-discipline cadence) before it's a dispatchable todo — correctly
  `assigned_vm: NA` per 3 independent na-eligibility-audit passes. Also genuinely cross-AG in scope, not tradfi-primary.

## Deferred — operator-gated (a ruling unblocks these; unchanged or newly-found, NOT re-asked if already asked)

Unchanged from batch6 (not re-asked): `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (which
`EXCHANGE_CODE_TO_NAME` registry is authoritative);
`issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s `[DESIGN] P2` on whether
real aggregated `ohlcv_15m`/`ohlcv_24h` TradFi bars are wanted;
~~`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`'s residual catalogue-script `--apply` reapplication
(91 CBOE + 312 DBEQ rows)~~ — **STALE, corrected 2026-08-07 (operator ruling, via consolidated NA-blocker-digest audit):
"go ahead" is the confirmed-current answer.** This doc's own listing here was written ~3h BEFORE that ruling landed in
the source doc (`canonical_id_p1...`'s own todo already reads "RULED 2026-08-06: go-ahead to run `--apply`" and
correctly self-flagged this exact staleness) — this doc's copy just never got updated. No longer operator-gated; the
`--apply` is cleared to run. See `plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md` item 1/6 (now
closed) for the full contradiction trace; the entirety of
`issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md` (item 3 is the same `EXCHANGE_CODE_TO_NAME` gate
above).

Newly found this pass:

- **`tradfi_adapter_dead_code_fallback_audit_2026_07_25.md`'s Finding M-3** — decide whether to wire
  `DatabentoCmeConverter`/`DatabentoOpraConverter` into the live path, delete them, or document as intentionally unused;
  a 3-way judgment call with no evidence-based tiebreaker.
- **`tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`'s todo 1 (P0) + dependent todo 4** — a
  destructive `--apply` migration/purge over ~81K CME+CBOE `WithinBoundsTradfiSourceZero` manifest rows, explicitly
  gated on operator go-ahead per the delete-safety protocol (analogous to
  `tradfi_manifest_content_recovery_completion`'s own retire-phase hard-stop). (Todo 3 of this same doc is already
  drafted, still-draft, in batch6 — not re-drafted.)
- **`tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s DP-FETCH-009 finding** —
  `deployment-service`'s `_read_attempted_failed_cells` has no date-recency window, so stale `attempted_failed` rows
  alone keep `DP_RUN_MOSTLY_EMPTY` paging regardless of current health. 3 named remediation options (purge/reclassify,
  add a recency-window exclusion, or both) with no stated preference — a genuine implementation-approach judgment call,
  not purely bounded; needs a pick before it's a batch todo.

## Deferred — self-dispatched already (don't duplicate; flagging a staleness/visibility gap instead)

- **`mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`'s item 2** (ETF/OPTION SchemaContract registration
  gap) was blocked on a P2 mechanism-(a) fix that shipped 2026-08-03 — the blocking annotation was never refreshed and
  now reads stale. This doc is `assigned_vm: planning` + `status: open` (self-dispatched, `sequential: true`) — no new
  batch todo needed, but worth flagging that its own item 1 (`[OPERATOR]` P2, still genuinely unresolved) may be
  sequence-blocking item 2 from ever reaching the backlog even though item 2's own precondition cleared.
- **`strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`'s checkbox 1** — the operator already ruled "wire up"
  (BLK-75060009, 2026-08-05), but the checkbox itself is still tagged `[OPERATOR]` and the engineering action (real
  callers for `strategy_orders`/`strategy_positions`/`strategy_pnl` + deployment config + the `PATH_REGISTRY` divergence
  fix) is unshipped (live-verified: zero callers in the strategy-service tree as of the doc's own 2026-08-06 read). This
  doc is self-dispatched (`assigned_vm: planning`, `status: open`) and multi-AG (`[cefi, defi, tradfi]`) — per the
  primary-owner rule this is not tradfi's doc to retag, but the stale `[OPERATOR]` tag on an already-decided item is
  worth flagging to whichever tranche owns it (or the operator directly), since a stale tag can silently block
  self-dispatch the same way it did for the item above.
- **`tradfi_backfill_oom_remediation_2026_06_24.md`'s P3 MDPS-candle-writer spillover check** — doc is actively
  self-worked (5+ dated sessions, most recently today); redundant to duplicate into a batch todo.
- **`features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`** — item 1 (genuine delta_one:TRADFI
  force+skip proof) is gated on TRADFI MDPS actually producing captured `processed_candles` rows, which is an upstream
  data-availability blocker no batch todo can force; item 2 (a malformed "ticks" instrument_id, surfaced by the
  pre-flight scanner) is explicitly self-described as "low-priority" and not yet its own tracked issue — small enough to
  fold into a future batch's housekeeping rather than its own slot here.

## Deferred — already drafted elsewhere, pending that plan's promotion (not re-drafted here)

- **`tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`**'s residual 983 FX `SPOT_PAIR` rows carrying the
  literal `"ticks"` instrument_id (leaked from the bundle filename) are already scoped as a real, Done-when-bearing
  `[DATA] P2` todo inside `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (lines 189-204) — that whole plan is
  itself `status: draft`, same as batch6/7. Drafting a competing todo here would duplicate existing, more-detailed
  scoping; the fix is promoting `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`, not a new batch7 entry.
- **`tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md`** is not an issue doc but a complete, already
  well-scoped standalone draft PLAN (7 todos: JSON-access-pattern fix, `MacroResultRecord` schema extension, the actual
  ForexFactory scraper build, backfill launcher + cron, fixture-based tests, an honest-coverage check). It needs
  operator review/promotion (`status: draft` → `active`), not folding into a batch todo — recorded here for the
  operator's attention alongside batch6/7.

## Flagged, not batched — cross-tranche ownership

Carried forward from batch6: **`mtds_is_full_adapter_smoketest_findings_2026_07_07.md`**'s 4 TradFi-specific bugs never
promoted to checkboxes (`parent_epic: instruments_master`, 5-way `asset_group`) — still unresolved as of this pass; the
one real active-adjacent todo naming it (`tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` line 149) is itself
in a draft, undispatched plan.

Newly found this pass (all multi-AG or epic-owned-elsewhere; per the primary-owner rule a WRITE to these belongs to
whichever tranche actually owns the content, not tradfi reaching in — each is flagged so it isn't lost):

- **`ag_closeout_audit_rollout_2026_07_25.md`** — sole open item is the corpus-wide operator-gated mass
  status/`assigned_vm` flip finalization; owning tranche resolves to `cefi` (parent_epic
  `agent_operating_framework_master` doesn't map to any of this doc's 5 listed AGs, falls back to `tranches[0]`).
  Tradfi's own historical slice here (batch1/2/4 mass-flip) is already done.
- **`adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`** — sole open item is a
  full-trace-vs-spot-check cadence judgment call over ~55 untraced findings; `instruments_master` epic, 5-way AG.
- **`canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`** — both remaining items (a malformed-checkbox
  bare-wire-symbol id defect, a quarantine/honest-absence disposition gated on a separate design doc) are CeFi-venue
  content, not tradfi's, despite living in a `[cefi, tradfi, meta]`-tagged doc.
- **`estate_orphan_assessment_2026_07_21.md`**'s todo 6 — CONTESTED between cefi (KEEP-NA) and defi (RECLASSIFY)
  na-eligibility-audit tranches; genuinely needs an operator ruling on which side wins, not a third opinion from tradfi.
- **`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`** — all 8 remaining items are
  design/operator-gated content (mockup fixes, a CeFi parquet-resharding design, a PREDICTION market_metadata axis move,
  a historical-manifest backfill needing its own scoping); `[cefi, defi, tradfi, prediction]`, `instruments_master`
  epic.
- **`instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md`** — remaining items
  are prediction-owned (todo 8, a `market=` shape operator ruling) and sports-owned (historical-backlog migration gated
  on a CI/capacity-crisis condition); tradfi's own slice (2 disjoint pairs) is already fully resolved.
- **`instruments_docs_audit_outstanding_items_2026_07_08.md`**'s §H — 4 items + a never-run doc-cleanup pass are
  genuinely 100% tradfi content, but the doc's own `asset_group` is 5-way and `parent_epic: instruments_master`; per the
  same precedent that kept tradfi from drafting into `mtds_is_full_adapter_smoketest_findings` (a structurally identical
  case last batch), flagged here rather than drafted.
- **`mdps_features_deadcode_consolidation_2026_07_20.md`** — 4 remaining items (2 broken/non-runnable VM launchers, 1
  unregistered zombie-watchdog blind spot, 1 dual-entrypoint cleanup) all gate on the SAME unresolved operator
  keep/delete/design-adjudication ask; `[cefi, defi, tradfi, sports, prediction]`.
- **`ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`** — both remaining items
  (verify `ml_service`'s CLI surface vs. its launcher; determine launcher-consolidation overlap) explicitly fold into
  `mdps_features_deadcode_consolidation_2026_07_20.md`'s own still-unresolved operator decision above.
- **`uac_data_type_validity_combinator_fragmentation_2026_07_07.md`** — operator decision needed on 9 DeFi (protocol,
  data_type) pairs (wire real capture vs. roll back aspirational genesis dates) + 2 unexecuted rollback candidates + an
  unscoped `deployment-api` retirement follow-up; `[cefi, defi, tradfi]`, `instruments_master` epic.
- **`uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`** — wiring live catalogue providers for
  DEFI/TRADFI/PREDICTION into `deployment-api/venue_resolution.py` is real, bounded, genuinely new engineering work, but
  `parent_epic: cefi_master` — cefi's own audit is the right vehicle to draft it, not tradfi.
- **`candle_feature_canonical_path_divergence_2026_07_20.md`**'s todos 9 + 13 (corpus-wide `pipeline_mode`-less
  split-brain count + a `ProvisionalTargetIndex` bucket-key precision fix) — cross-AG scope, not tradfi-primary (todo 3
  of this same doc, the TradFi-specific ~7.1M-object quarantine, IS already fully covered by an active
  `tradfi_manifest_content_recovery_completion_2026_07_24.md` todo — not orphaned).

## Reconciliation ledger (orphan count accounting)

36 orphaned docs total this pass = 5 source docs drafted into the 4 todos above (2 combined into todo 2) + 4
too-large-or-risky + 7 operator-gated (4 unchanged-carried + 3 newly-found) + 4 self-dispatched-already + 2
already-drafted-elsewhere + 12 flagged cross-tranche-owned + 2 accounted for indirectly (`tradfi_sp500_ml_and_arb...`
counted under too-large; `mtds_is_full_adapter_smoketest_findings` counted under flagged, both carried from batch6).
Every orphaned doc found this pass has a durable disposition recorded either as a todo above or in one of the Deferred/
Flagged sections — none is left only in this plan's own drafting-session reasoning.

## File-collision matrix (verified before finalizing — same-priority todos run concurrently by default)

| Todo | Primary file(s) touched                                                                                                       |
| ---- | ----------------------------------------------------------------------------------------------------------------------------- |
| 1    | `market-tick-data-service` — new dedicated reconciliation script (name TBD by the worker; distinct from todo 2's file)        |
| 2    | `market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_canonical_2026_07.py` (single file, both sub-fixes) |
| 3    | `instruments-service/scripts/cleanup_legacy_twins.py` (read-only investigation, no code edit expected)                        |
| 4    | `features-service` delta_one `orchestrator.py`                                                                                |

No file appears twice — all 4 todos touch distinct repos/files.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_satellite_ao_dispatch_batch7_2026_08_06_finalize.md` (`depends_on` on this plan plus `gate_on_depends: true`),
mirroring the batch1-6 finalize pattern.

## Progress Log

- **context-scout 2026-08-07**: populated context_scope (6 entries) — 3 codex docs (manifest/data-status, delete-safety,
  and the batch's own conflict-check protocol) plus the 3 exact source files the File-collision matrix names for todos
  2-4 (`migrate_tradfi_canonical_2026_07.py`, `cleanup_legacy_twins.py`, delta_one `orchestrator.py`); todo 1's target
  is a not-yet-built script with no existing file to cite. Dropped `tradfi-databento-sourcing-ssot.md` from the doc's
  own "Codex SSOTs" list to stay within the 6-entry cap — this batch's 4 todos are post-capture manifest/migration
  fixes, not databento vendor-sourcing content.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **slot-15 worker 2026-08-09** (task `tradfi_satellite_ao_dispatch_batch7-001`): shipped todo 1
  (`market-tick-data-service@63cff354`). Full per-root census (live manifest, immediately pre-apply,
  `venue=CME`/`instrument_type in {futures_chain,options_chain}`/`data_type in {ohlcv_1m,ohlcv_1s}`/`capture_status= captured`/blank
  `instrument_id`/non-blank `underlying`/`instrument_count>0`), 3,267 rows / 41 roots: `SP500` ohlcv_1m=797 ohlcv_1s=797
  · `BTC` ohlcv_1m=221 ohlcv_1s=145 · `ETH` ohlcv_1m=206 ohlcv_1s=145 · `COPPER` ohlcv_1m=145 ohlcv_1s=146 · `CRUDE`
  ohlcv_1m=146 ohlcv_1s=145 · `GOLD` ohlcv_1m=145 ohlcv_1s=146 · `MET` ohlcv_1m=34 · `MBT` ohlcv_1m=24 · then 27 roots
  at 1 row each (AUD/CORN/EC6E/ECCL/ECGC/ECNQ/ECRTY/EUR/
  GASOLINE/HEATINGOIL/JPY/MICRO-SP500/MXN/NATGAS/SILVER/SOYBEAN/SOYMEAL/SOYOIL/TBOND×2/TNOTE10Y×2/TNOTE2Y/TNOTE5Y/ WHEAT
  — mostly options_chain, ohlcv_1m and ohlcv_1s each). This is dramatically smaller than the todo's own
  28,307+111-for-ES-alone figure (from the issue doc's 2026-07-30 investigation) — re-verified this is NOT a methodology
  gap: the 10 days between that snapshot and this run saw substantial CME backfill/recapture activity with the
  already-fixed writer, naturally superseding most of the original blank-id population with fresh correctly-tagged twins
  for the same (date, underlying, data_type) keys (confirmed directly: 2,492 of 3,267 restamped candidates deduped
  against exactly such a pre-existing twin). Applied 100% resolved / 0 quarantined; independent fresh post-apply census
  (separate `read_availability_index_safe` call, not just the script's own self-report) confirms 0 remaining in-scope
  blank rows, 0 duplicate keys. Memory note: the live manifest is ~7.02M rows/~50 cols — an early unbounded local run
  (before the fix below) climbed to ~9.5GB RSS and was killed on this shared host; root cause was a defensive
  `df.copy()` plus several redundant full-column `.map()` re-computations in my own first draft, not the underlying data
  volume — fixed by narrowing to cheap categorical masks before any per-row string coercion and mutating the manifest
  DataFrame in place; both the dry-run and the real `--apply` then completed cleanly under `run-bounded-analysis.sh`
  (10G/14G caps, peak measured ~9.4GB). **Side-finding, NOT part of this todo**: the same live query surfaced two
  adjacent blank-`instrument_id` populations in the identical (CME, ohlcv_1m/1s, captured) shape —
  `instrument_type=combo` (~301K rows, confirmed BY DESIGN id-less per `_tradfi_manifest_shard.py`'s own comment, not a
  bug) and `instrument_type=FUTURE` (~19.6K rows, singular/ canonical-cased, a DIFFERENT non-chain-bundle write path,
  actively growing — ~50K rows/day written across the broader unscoped population in the days immediately before this
  session). Filed as `issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` rather than fixed here (outside
  this todo's literal "CME futures_chain/options_chain shards" wording; different, not-yet-understood root cause).
- **slot-3 worker 2026-08-09** (task `tradfi_satellite_ao_dispatch_batch7-002`, IN PROGRESS — not yet flippable, both
  fixes committed locally but NOT YET PUSHED): both hardening fixes (`_rel()` quarantine-prefix guard +
  `_VENUE_REMAP`-equivalent validation) implemented in `migrate_tradfi_canonical_2026_07.py` with 33 tests (12 new), all
  passing — committed as `market-tick-data-service@ff6c2f4a`. A separate, unrelated pre-existing STEP 5.95 TID251
  ratchet regression (in `scripts/one_offs/verify_defi_glued_ids_2026_07_24.py`, a DeFi one-off — not part of this
  todo's scope) blocked Pass-1 QG on this repo; root-caused as a `noqa: TID251` comment landing on the wrong physical
  line of a multi-line/parenthesized `google.cloud import storage` — fixed by collapsing to one line
  (`market-tick-data-service@8c5fe244`, second attempt — see trap below). **Trap hit twice, worth flagging for anyone
  else who touches a `noqa: TID251`/`noqa: DTZ00x` comment near this repo's 120-char ruff line-length**: a single-line
  import + a sufficiently long noqa reason exceeds the line-length limit, so ruff's own formatter (which pre-commit runs
  automatically) silently re-wraps the import into multi-line parenthesized form — which moves the noqa comment off the
  diagnostic's anchor line and **reintroduces the exact ratchet violation the fix was meant to close**, with no error at
  commit time (ruff's formatter treats it as a normal reformat, not a lint failure). First attempt at fixing this file
  looked correct standalone (`ruff check` passed) but broke again the moment `git commit` ran pre-commit's auto-format
  hook. Fix: keep the noqa reason short enough that `import line + comment` stays under the line-length limit as a
  single physical line (verified via `ruff format --diff` showing zero diff, not just `ruff check` passing — the format
  check is the one that actually predicts what pre-commit will do to the line). **Status at time of this note**: a fresh
  Pass-1 `quality-gates.sh` re-run is in progress (background, `PYRIGHT_TIMEOUT=420` per the same host-contention
  mitigation used for todo 1's basedpyright timeouts) to re-validate against the new HEAD before quickmerge; both
  commits are ahead of `origin/live-defi-rollout` by 2, not yet pushed. Next worker/session: check `.qg_last_passed_sha`
  in market-tick-data-service against current HEAD — if it matches, proceed straight to
  `scripts/quickmerge.sh --agent --files 'scripts/one_offs/verify_defi_glued_ids_2026_07_24.py'` (ships both commits),
  verify `git rev-list --count origin/live-defi-rollout..HEAD == 0`, then flip todo 2 above with both SHAs (`ff6c2f4a` +
  `8c5fe244`) and call `/done` for `tradfi_satellite_ao_dispatch_batch7-002`.
- **slot-3 worker 2026-08-09** (task `tradfi_satellite_ao_dispatch_batch7-002`, DONE): fresh Pass-1 `quality-gates.sh`
  re-run (`PYRIGHT_TIMEOUT=420`) went fully green against HEAD `8c5fe244` — STEP 5.95 (TID251 ratchet) explicitly passed
  this time, sentinel `.qg_last_passed_sha` written matching HEAD. Pass-2
  `scripts/quickmerge.sh --agent --files 'scripts/one_offs/verify_defi_glued_ids_2026_07_24.py'` shipped both commits;
  quickmerge amended the tip commit to add the missing `Quickmerge: agent` trailer (local `8c5fe244` → pushed
  `e72feb7c`, content unchanged — verified via `git show --stat HEAD`: 1 file, 1 insertion/3 deletions, matches the
  intended noqa-shortening diff exactly, despite quickmerge's own benign message-mismatch WARN which only flags the
  commit SUBJECT text, not tree content). Post-push: `git rev-list --count origin/live-defi-rollout..HEAD` = 0,
  `git status --porcelain` empty. Both fixes (quarantine-prefix `_rel()` guard + `_VENUE_REMAP`-equivalent venue
  validation, 33 tests) and the STEP 5.95 unblock are now on `origin/live-defi-rollout`.

## Codex SSOTs

`/codex/02-data/tradfi-databento-sourcing-ssot.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.
