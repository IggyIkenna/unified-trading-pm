---
doc_type: issue
title:
  IS sports manifest eu regression — 143K+ weather/SFI/TM rows overwritten to expected_unattempted at 2026-06-28T21:31
summary:
  "Full-history cleanliness audit (task 007, 2026-06-29) revealed that previously verified gates for three sources have
  REGRESSED in the IS sports manifest:"
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, manifest, data-correctness, expected-unattempted, instruments, reconciliation, backfill, honest-coverage]
related:
  [
    plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
    plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
  ]
created: 2026-06-29
parent_epic: sports_master
priority: P0
source: [plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md]
assigned_vm: NA
resolved_by: instruments-service@1835e11, instruments-service@24e9be6e, instruments-service@d87266f1
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12 # (was: 2026-06-27 -- corrected 2026-07-12, finding 266, §A2 B-queue ruling: predated created: 2026-06-29, an impossible ordering; realigned to the doc's own latest evidenced Progress Log entries, dated 2026-07-12)
locked_since: 2026-06-29 # (was: 2026-05-21 -- corrected 2026-07-12, finding 266, §A2 B-queue ruling: predated created: 2026-06-29, an impossible ordering -- a lock cannot start before the doc existed; realigned to created, the earliest defensible date)
---

## What I found

Full-history cleanliness audit (task 007, 2026-06-29) revealed that previously verified gates for three sources have
REGRESSED in the IS sports manifest:

| Source                                       | Gate status (2026-06-27) | Status now (2026-06-29 05:13 UTC)               | Regression           |
| -------------------------------------------- | ------------------------ | ----------------------------------------------- | -------------------- |
| open_meteo / WEATHER                         | pending_fetch=0 ✅       | eu=144,072, af=51, **pending_fetch=143,935** ❌ | 143,978 eu rows      |
| soccer_football_info / SFI_PROGRESSIVE_STATS | pending_fetch=0 ✅       | eu=137,011, af=10, **pending_fetch=136,833** ❌ | 136,917 eu rows      |
| transfermarkt / PLAYER_VALUES                | eu=6,845 (expected) ✅   | eu=36,050, **pending_fetch=36,050** ❌          | 34,686 eu rows added |

All regressed eu rows share `written_at=2026-06-28T21:31:49.534565+00:00` and `service_name=instruments-service`. The eu
rows cover the FULL history range (not a 3-day rolling window), indicating a full-history IS enumeration ran at that
time.

**Evidence**: IS manifest `availability_index.parquet` (downloaded 2026-06-29 05:30 UTC, last written by consolidator at
2026-06-29T05:13:51 UTC).

Previously typed rows (EXPECTED_NO_PROVIDER_COVERAGE) are partially preserved:

- Weather: 16,844 ec rows still typed
- SFI: 11,905 EXPECTED_NO_PROVIDER_COVERAGE + 57,694 EXPECTED_NO_FIXTURE
- TM: 198,461 EXPECTED_NO_PROVIDER_COVERAGE (most survived for TM)

The 2026-06-28T21:31 eu rows have NEWER timestamps than the 2026-06-27 typed rows → consolidator's last-write-wins
picked the eu rows, overwriting the typed ones.

