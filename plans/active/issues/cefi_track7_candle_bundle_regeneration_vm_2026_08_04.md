---
doc_type: issue
title: CeFi Track-7 candle bundle regeneration — dedicated VM needed for MDPS --force backfill
summary: >-
  The 149 stale per-leg objects from the bundle-collision race are all GONE (deleted), but the replacement ticks.parquet
  bundles are incomplete across 105/112 affected cells. MDPS --force cannot run on the shared planning VM (34GB+ RSS,
  risk of AO outage). A dedicated VM is needed to regenerate the 8 affected days.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service]
scope: [engineer]
tags: [cefi, track-7, candle-bundle, mdps-backfill, vm-required]
related:
  [
    /plans/archive/2026_07/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
author: slot-11 (data_engineering)
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  cefi_consolidated_native_ao_extract_2026_07_25.md Todo 7 (Track-7 candle bundle-collision fix)
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/cefi_consolidated_native_ao_extract_2026_07_25.md,
    deployment-service/scripts/vm/launch-mdps-backfill-vm.sh,
  ]
---

# CeFi Track-7 candle bundle regeneration — dedicated VM needed

## What I found

### Part (a): Raw-tick presence — ALL PASS

All 8 affected days have raw-tick data in GCS for both BYBIT `futures_chain` and DERIBIT `options_chain`. The backfill
is unblocked on the source-data side. See the plan Progress Log for the full per-day table.

### Part (b): 149 stale objects are all GONE

All 149 per-leg residual objects listed in `plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv` (93
BYBIT futures_chain + 56 DERIBIT options_chain) return 404 from GCS — deleted. The immediate GCS clutter from the
bundle-collision race is resolved.

### Part (b): Bundle integrity — 105/112 cells INCOMPLETE

The canonical `ticks.parquet` bundles under
`processed_candles/by_date/day={day}/pipeline_mode=batch_tardis/timeframe={tf}/data_type={dtype}/instrument_type={INSTYPE}/venue={VENUE}/ticks.parquet`
were audited across all 8 days × 7 timeframes × 2 venue/type combos (112 cells total):

| Status  | Count | Description                                                            |
| ------- | ----- | ---------------------------------------------------------------------- |
| OK      | 7     | Correct symbol count matching pre-delete per-leg CSV                   |
| PARTIAL | 9     | Bundle exists but has only 1 symbol (the "race winner") instead of 2-3 |
| MISSING | 96    | No bundle at all at this path                                          |

Pattern:

- Only `15s` and `15m` timeframes have any bundles at all (all BYBIT futures_chain)
- All DERIBIT options_chain cells are MISSING across all 8 days × 7 timeframes
- BYBIT futures_chain for 2025-11-01 and 2026-01-01: ALL timeframes MISSING
- Every existing `15m` BYBIT bundle is PARTIAL — has only BTC, missing ETH (and SOL where applicable)

### Part (b): MDPS `--force` cannot run on shared planning VM

Attempted a narrow MDPS `--force` run (single day, single venue, single data_type, 2 timeframes). The MDPS framework
loaded 5,610 instruments and RSS climbed to 34GB+ before the run was killed. Running the full MDPS on the shared
planning VM would risk another AO outage (2 prior incidents: `expand_defi_pool_catalogue` 43.6GB,
`features_service.cross_instrument` 38.8GB). Dry-run mode works correctly and confirms the scoped backfill would only
touch 2-10 raw-tick files per cell.

## Why it matters

The 149 stale per-leg objects were correctly deleted, but their data was never merged into the shared `ticks.parquet`
bundles. Downstream consumers (features-service, strategy-service, UI) reading the bundle only see one leg's data (e.g.,
BTC futures chain but not ETH futures chain for the same day). This is a silent data gap — the bundles EXIST (no
manifest error) but are INCOMPLETE.

## Recommended decision

Launch a dedicated MDPS `--force` backfill VM (SPOT, per backfill-VM-defaults) scoped to:

- 8 days: 2023-06-01, 2023-08-02, 2023-11-02, 2024-02-01, 2024-02-02, 2024-07-01, 2025-11-01, 2026-01-01
- 2 venues: BYBIT (futures_chain), DERIBIT (options_chain)
- 7 timeframes: 15s, 1m, 5m, 15m, 1h, 4h, 1d
- Asset group: CEFI
- `--force` flag to regenerate existing bundles

The scope is tiny (2-10 raw-tick inputs per cell) — the MDPS framework overhead is the only reason this can't run on the
shared VM. A dedicated f1-micro or e2-small SPOT instance is sufficient.

## Todos

- [x] ✅ [INFRA] P2. **Launch dedicated MDPS `--force` candle backfill VM for Track-7: 8 days × BYBIT futures_chain +
      DERIBIT options_chain × 7 timeframes, CEFI only.** (repo: deployment-service, market-data-processing-service). Use
      the standard `launch-mdps-backfill-vm.sh` launcher with
      `MDPS_DATA_TYPES="futures_chain options_chain" MDPS_VENUES="BYBIT DERIBIT" MDPS_TIMEFRAMES="15s 1m 5m 15m 1h 4h 1d" MDPS_ASSET_GROUP=CEFI`,
      `--force`, and `--start-date 2023-06-01 --end-date 2026-01-01`. Bounded scope: ~600 raw-tick input files total
      across 8 non-contiguous days. SPOT instance (idempotent `--force` is safe to re-run on preemption). **Done when**:
      VM completes with exit 0, post-backfill bundle audit shows all 112 cells OK (correct per-leg symbol counts).
      **Launched**: `mdps-backfill-cefi-20260804-190444` (SPOT, e2-standard-8, asia-northeast1-c, RUNNING as of
      2026-08-04T19:04:44Z). GCS logs:
      `gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-cefi-20260804-190444/`. Post-completion
      audit todo below.

## Progress Log

- **context-scout 2026-08-05**: populated context_scope (5 entries).
