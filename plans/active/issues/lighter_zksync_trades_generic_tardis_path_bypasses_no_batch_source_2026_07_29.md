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

## Not yet determined

- The EXACT code path/file that's still calling Tardis for `(LIGHTER-ZKSYNC, trades)` — I traced it to "the generic
  `--operation download` orchestrator" per the sibling handler's own docstring reference, but did not read that
  orchestrator's source directly to confirm the missing check.
- Whether the SAME gap affects `(LIGHTER-ZKSYNC, book_snapshot_5)` or `(EXTENDED-STARKNET, book_snapshot_5)` — not
  checked in this pass, worth the same live-manifest cross-reference.
- Whether the 1 `captured` row (from `market-data-processing-service`, not MTDS) for this combo is a benign anomaly
  (e.g. a different valid symbol/edge case) or itself a symptom worth tracing.

## Todos

- [ ] [FIX] P2. Find the generic `--operation download` Tardis orchestrator (per `_onchain_perp_batch_lighter.py`'s own
      docstring reference) and add a `venue_data_type_has_batch_source()` (or equivalent UAC registry) check before it
      attempts `(LIGHTER-ZKSYNC, trades)` — matching the exclusion the venue-specific handlers already correctly apply.
      Repo: market-tick-data-service.
- [ ] [DATA] P3. Check whether the same generic-path bypass affects `(LIGHTER-ZKSYNC, book_snapshot_5)` or
      `(EXTENDED-STARKNET, book_snapshot_5)` via the same live-manifest cross-reference method used here. Repos:
      market-tick-data-service, unified-api-contracts.
- [ ] [DATA] P3. Once the writer is fixed, the existing 24,559 polluting rows for `(LIGHTER-ZKSYNC, trades)` need a
      cleanup pass (delete or re-classify) so the honest-coverage denominator stops carrying a permanently-unclosable
      cell — attended real-infra step, not autonomous (manifest row deletes need the same care as GCS object deletes).
      Repo: market-tick-data-service.
