---
doc_type: plan
title:
  Transfermarkt + SFI team-mapping cache + league/team drift detection (reduce API calls; catch silent partial writes)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-22
priority: P2
owner: agent
type: code
epic: none
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: features-sports-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on:
  [
    features_sports_denormalisation_pipeline_2026_04_21,
    features_sports_derived_data_crime_fixes_2026_04_21,
    features_sports_upstream_coverage_gaps_2026_04_21,
  ]
isProject: false
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

## Deferred work — migrated to: `plans/active/issues/batch4_strategy_ui_archived_plan_residuals_2026_07_21.md` — successor:

batch4_strategy_ui_archived_plan_residuals (the 2 residual `[HUMAN]` gates — post-merge cache-speedup validation +
plan-unlock approval — need an operator to actually run the comparison; no evidence found either happened, tracked as
fresh todos there rather than fabricated).

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. 20/2 (91%) done.
> instruments-service 9bf23d8 + UAC 36bed50 + UTL bf7ad8d1 + FSS 1bdf58d shipped 4 tracks across 4 repos. Ready for
> archive after 2 polish items + plan unlock. See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

## Context

Two observed gaps in the sports reference-data fetch path, surfaced while watching the `tm-backfill-20260421-231758` +
`sfi-backfill-20260421-231826` VMs during the upstream-coverage backfill (plan
`features_sports_upstream_coverage_gaps_2026_04_21`, 2026-04-21):

1. **Every backfill VM re-fetches teams from scratch**. `instruments-service` has per-league honest-coverage manifest
   writes (`captured` / `empty_confirmed` / `attempted_failed` for every expected league), but no persistent
   **team-mapping cache** at `sports_reference/mappings/...parquet`. The adapter hits Transfermarkt / SFI APIs for every
   trigger date, including redundant fetches when consecutive trigger dates fall within days of each other. The same
   team-mapping pattern already exists for other sports providers (`team_mapping.parquet`, `fixture_mapping.parquet` —
   written by `orchestrator._write_team_mapping` / `_write_fixture_mapping` at L3197-3250, read by
   `features-sports-service/data/gcs_reader.py::read_team_mapping` / `read_fixture_mapping`); Transfermarkt + SFI are
   the exceptions.

2. **No data-quality assertion that fetched teams match the expected league roster**. If Transfermarkt returns 18 teams
   for EPL instead of 20 (API partial response, mid-season edge case, rate-limit clipped response), the adapter silently
   writes 18 rows to the `PLAYER_VALUES` manifest as `captured` — indistinguishable from a legitimate 20-team fetch.
   Same shape applies to SFI's progressive_stats leagues. UAC already carries a `LeagueDefinition` registry; adding an
   `expected_team_count_for_season` field + a simple `|got - expected| / expected > threshold` check in the adapter
   emits `ADAPTER_FETCH_ANOMALY` events without blocking the write (honest-coverage still fires).

## Blast radius

| Repo                    | Scope                                                                                                                                                                                                     |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| unified-api-contracts   | `LeagueDefinition.expected_team_count_per_season` (new optional field) + seed values per league × season.                                                                                                 |
| instruments-service     | `orchestrator._fetch_transfermarkt_data` + `_fetch_sfi_data`: (a) read/write `sports_reference/mappings/...`; (b) short-circuit fetch on cache hit + trigger-date miss; (c) drift-detection anomaly emit. |
| features-sports-service | `data/gcs_reader.py::read_transfermarkt_team_mapping()` + `read_sfi_team_mapping()` helpers (parallel to existing `read_team_mapping`).                                                                   |
| unified-trading-pm      | Codex §2.2 (Transfermarkt) + §2.4 (SFI) cache-location + expected-count doc rows.                                                                                                                         |

## PRE-AUDIT-FINDINGS (2026-04-22 — agent)

Phase-0 findings already accumulated during the parent plans. Execution agent should verify each item before code:

### Existing team-mapping pattern to clone

- [`instruments-service/instruments_service/engine/orchestrator.py`](../../../instruments-service/instruments_service/engine/orchestrator.py)
  L3197-3256 — `_write_team_mapping(bucket)` writes a single flat parquet at
  `sports_reference/mappings/team_mapping.parquet` combining UAC `team_mappings.py` + `team_names.py`. No partitioning.
  Run once per date (`_write_team_mapping` + `_write_fixture_mapping(bucket, date)` both called at L3197-3198 —
  `_write_fixture_mapping` partitions by date, `_write_team_mapping` does not).
