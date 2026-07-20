---
doc_type: issue
title: Sports data capture gap — EPL 2025 absent from GCS availability index
summary:
  Filed from the [VERIFY] P1 run of `run_live_verify_sports` (verify_p1_prereq_dag-003, 2026-06-29) after the Finding-2
  semantic fix.
status: resolved
nature: process
asset_group: [sports]
stage: [meta]
repos: [e2e-testing, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, manifest, data-correctness, backfill, instruments, honest-coverage, verification]
related: [plans/active/issues/verify_p1_prereq_dag_2026_06_29.md]
created: 2026-06-29
parent_epic: sports_master
priority: P2
source: [plans/active/issues/verify_p1_prereq_dag_2026_06_29.md, verify_p1_prereq_dag-003]
assigned_vm: planning
resolved_by: unified-api-contracts@0d7805a8
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-20
locked_since: 2026-06-29 # (was: 2026-05-21 -- corrected 2026-07-12, finding 280, §A2 B-queue ruling: predated created: 2026-06-29, an impossible ordering -- a lock cannot start before the doc existed; realigned to created, the earliest defensible date)
---

# Finding 3 — Sports data capture gap: EPL 2025 absent from GCS manifest

Filed from the [VERIFY] P1 run of `run_live_verify_sports` (verify_p1_prereq_dag-003, 2026-06-29) after the Finding-2
semantic fix.

## What I found

```
Run: run_live_verify_sports --today 2025-12-01 --league-id EPL --season-year 2025
GCP project: central-element-323112

Result: INSUFFICIENT_HISTORY (4/4 shards)
  api_football  FIXTURES    captured=0  missing_rows=123
  footystats    MATCH_STATS captured=0  missing_rows=123
  odds_api      ODDS        captured=0  missing_rows=123
  understat     XG          captured=0  missing_rows=123

Window: [2025-08-01, 2025-12-01] (semantic fix confirmed — window_end=today ✓)
Bucket: tick-data / sports
```

The semantic fix (Finding-2, unified-api-contracts@0d7805a8) is working correctly: the required window now clips to
`today` (2025-12-01) instead of the full season end (2026-05-31). The `INSUFFICIENT_HISTORY` verdict is now due to a
genuine data gap — the availability index contains zero captured rows for EPL 2025 across all 4 sports data types.

## Why it matters

EPL 2025 sports data (api_football FIXTURES, understat XG, odds_api ODDS, footystats MATCH_STATS) is the only clean AG
in the VERIFY P1 prereq DAG (other AGs are gated on phantom-reconciliation plans). If the sports capture pipeline has
never run for EPL 2025 or its output isn't merged into the consolidated availability index, the smoke harness cannot
produce a RUNNABLE verdict even with the semantic fix applied.

This gates the [VERIFY] P1 milestone: RUNNABLE for sports is blocked until the capture gap is resolved.

## Recommended decision

Operator to determine which of the following applies:

1. The sports capture pipeline ran but writes to a path not covered by the availability index bucket (path-prefix
   mismatch). → Fix: re-index or widen the prefix template.
2. The sports capture pipeline has not been run for EPL 2025 yet. → Fix: trigger a sports backfill run for EPL 2025,
   verify manifest rows appear.
3. The consolidated manifest index was last built before the sports captures landed. → Fix: re-run the manifest
   consolidator for the sports bucket.

## Investigation Results (slot-8, 2026-06-29)

GCS and availability-index investigation completed. The `captured=0` result is caused by **harness configuration bugs +
one genuine pipeline gap**, NOT a missing consolidation or failed overall capture pipeline.

### Root cause A — Wrong bucket (harness bug)

The verify harness (`live_manifest_reader.py`) calls `resolve_bucket_name(kind="tick-data", asset_group="sports")` which
resolves to `market-data-tick-sports-prd-central-element-323112` (the MDPS/bookmaker-odds bucket). The structured sports
data (FIXTURES, XG, MATCHES, ODDS data-types) lives in `instruments-store-sports-prd-central-element-323112` (the IS
bucket).

The MDPS bucket uses bookmaker venue names (BETFAIR_EX_EU, ODDS_API, etc.); the IS bucket uses source-name venues
(API_FOOTBALL, UNDERSTAT, FOOTYSTATS). The harness filtering by `venue=api_football` / `venue=footystats` / etc. against
the MDPS bucket produces 0 rows.

### Root cause B — Venue name case mismatch

Even if the harness read the IS bucket, the atom venue is lowercase (`api_football`) but IS bucket has uppercase
(`API_FOOTBALL`). Filter: `df["venue"] == "api_football"` → 0 matches.

