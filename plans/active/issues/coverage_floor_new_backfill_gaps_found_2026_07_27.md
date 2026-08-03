---
doc_type: issue
title: 3 new data-completeness findings surfaced while fixing coverage_floor_registries_no_cross_propagation-002
summary: >-
  Small standalone note (disk-full incident prevented editing the parent issue doc directly at write time — see
  coverage_floor_registries_no_cross_propagation_2026_07_17.md's [DATA] P1 status note for the full context). Fold these
  3 todos into that doc once disk recovers and delete this file.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [coverage-floor, backfill-gap, data-completeness]
related:
  [
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
source:
  "slot-6, 2026-07-27, coverage_floor_registries_no_cross_propagation-002, surfaced while manifest-probing 8 CeFi venue
  coverage floors"
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    unified-api-contracts/unified_api_contracts/registry/venue_mapping.py,
    market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py,
  ]
---

# 3 new backfill/data-completeness findings

## Todos

- [x] [DATA] P1. **DONE 2026-07-27 (slot-15)** — **HYPERLIQUID never-attempted backfill gap, root-caused + backfill
      confirmed in flight.** Re-verified: `market-data-tick-cefi-prd-central-element-323112` has ZERO manifest rows of
      ANY `capture_status` (not even `expected_unattempted`) for HYPERLIQUID across ALL data_types (`book_snapshot_5`,
      `derivative_ticker`, `trades`) in the entire `2023-04-15..2023-12-31` window — confirmed via a bounded,
      column-projected manifest read (no VM, no corpus walk), not just the originally-cited `book_snapshot_5` slice.
      **Root cause: never scheduled, NOT an adapter/source gap.** The HYPERLIQUID S3 adapter
      (`market_tick_data_service/adapters/hyperliquid_s3.py`) hardcodes `S3_L2_BOOK_START = 2023-04-15` — verified real,
      live vendor data via a direct requester-pays S3 probe (`hyperliquid_s3_archives_dead_upstream_2026_07_13.md`) — so
      the source genuinely has data here; nobody ever dispatched a backfill job that enumerated these shards (a genuine
      source gap or adapter defect would still leave `attempted_failed`/`expected_unattempted` rows; total absence of
      ANY manifest row means the shards were never even in scope for a run). **Backfill: found ALREADY IN FLIGHT, not
      launched by me.** `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` already documents
      `HYPERLIQUID: 2023-01-01 → today` as its intended coverage. A DRY_RUN confirmed a scoped re-run
      (`YEARS=2023 OVERRIDE_START_DATE=2023-04-15 OVERRIDE_END_DATE=2023-12-31 DATA_TYPES="book_snapshot_5;derivative_ticker"`,
      `trades` excluded — no real trades source exists before 2025-03-22 per `S3_TRADES_START`) would correctly target
      this exact gap, so I launched it for real (5 SPOT shards, `SHARD_DAYS=60`). **Before those shards did any work,
      discovered a pre-existing VM `cefi-hyperliquid-2023-20260727-071055` (launched 2026-07-27T00:10:58-07:00, ~47 min
      before mine) already RUNNING with a SUPERSET scope** (`VM_START_DATE=2023-01-01`, `VM_END_DATE=2023-12-31`,
      `VM_DATA_TYPES=trades;book_snapshot_5;derivative_ticker`, `VM_VENUE=HYPERLIQUID`) — almost certainly a concurrent
      AO worker dispatched the same underlying finding (this doc's own summary notes it was surfaced from
      `coverage_floor_registries_no_cross_propagation-002`, slot-6, which independently found the same gap while fixing
      the coverage-floor registries). **Deleted my 5 redundant STAGING VMs immediately**
      (`gcloud compute instances delete`, confirmed clean — none had started real work, no wasted spend beyond ~1 min of
      boot) rather than duplicate in-flight work / risk a shard-write race. Verified the pre-existing VM is genuinely
      healthy, not zombied: `RUNNING` status, serial console shows continuous minute-cadence activity through 07:58Z
      (~15 min before my check). **Not yet independently confirmed via captured manifest rows** — the consolidated
      `_index/availability_index.parquet` still shows 0 rows for this window as of this check, which is EXPECTED
      (manifest consolidation runs on its own cadence, lagging behind per-VM-shard writes; `MANIFEST_PER_VM_SHARDS=true`
      is set on that VM) and is NOT evidence the backfill is stalled. **Residual**: re-verify captured rows for this
      window once the VM completes (a few hours, VM-scale — not re-dispatched as a separate todo here since it is a
      natural follow-up check on already-in-flight work, not new work).
- [x] ✅ [DATA] P2. **DONE 2026-08-02 (slot-9)** — **DERIBIT sparse/partial 2019 historical backfill — root-caused +
      code fix shipped.** Confirmed via a bounded, column-projected manifest read
      (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, no corpus walk) of
      DERIBIT/`trades` 2019-05-08..2019-12-31 (238 calendar days): 84 days carry real `capture_status=captured` rows
      (`source=tardis`, `instrument_count` 3,800-193,593/day — genuine partial historical data, not placeholders); the
      other 154 days have NO manifest row of ANY status (never attempted, not a failure). **Answer: YES, worth
      completing, and more is available than even the 2019-05-08 floor implies.** Queried Tardis's own exchange metadata
      (`GET https://api.tardis.dev/v1/exchanges/deribit`, public, read-only): `BTC-PERPETUAL`/`ETH-PERPETUAL`
      `trades`/`book_snapshot_5`/`derivative_ticker`/etc. are ALL `availableSince: 2019-03-30` — i.e. Tardis has dense
      vendor-side data 5+ weeks before our registry floor (2019-05-08) and 9+ months before `book_snapshot_5`/
      `derivative_ticker`'s clean 2020-01-01 start. **Root cause of why 2019 was never backfilled**: the standard
      sharded-backfill launcher (`deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh`)'s `_venue_years()`
      never included `"2019"` for DERIBIT (only `2020..2026`), even after the registry floor
      (`venue_mapping.py`/`coverage_starts.py`) was corrected to 2019-05-08 on 2026-07-27 — so no full-year sharded run
      has EVER targeted 2019; the existing sparse 84-day rows are the residue of some earlier ad-hoc/pre-launcher
      process, not this launcher's output. **Fix shipped**: added `"2019"` to DERIBIT's year list in `_venue_years()`,
      and generalized the `START_DATE` override (previously 2026-only) to non-2026 years, so a future launch can start
      exactly at `2019-03-30` (Tardis's real `availableSince`) instead of a year-granular launch wasting ~89 days
      (2019-01-01..2019-03-29) where the vendor has zero data. **Not launched as a live VM in this task** — the Tardis
      fleet's hard 1-concurrent-VM cap was clear at investigation time (verified via `gcloud compute instances list`,
      zero Tardis-consuming VMs running), but a DERIBIT 2019 heavy+light launch is 2 buckets (heavy=trades+
      book_snapshot_5, light=derivative_ticker+options_chain+futures_chain per `DATA_LIGHT_DERIBIT`) that must be
      sequenced one-at-a-time under the cap, plus real multi-day GCP/Tardis cost — out of scope for this investigation
      task to launch unilaterally. **Follow-up** (not re-dispatched as a separate todo — a natural next step on
      already-shipped code, same class as the HYPERLIQUID item above): dispatch
      `YEARS=2019 START_DATE=2019-03-30 LAUNCH_GROUPS=heavy VENUES=DERIBIT bash scripts/vm/launch-cefi-sharded-backfill.sh`
      (then `LAUNCH_GROUPS=light` once heavy completes/frees the Tardis slot). Evidence: `deployment-service@4fff44f`
      (quickmerge-landed, verified ancestor of `origin/live-defi-rollout`). (repo: market-tick-data-service backfill /
      deployment-service)
- [ ] [DATA] P3. **BINANCE-DELIVERY has zero real data.** `venue_mapping.py`'s `BINANCE-DELIVERY` entry (`2020-01-01`)
      has ZERO real captured rows in the manifest — only 7 `attempted_failed` rows dated 2026-07-26. The registered
      floor is unverifiable against measured reality because no real data exists yet. Investigate whether Binance COIN-M
      delivery contracts are actually being fetched at all, or whether this is a dead/never-implemented shard. (repo:
      market-tick-data-service)

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **slot-9 2026-08-02**: closed the DERIBIT P2 todo — root-caused (launcher's `_venue_years()` never had 2019 for
  DERIBIT) + fix shipped (`deployment-service@4fff44f`) + synced the duplicate todo in
  `coverage_floor_registries_no_cross_propagation_2026_07_17.md`. 1 of 3 todos in this doc now remain open (P3
  BINANCE-DELIVERY); the doc's own header note (fold into the parent doc + delete once disk recovers) is still
  outstanding but out of scope for this task.
