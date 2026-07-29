---
doc_type: issue
title: >-
  A generic Tardis batch-download path still attempts (and fails) LIGHTER-ZKSYNC trades every day, bypassing the
  already-declared VENUE_DATA_TYPE_NO_BATCH_SOURCE exclusion
summary: >-
  Discovered while backfilling mdps candles for HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET trades (2026-07-28/29
  campaign). UAC's `VENUE_DATA_TYPE_NO_BATCH_SOURCE["LIGHTER-ZKSYNC"] = frozenset({"trades", "book_snapshot_5"})` and
  the specific `_onchain_perp_batch_lighter.py`/`_onchain_perp_batch_live_only.py` handlers correctly exclude these
  combos from the batch expected/reachable universe (per the 2026-07-15 operator ruling documented in those handlers'
  docstrings: a "physically cannot be retrieved" combo should never be seeded, no `expected_unattempted`, no
  `empty_confirmed`). But the consolidated cefi manifest shows `market-tick-data-service` (pipeline_mode=`batch_tardis`)
  is STILL writing `attempted_failed`/`empty_confirmed` rows for `(LIGHTER-ZKSYNC, trades)` as recently as
  2026-07-28T17:26:59Z (same day as this doc) — 24,559 total rows for this combo (22,871 expected_unattempted, 1,661
  empty_confirmed, 26 attempted_failed, 1 captured), spanning dates back to 2026-02-20 and writes as recent as today.
  This is a DIFFERENT code path than the specific handlers already fixed for this venue (per
  `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`'s extensive fix history) — the generic `--operation
  download` Tardis orchestrator (the same one `_onchain_perp_batch_lighter.py`'s own docstring says it reuses for other
  Tardis-CeFi venues) appears to not check `venue_data_type_has_batch_source()` before attempting LIGHTER-ZKSYNC trades
  via Tardis, so it keeps trying and failing (or writing a typed empty row) every day, forever, for a combo that can
  never succeed.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags:
  [
    cefi,
    lighter-zksync,
    honest-coverage,
    no-batch-source,
    expected-universe,
    manifest-pollution,
    tardis,
    data-pipeline-correctness,
  ]
related:
  [
    /plans/active/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
    /plans/active/issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md,
  ]
created: 2026-07-29
parent_epic: cefi_master
priority: P2
estimate_class: research
assigned_role: data_engineering
source: >-
  Surfaced while verifying LIGHTER-ZKSYNC/EXTENDED-STARKNET trades batch coverage for the 2026-07-28/29 mdps-backfill-
  cefi campaign (15-VM parallel fleet, market-data-processing-service re-aggregating already-captured raw_tick_data into
  processed_candles). Read `unified_api_contracts/registry/market_data_categories.py:2275-2292`
  (`VENUE_DATA_TYPE_NO_BATCH_SOURCE`) and `market_tick_data_service/cli/handlers/_onchain_perp_batch_lighter.py`
  directly, then cross-checked against a live `read_availability_index()` read of the consolidated cefi manifest
  (read-only, no corpus walk).
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# Generic Tardis batch path still attempts LIGHTER-ZKSYNC trades despite the declared no-batch-source exclusion

> Investigation-only record (this doc). No code was changed while authoring this doc — `assigned_vm: NA`, a human
> decides when to pick this up.

## What I found

`unified_api_contracts/registry/market_data_categories.py:2275-2292` declares:

```python
VENUE_DATA_TYPE_NO_BATCH_SOURCE: dict[str, frozenset[str]] = {
    ...
    "LIGHTER-ZKSYNC": frozenset({"trades", "book_snapshot_5"}),
}
```

with the comment confirming LIGHTER-ZKSYNC's own REST is snapshot-only for both, and
`market_tick_data_service/cli/handlers/_onchain_perp_batch_lighter.py` (the venue's specific batch handler) correctly
honors this — its docstring documents the 2026-07-15 operator ruling that a "physically cannot be retrieved" combo must
never even be seeded into the batch expected/reachable universe (no `expected_unattempted`, no `empty_confirmed` row,
full stop) — reading UAC's registry via `enumerate_expected_universe.py`'s `_row_data_types`.

**But the consolidated cefi manifest contradicts this in practice.** A direct `read_availability_index()` read
(2026-07-29) shows:

```
LIGHTER-ZKSYNC trades: 24,559 rows
  expected_unattempted   22,871
  empty_confirmed         1,661
  attempted_failed           26
  captured                    1
```

with `written_at` spanning **2026-02-20 through 2026-07-28T17:26:59Z** — i.e. rows are still being written TODAY, well
after the 2026-07-15 ruling that should have stopped this entirely. Filtering to just today's writes:

```
60 rows written 2026-07-28 (today):
  empty_confirmed   pipeline_mode=batch_tardis   service_name=market-tick-data-service   50
  attempted_failed  pipeline_mode=batch_tardis   service_name=market-tick-data-service    9
  captured          pipeline_mode=batch_tardis   service_name=market-data-processing-service  1
```

The writer is `market-tick-data-service` via `pipeline_mode=batch_tardis` — this is NOT the specific
`_onchain_perp_batch_lighter.py`/`_onchain_perp_batch_live_only.py` handlers (which correctly exclude this combo), but a
DIFFERENT, more generic Tardis-download code path. `_onchain_perp_batch_lighter.py`'s own docstring names this path
explicitly: "the SAME production-proven Tardis call the generic `--operation download` orchestrator already uses for
other Tardis-CeFi venues" — strongly suggesting that generic orchestrator does not call
`venue_data_type_has_batch_source()` (or equivalent) before attempting `(LIGHTER-ZKSYNC, trades)`, so it keeps trying
(and failing, or writing a typed empty row) on every scheduled run, indefinitely, for a combo that can never resolve to
real data.

**Consequence**: the "honest coverage" denominator for this cell is permanently polluted — `expected_unattempted` rows
for a structurally-impossible combo can never transition to `captured`, so any consumer trusting this cell's coverage
percentage sees a permanent, unclosable gap that isn't really a gap at all (per the operator's own 2026-07-15 ruling,
this cell shouldn't even be IN the denominator).

## Root cause (confirmed 2026-07-29)

The generic path is `market_tick_data_service/engine/orchestrator/venue_fetch.py::_process_venue`, which resolves a
venue's per-run data_types via UAC's `get_expected_data_types_for_venue(venue)`. That function reads
`VENUE_DATA_TYPE_CAPABILITIES` (the venue's full declared capability list, any transport) and — prior to this fix —
never cross-checked `VENUE_DATA_TYPE_NO_BATCH_SOURCE`/`venue_data_type_has_batch_source()` at all. That check existed in
the codebase (used correctly by the specific `_onchain_perp_batch_live_only.py` handler), but
`get_expected_data_types_for_venue()` had no way to know a caller wanted the batch-reachable subset only — it always
returned the full capability list. A corpus-wide grep confirmed 13 real call sites (5 MTDS, 6 deployment-api, 2
internal-to-UAC) and zero in
agent-orchestrator/deployment-service/execution-service/strategy-service/unified-trading-library/features-sports-service,
so the fix scope was fully bounded.

- Whether the 1 `captured` row (from `market-data-processing-service`, not MTDS) for this combo is a benign anomaly —
  not re-investigated; MDPS candle-aggregates from whatever raw ticks exist regardless of whether the combo is
  batch-sourced, so a single stray captured row from an MDPS re-aggregation pass is not evidence of a live batch fetch
  succeeding, and isn't concerning enough to block this fix.

## Todos

- [x] [FIX] P2. Find the generic `--operation download` Tardis orchestrator and add a
      `venue_data_type_has_batch_source()` (or equivalent UAC registry) check before it attempts
      `(LIGHTER-ZKSYNC, trades)` — matching the exclusion the venue-specific handlers already correctly apply. Repo:
      market-tick-data-service. **DONE** — added a keyword-only `for_batch: bool = False` parameter to UAC's
      `get_expected_data_types_for_venue()` (default `False` preserves byte-identical behavior for the other 11 call
      sites); when `True`, filters the returned list through the existing `venue_data_type_has_batch_source()`. Wired
      `for_batch=True` into the 2 confirmed-buggy call sites inside `venue_fetch.py::_process_venue` (both the
      CLI-filter-absent default-resolution branch and the CLI-filter-present UAC-validation branch).
      `unified-api-contracts@d4045838` (4 new tests in `TestGetExpectedDataTypesForVenueForBatch`, full
      `quality-gates.sh` green — 6 pre-existing failures in that run are unrelated, from a concurrent session's
      in-flight FRED/ECB/OFR source-priority work, confirmed via standalone re-run showing they reference
      `("tradfi", "yield_curve"/"ohlcv_1d"/"cds_spread")`, not this change). `market-tick-data-service@6365f05f` (full
      `quality-gates.sh` green, 2109s — resource-drift warning only, from shared-host QG-governor queue contention, not
      a regression; sentinel written). File is at the repo's 900-line `MAX_FILE_LINES` cap; the fix was scoped to a
      net-zero-line edit of the 2 existing call sites to stay under it.
- [x] [DATA] P3. Check whether the same generic-path bypass affects `(LIGHTER-ZKSYNC, book_snapshot_5)` or
      `(EXTENDED-STARKNET, book_snapshot_5)` via the same live-manifest cross-reference method used here. Repos:
      market-tick-data-service, unified-api-contracts. **CONFIRMED both affected, both resolved by the same fix** — live
      manifest read (2026-07-29): `(LIGHTER-ZKSYNC, book_snapshot_5)`: 24,558 rows (22,871 expected_unattempted, 1,661
      empty_confirmed, 26 attempted_failed), 59 written today (50 empty_confirmed + 9 attempted_failed, both
      `pipeline_mode=batch_tardis`/ `market-tick-data-service`). `(EXTENDED-STARKNET, book_snapshot_5)`: 19,956 rows
      (18,408 expected_unattempted, 1,548 empty_confirmed), 50 written today (all empty_confirmed,
      `pipeline_mode=batch_extended`/ `market-tick-data-service`). Both venues declare `book_snapshot_5` in
      `VENUE_DATA_TYPE_NO_BATCH_SOURCE`, so both are excluded once `for_batch=True` is honored by the same 2 call sites
      fixed above — no separate code change needed.
- [x] [DATA] P3. Once the writer is fixed, the existing ~69,000 polluting rows across the 3 affected combos
      (`LIGHTER-ZKSYNC` trades: 24,559 + book_snapshot_5: 24,558; `EXTENDED-STARKNET` book_snapshot_5: 19,956) need a
      cleanup pass (delete or re-classify the `expected_unattempted`/`empty_confirmed`/`attempted_failed` rows written
      under this now-fixed bug) so the honest-coverage denominator stops carrying permanently-unclosable cells. **DONE
      2026-07-29** — chose DELETE over reclassify: unlike
      `reclass_cefi_tardis_impossible_combinations_400_2026_07_27.py`'s precedent (a legitimate per-cell confirmed-
      absence finding worth preserving as `empty_confirmed`), these rows represent an entire (venue, data_type) AXIS
      that should never have been in the batch-expected universe at all — the 2026-07-15 ruling's own language ("no
      expected_unattempted, no empty_confirmed row, full stop") makes deletion the semantically correct target state.
      Wrote `market-tick-data-service/scripts/reclass_cefi_no_batch_source_phantom_rows_2026_07_29.py` mirroring the
      Tardis-400 script's safety mechanics (dry-run default, snapshot-before-write, gate checks on row-count
      arithmetic + `captured` preservation). Confirmed via a fresh manifest read of both writers
      (`instruments-service`'s stale pre-2026-07-15-fix `expected_unattempted` seeding + `market-tick-data-service`'s
      now-fixed `attempted_failed`/`empty_confirmed`) that the full 69,223-row scope belonged to this bug, with exactly
      1 legitimate exception preserved untouched:
      `(LIGHTER-ZKSYNC, trades, 2026-05-01, BTC-USDC@LIN,     captured, service=market-data-processing-service)` — a
      different service's candle-reaggregation artifact, out of scope. Snapshot taken first
      (`gs://market-data-tick-cefi-prd-central-element-323112/_index/snapshots/     pre_no_batch_source_phantom_removal_20260729T154127Z.parquet`),
      then applied: 69,223 rows removed (9,951,022 → 9,881,799), gate checks passed. Post-apply independent verification
      read confirms the exact target end-state: `(LIGHTER-ZKSYNC, trades)` 1 row (the preserved captured row),
      `(LIGHTER-ZKSYNC, book_snapshot_5)` 0 rows, `(EXTENDED-STARKNET, book_snapshot_5)` 0 rows.

## Follow-up: LIGHTER-ZKSYNC derivative_ticker real backfill attempted, hit a SEPARATE bug

Per this doc's earlier note that `(LIGHTER-ZKSYNC, derivative_ticker)` — unlike the 3 no-batch-source combos above —
genuinely IS batch-reachable via Tardis (confirmed by the 2026-07-07 manual verification) but had never actually been
backfilled in production (0 captured), I attempted a real production backfill (2026-04-17 through today, 179
instruments) as a direct follow-up. The Tardis fetch itself succeeded (confirming real data exists), but every write
failed a schema-contract check due to a SEPARATE, previously-undiscovered bug: Tardis's numeric `market_id` leaks into
the written `symbol` column/filename instead of the original ticker. Full root cause, evidence, and a scoped
(not-yet-implemented) fix approach are tracked in the new companion doc:
`/plans/active/issues/lighter_zksync_derivative_ticker_tardis_numeric_market_id_leaks_into_symbol_schema_2026_07_29.md`.
No manifest cleanup was needed from this attempt — verified the brief VM run only wrote honest `empty_confirmed` rows
for genuinely pre-coverage dates, no false `attempted_failed`/`captured`.