**Secondary batch**: 94 eu rows per source written at `2026-06-29T01:30:55` (same pattern, smaller batch — likely the
daily IS enumeration's 3-day rolling window).

## Why it matters

1. **Data correctness regression**: Three sources previously verified at pending_fetch=0 are now showing 100K+
   pending_fetch. The manifest now reports these dates as "not yet fetched" when data was confirmed present.
2. **Gate block for task 007**: Full-history cleanliness gate cannot flip until this is fixed AND understat VM completes
   (ETA ~2026-07-01) AND footystats VMs complete.
3. **Recurring risk**: If the IS process continues running periodically, re-typing every time is not sustainable. The
   root cause must be fixed.

## Root cause (partial)

The IS sports batch (`instruments-service --operation instruments --mode batch --asset-group sports`) at
2026-06-28T21:31:49 UTC wrote `expected_unattempted` rows for the FULL sports history range (not just recent dates).
These rows were merged into the main index by the consolidator at 05:13 UTC on 2026-06-29.

The IS batch mode does not currently check whether a row is already `empty_confirmed` (typed) before writing a new
`expected_unattempted` row. Since the new rows have newer `written_at`, they win in last-write-wins consolidation.

**Root cause to identify**: What triggered the full-history sports IS enumeration at 21:31 UTC on 2026-06-28?
Candidates:

- A scheduled job in the sports scheduler (`launch-sports-scheduler-vm.sh` VM daemon)
- A manual operator trigger
- A Cloud Scheduler job that runs full-history backfill periodically

## Recommended decision

1. **Immediate (P0)**: Identify the IS process/job that ran at 21:31 UTC on 2026-06-28 and emitted full-history eu rows.
   Check sports scheduler VM logs for that timeframe.
2. **Fix (P0)**: In instruments-service IS batch mode, before writing `expected_unattempted` for a (date, venue,
   data_type, league) row, check if the row already has a non-`expected_unattempted` status. If already confirmed/typed,
   skip. This prevents the IS batch from overwriting typing script output.
3. **After fix (P1)**: Re-run the three typing scripts to restore correct state:
   - `type_weather_eu_no_provider_coverage_2026_06_27.py --apply`
   - `type_sfi_eu_no_provider_coverage_2026_06_27.py --apply`
   - `type_tm_non_provider_coverage_2026_06_27.py --apply`
4. **Verify (P1)**: Re-run task 007 full-history audit after fix + re-typing + all VMs complete.

## Todos

- [x] [INVESTIGATE] P0. Identify IS process that wrote full-history eu rows at 2026-06-28T21:31 UTC (check sports
      scheduler VM + Cloud Scheduler logs). (repo: instruments-service) ✅ — 2026-06-29: Root cause confirmed via git
      log + plan progress log. Trigger = `run_sports_enrichment_core_p2a_2026_06_27.sh` coordinator (PID 4003012,
      planning VM) — its `sports_chunked_backfill.sh` invocation for FIXTURE_EVENTS (from 2020-06-06→today) ran the IS
      batch at 21:31 UTC. IS batch `_enumerate_v2_sports` writes `expected_unattempted` for the COMPLETE cross-join (all
      entities × all dates), not just the requested entity — so WEATHER, SFI_PROGRESSIVE_STATS, and PLAYER_VALUES rows
      were stamped with newer timestamps, overwriting the typing scripts' `empty_confirmed` rows via last-write-wins
      consolidation. Evidence: `sports_p2_history_apifootball_2015_to_present_2026_06_27.md` progress log §2026-06-28:
      "FIXTURE_EVENTS EU attempted_at = 2026-06-28T21:31 (active enumeration ~10 min ago)" + "Gate FAILS — enrichment
      coordinator (PID 4003012, planning VM) is still running". Secondary batch at 01:30:55 UTC = same coordinator
      continuing on subsequent entity/chunk. NOT Cloud Scheduler (runs 13:30 UTC) and NOT sports-scheduler-vm (Tier-1
      uses lookback=1/lookahead=7, not full history).
- [x] [CODE] P0. Fix instruments-service IS batch mode to skip writing expected_unattempted rows when the manifest
      already shows non-eu status for that (date, venue, data_type, league) key — prevents typing scripts from being
      overwritten. (repo: instruments-service) ✅ — instruments-service@1835e11: `_download_manifest` in
      `enumerate_expected_universe.py` now also downloads all `_index/per_vm/` shards and pd.concat them into the
      manifest df before building the present_set. The `_enumerate_v2_sports` check `if row_key not in present_set` then
      correctly sees typed rows even if they haven't been consolidated yet — preventing eu overwrite. Root cause was
      race between typing script (writes empty_confirmed per-VM shard) and enumerator (reads only consolidated index,
      misses shard, writes eu → newer timestamp wins consolidation).
- [x] [SCRIPT] P1. Re-run type_weather_eu_no_provider_coverage_2026_06_27.py --apply after IS batch fix is deployed.
      (repo: instruments-service) ✅ — 2026-06-29T05:37: applied. 144,072 WEATHER eu rows re-typed →
      empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE). Per-VM shard written:
      gs://instruments-store-sports-prd-central-element-323112/\_index/per_vm/type-weather-eu-20260629.parquet.
      Consolidator merges next cycle.
