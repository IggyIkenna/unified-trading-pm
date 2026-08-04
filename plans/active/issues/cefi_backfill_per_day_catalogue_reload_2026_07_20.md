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
    /plans/archive/issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
  ]
created: 2026-07-20
author: unknown
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
context_scope:
  [
    /plans/archive/issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_onchain_perp_batch_symbols.py,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
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

## Todos

- [ ] [BACKEND] P2. **Implement the proper fix (range-loop in one process, or a cross-process `CeFiCatalogReader`
      cache)** — the interim per-year sharding mitigation only hides the per-day catalogue-reload waste behind
      parallelism; neither of the two proper-fix options above has been implemented.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the sole todo is an unresolved choice
  between two architectures (range-loop in one process vs a cross-process catalogue cache), one of which changes the
  shared VM startup script fleet-wide.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (tranche=cefi, autonomous): KEEP-NA, valid — re-verdicted only because the
  2026-08-01 `context-scout` frontmatter backfill moved the doc's git date past the 07-30 marker; the body is
  byte-identical to the 07-30 reading (verified `git diff eaa6bfd1e..HEAD` = the `context_scope` block only). Verdict
  unchanged: the sole todo is still an unresolved architecture choice (range-loop in one process vs a cross-process
  `CeFiCatalogReader` cache), one branch of which rewrites the shared fleet-wide VM startup script. Not
  worker-determinable.
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) — body unchanged since 2026-08-01, existing list
  still accurate.
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-02 verdict; the
  sole todo is still an unresolved architecture choice (range-loop rewrite vs. cross-process cache), one branch of which
  touches the shared fleet-wide VM startup script — a design call, not bounded worker-determinable work.
- **[DIAG] P2 profiling 2026-08-04** (slot 10, `cefi_satellite_ao_dispatch_batch3-005`): profiled
  `catalogue_symbols_for_venue("HYPERLIQUID", 2025-01-04)` on the orchestrator host (GCP, in-region) with the live prod
  catalog (`instruments-store-cefi-prd/prod/catalog.parquet`, 431,301 rows × 40 columns, 9.1 MB). **Read-only — zero
  code, GCS, or manifest mutations.** Results below.

  ### Profile breakdown: where the ~17s goes

  | Phase                                                          | Wall time  | % of total | Notes                                                                                   |
  | -------------------------------------------------------------- | ---------- | ---------- | --------------------------------------------------------------------------------------- |
  | (i) GCS object download (`download_bytes`)                     | **0.19s**  | ~1%        | 9.1 MB from in-region GCS; backfill VM may be ~1-3s                                     |
  | (ii) Parquet parse (`pd.read_parquet`)                         | **0.54s**  | ~3%        | pyarrow C++ engine, 431k rows                                                           |
  | (iii) `_build_has_perp_for_base` (iterrows over ALL 431k rows) | **~6-7s**  | ~40%       | Builds `(base_exchange, base_upper)` set of perp-gated bases                            |
  | (iii) `_yield_for_date` (iterrows over ALL 431k rows AGAIN)    | **~6-7s**  | ~40%       | Per-row Series construction + venue filter + date check + MVP gate + `CatalogRow` build |
  | `CeFiCatalogReader.__init__` + other                           | **~0.5s**  | ~3%        | Client init, bucket resolution                                                          |
  | **Total (in-memory, cached catalog)**                          | **~13.1s** | ~85%       | The sum of the two `iterrows()` passes                                                  |
  | **Total (fresh reader, no cache)**                             | **~13.8s** | —          | Same as above + 0.7s download+parse                                                     |

  The ~4s gap between the observed ~13s here and the ~17s reported in the VM run.log is attributable to: (a) slower CPU
  on the e2-standard backfill VM vs the orchestrator host, (b) pandas 2.x `iterrows()` being CPU-frequency-sensitive,
  and (c) the backfill VM's GCS download being cross-region (~1-3s vs in-region 0.2s). The shape is identical: the
  dominant cost is `iterrows()` constructing a new `pd.Series` per row (862k Series objects across both passes), plus
  `sanitize_array`/`maybe_infer_to_datetimelike` type-inference overhead on every single row.

  ### cProfile hot-path attribution (deep profile confirms the iterrows bottleneck)

  The 53s cProfile run (profiler overhead ~4×) shows the exact same shape:
  - `DataFrame.iterrows`: 1.3s tottime / **44.3s cumtime** — the loop driver
  - `Series.__init__`: **5.3s tottime** — constructing a Series per row (862k times)
  - `sanitize_array`: **3.3s tottime** — type inference per row
  - `maybe_infer_to_datetimelike`: **3.3s tottime** — datetime coercion per row
  - `_build_has_perp_for_base`: 0.8s tottime / **27.1s cumtime** (profiler-inflated; real ~6-7s)
  - `_yield_for_date`: 0.5s tottime / **25.3s cumtime** (profiler-inflated; real ~6-7s)
  - The per-row PREDICATES (venue check, date filter, MVP gate, `CatalogRow` build) are **negligible** — ~0.65s total
    across all 431k rows

  Cross-venue consistency check (all 4 onchain-perp venues on 2025-01-04, cached catalog): HYPERLIQUID 12.5s (178
  symbols), ASTER 12.8s (452 symbols), LIGHTER-ZKSYNC 13.4s (179 symbols), EXTENDED-STARKNET 13.9s (76 symbols). The
  `_yield_for_date` cost is row-count-driven (always iterates the full 431k), not result-count-driven — the number of
  symbols yielded varies 4-6× but wall time varies only ~10%.

  ### Impact on the Option A vs Option B design decision

  **The ~17s is an in-memory `iterrows()` bottleneck, NOT a cacheable GCS-download+parse cost.** The GCS download +
  parquet parse together are **≤0.7s** (in-region) — ~4% of the total. This means:

  - **Option B (cross-process local-disk cache in `CeFiCatalogReader`) would save ≤0.7s per day.** It does not touch the
    `iterrows()` passes — `list_instruments` still calls `_build_has_perp_for_base` + `_yield_for_date`, both of which
    iterate the full cached DataFrame. A local-disk cache would reduce a ~17s per-day cost to... ~16.3s. **Option B is
    the wrong design for this bottleneck.**

  - **Option A (range-loop in one process) would eliminate the per-day cost entirely** — load the catalogue once,
    resolve the universe once per venue (not once per venue per day), loop days internally. The 13-17s becomes a
    one-time startup cost amortized across the entire backfill range. A 565-day backfill currently pays ~565 × 17s ≈
    2.7h of catalogue overhead; Option A reduces this to ~17s total.

  - **A vectorized filter (not in scope, but noted)** — replacing `iterrows()` with columnar/vectorized predicates (e.g.
    `df[df['venue'].isin(venue_set) & date_mask & mvp_mask]`) or even `itertuples()` would reduce the in-memory
    filtering from ~13s to well under 1s. This is a complementary optimization that would benefit BOTH options and is
    orthogonal to the Option A/B decision. It does not require changing the per-day subprocess architecture.

  **Evidence favours Option A** (range-loop in one process) as the design that actually addresses the measured
  bottleneck. Option B caches the wrong thing (the <1s GCS I/O instead of the ~13s `iterrows()`). The operator should
  rule accordingly.

  Raw profiling script: `market-tick-data-service/profile_catalogue_symbols.py` (one-off, to be deleted after the data
  is committed to this doc — see the batch3 plan todo 5 done-definition).
