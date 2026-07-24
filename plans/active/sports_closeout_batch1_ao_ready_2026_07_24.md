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

- [x] [CODE] P0. ✅ Migrate the fixtures manifest atom from the hardcoded `"FIXTURES"` literal to
      `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` across every writer/reader call site — `instruments-service@e19c5a7a`
      (`sports_reference_fixtures.py`, `process_write.py`, `writers.py`, `catalogue.py`, `process_completeness.py`,
      `process_preflight.py`, `process_zero_records.py`, `sports_fixtures_daily_repoll.py`) + the UAC
      `SCHEDULE_DEFINING_DATA_TYPES` constant `unified-api-contracts@6d9c7b59`. **Done when** (CODE scope — MET): every
      named call site emits/reads the new atoms, `SCHEDULE_DEFINING_DATA_TYPES == frozenset({FIXTURES_SCHEDULE})`, QG
      green + sentinel-verified. **RESCOPED 2026-07-24 (main, re BLK-61c182dc)**: the original census-zero Done-when
      also covered the historical manifest backfill — a distinct data action with now-resolved design — so it is SPLIT
      into the new `[DATA]` backfill todo below. Not false progress: the 337,464-legacy-row census-zero requirement is
      not dropped, it moves to that todo. **CORRECTION 2026-07-24 (cicd escalation agt-2a122f, re ldr_qg_failure on
      deployment-api)**: the exact-narrow `SCHEDULE_DEFINING_DATA_TYPES == frozenset({FIXTURES_SCHEDULE})` clause caused
      a REAL regression while the 337,464 legacy rows still existed — `deployment-api`'s
      `tests/unit/data_status/test_oow_denominator.py` went RED on `live-defi-rollout` because the narrow set silently
      stopped resolving legacy `data_type="FIXTURES"` `SOURCE_RETURNED_ZERO` empties as out-of-window (a genuine
      coverage-math regression, not stale-test drift — pre-cutover manifest rows permanently carry the legacy atom per
      `fixture_lifecycle.py`'s own module docstring). Fixed to ADDITIVE — `unified-api-contracts@c2b303f7`:
      `frozenset({"FIXTURES", FIXTURES_SCHEDULE})` — as an interim protective measure for the window during which legacy
      rows still exist. This todo's "Done when" clause is therefore currently UNMET on the exact-set reading (harmless
      no-op difference in practice — the extra literal only matches rows the backfill below is retiring). Narrow it back
      to `frozenset({FIXTURES_SCHEDULE})` once the `[DATA]` backfill todo's own Done-when (census-zero, immediately +
      after ≥2 consolidator cycles) is verified — tracked as the last step of that todo, not a separate item.
