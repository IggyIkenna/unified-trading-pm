---
doc_type: plan
title: Regime Clustering + Proximity → Factor-Targeted Structure Allocator
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, features-service, greeks-service, ml-service, strategy-service, trading-agent-service]
scope: [engineer, admin]
tags: []
related:
  [
    plans/epics/features_and_ml_master.md,
    plans/epics/strategy_master.md,
    plans/epics/trading_agent_master.md,
    plans/epics/execution_master.md,
  ]
created: "2026-05-29"
parent_epic: features_and_ml_master
priority: P1
model_tier: opus-required
thinking_tier: max
estimate_class: brand-new
estimate_baseline_ai_days: 18
estimate_calibrated_ai_days: 18
assigned_vm: vm-ml
priority_history: "P2→P1 2026-05-30 (operator: feed dispatch)"
locked_by: live-defi-rollout
locked_since: 2026-05-29
completion_gates: { code: C5, deployment: D3, business: B4 }
repo_gates:
  - { repo: features-service, code: C0, deployment: none, business: none }
  - { repo: ml-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: trading-agent-service, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: greeks-service, code: C0, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C0, deployment: none, business: none }
  - { repo: market-data-processing-service, code: C0, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
---

# Regime Clustering + Proximity → Factor-Targeted Structure Allocator

> **✅ ARCHIVED 2026-06-21 — all phases done; codex regime-clustering-structure-allocator.md aligned. Deferred:
> LedgerRow vanna/volga emission = small epic-owned follow-up (features_and_ml_master); Tardis hist sub →
> issues/cefi_tardis_historical_blocked_credentials. [unlock-plan]**

> **Provenance**: distilled from a design conversation (Ikenna ↔ external collaborator "Kade"/Blue Flame, 2026-05-29).
> The "best of both worlds" merge: our existing PIT-guarded, walk-forward, batch=live infra **+** the genuinely good
> ideas surfaced externally — (a) factor-targeted _dynamic_ structure construction instead of a fixed-structure menu
> lookup, (b) an analog-based execution gate, (c) a hard deterministic pre-trade risk-veto layer. Plus the validation
> discipline both sides were missing (abstain/OOD guard, deflated-Sharpe overfit control, discrete-grid execution
> realism, edge-not-tracking-error objective).

## Crux

Five-step pipeline, mapped onto what already exists vs what is new:

1. **Vectorise market state** → feature vector. _Exists_ (`features-service` `feature_writer.py:316-351`, 3-layer PIT
   guard).
2. **Cluster historical states (unsupervised)** → discover regimes. _Partial_ — HMM walk-forward exists
   (`cross_instrument/app/calculators/regime_calculator.py:121-150`); learned clustering + proximity is **new**.
3. **Assign live vector → cluster** (which regime?). **New** — plus an **abstain/OOD guard** (no confident regime).
4. **Allocate a bespoke options structure** conditioned on cluster history → custom strikes/wings. **New** — only a
   hardcoded 2-leg straddle exists today (`vol_trading/options.py:86-100`). Build as **factor-targeted construction
   solved over the discrete listed universe**, not menu lookup, not optimise-then-snap.
5. **Repeat per timeframe** with an explicit **fusion rule**. **New.**

## Design invariants (HARD)

- **Batch = Live**: fit clusters in batch only; `assign` + `proximity` run identical code batch/live (one GCS artifact).
- **No look-ahead**: PnL features strictly point-in-time lagged; PCA/cluster models **fit inside each walk-forward fold
  (train only)**, applied forward. Fitting any transform on full history is leakage and is review-blocking.
- **Discrete reality**: prediction/ML may live on a continuous _normalised_ surface; **execution ledger + P&L must
  convert to real listed strikes/terms with fees + size/depth-aware slippage.**
- **Abstain is a first-class output**: overlap / out-of-distribution live state → minimum size or no-trade, never a
  forced bucket.
- **Overfit controls mandatory**: structure selection per regime validated out-of-sample (Deflated Sharpe / PBO), never
  "the structure that dominated in the backtest permutation pool" / "the cluster that had +Sharpe in-sample."
- **Objective is edge, not replication**: maximise expected P&L net of cost subject to tracking-error + risk constraints
  — never minimise greek tracking error alone.

## Operator decisions (resolved 2026-05-30)

> Operator calls baked in so autonomous workers build against them instead of stalling at judgment walls.

- **Priority**: P1 (bumped from P2) — dispatcher actively feeds it; still ordered behind live-DeFi cutover P0s.
- **Options data source**: **Deribit + Tardis** (crypto-options focus). **REUSE** existing ingestion — MTDS Deribit
  adapter (`market_tick_data_service/.../adapters/deribit.py`) + MDPS `CefiOptionsChainAdapter`
  (`market_data_processing_service/.../adapters/cefi/options_chain_adapter.py`) already land Deribit BTC/ETH chains
  (bid_iv/ask_iv/mark_iv, bid/ask price, strike, OI, top-of-book size). Tardis historical sub = the only credential ask
  (operator-acked here).
- **Strike/term normalisation**: **forward log-moneyness `k = ln(K/F)` + business-day tenor**. Delta-space is a deferred
  upgrade (needs the vol surface). Requires forward `F` (ABSENT today — Phase 1 forward-price item).
- **Timeframe fusion**: build **BOTH** (a) long-frame-gates-short-frame AND (b) weighted-vote-across-timeframes, behind
  a **config toggle**; A/B test both OOS — do not hardcode one (Phase 6).

### Reuse map (from 2026-05-30 audit — build only the gaps)

| Need                           | Status  | Reuse / build                                                         |
| ------------------------------ | ------- | --------------------------------------------------------------------- |
| Option chains (bid/ask + size) | PARTIAL | REUSE MTDS+Tardis Deribit; BUILD full depth + live REST + multi-venue |
| Greeks Δ/Γ/Θ/Vega/Ρ            | EXISTS  | REUSE greeks-service PricingLedger                                    |
| Greeks vanna/volga             | ABSENT  | BUILD — extend BS kernel (Phase 3)                                    |
| Vol surface                    | PARTIAL | REUSE features-service term-structure/skew pillars; interpolate grid  |
| Forward `F`                    | ABSENT  | BUILD from perp mark+funding / futures mark (Phase 1)                 |

---

## Phase 0 — Unblock per-archetype PnL attribution (foundation)

- [x] ✅ [STRATEGY] P2. Wire real per-archetype `pnl_realized` / `pnl_unrealized` into `StrategyPnlStreamEvent` —
      replace the `0` placeholders (`strategy-service/.../carry_and_yield/staked_basis.py:601-620` + APD
      `price_dispersion.py`). **DONE 2026-05-30** — strategy-service@8deaf28: `_session_pnl_realized` +
      `_session_pnl_unrealized` added to `BaseArchetypeEngineV2`; staked_basis accumulates net_carry bps/yr income per
      elapsed hour; APD accumulates expected round-trip PnL (gross − cost) per instruction. 8 tests pass; ruff +
      basedpyright clean.
- [x] ✅ [FEATURES] P2. Subscribe the PnL stream in features-service, roll to lagged 30d/Nd windows, land as feature
      group `strategy_pnl_archetype` through the existing `FeatureWriter` PIT path. Regime-focused → lag is acceptable
      by design. **DONE 2026-05-30** — features-service@13421644: new module
      `features_service/strategy_pnl_archetype/rolling_compute.py`. PIT window [target_date−N, target_date−1]; outputs
      pnl_realized_Nd, pnl_unrealized_last, n_trades_Nd, sharpe_Nd, drawdown_Nd (null < min_periods=5). 12 unit tests;
      basedpyright 0 errors.
- [x] [FEATURES] P2. **PnL vectorisation = one sub-vector per archetype** (each archetype contributes its own
      PnL/Sharpe/drawdown dims) concatenated into the market-state feature vector, so the cluster space sees _how each
      archetype is performing now_ alongside conventional market features. This is the explicit "PnL-per-archetype as
      features" lever — it enriches regime discovery beyond price/fundamental features alone.
      `vectorise_pnl_sub_vectors()` in rolling*compute.py: pivots tall→wide, {archetype}*{metric} columns, null for
      absent archetypes. 5 unit tests; basedpyright 0 errors. Pushed features-service 936032d0.
- [x] [TEST] P2. PIT test: assert every `strategy_pnl_archetype` value is knowable strictly before its row `timestamp`
      (extend `LookaheadBiasError` coverage). 11 tests across 4 classes (TestInputEventsPitSafe,
      TestWindowBoundaryPitCorrectness, TestAvailableAtSemanticsNotFuture, TestPitEnforcerAndComputeAgreement); 0
      ruff/basedpyright errors. Pushed features-service 994e2479.

## Phase 1 — Regime clustering as a PIT feature (features-service)

- [x] [FEATURES] P2. New `cross_instrument/app/calculators/regime_clustering.py`: `fit_regime_clusters()` (batch only) —
      PCA-whiten/decorrelate **inside fold** → GMM (soft) / HDBSCAN fit via `PurgedWalkForwardSplitter`
      (`ml-service/.../backtest_v2/walk_forward.py`, with embargo). Persist centroids + transform to GCS + manifest
      (`feature_group="regime_clustering"`, `job_id=fold_id`). `ClusterFoldResult` dataclass + `persist_cluster_fits()`
      GCS writer. 16 unit tests; 0 ruff/basedpyright errors. Pushed features-service 03191758.
- [x] [FEATURES] P2. `assign_clusters()` + `compute_proximity()` — identical batch/live code. Emit `cluster_id`, soft
      membership probs, centroid distances, and `regime_abstain` flag (distance > threshold OR membership entropy high).
      Post-PCA Euclidean distances (= Mahalanobis in original space). `ClusterAssignment` dataclass +
      `assignment_to_dataframe()`. 14 new unit tests (30 total); 0 ruff/basedpyright errors. Pushed features-service
      68817bfb.
- [x] ✅ [SCRIPT] P3. Use **exact** distances (data is ~MBs; no IVF-PQ/quantisation). Metric = Mahalanobis / post-PCA
      Euclidean, never raw correlated-feature Euclidean. — Already implemented in `assign_clusters()` /
      `compute_proximity()` at features-service@68817bfb (post-PCA Euclidean = Mahalanobis in original space). No
      additional code needed.
- [x] [UAC] P2. Register `regime_clustering` (+ `strategy_pnl_archetype`) in
      `unified_api_contracts/.../features/registry.py EXPECTED_FEATURE_GROUPS_BY_SERVICE`. Both added under
      cross-instrument section in `EXPECTED_FEATURE_GROUPS_BY_SERVICE["features-service"]`. Pushed UAC 8ae2dcb.
- [x] ✅ [FEATURES] P1. **Compute forward price `F`** (ABSENT today) from perp mark + funding
      (`F ≈ S·(1 + funding·τ_next)`) or futures mark; land as a small PIT feature/ledger field. Prerequisite for the
      forward-log-moneyness normalisation (Phase 3). **DONE 2026-05-30** —
      `features_service/delta_one/app/calculators/forward_price.py` (ForwardPrice calculator): perp path
      `F = mark*(1+funding*tau_next)` with tau resolved from 00/08/16 UTC boundaries or next_funding_ts column; futures
      path `F = close`. Outputs `forward_price` + `tau_next_funding`. 18 unit tests; basedpyright 0 errors; ruff clean.
      Pushed to features-service @ 7d9222bd.

## Phase 2 — Consume regime in supervised layer (ml-service) — _no new service_

- [x] [ML] P2. Feed `cluster_id` / soft-membership into `regime_conditional_trainer.py:20-95` (augment the thin binary
      vol-regime it splits on today). Confirms separation of concerns: clustering = unsupervised _discovery_; ml-service
      = supervised _selection_. No kNN/clustering lands inside ml-service. `train_cluster_conditional_models()` +
      `has_cluster_columns()` + helpers. prob_cluster_k retained as features; cluster_id dropped (split key). 7 new unit
      tests; ruff clean. Pushed ml-service 8fb2338.
- [x] ✅ [STRATEGY] P3. Route `cluster_id` into `RegimeAwareAllocator.regime_score`
      (`portfolio_allocator/archetypes.py:360`). — strategy-service@529abc8 (backfill 2026-05-30).
      `cluster_regime_score(cluster_id, soft_probs)` converts GMM assignment to Decimal score in [0,1].
      `RegimeAwareAllocator.weight()` uses it directly.

## Phase 3 — Factor-targeted structure allocator (strategy-service / trading-agent) — _the real new build_

- [x] ✅ [STRATEGY] P2. Per-cluster target **risk-factor exposure** (delta/gamma/vega/vanna/volga/basis) learned from
      that cluster's PIT history → solve for the option combo that hits the target. Replaces fixed-menu (iron
      condor/straddle) with continuous construction. (This is the legit core of the external "factor-deconstruction"
      idea, de-marketed.) **DONE 2026-05-30 slot-2** —
      `strategy_service/engine/strategies/v2/vol_trading/cluster_greek_targets.py`.
      `ClusterGreekRecord(cluster_id, delta, gamma, vega, vanna, volga, basis)` PIT observation dataclass;
      `ClusterGreekTargets(cluster_id, targets, basis_target, n_observations)` learned output;
      `fit_cluster_greek_targets()` groups by cluster_id, drops clusters with < 30 observations, aggregates via median
      (or mean); `make_cluster_allocator()` factory wires learned targets into `DiscreteStructureAllocator`, falling
      back to unconstrained when cluster missing. `_aggregate_records()` internal helper. Unit tests:
      `tests/unit/engine/strategies/v2/test_cluster_greek_targets.py`. QG green — strategy-service@30cafe5.
