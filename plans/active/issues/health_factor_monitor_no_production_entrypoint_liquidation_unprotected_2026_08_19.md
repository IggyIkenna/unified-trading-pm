---
doc_type: issue
title: HealthFactorMonitor has zero production instantiations — the liquidation trigger path for leveraged DeFi positions may be unwired
summary: >-
  `execution_service/defi_execution/monitors/health_factor_monitor.py`'s `HealthFactorMonitor` is real, substantial,
  near-block-time monitoring code, but `HealthFactorMonitor(` has ZERO production call sites (measured 2026-08-19,
  tests excluded). `DeleverageExecutor` has exactly one — a module-level `_DEFAULT_EXECUTOR` singleton, which is
  instantiation without evidence of anything driving it. Leveraged DeFi carry positions (carry_staked_basis and
  siblings) depend on this path to react to liquidation risk faster than the strategy's own evaluation cadence. If
  nothing runs the monitor, that protection does not exist at runtime.
status: open
nature: issue
asset_group: [defi]
stage: [execution]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [defi, liquidation, health-factor, risk, funds-safety, unwired-code, execution]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /codex/04-architecture/position-risk-centralization.md,
    /codex/09-strategy/architecture-v2/axes/hold-policy.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-19
last_updated: "2026-08-19"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P0
severity: P0
source: >-
  Operator asked what happens to carry_staked_basis on liquidation, and whether hourly evaluation is adequate. A
  sub-agent traced the real trigger path and reported the monitor had no production call sites; the orchestrating
  session independently reproduced the measurement before filing.
drift_direction: advance-code
depends_on: []
context_scope:
  [
    execution-service/execution_service/defi_execution/monitors/health_factor_monitor.py,
    execution-service/execution_service/algo_library/deleverage_executor.py,
    /codex/04-architecture/position-risk-centralization.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
---

# The liquidation trigger path has no production caller

## What the operator asked

*"What do we do when we get liquidated, or there's a chance of liquidation? How does that carry forward? If we're
evaluating every hour, it's not great if we get liquidated — we need trigger-based stuff from the risk engine."*

The design answers that correctly. The runtime may not.

## Measured 2026-08-19

| Symbol                                | Production instantiations (tests excluded) |
| ------------------------------------- | ------------------------------------------ |
| `HealthFactorMonitor(`                | **0**                                      |
| `DeleverageExecutor(`                 | 1 — `_DEFAULT_EXECUTOR` module-level singleton in `algo_library/deleverage_executor.py` |

The design is sound and is NOT the problem: liquidation response is meant to be **event-triggered**, not
schedule-polled. `HealthFactorMonitor` runs a near-block-time per-chain WS/poll loop; `DeleverageExecutor` is
`MarginEvent`-driven. `timeframe: 1h` on a DeFi carry config is a **feature/backtest bar resolution**
(`cli/handlers/batch_handler.py`), never a risk-check cadence — so the hourly figure the operator saw was never
the liquidation cadence.

The gap is that nothing appears to start the monitor.

## Why P0

This is the same shape as `TransferCoordinator` never being instantiated in production: real code, real tests,
no runtime entry point — and a spot-check of the class itself looks healthy. It sits on a **leveraged, live-capital
DeFi path**, where the failure mode is a liquidation nobody reacted to. A monitor that is never started raises
nothing and logs nothing, so its absence is invisible until it matters.

## Todos

- [ ] [AGENT] P0. **Establish whether anything starts `HealthFactorMonitor` at runtime.** Grep is necessary but not
      sufficient — check service bootstrap/startup wiring, any task-runner or scheduler registration, and whether it
      is constructed indirectly (factory, DI container, config-driven registry). A negative result must be a
      *measured* negative, naming what was searched, not "0 grep hits".
- [ ] [BACKEND] P0. **If it is genuinely unwired, wire it** — the monitor must be started for every chain carrying
      a leveraged position, with its lifecycle tied to the position's, not to a request. If it IS wired by an
      indirect path, document that path in
      [position-risk-centralization](/codex/04-architecture/position-risk-centralization.md) so the next reader does
      not repeat this investigation.
- [ ] [BACKEND] P0. **Confirm `DeleverageExecutor` is actually driven.** A module-level singleton exists; find what
      publishes the `MarginEvent`s it consumes and prove the chain from margin event to executed deleverage. If the
      publisher is missing, the executor is decorative.
- [ ] [REVIEW] P1. **State the liquidation contract in the strategy configs' own terms.** For every leveraged DeFi
      archetype, record what happens on liquidation and on approach-to-liquidation, and which component owns each
      step — so a config author can see the protection rather than assume it.
- [ ] [REVIEW] P1. **Sweep for the same defect class.** `TransferCoordinator`, `HealthFactorMonitor` and
      `QuoteHandler` (deleted 2026-08-15) are three instances of substantial code with no production entry point.
      Enumerate execution-service classes with tests but no non-test instantiation — this is now a pattern, not a
      coincidence.

## Progress Log

**2026-08-19 — filed.** No code touched. Measurement reproduced independently by the orchestrating session before
filing; the sub-agent that first reported it had tracked it only as a `[AGENT] P2` trace task inside an unrelated
repricer design doc, which understates a funds-safety gap.
- **context-scout 2026-08-20**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — conflict-checked before considering RECLASSIFY: `plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md` (status: open) already tracks the identical HealthFactorMonitor/DeleverageExecutor wiring trace as its own `[AGENT] P2` open todo (line ~638) — the same duplicate-tracking risk flagged in this doc's own body ("the sub-agent that first reported it had tracked it only as a [AGENT] P2 trace task inside an unrelated repricer design doc"). `w_state_recovery_real_wiring_2026_08_20.md` (assigned_vm: planning, active) explicitly EXCLUDES HealthFactorMonitor from its own scope (line ~235), confirming this gap is known fleet-wide but deliberately not yet dispatched anywhere. Per the conflict-check rule, NOT extracting the bounded measure/confirm todos (1, 3) this pass — a coordinated citation-fix against the repricer doc is needed first to avoid a future duplicate dispatch. This remains a real P0 funds-safety finding; flagging in the audit report per the workspace's big-finding rule even though already properly filed. Doc stays `assigned_vm: NA`.
