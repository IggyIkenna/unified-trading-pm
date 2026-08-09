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

- **2026-08-07T10:2XZ** — Doc created in response to the operator's scope-widening directive. Ran the first
  comprehensive per-source census (table above) — this is meaningfully bigger than the vendor-completion audit done
  earlier the same session suggested (that audit's "100% clean" verdict for weather/understat only checked
  `attempted_failed`, missing the `expected_unattempted` backlog entirely — corrected here). Diagnosed odds_api's two
  failure modes (stale-credential 401s vs. the live, still-recurring SOURCE_RETURNED_ZERO honest-coverage guard-rail
  rejection). Killed the stuck Transfermarkt retry VM after confirming 2h17m of zero progress against a durably-502ing
  vendor endpoint. No remediation done yet beyond what's already tracked in the AF doc — this tick was entirely
  discovery + scoping; next tick should start on the P0 odds_api items.
- **2026-08-07T11:35Z** — **`mtds-backfill-odds-1` is behaving genuinely differently from every prior attempt in
  `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s history** — actively skip-fasting through already-covered
  dates at ~0.2-0.3s each (2020-08-01→2020-08-26 in under a minute) and correctly real-fetching genuinely-missing dates
  (2020-08-18: 782 rows written via the Tier-2 sentinel fan-out). This is the first live confirmation that the
  2026-07-30 freshness-scoping fix's own claim — "narrower/cheaper run, won't re-touch the 1,545 already-covered days" —
  is actually true in practice, not just in the fix author's analysis. One minor non-fatal warning noted
  (`venue=ODDS_API: data_type 'ODDS' is not valid for this venue's asset group`) but it didn't block the real write —
  not chasing it further this tick. No `PROGRESS.json` yet (still inside its first 250-day chunk). Still RUNNING, no
  signs of the preemption/freeze/OOM patterns that killed every prior attempt — watching through to actual completion.
  Weather backfill (`weather-backfill-20260807-120241`) also healthy: 16,361+ entries written, real per-date
  fixture-venue matching working, automatic archive-tier fallback handling minor upstream 400s cleanly. Launched the SFI
  expected_unattempted backfill (205,363 shards,
  `launch-sfi-backfill-vm.sh --entity SFI_PROGRESSIVE_STATS 2020-06-06 2026-08-07`) — confirm it reached RUNNING next
  tick. Checked Transfermarkt for endpoint recovery signal: no new manifest activity for `source=transfermarkt` since
  before the VM was killed (still 8 attempted_failed, unchanged) — this session's identity lacks Secret Manager access
  to the RapidAPI key to check the endpoint directly, so deferring rather than blind-retrying into a possibly-still-down
  endpoint.
- **2026-08-07T11:57Z — Intermediate re-census** (`census_all_sports_sources_2026_08_07.py`,
  instruments-service@f917f04f, 9,552,235 rows post-floor, down from 10,463,368 — consistent with China/Russia purge
  removing out-of-scope rows). VMs all still RUNNING: `mtds-backfill-odds-1`, `mtds-backfill-odds-401-retry`,
  `sfi-backfill-20260807-123519`, `weather-backfill-20260807-120241`. **Not yet converged**; doc remains open.

  | source                   | attempted_failed |  captured | empty_confirmed | expected_unattempted | Δ vs baseline                                             |
  | ------------------------ | ---------------: | --------: | --------------: | -------------------: | --------------------------------------------------------- |
  | api_football             |           30,044 | 1,608,086 |       3,242,485 |              649,952 | AF↓5,014 (quota exhaustion clearing via running backfill) |
  | odds_api                 |           14,005 |    39,405 |          25,085 |                    0 | AF↑89 (SOURCE_RETURNED_ZERO still live-recurring)         |
  | mdps_odds_horizon_bucket |            2,791 |   198,520 |         256,585 |              157,994 | unchanged — backfill VM running                           |
  | transfermarkt            |                8 |    37,611 |         378,449 |                    0 | unchanged — vendor still down                             |
  | instruments_service      |                2 |     2,169 |          60,145 |                    0 | unchanged                                                 |
  | footystats               |                0 |    63,603 |       1,116,989 |                    0 | rows reduced (China/Russia purge)                         |
  | open_meteo (weather)     |                0 |    16,479 |         196,329 |              205,517 | EU unchanged — backfill VM running                        |
  | soccer_football_info     |                0 |    20,118 |         190,742 |              205,363 | EU unchanged — backfill VM running                        |
  | understat                |                0 |     7,158 |         826,321 |                   30 | rows reduced (China/Russia purge); EU=30 unchanged        |

  Key findings: (1) odds_api AF **increased** by 89, confirming SOURCE_RETURNED_ZERO cluster still actively generating
  new failures — P0 investigation unresolved. (2) `mtds-backfill-odds-401-retry` VM running (not yet in manifest). (3)
  Blank-source row (250 captured, no source value) appeared in manifest — minor artifact, not investigated. (4) A new
  census should be run once all VMs reach clean terminal state.

- **2026-08-07T12:15Z** — **Root-caused + fixed the 13,045-row SOURCE_RETURNED_ZERO cluster.** Root cause: the v1
  sentinel (`_emit_sports_v1_sentinels`) was missing the per-bookmaker coverage gate that the v2 path already had.
  `is_expected_for_source("odds_api", ...)` returns `True, None` for all leagues (generic catch-all — no bookmaker
  dimension), so all 22 bookmakers were treated as expected for every league with a fixture. The fix: add
  `_is_bookmaker_league_covered_exact(bm, league_id)` check inside the `SOURCE_RETURNED_ZERO` branch — when False, emit
  `empty_confirmed(EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE)` instead of `attempted_failed`. Import already existed;
  mirrors v2 exactly. Test updated (old name renamed + coverage mock added) + new uncovered-path test added. Shipped:
  `market-tick-data-service@70f131667`, QG green. The recurring 13,045 rows will resolve on next backfill run as the v1
  sentinel re-emits these shards with the correct classification.

- **2026-08-07T12:00Z** — **Confirmed credential valid + launched targeted 401-retry VM.** Credential check:
  `mtds-backfill-odds-1` (sweeping 2020-06-06→2026-08-07) has been running with zero 401s; wrote 782 rows on 2020-08-18
  confirming the key is live. Launched `mtds-backfill-odds-401-retry`
  (`launch-mtds-sports-odds-backfill-vm.sh --vm-name mtds-backfill-odds-401-retry --start 2025-09-01 --end 2026-07-27 --allow-parallel`,
  SPOT e2-highmem-4, concurrency guard: 1+1=2 ≤ cap 5, all 4 tarballs fresh). VM RUNNING at 11:55:46Z, startup script
  completed (exit 0, PID 4903/4917), first log at 11:59:01Z with skip-fast through covered dates and real-fetching
  2026-02-22 (960 credits, no 401s). `check_shard_freshness(retry_failed=True)` will mark the 871 `attempted_failed`
  401-rows as stale and re-fetch them as the VM sweeps through their dates.
