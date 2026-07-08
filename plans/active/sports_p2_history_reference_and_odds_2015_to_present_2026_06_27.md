---
doc_type: plan
title:
  Sports P2b — reference + odds history to zero-missing (weather · SFI · transfermarkt · understat · footystats ·
  odds-api)
summary:
  Backfill all reference sources and MTDS odds across their full history coverage windows to zero-missing, generalising
  the golden-window recipe.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags:
  [sports, reference-sources, odds, history-backfill, 2015-present, weather, understat, footystats, transfermarkt, sfi]
related:
  [
    plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
    plans/active/sports_reference_backfill_oom_2026_06_22.md,
  ]
created: 2026-06-27
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by:
depends_on: [sports_p0_spot_vm_launchers_2026_06_27, sports_p1_golden_window_e2e_gate_2026_06_27]
source:
assigned_role: data_engineering
drift_direction: advance-code
---

> **🟢 TRANSFERMARKT BACKFILL RUNNING** — `tm-backfill-20260629-060317` SPOT e2-standard-8 asia-northeast1-c, launched
> 06:03 UTC 2026-06-29, range 2021-01-01→2026-06-29. Resolves 34,686 regression eu rows (IS enumerate overwrite at
> 2026-06-28T21:31; IS fix at instruments-service@1835e11 prevents future regression). Tarball:
> instruments-service@051e5a8. GCS log:
> `gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260629-060317/run.log`. Singleton lock active.

> **🟢 FOOTYSTATS M+P+ODDS FULL-HISTORY BACKFILL** — `fs-backfill-20260706-161335` SPOT e2-standard-8 asia-northeast1-c,
> launched 16:13 UTC 2026-07-06 by slot-11, range 2019-01-01..2026-07-05 (all entities: M+P+ODDS). Root cause: the M+P
> VM for 2019-01-01..2026-02-19 never ran after ODDS VM 2 completed; current state: PREDICTIONS eu=44,298 / MATCHES
> pending=6,569 / ODDS pending=1,595. GCS log:
> `gs://deployment-scripts-central-element-323112/vm-logs/fs-backfill-20260706-161335/run.log`. Singleton lock active.

> **🟡 UNDERSTAT SPOT VM PREEMPTED + LOCAL BACKFILL TERMINATED** — SPOT VM `us-backfill-20260628-070120` was preempted
> at 2026-06-29 14:49 UTC while still processing 2019-08-09 (no exit marker in run.log, last mtime 14:49:36Z; VM object
> deleted). Never relaunched. Sibling plan `understat_local_backfill_completion_2026_07_06.md` shipped a resume-aware
> LOCAL driver (`instruments-service/scripts/backfill/understat_bulk_backfill.py` @ 6716f55) — final process (PID
> 1782092 orphaned PPID=1) terminated 2026-07-06 20:46:53 UTC with `MAX ROUNDS reached; still 108 attempted_failed` +
> `UNDERSTAT BULK BACKFILL COMPLETE`. Post-run manifest for big-5 native leagues via `/tmp/verify_understat_gate.py`
> against `_index/availability_index.parquet` (5,387,490 total rows, 621,142 understat rows): XG `attempted_failed=0` /
> `expected_unattempted=315` (63/league × 5); XG_SHOTS `attempted_failed=384` (all `HTTP_NOT_FOUND`, attempted_at
> 2026-06-23 → 2026-06-29, i.e. pre-fix classify_error residue) / `expected_unattempted=13,811` (~2,762/league × 5).
> Hollow-shots check: XG_SHOTS `(date, league)` captured atoms match XG at 99.5–100% per big-5 league
> (EPL/LA_LIGA/SERIE_A 100.0%; BUNDESLIGA 99.7%; LIGUE_1 99.5%) — captured shots are REAL, not hollow. See Progress Log
> entry `2026-07-06 ~21:00 UTC — slot-7`.

> **🟢 ODDS-API (MTDS) BACKFILL RUNNING** — `mtds-backfill-odds-1` SPOT e2-standard-4 asia-northeast1-c, launched 21:12
> UTC 2026-06-27, range 2020-06-06..2026-06-27, 7-day chunks, MANIFEST_PER_VM_SHARDS=true. GCS log:
> `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-odds-1/run.log`. Runs concurrently with
> understat+footystats (separate singleton namespace `mtds-backfill-odds-*`).

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 2). Generalizes the
> golden-window recipe to ALL non-AF reference sources + MTDS odds across their full coverage windows — the R1/R3 "all
> these sources backfilled to zero-missing". **PREREQ: P1e GREEN.** One agent, `data_engineering` (Sonnet/high).
> Season-aware smart-skip within each source's `coverage_start`.

# Sports P2b — reference + odds history to zero-missing

## Scope + per-source coverage windows (the clips that define "zero-missing")

| Source              | data_type(s)                     | `coverage_start` | History to backfill                          | Launcher                                 |
| ------------------- | -------------------------------- | ---------------- | -------------------------------------------- | ---------------------------------------- |
| open_meteo          | `WEATHER`                        | 2019-03-02       | 2019-03→present (per captured fixture venue) | `launch-openmeteo-backfill-vm.sh`        |
| soccerfootball_info | `SFI_PROGRESSIVE_STATS`          | 2020-01-01       | 2020→present (single-stream)                 | `launch-sfi-backfill-vm.sh`              |
| transfermarkt       | `PLAYER_VALUES`(+`TRANSFERS`)    | 2019-01-01       | 2019→present (transfer-window-aware)         | `launch-transfermarkt-backfill-vm.sh`    |
| understat           | `XG`, `XG_SHOTS`                 | 2014-01-01       | 2014→present (5 native leagues only)         | `launch-understat-backfill-vm.sh`        |
| footystats          | `MATCHES`, `PREDICTIONS`, `ODDS` | 2019-01-01       | 2019→present (ODDS reversed 2026-06-27)      | `launch-footystats-backfill-vm.sh`       |
| odds_api (MTDS)     | `trades`/`odds_horizon_bucket`   | 2020-06-06       | 2020-06→present (bookmaker-league subset)    | `launch-mtds-sports-odds-backfill-vm.sh` |

