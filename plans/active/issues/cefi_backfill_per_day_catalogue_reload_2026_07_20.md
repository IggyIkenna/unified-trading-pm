---
doc_type: issue
title: >-
  cefi on-chain-perp batch backfill re-loads the 428k-row catalogue + re-resolves the venue universe on EVERY day (fresh
  subprocess per day) — per-day throughput is bootstrap-bound (~30-34s/day) regardless of data volume
summary: >-
  The VM startup loop for collect-onchain-perp-batch (HL/ASTER/LIGHTER/EXTENDED) invokes the CLI once PER DAY as a fresh
  subprocess. Each invocation re-bootstraps the service AND calls resolve_venue_symbols → catalogue_symbols_for_venue →
  CeFiCatalogReader.list_instruments, which loads the ENTIRE instruments-store-cefi prod/catalog.parquet (428,625 rows)
  from GCS and re-resolves the per-venue active-perp universe. Measured on the 2026-07-20 HL trades backfill: ~30-34s
  WALL PER DAY even for empty pre-data days (0 rows), of which ~17s is a single CPU-bound block (cpu=111%) between
  "loaded 428625 catalogue rows" and "catalogue-driven universe for HYPERLIQUID on <day> = 172 symbols". So a one-VM
  full-universe HL trades backfill (~565 days) takes ~3.5h dominated by per-day catalogue reload + universe
  re-resolution, NOT by the S3 download. The MTDS parse-once-per-day trades fix (mtds@a6e974b6) removed the separate
  165x per-instrument download redundancy WITHIN a day, but this per-DAY process churn is a different, now-dominant
  cost.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [vm-launcher, backfill, performance, catalogue, did-we-reload-the-code, cefi-onchain-perp]
related:
  [
    /plans/active/issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
  ]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: data-pipeline
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source:
  [
    "discovered 2026-07-20 while accelerating the HL trades full-universe backfill (operator: 'surely you don't need to
    reload same catalogue each day you can cache it load once no?')",
  ]
---

# cefi backfill re-loads the catalogue + re-resolves the universe every day

## Evidence

VM `cefi-hyperliquid-2025-20260720-093104`, run.log (per-day subprocess for 2025-01-04):

```
08:35:27  DomainValidationService initialized  (per-day __bootstrap__ begins)
08:35:29  op=collect-onchain-perp-batch
08:35:29  cefi_catalog_reader: loaded 428625 catalogue rows from instruments-store-cefi-prd/prod/catalog.parquet
08:35:32  RESOURCE_SAMPLE cpu=111.2%  ← CPU-bound
08:35:49  OnchainPerpBatch: catalogue-driven universe for HYPERLIQUID on 2025-01-04 = 172 symbols   (~17s later)
08:35:50  OnchainPerpBatch complete for 2025-01-04: 0 rows
```

~34s wall for a **0-row** day. Next day (2025-01-05) repeats the whole bootstrap+catalogue+resolution from a fresh
subprocess. `HyperliquidS3Downloader` is also constructed per-shard (~172/day) for the `_assert_source_reachable`
credential preflight (each does a Secret Manager fetch — cheap ~1s/day, but still per-instrument churn).

## Root cause

- **Per-day subprocess:** the VM startup script (`setup-data-pipeline-vm.sh`) loops the day range and invokes the CLI
  once per day. `OnchainPerpBatchHandler.handle()` processes a SINGLE `payload.date` — it does not loop a range.
- **Catalogue reload:**
  `market_tick_data_service/cli/handlers/_onchain_perp_batch_symbols.py::catalogue_symbols_for_venue` builds a fresh
  `CeFiCatalogReader` and calls `list_instruments("cefi", day, day, venues=[venue])`, loading the full 428k-row
  catalogue from GCS + re-resolving the universe — every day, in every fresh process.

## Proper fix (two options)

1. **Range-loop in one process (preferred):** have `collect-onchain-perp-batch` accept a `[start,end]` window and loop
   days internally, loading the catalogue + constructing the `HyperliquidS3Downloader` (and its parse-once day-cache)
   ONCE per process; change the startup loop to call the CLI once per shard instead of once per day. Eliminates the
   per-day bootstrap + catalogue reload entirely (one bootstrap per VM). Touches the shared VM startup script — pair
   with `vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md` (rollout the edited startup script to GCS).
2. **Cross-process cache in `CeFiCatalogReader`:** cache the parsed catalogue (or the resolved per-(venue,day) universe)
   to local disk keyed by (bucket, catalogue object generation/mtime); subsequent per-day processes on the same VM read
   local instead of re-downloading+re-parsing. Smaller blast radius, but still pays a per-process parse; the CPU-bound
   ~17s must be shown to be the GCS-parse (cacheable) vs. an in-memory filter over 428k rows (needs a different fix).
   Reuse ONE `HyperliquidS3Downloader` for the `_assert_source_reachable` preflight too (cache on `self`, cache the
   `is_available` result — credentials don't change within a process).

## Interim mitigation — SHIPPED

Finer-than-year date-range sharding added to the launcher (`deployment-service@00886fe`,
`scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`): `SHARD_DAYS=N` sub-divides each year into N-day range VMs and
`OVERRIDE_START_DATE` skips empty pre-data days. HL requester-pays S3 is not rate-limited (exempt from the Tardis 1-VM
cap), so the per-day waste is parallelized across many VMs. The 2026-07-20 HL trades full-universe backfill ran as 21
shards (2025-05-25→2026-07-20) in ~20min instead of ~3.5h. This does not remove the per-day waste — it hides it behind
parallelism (fleet still does ~565 catalogue reloads total). The proper fix above removes it.
