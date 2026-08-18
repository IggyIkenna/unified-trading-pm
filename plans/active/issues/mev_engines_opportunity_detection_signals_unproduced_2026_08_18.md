---
doc_type: issue
title: 3 of 4 code-shipped MEV strategy engines have no producer for their own opportunity-detection features
summary: >-
  BACKRUN, JIT_LIQUIDITY, and LIQUIDATION_BUNDLE are all `implementation_status: code-shipped` with real, wired
  cost/profitability math (gas, fees) — but the feature keys that answer "is there an opportunity right now"
  (backrun_target_swap_size_usd_<chain>, backrun_arb_spread_bps_<chain>, jit_pending_swap_size_usd_<pool>,
  liq_candidate_debt_amount_<id>, liq_candidate_health_factor_<id>, liq_candidate_liq_bonus_pct_<id>) have zero
  producer anywhere in the workspace. `features.get(key, 0.0)` silently defaults, so these engines cannot fire in a
  real paper/live run today, despite being registered and "shipped." A distinct root cause from the ARBITRAGE_MEV_
  SANDWICH mempool-feed gap (that one is genuinely blocked on infrastructure that doesn't exist; this one just needs
  calculators built from data that likely already exists).
status: open
nature: issue
asset_group: [defi]
stage: [strategy, features]
repos: [strategy-service, features-service]
scope: [engineer]
tags: [mev, defi, strategy-correctness, silent-default, data-correctness, features-service]
priority: P1
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
created: 2026-08-18
source: >-
  Found investigating whether ARBITRAGE_MEV_BACKRUN/_JIT_LIQUIDITY/_LIQUIDATION_BUNDLE could be declared in UAC's
  ARCHETYPE_FEATURE_GROUPS registry, prompted by an operator question ("where is mempool data actually available")
  after MEV was left undeclared for a mempool-visibility reason. Sibling finding to
  `defi_gas_net_cost_partial_wiring_gap_2026_08_17.md` (same class of bug — a real formula reading a feature nothing
  produces — but that doc covered the COST/profitability side, already mostly fixed; this covers the
  TRIGGER/opportunity-detection side, not previously checked).
related:
  [
    /plans/active/issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md,
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-backrun.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-jit-liquidity.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-mev-liquidation-bundle.md,
  ]
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
---

# 3 of 4 code-shipped MEV engines have no producer for their own opportunity-detection features

## What was checked (grep-then-read, not grep-only)

Every feature key each engine's `on_tick()` actually reads (`features.get(...)`), then a workspace-wide search
(features-service, market-data-processing-service, strategy-service, instruments-service) for a real producer of
each specific key name — not the feature_group's existence, the EXACT key.

## Real, wired (confirmed by `defi_gas_net_cost_partial_wiring_gap_2026_08_17.md`, not re-verified here)