- **2026-08-07T12:10Z — CORRECTION to the prior tick's optimistic `mtds-backfill-odds-1` assessment; it was wrong.**
  What looked healthy at 11:35Z (skip-fasting correctly, one real write for 2020-08-18) was only the FIRST few minutes
  of a repeating OOM-crash-loop I hadn't yet seen the full shape of. By 12:00Z the VM had OOM-killed
  (`exit=137 reason=OOM_KILLED`) on chunk 1/10 (`2020-06-06→2021-02-10`, the default 250-day chunk) for **10 consecutive
  leagues in ~50 minutes** — EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1, EREDIVISIE, PRIMEIRA_LIGA, JUPILER_PRO,
  SUPER_LIG, SCOTTISH_PREMIERSHIP — every single one crashing identically, zero successful chunk completions across any
  league, zero real forward progress despite ~50 minutes of GCE billing. This is the exact "cumulative, monotonic memory
  growth across real-fetch days" signature already documented (and never fully root-caused) in
  `plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` — retagged that doc's own stale
  `BLOCKED-CREDENTIALS` P1 too (same 2026-08-02→08-03 story) and recorded this fresh 2026-08-07 recurrence there. Killed
  `mtds-backfill-odds-1`. Attempted to relaunch with `--chunk-size 5` (that doc's best-validated, if imperfect,
  mitigation) but the concurrency guard correctly REFUSED (`mtds-backfill-odds-401-retry` already counts as 1 running,
  cap 1 without `--allow-parallel`) — waiting for that VM to finish rather than overriding, since it's small and already
  making genuine progress (real trades data confirmed writing, e.g. 786 rows for 2026-02-23, healthy memory ~40%).
  **Lesson for next tick**: relaunch the full-range odds_api backfill with
  `--vm-name <fresh> --chunk-size 5 --start 2020-06-06 --end <today>` (no `--force`) ONLY after confirming zero
  `mtds-backfill-odds-*` VMs are running (or explicitly pass `--allow-parallel` if `401-retry` is still going and credit
  budget is re-verified healthy first) — and even then, per the OOM doc's own "fifth recurrence" history,
  `--chunk-size 5` has previously still OOM'd 4 times in 75 chunks (much better than 10/10, but not proven-clean) —
  expect to babysit this, not launch and walk away. All other VMs healthy this tick: AF campaign PLAYER_STATS climbing
  (2025-03-08), footystats climbing (2023-04-23), SFI climbing with real writes (21,742 rows for 2020-10-17), weather
  confirmed still RUNNING (log read hit a transient 404, not treated as a failure signal on its own).
- **2026-08-07T12:21Z (slot 15)** — **Transfermarkt endpoint verification: still 502.** Confirmed
  `transfermarkt-football-data-api.p.rapidapi.com/api/v1/competitions/standings` returns HTTP 502 with RapidAPI message
  `"The API is unreachable, please contact the API provider" / "Your Client (working) ---> Gateway (working) ---> API (not working)"`.
  Now 3h+ since initial failure at 10:17Z. Secret Manager access confirmed working (key len=50 chars); the 8
  `attempted_failed` PLAYER_VALUES rows remain unretried. Tagged todo `[BLOCKED-UPSTREAM-OUTAGE]` — do not relaunch
  blind; verify endpoint returns 200 before dispatching a retry VM.
- **2026-08-07T12:38Z** — Applied the new codex rule 1b (`/codex/12-agent-workflow/async-wait-and-poll-discipline.md`,
  added this tick) properly this time: verified all five running VMs by diffing actual progress VALUES against the prior
  tick's readings, not just checking that log lines were still appearing. All genuinely healthy: AF campaign
  PLAYER_STATS 2025-03-08→2025-05-31 (chunk 21/26), footystats 2022-10-13→2023-10-16, SFI 2020-10-17→2021-02-17..19
  (distinct advancing dates), weather processing 2024-02-18..22, `mtds-backfill-odds-401-retry` 2026-02-23→2026-03-01
  with **zero** `CHUNK_FAILED`/`OOM_KILLED` matches across its entire log (not just the tail) — genuinely clean, still
  mid-chunk-1-of-2. Live-reverified odds-api credits: 14,463,684 remaining (only ~12,690 used since the ~11:35Z check,
  very low burn rate). Since `401-retry` is EPL-only/2025-09→2026-05 (non-overlapping in practical terms with a
  full-range/all-league relaunch — by the time a full sweep reaches that window, `401-retry`'s work will already be
  captured and skip-fast) and credits are healthy, launched the full-range small-chunk backfill WITH `--allow-parallel`
  rather than waiting further: `mtds-backfill-odds-smallchunk-20260807`
  (`--chunk-size 5 --start 2020-06-06 --end 2026-08-07`, no `--force`). This is the mitigation
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` itself flags as imperfect (previously OOM'd 4/75 chunks) —
  watching closely next tick for `CHUNK_FAILED`/`OOM_KILLED` recurrence, not treating this as fire-and-forget.
- **2026-08-07T13:08Z — both odds VMs confirmed genuinely healthy, zero OOM signatures.**
  `mtds-backfill-odds-smallchunk-20260807`: 0 `CHUNK_FAILED`/`OOM_KILLED` matches across its full log, now at chunk
  6/451 (`2020-07-01→2020-07-05`), skip-fasting + real-fetching correctly across ~30 leagues per chunk. Full-range,
  5-day-chunked, so a fresh subprocess baseline every chunk — the mitigation appears to be holding.
  `mtds-backfill-odds-401-retry`: also 0 `CHUNK_FAILED`/`OOM_KILLED`, still chunk 1/2 but genuinely progressing
  (2026-03-01 → date not yet logged this check, prior tick's date confirmed superseded). Its memory (`RESOURCE_SAMPLE`
  over the last 8 minutes: 50.8%→78.5%→50.4%→70.1%→39.3%→67.5%→10.5%→...→71.1%) is **oscillating, not monotonically
  climbing** — this is the healthy per-date-cleanup signature, distinct from the broken default-chunk-size VM's
  cumulative-growth pattern from two ticks ago. No action needed; continuing to watch since this VM's single chunk spans
  8+ months uninterrupted (no 5-day respawn safety net like the sibling VM has), so it remains the more theoretically
  exposed of the two, just not currently showing distress.
- **2026-08-07T13:38Z — `mtds-backfill-odds-401-retry` finally OOM'd, but this is the GOOD failure mode, not a repeat of
  the earlier bad one.**
  `CHUNK_FAILED: chunk=1/2 league=EPL range=2025-09-01→2026-05-08 exit=137 reason=OOM_KILLED time=2026-08-07T13:31:29Z`
  — EPL's single 8-month chunk finally hit the ceiling, but only after covering the overwhelming majority of the range
  (Sept 2025 through ~March 2026 already confirmed captured in prior ticks' checks, written incrementally via
  `ManifestWriter` per-date, not held in memory — that data is durable regardless of the crash). The wrapping
  `mtds_chunk_loop.sh` correctly caught the failure and **auto-recovered by moving to the next league (LA_LIGA)** rather
  than freezing — exactly the "fail-loud, self-recovering" design
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` documents working correctly for chunk-level failures. No
  manual intervention taken; letting it continue through the remaining leagues. **Residual gap to track**: EPL's tail
  (~2026-03 through 2026-05-08, the portion after the last confirmed-captured date) may still need a narrow follow-up
  retry once this VM finishes its full league sweep — added as a todo below rather than acting now, since the sweep
  isn't done yet and a premature narrow retry would just get re-covered by the eventual full-range small-chunk VM
  anyway. `mtds-backfill-odds-smallchunk-20260807` remains fully clean: 0 `CHUNK_FAILED`/`OOM_KILLED` matches, now at
  chunk 13/451 (`2020-08-05→2020-08-09`).