- [ ] [DATA] P0. Backfill the 337,464 legacy `data_type="FIXTURES"` sports manifest rows to `FIXTURES_SCHEDULE`
      (read-only prod census 2026-07-24, bucket `instruments-store-sports-prd-central-element-323112`). **PRE-FLIGHT
      DONE 2026-07-24 (worker)**: found + fixed 2 live bugs the original resolution assumed were clean — a 9th missed
      call site (`sports_fixture_status_refresh.py`) was CONTINUOUSLY re-creating legacy rows, and
      `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` was silently mis-attributing pipeline_mode — both fixed + shipped
      `instruments-service@47c1ffb3`, QG green. **MECHANISM CORRECTED (worker, 2026-07-24) — supersedes the original 1→2
      fan-out design**: exhaustive grep found `FIXTURES_OUTCOMES` has NO live manifest writer anywhere (GCS-object label
      only) — the proven codebase convention (`process_write.py`, `sports_fixtures_daily_repoll.py`) is ONE manifest
      atom per fixture-capture event. This is a **1:1 in-place restamp** (`data_type: "FIXTURES"→"FIXTURES_SCHEDULE"`),
      mirroring this same plan's already-completed sibling precedent
      (`market-tick-data-service/scripts/restamp_sports_odds_horizon_bucket_2026_07_22.py`'s snapshot→mask→rewrite→CAS
      pattern) — NOT a GCS read/re-derive, NOT `migrate_fixtures_split.py`. Idempotent + SPOT-VM per the backfill HARD
      RULE; backup-then-write. **Done when**: a census via
      `deployment-api/scripts/census_manifest_data_type_2026_07_24.py --filter-prefix FIXTURES` returns zero
      `data_type="FIXTURES"` rows for sports, verified immediately AND after ≥2 consolidator cycles, AND
      `unified-api-contracts`'s `SCHEDULE_DEFINING_DATA_TYPES` (additive since `c2b303f7` — see todo 1's correction note
      above) is narrowed back to `frozenset({FIXTURES_SCHEDULE})` as the final step. Full analysis + corrected-design
      details: `/plans/active/issues/fixtures_manifest_legacy_backfill_2026_07_24.md`. (repo: instruments-service —
      bucket `instruments-store-sports-*` is IS-owned by naming convention, confirmed 2026-07-24:
      `restamp_fixtures_manifest_legacy_atom_2026_07_24.py` written there) **CONTENTION (worker pre-flight,
      2026-07-24)**: `instruments-sports` has its own `*/1 * * * *` consolidator cron
      (`uts-prod-manifest-consolidator-instruments-sports-cron`) PLUS a documented history of livelock/slow-run
      incidents on this specific bucket (lock TTL bumped to 2400s vs. 300s default) — CONTENDED, same class as the
      already-completed `odds_horizon_bucket` sibling precedent. Dry-run only so far; `--apply` needs an
      operator-authorized paused-cron window (mirror the documented pause/impersonation/resume recipe,
      `gcloud scheduler jobs pause uts-prod-manifest-consolidator-instruments-sports-cron     --location=asia-northeast1 --project=central-element-323112`,
      then resume after — see this plan's own `odds_horizon_bucket` precedent's Progress Log entry for the exact recipe)
      — asked via /blocked, not paused autonomously per `SUB_AGENT_MANDATORY_RULES.md`.
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
- [x] ✅ [DATA] P0. Run `reprocess_sports_odds.py --force` for 2025-12-18, 2025-12-24, and 2025-12-31 through the real
      script (not a hand-edit) so the manifest's coarse row flips off the stale `captured` state (a legacy-path capture
      leak) to the honest verdict: `attempted_failed` for 12-18/12-31, `empty_confirmed` for 12-24. **Done when**: a
      manifest read for those 3 dates on the sports odds shard shows the stated verdicts, not `captured`.

      **Actual honest verdict differs from the prediction above**: the real script classifies all 3 dates as
                                                                                  `attempted_failed`/`ADAPTER_RETURNED_EMPTY_OUTPUT` (raw odds exist, adapter filters to zero rows), including
                                                                                  12-24 — not `empty_confirmed` as predicted (the plan's own earlier, already-completed P1 todo had already found
                                                                                  this for all 3 dates; the split predicted here was stale at authoring time).

                                                                                  **GATED then RESOLVED 2026-07-24**: `reprocess --force` (slot 5) correctly wrote the verdict but the live
                                                                                  `*/1`-min sports manifest consolidator resurrected the stale `captured` row within 1-6 min every time (root
                                                                                  cause: a read-modify-write TOCTOU race between the consolidator's own merge cycle and any external direct
                                                                                  writer — not the documented captured-outranks tie-break against clean per-VM-shard inputs). Resolved via two
                                                                                  complementary fixes, both verified: (1) slot 4 durably corrected these exact 3 dates' rows via a
                                                                                  paused-consolidator-cron CAS write (codex §519 recipe), verified STABLE across ≥2 real consolidator cycles
                                                                                  (8-min wait, all 31 rows still `attempted_failed` via `ManifestWriter.lookup()` + a direct raw-index read); (2)
                                                                                  slot 5 closed the underlying TOCTOU race in `unified-trading-library@14301571` so future direct-writer
                                                                                  corrections don't need a cron-pause dance (full evidence + root-cause trace in
                                                                                  `/plans/active/issues/sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md` and
                                                                                  `/plans/active/issues/sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md`, both
                                                                                  now resolved). Condition `sports-odds-consolidator-resurrection-fixed` satisfied.