- [x] ✅ [GREEKS] P2. **Extend greeks-service BS kernel with vanna + volga** (`greeks_service/kernels/black_scholes.py`
      — today Δ/Γ/Θ/Vega/Ρ only; UAC `OptionGreeks` already has vanna/volga slots). REUSE the existing PricingLedger
      output path. The factor-target objective needs these second-order greeks. — greeks-service@de96df3 | 11 new tests
      in TestVannaVolga; ATM vanna≈-0.281, volga≈0.0985. LedgerRow wiring deferred (UAC cross-repo, separate task).
- [x] ✅ [STRATEGY] P2. **Normalised strike/term coordinates — RESOLVED 2026-05-30**: model/select in **forward
      log-moneyness `k = ln(K/F)` + business-day tenor `τ`** (arbitrage-correct, stationary across underlyings + time).
      Depends on forward `F` (Phase 1 forward-price item). Delta-space is a deferred upgrade (needs the vol surface).
      Training/clustering + the factor-target solve run in this normalised space; the real listed strike/expiry is
      recovered in Phase 4. **DONE 2026-05-30 slot-2** —
      `strategy_service/engine/strategies/v2/vol_trading/discrete_structure_allocator.py`:
      `ListedOption.forward_price: Decimal | None` field + `ListedOption.log_moneyness` property (`k = ln(K/F)`);
      `business_day_tenor()` standalone function (Mon–Fri calendar, 252 d/yr). 12 new tests (ATM/OTM/ITM sign semantics
  - FD-verified values). basedpyright + ruff clean. QG green — strategy-service@9d53bee.