- **2026-08-07T14:17Z — `401-retry` OOM'd 5 more times (6 total), but produced a genuinely useful diagnostic, not just
  churn.** Precise timing: EPL (first subprocess this VM's lifetime) survived 93.3 min; every subsequent league
  (LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1, EREDIVISIE) OOM'd in a tight 6.5-8.9 min band — too consistent across leagues
  with genuinely different real-fetch densities to be pure per-process real-fetch-volume variance, suggesting something
  persists across subprocess launches within one VM lifetime (candidate mechanisms + full writeup added to
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`'s Progress Log — not investigated further here, out of scope
  for an operational tick). No data lost (per-date incremental writes are durable); self-recovery continues working
  correctly (now on PRIMEIRA_LIGA). Not killing it — still net-positive real progress each cycle. AF campaign
  PLAYER_STATS now at **chunk 24/26** (only 2 left). footystats (2024-09-22→2025-04-06), SFI (2021-11-02→2022-03-11),
  weather (→2026-07-25), `mtds-backfill-odds-smallchunk-20260807` (chunk 17/451, still 0 OOM) all confirmed healthy via
  value-diffs.
- **2026-08-07T14:47Z — CORRECTION: weather backfill finished (exit_code=0, self-deleted) but did NOT actually resolve
  the honest-coverage gap — do not read `exit_code=0` as "done" (exactly the trap codex rule 4a warns about).**
  `weather-backfill-20260807-120241` reached `last_completed_date=2026-08-07` (the full range end) and exited cleanly,
  but a fresh census shows: `expected_unattempted` barely moved (205,517 → 205,302, only -215) and **16,241 NEW
  `attempted_failed` rows appeared** (`error_reason=ClientResponseError`, spread across ~478 distinct dates from
  2024-01-03 to 2026-08-07 — not a narrow today-only edge case, a genuine broad vendor-API issue; the tail log showed
  the concrete signature: `400 Bad Request` against
  `customer-previous-runs-api.open-meteo.com/v1/forecast?...&previous_day1&...`). Also confirmed the remaining
  `expected_unattempted` rows span the FULL date range including recent dates (e.g. 2026-07-28: 350 rows on a single
  date) — meaning many (date, venue) shards were never even attempted despite the date-loop completing, a separate
  puzzle from the `ClientResponseError` cluster. **Two genuinely new, unresolved findings, not a closed line item**: (1)
  root-cause the `customer-previous-runs` 400 errors (vendor contract issue? request malformed for certain date/venue
  combos?); (2) explain why so many shards remain fully untouched despite the date-iteration reaching the full range (a
  skip-condition false-positive, a per-venue sub-loop bug, or a rate-limit silently short-circuiting without recording
  `attempted_failed`?). Neither investigated further this tick — flagging clearly rather than claiming a false win.
  `mtds-backfill-odds-smallchunk-20260807` had its first OOM this tick (chunk 18/451, EPL, `exit=137`) but
  self-recovered correctly (moved to LA_LIGA) — 1 failure in 18 chunks, consistent with (better than) the OOM doc's own
  "4/75 chunks" precedent for `--chunk-size 5`, not concerning. `401-retry`'s per-league OOM cadence holds steady at
  ~6-9 min (4 more failures: PRIMEIRA_LIGA, JUPILER_PRO, SUPER_LIG, SCOTTISH_PREMIERSHIP; now on GREEK_SUPER_LEAGUE, 10
  total) — stable, not degrading further, no action needed.
- **2026-08-07 (slot 4) — Root-caused and fixed weather's 16,241 `ClientResponseError` rows
  (`instruments-service@1fafbe23`).** Root cause: inside `OpenMeteoAdapter.get_weather_match_window`, the inner `except`
  block for the `customer-previous-runs-api.open-meteo.com` call (lines 154-162) had a spurious `raise` that propagated
  the 400 Bad Request upward, aborting the entire fetch. The adapter's OWN comment at line 136 already stated the
  correct intent ("if Previous Runs API is down, skip forecasts and still get actuals"), but the `raise` contradicted it
  — so every date ≥ 2024-01-01 where the customer previous-runs endpoint returned 400 became an `attempted_failed` row
  instead of getting actual weather from the archive/forecast endpoint. Fix: removed `raise`; added regression test
  `test_prev_runs_400_falls_back_to_actuals` in `test_open_meteo_adapter_coverage.py` and updated
  `test_previous_runs_api_exception_propagates` (renamed, docstring and `call_count` assertion corrected). QG green. On
  the next weather backfill run, the 16,241 shards will be re-touched; they should resolve to `captured` (venues with
  weather data) or `empty_confirmed` (venues with no data) rather than `attempted_failed`.
- **2026-08-07 (slot 7) — Root-caused why weather's `expected_unattempted` barely moved (205,517→205,302, -215).**
  Confirmed via code inspection of `weather.py` +
  `instruments-service/scripts/type_weather_eu_no_provider_coverage_2026_06_27.py`. **Not** a skip-condition
  false-positive or per-venue sub-loop bug. Definitive finding: `_fetch_weather_data` builds
  `_expected_weather_league_ids` using `get_expected_leagues_for_source("open_meteo", classifications=["Prediction"])` —
  only ~33 leagues. All write paths (season-window guard → `record_expected_empty` → `EMPTY_CONFIRMED`; coverage-start
  guard; `_record_weather_empty`; `_record_weather_failed`; end-of-function EXPECTED_NO_FIXTURE loop) write exclusively
  for league_ids in that 33-league set. The 205K `expected_unattempted` rows are for the ~172 non-Prediction leagues
  seeded historically (dates 2026-02-20→2026-06-26, documented in the existing one-off script's own docstring) by an
  older weather VM that used a broader league set. Since the backfill never emits ANY manifest entry for non-Prediction
  leagues — not captured, not empty_confirmed, not attempted_failed — those rows are structurally unreachable by the
  weather writer regardless of date range. The -215 reduction = 215 Prediction-league rows that happened to still be
  expected_unattempted and got resolved. The 350 rows on 2026-07-28 are for non-Prediction leagues, untouched by design.
  Resolution path: `instruments-service/scripts/type_weather_eu_no_provider_coverage_2026_06_27.py --apply`
  (reclassifies to `empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE)`) + consolidator pass — separate action, not this
  task.
- **2026-08-07T16:53Z** — **footystats' 50-league backfill VERIFIED cleanly done** (re-census, not just `exit_code=0`):
  0 `attempted_failed`, 0 `expected_unattempted` both before and after; +2,383 captured / +8,088 empty_confirmed for the
  18 newly-widened leagues. First VM this session to converge with zero loose ends — the footystats line item in the
  priority table above can be considered closed. FIXTURE_STATS (AF-doc scope, cross-referenced) is doing a full
  skip-fast sweep from 2020-06-06 rather than literally resuming from a checkpoint — expected, not a bug, just slower
  wall-clock. All other VMs (SFI, both odds VMs) confirmed healthy via value-diffs, consistent with established patterns
  — no new incidents.
- **2026-08-07T17:18Z — found + fixed a real stale-code problem: `mtds-backfill-odds-smallchunk-20260807` was running ~5
  hours of PRE-FIX code past the SOURCE_RETURNED_ZERO fix landing.** Investigating `401-retry`'s SPOT preemption (clean,
  expected — `compute.instances.preempted` at 16:55:35Z, right after its last log line, not an app bug) surfaced
  something bigger: odds_api `attempted_failed` had grown to 26,934 (from 13,916), and the original 871 stale-401 rows
  were STILL completely untouched despite hours of VM runtime. Root cause: the SOURCE_RETURNED_ZERO fix
  (`market-tick-data-service@70f13166`) landed at **2026-08-07T12:19:49Z**, but both odds VMs I'd launched (`401-retry`
  at 04:55:46Z, `smallchunk` at 05:39:59Z) started HOURS before that — their baked tarballs simply predate the fix's
  existence, so the launch-time freshness check had nothing to catch (the fix didn't exist yet at launch). `smallchunk`
  was still running live with the stale tarball, actively generating **13,025 NEW SOURCE_RETURNED_ZERO
  `attempted_failed` rows since the fix landed** (verified via `attempted_at` timestamps, split cleanly pre/post-fix at
  ~13,038/~13,025). Checked `scripts/reset_source_returned_zero_manifest.py` as a candidate remediation — doesn't apply,
  it targets a different pattern (`capture_status=empty_confirmed` fake-empties, not `attempted_failed` rows; ours are
  correctly classified, just need re-attempting with fixed code). Killed `smallchunk`, relaunched as
  `mtds-backfill-odds-smallchunk2-20260807` (`--chunk-size 5`, no `--force`), verified via
  `git merge-base --is-ancestor` that the new tarball's commit (`52d6da40`) genuinely includes the fix. Going forward:
  `attempted_failed` is not in this pipeline's skip-set, so the relaunch will naturally re-attempt all 26,934 rows
  including the original 871 stale-401s. **Lesson for future launches**: a VM's tarball freshness is only checked
  against the repo at LAUNCH TIME — a long-running VM (hours+) can silently drift stale if a relevant fix lands mid-run;
  for any multi-hour backfill, worth a mid-run check of whether a relevant fix has landed since launch, not just a
  freshness check at launch.
- **2026-08-07T18:05Z (slot 4) — Understat expected_unattempted P3 investigation CLOSED: confirmed live-cron artifact.**
  Ran `census_understat_expected_unattempted_2026_08_07.py` (instruments-service@1ebc2ca9, bounded, read 9,595,128
  manifest rows). Result: **25 rows** remain (post China/Russia purge from 30), all dated 2026-08-05→2026-08-07, all
  venue="" (blank), data_type=XG (10) and XG_SHOTS (15). Code inspection of `engine/orchestrator/understat.py` confirms:
  `expected_unattempted` rows are seeded by the production IS cron for recent fixture shards before the daily pass
  processes them; the empty venue is the standard "not yet processed" signature. No understat backfill VM was running.
  No corrective action needed — these 25 rows resolve naturally on the next daily IS cron cycle.
- **2026-08-07T20:03Z (slot 13) — EPL odds_api tail re-census completed; narrow retry NOT launched.** Ran
  `census_epl_odds_api_attempted_failed_2026_08_07.py` (instruments-service@ca437ed3). Result: 206 EPL
  `attempted_failed` rows across date range 2020-10-06→2026-08-06 (most recent `attempted_at`=2026-08-07T16:51Z).
  Breakdown: **23 UNCLASSIFIED:401** (stale-credential window 2025-09→2026-05, the original 401-retry target) + **183
  SOURCE_RETURNED_ZERO** (created by old unfixed `smallchunk` VM before it was killed at 17:18Z; will resolve with fixed
  code). Narrow retry NOT launched: `401-retry` was preempted (SPOT) at 16:55Z before finishing its league sweep, but
  `mtds-backfill-odds-smallchunk2-20260807` (full range 2020-06-06→2026-08-07, 5-day chunks, fixed SOURCE_RETURNED_ZERO
  code as of commit `52d6da40`) is running and will naturally re-attempt all 206 rows when its sweep reaches EPL's date
  ranges — consistent with the todo's own rationale. VM confirmed active at 20:00Z (chunk 18/451, EREDIVISIE 2020-08,
  memory oscillating 5-71%, no monotonic growth).
- **2026-08-07T21:16Z — MILESTONE: SFI genuinely converged (verified via re-census, rule 4a), AND both weather's + SFI's
  `expected_unattempted` backlogs (410,665 rows combined) are now correctly reclassified.**
  `sfi-backfill-20260807-123519` reached `last_completed_date=2026-08-07` (full range end), `exit_code=0`, self-deleted.
  Re-census showed the SAME pattern weather hit: `expected_unattempted` completely unchanged (205,363→205,363, zero
  movement) plus 80 new `attempted_failed` rows — exit_code=0 again did NOT mean the gap resolved (rule 4a validated a
  second time). Root-cause verification: **zero overlap** between SFI's 33 captured leagues (≈ its 34-league
  Prediction-tier write scope) and the 350 leagues comprising the stuck backlog — those 205,363 rows were seeded
  historically by a broader-scope run and are structurally unreachable by the current narrower-scope writer, no matter
  how many times it's re-run. Exact same pattern as weather (already diagnosed by another worker, "slot 7," but its own
  remediation script had never actually been RUN). Found the sanctioned, already-built, precedent-tested fix for both:
  `scripts/type_sfi_eu_no_provider_coverage_2026_06_27.py` and
  `scripts/type_weather_eu_no_provider_coverage_2026_06_27.py` (dated 2026-06-27, correctness-fixed 2026-07-08 to
  exclude genuinely-covered leagues from the retype) — both reclassify `expected_unattempted` + blank-reason +
  non-covered-league rows to `empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE)`, writing ONLY an additive per-VM shard
  (never touching the canonical index directly — the consolidator's last-write-wins merge picks up the retype next
  cycle, so this is much lower-risk than a canonical-index rewrite). Ran both dry-run then `--apply`: SFI 205,363 rows
  retyped (`type-sfi-eu-1786133580.parquet`), weather 205,302 rows retyped (`type-weather-eu-1786133699.parquet`).
  **Pending the next manifest-consolidator cycle to actually land in the canonical index** — the live
  `expected_unattempted` count will still read the old figures until that merge completes; re-verify next tick. The 80
  new SFI `attempted_failed` rows and weather's pre-existing 16,241 (already root-caused + code-fixed earlier this
  session) are separate, smaller residuals, not touched by this reclassification.
- **2026-08-07T20:47Z — CONFIRMED: the consolidator merge landed, both sources genuinely converged.** Re-census (rule
  4a, live manifest re-read, not assumed): `soccer_football_info` — `empty_confirmed` 208,726→**414,173** (+205,447,
  matching the retype), `expected_unattempted` **completely gone** (0 rows, was 205,363), `captured` 20,953,
  `attempted_failed` unchanged at 80. `open_meteo` — `empty_confirmed` 215,865→**421,167** (+205,302, an EXACT match to
  the retype count), `expected_unattempted` **completely gone** (0 rows, was 205,302), `captured` 28,698,
  `attempted_failed` unchanged at 16,241 (the already-tracked, separately-fixed residual). Both sources are now down to
  just `captured` + `empty_confirmed` + a small, already-diagnosed `attempted_failed` tail — this is genuinely,
  verifiably the operator's original target state for these two vendors. `mtds-backfill-odds-smallchunk2-20260807`
  (chunk 18/451, now 6 OOM total — checked the actual league list: EPL, EREDIVISIE, PRIMEIRA_LIGA, JUPILER_PRO,
  SUPER_LIG, GREEK_SUPER_LEAGUE, six DIFFERENT leagues each failing once and self-recovering, not a stuck repeat —
  consistent with the established tolerable pattern, watching but not intervening) and FIXTURE_STATS (chunk 6/26,
  2021-10-14) both remain healthy.
- **2026-08-07T21:22Z — smallchunk2 odds STILL on chunk 18/451, now confirmed 10/18 leagues OOM'd (55%) — root-caused as
  genuine per-league progress, not a stall (full detail + league list in
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`@`b90338bfd9`).** PROGRESS.json's `last_completed_date`
  reading (`2020-08-29`, `updated=19:22:22Z`) looked 2h-stale at first glance — this is exactly the rule-1b check case,
  so read the full `run.log` (not just PROGRESS.json) rather than concluding either way from the checkpoint alone:
  confirmed 18 DISTINCT leagues attempted this chunk (EPL...BRASILEIRAO, zero repeats), EKSTRAKLASA fully completed, the
  other 10 OOM'd once each and correctly advanced (self-recovery intact). Verdict: not a stall, PROGRESS.json simply
  checkpoints at the whole-chunk boundary and this specific 2020-08-30→2020-09-03 range (a genuine European
  season-opener window) is unusually failure-prone. FIXTURE_STATS re-checked same tick: `last_completed_date=2021-11-19`
  (up from 2021-11-06), `updated=21:22:14Z` (fresh) — healthy, no action needed. No intervention on either VM this tick.