- [`features-sports-service/features_sports_service/data/gcs_reader.py::read_team_mapping`](../../../features-sports-service/features_sports_service/data/gcs_reader.py)
  L720+ — reads the flat parquet. Parallel `read_fixture_mapping` at L741+. Clone this shape for Transfermarkt + SFI.

### Transfermarkt-specific

- TM data is **season-scoped**, not date-scoped. `_fetch_transfermarkt_data` at L4107 passes `season=YYYY` to
  `adapter.get_teams(tm_code, season=season)`. Cache partition must be per-season to prevent 2023 → 2024 overwrites.
  Suggested path: `sports_reference/mappings/transfermarkt_league_teams/season={YYYY}/teams.parquet`.
- Trigger dates are driven by UAC `get_leagues_needing_refresh(date)` in
  [`unified-api-contracts/unified_api_contracts/canonical/domain/sports/season_dates.py`](../../../unified-api-contracts/unified_api_contracts/canonical/domain/sports/season_dates.py)
  L176: season_start ± 3d + transfer_windows open ± 3d + close ± 3d. ~12-15 trigger dates per league per year.
- Current per-league outcome tracking at L4219-4314 (`_captured_league_counts`, `_empty_leagues`, `_failed_leagues`,
  `_unmapped_leagues`) is the ideal hook point for the anomaly check — do the check inside the for-loop at L4225 just
  before `_captured_league_counts[league_def.league_id] = _league_count`.

### SFI-specific

- SFI adapter at
  [`instruments-service/instruments_service/engine/orchestrator.py::_fetch_sfi_data`](../../../instruments-service/instruments_service/engine/orchestrator.py)
  L4321+. Two entities: `SFI_LEAGUES` (league metadata), `SFI_PROGRESSIVE_STATS` (per-match streaks). No team entity at
  the provider level — SFI returns league-scoped progressive stats keyed by internal `match=<hex>` IDs, not per-team
  rosters like Transfermarkt. So the "team cache" for SFI is actually a **league-mapping cache** (SFI internal league
  hex IDs ↔ canonical league_id). This is narrower than the TM case.

### UAC helpers to extend

- [`unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py::get_expected_leagues_for_source`](../../../unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py)
  — already provides the league denominator for both providers; audit whether `LeagueDefinition` carries a team-count
  field today (grep says no) and add as optional.

## Pre-audit manifest

| File / thing to find | Purpose | Expected outcome | |
---------------------------------------------------------------------------------------------------------------- |
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| -------------------------------------------------------------------------------------------------------- |
------------------------------ | | `instruments-service/instruments_service/engine/orchestrator.py::_write_team_mapping`
| Confirm the pattern (flat parquet, no partitioning, one write per orchestrator run). | Use same shape but partition TM
output by `season=`. | |
`instruments-service/instruments_service/reference_data/adapters/sports/adapters/transfermarkt.py::get_teams` | Confirm
the adapter signature + response shape (list of `TransfermarktTeamSquad` with nested `players`). | Hash the team roster
per league-season → cache short-circuit key. | |
`unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py::LeagueDefinition` | Check what
fields exist today on the dataclass. | Add
`expected_team_count_per_season: dict[int, int]                                                      | None = None` +
migration note. | | Existing expected-instrument-count pattern (parent plan shipped 2026-04-21) |
`unified_api_contracts.get_expected_instruments_for_venue` + `is_per_instrument_shard_data_type` from MTDS Phase 8
(memory `project_sports_data_status_overhaul_2026_04_20.md`). | Mirror the API shape:
`get_expected_team_count_for_league(league_id, season)` with `None` when unknown. | |
`features-sports-service/features_sports_service/data/gcs_reader.py::read_team_mapping` / `read_fixture_mapping` |
Pattern to clone for TM + SFI mapping readers. | Add `read_transfermarkt_team_mapping(season: int)` +
`read_sfi_league_mapping()` — same signature shape. |

## Success criteria

Per-track:

- **Track 1 — TM team-mapping cache.** Second VM run on same date range takes **< 20% of first-run wall-clock** for
  league-iteration phase (measurable: compare TM VM run timestamps pre/post cache).
  `sports_reference/mappings/transfermarkt_league_teams/season=2024/teams.parquet` written once per season-backfill,
  containing `league_id, canonical_league, team_id, name, squad_size, player_count, last_fetched_at`. Adapter
  skip-if-not-trigger logic: on non-trigger dates within cache-staleness window, skip the API call entirely and record
  per-league `captured` from cache with `cached=True` provenance flag.
