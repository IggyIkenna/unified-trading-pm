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
- [ ] [BACKEND] P1. **Morpho strategy-wiring + flash-loan/atomic-tx reachability — confirmed genuinely stubbed/broken
      in live mode 2026-08-19, matching a parallel agent's independent finding.**
      `engine/handlers/flash_loan_handler.py`'s live-mode docstring says steps are "encoded, not executed
      separately" via `AtomicBundleExecutor`, but `algorithms/atomic_bundle_executor.py::execute_bundle` has **zero
      callers anywhere in execution-service** outside its own file and an `__init__.py` re-export — it is never
      actually invoked, and even its own `execute_bundle` loops sequential single-instruction calls rather than
      building one atomic on-chain tx despite the docstring's claim. `algo_library/multicall_batcher.py::
      MulticallBatcher` does real Multicall3 grouping/encoding and IS used by `intent_engine.py`, but neither file
      contains a `send_transaction`/broadcast call — encoding-only, no wired submission path. Cross-reference:
      `/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` (2 open / 18 done)
      already names `_submit_flash_loan` staying a stub as a sub-finding — this todo is the flash-loan/atomic-bundle
      half of that doc's broader read/execute-asymmetry finding, don't duplicate its tracking. A parallel agent has
      also documented this in codex/ this session (`AtomicBundleExecutor` orphaned-from-live-dispatch note) — cite,
      don't re-derive the codex-side writeup. Done-when: either the live submission path is wired end-to-end with a
      real testnet tx, or `AtomicBundleExecutor`/`flash_loan_handler` are explicitly marked not-production-ready
      with a tracked follow-up.
- [ ] [BACKEND] P1. **CoW Swap — genuinely greenfield, confirmed 2026-08-19** (zero code anywhere in the repo beyond
      3 unrelated design-comment mentions of "CowSwap" as inspiration for `intent_engine.py`/`solver_auction.py`).
      Build a CoW Swap execution adapter from scratch: order-signing (CoW Protocol off-chain order + on-chain
      settlement), quote fetching, order submission to the CoW API, fill tracking. Follow the existing DEX-adapter
      shape (`defi_execution/protocols/uniswap.py` + `uniswap_live.py` as the closest analog — swap-only, no limit
      orders, per the instruction/order-type registry finding below).
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
- [ ] [OPERATOR] P3. BLOCKED-OPERATOR-DECISION — **Solana spot+perp basis trade bridged to Ethereum, venue names
      TBD.** Genuinely greenfield at the PM-doc level (no existing doc covers this exact "Solana basis bridged to
      Ethereum" shape — the nearest existing plan,
      `/plans/active/solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md`, is SOL-native LST carry via
      Jupiter perps + Kamino borrow, not a cross-chain bridge structure). Bridge architecture itself is owned by a
      separate, parallel agent working only in `codex/` (already landed several dated 2026-08-19 codex commits on
      EVM/Solana bridge architecture — see `/codex/04-architecture/transfer-coordinator.md` and its neighbors) — do
      not duplicate that work here; this todo is a placeholder pending the operator naming the actual Solana
      venue(s) to use.
- [ ] [OPERATOR] P1. **Manual-live vs automated-live execution mode — cross-cutting requirement, not
      Betfair-specific.** Operator (2026-08-19), exact words: "the whole strategy service and execution need to
      understand that there's a manual Live mode where everything is our own manual execution, and there's an
      automated Live mode." Applies to EVERY venue in this epic's priority set, not just Betfair. **What already
      exists** (2026-08-19 audit): UAC's `OperationalMode` enum already has a `MANUAL` value, consumed in
      `execution_service/cli/handlers/__init__.py` (`OperationalMode.MANUAL` resolves to
      `LiveExecutionHandler(mode=mode)`, differing from `LIVE` only in instruction source — HTTP manual API vs
      automated strategy signals, not a fully separate engine) and wired through `manual_instruction_api.py`/
      `manual_instruction_helpers.py`. This is real infra to build on, not a from-scratch build. **What's missing**:
      `MANUAL` today is one flat value alongside `LIVE`/`PAPER`/`BACKTEST` — there is no "LIVE, with a
      manual-vs-automated sub-axis" concept. Companion strategy-service-side gap tracked in `strategy_master.md`'s
      matching todo (cross-reference, this is the execution-service half). `[OPERATOR]`: the exact modeling decision
      (a new sub-enum on `OperationalMode`? a field on the execution instruction? per-archetype config?) is a design
      call, not mechanically derivable — resolve it first; the wiring itself (updating `LiveExecutionHandler`
      dispatch, the manual-instruction API, per-venue adapter selection) is `[BACKEND]`-eligible follow-up once
      scoped.
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
