---
doc_type: codex-ssot
title: Sports Adapter Dependency Order — SSOT
summary:
  api-football is T0 (canonical fixtures_schedule/fixtures_outcomes/leagues/teams) for every sports date; T1 enrichment
  adapters (footystats/understat/transfermarkt/SFI/open-meteo/betfair) are INTENDED to read its GCS parquet via a
  factory-preflight DependencyError gate — that gate does not fire in production (date kwarg never passed by any real
  caller).
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
last_reviewed: 2026-07-23
code_refs:
---

# Sports Adapter Dependency Order — SSOT

> **Note (2026-07-19, body rewritten 2026-07-23).** This doc previously described the pre-split bare `entity=fixtures`
> shape and treated the T0/T1 pre-flight gate as an active safety net. Both are now fixed in place in §1/§3/§4.1/§5
> below — this banner is a pointer, not a restatement. Background:
> `plans/active/issues/ sports_t0_t1_dependency_gate_never_wired_2026_07_15.md`,
> `plans/active/sports_consolidated_closeout_2026_07_19.md` (ENTITY-SPLIT / Track E).

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

## 1. The invariant — api-football is T0 for every sports date (design intent; the gate does not enforce it)

**api-football is the canonical source of fixture IDs, league definitions, team rosters, and kickoff times for the
entire sports pipeline.** Every other sports adapter in instruments-service is an **enrichment** adapter that is
INTENDED to read api-football's canonical output from GCS to resolve its own per-fixture / per-league joins. That is the
design. What actually happens in production today is narrower — read the two caveats below before relying on anything
else in this section.

**Caveat 1 — fixtures entity is SPLIT; the bare entity is FROZEN.** The T0 api-football writer no longer writes a single
`entity=fixtures/` partition. Since **2026-05-23** (last real write to the bare entity, measured) it writes two entities
side by side, both under a `pipeline_mode=batch_api_football/` hive segment:

- `entity=fixtures_schedule/` — schedule fields (kickoff time, teams, round, venue_id, …) for every fixture, played or
  not.
- `entity=fixtures_outcomes/` — scores + status, populated once a fixture completes.

Bare `entity=fixtures/` (no `pipeline_mode=` segment, no split) is **FROZEN** — nothing has landed there since
2026-05-23. Any adapter, script, or doc still reading or writing bare `entity=fixtures/` is targeting a dead path.