Pre-`coverage_start` cells are `EXPECTED_PRE_SOURCE_COVERAGE_START`; per-source league subsets (understat 5, odds-api
restriction) are `EXPECTED_NO_PROVIDER_COVERAGE`/`EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE`. Each source has its own
singleton-lock namespace → may run concurrently.

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the sports
> launchers default to SPOT. Backfills are idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a
> preemption must NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/honest-absence-downstream-handling.md` — coverage clips + per-source subset typing
- `codex/02-data/availability-manifest-and-data-status.md` — single-walk discipline; `pending_fetch == 0` target
- `codex/02-data/sports-gcs-path-ssot.md` — per-source layouts

## Todos

- [x] [DATA] P0. **Weather history → zero-missing** 2019-03→present (per captured-fixture venue; the expected set
      follows P2a fixtures). **Gate**: full-history query `(open_meteo, WEATHER)` `pending_fetch == 0`; 0 blank-reason;
      silent-day class re-fetched or typed. 1. ✅ — weather-backfill-20260627-160501 VM ran 2019-03-02→2026-06-27
      (12,162 captured, 5,721 empty_confirmed). 2. ✅ — instruments-service@8ad3b57: source=open_meteo on all weather
      manifest calls + typing script. 3. ✅ — type_weather_eu_no_provider_coverage_2026_06_27.py applied (200,992
      non-expected-league EU rows → EXPECTED_NO_PROVIDER_COVERAGE). Gate: pending_fetch=0, 206,713 empty_confirmed,
      12,162 captured, 51 attempted_failed (typed).
- [x] [DATA] P0. **SFI history → zero-missing** 2020→present, single-stream (no chunks; 429-storm guard). **Gate**:
      `(soccerfootball_info, SFI_PROGRESSIVE_STATS)` `pending_fetch == 0` within window; 0 un-evidenced failed. ✅ —
      sfi-backfill-20260627-165435 VM running (SFI_PROGRESSIVE_STATS 2020-01-01→2026-06-27, e2-standard-8 SPOT). Gate
      verified 2026-06-27 17:46 UTC: pending_fetch=0, expected_unattempted=0, 20,841 captured, 259,813 empty_confirmed,
      10 attempted_failed (all evidenced: phantom_captured_no_parquet_at_canonical_path, 0 blank-reason).
      type_sfi_eu_no_provider_coverage_2026_06_27.py dry-run: 0 rows to type (manifest already clean).
- [x] [DATA] P0. **Transfermarkt history → zero-missing** 2019→present, transfer-window-aware (PER_DAY_PER_SEASON bulk;
      the OOM single-index-read fix from `sports_reference_backfill_oom` must be live). **Gate**:
      `(transfermarkt, PLAYER_VALUES)` `pending_fetch == 0` within window; window-closed days typed, not failed. ✅ —
      Gate verified 2026-06-28 UTC: pending_fetch=0, attempted_failed=0, captured=39,678, empty_confirmed=272,910,
      expected_unattempted=6,845 (transfer-window-closed dates, TM-covered leagues). VM tm-backfill-20260627-222604
      completed; typing script typed 8,744 non-TM leagues as EXPECTED_NO_PROVIDER_COVERAGE (@fbb032d).
- [ ] [DATA] P0. **Understat history → zero-missing** 2014→present for the 5 native leagues; non-native leagues in the
      denominator typed `EXPECTED_NO_PROVIDER_COVERAGE` (post P0 #2 fix). **Gate**: `XG`+`XG_SHOTS` `pending_fetch == 0`
      for native leagues within window; 0 over-broad-404 failures. **BLOCKED-PREREQUISITES (2026-07-08, slot-2) —
      corrects the prior slot-7 hypothesis, which was tested and DISPROVEN this session**: prior note guessed "a driver
      re-run with an updated `--end`/`--cutoff` covering 2026 would close [the XG 250-gap] in minutes" — **tested
      live**: re-ran `understat_bulk_backfill.py --start 2014 --end 2026 --cutoff 2026-07-06` (PID 3289798,
      `/tmp/understat_backfill_tail2.log`), completed clean (`RESUME: 1/2202 dates pending` →
      `ALL DATES CAPTURED (0     attempted_failed)`), **re-verified via `/tmp/verify_understat_gate.py`: ZERO CHANGE** —
      XG `expected_unattempted` still exactly 250, XG_SHOTS still exactly 5,843, identical date ranges. Root cause is
      NOT a season-range gap: `enumerate_dates()` only ever contains dates understat's own `getLeagueData` marks
      `isResult=true`; the 250/5,843 `expected_unattempted` dates are **not in that fixture set at all** (confirmed:
      latest XG/XG_SHOTS captured date for every big-5 league is 2026-05-16→05-24, i.e. genuine end-of-2025-season — the
      2026-05-05→07-08 XG dates are past-season/close-season with no real fixtures). Also confirmed via direct manifest
      read (`/tmp/check_eu_reason.py`): **all 250 + 5,843 rows carry a BLANK `error_reason`** (not a documented
      `EXPECTED_NO_FIXTURE`-style reason) and were `attempted_at` 2026-06-19→2026-07-08 — i.e. written by the DAILY
      forward-poll enum, not the backfill driver (driver's own `pending_dates()` correctly treats `expected_unattempted`
      as still-pending and would reprocess it — but only for dates already in its own fixture-derived `all_dates` set,
      which these aren't). XG_SHOTS year/month distribution (`/tmp/check_fixture_calendar.py`): spread across ALL years
      2018-2026 and all months (skewed toward Jun/Jul off-season, but present in every month) — consistent with the
      sibling plan's earlier note that most of these are legitimate per-league non-matchday dates (this league didn't
      play that day; a different big-5 league did) rather than a global capture failure. **Unresolved question requiring
      an operator/architecture call, not a re-run**: are blank-`error_reason` `expected_unattempted` rows for genuine
      non-matchdays a PASSING terminal state (i.e. is the plan's own "`pending_fetch == 0`" gate wording being loosely
      applied to a state that's actually fine), or is this the SAME blank-reason daily-forward-poll bug class already
      fixed for weather/SFI in item #7's 2026-07-08 typing pass (`type_weather_eu_no_provider_coverage_2026_06_27.py` /
      SFI sibling) — i.e. does understat need its own analogous typed-reason pass instead of a bare backfill re-run?
      Filed as a todo in `plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md` (understat
      blank-reason EU rows, same root-cause family as weather/SFI, 250 XG + 5,843 XG_SHOTS rows, big-5 only).
      **Un-block**: resolve that todo (either a documented-reason typing pass if these are legitimate non-matchdays, or
      a targeted force-refetch of the specific dates if some are real gaps) — sibling plan's task -004/-005 remain the
      gate-flip vehicle once this item's own residual is closed.
- [ ] [DATA] P0. **footystats history → zero-missing** 2019→present (`MATCHES` + `PREDICTIONS` + `ODDS`). NOTE: ODDS
      removal reversed 2026-06-27 (#6 REVERSED, operator decision) — footystats ODDS are pre-match snapshot reference
      data that stays in IS; see sports_p0 task 003. **Gate**: `(footystats, PREDICTIONS)` + `(footystats, MATCHES)` +
      `(footystats, ODDS)` `pending_fetch == 0` within window; 0 blank-reason; ODDS parquets present in GCS.
      **BLOCKED-PREREQUISITES (2026-07-08, slot-7)**: VM `fs-backfill-20260706-161335` TERMINATED cleanly (`exit_code=0`
      confirmed via GCS run.log, completed 2026-07-07 23:46 UTC, processed through end-cutoff 2026-07-05). **Ran a
      typing pass** (`type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py --apply`,
      instruments-service@4368f38, dynamic "≥1 captured row = covered" logic) to clear 432 genuinely non-covered-league
      rows (119, AUSTRALIA_CUP, COPA_LIBERTADORES, etc.) — down from the stale-looking 44,454/5,782 pre-typing snapshot.
      **Gate still FAILS on real gaps** (re-verified 2026-07-08 20:10 UTC, shard-merged read): MATCHES
      `pending_fetch=5,641` — 96% concentrated in 4 REGULAR leagues (CHILE_PRIMERA=1,459, K_LEAGUE_1=1,451,
      LIGA_MX=1,291, ARGENTINA_PRIMERA=1,228), i.e. near-total-history gaps for leagues nominally "covered" (≥1 captured
      row exists) — looks like a footystats MATCHES fetch bug specific to these 4 leagues, not a config/typing issue.
      PREDICTIONS `pending_fetch=44,163` — 93% concentrated in continental/cup competitions (UECL=2,303, UEL=2,302,
      UCL=2,297, SWISS_CUP=2,279, COPA_ARGENTINA=2,277, CHILE_PRIMERA_B=2,277, LIGA_EXPANSION_MX=2,275,
      JLEAGUE_CUP=2,069, TURKIYE_KUPASI=2,063, TACA_DE_PORTUGAL=2,061, +37 more), each missing ~75-85% of its full
      2019-2026 date range — the pattern (near-uniform per-league residual spanning the FULL history, not a recent tail)
      looks like a fixture-calendar-awareness gap: cup competitions don't play every day, and the PREDICTIONS
      orchestrator likely never resolves a no-fixture-that-day cup date to `empty_confirmed(EXPECTED_NO_FIXTURE)`,
      leaving the enum's blanket eu placeholder untouched forever (same shape as the understat over-broad-404 fix, but
      unaddressed for footystats). ODDS `pending_fetch=1,264` (not yet root-caused this session). **This is a CODE gap,
      not closeable by re-running the same backfill VM or a typing script** — recommend filing a dedicated follow-up
      plan/issue for footystats MATCHES (4-league fetch bug) + PREDICTIONS (fixture-calendar honest-absence) before the
      next VM launch, else a re-run will reproduce the same residual. **FILED 2026-07-08 (slot-14)**:
      `plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md` — 4 actionable todos (MATCHES fix,
      PREDICTIONS fixture-calendar fix, ODDS root-cause, re-verify-and-flip) so a future data_engineering dispatch can
      execute without re-diagnosing.
- [x] [DATA] P0. **odds-api history → zero-missing** 2020-06→present (bookmaker-league subset; uncovered leagues typed).
      **Gate**: `(odds_api, trades)` `pending_fetch == 0` for covered leagues within window; uncovered leagues typed. ✅
      — `mtds-backfill-odds-1` VM completed 2026-06-28T03:41 UTC (rc=0, 317/317 chunks, 2020-06-06→2026-06-27, 7-day
      chunks, MANIFEST_PER_VM_SHARDS=true). Gate verified 2026-06-29: source=odds_api manifest rows: captured=223701,
      empty_confirmed=22(SOURCE_RETURNED_ZERO), expected_unattempted=0, attempted_failed=0, pending_fetch=0. Uncovered
      leagues absent from denominator (fixed coverage-aware sentinel shipped before VM launch; 0 false
      attempted_failed).
- [ ] [VERIFY] P1. **Full-history reference cleanliness.** **Gate**: full-history audit → 0 pending-fetch + 0
      blank-reason + 0 un-evidenced failed for all 6 sources within their coverage windows. **BLOCKED-PREREQUISITES
      (2026-07-08, slot-7)**: items #4 (understat) + #5 (footystats) both still unflipped — re-verified LIVE 2026-07-08
      20:10 UTC via `read_availability_index` (shard-merged, single-walk-safe, no whole-corpus GCS list). **Fixed a real
      correctness bug found while re-verifying**: `type_weather_eu_no_provider_coverage_2026_06_27.py` and
      `type_sfi_eu_no_provider_coverage_2026_06_27.py` had NO league-coverage check in their masks — they blanket-typed
      every blank-reason EU row as `EXPECTED_NO_PROVIDER_COVERAGE` regardless of whether the league was actually
      covered. Safe on the 2026-06-27 one-time run (every matching row happened to be non-covered), but a recurring
      daily forward-poll enum keeps writing NEW blank-reason EU rows for covered leagues too (264 rows each for
      weather/SFI, dates 2026-06-30→2026-07-08) — re-running the scripts unchanged would have silently mistyped a real
      pending-fetch as permanent no-coverage. Fixed both masks to exclude currently-covered leagues
      (instruments-service, this commit) before re-running. Also ran the existing (already-correct, dynamic-coverage)
      `type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py --apply` (432 genuinely non-covered rows
      typed). **Net effect**: weather/SFI eu dropped 3,601→264 each; footystats MATCHES eu dropped 5,782→5,641,
      PREDICTIONS 44,454→44,163 (the non-covered-league noise is gone; what's left is a REAL gap, not a typing backlog).
      Transfermarkt needed NO typing — 0 non-covered rows against the authoritative 55-league covered set (its full
      1,364 pending_fetch is a real gap, dates 2025-12-10→2026-07-08, needs a new backfill VM covering that window — the
      last TM VM only ran through 2026-06-29). **Current per-source state (all FAIL)**: open_meteo pending_fetch=264,
      SFI pending_fetch=264 (both recent-date covered-league — plausibly daily-pipeline lag, not backfill scope, but
      unverified this session), transfermarkt pending_fetch=1,364 (real gap, needs VM), understat XG pending_fetch=250 /
      XG_SHOTS pending_fetch=5,843 (see item #4 note), footystats MATCHES pending_fetch=5,641 / PREDICTIONS
      pending_fetch=44,163 / ODDS pending_fetch=1,264 (see item #5 note — these are CODE gaps, not VM-rerun-closeable).
      odds_api PASS (unchanged). **Un-block sequence unchanged in shape**: item #4 and #5 must both reach
      pending_fetch=0 before this item can flip; given items #4/#5 residuals are now diagnosed as requiring either a
      targeted re-fetch (TM, understat XG-tail) or an orchestrator code fix (footystats MATCHES 4-league bug, footystats
      PREDICTIONS cup fixture-calendar gap), this is NOT a quick re-dispatch — recommend the operator review whether
      footystats MATCHES/PREDICTIONS deserves its own follow-up plan before further VM spend. **UPDATE 2026-07-08 20:58
      UTC (slot-5)**: re-verified live via `read_availability_index` (single-walk-safe) — state byte-for-byte unchanged
      from slot-7's 20:10 UTC snapshot (confirmed no VM had launched in the interim: 0
      `tm-backfill-*`/`us-backfill-*`/`fs-backfill-*` instances RUNNING). Drilled into the TM 1,364-row residual by
      `league_id` (not the always-blank `league` column): confirmed genuine, 47 TM-covered leagues × 34 sparse dates
      (2025-12-10, then clusters 2026-05-01→05-04, 05-27→06-24, 07-07→07-08), `written_at` in small daily-forward-poll
      batches (993 on 06-19, 184 on 06-23, ~46-47/day since) — a real per-league fetch gap inside dates the prior TM VM
      (`tm-backfill-20260629-060317`, range 2021-01-01→2026-06-29) nominally covered but didn't fully close, NOT a
      typing-fixable artifact. **Action taken**: launched `tm-backfill-20260708-205809` SPOT e2-standard-8
      asia-northeast1-c, range 2025-12-10→2026-07-08 (tarball verified fresh: default `instruments-service-code.tar.gz`
      built from @19693ca, only 2 non-sports commits behind current HEAD @42eeefb). GCS log:
      `gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260708-205809/run.log`. Singleton lock
      confirmed clear before launch. Understat XG-tail (250 rows, 2026-05-05→2026-07-08) and XG_SHOTS/footystats
      residuals left untouched — XG_SHOTS is explicitly gated on sibling plan
      `understat_local_backfill_completion_2026_07_06.md` tasks -002/-004 (do not duplicate that diagnosis from this
      plan), and footystats MATCHES/PREDICTIONS need an orchestrator code fix per slot-7's diagnosis, outside a VERIFY
      task's scope pending operator review. **Gate still NOT MET** — no checkbox flip. **Post-VM step** (next slot to
      pick this up): wait for `tm-backfill-20260708-205809` TERMINATED + consolidator merge (≤1 min), re-query
      `(transfermarkt, PLAYER_VALUES) pending_fetch`; if 0 (or only the window-closed baseline), TM is fully resolved
      and the remaining blockers are understat XG_SHOTS + footystats MATCHES/PREDICTIONS only.

**Full-execution criterion**:

- ✅ Every non-AF reference source + odds-api reads zero-expected-missing across its coverage window, manifest-verified.
  - **What ran**: per-source year-chunked backfill VMs (launchers above) on the instruments + market-data sports
    buckets.
  - **Verification**: per-source full-history query output pasted into the Progress Log.

## Success criteria

- All 6 sources zero-missing within their coverage windows for the 94 universe; per-source subsets typed (never
  false-missing/failed).
- Concurrent per-source runs; OOM fix confirmed live; no new whole-corpus walk.

## Dependencies

- **Upstream (prereq)**: P1e; `sports_reference_backfill_oom_2026_06_22` (OOM fix shipped).
- **Feeds**: P2c (features history). Runs concurrently with P2a.

## Progress Log

### 2026-07-08 21:3x UTC — slot-3: item #4 root cause found + fix shipped + closer running

**Task**: `sports_p2_history_reference_and_odds_2015_to_present-016` (item #4), resumed from slot-2's 20:55 UTC
diagnosis (which filed the follow-up todo in
`plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md`).

**Root cause identified** (reading `scripts/enumerate_expected_universe.py::_enumerate_v2_sports`, line ~2007): the v2
sports enumerator is LEAGUE-GRAIN, not fixture-grain — for every alive `(league, data_type, date)` cell not already
present in the manifest it seeds a bare `expected_unattempted` row with `reason=""`, regardless of whether the league
actually played that day. This is exactly the same bug shape as the weather/SFI/footystats blank-reason residuals fixed
earlier today, just never enumerated for understat specifically (understat has its own per-league entity-coverage
filter, so the naive "type away as EXPECTED_NO_PROVIDER_COVERAGE" fix used for weather/SFI does NOT apply — a big-5
league IS covered, the gap is at the DATE level, not the league level). Confirmed live: 6,093 residual rows (XG=250,
XG_SHOTS=5,843) span exactly 1,169 unique dates, near-evenly across all 5 big-5 leagues (~1,218-1,219 each) — consistent
with a blanket per-date seed rather than a real per-league fixture gap.

**Why the existing backfill driver can't touch these**: `understat_bulk_backfill.py`'s own `enumerate_dates()` only
contains dates understat's `getLeagueData` marks `isResult=true` — a residual date that isn't a real fixture day for ANY
big-5 league literally never enters its date set, so re-running it (as slot-2 already tested) produces zero change,
confirming this needs a different tool, not a different `--end`/`--cutoff`.

**Fix shipped** (no operator call needed — this follows the exact WRITER-materializes-the-answer pattern already used
elsewhere, just needs the right date set): `instruments-service@c14ef7d`,
`scripts/backfill/understat_eu_residual_closer_2026_07_08.py`. Does NOT re-implement fixture-calendar logic — reads the
manifest for the LIVE blank-reason residual dates, then force-refetches exactly those dates via the SHIPPED per-date
capture path (`_fetch_understat_xg` / `_run_understat_shots_date`, `force=True`). That path already does the correct
thing per (date, league): real fixture found → captures real data; season-window guard / no fixture →
`record_expected_empty`/`record_empty(reason=...)` which stamps `capture_status=empty_confirmed` with a typed reason —
converting every blank-reason `expected_unattempted` row into a correctly-typed terminal state either way, closing the
"0 over-broad-404 failures" / `pending_fetch == 0` gate honestly (no re-derivation risk, no new silent placeholders).

**Running now** (local process, PID 3704218, `/tmp/understat_eu_residual_closer.log` on the planning VM slot-3 worktree
— matches the sibling bulk-backfill driver's precedent of running LOCAL rather than a VM, since understat is a
single-origin scraper with no bulk endpoint and one IP is the rate ceiling regardless of VM count). Self-healing retry
loop built in (mirrors `understat_bulk_backfill.py`). Early observation: pure off-season dates (e.g. 2019-07-xx) resolve
via the season-window guard without even hitting the network (cheap); in-season no-match dates correctly resolve via
`record_empty` after a real per-league fixture check.

**Gate still NOT MET — no checkbox flip yet.** Next step (this session or next slot, whichever finishes first): once the
closer logs `=== UNDERSTAT EU RESIDUAL CLOSER COMPLETE ===`, re-verify via a live manifest read
(`data_type in (XG, XG_SHOTS)`, `league_id` in big-5, `capture_status=expected_unattempted`, blank `error_reason`) — if
0, flip this item's checkbox with the before/after counts as evidence.

### 2026-07-08 21:0x UTC — slot-14: item #7 re-dispatch — TM VM healthy (too early to close), footystats issue doc filed

**Task**: `sports_p2_history_reference_and_odds_2015_to_present-015` (item #7 P1 verify flip), re-dispatched moments
after slot-5's 20:58 UTC TM VM launch.

**VM check**: `tm-backfill-20260708-205809` confirmed RUNNING via
`/home/ubuntu/google-cloud-sdk/bin/gcloud compute instances list` (non-snap gcloud; snap gcloud still broken on this
host). `run.log` tail shows healthy heartbeats + successful club fetches as of 21:03 UTC (VM started 21:00 UTC — ~3 min
in, far too early to expect the 2025-12-10 → 2026-07-08 range to finish; not stalled, no action needed). Did not
block-wait on it (async-wait discipline — polling a freshly-launched multi-hour VM is not productive use of this
dispatch).

**Gate cannot flip regardless of the TM outcome** — items #4 (understat) and #5 (footystats) are both still `- [ ]` with
real residuals requiring code work, not a VM re-run. Item #5's own diagnosis (slot-7, 2026-07-08 20:10 UTC) recommended
filing a dedicated follow-up issue before further footystats VM spend; checked and none existed. **Filed**
`plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md` with 4 actionable todos (MATCHES 4-league
fetch-bug root-cause, PREDICTIONS cup fixture-calendar fix, ODDS root-cause, re-verify-and-flip) so a future
data_engineering dispatch with full session budget can execute the fix instead of re-diagnosing from the same snapshot a
4th time.

**Gate still NOT MET — no checkbox flip.** Next slot: check `tm-backfill-20260708-205809` for TERMINATED + consolidator
merge (won't be soon — launched 21:00 UTC, 7-month range); if resolved, TM closes and only understat XG_SHOTS + the
newly-filed footystats issue doc's 4 todos remain before item #5 (and then #7) can flip.

### 2026-07-08 20:58 UTC — slot-5: item #7 re-dispatch — TM gap confirmed real, backfill VM launched

**Task**: `sports_p2_history_reference_and_odds_2015_to_present-015` (item #7 P1 verify flip), re-dispatched moments
after slot-7's exhaustive 20:12 UTC re-verify.

**Freshness check first** (avoided duplicating slot-7's work): re-ran `read_availability_index` — all 6 sources'
`pending_fetch` counts matched slot-7's snapshot exactly (TM=1,364, understat XG=250, XG_SHOTS=5,843, footystats
MATCHES=5,641, PREDICTIONS=44,163, ODDS=1,264); confirmed 0 `tm-backfill-*`/`us-backfill-*`/`fs-backfill-*` VMs RUNNING
via `gcloud compute instances list` (non-snap gcloud at `/home/ubuntu/google-cloud-sdk/bin` — the snap gcloud on this
host is broken, `snap-confine` permission error, matching the earlier 2026-06-29 note).

**New diagnosis on the TM residual**: drilled into the 1,364 TM eu rows by the correct `league_id` column (the `league`
column in this manifest schema is always blank — a red herring on first pass). Confirmed 47 distinct TM-covered
`league_id`s across 34 sparse dates (2025-12-10 standalone, then clusters 2026-05-01→05-04, 05-27→06-24, 07-07→07-08) —
a genuine per-league fetch gap inside the range the prior TM VM (`tm-backfill-20260629-060317`, 2021-01-01→2026-06-29)
nominally covered but didn't fully close, not a typing-fixable artifact. This confirms slot-7's "real gap, needs new
backfill VM" call.

**Action**: verified the default code tarball (`instruments-service-code.tar.gz`, built from @19693ca) is fresh — only 2
non-sports commits behind current HEAD (@42eeefb: a docs commit + an unrelated DeFi dedupe fix) — so it already carries
slot-7's enumerate-race fix (@1835e11) and today's typing-mask fixes. Launched `tm-backfill-20260708-205809` SPOT
e2-standard-8 asia-northeast1-c, range 2025-12-10→2026-07-08. GCS log:
`gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260708-205809/run.log`.

**Left untouched** (outside this task's scope / already assigned elsewhere): understat XG_SHOTS (gated on sibling plan
`understat_local_backfill_completion_2026_07_06.md` tasks -002/-004 — did not duplicate that diagnosis) and footystats
MATCHES/PREDICTIONS (need an orchestrator code fix per slot-7's diagnosis; recommend operator review before further VM
spend, as slot-7 already flagged).

**Gate still NOT MET — no checkbox flip.** Full detail appended to item #7's bullet above. Next slot: after
`tm-backfill-20260708-205809` TERMINATED + consolidator merge, re-verify TM `pending_fetch`; if resolved, only understat
XG_SHOTS + footystats MATCHES/PREDICTIONS remain (both need code work, not a quick re-dispatch).

### 2026-07-08 20:12 UTC — slot-7: item #7 re-verify + typing-bug fix + true-residual characterization

**Task**: `sports_p2_history_reference_and_odds_2015_to_present-015` (item #7 P1 verify flip).

**Live re-verify** (via `read_availability_index`, shard-merged, single-walk-safe — NOT a whole-corpus GCS list) across
all 6 sources confirmed the gate is still FAIL, but found the prior "0 pending-fetch blocked only on VM completion"
framing was stale: the footystats VM (`fs-backfill-20260706-161335`) and the understat driver (sibling plan task -001)
had BOTH already completed, yet the gate still failed — because a large fraction of the reported `pending_fetch` was
actually non-covered-league typing noise, not a real gap. Ran the existing typing pipeline to separate the two:

**Bug found + fixed before running**: `type_weather_eu_no_provider_coverage_2026_06_27.py` and
`type_sfi_eu_no_provider_coverage_2026_06_27.py` had NO league-coverage check in their mask — they blanket-typed every
blank-`error_reason` EU row for their source as `EXPECTED_NO_PROVIDER_COVERAGE`, regardless of whether the league is
actually covered. This was safe on the original 2026-06-27 one-time run (every matching row happened to be non-covered),
but a **daily forward-poll enum keeps writing fresh blank-reason EU rows every ~24h for ALL 6 sources** (confirmed via
`written_at`: batches on 2026-06-30, 07-01…07-08) — some of those NEW rows are for genuinely-covered leagues (264 each
for weather/SFI, dates 2026-06-30→2026-07-08). Re-running the scripts unchanged would have silently mistyped real
pending-fetch as permanent no-coverage — a silent-placeholder violation. Fixed both masks to exclude currently-covered
leagues (`get_expected_leagues_for_source`) before applying.

**Typing pass applied** (instruments-service, this session):

| Script                                                                  | Rows typed  | Safety                                      |
| ----------------------------------------------------------------------- | ----------- | ------------------------------------------- |
| `type_weather_eu_no_provider_coverage_2026_06_27.py` (fixed)            | 3,337       | now excludes covered leagues                |
| `type_sfi_eu_no_provider_coverage_2026_06_27.py` (fixed)                | 3,337       | now excludes covered leagues                |
| `type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py` | 432         | already dynamic-covered (≥1 captured row)   |
| `type_footystats_odds_non_covered_leagues_2026_06_29.py`                | 0           | already clean                               |
| `type_tm_non_provider_coverage_2026_06_27.py`                           | 0 (not run) | checked: 0 non-covered rows exist currently |

**Post-typing true state (2026-07-08 20:10 UTC, all still FAIL):**

| source               | data_type             | captured | empty   | eu     | af  | pending_fetch | note                                                                                                                                                                                                        |
| -------------------- | --------------------- | -------- | ------- | ------ | --- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| open_meteo           | WEATHER               | 12,037   | 245,808 | 264    | 51  | 264           | recent dates 06-30→07-08, covered leagues — maybe daily lag                                                                                                                                                 |
| soccer_football_info | SFI_PROGRESSIVE_STATS | 19,743   | 207,504 | 264    | 10  | 264           | same pattern as weather                                                                                                                                                                                     |
| transfermarkt        | PLAYER_VALUES         | 45,911   | 213,907 | 1,364  | 0   | 1,364         | real gap, 2025-12-10→2026-07-08, needs new backfill VM                                                                                                                                                      |
| understat            | XG                    | 6,673    | 11,283  | 250    | 0   | 250           | 2026-05-05→2026-07-08 — driver's `--end 2025` didn't cover 2026                                                                                                                                             |
| understat            | XG_SHOTS              | 6,671    | 3,927   | 5,843  | 0   | 5,843         | ~1,168/league spread 2018-2026 — genuine gap, driver did NOT close despite "ALL DATES CAPTURED"                                                                                                             |
| footystats           | MATCHES               | 23,328   | 206,629 | 5,641  | 21  | 5,641         | 96% in CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA — near-total gap, looks like a per-league fetch bug                                                                                               |
| footystats           | PREDICTIONS           | 23,890   | 195,775 | 44,163 | 0   | 44,163        | 93% in cup/continental competitions — near-uniform ~75-85% gap per league, looks like missing fixture-calendar honest-absence (same shape as the understat over-broad-404 fix, never applied to footystats) |
| footystats           | ODDS                  | 27,392   | 79,350  | 1,264  | 20  | 1,264         | not root-caused this session                                                                                                                                                                                |
| odds_api             | trades                | 223,701  | 14      | 0      | 0   | 0             | PASS                                                                                                                                                                                                        |

**Assessment**: the remaining residuals across TM/understat-XG_SHOTS/footystats-MATCHES/footystats-PREDICTIONS are NOT
closeable by re-running the same VM or a typing script — they need either a targeted backfill for a specific date window
(TM, understat XG-tail) or an orchestrator code fix (footystats MATCHES 4-league bug, footystats PREDICTIONS
fixture-calendar gap). Filed the full breakdown in
`plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md` (already-open P0 issue covering the "eu
regression" theme — added an update rather than a new doc since this is the same root class, now confirmed
recurring/daily rather than one-time). **No checkbox flipped** (items #4, #5, #7 all remain gate-not-met, correctly).
Code shipped: instruments-service (2 script fixes). Recommend operator review: footystats MATCHES + PREDICTIONS likely
deserve a dedicated follow-up plan before the next VM launch, else a re-run reproduces the same residual.

### transfermarkt PLAYER_VALUES coverage state (2026-06-27 23:45 UTC, slot-5 monitoring)

IS manifest (`instruments-store-sports-prd-central-element-323112`):

**Raw counts (gap range 2026-02-20→2026-06-26):**

| capture_status       | count (raw) | notes                                                  |
| -------------------- | ----------- | ------------------------------------------------------ |
| captured             | 427         | VM-written (TM-covered leagues on open-window dates)   |
| empty_confirmed      | 199,889     | includes 8,744 typed by typing script (non-TM leagues) |
| expected_unattempted | 6,845       | TM-covered leagues (55) × remaining VM dates only      |

**After dedup (last-write-wins by written_at):** pending_fetch = 4,087 (all 55 TM-covered leagues, 0 non-TM)

**Gate status**: IN PROGRESS — VM at 2026-04-01, ~87 dates remaining. Non-TM leagues resolved ✅.

**Key discoveries (2026-06-27 23:30 UTC):**

- Manifest denominator = 126 leagues/day (not 55): cup competitions, lower divisions also in denominator
- VM (orchestrator) covers exactly 55 leagues via
  `get_expected_leagues_for_source("transfermarkt", classifications=["Prediction", "Features"])` +
  `get_prediction_leagues()`
- 71 non-TM leagues (cups, lower divisions) → typed as EXPECTED_NO_PROVIDER_COVERAGE via
  `type_tm_non_provider_coverage_2026_06_27.py` (instruments-service@fbb032d), applied 23:41 UTC
- Typing script result: 8,744 rows typed; consolidator merged at ~23:44 UTC
- Canonical index after dedup: EU down to 4,087 (all TM-covered leagues, 0 non-TM)

**VM `tm-backfill-20260627-222604`** RUNNING: processing at 2026-04-01 as of 23:42 UTC (41/127 days = 32%). API-call
dates (transfer windows open): ~2-3 min/day. ETA VM completion: ~03:00–04:00 UTC 2026-06-28. After VM TERMINATED: wait
for consolidator (≤1 min), re-download index, verify pending_fetch==0, flip checkbox.

**Completed 2019→2026-02-19** (pre-existing, not touched by this VM):

- captured: 39,584 | empty_confirmed: 264,736 | expected_unattempted: 0

### footystats coverage state (2026-06-27 ~22:00 UTC)

IS manifest (`instruments-store-sports-prd-central-element-323112`):

| data_type   | captured | attempted_failed | expected_unattempted | empty_confirmed | coverage |
| ----------- | -------- | ---------------- | -------------------- | --------------- | -------- |
| MATCHES     | 26,266   | 1,460            | 161,335              | 148,392         | 13.9%    |
| PREDICTIONS | 27,875   | 560              | 161,571              | 117,805         | 14.7%    |
| ODDS        | 29,129   | 1,119            | 11,486               | 74,432          | 69.8%    |

**ODDS rows intact** (29K captured; code restored at instruments-service@3d4f1a1 + @edebc6b).

**VM sequence needed** (singleton lock: only one `fs-backfill-*` at a time):

1. Current: `fs-backfill-20260627-200928` RUNNING — 2026-02-20..2026-06-27 MATCHES+PREDICTIONS (ETA ~01:40 UTC
   2026-06-28)
2. After #1 completes → ODDS VM: `bash launch-footystats-backfill-vm.sh --entity ODDS 2019-01-01 2026-06-27 --force`
3. After #2 completes → MATCHES+PREDICTIONS history: `bash launch-footystats-backfill-vm.sh 2019-01-01 2026-02-19`
   (Multiple runs may be needed due to VM runtime limits; chunk by year if needed)

### understat XG + XG_SHOTS coverage state (2026-06-27 23:55 UTC, slot-9 monitoring)

IS manifest (`instruments-store-sports-prd-central-element-323112`), full history:

**XG — native leagues (EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1):**

| capture_status       | count   | notes                                                       |
| -------------------- | ------- | ----------------------------------------------------------- |
| captured             | 3,429   | across 5 native leagues, full history                       |
| empty_confirmed      | 222,346 | off-season / no-fixture dates                               |
| expected_unattempted | 265     | 53/league, dates 2026-05-05→2026-06-26 (VM not yet reached) |
| attempted_failed     | 0       | 0 HTTP_NOT_FOUND for native leagues ✅                      |

**XG_SHOTS — native leagues:**

| capture_status       | count   | notes                                                                             |
| -------------------- | ------- | --------------------------------------------------------------------------------- |
| captured             | 0       | VM not yet written XG_SHOTS for native leagues (shard in progress)                |
| empty_confirmed      | 202,875 | matches with 0 shots or off-season                                                |
| expected_unattempted | 635     | 127/league, dates 2026-02-20→2026-06-26                                           |
| attempted_failed     | 397     | 79–80/league, HTTP_NOT_FOUND, dates 2017-04-01→2026-03-02 (over-broad-404 legacy) |

**Non-native leagues (87,630 rows):** ALL `empty_confirmed` with `error_reason=EXPECTED_NO_PROVIDER_COVERAGE` ✅ Already
typed.

**Blank-league XG phantom rows (296 rows):** `attempted_failed`, `reason=phantom_captured_no_parquet_at_canonical_path`,
dates 2019-01-09→2026-04-16. NOT gate-blocking for item #4 (blank league_id ≠ native leagues); needs extended run of
`reclassify_xg_blank_league_phantoms.py` for P1 verification (item #6).

**Skip efficiency:** XG: 4,211/4,561 dates skip-eligible (92.3%). XG_SHOTS: only 342/4,561 (7.5%) — bottleneck.

**Gate status: IN PROGRESS** — VM `us-backfill-20260627-210801` RUNNING (SPOT, asia-northeast1-c). At 2014-03-08 as of
23:51 UTC 2026-06-27 (~2.7h elapsed). Full range 2014-01-01→2026-06-27 = 4,561 dates. XG_SHOTS skip rate (7.5%) = ~4,219
API-call dates × ~1.5-2.5 min = **~4-5 days ETA** for full completion.

**Over-broad-404 resolution**: The 397 `XG_SHOTS` `HTTP_NOT_FOUND` rows will self-resolve when VM reaches those dates.
Per-match 404 from `get_match_shots()` is now treated as honest absence (→ `empty_confirmed`) and per-league error
scoping is fixed. Consolidator last-write-wins merges the correct rows over the stale failed ones.

**After VM TERMINATED**: wait for consolidator (≤1 min), re-query: XG `expected_unattempted==0` for 5 native leagues,
XG_SHOTS `attempted_failed==0` (HTTP_NOT_FOUND), then flip checkbox.

**Singleton lock**: no concurrent `us-backfill-*` VMs (AJAX per-IP rate limit).

**Status update (2026-06-28 17:32 UTC, slot-9):** VM `us-backfill-20260628-070120` RUNNING. Progress: 689/4,561 dates
(15.1%), at 2015-11-20. Rate ~79s/date. ETA: ~2026-07-02 06:30 UTC (~3.6 days). uv cross-filesystem symlink mitigation
reverted (dir removed; future uv syncs will recreate on root disk as regular dir enabling hardlinks). Host disk: 898MB
free, draining ~2 MB/min from fleet orch-agent-main conversation logs (largest: 253MB, 104MB, 96MB). VM execution
unaffected (runs on GCE). Risk: local gcloud monitoring may fail if disk hits 0 before VM completes — operator disk
expansion or log rotation needed.

**Status update (2026-06-28 20:20 UTC, slot-9):** VM `us-backfill-20260628-070120` RUNNING. Progress: ~820/4,561 dates
(18%), at 2016-04-01 as of 19:58 UTC. Rate ~56.8s/date effective. ETA revised: **~2026-07-01 07:00 UTC** (~59h
remaining). Host disk hit 100% — slot-9 cleaned 611MB of confirmed-inactive orch-agent-main conversation logs; 3.1GB now
free.

Consolidated manifest (`availability_index.parquet`, 2026-06-28T20:03:40Z):

| data_type | capture_status       | count  | notes                                                                                             |
| --------- | -------------------- | ------ | ------------------------------------------------------------------------------------------------- |
| XG        | captured             | 3,429  | all leagues combined                                                                              |
| XG        | empty_confirmed      | 33,666 | all leagues                                                                                       |
| XG        | expected_unattempted | 265    | 53/native × 5 leagues — gate not met ❌                                                           |
| XG        | attempted_failed     | 296    | blank-league phantoms (non-gate-blocking for item #4)                                             |
| XG_SHOTS  | empty_confirmed      | 16,162 | all leagues                                                                                       |
| XG_SHOTS  | expected_unattempted | 635    | 127/native × 5 leagues (2026-02-20→2026-06-26) — gate not met ❌                                  |
| XG_SHOTS  | attempted_failed     | 405    | all native (↑8 from 397; over-broad-404 legacy; self-resolve when VM re-visits) — gate not met ❌ |

**Gate not met — blocked on VM completion**: All three gate conditions (XG eu=265, XG_SHOTS eu=635, XG_SHOTS failed=405)
resolve when VM finishes. No code changes needed; VM running correctly. After VM TERMINATED + consolidator (≤1 min):
re-query → flip checkbox ✅.

**Status update (2026-06-29 01:45 UTC, slot-9):** VM `us-backfill-20260628-070120` RUNNING. Progress: 1,271/4,561 dates
(27.9%), at 2017-06-17. Rate ~53s/date effective (67.9 dates/h). ETA revised: **~2026-07-01 02:17 UTC** (~48.5h
remaining).

Consolidated manifest (`_index/availability_index.parquet`, 2026-06-29T01:33:30Z):

| data_type | capture_status       | count   | notes                                                               |
| --------- | -------------------- | ------- | ------------------------------------------------------------------- |
| XG        | captured             | 3,429   | all leagues combined                                                |
| XG        | empty_confirmed      | 298,441 | all leagues (↑ VM writing off-season empties)                       |
| XG        | expected_unattempted | 280     | 56/native × 5 leagues — gate not met ❌                             |
| XG        | attempted_failed     | 296     | blank-league phantoms (non-gate-blocking)                           |
| XG_SHOTS  | empty_confirmed      | 282,691 | all leagues                                                         |
| XG_SHOTS  | expected_unattempted | 13,776  | 2,755/native × 5 leagues — gate not met ❌                          |
| XG_SHOTS  | attempted_failed     | 421     | all native (↑16; over-broad-404; self-resolve when VM re-visits) ❌ |

Native-league gate: XG pending_fetch=280, XG_SHOTS pending_fetch=14,197 — not met. VM still processing; no code changes
needed.

**Status update (2026-06-29 04:30 UTC, slot-9):** VM `us-backfill-20260628-070120` RUNNING. Progress: ~1,461/4,561 dates
(~32%), at 2018-01-01. Rate ~60-70 dates/h. ETA revised: **~2026-07-01 02:00 UTC** (~45h remaining).

**BUG FOUND + FIXED: `_classify_error` URL substring collision (instruments-service@7bb8c26)**

ROOT CAUSE: `_classify_error` matched `"401" in msg`, `"429" in msg`, `"403" in msg` against the full exception message
including the URL. Understat match IDs like `/getMatch/5401` → `"401" in msg` → INVALID_API_KEY (not HTTP_NOT_FOUND).
Since `get_match_shots()` only returns `[]` without incrementing `_fetch_error_count` for `HTTP_NOT_FOUND`, this
misclassification caused `_fetch_error_count` to increment → league added to `_shots_failed_canonical` →
`record_failed(HTTP_NOT_FOUND)` instead of `record_empty(EXPECTED_NO_FIXTURE)`.

EVIDENCE from VM log:

- `ADAPTER_FETCH_FAILED venue=understat error_code=RATE_LIMIT_EXCEEDED: 404, message='Not Found', url='.../getMatch/5429'`
  (match 5429 → "429" in msg)
- `ADAPTER_FETCH_FAILED venue=understat error_code=INVALID_API_KEY: 404, message='Not Found', url='.../getMatch/5401'`
  (match 5401 → "401" in msg)
- `ADAPTER_FETCH_FAILED venue=understat error_code=FORBIDDEN: 404, message='Not Found', url='.../getMatch/5403'` (match
  5403 → "403" in msg)

FIX: `_classify_error` now prioritises the HTTP status param over substring matching — if `status` is not None, return
the classification directly. String matching only applies for statusless network errors.

IMPACT:

- 27 new false-failed rows in 2014-2017 (written by current VM with buggy code). These will NOT self-resolve when VM
  re-visits (already processed).
- 396 legacy failed rows (2019-2026, from pre-fix VMs) — WILL self-resolve when the (fixed) code processes those dates.
  But current VM has old code baked in → those dates may accumulate additional false-failed rows.
- Typing script `reclassify_xg_shots_false_failed_2026_06_29.py` shipped at instruments-service@15dc9b5. Run AFTER VM
  terminates to reclassify ALL `XG_SHOTS attempted_failed(HTTP_NOT_FOUND)` native-league rows to
  `empty_confirmed(EXPECTED_NO_FIXTURE)`.

Consolidated manifest (`_index/availability_index.parquet`, 2026-06-29T04:29:41Z):

| data_type | capture_status       | count   | notes                                                                               |
| --------- | -------------------- | ------- | ----------------------------------------------------------------------------------- |
| XG        | captured             | 3,429   | all leagues combined                                                                |
| XG        | empty_confirmed      | 298,441 | all leagues                                                                         |
| XG        | expected_unattempted | 280     | 56/native × 5 leagues — gate not met ❌                                             |
| XG        | attempted_failed     | 296     | blank-league phantoms (non-gate-blocking)                                           |
| XG_SHOTS  | empty_confirmed      | 283,449 | all leagues                                                                         |
| XG_SHOTS  | expected_unattempted | 13,776  | 2,755/native × 5 leagues — gate not met ❌                                          |
| XG_SHOTS  | attempted_failed     | 423     | 27 new false-failed (VM bug) + 396 legacy; need typing script after VM completes ❌ |

**Gate not met — blocked on VM completion**: VM ETA ~2026-07-01 02:00 UTC. After VM TERMINATED:

1. Wait ≤1 min for consolidator merge
2. Run `reclassify_xg_shots_false_failed_2026_06_29.py --apply` (per-VM shard; consolidator applies last-write-wins)
3. Wait ≤1 min for consolidator to merge typing shard
4. Re-query: XG `expected_unattempted==0`, XG_SHOTS `expected_unattempted==0`, XG_SHOTS `attempted_failed==0` for native
   leagues
5. If all zero: flip checkbox ✅

### 2026-06-29 05:15 UTC — slot 2: understat VM progress check

**VM `us-backfill-20260628-070120`** RUNNING. At 2018-02-08 as of 05:10 UTC. Progress: ~1,500/4,561 dates (~33%). Rate
~68 dates/h. ETA unchanged: **~2026-07-01 02:00 UTC** (~44h remaining). GCS log tail confirms clean execution — XG
short-circuiting (all 5 native leagues captured), XG_SHOTS fetching match shots, per-VM shard updated every 5 entries.
No errors.

**All code ready**. Reclassify script at `instruments-service@15dc9b5`. No code action needed until VM TERMINATED.

**Post-VM verification steps (unchanged from 04:30 entry)**:

1. Wait ≤1 min for consolidator merge after VM TERMINATED
2. `GCP_PROJECT_ID=central-element-323112 PROJECT_ID=central-element-323112 DEPLOYMENT_ENV_SHORT=prd CLOUD_PROVIDER=gcp MANIFEST_PER_VM_SHARDS=true VM_NAME=reclassify-xg-shots-$(date +%s) .venv/bin/python scripts/reclassify_xg_shots_false_failed_2026_06_29.py --apply`
3. Wait ≤1 min for consolidator to merge typing shard
4. Re-query: XG `expected_unattempted==0`, XG_SHOTS `expected_unattempted==0`, XG_SHOTS `attempted_failed==0` for native
   leagues
5. If all zero: flip checkbox ✅

**Task parked** — re-dispatch this task after VM TERMINATED (~2026-07-01 02:00 UTC).

### 2026-06-29 06:34 UTC — slot 4: understat VM status check

**VM `us-backfill-20260628-070120`** RUNNING (GCE: STATUS=RUNNING). At 2018-04-14 as of 06:32 UTC. Progress:
~1,565/4,561 dates (~34%). Rate ~60-68 dates/h. ETA: **~2026-07-01 02:00 UTC** (~43h remaining). GCS log clean — XG
short-circuiting (all 5 native leagues captured), XG_SHOTS fetching match shots.

**Manifest state (downloaded 06:34 UTC, availability_index.parquet):**

| data_type | capture_status       | count   | notes                                                                                     |
| --------- | -------------------- | ------- | ----------------------------------------------------------------------------------------- |
| XG        | captured             | 4,444   | all leagues                                                                               |
| XG        | empty_confirmed      | 298,441 | all leagues                                                                               |
| XG        | expected_unattempted | 280     | 56 dates × 5 native leagues — gate not met ❌                                             |
| XG        | attempted_failed     | 296     | blank-league phantoms (non-gate-blocking)                                                 |
| XG_SHOTS  | empty_confirmed      | 283,658 | all leagues                                                                               |
| XG_SHOTS  | expected_unattempted | 13,776  | 2,755 dates × 5 native leagues (enum regression rows, VM self-corrects) — gate not met ❌ |
| XG_SHOTS  | attempted_failed     | 424     | false-failed, need reclassify script after VM — gate not met ❌                           |

**No code action needed** — VM running correctly, all code ready (reclassify script at instruments-service@15dc9b5).
Task blocked on VM completion. /blocked filed.

### 2026-06-29 06:35 UTC — slot 7: understat VM status + enum-run XG_SHOTS eu finding

**VM `us-backfill-20260628-070120`** RUNNING. At 2018-04-07 as of 06:23 UTC. Progress: ~1,558/4,561 dates (~34%). Rate
~68 dates/h. ETA: **~2026-07-01 02:00 UTC** (~43h remaining). GCS log tail clean.

**Manifest state (downloaded 06:25 UTC, availability_index.parquet):**

| data_type | capture_status       | count   | notes                                                                          |
| --------- | -------------------- | ------- | ------------------------------------------------------------------------------ |
| XG        | captured             | 4,444   | all leagues (↑ from 3,429 — VM writing)                                        |
| XG        | empty_confirmed      | 298,441 | all leagues                                                                    |
| XG        | expected_unattempted | 280     | 56/native × 5 leagues, dates 2026-05-05→2026-06-29 — gate not met ❌           |
| XG        | attempted_failed     | 296     | blank-league phantoms (non-gate-blocking)                                      |
| XG_SHOTS  | empty_confirmed      | 283,658 | all leagues                                                                    |
| XG_SHOTS  | expected_unattempted | 13,776  | 2,756 unique dates × 5 native leagues, 2018-01-01→2026-06-29 — gate not met ❌ |
| XG_SHOTS  | attempted_failed     | 424     | all native, false-failed (need typing script) ❌                               |

**NEW FINDING — enum run at 21:31 UTC 2026-06-28 wrote 13,776 XG_SHOTS eu rows:** All 13,776 XG_SHOTS eu rows have
`written_at = 2026-06-28T21:31:49.534565+00:00` — same as the TM regression enum run
(`enum-universe-sports-20260628-213115`). The enum wrote XG_SHOTS eu for 2018-01-01→present, overwriting rows the VM had
written for dates it processed BEFORE the enum ran (~2016-02-22 territory).

**Self-resolution**: As the VM processes each date from 2018-01-01 onwards (VM is currently at 2018-04-07 — already past
2018-01-01), it writes empty_confirmed rows with NEWER timestamps than the enum's eu rows. These win in last-write-wins
consolidation. For 2018-01-01 to 2018-04-06: VM has already processed these dates after the enum ran (VM processed them
at ~04:30 UTC today, newer than 21:31 UTC yesterday), so those rows are being merged by the consolidator. The eu count
will drop continuously as the VM progresses.

**No code action needed** — VM self-corrects all eu rows. Gate still blocked on VM completion (~2026-07-01 02:00 UTC).
Post-VM steps unchanged (same as 05:15 UTC entry above). Task parked; slot-7 blocked (/blocked BLK-d37c0d60).

### 2026-06-29 06:20 UTC — slot 9: footystats ODDS gate analysis + second VM + typing

**ODDS VM 1 completed** (`fs-backfill-20260629-043218`, exit_code=0, 06:04 UTC). Gate NOT met:

- 6,294 eu rows: 4,976 non-covered-league artifacts (58 leagues, never had captured ODDS) + 1,318 covered-league eu from
  race condition
- 286 af rows: 285 phantom_captured_no_parquet (SUPER_LIG=183, SWISS_SUPER_LEAGUE=92, CHILE_PRIMERA=4, LIGUE_1=1) + 6
  blank-league

**Root cause of 285 phantom af rows persisting**: ODDS VM 1 launched at 04:32 UTC, 7 min after phantom-audit shard
(04:25 UTC). Consolidator hadn't merged phantom-audit shard yet → VM's `_should_skip_date_for_per_league` read old
consolidated index, saw captured for those dates → skipped → phantom-audit af wins after consolidation.

**Actions taken (2026-06-29 06:00-06:22 UTC)**:

1. Typed 4,976 non-covered eu rows: `type_footystats_odds_non_covered_leagues_2026_06_29.py --apply` at
   instruments-service@810ac26. Shard: `_index/per_vm/type-fs-odds-1782713875.parquet`.
2. Launched `fs-backfill-20260629-062206` SPOT ODDS VM for 2020-09-01..2026-06-15 to re-process 285 af dates. This time
   consolidated index shows af (not captured) → skip-check returns False → processes those dates.

**Post-VM 2 verification steps**:

1. Wait ≤1 min for consolidator after VM TERMINATED
2. Re-query `(footystats, ODDS)` — expect captured=30K+, empty_confirmed=70K+, eu≈0, af≈0 (or only blank-league af if
   not resolvable)
3. If 6 blank-league af rows persist: investigate + type away separately
4. After ODDS gate met → launch M+P VM: `bash launch-footystats-backfill-vm.sh 2019-01-01 2026-02-19`
5. After M+P VM completes: verify `(footystats, MATCHES)` + `(footystats, PREDICTIONS)` pending_fetch==0 → reflip
   footystats checkbox ✅

### 2026-06-29 06:03 UTC — slot 9: TM regression eu investigation + re-backfill VM launch

**Context**: IS manifest eu regression at 2026-06-28T21:31 (enum run `enum-universe-sports-20260628-213115`) wrote
34,686 eu rows for TM-covered leagues, overwriting previously-valid captured/empty_confirmed rows in the consolidated
index. Root cause: enumerate read only consolidated index (race condition, fixed at instruments-service@1835e11).

**TM eu analysis** (manifest downloaded 2026-06-29T05:55 UTC):

| capture_status       | count                  |
| -------------------- | ---------------------- |
| captured             | 39,807                 |
| empty_confirmed      | 212,907                |
| expected_unattempted | 36,050 → pending_fetch |

Regression eu (34,686 from `enum-universe-sports-20260628-213115`): 47 leagues × 738 specific dates (2021-03-16 to
2026-06-28), by year: 2021=8,037 / 2022=9,400 / 2023=1,316 / 2024=9,259 / 2025=6,110 / 2026=564.

Non-regression eu (1,364 rows from 2026-06-19/23/26/29 enum runs): recent forward-poll dates, will be covered by the new
backfill VM.

**Action**: Launched `tm-backfill-20260629-060317` SPOT e2-standard-8 at 06:03 UTC, range 2021-01-01→2026-06-29.
Tarball: instruments-service@051e5a8 (includes enumerate fix @1835e11). GCS log:
`gs://deployment-scripts-central-element-323112/vm-logs/tm-backfill-20260629-060317/run.log`. Singleton lock active.