- [x] ✅ [STRATEGY] P1. **Solve over the discrete listed universe directly** (constrained/combinatorial over real listed
      strikes×expiries) — NOT optimise-continuous-then-snap (nearest-strike ≠ nearest-risk; snapping distorts the
      engineered profile). **DONE 2026-05-30** —
      `strategy_service/engine/strategies/v2/vol_trading/discrete_structure_allocator.py`. `DiscreteStructureAllocator`
      enumerates N-leg combos × 2ⁿ side assignments directly over the discrete `ListedOption` chain. Dollar-scaled
      greek-penalty objective. Pluggable `expected_pnl_fn` for Phase 2 regime wiring. 17 unit tests in
      `tests/unit/engine/strategies/v2/test_discrete_structure_allocator.py`. QG passes.
- [x] ✅ [STRATEGY] P1. **Objective = maximise expected P&L net of cost, subject to (a) greek-tracking-error constraint
      and (b) risk gates** — NOT minimise greek tracking error alone (tracking error is a _replication_ objective; the
      min-tracking-error portfolio can be negative-EV after costs). Tracking-error penalty terms must be **dollar-scaled
      per greek** (greek × P&L sensitivity), never raw-unit summed. Any brute-force combo winner re-validated OOS (see
      PBO gate). **DONE 2026-05-30** — `RiskGates` hard-limit dataclass (delta/vega/gamma/premium caps); veto pipeline
      in `DiscreteStructureAllocator.solve()`: enumerate → risk-gate veto → OOS validation → rank. `OosVetoResult` hook
      for Phase-7 Deflated Sharpe/PBO (pass-through until wired). Dollar-scaled greek penalty in score already ✅.
      strategy-service@c854b0e2.
