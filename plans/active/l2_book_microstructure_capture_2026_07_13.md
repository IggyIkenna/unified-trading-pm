---
doc_type: plan
title: Deeper-Than-L5 Order Book Capture — populate queue_position_* for MARKET_MAKING_QUEUE_MICROSTRUCTURE
summary:
  Capture a deeper-than-L5 (L10/full-L2) order book for the 9 CeFi venues already carrying book_snapshot_5, derive
  queue_position_bid/ask + book_depth_levels through the canonical CanonicalBookMicrostructure shape, and flip their UAC
  capability rows from honest-absent to live_capable — unblocks MARKET_MAKING_QUEUE_MICROSTRUCTURE's backtest.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, features]
repos: [market-tick-data-service, features-service, unified-api-contracts]
scope: [engineer]
tags: [strategy, v2-engine, market-making, orderbook, microstructure]
related: [v2_engine_venue_buildout_2026_06_15.md]
created: 2026-07-13
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
assigned_role: backend-engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source: [v2_engine_venue_buildout_2026_06_15.md follow-up, Phase E1 finding 2026-06-15]
sequential: false
---

# Deeper-Than-L5 Order Book Capture

> **Split out 2026-07-13** from [`v2_engine_venue_buildout_2026_06_15.md`](v2_engine_venue_buildout_2026_06_15.md)
> Follow-ups section. `MarketMakingQueueMicrostructureEngine` (strategy-service@257df34a) already consumes
> `queue_position_bid`/`queue_position_ask` and degrades honestly (no quote) when they're absent — this plan is purely
> the upstream data build; do NOT touch the engine itself.

## Ground truth — canonical shape, do not fork a parallel schema

- Target schema: `CanonicalBookMicrostructure`
  (`unified-api-contracts/unified_api_contracts/canonical/domain/market/microstructure.py`) ALREADY declares
  `queue_position_bid`/`queue_position_ask`/`book_depth_levels` as fields — they are honest-absent on the shipped L5
  feed, not missing from the schema. This plan populates existing fields, it does not add new ones.
- Target data_types: `queue_position` and `depth_of_book_10` — these EXACT names are already registered in
  `unified-api-contracts/unified_api_contracts/registry/data_type_capability.py` with
  `live_capable=False, batch_capable=False` (Phase D part (a) of the parent plan). This plan's job is to make that flip
  to `True` become honest, by building the capture that backs it — do not rename or duplicate these data_types.
- Source convention: the existing `mtds_microstructure` `COMPUTED_SOURCE` (mirrors `greeks_service`,
  `SOURCE_PRIORITY[("cefi","queue_position"|"depth_of_book_10"|"order_flow_imbalance")] = ["mtds_microstructure"]`)
  already exists and derives from the venue's own `book_snapshot_5` shard — extend
  `derived/book_microstructure_compute.py` in MTDS to consume a deeper book input, do not invent a second
  computed-source name.
- **Canonical path/bucket rules (mandatory, no exceptions)**: every parquet write carries the
  `pipeline_mode = {mode}_{source}[_{transport}]` hive-partition key LEFT of `asset_group=`
  (`codex/02-data/pipeline-mode-partition.md`); every bucket lookup goes through
  `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` — never an inline `gs://` path; GCS
  object ops (copy/delete/describe) go through UTL `gcs_copy_object`/`gcs_delete_object`/`gcs_describe_object`, never a
  `gcloud`/`gsutil` subprocess.
- Target venues: the 9 CeFi venues currently carrying `book_snapshot_5` (Binance-FUT/SPOT, OKX-FUT/SPOT/SWAP, Bybit,
  Deribit, Coinbase-SPOT, Upbit) — use their EXACT existing canonical `VENUE-KIND` registry keys, do not introduce a new
  casing/naming variant.

## Todos

- [ ] [SCRIPT] P2. Per venue in the 9-venue `book_snapshot_5` set, confirm whether its public API exposes a deeper
      order-book depth (L10/L20/full-L2) beyond the L5 already captured — this is a real per-venue API capability check,
      not assumed uniform. Document which venues can and cannot go deeper; honest gaps for any venue that genuinely
      can't are acceptable, do not force a fake depth. Repo: market-tick-data-service (research + doc).
- [ ] [DATA] P2. For each venue confirmed capable, extend the live capture (or add a new deeper-book live handler
      alongside the existing L5 one) to pull the deeper book. Reuse the existing `book_snapshot_5` connector pattern per
      venue — do not fork a new connector framework.
- [ ] [SCRIPT] P2. Extend `market-tick-data-service/.../derived/book_microstructure_compute.py`
      (`compute_book_microstructure`) to populate `queue_position_bid`/`queue_position_ask`/`book_depth_levels` from the
      deeper book input when present, keeping the existing L5-only honest-absence path unchanged for any venue still
      capped at L5. Repo: market-tick-data-service.
- [ ] [SCRIPT] P2. Flip `queue_position` + `depth_of_book_10` to `live_capable=True` (and `batch_capable=True` if a
      batch/replay path is also built) in `data_type_capability.py`, scoped ONLY to the venues that actually ship
      deeper-book data — do not blanket-flip venues still capped at L5. Repo: unified-api-contracts.
- [ ] [SCRIPT] P2. Extend `features-service/.../book_microstructure_feature_extractor.py`
      (`extract_book_microstructure_feature_dict`) to surface `queue_position_bid`/`queue_position_ask`/
      `book_depth_levels` when present — the honest-absence behavior for capped venues must be preserved exactly as
      today. `formula_version=1` on any new derived keys. Repo: features-service.
- [ ] [SCRIPT] P2. Connectivity-test the new deeper-book path with a small bounded live pull per capable venue (mirrors
      the existing `book_microstructure_connectivity_check.py` pattern) — proves the pipeline, is NOT a backfill. Repo:
      market-tick-data-service.
- [ ] [SCRIPT] P2. Do NOT flip `MarketMakingQueueMicrostructureEngine`'s registration here — that stays in the parent
      plan's Phase E1, gated on this data landing AND a passing `GroupBRunner` backtest (which needs historical
      deeper-book replay, still no backfill authorised). This todo is DONE when the feed is honestly live for the
      capable venues, not when the engine registers.

## Progress Log

(loop handoff lands here)
