---
doc_type: plan
title: recon-rebalancing-order-recovery-2026-03-10
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service, strategy-service, system-integration-tests]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
overview: Automated position correction, order recovery on restart, portfolio drift rebalancing, and DeFi vault yield rebalancing with full observability.
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: position-balance-monitor-service, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: execution-service, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: strategy-service, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-events-interface, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: system-integration-tests, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
depends_on: [stub_completion_interfaces_and_infra, error_normalisation_unknown_exchanges_2026_03_10, api_keys_and_auth]
todos:
- {id: stream-a-correction-dispatcher, content: Implement CorrectionDispatcher; wire into reconciliation_engine; add 2 UEI events, status: done, note: DONE — pbs/core/correction_dispatcher.py + startup_reconciler.py exist with real CorrectionDispatcher. POSITION_CORRECTION_DISPATCHED/FAILED events confirmed in schemas.py}
- {id: stream-b-order-recovery, content: Implement OrderRecoveryEngine; circuit breaker gate; wire into startup, status: done, note: DONE — execution-service/engine/startup/order_recovery.py with OrderRecoveryEngine. ORDER_ORPHANED/ORDER_RECOVERY_COMPLETED/FAILED events confirmed in schemas.py}
- {id: stream-c-portfolio-rebalancer, content: Implement PortfolioRebalancer; per-strategy config; wire into scheduler, status: done, note: DONE — strategy-service/engine/rebalancing/portfolio_rebalancer.py with PortfolioRebalancer. PORTFOLIO_REBALANCE_TRIGGERED/COMPLETED events confirmed in schemas.py}
- {id: stream-d-defi-vault-rebalancer, content: Implement DeFiVaultRebalancer; yield monitor; gas estimator, status: done, note: 'DONE — strategy-service/engine/rebalancing/defi_vault_rebalancer.py, defi_yield_monitor.py, gas_estimator.py all present. DEFI_VAULT_REBALANCED confirmed in schemas.py'}
- {id: uei-events, content: Add 8 new UEI events to unified-events-interface/schemas.py (coordinated via uei_pending_event_additions plan), status: done, note: 'DONE — all 8 events confirmed in schemas.py: POSITION_CORRECTION_DISPATCHED/FAILED, ORDER_ORPHANED/RECOVERY_COMPLETED/FAILED, PORTFOLIO_REBALANCE_TRIGGERED/COMPLETED, DEFI_VAULT_REBALANCED'}
- {id: integration-tests, content: Add test_recon_rebalancing.py integration tests in system-integration-tests, status: done, note: 'DONE — system-integration-tests/tests/integration/test_recon_rebalancing.py created; 10 integration tests covering all 4 streams (correction dispatcher, order recovery, portfolio rebalancer, DeFi vault rebalancer). Commit d29523a.'}
isProject: false
---

# Plan: Reconciliation, Rebalancing & Order Recovery

status: active priority: P0 owner: backend target: 2026-03-19

> ⚠️ **M4 SEQUENCING NOTE (2026-03-11):** This plan adds 8 UEI events to `unified-events-interface/schemas.py`. These
> events are tracked in `uei_pending_event_additions.md` — coordinate all UEI additions as a single PR batch to avoid
> schemas.py merge conflicts.
>
> **M5 UNBLOCKED (2026-03-11):** `error_normalisation_unknown_exchanges_2026_03_10` Phase 1 (P1.1
> `CanonicalUnknownVenueError`) is now DONE. The dependency that was blocking `CorrectionDispatcher` (Stream A) is
> resolved. This plan is now unblocked for implementation.
>
> **M4 SEQUENCING NOTE (Grafana):** Commit all `strategy-service` changes in this plan before
> `strategy_visibility_grafana_2026_03_10` begins. Grafana plan depends on `DEFI_VAULT_REBALANCED` and other events from
> this plan being in strategy-service schemas.

## Context

