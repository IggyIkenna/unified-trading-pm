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

- [ ] [SCRIPT] P0. **Investigate + fix the odds_api SOURCE_RETURNED_ZERO cluster** (13,045 rows, still recurring as of
      2026-08-06) — root-cause whether this is a genuine per-bookmaker vendor gap or an adapter/rate-limit bug; do not
      silently reclassify to `empty_confirmed`.
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
- [ ] [SCRIPT] P2. **Retry Transfermarkt's 8 attempted_failed PLAYER_VALUES rows** once
      `transfermarkt-football-data-api.p.rapidapi.com/api/v1/competitions/standings` recovers (durably 502ing as of
      2026-08-07T10:17Z) — check the endpoint before relaunching, don't blind-retry into the same wall.
- [x] ✅ [SCRIPT] P2. **Launched weather (open_meteo) full backfill** — `weather-backfill-20260807-120241`,
      `launch-openmeteo-backfill-vm.sh --entity WEATHER 2020-06-06 2026-08-07`, confirmed RUNNING (auto-republished a
      stale instruments-service tarball before create, then succeeded). Watch for completion + re-census next tick.
- [x] ✅ [SCRIPT] P2. **Launched SFI full backfill** — `sfi-backfill-20260807-123519` confirmed RUNNING
      (`launch-sfi-backfill-vm.sh --entity SFI_PROGRESSIVE_STATS 2020-06-06 2026-08-07`), targeting 205,363
      expected_unattempted shards (distinct from the already-resolved 89-row attempted_failed cluster).
- [ ] [SCRIPT] P3. **Understat 30-row expected_unattempted tail** — check if it's just an in-progress-run artifact.
- [ ] [SCRIPT] P2. **Out-of-scope audit pass** across every source — compare captured league/data_type combos against
      current UAC scope, looking for more footystats-China/Russia-style residue.
- [x] ✅ [SCRIPT] P0. **Re-census run 2026-08-07T11:57Z** (instruments-service@f917f04f,
      `scripts/census_all_sports_sources_2026_08_07.py`, 9,552,235 manifest rows post-floor) — VMs still running; not
      yet converged. Updated table below in Progress Log. Re-census needed once backfill VMs complete.

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
