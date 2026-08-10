---
doc_type: codex-ssot
title: paper-vs-live-execution-seam
summary:
  Pins the principle that batch / paper / live / manual differ ONLY at the execution-service fill source — strategy /
  risk / P&L / position / alerting / reconciliation are identical across modes; pricing has no "paper" concept, mock
  data is for risk-sims not paper-trading, and the mock-vs-paper boundary is operator-discipline (no code enforcement).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [batch-live-reconciliation-service, execution-service]
scope: [engineer, admin]
tags: [paper-trading, live-trading, execution, reconciliation, defi, batch-live]
related:
  [
    /codex/04-architecture/operational-modes.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/execution-modes-and-chain-resolution.md,
    /codex/05-infrastructure/per-venue-paper-policy.md,
    /codex/04-architecture/reconciliation-resolution.md,
  ]
created: 2026-05-09
authoritative_for: [paper-vs-live-vs-batch execution seam, mode-divergence-only-at-execution-layer principle]
referenced_by:
  [
    /codex/04-architecture/multi-mode-wallet-isolation.md,
    /codex/04-architecture/operational-modes.md,
    /codex/04-architecture/order-state-machine.md,
    /codex/04-architecture/reconciliation-resolution.md,
    /codex/04-architecture/separation-of-concerns.md,
    /codex/05-infrastructure/per-venue-paper-policy.md,
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md,
    /codex/14-customer-journeys/dart/mode-toggle.md,
  ]
owner:
last_reviewed: 2026-08-09
code_refs:
overview:
  Pins the principle that batch / paper / live differ ONLY at the execution layer — strategy / risk / P&L / position /
  alerting / instructions are identical across modes. Pricing has no real "paper" concept (just right data); mock-data
  is for risk simulations + dev fixtures (NOT paper-trading); mock-vs-paper is operator-discipline only (no
  enforcement).
type: codex-ssot
locked_by: live-defi-rollout
locked_since: 2026-05-09
spawned_from: plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
implements_in: plans/archive/2026_07/master_to_live_defi_2026_05_23.md
---

# Paper-vs-live execution seam

> **Canonical 2026-05-10.** Per-venue paper-target policy + simulate-first-floor / testnet-upgrade-where-credentials-
> exist mechanics live in
> [`/codex/05-infrastructure/per-venue-paper-policy.md`](/codex/05-infrastructure/per-venue-paper-policy.md) (the
> `PAPER_EXECUTION_TARGETS` SSOT — the name `paper_target_registry` used in these docs matches no code symbol; see the
> note below). Solana paper for non-EVM uses devnet / localnet / surfnet per the same registry. Consumer-site
> implementation (Group F sub-items `pvl-p17a` / `pvl-p17b` / `pvl-p17c` / `pvl-p17d` / `pvl-p20a..c`) owned by
> `master_to_live_defi_2026_05_23.md`.

## TL;DR

The workspace SSOT is **batch = paper = live = same code path, only fill source differs**. The seam where modes diverge
sits exclusively in execution-service:

- **Batch**: matching engine produces fills against historical replay.
- **Paper**: matching engine produces fills against live ticks (simulate-first floor) OR real venue testnet / forked
  chain (testnet upgrade per `get_paper_target()`).
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
[`risk_simulations_limits_alerting_2026_05_10.md`](../../plans/archive/risk_simulations_limits_alerting_2026_05_10.md).

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
    ├─ target == TESTNET ─────▶ get_paper_target(venue_or_chain) →
    │                              Solana: devnet/localnet/surfnet
    │                              Deribit: testnet endpoint
    │                              Sports: PaperBettingAdapter
    │                              Prediction: matching-engine simulation
    │                              (default fallback): matching engine
    │
    ├─ target == FORK ─────────▶ get_paper_target(venue_or_chain) →
    │                              EVM: Tenderly fork
    │
    └─ target == MAINNET ─────▶ real venue adapter (CeFi connector / DeFi connector /
                                  sports adapter / prediction adapter)
                                  + trigger == MANUAL_OPERATOR → manual-pending queue (operator
                                    approves via DART per pvl-p23c)
                                  + trigger == AUTOMATED → fire immediately
