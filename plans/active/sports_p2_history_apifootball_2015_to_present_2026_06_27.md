---
title: "Sports P2a — API-Football history 2015→present to zero-missing (+ league-noise wipe + 2015-17 diagnosis)"
parent_epic: sports_master
priority: P1
status: active
assigned_vm: NA
assigned_vm: human-planning
assigned_role: data_engineering
drift_direction: advance-code
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p1_golden_window_e2e_gate_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/instruments_foundation_completeness_2026_06_24.md
  - plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 2). Generalizes the
> golden-window-proven recipe to ALL of api-football history, **2015→present**, 94-league universe — the R1 "every
> fixture since 2015, zero expected-missing". **PREREQ: P1e GREEN** (window proven). One agent, `data_engineering`
> (Sonnet/high). Smart-skip + season-aware (only not-honest-complete cells). Re-homes G1/G2 from
> `instruments_foundation_completeness` (which is on vm-cefi and won't reach sports).

# Sports P2a — API-Football history 2015→present

## Scope + coverage clips (the "zero expected-missing" definition)

- **FIXTURES**: `coverage_start = 2015-01-01` → backfill 2015→present, all 94 leagues, season-aware (off-season →
  `EXPECTED_PRE_SEASON`/`POST_SEASON`; no-match day → `EXPECTED_NO_FIXTURE`).
- **Enrichment** (`FIXTURE_EVENTS`/`LINEUPS`/`STATS`, `PLAYER_STATS`): `DATA_TYPE_COVERAGE_START = 2020-06-06` →
  pre-2020-06 cells are `EXPECTED_PRE_SOURCE_COVERAGE_START` (honest absence, NOT fetched, NOT missing); 2020-06→present
  backfilled.
- **Core** (`TEAMS`/`STANDINGS`/`INJURIES`): per their `coverage_start`.
- "Zero expected-missing" = `expected_unattempted_pending_fetch == 0` for every `(api_football, data_type)` for
  `date ≥ coverage_start`; everything else is a typed `EXPECTED_*`.

> **SPOT VMs (HARD)** — launch every VM in this plan as **spot/preemptible** (the cloud can reclaim + kill it at any
> moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); the sports
> launchers default to SPOT. Backfills are idempotent/skip-existing, so a reclaimed VM relaunches + resumes — and a
> preemption must NOT raise a false `DP_VM_GONE_NO_CAPTURE` (R5).

## Codex SSOTs

- `codex/02-data/honest-absence-downstream-handling.md` — coverage clips, season calendar, typed `EXPECTED_*`
- `codex/02-data/availability-manifest-and-data-status.md` — `expected_unattempted` writer-materialised; single-walk
  discipline
- `codex/02-data/sports-gcs-path-ssot.md` — `candidate_parquet_paths()` + layouts

## Todos

- [ ] [DATA] P0. **Wipe the non-canonical league NOISE (G1)** — 1,437 non-canonical leagues (~106k rows) vs the 94
      universe. Snapshot-first, consolidator-paused. (Re-homed from `instruments_foundation_completeness` G1.) **Gate**:
      post-wipe the sports `_index` carries ONLY the 94 canonical leagues (+ legit cups per `LEAGUE_REGISTRY`); snapshot
      object exists; the universe denominator is now exactly the canonical set.
- [ ] [DATA] P0. **Diagnose the 2015–2017 zero-captured (G2 — research).** 35,889 all-`empty_confirmed` cells across 76
      MVP leagues for 2015–2017. Probe api-football: is it a SUBSCRIPTION floor (→ adjust the real coverage floor in UAC
      `SOURCE_COVERAGE_START`/`DATA_TYPE_COVERAGE_START` so these become `EXPECTED_PRE_SOURCE_COVERAGE_START` honest
      absence) OR a backfill-bug (→ scoped `--force` re-run fills them)? (Re-homed from G2.) **Gate**: a documented
      verdict per league-year with a live `/status`-evidenced probe; UAC coverage constants reflect the TRUE
      subscription floor; no cell left blank/pending — each is either captured or typed `EXPECTED_*`.
- [ ] [DATA] P0. **Re-run the 40,041 FIXTURES `attempted_failed`** (2018/2021/2023 clusters) via
      `--recovery-fixture-ids` / entity-scoped re-run. (Re-homed from G2.) **Gate**: those clusters → captured or
      `FetchEvidence`-backed failed; 0 un-evidenced `attempted_failed`.
- [ ] [DATA] P0. **Backfill FIXTURES 2015→present** for the 94 leagues, season-aware smart-skip (gap-fill only).
      Fixtures are fast/cheap relative to enrichment (operator: "fixtures should be fairly quick"). Singleton-locked
      `af-backfill-*` VMs; chunk by year to stay resumable + within rate budget. **Gate**: full-history
      `read_availability_index` query → `(api_football, FIXTURES)` `pending_fetch == 0` for `date ≥ 2015-01-01`, 94
      leagues; every non-captured cell typed.
- [ ] [DATA] P0. **Backfill enrichment + core 2020-06→present** within coverage windows, season-aware smart-skip
      (depends on FIXTURES existing — enrichment is keyed by fixture_id). Pre-2020-06 enrichment stays
      `EXPECTED_PRE_SOURCE_COVERAGE_START`. **Gate**: full-history query → each enrichment/core data_type
      `pending_fetch == 0` within its coverage window; 0 blank-reason; VMs honoured the singleton lock + emitted
      STARTED/STOPPED.
- [ ] [VERIFY] P1. **Full-history AF cleanliness.** **Gate**: `run_fixture_completeness_audit_2026_06_25.py` over
      2015→present reports 0 pending-fetch + 0 blank-reason + 0 un-evidenced failed for every AF data_type.

**Full-execution criterion**:

- ✅ Every api-football data_type reads zero-expected-missing across 2015→present for the 94 universe,
  manifest-verified.
  - **What ran**: the G1 wipe, the G2 probe, the year-chunked `af-backfill-*` VMs (FIXTURES then enrichment) on
    `instruments-store-sports-prd-central-element-323112`.
  - **Verification**: the full-history audit output (per data_type pending=0/blank=0/failed=0-or-evidenced) + the G2
    verdict pasted into the Progress Log.

## Success criteria

- FIXTURES zero-missing 2015→present; enrichment/core zero-missing within coverage windows; pre-coverage cells typed.
- League-noise wiped → denominator = the 94 canonical universe; 2015-17 zero-captured resolved (honest-absence floor OR
  filled).
- Re-uses the P1e-proven recipe; no new whole-corpus GCS walk.

## Dependencies

- **Upstream (prereq)**: P1e (golden window GREEN).
- **Feeds**: P2c (features history). Runs concurrently with P2b.

## References

- `instruments_foundation_completeness_2026_06_24.md` — G0→G5 sports gates (vm-cefi; G1/G2 re-homed here)
- `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — the SEPARATE curated ~300-league
  reference expansion (out of scope; 94 only here)
