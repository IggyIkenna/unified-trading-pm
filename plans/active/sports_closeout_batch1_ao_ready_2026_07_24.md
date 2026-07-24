---
doc_type: plan
title: Sports closeout batch 1 — AO-dispatch-ready extraction (independent, non-overlapping todos)
summary: >-
  First AO-dispatchable batch extracted from sports_consolidated_closeout_2026_07_19.md (the canonical umbrella plan,
  permanently assigned_vm=NA by operator ruling — too many todos + unmachined cross-todo dependencies to dispatch
  directly). 20 todos hand-picked for genuine independence: no unmet prerequisite among them, no two todos touch the
  same file, none blocked on operator/credential/live-VM-fleet state. Everything with a real dependency (the K1/K2
  casing-revert DATA migration, the EXCHANGE_ODDS/FIXED_ODDS fork's internally-ordered chain, anything gated on the
  league_id migration/CF-8 window/AWS IAM access, the cross_ag_prediction bleed's still-open consolidator TOCTOU bug)
  was deliberately left in the parent for a later, carefully-sequenced batch.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, canonical, honest-coverage, close-out, batch-1]
related:
  [/plans/active/sports_consolidated_closeout_2026_07_19.md, /plans/active/sports_consolidated_audit_2026_07_19.md]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 10.4
estimate_calibrated_ai_days: 8.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_consolidated_closeout_2026_07_19]
source: >-
  Extracted 2026-07-24 from sports_consolidated_closeout_2026_07_19.md per that plan's own frontmatter instruction
  ("extract the specific ready todo(s) into a NEW child plan... never by editing this field") and direct operator
  request. Every todo below is copied from that plan's live text (Tracks F/C/O/H/V/K/D/X), re-worded to cite symbols
  instead of line numbers and to state an explicit done-when per task_template.md §3.
assigned_role: data_engineering
drift_direction: advance-code
---

# Sports closeout batch 1 — AO-dispatch-ready extraction

> **Read `sports_consolidated_closeout_2026_07_19.md` first** — it is the canonical plan this batch is extracted from;
> every todo below traces back to a specific Track in that doc. This plan does not duplicate its evidence base, only the
> specific, verified-independent action items.

## Why these 20 and not others

`sports_consolidated_closeout_2026_07_19.md` has 88 open todos (17 P0) across many repos. Most were deliberately
EXCLUDED from this first batch because they are blocked on one of:

- **A real, unmet cross-todo dependency** — e.g. the venue-vocabulary re-stamp needs the parse-bug fix (todo 2 below) to
  land and hold first; Track H's registry-aware coverage denominator needs the league_id migration first; the
  EXCHANGE_ODDS/FIXED_ODDS fork is its own internally-ordered 9-step chain.
- **Operator/credential gating** — the AWS IAM sports-pipeline-dormancy investigation, the CF-8 maintenance window
  (`BLK-d9137d48`), the EXCHANGE_ODDS/FIXED_ODDS venue-class mapping confirmation.
- **Live VM-fleet or scheduler sequencing** that genuinely needs a human watching (Sports IS L6 index regression's
  strict 3-step order; the 2 long-running SPOT VMs already in flight).
