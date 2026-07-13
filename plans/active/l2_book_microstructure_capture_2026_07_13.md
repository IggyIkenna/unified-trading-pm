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
last_updated: 2026-07-13
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source: [v2_engine_venue_buildout_2026_06_15.md follow-up, Phase E1 finding 2026-06-15]
sequential: true
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

- [x] ✅ [SCRIPT] P2. Per venue in the 9-venue `book_snapshot_5` set, confirm whether its public API exposes a deeper
      order-book depth (L10/L20/full-L2) beyond the L5 already captured — this is a real per-venue API capability check,
      not assumed uniform. Document which venues can and cannot go deeper; honest gaps for any venue that genuinely
      can't are acceptable, do not force a fake depth. Repo: market-tick-data-service (research + doc). — DONE
      `market-tick-data-service@4cf33fbe` (`docs/L2_BOOK_DEPTH_RESEARCH_2026_07_13.md`). **All 9 venues genuinely
      support deeper-than-L5 depth** — no honest capability gap on any venue (the constraint is auth/VIP-tier gating on
      some channels, not missing capability). Summary: Binance Futures/Spot → 20 (WS partial) / 1000-5000 (REST+diff),
      no gating; OKX Futures/Spot/Swap (unified v5 schema) → 400 levels (`books`), with `books50-l2-tbt`/ `books-l2-tbt`
      gated behind VIP4+/VIP5+ trading-fee tiers (medium-high confidence — OKX's SPA docs couldn't be rendered directly,
      corroborated via secondary sources); Bybit → 1000 levels (linear/inverse/spot), no gating; Deribit → 20 grouped
      (no auth) / unlimited raw (requires authenticated WS); Coinbase Spot → full L2 uncapped via `level2_batch`
      (no-auth); Upbit → 30-level hard cap, no gating. Full per-venue citations + todo-2 implementation targets (which
      channel/depth to actually pull, given gating) are in the doc. `quality-gates.sh` green (237s,
      `IGNORE_TIMEOUT=true`) after this repo saw 5 sentinel-invalidating rebases from sustained concurrent commit
      traffic across slots — sentinel verified at `4cf33fbe2fdaf29302a86960c27e471227203a92`.
- [x] ✅ [DATA] P2. For each venue confirmed capable, extend the live capture (or add a new deeper-book live handler
      alongside the existing L5 one) to pull the deeper book. Reuse the existing `book_snapshot_5` connector pattern per
      venue — do not fork a new connector framework. — **DONE for 5/9 venues, slot 8,
      `market-tick-data-service@ff479373`**: COINBASE-SPOT (level2 was already uncapped, just slices 10 levels instead
      of 5 off the same maintained state), BYBIT (`orderbook.200`, was `.50`), DERIBIT (`book.*.none.20.100ms`, was
      `.none.5.`), BINANCE-FUTURES (new `depth20@100ms` subscription), OKX-SWAP (new `books` channel — 400 levels,
      un-gated — with snapshot+update local-book reconstruction, unlike `books5`'s flat snapshot; does NOT validate
      OKX's optional per-frame checksum, flagged as a known limitation not hidden). All via the existing
      `data_type`-branching factory pattern (`WS_FEED_CONNECTOR_FACTORIES`), no new framework. 23 new unit tests,
      355/355 relevant tests green, 0 new basedpyright violations (verified file-by-file against the pre-change
      baseline). **Premise correction — 4/9 venues found to have NO live `book_snapshot_5` at all** (BINANCE-SPOT,
      OKX-FUTURES, OKX-SPOT, UPBIT are trades-only or batch-only live), discovered while tracing each venue's factory to
      extend it — filed as `issues/l2_book_depth10_missing_l5_prerequisite_venues_2026_07_13.md` (their own
      build-from-scratch scope, bigger than "extend", not silently rolled into this todo). Todos 3-5 below can proceed
      for the 5 done venues; the 4-venue gap is tracked separately and does not block them.
- [ ] [SCRIPT] P2. **RE-CREATE** (not extend) `market-tick-data-service/.../derived/book_microstructure_compute.py`
      (`compute_book_microstructure`) to populate `queue_position_bid`/`queue_position_ask`/`book_depth_levels` from the
      deeper book input when present, keeping the existing L5-only honest-absence path unchanged for any venue still
      capped at L5. Repo: market-tick-data-service. **Premise correction (2026-07-13,
      `plans/active/issues/l2_book_microstructure_capture_target_file_retired_2026_07_13.md`):** this file (+ its
      handler, CLI wiring, tests) was DELETED in commit `a4fb3d13` on 2026-07-07 (also on `main` via `917a8ccf`) when
      `order_flow_imbalance` was retired for "zero real consumers, zero production rows ever captured". It never had a
      deeper-book code path even before deletion (`git show a4fb3d13^:...` shows it consumed a fixed L5-capped
      `L5BookInput`, always honest-absent on deeper fields) — so this is new-construction on a deleted foundation, not a
      small addition to an existing file. Whoever picks this up: read the deleted file's last state via
      `git show a4fb3d13^:market_tick_data_service/market_interface/derived/book_microstructure_compute.py` for the
      canonical-shape/honest-absence pattern to preserve, then build fresh against the deeper-book input from todo 2.
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