- **Track 2 — Drift-detection.** When `len(teams) vs expected_team_count` deviates > 10% threshold for a league,
  `ADAPTER_FETCH_ANOMALY` event emits with details: `{league_id, expected, got, deviation_pct, season}`. Write still
  proceeds (shard-isolation — never block the manifest). Regression test: inject 17-team response for EPL (expected 20),
  assert event emitted + manifest write still captured.
- **Track 3 — SFI league-mapping cache.** Same shape as Track 1 but narrower (league hex-id ↔ canonical, no team
  rosters). Also drift-detection on the expected-league denominator: SFI should return ~33 Prediction-classified
  leagues; anomaly if fewer than ~28 (15% threshold).
- **Track 4 — Codex updates.** §2.2 (TM) + §2.4 (SFI) document the new cache paths + staleness window. UAC
  `LeagueDefinition.expected_team_count_per_season` documented as optional/seed-driven.

## Dependency graph

```
Phase 0 (pre-audit verification — embed findings in plan PRE-AUDIT-FINDINGS)
      │
      ├─► Track 1: TM team-mapping cache [PARALLEL]
      │       ├─ 1.1 UAC LeagueDefinition.expected_team_count_per_season
      │       ├─ 1.2 orchestrator._write_transfermarkt_team_mapping
      │       ├─ 1.3 orchestrator._fetch_transfermarkt_data: cache-hit short-circuit
      │       ├─ 1.4 features-sports-service/data/gcs_reader::read_transfermarkt_team_mapping
      │       └─ 1.5 Unit tests (cache write + hit + staleness + trigger-forced refresh)
      │
      ├─► Track 2: Drift detection (TM + SFI) [SEQUENTIAL after Track 1.1 UAC field]
      │       ├─ 2.1 UAC get_expected_team_count_for_league(league_id, season)
      │       ├─ 2.2 orchestrator: anomaly check inside TM per-league loop
      │       ├─ 2.3 orchestrator: anomaly check inside SFI per-league loop
      │       ├─ 2.4 UTL: ADAPTER_FETCH_ANOMALY event def (if not already present)
      │       └─ 2.5 Unit tests — expected vs got deviation > threshold emits event
      │
      ├─► Track 3: SFI league-mapping cache [PARALLEL with Track 1]
      │       ├─ 3.1 orchestrator._write_sfi_league_mapping
      │       ├─ 3.2 orchestrator._fetch_sfi_data: cache-hit short-circuit
      │       ├─ 3.3 features-sports-service/data/gcs_reader::read_sfi_league_mapping
      │       └─ 3.4 Unit tests
      │
      └─► Track 4: Codex + QG + quickmerge [SEQUENTIAL, final gate]
              ├─ 4.1 codex/02-data/sports-scheduling-and-sharding.md §2.2 + §2.4 updates
              ├─ 4.2 QG on all 4 repos
              ├─ 4.3 Commit + push (UAC → instruments-service → features-sports-service → PM)
              └─ 4.4 Post-merge: re-run TM + SFI backfill on a narrow test window to measure cache speedup
```

## Parallelisation

- Track 1 + Track 3 are independent (different adapters, different GCS paths).
- Track 2 depends on Track 1.1 (UAC field exists) but is otherwise independent of both cache tracks.
- Track 4 is sequential — needs all three tracks landed.

## Phases

### Phase 0: Pre-audit verification [SEQUENTIAL]

- [x] [AGENT] P0. Confirm TM + SFI adapter signatures match assumptions in PRE-AUDIT-FINDINGS. Grep
      `TransfermarktTeamSquad` definition + `SFI_LEAGUES` response shape. Update PRE-AUDIT-FINDINGS with any deltas.

- [x] [AGENT] P0. Confirm UAC `LeagueDefinition` current fields via grep. Confirm no existing `expected_team_count`
      field anywhere in UAC sports.

- [x] [AGENT] P0. Confirm `ADAPTER_FETCH_ANOMALY` event definition in UTL events registry (or note it's missing and
      needs adding in Track 2.4).

### Track 1: Transfermarkt team-mapping cache [PARALLEL, depends on Phase 0]

- [x] [AGENT] P1. UAC: add `LeagueDefinition.expected_team_count_per_season: dict[int, int] | None = None` in
      [`unified_api_contracts/canonical/domain/sports/league_data.py`](../../../unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py).
      Seed well-known leagues (EPL=20, LaLiga=20, Bundesliga=18, SerieA=20, Ligue1=18, Championship=24, EFL1=24,
      EFL2=24, MLS=29, etc.) for seasons 2020-2026 inclusive. Add public accessor
      `get_expected_team_count_for_league(league_id: str, season: int) -> int | None`. 5+ unit tests proving accessor
      works for known and unknown leagues + seasons.