- **2026-08-07T21:53Z — FIXTURE_STATS jumped 89 days** (`last_completed_date=2022-02-16`, was `2021-11-19`,
  `updated=21:52:23Z` fresh) — healthy, accelerating. **smallchunk2 odds STILL on chunk 18/451** (PROGRESS.json
  checkpoint unchanged, `2020-08-29`/`19:22:22Z` — now 2.5h stale on the checkpoint alone), but `run.log` confirms
  continued genuine progress: 22 distinct leagues attempted this chunk now (up from 18), currently on `J1_LEAGUE`,
  actively running (RSS cycling 10-23GiB normally, no stuck/frozen process), 12 total OOMs (up from 10, still zero
  repeats — each OOM'd league only failed once). This chunk has now run ~2h40m; not yet escalating — self-recovery
  remains intact and every restart is still doing real, distinct work, but flagging for whoever next touches this: if
  it's still on chunk 18 at the NEXT tick, that would be a genuine outlier worth deeper thought (e.g. whether the full
  league roster for this chunk is unusually long, not just unusually OOM-prone).
- **2026-08-07T22:21Z — followed up on the flagged outlier: STILL on chunk 18/451 (~3h now), but confirmed this is the
  roster being genuinely large for this specific week, not malfunction.** FIXTURE_STATS:
  `last_completed_date=2022-04-06` (up from 2022-02-16, +49 days), fresh checkpoint (`22:20:25Z`) — healthy, continuing
  to accelerate, no action needed. odds smallchunk2: full `run.log` re-read (rule 1b) shows **25 distinct leagues
  attempted this chunk now** (up from 22 last tick — EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1, EREDIVISIE,
  PRIMEIRA_LIGA, JUPILER_PRO, SUPER_LIG, SCOTTISH_PREMIERSHIP, GREEK_SUPER_LEAGUE, AUSTRIAN_BUNDESLIGA,
  SWISS_SUPER_LEAGUE, DANISH_SUPERLIGA, ELITESERIEN, EKSTRAKLASA, ALLSVENSKAN, BRASILEIRAO, ARGENTINA_PRIMERA, MLS,
  J1_LEAGUE, CHILE_PRIMERA, LIGA_MX, K_LEAGUE_1, A_LEAGUE — spanning Europe, South America, Asia, North America,
  Oceania), still **zero repeats**, 13 total OOMs (+1 since last tick, LIGA_MX). This spread (multiple continents' top
  flights all represented) plus the fact the chunk is STILL not exhausted after 25 leagues strongly suggests the
  Prediction-tier roster is simply large and this 2020-08-30→2020-09-03 week is the first chunk since the 2020-06-06
  range start where essentially every league worldwide has a real season-opener fixture simultaneously — i.e. this may
  be close to a full-roster real-fetch pass in one chunk, something later/earlier chunks in off-season weeks won't
  repeat. Not a stall by rule 1b's own test (values keep climbing every tick); no intervention — self-recovery, zero
  data loss, genuinely converging.
