---
doc_type: plan
title:
  features-sports — close upstream-data coverage gaps (Transfermarkt 2020-26 backfill, SFI LEAGUES+PROGRESSIVE backfill,
  weather venue-id cross-ref)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-21
priority: P1
owner: agent
type: code
epic: none
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: deployment-service, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: features-sports-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: [features_sports_denormalisation_pipeline_2026_04_21, features_sports_derived_data_crime_fixes_2026_04_21]
isProject: false
---

## Deferred work — migrated to: `plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md` —

successor: instruments_mtds_subset_consistency_remediation_2026_06_17 (both post-backfill verification items are
subsumed by that plan's still-open Transfermarkt PLAYER_VALUES / SFI_PROGRESSIVE_STATS backfill-verification todo; the
literal `SFI_LEAGUES` check is additionally moot — that data_type was retired 2026-04-24. The
`[HUMAN] P0. Approve unlock` item is a stale leftover from an already-completed archival — no `locked_by` is set on this
file.)

## Context

While shipping the denormalisation pipeline (plan `features_sports_denormalisation_pipeline_2026_04_21`) and the
data-crime follow-up (`features_sports_derived_data_crime_fixes_2026_04_21`), three upstream-data gaps surfaced that
prevent the pipeline from producing non-NULL values in prod. None of them are pipeline logic bugs (the 31 pipeline unit
tests remain green); all three are raw-layer coverage or cross-ref issues.

## PRE-AUDIT-FINDINGS (2026-04-21 — agent)

### Track A — Transfermarkt `player_values` backfill (operator task)

- Prod partitions exist only for `day=2019-01-01 / 2019-01-02` under
  `gs://instruments-store-sports-central-element-323112/sports_reference/by_date/day={D}/entity=player_values/`.
- `launch-transfermarkt-backfill-vm.sh` already exists
  ([`deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh`](../../../deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh))
  — singleton-locked (shared API key, ~1 req/sec pacing), accepts explicit historical date ranges, routes via
  `setup-data-pipeline-vm.sh` →
  `python -m instruments_service --operation instruments --mode batch --asset-group SPORTS --sports-provider TRANSFERMARKT --start-date ... --end-date ...`.
- **No new code** needed here. Just tarball refresh + fire.

### Track B — SFI `SFI_LEAGUES + SFI_PROGRESSIVE_STATS` backfill (new launcher + operator run + codex fix)

- Prod has `entity=sfi_leagues` partitions for 2019-01 only (same period as Transfermarkt). Zero 2020-2026 coverage.
- `launch-sfi-forward-poll.sh` exists but is forward-poll only (T-1 default; singleton-locked). **There is no backfill
  variant**.
- **Codex correction needed**: `codex/02-data/sports-scheduling-and-sharding.md` §2.4 currently declares `SFI_STANDINGS`
  as a fetched data_type. But
  [`instruments-service/instruments_service/engine/orchestrator.py`](../../../instruments-service/instruments_service/engine/orchestrator.py)
  L4365-4367 explicitly says "SFI has NO standings endpoint (confirmed from archived service). Standings come from API
  Football" and sets `_want_sfi_standings = False`. Codex §2.4 `SFI_STANDINGS` declaration is aspirational and
  contradicts the shipped code — it needs to be removed / corrected.
- **New launcher** `launch-sfi-backfill-vm.sh` needed — same shape as `launch-sfi-forward-poll.sh` but accepts explicit
  historical date ranges (like `launch-transfermarkt-backfill-vm.sh`), entity filter
  (`SFI_LEAGUES | SFI_PROGRESSIVE_STATS`), singleton-lock with `sfi-backfill-*` prefix distinct from `sfi-fwd-*`.

### Track C — Weather venue-id cross-ref (code + data-quality fix)

- Parent plan's 2024-09-01 dry-run: `weather_source='none'` for 100% of fixtures. Root cause: fixtures parquet's
  `venue_id` field is a numeric string (e.g. `'562'`) while weather parquet's `venue_id` is a textual canonical code
  (e.g. `'DE_LEUNEN'`).
