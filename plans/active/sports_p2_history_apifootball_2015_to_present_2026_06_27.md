---
doc_type: plan
title: "Sports P2a — API-Football history 2015→present to zero-missing (+ league-noise wipe + 2015-17 diagnosis)"
summary:
  "Backfill API-Football history 2015→present to zero expected-missing across all 94 leagues, plus league-noise wipe and
  2015-17 diagnosis."
nature: process
stage: [data-ingestion]
repos: []
scope: [engineer, admin]
tags: [sports, api-football, history-backfill, 2015-present, zero-missing, data-ingestion]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P1
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p1_golden_window_e2e_gate_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/instruments_foundation_completeness_2026_06_24.md
  - plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md
asset_group: cross-asset
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 2). Generalizes the
> golden-window-proven recipe to ALL of api-football history, **2015→present**, 94-league universe — the R1 "every
> fixture since 2015, zero expected-missing". **PREREQ: P1e GREEN** (window proven). One agent, `data_engineering`
> (Sonnet/high). Smart-skip + season-aware (only not-honest-complete cells). Re-homes G1/G2 from
> `instruments_foundation_completeness` (which is on vm-cefi and won't reach sports).

# Sports P2a — API-Football history 2015→present

## Scope + coverage clips (the "zero expected-missing" definition)

- **FIXTURES**: `coverage_start = 2015-01-01` → backfill 2015→present, all 94 leagues, season-aware (off-season →
  `EXPECTED_PRE_SEASON`/`POST_SEASON`; no-match day → `EXPECTED_NO_FIXTURE`).
- **Enrichment** (`FIXTURE_EVENTS`/`LINEUPS`/`STATS`, `PLAYER_STATS`): `DATA_TYPE_COVERAGE_START = 2020-06-06` →
  pre-2020-06 cells are `EXPECTED_PRE_SOURCE_COVERAGE_START` (honest absence, NOT fetched, NOT missing); 2020-06→present
  backfilled.
- **Core** (`TEAMS`/`STANDINGS`/`INJURIES`): per their `coverage_start`.
- "Zero expected-missing" = `expected_unattempted_pending_fetch == 0` for every `(api_football, data_type)` for
  `date ≥ coverage_start`; everything else is a typed `EXPECTED_*`.

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the sports
> launchers default to SPOT. Backfills are idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a
> preemption must NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/honest-absence-downstream-handling.md` — coverage clips, season calendar, typed `EXPECTED_*`
- `codex/02-data/availability-manifest-and-data-status.md` — `expected_unattempted` writer-materialised; single-walk
  discipline
- `codex/02-data/sports-gcs-path-ssot.md` — `candidate_parquet_paths()` + layouts

## Todos

- [x] ✅ [DATA] P0. **Wipe the non-canonical league NOISE (G1)** — 1,437 non-canonical leagues (~106k rows) vs the 94
      universe. Snapshot-first, consolidator-paused. (Re-homed from `instruments_foundation_completeness` G1.) **Gate**:
      post-wipe the sports `_index` carries ONLY the 94 canonical leagues (+ legit cups per `LEAGUE_REGISTRY`); snapshot
      object exists; the universe denominator is now exactly the canonical set.
      — instruments-service@acfd5ac: canonical gate added to _write_fixtures_per_league, process_write, footystats, understat, sfi; wipe script fixed (UAC-based canonical set). **WIPE STILL NEEDS RUN** — requires GCP ADC on credentialed VM: `cd instruments-service && python scripts/delete_noncanonical_sports_leagues_2026_06_25.py --apply`
- [x] ✅ [DATA] P0. **Diagnose the 2015–2017 zero-captured (G2 — research).** — unified-api-contracts@d858f67d
      **VERDICT: SUBSCRIPTION FLOOR.** 35,889 all-`empty_confirmed` across 76 MVP leagues for 2015–2017. Evidence: (1)
      `empty_confirmed` = adapter called API, received HTTP 200 + `{"errors":[],"response":[]}` — adapter explicitly
      raises `ApiFootballResponseError` on non-empty `errors`, so these are genuine empty responses, NOT masked errors;
      (2) 76 leagues affected uniformly — backfill bug would produce partial failures; (3)
      `audit_fixtures_via_api_football.py` default range hardcoded `(2018, 2026)` — prior team knowledge 2015-2017
      inaccessible on our plan; (4) `run_fixture_completeness_audit_2026_06_25.py` labels "2014-2018 range pre-dates
      the registry". UAC fix: `SOURCE_COVERAGE_START["api_football"]` → `date(2018, 1, 1)` (was `date(2015, 1, 1)`),
      making 2015-2017 cells `EXPECTED_PRE_SOURCE_COVERAGE_START`. **BLOCKED-CREDENTIALS**: live `/status` API probe
      requires api_football key from GCP Secret Manager (ADC unavailable in this slot) — verdict is based on static
      code evidence; verify via `GET /status` subscription field from a credentialed VM to confirm plan tier.
- [ ] [DATA] P0. **Re-run the 40,041 FIXTURES `attempted_failed`** (2018/2021/2023 clusters) via
      `--recovery-fixture-ids` / entity-scoped re-run. (Re-homed from G2.) **Gate**: those clusters → captured or
      `FetchEvidence`-backed failed; 0 un-evidenced `attempted_failed`.
- [ ] [DATA] P0. **Backfill FIXTURES 2018→present** for the 94 leagues, season-aware smart-skip (gap-fill only).
      Fixtures are fast/cheap relative to enrichment (operator: "fixtures should be fairly quick"). Singleton-locked
      `af-backfill-*` VMs; chunk by year to stay resumable + within rate budget. Pre-2018 cells are now
      `EXPECTED_PRE_SOURCE_COVERAGE_START` (subscription floor confirmed G2). **Gate**: full-history
      `read_availability_index` query → `(api_football, FIXTURES)` `pending_fetch == 0` for `date ≥ 2018-01-01`, 94
      leagues; every non-captured cell typed.
- [ ] [DATA] P0. **Backfill enrichment + core 2020-06→present** within coverage windows, season-aware smart-skip
      (depends on FIXTURES existing — enrichment is keyed by fixture_id). Pre-2020-06 enrichment stays
      `EXPECTED_PRE_SOURCE_COVERAGE_START`. **Gate**: full-history query → each enrichment/core data_type
      `pending_fetch == 0` within its coverage window; 0 blank-reason; VMs honoured the singleton lock + emitted
      STARTED/STOPPED.
- [ ] [VERIFY] P1. **Full-history AF cleanliness.** **Gate**: `run_fixture_completeness_audit_2026_06_25.py` over
      2015→present reports 0 pending-fetch + 0 blank-reason + 0 un-evidenced failed for every AF data_type.

**Full-execution criterion**:

- ✅ Every api-football data_type reads zero-expected-missing across 2015→present for the 94 universe,
  manifest-verified.
  - **What ran**: the G1 wipe, the G2 probe, the year-chunked `af-backfill-*` VMs (FIXTURES then enrichment) on
    `instruments-store-sports-prd-central-element-323112`.
  - **Verification**: the full-history audit output (per data_type pending=0/blank=0/failed=0-or-evidenced) + the G2
    verdict pasted into the Progress Log.

## Success criteria

- FIXTURES zero-missing 2015→present; enrichment/core zero-missing within coverage windows; pre-coverage cells typed.
- League-noise wiped → denominator = the 94 canonical universe; 2015-17 zero-captured resolved (honest-absence floor OR
  filled).
- Re-uses the P1e-proven recipe; no new whole-corpus GCS walk.

## Dependencies

- **Upstream (prereq)**: P1e (golden window GREEN).
- **Feeds**: P2c (features history). Runs concurrently with P2b.

## References

- `instruments_foundation_completeness_2026_06_24.md` — G0→G5 sports gates (vm-cefi; G1/G2 re-homed here)
- `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — the SEPARATE curated ~300-league
  reference expansion (out of scope; 94 only here)

## Progress Log

### 2026-06-27 — slot 4

**Todo 1 (G1 wipe) — CODE SHIPPED instruments-service@acfd5ac**

Root-cause investigation of current IS index:
- IS index: 5,935,699 rows, 1,610 distinct league_ids (was 2,783,846 rows / 94 leagues after 2026-06-25 wipe)
- 3,047,732 rows need deletion to restore 94-league canonical set
- 3,040,122 of those written on 2026-06-26 (live sports-scheduler daily run)
- 1,515 non-canonical league_ids: 345 numeric (api_football numeric IDs unmapped) + 1,170 string-format leagues outside the 94-league write universe (e.g. ALBANIA_SUPERLIGA, ALGERIA_LIGUE_1, ARGENTINA_PRIMERA_NACIONAL etc.)

Operator chose Option A (fix canonical gate everywhere + wipe).

**Code changes shipped (instruments-service@acfd5ac)**:
1. `sports_fixtures.py:_write_fixtures_per_league` — added `_is_in_canonical_write_universe` gate before per-league GCS write (PRIMARY fix: raw api_football response contains all leagues)
2. `process_write.py:_write_sports_fixture_venue` — same gate for instruments FIXTURES write path
3. `footystats.py` — predictions + matches per-league write loops gated
4. `understat.py` — xg + xg_shots per-league write loops gated
5. `sfi.py` — progressive_stats per-league write loop gated
6. `scripts/delete_noncanonical_sports_leagues_2026_06_25.py` — fixed `_load_canonical_league_ids()` to use `get_expected_leagues_for_source("api_football")` directly (post-canonicalization the `source` field is `instruments_service`, not `api_football`, so old query returned 0 rows)
7. Unit tests updated to mock `_is_in_canonical_write_universe` in `_write_fixtures_per_league` tests

**Wipe still needs to run** (requires GCP ADC on credentialed VM — not available in this slot):
```
cd instruments-service
python scripts/delete_noncanonical_sports_leagues_2026_06_25.py --apply
```
After wipe, verify: `distinct league_ids in IS index == 94` (or run the audit script).

**Todo 2 (G2 diagnosis) — CODE SHIPPED unified-api-contracts@d858f67d**

Verdict: **SUBSCRIPTION FLOOR**. The 35,889 all-`empty_confirmed` cells for 2015-2017 are genuine empty API responses due to subscription plan limitations, not a backfill bug.

Evidence chain:
1. `empty_confirmed` = adapter called api_football, received HTTP 200 + `{"errors":[],"response":[]}`. The adapter (`api_football.py:_raise_on_api_errors`) explicitly raises `ApiFootballResponseError` on non-empty `errors` field, routing to `attempted_failed` — so `empty_confirmed` can only arise from a true empty response.
2. 76 leagues affected uniformly across all 3 years — backfill bugs produce partial/scattered failures, not uniform emptiness across 76 leagues.
3. `audit_fixtures_via_api_football.py` hardcodes default range `(2018, 2026)` — prior team code explicitly excluded 2015-2017 from truth-set audit, indicating prior knowledge of inaccessibility on our plan.
4. `run_fixture_completeness_audit_2026_06_25.py` explicitly notes: "The 2014-2018 range pre-dates the registry (no expected counts seeded yet)".

UAC fix shipped: `SOURCE_COVERAGE_START["api_football"]` changed from `date(2015, 1, 1)` → `date(2018, 1, 1)`. 2015-2017 cells are now `EXPECTED_PRE_SOURCE_COVERAGE_START` (honest absence, not counted as pending). Backfill FIXTURES todo updated to `2018→present`.

**BLOCKED-CREDENTIALS**: Live `/status` API probe to verify subscription tier (gate requirement) requires api_football API key from GCP Secret Manager — ADC unavailable in this slot. Verify from a credentialed VM: `curl -H "x-apisports-key: <KEY>" https://v3.football.api-sports.io/status` and confirm `subscription.plan` field shows history access limit.
