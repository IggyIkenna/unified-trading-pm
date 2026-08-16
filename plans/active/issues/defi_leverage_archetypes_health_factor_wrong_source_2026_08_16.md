---
doc_type: issue
title: >-
  DeFi-leverage archetypes' liquidation kill-gate reads the wrong data source — the correct centralized module
  exists but nothing calls it
summary: >-
  `CARRY_STAKED_BASIS` and `CARRY_RECURSIVE_STAKED` — the only two DeFi archetypes that take on-chain leverage
  (post collateral / borrow against it) — both gate liquidation risk on `features.get("health_factor")`, a generic
  features-service value that carries no wallet-specific meaning and has never been populated with real data. The
  correct centralized module (`DeFiHealthAggregator` / `positions_health.py`, already client_id-scoped) exists but
  is never called from the strategy engine — it's HTTP-only, execution-service-facing. Also found: the centralized
  module itself isn't fed by any live source (only tests call its update path), a stub on-chain Aave adapter in
  strategy-service returns `NotImplementedError`, and the data model is missing LTV/borrow-capacity/liquidation-price
  fields an archetype would need. Filed per operator direction to establish a strategy-agnostic, venue-agnostic
  centralized pattern for private on-chain position/risk reads, after two rounds of investigation surfaced this
  while scoping the Elysium carve-out's excluded `health_factor` field.
status: open
nature: issue
asset_group: [defi]
stage: [execution]
repos: [strategy-service, execution-service, unified-api-contracts]
scope: [engineer]
tags: [defi, risk, health-factor, liquidation, architecture, centralization, strategy-agnostic]
related:
  [
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
    /codex/04-architecture/defi-execution-overview.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: infrastructure_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role:
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/defi-position-risk-centralization.md,
  ]
source: >-
  Interactive session 2026-08-16, surfaced while scoping which DeFi feature fields the Elysium carve-out owes the
  client. Two agent-dispatched investigations traced the actual wiring rather than trusting docstrings: the first
  found features-service's `_process_health_factor()` docstring falsely claims per-wallet Aave polling (it actually
  reads generic protocol-level rate-index data); the second enumerated every DeFi-leverage-capable archetype and
  traced their real risk-data sourcing end to end.
---

# DeFi-leverage archetypes' liquidation kill-gate reads the wrong data source

## Finding

Exactly two archetypes in strategy-service take genuine on-chain DeFi leverage (post collateral, borrow against
it) — everything else (`rotation_lending.py`, all three `defi_lp/*.py` engines, every non-DeFi archetype) is
supply-side/LP-only or CEX-margin, confirmed by an exhaustive search for borrow/collateral/lend logic:

| Archetype | File | Leverage mechanism |
| --- | --- | --- |
| `CARRY_STAKED_BASIS` | `strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py` | `LST_AS_MARGIN` mode posts the LST as real on-chain-derived perp margin |
| `CARRY_RECURSIVE_STAKED` | `strategy_service/engine/strategies/v2/carry_and_yield/recursive_staked.py` | Genuine `STAKE→LEND→BORROW→STAKE...` recursive loop |

**Both read their liquidation kill-gate from the same wrong source**: `features.get("health_factor")` —
`staked_basis.py:419`, `recursive_staked.py:115` (entry gate) and `:447` (exit/unwind gate, `_check_family2_health_kill`).
That key comes from features-service's generic per-tick features pipeline. A separate investigation this session
found the pipeline function that was believed to populate it (`_process_health_factor()` in
`features-service/features_service/onchain/engine/orchestrator.py`) has a **false docstring** — it claims to poll
Aave's `getUserAccountData()` per wallet, but actually reads the same generic MTDS `rate_indices` data every
sibling Aave feature calculator uses, with no wallet parameter anywhere. The value has never carried real
per-position meaning, and the corpus has never had it populated (confirmed: paper-run substitutes a hardcoded
safe constant because "the dedicated health_factor feature group carries no numeric column yet in this corpus,"
`strategy_service/cli/handlers/paper_run_handler.py:26-28,343`).

**`recursive_staked.py` copied the pattern deliberately, not accidentally** — its own docstring (lines 436-439)
says it reuses "the same `health_factor` feature / `min_health_factor`" as `staked_basis.py`. Any future third
DeFi-leverage archetype is likely to copy the same broken precedent unless a correct centralized call is
established as the pattern to copy instead.

## The correct centralized module exists — but nothing calls it, and nothing feeds it

- `strategy_service/position/core/defi_health_aggregator.py` (`DeFiHealthAggregator`) is genuinely venue/protocol-
  agnostic by construction (iterates whatever `DeFiLendingPosition` objects it's given, keyed by protocol/chain, no
  protocol-specific branching) and already `client_id`-scoped. **But it's only instantiated in
  `position/api/routes/risk.py:248,271` (HTTP routes) — never imported by any `engine/strategies/v2/**` file.**
- `positions_health.py`'s own docstring names its real consumer as execution-service's `run_wallet_preflight_checks`
  Layer-4, not strategy-service archetypes.
- **Neither is fed by a live source today.** Grep found only test-file callers of `update_wallet_health_from_lending`
  — no production code path pushes real lending-position data into `DeFiHealthAggregator`'s state.