- **Origin of both keys:**
  - Fixtures: raw API-Football `api_football.py` L124 writes `venue_id=vid` where `vid` is numeric. When a fixture is
    loaded via `features-sports-service`'s `gcs_reader._normalize_fixtures` L188-190, `venue_id` is forced to numeric
    via `pd.to_numeric(errors="coerce")` → `str(int(v))`. Canonical string venues become empty `""`.
  - Weather: OpenMeteo orchestrator at
    [`instruments-service/instruments_service/engine/orchestrator.py`](../../../instruments-service/instruments_service/engine/orchestrator.py)
    L4670-4680 reads fixtures' `venue.venue_id` dict-path. If fixtures carry canonical dicts at that moment, the weather
    parquet is keyed by canonical textual codes. This is inconsistent with what gets read downstream.
- **Venues reference (`day=all/entity=venues/venues.parquet`):** has columns
  `venue_id (numeric), name, city, country, capacity, surface, latitude, longitude, altitude` — uses NUMERIC ids
  (aligned with fixtures, not aligned with current weather parquet).
- **Fix options:**
  - **Option A (upstream):** normalise weather parquet key to use numeric `venue_id` matching fixtures + venues. One
    OpenMeteo write-path fix, plus a one-off rewrite of existing weather parquets to migrate old textual keys. Clean
    long-term SSOT.
  - **Option B (downstream helper):** features-sports-service `pipeline/fixture_features._lookup_weather` resolves
    numeric `venue_id` → canonical code via `venues.parquet` (numeric `venue_id` → `name` → `build_venue_id(name)`).
    Works without backfilling weather parquets; one extra join-hop at feature-compute time.
- **Recommendation:** Option B first (quick win, fixes the feature pipeline immediately). Track Option A as a cross-repo
  cleanup plan for later once Option B proves the mapping is correct.

### Blast radius

| Track | Repos touched                                                                                   | Code changes                                                                                                   | Operator runs                          |
| ----- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| A     | deployment-service (tarball) + instruments-store (VM target bucket)                             | 0 code — tarball refresh + VM fire                                                                             | 1 multi-year VM run                    |
| B     | deployment-service (new launcher) + unified-trading-pm (codex §2.4 fix)                         | New `launch-sfi-backfill-vm.sh` ~200 LoC (copy-adapt pattern from Transfermarkt launcher) + codex §2.4 rewrite | 1 multi-year VM run                    |
| C     | features-sports-service (pipeline/fixture_features.py) + unified-trading-pm (codex §9.1 update) | `_lookup_weather` venue-id resolution hop via venues DF + 3 unit tests                                         | 0 (dry-run verification on 2024-09-01) |

### Pre-audit manifest