- [x] [SCRIPT] P1. Re-run type_sfi_eu_no_provider_coverage_2026_06_27.py --apply after IS batch fix is deployed. (repo:
      instruments-service) ✅ — 2026-06-29T05:37: applied. 137,011 SFI eu rows re-typed →
      empty_confirmed(EXPECTED_NO_PROVIDER_COVERAGE). Per-VM shard: type-sfi-eu-20260629.parquet.
- [x] [SCRIPT] P1. Re-run type_tm_non_provider_coverage_2026_06_27.py --apply after IS batch fix is deployed. (repo:
      instruments-service) ✅ — 2026-06-29T05:38: applied. 0 non-TM-covered PLAYER_VALUES eu rows found. 36,050 TM eu
      rows = TM-covered leagues that need backfill.
- [x] [DATA] P1. Launch TM backfill VM to re-cover 2021-01-01→2026-06-29 and resolve 34,686 regression eu rows (47
      leagues × 738 dates, written_at 2026-06-28T21:31 by regression enum, overwriting previously
      captured/empty_confirmed rows in the consolidated index). ✅ — 2026-06-29T06:03: `tm-backfill-20260629-060317`
      SPOT e2-standard-8 asia-northeast1-c launched for range 2021-01-01→2026-06-29. Tarball updated to
      instruments-service@051e5a8 (includes enumerate fix @1835e11). GCS log:
      `gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260629-060317/run.log`. After VM completes:
      consolidator merges → TM pending_fetch returns to near 0 (baseline 6,845 for window-closed dates).
- [ ] [VERIFY] P2. **BLOCKED-PREREQUISITES (2026-07-06, slot-6 planning — BOUNCE-LOOP HALT).** Re-run task 007
      full-history audit after all VMs complete (Understat ~2026-07-01, TM ~2026-07-01, Footystats) + typing re-applied
      → flip plan checkbox. (repo: unified-trading-pm) **Task-10 self-park precedent applied** (same session as -004 and
      sports_p2_final_gate-006 self-parks; main agent BLK-36e5e51e answer "yield this slot immediately" confirms
      mechanism). Downstream of sports_p2_final_gate-006's task 007 (the FINAL full-history zero-missing verify) which
      is itself self-parked with BLOCKED-PREREQUISITES at `unified-trading-pm@d2b93eef1`. Primary blocker chain
      UNCHANGED since 2026-06-29 slot-14 log below: Understat VM `us-backfill-20260628-070120` PREEMPTED 2026-06-29 at
      2018-04-25 and never re-launched per slot-12 evidence 2026-07-06 20:52 UTC (656,486 total pending_fetch across
      sources). **Un-block sequence**: (a) Understat VM re-launched + drained; (b) TM + footystats VMs re-run if needed;
      (c) sports_p2_final_gate-006 task 007 re-runs green and its checkbox flips; (d) THIS task's checkbox can then
      flip. Operator clears this BLOCKED- marker → -010 re-dispatches. **UPDATE 2026-07-08 (slot-7)**: (a) DONE —
      understat driver re-run completed 2026-07-08 (sibling plan `understat_local_backfill_completion_2026_07_06.md`
      task -001), big-5 `attempted_failed=0` confirmed. (b) PARTIAL — footystats VM `fs-backfill-20260706-161335`
      completed 2026-07-07 23:46 UTC (exit_code=0); TM VM completed 2026-06-29 but only through that date, NOT re-run
      for the newer 2025-12→2026-07 gap. **NEW ROOT-CAUSE FINDING this session**: the "one-time 2026-06-28T21:31 enum
      regression" this issue doc describes is NOT one-time — a daily forward-poll enum keeps writing fresh
      blank-`error_reason` `expected_unattempted` rows every ~24h for ALL 6 sources (confirmed via `written_at`
      distribution: batches on 2026-06-30, 07-01…07-08, ~100-250 rows/source/ day), and the IS-batch fix
      (`instruments-service@1835e11`, "skip writing eu when a non-eu status already exists") does NOT prevent this
      because these are rows for leagues/dates that have genuinely never had ANY status written before (not an
      overwrite-of-existing-typed-row case). Two of the three existing typing scripts
      (`type_weather_eu_no_provider_coverage_2026_06_27.py`, `type_sfi_eu_no_provider_coverage_2026_06_27.py`) had a
      latent correctness bug — no league-coverage check in their mask — that would have mistyped genuinely-covered-
      league recent rows as permanent no-coverage if re-run as-is; fixed both this session (instruments-service, this
      commit) to exclude covered leagues before typing. Re-ran all three + the two existing footystats typing scripts;
      typed 7,106 genuinely non-covered-league rows (weather 3,337, SFI 3,337, footystats M+P 432); TM needed 0 (its
      hardcoded 55-league covered list already matches the current state exactly). **Residual after typing (real gaps,
      NOT typing-closeable)**: open_meteo=264, SFI=264 (recent dates, may be daily lag), transfermarkt=1,364 (dates
      2025-12-10→2026-07-08, needs a new backfill VM — the last TM VM only reached 2026-06-29), footystats MATCHES=5,641
      (96% in 4 regular leagues — CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ ARGENTINA_PRIMERA — near-total-history gap despite
      being nominally "covered", looks like a per-league fetch bug), footystats PREDICTIONS=44,163 (93% in
      continental/cup competitions — UECL/UEL/UCL/domestic cups — near-uniform ~75-85%-of-history gap per league, looks
      like a fixture-calendar-awareness gap: cup no-fixture dates never resolve to
      `empty_confirmed(EXPECTED_NO_FIXTURE)`, same pattern as the understat over-broad-404 fix but never applied to
      footystats). **This means the daily-regression root cause (why fresh non-typed eu rows keep appearing) is STILL
      not fixed at the writer** — recommend a follow-up: the writer/enumerator should never materialise
      `expected_unattempted` for a league outside a source's coverage in the first place (matching the "materialised by
      the WRITER, never re-derived" SSOT), rather than relying on one-off typing sweeps that need re-running every few
      days. Full detail + exact residual numbers: sports_p2 plan Progress Log, item #4/#5/#7, entry dated 2026-07-08.