**Expected result**: VM writes captured/empty_confirmed for all 738 eu dates × 47 leagues → consolidator merges → TM
pending_fetch returns to ≤6,845 (only window-closed dates that TM skips remain eu). Estimate: ~15-20h (at 2-3 min/date
for transfer-window-open dates, window-closed dates fast).

**Post-VM steps**: Wait ≤1 min for consolidator, re-query, verify
`(transfermarkt, PLAYER_VALUES) pending_fetch ≤ 6,845`. If confirmed: TM gate re-met. Then task 007 gate depends only on
Understat + Footystats VMs completing.

### 2026-06-29 — slot 8: footystats ODDS phantom flip + ODDS VM launch

**Finding**: The footystats todo `[x]` was flipped prematurely (slot 5, 2026-06-27). The "ODDS 29K captured intact"
claim was incorrect — phantom audit (slot-8, 22:01 UTC 2026-06-27) confirmed ALL 29,129 `captured` ODDS rows had 0 GCS
parquets. Data was wiped by `wipe_footystats_odds_2026_06_25.py` on 2026-06-25 05:16 UTC (before the reversal).

**Actions taken**:

1. **Phantom flip `--apply` ran at 04:25 UTC 2026-06-29**:
   `reconcile_phantom_manifest_rows_all.py --asset-group sports --data-types ODDS --apply --workers 4`. Result: 26,220
   rows → `attempted_failed`, 2,909 pre-launch excluded. Post-flip dry-run confirms: 0 phantom rows remain.

