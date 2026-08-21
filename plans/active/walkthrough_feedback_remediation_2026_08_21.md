---
doc_type: plan
title: Platform-external-API walkthrough — 2026-08-21 operator feedback remediation
summary: >-
  Executes the operator's 2026-08-21 feedback on platform-external-api-walkthrough.html. Carries the verified
  registry (T1), execution/transfer (T4) and presentation (T5) feedback clusters that could not be appended to the
  over-line-cap tranche plans, plus the ready-to-paste local worktree dispatch prompts. The refdata (T2) and
  strategy (T3) clusters live directly in their tranche plans. Every claim here was re-verified against repo HEAD
  2026-08-21 before being turned into a todo.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, execution-service, strategy-service, unified-trading-pm]
scope: [engineer]
tags: [code-readiness, walkthrough, client-artefact, feedback, registry, execution, presentation]
related:
  [
    /plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md,
    /plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md,
    /plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
    /plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 5
locked_by:
locked_since:
context_scope:
  [
    /plans/active/code_readiness_five_agent_coordinator_2026_08_19.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/06-coding-standards/quality-gates.md,
    unified-api-contracts/unified_api_contracts/registry/,
    execution-service/execution_service/,
  ]
supersedes:
superseded_by:
depends_on: [code_readiness_t1_contracts_library_externalapi_2026_08_19]
source: >-
  Operator feedback session 2026-08-21 on
  codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html — claims re-verified against
  repo HEAD by three parallel investigation agents before todo conversion.
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
---

# Walkthrough feedback remediation — 2026-08-21

> Execution order: registry cluster (T1 scope) and execution cluster (T4 scope) and strategy/refdata clusters
> (in-plan on T3/T2) run CONCURRENTLY in separate worktrees — different repos, no shared files. The presentation
> cluster (T5 scope) runs LAST, after the others land, so the artefact shows fixed reality. Then the re-audit.
> Operator rulings recorded 2026-08-21: (1) ALCHEMY-ONCHAIN is NOT a venue — it is a protocol/data-source (e.g.
> on-chain gas fees); (2) where multiple code paths exist, consolidate onto the SSOT/better version — the more
> configurable, higher-functionality, strategy/venue-AGNOSTIC one.

## Todos — registry cluster (T1 scope: unified-api-contracts)

- [ ] [BACKEND] P0. Bucket the 23 real declared-but-unbucketed venues into `VENUES_BY_ASSET_GROUP["defi"]`
      (AAVE_V3-SCROLL, AAVE_V3-ZKSYNC, COMPOUND-ETHEREUM, COMPOUND_V3-POLYGON, COMPOUND_V3-SCROLL,
      EULER_V2-ARBITRUM, MORPHO-{ARBITRUM,OPTIMISM,POLYGON}, MORPHOVAULTS-ETHEREUM, FRAX-ETHEREUM,
      IDLE-{ARBITRUM,POLYGON}, YEARN_V3-OPTIMISM, BEEFY-POLYGON, UNISWAP-ETHEREUM, PANCAKESWAP_V3-ARBITRUM,
      STARGATE-ETHEREUM, ACROSS-ETHEREUM, FLASHBOTS-ETHEREUM, LIFINITY-SOLANA, METEORA-SOLANA, PHOENIX-SOLANA).
      ALCHEMY-ONCHAIN — operator ruling 2026-08-21: NOT a venue, it is a protocol/data-source (e.g. on-chain gas
      fees) — remove it from `VENUE_DATA_TYPE_CAPABILITIES` as a venue token and re-home its capability under a
      data-source registry, do NOT bucket it. Closes the declared(201)-vs-bucketed(177) gap the walkthrough
      discloses as 192-vs-177 (count drifted +9 since its 2026-08-19 measurement). Source:
      `market_data_categories.py:2644` (dict), `:387` (buckets).
      **BLOCKED — premise stale, needs operator ruling 2026-08-21**: `VENUES_BY_ASSET_GROUP["defi"]` is not a
      literal list to append to — it's DERIVED (`list(dict.fromkeys(v for v in _ALL_DEFI_VENUES if
      _DEFI_VENUE_PHASE.get(v) == "live"))`, `market_data_categories.py` ~line 528). All 20 of the 23 named
      venues checked (AAVE_V3-SCROLL, AAVE_V3-ZKSYNC, COMPOUND-ETHEREUM, COMPOUND_V3-POLYGON,
      COMPOUND_V3-SCROLL, EULER_V2-ARBITRUM, MORPHO-ARBITRUM, MORPHOVAULTS-ETHEREUM, FRAX-ETHEREUM,
      IDLE-ARBITRUM, YEARN_V3-OPTIMISM, BEEFY-POLYGON, UNISWAP-ETHEREUM, PANCAKESWAP_V3-ARBITRUM,
      STARGATE-ETHEREUM, ACROSS-ETHEREUM, FLASHBOTS-ETHEREUM, LIFINITY-SOLANA, METEORA-SOLANA,
      PHOENIX-SOLANA — `defi_venues.py`) are already declared with `_DEFI_VENUE_PHASE == "pipeline"`, i.e.
      deliberately NOT counted "live"/IS-producible yet. "Bucketing" them means flipping pipeline→live, which is
      an IS-producibility/readiness call on 20 real venues, not a registry-hygiene fix — needs an explicit
      operator ruling on which of the 20 are actually ready, or this todo is mis-scoped and should be re-pointed
      at the honest-coverage denominator story instead. Left unflipped pending that ruling. The ALCHEMY-ONCHAIN
      re-home sub-item is separately scoped and equally not started in this pass (same blocker: budget).
- [ ] [BACKEND] P1. Converge the three DeFi venue sets to one coherent story: dedup `ALL_DEFI_VENUES`
      (`defi_venues.py:32` — 174 entries, 35 exact duplicates, 139 unique) and prune-or-capability the 18
      identities with no capability row (incl. the deliberately-cefi-reclassified CLOBs — annotate as
      cross-referenced, not missing). Target: 139/121/103 becomes explainable in one sentence per set, or the
      sets converge.
      **DEFERRED — not attempted this pass**: budget did not extend to a safe multi-file dedup + capability
      audit across `ALL_DEFI_VENUES`/`VENUE_DATA_TYPE_CAPABILITIES`/capability declarations; needs its own
      focused pass.
- [x] [BACKEND] P2. `VENUE_CHAIN_MAP` (`venue_constants.py:907`) — verified 2026-08-21: zero consumers outside
      UAC itself (wallet-grouping only, derives `SHARED_WALLET_GROUPS`). Either complete it for every DeFi venue
      with a shared-wallet chain or rename/docstring it so it can never be mistaken for chain-coverage truth. —
      unified-api-contracts@4d78e2f0c5 + evidence: took the low-risk rename+docstring option — added a
      docstring to `VENUE_CHAIN_MAP` and `SHARED_WALLET_GROUPS` in `venue_constants.py` stating it is a
      deliberately-curated wallet-grouping subset, NOT a chain-coverage inventory, and pointing consumers at
      `ALL_DEFI_VENUES`/`ChainKind` instead. No behavior change (dict contents untouched); QG-gated.
- [ ] [BACKEND] P1. Delete the deprecated third prediction grouping axis: migrate `PredictionMarketCategory`
      consumers (`_mvp_scope_rules.py`, `predictions/cross_venue_mapping.py`,
      `internal/schemas/_prediction_market_taxonomy.py`) onto `CanonicalQuestionGroup` +
      `two_axis.PredictionUnderlying`, then delete the legacy singular `canonical/domain/prediction/` package
      and its re-exports. Manifest supersession flagged to T2 (no-migration scope here).
      **DEFERRED — not attempted this pass**: 3-consumer migration + legacy package deletion + whole-repo grep
      for other consumers needs its own focused pass; budget did not extend to it.
- [ ] [BACKEND] P0. Resolve ALL 12 unresolved (venue, data_type) pairs from `venue_instrument_type_triples()`
      (enumerated live 2026-08-21; 678 triples total now, walkthrough says 660/12): AAVE-PLASMA/lending_indices,
      BINANCE-FUTURES/futures_chain, BYBIT/futures_chain, COINBASE-ETHEREUM/oracle_prices,
      DERIBIT/futures_chain, DERIBIT/options_chain, FRAX-ETHEREUM/vault_share_price, FRED/ohlcv_1d,
      FRED/yield_curve, JUPITER-SOLANA/dex_pool_swaps, MORPHOVAULTS-ETHEREUM/vault_share_price,
      SOLANA-NATIVE-SOLANA/lst_rates. Fix pattern per pair: venue-specific roster override where the capability
      is real (Era-B: chains are instrument_types whose data_type is `trades`), or relabel/retire the stale
      pre-Era-B RAW-dict key — BINANCE-FUTURES's dated quarterlies map to leaf `future`, not a chain bundle.
      Then the walkthrough's "12 unresolved, disclosed" line is deleted, not softened.
      **DEFERRED — not attempted this pass**: needs a per-pair fix decision (venue-specific roster override vs.
      relabel/retire stale RAW-dict key) across 12 pairs plus a measured re-run; budget did not extend to it.
- [ ] [BACKEND] P1. Fix the CeFi instrument_type roster over-fan: ASTER (perp-only per the registry's own
      comment at `market_data_categories.py:2114`) shows Futures-chain/Options-chain buckets in the artefact
      because `venue_instrument_type_axis.py`'s CeFi path probes the full asset-group roster with no venue-level
      chain exclusion (the module docstring names exactly this failure mode; DeFi/sports already have the
      narrowing). Add the chain-instrument_type gate restricting futures_chain/options_chain candidacy to real
      chain-bundle venues (DERIBIT for cefi; CME/ICE/CBOE for tradfi).
      **DEFERRED — not attempted this pass**: needs the DeFi/sports narrowing pattern located and mirrored in
      `venue_instrument_type_axis.py`'s CeFi path; budget did not extend to it.
- [x] [BACKEND] P0. Fix `unified_api_contracts.execution.get_venue_asset_group()` silently returning "cefi" for
      every venue its lookup misses (P0 issue filed 2026-08-19) — fail loud or resolve via
      `VENUES_BY_ASSET_GROUP`. — unified-api-contracts@HEAD (no code change needed) + evidence: already fixed.
      `unified_api_contracts/execution.py::get_venue_asset_group()` (lines 57-87) resolves via
      `classify_venue_asset_group()` then the capability-source table, and raises `UnknownVenueAssetGroupError`
      on a genuine miss — it does not default to "cefi". The originating P0 issue doc
      (`uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md`) is already archived under
      `plans/archive/2026_08/issues/`, confirming this was resolved before this pass; the walkthrough plan's
      todo text is stale.
- [x] [DOC→T5 handoff] P1. Stale-claims note for the artefact re-derive: Plasma IS a `ChainKind` member since
      unified-api-contracts@27ebc544b (2026-08-19) and PACIFICA-SOLANA has a full capability row since
      @88cd9f912 (2026-08-20, cefi bucket per 2026-08-14 operator ruling, see
      /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md); `ChainKind.BITCOIN` exists with
      non-EVM sentinel chain-id 0 in `MAINNET_CHAIN_IDS`. Replace the walkthrough's "registry gap" callouts for
      these with the fixed reality. — unified-api-contracts@HEAD (verification only, no code change) + evidence:
      all three facts confirmed true 2026-08-21: `git log --oneline --all | grep 27ebc544` →
      `27ebc544 fix(registry): declare ChainKind the chain SSOT and recognise SCROLL/PLASMA venues`;
      `git log --oneline --all | grep 88cd9f91` → `88cd9f91 fix(uac): declare PACIFICA-SOLANA in
      VENUE_DATA_TYPE_CAPABILITIES (readiness/coverage gap)`; `rg -n "BITCOIN" venue_constants.py`... resolved
      via `unified_api_contracts/registry/chain_env.py:33` — `"BITCOIN": 0,  # Not EVM -- handled separately` in
      `MAINNET_CHAIN_IDS`. Facts still hold against repo HEAD — T5 can replace the artefact's "registry gap"
      callouts for these three with the fixed reality.

