---
title:
  api_football enrichment-only mode pre-flight vs runtime contract mismatch — blocks per-fixture entity backfill on
  forward-polled days
created: 2026-05-13
author: ikenna-slot-8
severity: P1
source:
  - instruments-service/instruments_service/engine/orchestrator.py (pre-flight check vs fixture_mapping_write)
  - VM af-backfill-20260513-161517 logs (failed 2026-05-13 15:18:55 UTC)
related:
  - plans/active/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md (Phase 3.C blocker)
  - plans/active/api_football_minimal_flattening_removal_2026_05_07.md (Phase 3 verification)
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## What I found

Launched `bash launch-api-football-backfill-vm.sh --entity FIXTURE_STATS 2026-04-26 2026-04-26` to verify Phase 3.C of
the api_football flattened-normalizer rollout. VM ran ~10s then failed with:

```
date=2026-04-26: per-entity breakdown — 0 core missing ([]), 1 per-fixture missing (['FIXTURE_STATS']), 0 instruments missing
date=2026-04-26: core entities fresh — enrichment-only mode for ['FIXTURE_STATS']
date=2026-04-26: 0 stale + 1 missing venues/entities — will re-fetch (stale=[], missing=['FIXTURE_STATS'])
[8s later]
ERROR fixture_mapping_write: 404 No such object:
  instruments-store-sports-central-element-323112/instrument_availability/by_date/day=2026-04-26/venue=API_FOOTBALL/instruments.parquet
WARNING Handler InstrumentsHandler failed on payload 1: record_empty() called with blank reason.
  Pass a typed reason from EMPTY_CONFIRMED_REASONS [row_key={'date': '2026-04-26', 'data_type': 'FIXTURE_STATS'}]
[vm-exec] command exited rc=1
DEPLOYMENT_FAILED (exit_code=1)
```

GCS verification: `gs://instruments-store-sports-central-element-323112/sports_reference/by_date/day=2026-04-26/` has 13
entity directories (fixtures, footystats\_\*, injuries, leagues, player_stats, progressive_stats, standings, teams,
transfermarkt_leagues, understat_xg, weather) but NO `entity=fixture_stats/` and NO
`instrument_availability/by_date/day=2026-04-26/venue=API_FOOTBALL/instruments.parquet`.

## Why it matters

1. **Forward-polled fixture days cannot enter per-fixture enrichment mode**. The orchestrator pre-flight asks "are
   instruments fresh?" and gets "yes" (`0 instruments missing`) — but the fixture_mapping_write phase then READS the
   instruments.parquet to merge with new mappings, and that file doesn't exist for any day where fixtures were captured
   via forward-poll BEFORE the per-fixture entities were ever fetched.

2. **Phase 3.C verification of api_football flattened-normalizer rollout is blocked** — cannot do an end-to-end VM run
   to produce a new-schema FIXTURE_STATS parquet without first remediating the missing `instruments.parquet`. Phase 3.B
   (live-API → normalizer shape verification) DID pass (Slot 8, 2026-05-13, fixture 1382849 — 2 stat rows × 18+ cols, 15
   events, 40 lineup players). The remaining Phase 3.C value-add is "GCS parquet + UI schema modal reflects new shape" —
   blocked.

3. **The manifest hardening IS working correctly here** (silver lining). When the 404 hit, the orchestrator tried to
   gracefully `record_empty()` with blank reason. The new UAC `EMPTY_CONFIRMED_REASONS` closed-set guard REJECTED the
   call (`LegacyBlankErrorReasonError` rule). This is writegate Phase 3.D.5 in force. Same shape protected the May-23
   critical path from silent empty-placeholder bugs (2026-05-05 incident reference).

## Recommended decision

Three options, in increasing scope:

### Option A — Fix the pre-flight contract (P1)

Update `orchestrator.py` pre-flight `0 instruments missing` check to ACTUALLY verify the instruments.parquet path
exists, OR teach the enrichment-only-mode path to handle the missing-instruments.parquet case (build a fresh mapping
from `entity=fixtures/` directly when the upstream availability parquet is absent). Scope: ~1 cal AI-day; well-scoped to
`orchestrator.py` per-entity pre-flight.

### Option B — Backfill the missing instruments.parquet per day (P2)

Run a one-shot script that walks `sports_reference/by_date/day=*/entity=fixtures/` and writes the corresponding
`instrument_availability/by_date/day=*/venue=API_FOOTBALL/instruments.parquet` for every forward-poll day where it's
missing. Then per-fixture enrichment can run. Scope: ~0.5 cal AI-day script + multi-hour data fill VM run.

### Option C — Defer Phase 3.C VM verification to next session (P2)

Phase 3.B already verified the code path against live API. The contract registry (UAC SchemaContracts) ships the new
shape regardless of GCS state. Phase 3.C end-to-end can wait until the natural sports forward-poll cycle re-touches
affected days OR until Option A/B remediates.

**Recommendation**: Option A is the right fix (pre-flight should accurately reflect what runtime opens). Operator triage
on cycle priority. Phase 3.B operational validation stands.

## Provenance

- Slot 8 (ikenna tab/8) launched VM 2026-05-13 16:15 UTC, failed 16:18 UTC, VM auto-deleted
- Pre-existing forward-poll backfill convention: fixtures captured at NS-status → status never updates →
  instruments.parquet rollup never runs
- Same root may affect other per-fixture entities (FIXTURE_EVENTS / FIXTURE_LINEUPS / PLAYER_STATS) on forward-polled
  days
