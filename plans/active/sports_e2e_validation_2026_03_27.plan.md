---
title: "Sports E2E Validation + Feature Regeneration"
status: active
priority: P0
created: 2026-03-27
locked_by: live-defi-rollout
locked_since: 2026-03-27
---

# Sports E2E Validation + Feature Regeneration

## Context

Phase A (reference data backfill) and Phase D (odds migration) are complete. 288M odds rows + 143K fixtures + 1.87M
events in GCS. MTDS schema aligned to v3. Bookmakers= cost fix applied (30 credits/call vs 120). Need to validate the
full pipeline E2E, backfill the 80-day odds gap, and regenerate all features from historical data.

## Phase 1: MTDS E2E Validation (SEQUENTIAL)

Validate that MTDS downloads odds correctly with the new bookmakers= param and writes to GCS in the correct schema.

- [ ] [SCRIPT] P0. Run MTDS for 1 day (2026-03-27) with bookmakers= param, confirm 30 credits/call, verify GCS output
      schema matches migrated v3 data
- [ ] [SCRIPT] P0. Verify GCS output: 20 bookmakers, 14 time buckets, canonical instrument IDs, microsecond timestamps
- [ ] [SCRIPT] P1. Run MTDS for 7 days (2026-03-20 to 2026-03-27), time the run, extrapolate cost for 80-day backfill
- [ ] [SCRIPT] P1. Create MTDS sports doc at `market-tick-data-service/docs/SPORTS_ODDS.md` covering process, cost,
      schema

**Success criteria**: GCS parquet schema matches migrated data. Credits used = ~14K per day (30 × 14 buckets × 33
leagues).

## Phase 2: FSS E2E Validation (SEQUENTIAL, after Phase 1)

Validate that FSS reads from GCS and computes features correctly.

- [ ] [SCRIPT] P0. Run FSS for 1 day (2026-03-22 — has both reference data and odds), time the run
- [ ] [SCRIPT] P0. Verify output: check which of 23 calculators produce output, count features per group
- [ ] [SCRIPT] P1. Identify which calculators fail and why (missing provider data, missing GCS paths, etc.)
- [ ] [SCRIPT] P1. Run FSS for 7 days, time it, identify bottlenecks
- [ ] [SCRIPT] P1. Create FSS sports doc at `features-sports-service/docs/SPORTS_FEATURES.md`

**Success criteria**: At least odds-based calculators (odds_calculator, steam_detector) produce correct output from GCS
data.

## Phase 3: Odds Gap Backfill (PARALLEL with Phase 2)

Backfill 2025-12-31 to 2026-03-21 (~80 days) via MTDS batch.

- [ ] [SCRIPT] P0. Run MTDS backfill: `--start-date 2025-12-31 --end-date 2026-03-21` — estimated ~1.1M credits,
      ~20min/day
- [ ] [SCRIPT] P0. Verify no gaps: BigQuery `SELECT COUNT(DISTINCT day) FROM odds_ticks_hive` should show ~1,905 days
      (1825 migrated + 80 backfilled)
- [ ] [SCRIPT] P1. Update BigQuery external table if needed

**Success criteria**: Continuous odds coverage from 2020-06-06 to present. No date gaps.

## Phase 4: Feature Regeneration Timing (SEQUENTIAL, after Phase 2)

Profile feature regeneration cost to decide local vs VM.

- [ ] [SCRIPT] P0. Time FSS for 1 week of historical data (e.g. 2025-12-15 to 2025-12-21) — measures compute only, no
      API calls for odds calculators
- [ ] [SCRIPT] P0. Identify which calculators need live API calls (FootyStats, Understat, etc.) vs pure GCS reads
- [ ] [SCRIPT] P1. For GCS-only calculators: extrapolate to full 5.5 years, decide local vs VM
- [ ] [SCRIPT] P1. For API-dependent calculators: estimate API credit cost, decide batch strategy
- [ ] [SCRIPT] P2. If VM needed: use pattern from odds migration (e2-standard-2, asia-northeast1-b, screen session)

**Success criteria**: Clear time/cost estimate for full regeneration. Decision on local vs VM.

## Phase 5: Full Feature Regeneration (after Phase 4)

- [ ] [SCRIPT] P0. Run GCS-only feature calculators for full history (2020-06 to present)
- [ ] [SCRIPT] P1. Run API-dependent calculators where data available (FootyStats, Open-Meteo)
- [ ] [SCRIPT] P2. Verify feature counts: target 672 features across 23 groups
- [ ] [SCRIPT] P2. BigQuery external table over features bucket

**Success criteria**: Features parquets in GCS for full history. BigQuery-queryable.

## Phase 6: Cleanup + Convergence

- [ ] [SCRIPT] P1. Converge GCS path conventions: `sports_reference/by_date/entity=` vs `sports_reference/fixtures/day=`
- [ ] [SCRIPT] P1. Delete remaining orphaned GCS paths (old hyphenated instrument_availability, catalogue, test output)
- [ ] [SCRIPT] P1. Delete USRI odds_api.py adapter (orphaned — odds owned by UMI)
- [ ] [SCRIPT] P2. Reference data re-backfill with microsecond timestamps (fixtures/stats/events — quick ~20min)
- [ ] [SCRIPT] P2. Update handoff memory with final state

## Dependency Graph

```
Phase 1 (MTDS validation)
    │
    ├──→ Phase 2 (FSS validation)
    │        │
    │        └──→ Phase 4 (timing profile)
    │                  │
    │                  └──→ Phase 5 (full regeneration)
    │
    └──→ Phase 3 (odds backfill) ── PARALLEL with Phase 2
                                          │
                                          └──→ Phase 5

Phase 6 (cleanup) ── after all above
```
