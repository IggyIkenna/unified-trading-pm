---
doc_type: issue
title:
  "api_football enrichment gate has TWO previously-undiagnosed root causes on top of the already-fixed
  chronological-scan/watchdog issues: (1) captured FIXTURES rows frozen at status_short=NS forever block enrichment's
  completed-fixture lookup, so relaunching never resolves them; (2) the read_availability_index pending_fetch count is
  reader-path-dependent (column selection changes which shard files get merged), so the same query can report wildly
  different totals for the identical key"
summary:
  "Dispatched onto sports_p2_history_apifootball_2015_to_present-001 (the 20+-bounce full-history-enrichment todo).
  Confirmed the 4 VMs from the prior session's narrow-window redirect (af-backfill-20260718-16{1608,1641,1712,1740}) all
  completed exit_code=0 through their VM_END_DATE=2026-07-14. Re-ran the established
  query_api_football_pending_clusters_2026_07_18.py gate script: total pending_fetch STILL 6,925 — byte-for-byte
  identical to every prior read in this bounce history, despite the fleet running its full window to completion. Root
  cause 1 (NS-staleness): read the actual per-league FIXTURES parquets for the residual pending-cluster dates. The
  2026-06-24..2026-07-14 cluster (majority of FIXTURE_EVENTS/LINEUPS/STATS/PLAYER_STATS pending mass) is essentially
  100% status_short=NS (Not Started) in the captured FIXTURES data, even though these dates are now days to weeks in the
  past and the matches have obviously concluded in the real world. The 2026-02-21..2026-03-22 cluster is a 30-45%
  NS-stuck mix. `_read_fixture_ids_from_gcs` (instruments_service/engine/orchestrator/sports_fixtures.py:225) only
  treats status_short in {FT,AET,PEN} as 'completed' and enrichment can only ever act on completed fixture_ids — so for
  any date whose FIXTURES row was captured before kickoff/before the match finished and never re-fetched, enrichment
  logs '0 completed fixture IDs' and can NEVER make progress there, no matter how many times the fleet relaunches with
  the SAME (non-force) presence- skip semantics. There is no code path anywhere in this system that re-fetches FIXTURES
  to refresh a stale NS status once a row has been captured once. Verified the fix: a single `--sports-entity FIXTURES
  --force` CLI run for 2026-06-24 re-fetched fixtures live (picking up their now-final status) and cascaded into real
  enrichment writes in the same pass (814 fixture_events / 1936 fixture_lineups / 18 fixture_stats / 253 player_stats
  rows). Root cause 2 (reader inconsistency): read_availability_index's manifest reader falls back from the canonical
  consolidated blob to a per-VM-shard merge whenever the consolidated blob is >120s old (`_read_consolidated_if_fresh`
  in unified_trading_library/manifest_writer/_read_index.py:727). Two back-to-back reads for the IDENTICAL
  (date=2026-06-24, data_type=FIXTURE_EVENTS, source=api_football) key, differing only in whether `league_id` was in the
  requested `columns` list, returned utterly different distributions: without league_id — 189 total rows (captured=2,
  empty_confirmed=93, expected_unattempted=94); with league_id — 94 total rows, ALL expected_unattempted, 0
  captured/empty. Since every prior dispatch on this todo (20+) used exactly this reader/script to declare 'gate still
  failing, 6,925 pending, unchanged', and the underlying per-VM-shard-fallback merge behavior is
  column-selection-sensitive, the reliability of every one of those readings needs re-examination — it is plausible the
  true pending count has been silently drifting down (or has genuinely been static) but the measurement instrument
  itself cannot currently distinguish those cases when it falls into the fallback path."
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags:
  [
    sports,
    api-football,
    enrichment,
    honest-absence,
    data-correctness,
    manifest-consolidator,
    fixture-status,
    stale-cache,
  ]
related:
  [
    plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    plans/active/issues/api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md,
    plans/active/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md,
    plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md,
    codex/02-data/availability-manifest-and-data-status.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-19
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source: [data_engineering worker, slot 8, sports_p2_history_apifootball_2015_to_present-001 dispatch 2026-07-19]
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# api_football enrichment: stale-NS fixture status + gate reader inconsistency

> **NOTIFY-OPERATOR (big finding — data-correctness, cross-cutting, invalidates 20+ prior gate readings on
> `sports_p2_history_apifootball_2015_to_present-001`).** Two genuinely new, previously-undocumented root causes found
> this session, on top of the already-fixed zombie-watchdog-kill and chronological-scan issues tracked separately.
> Neither of these is fixed by "relaunch the fleet again."

## What I found

**Context**: dispatched onto the api_football full-history-enrichment todo (20+ bounces across 2 days). The prior
session's narrow-window redirect fleet (`af-backfill-20260718-16{1608,1641,1712,1740}`, `VM_START_DATE=2026-02-21`
`VM_END_DATE=2026-07-14`) had all 4 VMs complete cleanly (`exit_code=0`) overnight, per their own `run.log`s'
`DEPLOYMENT_COMPLETED` lines (19:50-20:09Z 2026-07-18).

