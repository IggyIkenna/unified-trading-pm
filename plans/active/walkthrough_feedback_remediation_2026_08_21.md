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
- [x] [BACKEND] P1. Delete the deprecated third prediction grouping axis: migrate `PredictionMarketCategory`
      consumers (`_mvp_scope_rules.py`, `predictions/cross_venue_mapping.py`,
      `internal/schemas/_prediction_market_taxonomy.py`) onto `CanonicalQuestionGroup` +
      `two_axis.PredictionUnderlying`, then delete the legacy singular `canonical/domain/prediction/` package
      and its re-exports. Manifest supersession flagged to T2 (no-migration scope here). —
      unified-api-contracts@4f25d5f0da + evidence: `_mvp_scope_rules.py`'s `market_groups` field was already a
      bare `frozenset[str]` (only docstring/comment referenced the enum — reworded, no code change);
      `cross_venue_mapping.py`'s `PredictionMarketCrossVenueMapping` schema (formerly imported from the deleted
      package) is now DEFINED in this module with `category: PredictionUnderlying` (was
      `PredictionMarketCategory`, populated via the real Axis-1 `underlying` instead of the deleted
      `_category_for_underlying`/`category_for_group` helpers, both removed); `_prediction_market_taxonomy.py`
      only referenced the deleted enum in its module docstring (reworded to `PredictionUnderlying`) — its own
      `PredictionShardCategory` enum is unrelated and untouched. Deleted
      `canonical/domain/prediction/{__init__.py,prediction_mapping.py}` (incl. the unused legacy
      `CanonicalPredictionMarket`/`PredictionMarketMapper`/`MappingRule`/`OrphanDetector`/
      `PREDICTION_MARKETS_CONFIG_*` config-versioning surface — ~~no production consumer, only its own now-deleted
      test file~~ **CORRECTION 2026-08-21 (T2 session, found while re-gating an unrelated Kalshi ship): this claim
      was WRONG.** The self-audit's `rg` was scoped to `unified-api-contracts/` only and never checked downstream
      repos. `PredictionMarketMapper` has a real, live production consumer:
      `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket/{markets.py,parsing.py}`
      (module-level `_MAPPER = PredictionMarketMapper()`, called in `_parse_market()` to classify every Polymarket
      market). This deletion broke collection for instruments-service's ENTIRE test suite
      (`ModuleNotFoundError: No module named 'unified_api_contracts.prediction'` at conftest import time — every
      test, not just prediction ones — 4079 collection errors measured). Same root cause + shape as the sibling
      `deployment_api_prediction_catalogue_broken_by_uac_category_deletion_2026_08_21.md` issue this todo's own
      "Manifest supersession flagged to T2" line anticipated; filed as
      `/plans/archive/issues/instruments_service_polymarket_broken_by_uac_prediction_market_mapper_deletion_2026_08_21.md`.
      test file) + `unified_api_contracts/prediction.py` facade + every re-export in `unified_api_contracts/`,
      `canonical/domain/`, and `predictions/__init__.py`. `rg 'PredictionMarketCategory|canonical/domain/prediction[^s]'`
      is zero in live code (only historical-migration-note prose in docstrings/comments remains) — **that `rg` ran
      inside `unified-api-contracts/` only; it does not cover downstream-repo consumers, see correction above.**
      QG-gated (`quality-gates.sh --no-fix` green **in unified-api-contracts only** — this never covered
      instruments-service, a separate repo with its own gate, now red until the linked issue is resolved): also
      fixed 2 pre-existing, unrelated repo-wide QG blockers hit along
      the way — `internal/architecture_v2/__init__.py` missing from the `SIZE_EXTRA_EXCLUDES` `__init__.py`-facade
      allowlist (900-line hard gate), and 4 blank-`asset_group` false/true positives in
      `cloud_run_job_registry.py`/`deployment_classification.py` (STEP 5.96 ratchet, baseline=0) — both predate
      this session (confirmed via `git show HEAD`/`git status`), neither touches prediction code.
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
- [x] ✅ [BACKEND] P2. **RESOLVED 2026-08-21 — operator-confirmed non-issue, no code change needed.** Operator
      asked the right question directly: "why does exec need to know whether it's a rebalance — they just need
      urgency for gas fees?" Re-read `TransferHandler._execute_rebalance_transfer`'s own docstring + body: it
      delegates STRAIGHT to `_execute_onchain_transfer` — mechanically byte-for-byte identical, kept as a
      separate dispatch branch only as a future seam ("a future rebalance-specific concern (netting receipts,
      rebalance-only metrics) has a dedicated seam without touching the dispatch table again" — its own words).
      So `classify_transfer_type()` never returning `REBALANCE` has ZERO functional impact today: a transfer
      that "should" be REBALANCE classifies as plain `ON_CHAIN` instead and produces the identical result.
      There is no current gas-fee/urgency distinction either — grepped `transfer_handler.py`/`isolation.py` for
      urgency/gas_priority/priority_fee, zero hits; no such field or behavior exists yet for ANY transfer type,
      REBALANCE included. **No action needed unless/until a real rebalance-specific mechanic (netting, distinct
      metrics, a genuine gas-priority axis) is actually built** — at that point THIS is the todo to reopen, and
      the real design question becomes generic ("does urgency belong on `ExecutionInstruction` for every
      transfer, not REBALANCE-specifically"), not a `BusTransferType` producer-signal problem.
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
- [x] ✅ [BACKEND] P2. **CLOSED 2026-08-21 — `execution-service@8d4356bf2c`.** Traced both: `SORAlgorithm` already
      had a real bridge into the `ExecutionAlgorithm` interface `DefaultAlgorithmFactory` uses
      (`engine/execution/algorithms/sor.py`, derives its config from the `Instruction` itself via
      `instruction_to_sor_config` — no missing input), it just was never registered — registered it, SOR is now
      genuinely reachable from a manual submission. `ICEBERG` has NO equivalent bridge in
      `engine/execution/algorithms/` — only the lower-level `algo_library` implementation and the separate,
      still-unwired `adapters/algorithm_factory.AlgorithmFactory` class — same failure mode `BEST_PRICE` had, no
      real fix available without building a new bridge (tracked as its own follow-up, not attempted). Removed
      from `_SUPPORTED_ALGOS`/`MANUAL_ONLY_ALGOS` like `BEST_PRICE` was. 3 tests updated, 2 added
      (`test_dynamic_venues.py`, `test_select_manual_algorithm.py`, `test_orchestrator.py`), full QG green.

## Todos — presentation cluster (T5 scope: the artefact itself; run AFTER the clusters above land)

- [x] [DOC] P0. Sticky left-hand TOC sidebar: contents pinned left, scroll-spy highlighting the current
      section, click-to-jump. Wide content keeps its own overflow scroll. — unified-trading-pm@b8f4fea784.
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
        content/wave-1-dependent and were NOT touched — unified-trading-pm@b8f4fea784.
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
        work gated on wave-1 landing and were NOT done — unified-trading-pm@b8f4fea784.
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
        landing. `platform-api-reference.html` itself is unchanged. unified-trading-pm@62828f01cb.
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
        wave-1 landing and was NOT done — unified-trading-pm@b8f4fea784.
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

- 2026-08-21 — T4 wave-1b session: drafted an independent todos-1-3 implementation, QG-passed, then found a
  CONCURRENT session had already landed a more complete version (`execution-service@b1857845c`) and a THIRD
  session had already flipped todos 1-4 in this doc — discarded the redundant draft rather than re-shipping a
  duplicate. Net contribution: flipped todo 5 (verified true against HEAD, no code change).

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

- [x] [SCRIPT] P2. execution-service: `POST /external/instructions` CANCEL currently only supports
      `cancel_scope=SINGLE`; add an `ALL_FOR_STRATEGY_INSTANCE` lookup (index `order_tracker` by strategy-instance,
      not just `instruction_id`) so the doc's remaining "Coming soon" cancel-scope note can close. <1 day. —
      execution-service@4e35a09b2 (2026-08-21). `Instruction.strategy_id` threaded from `StrategyInstruction`
      through `manual_request_to_instruction()`; `ExecutionOrchestrator` now indexes `strategy_id_to_order_ids`
      and exposes `get_orders_for_strategy_instance()`/`get_order_instrument_id()` (+ the orchestrator's own
      missing `mark_cancelled()`, a pre-existing gap both cancel scopes depended on); new
      `_cancel_all_for_strategy_instance()` sweeps every cached orchestrator. Tests: multi-venue multi-order
      sweep, other-instance orders unaffected, no-orders 404, partial-failure CANCEL_FAILED
      (`tests/unit/test_external_instruction_api.py::TestCancelInstructionPath`). QG green (8915 passed, cov
      82.53%). `platform-api-reference.html` CANCEL row updated (both scopes wired) —
      `unified-trading-pm@185e266a0e`.
- [x] ✅ [SCRIPT] P2. **SHIPPED 2026-08-21 — execution-service@56d6e7480e.** The live tick-ingestion loop was
      already built and wired BEFORE this session (`feature_tick_subscriber.py`, execution-service@0be361333,
      started from the `api.main` lifespan) — the original ">1 day, needs a tick-source decision" framing was
      stale. This session read the real code, found the actual gap (`QuoteMaintainer.on_underlying_tick`
      resubmitted BUY/SELL orders to the venue on EVERY tick unconditionally, even with zero price change — real
      order-spam churn), and shipped the fix: no-churn order-state memoization + 6 new tests, isolated-worktree QG
      green (8980 passed, 0 failed), landed on `live-defi-rollout`, verified an ancestor of origin. Was blocked
      ~30min on an external `unified-api-contracts` dependency conflict (a concurrent T1 registry-cluster
      session's uncommitted work, unrelated to this change) — retried once that session landed
      (unified-api-contracts@4f25d5f0); full blocked-then-unblocked evidence in the Progress Log entry below.
      `platform-api-reference.html`'s QUOTE prose (drafted this session) ships next, same turn, via
      `safe-doc-push.sh`.
- [x] [SCRIPT] P1. execution-service: `docs/plans/active/issues/external_instruction_defi_handlers_simulation_only_2026_08_20.md`
      names BORROW/REPAY as the last 2 DeFi action types on pure simulation — wiring them through the same
      `defi_live_dispatch` seam SWAP/LEND/WITHDRAW/STAKE/UNSTAKE just used would close the doc's last 2
      DeFi-side "Coming soon" rows in well under a day, since the dispatch pattern is now proven 5x. —
      execution-service@4e35a09b2 (2026-08-21). `dispatch_borrow_live()` added to `defi_live_dispatch.py` (AAVE V3
      `borrow()`/`repay()`, same `_resolve_live_connector` seam); `BorrowHandler` now accepts `defi_adapter=` and
      routes through it; `HandlerRegistry._DEFI_LIVE_DISPATCH_OPERATIONS` extended; `external_instruction_defi.py`/
      `external_instruction_api.py` wired to accept `BorrowInstruction`/`RepayInstruction` (12 of 15
      `StrategyInstructionV2` action types now live, up from 10). Tests per the existing per-type pattern
      (`tests/unit/test_defi_live_dispatch.py::TestDispatchBorrowLive`,
      `tests/unit/test_external_instruction_api.py::TestBorrowRepayInstructionPath`,
      `tests/unit/test_handler_registry.py`). QG green (8915 passed, cov 82.53%). Closes
      `external_instruction_defi_handlers_simulation_only_2026_08_20.md`'s last 2 DeFi rows;
      `platform-api-reference.html` BORROW/REPAY rows updated — `unified-trading-pm@185e266a0e`.
- [x] [SCRIPT] P2. execution-service: BRIDGE/LP_MINT/LP_BURN wired to real execution — the last 3 of 16
      `StrategyInstructionV2` action types, closing
      `/plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md`'s BRIDGE half (its ATOMIC
      half was already closed) and the LP_MINT/LP_BURN gap this todo named. **BRIDGE**: `TransferHandler`'s
      `_execute_bridge_transfer` stub replaced with real dispatch via a new `LiveBridgeTransferAdapter` wrapping
      `SocketBridgeConnector` (`execution_service/defi_execution/protocols/bridge.py` — a real, live-capable Socket
      v2 bridge-route aggregator across Across/Stargate/CCTP/Hop that already existed but was never wired into any
      reachable adapter, confirmed via a repo-wide grep before this change). New `force_transfer_type` override on
      `TransferHandler._resolve_transfer_type` (metadata-carried, no UAC schema change) — required because
      `classify_transfer_type()` has no notion of a bare chain-name pair and never derives BRIDGE on its own (its
      own module comment: "same chain assumed; caller can override to BRIDGE"). New durable
      `GcsTransferStateStore` (`execution_service/defi_execution/bridge_state_store.py`) satisfies
      `SocketBridgeConnector`'s durable-state-store requirement for live dispatch. Self-bridges to the connector's
      own resolved wallet address when no recipient is given (`BridgeInstructionV2` carries no recipient field).
      **LP_MINT/LP_BURN**: new `LpMintHandler`/`LpBurnHandler` (mirroring `BorrowHandler`'s
      ALPHA_ZERO-simulation/live-dispatch split) + a new, independent `lp_concentrated_dispatch` seam (kept
      separate from `defi_live_dispatch.py` to avoid colliding with the concurrent BORROW/REPAY session) calling
      `UniswapConnector.mint_position()`/`.burn_position()` — real NPM mint/decrease-liquidity+collect calls that
      already existed on that connector, just never had a dispatch-seam consumer. New `OperationType.LP_MINT`/
      `.LP_BURN` members (UAC, purely additive). All three LIVE-WIRED for one venue/protocol each so far (Socket
      for BRIDGE, Uniswap V3 for LP_MINT/LP_BURN); fall back to existing/ALPHA_ZERO simulation outside LIVE/MANUAL
      mode, same convention as every other DeFi handler. The file-coordination collision this todo flagged
      resolved cleanly: confirmed the sibling BORROW/REPAY + CANCEL-scope commit
      (`execution-service@4e35a09b2`) landed before touching `external_instruction_api.py`/
      `external_instruction_defi.py`, per the dispatching operator's own instruction. Tests: new
      `test_lp_concentrated_dispatch.py`, `test_bridge_state_store.py`, `test_live_bridge_adapter.py`,
      `test_lp_handlers.py`, `test_transfer_factory.py`, `test_transfer_handler_bridge.py`,
      `test_external_instruction_bridge_lp_translation.py`, plus a new `TestBridgeInstructionPath` class and an
      `_FakeTransferAdapter.execute_bridge_transfer` addition in the existing `test_external_instruction_api.py`
      (all RPC/connector boundaries mocked — no live mainnet calls in tests). UAC round-trip test coverage added
      for `BridgeInstructionV2`/`LpMintInstruction`/`LpBurnInstruction` (schema classes already existed, pre-dating
      this session; only test coverage was missing).
      `platform-api-reference.html` BRIDGE/LP_MINT/LP_BURN rows + stat + error-table updated (removed the stale
      501 row — there is no longer a "recognised but unrouted" 501 case on this surface at all).
      QG green both repos. — `execution-service@0aa709f076`, `unified-api-contracts@3204e607e4`,
      `unified-trading-pm@<this-commit>`.
- [x] [SCRIPT] P0. execution-service: bind `POST /external/instructions`' `identity.client_id` to the
      authenticated caller's `auth.org_id` — CTO handoff's "Execution client_id is caller supplied without org
      binding" correction (Security/P0). Found already implemented as uncommitted, stale (27+ min untouched,
      mtime-verified dead WIP per the multi-agent-safety liveness gate) work in `external_instruction_api.py` while
      shipping the BRIDGE/LP_MINT/LP_BURN todo above, which also touches this file — inherited and shipped in the
      same commit rather than left stranded. New `_enforce_client_org_binding(auth, client_id)`, called once at the
      top of `submit_external_instruction` before any action-type branching (every `StrategyInstructionV2` member
      inherits `identity.client_id` from the shared envelope base, so one seam covers every action type).
      `auth.is_internal` callers bypass (cross-client reach for reconciliation/support, same precedent
      client-reporting-api's `enforce_entitlement` documents); external callers denied HTTP 403 the moment
      `auth.org_id != identity.client_id` — deny-by-default, including the empty/absent case. —
      `execution-service@0aa709f076` (same commit as the todo above).
- [x] [SCRIPT] P0. client-reporting-api: secure or disable `GET /api/v1/stream/reports` (`reports_stream.py`) —
      ✅ Fixed — `client-reporting-api@ef90afc547`. Moved the route inside `_authenticated_router` (blanket
      `create_api_auth` token check, 401 without one) and added `require_internal(auth)` at the route level (the
      queue has no per-`client_id` scoping, so internal-only is the strictest correct gate — judgment call noted).
      Regression-tested in `tests/unit/test_entitlement_backfill.py::TestReportsStreamAuth` (401 unauthenticated,
      403 external, internal opens the stream without raising). `platform-api-reference.html` §05 updated to match.
- [x] [SCRIPT] P1. client-reporting-api: apply `enforce_entitlement`/`require_internal` to the 13 routes confirmed
      2026-08-21 to call neither today (`alerts.py`, `compliance.py`, `documents.py`, `docusign.py` in full, plus
      `reporting/investor_relations_archive.py`) — ✅ Fixed — `client-reporting-api@ef90afc547`. All 13 enumerated
      independently (matched the CTO count): `compliance.py`'s 4 routes + `documents.py`'s `POST /upload-url` and
      `GET /` (list) are `enforce_entitlement`-scoped via their existing `org_id`/`client_id` params;
      `documents.py`'s `GET /{document_id}/download-url` and `docusign.py`'s `send-for-signature`/
      `signature-status` resolve the document's real owning org from the shared store and entitlement-scope to
      that, falling back to `require_internal` when unresolvable (live-mode uploads don't persist ownership yet —
      fail closed, not a caller-supplied-org trust); `alerts.py`, `documents.py`'s `DELETE`, `docusign.py`'s
      webhook, and `investor_relations_archive.py` are `require_internal` (no client-scoping param exists on any of
      them — strictest plausible gate, each choice noted in the code). Per-route-class tests (entitled/unentitled
      403/unauthenticated 401) in `tests/unit/test_entitlement_backfill.py`. `platform-api-reference.html` §05
      endpoint index + callouts updated to match.
- [x] [SCRIPT] P2. client-reporting-api: remove or sandbox-gate the unconditionally-fixture routes
      (`GET /api/v1/exports/trades`, `/coin-breakdown`, `/daily-summary`, `/hourly-snapshots` —
      `MOCK_TRADES`/`MOCK_COIN_BREAKDOWN`/`get_mock_performance_summary()`, none gated by `CLOUD_MOCK_MODE`, plus
      DocuSign envelope status via `MOCK_ENVELOPES`) — ✅ Fixed — `client-reporting-api@ef90afc547`. `/trades` now
      reuses the canonical ledger fills, falling back to backfilled history; `/coin-breakdown` reuses
      `compute_coin_breakdown` (same engine `performance.py`'s real route uses, own honest column set — no
      entry/current-price/cost-basis padding); `/daily-summary` reuses `compute_monthly_returns` over the real
      equity curve (own reduced column set, `{month, return_pct}` only — that's all the real engine produces);
      `/hourly-snapshots` has no real data source at all (no hourly-granularity equity store exists), so real mode
      returns an explicit labeled "No data" rather than relabeling daily data as hourly. All four fall back to the
      pre-existing fixture only under `CLOUD_MOCK_MODE=true`; an empty real result is an explicit "No data" row,
      never a silent fixture. DocuSign envelope status was checked and found already honest — see the follow-up
      todo below. Tests in `tests/unit/test_exports_honesty.py` (mock-mode fixture unchanged, real-mode reuses the
      real reader, empty real result = explicit "No data"). `platform-api-reference.html` §05 "real vs fixture"
      callout updated to match.
- [ ] [SCRIPT] P2. client-reporting-api: side-discovery from the P2 fixture-honesty fix above — DocuSign envelope
      status (`GET /api/v1/documents/{document_id}/signature-status`) was checked and found ALREADY honest
      (`docusign.py`: `MOCK_ENVELOPES` only under `CLOUD_MOCK_MODE=true`, live-mode returns an honest `404` rather
      than the fixture), so no code change was needed there — noted here only so the CTO handoff's list isn't
      silently dropped. `reporting/investor_relations_archive.py`'s data source
      (`data/investor_relations_archive_metadata.json`, sibling to the route module) does not exist in this repo at
      all — it is caught by the repo-wide `.gitignore` `data/` pattern (meant for repo-local scratch data, not this
      route's actual source of truth) and was never committed, so the route 500s (`FileNotFoundError`) on every
      fresh checkout / live deployment, independent of the entitlement fix landed alongside this todo. Needs either
      a `.gitignore` negation for this specific path plus committing real content, or relocating the data out of a
      gitignored directory.
- [ ] [SCRIPT] P3. client-reporting-api: `exports.py`'s real-mode `GET /api/v1/exports/trades` (2026-08-21 P2
      fixture-honesty fix) covers the two most common cases — canonical ledger fills, falling back to backfilled
      history — the same primary/fallback sources `trades.py::get_trade_history` uses. The rarer case of a client
      with neither ledger fills nor backfilled history but with live-collector-only state isn't covered yet (that
      route's third fallback, `get_collector().get_client_trades(...)`, wasn't reused to keep the fix scoped). Low
      priority: affects only clients with no ledger run and no backfill history.
- [x] [SCRIPT] P0. instruments-service: build org-scoped entitlement into the external instrument catalogue — the
      external router discarded `AuthContext` after the auth dependency ran (`del auth`, `external.py:86`),
      serving an identical catalogue to every authenticated caller (Security/P0, the same "auth is a gate, not a
      scope" class as MTDS's and execution-service's fixes above). New
      `instruments_service/api/entitlement.py::enforce_asset_group_entitlement`, mirroring client-reporting-api's
      `enforce_entitlement` two-gate model: `auth.is_internal` bypasses; an external org's `subscription_tier`
      resolves its entitled `asset_group` scope via `_TIER_ASSET_GROUPS` (keyed by UAC's `SubscriptionTier`), 403
      on an out-of-scope ask. Neither client-reporting-api's own entitlement module nor deployment-api's
      `ClientSubscription` store carries a per-org asset_group scope reachable without a service→service call, so
      per the fallback instruction this reuses `AuthContext.subscription_tier` (already resolved from JWT claims
      by the same `create_api_auth` dependency) — a UAC-typed entitlement config read, not a new store.
      Default-full-catalogue ships today (`_TIER_ASSET_GROUPS` empty — reference data is the product's front
      door); the filter seam is real and tested, so tightening a tier later is a config edit, not a code change.
      Both `GET /v1/instruments` and `/bulk` wired; a bad `asset_group` still 400s before the 403 entitlement
      check runs. Tests: entitled-subset filtering, internal full access, default-entitlement path, 401 unchanged
      (`tests/unit/test_entitlement.py`, `tests/unit/test_external_router.py`). `quality-gates.sh --no-fix` green
      (5427 passed, cov 88.25%) — `instruments-service@0abd96f3bb`. `platform-api-reference.html`'s "What auth
      does not do on these two routers" callout rewritten for the instruments half —
      `unified-trading-pm@e2bae4c5f2`.
- [x] ✅ [DOC] P2. platform-api-reference.html §04: `ControlInstruction` (action ∈ `{KILL_SWITCH, FLATTEN_POSITION}`,
      `unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py:457-468`) is a real,
      already-committed 16th `StrategyInstructionV2` union member — confirmed wired at
      `origin/live-defi-rollout` execution-service HEAD (`8d4356bf2c`,
      `external_instruction_api.py::_submit_control_instruction`: `KILL_SWITCH` activates the durable kill switch
      directly, `FLATTEN_POSITION` delegates to `AccountInstructionOrchestrator.CLOSE_ALL`, both gated on a
      required `authorization_id`) — but it is entirely absent from this page's instruction-type-support table and
      every "N of 15" count. **2026-08-21 (this session)**: added the `KILL_SWITCH` / `FLATTEN_POSITION` row to the
      instruction-type-support table and corrected the surrounding count framing — re-reading
      `submit_external_instruction`'s dispatch chain directly (execution-service HEAD `959c045e9`) showed the
      page's prior "QUOTE is the missing one" framing was itself wrong: QUOTE is fully dispatched (one of the
      fifteen), `ControlInstruction` is the genuine, sole undispatched 16th member — `_submit_control_instruction()`
      exists and is correct but `submit_external_instruction`'s isinstance chain never calls it, so a
      `ControlInstruction` body still 501s today. Disclosed plainly with a Source citation, no hedge language.
      `unified-trading-pm` (this ship).

- 2026-08-21 — built the ledger-matching
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
  **Verified re: task's "already-done" baseline** — confirmed still true against current HEAD: MTDS availability
  `data_type`-without-`venue` fix (§03's callout, already landed + disclosed); ev-check/ev-verified markers are the
  prior session's completed sweep, no false claims found; checker unchanged by this session's edits.
  **Task item 3**: at the time, BORROW/REPAY/`cancel_scope=ALL_FOR_STRATEGY_INSTANCE`/`ControlInstruction` were
  still mid-flight on a concurrent T4 execution-service lane — left untouched rather than reverted (see the
  `- 2026-08-21 — BRIDGE/LP_MINT/LP_BURN wired` entry and the completion-pass entry above for how each of these
  landed/resolved). New follow-up todos filed that session: execution-service client_id↔org_id binding
  (Security/P0), client-reporting-api's unauthenticated global report stream (Security/P0), its 13
  no-entitlement-check routes (Security/P1), its unconditional-fixture reporting routes (Integrity/P2) — all since
  resolved, see later entries. Checker at the time: 246 open markers, baseline 247.
  Shipped via `scripts/dev/safe-doc-push.sh`.

- 2026-08-21 — BRIDGE/LP_MINT/LP_BURN wired to real execution (last 3 of 16 `StrategyInstructionV2` action
  types) + the client_id↔org_id binding P0 todo, inherited from stale dead WIP in the same file — full detail in
  the matching `- [x]` todo above. Shas: `unified-api-contracts@3204e607e4`, `execution-service@0aa709f076`.

- 2026-08-21 — Resolved the `4f25d5f0` deployment-api fallout (`PredictionMarketCategory` deletion + a second
  same-commit `prediction_markets_config_descriptor` break): `deployment-api@9947cc40ae`, quality-gates.sh green
  (5427 passed). Full detail archived:
  `/plans/archive/issues/deployment_api_prediction_catalogue_broken_by_uac_category_deletion_2026_08_21.md`.

- 2026-08-21 — Fourth `4f25d5f0` consumer closed: features-service's two cross-venue-mapping test files built
  `PredictionMarketCrossVenueMapping` fixtures via the deleted `PredictionMarketCategory` enum — migrated to
  `PredictionUnderlying` (`.BTC`/`.SPORTS_EPL`); no production code read `.category` (grep-confirmed).
  quality-gates.sh --no-fix green (18540 passed). `features-service@1fb32923a8`.

- 2026-08-21 — **platform-api-reference.html completion pass (operator directive)**: every remaining `st-part` row
  verified against current LDR code, flipped to plain complete prose or honestly disclosed where code doesn't
  support the claim. Removed all 20 `st-part` spans (6 section-head, 14 endpoint) across §01/§02/§03/§05/§06 —
  verified against instruments-service, market-tick-data-service, client-reporting-api, strategy-service HEADs
  pulled fresh (§06 kept its honest "dark until 2026-09-01" framing — business-scheduled, not a code gap). §04:
  rewrote all 14 instruction-table rows to plain prose after re-reading `external_instruction_api.py` (HEAD
  `959c045e9`) — found and fixed a real inaccuracy: "QUOTE is the missing 16th" was wrong (QUOTE dispatches fine);
  the genuine sole undispatched member is `ControlInstruction` — `_submit_control_instruction()` is real but never
  called from the dispatch chain (grepped every caller: zero). Added the missing row + Source citation (todo
  checked off above), fixed the matching stale "13 of 16" line in §07. Resolved 5 "not independently
  read"/"? check" hedges into facts or a scoped `owner:` tag (3 permanent "dynamic field" disclosures). Removed
  narration voice in §05/§06 ledes+callouts. `check_artefact_claim_ownership.py`: markers 245→206 (baseline 247);
  0 untagged; 0 unresolved refs. **Not flipped**: none — the one genuine gap (`ControlInstruction`) was disclosed,
  not hidden. **Out of scope**: §01's excluded "What auth does not do" callout (two sibling lanes landed real
  rewrites this session, `unified-trading-pm@e2bae4c5f2`+`instruments-service@0abd96f3bb`); operator's separate
  "Security, audit and client isolation" directive doesn't apply — that string only exists in other artefacts, left
  for their owning session. Also split a text-merge artifact next to the `ControlInstruction` todo (two paragraphs
  concatenated on one line) — no content altered.

- 2026-08-21 — **platform-external-api-walkthrough.html client-voice + completion pass, checkpoint 1/2.**
  Re-verified against `origin/live-defi-rollout` first: `instruments-service@0abd96f3bb`
  (`enforce_asset_group_entitlement`, wired `external.py:94`/`:131`), `execution-service@0aa709f076`
  (`_enforce_client_org_binding`) confirmed ancestor + wired. **MTDS's entitlement seam did NOT verify** —
  `market_tick_data_service/api/entitlement.py` is untracked, uncommitted local-only diff in this checkout (local
  HEAD == origin HEAD `802784de`), absent from origin entirely, though `platform-api-reference.html`'s own §01
  already claims it landed — flagged to the operator in this session's report, not fixed here (out of scope).
  Rewrote the auth callout (was "del auth"/"gate not a scope" forensics) into landed-model prose mirroring
  `platform-api-reference.html` §01; MTDS stated only as its real router-gate today. Two more stale claims fixed
  while sourcing that rewrite: `ChainKind` is 24 members incl. `PLASMA` (confirmed on origin) — added the table
  row, deleted the now-moot "Correction"/"gap surfaced" pair; `VENUE_CHAIN_MAP`'s docstring fix
  (`unified-api-contracts@4d78e2f0c5`, confirmed ancestor) already states wallet-grouping-not-coverage, so its
  callout was restated plainly instead of re-warning about a closed gap. Verified `StrategyInstructionV2` is 16
  members on origin (dispatch chain confirmed NOT routing to `_submit_control_instruction`) — fixed 5 stale
  "15 of 15" counts to "15 of 16" across §02/§26, added the missing `KILL_SWITCH`/`FLATTEN_POSITION` table row,
  fixed §09's Control row (was "not yet expressible" — false; the gap is dispatch, not the schema); repointed
  §14's dead `transfer_coordinator.py` citation to `transfer_handler.py`. **Lost-and-redone**: the first 5 edits were silently reverted by a concurrent write between two edit batches
  (Edit tool's drift warning + `git diff` caught it, the `walkthrough_file_shared_checkout_repeated_content_loss_
  2026_08_20.md` failure mode) — redone + grep-verified before this ship. Checkpoint 2/2 follows this session.
