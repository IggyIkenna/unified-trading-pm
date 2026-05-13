# Sports fixtures lifecycle

> **SSOT for the lifetime of a sports fixture across the ingestion pipeline.** Codifies the state machine, per-state
> available_at semantics, and cross-source verifier design.

## State machine

A fixture moves through 8 states from creation to final settlement:

```
SCHEDULED ──► PRE_MATCH ──► LIVE ──► HALFTIME ──► LIVE_2H ──► MATCH_END ──► POST_MATCH ──► SETTLED
   │                                                              │
   ▼                                                              ▼
CANCELLED                                                    PARTIAL/ABANDONED
POSTPONED                                                    (rare; equivalent to MATCH_END for stats)
```

- **SCHEDULED**: Fixture announced, kickoff in the future. Only schedule/venue/team data exists.
- **PRE_MATCH**: T-60 min before kickoff. Lineups + final pre-match odds + weather forecast land.
- **LIVE**: Match in play, regulation 1st half. Live odds + progressive stats stream every ~30s.
- **HALFTIME**: 15-min break. Live data freezes; ad-hoc analyst notes.
- **LIVE_2H**: 2nd half + extra time + injury time. Live data resumes.
- **MATCH_END**: Final whistle. `timer_seconds` freezes — canonical match-end signal.
- **POST_MATCH**: Post-match data lands (final stats, xG, settled odds). Multi-source cascade.
- **SETTLED**: All post-match data consolidated; odds markets settled.

### Status-code mappings (per-source)

| State     | api_football `status_short` | SFI proxy                        | FootyStats  | Understat   |
| --------- | --------------------------- | -------------------------------- | ----------- | ----------- |
| SCHEDULED | `NS`                        | (no SFI row yet)                 | `scheduled` | (no row)    |
| PRE_MATCH | `NS` (within T-60min)       | (no SFI row yet)                 | `scheduled` | (no row)    |
| LIVE / 2H | `1H` / `2H` / `LIVE`        | `timer_seconds` advancing        | `live`      | (no live)   |
| HALFTIME  | `HT`                        | `ht_start_timer` ≤ ts ≤ `ht_end` | `live`      | (no live)   |
| MATCH_END | `FT` / `AET` / `PEN`        | `timer_seconds` frozen           | `complete`  | (rows land) |
| CANCELLED | `CANC`                      | (no SFI row)                     | `cancelled` | (no row)    |
| POSTPONED | `PST`                       | (no SFI row)                     | `postponed` | (no row)    |
| ABANDONED | `ABD` / `AWD`               | sparse                           | sparse      | sparse      |

Closed set lives in UAC `MatchStatus` SSOT (UAC@1a831b0 per sports_master). Reference:
`unified_api_contracts/canonical/domain/sports/match_status.py`.

## available_at semantics per state

Per CLAUDE.md "batch=live unified pipeline" rule, `available_at` MUST equal the live-pipeline-arrival timestamp. The
stamp depends on which state's data type is being written:

| Data type               | State signal     | available_at formula                                      |
| ----------------------- | ---------------- | --------------------------------------------------------- |
| FIXTURES (schedule)     | SCHEDULED        | announcement time (fetched_at when fixture first appears) |
| LINEUPS                 | PRE_MATCH        | `kickoff - 60min` (publication lag P95)                   |
| PRE_MATCH_ODDS          | PRE_MATCH        | last-update ≤ kickoff; stamped at last update             |
| WEATHER (forecast_t0)   | PRE_MATCH        | forecast issue time (~kickoff hour)                       |
| WEATHER (forecast_t24h) | SCHEDULED        | kickoff - 24h                                             |
| SFI_PROGRESSIVE_STATS   | LIVE → MATCH_END | per-snapshot wall-clock; freeze stamp = match_end_time    |
| LIVE_ODDS               | LIVE → MATCH_END | per-update wall-clock                                     |
| FIXTURE_STATS           | POST_MATCH       | `match_end_time + SFI_DATA_LAG_P95_SECONDS (=300s)`       |
| FIXTURE_PLAYER_STATS    | POST_MATCH       | same as FIXTURE_STATS                                     |
| Understat XG            | POST_MATCH       | Understat data-available timestamp (typically T+1h)       |
| FootyStats MATCHES post | POST_MATCH       | FootyStats fetched_at (batched, T+5-15min)                |
| WEATHER (actual)        | POST_MATCH       | OpenMeteo reanalysis publish time (T+24h)                 |
| RESULTS / SETTLEMENT    | SETTLED          | `match_end_time + settlement_window`                      |

`match_end_time` itself is resolved via the cascade documented in
[`match-end-time-cascade.md`](match-end-time-cascade.md) (UTL@89c0ae15).

## Cross-source fixture status verifier (design)

### Why this exists