**Root cause 1 — captured FIXTURES rows never get their status refreshed, so enrichment permanently sees "0 completed
fixture IDs" for a whole class of dates.**

`_read_fixture_ids_from_gcs` (`instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py:225-251`)
reads the already-captured FIXTURES parquet for a date and filters `status_short.isin({"FT","AET","PEN"})` to decide
which fixture_ids are "completed" and therefore eligible for per-fixture enrichment (events/lineups/stats/player_stats).
Direct parquet reads of the captured FIXTURES data show:

| date range                                                                                        | status_short distribution                                      |
| ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 2026-06-24                                                                                        | 155/155 `NS` (100%)                                            |
| 2026-06-29                                                                                        | 39/39 `NS` (100%)                                              |
| 2026-07-04                                                                                        | 508/508 `NS` (100%)                                            |
| 2026-07-13                                                                                        | 2 `FT`, 1 `1H` (partial refresh — some leagues DO get updated) |
| 2026-05-08                                                                                        | 61 `NS`, 1 `CANC`                                              |
| 2026-02-21                                                                                        | 185 `FT`, 132 `NS`, 6 `PEN`, 1 `AWD` (mixed — 41% stuck)       |
| 2026-03-01 / 2026-03-22                                                                           | ~45-48% `NS`, rest `FT`/`PEN`                                  |
| 2020-08-16, 2020-12-02/03, 2021-01-19/20, 2021-06-14/17, 2021-07-28/29, 2024-12-24/25, 2025-12-25 | 100% `FT`/`AET`/`PEN`/`CANC` (fully settled, no NS)            |

The pattern: dates that were captured close to real-time (near the FIXTURES daily/forward pipeline's write time) get
frozen at whatever status the match had AT CAPTURE TIME — usually `NS` (not yet kicked off) — and **there is no code
path anywhere in instruments-service that re-fetches a date's FIXTURES to pick up the final result once the match
concludes**. Older, already-historical dates (2020/2021/2024/2025) show 100% settled status because they were captured
well after the fact (via the original backfill / truthset recovery), so they never hit this gap. The
2026-06-24..2026-07-14 residual cluster (53-71% of every enrichment entity's pending mass per
`query_api_football_pending_clusters_2026_07_18.py`) is who this affects hardest — it is not a "backfill hasn't reached
it yet" gap (the redirected fleet DID walk through every one of these dates and completed), it is a structural dead end:
the fetch step correctly runs, correctly finds the date's FIXTURES already captured, and correctly finds 0 of them
"completed" — because none of them were ever revisited after kickoff.

**Verified the fix works**: ran
`GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV_SHORT=prd .venv/bin/instruments-service --operation instruments --mode batch --asset-group SPORTS --sports-provider API_FOOTBALL --start-date 2026-06-24 --end-date 2026-06-24 --sports-entity FIXTURES --force`
for the single worst-case date. `--force` re-fetches FIXTURES live (bypassing presence-skip), which naturally surfaces
the now-final status, and the SAME run cascades straight into enrichment in one pass: log evidence shows "814
fixture_events rows written" / "1936 fixture_lineups rows written" / "18 fixture_stats rows written" / "253 player_stats
rows written" for this one date — genuine, non-redundant enrichment that no amount of non-force relaunching would ever
have produced.

**Root cause 2 — `read_availability_index`'s pending-count is reader-path-dependent, not just slow-to-consolidate.**

Every one of this todo's 20+ dispatches has used `read_availability_index` (directly or via
`query_api_football_pending_clusters_2026_07_18.py`) to measure gate progress, and has consistently logged "total
pending_fetch unchanged" even across dispatches where real enrichment writes were independently confirmed via per-VM
manifest shards (see slot-3/slot-9/slot-13/slot-14's entries in
`plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md`). This session found a second, more specific
reason beyond "the consolidator hasn't merged yet": `_read_consolidated_if_fresh`
(`unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:727-788`) falls back to
`_read_and_merge_per_vm_shards` whenever the consolidated blob is `>120s` old (logged as
`ManifestReader: consolidated blob age Xs > 120s threshold — falling back to per-VM shards`). Two reads run back to
back, for the exact same key (`date=2026-06-24`, `data_type=FIXTURE_EVENTS`, `source=api_football`), differing ONLY in
whether `league_id` was included in the requested `columns`:

- WITHOUT `league_id`: 189 rows — `captured=2`, `empty_confirmed=93`, `expected_unattempted=94`
- WITH `league_id`: 94 rows — ALL `expected_unattempted`, zero `captured`/`empty_confirmed`

Both reads happened within the same fallback (per-VM-shard-merge) window. This strongly suggests the per-VM-shard merge
path resolves a different SET of underlying shard files (or applies a different concat/dedup behavior) depending on
which columns are requested — plausibly because older per-VM shard files lack a `league_id` column and get silently
excluded (or handled differently) when that column is part of the request. Whatever the precise mechanism, **the same
query, run seconds apart, gives incompatible answers for whether a specific enrichment cell is still pending** — which
means the "6,925 pending, byte-for-byte unchanged" readings this todo's whole bounce history has relied on to conclude
"no progress" cannot be taken at face value; they may have been reading a fallback view that simply doesn't reflect
fresh per-VM-shard writes reliably.

## Why it matters

This todo (`sports_p2_history_apifootball_2015_to_present-001`) has bounced across 20+ dispatches over 2 days, consuming
a genuinely large amount of fleet time (5+ VM-fleet relaunches), specifically BECAUSE its own gate query kept reporting
zero progress. Root cause 1 explains why relaunching the SAME dates over and over could never close the gate even with
perfectly healthy VMs — the fetch step was structurally incapable of resolving those cells. Root cause 2 means the
diagnostic instrument every dispatch has relied on to decide "still stuck" vs. "converging" may itself be unreliable in
exactly the situations (fresh writes, <120s old) this bounce history keeps hitting. This is squarely a data-correctness
/ pipeline-observability defect, not specific to this one todo — the same `read_availability_index` fallback path is
shared by every consumer of every instruments-* manifest bucket.

## Recommended decision / next steps

- [ ] [DATA] P1. Add a periodic FIXTURES status-refresh pass to the api_football pipeline: for any already-captured date
      whose fixtures are still `status_short` NOT IN `{FT,AET,PEN,CANC,AWD,PST,ABD}` (i.e. non-terminal) AND the date is
      more than ~2 days in the past, re-fetch that date with `--force` to pick up the real final status before
      enrichment ever attempts it. (repo: instruments-service — likely the daily/forward sports scheduler cron, or a new
      dedicated one-off + a recurring hook.) This is what actually unblocks
      `sports_p2_history_apifootball_2015_to_present-001`'s gate — no non-force relaunch of the enrichment fleet will
      ever close it while stale-NS fixtures exist in the target window.
- [ ] [DATA] P1. Quantify + run a bounded `--force` FIXTURES refresh for the currently-known residual clusters:
      2026-02-21..2026-03-22 (30-45% NS) and the tail of 2026-06-24..2026-07-14 (a VM, `af-backfill-20260719-160307`,
      was launched this session for 2026-06-25..2026-07-14 with `--force     --sports-entity FIXTURES`; verify it
      completes and re-measure). Do NOT blanket-`--force` the 2026-02-21..03-22 window without first checking whether a
      smarter per-fixture-targeted refresh is available — a blanket force there would re-fetch the 55-70% of leagues
      that are already correctly settled, wasting real API-key budget (see the launcher's own over-subscription
      warnings).
- [ ] [DATA] P2. Investigate `_read_and_merge_per_vm_shards` / `_read_consolidated_if_fresh` column-selection
      sensitivity (repo: unified-trading-library, `unified_trading_library/manifest_writer/_read_index.py`) — confirm
      whether requesting `league_id` (or any column) changes which shard files are included in the fallback merge, and
      if so, fix the merge to be column-selection-invariant (the set of rows returned for a fixed filter should never
      depend on which columns are also requested). This is fleet-wide blast radius: every instruments-* bucket consumer
      using `read_availability_index` during a >120s-stale-consolidated window is exposed to the same inconsistency.
- [ ] [PROCESS] P2. Once the P2 reader fix lands, re-audit whether any OTHER "gate unchanged, bounce again" call made
      across this todo's 20+-dispatch history was itself a reader-fallback artifact rather than genuine zero progress —
      the per-VM-shard direct-read technique several dispatches already used (slot-9/13/14) as a workaround should
      become the DEFAULT verification method until the reader fix ships, not an ad-hoc fallback.