2. **ODDS backfill VM launched at 04:32 UTC 2026-06-29**: `fs-backfill-20260629-043218` SPOT e2-standard-8
   asia-northeast1-c, range 2019-01-01..2026-06-29, entity=ODDS only. Code at IS@97ccf8d (includes ODDS restore at
   @3d4f1a1+@edebc6b). GCS log:
   `gs://deployment-scripts-central-element-323112/vm-logs/fs-backfill-20260629-043218/run.log`. VM launched via Python
   compute API (gcloud snap-confine broken on planning VM).

3. **Footystats checkbox UNFLIPPED** — gate requires `(footystats, ODDS) pending_fetch == 0` which will only be met
   after the ODDS VM completes. M+P 2019-01-01..2026-02-19 also still needed (singleton lock: after ODDS VM).

**Next steps**: Monitor `fs-backfill-20260629-043218` (check GCS log for progress). After ODDS VM TERMINATED: wait for
consolidator, verify `(footystats, ODDS) pending_fetch == 0`, then launch M+P 2019-01-01..2026-02-19 VM. After both
complete + gate met → reflip footystats checkbox. Issue doc
`issues/sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md` updated.

### 2026-06-29 06:49 UTC — slot 4: P1 verify gate status check

**All 3 in-progress VMs confirmed RUNNING at 06:49 UTC** (gate NOT met):

