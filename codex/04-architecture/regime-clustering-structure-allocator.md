# Regime Clustering → Factor-Targeted Structure Allocator

> SSOT for the end-to-end pipeline from market-state vectorisation to live options structure selection. **Plan of
> record**: `plans/active/regime_clustering_structure_allocator_2026_05_29.md`

---

## Pipeline (5 steps)

```
features-service          ml-service / strategy-service      strategy-service / execution-service
─────────────────────     ──────────────────────────────     ────────────────────────────────────
1. Vectorise             2. Cluster + assign               3. Construct             4. Gate + fill
   market state    →       regime + OOD guard       →       factor-targeted    →    risk veto +
   (PIT, lagged)            abstain if unclear              options structure       slippage model
                                                                    ↓
                                                          5. Repeat per timeframe → fuse
```

### Step 1 — Vectorise market state

- **Who**: `features-service` `feature_writer.py` (3-layer PIT guard, lagged features).
- **Output**: feature vector per tick, per instrument. Includes `strategy_pnl_archetype` group (per-archetype rolling
  P&L, Sharpe, drawdown).
- **Look-ahead invariant**: all features strictly point-in-time lagged; zero future contamination.

### Step 2 — Cluster historical states / assign live vector

- **Who**: unsupervised clustering (GMM (soft) or HDBSCAN) trained inside each walk-forward fold.
- **Batch**: fit clusters on train split → save artifact to GCS.
- **Live**: load artifact → assign incoming vector → emit `ClusterAssignmentPayload`.
- **Abstain guard**: when membership entropy exceeds threshold (OOD state) → `regime_abstain=True` → minimum size or
  no-trade. Never force-assign an uncertain vector into a regime.
- **No-look-ahead rule**: clustering models fit on train window only; applied forward on held-out data.

### Step 3 — Factor-targeted structure construction

- **Who**: `strategy_service/engine/strategies/v2/vol_trading/discrete_structure_allocator.py`.
- **Objective**: maximise expected P&L net of execution cost, **subject to** Greek-tracking-error constraints. Not
  tracking-error minimisation (which is negative-EV after costs).
- **Discrete-grid invariant**: solve runs over real listed strikes × expiries; no continuous proxy then snap.
  Nearest-strike ≠ nearest-risk.
- **Dollar-scaled Greeks**: every penalty term multiplied by caller-supplied `dollar_scale` so all terms are in USD.
- **Per-cluster targets**: `cluster_greek_targets.py` learns median delta/gamma/vega/vanna/volga/basis per cluster from
  PIT history (≥30 observations; missing clusters fall back to unconstrained).
- **Normalised coordinates**: log-moneyness `k = ln(K/F)` + business-day tenor τ (252 d/yr). Forward
  `F = spot + funding carry`. Delta-space deferred (needs full vol surface).

### Step 4 — Gate + fill

Three independent layers applied in order. A breach at any layer vetoes the structure.

| Layer                                  | Module                                           | Trigger                                                                              |
| -------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------ | --- | --- | ---- | --- | --- | --------------------------- |
| **Risk gates** (pre-score)             | `RiskGates` in `discrete_structure_allocator.py` |                                                                                      | Δ   | ,   | Vega | ,   | Γ   | caps; premium floor/ceiling |
| **Portfolio gate** (post-construction) | `portfolio_risk_gate.py`                         | Margin ceiling, per-tenor vega/gamma, liquidity cost                                 |
| **Analog execution gate** (Phase 5)    | `analog_gate.py` `KnnAnalogGate`                 | kNN of historical analogs; size down/veto on bad execution history; cluster-filtered |

**Slippage model**: `options_slippage.py` — size/depth-aware. Legs that walk past top-of-book depth are penalised by
`price_impact_per_contract × qty_beyond²`. Plugged into `DiscreteStructureAllocator` via `slippage_fn`.

### Step 5 — Multi-timeframe fusion

- **Who**: `timeframe_fusion.py`.
- **Two modes** (config toggle, never hardcode one):
  - **`"gate"`**: long-frame assignment checks "is the wind at our back?". If long-frame abstains or confidence <
    threshold, short-frame signal is suppressed.
  - **`"vote"`**: entropy-weighted blended soft-probs across all timeframes. Abstain when blended entropy > threshold.
- **A/B**: both modes deployed; OOS Deflated Sharpe comparison picks the winner.

---

## Batch = Live seam

| Concern           | Batch                                           | Live                                            |
| ----------------- | ----------------------------------------------- | ----------------------------------------------- |
| Clustering model  | fit on train fold                               | load GCS artifact, `assign()` only              |
| Feature PIT guard | 3-layer (`feature_writer.py:316-351`)           | identical code path                             |
| Structure solve   | `DiscreteStructureAllocator.solve()`            | identical code path                             |
| Greek computation | `greeks-service` `BlackScholesKernel`           | identical Decimal arithmetic                    |
| Fill simulation   | `options_slippage.py`                           | execution-service fills — same model parameters |
| Schema            | `LedgerRow` (option_delta/gamma/theta/vega/rho) | identical                                       |

**Hard rule**: no separate backtest code path. Fills in batch are simulated; fills in live are real — same model, same
risk gates, same slippage model parameters.

---

## Abstain semantics

`regime_abstain=True` is a **first-class output**, not an error. It triggers when:

1. Membership entropy of the cluster assignment exceeds the OOD threshold.
2. Long-frame fusion gate suppresses the short-frame signal.
3. Blended vote entropy is too diffuse to commit to a cluster.