| File / thing to find                                                                                  | Purpose                                                                                                   | Expected outcome                                                                                                        |
| ----------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh`                                   | Pattern reference for Track A fire + Track B new launcher.                                                | Singleton-lock + `setup-data-pipeline-vm.sh` routing + `--entity` filter; confirmed L1-50.                              |
| `deployment-service/scripts/vm/launch-sfi-forward-poll.sh`                                            | Pattern reference for Track B new launcher (shares SFI-specific metadata).                                | Singleton-lock + rate-limit guidance + provider token metadata; confirmed L1-40.                                        |
| `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`                                             | Check `VM_TASK=sports-forward-poll` handles the backfill payload too (or a new VM_TASK branch is needed). | Confirm in Phase 0 — if a dedicated branch is required for sfi-backfill vs sfi-forward-poll, extend setup script.       |
| `instruments-service/instruments_service/engine/orchestrator.py` L4365-4367                           | Confirm `_want_sfi_standings = False` comment on SFI endpoint reality.                                    | Codex §2.4 `SFI_STANDINGS` bullet contradicts shipped code — remove.                                                    |
| `instruments-service/instruments_service/reference_data/adapters/sports/adapters/open_meteo.py`       | Audit what `venue_id` key OpenMeteo writes (canonical vs numeric).                                        | Confirm the numeric-vs-textual mismatch origin; decide Track C Option A vs B.                                           |
| `features-sports-service/features_sports_service/data/gcs_reader.py` L188-190 (`_normalize_fixtures`) | Confirm the `pd.to_numeric` force that drops canonical string venue_ids.                                  | Extend fixture normalisation to keep both forms (numeric + text) until a migration reconciles the upstream write-paths. |
| `unified-api-contracts/unified_api_contracts/canonical/domain/sports/canonical_ids.py`                | Check `build_venue_id(name)` exists + its exact hash formula.                                             | Reuse for numeric→canonical mapping in `_lookup_weather` if Option B is chosen.                                         |

### Success criteria

Per-track:

- **Track A.** A Transfermarkt backfill VM successfully writes `player_values` partitions for the date range
  `2020-01-01 .. 2026-04-21` (approx 2350 daily shards). `gsutil ls` on a mid-range date (e.g. `day=2022-06-15`) returns
  a non-empty parquet. On success, re-run the parent plan's 2024-09-01 dry-run with `_load_transfermarkt_values`
  un-patched — `home_team_value_eur_as_of_kickoff` should populate for at least some EPL fixtures.
- **Track B.** `launch-sfi-backfill-vm.sh` shellcheck clean + dry-run with `--dry-run` flag prints the assembled
  metadata without firing. Singleton-lock refuses a second launch when `sfi-backfill-*` VM is RUNNING. Codex §2.4
  updated to match the shipped "no standings endpoint" reality. One live backfill run for 2020-01-01..2026-04-21
  populates `entity=sfi_leagues` + `entity=progressive_stats` daily.
- **Track C.** `features-sports-service/scripts/quality-gates.sh` green. New unit tests prove numeric venue_id resolves
  to canonical weather-row. Dry-run on 2024-09-01 shows `weather_source` ∈ `{actual, forecast_t0, forecast_t24h}` for at
  least some fixtures (not `'none'` across the board).

### Dependency graph

```
Phase 0 (audit — shared across tracks, already largely done in this PRE-AUDIT-FINDINGS section)
      │
      ├─► Track A: Transfermarkt backfill                        [PARALLEL]
      │       ├─ A.1 tarball refresh
      │       └─ A.2 fire VM + watchdog
      │
      ├─► Track B: SFI backfill launcher + codex fix            [PARALLEL]
      │       ├─ B.1 new launcher code
      │       ├─ B.2 setup-data-pipeline-vm.sh extension (if needed)
      │       ├─ B.3 codex §2.4 rewrite
      │       ├─ B.4 tarball refresh
      │       ├─ B.5 fire VM + watchdog
      │       └─ B.6 quickmerge deployment-service + PM
      │
      ├─► Track C: Weather venue-id cross-ref                    [PARALLEL]
      │       ├─ C.1 audit OpenMeteo write-path (determine Option A vs B)
      │       ├─ C.2 `_lookup_weather` venue-mapping hop (Option B)
      │       ├─ C.3 unit tests
      │       ├─ C.4 dry-run on 2024-09-01 against prod GCS
      │       ├─ C.5 codex §9.1 update (remove venue-id follow-up bullet)
      │       └─ C.6 quickmerge features-sports-service + PM
      │
      └─► Final: plan todos flipped + human unlock
