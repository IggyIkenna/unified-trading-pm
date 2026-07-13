---
doc_type: issue
title:
  CeFi backfill VMs resolve ZERO instruments for every (venue, date) — "NO INSTRUMENTS FOUND" honest-skip on
  venues/dates with confirmed by_date coverage, while the CeFi instruments availability index is being actively
  rewritten
summary:
  "Found 2026-07-13 ~21:15Z by the Tardis lease pilot waves (tardis_concurrent_ip_lockout_2026_07_12.md): TWO
  consecutive 2-VM waves (BITFINEX-SPOT/BYBIT-SPOT 2025, then BINANCE-FUTURES 2024 heavy+light) had EVERY processed date
  honest-skip with 'MTDS: venue=<V> date=<D> — NO INSTRUMENTS FOUND (instruments-service data missing)' — including
  BINANCE-FUTURES 2024, which has weeks of prior v10 backfill history AND confirmed-present
  instrument_availability/by_date/day=2024-06-15/venue=BINANCE-FUTURES/ partitions (checked live). The VMs' catalogue
  reader loads fine (364,326 cefi rows), so the failure is the per-(venue,date) availability lookup. The CeFi
  instruments availability index (instruments-store-cefi-prd _index/availability_index.parquet) shows Update time
  21:20:40Z (minutes before the check) at 2.7MB — consistent with the ACTIVE
  aster_cefi_data_defi_bucket_migration_2026_07_13.md workstream (AO task -007: 'Rewrite/extend the canonical CeFi
  _index/availability_index.parquet manifest rows') rewriting it mid-wave. All 4 pilot VMs were stall-watchdog-killed
  (exit 137, STALL_PROGRESS_REGEX=uploaded never matching an all-skip run). SECONDARY finding in the same logs: the
  honest-skip manifest write itself fails ('MalformedRowKeyError: shard-atom field chain was explicitly passed as empty'
  — hard_schema_enforcement Phase 4 vs a skip-sentinel callsite passing chain='') so the skip rows never even land as
  expected_unattempted. NOT touched further: the index is another workstream's active migration surface — collision
  risk; verify instrument resolution AFTER the ASTER migration settles, then re-run the lease pilot."
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [cefi, backfill, instrument-resolution, availability-index, migration-collision, data-correctness, big-finding]
related:
  [
    tardis_concurrent_ip_lockout_2026_07_12.md,
    ../aster_cefi_data_defi_bucket_migration_2026_07_13.md,
    ../data_pipeline_e2e_check_2026_07_10.md,
  ]
created: 2026-07-13
parent_epic: cefi_master
priority: P0
source:
  [Tardis lease pilot waves 1+2 (4 real VMs, run.log evidence), live gsutil store checks, 2026-07-13 ~20:00-21:25Z]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data-pipeline-engineer
drift_direction: unknown
depends_on: []
---

# CeFi backfill instrument resolution returns empty for every (venue, date)

## Evidence

- Pilot 1 (`BITFINEX-SPOT`/`BYBIT-SPOT` 2025, VMs `cefi-{bitfinex,bybit}-spot-2025-heavy-20260713-200213`) and pilot 2
  (`BINANCE-FUTURES` 2024 heavy+light, `cefi-binance-futures-2024-{heavy,light}-20260713-204215`): every date logs
  `NO INSTRUMENTS FOUND (instruments-service data missing for venue=<V> date=<D>) ... Skipping venue.` then
  `SKIPPED SHARDS ... 1/1 venues skipped (no instruments)`. All 4 VMs exit 137 (stall watchdog — an all-skip run never
  emits the `uploaded` progress signal).
- The SAME VM logs show `cefi_catalog_reader: loaded 364326 catalogue rows` — the catalogue path works; the
  per-(venue,date) availability gate is what returns empty.
- `instrument_availability/by_date/day=2024-06-15/venue=BINANCE-FUTURES/` EXISTS in `instruments-store-cefi-prd`
  (checked live 21:2xZ) — the source partitions are present.
- `instruments-store-cefi-prd/_index/availability_index.parquet`: `Update time: 21:20:40Z` (minutes old at check),
  2,764,248 bytes — being actively rewritten, timing-consistent with
  `aster_cefi_data_defi_bucket_migration_2026_07_13.md` AO task `-007` ("Rewrite/extend the canonical CeFi
  `_index/availability_index.parquet` manifest rows").

## Secondary finding (same logs)

`Manifest write failed (non-blocking): MalformedRowKeyError: shard-atom field 'chain' was explicitly passed as empty` on
every honest-skip `expected_unattempted` write (`row_key={date, venue, chain: '', data_type, instrument_type}`) —
hard_schema_enforcement Phase 4 made empty `chain` a hard error and this skip-path callsite still passes `chain=''` for
non-chain venues. The honest-skips therefore never land in the manifest — a silent denominator gap on top of the skip
itself.

## Deliberately NOT actioned this session

The availability index is another workstream's ACTIVE migration surface (collision risk). Next steps for whoever picks
this up (or after the ASTER migration completes): (1) confirm per-(venue,date) resolution against the settled index
(BINANCE-FUTURES 2024 should resolve hundreds of instruments); (2) fix the `chain=''` skip-sentinel row_key (either omit
`chain` for non-chain venues or populate it); (3) re-run the Tardis lease pilot
(`tardis_concurrent_ip_lockout_2026_07_12.md`, operator-approved slice BINANCE-FUTURES 2024) — the lease mechanism is
still UNEXERCISED in production multi-VM conditions.
