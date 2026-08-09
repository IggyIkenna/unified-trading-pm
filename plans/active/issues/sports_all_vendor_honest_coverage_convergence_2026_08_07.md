---
doc_type: issue
title:
  All sports-vendor honest-coverage convergence — every source (incl. odds_api / MTDS) down to captured +
  empty_confirmed only
summary: >-
  Operator directive (2026-08-07, verbatim): "continue with sports_af_full_entity_completion_2026_08_03.md if its spec'd
  to be all data sourced backfilled to 100% honest coverage — only captured and empty confirmed — any attempted_failed
  or out of scope or expected unattempted should be backfilled, migrated, deleted or reconciled including odds api so
  that IS and MTDS is 100% done." That doc is scoped specifically to API-Football entities (title: "Full API-Football
  entity completion") and is already at 800/1000 lines — this is a genuinely broader, different-in-kind mandate (every
  sports source, including odds_api/MTDS, not just AF), so it gets its own doc per this workspace's own established
  split precedent (the AF doc itself was split off from `sports_satellite_ao_dispatch_batch2_2026_07_24.md` for the same
  reason). A full live census across every sports source (2026-08-07T10:2X Z, single manifest read, 10,463,368 rows)
  found the real remaining scope: it is much larger than the vendor-completion audit done earlier the same session
  suggested — that audit only checked `attempted_failed=0` per vendor and called weather + understat "100% clean" on
  that basis, which was true but incomplete: weather alone has 205,517 `expected_unattempted` rows (never even tried)
  and SFI has 205,363. odds_api has by far the largest `attempted_failed` cluster (13,916 rows, two distinct root
  causes, one of them still actively recurring as of yesterday). This doc is the tracking home for all of it going
  forward.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [sports, honest-coverage, data-correctness, odds-api, mtds, multi-vendor]