**Caveat 2 — the pre-flight dependency gate in §4-§5 does NOT fire in production.** `check_api_football_dependency()`
only runs when the factory call site passes `date=`, and every real T1 call site (`footystats.py`, `transfermarkt.py`,
`understat.py`, `sfi.py`, plus `open_meteo`/`betfair`) constructs its adapter via
`create_sports_reference_adapter(venue)` — no `date=` kwarg — so the gate never executes. This is confirmed by live
data: Understat has captured rows for 2014-2017 dates where api-football has zero fixtures, which the gate would have
blocked had it fired. Treat the rest of this doc (including this section's own dependency graph) as the **intended
contract**, not a description of an active safety net. Fixing the gate is scoped as Track E of
`plans/active/sports_consolidated_closeout_2026_07_19.md` ("Wire the T0/T1 dependency gate for real") and tracked in
`plans/active/issues/sports_t0_t1_dependency_gate_never_wired_2026_07_15.md`.

### Dependency graph (intended — see caveats above)

```
                T0 (INTENDED to run FIRST for each date — not enforced, see caveat 2 above)
                      ┌────────────────────┐
                      │   api-football     │
                      │ (canonical fixtures│
                      │   + leagues + teams│
                      │    + schedules)    │
                      └──────────┬─────────┘
                                 │ writes (pipeline_mode=batch_api_football/)
                                 ▼
      sports_reference/by_date/day={date}/pipeline_mode=batch_api_football/
        entity=fixtures_schedule/...   (schedule incl. round — every fixture, played or not)
        entity=fixtures_outcomes/...   (scores + status — completed fixtures only)
        entity=leagues/leagues.parquet
        entity=teams/teams.parquet
        entity=standings/...
        entity=injuries/...
      [bare entity=fixtures/ — FROZEN 2026-05-23, do not target]
                                 │
          ┌──────┬──────┬────────┼────────┬──────┬──────┐
          │      │      │        │        │      │      │
          ▼      ▼      ▼        ▼        ▼      ▼      ▼
        T1 (any order, parallel-safe — INTENDED to run only AFTER T0 lands for the
            date; nothing in production actually enforces this ordering, see caveat 2)
        ┌──────┐ ┌──────────┐ ┌────────┐ ┌─────────────┐ ┌──────┐ ┌──────┐
        │footy-│ │understat │ │trans-  │ │soccer_foot- │ │open_ │ │bet-  │
        │stats │ │(xG)      │ │fermarkt│ │ball_info    │ │meteo │ │fair  │
        │      │ │          │ │(player │ │(SFI         │ │(wx)  │ │(odds)│
        │      │ │          │ │ values)│ │ leagues +   │ │      │ │      │
        │      │ │          │ │        │ │ standings)  │ │      │ │      │
        └──────┘ └──────────┘ └────────┘ └─────────────┘ └──────┘ └──────┘
```

### Why each T1 adapter is intended to depend on api-football

Each enrichment adapter is INTENDED to read
`sports_reference/by_date/day={date}/pipeline_mode=batch_api_football/entity=fixtures_schedule/...` (the split schedule
entity — `entity=fixtures_outcomes/` too, wherever it needs scores/status) at the start of its fetch to resolve one or
more of:

- **FootyStats** — joins its `home_team` / `away_team` string columns on canonical fixture IDs (`build_fixture_id(...)`
  in `unified_api_contracts.sports`) to deduplicate against api-football's `af_fixture_id`. Without api-football
  fixtures, FootyStats rows can't be joined downstream.
- **Understat** — resolves per-match xG rows to canonical fixture_ids by date + teams. Without api-football fixtures,
  Understat output has no fixture_id column and downstream features can't join.
- **Transfermarkt** — resolves player-value snapshots to teams that api-football has already fetched. Transfermarkt's
  league triggers (`get_leagues_needing_refresh`) work standalone but its team-level joins require api-football's team
  IDs.
- **SoccerFootball.info (SFI)** — league standings + progressive stats are keyed on api-football's league_id.
- **Open-Meteo** — the weather adapter is intended to read `entity=fixtures_schedule/` to extract the `venue_id` list
  (and thence lat/long) before hitting the Open-Meteo API. Without fixtures, no weather is produced.
- **Betfair** — exchange odds rows are joined on canonical fixture IDs for feature calculation.

### What "T0 first" does NOT mean

- It does NOT mean api-football is a blocker for the entire run — each enrichment adapter can be re-run idempotently
  once api-football catches up.
- It does NOT mean the adapters import api-football as Python code. The dependency is on the GCS parquet artefacts, not
  on the adapter class.
- It does NOT apply to **per-venue shard-level failures inside the shard loop**. That is governed by
  `codex/04-architecture/shard-level-failure-isolation.md`. This doc governs only the **pre-flight gate** — and, per
  caveat 2 above, that gate does not actually run in production, so there is currently no enforcement point BEFORE the
  shard loop starts either. §4-§5 spell this out in detail.

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

Each adapter writes to one or more `entity=` partitions under
`sports_reference/by_date/day={date}/pipeline_mode=batch_api_football/` (api-football's own entities carry the
`pipeline_mode=` segment; T1 adapters write their own entities alongside it). Cross-reference:
`codex/02-data/per-asset-group-bucket-layouts.md` § "instruments-service writes — SPORTS".

**The "Reads (dep)" column is the INTENDED join dependency, not an enforced one** — §1 (caveat 2) and §4-§5 explain why
the factory pre-flight that is supposed to guarantee it never actually fires in production.

| Adapter                       | Writes entity partitions                                                                                                                                                                                                                  | Reads (dep) — intended, not gate-enforced       |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **api_football (T0)**         | `entity=fixtures_schedule` `entity=fixtures_outcomes` `entity=leagues` `entity=teams` `entity=standings` `entity=injuries` `entity=lineups` `entity=fixture_stats` — bare `entity=fixtures` is FROZEN since 2026-05-23, never write there | — (root of the tree)                            |
| **footystats (T1)**           | `entity=footystats_matches` `entity=footystats_odds` `entity=footystats_predictions`                                                                                                                                                      | `entity=fixtures_schedule/`                     |
| **understat (T1)**            | `entity=understat_xg`                                                                                                                                                                                                                     | `entity=fixtures_schedule/`                     |
| **transfermarkt (T1)**        | `entity=transfermarkt_leagues` `entity=transfermarkt_teams`                                                                                                                                                                               | `entity=teams/teams.parquet` (api-football)     |
| **soccer_football_info (T1)** | `entity=sfi_leagues` `entity=sfi_standings` `entity=progressive_stats`                                                                                                                                                                    | `entity=leagues/leagues.parquet` (api-football) |
| **open_meteo (T1)**           | `entity=weather`                                                                                                                                                                                                                          | `entity=fixtures_schedule/` (venue_id column)   |
| **betfair (T1)**              | `entity=betfair_odds`                                                                                                                                                                                                                     | `entity=fixtures_schedule/`                     |

**Test-mode variants** write to the same entity paths inside the `-test-` suffixed bucket
(`instruments-store-sports-prd-{project_id}-test`). Whichever bucket `IS_TEST_RUN` resolves to is where the (rarely
invoked) pre-flight probe would read from too — it does not duplicate data between prod and test.

---

## 4. Failure modes

### 4.1 api-football entirely missing for date `D`

**In production, neither branch below fires the way it was designed to** — see §1 caveat 2. Downstream T1 adapters:

- **If called via `create_sports_reference_adapter(venue, date=D, ...)`**: factory raises
  `unified_trading_library.DependencyError` with the actionable remediation message below. The adapter is never
  instantiated. **This is the branch every real T1 call site would need to hit for the gate to do anything — none of
  them do.**
- **If called via `create_sports_reference_adapter(venue)` without `date`**: no pre-flight fires. This is NOT a rare
  "legacy callers" fallback path as originally documented — grep across `footystats.py`, `transfermarkt.py`,
  `understat.py`, `sfi.py`, `open_meteo`, and `betfair` shows this is the ONLY path every real production call site
  uses. The adapter is always instantiated, whether or not api-football has landed for the date, and there is no other
  pre-flight stage upstream that gates it either.

Net effect: when api-football is missing for date `D`, T1 adapters run anyway today and silently produce zero rows — the
exact silent-failure mode this module's own docstring says the gate was built to replace. Fixing this is Track E of
`plans/active/sports_consolidated_closeout_2026_07_19.md` ("Wire the T0/T1 dependency gate for real").

The error message format the gate _would_ emit if a caller ever passed `date=` (see `_build_remediation_message`) — note
it still names the FROZEN bare `entity=fixtures` path, a separate staleness in the message template itself, tracked in
the same Track E item:

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

## 5. Implementation — fail-loud boundary (as designed; NOT what runs in production)

The dependency gate is implemented as a pre-flight check at the **factory entry point**, not inside the per-venue shard
loop. As designed, this would be the ONE place in the sports pipeline where raising `DependencyError` is correct
behaviour. **As deployed, it is a known-broken safety net, not a working one** — `check_api_football_dependency()` only
executes when the factory call site passes `date=`, and grep across every real T1 call site confirms none of them do (§1
caveat 2, §4.1). Read the two bullets below as the intended design, then apply the caveat that follows.

- Shard-level isolation (`codex/04-architecture/shard-level-failure-isolation.md`): inside the shard loop, all errors
  are caught per-shard and logged as `VENUE_PROCESSING_FAILED` events. No `raise`. This part IS live in production and
  unaffected by the gate's dead-code status — it keeps a bad shard from killing the whole day's run.
- **Pre-flight** (this doc, as designed): BEFORE the shard loop starts, if api-football is missing for the whole date,
  fail loud — because every T1 shard would otherwise fail silently, corrupting the manifest's `capture_status`
  semantics. A single loud `DependencyError` is cheaper to diagnose than N silent `empty_confirmed` rows that are
  actually "dep was missing". **In production this never triggers**: no `date=` reaches the factory, so T1 shards run
  against a missing dependency and produce exactly the silent-failure outcome this bullet describes as prevented.

The gate's storage-probe fallback — if the probe itself fails (transport error, auth failure), raise `DependencyError`
rather than leak the underlying exception — is still correct behaviour on the rare occasions the gate IS invoked with a
`date` (unit tests, ad hoc scripts). It has no bearing on the production call path, where the gate is never invoked at
all.

**Do not cite this section as evidence the sports pipeline is protected against a missing api-football day — it is
not**, until Track E of `plans/active/sports_consolidated_closeout_2026_07_19.md` ("Wire the T0/T1 dependency gate for
real") lands.

---

## 6. When to update this doc

- Adding a new sports adapter → add a row to §3 and add the venue key to `_API_FOOTBALL_DEPENDENT_VENUES` in
  `sports_dependency.py`.
- Replacing api-football with a different canonical fixtures source → this doc needs a rewrite, not a patch. Cross-ref
  the migration plan from `plans/active/`.
- Changing the sports bucket naming convention → update §1 diagram and §4.4 test-bucket-divergence section.
- New entity partition introduced under `sports_reference/by_date/` → add to §3 matrix AND to
  `codex/02-data/per-asset-group-bucket-layouts.md`.
