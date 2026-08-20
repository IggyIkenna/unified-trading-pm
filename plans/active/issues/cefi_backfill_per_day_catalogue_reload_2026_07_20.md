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
parent_epic: security_and_cross_cutting_master
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
    market-tick-data-service/market_tick_data_service/engine/cefi_catalog_reader.py,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
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

## Profile findings — cProfile breakdown of the ~17s CPU block (2026-08-04)

A cProfile run of one full `list_instruments("cefi", day=2025-06-15, day, venues=["HYPERLIQUID"])` invocation on the
orchestrator VM, measuring all three phases separately (wall clock):

| Phase                  | Wall time  | % of total | Notes                                                                          |
| ---------------------- | ---------- | ---------- | ------------------------------------------------------------------------------ |
| (i) GCS download       | **0.19s**  | 0.4%       | `download_bytes()` on `prod/catalog.parquet` — 8.6 MB                          |
| (ii) Parquet parse     | **0.65s**  | 1.2%       | `pd.read_parquet(BytesIO(raw))` — 431,301 rows × 40 cols                       |
| (iii) In-memory filter | **53.68s** | 98.5%      | `df.iterrows()` loop over all 431k rows + MVP gate + `CatalogRow` construction |
| **Total**              | **54.52s** |            |                                                                                |

**Where the 53.68s of phase (iii) goes:**

- `_build_has_perp_for_base()` — **26.68s** (1 call iterating ALL 431k rows via `df.iterrows()` to find which
  `(exchange, base)` pairs have a PERPETUAL/EQUITY_PERP row)
- `_yield_for_date()` — **26.88s** (1 call + 178 generator yields, iterating ALL 431k rows a SECOND time to filter by
  venue, active-date window, MVP capture universe, and margin-leg gate)
- `catalogue_symbols_for_venue`'s own symbol-set loop: included in the `_yield_for_date` time

The per-day backfill subprocess pays BOTH costs: `_build_has_perp_for_base` re-computes the same per-exchange perp-index
from the full catalogue (the catalogue is date-independent — the same result every day), and `_yield_for_date` re-scans
all 431k rows even though the MVP gate's perp-bases set hasn't changed and the venue filter eliminates ~99.96% of rows
(~172 of 431k pass).

cProfile confirms the bottleneck is pure `pandas` row-at-a-time overhead: 862,604 calls to `df.iterrows()`, 876,306
calls to `_get_first` (column extraction per row), ~30M `isinstance` checks — standard `iterrows()` tax on a 431k×40
DataFrame.

**Which fix option does the evidence favour (operator information only — neither is adopted here):**

- **Option B (cross-process local-disk cache of the GCS download) would fix 0.4% of the total time.** The GCS download +
  parquet parse together account for under 2% of wall clock. Even eliminating them entirely would not move the needle —
  the bottleneck is the in-memory row iteration, not I/O. **Option B is the wrong design for the stated problem.**
- **Option A (range-loop in one process, loading the catalogue + constructing the reader once per process) is the
  correct direction**, because it eliminates the per-day re-iteration over all 431k rows — both the
  `_build_has_perp_for_base` scan and the `_yield_for_date` per-row loop repeat identically every subprocess. One
  bootstrap per VM instead of one per day directly removes the dominant cost.

This profiling run was strictly read-only: zero code changes, zero GCS/manifest mutations, zero VM launches.

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
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-04 verdict; the
  sole todo is still an unresolved architecture choice (range-loop rewrite vs. cross-process cache) touching the shared
  fleet-wide VM startup script. A 2026-08-04 cProfile finding narrows which option is correct but the doc explicitly
  declines to adopt/implement on that evidence alone.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — swapped the interim-mitigation launcher (already
  shipped, `SHARD_DAYS` sharding) for `engine/cefi_catalog_reader.py`, the file the 2026-08-04 cProfile finding
  pinpoints as the actual bottleneck (`_build_has_perp_for_base`/`_yield_for_date`, 98.5% of wall time) and thus the
  real target of the still-open "implement the proper fix" todo.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — sole open item is a range-loop-vs-cache architecture choice,
  genuine judgment call.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (cefi tranche)**: KEEP-NA, valid — re-checked against
  the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement, GSM secret `deepseek-v4-pro-api-key` + 5 Slack
  webhooks). Specifically verified "Option B retired" is UNRELATED to this doc's own locally-named "Option A/Option
  B" (the range-loop-vs-cross-process-cache choice in the 2026-08-04 cProfile finding) — the actual "Option B
  retired" ruling (`unified-trading-pm@e0c0496ba1`, 2026-08-08) formally retires the never-built PM-reconciler
  release-tag minter, a wholly different subsystem (`post_cutover_silent_assumption_sweep_2026_07_23.md`). No
  criterion bounds the sole open item. No reclassification.
- **na-eligibility-audit 2026-08-16** [body-hash:7537092b6116b0f1]: KEEP-NA, valid — Full end-to-end read (192 lines) confirms exactly 1 open todo, matching both the Phase-0 inventory and a fresh grep.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) — re-verified all 5 entries resolve on
  disk and remain accurate; content since the last marker was `na-eligibility-audit` re-confirmations only (no new
  dependencies).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
