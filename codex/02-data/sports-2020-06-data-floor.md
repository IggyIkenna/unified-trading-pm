---
doc_type: codex-ssot
title: The 2020-06 sports data floor (odds start 2020-06-06; pre-floor is fabrication-by-construction)
summary: >-
  Operator ruling 2026-07-21: sports ODDS tick data starts 2020-06-06 (measured: the tick bucket has ZERO day-partitions
  before it), so 2020-06 is the base month for ALL sports honest-coverage denominators, MDPS candle derivation, features
  computation, and fixture EXPECTATIONS. Nothing downstream is legitimately computable without odds, so every sports
  artifact dated before 2020-06-06 is fabrication-by-construction and is WIPED from GCS + manifest (delete, do not
  backfill). This doc is the SSOT for the floor date, its rationale, and the enforcement surface every producer/consumer
  must clamp to.
status: current
nature: ssot
asset_group: [sports]
stage: [data]
repos:
  [
    unified-api-contracts,
    instruments-service,
    market-data-processing-service,
    features-service,
    deployment-service,
    deployment-api,
  ]
scope: [engineer, admin]
tags: [sports, data-floor, honest-coverage, fabrication, wipe, coverage-denominator, fixture-expectation, hard-rule]
related:
  [
    availability-manifest-and-data-status.md,
    honest-coverage-model.md,
    honest-absence-downstream-handling.md,
    gcs-and-manifest-delete-safety-protocol.md,
    ../../plans/active/sports_master_closeout_2026_07_21.md,
  ]
created: 2026-07-21
authoritative_for:
  [
    the 2020-06 sports data floor date,
    pre-floor sports data is fabrication-by-construction,
    the sports floor enforcement surface,
  ]
referenced_by:
owner:
last_reviewed: 2026-07-21
code_refs:
  [
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py,
    instruments-service/instruments_service/engine/validation_utils.py,
    deployment-service/scripts/vm/launch-sports-entity-sweep-vm.sh,
  ]
---

# The 2020-06 sports data floor

## The ruling (operator, 2026-07-21 — authoritative)

**Sports ODDS tick data starts 2020-06-06.** Measured: the odds tick bucket
`market-data-tick-sports-prd-central-element-323112` has **ZERO day-partitions before 2020-06-06** (1,942 from
2020-06-06 on). The operator ruled that **2020-06 is the base month for ALL sports data** — honest-coverage
denominators, MDPS candle derivation, features/`derived_features` computation, and fixture EXPECTATIONS all start here.

Odds are the spine of every sports strategy; without odds, nothing downstream (candles, features, labels, fixture
expectations) is legitimately computable. Therefore **every sports artifact dated before 2020-06-06 is
fabrication-by-construction** — a `derived_features` parquet computed for a day with no odds is a fabricated row, not a
gap. The honest resolution is to **DELETE pre-floor sports data from GCS + manifest — not backfill it**. This is the
authoritative resolution of the "fabricated `derived_features` / re-run couldn't compute 2018-2020" findings.

> This ruling **supersedes** the 2026-07-15 UAC coverage-floor amendment that set footystats / transfermarkt /
> open_meteo floors back to 2018-01-01. That amendment was reverted (`unified-api-contracts@8cdf7808`); all sports
> `SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` floors are clamped to `date(2020, 6, 6)`.

## The floor date

`SPORTS_DATA_FLOOR = 2020-06-06` (inclusive). The SSOT constant lives in UAC `canonical/domain/sports/league_data.py`
(`SOURCE_COVERAGE_START`, all sports sources clamped to `date(2020, 6, 6)`); `clip_dates_to_source_coverage` returns an
empty-window signal for a request that ends before the floor.

## Enforcement surface (every place the floor is clamped)

A producer or consumer that does NOT clamp to the floor re-introduces fabrication. The floor is applied at:

1. **UAC coverage-floor SSOT** — `SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` for every sports source =
   `date(2020, 6, 6)`. This is the one SSOT; the sites below either read it or are clamped to match it.
2. **Coverage denominators / honest coverage** — `enumerate_expected_universe.py` seeds
   `EXPECTED_PRE_SOURCE_COVERAGE_START` for dates below the floor (never a real expected cell); the data-status
   denominators (deployment-api `data_status/*`) read the same UAC floor.
3. **Fixture-expectation gates** — the fixture-calendar gate + `EXPECTED_NO_FIXTURE` seeding must never materialise
   expected rows for pre-floor alive-days.
4. **MDPS / features compute start-date** — candle derivation + `derived_features` / `fixture_features` compute start
   clamped to the floor.
5. **Manifest `expected_unattempted` (WRITER-materialised)** — the enumerator / expectation seeder must not materialise
   expected rows for pre-floor dates.
6. **Backfill launcher `START_DATE` defaults** — every sports launcher clamps to 2020-06-06:
   `launch-sports-entity-sweep-vm.sh` (api_football + enrichment sweeps), `launch-sports-instruments-reference-vm.sh`
   (entirely-pre-floor windows removed), `launch-mdps-backfill-vm.sh` (sports default). A running backfill from a
   pre-floor start re-fabricates.
7. **Venue-epoch skip gate** — `instruments-service/.../validation_utils.py::get_venue_epoch` clamps `api_football` /
   `soccerfootball_info` / `footystats` epochs to 2020-06-06 (defence-in-depth: a pre-floor date is skipped even if a
   launcher passes one).
8. **Data-status / catalogue UI** — denominators + the could-exist catalogue floored at 2020-06.

## The wipe (delete, do not backfill)

Pre-floor sports objects + manifest rows are deleted under the
[GCS + manifest delete-safety protocol](gcs-and-manifest-delete-safety-protocol.md). This is a **specific
operator-authorised delete campaign** ("data before this can just be wiped out from gcs and manifest to keep things
honest", 2026-07-21) — the day-partition (`day=<D>` with `D < 2020-06-06`) is the delete scope, parsed from the object
PATH (not `time_created`, which is `None` via the UTL list client). `features-sports-prd` has GCS soft-delete (7d) as
the recovery net; `instruments-store-sports-prd` has soft-delete=0, so its wipe is scoped to the day-partitioned
`by_date/` fabrication subtree only (the current-state reference registries — `teams_in_league/`, `mappings/`,
`master/`, `standings/` — are NOT per-day fabrication and are left untouched). Every delete pass ends with a GCS-walk
manifest rebuild (`deployment-service/scripts/rebuild_sports_manifest.py`) so no phantom pre-floor rows survive.

## What is MOOT after the floor

Any plan/track that backfills sports history before 2020-06 is moot — the 2015→present `derived_features` backfill, the
api-football 2015→2020-06 reference expansion, and the 2017/2018 fabricated-corpus remediation are all inside the wipe's
blast radius. Only the 2020-06→present slice is legitimate work.