- **2026-08-07T22:50Z** — FIXTURE_STATS +45 days (`last_completed_date=2022-05-21`, fresh `22:49:35Z`), steady. odds
  smallchunk2 STILL chunk 18/451 (~3.5h) — lighter rule-1b diff (root cause already established, not re-litigating): 29
  distinct leagues now (up from 25), 15 OOM (up from 13), still zero repeats, RSS cycling normally — continued genuine
  movement, no intervention.
- **2026-08-07T23:17Z — CLOSED: chunk 18/451 finally cleared. FIXTURE_STATS +72 days.** FIXTURE_STATS:
  `last_completed_date=2022-08-01` (fresh `23:16:40Z`), continuing to accelerate. odds smallchunk2: `run.log`'s own
  `PROGRESS: chunk=18/451 ... time=2026-08-07T22:59:42Z` line confirms the chunk completed — total elapsed **3h38m**
  (started 19:21:28Z per chunk 17's completion line), final tally **30 distinct leagues attempted, 16 OOM'd once each
  (14 succeeded clean on first try)**, zero repeats throughout — closes out the season-opener-week investigation as
  designed-behavior, not a bug. Chunk 19 (`2020-09-04→2020-09-08`) is already under way and moving fast — its first
  league is skip-fasting through dates (`SKIP date=2020-09-04/05/06`), confirming the off-season-weeks-move-faster
  hypothesis. **New finding for future ticks**: `PROGRESS.json` itself did NOT update at the chunk-18→19 transition — it
  still read the stale `2020-08-29`/`19:22:22Z` value even ~18 minutes after chunk 18's own `run.log` completion line.
  The true checkpoint state must be cross-checked against `run.log`'s own `PROGRESS: chunk=N` lines near a suspected
  chunk boundary, not trusted from `PROGRESS.json` alone — worth a rule-1b/4a addendum if this recurs. Reverting to
  lightweight per-tick `PROGRESS.json` checks per the standing instruction, since the outlier is now closed; will only
  re-deep-dive if a future chunk shows the same multi-hour-stall signature.
- **2026-08-07T23:17Z — self-correction: FIXTURE_STATS's chunk NUMBER had gone stale in the journal for several ticks.**
  Every tick's `last_completed_date` reading was genuinely accurate (each one re-fetched live), but I'd been carrying
  forward the label "chunk 6/26" from an early tick without re-verifying it against `run.log` — a live check just now
  shows it's actually **chunk 9/26** (`2022-05-27→2022-08-24`, chunks 6-8 each cleared in well under an hour: chunk 6 @
  21:25:10Z, chunk 7 @ 21:56:53Z, chunk 8 @ 22:51:26Z). No data-integrity issue — the underlying values were never
  wrong, only the derived chunk-number label I was echoing. At this clip (~3-9 chunks/hour once past quota-limited early
  chunks), 26/26 is plausibly within the next 1-3 hours. Using the verified chunk 9/26 going forward.
