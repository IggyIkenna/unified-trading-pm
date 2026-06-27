---
doc_type: plan
title:
  "Sports P2b — reference + odds history to zero-missing (weather · SFI · transfermarkt · understat · footystats ·
  odds-api)"
summary:
  "Backfill all reference sources and MTDS odds across their full history coverage windows to zero-missing, generalising
  the golden-window recipe."
nature: process
stage: [data-ingestion]
repos: []
scope: [engineer, admin]
tags:
  [sports, reference-sources, odds, history-backfill, 2015-present, weather, understat, footystats, transfermarkt, sfi]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P1
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p1_golden_window_e2e_gate_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/sports_reference_backfill_oom_2026_06_22.md
asset_group: cross-asset
---

> **🟢 FOOTYSTATS BACKFILL RUNNING** — `fs-backfill-20260627-200928` SPOT e2-standard-8 asia-northeast1-c, launched
> 20:09 UTC 2026-06-27, range 2026-02-20..2026-06-27 (MATCHES+PREDICTIONS only — launched before ODDS code restore).
> ODDS code restored at instruments-service@3d4f1a1 (2026-06-27 21:10 UTC). After current VM completes (~01:40 UTC
> 2026-06-28), launch ODDS-only VM: `bash launch-footystats-backfill-vm.sh --entity ODDS --force 2019-01-01 2026-06-27`.
> Singleton lock prevents concurrent footystats VMs.

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 2). Generalizes the
> golden-window recipe to ALL non-AF reference sources + MTDS odds across their full coverage windows — the R1/R3 "all
> these sources backfilled to zero-missing". **PREREQ: P1e GREEN.** One agent, `data_engineering` (Sonnet/high).
> Season-aware smart-skip within each source's `coverage_start`.

# Sports P2b — reference + odds history to zero-missing

## Scope + per-source coverage windows (the clips that define "zero-missing")

| Source              | data_type(s)                   | `coverage_start` | History to backfill                          | Launcher                                 |
| ------------------- | ------------------------------ | ---------------- | -------------------------------------------- | ---------------------------------------- |
| open_meteo          | `WEATHER`                      | 2019-03-02       | 2019-03→present (per captured fixture venue) | `launch-openmeteo-backfill-vm.sh`        |
| soccerfootball_info | `SFI_PROGRESSIVE_STATS`        | 2020-01-01       | 2020→present (single-stream)                 | `launch-sfi-backfill-vm.sh`              |
| transfermarkt       | `PLAYER_VALUES`(+`TRANSFERS`)  | 2019-01-01       | 2019→present (transfer-window-aware)         | `launch-transfermarkt-backfill-vm.sh`    |
| understat           | `XG`, `XG_SHOTS`               | 2014-01-01       | 2014→present (5 native leagues only)         | `launch-understat-backfill-vm.sh`        |
| footystats          | `MATCHES`, `PREDICTIONS`       | 2019-01-01       | 2019→present                                 | `launch-footystats-backfill-vm.sh`       |
| odds_api (MTDS)     | `trades`/`odds_horizon_bucket` | 2020-06-06       | 2020-06→present (bookmaker-league subset)    | `launch-mtds-sports-odds-backfill-vm.sh` |

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
- [ ] [DATA] P0. **Transfermarkt history → zero-missing** 2019→present, transfer-window-aware (PER_DAY_PER_SEASON bulk;
      the OOM single-index-read fix from `sports_reference_backfill_oom` must be live). **Gate**:
      `(transfermarkt, PLAYER_VALUES)` `pending_fetch == 0` within window; window-closed days typed, not failed.
- [ ] [DATA] P0. **Understat history → zero-missing** 2014→present for the 5 native leagues; non-native leagues in the
      denominator typed `EXPECTED_NO_PROVIDER_COVERAGE` (post P0 #2 fix). **Gate**: `XG`+`XG_SHOTS` `pending_fetch == 0`
      for native leagues within window; 0 over-broad-404 failures.
- [ ] [DATA] P0. **footystats history → zero-missing** 2019→present (`MATCHES` + `PREDICTIONS` + `ODDS`). NOTE: ODDS
      removal reversed 2026-06-27 (#6 REVERSED, operator decision) — footystats ODDS are pre-match snapshot reference
      data that stays in IS; see sports_p0 task 003. **Gate**: `(footystats, PREDICTIONS)` + `(footystats, MATCHES)` +
      `(footystats, ODDS)` `pending_fetch == 0` within window; 0 blank-reason; footystats ODDS rows intact in IS (do NOT
      wipe them).
- [ ] [DATA] P0. **odds-api history → zero-missing** 2020-06→present (bookmaker-league subset; uncovered leagues typed).
      **Gate**: `(odds_api, trades)` `pending_fetch == 0` for covered leagues within window; uncovered leagues typed.
- [ ] [VERIFY] P1. **Full-history reference cleanliness.** **Gate**: full-history audit → 0 pending-fetch + 0
      blank-reason + 0 un-evidenced failed for all 6 sources within their coverage windows.

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

## References

- `sports_reference_backfill_oom_2026_06_22.md` — OOM single-read fix (vm-sports)
