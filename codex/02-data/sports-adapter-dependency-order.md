---
doc_type: codex-ssot
title: Sports Adapter Dependency Order — SSOT
summary:
  api-football is T0 (canonical fixtures_schedule/fixtures_outcomes/leagues/teams) for every sports date; T1 enrichment
  adapters read its GCS parquet via a factory-preflight DependencyError gate. As of instruments-service@3c424e61
  (2026-07-28) the gate is WIRED and fires in production for the 4 implemented, dependent T1 adapters
  (footystats/understat/transfermarkt/soccer_football_info); open_meteo/betfair remain outside this factory path (see §1
  caveat 2).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: [sports, instruments, backfill, footystats, data-correctness, orchestrator]
related:
  [
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-04-20
authoritative_for: [sports adapter T0/T1 run-order dependency, api-football pre-flight DependencyError gate]
referenced_by:
  [
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/15-runbooks/backfill-completion-playbook.md,
    /codex/15-runbooks/smoke-testing-playbook.md,
  ]
owner:
last_reviewed: 2026-07-28
code_refs:
---

# Sports Adapter Dependency Order — SSOT

> **Note (2026-07-19, body rewritten 2026-07-23, gate-live update 2026-07-28).** This doc previously described the
> pre-split bare `entity=fixtures` shape and treated the T0/T1 pre-flight gate as an active safety net; the 2026-07-23
> rewrite corrected both to "intended but not enforced." **As of `instruments-service@3c424e61` (2026-07-28) the
> pre-flight gate IS wired and fires in production** for the 4 implemented dependent T1 adapters
> (footystats/understat/transfermarkt/soccer_football_info) — `date=`/`bucket=` are now threaded through every real call
> site, verified by `tests/unit/test_sports_t0_t1_gate_real_callers.py`. §1/§3/§4.1/§5 below are updated accordingly.
> Background: `/plans/archive/issues/sports_t0_t1_dependency_gate_never_wired_2026_07_15.md` (RESOLVED, archived),
> `/plans/active/sports_consolidated_native_ao_extract_2026_07_25.md` (Track E, where the fix landed).

**Purpose**: canonical reference for the run-order of sports reference-data adapters inside instruments-service. Written
2026-04-20 as part of Phase 3 of the `institutional_smoke_matrix_2026_04_20` plan after the SPORTS smoke incident
surfaced a silent dependency between the enrichment adapters and api-football's canonical fixtures output.

**Status**: canonical. Every operator launching a sports backfill or smoke run MUST consult this doc before scheduling
parallel shards. Every new sports adapter added to `instruments-service` MUST declare its upstream dependency in the
matrix below.

**Cross-references**:

- Per-asset-group bucket & path layouts: `/codex/02-data/per-asset-group-bucket-layouts.md`
- Smoke matrix plan: `plans/archive/institutional_smoke_matrix_2026_04_20.plan.md` § Phase 3
- Availability manifest schema: `/codex/02-data/availability-manifest-and-data-status.md`
- Shard-level failure isolation (shard-level, NOT pre-flight): `/codex/04-architecture/shard-level-failure-isolation.md`
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

**Caveat 2 — the pre-flight dependency gate in §4-§5 NOW fires in production, for the 4 implemented dependent T1
adapters (as of `instruments-service@3c424e61`, 2026-07-28).** `check_api_football_dependency()` runs when the factory
call site passes `date=`; every real T1 call site (`footystats.py` x3, `transfermarkt.py`, `understat.py`, `sfi.py`) — 5
call sites across the 4 implemented adapters — now constructs its adapter via
`create_sports_reference_adapter(venue, date=date, bucket=bucket)`, placed AFTER each function's own skip/guard checks
so the gate fires only when a fetch is actually about to be attempted (this is why it does NOT retroactively break
Understat's pre-2018 captures — those dates are already cached/complete and never reach the gate on a re-run). Verified
by `tests/unit/test_sports_t0_t1_gate_real_callers.py` (4 tests proving a real ordering violation raises
`DependencyError` from the actual orchestrator functions, not just the factory in isolation). Treat the rest of this doc
(including this section's own dependency graph) as **live production behaviour for footystats/understat/
transfermarkt/soccer_football_info**, not merely intended.

`open_meteo` and `betfair` remain OUTSIDE this factory path and are NOT gated: `open_meteo` is fetched via a separate
function (`weather.py::_fetch_weather_data`) that never calls `create_sports_reference_adapter`; `betfair` has no
adapter implementation in this repo at all (present only as a placeholder key in `_API_FOOTBALL_DEPENDENT_VENUES`, per
`sports_dependency.py`). Both were already out of scope for the fix (grep confirms neither had a real call site to
thread `date=` through) — this is pre-existing, unchanged by the fix, not a regression. Fixed via Track E of
`plans/active/sports_consolidated_native_ao_extract_2026_07_25.md` ("Wire the T0/T1 dependency gate for real"); source
issue archived at `/plans/archive/issues/sports_t0_t1_dependency_gate_never_wired_2026_07_15.md`.

### Dependency graph (gate-enforced for footystats/understat/transfermarkt/soccer_football_info — see caveats above)

```
                T0 (must run FIRST for each date — gate-enforced for the 4 implemented T1 adapters, see caveat 2 above)
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
        T1 (any order, parallel-safe — MUST run only AFTER T0 lands for the date;
            gate-enforced for footystats/understat/transfermarkt/soccer_football_info,
            NOT enforced for open_meteo/betfair — see caveat 2)
        ┌──────┐ ┌──────────┐ ┌────────┐ ┌─────────────┐ ┌──────┐ ┌──────┐
        │footy-│ │understat │ │trans-  │ │soccer_foot- │ │open_ │ │bet-  │
        │stats │ │(xG)      │ │fermarkt│ │ball_info    │ │meteo │ │fair  │
        │      │ │          │ │(player │ │(SFI         │ │(wx)  │ │(odds)│
        │      │ │          │ │ values)│ │ leagues +   │ │      │ │      │
        │      │ │          │ │        │ │ standings)  │ │      │ │      │
        └──────┘ └──────────┘ └────────┘ └─────────────┘ └──────┘ └──────┘
```

### Why each T1 adapter depends on api-football

Each enrichment adapter is intended (and, for the 4 implemented adapters, gate-enforced) to read
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
  `/codex/04-architecture/shard-level-failure-isolation.md`. This doc governs only the **pre-flight gate** — which, per
  caveat 2 above, now runs in production BEFORE the shard loop starts for footystats/understat/transfermarkt/
  soccer_football_info (not for open_meteo/betfair). §4-§5 spell this out in detail.

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
`/codex/02-data/per-asset-group-bucket-layouts.md` § "instruments-service writes — SPORTS".

**The "Reads (dep)" column is gate-enforced for footystats/understat/transfermarkt/soccer_football_info** (§1 caveat 2,
§4-§5) as of `instruments-service@3c424e61`; for **open_meteo/betfair it remains intended-only, not gate-enforced** —
neither has a real call site through the gated factory path (§1 caveat 2).

| Adapter                       | Writes entity partitions                                                                                                                                                                                                                  | Reads (dep)                                                                                                              |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **api_football (T0)**         | `entity=fixtures_schedule` `entity=fixtures_outcomes` `entity=leagues` `entity=teams` `entity=standings` `entity=injuries` `entity=lineups` `entity=fixture_stats` — bare `entity=fixtures` is FROZEN since 2026-05-23, never write there | — (root of the tree)                                                                                                     |
| **footystats (T1)**           | `entity=footystats_matches` `entity=footystats_odds` `entity=footystats_predictions`                                                                                                                                                      | `entity=fixtures_schedule/` — **gate-enforced**                                                                          |
| **understat (T1)**            | `entity=understat_xg`                                                                                                                                                                                                                     | `entity=fixtures_schedule/` — **gate-enforced**                                                                          |
| **transfermarkt (T1)**        | `entity=transfermarkt_leagues` `entity=transfermarkt_teams`                                                                                                                                                                               | `entity=teams/teams.parquet` (api-football) — **gate-enforced**                                                          |
| **soccer_football_info (T1)** | `entity=sfi_leagues` `entity=sfi_standings` `entity=progressive_stats`                                                                                                                                                                    | `entity=leagues/leagues.parquet` (api-football) — **gate-enforced**                                                      |
| **open_meteo (T1)**           | `entity=weather`                                                                                                                                                                                                                          | `entity=fixtures_schedule/` (venue_id column) — intended only, no gated call site (`weather.py` doesn't use the factory) |
| **betfair (T1)**              | `entity=betfair_odds`                                                                                                                                                                                                                     | `entity=fixtures_schedule/` — intended only, no adapter implementation exists yet                                        |

**Test-mode variants** write to the same entity paths inside the `-test-` suffixed bucket
(`instruments-store-sports-prd-{project_id}-test`). Whichever bucket `IS_TEST_RUN` resolves to is where the (rarely
invoked) pre-flight probe would read from too — it does not duplicate data between prod and test.

---

## 4. Failure modes

### 4.1 api-football entirely missing for date `D`

**As of `instruments-service@3c424e61` (2026-07-28), the first branch below is what actually happens in production for
footystats/understat/transfermarkt/soccer_football_info.** For open_meteo/betfair the second branch still applies (§1
caveat 2 — neither has a gated call site).

- **`create_sports_reference_adapter(venue, date=D, bucket=bucket)`** (the real call shape for the 4 implemented T1
  adapters, placed after each function's own skip/guard checks): factory raises
  `unified_trading_library.DependencyError` with the actionable remediation message below. The adapter is never
  instantiated. **This is now the live production path** for footystats/understat/transfermarkt/soccer_football_info —
  verified by `tests/unit/test_sports_t0_t1_gate_real_callers.py`.
- **`create_sports_reference_adapter(venue)` without `date`**: no pre-flight fires. This remains the ONLY path for
  open_meteo (fetched via a separate `weather.py` function that never calls the factory) and betfair (no adapter
  implementation exists).

Net effect: for footystats/understat/transfermarkt/soccer_football_info, api-football missing for date `D` now fails
loud with an actionable message BEFORE the shard loop starts — the silent-zero-rows failure mode this module's own
docstring describes is closed for these 4 adapters. For open_meteo/betfair it remains open (pre-existing, unchanged by
this fix — see §1 caveat 2 for why). Fixed via Track E of
`plans/active/sports_consolidated_native_ao_extract_2026_07_25.md` ("Wire the T0/T1 dependency gate for real").

The error message format the gate emits when it fires (see `_build_remediation_message`) — it still names the FROZEN
bare `entity=fixtures` path rather than the live split `entity=fixtures_schedule`, a cosmetic staleness in the message
template (the underlying PROBE already checks the split paths correctly, so this does not cause a false
`DependencyError` — only a stale-looking path in the message an operator sees when the dependency genuinely IS missing).
Tracked as its own P3 follow-up in `plans/active/sports_consolidated_native_ao_extract_2026_07_25.md` (Track E
follow-up):

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

## 5. Implementation — fail-loud boundary (live in production for footystats/understat/transfermarkt/soccer_football_info)

The dependency gate is implemented as a pre-flight check at the **factory entry point**, not inside the per-venue shard
loop — the ONE place in the sports pipeline where raising `DependencyError` is correct behaviour. **As of
`instruments-service@3c424e61` (2026-07-28), this is a working safety net for the 4 implemented dependent T1 adapters**
— `check_api_football_dependency()` now executes on every real call site for footystats/understat/
transfermarkt/soccer_football_info (§1 caveat 2, §4.1). It remains NOT wired for open_meteo (separate non-gated fetch
path) and betfair (no adapter implementation). Read the two bullets below as the live behaviour for the 4 gated
adapters.

- Shard-level isolation (`/codex/04-architecture/shard-level-failure-isolation.md`): inside the shard loop, all errors
  are caught per-shard and logged as `VENUE_PROCESSING_FAILED` events. No `raise`. This part IS live in production and
  is unaffected by (independent of) the pre-flight gate's own status — it keeps a bad shard from killing the whole day's
  run.
- **Pre-flight** (this doc): BEFORE the shard loop starts, if api-football is missing for the whole date, fail loud —
  because every T1 shard would otherwise fail silently, corrupting the manifest's `capture_status` semantics. A single
  loud `DependencyError` is cheaper to diagnose than N silent `empty_confirmed` rows that are actually "dep was
  missing". **This now triggers in production** for footystats/understat/transfermarkt/soccer_football_info, closing
  exactly the silent-failure gap this bullet describes.

The gate's storage-probe fallback — if the probe itself fails (transport error, auth failure), raise `DependencyError`
rather than leak the underlying exception — is correct behaviour whenever the gate is invoked with a `date` (now the
normal production call shape for the 4 gated adapters, as well as unit tests / ad hoc scripts). It has no bearing on
open_meteo/betfair, which never reach this factory path at all.

**This section now IS evidence the sports pipeline is protected against a missing api-football day, for
footystats/understat/transfermarkt/soccer_football_info** — verified by
`tests/unit/test_sports_t0_t1_gate_real_callers.py`. It is NOT evidence of protection for open_meteo/betfair (§1
caveat 2) — no fix is currently scoped for those two, since neither has a real gated call site to begin with.

---

## 6. When to update this doc

- Adding a new sports adapter → add a row to §3 and add the venue key to `_API_FOOTBALL_DEPENDENT_VENUES` in
  `sports_dependency.py`.
- Replacing api-football with a different canonical fixtures source → this doc needs a rewrite, not a patch. Cross-ref
  the migration plan from `plans/active/`.
- Changing the sports bucket naming convention → update §1 diagram and §4.4 test-bucket-divergence section.
- New entity partition introduced under `sports_reference/by_date/` → add to §3 matrix AND to
  `/codex/02-data/per-asset-group-bucket-layouts.md`.