- **2026-08-07T23:47Z — upgrading last tick's `PROGRESS.json` finding: it's not lag, the file appears to have STOPPED
  updating entirely for odds smallchunk2.** FIXTURE_STATS: +30 days (`last_completed_date=2022-08-31`, fresh
  `23:46:43Z`) — a bit slower than recent ticks but healthy. odds smallchunk2: `PROGRESS.json` still reads the exact
  same stale value as 4.5 hours ago (`2020-08-29`/`19:22:22Z`, chunk 17's write), but `run.log`'s own
  `PROGRESS: chunk=N` lines prove real progress has continued well past the last tick's finding: **chunk 19 @ 23:18:02Z,
  chunk 20 @ 23:24:10Z, chunk 21 @ 23:30:17Z — each cleared in ~6 minutes**, currently on **chunk 22/451**
  (`2020-09-19→2020-09-23`), zero new OOMs since chunk 18 closed (still 16 total). This confirms two things at once: (1)
  the season-opener week really was the sole outlier — normal off-season chunks fly through in ~6 min once the league
  roster is mostly skip-fast/cheap real-fetches, and (2) `PROGRESS.json`'s GCS upload for this VM has not written a
  single new value since chunk 17 (19:22:22Z) despite 5 more chunks completing since — this is no longer "lag," it looks
  like the upload step itself stopped functioning for this file specifically (the VM is otherwise clearly alive:
  `run.log` keeps growing, manifest shards keep writing, heartbeats keep firing). **Not blocking** — `run.log`'s own
  `PROGRESS: chunk=N` lines are a fully reliable substitute and this doc will use them as ground truth for this VM going
  forward — but worth a note in `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` for whoever next touches the
  launcher, since a future session trusting `PROGRESS.json` alone on this specific VM would wrongly conclude it's been
  stuck since 19:22Z.
- **2026-08-08T00:16Z** — FIXTURE_STATS +29 days (`last_completed_date=2022-09-29`, fresh `00:15:42Z`), steady. odds
  smallchunk2 (via `run.log`, `PROGRESS.json` still not used per above): now **chunk 25/451** (`2020-10-04`), up from
  chunk 22 — chunks 23 (00:07:19Z) and 24 (00:13:41Z) both cleared, zero new OOMs (still 16 total since chunk 18). Both
  VMs healthy, no intervention.
- **2026-08-08T01:24Z (slot 14)** — **Recurrence of the exact killed-and-tagged anti-pattern: a second Transfermarkt
  backfill VM was launched blind, 13h into the still-ongoing outage, and got stuck the same way.** Dispatched
  `sports_satellite_ao_dispatch_batch9-002` (the golden-window PLAYER_VALUES relaunch todo) and found
  `tm-backfill-20260807-233040` already RUNNING (launched 2026-08-07T23:30:47Z, exact matching scope:
  `--sports-entity PLAYER_VALUES --sports-provider TRANSFERMARKT --start-date 2025-09-01 --end-date 2025-11-30`, no
  `--force`) — some earlier session/dispatch launched it without checking this doc's BLOCKED-UPSTREAM-OUTAGE tag first.
  `run.log` showed the identical signature this doc already diagnosed at 10:17Z the day before:
  `transfermarkt_teams_fetch` cycling through leagues, each one exhausting all 10 retry-with-backoff attempts against
  `GET /api/v1/competitions/standings` (HTTP 502 every time), ~10 min/league, **zero rows written and zero leagues
  captured across 1h45m** (23:33Z→01:16Z). Direct-probed the endpoint myself with the adapter's real params
  (`id=GB1&season=2025`, not the malformed query I tried first which returned a fast 422 from RapidAPI's gateway itself)
  — still **HTTP 502, ~52s latency**, confirming the outage is continuous and now 15h+ old (started 2026-08-07T10:17Z).
  Killed `tm-backfill-20260807-233040` (`gcloud compute instances delete`, confirmed via heartbeat-blob freshness +
  run.log zero-progress — same justified-stale basis as the original 2h17m kill this doc already recorded), matching
  this doc's own standing guidance rather than letting it burn further GCE billing against a call that cannot succeed.
  Did **not** relaunch. `sports_satellite_ao_dispatch_batch9_2026_08_04.md` todo 2 stays unchecked, annotated with this
  citation — real completion requires the vendor endpoint to recover first. **Lesson for future dispatches**: any
  Transfermarkt PLAYER_VALUES/TEAM launcher todo should grep this doc (or its `BLOCKED-UPSTREAM-OUTAGE` tag) for a live
  outage before launching, not just check the launcher's own singleton lock — the singleton lock only prevents a
  _second_ concurrent VM, it doesn't stop the _first_ one from launching blind into a known-dead endpoint.
- **2026-08-08T00:16Z-02:46Z — long tick: (1) FIXTURE_STATS confirmed chunk 12/26 @ `2023-03-05`, (2) odds smallchunk2
  found DELETED with no explanation, root-caused as an external forced-kill (not self-delete-on-exit, not OOM, not
  preemption), real progress preserved through chunk 25/451, and RELAUNCHED as `smallchunk3`.** FIXTURE_STATS:
  `PROGRESS.json` read via direct HTTPS GET (see below) shows `last_completed_date=2023-03-05`, `run.log`'s own
  `PROGRESS: chunk=11/26 range=2022-11-23→2023-02-20 time=2026-08-08T02:00:13Z` +
  `--- Chunk 12/26: 2023-02-21 → 2023-05-21 ---` confirms **chunk 12/26**, actively processing `date=2023-03-06` with
  real API calls succeeding — healthy, no action needed. **Tooling note (not a durable lesson, just this tick's
  noise)**: `gcloud storage cat`/`cp` intermittently failed for over an hour with THREE different error types in
  sequence (404, network error, 401) on files that `gcloud storage ls -L` proved existed and were being freshly written
  (`Update Time` matched real recent activity) — worked around via a direct HTTPS GET
  (`curl -H "Authorization: Bearer $(gcloud auth print-access-token ...)" "https://storage.googleapis.com/storage/v1/b/<bucket>/o/<url-encoded-path>?alt=media"`,
  optionally with a `Range:` header for large files), which worked reliably throughout. Resolved on its own by ~02:44Z
  (plain `gcloud storage cat` worked normally again for the relaunch verification below). <br><br>**odds smallchunk2
  deletion**: `gcloud compute operations list` showed `delete` ops at `00:55:20Z` and `00:56:15Z`,
  principal=`1060025368044-compute@developer.gserviceaccount.com` (the shared automation SA — not attributable to a
  specific human or session from this alone). `run.log`'s GCS object `Update Time` metadata (`00:37:08Z`) confirms the
  file genuinely stopped growing ~18 min before the delete, mid-chunk-26 (`league=EPL, 2020-10-09→2020-10-13`), ending
  on an ordinary `RESOURCE_SAMPLE` line — **no terminal `exit_code=` line, no `Traceback`, no `CHUNK_FAILED`, no
  completion marker**, which per `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`'s "Self-deleting VM/job"
  rule (a graceful self-delete-on-exit writes the terminal exit_code to `run.log` _before_ destroying itself) means this
  does **not** match the VM's own normal self-delete-on-completion-or-crash behavior — it looks like an external forced
  deletion. No entry anywhere in this doc from another worker/slot claims responsibility (checked full-doc grep for
  "smallchunk2"). **Not proof of completion either way** (rule 4a) — real confirmed progress stops at chunk 25/451
  (`2020-10-08`), 426 chunks still remaining, nowhere near done. **Recovery**: `odds-api-concurrency-guard.sh` confirmed
  0 running odds VMs (cap=1, would permit a relaunch), so relaunched immediately with the identical params
  (`START_DATE=2020-06-06 END_DATE=2026-08-07 CHUNK_SIZE=5`, tarballs verified fresh incl.
  `market-tick-data-service@0e40bc53b168`) as **`mtds-backfill-odds-smallchunk3-20260808`** — guard passed
  (`0 running + 1 planned = 1 <= cap 1`), VM created RUNNING, verified booted and correctly skip-fasting through
  already-covered dates (`chunk 1/451`, ~7s/league) confirming zero data loss and correct resume behavior. Using
  `smallchunk3`'s `run.log` as ground truth going forward (same `PROGRESS.json`-may-lag caveat applies until proven
  otherwise on this new instance). **Open question, not investigated further**: who/what actually issued the delete —
  worth asking the operator or checking other slots' session logs if this pattern recurs, since an unexplained VM kill
  mid-run is exactly the kind of thing that should be attributable.
- **2026-08-08T03:15Z** — FIXTURE_STATS +80 days (`last_completed_date=2023-05-24`, fresh `03:14:21Z`), steady, roughly
  chunk 13/26 now. `smallchunk3` confirmed healthy via `run.log`: chunk 7/451 (`2020-07-06→2020-07-10`), chunks 1-6 each
  cleared in a steady ~4.5min (subprocess-bootstrap overhead across ~40-60 rostered leagues dominates even pure
  skip-fast dates — matches the earlier bootstrap-cost pattern seen on smallchunk2), zero OOMs so far (expected —
  skip-fast dates need minimal memory). At this pace, ETA to reach chunk 26 (`2020-10-09`, where real new work resumes
  past smallchunk2's last confirmed progress) is roughly another ~1h20m. Both VMs healthy, no intervention.
- **2026-08-08T03:43Z** — FIXTURE_STATS +72 days (`last_completed_date=2023-08-04`, fresh `03:41:29Z`), steady. odds
  smallchunk3: chunk 13/451 now (`2020-08-05`), up from chunk 7 — pace holding at ~4.5min/chunk, zero OOMs. ~13 chunks
  (~58 min) remaining to reach chunk 26. Both healthy, no intervention.
- **2026-08-08T04:10Z** — FIXTURE_STATS +30 days (`last_completed_date=2023-09-03`, fresh `04:09:26Z`), steady. odds
  smallchunk3: chunk 17/451 (`2020-08-25`), zero OOMs still. **Forward-looking note**: chunk 18
  (`2020-08-30→2020-09-03`) is next — the same season-opener week that took smallchunk2 3h38m with a 55% per-league OOM
  rate. Since smallchunk2 already durably captured ~14/30 of that window's leagues before dying (manifest writes survive
  VM death regardless of which VM wrote them), `smallchunk3` should skip-fast through those and only need real
  re-fetches for the ~16 leagues smallchunk2 left `attempted_failed` (EPL, EREDIVISIE, PRIMEIRA_LIGA, JUPILER_PRO,
  SUPER_LIG, GREEK_SUPER_LEAGUE, SWISS_SUPER_LEAGUE, DANISH_SUPERLIGA, ELITESERIEN, ALLSVENSKAN, and others per the
  earlier per-league tally) — expect SOME OOMs to resume there, but a materially shorter pass than the original ordeal.
  Not alarming if it happens; logging the expectation now so it reads as anticipated, not a new incident.
- **2026-08-08T04:38Z** — FIXTURE_STATS +47 days (`last_completed_date=2023-10-20`, fresh `04:37:30Z`), steady. odds
  smallchunk3: **now in chunk 18** (`2020-08-30→2020-09-03`, the known season-opener week), 4 leagues attempted so far
  (EPL, LA_LIGA, BUNDESLIGA, SERIE_A), **zero OOMs** — confirms the skip-fast-for-already-captured-leagues hypothesis
  from last tick, materially better than smallchunk2's original 55% OOM rate on this same chunk. Watching for it to
  clear; not alarming if OOMs do appear on the previously-`attempted_failed` leagues later in this chunk.
- **2026-08-08T05:05Z** — FIXTURE_STATS +49 days (`last_completed_date=2023-12-08`, fresh `05:04:33Z`), steady. odds
  smallchunk3: still in chunk 18, now **10 distinct leagues attempted, still zero OOMs** (~46 min into this chunk) — the
  skip-fast-plus-partial-real-fetch pattern is holding cleanly, just at the usual ~4.5min/league bootstrap-bound pace
  rather than a faster-than-normal clip; the real win is avoiding the wasted OOM-restart cycles entirely. Both healthy,
  no intervention.
- **2026-08-08T05:33Z — MAJOR (recurring): `smallchunk3` also died, second occurrence of the identical
  silent-hang-then-watchdog-kill pattern. New issue doc filed.** `smallchunk3` was gone from
  `gcloud compute instances list` entirely — not OOM (last RSS=8.6GiB, well below the ~28-31GiB OOM range), not the VM's
  own graceful self-delete (no terminal `exit_code=` line). `run.log` went silent at `05:05:17Z` (mid-chunk-18,
  `SCOTTISH_PREMIERSHIP` real-fetch), **the heartbeat blob itself also stopped updating** (`05:06:23Z`, confirmed via
  `gcloud storage ls -L`) — ruling out a watchdog false-positive against a still-alive VM (the documented 2026-07-18
  API-Football precedent) and pointing instead to a genuine ~20-minute hang that `vm_zombie_watchdog.py` correctly
  caught and killed (`delete` op at `05:26:25Z`). This is the SAME signature as `smallchunk2`'s death earlier this
  session (~19 min silent gap there too). Filed as a proper new issue since it's now a confirmed-recurring pattern, not
  investigated to root cause yet (would need to catch a live hang in progress via `py-spy`/`strace`, not post-mortem):
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`. No data loss — chunk 18's progress through
  `SCOTTISH_PREMIERSHIP` (10 leagues) is durable. Relaunched as **`mtds-backfill-odds-smallchunk4-20260808`** (guard
  passed, RUNNING, tarballs fresh); not yet verified booted this tick (checked too soon after launch — startup script
  was still extracting tarballs). FIXTURE_STATS unaffected, continuing healthy.
- **2026-08-08T05:57Z — smallchunk4 confirmed booted + healthy.** Chunk 4/451 (`2020-06-21`), zero OOMs, correctly
  skip-fasting through already-covered ground same as prior relaunches — no third occurrence yet (it's still well before
  chunk 18, where both prior deaths' real-fetch load was heaviest). FIXTURE_STATS jumped **98 days**
  (`last_completed_date=2024-03-15`, fresh `05:55:28Z`) — steadily accelerating toward chunk 26/26. Both healthy, no
  intervention.
- **2026-08-08T06:24Z** — FIXTURE_STATS +34 days (`last_completed_date=2024-04-18`, fresh `06:23:27Z`), steady. odds
  smallchunk4: chunk 10/451 now (`2020-07-21`), up from chunk 4, ~5min/chunk pace, zero OOMs — still no third
  occurrence, 8 chunks remaining before reaching chunk 18's known danger zone. Both healthy, no intervention.
- **2026-08-08T06:52Z** — FIXTURE_STATS +30 days (`last_completed_date=2024-05-18`, fresh `06:50:26Z`), steady. odds
  smallchunk4: chunk 15/451 now (`2020-08-15`), zero OOMs, ~5min/chunk pace holding — 3 chunks remaining before
  chunk 18. Both healthy, no intervention.
- **2026-08-08T07:22Z — smallchunk4 just entered chunk 18, the critical watch-point.** FIXTURE_STATS +69 days
  (`last_completed_date=2024-07-26`, fresh `07:21:37Z`), accelerating well. odds smallchunk4: chunk 17 cleared
  (`07:19:09Z`), now in **chunk 18** (`2020-08-30→2020-09-03`), 1 league attempted so far (`EPL`), zero OOMs total
  across the entire run. This is exactly where `smallchunk3` died last time — watching closely next tick.
- **2026-08-08T07:39Z — smallchunk4 SURVIVED the critical window, still alive and progressing through chunk 18.** 4
  leagues attempted so far (`EPL, LA_LIGA, BUNDESLIGA, SERIE_A`), zero OOMs total, actively logging as recently as ~90s
  ago — no third occurrence. Useful negative data point: this specific chunk can clear cleanly, so the hang isn't
  deterministically tied to chunk 18's content alone. FIXTURE_STATS +14 days (`last_completed_date=2024-08-09`, fresh
  `07:38:10Z`), still healthy. Continuing to watch until smallchunk4 is clearly into chunk 19+.
- **2026-08-08T08:13Z** — FIXTURE_STATS +35 days (`last_completed_date=2024-09-13`, fresh `08:11:18Z`), steady. odds
  smallchunk4: still chunk 18/451, now 2 OOMs total (up from 0) — normal self-recovery pattern (distinct leagues,
  correctly advancing), not the silent-hang signature (no total-silence gap observed). Both healthy, no intervention.
  **Also this tick**: dug into whether the AF entity chain (FIXTURE_STATS→FIXTURE_LINEUPS→INJURIES) could be
  parallelized per an operator ask — confirmed it cannot (real, previously-hit account-wide API-Football daily quota,
  launcher refuses a 2nd concurrent AF VM by design) — but confirmed via live AO backlog that 3 workers (slots 5, 7, 12)
  are already actively dispatched on `sports_taxonomy_p1`'s remaining P0 todos in parallel with this campaign, so
  parallelism is already maximized where it's genuinely available. No action needed on this doc from that finding.
- **2026-08-08T08:40Z — THIRD occurrence of odds smallchunk deletion, pattern now definitively confirmed.**
  `mtds-backfill-odds-smallchunk4-20260808` was gone from `gcloud compute instances list` entirely. Confirmed via
  `gcloud compute operations list`: `delete` op at `08:27:34Z`. `run.log` last real line `08:11:46Z` (mid-chunk-18,
  `AUSTRIAN_BUNDESLIGA`, RSS=24.4GiB — a third, very different RSS value, ruling out a memory-threshold trigger),
  heartbeat blob last update `08:11:31Z` — ~16 min silent gap, consistent with the prior two (~19min, ~20-21min). Same
  signature as before: no exit_code, no Traceback, no CHUNK_FAILED — a real hang, correctly caught by the watchdog.
  Updated `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md` in full (timeline table, bumped P2→P1,
  closed the "if a third occurrence" todo, opened a new one flagging the actual blocker for live diagnosis: this
  session's `gcloud compute ssh` via IAP is unauthorized, so catching a live hang with `py-spy`/`strace` isn't currently
  possible from here — needs a session/operator with working SSH access). No data loss — durable progress through chunk
  17 + partial chunk 18. Relaunched as **`mtds-backfill-odds-smallchunk5-20260808`** (guard passed, RUNNING).
  FIXTURE_STATS unaffected, continuing healthy.
- **2026-08-08T09:13Z** — FIXTURE_STATS +86 days (`last_completed_date=2024-12-08`, fresh `09:12:35Z`), accelerating
  well. odds smallchunk5: chunk 7/451 (`2020-07-06`), zero OOMs, healthy skip-fast pace — still well before chunk 18's
  danger zone. Both healthy, no intervention.
- **2026-08-08T09:40Z** — FIXTURE_STATS +71 days (`last_completed_date=2025-02-17`, fresh `09:39:39Z`), getting close to
  convergence. odds smallchunk5: chunk 12/451 (`2020-07-31`), zero OOMs, 6 chunks remaining before chunk 18. Both
  healthy, no intervention.
- **2026-08-08T10:07Z** — FIXTURE_STATS +49 days (`last_completed_date=2025-04-07`, fresh `10:06:41Z`). odds
  smallchunk5: chunk 17/451 (`2020-08-25`), zero OOMs — chunk 18 (2 of the 3 prior hang occurrences happened there)
  starts next. Watching closely next tick.
- **2026-08-08T10:29Z — smallchunk5 SURVIVED entering chunk 18, no 4th occurrence.** FIXTURE_STATS +34 days
  (`last_completed_date=2025-05-11`, fresh `10:28:32Z`), close to convergence. odds smallchunk5: 4 leagues attempted in
  chunk 18 (`EPL, LA_LIGA, BUNDESLIGA, SERIE_A`), 3 OOMs total (up from 0) with normal self-recovery, actively logging
  as recently as 25s ago. Both healthy, no intervention. Continuing to watch until clearly past chunk 18.
- **2026-08-08T10:51Z** — FIXTURE_STATS +70 days (`last_completed_date=2025-07-20`, fresh `10:50:24Z`), very close to
  its 2026-08-07 target end now. odds smallchunk5: still chunk 18, 11 distinct leagues attempted (zero repeats), 8 OOMs
  total (up from 3) with normal self-recovery, actively logging as recently as ~17s ago — no 4th occurrence. Both
  healthy, no intervention.
- **2026-08-08T11:13Z — operator invoked `/autonomous`, "finish everything," and left.** Continuing this loop under the
  autonomous completion contract (`cursor-configs/AUTONOMOUS_AGENT_RULES.md`) — no change to method, just no further
  per-tick user check-ins expected. FIXTURE_STATS +26 days (`last_completed_date=2025-08-15`, fresh `11:12:09Z`) — pace
  has accelerated sharply the last several ticks (enrichment-only mode, mostly-covered dates), likely converging within
  a few more ticks. odds smallchunk5: still chunk 18, 16 OOMs total (up from 8) but actively logging as recently as ~15s
  ago — genuinely alive, no hang signature. Both healthy, no intervention. Per rule 2 of the autonomous contract, also
  picking up the previously-parked cross-vendor honest-absence/denominator-hardening generalization ask as a scoped
  audit + documented proposal (not a unilateral architecture change) rather than leaving it `BLOCKED-OPERATOR` — will
  work this in as a parallel thread once the current milestone watch eases.
- **2026-08-08T~11:35Z — CLOSED: cross-vendor denominator-hardening ask.** Background audit (footystats, open_meteo,
  soccer_football_info, transfermarkt, understat — the 5 vendors the operator's original ask named, distinct from
  api_football/odds_api which have their own dedicated docs, and instruments_service/mdps_odds_horizon_bucket which are
  internal not vendors) found the generalization **already holds workspace-wide**: a fresh live census of all 9 sports
  manifest sources shows **0% blank-`error_reason` `empty_confirmed` rows everywhere**, not just the 5 — a direct
  downstream effect of the SFI/weather retype fixes landed earlier this session plus the other 3 vendors never having
  had the blank-reason problem. Per-vendor dominant reason codes: footystats `EXPECTED_NO_PROVIDER_COVERAGE` 70.8%,
  open_meteo 87.4%, SFI 85.7%, transfermarkt 92.1% (matches the original PLAYER_VALUES finding almost exactly),
  understat 97.9%. Checked for the SFI/weather-class `expected_unattempted` structural bug in all 5: only 3 residuals
  exist (open_meteo 384, SFI 350, understat 35), all dated `2026-08-05` through today — the already-diagnosed
  self-resolving in-progress-cron-shard pattern, not a new backlog. One candidate that looked structural — **footystats'
  891 `expected_unattempted` rows for CHINA_SUPER_LEAGUE + RUSSIA_PREMIER_LEAGUE** — resolved as honest, expected churn:
  the 2026-08-07 out-of-scope purge (`footystats_purge_out_of_scope_leagues_2026_08_07.py`) removed these leagues from
  subscription scope, and the full-history footystats backfill VM (`fs-backfill-20260807-100731`) is correctly
  re-sweeping the entire league universe, writing fresh honestly-typed `empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE)`
  rows as it passes over these 2 now-descoped leagues — same as every other non-subscribed league. **Not a bug, no
  action needed** — but noting here so a future tick doesn't mistake this for a live regression and attempt to re-purge
  rows that will just regenerate on the next full sweep. **No retype script run, no manifest purge performed** — nothing
  was found wrong to fix. Shipped the one genuine deliverable: two small codex/skill-doc additions codifying the
  "blank-reason-is-a-code-smell" principle for future vendors (`/codex/02-data/honest-absence-downstream-handling.md`
  Reason Taxonomy § principle 3, `cursor-configs/skills/data-pipeline-reconciliation/reference-sports.md` per-vendor
  audit step 6) — pushed `304041840e`. This closes the last standing item from the operator's original big-picture asks
  for this session.
- **2026-08-08T11:31Z** — FIXTURE_STATS +14 days (`last_completed_date=2025-08-29`, fresh `11:27:41Z`) — smaller jump
  this tick but still steady. odds smallchunk5: still chunk 18 (~70 min this pass now), 20 OOMs total (up from 16),
  actively logging as recently as ~2 min ago — no hang signature, continuing normal self-recovery. Both healthy, no
  intervention.
- **2026-08-08T11:53Z — smallchunk5 cleared chunk 18.** Chunk 18 took `10:20:04Z→11:51:19Z` (1h31m), 24 total OOMs this
  pass, zero hangs — now on **chunk 19/451** (`2020-09-04`), moving fast with skip-fast dates. FIXTURE_STATS +24 days
  (`last_completed_date=2025-09-22`, fresh `11:52:30Z`), steady. Both healthy, no intervention.
- **2026-08-08T12:15Z** — FIXTURE_STATS +25 days (`last_completed_date=2025-10-17`, fresh `12:15:18Z`), steady. odds
  smallchunk5: chunk 20/451 (`2020-09-09`), zero new OOMs since clearing chunk 18 (still 24 total). Both healthy, no
  intervention.
- **2026-08-08T12:37Z** — FIXTURE_STATS +18 days (`last_completed_date=2025-11-04`, fresh `12:37:03Z`), steady. odds
  smallchunk5: chunk 22/451 (`2020-09-19`), zero new OOMs (still 24 total). Both healthy, no intervention.
- **2026-08-08T12:59Z** — FIXTURE_STATS +26 days (`last_completed_date=2025-11-30`, fresh `12:58:49Z`), steady. odds
  smallchunk5: chunk 24/451 (`2020-09-29`), zero new OOMs (still 24 total). Both healthy, no intervention.
- **2026-08-08T13:21Z — FIXTURE_STATS crossed into 2026.** +34 days (`last_completed_date=2026-01-03`, fresh
  `13:20:37Z`) — very close to its 2026-08-07 target end now, likely just 1-2 chunks remaining. Watching very closely
  next tick. odds smallchunk5: chunk 25/451 (`2020-10-04`), 1 new OOM (25 total). Both healthy, no intervention.
- **2026-08-08T13:45Z — FIXTURE_STATS confirmed chunk 23/26, entering 24/26 (3 chunks remain, not 1-2 as estimated).**
  Verified via `run.log`'s own chunk markers: chunk 23 (`2025-11-07→2026-02-04`) done, now in chunk 24
  (`2026-02-05→2026-05-05`). `last_completed_date=2026-02-26`, fresh `13:37:06Z`. **odds smallchunk5 died — FOURTH
  occurrence**, this time at chunk 26 (`LA_LIGA`, RSS=13.5GiB), same ~17min silent-gap signature, no exit_code. This was
  smallchunk5's longest life yet (~5h27m) and furthest progress (cleared chunk 18 fully, then 8 more chunks to 26) —
  genuinely useful evidence downgrading the "chunk 18 is special" hypothesis toward a time-since-boot/cumulative-load
  trigger instead. Reconsidered pause-vs-relaunch seriously at 4 occurrences; decided to keep relaunching (empirically
  working — durable net progress every time, doesn't block anything). Relaunched as
  `mtds-backfill-odds-smallchunk6-20260808` (guard passed, confirmed RUNNING). Full detail + updated Timeline table:
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`@`179166cf88` (also resolved a git stash conflict
  with a concurrent na-eligibility-audit entry on that doc — both pieces of content preserved).
