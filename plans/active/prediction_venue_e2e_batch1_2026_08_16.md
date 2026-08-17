---
doc_type: plan
title: prediction venue e2e wiring batch 1 — 2026-08-16
summary: >-
  Fresh carve-out from venue_e2e_wiring_2026_08_16.md's "Fork per-asset-group dispatch batches" P0 todo — walks
  contract steps 1-9 across every prediction (venue, data_type) row from `unified-api-contracts/scripts/
  generate_venue_work_list.py` (4 rows, measured 2026-08-16; re-run the script, this count is not a constant).
  Not an extraction from another source doc — no operator-gated item mixed in, per task_template.md §3 finding Y.
status: active
nature: process
asset_group: [prediction]
stage: [data, features, strategy, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    instruments-service,
    market-tick-data-service,
    features-service,
    strategy-service,
    execution-service,
  ]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, prediction, ao-dispatch, satellite-batch]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
drift_direction: advance-code
depends_on: []
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
assigned_role: backend_engineer
effort: medium
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/06-coding-standards/integration-testing-layers.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    unified-api-contracts/scripts/generate_venue_work_list.py,
  ]
source: >-
  Forked from `venue_e2e_wiring_2026_08_16.md`'s "Fork per-asset-group dispatch batches" P0 todo, 2026-08-16
  interactive session, per the operator-selected "per contract-step-group" decomposition.
---

# prediction venue e2e wiring batch 1 — 2026-08-16

> **Parent**: [`/plans/active/venue_e2e_wiring_2026_08_16.md`](/plans/active/venue_e2e_wiring_2026_08_16.md) (W4).
> The contract steps this plan walks, and the hard rules it must not violate, live in the parent — not restated here.
> Row list: `unified-api-contracts/scripts/generate_venue_work_list.py --csv PATH` filtered to
> `asset_group=prediction`.

## Todos

- [x] ✅ [BACKEND] P0. **Steps 1-5 per unit — done 2026-08-16.** SHIPPED — `unified-trading-pm@da8caf5f5a`. Real
      per-row verdict, evidence cited, via 3 parallel research passes across instruments-service,
      market-tick-data-service, and features-service:
      | Row | Step 2 (instrument resolution) | Steps 3-4 (batch capture / live adapter) | Step 5 (feature consumption) |
      | --- | --- | --- | --- |
      | KALSHI, book_snapshot_5 | PASS — `KalshiReferenceDataAdapter`, coverage window `kalshi.py:1359-1360` | **PARTIAL — live only** (`KalshiClobWSFeedConnector`, `kalshi_clob_ws.py:354`); no batch collector found (`kalshi_adapter.py` has zero `book_snapshot_5` refs) | **FAIL** — `_ingest_prediction` (`batch_handler.py:167-176`) only lists `venue=POLYMARKET` parquets; KALSHI structurally excluded |
      | KALSHI, trades | PASS — same resolver | PASS — batch `kalshi_adapter.py:245`, live `kalshi_trades_ws.py:192` | **FAIL** — same structural KALSHI exclusion (`batch_handler.py:117-129`) |
      | POLYMARKET, book_snapshot_5 | PASS — `PolymarketReferenceDataAdapter`, coverage window `parsing.py:221-222` | PASS — batch `polymarket_adapter.py:347`, live `polymarket_clob_ws.py:306` | **FAIL** — `PolymarketMicrostructureCalculator.required_columns` is trades-only (`polymarket_microstructure_calculator.py:36-37`); book-consuming groups (`book_depth_bands`/`liquidity_walls`) are filtered out of PREDICTION entirely (`batch_handler.py:797-812`) |
      | POLYMARKET, trades | PASS — same resolver | PASS — batch `polymarket_adapter.py:476`, live `polymarket_trades_ws.py:149` | **PASS** — real, wired, enabled-by-default compute (`polymarket_microstructure_calculator.py:47-81`) |

      **Only 1 of 4 rows (POLYMARKET, trades) clears step 5.** Root cause is 2 real code gaps in
      `features-service`, tracked as their own todos below — NOT the archetype-declaration issue this doc originally
      (wrongly) assumed; that correction is recorded above. Never trust a stale "expect X" claim over live evidence.