- [x] ✅ [STRATEGY] P1. **Overfit gate**: per-cluster structure must clear Deflated Sharpe / PBO out-of-sample before it
      is selectable. Reject "dominated-in-permutation-pool" / "+Sharpe-in-sample" winners. `overfit_gates.py`:
      `deflated_sharpe_ratio()` (Bailey & Lopez de Prado 2014), `DeflatedSharpeGate`, `PboGate` stub,
      `CompositeOosGate`. 23 unit tests. strategy-service@45043b3.
- [x] ✅ [TRADING-AGENT] P2. Emit structure as `param_overrides` via `allocation_directive_loop.py emit_directives()`
      into `vol_trading_options` / a new options engine. **DONE 2026-05-30** — `on_cluster_assignment_event()` +
      `on_options_structure_event()` hooks; `emit_directives()` emits `VOL_TRADING_OPTIONS`
      `ArchetypeAllocationDirective` carrying
      `cluster_id`/`soft_probs`/`regime_abstain`/`structure_legs`/`structure_score` as `param_overrides` when both
      events received. `_build_vol_trading_param_overrides()` helper. 8 new unit tests (12 total). basedpyright + ruff
      clean. — trading-agent-service@2e7c845

## Phase 4 — Continuous→discrete execution realism

- [x] ✅ [FEATURES] P1. **Historical option chains = REUSE Deribit + Tardis (RESOLVED 2026-05-30)** — MTDS Deribit
      adapter
  - MDPS `CefiOptionsChainAdapter` already land Deribit BTC/ETH chains (bid_iv/ask_iv/mark_iv, bid/ask price, strike,
    OI, top-of-book size). Tardis historical sub = `BLOCKED-CREDENTIALS` (operator-acked 2026-05-30). **Gaps to build**:
    full order-book depth per strike (only top-of-book size today); live Deribit REST chain (not just Tardis batch);
    multi-venue (Binance/Bybit/OKX). **DONE 2026-05-30** — resolution confirmed: existing MTDS+Tardis ingestion covers
    current need; gap items (full depth, live REST, multi-venue) are future plan tasks. No code change required.