```

## Reconciliation

> **SHIPPED 2026-05-27 (was DESIGN-ONLY DEFERRED 2026-05-12 per slot 8 audit PB-5; un-deferred per BLRS audit
> `plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md`)**: 3-way reconciliation (batch ↔ paper ↔
> live) is **implemented today**. The `batch-live-reconciliation-service` stage DAG ships `stage0_config_pull` +
> `stage0_manifest_reason_check` + `stage0_data_pipeline_recon` + `stage1_ml_recon` + `stage2_strategy_recon` +
> `stage3_execution_recon` + **`stage3b_paper_live_recon`** + **`stage3c_batch_paper_recon`** +
> `stage4_agent_analysis` + `stage5_results_writer`, with **per-pair thresholds** (`PaperLiveThresholds` 2× tighter,
> `BatchPaperThresholds` wider) in `models/deviation_thresholds.py`. Successor plan `pvl-p21a` remains open only for
> per-archetype tolerance bands (see `master_to_live_defi_2026_05_23.md` Group F-21).

The 3-way reconciliation (batch ↔ paper ↔ live) in `batch-live-reconciliation-service`:

- **Batch-vs-live** (`stage3_execution_recon`): matches within slippage + commission tolerance over a window. The
  original recon target.
- **Paper-vs-live** (`stage3b_paper_live_recon`): matches more tightly (same data, similar API conditions) — 2× tighter
  thresholds; breaches route `AUTO_DEMOTE_TO_PAPER`. Pre-cutover wiring signal.
- **Batch-vs-paper** (`stage3c_batch_paper_recon`): matches within matching-engine fidelity tolerance; breaches route
  `ALERT` only. Validates simulator faithfulness.

Per-pair tolerance thresholds are codified in `models/deviation_thresholds.py`. Failure-routing actions in use today:
`ALERT` + `AUTO_DEMOTE_TO_PAPER` (`AUTO_PAUSE_LIVE` is defined but not yet wired). **Per-archetype** tolerance bands
remain the open `pvl-p21a` extension.

## Composes with

- [`operational-modes.md`](operational-modes.md) — the canonical mode enum + decompose helper.
- [`batch-live-architecture.md`](batch-live-architecture.md) — broader batch=live SSOT this doc specialises.
- [`/codex/05-infrastructure/per-venue-paper-policy.md`](/codex/05-infrastructure/per-venue-paper-policy.md) — the
  `PAPER_EXECUTION_TARGETS` / `get_paper_target()` SSOT.

## Review note — 2026-08-09 (code-verified)

Reviewed against the live code rather than date-bumped. What was checked and found:

- ✅ **The instruction carries the mode.** `mode: OperationalMode` is a real field on `StrategyInstruction`
  (`unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/_instruction_base.py`, ~line 308), with
  its own unit tests — the `pvl-p17d` claim above holds.
- ✅ **The matching engine and its ALPHA_ZERO benchmark matcher exist**
  (`unified_api_contracts/internal/domain/matching_engine/`).
- ❌ **`paper_target_registry` is not a real symbol.** Every reference in this doc has been renamed to the actual API:
  `PAPER_EXECUTION_TARGETS` (a `dict[str, ExecutionTarget]`) and `get_paper_target(chain_or_venue)`, both in
  `unified_api_contracts/internal/paper_execution_targets.py`. The old name appears only in PM docs — 7 doc hits, 0 code
  hits — so anyone grepping the codebase for it found nothing and had no way to tell whether the registry was unbuilt or
  merely misnamed. It is built; it was misnamed here.
- ✅ **`ExecutionTarget.FORK` matters to this doc's seam diagram — FIXED 2026-08-10 (docs-reconcile).**
  `get_paper_target("ethereum")` returns `FORK`, not `TESTNET`, so the EVM/Tenderly path is a distinct target rather
  than a flavour of testnet; the diagram above now has its own `target == FORK` branch instead of nesting Tenderly under
  `TESTNET`. See `/codex/04-architecture/operational-modes.md`'s corrected schema block (same review pass) for the full
  enum.

Sibling corrections from the same pass — including three "deleted" anti-patterns that are still live — are tracked in
`/plans/active/issues/operational_modes_antipatterns_not_actually_deleted_2026_08_09.md`.