| VM                            | Status  | Current date | Rate                             | ETA                                  |
| ----------------------------- | ------- | ------------ | -------------------------------- | ------------------------------------ |
| `tm-backfill-20260629-060317` | RUNNING | 2021-05-25   | ~55 entries/date, ~45s/date      | ~16:30 UTC today                     |
| `fs-backfill-20260629-062206` | RUNNING | 2021-01-29   | ~5.6 dates/min (mostly skipping) | ~12:00 UTC today                     |
| `us-backfill-20260628-070120` | RUNNING | 2018-04-25   | ~68 dates/h                      | **~2026-07-01 02:00 UTC (blocking)** |

**FINDING — FS ODDS VM 2 validation error**: date=2021-01-24 produced
`[MEDIUM] validation error: "Expected bytes, got a 'Timestamp' object", 'Conversion failed for column kickoff_utc with type object'`.
Capture still succeeded (74 rows, manifest updated). This may indicate kickoff_utc column type mismatch in parquets
written by this VM. Non-gate-blocking but worth noting for downstream parquet consumers.

**Gate status**: NOT MET. Understat VM ETA ~40h is the blocking constraint (XG `expected_unattempted=280`, XG_SHOTS
`expected_unattempted=13,776`, XG_SHOTS `attempted_failed=424`). TM and FS may complete today but understat will not.