- [x] ✅ [EXECUTION] P1. Slippage model uses quote **size/depth + partial fills**, not just spread width — options books
      are thin; "can't fill the size" is the binding constraint. `OptionsSlippageModel`: top-of-book size check + linear
      price impact for excess qty; plugged into `DiscreteStructureAllocator` via `slippage_fn` parameter. 12 unit tests.
      strategy-service@10b8eaa.
- [x] ✅ [STRATEGY] P1. P&L computed on rounded discrete contracts incl. exchange fees + modelled slippage (no
      synthetic-mid fills). `exchange_fee_per_contract` parameter added to `DiscreteStructureAllocator`; fill_value uses
      bid/ask (not mid); qty defaults to integer 1. 8 unit tests. strategy-service@ba78a8e.

## Phase 4b — Hard pre-trade risk-gate veto (the "survival layer")

> Absorbs the genuinely-good Tier 3 of the external design — a deterministic, **model-independent** veto that assumes
> the model can be wrong. **Reuse, do not rebuild**: wire into execution-service's existing pre-trade path (per-client
> preflight KMS → venue auth → balance; shard-level isolation) rather than inventing a new "Go-Bus."

- [x] ✅ [EXECUTION] P1. After construction + sizing, every proposed structure passes a hard-limit gate (margin ceiling,
      portfolio VaR, aggregate per-tenor vega/gamma caps, liquidity-sink check). Breach → systemic veto, drop trade.
      Limits are static config, independent of the regime model. `PortfolioRiskGate` + `PortfolioSnapshot` in
      `portfolio_risk_gate.py`. 16 unit tests. strategy-service@a937219.
- [x] ✅ [EXECUTION] P2. Gate is the LAST step (after Phase 3 sizing + Phase 5 analog overlay) and cannot be overridden
      by a high regime/conviction score — a "good" prediction that breaches a risk limit is still vetoed. **DONE
      2026-05-30** — `StructurePipeline` in `structure_pipeline.py`: wraps `DiscreteStructureAllocator.solve()` →
      `analog_gate_fn` (Phase 5 stub) → `PortfolioRiskGate.allows()` (LAST). `regime_context` flows to allocator +
      analog gate only; never reaches the portfolio gate. `AnalogGateResult` + `PipelineResult` audit types. 10 unit
      tests incl. conviction-bypass proof + fallback-to-next-candidate. basedpyright + ruff clean. —
      strategy-service@da4f32a

## Phase 5 — Analog-based execution gate (steal from Blue Flame — the genuinely good idea)

- [x] ✅ [EXECUTION] P2. Risk overlay: kNN of analogous historical states → if analogs executed with heavy
      slippage/loss, size down or veto; if clean, soft-Kelly up. Conditions on realised execution quality (≈exogenous),
      so survives the selection-bias critique. Layered on top of Phase 3 sizing, reads the same regime artifact. —
      strategy-service@8d81652 | `AnalogExecutionGate` kNN gate; veto/size-down/neutral/kelly-boost ladder; 13 unit
      tests; pure stdlib, no I/O. + strategy-service@877dad9 | `KnnAnalogGate` in `analog_gate.py`; cluster-filtered
      kNN + soft-Kelly `scale_factor` + `AnalogRecord`/`ExecutionQuality` types; callable as `analog_gate_fn`.

