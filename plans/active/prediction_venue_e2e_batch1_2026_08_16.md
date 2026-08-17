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
- [ ] [BACKEND] P2. **Gap: KALSHI has a live book_snapshot_5 connector
      (`market_tick_data_service/live/connectors/kalshi_clob_ws.py:354`) but no batch/backfill collector** —
      `kalshi_adapter.py`'s `download_batch` is trades-only. Cannot backfill KALSHI order-book history; live-only
      capture means no historical replay/backtest for this data_type. Done-when: a batch collector exists (mirroring
      `PolymarketAdapter._build_book_snapshot_5_rows`, `polymarket_adapter.py:347`) or this is explicitly ruled
      out-of-scope with a cited reason.
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
- [ ] [BACKEND] P1. **Gap: no feature_group consumes POLYMARKET book_snapshot_5.**
      `PolymarketMicrostructureCalculator` is trades-only (`polymarket_microstructure_calculator.py:36-37`), and
      the generically-applicable book-consuming groups (`book_depth_bands`/`liquidity_walls`/`order_flow_inference`/
      `microstructure`/`flow_interaction`) are all filtered out of PREDICTION by
      `_filter_feature_groups_for_asset_group` (`batch_handler.py:797-812`) — real captured book data (batch+live,
      confirmed PASS above) is fully orphaned. Done-when: at least one feature_group reads POLYMARKET
      book_snapshot_5, or the gap is confirmed intentional with a cited reason.
- [ ] [BACKEND] P2. **Triage stale abandoned WIP in `.tabs/8/features-service-clean-check`** (found by a review
      agent 2026-08-17, 15.9 days stale, 9 files staged: deletes `kalshi_microstructure_calculator.py` +
      `prediction_ingest.py`; edits `batch_handler.py`/`config.py`/`orchestrator.py`/`feature_builder_registry.py`/
      `feature_definitions.yaml`/`test_batch_handler.py`). Looks like an earlier, abandoned attempt at the KALSHI
      PREDICTION-ingest P1 gap todo above — but that todo is already SHIPPED (`unified-trading-pm@fd06d1dee`-era
      fix ADDED `KalshiMicrostructureCalculator` + moved logic into a new `engine/prediction_ingest.py`), whereas
      this stale WIP stages DELETES of those exact two files. Strong signal this is a superseded, now-dangerous
      duplicate — committing it as-is would likely REVERT the shipped fix. Done-when: a fresh triage confirms
      superseded-by-shipped-fix and discards the stale WIP (`git stash`/reset, not a blind restore), OR a closer
      read finds the staged deletes target genuinely different dead code and the WIP is salvaged instead.
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
- [ ] [BACKEND] P2. **Gap: `PolymarketPositionAdapter`'s live path is stubbed**
      (`strategy_service/position/position_interface/adapters/polymarket.py`, `get_positions()`/`get_balances()`
      both `raise NotImplementedError`) — batch/paper work via the generic `LedgerPositionAdapter`, but no live
      Gamma-API integration exists. Done-when: live position/balance resolution works for POLYMARKET, or this is
      confirmed out-of-scope for the carve-out's contracted archetypes with a cited reason.
- [ ] [BACKEND] P1. **Gap: no `archetype_slots_*.py` wires POLYMARKET into any `MARKET_MAKING_*` archetype** —
      it's only declared for `ARBITRAGE_PRICE_DISPERSION`/`RULES_DIRECTIONAL_EVENT_SETTLED`, not
      `MARKET_MAKING_PREDICTION`/`_CONTINUOUS`/`_INVENTORY_SKEW`/`_QUEUE_MICROSTRUCTURE` — the archetypes step 5
      confirmed actually consume POLYMARKET's `trades` feature output. Real captured data, real computed
      features, zero strategy slot using them for the archetypes that need them. Done-when: POLYMARKET is added
      to at least one `MARKET_MAKING_*` archetype's slot declaration, or the omission is confirmed intentional
      with a cited reason.
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
- [ ] [BACKEND] P1. **Gap: KALSHI has no transfer rail at all** — absent from `VENUE_WALLET_CAPABILITIES`
      (`unified-api-contracts/unified_api_contracts/internal/domain/execution_service/transfer_types.py:210-223`)
      and from `/codex/04-architecture/transfer-architecture.md`'s venue tables, with no documented reason. Without
      a `VENUE_WALLET_CAPABILITIES` entry, `classify_transfer_type("KALSHI", ...)` falls through to a CeFi-
      withdrawal default despite Kalshi having no CCXT `withdraw()` support — a live-money correctness risk, not
      just a missing feature, if ever actually invoked. Done-when: either a real `VENUE_WALLET_CAPABILITIES` entry
      + working rail is added for KALSHI, or the exclusion is confirmed intentional (e.g. "Kalshi funds via its
      own bank/ACH UI, no in-system rail by design") and documented in `transfer-architecture.md`.
- [x] ✅ [BACKEND] P1. **Record every NEW gap found while executing steps 6-8 — done 2026-08-16.** Fulfilled by
      the 3 gap todos added above during the steps 6-8 sweep (live position stub, missing archetype/slot wiring,
      execution not routing through `InstructionActionV2`) — none left as prose only.
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
