---
name: paper-vs-live-execution-seam
overview:
  Pins the principle that batch / paper / live differ ONLY at the execution layer — strategy / risk / P&L / position /
  alerting / instructions are identical across modes. Pricing has no real "paper" concept (just right data); mock-data
  is for risk simulations + dev fixtures (NOT paper-trading); mock-vs-paper is operator-discipline only (no
  enforcement).
type: codex-ssot
status: canonical (extracted from master plan + question doc 2026-05-10)
created: 2026-05-09
last_reviewed: 2026-05-10
locked_by: live-defi-rollout
locked_since: 2026-05-09
spawned_from: plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
implements_in: plans/active/master_to_live_defi_2026_05_23.md # Group F items 17/20
---

# Paper-vs-live execution seam

> **Canonical 2026-05-10.** Per-venue paper-target policy + simulate-first-floor / testnet-upgrade-where-credentials-
> exist mechanics live in [`../05-infrastructure/per-venue-paper-policy.md`](../05-infrastructure/per-venue-paper-policy.md)
> (the `paper_target_registry` SSOT). Solana paper for non-EVM uses devnet / localnet / surfnet per the same registry.
> Consumer-site implementation (Group F sub-items `pvl-p17a` / `pvl-p17b` / `pvl-p17c` / `pvl-p17d` / `pvl-p20a..c`)
> owned by `master_to_live_defi_2026_05_23.md`.

## TL;DR

The workspace SSOT is **batch = paper = live = same code path, only fill source differs**. The seam where modes diverge
sits exclusively in execution-service:

- **Batch**: matching engine produces fills against historical replay.
- **Paper**: matching engine produces fills against live ticks (simulate-first floor) OR real venue testnet / forked
  chain (testnet upgrade per `paper_target_registry`).
- **Live**: real venue API + real capital + real fills.
- **Manual**: real venue API + real capital, but operator pulls the trigger per instruction.

Strategy / risk / P&L / position-balance / alerting / reconciliation / instructions are **identical across all four
modes**. Anything else branching on mode is an anti-pattern.

## Three principles

### 1. Pricing has no real "paper" concept

Either the data is right (current live tick stream, accurate historical replay) or it isn't. There is no "paper price"
that's distinct from a "live price." A strategy in batch reads historical ticks; in paper or live it reads the current
Pub/Sub feed. Same upstream, same shape. **Don't introduce paper-specific data sources.**

### 2. Mock data is for risk simulations + dev fixtures, NOT paper-trading

`CLOUD_MOCK_MODE=true` / `VITE_MOCK_API=true` / `MOCK_STATE_MODE=interactive` are dev-mode flags. Risk simulations (drop
the underlying 30%, spike funding to 100bps/8h, simulate a venue freeze, simulate a chain reorg) live in a separate
surface owned by
[`risk_simulations_limits_alerting_2026_05_08.md`](../../plans/questions/risk_simulations_limits_alerting_2026_05_08.md).

Mock-data ≠ paper-trading. Conflating them is an anti-pattern.

### 3. Mock-vs-paper boundary is operator-discipline, NOT enforced

The combinations `(paper_trade=true, CLOUD_MOCK_MODE=true)` and similar are **legitimate** — UI dev rendering against
mock backend with paper-shaped data is a real use case. execution-service does NOT hard-refuse these combinations at
boot. Operator-discipline keeps the boundary; no code-level enforcement (Settled #10).

## The execution seam concretely

Within execution-service, the seam manifests as:

```
Strategy emits instruction (carries mode: OperationalMode field per pvl-p17d)
    │
    ▼
Risk-and-exposure pre-flight checks (mode-blind)
    │
    ▼
Position-balance state-update (mode-blind)
    │
    ▼
Execution-service routes per `decompose(mode)`:
    │
    ├─ target == SIMULATION ──▶ matching engine (5 matchers: L0 Sports TOB, L1 TradFi,
    │                                              L2 CeFi, AMM, ALPHA_ZERO benchmark)
    │
    ├─ target == TESTNET ─────▶ paper_target_registry[venue/chain] →
    │                              EVM: Tenderly fork
    │                              Solana: devnet/localnet/surfnet
    │                              Deribit: testnet endpoint
    │                              Sports: PaperBettingAdapter
    │                              Prediction: matching-engine simulation
    │                              (default fallback): matching engine
    │
    └─ target == LIVE_VENUE ──▶ real venue adapter (CeFi connector / DeFi connector /
                                  sports adapter / prediction adapter)
                                  + trigger == MANUAL → manual-pending queue (operator
                                    approves via DART per pvl-p23c)
                                  + trigger == AUTOMATED → fire immediately
```

## Reconciliation

> **DEFERRED — DESIGN-ONLY 2026-05-12 (per slot 8 audit PB-5)**: 3-way reconciliation (batch ↔ paper ↔ live) is the
> *target* shape per `pvl-p21a`. Today the live `batch-live-reconciliation-service` stage DAG ships **5 logical
> stages** (`stage0_config_pull` + `stage0_data_pipeline_recon` + `stage1_ml_recon` + `stage2_strategy_recon` +
> `stage3_execution_recon` + `stage4_agent_analysis` + `stage5_results_writer`) and **per-stage thresholds only**
> (`MLThresholds` / `StrategyThresholds` / `ExecutionThresholds` / `DataPipelineThresholds` in
> `models/deviation_thresholds.py` — no per-pair batch/paper/live constants and no `paper_live_recon.py` /
> `batch_paper_recon.py` stage). Successor plan: `pvl-p21a` (3-way recon design) + `master_to_live_defi_2026_05_23.md`
> Group F-21.

The target 3-way reconciliation (batch ↔ paper ↔ live) will extend `batch-live-reconciliation-service` per `pvl-p21a`:

- **Batch-vs-live**: will match within slippage + commission tolerance over a window. The original recon target (ships today).
- **Paper-vs-live**: will match more tightly (same data, similar API conditions). Useful pre-cutover signal (DEFERRED).
- **Batch-vs-paper**: will match within matching-engine fidelity tolerance. Validates simulator faithfulness (DEFERRED).

Once shipped, per-pair tolerance thresholds will be codified in `models/deviation_thresholds.py`. Closed-set
failure-routing policy will be: alert / auto-pause-live / auto-demote-to-paper.

## Composes with

- [`operational-modes.md`](operational-modes.md) — the canonical mode enum + decompose helper.
- [`batch-live-architecture.md`](batch-live-architecture.md) — broader batch=live SSOT this doc specialises.
- [`../05-infrastructure/per-venue-paper-policy.md`](../05-infrastructure/per-venue-paper-policy.md) — the
  `paper_target_registry` SSOT.