`position-balance-monitor-service` has a reconciliation engine (`PBS/core/reconciliation_engine.py`) that compares
internal fill-based positions against exchange-reported positions, producing MATCH/DISCREPANCY/CRITICAL snapshots.
However:

1. CRITICAL discrepancies only log/alert — no automated correction is triggered
2. On service restart, no order recovery logic reconciles open orders with exchange state
3. Portfolio drift (target weight vs actual weight) has no rebalancing workflow
4. DeFi vault positions across protocols (Aave/Curve/Uniswap) have no yield-differential rebalancing

Goal: the system autonomously corrects position discrepancies within config thresholds, recovers open orders on restart,
rebalances portfolio drift on schedule, and rebalances DeFi vaults on yield differentials — all with full observability
and no manual intervention required.

---

## Stream A: Position recon → automated correction

### A1 — Correction dispatcher

File: `position-balance-monitor-service/position_balance_monitor_service/core/correction_dispatcher.py` (new)

```python
class CorrectionDispatcher:
    """On CRITICAL discrepancy, submits a correction order via execution-service."""

    async def dispatch_correction(self, snapshot: ReconciliationSnapshot) -> None:
        """
        If snapshot.status == CRITICAL and abs(discrepancy) > auto_correct_threshold:
          1. Calculate correction qty = exchange_qty - internal_qty
          2. Submit market order via execution-service /orders REST endpoint
          3. Log POSITION_CORRECTION_DISPATCHED UEI event
          4. If execution fails: log POSITION_CORRECTION_FAILED, escalate to alerting-service
        """
```

Config fields (in PBS config.py):

- `auto_correct_threshold_pct: float = 1.0` — only correct if discrepancy > 1%
- `auto_correct_max_qty: float` — safety cap, never correct more than this
- `auto_correct_enabled: bool = False` — default off in dev, on in production

### A2 — Wire into reconciliation_engine.py

File: `position-balance-monitor-service/position_balance_monitor_service/core/reconciliation_engine.py`

After emitting `POSITION_CRITICAL_DISCREPANCY`, call `CorrectionDispatcher.dispatch_correction()` if
`auto_correct_enabled=True`.

New UEI events to add to `unified-events-interface/schemas.py`:

- `POSITION_CORRECTION_DISPATCHED`
- `POSITION_CORRECTION_FAILED`

### A3 — Startup reconciliation

File: `position-balance-monitor-service/position_balance_monitor_service/core/startup_reconciler.py` (new)

On PBS startup:

1. Fetch all positions from exchange REST APIs (full, not cached)
2. Run `reconciliation_engine.reconcile_all_positions()`
3. Log any CRITICAL discrepancies before accepting new data
4. Only emit `STARTED` event after startup reconciliation passes (or explicitly skipped with flag)

---

## Stream B: Order recovery on restart

### B1 — Order recovery module

File: `execution-service/execution_service/engine/startup/order_recovery.py` (new)

```python
class OrderRecoveryEngine:
    """
    On execution-service startup, for each connected venue:
    1. Fetch open orders from exchange REST API
    2. Compare against internal OrderBook state
    3. For each open order in exchange but NOT in internal state:
       - If age > MAX_ORPHAN_AGE_MINUTES: cancel it via venue API
       - Else: re-register in internal OrderBook as PENDING
    4. For each order in internal state as PENDING but NOT in exchange:
       - Mark as EXCHANGE_REJECTED, log ORDER_ORPHANED event
    5. For each partially filled order not yet applied internally:
       - Apply fill, update position tracker
    """
    MAX_ORPHAN_AGE_MINUTES: int = 5  # configurable per venue type
```

New UEI events:

- `ORDER_ORPHANED`
- `ORDER_RECOVERY_COMPLETED`
- `ORDER_RECOVERY_FAILED`

### B2 — Circuit breaker gate for recovery

