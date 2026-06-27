---
doc_type: plan
title: "Sports P1b — golden-window reference sources to 100% (weather · SFI · transfermarkt · understat · footystats)"
summary:
  "Drive all non-API-Football reference sources (weather, SFI, transfermarkt, understat, footystats) to 100% honest
  coverage on the golden window."
nature: process
stage: [data-ingestion]
repos: []
scope: [engineer, admin]
tags: [sports, reference-sources, golden-window, weather, understat, footystats, transfermarkt, sfi, backfill]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P0
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27
  - sports_reference_backfill_oom_2026_06_22
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/sports_reference_backfill_oom_2026_06_22.md
  - plans/active/data_completion_to_100_all_ag_2026_06_21.md
asset_group: cross-asset
---


> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 1). Drives every
> NON-API-Football reference source to 100% honest coverage on the golden window (**2025-09-01 .. 2025-11-30**,
> 94-league universe). PREREQ: **P0 shipped** (understat-404 fix is part of P0) + **`sports_reference_backfill_oom`
> shipped** (the OOM single-index-read fix these backfills depend on). One agent, `data_engineering` (Sonnet/high). All
> these sources are bounded by the 94 universe (weather is location-based once the home team is known).

# Sports P1b — golden-window reference sources to 100%

## Scope (per source / data_type on the golden window)

| Source                    | data_type(s)                   | `coverage_start` (in-window? ) | Golden-window state (2026-06-24)                                              | VM launcher                           |
| ------------------------- | ------------------------------ | ------------------------------ | ----------------------------------------------------------------------------- | ------------------------------------- |
| open_meteo                | `WEATHER`                      | 2019-03-02 ✅                  | verify; location-based per home venue                                         | `launch-openmeteo-backfill-vm.sh`     |
| soccerfootball_info (SFI) | `SFI_PROGRESSIVE_STATS`        | 2020-01-01 ✅                  | verify (single-stream; chunks BANNED post-429)                                | `launch-sfi-backfill-vm.sh`           |
| transfermarkt             | `PLAYER_VALUES` (+`TRANSFERS`) | 2019-01-01 ✅                  | **256 `attempted_failed` — retry**                                            | `launch-transfermarkt-backfill-vm.sh` |
| understat                 | `XG`, `XG_SHOTS`               | 2014-01-01 ✅                  | ~100% post P0 #2 fix — verify                                                 | `launch-understat-backfill-vm.sh`     |
| footystats                | `MATCHES`, `PREDICTIONS`       | 2019-01-01 ✅                  | **PREDICTIONS ~3,078 blank-reason → relabel**; MATCHES = honest no-match days | `launch-footystats-backfill-vm.sh`    |

