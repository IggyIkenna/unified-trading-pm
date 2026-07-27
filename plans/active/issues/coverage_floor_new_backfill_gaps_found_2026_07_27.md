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

- [ ] [DATA] P1. **HYPERLIQUID never-attempted backfill gap.** `market-data-tick-cefi-prd-central-element-323112` has
      ZERO manifest rows of ANY `capture_status` (not even `empty_confirmed`) between 2023-04-15 (book_snapshot_5's
      vendor-verified S3-archive start, per `venue_mapping.py`'s comment + a documented 2026-05-05 incident
      investigation) and 2023-12-31; real captures only begin 2024-01-01. The coverage floor itself is correct
      (2023-04-15, fixed in the parent issue doc) — this is a SEPARATE, genuine backfill gap: the window the floor says
      should be expected has never been fetched. Investigate why (adapter gap? never scheduled?) and either backfill it
      or file a `BLOCKED-*` reason if structurally infeasible. (repo: market-tick-data-service or the CeFi backfill
      launcher)
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
