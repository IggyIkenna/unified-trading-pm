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
2. **api_football — 35,058 attempted_failed** (STANDINGS 12,693 / FIXTURE_STATS 11,914 / FIXTURE_EVENTS 4,996 / TEAMS
   2,657 / FIXTURES_SCHEDULE 1,969 / FIXTURES 730 / PLAYER_STATS 77 / TRADES 4), **plus 658,426 expected_unattempted.**
   This overlaps heavily with `sports_af_full_entity_completion_2026_08_03.md`'s existing backfill todos (PLAYER_STATS/
   TEAMS/STANDINGS/INJURIES/FIXTURE_LINEUPS) — that doc's backfills, once run, should absorb most of the
   `expected_unattempted` figure; the `attempted_failed` clusters are a DIFFERENT lens (real failures, not just
   not-yet-attempted) and haven't been root-caused per-data_type yet. Don't duplicate that doc's todos here — this entry
   is a pointer + the reminder that `attempted_failed` needs its own root-cause pass distinct from the "needed" backfill
   counts already tracked there.
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
- [ ] [SCRIPT] P0. **Retry the odds_api 871 `401 Unauthorized` rows** with the current credential (no 401s recorded
      since 2026-07-27, so the key is presumably already fixed) — confirm, then targeted-retry those specific shards.
- [ ] [SCRIPT] P1. **Root-cause api_football's 35,058 attempted_failed** per data_type (STANDINGS/FIXTURE_STATS/
      FIXTURE_EVENTS/TEAMS/FIXTURES_SCHEDULE/FIXTURES/PLAYER_STATS) — distinct from the "needed" backfill counts already
      tracked in `sports_af_full_entity_completion_2026_08_03.md`.
- [ ] [SCRIPT] P1. **Launch the single, guard-respecting odds_api gap-backfill VM** (root cause already found + fixed;
      credential blocker retagged unblocked 2026-08-07) — see `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`
      P1/P2, which owns this; watch it through to an actual clean terminal state.
- [ ] [SCRIPT] P2. **Retry Transfermarkt's 8 attempted_failed PLAYER_VALUES rows** once
      `transfermarkt-football-data-api.p.rapidapi.com/api/v1/competitions/standings` recovers (durably 502ing as of
      2026-08-07T10:17Z) — check the endpoint before relaunching, don't blind-retry into the same wall.
- [ ] [SCRIPT] P2. **Launch weather (open_meteo) full backfill** for the 205,517 expected_unattempted shards.
- [ ] [SCRIPT] P2. **Launch SFI full backfill** for the 205,363 expected_unattempted shards (distinct from the
      already-resolved 89-row attempted_failed cluster).
- [ ] [SCRIPT] P3. **Understat 30-row expected_unattempted tail** — check if it's just an in-progress-run artifact.
- [ ] [SCRIPT] P2. **Out-of-scope audit pass** across every source — compare captured league/data_type combos against
      current UAC scope, looking for more footystats-China/Russia-style residue.
- [ ] [SCRIPT] P0. **Re-census this whole table once every item above lands** — confirm every source converges to
      `attempted_failed=0, expected_unattempted=0` (modulo genuine honest-absence floors), then this doc closes and the
      operator's "IS and MTDS 100% done" directive is genuinely met.

## Progress Log

- **2026-08-07T10:2XZ** — Doc created in response to the operator's scope-widening directive. Ran the first
  comprehensive per-source census (table above) — this is meaningfully bigger than the vendor-completion audit done
  earlier the same session suggested (that audit's "100% clean" verdict for weather/understat only checked
  `attempted_failed`, missing the `expected_unattempted` backlog entirely — corrected here). Diagnosed odds_api's two
  failure modes (stale-credential 401s vs. the live, still-recurring SOURCE_RETURNED_ZERO honest-coverage guard-rail
  rejection). Killed the stuck Transfermarkt retry VM after confirming 2h17m of zero progress against a durably-502ing
  vendor endpoint. No remediation done yet beyond what's already tracked in the AF doc — this tick was entirely
  discovery + scoping; next tick should start on the P0 odds_api items.
