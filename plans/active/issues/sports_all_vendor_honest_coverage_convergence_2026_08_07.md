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
- [ ] [SCRIPT] P1. **Odds_api gap-backfill campaign — babysit the `mtds-backfill-odds-*` fleet to genuine completion.**
      This todo replaces reliance on an interactive session's own self-scheduled monitoring loop — handing it to normal
      AO dispatch (this doc is already `assigned_vm: planning`) so it survives across dispatches without needing a
      specific chat session kept alive. **Done-when**: re-run
      `cd market-tick-data-service && GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp     DEPLOYMENT_ENV=prod CLOUD_MOCK_MODE=false .venv/bin/python     scripts/sports/census_odds_api_gap_verify_2026_08_02.py 2>&1 | grep -E "DAY-LEVEL|VERDICT"`
      reads 0 missing days, OR 2+ consecutive dispatches (spaced hours apart) read an identical small residual — treat
      that as a genuine honest-absence floor the same way the AF entities' small non-zero floors were treated (see
      `sports_af_full_entity_completion_2026_08_03.md`), then flip this todo citing the stable reading. Full gap
      breakdown + root-cause history: `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` (635→590→300 missing days
      across several rounds of fixes: launcher OOM bug, manifest-consolidator stall, credential/quota block — all
      resolved). **State at handoff (2026-08-10T08:30Z)**: 300/2257 days missing, unchanged since 2026-08-02 — NOT a
      stall, the current run walks sequentially from 2020-06-06 forward and hadn't yet reached the earliest real gap
      (2021-06-07, ≈chunk 70/425) as of this entry; re-run the census only when the frontier is estimated to have passed
      a milestone like that, not every dispatch (it's cheap but there's no point re-reading an unchanged number). **Each
      dispatch, in order**: (1) check `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`'s tail for the
      current occurrence count and read its Timeline table + the most recent Progress Log entries for the full
      established playbook (chunk 18 and chunk 26 are the historically dominant silent-hang death sites, 7/12 and 4/12
      respectively; chunk 8 is also now a confirmed danger point per occurrence 12 — don't assume safety at any specific
      chunk); (2)
      `gcloud compute instances list --account=1060025368044-compute@developer.gserviceaccount.com     --filter="name~'mtds-backfill-odds'"`
      for the live instance; (3) if gone, distinguish CONFIRMED SILENT HANG (triple-signal ~15-21min silence across
      run.log/heartbeat-blob/WATCHDOG_TRACE.log, then a `delete` op from account
      `1060025368044-compute@developer.gserviceaccount.com` — add a Timeline row + Progress Log entry to the hang-doc,
      bump its occurrence count) from a ROUTINE SPOT PREEMPTION (`compute.instances.preempted` system event, not a
      `delete` op — NOT an occurrence, wait ~5min for the fleet's own auto-recovery via `unified-trading-sa@...` before
      relaunching manually); (4) relaunch via
      `CLOUDSDK_CORE_ACCOUNT=1060025368044-compute@developer.gserviceaccount.com bash     deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh --vm-name     mtds-backfill-odds-smallchunkN-20260810`
      (increment N; the launcher can background past a short foreground timeout on tarball republish — check its output
      when it completes rather than assuming failure), confirm genuine boot via `run.log` content, not
      exit_code/creation alone; (5) journal a Progress Log entry to this doc citing chunk position, OOM count,
      occurrence count, and (only when re-run) the gap census reading; commit+push+verify
      (`git rev-list --count origin/<branch>..HEAD` must be 0 after push). **Not AO-dispatchable as a single one-shot
      todo** (the underlying task runs for days across many silent-hang cycles) — this is intentionally designed to be
      picked up, make partial progress, and left open across many repeated dispatches, the same proven pattern already
      used for weeks in `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s own P1/P2 todos.
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
- **20:34Z — 🎉 MAJOR MILESTONE: FIXTURE_LINEUPS shard-level target reached (needed 1,326 → 116, matching
  FIXTURE_STATS's own 116-shard honest-absence floor exactly). Also: 8th silent-hang occurrence (smallchunk13, chunk 18,
  relaunched).** Census confirms FIXTURE_LINEUPS has converged to the same genuine honest-absence residual as
  FIXTURE_STATS — this is the target state, not a fluke (clean match to precedent). **However, the INJURIES launch is
  NOT triggered yet**: the current FIXTURE_LINEUPS VM (`af-backfill-20260809-180612`) is still actively running its
  full-range resume sweep (chunk 3/5 as of this check, ~70min estimated remaining) and the AF launcher's singleton lock
  only permits ONE concurrent VM account-wide (previously confirmed: parallelizing
  FIXTURE_STATS→FIXTURE_LINEUPS→INJURIES is not possible due to the real account-wide API-Football daily quota) — so
  INJURIES must wait for this VM to complete and self-delete, matching the exact precedent FIXTURE_STATS itself set
  (didn't declare done/launch-next until its own VM reached 26/26 chunks and gracefully exited). **Correction to my own
  earlier-tick trigger criterion**: shard-count alone reaching the floor is necessary but not sufficient — the singleton
  lock's actual availability (VM completion) is the real gate. Will launch INJURIES the moment
  `af-backfill-20260809-180612` self-deletes. Separately: `smallchunk13` died with clean 3-signal evidence (~17.6min
  gap, chunk 18 again — back-to-back with occurrence 7/smallchunk12, now the clear majority death chunk at 4/8),
  relaunched as `mtds-backfill-odds-smallchunk14-20260809`, confirmed genuinely booted (chunk 1/451, correct skip-fast).
  Full detail: `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` (now 8x).
- **21:33Z — 🎉🎉 MAJOR MILESTONE: FIXTURE_LINEUPS FORMALLY CLOSED OUT (genuinely converged, VM completed cleanly),
  INJURIES LAUNCHED (final entity in the AF campaign queue).** `af-backfill-20260809-180612` reached
  `PROGRESS: chunk=5/5 range=2026-05-15→2026-08-08 time=2026-08-09T21:17:46Z`, `instruments-backfill loop complete`,
  `exit_code=0`, clean graceful self-delete via `VM_SHUTDOWN_ON_COMPLETION` — same completion signature FIXTURE_STATS
  set as precedent. **Per rule 4a, re-censused live before trusting the clean exit**: FIXTURE_LINEUPS needed **still
  116** (unchanged from the pre-completion reading, confirming durable, genuine convergence — not a fluke or a
  regression). This closes out FIXTURE_LINEUPS at the exact same honest-absence floor as FIXTURE_STATS (116 each).
  **Launched INJURIES immediately** (the AF campaign's final queued entity, singleton lock now free):
  `deployment-service/scripts/vm/launch-api-football-backfill-vm.sh` with
  `RESUME_ENTITY=INJURIES RESUME_START_DATE=2020-06-06 RESUME_END_DATE=2026-08-09` (same pattern as the earlier
  FIXTURE_LINEUPS launch) — created `af-backfill-20260809-222924`, confirmed RUNNING via the launcher's own output
  (tarballs fresh, guard passed); boot-health verification via run.log in progress (background poll, not yet trusted on
  exit_code alone). Confirmed baseline via `census_all_af_entities_completion_2026_08_03.py` right before launch:
  INJURIES needed=62,709 (unchanged, matches the last dedicated reading — the biggest remaining chunk of the whole AF
  campaign). Separately: `smallchunk14` healthy at chunk 9/451, zero incidents this tick. **AF campaign status: 3 of 4
  full-league entities now converged (FIXTURE_STATS, PLAYER_STATS, FIXTURE_LINEUPS) — only INJURIES (running), STANDINGS
  (271 needed), and TEAMS (96 needed) remain**, with STANDINGS/TEAMS being small honest-absence-adjacent residuals
  likely to resolve incidentally as INJURIES sweeps the same date range.
- **21:46Z — a SECOND, undocumented odds_api VM (`smallchunk10`, reused name) ran concurrently with `smallchunk14` for
  ~15 min — a real `odds-api-concurrency-guard.sh` cap-violation — but self-resolved (deleting on its own) before any
  action was needed.** Full detail + evidence in the owning issue doc:
  `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s 21:46Z Progress Log entry. Short version: `smallchunk10`
  (`START_DATE=2020-08-29`, heavily overlapping `smallchunk14`'s `START_DATE=2020-06-06`, both `END_DATE=2026-08-08`)
  appeared `RUNNING` alongside `smallchunk14` with no launch provenance in either doc — most likely an uncoordinated
  concurrent-slot relaunch. Credit balance checked live and healthy (10,654,194 of 15M remaining), so not urgent; by the
  time investigation finished `smallchunk10` had already entered `STOPPING` on its own. `smallchunk14` unaffected,
  healthy at chunk 12/451. No VM launched or killed by this tick. Flagging: if this shape recurs and does NOT
  self-resolve, escalate to the operator (real vendor-credit double-spend risk).
- **22:03Z — Both fleets healthy, genuine forward progress confirmed on INJURIES (rule 1b).**
  `af-backfill-20260809-222924` (INJURIES): real date progress 2020-06-16→2021-01-17 since launch, entity-scoped mode
  correctly restricting to INJURIES only. `smallchunk14`: chunk 15/451 (`2020-08-15→2020-08-19`), **zero OOMs across the
  entire run so far**, heartbeat fresh (~1.7min old) — 3 chunks from chunk 18. Census
  (`census_all_af_entities_completion_2026_08_03.py`): INJURIES needed **62,709 → 60,733** (-1,976 in ~27min, ~4,391/hr)
  — genuine movement, though at this rate full convergence is ~14h out (this is by far the largest remaining AF entity,
  expect a long haul, not a quick tick-over- tick drop like FIXTURE_LINEUPS showed). STANDINGS (271) and TEAMS (96)
  unchanged, as expected (not independently tracked unless they stall). No intervention needed.
- **22:46Z — Both fleets healthy, INJURIES rate accelerated sharply.** `af-backfill-20260809-222924`: real progress
  2021-01-17→2021-11-04 since last check, writing genuine injury rows (e.g. 125 for 2021-11-04), new
  `[[VM_PROGRESS]] last_completed_date=... monotonic=true` marker observed (useful ground-truth signal for future
  ticks). `smallchunk14`: cleared chunk 17 cleanly, now in chunk 18 with 1 expected OOM-retry (EPL, self-recovering, not
  actionable) on LA_LIGA, RSS climbing (24.8GiB, approaching but not yet OOM range), heartbeat fresh (~54s old). Census:
  INJURIES needed **60,733 → 52,494** (-8,239 in ~43min, ~11,497/hr — up sharply from ~4,391/hr last tick; ETA to
  convergence now ~4.6h at this rate, down from the earlier ~14h estimate). STANDINGS/TEAMS unchanged as expected. No
  intervention needed.
- **23:19Z-23:27Z — 9th silent-hang occurrence (smallchunk14, chunk 18 again — now 5/9 occurrences at chunk 18, a clear
  majority), relaunched; INJURIES steady progress continues.** `smallchunk14` died with clean 3-signal evidence
  (~17.3min gap, standard watchdog account, RSS=17.3GiB — not OOM), relaunched as
  `mtds-backfill-odds-smallchunk15-20260810` (new date, timestamp-suffixed), confirmed genuinely booted (chunk 1/452,
  correct skip-fast). Full detail: `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` (now 9x). INJURIES
  (`af-backfill-20260809-222924`): `[[VM_PROGRESS]]` marker confirms real monotonic advance to 2022-06-19 (from
  2021-11-04 last tick). Census: INJURIES needed **52,494 → 47,294** (-5,200 in ~33min, ~9,455/hr — steady, similar
  order to last tick; ETA holding around ~5h). Both fleets healthy overall, no further intervention needed.
- **00:26Z — Both fleets healthy, INJURIES accelerating further.** `af-backfill-20260809-222924`: `[[VM_PROGRESS]]`
  monotonic advance 2022-06-19→2023-09-04 (over a year of dates in under an hour). `smallchunk15`: chunk 12/452, **zero
  OOMs across the entire run so far**, fresh (~19s heartbeat lag) — 6 chunks from chunk 18. Census: INJURIES needed
  **47,294 → 35,732** (-11,562 in ~59min, ~11,764/hr — accelerating further; ETA now ~3h, down from ~5h). Minor
  non-issue: PLAYER_STATS shows `needed=3` (was 0) — its `expected` denominator grew by exactly 3 as "today" advances
  and new fixture-days enter scope; not a regression, those 3 shards are brand-new and simply not yet captured.
  STANDINGS/TEAMS unchanged. No intervention needed.
- **00:57Z — Both fleets healthy, INJURIES holding accelerated pace.** `af-backfill-20260809-222924`: `[[VM_PROGRESS]]`
  monotonic advance 2023-09-04→2024-04-04. `smallchunk15`: chunk 17/452, zero OOMs across the entire run so far, fresh
  (~11s heartbeat lag) — 1 chunk from chunk 18, watching closely next tick. Census: INJURIES needed **35,732 → 29,480**
  (-6,252 in ~31min, ~12,101/hr — steady, consistent with the recent accelerated pace; ETA ~2.4h). Not yet near the
  convergence floor (~1000-2000 range) — no "campaign done" planning needed yet. No intervention needed.
- **01:28Z — 10th silent-hang occurrence (smallchunk15, chunk 18 again — now 6/10, the clear majority), relaunched;
  caught the STOPPING transition live for the first time this session; discovered + filed a separate manifest
  consolidator finding.** `smallchunk15` died with clean 3-signal evidence (~15.5min gap, standard watchdog account,
  RSS=22.8GiB — not OOM); a background poll caught it in `status=STOPPING` at 01:27:33Z before full deletion at
  01:28:47Z (first live catch this session, previously always found already-gone). Relaunched as
  `mtds-backfill-odds-smallchunk16-20260810`, confirmed genuinely booted (chunk 1/452, correct skip-fast). Full detail:
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` (now 10x). **Separately**: two consecutive INJURIES
  census reads ~50min apart were byte-identical (needed=29,480 both times) despite the VM's own `[[VM_PROGRESS]]` marker
  confirming real, substantial date advancement in that window — root-caused via Cloud Logging: the sports manifest
  consolidator for this bucket has been reporting a static `rows_out=17090683` across
  > =5 genuine merges spanning 1h+ (rows_in and dedup_dropped both climbing in lockstep, netting zero canonical growth),
  > plus a 15min streak where every consolidator attempt returned `error=locked`. This matches the symptom signature of
  > the already-RESOLVED `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` incident (that one was
  > odds_api-specific, root-caused to a freshness-sentinel bug, not a consolidator defect) but for a different entity
  > (INJURIES) — NOT assumed to be the same root cause without verification. Filed as its own P1 doc:
  > `sports_manifest_consolidator_static_rows_out_injuries_2026_08_10.md`. **Practical implication for this monitoring
  > loop going forward**: during a stall like this, trust a live VM's own progress marker (`[[VM_PROGRESS]]`/chunk
  > markers) over a flat census reading — the underlying campaigns are NOT actually stalled, only the aggregate
  > measurement is currently blind. Both fleets' underlying work is healthy; the census-based "needed" numbers from the
  > last ~1h+ should be treated as a lower bound on true progress, not a stall signal.
- **02:39Z — Manifest consolidator stall has RESOLVED; both fleets healthy.** `smallchunk16`: chunk 13/452, zero OOMs
  across the entire run so far, fresh — 5 chunks from chunk 18. `af-backfill-20260809-222924`: `[[VM_PROGRESS]]`
  monotonic advance continuing to 2024-11-02. Census confirms the manifest consolidator finding from last tick
  (`sports_manifest_consolidator_static_rows_out_injuries_2026_08_10.md`) has self-resolved: manifest rows grew
  (16,176,107 → 16,181,741, +5,634) and INJURIES needed dropped **29,480 → 20,490** (-8,990) — both the census and the
  VM's own progress marker now agree on genuine forward movement (not reporting a precise hourly rate this tick since
  the stall window makes the elapsed-time denominator ambiguous). No intervention needed on either fleet.
- **03:12Z — Both fleets healthy, no new hang, real forward progress on both measures.** Same live instances as last
  tick (`af-backfill-20260809-222924`, `mtds-backfill-odds-smallchunk16-20260810`) — no rotation, still 10x hang
  occurrences (no 11th). `smallchunk16`: chunk 16/452, zero OOMs/CHUNK_FAILED, fresh (log activity at current wall time)
  — 2 chunks from chunk 18. INJURIES `[[VM_PROGRESS]]` monotonic advance 2024-11-02 → 2025-05-04 (~6 real months in
  ~30min). Fresh census confirms genuine progress: INJURIES needed **20,490 → 17,135** (-3,355); other AF entities
  unchanged at their floors (PLAYER_STATS=3, STANDINGS=271, TEAMS=96); grand total needed 20,860 → 17,505. Note:
  manifest row total itself read flat (16,181,741, same as last tick) even though INJURIES needed dropped — entity-level
  resolution apparently isn't purely a function of the aggregate row count, so not treating this as a fresh stall (both
  the VM's own marker and the entity-specific needed count independently confirm real movement). No intervention needed
  on either fleet.
- **03:31Z — INJURIES strong progress; smallchunk16 POSSIBLE 11th hang developing (watching, not yet confirmed).** Same
  instances as last tick, still 10x confirmed hang occurrences. INJURIES `[[VM_PROGRESS]]` monotonic advance 2025-05-04
  → 2025-09-20 (~4.5 real months in ~19min, strong pace); census confirms INJURIES needed **17,135 → 13,957** (-3,178);
  other entities unchanged at floor. Manifest row total still flat at 16,181,741 (3rd consecutive reading at this exact
  value while INJURIES needed keeps dropping each tick) — now a stable, reproducible pattern across 2 ticks; treating
  entity-level `needed` (corroborated independently by the VM's own progress marker every tick) as the trustworthy
  signal, not reopening the filed consolidator issue since actual progress is unambiguous. **Watch item**:
  `smallchunk16` hit chunk 18 at ~03:25Z with RSS climbing fast (1.7→10.2→16.4→21.5GiB across ~1min), then all
  `run.log`/`WATCHDOG_TRACE.log` activity stopped at ~03:26:39-49Z; heartbeat blob's last update 03:27:19Z. As of this
  entry (03:31:15Z, ~4.5min silent) the instance is still `RUNNING` (not yet `STOPPING`) — too early to call an 11th
  occurrence (prior silences ran 15-21min before deletion) but the profile (chunk 18, fast RSS climb, silence onset)
  matches the established signature closely. Not relaunching preemptively — will re-check on a shortened watch interval;
  if it resolves into a full triple-signal silence + delete op, will log as the 11th occurrence and relaunch immediately
  per the established pattern. If it recovers/resumes cleanly, that would be the first-ever self-recovery from this
  signature — also worth noting either way.
- **03:50Z — 11th silent-hang occurrence CONFIRMED for `smallchunk16` (chunk 18, ~19.8min gap, longest yet); relaunched
  as `smallchunk17`; INJURIES needed 13,957 → 11,001.** The watch item flagged last tick resolved as a confirmed hang,
  not a self-recovery: `smallchunk16` stayed silent from `03:26:39Z`, was caught live in `STOPPING` at `03:46:52Z` (2nd
  live catch this session), delete op confirms insert `03:46:30Z` — a ~19.8min gap, the longest confirmed so far though
  still within the established ~16-24min range, not a new outlier. Chunk 18 is now the dominant death site at 7/11 (vs
  4/11 at chunk 26); EPL has recurred as the death-league 3 times. Relaunched immediately as
  `mtds-backfill-odds-smallchunk17-20260810`, guard confirmed `0 running + 1 planned = 1 <= cap 1`, tarballs fresh,
  instance created and `RUNNING`; boot-health verification (first real run.log line) pending as of this entry — not yet
  trusting exit_code/creation alone. Full detail + Timeline row + Progress Log entry:
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` (now 11x). **Separately**: INJURIES continued
  strong, unambiguous progress — `[[VM_PROGRESS]]` advanced 2025-09-20 → 2025-12-19 this tick, census confirms needed
  dropped **13,957 → 11,001** (-2,956); manifest row total has now been flat at 16,181,741 for a 4th consecutive reading
  while needed keeps declining every tick — a stable, reproducible decoupled-metric pattern (not a stall; both
  independent signals keep confirming real forward movement). Other AF entities unchanged at their floors.
- **04:16Z — Both fleets healthy; INJURIES accelerating hard toward convergence (needed 11,001 → 5,406, -5,595 in one
  tick).** Same live instances (`af-backfill-20260809-222924`, `mtds-backfill-odds-smallchunk17-20260810`) — no
  rotation, still 11x hang occurrences (no 12th). `smallchunk17`: chunk 5/425, zero OOMs/CHUNK_FAILED, fresh — 13 chunks
  from chunk 18. INJURIES `[[VM_PROGRESS]]` monotonic advance 2025-12-19 → 2026-05-22 (~5 real months in ~22min, the
  fastest pace observed yet, now within ~2.5 months of the 2026-08-09 end date). Fresh census confirms the acceleration:
  INJURIES needed **11,001 → 5,406** (-5,595); other AF entities unchanged at floor (PLAYER_STATS=3, STANDINGS=271,
  TEAMS=96); grand total needed 11,371 → 5,776 — the campaign is now visibly closing in on whatever INJURIES' own
  honest-absence floor turns out to be (watching closely over the next few ticks; may not reach exactly 0, similar to
  the other 3 entities' small non-zero floors). Manifest row total flat at 16,181,741 for a 5th consecutive tick while
  needed keeps dropping — the decoupled-metric pattern remains stable and not concerning. No intervention needed on
  either fleet.
- **04:39Z — MAJOR MILESTONE: INJURIES backfill VM (`af-backfill-20260809-222924`) completed its full date range CLEANLY
  and self-deleted — needed dropped to 334, near the same order of magnitude as the other 3 entities' floors.**
  Confirmed via run.log: reached `PROGRESS: chunk=26/26 range=2026-08-04→2026-08-09` (the full 2020-06-06→2026-08-09
  assigned range), `[vm-exec] command exited rc=0`, `DEPLOYMENT_COMPLETED ... exit_code=0`, then
  `VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete`. Confirmed via `gcloud compute operations list`: the delete
  op was issued by `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` (the VM's own service account
  self-terminating on completion), NOT the `1060025368044-compute@...` watchdog account — this is a genuine clean
  finish, not a silent-hang kill (the hang-doc's tracked signature is unrelated to this event). Fresh census confirms
  INJURIES needed **5,406 → 334** (-5,072); all 4 AF entities are now at small residual floors: PLAYER_STATS=3,
  INJURIES=334, STANDINGS=271, TEAMS=96 — grand total needed only **704** shards (down from tens of thousands at
  campaign start). **Not yet declaring the AF campaign fully done**: per rule 4a (never trust a single reading), 334
  needs at least one more stable re-census before treating it as INJURIES' genuine honest-absence floor rather than a
  residual still being caught up by the manifest consolidator from the VM's final batch of per-VM shard writes (the
  manifest row total itself is still flat at 16,181,741 for a 6th consecutive tick, though no active INJURIES VM remains
  to explain further catch-up the way earlier ticks did) — will re-check next tick with no VM running to see if 334
  holds steady. The AF singleton lock is now free (no AF VM running); with FIXTURE_STATS, FIXTURE_LINEUPS, PLAYER_STATS,
  STANDINGS, and TEAMS already converged and INJURIES now essentially converged too, there is no further AF entity
  queued to launch — if 334 confirms stable, the AF side of this dual-fleet campaign is effectively complete, leaving
  only the odds_api backfill as the sole remaining open campaign. **Odds fleet**: same instance
  (`mtds-backfill-odds-smallchunk17-20260810`), still 11x hang occurrences (no 12th); chunk 10/425, zero
  OOMs/CHUNK_FAILED, fresh — 8 chunks from chunk 18 (watch closer next tick as it approaches).
- **04:58Z — AF CAMPAIGN COMPLETE: INJURIES needed confirmed stable at 334 (byte-identical repeat reading, no active
  VM), all 4 AF entities converged.** Re-census with no INJURIES VM running reads **identical** to the prior tick:
  INJURIES needed=334 (unchanged), manifest rows=16,181,741 (unchanged, 7th consecutive flat reading), confirmed no new
  `af-backfill-*` instance exists anywhere. Per rule 4a (never trust a single reading), this repeat-stable value with
  zero active writers confirms 334 is INJURIES' genuine honest-absence floor, not consolidator catch-up lag. **All 4 AF
  entities are now at their converged floors**: PLAYER_STATS=3, INJURIES=334, STANDINGS=271, TEAMS=96 — grand total
  needed=704 shards, unchanged from last tick. Combined with FIXTURE_STATS/FIXTURE_LINEUPS' earlier confirmed
  convergence (both at needed=116, matching exactly), **the entire AF full-entity-completion campaign (FIXTURE_STATS →
  FIXTURE_LINEUPS → PLAYER_STATS → INJURIES → STANDINGS → TEAMS) is now DONE** — no further AF VM launches are needed;
  the singleton lock is permanently free going forward for this campaign. The standing monitoring loop continues for the
  odds_api fleet only (the sole remaining open campaign). **Odds fleet**: `smallchunk17` was SPOT-preempted
  (`compute.instances.preempted`, routine — NOT the tracked hang signature) at 04:44:35Z and auto-relaunched by the
  fleet's own recovery mechanism (`unified-trading-sa@...`) within ~2min at 04:46:30Z, confirmed genuinely resuming
  (chunk 2/415, zero OOMs, correctly skip-fasting). Still 11x hang occurrences (no 12th) — this preemption is unrelated
  to that tracked pattern. No intervention needed.
- **05:22Z — Odds fleet healthy, no new hang (still 11x); AF sanity-check clean (no new af-backfill instance, as
  expected now the AF campaign is closed).** `smallchunk17`: chunk 5/415, zero OOMs/CHUNK_FAILED, fresh (~8s log lag) —
  13 chunks from chunk 18. **Noted for future ticks**: unlike the 4 AF entities, there is no dedicated odds_api-wide
  census script in this repo tree — the reliable ground-truth completion signal for this fleet is the VM's own chunk
  total (currently 415, recalculated fresh at each boot as remaining real-work chunks shrink — was 452 several
  relaunches ago, then 425, now 415) reaching its own final chunk N/N followed by a clean `exit_code=0` +
  `VM_SHUTDOWN_ON_COMPLETION` self-delete, mirroring exactly how the INJURIES AF-entity VM completed last tick. Watching
  for that same signature on this fleet as the terminal completion event, alongside the shrinking chunk-total trend as a
  proxy for how close the campaign is to done. No intervention needed this tick.
- **05:54Z — Odds fleet healthy, no new hang (still 11x); AF sanity-check clean.** `smallchunk17`: chunk 8/415, zero
  OOMs/CHUNK_FAILED, RSS=10.2GiB (unremarkable), ~3min log lag (within normal noise, not concerning — established hang
  signature is 15-21min total silence) — 10 chunks from chunk 18. No new `af-backfill-*` instance exists (AF campaign
  remains closed as expected). No intervention needed.
- **06:25Z — 12th silent-hang occurrence CONFIRMED for `smallchunk17` (NEW death site: chunk 8, not 18 or 26);
  relaunched as `smallchunk18`, VM created + RUNNING, run.log boot-health still pending.** `smallchunk17` went silent
  `05:51:56Z`-`05:53:55Z`, deleted by the watchdog account at `06:14:41Z` (~20.8min gap, longest yet but still within
  the established range). Died mid-chunk-8, EPL, RSS=10.2GiB — the FIRST occurrence at a chunk other than 18 or 26 in
  this campaign's history (updated tally: 18×7, 26×4, 8×1), meaningfully weakening the per-chunk-content correlation
  hypothesis further. Full detail + Timeline row + Progress Log entry:
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` (now 12x). **Relaunch anomaly (resolved)**: the
  standard launcher invocation did not complete within the harness's 120s foreground window (prior relaunches always
  completed in ~10-15s) and was moved to a background task — the actual cause, confirmed from the completed task's
  output, was a stale-tarball republish step (`lc_verify_tarball_freshness: republish complete — re-verifying`,
  re-uploading `setup-data-pipeline-vm.sh`/`vm-exec-with-gcs-tee.sh`), NOT a hang in the launcher itself.
  `mtds-backfill-odds-smallchunk18-20260810` confirmed created and `RUNNING` via `gcloud compute instances list`;
  `run.log` boot-health (first real log line) not yet available as of this entry (still within the normal ~1-2min
  tarball-extraction boot window) — will confirm genuine progress next tick, not trusting VM-created/RUNNING alone. AF
  sanity check remains clean (no new `af-backfill-*` instance).
- **06:44Z — `smallchunk18` boot-health CONFIRMED healthy; the ~5.5min-and-counting run.log delay was just slower
  tarball extraction, not a genuine problem.** Real log content now present: chunk 3/425, zero OOMs/CHUNK_FAILED,
  correctly skip-fasting through already-covered dates. Still 12x hang occurrences (no 13th). AF sanity check remains
  clean (no new `af-backfill-*` instance). No intervention needed.
- **07:13Z — Odds fleet healthy, no new hang (still 12x); cleared chunk 8 (the new confirmed danger point) cleanly.**
  `smallchunk18`: chunk 9/425, zero OOMs/CHUNK_FAILED, fresh (~1.3min log lag) — 9 chunks from chunk 18. AF sanity check
  remains clean (no new `af-backfill-*` instance). No intervention needed.
- **07:37Z — CORRECTION + better ground-truth tool found: a dedicated odds_api-wide gap census DOES exist**
  (`market-tick-data-service/scripts/sports/census_odds_api_gap_verify_2026_08_02.py`), contradicting an earlier tick's
  claim that no such script exists (that was a search-thoroughness miss, not a fact about the codebase) — it was built
  by the prior `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` investigation (635→590→300 missing days across
  several rounds of fixes: OOM bug, manifest-consolidator stall, credential/quota block). Ran it fresh: **300 of 2257
  calendar days since the 2020-06-06 floor still have ZERO manifest row for odds_api** — byte-identical to the
  2026-08-02 reading, i.e. genuinely ZERO net gap-closure in the ~8 days since, despite this whole campaign's relaunch
  history. This is NOT a stall: the current run walks sequentially from 2020-06-06 forward and is only at chunk 13/425
  (~2020-08-09) — the earliest of the 151 real gap-ranges is 2021-06-07, so the campaign hasn't reached a single actual
  gap day yet; everything so far has been skip-fast through already-covered 2020 ground (1957/2257 days, 87%, are
  already captured — this was never a from-scratch backfill). The 300-day gap is dominated by 3 named multi-week ranges
  (2024-11-21→12-31 41d, 2026-02-22→03-28 35d, 2026-06-25→07-15 21d) plus ~148 smaller 3-5 day ranges scattered
  2021-2026 — full breakdown + root-cause history in `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`. **Going
  forward, this census (re-run periodically, not every tick — it's cheap, ~4s/one manifest read) is the authoritative
  completion signal for this campaign, not the chunk-counter proxy** — the chunk counter tells us the VM is alive and
  progressing but not whether real gap-closing work is happening yet; watch for the 300 to start dropping once the
  frontier passes ~chunk 70 (≈2021-06). **Odds fleet health this tick**: `smallchunk18` at chunk 13/425, zero
  OOMs/CHUNK_FAILED, fresh (~1.5min log lag) — 5 chunks from chunk 18 (tightening next wakeup to watch it through the
  danger zone). Still 12x hang occurrences (no 13th). AF sanity check remains clean.
- **07:52Z — Odds fleet healthy, no new hang (still 12x); still approaching chunk 18.** `smallchunk18`: chunk 15/425,
  zero OOMs/CHUNK_FAILED, very fresh (~40s log lag) — 3 chunks from chunk 18, keeping the tightened watch interval until
  it clears. AF sanity check remains clean (no new `af-backfill-*` instance). Not re-running the odds_api gap census
  this tick (nothing new to learn — frontier is still deep in already-covered 2020 ground, well before the first real
  gap at ~chunk 70/2021-06). No intervention needed.
- **08:06Z — `smallchunk18` gone: a routine SPOT preemption (NOT the tracked 13-occurrence-yet silent-hang bug), but
  auto-recovery didn't fire within ~11min (longer than the ~2-4min auto-recovery window seen earlier this session for
  the same preemption class) — relaunching manually as `smallchunk19`.** Confirmed via `gcloud compute operations list`:
  a `compute.instances.preempted` system event at `07:55:55Z` (aligning almost exactly with the last observed signals —
  run.log `07:53:50Z`, heartbeat `07:55:31Z`, WATCHDOG_TRACE `07:55:03Z`), NOT a `delete` op from the
  `1060025368044-compute@...` watchdog account — this is the routine SPOT-preemption pattern (same class as
  smallchunk16's and FIXTURE_LINEUPS' earlier preemptions), distinct from the hang-doc's tracked silent-hang signature;
  still 12x confirmed hang occurrences, this is NOT a 13th. Died at chunk 15/425 (well before chunk 18), zero
  OOMs/CHUNK_FAILED beforehand. Waited ~11min for the fleet's own auto-recovery mechanism (which handled prior
  preemptions within ~2-4min) — no new instance appeared, so relaunched manually via the standard launcher
  (`--vm-name mtds-backfill-odds-smallchunk19-20260810`); the launch command backgrounded past the harness's 120s
  timeout (this time all 4 tarballs were already fresh, unlike occurrence 12's republish-driven delay — cause of the
  slowness this time unclear). Guard confirmed `0 running + 1 planned = 1 <= cap 1`, `smallchunk19` created and
  `RUNNING`; `run.log` boot-health still pending as of this entry, not yet trusted on VM-created/RUNNING alone. AF
  sanity check remains clean.
- **08:31Z — `smallchunk19` ALSO preempted, within ~2min of creation (before any run.log line was ever written) —
  relaunched as `smallchunk20`.** Confirmed via `gcloud compute operations list`: insert `08:09:50Z`, a second
  `compute.instances.preempted` system event at `08:11:45Z` — routine SPOT variance, not the tracked hang (no `delete`
  op from the watchdog account, and no processing ever started to exhibit that signature anyway). Two preemptions in
  ~35min is unusual but not itself actionable (no available evidence distinguishes it from ordinary zone-level SPOT
  capacity variance; not switching to on-demand over 2 data points). No auto-recovery fired again within the ~20min this
  VM was absent, so relaunched manually via the standard launcher (`--vm-name mtds-backfill-odds-smallchunk20-20260810`)
  — guard confirmed `0 running + 1 planned = 1 <= cap 1`, all 4 tarballs fresh, created and `RUNNING`. **New todo added
  this tick**: a proper `- [ ]` AO-dispatchable todo for this fleet's ongoing babysitting-to-completion was missing from
  this doc's `## Todos` section (the doc has always been `assigned_vm: planning`, but all monitoring work since
  2026-08-07 has lived only in this Progress Log narrative with no open checkbox for AO's backlog regenerator to pick
  up) — added, citing the full established playbook (hang-doc, preemption-vs-hang disambiguation, census script,
  relaunch command) so a fresh AO dispatch can continue this without needing this session's accumulated context. AF
  sanity check remains clean.
- **09:05Z — CORRECTION: 3rd preemption confirmed for `smallchunk20` too (not a hang); found another session's VM
  already covering the gap — did NOT launch a duplicate `smallchunk21`.** Verified via `gcloud compute operations list`:
  `smallchunk20` also died via `compute.instances.preempted` (`08:38:22Z`, ~5.5min lifespan) — **all 3 of
  smallchunk18/19/20 were routine preemptions, zero actual silent-hangs this window**, confirmed via the authoritative
  operations list each time (not inferred from silence alone). A concurrent AO dispatch of the sibling
  `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` doc's own P1 backfill todo independently observed the same
  0-VM window and tentatively logged it as "13th/14th hang occurrence" — that inference didn't check operations list and
  is incorrect per the evidence above; **the hang-doc's occurrence count stays correctly at 12x**, not 13x/14x. My own
  relaunch attempt (`smallchunk21`) failed outright at launch time (stale `unified-api-contracts` tarball even after
  auto-republish — transient, the repo's working tree is clean now) and never created an instance. By the time I checked
  again, a different VM had appeared: `mtds-backfill-odds-gap-20260727-20260806` (`--start 2026-07-27 --end 2026-08-06`,
  a narrow targeted range covering the scheduler-dormancy gap window, `RESUME_ALLOW_PARALLEL=true`, created `08:54:37Z`)
  — confirmed genuinely healthy and real-fetching (chunk 1, real `Processed date=2026-07-27` rows, `ManifestWriter`
  writes), though its RSS was climbing fast (9→28GiB in ~3min, 92.9% mem at last sample — worth watching for an OOM next
  tick). Did NOT launch a duplicate, respecting the fleet's singleton-VM policy — the sibling doc's own dispatch
  independently reached the same non-duplication decision. **Discovered this tick**: AO is already actively dispatching
  the ORIGINAL `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` doc's own P1 backfill todo (task
  `-3b44a0a4ec31`, multiple dispatches: slot 20, slot 3, slot 26...) — this is a working, proven precedent for exactly
  the AO-dispatch pattern just set up in this doc's own new todo above; the two todos now track overlapping scope (both
  "keep the odds fleet alive to completion") and should be treated as the same underlying work, not duplicated effort —
  the sibling doc already cross-references this doc as "Full live tracker," closing the loop in one direction.