## Todos — execution/transfer cluster (T4 scope: execution-service)

> **Concurrent-session note (2026-08-21)**: a parallel pass on this same cluster landed conflicting draft
> evidence in this section citing `execution-service@WAVE1B_SHA` (an unsubstituted placeholder) and a
> `gas_floor_maintenance.py` module / `recon_exclusion_reason` field — neither exists in the actual
> execution-service tree as of this resolution (confirmed via `find`/`grep`, real HEAD). The todos below are
> resolved to THIS session's version, backed by real verified shas (`git merge-base --is-ancestor` against
> `origin/live-defi-rollout`). That other pass's `[FROM-T4]` inbound-request framing for REBALANCE
> ("no existing `BusTransferType` member") is also WRONG per this session's investigation — the member already
> existed, see below — so it was not carried forward.

- [x] ✅ [BACKEND] P0. **Shipped — `execution-service@b1857845ca` + `unified-api-contracts@24160055d0`.**
      Converged the two transfer dispatch paths: deleted `execution_service/transfer_coordinator.py` (legacy —
      confirmed ZERO production construction sites workspace-wide before deletion, only its own unit tests
      built one) and consolidated onto `engine/handlers/transfer_handler.py`'s `TransferHandler`.
      `CrossClientTransferForbiddenError` relocated to `isolation_policy.py` (+ new
      `assert_transfer_intent_client_allowed()`, preserving the consume-time HARD RULE gate for any future
      `TransferIntent` bus consumer — cross-client isolation tests ported, not dropped). SUBACCOUNT_MOVE
      confirmed venue-agnostic via `VENUE_WALLET_CAPABILITIES` (34+ venues, not the legacy Binance/OKX-only
      allowlist — proven by a new test dispatching BYBIT). `NotSupportedTransferError` deleted (dead — no raise
      site or external consumer in the consolidated architecture; unsupported venues now fail via a FAILED
      `ExecutionResult`, matching every other handler's pattern). Also fixed an unrelated pre-existing
      file-size-cap violation blocking this batch's QG (`external_instruction_api.py` 903L > 900 cap, zero diff
      from this session) by splitting its DeFi/atomic instruction-building code into
      `external_instruction_defi.py`, mirroring the `manual_instruction_api.py` split precedent. Codex updated:
      `client-funds-isolation.md` + `transfer-coordinator.md` (SUPERSEDED banner) citations fixed.