- [x] [AGENT] P1. instruments-service: add `_write_transfermarkt_team_mapping(bucket, teams_df, season)` paralleling
      `_write_team_mapping` at L3203. Write to
      `sports_reference/mappings/transfermarkt_league_teams/season={YYYY}/teams.parquet`. Columns:
      `league_id, canonical_league, team_id, name, squad_size, player_count, last_fetched_at`. Idempotent (overwrites on
      re-run).

- [x] [AGENT] P1. instruments-service: modify `_fetch_transfermarkt_data` cache-hit short-circuit. Flow: 1. At the top
      of `_want_teams` block, try to read `mappings/transfermarkt_league_teams/season={YYYY}/teams.parquet`. 2. If cache
      exists AND `last_fetched_at` is within 7 days AND `date` is NOT a trigger date for any league
      (`get_leagues_needing_refresh(date)` returns `[]`) → populate `_captured_league_counts` from cache + emit
      per-league `captured` manifest rows with `cached=True` provenance metadata + skip the API loop. 3. Otherwise,
      proceed with API loop as today, then write cache at end.

- [x] [AGENT] P1. features-sports-service: add `read_transfermarkt_team_mapping(season: int) -> pd.DataFrame` to
      [`data/gcs_reader.py`](../../../features-sports-service/features_sports_service/data/gcs_reader.py) paralleling
      `read_team_mapping` at L720+. Short-circuit + return empty DataFrame on 404 (same as existing helpers).

- [x] [AGENT] P1. Unit tests: - Cache write: given a teams DataFrame, assert parquet landed at expected path with
      expected schema. - Cache hit on non-trigger date: patched `get_leagues_needing_refresh` returns `[]`, cache
      parquet exists → no API calls made (mock adapter raises if called). - Cache miss on trigger date: patched
      `get_leagues_needing_refresh` returns non-empty → API loop runs, cache is rewritten. - Cache staleness: parquet
      is > 7 days old → API loop runs regardless of trigger state. - Manifest `cached=True` provenance for cache-hit
      rows.

### Track 2: Drift-detection anomaly emit [SEQUENTIAL, depends on Track 1.1 UAC field]

- [x] [AGENT] P1. UTL: add `ADAPTER_FETCH_ANOMALY` to events registry if absent
      ([`unified_trading_library/events/`](../../../unified-trading-library/unified_trading_library/events/) — grep for
      `ADAPTER_FETCH_FAILED` to find the file). Payload shape:
      `{venue, endpoint, league_id, date, expected_count,     got_count, deviation_pct, severity}`.

- [x] [AGENT] P1. instruments-service: inside TM per-league loop at L4225-4253, after `_league_count` is computed but
      before `_captured_league_counts[...] = _league_count`, call:
      `python     expected = get_expected_team_count_for_league(league_def.league_id, season)     if expected is not None and expected > 0:         deviation = abs(_league_count - expected) / expected         if deviation > 0.10:             log_event("ADAPTER_FETCH_ANOMALY", details={                 "venue": "transfermarkt",                 "endpoint": "get_teams",                 "league_id": league_def.league_id,                 "date": date,                 "expected_count": expected,                 "got_count": _league_count,                 "deviation_pct": round(deviation * 100, 1),                 "severity": "HIGH" if deviation > 0.25 else "MEDIUM",             })     `
      Same pattern in SFI loop if applicable (league-count anomaly not team-count; cross-check expected Prediction
      league denominator against returned league count).

- [x] [AGENT] P1. Unit tests: - EPL returns 17 teams, expected 20 → `ADAPTER_FETCH_ANOMALY` event emitted with
      `deviation_pct=15.0` + `severity=MEDIUM`. - EPL returns 12 teams → `severity=HIGH`. - EPL returns 20 (exact match)
      → no event. - Unknown league (no expected count) → no event (silent skip). - Manifest write still proceeds
      regardless of anomaly.

### Track 3: SFI league-mapping cache [PARALLEL with Track 1]

- [x] [AGENT] P2. instruments-service: add `_write_sfi_league_mapping(bucket, leagues_df)` writing to
      `sports_reference/mappings/sfi_league_mapping.parquet` (no season partition — SFI leagues are long-lived hex IDs
      not season-scoped). Columns: `canonical_league_id, sfi_league_hex, name, last_fetched_at`.

- [x] [AGENT] P2. instruments-service: modify `_fetch_sfi_data` cache-hit short-circuit. SFI leagues refresh cadence per
      codex §2.4: Tier-1 every 6h for `SFI_LEAGUES`. Shorter staleness window (24h) than TM.