**Task parked** — re-dispatch after Understat VM TERMINATED (~2026-07-01 02:00 UTC). No code action needed; all code
ready. /blocked filed (slot 4).

### 2026-07-06 16:13 UTC — slot-11: footystats M+P+ODDS full-history VM launched

**Root cause (identified 2026-07-06):** The M+P VM for 2019-01-01..2026-02-19 was sequenced after ODDS VM 2
(`fs-backfill-20260629-062206`) but never launched once ODDS VM 2 completed on 2026-06-29. This left the entire 7-year
history uncaptured for 49 PREDICTIONS leagues and several MATCHES leagues.

**Manifest state at VM launch (2026-07-06 16:13 UTC):**

| data_type   | capture_status       | count (footystats-sourced)                                               |
| ----------- | -------------------- | ------------------------------------------------------------------------ |
| PREDICTIONS | expected_unattempted | 44,298 (49 leagues, all years 2019-2026)                                 |
| MATCHES     | expected_unattempted | 5,630 (CHILE_PRIMERA/K_LEAGUE_1/LIGA_MX/ARGENTINA_PRIMERA + others)      |
| MATCHES     | attempted_failed     | 939 (SEGUNDA_DIVISION — investigate post-VM)                             |
| ODDS        | expected_unattempted | 1,318 (race-condition eu from ODDS VM 1; may resolve)                    |
| ODDS        | attempted_failed     | 277 (phantom/ArrowType/PipelineModeSourceMismatch — investigate post-VM) |