Same fixture has rows in 4+ data sources (api_football, SFI, FootyStats, Understat). Each source publishes its own
status independently. **Cross-source drift is a silent correctness bug class** — e.g. api_football marks fixture `FT`
but SFI's `timer_seconds` is still advancing (replay or feed lag). Without cross-source reconciliation, downstream
features-sports may join post-match stats to a still-running fixture and produce stale features.

### Verifier responsibilities

1. **Detect divergence**: For each fixture, compare `MatchStatus` derived from each source. If sources disagree about
   which lifecycle state the fixture is in, raise a `FixtureStatusDriftError` (severity P1; not fail-fast — issue a
   finding doc).
2. **Detect late-arriving terminal state**: Track per-source latency to reach MATCH_END. If any source still reports
   LIVE > 30 min after another's MATCH_END timestamp, flag the lag for adapter ops review.
3. **Confidence rollup**: Compute a per-fixture "status confidence" = fraction of sources that agree on the current
   state. Surface in deployment-ui drilldown.

### Architecture

```
                              ┌──────────────────────────────┐
   api_football FIXTURES ────►│                              │
   SFI progressive freeze  ──►│ CrossSourceFixtureVerifier   │
   FootyStats MATCHES status►│ (features-sports OR new svc) │──► FixtureStatusReport
   Understat XG presence ───►│                              │     ├── consensus_state
                              └──────────────────────────────┘     ├── confidence (0..1)
                                                                   ├── disagreeing_sources[]
                                                                   └── drift_details
```

- **Runs**: per-fixture, daily after all sources have had P95 time to land (i.e. ~T+24h post-kickoff).
- **Input**: 4 parquet reads (api_football FIXTURES, SFI_PROGRESSIVE_STATS, FootyStats MATCHES, Understat XG) for the
  fixture's date partition.
- **Output**: `FixtureStatusReport` records written to a new `cross_source_fixture_status` data_type under
  `asset_group=sports, instrument_type=match`. Schema deferred — owner drafts on first concrete prototype.

### Decision logic (informal)

```python
def derive_consensus_state(
    af_status: MatchStatus | None,
    sfi_state: MatchStatus | None,
    fs_status: MatchStatus | None,
    us_present: bool,
) -> tuple[MatchStatus, float, list[str]]:
    """Returns (consensus_state, confidence_pct, disagreeing_sources)."""
    votes = [s for s in (af_status, sfi_state, fs_status) if s is not None]
    if not votes:
        return (MatchStatus.UNKNOWN, 0.0, ["all_sources_missing"])
    if us_present:
        # Understat only emits for completed matches in covered leagues
        votes.append(MatchStatus.MATCH_END)
    # Majority vote; tie-break by api_football (highest fidelity)
    ...
```

### Adapter integration

Each adapter MUST stamp its derived `MatchStatus` using the UAC SSOT enum, NOT ad-hoc string sets. This is the
"MatchStatus adapter migration" todo currently DEFERRED in sports_master:

- Replace `{"FT", "AET", "PEN"}` literal sets with `AF_COMPLETED_CODES` constant
- Replace `status in ("complete",)` checks with `status == MatchStatus.MATCH_END`
- Wire UAC's `MatchStatus.from_api_football_status_short()` / `.from_footystats_status()` / `.from_sfi_state()` helpers
  across the 4 adapters

This unblocks the verifier (which presumes every adapter produces canonical `MatchStatus`).

## Schema columns supporting lifecycle

| Contract                         | Lifecycle field                                        | UAC commit  |
| -------------------------------- | ------------------------------------------------------ | ----------- |
| `SPORTS_FIXTURES`                | `status_long`, `status_short`                          | (existing)  |
| `SPORTS_FIXTURES`                | `match_end_time`                                       | UAC@0ba9e5b |
| `SPORTS_SFI_PROGRESSIVE_STATS`   | `ft_timer`, `match_end_time`                           | UAC@1848647 |
| `SPORTS_SFI_PROGRESSIVE_STATS`   | `ht_start_timer`, `ht_end_timer`                       | (existing)  |
| (deferred) `CROSS_SOURCE_STATUS` | `consensus_state`, `confidence`, `disagreeing_sources` | TBD         |

## Cross-references

- **Plan**: `plans/epics/sports_master_2026_05_07.md` § "C.6 + C.10 match_end_time cascade"
- **Match-end cascade**: [`match-end-time-cascade.md`](match-end-time-cascade.md)
- **MatchStatus SSOT**: `unified_api_contracts/canonical/domain/sports/match_status.py`
- **Batch=live SSOT**: `codex/04-architecture/batch-live-architecture.md`
- **Availability stamping**: `codex/02-data/availability-manifest-and-data-status.md`
- **Honest absence**: `codex/02-data/honest-absence-downstream-handling.md`
