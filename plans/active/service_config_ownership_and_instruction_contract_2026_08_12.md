---
doc_type: plan
title: >-
  Service config ownership — the instruction contract, per-service config.py, and hot reload everywhere
summary: >-
  Establishes the target the operator set 2026-08-12: the strategy↔execution contract is the INSTRUCTION (trade / swap /
  back-lay / atomic) plus a strategy-sent reference price, execution-service owns algo selection entirely via its own
  per-client config, and each service centralises schema + defaults in its own config.py with the instance in GCS and
  everything hot-reloadable including API keys. The audit behind this plan found the target much closer than expected —
  and blocked in three specific places. Already right: `StrategyInstructionEnvelope` carries `execution_policy_ref`,
  `urgency`, `eligible_venues` and `venue_constraints`, so strategy already opts into execution behaviour BY REFERENCE;
  `execution_policies.py` is already a content-hashed, versioned, first-match-wins algo rule-table gated on instruction
  action; `select_algorithm()` already accepts a config-supplied algo and validates it per instruction type;
  execution-service already hot-reloads instruments, CLIENTS and rate-limits, plus API keys. The three blockers: (1) the
  execution-policy registry has ZERO consumers, no client/slot keying, no GCS loader and no hot reload; (2)
  `reference_price` exists only on `QuoteInstruction`, so the benchmark-fill assumption that makes strategy-only
  backtests possible has no field to travel on for trade/swap; (3) strategy-service does not wire `ClientDomainConfig`
  at all, which is exactly why API keys hot-reload while a client leverage change needs a restart.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, execution-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [config, hot-reload, execution-policy, instruction-contract, per-client-isolation, backtest, service-boundary]