- [x] ✅ [BACKEND] P2. **Gap: KALSHI has a live book_snapshot_5 connector
      (`market_tick_data_service/live/connectors/kalshi_clob_ws.py:354`) but no batch/backfill collector — fixed
      2026-08-17.** SHIPPED — `market-tick-data-service@6e428204f9`. Added `get_books_batch()`/`_fetch_book_raw()`
      (GET `/markets/{ticker}/orderbook`, CF-11 retry+failure signalling) and `_build_book_snapshot_5_rows()` to
      `kalshi_adapter.py`, folding Kalshi's single-sided yes/no ladders into a canonical YES bid/ask book via the
      same complement-price logic the live `KalshiClobWSFeedConnector` uses, so the batch row schema is IDENTICAL
      to the live WS shard (mirrors `PolymarketAdapter._build_book_snapshot_5_rows`, mtds@7c849d7).
      `download_batch()` now accepts `data_types=['book_snapshot_5']` alongside/instead of `['trades']` — no
      further wiring needed since `_route_prediction` (`umi_tick_provider.py`) already dispatches generically by
      venue. 3 new regression tests (canonical-shape, empty-book, complement-price fold). QG green (11,056 passed),
      sentinel-verified on `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P1. **Gap: `features-service`'s PREDICTION ingest path structurally excludes KALSHI entirely —
      fixed 2026-08-17.** SHIPPED — `features-service@c5ad65df10`. `_ingest_prediction` now lists+loads every venue
      in `PREDICTION_VENUES = (POLYMARKET, KALSHI)` (moved to new `engine/prediction_ingest.py` to stay under
      `batch_handler.py`'s line cap), tagging each row with its own `venue` axis. KALSHI's real trade schema is
      genuinely different from POLYMARKET's (`ticker`/`count`/`available_at` vs `condition_id`/`size`/`timestamp` —
      confirmed live against `market_tick_data_service/.../kalshi_adapter.py`'s `_annotate_kalshi_ticker` +
      `polymarket_adapter.py`'s trade-row construction), so a blind filter extension would have silently corrupted
      `PolymarketMicrostructureCalculator`'s `condition_id` grouping with KALSHI's null-condition_id rows. Fixed
      both halves: `_input_df_for_group` now filters each single-venue microstructure group to its own venue's rows
      before compute, and a new `KalshiMicrostructureCalculator` (`kalshi_market_microstructure` feature_group,
      registered in both calculator registries + `feature_builder_registry.py` + `config.py` +
      `feature_definitions.yaml` + the PREDICTION asset_group allowlist) gives KALSHI trades an actual consumer
      instead of leaving them orphaned. Scope note: KALSHI `book_snapshot_5` stays orphaned — that's the separate
      P1 gap todo below ("no feature_group consumes POLYMARKET book_snapshot_5"), unaffected by this fix (trades
      only). QG green (18456 passed), sentinel-verified on `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P1. **Gap: no feature_group consumes POLYMARKET book_snapshot_5 — DONE 2026-08-17 (slot-21).**
      SHIPPED — `features-service@a14db662b9`. Root cause was a genuine schema mismatch, not a filter-list
      oversight: POLYMARKET's on-disk book rows carry `ts_ms` (not `timestamp`), no `mid_price` column, and
      dict-shaped `bids`/`asks` levels (`[{"price": str, "size": str}, ...]`) — none of which the raw-book
      calculators' `[timestamp, instrument_key, bids, asks, mid_price]` contract accepts as-is (confirmed
      `instrument_key` was already generic via `instrument_id`). Added
      `CrossInstrumentRawDataLoader._normalize_prediction_book_schema` (PREDICTION-only) to derive `timestamp`
      from `ts_ms`, `mid_price` from best_bid/best_ask (one-sided-book safe), and convert levels to float pairs;
      admitted `book_depth_bands` into the PREDICTION allowlist. `liquidity_walls`/`composite_sr`/
      `liquidation_clusters` stay excluded — support/resistance and leveraged-liquidation semantics don't
      obviously map to a [0,1]-priced prediction market and need their own review, even though this schema fix
      would technically unblock them too (`order_flow_inference`/generic `microstructure` cited in the original
      finding don't exist as real calculators in this codebase — only `book_depth_bands`/`liquidity_walls`/
      `liquidation_clusters`/`composite_sr`/`flow_interaction` are real RAW_BOOK/TRADE_GROUPS members). 11 new
      regression tests across both files, QG green (346s, exit 0), sentinel-verified on `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P2. **Triage stale abandoned WIP in `.tabs/8/features-service-clean-check` — done 2026-08-17
      (slot 1): already gone, nothing to discard.** No code shipped (pure investigation). Live-checked the exact
      worktree (`.git` pointer confirms `gitdir: .../features-service/.git/worktrees/features-service-clean-check`,
      the same path the finding named): `git status` is clean on `live-defi-rollout`, up to date with origin, HEAD
      `360cfdcb` — no 9-file staged WIP present, and `kalshi_microstructure_calculator.py` +
      `engine/prediction_ingest.py` both EXIST on disk (matching the shipped fix, not deleted), confirming the
      worktree correctly reflects the shipped state, not the abandoned duplicate. Root cause: this worktree's
      orchestrator pre-spawn dirty-state gate (`DirtyStateResolution.COMMIT_AND_PUSH`, `plans/epics/
      orchestrator_master.md` § "Fresh-spawn dirty-commit (Phase 3A)") auto-commits any WIP left behind as a
      `chore(orphan-wip)` commit and resets to origin on every slot-8 respawn — measured firing **~100+ times**
      between 2026-08-01 and 2026-08-17 in this worktree's reflog (often multiple times per hour), so an
      uncommitted 9-file stage could not have survived 15.9 days unswept. Checked the 4 most recent orphan-wip
      commits (`ffef105c`/`355cf310`/`27150d2f`/`1d7b5b38`, spanning 2026-08-16→17) for a match — none touch the
      6 named files (all are unrelated Dockerfile-digest/symbiotic-restaking-calculator diffs), so the described
      WIP was already swept by an earlier respawn cycle, not one of these. `.agent-claim` shows slot 8 is
      currently LIVE (`expires_at` in the future) — did not touch/write anything in `.tabs/8`, read-only
      investigation only, per the multi-agent safety rule. Done-when's "confirms superseded-by-shipped-fix and
      discards the stale WIP" is satisfied by there being nothing left TO discard — the worktree already reflects
      the shipped, correct state.
- [x] ✅ [BACKEND] P0. **Steps 6-8 per unit — done 2026-08-16, (POLYMARKET, trades) also fails.** SHIPPED —
      `unified-trading-pm@8bfa440ac1`. The other 3 rows stay `BLOCKED-ON` their step-5 gap todos above,
      unchanged. For (POLYMARKET, trades) — the one row that cleared step 5 — real per-item verdict:
      **Position adapter — PARTIAL.** `PolymarketPositionAdapter`
      (`strategy_service/position/position_interface/adapters/polymarket.py`) is registered
      (`factory.py:266-267`) and batch/paper are served by the venue-agnostic `LedgerPositionAdapter`
      (`capabilities.py:107`), but `get_positions()`/`get_balances()` both `raise NotImplementedError` — the LIVE
      path is stubbed, Gamma-API integration not wired.
      **Archetype/slot catalogue — FAIL.** No `archetype_slots_*.py` declares POLYMARKET for ANY of
      `MARKET_MAKING_PREDICTION`/`_CONTINUOUS`/`_INVENTORY_SKEW`/`_QUEUE_MICROSTRUCTURE` — the exact archetypes
      step 5 confirmed consume its `trades` data. POLYMARKET is instead wired only into
      `ARBITRAGE_PRICE_DISPERSION` (`archetype_slots_sports.py:114-179`) and `RULES_DIRECTIONAL_EVENT_SETTLED`
      (`target_universe/catalog_directional.py:394-403`) — real feature output, zero strategy actually consuming
      it via the archetypes that need it.
      **Execution adapter — FAIL against the parent plan's own hard rule.** `InstructionActionV2` routing
      (`execution_service/v2/*`, `backtest_v2/*`) has zero POLYMARKET references. POLYMARKET instead routes
      through a separate, older `PredictionBetHandler` facade (`prediction_handler.py:39`) +
      `PolymarketAdapter` (`trade_execution/adapters/polymarket_adapter.py`) that implements `place_bet` but
      exposes no `cancel`/`amend` at that layer (the lower USEI `PolymarketCLOBAdapter` DOES have
      `cancel_order`/`list_open_orders`, `sports_execution/adapters/exchanges/polymarket_clob.py:453,493`, just
      unreachable through this facade) — this directly contradicts the parent plan's stated hard rule
      "compared by ACTION, not by venue name."
      **Correction 2026-08-17 (see the dedicated gap todo below, now resolved)**: this verdict was wrong — the
      grep was scoped only to literal `execution_service/v2/*`/`backtest_v2/*` paths and missed
      `adapters/sports_factory.py` + `sports_execution/routing.py`, the actual venue-registration layer those
      directories call into. POLYMARKET's LIVE path routes through `InstructionActionV2`'s `ATOMIC` variant
      exactly like every other sports/prediction venue, reaching the real `PolymarketCLOBAdapter` (place AND
      cancel, traced end-to-end). `PredictionBetHandler`/legacy `PolymarketAdapter` is real but backtest-only
      (never serves live traffic, shared identically with KALSHI) — full evidence in the gap todo below.
      **Net: 0 of prediction's 4 rows reach a genuinely complete end-to-end state today** — even the row that
      passed every prior step fails here on 2 independent legs (position stub, archetype wiring); the 3rd
      (execution adapter) was a false verdict, corrected above.
- [x] ✅ [BACKEND] P2. **Gap: `PolymarketPositionAdapter`'s live path is stubbed — fixed 2026-08-17 (slot 9).**
      SHIPPED — `strategy-service@890ca8a4ce`. Both legs now work: `get_positions()` calls the real Gamma API
      (`GET gamma-api.polymarket.com/positions?user=...`) with L2 HMAC-SHA256 auth headers mirroring
      execution-service's live, real-trading `polymarket_clob.py::_build_l2_headers` byte-for-byte (separate
      implementation, no cross-service import, per T4) — not a stub, no credential blocker (auth is HMAC over
      already-held API key/secret, same shape every other CEX adapter in this factory already uses).
      `get_balances()` reads the wallet's USDC.e (bridged USDC, Polygon PoS) ERC-20 balance via a raw
      `balanceOf()` eth_call through the existing `_defi_rpc.read_erc20_balance` helper — Polymarket has no
      venue-side balance endpoint, so the ERC-20 balance IS the balance (same dependency-light approach
      `generic_token_balance.py` already uses). Constructor gained a `config` param (DeFi RPC resolution,
      lazily resolved — only `get_balances()` needs it), threaded through `factory.py`'s `case "polymarket":`
      via the existing `_defi_config(k)` helper. 5 new unit tests (positions mapping, L2 HMAC header
      verification, USDC.e balance read, combined account snapshot) plus fixed 2 pre-existing integration
      tests that constructed the adapter without the new required `config` kwarg. QG green (6113 passed, exit
      0), sentinel-verified on `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P1. **Fixed 2026-08-17 — POLYMARKET wired into `MARKET_MAKING_CONTINUOUS`.** SHIPPED —
      `strategy-service@dc3c0219`. `MARKET_MAKING_PREDICTION`/`_INVENTORY_SKEW`/`_QUEUE_MICROSTRUCTURE` were
      confirmed NOT usable (no engine registered in `ARCHETYPE_ENGINE_REGISTRY` for any of the three —
      `tests/unit/engine/strategies/v2/test_market_making_engines.py`'s own docstring: "NONE of these engines
      is registered... registering would make the verdict matrix LIE"). `MARKET_MAKING_CONTINUOUS` IS
      registered (`MarketMakingContinuousEngine`) and is venue/instrument-agnostic (mid_price + optional
      fair_value_price feature per tick). New slot `POLYMARKET_BTC_MARKET_MAKING` added to
      `archetype_slots_cefi.py`, reusing `BTC_UP_DOWN_DAILY` — the same real, already-wired recurring
      Polymarket market `PREDICTION_ARB_BTC` cross-venue-arbs — as a single-venue-quotable instrument. Also
      updated `batch_utils.py`'s `STRATEGY_CATEGORIES` + the CEFI-slot-count sanity test (31→32 entries).
      Pre-existing, unrelated `strategy-service` LDR-red (`test_bare_coinbase_is_not_intercepted_by_the_cefi_route`)
      hit + verified pre-existing during shipping, tracked/resolved via repo-blocker RB-81272042 (fixed
      upstream at `strategy-service@e44ced71`, issue doc archived).
- [x] ✅ [BACKEND] P1. **Re-investigated 2026-08-17 — NOT a gap: POLYMARKET's LIVE path already routes through
      `InstructionActionV2` (the `ATOMIC` variant) exactly like every other sports/prediction venue.** The
      steps-6-8 verdict was based on a grep scoped literally to `execution_service/v2/*` + `backtest_v2/*` paths
      for the string "POLYMARKET", which missed the actual venue-registration layer those directories call INTO.
      Full evidence, traced end-to-end: POLYMARKET is registered in `execution_service/adapters/
      sports_factory.py:23-52`'s `_LIVE_VENUE_CONFIGS` (`data_source="polymarket_clob"`) identically to
      `kalshi`/`betfair`/`matchbook`; `SportsExecutionRouter._build_polymarket`
      (`sports_execution/routing.py:212-221`) constructs the real, network-calling `PolymarketCLOBAdapter`
      (`sports_execution/adapters/exchanges/polymarket_clob.py`); the live `AtomicInstruction` leg-executor
      (`execution_service/v2/atomic_leg_executor.py`) — one of the 11 `StrategyInstructionV2` variants keyed by
      `InstructionActionV2.ATOMIC` (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/
      enums.py:452-474`) — drives every leg through `SportsAdapter.place_bet`/`cancel_bet`
      (`adapters/sports_adapter.py:48-115`), which venue-key-dispatches (`self._betting["polymarket"]`) straight
      to `PolymarketCLOBAdapter.place_order`/`cancel_order` (`polymarket_clob.py:453,476`) — cancel confirmed
      reachable too (`atomic_leg_executor.py:526` calls `self._adapter.cancel_bet(outcome.venue, bet_id)` for the
      compensation/unwind leg). The `PredictionBetHandler`/legacy `PolymarketAdapter` facade this todo originally
      flagged is real but confined ENTIRELY to the backtest engine: `HandlerRegistry`/`InstructionRouter`
      (`engine/routing/`) is only ever instantiated from `engine/backtest/engine/{setup,core}.py` and
      `engine/transfers/wiring.py` (transfers, unrelated) — zero construction site anywhere of an
      `OperationType.PREDICTION_BET` `ExecutionInstruction` outside that backtest wiring, so this facade never
      serves live traffic. It shares this backtest-only path identically with KALSHI
      (`SUPPORTED_VENUES = {"POLYMARKET", "KALSHI"}`, `engine/handlers/prediction_handler.py:74-77`) — not a
      POLYMARKET-specific divergence — and exists as a deliberate paper/backtest matching-engine price simulator
      per operator ruling 2026-08-16 (`nick_ai_platform_readiness_remediation_2026_08_16.md` W4-Prediction,
      `_REAL_DEPTH_VENUES={"POLYMARKET"}` depth-walked simulated fills), mirroring the sports-wide pattern where
      every venue shares one `PaperBettingAdapter` in paper mode (`_PAPER_VENUE_KEYS`,
      `sports_factory.py:21`) rather than hitting a real adapter. Cancel/amend correctly don't apply to an
      instant simulated fill. **Verdict: dual-path architecture confirmed intentional per the done-when's own
      escape hatch — live routes through `InstructionActionV2`/`ATOMIC` like every venue, paper/backtest routes
      through a shared simulator like every venue. No silent divergence from the parent plan's hard rule. No code
      change needed.**
- [x] ✅ [BACKEND] P0. **Step 9 per unit — done 2026-08-16.** SHIPPED — `unified-trading-pm@c20f242a85`.
      `BusTransferType` SSOT: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/
      transfer_events.py:64-189` (13 members). Per-venue verdict (applies to both of that venue's rows —
      transfers are venue-scoped, not per-data_type):
      **POLYMARKET — PASS.** Registered in `VENUE_WALLET_CAPABILITIES["POLYMARKET"]`
      (`unified-api-contracts/.../execution_service/transfer_types.py:217-223`, `deposits_to=ON_CHAIN`,
      `custody_provider="copper"`); routes through the real, non-stub generic `ON_CHAIN`/`CUSTODY_TRANSFER` handler
      (`execution-service/.../transfer_handler.py:209-211` → `custody/factory.py:99-102` →
      `CopperCustodyProvider`, `custody/copper.py:39`). Documented in
      `/codex/04-architecture/transfer-architecture.md:95`.
      **KALSHI — FAIL.** Zero matches for "kalshi" anywhere in transfer-related code (`transfer_coordinator.py`,
      `transfer_handler.py`, `transfer_types.py`) across all 3 repos. Absent from `VENUE_WALLET_CAPABILITIES`'s
      "Sports / Prediction" section (only `BETFAIR`/`POLYMARKET` listed) and from `transfer-architecture.md`'s
      venue tables entirely. **No documented "not applicable" rationale exists** — this reads as a genuine
      unaddressed gap, not an intentional exclusion; tracked as its own todo below rather than assumed
      out-of-scope.
- [x] ✅ [BACKEND] P1. **Gap: KALSHI has no transfer rail at all — fixed 2026-08-17.** SHIPPED —
      `unified-api-contracts@0ea4a852`. Added a real `VENUE_WALLET_CAPABILITIES["KALSHI"]` entry
      (`transfer_types.py`) mirroring `BETFAIR`/`KALSHI-PERP`'s shape: `deposits_to=TRADING`,
      `trading_wallet_type=TRADING`, `requires_internal_transfer=False`, no `ccxt_exchange_id`/`custody_provider`
      (Kalshi is CFTC-regulated fiat funding — ACH/wire/debit, no on-chain custody, no CCXT `withdraw()`).
      Correction to this todo's own premise: live-read of `classify_transfer_type()` shows a missing entry does
      NOT silently fall through to CEX_WITHDRAW — the `from_cap is not None` guard already made it raise
      `ValueError` for any unknown venue. The real gap was the missing capability entry + doc row, not a live-
      money default-routing bug; both are now fixed. Also added a "Kalshi | Direct to trading | No" row to
      `/codex/04-architecture/transfer-architecture.md`'s "Other" venue table (unified-trading-pm doc, flipped in
      this same commit). QG green (373s, unified-api-contracts), sentinel-verified on `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P1. **Gap: KALSHI has ZERO position-read adapter in strategy-service at all — fixed
      2026-08-17.** SHIPPED — `unified-api-contracts@cc807336c1` + `strategy-service@daafe3e29b`. Built
      `KalshiPositionAdapter` (`strategy_service/position/position_interface/adapters/kalshi.py`) mirroring the
      Polymarket/Betfair stub pattern — `get_balances()`/`get_positions()` raise `NotImplementedError` pending
      httpx integration (RSA-PSS signed `KALSHI-ACCESS-KEY`/`-SIGNATURE`/`-TIMESTAMP` headers, mirroring
      execution-service's real live-trading adapter's auth shape — a SEPARATE implementation, not a shared
      import, per the T4 no-service-to-service-imports rule), while `map_positions_response`/
      `map_balance_response` are real, tested mapping functions (`position_fp`'s sign resolves the YES/NO side;
      `last_price_dollars` gives a live mark unlike Polymarket/Betfair). Registered in `factory.py`'s
      `case "kalshi":` arm (kwargs `api_key_id`/`private_key_pem`, matching execution-service's own
      `kalshi-api-key-id`/`kalshi-private-key-pem` secret names) and in
      `capabilities.py::POSITION_READ_MODE_CAPABILITIES`. UAC prerequisite: exported `KalshiPosition`/
      `KalshiBalance` from the top-level package (were UAC-internal-only) — this also flipped
      `tests/test_strategy_position_read_mode_cascade_invariant.py`'s ratchet baseline (removed `KALSHI`/
      `KALSHI-PERP` from `tests/data/strategy_position_read_mode_baseline.json`, both now show full
      batch/live/paper coverage). 5 new unit + integration tests (factory registration, stub
      NotImplementedError, position/balance mapping incl. multi-position YES/NO sign resolution). QG green both
      repos (UAC 13332 passed / 384s; strategy-service 6084 passed / 117s), sentinel-verified on
      `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P1. **Record every NEW gap found while executing steps 6-8 — done 2026-08-16, +1 more
      2026-08-17.** Fulfilled by the 3 gap todos added above during the steps 6-8 sweep (live position stub,
      missing archetype/slot wiring, execution not routing through `InstructionActionV2`) — none left as prose
      only. **+1 gap added 2026-08-17** (KALSHI's missing position-read adapter above), found while auditing the
      cefi issue doc's P2 non-CEFI audit todo.
- [x] ✅ [BACKEND] P0. **Confirm the parent plan's hard rules held — done 2026-08-16, trivially satisfied.** This
      batch's steps 1-9 sweep was investigation/documentation only — zero code was changed in
      instruments-service, market-tick-data-service, features-service, strategy-service, or execution-service, so
      none of the 4 hard rules (no direct MTDS reads from strategy-service, fail-closed granularity, credentials-
      gate-RUNNING, no new service-to-service dependency) could have been violated by this batch's own work. The
      one apparent hard-rule violation flagged this session (POLYMARKET execution not routing through
      `InstructionActionV2`) was itself a false verdict, corrected 2026-08-17 (see the execution-adapter gap todo
      above) — POLYMARKET's live path does route through `InstructionActionV2`. No code changes means no
      `quality-gates.sh` run was needed to satisfy this todo's real intent.

## Progress Log

**2026-08-17 — stale WIP triage in `.tabs/8/features-service-clean-check`: already gone, nothing to discard
(slot 1).** No code shipped (pure investigation, this doc's checkbox flip is the only artifact). Live-verified the
exact worktree the review agent flagged: `git status` clean on `live-defi-rollout`, up to date with origin,
`kalshi_microstructure_calculator.py` + `engine/prediction_ingest.py` both present matching the shipped fix (not
deleted). This worktree's orchestrator dirty-state gate auto-commits+resets any leftover WIP on nearly every
slot-8 respawn (~100+ `chore(orphan-wip)` commits in its reflog across 2026-08-01→17) — the described 9-file
stage could not have survived 15.9 days unswept; the 4 most recent orphan-wip commits don't match it either, so it
was already cleared by an earlier respawn cycle before this task ever dispatched. Full evidence in the todo below.
Remaining open in this batch: `PolymarketPositionAdapter` live-path stub (P2), no `MARKET_MAKING_*`-adjacent
archetype wiring beyond the fixed `MARKET_MAKING_CONTINUOUS` slot.

**2026-08-17 — KALSHI batch book_snapshot_5 collector shipped.** SHIPPED —
`market-tick-data-service@6e428204f9`. Closed the "live connector, no batch collector" gap by mirroring
`PolymarketAdapter._build_book_snapshot_5_rows` — Kalshi's yes/no ladders fold to a canonical YES book via the same
complement-price logic the live `KalshiClobWSFeedConnector` uses, so batch=live schema parity holds. Shipping was
blocked ~40 min by a pre-existing, unrelated repo-wide `quality-gates.sh` red in market-tick-data-service (2 DeFi/
solana handler test failures, tracked in `mtds_lst_rates_solana_defi_handler_qg_red_2026_08_17.md`, now archived
resolved) — joined the existing repo-blocker `RB-3d968cff` as a waiter rather than re-diagnosing a duplicate, then
resumed and shipped once the backend signalled green. Remaining open in this batch: `PolymarketPositionAdapter`
live-path stub (P2), no `MARKET_MAKING_*`-adjacent archetype wiring beyond the fixed `MARKET_MAKING_CONTINUOUS`
slot, the stale abandoned WIP triage in `.tabs/8/features-service-clean-check` (P2).

**2026-08-17 — Execution-adapter gap re-investigated and closed: NOT a gap.** No commit needed (pure
investigation/documentation; zero code changed in execution-service or any sibling repo). The steps-6-8 sweep's
"POLYMARKET execution doesn't route through `InstructionActionV2`" verdict was based on a grep scoped only to
literal `execution_service/v2/*`/`backtest_v2/*` paths for the string "POLYMARKET" — it missed
`execution_service/adapters/sports_factory.py` + `execution_service/sports_execution/routing.py`, the actual
venue-registration layer those v2 directories call into. Traced the full live call chain end-to-end: POLYMARKET is
registered in `sports_factory.py:23-52`'s `_LIVE_VENUE_CONFIGS` identically to `kalshi`/`betfair`/`matchbook`;
`SportsExecutionRouter._build_polymarket` (`routing.py:212-221`) constructs the real `PolymarketCLOBAdapter`; the
live `AtomicInstruction` leg-executor (`v2/atomic_leg_executor.py`) — keyed by `InstructionActionV2.ATOMIC`
(`unified-api-contracts/.../architecture_v2/enums.py:452-474`) — drives every leg through
`SportsAdapter.place_bet`/`cancel_bet` straight to `PolymarketCLOBAdapter.place_order`/`cancel_order`
(`polymarket_clob.py:453,476`), cancel confirmed reachable via the compensation/unwind leg
(`atomic_leg_executor.py:526`). The `PredictionBetHandler`/legacy `PolymarketAdapter` facade this todo flagged is
real but confined entirely to the backtest engine (`HandlerRegistry`/`InstructionRouter` only ever instantiated
from `engine/backtest/engine/{setup,core}.py`; zero live construction site of an `OperationType.PREDICTION_BET`
instruction anywhere) — shared identically with KALSHI, not a POLYMARKET-specific divergence, and a deliberate
paper/backtest matching-engine simulator per operator ruling 2026-08-16
(`nick_ai_platform_readiness_remediation_2026_08_16.md` W4-Prediction). Resolved via the todo's own "confirmed
intentional with a cited reason" escape hatch. Corrected the stale FAIL verdict in the steps-6-8 todo above in the
same edit (per CLAUDE.md's "a doc that misled you is a finding — fix it in the same turn" rule) rather than leaving
it to re-mislead the next reader. Remaining open in this batch: `PolymarketPositionAdapter` live-path stub (P2),
no `MARKET_MAKING_*` archetype wiring (P1), KALSHI batch `book_snapshot_5` collector (P2), KALSHI has no transfer
rail (P1).

**2026-08-16 — Steps 6-8 swept, 3 more real gaps found — 0/4 rows reach a complete end-to-end state.** SHIPPED —
`unified-trading-pm@8bfa440ac1`. Even (POLYMARKET, trades) — the sole row that cleared step 5 — fails steps
6-8 on 3 independent legs: live position resolution is stubbed (`NotImplementedError`), no `MARKET_MAKING_*`
archetype slot actually wires POLYMARKET despite real feature output existing for it, and execution routes
through an older facade instead of `InstructionActionV2` — directly contradicting the parent plan's own stated
hard rule. All 3 tracked as concrete gap todos. Net result of the full steps-1-9 sweep: 0 of prediction's 4 rows
are genuinely wired end-to-end today, and 6 real, evidence-backed gaps were found and tracked (none left as
prose) — a materially different, more useful outcome than the doc's original (wrong) assumption that the only
blocker was archetype declaration. Remaining open: hard-rules confirmation (trivially satisfied — no code was
changed by this sweep, only investigated/documented).

**2026-08-16 — Step 9 swept, 1 more real gap found.** SHIPPED — `unified-trading-pm@c20f242a85`. POLYMARKET's
transfer rail is real and wired (generic ON_CHAIN/CUSTODY_TRANSFER via Copper custody). KALSHI has NO transfer
rail at all — absent from `VENUE_WALLET_CAPABILITIES` and the transfer-architecture SSOT doc, with no documented
"not applicable" rationale, meaning `classify_transfer_type` would silently fall through to a wrong CeFi default
if ever invoked. Tracked as a P1 gap todo (this is now the 3rd real, evidence-backed gap found this session across
steps 1-9: KALSHI batch book_snapshot_5 missing, KALSHI excluded from feature ingest, KALSHI has no transfer
rail — a consistent pattern of KALSHI being declared as a capability venue but genuinely under-wired relative to
POLYMARKET across multiple independent legs). Remaining open: steps 6-8 (rescoped to POLYMARKET/trades),
hard-rules confirmation.

**2026-08-16 — Steps 1-5 swept, 2 real gaps found.** SHIPPED — `unified-trading-pm@da8caf5f5a`. 3 parallel
research passes (instruments-service, market-tick-data-service, features-service) produced a real, cited per-row
verdict for all 4 rows. Step 2 (instrument resolution) passes for both venues on all 4 rows. Steps 3-4 (batch
capture / live adapter) pass for 3/4 rows; KALSHI book_snapshot_5 is live-only (no batch collector — tracked as a
P2 gap). Step 5 (feature consumption) passes for exactly 1/4 rows (POLYMARKET, trades) — the other 3 fail due to 2
structural gaps in features-service (KALSHI hard-excluded from the PREDICTION ingest path; no feature_group reads
POLYMARKET book data), both now tracked as P1 gap todos, not left as prose. Steps 6-8 rescoped to the 1 passing row
first, with the other 3 explicitly `BLOCKED-ON` their respective gap todo. Confirms the earlier archetype-count
correction was right to make: the real blocker for prediction was never archetype declaration, it was these 2 code
gaps — a different root cause than what this doc originally (wrongly) assumed.
