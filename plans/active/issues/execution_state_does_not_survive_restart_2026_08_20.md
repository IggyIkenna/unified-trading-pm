---
doc_type: issue
title: Execution-service cannot survive a restart with state intact — orders, positions, PnL and fills are all in-memory-only, and the one recovery component built for it is unwired
summary: >-
  Measured 2026-08-20: `InMemoryOrderPersistence` / in-memory position tracking are hardcoded in
  `engine/live/factory.py`, the `PostgreSQLOrderPersistence` alternative raises `NotImplementedError` from every real
  method and is not even offered by the factory, and `OrderRecoveryEngine` — the component built to reconcile surviving
  venue orders on startup — has zero production instantiations despite a `--skip-recovery` CLI flag and a docstring
  claiming it runs. A live process restart therefore loses the order book, positions, realised PnL and fee/funding
  accruals, with no venue reconciliation to rebuild them. This is a precondition for live capital, not a recovery-plane
  nicety.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    execution,
    durability,
    funds-safety,
    unwired-code,
    recovery,
    restart,
    reconciliation,
    epoch-fencing,
  ]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/04-architecture/cross-domain-state-fabric.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /plans/active/issues/health_factor_monitor_no_production_entrypoint_liquidation_unprotected_2026_08_19.md,
    /plans/epics/system_readiness_master.md,
  ]