related:
  [
    /plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md,
    /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md,
    /codex/04-architecture/execution-policy.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 5
assigned_role:
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-12, operator statement of target architecture: "exec_algo configuration lives in execution
  service. the contract between strategy and execution is the instructions (trade, swap, back/lay, atomic etc). and
  strategy sends the ref price, execution layer marks underlying against either statically or updates as ul moves.
  execution also strategy client config tells it which algos to use for each strategy instruction type etc. so no
  execution direct config is handled by strategy at all really or shouldn't be, hence we can do strategy backtests using
  just strategy service and the upstream data from data pipeline given the benchmark fill assumption it makes." Plus:
  "hot reload for execution config same as strategy config including api keys and all other params centralised to each
  service in their config.py should be the goal."
---

# Service config ownership — instruction contract, per-service `config.py`, hot reload everywhere

> **Read the audit first (§ A).** The headline is that the ARCHITECTURE is already right and mostly built; what is
> missing is wiring, in three specific places. Do not redesign what § A marks ✅.

## Codex SSOTs

`/codex/04-architecture/execution-policy.md` (the algo rule-table contract) ·
`/codex/06-coding-standards/config-reloader-pattern.md` (typed config reloaders) ·
`/codex/04-architecture/tier-and-import-architecture.md` (no service↔service deps) ·
`/codex/09-strategy/operational/paper-batch-live-reconciliation.md` (the ε=0 spine the ref price feeds)

## § A. Audit 2026-08-12 — how close the reality is to the target

### Already correct (do NOT rebuild)

| Target property                                                | Reality                                                                                                                                                                                                                                                                                                      |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Contract is the instruction, and strategy opts in BY REFERENCE | `StrategyInstructionEnvelope` carries `execution_policy_ref` — a reference, never the policy body. It also already carries `urgency`, `deadline_utc`, `eligible_venues`, `venue_constraints`, `venue_routing_mode`, `target_venue`, `chain`                                                                  |
| Execution owns algo selection, keyed by instruction type       | `execution_service/v2/execution_policies.py`: immutable **content-hashed, versioned** artifacts; `AppliesTo` gates on `actions` (InstructionActionV2) / `urgency` / `venue_categories` / `instrument_types`; `PolicyRule.when → then_algo + then_params`; document-order, first-match-wins, **default-deny** |
| Algo validity is per instruction type                          | `select_algorithm(instruction_type, …, config_algorithm)` already validates a config-supplied algo against UAC `ALGOS_BY_INSTRUCTION_TYPE` (8 types, different valid sets — `TRADE` 8, `ZERO_ALPHA` 1)                                                                                                       |
| Execution config hot-reloads                                   | execution-service runs **three** `DomainConfigReloader`s — instruments, **clients**, rate-limits — plus `ApiKeyReloader` (Hyperliquid) and a separate `_BybitKeyReloader`                                                                                                                                    |
| A per-client hot-reloadable substrate exists                   | UTL `ClientDomainConfig`: `active_clients` + `client_configs: dict[client_id, dict[…]]`, reloading via the `config-domain-clients` domain                                                                                                                                                                    |

### The three blockers

- **B1 — the execution-policy registry has no consumers.** `ExecutionPolicyArtifact` / `PolicyRule` appear only in
  `v2/__init__.py` re-export plumbing. No `client_id` or `slot_label` keying, no GCS loader, no hot reload; `register()`
  is in-memory. So the correct artifact exists and nothing evaluates it.
- **B2 — `reference_price` exists only on `QuoteInstruction`.** `TradeInstruction` carries `max_price`, which is a
  BOUND, not a benchmark. So "strategy sends the ref price, execution marks the underlying against it" has **no field to
  travel on** for trade/swap — and the benchmark-fill assumption that makes strategy-only backtests possible therefore
  cannot be expressed on the contract.
- **B3 — strategy-service does not wire `ClientDomainConfig`.** It runs reloaders for `StrategyDomainConfig` and
  `InstrumentDomainConfig` only. **This is the precise reason API keys hot-reload while a client leverage change is a
  restart** — the substrate is in UTL and already used next door, just not subscribed to here.

### The systemic pattern worth naming

B1 is the **third** instance found in one session of the same shape: a well-formed contract built ahead of its loader —
`WalletMappingConfig` (zero consumers), `ClientsYaml` (zero consumers), `ExecutionPolicyArtifact` (zero consumers). The
shapes being right is genuinely good news; the risk is that "declared" keeps reading as "done". Every todo below that
wires one of these must also delete or update whatever doc claims it is already live.

### Corrected in flight

- [x] [AGENT] P0. ✅ **Removed the execution section from strategy-service's param schema —
      `strategy-service@4762c211ab`, gate green (exit measured via redirect).** An earlier commit the same day
      (`664f5b42b2`) had added `exec_algo` / `exec_urgency` / `exec_max_participation_pct` / `exec_max_slippage_bps`
      there. That was wrong on the operator's correction: it created a **second source of truth** for the
      execution-policy artifact, and `urgency` was already a first-class envelope field, so the param was redundant as
      well as misplaced. Replaced with a `reference_price` section, which strategy genuinely DOES own —
      `refprice_mark_mode` (`STATIC_AT_SEND` | `UPDATE_AS_UNDERLYING_MOVES`, both operator-named modes),
      `refprice_source`, `refprice_max_drift_bps`. A regression test now fails if anyone re-adds execution config to
      strategy-service.

## § B. Make the execution-policy registry real (unblocks B1)

- [ ] [AGENT] P0. **Key execution policies by `(client_id, slot_label)`** so "execution's strategy-client config tells
      it which algos to use per instruction type" is expressible. Reuse the pair the event tag already carries; do not
      invent a third identity.
- [ ] [AGENT] P0. **Give the registry a GCS loader + `DomainConfigReloader` subscription**, so a policy change is
      dynamic rather than a deploy. Follow execution-service's existing three-reloader pattern rather than a new
      mechanism.
- [ ] [AGENT] P0. **Wire policy evaluation into the live execution path** and have `select_algorithm()` take its
      `config_algorithm` from the resolved policy. The parameter already exists and already validates per instruction
      type, so this is connection, not design.
- [ ] [AGENT] P1. **Reject an unknown `execution_policy_ref` loudly.** Default-deny is already the rule-evaluation
      semantic; make an unresolvable REF equally loud rather than silently falling back to a default algo, which would
      hide a misconfigured client.

## § C. Put the reference price on the contract (unblocks B2, and the backtest property)

- [ ] [AGENT] P0. **Add the reference price to the shared instruction envelope**, not just `QuoteInstruction` — with the
      mark mode (static at send vs updating as the underlying moves) so execution knows which to apply. This is the
      field the `refprice_*` params shipped in `4762c211ab` configure, and they are inert until it exists.
- [x] [AGENT] P0. ✅ **The benchmark-fill assumption IS already written and shared — no new contract needed.**
      `/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md` is the contract,
      `/codex/04-architecture/backtest-groups.md` § "Group B" is the isolation model, and both services implement it
      (`benchmark_fills.py` Group B / `BenchmarkMatcher` Group C). An earlier draft of this plan claimed it was "an
      assumption with no written contract" — that was wrong, found while auditing execution-service. The gap is
      duplicate implementation (§ G3), not a missing definition.
- [ ] [AGENT] P1. **Prove the standalone-backtest property with a test**, not an argument: run a Group-B backtest using
      only strategy-service + pipeline data, asserting no execution-service import and no execution config read. The
      architecture already intends this — `benchmark_fills.py` says Group B "replaces execution entirely" — but nothing
      _enforces_ it, so a future import would silently break the property. That test is the guard on the whole service
      boundary.
- [ ] [AGENT] P1. **Reconcile the ref price with the ε=0 spine.** `UPDATE_AS_UNDERLYING_MOVES` means the benchmark is
      time-varying, so a batch rerun must re-derive the same series — pin it to the same tick source and add it to the
      `paper(W) == batch-rerun(W)` assertion rather than assuming it reproduces.

## § D. Per-service config centralisation + hot reload (unblocks B3)

- [ ] [AGENT] P0. **Subscribe strategy-service to `ClientDomainConfig`.** The single highest-value item in this plan: it
      is what turns a client leverage change from a restart into a hot reload, and the substrate already exists in UTL
      and is already used by execution-service. Pair it with the param-change callback and versioned-event discipline in
      [per-client config keying](/plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md) §
      "Dynamic param updates" — a silent swap breaks the ε=0 proof.
- [ ] [AGENT] P1. **Give `client_configs` a typed schema.** It is `dict[str, dict[str, DomainConfigValue]]` — the
      transport, keying and reload are right, but the payload is an untyped bag, so nothing validates a client's
      leverage is a number in range. Type it against the governing schema so the wizard and the reloader agree.
- [ ] [AGENT] P1. **Resolve execution-service's missing `config.py`.** The operator's goal is schema + defaults in each
      service's `config.py`; execution-service has **no such file** — its typed config is
      `service_config.py::ExecutionServicesConfig(UnifiedCloudConfig)`. Decide rename-vs-document and apply it
      consistently across services, so "look in config.py" is true everywhere or nowhere.
- [ ] [AGENT] P1. **Close the Bybit API-key reload asymmetry.** Hyperliquid reloads via the shared `ApiKeyReloader`;
      Bybit needs a bespoke `_BybitKeyReloader` because UAC's `DATA_SOURCE_TO_SECRET` registry cannot express it. Fix
      the registry so one mechanism serves both — two reloaders for the same job is how one of them silently stops being
      maintained.
- [ ] [AGENT] P2. **Inventory every remaining `config.py`-shaped knob per service** and state, per knob, whether it is
      hot-reloadable. The goal is "everything centralised and hot-reloadable"; without the inventory there is no way to
      say how far along that is, and partial coverage reads as full coverage.

## § G. Execution-service change surface — measured 2026-08-12, exhaustive

> Operator asked to be "fully sure even for the execution service stuff what the changes needed are". This section is
> that answer. **The headline: the benchmark-fill architecture — the load-bearing piece — is already built, and only
> three things are genuinely missing.**

### Already built, and better than expected

| Capability                          | What exists                                                                                                                                                                                                                                                                                                                              |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **The benchmark fill itself**       | `BenchmarkMatcher` with `BookType.ALPHA_ZERO`, **always-fill** — the benchmark-fill assumption is implemented, not assumed                                                                                                                                                                                                               |
| **The two-layer attribution split** | `pnl_attribution/rows.py` builds rows from a PAIR of (benchmark, live) `MatchResult`s: **STRATEGY layer** = benchmark-fill decomposition at benchmark price (delta/funding/basis/carry/financing/greeks/settlement/fx); **EXECUTION layer** = `live_fill − benchmark_fill` residual → `SLIPPAGE` + `FEES` (surprise = actual − modelled) |
| **Slippage**                        | Computed, correctly signed and layered: `slippage = sign * (benchmark.fill_price - live.fill_price) * filled_quantity`, emitted as `PnLFactor.SLIPPAGE` / `PnLLayer.EXECUTION`                                                                                                                                                           |
| **Alpha, with statistical rigour**  | `benchmark/metrics.py` (328 lines): `StatisticalMetrics` (mean, std, standard error, 95% CI, `ci_width`, `is_reliable`) and `PathAwareMetrics` (`early_alpha_bps` / `mid_alpha_bps` / `late_alpha_bps` + `cumulative_alpha_curve`)                                                                                                       |
| Surrounding benchmark tooling       | `comparison.py`, `enhanced_comparison.py`, `ranking.py`, `regimes.py`, `storage.py`, `html_report.py`                                                                                                                                                                                                                                    |

**Why this matters more than any other finding in the plan**: the STRATEGY-layer / EXECUTION-layer split is _exactly_
why a strategy-only backtest is legitimate. The strategy-attributable PnL is computable at benchmark price with no
execution involvement; everything execution adds or destroys is the residual. That is the property the service boundary
exists to protect, and it is already implemented rather than aspirational.

### The three real gaps

- [ ] [AGENT] P0. **G1 — feed `config_algorithm`; nothing supplies it.** The hook is threaded through THREE levels —
      `selector.select_algorithm(instruction_type, requested_algorithm, config_algorithm)`, the
      `HandlerRegistry.select_algorithm()` wrapper that forwards it, and validation against `ALGOS_BY_INSTRUCTION_TYPE`
      — and **zero call sites supply it** (the only `requested="TWAP"` is a docstring example, not live code). So the
      change is: resolve the per-`(client_id, slot_label)` policy, pass its `then_algo` as `config_algorithm`. **No new
      plumbing** — the parameter, the validation and the fallback chain already exist.
- [ ] [AGENT] P0. **G2 — add instruction-level `received_at` / `sent_at`; latency is the ONLY missing analytic.** Alpha
      and slippage are built; latency has nothing to compute from. The timestamps that exist are unrelated —
      `received_at_mark_price_eth` (restaking rewards), `token.received_at_utc` (dust quote sources), `submitted_at` (an
      order-adapter idempotency cache). **There is no instruction-level received/sent pair in either service.** Both
      sides need it, per the operator, so define it once in UAC on the envelope and the fill record rather than twice.
- [ ] [AGENT] P0. **G3 — collapse the benchmark's TWO independent implementations into one sent value.** _Corrected from
      an earlier draft of this plan that framed this as two competing benchmarks — it is not._ There is **one**
      benchmark-fills contract bridging the backtest groups
      ([backtest-groups](/codex/04-architecture/backtest-groups.md): Group B uses benchmark fills, Group C measures
      execution alpha "against the same benchmark"), and **the standalone-backtest property is already built**:
      `strategy_service/engine/backtest/benchmark_fills.py` is a pure, bit-identical, 653-line Group-B implementation
      whose own docstring states it lives in strategy-service "because Group B replaces execution entirely". The real
      risk is therefore not disagreement-by-design but **drift between two implementations of one definition** — 653
      lines here, `BenchmarkMatcher` there. **Second correction, 2026-08-12 (operator question "why not just make it a
      no-op in execution-service"):** the duplication is narrower than the paragraph above assumed, and the operator's
      instinct is right. `BenchmarkMatcher` is ONE of five matchers (`L0`/`L1`/`L2`/`AMM`/`Benchmark`), scoped to
      **ALPHA_ZERO protocol ops — LEND/STAKE/BORROW**, and its benchmark-price mode is already "instant fill at a
      **strategy-supplied** benchmark price, `price_impact_bps = 0`, because the matcher assumes the strategy already
      absorbed any external impact accounting upstream" — i.e. **on the trade path it already consumes rather than
      re-derives.** So sending the reference formalises the legacy mode's existing assumption; it does not displace a
      rival calculation, and there is no independent trade-side benchmark engine to delete. **Recommendation:
      strategy-sent is authoritative and the trade path becomes an explicit pass-through.**
- [ ] [AGENT] P0. **G3a — do NOT no-op the lending path.** The same matcher's Phase-3B lending mode routes through
      `LendingRateImpactCalculator` (`matching_engine/lending/rate_impact.py`) so backtest yield uses the **POST-trade**
      rate: `fill_price` becomes post-trade APY and `price_impact_bps` the signed rate delta (negative for SUPPLY/REPAY
      as utilisation drops, positive for BORROW/WITHDRAW). **strategy-service cannot compute this** — it is a function
      of pool state and your own size — and using the pre-trade rate would silently **overstate lending and borrow
      yields** on every recursive-carry and yield archetype. This matcher is not simulating a venue; it is modelling
      own-size market impact on a real pool. Add a test asserting the lending path stays live if the trade path is
      collapsed, so a future "make the benchmark matcher a pass-through" change cannot take the rate impact with it.

### Smaller execution-service items

- [ ] [AGENT] P1. **Unify the algo vocabulary — there are two.** `engine/instruction_convert.py` does
      `algorithm = (algo or "MARKET").upper()`, and **`"MARKET"` does not exist in UAC `EXECUTION_ALGOS`** at all; it
      also re-implements TWAP slicing params inline. That is a second naming system on the manual-instruction path,
      invisible to the selector's validation. Either register the manual path's names in UAC or route it through the
      selector.
- [ ] [AGENT] P1. **Wire the execution-policy evaluator** (see § B) — `ExecutionPolicyArtifact` / `PolicyRule` appear
      only in `v2/__init__.py` re-export plumbing, so the rule evaluator that already implements first-match-wins /
      default-deny is never called.
- [ ] [AGENT] P2. **Confirm the benchmark module's own consumers.** `metrics.py` is imported only by its siblings
      (`enhanced_comparison.py`, `ranking.py`) — verify the chain reaches a live/reporting caller rather than
      terminating in the benchmark package, so the alpha metrics are actually surfaced somewhere.

## § H. Where transfers route — answered 2026-08-12, and the split is already correct

Operator question: _"what do transfer instructions route to — exec service or strategy service?"_ **Both, and the
division is the same intent-vs-method split as trades — no change needed.**

| Stage                        | Service           | What it does                                                                                                                                                                                                                                                                                                                                                                   |
| ---------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Emit** (decide + net)      | strategy-service  | `IntraClientRebalanceCoordinator` (`transfer_coordinator.py`) nets N strategies' requests for ONE client into the **minimum set of intents** — one per `client × {unordered venue pair} × asset × transfer_type` — summing signed amounts, dropping flows that cancel to zero, collapsing bidirectional flows to a single net direction. Emits canonical UAC `TransferIntent`. |
| **Consume** (move + confirm) | execution-service | `execution_service.transfer_coordinator.TransferCoordinator` plus `engine/transfers/` — `live_custody_adapter.py` (the custody rail) and `confirmation_poller.py` (settlement confirmation)                                                                                                                                                                                    |

### I/O, adaptor and routing are ENTIRELY execution-service (verified 2026-08-12)

Operator asked to confirm rather than assume. Measured: **strategy-service has zero transfer I/O** — no
`withdraw`/`custody`/`rpc`/`web3`/`send_transaction`/`bridge` anywhere in `transfer_coordinator.py` or
`rebalance_emit_pipeline.py`, and `transfer_coordinator.py` is its only transfer-related module. The whole rail lives in
`execution-service/execution_service/engine/transfers/`:

| Piece                      | What it does                                                                                                                                                                                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `adapter.py`               | The `TransferAdapter` Protocol — `execute_internal_transfer`, `execute_withdrawal`, `execute_onchain_transfer`, `get_transfer_status`, `get_balance` (all async), each taking an optional `FundTransferContext` for fund/share-class routing                                   |
| `factory.py`               | Adapter selection **by `OperationalMode`**: BACKTEST/PAPER → `MockTransferAdapter` (instant, no credentials); LIVE/MANUAL → `CompositeTransferAdapter`. Its docstring states the discipline explicitly: _"Same code path for batch and live — adapter injection, not if/else"_ |
| `CompositeTransferAdapter` | **The rail router**: CeFi operations (internal transfers, withdrawals, CeFi balance) → CCXT adapter; on-chain operations (custody transfers, on-chain balance) → custody adapter; status polling tries CCXT first, then custody                                                |
| `live_ccxt_adapter.py`     | The CeFi rail                                                                                                                                                                                                                                                                  |
| `live_custody_adapter.py`  | The on-chain / custody rail, resolving through `custody/factory.py::get_custody_provider` (Copper / CEFFU)                                                                                                                                                                     |
| `confirmation_poller.py`   | Settlement confirmation                                                                                                                                                                                                                                                        |

**Note for the § J6 enum union**: the live router branches on **CeFi-vs-on-chain**, not on any `TransferType` member. So
the unioned enum must map cleanly onto those two rails (plus custody), or the classification and the routing will
disagree — worth settling as part of the union rather than after it.

**Why netting must sit strategy-side**: it requires seeing every strategy for one client at once, which is exactly the
view execution-service does not have. Execution receives an already-minimal set of intents rather than N overlapping
ones — the same reason strategy owns the reference price and not the algo.

**The cross-client guard is enforced at BOTH layers deliberately** — `CrossClientTransferForbiddenError` is raised at
strategy-side emit AND at execution-side consume
([client-funds-isolation](/codex/04-architecture/client-funds-isolation.md)). That is defence in depth on the one rule
with no acceptable failure mode, not redundancy to remove.

- [x] [AGENT] P2. ✅ **VERIFIED 2026-08-12 — and the answer is worse than the hypothesis. NOT WIRED, and nothing emits
      `TransferIntent` at all.** The todo asked whether transfers reach execution un-netted. They do not reach execution
      **at any level**: a workspace-wide search for production `TransferIntent(` construction returns **zero hits**
      outside the UAC class definition. `execution_service/transfer_coordinator.py`
      `TransferCoordinator.execute(intent)` is a real consume-time entry point **with no live producer feeding it**.
      **Three independent breaks, each fatal on its own:** (a) `enable_transfer_rebalancing` (`config.py:455`, default
      `False`) is never set True outside tests — `colocated_engine.py:94-98` builds the worker target without ever
      passing or reading it, so it always falls through to the `False` default at `client_worker.py:283`. (b) **Zero
      non-test `TransferRequest(` construction sites.** The coordinator's own docstring example calls
      `strat.compute_rebalance_transfers()` — **that method does not exist anywhere in the codebase**; the only hit is
      the docstring itself. (c) **Nothing sends `REBALANCE_PERIOD_TICK`.** The only producer-side `pipe.send` in
      strategy-service is `CREDENTIAL_ROTATED` (`client_admission_controller.py:215`), so
      `_handle_rebalance_period_tick` (`client_worker.py:214`) never fires in production even if (a) and (b) were fixed.
      The wrapper chain itself is genuine production code — `RebalanceEmitPipeline`
      (`rebalance_emit_pipeline.py:73,76,99`) is instantiated in `client_worker.py:117` and carried on
      `ClientContext.rebalance_pipeline` — which is exactly why reading the module tree suggested it worked.
- [ ] [OPERATOR] P0. **Transfers do not execute in production — decide the path to live before funds move.** This is a
      capability gap, not a bug in one function: the emit side has three disconnected breaks and the consume side has no
      producer. Everything downstream of it — sweeps, intra-client rebalancing, the `sweep_threshold_usd` /
      `min_eth_reserve` config fields (`config.py:461-470`, also unconsumed) — is inert. **Material for live trading**:
      any strategy assuming its collateral can be moved between venues is assuming a path that does not run today.
- [ ] [AGENT] P1. **Correct a false "done" claim in the archive.**
      `/plans/archive/defi_transfers_and_gas_fees_2026_03_27.plan.md:237` records as DONE (2026-03-27) that a
      `PortfolioRebalancer` at `strategy_service/engine/rebalancing/` was extended to emit TRANSFER instructions —
      **neither that directory nor that class exists in the current tree.** An archived plan asserting a shipped
      capability that was never shipped is the most expensive kind of stale doc, because archival implies it was
      verified. Add a correction banner rather than editing the history silently.

## § I. Candle-based fills — the tier already exists; the sub-candle idea has a real niche

Operator question: _"do we have a matcher for OHLCV? … the OHLCV fill in execution service would be smarter using the
smaller candles where they exist … VWAP of those smaller candles adjusted for our max % of each candle we think we can
fill at. Is that what an L0 fill is, or is that just trades?"_

**L0 is not it.** `L0_TOB` is top-of-book only — scraped bookmakers and odds aggregators, best bid/offer with sizes,
**fill-or-reject with no partial fills**. Neither trades nor candles.

**The concern is exactly tier 1, and tier 2 is the already-built fix.** `ExecutionFidelityTier` has three rungs, rank-
clamped in `utils/fidelity_selector.py`:

| Tier               | Rank | BookType           | Fill basis                                                |
| ------------------ | ---- | ------------------ | --------------------------------------------------------- |
| `OHLC_BAR`         | 1    | `L1_MBP`           | bar fill — the naive tier the operator is wary of         |
| `CANDLE_BOOK_COLS` | 2    | `CANDLE_BOOK_COLS` | **precomputed intra-bar book summary — walks real depth** |
| `L2_TICK`          | 3    | `L2_MBP`           | full L2 walk via NautilusTrader                           |

`CandleBookColsMatcher` (`matching_engine/candle_book_cols.py`) consumes Plan-1 book-summary columns on the processed
candle — `book_spread_bps_tw_mean` for fill price, `book_mid_close` for the reference, and per-level
`book_{bid,ask}_qty_L{1..5}_tw_mean` for liquidity. It computes `best_ask = mid_close + half_spread`,
`total_depth = Σ ask_qty_L1..L5`, and prices a fill as `best ± (quantity / total_depth) × half_spread` on the adverse
side — linear impact in `quantity/total_depth`, justified as the closed-form expectation of walking uniformly
distributed depth at the average level price. **It rejects on zero depth rather than assuming unlimited fill**, which is
precisely the failure mode the operator named. It is a pure function, explicitly so the ε=0 spine survives a promotion
from `OHLC_BAR` to `CANDLE_BOOK_COLS`.

**So it walks DEPTH, not traded volume** — a strictly better basis than a share-of-volume cap, because depth is what an
order actually fills against.

### Where the operator's sub-candle idea is still the right answer

- [ ] [AGENT] P0. **DECIDED 2026-08-12 — build the sub-candle rung as a graded fallback, not a binary.** Operator:
      _"some things won't have that as they never had tick data, so needs to handle both cases … it's making smarter
      fallbacks, and only if no more granular candles to do the fallback then another fallback to the more basic version
      is fine."_ The ladder becomes **book-columns → sub-candle VWAP → OHLC bar**, each rung used only when the one
      above has no data. `CandleBookColsMatcher` needs `BOOK_SUMMARY_COLUMNS` precomputed on the candle, and cells that
      never had tick data can never have them — today those drop straight to the naive tier, which is the gap. Nothing
      sub-candle exists anywhere in `matching_engine/`. **The insertion is architecturally clean**:
      `execution_fidelity(asset_group, venue, instrument_type, mode)` resolves the data-supported tier **declaratively
      from the cell's MVP data_types in `MVP_SCOPE`** — not by probing storage — so "has 1m candles, lacks book columns"
      is expressible as a decision-table rule. `clamp_tier()` already only ever clamps DOWN, so a new rung cannot
      silently upgrade anything. **Two cautions for the implementer.** (1) `_TIER_RANK` is integer-ranked
      `OHLC_BAR: 1 / CANDLE_BOOK_COLS: 2 /     L2_TICK: 3`; inserting between 1 and 2 means renumbering, which touches
      every clamp comparison and any persisted tier value — prefer widening the scale over shifting existing numbers.
      (2) Preserve the existing fail-loud guard: a cell not in `MVP_SCOPE` raises rather than degrading, because
      "execution must never silently fall back to OHLC for a venue/instrument_type that is not even in the capture
      universe" — the new rung must not become a soft landing for cells that should still raise.
- [ ] [AGENT] P1. **Measure the population the new rung serves** — cells with finer candles but no book-summary columns
      — so the build is sized against real coverage rather than assumed need. This informs, but no longer gates, the
      work above.
- [ ] [AGENT] P1. **If it is built, carry PB.8's correction — a share of candle VOLUME over-counts fillable volume.**
      `e2e-testing/scripts/paper_trading/_aggtrades_fidelity.py` (PB.8) already measured this against real Binance
      aggTrades: a resting maker only fills against trades that hit its level **on the filling side** (for a resting BUY
      at L: aggressive SELLS at price ≤ L, `isBuyerMaker=True`), while total candle volume includes the other side and
      trades away from L. So a flat "25% of the candle" participation cap is optimistic by a measurable ratio. The
      sibling `_fill_backtest.py` (PB.7) already prototypes the participation model itself — 15m bars, `PART = 0.25`,
      three policies (`full` / `single_shot` / `requote`) — and quantifies the liquidity drag versus the full-fill
      ideal. **Both are `Lifecycle: campaign` scripts whose delete-when condition is "the fill-model decision is made
      and the winner shipped"** — so the decision above is the thing actually blocking their retirement.

- [ ] [AGENT] P1. **Update `/codex/04-architecture/execution-policy.md`** to state the `(client_id, slot_label)` keying
      and the loader/reload story once § B lands — and to say plainly that the registry was declared-but-unwired until
      then, so the doc stops implying a live mechanism.
- [ ] [AGENT] P1. **Write the service-boundary contract into codex**: instruction + reference price is the whole
      surface; execution config never crosses; the standalone-backtest property is the test of it. No codex doc
      currently states this in one place, which is why it took a code audit to answer.
- [ ] [AGENT] P2. **Reconcile `/codex/06-coding-standards/config-reloader-pattern.md`** against the measured reality —
      three reloaders in execution-service, two in strategy-service, and the per-service `config.py` inconsistency.

## § J. Dual-path register — operator directive 2026-08-12: one SSOT per consumed thing

> _"make sure codex and code has SSOT for things — no dual paths for same data consumption"_. This register exists
> because **three of my own wrong statements this session were symptoms of dual paths**: I could not tell which of two
> surfaces was authoritative because both existed and neither said it wasn't. Each row is a defect, not a design.

| #   | Consumed thing          | SSOT                                                    | Dual path (the problem)                                                                          | Measured consequence                                                                                           |
| --- | ----------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| J1  | **`book_type`**         | UAC `BookType` StrEnum — SIX members                    | `execution_service/cli/domain_runners.py:36` — a **shadow class**, TWO members, own `validate()` | **Rejects `CANDLE_BOOK_COLS`, `AMM`, `ALPHA_ZERO`, `L0_TOB`** — this CLI path cannot select the candle matcher |
| J2  | Strategy slot catalogue | `target_universe/catalog_*.py`                          | `archetype_slots_defi.py`                                                                        | The two disagree on whether SOL staked basis is runnable                                                       |
| J3  | Benchmark fill          | benchmark-fills contract                                | implemented twice: `benchmark_fills.py` (Group B) + execution matchers (Group C)                 | One definition, two implementations, free to drift — § G3                                                      |
| J4  | Execution algo names    | UAC `EXECUTION_ALGOS`                                   | `engine/instruction_convert.py` `"MARKET"`                                                       | A name the selector's validation has never heard of                                                            |
| J5  | Strategy config loading | `engine/core/config_loader.py::ConfigLoader` (GCS/JSON) | `config.py::load_strategy_config` (local YAML) **plus a third** in `strategy_config_loader.py`   | **Two functions share the name `load_strategy_config`** with different substrates                              |
| J6  | Transfer types          | `BusTransferType` (5) — the most load-bearing           | exec-svc `transfer_types` (5), `architecture_v2.enums` (7), `domain.defi.transfers` (6)          | **20 distinct values, 18 of them in exactly ONE enum** — the union IS the capability surface                   |

### J6 measured in full (2026-08-12) — and why this one is a BUILD, not a delete

Four enums, **20 distinct values, and only two shared by more than one enum** (`BRIDGE` across three, `CEX_WITHDRAWAL`
across two). Every one of the four carries unique members: A 3, B 6, C 4, D 5. **So no existing enum can be adopted
as-is without losing capability** — this is the union-and-complete case from the rule above, not a delete.

**Which is the real SSOT**: `BusTransferType` (`canonical.crosscutting.transfer_events`) — the only one re-exported at
UAC top level, and the one routing BOTH services' `TransferCoordinator`. The plan previously named the exec-service
`transfer_types.TransferType` as the routing SSOT; measurement says otherwise (that one is deep-path only, never
re-exported, and one of its two importers carries a `# noqa: qg-deep-import`).

**Aliases to merge** (same concept, different spelling — each pair currently fails equality): `CEX_WITHDRAW` /
`CEX_WITHDRAWAL` · `ON_CHAIN` / `ON_CHAIN_TRANSFER` / `SAME_CHAIN` · `CEX_INTERNAL` / `INTERNAL_SUBACCOUNT` /
`SUBACCOUNT_MOVE` · `BRIDGE` / `CROSS_CHAIN`. The `transfer_events.py` docstring **already flags the
`CEX_WITHDRAW`/`CEX_WITHDRAWAL` pair as a known gap** and the fix was never made.

**Unfinished capability the union preserves** — the members that exist in exactly one enum are stated intents, not dead
code: `WRAP_UNWRAP`, `UNITY_WALLET_OP`, `IBKR_FUND_MOVE`, `CUSTODY_TRANSFER`, `SWEEP`, `REBALANCE`,
`DEFI_DEPOSIT`/`DEFI_WITHDRAW`. **`architecture_v2.enums.TransferType` has ZERO importers workspace-wide** — an earlier
read of this called it safe to delete; under the operator's rule it is the opposite, because its six unique members are
the clearest surviving statement of what transfers were meant to support.

- [x] [AGENT] P0. ✅ **Unioned onto `BusTransferType` — `unified-api-contracts@4663daf908`**, gate green (re-run
      independently, exit measured via redirect, not the authoring agent's reported result). **20 source values → 13
      members**: 4 alias groups merged, `CEX_WITHDRAWAL_DEPOSIT` split into `CEX_WITHDRAW` + `CEX_DEPOSIT`, and all 9
      single-enum uniques preserved verbatim per the operator's ruling — including the three from the zero-importer enum
      (`WRAP_UNWRAP`, `UNITY_WALLET_OP`, `IBKR_FUND_MOVE`), which are unfinished capability rather than dead code. **The
      rail concern is now settled in the type itself**: a `TransferRail` enum plus `BUS_TRANSFER_TYPE_RAIL` classifies
      every member, so classification and the live CeFi-vs-on-chain router cannot silently disagree. The mapping is
      **grounded, not invented** — sourced from
      [transfer-rebalance](/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md), which carries an
      explicit per-member mechanism column. Two members genuinely do not fit the CeFi/on-chain binary —
      `UNITY_WALLET_OP` (Unity API) and `IBKR_FUND_MOVE` (IBKR internal) are neither a CCXT call nor a chain transaction
      — so they map to a third `OTHER` rail rather than being forced, consistent with
      [transfer-architecture](/codex/04-architecture/transfer-architecture.md)'s standing "no manual/acknowledged
      transfer path" finding for exactly those two. Note `CEX_DEPOSIT` is ON_CHAIN (you send to the venue's deposit
      address) while `CEX_WITHDRAW` is CEFI (an exchange API call) — the asymmetry is correct and matches
      `CompositeTransferAdapter`'s split. A pre-existing test hardcoding the old 5-member closed set was updated in the
      same change; it would otherwise have failed the moment the enum legitimately grew.
- [x] [AGENT] P0. ✅ **Transfer break (a) fixed — `strategy-service@db6e38ae3a`**, gate green. `colocated_engine.py` now
      reads `enable_transfer_rebalancing` from config and forwards it to `make_worker_target`, so the flag can finally
      do something. Regression test asserts **both** `True` and `False` reach the call — asserting only `True` would
      still pass against a hard-coded value. Shipped AFTER the UAC union because quickmerge's dep gate correctly refused
      while a dependency had uncommitted changes.
- [ ] [AGENT] P0. **Break (c): add a `REBALANCE_PERIOD_TICK` producer.** Nothing sends it, so
      `_handle_rebalance_period_tick` (`client_worker.py:214`) never fires even with (a) fixed. The only producer-side
      `pipe.send` in strategy-service is `CREDENTIAL_ROTATED` (`client_admission_controller.py:215`) — that is the
      pattern to follow.
- [ ] [AGENT] P0. **Break (b): implement `compute_rebalance_transfers()` as dust-sweep + gas-reserve top-up.** Scope is
      narrower than "rebalancing" implies, and the existing config states it: `sweep_threshold_usd` (default 10.0) is
      _"USD threshold below which wallet balances are swept to the main wallet"_ and `min_eth_reserve` (0.05) is
      _"minimum ETH balance to maintain in DeFi wallets for gas"_ (`config.py:461-470`, both currently unconsumed). That
      is **threshold logic, not a judgment call**, so it is determinable. Balance source exists
      (`position/core/venue_balance_tracker.py::get_all_balances`), and `TransferRequest` already carries the right
      shape (`source_venue`→`dest_venue`, asset, amount, `transfer_type: BusTransferType`). Emit transfer types whose
      `BUS_TRANSFER_TYPE_RAIL` rail matches the rail that can actually service them. | J7 | Archetype universe |
      `StrategyArchetype` (60) | factory-registered (32), `PARAM_SCHEMA_REGISTRY` (35) | **Measured: only 13 overlap.**
      19 engines have no schema, 22 schemas have no engine, 6 have neither |

### J7 measured in full (2026-08-12, registries loaded in Python — not grepped)

The "60 / 32 / 35" framing understated this badly. The real overlap is **13**:

- **19 engines with NO param schema** — `CARRY_BASIS_DATED`, `CARRY_BASIS_DATED_INV`, `CARRY_BASIS_PERP_INV`,
  `CARRY_FUNDING_DISPERSION`, `CARRY_RECURSIVE_BORROW_LENDING_ONLY`, `EVENT_DRIVEN`, `LIQUIDATION_CAPTURE`,
  `ML_DIRECTIONAL_*` (2), `RULES_DIRECTIONAL_*` (2), `STAT_ARB_*` (2), `TSMOM_BTC_CTA`, `ARBITRAGE_*` (5). These can
  **execute** but their params bypass the validated path entirely, so a bad or missing param reaches a running strategy
  silently.
- **22 schemas with NO engine** — the entire `MARKET_MAKING_*` (5) and `VOL_*` (17) cluster. A config for these
  validates successfully and then fails at dispatch, because `get_archetype_engine_class()` raises for every one. The
  clustering says this is one unimplemented product family, not scattered rot — and it matches the vol family's dead
  catalogue keys found separately.
- **6 with neither** — `ARBITRAGE_MEV_SANDWICH`, `VOL_0DTE_PIN_RISK`, and the four `PORTFOLIO_*` members.

**Consequence for work shipped earlier today**: the four governing sections were merged into all 35
`PARAM_SCHEMA_REGISTRY` keys — so **22 of them landed on archetypes with no engine, while 19 executable archetypes got
none.** Not harmful (the rows are `wired=False`), but the merge target should be the ENGINE set, not the schema set,
once the two are reconciled.

- [ ] [AGENT] P0. **Add the gate first, then reconcile.** `factory-registered ⊆ param-schema-covered` is the invariant
      that matters (an engine with no schema is the dangerous direction); the reverse — a schema with no engine — should
      warn rather than fail while the vol/market-making family is unbuilt.

### The rule for resolving a dual path — operator ruling 2026-08-12

> _"rather than deleting code that's not fully built, better to unify it to SSOT paths where duplication exists and
> handle the union and complete the build. There's likely a reason the code build was started."_

**The test is whether the duplicate carries UNIQUE MEMBERS or is a STRICT SUBSET.**

| Shape                                                        | Action                                                                                   |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Strict subset of the SSOT, no unique members (J1 `BookType`) | **Delete and import the SSOT** — nothing is lost, and the subset was actively wrong      |
| Carries members the SSOT lacks (J6 transfer enums)           | **Union into the SSOT, then complete the build** — each unique member is a stated intent |

The second case is the common one and the easy mistake: an unused enum member is not dead weight, it is **a capability
someone scoped and did not finish**. Deleting it silently discards the design decision along with the code.

- [x] [AGENT] P0. ✅ **J1 resolved — shadow `BookType` deleted, UAC enum imported.** `execution-service@a75d953ece`,
      gate green `--no-fix` (exit measured via redirect). This one qualified for deletion under the rule above: its two
      members were a strict subset of UAC's six, so **no capability was lost**. Replaced with `validate_book_type()`
      validating against the enum itself, so it cannot drift out of date again; added a regression test asserting every
      UAC member validates, plus one naming `CANDLE_BOOK_COLS` specifically. **Severity corrected during the fix**: the
      caller catches the `ValueError` and only logs (`domain_runners.py:77-80`), so this was a **false diagnostic, not a
      hard block** — a valid `CANDLE_BOOK_COLS` or `AMM` config ran fine while being reported invalid. An earlier note
      in this plan overstated it as blocking. The test suite had also locked the defect in place by asserting
      `validate("AMM")` raises.
- [ ] [AGENT] P1. **Add a "no shadow SSOT type" gate.** J1 and J6 are one defect class: a local class/enum redefining a
      name UAC owns. A mechanical check — any class whose name matches a UAC-exported symbol and is not an import —
      catches both at commit time, and is cheaper than the audit that eventually finds J8.
- [ ] [AGENT] P1. **For every remaining row, name the SSOT in codex and mark the other path.** Where both must exist for
      a real reason (Group B / Group C in J3), **state in both places which is authoritative and why**. A dual path
      documented as intentional stops costing an auditor an hour; an undocumented one costs it every time.

## § K. e2e fill models → execution-service reproducibility (operator ask 2026-08-12)

Question: are e2e's candle-matching mechanisms reproducible inside execution-service across different candle-matching
assumptions? **Mechanisms: mostly yes. Parameterisation: no — and the missing knob is the one that matters most.**

| e2e assumption (`scripts/paper_trading/_ledgers.py`)                                                                                                                            | execution-service equivalent                                                                                                             | Reproducible?                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| Taker IOC — VWAP-walk recorded book depth, accumulate quote-notional per level                                                                                                  | `L2Matcher` (L2 walk) / `CandleBookColsMatcher` (depth walk, linear impact)                                                              | ✅ yes                        |
| Maker resting at mid ∓ `MAKER_IMPROVE_BP` (1bp), filled by trades that cross the limit                                                                                          | `TradeMatcher` passive path — `PASSIVE_ORDER_TYPES`, "simulates our order resting in the book and getting hit by" trade data, `is_maker` | ✅ mechanism exists           |
| Candle-based fill without tick data                                                                                                                                             | `CandleBookColsMatcher`                                                                                                                  | ✅ yes                        |
| **Participation cap — "a resting maker captures at most 25% of the volume that trades THROUGH its limit each 1m"**, per-strategy (`cs` 25% / `basis` 100% / `short` 25%, PB.12) | **nothing** — zero occurrences of `participation` anywhere in `matching_engine/`                                                         | ❌ **NOT expressible**        |
| Fallback ladder: book-walk fails → next-1m open + flat `TAKER_SLIP_BP`; no 1m bar → `unfilled-no1m`                                                                             | not modelled as a tiered fallback                                                                                                        | ❌ needs verification / build |
| `real_slip` guard so a genuine VWAP walk does not double-count synthetic slip                                                                                                   | no equivalent flag found                                                                                                                 | ❌                            |

- [ ] [AGENT] P0. **Add a participation cap to the passive fill path.** This is the single knob that separates e2e's
      model from execution-service's, it is per-strategy in e2e (PB.12 tuned it: high-turnover `cs` 25%, `basis` 100%),
      and PB.7 measured that ignoring it is exactly the "liquidity drag" gap versus the full-fill ideal. Without it,
      execution-service's passive fills are the optimistic model PB.7 was built to disprove.
- [ ] [AGENT] P0. **Carry PB.8's correction into the cap's definition.** The cap must apply to volume that crosses the
      limit **on the filling side** (for a resting BUY at L: aggressive SELLS at price ≤ L, `isBuyerMaker=True`), not to
      total candle volume — `_ledgers.py` already resolves the maker fill "against the REAL aggTrades flow that crossed
      our limit (true volume-at-price)", so the corrected model is already written down, not merely measured.
- [ ] [AGENT] P1. **Route the per-strategy fill assumptions through the execution-policy `then_params`** rather than a
      new config surface — this is precisely what that artifact is for, and it ties § K to § B/§ G1: the policy registry
      being unwired is _why_ per-strategy fill parameterisation has nowhere to live today.
- [ ] [AGENT] P2. **Then retire the campaign scripts.** `_fill_backtest.py` and `_aggtrades_fidelity.py` both carry
      `Lifecycle: campaign` with delete-when "the fill-model decision is made + the winner is shipped". They are the
      decision record; once the cap and its side-filter ship, they go.

## § F. Artifacts (do LAST, per operator sequencing)

- [ ] [AGENT] P2. **Update the three artifacts once § B–E land.** Operator instruction: artifacts follow plans and
      codex, never lead them. The service-boundary story is genuinely good material — the contract is narrow and the
      standalone-backtest property is a real engineering claim — but it must describe what is wired, so it cannot be
      written until § B–D are done. Artifacts: platform overview, carve-out spec, deep dive.

## Progress Log

- **2026-08-12 (execution-service deep audit)** — § G added. **The single most important finding: the target property —
  "strategy backtests using just strategy-service and the upstream data, given the benchmark fill assumption" — is
  already the documented AND implemented architecture**, as Group B. `benchmark_fills.py` (653 lines, pure,
  bit-identical) exists in strategy-service precisely because "Group B replaces execution entirely"; Group C in
  execution-service measures execution alpha against the same benchmark; `pnl_attribution/rows.py` already splits
  STRATEGY-layer from EXECUTION-layer PnL; `benchmark/metrics.py` already computes alpha with 95% CIs and early/mid/late
  path decomposition. So the answer to "how close are we" is: **the load-bearing piece is built.** **A correction I made
  to my own work mid-audit, worth keeping**: I first wrote (into this plan AND into `benchmark-fills.md`) that there
  were TWO benchmarks with two owners, reasoning that a per-algo reference is unknowable to strategy at send time. That
  was wrong, and `backtest-groups.md` says so in one line — the contract is shared and the reference is derivable from
  the instruction, which is why strategy-service can and does compute it. Both documents are corrected. The real risk is
  narrower and more useful: **one definition, two independent implementations, free to drift** — which is the actual
  argument for sending the reference price. Reaching for the doc that already covered it before writing the conclusion
  would have skipped the wrong version entirely.
- **2026-08-12** — Authored from the operator's statement of target architecture plus a same-session audit. The audit's
  most useful result was negative: **almost nothing here needs designing.** The envelope already opts in by reference,
  the policy artifact is already content-hashed and versioned with the right gating axes, the selector already validates
  per instruction type, and execution-service already hot-reloads three domains including clients. Three gaps do the
  damage, and B3 (strategy-service not subscribing to `ClientDomainConfig`) is a one-line-shaped fix behind a
  determinism requirement. Also corrected a same-day error of mine: execution params had been added to
  strategy-service's param schema hours earlier and are now removed (`strategy-service@4762c211ab`) with a regression
  guard, because they competed with the execution-policy artifact for the same responsibility.
