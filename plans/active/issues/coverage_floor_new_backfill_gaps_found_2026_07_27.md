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
related: [/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md]
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
- [ ] [DATA] P2. **DERIBIT sparse/partial 2019 historical backfill.** `trades` data_type has real captured rows
      (thousands-to-hundreds-of-thousands `instrument_count`/day, not placeholders) 2019-05-08 through 2019-12, but NOT
      on every calendar day (multi-day gaps) — unlike `book_snapshot_5`/`derivative_ticker`, which start cleanly and
      densely at 2020-01-01. Investigate whether more complete 2019 Deribit history is available from Tardis (their
      archive plausibly reaches further back, per DERIBIT's now-corrected-but-previously-unverified 2016-06-13 seed) and
      whether the existing sparse rows are worth completing into a dense daily series. (repo: market-tick- data-service
      backfill)
- [ ] [DATA] P3. **BINANCE-DELIVERY has zero real data.** `venue_mapping.py`'s `BINANCE-DELIVERY` entry (`2020-01-01`)
      has ZERO real captured rows in the manifest — only 7 `attempted_failed` rows dated 2026-07-26. The registered
      floor is unverifiable against measured reality because no real data exists yet. Investigate whether Binance COIN-M
      delivery contracts are actually being fetched at all, or whether this is a dead/never-implemented shard. (repo:
      market-tick-data-service)