**Action:** Launched `fs-backfill-20260706-161335` SPOT e2-standard-8 asia-northeast1-c, range 2019-01-01..2026-07-05
all entities (M+P+ODDS), via Python compute API (gcloud snap-confine broken). Tarball:
`instruments-service-code@2fa38777a79b8bd95dc8c2c6acc44e13779fd41a.tar.gz` (updated 2026-07-06 16:00 UTC — fresh).

**Post-VM steps:**

1. Wait ≤1 min for consolidator merge after VM TERMINATED
2. Re-query: MATCHES + PREDICTIONS + ODDS pending_fetch == 0 for footystats source
3. If SEGUNDA_DIVISION af=939 persists: investigate — type as EXPECTED_NO_PROVIDER_COVERAGE if not covered
4. If ODDS af=277 (phantom/ArrowType) persists: investigate each error_reason; phantom → phantom-audit; ArrowType →
   investigate schema
5. If ODDS eu=1,318 persists: check if these are non-covered leagues → type as EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE
6. Once all pending_fetch == 0 → flip checkbox ✅

### 2026-07-06 16:45 UTC — slot-10: VM baseline + parked pending completion

**VM `fs-backfill-20260706-161335`** RUNNING. At date=2019-01-18 as of 16:38 UTC (~25 min elapsed since 16:13 UTC
launch; ~1% of 2743-date range). Rate ~1.4 dates/min effective (mix of API-call dates and skip dates). **ETA: 24-40
hours from launch** = ~2026-07-07 16:00 UTC to 2026-07-08 08:00 UTC. GCS log clean; FOOTYSTATS DONE lines confirm
M+P+ODDS being fetched per date; per-VM shard updated every ~5-8 entries.

**Manifest state (consolidated index `_index/availability_index.parquet`, updated 2026-07-06T16:40:50Z):**

| data_type   | captured | empty_confirmed | expected_unattempted | attempted_failed | pending_fetch | coverage |
| ----------- | -------- | --------------- | -------------------- | ---------------- | ------------- | -------- |
| MATCHES     | 26,366   | 256,528         | 5,630                | 939              | 6,569         | 97.7%    |
| PREDICTIONS | 28,599   | 195,099         | 44,298               | 0                | 44,298        | 83.5%    |
| ODDS        | 30,702   | 79,358          | 1,318                | 277              | 1,595         | 98.6%    |

**Pre-analysis of residual af rows (all `phantom_captured_no_parquet_at_canonical_path`):**

- MATCHES af=939: 100% SEGUNDA_DIVISION. Confirmed IS a footystats-covered Prediction+Features league (UAC
  `get_expected_leagues_for_source("footystats", classifications=["Prediction","Features"])` → 46 leagues incl.
  SEGUNDA_DIVISION).
- ODDS af=277: SUPER_LIG=183, SWISS_SUPER_LEAGUE=92, LIGUE_1=1, blank=1; +1 RuntimeError. SUPER_LIG / SWISS_SUPER_LEAGUE
  / LIGUE_1 are also all footystats-covered.
- All 1,216 phantom af rows have `written_at` in 2026-05-01..2026-05-07 — 2 months old, present in the current
  consolidated index BEFORE VM launched. VM's `_should_skip_date_for_per_league` reads the up-to-date index → sees `af`
  (not `captured`) → will NOT skip → will re-process these dates and replace phantom af with fresh capture attempts. No
  pre-VM typing scripts needed; auto-heal expected.