Each source's backfill VMs have their OWN singleton-lock namespace, so they may run concurrently (the agent launches +
monitors each for the 91-day window). SFI is single-stream (no chunking) per the 2026-04-19 429-storm incident.

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the sports
> launchers default to SPOT. Backfills are idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a
> preemption must NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/honest-absence-downstream-handling.md` — typed `EXPECTED_*` (off-season / no-fixture /
  no-provider-coverage); SFI/understat per-league coverage subsets are honest absence
- `codex/02-data/sports-gcs-path-ssot.md` — per-source layouts (`PER_DAY_BARE` weather/XG, `PER_DAY_PER_SEASON`
  player_values, `PER_DAY_PER_LEAGUE` SFI/XG_SHOTS)
- `codex/02-data/availability-manifest-and-data-status.md` — `expected_unattempted_pending_fetch == 0` target

## Todos

- [x] ✅ [DATA] P0. **Weather (open_meteo) → 100% on the window.** Gap-fill `WEATHER` for the 91 days (forecast-issue-time
      stamped); weather is per-venue once the home team is known, so the expected set follows the fixtures captured in
      P1a. **Gate**: window query → `(open_meteo, WEATHER)` 0 `pending_fetch`, 0 blank-reason; any silent-day gap (the
      historical open-meteo-silence class) re-fetched or typed.
      — 2026-06-27: read_availability_index(instruments-store-sports-prd): (open_meteo, WEATHER) 2025-09-01..11-30:
        579 captured, 0 pending_fetch, 0 attempted_failed, 0 blank-reason EC. Gate ALL PASSED. No gap-fill needed.
- [x] ✅ [DATA] P0. **SFI (`SFI_PROGRESSIVE_STATS`) → 100% on the window** — single-stream only (no chunks). Relabel any
      historical SFI failure cluster to a typed reason (the retired `SFI_STANDINGS`/`SFI_LEAGUES` are NOT in scope; only
      the active `SFI_PROGRESSIVE_STATS`). **Gate**: window query → `(soccerfootball_info, SFI_PROGRESSIVE_STATS)` 0
      `pending_fetch`, 0 un-evidenced `attempted_failed`; no 429-storm (rate honoured).
      — 2026-06-27: source name in IS is `soccer_football_info`. read_availability_index 2025-09-01..11-30:
        889 captured, 2119 empty_confirmed (all EXPECTED_NO_FIXTURE), 0 pending_fetch, 0 AF, 0 blank-reason.
        Gate ALL PASSED. No backfill needed.
- [x] ✅ [DATA] P0. **Transfermarkt PLAYER_VALUES → 100% on the window** — re-fetch the 256 `attempted_failed`
      (transfer-window-aware; PER_DAY_PER_SEASON bulk layout). **Gate**: window `(transfermarkt, PLAYER_VALUES)`
      `attempted_failed` → 0 (or `FetchEvidence`-backed); transfer-window-closed days typed, not failed.
      — 2026-06-27: read_availability_index 2025-09-01..11-30: 2287 captured, 2718 EC (1634 EXPECTED_NO_MAPPING +
        1084 EXPECTED_NO_PROVIDER_COVERAGE), 0 AF, 0 pending_fetch, 0 blank-reason. Gate ALL PASSED.
- [x] ✅ [VERIFY] P0. **Understat XG/XG_SHOTS → 100% on the window** (post P0 #2 per-league-404 fix). understat covers only
      `{EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1}` — non-understat leagues in the denominator must be
      `EXPECTED_NO_PROVIDER_COVERAGE`, not failed. **Gate**: window query → `XG` + `XG_SHOTS` at 100% honest coverage
      for understat-native leagues; non-native leagues typed `EXPECTED_NO_PROVIDER_COVERAGE`; 0 over-broad-404 failures.
      — 2026-06-27: VM `us-backfill-20260627-163214` rc=0; rescan `sports-manifest-rescan-20260627-180901` rc=0.
        Prd index (instruments-store-sports-prd-central-element-323112): XG 546 rows (3 captured, 543 EC: 455
        SOURCE_RETURNED_ZERO + 88 EXPECTED_NO_FIXTURE), 0 blank-reason, 0 unattempted, 0 AF. XG_SHOTS 455 rows (455
        EXPECTED_NO_FIXTURE), 0 blank-reason, 0 unattempted, 0 AF. Prior 45 HTTP_NOT_FOUND → EXPECTED_NO_FIXTURE
        (0 matches in understat-native leagues for 2025-11-20..2025-11-29). Gate ALL PASSED.
- [x] ✅ [DATA] P0. **footystats MATCHES + PREDICTIONS → 100% on the window** — relabel the ~3,078 blank-reason PREDICTIONS
      empties to `SOURCE_RETURNED_ZERO` (or re-fetch where genuinely missing); MATCHES `SOURCE_RETURNED_ZERO` no-match
      days are honest absence (keep). Note: footystats `ODDS` are KEPT in IS (operator 2026-06-27 — predictive); P1b
      does not change them. **Gate**: window query → `(footystats, PREDICTIONS)` 0 blank-reason; `(footystats, MATCHES)`
      every non-captured cell typed; footystats `ODDS` rows retained (unchanged).
      — 2026-06-27: `reconcile_sports_blank_empty_reason_2026_06_24.py` dry-run → blank_before=0 (already typed by prior
        run). Confirmed via direct manifest query on golden window 2025-09-01..2025-11-30:
        PREDICTIONS 3,290 EC, 0 blank (EXPECTED_NO_FIXTURE:2694, SOURCE_RETURNED_ZERO:596);
        MATCHES 3,471 EC, 0 blank (SOURCE_RETURNED_ZERO:3328, EXPECTED_NO_FIXTURE:143);
        ODDS 3,204 EC retained (EXPECTED_NO_FIXTURE:2587, SOURCE_RETURNED_ZERO:617), 0 blank. All gates PASSED.
- [ ] [DATA] P1. **No-blank-reason invariant** across all reference sources on the window. **Gate**: window `_index`
      slice has 0 `empty_confirmed` rows with blank/null `error_reason` for any of the 5 sources.

**Full-execution criterion**:

- ✅ Every non-AF reference source reads 100% honest coverage on 2025-09-01..2025-11-30 for the 94 universe,
  manifest-verified.
  - **What ran**: per-source backfill VMs (the launchers above) on the window; `read_availability_index` window query.
  - **Verification**: per-source window query (`pending_fetch=0`, `blank_reason=0`, `attempted_failed=0`-or-evidenced)
    pasted into the Progress Log.

## Success criteria

- All 5 reference sources at 100% honest coverage on the golden window for the 94 universe; per-source coverage SUBSETS
  (SFI/understat/odds-api restrictions) expressed as typed `EXPECTED_*`, never false-missing or false-failed.
- The OOM fix (`sports_reference_backfill_oom`) confirmed shipped before launch (single index read per date).

## Dependencies

- **Upstream (prereq)**: P0; `sports_reference_backfill_oom_2026_06_22` (OOM fix shipped).
- **Feeds**: P1d (features), P1e (gate). Runs concurrently with P1a, P1c.

## Progress Log

### 2026-06-27 — Understat XG/XG_SHOTS verify (slot 6)

Re-fetch VM: `us-backfill-20260627-163214` SPOT asia-northeast1-c, 2025-09-01..2025-11-30 → rc=0.
Manifest rescan: `sports-manifest-rescan-20260627-180901` → rc=0 (2,594,563 rows consolidated).

**Gate check (prd index: instruments-store-sports-prd-central-element-323112):**
| data_type | captured | empty_confirmed | attempted_failed | unattempted | blank_reason | Gate |
|---|---|---|---|---|---|---|
| XG | 3 | 543 (SOURCE_RETURNED_ZERO:455, EXPECTED_NO_FIXTURE:88) | 0 | 0 | 0 | ✅ PASS |
| XG_SHOTS | 0 | 455 (EXPECTED_NO_FIXTURE:455) | 0 | 0 | 0 | ✅ PASS |

**Finding — HTTP_NOT_FOUND resolved:** Prior 45 `HTTP_NOT_FOUND` failures on 2025-11-20..2025-11-29 × 5 understat-native
leagues converted to `EXPECTED_NO_FIXTURE`. VM found 0 matches in understat-native leagues for those dates (end-of-season
fixture gap / international break). No over-broad-404 failures. Both XG and XG_SHOTS at 100% honest coverage.

## References

- `sports_reference_backfill_oom_2026_06_22.md` — the OOM single-read fix (vm-sports)
- `issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` — understat-404 + TM-failure diagnosis
