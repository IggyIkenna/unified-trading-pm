---
doc_type: epic
title: Execution Master
summary:
  L2 epic owning execution-service — order/transfer handlers, treasury coordinator, custody integration, flash loans,
  the matching engine, MEV protection, and per-incident recon-freeze signal emission consumed by alerting-service.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service, trading-agent-service]
scope: [engineer, admin]
tags: [execution, defi, quality-gates, escalation, live-trading]
related:
  [
    ../archive/2026_07/execution_fidelity_tiers_uac_governed_2026_06_28.md,
    ../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    ../archive/issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md,
  ]
created: 2026-05-21
name: execution_master
tier: L2
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans: []
last_updated: 2026-08-19 # was 2026-08-18 — added "Venue MVP-readiness" P1 section (priority venue/protocol set audit
  # + manual/automated live-mode cross-cutting requirement + instruction/order-type/venue registry finding), see body
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Execution Master

## Report

Live HTML ledger: https://claude.ai/code/artifact/88c59faa-ca5d-4ad6-935f-6ce9aa130d11 (generated 2026-08-19,
`/plan-reconcile execution_master`)

**Owns**: execution-service: handlers + transfers + treasury coordinator + custody integration + flash loan + matching
engine

**Status**: stub created 2026-05-21 by `migrate_epics_2026_05_21.py`. Operator fills body with P0/P1/P2/P3 priority
blocks listing all assigned active plans.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## P0 — must complete before next foundation gate

### [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — execution-service cluster

**status**: 🟠 ACTIVE — QG sweep for execution-service (20 ruff errors) + trading-agent-service (ruff clean). Run
`bash scripts/quality-gates.sh` exit 0 in each. PREREQ: UTL QG green. [vm: vm-trading-core]

- [ ] [CODE] P1. **G12 (execution-side) — emit per-incident recon-freeze signals** that the alerting-service publisher
      (owned in `observability_master`) consumes: symbol-scoped for symbol breaks, account-wide for account-level SEV0s.
      In-scope for May-23. Repo: execution-service. From
      `archive/issues/recon_freeze_armed_never_published_2026_05_27.md`. **Escalated P2→P0 2026-07-12 by operator
      ruling** (plan-reconciliation Q&A finding 367): subscriber code confirmed absent in execution-service; live orders
      currently NEVER blocked by recon-freeze state — safety gap on the passed May-23 critical path; alerting-service
      twin already shipped P0. See plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md §A2.

## P1 — Venue MVP-readiness: priority venue/protocol set (2026-08-19 audit)

Audit scope: CeFi (Deribit, Hyperliquid, Binance, OKX, Bybit, Aster), Ethereum DeFi (AAVE V3, Lido, EtherFi), sports
(Betfair), Polymarket, Kalshi, IBKR, Morpho, Uniswap, CoW Swap, plus custody (Copper, CEFFU) and a Solana basis-trade
placeholder. **Verified 2026-08-19 by direct code read — almost nothing here is greenfield.** All 6 CeFi venues have
real live-wired CCXT adapters (`execution_service/trade_execution/adapters/{deribit,hyperliquid,binance,okx,bybit,
aster}_ccxt.py` — real/sim split via `_place_order_live()` → `_submit_ccxt_order()`). AAVE V3/Lido/EtherFi/Uniswap all
have real on-chain live-execution paths (`defi_execution/protocols/{aave,aave_live,lido,etherfi,uniswap,
uniswap_live}.py`, paper-mode-gated broadcast). Betfair has a real adapter
(`sports_execution/adapters/exchanges/betfair.py`). Kalshi is genuinely live (RSA-PSS signing,
`sports_execution/adapters/exchanges/kalshi.py`). IBKR is real but capability-gated off mainnet
(`trade_execution/adapters/ibkr_tradfi.py` — UAC declares `place_order` unsupported until batch=paper=live is proven
end-to-end for tradfi). **Only CoW Swap is genuinely greenfield** (zero hits anywhere in the repo beyond 3 unrelated
design-comment mentions).