**Task parked** — re-dispatch condition: VM TERMINATED AND
`(footystats, MATCHES)+(footystats, PREDICTIONS)+(footystats, ODDS) pending_fetch == 0`. Post-VM steps unchanged from
16:13 UTC entry above (verify pending_fetch, run typing only if af/eu residues persist beyond phantoms, then flip item
#5 checkbox).

### 2026-07-06 ~21:00 UTC — slot-7: understat item #4 re-evaluation after local backfill terminated

**Task**: `sports_p2_history_reference_and_odds_2015_to_present-016` (item #4 checkbox flip).

**Live state check**:

- SPOT VM `us-backfill-20260628-070120` — `gcloud describe` returns "not found" (deleted). run.log
  (`gs://deployment-scripts-central-element-323112/vm-logs/us-backfill-20260628-070120/run.log`, mtime 2026-06-29
  14:49:36 UTC, 1.62 MiB) last entry is `PIPELINE_HEARTBEAT ... ts=2026-06-29T14:49:22Z` while still processing
  `date=2019-08-09`. No `PROGRAM_END`, no `exit`, no `preempt`/`shutdown` markers → SPOT preemption mid-run, ~15% into
  the 4,561-date range. Never relaunched as a VM.
- LOCAL backfill process (PID 1782092, orphaned PPID=1) — `ps -p 1782092` empty; `/tmp/understat_backfill.log` mtime
  2026-07-06 20:46:53 UTC. Log ends with `[VERIFY 6] attempted_failed dates remaining: 108` →
  `WARNING === MAX ROUNDS reached; still 108 attempted_failed ===` → `INFO === UNDERSTAT BULK BACKFILL COMPLETE ===` →
  `ManifestWriter: per-VM shard updated (1040 total entries, 15 new, process_final=True)`. 2,767 `rows written for date`
  log lines total. Process terminated cleanly at max-rounds cutoff.

**Manifest verification (via `/tmp/verify_understat_gate.py`, reads single `_index/availability_index.parquet` — NO
whole-corpus walk, respects single-walk discipline)**:

Big-5 native leagues (EPL/LA_LIGA/BUNDESLIGA/SERIE_A/LIGUE_1):

| data_type | captured | empty_confirmed | attempted_failed | expected_unattempted | pending_fetch |
| --------- | -------- | --------------- | ---------------- | -------------------- | ------------- |
| XG        | 9,132    | 19,764          | 0                | 315 (63/league × 5)  | 315           |
| XG_SHOTS  | 6,675    | 7,580           | 384              | 13,811               | 14,195        |

XG_SHOTS `attempted_failed=384` all `error_reason='HTTP_NOT_FOUND'`, `attempted_at 2026-06-23 → 2026-06-29` — these are
the pre-`_classify_error`-fix (instruments-service@7bb8c26) legacy false-failed rows that the reclassify script
`reclassify_xg_shots_false_failed_2026_06_29.py` (instruments-service@15dc9b5) was written to fix. Neither script ran
against this residue yet.

Hollow-shots check (unique (date, league) captured atoms — did the shots endpoint return real data or hollow via the
`/getMatch` dead endpoint?):

| league     | XG captured atoms | XG_SHOTS captured atoms | common | shots-coverage |
| ---------- | ----------------- | ----------------------- | ------ | -------------- |
| EPL        | 1,318             | 1,318                   | 1,318  | 100.0%         |
| LA_LIGA    | 1,576             | 1,576                   | 1,576  | 100.0%         |
| BUNDESLIGA | 1,165             | 1,162                   | 1,162  | 99.7%          |
| SERIE_A    | 1,342             | 1,342                   | 1,342  | 100.0%         |
| LIGUE_1    | 1,275             | 1,268                   | 1,268  | 99.5%          |

Post-fix `/getMatchData` endpoint (instruments-service@527b9d9) produced REAL shots data — the hollow-shots concern that
motivated the parking is now proven resolved on the captured rows. Latest captured date per big-5 league: 2026-05-16
(BUNDESLIGA/LIGUE_1) → 2026-05-24 (EPL/LA_LIGA/SERIE_A) — recent enough that XG `expected_unattempted=63/league` is
plausibly ~9 weeks of post-latest window that the backfill's `--cutoff 2026-07-06` covered but understat didn't actually
have data for (needs confirmation via a re-fetch pass, not gate-flippable as-is).

**Gate NOT met** — item #4 (this checkbox) requires `XG+XG_SHOTS pending_fetch == 0` for native leagues + 0
over-broad-404. Both conditions fail with the residues above. **Un-block sequence** encoded on the item #4 checkbox
BLOCKED-PREREQUISITES marker; the immediate next-step owned by task -002 of
`understat_local_backfill_completion_2026_07_06.md` (run the reclassify script) will collapse the 384 af to zero; the
13,811 XG_SHOTS eu and 315 XG eu need a separate diagnosis pass (are they dates outside understat's real fixture
calendar? if so, type as `EXPECTED_NO_FIXTURE`; if not, drive a re-run over just those dates).

**Task -016 output**: no flip, no code, no VM launch. Deliverable = this Progress Log entry + the top-of-plan banner
update from `🟢 UNDERSTAT BACKFILL RUNNING` → `🟡 UNDERSTAT SPOT VM PREEMPTED + LOCAL BACKFILL TERMINATED` + the item #4
BLOCKED-PREREQUISITES marker so the dispatcher filters this task from priority-only regen until (a) task -002 of the
sibling plan runs the reclassify script and (b) the XG_SHOTS eu is diagnosed + resolved. Slot-7 releases via /done on
this update.

### 2026-07-06 ~22:00 UTC — slot-5: item #7 (P1 VERIFY gate) re-evaluation after auto-dispatch

**Task**: `sports_p2_history_reference_and_odds_2015_to_present-015` (item #7 P1 verify flip).

**Auto-dispatch context**: task -015 dispatched to slot-5 at Tier 1 Priority 999
(`dispatch_reason: "highest-rank queued task with prereqs met and no collision"`) despite the plan's serial ordering
(items #1-#6 → item #7) not being machine-encoded as `depends_on`. Items #4 (understat) + #5 (footystats) still
unflipped, so the P1 gate's precondition ("0 pending-fetch + 0 blank-reason + 0 un-evidenced failed for all 6 sources")
cannot be met.

**Live state check**:

- **Understat process (item #4 prereq)**: PID 1782092 (orphaned local driver from slot-7 session) **NOT running** —
  `ps -p 1782092` empty. `/tmp/understat_backfill.log` mtime 2026-07-06 20:46:53 UTC, last 3 lines
  `MAX ROUNDS reached; still 108 attempted_failed` → `UNDERSTAT BULK BACKFILL COMPLETE` → per-VM shard
  `understat-bulk-backfill.parquet` finalized (`process_final=True`, 1040 total entries, 15 new). Row-write count:
  2,767. The local backfill terminated cleanly at the MAX_ROUNDS cutoff; 108 dates remain stubbornly `attempted_failed`.
- **Footystats VM (item #5 prereq)**: `fs-backfill-20260706-161335` **RUNNING** — confirmed `status=RUNNING` via
  `compute_v1.InstancesClient()` at 22:00 UTC. GCS log
  (`gs://deployment-scripts-central-element-323112/vm-logs/fs-backfill-20260706-161335/run.log`, size 391,737 bytes,
  mtime 21:59:12Z) tail shows processing date=2020-03-15 as of 21:59 UTC (all-canonical-leagues-captured short-circuit →
  skip, PIPELINE_HEARTBEAT every ~60s). At ~440/2743 dates (~16%) after 5.75h elapsed → ~76.5 dates/h → **ETA
  ~2026-07-08 04:00-08:00 UTC** to reach 2026-07-05 end-cutoff. VM behaving normally; the M+P VM sequencing gap
  identified in the 16:13 UTC launch entry is being filled correctly.

**Manifest verification (single-walk, reads `_index/availability_index.parquet` via `/tmp/verify_understat_gate.py` —
respects single-walk discipline)**:

Big-5 native leagues understat gate:

| data_type | captured | empty_confirmed | attempted_failed | expected_unattempted | pending_fetch |
| --------- | -------- | --------------- | ---------------- | -------------------- | ------------- |
| XG        | 9,132    | 19,764          | 0                | 315 (63/league × 5)  | 0             |
| XG_SHOTS  | 6,675    | 7,580           | 384              | 13,811               | 0             |

XG_SHOTS `attempted_failed=384` all `reason=HTTP_NOT_FOUND`, `attempted_at 2026-06-23 → 2026-06-29` — the pre-fix
`_classify_error` (instruments-service@7bb8c26) legacy false-failed rows. The reclassify script
`reclassify_xg_shots_false_failed_2026_06_29.py` (instruments-service@15dc9b5) exists but has not been run against this
residue. XG_SHOTS `expected_unattempted=13,811` = 2,762 unique dates × 5 native leagues, all with
`written_at=2026-06-28T21:31:49Z` (from `enum-universe-sports-20260628-213115` regression enum) — these need diagnosis:
either dates outside understat's real fixture calendar (type as `EXPECTED_NO_FIXTURE`) or need targeted re-fetch.

Hollow-shots check (99.5–100% XG_SHOTS/XG captured atom parity per big-5 league) confirms the captured shots are REAL,
not hollow — the shots endpoint fix (`/getMatchData`, instruments-service@527b9d9) is producing real data on captured
rows.

**Gate assessment**: **NOT MET**. Item #4 residue (384 af + 315 XG eu + 13,811 XG_SHOTS eu on big-5 native leagues)
alone fails "0 un-evidenced failed" and "0 pending-fetch" for the understat source. Item #5 footystats VM still ~30h
from completion; pre-VM eu counts (PREDICTIONS=44,298, MATCHES pending=6,569, ODDS pending=1,595) will drop as VM
processes but are not yet at zero.

**Precedent applied without re-filing /blocked**: this is the exact pattern documented in the sibling plan
`understat_local_backfill_completion_2026_07_06.md` — tasks -004/-005/-006/-007 all auto-dispatched over unmet
plan-explicit prereqs (BLK-afcc5da6 → -001 OPTION A; BLK-18a3d596 → -004 OPTION A; -006/-007 applied without re-filing
per session precedent). Main-agent verdict on that pattern is PARK. Same shape here — item #7 requires items #4 + #5,
both unmet; the operationally correct action is to add a BLOCKED-PREREQUISITES marker inside the item #7 checkbox line
(matches how -005 / -006 / -007 are structured so the dispatcher filters this task from priority-only regen until an
operator clears it).

**Task -015 output**: no flip on item #7, no code ship, no VM launch. Deliverable = this Progress Log entry + the item
#7 BLOCKED-PREREQUISITES marker with the full un-block sequence. Slot-5 releases via /done on this update. Operator
flag: when both prereqs complete, item #7 re-dispatch should regen after items #4 and #5 checkboxes flip (no direct
`depends_on` encoding available on the item-level; the checkbox marker is the current gating mechanism).

## References

- `sports_reference_backfill_oom_2026_06_22.md` — OOM single-read fix (vm-sports)