- **2026-08-08T14:02Z** — FIXTURE_STATS still chunk 24/26 (`2026-02-05→2026-05-05`), `last_completed_date=2026-04-09`
  fresh — **2 chunks remain (25, 26)**. odds smallchunk6: chunk 4/451 (`2020-06-21`), zero OOMs, healthy skip-fast pace.
  Both healthy, no intervention.
- **2026-08-08T14:19Z — FIXTURE_STATS entered chunk 25/26, the LAST chunk before it.** Chunk 24 completed `14:12:30Z`,
  now in chunk 25 (`2026-05-06→2026-08-03`) — only chunk 26 remains after this. odds smallchunk6: chunk 8/451
  (`2020-07-11`), zero OOMs, healthy. Both healthy, no intervention. Watching very closely next tick for FIXTURE_STATS's
  genuine convergence.
- **2026-08-08T14:36Z** — FIXTURE_STATS still in chunk 25/26, but very close to its end now
  (`last_completed_date=2026-07-17`, fresh `14:34:51Z`, vs chunk boundary `2026-08-03`) — likely converges within the
  next tick or two. odds smallchunk6: chunk 11/451 (`2020-07-26`), zero OOMs, healthy. Both healthy, no intervention.
  (Note: FIXTURE_STATS's `run.log` returned a transient 404 this tick before a retry succeeded — PROGRESS.json stayed
  reliable throughout, consistent with the earlier-documented GCS flakiness pattern, not a real signal.)
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