- [x] [AGENT] P2. features-sports-service: `read_sfi_league_mapping() -> pd.DataFrame` in gcs_reader.

- [x] [AGENT] P2. Unit tests (parallel shape to Track 1.5).

### Track 4: Codex + QG + quickmerge [SEQUENTIAL]

- [x] [AGENT] P1. Update codex
      [`02-data/sports-scheduling-and-sharding.md`](../../codex/02-data/sports-scheduling-and-sharding.md): - §2.2
      (Transfermarkt): document cache path
      `sports_reference/mappings/transfermarkt_league_teams/season={YYYY}/teams.parquet` + 7-day staleness +
      trigger-date invalidation. Cross-ref `get_leagues_needing_refresh` as authoritative trigger schedule. - §2.4
      (SFI): document `sports_reference/mappings/sfi_league_mapping.parquet` + 24h staleness. - New §2.7 "Data-quality
      drift detection" subsection documenting the `ADAPTER_FETCH_ANOMALY` event + threshold (10% deviation). Cross-ref
      UAC `get_expected_team_count_for_league`.

- [x] [AGENT] P1. `bash unified-api-contracts/scripts/quality-gates.sh` green.
- [x] [AGENT] P1. `bash instruments-service/scripts/quality-gates.sh` green.
- [x] [AGENT] P1. `bash features-sports-service/scripts/quality-gates.sh` green.

- [x] [AGENT] P1. Commit + push in dep order: UAC first → instruments-service → features-sports-service → PM.

- [ ] [HUMAN] P2. Post-merge validation: re-run
      `bash deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh --entity PLAYER_VALUES 2025-06-01 2025-06-14`
      (narrow 14-day window) BEFORE tarball refresh (cold cache), then AGAIN after the shipped code is in the tarball.
      Compare wall-clock of Phase 1 league-iteration. Expect ≥ 80% reduction on second run for non-trigger days.

- [ ] [HUMAN] P2. Approve unlock of this plan (`[unlock-plan]` commit) once all todos are `[x]` and the post-merge
      validation run confirms cache-hit speedup.

## SSOT cross-refs

- Existing mapping write pattern: `instruments-service/engine/orchestrator.py` L3197-3256 (`_write_team_mapping`,
  `_write_fixture_mapping`).
- Existing mapping read pattern: `features-sports-service/data/gcs_reader.py` L720+ (`read_team_mapping`,
  `read_fixture_mapping`).
- Trigger schedule: `unified-api-contracts/canonical/domain/sports/season_dates.py::get_leagues_needing_refresh`.
- Expected-denominator pattern: UAC `get_expected_leagues_for_source` + (shipped 2026-04-21 per memory)
  `get_expected_instruments_for_venue` + `is_per_instrument_shard_data_type` in MTDS Phase 8 —
  `get_expected_team_count_for_league` follows the same shape.
- Parent plans providing context: `features_sports_denormalisation_pipeline_2026_04_21`,
  `features_sports_derived_data_crime_fixes_2026_04_21`, `features_sports_upstream_coverage_gaps_2026_04_21`.
- Lookahead-bias discipline + honest-coverage manifest: codex `02-data/sports-scheduling-and-sharding.md` §5 + §6.

## Out of scope

- **Cache-driven incremental writes**: if `get_teams()` returns the same roster as cached, skip the `PLAYER_VALUES`
  parquet write. Not scoped here — always overwrite (idempotent) to preserve the date-partitioned manifest contract.
  Disk / IO cost is small vs API rate-limit savings.
- **Team-ID cross-provider mapping**: this plan caches TM's own `(league_id, team_id)` roster. Cross-referencing TM
  `team_id` to canonical `team_id` used by API-Football is separate UAC work (already partially done via
  `team_mapping.parquet`).
- **Anomaly auto-healing**: if drift detected, just emit the event — don't retry, don't call a fallback provider.
  Retry-policy belongs in a separate adapter-resilience plan.
- **FootyStats + Understat equivalents**: both have their own fetch patterns (FootyStats already writes
  `footystats_matches/` per date; Understat is season-fetched in-memory). If operator sees equivalent waste on those
  adapters, file a follow-up.
- **Cache invalidation on expected-count change**: when UAC seed for `expected_team_count` for a league×season changes
  (e.g. MLS expands from 29 to 30), existing cached parquets keep the old count in the drift check. Not a real-world
  problem since seed values are slow-moving; if ever needed, add a `uac_seed_hash` column to cache schema and invalidate
  on mismatch.