Order recovery runs only if circuit breaker is CLOSED for that venue. If OPEN at startup: queue recovery, retry on
HALF_OPEN probe success.

### B3 — Wire into execution-service startup

File: `execution-service/execution_service/main.py` (or equivalent startup entry point) Wire `OrderRecoveryEngine.run()`
after circuit breaker initialisation, before accepting new orders. Emit `STARTED` only after recovery is complete or
explicitly skipped via `--skip-recovery` flag.

---

## Stream C: Portfolio drift correction (strategy-service)

### C1 — Portfolio rebalancer

File: `strategy-service/strategy_service/engine/rebalancing/portfolio_rebalancer.py` (new)

```python
class PortfolioRebalancer:
    """Detects drift from target allocations and generates rebalancing orders."""

    drift_threshold_pct: float = 2.0          # configurable per strategy
    rebalancing_window_minutes: int = 30       # TWAP duration for rebalancing orders
    min_order_usd: float = 100.0               # skip dust positions below this

    async def check_and_rebalance(self) -> list[RebalancingOrder]:
        """
        For each strategy portfolio:
        1. Fetch target weights from strategy config
        2. Fetch current weights from position-balance-monitor-service
        3. Calculate drift = |target_weight - current_weight| per asset
        4. If drift > drift_threshold_pct and notional > min_order_usd:
           - Generate TWAP rebalancing order (reduce over-weight, increase under-weight)
        5. Submit to execution-service
        6. Log PORTFOLIO_REBALANCE_TRIGGERED and PORTFOLIO_REBALANCE_COMPLETED events
        """
```

Triggers:

- **Scheduled**: daily at 00:00 UTC via Cloud Scheduler
- **Event-driven**: on `POSITION_CRITICAL_DISCREPANCY` UEI event
- **Threshold**: on any single position changing >10% of total portfolio value

### C2 — Per-strategy rebalancing config

File: `strategy-service/strategy_service/configs/rebalancing_config.yaml` (new)

```yaml
cefi_momentum:
  btc_target: 0.40
  eth_target: 0.35
  sol_target: 0.25
  drift_threshold_pct: 3.0
  rebalancing_window_minutes: 60

defi_basis:
  drift_threshold_pct: 5.0 # wider tolerance for DeFi (gas costs)
  rebalancing_window_minutes: 30
```

### C3 — Wire into strategy-service scheduler

File: `strategy-service/strategy_service/engine/scheduler.py` Add scheduled job for
`PortfolioRebalancer.check_and_rebalance()`.

---

## Stream D: DeFi vault rebalancing

### D1 — Yield snapshot fetcher

File: `strategy-service/strategy_service/engine/rebalancing/defi_yield_monitor.py` (new)

Fetches current APY from each DeFi protocol via UMI DeFi adapters (5-minute cache):

- Aave V3: supply APY per asset (USDC, USDT, ETH, wBTC)
- Curve: pool APY (3pool, stETH, tricrypto)
- Uniswap V3: fee APY per LP position
- Lido / EtherFi / Ethena: staking/restaking yield
- Morpho / Euler / Fluid: lending rates

### D2 — DeFi vault rebalancer

File: `strategy-service/strategy_service/engine/rebalancing/defi_vault_rebalancer.py` (new)

```python
class DeFiVaultRebalancer:
    """
    Moves liquidity between protocols when yield differential exceeds threshold.
    Example: Aave USDC APY=4.2% vs Morpho USDC APY=5.8% → differential 1.6% > threshold 1.0%
    → move up to 30% of Aave USDC position to Morpho.
    Uses execution-service DeFi handlers: lend_handler, swap_handler.
    """
    yield_differential_threshold: float = 1.0  # 1% APY differential
    max_single_move_pct: float = 30.0           # never move more than 30% in one rebalance
    cooldown_hours: int = 24                    # minimum hours between rebalances for same pair
    gas_cost_usd_max: float = 50.0              # skip if gas cost > $50
```

