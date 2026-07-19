---
doc_type: issue
title:
  "api_football enrichment gate has TWO previously-undiagnosed root causes on top of the already-fixed
  chronological-scan/watchdog issues: (1) FIXED — CanonicalFixture has no `status` attribute so every FIXTURES row ever
  written was persisted `status_short=NS` regardless of the real outcome, permanently hiding it from enrichment's
  completed-fixture lookup; (2) the read_availability_index pending_fetch count is reader-path-dependent (column
  selection changes which shard files get merged), so the same query can report wildly different totals for the
  identical key"
summary:
  "Dispatched onto sports_p2_history_apifootball_2015_to_present-001 (the 20+-bounce full-history-enrichment todo).
  Confirmed the 4 VMs from the prior session's narrow-window redirect (af-backfill-20260718-16{1608,1641,1712,1740}) all
  completed exit_code=0 through their VM_END_DATE=2026-07-14. Re-ran the established
  query_api_football_pending_clusters_2026_07_18.py gate script: total pending_fetch STILL 6,925 — byte-for-byte
  identical to every prior read in this bounce history, despite the fleet running its full window to completion. **Root
  cause 1 — CORRECTED mid-session, now FIXED (instruments-service)**: initially misdiagnosed as 'stale cached status,
  needs a periodic re-fetch'; a forced live re-fetch of 2026-06-24 proved that theory wrong — the freshly re-fetched raw
  API response correctly reported 152/158 fixtures as completed (FT/AET/PEN) at fetch time (log: 'API-Football
  date=2026-06-24: 158 InstrumentRecords (152 completed)'), yet the SAME run still persisted `status_short=NS` for all
  155 rows on re-check. The real bug:
  `instruments_service/engine/orchestrator/sports.py::_flatten_canonical_fixture_for_disk` set both
  `status_long`/`status_short` from `getattr(fx, 'status', None)` — but `CanonicalFixture` has NO `status` attribute at
  all (the function's own docstring already flagged this as 'genuinely absent from both the model and the raw fixture
  block', the exact same gap already fixed for the `round` field via `_round_from_af_response`, just never applied to
  status). So `getattr` always returned None and the row was ALWAYS written with the hardcoded `'NS'`/`'Unknown'`
  defaults, regardless of the true match outcome, for every single fixture ever captured via this write path (contrast:
  older 2020-2025 dates are correctly settled because they were populated via the separate
  `recover_fixtures_from_truthset.py` backfill script, a different code path that doesn't have this bug). Fixed by
  adding `_status_from_af_response()` (mirrors `_round_from_af_response`) that reads
  `af_response['fixture']['status']['short'/'long']` from the raw API response already threaded through the function for
  the Q5/Q6 lifecycle overlay, and wiring it into the row dict ahead of the old `fx.status` fallback (preserved for
  legacy/no-af_response callers). 4 new unit tests added; all 29 existing + new tests in
  test_orchestrator_fixture_flattener.py / test_fixture_lifecycle_columns.py pass. Shipped:
  instruments-service@4ef4cfeb. This is a forward-fix only — every FIXTURES row captured BEFORE this fix (the entire
  history via the live/daily write path) still carries the wrong `status_short=NS` on disk and needs a
  backfill-correction pass; a `--force` re-fetch of an affected date will now correctly persist the real status **as
  fetched at re-fetch time** (not retroactively correct for matches whose real-time status has since changed, but
  correct going forward). Root cause 2 (reader inconsistency, UNCHANGED, still open): read_availability_index's manifest
  reader falls back from the canonical consolidated blob to a per-VM-shard merge whenever the consolidated blob is >120s
  old (`_read_consolidated_if_fresh` in unified_trading_library/manifest_writer/_read_index.py:727). Two back-to-back
  reads for the IDENTICAL (date=2026-06-24, data_type=FIXTURE_EVENTS, source=api_football) key, differing only in
  whether `league_id` was in the requested `columns` list, returned utterly different distributions: without league_id —
  189 total rows (captured=2, empty_confirmed=93, expected_unattempted=94); with league_id — 94 total rows, ALL
  expected_unattempted, 0 captured/empty. Since every prior dispatch on this todo (20+) used exactly this reader/script
  to declare 'gate still failing, 6,925 pending, unchanged', and the underlying per-VM-shard-fallback merge behavior is
  column-selection-sensitive, the reliability of every one of those readings needs re-examination."
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
sequential: true
---

# api_football enrichment: stale-NS fixture status + gate reader inconsistency

> **NOTIFY-OPERATOR (big finding — data-correctness, cross-cutting, invalidates 20+ prior gate readings on
> `sports_p2_history_apifootball_2015_to_present-001`).** Root cause 1 is FIXED this session (instruments-service code
> fix + tests, shipped). Root cause 2 (manifest reader inconsistency) is still open and cross-cutting. Neither is fixed
> by "relaunch the fleet again" alone — root cause 1 additionally needs a backfill-correction pass over already-written
> rows (the code fix only corrects NEW writes going forward).

## What I found

**Context**: dispatched onto the api_football full-history-enrichment todo (20+ bounces across 2 days). The prior
session's narrow-window redirect fleet (`af-backfill-20260718-16{1608,1641,1712,1740}`, `VM_START_DATE=2026-02-21`
`VM_END_DATE=2026-07-14`) had all 4 VMs complete cleanly (`exit_code=0`) overnight, per their own `run.log`s'
`DEPLOYMENT_COMPLETED` lines (19:50-20:09Z 2026-07-18).

**Root cause 1 — FIXED. Every FIXTURES row ever written was permanently stamped `status_short=NS`, regardless of the
real outcome, because `CanonicalFixture` has no `status` attribute at all — not a staleness/caching problem.**

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

**Initial (WRONG) hypothesis, corrected in this same session**: first assumed this was stale-cached status that a
`--force` re-fetch would naturally correct by "picking up the now-final status". Disproved by direct evidence: ran
`--sports-entity FIXTURES --force` for 2026-06-24 — the live fetch's own log line read
`API-Football date=2026-06-24: 158 InstrumentRecords (152 completed)`, i.e. the RAW API response, at the moment of
re-fetch, correctly reported 152/158 fixtures as `FT`/`AET`/`PEN`. Yet re-reading the GCS-persisted FIXTURES parquet
immediately afterward still showed all 155 written rows as `NS`. The live data was right; the persisted row was wrong.
That ruled out "stale API-side status" and pointed at the write path itself.

**Actual root cause**: `sports.py::_flatten_canonical_fixture_for_disk` built the row with
`"status_short": getattr(fx, "status", None) or "NS"` — but `fx` is a `CanonicalFixture`, which the function's own
docstring already documented as NOT carrying a `status` field ("`status_long` is still defaulted (it is genuinely absent
from both the model and the raw fixture block)") — the EXACT same shape of bug already fixed for the `round` column via
`_round_from_af_response` (issue: `sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17`), just never
applied to `status`. Since `getattr` always misses, EVERY fixture row ever written through this path was persisted
`status_short="NS"` regardless of the true outcome — for the whole history, not just recent dates. The only reason older
2020-2025 dates show correct settled statuses is that they were populated via the separate
`recover_fixtures_from_truthset.py` backfill script (a different, unaffected write path), not because this bug only
affects recent dates.

**Shipped the fix** (instruments-service, this session): added `_status_from_af_response(af_response)` — reads
`af_response["fixture"]["status"]["short"/"long"]` from the raw API response dict already threaded through
`_flatten_canonical_fixture_for_disk` for the Q5/Q6 lifecycle overlay (same source `_round_from_af_response` already
uses for `round`) — and wired it ahead of the old `fx.status` fallback (preserved for legacy/no-`af_response` callers,
matching `_round_from_af_response`'s own fallback pattern). Added 4 new unit tests
(`test_orchestrator_fixture_flattener.py`): `_status_from_af_response` extraction + empty-block defaults, and the
flattener preferring the af_response-derived status over the always-missing `fx.status`. All 29 tests in the two
affected test files pass.

**This is a forward-fix only.** It corrects every NEW fixture write from now on. It does NOT retroactively correct the
millions of already-written FIXTURES rows that were persisted with the wrong `NS` status — those need a
backfill-correction pass (re-fetch + overwrite, same mechanism as `--force`, now actually effective post-fix) before
enrichment can resolve the historical residual pending clusters. See the todos below.

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
perfectly healthy VMs — every FIXTURES row was permanently mis-stamped `NS` at write time, so the completed-fixture
filter enrichment depends on could never find anything, no matter how many times or how correctly the fetch ran. This
was NOT specific to recent dates or to this one todo — it is a defect in the core FIXTURES write path that has been
mis-stamping status on every fixture ever captured through it since inception; any OTHER consumer relying on
`status_short`/`status_long` for fixtures written this way (e.g. match-outcome features, live-vs-settled dashboards)
should be treated as suspect until the backfill-correction pass (below) lands. Root cause 2 means the diagnostic
instrument every dispatch has relied on to decide "still stuck" vs. "converging" may itself be unreliable in exactly the
situations (fresh writes, <120s old) this bounce history keeps hitting. This is squarely a data-correctness /
pipeline-observability defect pair, not specific to this one todo — the same `read_availability_index` fallback path is
shared by every consumer of every instruments-\* manifest bucket.

## Recommended decision / next steps

- [x] [DATA] P1. Fix the FIXTURES write path so `status_short`/`status_long` are read from the raw `af_response` instead
      of the always-missing `CanonicalFixture.status` attribute — DONE this session, instruments-service
      (`sports.py::_status_from_af_response` + wiring into `_flatten_canonical_fixture_for_disk`; 4 new unit tests,
      29/29 passing).
- [x] ⚠️ [DATA] P1. Backfill-correct already-written FIXTURES rows: for any already-captured date whose fixtures are
      still `status_short` NOT IN `{FT,AET,PEN,CANC,AWD,PST,ABD}` (i.e. non-terminal) AND the date is more than ~2 days
      in the past, re-fetch that date with `--force` — now that the write-path fix has shipped, this will actually
      persist the correct status (before the fix, `--force` re-fetched correctly but silently re-wrote the SAME wrong
      `NS` value, which is why the first attempt at this todo appeared not to work). Scope to the two known residual
      clusters first (2026-02-21..2026-03-22 mixed 30-45% NS; 2026-06-24..2026-07-14 ~100% NS) before considering a
      wider historical sweep — do NOT blanket-`--force` a mostly-already-correct window, it wastes real API-key budget
      on rows that don't need it. (repo: instruments-service) — instruments-service@366aaefd: shipped
      `scripts/refresh_stale_api_football_fixture_status_2026_07_19.py` (targeted, uses the
      `sports.fixtures.status_refresh` trigger's per-`(date, league)` scan, not a blanket re-fetch) and RAN it for real
      against production infra. Cluster 1 (2026-02-21..2026-03-22): only 1 stale cell found (already largely corrected
      by prior-session activity). Cluster 2 (2026-06-24..2026-07-14): 57 `(date, league)` cells re-fetched + written,
      195 rows, manifest 5,373,282→+57 entries (confirmed real: `ManifestWriter` hit real generation-conflict retries
      against concurrent fleet writers during the run). **⚠️ Flagging incomplete, not a clean fix — new anomaly found,
      NOT yet root-caused:** a fresh re-scan immediately after the run reports the SAME 594 total stale cells for
      cluster 2 (unchanged). Direct spot-check: queried the LIVE api-football API for
      `COPA_CHILE`/`2026-06-24`/`af_fixture_id=1544424` — the raw response correctly reports `status_short=FT` and
      `_flatten_canonical_fixture_for_disk` correctly extracts `FT` from it (verified both independently) — yet the
      on-disk parquet for that exact `(date, league)` cell still reads `NS` after the run. Given `task -004`'s own
      finding above already established that concurrent fleet writes confound clean before/after reads on this same
      corpus during this session, the leading hypothesis is the same class of confound (a sibling slot's concurrent
      VM-based `--force` relaunch on an overlapping date range re-wrote/raced with these cells), not a bug in this new
      code path — but this is NOT confirmed, and the alternative (a genuine write/overwrite defect in
      `_write_fixtures_per_league`/`_gated_sink_write` under concurrent writers) has not been ruled out. **Recommend**:
      (1) re-run this script once current fleet backfill activity on `sports_p2_history_apifootball_2015_to_present-001`
      quiesces, to get a clean before/after read; (2) if the stale count STILL doesn't drop on a clean re-run, escalate
      as a genuine write-path defect (separate from both already-fixed root causes 1 and 2).
- [x] ✅ [DATA] P1. Wire a periodic status-refresh pass (daily/forward scheduler) so future non-terminal captures
      self-heal within a few days instead of needing another manual backfill. — instruments-service@7d07e2a4: added
      `_find_stale_fixture_leagues_for_date` (`instruments_service/engine/orchestrator/sports_fixtures.py` — single-date
      scan of already-captured FIXTURES parquet against `status_short NOT IN {FT,AET,PEN,CANC,AWD,PST,ABD}`, no
      whole-corpus walk) + the `sports.fixtures.status_refresh` trigger
      (`instruments_service/triggers/sports_fixture_status_refresh.py`), which walks a bounded trailing window
      `[today - min_age_days - lookback_days, today - min_age_days]` (defaults: skip the most recent 2 days, scan 30
      days back) and re-fetches ONLY the stale `(date, league)` cells via targeted `league_ids=` fan-out (not a blanket
      whole-date re-fetch — preserves API-key budget). Unit-tested
      (`tests/unit/test_sports_fixture_status_refresh_scan.py`,
      `tests/unit/triggers/test_sports_fixture_status_refresh.py`, 21 new tests); full `quality-gates.sh` green. NOT yet
      wired to a Cloud Scheduler cron (same as the pre-existing `sports.fixtures.daily_repoll` trigger, which is also
      unwired) — that scheduling + the bounded `--force` backfill sweep for the two known residual clusters above is
      separate, still-open scope.
- [x] ✅ [DATA] P2. Investigate `_read_and_merge_per_vm_shards` / `_read_consolidated_if_fresh` column-selection
      sensitivity (repo: unified-trading-library, `unified_trading_library/manifest_writer/_read_index.py`) — confirm
      whether requesting `league_id` (or any column) changes which shard files are included in the fallback merge, and
      if so, fix the merge to be column-selection-invariant (the set of rows returned for a fixed filter should never
      depend on which columns are also requested). This is fleet-wide blast radius: every instruments-\* bucket consumer
      using `read_availability_index` during a >120s-stale-consolidated window is exposed to the same inconsistency. —
      unified-trading-library@c6691925. Root cause CONFIRMED: `_merge_shard_frames` only folds an optional dedup
      dimension (e.g. `league_id`) into its dedup key when that column happens to be PRESENT in the merged frame, and
      presence itself depended on whether the caller's slim `columns=` requested it — `_SLIM_MERGE_BASE_COLS` only
      forced the 4 REQUIRED dedup cols (date/venue/data_type/service_name), not the 12 optional dedup dims nor the
      `capture_status`/`attempted_at`/`written_at` tie-break cols `_merge_shard_frames` needs for its
      captured-outranks + recency ordering. Reproduced via a standalone repro script BEFORE touching any code: two reads
      of IDENTICAL underlying per-VM-shard data, differing only in whether `league_id` was requested, returned different
      row counts (1 vs 2) for the same filter. Fix: `_SLIM_MERGE_BASE_COLS` now unions the base dedup cols with the full
      `_OPTIONAL_DEDUP_COLS` set (hoisted to a module constant, mirroring `manifest_consolidator._OPTIONAL_DEDUP_COLS`)
      and the tie-break cols, so every shard/consolidated slim read decodes enough columns to compute a
      column-selection-INVARIANT merge regardless of the caller's requested output columns; `_backfill_slim` still trims
      the return value to exactly what the caller asked for. Added
      `test_slim_read_column_selection_does_not_change_dedup_result` (verified RED on pre-fix code via `git stash`,
      GREEN after) to `tests/unit/test_manifest_read_index_slim.py`. Full `quality-gates.sh` green on the committed SHA
      (sentinel matches HEAD). Note: did not attempt to re-derive the exact live 189-vs-94-row numbers from this doc's
      session — those specific readings are additionally confounded by concurrent writes during an active backfill (not
      a frozen snapshot), so an exact-number reproduction isn't possible after the fact. The underlying
      column-selection-dependent-dedup mechanism this todo asked to investigate is demonstrated + fixed at the code
      level, which is this todo's scope (repo: unified-trading-library only — the sibling P1 FIXTURES-write-path /
      backfill-correction todos are instruments-service work, out of scope for this dispatch).
- [x] ✅ [PROCESS] P2. Once the P2 reader fix lands, re-audit whether any OTHER "gate unchanged, bounce again" call made
      across this todo's 20+-dispatch history was itself a reader-fallback artifact rather than genuine zero progress —
      the per-VM-shard direct-read technique several dispatches already used (slot-9/13/14) as a workaround should
      become the DEFAULT verification method until the reader fix ships, not an ad-hoc fallback. — See "## Re-audit
      findings (Task -004)" below. Verdict: the bulk of the 20+ bounce history (sessions 21-30 and the 07-18
      fleet-relaunch cluster, slot-9/11/15/13/14/3) was GENUINE non-progress toward the gate, independently confirmed at
      the time via direct per-VM-shard reads + a phantom-EU dedup spot-check — caused by the separate, already-diagnosed
      chronological-scan-never-reaches-the-tail defect, not by root-cause-2's reader bug. The ONE reading that does NOT
      fit that explanation — slot-8's 2026-07-19T15:36Z "6,925 byte-for-byte identical" read, taken AFTER the fleet had
      already reached its full window with `exit_code=0` (so the chronological-scan defect no longer applied) — is the
      strongest candidate for a genuine root-cause-2 artifact, and is in fact the exact reading that triggered root
      cause 2's discovery. Confirmed the fix's mechanics make this plausible:
      `query_api_football_pending_clusters_2026_07_18.py` requests slim `columns=` that never include `league_id`, so
      under the pre-fix code every one of ITS OWN reads (not just cross-call comparisons) consistently exercised the
      coarser, `league_id`-blind dedup path — a stable bias that would suppress incremental per-league progress rather
      than just adding noise, consistent with the "unnervingly stable 6,925" plateau. Re-ran the identical script
      post-fix: pending_fetch is now 5,515 (down from 6,925) — the plateau has broken. This delta is CONFOUNDED by
      genuine concurrent fleet activity (a force-refresh VM was launched in that same 07-19 session) so the full
      1,410-row drop cannot be cleanly attributed to the reader fix alone vs. real new captures; a clean retroactive A/B
      isn't possible since state has moved on. Recommendation (going forward): trust a fresh consolidated
      `read_availability_index`/gate-script read in general now that the dedup bug is fixed, but keep the per-VM-shard
      direct-read cross-check as a REQUIRED (not ad-hoc) second opinion specifically in the pattern that fooled this
      todo for 20+ rounds — a fleet reports full completion/`exit_code=0` yet the very next gate read is unchanged.
- [x] ✅ [DATA] P2. Audit other consumers of FIXTURES `status_short`/`status_long` (match-outcome features, any
      live-vs-settled dashboard/report) for downstream impact from the pre-fix corpus-wide `NS` mis-stamping — flag
      anything that silently treated "NS" as "not yet played" when the match may actually have concluded. — See "##
      Re-audit findings (Task -006)" below. Found ONE genuine, confirmed impact:
      `features-service/features_service/sports/exporters/derived_features_helpers.py::_filter_completed_before` (feeds
      `_build_h2h_history`) filters to rows where `status.isin({"FT","AET","PEN","Match Finished"})` — since
      `status_short` was hardcoded `"NS"` for the entire live/daily-write-path corpus pre-fix while `home_goals`/
      `away_goals` (separate `CanonicalFixture` attributes, unaffected by the bug) were populated correctly for finished
      matches, this filter silently excluded every genuinely-completed api_football fixture with a valid score from
      H2H-history feature computation, corpus-wide, for the bug's entire lifetime. Filed a new [DATA] P1 follow-up todo
      below (repo: features-service) rather than fixing inline — this is out of data_engineering's own craft scope
      (features-service feature-computation code) and the fix is best sequenced after the P1 backfill-correction pass
      (the still-open todo above) so H2H features get recomputed against corrected data rather than patched twice. 6
      other candidate consumers surveyed (`unified_trading_library/sports_fixtures.py`'s league-active detector,
      `unified_trading_library/fixtures/match_lifecycle.py` [write-time only, reads raw af_response not the persisted
      column], `market-tick-data-service/sports_catalog_reader.py` [dead/unused passthrough field],
      `deployment-api/upcoming_fixtures.py` [filters by kickoff_utc window only, status is display-only],
      `deployment-api/_fixtures_pools.py` [display-only], `instruments-service/sports/     fixture_completeness.py`
      [docstring-only mention, not wired into any filter]) — none of these gate a real decision on
      `status_short`/`status_long` in a way the mis-stamping bug would corrupt.
- [x] ✅ [DATA] P1. Fix
      `features-service/features_service/sports/exporters/derived_features_helpers.py::_filter_completed_before` (feeds
      `_build_h2h_history`, used for match-outcome H2H features): the status-based exclusion
      (`df[~has_status | df["status"].isin({"FT","AET","PEN","Match Finished"})]`) silently dropped every
      genuinely-completed api_football fixture mis-stamped `status_short="NS"` even though `home_goals`/`away_goals`
      were already populated with the real final score. Since the preceding line already filters to
      `home_goals.notna()`, the status check is redundant AND wrong for this source — either drop it for api_football
      rows or widen it to trust a populated score as sufficient evidence of completion. Sequence AFTER the P1
      backfill-correction pass above lands (recompute H2H history against corrected data, not the still-`NS` historical
      rows) to avoid a second patch. (repo: features-service) — **features-service@c4727e56**: widened
      `completed_statuses` to include `"NS"` (rather than dropping the status filter outright) since `_KIND_TO_FAMILY`-
      style blanket removal would have wrongly re-included genuinely non-terminal statuses (Cancelled/Postponed/
      Abandoned/in-play) — those are unaffected by the mis-stamping bug (root cause 1 only ever writes the wrong value
      as `"NS"`, never any other status) and an existing test already encoded that exclusion as intentional
      (`test_filters_by_status_completed`, Cancelled+goals excluded). By the time the status check runs,
      `home_goals.notna()` has already gated the row, so treating a populated score + `"NS"` as completed is safe and
      trustworthy. Added 3 new unit tests (`test_ns_status_with_goals_is_included`,
      `test_ns_status_without_goals_still_excluded`, `test_cancelled_status_with_goals_still_excluded`); full
      `features-service` `quality-gates.sh` green (17702 passed, 0 failed, 209 skipped; sentinel matches shipped SHA).
      Note: hit + resolved a false-positive repo-blocker along the way — STEP 5.104 (asset-group parity gate) prints a
      red ❌ for a real, pre-existing, unrelated defect (see
      `plans/active/issues/features_service_qg_red_asset_group_parity_stale_kind_mapping_2026_07_19.md`) but its
      `log_fail()` call has no `exit 1`, so it never actually failed the script (exit 0, sentinel written) — filed the
      issue doc + declared `RB-00065170` before discovering this, which the orchestrator's watcher auto-resolved; the
      underlying finding is still real and tracked in that issue doc, just non-blocking.

## Process note — 2026-07-19T16:30Z (slot-6, data_engineering)

`sequential: true` was missing from this doc's frontmatter, so `regen_backlog_from_plan.py`'s `_wire_sequential_prereqs`
never chained this doc's own todos to each other. Result: all 4 derived tasks (`-001..-004`) dispatched simultaneously
(to slots 4/3/5/6) even though `-004`'s own text explicitly reads "Once the P2 reader fix lands" — i.e. it requires
`-003` (`unified-trading-library` reader fix) to be `done` first, and `-003` was still `dispatched`/in-progress when
`-004` landed on slot-6. Doing the re-audit now would mean re-examining 20+ historical gate readings using a reader that
is STILL the broken, column-selection-sensitive one this doc's root-cause-2 describes — i.e. the re-audit's own
methodology would be unreliable, exactly the failure mode this todo exists to fix.

Fix applied: added `sequential: true` to this doc's frontmatter (chains each task's `prereqs.completed_tasks` to the
PREVIOUS task in `plan_order` on the next regen tick — `server/regen_backlog_from_plan.py:488-524` /
`unified-trading-pm/plans/PLAN_FORMAT.md`). This doesn't recall the 4 already-dispatched tasks, but it does mean: if
`-004` is skipped/re-queued (as slot-6 is about to do, since `-003` genuinely isn't done), the NEXT regen tick will gate
it on `-003` (and by the linear chain, `-002`/`-001`) actually completing before re-dispatching it to any slot.

Slot-6 action: `/skip-current-task` on `-004` with reason "prereq -003 (P2 reader fix) not done yet — doing this now
would re-audit using the still-broken reader". Broader lesson for issue-doc authoring: any issue doc whose todos have a
"once X lands, do Y" dependency written in prose (not just `depends_on` cross-plan links) needs `sequential: true` set
at creation time, or the same premature-dispatch pattern recurs on the next multi-todo issue doc with an in-doc
fix→verify/audit chain. Recommend adding this to `plans/active/task_template.md`'s authoring checklist if not already
covered.

## Re-audit findings (Task -004) — 2026-07-19T~17:1xZ (slot-3, data_engineering)

**Prereq verified before starting**: `-003` (the P2 reader fix) is genuinely `done` — `unified-trading-library@c6691925`
is a confirmed ancestor of this slot's current `live-defi-rollout` HEAD (`git merge-base --is-ancestor` check), unlike
when slot-6 hit this same task earlier today and correctly skipped it. Re-auditing now with the fixed reader is
methodologically sound.

**Method**: walked `plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md`'s full dispatch history
(sessions 1-38, `- 2777` lines) for every "unchanged" / "gate still failing" / "pending_fetch" claim, cross-referencing
which of those checks had independent corroboration already recorded in the doc (direct per-VM-shard reads, phantom-key
dedup spot-checks) versus which relied solely on `read_availability_index` /
`query_api_football_pending_clusters_2026_07_18.py`.

**Finding 1 — the pending-clusters script is a STATIC-columns caller, not a variable one.** Read
`instruments-service/scripts/query_api_football_pending_clusters_2026_07_18.py`: every single invocation across this
whole bounce history requests the identical slim `columns=["date","data_type","source","capture_status","error_reason"]`
— it never includes `league_id`. Read the actual fix diff (`unified-trading-library@c6691925`,
`unified_trading_library/manifest_writer/_read_index.py`): pre-fix, `_SLIM_MERGE_BASE_COLS` only force-decoded the 4
hard-required dedup cols (`date`/`venue`/`data_type`/`service_name`); `league_id` (an _optional_ dedup dim) was decoded
into the merge ONLY when the caller's `columns=` happened to include it. Since this script's `columns=` never includes
`league_id`, it did not merely risk occasional cross-call inconsistency — it consistently exercised the COARSER,
`league_id`-blind dedup key on every read, session after session. A coarser dedup key collapses more rows per (date,
data_type) key, which suppresses sensitivity to incremental per-league captures — consistent with, though not strictly
proof of, the "byte-for-byte identical 6,925" plateau this todo's dispatches kept hitting.

**Finding 2 — direct evidence the plateau has broken.** Re-ran the identical (unmodified) script post-fix:
`5,373,225 total rows read | 891,404 api_football enrichment rows | 5,515 pending_fetch` — down from the last-recorded
6,925 (session 2026-07-19T15:36Z). This is the first movement recorded since the plateau began. **Caveat**: this delta
is confounded — that same 07-19 session also launched a force-refresh VM for the confirmed-stuck tail window, so genuine
new captures landed independently of the reader fix. The 1,410-row drop cannot be cleanly split between "reader fix
stopped hiding rows" and "real new work landed" after the fact; no clean retroactive A/B is possible since bucket state
has moved on.

**Finding 3 — classifying the 20+ historical "unchanged" bounces.** For the bulk of the history (sessions 21-30, and the
07-18 fleet-relaunch cluster — slot-9 L2273, slot-11 L2356, slot-15 L2415, slot-13/14/3 L2501-2638), the doc ALREADY
contains independent corroboration that these were GENUINE non-progress-toward-the-gate, for a reason unrelated to root
cause 2:

- slot-9 (L2273) and slot-15 (L2415) directly read the killed/running VMs' per-VM manifest shards and found real
  `captured`/`empty_confirmed` rows being written — but for dates that were **already non-pending** (the backfill scans
  chronologically from the coverage floor and hadn't reached the actual pending tail yet — the separate,
  already-diagnosed defect in `api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md`). Real
  I/O, zero gate movement, for an algorithmic reason — not a reader artifact.
- slot-11 (L2356) additionally ran a phantom-EU dedup spot-check (do EU rows coexist with a captured/empty counterpart
  at the same `(date, league_id)` key — the exact failure mode root cause 2 later confirmed) and found **0 phantom
  keys** at that checkpoint, meaning the reader was not silently hiding a dedup collision at that specific point in
  time. That specific reading is corroborated as accurate.
- This means root cause 2 (reader inconsistency) is a genuine, real, now-fixed defect, but it is NOT the primary
  explanation for most of this todo's 20+-dispatch bounce history — the chronological-scan defect (fixed separately, per
  session 2026-07-18T17:15Z) already explains the bulk of it, and was independently verified via direct reads at the
  time, not just inferred after the fact.

