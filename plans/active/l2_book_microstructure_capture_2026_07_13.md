---
doc_type: plan
title: Deeper-Than-L5 Order Book Capture — populate queue_position_* for MARKET_MAKING_QUEUE_MICROSTRUCTURE
summary:
  Capture a deeper-than-L5 (L10/full-L2) order book for the 9 CeFi venues already carrying book_snapshot_5, derive
  queue_position_bid/ask + book_depth_levels through the canonical CanonicalBookMicrostructure shape, and flip their UAC
  capability rows from honest-absent to live_capable — unblocks MARKET_MAKING_QUEUE_MICROSTRUCTURE's backtest.
status: active
nature: process
asset_group:
  [cefi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # scoped entirely to 9 CeFi venues already carrying book_snapshot_5 (Binance/OKX/Bybit/Deribit/Coinbase/Upbit)

stage: [data, features]
repos: [market-tick-data-service, features-service, unified-api-contracts]
scope: [engineer]
tags: [strategy, v2-engine, market-making, orderbook, microstructure]
related: [/plans/active/v2_engine_venue_buildout_2026_06_15.md, /plans/active/cefi_consolidated_closeout_2026_07_18.md]
created: 2026-07-13
parent_epic: strategy_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
assigned_role: backend_engineer
drift_direction: advance-code
last_updated: 2026-07-13
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source: [v2_engine_venue_buildout_2026_06_15.md follow-up, Phase E1 finding 2026-06-15]
sequential: true
context_scope:
  [
    market-tick-data-service/market_tick_data_service/derived/book_microstructure_compute.py,
    features-service/features_service/cefi/book_microstructure_feature_extractor.py,
    /plans/archive/issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md,
    /plans/archive/issues/l2_book_microstructure_features_extractor_snapshot_path_retired_2026_07_14.md,
    /plans/active/v2_engine_venue_buildout_2026_06_15.md,
  ]
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
  (`/codex/02-data/pipeline-mode-partition.md`); every bucket lookup goes through
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
      `market-tick-data-service@15f5657b`**: COINBASE-SPOT (level2 was already uncapped, just slices 10 levels instead
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
- [x] ✅ [SCRIPT] P2. **RE-CREATE** (not extend) `market-tick-data-service/.../derived/book_microstructure_compute.py`
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
      canonical-shape/honest-absence pattern to preserve, then build fresh against the deeper-book input from todo 2. —
      **DONE, slot-13, `market-tick-data-service@019276470203`.** Recreated the module against a single generalized
      `BookInput` dataclass (bids/asks of any depth, not fixed to 5) rather than two parallel input types: the
      always-derivable fields (spread/relative_spread/imbalance/microprice) compute over whatever depth is present,
      identical to the pre-deletion L5 logic; `queue_position_bid`/`queue_position_ask` (resting size at the best
      bid/ask — matches `CanonicalBookMicrostructure`'s "aggregate resting size ahead" field definition) and
      `depth_levels_bid`/`depth_levels_ask` (full ladder as `CanonicalDepthLevel` rows, `order_count` honest-absent —
      this is an aggregated-depth capture, not order-by-order full-L2) populate ONLY when `captured_depth > 5`, i.e. a
      genuine capture from the todo-2 deeper-book connectors — an L5-only book takes the exact same honest-absence path
      as the deleted module. Wired into `derived/__init__.py` alongside the existing dividend_yield/rebase_rate exports.
      10 new unit tests (always-derivable fields, L5-depth honest absence at both <5 and exactly-5 levels, deeper-book
      population including one-sided deeper books, batch==live determinism) — all green, plus the existing 25 `derived/`
      tests unaffected. Full `quality-gates.sh` green (`ALL QUALITY GATES PASSED`, sentinel-verified at the shipped
      SHA). Shipped via `quickmerge --agent --files` after two mid-flight rebases onto concurrent peer pushes (this is a
      hot file under sustained multi-slot traffic) — each rebase re-verified via a fresh full QG run before the final
      push, never skipped.
- [x] ✅ [SCRIPT] P2. Flip `queue_position` + `depth_of_book_10` to `live_capable=True` (and `batch_capable=True` if a
      batch/replay path is also built) in `data_type_capability.py`, scoped ONLY to the venues that actually ship
      deeper-book data — do not blanket-flip venues still capped at L5. Repo: unified-api-contracts. — **DONE (partial,
      by design), slot-13, `unified-api-contracts@aab15c3e8c044c8b422240f4c22f24ec7e19a0ea`.** Split the two data_types
      instead of flipping both identically: `depth_of_book_10` is raw-captured directly by a per-venue WS connector
      (todo 2, `market-tick-data-service@15f5657b`) — flipped `live_capable=True` for the 5 genuinely capable venues
      (COINBASE-SPOT, BYBIT, DERIBIT, BINANCE-FUTURES, OKX-SWAP), stayed honest-absent for the other 4. `queue_position`
      is COMPUTED — `compute_book_microstructure` exists (todo 3) but **no handler dispatches it against a live feed and
      writes the result** (the pre-retirement handler was deleted in `a4fb3d13` and was never rebuilt — not covered by
      any todo in this plan). Flipping `queue_position` to `live_capable=True` right now would have been a false claim
      (a "hollow capability", the same failure mode the HARD CONTRACT above warns against for engine registration) —
      left it `live_capable=False` for every venue and added the todo below to close the gap. No `batch_capable` flip
      for either (todo 2 was live-only, no batch/replay path built). Along the way, fixed an unrelated pre-existing
      QG-red in this repo (`test_ws_cassette_coexistence.py` — 4 new WS connectors from
      `l2_book_depth10_missing_l5_prerequisite_venues_2026_07_13.md` were never added to `_CONNECTOR_TO_VENUE`, verified
      pre-existing via clean-tree `git stash` before fixing; adjacent, small, fixed in the same shipment rather than
      blocking on a repo-blocker). Full `quality-gates.sh` green.
- [x] ✅ [SCRIPT] P2. **NEW (discovered 2026-07-13, slot-13):** Build the handler + CLI wiring to dispatch
      `compute_book_microstructure` (market-tick-data-service, recreated todo 3) against the live `depth_of_book_10`
      feed (todo 2, 5 capable venues) and write the resulting `queue_position_bid/ask` + `depth_levels_bid/ask` rows —
      mirrors the deleted `book_microstructure_handler.py` pattern
      (`git show a4fb3d13^:market_tick_data_service/cli/handlers/book_microstructure_handler.py` for the shape to
      preserve: shard-isolated per-venue derivation, `record_captured(source="mtds_microstructure")`,
      `resolve_bucket_name(...)`, no raw `gs://`). This is the gap between todo 3 (pure compute function, done) and todo
      5 below (features-service extraction, which has nothing to read until this lands) — todo 5 is effectively blocked
      on this. Only after this lands should `queue_position`'s `data_type_capability.py` rows flip to
      `live_capable=True` for the 5 capable venues. Repo: market-tick-data-service. — **DONE, slot-11,
      `market-tick-data-service@ef467572`.** New `BookMicrostructureHandler`
      (`cli/handlers/book_microstructure_handler.py`): reads already-captured `depth_of_book_10` rows via
      `CanonicalParquetReader.read_shard()` for the 5 capable venues (+ per-venue instrument_type map — DERIBIT covers
      PERPETUAL+FUTURE, the rest PERPETUAL/SPOT only), converts rows to `BookInput`, calls
      `compute_book_microstructure`, writes via
      `record_captured(source="mtds_microstructure", pipeline_mode=PipelineMode.BATCH_MTDS_MICROSTRUCTURE)` with
      shard isolation (no `raise` in the per-venue/ per-instrument loop, `classify_venue_error`+`ADAPTER_FETCH_FAILED`).
      Honest gap (no manifest write) when no `depth_of_book_10` shard exists for a (venue, instrument_type, day) — never
      a fabricated `record_failed`/`empty`. **Known documented limitation**: the live `depth_of_book_10` WS connectors
      (all 5 venues, verified directly) write no per-row capture timestamp column, so `as_of` is stamped as the shard's
      day at 12:00 UTC (day-representative, not per-row-precise) — see the handler's module docstring. Wired as
      `--operation collect-book-microstructure --mode batch` in `cli/main.py`. 18 new unit tests (row parsing,
      shard-isolation, honest-gap routing), full `quality-gates.sh` green (sentinel-verified). Also flipped
      `queue_position`'s `data_type_capability.py` rows to `live_capable=True` for the 5 capable venues
      (`unified-api-contracts@4b945423`), mirroring `depth_of_book_10`'s own split — updated
      `test_book_microstructure_schema.py` accordingly. **Tracking-discrepancy correction**: the AO backlog had task
      `l2_book_microstructure_capture-008` (this todo) marked `done` with `done_sha=019276470203` — that SHA is actually
      todo 3's commit (the compute function only); no handler file existed in the repo before this dispatch. This plan
      doc's checkbox (the real SSOT) was correctly still unchecked; only the backlog DB row had drifted.
- [ ] [SCRIPT] P2. **BLOCKED-DATA-CORRECTNESS** — retagged from `BLOCKED-OPERATOR-DECISION` (2026-07-28): the
      architecture question this todo was originally waiting on is answered (issue doc
      [`issues/l2_book_microstructure_features_extractor_snapshot_path_retired_2026_07_14.md`](issues/l2_book_microstructure_features_extractor_snapshot_path_retired_2026_07_14.md),
      status resolved, Option C confirmed 2026-07-14) — see the resolution note further down in this same todo. What
      remains is a real technical/data-correctness dependency, not an operator decision: Option A (the MDPS
      column-pipeline extension this todo needs) is deferred until the `MarketMakingQueueMicrostructureEngine` backtest
      gate (todo 7 below) is actually picked up, and todo 7 is itself `BLOCKED-DATA-CORRECTNESS` on the CeFi live-WS
      capture pipeline being dormant (see todo 7's own note). Extend
      `features-service/.../book_microstructure_feature_extractor.py` (`extract_book_microstructure_feature_dict`) to
      surface `queue_position_bid`/`queue_position_ask`/ `book_depth_levels` when present — the honest-absence behavior
      for capped venues must be preserved exactly as today. `formula_version=1` on any new derived keys. Repo:
      features-service. **Blocked on the new handler-wiring todo above** — until it lands,
      `queue_position`/`depth_levels_*` are honest-absent from every captured row, so there is nothing new for this
      extractor to surface yet. **PREMISE CORRECTION (2026-07-14, slot-11,
      `plans/active/issues/l2_book_microstructure_features_extractor_snapshot_path_retired_2026_07_14.md`):** the
      handler-wiring todo above IS now done, but this todo's target — `extract_book_microstructure_feature_dict` reading
      raw `CanonicalBookMicrostructure` snapshot rows — no longer exists. It was DELETED as "no-tech-debt" by
      `features_read_book_columns_not_snapshots_2026_06_28.md` (complete, `features-service@d794b8c1`, 2026-06-29),
      which repointed the extractor at MDPS's precomputed bar-level candle columns
      (`unified_api_contracts.internal.domain.market_data_processing.book_summary_spec`, L1-L5 only, no
      `queue_position`/deeper-depth columns exist there). Surfacing `queue_position`/`depth_levels_*` in features now
      requires an ARCHITECTURE decision (extend MDPS's column pipeline to match — bigger scope, new plan — vs.
      reintroduce a parallel raw-snapshot read path, which reverses the 2026-06-28/29 decision) — not a same-shape
      "extend the extractor" edit. **RESOLVED 2026-07-14 (slot 14, `BLK-e5571ccf`): operator confirmed Option C** —
      leave `queue_position`/deeper `depth_levels_*` as MTDS-only data for now, no features-service consumer yet; Option
      B (parallel snapshot path) explicitly rejected; Option A (MDPS column extension) agreed as the right long-term
      path but NOT authorized as its own plan until the `MarketMakingQueueMicrostructureEngine` backtest gate (todo 7
      below) is actually picked up. See
      [`issues/l2_book_microstructure_features_extractor_snapshot_path_retired_2026_07_14.md`](issues/l2_book_microstructure_features_extractor_snapshot_path_retired_2026_07_14.md)
      (status: resolved) for the full option analysis + resolution. **Checkbox intentionally stays unflipped** — this
      todo's actual scope (extend the extractor) remains honestly undone/deferred, not completed; the decision that
      unblocks or permanently defers it is what's now resolved.
- [x] ✅ [SCRIPT] P2. Connectivity-test the new deeper-book path with a small bounded live pull per capable venue
      (mirrors the existing `book_microstructure_connectivity_check.py` pattern) — proves the pipeline, is NOT a
      backfill. Repo: market-tick-data-service. — **DONE, slot-11, `market-tick-data-service@bc9cd08c`.** Recreated
      `scripts/book_microstructure_connectivity_check.py` (deleted in `a4fb3d13`) adapted for the deeper-book path: live
      REST pull per capable venue (COINBASE-SPOT/BYBIT/DERIBIT/BINANCE-FUTURES/OKX-SWAP, each venue's public order-book
      snapshot endpoint, 20 levels requested) through `compute_book_microstructure`, asserting `captured_depth > 5` and
      that `queue_position_bid/ask`/`depth_levels_bid/ask` ARE populated (the opposite assertion from the retired
      L5-only check, which asserted honest-absence). **Premise note**: checked the availability manifest first
      (`read_availability_index`, not a raw GCS walk) — `depth_of_book_10` has **0 rows ever captured** in production;
      todo 2's live WS connectors (`market-tick-data-service@15f5657b`) have shipped but never actually been dispatched.
      A GCS-read connectivity test would have had nothing to read, so this hits each venue's REST endpoint directly
      (separate from the WS subscription used for live capture) — proves venue reachability + the derivation without
      depending on a prior live-capture run. **Ran live against real production APIs at authoring time — all 5 venues
      passed** (captured_depth=20 for every venue; sample: BINANCE-FUTURES imbalance=0.55/queue_position bid=7.012
      ask=2.083, DERIBIT bid=2510.0 ask=146280.0, etc. — full per-venue output in the session transcript). Exit 0.
      `quality-gates.sh` green (147s, sentinel-verified at the shipped SHA).
- **[SCRIPT] P2. EXTRACTED 2026-08-09 — moved to `cefi_satellite_ao_dispatch_batch13_2026_08_09.md` todo 2 for AO
  dispatch (parent_epic: strategy_master). See that doc for the live checkbox + evidence.** (Wire `depth_of_book_10`
  into the CeFi live event-log capture dispatcher — the source doc's own round5-cefi-question-resolution 2026-08-08
  entry below re-scoped this from an operator question to a bounded wiring gap.) Historical investigation trail retained
  below for context (do not re-derive): **BLOCKED-DATA-CORRECTNESS (historical)** — Do NOT flip
  `MarketMakingQueueMicrostructureEngine`'s registration here — that stays in the parent plan's Phase E1, gated on this
  data landing AND a passing `GroupBRunner` backtest (which needs historical deeper-book replay, still no backfill
  authorised). This todo is DONE when the feed is honestly live for the capable venues, not when the engine registers.
  **BLOCKED-DATA-CORRECTNESS (2026-07-14, slot-11):** verified the done-condition before flipping — it is NOT true.
  Manifest check found `depth_of_book_10` has 0 rows ever captured, AND — much bigger — the entire CeFi live WS
  tick-capture pipeline (every `live_*` pipeline_mode, every data_type, every venue) has produced no manifest rows since
  2026-06-29 (15 days stale); no running compute instance in the project looks like a persistent live-WS process. Filed
  [`issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md`](issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md)
  (P1, NOTIFY-OPERATOR class per the data-pipeline-correctness HARD RULE) — did NOT attempt to relaunch anything myself
  (needs operator context on the correct deployment target + whether this is an intentional pause). **Checkbox NOT
  flipped** pending that finding's resolution; the engine-registration guard itself is trivially satisfied (not
  touched), but that's not what this todo's done-condition actually gates on. **RE-VERIFIED STILL DORMANT (2026-07-16,
  slot-7):** re-dispatched 2 days after the issue doc's "intentional pause" resolution (`BLK-55d45a68`) — checked
  whether the pause had lifted before assuming it still applied. Bounded `read_availability_index` query over
  `2026-06-30..2026-07-16` on the CeFi tick bucket: 502,153 rows, **0** with a `live_*` pipeline_mode (all
  `batch_tardis`/`batch_aster`/`batch_hyperliquid`/`batch_extended`/`batch_deribit`). Bounded GCS prefix check on
  `day=2026-07-15` and `day=2026-07-16`: no `pipeline_mode=live_*` directory either day. `gcloud compute instances list`
  (project-wide): the identified relaunch target (`mtds-live-cefi-consolidated*`, per the issue doc's "Relaunch targets
  identified") has never been launched, in any state. Nothing has changed since 2026-07-14 — the intentional pause is
  still in effect, done-condition still false. **Checkbox NOT flipped** (still correct). No infra touched (read-only
  check).

      **RESOLVED — premise now stale (round5-cefi-question-resolution 2026-08-08).** The "is the pipeline dormant,
      should it be relaunched" question no longer needs an operator answer: it already WAS relaunched, on
      2026-07-31, and has run continuously since (confirmed via
      `plans/archive/issues/cefi_live_event_cold_compactor_oom_and_legacy_path_check_2026_08_07.md`, filed 2026-08-07
      — VM `mtds-live-cefi-consolidated-20260806-163414` running all 16 shards; warm capture flowing continuously
      since `2026-07-31T13:07Z`). The architecture also changed underneath this todo: live capture no longer writes
      the legacy `raw_tick_data/pipeline_mode=live_*` path this todo's own checks were probing (confirmed permanently
      empty by that same doc — it's now a retired path) — it writes an event-log spine instead
      (`gs://central-element-323112-events/live-events/warm/cefi/`). **But todo 7's actual done-condition is still
      false, for a different, now-precise, NON-operator reason**: live-checked 2026-08-08,
      `gcloud storage ls "gs://central-element-323112-events/live-events/warm/cefi/"` lists exactly 4 data_types —
      `book_snapshot_5`, `derivative_ticker`, `liquidations`, `trades` — **`depth_of_book_10` is NOT among them.** The
      deeper-book WS connectors this plan's todo 2 shipped (`market-tick-data-service@15f5657b`) were never wired
      into the new event-log-based live-capture dispatcher, so `depth_of_book_10` still has 0 live rows despite the
      general pipeline being healthy again. This is now a bounded, worker-determinable `[SCRIPT]` gap (wire
      `depth_of_book_10` into the live event-log capture path, mirroring how `book_snapshot_5`/`trades`/etc. are
      already wired), not an operator question — checkbox correctly stays unflipped, but the blocking reason changes
      from "ask the operator whether to relaunch" to "wire one more data_type into the already-running live
      capture." Not fixed in this pass (documentation-question audit, not an implementation dispatch).

## Progress Log

### 2026-07-17 — slot 10 (Todo 5 re-dispatched a third time — root-caused + fixed the repeat-dispatch bug)

Dispatched `l2_book_microstructure_capture-005` (todo 5) again — third occurrence (slot-11 2026-07-14, slot-7
2026-07-16, now slot-10). Re-verified the 2026-07-14 Option-C resolution before touching anything: read
`features-service/features_service/cefi/book_microstructure_feature_extractor.py` directly — still only exports
`extract_book_microstructure_from_candle_columns` (`formula_version=2`), no `queue_position_bid`/`queue_position_ask`/
`depth_levels_*` fields, docstring still states it "Replaces the retired snapshot path". Also grepped for any new
MDPS-scoped follow-up plan authorizing Option A — none exists (only the issue doc referencing it as future work).
Nothing has drifted; the decision is still Option C, still correctly deferred, checkbox correctly stays unflipped.

**Root-caused the actual repeat-dispatch bug** (both slot-11 and slot-7 flagged this as a backlog-hygiene gap needing
main/operator + orchestrator-VM `backlog.yaml` access — that's true for a _priority/prereq_ park, but there's a
mechanism that's fully in a worker's reach): read `agent-orchestrator/server/regen_backlog_from_plan.py`
`_parse_open_todos()` — it iterates the plan file **one raw line at a time** and `_UNCHECKED_RE` /
`_NON_DISPATCHABLE_RE` (the `BLOCKED-[A-Z]` / stretch-optional marker convention) only ever sees that **first physical
line** of a multi-line checkbox item; anything on a wrapped/indented continuation line is invisible to the parser. Todo
7 already had a `**BLOCKED-DATA-CORRECTNESS**` marker in its body (added 2026-07-14) — but it was 4 lines down from the
checkbox, not on the first line, so it never actually suppressed dispatch (confirmed via `task_still_dispatchable()`,
which keys off the exact same `_parse_open_todos()` output). Todo 5 had no marker at all.

**Fix applied (this dispatch, plan-doc edit only — no `backlog.yaml`/orchestrator-VM access needed):** moved a
`**BLOCKED-DATA-CORRECTNESS**` prefix onto todo 7's first checkbox line (same classification it already carried in-body,
just relocated to where the parser reads it), and added a new `**BLOCKED-OPERATOR-DECISION**` prefix onto todo 5's first
checkbox line (matches the taxonomy: it is genuinely waiting on a future operator authorization event — Option A being
picked up when the `MarketMakingQueueMicrostructureEngine` backtest gate is worked). Both todos stay fully visible in
the plan; `regen_backlog_from_plan.py`'s next tick should now exclude both from the dispatchable backlog
(`_parse_open_todos` skip + `task_still_dispatchable` no longer finding the brief among current open+dispatchable todos
prunes the existing queued rows too) instead of re-dispatching them to another slot.

Checkbox states unchanged (todo 5 still `[ ]`, correctly deferred-not-done; todo 7 still `[ ]`, correctly
blocked-not-done). This is a docs-only fix, ships via the `docs(plans):` carve-out (no code in this commit).

### 2026-07-14 — slot 11 (Todo 7 — verified done-condition false, filed a bigger NOTIFY-OPERATOR finding)

Dispatched task `l2_book_microstructure_capture-007` right after `/done`-ing todo 6. Todo 7's action item (don't touch
the engine registration) is trivially satisfied by not touching strategy-service. But its actual done-condition is "the
feed is honestly live for the capable venues" — checked that before flipping anything, rather than treating "the action
item is a no-op" as "the todo is done".

Widened the manifest check from todo 6's `depth_of_book_10`-only finding to `book_snapshot_5` (this plan's own stated
foundation) and then to every `live_*` pipeline_mode row in the CeFi manifest: **no live-mode manifest row anywhere
newer than 2026-06-29** (15 days stale at check time), across every data_type and venue, not just this plan's 5.
Cross-checked via bounded (non-recursive) GCS listing on 4 sampled recent days — only `pipeline_mode=batch_*`
directories present, zero `live_*`. `gcloud compute instances list` (project-wide) shows only backfill/batch VMs
running; no GKE clusters. This reads as the entire CeFi live tick-capture pipeline being dormant, not a
`depth_of_book_10`-specific gap — filed
[`issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md`](issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md)
(P1, NOTIFY-OPERATOR per the data-pipeline-correctness HARD RULE) rather than trying to relaunch anything myself (no
context on the correct deployment target or whether this is an intentional pause — real production infra, not a call to
make unilaterally).

**Checkbox NOT flipped** — the done-condition is honestly false. This plan-doc + issue-doc edit ships via the
`docs(plans):` carve-out (no code this dispatch). `/done`-ing this dispatch with the finding + issue doc as the evidence
— same posture as the todo 5 premise-correction earlier in this session.

### 2026-07-14 — slot 11 (Todo 6 shipped — deeper-book connectivity check)

Dispatched task `l2_book_microstructure_capture-006` (todo 6, connectivity test) right after `/done`-ing the Todo 4/5
dispatch above. Checked the availability manifest before writing anything (`read_availability_index`, bounded — NOT a
raw GCS walk, killed an accidental recursive `gsutil ls -r` mid-investigation before it completed): `queue_position` AND
`depth_of_book_10` both show **0 captured rows ever** — todo 2's live WS connectors are shipped but have never actually
been dispatched in production. Built `scripts/book_microstructure_connectivity_check.py` (recreated from the deleted
`a4fb3d13` version, adapted for the deeper-book path — see the todo's own checkbox above for full detail) hitting each
of the 5 capable venues' public REST order-book endpoints directly rather than depending on a prior live capture. Ran it
live against real production venue APIs — all 5 passed. Shipped `market-tick-data-service@bc9cd08c`, QG green,
quickmerged.

**Note for whoever picks up todo 7 / the parent plan's Phase E1 next**: the live WS `depth_of_book_10` capture (todo 2)
has never actually run — "the feed is honestly live for the capable venues" (todo 7's own done-condition) is NOT yet
true in the sense of continuous production capture, only in the sense that the code path is proven end-to-end (this
todo) and the capability registry is honestly flipped (todo 4). Whether that gap needs a dispatch-the-live-capture todo
before Phase E1 proceeds is a call for whoever picks up todo 7 — not addressed in this dispatch (out of this task's
scope).

### 2026-07-14 — slot 11 (Todo 4 shipped; Todo 5 premise-correction — BLOCKED-OPERATOR)

Dispatched task `l2_book_microstructure_capture-005` (brief: extend the features-service extractor, todo 5). Fresh-pull
confirmed the AO backlog had already marked the actual prerequisite (handler+CLI wiring, backlog id `-008`) `done` — but
with `done_sha=019276470203`, which is todo 3's commit (pure compute function only); no handler file existed in the repo
and nothing called `compute_book_microstructure` outside its own module/tests. The plan doc's own checkbox (the real
SSOT) was correctly still unchecked.

**Built the actual prerequisite (Todo 4)**: `BookMicrostructureHandler` in market-tick-data-service — reads captured
`depth_of_book_10` rows via `CanonicalParquetReader.read_shard()` for the 5 capable venues, derives `queue_position` via
`compute_book_microstructure`, writes via `record_captured(source="mtds_microstructure")`. Full detail + evidence in the
todo's own checkbox above. Shipped `market-tick-data-service@ef467572` + `unified-api-contracts@4b945423` (capability
flip), both quality-gates.sh green, both quickmerged to `live-defi-rollout`.

**Then attempted the actual assigned task (Todo 5)** and found it targets retired code: the extractor no longer reads
`CanonicalBookMicrostructure` snapshot rows at all (deleted "no-tech-debt" by
`features_read_book_columns_not_snapshots_2026_06_28.md`, complete since 2026-06-29) — it reads MDPS precomputed
bar-column candle fields (L1-L5 only, no `queue_position`). Filed
[`issues/l2_book_microstructure_features_extractor_snapshot_path_retired_2026_07_14.md`](issues/l2_book_microstructure_features_extractor_snapshot_path_retired_2026_07_14.md)
with the full option analysis (extend MDPS's column pipeline vs. reintroduce a parallel snapshot-read path vs. leave
`queue_position` MTDS-only for now) — recommending the third pending an operator/main decision on whether the MDPS
extension is worth a new plan. Did NOT unilaterally reintroduce the deleted snapshot-read pattern — that would reverse
an already-shipped, deliberate architecture decision without authorization.

**Checkbox state**: Todo 4 flipped `[x]`. Todo 5 NOT flipped — genuinely blocked on an operator/main architecture
decision, not a coding gap. This plan-doc + issue-doc edit ships via the `docs(plans):` carve-out (no code in this
commit). `/blocked` posted to the orchestrator citing the issue doc; `/done`-ing this dispatch with the Todo 4 shipment
as the evidence (the actual deliverable this session produced) since Todo 5 cannot honestly be marked done or continued
without that decision.

### 2026-07-14 — slot 14 (Issue-doc DESIGN todo resolved: Option C confirmed)

Dispatched task `l2_book_microstructure_features_extractor_snapshot_path_retired-001` (the issue doc's DESIGN todo).
Posted `/blocked` (`BLK-e5571ccf`) with the three options + recommendation (C now, A as real follow-up); operator
answered confirming **Option C** and explicitly rejecting Option B, with Option A deferred until the
`MarketMakingQueueMicrostructureEngine` backtest gate (todo 7) is actually picked up. Flipped the issue doc's DESIGN
todo `[x]`, set the issue doc `status: resolved` + `resolved_by`, added a Resolution section, and marked its P3
follow-up todo as not-authorized-today. Updated this plan's todo 5 note to record the resolution — todo 5's own checkbox
stays unflipped (the extractor work itself remains undone/deferred by design, not completed).

### 2026-07-16 — slot 7 (Todo 5 re-dispatched — resolution re-verified, no code change; flags a backlog-hygiene gap)

Dispatched task `l2_book_microstructure_capture-005` again (backlog id `-005`, todo 5). Re-verified the 2026-07-14
resolution still holds before touching anything: read the live extractor at
`features-service/features_service/cefi/book_microstructure_feature_extractor.py` directly — it is unchanged since
`features-service@d794b8c1`, still reads MDPS's precomputed bar-column path
(`extract_book_microstructure_from_candle_columns`, `formula_version=2`, docstring literally states "Replaces the
retired snapshot path"), still has no `queue_position_bid`/`queue_position_ask`/deeper `depth_levels_*` fields. Nothing
has drifted; Option C (confirmed 2026-07-14) still applies, Option B (parallel snapshot path) is still rejected. Did NOT
write any extractor code — that would reverse the operator's confirmed decision.

**Process finding (not a code gap):** todo 5's checkbox is _intentionally_ left `- [ ]` because the work is deferred,
not because it's undone-but-actionable — but `regen_backlog_from_plan.py` derives a dispatchable backlog task from any
unchecked checkbox with no way (from a worker slot) to distinguish "genuinely open" from "resolved-deferred pending a
future authorization event". This is the **second** time this exact backlog task (`l2_book_microstructure_capture-005`)
has been dispatched to a worker who then has to re-discover the 2026-07-14 resolution from scratch. Checked `RULES.md` §
"Park a task" — the fix (`priority: 999` + `priority_override: true` + a gating prerequisite condition on the task's
`data/config/backlog.yaml` entry) requires editing that file directly; it is **not** present in any
`.tabs/*/agent-orchestrator` slot clone (only `backlog.test.yaml` ships in git — the live `backlog.yaml` is
orchestrator-VM-local runtime state) and there is no `PATCH /api/backlog/{id}` surface to tune priority/prereqs remotely
(checked `/openapi.json` — only `GET/DELETE/reopen/blockers` exist on `/api/backlog/{task_id}`). So this park is
genuinely **out of worker-slot reach** and needs main/operator with orchestrator-VM access.

**Recommendation for main/operator**: park `l2_book_microstructure_capture-005` (`priority: 999` +
`priority_override: true` + a new `l2_book_microstructure_features_extractor_authorized` prerequisite seeded `false`)
until Option A (the MDPS column-pipeline extension) is authorized as its own plan per the 2026-07-14 resolution — or add
a `PATCH`-style backlog-tune endpoint so a worker slot can self-serve this pattern instead of re-dispatching into the
same resolved-deferred todo repeatedly. No operator action needed on the underlying technical question — that part is
already decided.

Checkbox stays unflipped (unchanged from 2026-07-14 — still correctly reflects deferred-by-design, not completed). This
is a docs-only progress-log update, ships via the `docs(plans):` carve-out (no code in this commit).

### 2026-07-16 — slot 7 (Todo 7 re-dispatched — pause re-verified still in effect; second repeat-dispatch this session)

`/done`-ing todo 5 (above) immediately handed out `l2_book_microstructure_capture-007` as `next_task` — the SAME
resolved-deferred pattern as todo 5, now on its second occurrence in one session. Todo 7's own done-condition ("the feed
is honestly live for the capable venues") was found false on 2026-07-14 (slot-11) and traced to an intentional CeFi
live-capture pause (issue doc `cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md`, `BLK-55d45a68`). Rather
than assume the 2-day-old resolution still held, re-checked fresh: bounded manifest query (`2026-06-30..2026-07-16`,
CeFi tick bucket) shows 0 `live_*` rows out of 502,153; bounded GCS prefix checks on `day=2026-07-15`/`07-16` show no
`live_*` directory; the identified relaunch VM (`mtds-live-cefi-consolidated*`) has never been launched in any state.
**Nothing has changed** — pause still in effect, done-condition still false, checkbox correctly stays unflipped. Full
detail in the todo's own checkbox note above.

**Backlog-hygiene pattern now confirmed twice in one plan**: both todo 5 and todo 7 are resolved-deferred-pending-an-
external-event todos whose checkboxes are correctly left unflipped, but `regen_backlog_from_plan.py` re-derives a
dispatchable task from them every cycle regardless, and no worker-slot-reachable mechanism exists to park either one
(see todo 5's note above — no `PATCH /api/backlog/{id}`, no `backlog.yaml` in any slot clone). Recommend main/operator
treat this as one backlog-hygiene fix covering both `l2_book_microstructure_capture-005` and `-007` rather than two
one-off findings — the same park recipe (RULES.md § "Park a task") applies to both, gated respectively on "Option A
MDPS-extension authorized" (todo 5) and "a fresh CeFi live manifest row lands" (todo 7, naturally self-clearing once the
migration completes — c.f. `/codex/02-data/honest-absence-downstream-handling.md` § "Reference incidents").

Docs-only update, ships via the `docs(plans):` carve-out (no code in this commit).

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - both todos are tagged
  BLOCKED-DATA-CORRECTNESS on the dormant CeFi live-WS capture pipeline; no worker can discharge them until that data
  lands.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries) -- swapped in the real capture/extractor
  source modules + the two blocking issue docs (both now ARCHIVED, corrected from the doc's own stale `issues/...`
  active-relative links) that the 2 open BLOCKED-DATA-CORRECTNESS todos actually gate on.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — both open todos carry a first-line
  BLOCKED-DATA-CORRECTNESS tag citing specific unresolved external/architecture dependencies. CAVEAT for next toucher: a
  same-day sibling doc (cefi_live_event_cold_compactor_oom_and_legacy_path_check_2026_08_07.md) found the CeFi live
  pipeline is alive again since 2026-07-31 (the "dormant since 06-29" framing todo 7 leans on is stale), but does NOT
  confirm depth_of_book_10 specifically (this plan's target data_type) is among the live shards — needs a narrow
  depth_of_book_10 manifest check before todo 7 is re-evaluated, not a full re-litigation.
- **round5-cefi-question-resolution 2026-08-08**: did exactly the narrow check the 08-07 caveat flagged —
  `gcloud storage ls "gs://central-element-323112-events/live-events/warm/cefi/"` lists 4 data_types
  (book_snapshot_5/derivative_ticker/liquidations/trades), no `depth_of_book_10`. Todo 7 stays unflipped but the "is the
  pipeline dormant, should it relaunch" operator-question framing is now retired — the pipeline IS alive (since
  2026-07-31); the remaining gap is a bounded technical one (wire `depth_of_book_10` into the new event-log live-capture
  dispatcher). See the todo's own annotation above.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid overall — todo 7 is now bounded per the
  round5 finding directly above (a scoped wiring gap, not an operator question), but todo 5 remains explicitly
  `BLOCKED-OPERATOR-DECISION` (Option A/MDPS-column-extension authorization gated on todo 7's backtest work actually
  being picked up — an explicit dated ruling, not re-litigated per this sweep's own rules). Whole-doc flip stays blocked
  per the HARD RULE. Cross-checked against `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` (today's independent
  full-corpus audit, authored before this same-day round5 update landed) — its "todo 7 similarly judgment-gated"
  characterization is now stale; todo 7's re-scoped bounded framing supersedes it. **Recommendation for the next
  `/ag-closeout-audit` cefi batch (batch11)**: extract todo 7 alone (wire `depth_of_book_10` into the live event-log
  capture dispatcher) into a satellite AO-dispatch item — not executed in this pass, same reasoning as the other
  extraction recommendations in this sweep.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — sole item gated by dated operator
  ruling BLK-e5571ccf (2026-07-14, issues/l2_book_microstructure_features_extractor_snapshot_path_retired_2026_07_14.md,
  status: resolved); step 1 of 3 now has a live AO-dispatch path (batch13 todo 2) but steps 2-3 remain un-authorized.