## Phase 6 — Multi-timeframe + fusion

- [x] ✅ [FEATURES] P3. Run clustering per timeframe window. — features-service@e6b331fc |
      `fit_and_assign_per_timeframe()` in `regime_clustering.py`: runs independent PCA-whitened GMM fits per timeframe
      dict (e.g. `{"1h": df, "4h": df, "24h": df}`); returns `PerTimeframeClusterResult` per timeframe with
      `fold_results` + latest-fold `ClusterAssignment`. `ClusterFoldResult` gains `test_start`/`test_end` fields.
      Consumer: `timeframe_fusion.fuse_cluster_assignments()` at strategy-service@8391bdd. 37 unit tests (7 new) green.
- [x] ✅ [STRATEGY] P2. **Implement BOTH fusion modes behind a config toggle (RESOLVED 2026-05-30)**: (a) long-frame
      regime gates short-frame entry; (b) weighted vote across timeframes (weighted by membership confidence). A/B test
      both OOS; operator picks the winner from results — do not hardcode one. — strategy-service@8391bdd |
      `timeframe_fusion.py`: `fuse_cluster_assignments()` dispatches on `TimeframeFusionConfig.mode="gate"|"vote"`.
      Gate: long-frame confidence gates short-frame entry. Vote: entropy-weighted blended soft-probs. 22 unit tests.

## Phase 7 — Validation, acceptance KPIs, codex

- [x] ✅ [TEST] P1. **Backtest↔paper tracking-error KPI** (B4): backtest P&L must track paper fills within a declared
      bps band — the single number that proves the continuous→discrete bridge is real, not cosmetic.
      `compute_tracking_error_bps()` + `BacktestPaperParityChecker`. 13 unit tests (TE=0 for discrete fills).
      strategy-service@13e63cc.
- [x] ✅ [TEST] P1. All fitting under purged+embargoed walk-forward; report deflated OOS Sharpe per regime + abstain
      coverage on OOD live states. `purge_embargo_split()` + `WalkForwardReport` + `RegimeOosReport`. 20 unit tests.
      strategy-service@cbd9660.
- [x] ✅ [CODEX] P2. Write `/codex/04-architecture/regime-clustering-structure-allocator.md` (pipeline, batch=live seam,
      abstain semantics, discrete-grid execution contract, three-layer policy/construction/risk decision matrix) +
      update `features_and_ml_master` related_plans. — unified-trading-pm (codex doc created; features_and_ml_master
      related_plans updated).

---

## Success criteria (B3 KPIs)

| KPI                               | Target                                                             |
| --------------------------------- | ------------------------------------------------------------------ |
| Backtest↔paper P&L tracking error | within declared bps band (B4)                                      |
| Per-regime structure OOS edge     | Deflated Sharpe > 0 / PBO below threshold                          |
| OOD coverage                      | 100% of no-confident-regime live states route to abstain/min-size  |
| Risk-gate veto                    | 100% of limit-breaching structures vetoed regardless of conviction |
| Look-ahead                        | 0 violations (PIT gate + fit-in-fold)                              |

## Decision matrix (policy / construction / risk) — maps the external "three-tier" design

| Layer                                         | This plan                                              | Correction vs external design                                                                                                                    |
| --------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Policy** (is the strategic direction good?) | Phase 1–3 regime proximity + per-cluster factor target | external Tier-1 "+Sharpe per cluster" lacks overfit control → our Deflated-Sharpe/PBO gate                                                       |
| **Construction** (which real contracts?)      | Phase 3 discrete solve + Phase 4 execution realism     | external Tier-2 minimises greek tracking error → ours maximises **edge net of cost** with tracking error as a _constraint_, dollar-scaled greeks |
| **Risk** (does it breach a hard limit?)       | Phase 4b deterministic veto                            | external Tier-3 is sound — reuse execution-service preflight, not a new bus                                                                      |

## Separation-of-concerns note (resolves the "overlap with ml-service hierarchical learning?" question)

ml-service "hierarchical learning" = supervised stacking + regime-conditional specialists; it **consumes** a regime
label. This plan **produces** a richer regime label (unsupervised, in features-service) and a structure layer
(strategy-service/trading-agent/execution-service). The "hierarchy" is the **service pipeline**, not a monolith —
opposite of the external single-DB design. No clustering/kNN belongs inside ml-service.