- `block_priority_gas_p90_gwei_<chain>` → `features-service/.../block_priority_gas_distribution_calculator.py`.
- `dex_swap_fee_bps_<pool>` → `features-service/.../dex_pool_swap_flow_calculator.py`.
- `gas_price_gwei_<chain>` / `gas_cost_usd` → real, MTDS `gas_fees`-sourced (yesterday's fix).
- `flash_loan_fee_bps_<source>` → UAC `FEES_REGISTRY` constant, not a feature but a real cited number.
- `lp_pool_sqrt_price_<pool>` — has a real caller in `strategy-service/.../paper_run_handler.py::_build_dex_lp_tick`
  (shared with the already-declared `DEFI_LP_CONCENTRATED`/`DEFI_LP_POOL`), though whether that path is genuinely
  fed by live captured data in a real (non-paper) run was not traced to its end this session.

## NOT WIRED — zero producer found anywhere, silently defaults to 0.0/""

1. **`BACKRUN`** (`strategy-service/.../mev/backrun.py:71-74`) — `backrun_target_swap_size_usd_<chain>`,
   `backrun_arb_spread_bps_<chain>`, `backrun_target_pool_<chain>` all `.get(key, 0.0)`/`.get(key, "")`. Since
   `target_swap_usd` defaults to 0.0 and the trigger is `target_swap_size_usd >= min_target_swap_usd` (a positive
   threshold), **the trigger condition can never be true in a real run.** Only `block_priority_gas_p90_gwei` (used
   for bid-sizing AFTER the trigger fires) is real — the trigger itself never fires.
2. **`JIT_LIQUIDITY`** (`strategy-service/.../mev/jit_liquidity.py:151`) — `jit_pending_swap_size_usd_<pool>`
   `.get(key, 0.0)`. Same shape: `pending_size < min_swap_threshold_usd` is always true when the key defaults to
   0.0, so the position never mints. The codex archetype doc's claim ("today the engine reads a features-onchain
   inferred signal") was not confirmed by this search — no calculator anywhere produces this specific key.
3. **`LIQUIDATION_BUNDLE`** (`strategy-service/.../mev/liquidation_bundle.py:265-267`) —
   `liq_candidate_debt_amount_<id>`, `liq_candidate_health_factor_<id>`, `liq_candidate_liq_bonus_pct_<id>`, all
   `.get(id_key)` with no default shown at these call sites (likely `None`, worth confirming) — meaning candidate
   IDENTIFICATION (which position is even liquidatable) has no producer, distinct from `LIQUIDATION_CAPTURE`'s
   already-declared `liquidation_clusters`/`liquidation_band_prediction` feature_groups, which this engine does NOT
   appear to read from directly (not confirmed as the same underlying data by this pass).

## Why this wasn't fixed in the same commit

This is real strategy/features craft work — building 3 new opportunity-detection calculators (or wiring existing
ones under new key names) — not a registry declaration or a data-pipeline fix. Filed rather than silently worked
around, per findings-triage. Deliberately NOT declared in UAC's `ARCHETYPE_FEATURE_GROUPS` for these 3 archetypes as
a result — declaring a feature_group these engines don't actually consume for their trigger condition would be the
exact "wrong entry, worse than honest gap" failure that registry's own docstring warns against.

## Distinct from the MEV mempool-feed gap

`ARBITRAGE_MEV_SANDWICH` needs infrastructure that doesn't exist (mempool visibility) — a data-source problem,
tracked via the already-paused `plans/archive/mempool_feed_integration_2026_06_01.plan.md`. Confirmed 2026-08-18
against bloXroute's own docs that this is a genuine, unavoidable constraint, not just this workspace's own gap:
Tx-Trace retains data "only for a few hours," Bundle-Trace covers only self-submitted bundles, and the Gateway
explicitly does not store blockchain data — no vendor sells historical mempool data because none exists past the
live window. Live-capture-then-batch (mirroring the prediction-market quote pipeline: subscribe live, persist what
streams by, backtest against the accumulating self-built corpus from that point forward) is the only path, and it
starts from zero history on day one.

These 3 (BACKRUN/JIT_LIQUIDITY/LIQUIDATION_BUNDLE) need calculators built from data that mostly already exists —
confirmed swap/pool-state data for BACKRUN/JIT_LIQUIDITY (see this doc's own §"Real, wired" above). For
LIQUIDATION_BUNDLE specifically: **correction to this doc's own earlier claim** — `LIQUIDATION_CAPTURE`'s declared
feature_groups (`liquidation_clusters`, `liquidation_band_prediction`) are CeFi-scoped
(`asset_group="cefi"`, `data_type={liquidations,book_snapshot,funding_rate,ohlcv_1m}`), NOT DeFi lending data — so
LIQUIDATION_BUNDLE cannot simply reuse them despite the "extends LIQUIDATION_CAPTURE" framing in its own codex doc.
Checked separately (2026-08-18): DeFi lending MARKET data for LIQUIDATION_BUNDLE's venue universe is real and
present — 7 of 8 protocols (AAVE_V3, COMPOUND_V3, FLUID, EULER_V2, RADIANT, VENUS, BENQI) show 100% Layer-1
completeness against their own declared expected matrix; the 8th, `MORPHO_BLUE` (the codex doc's own venue name),
is captured too, just under the real UAC venue name `MORPHO` (plus a separate `MORPHOVAULTS`) — a naming mismatch
between the codex archetype doc and the live registry, not a data gap. **Not yet confirmed**: whether the captured
data_type per venue actually carries health-factor/position-risk fields specifically (vs. only generic lending-rate
data) — the calculator-build todo below should verify this as its first step, not assume it.

**Bundle-simulation infrastructure exists** (found 2026-08-18, answering "do we need Tenderly too"): a real
`TenderlyExecutionProvider` already exists (`execution-service/execution_service/providers/tenderly.py`) — Tenderly
Virtual TestNet fork + `simulate-bundle` support (`TenderlyTx`/`BundleSimResult`), wired into the core
`matching_engine.py` (not governance-only — `governance/proposal_simulator.py` is a separate consumer of the same
generic provider). **Not confirmed**: whether `liquidation_bundle.py`/`jit_liquidity.py`/`sandwich_theoretical.py`
actually call it before submitting a bundle, or whether it's available-but-unused for MEV specifically (matching
this doc's own established pattern of infrastructure existing without being wired to its obvious consumer).

## Todos

- [ ] [REVIEW] P2. **Confirm whether the MEV engines actually call `TenderlyExecutionProvider.simulate-bundle`
      before submission** — infrastructure exists and is wired into `matching_engine.py`, but no MEV-engine call
      site was confirmed this session. If unused, that's a real pre-submission safety gap for `LIQUIDATION_BUNDLE`'s
      atomic flash-loan bundle in particular (a revert there costs gas only, but an unsimulated bundle is still a
      worse bet than a simulated one).
- [ ] [REVIEW] P1. **Confirm the exact default behavior** at `liquidation_bundle.py:265-267` (no explicit default
      shown in this pass — could be `None`, raising downstream, or silently coerced) before scoping the fix.
- [ ] [FEATURES] P2. **Build the BACKRUN opportunity-detection calculator** — `backrun_target_swap_size_usd_<chain>`
      / `backrun_arb_spread_bps_<chain>` / `backrun_target_pool_<chain>`, likely derivable from
      `dex_pool_swap_flow` (swap detection) + `cross_venue_spreads` (already-declared cross-venue spread) — needs a
      design decision on exact derivation, not a blind guess.
- [ ] [FEATURES] P2. **Build or confirm the JIT_LIQUIDITY pending-swap-size producer**
      (`jit_pending_swap_size_usd_<pool>`) — the codex doc's own text says this should already exist as an
      "inferred signal," which this session's search did not find; reconcile the doc against the code before
      building anything new.
- [ ] [STRATEGY] P2. **Build the LIQUIDATION_BUNDLE candidate-identification producer**
      (`liq_candidate_*_<id>`) — likely reuses `LIQUIDATION_CAPTURE`'s existing `liquidation_clusters`/
      `liquidation_band_prediction` feature_groups, but the exact ID-keyed shape these `.get()` calls expect needs
      confirming against what those feature_groups actually emit.
- [ ] [AGENT] P3. **Once any of the above lands, declare the corresponding archetype in UAC's
      `ARCHETYPE_FEATURE_GROUPS`** the same way the other MEV-adjacent archetypes were declared 2026-08-18 — real
      dispatch-site citation required, not inferred.

## Progress Log

**2026-08-18 — filed.** Found while investigating whether to declare 3 MEV archetypes in UAC's registry, not from a
dedicated audit — narrow, direct-read confirmation across the 3 engine files plus a workspace-wide grep for each
specific feature key, not a corpus-wide sweep.
