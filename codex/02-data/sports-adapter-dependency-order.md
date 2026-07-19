---
doc_type: codex-ssot
title: Sports Adapter Dependency Order — SSOT
summary:
  api-football is T0 (canonical fixtures/leagues/teams) for every sports date; T1 enrichment adapters
  (footystats/understat/transfermarkt/SFI/open-meteo/betfair) read its GCS parquet, gated by a factory-preflight
  DependencyError.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [sports, instruments, backfill, footystats, data-correctness, orchestrator]
related:
  [
    codex/02-data/sports-data-source-coverage-matrix.md,
    codex/02-data/sports-scheduling-and-sharding.md,
    codex/02-data/per-asset-group-bucket-layouts.md,
    codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-04-20
authoritative_for: [sports adapter T0/T1 run-order dependency, api-football pre-flight DependencyError gate]
referenced_by:
  [
    codex/02-data/sports-data-source-coverage-matrix.md,
    codex/02-data/sports-gcs-path-ssot.md,
    codex/02-data/sports-scheduling-and-sharding.md,
    codex/15-runbooks/backfill-completion-playbook.md,
    codex/15-runbooks/smoke-testing-playbook.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Sports Adapter Dependency Order — SSOT

> **⚠️ CORRECTION (2026-07-19) — two live drifts in this doc.** (1) **Entity split**: the T0 api-football writer and
> every T1 reader now use `entity=fixtures_schedule` (+ `entity=fixtures_outcomes` for scores/status) under
> `pipeline_mode=batch_api_football/`, NOT the bare `entity=fixtures` this doc's §1/§3 still show — the bare entity is
> FROZEN (last real write 2026-05-23, measured). (2) **The §5 fail-loud dependency gate is UNREACHABLE in production**:
> `check_api_football_dependency()` only fires `if date is not None`, and grep-verified that every real T1 call site
> (`footystats.py`, `transfermarkt.py`, `understat.py`, `sfi.py`) omits `date=` — confirmed by live data (understat has
> captured rows 2014-2017 where api-football has zero fixtures, impossible if the gate fired). See
> `plans/active/issues/sports_t0_t1_dependency_gate_never_wired_2026_07_15.md` +
> `plans/active/sports_consolidated_closeout_2026_07_19.md` (ENTITY-SPLIT / CODEX tracks).

**Purpose**: canonical reference for the run-order of sports reference-data adapters inside instruments-service. Written
2026-04-20 as part of Phase 3 of the `institutional_smoke_matrix_2026_04_20` plan after the SPORTS smoke incident
surfaced a silent dependency between the enrichment adapters and api-football's canonical fixtures output.

**Status**: canonical. Every operator launching a sports backfill or smoke run MUST consult this doc before scheduling
parallel shards. Every new sports adapter added to `instruments-service` MUST declare its upstream dependency in the
matrix below.

**Cross-references**:

- Per-asset-group bucket & path layouts: `codex/02-data/per-asset-group-bucket-layouts.md`
- Smoke matrix plan: `plans/archive/institutional_smoke_matrix_2026_04_20.plan.md` § Phase 3
- Availability manifest schema: `codex/02-data/availability-manifest-and-data-status.md`
- Shard-level failure isolation (shard-level, NOT pre-flight): `codex/04-architecture/shard-level-failure-isolation.md`
- Implementation: `instruments-service/instruments_service/reference_data/sports_dependency.py`
- Adapter factory: `instruments-service/instruments_service/reference_data/adapters/sports/factory.py`
- Test: `instruments-service/tests/unit/test_sports_dependency_enforcement.py`

---

## 1. The invariant — api-football is T0 for every sports date

**api-football is the canonical source of fixture IDs, league definitions, team rosters, and kickoff times for the
entire sports pipeline.** Every other sports adapter in instruments-service is an **enrichment** adapter that reads
api-football's canonical output from GCS to resolve its own per-fixture / per-league joins. Without api-football's
parquet in place for date `D`, none of the enrichment adapters can produce useful output — they either read empty
results silently (historical behaviour) or, as of this plan, fail loud with `unified_trading_library.DependencyError` at
the factory pre-flight.

### Dependency graph

```
                      T0 (MUST run FIRST for each date)
                      ┌────────────────────┐
                      │   api-football     │
                      │ (canonical fixtures│
                      │   + leagues + teams│
                      │    + schedules)    │
                      └──────────┬─────────┘
                                 │ writes
                                 ▼
      sports_reference/by_date/day={date}/
        entity=fixtures/fixtures.parquet
        entity=leagues/leagues.parquet
        entity=teams/teams.parquet
        entity=standings/...
        entity=injuries/...
                                 │
          ┌──────┬──────┬────────┼────────┬──────┬──────┐
          │      │      │        │        │      │      │
          ▼      ▼      ▼        ▼        ▼      ▼      ▼
        T1 (any order, parallel-safe AFTER T0 completes for the date)
        ┌──────┐ ┌──────────┐ ┌────────┐ ┌─────────────┐ ┌──────┐ ┌──────┐
        │footy-│ │understat │ │trans-  │ │soccer_foot- │ │open_ │ │bet-  │
        │stats │ │(xG)      │ │fermarkt│ │ball_info    │ │meteo │ │fair  │
        │      │ │          │ │(player │ │(SFI         │ │(wx)  │ │(odds)│
        │      │ │          │ │ values)│ │ leagues +   │ │      │ │      │
        │      │ │          │ │        │ │ standings)  │ │      │ │      │
        └──────┘ └──────────┘ └────────┘ └─────────────┘ └──────┘ └──────┘
```

### Why each T1 adapter depends on api-football

Each enrichment adapter in the orchestrator's `_enrichment_providers` short- circuit reads
`sports_reference/by_date/day={date}/entity=fixtures/fixtures.parquet` at the start of its fetch to resolve one or more
of:

- **FootyStats** — joins its `home_team` / `away_team` string columns on canonical fixture IDs (`build_fixture_id(...)`
  in `unified_api_contracts.sports`) to deduplicate against api-football's `af_fixture_id`. Without api-football
  fixtures, FootyStats rows can't be joined downstream.
- **Understat** — resolves per-match xG rows to canonical fixture_ids by date + teams. Without api-football fixtures,
  Understat output has no fixture_id column and downstream features can't join.
- **Transfermarkt** — resolves player-value snapshots to teams that api-football has already fetched. Transfermarkt's
  league triggers (`get_leagues_needing_refresh`) work standalone but its team-level joins require api-football's team
  IDs.
- **SoccerFootball.info (SFI)** — league standings + progressive stats are keyed on api-football's league_id.
- **Open-Meteo** — the weather adapter reads `entity=fixtures/fixtures.parquet` to extract the `venue_id` list (and
  thence lat/long) before hitting the Open-Meteo API. Without fixtures, no weather is produced.
- **Betfair** — exchange odds rows are joined on canonical fixture IDs for feature calculation.

### What "T0 first" does NOT mean

- It does NOT mean api-football is a blocker for the entire run — each enrichment adapter can be re-run idempotently
  once api-football catches up.
- It does NOT mean the adapters import api-football as Python code. The dependency is on the GCS parquet artefacts, not
  on the adapter class. The factory pre-flight reads GCS, not Python state.
- It does NOT apply to **per-venue shard-level failures inside the shard loop**. That is governed by
  `codex/04-architecture/shard-level-failure-isolation.md`. This doc governs only the **pre-flight gate** that runs
  BEFORE the shard loop starts.

---

## 2. Parallelisation after T0

Once api-football completes for date `D`, the T1 adapters are **mutually independent**. They can run concurrently
without ordering constraints between themselves. Typical orchestration:

```text
for date in date_range:
    run api-football(date)               # T0 — SEQUENTIAL per date
    wait for api-football(date) to land in GCS
    parallel:
        run footystats(date)
        run understat(date)
        run transfermarkt(date)
        run soccer_football_info(date)
        run open_meteo(date)
        run betfair(date)
```

**Smoke-matrix implication** (`institutional_smoke_matrix_2026_04_20` plan, Phase 4): the smoke orchestrator MUST
schedule api-football first per date and fan out the T1 adapters only after the api-football parquet is observable in
the `-test-` bucket. The smoke matrix script calls `create_sports_reference_adapter(venue, date=date, ...)` for every T1
venue; if the operator skips api-football, every T1 call surfaces a `DependencyError` with the exact CLI remediation to
run first.

**Production-backfill implication**: the same rule holds for real backfill runs. `launch-sfi-forward-poll.sh` and the
sports backfill launcher already schedule api-football first per date; this doc codifies the invariant so new launchers
inherit it.

---

## 3. Per-entity coverage matrix

Each adapter writes to one or more `entity=` partitions under `sports_reference/by_date/day={date}/`. Cross-reference:
`codex/02-data/per-asset-group-bucket-layouts.md` § "instruments-service writes — SPORTS".

| Adapter                       | Writes entity partitions                                                                                                       | Reads (dep)                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| **api_football (T0)**         | `entity=fixtures` `entity=leagues` `entity=teams` `entity=standings` `entity=injuries` `entity=lineups` `entity=fixture_stats` | — (root of the tree)                                 |
| **footystats (T1)**           | `entity=footystats_matches` `entity=footystats_odds` `entity=footystats_predictions`                                           | `entity=fixtures/fixtures.parquet`                   |
| **understat (T1)**            | `entity=understat_xg`                                                                                                          | `entity=fixtures/fixtures.parquet`                   |
| **transfermarkt (T1)**        | `entity=transfermarkt_leagues` `entity=transfermarkt_teams`                                                                    | `entity=teams/teams.parquet` (api-football)          |
| **soccer_football_info (T1)** | `entity=sfi_leagues` `entity=sfi_standings` `entity=progressive_stats`                                                         | `entity=leagues/leagues.parquet` (api-football)      |
| **open_meteo (T1)**           | `entity=weather`                                                                                                               | `entity=fixtures/fixtures.parquet` (venue_id column) |
| **betfair (T1)**              | `entity=betfair_odds`                                                                                                          | `entity=fixtures/fixtures.parquet`                   |

**Test-mode variants** write to the same entity paths inside the `-test-` suffixed bucket
(`instruments-store-sports-prd-{project_id}-test`). The factory pre-flight reads whichever bucket `IS_TEST_RUN` resolves
to — it does not duplicate data between prod and test.

---

## 4. Failure modes

### 4.1 api-football entirely missing for date `D`

Downstream T1 adapters:

- **If called via `create_sports_reference_adapter(venue, date=D, ...)`**: factory raises
  `unified_trading_library.DependencyError` with the actionable remediation message below. The adapter is never
  instantiated.
- **If called via `create_sports_reference_adapter(venue)` without `date`**: legacy callers (unit tests,
  reference-data-only dry runs) build the adapter. No pre-flight fires — the orchestrator is expected to gate the
  dependency at its own pre-flight stage before it has a date.

The error message format (see `_build_remediation_message`):

```text
api-football reference data missing for date 2026-04-14 in
instruments-store-sports-central-element-323112
(expected gs://instruments-store-sports-central-element-323112/
 sports_reference/by_date/day=2026-04-14/entity=fixtures/fixtures.parquet).
Run this first:
  python -m instruments_service --operation instruments --mode batch \
    --asset-group SPORTS --sports-provider API_FOOTBALL \
    --start-date 2026-04-14 --end-date 2026-04-14
```

### 4.2 api-football partially missing — league X has fixtures, league Y doesn't

api-football fetches fixtures for ALL registered leagues as a single shard per date (see `get_prediction_leagues()` in
UAC). The typical partial- failure shape is **all-or-nothing per date**: either the parquet lands with rows from every
league that had fixtures, or it doesn't land at all.

If a league has zero fixtures on date `D` (e.g. out-of-season):

- api-football writes an empty-but-schema-complete `fixtures.parquet` (or omits rows for that league). This is a
  legitimate zero-fixture day.
- T1 adapters iterate `fixtures.parquet`, find zero rows for league Y, and legitimately produce zero enrichment rows.
- Both api-football and T1 adapters record `capture_status=empty_confirmed` in the availability manifest — NOT
  `attempted_failed`. Smoke matrix treats `empty_confirmed` as PASS.

If api-football partially fails (API 5xx mid-fetch), the whole shard for that date is marked `attempted_failed` by
api-football's own error classification. The fixtures parquet MAY exist with a partial row set but will be reconciled on
the next scheduled re-run. T1 adapters launched against a partial-failure date will still find the partial parquet and
produce enrichment rows for the fixtures that were captured; downstream feature-service jobs must not trust counts until
api-football's shard hits `capture_status=captured`.

### 4.3 Graceful degradation

Enrichment adapters **do not** fail the shard when api-football fixtures are present but the specific row they need is
missing. E.g. FootyStats produces a row for a fixture that api-football didn't list — the downstream join drops it but
the shard succeeds. This is the correct "shard-level failure isolation" behaviour documented in the sibling codex doc.

The pre-flight `DependencyError` only fires when the **parquet file is entirely missing**, not when individual rows are
missing from it.

### 4.4 Test bucket divergence

A common operator confusion: running a smoke with `IS_TEST_RUN=true` when only the prod bucket has api-football data.
The pre-flight reads the `-test-` bucket and (correctly) raises `DependencyError` — the operator must run api-football
with `IS_TEST_RUN=true` first to populate the test bucket. Codified in smoke-matrix plan Phase 1
(`phase-1-dep-checker-test-mode`).

---

## 5. Implementation — fail-loud boundary

The dependency gate is implemented as a pre-flight check at the **factory entry point**, not inside the per-venue shard
loop. This is the ONE place in the sports pipeline where raising `DependencyError` is correct behaviour:

- Shard-level isolation (`codex/04-architecture/shard-level-failure-isolation.md`): inside the shard loop, all errors
  are caught per-shard and logged as `VENUE_PROCESSING_FAILED` events. No `raise`. This keeps a bad shard from killing
  the whole day's run.
- **Pre-flight** (this doc): BEFORE the shard loop starts, if api-football is missing for the whole date, fail loud —
  because every T1 shard would fail silently, corrupting the manifest's `capture_status` semantics. A single loud
  `DependencyError` is cheaper to diagnose than N silent `empty_confirmed` rows that are actually "dep was missing".

The gate is deliberately permissive in one way: if the storage probe itself fails (transport error, auth failure), the
gate still raises `DependencyError` rather than leaking the underlying exception. This keeps the error taxonomy
consistent for the caller: "either the dep is there, or the gate tells you what to run to make it there".

---

## 6. When to update this doc

- Adding a new sports adapter → add a row to §3 and add the venue key to `_API_FOOTBALL_DEPENDENT_VENUES` in
  `sports_dependency.py`.
- Replacing api-football with a different canonical fixtures source → this doc needs a rewrite, not a patch. Cross-ref
  the migration plan from `plans/active/`.
- Changing the sports bucket naming convention → update §1 diagram and §4.4 test-bucket-divergence section.
- New entity partition introduced under `sports_reference/by_date/` → add to §3 matrix AND to
  `codex/02-data/per-asset-group-bucket-layouts.md`.