- **The cross_ag_prediction bleed** — `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` ROUND
  6 (2026-07-24) pinned a TOCTOU bug in the shared manifest consolidator as the actual mechanism; nothing that touches
  that surface is safe to dispatch until the consolidator fix (that issue doc's todo 12) ships.
- **File overlap with another todo already in this batch** — e.g. the T0/T1 dependency-gate wiring and the
  entity=fixtures consumer sweep both touch `process_preflight.py`/`sports_fixtures_daily_repoll.py`, which todo 1 below
  (C1) also touches; the catalogue player-grain upgrade touches `build_instrument_catalogue.py`, which todo 2 below also
  touches. Both were left for batch 2 rather than forced into a `sequential: true` chain that would have serialised this
  whole batch's real parallelism.

**No two todos below touch the same file** (verified against every file/symbol cited in the parent plan's Track F/C/O/
H/V/K/D/X sections) — this batch is intentionally left ungated (no `sequential: true`) so independent workers can claim
todos concurrently.

## Todos

- [ ] [CODE] P0. Migrate the fixtures manifest atom from the hardcoded `"FIXTURES"` literal to
      `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` across every writer/reader call site so the manifest atom matches the
      writer atom — `instruments-service`'s `sports_reference_fixtures.py`, `process_write.py`, `writers.py`,
      `catalogue.py`, `process_completeness.py`, `process_preflight.py`, `process_zero_records.py`,
      `sports_fixtures_daily_repoll.py`, plus `unified-api-contracts`'s `_honest_coverage_logic.py`'s
      `SCHEDULE_DEFINING_DATA_TYPES` constant (a 9th call site found 2026-07-23, easy to miss since it's a different
      repo). **Done when**: a corpus-wide manifest census for sports returns zero rows with `data_type="FIXTURES"` (only
      `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` remain) and `SCHEDULE_DEFINING_DATA_TYPES` matches the new atom.
- [x] [CODE] P0. ✅ Fix 3 asset_group-blind positional-parse bugs in `market-data-processing-service`'s
      `canonical_writer_shaping.py` (`_type_token_from_canonical_id`, `_infer_chain`) and its call sites
      (`live_workers.py`, `live_workers_chain.py`, `batch_workers.py`, `candle_write_mixin.py`), plus
      `instruments-service`'s `build_instrument_catalogue.py`'s `_instrument_type_from_id`: for sports, `venue` must
      resolve from the bookmaker token (not the sport token it wrongly reads today), `instrument_type` must resolve the
      market token through `ODDS_API_MARKET_TO_CANONICAL` lower-cased (not the bookmaker token), and `chain` must never
      be written for sports (always null — sports has no `chain` column in `SPORTS_ODDS_TRADES`'s SchemaContract). Gate
      every fix on `asset_group` so CeFi/DeFi/TradFi/prediction parsing is untouched. Do NOT touch the intentional
      `mdps_odds_horizon_bucket` `venue=ODDS_API` aggregate (a different, deliberate identity). **Done when**: the
      deployment-ui sports Distinct Values panel reads 0 non-canonical `venue`/`instrument_type` values from fresh
      writes, and `chain` is null on every new sports row. — **market-data-processing-service@51502c3**,
      **instruments-service@f46e553e**. Added asset_group-gated `_venue_token_from_canonical_id` /
      `_resolve_empty_failed_shard_tuple` helpers alongside the fixed `_type_token_from_canonical_id`/`_infer_chain`;
      threaded `asset_group` through every listed call site + `canonical_writer.py`/`canonical_writer_streaming.py`'s
      production write paths; every non-sports asset_group verified byte-identical (parameter defaults preserve old
      behaviour). Evidence: both repos' `quality-gates.sh` green (MDPS 87s, IS 152s); 6 new unit-test cases exercising
      the exact sports id shape (`SPORT:BOOKMAKER:MARKET:LEAGUE:SEASON:HOME-AWAY::SELECTION`) across
      `_type_token_from_canonical_id`/`_venue_token_from_canonical_id`/`_infer_instrument_type`/`_infer_chain`/
      `_resolve_empty_failed_shard_tuple` (MDPS) + `_instrument_type_from_id` (IS), all passing; MDPS's 103/103 full
      unit suite for the touched test files green (no regressions). **Not independently verified**: the literal
      done-when (deployment-ui Distinct Values panel on FRESH LIVE writes) — that needs an actual live/backfill sports
      write to land after this ships; the instruments-service `_instrument_type_from_id` gate is confirmed
      defensive/inert today (no reachable sports call path through `build_catalogue_dataframe`, per code-path trace) so
      its half of the done-when doesn't apply until that path exists. Surfaced + filed (NOT caused by this fix — see the
      doc for the pre/post-diff proof): `mdps_canonical_writer_adapter_contract_baseline_regression_2026_07_24.md`
      (pre-existing STEP 5.70 warn-only baseline drift on `canonical_writer.py`, 17<18).
- [ ] [DATA] P0. Run `reprocess_sports_odds.py --force` for 2025-12-18, 2025-12-24, and 2025-12-31 through the real
      script (not a hand-edit) so the manifest's coarse row flips off the stale `captured` state (a legacy-path capture
      leak) to the honest verdict: `attempted_failed` for 12-18/12-31, `empty_confirmed` for 12-24. **Done when**: a
      manifest read for those 3 dates on the sports odds shard shows the stated verdicts, not `captured`.
- [ ] [DIAG] P1. Investigate why `sfi_progressive_features` is corpus-empty (1 manifest row) in `instruments-service`'s
      `sfi.py`/`process_enrichment.py` despite a documented 2020-to-present capture window, then run whatever backfill
      the root cause implies. **Done when**: either a written root-cause conclusion + the backfill has run and the
      manifest shows non-trivial row counts, or (if the cause is a genuine external blocker) the finding is filed as its
      own issue doc with the blocker named.