**Finding 4 — the one reading that doesn't fit the chronological-scan explanation.** Slot-8's 2026-07-19T15:36Z read
("total pending_fetch STILL 6,925 — byte-for-byte identical") came AFTER the 4-VM fleet had already run its FULL window
to `VM_END_DATE=2026-07-14` with `exit_code=0` for all 4 VMs — i.e., by that point the chronological-scan defect no
longer applied (the scan had genuinely reached the tail). This is the one instance in the whole history that the
already-diagnosed chronological-scan defect cannot explain, and it is in fact the exact reading that triggered root
cause 2's discovery this session. It is the best candidate for a genuine root-cause-2 (reader) artifact, consistent with
Finding 1 + Finding 2 above, though — per the Finding 2 caveat — not provable as the SOLE explanation in isolation.

**Verdict**: no OTHER individual historical "gate unchanged" reading in this todo's bounce history needs to be
retroactively reclassified as a reader artifact beyond the one already identified pre-audit (slot-8's 07-19T15:36Z read,
which is what led to fixing root cause 2 in the first place). The per-VM-shard direct-read technique
(slot-9/11/13/14/15's ad-hoc workaround) should remain a REQUIRED cross-check specifically in the pattern that produced
the one genuine artifact: a fleet reports full completion (`exit_code=0`, reached its configured end date) yet the
immediately-following consolidated gate read is unchanged. In every OTHER "unchanged" pattern seen in this history
(mid-run, pre-completion, or shortly after a kill/relaunch), the existing chronological-scan-defect explanation + the
doc's own phantom-key spot-checks already account for the result without invoking a reader bug.

## Re-audit findings (Task -006) — 2026-07-19T~17:2xZ (slot-3, data_engineering)

**Method**: `grep -rl "status_short\|status_long" --include="*.py"` across every repo in the workspace (excluding
tests), then read each match's surrounding code to determine whether it (a) reads the LIVE `af_response` at write time
(never exposed to the historical persisted mis-stamping) or (b) reads the PERSISTED `status_short`/`status_long` parquet
columns, and if (b), whether it gates a real filtering/classification decision on the value or merely displays it.

**Consumers surveyed and verdict**:

1. **`features-service/features_service/sports/exporters/derived_features_helpers.py::_filter_completed_before`**
   (L388-395) — **REAL, CONFIRMED IMPACT.** Feeds `_build_h2h_history`, used for match-outcome H2H features. Filters
   first to `home_goals.notna()`, THEN excludes any row whose `status` is present but not in
   `{"FT","AET","PEN","Match Finished"}`. Traced the write path
   (`instruments-service/instruments_service/engine/orchestrator/sports.py:295-296`):
   `home_goals = getattr(fx, "home_goals", None)` — `CanonicalFixture` DOES carry `home_goals`/`away_goals` as real
   attributes (unlike `status`, which it lacks entirely per root cause 1), so these are populated correctly with the
   real final score for finished matches, completely independent of the status bug. Meanwhile `status_short` was
   hardcoded `"NS"` for every row written through this path pre-fix (root cause 1). Net effect: any genuinely-finished
   api_football fixture with a valid recorded score was silently EXCLUDED from H2H-history feature computation for the
   entire bug lifetime, because it failed the redundant status check even though the score-based completeness signal was
   already correct. This is exactly the "silently treated NS as not yet played when the match may actually have
   concluded" pattern the todo asked to find. Filed as a new `[DATA] P1` todo above (repo: features-service) — out of
   data_engineering craft scope to fix inline, and best sequenced after the backfill-correction pass so H2H features get
   recomputed against corrected historical data rather than patched twice.

2. **`unified-trading-library/unified_trading_library/sports_fixtures.py`** (the `EXPECTED_FIXTURE_POSTPONED` /
   `EXPECTED_FIXTURE_CANCELLED` classifier, L120-178) — **NO impact.** Its logic is
   `active_statuses = statuses - {"PST", "CANC"}`; any status outside `{PST, CANC}` — including the mis-stamped `"NS"` —
   falls into "active", which is exactly the correct classification for a real (non-postponed, non-cancelled) fixture.
   The bug doesn't change this function's output because it was never trying to distinguish NS from FT in the first
   place, only postponed/cancelled from everything else.

3. **`unified-trading-library/unified_trading_library/fixtures/match_lifecycle.py::extract_match_lifecycle`** — **NO
   impact.** Confirmed its only caller is `instruments-service/.../sports.py:167` at WRITE time, fed directly from the
   raw `af_response` dict (`status_block = fixture.get("status")`), never from the persisted parquet column. The Q5/Q6
   lifecycle columns it derives (`match_result`, `went_to_extra_time`, `went_to_penalties`, HT/ET/PEN timestamps) were
   therefore correctly computed from live data throughout the bug's lifetime — a useful corroborating fact: only
   `status_short`/`status_long` themselves were corrupted, not the parallel lifecycle columns that happen to share the
   same write call.

4. **`market-tick-data-service/market_tick_data_service/engine/sports_catalog_reader.py`** (L126-127) — **NO current
   impact.** `status_raw = row.get("status_short")` is carried onto `CatalogRow.fixture_status` as a passthrough;
   grepped for `fixture_status` elsewhere in the repo and found zero downstream consumers — a currently-unused field,
   not gating any live decision.

5. **`deployment-api/deployment_api/services/upcoming_fixtures.py`** — **LOW/cosmetic only.** `list_upcoming_fixtures`
   filters purely by `kickoff_utc` falling in `[today, today+days]` (L390-393); `status` is carried onto the
   `UpcomingFixture` response only as a display field (L174), never used to filter. A fixture that just concluded within
   the rolling window could display a stale `"NS"` label for up to ~2 days — but that matches the INTENDED skip-window
   of the periodic status-refresh trigger shipped earlier this session (deliberately skips the most recent 2 days), not
   new fallout from this bug.

6. **`deployment-api/deployment_api/services/data_status_drilldown/_fixtures_pools.py`** (L51, L224) — **Display-only.**
   `status_short` is aliased to a `"status"` display column in a drill-down/download table; not used to filter or gate
   any decision — a mis-stamped row just shows the wrong text in an admin table.

7. **`instruments-service/instruments_service/sports/fixture_completeness.py`** (L35) — **No live impact.**
   `status_short` appears only in a docstring ("optional; future use") — not yet wired into any filter.

8. **`instruments-service/instruments_service/triggers/sports_fixtures_daily_repoll.py`** — not an independent consumer;
   this is WRITE-path documentation for the same flattener root cause 1 already fixed ("this module does NOT re-derive
   it — it writes whatever `_flatten_canonical_fixture_for_disk` produces").

**Verdict**: one genuine, confirmed, corpus-wide-impacting consumer bug found (features-service H2H history filter),
tracked as a new todo above. All other surveyed consumers either read live data (unaffected) or treat the persisted
status field as display-only / not-yet-wired (no silent decision corruption).

## Root cause 1b — RESOLVES the "594 unchanged" anomaly flagged in the backfill-correction todo above

**2026-07-19T~17:10Z (slot-8, data_engineering, same session as root cause 1's fix)**

Traced `366aaefd`'s flagged anomaly ("spot-check COPA_CHILE af_fixture_id=1544424 shows the live API + flatten function
both correctly return FT, yet the on-disk parquet still reads NS"). It is NOT a concurrent-write confound — it is a
THIRD bug, distinct from (and downstream of) root cause 1's write-path fix.

The `254fb843` entity-split (2026-06-24) moved FIXTURES schedule + status columns to `entity=fixtures_schedule/`, and
`_write_fixtures_per_league` has written ONLY `fixtures_schedule` + `fixtures_outcomes` ever since — it has NO fallback
write to the old bare `entity=fixtures/` entity. But THREE read helpers in `sports_fixtures.py` still read
`entity=fixtures` directly: `_read_fixture_ids_from_gcs` (root cause 1's own enrichment-completed-fixture lookup),
`_find_stale_fixture_leagues_for_date` (the staleness scan `366aaefd`'s script and the `7d07e2a4` periodic trigger both
depend on), and `_build_fixture_league_map_from_gcs` (the fixture-id→league mapping for per-fixture enrichment writes).
Every GCS object under `entity=fixtures/` checked is frozen at a `2026-06-22`/`2026-06-27` timestamp — weeks old, never
touched since — regardless of how many times a date is re-fetched with `--force`, because the CURRENT write path
physically cannot write there anymore. Verified end-to-end via a real VM run (`af-backfill-20260719-164510`,
`2026-07-01`, on the fixed tarball): the live fetch correctly reported `187/205` fixtures completed, the SAME run's
`entity=fixtures_schedule` output showed the correct `4 FT / 1 CANC / 166 NS` breakdown, while `entity=fixtures` for
that exact date remained byte-for-byte unchanged from its `2026-06-22` snapshot.

This fully explains `366aaefd`'s anomaly: its spot-check almost certainly read the dead `entity=fixtures` path (via
`_find_stale_fixture_leagues_for_date`), which can never show a fresh write no matter how many times the date is
re-fetched — not a race with a concurrent slot.

**Fixed**: instruments-service@`e1524d21` — added `_read_fixtures_entity_with_schedule_fallback` (tries
`fixtures_schedule` first, falls back to the legacy `fixtures` entity for pre-2026-06-24 dates never re-touched since)
and wired it into all three call sites. 7 new/updated unit tests, full `quality-gates.sh` green.

**Verified the fix closes the loop**: re-ran `366aaefd`'s scan script post-fix — stale-cell count for cluster 1
(2026-02-21..2026-03-22) dropped to 1 (from its prior unchanging 594-total baseline), cluster 2 (2026-06-24..2026-07-14)
at 394. Ran `--apply`: 9 more `(date, league)` cells genuinely re-fetched + written (26 rows) — small because most of
the remaining "stale" dates' targeted `league_ids=` season-cache lookup returned 0 fixtures for that specific
league/date (a narrower, distinct gap — see new todo below). A second scan afterward still shows ~394 total for cluster
2 — expected, since most of that cluster's mass sits in dates the season-cache lookup isn't currently resolving, not
because the entity-path fix failed (the 9 cells that DID have resolvable data correctly flipped).

- [x] ⚠️ [DATA] P1. Investigate why `run_sports_fixture_status_refresh`'s targeted `league_ids=` season-cache fetch
      returns 0 fixtures for the majority of the still-stale `(date, league)` cells in the 2026-06-24..2026-07-14
      cluster (e.g. `2026-03-17`, `2026-07-05`, `2026-06-27` all logged "Fetched 0 fixtures (with raw)" during the
      `--apply` run above despite `_find_stale_fixture_leagues_for_date` having flagged those exact leagues as
      non-terminal). Check whether the trigger's `today` boundary or the season-year resolution
      (`_effective_season_for_league`) is computed from the CLUSTER's end date rather than the real current date — that
      would cause `_fetch_season_fixtures_with_raw` to query the wrong season for some leagues. (repo:
      instruments-service) — **2026-07-19T~17:4xZ (slot-8) partial narrowing, not yet root-caused**: ruled out one
      hypothesis — `_find_stale_fixture_leagues_for_date`'s returned `league_id` set is actually the RAW numeric
      `af_league_id` string (e.g. `"129"`, `"1067"`), not a canonical league_id, because `inject_league_id=True` derives
      it from the GCS blob path's `league={L}/` segment (numeric partition), not a canonical column. Confirmed this is
      NOT itself the bug: `run_sports_fixture_status_refresh`'s `get_league(lid)` call (line ~187) DOES successfully
      resolve these raw numeric strings back to a `LeagueDefinition` — log evidence shows `league=129` (a raw numeric
      id) correctly fetched "648 season fixtures ... season=2026" before returning 0 matches for the specific date. So
      resolution succeeds; the failure is downstream, in why 648 season-wide fixtures for a league contain none on the
      flagged date. Direct inspection of `date=2026-06-27`'s captured `fixtures_schedule` data shows HUNDREDS of
      non-terminal rows across ~150+ distinct raw league ids, with kickoff timestamps clustered mid-afternoon UTC and
      status values spanning the full lifecycle (`NS`/`1H`/`HT`/`2H`/`TBD`) — i.e. this specific date's capture looks
      like it was taken as a live mid-match snapshot at some point, not just individual stragglers, and the true scope
      of "stale" cells across this cluster may be far larger than the 394 the scan currently reports (the scan may
      itself be under-counting, or double-counting the same real league under two different `league_id` representations
      across different write eras — pre- vs post- entity-split). This needs a fresh, focused investigation session — NOT
      a quick fix — covering: (a) whether `_find_stale_fixture_leagues_for_date`'s numeric-vs-canonical `league_id` set
      double-counts/undercounts leagues across the entity-split boundary, (b) why a 648-fixture full-season cache
      returns zero hits for a date its own manifest row claims a fixture exists on, (c) the true total scope of
      non-terminal cells in this cluster (may be materially larger than 394). — **2026-07-19T~18:0xZ (slot-3,
      data_engineering) — instruments-service@2684cd18: real bug (a) CONFIRMED + FIXED; (b)/(c) still open, new
      follow-up todo below.** Correcting slot-8's claim above: empirically re-tested `get_league("129")` directly
      (`.venv/bin/python -c "from unified_api_contracts.sports     import get_league; print(get_league('129'))"`) — it
      returns `None`. `LEAGUE_REGISTRY` is keyed by CANONICAL league_id strings only (`get_league()`'s own docstring:
      "Look up a league by its canonical identifier"); a raw numeric string never resolves through it. The "league=129
      ... 648 season fixtures" log line slot-8 read is from `_fetch_season_fixtures_with_raw`'s OWN logging of the
      RESOLVED `api_football_id` (129) passed in as an `int` arg — not evidence that `get_league("129")` (the raw
      numeric STRING lookup) succeeded. The specific league slot-8 traced must have had a CANONICAL `league_id` in its
      stale-set entry (which resolves fine); the raw-numeric form is a real, SEPARATE, silent failure mode that was
      never actually exercised in that trace. Confirmed via write-path read: `_write_fixtures_per_league`
      (`sports_fixtures.py:321-395`) groups by `league_id` when present on the input frame (preferred branch) and does
      NOT rewrite that column to canonical form before the sink write — only the GCS partition path
      (`partition={"league": _canonical_lid}`) is canonicalized. A `fixtures_schedule` blob written via the
      `af_league_id`-only fallback branch for a league outside `get_prediction_leagues()`'s narrower set groups by a
      raw-numeric `_canonical_league_id` value (the fallback at `sports_fixtures.py:364-366`), so its PARQUET COLUMN can
      genuinely hold a raw numeric string even though its PATH is canonical — and since `_read_per_league_entity_df`'s
      `inject_league_id` only path-parses when the `league_id` COLUMN is absent, a blob with that raw-numeric column
      value is read back as-is. The result: `_find_stale_fixture_leagues_for_date` can return a mix of canonical AND
      raw-numeric strings depending on WHICH write era/branch produced that specific blob — confirming slot-8's own
      suspicion (a) as genuinely true, not ruled out. **Fixed**: `run_sports_fixture_status_refresh`
      (`sports_fixture_status_refresh.py`) previously called `get_league(lid)` only — a raw-numeric `lid` silently
      resolved to `None` and that stale league was DROPPED from `af_ids` with zero logging, meaning it was NEVER
      re-fetched, forever, on every single trigger run. Added `_resolve_stale_league()` (mirrors
      `_canonical_league_id`'s own numeric-resolution pass: falls back to `get_league_by_api_football_id(int(lid))` when
      `get_league(lid)` returns `None` and `lid.isdigit()`), and now logs a `logger.warning` naming every stale
      `league_id` that STILL can't resolve via either path (previously 100% silent) — this closes part of open question
      (a) (raw-numeric entries were being silently dropped, not just theoretically at risk) and makes (c) empirically
      answerable on the next live trigger run (the new warning log directly reports the count + identity of
      genuinely-unresolvable cells vs. previously-invisible-but-now-fixed numeric ones). 2 new unit tests
      (`test_raw_numeric_league_id_resolves_via_af_id_fallback`,
      `test_unresolvable_numeric_league_id_skipped_and_logged`); all 17 tests in the file pass; full `quality-gates.sh`
      green (sentinel matches shipped SHA). **(b) and (c) remain genuinely open** — this fix resolves a real silent-drop
      bug but does NOT explain why a CANONICAL-resolved league's own 648-fixture season cache misses a date its manifest
      claims exists (slot-8's original, still-unexplained anomaly) — see new todo below.

- [x] ✅ [DATA] P1. Root-cause why a CANONICAL-resolved league's `_fetch_season_fixtures_with_raw` season cache (648
      fixtures for league_id=129/Argentine Primera Nacional, season=2026) returns ZERO matches for
      `fx.kickoff_utc.date().isoformat() == date` on a specific flagged date (e.g. `2026-06-27`) whose
      `fixtures_schedule` manifest row claims a fixture exists there — slot-8's original anomaly, NOT explained by the
      raw-numeric silent-drop bug fixed above (this league resolved fine). Season-year computation was verified correct
      for this case (`_effective_season_for_league(129, ref_date)` with `season_months=(2,11)` → season 2026 for any
      March/June/July 2026 date, confirmed via direct `.venv/bin/python` invocation) — NOT a wrong-season bug. Candidate
      directions for the next session: (i) whether the specific match on that date is tracked under a DIFFERENT
      api_football league id in their system (e.g. a cup/playoff stage) even though our `LeagueDefinition` groups it
      under the same canonical id — `/fixtures?league=129&season=2026` would then genuinely never return it; (ii)
      whether `kickoff_utc` on the season-cache fixtures for this league is somehow NOT exactly UTC despite `_iso()`'s
      handling (spot-check the raw `af_response['fixture']['date']` string for a known fixture on the flagged date
      against its parsed `kickoff_utc.isoformat()`); (iii) run the live re-fetch again with the NEW loud-logging from
      the fix above to get a clean count of genuinely-unresolvable vs. now-fixed cells, THEN re-examine whether any
      residual "0 matches" cases are canonical-resolved (this bug) or raw-numeric (already fixed). Needs live GCS +
      api-football queries against production data — a bounded, focused session, not a static-code read. (repo:
      instruments-service) — **2026-07-19T~18:3xZ (slot-7, data_engineering) — instruments-service@b664aaa6:
      ROOT-CAUSED + FIXED, live-verified against production.** Ruled out both candidate hypotheses (i)/(ii) directly:
      live-fetched the real 648-fixture season cache for league=129/season=2026 — all 648 raw `fixture.date` strings
      carry a `+00:00` offset (candidate (ii), non-UTC offset, DISPROVEN — `_iso()`'s tz handling is not at fault here),
      and the season cache genuinely contains ZERO fixtures dated 2026-06-27 (dates jump 06-23→07-04, a real gap, not a
      league-id split per candidate (i)). Cross-referenced the captured `fixtures_schedule` blob for `date=2026-06-27`
      directly: 18 rows with `af_league_id==129`, all `status_short=NS`, `af_fixture_id` range 1498613-1498630. Queried
      api-football's `/fixtures?id=<id>` directly for 3 of those ids: ALL still resolve under
      `league.id=129 season=2026`, but `fixture.date` now reads `2026-07-04`/`2026-07-05` with `status=FT` (Match
      Finished). Extended the check to all 18 captured ids — **100% (18/18) confirmed moved to a different live date**,
      0 vanished, 0 unchanged. **Actual root cause**: the entire round of Primera Nacional matches originally scheduled
      for 2026-06-27 was POSTPONED by the league to 2026-07-04/07-05 sometime after capture. The season-cache date
      filter (`fx.kickoff_utc.date().isoformat() == date`) always reflects the CURRENT live schedule — it can never find
      a rescheduled fixture under its OLD captured date again, no matter how many times it's re-queried. Not a bug in
      season fetch, league resolution, or timezone handling — a genuine data-modeling gap: nothing detects/recovers a
      fixture whose real-world date changed after capture. **Fixed**: added `ApiFootballAdapter.get_fixtures_by_ids()`
      (direct `/fixtures?ids=<id>-<id>-...` lookup, batched 20/call, bypassing date/league filtering entirely) + a
      base-adapter default (empty list) for non-api_football sources. Added `_find_stale_fixture_ids_for_date()`
      (fixture-level sibling of `_find_stale_fixture_leagues_for_date`) and wired a reschedule fallback into
      `run_sports_fixture_status_refresh`: any stale fixture the season-cache date filter can't find is re-fetched
      directly by id — which ALSO recovers fixtures whose `league_id` couldn't be resolved (no league resolution needed
      for a by-id lookup), closing that residual gap for free. Refactored the trigger into
      `_resolve_stale_league_af_ids` + `_reschedule_fallback_fetch` helpers to stay under the module-function-size gate
      (200L). 12 new/updated unit tests across 3 test files (adapter batching/pagination/ error-reraise,
      fixture-id-level scan, and 4 new trigger-level reschedule-fallback scenarios incl. error isolation +
      unresolved-league recovery); full `quality-gates.sh` green (sentinel matches shipped SHA, exit 0). Note: this is a
      status-refresh-time RECOVERY (the row gets its correct terminal status re-written under its original `day_str`
      partition once the by-id fallback fires on a future scheduled run) — it does not retroactively move the GCS
      partition itself; a `(b)`/`(c)`-style "how much of the corpus is affected" sweep was out of this task's root-cause
      scope and would need its own bounded investigation if the operator wants a corpus-wide estimate.

- [ ] [DATA] P1. **Add an off-season/no-fixture-that-date gap-closer for the 4 per-fixture ENRICHMENT entities
      (FIXTURE_EVENTS/FIXTURE_LINEUPS/FIXTURE_STATS/PLAYER_STATS) — they have NO equivalent to `process_write.py`'s
      `_expected_af_lids - _captured_lids` off-season closer, which only covers the core `FIXTURES` entity.** Found
      2026-07-19T~19:00-20:20Z (slot-4, `sports_p2_history_apifootball_2015_to_present-001`) while investigating why the
      `-001` full-history enrichment gate's `pending_fetch` total (5,515) stayed byte-identical across 5 independent
      reads spanning ~2h15m despite a healthy, actively-fetching 4-VM fleet that provably walked PAST several flagged
      pending clusters without them clearing (confirmed via `[[VM_PROGRESS]] last_completed_date=` VM checkpoints vs. a
      fresh per-VM-shard gate re-read). Direct targeted reads
      (`date, data_type, capture_status, error_reason,     league_id` columns) on two sampled clusters show the SAME
      shape: `FIXTURE_STATS 2020-06-14` = 95 cells, 92 already closed (`captured`/`empty_confirmed`), only 3 still
      `expected_unattempted` — specific leagues `AUSTRIAN_BUNDESLIGA`/`AUSTRIAN_2_LIGA`/`GREEK_SUPER_LEAGUE`;
      `FIXTURE_EVENTS 2020-08-16..19` = 380 cells, 378 closed, only 2 pending — `UEL` (2020-08-16) and `A_LEAGUE`
      (2020-08-19). **Root cause (code-traced, NOT yet live-verified against a specific reproducing fixture)**:
      `instruments_service/engine/orchestrator/sports_reference_fixtures.py`'s per-fixture enrichment loop is keyed
      ENTIRELY off `af_fid_to_league` — built from fixture IDs that ACTUALLY EXIST for that date (the core `FIXTURES`
      capture). A league with genuinely ZERO fixtures that date NEVER appears in `af_fid_to_league`, so it never reaches
      ANY of this loop's `record_captured`/`record_empty`/`record_failed` calls for these 4 entities — there is no
      per-league "this league had no matches today, confirm empty" path here, unlike
      `instruments_service/engine/orchestrator/process_write.py:315-360`'s `_expected_af_lids - _captured_lids` loop
      (added for the `FIXTURES` entity itself, `api_football_fixtures_stuck_612_residual_2026_07_15`, using
      `EmptyConfirmedReason.EXPECTED_PAUSED_LEAGUE` off `get_league_fixture_calendar`). If a broad seed process
      originally stamped `expected_unattempted` for these 4 entities across the FULL (date × 94-league) cross-product
      (matching TEAMS/INJURIES' seeding pattern elsewhere in this doc), then any (date, league) cell where that league
      had zero fixtures that date is STRUCTURALLY UNCLOSABLE by these 4 entities' current write path — no amount of
      fleet re-fetching, however many times repeated, can ever visit that key. This would explain why THIS EXACT task
      has bounced 20+ times across `sports_p2_history_apifootball_2015_to_present-001` and its predecessor plans without
      the gate ever reaching 0 despite enormous cumulative fetch effort. **NOT yet confirmed** as the sole/complete
      explanation — needs: (a) live confirmation that `AUSTRIAN_2_LIGA`/`GREEK_SUPER_LEAGUE`/`UEL`/`A_LEAGUE` genuinely
      had 0 fixtures on their specific flagged dates (via a direct api-football query, mirroring the -009 methodology
      above) rather than some OTHER stall reason; (b) a corpus-wide check of whether ALL 5,515 residual `pending_fetch`
      cells across the 4 entities fit this "league had zero fixtures that date" shape, or whether some are a distinct
      mechanism; (c) if confirmed, design + ship the mirror fix — likely reusing
      `_expected_af_lids`/`get_league_fixture_calendar`/`EXPECTED_PAUSED_LEAGUE` from `process_write.py`, applied once
      per date across all 4 enrichment entities for `expected_af_lids - {leagues in af_fid_to_league}`. **Caution**:
      this write path is shared/high-blast-radius (every date × every league) and this plan's own history
      (`sports_index_recency_masked_captured_atoms_2026_07_13`,
      `legacy_seed_captured_outranks_resurrection_risk_2026_07_15`) shows a wrong empty-reason/grain choice here has
      previously caused expensive-to-diagnose false-empty corruption — do NOT ship without a live-fetch spot-check
      confirming the target cells are genuinely zero-fixture, not some other stall. (repo: instruments-service)
