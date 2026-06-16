---
scope: [engineer, admin]
title: Match end-time resolution cascade
type: data
status: living
last_reviewed: 2026-05-17
owner: sports-domain
---

# Match end-time resolution cascade

> **SSOT for sports fixture `match_end_time` derivation.** Codifies the priority order used by
> `unified_trading_library.fixtures.resolve_match_end_time()` (UTL@89c0ae15 / C.6 Step 3).

## Why match_end_time exists

Sports fixtures emit data across two distinct phases — pre-match (lineups, odds, weather) and post-match (final stats,
xG, settled odds). Post-match data_types need a defensible timestamp for `available_at` stamping per CLAUDE.md
"batch=live unified pipeline" rule. The wall-clock kickoff time is insufficient: a match can run 90-120+ min depending
on stoppage, extra time, and penalties.

`match_end_time` is that defensible timestamp — the canonical UTC moment a match concluded, used to:

- Stamp `available_at` on post-match parquets (FIXTURE_STATS, SFI_PROGRESSIVE_STATS, understat XG)
- Settle market-closing odds windows (no settlement before match end)
- Compute live-pipeline-arrival latency for live=batch parity checks
- Bound the live-poll window for SFI progressive-stats freeze detection

## Cascade priority (first-match wins)

| Priority | Source                               | Provenance label               | Confidence |
| -------- | ------------------------------------ | ------------------------------ | ---------- |
| 1        | api_football FIXTURES.match_end_time | `api_football_native`          | High       |
| 2        | SFI progressive-stats freeze detect  | `sfi_freeze_detect`            | High       |
| 3        | FootyStats post-match data timestamp | `footystats_post_match`        | Medium     |
| 4        | Understat post-match data timestamp  | `understat_post_match`         | Medium     |
| 5        | `kickoff_utc + 120min` fallback      | `kickoff_plus_120min_fallback` | Low        |

### Why this order

- **api_football native (top)**: api_football's FIXTURES endpoint exposes
  `periods.second.duration + et.duration + injury_time` deltas, allowing exact computation:
  `match_end_time = kickoff + 1st_half + halftime_break + 2nd_half + et + injury_time`. This is authoritative when
  api_football covers the fixture.
- **SFI freeze detect (2)**: SFI's progressive-stats feed polls every ~30s. When `timer_seconds` stops advancing for ≥2
  consecutive snapshots, the last advancing snapshot's `available_at` is the canonical match-end. Stamped via UTL
  `detect_match_end_time()` helper (instruments-service).
- **FootyStats post-match (3)**: FootyStats publishes consolidated post-match data with a `fetched_at` timestamp. Lower
  fidelity than (1) and (2) because the fetch is batched and may lag match end by 5-15 min, but still bounded.
- **Understat post-match (4)**: Same shape as (3). Lower priority than FootyStats only because Understat's coverage is
  narrower (top-flight only).
- **kickoff + 120min fallback (5)**: Catch-all for fixtures where no upstream source has populated the match-end signal
  yet. 120 min covers a typical regular-time match (90 min) + halftime (15 min) + injury time + safety margin. Should
  never be the durable answer; re-resolve once upstream backfills land.

## Implementation

### UTL helper

```python
from unified_trading_library.fixtures import resolve_match_end_time, MatchEndTimeResolution

result: MatchEndTimeResolution = resolve_match_end_time(
    fixture_id="f12345",
    af_match_end_time=fix.match_end_time,        # from api_football FIXTURES parquet
    sfi_freeze_time=sfi_freeze,                   # from SFI progressive-stats freeze detect
    footystats_post_match_time=fs_fetched_at,    # from FootyStats MATCHES parquet
    understat_post_match_time=us_fetched_at,     # from Understat XG parquet
    kickoff_utc=fix.kickoff_utc,                  # always pass for fallback
)
# result.timestamp -> datetime
# result.provenance -> str (cascade label)
```

Raises `ValueError` only when **all sources are None** (including kickoff_utc). Callers must guarantee at minimum
`kickoff_utc` is present.

### Downstream consumers

Wire `resolve_match_end_time()` at write-time in these adapters (C.6 Step 4):

- **instruments-service** FIXTURE_STATS writer
- **instruments-service** SFI_PROGRESSIVE_STATS writer (already wired per instruments-service@af06124 via
  `detect_match_end_time()` + `SFI_DATA_LAG_P95_SECONDS`)
- **instruments-service** understat XG writer
- **instruments-service** fixture_player_stats writer

Each writer:

1. Loads source data for the fixture
2. Calls `resolve_match_end_time()` with whatever sources it has access to
3. Stamps the returned timestamp on the row's `match_end_time` column AND uses it as the basis for `available_at`
   (typically `match_end_time + SOURCE_LAG_P95`)
4. Logs `result.provenance` for traceability

## Schema columns

The cascade output lands in these UAC schema contracts:

| Contract                       | Column           | dtype               | Notes                                     |
| ------------------------------ | ---------------- | ------------------- | ----------------------------------------- |
| `SPORTS_FIXTURES`              | `match_end_time` | datetime64[ns, UTC] | Wired in IS orchestrator (C.6 Step 1)     |
| `SPORTS_SFI_PROGRESSIVE_STATS` | `match_end_time` | datetime64[ns, UTC] | UAC@1848647 (C.6 Step 2)                  |
| `SPORTS_SFI_PROGRESSIVE_STATS` | `ft_timer`       | int64               | UAC@1848647 — raw timer_seconds at freeze |
| `SPORTS_FIXTURE_STATS`         | `match_end_time` | datetime64[ns, UTC] | Pending — C.6 Step 4 wiring               |

## Tests

Unit tests at `unified-trading-library/tests/unit/test_fixtures_resolver.py` (UTL@520cbb2a) cover:

- Each cascade tier wins when present
- Cascade skips None sources without short-circuiting
- ValueError raised when all sources None
- NamedTuple return supports unpacking
- Fallback math (kickoff + 120min) is exact

## Cross-references

- **Plan**: `plans/epics/sports_master.md` § "C.6 + C.10 match_end_time cascade"
- **Implementation**: `unified-trading-library/unified_trading_library/fixtures.py`
- **Batch=live SSOT**: `codex/04-architecture/batch-live-architecture.md`
- **Availability stamping**: `codex/02-data/availability-manifest-and-data-status.md`
- **Honest absence**: `codex/02-data/honest-absence-downstream-handling.md`