```

Tracks A / B / C are entirely independent and can run in parallel (different repos, different dep graphs).

## Phases

### Phase 0: Pre-audit [SEQUENTIAL — do first, done in this section]

- [x] [AGENT] P0. Audit existing Transfermarkt + SFI launchers, orchestrator SFI-endpoint reality, OpenMeteo write-path,
      fixture venue_id normalisation, UAC `build_venue_id`. Findings embedded in this PRE-AUDIT-FINDINGS section.

### Track A — Transfermarkt backfill 2020-2026 [OPERATOR, PARALLEL]

- [x] [HUMAN] P1. Refresh SPORTS category tarball:
      `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS`.

- [x] [HUMAN] P1. Fire Transfermarkt backfill VM:
      `bash deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh --entity PLAYER_VALUES 2020-01-01 2026-04-21`.
      ETA: ~12-24h wall-clock on e2-standard-2 (rate-limited ~1 req/sec; ~2350 daily partitions × per-league fetch
      fan-out). Track via `gcloud logging read 'resource.labels.instance_id=<vm>' --limit 50 --format json` + events
      `ADAPTER_FETCH_*` / `TRANSFERMARKT_*`.

- [ ] [AGENT] P1. Post-backfill verification:
      `gsutil ls gs://instruments-store-sports-central-element-323112/sports_reference/by_date/day=2022-06-15/entity=player_values/`
      returns non-empty parquet. Re-run `compute_fixture_features("2024-09-01")` **without** the
      `_load_transfermarkt_values` patch from the parent plan's dry-run — `home_team_value_eur_as_of_kickoff` populates
      for at least some EPL fixtures (Transfermarkt covers EPL, non-EPL leagues may still NULL).

### Track B — SFI backfill launcher + codex fix [PARALLEL]

- [x] [AGENT] P1. Check `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` — does `VM_TASK=sports-forward-poll`
      already handle the SFI backfill invocation (same provider, same CLI args), or is a new `VM_TASK=sfi-backfill`
      branch needed? If the forward-poll path works for backfill too, skip to next item; else extend setup script.

- [x] [AGENT] P1. Create `deployment-service/scripts/vm/launch-sfi-backfill-vm.sh` by copy-adapting the Transfermarkt
      launcher pattern. Key differences: - Singleton-lock prefix `sfi-backfill-*` (distinct from `sfi-fwd-*`; both locks
      can coexist since they target different VM families but share the same SFI API key — actually: they must lock EACH
      OTHER since they share `soccer-football-info-api-key`; use `sfi-*` prefix for the lock check). - Provider token:
      `--sports-provider SOCCER_FOOTBALL_INFO`. - Entity filter: `--entity SFI_LEAGUES | SFI_PROGRESSIVE_STATS` (mirror
      the Transfermarkt flag name). - Default range: none (explicit start + end required — this is a backfill, not a
      rolling poll). - Header comment cites codex §2.4 for SFI_STANDINGS-is-absent reality.

- [x] [AGENT] P1. Update codex `unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md` §2.4: - Remove
      `SFI_STANDINGS` from the `Fetches:` list. - Add a one-line note: "SFI has no standings endpoint. Pre-match league
      position comes from API-Football `STANDINGS` (see §2.1). This is enforced by
      `instruments-service.engine.orchestrator.py` L4365-4367." - Remove the `Denormalisation to fixture` bullet's
      reference to SFI standings; redirect to the API-Football proxy.

- [x] [HUMAN] P1. Refresh SPORTS category tarball post-launcher-merge:
      `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS`.

- [x] [HUMAN] P1. Fire SFI backfill VM:
      `bash deployment-service/scripts/vm/launch-sfi-backfill-vm.sh 2020-01-01 2026-04-21`. ETA: ~12-24h. Track via
      `gcloud logging` + `ADAPTER_FETCH_*` / `SFI_*` events.

- [ ] [AGENT] P1. Post-backfill verification: `gsutil ls ...day=2022-06-15/entity=sfi_leagues/` non-empty.
      `instruments-service` data-status drilldown UI shows the new coverage. No rebuild of features-sports-service
      needed — new SFI coverage flows transparently through `derived_features_exporter`'s progressive-stats calculator.

- [x] [AGENT] P0. Quickmerge deployment-service (new launcher) + PM (codex §2.4 rewrite).

### Track C — Weather venue-id cross-ref [PARALLEL]

- [x] [AGENT] P0. Audit OpenMeteo adapter to confirm what `venue_id` representation it emits. If OpenMeteo writes
      canonical textual codes (`DE_LEUNEN`) while `venues.parquet` writes numeric (`562`), document the mismatch in this
      plan before coding.