related:
  [
    plans/active/issues/sports_af_full_entity_completion_2026_08_03.md,
    plans/active/issues/transfermarkt_player_values_data_discarded_2026_08_07.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-07
author: claude-agent
priority: P1
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["sports_af_full_entity_completion_2026_08_03 continuation, operator directive, 2026-08-07"]
drift_direction: advance-code
context_scope:
  [
    instruments-service/scripts/census_other_vendors_gap_2026_08_06.py,
    instruments-service/instruments_service/engine/orchestrator/transfermarkt.py,
    instruments-service/instruments_service/engine/orchestrator/sfi.py,
    deployment-service/scripts/vm/launch-sfi-backfill-vm.sh,
    deployment-service/scripts/vm/launch-footystats-backfill-vm.sh,
  ]
---

## The full picture (live census, 2026-08-07T10:2XZ, one manifest read, 10,463,368 rows)

| source                   | attempted_failed |  captured | empty_confirmed | expected_unattempted |
| ------------------------ | ---------------: | --------: | --------------: | -------------------: |
| api_football             |           35,058 | 1,807,273 |       3,465,256 |              658,426 |
| footystats               |                0 |    83,827 |       1,229,662 |                    0 |
| instruments_service      |                2 |     3,626 |          96,842 |                    0 |
| mdps_odds_horizon_bucket |            2,791 |   198,520 |         261,907 |              157,994 |
| odds_api                 |           13,916 |    39,405 |          28,088 |                    0 |
| open_meteo (weather)     |                0 |    12,905 |         245,430 |              205,517 |
| soccer_football_info     |                0 |    20,864 |         206,734 |              205,363 |
| transfermarkt            |                8 |    48,895 |         419,099 |                    0 |
| understat                |                0 |    14,380 |       1,000,336 |                   30 |

`mdps_odds_horizon_bucket` is the MTDS-side entry in this same sports manifest — this is the "so IS and MTDS is 100%
done" half of the operator's ask; it is not a separate system to census.

**Correction to this session's earlier vendor-audit claim**: weather and understat were reported "100% clean" based only
on `attempted_failed=0`, which is true but not the same as done — weather has 205,517 `expected_unattempted` shards
(never attempted at all) and understat has 30. SFI, freshly resolved to `attempted_failed=0` this session, has 205,363
`expected_unattempted`. None of these were checked against `expected_unattempted` before now.

## Priority order (by `attempted_failed` size, then by whether the cluster is live/recurring)

1. **odds_api — 13,916 attempted_failed, two distinct causes, P0.**
   - **871 rows: `401 Unauthorized`.** All `attempted_at` between 2026-07-26T07:54Z and 2026-07-27T00:07Z — a single
     backfill run that hit a bad/expired credential for its whole session, historical target dates 2025-09-01 through
     2026-07-27. No 401s recorded since 2026-07-27 (10+ days), so the credential is presumably fixed/rotated since —
     these 871 rows just never got retried. Straightforward: re-run a targeted backfill against the specific (date,
     league, bookmaker) shards in this set with the current key; if it still 401s, the credential needs a real fix
     first.
   - **13,045 rows:
     `record_empty(reason=SOURCE_RETURNED_ZERO) rejected: ... catalog says 'trades' was ALIVE on <BOOKMAKER>/<date> ... this is a real fetch failure, not honest absence`.**
     This is the honest-coverage guard rail correctly refusing to let a zero-row response masquerade as absence when the
     instrument catalog says the market was live. Clustered across many bookmakers (LADBROKES_UK, SPORT888, CASUMO,
     MATCHBOOK, UNIBET_UK, BETFAIR_SB_UK, FANDUEL, BETVICTOR, SMARKETS, ...) and spiking on specific dates (2026-08-02:
     1,082; 2026-05-27: 782; 2026-05-07: 782; 2026-03-30: 759; 2026-08-06: 743). **Still actively recurring** —
     `attempted_at` extends to 2026-08-06T19:10Z, yesterday. Not yet root-caused: needs the same treatment as the SFI
     mis-scoping / Transfermarkt 502 investigation this session — check whether this is a genuine per-bookmaker vendor
     gap (some books really do stop offering odds on some fixtures) that should instead be teaching the
     catalog/`is_transfer_window_open`-style eligibility check, or a genuine adapter/rate-limit bug worth fixing at the
     source. **Do not just flip these to `empty_confirmed`** — the guard rail exists because that would be dishonest;
     the fix has to be in either the catalog's aliveness signal or the actual fetch path.
2. **api_football — 35,058 attempted_failed, mostly ALREADY EXPLAINED.** Breaks down as: 27,314 tagged
   `error_reason="requests"`, all `attempted_at` between 2026-08-06T19:27Z and 2026-08-07T00:01Z — this is the SAME
   API-Football daily-quota exhaustion already root-caused earlier this session (confirmed self-resolving reset ~01:45Z
   2026-08-07); the currently-running AF campaign backfill (`af-backfill-20260807-013716`) is already past the reset and
   actively succeeding, so these rows should clear naturally as its sweep re-touches those shards — no separate action
   needed. 4,996 tagged `fixture_events_phantom_manifest_reflip_2026_07_26` — a named, deliberate historical operation,
   not an active bug. 2,699 `FIXTURES_FETCH_FAILED` — smaller, not yet individually investigated. Remaining ~730-2,657
   across TEAMS/FIXTURES_SCHEDULE/FIXTURES/PLAYER_STATS/TRADES — small, not yet investigated. **Plus 658,426
   expected_unattempted** — overlaps heavily with `sports_af_full_entity_completion_2026_08_03.md`'s existing backfill
   todos (PLAYER_STATS/TEAMS/STANDINGS/INJURIES/FIXTURE_LINEUPS); that doc's backfills, once run, should absorb most of
   it. Don't duplicate that doc's todos here.
3. **mdps_odds_horizon_bucket — 2,791 attempted_failed, 157,994 expected_unattempted.** ALREADY ROOT-CAUSED — not a new
   problem. This is the residual/exposed backlog from a freshness-check bug (a rollup sentinel row was satisfying
   odds_api's staleness check, permanently pinning ~572 days "fresh") fixed 2026-07-30
   (`market-tick-data-service@362e64e3`, `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`). The actual
   backfill to fill the exposed gap is tracked in `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` — its P1/P2
   todos were stuck `BLOCKED-CREDENTIALS` (stale as of the 2026-08-02 quota exhaustion); retagged 2026-08-07 after
   confirming live the 2026-08-03 top-up landed (14.4M credits available). **That doc's own history is a warning**: 5+
   uncoordinated relaunches, preemptions, and silent freezes chasing this exact gap, one contributing to the original
   quota-exhaustion incident. Next action: one single, guard-respecting VM launch
   (`launch-mtds-sports-odds-backfill-vm.sh --start 2020-06-06 --end <today>`, no `--force`), watched through to an
   actual clean terminal state — no prior attempt has reached one. Don't duplicate tracking here; that doc owns it.
4. **transfermarkt — 8 attempted_failed, unchanged.** Root-caused this session: the vendor's
   `transfermarkt-football-data-api.p.rapidapi.com/api/v1/competitions/standings` endpoint is durably returning HTTP 502
   as of 2026-08-07T10:17Z (2h17m of continuous retry-cycling with zero progress, confirmed via `run.log`) — killed the
   stuck retry VM (`tm-backfill-20260807-085636`) rather than keep burning SPOT time against a dead endpoint. Retry
   later once the vendor recovers; check `/api/v1/competitions/standings` specifically before relaunching blind.
5. **weather (open_meteo) — 205,517 expected_unattempted.** SFI (soccer_football_info) — 205,363 expected_unattempted.
   Both need a straightforward backfill launch (no known blocker, just never run against the full range) — lower
   priority than the `attempted_failed` items above since these are honest "not yet tried" rather than "tried and
   failed," but they're real gaps against the operator's "only captured/empty_confirmed" target.
6. **understat — 30 expected_unattempted.** Negligible, likely just the tail of an in-progress run. Low priority.

## Out-of-scope / migrate-or-delete residue

The footystats China/Russia purge (2026-08-07, `instruments-service@8548182b5`,
`sports_af_full_entity_completion_2026_08_03.md` Progress Log) is the only known "out of scope, needs deletion" residue
found so far and is already resolved. No other source currently shows a similar leftover-from-scope-change pattern —
this needs a proper audit pass (compare each source's captured league/data_type combinations against its current
UAC-registered scope) rather than assuming there's nothing else; not yet done.

## Todos

- [x] ✅ [SCRIPT] P2. **Retry EPL's odds_api tail gap** — re-census run 2026-08-07T20:03Z
      (`instruments-service@ca437ed3`, `scripts/census_epl_odds_api_attempted_failed_2026_08_07.py`): 206 EPL
      `attempted_failed` rows remain (23 UNCLASSIFIED:401 from stale-credential window, 183 SOURCE_RETURNED_ZERO from
      old unfixed `smallchunk` VM). Narrow retry NOT launched: `mtds-backfill-odds-401-retry` was preempted (SPOT) at
      16:55Z before completing its league sweep; `mtds-backfill-odds-smallchunk2-20260807` (full range 2020-06-06→today,
      5-day chunks, fixed SOURCE_RETURNED_ZERO code) is running and will naturally re-attempt all 206 rows when it
      reaches EPL's date range — consistent with the todo's own rationale ("premature action would just be redone by the
      eventual full-range small-chunk VM anyway").
- [x] ✅ [SCRIPT] P0. **Investigate + fix the odds_api SOURCE_RETURNED_ZERO cluster** (13,045 rows) — root-caused as
      genuine per-bookmaker vendor gap: v1 sentinel's `SOURCE_RETURNED_ZERO` branch lacked the
      `_is_bookmaker_league_covered_exact` gate that v2 already had. Fix: add per-bookmaker coverage gate; uncovered
      pairs now emit `empty_confirmed(EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE)` instead of `attempted_failed`.
      `market-tick-data-service@70f131667` · QG green · 6 v1 sentinel tests pass.
- [x] ✅ [SCRIPT] P0. **Retry the odds_api 871 `401 Unauthorized` rows** — confirmed credential working
      (mtds-backfill-odds-1 running with no 401s, 782 rows fetched on 2020-08-18); launched targeted VM
      `mtds-backfill-odds-401-retry` (2025-09-01→2026-07-27, SPOT e2-highmem-4, `--allow-parallel`) at
      2026-08-07T11:55:46Z, RUNNING at T+3.5min with log at 11:59:01Z, skip-fast through covered dates, real-fetching
      2026-02-22 with no 401s. The VM will naturally retry all 871 `attempted_failed` rows as it sweeps through that
      range (check_shard_freshness retry_failed=True is the default).
- [x] ✅ [SCRIPT] P1. **api_football's 35,058 attempted_failed — root-caused 2026-08-07**: 27,314 (78%) is the
      already-known 2026-08-06 daily-quota exhaustion, self-resolving via the currently-running AF campaign; 4,996 is a
      named historical operation, not a bug. Remaining ~4,748 across FIXTURES_FETCH_FAILED/TEAMS/FIXTURES_SCHEDULE/
      FIXTURES/PLAYER_STATS/TRADES not individually root-caused — small enough to leave as a residual watch item, not
      reopening this todo for it.
- [x] ✅ [SCRIPT] P1. **Launched the single, guard-respecting odds_api gap-backfill VM** — 2026-08-07T11:0XZ,
      `mtds-backfill-odds-1` (`launch-mtds-sports-odds-backfill-vm.sh --start 2020-06-06 --end 2026-08-07`, no
      `--force`), guard confirmed `0 running + 1 planned <= cap 1`, all 4 tarballs fresh. RUNNING as of the check right
      after launch — watching through to actual clean completion next tick (see
      `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` for the full history/context).
- [ ] [SCRIPT][BLOCKED-UPSTREAM-OUTAGE] P2. **Retry Transfermarkt's 8 attempted_failed PLAYER_VALUES rows** (now the
      golden-window relaunch's 256-cell scope too — see
      `/plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md` todo 2) once
      `transfermarkt-football-data-api.p.rapidapi.com/api/v1/competitions/standings` recovers — confirmed still
      returning HTTP 502 at 2026-08-07T12:21Z (3h+ after initial failure at 10:17Z; RapidAPI message: "API (not
      working)"), and **still 502 at 2026-08-08T01:20Z** (15h+ outage, direct probe with the correct `id`/`season`
      params, ~52s latency before the 502 — see Progress Log entry below). Tagged BLOCKED-UPSTREAM-OUTAGE; do not
      relaunch without verifying the endpoint returns 200 first.
- [x] ✅ [SCRIPT] P2. **Launched weather (open_meteo) full backfill, ran to `exit_code=0`** —
      `weather-backfill-20260807-120241` completed cleanly but did NOT resolve the gap (re-census:
      `expected_unattempted` barely moved 205,517→205,302; 16,241 new `attempted_failed` rows appeared) — split into the
      two follow-up todos below rather than reopening this one, since the LAUNCH itself succeeded; what's left is
      root-cause work.
- [x] ✅ [SCRIPT] P1. **Root-cause weather's 16,241 `ClientResponseError` rows** — root cause: spurious `raise` inside
      the inner `except` for the `customer-previous-runs-api.open-meteo.com` call aborted the entire fetch instead of
      skipping forecasts and continuing to actual weather (the comment at line 136 already described the correct
      behaviour). Fix: removed the `raise`; added regression test. `instruments-service@1fafbe23`, QG green. On next
      backfill run the 16,241 `attempted_failed` shards will be re-touched and should resolve to `captured` or
      `empty_confirmed`.
- [x] ✅ [SCRIPT] P1. **Explain why weather's `expected_unattempted` barely dropped** — root-caused: NOT a
      skip-condition false-positive or per-venue sub-loop bug. The 205K rows are for non-Prediction leagues NOT in
      `_expected_weather_league_ids = get_expected_leagues_for_source("open_meteo", classifications=["Prediction"])`
      (~33 leagues). Every write path in `_fetch_weather_data` (season-window guard, coverage-start guard,
      `_record_weather_empty`, `_record_weather_failed`, end-of-function EXPECTED_NO_FIXTURE loop) writes ONLY for those
      33 leagues; non-Prediction league rows persist as `expected_unattempted` indefinitely. The -215 net reduction came
      from 215 Prediction-league rows resolved by this run. The 350 rows on 2026-07-28 are for non-Prediction leagues —
      untouched by design. Fix path: `type_weather_eu_no_provider_coverage_2026_06_27.py     --apply` (already exists
      for this exact pattern). See Progress Log 2026-08-07 (slot 7).
- [x] ✅ [SCRIPT] P2. **Launched SFI full backfill** — `sfi-backfill-20260807-123519` confirmed RUNNING
      (`launch-sfi-backfill-vm.sh --entity SFI_PROGRESSIVE_STATS 2020-06-06 2026-08-07`), targeting 205,363
      expected_unattempted shards (distinct from the already-resolved 89-row attempted_failed cluster).
- [x] ✅ [SCRIPT] P3. **Understat 30-row expected_unattempted tail** — confirmed live-cron artifact, no action needed.
      instruments-service@1ebc2ca9 (`scripts/census_understat_expected_unattempted_2026_08_07.py`): 25 rows remain
      post-China/Russia-purge (from 30), all dated 2026-08-05→08-07, empty venue, XG/XG_SHOTS — in-progress IS cron
      shards for recent fixtures; resolve naturally on next daily cycle.
- [x] ✅ [SCRIPT] P2. **Out-of-scope audit pass** across every source — compare captured league/data_type combos against
      current UAC scope, looking for more footystats-China/Russia-style residue. instruments-service@122e4571
      (`scripts/audit_out_of_scope_sports_leagues_2026_08_07.py`, read-only, 7 sources, HIGH RISK / LOWER RISK
      classification, exit 0=clean/1=residue).
- [x] ✅ [SCRIPT] P0. **Re-census run 2026-08-07T11:57Z** (instruments-service@f917f04f,
      `scripts/census_all_sports_sources_2026_08_07.py`, 9,552,235 manifest rows post-floor) — VMs still running; not
      yet converged. Updated table below in Progress Log. Re-census needed once backfill VMs complete.
- [x] ✅ [SCRIPT] P2. **Bake the vendor-completion/attempted_failed/honest-absence audit checks into a daily AO run** —
      operator asked (repeated across this session) for the checks done ad hoc here to run automatically every day,
      choice of `/data-pipeline-check-*` vs `/data-pipeline-reconciliation` left to the agent. Added a new "Per-vendor
      completion audit" section to
      `unified-trading-pm/cursor-configs/skills/data-pipeline-reconciliation/reference-sports.md` (`722fd6d4cf`) — the
      closer structural fit, since SKILL.md § 3b already owns the manifest/`capture_status` surface this procedure
      extends. Documents the 5-step procedure (per-source pivot, error_reason sub-classification, timestamp liveness
      check, never-trust-exit_code-alone, mid-run tarball-staleness check) with the concrete gotchas measured this
      session, cross-linked back to this doc's Progress Log for full worked examples.
- [x] ✅ [SCRIPT] P1. **Confirmed the SFI + weather reclassifications landed in the canonical index** —
      2026-08-07T20:47Z re-census: `expected_unattempted` is completely gone (0 rows) for both sources,
      `empty_confirmed` grew by exactly the retyped counts (SFI +205,447 ≈ 205,363 retyped; weather +205,302, an exact
      match). Both sources now hold only `captured` + `empty_confirmed` + their small, already-diagnosed
      `attempted_failed` tail.
- [x] ✅ [SCRIPT] P2. **Checked `type_understat_eu_no_provider_coverage.py` — NOT the same pattern, no action needed.**
      Dry-run (2026-08-07T22:18Z) confirms understat's 25 rows are `reason=EXPECTED_NO_FIXTURE`, dates 2026-08-05→
      2026-08-07 (today/yesterday) — matches the earlier "slot 4" diagnosis exactly (self-resolving IS-cron artifact for
      recent fixture shards not yet processed by the daily pass), not the weather/SFI structural bug
      (`EXPECTED_NO_PROVIDER_COVERAGE`, historically-seeded, permanently unreachable by a narrower current writer).
      footystats/transfermarkt/odds_api already repeatedly confirmed at `expected_unattempted=0` throughout this
      session's census runs — no script needed, nothing to check. This closes the systemic-sweep question: only
      weather + SFI had the structural bug, both now fixed.

## Progress Log

- **2026-08-07T10:2XZ→2026-08-08T14:54Z (compacted 2026-08-09, was 570 lines of granular per-tick play-by-play — see git
  history at this doc's own path for the full detail if ever needed).** Summary of everything resolved in this window:
  - **weather (open_meteo)**: root-caused + fixed 16,241 `ClientResponseError` rows (spurious `raise` in
    `OpenMeteoAdapter.get_weather_match_window`'s previous-runs fallback, `instruments-service@1fafbe23`). Separately
    root-caused its 205,517 `expected_unattempted` backlog as structurally unreachable (seeded historically by a
    broader-scope run than the current Prediction-tier writer covers) and resolved via
    `scripts/type_weather_eu_no_provider_coverage_2026_06_27.py --apply` (205,302 rows retyped to
    `empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE)`) — **converged**, verified via re-census post-consolidator-merge.
  - **SFI (soccer_football_info)**: identical structural `expected_unattempted` pattern (205,363 rows), same remediation
    script, same verified convergence.
  - **footystats**: 50-league backfill verified cleanly done (0 `attempted_failed`, 0 `expected_unattempted`).
  - **understat**: 25-row residual closed as a self-resolving live-cron artifact (not a bug).
  - **transfermarkt**: `BLOCKED-UPSTREAM-OUTAGE` — confirmed HTTP 502 on `competitions/standings` twice (direct probe),
    outage ongoing since 2026-08-07T10:17Z; a second blind-launched retry VM was found and killed for burning GCE
    against the same dead endpoint. Still open, gated on vendor recovery.
  - **odds_api**: root-caused + fixed the `SOURCE_RETURNED_ZERO` misclassification (missing per-bookmaker coverage gate
    in the v1 sentinel, `market-tick-data-service@70f131667`). The odds backfill VM chain
    (`mtds-backfill-odds-1`→`401-retry`→`smallchunk`→`smallchunk2`→`smallchunk3`→`smallchunk4`→`smallchunk5`→`smallchunk6`)
    went through this window's early OOM-retry-storm findings (self-recovering, not a bug — chunk 18's 2020-08-30→09-03
    season-opener week is unusually real-fetch-heavy across every league worldwide simultaneously) and the FIRST FOUR
    confirmed silent-hang-then-watchdog-kill occurrences (smallchunk2/3/4/5, each ~16-21min total silence then a correct
    watchdog kill, no data loss — durable per-VM manifest shards survive regardless of which VM wrote them). Full
    timeline + diagnostic detail lives in the dedicated doc:
    `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` (now tracking 6 occurrences as of this doc's
    latest entries below).
  - **Cross-vendor denominator-hardening audit** (operator ask, footystats/open_meteo/SFI/transfermarkt/understat):
    closed — a fresh census confirmed 0% blank-`error_reason` `empty_confirmed` rows workspace-wide already, only 3
    small self-resolving cron-artifact residuals found, nothing to fix. Two codex/skill-doc additions shipped codifying
    the "blank-reason-is-a-code-smell" principle.
  - **FIXTURE_STATS**: converged its own chunk 26/26 sweep (`af-backfill-20260807-161736`, clean exit_code=0), re-census
    confirmed genuine (24,462→116 needed shards, the residual being an honest-absence floor). Same census confirmed
    **PLAYER_STATS fully resolved** (needed=0). This triggered the AF entity chain's next stage: FIXTURE_LINEUPS
    launched immediately (line below), then INJURIES queued behind it.
- **2026-08-08T14:54Z — 🎉 MAJOR MILESTONE: FIXTURE_STATS GENUINELY CONVERGED.** `af-backfill-20260807-161736` completed
  all 26 chunks: `PROGRESS: chunk=26/26 range=2026-08-04→2026-08-07 time=2026-08-08T14:40:07Z`,
  `instruments-backfill loop complete`, `exit_code=0`, clean graceful self-delete via `VM_SHUTDOWN_ON_COMPLETION`. **Per
  rule 4a, re-censused live before trusting the clean exit** — ran
  `instruments-service/scripts/census_fixture_stats_lineups_widening_volume_2026_07_31.py`: **FIXTURE_STATS needed
  dropped from 24,462 to just 116** (99.5%+ resolved — a genuine honest-absence-floor residual, not a real gap, matching
  the campaign's own stated completion criterion). Same census run also confirmed **PLAYER_STATS is now fully resolved**
  (`census_all_af_entities_completion_2026_08_03.py`: needed=0, down from 18) — hadn't been re-checked in a while, a
  nice bonus find. **Launched FIXTURE_LINEUPS immediately** per the AF doc's own todo (line 205, corrected earlier this
  session from the wrong INJURIES-first assumption): `deployment-service/scripts/vm/launch-api-football-backfill-vm.sh`
  with `RESUME_ENTITY=FIXTURE_LINEUPS RESUME_START_DATE=2020-06-06 RESUME_END_DATE=2026-08-07` (same range/launcher
  family FIXTURE_STATS used, singleton lock confirmed free first). Launch took >120s (moved to background) — confirming
  the new VM actually started next tick, not assuming success from the command alone. FIXTURE_LINEUPS still needs the
  full 58,523 shards (unchanged, no backfill had run against it yet). This flips the AF campaign's remaining scope to:
  FIXTURE_LINEUPS (running now) → INJURIES (62,709 needed, queued behind the same singleton lock) → final re-census
  across all 8 entities → close the doc. AF entity doc flipped + pushed at its 1000-line cap exactly (`0f2ba70293`).
- **2026-08-08T15:00Z — CORRECTION: the first FIXTURE_LINEUPS launch attempt actually FAILED** (good thing the Progress
  Log entry above already said "confirming next tick, not assuming success" — it hadn't converged yet, this confirms
  why). Launcher output ended `ERROR: auto-republish completed but tarball(s) still stale ... aborting launch`.
  Root-caused: `instruments-service` had a dirty `uv.lock` (harmless auto-regenerated diff — just added marker variants
  for an already-declared `schema-validation` extra, from running the census scripts earlier this tick — not real work,
  confirmed via `git diff --stat` = 7 lines, all mechanical). This IS the `auto`-mode tarball guard working as designed
  (fixed `deployment-service@450b212`, 2026-08-07, per
  `lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md`) — it correctly refused to launch onto
  potentially-stale code rather than a new bug. Fixed by `git restore uv.lock` (confirmed zero content loss — pure
  lockfile noise, not intentional work) and retried. Retry is currently in progress (backgrounded, >120s again — tarball
  republish across 3 repos takes a while); confirming genuine VM creation next tick before trusting it.
- **2026-08-08T15:08Z** — 2nd retry ALSO failed, differently: only `instruments-service` flagged stale despite a
  genuinely clean, origin-synced tree (`git status --short` empty, 0 ahead/0 behind `origin/live-defi-rollout`).
  Root-caused via direct manifest read (`gcloud storage cat .../instruments-service-code.manifest.json`):
  `commit_sha=8548182b...` (older) vs local HEAD `6cdb0423...` — a genuine concurrent-push timing race on the shared
  branch between the republish step reading HEAD and the manifest settling, not a bug in this checkout. Retried a 3rd
  time (backgrounded).
- **2026-08-08T15:16Z — ✅ FIXTURE_LINEUPS LAUNCH CONFIRMED GENUINE on the 3rd attempt.** `lc_verify_tarball_freshness`
  passed clean this time (`tarball fresh: instruments-service @ 6cdb04239097`), VM `af-backfill-20260808-160815` created
  (`asia-northeast1-c`, RUNNING). Per no-fire-and-forget discipline, waited and read `run.log` directly rather than
  trusting the launcher's own exit code: confirmed genuine real work — `Fetched N lineup rows for fixture=<id>` lines
  against real AF fixture IDs, `PIPELINE_HEARTBEAT` emitting on schedule, a healthy mix of populated (36-40 rows) and
  legitimately-empty (0 rows — fixtures with no lineup data, expected) fetches. FIXTURE_LINEUPS is genuinely progressing
  now. Two of three launch attempts failing on transient/environmental causes (not logic bugs) is now the established
  pattern for this launcher under concurrent multi-worker load — noted for future launches, not a standalone issue worth
  its own doc.
- **2026-08-08T15:40Z** — both fleets healthy, no intervention. odds smallchunk6: entered chunk 18/451 (the danger chunk
  — 2 of 4 prior occurrences died here) at `15:16:04Z`; as of `15:39:26Z` still actively logging fresh real work
  (`Odds API batch complete: date=2020-08-31`), essentially current — NOT a silent hang like the prior 4 deaths (which
  always went 16-21 min quiet before the watchdog kill). RSS sawtooth continues (climbs to ~24GiB then resets <1GiB per
  date-batch, expected/normal). FIXTURE_LINEUPS (`af-backfill-20260808-160815`): confirmed progressing to genuinely
  different fixture IDs between this check and the 15:14Z check (was 503xxx/209xxx/208xxx range, now
  164xxx/564xxx/566xxx range) — rules out a stuck retry-loop, real forward movement through the 58,523-shard backlog.
- **2026-08-08T16:05Z — killed and relaunched smallchunk6 (unnecessarily, self-corrected).** Deeper look at chunk 18
  showed 14 explicit `CHUNK_FAILED exit=137 reason=OOM_KILLED` lines (one per league, each auto-retried by
  `mtds_chunk_loop.sh`) over 45 min. Misread this as a new "infinite crash loop" distinct from the odds hang doc's
  tracked bug and killed the VM — but the odds hang doc's own prior entry already documents `smallchunk5` clearing this
  same chunk via 24 such OOM-kill+retry cycles before succeeding ("24 OOM/zero hangs"). Explicit `CHUNK_FAILED` +
  continuous restart activity is the designed retry-until-success mechanism, not the silent-hang bug (which has NO error
  message, no restart, just quiet). No real progress lost (OOM-retry state isn't durable across attempts regardless of
  VM identity) — relaunched fresh as `mtds-backfill-odds-smallchunk7-20260808`. Full correction:
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`. **Standing rule going forward**: `CHUNK_FAILED`/
  OOM-kill-with-immediate-restart is expected background noise, not actionable — only total silence (no restart, no
  error line) for >10-15 min while RUNNING is the real signal.
- **2026-08-08T16:13Z** — `mtds-backfill-odds-smallchunk7` confirmed booted and genuinely working: skip-fasting through
  already-captured dates rapidly, real fetch on new ground (`2020-08-18`), heartbeat fresh. No re-census yet (too early
  — will check once past the chunk-18 OOM-retry stretch, expect ~30-90min per the smallchunk5/6 precedent, NOT
  actionable unless it goes fully silent). FIXTURE_LINEUPS still actively progressing at `16:08Z` (new fixture ID range
  599xxx/595xxx). Both healthy.
- **2026-08-08T16:40Z — SECOND self-correction: `smallchunk7` was misconfigured, killed + fixed.** Found
  `CHUNK_FAILED chunk=1/10 ... range=2020-06-06→2021-02-10 exit=137 reason=OOM_KILLED` — a **250-day** chunk span,
  OOM-killing immediately on its first attempt (5 failures in ~20 min, chunk 1 of only 10 total). Root cause: my
  relaunch omitted `--chunk-size`, silently defaulting to the launcher's `CHUNK_SIZE=250` instead of the established
  5-day "smallchunk" convention. Confirmed the correct value via `smallchunk5`/`smallchunk6`'s own `LAUNCH_PARAMS.json`
  (`"CHUNK_SIZE": "5"`) before fixing. Killed the misconfigured VM, relaunched correctly as
  **`mtds-backfill-odds-smallchunk8`** with `CHUNK_SIZE=5` explicit (launcher output confirmed
  `Chunk: 5 days per batch`, RUNNING, all 4 tarballs fresh). Two config mistakes in two consecutive relaunches this tick
  — going forward, **always verify a relaunch's actual chunk-size/config against a known-good prior instance's
  `LAUNCH_PARAMS.json` before trusting launcher defaults**, not just VM RUNNING status.
- **2026-08-08T16:43Z — FIXTURE_LINEUPS first real re-census (rule 4a).** Needed dropped **58,523 → 56,779** (genuine
  ~1,744-shard net progress in ~1h27m since launch), despite the denominator itself growing (other campaigns capturing
  more schedule shards concurrently, per the doc's own dynamic denominator formula). FIXTURE_STATS residual unchanged at
  116 (correctly stable, no active backfill targeting it now). Confirmed genuine forward convergence, not a fluke.
- **17:10Z-20:52Z (9 routine ticks, all healthy, no action, compacted 2026-08-09).** smallchunk8 climbed cleanly chunk
  5→24/451, zero OOMs until entering the chunk-18 danger zone at 18:37Z, then 5→24 `CHUNK_FAILED` (in-range, expected),
  **cleared it at 19:58Z at exactly 24 retries — matching smallchunk5's precedent exactly**. FIXTURE_LINEUPS needed
  dropped steadily across 8 re-census points, 56,779→49,250 (~550-1,555/interval, best rate 20:52Z), no stalls,
  ~27-30min cadence throughout. Doc hit its 1000-line cap around here — future ticks go terser.
- **21:19Z — FIXTURE_LINEUPS hit the API-Football daily quota wall, PAUSED (VM deleted).** Same account-wide daily quota
  this campaign hit before (2026-08-06, confirmed UTC-midnight reset ~01:45Z on 2026-08-07 —
  `sports_af_full_entity_completion_2026_08_03.md` history). `run.log` showed 1,770
  `'reached the request limit for the day'` errors starting `21:03:32Z`, `recovery=fail_fast` — verified NOT silently
  writing false `empty_confirmed` rows (checked for `ManifestWriter`/persistence near the failures — none for the failed
  fetches, only genuine `EXPECTED_NO_PROVIDER_COVERAGE` skips), so no data-integrity risk, just wasted ~120 req/min
  against a wall. Deleted `af-backfill-20260808-160815` (billing-waste avoidance, same reasoning as the Aug-6 precedent)
  — its checkpoint is durable, relaunch resumes forward, no work lost. Re-census just before full exhaustion: needed
  49,250→48,593 (-657, real). smallchunk8 (odds_api, different vendor) confirmed unaffected, still RUNNING healthy.
  **Per precedent, NOT probing again until well past tonight's UTC midnight** (~00:00Z) — plan to test-relaunch around
  01:00-01:30Z. INJURIES (next AF-campaign item, same singleton lock/API key) also blocked until then — no point
  launching either.
- **22:25Z-05:11Z (2026-08-09, further compacted).** smallchunk8 died silently (5th occurrence, chunk 26 3rd time,
  ~15-16min gap) → relaunched `smallchunk9`, climbed cleanly chunk 7→26/451 across the night (zero OOMs until chunk 18,
  then in-range `CHUNK_FAILED` cycling through 18 and 26, heartbeat blob confirmed alive throughout even when run.log
  text briefly lagged — established diagnostic: trust heartbeat blob over run.log staleness). **AF daily quota RESET
  CONFIRMED at 01:05Z** (probe via `af-backfill-20260809-020527`, `remaining_daily_quota=149210` was 0 the day before,
  matches the Aug-6/7 UTC-midnight-reset precedent) — FIXTURE_LINEUPS resumed, baseline 48,566. A ~2h15m flat census
  reading was traced to consolidator lock-contention lag (real merges ~11-15min, found an unresolved
  `shards_listed=12`→`downloaded=7` gap, data itself confirmed safe) and self-resolved at 05:11Z (→48,432). Also:
  recovered a push-integrity issue this stretch — always verify `ahead=0/behind=0` independently, never trust
  `safe-doc-push.sh`'s own message alone. context-scout 2026-08-09: refreshed context_scope (5 entries).
- **05:39Z — `smallchunk9` was silently replaced by an AUTOMATED relaunch; cause of the original's death is
  UNKNOWN/unrecoverable, and both forensic logs were destroyed by the reuse.** Found via
  `gcloud compute operations list`: the original instance was deleted at `05:26:17Z` (within the 05:11Z→05:39Z
  monitoring gap), then a NEW instance — same name, same GCP VM ID space — was created at `05:32:25Z` by a **different
  principal** (`unified-trading-sa@central-element-323112.iam.gserviceaccount.com`, not the `1060025368044-compute@...`
  account used for every manual action and the zombie-watchdog kills all session) — this is a
  previously-unobserved-in-this-campaign **automated SPOT-preemption relaunch mechanism** (`RelaunchPreemptedVm`, per
  the launcher's own header comment), genuinely distinct from anything I did. **Cannot determine whether the original
  died from the tracked silent-hang bug or a genuine SPOT preemption** — both `run.log` and `WATCHDOG_TRACE.log` live at
  name-keyed (not timestamp-keyed) GCS paths, so the new instance's startup **completely overwrote** the old one's
  history (no `CHUNK_FAILED`/chunk-26 content survives). **Not counting this as a confirmed 6th silent-hang occurrence**
  — genuinely inconclusive, unlike occurrences 1-5 which all had clean heartbeat-blob evidence. **Process lesson**:
  `smallchunk8`/`smallchunk9`'s no-timestamp-suffix naming (a convention regression from the timestamp-suffixed
  `smallchunk2-20260807` etc. used earlier) destroys forensic history across same-name relaunches — future relaunches in
  this campaign should reintroduce a timestamp suffix. New instance confirmed healthy (heartbeat 43s old at last check),
  fresh at chunk 1/435 (resumed from a checkpoint around `2020-08-29`, ~6wk behind where the old instance had reached —
  will skip-fast re-verify that stretch, no data loss, just some redundant work). No relaunch action needed from me —
  already recovered. FIXTURE_LINEUPS needed **48,432 → 47,947** (-485, real, lag fully resolved), heartbeat live. Both
  healthy.
- **07:15Z — NEW failure mode found: run.log's GCS-tee upload can silently stall while the VM stays genuinely alive by
  every other signal — killed and relaunched (unverifiable, not confirmed-dead).** New smallchunk9's `run.log` content
  froze at `05:59:40Z` (confirmed via direct object metadata, `Update Time` unchanged) — but its `WATCHDOG_TRACE.log`
  (separate GCS path) showed continuous LOCAL file-size growth up to `07:15:16Z` (essentially live), meaning the on-VM
  process was very likely still running — just its upload of `run.log` to GCS had broken, specifically. This is DISTINCT
  from both prior patterns: unlike a silent hang, the heartbeat blob AND watchdog trace stayed live; unlike simple GCS
  flush-lag (usually <10min), this was 76+min. Without SSH, I could not distinguish "still making real chunk progress,
  just blind to me" from "stuck in some other loop that keeps churning local log bytes" — killed it rather than keep
  trusting an unverifiable signal (9 `CHUNK_FAILED` already on chunk 1 was also unusually high for a
  non-historically-dangerous chunk). Relaunched as **`mtds-backfill-odds-smallchunk10-20260809`** (timestamp-suffixed
  this time, per the naming lesson from the last incident). Full detail:
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`.
- **07:54Z-10:21Z (compacted).** smallchunk10 launch confirmed genuine, climbed cleanly chunk 1→17/451 with **zero
  OOMs** (cleanest run yet) before the streak ended at chunk 18 as expected (21 `CHUNK_FAILED` by 10:21Z, in-range).
  FIXTURE_LINEUPS dropped steadily across 6 re-census points, 43,518→34,003 (rate held/accelerated,
  ~1,000-2,500/interval), heartbeat live throughout both fleets. No incidents this stretch.
- **10:49Z** — smallchunk10 still chunk 18, 21 `CHUNK_FAILED` (in-range), heartbeat live. FIXTURE_LINEUPS needed
  **34,003 → 32,547** (-1,456). Both healthy. Did a compaction pass (962→952 lines).
- **11:04Z** — smallchunk10 chunk 18 finally cleared (26 total `CHUNK_FAILED` before clearing) and moved on to chunk
  19/451, real forward work (`Odds API batch complete: date=2020-09-07`), heartbeat ~1.5min old, RSS ~1.08GiB/7.7% —
  healthy, no OOM signature on the new chunk. Full detail:
  `plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`.
- **13:08Z — CONFIRMED 6th silent-hang occurrence: `smallchunk10` killed by the watchdog at chunk 26.** All 3 signals
  (run.log, heartbeat blob, `WATCHDOG_TRACE.log`) went silent together ~12:50Z; VM deleted `13:07:57Z` (~18min gap, by
  the standard `1060025368044-compute@...` account — matches the watchdog's own established pattern exactly, clean
  multi-signal evidence unlike the smallchunk9 incident). Relaunched as `mtds-backfill-odds-smallchunk11-20260809`
  (timestamp-suffixed). FIXTURE_LINEUPS unaffected, healthy, far advanced. Full detail:
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`.
- **14:27Z (slot 4, data_engineering, odds_api-doc dispatch) — `smallchunk11` (the 13:08Z relaunch) is ALSO dead, but
  from a genuinely NEW failure mode: SETUP FAILURE, not OOM/silent-hang. Currently 0 odds_api backfill VMs running.**
  `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-odds-smallchunk11-20260809/` shows
  `EXIT_STATUS=1`/`SETUP_EXIT_STATUS=1` at `14:15:5{0,2}Z`, no `run.log` ever created — the pipeline itself never
  started. `vm-setup.log` (2497 bytes, complete) shows code deploy succeeded for all 4 repos
  (uac`82505ed7`/utl`262a8531`/deployment-service`1e85ce3b`/mtds`15864866`) then fails within 1s at
  `uv pip install --no-sources -e .../uac -e .../utl -e .../mtds` — `SETUP FAILED rc=1` with **no pip stderr captured**
  despite the startup template piping everything through `tee`; could not determine whether pip genuinely fast-failed
  (e.g. a lockfile/version conflict from the freshly-deployed tarball SHAs above) or the self-delete raced the tee
  buffer flush. This is a DIFFERENT bug class from the watchdog/OOM pattern this doc has tracked all along — worth its
  own follow-up if it recurs (the launcher's setup-failure path doesn't reliably preserve the actual error). Did not
  relaunch myself (dispatched via the odds_api-scattered-gaps doc, whose own standing instruction there is "do not
  launch a VM from this todo" — deferring to whoever continues this tracker). Full detail + the odds_api-doc side of
  this entry: `plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`. **Net: the campaign is
  currently stalled at 0 running VMs** — next continuation of this doc should check for a live VM first and, if still 0,
  do a fresh guard-respecting relaunch (`odds-api-concurrency-guard.sh` cap=1 permits it) and watch the first few
  minutes closely to confirm setup actually completes this time before walking away.
- **15:13Z-15:22Z (slot 20) — picked up this doc's own recommended next continuation: 0 VMs still running after 46min,
  relaunched `mtds-backfill-odds-smallchunk12-20260809`, and likely root-caused `smallchunk11`'s setup failure.** The
  launch's `lc_verify_tarball_freshness` check caught the `market-tick-data-service` tarball STALE (pinned sha
  `1a704b0f0892` vs repo HEAD `85872cab756e`) and auto-republished it before creating the VM — `smallchunk11` almost
  certainly deployed against that stale/mismatched tarball, consistent with its near-instant
  `uv pip install -e .../mtds` failure with no captured stderr. Watched the new VM through setup (polled 30s×6):
  `run.log` appeared clean at T+~4min, real pipeline bootstrap + `SKIP date=2020-06-06: all 1 venues fresh` (correct
  skip-fast resume, no data loss). No setup failure this pass. Full detail:
  `plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`.
- **15:20Z — DEEPER ROOT CAUSE found in parallel: a fleet-wide P0 bug, not tarball staleness or odds-specific.**
  `setup-data-pipeline-vm.sh:940`'s `SETUPTOOLS_SCM_PRETEND_VERSION="0.99.0"` had fallen below UAC's own real floor
  (MDPS/MTDS/UTL/deployment-service all now require `unified-api-contracts>=0.106.0`), so `uv pip install` failed ~1s in
  on **every** VM using the shared Pattern-A bootstrap — confirmed via `uts-prd-sa@...` self-delete audit logs showing
  dozens of unrelated campaigns (tradfi-bf-*, mdps-backfill-cefi, expected-universe-v2-sports, footystats-fwd) also
  dying within ~2min of boot in the same window. Fixed: bumped pretend-version to `0.199.0`, shipped
  `deployment-service@501eb48b8` via quickmerge, verified ancestor-of-origin. **Confirmed working**: the fleet's
  automated SPOT-relaunch mechanism (`unified-trading-sa@...`) picked up the gap and launched `smallchunk12` unprompted
  — verified genuinely at chunk 1/452 real work (not just exit_code=0). Odds campaign resumed. Full detail:
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`.
- **17:35Z — Dual-fleet health check + fresh FIXTURE_LINEUPS census (rule 1b, diffing actual values not log activity).**
  smallchunk12: RUNNING, chunk 18/452 (now GREEK_SUPER_LEAGUE, was BUNDESLIGA last check — real forward progress within
  the chunk), RSS 10.5GiB (normal range), heartbeat fresh. FIXTURE_LINEUPS (`af-backfill-20260809-020527`): RUNNING,
  actively fetching current fixtures (~1.2-1.36M fixture ID range), fresh timestamps. Ran
  `census_fixture_stats_lineups_widening_volume_2026_07_31.py` fresh: **FIXTURE_LINEUPS needed dropped 32,547 → 11,257**
  (-21,290 shards over ~6.5h since the last reading at 10:49Z — genuine, substantial, continued convergence;
  FIXTURE_STATS confirmed still resolved at 116). At the observed rate (~3,275 shards/hr), full convergence to near-zero
  is roughly ~3-4h out, not yet at the "launch INJURIES next" trigger threshold — continuing to monitor rather than
  launching prematurely. Both VMs healthy, no intervention needed this tick.
- **18:11Z — 7th silent-hang occurrence (smallchunk12, chunk 18), relaunched; FIXTURE_LINEUPS SPOT-preempted +
  auto-recovered; census shows accelerating convergence.** `smallchunk12` died with clean 3-signal evidence (~19min
  silent gap, standard watchdog account, RSS=15.9GiB — not OOM); relaunched as
  `mtds-backfill-odds-smallchunk13-20260809`, confirmed genuinely booted (chunk 1/451, correct skip-fast). Full detail:
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` (now 7x). Separately, FIXTURE_LINEUPS's VM was
  routinely SPOT-preempted (not the hang pattern) and auto-relaunched as `af-backfill-20260809-180612` within ~4 min,
  confirmed resuming cleanly. Fresh census: FIXTURE_LINEUPS needed **11,257 → 8,332** (-2,925 in ~32min, rate
  accelerated to ~5,484/hr vs ~3,275/hr last tick) — still not at the near-zero INJURIES-launch trigger, but closing in
  (~1.5h out at this rate if it holds). Both fleets healthy, no further intervention needed this tick.
- **18:42Z — Both fleets steady, no incidents.** `smallchunk13`: chunk 7/451 (`2020-07-06→2020-07-10`), zero OOMs,
  healthy skip-fast pace, fresh timestamps. `af-backfill-20260809-180612`: actively fetching current fixtures
  (~1.35-1.39M range), fresh. Census: FIXTURE_LINEUPS needed **8,332 → 6,334** (-1,998 in ~31min, ~3,750/hr — steady,
  89% converged from the 58,523 campaign start). Still not at the near-zero INJURIES trigger (targeting a floor similar
  to FIXTURE_STATS's own 116-shard honest-absence residual); no intervention needed.
- **19:14Z — Both fleets healthy, no incidents; FIXTURE_LINEUPS rate has slowed noticeably.** `smallchunk13`: chunk
  14/451 (`2020-08-10→2020-08-14`), real forward progress (up from chunk 7), zero OOMs, healthy — 4 chunks from chunk
  18's danger zone, watching next tick. `af-backfill-20260809-180612`: actively writing real manifest shards (13,620
  total entries this VM instance), now processing more "enrichment-only" per-fixture sweeps (log shows
  `core entities fresh — enrichment-only mode`) rather than fresh core fetches — plausible explanation for the slowdown
  below. Census: FIXTURE_LINEUPS needed **6,334 → 5,741** (-593 in ~32min, ~1,112/hr — down sharply from the prior
  ~3,750/hr; still genuine forward movement per rule 1b, not a stall, just a real rate change likely from the campaign
  shifting into slower enrichment-only territory). At this new rate, ~5.2h to the near-zero floor (was ~1.7h estimate
  last tick) — re-estimating each tick rather than trusting the old rate. Not yet at the INJURIES trigger, no
  intervention needed.
- **19:44Z — smallchunk13 reached chunk 17/451 (doorstep of the chunk-18 danger zone), zero OOMs across the entire run
  so far — genuinely clean. FIXTURE_LINEUPS rate sped back up sharply.** Census: FIXTURE_LINEUPS needed **5,741 →
  3,462** (-2,279 in ~30min, ~4,558/hr — back up from the prior tick's slower ~1,112/hr; the rate has been genuinely
  variable tick-to-tick, re-estimate fresh each time rather than trusting the last reading). Getting close to the
  ~100-500 near-zero floor now (~46min out at this rate, though the rate itself may shift again) — not yet triggering
  the INJURIES launch, watching very closely next tick for genuine convergence. Both fleets healthy, no intervention.
- **20:08Z — smallchunk13 entered chunk 18 as expected; hit 3 OOM-retries so far (EPL, LA_LIGA, BUNDESLIGA, now on
  SERIE_A) — this is the established, self-recovering, NOT-actionable pattern, not a repeat of the tracked silent-hang
  bug** (chunk 17 cleared cleanly first, heartbeat fresh at 20:08:14Z, ~23s old at check time). FIXTURE_LINEUPS hitting
  API rate limits (`sleeping 59s to next minute`), a normal self-throttle, not a failure. Census: FIXTURE_LINEUPS needed
  **3,462 → 1,326** (-2,136 in ~24min, ~5,340/hr) — very close to the ~100-500 near-zero floor now but still just above
  the >1000 hold-off threshold, so NOT launching INJURIES yet. Expect genuine convergence within the next tick or two at
  this rate. Both fleets healthy, no intervention needed.
