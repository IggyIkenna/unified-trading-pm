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
- [ ] [DATA] P1. Backfill-correct already-written FIXTURES rows: for any already-captured date whose fixtures are still
      `status_short` NOT IN `{FT,AET,PEN,CANC,AWD,PST,ABD}` (i.e. non-terminal) AND the date is more than ~2 days in the
      past, re-fetch that date with `--force` — now that the write-path fix has shipped, this will actually persist the
      correct status (before the fix, `--force` re-fetched correctly but silently re-wrote the SAME wrong `NS` value,
      which is why the first attempt at this todo appeared not to work). Scope to the two known residual clusters first
      (2026-02-21..2026-03-22 mixed 30-45% NS; 2026-06-24..2026-07-14 ~100% NS) before considering a wider historical
      sweep — do NOT blanket-`--force` a mostly-already-correct window, it wastes real API-key budget on rows that don't
      need it. (repo: instruments-service)
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
- [ ] [DATA] P2. Audit other consumers of FIXTURES `status_short`/`status_long` (match-outcome features, any
      live-vs-settled dashboard/report) for downstream impact from the pre-fix corpus-wide `NS` mis-stamping — flag
      anything that silently treated "NS" as "not yet played" when the match may actually have concluded.

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
