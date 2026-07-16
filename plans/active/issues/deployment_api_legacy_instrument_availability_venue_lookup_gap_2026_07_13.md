---
doc_type: issue
title:
  deployment-api legacy `/instrument-availability` endpoint can't resolve asset_group for ASTER (and any venue outside
  its hardcoded 12-venue list)
summary: >
  While confirming downstream readers pick up the migrated ASTER cefi data
  (aster_cefi_data_defi_bucket_migration_2026_07_13.md Phase 3 Todo 2), found that deployment-api's real/current
  data-status drilldown (GET /api/data-status/drilldown/{service}/{asset_group}) correctly surfaces the migrated data —
  live-verified for ASTER/derivative_ticker/2023-11-01 — but a separate, legacy endpoint (GET
  /api/data-status/instrument-availability) is broken for ASTER, and for any venue outside a hardcoded 12-venue
  substring list, because it derives asset_group from a hardcoded per-venue lookup instead of the canonical
  VENUE_TO_ASSET_GROUP registry, and probes a flat non-canonical GCS path instead of reading the availability manifest.
status: resolved
nature: notes
asset_group: [cefi, defi, tradfi]
stage: [data]
repos: [deployment-api]
scope: [engineer]
tags: [data-status, deployment-api, venue-registry, pre-existing, aster]
related: [plans/archive/2026_07/aster_cefi_data_defi_bucket_migration_2026_07_13.md]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P3
source:
  aster_cefi_data_defi_bucket_migration-008 dispatch (Phase 3 Todo 2, "confirm downstream readers"), slot 9, 2026-07-13
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by: slot-13 (2026-07-14), deployment-api@d3a64da
---

# deployment-api legacy `/instrument-availability` endpoint has a hardcoded venue→asset_group gap

## What I found

Investigating whether MDPS / features-service / deployment-api correctly pick up the newly-migrated ASTER cefi tick data
(previously stranded in the DeFi bucket, now copied to the canonical CeFi bucket per
`aster_cefi_data_defi_bucket_migration_2026_07_13.md`), I confirmed the **real** data-status surface works:

- `GET /api/data-status/drilldown/{service}/{asset_group}` → `deployment_api/services/data_status_hierarchical.py:400`
  `get_hierarchical_drilldown()` resolves the bucket dynamically via `build_bucket_name()` →
  `resolve_bucket_name(cloud="gcp", kind=..., asset_group=...)` (`asset_group` is a caller-supplied URL param, not
  inferred from venue) and reads the live `availability_index.parquet` manifest. **Live-verified**: called this function
  directly (no HTTP server needed) for `service="market-tick-data-service"`, `asset_group="cefi"`, `venue=ASTER`,
  `data_type=derivative_ticker`, `window=2023-11-01` — a day the migration plan confirms was previously **0%** present
  in the CeFi bucket (`zero_dup` band) — and got back `captured: 63, completion_pct: 100.0` reading from
  `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, with
  `pipeline_mode: batch_aster` provenance and canonical `ASTER:PERPETUAL:{BASE}-{QUOTE}@LIN` instrument keys. This
  endpoint needs no fix — GOOD.

While tracing the deployment-api data-status routes, found a **separate, legacy** endpoint that is broken, unrelated to
the migration:

- `GET /api/data-status/instrument-availability` → `deployment_api/routes/data_status/_query_meta.py:130-163` →
  `deployment_api/services/data_query_service.py` `get_instrument_availability()` calls `_venue_to_category()`
  (`data_query_service.py:654-663`), a hardcoded substring match recognizing only `BINANCE/BYBIT/OKX/DERIBIT` (cefi),
  `NYSE/NASDAQ/CME/CBOE/ICE` (tradfi), `UNISWAP/AAVE/CURVE/BALANCER` (defi) — 12 venues total. `venue=ASTER` (or any
  venue outside this list, e.g. any of the other CeFi venues onboarded since this was written) returns
  `{"error": "Could not determine asset group for venue: ASTER"}`.
- Independent of the venue-lookup gap, `_check_daily_availability()` (`data_query_service.py:684-705`) probes a flat
  path shape (`f"{venue}/{instrument_type}/{instrument}/{date}/{data_type}"`) that does not match the real hive layout
  (`raw_tick_data/by_date/day=.../pipeline_mode=.../asset_group=.../venue=.../instrument_type=.../data_type=...`) and
  never reads the availability manifest at all — this endpoint looks broken/stale for essentially any real instrument,
  not an ASTER-specific regression.

## Why it matters

- Not caused by, and does not block, the ASTER migration — the endpoint operators/UI actually use for coverage
  drilldowns (`/drilldown/{service}/{asset_group}`) works correctly and already reflects the migrated data.
- But it is a genuine, currently-live correctness gap: any caller of `/instrument-availability` for ASTER (or any venue
  outside the hardcoded 12) gets a hard error instead of an answer, and even for the 12 recognized venues the path-shape
  mismatch means the check likely never finds real data. Low severity (a legacy/parallel endpoint, not the primary UI
  path) but worth a tracked fix rather than leaving a silently-wrong venue allowlist to bit-rot further as new venues
  (ASTER included) onboard.

## Recommended decision

Not fixed inline — out of scope for the migration task that surfaced it, and the correct fix is broader than
ASTER-specific (replace the hardcoded venue-substring list with the canonical UAC `VENUE_TO_ASSET_GROUP` registry
lookup, and fix `_check_daily_availability()`'s path template to match the real hive-partition layout, ideally by
delegating to the same manifest-backed path the `/drilldown` endpoint already uses correctly).

## Todos

- [x] ✅ [BACKEND] P3. `deployment-api/deployment_api/services/data_query_service.py:654-663` `_venue_to_category()`:
      replace the hardcoded 12-venue substring list with a lookup against the canonical UAC `VENUE_TO_ASSET_GROUP`
      registry (same source `instruments-service` and MTDS already use) so newly-onboarded venues (ASTER included)
      resolve correctly. — deployment-api@38213b6
- [x] ✅ [BACKEND] P3. `deployment-api/deployment_api/services/data_query_service.py:684-705`
      `_check_daily_availability()`: fix the flat path-shape probe (or delegate to the manifest-backed
      `read_availability_index()` path the `/drilldown` endpoint uses) so this endpoint reflects real data instead of
      being stale/broken for effectively every instrument. (repo: deployment-api) — **DONE, slot-13,
      `deployment-api@d3a64da`.** Delegated to `read_availability_index`
      (`deployment_api.services.manifest_source.     read_manifest_index`) — the exact manifest-backed path
      `/drilldown/{service}/{asset_group}` already uses — filtered by
      `venue`/`instrument_id`/`instrument_type`/`date`/`data_type`, with `capture_status == "captured"` as the
      availability signal (pre-v5 rows without `capture_status` default to captured, matching the legacy convention used
      elsewhere in the data-status stack, e.g. `_aggregate_counts` in `data_status_hierarchical.py`). Updated the 9
      existing tests to mock `read_availability_index` with a manifest-shaped DataFrame instead of `object_exists` (now
      unused, removed from imports); added 2 new tests (manifest-backed lookup for a non-hardcoded venue,
      `capture_status` filtering). Full `quality-gates.sh` green. Both todos in this issue doc are now done.