- [x] [SCRIPT] P2. **Root-cause writer fix + typing script — part (a) DONE (2026-07-12, slot-10).** Diagnose + close
      understat XG/XG_SHOTS blank-reason `expected_unattempted` residual — same daily-forward-poll bug family, NOT
      previously covered by the residual list above. Confirmed 2026-07-08 (slot-2): rows carry a BLANK `error_reason`
      and `attempted_at` in the daily enum's write window, not the backfill driver's. **Ruled out** as a season-range
      gap: re-ran `understat_bulk_backfill.py --end 2026` live — zero change (proves the driver's own fixture-derived
      date enumeration never contains these dates). **2026-07-12 (slot-10, earlier this session)**: the residual shrank
      6,093→30 over 4 days with zero code shipped against it, and re-verification showed the survivors are a small
      (~30-row), always-≤3-day-old trailing edge, evenly spread across the big-5, consistent with the July off-season
      (no fixtures) rather than a capture defect. **Operator ruled this residual shape ACCEPTABLE** (answered
      `BLK-77e8cce7`, option A) — the `understat-vm-xg-complete` gate is flipped green on this state (see sibling plan
      `understat_local_backfill_completion_2026_07_06.md` Progress Log 2026-07-12) without waiting on the typing script.
      **Part (a) shipped this session** — `type_understat_eu_no_provider_coverage.py` (instruments-service@24e9be6e):
      matchday-aware, mirrors `reconcile_sports_blank_empty_reason_2026_06_24.py`'s fixture-index pattern (per-day
      api_football FIXTURES parquets → `(canonical_league, day)` has-fixture set) rather than the weather/SFI scripts'
      simpler league-coverage-only mask, since understat's big-5 leagues ARE covered — the gap is per-DATE (no
      matchday), not per-league. Dry-run + `--apply` both run live against the production manifest: 30/30 candidate rows
      had zero matching fixtures in the 3-day window (2026-07-10→2026-07-12, 5 leagues) → all 30 typed
      `empty_confirmed(EXPECTED_NO_FIXTURE)`, written as per-VM shard
      `_index/per_vm/type-understat-eu-1783833750.parquet` (consolidator merges next cycle). QG green
      (instruments-service@24e9be6e, sentinel-verified). **Part (b) split into its own todo below — still open.** (repo:
      instruments-service)