- [ ] [INFRA] P1. **CeFi IAM/secret-scope grants — bybit, hyperliquid, okx, aster.** (Deribit's IAM was already fixed
      live this session — don't redo it; binance's `{read,trade,write}` triple is already complete.) Cross-reference,
      don't duplicate: `/plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md` (3 open / 4
      done) already tracks this — 8 venues including these 4 still lack the full `{venue}-{read,trade,write}-api-key`
      GSM secret triple. Grant the specific secrets per `execution_service/service_config.py`'s existing field
      convention (`{venue}_trade_api_key_secret_name` etc.) and re-verify a real API call succeeds per venue, not
      just an IAM policy dump. **OKX additionally has no secret-name fields in `service_config.py` at all** ("no
      pooled/house entry yet, client-scoped only" per its own comment) — add them before the grant can even target
      something. Done-when: a live authenticated call (order-status or balance query) succeeds per venue.
- [ ] [BACKEND] P2. **AAVE V3 / Lido / EtherFi live-wiring audit — confirm the paper-mode gate is exercised, not
      dormant.** All three (`defi_execution/protocols/{aave_live,lido,etherfi}.py`) build/sign/broadcast real
      transactions in live mode and are deliberately no-op in paper mode. Audit: has the live broadcast path ever
      actually run against a real (even testnet) chain, or does `paper_trade=True` sit permanently on in every
      deployed config? Done-when: a dated log/tx-hash citation of a real broadcast, or an explicit statement that
      none has ever run.
- [x] [BACKEND] P1. ✅ **Betfair execution — operator correction 2026-08-19: use the real adapter, not manual-only.**
      A prior framing treated Betfair as manual-entry-only with "no adapter needed" — superseded. A real execution
      adapter already exists: `execution_service/sports_execution/adapters/exchanges/betfair.py` (+
      `betfair_order_mapping.py`), canonical `place_order`/`cancel_order`/`list_orders`, no stub markers. Wire it as
      BOTH a manual-live venue (human executes on Betfair directly, system books the fill via the manual-instruction
      path) AND an automated-live venue (this adapter executes directly) — see the manual/automated live-mode todo
      below, this is its first concrete instance. Distinct from the MTDS market-data side: the live market-data WS
      connector is a separate, still-BLOCKED-CREDENTIALS concern tracked in
      `/plans/active/issues/prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md` (1 open / 3 done) —
      cross-reference, do not duplicate; that doc is about MTDS market data, not this execution-adapter wiring.
- [ ] [BACKEND] P2. **Polymarket dead-code audit — `sports_execution/prediction_markets/polymarket.py` (250 lines)
      is unreferenced in production.** Its own docstring says "not yet wired to a live fetch call anywhere in
      execution-service"; only consumers are `__init__.py` re-exports + its own unit test. The REAL live path is
      `sports_execution/adapters/exchanges/polymarket_clob.py` (558 lines, genuinely used by routing.py,
      sports_factory.py, the odds aggregator). Either delete the dead file (per CLAUDE.md "delete deprecated code, no
      shims") or state why it's kept — don't leave it ambiguous.
- [ ] [INFRA] P2. **Kalshi / IBKR IAM extension** — same secret-provisioning pattern as the CeFi grants above; extend
      `/plans/active/issues/per_venue_scope_key_provisioning_incomplete_2026_07_23.md` if it already names these two,
      otherwise fold them into it rather than opening a parallel tracker.
- [ ] [BACKEND] P0. **Morpho flash-loan stub — DECIDED 2026-08-19: fix now, not deferred** (was previously framed
      as an audit/reachability-check; Morpho is a named priority venue and this directly blocks it).
      `RecursiveLoopOrchestrator._submit_flash_loan()`
      (`execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py:704`) unconditionally returns
      `(None, 0)` whenever `self._w3` is set — i.e. **live mode, the only condition that matters for real fund
      movement**:
      ```python
      def _submit_flash_loan(self, request, receiver_address, actions) -> tuple[str | None, int]:
          if self._w3 is None:
              return (f"0xSIM_FLASH_{request.correlation_id[:8]}", 350_000)
          return (None, 0)
      ```
      Both `_flash_open()`/`_flash_close()` treat a `None` tx_hash as failure
      (`RECURSIVE_LOOP_FLASH_REPAYMENT_INSUFFICIENT`), so **every live-mode `OpeningMode.FLASH` request fails at
      this line today**, independent of position state, health factor, or gas budget. Documented in
      `/codex/04-architecture/flash-loan-receiver.md` § "Live-mode flash-loan submission is stubbed" (that doc's own
      closing line — "whether fixing this stub is in scope now is a genuinely open question the operator has not
      decided" — is now stale per this decision; corrected in the same edit as this todo). Address resolution
      (`FLASH_LOAN_RECEIVER_REGISTRY` lookup + `eth_getCode` bytecode check) already works and the deployed
      `RecursiveLeverageReceiver.sol` contracts are real — only the encode-and-broadcast step is missing. Fix: build
      + sign + broadcast the `flashLoan()` tx the same way the already-live-capable PERSISTENT driver (per-iteration
      supply→borrow, no flash loan) makes its real `AAVEConnector` calls — that driver is the reference pattern.
      Cross-reference, don't duplicate: `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`
      (2 open / 18 done) already names this stub as a sub-finding. Done-when: a real testnet `flashLoan()` tx
      succeeds end-to-end through `_flash_open()`/`_flash_close()` with `self._w3` set.
- [ ] [BACKEND] P2. **`AtomicBundleExecutor`/`MulticallBatcher` — separate, still-undecided gap, not conflated with
      the flash-loan fix above.** `algorithms/atomic_bundle_executor.py::execute_bundle` has zero callers anywhere
      in execution-service outside its own file + an `__init__.py` re-export (never invoked), and even its own
      `execute_bundle` loops sequential single-instruction calls rather than building one atomic on-chain tx despite
      its docstring's claim. `algo_library/multicall_batcher.py::MulticallBatcher` does real Multicall3
      grouping/encoding and IS used by `intent_engine.py`, but neither file contains a `send_transaction`/broadcast
      call — encoding-only, no wired submission path. Unlike the flash-loan stub above, the operator has not ruled
      on this one — done-when: either the live submission path is wired end-to-end with a real testnet tx, or
      `AtomicBundleExecutor` is explicitly marked not-production-ready with a tracked follow-up (an `[OPERATOR]`
      scoping call, not assumed).
- [ ] [BACKEND] P1. **CoW Swap — genuinely greenfield, confirmed 2026-08-19** (zero code anywhere in the repo beyond
      3 unrelated design-comment mentions of "CowSwap" as inspiration for `intent_engine.py`/`solver_auction.py`).
      Build a CoW Swap execution adapter from scratch: order-signing (CoW Protocol off-chain order + on-chain
      settlement), quote fetching, order submission to the CoW API, fill tracking. Follow the existing DEX-adapter
      shape (`defi_execution/protocols/uniswap.py` + `uniswap_live.py` as the closest analog — swap-only, no limit
      orders, per the instruction/order-type registry finding below).
- [ ] [DATA] P1. **CoW Swap — historical/batch data capability is required alongside the live execution adapter,
      not optional.** Per the batch=live=paper determinism invariant (CLAUDE.md "Live = batch (event-log
      spine)... paper(W)==batch-rerun(W) epsilon=0") and the operator's explicit question this session ("we also
      need to have historical data for CoW batch-live symmetry... otherwise we can't replay the market data"): a
      live-only adapter with no MTDS/MDPS historical capture means CoW Swap can never be backtested or
      paper-simulated once the execution adapter above lands — batch/paper mode would have nothing to replay
      against for this venue. Tracked on the data side in `mtds_mdps_master.md`'s CoW Swap MTDS/MDPS todo (batch
      adapter + candle-derivation wiring, sequenced against this execution build, following the existing
      `defi_execution/protocols/uniswap.py`-analog MTDS backfill pattern other DEX venues already use) — cite it
      here rather than duplicating; this todo exists so the requirement is visible from the execution-side todo
      too, since it is easy to ship a live adapter alone and consider the venue "done" without it.
- [x] [BACKEND] P2. ✅ **Uniswap gap audit — closed 2026-08-19, code is NOT a gap.** Prior framing assumed Uniswap
      might be partial/simulation-only; verified execution-service has a substantial live V3 execution surface
      (`defi_execution/protocols/{uniswap,uniswap_encoding,uniswap_live}.py`, 479 lines in `uniswap_live.py` alone) —
      real swap execution + LP position management (mint/decrease/collect/burn via NonfungiblePositionManager), same
      paper-mode-gated broadcast pattern as AAVE/Lido/EtherFi. The genuine Uniswap gap is upstream, on the DATA side,
      not execution: `/plans/active/issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md` (1 open /
      1 done) — 199,397 bare UNISWAP/SUSHISWAP manifest rows with no factory-address resolution. Cross-reference,
      don't duplicate; that doc is MTDS/manifest-side, this execution-service side is confirmed fine.
- [ ] [BACKEND] P2. **Copper / CEFFU custody integration audit + non-custodial-transfer research** (exploratory,
      NOT a build commitment — operator has stated custody remains preferred). Copper
      (`execution_service/custody/copper.py`, 285 lines) looks like a real, complete implementation (HMAC signing,
      transfer/balance/wallet-list, no stub markers) — audit whether it's actually exercised end-to-end against a
      live Copper sandbox/account, or only unit-tested. CEFFU (`execution_service/custody/ceffu.py`, 325 lines) is a
      **deliberate, explicit stub** — every method raises `NotImplementedError` pending an operator-delivered API
      spec; this is a deliberate design choice awaiting that spec, not an oversight. SSOT:
      `/codex/04-architecture/custody-providers.md` (carries its own 6-item CEFFU "Open questions" checklist under
      §2.4) — reference, do not duplicate. Separately, as an explicitly exploratory / low-conviction research spike:
      research what a non-custodial wallet-transfer option would require (self-custodied wallet + on-chain transfer
      instead of a custody provider) — research output only, not a build todo, until/unless the operator says
      otherwise.
- [ ] [OPERATOR] P3. BLOCKED-OPERATOR-DECISION — **Solana↔Ethereum basis-trade BRIDGE architecture** (distinct from
      the per-venue Solana audit below, which resolves the venue-naming half of this placeholder). Bridge
      architecture itself is owned by a separate, parallel agent working only in `codex/` (already landed several
      dated 2026-08-19 codex commits on EVM/Solana bridge architecture — see
      `/codex/04-architecture/transfer-coordinator.md` and its neighbors) — do not duplicate that work here.

### Solana venue set — Jupiter, Raydium, Drift, Pacifica, Jito (real per-venue audit, 2026-08-19)

Operator (2026-08-19), exact words: "jupiter raydium and drift should all be used" for the Solana spot+perp basis
trade, plus Pacifica (already covered by its own dedicated plan) and Jito (LST — the Solana-side equivalent of
Lido/EtherFi, asked about explicitly). Real per-venue grep across execution-service, strategy-service, MTDS,
features-service, instruments-service — not an assumption from "extensively referenced" hit counts:

| Venue | Execution | Strategy | MTDS batch/live | Features |
| --- | --- | --- | --- | --- |
| Jupiter (spot) | live, complete (adapter + swap exec + live WS shipped 2026-08-08) | not applicable to spot-only usage | batch+live, real | generic `dex_pool_swaps` mapping (no venue-specific calculator needed) |
| Jupiter (perps) | **not built** — `JupiterConnector` is swap-only, no perp methods | n/a — no perp surface exists yet | n/a | n/a |
| Raydium | **`supports_live=True`** — real `send_transaction()` via `BaseSolanaConnector`, not simulation-only | **registered**: `CARRY_BASIS_PERP@raydium-hyperliquid-sol-1h-sol-v5-prod` (`spot_venue=raydium`) + `MARKET_MAKING_CONTINUOUS@raydium-sol-usdc-1h-sol-v5-prod` — real slots, not candidate-only | batch (`raydium_classic_amm_handler.py`, 480L) + live (`raydium_defi_ws.py`, 323L), both real | 0 venue-specific hits; covered generically via the shipped `dex_pool_swaps` feature-group mapping (same pattern as Uniswap) |
| Drift | zero Drift-specific code found (confirmed by grep — matches the removal claim below) | n/a | n/a | n/a |
| Pacifica | simulation-only pending an operator wallet-key decision (own dedicated plan tracks this) | **registered**: `CARRY_FUNDING_DISPERSION` + `CARRY_BASIS_PERP` | batch+live, both real, **fully shipped 2026-08-14/15** across all 5 repos | n/a — funding-rate feature path is CeFi-side, Pacifica is `cefi`-classified |
| Jito (LST, jitoSOL) | `stake()`/`unstake()` simulation-only (`supports_live=False`) — needs the `spl-stake-pool` SDK | **registered**: `CARRY_RECURSIVE_STAKED@kamino-jito-hyperliquid-sol-1h-sol-v2-prod` | batch (`lst_rates_handler.py`/`staking_yields_handler.py`) + live (`jito_defi_ws.py`), both real | real (`lst_features.py`, `lst_seasonal_rewards_collector.py`) |
| Jito Restaking (`JITORESTAKING-SOLANA`, separate product) | simulation-only, same SDK gap as jitoSOL | not found registered in any archetype slot | batch only (`restaking_jito_adapter.py`) — **no live connector found**, unlike jitoSOL | not separately audited this pass |

- [x] [BACKEND] P1. ✅ **Jupiter, Raydium, Pacifica, Jito(LST) — confirmed NOT greenfield, matching the memory
      note's caveat that "extensively referenced" needed real verification, not assumption.** Per-venue evidence in
      the table above. Jupiter perps and Jito Restaking's live leg are the only genuine build gaps found, both
      already covered by narrower todos below or by the existing Jupiter+Kamino plan — nothing else in this row
      needs new work.
- [x] [BACKEND] P2. ✅ **Correction to a sibling plan, found during this audit.**
      `/plans/active/solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md` §C's first todo ("Implement
      Kamino `borrow`/`repay`... it currently has `supply`/`withdraw`... — the lending side only") is stale —
      `execution_service/defi_execution/protocols/kamino.py::borrow()`/`repay()` (lines 246/264) are real
      implementations (`_submit_kamino_tx_api_op`: Kamino's Transactions API → sign → broadcast, with a paper-mode
      short-circuit), not stubs. Corrected directly in that plan's own Progress Log rather than left to rot — see
      that doc. Consequence: Jito's `CARRY_RECURSIVE_STAKED` slot above is NOT blocked by a missing Kamino
      execution capability; only Jito's own stake-pool write path (jitoSOL side) remains simulation-only.
- [ ] [OPERATOR] P1. **Drift — reconcile this session's operator request against the standing 2026-08-14 kill
      ruling before any Drift code work resumes.** This session's operator instruction named Drift as one of four
      venues for the Solana spot+perp basis trade; the durable codex ruling
      (`/codex/04-architecture/solana-defi-coverage.md`, 🔴 tombstone 2026-07-16, reaffirmed in the 🟢 REVERSAL
      banner 2026-08-14 — "DRIFT-SOLANA stays removed... nothing in this reversal touches Drift") is a real,
      recent (5 days old at time of writing), twice-stated decision citing a specific $280M Lazarus-attributed hack
      and an unproven ~$0-TVL Velocity relaunch. **This is a genuine SSOT contradiction, not a stale doc** — get an
      explicit fresh operator ruling naming which one governs before writing any Drift-specific code (re-affirm the
      kill, or explicitly reverse it a second time with the current Velocity-DEX risk picture considered). Do not
      silently pick either side.
- [ ] [BACKEND] P2. **Jito Restaking — confirm whether a live-feed connector genuinely doesn't exist or was missed
      this pass.** `restaking_jito_adapter.py` (MTDS) has batch coverage; no `jito_restaking`/`JITORESTAKING` hit
      appeared in `live/connectors/*.py` this session's grep. If genuinely absent, scope whether restaking
      (distinct from jitoSOL LST) needs live coverage for any MVP archetype before building it — don't build
      speculatively.
- [ ] [BACKEND] P3. **Jito Restaking — register an archetype slot if it should trade at all**, mirroring the
      jitoSOL LST pattern (`CARRY_RECURSIVE_STAKED@kamino-jito-...`) if a restaking-specific archetype use case
      exists; today it has adapters at every layer but zero strategy-side registration.
- [ ] [BACKEND] P1. **Manual-live vs automated-live execution mode — DECIDED 2026-08-19: static, per-strategy-
      instance config, cross-cutting requirement, not Betfair-specific.** Operator (2026-08-19), exact words: "the
      whole strategy service and execution need to understand that there's a manual Live mode where everything is
      our own manual execution, and there's an automated Live mode." Applies to EVERY venue in this epic's priority
      set, not just Betfair. **Design decision (no longer open)**: manual-vs-automated is set ONCE when a strategy
      instance is launched — the same shape as the existing paper-vs-live distinction — not a dynamic per-order or
      per-venue-default mechanism. **What already exists** (2026-08-19 audit, build on this, don't rebuild): UAC's
      `OperationalMode` enum already has a `MANUAL` value, consumed in `execution_service/cli/handlers/__init__.py`
      (`OperationalMode.MANUAL` resolves to `LiveExecutionHandler(mode=mode)`, differing from `LIVE` only in
      instruction source — HTTP manual API vs automated strategy signals, not a fully separate engine) and wired
      through `manual_instruction_api.py`/`manual_instruction_helpers.py`. UAC also has
      `ExecutionTrigger = {AUTOMATED, MANUAL_OPERATOR}` — the closest existing primitive to "who executes" — but it
      has exactly one live consumer today (`close_all/_template.py`, the emergency kill-switch close-all path).
      **Build**: (1) add a per-strategy-instance manual/automated flag set at launch time (same launch-config
      surface as the paper/live flag), (2) wire `OperationalMode.MANUAL`/`ExecutionTrigger.MANUAL_OPERATOR` into
      that concrete shape beyond the one close-all call site — `LiveExecutionHandler` dispatch, the
      manual-instruction API, per-venue adapter selection all read the new flag instead of assuming automated.
      Companion strategy-service-side build tracked in `strategy_master.md`'s matching todo (cross-reference, this
      is the execution-service half — the two sides must land the SAME shape). Done-when: launching a strategy
      instance with the manual flag set routes every live order through the manual-instruction/tracking path (no
      automated adapter call), and launching without it behaves exactly as today's automated live path, for at
      least one venue end-to-end (Betfair is the natural first instance per the item above).
- [ ] [BACKEND] P1. **Instruction-type x order-type x venue-capability registry — PARTIAL, confirmed 2026-08-19,
      operator-requested audit.** Operator: "That's supposed to be governed in registries... for all of them" (every
      instruction-type x order-type x venue combination, not just the DEX-swap example that prompted the question).
      Audit found TWO different granularities, neither closing the loop: **(1)** a REAL, ENFORCED registry exists at
      the `OperationType x venue` level — `BaseHandler.supported_operations` + `SUPPORTED_VENUES`, checked in each
      handler's `validate()` (`engine/handlers/base_handler.py` + subclasses) — e.g. `TradeHandler.validate()`
      genuinely rejects a `LIMIT` order missing `limit_price` and checks venue membership. **(2)** The finer
      `OrderType x venue` registry, `unified-api-contracts`' `architecture_v2/order_semantics.py::
      VENUE_ORDER_SEMANTICS`, is genuinely rich (TIF/post-only/make-take/atomic-execution per venue,
      code-scan-backfilled with file:line provenance) but has **zero runtime consumers** — only its own tests and a
      PM-repo doc-generation script (`scripts/openapi/{generate_strategy_prospectus,_capability_gaps,
      emit_capability_gap_todos}.py`) import it; execution-service never reads it. Concretely broken:
      `engine/handlers/swap_handler.py::SwapHandler.validate()` declares a swap-only `SUPPORTED_VENUES` set but
      never checks it, and never reads `instruction.order_type` at all — it always constructs
      `OrderType.MAX_SLIPPAGE` regardless of what was passed in, so a `SWAP` operation carrying `order_type=LIMIT`
      is silently accepted and silently ignored rather than rejected. No validator anywhere enforces the
      instruction-type -> order-type -> venue-capability cross product as a whole (confirmed via UAC's
      `ExecutionInstruction.__post_init__`, which only defaults a missing `order_type`, never cross-validates one).
      **Done-when**: `SwapHandler.validate()` actually reads `instruction.order_type` and rejects anything outside
      its supported set (fixing the dead venue-allowlist in the same pass); a validator wired at instruction-ingest
      time (reusing `VENUE_ORDER_SEMANTICS` as the source-of-truth table rather than inventing a second one) rejects
      an incompatible instruction-type/order-type/venue combination fail-loud, matching this workspace's existing
      fail-loud convention — never silently accepting or silently substituting a different order type than what was
      requested.

## P2 — opportunistic / post-cutover (slot 7 dispatch 2026-06-01)

- [ ] [CODE] P2. **F-32 — size-based MEV auto-escalation (post-cutover).** Operator decision 2026-06-01: MEV mode is
      **directive-driven** for May-23 (F-32 closed for the cutover). Post-cutover, add size-based auto-escalation of MEV
      protection. Repo: execution-service. From `archive/issues/audit03_ikenna_review_routing_2026_05_22.md`.
- G12 escalated to P0 2026-07-12 (see P0 section).

## Assigned active plans

### [`strategy_archetype_latency_deployment_profile_execution_2026_08_10`](../active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md)

**status**: active (`assigned_vm: planning`, AO-dispatched) · **estimate**: 4.0 cal AI-days (class: brand-new)
**title**: Execution — wire archetype-declared deployment-profile requirements into runtime-topology.yaml + derive
deployments from active archetypes. Retagged from `strategy_master` 2026-08-19 (execution_master_scope audit) — the
whole doc is deployment-profile/co-location infra derivation from archetype latency needs, matching the operator's
named "co-location" execution_master scope, not strategy config/parameterization. See
[the audit issue](/plans/active/issues/execution_master_scope_scattered_across_strategy_and_cross_cutting_2026_08_19.md).

## Folded-in epic: Trading Agent Master (folded 2026-08-18)

**Source**: [`trading_agent_master.md`](trading_agent_master.md) (0 corpus references, 42 lines) — folded into this
epic per
[`/codex/11-project-management/epic-taxonomy-2026-08-18.md`](/codex/11-project-management/epic-taxonomy-2026-08-18.md)
(domain 5, Execution service). The source file is kept as archaeology, `status: superseded`, with a banner pointing
here — do not add new work there.

**Owns**: trading-agent-service closed-loop allocator, `AllocationDirective` pipeline, and `StrategyPnlStreamEvent`
consumer. Architecture-unlock (directive pipeline + event contracts + UAC schema + codex SSOT) shipped 2026-05-23;
P3 backlog covers real allocator logic, ML/LLM subscribers, and `performance_features` passthrough.

**Repos**: trading-agent-service (already listed in this epic's own `repos:` frontmatter).

**Assigned active plans**: none declared `parent_epic: trading_agent_master` at fold time — new work in this area
now declares `parent_epic: execution_master`.

**Archived plans**:
[`trading_agent_service_architecture_unlock_2026_05_22`](../archive/2026_05/trading_agent_service_architecture_unlock_2026_05_22.md) —
architecture-unlock (directive pipeline + event contracts + UAC schema + codex SSOT), shipped 2026-05-23.