- [x] [DATA] P1. ✅ Purge/backup-delete the leaked legacy-path (no `pipeline_mode=` prefix) T-0 shards for
      2025-12-18/24/31 (100% post-kickoff captures) via `unified_trading_library`'s `gcs_copy_object`/
      `gcs_delete_object` (never subprocess `gsutil`) — snapshot first (GCS soft-delete gives a 7-day recovery window,
      the safety net for this NOT being `[OPERATOR]`-tagged). First confirm no live reader consumes the unprefixed path
      — if one does, fix that reader before deleting, don't delete out from under a live consumer. **Done when**: a
      listing for those 27 known object paths returns none, and the confirmed-no-reader check is documented. — **DONE
      2026-07-24.** Bounded listing (3 known dates, not a corpus walk) under
      `gs://market-data-tick-sports-prd-central-element-323112/processed/by_date/day={date}/data_type=odds_horizon_bucket/`
      found **28** legacy `timeframe=T-0/bucketed.parquet` shards (9 for 12-18, 10 for 12-24, 9 for 12-31), not 27 as
      estimated — measured directly, every shard sampled at 100% `bm_minutes_to_kickoff < 0` (post-kickoff), matching
      the finding. **Reader check**: `features-service`'s `read_bucketed_odds()`
      (`features_service/sports/data/gcs_reader.py:568`) DOES fall back to this exact legacy prefix when no canonical
      `pipeline_mode=batch_mdps_odds_horizon_bucket` shard exists — confirmed 0 canonical shards for all 3 dates before
      deletion, so this reader was live-consuming the leaked T-0 data (feeding contaminated post-kickoff rows into
      `odds_features` at the T-0 model horizon). No reader FIX was needed: the reader lists+concatenates every
      `bucketed.parquet` under whichever prefix wins and already handles a missing horizon as honest absence
      (`_find_best_snapshot` → `None` → skipped) — removing only the T-0 shard leaves the other, uncontaminated
      per-(league,horizon) shards for those dates intact and correctly still reachable via the same fallback. Snapshot:
      confirmed `soft_delete_policy.retentionDurationSeconds=604800` (7-day) live on the bucket before deleting (the
      task's own stated safety net); recorded every object's `(name, generation, size)` pre-delete for the 7-day
      recovery window. Deleted all 28 via `unified_trading_library.cloud_interface.gcs_delete_object` (0 failures).
      Post-delete listing for `day=2025-12-18/24/31` under `data_type=odds_horizon_bucket/` returns **0 objects** —
      confirms these 3 dates held ONLY the contaminated T-0 shards (consistent with the B2 finding that every other
      horizon returned `ADAPTER_RETURNED_EMPTY_OUTPUT` on those dates), so the date now correctly reads as honest
      absence end-to-end, not a partial purge. No code change required (pure data op); manifest coarse-row correction
      for these 3 dates is the separate P0 todo above (`reprocess_sports_odds.py --force`), not duplicated here.
- [x] ✅ [DIAG] P1. Root-cause why `reason`/`error_code`/`empty_reason`/`classified_error` read back blank for the
      sports odds manifest (a schema gap vs. a silent-empty write bug) — this unblocks two other diagnoses (the
      `attempted_failed` triplet root-cause and the `empty_confirmed` emitter identification) that stay out of this
      batch until this one lands. **Done when**: a written conclusion states which mechanism it is, with the specific
      write-path code reference. — unified-trading-pm@(this commit)

      **Conclusion: SCHEMA GAP, not a silent-empty write bug.** None of `reason`/`error_code`/`empty_reason`/
                      `classified_error` is a manifest COLUMN — confirmed against the live production schema itself: a targeted
                      single-file read of `gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`
                      (563,384 rows, 2026-07-24) lists 39 real columns and the only reason-bearing one is `error_reason`; none of the
                      other 4 names appear. The manifest's `AvailabilityRecord` schema
                      (`unified-trading-library/unified_trading_library/manifest_writer/_rows.py:284-346`) declares exactly one field
                      for this info — `error_reason: str = ""` — and every `record_*` write path
                      (`unified-trading-library/unified_trading_library/manifest_writer/_writer_record.py`) funnels into it via
                      `_record_status(..., error_reason=...)`. The 4 task-title names are each a DIFFERENT adjacent symbol that a
                      reader could mistake for a manifest column: `reason` is the kwarg name on `record_empty()`/`record_zero_rows()`
                      (`_writer_record.py:99,420,524` — its VALUE is what lands in `error_reason`, not a stored column name);
                      `error_code` is the attribute on `VenueErrorClassification`, the object `classify_venue_error()` returns
                      (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/__init__.py:47`); `empty_reason` is a
                      dict KEY in deployment-api's UI-facing `compute_empty_reason_counts()` breakdown
                      (`deployment-api/deployment_api/services/data_status/coverage_metrics.py:255`, which itself reads
                      `df["error_reason"]` correctly — line 283); `classified_error` is a local Python variable inside
                      `market-tick-data-service/market_tick_data_service/engine/orchestrator/sentinels.py:221-227`
                      (`_emit_sports_tier2_sentinels`) holding the string before it's passed as `record_failed(error=
                      sports_classified_error)`. Every sanctioned sports call site reviewed (`sentinels.py`, `sports_reference_core.py`,
                      `process_zero_records.py`, `process_preflight.py`, `footystats.py`, `manifest_recorder.py`) passes an explicit
                      `reason=`/`error=` argument; `record_failed()` additionally hard-raises `ValueError` on an empty `error` string
                      (`_writer_record.py:481-482`). Live-data confirmation: today's 21,920 `empty_confirmed` sports rows are 0.00%
                      blank on `error_reason` (100% carry `SOURCE_RETURNED_ZERO`); the earlier `attempted_failed` BETFAIR/MATCHBOOK/
                      PINNACLE triplet was independently confirmed non-blank (`VENUE_FETCH_FAILED` / an `EmptyFromLiveInstrumentError`
                      guard message) by `issues/sports_trades_attempted_failed_2026_07_23.md`'s own live query before that population
                      was wiped same-day (`market-tick-data-service@e9d9dec0`). **Unblocks**: both downstream diagnoses should query the
                      real `error_reason` column (grouped by `source`/`pipeline_mode`/`venue`) — the data needed for both is present and
                      populated, not missing.

- [x] ✅ [CODE] P1. Fix `AG_STALENESS_BUDGET_SEC["sports"]` in `unified-trading-library`'s
      `manifest_writer/_staleness_budget.py` to **≥1800s**, merging two previously-conflicting recommendations (sweep
      §J's rejected 180-240s figure and the issue doc's own already-correct 1800s target) into the single correct value
      — matches the observed ~11-minute blob-age refresh cadence. **Done when**: the constant reads ≥1800 and a
      staleness-budget unit test (existing or new) asserts it. — unified-trading-library@fd87daa1: added
      `"sports": 1800` to `AG_STALENESS_BUDGET_SEC`, updated the module docstring with the sports cadence note, and
      added `tests/unit/test_manifest_writer_staleness_budget.py` (4 tests asserting the value + resolver behavior). QG
      green (287s), quickmerge shipped to live-defi-rollout.
- [ ] [DATA] P1. Run the round-derivation residual backfill for the reachable in-window (cup-vs-league resolved,
      registry-member, post-2019) blank-`round` pairs, using the round-derivation mechanism the 2026-07-18 sweep already
      confirmed terminal. **Done when**: a corpus-wide census shows 0 remaining blank-round rows in the in-window,
      registry-member population.
- [x] ✅ [CODE] P1. Promote the existing sports golden window (2025-09-01…11-30) into a shared "right days" SSOT module
      that both the sports smoke tests (`SPORTS_SMOKE_DATES`) and backfill launchers import, instead of each hardcoding
      its own copy. **Done when**: both consumers import from the new module and no duplicate date literal remains in
      either. — unified-api-contracts@a02a71e0 + instruments-service@a80b3ad2 + features-service@00547173

      New SSOT: `unified_api_contracts/canonical/domain/sports/right_days.py`
          (`SPORTS_SMOKE_DATES` + `SPORTS_GOLDEN_WINDOW_START`/`SPORTS_GOLDEN_WINDOW_END`, re-exported at the
          `canonical.domain.sports` package level per the existing `X as X` convention). Two real, literal-constant
          duplicates found in a full-workspace search (both other "golden window" hits were docstrings/comments, not code
          constants): `features-service`'s `scripts/sports/smoke_matrix.py` (`SPORTS_SMOKE_DATES` dict — busy/thin/
          known_buggy_* dates) now imports from the UAC module instead of defining its own copy; `instruments-service`'s
          `scripts/verify_golden_window_parquet_presence_2026_07_14.py` (`_WINDOW_START`/`_WINDOW_END` string literals) now
          imports `SPORTS_GOLDEN_WINDOW_START`/`SPORTS_GOLDEN_WINDOW_END` instead of hardcoding. Verified both imports
          resolve (`unified_api_contracts.canonical.domain.sports.right_days`, both repos already carry UAC as a `uv`
          path dependency) and both files still parse; `quality-gates.sh` green on all 3 repos.

- [ ] [CODE] P1. Build a sports pipeline-check for the instruments-service → market-tick-data-service →
      market-data-processing-service → features-service middle leg that asserts CONTENT (not just presence) at each
      stage — no such check exists today for sports, unlike CeFi/TradFi's `/data-pipeline-check-mtds`/
      `/data-pipeline-check-mdps`. **Done when**: the check fails on the pinned busy smoke date (2025-12-20) if any
      leg's output is empty or shape-wrong, verified by deliberately breaking one leg and confirming the check catches
      it.
- [ ] [DIAG] P2. Wire `is_promotion_relegation` (currently hardcoded `False` in `features-service`'s
      `season_context.py`) from the standings relegation-zone classification `_compute_league_batch` already computes,
      or formally retire the field + its `points_at_stake` multiplier if it's genuinely unneeded. **Done when**: either
      the field reflects real relegation-zone data on a sample date, or it's removed with its multiplier and no dangling
      reference remains.
- [ ] [DIAG] P2. Determine whether `clv_*`/`odds_movement_*` being all-null in `odds_features` is honest-absence (if
      they source from MDPS's dead `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` products, never scheduled) or
      a genuine gap — check the actual sourcing, don't assume. **Done when**: a written conclusion states which, with
      sample dates + result counts cited.
- [ ] [DATA] P2. Purge the 4 dead dimension groups (players/coaches/referees/rounds, 4,216 rows each) still inflating
      the features manifest — already operator-ruled per `plan_reconciliation_operator_decisions_2026_07_11.md` §A2, not
      a fresh decision; snapshot first (manifest-row snapshot, reversible). **Done when**: a manifest census for these 4
      dimension groups returns 0 rows.
- [ ] [DATA] P2. Purge the 1,337 dead `odds_horizon_bucket_{15m,1h,4h,1d}` manifest rows (a retired, timeframe-baked
      cohort) — snapshot first (manifest-row snapshot, reversible). **Done when**: a manifest census for that data_type
      prefix returns 0 rows.
- [ ] [DIAG] P2. Confirm sports genuinely never emits `expected_unattempted` in the odds manifest (0 of ~1.97M rows) by
      design, or fix the miscoercion into `empty_confirmed` if it's a bug. **Done when**: a written conclusion states
      which, with the manifest query used to confirm it.
- [ ] [DIAG] P2. Grep `features-service` and `strategy-service` for any real consumer of MDPS's
      `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` derived products before their fate is decided (operator
      ruling: wire up for real if something downstream needs them, do NOT retire blind). **Done when**: a written list
      of consumers found (or confirmed empty) is produced.
- [ ] [DOC] P2. Verify `sports-data-source-coverage-matrix.md`'s body isn't stale-under-banner (check every claim
      against current live source, the same failure mode already found + fixed in 6 sibling sports codex docs), and fix
      the 5 broken `related:` paths in `sports_master.md`. **Done when**: the doc's body matches its banner and every
      `related:` path in `sports_master.md` resolves to a real file.
- [ ] [CLEANUP] P3. Drop the frozen 2018-2020 `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` GCS scaffolding
      (dead cohort, no live writer), correct `SPORTS_INSTRUMENTS.md`'s stale "lineups player-id strip" claim (verified
      false), and add a junk-symbol guard rejecting non-ASCII characters in fixture names. **Done when**: the
      scaffolding is gone (snapshot first), the doc claim is corrected, and the guard rejects a non-ASCII test fixture
      name.
- [ ] [DOC] P3. Document the pre-2019 (2013-2018) api-football exclusion as an intentional, operator-decided scope
      boundary (already ruled — no fresh spend) in the audit's gap table, so the remaining-blanks arithmetic reads clean
      without an unexplained gap. **Done when**: the audit doc states the exclusion explicitly with the ruling citation.
- [ ] [DOC] P3. File an issue doc for the QG structural finding: at least two `quality-gates.sh` steps
      (`check_backfill_vm_disk_provisioning.py` in `deployment-service`, and the ruff LINT step) resolve target paths
      through the canonical MAIN clone rather than respecting `cwd`/a worktree's own tree, so no worktree-based
      isolation reliably gets a green QG sentinel while any other agent has dirty/untracked lint/disk-provisioning
      issues in the shared MAIN clone. File under `plans/active/issues/` with `asset_group: [meta]` (workspace-infra,
      not sports-specific). **Done when**: the issue doc exists with the reproduction steps already known (moving a file
      out of MAIN flips the check clean; a lint failure can reference another agent's untracked MAIN file).