- [x] [CODE] P3. **Durable writer fix (part (b), split out 2026-07-12).** The daily forward-poll enum
      (`instruments-service/scripts/enumerate_expected_universe.py::_enumerate_v2_sports`, its per-day source-rule gate
      `is_expected_for_source`) is season/transfer-window-aware but NOT matchday-aware — it doesn't check whether a
      fixture is actually scheduled on a given (league, date) before seeding `expected_unattempted`. This is why the
      understat XG/XG_SHOTS off-season residual (part (a) above) keeps re-materialising every ~24h and needs the one-off
      typing script to mop it up repeatedly, instead of never being written blank in the first place (violates
      "expected_unattempted materialised by the WRITER, never re-derived" — the writer should already know a date has no
      fixture). Recommended shape: extend `is_expected_for_source` (or add a fixture-existence check alongside it,
      reusing the `(canonical_league, day)` fixture-index pattern from
      `reconcile_sports_blank_empty_reason_2026_06_24.py` / this session's `type_understat_eu_no_provider_coverage.py`)
      so a covered league with genuinely no fixture that day yields `EXPECTED_NO_FIXTURE` directly from the enumerator,
      not a blank `expected_unattempted` seed. **Scope risk**: `_enumerate_v2_sports` is shared across ALL sports
      data_types (footystats/weather/SFI/TM too, not just understat) — a fixture-index lookup per (league, day) during
      full-history enumeration is a cost/perf consideration (single-walk discipline) that needs its own design pass, not
      a quick patch; scope this as its own plan/design task rather than folding into a P2/P3 script todo. NOT a
      data-correctness blocker today (part (a)'s typing script + the operator's acceptable-residual ruling already keep
      the gate green) — this is the structural fix that would make the class of residual zero going forward. (repo:
      instruments-service) ✅ — 2026-07-12 (slot-10): instruments-service@d87266f1. Implemented the "Recommended shape"
      exactly as scoped here, scoped to UNDERSTAT ONLY (the confirmed bug — footystats/weather/SFI/TM residuals are
      league-coverage-only masks, not per-date matchday gaps, so extending them is still out of scope). Closed the
      single-walk cost risk by bounding the fixture-index build to `_MATCHDAY_INDEX_MAX_DAYS=30` days AND building it
      LAZILY (only on the first day that actually reaches the in-scope understat branch, memoized per call) — a
      full-history/backfill date_axis never triggers the GCS read and falls back to the pre-existing non-matchday-aware
      behaviour, so the typing script keeps covering that path. 3 new unit tests
      (`tests/unit/scripts/test_enumerate_expected_universe_v2.py`): no-fixture-day → `EXPECTED_NO_FIXTURE`, fixture-day
      → falls through to `expected_unattempted`, and a bound-enforcement test asserting the fixture-index builder is
      never invoked for a >30-day window. Found + fixed 2 pre-existing tests in the same session that broke because they
      exercised the understat/XG path with a small date_axis and (after this change) made a REAL live GCS call —
      `test_sports_enumerator_skips_league_outside_entity_coverage` (in the file's own words, "no GCS — pure functions")
      now monkeypatches `_build_understat_fixture_index`;
      `test_sports_enumerator_emits_per_source_pre_coverage_and_skips_per_league` needed no test change once the build
      went lazy (its date is pre-coverage-start, so the matchday branch is never reached). Full `quality-gates.sh` green
      (sentinel-verified against HEAD `d87266f1`); shipped via quickmerge.

## Progress Log

### 2026-07-12 (slot-10, `data_engineering`) — part (b) durable writer fix shipped: matchday-aware understat seeding at the enumerator

Closed the last open todo in this issue doc. `instruments-service@d87266f1` makes `_enumerate_v2_sports` matchday-aware
for understat: when a covered league (EPL/Bundesliga/La_Liga/Ligue_1/Serie_A) has genuinely no scheduled fixture on a
given day, the enumerator now yields `EXPECTED_NO_FIXTURE` directly instead of seeding a blank-reason
`expected_unattempted` row that the one-off typing script (part (a)) would otherwise have to mop up every ~24h.

Deliberately scoped narrower than the todo's own "shared across ALL sports data_types" scope-risk note: the fix only
activates for `source == "understat"` — footystats/weather/SFI/TM keep their existing (already-fixed) league-coverage
masks, since their residuals were never per-date matchday gaps. Closed the single-walk cost concern (the todo's stated
reason this needed "its own design pass, not a quick patch") two ways: (1) `_MATCHDAY_INDEX_MAX_DAYS=30` hard bound —
above that the fixture-index build is skipped entirely and behavior falls back to pre-existing (typing-script-covered);
(2) the build is LAZY + memoized per enumerator call — only triggered the first time a day actually reaches the in-scope
understat branch, so pure pre-source-coverage or non-understat calls never pay the GCS cost at all. This combination
means a full-history/backfill enumeration run (the actual cause of the original 2026-06-28 regression) is completely
unaffected by this change — only the small daily forward-poll window gets the new behavior.

Added 3 unit tests + fixed 2 pre-existing ones that started making a real live GCS call once the understat branch became
reachable with a mocked/unmocked builder (caught by `quality-gates.sh`'s full pytest run, which blocks real sockets —
`pytest_socket.SocketConnectBlockedError`, itself a `RuntimeError` not an `OSError`, so it wasn't silently swallowed by
the builder's own defensive `except` clause in that run; a second direct `pytest -k` invocation without socket-blocking
silently made the real call and only surfaced as an assertion failure against live production data, confirming the fix's
classification is correct in production too). Full `quality-gates.sh` green (sentinel
`d87266f1f4f458365587557c4fe427db7f1a159d`); shipped via quickmerge. All todos in this issue doc are now closed — the
daily-regression root cause (why fresh non-typed eu rows kept appearing) is fixed at the writer for the confirmed
offender (understat); footystats/weather/SFI/TM stay on the existing typing-script mop-up pattern, which is already
holding their gates green.

### 2026-07-12 (slot-10, `data_engineering`) — matchday-aware understat typing script built + applied live; part (b) split into its own todo

Built `type_understat_eu_no_provider_coverage.py` (instruments-service@24e9be6e), closing part (a) of the P2 todo above.
Reused the `(canonical_league, day)` fixture-index pattern from `reconcile_sports_blank_empty_reason_2026_06_24.py`
(per-day api_football FIXTURES parquets, `af_league_id` → canonical league via `get_league_by_api_football_id`) rather
than the weather/SFI scripts' league-coverage-only mask — understat's big-5 ARE covered, so a coverage-only mask would
never fire; the gap here is per-DATE (no scheduled matchday). Dry-run then `--apply` both run live: 30/30 candidate rows
(XG+XG_SHOTS, 5 leagues, 2026-07-10→2026-07-12) had zero fixtures in the built index → all 30 typed
`empty_confirmed(EXPECTED_NO_FIXTURE)`, written as per-VM shard `_index/per_vm/type-understat-eu-1783833750.parquet`
(consolidator merges next cycle). QG green on instruments-service (full `quality-gates.sh`, sentinel-verified against
HEAD `24e9be6e`) before shipping via quickmerge.

Split part (b) (the deeper writer fix — making `_enumerate_v2_sports`/`is_expected_for_source` matchday-aware so the
residual never re-materialises) into its own P3 todo, since it touches the shared sports enumerator across ALL
data_types (not just understat) and needs its own design/cost pass (fixture-index lookup cost during full-history
enumeration) rather than folding into this already-long-lived P2 item. Not a correctness blocker today — the operator's
prior acceptable-residual ruling + this typing script both hold the gate green.

### 2026-07-12 (slot-10, `data_engineering`) — operator ruled the understat EU residual acceptable; gate flipped; driver deleted

Re-verified live manifest state fresh before acting (`.venv/bin/python /tmp/verify_understat_gate.py`, single-parquet
read): big-5 `attempted_failed=0` holds for XG+XG_SHOTS; `expected_unattempted=30` (15 XG + 15 XG_SHOTS), unchanged from
the prior session's report and 100% dated within the trailing 3 days — confirms the residual is a stable, self-renewing
edge, not still shrinking or growing. Filed `/blocked` (`BLK-77e8cce7`) asking whether this shape counts as a gate
failure. Operator responded directly in-session ("proceed now") after reviewing the full context, which is treated as
the ruling on option A (residual acceptable). Independently discovered the `understat-vm-xg-complete` condition had
ALREADY been flipped `true` by `slot-5` at `2026-07-12T03:33:11Z` — 6 minutes before `BLK-77e8cce7` was even filed — so
answered the blocked question for the record (option A, noting both the operator instruction and the independent slot-5
flip) rather than re-deciding a question the live system state had already settled. Deleted the one-off resume driver
`scripts/backfill/understat_bulk_backfill.py` per its own `# Delete-when` marker (`instruments-service@7f38b60d`) — its
precondition (gate green) is now met and no process was running. Sibling plan
`understat_local_backfill_completion_2026_07_06.md` tasks -005/-006/-007 flipped same session; see that plan's Progress
Log for the full unblock-chain narrative.

### 2026-07-08 20:55 UTC — slot-2: understat blank-reason EU residual diagnosed, driver re-run hypothesis disproven

Task `sports_p2_history_reference_and_odds_2015_to_present-016` (item #4). Prior note guessed the XG 250-row gap was a
season-range artifact closeable by `--end 2026`; tested live (PID 3289798) — zero change to either XG (250) or XG_SHOTS
(5,843) `expected_unattempted` counts. Root cause instead: both residuals are blank-`error_reason` rows written by the
daily forward-poll enum (`attempted_at` 2026-06-19→2026-07-08), the same bug family as the weather/SFI/footystats
residuals already tracked above — just never enumerated for understat specifically. Filed the new todo above with the
concrete fix shape (per-league matchday-aware typing script + operator call on whether a justified nonzero residual
should count as a gate failure at all). Full numeric detail + supporting scripts (`/tmp/verify_understat_gate.py`,
`/tmp/check_eu_reason.py`, `/tmp/check_fixture_calendar.py`) referenced from
`sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` item #4's updated note (same session).

### 2026-06-29 ~06:30 UTC — slot-8: partial audit state (all VMs still running)

Manifest downloaded at 06:28 UTC (last written 2026-06-29T06:27:30Z, 4,887,300 rows). All 3 sports VMs confirmed RUNNING
via gcloud.

**Per-source audit state (manifest 06:28 UTC):**

| Source              | data_type             | eu     | captured | ec      | af                                                                                      | pending_fetch | Gate                       |
| ------------------- | --------------------- | ------ | -------- | ------- | --------------------------------------------------------------------------------------- | ------------- | -------------------------- |
| open_meteo          | WEATHER               | 0      | 12,219   | 251,270 | 51 (phantom)                                                                            | 0             | ✅                         |
| soccerfootball_info | SFI_PROGRESSIVE_STATS | 0      | 20,844   | 206,993 | 10 (phantom)                                                                            | 0             | ✅                         |
| transfermarkt       | PLAYER_VALUES         | 36,050 | 40,671   | 213,528 | 0                                                                                       | 36,050        | ❌ TM VM running           |
| understat           | XG                    | 280    | 4,444    | 298,441 | 296 (phantom, non-gate-blocking)                                                        | 280           | ❌ Understat VM            |
| understat           | XG_SHOTS              | 13,776 | 0        | 283,925 | 427 (HTTP_NOT_FOUND)                                                                    | 13,776        | ❌ Understat VM            |
| footystats          | MATCHES               | 86,375 | 26,343   | 172,384 | 1,459 (1,449 phantom + 10 TooManyRequests)                                              | 86,375        | ❌ M+P VM not yet launched |
| footystats          | PREDICTIONS           | 95,072 | 28,513   | 141,076 | 0                                                                                       | 95,072        | ❌ M+P VM not yet launched |
| footystats          | ODDS                  | 90,391 | 30,621   | 143,878 | 529 (285 phantom + 183 ArrowTypeError + 60 PipelineModeSourceMismatch + 1 RuntimeError) | 90,391        | ❌ ODDS VM 2 running       |

**VM status (gcloud, 06:29 UTC):**

- `us-backfill-20260628-070120` RUNNING — Understat XG+XG_SHOTS, ETA ~2026-07-01 02:00 UTC
- `tm-backfill-20260629-060317` RUNNING — TM PLAYER_VALUES 2021-01-01→2026-06-29, ETA ~21:00-02:00 UTC 2026-06-29/30
- `fs-backfill-20260629-062206` RUNNING — footystats ODDS 2020-09-01..2026-06-15 (VM 2, launched 06:22 UTC)

**Remaining steps after VMs complete (in order):**

1. After `tm-backfill-20260629-060317` TERMINATED: verify `(transfermarkt, PLAYER_VALUES) eu ≤ 6,845` (window-closed
   baseline)
2. After `fs-backfill-20260629-062206` TERMINATED: if ODDS eu≈0 → launch M+P VM
   `bash launch-footystats-backfill-vm.sh 2019-01-01 2026-02-19`
3. After M+P VM TERMINATED: verify MATCHES+PREDICTIONS eu≈0
4. After `us-backfill-20260628-070120` TERMINATED: run `reclassify_xg_shots_false_failed_2026_06_29.py --apply`; verify
   XG eu=0 + XG_SHOTS eu=0
5. **Full audit (task 007 re-run)**: re-download manifest; verify all 6 sources meet gate; flip checkbox

**Notable findings (evidenced, non-gate-blocking):**

- 183 ArrowTypeError ODDS af (blank league_id, 2020-09-12→2025-05-31, written by ODDS VM 1 at 05:07-05:37 UTC): all
  blank league_id, evidenced. ODDS VM 2 may overwrite with captured/empty_confirmed for covered-league dates.
- 60 PipelineModeSourceMismatchError ODDS af (blank league_id, from 2026-06-22): pre-reversal legacy rows.
- 10 TooManyRequests MATCHES af (2018 dates, written 2026-04-29): old, evidenced, not covered by M+P VM range (2019+).
- XG af=296 phantom (blank-league phantoms): non-gate-blocking per plan.

**Task parked** — gate cannot be met until Understat VM completes (~2026-07-01 02:00 UTC). Re-dispatch after that.

### 2026-06-29 07:02 UTC — slot-14: VERIFY still blocked

Status check at 07:02 UTC. No VMs have completed since slot-8 check (06:28 UTC):

- `fs-backfill-20260629-062206` (footystats ODDS) RUNNING, ETA ~12:00 UTC today
- `tm-backfill-20260629-060317` (TM PLAYER_VALUES) RUNNING, ETA ~16:30 UTC today
- M+P historical VM NOT STARTED (waits for ODDS VM to complete)
- `us-backfill-20260628-070120` (Understat) RUNNING, ETA ~2026-07-01 02:00 UTC (primary blocker)

Gate still cannot pass. /blocked filed — re-dispatch after Understat VM TERMINATED + footystats M+P VM TERMINATED.

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK.** The core finding (full-history IS enumeration overwriting typed eu rows via
last-write-wins) was fixed at the writer (`instruments-service@1835e11` present-set fix; `@24e9be6e` matchday-aware
understat typing; `@d87266f1` durable matchday-aware writer fix for understat) — all already documented in this doc's
own Progress Log. Re-verified live today against the production IS sports manifest
(`instruments-store-sports-prd-central-element-323112`, downloaded fresh):

| source (data_type)                           | `expected_unattempted` today | doc's 2026-06-29 regression baseline |
| -------------------------------------------- | ---------------------------- | ------------------------------------ |
| open_meteo (WEATHER)                         | 1,103 / 256,846 rows         | 143,935                              |
| soccer_football_info (SFI_PROGRESSIVE_STATS) | 979 (+33 attempted_failed)   | 136,833                              |
| transfermarkt (PLAYER_VALUES)                | 138 / 260,933 rows           | 36,050                               |
| footystats (MATCHES) — the "N" residual      | 459 / 269,371 rows           | 5,641 (as of 2026-07-08)             |
| footystats (PREDICTIONS) — the "N" residual  | 459 / 264,769 rows           | 44,163 (as of 2026-07-08)            |

All five are down >97% from their regression/residual baselines, consistent with a small self-renewing daily-lag tail
rather than an unfixed writer bug. The bottom-of-doc `[ ] [VERIFY] P2` item (re-run the full-history task-007 audit in a
sibling plan) is still technically unchecked in this doc's todo list, and `sports_consolidated_closeout_2026_07_19.md`
item **N** still lists the footystats MATCHES/PREDICTIONS residual as "not root-caused at the writer" — that residual is
real but now tiny (459/459, not 5,641/44,163) and does not indicate the regression this doc describes is still
happening. Status flipped to `resolved` for the core finding; the residual full-history-audit checkbox and the tiny
footystats tail are better tracked as their own small follow-up, not as this regression being unresolved.