context_scope:
  [
    execution-service/execution_service/engine/live/factory.py,
    execution-service/execution_service/engine/live/persistence/postgresql.py,
    execution-service/execution_service/engine/startup/order_recovery.py,
    execution-service/execution_service/pre_crash_checkpoint.py,
    execution-service/execution_service/services/account_history_client.py,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P0
severity: P0
source: >-
  Sonnet-5 sub-agent measurement audit dispatched 2026-08-20 against an external batch/paper/live recovery-plane
  architecture proposal. The audit was asked "what exists today" per claim; these findings are what it measured, with
  its own uncertainty flags preserved below.
drift_direction: advance-code
depends_on: []
---

# A restart loses the book

## The single sentence

**Kill an execution-service process today and the orders, positions, realised PnL, partial fills, fee and funding
accruals all go with it — and nothing queries the venue to rebuild them.**

## Measured 2026-08-20

| Finding                                                                                                              | Evidence                                                                                                                        |
| -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Order + position persistence is **in-memory only, and hardcoded**                                                     | `engine/live/factory.py:20-23 create_oms()` constructs `InMemoryOrderPersistence`; `factory.py:48-52` the same for positions       |
| The Postgres alternative is a **stub that would crash if selected**                                                    | `engine/live/persistence/postgresql.py` — every real method (`save_order`, `get_order`, `update_order_status`, `get_all_orders`, `get_orders_by_status`, `get_orders_by_strategy`, `save_position`, `get_position`, `get_all_positions`) raises `NotImplementedError`; the factory does not offer it as an option |
| `OrderRecoveryEngine` has **zero production call sites**                                                              | `rg 'OrderRecoveryEngine\('` → hits only in `tests/unit/engine/test_order_recovery.py` and `tests/unit/test_order_recovery.py`     |
| Its default venue adapter is an **explicit stub**                                                                     | `engine/startup/order_recovery.py:136-168` — `fetch_open_orders` returns `[]`; `cancel_order`/`confirm_cancel` always return `True` |
| The `--skip-recovery` flag's attribute is **never read**                                                              | `cli/argument_parser.py:183` defines it; `rg skip_recovery` → 0 reads. `cli/main.py:10-12` docstring claims the engine runs in live mode |
| `pre_crash_checkpoint.py` contains **no state serialization**                                                          | 101 lines: a SIGTERM handler + an 85%-RSS watchdog, both converging on one `logger.critical`, one `log_event`, `sys.exit()`. Nothing reads it back |
| Funding reconciliation **can never succeed**                                                                          | `providers/account_history_client.py` — `get_fill_fees` / `get_funding_payments` unconditionally `return []`; no subclass override found. `services/funding_recon_engine.py` therefore always reports PENDING |
| **No epoch fencing** on the order path                                                                                | searched `epoch\|fenc(e\|ing)\|lease\|generation_id\|instance_generation` across `engine/`, `orders/`, `orchestration/`, `api/` → zero hits |

## Why this is P0 and not an architecture improvement

The recovery-plane work this audit was scoping is a **design** question. This is not. Real capital plus an
in-memory-only order book means an ordinary deploy, an OOM kill, or a preemption leaves live orders resting at a venue
that the restarted process does not know exist, cannot cancel, and will not reconcile. The
[autonomous recovery matrix](/codex/04-architecture/autonomous-recovery-matrix.md) explicitly warns that "simply
stopping downstream processing is dangerous if it leaves live orders resting" — that is precisely the state a restart
produces today.

**This is the FOURTH instance of one pattern**, and that is now the finding rather than a coincidence: substantial,
tested code with no production entry point, where a spot-check of the class itself looks healthy.
`TransferCoordinator`, `HealthFactorMonitor`, `QuoteHandler` (deleted 2026-08-15), and now `OrderRecoveryEngine` —
which is worse than the others because a CLI flag and a docstring both actively assert it runs.

## Todos

- [ ] [BACKEND] P0. **Make order and position state durable before any live capital.** Either implement
      `PostgreSQLOrderPersistence` properly and offer it from `create_oms()`, or replace the persistence protocol with
      something that is durable by construction. Do NOT leave a `NotImplementedError` stub reachable by config — a
      `USE_DATABASE=true` that crashes on first save is worse than no option at all.
- [ ] [BACKEND] P0. **Wire `OrderRecoveryEngine` into the live startup path with a real venue adapter.** A component
      that a CLI flag and a docstring both claim runs, and which does not, is worse than an absent one — it defeats the
      check a reader would make. **Deleting it is NOT an option** (operator ruling R20, 2026-08-20): removing the
      declaration would satisfy any gate while moving the platform further from target state. The same applies to
      `PostgreSQLOrderPersistence` and to the unused `RedisStreamTransport` — build what is declared.
- [ ] [BACKEND] P0. **Make `--skip-recovery` do something or remove it.** Its attribute is defined and never read.
- [ ] [BACKEND] P1. **Implement `AccountHistoryClient` per venue, or make its emptiness loud.** Returning `[]`
      unconditionally means funding reconciliation reports PENDING forever and never fails — the same silent-plausible
      -default shape as `get_venue_asset_group()` returning `"cefi"`.
- [ ] [BACKEND] P1. **Add epoch fencing to the order path** so a superseded instance cannot keep submitting. Nothing
      currently prevents two live instances both sending orders.
- [x] ✅ [REVIEW] P1. **EXTRACTED 2026-08-21** — rename or gut `pre_crash_checkpoint.py`. Extracted to
      `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch (na-eligibility-audit,
      cross-cutting tranche, batch 2 of 3).
- [x] ✅ [AGENT] P1. **EXTRACTED 2026-08-21** — enumerate execution-service classes with tests but no non-test
      instantiation. Extracted to `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch
      (na-eligibility-audit, cross-cutting tranche, batch 2 of 3).
- [x] ✅ [REVIEW] P2. **EXTRACTED 2026-08-21** — close the audit's own open questions (read `engine/orphan_monitor.py`,
      `venue_failover.py`, `venue_cascade_monitor.py`, `manual_pending_queue.py`, `order_rejection_tracker.py`,
      `utils/fidelity_selector.py`, `trade_execution/adapters/_rate_limit.py`,
      `sports_execution/monitoring/venue_health.py:23 VenueHealthStatus` in full). Extracted to
      `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch (na-eligibility-audit,
      cross-cutting tranche, batch 2 of 3).

## What was measured as PRESENT, so nobody re-audits it

- **One matching kernel with declared fidelity levels** — `matching_engine/engine.py:701 MatchingEngine` routes by
  `BookType` to `L0Matcher` / `L1Matcher` / `L2Matcher` / `AMMMatcher` / `BenchmarkMatcher`. No true L3/MBO matcher,
  and latency/reject/venue-priority models are not part of the `BookType` taxonomy.
- **Side-effect suppression is a substituted adapter, not a flag** — `LiveMatchingEngine` vs `PaperMatchingEngine` with
  separate factories (`modes/live/matching_engine.py:179-205, 208-221`). The primitive is sound; it is selected on
  credential availability, not on a recovery phase.
- **UTL `EventTransport` supports cursor replay** — `read(after=...)` on all three implementations.
  `RedisStreamTransport` and `PubSubTransport` are consumer-independent append-only logs; `InMemoryTransport` is a
  bounded 10,000-entry deque with durability equal to process lifetime, and it is the paper/backtest topology.

## Progress Log

**2026-08-20 — filed.** No code touched. Findings come from a scoped read-only measurement audit; its uncertainty flags
are preserved in the P2 todo above rather than dropped. `PubSubTransport`'s module docstring still calls it a "stub
pending Plan 03 infra" while the implementation looks complete — not resolved here, and it is unclear which of the doc
or the code is stale.

- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries); corrected 1 stale path —
  `account_history_client.py` lives under `execution_service/services/`, not `execution_service/providers/`.