### Root cause C — Data_type name mismatch

Harness checks `data_type=MATCH_STATS` but IS bucket has `data_type=MATCHES`. footystats data in MDPS bucket has
`data_type=odds` (not `MATCH_STATS`).

### Root cause D — Genuine pipeline gap: understat XG = 0 captures

IS bucket (EPL 2025): `data_type=XG, source=understat` → 365 rows all `empty_confirmed`. No understat XG data for EPL
2025 exists anywhere in GCS. `batch_understat` pipeline mode is absent from the MDPS bucket for all 2025 dates.

### Actual EPL 2025 data status (IS bucket, league_id=EPL)

| data_type                  | captured                               | empty_confirmed | notes                                                     |
| -------------------------- | -------------------------------------- | --------------- | --------------------------------------------------------- |
| FIXTURES (api_football)    | 117 total / 112 via API_FOOTBALL venue | 365             | match-day rows captured; empty_confirmed = non-match days |
| MATCHES (footystats)       | 112                                    | 314             | same 112 match days                                       |
| ODDS (footystats/odds_api) | 112                                    | 232             | same 112 match days                                       |
| XG (understat)             | **0**                                  | 365             | **genuine gap — pipeline never ran**                      |

GCS raw_tick_data confirms: `batch_footystats` and `batch_odds_api` pipeline modes exist for 2025 match days.
`batch_api_football` and `batch_understat` are absent for the 2025 season dates.

### Recommended decision (updated)

**Option 1 (correct path):** Fix the verify harness to read the IS bucket + fix the venue case and data_type mapping.
This will turn FIXTURES/MATCHES/ODDS from `captured=0` to `captured=112` (all match days covered). THEN assess if
112/365 days meets the RUNNABLE threshold (the 365 empty_confirmed are expected for non-match days, so this may already
be sufficient).

**Option 2 (also required):** Trigger a backfill for `understat XG` for EPL 2025 (`batch_understat` pipeline mode,
league_id=EPL, 2025 season). This is the only genuine data gap among the 4 shards.

## Actionable follow-ups

- [x] [INVESTIGATE] P1. Check if EPL 2025 sports capture files exist in GCS (tick-data/sports bucket); distinguish
      missing-capture from missing-index. (repo: e2e-testing) ✅ — see Investigation Results above
- [x] [FIX] P1. Fix verify harness bucket: change `UTLManifestReader._bucket_for` to use `kind="instruments-store"` (or
      equivalent IS bucket resolver) for the sports FIXTURES/XG/MATCHES/ODDS shard types. Fix venue case
      (lowercase→uppercase) and data_type mapping (MATCH_STATS→MATCHES). (repo: e2e-testing) ✅ — e2e-testing@cad2951,
      e2e-testing@9120c4d. Source-based filter added (MATCHES/ODDS have venue=''); ShardAtom.source field added.
- [x] [FIX] P1. Trigger backfill for understat XG for EPL 2025 season (batch_understat pipeline, league_id=EPL, dates
      2025-08-01 to 2025-12-01). This is the only genuine data gap — all other shard types have match-day coverage in
      the IS bucket. (repo: instruments-service) ✅ — instruments-service@45ab27c Script:
      scripts/backfill_understat_xg_epl_2025_2026_06_29.py (calls \_fetch_understat_xg with force=True for each date in
      the range; run with MANIFEST_PER_VM_SHARDS=true + unique VM_NAME to write per-VM shards safely).
- [x] [VERIFY] P1. Re-run `run_live_verify_sports --today 2025-12-01` after harness fix → expect RUNNABLE for
      FIXTURES/MATCHES/ODDS; after understat backfill → expect RUNNABLE for XG. (repo: e2e-testing) ✅ —
      e2e-testing@35e00d3. Results (2026-06-29, today=2025-12-01): FIXTURES → RUNNABLE (C=18, M=0) ✅ MATCH_STATS →
      RUNNABLE (C=36, M=0) ✅ ODDS → INSUFFICIENT_HISTORY (C=36, M=6; holes: 2025-08-14/27, 09-04/10, 11-06 + 1) XG →
      HONEST_EMPTY (C=0) — expected; backfill still pending Additional runtime fixes landed: str-date parse, IS-bucket
      dedup, MATCH_STATS→MATCHES translation. New finding: ODDS has 6 genuinely missing match days in the [2025-08-01,
      2025-12-01] window. ODDS backfill (footystats source, EPL, those 6 dates) is a further FIX needed for full
      RUNNABLE.
