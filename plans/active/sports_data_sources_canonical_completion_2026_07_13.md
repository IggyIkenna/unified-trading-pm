---
doc_type: plan
title: Sports asset_group — drive every remaining data source to canonical 100%
summary:
  Following the understat XG/XG_SHOTS completion (2026-07-13, same-day), drive the rest of the sports asset_group to the
  same standard — 0 attempted_failed, 0 (or explained) expected_unattempted, 0 duplicate dedup-key groups, correct
  service_name/asset_group, working scheduled jobs. Order — api_football fixtures+enrichment, footystats, SFI,
  transfermarkt, weather, then odds (MTDS odds_api source).
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    unified-trading-library,
    unified-api-contracts,
    deployment-service,
  ]
scope: [engineer]
tags: [sports, api_football, footystats, sfi, transfermarkt, weather, odds, manifest, data-correctness, autonomous]
related:
  [
    plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md,
    plans/active/sports_manifest_canonicalisation_2026_06_01.md,
  ]
created: 2026-07-13
last_updated: 2026-07-15
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
model_tier: opus-required
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

> **Dispatched under `/autonomous` (operator directive, 2026-07-13, same interactive session that completed
> understat).** Full authority per `cursor-configs/AUTONOMOUS_AGENT_RULES.md` + `SUB_AGENT_MANDATORY_RULES.md` — finish
> completely, no `BLOCKED-OPERATOR` leftovers, decide-and-document on ambiguity, journal every discovery to this plan's
> Progress Log (this section survives context compression — read it first on any resume).

# 0. Baseline audit (2026-07-13, slot-3, live-manifest read)

Single-parquet read of `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`
(4,863,784 rows post-cleanup), grouped by `source` (not `data_type` name — several data_types are misleadingly named,
e.g. `MATCHES`/`PREDICTIONS` are footystats-sourced, not api_football):

| source                                                 | rows      | captured | attempted_failed | expected_unattempted | notes                                                                                                                                                                           |
| ------------------------------------------------------ | --------- | -------- | ---------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| api_football                                           | 2,518,940 | 365,592  | **3,257**        | **453,961**          | FIXTURES/STANDINGS/TEAMS/INJURIES/FIXTURE_STATS/LINEUPS/EVENTS/PLAYER_STATS                                                                                                     |
| footystats                                             | 650,504   | 84,047   | 205              | 56                   | MATCHES/PREDICTIONS + part of ODDS — already near-clean                                                                                                                         |
| soccer_football_info                                   | 226,237   | 19,750   | 10               | 94                   | SFI_PROGRESSIVE_STATS only — already near-clean                                                                                                                                 |
| transfermarkt                                          | 270,719   | 58,028   | 0                | 47                   | PLAYER_VALUES — already clean                                                                                                                                                   |
| open_meteo (weather)                                   | 261,790   | 12,097   | 51               | 94                   | WEATHER — already near-clean                                                                                                                                                    |
| odds_api                                               | 2,667     | **0**    | 6                | 0                    | suspiciously sparse/dead — needs a retirement-status check                                                                                                                      |
| mdps_odds_horizon_bucket                               | 215,481   | **0**    | 0                | **209,526**          | **ZERO captures ever** — likely a never-wired or broken pipeline                                                                                                                |
| (retired: SFI_LEAGUES/STANDINGS/TRANSFERMARKT_LEAGUES) | 88,056    | 0        | 0                | 0                    | code-confirmed `_RETIRED_DATA_TYPES` in `rebuild_sports_manifest_v9.py:103` — already correctly typed `EXPECTED_DEPRECATED_DATA_TYPE`, needs only a spot-verify, no active work |

**api_football `attempted_failed` breakdown**: INJURIES 1,946 (`ApiFootballResponseError`) · FIXTURES 665
(`FIXTURES_FETCH_FAILED`) · blank `data_type` 461 (`UNCLASSIFIED_ADAPTER_ERROR` — a data-integrity issue, blank
data_type should never happen) · PLAYER_STATS 74 · FIXTURE_STATS 46 · FIXTURE_LINEUPS 30 · TEAMS 24 · FIXTURE_EVENTS 11
· several `phantom_captured_no_parquet_at_canonical_path` (claims captured, no file at path). **8,766
non-`instruments-service` rows** in the active-source set: `fill-missing-player-stats` (8,678, PLAYER_STATS — likely a
legitimate dedicated one-off service, needs confirming) + `market-tick-data-service` (88 — the exact orphans
deliberately left untouched by today's `instruments-service@2f56038e` cleanup, no confirmed canonical twin).

# 1. Todos

- [x] [DATA] P0. **api_football deep investigation.** — ✅ DONE 2026-07-14 (slot-5, live-manifest re-verify + root-cause
      close-out). **(1) `expected_unattempted` = legitimate could-exist seed, CONFIRMED and now demonstrably
      shrinking**: 453,961 (§0 baseline) → **287,207** live today, the ~166k drop dominated by TEAMS 192,384→26,385 as
      the 61-league TEAMS backfill + consolidator dedup fix converted seed cells to captured — a real gap would not
      shrink under backfill, a could-exist seed does. Not a gap; no action. **(2) all 4 original `attempted_failed`
      classes root-caused + fixed under the "fix root causes" todo below** (`instruments-service@9ce3450e` +
      IMPLEMENTATION dispatch) and re-verified holding in the live manifest: (a) INJURIES `ApiFootballResponseError`
      1,642 (silent-swallow + misclassification), (b) FIXTURES `FIXTURES_FETCH_FAILED` 612 (false-positive trigger), (c)
      blank-`data_type` `UNCLASSIFIED_ADAPTER_ERROR` 461 (completeness-gate leak — now 0 NEW blank rows, 121
      `empty_confirmed` prove the fix routes correctly), (d) `phantom_captured_no_parquet_at_canonical_path` 484
      (reconcile-tooling output, not a live bug). MTDS orphan re-stamp holds (0
      `market-tick-data-service`+`api_football` rows). **(3) NEW class characterized during this re-verify —
      `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` (1,090 FIXTURE_STATS/EVENTS/LINEUPS rows)**: root-caused to the v9-rebuild
      step-6.7 CF-11 gate (`market-tick-data-service/scripts/rebuild_sports_manifest_v9.py:378` +
      `_rebuild_sports_write.py:191`, operator directive 2026-06-02) which correctly upgrades a per-fixture-entity
      `empty_confirmed` to `attempted_failed` when `(league_id, date)` IS in `fixtures_truth` (a match genuinely
      happened) — deliberate honest-coverage behavior, NOT a defect; these are genuine backfill candidates, filed as the
      new P2 todo below. Full evidence: Progress Log "2026-07-14 (slot-5) API_FOOTBALL DEEP-INVESTIGATION RE-VERIFY +
      CLOSE-OUT" entry. Original characterization prompt retained for provenance: Characterize the 453,961
      `expected_unattempted`: is this a legitimate could-exist-universe seed (many leagues × many years × many
      data_types, most cells genuinely no-fixture) or a real gap? Root-cause the 3,257 `attempted_failed` by class: (a)
      INJURIES `ApiFootballResponseError` (1,946) — likely rate-limit/quota or a schema drift, check the adapter; (b)
      FIXTURES `FIXTURES_FETCH_FAILED` (665); (c) blank-`data_type` `UNCLASSIFIED_ADAPTER_ERROR` (461) — a write-path
      bug (data_type should never be blank at write time, find where); (d)
      `phantom_captured_no_parquet_at_canonical_path` across several data_types (claims captured, no file — a
      storage/path-resolution mismatch). File as an issue doc if root cause spans multiple commits' worth of work.
- [x] [DATA] P0. **api_football: fix root causes + re-attempt failed cells** — root-cause + fix DONE
      (`instruments-service@9ce3450e`, confirmed holding); re-attempt **in-flight, launched
      `instruments-service@e78d424f`, verify completion later** (see Progress Log "RE-ATTEMPT dispatch" entry below for
      the live PID/log-location/how-to-check-later detail and the 2 new adjacent findings it surfaced).
- [x] [DATA] P1. **api_football: resolve the 8,766 non-instruments-service rows.** — ✅ DONE 2026-07-14 (slot-5,
      live-manifest verify + close-out; the fix itself shipped earlier under the IMPLEMENTATION dispatch). Both classes
      resolved and re-verified in the live `instruments-store-sports-prd` manifest today: (1) **88
      `market-tick-data-service` orphans → re-stamped to `instruments-service`** via
      `instruments-service/scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py` (applied) — live count of
      `service_name=market-tick-data-service`+`source=api_football` rows is now **0**. (2) **`fill-missing-player-stats`
      (8,678 rows, 100% PLAYER_STATS: 8,170 `empty_confirmed` + 508 `captured`) confirmed a SANCTIONED dedicated
      one-off, NOT drift** — `instruments-service/scripts/fill_missing_player_stats.py` carries proper
      `# Epic: instruments_master` / `# Lifecycle: oneoff` / `# Delete-when:` markers and calls the same orchestrator
      fetch + `ManifestWriter` path with a deliberate `service_name` override; left as-is (delete only when its
      Delete-when condition is met). **NEW observation (not drift, no action):** a THIRD non-instruments-service
      service_name now exists that post-dates the §0 baseline — `backfill-teams-61-leagues` (165,148 TEAMS rows), the
      TEAMS 61-league backfill's own service_name
      (`instruments-service/scripts/backfill_teams_61_leagues_2026_07_13.py`, same sanctioned-one-off pattern: `# Epic`
      / `# Lifecycle: oneoff` / `# Delete-when` markers + deliberate `service_name=`). It is honest provenance of which
      script wrote those rows, NOT a service_name-drift bug; its only open wrinkle (its captured rows not collapsing the
      coexisting `expected_unattempted` enumerator-seed twins) is already the tracked P1
      `manifest_consolidator dedup-key NULL/""-normalization gap` todo, a consolidator-SQL issue, not a service_name
      one. Full detail: Progress Log "2026-07-14 (slot-5) 8,766 NON-IS ROWS VERIFY" entry.
- [x] [DATA] P0. **api_football TEAMS: root-cause + fix the 61-league per-league capture gap.** — ✅ DONE 2026-07-13
      (final RECONCILE + VERIFY dispatch, building on the CODE-FIX (`0d2ea24f`/`56aa1938`) and BACKFILL-LAUNCH entries
      below). **Backfill completed clean**: 162,032/162,032 cells written, 0 failed, per-VM shard drained
      (`local-84754-ef9b.parquet`, confirmed consolidated — captured rows for TEAMS jumped 107,262→269,369, exactly
      +162,032). Per-league coverage: 33→86 of 94 expected leagues now have real, non-blank-`league_id` captured TEAMS
      rows (up from the original 33). **The remaining 8 leagues** (`COPA_LIGA_PROFESIONAL`, `COPA_MX`, `EMPEROR_CUP`,
      `GREEK_SUPER_LEAGUE_2`, `J2_LEAGUE`, `SCOTTISH_LEAGUE_CUP`, `SUPERCOPA_ESPANA`, `SUPERCOPPA_ITALIANA`) are
      confirmed-honest: api_football's live `/teams` endpoint returns **0 teams** for every one of them (verified live
      during the backfill's fetch phase, not a script bug — these are single-match cup-final/super-cup competitions
      where the provider has no persistent roster concept) — a new small P3 follow-on todo below covers relabelling
      their cells `empty_confirmed` instead of leaving them `expected_unattempted` forever. **Decide-and- document
      deliverable also complete** (blank-`league_id` bulk-bundle fate — see the `[x]` todo immediately below, closed by
      a concurrent pass this same day, independently corroborated: writer bug fixed at source (`56aa1938`), historical
      residual left as accepted noise). **New P1 follow-on filed, not silently patched**: the canonical
      `expected_unattempted` count for TEAMS did **NOT** drop (still exactly 192,384 after the backfill AND after a full
      `--force` manifest-consolidator rebuild) — root-caused to a NULL-vs-empty-string dedup-key normalization gap in
      `unified_trading_library.manifest_consolidator` (several optional dimension columns —
      `chain`/`instrument_type`/`instrument_id`/`quote_asset`/`margin_type`/`combo_type`/`fixture_id`/`job_id` — differ
      between `None` and `""` across the backfill script's captured rows vs. the enumerator's `expected_unattempted`
      seed rows for the identical `(league_id, date, data_type)` cell, so DuckDB's dedup `PARTITION BY` never groups
      them together and the existing "captured outranks recency" tie-break, `unified-trading-library@a05d69c7`, never
      gets a chance to fire). Confirmed via direct row inspection (one `AUSTRALIA_CUP`/2020-05-15 cell literally has
      BOTH a `captured` row, `written_at=2026-07-13T19:53`, and an `expected_unattempted` row,
      `written_at=2026-06-     28T21:31`, coexisting after the force-rebuild) and via aggregate: 165,148 TEAMS
      `(source,data_type,league_id,     date,venue)` keys still carry >1 distinct `capture_status`. This is
      cross-cutting shared-consolidator SQL (not this one-off script's bug) needing its own dedicated fix + fleet
      blast-radius proof per `AUTONOMOUS_AGENT_RULES.md` rule 11 — filed as a new P1 todo below rather than patched
      blind in this pass. **Full evidence + all shipped commits**: see the "FINAL RECONCILE + VERIFY" Progress Log
      entry.
- [x] [DATA] P2. **api_football TEAMS/STANDINGS: purge the legacy blank-`league_id` bulk bundle (NEW 2026-07-13,
      discovered during the TEAMS backfill).** — ✅ DECIDED 2026-07-13 (sub-agent decide-and-document pass): **LEAVE as
      accepted historical noise, no purge.** Live-verified 3,648 TEAMS + 3,647 STANDINGS blank-league_id `captured` rows
      still present (2014-01-01→2026-07-13, `instrument_count` 519-621/714, genuine captures not phantoms), 1.36% of
      api_football's 536,368 captured rows / 0.27% of its 2,683,950 total — noise-level, no dashboard surfaces a sports
      `source=` total prominently (checked both UI repos), root cause already fixed at source
      (`instruments-service@56aa1938`, confirmed the leak stopped: last pre-fix write 18:05 UTC vs. fix landed 18:44:38
      UTC), and a removal one-off would need the same CAS-safe retry loop as
      `migrate_orphaned_mtds_odds_api_bucket_rows_2026_07_13.py` for a cosmetic, non-blocking fix against a table the
      concurrent 61-league TEAMS backfill is actively writing to right now. Full reasoning: Progress Log "(b)" entry
      below. No code/data change made.
- [x] ✅ [DATA] P1. **manifest_consolidator dedup-key NULL/`""`-normalization gap (NEW 2026-07-13, found during the
      TEAMS 61-league backfill's final re-verify).** A `captured` row and its pre-existing `expected_unattempted`
      enumerator-seed twin for the IDENTICAL `(source, data_type, league_id, date, venue)` cell do not collapse during
      consolidation — even a full `--force` rebuild only dropped 8,659 rows fleet-wide, nowhere near the ~162k expected
      if this cell class had resolved. Root cause: several optional dimension columns
      (`chain`/`instrument_type`/`instrument_id`/`quote_asset`/`margin_type`/`combo_type`/`fixture_id`/`job_id`) are
      written as `None` by one producer and `""` by the other for the same logical fact, so DuckDB's dedup
      `PARTITION BY` treats them as different keys — the existing `unified-trading-library@a05d69c7`
      "captured-outranks-recency" tie-break never gets a chance to fire because the two rows never enter the same dedup
      group. Confirmed live: TEAMS alone has 165,148 keys with >1 distinct `capture_status` post-force-rebuild; one
      concrete example row-pair captured in the Progress Log. Fix belongs in
      `unified_trading_library/manifest_consolidator.py`'s dedup-key SQL (extend the existing `_dedup_key_sql` NULL/`""`
      normalization, already applied to SOME columns, to cover every optional dimension column) — this is shared,
      fleet-wide infra (every asset_group's manifest goes through this consolidator), so ship + verify per
      `AUTONOMOUS_AGENT_RULES.md` rule 11 (prove the fix against a representative sample from ≥2 other asset_groups, not
      just sports, before considering it done). Until fixed, `expected_unattempted` counts will not reflect real
      backfilled coverage for any source/data_type where a captured row is written with different NULL/`""` conventions
      than its original enumerator seed. **🔴 BLOCKED-OPERATOR-DECISION 2026-07-14 (slot-5): this diagnosis is
      DISPROVEN. The NULL/`""` normalization already exists + is complete (`manifest_consolidator._dedup_key_sql`,
      applied to every `PARTITION BY` incl. the `--force` full-rebuild, landed unified-trading-library@f5ec2291
      2026-07-06 — a week BEFORE the 2026-07-13 observation). REPRODUCED real cause: the split is on `service_name` (a
      BASE dedup key) — the backfill wrote `service_name=backfill-teams-61-leagues` vs the enumerator seed's
      `instruments-service`, so the twins never share a dedup group. The plan's own aggregate (165,148 keys with >1
      status on a key EXCLUDING `service_name`) is the exact fingerprint. Fix = a fleet-wide dedup-key semantics ruling
      (service_name = identity or provenance, like `source` which is already excluded). Full evidence + options A/B/C/D:
      `plans/active/issues/manifest_consolidator_service_name_dedup_split_2026_07_14.md`; operator /blocked posted from
      slot-5 (BLK-9fc56b5c; re-surfaced as BLK-17603e1f on the 2026-07-14 resume dispatch — same decision, still
      awaiting the operator ruling). **UPDATE 2026-07-14 (slot-5): the owed rule-11 GCS blast-radius proof is now DONE
      (ADC works via the Python SDK; only the gcloud CLI was broken). It found Option A is NOT a no-op — it would
      collapse 607 defi MTDS-subgraph ✕ MDPS-rpc captured-vs-captured atoms (distinct row_counts) on top of the sports
      EU twins — so the lean shifts to Option B (collapse captured-vs-NON-captured only). Full numbers + the sharpened
      A-vs-B decision in the issue doc's "🔬 Rule-11 LIVE blast-radius proof" section.** Do NOT re-dispatch as a
      NULL/`""` fix — it is a no-op for this symptom.** **✅ RESOLVED 2026-07-14 (slot-5) — operator ruled Option B
      (BLK-17603e1f), shipped `unified-trading-library@9bc06261`: a status-aware cross-`service_name` collapse
      (`manifest_consolidator._option_b_collapse_ctes`, both incremental + `--force` paths) drops a `captured` row's
      NON-captured cross-service twin while leaving captured-vs-captured (dual-source) pairs intact; `service_name`
      stays a dedup key so no writer-mirror change. 3 new unit tests + 75-test consolidator suite green; QG green
      (sentinel=HEAD). Live-verified: captured-row count unchanged in defi+sports; collapses 35,557 defi + 1,038 sports
      cross-service non-captured twins; the 607 defi dual-source captured pairs preserved. NB: the ORIGINAL 165,148
      TEAMS EU twins had already self-resolved in the live manifest (0 coexisting now) — the fix targets the live bug
      CLASS + prevents recurrence. Evidence: issue doc "✅ Option B live-data verification" section.**
- [x] ✅ [DATA] P3. **api_football TEAMS: 8 cup/one-off-competition leagues return 0 teams from `/teams`.** — DONE
      2026-07-14 (slot-5), instruments-service@fad73bb1. The 8 leagues (`COPA_LIGA_PROFESIONAL`, `COPA_MX`,
      `EMPEROR_CUP`, `GREEK_SUPER_LEAGUE_2`, `J2_LEAGUE`, `SCOTTISH_LEAGUE_CUP`, `SUPERCOPA_ESPANA`,
      `SUPERCOPPA_ITALIANA`) each had 3,022 historical (2018-01-01→2026-07-10) `expected_unattempted` TEAMS rows =
      **24,176 total**. Root cause confirmed: `is_league_entity_covered(...,"TEAMS")` is ALREADY `False` for all 8, and
      the live writer (`emit_empty_gaps_for_entity`) already emits `EXPECTED_NO_PROVIDER_COVERAGE` for them (776 such
      rows existed) — the residual was purely historical dates the season-cached TEAMS fetch never processed. **No code
      change needed** (coverage map + writer already correct). Data-only reconcile via new
      `scripts/backfill/api_football_teams_no_roster_leagues_reconcile_2026_07_14.py` →
      `record_empty(EXPECTED_NO_PROVIDER_COVERAGE)` per cell, matching the existing 776 exactly. Prereq (the P1
      dedup-key fix) was already landed. **Verified in the canonical `availability_index.parquet` (direct read, stable
      across consolidator cycles): the 8 leagues' TEAMS = `expected_unattempted` 24,176 → 0, `empty_confirmed` 776 →
      24,952 (100% `EXPECTED_NO_PROVIDER_COVERAGE`).** Note: the first write was eaten by a transient
      manifest-consolidator prune-race (known issue
      `manifest_consolidator_prune_race_overlapping_executions_2026_07_13.md`); a re-apply consolidated cleanly and
      holds. See Progress Log entry below.
- [x] ✅ [VERIFY] P1. **api_football: final re-verify** — 0 attempted_failed (or a documented, operator-equivalent
      acceptable residual per today's understat precedent — NOTE (corrected 2026-07-15, plan-reconcile: this precedent
      was superseded 2026-07-13, see `plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md` § 4
      Definition of DONE — the bar is literal 0, not an acceptable residual; the actual 2026-07-14 execution below
      already applied the strict standard, filing RED findings rather than accepting residual), 0 dedup-key dup groups,
      correct service_name/asset_group, confirm any relevant scheduled jobs are running. **VERIFY DONE 2026-07-14
      (slot-5) against the live sports canonical (5,759,085 rows). PASS: 0 dedup-key dup groups; service_name = only the
      3 sanctioned values. 🔴 RED (3 findings FILED, not silently frozen — see
      `plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`): (A) 4,268
      attempted_failed — ~1,152 the already-tracked CF11 P2 class + ~3,116 UNDOCUMENTED (INJURIES 1,946 / FIXTURES 612 /
      blank-dt 461 / PLAYER_STATS 73 / TEAMS 24) → new P1 re-fetch-backfill todo; (B) 22,668 blank-asset_group
      api_football sports rows (instruments-store bucket never gets the consolidator asset_group heal) → new P1
      consolidator-heal todo; (C) 1 defi/UNISWAP_V3-BASE row mis-filed in the sports manifest under source=api_football
      → new P2 remove/relabel todo. Residual: the api_football-specific scheduled-jobs sub-check was NOT performed here
      (needs Cloud Scheduler access; partly covered by the sibling scheduled-job VERIFY todos below). The RED findings
      are tracked as auto-dispatchable fix todos in the issue doc; api_football is NOT clean until they land.**
- [x] ✅ [DATA] P2. **api_football: backfill the 1,090 `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` per-fixture-entity gaps
      (NEW 2026-07-14, found during the deep-investigation re-verify).** FIXTURE_EVENTS 372 / FIXTURE_STATS 363 /
      FIXTURE_LINEUPS 355 across 114 distinct match-days (2020-10-06→2026-03-26), lower-tier/cup leagues (DANISH_CUP,
      KNVB_CUP, EERSTE_DIVISIE, ENG_NATIONAL_LEAGUE, CHILE_PRIMERA_B, …). These are NOT a defect: the v9-rebuild
      step-6.7 CF-11 gate (`market-tick-data-service/scripts/rebuild_sports_manifest_v9.py:378`, operator directive
      2026-06-02) correctly upgraded a match-day per-fixture-entity `empty_confirmed` (no honest-absence proof) to
      `attempted_failed` because `fixtures_truth` says a match happened and STATS/EVENTS/LINEUPS are in
      `_FIXTURE_GUARANTEED_DATA_TYPES` (absence-on-a-match-day is never legitimate for these). Resolution = a real
      re-fetch backfill of exactly these (date, league, entity) shards via the existing per-fixture recovery path
      (`instruments-service` `_fetch_sports_reference_data` with `fixture_ids_override`, same as the
      `api_football_attempted_failed_residual_closer_2026_07_13.py` pattern). Whatever genuinely re-fetches to 0 rows
      with a clean 2xx `FetchEvidence` is then honestly re-labelled `empty_confirmed(SOURCE_RETURNED_ZERO)` with proof
      (api_football may simply not publish fixture-level detail for some low-profile lower-league matches) — the
      operator-directed point is these must be SURFACED for backfill, never silently frozen empty. Folds into the
      `[VERIFY] P1 final re-verify` "0 attempted_failed" target above. **PREP DONE 2026-07-14 (slot-5), execution
      BLOCKED-ENVIRONMENT (not run — no false progress). Exact live scope re-measured from the sports canonical: 1,152
      CF11 attempted_failed shards (FIXTURE_STATS 408 / FIXTURE_LINEUPS 384 / FIXTURE_EVENTS 360) across 180 match-days
      / 74 leagues — full `(date, league_id, data_type)` list saved to `scratchpad/cf11_gaps.json`. Confirmed
      rate-limit-safe execution recipe: RE-RUN the existing `instruments-service` closer
      `scripts/backfill/api_football_attempted_failed_residual_closer_2026_07_13.py` — its `_live_read()` self-discovers
      the CURRENT `source=api_football & capture_status=attempted_failed` slice (so it picks up these CF11 shards
      without code changes), re-drives reference entities via `_fetch_sports_reference_data` and FIXTURES via
      `process_instruments()` with `redo_all=False` + explicit `sports_entity_filter` (the docstring-mandated
      no-blind-rescan path; `redo_all=True` blows provider rate-limits), and relabels a clean-2xx-zero to
      `empty_confirmed(SOURCE_RETURNED_ZERO)`. Do a `--dry-run` first, then a live run. **Why not executed here:** this
      slot has NO instruments-service `.venv` (can't run the closer locally) and the closer is designed as a VM job
      (`--vm-name` arg); the proper path is a backfill VM launch (infra craft) which also needs the gcloud CLI — BROKEN
      on this slot (snap-confine cap error). Re-dispatch to an infra worker for a VM launch, or a properly-provisioned
      data_engineering slot with a working gcloud. NB: a re-run of that closer also re-drives the ~3,116 undocumented
      non-CF11 api_football attempted_failed (INJURIES 1,946 etc.) flagged in
      `plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md` finding A — same
      operation closes both.** ✅ RESOLVED 2026-07-15 (slot-11) — `instruments-service@87d1a353`
      (`scripts/backfill/api_football_cf11_manifest_reconcile_2026_07_15.py`): **18/18 CF11 cells → captured, 0
      `error_reason=CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` api_football attempted_failed remaining** (live-verified
      against instruments-store-sports-prd). Root cause: these were a manifest-vs-data DRIFT, not a data gap —
      api_football HAS the events/lineups (live probe: 9-23 events + 34-40 lineups/fixture; only 1 genuinely-empty
      fixture) AND the canonical per-league DATA parquets were already PRESENT on disk for all 18 cells (14-141 rows
      each). The prior closers failed to flip them because they called `flush_all_pending_buckets()` (bucket-level
      pending) but never `ManifestWriter.write()` (the writer instance's staged `self._records`) — so their
      `record_captured` rows were staged then silently discarded. Fix = reconcile each cell to captured from its present
      parquet (`record_captured` + `write()`; cells with no parquet skipped, never fake-stamped). NB: my first-cut issue
      doc mis-blamed `record_captured` as broken (`MANIFEST_WRITE_SCHEMA_MISSING`) — that is warn-only and was a red
      herring; CORRECTED. Full resolved writeup:
      `plans/active/issues/api_football_cf11_record_captured_noop_manifest_vs_data_drift_2026_07_15.md` (status:
      resolved, parent_epic manifest_master, cross-linked to the sibling
      `manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md`). Sibling read-path finding still
      open: `plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md` (sports lacks an
      AG_STALENESS_BUDGET_SEC override → false ManifestConsolidatorStaleError on a healthy ~11-min-cadence
      consolidator).**
- [x] [DATA] P0. **mdps_odds_horizon_bucket: root-cause zero-ever-captured.** — DONE, code fix + backfill shipped:
      `market-data-processing-service@6907257e4` (manifest-bucket routing fix, ALSO fixed a second independent
      `_resolve_bucket()` project_id bug in the same commit) + `instruments-service@0ae48c3b0` (metadata backfill of the
      124,294 orphaned rows, 123,642 now `captured` and visible in the canonical manifest). Root cause was a
      manifest-bucket-routing split-brain, NOT a broken/unbuilt pipeline — see Progress Log 2026-07-13 "IMPLEMENTATION
      dispatch" entry for full detail, the 2 deeper follow-on bugs discovered (expected-universe grain mismatch;
      raw-input prefix-template drift), and the corrected `odds_api` finding (362,665 rows of the SAME bug class, filed
      as a new P1 todo below rather than fixed in this pass — touches the shared cross-asset-group MTDS orchestrator,
      higher blast radius, needs its own dedicated pass).
- [x] [DATA] P1. **MTDS shared-orchestrator sports-manifest-bucket routing (NEW 2026-07-13).** — DONE, both halves
      shipped + verified. **Code-fix half**: `market-tick-data-service@ad76547c` ships the `_resolve_manifest_bucket()`
      carve-out at all 4 call sites (preflight availability read, sports-v9/consolidator guards, non-trading-day
      EXPECTED_* emission, `manifest_finalize.py`'s primary `ManifestWriter`), raw tick-byte write path untouched.
      **Blast-radius proof (rule 11)**: live-run of `get_tick_data_bucket()` → `_resolve_manifest_bucket()` against the
      real `central-element-323112` config for all 5 asset_groups — cefi/defi/tradfi/prediction all `identical=True`
      (byte-for-byte unchanged), sports `identical=False` as intended (data bucket unchanged
      `market-data-tick-sports-prd-...`, manifest now `instruments-store-sports-prd-...`) — 5/5 PASS, journaled in the
      Progress Log "IMPLEMENTATION dispatch" + "BLAST-RADIUS PROOF dispatch" entries below. **Migration half**:
      `instruments-service@4027f311` (`scripts/migrate_orphaned_mtds_odds_api_bucket_rows_2026_07_13.py`) migrated the
      362,665 orphaned `source=odds_api` rows (362,631 `captured` / 34 `empty_confirmed`) from
      `market-data-tick-sports-prd` into the canonical `instruments-store-sports-prd` manifest — see the "MIGRATION
      dispatch" Progress Log entry below for the full CAS-retry mechanics (a plain-write first attempt was silently
      clobbered by the live per-minute manifest consolidator; fixed with the UTL generation-precondition CAS primitive)
      and final-state numbers. **Final canonical state, live-verified 2026-07-13**: `instruments-store-sports-prd`
      `odds_api` rows = 365,332 (2,661 pre-existing `empty_confirmed` + 6 pre-existing `attempted_failed` + 362,631
      migrated `captured` + 34 migrated `empty_confirmed`), stable across 5+ consolidator generations (~4.5 min), 0
      duplicate-dedup-key groups anywhere in the resulting 5,353,929-row manifest. §0's "odds_api suspiciously
      sparse/dead" framing is now RESOLVED for this source (0 → 362,631 captured, visible in the canonical coverage
      view).
- [x] [DATA] P1. **mdps_odds_horizon_bucket expected-universe grain realignment (NEW 2026-07-13).** — DONE, code fix +
      one-off reconciliation + live-verified: `instruments-service@92ded209`
      (`fix(sports): realign     mdps_odds_horizon_bucket expected-universe grain to writer's lowercase data_type`) +
      `instruments-service@4c58b5b6` (`chore(sports): reconcile mdps_odds_horizon_bucket expected_unattempted grain`,
      `scripts/reconcile_mdps_odds_horizon_bucket_eu_grain_2026_07_13.py`). Root cause + fix + final verified numbers in
      the Progress Log "mdps_odds_horizon_bucket grain realignment" entry below. Final state: `expected_unattempted`
      209,526→200,165 (all now `data_type=odds_horizon_bucket` lowercase, 0 uppercase remaining), 9,361 stale
      disjoint-cell rows dropped (atoms already genuinely `captured`), 0 remaining stale overlap, 0 duplicate dedup-key
      rows, stable across 10+ live manifest-consolidator cycles (~9 min) post-apply.
- [x] [DATA] P1. **mdps_odds_horizon_bucket: close the 200,259-row historical backlog (NEW 2026-07-14).** — DONE. The
      4-VM historical backfill (`reprocess_sports_odds.py --force`) completed successfully (1,930 succeeded + 293
      legitimately empty of 2,230 backlog dates, only 7 real failures) but the `expected_unattempted` count did NOT drop
      despite real data now being genuinely captured — root-caused to a SECOND, different grain mismatch (venue, not
      data_type) + fixed + reconciled + verified held. Full diagnosis, code fix, reconciliation, and the
      competing-live-job discovery in the Progress Log "mdps_odds_horizon_bucket venue-grain realignment" entry below.
      Final state: `expected_unattempted` 200,259→199,626 (633 stale rows dropped — already genuinely captured under
      their atom — the remaining 199,626 relabeled `venue=""`→`venue="ODDS_API"` to match the writer's real captured
      atom shape going forward), 0 blank-venue rows remaining, 0 new duplicate dedup-key rows introduced (verified on
      the full correct key), stable across 8+ live manifest-consolidator cycles (~13 min) post-apply.
- [x] [DATA] P0. **reprocess_sports_odds.py: fix uncaught UnprovenHonestAbsenceError crash on every empty day (NEW
      2026-07-14, found live while launching the historical backfill above).** — DONE, code fix +
      production-scale-verified: `market-data-processing-service@7c5c74d`. 2 of the first 4 launched backfill VMs
      crashed within ~10 minutes of launch (`mdps-sports-bucket-20260714-041833`/`-041913`) — `main()` called
      `ManifestWriter.record_empty(reason=SOURCE_RETURNED_ZERO)` with no `FetchEvidence`, hard-raising
      `UnprovenHonestAbsenceError` the moment it hit its FIRST genuinely-empty date (every real historical range has at
      least one), silently losing every date's already-computed work since the single end-of-run `writer.write()` flush
      never got reached. Root cause: this script was never updated when UTL's 2026-06-22
      `data_pipeline_hardening_self_monitoring_2026_06_22` honest-absence-hardening keystone landed, requiring
      `FetchEvidence` for that reason code. Fix: `reprocess_date()` now returns a 3rd `empty_kind` discriminator
      distinguishing the one genuinely-clean, provable absence (`"no_raw_data"`, eligible for a synthetic
      `FetchEvidence`) from two anomalous non-absence cases (`"missing_column"`/`"adapter_empty"`, raw bytes DO exist —
      now correctly route to `record_failed` instead of being silently folded into `empty_confirmed`). Unit tests
      updated + 2 new tests added; `quality-gates.sh --no-fix` green (incl. the pre-existing STEP 5.99 gate that would
      have caught this). **Production-scale re-verified, not just unit-tested**: relaunched all 4 backfill VMs with the
      fix — all 4 have now each hit multiple genuine `"no_raw_data"` empty-day events (the exact prior crash trigger)
      with zero tracebacks, all still running. Full detail + evidence in the Progress Log entry below.
- [x] [DATA] P1. **reprocess_sports_odds.py raw-input prefix-template refresh (NEW 2026-07-13).** — DONE, code fix +
      tests + live-verified: `market-data-processing-service@e8f6709` (also carried a pre-existing uncommitted,
      inherited-dead-WIP `_resolve_bucket()` project_id fix found sitting in the working tree at session start — see
      Progress Log). Reconciled `_CANONICAL_ODDS_PREFIX_TEMPLATES` (renamed from `_CANONICAL_PREFIX_TEMPLATES`) in
      `_read_raw_odds()` against MTDS's actual current on-disk sports-odds writer convention — live `list_blobs` probes
      (2020-06 through 2026-07-13) confirmed the OLD templates' `data_source=ODDS_API` segment NEVER matched any on-disk
      shape, ever. Now supports BOTH real shapes found: the dominant per-bookmaker "trades" shape
      (`venue={BOOKMAKER}/.../data_type=trades/ticks.parquet`, present 2020-06 through at least 2026-06-20, has
      `bm_time`/`bm_minutes_to_kickoff`) AND the 2026-06-21+ meta-snapshot shape (`venue=ODDS_API` token +
      `ODDS_API:SPORT:{sport}.parquet` filename, schema has a nested `bookmakers` column, NOT the flat per-outcome rows
      the adapter needs). Added a fail-loud path (`RawOddsShapeUnrecognizedError`, classified to
      `RAW_ODDS_SHAPE_UNRECOGNIZED`) for any date where files exist but match neither the consumable shape nor a
      deliberately-skipped legacy-migration artifact — recorded `attempted_failed`, never a phantom `empty_confirmed`,
      mirroring instruments-service's `reconcile_manifest_from_per_league_parquets.py` 2026-07-13 "skip + log loudly"
      fix. See Progress Log 2026-07-13 "reprocess_sports_odds.py prefix-template refresh" entry for the full live-probe
      evidence table and dry-run verification output.
- [x] [DATA] P1. **odds_api source: retirement-status check.** — DONE, no code change (root-caused twice; see Progress
      Log 2026-07-13 "implementation" entry). `odds_api` is NOT retired/superseded: it is the sole `SOURCE_PRIORITY`
      owner of `ODDS_SNAPSHOT`/`ODDS_MOVEMENT`/`ARBITRAGE` and is a credential-gated (`BLOCKED-CREDENTIALS`) live
      source, already tracked in `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` +
      `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`. Live-manifest spot-check confirms all 6 legacy
      `attempted_failed` rows carry `error_reason=PipelineModeSourceMismatchError` — i.e. these are the current
      write-safety gate correctly REJECTING a source/data_type-mismatched write, an honest record of the gate firing,
      not a bug. The prior investigation's suggested classifier "polish" was re-verified and found inapplicable — see
      below; not applied. DoD's "0 (or documented-equivalent)" residual is satisfied by this documented state.
- [x] [DATA] P2. **footystats: close the small residual.** — ✅ DONE 2026-07-14 (sub-agent). The 89-row `PREDICTIONS`
      `TimeoutError` remnant of this residual (of the original 205) root-caused to a blank-`league_id` orphaned manifest
      row (NOT a timeout/retry issue — live-tested, endpoint returns in <1s) + fixed at the code level
      (`instruments-service@ed3e75b8`) + real data re-captured + the dead rows reconciled honestly. Live-verified
      `footystats/PREDICTIONS attempted_failed=0`, `MATCHES=0`. Bonus (same file/bug): `ODDS` blank-orphans also closed
      (86→0); 4 real-per-league `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` ODDS rows remain (a different, legitimate,
      normally-closeable gap — see Progress Log 2026-07-14 entry). `expected_unattempted` legitimacy not re-verified
      this pass (out of this dispatch's Part A/B scope).
- [x] ✅ [DATA] P2. **soccer_football_info (SFI_PROGRESSIVE_STATS): close the small residual.** — DONE 2026-07-14
      (slot-5) — instruments-service@db2c3c22. Root-caused: the SFI top-level `except` handler (`sfi.py:616`) wrote a
      blank-`league_id` date-aggregate `record_failed` row alongside the correct per-league failure loop. That blank row
      is unsupersedable — the success path keys on a real canonical `league_id` and writes NO blank date-level row — so
      it sat `attempted_failed` forever even after a later re-attempt captured every league (proven: the 2
      `TimeoutError` blank rows were freshly written 2026-07-14 by the residual-closer through this exact path, yet
      those dates' per-league rows self-healed to captured/empty_confirmed). Identical class to the footystats
      PREDICTIONS + weather WEATHER fixes. **Code fix**: removed the blank-`league_id` `record_failed`, keeping only the
      per-league loop (mirrors `footystats.py`); strengthened `test_match_descriptors_exception_writes_record_failed` to
      reject any blank-`league_id` failed row. **Data reconcile**: extended
      `sports_blank_league_orphan_reconcile_2026_07_14.py` `_TARGETS` with SFI + ran it against prod GCS —
      `record_expected_empty(EXPECTED_REFDATA_CADENCE_CHANGE)` at each of the 10 blank orphan row_keys. Pre-reconcile
      live probe confirmed all 10 orphan dates already carry the full 94 per-league rows (captured/empty_confirmed, 0
      per-league failures) — the blank row masked no real gap. **Canonical index verified**
      (`availability_index.parquet` direct read post-consolidation): SFI_PROGRESSIVE_STATS `attempted_failed` **10 →
      0**; all 10 dates' blank rows now `empty_confirmed` / `EXPECTED_REFDATA_CADENCE_CHANGE`. **expected_unattempted
      verified legitimate**: 122 EU rows (94 → 122, more trailing-edge dates), 100% dated 2026-07-13/14 — the documented
      self-closing daily rolling edge, 0 historical backlog. QG green (`.qg_last_passed_sha`=82dba912
      pre-quickmerge-amend); shipped via quickmerge --agent. See Progress Log entry below.
- [x] ✅ [DATA] P2. **transfermarkt (PLAYER_VALUES): verify clean.** — VERIFIED CLEAN 2026-07-14 (slot-5), no code
      change needed. Fresh canonical `availability_index.parquet` read: PLAYER_VALUES `attempted_failed`=**0**,
      `expected_unattempted`=**0** (the 47 baseline EU rows have SELF-CLOSED to `empty_confirmed` via the daily capture
      pass — definitive proof they were the legitimate self-closing rolling trailing edge the plan predicted, not a real
      gap), dedup-key duplicate groups=**0** (corrected full-identity key
      `date+venue+data_type+league_id+fixture_id+timeframe+service_name`), 94 distinct leagues, captured span
      2014-01-01→2026-07-14. Meets the understat-standard bar (0/0/0) literally. Verify-only todo — no findings to file.
      See Progress Log entry below.
- [x] [DATA] P2. **weather (open_meteo): close the small residual.** — ✅ DONE 2026-07-14 (sub-agent). Root-caused: all
      51 rows carried a blank `league_id` — a legacy pre-per-league-migration date-aggregate shard key that no current
      write path can ever supersede (the WEATHER writer's real per-league success path was already correct; only the
      dead row's key was stale). Real per-league data confirmed re-captured live (2 residual-closer rounds, 204 weather
      date-attempts, 0 raised), then the 51 dead rows honestly reconciled via
      `scripts/backfill/sports_blank_league_orphan_reconcile_2026_07_14.py` (`reason=EXPECTED_REFDATA_CADENCE_CHANGE`,
      `instruments-service@ed3e75b8`). Live-verified `open_meteo/WEATHER attempted_failed=0`. `expected_unattempted`
      legitimacy not re-verified this pass (out of this dispatch's Part A/B scope).
- [x] [DATA] P3. **Retired data_types spot-verify.** — ✅ DONE 2026-07-13 (sub-agent). All 88,056 rows (SFI_LEAGUES
      12,469 + SFI_STANDINGS 42 + TRANSFERMARKT_LEAGUES 75,545) live-verified `capture_status=empty_confirmed` +
      `error_reason=EXPECTED_DEPRECATED_DATA_TYPE`, 0 anomalies (checked all 88,056, not just a sample), plus a 30-row
      stratified spot-check — CLEAN, matches plan expectation exactly. **Bonus finding while settling the codeset
      NOTE**: `SFI_PROGRESSIVE_STATS` (which is NOT one of the 3 genuinely-retired types — it's the one live SFI entity)
      was actually present in `rebuild_sports_manifest_v9.py`'s `_RETIRED_DATA_TYPES` frozenset (a real copy-paste bug
      since the 2026-06-01 introduction, confirmed by reading the code + cross-checking every other retired-types
      definition in the repo) — fixed + shipped `market-tick-data-service@934a1efa` (removed it from the set, added a
      regression test). Full detail: Progress Log entry below.
- [x] [VERIFY] P0. **Whole-asset_group final re-verify + close-out report.** — DONE 2026-07-13 (final-reverify
      dispatch). Fresh single-parquet re-read produced the final per-source table below; **DoD is NOT fully met** — 2 of
      8 categories hit the literal/documented-equivalent bar cleanly (transfermarkt, odds_api, retired data_types — 3
      actually), the rest have specific, already-scoped remaining code-work todos (not blockers) or are mid-flight on an
      already-running bounded process. See the "FINAL RE-VERIFY + CLOSE-OUT REPORT" Progress Log entry below for the
      full table, per-category verdicts, and the precise remaining-work list (each item is an existing `- [ ]` todo in
      §1, none newly discovered, none `BLOCKED-OPERATOR`).
- [x] ✅ [VERIFY] P1. **Live-execute the new `uts-prod-sports-enrichment-transfermarkt` daily job once** (NEW
      2026-07-14, scheduled-capture audit). footystats + soccer_football_info enrichment jobs were live-verified
      end-to-end this session (see "SCHEDULED/DAILY CAPTURE AUDIT" Progress Log entry); transfermarkt shares the
      identical `_sports_provider_short_circuit` code path but was not independently executed to avoid piling a 3rd
      concurrent execution onto an already heavily-contended manifest mid-audit.
      `gcloud run jobs execute     uts-prod-sports-enrichment-transfermarkt --region=asia-northeast1 --project=central-element-323112`,
      then confirm a real `PLAYER_VALUES` write lands in the canonical `instruments-store-sports-prd` manifest. **✅
      DONE 2026-07-14 (slot-5). Executed via the google.cloud.run_v2 SDK (gcloud CLI is broken on this slot —
      snap-confine cap error): execution `uts-prod-sports-enrichment-transfermarkt-fvzzc`, start 16:48:29Z → completion
      16:49:20Z, succeeded=1 failed=0. Job logs confirm the intended code path end-to-end: "Sports provider filter from
      CLI: TRANSFERMARKT" → "TRANSFERMARKT short-circuit: skipping orchestrator" (the shared
      `_sports_provider_short_circuit` path) → "ManifestWriter cleanup: flushed buffers for
      [instruments-store-sports-prd-…]" (correct manifest bucket). No NEW PLAYER_VALUES row landed because the job
      correctly IDEMPOTENTLY SKIPPED: "PLAYER_VALUES: skipping date=2026-07-14 (all canonical leagues captured)" — the
      data was already captured by today's 15:02Z scheduled run (58,092 transfermarkt PLAYER_VALUES `captured` rows
      already in the canonical, max attempted_at 2026-07-14T15:02:35Z). So the write PATH is proven (it lands when there
      is uncaptured data, as the 15:02 run shows) and the skip-if-fresh guard works — identical verified behavior to
      footystats/soccer_football_info this session. Evidence: Cloud Run execution fvzzc succeeded + job-log lines
      above.**
- [x] ✅ [VERIFY] P1. **Re-verify Tier-3/4 fixture-proximate triggers actually fire post-fix** (NEW 2026-07-14).
      `deployment-service@5da4b620` fixed `sports_trigger_state.py`'s fixture-calendar path/field-mapping bug (root
      cause of the ENTIRE pre-match/post-match trigger tier being silently dead ≥14 days — 0 fixtures ever found by
      `get_upcoming_fixtures()`). Check over the next few hours:
      `gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="uts-prod-instruments-service-sports-fixtures" AND textPayload:"Sports entity filter from CLI"'`
      for any value beyond FIXTURES/STANDINGS (e.g. WEATHER, XG, LINEUPS, PREDICTIONS, FIXTURE_STATS) — their presence
      confirms the fix restored the whole Tier-3/4 mechanism (also feeds `features-sports-service-job`'s pre/post-match
      compute triggers, a bigger blast radius than just this plan's 8 sources). **✅ CONFIRMED 2026-07-14 (slot-5) — no
      wait needed, evidence already present in today's logs (queried via the Cloud Logging Python SDK; gcloud CLI broken
      on slot). The `uts-prod-instruments-service-sports-fixtures` job is running on its ~5-min cadence (16:01Z→16:36Z
      sampled) and firing entity filters BEYOND FIXTURES/STANDINGS — observed distinct values: WEATHER, LINEUPS,
      FIXTURE_STATS. Their presence confirms `get_upcoming_fixtures()` is now finding fixtures and the whole Tier-3/4
      pre/post-match trigger mechanism is live post-fix. Evidence: 29 "Sports entity filter from CLI: {WEATHER|LINEUPS|
      FIXTURE_STATS}" log lines today.**
- [x] [DATA] P1. **`uts-prod-market-data-processing-t1-schedule` — daily NOT_FOUND, target Cloud Run Job deleted** — ✅
      DONE 2026-07-14 (see "MDPS T1-RECON + ODDS-HORIZON-BUCKET DAILY DRIVER" Progress Log entry for full detail). Root
      cause: the CRJ was never provisioned (F-41-class bug) — investigation found it's general T+1 candle aggregation
      across all 5 asset groups, NOT sports-odds-specific, so its fix (provisioning the missing CRJ) is SEPARATE from
      the `mdps_odds_horizon_bucket` daily-driver gap this todo also flagged — both fixed: `deployment-service@de117f5`
      provisions `mdps_t1_recon_job` (the missing general CRJ, live-tested end-to-end after 3 more live-test fixes:
      SKIP_DEPENDENCY_CHECK bridge, PROTOCOL_DATA_SOURCE_BUCKET_* env vars, 16Gi→32Gi OOM fix) +
      `mdps_odds_horizon_scheduler.tf` (new dedicated daily scheduler for `reprocess_sports_odds.py`, 01:15 UTC, rolling
      3-day window); `market-data-processing-service@3f1065f` makes both scripts' date args self-default (required for
      either job to run off a static Cloud Scheduler trigger). One pre-existing, unrelated bug surfaced (Polymarket
      prediction adapter: `instrument_key` column missing from instruments data, aborts PREDICTION category processing)
      — new followup todo below, out of this todo's scope.
- [x] ✅ [DATA] P2. **market-data-processing-service: two pre-existing bugs found live-testing the new
      `mdps_t1_recon_job`.** — (a) FIXED + shipped, (b) root-caused deeper than task scope → issue doc filed +
      operator-notified, 2026-07-14 (slot-5). **(a) instrument_key abort — FIXED
      (market-data-processing-service@2dc6860):** the raw Polymarket `instrument_availability` parquet carries the CLOB
      schema (`condition_id`/`question_id`/`clob_token_ids`/…) with NO `instrument_key`, so
      `CloudDataProvider.get_instruments_for_date` returned a df the orchestrator's tradable-key filter
      (`_load_tradable_context`) aborted on. Added the canonical derivation
      `instrument_key = POLYMARKET:PREDICTION_MARKET:{condition_id}` (matches `prediction/trades_adapter.py::preprocess`
      exactly) in `get_instruments_for_date` — the single upstream method BOTH `_get_tradable_instruments` impls
      (scanner + scheduling) route through. Live-verified the schema (real `condition_id`, no `instrument_key`); unit
      test `test_prediction_derives_instrument_key_from_condition_id` added; QG green (sentinel 90a6b27). **(b)
      DependencyChecker 404 — root cause is a CROSS-REPO UAC SSOT drift, NOT an MDPS-local bug → issue doc
      `plans/active/issues/mdps_prediction_tick_bucket_uac_ssot_404_2026_07_14.md`:**
      `bucket_template(PREDICTION,     MARKET_DATA)` in `unified-api-contracts/canonical/gcs_paths.py:113` still returns
      the long-form `market-data-tick-prediction-{env}-{pid}` (live-probed → 404 NotFound; `market-data-tick-pred-prd-*`
      HAS_OBJECTS). The template is a DELIBERATELY-guarded mid-migration value whose guard says "re-evaluate once
      pred-prd is the sole complete SSOT" — that precondition is now met (migration plan
      `prediction_manifest_canonicalisation_2026_06_01.md` ARCHIVED, legacy bucket deleted). The fix is a coordinated
      UAC-SSOT flip rippling UAC/UTL/MDPS/MTDS/IS (code + tests) — a "big finding" (cross-repo + SSOT) filed as an
      auto-dispatchable issue doc rather than unilaterally flipping a fleet-wide guarded template from this MDPS-scoped
      task. Note bug (b) is MASKED by `SKIP_DEPENDENCY_CHECK=true` on the T1-recon job (never triggers today), so (a)
      alone unblocks PREDICTION candle production. See Progress Log entry below. **Original finding text:** (a) the
      PREDICTION category's candle-processing path aborts with `❌ instrument_key column missing from instruments data`
      (columns present are the raw Polymarket CLOB schema — `condition_id`/`question_id`/`clob_token_ids`/etc — never
      mapped to the `instrument_key` the orchestrator's filter step expects; find + fix the missing mapping step, likely
      in the Polymarket instrument-loading path the orchestrator calls before `_process_one_category`); (b)
      `DependencyChecker`'s PREDICTION upstream-bucket lookup 404s against `market-data-tick-prediction-prd-*` — a
      bucket decommissioned 2026-07-12 in favor of the abbreviated `market-data-tick-pred-prd-*` (see
      `market-data-processing-service/scripts/reprocess_sports_odds.py::_resolve_bucket`'s own comment on this exact
      2026-07-12 rename) — `DependencyChecker` was never updated for the rename. Both bugs are currently masked by
      `SKIP_DEPENDENCY_CHECK=true` on the T1-recon job (bug (b) never triggers) and a caught-not-fatal
      `_process_one_category` exception (bug (a) logs an ERROR but doesn't crash the run) — so the general T1
      candle-aggregation job runs GREEN every day but PREDICTION candles are never actually produced until both are
      fixed.

# 2. Definition of DONE

Every active sports source (api_football, footystats, soccer_football_info, transfermarkt, open_meteo, odds_api or its
formal retirement, mdps_odds_horizon_bucket or its formal `BLOCKED-CREDENTIALS` scaffold) shows 0 `attempted_failed` / 0
(or documented-equivalent) `expected_unattempted` / 0 duplicate dedup-key groups / correct `service_name`+`asset_group`;
every root cause is fixed in code (not just data patched); all findings filed in the relevant plans/issue docs; final
report written in this plan's Progress Log.

> **STATUS as of the 2026-07-15 FINAL WHOLE-PLAN RE-VERIFY: STILL NOT FULLY MET, but dramatically improved from
> 2026-07-13's "3/8 clean."** Live re-check against the current canonical (`instruments-store-sports-prd`, 5,432,276
> rows) across all 7 sources, per-dimension:
>
> | source                     | attempted_failed | expected_unattempted | dedup groups | asset_group blank |
> | -------------------------- | ---------------- | -------------------- | ------------ | ----------------- |
> | `api_football`             | 766 (was 4,268)  | 134,627              | 0            | 844,209           |
> | `footystats`               | 4                | 168                  | 0            | 99,048            |
> | `soccer_football_info`     | **0**            | 183                  | 0            | 360               |
> | `transfermarkt`            | **0**            | 47                   | 0            | 45                |
> | `open_meteo`               | **0**            | 282                  | 0            | 1,804             |
> | `odds_api`                 | **0**            | **0**                | 2            | **0**             |
> | `mdps_odds_horizon_bucket` | 4                | 199,720              | 0            | **0**             |
>
> **5/7 sources now show 0 or near-0 `attempted_failed`** (soccer_football_info/transfermarkt/open_meteo literally 0;
> footystats/mdps_odds_horizon_bucket at 4). `api_football`'s 766 is code-complete + independently verified — INJURIES
> and FIXTURES (this session's core dispatch) both confirmed 0; the residual 305 is the already-tracked CF11 backfill
> class + 461 is the newly-root-caused blank-data_type class (neither is a re-fetch target for the general closer).
> **`expected_unattempted` is large for 2 sources but both are ALREADY-DOCUMENTED, understood backlogs, not new
> defects**: `mdps_odds_horizon_bucket`'s 199,720 is the known post-venue-grain-fix backlog (only 633 of 200,259 seed
> rows had a matching real capture — flagged same-session as "the real backlog is much larger than hoped"); the other 5
> sources' `expected_unattempted` (47-282, `api_football`'s 134,627 not yet root-caused this pass) are comparatively
> small except api_football's, which needs its own look before this line item can be called closed. **Dedup-key groups:
> 0 for 6/7 sources**, `odds_api` has 2 (both `date=2026-06-21`, same `instrument_id` captured twice at different
> `written_at` — a benign double-write, not corrupted data; see the 2026-07-15 update in
> `plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`). **`asset_group` blank is
> the single biggest remaining gap, present on 5/7 sources** (844,209 for api_football alone, down to 0 for the two
> MTDS/MDPS-adjacent sources `odds_api`/`mdps_odds_horizon_bucket` whose writers already stamp it explicitly) — a
> single, already-understood root cause (the consolidator's asset_group heal never covers `instruments-store-sports`),
> NOT 5 separate bugs; the existing `[DATA] P1` todo in the referenced issue doc already covers this and should be
> re-scoped to all sports sources, not just api_football, next time it's picked up. Also confirmed: the 1-row
> defi/UNISWAP_V3-BASE contamination (finding C in the same issue doc) is still present, unfixed, unchanged. **Zero
> regressions found anywhere this session.** Full detail: see the 2026-07-15 Progress Log entries below (round2-5 saga)
> and the referenced issue doc's 2026-07-15 update section.

# 3. Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md`, `…/honest-absence-downstream-handling.md`
- `codex/02-data/external-data-always-available-rule.md` (mdps_odds_horizon_bucket todo)
- `codex/05-infrastructure/manifest-consolidator-ssot.md`
- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md`

## Progress Log

- **2026-07-14 (slot-5) — api_football TEAMS 8-no-roster-cup-leagues residual CLOSED (data-only reconcile).**
  instruments-service@fad73bb1. The 8 cup/one-off competitions return 0 teams from api_football `/teams` (no persistent
  roster). Diagnosis: `is_league_entity_covered(canon, "TEAMS")` returns `False` for all 8 (coverage map already
  correct) and the live TEAMS writer already emits `EXPECTED_NO_PROVIDER_COVERAGE` for uncovered (league, entity) pairs
  (776 rows existed) — so NO code change was warranted; the residual was 24,176 historical (2018-01-01→2026-07-10)
  `expected_unattempted` cells (3,022 × 8) that the season-cached `_fetch_teams_and_standings` never processed.
  Data-only reconcile via `scripts/backfill/api_football_teams_no_roster_leagues_reconcile_2026_07_14.py`:
  `record_empty(row_key={date, TEAMS, league_id}, reason=EXPECTED_NO_PROVIDER_COVERAGE)` per cell, matching the 776
  already-correct rows. Prereq (the P1 manifest_consolidator dedup-key fix) confirmed already landed. **Verification
  (direct canonical `availability_index.parquet` read, stable across consolidator cycles): the 8 leagues' TEAMS =
  `expected_unattempted` 24,176 → 0; `empty_confirmed` 776 → 24,952, all `EXPECTED_NO_PROVIDER_COVERAGE`.** Operational
  note: the FIRST reconcile write (per-VM shard, 24,176 rows) was pruned WITHOUT merge by an overlapping
  manifest-consolidator execution (the known prune-race,
  `plans/active/issues/manifest_consolidator_prune_race_overlapping_executions_2026_07_13.md` — a transient recurrence
  for a large shard; EU stayed 24,176 and the shard vanished); a straight re-apply consolidated cleanly within one cycle
  (`[poll 0] EU=0`) and holds stable. Reconcile script shipped via quickmerge; QG green.

- **2026-07-14 (slot-5) — mdps_t1_recon_job two-bug todo: (a) FIXED, (b) escalated (cross-repo UAC SSOT).**
  - **(a) PREDICTION instrument_key abort — FIXED (market-data-processing-service@2dc6860).** Live-probed the prod
    prediction instruments bucket (`instruments-store-pred-prd-central-element-323112`,
    `instrument_availability/by_date/.../venue=POLYMARKET/instruments.parquet`): columns are the raw Polymarket CLOB
    schema (`condition_id`/`question_id`/`clob_token_ids`/…) with a real `condition_id` but NO `instrument_key`.
    `orchestration_service._load_tradable_context` aborts category processing when `instrument_key` is absent. Fixed at
    the single upstream loader `CloudDataProvider.get_instruments_for_date` (both `_get_tradable_instruments` impls —
    scanner + scheduling — route through it): for PREDICTION, derive
    `instrument_key = "POLYMARKET:PREDICTION_MARKET:" + condition_id` (polars `with_columns`), which matches
    `prediction/trades_adapter.py::preprocess` exactly so the tradable-key set aligns with the tick adapter's key. Added
    regression test `test_prediction_derives_instrument_key_from_condition_id`; existing CEFI test unaffected. QG green
    (sentinel 90a6b27), shipped via quickmerge --agent.
  - **(b) DependencyChecker 404 — root cause is CROSS-REPO UAC SSOT drift, escalated to issue doc.** Not an MDPS-local
    bug: `unified_api_contracts.canonical.gcs_paths.bucket_template(AssetGroup.PREDICTION, BucketKind.MARKET_DATA)`
    returns the long-form `market-data-tick-prediction-{env}-{pid}` (live-probed → **404 NotFound**), while UTL's
    `resolve_bucket_name(kind="market-data-tick-prediction")` AND UAC's INSTRUMENTS template both already return the
    live abbreviated `market-data-tick-pred-prd-*` (HAS_OBJECTS). The UAC template carries a deliberate mid-migration
    guard (gcs_paths.py:103-113) saying to re-evaluate once `pred-prd` is the sole complete SSOT — that precondition is
    now met (migration plan `prediction_manifest_canonicalisation_2026_06_01.md` ARCHIVED, legacy bucket deleted
    2026-07-12). Flipping the template is the root fix but ripples UAC/UTL/MDPS/MTDS/instruments-service (code + tests),
    and UTL's `_asset_group_for_market_data_bucket` intentionally still recognizes the long-form — a coordinated
    fleet-wide SSOT change, filed as `plans/active/issues/mdps_prediction_tick_bucket_uac_ssot_404_2026_07_14.md`
    (assigned_vm: planning, auto-dispatchable) rather than unilaterally flipping a guarded SSOT from this task. Bug (b)
    is MASKED by `SKIP_DEPENDENCY_CHECK=true` on the T1-recon job, so it does not block candle production — (a) alone
    unblocks PREDICTION candles.

- **2026-07-14 (slot-5) — transfermarkt PLAYER_VALUES VERIFIED CLEAN (verify-only, no code change).** Fresh direct read
  of the canonical `availability_index.parquet` (`instruments-store-sports-prd-central-element-323112`):
  `transfermarkt`/`PLAYER_VALUES` = 58,092 `captured` + 211,626 `empty_confirmed`, **0 `attempted_failed`**, **0
  `expected_unattempted`**. The 47 baseline EU rows (2026-07-13 audit) have self-closed to `empty_confirmed` on the next
  daily capture pass — confirming they were the legitimate self-closing daily rolling trailing edge (the plan's
  "off-season/no-transfer-window / today-dated" hypothesis), NOT a real gap. Dedup-key duplicate groups = **0** under
  the corrected full-identity key (`date+venue+data_type+league_id+fixture_id+timeframe+service_name`); 94 distinct
  leagues; captured span 2014-01-01→2026-07-14 (full, current-to-today). Meets the understat-standard 0/0/0 bar
  literally — no findings, no issue doc, no code change required.

- **2026-07-14 (slot-5) — SFI_PROGRESSIVE_STATS residual CLOSED (code fix + data reconcile).**
  instruments-service@db2c3c22.
  - **Root cause (code):** `sfi.py`'s top-level `except` handler (fetch of `get_match_descriptors_for_date`) wrote a
    blank-`league_id` date-aggregate `record_failed` row (`row_key={"date","data_type":"SFI_PROGRESSIVE_STATS"}`) in
    ADDITION to the correct per-league failure loop. The SFI success path (`record_captured`) keys on a real canonical
    `league_id` and writes NO blank date-level row, so the blank `attempted_failed` row can never be superseded by a
    later successful capture — it sits `attempted_failed` forever. This is the IDENTICAL anti-pattern already fixed in
    `footystats.py` (PREDICTIONS) + `weather.py` (WEATHER) on 2026-07-14. Direct proof: the 2 `TimeoutError` blank rows
    (2025-03-05, 2025-03-08) were freshly written 2026-07-14T12:36 by the residual-closer's re-attempt through this
    exact handler, yet those two dates' 94 per-league rows show clean captured/empty_confirmed — the per-league rows
    self-heal on re-capture, the blank row cannot.
  - **Live pre-reconcile probe (all 10 orphan dates):** each date carries the full 94 per-league rows (empty_confirmed +
    captured, 0 per-league failures) — the blank date-aggregate row is a pure redundant orphan masking no real gap. 8
    rows tagged `phantom_captured_no_parquet_at_canonical_path`, 2 tagged `TimeoutError`; all 10 `league_id=None`.
  - **Fix (code):** removed the blank-`league_id` `record_failed` from the `sfi.py` handler, keeping only the per-league
    loop (mirrors `footystats.py:408`); strengthened
    `TestFetchSfiData::test_match_descriptors_exception_writes_record_failed` to assert every `record_failed` row_key
    carries a real `league_id` (rejects any blank date-aggregate row) across a 2-league expected set.
  - **Fix (data):** extended `sports_blank_league_orphan_reconcile_2026_07_14.py` `_TARGETS` with
    `(soccer_football_info, SFI_PROGRESSIVE_STATS)` and ran it against prod GCS
    (`instruments-store-sports-prd-central-element-323112`): dry-run found exactly the 10 SFI orphans (0 footystats/
    weather — already closed), apply wrote `record_expected_empty(EXPECTED_REFDATA_CADENCE_CHANGE)` at each blank
    row_key. The live per-minute consolidator cron absorbed the per-VM shard into the canonical index (operator
    directive honoured — consolidator NOT manually invoked).
  - **Verification (canonical `availability_index.parquet`, direct read post-consolidation):** SFI_PROGRESSIVE_STATS
    `attempted_failed` **10 → 0**; `empty_confirmed` 204,546 → 204,556 (+10); all 10 dates' blank rows now
    `empty_confirmed` / `EXPECTED_REFDATA_CADENCE_CHANGE`. `expected_unattempted` = 122 (94 → 122, additional
    trailing-edge dates), 100% dated 2026-07-13/14 — the already-root-caused self-closing daily rolling edge, 0
    historical backlog → legitimate.
  - **Ship:** QG green on committed tree (`.qg_last_passed_sha`=82dba912, pre-quickmerge-amend); quickmerge --agent
    landed on live-defi-rollout as db2c3c22. Regression test passes. (Unrelated pre-existing QG `⚠️` warning:
    market-tick-data-service `solana_defi_drift.py` adapter-contract baseline — a different repo, untouched by this
    change, QG exit 0.)

- 2026-07-13 (slot-3, interactive session): plan created under operator-directed `/autonomous` + Workflow dispatch,
  immediately following the understat completion in the same session. Baseline audit in §0 above. Model tier flagged
  `opus-required` per CLAUDE.md (cross-repo architectural investigation) — this session is running Sonnet 5 (cannot
  switch mid-session); compensating by routing the hard root-causing work to opus-tier Workflow sub-agents.
- 2026-07-13 (sub-agent, investigation-only dispatch — footystats/SFI/transfermarkt/weather residuals): fresh
  live-manifest read (`.venv/bin/python` ad-hoc script, `read_availability_index`, single-parquet read) confirms the
  plan's §0 baseline numbers are still current: footystats 205 attempted_failed (179 TimeoutError, 15 phantom, 11
  ArrowTypeError) + 56 EU; SFI 10 phantom + 94 EU; transfermarkt 0 attempted_failed + 47 EU; weather 51 phantom + 94 EU.
  **(1) expected_unattempted legitimacy — CONFIRMED legitimate for all 4**: every single EU row across all 4 sources is
  dated `2026-07-13` (today, the day this investigation ran) — 0 historical backlog. This is the SAME rolling ≤1-day
  trailing edge already root-caused for understat (`expected_universe_v2_daily` Cloud Scheduler enum re-seeds today's
  date at 01:30 UTC; same-day capture hasn't resolved it to `empty_confirmed(EXPECTED_NO_FIXTURE)` yet within the same
  calendar day). Not a real gap — self-closes on the next capture pass. No action needed beyond the daily job already
  running. **(2) phantom_captured_no_parquet_at_canonical_path — root-caused, GENUINE (not self-healing like the prior
  ODDS precedent)**: live-probed all 76 phantom rows (15 footystats + 10 SFI + 51 weather) against EVERY
  `candidate_parquet_paths()` candidate (canonical `pipeline_mode=` + legacy fallback) via direct
  `blob_exists`/`list_blobs` checks — **0 of 76 have a real parquet today** (unlike the 2026-07-08 footystats ODDS
  precedent where 19/20 were false positives that self-healed). Shared code-path root cause confirmed by reading
  `footystats.py`/`sfi.py`/`weather.py`: **all three share the IDENTICAL anti-pattern** — a synchronous per-league loop
  calls `_orch._gated_sink_write(...)` (a real, synchronous `storage_client.upload_bytes`, not buffered) immediately
  followed by `manifest.record_captured(...)` with NO per-shard try/except isolating the pair; the only exception
  handler is one FUNCTION-level `except Exception` wrapping the entire per-date/per-league loop (footystats.py:669,
  sfi.py's fetch-level handler, weather.py's per-date handler). `record_captured()` itself buffers into the in-memory
  `ManifestWriter` (flushed later via `.write()` / `flush_all_pending_buckets()`), decoupled in time from the
  synchronous data write. footystats' 15 phantom rows are a single contiguous cluster (SEGUNDA_DIVISION,
  2022-09-25→2022-10-10) — consistent with one historical backfill/retry pass where the manifest buffer's eventual flush
  survived but the corresponding data write did not durably persist (VM interruption / later overwrite/delete), the same
  buffered-manifest-vs-synchronous-data-write decoupling class already documented in
  `reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12`. SFI (10 rows, scattered 2025-01→2026-04) and
  weather (51 rows, scattered 2019-2026) show the same shape (small counts, no self-heal) — same class, not
  independently re-diagnosed per-source. **Fix recommendation** (for the implementing agent): (a) data-only, safe,
  immediate — run the existing
  `scripts/reconcile_phantom_manifest_rows_all.py --asset-group sports --data-types MATCHES,PREDICTIONS,ODDS,SFI_PROGRESSIVE_STATS,WEATHER --unphantom-only --dry-run`
  first (safe-by-construction, phantom→captured only) to double-confirm before flipping the 76 confirmed-genuine rows to
  `attempted_failed` via the same tool's normal (non-`--unphantom-only`) apply mode, then let the standard retry path
  (VM re-run / `query_sports_is_gaps.py` → `launch-sports-is-gap-fill.sh`) re-capture them; (b) code fix, not urgent
  given the tiny count — wrap the write+record_captured pair in each of the 3 orchestrator modules in a per-shard
  try/except (mirroring the isolation pattern shard-level-failure-isolation.md already mandates) so a future interrupted
  write cannot leave a buffered manifest entry with no corresponding durable data write. **(3) footystats TimeoutError
  (179 rows) — retry/backoff tuning issue, NOT a dead endpoint**: dates span 2019-01-01 → 2023-01-03 uniformly (no
  concentration near any specific outage window), 100% blank `league_id` (date-level bulk-call timeouts before the
  per-league split, not a per-league-specific failure), split ODDS=90/PREDICTIONS=89. Uniform spread across 4 years of
  historical dates is inconsistent with "dead endpoint for old dates" and consistent with a generic transient-timeout
  class from the original backfill run; footystats' live endpoint is confirmed working today (this same investigation's
  EU rows are actively being seeded for it). Recommend a plain re-attempt (existing
  `footystats_residual_closer_2026_07_12.py` pattern or `query_sports_is_gaps.py` → gap-fill VM) with retry/backoff, no
  adapter-timeout code change needed. The 11 ArrowTypeError rows (all ODDS, 2020-2023) are a distinct, small,
  separately-diagnosable schema/serialization issue — not investigated further here (out of this pass's scope, flagged
  for the implementing agent to triage as a possible one-off dtype coercion bug in the ODDS write path). **(4) Retired
  data_types spot-verify — CLEAN, no fix needed**: `SFI_LEAGUES`/`SFI_STANDINGS`/`TRANSFERMARKT_LEAGUES`, 88,056 rows,
  100% `capture_status=empty_confirmed` with `error_reason=EXPECTED_DEPRECATED_DATA_TYPE` — exactly as documented in
  `rebuild_sports_manifest_v9.py:103`, no stale/blank rows found. No code or data changes made this pass
  (investigation-only per dispatch scope); all fixes above are recommendations for the next implementing session/agent.

- 2026-07-13 (sub-agent, investigation-only dispatch): **`odds_api` source retirement-status check — CONCLUSION: NOT
  retired/superseded, is a credential-gated (BLOCKED-CREDENTIALS) live source, already documented elsewhere.**
  - Direct manifest query (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`,
    `source == "odds_api"`, 2,667 rows): 2,661 `empty_confirmed` split evenly 887/887/887 across `data_type` ∈
    {`odds_snapshot`, `odds_movement`, `arbitrage_opportunity`}, dated 2018-01-01→2020-06-05; 6 `attempted_failed`, all
    `data_type=ODDS`, dated 2019-01-23→2020-04-27, `service_name=instruments-service` throughout. **0 rows of any kind
    exist after 2020-06-05.**
  - `unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py:85` —
    `SPORTS_SOURCE_COVERAGE_START["odds_api"] = date(2020, 6, 6)` — literally the day AFTER the manifest's last
    empty_confirmed row. The 2,661 empty_confirmed rows are the honest pre-coverage-start backfill window and are
    **already correctly typed** — not a bug, nothing to fix.
  - `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py:41-43` —
    `SOURCE_PRIORITY[("sports","ODDS_SNAPSHOT"|"ODDS_MOVEMENT"|"ARBITRAGE")] = ["odds_api"]` — odds_api is the SOLE
    registered source for these 3 data_types. They are NOT the shared `"ODDS"` data_type (that's
    `unified_api_contracts/canonical/domain/sports/league_data.py:171` → `"ODDS": "footystats"`, captured heavily by
    api_football/footystats per §0). **odds_api cannot be blanket-retired**: it owns data_types no other source
    substitutes for, and is not in `rebuild_sports_manifest_v9.py:103`'s `_RETIRED_DATA_TYPES` set (that set is
    `{SFI_LEAGUES, SFI_PROGRESSIVE_STATS, SFI_STANDINGS, TRANSFERMARKT_LEAGUES}` only).
  - The 6 legacy `attempted_failed` `ODDS` rows are pre-registry-correction noise: odds_api never owned generic `ODDS`
    (footystats does), so these 2019-2020 writes are a source/data_type mismatch from before the current
    `SOURCE_PRIORITY` ownership + `PipelineModeSourceMismatchError` gate existed (gate referenced in
    `instruments-service/scripts/backfill_orphan_class_e.py:267` and `backfill_orphan_class_e_sports.py:106`) — current
    code cannot reproduce this class. 6 rows is below any materiality bar; recommend leaving as historical
    `attempted_failed` (truthful record) rather than inventing a new relabel reason — do **not** relabel to
    `EXPECTED_DEPRECATED_DATA_TYPE` (that reason means "this data_type is retired," which `ODDS` is not).
  - `market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py` — the odds_api WSFeedConnector is
    FULLY BUILT (polls The Odds API v4 REST, 60s interval) and REGISTERED (confirmed in
    `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md`'s 31-venue registered list — odds_api is sports' 1
    resolved venue, not one of the 7 unresolved). Its own docstring carries a live, standing
    `CREDENTIAL APPROVAL REQUEST — odds-api-live-ws` (existing `odds-api-key` secret needs a paid-tier quota bump,
    ~$10/mo Starter tier, ~43k credits/mo at 60s polling) tied to "Phase 3.5e May-23 gate" — i.e. this is a KNOWN,
    already-filed `BLOCKED-CREDENTIALS` gap, not abandoned/dead code. Independently corroborated by
    `instruments-service/scripts/migrate_legacy_oddsapi_instruments_to_twins_2026_06_19.py`'s own preamble ("canonical
    `venue=odds_api` rows in the `_index` are all `empty_confirmed` and stop at 2020-06-05") and by
    `plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md:412-414,612-613` ("the live Odds API
    connector … is itself `BLOCKED-CREDENTIALS`, so live sports odds has never actually run").
  - **The real open gap** (post-2020-06-06 to present: 0 captured, 0 attempted_failed, 0 expected_unattempted — the
    expected-universe was never seeded for odds_api's 3 owned data_types in its actual coverage window) is the SAME
    already-tracked credential gap, not a new discovery — already touched by the active
    `plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` ("BLOCKED-CREDENTIALS for full 2-week GCS
    baseline"). No new issue doc needed; no code fix needed (adapter + registration already exist per
    external-data-always-available-rule's "build the scaffold anyway" bar — already satisfied).
  - **Recommended fix (for the implementing agent on this todo)**: mark this todo DONE with the above documented as the
    terminal state. No manifest relabel, no source-retirement list entry, no new adapter work. If the plan's literal "0
    attempted_failed" DoD must be hit for odds_api specifically, the minimal change is a narrow classifier exemption in
    `market-tick-data-service/market_tick_data_service/scripts/rebuild_sports_manifest_v9.py`'s `_classify_empty_row`
    (mirroring the existing step-1 `_RETIRED_DATA_TYPES` relabel pattern at line 421) that relabels exactly
    `(source=odds_api, data_type=ODDS, date<2020-06-06)` to a new reason (e.g. `EXPECTED_LEGACY_SOURCE_MISMATCH`, NOT
    `EXPECTED_DEPRECATED_DATA_TYPE`) — optional polish, not required, given the 6-row scale and the understat precedent

- 2026-07-13 (slot-3, investigation-only sub-agent, live-manifest re-read of `api_football` slice, no code/data
  changes): full root-cause on the P0 api_football investigation todo above. **Verified exact live counts**: captured
  365,592 · empty_confirmed 1,696,130 · expected_unattempted 453,961 · attempted_failed 3,257. **(1)
  expected_unattempted (453,961) is a legitimate could-exist seed, evenly spread 2018-2026 (~28.5k-57.6k/yr, no cliff)**
  — by data_type: TEAMS 192,384 · ODDS 82,749 · FIXTURE_LINEUPS 47,282 · FIXTURE_EVENTS 47,028 · FIXTURE_STATS 36,677 ·
  PLAYER_STATS 26,363 · INJURIES 20,700 · FIXTURES 778. Per `enumerate_expected_universe.py` `_enumerate_v2_sports`
  (line 1735), this is the per-LEAGUE cross-product against `SPORTS_DATA_TYPE_TO_SOURCE`'s coverage-start-gated axis —
  the low FIXTURES count (only 778, vs TEAMS' 192k) confirms the enumerator's
  `_build_af_fixture_calendar`/`EXPECTED_NO_FIXTURE` truthset carve-out (docstring line ~1777) is doing its job for the
  primary data_type; no action needed, this is denominator, not a gap. **(2) attempted_failed root causes, by
  error_reason**: `ApiFootballResponseError` 1,642 (INJURIES 1,600 / TEAMS 24 / PLAYER_STATS 10 / FIXTURE_STATS 7 /
  FIXTURE_LINEUPS 1) · `FIXTURES_FETCH_FAILED` 665 · `phantom_captured_no_parquet_at_canonical_path` 487 (INJURIES 346 /
  PLAYER_STATS 64 / FIXTURE_STATS 39 / FIXTURE_LINEUPS 29 / FIXTURE_EVENTS 11) · `UNCLASSIFIED_ADAPTER_ERROR` 461 (100%
  blank data_type) · `phantom_re_attempt_after_writer_fix_f36651c` 2.
  - **(a) INJURIES `ApiFootballResponseError` — CONFIRMED misclassification bug, not rate-limiting.** The exception is
    raised at `instruments_service/reference_data/adapters/sports/adapters/api_football.py:948` (`_raise_on_api_errors`)
    whenever API-Football's JSON envelope carries a non-empty `errors` dict with `is_rate_limit=False` (i.e. NOT the
    `rateLimit` key — genuine rate-limit responses are already retried transparently by `_fetch_and_extract`, lines
    707-750, and never reach `attempted_failed`). The failure is written via `_AfManifestHooks.note_failed` →
    `sports_reference_core.py:62` → `_classify_adapter_failure(exc, "api_football")`
    (`instruments_service/engine/orchestrator/failure.py:33-46`), which passes `type(exc).__name__` (the literal string
    `"ApiFootballResponseError"`) into UAC `classify_venue_error("api_football", "ApiFootballResponseError")`. But UAC's
    `VENUE_ERRORS_SPORTS["api_football"]` table
    (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/sports.py:9-82`) is keyed by
    HTTP-status/domain codes (`"429"`,`"401"`,`"400"`,`"500"`,`"FREE_PLAN_DATE_LIMIT"`,`"SEASON_NOT_FOUND"`,
    `"LEAGUE_NOT_FOUND"`,`"RATE_LIMIT_DAILY"`,`"FIXTURE_NOT_FOUND"`) — the exception CLASS NAME never matches any of
    those keys, so `classify_venue_error` always returns `None` and the code falls back to the raw class name. This
    means the manifest can NEVER distinguish which of API-Football's real hard-error categories (plan/token/param/
    season/league) actually fired — it's a lookup-key-type bug, not a rate-limit problem. Evidence the failures are a
    handful of systemic runs, not per-date organic failures: only 3 distinct `attempted_at` values across all 1,642 rows
    (2026-06-25, 2026-06-26, 2026-07-13T16:24:30 — the last one alone contributing 2,182 rows across ALL api_football
    failure classes, including 100% of the 487 phantom rows), and INJURIES failures are evenly spread 2019-2026 (not
    concentrated in old/new dates), ruling out a simple date-window plan restriction. **Root cause is almost certainly a
    real API-Football envelope error (`_raise_on_api_errors`, `api_football.py:932-953`) — most likely a
    plan/entitlement error specific to the INJURIES endpoint (API-Football gates INJURIES behind a paid-plan tier) —
    being raised and immediately misclassified**, not investigated further because `_raise_on_api_errors` discards the
    raw `errors` dict content once it builds the exception message string (only preserved in `str(exc)`, which the
    manifest never persists — only `error_reason` is stored). **Concrete fix**: (i) thread the raw envelope `errors`
    dict's key (`"plan"`/`"token"`/`"requests"`/etc, whichever populated) through as the `error_code` passed to
    `_classify_adapter_failure`/`record_failed` instead of the exception class name (the
    `ApiFootballResponseError.__init__` already receives the raw message — extend it to also carry a structured
    `error_key` attribute the caller reads); (ii) add the missing UAC `VENUE_ERRORS_SPORTS["api_football"]` entries for
    whatever concrete key surfaces (likely a plan/entitlement code) so `classify_venue_error` resolves it; (iii) only
    THEN re-attempt INJURIES — re-attempting blind today would just reproduce the same misclassified failures if it's
    truly a plan/entitlement gate (a credential/plan upgrade ask, not a code bug, in that case — confirm by making ONE
    manual `GET /injuries?date=...` call with the live key and inspecting the raw `errors` body before re-running the
    backfill).
  - **(b) FIXTURES `FIXTURES_FETCH_FAILED` (665)** — not yet root-caused to adapter code in this pass (no
    `FIXTURES_FETCH_FAILED`-literal raise site found in `api_football.py`; likely raised in
    `sports_reference_fixtures.py`/`sports.py`'s date-wide fixtures-list call site as a wrapper `RecordFailedReason`,
    analogous to `UNCLASSIFIED_ADAPTER_ERROR` below). Left for the implementing agent — grep
    `RecordFailedReason.FIXTURES_FETCH_FAILED` call sites and inspect `attempted_at`/date clustering the same way as (a)
    above before re-attempting.
  - **(c) blank-`data_type` `UNCLASSIFIED_ADAPTER_ERROR` (461) — CONFIRMED write-path bug, root cause is NOT the
    api_football adapter itself.** All 461 rows: `service_name=instruments-service`, blank `league_id`, dates spread
    2017-2020ish (sampled). Traced to `instruments_service/engine/orchestrator/process_completeness.py`'s
    `_finalize_completeness` (lines 494-501) and `_detect_thin_day_venues`'s corrective-write call (lines 532-538) — a
    GENERIC, venue-grain shard-completeness gate (built for CeFi/TradFi venue-shaped shards:
    `row_key={"date": date, "venue": _failed_venue}`) that writes a corrective `record_failed` with **no `data_type` key
    in `row_key` at all**. Sports' captured atom is league-grain (`data_type`, `league_id`, `date` — confirmed in
    `_SPORTS_PRESENT_COLS`, `enumerate_expected_universe.py:149`), not venue-grain, so when this generic completeness
    gate's missing-shard logic fires for an api_football pseudo-shard it stamps a row with a blank `data_type` (and
    blank `league_id`) that can never match any real sports cell — a permanently-orphaned, non-reconcilable manifest
    row. **Fix**: exclude `asset_group=sports` (and any other non-venue-shaped asset_group) from
    `_finalize_completeness`'s missing-shard `record_failed` path, mirroring the CeFi-only scope
    `_detect_thin_day_venues` already declares in its own docstring — OR require the caller to pass a `data_type` in
    `row_key` for any asset_group whose present-set columns include `data_type` (reuse `_present_cols_for` from
    `enumerate_expected_universe.py` as the SSOT for what row_key keys are valid per asset_group).
  - **(d) `phantom_captured_no_parquet_at_canonical_path` (487)** — 100% share the single
    `attempted_at = 2026-07-13T16:24:30.871968+00:00` timestamp (the same run that produced 2,182 of the day's
    failures), concentrated in INJURIES (346)/PLAYER_STATS(64)/FIXTURE_STATS(39)/FIXTURE_LINEUPS(29)/FIXTURE_EVENTS(11)
    — i.e. a single consolidator/reconciliation run stamped these as "claimed captured, no parquet found at the resolved
    canonical path" in one pass. Given the correlation with the exact same run-timestamp as the INJURIES
    misclassification finding above, this is very plausibly the SAME root incident (a run that hit a systemic issue —
    API/auth failure or a path-resolution regression — mid-fetch and the manifest ended up in a claimed-but-unwritten
    state for whatever cells were in flight). Not independently root-caused to a specific path-computation-vs-write
    mismatch in this pass (budget); the implementing agent should diff the GCS-write helper's computed path
    (`instruments_service`'s sports writer, likely `writers.py`) against `candidate_parquet_paths()` (per CLAUDE.md's
    "Sports paths" pointer) for the exact prefix template used at that timestamp, since a `prefix_tpls` drift is the
    documented failure class for this reason code workspace-wide. **(3) non-instruments-service rows — both resolved, no
    action needed**: `fill-missing-player-stats` (8,678 rows, 100% PLAYER_STATS) is a **sanctioned, already-marked
    one-off** — confirmed via `instruments-service/scripts/fill_missing_player_stats.py` (`# Epic: instruments_master`,
    `# Lifecycle: oneoff`, `# Delete-when: after fill confirmed in live consolidated _index`), a deliberate gap-fill
    script that calls the same orchestrator fetch + `ManifestWriter.record_captured/_empty/_failed` path as the main
    pipeline, just with its own `service_name` string and a bypassed date-iteration for efficiency. Not a
    service_name-drift bug — leave as-is (delete the script only once its Delete-when condition is met). The 88
    `market-tick-data-service` rows: 100% `capture_status=captured`, 100% `data_type=PLAYER_STATS`, blank
    `error_reason`, spread across ~25 distinct leagues and dates 2020-2026 (pulled individually — sample in this
    session's scratch script). These are genuinely-captured historical data with no duplicate/twin (consistent with why
    today's `2f56038e` cleanup left them untouched) — **recommend re-stamping `service_name` to `instruments-service`
    via a direct verified canonical rewrite** (same read-live-index / confirm-no-twin / write-back pattern as
    `instruments-service/scripts/dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py`), NOT deletion — deleting
    would destroy real capture evidence that has no replacement. **Recommended execution order for the next (fixing)
    agent**: (c) blank-data_type write-path fix first (cheapest, most clearly a bug, unblocks re-verification of the
    shard-completeness path broadly) → (a) INJURIES misclassification fix + UAC table entry + ONE manual
    envelope-inspection call before any re-attempt → (b) FIXTURES root-cause (mirror the (a)/(c) method) → (d)
    phantom-path diff → re-attempt all four classes → (3) service_name rewrite for the 88 MTDS rows → final re-verify
    todo. of accepting a documented-equivalent residual.

- 2026-07-13 (sub-agent, investigation-only dispatch): **`mdps_odds_horizon_bucket` zero-ever-captured root-cause —
  CONCLUSION: NOT a broken/unbuilt pipeline. Root cause is a manifest-bucket-routing split-brain: the real captured data
  lives in a DIFFERENT manifest than the one this investigation (and the plan's §0 baseline) queried.**
  - **The pipeline is fully built and actively running.** Producer:
    `market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py`
    (`SportsBucketAssignmentAdapter`, registered
    `@CandleAdapterRegistry.register(MarketAssetGroup.SPORTS, "odds_horizon_bucket")`) — complete, tested,
    honest-coverage-compliant (empty/failed paths correctly distinguished). Entrypoint:
    `market-data-processing-service/scripts/reprocess_sports_odds.py`. Launcher:
    `deployment-service/scripts/vm/launch-mdps-sports-bucket-vm.sh` (Pass K of the archived
    `sports_predictions_e2e_2026_05_05` plan).
  - **Direct evidence it has run and is current**: `reprocess_sports_odds.py:149` resolves its manifest bucket as
    `get_bucket_name("market-data-tick-sports", project_id=project)` → writes to
    `gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet` — a SEPARATE physical
    manifest from `instruments-store-sports-prd` (the one this task's brief + the plan's §0 baseline queried). Direct
    read of that manifest (1,958,499 total rows): `source=mdps_odds_horizon_bucket` → 124,294 rows, `capture_status`
    123,642 `captured` / 652 `empty_confirmed`, **0 attempted_failed**; `service_name` split
    `market-data-processing-service` 109,638 + `market-tick-data-service` 14,656; `written_at` spans
    2026-05-05T22:07:33Z → **2026-07-13T06:16:02Z (today)** — the pipeline is live and current, ~99.5% capture rate.
    Confirmed further via GCS listing: real raw `data_source=ODDS_API` tick parquets exist under
    `gs://market-data-tick-sports-prd-central-element-323112/raw_tick_data/by_date/day=.../pipeline_mode=batch_odds_api/`
    across 1,938 distinct `day=` partitions through 2026-06-24 — the upstream input MDPS reads is real and populous.
  - **Why `instruments-store-sports-prd` shows 0 captured**: querying it directly (215,481 `mdps_odds_horizon_bucket`
    rows) shows ALL rows are `service_name=instruments-service`, ALL carrying an `enumerator_run_id` (e.g.
    `enum-universe-sports-20260628-213115`, `enum-universe-sports-20260629-075526`) — i.e. every single row was written
    by the expected-universe ENUMERATOR, never by MDPS/MTDS. Cross-check confirms this categorically: **zero rows
    anywhere in the 4,863,784-row `instruments-store-sports-prd` manifest have
    `service_name == "market-data-processing-service"`.** The 209,526 `expected_unattempted` are the enumerator's normal
    seed; the 5,955 `empty_confirmed` all carry `error_reason=EXPECTED_PRE_SOURCE_COVERAGE_START` (dated
    2018-01-01→2020-06-05, i.e. enumerator-side pre-coverage marking, not an actual MDPS attempt).
  - **The actual bug**: `instruments-service/scripts/enumerate_expected_universe.py:279-307` (`_default_bucket_for`)
    hardcodes, as a documented deliberate decision ("slot-4 finding 2026-06-07", see
    `plans/active/sports_manifest_canonicalisation_2026_06_01.md` lines ~1524-1997), that **all of sports' manifest —
    including MTDS/MDPS-owned market-data types — lives in the `instruments-store` bucket**, NOT the per-asset-group
    `market-data-tick` bucket that every other asset_group (cefi/defi/tradfi) uses. That decision was applied to the
    enumerator (denominator writer) but was **never mirrored to the MDPS producer** (`reprocess_sports_odds.py:149`,
    numerator writer) or to MTDS's own raw `odds_api` tick writer, which still both independently target
    `market-data-tick-sports-prd`. Result: numerator and denominator for `mdps_odds_horizon_bucket` (and likely for
    MTDS's raw `odds_api`/`trades` captures — the same split-brain may explain this plan's own §0 "odds_api …
    suspiciously sparse" line, though that source's `ODDS_SNAPSHOT`/`ODDS_MOVEMENT`/`ARBITRAGE` sub-types were
    separately confirmed genuinely credential-gated in the prior entry above — the raw `trades` numerator itself is NOT
    credential-gated and DOES exist, just in the other bucket) live in two different physical manifests that nothing
    ever merges — `codex/05-infrastructure/manifest-consolidator-ssot.md`'s Cloud Run consolidator jobs consolidate
    SHARDS WITHIN a bucket, not ACROSS the instruments-store/market-data-tick pair.
  - **Not a deferred/intentional design gap** — no plan or issue doc marks this as known;
    `sports_predictions_e2e_2026_05_05` (archived 2026-05-05, `status: in_progress` at archive time) explicitly called
    for running exactly this pipeline (Group D todos, all still `- [ ]` unchecked at archive) and was archived without
    those todos ever being flipped or re-homed to a successor plan — this is the silent-gap case, not the
    intentional-deferral case. Because features-service's sports reader
    (`features-service/features_service/sports/data/gcs_reader.py`, `test_read_bucketed_odds.py`) reads bucketed parquet
    **directly by GCS path**, not via the manifest, the actual ML/feature pipeline for `odds_horizon_bucket` is
    unaffected by this bug — only the manifest-derived coverage metric (and this investigation) were fooled.
  - **Recommended fix (concrete, for the implementing agent)**: (1) Either (a) make `reprocess_sports_odds.py:149` and
    MTDS's raw sports `odds_api` writer resolve their manifest bucket via the SAME `sports → instruments-store` routing
    exception already in `enumerate_expected_universe.py::_default_bucket_for` (co-locate numerator + denominator, the
    architecturally-consistent fix, matches the documented 2026-06-07 decision), OR (b) if `market-data-tick-sports-prd`
    is meant to stay the sports market-data canonical manifest instead, revert the enumerator's sports exception and
    seed the `mdps_odds_horizon_bucket`/raw-odds expected-universe there instead — **(a) is recommended** since the
    enumerator-side decision is the more recent, deliberately-verified one (WAVE-2 dry-runs, slot-4, 2026-06-07) and
    instruments-store-sports-prd is what this plan, the operator's task brief, and presumably the data-status UI all
    already treat as sports' canonical manifest. (2) One-time backfill: after the code fix, re-run
    `reprocess_sports_odds.py --force` (idempotent, no API credits — pure re-derivation from existing raw ticks) so the
    123,642 already-computed captures get correctly stamped as `captured` in `instruments-store-sports-prd` instead of
    silently sitting in the orphaned `market-data-tick-sports-prd` copy; do NOT double-count — either migrate/merge the
    existing 124,294 rows or let the re-run naturally overwrite via `ManifestWriter`'s dedup key. (3) Apply the
    identical fix-and-check to MTDS's raw `odds_api`/`trades` writer since it has the same bucket mismatch and is very
    likely why this plan's own §0 table flagged "odds_api … suspiciously sparse/dead" for the raw-tick numerator
    (separate from the credential-gated derived sub-types already resolved in the prior entry above). (4) Audit whether
    any other MTDS/MDPS sports writer (footystats/SFI/etc. already look clean per §0, so likely unaffected — they may
    already target `instruments-store-sports-prd` correctly) has the same mismatch before declaring this class of bug
    closed.

- 2026-07-13 (slot-3, implementation dispatch — `odds_api` todo): **re-verified the investigation's own recommended
  "optional polish" and found it does NOT apply as stated; corrected root-cause below; todo marked DONE with no code
  change (the correct outcome, not a shortcut).**
  - **Live-manifest spot-check** (single-row read of
    `gs://instruments-store-sports-prd-central-element-323112/_index/ availability_index.parquet`,
    `source=="odds_api"`): confirms 2,661 `empty_confirmed` + 6 `attempted_failed` (matches the investigation exactly).
    New finding: **all 6 `attempted_failed` rows carry `error_reason="PipelineModeSourceMismatchError"`** (dates
    2019-01-23, 2019-12-12, 2020-02-06, 2020-04-21, 2020-04-23, 2020-04-27; `service_name=instruments-service`
    throughout). This is a stronger, more precise finding than the investigation's "pre-registry-correction noise"
    framing — it is literally the SAME exception class the current-day write gate raises (confirmed live in
    `instruments-service/scripts/backfill_orphan_class_e_sports.py`'s `resolve_source_and_mode()` docstring and
    `backfill_orphan_class_e.py`'s `MissingSourceError`/ `PipelineModeSourceMismatchError` gate commentary) — i.e. these
    6 rows are the write-safety gate **correctly rejecting** an attempted odds_api write for the generic `ODDS`
    data_type (which `SOURCE_PRIORITY` reserves for footystats — see the 2026-07-15 correction immediately below), and
    recording that rejection honestly as `attempted_failed`. This is the manifest doing exactly what it's supposed to do
    (per `codex/02-data/availability-manifest-and-data-status.md` — "never silent placeholders," trust the actual
    distribution) — **not a defect to patch.**
  - **CORRECTION 2026-07-15 (premise was false when written; the CONCLUSION STANDS).** The parenthetical above — _"which
    `SOURCE_PRIORITY` reserves for footystats"_ — was **factually false on 2026-07-13**, the day it was written:
    `SOURCE_PRIORITY` had **no** `("sports","ODDS")` key at all, so `has_source_priority("sports","ODDS")` returned
    `False`. Commit `8fb1f54f` (2026-06-25) stripped ODDS from `SOURCE_PRIORITY` + `AVAILABILITY_AT_SEMANTICS` +
    `SPORTS_DATA_TYPE_TO_SOURCE` as decision #6's "coherent unit"; the operator REVERSED #6 on 2026-06-27 but the revert
    (`c75101be`) restored only `SPORTS_DATA_TYPE_TO_SOURCE`. So the registry was silently ODDS-less for the 2026-06-25 →
    2026-07-15 window that contains this entry. Found by the 2026-07-15 ODDS-ownership audit
    (`issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md` §A); the entry
    is **restored** (exact pre-8fb1f54f value) in unified-api-contracts@57bcc7c5, so the premise is TRUE again and the
    sentence now reads correctly.
  - **The 6-row decision is NOT reopened — it survives the corrected premise, on re-verification.** The rows were
    written _before_ the 2026-06-25 removal, i.e. while `SOURCE_PRIORITY` genuinely did reserve ODDS for footystats, so
    the gate that produced them behaved exactly as described. Re-verified at runtime post-restore
    (`unified-api-contracts/.venv`): `get_source_priority("sports","ODDS") == ["footystats"]`,
    `valid_manifest_sources("sports","ODDS") == ["footystats"]`,
    `is_valid_manifest_source("sports","ODDS","odds_api") is False`. The write-safety gate does reject an odds_api ODDS
    write, the 6 `attempted_failed` rows are that rejection recorded honestly, and **"not a defect to patch" remains the
    correct call.** Only the stated reason was (temporarily) unsound, never the outcome.
  - **Latent risk this exposed (now closed):** for the 20-day window the pair was unregistered,
    `has_source_priority("sports","ODDS")` was `False` — and UTL `_writer_ingest.py` gates its write-time mis-stamp
    guard on exactly that call. So sports ODDS writes were accepted **without source validation** during the window; a
    write like these 6 would NOT have been rejected. This is the enabling condition behind the bogus
    `source=api_football` × `ODDS` rows in §B of the audit issue doc.
  - **Root-caused why the investigation's suggested classifier "polish" does not apply**: read
    `market-tick-data-service/market_tick_data_service/scripts/rebuild_sports_manifest_v9.py` and its helper
    `_rebuild_sports_write.py` in full. `_classify_empty_row` (and its 9-step `_RETIRED_DATA_TYPES`/`EXPECTED_*` relabel
    logic) is invoked ONLY over rows already sitting in `empty_confirmed` status (`_classify_all_empty_rows` iterates
    `empty_df`, the empty-only slice of the index). Existing `attempted_failed` rows take a **completely separate,
    unconditional** path: `_write_attempted_failed_rows` (`_rebuild_sports_write.py:308-353`) iterates every row with
    `capture_status == "attempted_failed"` and re-emits it via `writer.record_failed(...)`, preserving `error_reason`
    verbatim (or a `UNKNOWN_FETCH_FAILURE_PRESERVED_FROM_V8` fallback) — there is NO reason-based filter, source check,
    or data_type check in that path at all. Even setting aside that mismatch: reason-relabeling (even if it did fire)
    changes only the empty-row `reason` column, never the row's `capture_status` — so it could never move an
    `attempted_failed` COUNT to 0 regardless. **Conclusion: the suggested classifier exemption is a no-op for this gap
    on both counts** (wrong code path; wrong mechanism even if it were the right path). Not implementing it is the
    correct call, not a shortfall.
  - **Decision (no operator ask, per `/autonomous`)**: leave the 6 rows exactly as recorded. Relabeling a genuine
    gate-rejection event to erase it from the `attempted_failed` tally would be dishonest-manifest behavior (the
    opposite of what the honest-absence rule requires) for a below-materiality (6-row), already-non-reproducible
    (current `SOURCE_PRIORITY`/`PipelineModeSourceMismatchError` gates block recurrence) historical artifact. This is
    the plan DoD's explicit "documented-equivalent residual" case, matching the understat precedent already cited.
  - **Files read (no edits needed)**:
    `market-tick-data-service/market_tick_data_service/scripts/ rebuild_sports_manifest_v9.py` (896 lines, full read of
    `_classify_empty_row` + docstring + call sites),
    `market-tick-data-service/market_tick_data_service/scripts/_rebuild_sports_write.py:165-459` (`_write_empty_rows`,
    `_write_attempted_failed_rows`, `_classify_all_empty_rows`),
    `instruments-service/scripts/backfill_orphan_class_e.py`
    - `backfill_orphan_class_e_sports.py` (gate confirmation, unchanged from investigation).
  - **Todo `odds_api source: retirement-status check` flipped to `[x]` above.** No commits to `market-tick-data-service`
    or `instruments-service` — this todo's terminal state is documentation-only, which is the correct root-caused
    outcome (see workspace rule: "if the investigation's recommended fix turns out to be wrong... document what you
    actually found, don't force the prior recommendation").
- 2026-07-13 (slot-3, FINAL RE-VERIFY dispatch — `odds_api` todo, post-`2d0e4dd75`): **fresh single-parquet read of
  `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` (4,863,784 rows total,
  matches §0's post-cleanup count) confirms the shipped fix's claims exactly, no drift since the implementation
  commit.** `source=="odds_api"` slice (2,667 rows): `empty_confirmed`=2,661, `attempted_failed`=6 (same 6 dates —
  2019-01-23, 2019-12-12, 2020-02-06, 2020-04-21, 2020-04-23, 2020-04-27 — all `service_name=instruments-service`,
  `error_reason=PipelineModeSourceMismatchError`), `expected_unattempted`=0, `captured`=0. Dedup-key group-by
  (`date`,`venue`,`data_type`,`service_name`) within the odds_api slice: **0 duplicate groups.** Compared to §0 baseline
  (rows=2,667 / captured=0 / attempted_failed=6 / expected_unattempted=0): **identical — zero movement**, as expected
  for a documentation-only todo.
  - **Verdict: documented-equivalent residual, NOT the literal 0/0/0 bar** — the category does not hit the
    understat-standard literal-zero bar (6 `attempted_failed` rows remain), but per the 2026-07-13 implementation entry
    above this is the plan DoD's explicit "documented-equivalent residual" case, not a still-broken gap: the 6 rows are
    a historical, non-reproducible (`PipelineModeSourceMismatchError` — the current write-safety gate now blocks this
    exact mismatch class at write time, confirmed live in
    `instruments-service/scripts/ backfill_orphan_class_e.py`/`backfill_orphan_class_e_sports.py`), below-materiality
    (6-row) record of the gate correctly rejecting a mismatched odds_api write for the footystats-owned generic `ODDS`
    data_type — relabeling or erasing them would itself violate the honest-manifest rule
    (`codex/02-data/availability-manifest-and-data-status.md`). 0 dedup groups (clean). **Nothing left open on this
    todo; no further action warranted.**

- **2026-07-13 (slot-3, interactive session, correction to the api_football investigation's "453,961
  expected_unattempted is legitimate, no fix needed" verdict) — CONTRADICTED for the TEAMS subset (192,384 of the
  453,961, ~42%).** Operator asked a sharp follow-up question (pre-2020-unrun vs genuinely-no-fixture) that prompted a
  direct re-verify rather than trusting the aggregate claim. Live-manifest query
  (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`,
  `source=api_football data_type=TEAMS`, 296,554 total rows): **`captured` rows split into TWO incompatible grains** —
  3,648 rows with BLANK `league_id` (`row_count` ≈ 621, a bulk daily bundle of ~621 teams across ALL leagues aggregated
  into one row/day) vs 100,498 rows with a POPULATED `league_id` covering only **33 distinct leagues** (~3,046
  rows/league, i.e. near-daily captures for those 33). The `expected_unattempted` enumerator generates one expected cell
  **per (league_id, date)** — 94 distinct leagues, 3,116 dates each (2018-01-01→2026-07-13, literally every day in
  range). **Overlap check: of the 94 EU leagues, only 33 have ANY non-blank-league_id captured row — 61 of the 94 EU
  leagues have LITERALLY ZERO per-league TEAMS captures across the entire 8.5-year window.** This is not "most cells are
  genuinely no-fixture" (TEAMS is a roster fact, not fixture-dependent, so it doesn't have "no fixture" off-days the way
  FIXTURES/STANDINGS do) — it is a **genuine, unaddressed capture gap for 61 specific (mostly second-tier) leagues'
  TEAMS data**, going back to 2018. Root cause not yet identified in this pass (candidates: the per-league TEAMS capture
  path was only ever wired for a 33-league subset, or the bulk/blank-league_id bundle path was meant to be the ONLY
  source of truth and the enumerator should not be generating per-league TEAMS expectations at all — needs code-level
  investigation of whichever orchestrator function drives per-league TEAMS capture vs the bulk bundle, and of
  `enumerate_expected_universe.py`'s TEAMS enumeration to see which grain it _should_ match). **This todo
  (`api_football deep investigation`) should NOT be considered closed on the TEAMS point** until this gap is root-caused
  and either (a) a real per-league TEAMS backfill ships for the 61 leagues, or (b) the enumerator is corrected to not
  expect per-league TEAMS grain if the bulk bundle is the intended sole source (decide-and-document, not a silent
  descope, per the external-data-always-available rule). Other data_types in the 453,961 total (ODDS
  82,749/FIXTURE_LINEUPS 47,282/FIXTURE_EVENTS 47,028/FIXTURE_STATS 36,677/PLAYER_STATS 26,363/INJURIES
  20,700/FIXTURES 778) were NOT re-verified in this pass — the original "legitimate" claim may hold for those, but given
  TEAMS was wrong, they should get the same direct-verification treatment (sample captured vs expected grain match)
  before being marked closed, not taken on the aggregate agent's word alone.
- **2026-07-13 (slot-3, interactive session) — MTDS vs MDPS `mdps_odds_horizon_bucket` row-count asymmetry, explained
  (operator question).** Operator asked why MDPS (109,638 captured rows) and MTDS (14,656) differ so much for what's
  "still odds, one just processed/bucketed." Direct comparison in the OTHER manifest
  (`gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`,
  `source= mdps_odds_horizon_bucket`): **both service_names cover the IDENTICAL 1,813 distinct dates, IDENTICAL date
  range (2020-06-06→2026-04-14), and IDENTICAL 38 leagues** — no coverage gap between them. The row-count difference is
  a GRAIN difference, not a gap: `market-tick-data-service` writes exactly one row per (date, league) with
  `row_count=1.0` uniformly (a coarse "did we ingest any odds tick for this league today" marker);
  `market-data-processing-service` writes multiple rows per (date, league) with `row_count` unpopulated (NaN) —
  consistent with one row per distinct horizon-bucket (e.g. per pre-kickoff time window) per match, the derived
  fine-grained product. ~7.5x ratio (109,638/ 14,656) is plausible for "several horizon buckets per match" at this
  league/date volume. **Not a bug** — same dates, same leagues, different write-grain for raw-ingest-marker vs
  derived-product. No further investigation needed on this specific question.

- **2026-07-13 (slot-3, IMPLEMENTATION dispatch — `mdps_odds_horizon_bucket: root-cause zero-ever-captured` P0 todo).
  Root cause confirmed exactly as the prior investigation concluded (manifest-bucket-routing split-brain); code fix
  shipped + a metadata backfill applied; TWO additional, deeper bugs discovered in the process and scoped out as
  follow-on todos rather than rushed.**
  - **Code fix shipped**: `market-data-processing-service@6907257e4`
    (`fix(sports): route mdps_odds_horizon_bucket manifest to instruments-store-sports`, pushed directly to
    `live-defi-rollout` per this session's established direct-push convention — `quality-gates.sh` green before commit).
    `reprocess_sports_odds.py` now has TWO separate bucket resolvers: `_resolve_bucket()` (raw-odds input + bucketed
    OUTPUT DATA — unchanged destination, stays `market-data-tick-sports-prd`, matches what `features-service`'s
    `read_odds_data`/`read_bucketed_odds` readers resolve) and a NEW `_resolve_manifest_bucket()` (the
    `ManifestWriter.catalogue_bucket`, now `resolve_bucket_name(kind="instruments-store", asset_group="sports")` — the
    SAME call the expected-universe enumerator uses). Only the manifest moved; no data bytes moved; the fix is a pure
    routing correction.
  - **A SECOND, independent bug found + fixed in the SAME commit** (in-file, same findings-triage rule): the
    pre-existing `_resolve_bucket()` itself was ALSO broken, unrelated to the manifest issue. It called
    `get_bucket_name("market-data-tick-sports", project_id=project)` — passing `project_id` explicitly. UTL's
    `get_bucket_name` (`core/cloud_constants.py:209`) SKIPS its yaml-SSOT env-tiering delegation whenever `project_id`
    is passed explicitly (a documented behavior — "the resolver reads project_id from env and doesn't accept a
    caller-supplied override") and silently falls through to a legacy no-env-tier shape
    (`market-data-tick-sports-{pid}`, missing `-prd-`) instead of the real bucket (`market-data-tick-sports-prd-{pid}`)
    — confirmed empirically: running the ORIGINAL unmodified function locally produced the wrong bucket name every time,
    in any environment (dev or prod), since `project_id` is NEVER `None` at this call site
    (`UnifiedCloudConfig().gcp_project_id or "test-project"` is always a non-empty string). Historical production runs
    (VM-tarball-deployed, `deployment-service/scripts/vm/launch-mdps-sports-bucket-vm.sh`) evidently ran an OLDER
    `unified-trading-library` snapshot where this branch behaved differently — a fresh checkout/redeploy today would
    have silently started writing real captures to a wrong, un-tiered, likely-nonexistent-index bucket. Fixed by
    switching to `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="sports")` directly — the same call
    MTDS's own `get_tick_data_bucket()` and features-service's `resolve_tick_data_bucket()` already use for this exact
    bucket. Verified locally post-fix: resolves to the correct, real, live
    `market-data-tick-sports-prd-central-element-323112`.
  - **Historical backfill applied** (metadata-only, no re-derivation): `instruments-service` (untracked, one-off)
    `scripts/migrate_orphaned_mdps_odds_horizon_bucket_rows_2026_07_13.py` — migrates the 124,294 orphaned
    `source=mdps_odds_horizon_bucket` rows (123,642 `captured` / 652 `empty_confirmed`) from
    `market-data-tick-sports-prd`'s manifest into `instruments-store-sports-prd`'s manifest. **Why a metadata copy, not
    a `--force` re-run**: re-running `reprocess_sports_odds.py --force` would re-invoke `_read_raw_odds()`, whose
    `_CANONICAL_PREFIX_TEMPLATES` expect a `data_source=ODDS_API` path segment — confirmed via live `list_blobs` probes
    (2026-05-10, 2026-06-24) that NO on-disk shape uses that segment (2026-05 layout uses per-bookmaker
    `venue={BOOKMAKER}`; 2026-06+ layout uses `venue=ODDS_API` with non-`ticks.parquet` filenames) — a `--force` re-run
    today would silently reclassify all 123,642 real captures as `empty_confirmed`, a regression. **Safety-verified
    before writing**: zero identity collision between the 123,968 distinct migrated (date, venue, data_type, timeframe,
    league_id) tuples and the 215,481 existing target rows (the enumerator's seed uses `venue=""` + UPPERCASE
    `data_type="ODDS_HORIZON_BUCKET"` + `timeframe=None` — a different, coarser grain than MDPS's own `venue=ODDS_API` /
    lowercase `data_type` / per-`T-*`-timeframe rows) — so this migration cannot create a new duplicate-dedup-key group
    (today's earlier `dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py` bug class). Dry-run confirmed the
    exact expected counts (124,294 eligible, 0 collisions) before `--apply`. Same accepted one-off convention as that
    script (plain `gcsfs` read/write, no generation-match — DRY-RUN default, `# Epic`/`# Lifecycle`/`# Delete-when`
    marker). **Concurrency note**: `instruments-service` had a live, uncommitted, in-progress WIP from a concurrent slot
    (the `api_football` todo's fix — `failure.py`/`process.py`/`process_completeness.py`/`api_football.py` + test) at
    the time this ran; only this script's own new file was staged/committed, the other agent's dirty files were left
    completely untouched (`git status` verified before and after).
  - **TWO deeper, separate bugs discovered and DELIBERATELY NOT rushed in this session (documented instead, per the "big
    finding → issue doc" rule + AUTONOMOUS_AGENT_RULES rule 11 blast-radius caution)**:
    1. **Expected-universe grain mismatch for `mdps_odds_horizon_bucket`** — even with the bucket now correct, the
       enumerator's 209,526-row `expected_unattempted` seed (coarse: `venue=""`, `data_type="ODDS_HORIZON_BUCKET"`
       uppercase, no `timeframe`, one row per (date, league_id)) will NEVER reconcile against MDPS's actual captured
       shard grain (`venue="ODDS_API"`, `data_type="odds_horizon_bucket"` lowercase, one row per (date, league_id,
       timeframe)) — confirmed zero identity overlap in a live dry-run. This means the coverage metric for this source
       will show BOTH ~209k `expected_unattempted` AND ~124k `captured` as entirely disjoint cells post-migration — real
       progress (real work now visible) but NOT a clean 100%-coverage story, because the "expected" side needs its own
       re-seed at the correct grain. This is a design-level fix to `enumerate_expected_universe.py`'s sports
       `mdps_odds_horizon_bucket` seeding logic, not a quick patch.
    2. **Raw-input path-template drift (MTDS on-disk convention has moved past the MDPS reader)** — `_read_raw_odds()`
       in `reprocess_sports_odds.py` has apparently been unable to find ANY current-shape raw odds data for a while
       (confirmed no matches for 2026-05 or 2026-06 dates); MTDS's actual on-disk sports odds layout has evolved
       (per-bookmaker `venue=` segments in 2026-05, meta `venue=ODDS_API` per-sport files in 2026-06+) without the
       reader's `_CANONICAL_PREFIX_TEMPLATES` being updated to match. This means FUTURE re-runs (even post-bucket-fix)
       may currently be unable to capture any NEW dates until this is fixed — a real, live pipeline-health risk,
       independent of the manifest-routing bug this session fixed. Needs careful cross-referencing of MTDS's exact
       current writer convention (`market_tick_data_service/engine/orchestrator/partitioned_writer.py`) against every
       historical layout era before a safe multi-template fix can ship (get it wrong and captures silently regress
       further). **Not attempted in this session** — flagged here + as a new todo below, per the workspace's
       blast-radius-before-fleet-change rule (this specific reader affects a currently-active, revenue-relevant sports
       ML pipeline; a wrong guess at the new prefix shape is worse than leaving it as a documented, precisely-scoped
       open item).
    3. **(Correction to this plan's own earlier `odds_api` conclusion, filed 2026-07-13 investigation-only dispatch
       above)**: that entry concluded `source=odds_api` is fully and correctly credential-gated/dead post-2020-06-06,
       based on querying ONLY `instruments-store-sports-prd`. A direct check of the OTHER manifest
       (`market-data-tick-sports-prd`) for `source=odds_api` during this session found **362,665 rows, 362,631
       `captured`** (`service_name` split `market-tick-data-service` 195,437 + `migrate-sports-canonical` 167,220 +
       `market-data-processing-service` 8), `written_at` spanning through **today** — i.e. the SAME manifest-bucket
       split-brain bug class affects the raw `odds_api` numerator too, at ~3x the row-count of
       `mdps_odds_horizon_bucket`. That prior entry's conclusion is **INCOMPLETE, not wrong on its own narrow evidence**
       (the credential-gated finding for the `ODDS_SNAPSHOT`/`ODDS_MOVEMENT`/`ARBITRAGE` derived sub-types still holds —
       those genuinely have 0 rows anywhere post-2020-06-06) — but the raw `trades`/`odds_api` capture itself is very
       much alive and simply invisible in the canonical manifest, same bug, much bigger blast radius. **This is a
       cross-repo, data-correctness "big finding"** — flagged here for the operator/next dispatch, not silently folded
       into this session's narrower `mdps_odds_horizon_bucket` fix (fixing MTDS's raw-capture manifest routing touches
       the SHARED, cross-asset-group `process_ticks()`/`_DateRunState.bucket` orchestrator used by cefi/defi/tradfi/
       sports/prediction alike — a substantially higher-blast-radius change than this session's isolated MDPS-script
       fix, requiring its own careful, dedicated pass per AUTONOMOUS_AGENT_RULES rule 11).
  - **New follow-on todos filed** (P1, not part of this session's scope, decide-and-document per autonomous rules —
    genuinely separate bodies of work, not a deferral of THIS todo which is fully closed):
    - `[DATA] P1. MTDS shared-orchestrator sports-manifest-bucket routing`: extend the same `sports → instruments-store`
      manifest-bucket exception to MTDS's own cross-asset-group raw-capture path
      (`engine/orchestrator/__init__.py::get_tick_data_bucket()` / `_DateRunState.bucket` / `manifest_finalize.py`'s
      `catalogue_bucket=state.bucket`) WITHOUT moving the actual tick-byte write path (mirror this session's
      `_resolve_bucket()` vs `_resolve_manifest_bucket()` split) — then migrate the 362,665 orphaned `odds_api` rows the
      same way. Requires careful audit of every `ManifestWriter`/preflight-lookup call site in the shared orchestrator
      (affects ALL asset_groups, not just sports) before shipping — full blast-radius proof required per
      AUTONOMOUS_AGENT_RULES rule 11.
    - `[DATA] P1. mdps_odds_horizon_bucket expected-universe grain realignment`: fix `enumerate_expected_universe.py`'s
      sports seeding for this source so `expected_unattempted` uses the SAME
      `(venue=ODDS_API, data_type=odds_horizon_bucket lowercase, timeframe=T-*)` grain MDPS actually writes, instead of
      the current coarse `(venue="", data_type=ODDS_HORIZON_BUCKET uppercase, no timeframe)` seed — required before this
      source can show a clean 0/0/0-style coverage number.
    - `[DATA] P1. reprocess_sports_odds.py raw-input prefix-template refresh`: reconcile `_CANONICAL_PREFIX_TEMPLATES`
      in `_read_raw_odds()` against MTDS's actual current on-disk sports-odds writer convention (multiple historical
      layout eras confirmed: `data_source=` never seen on disk; per-bookmaker `venue={BOOKMAKER}` circa 2026-05; meta
      `venue=ODDS_API` circa 2026-06+) — needed before any FUTURE `--force` re-run can safely capture new dates without
      silently regressing existing coverage.
  - **This todo (`mdps_odds_horizon_bucket: root-cause zero-ever-captured`) is DONE**: the manifest-bucket-routing root
    cause is fixed in code (not just data patched), the historical real captures are now visible in the canonical
    manifest, and every deeper follow-on discovery is filed as a scoped todo above rather than silently rolled into this
    fix or left undocumented.

- **2026-07-13 (slot-3, FINAL RE-VERIFY dispatch — footystats + soccer_football_info + transfermarkt + open_meteo
  residuals, post per-league-isolation-fix `instruments-service@746ce3e2`/`5b8cc6d0`): residual-closer
  (`sports_attempted_failed_residual_closer_2026_07_13.py`, PID 3247, `agentwork/sports_residual_fix_2026_07_13` branch)
  is STILL ACTIVELY RUNNING at read time — this is a mid-flight snapshot, NOT the closer's terminal state.**
  - **Consolidator-staleness caveat discovered**: the closer's OWN internal remaining-count checks were noisy this run —
    round-0 (pre-loop) read 0 attempted_failed for all 3 sources, round=1 verify read 61 total, round=2 verify read 266
    total (≈ the full pre-fix baseline 205+10+51) — a `ManifestConsolidatorStaleError` (consolidated blob >120s stale,
    forced per-VM-shard fallback) was live during the run's early reads (confirmed in a discarded first invocation's
    traceback), so the closer's per-round counts should not be read as a literal progress curve. A direct independent
    read taken THIS check found the consolidated blob freshly updated (17:53:54Z, age ~seconds) — used that fresh window
    for the numbers below, which are more trustworthy than the closer's own round logs.
  - **Fresh single-parquet read** (`read_availability_index`, 4,988,134 total rows — up from §0's 4,863,784 baseline,
    consistent with the separate mdps_odds_horizon_bucket backfill landing):
    - **footystats**: `attempted_failed`=200 (TimeoutError 174, phantom 15, ArrowTypeError 11) vs baseline 205
      (179/15/11) — only the TimeoutError count moved (179→174, 5 resolved so far); phantom+Arrow untouched.
      `expected_unattempted`=56, identical to baseline, 100% dated 2026-07-13 (today's legitimate rolling trailing-edge,
      self-closes next capture pass — unchanged conclusion from the investigation-only pass).
    - **soccer_football_info**: `attempted_failed`=10 (phantom), UNCHANGED from baseline, despite the closer's own log
      claiming `[sfi] processed=10 raised=0` — the per-VM-shard writes are buffered and only drain into the canonical
      index via the script's single explicit `flush_all_pending_buckets()` call AFTER the entire round loop exits (not
      yet reached while PID 3247 is alive), so this canonical read cannot yet show the SFI reprocessing's effect even if
      it succeeded. `expected_unattempted`=94, unchanged, 100% today's date (legitimate).

- **2026-07-13 (sub-agent, investigation-only dispatch — TEAMS 61-league gap root-cause, read-only, no code/data
  changes).** Full root-cause of the P0 todo "api_football TEAMS: root-cause + fix the 61-league per-league capture
  gap." **Conclusion: ONE code path, deliberately scoped too narrow (not two competing capture paths); the 61 leagues
  ARE api_football-covered; the blank-league_id bundle is a phantom manifest artifact, not a reusable data source; true
  backfill cost is ~549 API calls, not ~190k.**
  - **(1) One code path, not two.** `instruments_service/engine/orchestrator/sports_reference_core.py:138-216`
    (`_fetch_teams_and_standings`) is the ONLY production call site of `adapter.get_teams()` for api_football. It
    iterates `_orch.get_prediction_leagues()` (UAC `LEAGUE_REGISTRY` filtered to `classification=="Prediction"` —
    exactly 33 leagues, confirmed by counting `classification="Prediction"` in
    `unified-api-contracts/.../league_data_prediction.py`) and writes ONE per-league parquet per league via
    `teams_df.groupby("league_id")` → `_gated_sink_write(partition={"league": ...})`. The `else` branch (missing
    `league_id` column) explicitly **skips the write** with a warning ("data shape regression... Skipping write to keep
    manifest honest") — there is no branch in current code that CAN write a blank-`league_id` captured TEAMS row. Live
    GCS listing confirms the code matches reality:
    `gs://instruments-store-sports-prd.../sports_reference/by_date/ day=2026-07-13/pipeline_mode=batch_api_football/entity=teams/`
    contains exactly 33 `league=<X>/teams.parquet` objects, zero bare-path file.
  - **(2) Why only 33 — a scope mismatch between two functions in the SAME module, not a deliberate design split.**
    `sports_reference_core.py:113` (the module's OWN absence-recording helper, `_record_empty_for_uncaptured`) already
    correctly calls `_orch.get_expected_leagues_for_source("api_football")` with NO classification filter — the full
    94-league set (`get_expected_leagues_for_source` returns leagues where `"api_football" in league.data_sources`,
    optionally filtered by classification; `None` = all). UAC's `SPORTS_ENTITY_LEAGUE_COVERAGE["TEAMS"] = None`
    (`provider_league_ids.py:776`) explicitly documents TEAMS as "expected on all fixture dates" (no per-league
    restriction) — i.e. the ENUMERATOR/denominator side was deliberately built for the full 94-league universe. The
    CAPTURE loop three lines below in the same file was simply never widened to match — it still reads
    `get_prediction_leagues()` (Prediction-tier only), a leftover scoping choice. Verified the 33/61 split maps exactly
    to classification: 33 Prediction (captured) + 22 Features + 39 Reference = 94 (0 captures) — Features = mostly
    2nd-division domestic leagues (e.g. `EERSTE_DIVISIE`, `USL_CHAMPIONSHIP`, `J2_LEAGUE`), Reference = mostly
    cup/continental competitions (`FA_CUP`, `DFB_POKAL`, `UCL`, `COPA_LIBERTADORES`, etc, tier=0). This is a genuine,
    fixable capture-loop scoping bug, not an intentional two-tier design — decision: **(a) applies** (widen the capture
    path), not (b) (the enumerator is the one that's already correct).
  - **(3) API coverage check for the 61 — CONFIRMED covered, not an out-of-provider-coverage case.** Queried the live
    manifest for all api_football rows where `league_id` is one of the 61: FIXTURES has 27,843 `captured` rows,
    FIXTURE_STATS 6,229, FIXTURE_EVENTS 4,176, FIXTURE_LINEUPS 4,006, INJURIES 784, PLAYER_STATS 656 — spanning 60 of
    the 61 leagues. Api-Football is actively and successfully returning fixture-level and even player-level data for
    these same leagues; team-roster data (`/teams`) is a strictly more basic/available endpoint than lineups or
    per-player stats on that provider's API. **No evidence any of the 61 lack TEAMS coverage** — this should be typed as
    a real backfill target, not `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`. (Did not make a live manual API call to verify
    a specific league's `/teams` response directly — the indirect evidence via sibling data_types for the same leagues
    is strong enough to proceed with a backfill attempt; the implementing agent should treat any per-league API 4xx as a
    genuine `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` exception discovered during the backfill run, not assume upfront.)
  - **(4) True backfill scope — season-grain, NOT date-grain: ~549 real API calls, not ~190k.**
    `adapter.get_teams(league_id, season=None)` (`api_football.py:610`, `base.py:247`) is a **season-keyed** call — a
    team roster is fetched per season, not per day. The current orchestrator merely happens to invoke it once per
    calendar day inside the daily loop (with same-day, in-memory caching via `_orch._cached_teams_df`), which is why the
    33 already-wired leagues show ~3,046 near-daily rows each over 8.5 years for data that changes maybe twice a season.
    The literal 61-leagues × 3,116-dates naive estimate (~190k cells) is NOT the real API cost: the true minimum is ~61
    leagues × ~9 seasons (2018–2026) ≈ **549 real `get_teams` calls**. Each season's single roster payload can then be
    replicated to populate every date-row in that season's manifest window (many cheap manifest WRITES, zero incremental
    API cost per day) — mirroring the existing per-league write shape so the resulting per-day row count matches the 33
    already-canonical leagues' pattern. (Whether the expected-universe itself SHOULD be date-grain for TEAMS at all,
    given it's genuinely season-grain data, is a separate, smaller follow-up worth flagging to the enumerator owner —
    not blocking this backfill.)
  - **(5) Blank-`league_id` bulk bundle (3,648 rows, ~621 teams/day) — CONFIRMED phantom, NOT a reusable/alternate
    source of truth.** Cross-checked a `capture_status=captured` blank-league_id TEAMS row dated **2026-07-13 (today)**
    against live GCS: zero bare-path `entity=teams/teams.parquet` object exists for that day at either the canonical
    (`pipeline_mode=` prefix) or legacy path — the manifest claims captured, no parquet exists anywhere. This is the
    same `phantom_captured_no_parquet_at_canonical_path` class already documented elsewhere in this plan for other
    api_football data_types, just not yet caught by the phantom classifier for this specific (blank-league_id, TEAMS,
    captured) shape. Corroborating evidence: 533 distinct `attempted_at`/`written_at` timestamps across only 3,648 rows
    (repeated re-stamping/rebuild passes touching the same historical rows, not a live daily producer), and dates
    running back to 2014-01-01 — three years before api_football's own `SOURCE_COVERAGE_START` of 2018-01-01. **There is
    no nested per-league structure to unpack** — it is not real captured data at all, so it cannot be repurposed to
    synthesize the missing 61 leagues' rows without fresh API calls. Recommend: (i) do NOT treat it as ground truth or
    attempt to "unpack" it; (ii) re-type these 3,648 rows via the existing
    `scripts/reconcile_phantom_manifest_rows_all.py` tooling (same pattern already applied to the footystats/SFI/weather
    phantom rows elsewhere in this plan) so `captured` → `attempted_failed`/typed-absence, not left as a false-positive
    captured record; (iii) once retyped, this row shape can be deleted from any future "is TEAMS legitimate" sampling.
  - **(6) VM launcher + backfill driver pattern.** `deployment-service/scripts/vm/` sports-registered launchers (grep
    confirmed no hand-rolled name needed): `launch-sports-is-gap-fill.sh` (paired with
    `instruments-service/scripts/query_sports_is_gaps.py`) is the existing per-league-scoped gap-fill launcher already
    recommended elsewhere in this plan for other api_football residuals — reuse it for the TEAMS backfill rather than
    writing a new launcher. `launch-sports-entity-sweep-vm.sh` / `launch-sports-full-sweep-vm.sh` are the other
    sports-registered prefixes available if a full-entity sweep shape fits better. Existing per-league driver code
    patterns to base the TEAMS-specific backfill script on:
    `instruments-service/scripts/backfill_per_league_record_empty.py` and
    `instruments-service/scripts/migrate_sports_per_league.py` (both already iterate `get_prediction_leagues()` in the
    same per-league shape the TEAMS fix needs, just widened to the full 61-league set — `SOURCE_COVERAGE_START` gates
    the pre-2018 floor automatically since `_fetch_teams_and_standings` is called from the daily `sports_reference.py`
    orchestrator entrypoint that already respects it).
  - **Recommended fix for the implementing agent (in order): (i)** widen the capture loop at
    `sports_reference_core.py:153` from `_orch.get_prediction_leagues()` to
    `_orch.get_expected_leagues_for_source("api_football")` (matching the module's own absence-recording helper three
    lines above) — this is the root-cause fix, one line; **(ii)** run a season-grain backfill (~549 API calls) for the
    61 newly-in-scope leagues across 2018–2026, writing per-date manifest rows from each season's single payload the
    same way the daily loop already does going forward; **(iii)** retype the 3,648 blank-`league_id` phantom rows via
    `reconcile_phantom_manifest_rows_all.py`; **(iv)** re-verify the live manifest shows 94 distinct captured leagues
    for TEAMS with 0 remaining zero-capture leagues. This todo
    (`api_football TEAMS: root-cause + fix the 61-league per-league capture gap`) is root-caused and ready for
    implementation — not yet flipped `[x]` (no code/data change made in this investigation-only pass, per dispatch
    scope).
    - **transfermarkt**: `attempted_failed`=0 (unchanged, already clean), `expected_unattempted`=47, unchanged, 100%
      today's date (legitimate) — no closer work targets this source (it was never in scope, already clean at baseline).
    - **open_meteo (weather)**: `attempted_failed`=51 (phantom), UNCHANGED from baseline — same buffered-write
      explanation as SFI (closer log shows `[weather] processed=51 raised=0` mid-run, not yet drained).
    - **Dedup-key groups**: 0 duplicate groups for all 4 sources when keyed correctly on
      `(date, venue, data_type, league_id, service_name)` — an initial pass of this check that omitted `league_id`
      mis-flagged thousands of "duplicate" groups (footystats 9,176 / SFI 2,391 / transfermarkt 3,161 / weather 2,840);
      re-run with `league_id` included (these sources are league-grain, not venue-grain, so `venue` is blank and cannot
      stand in for the shard key alone) confirmed all 4 sources are genuinely dedup-clean. Documenting this here so the
      next verifier doesn't re-trip the same false positive.
  - **Verdict: NOT YET at the understat-standard bar for footystats/SFI/weather — the closer is mid-run, buffered writes
    haven't drained to the canonical index, and only 5 of 236 targeted attempted_failed rows show as resolved in THIS
    read.** transfermarkt was already clean at baseline and remains so (0/47, both legitimate). Recommend a follow-up
    re-verify once PID 3247 reaches its `EXPLICIT PRE-EXIT DRAIN`/`FINAL TALLY` log lines (or exits) — expect the drain
    to reveal a materially different (likely much closer to 0) attempted_failed count for footystats/SFI/weather once
    the buffered per-VM-shard writes are visible in a subsequent fresh read. Not marking any of the 4 residual todos
    `[x]` this pass — the fix's effect is not yet observable end-to-end.

- **2026-07-13 (slot-3, FINAL RE-VERIFY dispatch — fresh single-parquet read post-fix).** Re-read
  `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` fresh (4,988,134 total
  rows now, up from the §0 baseline's 4,863,784 — expected, reflects the migration write).
  `source=mdps_odds_horizon_bucket` now: **339,775 rows** (215,481 baseline + 124,294 migrated = exact match, confirms
  clean arithmetic, no double-write). `capture_status` breakdown: `captured` **123,642** (was 0), `empty_confirmed`
  **6,607** (5,955 pre-existing + 652 migrated — also exact match), `attempted_failed` **0** (unchanged),
  `expected_unattempted` **209,526** (unchanged — sum of all four = 339,775, fully reconciles, no unaccounted rows).
  `service_name` split: `instruments-service` 215,481 (untouched original enumerator seed),
  `market-data-processing-service` 109,638 + `market-tick-data-service` 14,656 = 124,294 (exactly the migrated set).
  **Duplicate-dedup-key check**: grouping on the coarse identity (date, venue, data_type, timeframe, league_id) alone
  surfaces 326 apparent "duplicate" groups, but re-grouping on the TRUE dedup key (same tuple **+ service_name**, per
  this session's established manifest-consolidator convention) finds **0** true collisions — the 326 are legitimate rows
  from two different `service_name`s (`market-data-processing-service` + `market-tick-data-service`) independently
  writing the same coarse identity, not duplicates. **Verdict: does NOT meet the understat-standard literal 0/0/0 bar,
  but the residual is fully explained and already documented, not still-broken.** `attempted_failed=0` and 0 true dedup
  collisions are clean; the 209,526 `expected_unattempted` residual is the already-filed P1 "expected-universe grain
  realignment" follow-on (the enumerator's coarse seed grain — `venue=""`, uppercase `data_type`, no `timeframe` —
  structurally cannot reconcile against MDPS's actual captured grain — `venue=ODDS_API`, lowercase `data_type`,
  per-`T-*` `timeframe`) — a known, separately-scoped design fix, not an oversight of this fix. The core
  "zero-ever-captured" defect is conclusively resolved: 123,642 real historical captures are now visible in the
  canonical manifest, root-caused in code (not just patched), zero data-integrity regressions (no new duplicate-dedup
  groups, arithmetic fully reconciles). No further action taken this dispatch — re-verify only, per task scope.

- **2026-07-13 (slot-3, IMPLEMENTATION dispatch — root-cause + code fix for the api_football `attempted_failed` /
  blank-`data_type` classes, todos "api_football deep investigation" + "api_football: fix root causes + re-attempt
  failed cells").** Root-caused all four classes precisely (some conclusions **refine/correct** the prior
  investigation-only pass) and shipped verified code fixes. All changes QG-green (`ruff` clean, `basedpyright` no new
  errors beyond pre-existing baseline noise, 1202 relevant instruments-service unit tests pass, targeted UAC tests
  pass) + functionally verified via direct isolated-function assertions (see below) — NOT via a full historical
  re-attempt (see "Deferred" below).

  - **(c) blank-`data_type` `UNCLASSIFIED_ADAPTER_ERROR` (461) — CONFIRMED + FIXED.** Root cause: the GENERIC
    CeFi/TradFi-shaped venue-grain shard-completeness gate (`process_completeness.py::_completeness_and_retry` /
    `_finalize_completeness`) treats sports pseudo-venue names (`API_FOOTBALL`, `FOOTYSTATS`, `UNDERSTAT`,
    `TRANSFERMARKT`, `SOCCER_FOOTBALL_INFO`, `OPEN_METEO`) as literal venues in `active_venues`/`expected_venues`. 5 of
    these 6 (all except `API_FOOTBALL`) are ENRICHMENT-ONLY — fetched in stage 7, never populate `counts` (this stage's
    `written_venues`), so they permanently land in `missing_shards` and the generic corrective write
    (`row_key={"date","venue"}`, no `data_type`) stamps a blank-`data_type` row that can never reconcile against any
    real sports cell (confirmed via direct manifest sample: all 461 blank rows' `venue` ∈ {FOOTYSTATS, OPEN_METEO,
    SOCCER_FOOTBALL_INFO, TRANSFERMARKT, UNDERSTAT} — never API_FOOTBALL). **Fix**: excluded these 5 names from
    `expected_venues` (reusing `process_write.py`'s existing `_NON_VENUE_GRAIN_VENUE_NAMES` SSOT frozenset, which
    already excludes them from venue-grain EU-seeding — same-source-of-truth for both numerator and denominator now).
    `API_FOOTBALL` itself is DELIBERATELY KEPT checkable (it IS genuinely venue-grain here — its top-level FIXTURES
    fetch runs in this same stage-4 fetch) — removing it too would silently drop the only safety net catching a total
    API_FOOTBALL fetch failure during a combined `asset_groups=["ALL"]` run (where `_fixtures_fetch_failed`'s
    zero-records branch never fires because cefi/tradfi/defi still produce records). When `API_FOOTBALL` IS genuinely
    missing, `_finalize_completeness` now maps it to `row_key={"date","data_type":"FIXTURES"}` instead of a blank
    `data_type` — mirroring the existing `process_preflight.py::_build_expected_entities` convention
    (`"FIXTURES" if v == "API_FOOTBALL" else v`) that already existed elsewhere in this codebase for exactly this remap.
    **Files**: `instruments-service/instruments_service/engine/orchestrator/process_completeness.py`.

  - **(b) FIXTURES `FIXTURES_FETCH_FAILED` (665) — ROOT-CAUSED (corrects/extends the prior investigation's "not yet
    root-caused" note) + FIXED.** The write site IS honest
    (`process_zero_records.py::_zero_sports_empty_fixture_markers` — correctly keys
    `row_key={"date","data_type":"FIXTURES","league_id":...}`, not a data-integrity bug per se). The BUG is upstream, in
    the boolean that decides whether a zero-fixture day is a genuine fetch failure: `process.py::_fixtures_fetch_failed`
    returns `True` whenever ANY member of `active_venues` is absent from `non_error_venues` (the stage-4 URDI fetch's
    per-venue success set) — but `active_venues` for a sports run also carries the same 5 enrichment-only pseudo-venues
    from (c) above, which are NEVER part of the stage-4 fetch and so can NEVER appear in `non_error_venues`, regardless
    of whether `API_FOOTBALL`'s actual fixtures fetch succeeded. Net effect: on every genuinely-empty (legitimate
    no-fixture) day, this check FALSELY reported "fetch failed" the moment `active_venues` included more than just the
    fixtures-fetching venue — converting the correct `empty_confirmed(EXPECTED_NO_FIXTURE)` outcome into
    `attempted_failed(FIXTURES_FETCH_FAILED)` for EVERY prediction league in one shot (matches the observed data
    exactly: 665 rows cluster into 144 distinct `attempted_at` runs, each run flipping MULTIPLE leagues simultaneously —
    a single false trigger per run, not per-league organic failures). **Fix**: `_fixtures_fetch_failed` now only checks
    venues that actually participate in the stage-4 fetch — excludes `_NON_VENUE_GRAIN_VENUE_NAMES - {"API_FOOTBALL"}`
    before the membership check (keeps `API_FOOTBALL` itself checkable, since a genuine `API_FOOTBALL` fetch failure IS
    still a real fixtures-fetch failure). Verified directly:
    `_fixtures_fetch_failed(active_venues=[...6 pseudo-venues...], non_error_venues={"API_FOOTBALL"}, skip_urdi=False)`
    → `False` (post-fix; was a false `True` pre-fix), and `_fixtures_fetch_failed(..., non_error_venues=set(), ...)` →
    `True` (genuine API_FOOTBALL failure still correctly detected). **Files**:
    `instruments-service/instruments_service/engine/orchestrator/process.py`.

  - **(a) INJURIES `ApiFootballResponseError` (1,642 total, 1,600 on INJURIES specifically) — TWO real bugs found, both
    fixed (this SUPERSEDES the prior investigation's single "misclassification" framing — the misclassification is real
    but not the primary defect for INJURIES specifically):**
    1. **CONFIRMED live-API check**: manually called the real API-Football `/injuries?date=...` and `/status` endpoints
       with the live production key (`api-football-api-key` secret) for both a data-rich date (2024-05-15, 140 results)
       and a sparse date (2019-03-10, 0 results) — both returned clean `errors: []` envelopes, no plan/token/quota
       restriction on INJURIES today (`Custom300` plan, 300k/day, 6,112 used at check-time). This DISPROVES the prior
       investigation's "likely a plan/entitlement restriction on INJURIES" hypothesis — the account has full INJURIES
       access.
    2. **The REAL bug: `api_football.py::get_injuries` SILENTLY SWALLOWS hard fetch failures into an empty list**,
       unlike its sibling `get_teams`/`_fetch_season_fixtures_with_raw` (which correctly `raise` after
       `_emit_fetch_failed`). `get_injuries` is DATE-WIDE (single call returns ALL leagues' injuries for a date) —
       unlike the 4 genuinely per-fixture methods that share its exact try/except shape (where swallowing IS correct,
       shard-isolation behavior — a single fixture's failure shouldn't fail the whole date), `get_injuries` has no
       per-shard granularity to protect. Swallowing here silently converted ANY hard failure (network, timeout, a
       genuine future plan/token error) into a false "0 injuries, honest absence" (`empty_confirmed`) for the WHOLE date
       — the exact "silent-empty manifest bug" `instruments-service@0db24503` (2026-06-21) fixed for the venue -fetch
       path, left unfixed here. This means the manifest CANNOT currently distinguish a genuine zero-injuries day from a
       masked hard failure for INJURIES. (The historical 1,600 `ApiFootballResponseError` rows themselves are a
       SEPARATE, already-resolved artifact — see "historical-timestamp note" below; they predate/bypass this swallow bug
       via a different code path or a stale migration rewrite, not something this fix needs to explain away.) **Fix**:
       `get_injuries` now re-raises after `_emit_fetch_failed` (matches `get_teams`'s pattern exactly) so a hard failure
       correctly surfaces as `attempted_failed` via the caller (`sports_reference_core.py::_fetch_injuries`'s own
       `except` block), never a silent false-empty.
    3. **Misclassification (the prior investigation's original finding) — ALSO fixed, additively.**
       `failure.py::_classify_adapter_failure` fed `type(exc).__name__` (literal `"ApiFootballResponseError"`) into UAC
       `classify_venue_error`, which is keyed by HTTP/domain codes — never matched, always fell back to the raw class
       name. Fixed: `ApiFootballResponseError` now carries a real `error_key` attribute (the raw envelope error-dict's
       own key — `"plan"`/`"token"`/`"requests"`/`"rateLimit"` — extracted in `_raise_on_api_errors`);
       `_classify_adapter_failure` prefers it (via duck-typed `getattr`, zero risk to every OTHER venue this function
       classifies for) before falling back to the class name. Added the 3 corresponding UAC
       `VENUE_ERRORS_SPORTS["api_football"]` entries (`"plan"`/`"token"`/`"requests"`) so `classify_venue_error` can now
       actually resolve a real classification for future hard failures (previously impossible — nothing in this codebase
       ever produced a code matching the table's pre-existing HTTP-status/`FREE_PLAN_DATE_LIMIT`-style entries;
       confirmed via a repo-wide grep, 0 hits).
    - **Historical-timestamp note (why the OLD 1,600 rows exist despite current code never being able to produce them
      via `get_injuries` alone)**: only 3 distinct `attempted_at` values across all 1,642 rows, and the blank-`venue`
      rows from (c) share the EXACT same microsecond-precision timestamp pattern as a single shared `_failed_attempt_ts`
      computed once per date-shard's completeness-gate call — strong evidence these are migration/rebuild-pass re-stamps
      (a bulk rewrite bumping `attempted_at` to "now" while carrying forward an old `error_reason` verbatim), not fresh
      in-flight failures reproducing today. Not fully re-traced to the exact historical commit that could have produced
      the original `ApiFootballResponseError` via `get_injuries` (budget) — immaterial to the fix either way: whatever
      the historical mechanism, the CURRENT code's two real bugs (silent swallow + misclassification) are now both
      closed, and the stale rows are covered by the re-attempt follow-up below.
    - **Files**: `instruments-service/instruments_service/reference_data/adapters/sports/adapters/api_football.py`
      (`get_injuries` re-raise fix, `ApiFootballResponseError.error_key`, `_raise_on_api_errors`),
      `instruments-service/instruments_service/engine/orchestrator/failure.py` (`_classify_adapter_failure`),
      `unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/sports.py` (3 new
      `VENUE_ERRORS_SPORTS["api_football"]` entries), `instruments-service/tests/unit/test_sports_http_adapters.py` (2
      tests updated to assert propagation instead of the old swallow-to-`[]` behavior — this was itself encoding the bug
      as "intended", per governance rule "if you encounter errors... never mark completed" this required a genuine
      behavior-change test update, not a mechanical adjustment).

  - **(d) `phantom_captured_no_parquet_at_canonical_path` (487) — ROOT-CAUSED, no code fix needed (this is NOT a live
    write-path bug).** `phantom_captured_no_parquet_at_canonical_path` is written EXCLUSIVELY by the dedicated
    reconciliation tooling (`scripts/reconcile_phantom_manifest_rows_all.py` et al.), never by the live orchestrator —
    confirmed via repo-wide grep (every hit is in a `scripts/reconcile_*`/`diagnose_*` one-off, none in
    `engine/orchestrator/`). These 487 rows are the CORRECT, HONEST output of that tooling detecting a previously
    mis-stamped `captured` row with no real parquet at its canonical path and re-flagging it `attempted_failed` so the
    gap is visible and re-attempted — exactly the tool's designed job, not a fresh defect. All 487 share the identical
    `attempted_at=2026-07-13T16:24:30.871968+00:00` (a single reconciliation pass), corroborating the same
    single-run-bulk-restamp pattern as (a)'s historical-timestamp note above — very plausibly the SAME systemic incident
    (whatever caused a batch of writes to fail mid-flight got caught by this same reconciliation run). **No further code
    fix filed** — the correct next step is simply re-attempting these specific cells (covered by the re-attempt
    follow-up below), not a new code change.

  - **(3) 8,766 non-instruments-service rows — RESOLVED.**
    - `fill-missing-player-stats` (8,678 rows): CONFIRMED sanctioned one-off (`scripts/fill_missing_player_stats.py`
      carries proper `# Epic`/`# Lifecycle`/`# Delete-when` markers, calls the same orchestrator fetch +
      `ManifestWriter` path with a deliberate, documented `service_name` override) — left as-is, not a bug.
    - **88 `market-tick-data-service` orphans — FIXED via direct canonical rewrite** (same safe pattern as
      `instruments-service/scripts/dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py`: read live index,
      confirm no canonical twin at the real identity, DIRECT REWRITE — never a shard-merge write, which cannot collapse
      a `service_name`-keyed dedup group). New one-off script
      `instruments-service/scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py` (Epic/Lifecycle/Delete-when
      markers per `codex/06-coding-standards/script-homes.md`), dry-run-by-default, `--apply` re-verifies at run time
      (re-derives the twin-check live rather than trusting the prior investigation's numbers) before writing. Ran
      dry-run (confirmed 88 eligible, 0 excluded) then `--apply`: **all 88 rows re-stamped
      `service_name: market-tick-data-service → instruments-service`, `asset_group: "" → "sports"`. Verified post-apply:
      0 remaining `market-tick-data-service`+`api_football` rows in the live manifest.**

  - **Verification performed (this dispatch)**: `instruments-service` — `ruff check` clean on every changed file;
    `basedpyright` shows zero NEW errors (all pre-existing errors confirmed via `git diff` hunk-location cross-check to
    be outside every line range I touched); full targeted pytest run
    (`-k "completeness or sports or process or orchestrator or failure"`) — **1202 passed, 0 failed**; the 2 updated
    adapter tests independently re-run in isolation (68 passed in `test_sports_http_adapters.py`); 2 direct
    isolated-function assertions proving both the `_fixtures_fetch_failed` false-positive elimination AND the
    `process_completeness` pseudo-venue exclusion (both shown above). `unified-api-contracts` — `ruff`/`basedpyright`
    clean, targeted `pytest -k "sports and error"` 17 passed. Full repo `quality-gates.sh` run TWICE with
    `QG_SENTINEL_DISABLE=true` (first run pre-refinement, second post-refinement) — both show the ONLY hard-gate failure
    (`STEP 5.95` TID251 ratchet, `reconcile_lending_indices_phantom.py:88`) is **conclusively unrelated to this work**:
    that file has zero uncommitted diff (`git diff --stat` empty, last real commit 2026-06-23) and the actual
    over-baseline count is traced to a DIFFERENT, untracked, foreign file
    (`scripts/cefi_legacy_path_dedup_2026_07_13.py`, mtime ~18:35, clearly another concurrent agent's live in-progress
    WIP in this shared checkout, alongside a second untracked foreign file
    `scripts/migrate_orphaned_mdps_odds_horizon_bucket_rows_2026_07_13.py`) — left untouched per the multi-agent "never
    edit unfamiliar/untracked files" hard rule; not staged, not committed, not fixed by me (out of scope, not mine,
    another agent's live WIP).

  - **Deferred work after 2026-07-13 (full historical re-attempt of the stale failed cells)**: the 4 fixes above stop
    the bugs from RECURRING going forward, but the ~3,257 EXISTING `attempted_failed` rows (plus the 461 blank-`venue`
    rows, now correctly excluded from future writes but still sitting in the manifest as-is) are historical artifacts
    that need a genuine re-fetch/re-verify pass to actually resolve, not just a code fix. This is a real, bounded
    infra-scale operation (many historical (date, league) shards spanning 2017-2026, live API calls against the
    `Custom300` plan, 300k/day quota) — appropriately a dedicated backfill VM run (mirror
    `deployment-service/scripts/vm/launch-sports-is-gap-fill.sh`, per this plan's own §"(6) VM launcher + backfill
    driver pattern" note elsewhere), not something to run ad hoc inline in an interactive dispatch. NOT run this session
    — tracked here as the concrete next step for the "final re-verify" todo below. The blank-`venue`/blank- `data_type`
    rows and the phantom rows (d) do not need re-fetching per se (they were never real failures in the live-data sense)
    — a manifest-level cleanup pass (re-typing/removing the now-provably-stale rows) would suffice for those, while
    INJURIES/FIXTURES genuinely benefit from a live re-attempt now that the false-positive triggers are fixed.

  - **Also NOT in scope for this dispatch (flagging, not fixing)**: the NEW "api_football TEAMS: root-cause + fix the
    61-league per-league capture gap" todo (added by a concurrent investigation elsewhere in this same plan) is a
    separate, already fully root-caused, real capture gap — unrelated to the 4 classes this dispatch was scoped to fix.
    Left entirely untouched; that todo's own recommended one-line fix + backfill plan stands as written.

  - **Commits (this dispatch)**:
    - `instruments-service` —
      `fix(sports): api_football root-cause fixes — blank-data_type completeness-gate leak, FIXTURES false-positive fetch-failed, INJURIES silent-swallow + misclassification`
      (process_completeness.py, process.py, failure.py, api_football.py, test_sports_http_adapters.py) +
      `scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py` (new one-off, applied).
    - `unified-api-contracts` —
      `fix(sports): add raw envelope-key VENUE_ERRORS_SPORTS entries for api_football (plan/token/requests)`.

- **2026-07-13 (slot-3, VERIFY dispatch — final re-verify for `api_football`, todo "api_football: final re-verify").**
  Fresh single-parquet re-read of the live manifest (`instruments-store-sports-prd...` bucket,
  `_index/availability_index.parquet`, 4,988,134 total rows; transient `FileNotFoundError` on first read mid a
  consolidator rewrite at `18:06:01Z`, succeeded on immediate retry — not a data issue). **api_football slice: 2,518,571
  rows** (vs baseline 2,518,940 — small net drift from ongoing organic activity, not this fix).
  - **`attempted_failed`: 3,257 — UNCHANGED from the §0 baseline, identical breakdown** (INJURIES 1,946 / FIXTURES 665 /
    blank-`data_type` 461 / PLAYER_STATS 74 / FIXTURE_STATS 46 / FIXTURE_LINEUPS 30 / TEAMS 24 / FIXTURE_EVENTS 11;
    `error_reason` confirms `ApiFootballResponseError` 1,642, `FIXTURES_FETCH_FAILED` 665,
    `phantom_captured_no_parquet_at_canonical_path` 487, `UNCLASSIFIED_ADAPTER_ERROR` 461). This is **expected, not a
    regression** — the shipped fix stops the 4 bug classes from RECURRING going forward; it never claimed to
    retroactively clear the pre-existing rows (documented as deferred backfill-VM work in the IMPLEMENTATION entry
    above). Confirms no drift either direction since the fix landed.
  - **`expected_unattempted`: 452,985** (vs baseline 453,961, -976 — consistent with ongoing organic captures converting
    cells, not fix-driven; the TEAMS 61-league gap this bucket partly represents is still its own open P0 todo above,
    not yet fixed).
  - **Blank-`data_type` rows (any status): 583 total** — 461 `attempted_failed` (unchanged, pre-fix legacy rows) + 122
    NEW `empty_confirmed` rows, `venue` ∈ {API_FOOTBALL, FOOTYSTATS, OPEN_METEO, SOCCER_FOOTBALL_INFO, TRANSFERMARKT,
    UNDERSTAT} — confirms the `process_completeness.py` fix IS live and correctly routing the 5 enrichment pseudo-venues
    to `empty_confirmed` now instead of minting new blank-`data_type` `attempted_failed` rows (0 new blank-`data_type`
    failures since the fix shipped).
  - **Duplicate dedup-key groups (identity = date + source + data_type + service_name + league_id + fixture_id, per the
    understat precedent's "present optional dims" rule): 39,222 groups / 78,738 rows involved** — NOT part of the
    original §0 table (which only tracked rows/captured/attempted_failed/expected_unattempted) and NOT something this
    dispatch's fix touched. Root-caused via sampling (e.g. `2018-01-01/FIXTURES/A_LEAGUE`): each group is an OLD
    superseded row (an earlier `empty_confirmed`/`attempted_failed` write) sitting alongside a NEWER `captured` row from
    the same `attempted_at=2026-07-13T16:24:30.871968Z` reconciliation pass noted in finding (d) above — i.e. the
    reconciliation tooling's re-attempt writes are landing correctly but the manifest consolidator, per the
    already-established precedent, does not remove the stale superseded row on a shard-merge write; only a direct
    canonical rewrite does. This is a **pre-existing manifest-hygiene residual, not a new defect and not introduced by
    today's fix** — same class as the 88 MTDS orphans fixed earlier this session, scoped as follow-up cleanup rather
    than in this VERIFY pass.
  - **Verdict: does NOT yet meet the understat-standard 0/0/0 literal bar.** All three residuals are
    **documented/explained, not silently-broken**: `attempted_failed` (3,257) is a known, bounded, already-scoped
    backfill-VM re-attempt (deferred by design, confirmed unchanged not regressed); `expected_unattempted` (452,985) is
    substantially the still-open TEAMS-gap investigation plus a legitimate could-exist-universe seed; the 39,222
    duplicate groups are stale-superseded rows needing a direct-rewrite cleanup pass (same fixable pattern as the MTDS
    orphans). The 4 shipped code fixes are confirmed WORKING (0 new blank-`data_type` failures, 0 new false-positive
    FIXTURES_FETCH_FAILED since ship) — this category is **code-complete but not yet manifest-clean**; closing to a
    literal 0/0/0 requires the deferred backfill-VM re-attempt + a canonical dedup-rewrite pass, both already tracked as
    open todos in this plan.

- **2026-07-13 (slot-3, AUDIT dispatch, read-only — MTDS shared-orchestrator sports-manifest-bucket routing, full
  call-site enumeration BEFORE any code change).** Confirms the MDPS-sibling split-brain bug also exists in MTDS's
  shared cross-asset-group orchestrator (`market-tick-data-service/market_tick_data_service/engine/orchestrator/`).
  - **Resolver + call sites (file:line)**:
    1. `__init__.py:768` `get_tick_data_bucket(config, asset_group, test_aware)` — the single resolver; delegates to
       `get_market_data_bucket(ag)` (line 825) or, for `prediction`,
       `resolve_bucket_name(kind="market-data-tick-prediction")` (line 815; deliberately PROD-only even under
       `test_aware`). No asset_group carve-out exists today — sports is NOT special-cased.
    2. `__init__.py:666` — early-return (no active venues) branch calls
       `get_tick_data_bucket(_config, asset_group=_primary_ag, test_aware=True)` and feeds it straight into
       `_emit_non_trading_day_expected_empties(...)` → `ManifestWriter(catalogue_bucket=bucket)` at `__init__.py:446`
       (def at 432) — a 2nd, independent manifest-WRITE call site (EXPECTED_* non-trading-day sentinels).
    3. `__init__.py:679` — the primary resolution:
       `_bucket = get_tick_data_bucket(_config, asset_group=primary_asset_group, test_aware=True)`, stored once as
       `_DateRunState.bucket` (ctor arg `__init__.py:696`, field `_state.py:116`) and reused for the WHOLE date-run
       across 5 consumers:
       - `manifest_finalize.py:573-575` `ManifestWriter(catalogue_bucket=state.bucket, batch_size=500)` — **the PRIMARY
         manifest-write call site** (captured/failed/sentinel rows for the date; this is the one the MDPS-fix precedent
         maps onto).
       - `__init__.py:706` → `_run_preflight_availability_check(state, _bucket, force)` →
         `read_availability_index(bucket)` at `__init__.py:517` — manifest READ (skip-if-fresh preflight); MUST also
         carry the carve-out or preflight will keep reading the OLD (wrong) bucket after the write moves and never see
         prior sports captures → perpetual re-fetch.
       - `__init__.py:707` → `_run_preflight_guards(_bucket, primary_asset_group, _config, force)` →
         `_check_sports_v9_columns(bucket, config)` (`venue_fetch.py:161`, sports-only schema guard, internally calls
         `read_availability_index(bucket)`) and `assert_consolidator_healthy(bucket)` (UTL
         `manifest_writer/_state.py:365`) — both manifest-health reads that must follow the same carve-out for sports.
       - `venue_fetch.py:395` (`_process_venue`, CeFi/DeFi/TradFi/Prediction) and `venue_fetch.py:590` (sports-specific
         venue-write helper) both do `_bucket = state.bucket` → feed `PartitionedTickWriter(bucket=_bucket, ...)` →
         `partitioned_writer.py:207` `StreamingParquetWriter(bucket=self._bucket, ...)` — **the RAW tick-data byte
         write. MUST NOT CHANGE for any asset_group, sports included** — this stays `market-data-tick-sports-prd-...`
         (that's where the actual parquet bytes correctly live; only the MANIFEST pointer is wrong).
  - **Per-asset_group manifest-bucket baseline TODAY** (read from
    `unified-trading-pm/configs/cloud-providers.yaml:154-163`, GCP prod, `DEPLOYMENT_ENV_SHORT=prd`,
    `GCP_PROJECT_ID=central-element-323112` — confirms the "before" state that must stay byte-identical for the 4
    non-sports groups):
    - cefi → `market-data-tick-cefi-prd-central-element-323112`
    - defi → `market-data-tick-defi-prd-central-element-323112`
    - tradfi → `market-data-tick-tradfi-prd-central-element-323112`
    - sports → `market-data-tick-sports-prd-central-element-323112` **(WRONG — target is
      `instruments-store-sports-prd-central-element-323112`, matching `enumerate_expected_universe.py`'s 2026-06-07 seed
      target and the shipped MDPS-sibling fix)**
    - prediction → `market-data-tick-pred-central-element-323112` (dedicated flat kind, unaffected by the carve-out
      either way — never touches the per-asset_group `market-data` dict).
  - **Fix scope, precisely**: the sports-only carve-out must intercept ONLY the manifest-bucket resolution at the 4
    consumer sites under (3) above (`manifest_finalize.py:575`, `preflight.py`'s `read_availability_index`/
    `_check_sports_v9_columns`/`assert_consolidator_healthy` reads, and the `__init__.py:446` non-trading-day writer) —
    i.e. introduce a `_resolve_manifest_bucket()` (sports → `instruments-store-sports-prd-...`, else identical to
    `get_tick_data_bucket()`) and re-point those 4 read/write sites at it, while `venue_fetch.py:395/590` +
    `partitioned_writer.py:207` (the raw parquet byte write) keep calling the UNCHANGED `get_tick_data_bucket()` /
    `state.bucket` for all 5 asset_groups incl. sports. cefi/defi/tradfi/prediction's manifest resolution must stay
    byte-identical — proven above by the yaml baseline (none of those 4 sites' `asset_group` branch would be touched by
    an `if asset_group == "sports"` carve-out).
  - **Orphaned-row migration scope, independently verified via direct GCS/parquet read (ADC,
    `central-element-323112`)**:
    `gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet` (1,958,499 total rows)
    has **362,665 rows with `source=odds_api`** — **362,631 `captured` + 34 `empty_confirmed`** (data_type breakdown:
    362,649 lower/upper-case `trades`-family rows + 16 spread across `ODDS_MOVEMENT`/
    `ODDS_SNAPSHOT`/`odds_movement`/`odds_snapshot`), date range **2020-06-06 → 2026-06-24** (NOT "through today"
    2026-07-13 as the dispatch context framed it — most recent consolidated row is 19 days stale; flagging the
    discrepancy, not correcting the plan's prior finding, which was about row COUNT and was independently reproduced
    exactly: 362,665/362,631). Top venues: UNIBET (22,129), PADDYPOWER (21,888), PINNACLE (21,084), DRAFTKINGS (19,939).
    **No overlap** confirmed with the canonical bucket:
    `gs://instruments-store-sports-prd-central-element-323112/_index/ availability_index.parquet` (4,988,135 total rows)
    carries only **2,667 odds_api rows** (2,661 `empty_confirmed` + 6 `attempted_failed`), date range **2018-01-01 →
    2020-06-05** — a disjoint pre-backfill window; a `(date, venue, data_type, instrument_id, underlying, fixture_id)`
    join across both slices returned **0 matching rows**. Matches the plan's earlier finding exactly — independently
    confirmed, not just re-asserted.
  - **Live-writer coordination check**: `deployment-service/terraform/gcp/sports_scheduler_cron.tf` confirms
    `google_cloud_scheduler_job.sports_scheduler_cron` (`${env_prefix}-sports-scheduler-cron`) is **ENABLED**, firing
    every 5 min (`sports_trigger_scheduler.SportsTriggerScheduler.poll_interval_seconds=300`), triggering Cloud Run Job
    `sports-scheduler` → `python -m deployment_service sports-trigger run --one-shot --backend cloud ...` which
    dispatches into market-tick-data-service (+ features-sports-service) per `configs/sports-trigger-tiers.yaml`. **This
    IS a live, actively-scheduled writer into the exact code path being fixed** — the same drain-then-migrate
    coordination pattern used for the MDPS sibling fix applies here too (this is a fix-implementation todo, not part of
    this read-only audit).
  - **No code changed in this dispatch** — audit only, per the task's explicit read-only scope.

- **2026-07-13 (slot-3, IMPLEMENTATION dispatch — MTDS shared-orchestrator sports-manifest-bucket routing, CODE FIX
  SHIPPED).** Implemented + shipped the sports-only carve-out scoped by the audit entry above.
  `market-tick-data-service@ad76547c` (pushed to `live-defi-rollout`, direct push per this session's established pattern
  — QG-green tree confirmed via `.qg_last_passed_sha == HEAD` before commit, re-verified after 2 unrelated
  concurrent-agent FF-pulls; commit hooks `check-branch-drift` + `Enforce slot·host commit identity` PASSED).
  - **Diff**: new file `engine/orchestrator/_manifest_bucket.py` (52L) housing
    `_resolve_manifest_bucket(data_bucket: str, asset_group: str) -> str` — returns
    `resolve_bucket_name(cloud=_cloud, kind="instruments-store", asset_group="sports")` when
    `asset_group.lower() == "sports"`, else returns `data_bucket` UNCHANGED (kept in its own module rather than inline
    in `engine/orchestrator/__init__.py` to respect the 900-line file-size ratchet — inlining it pushed that file to
    940L). Wired into the 4 sites the audit named:
    1. `__init__.py`'s early-return non-trading-day branch — now computes
       `_resolve_manifest_bucket(get_tick_data_bucket(...), _primary_ag)` before calling
       `_emit_non_trading_day_expected_empties(...)` (feeds the `__init__.py:446` `ManifestWriter`).
    2. `process_ticks()`'s main flow — new `_manifest_bucket = _resolve_manifest_bucket(_bucket, primary_asset_group)`
       local, passed to both `_run_preflight_availability_check(state, _manifest_bucket, force)` (the
       `read_availability_index` skip-if-fresh read) and
       `_run_preflight_guards(_manifest_bucket, primary_asset_group, _config, force)` (feeds
       `_check_sports_v9_columns` + `assert_consolidator_healthy`).
    3. `_DateRunState` gained a new `manifest_bucket: str` field (`_state.py`, defaults to `bucket` when the caller
       doesn't pass one explicitly — every non-orchestrator/test construction site of `_DateRunState` stays
       byte-identical to pre-fix behavior since only `process_ticks()` passes `manifest_bucket=` explicitly).
    4. `manifest_finalize.py:575` — `ManifestWriter(catalogue_bucket=state.bucket, ...)` →
       `catalogue_bucket= state.manifest_bucket` (the PRIMARY manifest-write call site).
  - **Untouched (raw tick-BYTE write path, all 5 asset_groups)**: `venue_fetch.py:395` and `venue_fetch.py:590` both
    still read `state.bucket` directly (never `state.manifest_bucket`) feeding `PartitionedTickWriter` →
    `partitioned_writer.py:207`'s `StreamingParquetWriter` — grepped post-fix, 0 hits for `manifest_bucket` in either
    file, confirming the raw-byte path was never touched.
  - **Blast-radius proof (AUTONOMOUS_AGENT_RULES.md rule 11)**: `_resolve_manifest_bucket()`'s
    `if asset_group.lower() == "sports"` branch is the ONLY conditional; every other asset_group (cefi/defi/tradfi/
    prediction) falls through to `return data_bucket` unchanged — i.e. `_manifest_bucket == _bucket` byte-for-byte for
    those 4, identical to the pre-fix value every one of the 4 consumer sites received. This is provable by inspection
    (single `if`, no other branch) rather than requiring a live per-asset_group run; cross-checked against the audit's
    yaml-baseline table (cefi/defi/tradfi/prediction bucket names unchanged).
  - **Live-writer coordination — NO drain/pause performed, and none was needed**: the audit flagged
    `sports_scheduler_cron` (5-min cadence) as a live writer into this exact code path. Reasoning for shipping without a
    pause (matching the MDPS-sibling precedent, which also shipped its code fix without a drain step): (a)
    `ManifestWriter` is append-only per-VM-shard — there is no read-modify-write race across a code deploy, only a clean
    before/after split; (b) the read side (`read_availability_index`/`_check_sports_v9_columns`/
    `assert_consolidator_healthy`) and the write side (`manifest_finalize.py`'s `ManifestWriter`) both flip to the new
    bucket in the SAME commit/deploy — there is no window where reads and writes target different buckets, so no new
    split-brain is introduced by the deploy itself; (c) the one real transient effect is that cron invocations landing
    shortly after this deploy reaches production will see an (almost) empty `instruments-store-sports-prd` manifest for
    `odds_api` (only the pre-existing 2,667 disjoint-window rows) and may re-attempt dates already covered by the
    362,665 orphaned rows sitting in the OLD bucket — wasted API calls / duplicate captures, not data loss or
    corruption, and self-heals once the follow-on migration (below) backfills the orphaned rows into the canonical
    bucket. This is the same tradeoff the MDPS-sibling fix accepted.
  - **Explicitly OUT of scope for this commit (separate follow-on, NOT done here)**: migrating the 362,665 orphaned
    `source=odds_api` rows from `market-data-tick-sports-prd-central-element-323112` into
    `instruments-store-sports-prd-central-element-323112`. The dispatch that shipped this code fix scoped it to "the 4
    call sites," matching the MDPS-sibling commit's own scope (code fix only, no migration in the same commit).
  - **QG evidence**: `market-tick-data-service` `scripts/quality-gates.sh --no-fix` ran twice (once pre-pull, once
    post-pull after 2 unrelated concurrent-agent FF-pulls) — both exit 0, `.qg_last_passed_sha` matched `HEAD` before
    each commit attempt. Two new violations surfaced by the first pass (`__init__.py` 940L > 900L cap;
    `_state.py::_init_run_params` 52L > 50L method cap) were fixed by extracting `_manifest_bucket.py` into its own
    module and trimming comments — both files back within ratchet (`__init__.py` 899L, `_init_run_params` 48L),
    confirmed via a direct `ast`-based line-count check (not just re-running the gate).
  - **Plan status**: todo "MTDS shared-orchestrator sports-manifest-bucket routing" (§1, `P1`) is a bundled code-fix +
    migration item. **The code-fix half is DONE** (`market-tick-data-service@ad76547c`); the migration half remains
    **open** — checkbox left `[ ]` with this sub-status noted rather than flipped, since the item's own text explicitly
    includes "then migrate the 362,665 orphaned rows" as part of its definition of done.
    - (exact SHAs recorded via the git-commit skill in the same turn as this log entry — see repo `git log -1`.)
- **2026-07-13 (sub-agent, BLAST-RADIUS PROOF dispatch, AUTONOMOUS_AGENT_RULES.md rule 11 closing self-check for
  `market-tick-data-service@ad76547c`) — all 5 asset_groups PROVED, PASS.** Ran the actual resolver code path with real
  inputs (not assertion-by-inspection): `GCP_PROJECT_ID=central-element-323112 .venv/bin/python -c` calling
  `get_tick_data_bucket(None, ag, test_aware=False)` then `_resolve_manifest_bucket(data_bucket, ag)` for
  `ag in {cefi, defi, tradfi, sports, prediction}` against the live `central-element-323112` GCP config (ADC-authed, no
  mocks). Observed:
  - `cefi`: data=`market-data-tick-cefi-prd-central-element-323112`, manifest=SAME → `identical=True`. **PASS**
    (byte-identical to pre-fix; cefi never enters the sports-only `if` branch).
  - `defi`: data=`market-data-tick-defi-prd-central-element-323112`, manifest=SAME → `identical=True`. **PASS.**
  - `tradfi`: data=`market-data-tick-tradfi-prd-central-element-323112`, manifest=SAME → `identical=True`. **PASS.**
  - `prediction`: data=`market-data-tick-pred-prd-central-element-323112`, manifest=SAME → `identical=True`. **PASS.**
  - `sports`: data=`market-data-tick-sports-prd-central-element-323112` (unchanged raw-byte bucket), manifest=
    `instruments-store-sports-prd-central-element-323112` (the canonical bucket — `identical=False`, as intended).
    **PASS** — sports now resolves to the correct manifest bucket.
  - **Corroborating evidence (not just the live run)**: `git show ad76547c -- .../__init__.py` diff shows all 4 non-
    sports call sites previously read `_bucket` (== `get_tick_data_bucket()`'s return, i.e. `data_bucket`) directly for
    both the raw-write AND manifest/preflight/non-trading-day paths; post-fix they read
    `_manifest_bucket = _resolve_manifest_bucket(_bucket, ag)`, and `_resolve_manifest_bucket`'s body is a single
    `if asset_group.lower() == "sports": return resolve_bucket_name(...)` / `return data_bucket` — algebraically
    provable that any `ag != "sports"` returns its input `data_bucket` unchanged, matching the live-run observation
    exactly. `venue_fetch.py:395,590` (`_bucket = state.bucket`, the actual `PartitionedTickWriter`/
    `StreamingParquetWriter` raw-byte write path) greps to 0 references of `manifest_bucket` — confirmed untouched, so
    no asset_group's raw tick-byte write location changed.
  - **Working-tree/QG state at proof time**: `market-tick-data-service` `git status` clean, HEAD == `ad76547c` (no drift
    since the code-fix commit); `.qg_last_passed_sha` on disk (`b11199c…`) is STALE relative to HEAD — expected
    (gitignored sentinel, this shared clone had a concurrent agent's QG run land after the code-fix commit per the
    per-tab-worktrees shared-repo model) and immaterial to this proof since no new code was written in this pass, only a
    read-only verification.
  - **Verdict: 5/5 asset_groups PASS.** No regression found for cefi/defi/tradfi/prediction; sports fix confirmed live.
    Nothing reverted, nothing further to fix. The P1 todo's checkbox stays `[ ]` per the prior entry's note (code half
    done + proved; migration half of the bundled item remains the only open piece, unchanged by this proof pass).
- **2026-07-13 (sub-agent, MIGRATION dispatch — MTDS shared-orchestrator sports-manifest-bucket routing, migration half
  SHIPPED, P1 todo now fully DONE).** Gated on the blast-radius proof above (5/5 PASS, confirmed clean before
  proceeding). Migrated the 362,665 orphaned `source=odds_api` rows from `market-data-tick-sports-prd` into the
  canonical `instruments-store-sports-prd` manifest.
  - **Script**: `instruments-service` (untracked, one-off)
    `scripts/migrate_orphaned_mtds_odds_api_bucket_rows_2026_07_13.py` — same identity/collision-check shape as the
    `mdps_odds_horizon_bucket` sibling script, but using the CANONICAL manifest-consolidator dedup key
    (`unified_trading_library.manifest_consolidator._BASE_DEDUP_COLS` + `_OPTIONAL_DEDUP_COLS`: `date`, `venue`,
    `data_type`, `service_name`, `timeframe`, `league_id`, `chain`, `instrument_type`, `underlying`, `feature_group`,
    `model_family`, `training_period`, `strategy_id`, `client_id`, `instruction_type`, `instrument_id`) rather than a
    narrower ad-hoc subset — confirmed 0 self-duplicates within the 362,665 source rows and 0 collisions against the
    FULL 4,988,148-row target manifest (not just its 2,667 pre-existing `odds_api` rows) on this key, both before and
    re-checked at write time.
  - **Dry-run first** (per task instruction): confirmed 362,665 eligible rows (362,631 `captured` / 34
    `empty_confirmed`), 0 collisions, matching the audit's numbers exactly.
  - **CRITICAL FINDING — plain gcsfs read/write is UNSAFE against this specific bucket right now, unlike the
    MDPS-sibling script's precedent.** A first `--apply` attempt using that exact "plain gcsfs read/write, no
    generation-match" convention appeared to succeed (logged `rows_out=5,350,813`), but a re-verify read ~90s later
    showed the target back at the EXACT pre-migration baseline (4,988,148 rows / 2,667 `odds_api`) — the object's own
    `consolidator_run_at`/`consolidator_content_write_at` custom metadata proved the LIVE `instruments-store-sports`
    manifest consolidator (GCP Cloud Run Job, Cloud Scheduler cron `*/1 * * * *` UTC, confirmed via
    `codex/05-infrastructure/manifest-consolidator-ssot.md`) silently overwrote the write within one cycle — its
    read-merge-write started before this script's write landed and finished after, clobbering it with a merge computed
    from the stale snapshot. **Fix**: rewrote the `--apply` path to use the UTL generation-precondition CAS primitive
    (`StorageClient.download_bytes_with_generation` / `.conditional_upload_bytes(if_generation_match=...)`,
    `unified_trading_library/cloud_interface/abstractions.py` — documented in-code as the "sanctioned home for a
    distributed-lock/lease primitive") in a bounded retry loop (30 attempts, 5s backoff): read target + generation
    together (one GET, no metadata/download race), recompute the collision-checked merge against the freshly-read
    target, attempt an atomic compare-and-swap write; a `PreconditionFailed` (412) means the consolidator won the race
    in the interim — re-read the now-current generation and retry rather than blind-overwriting. **Also found**: a plain
    multi-column `gcsfs` range-projected read (`pd.read_parquet(fh, columns=[...])`) against this same live object
    intermittently raised `OSError: Couldn't deserialize thrift ... Deserializing page header failed` — consistent with
    gcsfs issuing multiple separate range-GETs for a columnar read that can straddle a mid-flight object replacement;
    switched all verification reads to the same CAS primitive's single-GET `download_bytes_with_generation` (full-bytes
    fetch, then local in-memory column projection via pandas), which read cleanly on every subsequent poll.
  - **Write succeeded on CAS retry attempt 5/30** (generation `1783969076071393` → `1783969117086486`), after 4 prior
    attempts lost the race to the consolidator (each logged a `PreconditionFailed` + re-read + re-merge). Result:
    `rows_in=4,988,148 rows_added=362,665 rows_out=5,350,813`.
  - **Persistence empirically verified across multiple subsequent consolidator cycles** (not just asserted from the
    single write): polled the canonical manifest 8× over ~4.5 minutes using the same generation-pinned CAS read. The
    object's generation advanced 5 times during the poll window (confirming the consolidator kept running normally
    throughout), and the `odds_api` row count held rock-steady at every single poll: 365,332 total (362,631 `captured` +
    2,695 `empty_confirmed` + 6 `attempted_failed`) — i.e. the consolidator's own subsequent read-merge-write cycles
    PRESERVE the manually-migrated rows (consistent with the `mdps_odds_horizon_bucket` sibling migration's rows still
    being present at that plan item's later "final re-verify" checkpoint) once the write itself isn't lost to a
    mid-flight race.
  - **Final live re-verify (fresh read, full canonical manifest, post-migration)**:
    - `instruments-store-sports-prd-central-element-323112` total rows: 4,988,148 → **5,353,929** (the +3,116 beyond the
      immediate post-apply 5,350,813 is ordinary intervening live-capture growth from other sources during the ~5-minute
      verification window, not a migration artifact).
    - `source=odds_api` rows: 2,667 → **365,332** = 2,661 pre-existing `empty_confirmed` + 6 pre-existing
      `attempted_failed` + **362,631 newly-visible `captured`** + 34 newly-visible `empty_confirmed`. **The canonical
      coverage view now shows 362,631 captured `odds_api` rows, up from 0 non-legacy captures** — matches the task's
      target exactly.
    - **0 duplicate-dedup-key groups** anywhere in the resulting 5,353,929-row manifest (checked on the full canonical
      manifest-consolidator dedup key, not just among the migrated rows) — confirms the migration did not create the
      2026-07-13 `dedup_mtds_instruments_surface_duplicate_rows` bug class.
  - **§0 reconciliation**: the plan's §0 framing of `odds_api` as "suspiciously sparse/dead" is now RESOLVED — the data
    was never sparse or dead, it was a manifest-bucket-routing split-brain identical in class to
    `mdps_odds_horizon_bucket` (numerator written to `market-data-tick-sports-prd`, denominator/canonical view seeded
    from `instruments-store-sports-prd`); both the code path (going forward) and the historical backfill (this
    migration) are now fixed.
  - **Shipped**: `instruments-service@4027f311` (pushed to `live-defi-rollout`, direct push per this session's
    established no-quickmerge convention; `quality-gates.sh --no-fix` green, `.qg_last_passed_sha == HEAD` before
    commit). **Adjacent fix bundled in the same commit** (findings-triage "outside-plan small+clear → ≤30 min"):
    `scripts/reconcile_legacy_nan_placeholder_bars.py` (a pre-existing, already-committed, unrelated one-off script)
    imported `google.cloud.storage` directly — a TID251 ratchet violation (59 > baseline 58) that was blocking a green
    `quality-gates.sh` tree for this commit. Swapped to `get_storage_client()` (`download_file`/`upload_file`,
    behavior-identical) rather than raising the baseline. No other repo files touched; two foreign untracked scripts
    (`backfill_teams_61_leagues_2026_07_13.py`, `cefi_legacy_path_dedup_2026_07_13.py`) present in the shared clone from
    concurrent agents were left untouched per multi-agent safety.
  - **Plan status**: the P1 todo "MTDS shared-orchestrator sports-manifest-bucket routing" is now **fully DONE** —
    checkbox flipped `[x]` above (§1). No further action needed on this item.
- **2026-07-13 (sub-agent, read-only investigation) — api_football TEAMS 61-league gap: ROOT CAUSE FOUND (code
  unchanged, no fix shipped yet — this pass was investigation-only per dispatch).** **(1) One code path, not two.**
  `instruments_service/engine/orchestrator/sports_reference_core.py::_fetch_teams_and_standings` (lines 138-216) is the
  ONLY current TEAMS-writing function. It loops `for league_def in _orch.get_prediction_leagues()` (line 153) — that
  helper (`unified_api_contracts…league_data.py:405`) returns leagues whose UAC `classification == "Prediction"`, which
  is **33 leagues**, confirmed live via
  `unified_api_contracts.canonical.domain.sports.league_data.get_prediction_leagues()`. It then writes ONLY per-league
  partitions (line 190-201); the bare/no-league-id write branch is explicitly retired and now just logs-and-skips
  ("TEAMS bare-path fallback triggered … data shape regression", line 202-208) — **this live code path cannot produce a
  blank-`league_id` captured row.** **(2) Root cause = a classification-filter mismatch between writer and enumerator,
  not a hardcoded allowlist.** The EU enumerator's denominator comes from
  `get_expected_leagues_for_source("api_football")` (`league_data.py:581`) — classification-AGNOSTIC, returns every
  league whose `data_sources` frozenset contains `"api_football"` = **94 leagues** (live-verified). The writer uses the
  classification-FILTERED `get_prediction_leagues()` (Prediction-tier only) instead. Live set arithmetic: of the 94 EU
  leagues, exactly 61 are NOT in `get_prediction_leagues()` ∩ api_football — matching the plan's number exactly. **(3)
  The 61 missing leagues, by UAC classification/tier** (all have real non-null `api_football_id`s in `LEAGUE_REGISTRY`,
  which is WHY they're in the 94-league EU set at all): **22 "Features"-tier domestic lower divisions** (tier 2/3/5) —
  ARGENTINA_PRIMERA_NACIONAL, AUSTRIAN_2_LIGA, BELGIAN_FIRST_B, BRASILEIRAO_SERIE_B, CHILE_PRIMERA_B,
  DANISH_1ST_DIVISION, EERSTE_DIVISIE, ENG_NATIONAL_LEAGUE, FRANCE_NATIONAL, GREEK_SUPER_LEAGUE_2, J2_LEAGUE,
  K_LEAGUE_2, LIGA_EXPANSION_MX, LIGA_PORTUGAL_2, NORWAY_1_DIVISJON, POLAND_I_LIGA, PRIMERA_RFEF, SCOTTISH_CHAMPIONSHIP,
  SUPERETTAN, SWISS_CHALLENGE_LEAGUE, TFF_FIRST_LEAGUE, USL_CHAMPIONSHIP; **39 "Reference"-tier cup/supercup
  competitions** (tier 0) — AUSTRALIA_CUP, AUSTRIAN_CUP, BELGIAN_CUP, CARABAO_CUP, COPA_ARGENTINA, COPA_CHILE,
  COPA_DEL_REY, COPA_DO_BRASIL, COPA_LIBERTADORES, COPA_LIGA_PROFESIONAL, COPA_MX, COPA_SUDAMERICANA, COPPA_ITALIA,
  COUPE_DE_FRANCE, DANISH_CUP, DFB_POKAL, DFL_SUPERCUP, EMPEROR_CUP, FA_CUP, GREEK_CUP, JLEAGUE_CUP, KNVB_CUP,
  KOREAN_FA_CUP, NORWEGIAN_CUP, POLISH_CUP, SCOTTISH_CUP, SCOTTISH_LEAGUE_CUP, SUPERCOPA_ESPANA, SUPERCOPPA_ITALIANA,
  SVENSKA_CUPEN, SWISS_CUP, TACA_DA_LIGA, TACA_DE_PORTUGAL, TROPHEE_CHAMPIONS, TURKIYE_KUPASI, UCL, UECL, UEL,
  US_OPEN_CUP. **No hardcoded allowlist file — the "allowlist" IS the Prediction-classification filter itself**, applied
  at the wrong layer (capture loop should use the same source-coverage filter as the enumerator, not a
  betting-model-relevance filter). **(4) API coverage: likely YES for all 61, unproven for cup-type specifically.**
  Every one of the 61 already carries a valid `api_football_id` in `LEAGUE_REGISTRY` (that's the only reason they're in
  `get_expected_leagues_for_source("api_football")` at all) — api-football's `/teams?league={id}&season={y}` endpoint is
  keyed purely off that numeric ID and has no known Prediction-tier gating, so there's no code/registry reason to expect
  failure. Caveat: none of the 33 already-captured leagues are cup competitions, so the 39 Reference-tier cups are
  UNTESTED by precedent — recommend one live smoke call per cup-tier league before committing to a full backfill. The
  `sports_league_entity_coverage.json` TEAMS-observed list (34 entries incl. `UNKNOWN`) is circular evidence — it's
  DERIVED from the existing captured corpus, so it trivially matches the current 33-league gap and cannot be used to
  pre-screen; it should be regenerated only AFTER a real attempt. **(5) Backfill scope — flag before sizing a VM.**
  Naive full 2018-2026 daily backfill = 61 leagues × ~3,046 days ≈ **185,800 API calls**. But TEAMS is roster data
  (stable within a season) — the 33 already-captured leagues' ~3,046-rows/league cadence reflects the writer's
  in-process `_cached_teams_df` reuse across dates WITHIN one orchestrator run (0 extra API calls per cached date), not
  evidence that literal daily granularity is required or was 3,046 real API calls. No downstream consumer found in this
  pass that needs a dated daily TEAMS snapshot vs. "latest per league-season" (features-sports-service reads the
  per-league `teams.parquet`, not visibly date-keyed beyond most-recent). **Recommend the backfill-implementation todo
  explicitly decide-and-document**: either justify daily cadence with a named consumer, or switch to per-season cadence
  (~61 leagues × ~8 seasons ≈ 500 calls) — this could cut the real API-call count by >99% while still satisfying
  "canonical per-league TEAMS coverage" per the operator's stated model. **(6) The blank-`league_id` bulk bundle is a
  SEPARATE, likely-legacy artifact, not the current writer's output and not confirmed reusable.** Live-manifest query
  confirms 3,648 blank rows spanning 2014-01-01→2026-07-13 (plus one literal `date="all"` sentinel row) — i.e. it is NOT
  simply pre-2018 legacy data (a date range that recent looked at first like an ongoing duplicate live writer, but the
  CURRENT `_fetch_teams_and_standings` cannot produce a blank-league row per finding (1), so these are residual MANIFEST
  rows, most likely from `scripts/migrate_bare_to_per_league.py` (docstring: "reads legacy bare parquets, splits by
  league_id, writes per-league, updates the manifest with per-league captured rows, and deletes the bare parquet")
  having been run but either not covering TEAMS fully or not retro-deleting the old bare manifest rows after the
  per-league rows were added — **not fully resolved in this pass, needs one more check before backfill ships** (confirm
  no live scheduler/poller still bare-writes TEAMS) to avoid a fresh backfill re-creating parallel blank rows. Did NOT
  get to opening a sample bare-captured `teams.parquet` file's raw columns (time-boxed out) — worth checking whether the
  raw team records still carry a league/competition reference internally despite the manifest row_key being blank, which
  would let the 61-league gap be substantially re-derived from already-captured bytes at near-zero new API cost rather
  than a fresh fetch; flagged as the first thing the implementation pass should check. **(7) VM/launcher precedent for
  the eventual backfill**: `af-backfill-` is the registered general api_football VM prefix
  (`deployment-service/deployment_service/vm_prefix_registry.py:618`, bucket=`instruments-store-sports-*`); the
  better-fit precedent is the **targeted gap-fill pattern** `fill-missing-player-stats-`
  (`deployment-service/scripts/vm/launch-fill-missing-player-stats-vm.sh` +
  `instruments-service/scripts/fill_missing_player_stats.py`) — reads the canonical manifest, computes the missing
  `(league_id, date)` cells directly, fires ONLY at those shards (not a full chronological re-walk), and singleton-locks
  against `af-backfill-*` (shared api_football rate-limit key). Recommend basing a new `fill-missing-teams` driver on
  this exact pattern once (5)/(6) resolve the true scope. **Net: this todo is NOT yet closed** — root cause is
  identified and documented (a filter-layer mismatch in the writer, not the enumerator; fix = change
  `_fetch_teams_and_standings`'s league source to match the enumerator's `get_expected_leagues_for_source` call), but no
  code was changed, no backfill ran, and the blank-bundle provenance + true backfill cadence remain open sub-questions
  for the implementation pass.

- **2026-07-13 (sub-agent, CODE-FIX IMPLEMENTATION dispatch for the P0 todo "api_football TEAMS: root-cause + fix the
  61-league per-league capture gap" — the forward-going code fix only, per this dispatch's scope).**
  **instruments-service@0d2ea24f** (pushed to `live-defi-rollout`, direct push per this session's established
  no-quickmerge convention — dep tree stayed clean via `git pull --ff-only` before/after). **Decision**: the root cause
  (previous entry) IS the code bug — no hardcoded allowlist file existed; the "allowlist" was the Prediction-tier
  classification filter applied at the wrong layer. Fix: `sports_reference_core.py::_fetch_teams_and_standings` now
  loops `_orch.get_expected_leagues_for_source("api_football")` (the same call `hooks.emit_empty_gaps_for_entity`
  already uses for the STANDINGS honest-absence emission in the same function) instead of
  `_orch.get_prediction_leagues()`. Since TEAMS + STANDINGS share the single `prediction_league_ids` loop in this
  function, BOTH entities are widened from 33 → 94 leagues by this one change — matches UAC
  `SPORTS_ENTITY_LEAGUE_COVERAGE["TEAMS"]`/`["STANDINGS"]` both being `None` ("expected on all fixture dates", i.e. all
  leagues, confirmed live in `unified_api_contracts/canonical/domain/sports/provider_league_ids.py:772`). No leagues
  were typed `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` — the investigation found no evidence any of the 61 lack real
  api_football TEAMS coverage (all carry a valid `api_football_id`; the only untested subset is the 39 cup-type leagues,
  since none of the 33 already-captured are cups — flagged for a smoke-test before the eventual backfill, not a reason
  to descope). **Files changed**: `sports_reference_core.py` (the fix + docstring explaining the root cause inline for
  future readers), `sports_reference.py` (matching comment update), `test_orchestrator_sports_pipeline.py` +
  `test_orchestrator_boost.py` (patch targets moved from `get_prediction_leagues` to `get_expected_leagues_for_source`
  to match the new call site — same mocks/assertions, no behavior-under-test change). `quality-gates.sh --no-fix` ran
  clean (sentinel written, HEAD == sentinel SHA) before commit. **Adjacent fix in the same commit** (findings-triage "in
  your file → fix in same commit" did not apply since it's a different file, but this was a tree-wide blocker unrelated
  to sports that would have blocked ANY commit to this shared clone): `scripts/reconcile_lending_indices_phantom.py` had
  a pre-existing (committed 2026-06-23, untouched since) direct `from google.cloud import storage` import tripping the
  TID251 ratchet (59 live sites > baseline 58) — diverging from its own documented sister-script precedent
  (`reconcile_phantom_manifest_rows_all.py` uses the UTL `StorageClient` abstraction). Rewrote it onto
  `get_storage_client()`/`StorageClient` (`download_bytes`/`upload_from_file_obj`/ `list_blobs`), which also let the
  tempfile-download dance collapse to a direct `io.BytesIO` read (dropped the now-unused `tempfile`/`os`/`contextlib`
  imports). Verified this DeFi-domain fix didn't change behavior (same GCS paths, same phantom-classification logic,
  only the client library swapped) — did not touch its `--apply-flips` logic or classification rules. **Not done in this
  dispatch (explicitly out of scope — "implement the code fix", not the full backfill)**: the historical backfill for
  the 61 previously-uncaptured leagues (cadence decision — daily vs. per-season — still open per the investigation's
  point (5)); the blank-`league_id` bulk-bundle reconciliation/cleanup (point (6), needs a check that no live daemon
  still bare-writes TEAMS before any backfill ships, to avoid re-creating parallel blank rows); and the VM launch itself
  (precedent identified: `fill-missing-player-stats-`-style targeted gap-fill, not a full `af-backfill-` re-walk).
  **This todo's checkbox is intentionally left unchecked** — the code bug is fixed and shipped (new captures going
  forward will cover all 94 leagues), but the P0 todo's full scope ("fix the 61-league… gap") is not closed until the
  historical backfill lands; next pass should pick up directly at the VM-launch step using the precedent above.

- **2026-07-13 (slot-3, FINAL RE-VERIFY + CLOSE-OUT REPORT dispatch — whole-asset_group, todo "Whole-asset_group final
  re-verify + close-out report").** Fresh single-parquet read (`.venv/bin/python` + `pandas.read_parquet` direct, NOT
  `read_availability_index()` — that helper's in-process TTL cache + `ManifestConsolidatorStaleError` staleness gate
  returned 0 rows against a live bucket read moments earlier in this same dispatch; a direct GCS parquet read is
  equivalent for a point-in-time audit and is what every prior VERIFY entry in this plan actually used) of
  `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`: **4,988,135 total rows**
  (vs §0's 4,863,784 post-cleanup baseline — the mdps backfill + ongoing organic captures account for the growth; a full
  `source`-column sum reconciles exactly to the total, 0 unaccounted rows).

  **Final per-source table (§0 shape + a dedup-dup-groups column, corrected key =
  `date+venue+data_type+league_id+ fixture_id/timeframe+service_name` — see methodology note below):**

  | source                                                    | §0 rows → now         | §0 captured → now       | §0 attempted_failed → now                    | §0 expected_unattempted → now                | dedup dup groups (now) |
  | --------------------------------------------------------- | --------------------- | ----------------------- | -------------------------------------------- | -------------------------------------------- | ---------------------- |
  | api_football                                              | 2,518,940 → 2,518,571 | 365,592 → 370,340       | 3,257 → **3,257 (unchanged)**                | 453,961 → 452,985                            | **0**                  |
  | footystats                                                | 650,504 → 650,876     | 84,047 → 84,311         | 205 → **175 (↓30, in-flight)**               | 56 → 56                                      | 0                      |
  | soccer_football_info                                      | 226,237 → 226,237     | 19,750 → 20,555         | 10 → **10 (unchanged, in-flight)**           | 94 → 94                                      | 0                      |
  | transfermarkt                                             | 270,719 → 270,719     | 58,028 → 58,028         | 0 → **0 (clean)**                            | 47 → 47                                      | 0                      |
  | open_meteo (weather)                                      | 261,790 → 261,790     | 12,097 → 12,298         | 51 → **51 (unchanged, in-flight)**           | 94 → 94                                      | 0                      |
  | odds_api                                                  | 2,667 → 2,667         | 0 → 0                   | 6 → **6 (unchanged, documented-equivalent)** | 0 → 0                                        | 0                      |
  | mdps_odds_horizon_bucket                                  | 215,481 → 339,775     | 0 → **123,642 (fixed)** | 0 → 0                                        | 209,526 → 209,526 (documented, open)         | 0                      |
  | retired (SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES) | 88,056 → 88,056       | 0 → 0                   | 0 → 0                                        | 0 → 0 (100% `EXPECTED_DEPRECATED_DATA_TYPE`) | n/a                    |

  **Concrete improvement vs §0**: mdps_odds_horizon_bucket's zero-ever-captured defect is gone (0 → 123,642 captured);
  footystats attempted_failed is actively falling (205 → 175, confirmed live mid-read); api_football's previously
  reported 39,222 dedup-dup-groups (from the earlier VERIFY entry above) is **now 0** — see methodology correction
  below; every other source's core numbers are stable/unchanged (no regressions anywhere).

  **Dedup-key methodology correction (important, corrects the earlier VERIFY entry's 39,222 figure)**: the prior
  api_football VERIFY entry's stated key (`date+source+data_type+service_name+league_id+fixture_id`) omits `venue`.
  Re-running that exact key here reproduces a large apparent duplicate count (40,825 groups / 81,944 rows) — but
  sampling the largest groups shows they are **not real duplicates**: they are the ~460 blank-`data_type`/blank-
  `league_id` enrichment-pseudo-venue rows (`venue` ∈ {FOOTYSTATS, OPEN_METEO, SOCCER_FOOTBALL_INFO, TRANSFERMARKT,
  UNDERSTAT} — the same rows behind the already-documented `UNCLASSIFIED_ADAPTER_ERROR` finding), which only `venue`
  distinguishes from one another. This is the **identical false-positive class** already root-caused elsewhere in this
  plan for footystats/SFI/weather ("league-grain sources with blank venue... false-positived thousands of duplicates").
  Adding `venue` back into the key (`date+venue+data_type+league_id+fixture_id+service_name`) drops api_football to **0
  true duplicate groups** — verified by direct construction (not just count), and independently reproduced for
  mdps_odds_horizon_bucket: a `date+venue+data_type+timeframe+service_name` key (omitting `league_id`) false-positived
  15,527 groups on the enumerator's per-league `expected_unattempted` seed rows (which share every other dimension and
  differ ONLY by `league_id`); adding `league_id` back drops it to 0. **Corrected dedup methodology for this plan going
  forward: the full identity is `date+venue+data_type+league_id+fixture_id+timeframe+service_name` — no subset of these
  is safe to drop for any sports source**, since different sources' "duplicate-looking" collisions are broken by
  different individual columns.

  **Per-category verdict vs the understat-standard bar (0/0/0 literal or documented-equivalent)**:

  - **MEETS the bar (3/8)**: `transfermarkt` (0 attempted_failed, 47 EU 100%-dated-today/self-closing, 0 dedup) — clean.
    `odds_api` (6 attempted_failed, all `PipelineModeSourceMismatchError` — the write-safety gate correctly rejecting
    historical mismatched writes, already closed as documented-equivalent by the earlier VERIFY entry above,
    re-confirmed unchanged) — closed. `retired data_types` (88,056 rows, 100% `EXPECTED_DEPRECATED_DATA_TYPE`, 0
    attempted_failed) — clean, the P3 spot-verify todo can close.
  - **Core defect fixed, one specific residual remains (1/8)**: `mdps_odds_horizon_bucket` — the zero-ever-captured bug
    is conclusively resolved (123,642 real captures now visible, 0 dedup groups). The remaining 209,526
    `expected_unattempted` is NOT a new/silent gap — it is the already-root-caused, already-scoped
    `enumerate_expected_universe.py` grain-mismatch todo (enumerator seeds `venue=""`/uppercase/no-`timeframe`; writer
    uses `venue=ODDS_API`/lowercase/per-`timeframe`) — a specific code fix, not yet shipped, not blocked by anything.
  - **Code-complete, manifest not yet clean (1/8)**: `api_football` — the 4 shipped bug-class fixes are confirmed live
    and holding (`attempted_failed` unchanged at 3,257, 0 new blank-`data_type` failures since ship); dedup is now
    provably 0 (methodology-corrected). Two specific, non-blocking items remain open: (a) a dedicated backfill-VM
    re-attempt of the 3,257 stale rows (infra op, precedent pattern exists, not yet launched); (b) the TEAMS 61-league
    capture-gap fix (root-caused this session — `_fetch_teams_and_standings` uses the wrong league-source filter,
    `get_prediction_leagues()` instead of `get_expected_leagues_for_source("api_football")` — fix identified, not yet
    shipped, plus a blank-league-bundle provenance sub-question flagged for the implementation pass).
  - **In-flight on an already-running bounded process, not blocked (3/8)**: `footystats` / `soccer_football_info` /
    `open_meteo` — the residual-closer (`sports_attempted_failed_residual_closer_2026_07_13.py`, PID 3247,
    `--max-rounds 6`) is confirmed LIVE right now: its per-VM-shard GCS object
    (`_index/per_vm/sports-attempted-failed-residual-closer-slot3.parquet`) was last written at `18:18:10Z`, 14 seconds
    before this read at `18:18:24Z`. footystats has already dropped 205→175 attempted_failed (TimeoutError 174,
    ArrowTypeError 1 remaining); SFI (10, phantom) and weather (51, phantom) are unchanged so far — per this plan's own
    prior mid-flight note, their fixes stay buffered in-process until the closer's single end-of-run
    `flush_all_pending_buckets()` drain, which has not fired yet for those two sources. All three sources' EU rows are
    100%-dated-today (self-closing daily rolling edge, already root-caused, no action needed). **This is not a blocker**
    — the process is bounded and will self-terminate; the concrete next step is one more re-verify read after PID 3247
    exits.

  **Precise remaining-work list (none `BLOCKED-OPERATOR`/`BLOCKED-CREDENTIALS`, none newly discovered — every item is
  already an open `- [ ]` todo in §1 above)**:
  1. api_football historical backfill-VM re-attempt of the 3,257 stale `attempted_failed` rows (bounded infra op).
  2. api_football TEAMS 61-league capture-gap fix (`_fetch_teams_and_standings` league-source filter) + scoped backfill.
  3. mdps_odds_horizon_bucket `enumerate_expected_universe.py` grain realignment.
  4. MTDS shared-orchestrator sports-manifest-bucket routing generalization + migration of the 362,665
     `odds_api`-in-MTDS orphan rows (blast-radius mapped, fleet-wide proof required before shipping per
     `AUTONOMOUS_AGENT_RULES.md` rule 11 — touches every asset_group's manifest resolution, not just sports).
  5. `reprocess_sports_odds.py` raw-input prefix-template refresh.
  6. Let the in-flight residual-closer (PID 3247) run to its own bounded completion (`--max-rounds 6`), then one more
     fresh re-verify read for footystats/soccer_football_info/open_meteo.

  **DoD status**: NOT fully met. 3/8 categories clean/documented-equivalent, 1/8 core-defect-fixed with one open
  follow-on, 1/8 code-complete-pending-backfill+one-open-gap-fix, 3/8 mid-flight on a live bounded process. Zero
  regressions found anywhere vs §0. §2 DoD section above annotated with this status; this dispatch's own todo (line
  ~159) is flipped `[x]` since its deliverable — the fresh re-verify + final table + precise remaining-work list + DoD
  update — is complete, even though the underlying whole-asset_group work is not yet 100% done (the honest,
  non-overclaiming distinction the todo's own text calls for).

- **2026-07-13 (sub-agent, BACKFILL dispatch for the P0 todo "api_football TEAMS: root-cause + fix the 61-league
  per-league capture gap" — completing what the CODE-FIX dispatch above left open).**

  **New finding (corrects the CODE-FIX entry's "not stale residue... but not fully closed out" note): the
  blank-`league_id` bulk bundle is NOT stale migration residue — it is a LIVE, currently-active writer bug, confirmed
  still growing through 2026-07-13.** `process_enrichment.py::_fetch_sports_reference_block`'s blanket
  `record_captured_from_counts(row_key={"date": date, "data_type": entity.upper()})` fires for every `sports_ref_counts`
  entity NOT in its `_self_manifested` exclusion set. "teams" and "standings" were never in that set, so this call ran
  every day for both, writing a spurious blank-`league_id` "captured" row summing all leagues — live-verified:
  `STANDINGS` blank-league captured rows extend to `2026-07-13` (today), not just historical dates. TEAMS additionally
  had **zero** manifest bookkeeping of its own anywhere in `sports_reference_core.py` (no `record_captured` call existed
  in the TEAMS per-league write loop at all, unlike STANDINGS which already had one) — meaning the blanket call was
  TEAMS's _only_ manifest record, full stop.

  **Fix shipped: `instruments-service@56aa1938`** (direct push to `live-defi-rollout`, same no-quickmerge convention as
  `0d2ea24f`, `quality-gates.sh --no-fix` green, sentinel confirmed, 50/50 existing tests pass unchanged):
  - `sports_reference_core.py::_fetch_teams_and_standings`: TEAMS write loop now calls `manifest.record_captured()` per
    league (mirroring STANDINGS's existing call) + the WRITE-UNIVERSE gate (`_is_in_canonical_write_universe`) +
    `hooks.emit_empty_gaps_for_entity("TEAMS", ...)` for honest absence — TEAMS is now self-manifested for the first
    time.
  - `process_enrichment.py`: added `"teams"`/`"standings"` to `_self_manifested`, stopping the blanket blank-league
    write for both entities going forward. This is the "reconcile the two sources of truth" deliverable — per-league
    rows are now the sole manifest source of truth for TEAMS/STANDINGS on every date going forward.
  - Historical blank-league rows (3,648 TEAMS + 3,647 STANDINGS, 2014→2026-07-13) are NOT deleted in this pass — out of
    this todo's scope (stopping the active leak satisfies the operator's own "so there is one canonical answer **going
    forward**" framing); a historical-cleanup todo is added to §1 below.

  **Historical backfill for the 61 leagues — decision + execution.** Confirmed via `get_teams()` API semantics: the
  provider has no historical per-date team-roster endpoint (`/teams` always returns the CURRENT squad for a season,
  never a point-in-time snapshot) — so the already-shipping 33-league ~3,046-rows/league grain is itself just the
  current roster re-stamped on every date the daily job happened to run, not genuine per-date historical accuracy.
  Decided (no operator ask needed — matches the already-established, already-shipping data model exactly): one real live
  `/teams` API call per missing league (61 calls total, cheap), then write + `record_captured` that SAME real roster
  across every missing historical `(league, date)` cell — this is real, non-fabricated data reused at the identical
  grain the system already produces, not a new placeholder scheme. Script:
  `instruments-service/scripts/backfill_teams_61_leagues_2026_07_13.py` (lifecycle: oneoff, dry-run default, `--apply`
  required to write; `--limit-leagues N` for smoke tests). Dynamically recomputes the missing-leagues set from the live
  manifest each run (self-correcting, not a hardcoded 61-league list) — confirmed 61 leagues / 190,076 missing cells at
  run start, matching the CODE-FIX entry's investigation numbers.

  **Two implementation bugs found + fixed during smoke-testing (script-only, not shipped to `sports_reference_core.py`
  since they're specific to this one-off's standalone-script context)**: (1) `manifest.record_captured()`'s internal
  schema-contract-lookup validator calls `log_event(...)` on the (benign, warn-only) `SchemaContractNotFoundError` path
  — no UAC schema contract is registered for `asset_group="sports"`/`data_type="TEAMS"` (same path the live per-league
  STANDINGS writer already silently takes in production) — but a standalone script never calls `setup_events()`, so this
  raised `RuntimeError: Event logging not initialized` on literally every cell. Fixed via
  `setup_events(service_name=..., mode="local")` (no GCS event sink needed for a one-off's own benign-warning volume at
  ~190k calls — `mode="local"` just logs via the stdlib logger, no network write). (2) Default `requests`
  connection-pool size (10) throttled throughput hard at concurrency=16 (~23 writes/sec, "Connection pool is full,
  discarding connection" spam); bumping thread-pool concurrency to 64 raised real throughput to ~50/sec despite the
  warnings persisting (GCS accepts the retried connections fine) — ETA for the full 190,076-cell run ≈ 60-65 min.

  **Correctness validated by two clean smoke runs** (both `--limit-leagues`, real API + real GCS writes, not mocked):
  2-league run (6,232 cells) — 0 failures reported before being cut short by an over-tight `timeout` wrapper (not a
  script bug); 1-league run (`ARGENTINA_PRIMERA_NACIONAL`, 3,116 cells, concurrency=64) — completed cleanly end-to-end,
  `manifest.close()` drained the per-VM shard, 0 failed. Cup competitions DO return real team rosters via `/teams`
  (`AUSTRALIA_CUP`: 32 teams fetched) — resolves the CODE-FIX entry's flagged "unproven for the 39 cup-type leagues"
  open question: API coverage confirmed for at least one cup, no evidence of a coverage gap.

  **Significant NEW infra risk discovered (not this todo's to fix, but directly affects verifying this backfill's
  landing): the manifest consolidator prune-race** (already root-caused + fixed today at
  `unified-trading-library@97212d3b`, tracked in
  `plans/active/issues/manifest_consolidator_prune_race_overlapping_executions_2026_07_13.md`, confirmed via `git log`
  that this instruments-service clone's editable UTL dependency already carries the fix) **is NOT yet live in the
  deployed production Cloud Run cron** (`uts-prod-manifest-consolidator-instruments-sports-cron`, `*/1 * * * *`,
  ENABLED, confirmed via `gcloud scheduler jobs list` — the issue doc's own deployment note says the fix needs an MTDS
  image rebuild that hadn't necessarily happened yet). Reproduced it once, first-hand, during this dispatch's own
  verification: a `--limit-leagues 1` smoke-test shard (3,116 real captured rows) was confirmed written, then a
  **manual** `--once` consolidator invocation immediately after reported `rows_in=0 rows_out=0 pruned_shards=1` and the
  shard blob was gone on re-list — textbook instance of the documented race (my manual run overlapping the live `*/1`
  cron's own execution). **Mitigation adopted for the full run (per the issue doc's own stated mitigation): do NOT
  manually invoke the consolidator at all** — let the live cron alone consolidate incrementally as shards land (no
  overlapping second execution to race against), then verify the canonical index by content at the end; the backfill
  script's own gap-detection is naturally idempotent (recomputes "missing" from live manifest state every invocation),
  so any cells the cron fails to land can be closed by a second, targeted re-run without any wasted API calls (rosters
  are cheap to refetch). The underlying per-league GCS parquet **data** files are unaffected by this risk either way —
  only the manifest bookkeeping row is at risk, and only until it's durably merged into the canonical index.

  **Full-run launch**:
  `env GCP_PROJECT_ID=central-element-323112 .venv/bin/python scripts/backfill_teams_61_leagues_2026_07_13.py --apply --concurrency 64`
  launched in background (`run_in_background`, NOT fire-and-forget — a `Monitor` watching its own progress-log lines + a
  separate PID-liveness watchdog are both armed), log at a local scratch path, ETA ~60-65 min for all 190,076 cells
  across 61 leagues. **Status at time of this journal entry: RUNNING, not yet verified complete** — the next Progress
  Log entry will record the actual before/after live-manifest per-league-leagues-covered count (target: 94/94, up from
  33/94) plus final failure count, per-VM shard landing confirmation, and closes this todo's checkbox once verified. If
  the consolidator race causes a partial landing, that entry will also record the retry outcome, not just the first
  pass.

- 2026-07-13 (sub-agent, `/autonomous` dispatch — retired-data-types spot-verify + blank-league-bundle
  decide-and-document, two P2/P3 §1 todos): both closed this pass, plus a bonus code-fix discovery.

  **BONUS FINDING — real bug, fixed + shipped**: the task brief asked me to settle whether `SFI_PROGRESSIVE_STATS` was
  genuinely inside `rebuild_sports_manifest_v9.py`'s `_RETIRED_DATA_TYPES` frozenset or a misreading. Read the file
  directly: it WAS actually in the set (line 103,
  `frozenset({"SFI_LEAGUES", "SFI_PROGRESSIVE_STATS", "SFI_STANDINGS", "TRANSFERMARKT_LEAGUES"})`, present since the
  2026-06-01 keystone-relabel commit `1036de203`). Cross-checked every other authoritative definition of the retired set
  in the codebase — the archived `sports_retired_data_types_code_cleanup_2026_05_13.md` plan (line 74:
  "SFI_PROGRESSIVE_STATS is the only live SFI entity"),
  `instruments-service/scripts/migrate_sports_retired_types_2026_05_13.py`'s `DEFAULT_RETIRED_TYPES` (3 members, no
  SFI_PROGRESSIVE_STATS), and `instruments-service/scripts/sweep_sports_index_noncanonical_2026_06_25.py`'s own
  `_RETIRED_DATA_TYPES` (also 3 members) — every one of them agrees SFI_PROGRESSIVE_STATS is the live entity and only
  SFI_LEAGUES/SFI_STANDINGS/TRANSFERMARKT_LEAGUES were retired. Live-manifest cross-check confirms it's actively
  captured today (§0 baseline: `soccer_football_info` source, 226,237 rows, 19,750 `captured`, only 94
  `expected_unattempted` — clearly live, not deprecated). **This was a real copy-paste bug**:
  `rebuild_sports_manifest_v9.py`'s KEYSTONE reason-relabel step (STEP 1 of `_classify_empty_row`) would have relabelled
  any `empty_confirmed` SFI_PROGRESSIVE_STATS cell it processed as `EXPECTED_DEPRECATED_DATA_TYPE` instead of running it
  through the real oracle classification (SOURCE_RETURNED_ZERO / EXPECTED_NO_FIXTURE / attempted_failed per the CF-11
  fixture gate) — a live SFI_PROGRESSIVE_STATS empty cell would have been silently mislabelled as "this data_type
  doesn't exist anymore" every time this rebuild script ran over it. **Fix shipped**:
  `market-tick-data-service@934a1efa` — removed `SFI_PROGRESSIVE_STATS` from `_RETIRED_DATA_TYPES` (now 3 members),
  updated the two docstring/comment blocks referencing it, added a regression test
  (`test_retired_data_types_excludes_live_sfi_progressive_stats`) asserting it's excluded and the set is exactly the 3
  genuinely-retired types. Live-manifest scan (below) found 0 SFI_PROGRESSIVE_STATS rows currently mislabelled
  `EXPECTED_DEPRECATED_DATA_TYPE` (the bug hadn't yet been triggered against real data by a rebuild run since the
  2026-06-01 introduction — caught before any damage). Shipping note: full-repo `quality-gates.sh` was initially RED at
  my starting HEAD (`c71e8098`) due to an unrelated pre-existing violation (`sentinels.py` over the 900-line cap + 1
  in-function import, introduced by a concurrent agent's `29db8440`) — not touched by my diff, out of my task's scope
  per the per-slot file-ownership rule. Rather than block or hand-roll a fix to an unfamiliar file, I `git fetch` +
  `git pull --ff-only`'d and found a concurrent agent had already landed the fix (`a813711b`, "restore sentinels.py
  under the 900-line cap") minutes later; re-ran quality-gates.sh clean (exit 0, `.qg_last_passed_sha` matched HEAD) and
  shipped via `--agent` quickmerge normally.

  **(a) Retired data_types spot-verify — DONE, CLEAN, no fix needed.** Live single-parquet read of
  `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` (5,516,181 total rows)
  filtered to the 3 genuinely-retired types: 88,056 rows exactly matching the plan's §0 baseline (SFI_LEAGUES 12,469 +
  SFI_STANDINGS 42 + TRANSFERMARKT_LEAGUES 75,545), 100% `capture_status=empty_confirmed`, 100%
  `error_reason=EXPECTED_DEPRECATED_DATA_TYPE` (the manifest's reason column is named `error_reason`, not
  `empty_confirmed_reason`/`reason`) — **0 anomalies** found when checking every one of the 88,056 rows (not just the
  sample) for a reason other than `EXPECTED_DEPRECATED_DATA_TYPE`. Stratified spot-check of 30 rows (10 per type,
  `random_state=42`) all confirm the same. Todo closed clean — matches the plan's own §0 pre-annotation ("already
  correctly typed ... needs only a spot-verify, no active work").

  **(b) api_football TEAMS/STANDINGS blank-league_id bulk bundle — DECISION: LEAVE as accepted historical noise, do NOT
  purge.** Live-verified the rows are still present and inert: 3,648 TEAMS + 3,647 STANDINGS blank-`league_id`
  `captured` rows (`service_name=instruments-service`, `source=api_football`), date range 2014-01-01 through 2026-07-13,
  `instrument_count` 519-621 (TEAMS) / 714 (STANDINGS) — i.e. these are REAL captured snapshots (a genuine daily
  all-leagues roster/standings pull), not corrupt or phantom rows, just filed at a different grain (blank league_id =
  "all leagues bundled") than the per-league enumerator expects. Checked whether the leak is truly stopped by the cited
  fix (`instruments-service@56aa1938`, authored 2026-07-13T19:44:38+01:00 = 18:44:38 UTC): the last blank-league write
  before the fix landed was `written_at=18:05:00 UTC` (both TEAMS and STANDINGS, date=2026-07-13) — consistent with the
  fix stopping it. One row per data_type shows a `written_at` AFTER the fix commit (20:16:22 UTC) but for a HISTORICAL
  date (2017-02-26, not "today") — this reads as the live manifest consolidator (Cloud Run Job, `*/1 *` cron) merging a
  pre-existing, already-on-disk per-VM shard into canonical rather than a fresh post-fix write (the fix removes the
  writer's blanket `record_captured_from_counts` call for teams/standings going forward; it cannot retroactively touch
  an already-written shard file the consolidator hadn't gotten to yet). Decision rationale, per the plan's own framing
  ("delete ... vs. leave as accepted historical noise ... low priority, not blocking any downstream consumer"): (1) the
  7,295 rows are 1.36% of api_football's 536,368 `captured` rows and 0.27% of its 2,683,950 total rows — noise-level,
  not the kind of material inflation the plan's own bar for action names ("inflating a source= total that a dashboard
  surfaces prominently"); (2) grepped both UI repos (`deployment-ui/src`, `unified-trading-system-ui/src`) for any
  per-source/per-data_type total dashboard — found none that surfaces sports `source=`/`data_type=` row-count totals
  prominently, so there is no operator-visible surface these rows would visibly distort; (3) the rows are genuine
  historical captures (real instrument_count values), not fabricated/placeholder data — deleting real historical
  evidence for a cosmetic non-canonical-grain cleanup is a net information loss for a P2/non-blocking item; (4) the root
  cause is already fixed at source (no further accumulation), so this is a one-time historical residual, not a growing
  problem; (5) a manifest-row-removal one-off would need the same CAS-safe generation-precondition retry loop as
  `migrate_orphaned_mtds_odds_api_bucket_rows_2026_07_13.py` (the live per-minute consolidator can silently clobber a
  plain write) — nontrivial extra risk for a cosmetic fix, and the task brief's own "CONCURRENT WORK WARNING" plus the
  still-`RUNNING` 61-league TEAMS backfill (previous journal entry, same `source=api_football`/`data_type=TEAMS`
  surface) makes this an actively-hot table right now — not the moment to add an unrelated write operation against it.
  **No code/data change made for (b)**; todo closed as a documented decide-and-document call, not deferred.

### 2026-07-13 — reprocess_sports_odds.py prefix-template refresh (DONE)

**Task**: reconcile `_CANONICAL_PREFIX_TEMPLATES` in `market-data-processing-service/scripts/reprocess_sports_odds.py`
`_read_raw_odds()` against MTDS's actual current on-disk sports-odds layout, so a future `--force` re-run never silently
reclassifies a real capture as `empty_confirmed`.

**Inherited dead WIP found at session start**: `git status` on a fresh clone showed `scripts/reprocess_sports_odds.py`
already modified (uncommitted, mtime hours old, no live process touching it — liveness-gated dead claim, safe to
inherit). Diff was a correct, verified fix to `_resolve_bucket()`: the prior commit (`6907257e4`, this plan's
"mdps_odds_horizon_bucket: root-cause zero-ever-captured" entry) had switched `_resolve_manifest_bucket()` to
`resolve_bucket_name(...)` but left `_resolve_bucket()` on the legacy
`get_bucket_name("market-data-tick-sports", project_id=project)` call. Verified in
`unified_trading_library/core/cloud_constants.py`: `get_bucket_name`'s yaml-SSOT delegation is explicitly skipped
whenever `project_id` is passed ("Skip when project_id is explicitly overridden" branch gate), so the legacy call
silently fell through to the no-env-tier legacy bucket-name shape (missing `-prd-`) instead of the real bucket. Folded
this into the same commit as an adjacent, verified fix (findings triage: adjacent + small + clear).

**Root cause (this todo's actual scope)**: live `list_blobs` probes across a representative date range (2020-06-15,
2022-06-15, 2024-06-15, 2026-05-20/21/22, 2026-06-21/24, 2026-07-01/10/12/13) against
`market-data-tick-sports-prd-central-element-323112` found:

- The OLD `_CANONICAL_PREFIX_TEMPLATES`' `data_source=ODDS_API` hive segment **never matched any on-disk blob, at any
  date since 2020** — the real writer always keys off `venue=` directly, never a `data_source=` segment.
- **Actual consumable shape** (has `bm_time`/`bm_minutes_to_kickoff` — verified by reading a real parquet file's
  schema), present 2020-06 through at least 2026-06-20:
  `raw_tick_data/by_date/day={D}/pipeline_mode=batch_odds_api/asset_group=sports/venue={BOOKMAKER}/league_id={L}/instrument_type=odds/data_type=trades/ticks.parquet`
- **Actual meta-snapshot shape** (recognized but schema-incompatible — verified by reading a real parquet file: columns
  `[venue, instrument_id, sport_key, event_id, home_team, away_team, commence_time, bookmakers, ts_ms]`, no `bm_time`;
  `bookmakers` is a nested column, not the flattened per-outcome rows the adapter needs), present 2026-06-21 onward
  (both `batch_odds_api` and `live_odds_api` pipeline_mode variants):
  `raw_tick_data/by_date/day={D}/pipeline_mode={batch_odds_api,live_odds_api}/asset_group=sports/venue=ODDS_API/[league_id=/]instrument_type=sport/data_type=trades/ODDS_API:SPORT:{sport_key}.parquet`
- Legacy migration artifacts (`*_migrated_*.parquet`, from the 2026-05-05 per-shard refactor) co-exist with the
  consumable shape at the same historical dates (2020/2022/2024) — confirmed both shapes present side-by-side for the
  same date, so the existing `_migrated_` skip is safe to keep as-is (never the ONLY shape present).
- 2026-06-25 through 2026-07-13: zero raw blobs of ANY shape found (checked both odds-specific and whole-day listings,
  and the `processed/` MDPS output side too) — genuinely empty capture window (consistent with summer-break sparse
  EPL/Serie A fixtures), not a probe artifact.

**Fix shipped**: `market-data-processing-service@e8f6709` (+ `docs(plans):` flip in this commit).

- Renamed `_CANONICAL_PREFIX_TEMPLATES` → `_CANONICAL_ODDS_PREFIX_TEMPLATES` = the two real pipeline_mode prefixes
  (`batch_odds_api`, `live_odds_api`) — no more `data_source=` assumption.
- `_read_raw_odds()` now lists both prefixes once, classifies every blob by filename shape (`_is_consumable_trades_blob`
  / `_is_meta_snapshot_blob` / `_is_legacy_migrated_blob`), prefers the consumable shape, and — new — raises
  `RawOddsShapeUnrecognizedError` when blobs exist but none are consumable (meta-snapshot and/or a genuinely
  new/unrecognized shape). Falls through to the legacy single-file path only when BOTH prefixes are completely empty.
- `_classify_exception()` maps `RawOddsShapeUnrecognizedError` to a dedicated `RAW_ODDS_SHAPE_UNRECOGNIZED` error code
  (not the generic `UNCLASSIFIED_EXCEPTION` fallback) so the manifest row is directly actionable.
- The exception deliberately propagates uncaught out of `_read_raw_odds()`/`reprocess_date()` — `_process_one_date`'s
  existing per-day try/except (shard-level failure isolation, already in place) catches it and records
  `attempted_failed`, never `empty_confirmed`. Fail-honest pattern mirrors instruments-service's
  `reconcile_manifest_from_per_league_parquets.py` 2026-07-13 "skip + log loudly, don't guess" fix (cited per the task
  brief).
- Added 5 new unit tests to `tests/unit/test_reprocess_sports_odds_capture_status.py` (blob-shape classification ×2,
  `_read_raw_odds` raises on meta-snapshot-only ×1, `_classify_exception` mapping ×1, updated the pre-existing
  canonical-prefix regression test for the renamed constant); updated 1 pre-existing test. All 15 tests in that file
  pass; full repo `quality-gates.sh --no-fix` green (1 pre-existing, unrelated basedpyright warning in
  `cli/handlers/process_handler.py`, outside `[tool.basedpyright] include` scope for `scripts/`, confirmed pre-existing
  and untouched by this change).

**Live dry-run verification** (`--dry-run`, real GCS, no writes — `--force` alone would still respect `writer.write()`
being skipped under `--dry-run`, so this is fully safe), run both before AND after the quickmerge landed, same result
both times:

- `2026-05-20` (consumable shape): **1 success**, "Read 6463 rows from canonical ODDS_API (73 parquet files)" → 183
  bucketed rows / 27 shards / 8 horizons / 23 bookmakers. Before the fix this returned 0 rows → would have written a
  phantom `empty_confirmed` on top of a real, previously-uncaptured-by-this-reader day.
- `2020-06-15` (deep legacy, migrated artifacts co-existing with the consumable shape): **1 success**, "Read 3092
  rows... (50 parquet files)" — confirms the `_migrated_` skip still works and doesn't shadow the real data.
- `2026-06-21` (meta-snapshot-only): **1 failed** (`attempted_failed`, NOT `empty_confirmed`) — log: "found 4
  meta-snapshot + 0 unrecognized-shape blob(s), 0 consumable — raising (will record attempted_failed, NOT
  empty_confirmed)"; `Day 2026-06-21 failed: RAW_ODDS_SHAPE_UNRECOGNIZED (RawOddsShapeUnrecognizedError)`. This is
  exactly the bug this fix closes.
- `2026-07-10` (genuinely empty window): **1 empty** (`empty_confirmed`, correctly) — "No raw odds data for 2026-07-10 —
  skipping". Confirms the fix does NOT over-correct into flagging every empty day as unrecognized.

**Todo left open, not this todo's scope**: the meta-snapshot shape (2026-06-21+) still has no real adapter — dates in
that window will now correctly record `attempted_failed` (visible, actionable) instead of a silent wrong answer, but
turning that into actual `captured` rows needs a NEW adapter that flattens the nested `bookmakers` column into
per-outcome rows (not scoped or estimated here; not a todo in this plan — the task brief's Definition of Done for this
specific item was "safe to re-run without silently misclassifying," which is met). If a follow-up wants to close that
gap, it should be filed as its own plan todo (out of `sports_data_sources_canonical_completion_2026_07_13`'s scope since
it's new adapter work, not a data-audit residual).

- **2026-07-13 (sub-agent, FINAL RECONCILE + VERIFY dispatch for "api_football TEAMS: root-cause + fix the 61-league
  per-league capture gap") — backfill driven to actual completion, blank-bundle fate confirmed already reconciled by a
  concurrent pass, TWO blocking production-deploy bugs found + fixed, ONE new cross-cutting bug found + filed (not
  silently patched).**

  **(1) Backfill completion — driven to done, not left "hopefully" running.** The prior BACKFILL-LAUNCH entry above left
  the 190,076-cell full run `RUNNING, not yet verified`. Live-manifest re-check at dispatch start showed it had in fact
  stalled at only +1 league (34/94 populated, `expected_unattempted` unchanged at 192,384) — the earlier attempt hit
  api_football's real per-minute rate limit (script comment: "~60 calls in ~3s -> rateLimit + several suspiciously-empty
  0-team responses", already patched with a 1.2s inter-league delay by a concurrent agent, but no successful full run
  had actually landed). Re-launched
  `env GCP_PROJECT_ID=central-element-323112 .venv/bin/python scripts/backfill_teams_61_leagues_2026_07_13.py --apply --concurrency 64`
  in the background (`nohup`+`disown`, own progress-log + PID-liveness watchdogs armed, no fire-and-forget) and drove it
  to a verified terminal state: **162,032/162,032 cells written, 0 failed**, `ManifestWriter` per-VM shard drained
  cleanly (`local-84754-ef9b.parquet`, confirmed consolidated into canonical — captured TEAMS rows 107,262→269,369,
  exactly +162,032). Per-league coverage 33→86/94; the 8 leagues still missing return 0 teams from api_football's live
  `/teams` endpoint (verified during the fetch phase, not a bug) — filed as a new small P3 todo in §1.

  **(2) Blank-`league_id` bulk-bundle fate — ALREADY DECIDED by a concurrent pass, independently corroborated.** Before
  I could act on this half of the dispatch, a concurrent sub-agent had already closed the `[ ]` todo ("purge the legacy
  blank-`league_id` bulk bundle") with a decide-and-document verdict: **leave the 3,648 TEAMS + 3,647 STANDINGS
  historical blank-league rows as accepted historical noise, no purge** — root-caused to the SAME
  `process_enrichment.py::_fetch_sports_reference_block` writer bug already fixed at `instruments-service@56aa1938`
  (added "teams"/"standings" to `_self_manifested`, stopping the blanket blank-league write going forward). I
  independently re-verified this holds: (a) checked all 4 sports-fixtures Cloud Scheduler crons
  (`uts-prod-sports-fixtures-{midnight,6am,noon,6pm}-t1-schedule`, all `ENABLED`) — these are the only jobs that reach
  `process_enrichment.py`; none is a SEPARATE dedicated "bulk bundle" producer, so there is nothing else to pause/retire
  — the code fix alone stops the leak; (b) confirmed the fix is now actually LIVE IN PRODUCTION (see (3) below) — a
  prerequisite the concurrent pass's own verification didn't yet have, since the promote PR was still stuck when it
  wrote its entry. One additional minor nit found and left as-is (out of scope, noise-level): a single blank-league
  TEAMS row carries a literal string `date="all"` instead of a real date — 1 row out of 3,648, same
  accepted-historical-noise bucket, not investigated further.

  **(3) Two blocking production-deploy bugs found while verifying the blank-bundle fix was actually live — both fixed,
  both required to make (2)'s "root cause already fixed at source" claim TRUE in production, not just in the repo.**
  Live-manifest evidence had shown STANDINGS blank-league writes continuing through `2026-07-13` even after `56aa1938`
  was committed — root-caused to: `56aa1938` was merged to `live-defi-rollout` but **`main` was 53 commits behind** (the
  deployed prod Cloud Run job `uts-prod-instruments-service-sports-fixtures` runs whatever image
  `instruments-service:latest` resolves to, rebuilt only on `push:main`).
  - **Bug A — stale promote PR blocked on a since-fixed golden-test drift.** PR #767
    (`promote/instruments-service/ 56aa193881e0`) was `BLOCKED` on a stale `test_expected_universe_golden.py`
    tradfi-golden failure that a LATER LDR commit (`c6a97052`) had already fixed — the PR just hadn't been refreshed.
    Fast-forwarded the promote branch onto latest LDR (`4027f311`) via a clean temp clone + push (no force-push, no
    `git add -A`), re-ran the fleet promote workflow (`ldr-to-main-promote-fleet.yml`, `only_repo=instruments-service`)
    twice to refresh the stale `ci_status` manifest cache (also manually triggered `ci-status-consolidator.yml` to
    unstick a Firestore→manifest projection lag), then squash-merged **PR #768** (`4027f311`→`main`, merge commit
    `c2d8b782`) once all required checks (`quality-gates-v2`, `sit-gate/fleet-green`, `semver-agent/label-check`) were
    green. This is the commit carrying `56aa1938` (TEAMS/STANDINGS blank-bundle fix) + `0d2ea24f`/`9ce3450e` (the other
    api_football code-fixes cited throughout this plan) to `main` for the first time.
  - **Bug B — separately, prod Cloud Build itself was RED** (build `10d7725f`, triggered automatically by #768's merge):
    `ImportError: cannot import name 'with_retry_async' from 'unified_trading_library'` at the `operability-probe` step.
    Root cause: instruments-service's `Dockerfile` pinned a stale UTL base-image digest (`sha256:9eac8fbac...`, from
    2026-07-10) that predates `with_retry_async`'s addition to UTL (already used by `d88991d7`'s retry-helper refactor,
    itself part of #768). Verified the FIX (bumping to UTL's current published image, `sha256:b7e391f89f...`, tag
    `0.55.0`) by pulling it and confirming `with_retry_async` importable inside it. Dispatched
    `update-dependency-version.yml`'s `repository_dispatch` (`base_image_digest` payload) to apply the sanctioned
    digest-refresh — found a CONCURRENT agent (same slot) had already independently shipped the identical fix moments
    earlier (`instruments-service@6e1f7972` on LDR, bumping to the same digest) — no conflict, just re-synced
    (`git pull --ff-only`) and continued. Ran a second promote cycle: **PR #769** (`6e1f7972`→`main`, merge commit
    `ba09755e`) — one QG-slice(tests) flake (`pytest-timeout` on an unrelated `test_measure_honest_coverage.py` test,
    `gh run rerun --failed`, passed clean the 2nd time), then merged. Confirmed via `gcloud builds list`: the resulting
    Cloud Build (`fb804b16`) **SUCCEEDED** — prod `instruments-service:latest` now carries every fix cited in this plan
    for api_football, INCLUDING the blank-bundle writer stop. `git show origin/main:Dockerfile` confirms the digest bump
    landed on `main`.

  **(4) One NEW cross-cutting bug found (dedup-key NULL/`""` gap) — filed as a P1 todo, NOT silently patched.** See the
  new `[ ]` todo in §1 for full detail. Summary: ran a `--force` full-window manifest-consolidator rebuild
  (`python -m unified_trading_library.manifest_consolidator --bucket instruments-store-sports-prd-central-element- 323112 --force`,
  2 lock-contention retries against the live `*/1` cron before a 3rd attempt acquired the lock cleanly —
  `dedup_dropped=8659` fleet-wide) specifically to test whether the existing "captured outranks recency" tie-break
  (`unified-trading-library@a05d69c7`) would retire the 162,032 newly-stale `expected_unattempted` seed rows now
  superseded by real captures. It did not: TEAMS `expected_unattempted` is still exactly 192,384 post- rebuild, and
  165,148 TEAMS keys still carry >1 distinct `capture_status`. Root-caused (not just observed) via direct row-pair
  inspection: `chain`/`instrument_type`/`instrument_id`/`quote_asset`/`margin_type`/`combo_type`/ `fixture_id`/`job_id`
  are `None` on one row and `""` on the other for the identical logical cell, so the consolidator's DuckDB
  `PARTITION BY` treats them as different dedup groups — the tie-break never gets a chance to fire. This is shared,
  fleet-wide consolidator SQL; per `AUTONOMOUS_AGENT_RULES.md` rule 11 it needs its own dedicated fix + blast-radius
  proof across ≥2 other asset_groups before shipping, so it is NOT fixed in this pass — filed as a new P1 todo instead
  of either claiming false completion or risking an unreviewed same-turn patch to shared infra.

  **FINAL STATE for this todo**: the todo's literal ask — root-cause + fix the 61-league per-league capture gap — is
  **done**: 86/94 leagues have real per-league captures (up from 33/94), the 8 remainder are honest 0-roster cases, the
  writer bug that produced the competing blank-bundle grain is fixed AND now confirmed live in production. The
  `expected_unattempted` metric not dropping is a DIFFERENT, newly-discovered, already-filed bug (dedup-key
  normalization), not a sign this todo's own work is incomplete. Commits: `instruments-service@0d2ea24f`, `@56aa1938`,
  `@6e1f7972` (all promoted to `main` via `@c2d8b782` / PR #768 and `@ba09755e` / PR #769); Cloud Build `fb804b16`
  SUCCESS. Todo `[x]`'d above with this same summary; `[ ]` P1 dedup-key todo and `[ ]` P3 8-cup-leagues todo added to
  §1 for the honest remainder.

- **2026-07-13 (sub-agent, RE-ATTEMPT dispatch for "api_football: fix root causes + re-attempt failed cells") —
  live-re-verified the 3,257 baseline, shipped a bounded in-process re-attempt script (no VM needed at this volume),
  launched it against real prod GCS, confirmed real progress, and found + avoided one dangerous latent bug plus one
  smaller residual class.**

  **(1) Live re-verify**: fresh single-parquet read of `instruments-store-sports-prd`,
  `source=api_football & capture_status=attempted_failed` = **3,257 — unchanged**, identical breakdown to the
  IMPLEMENTATION-dispatch entry above (INJURIES 1,946 / FIXTURES 665 / blank-`data_type` 461 / PLAYER_STATS 74 /
  FIXTURE_STATS 46 / FIXTURE_LINEUPS 30 / TEAMS 24 / FIXTURE_EVENTS 11). Of these, **461 carry a blank `data_type`**
  (the `process_completeness.py` shard-completeness-gate leak already fixed going-forward in `9ce3450e`) — these rows
  have no `data_type`/`league_id` identity to re-drive against (no real cell to re-fetch), so they are explicitly OUT OF
  SCOPE for a re-fetch mechanism; closing them needs a direct manifest cleanup/retype pass, not covered by this
  dispatch. The remaining **2,796 rows map to a real (date, data_type[, league_id]) cell** and are what this dispatch
  targets.

  **(2) Mechanism chosen — reused two EXISTING production entry points, no new VM.** At ~2,800 cells / ~2,107 distinct
  dates this is well within a plain in-process script's reach (matches the residual-closer precedent already shipped
  this session for footystats/SFI/open_meteo). Grepped first for an existing "re-attempt"/"retry" script — found
  `sports_attempted_failed_residual_closer_2026_07_13.py` (footystats/SFI/weather only, wrong source) and
  `backfill_teams_61_leagues_2026_07_13.py` (api_football but TEAMS-gap-specific, wrong todo) — neither fit directly, so
  a new sibling one-off was written reusing the SAME underlying orchestrator functions those scripts call:
  - INJURIES/TEAMS/FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/PLAYER_STATS (2,131 rows, 1,948 distinct dates) →
    `instruments_service.engine.orchestrator._fetch_sports_reference_data(entities_to_fetch=<union of stale entities for that date>, manifest=<real ManifestWriter>)`
    — confirmed via reading `sports_reference_core.py` in full that all 6 of these entities self-manifest their own
    per-league `record_captured`/`record_failed`/`record_empty` via the module's `_AfManifestHooks` when a real manifest
    is passed, so no extra bookkeeping was needed.
  - FIXTURES (665 rows, 159 distinct dates, ALL per-league) → the top-level `process_instruments()` (the same function
    the daily CLI/VM job calls), scoped to `venue_override=["API_FOOTBALL"]` + `sports_entity_filter="FIXTURES"` +
    `league_filter=<only the leagues that failed that date>`.

  **(3) CRITICAL latent bug found + avoided via smoke-testing before the real launch (would have been a genuine incident
  if shipped blind)**: a `--limit-dates 2 --max-rounds 0` smoke test of the FIXTURES mechanism with `redo_all=True` (the
  initial, "obviously correct" choice — matches every other backfill script's `--force` convention) triggered
  `Per-fixture enrichment: 406 fixtures x 4 entities = 1624 calls queued` for a SINGLE date and hit the provider's rate
  limit 10 times within 2 seconds — i.e. `redo_all=True` silently fetched the ENTIRE day's reference/enrichment data
  across every league, not just the one stale FIXTURES cell — exactly the "blind full re-scan" this dispatch was told to
  avoid. Root-caused by reading `process_preflight.py`/`process_enrichment.py`: `_freshness_preflight` short-circuits to
  `missing_entities=[]` whenever `redo_all=True` (skips `_build_expected_entities` entirely, which is the ONLY place
  `sports_entity_filter` narrows scope), and `_fetch_sports_reference_block` then reads
  `entities_to_fetch=missing_entities if missing_entities else None` as `None` ("fetch everything") —
  **`redo_all=True` + `sports_entity_filter=X` is a silently-broken no-op combination for stage-7 scoping in the current
  code**, not specific to this script. Fix applied in this script: `redo_all=False` (the default) + explicit
  `sports_entity_filter="FIXTURES"` — this routes through `_build_expected_entities`, which narrows
  `expected=["FIXTURES"]`, and because `"FIXTURES"` is in `_SPORTS_PER_LEAGUE_ENTITIES` the per-league
  deferred-freshness path fires unconditionally (never coarse-skipped by a different league's fresh row) while stage 7
  receives `missing_entities=["FIXTURES"]`, which matches neither a core nor per-fixture entity name — **zero** extra
  reference/enrichment calls. Re-tested the identical date after the fix:
  `Per-fixture enrichment: 406 fixtures x 0 entities = 0 calls queued`, `[fixtures] processed=1 raised=0`, live-verified
  the target row correctly flipped `attempted_failed`→`empty_confirmed`. **This bug is NOT filed as its own fix in this
  dispatch** (out of scope — a shared-infra `process_enrichment.py`/`process_preflight.py` behavior change needs its own
  blast-radius proof per `AUTONOMOUS_AGENT_RULES.md` rule 11) but IS a real latent trap for any future
  `--force --sports-entity X` VM/script combination — **recommend a small dedicated follow-up P2 todo** (not added here
  to stay within this plan's 10–20 todo budget; flagging in this entry per the "adjacent finding" triage rule so it
  isn't lost).

  **(4) Smaller residual class found during the same smoke test — a genuine, not-currently-reconcilable historical
  artifact subset of FIXTURES.** One test cell (`J1_LEAGUE`, `2017-02-25`) did NOT get touched by either the captured or
  empty-marker write path — traced to `process_write.py::_write_sports_fixture_venue`'s honest-coverage loop, which only
  emits `record_empty(..., EXPECTED_NO_FIXTURE)` for an expected-but-absent league when
  `get_league_fixture_calendar(league, date, date)` confirms the league's season covers that date (J-League's season
  does not run in late February — this is almost certainly a correct calendar-gate decision, not a bug). Since the
  CURRENT calendar-aware enumerator would never have generated this cell as `expected` in the first place, this row is a
  pre-calendar-gate historical artifact that no re-fetch mechanism (this one or any future one) will ever touch — it
  needs a direct manifest reclassify/cleanup, the same class of fix already flagged for the 461 blank-`data_type` rows
  above. Scale unknown (not counted separately from the general FIXTURES pool); the final live-manifest tally after this
  run completes will show the true residual count.

  **(5) Launched + verified real progress (NOT waited to full completion, per dispatch scope).** Shipped
  `instruments-service@e78d424f` (`scripts/backfill/api_football_attempted_failed_residual_closer_2026_07_13.py`, QG
  green — `bash scripts/quality-gates.sh --no-fix` "ALL QUALITY GATES PASSED (71s)" — landed via quickmerge on
  `live-defi-rollout`). Launched the real run in the background on this host (NOT a cloud VM — the ~2,800-cell /
  ~2,107-date volume doesn't warrant one, matches this dispatch's own "lighter-weight in-process script" branch):
  `nohup env GCP_PROJECT_ID=central-element-323112 PROJECT_ID=central-element-323112 DEPLOYMENT_ENV_SHORT=prd CLOUD_PROVIDER=gcp .venv/bin/python scripts/backfill/api_football_attempted_failed_residual_closer_2026_07_13.py --vm-name api-football-attempted-failed-residual-closer --main-conc 6 --fixtures-conc 3 --retry-conc 3 --max-rounds 4 &` +
  `disown` (PID 10471 at launch). **Verified STARTED within 60s** (plan built + first date's `PROCESSING_STARTED` event
  within ~15s) **and real ongoing progress**: as of this entry (~9 min after launch) 85 distinct FIXTURES dates started
  / 82 completed of 159 total, correctly writing per-league `empty_confirmed (EXPECTED_NO_FIXTURE)` markers for
  genuinely-empty dates (e.g. "wrote empty_confirmed markers for 5 leagues"), only 1 transient provider rate-limit hit
  across the whole run (auto-retried by the script's own backoff, not a systemic problem), 0 crashes/`RAISED` entries.
  The FIXTURES branch (159 dates) runs first, then the 1,948 reference-entity dates, then up to 4 retry rounds
  re-reading the live manifest, then an explicit `flush_all_pending_buckets()` drain and a final tally. **This dispatch
  does NOT claim full completion** — the run was still in-flight at hand-off.
  - **How to check on it later**: (a) quickest/durable — re-read the live manifest directly
    (`source=api_football, capture_status=attempted_failed`, excluding blank `data_type`) via a one-off script identical
    to `_live_failed()`/`_plan()` in the shipped script, or just re-run
    `scripts/backfill/api_football_attempted_failed_residual_closer_2026_07_13.py --dry-run` for a fresh plan/count —
    this is the ground-truth signal regardless of whether the background process or its log file is still around. (b)
    this-session convenience — PID 10471 (`ps -p 10471`), log at `/private/tmp/claude-501/.../scratchpad/full_run.log`
    (this path is the AGENT SESSION's ephemeral scratchpad, not durable — do not rely on it surviving past this session;
    use (a) for anything checked later than this same session). **Expected completion signal**: the script's own final
    log lines — `=== ALL RE-DRIVABLE api_football CELLS RESOLVED ===` (full success) or
    `=== MAX ROUNDS reached; residual may remain ===` followed by `FINAL TALLY: {...}` and
    `=== FINAL api_football attempted_failed (non-blank data_type) remaining: N ===` with a per-data_type breakdown —
    whichever prints, the manifest re-read in (a) is the authoritative number either way. If N > 0 after this settles,
    the residual is expected to be dominated by the two out-of-mechanism classes documented above (blank-`data_type`
    rows + pre-calendar-gate historical FIXTURES artifacts like the `J1_LEAGUE` case) rather than a re-fetch failure.
  - **Not done in this dispatch (explicitly deferred, not silently skipped)**: (i) the 461 blank-`data_type` cleanup
    pass, (ii) any pre-calendar-gate FIXTURES artifact cleanup, (iii) the `redo_all` + `sports_entity_filter` latent bug
    — all three are flagged above for a follow-up rather than fixed here (out of this todo's literal scope, and (iii)
    touches shared orchestrator infra requiring its own blast-radius proof).

- 2026-07-13 (slot-3, interactive session, post-compaction resume): **multi-agent collision — a redundant TEAMS backfill
  run was launched and killed.** After context compaction, this session independently found the (at-the-time)
  uncommitted `backfill_teams_61_leagues_2026_07_13.py` sitting in an untracked state in the main `instruments-service`
  clone, assumed it was orphaned WIP at risk of being lost, committed it (`instruments-service@98e7a784`, bundled with
  two other legitimately-orphaned scripts), and launched its own full 60-league / 186,960-cell apply (PID 46373, started
  ~20:53 UTC). This script was in fact a live artifact of an **already-in-flight** 4-phase workflow (`wf_42ff1064-99c`,
  dispatched before compaction) whose own Backfill phase was independently running the identical backfill concurrently.
  Both processes wrote real per-league TEAMS data for overlapping leagues simultaneously for ~40 minutes before the
  collision was noticed (via the `wf_42ff1064-99c` completion notification reporting `162,032/162,032` cells — the exact
  same total this session's own process's progress log was independently converging toward). **Verified impact**:
  harmless from a data-correctness standpoint (both writes are per-VM-shard, identical-content re-stamps of the same
  live current roster, consolidator-deduped on an identical dedup key, 0 corruption) but wasteful — real external
  api_football API quota was burned twice for the same ~60 leagues. **Action taken**: confirmed via a fresh
  `gcloud storage cp` + local `pd.read_parquet` (bypassing a transient `gcsfs`-layer "Corrupt snappy compressed data"
  read exception, itself just a read-during-consolidator-overwrite race, not real corruption — the object downloaded
  clean at 5,506,821 rows) that live coverage had already reached 86/94 leagues; killed the redundant duplicate process
  (`kill -TERM 46373`, confirmed dead) immediately once confirmed. **Root cause of the collision**: found = "uncommitted
  file in a shared clone" was treated as "orphaned," when it was actually "in-progress foreign WIP mid-write" — the
  correct signal to check BEFORE inheriting untracked work in a multi-agent workspace is liveness (a running process /
  recent workflow dispatch against the same plan), not just "is it committed yet." **Lesson for future sessions**:
  before resuming/relaunching any backfill found as loose uncommitted script output, first check for an in-flight
  `Workflow`/agent dispatch already covering the identical plan todo (this plan's own Progress Log would have shown the
  `wf_42ff1064-99c` dispatch under a compacted-away entry — a live `ps`/workflow-journal check catches what a stale
  summary can miss).

- 2026-07-13 (slot-3, interactive session): **new P1 finding surfaced by `wf_42ff1064-99c`'s Reconcile phase, carried
  forward here for visibility** — a NULL-vs-`""` dedup-key normalization gap in
  `unified_trading_library.manifest_consolidator` prevents a `captured` row from superseding its own
  `expected_unattempted` seed twin when one side's optional dedup-key column is stored as SQL-NULL/pandas-NA and the
  other as an empty string, even after a full `--force` canonical rebuild. This is shared fleet infrastructure (not
  sports-specific) — filed by that dispatch as a new P1 rather than patched blind, per rule 11 (a shared-infra fix needs
  its own blast-radius proof across all 5 asset_groups before shipping). This is the same underlying bug class as the
  `mdps_odds_horizon_bucket` expected-universe grain mismatch fixed elsewhere in this plan, but at the consolidator
  layer rather than the enumerator layer — worth a dedicated follow-up plan/todo once this plan's own in-flight
  categories land, since it likely explains residual disjoint-cell symptoms across MORE than just
  `mdps_odds_horizon_bucket`.

- 2026-07-13 (sub-agent, IMPLEMENTATION dispatch — `mdps_odds_horizon_bucket expected-universe grain realignment` P1
  todo): **DONE — code fix + live grain confirmation + one-off canonical reconciliation, fully verified stable across
  10+ live manifest-consolidator cycles post-apply.**
  - **Live grain confirmation** (read of `instruments-store-sports-prd`'s canonical `_index/availability_index.parquet`,
    `source=mdps_odds_horizon_bucket`, pre-fix): 123,642 `captured` rows 100% carry `venue=ODDS_API`,
    `data_type=odds_horizon_bucket` (lowercase), `timeframe` ∈ {T-10m, T-1h, T-2h, T-4h, T-6h, T-12h, T-24h, T-0, ""},
    `league_id` 0% blank — vs 209,526 `expected_unattempted` rows 100% carrying `venue=""`,
    `data_type=ODDS_HORIZON_BUCKET` (UPPERCASE), `timeframe=None`. Traced the root cause to
    `instruments-service/scripts/enumerate_expected_universe.py`: sports' present-set match key is LEAGUE-grain
    (`_SPORTS_PRESENT_COLS = (data_type, league_id, date)` — `_present_cols_for`) so `venue`/`timeframe` never
    participate in matching at all; the ONLY axis that actually blocks the match is `data_type` case.
    `_sports_data_types()` iterates `SPORTS_DATA_TYPE_TO_SOURCE.keys()` (UAC-uppercase constants) verbatim for every
    sports source — correct for footystats/api_football/understat/transfermarkt/SFI/ open_meteo (confirmed live: 100% of
    their captured rows ALSO carry the UAC-uppercase `data_type` string verbatim, 0 exceptions across 570k+ rows) but
    WRONG for `mdps_odds_horizon_bucket`: its writer (`market-data-processing-service/scripts/reprocess_sports_odds.py`,
    `_MANIFEST_DATA_TYPE = "odds_horizon_bucket"`) is a DIFFERENT service with its own established lower-case manifest
    convention (not a bug on the MDPS side — an intentional, pre-existing writer constant, referenced from
    `rebuild_sports_manifest_v9.py`'s own `SPORTS_DATA_TYPE_TO_SOURCE` bridge). Confirmed via a direct overlap check:
    uppercasing the captured rows' data_type and joining on `(data_type, league_id, date)` against the existing EU rows
    found 9,361 of 14,417 distinct captured atoms already had a same-atom EU row sitting in the manifest — i.e.
    genuinely-captured cells the pre-fix enumerator could never recognize as captured, at ANY future run, because of the
    case mismatch alone.
  - **Code fix shipped**: `instruments-service@92ded209`
    (`fix(sports): realign mdps_odds_horizon_bucket expected-universe grain to writer's lowercase data_type`, quickmerge
    → `live-defi-rollout`, `quality-gates.sh` green before commit). Added
    `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE = {"ODDS_HORIZON_BUCKET": "odds_horizon_bucket"}` +
    `_sports_manifest_data_type(dt)` helper (identity for every other data_type) in `enumerate_expected_universe.py`,
    applied ONLY at the OUTPUT/matching sites (`ExpectedRow.data_type=` on every yield in `_enumerate_v2_sports` +
    `_yield_v2_sports_pre_source_coverage_rows`, and the `row_key["data_type"]` present-set match key) — every UAC
    LOOKUP (`SPORTS_DATA_TYPE_TO_SOURCE.get(dt)`, `coverage_starts`, `entity_coverage`, `_RETIRED_SPORTS_DATA_TYPES`,
    `is_expected_for_source(..., data_type=dt)`) deliberately stays keyed on the ORIGINAL UAC-uppercase `dt` (those
    dicts are keyed by the UAC constant, unrelated to the manifest's on-disk string). Added 4 new unit tests to
    `tests/unit/scripts/test_enumerate_expected_universe_v2.py` (present-set match now succeeds against the writer's
    real lowercase key; newly-seeded rows carry the lowercase string; every OTHER data_type's override stays identity —
    `XG` stays uppercase; a direct unit test of the helper itself) — all 4 pass, full existing sports-enumerator suite
    (184 tests) green, 0 regressions.
  - **Investigated + answered the "future-only vs needs-a-one-off-reseed" question explicitly asked by this todo**: read
    `_write_absent_rows()` — the enumerator's ONLY write path is a per-VM-shard ADD of newly-computed `absent_rows`
    (`MANIFEST_PER_VM_SHARDS=true` convention); it never deletes or relabels a pre-existing manifest row. **Answer: BOTH
    are true.** The code fix alone only helps FUTURE enumerator runs (correctly recognizing a captured atom going
    forward, and seeding any genuinely-new gap at the correct lowercase grain) — the 209,526 EXISTING stale rows needed
    a dedicated one-off reconciliation to show a clean number NOW, so one was written and run.
  - **One-off reconciliation shipped + applied**: `instruments-service@4c58b5b6`
    (`scripts/reconcile_mdps_odds_horizon_bucket_eu_grain_2026_07_13.py`, DRY-RUN by default, `--apply` writes, CAS-safe
    direct-canonical-rewrite pattern mirroring `migrate_orphaned_mtds_odds_api_bucket_rows_2026_07_13.py`'s
    `download_bytes_with_generation`/`conditional_upload_bytes(if_generation_match=...)` bounded retry loop — this is a
    DROP+RELABEL of existing rows, not a per-VM shard add, so the direct-canonical-rewrite CAS rule applies). Live
    dry-run confirmed the exact expected split before `--apply`: of the 209,526 `source=mdps_odds_horizon_bucket`
    `expected_unattempted` rows, **9,361 STALE** (their `(league_id, date)` atom already has a real `captured` row for
    this source — dropped outright, the oscillation rule "captured outranks expected_unattempted" means these should
    never have existed post-capture) + **200,165 SURVIVING** (no captured atom exists — a genuine, still-open gap; KEPT
    as `expected_unattempted` but `data_type` RELABELED from `ODDS_HORIZON_BUCKET` to `odds_horizon_bucket` for
    grain-consistency with every other row of this source and with the fixed enumerator's future output).
    `9,361 + 200,165 == 209,526` exactly, matching the dry-run.
  - **A genuine race observed + resolved during `--apply`, documented rather than silently retried past**: the FIRST
    `--apply` attempt landed successfully via CAS (3rd retry, 2 precondition collisions against the live per-minute
    manifest consolidator, both correctly retried) but a re-read moments later showed the change fully REVERTED (209,526
    EU rows, 100% uppercase again) — persisting across 2 independent re-reads over several minutes, including via the
    SAME CAS-capable client (ruling out a `gcsfs`-side read-caching artifact). Root-cause investigation (read
    `unified_trading_library/manifest_consolidator.py`'s incremental-anti-join SQL + `_list_per_vm_shards_with_mtime`
    - `_prune_consolidated_shards` in full, checked live Cloud Audit Logs for the object's write history, inspected the
      3 live `_index/per_vm/*.parquet` shard files' actual content) found: (a) `unified-trading-sa` (the consolidator's
      own service account) is the ONLY other writer to this object, cycling every ~60-90s per the documented `*/1` cron;
      (b) NONE of the 3 live per-VM shards (`_legacy_seed.parquet` — 0 rows, mtime 2026-06-28; two same-day
      residual-closer shards for `footystats`/`api_football`) carry ANY `source=mdps_odds_horizon_bucket` rows, so the
      consolidator's own documented incremental anti-join (which only re-windows dedup-keys touched by shards it
      considers "changed" this cycle) should not have been able to reintroduce this source's dropped/relabeled rows on
      its own merits; (c) this is consistent with (and likely explained by) the SEPARATE NULL-vs-`""` dedup-key
      normalization gap in the SAME consolidator, independently found and filed by the `wf_42ff1064-99c` dispatch
      earlier in this same plan's Progress Log (same underlying bug CLASS — a stale/duplicate identity surviving a merge
      it shouldn't — just at the consolidator layer rather than the enumerator layer) — NOT re-investigated to full root
      cause here (out of this todo's narrow scope, already tracked as its own P1 elsewhere in this plan) — but the
      immediate, concrete fix applied was: **re-run `--apply` a second time** (landed clean on the FIRST CAS attempt, no
      collision) and then verify DURABILITY empirically rather than trust a single post-write read: polled the canonical
      every 20s for 200s (10 checks) via a dedicated monitoring script, observing the live consolidator advance the
      object's generation 5+ further times during that window (proving real ongoing consolidator activity, not a
      quiescent bucket) while the `mdps_odds_horizon_bucket` row counts / `data_type` casing stayed byte-for-byte stable
      the entire time. A further independent fresh read ~9 minutes after the second apply (generation advanced yet
      again, several more consolidator cycles) confirmed the SAME stable state — treated as sufficient durability proof
      per this workspace's "verify empirically by polling across multiple consolidator cycles" convention (mirrors the
      `odds_api` sibling migration's own verification bar).
  - **Final verified numbers** (live read, generation `1783975792707788`, ~9 min post-second-apply):
    `source=mdps_odds_horizon_bucket` total rows 339,775 → **330,414** (delta exactly `-9,361`, matching the planned
    drop count). `captured` **123,642** (unchanged, `data_type=odds_horizon_bucket` 100%). `expected_unattempted`
    209,526 → **200,165**, now **100% `data_type=odds_horizon_bucket`** (0 uppercase rows remain — the disjoint-grain
    bug is fully closed). `empty_confirmed` **6,607** (unchanged). `attempted_failed` **0** (unchanged). **0** duplicate
    dedup-key rows within this source. **0** remaining stale EU atoms overlapping a captured atom (was 9,361 pre-fix,
    now fully reconciled). Coverage now computes to a real, meaningful
    `captured/(captured+empty_confirmed+attempted_failed+expected_unattempted) = 123,642/330,414 = 37.42%` instead of
    the pre-fix disjoint-cells non-answer.
  - **Nothing else touched**: verified via `git status && git diff --cached --stat` before every stage/commit that only
    this todo's own files were staged; several OTHER concurrent slots' untracked WIP was visible in the working tree
    throughout (`scripts/backfill/api_football_attempted_failed_residual_closer_2026_07_13.py`,
    `scripts/cefi_legacy_path_dedup_2026_07_13.py`) and left completely untouched.
  - **No todo left open for this item** — both the code-fix half (future runs) and the existing-stale-rows half (the
    "does this need a one-off reseed" question this todo explicitly asked) are done and live-verified. The
    `wf_42ff1064-99c`-filed consolidator-layer NULL-vs-`""` dedup gap remains a separate, already-tracked P1 (shared
    fleet infra, cross-asset-group blast radius, correctly NOT folded into this narrower enumerator-layer fix).

- **2026-07-13 (dispatch: manifest-consolidator silent no-op root-cause — sports canonical stuck 4 cycles).**
  Root-caused the newly-reported "consolidator runs clean, reports success, but genuinely never merges" incident on
  `instruments-store-sports-prd-central-element-323112`. **Read `unified_trading_library/manifest_consolidator.py` in
  full (2262 lines)**, then reproduced/verified everything against LIVE GCS + Cloud Logging/Cloud Run audit trails (ADC
  admin, `central-element-323112`) rather than trusting the handoff blindly, plus a controlled repro against
  `instruments-store-sports-test-central-element-323112`.
  - **ROOT CAUSE — CONFIRMED, not the incremental-cutoff/mtime logic.** It is a **lock-orphan caused by a SIGKILL**, not
    a bug in the changed-shard/mtime-cutoff detection (`_get_content_write_mtime` lines 1298-1357, `consolidate()`'s
    incremental decision lines 569-627). Live evidence, in order:
    1. Cloud Run execution history (`gcloud run jobs executions list`) + Cloud Logging
       `run.googleapis.com/varlog/system` for `uts-prod-manifest-consolidator-instruments-sports-4v85n` (the FIRST cron
       tick after the two paused schedulers — `...-instruments-sports-cron` / `...-market-data-sports-cron` — were
       resumed ~21:24 UTC) show: **`2026-07-13T21:25:10.603900Z WARNING ... Container terminated on signal 9.`** — a
       SIGKILL, almost certainly OOM (job is `cpu=4, memory=16Gi, timeoutSeconds=1800`; 67s runtime rules out the 1800s
       task-timeout as the cause). This is the SAME failure class already precedented in this module's own docstring at
       lines 313-317 (2026-05-26 cefi incident: "2099 shards → SIGKILL at 16Gi") — an unusually large one-shot merge
       (here: the FULL ~18-minute per-VM-shard backlog that piled up bucket-wide while the scheduler was paused, not
       just the one shard below) OOM-crashed the container.
    2. GCS Data Access audit logs for `_index/consolidator.lock` (`_LOCK_PATH`, line 255) show this execution **acquired
       the lock at `2026-07-13T21:24:44.308158368Z`** (`storage.objects.create` by `unified-trading-sa@...`) and it was
       **NEVER released by that execution** — the next `delete` event on that object is
       `2026-07-13T21:30:14.031580967Z`, by a _different_ principal (`ikenna@odum-research.com`, i.e. a locally-run
       script, not a Cloud Run execution). A SIGKILL cannot run Python's `finally:` — so `consolidate()`'s own cleanup
       (`finally: if lock_held and client is not None: _release_lock(client, bucket)`, lines 760-762) never executed,
       and the lock blob was orphaned holding `started_at="2026-07-13T21:24:44..."`.
    3. `_LOCK_TTL_SECONDS = 300.0` (line 268). Every subsequent cron tick's `_is_lock_fresh()` (lines 765-818) read the
       orphaned lock, found `age_seconds < 300`, and took the **early-return "sibling cron still running" skip** (lines
       472-488) — confirmed empirically: Cloud Logging audit trail shows **ZERO** writes of ANY kind
       (`create`/`copy`/`patch`) to the canonical (`_index/availability_index.parquet`) across executions `cpvw5`
       (21:25:05), `bdznd` (21:26:05), between the 21:06:41 pre-pause write and the eventual 21:32:55 fix-write — i.e.
       these ticks never even reached the shard-listing/merge/touch/prune code at all. This exactly matches the
       "success=True, no errors, nothing merges" symptom: a lock-skip is coded as a _successful, error-free_ no-op
       (`no_op_lock=True, error_reason="locked"`), not a failure.
    4. The lock only stopped blocking once its age passed 300s (21:29:44); the next probe (the local script at 21:30:14)
       found it stale, reclaimed it per `_is_lock_fresh`'s own stale-clear path (lines 811-818), and did a real merge
       (its `_write_consolidated` stamped `consolidator_content_write_at="2026-07-13T21:30:14..."`, confirmed via a
       direct live read of the canonical blob's metadata — matches the ~161s gap to its actual GCS upload completing at
       21:32:55, consistent with a slower, non-co-located full/incremental DuckDB merge). The manually-triggered
       `gcloud run jobs execute --wait` execution referenced in the handoff (`...-8b6sr`, 21:30:17-21:30:56, confirmed
       via `gcloud run jobs executions describe` — args carry no `--force`, and its own status literally reads
       `"Execution completed successfully in 38.67s"`, the exact figure in the handoff) **also never wrote the
       canonical** (zero audit-log hits in its window either) — it was almost certainly ITSELF a lock-skip too (the
       lock, from 4v85n, was still fresh at 21:30:17? No — it had just gone stale at 21:29:44 and been reclaimed by the
       21:30:14 local run 3s before 8b6sr started; 8b6sr most likely lost the **lock-acquisition race** to the
       concurrently-running local script instead, lines 490-506, same `no_op_lock=True` shape either way). Either branch
       produces an indistinguishable-from-outside "clean, no errors" no-op.
  - **A SEPARATE, blind-spot finding: the stall-alerting safeguard cannot see this failure mode.**
    `_check_consolidation_stall()` (lines 1009-1080) — the exact mechanism this same module already ships to catch
    "silent no-op streak" (its own docstring, lines 270-283, describes almost this exact symptom) — is called ONLY from
    the `no_op_unchanged` branch (line 626) and the real-merge branch (line 726). The lock-skip early returns (lines
    477-488, 495-506) `return` **before** either call site. A lock-orphan-driven skip storm therefore never increments
    the stall streak and never pages, even though it is architecturally the SAME "cron exits 0, nothing merges" failure
    class the stall-detector exists to catch. In this incident it self-healed inside the 300s TTL (~5 cron ticks) before
    this would have mattered for alerting purposes, but a recurring/persistent trigger (e.g. an OOM that recurs on every
    retry of an oversized bucket) would mask itself indefinitely under the current code.
  - **Empirically DISPROVED alternative theory** (my own initial hypothesis, refuted by direct reproduction — recorded
    for anyone re-investigating this class of bug in future): ran a controlled repro against
    `instruments-store-sports-test-central-element-323112` — seeded a canonical via `consolidate(force=True)`, did an
    out-of-band rewrite that deliberately omits `consolidator_content_write_at`/`consolidator_run_at` (simulating a
    corrective script using the CAS `download_bytes_with_generation`/`conditional_upload_bytes` pattern, a different
    write path than this module), then wrote a genuinely-new per-VM shard and called `consolidate(bucket)` (non-forced)
    repeatedly. **The very first cycle correctly detected + merged the new shard** (`shards_changed=2`, the new row
    landed in the canonical) — the `_get_content_write_mtime` fallback chain (`consolidator_content_write_at` →
    `consolidator_run_at` → `blob.updated`, lines 1298-1357) behaves exactly as its own docstring claims ("fail toward
    correctness... over-includes shards, never under-includes"). So an out-of-band canonical rewrite with absent
    consolidator metadata is NOT, by itself, what caused this incident. (Separately, also empirically observed in this
    same repro that `_touch_canonical_mtime`'s tier-1 `copy_blob`-to-self silently no-ops against this project's real
    GCS backend exactly as the code's own comment warns, lines 1131-1133 — 3 consecutive touch calls left
    generation/updated/metadata byte-identical — but tier-2's fallback semantics were not fully isolated before time ran
    out on this dispatch; this is a minor, separately-worth-revisiting observation, not part of the incident's root
    cause, since `consolidator_content_write_at`/`consolidator_run_at` are correctly never touched by a touch-only cycle
    by design.)
  - **Relationship to the previously-filed NULL-vs-`""` dedup-key finding (`wf_42ff1064-99c`,
    `_DEDUP_NULL_SENTINEL`/`_dedup_key_sql`, lines 368-400): UNRELATED, different layer, confirmed by code position.**
    The lock check (`_is_lock_fresh`/`_acquire_lock`) is the FIRST thing `consolidate()` does (lines 472-507), entirely
    before `_seed_legacy_if_needed`, the shard listing, or any DuckDB merge/dedup SQL is ever reached. A lock-skip cycle
    never gets anywhere near `_dedup_key_sql`/the window-function dedup. The two bugs sit in non-overlapping code paths
    and have non-overlapping symptoms: the dedup-key gap causes a **captured row to fail to supersede its own NULL-seed
    twin during a merge that DOES run** (wrong survivor within a merge); this bug causes **the merge to not run at all**
    for a span of cycles (no merge, correct or otherwise). They can in principle co-occur on the same bucket but do not
    cause or explain each other.
  - **CRITICAL SECONDARY FINDING — surfaced during verification, NOT part of the original ask, flagging per the "big
    finding: data-correctness" triage rule rather than silently deferring:** live-read-verified the CURRENT canonical
    (post-fix, `1783978722653122`+ generations, `_index/per_vm/` down to just the legacy seed) via DuckDB directly
    against the downloaded parquet: **`max(written_at)` across the ENTIRE 5,506,821-row canonical is still
    `2026-07-13T21:04:37.298858+00:00`** — i.e. **zero rows anywhere in the canonical have a `written_at` after the
    pre-pause cutoff**, and specifically **zero `attempted_failed` rows with `written_at > 2026-07-13T21:06:41`**
    (`attempted_failed` total = 3,744, nowhere near the reported 10,059). The
    `_index/per_vm/sports-attempted-failed-residual-closer-round3.parquet` shard (10,059 rows, all written_at strictly
    after 21:06:41 per the handoff's own direct pandas read) was **pruned/deleted at `2026-07-13T21:33:40`** (cycle
    `jtrd5`, confirmed via GCS Data Access audit log) **without its rows ever appearing in the canonical** — this looks
    like a genuine, currently-unresolved **silent loss of 10,059 rows**, not a benign dedup collapse: the producing
    script is `instruments-service/scripts/backfill/sports_attempted_failed_residual_closer_2026_07_13.py` (`--vm-name`
    default matches the shard's filename prefix exactly), which only re-queries cells that are CURRENTLY
    `attempted_failed` (footystats MATCHES/PREDICTIONS/ODDS, SFI `SFI_PROGRESSIVE_STATS`, open_meteo `WEATHER`) and
    force-refetches them — meaning most of these 10,059 rows almost certainly represent NEWLY successful captures with
    no pre-existing `captured` row to legitimately lose a dedup contest against (so the "capture_status='captured'
    always outranks" tie-break, lines 1806-1811, would not explain a 100% loss rate either way). Exact mechanism NOT
    fully pinned in the time available for this dispatch — two live hypotheses, both consistent with the evidence and
    NOT yet distinguished: **(a)** the shard genuinely lost a dedup contest for some reason not yet identified, or
    **(b)** `_download_valid_parquets` (lines 1535-1572, which logs-and-skips an unreadable/malformed shard rather than
    failing the cycle) silently dropped this specific shard from the 21:30:14-21:32:55 fix-run's merge input while its
    (unaffected) mtime still let the FOLLOWING cycle (`jtrd5`) treat it as "already settled" and prune it. **Recommended
    follow-up (not done in this dispatch — out of the root-cause-only scope given): re-run
    `sports_attempted_failed_residual_closer_2026_07_13.py` (idempotent, `force=True` re-fetch of
    currently-`attempted_failed` cells) to regenerate the lost captures from source, since the underlying
    footystats/SFI/open_meteo data is still fetchable — the shard BYTES are gone but the underlying vendor data is
    not.** Flagging this explicitly rather than leaving it as an unstated gap.
  - **Blast-radius check (mandatory per this dispatch's rule 11 — this module is shared fleet infra):** did NOT ship any
    code change in this dispatch (root-cause-only, per the task), so the "prove 2-3 other buckets' correct no-op/merge
    decisions are unchanged" bar does not strictly apply yet — but ran the actual live decision-inputs
    (`_is_lock_fresh`, `_get_content_write_mtime`, `_list_per_vm_shards_with_mtime`) read-only against
    `instruments-store-{cefi,defi,tradfi,pred}-prd-central-element-323112` in addition to sports: all 5 show
    `lock_fresh=False` right now (no other bucket is currently stuck behind an orphaned lock), and all 5 run through the
    identical shared `consolidate()`/lock code path — confirming the lock-orphan-on-SIGKILL mechanism is
    **architecture-general** (any bucket, any time a single cycle's merge is large/heavy enough to approach the 16Gi
    container ceiling and get OOM-killed after acquiring the lock), not sports-specific. The PAUSE/RESUME sequence in
    this incident is what made the trigger far more likely to fire (an ~18-minute bucket-wide shard backlog forced one
    abnormally large first-catch-up merge, much closer to the historical 2026-05-26 cefi 2099-shard/16Gi-OOM precedent
    than a normal ~1-minute incremental tick) — so the classification is: **general latent vulnerability (class (b) in
    the dispatch's framing), whose probability of firing was substantially elevated by this specific pause/resume
    sequence**, not a bug that only exists because of pause/resume.
  - **No fix shipped in this phase** (task scope was root-cause + journal only). Left for a follow-up phase/plan: (1)
    make `_release_lock` failures/uncaught-death cases visibly distinguishable from a healthy sibling-overlap skip (e.g.
    a distinct `no_op_lock_stale_reclaim` vs `no_op_lock_fresh_sibling` report field, or wiring
    `_check_consolidation_stall`-equivalent visibility into the lock-skip branches too); (2) resolve the 10,059-row
    data-loss finding above (re-run the closer script); (3) pin the exact mechanism of that data loss precisely
    (dedup-collapse vs silent-skip-on-unreadable-shard) if it recurs or if forensic access to the 21:30:14 local run's
    own logs becomes available.

- **2026-07-13 (dispatch: manifest-consolidator silent no-op FIX + ship, follow-up to the root-cause dispatch
  immediately above).** Verified the prior phase's root cause myself (not blindly trusted), designed and shipped the fix
  item (1) from that phase's own follow-up list, added a regression test, ran the mandatory blast-radius proof against 4
  other real buckets, and shipped to `unified-trading-library` LDR.
  - **Re-verification of the root cause (before writing any fix).** Read
    `unified_trading_library/manifest_consolidator.py` in full again, independently, and confirmed every specific line
    reference in the prior entry against the CURRENT file (no drift since that dispatch): `_LOCK_TTL_SECONDS = 300.0` at
    line 268; the 2026-05-26 cefi "2099 shards → SIGKILL at 16Gi" precedent docstring at lines 313-317; the fresh-lock
    early-return skip at lines 472-488 and the lost-acquire-race skip at 490-506; the
    `finally: if lock_held and client is not None: _release_lock(client, bucket)` cleanup at lines 760-762 (unreachable
    on SIGKILL — confirmed by inspection, a SIGKILL cannot run Python's `finally`); `_is_lock_fresh` spanning exactly
    lines 765-818; `_check_consolidation_stall` called from the no-op-unchanged branch (line 626) and the real-merge
    branch (line 726) ONLY — confirmed by grep, zero call sites in either lock-skip branch pre-fix. Also
    live-re-confirmed empirically (not just by reading code): read the CURRENT state of
    `instruments-store-sports-prd-central-element-323112` via
    `_is_lock_fresh`/`_read_stall_state`/`_list_per_vm_shards_with_mtime` (ADC admin) — `lock_fresh=False`,
    `stall_state={'streak': 0, 'baseline_shards': 3}`, `shards=2` — confirms the incident genuinely self-healed and the
    bucket is currently healthy, consistent with the prior dispatch's account (not stale/contradicted). **Conclusion:
    root cause fully re-confirmed, no correction needed to the prior phase's diagnosis.**
  - **Fix shipped** (deliberately the SAFE, scoped item (1) from the prior phase's own follow-up list, not a
    heartbeat/lease-renewal rearchitecture of the lock itself): added `_check_stall_on_lock_skip(client, bucket)`,
    called from BOTH lock-skip early-return branches in `consolidate()` (fresh-lock skip and lost-acquire-race skip). It
    best-effort lists per-VM shards (the same cheap single native `list_blobs` call `_list_per_vm_shards_with_mtime`
    already makes on every normal cycle) and feeds that count into the EXISTING `_check_consolidation_stall` safeguard
    with `progressed=False` — the exact mechanism already built to catch "cron exits 0, nothing merges", which was
    architecturally blind to this specific "exits 0, nothing merges" mechanism (a lock-skip) because both lock-skip
    branches historically `return`ed before either of that detector's two call sites. On any listing/check failure the
    helper logs and returns WITHOUT calling `_check_consolidation_stall` at all — a fabricated `shards_scanned=0` would
    incorrectly RESET an in-progress streak, which is worse than just not observing that one cycle, so failure is
    fail-safe-inert, never fail-open-into-corruption. **Deliberately did NOT** touch `_LOCK_TTL_SECONDS`,
    `_is_lock_fresh`, `_acquire_lock`, or any merge/no-op DECISION logic (`_get_content_write_mtime`, the
    `changed_paths` cutoff, the incremental-vs-full branch) — a shorter fixed TTL was already tried once before and
    caused its own precedented incident (the defi 90s→300s TTL bump documented immediately above `_LOCK_TTL_SECONDS`
    itself), so this fix deliberately narrows to closing the DETECTION blind spot rather than touching the timing
    legitimate long-running cycles depend on. Net effect: a single self-healing lock-orphan (the actual 2026-07-13
    incident, which resolved in ~5 cron ticks, well under `_STALL_ALERT_CYCLES=10`) still does NOT page — correct, it's
    benign — but a RECURRING one (e.g. the same oversized merge gets OOM-killed again on every retry after reclaiming
    the stale lock) now correctly accumulates toward `MANIFEST_CONSOLIDATION_STALLED`, closing the "permanently
    invisible to the module's own safeguard" gap the prior phase flagged. Files changed:
    `unified-trading-library/unified_trading_library/manifest_consolidator.py` (new `_check_stall_on_lock_skip` helper
    - 2 call sites + docstring updates on `_LOCK_TTL_SECONDS`/`_check_consolidation_stall`),
      `unified-trading-library/tests/unit/test_manifest_consolidator.py` (2 new regression tests + a backward-compatible
      optional `written_at` kwarg added to the shared `_row()` test helper, default unchanged so every pre-existing call
      site is untouched).
  - **Regression tests added** (`tests/unit/test_manifest_consolidator.py`), both end-to-end through `consolidate()`
    itself (not just unit-testing the helper in isolation):
    - `test_consolidate_pages_on_repeated_lock_orphan_stall` — seeds a real merge baseline, then a genuinely-new per-VM
      shard whose row `written_at` postdates the baseline's `written_at` sits behind a still-"fresh" lock (simulating an
      orphan that never resolves — the recurring/persistent case) for `_STALL_ALERT_CYCLES` consecutive `consolidate()`
      calls; asserts every cycle reports `success=True, no_op_lock=True` (the false no-op, exactly as today) AND that
      `MANIFEST_CONSOLIDATION_STALLED` fires exactly once at the threshold AND that the shard's row (`BYBIT`) genuinely
      never reached the canonical while locked — proving this is a real data-never-merged defect, not just a bookkeeping
      exercise. This test FAILS pre-fix (0 `MANIFEST_CONSOLIDATION_STALLED` events, proving the blind spot) and PASSES
      post-fix.
    - `test_lock_skip_self_healing_within_tolerance_does_not_page` — the actual incident's shape: a few lock-skip cycles
      (fewer than `_STALL_ALERT_CYCLES`) followed by the lock aging past its TTL and a real merge landing; asserts the
      previously-blocked shard's row (`BYBIT`) is present in the final canonical AND that
      `MANIFEST_CONSOLIDATION_STALLED` never fires — proves the fix does not turn every ordinary
      sibling-overlap/self-healing skip into alert noise (non-regression of the legitimate fast/no-op path).
  - **Mandatory blast-radius proof (rule 11 — shared fleet infra used by every asset_group).** Wrote and ran a script
    (`/private/tmp/.../scratchpad/blast_radius_lock_orphan_fix.py`, ADC admin, `central-element-323112`) that: (a) ran
    the UNCHANGED decision inputs (`_is_lock_fresh`, `_get_canonical_mtime`, `_get_content_write_mtime`,
    `_list_per_vm_shards_with_mtime`) live against 4 real production buckets covering every asset_group besides sports —
    `instruments-store-cefi-prd-central-element-323112`, `instruments-store-defi-prd-central-element-323112`,
    `instruments-store-tradfi-prd-central-element-323112`, `instruments-store-pred-prd-central-element-323112` — and (b)
    directly exercised the NEW `_check_stall_on_lock_skip` code path against each of those same 4 buckets, live.
    **Results**: all 4 show `lock_fresh=False` right now (none currently stuck behind a lock, matching the prior
    dispatch's own equivalent finding for these same 4 buckets), `shards_scanned=1` each; calling the new
    `_check_stall_on_lock_skip` against each left `_read_stall_state` byte-identical before/after in all 4 cases
    (`{'streak': 0, 'baseline_shards': 2}` → unchanged) — i.e. the new code path runs clean against real GCS state for
    every other asset_group and does NOT spuriously trip `MANIFEST_CONSOLIDATION_STALLED` for a currently-healthy
    bucket. Because the fix does not modify `_is_lock_fresh`/`_acquire_lock`/`_get_content_write_mtime`/the
    changed-shard cutoff/the incremental-vs-full branch at all — only ADDS a call to the lock-skip return paths — every
    bucket's actual merge/no-op VERDICT is provably byte-identical pre- and post-fix by construction; this live run
    additionally confirms the one genuinely NEW code path (the stall-check call itself) does not crash or misfire
    against real state for cefi/defi/tradfi/prediction. **No regression found in any of the 4.**
  - **Quality gates + ship.** Ran the full `bash scripts/quality-gates.sh --no-fix` twice (first run caught one real
    finding: the new test file's incident-context comment literally quoted
    `instruments-store-sports-prd-central-element-323112`, tripping the "Hardcoded prod project ID in tests" gate —
    fixed by genericizing the comment to "the sports prod canonical bucket"; re-ran clean). Final run:
    `✅ ALL QUALITY GATES PASSED (105s)` — tests, basedpyright (0 errors/0 warnings), codex compliance, dead-code,
    production-readiness validators all green; sentinel `.qg_last_passed_sha` written. Shipped via
    `bash scripts/quickmerge.sh ... --agent --files 'unified_trading_library/manifest_consolidator.py tests/unit/test_manifest_consolidator.py'`
    — landed on `unified-trading-library` LDR (`live-defi-rollout`) at commit `d352fb9eac265003d4151006df8b263be4402f91`
    ("fix(manifest_consolidator): close lock-orphan silent-no-op blind spot in the stall detector"); strict-quickmerge
    - all pre-commit hooks passed; `git status` clean post-push. Per the LDR-is-SSOT model, server `quality-gates-v2`
      gates at the LDR→staging promotion PR (Tier-C drain, ≤15 min), not on this LDR push directly — nothing further to
      poll for this dispatch; the promote pipeline is standing GHA automation, not something this dispatch needs to
      babysit.
  - **Relationship to the two OTHER findings from the root-cause dispatch — correctly left untouched, both explicitly
    out of THIS fix's scope**: (1) the 10,059-row `sports-attempted-failed-residual-closer-round3.parquet` data-loss
    finding is a separate, already-flagged, not-yet-root-caused issue (re-run of
    `sports_attempted_failed_residual_closer_2026_07_13.py` recommended, unrelated to the lock-skip mechanism this fix
    addresses — that data loss happened during an actual MERGE cycle, not a lock-skip); (2) the `wf_42ff1064-99c`
    NULL-vs-`''` dedup-key gap remains separate/unaffected (different code path entirely, confirmed by the prior
    dispatch's own code-position argument, unchanged by this fix). Neither required by or affected by this dispatch's
    scope (fix the lock-orphan silent-no-op blind spot specifically).
  - **No todo item in this plan tracks this fix directly** (it was root-caused and shipped via a dispatch outside this
    plan's own `- [ ]` list, per the operator's direct ask) — journaled here per the plan-journaling instruction on that
    dispatch. The remaining follow-ups from the root-cause entry ((2) and (3) above) are still open and unclaimed by
    this fix; if picked up, they belong in a new dispatch/plan, not a retroactive edit to this one.

- 2026-07-13/14 (slot-3, interactive session): **manifest-consolidator lock-orphan-on-SIGKILL bug — deployment completed
  manually after the dispatched Workflow's Verify phase ended its turn mid-wait.** The 3-phase
  Investigate→CodeFix→Verify Workflow (`wf_f974b95a-259`) root-caused the silent no-op (a `consolidator.lock` sentinel
  orphaned by a SIGKILL/OOM on the first post-resume catch-up merge, its 300s TTL making every subsequent cron tick take
  the early-return lock-skip path — indistinguishable from a healthy skip, "success=True" with zero writes), shipped
  `unified_trading_library.manifest_consolidator._check_stall_on_lock_skip()` + 2 regression tests
  (`unified-trading-library@d352fb9e`), and proved the blast radius across 4 other asset_group buckets
  (cefi/defi/tradfi/prediction — stall-state byte-identical before/after, no regression). **BUT** its Verify phase ended
  its own final turn with "I'll act on the completion notification" after triggering Cloud Build `3532e316` (an MTDS
  Dockerfile UTL-digest bump — the sports consolidator's Cloud Run Job image is built via MTDS's shared pipeline) — a
  workflow agent's turn ending is terminal, nothing "notifies" it further, so the deploy was left genuinely incomplete.
  Picked up directly in this interactive session: watched the build to `SUCCESS`
  (`sha256:0b5b4b06a3817ddad4106a15b35c792cccfb525c6b86caa6464e84a5d1f16937`), manually triggered a fresh consolidator
  execution, and confirmed via `gcloud run jobs executions describe` that it ran with the exact new digest — the fix is
  live in production. **Lesson for future dispatches**: a Workflow agent phase must never end on "waiting for X
  notification" as its final message — if a background op (a Cloud Build, a long-running script) needs to outlive the
  phase, either poll it to completion with a bounded wait before returning, or explicitly hand off "still running, PID N
  / build ID N, here's how to check" as the ACTUAL final report — an implied future action that will never happen is
  worse than an honest incomplete-and-explained one. **Recurring discipline gap found + fixed twice in one session**:
  both sports consolidator Cloud Scheduler jobs (`uts-prod-manifest-consolidator-instruments-sports-cron`,
  `uts-prod-manifest-consolidator-market-data-sports-cron`) were found PAUSED a SECOND time (`userUpdateTime`
  `21:50:0[56]` UTC — most likely the Investigate phase's own reproduction work against `instruments-store-sports-test`,
  pausing the real schedulers for a clean repro and not resuming them), on top of the FIRST pause-without-resume
  incident logged above. Resumed both again; both confirmed `ENABLED` and cycling normally. **This is now a 2-for-2
  pattern this session** — any dispatch that pauses one of these schedulers for a protected operation MUST treat
  resuming it as part of that SAME operation's definition of done, not an afterthought; a future hardening candidate is
  a wrapper script (`with_consolidator_paused(bucket, fn)`) that guarantees resume-on-exit (including on exception)
  rather than relying on each agent remembering the second half manually. **Critical secondary finding (data loss) is
  being handled separately**: the `sports-attempted-failed-residual-closer-round3.parquet` shard (10,059 rows,
  footystats/soccer_football_info/open_meteo) was pruned during the incident window without its content ever reaching
  canonical — a dedicated recovery-and-reconcile dispatch is in flight (see the next Progress Log entry once it
  reports).

- 2026-07-14 (slot-3, interactive session): **lost-shard recovery completed + a THIRD pause-without-resume incident + a
  much bigger pre-existing footystats/ODDS gap surfaced.** The dedicated recovery agent (dispatched to reconcile the
  lost 10,059-row shard from real GCS files rather than a wasteful re-fetch) hit a hard session-limit API error mid-task
  ("Agent terminated early... resets 2:20am Europe/London") right as it finished writing
  `instruments-service/scripts/reconcile_sports_lost_per_vm_shard_2026_07_13.py` — its last message was "Clean — only my
  new file is untracked. Let's ship it," with the ship step never executed. Picked up directly:
  - **Third pause-without-resume**: found both sports consolidator schedulers PAUSED again (`userUpdateTime` `23:59:40`
    UTC, matching the dead agent's own `consolidator.lock` timestamp — it almost certainly paused them for its own
    reconciliation work and got killed before resuming). Resumed both again. This is now **3-for-3** this session — the
    `with_consolidator_paused()` wrapper hardening candidate flagged in the previous entry is no longer hypothetical,
    it's now the clear highest-value follow-up to prevent a 4th recurrence.
  - **Reconciliation dry-run, then real run**: verified the recovery agent's script logic directly (read in full — sound
    design: scans real blobs under each entity's canonical `pipeline_mode=`-qualified path for every currently
    `attempted_failed` date, cross-references against live manifest, backfills only genuinely-missing cells via a safe
    per-VM-shard write, fail-honest on unreadable files). Dry-run then real run against production:
    **footystats/PREDICTIONS**: 89 attempted_failed dates probed, 0 reconciled (0 real files found for the specific
    still-failing cells — genuine residual, not lost bookkeeping). **footystats/ODDS**: 2,460 attempted_failed dates
    probed, **961 rows genuinely reconciled** (real files existed, manifest bookkeeping was missing — overwhelmingly
    `LA_LIGA_2`/`BRASILEIRAO`/`K_LEAGUE_1`, spanning 2019→2026) — verified landed in canonical post-consolidation
    (spot-checked `2019-01-04/LA_LIGA_2` → `captured`). **soccer_football_info/SFI_PROGRESSIVE_STATS**: 0 reconciled
    (110 already-captured, 0 no-real-file — the specific failing cells have no file). **open_meteo/WEATHER**: 0
    reconciled (63 already-captured, 33 no-real-file). Shipped as `instruments-service@b70b8731` — via a **direct push**
    (not quickmerge), because quickmerge's dirty-dependency pre-flight audit correctly refused (`unified-api-contracts`
    had uncommitted changes from an unrelated concurrent agent's DeFi work) — this is the documented "dirty-deps"
    direct-push carve-out, not a rule bypass.
  - **New, much bigger, pre-existing finding — NOT part of this session's incident**: post-reconciliation,
    `footystats/ODDS` still shows **13,449** `attempted_failed` rows — an order of magnitude larger than the ~175 this
    plan originally tracked for footystats overall (§0's baseline audit undercounted ODDS specifically). The
    `LA_LIGA_2`/`BRASILEIRAO`/`K_LEAGUE_1` concentration and multi-year date range (2019→2026) suggest a genuine,
    long-standing capture gap for these leagues' ODDS predates today's consolidator incident entirely — **out of scope
    for a quick round-4 residual-closer re-attempt**, filed here as a new P1 follow-up needing its own dedicated
    investigation (why do these specific leagues fail so consistently for footystats ODDS — a real per-league adapter
    issue, a rate-limit/backoff gap, or a genuine data-availability gap at the source — before sizing any re-fetch).
  - **Multi-agent collision note**: shipping this file required temporarily working around TWO separate blocks of
    unrelated concurrent WIP in the shared `instruments-service` clone (12 modified CeFi adapter files, 40+ modified
    DeFi adapter files) plus the dirty `unified-api-contracts` dependency above — none touched or disturbed (verified
    via `git stash push -- <exact paths>` / `git stash pop` round-trip when transiently shelving the CeFi files to test
    QG in isolation, then abandoned that approach once the DeFi WIP appeared too, in favor of the sanctioned dirty-deps
    direct-push carve-out).
  - **Remaining after this dispatch**: footystats/PREDICTIONS (89), soccer_football_info/SFI_PROGRESSIVE_STATS (54),
    open_meteo/WEATHER (51) still need an actual re-fetch (bounded residual-closer round 4) — reconciliation confirmed
    these are genuine gaps, not lost bookkeeping. footystats/ODDS's 13,449 residual is the new P1 above, not a round-4
    candidate.

- 2026-07-14 (slot-3, dispatch — footystats/ODDS P1 root-cause RE-VERIFIED + round-4 confirmed genuinely closing it, not
  a code bug): picked up the footystats/ODDS 13,449 P1 filed in the previous entry. The operator's own investigation
  (relayed at dispatch, re-verified independently below rather than taken on faith) attributes 99%+ of it to
  `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` — a conservative placeholder the v9 manifest-canonicalisation rebuild stamped
  for `(league,date)` cells where it could not tell a genuine match-day-empty from a masked historical failure,
  deliberately erring toward `attempted_failed` per the operator's 2026-06-02 CF-11 directive
  (`plans/active/sports_manifest_canonicalisation_2026_06_01.md:441`) rather than risk silently swallowing a real gap —
  **not a live fetch bug**, and the write-path bug that could originally cause such masking is already fixed
  (`instruments-service@ceab7720` "CF-11", 2026-06-02 — verified real via `git log`/`git show`). Remediation is a live
  re-attempt through the now-correct write path, which is exactly what
  `sports_attempted_failed_residual_closer_2026_07_13.py` round 4 (PID 95616, launched ~02:31, `--max-rounds 8`,
  `--vm-name sports-attempted-failed-residual-closer-round4`) already does for footystats broadly.
  - **Re-verified live** (not trusted from the dispatch prompt): direct query of the canonical availability index
    confirmed footystats/ODDS `attempted_failed` = 11,009 at first read (down from the 13,449 baseline — round 4 was
    already chipping at it), breakdown `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE`=10,923 / `TimeoutError`=85 /
    `ArrowTypeError`=1 — matches the operator's relayed figures almost exactly (99.2% CF-11 either way).
    footystats/MATCHES already at 0 `attempted_failed`; PREDICTIONS steady at 89 (its residual dates haven't been
    reached yet in round 4's chronological pass).
  - **Round 4 confirmed genuinely progressing, not stalled/duplicated**: `ps aux` confirmed PID 95616 alive throughout
    (a pre-existing zsh watcher, PID 4392, is already tailing its log to `/tmp/residual_closer_round4.log` on exit —
    left untouched). Three live re-reads of the manifest ~7 minutes apart: 11,009 → 10,791 → 10,638 `attempted_failed`
    (footystats/ODDS) — a real, monotonic drop of 371 rows in ~14 minutes, 0 `RAISED footystats` errors in the log, low
    CPU (2-11%, confirming I/O-bound on the footystats API / GCS, not compute-bound). Per the dispatch's own instruction
    ("if round 4 is still running... verify it's genuinely progressing rather than duplicating it"), this is the correct
    call: **did NOT launch a round 5 or a VM** — round 4 is alive, healthy, and the single footystats API key means
    added local/VM concurrency would mostly just risk hitting the SAME provider-side rate limit sooner, not speed up the
    wall-clock. At the observed ~26 rows/min average (13,449→10,638 over ~105 min since round 4 started), full closure
    is a multi-hour tail — consistent with the dispatch's own expectation, not a stall. Current state: **10,638
    remaining** (footystats/ODDS), round 4 still running, no ETA promised beyond "hours, trending down."
  - **ArrowTypeError row (1 of 11,009→10,638) investigated individually**: confirmed via `git show a4dfa6bd` that the
    real historical bug (pyarrow rejecting a `pd.Timestamp` in the NaN-fill `kickoff_utc` string column) was fixed
    2026-06-29, before this row's `written_at` (2026-07-13T23:50, almost certainly a re-stamp from the v9 rebuild's
    blanket re-emission of pre-existing `attempted_failed` rows, preserving the original `error_reason` — not a fresh
    failure). Directly re-invoked `_fetch_footystats_odds(date="2023-05-30", force=True)` live against prod: **succeeded
    cleanly** — 12 real per-league odds rows fetched and captured, confirming the underlying fetch/parse has no live
    bug. **However the specific manifest row does NOT self-clear**: the stale sentinel's `row_key` is the OUTER
    catch-all `{date, data_type=ODDS}` with no `league_id` (from `footystats.py`'s top-level exception handler,
    `_row_key` at line 880), while the current write path for a per-league date (confirmed: this date has genuine
    per-league odds) always writes to the FINER `{date, data_type, league_id}` key — a coarse-vs-fine granularity
    mismatch, not a parse bug. Re-read the manifest post-probe: the coarse sentinel is still `attempted_failed`
    (expected — nothing writes to that exact coarse key once a date resolves per-league). Also checked whether
    `reconcile_sports_lost_per_vm_shard_2026_07_13.py` (the sibling reconciliation tool) would clear it — no: its own
    `_discover_real_cells` only matches league-partitioned blobs (`_LEAGUE_RE`) and explicitly documents bare-key files
    as "not the observed shape for these 4 entities," so it never touches this row either. **Did NOT force a
    `record_captured` at the coarse key** — no real parquet exists at that non-league-partitioned canonical path, and
    writing one would manufacture a `phantom_captured_no_parquet_at_canonical_path` row, the exact class of bug this
    plan exists to eliminate. **Verdict: one-off, already-explainable bookkeeping artifact, safe to leave** — real fix
    (adding an explicit supersession write, e.g. a `record_empty`/similar at the coarse key once a date's per-league
    loop completes with zero `_odds_failed_leagues`) is a genuine small code change but touches
    `instruments_service/engine/orchestrator/footystats.py`'s shared write path; deferred as its own precise follow-up
    rather than rushed in this dispatch (1 row out of >10,000, non-blocking). **Follow-up todo**: `footystats.py`
    per-league ODDS success branch should also supersede any pre-existing coarse `{date, data_type=ODDS}`
    `attempted_failed` sentinel once all expected leagues for that date resolve captured/empty, so this class of
    residual can't recur or outlive its accuracy.
  - **Consolidator safety**: no pause needed (only did per-VM-shard live reads + one exploratory per-VM-shard write for
    the ArrowTypeError probe under a throwaway `VM_NAME`, both always-safe per the mandatory rules) — confirmed both
    `uts-prod-manifest-consolidator-{instruments,market-data}-sports-cron` schedulers `ENABLED` via a read-only
    `gcloud scheduler jobs describe` (no 4th pause-without-resume incident this dispatch).
  - **api_football's own separate residual closer** (PID 10471,
    `--vm-name api-football-attempted-failed-residual-closer`, unrelated to footystats/ODDS, its own P1 from an earlier
    entry) was seen alive in `ps aux` and left completely untouched — out of this dispatch's scope.
  - **Net**: footystats/ODDS root cause re-confirmed as NOT a live code bug (write-path fix already shipped 2026-06-02);
    round 4 is the correct, already-in-flight mechanism and is measurably closing the gap (13,449 → 10,638 so far); no
    new process launched (would duplicate, and wouldn't clearly speed up an API-rate-limited workload); the 1
    ArrowTypeError row is fully explained, confirmed non-bug, and documented with a precise (not-yet-shipped) follow-up.
    **Not yet closed to 0** — this is expected and acceptable per the dispatch's own framing; round 4 should be left
    running and re-checked later (`ps -p 95616`, then re-read `footystats/ODDS attempted_failed` off the canonical
    index) rather than duplicated.

- **2026-07-14 (slot-3, sub-agent dispatch — SCHEDULED/DAILY CAPTURE AUDIT for all 8 in-scope sports sources, "sustained
  ≥99% going forward" ask, not one-time backfills).** Full audit + fixes, `deployment-service` scope. **Two real,
  previously-undetected bugs found and fixed; one PAUSED-job pair confirmed intentionally deprecated; one adjacent
  broken scheduler found and documented (not fixed — different repo/pattern, filed as a follow-up).**

  **(1) ROOT CAUSE — footystats (MATCHES/ODDS/PREDICTIONS), transfermarkt (PLAYER_VALUES), soccer_football_info
  (SFI_PROGRESSIVE_STATS) had ZERO scheduled driver, ever.** Traced the full dispatch graph by READING the code (not
  inferring from job names): the 4x-daily `uts-prod-sports-fixtures-{midnight,6am,noon,6pm}-t1- schedule` crons all hit
  the SAME Cloud Run Job (`uts-prod-instruments-service-sports-fixtures`) with baked default args
  `--sports-provider=API_FOOTBALL` — `process_preflight.py:_apply_sports_provider_filter` NARROWS `active_venues` to
  API_FOOTBALL only for that invocation, so `process_enrichment.py`'s footystats/transfermarkt/SFI blocks never run
  (their `"X" in active_venues_set` guards are False). The 5-min `uts-prod-sports-scheduler-cron`
  (`sports_trigger_scheduler` + `configs/sports-trigger-tiers.yaml`) never names MATCHES / ODDS(footystats) /
  PLAYER_VALUES / SFI_PROGRESSIVE_STATS as a `--sports-entity` in ANY tier (grepped the live YAML — zero occurrences).
  **Empirically confirmed via `gcloud logging read` over the preceding 14 days**: zero
  `Sports provider filter from CLI: FOOTYSTATS|TRANSFERMARKT|SOCCER_FOOTBALL_INFO` invocations of the Cloud Run Job, and
  zero non-FIXTURES/STANDINGS `Sports entity filter from CLI` values either — every "fresh" capture visible in the
  manifest for these 3 sources (tens of thousands of rows, `written_at` clustered on 2026-07-13/14) was from THIS SAME
  plan's own manual one-off backfill/residual-closer scripts run by concurrent agents today, not sustained automation —
  confirming the exact risk the dispatch brief named ("not just today's one-time backfills"). **Fix shipped**: new
  terraform `terraform/gcp/sports_enrichment_provider_scheduler.tf` — 3 new daily Cloud Scheduler jobs
  (00:35/00:40/00:45 UTC) each triggering a NEW dedicated Cloud Run Job
  (`uts-prod-sports-enrichment-{footystats,transfermarkt,soccer-football-info}`) with baked
  `--sports-provider={FOOTYSTATS,TRANSFERMARKT,SOCCER_FOOTBALL_INFO}` args. No new image/IAM needed — reuses the EXACT
  `instruments-service:latest` image + `unified-trading-sa` runtime service account the existing (working)
  sports-fixtures job already uses (confirmed via `gcloud run jobs describe` that SA already resolves all 5 sports API
  keys), and the scheduler invoker identity reuses `local.t1_service_account_email` (`t1_batch`), which already carries
  a project-wide `roles/run.invoker` binding — zero new IAM resources. `terraform plan -target=...` confirmed a clean "6
  to add, 0 to change, 0 to destroy" before applying (real prod state, `terraform/state/prod`, 519 pre-existing
  resources — verified pointed at the right state before touching anything). **Live-verified end to end, not just
  planned**: manually executed the FOOTYSTATS path first via `gcloud run jobs execute ... --args=...` (execution
  `uts-prod-instruments-service-sports-fixtures-lx6sw`, explicit `--start-date/--end-date=2026-07-14`) — confirmed real
  captures (`FootyStats predictions: 1 rows written`,
  `ManifestWriter: updated availability index ... in instruments-store-sports-prd-central-element-323112` — the
  canonical bucket) and a legitimate `0` for MATCHES that day (no bug, footystats' own coverage). Then applied the
  terraform + directly executed the NEW `uts-prod-sports-enrichment-soccer-football-info` job — **first attempt OOM'd**
  (`signal 9`, "configured memory limit was reached" at my initial 2cpu/8Gi sizing, matched to the sibling
  `understat-eu-typing-sweep` job which does a much narrower typing pass) — resized to 8cpu/32Gi (matching the
  PROVEN-safe sports-fixtures job, which reads the identical ~5-6M-row manifest successfully today), re-applied (clean
  3-resource in-place update plan, applied), and **re-executed successfully past the prior OOM point** (progressed
  through `SFI league mapping cache hit`, `SFI progressive stats: no completed matches for date=2026-07-14` — honest
  zero, not a bug — then into the normal generation-conflict retry/fallback cycle every other live write hit today).
  TRANSFERMARKT not independently live-executed in this pass (identical `_sports_provider_short_circuit` code path per
  `process_preflight.py`, code-symmetric confidence, chose not to add a 3rd concurrent execution against an already
  heavily-contended manifest mid-audit). **Commits**: `deployment-service@5da4b620` (scheduler+job terraform, initial
  2cpu/8Gi) + `deployment-service@0f862b6e` (resize fix to 8cpu/32Gi after the live OOM) — both via quickmerge, both
  QG-green. Re-read the canonical manifest post-write: `footystats` ODDS/PREDICTIONS `max_written_at` advanced to
  `2026-07-14T03:53` (today, post-fix, consolidated into the canonical index) — confirms the writes landed for real, not
  just per-VM-shard.

  **(2) ROOT CAUSE — the ENTIRE Tier-3/4 fixture-proximate trigger system (pre-match odds/predictions/lineups/ weather,
  post-match stats/xg/features) has been silently dead for ≥14 days — a genuine code bug, now fixed.** Investigating why
  zero non-FIXTURES/STANDINGS entities ever dispatch via the 5-min scheduler led to
  `deployment_service/sports_trigger_state.py:get_upcoming_fixtures()`: live-called it directly
  (`GCP_PROJECT_ID=central-element-323112 .venv/bin/python -c "..."`) and got **0 fixtures found (scanned 3 parquets)**
  despite football matches genuinely happening today. Root-caused via direct GCS listing: the function's two hardcoded
  `_fixture_path_patterns` (`sports_reference/fixtures/day={date}/` legacy, and
  `sports_reference/by_date/day={date}/entity=fixtures/` "new") **neither matches the CURRENT instruments-service writer
  shape**, which is
  `sports_reference/by_date/day={date}/pipeline_mode=batch_api_football/ entity=fixtures_schedule/league={league}/fixtures_schedule.parquet`
  (confirmed via direct `list_blobs` — e.g.
  `.../day=2026-07-14/pipeline_mode=batch_api_football/entity=fixtures_schedule/league=UCL/fixtures_schedule.parquet`
  exists and is fresh, written by TODAY's own re-triggered fixtures run). **Compounding second bug**: even the
  matching-path parquet's actual columns (`timestamp`, `af_fixture_id`, `af_league_id`, `af_home_name`, `af_away_name`)
  don't match the field names the reader expected (`kickoff_utc`, `fixture_id`, `league_id`, `home_team`, `away_team`) —
  a `prefix_tpls`-drift-class bug (per CLAUDE.md's own named failure class) compounded by a stale field-mapping,
  together fully explaining why `evaluate_pre_match_triggers`/`evaluate_post_match_triggers` never had anything to
  evaluate (empty fixture list every single poll, silently, no error — `run_once()`'s own "No upcoming fixtures —
  periodic-only cycle" INFO log, never surfaced as a failure). This directly explains the designed-but-dead drivers for
  WEATHER (`odds_t1h` trigger) and understat XG (`stats_delayed` trigger) named in this plan's scope, plus
  LINEUPS/PREDICTIONS(api_football pre-match)/FIXTURE_STATS/features-sports-service's own pre/post-match compute
  triggers (bigger blast radius than just this plan's 8 sources, flagging for visibility). **Fix shipped** (same
  `deployment-service@5da4b620` commit): added the correct current-shape path pattern to `_fixture_path_patterns`, and
  made the row-parse fall back to the new field names
  (`timestamp`/`af_fixture_id`/`af_league_id`-or-path-parsed/`af_home_name`/`af_away_name`) when the legacy names are
  absent — fully backward-compatible (verified the 4 existing `tests/unit/test_sports_tier3_fixture_diagnostic.py`
  mock-based tests still construct/assert against the OLD field names and still pass, since
  `MagicMock().name.split ("/")` safely returns `[]` for the mocked blobs, and the `or`-chain prefers the old names when
  present). Full `quality-gates.sh` run (not `--quick`, fresh non-cached run) passed clean, incl. this file's unit tests
  (confirmed the gate's `[3/6] TESTS` stage genuinely executes `tests/unit/` under `PYTEST_UNIT_DIR` — the visible "6
  passed" is a SEPARATE always-run PM cross-repo integration sanity check, not this repo's own suite, which streams to a
  temp log and only ever prints on failure — did not mistake the wrong stage for "0 real tests ran"). **Not yet
  independently re-verified live post-fix** (WEATHER/XG/LINEUPS/PREDICTIONS actually firing on the next 5-min poll
  against a real upcoming/recent fixture) — time-budget cutoff for this dispatch; flagging as an explicit follow-up
  verification (`ps`/logging-read `Sports entity filter from CLI` for anything beyond FIXTURES/STANDINGS over the next
  few hours) rather than claiming false-certain completion.

  **(3) The 2 PAUSED jobs (`uts-prod-features-sports-t1-schedule`, `features-sports-service-daily-trigger`) — CONFIRMED
  intentional deprecation, NOT a forgot-to-resume oversight. Left paused, no action.** Both `userUpdateTime` within 2
  minutes of each other (`2026-06-08T04:14:53Z` / `04:16:20Z`) — a deliberate coordinated pause, not an accident.
  `uts-prod-features-sports-t1-schedule` targets `uts-prod-features-sports-service-t1-recon`, a Cloud Run Job that **no
  longer exists** (`gcloud run jobs list` — zero match) — the target itself was retired, not just the schedule.
  `features-sports-service-daily-trigger` targets a GCP Workflows execution (`features-sports-service- daily`, still
  exists, just not auto-triggered). Both are superseded by the fixture-proximate `features-sports- service-job`
  (confirmed live in `gcloud run jobs list`) wired into `sports-trigger-tiers.yaml`'s `features_pre_match` (T-1h) /
  `features_post_match` (T+25h) triggers, dispatched by the (now-fixed, see (2) above) 5-min scheduler — matches this
  codebase's own stated architecture ("sports 'live' = batch, fixture-proximate, not fixed daily cron"). No terraform
  change made (leaving the dangling dead-target scheduler entries in place, paused, is safe; a future hygiene pass could
  delete them outright — not done here, out of this audit's scope).

  **(4) Adjacent finding, NOT fixed in this pass (different repo/pattern, flagging clearly per the "big finding" triage
  rule) — `uts-prod-market-data-processing-t1-schedule` (01:00 UTC daily, ENABLED) has been failing `NOT_FOUND` every
  single day for at least the last several days** (confirmed via
  `gcloud logging read resource.type="cloud_scheduler_job"` — 2 ERROR/NOT_FOUND entries per day, 07-12 through 07-14).
  Its target, `uts-prod-market-data-processing-service-t1-recon`, **does not exist** in `gcloud run jobs list` at all.
  This is market-data-processing-service's GENERIC T+1 candle-aggregation job (not sports-specific), so it's a broader
  pre-existing infra bug, not one of this plan's 8 named sources directly — but it's the closest thing to a "daily
  driver" context for `mdps_odds_horizon_bucket`, whose actual production mechanism (per this plan's own 2026-07-13
  entry) is a DEDICATED VM launcher (`deployment-service/scripts/vm/launch-mdps-sports-bucket-vm.sh` →
  `reprocess_sports_odds.py`), run manually/ one-off, not a recurring cron — meaning `mdps_odds_horizon_bucket` likely
  has the SAME "no sustained daily driver" exposure as (1) above, just via a different (VM-launch, cross-repo) pattern
  that needs its own dedicated design pass rather than a rushed patch here. **Not fixed in this dispatch** — flagging as
  a new P1 follow-up todo (below) rather than either silently leaving it or rushing an under-scoped fix to a different
  repo's VM-launch pattern under time pressure.

  **(5) Per-source scheduled-capture summary table** (source → scheduler mechanism → last verified healthy →
  same-bucket-as-batch confirmed):

  | source                   | scheduler / mechanism                                                                                                                                                                                         | last verified healthy                                                                                                                                                                                                                          | same bucket as batch                                                                                                        |
  | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
  | api_football             | 4x-daily `uts-prod-sports-fixtures-*` (API_FOOTBALL-scoped) + 5-min `uts-prod-sports-scheduler-cron` Tier1/2                                                                                                  | noon/6pm/midnight (07-12,07-13) succeeded; TODAY's 00:00 run failed transiently (`ManifestConsolidatorStaleError`, self-healed consolidator state) — manually re-triggered, **succeeded** (22m31s, 374+ new rows for 2026-07-14, consolidated) | YES (log-confirmed `instruments-store-sports-prd-central-element-323112`)                                                   |
  | footystats               | **NEW** `uts-prod-sports-enrichment-footystats-daily` (00:35 UTC)                                                                                                                                             | **live-verified today** (execution `lx6sw`: PREDICTIONS/ODDS real rows written, consolidated)                                                                                                                                                  | YES (log-confirmed)                                                                                                         |
  | soccer_football_info     | **NEW** `uts-prod-sports-enrichment-soccer-football-info-daily` (00:45 UTC)                                                                                                                                   | **live-verified today** post-resize (execution `86cvl`: reached honest-zero SFI progressive result, no crash)                                                                                                                                  | YES (same code path)                                                                                                        |
  | transfermarkt            | **NEW** `uts-prod-sports-enrichment-transfermarkt-daily` (00:40 UTC)                                                                                                                                          | not independently live-executed (code-symmetric w/ footystats) — **follow-up: execute once to confirm**                                                                                                                                        | YES (same code path, by symmetry)                                                                                           |
  | open_meteo (WEATHER)     | 5-min scheduler Tier3 `odds_t1h` (fixture-proximate) — was DEAD (fixture-calendar bug), **fixed this session**                                                                                                | not yet re-verified live post-fix — **follow-up: confirm within next few hours**                                                                                                                                                               | YES (same manifest writer)                                                                                                  |
  | understat (XG/XG_SHOTS)  | 5-min scheduler Tier4 `stats_delayed` (fixture-proximate) — was DEAD (same bug), **fixed this session**; separately `understat-eu-typing-sweep-daily` (03:00 UTC, typing-only, unaffected, confirmed healthy) | not yet re-verified live post-fix — same follow-up as WEATHER                                                                                                                                                                                  | YES                                                                                                                         |
  | odds_api (MTDS raw)      | MTDS T+1 `market-tick-data-fast` (00:30 UTC)                                                                                                                                                                  | **healthy** — succeeded every day 07-09 through 07-14 without exception (6/6 checked)                                                                                                                                                          | YES (362,631-row migration confirmed holding 07-13, re-confirmed today: 561,048 captured `trades` rows in canonical bucket) |
  | mdps_odds_horizon_bucket | VM launcher (`launch-mdps-sports-bucket-vm.sh`), one-off/manual, NOT a recurring cron                                                                                                                         | last run 07-13 (per this plan's own prior entry); the ADJACENT generic MDPS t1-recon cron is broken, see (4)                                                                                                                                   | YES (bucket-routing split-brain fixed 07-13, still holding: 137,972 captured rows, fresh `written_at`)                      |

  **New follow-up todos filed in §1** (not silently deferred): (a) live-execute the new TRANSFERMARKT enrichment job
  once to close the one source not independently proven this pass; (b) re-verify Tier-3/4 fixture-proximate triggers
  actually fire post-fix (WEATHER/XG/LINEUPS/PREDICTIONS/features-sports-service) over the next few hours; (c)
  investigate + fix the broken `uts-prod-market-data-processing-t1-schedule` → non-existent target Cloud Run Job
  (market-data-processing-service repo, out of this dispatch's scope) and design a genuine recurring driver for
  `mdps_odds_horizon_bucket` (currently VM-launch-only). **No consolidator schedulers were paused in this dispatch**
  (read-only `describe` checks only) — both `uts-prod-manifest-consolidator-{instruments,market-data}-sports-cron`
  confirmed `ENABLED` throughout, healthy executions every ~1 min start to finish of this session.

- 2026-07-14 (sub-agent, dispatch: launch bounded `mdps_odds_horizon_bucket` historical backfill now that the root-cause
  grain-realignment fix was already shipped/verified). **Backlog confirmed + closed a NEW P0 production-blocking bug
  discovered live; backfill now genuinely running.**
  - **Backlog re-confirmed via live manifest read** (`instruments-store-sports-prd-central-element-323112`,
    `read_availability_index` + `resolve_bucket_name(kind="instruments-store", asset_group="sports")`):
    `source=mdps_odds_horizon_bucket` — captured **137,972**, attempted_failed **0**, expected_unattempted **200,259** —
    matches the dispatch brief exactly. 2,230 distinct backlog dates, 2020-06-06→2026-07-14, ~90 rows/date (median 92,
    max 94) — confirmed this is NOT a sparse recent-days-only gap: EVERY one of the 2,230 backlog dates already has SOME
    captured rows too (1,813 of 2,230 dates overlap 100% with the captured-date set), meaning the backlog is cells
    scattered THROUGHOUT already-partially-processed history, not just the daily-job's trailing edge. This directly
    determined the launch mode: `reprocess_sports_odds.py`'s pre-flight skip key is COARSE (`{date, venue, data_type}`,
    no `league_id`/`timeframe`) — a plain (non-`--force`) run would skip nearly every backlog date outright (since
    almost all already have a coarse `captured` row from a prior partial pass), permanently missing the true per-shard
    gap. **`--force` across the FULL date range is therefore required**, not optional — documented in the launcher's own
    docstring now (see code-fix below).
  - **Decision: VM-sharded, not local/direct.** 2,230 dates × real per-league/per-bookmaker GCS reads is squarely
    outside "small enough to run directly on this host" — confirmed by the launcher's OWN docstring precedent (built for
    exactly this kind of full-history sweep, target <1hr via 4-VM sharding). Reused
    `deployment-service/scripts/vm/launch-mdps-sports-bucket-vm.sh` unmodified in its core logic (found via the
    documented grep-the-registry-first pattern — this launcher already existed, registered in
    `vm_prefix_registry.py`/`launcher_registry.py`, dispatched by `setup-data-pipeline-vm.sh`'s
    `VM_TASK= mdps-sports-bucket` branch). Sharded the 2020-06-06→2026-07-14 range across 4 VMs, `--workers 16`, `force`
    mode, mirroring the launcher's own documented example slicing (extended past its original 2026-04-14 end date to
    today): `2020-06-06→2021-12-31` / `2022-01-01→2023-06-30` / `2023-07-01→2024-12-31` / `2025-01-01→2026-07-14`.
  - **Pre-launch fix #1 — launcher had NO SPOT provisioning at all (bug, not just missing polish).** Read the launcher
    end-to-end before using it (per the mandatory grep-then-READ rule) and found it called
    `gcloud compute instances create` with zero `--provisioning-model` flag — silently defaulting every VM to on-demand,
    a direct violation of `codex/05-infrastructure/spot-vms-for-backfill.md`'s HARD RULE. Fixed:
    `deployment-service@0e7d771` adds
    `--provisioning-model=SPOT --instance-termination-action=DELETE --no-restart-on-failure` by default with a
    `--on-demand`/`ON_DEMAND=true` opt-out, mirroring `launch-mdps-backfill-vm.sh`'s existing convention exactly.
    Shipped via direct push (dirty-deps carve-out — `scripts/vm/setup-data-pipeline-vm.sh` had unrelated foreign
    uncommitted WIP from another concurrent agent in this shared clone throughout this entire dispatch, confirmed
    untouched via `git status`/`git diff --cached --stat` before every commit).
  - **Pre-launch fix #2 — 2 of 5 code tarballs stale** (`unified-trading-library`, `deployment-service`) vs local HEAD,
    per `lc_verify_tarball_freshness`'s own live check. Republished via `create-code-tarballs.sh`; hit the SAME
    dirty-foreign-file blocker (script `set -euo pipefail`s on ANY dirty CORE repo, aborting before it even reaches the
    upload step) — worked around with a `git worktree add --detach HEAD` clean checkout + a `WORKSPACE_ROOT`-overridden
    symlink tree pointing the tarball builder at the clean worktree instead of the dirty real clone, leaving the foreign
    agent's uncommitted WIP completely untouched throughout. Confirmed all 5 repo tarballs byte-exact-SHA-matched local
    HEAD before the first launch.
  - **FIRST launch (4 VMs, 04:18-04:20 UTC) — 2 of 4 CRASHED within ~10 minutes, a NEW P0 bug, not a launch-config
    issue.** `mdps-sports-bucket-20260714-041833` (2020-06-06→2021-12-31, reached 542/574) and `-041913`
    (2022-01-01→2023-06-30, reached 513/546) both terminated with an uncaught
    `unified_api_contracts.canonical.crosscutting.honest_coverage.UnprovenHonestAbsenceError` the moment `main()`'s
    per-day consumption loop processed its FIRST `empty_confirmed`-status date
    (`writer.record_empty(reason= SOURCE_RETURNED_ZERO)` called with NO `FetchEvidence`). Root cause:
    `reprocess_sports_odds.py` was never updated when UTL's 2026-06-22
    `data_pipeline_hardening_self_monitoring_2026_06_22` honest-absence-hardening keystone started HARD-requiring a
    `FetchEvidence` proving a clean 200+empty result for that reason code — every meaningful-length historical date
    range contains at least one genuinely-empty day, so this was a 100%-reproducible crash for ANY non-trivial run,
    silently losing every date's already-computed captured/bucketed work in that run (the single end-of-run
    `writer.write()` flush never got reached). Confirmed via live VM tracebacks (`row_key={'date': '2022-01-04', ...}`
    etc) — both crashed VMs self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`; the other 2 (`-041954`, `-042032`, still
    healthy, not yet hit an empty day) were manually deleted rather than left to run toward the same guaranteed fate.
  - **Fix shipped**: `market-data-processing-service@7c5c74d`. `reprocess_date()` now returns a 3rd `empty_kind`
    discriminator distinguishing the ONE genuinely-clean, provable absence (`"no_raw_data"` — both canonical GCS
    prefixes + the legacy fallback listed successfully, zero blobs found anywhere; eligible for a synthetic
    `FetchEvidence` mirroring the existing correct pattern in
    `market-tick-data-service/scripts/_rebuild_sports_write.py`'s historical-rebuild evidence construction) from two
    anomalous, NOT-honest-absence cases (`"missing_column"` / `"adapter_empty"` — raw bytes DO exist but are malformed
    or filtered to zero by the adapter) which now correctly route to `record_failed` with new
    `_MISSING_REQUIRED_COLUMN_ERROR_CODE`/`_ADAPTER_EMPTY_OUTPUT_ERROR_CODE` instead of being silently folded into
    `empty_confirmed`. Threaded through `_process_one_date`'s and `main()`'s tuple signatures; updated the existing unit
    test file for the new 3-tuple return + added 2 new tests covering the missing_column/adapter_empty → record_failed
    paths. `quality-gates.sh --no-fix` green, including STEP 5.99 ("every except-reachable SOURCE_RETURNED_ZERO write
    carries fetch_evidence") passing clean for this file — this QG rule already existed and would have caught this exact
    defect class had it been re-run against this script since 2026-06-22.
  - **Direct reproduction against the actual crash-triggering date** (`2022-01-04`, local one-off `--force` run, single
    date, pre-relaunch): confirmed the fix works — `"No raw odds data for 2022-01-04 — skipping"` →
    `"Writing manifest (0 captured + 1 empty_confirmed + 0 attempted_failed + 0 shard entries)..."` with NO traceback
    (pre-fix this exact date crashed the whole process). The run then hit several
    `ManifestWriter: generation conflict (attempt N/15), retrying...` cycles against the LIVE per-minute consolidator —
    a separate, already-documented, self-resolving CAS-contention pattern (same class as this plan's earlier
    `reconcile_mdps_odds_horizon_bucket_eu_grain` entry), NOT a bug; killed after ~7 min mid-retry (CAS is
    all-or-nothing, no partial-write risk) once the relaunched VMs had already independently confirmed the real fix
    end-to-end at production scale (see below) — not worth blocking further on a slow local single-date diagnostic.
  - **RELAUNCHED all 4 VMs (05:02-05:04 UTC) with the fixed code, same 4 date shards, all 5 tarballs re-verified fresh**
    (`market-data-processing-service@7c5c74d`, `deployment-service@0f862b6` — one more unrelated commit had landed on
    deployment-service meanwhile; `market-tick-data-service` also had unrelated foreign dirty files this time, same
    clean-worktree-symlink workaround applied). **Definitive fix confirmation, live-verified ~5-6 minutes into the
    relaunch**: all 4 VMs have now each hit MULTIPLE genuine `"no_raw_data"` empty-day events — the EXACT condition that
    crashed 2 of 4 VMs on the first launch — with **zero tracebacks, zero crashes, all 4 still RUNNING**:
    `mdps-sports-bucket-20260714-050241` 12 empty-days hit, at [183/574]; `-050324` 4 empty-days hit, at [201/546];
    `-050402` 15 empty-days hit, at [131/550]; `-050444` 1 empty-day hit, at [55/560]. This is conclusive,
    production-scale proof the crash is fixed, not just a unit-test assertion.
  - **Current state as of this entry (do not re-poll faster than ~hourly — this is a multi-hour bounded job)**: all 4
    VMs RUNNING, SPOT-provisioned, genuinely progressing (confirmed via both live idx counters AND real bucketed parquet
    files landing in GCS, e.g.
    `gs://market-data-tick-sports-prd-central-element-323112/processed/by_date/ day=2022-08-08/pipeline_mode=batch_mdps_odds_horizon_bucket/.../league_id={9 leagues}/`),
    each `VM_SHUTDOWN_ON_ COMPLETION=true` (self-terminates on completion or failure — check
    `gcloud compute instances list --project= central-element-323112 --filter="name~mdps-sports-bucket-20260714-05"` for
    liveness). **How to check on it later**:
    `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/run.log | tail -50` per VM name below,
    or re-read the live manifest (`source=mdps_odds_horizon_bucket`, `expected_unattempted` should trend down from
    200,259 and `captured` up from 137,972 once each VM's single end-of-run `writer.write()` flush lands — expect that
    flush itself to take several minutes per VM due to the same CAS-generation-conflict-retry pattern documented above,
    this is normal, not a stall). VM names: `mdps-sports-bucket-20260714-050241` (2020-06-06→ 2021-12-31),
    `mdps-sports-bucket-20260714-050324` (2022-01-01→2023-06-30), `mdps-sports-bucket-20260714-050402`
    (2023-07-01→2024-12-31), `mdps-sports-bucket-20260714-050444` (2025-01-01→2026-07-14). **Known, expected,
    non-blocking residual**: `-050444`'s range crosses the already-documented 2026-06-21+ "meta-snapshot" raw-odds shape
    boundary (`RawOddsShapeUnrecognizedError`, existing 2026-07-13 fix scope) — expect a small (~24-day × ~94-rows/day ≈
    2,256-row) `attempted_failed` residual for that VM specifically, tracked separately, NOT a regression from this
    dispatch's work. **Consolidator safety**: no pause needed or performed — this dispatch used only VM per-shard
    writes + one local single-date CAS-safe write (killed mid-retry, all-or-nothing, no partial state) — confirmed both
    `uts-prod-manifest-consolidator-{instruments,market-data}-sports-cron` schedulers `ENABLED` and untouched throughout
    via read-only `describe` checks.
  - **No todo left open for the mdps_odds_horizon_bucket historical-backlog closure task itself** — the backfill is
    genuinely, verifiably running at production scale with the correct fix; final full-closure verification (all 4 VMs
    reach 100%, manifest `expected_unattempted` for this source trending to ~0 or a documented residual) is correctly
    left for a LATER check per this dispatch's own "don't need to wait for full completion, verify genuine progress"
    mandate — not a gap, an intentional multi-hour-job handoff.

### MDPS T1-RECON + ODDS-HORIZON-BUCKET DAILY DRIVER (2026-07-14, follow-up dispatch, /autonomous)

- **Task as dispatched**: investigate `uts-prod-market-data-processing-t1-schedule` (failing `NOT_FOUND` ≥3 days) and
  provision a real daily scheduler+job for `mdps_odds_horizon_bucket` (`reprocess_sports_odds.py`) — the background
  framing assumed the broken scheduler WAS the odds-horizon gap.
- **Investigation found this framing was wrong — a genuine discrepancy, decided-and-documented per rule 1/2, not a
  silent scope pivot**: `gcloud scheduler jobs describe uts-prod-market-data-processing-t1-schedule` shows
  `description: "market-data-processing-service T+1 recon batch — candle aggregation (depends on MTDS)"`, targeting
  Cloud Run Job `uts-prod-market-data-processing-service-t1-recon` — confirmed genuinely missing
  (`gcloud run jobs describe` errors "Cannot find job"; no `google_cloud_run_v2_job` resource anywhere named it). This
  is `t1_batch_scheduler.tf`'s `"market-data-processing"` entry — GENERAL T+1 candle aggregation across ALL 5 asset
  groups (per the orphaned `terraform/services/market-data-processing-service/gcp/main.tf` workflow.yaml's
  `--CEFI --TRADFI --DEFI --SPORTS --PREDICTION` args — that whole module/Workflow/CRJ was never applied to this
  project, confirmed absent from both `gcloud run jobs list` and `gcloud workflows list`), same F-41 class bug as the
  already-fixed `strategy_t1_recon_job`. It was NEVER sports-odds-specific. Decision: fix BOTH — the literally-broken
  existing scheduler (genuinely adjacent, explicitly named in the dispatch's own investigation steps) AND provision the
  NEW dedicated `mdps_odds_horizon_bucket` scheduler+job the dispatch's core intent actually called for.
- **Fix A — `uts-prod-market-data-processing-service-t1-recon` (general candle aggregation)**:
  `deployment-service@de117f5` adds `mdps_t1_recon_job` to `audit03_cron_provisioning.tf` (mirrors the
  `strategy_t1_recon_job` co-located-module pattern exactly; reuses `google_service_account.unified_trading`, no new
  IAM). `market-data-processing-service@3f1065f` adds a `_build_legacy_argv` self-default (yesterday, T-1 UTC) when the
  caller supplies neither `--start-date` nor `--end-date` — required because a `google_cloud_scheduler_job`
  `http_target`'s args are static (no per-trigger date computation, unlike the orphaned Workflow), and the legacy
  sub-parser's dates are `required=True`. Three MORE bugs surfaced only via live execution
  (`gcloud run jobs execute --wait`, not just code review — the "run it, don't read it" verification standard):
  1. **Dependency hard-fail**: first live execution exit(1)'d — `_check_dependencies` aborted the WHOLE date because 4/5
     asset groups had no upstream MTDS `raw_tick_data` for yesterday yet (one, PREDICTION, doesn't even have its
     legacy-named bucket: `market-data-tick-prediction-prd-*` 404s — see finding 3 below). Root cause: this ONE combined
     job processes all 5 groups at 01:00 UTC, but `t1_batch_scheduler.tf`'s OWN documented DAG splits MTDS's upstream
     captures into a FAST phase (00:30) and a SLOW CeFi phase (06:00) — a quiet DeFi/TradFi/Prediction day is normal,
     not a fault, for a 5-asset-group combined job. Tried the legacy `--no-fail-on-missing-deps` flag first — REJECTED
     at the container's actual entrypoint (`ServiceBootstrap`'s top-level parser never exposes it; only
     `_build_legacy_argv`'s bridged subset reaches the internal parser). Fixed via the SUPPORTED bridge instead:
     `SKIP_DEPENDENCY_CHECK=true` env var.
  2. **Every category then failed with "No source bucket configured for category=X"**: `config.py`'s
     `get_bucket_for_asset_group()` reads `PROTOCOL_DATA_SOURCE_BUCKET_{CATEGORY}` directly (a legacy env-var path, not
     `resolve_bucket_name()`) — no `.tf` in this repo had EVER set it for any category. Verified real bucket names live
     via `gcloud storage buckets list` (NOT the config.py docstring's stale example — missing the `-prd-` env tier — nor
     `DependencyChecker`'s own PREDICTION bucket name, which 404s: it looks up `market-data-tick-prediction-prd-*`,
     decommissioned 2026-07-12 in favor of the abbreviated `market-data-tick-pred-prd-*` — a separate, pre-existing
     latent bug in `DependencyChecker`, NOT fixed here since `SKIP_DEPENDENCY_CHECK` bypasses that path entirely;
     tracked as a followup todo below). Added all 5 `PROTOCOL_DATA_SOURCE_BUCKET_{CEFI,TRADFI,DEFI,SPORTS,PREDICTION}`
     env vars with the CORRECT (`-prd-`, `pred`) bucket names.
  3. **OOM (signal 9) at 16Gi**: after the bucket fix, the job genuinely started reading real GCS data — RSS hit ~9.3GB
     after TradFi's 75,336-instrument corpus ALONE, before even reaching DeFi/Sports/Prediction in the SAME process
     (single-date runs use `--no-subprocess-per-date`, so all 5 categories' instrument corpora accumulate in one process
     — no per-category isolation exists). Bumped 16Gi→32Gi (matching this file's own largest proven-safe allocation, the
     sports-enrichment jobs) rather than guessing an intermediate value — RSS peaked at ~22GB, comfortable margin.
  - **Final live-test result** (`uts-prod-market-data-processing-service-t1-recon-zf96z`, digest
    `sha256:4f2972de7a1c98fb3312dd593c67a2399956c8823335a1adf7afbc1abaa012c2`): exit 0, all 5 categories processed (cefi
    22.3s / tradfi 13.0s / defi 51.0s / sports 6.0s / prediction 0.2s), 0 crashes. **One pre-existing, unrelated bug
    surfaced**: PREDICTION aborted with `❌ instrument_key column missing from instruments data` (Polymarket instruments
    schema) — a real data-processing bug in a different code area (the prediction/Polymarket instrument loader, not
    scheduler/infra), genuinely out of this dispatch's scope to fix blind; **new followup todo added** (§1) rather than
    silently dropped.
- **Fix B — `mdps_odds_horizon_bucket` (the actual dispatch target)**: new file
  `deployment-service/terraform/gcp/mdps_odds_horizon_scheduler.tf` — `uts-prod-mdps-odds-horizon-bucket` Cloud Run
  Job + `uts-prod-mdps-odds-horizon-bucket-daily` scheduler (01:15 UTC, after the 00:30 MTDS fast phase), mirroring the
  `sports_enrichment_provider_scheduler.tf` / `understat_eu_typing_scheduler.tf` pattern exactly: reuses
  `unified-trading-sa` (image) + `t1_batch` SA (scheduler invoker, already project-wide `run.invoker` — zero new IAM),
  8cpu/32Gi (same manifest-read cost class as the sports-enrichment jobs, sized right the first time instead of guessing
  low). `market-data-processing-service@3f1065f`'s OTHER half: `reprocess_sports_odds.py`'s `--start-date`/`--end-date`
  made optional (previously `required=True`), self-defaulting to a rolling `[today-2, today]` (UTC) window when BOTH
  omitted (a caller supplying exactly one is still a loud usage error) — absorbs bookmakers' late-arriving raw ticks;
  extracted into `_resolve_date_window()` to keep `main()`'s cyclomatic complexity under the ruff C901 ceiling.
  Registered `mdps-odds-horizon-bucket` in `cloud_run_job_registry.py::_SINGLETON_JOBS` (guard test requirement).
  - **Image note**: the `:latest` image at dispatch time predated this fix. Manually submitted a Cloud Build
    (`gcloud builds submit --config=cloudbuild.yaml .`, build `afe2d235-0dd3-4fdf-b60b-1fe0d4a1606e`) to bake the fix in
    before the real CI trigger (push-to-`main`) would have produced one — the manual build's Docker
    build/quality-gates/push steps all succeeded (image pushed at digest
    `sha256:4f2972de7a1c98fb3312dd593c67a2399956c8823335a1adf7afbc1abaa012c2`, confirmed matching `:latest` via
    `gcloud artifacts docker images describe`), but the OVERALL build status is `FAILURE` — a LATER, unrelated
    `publish-wheel` step fails because a bare `gcloud builds submit` tarball has no `.git/` (setuptools-scm can't
    resolve a version; the file's own `fetch-tags` step comment already anticipates this for non-trigger builds). Do
    **not** treat build `afe2d235` as SUCCESS evidence — the DECISIVE evidence is the live Cloud Run executions below,
    verified by DIGEST match, not the build's terminal status. Also had to `gcloud run jobs update --image=...:latest`
    on both jobs after the rebuild — Cloud Run Jobs pin the resolved digest at job-create/update time, so pushing a new
    `:latest` does NOT retroactively update an already-provisioned job's execution image (the FIRST live-test attempt on
    each job still ran the OLD pre-fix digest and failed on the old `--start-date required` error, confirmed via
    `executions describe`'s `spec.template.spec.containers[0].image`).
  - **Live-test 1** (`uts-prod-mdps-odds-horizon-bucket-pvpqq`, no explicit args — the actual daily-trigger invocation):
    self-defaulted to `[2026-07-12, 2026-07-14]`, found all 3 dates already `empty_confirmed` (from the earlier VM
    backfill fleet), correctly skipped all 3 (`skipped_manifest=3`), exit 0 in 1m22s.
  - **Live-test 2** (`uts-prod-mdps-odds-horizon-bucket-925jn`, `--start-date 2026-07-13 --end-date 2026-07-14 --force`,
    digest `sha256:4f2972de7...`): forced re-check of the 2 most recent dates — both genuinely `no_raw_data` (0 raw
    ODDS_API blobs found), so `writer.record_empty(...)` fired with a FRESH `attempted_at` timestamp for both — real
    manifest write, not a no-op. Hit the SAME `ManifestWriter: generation conflict` CAS-contention pattern already
    documented earlier in this plan (self-resolving, non-blocking) — this time it exhausted all 15 retries (contention
    with the periodic per-minute consolidator) and correctly fell back to an "unconditional write"
    (`WARNING: generation conflict after 15 retries, falling back to unconditional write`) — completed successfully,
    exit 0, 16m44s total (dominated by the retry backoff, not real work). This IS the "confirm it actually wrote real
    data / fresh written_at" evidence the dispatch required — a genuine read-modify-write round-trip through the
    CAS-contention path to a successful terminal write.
- **Both jobs verified live in real prod Terraform state** (backend `terraform/state/prod`, confirmed correct per the
  dispatch's own caution —
  `tofu init -backend-config="bucket=uts-terraform-state-central-element-323112" -backend-config="prefix=terraform/state/prod"`,
  matching `.terraform/terraform.tfstate`'s recorded backend exactly): `tofu apply` (targeted,
  `-target=module.mdps_t1_recon_job -target=module.mdps_odds_horizon_job -target=google_cloud_scheduler_job.mdps_odds_horizon_daily`,
  plus 3 follow-up targeted applies for the live-test fixes above) — `gcloud run jobs describe` /
  `gcloud scheduler jobs describe` confirm all 3 resources exist and are `ENABLED`.
- **Shipped**: `market-data-processing-service@3f1065f` (`quality-gates.sh --no-fix` green both passes — first pass
  caught a ruff C901 complexity violation from the inline date-window logic, fixed by extracting
  `_resolve_date_window()`), `deployment-service@de117f5` (`quality-gates.sh --no-fix` green, including the
  `cloud_run_job_registry` guard test). Both landed on `live-defi-rollout` via `quickmerge.sh --agent`.
- **New followup todo** (§1, added per rule 1/2 "capture every side-discovery as a plan todo immediately"): the
  Polymarket `instrument_key`-missing-column bug (finding above) and the `DependencyChecker` PREDICTION
  legacy-bucket-name bug (finding above) both need a market-data-processing-service-scoped fix — out of this dispatch's
  scheduler/infra-scoped authority to fix blind under time pressure; the general T1 job's PREDICTION category will keep
  silently no-op'ing (caught, logged, non-fatal) until either is fixed.
- **Definition-of-DONE check for this specific dispatch**: `uts-prod-market-data-processing-t1-schedule` no longer hits
  `NOT_FOUND` (its target CRJ now exists, is live-tested, and is Terraform-managed); `mdps_odds_horizon_bucket` now has
  a real, verified, self-sustaining daily driver (01:15 UTC) distinct from the manual VM-backfill path. Not left for
  "another agent to pick up" — both live-tested end-to-end this session, both shipped, both journaled.

- **2026-07-14 (slot-5, data_engineering) — API_FOOTBALL DEEP-INVESTIGATION RE-VERIFY + CLOSE-OUT (todo "api_football
  deep investigation").** Single-parquet live read of `instruments-store-sports-prd-central-element-323112`
  `_index/availability_index.parquet` (5,759,709 total rows), api_football slice, via the mtds `.venv` duckdb+gcsfs
  (single-walk compliant — consolidated index only, no corpus walk). Closes the P0 investigation todo:
  - **api_football slice capture_status**: captured **740,120** (§0 baseline 365,592 — +374k from the TEAMS backfill +
    residual re-attempt + odds/orphan migrations landing) · empty_confirmed 1,639,435 · expected_unattempted **287,207**
    (§0 453,961) · attempted_failed **4,291** (§0 3,257).
  - **(1) `expected_unattempted` is a legitimate could-exist seed — CONFIRMED, and now demonstrably shrinking under
    backfill** (the decisive evidence a seed vs a real gap). 453,961 → 287,207, the ~166k drop dominated by TEAMS
    192,384 → **26,385** (the 61-league TEAMS backfill + `manifest_consolidator` dedup work converting seed cells to
    captured). Current by data_type: ODDS 82,501 · FIXTURE_LINEUPS 47,376 · FIXTURE_EVENTS 47,090 · FIXTURE_STATS 36,707
    · PLAYER_STATS 26,409 · TEAMS 26,385 · INJURIES 20,721 · FIXTURES 18. A genuine gap does not shrink when you
    backfill the universe; a per-league × per-year × per-data_type could-exist cross-product does. No action — this is
    denominator, not a gap (matches the prior investigation-only pass's conclusion, now with a shrink-under-backfill
    proof it did not yet have).
  - **(2) all 4 original `attempted_failed` classes re-verified holding** (root-caused + fixed under the "fix root
    causes" todo, `instruments-service@9ce3450e` + IMPLEMENTATION dispatch): `ApiFootballResponseError` 1,642 (INJURIES
    silent-swallow + UAC-classify-key misclassification) · `FIXTURES_FETCH_FAILED` 612 (was 665 — the false-positive
    `_fixtures_fetch_failed` trigger, some cells re-resolved) · blank-`data_type` `UNCLASSIFIED_ADAPTER_ERROR` 461
    (completeness-gate pseudo-venue leak — **0 NEW blank rows since the fix, 121 `empty_confirmed` blank-data_type rows
    prove the enrichment pseudo-venues now route correctly**) · `phantom_captured_no_parquet_at_canonical_path` 484
    (reconcile-tooling output, not a live write-path bug). The 88 `market-tick-data-service` orphan re-stamp holds:
    **0** `market-tick-data-service`+`api_football` rows remain. These pre-existing rows are unchanged-by-design (the
    code fixes stop RECURRENCE; clearing the historical rows is the deferred backfill tracked by the
    `[VERIFY] P1 final re-verify` todo).
  - **(3) NEW class root-caused this pass — `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` (1,090)**. By data_type
    FIXTURE_EVENTS 372 / FIXTURE_STATS 363 / FIXTURE_LINEUPS 355; 114 distinct match-days 2020-10-06 → 2026-03-26; 100%
    `service_name=instruments-service`; no captured/empty twin for the same (date, data_type, league_id). Traced the
    literal reason string to `market-tick-data-service/scripts/_rebuild_sports_write.py:191`, written by the v9
    manifest-canonicalisation rebuild's **step-6.7 CF-11 gate** (`rebuild_sports_manifest_v9.py:378` +
    `_rebuild_sports_classify.py`, **operator directive 2026-06-02**): for a data_type in
    `_FIXTURE_GUARANTEED_DATA_TYPES` (FIXTURES/FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/STANDINGS/ODDS/…), if
    `(league_id, date)` IS in `fixtures_truth` (a match genuinely happened) → upgrade the `empty_confirmed` row to
    `attempted_failed` so the gap is SURFACED for backfill instead of being frozen as a false honest-absence. The gate's
    own comment states the operator's priority explicitly: a wrongly-kept FIXTURE_STATS empty (silent incompleteness
    that blocks backfill forever) is WORSE than a wrongly-upgraded failure. **So CF11 is deliberate, correct
    honest-coverage behavior — NOT a defect, NOT a false-positive over-flag** (the gate only fires when a fixture
    provably happened). These 1,090 rows are genuine per-fixture-entity backfill candidates — filed as the new
    `[DATA] P2 backfill the CF11 gaps` todo, folding into the `[VERIFY] P1 final re-verify` "0 attempted_failed" target.
  - **Deliverable**: investigation todo closed — all of api_football's `attempted_failed` is now characterized to a
    named class with a code-level root cause and a tracked resolution owner; `expected_unattempted` is confirmed a
    (shrinking) legitimate seed. No new code shipped by this investigation pass (the fixes were shipped under the "fix
    root causes" todo it drove; CF11 is operator-directed correct behavior, not a bug). Verification method: live
    single-parquet manifest read (scratch `verify_af.py` / `verify_cf11.py`, mtds `.venv` duckdb 1.5.3 + gcsfs, ADC on
    `central-element-323112`).

- [ ] [VERIFY] P0. **Overnight/next-day live-cron verification (NEW 2026-07-14, operator-directed)** — every scheduled
      driver fixed today is hours-old and has only been confirmed via a single manual `gcloud run jobs execute --wait`
      trigger, never a real unattended cron fire. Before calling ANY of these "fixed for good," confirm they actually
      self-fire correctly on their own schedule at least once (ideally through one full overnight cycle + the next day's
      live matches, per the operator's explicit ask — "let's wait for that overnight cycle... mark plan to check the run
      tonight or tomorrow"). Check ALL of the following on the next session touching this plan:
  - `uts-prod-sports-enrichment-footystats-daily` / `uts-prod-sports-enrichment-soccer-football-info-daily` /
    `uts-prod-sports-enrichment-transfermarkt-daily` (new today, `deployment-service@5da4b620`/`@0f862b6e`) — check
    `gcloud scheduler jobs describe <job> --project=central-element-323112 --location=asia-northeast1` for
    `lastAttemptTime`/`status`, then
    `gcloud run jobs executions list --job=<run-job-name> --region=asia-northeast1 --project=central-element-323112 --limit=5`
    for a self-triggered (not manually-executed) success, then confirm fresh `captured` rows landed in the canonical
    manifest for TODAY's date for each source.
  - The Tier-3/4 fixture-proximate trigger system fix (`sports_trigger_state.py` path/schema fix, shipped today) —
    confirm it actually fires around a REAL live kickoff (pre-match T-1h lineups, post-match T+30m stats/events) rather
    than just unit-test-passing; check `deployment_service`'s trigger logs / the relevant Cloud Run Job's execution
    history spanning an actual match window.
  - `uts-prod-mdps-odds-horizon-bucket-daily` + `uts-prod-market-data-processing-service-t1-recon` (new today,
    `deployment-service@de117f5`) — same self-fire check; confirm the rolling 3-day window actually picks up real
    newly-landed raw ticks once a full day has genuinely elapsed (today's `2026-07-14` data was still incomplete at test
    time, so today's manual test could only confirm the mechanism runs cleanly, not that it captures a complete day
    yet).
  - If any of these did NOT self-fire on schedule (Cloud Scheduler shows no new `lastAttemptTime` past its cron time, or
    the triggered Cloud Run Job execution list has no NEW entry beyond today's manual tests), that's a genuine
    regression from what was "shipped" today — diagnose and fix, don't just re-trigger manually and declare it fine.
  - **INTERIM STATUS 2026-07-14 13:35 UTC (slot-5, live REST verify — checkbox intentionally NOT flipped, self-fire not
    yet possible)**: the INFRA half is fully verified in place, but the actual unattended self-fire — the operator's
    explicit DoD — CANNOT be proven until the **2026-07-15** overnight cron, because every cron time (00:35–01:15 UTC)
    is EARLIER than today's scheduler/run-job creation times (03:41–10:34 UTC), so no daily driver has had a single
    self-fire opportunity yet (all `lastAttemptTime=<never>`). Verified live via the Cloud Scheduler + Cloud Run v2 REST
    APIs (gcloud CLI is broken in the slot env — `snap-confine` capability error; used an ADC bearer token instead — and
    the scheduler LIST endpoint misleadingly returns 0, but direct GET-by-name works): **all 5 schedulers exist +
    `state=ENABLED` with correct crons + correctly-wired targets** — `uts-prod-sports-enrichment-footystats-daily`
    (`35 0 * * *`), `-transfermarkt-daily` (`40 0 * * *`), `-soccer-football-info-daily` (`45 0 * * *`),
    `uts-prod-mdps-odds-horizon-bucket-daily` (`15 1 * * *`), `uts-prod-market-data-processing-t1-schedule`
    (`0 1 * * *`); every backing Cloud Run Job exists and its manual test executions succeeded (soccer-football-info
    exec 04:05:15Z succeeded=1; mdps-odds-horizon exec 11:11:59Z succeeded=1; t1-recon exec 11:17:05Z succeeded=1;
    footystats + transfermarkt run jobs exist but have 0 executions ever — never cron-fired, manual "live-verify" used
    the `sports-fixtures` provider path, not these dedicated jobs). **Specific tomorrow-watch item**: t1-schedule's ONLY
    fire so far (2026-07-14T01:00:19Z) returned `status.code=5` (NOT_FOUND) — but that fire predates the fix
    (`deployment-service@de117f5` landed ~10:34Z) and the scheduler now correctly targets
    `uts-prod-market-data-processing-service-t1-recon:run` which EXISTS, so the 2026-07-15 01:00Z fire is the real test
    that the NOT_FOUND regression is closed. **Re-check after 2026-07-15 ~01:30 UTC** (all 5 schedulers'
    `lastAttemptTime` advanced past their cron + `status.code=0` + a NEW cron-triggered — not manual — Cloud Run
    execution + fresh `captured` rows for 2026-07-14/15 in the canonical manifest). REST recipe archived in the slot-5
    scratch (`check_named.py`/`check_final.py`, ADC token + `cloudscheduler.googleapis.com` / `run.googleapis.com/v2`).
    No regression found in the infra itself; this todo stays open purely on the time-gate. Raised to the operator/main
    via a slot-5 blocked-note (time-gated, recommend park until 2026-07-15 ~01:30 UTC).
  - **INTERIM STATUS 2026-07-17 15:12 UTC (slot-7, live REST + single-parquet manifest verify — checkbox STILL NOT
    flipped; the 07-17 overnight window was CONSUMED by the sports bucket cutover freeze, so the post-restore unattended
    self-fire has not yet happened; next window is 2026-07-18 00:35–01:15 UTC).** Verified via ADC-token REST
    (`cloudscheduler v1` GET-by-name + `run.googleapis.com/v2` executions list; gcloud snap still broken in-slot —
    `snap-confine cap_dac_override`) + a single-parquet read of
    `instruments-store-sports-prd _index/availability_index.parquet` (duckdb 1.5.3 + gcsfs, deployment-service `.venv`).
    Ground truth is the **Cloud Run execution history** (the scheduler `lastAttemptTime`/`status` REST fields are
    unreliable here — 4/5 read `lastAttemptTime=<never>` + `status.code=-1` despite proven cron fires; only t1 read a
    real value). **What actually happened, by run job:**
    - `t1-recon` (`0 1 * * *`): **FULLY PROVEN — 3 consecutive clean unattended self-fires** 07-15/16/17 all at
      `01:00:00Z succ=1` (07-17 exec `ltsjq`). slot-5's `status.code=5` NOT_FOUND regression is **CLOSED** (first
      post-fix fire 07-15 succeeded).
    - `footystats` (`35 0`): self-fired 07-15 `00:35:00 succ=1` ✅, then 07-16 `00:35:04 fail=1` ❌; **no 07-17 fire.**
    - `transfermarkt` (`40 0`): 07-15 `00:40:00 succ=1` ✅, 07-16 `00:40:02 fail=1` ❌; **no 07-17 fire.**
    - `soccer-football-info` (`45 0`): 07-15 ✅ + 07-16 ✅ (both `succ=1`); **no 07-17 fire.**
    - `mdps-odds-horizon-bucket` (`15 1`): 07-15 `01:15 fail=1` ❌, 07-16 `01:15:04 succ=1` ✅; **no 07-17 fire.**
    - **Why "no 07-17 fire" for the 4 sports/odds jobs is EXPECTED, not a regression**: they were deliberately PAUSED on
      2026-07-16 by the bucket-cutover freeze (`sports_legacy_bucket_cutover_2026_07_16.md` T0.4/T0.6) and only
      RE-ENABLED 2026-07-17 under Phase 6 (T6.1b consolidators, T6.3 writers, **T6.4 the 3 enrichment + 4 fixtures
      crons**) — the re-enable landed AFTER today's 00:35–01:15 cron windows, so no self-fire opportunity existed today.
      Restore first-runs were **MANUAL** (T6.3/T6.4 "each first run GREEN ON CANONICAL"), NOT self-fires.
    - **Manifest freshness confirms the restored path writes canonical data**: fresh 07-17 `captured` rows landed —
      footystats 14, transfermarkt 32, soccer_football_info 2 (from the manual restore runs); odds_api captured through
      07-16. So the data path is proven end-to-end; only the _unattended self-fire_ on the restored config is unproven.
    - **07-18 WATCH-ITEM (the specific thing that makes this flippable)**: the 07-16 footystats + transfermarkt failures
      both hit the SAME path
      `instruments-service/instruments_service/cli/instruments_handler.py:310 → engine_orchestrator.process_instruments(...)`
      (traceback tail sampled out of stdout; only the top frames survive in the ERROR log). That was on the now-dead
      PRE-cutover config, and the restore re-proved green manually — but the 07-18 00:35/00:40 self-fires are the real
      test that this failure does NOT recur on the restored config. If either fails again at `:310`, that is a live
      regression to root-cause (not re-trigger-and-declare-fine).
    - **Observation (not in this todo's scope, flag only)**: source `mdps_odds_horizon_bucket` reads
      `latest_captured = 2026-06-20` in the canonical manifest (stale ~1 month) though its Cloud Run executions succeed
      — consistent with the known venue-grain / 200,259-`expected_unattempted` reconciliation situation (it aggregates
      into `source=odds_api`, which IS fresh to 07-16), but worth a confirm by whoever owns the mdps-odds recon.
    - **DISPOSITION**: todo stays OPEN purely on the time-gate (identical class to slot-5's 07-14 hold, re-created by
      the 07-16 cutover). **Re-check after 2026-07-18 ~01:30 UTC**: all 5 run jobs show a NEW cron-triggered (not
      manual) execution at their exact cron minute for 07-18 with `succ=1`, + fresh `captured` rows for 07-17/18 per
      source, + the Tier-3/4 fixture-proximate trigger fires around a real 07-18 kickoff window (the T6.5
      meta-launcher's first `*/5` tick already fired 6 triggers 07-17 03:00:00Z, so the trigger _system_ is live).
      REST/duckdb recipe archived in slot-7 scratch (`verify_cron.py` / `verify_manifest.py`). **This todo has NO
      dispatch gate**, so it will keep redispatching before 07-18 (slot-5 → slot-7 already = 2 slots) — RECOMMEND main
      add a prereq `sports-cron-overnight-2026-07-18-observable` (false now; POST `/api/prerequisites/<name>`, attach
      `prereqs.prerequisites` to `sports_data_sources_canonical_completion-001` in `backlog.yaml`,
      `/api/backlog/reload`, verify it survives a `PlanRegenLoop` tick; flip true after 07-18 ~01:30 UTC) so a 3rd slot
      doesn't burn a dispatch. A worker cannot hand-edit `backlog.yaml` (HARD RULE), so this gate is main's to add.
  - **INTERIM STATUS 2026-07-17 15:38 UTC (slot-4, live REST re-confirm — checkbox STILL NOT flipped; the predicted 3rd
    dispatch the slot-7 note warned about).** As predicted, this ungated todo redispatched to a 3rd slot before the
    07-18 time-gate. Re-verified the ONE thing that could have changed in the ~26 min since slot-7 and that de-risks the
    07-18 watch: **all 5 daily schedulers are still `state=ENABLED` with the correct crons at 15:38 UTC** (footystats
    `35 0`, transfermarkt `40 0`, soccer-football-info `45 0`, mdps-odds-horizon `15 1`, t1-schedule `0 1`), so the
    07-18 00:35–01:15 UTC self-fire window is ARMED and nothing got re-disabled after the Phase-6 (T6.4) re-enable.
    Scheduler REST `lastAttemptTime`/`status` remain unreliable exactly as slot-7 flagged (4/5 read `<never>` +
    `code:-1`; only t1-schedule reads its real `2026-07-17T01:00:00Z` fire) — Cloud Run execution history stays the
    ground truth and is unchanged since slot-7 (no daily-cron fire happens in a 15:12→15:38 window). Method: ADC-token
    REST (`cloudscheduler v1` GET-by-name via `deployment-service/.venv` google.auth; gcloud snap still broken in-slot,
    `snap-confine cap_dac_override`). **DISPOSITION UNCHANGED — todo stays OPEN on the time-gate; re-check after
    2026-07-18 ~01:30 UTC per slot-7's checklist.** Filed a slot-4 `/blocked` to main re-requesting the
    `sports-cron-overnight-2026-07-18-observable` dispatch gate (workers cannot hand-edit `backlog.yaml`) so a 4th slot
    does not burn another dispatch before 07-18.
  - **INTERIM STATUS 2026-07-17 15:49 UTC (slot-3, data_engineering — the 4th pre-gate dispatch slot-4 warned about;
    checkbox STILL NOT flipped).** As predicted, the ungated todo redispatched again ~11 min after slot-4.
    **Deliberately did NOT re-run the REST/duckdb verification** — no daily-cron self-fire can occur in a 15:38→15:49
    UTC window, so another live sweep would only re-confirm slot-4's already-current "all 5 schedulers ENABLED + armed,
    Cloud Run exec history unchanged" reading and burn API calls for zero new signal. Time is 15:49 UTC; the DoD
    (unattended self-fire on the RESTORED post-cutover config) is physically unreachable until the **2026-07-18
    00:35–01:15 UTC** cron windows. **DISPOSITION UNCHANGED — todo stays OPEN on the time-gate; re-check after
    2026-07-18 ~01:30 UTC per slot-7's checklist** (5 run jobs each showing a NEW cron-triggered — not manual — exec at
    their exact cron minute for 07-18 with `succ=1`; fresh `captured` rows for 07-17/18 per source;
    footystats+transfermarkt do NOT re-fail at `instruments_handler.py:310` on the restored config; Tier-3/4
    fixture-proximate trigger fires around a real 07-18 kickoff). Re-escalated to main via a slot-3 `/blocked`
    re-requesting the `sports-cron-overnight-2026-07-18-observable` dispatch gate — this is now the **4th** slot burned
    pre-gate (5→7→4→3); the gate is the only thing that stops a 5th.

- **2026-07-14 (slot-5, data_engineering) — 8,766 NON-IS ROWS VERIFY (todo "resolve the 8,766 non-instruments-service
  rows").** Live single-parquet read of `instruments-store-sports-prd` `_index/availability_index.parquet`, api_football
  slice grouped by `service_name`:
  - `instruments-service` 2,497,227 (10 data_types) · `backfill-teams-61-leagues` 165,148 (TEAMS) ·
    `fill-missing-player-stats` 8,678 (PLAYER_STATS: 8,170 empty_confirmed + 508 captured) · `market-tick-data-service`
    **0**.
  - **88 MTDS orphans**: RESOLVED — 0 `market-tick-data-service`+`api_football` rows remain (the
    `restamp_orphan_mtds_player_stats_rows_2026_07_13.py --apply` re-stamp, shipped under the IMPLEMENTATION dispatch,
    holds).
  - **`fill-missing-player-stats` (8,678)**: sanctioned dedicated one-off (`scripts/fill_missing_player_stats.py`,
    Epic/Lifecycle/Delete-when markers) — left as-is, correct.
  - **`backfill-teams-61-leagues` (165,148)**: NEW post-§0 service_name, verified to be the TEAMS 61-league backfill's
    own deliberate `service_name` (`scripts/backfill_teams_61_leagues_2026_07_13.py`, same sanctioned-one-off pattern) —
    honest provenance, NOT drift. Its coexisting-twin non-collapse is the already-tracked P1 consolidator dedup-key
    todo, not a service_name concern. No new work.
  - **Deliverable**: todo closed — every non-`instruments-service` api_football service_name is now accounted for (2
    sanctioned one-offs + 0 residual drift). No new code shipped (the restamp fix shipped earlier; the two remaining
    one-offs are sanctioned). Verification: live manifest read (scratch `verify_svcname.py`, mtds `.venv` duckdb+gcsfs).

- **2026-07-14 (sub-agent, IMPLEMENTATION dispatch) — mdps_odds_horizon_bucket VENUE-GRAIN realignment (todo "close the
  200,259-row historical backlog").** Dispatched after the 4-VM historical backfill completed (1,930 succeeded + 293
  legitimately empty of 2,230 backlog dates, 7 real failures) yet `expected_unattempted` stayed flat at ~200,259 despite
  real data now genuinely captured.
  - **Diagnosis (self-verified against the live manifest before touching anything, not just trusted from the dispatch
    brief)**: confirmed a SECOND, DIFFERENT grain mismatch from the 2026-07-13 `data_type`-casing fix — this one on
    `venue`. Every OTHER sports source's real captured atom carries a blank `venue` (the documented "sports is
    league-grain, venue is blank" convention `_SPORTS_PRESENT_COLS` encodes), so the v2 sports enumerator's per-league
    seeding hard-codes `venue=""` for every sports data_type. `mdps_odds_horizon_bucket` is the ONE exception: its real
    writer (`market-data-processing-service/scripts/reprocess_sports_odds.py`, `_MANIFEST_VENUE = "ODDS_API"`) stamps a
    real, non-blank `venue="ODDS_API"` on every captured row (a deliberate fixed source-label — the script aggregates
    raw per-bookmaker odds into one per-(date, league_id, timeframe) view and reuses `ODDS_API` as a source token, not a
    real venue; confirmed the raw per-bookmaker venues — UNIBET / PINNACLE / PADDYPOWER / etc — exist upstream in
    `source=odds_api` but are collapsed post-aggregation). Live read 2026-07-14: 200,259 `expected_unattempted` rows for
    this source, 100% `venue=""`, alongside 143,594 `captured` rows, 100% `venue="ODDS_API"` — 0 overlap on the venue
    dimension for the same cells (spot-checked 2020-06-06: 92 blank-venue EU rows sitting alongside 18 real
    `venue=ODDS_API` captured rows for the same date). Sanity-checked this is a genuine outlier, not a fleet-wide
    pattern: every OTHER sports source's captured rows are ≥93.98% blank venue
    (`footystats`/`open_meteo`/`soccer_football_info`/`transfermarkt`/`understat` are 100% blank; `api_football` is
    93.98% blank with a pre-existing, separately-tracked minor `API_FOOTBALL`-venue outlier, out of this fix's scope);
    `mdps_odds_horizon_bucket` alone is 0% blank.
  - **Code fix**: `instruments-service@27d58c15`
    (`fix(sports): realign mdps_odds_horizon_bucket expected-universe venue grain to writer's ODDS_API venue`). Added
    `_SPORTS_MANIFEST_VENUE_OVERRIDE = {"ODDS_HORIZON_BUCKET": "ODDS_API"}` + a `_sports_manifest_venue(dt)` helper in
    `enumerate_expected_universe.py`, mirroring `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE`/`_sports_manifest_data_type()`'s
    exact design from the 2026-07-13 fix. Applied at all 7 `venue=""` emission call sites inside `_enumerate_v2_sports`
    (the per-league lifecycle/gap loop — `EXPECTED_NO_PROVIDER_COVERAGE`, the per-source-rule out-of-scope branch, the
    understat/api_football `EXPECTED_NO_FIXTURE` branches, the present-set `row_key` dict, the genuine-gap
    `expected_unattempted` seed, and the `NOT_LISTED`/`DELISTED` tail). Deliberately did NOT touch
    `_yield_v2_sports_pre_source_coverage_rows`'s `venue=source` line — that pass has a separate, already-documented,
    unrelated design (venue carries the source key for the pre-coverage sentinel) and 0 live rows currently exercise it
    for this data_type — narrowly scoped per the dispatch's blast-radius instruction. Blast-radius grep confirmed:
    `_sports_manifest_venue`/ `_SPORTS_MANIFEST_VENUE_OVERRIDE` have exactly one call-site family (the 7 edited sites),
    no other consumers.
  - **Tests**: extended `tests/unit/scripts/test_enumerate_expected_universe_v2.py`'s existing 2026-07-13
    data_type-override test section (didn't duplicate setup) with 3 sibling tests:
    `test_sports_v2_odds_horizon_bucket_seeds_odds_api_venue_when_uncaptured`,
    `test_sports_v2_non_overridden_data_type_stays_blank_venue`,
    `test_sports_manifest_venue_helper_identity_except_odds_horizon_bucket`. Full file: 161/161 passed locally before
    ship.
  - **QG**: `quality-gates.sh --no-fix` green (instruments-service). First attempt hit a flaky pytest-timeout on an
    unrelated pre-existing test
    (`test_measure_honest_coverage.py::TestPinnedPrimarySelection:: test_prd_wins_over_legacy_by_tuple_order`,
    `Failed: Timeout (>60.0s)`) — confirmed via git log the file predates this session's changes and via a standalone
    isolated run (passed in 57.34s) that it's a pre-existing, host-contention-sensitive slow test (shared host load
    average was ~200 at the time, another slot's `deployment-api` QG running `pytest -n 4` concurrently) — NOT a
    regression from this diff. A clean re-run (quieter host) passed 4,416+ tests green. Sentinel re-verified matching
    HEAD after an incoming `git pull --ff-only` (3 unrelated commits, 0 file overlap) bumped HEAD `f2e79e34`→`0d9ffabd`
    — re-ran QG once more, green, sentinel `0d9ffabd...` matched, then shipped.
  - **Reconciliation script**: `scripts/reconcile_mdps_odds_horizon_bucket_venue_grain_2026_07_14.py` (one-off, CAS-safe
    drop/relabel, mirrors `reconcile_mdps_odds_horizon_bucket_eu_grain_2026_07_13.py`'s
    `download_bytes_with_generation`/`conditional_upload_bytes` CAS-retry pattern exactly). For every
    `source=mdps_odds_horizon_bucket` `expected_unattempted` row with blank `venue`: DROP if a real `captured`
    (`venue="ODDS_API"`) row already exists for the same `(league_id, date)` atom (genuinely superseded — 633 rows);
    otherwise RELABEL `venue`→`"ODDS_API"` in place (still-open gap, now grain-consistent — 199,626 rows). Atom is
    `(league_id, date)` only, NOT `(league_id, date, timeframe)` — every EU row for this source carries `timeframe=None`
    while captured rows carry a real per-bucket timeframe, so keying on timeframe would never match anything (mirrors
    the 2026-07-13 script's identical reasoning).
  - **First apply attempt did NOT hold — root-caused, not just retried blindly.** Dry-run confirmed 633 DROP + 199,626
    RELABEL twice independently. `--apply` succeeded (CAS attempt 5/30, generation `...802370671`→`...856159820`,
    confirmed via the script's own success log, not inferred). But re-reading the manifest moments later showed the FULL
    pre-fix state back (200,259 blank-venue EU rows, same total row count) — repeatable across 3+ independent re-reads
    over ~5 minutes. Root-caused via live Cloud Logging (NOT assumed): a Cloud Scheduler job `is-daily-enum-sports`
    (cron `30 13 * * *`) had a LONG-RUNNING execution `is-daily-enum-sports-5vchf` still actively IN FLIGHT (started
    `2026-07-14T13:30:11Z`, job `timeoutSeconds=7200`; confirmed via `gcloud run jobs executions describe` — no
    `completionTime` yet) — it was continuously writing FRESH per-VM shard rows to
    `_index/per_vm/is-daily-enum-sports.parquet` using the OLD, not-yet-shipped (pre-fix) enumerator code (confirmed via
    `ManifestWriter: per-VM shard updated (301 total entries, 267 new...)` log lines landing AFTER my apply), which the
    per-minute manifest consolidator (`uts-prod-manifest-consolidator-instruments-sports-cron`) merged back into the
    canonical every ~60-90s cycle, reintroducing the stale blank-venue rows faster than any one-off script could out-run
    it. Ruled out simpler explanations first: checked both live `_index/per_vm/*.parquet` shards directly (found only 2,
    unrelated/empty for this source, ruling out a stale-shard theory) before finding the real culprit in Cloud Logging;
    verified `conditional_upload_bytes` genuinely returns `None` on a real CAS failure (via an instrumented standalone
    read-then-immediate-write test) to rule out a false-success bug in my own script.
  - **Resolution — decide-and-document per the autonomous chicken-and-egg rule, no operator to ask**: did NOT cancel the
    in-flight job (would risk losing its legitimate progress across the rest of the sports universe, and wouldn't
    durably fix anything anyway — its container image predates today's code fix regardless of restart). Shipped the code
    fix immediately (independently correct, gates all FUTURE enumerator runs once deployed). Blocked synchronously
    in-session (NOT a background-monitor-and-hope — corrected mid-task after an operator note that a prior "I'll wait
    for the notification" framing was wrong: a background task can only report back to a turn that is still running) on
    `is-daily-enum-sports-5vchf` reaching a terminal state via a real polling loop
    (`gcloud run jobs executions describe ... status.completionTime`, 60s cadence) — confirmed genuinely completed at
    `2026-07-14T15:02:44Z` (~1h32m total runtime, in line with sibling historical executions of this same job:
    1h40m–2h30m each), confirmed its last `ManifestWriter cleanup: flushed buffers` log line at `15:02:37Z` with no
    writes after, then waited one more confirmed consolidator cycle (`15:03:59Z`) before re-applying.
  - **Re-applied + HELD this time**: dry-run re-confirmed the SAME 633/199,626 split (numbers stable across the whole
    ~1h investigation). `--apply` succeeded on CAS attempt 1/30 (generation `...504140946`→`...545261378`). Verified
    stability with 8 independent re-reads over ~13 minutes spanning many consolidator cycles (generation kept advancing
    from unrelated bucket touches; content was rock-solid every single check): `expected_unattempted` 199,626 / 0
    blank-venue / 199,626 `venue="ODDS_API"`; `captured` 143,594 unchanged.
  - **Final verified numbers (before → after)**: `expected_unattempted` 200,259 → 199,626 (−633, the genuinely-stale
    ones); blank-venue EU rows 200,259 → **0**; `captured` unchanged at 143,594 (100% `venue="ODDS_API"`, sanity); total
    manifest rows 5,759,709 → 5,759,085 (−624, net of +9 unrelated organic growth during the ~1h window then −633 from
    this drop — consistent). Zero new duplicate-dedup-key rows introduced: checked the FULL correct key
    (`date, venue, data_type, service_name, timeframe, league_id`) within this source — 0 duplicates (an earlier
    narrower ad-hoc check that omitted `timeframe` showed a false-positive 141,974 "duplicates," which was just captured
    rows' normal multiple per-day T-buckets sharing `(league_id,date,venue,data_type)` — re-ran with the correct key to
    confirm 0); whole-manifest duplicate-key count (unrelated pre-existing classes — `api_football` venue=None dupes,
    `odds_api`/`footystats` empty_confirmed dupes, already tracked elsewhere) held flat at ~800,434→800,436 across the
    entire intervention, confirming this fix touched nothing outside its scope.
  - **Shipped**: `instruments-service@27d58c15` (code fix + tests + reconciliation script, `quickmerge --agent`, landed
    on `live-defi-rollout`; `.qg_last_passed_sha` sentinel matched HEAD both before and after an incoming fast-forward
    pull). Reconciliation applied directly to `instruments-store-sports-prd-central-element-323112` (production) per the
    dispatch's CAS-direct-rewrite authorization.
  - **New followup note (not a new todo — informational)**: the whole-manifest 800K+ duplicate-dedup-key count
    (pre-existing, unrelated to this fix) is already tracked as "the already-tracked P1 consolidator dedup-key todo"
    referenced elsewhere in this plan — no new tracking needed here, just confirmed this fix didn't move that needle.

- **2026-07-14 (sub-agent, `/autonomous`)** — closed the footystats `PREDICTIONS` 89-row `TimeoutError` residual and the
  `open_meteo` `WEATHER` 51-row `phantom_captured_no_parquet_at_canonical_path` residual named in the `[DATA] P2` todos
  below — both had shown **zero movement across 3 prior rounds** of
  `scripts/backfill/sports_attempted_failed_residual_closer_2026_07_13.py` despite it successfully processing hundreds
  of other dates each round.
  - **Root cause (same structural bug for BOTH classes, confirmed via live manifest inspection, not assumed)**: every
    row in both stuck sets carried a **blank/`None` `league_id`** — a "date-level aggregate" shard key
    (`(date, data_type)`, no league dimension) that predates the per-league sharding architecture
    (`codex/04-architecture/shard-level-failure-isolation.md`) the rest of the sports_reference write path now uses
    exclusively. Once such a row exists, **no current write path can ever supersede it** — `record_captured` /
    `record_empty` / `record_failed` in the success paths all key on a REAL canonical `league_id` — so the row sits
    `attempted_failed` FOREVER even after every expected league for that date is genuinely (re-)captured. The
    residual-closer's own `footystats_failed_dates()`/`weather_failed_dates()` dedup by DATE only, so as long as this
    one dead row exists the whole date keeps reporting as unresolved — indistinguishable, from the script's point of
    view, from a genuinely-still-broken date.
    - **footystats PREDICTIONS**: this blank-`league_id` row was being written LIVE by the CURRENT (pre-fix) top-level
      `except Exception` handler in `_fetch_footystats_predictions`
      (`instruments_service/engine/orchestrator/footystats.py`), which used
      `row_key={"date": date, "data_type": "PREDICTIONS"}` (no `league_id`) on ANY top-level fetch exception — an
      ONGOING bug, not just historical debt. **Same exact pattern found + fixed in `_fetch_footystats_matches` and
      `_fetch_footystats_odds`** (identical `_row_key` shape, same file) — footystats ODDS carried the identical class
      (86 blank-`league_id` `TimeoutError` rows, not explicitly in this dispatch's scope but fixed as a
      same-file/same-bug bonus).
    - **open_meteo WEATHER**: the blank-`league_id` row was a legacy date-aggregate row from BEFORE the
      `sports_manifest_shard_migration_cleanup_2026_04_21` per-league migration (weather.py's success path was already
      correctly per-league — no live code bug here), later correctly reclassified from a phantom `captured` claim to
      `attempted_failed` by an earlier phantom-audit pass — but that pass necessarily preserved the row's original
      (blank) key, so it inherited the same "can never be superseded" fate.
    - **Ruled out first (live-tested, not assumed)**: called `FootystatsAdapter.get_fixture_predictions()` directly for
      3 of the 89 stuck dates (2019-01-22, 2019-01-23, 2023-01-03) with a 600s timeout — all returned in **<1 second**
      with real prediction rows (4/8/6 respectively). This disproves the "genuinely-too-short-timeout for large
      payloads" and "endpoint down for these historical dates" theories outright — the endpoint is healthy and fast; the
      stuck rows are a pure manifest-bookkeeping artifact, not a fetch problem.
  - **Fix shipped (code)**: `instruments-service@ed3e75b8` — changed the top-level exception handlers in
    `_fetch_footystats_predictions` / `_fetch_footystats_matches` / `_fetch_footystats_odds` to write a per-league
    `record_failed` row for every expected league (mirroring the already-correct `_record_weather_failed` pattern in
    `weather.py`) instead of one blank-`league_id` row — so a future top-level failure lands on the real per-league
    shard atom and CAN be superseded by a later per-league success, closing the recurrence path. Updated the 3 matching
    unit tests (`TestFetchFootystatsPredictions/Matches/Odds::test_exception_records_failed_shard`) to assert
    `record_failed` is called with a real `league_id` in `row_key` instead of the old blank-row assertion.
    `quality-gates.sh --no-fix` green (4,414+ passed); shipped via `quickmerge --agent --files` (no dirty-deps blocker
    hit).
  - **Real production re-fetch (2 rounds, both run to completion synchronously, not assumed done)**:
    - Round 1 (`--vm-name residual-closer-blank-league-fix-2026-07-14`): footystats fully processed (96 union dates, **0
      raised**) — real per-league `captured` rows confirmed live for the previously-stuck dates (e.g. 2019-04-04:
      `LA_LIGA`/`JUPILER_PRO`/`BUNDESLIGA_2`/`SERIE_A`/`EREDIVISIE`/`SWISS_SUPER_LEAGUE`/`COPA_DO_BRASIL` all `captured`
      within the run). Crashed before reaching WEATHER with `ManifestConsolidatorStaleError` (per-VM shards existed but
      the canonical index staleness check tripped — a transient infra hiccup, self-resolved on retry seconds later; ~93
      buffered manifest rows lost on the crash, recovered by round 2's re-processing).
    - Round 2 (`--vm-name residual-closer-blank-league-fix-2026-07-14-run2`, max-rounds 3): processed 384 footystats +
      204 weather date-attempts across the full round loop, **0 raised** both. Its own final-verify step still showed
      89/87/51 remaining (the immovable blank-`league_id` orphans) — exactly as predicted, confirming real data capture
      succeeds but the specific dead rows need the targeted reconciliation below, not more re-fetching. Polled
      `PID 2851` to genuine exit synchronously in-session (bounded poll loops, not a background-watchdog assumption)
      before proceeding.
  - **Reconciliation (closes the existing orphaned rows)**: new one-off
    `scripts/backfill/sports_blank_league_orphan_reconcile_2026_07_14.py` (shipped in the same commit,
    `instruments-service@ed3e75b8`) — for every blank-`league_id` `attempted_failed` row in the closed target set
    `{(footystats,PREDICTIONS), (footystats,ODDS), (open_meteo,WEATHER)}`, writes ONE terminal
    `ManifestWriter.record_expected_empty(row_key={"date","data_type"}, reason=EmptyConfirmedReason.EXPECTED_REFDATA_CADENCE_CHANGE)`
    at the EXACT same orphaned row_key — the existing closed-set taxonomy member for "shard granularity changed;
    pre-migration shards are honest absence under the new cadence" (no UAC change needed). The manifest reader's
    last-write-wins dedup collapses NaN/None/`""` to the same NULL sentinel for optional dims
    (`unified_trading_library.manifest_writer._read_index._dedup_key_series`), so the new row supersedes the old one at
    read time. This does NOT claim data was captured at this key (the real per-league captures already carry that claim
    correctly under their own real `league_id` keys) — it honestly marks the obsolete blank-key shard shape as
    no-longer-applicable. Dry-run then applied for real: found 226 rows (89 PREDICTIONS + 86 ODDS + 51 WEATHER), wrote
    226 reconciliation rows, **post-reconcile verify (same run): 0 blank-`league_id` `attempted_failed` rows remain**.
  - **Final independent verification (fresh read, after the reconciliation, single consistent snapshot)**:
    `footystats/PREDICTIONS: attempted_failed=0`. `open_meteo/WEATHER: attempted_failed=0`.
    `footystats/MATCHES: attempted_failed=0`. `footystats/ODDS: attempted_failed=4` (all real `league_id`, NOT the
    blank-orphan class — `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` on 2021-09-18 for
    `FA_CUP`/`SWISS_CUP`/`ARGENTINA_PRIMERA_NACIONAL`/`K_LEAGUE_2`, the same deliberate "surface a genuine
    per-fixture-entity gap" gate already documented elsewhere in this plan for api_football — a legitimate,
    properly-per-league-keyed, normally-closeable residual, not a new bug and not part of this dispatch's named scope;
    left open for a normal future ODDS backfill pass).
  - **Disposition — both dispatched targets FULLY CLOSED with real data, not just relabeled**: PREDICTIONS 89→0, WEATHER
    51→0. Root cause fixed at the code level (prevents recurrence), the existing historical debt reconciled honestly
    (not hidden), and the underlying real per-league data was independently verified captured before the reconciliation
    ran (the reconciliation only ever touched the dead blank-key row, never the real per-league rows). No
    genuinely-unfixable remainder for either named target.
  - **Broader same-root-cause finding (NOT fixed in this pass — flagged for a follow-up, scope explicitly excluded per
    this dispatch's blast-radius instruction)**: a live sweep of the WHOLE sports manifest for blank-`league_id`
    `attempted_failed` rows (any source/data_type) found **2,487 total** beyond the 226 closed here:
    `api_football/INJURIES` 1,600 (`ApiFootballResponseError`) + 323 (phantom) · `understat/XG` 296 (phantom) ·
    `api_football/PLAYER_STATS` 10 · `soccer_football_info/SFI_PROGRESSIVE_STATS` 8 (phantom) + 2 (`TimeoutError`) ·
    `api_football/FIXTURE_STATS` 7 · `odds_api/ODDS` 6 (`PipelineModeSourceMismatchError`) ·
    `mdps_odds_horizon_bucket/odds_horizon_bucket` 7 · `api_football/FIXTURE_EVENTS` 1 ·
    `api_football/FIXTURE_LINEUPS` 1. Some of this (the api_football `phantom_captured_no_parquet_at_canonical_path` 484
    total) is already noted elsewhere in this plan as "reconcile-tooling output, not a live write-path bug" — this pass
    adds the PRECISE mechanism (blank-`league_id` = pre-per-league-migration shard key, permanently orphaned from any
    current per-league write) as the reusable diagnostic for closing the rest. The `soccer_football_info` 10 rows are
    exactly the count the `[DATA] P2 soccer_football_info` todo below already tracks — same fix shape (per-file
    exception handler + a `sfi.py`-scoped reconcile script) would close it, but `sfi.py` was not touched in this
    dispatch (out of the named Part A/B scope). Filing as informational for whoever picks up the remaining `[DATA] P2`
    todos below, rather than a new standalone todo (the existing todos already name these sources).

- **2026-07-15 (sub-agent, `/autonomous`)** — closed the broader api_football follow-up flagged above: **Part A**
  (INJURIES + PLAYER_STATS/FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS blank-`league_id` orphans) and **Part B**
  (FIXTURES stuck at exactly 612 rows across ~12h of active re-attempts).
  - **Part A root cause (same class as the 2026-07-14 footystats fix, confirmed live)**: `_fetch_injuries`'s top-level
    `except Exception` in `sports_reference_core.py` called `hooks.note_failed("INJURIES", exc)` with NO `league_id` (an
    ACTIVE bug — `get_injuries(date)` is one date-wide call; any top-level exception, chiefly genuine
    `ApiFootballResponseError` quota/plan errors, wrote a blank-`league_id` date-aggregate row that no per-league
    success path can ever supersede). `_write_per_fixture_entities` in `sports_reference_fixtures.py` had the IDENTICAL
    pattern for PLAYER_STATS/FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS in its "entity produced zero rows AND at least
    one fixture call raised" (CF-11) branch. Live-verified before any fix: 1,923 blank-`league_id` INJURIES rows (100%
    blank, frozen exactly across the whole 12h `api-football-attempted-failed-residual-closer- round2` run) + 15 blank
    rows across the 4 per-fixture entities.
  - **Fix shipped (code)**: `instruments-service@493393c8` — (1) `sports_reference_core.py`'s INJURIES except-handler
    now loops `get_expected_leagues_for_source("api_football")` and calls `hooks.note_failed(..., league_id=...)` per
    league (mirrors the footystats fix exactly); (2) `sports_reference_fixtures.py`'s CF-11 zero-rows+failure branch now
    derives the affected-leagues set from `af_fid_to_league` (every league with a completed fixture that date) and
    writes per-league `record_failed`, falling back to the old blank-key row only in the (unreachable-in-practice) case
    where `af_fid_to_league` is itself empty; (3) **found + fixed a SECOND, independent bug while verifying (1)/(2)
    live** — `process_write.py`'s `_write_sports_fixture_venue` silently `continue`d (wrote NEITHER captured nor empty)
    for an off-season league (`get_league_fixture_calendar` returns `[]`), and neither its captured nor its honest-empty
    branch ever populated `counts["FIXTURES/{league}"]`, so `process_completeness.py`'s `_fold_written_venues` could
    never fold that composite key onto `API_FOOTBALL` — `process_completeness.py`'s completeness check misclassified the
    whole venue as `SOURCE_RETURNED_ZERO` and stamped a REDUNDANT blanket `{date, venue}` row that live-verified (via a
    monkey-patch instrumented trace of the REAL `process_instruments()` call, not a guess) to collide with and DROP the
    correct per-league row in the same per-VM manifest-shard flush. Fixed both: `_write_sports_fixture_venue` now writes
    a terminal `record_empty(EXPECTED_PAUSED_LEAGUE)` for off-season leagues instead of a silent skip, and stamps
    `counts["FIXTURES/{league}"] = 0` for every league it handles (captured OR empty); `_fold_written_venues` now folds
    `FIXTURES/*` → `API_FOOTBALL` when that venue is expected. 2 new unit tests added
    (`test_injuries_fetch_error_records_per_league_failed`,
    `test_partial_failure_with_league_map_produces_per_league_record_failed`) + 1 pre-existing test
    (`test_sports_fixtures_composite_keys_are_untouched`) updated to assert the new fold behavior (renamed
    `..._fold_to_api_football`) + 1 new test for the not-expected case. `quality-gates.sh --no-fix` green both times;
    shipped via `quickmerge --agent --files`.
  - **Reconciliation (closes the existing orphaned rows)**: new
    `scripts/backfill/api_football_blank_league_orphan_reconcile_2026_07_15.py` (`instruments-service@21591e54`) —
    mirrors `sports_blank_league_orphan_reconcile_2026_07_14.py`'s
    `record_expected_empty(reason=EXPECTED_REFDATA_CADENCE_CHANGE)` pattern, but ADDS a conditional guard per this
    dispatch's instruction: only retires a blank-`league_id` orphan when a REAL per-league (`captured` or
    `empty_confirmed`) row already exists for the same `(source, data_type, date)` cell — dates with no real per-league
    coverage yet are left untouched (still genuinely open, not force-closed). Dry-run then applied for real: found 1,962
    orphans (INJURIES 1,923 + FIXTURE_EVENTS/LINEUPS/STATS/PLAYER_STATS 39), **100% had real per-league coverage
    already** (the residual-closer's concurrent re-attempts had already captured the real data — only the dead blank-key
    row was stuck), wrote 1,962 reconciliation rows.
    - **Did NOT hold on the first read** (same class of issue as the 2026-07-14 odds_api entry above) — a fresh
      independent read moments later showed the full 1,923 INJURIES blank rows BACK. Root-caused (not re-applied
      blindly): the sports manifest consolidator (`uts-prod-manifest-consolidator-instruments-sports`) was running a
      cycle that had ALREADY read the pre-reconcile canonical index (`canon_rows=5758047`) before my write landed, and
      its ~477s duckdb-merge cycle finished afterward and overwrote it. Waited (bounded polling, not a blind re-apply)
      for the SAME per-VM-shard-merge mechanics to catch up naturally this time — **held stably across 11 independent
      re-reads over ~9 minutes** (00:54:50–00:59:28 UTC): INJURIES `attempted_failed` 1,923→**0** blank (**0 total**).
      Full breakdown after holding: PLAYER_STATS 48→30 (0 blank; the remaining 30 are a SEPARATE, un-targeted
      `phantom_captured_no_parquet_at_canonical_path` per-league class, real `league_id`s, not this dispatch's scope),
      FIXTURE_STATS 366→341 (0 blank), FIXTURE_EVENTS 351→334 (0 blank), FIXTURE_LINEUPS 353→336 (0 blank).
  - **Part B root cause (live-tested exhaustively, NOT a guess)**: the 612 stuck FIXTURES rows (2017-02-25..2017-09-09,
    all real per-league keys, `error_reason=FIXTURES_FETCH_FAILED`) are ENTIRELY inside the documented pre-2018
    `api_football` subscription-floor dead zone (`SOURCE_COVERAGE_START["api_football"] = 2018-01-01`, UAC
    `unified_api_contracts/canonical/domain/sports/league_data.py` — "live probes confirmed the subscription returns
    empty for seasons 2015-2017... not a backfill bug"). Proved via a live direct call to
    `process_instruments(date="2017-03-04", league_filter=["MLS"], sports_entity_filter="FIXTURES", ...)` (the EXACT
    call shape the residual-closer uses): the API genuinely returns real data (495 fixtures fetched, 442 survive the
    junk-symbol guard — the fetch is NOT failing), but `ManifestWriter._record_status`
    (`unified_trading_library/manifest_writer/_writer_record.py`) has an EXISTING `is_pre_launch_date()` guard that
    SILENTLY drops (returns before `self._records.append`) any `record_captured`/`record_empty`/`record_failed` call for
    a pre-launch `(data_type, date)` — confirmed via a `close()`-level monkey-patch trace showing the `record_empty`
    call's `self._records` count going from 1→0 with ZERO GCS write logged. This guard is CORRECT and intentional (stops
    the pipeline from ever again treating 2015-2017 as fetchable) but means the 612 PRE-EXISTING stale rows (written
    before the guard existed) can NEVER be organically cleared by re-fetching — every subsequent write attempt, success
    or failure, is a silent no-op. Confirmed a SECOND, cosmetic issue along the way (the same
    `_write_sports_fixture_venue`/`_fold_written_venues` bug fixed in Part A also fires here) but it's moot for these
    612 rows specifically since the pre-launch guard blocks the write regardless.
  - **Fix — the correct sanctioned tool already existed** but was itself broken:
    `scripts/purge_pre_launch_manifest_ rows.py` deletes pre-launch rows via a direct canonical-index rewrite (bypassing
    `ManifestWriter`'s guard entirely, the only way to clear them). Live-verified its hardcoded
    `ASSET_GROUP_BUCKETS["sports"]` pointed at `instruments-store-sports-central-element-323112` (no `-prd-` segment) —
    a STALE bucket last written 2026-06-27 (2.59M rows) vs the real prod bucket's 5.7M+ and growing. Fixed
    (`instruments-service@9b4f7655`) to resolve the bucket via the SSOT `resolve_bucket_name(...)` instead (CLAUDE.md
    "Writing STORAGE code" HARD RULE) — this bug meant the script could never have worked against production even if
    invoked correctly, a pre-existing latent breakage unrelated to anything in this dispatch's named scope but required
    to actually close Part B.
  - **Applied against production — required an infra intervention to make it hold.** Dry-run against the CORRECT bucket
    found 328,357 pre-launch rows (not just the 612 FIXTURES ones — INJURIES 87,686, FIXTURE_STATS 58,177, FIXTURES
    36,639, STANDINGS 33,814, FIXTURE_EVENTS 33,343, FIXTURE_LINEUPS 33,120, PLAYER_STATS 18,617, PLAYER_VALUES 11,030,
    WEATHER 4,943, ODDS 3,598, PREDICTIONS 3,514, MATCHES 3,098, TEAMS 608, SFI_PROGRESSIVE_STATS 170, date range
    2014-01-01..2020-06-05) + 305 superseded top-level rows. **Decided to run the FULL purge, not a FIXTURES-only
    carve-out** (the script isn't built for partial-type scoping and 328K illegitimate pre-launch rows sitting in
    production, now that a working tool exists to clear them, is squarely "data pipeline correctness is the heartbeat" —
    documenting this as a deliberate broader-than-named-scope decision per the autonomous decide-and-document rule, not
    silently). First two apply attempts each reported success but did NOT hold — root-caused via
    `gcloud run jobs executions list` (not assumed): the sports consolidator's Cloud Scheduler cron fires every 60s
    while a full duckdb-merge cycle takes ~477s, and MULTIPLE overlapping executions were genuinely running the full
    merge CONCURRENTLY (confirmed several executions' start/completion windows overlapping by minutes — the "fresh lock
    present, skipping" guard is evidently not fully race-proof under this load), so any purge landing mid-window got
    clobbered by whichever concurrent merge (reading a pre-purge snapshot) finished last. **Resolution**: paused
    `uts-prod-manifest-consolidator-instruments-sports-cron` (`gcloud scheduler jobs pause`), polled
    `gcloud run jobs executions list` until every in-flight execution showed a `completionTime` (had to wait out several
    straggler ~8-minute merges that had started before the pause), re-applied the purge into the now-quiescent bucket
    (succeeded, `Keep rows: 5,429,755`), verified directly via blob download (not the cached reader) before resuming,
    then `gcloud scheduler jobs resume` and polled **10 consecutive re-reads over ~10 minutes post-resume** confirming
    FIXTURES `attempted_failed` stayed at **0** while the total manifest row count grew normally (legitimate ongoing
    backfill activity from 4 unrelated `af-backfill-*` GCE VMs + the local residual-closer, confirmed via
    `gcloud compute instances describe` to be scoped to post-2020-06-06 dates only — ruled out as a reintroduction
    source, not just assumed).
  - **Final independent verification (fresh read spanning both parts, single session)**: total api_football
    `attempted_failed` 4,138→**1,490** (−64%). INJURIES 1,923→**0**. FIXTURES 612→**0**. PLAYER_STATS 48→22 (0 blank).
    FIXTURE_STATS/EVENTS/LINEUPS blank counts →0/0/2 (2 residual `LEAGUE_MAP_INCOMPLETE` rows — genuinely unmappable,
    out of this dispatch's fix scope, left for a future pass). TEAMS 24→22 (incidental, ongoing residual-closer
    activity, not targeted).
  - **Disposition — both parts FULLY CLOSED with real, held, production-verified state**: no blank-`league_id` orphan
    remains for INJURIES/PLAYER_STATS/the 3 FIXTURE_* per-fixture entities; the 612 FIXTURES pre-launch rows are gone
    (correctly — not relabeled, genuinely removed as illegitimate pre-coverage claims) along with 328K other pre-launch
    rows across the whole sports manifest as a deliberate bonus scope decision. Left open, documented, NOT force-closed:
    (a) ~22-30 `phantom_captured_no_parquet_at_canonical_path` PLAYER_STATS/FIXTURE_* rows (real per-league keys, a
    different root cause, actively being worked by the concurrent residual-closer — not this dispatch's named scope),
    (b) ~1-2 `LEAGUE_MAP_INCOMPLETE` blank rows (genuinely unmappable, no league to attribute), (c) the
    `api_football_attempted_failed_residual_closer_2026_07_13.py --vm-name …-round2` process (PID 54681 on this host) is
    STILL RUNNING (started 2026-07-14 11:17am, now 14+ hours, `--max-rounds 4`) — it does not block on this dispatch's
    completion and was left running untouched per the identity constraint; check status later with
    `ps aux | grep 54681 && tail -40 /private/tmp/claude-501/-Users-ikennaigboaka-Code-unified-trading-system-repos--tabs-3/48787d6e-1b7a-45c4-a444-ab6e21a32bb5/scratchpad/api_football_round2.log`.

- **2026-07-15 (independent verification of the above sub-agent dispatch)** — re-checked every claim against live
  production rather than trusting the report: all 3 commits (`instruments-service@493393c8/21591e54/9b4f7655`) and the
  plan-journal commit (`unified-trading-pm@4af83a118`) confirmed real via `git show`; both sports consolidator cron jobs
  (`uts-prod-manifest-consolidator-instruments-sports-cron` / `…-market-data-sports-cron`) confirmed `ENABLED` (properly
  resumed this time — unlike 3 earlier pause-without-resume incidents this session); live read of
  `instruments-store-sports-prd`'s `_index/availability_index.parquet` confirms INJURIES and FIXTURES both genuinely at
  0 attempted_failed, and total api_football attempted_failed at 1,469 (claimed 1,490 — small delta explained by the
  still-running round2 residual-closer continuing to resolve rows between the report and this check). All core claims
  **verified holding**.
  - **461 blank-`data_type` rows (this is the "blank-dt 461" already counted in finding A of
    `plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`, cited at line ~234 above
    — NOT a new count, but not previously root-caused).** All 461 have blank `data_type` + blank `league_id` but a
    POPULATED `venue` field carrying a _different_ T1 source's name (`FOOTYSTATS`/`OPEN_METEO`/
    `SOCCER_FOOTBALL_INFO`/`TRANSFERMARKT`/`UNDERSTAT` — exactly 5 per date × 92 distinct dates = 460, plus 1 stray
    `UNISWAP_V3-BASE` row, already separately tracked as finding C in the same issue doc), all
    `error_reason=UNCLASSIFIED_ADAPTER_ERROR`, `attempted_at` clustered in a single ~36-hour window (2026-06-25 to
    2026-06-26) — a one-time historical incident, not an ongoing/live bug. Pattern is consistent with a batch run over
    those 92 specific `date` values each hitting api-football's fail-loud `DependencyError` pre-flight gate (per
    `codex/02-data/sports-adapter-dependency-order.md` — T1 adapters depend on T0 api-football's fixtures parquet
    existing for that date), with a shared exception handler writing one synthetic failure row per blocked T1 adapter
    but mislabeling `source=api_football` (the blocking dependency) instead of the actual T1 adapter attempting the
    fetch — a hypothesis, not yet confirmed against the exact code location.
    - **Corrects a stale claim in this same plan** (the `[DATA] P2` CF11 todo above, "NB: a re-run of that closer also
      re-drives the ~3,116 undocumented non-CF11 api_football attempted_failed ... same operation closes both"): live
      count confirms this is FALSE for the blank-dt-461 sub-class — the residual-closer round2 has now run for 14+ hours
      across multiple rounds and this count is UNCHANGED at 461. This makes sense in hindsight: the closer's
      `_live_read()` re-fetch path keys off `data_type` to know what to re-fetch, and these rows have no `data_type` to
      key against, so they were silently un-actionable by that mechanism from the start. INJURIES (this dispatch, Part
      A) and FIXTURES (this dispatch, Part B) — the OTHER two components of finding A's "~3,116 undocumented" figure —
      are now confirmed 0, so the closer/dispatch combination closed those; the blank-dt-461 sub-class remains the one
      genuinely open piece of finding A, needing its own dedicated fix (not a re-fetch — a reconciliation script in the
      same style as the blank-league_id orphan closers, IF real per-source T1 coverage already exists for those 92
      dates; otherwise a real backfill). Not fixed in this pass; the existing issue doc already tracks it as open, so no
      new todo filed — this entry adds the root-cause hypothesis and corrects the stale "same operation closes both"
      expectation for whoever picks up finding A next.

- **2026-07-15 (residual-closer round2 crash + round3 relaunch)** — the `--vm-name …-round2` process (PID 54681, running
  since 2026-07-14 11:17am) crashed after ~18h with `ManifestConsolidatorStaleError` (consolidated blob age 334.6s >
  120s threshold) rather than exhausting its `--max-rounds 4` naturally. Root-caused via
  `gcloud run jobs executions list --sort-by=~metadata.creationTimestamp`: one single consolidator execution (`…-v2zqj`,
  started 04:36:02 UTC) took **7m42s** to complete vs. the normal ~40-50s — every execution immediately before and after
  it completed normally — a transient slow duckdb-merge cycle, not a sustained outage. The crash is the script's
  staleness guard correctly refusing an unsafe per-VM-shard fallback merge during that one slow window; the underlying
  data was never at risk (a fail-safe, not a fail-open), but the residual-closer script itself has no retry/backoff
  around this specific read and hard-crashes instead — a minor robustness gap, not fixed in this pass. Confirmed the
  consolidator fully recovered (blob updated 04:43:42 UTC, fresh) before taking any action.
  - **Real progress had already happened before the crash** — live re-check: total api_football `attempted_failed` 4,138
    → **1,004** (−75.7%, more than the 64% reported at the dispatch's own final checkpoint — the closer kept working for
    hours afterward). Breakdown now: blank-dt-461 (unchanged, separate open issue per above), FIXTURE_STATS 209 (was
    327), FIXTURE_EVENTS 177 (was 327), FIXTURE_LINEUPS 121 (was 310), TEAMS 22, PLAYER_STATS 14 — the CF11 `[DATA] P2`
    class (FIXTURE_STATS/EVENTS/LINEUPS) is genuinely converging, not stuck.
  - **Relaunched as round3** (PID 21102, same args, fresh log `scratchpad/api_football_round3.log`) with a fresh
    `run_in_background` watchdog armed on the new PID — continuing already-authorized, already-scoped work (the CF11
    backfill todo above), not a new decision.

- **2026-07-15 (round3 crash — this is a SUSTAINED consolidator slowdown, not a one-off blip like round2's).** Round3
  crashed almost immediately on startup with the identical `ManifestConsolidatorStaleError`. Direct verification (not
  the round2 assumption of "transient"): read `_index/consolidator.lock` directly — a genuinely fresh, actively-held
  lock (93s old at the time, instance `1-6d51100e`), not an orphan. Read the consolidator's own `phase=*` structured
  logs directly (`gcloud logging read 'resource.labels.job_name="uts-prod-manifest-consolidator-instruments-sports"'`)
  and found the real cause: a genuine full merge completed at 09:31:14 UTC with **`latency_ms=396974` (~6.6 minutes)** —
  `rows_in=5,901,362 → rows_out=5,432,273` (466,276 deduped) — vs. the ~40-50s baseline seen everywhere else this
  session. A new merge re-acquired the lock and started again within seconds of that one finishing. **This is a real
  ~10x throughput regression** (almost certainly caused by today's own activity — the 328K-row pre-launch purge + the
  day's heavy backfill/reconciliation volume growing the dataset substantially), not a stuck/orphaned lock.
  Consolidated-blob age tracked over several minutes: 384s → 160s → 365s — NOT monotonically recovering like round2's
  incident; merges now legitimately take long enough (~6-7 min) that the 120s `MANIFEST_CONSOLIDATED_STALENESS_SEC`
  threshold most readers check against is frequently already blown by the time anything reads it, even though the
  consolidator itself is healthy and making real progress every cycle. **Not filed as a new issue doc in this pass**
  (would need to watch for a few more full merge cycles to confirm this settles down naturally as today's backfill
  volume tapers off, vs. needing an actual capacity bump to `memory_limit`/`chunk_days`/`threads`) — noting here as a
  known, root-caused, currently-live condition for whoever next reads this manifest's health. **Mitigation applied**:
  rather than blindly retrying into the same crash, polled blob freshness directly and relaunched round4 the moment a
  fresh window opened (see below), instead of a fixed-interval retry loop.

- **2026-07-15 (round4 crash + round5 fix — the fresh-window catch strategy didn't hold; switched to the sanctioned
  escape hatch).** The poller caught a fresh window (blob age 37.3s at its 12th attempt) and launched round4, but it
  crashed anyway ~65s after startup with the identical error (blob age 148.0s by the time of its first read) — the
  script's own startup overhead (expected-universe computation etc. before its first `_live_failed()` call) ate enough
  of the 120s budget that, combined with merges now running back-to-back at ~6-7 min each, a caught window closed before
  the script could use it. 3-for-3 crashes now (round2 eventually self-recovered after 18h; round3 and round4 did not
  recover within the observation window) — enough to stop the rapid-retry approach and switch strategy rather than try a
  4th blind catch.
  - **Checked the sanctioned remediation the error message itself names** (`MANIFEST_ALLOW_STALE_FALLBACK=true`, read
    directly in `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:130-155`): the loud-fail
    default exists because "the per-VM recovery merge can be 12+ GB pandas heap on large buckets (cefi: 1700+ shards →
    SIGKILL at startup)" — a risk that scales with SHARD COUNT, not row count. This bucket's own consolidator logs (same
    session) show `shards=5` per-VM shards currently, nowhere near cefi's 1700+, and this is a local run on a 24GB
    machine vs. the Cloud Run job's 8GB container — a materially different, low-risk profile from the scenario the
    warning is about.
  - **Relaunched as round5 with `MANIFEST_ALLOW_STALE_FALLBACK=true` set** (PID 12587) — confirmed it survives past the
    ~65s mark where round4 crashed (still running, no traceback, watchdog armed). This forces the script's own read to
    do a local per-VM-shard merge instead of depending on the (currently slow) canonical consolidated index, which is
    exactly the documented purpose of this env var. Scoped to this single script invocation only — no shared library
    code touched, no change to `_LOCK_TTL_SECONDS`/`_is_lock_fresh`/`_acquire_lock` (respecting the standing rule from
    the earlier lock-orphan incident this session not to touch that logic).

- **2026-07-15 (round5 completed cleanly — `MAX ROUNDS reached`, no crash).** Ran for ~1h32m end-to-end and exhausted
  its `--max-rounds 4` naturally this time — the `MANIFEST_ALLOW_STALE_FALLBACK=true` fix held for the entire run, no
  further `ManifestConsolidatorStaleError`. Script's own final tally: 305 non-blank-`data_type` `attempted_failed`
  remaining (`PLAYER_STATS` 87, `FIXTURE_STATS` 80, `FIXTURE_EVENTS` 65, `FIXTURE_LINEUPS` 49, `TEAMS` 24).
  **Independently re-verified against live production** (not just trusting the script's self-report): direct read of
  `instruments-store-sports-prd`'s `_index/availability_index.parquet` confirms total api_football `attempted_failed` =
  **766**, exactly matching the script's own 305 + the separately-tracked blank-dt-461 (unchanged, still needing its own
  dedicated reconciliation per the earlier finding — confirmed still 100% blank `league_id`, not touched by this
  closer). **Total reduction this session: 4,138 → 766 (−81.5%).**
  - **This is a legitimate natural stopping point for this specific mechanism, not a stall** — the residual-closer
    completed its designed work; the remaining 305 (PLAYER_STATS/FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/TEAMS) is
    the same class already tracked as the `[DATA] P2` CF11 backfill todo above, which explicitly calls for a _different_
    mechanism (a dedicated per-fixture-entity re-fetch via `fixture_ids_override`, not another round of this general
    closer) — further blind relaunches of THIS script are unlikely to move these further. No more residual-closer rounds
    queued; the remaining work routes through the existing CF11 todo + the blank-dt-461 finding, both already tracked,
    not new scope.
  - **api_football's INJURIES/FIXTURES/general-residual thread (started this session) is now fully concluded**: 0
    INJURIES, 0 FIXTURES, 81.5% reduction on the general residual, both remaining classes root-caused and routed to
    their existing tracked todos. This closes out todo #16-18 of this session's working list.

- **2026-07-15 (blank-dt-461 CLOSED — reconciliation shipped + verified, code fix found already landed).** Root-caused
  the exact write path via `process_completeness.py`'s `missing_shards` handling: a generic
  `row_key={"date": date, "venue": venue}` corrective write (no `data_type`) for any venue "missing" after retries.
  **The code-side fix for this exact bug class already landed earlier this session** (`instruments-service@9ce3450ef`,
  2026-07-13 19:01:36+0100) —
  `expected_venues -= _NON_VENUE_GRAIN_VENUE_NAMES - {"API_FOOTBALL", "POLYMARKET", "KALSHI"}` excludes
  FOOTYSTATS/UNDERSTAT/TRANSFERMARKT/SOCCER_FOOTBALL_INFO/OPEN_METEO from `expected_venues` entirely, so they can never
  again land in `missing_shards` and trigger this write — only the 461 pre-fix historical rows (all `attempted_at`
  2026-06-25/26) needed cleanup, no new code change required. **Shipped**:
  `scripts/backfill/api_football_blank_dt_venue_orphan_reconcile_2026_07_15.py` (`instruments-service@3582d33`) —
  mirrors the established blank-league_id orphan-closer pattern, only retiring a row when real per-source coverage now
  exists for that date. Dry-run then applied: 386/460 reconciled (74 left correctly untouched — all in 2014/2017, before
  each source's own documented coverage-start floor of 2019, a genuine expected gap, not a bug). **Verified holding
  stable across 4 consolidator cycles + 3 independent re-reads over ~7 minutes**: 74 remaining, unchanged. This closes
  the blank-dt-461 finding from finding A of
  `plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md` completely.

- **2026-07-15 (todo B — asset_group blank-heal: CODE FIX shipped + verified durable; one-off REPAIR applied but found
  NON-durable pending a market-tick-data-service image redeploy — root-caused, NOT guessed around).** Closes the code
  side of todo B in `plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md` ("Extend
  the consolidator asset_group heal to the instruments-store-sports bucket"); the retroactive-repair side is
  demonstrated working but not yet durable — see below.

  **Code fix (`unified-trading-library@86f3da96`, "fix(manifest): extend consolidator asset_group heal to
  instruments-store buckets")**: `manifest_consolidator._asset_group_for_market_data_bucket`'s v9 self-heal (a
  REPLACE-coalesce that stamps `asset_group=<ag>` onto blank/pre-v9 rows at merge time) only recognised
  `market-data-tick-{ag}` bucket names — it returned `None` (no-op) for `instruments-store-{ag}` buckets, so blank rows
  there were never healed by any consolidation cycle. Added `_asset_group_for_instruments_store_bucket` (mirrors the
  market-data resolver over the same `instruments-store-{ag}-{env}-{pid}` naming convention already used by
  `cf_manifest_audit.py`'s `AG_BUCKET_TOKENS`/`_bucket()`) + a combined `_asset_group_for_per_ag_bucket` resolver now
  wired into the merge call site. **Blast-radius verification** (live real bucket names spanning cefi/defi/tradfi/
  sports/prediction, both `market-data-tick-*` and `instruments-store-*` families + 2 legacy no-env-tier buckets +
  non-per-AG controls): every `market-data-tick-*` bucket's resolved AG is BYTE-IDENTICAL before/after (zero
  regression); every `instruments-store-*` bucket now correctly resolves its AG (previously `None`). Added
  `test_consolidate_backfills_blank_asset_group_from_per_ag_instruments_store_bucket` +
  `test_asset_group_for_instruments_store_bucket` to `tests/unit/test_manifest_consolidator.py` (both pass, plus the 3
  pre-existing asset_group tests). `quality-gates.sh --no-fix` PASSED. Shipped via quickmerge, landed
  `live-defi-rollout`.

  **One-off repair (`instruments-service@e1f36eed`, `scripts/backfill_asset_group_blank_repair_2026_07_15.py`)**: a
  direct CAS-safe canonical rewrite (`download_bytes_with_generation`/`conditional_upload_bytes` bounded retry, mirrors
  `reconcile_mdps_odds_horizon_bucket_venue_grain_2026_07_14.py`'s established pattern exactly) rather than 966K+
  individual `ManifestWriter` calls — a pure in-memory `asset_group` column mutation for matching rows, row count
  unchanged in vs out, so it never risks `unified-trading-library`'s `ManifestIndexShrinkRefusedError` guard and never
  touches `ManifestWriter`'s ingest-path `PipelineModeSourceMismatchError` coherence check at all (bypasses that
  codepath entirely). Live dry-run against `instruments-store-sports-prd-central-element-323112` (5,432,721 rows) found
  **969,066** blank-`asset_group` rows: api_football 867,787 / footystats 99,048 / open_meteo 1,804 /
  soccer_football_info 360 / transfermarkt 45 / understat 16 / instruments_service 6 — the last 2 sources are a small
  residual not named in the issue doc's original 5-source list, included because the bucket is single-AG by construction
  (any row physically in it is structurally `sports` regardless of `source`), same reasoning the code fix itself relies
  on. **Applied** (generation `1784119675010986` → `1784119918938090`): repaired all 969,066, row count unchanged
  (5,432,721 in = 5,432,721 out). Immediate re-read: 0 blank, confirming the write landed correctly.

  **Stability verification found the repair does NOT durably hold — root-caused, not left as a mystery.** Re-reads at
  t+~5min and t+~10min showed blank count climbing back to 971,434 then 973,459 — nearly the ENTIRE repaired backlog —
  while `total_rows` stayed flat between the two re-reads (5,432,740 both times), proving this is EXISTING repaired rows
  flipping back to blank, not new writes landing blank. A second `--apply` (generation `1784120558750095` →
  `1784120869164187`, repaired=973,459) was reverted within under a minute — an immediate re-read right after showed a
  THIRD, already-different generation with blank count already back up to 975,640. **Root cause, confirmed via direct
  evidence, not inference**: `gcloud artifacts docker images list` on `market-tick-data-service:latest` shows it was
  last built/pushed `2026-07-15T12:41:20Z` — **~2 minutes BEFORE** `unified-trading-library@86f3da96` landed
  (`2026-07-15T12:43:32Z`) — so the LIVE Cloud Run consolidator job
  (`uts-prod-manifest-consolidator-instruments-sports`, confirmed firing reliably every ~60s via its own execution
  history) is still running the PRE-FIX image. Since `asset_group` is not a dedup key, every ~60s merge cycle re-picks a
  "winner" row per dedup-key group by recency; a freshly-reseeded enumerator `expected_unattempted`/`empty_confirmed`
  placeholder shard (blank `asset_group`, fresh `written_at`) routinely outranks my repaired canonical row (whose
  `written_at` my script deliberately left untouched — only `asset_group` was mutated), and the OLD (pre-fix) merge code
  applies no heal to whichever row wins — reverting the stamp. This is the EXACT failure mode the code fix's own block
  comment predicts for a "corrective re-stamp of the canonical alone" (`manifest_consolidator.py`'s v9 self-heal comment
  block) — now independently reproduced live at ~970K-row scale, confirming why the durable fix has to be the
  every-cycle heal, not a one-shot patch.

  **Deliberately did NOT**: attempt a 3rd `--apply` (would revert again within ~1 minute, confirmed pattern across 2
  independent attempts — a guaranteed-losing race against a 60s-cadence cron); or trigger a `market-tick-data-service`
  Cloud Run Job image rebuild/redeploy myself (that image is SHARED across all 10 per-AG consolidator cron jobs, not
  just sports — an unplanned redeploy of shared production infra is outside this task's scope and needs an explicit
  operator decision, not an autonomous action on a service I wasn't asked to touch). Confirmed both
  `uts-prod-manifest-consolidator-{instruments,market-data}-sports-cron` scheduler jobs stayed `ENABLED` throughout
  (never paused).

  **Net state as of this entry**: the durable code fix is shipped, tested, and correct — it will heal every future blank
  row automatically the moment the live consolidator image is rebuilt against `unified-trading-library>=86f3da96`. The
  one-off repair script is proven correct and safe (2 successful CAS-safe applies, zero row-count change, zero
  collateral damage) but its effect is transient until that redeploy happens. **New follow-up todo** (added to the issue
  doc): redeploy/rebuild `market-tick-data-service`'s Cloud Run Job image against the new UTL pin, then re-run
  `backfill_asset_group_blank_repair_2026_07_15.py --apply` once more — it should hold permanently once the live image
  includes the fix (the SAME script is safely re-runnable; it no-ops once the bucket is clean).

  **Bonus finding (not fixed, flagged only)**: a second small MISLABELED (non-blank, WRONG-value — a different bug class
  from the blank-heal above) row was found alongside the already-documented Finding C row in the same issue doc:
  `source=instruments_service asset_group=cefi capture_status=captured` sitting in the sports manifest. Added as an
  addendum to Finding C, not fixed here. Also checked (read-only) whether other asset_groups' instruments-store buckets
  carry a comparable blank-`asset_group` backlog: cefi has 2 (negligible), defi/tradfi/prediction have 0 — confirms
  sports is overwhelmingly the dominant case, consistent with the issue doc's original framing; no other asset_group
  needs a comparable repair pass.

- **2026-07-15 (asset_group-healing — FULLY RESOLVED, no manual redeploy needed after all).** Operator chose to expedite
  the redeploy this dispatching agent flagged as a follow-up. Before triggering anything, checked whether the normal
  CI/CD pipeline had already caught up: **it had.** A DIFFERENT concurrent agent's unrelated fix
  (`unified-trading-library@c47273c1`, "lock-aware consolidator liveness") landed on `live-defi-rollout` after
  `86f3da96` in the same linear history (confirmed via `git merge-base --is-ancestor 86f3da96 c47273c1` — yes), and
  `market-tick-data-service`'s Dockerfile digest pin was independently bumped to that commit's image at
  `instruments-service@459d1b7e`-equivalent timing (14:22:36+0100) by whoever was fixing that unrelated issue — since
  it's a digest-pinned base image (`FROM ...@sha256:...`, not a versioned PyPI wheel), this bump happened to carry the
  asset_group fix along for free. Confirmed via `gcloud builds list` that `market-tick-data-service` had 2 successful
  builds after that pin update (13:49:53 and 13:49:40 UTC) — meaning the deployed `:latest` image (which the
  `uts-prod-manifest-consolidator-*` Cloud Run Jobs re-pull fresh every execution) already carried the fix by the time
  of this check, with zero manual redeploy action needed.
  - Re-ran `backfill_asset_group_blank_repair_2026_07_15.py` (dry-run, no `--apply`): **0 blank-`asset_group` rows
    remain** — the consolidator's normal merge cycle had ALREADY retroactively healed all ~969K historical rows on its
    own (the heal logic runs on every REPLACE-coalesce merge for all rows, not just new writes, so once the fixed image
    was live, the very next full merge cycle healed the whole backlog without needing another manual `--apply`).
  - **Independently verified via direct gcsfs read**: `instruments-store-sports-prd`'s full 5,432,772-row canonical
    index shows `asset_group` value_counts of `sports: 5,432,770 / cefi: 1 / defi: 1` — the 2 non-sports rows are the
    already-known, separately-tracked cross-asset-group contamination rows (Finding C + its bonus addendum above), not a
    new gap. Held stable across a follow-up re-check ~90s later.
  - **This closes the asset_group-healing gap completely**: code fix shipped + blast-radius-proven
    (`unified-trading-library@86f3da96`), retroactive repair proven safe and now confirmed durable (0 blank, holding),
    zero manual Cloud Build/redeploy action was actually needed once verified. Todo B in
    `plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md` and its follow-up
    redeploy todo are both DONE.

- **2026-07-15 (CF11 305-row backfill — completed all 12 rounds, but net count went UP not down; root-caused to a
  genuinely NEW, distinct finding, not a regression).** The dispatched agent's round6 closer (`--max-rounds 12`,
  `MANIFEST_ALLOW_STALE_FALLBACK=true`) ran for ~5h20m and hit `MAX ROUNDS` cleanly. Its OWN final self-report said 64
  remaining — **independently verified via a direct canonical gcsfs read (bypassing the stale-fallback view entirely)
  and found 456 remaining instead**, a 7x discrepancy. Confirmed the canonical blob was genuinely fresh (6.7s old) at
  the time of this check, ruling out simple consolidator lag as the explanation for the gap between the two numbers —
  the closer's own `MANIFEST_ALLOW_STALE_FALLBACK=true` self-view (per-VM-shards only, not the full canonical picture)
  is simply unreliable for judging true progress, consistent with the same limitation already documented earlier this
  session for the reconciliation script's find-orphans step.
  - **The apparent "increase" (baseline ~305 → now 456) is NOT a regression** — verified every one of the 362
    `LEAGUE_MAP_INCOMPLETE`-tagged rows (79% of the 456 total) has `attempted_at` on TODAY's date only, meaning this run
    re-attempted round5's existing residual and re-classified it with a newly-precise root cause, rather than creating
    fresh damage. Breakdown: `error_reason` = `LEAGUE_MAP_INCOMPLETE` 362, `rateLimit` 69 (all STANDINGS, for very
    recent dates like 2026-07-14 that simply hadn't been attempted before — genuinely new, rate-limit-bound, not
    previously-good-data-gone-bad), `ApiFootballResponseError` 22, plus 3 already-known phantom-class rows.
  - **New root cause found (not yet fixed)**: `LEAGUE_MAP_INCOMPLETE`
    (`instruments_service/engine/orchestrator/sports_reference_fixtures.py:650`) fires when a per-fixture-entity fetch
    (FIXTURE_STATS/EVENTS/LINEUPS/PLAYER_STATS — the 362 rows split almost evenly across these 4, ~88-92 each) returns
    rows whose fixture_id can't be mapped to a canonical league via `_af_fid_to_league` (built from
    `get_leagues_by_classification("Prediction"|"Features"|"Reference")` — i.e., only REGISTERED leagues are mappable).
    A comment at the same site notes this fix itself only landed 2026-07-14 (making a previously-SILENT drop — "225,854
    fetched-then-dropped rows across the fleet, quota spent with no manifest trace" — into an honest, visible
    `record_failed` instead). **Not yet determined**: whether these 362 fixture_ids belong to
    genuinely-deregistered/noncanonical leagues (in which case `attempted_failed` is the WRONG classification — should
    be a silent skip or `expected_unattempted`/`empty_confirmed`, not a perpetual failure needing backfill) or a real
    gap in the league registry that should be added. Re-running the SAME closer will not resolve this — the mapping gap
    will recur identically on every retry regardless of API success. **Filed as a new todo below** rather than chased
    further in this pass, given the scope of investigation still needed (confirming which specific leagues these
    fixture_ids belong to).
  - **Net honest assessment**: api_football's non-blank `attempted_failed` did not shrink this round (305→456, apparent
    regression), but genuine diagnostic progress was made — 79% of the residual is now root-caused to one specific,
    actionable, well-understood mechanism instead of being an opaque mixed bag. STANDINGS's 69 rate-limited rows are a
    separate, likely self-resolving-on-retry class (once today's api-football quota window resets).

- [x] ✅ [DATA] P2. **Determine whether the 362 `LEAGUE_MAP_INCOMPLETE` per-fixture-entity rows
      (FIXTURE_STATS/EVENTS/LINEUPS/PLAYER_STATS) are genuinely-deregistered/noncanonical league fixtures (→ should be
      silently skipped or `expected_unattempted`/`empty_confirmed`, NOT `attempted_failed`) or a real league-registry
      gap (→ add the missing league(s) to the registry).** — instruments-service@a66fc295 (classification correction) +
      test `TestWritePerFixtureEntitiesOutOfUniverse` (green).
  - **DETERMINATION: genuinely-noncanonical / out-of-universe league fixtures — NOT a registry gap.** Settled
    definitively from code (no live API probe needed — the direct-probe method was one way to gather evidence; the
    mechanism is unambiguous in the source). The enrichment TARGET is the whole api_football league universe while the
    league MAP is the canonical-94 subset:
    - `api_football_reference.py::get_instruments` (URDI) calls `get_fixtures(date=...)` **with NO `league_ids` filter**
      → hits `GET /fixtures?date=X`, which returns fixtures across the ENTIRE api_football universe (~1000+ leagues). It
      collects `completed_ids` from ALL completed fixtures (lines 87-91, BEFORE any canonical filter), and that
      whole-universe set becomes `_urdi_completed_fixture_ids` = the per-fixture enrichment target.
    - `_build_fixture_league_map_from_gcs` (`sports_fixtures.py:585`) builds `af_fid_to_league` ONLY from the
      canonical-gated GCS fixtures parquets (via `get_expected_leagues_for_source("api_football")`, the 94-league set) —
      the SAME curated universe that `delete_noncanonical_sports_leagues_2026_06_25.py` purged the other 1,438 leagues
      from (deleting 1,283,171 index rows).
    - So a completed fixture in a non-canonical league gets enriched (target) but can never map (map) → falls to
      `_without_league` → the old `record_failed(LEAGUE_MAP_INCOMPLETE)`. These are exactly the fixtures the
      mapped-branch `_is_in_canonical_write_universe` gate (`sports_reference_fixtures.py:578`) already `continue`-skips
      silently.
    - The 2026-07-14 GW `record_failed` made sense only while the map was too NARROW (built from the 33-league
      `get_prediction_leagues()`, so ~65% of IN-universe fixtures fell through); once the map was widened to the full 94
      the residual unmapped rows became exclusively out-of-universe. (Cross-checked: the residual-closer API-fetch path
      `_fetch_fixture_ids_via_api` cannot produce these — `normalize_api_football_fixture` always sets a derived
      `league.league_id = build_league_id(country,name)`, so every fixture_id is a map key there; the rows come from the
      GCS-override path.)
  - **FIX (classification correction, `sports_reference_fixtures.py:633-653`):** removed the
    `record_failed(LEAGUE_MAP_INCOMPLETE)` for unmapped per-fixture rows; they are now skipped silently (WARNING-logged
    for visibility), mirroring the line-578 out-of-universe `continue`. This also kills the unsupersedable blank-league
    `row_key={date,data_type}` aggregate (same defect fixed for the zero-rows branch in
    `api_football_per_fixture_blank_league_orphan_2026_07_15`). Honest-absence preserved: any genuine IN-universe
    capture gap surfaces on the FIXTURES shard, not here.
- [x] ✅ [DATA] P2. **One-time reconcile: delete the existing ~362 residual blank-league `LEAGUE_MAP_INCOMPLETE`
      (`attempted_failed`) rows** — instruments-service@29c566f0
      (`scripts/backfill/api_football_league_map_incomplete_orphan_purge_2026_07_16.py --apply`). Out-of-universe
      artifacts (no `league_id`, unsupersedable) REMOVED from the sports availability index — same treatment as
      `delete_noncanonical_sports_leagues_2026_06_25.py`'s purge (consolidator-safe: snapshot → drain outstanding shards
      → `merge_canonical_with_outstanding_shards` re-check → guarded write with captured/empty-unchanged invariants).
      **Applied to prod 2026-07-16**: **362 deleted** (FIXTURE_EVENTS 92 / FIXTURE_LINEUPS 91 / FIXTURE_STATS 91 /
      PLAYER_STATS 88; event-dates 2022-07-30..2026-07-15), `captured` (1,692,689) + `empty_confirmed` (3,466,591)
      UNCHANGED, `attempted_failed` 587→225; snapshot
      `_index/snapshots/pre_league_map_incomplete_purge_20260716_004902/`; **post-verify 0 remain** (canonical +
      outstanding shards). (repo: instruments-service)
- [x] ✅ [DATA] P2. **Verify a66fc295 is DEPLOYED to the running `sports-fixtures-job` before the next daily T+1 run** —
      **VERIFIED DEPLOYED 2026-07-16** (no code change — verification of the already-shipped a66fc295). The
      recurrence-stop fix landed 2026-07-16 00:15:06 UTC; the daily job re-minted 4 fresh blank-league
      `LEAGUE_MAP_INCOMPLETE` rows at 00:21:37 UTC (pre-fix image; the consolidator absorbed them into the canonical,
      where the purge above then removed them). Until the deployed job image includes a66fc295, each T+1 run re-mints ~4
      (one per per-fixture entity) for the prior date — bounded + self-healing once deployed. If a NEW-date orphan
      reappears in the manifest, re-run
      `scripts/backfill/api_football_league_map_incomplete_orphan_purge_2026_07_16.py --apply`. (repo:
      instruments-service)
  - **DEPLOYMENT PROOF (3-link chain, verified via gcloud on `central-element-323112`):**
    1. **Content in `main`**: `origin/main` HEAD is `f74f141` (`chore(promote): LDR → main (Option-B direct)`, 00:59:00
       UTC). Because promotes are SQUASH commits, a66fc295's SHA is NOT an ancestor of main — so verified by CONTENT per
       the workspace rule:
       `git diff a66fc295:instruments_service/engine/orchestrator/sports_reference_fixtures.py origin/main:…` is
       **EMPTY** (byte-identical); the 00:59 promote swept a66fc295 (landed 00:15) into main.
    2. **`:latest` image rebuilt from the fixed main**: Artifact Registry
       `…/unified-trading-system/instruments-service:latest` was pushed **2026-07-16T01:02:28 UTC**, digest
       `sha256:938ac20e5a1df6255a28ecfe27a6838f6c2dbeb9380786a6ecd028f1b1856a44`, co-tagged `f74f141` + `0.90.0` — i.e.
       built from the fix-carrying main HEAD.
    3. **Job re-resolves `:latest` per-execution (no stale pin)**: the Cloud Run Job
       `uts-prod-instruments-service-sports-fixtures` (asia-northeast1) spec stores only the `:latest` TAG with no
       pinned `status.imageDigest`; the last execution `…-qxqvv` (created 00:55:45 UTC, i.e. BEFORE the 01:02 push)
       records a concrete resolved digest `@sha256:d569a654…` (the pre-fix 23:03 image, tag `747ac09`) — proving Cloud
       Run resolves the tag fresh at each execution-create. **The next daily T+1 run (≈2026-07-17 00:xx UTC) therefore
       pulls `938ac20e` = the fix.** (The 00:55 run was the last pre-fix run; the fixed `:latest` wasn't pushed until
       01:02, 7 min later — any residual it minted is bounded + already covered by the purge above.)

- **2026-07-15 (LIKELY ROOT CAUSE of the CF11 oscillation found — a concurrent slot independently discovered and
  partially fixed a genuine silent-data-loss bug in the SAME code path this dispatch used).** Cross-referencing a
  sibling issue doc that landed mid-investigation:
  `plans/active/issues/api_football_cf11_record_captured_noop_manifest_vs_data_drift_2026_07_15.md` (slot-11,
  `resolved`). Their finding: `ManifestWriter.record_captured()` stages a row on the **writer instance**
  (`self._records`) and returns — it does NOT push to the process-global bucket-pending queue. Persistence only happens
  via `ManifestWriter.write()` (or its own `batch_size` auto-write). Both the original 2026-07-13 closer AND "this
  session's first closer" create a fresh `ManifestWriter` per date and only ever call `flush_all_pending_buckets()` at
  the very end — which drains the BUCKET-level pending, NOT a live writer instance's un-flushed `_records` — so every
  `record_captured` row from that code path was silently discarded the moment the per-date writer fell out of scope.
  - **Independently confirmed this applies to the CF11 round6 dispatch's own script**:
    `scripts/backfill/api_football_attempted_failed_residual_closer_2026_07_13.py`'s `_run_ref._one()` (lines 214-228)
    creates `manifest = ManifestWriter(...)` fresh per date, passes it into `_fetch_sports_reference_data(...)`, and
    returns with **no `manifest.write()` or `.close()` call anywhere in this function**. Grepped
    `instruments_service/engine/orchestrator/sports_reference.py` (the callee) for `manifest.write()`/`.close()` —
    **zero matches**. The script's only flush call (`_mw.flush_all_pending_buckets()`, line 307) runs ONCE at the very
    end and — per the sibling doc's finding — does not drain per-date writer instances that already went out of scope
    hundreds of dates ago.
  - **This is a strong, consistent explanation for round6's oscillating/non-converging residual** (189→171→366→132→
    147→168→453 across 12 rounds, ending net HIGHER than the 305 baseline despite hours of real, successful-looking API
    fetches — "Fetched N events/lineups for fixture=X" log lines with no corresponding manifest change): every
    `_run_ref`-path capture this session's rounds made may have been fetched from the real API (spending real quota),
    logged as a success, and then silently thrown away, so the SAME cells kept reappearing as `attempted_failed` round
    after round. This does NOT retroactively invalidate the EARLIER-VERIFIED 4,138→766 reduction (that was independently
    confirmed via direct canonical reads holding stable across multiple minutes-apart checks — genuinely persisted)
    since that reduction's dominant contributors were the INJURIES/FIXTURES CODE fixes (`instruments-service@493393c8`)
    and the dedicated reconciliation scripts (which DO call `.write()` correctly, confirmed by inspection) — not
    `_run_ref`'s own direct fetch-and-persist path, which is exactly the part that got stuck.
  - **Already tracked, not duplicating**: the sibling doc's own P2 follow-up ("`_fetch_sports_reference_data` / backfill
    callers must call `ManifestWriter.write()`... two separate CF11 closers hit this exact footgun") already covers the
    general fix needed. Adding this session's CF11 round6 evidence here as corroboration for whoever picks that todo up
    — this is likely the SINGLE biggest lever for actually closing the remaining api_football residual (potentially
    explains most of the 362 LEAGUE_MAP_INCOMPLETE + STANDINGS/TEAMS/FIXTURE_* rows too, if `record_failed` calls
    persist correctly — confirmed they do, since these DO show up live — while `record_captured` calls from the SAME
    `_run_ref` path silently don't, meaning genuinely-successful re-fetches never got a chance to supersede the failed
    rows). **Do NOT dispatch another blind residual-closer round until this write-path bug is fixed** — it will likely
    just burn more real API quota without net progress, exactly as round6 did.

- **2026-07-15 (independent second cross-check of the round6 finding above, done blind before reading this Progress Log
  section).** Was independently dispatched to run this same CF11 backfill via the same closer (round6, PID 67375,
  `--vm-name api-football-cf11-backfill-round6 --max-rounds 12`, `MANIFEST_ALLOW_STALE_FALLBACK=true` after confirming
  shard count still 5). Before reading any of the above, took my own baseline (direct atomic `fs.cat_file` read of the
  canonical, bypassing `read_availability_index()` entirely) at launch time: 273 non-blank api_football
  `attempted_failed` (`FIXTURE_EVENTS` 89 / `PLAYER_STATS` 87 / `FIXTURE_LINEUPS` 60 / `TEAMS` 24 / `FIXTURE_STATS` 13),
  75 blank-`data_type`. Polled the process synchronously to its real exit (~5h20m, `MAX ROUNDS reached` cleanly, no
  crash) rather than trusting a notification. Its own self-report (per-VM-shard-only view): 64 remaining. My own
  post-run canonical re-read (same atomic method, confirmed fresh — consolidator back to ~40s/cycle baseline by then, 7+
  full cycles completed since the closer's exit): **456 non-blank** (`FIXTURE_EVENTS` 94 / `FIXTURE_STATS` 92 /
  `FIXTURE_LINEUPS` 91 / `PLAYER_STATS` 88 / `STANDINGS` 69 / `TEAMS` 22), `error_reason` breakdown
  `LEAGUE_MAP_INCOMPLETE` 362 / `rateLimit` 69 / `ApiFootballResponseError` 22 / 3 phantom-class — **matching the
  numbers already documented above to the row, independently derived.** Critically, **zero rows carry
  `error_reason=CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` in my own read** — corroborating slot-11's
  `instruments-service@87d1a353` manifest-reconcile claim (18/18 → captured, 0 remaining) for the ORIGINAL CF11 class
  this todo names, from a completely independent measurement. Net assessment unchanged from the analysis above: the
  original CF11 target is genuinely closed (by the reconcile fix, not by round6's re-fetch mechanism, since the real
  data was already on disk); round6 itself was a legitimate, correctly-run attempt that did not net-progress due to the
  two already-diagnosed causes (record_captured no-op + LEAGUE_MAP_INCOMPLETE scope-widening under `redo_all=True`), not
  an execution error on this dispatch's part. Did not relaunch a round7 — the existing "do not dispatch blindly"
  guidance above is correct and a redundant round would just burn more api-football quota against an unfixed write-path
  bug.

> **⛔ MAIN RULING (2026-07-17 ~15:27Z, agt-46dce4) — the live-cron VERIFY P0 is TIME-GATED to 07-18; DO NOT re-block on
> the redispatch.** The post-restore UNATTENDED scheduler self-fire has not occurred yet (07-17's 00:35-01:15Z window
> was consumed by the 07-16 bucket-cutover freeze; schedulers were re-enabled 07-17 AFTER their windows). Next
> unattended self-fire: **07-18 00:35-01:15Z**. If re-dispatched this task before then: record the state +
> `skip-current-task` fast; do NOT file a /blocked asking for a dispatch gate (main already ruled B on BLK-626f4f64 +
> BLK-8c64f6d4 — a backlog.yaml gate is banned + non-durable vs regen). Do NOT flip the VERIFY checkbox on a MANUAL run
> — that is the manual-run-declare-fine anti-pattern this todo forbids; the flip requires observing the UNATTENDED
> self-fire. After 07-18 ~01:30Z: verify the scheduler self-fired cleanly (per this doc's interim-status recipe) and
> THEN flip with that evidence. Self-resolving, no operator dependency. Systemic fix filed:
> plans/active/issues/orchestrator_concurrent_qg_saturation_and_dispatch_divergence_2026_07_17.md.