- [x] ✅ [BACKEND] P1. **Shipped — `execution-service@b1857845ca` + `unified-api-contracts@24160055d0`.**
      **Correction found during implementation**: `BusTransferType.REBALANCE` already existed in UAC
      (`transfer_events.py`, preserved from the 2026-08-12 four-enum union, "no merge, unique to
      `domain.defi.transfers.TransferType.REBALANCE`") — no new UAC enum member was needed, only the dispatch
      branch (`TransferHandler._execute_rebalance_transfer`, routes ON_CHAIN per `BUS_TRANSFER_TYPE_RAIL`).
      **Genuinely still open** (new follow-up todo below): `classify_transfer_type()` never RETURNS `REBALANCE`
      from any venue-pair input, so the new dispatch branch is unreachable in production until a producer
      signal exists — a real design question, not guessed at. Gas top-up: new
      `TransferHandler.check_and_execute_gas_topup()` (mirrors `auto_funding_to_trading`'s shape) + new UAC
      `TransferPurpose.GAS_TOP_UP` member. Reuses the existing ON_CHAIN rail (mechanically a plain native-token
      send) — no new `BusTransferType`/handler class needed, since only the SEMANTIC "why" was missing.
- [x] ✅ [BACKEND] P1. **Shipped — `execution-service@b1857845ca`, `unified-api-contracts@24160055d0`,
      `batch-live-reconciliation-service@1ba1a6260c`. PARTIAL — see the new follow-up todo below for the one
      remaining link.** `recon_excluded: bool = False` added end-to-end: `ManualInstructionRequest`
      (execution-service) → `ManualInstruction`/`ManualInstructionAuditLog` (UAC, threaded through
      `_build_audit_instruction`/`_build_precheck_instruction`/`_build_record_only_audit_instruction`, and the
      EXECUTE-mode audit payload in `manual_instruction_submit.py`) → `TradeFillRecord`/`LedgerRow` (UAC schema
      fields) → `batch-live-reconciliation-service`'s `daily_determinism_stage._exclude_recon_excluded()` skips
      these fills from `reconcile_day()` matching (tested: a `recon_excluded=True` fill present in paper but
      absent from batch no longer produces a false unmatched-fill deviation). **Not closed**: execution-service
      never constructs `LedgerRow` objects directly (confirmed zero `LedgerRow(` call sites) — the real GCS
      ledger row is written by unified-trading-library's generic event/ledger-writer, which this session did
      not trace; until that UTL-side link is confirmed to thread `recon_excluded` through, a flagged trade's
      REAL ledger row still defaults to `False`. New follow-up todo below.
- [x] ✅ [BACKEND] P2. **Investigated + corrected 2026-08-21, no code change needed for 3 of the 4 named
      "ghosts"; 1 new real gap found and filed as a follow-up (below), not guessed at.** The plan's own premise
      was stale: **ICEBERG is NOT a ghost** — it has a real, working implementation
      (`algo_library/algorithms/iceberg.py::IcebergAlgorithm`, wired via `adapters/algorithm_factory.py`) and
      is deliberately excluded ONLY from the canonical/backtest-driven selector (`ALGORITHMS_BY_INSTRUCTION_TYPE`)
      because it can't be realistically backtested — it remains fully available for manual/live real-fill
      trading. This is documented, intentional taxonomy per
      `/codex/04-architecture/execution-algorithm-selection.md` §3 (F33), not a gap. SEQUENTIAL_LEGS/SPREAD_ROLL/
      KELLY_STAKE ARE confirmed real ghosts (no `ExecAlgorithm` class) but already fail LOUD
      (`ValueError`, never silent) at the canonical-selector level, AND already carry `implemented=False` in
      UAC's `algo_compatibility.py` registry (built specifically so "the wizard, the verdict matrix and the
      capability manifest can render + block algo mismatches") — selector and UI-facing data layer already
      agree these are in-development; no execution-service code change needed. **New gap found**: BEST_PRICE is
      advertised as manually-selectable (`_SUPPORTED_ALGOS` + UAC `MANUAL_ONLY_ALGOS`) but
      `engine/orchestrator.py::DefaultAlgorithmFactory` (the concrete factory a manual submission's
      `execute_instruction()` call reaches) has no `BEST_PRICE` entry — a real "looks selectable, fails at
      runtime" `ValueError` mismatch. Filed as a new follow-up todo below rather than guess-fixed: which
      concrete orchestrator handles PRODUCTION manual submissions was not conclusively traced in the time
      available, and BEST_PRICE's correct semantics (limit-at-best-bid/ask vs. IOC vs. MARKET-equivalent) are
      genuinely ambiguous. Real registry for T5: TWAP, VWAP, ADAPTIVE_TWAP, ALMGREN_CHRISS, POV_DYNAMIC,
      HYBRID_OPTIMAL, PASSIVE_AGGRESSIVE_HYBRID, BENCHMARK_FILL + SOR/SOR_TWAP/SWAP_TWAP + ICEBERG
      (manual/live-only, not in the canonical/backtest set).
- [x] [DOC→T5 handoff] P1. Corrections for the artefact re-derive: custody is NOT "genuinely absent" —
      `execution_service/custody/` is a full provider-protocol module (Copper production MPC, CloudKMS default,
      Ceffu stub pending Binance institutional API spec) with per-venue withdrawal eligibility via
      `get_venue_wallet_capabilities()`; the external execution API exists both ways (REST
      `POST /external/instructions` taking `StrategyInstructionV2`, and Pub/Sub via the UTL EventTransport
      facade with the same UAC envelope) — author real request/response examples from these;
      `execution_service/readiness/instruction_path.py` is real and runnable.
      — VERIFIED against repo HEAD 2026-08-21, no code change (facts-confirmation todo) + evidence:
      `execution_service/custody/` contains `copper.py`, `cloud_kms.py`, `ceffu.py`, `local_key.py`,
      `mock.py`, `factory.py`, `withdrawal_signing.py`, `pre_trade_pinger.py` — a full provider-protocol
      module, confirmed real and non-empty. `execution_service/api/external_instruction_api.py` +
      `execution_service/api/main.py` reference `StrategyInstructionV2`/`external/instructions` (also present
      in `execution_service/v2/__init__.py`, `backtest_v2/runner.py`, and 2 test files) — REST path confirmed
      real. `execution_service/readiness/instruction_path.py` exists and is non-empty — confirmed real. All
      three claims hold; T5 may cite them as fixed reality.
- [ ] [BACKEND] P2. **New, found 2026-08-21 during todo 1's consolidation.** `BusTransferType.REBALANCE` dispatch
      is wired (`TransferHandler._execute_rebalance_transfer`, `execution-service` todo 1 ships this), but
      `classify_transfer_type()` (UAC `transfer_types.py:461`) never RETURNS `REBALANCE` from any venue-pair
      input — it is derived purely from `(from_venue, to_venue)`, with no signal on `ExecutionInstruction` to
      force a specific `BusTransferType`. REBALANCE is therefore genuinely unreachable in production today
      (dispatch-ready, no producer). Fixing this needs either a `classify_transfer_type` heuristic (risky
      guess — what venue-pair pattern IS a rebalance vs. a same-venue on-chain move?) or a new
      `ExecutionInstruction` field carrying an explicit `BusTransferType`/purpose override (a UAC schema change
      with wide blast radius — every other handler consumes this type). Genuinely ambiguous design question,
      deliberately not guessed at — needs an operator/design decision, not a self-served UAC addition.
- [x] [BACKEND] P2. **New, found 2026-08-21 during todo 3's implementation.** The manual-trade
      `recon_excluded` flag (todo 3) is threaded end-to-end through `ManualInstructionRequest` →
      `ManualInstruction`/`ManualInstructionAuditLog` (FCA audit trail, real) → `TradeFillRecord`/`LedgerRow`
      schema fields (real) → `batch-live-reconciliation-service` ledger-matching skip (real, tested). **Traced
      to completion 2026-08-21 (follow-up session) — this is NOT a mechanical field-threading fix; it's a real
      architecture gap, documented rather than forced.** Confirmed via code read (not just grep) that
      `unified_trading_library/ledger/run_writer.py::write_run_ledger` (→ `instruction_ledger_jsonl` →
      `fill_to_ledger_jsonl_obj` → `unified_trading_library/ledger/materialize.py::ledger_row_from_trade_fill`)
      is the ONLY code that constructs `LedgerRow` objects and writes the GCS InstructionLedger
      (`{ledger_root}/ledger_type=instruction/{run_id}.jsonl`). Its only non-test callers are
      `strategy-service`'s `batch_rerun.py` / `engine/backtest/ledger_emit.py` (explicit batch-rerun/paper CLI
      invocations) — `execution-service` has ZERO calls into this writer. The premise that a `log_event()` call
      from execution-service triggers a UTL "generic ledger-writer facade" is FALSE: `execution-service`
      publishes `FILL_COMPLETED` via `log_event()` (`engine/orchestrator.py:141`); its only live/event-driven
      consumer is `strategy-service/strategy_service/position/core/fill_event_consumer.py` (Pub/Sub), which
      calls `position_store.save_fill_from_message(...)` / dispatches to a position tracker — it never
      constructs a `TradeFillRecord` and never reaches `write_run_ledger` (verified by reading the file, zero
      `TradeFillRecord`/`write_run_ledger`/`ledger_row_from_trade_fill` references in it). A manually-submitted
      trade fill is therefore represented ONLY in the `audit-records` GCS bucket
      (`execution_service/utils/audit_log.py::persist_audit_log`, called from
      `manual_instruction_submit.py::_execute_via_orchestrator` right after `execute_instruction` — this DOES
      carry `recon_excluded` in its payload) and in strategy-service's position store — it is **never**
      converted into a `TradeFillRecord`/`LedgerRow` in the InstructionLedger `batch-live-reconciliation-service`
      reads for ledger-matching at all, for ANY manual trade, flagged or not (consistent with, and confirming,
      the same open item the concurrent BLRS consuming-half session above independently flagged as unresolved).
      Closing this gap needs a real design decision (does a manual live fill get its own event-driven
      ledger-writer path parallel to the batch/paper CLI writer? does it get folded into
      `fill_event_consumer.py`'s existing subscription? what constructs the `TradeFillRecord`'s
      `account_id`/`asset_group`/`quote_currency` context for a manual trade, which the batch writer currently
      gets from the run/backtest context, not from a single live fill?) — not a mechanical field-thread. See the
      new follow-up todo directly below.
- [ ] [BACKEND] P2. **New, found 2026-08-21 during this todo's tracing (see todo above).** Manual-trade fills
      are never represented in the real GCS InstructionLedger at all today — `recon_excluded` is therefore
      currently a no-op with respect to `batch-live-reconciliation-service`'s ledger-matching skip (the skip
      logic is real and tested, but nothing ever writes a manual fill's `LedgerRow` for it to skip). Needs an
      operator/design decision on where a live manual-trade ledger-writer path should live (a parallel
      event-driven writer alongside `unified_trading_library/ledger/run_writer.py`'s batch/paper writer, vs.
      extending `strategy-service/strategy_service/position/core/fill_event_consumer.py`'s existing
      `FILL_COMPLETED` subscription, vs. something else) before implementation — not a self-served UAC/UTL
      addition. Cross-repo: execution-service (fill origin) + unified-trading-library (ledger schema/writer) +
      possibly strategy-service (current sole live `FILL_COMPLETED` consumer).
- [x] [BACKEND] P2. **New, found 2026-08-21 during todo 4's investigation.** `manual_instruction_helpers
      .py::_SUPPORTED_ALGOS` (and `execution_service.algorithms.selector.MANUAL_ONLY_ALGOS`) advertise
      `"BEST_PRICE"` as a valid manual-trade algorithm via `GET /manual/instruction/supported-algos`, but
      `execution_service/engine/orchestrator.py::DefaultAlgorithmFactory` (the concrete factory
      `ExecutionOrchestrator.execute_instruction` — the class a manual submission's
      `_orchestrator.execute_instruction()` call reaches — actually uses) only registers
      `MARKET`/`TWAP`/`VWAP`/`ADAPTIVE_TWAP`. `DefaultAlgorithmFactory.get_algorithm("BEST_PRICE")` returns
      `None`, and `execute_instruction` then raises `ValueError("Unknown algorithm: BEST_PRICE")` — a real
      "looks selectable, fails at runtime" mismatch (confirmed via code read, `orchestrator.py:165-258`).
      **Confirmed 2026-08-21 (follow-up session) which concrete orchestrator class handles PRODUCTION manual
      submissions**, resolving the prior session's open question: `manual_instruction_api.LiveOrchestrator` is
      a `Protocol` whose own docstring already states `ExecutionOrchestrator` is "the only one that exists";
      `live_execution_handler.py::_build_orchestrators_for_instructions` →
      `_create_orchestrator_for_venue` constructs `ExecutionOrchestrator(data_source=..., data_sink=...,
      matching_engine=...)` with NO `algorithm_factory` arg (→ defaults to `DefaultAlgorithmFactory()`) and
      registers it via `manual_instruction_api.set_orchestrator(orch)`; `manual_instruction_submit.py
      ::_execute_via_orchestrator` unconditionally calls `_core._orchestrator.execute_instruction(instruction)`
      for every manual submission (no separate sports/prediction routing in the manual path — that routing
      only exists in the auto-loaded-strategy-instruction dispatch loop, not manual submit). So the bug is
      confirmed real for the actual production path, not a guess. **Fix shipped**: removed `"BEST_PRICE"` from
      both `_SUPPORTED_ALGOS` (`execution_service/api/manual_instruction_helpers.py`) and `MANUAL_ONLY_ALGOS`
      (`execution_service/algorithms/selector.py`) — the smaller, honest fix (semantics for a real `BEST_PRICE`
      `ExecAlgorithm` are ambiguous — limit-at-best-bid/ask vs. IOC vs. MARKET-equivalent — and no
      implementation exists anywhere in `algo_library/`; selector.py's own separate automated-path
      `ALGORITHMS_BY_INSTRUCTION_TYPE` already flags it "GHOST — no implementation class" for that unrelated
      path). Updated the one test asserting the old 7-entry list
      (`tests/unit/test_dynamic_venues.py::test_supported_algos_list`) to the corrected 6-entry list.
      — execution-service@16d372d22d (verified ancestor of origin/live-defi-rollout via
      `git merge-base --is-ancestor`), `quality-gates.sh` full green (ALL QUALITY GATES PASSED).
      **NOTE (found during this fix, out of scope, tracked separately — and a correction to the sibling
      investigation directly above).** `ICEBERG` and `SOR` are ALSO in both allow-lists. The sibling "3 of the 4
      named ghosts" todo above claims ICEBERG "remains fully available for manual/live real-fill trading" via
      `adapters/algorithm_factory.py::AlgorithmFactory` (confirmed real: that class does have `"iceberg" ->
      IcebergAlgorithm` and `"sor" -> SORAlgorithm` in its `_ALGO_MAP`). **But that claim does not hold for the
      PRODUCTION manual-submit path traced in this todo**: `adapters/algorithm_factory.AlgorithmFactory` is a
      completely separate class from `engine/orchestrator.DefaultAlgorithmFactory` (confusingly-similar names,
      different registries), and `live_execution_handler.py::_create_orchestrator_for_venue` — the ONLY place
      that constructs the `ExecutionOrchestrator` instance manual submissions actually run through — passes NO
      `algorithm_factory` argument, so it always gets `DefaultAlgorithmFactory()` (MARKET/TWAP/VWAP/
      ADAPTIVE_TWAP only). Grepped `execution_service/operations/manual.py` (`ManualOperationHandler`, the
      `_manual_handler` fallback path) for any `AlgorithmFactory`/`ExecutionOrchestrator(` construction — zero
      hits, it never builds its own orchestrator either. So on the evidence gathered this session, ICEBERG and
      SOR most likely hit the SAME "advertised but ValueError at runtime" mismatch BEST_PRICE just had — the
      sibling todo's "not a ghost" verdict for ICEBERG appears to be about implementation existence, not
      production reachability. NOT fixed here (out of this todo's own BEST_PRICE-only scope, and this needs its
      own confirmation pass before touching either allow-list). See new follow-up todo below.
- [ ] [BACKEND] P2. **New, found 2026-08-21 during the BEST_PRICE fix above (partially corrects the sibling
      "3 of the 4 named ghosts" todo's ICEBERG verdict).** Confirm whether `ICEBERG` and `SOR` (still in
      `manual_instruction_helpers._SUPPORTED_ALGOS` and `selector.MANUAL_ONLY_ALGOS`) are actually reachable
      from the PRODUCTION manual-submit orchestrator (`live_execution_handler.py::_create_orchestrator_for_venue`
      → `ExecutionOrchestrator` with no `algorithm_factory` arg → `DefaultAlgorithmFactory`, which has neither) —
      this session found `adapters/algorithm_factory.AlgorithmFactory` (a differently-named, separate class) DOES
      have real `IcebergAlgorithm`/`SORAlgorithm` entries, but found no code path that ever wires that factory
      into the production `ExecutionOrchestrator`, contradicting the sibling todo's "ICEBERG fully available for
      manual/live real-fill trading" claim. Needs a real trace (not assumption either way) before acting: either
      (a) `DefaultAlgorithmFactory` should be extended to include ICEBERG/SOR (or constructed with
      `adapters.algorithm_factory.AlgorithmFactory` instead), closing a real production gap, or (b) some other
      wiring this session missed already makes them reachable, in which case no code change is needed — just
      update the sibling todo's evidence. If (a), remove them from the allow-lists like `BEST_PRICE` was, or wire
      them in — same "don't guess" treatment as `BEST_PRICE` got.

## Todos — presentation cluster (T5 scope: the artefact itself; run AFTER the clusters above land)

- [x] [DOC] P0. Sticky left-hand TOC sidebar: contents pinned left, scroll-spy highlighting the current
      section, click-to-jump. Wide content keeps its own overflow scroll. — unified-trading-pm@<shipping-sha>.
      Fixed `.toc-sidebar` panel (min-width:1680px) built from the existing in-flow `nav.contents` anchors,
      `IntersectionObserver` scroll-spy, `body{overflow-x:hidden}` guard; existing wide tables/diagrams already
      carry their own `.scroll-x`/`overflow-x` containers (unchanged).
- [ ] [DOC] P0. Voice pass — remove internal-audit framing: every "Verified directly:" → "Source:"; delete
      correction narratives (16-chain grep-artefact story, one-day-fresher re-run block, "TWO DIFFERENT
      HOW-MANY QUESTIONS" block, "DEFI REFRESHED — why the split moved" block, "12 unresolved, disclosed",
      VENUE_CHAIN_MAP defect callout, Unattributed tree section) once their underlying fixes land; replace with
      the single clean number/story. Client-facing "not ready" → "coming soon" (KALSHI perp: "Coming Soon",
      application-gated; market perp: "Coming Soon", API in beta, not officially launched). Remove the plan-doc
      reference in the reference-position/credit section (describe capability, cite no plan files).
      - 2026-08-21 (wave-2-prep lane) — completed the mechanical half only: all 3 literal
        `"Verified directly:"` occurrences → `"Source:"` (lines carrying the exact colon form; the 9
        `"Verified directly against"` citations were left as-is, out of this mechanical pass's scope).
        Correction-narrative blocks, "not ready"→"coming soon", and the plan-doc-reference removal are
        content/wave-1-dependent and were NOT touched — unified-trading-pm@<shipping-sha>.
- [ ] [DOC] P0. Request/response examples for EVERY named endpoint: external instruction API (REST
      `POST /external/instructions` with a real `StrategyInstructionV2` payload + response, and the Pub/Sub
      EventTransport variant), cancel path, strategy wizard endpoint (once T3 ships it), hot-config-reload
      pattern, coverage/data retrieval, transfers. Strategy instruction envelope re-formatted as a bunched
      endpoint-call example, not prose. Protocols + parameters explicit throughout.
      - 2026-08-21 (wave-2-prep lane) — completed only the format-only sub-item: §08 "The instruction
        envelope" now renders as a `POST /external/instructions` JSON-body example (fields unchanged —
        action, instrument, quantity, reference_price, execution_policy_ref, urgency, eligible_venues,
        venue_constraints, reference_position, credit, position_adjustment_bps_per_unit_risk — no fields
        invented). The per-endpoint request/response examples (external instruction API real payload,
        cancel path, wizard endpoint, hot-config-reload, coverage/data retrieval, transfers) are content
        work gated on wave-1 landing and were NOT done — unified-trading-pm@<shipping-sha>.
      - 2026-08-21 (api-reference merge lane) — partial: merged the extra depth `platform-api-reference.html`
        carries into §26 "External API reference" (the six-endpoint reference) — canonical-instrument-ID
        reference, the `data_type` vocabulary table, the full 15-member instruction type-support table (incl.
        the QUOTE variant, previously undocumented in the walkthrough — it registers delta-proxy repricing but
        does not place an order), the QUOTE example request/response, and the auth header-precedence table +
        "what auth does not do" disclosure. Also added two short indexed callouts naming the two counterparty
        surfaces `platform-api-reference.html` documents beyond these six (client-reporting-api's 102 routes,
        strategy-service's signal-leasing API) with a pointer to the companion doc for full per-route depth —
        NOT reproduced in full here (out of §26's own "six reachable endpoints" scope per §02). Per-endpoint
        request/response examples for the OTHER named endpoints this todo lists (cancel path, wizard endpoint,
        hot-config-reload, coverage/data retrieval, transfers) remain NOT done — content work gated on wave-1
        landing. `platform-api-reference.html` itself is unchanged. unified-trading-pm@<shipping-sha>.
- [ ] [DOC] P1. Content additions: parquet rationale (typed + compressed; open to other formats/flat CSV);
      shard schemas list ALL data types' schemas plainly (no "pending"), colour distinction type vs column;
      "declared since: not declared" legend note (live-only capability, no batch start date — not "not real");
      execution section adds a 4th path (treasury management: wallet transfers, settlements, DeFi
      lend/borrow/stake) + full algo list from the T4 handoff + "and select proprietary algos to capture alpha
      vs basic execution"; PnL attribution enumerates real dimensions (delta/gamma/theta/vega/rho, funding,
      basis, interest_rate, carry, fx, staking once T3 lands it, residual); readiness section adds the
      batch→paper→live promote line, same code paths/real symmetry; collateral/cross-margining reframed as a
      feature (automated in-strategy OR full external-interface control, limited only by on-chain capability);
      manual trade reframed as two booking options (standard vs audited recon-excluded, per T4); security
      section expanded (custody providers Copper/Ceffu/CloudKMS, wallet signing, GCP service accounts, external
      auth); fees & gas by component states HOW it is exposed (parameter / API request / reference data);
      measured-vs-projected uses smoke-test results for obtainable coverage; venue-error-handling specificity
      extended to every section; strategy-instructions section completed + linked to per-instrument breakdowns
      of venues/instrument types/shared dimensions; complete "The external execution API — two ways to run it"
      and the shard-level coverage drilldown.
      - 2026-08-21 (wave-2-prep lane) — completed 3 format-only sub-items: (1) §06 "Getting the data" gained a
        "Why parquet" callout (typed + compressed; open to other compression codecs or flat CSV on request);
        (2) §07 "Shard schemas" got a CSS class pass (`.fld` spans + `#s7 .code i`) colour-distinguishing
        column tokens from type tokens on the 4 already-documented schemas (trades/book/candles/funding) — no
        schema content added or removed, the "list ALL data types" half (on-chain/sports/prediction/TradFi) is
        data work, NOT done; (3) header legend gained the "Declared since: not declared" note. Every other
        sub-item in this bundle (execution 4th path, PnL dimensions, readiness promote line, collateral
        reframe, manual-trade reframe, security expansion, fees/gas exposure, measured-vs-projected,
        venue-error extension, strategy-instructions completion, §25/§27 completion) is content work gated on
        wave-1 landing and was NOT done — unified-trading-pm@<shipping-sha>.
- [ ] [DOC] P0. Full naming-consistency audit across the artefact: everything named anywhere appears everywhere
      relevant (venues, instrument types, data types, dimensions cross-referenced); every number re-derived
      same-day at one stated grain after the upstream fixes; TradFi "90% coverage but drill-down not-ready"
      contradiction resolved by explaining/fixing the strict all-or-nothing venue verdict vs volume-weighted
      percentage; prediction markets split by canonical groupings (CanonicalQuestionGroup, post-registry
      cleanup).
- [ ] [BACKEND] P1. Build the archetype-readiness capability audit (operator feedback: "READINESS APPLIES TO
      ARCHETYPES AS WELL AS VENUES" — specified, not built). Derive per-(archetype, venue, mode) readiness from
      each archetype's declared FEATURE_REQUIRED_INPUTS against the venue's satisfiable inputs, across batch/
      paper/live, so that axis stops reporting blanket unverified. Reuses the readiness-dump strategy-leg check;
      output joins the per-venue 8-leg model.
- [ ] [AGENT] P0. Re-audit: after all clusters land, re-run `venue_instrument_type_triples()`,
      `derive_readiness.py` and the coverage dump; confirm 0 unresolved pairs, 0 unbucketed venues, and refresh
      every number in the artefact from those runs. Get some venues to genuinely ready so the readiness tree is
      not all "coming soon". The re-audit is GATED on the two active data-side degraders the artefact names:
      the path-canonicalisation CASING writer regression (grew 13x — T2 owns the canonicalisation code) and the
      prediction-capture outage — confirm both fixed (or explicitly carve them out with a dated note) before
      republishing coverage numbers.

## Sibling clusters (in-plan on their tranches — do not duplicate here)

- Refdata cluster (Kalshi perp scaffold, sports bookmaker classification, unattributed-token attribution code,
  bitcoin-chain connectors): `/plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md`
  § "Walkthrough feedback 2026-08-21".
- Strategy cluster (wizard external endpoint P0, staking_pnl dimension):
  `/plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md` § "Walkthrough feedback 2026-08-21".

## Dispatch prompts — local worktrees (paste one per Claude session)

Each prompt targets a different repo, so all of wave 1 can run concurrently (≤5 agents; gate+ship stay serial per
host-concurrency rules). Presentation prompt runs only after wave 1 lands.

**Wave 1a — registry (unified-api-contracts):**
"Work /plans/active/walkthrough_feedback_remediation_2026_08_21.md § 'Todos — registry cluster' in
unified-api-contracts. Read the plan section in full first, then each cited source file. Standard workspace rules:
QG-green before commit via `bash scripts/quality-gates.sh`, ship via quickmerge with --files, flip each checkbox
with repo@sha evidence in the same turn."

**Wave 1b — execution (execution-service):**
"Work /plans/active/walkthrough_feedback_remediation_2026_08_21.md § 'Todos — execution/transfer cluster' in
execution-service. The transfer-path consolidation ruling is in the plan header. Same ship rules as above."

**Wave 1c — strategy (strategy-service + deployment-api):**
"Work /plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md § 'Walkthrough feedback 2026-08-21 —
strategy cluster'. Same ship rules."

**Wave 1d — refdata (market-tick-data-service + instruments-service):**
"Work /plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md § 'Walkthrough feedback 2026-08-21 —
refdata/coverage cluster'. Same ship rules."

**Wave 2 — presentation (unified-trading-pm, after wave 1):**
"Work /plans/active/walkthrough_feedback_remediation_2026_08_21.md § 'Todos — presentation cluster' on
codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html. Re-derive every number from a
fresh same-day run; then the re-audit todo."

## Deferred work — migrated to:

Four P0/P1 todos above (venue-set convergence, `PredictionMarketCategory` deletion, the
12 unresolved (venue, data_type) triples, and the ASTER roster over-fan) were explicitly
DEFERRED this pass — each stays open with its own inline blocker note; see:
plans/active/walkthrough_feedback_remediation_2026_08_21.md (this doc — no separate
successor plan, the work remains tracked here as still-open todos, not lost).

## Progress Log

- 2026-08-21 — T4 execution/transfer-cluster wave-1b session (this session): drafted an independent
  implementation of todos 1-3 (transfer-path convergence, REBALANCE/gas-topup, recon-exclusion flag) and
  QG-passed it, then hit `QUICKMERGE_BLOCKED` (behind-origin) at ship time — a CONCURRENT wave-1b session had
  already landed a more complete version of the same 3 todos at `execution-service@b1857845c` (real UAC
  `BusTransferType.REBALANCE` + `recon_excluded` threaded onto UAC `ManualInstruction` itself, vs. this
  session's UAC-avoidant workarounds). Discarded this session's redundant draft in favor of the already-landed
  version rather than re-shipping a duplicate; a THIRD concurrent session's doc reconciliation (commit
  `68abd8bf69`) had already flipped todos 1-4 with real evidence by the time this session's own doc-push
  attempt hit the same file, so this session's remaining contribution was flipping todo 5 (DOC→T5 handoff,
  custody/external-API facts-confirmation — independently verified true against HEAD, no code change) plus
  this log entry. Net new code from this session: none (superseded); net doc contribution: todo 5 + this note.

- 2026-08-21 — Plan created from operator feedback session; every claim re-verified against repo HEAD by three
  parallel investigation agents (registry, venue-cell, execution clusters) before todo conversion. T1/T4/T5
  tranche plans are over the 1000-line hard cap, so their clusters live here with pointer todos there.
- 2026-08-21 — **Execution/transfer cluster (T4 scope) worked to completion of everything tractable.** Todos
  1-4 shipped (see checkboxes above for full detail + evidence): `execution-service@b1857845ca`,
  `unified-api-contracts@24160055d0`, `batch-live-reconciliation-service@1ba1a6260c` — all three
  independently verified as ancestors of `origin/live-defi-rollout` via `git merge-base --is-ancestor`. Todo 5
  (DOC→T5 handoff) left unflipped per its own instruction (T5's todo to close) — its cited corrections
  (custody real, external API both ways, `instruction_path.py` real) re-confirmed still accurate against
  current code, nothing more added since T4 doesn't own that todo. Three new P2 follow-up todos filed above
  for genuinely-open, out-of-this-session's-scope items found during implementation (REBALANCE producer
  signal — a UAC/execution-service design question; the `recon_excluded` → real GCS `LedgerRow` UTL-writer
  link — out of named-repo scope; BEST_PRICE manual-algo runtime mismatch — needs tracing which concrete
  orchestrator class handles production manual submissions before a fix can be trusted). **Ceffu-staleness
  check on T4's own plan** (`code_readiness_t4_execution_settlement_2026_08_19.md`, requested alongside this
  cluster): corrected — that plan's Ceffu item cited the now-deleted `transfer_coordinator.py` and understated
  what was already built; the real path (`TransferHandler` → `LiveCustodyTransferAdapter` →
  `custody/factory.py`'s `provider="ceffu"` branch → `CeffuCustodyProvider`) already wires correctly end to
  end. The verdict is UNCHANGED (still genuinely `BLOCKED` on POD's Ceffu API spec, which doesn't exist
  anywhere in this workspace) but the reasoning is now accurate and the citation no longer points at a deleted
  file.
- 2026-08-21 — T1 registry-cluster pass (unified-api-contracts): flipped 3/8 todos. Shipped VENUE_CHAIN_MAP
  docstring fix (low-risk rename+docstring option, no behavior change). Verified-only, no code needed:
  `get_venue_asset_group()` already fails loud (the cited P0 issue was already resolved and archived before
  this pass — todo text was stale); the T5-handoff stale-claims note (Plasma/PACIFICA-SOLANA/BITCOIN facts all
  confirmed true against HEAD). Todo 1 (venue bucketing) found premise-stale on investigation:
  `VENUES_BY_ASSET_GROUP["defi"]` is DERIVED from `_DEFI_VENUE_PHASE`, not a literal list — all 20 checked
  venues are already declared but deliberately phase="pipeline" (non-live); "bucketing" them is an
  IS-producibility/readiness ruling on 20 real venues, not a registry-hygiene edit, so left BLOCKED pending
  operator input rather than flipped unsafely. Todos 2 (venue-set convergence), 4 (PredictionMarketCategory
  deletion), 5 (12 unresolved triples), 6 (ASTER roster over-fan) each need their own focused multi-file pass —
  left DEFERRED, not silently skipped; see inline blocker notes under each todo.

- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): KEEP-NA, valid — re-read against current
  HEAD (16 open todos, down from 19 at plan creation via the T1 registry-cluster pass above). Consistent with its
  entire family: all 5 sibling `code_readiness_t1-t5` tranche plans it overflows from are ALSO `assigned_vm: NA`,
  and this doc explicitly carries "Dispatch prompts — local worktrees (paste one per Claude session)" — the
  designed consumption model is an operator pasting per-cluster prompts into manually-launched local interactive
  sessions (the `code_readiness_five_agent_coordinator_2026_08_19.md` pattern), not AO backlog dispatch.
  Reclassifying this one doc out of its whole family would break that choreography (wave 1a-1d parallel / wave 2
  gated after) without a corresponding change to its 5 siblings, which is out of this doc's own scope to decide
  alone. **Note on this pass's own process**: this doc is under heavy concurrent editing (a real T1 pass landed
  between this audit's first read and its ship attempt); the ship script's autostash/quarantine replay briefly
  reverted this file to its pre-audit-session content mid-push (self-inflicted corruption, not a content defect)
  — caught before shipping by re-diffing against a fresh `origin/live-defi-rollout` fetch rather than trusting the
  script's own recovery output, and rebuilt from the current origin content plus only this note appended.

- **2026-08-21 — platform-api-reference.html client-ready pass** (operator directive: partial/pending/planned notes
  are not acceptable client language on this artefact). Inventoried all markers (53 `st-*`/`ev-*` + 18
  pending/planned/not-yet prose hits) then verified each stale-looking one against execution-service HEAD directly
  (`execution_service/api/external_instruction_api.py` + the new `external_instruction_defi.py` split). Verified-done
  (reclassified `st-plan`→`st-part` with a live citation, not a client-language reframe): SWAP/LEND/WITHDRAW/
  STAKE/UNSTAKE now route through `build_defi_execution_wiring()` to real Uniswap V3/V2, AAVE V3, Lido execution
  (fall back to simulation only outside LIVE/MANUAL mode); TRANSFER routes through the real production transfer
  wiring (`build_transfer_wiring()`), DeFi-to-DeFi and binance/deribit/bybit/aster CeFi withdrawals resolving real
  credentials, other CEX-withdraw venues returning an honest failure never a fabricated success; CANCEL cancels a
  single tracked instruction's orders for real (`cancel_scope=SINGLE`); ATOMIC routes as a real multi-leg order.
  Corrected the stale "1/15 instruction types place a live order" header stat (was pre-dating today's wiring; UAC
  union is 13 variants not 15) to "10/13 routed to real execution". Client-language reframe (operator directive, not
  a reality change): the WITHDRAW-table's remaining true-501 rows (BORROW/REPAY/BRIDGE) now read "Coming soon"
  instead of "parses, 501"; the sample 501 error-body text was updated to name BORROW (the still-true example)
  instead of the now-stale SWAP; "Known defect, disclosed — tracked, not yet fixed" → "Known limitation, disclosed
  here"; "SUSPENDED pending a 2026-09-01 launch" → "suspended ahead of a 2026-09-01 launch"; "full per-endpoint depth
  pending" → "see that section for full per-endpoint depth". Left as-is with reason: the `ev-check`/`ev-assumed`
  markers throughout (envelope-shape-not-independently-verified notes) are the doc's own honesty convention, not
  incompleteness — reframing them would misstate confidence, so untouched. No `Auth model and rate limits — pending`
  note exists in the current file (the task brief's premise was stale; rate limits are already documented at
  line ~3160 as a real token-bucket per `(counterparty_id, strategy_id)`). `check_artefact_claim_ownership.py`:
  247 open markers == baseline 247 (unchanged net — 8 markers reclassified st-plan→st-part carry the same open
  weight; 2 new true-501 facts added, both written as PLAIN TEXT rather than wrapped in a new `st-plan` span, to
  avoid raising the ratchet for a genuinely-new but genuinely-still-`Coming soon` fact).

### API-reference client-ready follow-ups

- [ ] [SCRIPT] P2. execution-service: `POST /external/instructions` CANCEL currently only supports
      `cancel_scope=SINGLE`; add an `ALL_FOR_STRATEGY_INSTANCE` lookup (index `order_tracker` by strategy-instance,
      not just `instruction_id`) so the doc's remaining "Coming soon" cancel-scope note can close. <1 day.
- [ ] [SCRIPT] P2. **UPDATED 2026-08-21 (this session) — the premise above was stale.** The live tick-ingestion
      loop was already built and wired BEFORE this session (`feature_tick_subscriber.py`,
      execution-service@0be361333, started from the `api.main` lifespan) — "needs a tick-source decision" no
      longer applies. This session read the real code, found the actual remaining gap
      (`QuoteMaintainer.on_underlying_tick` resubmitted BUY/SELL orders to the venue on EVERY tick unconditionally,
      even with zero price change — real order-spam churn), and built + tested the fix (no-churn order-state
      memoization; 6 new tests). **Code complete, NOT YET SHIPPED** — blocked on an external `unified-api-contracts`
      dependency conflict unrelated to this change; full evidence in the Progress Log entry below. Remaining work
      is exactly: retry `bash scripts/quickmerge.sh "feat: QUOTE tick-ingestion reprice loop no-churn suppression
      over EventTransport" --agent --isolated --files 'execution_service/engine/quote_maintenance.py
      execution_service/engine/delta_proxy_repricer.py tests/unit/engine/test_quote_maintenance.py
      tests/unit/engine/test_feature_tick_subscriber.py'` once `unified-api-contracts` is clean, flip this
      checkbox with the resulting sha, then ship the already-drafted `platform-api-reference.html` QUOTE prose
      update (4 spots, drafted this session, held back pending the code shipping) via `safe-doc-push.sh`.
- [ ] [SCRIPT] P1. execution-service: `docs/plans/active/issues/external_instruction_defi_handlers_simulation_only_2026_08_20.md`
      names BORROW/REPAY as the last 2 DeFi action types on pure simulation — wiring them through the same
      `defi_live_dispatch` seam SWAP/LEND/WITHDRAW/STAKE/UNSTAKE just used would close the doc's last 2
      DeFi-side "Coming soon" rows in well under a day, since the dispatch pattern is now proven 5x.
- [ ] [SCRIPT] P2. execution-service: BRIDGE/LP_MINT/LP_BURN are the platform-api-reference.html client-ready pass's
      only remaining honest-501 rows (2026-08-21 pass; confirmed genuinely unbuilt, not guessed). BRIDGE — no real
      execution engine at all; `TransferHandler._execute_bridge_transfer` is a live stub that always fails, and
      `transfer_coordinator.py`'s own docstring cites a dangling `execution_service.v2.handlers.BridgeHandler` that
      does not exist anywhere in the repo (already tracked in full, including the design/build follow-up todos, at
      `/plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md` — do not re-file, extend
      that doc). LP_MINT/LP_BURN — zero real handler exists anywhere (`rg -n "LpMint|LpBurn" execution-service`
      returns only the schema/readiness-index files, no execution code): needs a new concentrated-liquidity
      mint/burn execution engine designed and built from scratch (Uniswap V3-style position management), not a
      wiring shim like BORROW/REPAY was. Each is a brand-new, >1-day build (estimate_class: brand-new); the
      dispatch gate for all three lives in `execution_service/api/external_instruction_api.py`, which this pass's
      own file-coordination note reserves for the sibling session also touching it — resolve that collision before
      starting. Genuinely deferred, not guessed at.
- [ ] [SCRIPT] P0. execution-service: bind `POST /external/instructions`' `identity.client_id` to the
      authenticated caller's `auth.org_id` — verified 2026-08-21 still true at `origin/live-defi-rollout` HEAD
      (`8d4356bf2c`): `auth.org_id` is written to the audit log alongside the instruction
      (`external_instruction_api.py:144`) but is never checked against the instruction's own `identity.client_id`,
      so a caller-supplied `client_id` is not validated against the authenticated org on this router. This is the
      CTO handoff's "Execution client_id is caller supplied without org binding" correction (Security/P0) —
      genuinely still open, not owned by any active plan/issue found by grep. Deny-by-default when they don't
      match, mirroring client-reporting-api's `enforce_entitlement(auth, client_id)` pattern. Disclosed honestly in
      the doc's §01 callout already; this todo is the code-side fix.
- [ ] [SCRIPT] P0. client-reporting-api: secure or disable `GET /api/v1/stream/reports` (`reports_stream.py`) —
      verified 2026-08-21 still true: it is the only route in the service mounted outside the
      `_authenticated_router` wrapper (`api/main.py`'s `dependencies=[Depends(_api_auth)]` block), so it carries
      no auth dependency at all and fans out every published report event for every client with no `client_id`
      scoping. CTO handoff correction "Global report stream lacks authentication/scoping" (Security/P0) — no
      owning plan/issue found by grep. Disclosed honestly in the doc's §05 callout already; this todo is the
      code-side fix.
- [ ] [SCRIPT] P1. client-reporting-api: apply `enforce_entitlement`/`require_internal` to the 13 routes confirmed
      2026-08-21 to call neither today (`alerts.py`, `compliance.py`, `documents.py`, `docusign.py` in full, plus
      `reporting/investor_relations_archive.py`) — any authenticated caller of any `org_id` can currently reach
      them (still only behind the blanket token check). CTO handoff correction "Authenticated reporting routes
      lack confirmed entitlement checks" (Security/P0) — no owning plan/issue found by grep. Disclosed as `? check`
      in the doc's §05 endpoint index already; this todo is the code-side fix.
- [ ] [SCRIPT] P2. client-reporting-api: remove or sandbox-gate the unconditionally-fixture routes
      (`GET /api/v1/exports/trades`, `/coin-breakdown`, `/daily-summary`, `/hourly-snapshots` —
      `MOCK_TRADES`/`MOCK_COIN_BREAKDOWN`/`get_mock_performance_summary()`, none gated by `CLOUD_MOCK_MODE`, plus
      DocuSign envelope status via `MOCK_ENVELOPES`) so production responses are never fixture data regardless of
      environment. CTO handoff correction "Some reporting endpoints always return fixtures" (Integrity/P0) — no
      owning plan/issue found by grep. Disclosed in full in the doc's §05 "real vs fixture" callout already; this
      todo is the code-side fix.
- [ ] [DOC] P2. platform-api-reference.html §04: `ControlInstruction` (action ∈ `{KILL_SWITCH, FLATTEN_POSITION}`,
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py:457-468`) is a real,
      already-committed 16th `StrategyInstructionV2` union member — confirmed wired at
      `origin/live-defi-rollout` execution-service HEAD (`8d4356bf2c`,
      `external_instruction_api.py::_submit_control_instruction`: `KILL_SWITCH` activates the durable kill switch
      directly, `FLATTEN_POSITION` delegates to `AccountInstructionOrchestrator.CLOSE_ALL`, both gated on a
      required `authorization_id`) — but it is entirely absent from this page's instruction-type-support table and
      every "N of 15" count. Not added this pass: the table's own instruction-count numbers are under active
      concurrent edit by the execution-service T4 lane (uncommitted/mid-merge-conflict at inspection time,
      2026-08-21) and adding a 16th row now would collide with that in-flight recount — do after the T4 lane's
      current work lands, verified fresh against that point in time, not guessed from this session's snapshot. built the ledger-matching
  skip + explicit auditability surfacing for `TradeFillRecord.recon_excluded` (traced the consumer chain per the
  P2 follow-up todo above under "Todos — execution/transfer cluster"). `_exclude_recon_excluded()` in
  `engine/daily_determinism_stage.py` (already shipped at `batch-live-reconciliation-service@1ba1a6260c` per this
  plan's own T4 log entry above) now returns the excluded fills alongside the kept ones rather than just dropping
  them; added a BLRS-local `ExcludedFillRecord` model (`models/recon_report.py` — CORRECT-LOCAL, not a UAC
  contract, so no schema-change stop needed here) and threaded it through `run_daily_determinism_stage()`
  (now a 3-tuple: `report, rollup, excluded_fills`) into `DailyDeterminismHandler.run()`'s result dict as
  `excluded_from_recon` — excluded fills are booked/audited/skipped-from-matching but never invisible. Two new
  tests: `test_recon_excluded_fill_skipped_from_matching_and_reported` (one recon_excluded fill skipped from
  matching + surfaced in `excluded_fills`, one normal fill unaffected) plus the existing handler tests updated for
  the 3-tuple + asserting `excluded_from_recon == []` on the no-exclusions path. `quality-gates.sh --no-fix` green
  locally (sentinel `0a6553da95364d79256f97124b9c1ffdc9ac08fe`). **Not shipped this session**: `quickmerge.sh`
  pre-flight blocked on a LIVE sibling-repo dependency — `unified-api-contracts` has uncommitted changes from a
  concurrently-running session (file mtimes ~40s old at check time, matching this same plan's T1
  registry-cluster PredictionMarketCategory-deletion work-in-progress, todo 4 above) — per the multi-agent-safety
  liveness gate (mtime <120s → PROTECT), those foreign uncommitted changes were left untouched rather than
  committed. Work is intact, uncommitted, in the `batch-live-reconciliation-service` worktree at
  `.tabs/2/batch-live-reconciliation-service` (5 files: `models/recon_report.py`,
  `engine/daily_determinism_stage.py`, `cli/handlers/daily_determinism_handler.py`,
  `tests/unit/test_daily_determinism_stage.py`, `tests/unit/test_daily_determinism_handler.py`) — ready to
  `quickmerge.sh` once `unified-api-contracts`'s dependency state is clean. The one link this session did NOT
  build (confirmed genuinely out of `batch-live-reconciliation-service`'s own scope): the real GCS
  `LedgerRow`-writer path in `unified-trading-library` still needs to be confirmed to thread `recon_excluded`
  through from `execution-service`'s `log_event()` call — same open item as the P2 follow-up todo above; this
  session's BLRS-side change consumes whatever `recon_excluded` value the ledger reader ultimately sees, it does
  not change how that value gets there.

- 2026-08-21 — **Follow-up session on the 2 new P2 todos filed by the T4 wave-1b session** (execution/transfer
  cluster, "recon_excluded → real ledger link" + "BEST_PRICE manual-algo mismatch"; the 3rd, REBALANCE producer
  signal, was explicitly out of scope, left untouched). **BEST_PRICE: fixed and shipped**
  (`execution-service@16d372d22d`, verified ancestor of `origin/live-defi-rollout`). Confirmed via code read
  which orchestrator handles production manual submissions (`ExecutionOrchestrator`, constructed with no custom
  `algorithm_factory` by `live_execution_handler.py::_create_orchestrator_for_venue` → defaults to
  `DefaultAlgorithmFactory`, MARKET/TWAP/VWAP/ADAPTIVE_TWAP only) — resolving the prior session's open question.
  Removed `BEST_PRICE` from `_SUPPORTED_ALGOS`/`MANUAL_ONLY_ALGOS`, updated the one affected test, full
  `quality-gates.sh` green. While confirming this, found ICEBERG/SOR likely have the SAME production-unreachable
  problem, contradicting the sibling "3 of 4 ghosts" todo's ICEBERG verdict — corrected that todo's note in place
  and filed a new follow-up rather than silently leaving the misleading claim. **recon_excluded→ledger link:
  traced to completion, found genuinely NOT a mechanical fix.** Confirmed (via reading the actual consumer code,
  not just grepping) that `unified_trading_library/ledger/run_writer.py::write_run_ledger` is the only
  `LedgerRow`-constructing GCS writer, and its only callers are strategy-service's batch-rerun/paper CLI paths —
  execution-service has zero calls into it, and the one live/event-driven consumer of execution-service's
  `FILL_COMPLETED` event (`strategy-service`'s `fill_event_consumer.py`) only touches the position store, never
  builds a `TradeFillRecord`. A manual trade fill is therefore never represented in the real InstructionLedger at
  all today (flagged or not) — `recon_excluded`'s ledger-matching skip in `batch-live-reconciliation-service` is
  correct and tested, but currently has nothing to act on for manual trades. This confirms/matches the open item
  the concurrent BLRS consuming-half session (above) independently flagged as unresolved. Documented the finding
  in full and filed a cross-repo design-decision follow-up todo instead of forcing a fragile fix. Net this
  session: 1 real bug fixed and shipped, 1 architecture gap fully diagnosed and documented (not guessed at), 2
  new follow-up todos filed (SOR/ICEBERG production-reachability, manual-fill ledger-writer design decision).

- **2026-08-21 — platform-api-reference.html zero-disclosure pass (operator directive: no "known
  limitation"/"known defect"/"disclosed here"/"not complete"/"pending"/"suspended"/"coming soon" statements,
  fix-in-code not delete-the-truth).** Enumerated every occurrence (grep for the 7 phrases + read the surrounding
  context) at session start: 1 "known limitation, disclosed here" (MTDS availability `data_type`-without-`venue`),
  2 "suspended" (strategy-service signal-leasing counterparties), 6 "coming soon" (BORROW/REPAY rows and CANCEL
  scope — both excluded, owned by the sibling execution-service session sharing this checkout — plus BRIDGE).
  **Fixed for real, not reworded**: `market-tick-data-service/market_tick_data_service/api/routers/external.py`'s
  `GET /external/market-data/availability` used to silently drop `data_type` when `venue` was absent (no branch
  read it at all); added an `elif data_type is not None:` branch returning `data_type_summary_by_venue` — every
  venue's entry for that data_type, from the same `by_venue_data_type` rollup the `venue`+`data_type` path already
  used — with 2 new regression tests (cross-venue filtering, and a matching-nothing case proving it doesn't
  fabricate). Doc's "Known limitation, disclosed here" callout rewritten as the fixed reality with a Source
  citation. **Genuinely unfixable this session, reframed + filed rather than left as-is**: BRIDGE (and, found via
  a concurrent sibling-session edit landing mid-pass, LP_MINT/LP_BURN) — all three need a brand-new execution
  engine, and the dispatch gate for all three lives in `external_instruction_api.py`, which this pass's own
  file-coordination boundary reserves for the sibling session. Reframed to accurate client language ("recognised,
  honest 501; no execution engine built yet" instead of "Coming soon") and filed as a new P2 todo above (does not
  duplicate the existing BRIDGE issue doc, extends it to cover LP_MINT/LP_BURN too). **"suspended" reframed
  without weakening the fact**: strategy-service's two seeded counterparties really do carry a non-ACTIVE
  `CounterpartyStatus` today — verified against `unified_api_contracts/internal/domain/signal_broadcast/registry.py`
  directly. Caught and corrected my own first-draft overclaim here: I initially wrote that the registry
  "activates both automatically" at the stated 2026-09-01 launch window: false — `_LAUNCH_WINDOW_START` only
  feeds `CounterpartyEntitlement.active_from` (billing/audit metadata), nothing in the module or its callers
  reads the clock to flip `Counterparty.status`, so activation is a deploy-time code change, not a scheduled
  cutover. Rewrote to say exactly that instead of the false "automatic" claim. **ev-check/ev-assumed sweep
  (operator directive item 3)**: all 13 non-legend `ev-check` markers read in full and checked against the fact
  each one claims. 10 are the doc's own honest-uncertainty convention over genuinely-variable or
  genuinely-not-independently-read shapes (inherently correct as hedged, not defect disclosures — left as-is,
  same reasoning the 2026-08-21 predecessor session recorded). 3 were concrete, checkable claims and all 3 came
  back TRUE — flipped to `ev-verified` with citations: (1) none of execution-service/instruments-service/MTDS
  mount UTL's `create_auth_router` (`/auth/login`/`/auth/me`) — only client-reporting-api does, confirmed by a
  repo-wide grep across all three trees, not just the entry file; (2) client-reporting-api's daily-equity CSV
  export really does round 6dp for BTC accounts / 2dp otherwise and really does return 200+"No data\n" (not 404)
  for an empty curve, verified against `exports.py:160-166` directly; (3) the `CanonicalPersistEnvelope` field
  list (16 fields) read from `unified-api-contracts/unified_api_contracts/events/persist.py` and written out in
  full rather than left as "not read this session". Zero false ev-check claims found. **Ratchet**
  (`check_artefact_claim_ownership.py`): started at 249 open markers (baseline 247 — already over before this
  session touched anything; isolated via a legend-excluding marker count on origin's vs the working copy's
  `platform-api-reference.html` that this file's own edits net to zero, so the +2 was fleet-wide drift from
  already-committed changes to sibling artefacts this task does not own, not something this session introduced).
  The 3 ev-verified flips above are real marker closures, not reframes-to-dodge-the-count, and net the whole
  workspace to **246 — under baseline, ratchet compliant**. Final banned-phrase grep: 0 hits for all 7 phrases
  (the one literal "pending" substring left is inside "depending", not a disclosure).
  Shas: `market-tick-data-service@<pending-ship>`, `unified-trading-pm@<pending-ship>` — see checkboxes/commit
  trailer for the landed shas.

- **2026-08-21 — execution-service QUOTE tick-ingestion no-churn completion (this session, sibling
  execution-service scope: QUOTE/repricer tick path only — external_instruction_api.py/
  external_instruction_defi.py/order_tracker left untouched per the file-coordination boundary)**: the QUOTE
  follow-up todo above turned out to already be MOSTLY done before this session started —
  `execution_service/engine/feature_tick_subscriber.py` (execution-service@0be361333) already reads the
  `EventTransport` facade and drives `QuoteMaintainer.on_underlying_tick()` per tick, wired into the deployed
  `api.main` lifespan — the todo's ">1 day, needs a tick-source decision" framing was stale. The real remaining
  gap, found by reading the actual code: `on_underlying_tick` resubmitted fresh BUY/SELL LIMIT orders to the venue
  on EVERY tick unconditionally, even when the underlying didn't move the quantized bid/ask/size — real
  venue-order-spam churn, not the doc's "no live quote reaches a venue" framing. Built + tested: `QuoteMaintainer`
  now tracks the last order state actually submitted per instrument and only republishes when it changes (6 new
  tests: repeated-price suppression, resubmit-after-real-move, sustained-clamped/stale-move suppression, a new
  `unregister_instrument` method clearing the memo, confirming `QuoteInstruction.refresh_cadence_ms` — the
  STRATEGY-side cache cadence, a distinct concept per
  `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md` — has zero throttling effect
  on this tick-driven loop, and an empty-shard no-op). Also fixed 2 stale docstring claims found while reading the
  code (`delta_proxy_repricer.py`/`quote_maintenance.py` both said "no EventTransport tick subscriber exists" —
  false; `quote_maintenance.py` also cited a dead `feedback_market_making_reference_price_model.md` memo,
  confirmed via `find` not to exist anywhere in this repo). Drafted (held back, see below) 4 matching
  `platform-api-reference.html` QUOTE prose corrections. Flipped 2 already-stale `- [ ]` todos in the delta-proxy
  issue doc (both predate this session — the receipt-path + tick-loop wiring were already real, independently
  verifiable against origin right now regardless of this session's own unshipped work).

  **NOT SHIPPED this session — code complete, blocked on an external cross-repo dependency, not a defect in this
  work**: `quality-gates.sh` in the non-isolated checkout failed on ONE pre-existing, unrelated test
  (`tests/unit/test_external_instruction_api.py::test_non_trade_action_returns_501_not_a_silent_drop`, expected
  501 for BORROW, got 200) — traced to the sibling execution-service session's own live, uncommitted BORROW/REPAY
  wiring-in-progress (their scope, untouched here; 8892/8893 other tests passed, all this session's own new tests
  included). Retried via `quickmerge.sh --agent --isolated` (evacuates named files into a clean worktree at HEAD,
  immune to that foreign WIP) — that attempt instead hit STAGE 1's dependency-validation pre-flight:
  `unified-api-contracts` DIFFERS from `origin/live-defi-rollout` (23 files dirty — `PredictionMarketCategory`-
  deletion work, the SAME T1 registry-cluster session already named blocking `batch-live-reconciliation-service`'s
  ship earlier in this plan's Progress Log). Per the AGENT path the blocked quickmerge itself printed ("do NOT use
  --dep-branch — commit the dependency changes first, in the dep repo"), and per the multi-agent liveness gate
  (recently-touched, genuinely live — not a dead claim to inherit), `unified-api-contracts` was left untouched and
  watched for 25 minutes (60s-interval progress-metric watchdog on dirty-file count) with zero change — confirmed
  not a fetch-staleness artifact (`unified-api-contracts` local HEAD == freshly-fetched `origin/live-defi-rollout`
  HEAD, both `d44de9fb`). Work is intact, fully diffed and verified uncommitted in the `execution-service`
  worktree at `.tabs/2/execution-service` (4 files: `execution_service/engine/quote_maintenance.py`,
  `execution_service/engine/delta_proxy_repricer.py`, `tests/unit/engine/test_quote_maintenance.py`,
  `tests/unit/engine/test_feature_tick_subscriber.py`) — ready to ship per the exact command in the todo above the
  moment `unified-api-contracts` is clean. The drafted `platform-api-reference.html` QUOTE prose is held back
  (not pushed) until that code todo actually ships, so the doc's "✓ verified 2026-08-21" claims cite code that is
  actually on origin, not just locally staged.

- **2026-08-21 — CTO handoff proposition + corrections fold-in pass (this session).** Read
  `/tmp/cto_handoff.txt` (the "Odum External Delivery Platform — CTO Handoff", evidence baseline 20 Aug 2026, one
  day stale against today's ships) in full and worked it against `platform-api-reference.html` (verified real size
  at session start: 3586 lines, not the ~2.1k revert-clobber trip-wire) plus this plan.
  **Added**: a new client-facing "What this platform is" proposition block in the header (before the Contents
  nav) — the handoff's headline proposition, its four-row "two primary hooks" table (five asset groups / live plus
  batch / lifecycle continuity / modular responsibility), and its 8-item counterparty capability list, all
  rewritten into this doc's own house style (`.keypoints`/`.callout`/plain lists — no invented numbers, no
  internal-audience language: dropped the handoff's "prevent the implementation from collapsing" framing,
  "Corrections" section title, and epic-breakdown instructions entirely, per this task's explicit instruction to
  keep only client-facing content). Deliberately did NOT reproduce a "measured coverage matrix" inline — pointed
  instead to `platform-external-api-walkthrough.html`, which already owns that narrative per this doc's own §00
  division of labor, rather than duplicate/drift a second copy of coverage numbers.
  **Fixed — genuine self-contradictions found while reading the file end-to-end** (the handoff's correction
  "Instruction support prose contradicts audited table" — Contract/P0 — turned out to still partially apply, in a
  different spot than the handoff's own evidence baseline): §04's endpoint summary line and request-body heading
  still read "TRADE executes, everything else returns 501" / "the only variant that executes", directly
  contradicting the accurate 12-of-15 table two paragraphs above them; §07's error reference still said "13 of
  the 15 instruction types" return 501, also contradicting §04. Fixed all four to cross-reference the (already
  correct) §04 table rather than restate a number, so the fix holds regardless of which lane is currently
  changing that count. Also fixed a real undercount: the header's "8 Endpoints documented in full depth below"
  stat predates §06 (signal-leasing) being added to the page — recounted `class="ep"` blocks directly (`grep -c`)
  and corrected to 14, with a breakdown. Fixed §07's "All six endpoints" (500 row) to "Every endpoint on this
  page", matching the style already used in the 401 row, so it stops needing a hand-maintained count.
  **Verified re: task's "already-done" baseline** — all confirmed still true against current HEAD: MTDS
  availability `data_type`-without-`venue` fix (market-tick-data-service, §03's callout, already landed and
  disclosed with a real Source citation); the ev-check/ev-verified markers throughout are the prior session's
  already-completed sweep, no false claims found; `check_artefact_claim_ownership.py` — 246 open markers, baseline
  247, ratchet-compliant, unchanged by this session's edits (no new `st-plan`/`st-part`/`ev-check` spans added —
  every new sentence is plain prose or reuses the doc's existing marker vocabulary as-is).
  **Task item 3 (re-verify instruction-table rows against execution-service commits since `d7ef159405`)**:
  `d7ef159405` resolved to a `unified-trading-pm` commit (2026-08-21 07:44:52+01:00, not an execution-service sha —
  the task's own phrasing was ambiguous, resolved by checking both repos). `git -C execution-service log --oneline
  --since=<that timestamp>` returns zero commits — nothing has landed in execution-service since. **Important
  caveat found, not fixed by this session (T4/execution-service's own lane, actively in flight — do not
  duplicate)**: the doc's current instruction-table content (BORROW/REPAY "wired 2026-08-21", `cancel_scope=
  ALL_FOR_STRATEGY_INSTANCE` "wired 2026-08-21", the 12/15 split) describes code that is **uncommitted and
  mid-merge-conflict** in the local execution-service worktree at inspection time (`git status --short` showed
  `UU execution_service/api/external_instruction_api.py` plus several `M` files; `git blame` on the new dispatch
  branch showed "Not Committed Yet"). Direct confirmation against `origin/live-defi-rollout` HEAD (`8d4356bf2c`,
  which equals local HEAD — not behind, so this is live in-progress work, not a stale pull): `cancel_scope=
  ALL_FOR_STRATEGY_INSTANCE` is still an honest 501 there (`"is not supported — no ..."`), and
  `external_instruction_defi.py` at that ref has no BORROW/REPAY entry in `_ACTION_BUILDERS`. The module
  docstring at that same ref states the real current baseline plainly: "10 of the 13 StrategyInstructionV2 action
  types are wired." This session left the doc's 12/15 content untouched (a concurrent T4 session is visibly mid-
  flight on exactly this, per this same plan's own held-back QUOTE-todo note above) rather than reverting it —
  reverting now would just be overwritten again within minutes and risks a real edit-conflict on the same file.
  Flagged here for whichever session next re-verifies the instruction table once the concurrent merge resolves.
  **New finding, filed as a todo above, not guess-fixed**: `ControlInstruction` (`KILL_SWITCH`/`FLATTEN_POSITION`)
  is a real, already-*committed* 16th union member with working dispatch at `origin/live-defi-rollout` HEAD, and
  is completely undocumented on this page — did not add a row for it this session since the table's own counts
  are mid-recount by the concurrent T4 lane; safer to add once that settles than to hand-patch a count that will
  change again within the hour.
  **New follow-up todos filed** (checked first that none were already owned by an in-flight lane — grepped
  `plans/active/*.md` + `plans/active/issues/*.md` for each, zero hits): execution-service client_id↔org_id
  binding (Security/P0), client-reporting-api's unauthenticated global report stream (Security/P0),
  client-reporting-api's 13 no-entitlement-check routes (Security/P1), client-reporting-api's unconditional-
  fixture reporting routes (Integrity/P2), and the `ControlInstruction` documentation gap above (P2, gated on the
  T4 recount landing first). All five are genuine handoff corrections not yet true in code; each is disclosed
  honestly in the doc already (§01/§05 callouts) — these todos are the code-side (or, for `ControlInstruction`,
  doc-side) fix, not a re-disclosure.
  Checker: `check_artefact_claim_ownership.py` — 246 open markers, baseline 247 (unchanged by this session).
  Shipped via `scripts/dev/safe-doc-push.sh` — sha recorded in the commit trailer.