- [x] [AGENT] P0. Implement Option B (downstream resolution hop): in
      [`features-sports-service/features_sports_service/pipeline/fixture_features.py`](../../../features-sports-service/features_sports_service/pipeline/fixture_features.py)
      `_lookup_weather`, accept an optional `venues: pd.DataFrame` param; when fixture `venue_id='562'` fails to find a
      weather row, fall back to resolving `venues[venues.venue_id == '562'].name.iloc[0]` → `build_venue_id(name)` →
      look up weather by that canonical code. If either hop fails, return `_empty_weather()` as today.

- [x] [AGENT] P0. Unit tests in `tests/unit/test_fixture_features_pipeline.py` (extend existing file): -
      `test_weather_venue_id_resolved_via_venues_mapping_when_raw_numeric_id_not_in_weather_parquet` — fixture
      `venue_id='562'`, weather has only `'DE_LEUNEN'`, venues df maps `562 → "De Leunen"`, UAC `build_venue_id`
      produces `'DE_LEUNEN'` → weather row picked up. -
      `test_weather_venue_id_fallback_yields_empty_when_no_canonical_match` — numeric id maps to a name that
      `build_venue_id` yields a textual code NOT in weather → `weather_source='none'`.

- [x] [AGENT] P0. Dry-run on 2024-09-01 against prod GCS: `weather_source` ∈ `{actual, forecast_t0, forecast_t24h}` for
      ≥1 EPL fixture. Log `weather_source` coverage summary.

- [x] [AGENT] P0. Update codex `unified-trading-pm/codex/02-data/sports-scheduling-and-sharding.md` §9.1 — remove the
      `Weather venue-id cross-ref` out-of-scope bullet; add a §9.3 note documenting the Option B resolution hop + the
      recommendation to eventually migrate weather parquet to numeric keys (Option A follow-up).

- [x] [AGENT] P0. `bash features-sports-service/scripts/quality-gates.sh` green.

- [x] [AGENT] P0. Commit + push features-sports-service (code) + PM (codex + plan flip).

### Final

- [ ] [HUMAN] P0. Approve unlock of this plan (`[unlock-plan]` commit removing `locked_by`/`locked_since`) once all
      tracks reach their success criteria. Note: Track A + Track B operator runs take 12-24h each and span multiple
      sessions; the HUMAN unlock can be requested once Track C + Track B launcher code + codex fixes are shipped and the
      operator VMs are in-flight.

## Parallelisation

- Tracks A, B, C are fully independent — different repos, different dep graphs, different operator vs code work.
- Within Track B, the launcher + codex update + `setup-data-pipeline-vm.sh` audit can be done in one agent pass; tarball
  refresh + VM fire are operator-sequential.
- Within Track C, the OpenMeteo audit (Phase 0 C.1) determines the implementation path; C.2-C.6 are sequential within
  Track C.

## SSOT cross-refs

- Parent plans: `features_sports_denormalisation_pipeline_2026_04_21` (shipped),
  `features_sports_derived_data_crime_fixes_2026_04_21` (shipped).
- Launcher pattern: `launch-transfermarkt-backfill-vm.sh` (reference).
- SFI endpoint reality: `instruments-service/engine/orchestrator.py` L4365-4367 comment + `_want_sfi_standings = False`.
- Canonical venue ids: `unified-api-contracts/unified_api_contracts/canonical/domain/sports/canonical_ids.py`
  `build_venue_id`.
- Tarball refresh SSOT: `deployment-service/scripts/vm/create-code-tarballs.sh` (`--asset-group SPORTS` flag).
- Singleton-lock pattern: `launch-sfi-forward-poll.sh` + `launch-transfermarkt-backfill-vm.sh` +
  `launch-mtds-prediction-backfill-vm.sh`.

## Out of scope

- Track C Option A (OpenMeteo upstream write-path migration to numeric `venue_id` + existing weather parquet rewrite) —
  file as a follow-up plan once Option B ships and proves the numeric→canonical mapping is correct.
- FootyStats / Understat backfills — covered by existing `launch-footystats-backfill-vm.sh` +
  `launch-understat-backfill-vm.sh`; neither is flagged as a gap today.
- Weather ERA5 historical backfill for 2018-2019 — mentioned in parent plan's "Out of scope" list; dedicated plan if
  needed.