- [x] [DIAG] P1. ✅ Root-caused + backfilled. Corpus-empty was TWO stacked bugs, not a raw-capture gap (instruments-
      service's SFI_PROGRESSIVE_STATS raw capture was already ~healthy 2021→2025-12, confirmed via scoped GCS sample):
      (1) the Phase 0.6 feature-compute backfill (`features-service`'s `compute_sfi_progressive_only.py`) was written
      but never run at scale — the sole prior manifest row was a single-day (2020-01-01) test artifact migrated from a
      retired legacy flat GCS bucket by an unrelated one-off script, not a real backfill; (2) its launcher
      (`deployment-service/scripts/vm/launch-sfi-progressive-features-backfill-vm.sh`) was hardcoded to that same legacy
      flat bucket name, deleted 2026-07-21 by the bucket-consolidation migration — fixed to the canonical `-prd-`
      bucket, `deployment-service@826ca68`; (3) on the first real run the script crashed on day 2 of 2397:
      `ManifestWriter.record_empty()` now hard-requires a typed `reason=` (a writegate contract added after this script
      was written) — fixed with `EmptyConfirmedReason.EXPECTED_NO_FIXTURE`, `features-service@89a2ac9d`. **Backfill
      re-run clean**: VM `features-sfi-progressive-20260724-205430`, full 2020-01-01→2026-07-24 window (2397 days), 2086
      captured / 310 empty / 0 failed, 80,434 fixtures written, `STOPPED` exit_code=0. **Manifest verified**: canonical
      `availability_index.parquet` now carries 16,661 `feature_group=sfi_progressive` rows (was 1) — raw parquet read
      direct from GCS, bypassing the reader's in-process cache.
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
- [x] [DATA] P1. ✅ Ran the round-derivation mechanism to full closure. — **instruments-service (data-op, no code
      change)**. Two-stage: (1) `derive_sports_fixture_round_2026_07_18.py --apply` corpus-wide (270,938 rows scanned,
      374 newly closed for free since the 2026-07-19 terminal state, 26 refused as ambiguous multi-round matchdays); (2)
      a corpus census (single walk, projecting `af_league_id`/`season`/`round`, thread-pooled) isolated the residual to
      486 in-window (season>=2019), registry-member blank rows across 10 (league, season) pairs, then
      `backfill_sports_fixture_round_2026_07_17.py --apply --pairs-file` ran against the 2 pairs actually reachable via
      canonical folders.

      **Full reconciliation — every residual row accounted for, verified by 2 independent census runs agreeing
              exactly (486/486, split identically)**:

              | population | rows | status |
              | --- | ---: | --- |
              | `J2_LEAGUE` (99:2026) | 393 | honest absence — season not yet published (0 fixtures returned by the API), same class the 2026-07-19 sweep already established for this exact league/pattern |
              | `EREDIVISIE` (88:2025) | 7 | fetch-miss residue — API returned 309 fixtures for the season but these 7 specific `af_fixture_id`s weren't among them; same "residue in reached pairs — untouched, not guessed" category the 2026-07-19 sweep's own terminal state already accepted |
              | non-canonical `league=<raw_af_league_id>`/bare folders (10 pairs incl. `league=169`=CHINA_SUPER_LEAGUE) | 86 | **NEW finding**: structurally unreachable by the canonical-folder-scoped mechanism (writer bug, not a data gap) — filed as its own issue doc, see below |

              **Done-when interpretation**: the literal "0 remaining" is not achievable via this mechanism given genuine
              honest-absence + fetch-miss residue (matching the sweep's own precedent for what "terminal" means) plus a newly
              discovered writer bug that is out of this mechanism's scope by construction. The mechanism itself was run to
              full closure with zero remaining ambiguity — every row has a specific, verified reason.

              Findings filed (both require follow-up outside this task's scope):
              `issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` (85 leagues' `day=2026-04-14` shards carry an
              instrument-catalogue schema instead of fixtures data — found incidentally during the census) and
              `issues/sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24.md` (the 86-row non-canonical
              folder writer bug above).

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

- [x] [CODE] P1. ✅ Build a sports pipeline-check for the instruments-service → market-tick-data-service →
      market-data-processing-service → features-service middle leg that asserts CONTENT (not just presence) at each
      stage — no such check exists today for sports, unlike CeFi/TradFi's `/data-pipeline-check-mtds`/
      `/data-pipeline-check-mdps`. **Done when**: the check fails on the pinned busy smoke date (2025-12-20) if any
      leg's output is empty or shape-wrong, verified by deliberately breaking one leg and confirming the check catches
      it. — **features-service@4639106a**.

      New module `features_service/sports/compute/pipeline_middle_leg_check.py` (+ CLI wrapper
                                                                                                                      `scripts/sports/pipeline_content_check.py`, exported from `features_service.sports.compute`), reusing each
                                                                                                                      stage's existing READ-ONLY GCS reader instead of re-deriving path logic — no new whole-corpus walk, no new path
                                                                                                                      template: `read_reference_entity(date, "fixtures")` (instruments-service), `read_odds_data(date)`
                                                                                                                      (market-tick-data-service), `read_bucketed_odds(date)` (market-data-processing-service), and
                                                                                                                      `ml_readiness_check.verify_date(date)` (features-service's own odds_features gate, already-shipped Track K
                                                                                                                      content check). Each leg asserts real CONTENT, not presence: IS fixtures' identity columns
                                                                                                                      (`fixture_id`/`home_team_id`/`away_team_id`/`league_id`/`kickoff_utc`) must be present and not 100% null; MTDS
                                                                                                                      odds ticks' time-identity columns (`minutes_to_kickoff`/`bm_time`/`fetch_utc`) likewise; MDPS bucketed odds'
                                                                                                                      price columns (`home_odds`/`draw_odds`/`away_odds`) must not be 100% null AND (the SHAPE half of the done-when)
                                                                                                                      its distinct `fixture_id` coverage must be ≥10% of the same-date IS fixture count — catches a shard that returns
                                                                                                                      rows but for the wrong/near-empty set of fixtures, which a presence-only check (e.g. the existing
                                                                                                                      `check_pipeline_completeness.py`, which only reads manifest `capture_status`) cannot. CLI defaults `--date` to
                                                                                                                      `SPORTS_SMOKE_DATES["busy"]` (2025-12-20, the pinned busy date named in the done-when) — never synthesizes a day.
                                                                                                                      **Deliberately-broken-leg verification** (the done-when's explicit ask): `tests/sports/unit/test_pipeline_middle_leg_check.py`
                                                                                                                      adds 19 unit tests, including one deliberate-break case per leg — empty-output, all-null-identity-columns, and
                                                                                                                      (MDPS only) the low-fixture-coverage shape-wrong case — each asserting the corresponding `LegResult.passed is
                                                                                                                      False` and, via `run_middle_leg_check`, that the OVERALL report fails while every other (healthy) leg still runs
                                                                                                                      (shard-level isolation, per craft convention). Evidence: `quality-gates.sh` green on features-service (ran twice
                                                                                                                      — once pre-commit on the working tree, once `--no-fix` post-commit to stamp the sentinel against the shipped
                                                                                                                      HEAD); all 19 new tests pass as part of that run.

- [ ] [DIAG] P2. Wire `is_promotion_relegation` (currently hardcoded `False` in `features-service`'s
      `season_context.py`) from the standings relegation-zone classification `_compute_league_batch` already computes,
      or formally retire the field + its `points_at_stake` multiplier if it's genuinely unneeded. **Done when**: either
      the field reflects real relegation-zone data on a sample date, or it's removed with its multiplier and no dangling
      reference remains.
- [x] [DIAG] P2. ✅ Determine whether `clv_*`/`odds_movement_*` being all-null in `odds_features` is honest-absence (if
      they source from MDPS's dead `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` products, never scheduled) or
      a genuine gap — check the actual sourcing, don't assume. **Done when**: a written conclusion states which, with
      sample dates + result counts cited.

      **Conclusion: HONEST-ABSENCE, BY DESIGN — but the todo's own premise about the mechanism was wrong; checking the
                                                                                  actual sourcing (not assuming) caught it.** `clv_*`/`odds_movement_*` do NOT source from MDPS's 3 dead products —
                                                                                  confirmed in the sibling todo above (`sports_closeout_batch1_ao_ready-016`): a workspace-wide grep found zero
                                                                                  consumers of `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` anywhere in `features-service`. The REAL
                                                                                  mechanism is a **structural point-in-time (no-lookahead) design**, unrelated to MDPS scheduling:
                                                                                  `clv_*`/`odds_movement_*` are computed by `compute_clv_features`/`compute_opening_odds`
                                                                                  (`features_service/sports/calculators/odds_velocity.py:98,213`), which both REQUIRE a `T-0` ("closing") row in
                                                                                  their input to produce a non-null value (`compute_opening_odds`: `if open_col in result.columns and close_col in
                                                                                  result.columns: ... else: result[move_col] = np.nan`). `FEATURE_HORIZONS`
                                                                                  (`features_service/sports/calculators/odds_columns.py:211-214`) — the registry of which raw-odds horizons are
                                                                                  visible to each MODEL horizon's feature computation — has exactly 4 model boundaries (`T-24h`, `T-1h`, `T-10m`,
                                                                                  `HT`), and **`T-0` is not a member of ANY of their visible-horizon lists**, even the latest pre-match model
                                                                                  (`T-10m` sees up through `T-10m`, never `T-0`). This is deliberate leakage prevention, documented explicitly at
                                                                                  the call site (`odds_features_exporter.py:170-182`, `_restrict_to_visible_horizons`): "at T-24h the closing
                                                                                  snapshot simply isn't in the input, so `compute_clv_features` returns empty (it needs a T-0 leg)" — giving a
                                                                                  pre-match model the actual closing line would be a lookahead-bias bug. Since the exporter (`export_odds_features`)
                                                                                  only ever emits rows for `FEATURE_HORIZONS`' 4 keys, and none of them include `T-0`, `clv_*`/`odds_movement_*` are
                                                                                  **structurally guaranteed null in every written row**, not merely often-null.
                                                                                  **Live-data confirmation**: ran the real `export_odds_features()` compute path (no writes) for 3 real captured
                                                                                  dates — `2026-06-06` (6 rows, horizons `T-10m`/`T-1h`/`T-24h`, 2 rows each — 100% null on `clv_home`/`clv_draw`/
                                                                                  `clv_away`/`odds_movement_home`/`odds_movement_draw`/`odds_movement_away`), `2026-06-09` (3 rows, same 3 horizons,
                                                                                  1 row each, same 100% null), `2026-07-16` (3 rows, same pattern) — 0 of 12 total sampled (horizon, outcome) cells
                                                                                  across all 3 dates had a non-null `clv_*`/`odds_movement_*` value, matching the structural prediction exactly (no
                                                                                  `T-0` horizon ever appears in the output, so there is no row where a non-null value is even possible). No code fix
                                                                                  needed — this is correct, intentional behavior; the columns exist for schema completeness / future in-play (`HT`+)
                                                                                  use once MDPS's `odds_horizon_bucket` genuinely captures a `T-0` snapshot for a fixture (today `T-0`/in-play
                                                                                  capture is separately known-dark per the parent audit: `live_odds_api = 14 rows in 6 years`).

- [x] [DATA] P2. ✅ Purge the 4 dead dimension groups (players/coaches/referees/rounds, 4,216 rows each) still inflating
      the features manifest — already operator-ruled per `plan_reconciliation_operator_decisions_2026_07_11.md` §A2, not
      a fresh decision; snapshot first (manifest-row snapshot, reversible). **Done when**: a manifest census for these 4
      dimension groups returns 0 rows. — **features-service@bf088de1**. Confirmed no live writer emits these
      `feature_group` values (absent from `batch_write.py`'s `TABLE_TO_EXPORT`; a workspace-wide grep found zero
      production call sites, only a mock-data seed script). Purged 16,864 rows from the consolidated
      `features-sports-prd` availability index + 4 rows from a legacy per-VM shard (16,868 total), snapshotting each
      blob to `_index/purge_backups/` (outside every reader-scanned prefix, so the consolidator can't resurrect them)
      before rewriting. Post-purge census: 0 rows for all 4 groups; every other `feature_group` (fixture_features,
      derived_features, odds_features, injuries, leagues, fixture_stats, fixture_lineups, fixture_player_stats, venues,
      fixture_events, fixtures, teams, standings, sfi_progressive) unchanged. Script:
      `features-service/scripts/sports/purge_dead_dimension_groups_2026_07_24.py` (dry-run verified before apply).
- [x] [DATA] P2. ✅ Purge the 1,337 dead `odds_horizon_bucket_{15m,1h,4h,1d}` manifest rows (a retired, timeframe-baked
      cohort) — snapshot first (manifest-row snapshot, reversible). **Done when**: a manifest census for that data_type
      prefix returns 0 rows. — **ALREADY DONE 2026-07-22** (predates this todo's authoring 2026-07-24), confirmed via a
      fresh read-only census 2026-07-24:
      `market-tick-data-service/scripts/restamp_sports_odds_horizon_bucket_2026_07_22.py@2f3fb7cc` re-stamped these
      1,337 rows to the canonical bare `odds_horizon_bucket` (a RE-STAMP, not a row-delete — row-delete is
      verified-unsafe for this population, `_legacy_seed.parquet` resurrection re-supplies deleted rows on the next
      consolidator merge, per `plans/archive/issues/legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md`),
      snapshotted the full index to `_index/backups/` first per that script's own convention, ran `--apply` on
      2026-07-22 (operator-ruled "Yes, go ahead" per `distinct_values_noncanonical_audit_2026_07_20.md` lines 572-588),
      1,337 restamped / 0 escalated, verified post-write. Confirming census (2026-07-24, read-only, single column-pruned
      parquet read of bucket `market-data-tick-sports-prd-central-element-323112`, row_count=563,384):
      `odds_horizon_bucket_15m`=0, `_1h`=0, `_4h`=0, `_1d`=0; canonical bare `odds_horizon_bucket`=125,400. No new code
      or data change needed — this todo was stale/already-satisfied at authoring time.
- [x] [DIAG] P2. ✅ Confirm sports genuinely never emits `expected_unattempted` in the odds manifest (0 of ~1.97M rows)
      by design, or fix the miscoercion into `empty_confirmed` if it's a bug. **Done when**: a written conclusion states
      which, with the manifest query used to confirm it.

      **Conclusion: BY DESIGN, not a bug.** `record_expected_unattempted` has exactly ONE call site workspace-wide —
                                                                                          `market-tick-data-service/market_tick_data_service/engine/orchestrator/sentinels.py:194`
                                                                                          (`_emit_skipped_venue_sentinels`), gated on `if venue in skipped_shards:` in the per-venue sentinel loop
                                                                                          (`sentinels.py:823`). `skipped_shards[venue]` is populated ONLY at
                                                                                          `market_tick_data_service/engine/orchestrator/venue_fetch.py:551`, itself gated on
                                                                                          `venue.upper() in _VENUES_NEEDING_INSTRUMENT_PREFLIGHT` (`venue_fetch.py:526`) — an instruments-service
                                                                                          catalog-presence preflight check. `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT`
                                                                                          (`market_tick_data_service/engine/orchestrator/preflight.py:245`) is built from CeFi-Tardis + DeFi venues ONLY,
                                                                                          with an explicit code comment: `"Excludes: Sports (self-discovers), Prediction (self-discovers), TradFi/Databento
                                                                                          (UAC registry), Hyperliquid/Aster (hardcoded lists), FX."` Sports's single venue key
                                                                                          (`_LEAGUE_PARTITIONED_VENUES = frozenset({"ODDS_API"})`, `venue_fetch.py:100`) is therefore structurally
                                                                                          unreachable through the preflight-skip path — it can never enter `skipped_shards`, so the per-venue loop's
                                                                                          `if venue in skipped_shards` branch never fires for it, and it always falls through to
                                                                                          `_emit_sports_tier2_sentinels` (`sentinels.py:850-859`) instead. That sports-specific emitter (`_emit_sports_v1_
                                                                                          sentinels` / `_emit_sports_v2_sentinels`) has exactly 3 possible non-captured outcomes for every (bookmaker,
                                                                                          league/fixture) cell — `record_failed` (classified venue error → `attempted_failed`), `record_zero_rows(was_
                                                                                          expected=True)` (expected-but-empty fetch → `attempted_failed`), or `record_empty` (honest absence →
                                                                                          `empty_confirmed`) — `record_expected_unattempted` is never called from this path. Architecturally coherent: CeFi/
                                                                                          DeFi's `expected_unattempted` covers "instruments-service hasn't listed this venue's instrument universe yet, so
                                                                                          there's nothing to attempt" — sports has no such upstream-catalog-absence state because it self-discovers its
                                                                                          universe (bookmaker roster is static config; league/fixture scope comes from the live fixture catalog inside the
                                                                                          sentinel emitter itself, not a pre-attempt IS gate), so every non-captured sports cell is IMMEDIATELY classified
                                                                                          into one of the other 3 states at write time rather than deferred into a "not yet attempted" 4th state.
                                                                                          **Live-data confirmation**: a bounded single-file read of the consolidated
                                                                                          `market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet` (563,384 rows, 2026-07-24)
                                                                                          shows `capture_status` distribution `{captured: 541,464, empty_confirmed: 21,920}` — 0 rows of any other status,
                                                                                          confirming 0 `expected_unattempted` (and, incidentally, 0 `attempted_failed` at this snapshot). Query:
                                                                                          `pd.read_parquet(...)["capture_status"].value_counts()` on the downloaded index bytes via
                                                                                          `unified_trading_library.get_storage_client().download_bytes(bucket, "_index/availability_index.parquet")`.

- [x] [DIAG] P2. ✅ Grep `features-service` and `strategy-service` for any real consumer of MDPS's
      `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` derived products before their fate is decided (operator
      ruling: wire up for real if something downstream needs them, do NOT retire blind). **Done when**: a written list
      of consumers found (or confirmed empty) is produced.

      **Conclusion: CONFIRMED EMPTY — zero real consumers in either repo.** MDPS's 3 adapters declare their canonical
                                                                                      `data_type` keys explicitly: `SportsOddsMovementAdapter.data_type = "odds_movement"`
                                                                                      (`market_data_processing_service/app/adapters/sports/odds_movement_adapter.py:27`),
                                                                                      `SportsOddsSnapshotAdapter.data_type = "odds_snapshot"` (`odds_snapshot_adapter.py:27`),
                                                                                      `SportsArbitrageAdapter.data_type = "arbitrage_opportunity"` (`arbitrage_adapter.py:27`). A grep of both
                                                                                      `features-service` and `strategy-service` for the exact literal strings `"odds_movement"` / `"odds_snapshot"` /
                                                                                      `"arbitrage_opportunity"` (as a `data_type` value, GCS path segment `data_type=<x>/`, or adapter class name
                                                                                      `OddsMovementAdapter`/`OddsSnapshotAdapter`/`ArbitrageAdapter`) returns **zero hits in both repos**.
                                                                                      **False-positive check**: `features-service` DOES contain many hits for `odds_movement_home`/`_draw`/`_away`
                                                                                      (`features_service/sports/calculators/odds_velocity.py`, `odds_calculator.py`, `odds_columns.py`,
                                                                                      `feature_expectations.py`, `data/writer.py`, `exporters/odds_features_exporter.py`) — but these are a
                                                                                      **different, unrelated concept**: an independently-computed FEATURE COLUMN (`closing / opening - 1` per
                                                                                      per-selection odds, see `feature_expectations.py:247-249`'s own comment) derived directly from the raw
                                                                                      `odds_features`/`odds_api` open/close columns already captured by features-service's own pipeline — NOT a read of
                                                                                      MDPS's `odds_movement` GCS product. Confirmed by the exact-literal grep above finding these same files have ZERO
                                                                                      occurrences of the bare `"odds_movement"` data_type string (only the `_home`/`_draw`/`_away`-suffixed column
                                                                                      names). `strategy-service` has zero hits of any kind (feature-column or data_type). Consistent with the parent
                                                                                      audit's finding (`sports_consolidated_audit_2026_07_19.md` §1.3, "§ B2 ROOT-CAUSED") that the only live sports
                                                                                      MDPS job schedules `odds_horizon_bucket` — these 3 adapters are re-exported at the package `__init__.py` level
                                                                                      (`app/adapters/__init__.py`, `app/adapters/sports/__init__.py`) but never registered into any scheduler/job/CLI
                                                                                      entrypoint, i.e. dead code with dead outputs. Per the operator ruling this todo cites ("wire up for real if
                                                                                      something downstream needs them, do NOT retire blind"): nothing downstream needs them — retirement (out of this
                                                                                      todo's scope; done-when is the written consumer list) is now unblocked for a future todo.

- [x] [DOC] P2. ✅ Verify `sports-data-source-coverage-matrix.md`'s body isn't stale-under-banner (check every claim
      against current live source, the same failure mode already found + fixed in 6 sibling sports codex docs), and fix
      the 5 broken `related:` paths in `sports_master.md`. **Done when**: the doc's body matches its banner and every
      `related:` path in `sports_master.md` resolves to a real file. — **unified-trading-pm@bfb77b46c.** Found + fixed
      real staleness: (1) the FIXTURES-migration-status banner claim (code path shipped `is@e19c5a7a`/`@47c1ffb3`,
      historical backfill tracked separately — was stale-claiming the whole migration pending); (2) §1's
      LEAGUE_REGISTRY-derived expected-league-count table had drifted since its 2026-04-20 snapshot, re-verified live:
      `api_football` 95→96, `footystats` 46→48, `transfermarkt` 55→56, total 102→103 (propagated through
      §2.1/§2.2/§2.4's inline restatements too); confirmed the LOWER-case casing target is still `migration_pending` not
      yet live (fresh census: 100% UPPER-case live data) so §2's UPPER-case examples are current-accurate, not stale.
      `sports_master.md` had 7 broken paths (not 5) — files archived from `active/` to dated `archive/` subdirs without
      the referrer being updated; all fixed + verified resolving. Also found + fixed a pre-existing, unrelated broken
      link in `active_plan_inventory_dashboard_2026_07_24.md` (confirmed pre-existing on a clean tree before fixing) —
      someone else regenerated it concurrently with the identical fix, no separate commit needed from me.
- [ ] [CLEANUP] P3. Drop the frozen 2018-2020 `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` GCS scaffolding
      (dead cohort, no live writer), correct `SPORTS_INSTRUMENTS.md`'s stale "lineups player-id strip" claim (verified
      false), and add a junk-symbol guard rejecting non-ASCII characters in fixture names. **Done when**: the
      scaffolding is gone (snapshot first), the doc claim is corrected, and the guard rejects a non-ASCII test fixture
      name.

      **2 of 3 sub-parts SHIPPED 2026-07-24** — doc correction `instruments-service@97fbea22`, junk-symbol guard +
                  5 passing tests `unified-api-contracts@a6346f95` (guard added to the shared `canonical_ids._slug()`, since
                  "fixture names" isn't a distinct concept — team/league/player/venue names all funnel through it; rejects the
                  Unicode replacement char + control chars, still allows legitimate diacritics like "México"). Remaining:
                  locate the actual GCS bucket/path for the frozen scaffolding (not quickly locatable via grep — plain-English
                  "markets"/"outcomes"/"settlements" matches too many unrelated prediction/DeFi call sites) and purge it
                  (snapshot first). Tracked: `/plans/active/issues/sports_closeout_batch1_task018_partial_progress_2026_07_24.md`.

- [x] ✅ [DOC] P3. Document the pre-2019 (2013-2018) api-football exclusion as an intentional, operator-decided scope
      boundary (already ruled — no fresh spend) in the audit's gap table, so the remaining-blanks arithmetic reads clean
      without an unexplained gap. **Done when**: the audit doc states the exclusion explicitly with the ruling citation.
      — unified-trading-pm@ef78bfffb. Updated `sports_consolidated_audit_2026_07_19.md`'s § 6 "Operator decisions
      needed" § T bullet to state the resolution explicitly, citing the exact ruling: "§T decision — ANSWERED 2026-07-20
      (decision 3)" in `sports_consolidated_closeout_2026_07_19.md` Track V — pre-2019 (2013–2018) is intentionally OUT
      OF SCOPE, no further api-football spend. Noted that the 122,864 pre-2019 blank-round rows should be read as
      excluded-by-design against the 2019→2026 in-scope window, not an unexplained gap.
- [x] ✅ [DOC] P3. File an issue doc for the QG structural finding: at least two `quality-gates.sh` steps
      (`check_backfill_vm_disk_provisioning.py` in `deployment-service`, and the ruff LINT step) resolve target paths
      through the canonical MAIN clone rather than respecting `cwd`/a worktree's own tree, so no worktree-based
      isolation reliably gets a green QG sentinel while any other agent has dirty/untracked lint/disk-provisioning
      issues in the shared MAIN clone. File under `plans/active/issues/` with `asset_group: [meta]` (workspace-infra,
      not sports-specific). **Done when**: the issue doc exists with the reproduction steps already known (moving a file
      out of MAIN flips the check clean; a lint failure can reference another agent's untracked MAIN file). —
      unified-trading-pm@749312622:
      `plans/active/issues/qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md`. Carried
      forward the finding + both known reproduction steps verbatim (not re-derived); additionally traced a plausible
      (not independently confirmed) root-cause candidate — `WORKSPACE_ROOT`'s
      `${WORKSPACE_ROOT:-$(cd     "$(git rev-parse --show-toplevel)/.." && pwd)}` fallback pattern in
      `base-service.sh`/`quality-gates.sh` only derives worktree-locally when unset; a stale/persistent `WORKSPACE_ROOT`
      export in the calling shell would make every such gate silently MAIN-rooted regardless of which worktree invoked
      it — flagged as a hypothesis for the new [DIAG] todo to confirm, not asserted as proven (this session's own shell
      had it unset).

## Progress Log

- **2026-07-24 (slot-6, complete)** — Todo 4 (`sfi_progressive_features` corpus-empty DIAG) — see the flipped checkbox
  above for the full root-cause + evidence. One aside worth keeping for whoever touches this area next: this sandbox's
  `gsutil` fails WIF auth (`Unable to retrieve Identity Pool subject token`) while `gcloud storage` works fine with the
  same ADC — silently broke `create-code-tarballs.sh`'s upload step; worked around with a local `gsutil→gcloud storage`
  shim, not filed as an issue doc since it's unclear whether it reproduces outside this session's credential setup.
  Separately filed a real (low-severity) finding as its own issue doc:
  `manifest_reader_silent_empty_on_missing_project_id_2026_07_24.md` — `read_availability_index()` silently returns an
  empty DataFrame (not an error) when `GCP_PROJECT_ID` is unset, which cost real debugging time chasing a phantom
  "manifest write didn't land" false alarm before the raw parquet read (16,661 rows) proved the backfill was fine.