- A third piece, `strategy_service/position/position_interface/adapters/aave.py` (`AavePositionAdapter`), looks like
  it should be that live feed — but `get_balances()` and `get_positions()` both `raise NotImplementedError`
  (lines 71-78). It's a non-functional stub, and even if implemented it returns the wrong schema
  (`CanonicalPosition`, not `DeFiLendingPosition`) to plug directly into the aggregator.
- The one genuinely working live poller is `execution-service/execution_service/defi_execution/monitors/health_factor_monitor.py`
  (real `getUserAccountData()` calls, per-wallet) — but it isn't wired to feed `DeFiHealthAggregator` either.

**So there are three unconnected pieces**: (1) execution-service's working live poller, (2) strategy-service's
non-functional stub adapter, (3) the aggregation/serving logic with no live feed. None of the three talk to each
other today.

## Data model gaps

Even once wired, the centralized data model can't yet serve everything an archetype needs:

- `DeFiAggregatedHealth`/`ProtocolHealthBreakdown` (the aggregator's output) has health factor, collateral USD,
  debt USD, weighted APY, and per-chain breakdown — **but no LTV, no borrow-capacity, no liquidation-price** field.
  `recursive_staked.py` needs LTV for loop-depth sizing (currently derives it from static/governance params instead
  of live position state, `recursive_staked.py:156,176`).
- `PositionHealthSnapshot` (`positions_health.py`) has LTV and a `liquidation_threshold` the aggregator lacks — but
  that threshold is **hardcoded to `MarginModel.AAVE_V3`** (`positions_health.py:70-72`), not resolved per the
  position's actual protocol, so it silently gives a wrong answer for a non-Aave position.

## Todos

- [ ] [OPERATOR] P0. **Decide the fix shape**: (a) build a thin in-process/client-callable path from
      `engine/strategies/v2/*` into `DeFiHealthAggregator`/`positions_health` (new function, or a call to the
      existing HTTP route), or (b) a shared helper both strategy-service and execution-service import, keyed by
      wallet/client. Currently only the HTTP-route path exists; an archetype's `on_tick()` needs something callable.
- [ ] [AGENT] P0. **Wire a live feed into `DeFiHealthAggregator`.** Either finish `aave.py`'s
      `AavePositionAdapter` (fixing its schema mismatch — emit `DeFiLendingPosition`, not `CanonicalPosition`) or
      route execution-service's already-working `health_factor_monitor.py` output into the aggregator's state via
      `update_wallet_health_from_lending`. Do not build a third parallel poller.
- [ ] [AGENT] P0. **Switch `staked_basis.py:419` and `recursive_staked.py:115,447` to the centralized source**,
      once (a) and the live feed exist. This is the actual liquidation-risk fix — until this lands, both
      archetypes' kill-gates are not protecting against real liquidation risk.
- [ ] [AGENT] P1. **Extend the centralized data model**: add LTV, borrow-capacity, and liquidation-price to
      `DeFiAggregatedHealth`/`ProtocolHealthBreakdown`, or unify with `PositionHealthSnapshot`'s fields. Fix the
      `AAVE_V3`-hardcoded liquidation-threshold lookup in `positions_health.py:70-72` to resolve per-position
      protocol instead.
- [ ] [AGENT] P1. **Decide `aave.py`'s fate explicitly** — delete it in favor of the execution-service poller +
      PBMS pipeline, or finish it as the canonical feed. Don't leave a non-functional stub sitting alongside a
      working parallel path.
- [ ] [AGENT] P2. **Fix the misleading `_process_health_factor()` docstring** in
      `features-service/features_service/onchain/engine/orchestrator.py:621-623` — it describes per-wallet Aave
      polling the function doesn't do; describe it as generic protocol-level rate-index data instead.
- [ ] [AGENT] P2. **Once the centralized path exists, document and enforce it as the pattern** for any future
      DeFi-leverage-capable archetype — see the companion codex doc
      [defi-position-risk-centralization](/codex/04-architecture/defi-position-risk-centralization.md), authored
      in the same session.
- [ ] [OPERATOR] P2. **Design the mode-aware dispatch** (operator direction, 2026-08-16): batch → real historical
      data for that window; live → real-time poll against the actual wallet; paper splits into **paper-testnet**
      (poll a testnet deployment, validates wiring without touching production wallets) and **paper-live**
      (read-only poll of real mainnet data for the real wallet, no execution). Apply once the centralized path from
      the todos above exists — designing the mode dispatch before the underlying call exists would be premature.

## Progress Log

- **2026-08-16** — Filed from an interactive session. Two agent-dispatched investigations: the first debunked an
  initial "features-service queries private wallet data" hypothesis (it doesn't — the docstring was just wrong);
  the second enumerated every DeFi-leverage-capable archetype and traced the real gap precisely. Read-only research
  throughout — no code changed. Explicitly out of scope for the Elysium carve-out (`elysium_carveout_stubbed_strategy_service_2026_08_12.md`
  §A4 already excludes `health_factor` from that plan's data-scope, since no DeFi-side leverage is taken in the
  contracted strategies), but real production-risk-relevant for `staked_basis.py`'s live `LST_AS_MARGIN` structure
  if it's currently trading.