**On abstain**: the strategy outputs minimum size (or zero) for the current tick. No structure is constructed. The
decision is logged as `abstain_reason` in `FusedClusterAssignment`. KPI: 100% of no-confident-regime live ticks must
route to abstain — enforced in `RegimeOosReport`.

---

## Discrete-grid execution contract

1. **Listed universe**: real bid/ask/size from MTDS Deribit adapter + Tardis historical fills.
2. **Two-sided liquidity required**: `ListedOption` with `bid=None` or `ask=None` filtered out unless
   `require_two_sided=False`.
3. **Fill price**: buy legs fill at ask; sell legs fill at bid. No synthetic mid.
4. **Cost model**: `half_spread × qty` base + depth walk-in for `qty > top_of_book_size`.
5. **Greek convention**: vanna = ∂Δ/∂σ per unit fractional vol; volga = ∂vega/∂σ per unit fractional vol (inherits
   vega's /100 scale).
6. **No snap**: discrete solve runs on the real listed grid from the start. Never optimise a continuous proxy then round
   to nearest strike.

---

## Three-layer policy / construction / risk decision matrix

| Layer            | Implemented by                                            | What it decides                                | Key correction vs naïve designs                                                                      |
| ---------------- | --------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Policy**       | `ClusterAssignmentPayload` + per-cluster greek targets    | Is the strategic direction good? Which regime? | Deflated Sharpe / PBO overfit gate; abstain on OOD; no look-ahead                                    |
| **Construction** | `DiscreteStructureAllocator`                              | Which real contracts? What size?               | Edge objective (not tracking-error minimisation); dollar-scaled constraints; discrete from the start |
| **Risk**         | `RiskGates` + `PortfolioRiskGate` + `AnalogExecutionGate` | Does it breach a hard limit?                   | Model-independent, unconditional veto; analog gate conditions on exogenous execution quality         |

The three layers are **always executed in order** (enforced by `StructurePipeline`). A veto at any layer overrides all
lower-layer decisions. No exception for "high-conviction" regime signals.

```python
# structure_pipeline.py — enforced step order (cannot be reordered)
candidates = allocator.solve(regime_context)          # Phase 3
for candidate in candidates:
    analog = analog_gate_fn(candidate, regime_context)  # Phase 5
    if not analog.passes: continue
    pg_ok, _ = portfolio_gate.allows(candidate, snapshot)  # Phase 4b (LAST)
    if not pg_ok: continue
    return PipelineResult(candidate=candidate)
```

`regime_context` (cluster_id, soft_probs, feature_vector) flows to phases 3 and 5 only. The `PortfolioRiskGate` is
intentionally blind to conviction.

---

## Service ownership

| Component                         | Service                           | Module                                                                                                                  |
| --------------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Feature vectors + PnL sub-vectors | `features-service`                | `feature_writer.py`, `strategy_pnl_archetype/rolling_compute.py`                                                        |
| Clustering fit + assignment       | `features-service` (fit + assign) | `cross_instrument/regime_calculator.py` (features-service@`68817bfb` ships `assign_clusters()` + `compute_proximity()`) |
| Abstain guard                     | `strategy-service`                | `discrete_structure_allocator.py` `RiskGates`                                                                           |
| Structure solve                   | `strategy-service`                | `discrete_structure_allocator.py`                                                                                       |
| Greek computation                 | `greeks-service`                  | `kernels/black_scholes.py` `BlackScholesKernel`                                                                         |
| Slippage model                    | `strategy-service`                | `options_slippage.py` `OptionsSlippageModel`                                                                            |
| Portfolio gate                    | `strategy-service`                | `portfolio_risk_gate.py` `PortfolioRiskGate`                                                                            |
| Analog execution gate (kNN)       | `strategy-service`                | `analog_gate.py` `KnnAnalogGate` — cluster-filtered; slippage/win-rate veto; soft-Kelly scale                           |
| Gate pipeline                     | `strategy-service`                | `structure_pipeline.py` `StructurePipeline` — enforced Phase 3→4b→5 ordering                                            |
| Timeframe fusion                  | `strategy-service`                | `timeframe_fusion.py` `fuse_cluster_assignments()`                                                                      |
| Cluster greek targets             | `strategy-service`                | `cluster_greek_targets.py` `fit_cluster_greek_targets()`                                                                |
| Listed chain                      | `market-tick-data-service`        | `adapters/deribit.py` + `adapters/tardis.py`                                                                            |

---

## Separation-of-concerns note

**ml-service "hierarchical learning"** = supervised stacking + regime-conditional specialists. It **consumes** a regime
label.

**This pipeline** = **produces** the regime label (unsupervised clustering in features-service) + the resulting
structure (strategy-service → execution-service).

The "hierarchy" is the **service pipeline**, not a monolith. Clustering/kNN belongs in features-service +
strategy-service — never inside ml-service.

---

## Overfit controls (mandatory)

| Control                                   | Where                                                | What                                         |
| ----------------------------------------- | ---------------------------------------------------- | -------------------------------------------- |
| Purged + embargoed walk-forward           | `walk_forward_kpi.py` `purge_embargo_split()`        | Eliminates look-ahead and train-test leakage |
| Deflated Sharpe                           | `walk_forward_kpi.py` `WalkForwardReport`            | OOS Sharpe with multiple-testing correction  |
| PBO (Probability of Backtest Overfitting) | computed per cluster                                 | Rejects in-sample-only artefacts             |
| OOD abstain coverage                      | `walk_forward_kpi.py` `RegimeOosReport`              | 100% of OOD ticks must route to abstain      |
| Backtest↔paper tracking error            | `tracking_error_kpi.py` `BacktestPaperParityChecker` | Proves continuous→discrete bridge is real    |