Execution sequence per rebalance:

1. Fetch yield snapshot from `DeFiYieldMonitor`
2. Identify best yield per asset (USDC, ETH, etc.)
3. If differential > threshold AND estimated gas < max: generate move
4. Submit via execution-service: withdraw from lower-yield → swap if needed → deposit to higher-yield
5. Log `DEFI_VAULT_REBALANCED` event with: from_protocol, to_protocol, asset, amount, yield_improvement

### D3 — Gas cost estimator

File: `strategy-service/strategy_service/engine/rebalancing/gas_estimator.py` (new)

Uses UMI onchain adapters (Alchemy) to estimate gas cost before submitting. Abort rebalance if estimated cost exceeds
yield improvement profit over 30 days.

---

## New UEI Events (add to unified-events-interface/schemas.py)

- `POSITION_CORRECTION_DISPATCHED`
- `POSITION_CORRECTION_FAILED`
- `ORDER_ORPHANED`
- `ORDER_RECOVERY_COMPLETED`
- `ORDER_RECOVERY_FAILED`
- `DEFI_VAULT_REBALANCED`
- `PORTFOLIO_REBALANCE_TRIGGERED`
- `PORTFOLIO_REBALANCE_COMPLETED`

---

## Tests

### Unit tests (per stream)

- `test_correction_dispatcher.py` — mock execution-service, verify correction order on CRITICAL
- `test_startup_reconciler.py` — verify reconciliation runs before STARTED event
- `test_order_recovery.py` — mock exchange APIs, verify orphan detection/cancellation
- `test_portfolio_rebalancer.py` — mock PBS positions, verify drift calculation + order generation
- `test_defi_vault_rebalancer.py` — mock yield snapshots, verify trigger conditions and gas gate
- `test_gas_estimator.py` — mock Alchemy, verify gas cost calculation

### Integration tests

File: `system-integration-tests/tests/integration/test_recon_rebalancing.py`

- Inject position discrepancy → verify CRITICAL event + correction order submitted
- Simulate restart with orphan orders → verify `ORDER_RECOVERY_COMPLETED`
- Simulate drift >3% → verify rebalancing orders generated with correct direction
- Simulate yield differential >1% → verify DeFi vault rebalance triggered
- Simulate gas cost > $50 → verify rebalance skipped

---

## Verification Gates

- [ ] PBS: `auto_correct_enabled=True` in staging → correction orders submitted on CRITICAL
- [ ] Execution-service: restart with open orders → `ORDER_RECOVERY_COMPLETED` in logs
- [ ] Strategy-service: drift test → rebalancing orders generated within 60s
- [ ] DeFi vault: 1.5% yield differential → vault rebalance executed
- [ ] Gas gate: $60 estimated gas → rebalance skipped
- [ ] All 8 new UEI events exported from `unified-events-interface`

## Files Modified / Created

- `position-balance-monitor-service/core/correction_dispatcher.py` (new)
- `position-balance-monitor-service/core/startup_reconciler.py` (new)
- `position-balance-monitor-service/core/reconciliation_engine.py` (extend)
- `execution-service/engine/startup/order_recovery.py` (new)
- `execution-service/main.py` (wire startup)
- `strategy-service/engine/rebalancing/` (new directory — all D files above)
- `strategy-service/engine/scheduler.py` (add job)
- `strategy-service/configs/rebalancing_config.yaml` (new)
- `unified-events-interface/schemas.py` (8 new events)
- `system-integration-tests/tests/integration/test_recon_rebalancing.py` (new)

## Dependencies

- `stub_completion_interfaces_and_infra.md` (UPI adapters needed for DeFi execution)
- `error_normalisation_unknown_exchanges_2026_03_10.md` (canonical errors in recovery logic)
- `api_keys_and_auth.md` Phase 2–4 (DeFi protocol keys for yield monitoring)
